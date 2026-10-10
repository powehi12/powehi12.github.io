"""Offline regression tests for the pinned generator and blog security patch.

Usage: python -B scripts/test_gmeek_security.py /path/to/pristine/Gmeek
No GitHub requests, credentials, or site deployments are performed.
"""
import contextlib
import copy
import datetime
import html
from html.parser import HTMLParser
import io
import json
import os
from pathlib import Path
import runpy
import shutil
import sys
import tempfile
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch

from harden_gmeek import POLICY, SOURCE_HASHES, harden_tree

UPSTREAM = Path(sys.argv[1]).resolve()
BASELINE = "--baseline" in sys.argv
sys.argv = sys.argv[:1]


def issue(number, author="powehi12", title="Normal & quoted title", body="Article.", labels=("note",), pr=False):
    raw = {"state": "open", "user": {"login": author}}
    if pr:
        raw["pull_request"] = {}
    return SimpleNamespace(
        number=number, title=title, body=body, raw_data=raw, state="open",
        labels=[SimpleNamespace(name=name) for name in labels],
        created_at=datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc),
        get_comments=lambda: SimpleNamespace(totalCount=0),
        get_events=lambda: [],
    )


class Feed:
    def __getattr__(self, name):
        return lambda *args, **kwargs: self

    def rss_file(self, path):
        Path(path).write_text("<rss/>", encoding="utf-8")


class HeadingAudit(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_heading = False
        self.text = ""
        self.child_tags = []
        self.scripts = []
        self.attribute_values = []

    def handle_starttag(self, tag, attrs):
        self.attribute_values.extend(attrs)
        if tag == "h1":
            self.in_heading = True
        elif self.in_heading:
            self.child_tags.append(tag)
        if tag == "script":
            self.scripts.append(dict(attrs))

    def handle_endtag(self, tag):
        if tag == "h1":
            self.in_heading = False

    def handle_data(self, data):
        if self.in_heading:
            self.text += data


class SecurityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="gmeek-test-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "generator"
        self.workspace = Path(self.tmp.name) / "workspace"
        self.root.mkdir()
        self.workspace.mkdir()
        shutil.copy2(UPSTREAM / "Gmeek.py", self.root / "Gmeek.py")
        shutil.copytree(UPSTREAM / "templates", self.root / "templates")
        if not BASELINE:
            harden_tree(self.root)
        self.config = {
            "title": "Blog", "subTitle": "Description",
            "avatarUrl": "https://example.invalid/avatar.png",
            "GMEEK_VERSION": "v2.25", "themeMode": "fix",
            "needComment": 0, "urlMode": "issue",
            "script": '<script data-trusted="global">/* trusted */</script>',
        }
        self.write_config()
        self.calls = []

    def write_config(self):
        (self.root / "config.json").write_text(json.dumps(self.config), encoding="utf-8")

    def run_generator(self, issues, selected=""):
        by_number = {item.number: item for item in issues}
        repo = SimpleNamespace(
            name="powehi12.github.io", owner=SimpleNamespace(login="powehi12"),
            get_labels=lambda: [SimpleNamespace(name="note", color="123456")],
            get_issues=lambda: list(issues), get_issue=lambda n: by_number[n],
        )
        github = ModuleType("github")
        github.Github = lambda token: SimpleNamespace(get_repo=lambda name: repo)
        requests = ModuleType("requests")
        requests.RequestException = RuntimeError

        def markdown(url, json, headers):
            self.assertEqual(url, "https://api.github.com/markdown")
            self.calls.append(json["text"])
            return SimpleNamespace(
                text="<p>" + html.escape(json["text"]) + "</p>",
                raise_for_status=lambda: None,
            )
        requests.post = markdown
        xpinyin = ModuleType("xpinyin")
        xpinyin.Pinyin = lambda: SimpleNamespace(get_pinyin=lambda title: title)
        transliterate = ModuleType("transliterate")
        transliterate.translit = lambda title, **kwargs: title
        feedgen = ModuleType("feedgen")
        feedmodule = ModuleType("feedgen.feed")
        feedmodule.FeedGenerator = Feed
        modules = {
            "github": github, "requests": requests, "xpinyin": xpinyin,
            "transliterate": transliterate, "feedgen": feedgen, "feedgen.feed": feedmodule,
        }
        argv = ["Gmeek.py", "dummy-offline-token", "powehi12/powehi12.github.io", "--issue_number", selected]
        old_cwd = Path.cwd()
        try:
            os.chdir(self.root)
            with patch.dict(sys.modules, modules), patch.object(sys, "argv", argv), patch.dict(
                os.environ, {"GITHUB_WORKSPACE": str(self.workspace), "GITHUB_EVENT_NAME": "workflow_dispatch"}
            ), contextlib.redirect_stdout(io.StringIO()):
                runpy.run_path(str(self.root / "Gmeek.py"), run_name="__main__")
        finally:
            os.chdir(old_cwd)
        return json.loads((self.root / "blogBase.json").read_text(encoding="utf-8"))

    def test_full_filters_foreign_missing_identity_and_pull_requests(self):
        missing = issue(4)
        missing.raw_data["user"] = None
        closed = issue(5)
        closed.raw_data["state"] = closed.state = "closed"
        base = self.run_generator([
            issue(1, author="PoWeHi12"), issue(2, author="outsider", body="foreign body"),
            issue(3, pr=True), missing, closed, issue(6, labels=()),
        ])
        self.assertEqual(set(base["postListJson"]), {"P1"})
        self.assertEqual(len(self.calls), 1)
        self.assertFalse((self.root / "docs/post/2.html").exists())

    def test_incremental_rejects_foreign_before_body_rendering(self):
        self.run_generator([issue(1)])
        before = (self.root / "blogBase.json").read_bytes()
        self.calls.clear()
        missing = issue(2)
        missing.raw_data["user"] = {}
        for rejected in (issue(2, author="outsider"), issue(2, pr=True), missing, issue(2, labels=())):
            with self.subTest(rejected=rejected.raw_data), self.assertRaisesRegex(ValueError, "Only labeled Issues"):
                self.run_generator([issue(1), rejected], "2")
        self.assertEqual((self.root / "blogBase.json").read_bytes(), before)
        self.assertEqual(self.calls, [])
        self.assertFalse((self.root / "docs/post/2.html").exists())

    def test_incremental_owner_preserves_existing_articles(self):
        self.run_generator([issue(1), issue(2)])
        base = self.run_generator([issue(1), issue(2, title="Updated & literal")], "2")
        self.assertEqual(set(base["postListJson"]), {"P1", "P2"})
        self.assertEqual(base["postListJson"]["P2"]["postTitle"], "Updated & literal")
        self.assertTrue((self.root / "docs/post/1.html").exists())

    def test_legacy_cache_forces_full_rebuild_and_removes_stale_pages(self):
        self.run_generator([issue(1)])
        path = self.root / "blogBase.json"
        base = json.loads(path.read_text(encoding="utf-8"))
        base.pop("gmeekSecurityPolicy", None)
        stale = copy.deepcopy(base["postListJson"]["P1"])
        stale["postTitle"] = "Legacy foreign"
        stale["htmlDir"] = "docs/post/99.html"
        base["postListJson"]["P99"] = stale
        base["singeListJson"]["P100"] = dict(stale, htmlDir="docs/foreign.html")
        path.write_text(json.dumps(base), encoding="utf-8")
        for name in ("docs/post/99.html", "docs/foreign.html", "backup/foreign.md"):
            (self.root / name).write_text("stale untrusted content", encoding="utf-8")
        base = self.run_generator([issue(1), issue(99, author="outsider")], "1")
        self.assertEqual(set(base["postListJson"]), {"P1"})
        self.assertEqual(base["singeListJson"], {})
        self.assertEqual(base["gmeekSecurityPolicy"], POLICY)
        for name in ("docs/post/99.html", "docs/foreign.html", "backup/foreign.md"):
            self.assertFalse((self.root / name).exists())

    def test_titles_are_text_and_trusted_scripts_survive(self):
        for title in (
            '<img src=x onerror="window.__test=1"> & title',
            '</title><svg onload="window.__test=2"> " & &#60; \n 标题',
        ):
            with self.subTest(title=title):
                body = 'Article.\r\n##' + json.dumps({"script": '<script data-trusted="post">/* trusted */</script>'})
                base = self.run_generator([issue(1, title=title, body=body)])
                rendered = (self.root / "docs/post/1.html").read_text(encoding="utf-8")
                parsed = HeadingAudit()
                parsed.feed(rendered)
                self.assertEqual(parsed.text, title)
                self.assertEqual(parsed.child_tags, [])
                self.assertIn({"data-trusted": "global"}, parsed.scripts)
                self.assertIn({"data-trusted": "post"}, parsed.scripts)
                self.assertEqual(base["postListJson"]["P1"]["postTitle"], title)
                exported = json.loads((self.root / "docs/postList.json").read_text())
                self.assertEqual(exported["P1"]["postTitle"], title)

    def test_single_page_title_uses_html_and_javascript_contexts(self):
        self.config["singlePage"] = ["note"]
        self.write_config()
        title = 'About "</script><img src=x onerror=window.__test=3>'
        self.run_generator([issue(1, title=title)])
        rendered = (self.root / "docs/index.html").read_text(encoding="utf-8")
        parsed = HeadingAudit()
        parsed.feed(rendered)
        self.assertIn(("title", title), parsed.attribute_values)
        self.assertNotIn("</script><img", rendered)
        self.assertIn("\\u003c/script\\u003e", rendered)

    def test_modified_upstream_fails_before_any_patch_write(self):
        pristine = self.root / "Gmeek.py"
        # Restore originals so this checks the fingerprint boundary, not repeat application.
        for name in SOURCE_HASHES:
            shutil.copy2(UPSTREAM / name, self.root / name)
        before = pristine.read_bytes()
        template = self.root / "templates/post.html"
        template.write_text(template.read_text(encoding="utf-8") + "\nchanged", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Unexpected upstream"):
            harden_tree(self.root)
        self.assertEqual(pristine.read_bytes(), before)


if __name__ == "__main__":
    unittest.main(verbosity=2)
