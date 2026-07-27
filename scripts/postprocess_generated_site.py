#!/usr/bin/env python3
"""Apply deterministic safety, accessibility, and SEO fixes to Gmeek output.

Usage:
    python scripts/postprocess_generated_site.py docs
    python scripts/postprocess_generated_site.py --check docs

The script intentionally uses only the Python standard library so the same
post-processing step can run locally and in GitHub Actions.
"""

from __future__ import annotations

import argparse
import html as html_module
import json
import re
import sys
import unicodedata
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote


SITE_ORIGIN = "https://powehi12.github.io"
SITE_NAME = "qbyang 的个人博客"
SITE_DESCRIPTION = "记录 Agent、LLM、强化学习与论文阅读"
ASSET_VERSION = "20260727-5"

RSS_LINK = (
    f'<link rel="alternate" type="application/rss+xml" '
    f'title="{SITE_NAME} RSS" href="{SITE_ORIGIN}/rss.xml">'
)

# Match an HTML start tag without treating > characters inside quoted
# attributes as the end of the tag. Gmeek descriptions can contain Markdown
# block quotes, so a plain [^>]* matcher corrupts otherwise valid meta tags.
ATTRIBUTE_FRAGMENT = r"""(?:[^"'<>]|"[^"]*"|'[^']*')*"""
META_TAG_PATTERN = re.compile(
    rf"<meta\b{ATTRIBUTE_FRAGMENT}>",
    re.IGNORECASE | re.DOTALL,
)
LINK_TAG_PATTERN = re.compile(
    rf"<link\b{ATTRIBUTE_FRAGMENT}>",
    re.IGNORECASE | re.DOTALL,
)

COMMENT_RECOVERY_SCRIPT = """<script id="comment-load-recovery">
(function () {
  var loadTimer = null;
  var observer = null;

  function resetButton(button, message) {
    button.disabled = false;
    button.dataset.loading = "false";
    button.textContent = message;
    button.setAttribute("aria-label", message);
  }

  window.openComments = function () {
    var comments = document.getElementById("comments");
    var button = document.getElementById("cmButton");
    if (!comments || !button || button.dataset.loading === "true") return;

    if (loadTimer) window.clearTimeout(loadTimer);
    if (observer) observer.disconnect();
    comments.replaceChildren();
    button.dataset.loading = "true";
    button.disabled = true;
    button.textContent = "正在加载评论…";
    button.setAttribute("aria-label", "正在加载评论");

    var script = document.createElement("script");
    script.src = "https://utteranc.es/client.js";
    script.setAttribute("repo", "powehi12/powehi12.github.io");
    script.setAttribute("issue-term", "title");
    script.setAttribute("theme", "github-dark");
    script.setAttribute("crossorigin", "anonymous");
    script.async = true;

    function fail() {
      if (loadTimer) window.clearTimeout(loadTimer);
      if (observer) observer.disconnect();
      script.remove();
      comments.textContent = "评论暂时无法加载，请检查网络后重试。";
      resetButton(button, "重试加载评论");
    }

    function succeed() {
      if (loadTimer) window.clearTimeout(loadTimer);
      if (observer) observer.disconnect();
      button.style.display = "none";
      button.dataset.loading = "false";
    }

    script.addEventListener("error", fail, { once: true });
    observer = new MutationObserver(function () {
      if (comments.querySelector("iframe.utterances")) succeed();
    });
    observer.observe(comments, { childList: true, subtree: true });
    loadTimer = window.setTimeout(function () {
      if (!comments.querySelector("iframe.utterances")) fail();
    }, 10000);
    comments.appendChild(script);
  };
})();
</script>"""

TAG_FORM_SCRIPT = """<script id="tag-form-events">
(function () {
  var form = document.getElementById("site-search-form");
  var input = document.getElementById("search-input");
  if (!form) return;

  function applyHashState() {
    var label = window.location.hash.slice(1);
    try { label = decodeURIComponent(label); } catch (error) {}
    setClassDisplay(label || "All");
  }

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    searchShow();
  });
  if (input) {
    input.addEventListener("keydown", function (event) {
      if (event.key === "Enter" && !event.isComposing) {
        event.preventDefault();
        searchShow();
      }
    });
  }
  window.addEventListener("hashchange", applyHashState);
})();
</script>"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Harden and enrich generated Gmeek HTML."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Report generated files that are not post-processed; do not write.",
    )
    parser.add_argument(
        "docs",
        nargs="?",
        default="docs",
        type=Path,
        help="Generated site directory (default: docs).",
    )
    return parser.parse_args()


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def title_visual_units(value: str) -> float:
    """Estimate rendered title width across mixed Latin and CJK text."""
    text = normalize_space(
        html_module.unescape(re.sub(r"<[^>]+>", " ", value))
    )
    units = 0.0
    for character in text:
        if character.isspace():
            units += 0.25
        elif unicodedata.combining(character):
            continue
        elif unicodedata.east_asian_width(character) in {"W", "F"}:
            units += 1.0
        else:
            units += 0.5
    return units


def classify_post_title(html: str) -> str:
    """Add a deterministic size class to long article titles."""
    pattern = re.compile(
        r"<h1\b(?P<attrs>[^>]*)>(?P<content>.*?)</h1>",
        re.IGNORECASE | re.DOTALL,
    )

    def replace(match: re.Match[str]) -> str:
        attrs = match.group("attrs")
        class_match = re.search(
            r'\bclass\s*=\s*(["\'])(.*?)\1',
            attrs,
            re.IGNORECASE | re.DOTALL,
        )
        if not class_match:
            return match.group(0)

        classes = class_match.group(2).split()
        if "postTitle" not in classes:
            return match.group(0)

        classes = [
            class_name
            for class_name in classes
            if class_name not in {"postTitle--long", "postTitle--xlong"}
        ]
        visual_units = title_visual_units(match.group("content"))
        if visual_units >= 40:
            classes.append("postTitle--xlong")
        elif visual_units >= 28:
            classes.append("postTitle--long")

        quote_mark = class_match.group(1)
        class_attribute = f'class={quote_mark}{" ".join(classes)}{quote_mark}'
        attrs = (
            attrs[: class_match.start()]
            + class_attribute
            + attrs[class_match.end() :]
        )
        return f'<h1{attrs}>{match.group("content")}</h1>'

    return pattern.sub(replace, html, count=1)


def clean_description(value: str) -> str:
    value = html_module.unescape(value)
    # A few source posts contain nested Markdown links. Peel those layers until
    # the text stabilizes so a single invocation is fully idempotent.
    for _ in range(4):
        cleaned = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", value)
        cleaned = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", cleaned)
        if cleaned == value:
            break
        value = cleaned
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"(?m)^\s{0,3}(?:#{1,6}|>|[-*+]\s|\d+[.)]\s)", " ", value)
    value = re.sub(r"[*_`~$|]+", "", value)
    value = normalize_space(value)
    if not value:
        value = SITE_DESCRIPTION
    if len(value) > 160:
        value = value[:157].rstrip("，。；：、,.!?！？;: ") + "…"
    return value


def tag_attribute(tag: str, attribute: str) -> str | None:
    match = re.search(
        rf"\b{re.escape(attribute)}\s*=\s*([\"'])(.*?)\1",
        tag,
        re.IGNORECASE | re.DOTALL,
    )
    return match.group(2) if match else None


def matching_meta_tags(html: str, attribute: str, key: str) -> list[re.Match[str]]:
    expected = key.casefold()
    return [
        match
        for match in META_TAG_PATTERN.finditer(html)
        if (tag_attribute(match.group(0), attribute) or "").casefold() == expected
    ]


def extract_meta(html: str, attribute: str, key: str) -> str | None:
    matches = matching_meta_tags(html, attribute, key)
    return tag_attribute(matches[0].group(0), "content") if matches else None


def extract_title(html: str) -> str:
    match = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    if not match:
        return SITE_NAME
    return normalize_space(html_module.unescape(match.group(1)))


def remove_meta(html: str, attribute: str, key: str) -> str:
    expected = key.casefold()

    def replace(match: re.Match[str]) -> str:
        value = tag_attribute(match.group(0), attribute)
        return "" if value and value.casefold() == expected else match.group(0)

    return META_TAG_PATTERN.sub(replace, html)


def remove_link_rel(html: str, relation: str) -> str:
    expected = relation.casefold()

    def replace(match: re.Match[str]) -> str:
        values = (tag_attribute(match.group(0), "rel") or "").casefold().split()
        return "" if expected in values else match.group(0)

    return LINK_TAG_PATTERN.sub(replace, html)


def set_title(html: str, title: str) -> str:
    escaped = html_module.escape(title)
    if re.search(r"<title>.*?</title>", html, re.IGNORECASE | re.DOTALL):
        return re.sub(
            r"<title>.*?</title>",
            f"<title>{escaped}</title>",
            html,
            count=1,
            flags=re.IGNORECASE | re.DOTALL,
        )
    return html.replace("</head>", f"<title>{escaped}</title>\n</head>", 1)


def normalize_theme(html: str) -> str:
    root_pattern = re.compile(r"<html\b(?P<attrs>[^>]*)>", re.IGNORECASE)

    def replace_root(match: re.Match[str]) -> str:
        attrs = match.group("attrs")
        for name, value in (
            ("data-color-mode", "dark"),
            ("data-dark-theme", "dark"),
            ("data-light-theme", "dark"),
        ):
            attribute_pattern = re.compile(
                rf"\b{re.escape(name)}\s*=\s*([\"'])(.*?)\1",
                re.IGNORECASE | re.DOTALL,
            )
            replacement = f'{name}="{value}"'
            if attribute_pattern.search(attrs):
                attrs = attribute_pattern.sub(replacement, attrs, count=1)
            else:
                attrs += f" {replacement}"
        return f"<html{attrs}>"

    html = root_pattern.sub(replace_root, html, count=1)
    return re.sub(
        r'(script\.setAttribute\("theme",\s*)"(?:github-light|dark)"(\s*\);)',
        r'\1"github-dark"\2',
        html,
        flags=re.IGNORECASE,
    )


def public_url(relative: Path) -> str:
    path = relative.as_posix()
    if path == "index.html":
        return f"{SITE_ORIGIN}/"
    encoded_path = quote(path, safe="/@:+-._~!$&'()*+,;=")
    return f"{SITE_ORIGIN}/{encoded_path}"


def page_kind(relative: Path) -> str:
    if relative.parts and relative.parts[0] == "post":
        return "post"
    if relative.name == "tag.html":
        return "tag"
    if relative.name == "404.html":
        return "error"
    return "home"


def pagination_page_number(relative: Path) -> int | None:
    if len(relative.parts) != 1:
        return None
    if relative.name == "index.html":
        return 1
    match = re.fullmatch(r"page(\d+)\.html", relative.name)
    return int(match.group(1)) if match else None


def pagination_total_pages(paths: list[Path], docs: Path) -> int:
    return max(
        (
            page_number
            for path in paths
            if (page_number := pagination_page_number(path.relative_to(docs))) is not None
        ),
        default=1,
    )


def title_for_page(html: str, relative: Path) -> str:
    page_number = pagination_page_number(relative)
    if page_number and page_number > 1:
        return f"{SITE_NAME} - 第 {page_number} 页"
    if relative.name == "tag.html":
        return f"标签与搜索 - {SITE_NAME}"
    if relative.name == "404.html":
        return f"页面未找到 - {SITE_NAME}"
    return extract_title(html)


def description_for_page(html: str, relative: Path) -> str:
    if relative.name == "404.html":
        return "这个页面不存在，可能已被移动或删除。"
    if relative.name == "tag.html":
        return "按标签浏览或搜索 qbyang 的博客文章。"
    raw = extract_meta(html, "name", "description") or SITE_DESCRIPTION
    return clean_description(raw)


def add_body_class(html: str, class_name: str) -> str:
    pattern = re.compile(r"<body(?P<attrs>[^>]*)>", re.IGNORECASE)

    def replace(match: re.Match[str]) -> str:
        attrs = match.group("attrs")
        class_match = re.search(r'\bclass\s*=\s*(["\'])(.*?)\1', attrs, re.DOTALL)
        if class_match:
            classes = class_match.group(2).split()
            if class_name not in classes:
                classes.append(class_name)
            replacement = f'class={class_match.group(1)}{" ".join(classes)}{class_match.group(1)}'
            attrs = attrs[: class_match.start()] + replacement + attrs[class_match.end() :]
        else:
            attrs += f' class="{class_name}"'
        return f"<body{attrs}>"

    return pattern.sub(replace, html, count=1)


def add_attributes_to_id(html: str, element_id: str, attributes: dict[str, str]) -> str:
    pattern = re.compile(
        rf"<(?P<tag>[a-z][\w:-]*)(?P<attrs>[^>]*\bid\s*=\s*([\"'])"
        rf"{re.escape(element_id)}\3[^>]*)>",
        re.IGNORECASE,
    )

    def replace(match: re.Match[str]) -> str:
        attrs = match.group("attrs")
        for name, value in attributes.items():
            if not re.search(rf"\b{re.escape(name)}\s*=", attrs, re.IGNORECASE):
                attrs += f' {name}="{html_module.escape(value, quote=True)}"'
        return f"<{match.group('tag')}{attrs}>"

    return pattern.sub(replace, html, count=1)


def add_skip_link(html: str) -> str:
    if re.search(r'class\s*=\s*["\'][^"\']*\bskip-link\b', html, re.IGNORECASE):
        return html
    return re.sub(
        r"(<body[^>]*>)",
        r'\1\n<a class="skip-link" href="#content">跳到主要内容</a>',
        html,
        count=1,
        flags=re.IGNORECASE,
    )


def add_anchor_labels(html: str) -> str:
    pattern = re.compile(r"<a\b(?P<attrs>[^>]*)>", re.IGNORECASE)

    def replace(match: re.Match[str]) -> str:
        attrs = match.group("attrs")
        if re.search(r"\baria-label\s*=", attrs, re.IGNORECASE):
            return match.group(0)
        title_match = re.search(r'\btitle\s*=\s*(["\'])(.*?)\1', attrs, re.DOTALL)
        if not title_match:
            return match.group(0)
        label = normalize_space(html_module.unescape(title_match.group(2)))
        return f'<a{attrs} aria-label="{html_module.escape(label, quote=True)}">'

    return pattern.sub(replace, html)


def add_noopener(html: str) -> str:
    pattern = re.compile(
        r"<a\b(?P<attrs>[^>]*\btarget\s*=\s*([\"'])_blank\2[^>]*)>",
        re.IGNORECASE | re.DOTALL,
    )

    def replace(match: re.Match[str]) -> str:
        attrs = match.group("attrs")
        rel_match = re.search(r'\brel\s*=\s*(["\'])(.*?)\1', attrs, re.DOTALL)
        if rel_match:
            values = rel_match.group(2).split()
            for value in ("noopener", "noreferrer"):
                if value not in values:
                    values.append(value)
            new_rel = f'rel={rel_match.group(1)}{" ".join(values)}{rel_match.group(1)}'
            attrs = attrs[: rel_match.start()] + new_rel + attrs[rel_match.end() :]
        else:
            attrs += ' rel="noopener noreferrer"'
        return f"<a{attrs}>"

    return pattern.sub(replace, html)


def improve_header(html: str, kind: str) -> str:
    html = re.sub(
        r'(<img\b[^>]*\bclass=["\'][^"\']*\bavatar\b[^>]*\balt=)(["\']).*?\2',
        r'\1"qbyang 的头像"',
        html,
        flags=re.IGNORECASE,
    )
    html = re.sub(
        r'(<a\b(?=[^>]*\bclass=["\'][^"\']*\bblogTitle\b)(?![^>]*\bhref=))',
        rf'\1 href="{SITE_ORIGIN}/"',
        html,
        flags=re.IGNORECASE,
    )

    if kind == "home":
        html = re.sub(
            r'<div class="title-left">(?P<inner>.*?)</div>(?=\s*<div class="title-right">)',
            r'<h1 class="title-left">\g<inner></h1>',
            html,
            count=1,
            flags=re.DOTALL,
        )
    elif kind == "tag":
        html = re.sub(
            r'<span class="tagTitle">(?P<inner><span>.*?</span>\s*'
            r'<span[^>]*>.*?</span>)</span>',
            r'<h1 class="tagTitle" aria-live="polite">\g<inner></h1>',
            html,
            count=1,
            flags=re.DOTALL,
        )

    html = add_anchor_labels(html)
    html = re.sub(
        r'<svg\b(?P<attrs>(?=[^>]*\bclass=["\'][^"\']*\bocticon\b)[^>]*)>',
        lambda match: (
            match.group(0)
            if re.search(r"\baria-hidden\s*=", match.group("attrs"), re.IGNORECASE)
            else f'<svg{match.group("attrs")} aria-hidden="true">'
        ),
        html,
        flags=re.IGNORECASE,
    )
    return html


def improve_home_cards(html: str) -> str:
    pattern = re.compile(
        r'<a\s+class="(?P<classes>SideNav-item[^"]*)"\s+'
        r'href="(?P<href>[^"]+)">\s*'
        r'<div class="d-flex flex-items-center">(?P<main>.*?)</div>\s*'
        r'<div class="listLabels">(?P<labels>.*?)</div>\s*</a>',
        re.IGNORECASE | re.DOTALL,
    )

    def replace(match: re.Match[str]) -> str:
        classes = match.group("classes").split()
        if "post-card" not in classes:
            classes.append("post-card")
        labels = re.sub(
            r'<span class="Label LabelName"[^>]*>\s*<object>\s*'
            r'<a\b[^>]*\bhref="([^"]+)"[^>]*>(.*?)</a>\s*</object>\s*</span>',
            r'<a class="Label LabelName" href="\1">\2</a>',
            match.group("labels"),
            flags=re.IGNORECASE | re.DOTALL,
        )
        labels = re.sub(
            r"<object>\s*(<a\b.*?</a>)\s*</object>",
            r"\1",
            labels,
            flags=re.IGNORECASE | re.DOTALL,
        )
        return (
            f'<div class="{" ".join(classes)}">\n'
            f'    <a class="post-card-link d-flex flex-items-center" '
            f'href="{match.group("href")}">{match.group("main")}</a>\n'
            f'    <div class="listLabels">{labels}</div>\n'
            "</div>"
        )

    return pattern.sub(replace, html)


def improve_pagination(html: str, relative: Path, total_pages: int) -> str:
    current_page = pagination_page_number(relative)
    if current_page is None or total_pages <= 1:
        return html

    indicator = (
        f'<span class="page-indicator" aria-current="page" '
        f'aria-label="第 {current_page} 页，共 {total_pages} 页">'
        f"{current_page} / {total_pages}</span>"
    )
    pagination_pattern = re.compile(
        r"(?P<open><div\b"
        r"(?=[^>]*\bclass\s*=\s*[\"'][^\"']*\bpagination\b[^\"']*[\"'])"
        r"[^>]*>)(?P<body>.*?)(?P<close></div>)",
        re.IGNORECASE | re.DOTALL,
    )
    indicator_pattern = re.compile(
        r"<span\b"
        r"(?=[^>]*\bclass\s*=\s*[\"'][^\"']*\bpage-indicator\b[^\"']*[\"'])"
        r"[^>]*>.*?</span>",
        re.IGNORECASE | re.DOTALL,
    )
    previous_pattern = re.compile(
        r"(?P<previous><(?P<tag>a|span)\b"
        r"(?=[^>]*\bclass\s*=\s*[\"'][^\"']*\bprevious_page\b[^\"']*[\"'])"
        r"[^>]*>.*?</(?P=tag)>)",
        re.IGNORECASE | re.DOTALL,
    )

    def replace(match: re.Match[str]) -> str:
        body = indicator_pattern.sub("", match.group("body"))
        previous = previous_pattern.search(body)
        if not previous:
            return match.group(0)
        body = body[: previous.end()] + indicator + body[previous.end() :]
        return match.group("open") + body + match.group("close")

    return pagination_pattern.sub(replace, html, count=1)


def improve_tables(html: str) -> str:
    # Repair output produced by an early version of this post-processor before
    # applying the word-boundary-safe header rule below.
    html = html.replace('<th scope="col"ead>', "<thead>")
    html = html.replace(
        "<markdown-accessiblity-table>",
        '<div class="table-scroll" role="region" '
        'aria-label="可横向滚动的数据表" tabindex="0">',
    )
    html = html.replace("</markdown-accessiblity-table>", "</div>")
    html = re.sub(
        r"<th\b(?![^>]*\bscope\s*=)(?P<attrs>[^>]*)>",
        r'<th scope="col"\g<attrs>>',
        html,
        flags=re.IGNORECASE,
    )
    return html


def normalize_assets(html: str) -> str:
    html = re.sub(
        r"claude\.css(?:\?v=[^\"'\s>]+)?",
        f"claude.css?v={ASSET_VERSION}",
        html,
        flags=re.IGNORECASE,
    )
    html = re.sub(
        r"collapsible-toc\.js(?:\?v=[^\"'\s>]+)?",
        f"collapsible-toc.js?v={ASSET_VERSION}",
        html,
        flags=re.IGNORECASE,
    )
    html = re.sub(
        r"mathjax@3(?:\.\d+(?:\.\d+)?)?/",
        "mathjax@3.2.2/",
        html,
        flags=re.IGNORECASE,
    )
    return html


def inject_once_before_html_end(html: str, marker: str, script: str) -> str:
    if marker in html:
        return html
    if "</html>" in html:
        return html.replace("</html>", f"{script}\n</html>", 1)
    return html + "\n" + script + "\n"


def harden_tag_page(html: str) -> str:
    html = re.sub(
        r'<div class="subnav-search">(?P<inner>.*?)</div>',
        r'<form class="subnav-search" id="site-search-form" role="search">'
        r"\g<inner></form>",
        html,
        count=1,
        flags=re.DOTALL,
    )
    html = re.sub(
        r'<input(?P<attrs>[^>]*\bclass=["\'][^"\']*\bsubnav-search-input\b[^>]*)>',
        lambda match: (
            match.group(0)
            if re.search(r"\bid\s*=", match.group("attrs"), re.IGNORECASE)
            else '<input id="search-input" name="q" autocomplete="off"'
            + match.group("attrs")
            + ">"
        ),
        html,
        count=1,
        flags=re.IGNORECASE,
    )
    html = re.sub(
        r'<button(?P<attrs>[^>]*)\s+onclick=["\'][^"\']*searchShow\(\)[^"\']*["\']'
        r"(?P<tail>[^>]*)>",
        r'<button id="search-submit"\g<attrs>\g<tail>>',
        html,
        count=1,
        flags=re.IGNORECASE,
    )
    html = re.sub(
        r'<div class="notFind"(?P<attrs>[^>]*)>',
        lambda match: (
            '<div class="notFind"'
            + match.group("attrs")
            + (
                ""
                if re.search(r"\brole\s*=", match.group("attrs"), re.IGNORECASE)
                else ' role="status" aria-live="polite"'
            )
            + ">"
        ),
        html,
        count=1,
    )

    replacements = {
        'showLabels.innerHTML="&nbsp;&nbsp;"+label+" ";':
            'showLabels.textContent=label+" ";',
        'showLabels.setAttribute("onclick", "javascript:updateShowTag(\'" + label + "\');");':
            'showLabels.dataset.tag=label;\n'
            '        showLabels.setAttribute("aria-pressed", "false");\n'
            '        showLabels.addEventListener("click", function(){updateShowTag(this.dataset.tag);});',
        "LabelNum.innerHTML=labelsCount[label];":
            "LabelNum.textContent=labelsCount[label];",
        'div.setAttribute("class","lists "+jsonData[i][\'labels\'].join(" "));':
            'div.setAttribute("class","lists");\n'
            "            div.dataset.labels=JSON.stringify(jsonData[i]['labels']);",
        "title.innerHTML=jsonData[i]['postTitle'];":
            "title.textContent=jsonData[i]['postTitle'];",
        "LabelName.innerHTML=label;": "LabelName.textContent=label;",
        "LabelTime.innerHTML=jsonData[i]['createdDate'];":
            "LabelTime.textContent=jsonData[i]['createdDate'];",
        'tagTitle.innerHTML="Tag #"+label;':
            'tagTitle.textContent="Tag #"+label;\n'
            '    document.querySelectorAll("#taglabel .Label").forEach(function(button){\n'
            '        button.setAttribute("aria-pressed", String(button.dataset.tag===label));\n'
            '    });',
        'tagTitle.innerHTML="Search #"+searchInput;':
            'tagTitle.textContent="Search #"+searchInput;',
        ".childNodes[1].innerHTML.toUpperCase()":
            ".childNodes[1].textContent.toUpperCase()",
        "notFind.innerHTML='Not Find \"'+searchInput+'\"';":
            "notFind.textContent='未找到“'+searchInput+'”';",
    }
    for old, new in replacements.items():
        html = html.replace(old, new)

    svg_style = 'svg.setAttributeNS(null,"style","width:16px;height:16px");'
    svg_accessible = 'svg.setAttributeNS(null,"aria-hidden","true");'
    if svg_accessible not in html:
        html = html.replace(
            svg_style, svg_style + "\n            " + svg_accessible, 1
        )

    search_title = 'tagTitle.textContent="Search #"+searchInput;'
    reset_pressed = (
        'document.querySelectorAll("#taglabel .Label").forEach(function(button){\n'
        '        button.setAttribute("aria-pressed", "false");\n'
        "    });"
    )
    if reset_pressed not in html:
        html = html.replace(
            search_title, search_title + "\n    " + reset_pressed, 1
        )

    old_filter = """    else if(tagList.indexOf(label)!=-1){
        for(let i = 0; i < lists.length; i++){
            lists[i].style.display='none';
        }

        let labels = document.getElementsByClassName(label);
        for(let i = 0; i < labels.length; i++){
            labels[i].style.display='block';
        }
        document.getElementsByClassName("notFind")[0].style.display='none';
    }"""
    new_filter = """    else if(tagList.indexOf(label)!=-1){
        for(let i = 0; i < lists.length; i++){
            let labels=[];
            try{labels=JSON.parse(lists[i].dataset.labels||"[]");}catch(error){labels=[];}
            lists[i].style.display=labels.indexOf(label)!==-1?'block':'none';
        }
        document.getElementsByClassName("notFind")[0].style.display='none';
    }"""
    html = html.replace(old_filter, new_filter)

    old_update_tag = """function updateShowTag(label){
    if(window.location.hash.slice(1)!=encodeURI(label)){
        window.location.hash="#"+(label);
        setClassDisplay(label);
    }
}"""
    new_update_tag = """function updateShowTag(label){
    let targetHash="#"+encodeURIComponent(label);
    if(window.location.hash!==targetHash){
        window.location.hash=targetHash;
    }
    else{
        setClassDisplay(label);
    }
}"""
    html = html.replace(old_update_tag, new_update_tag)
    html = html.replace(
        'window.location.hash="#"+(searchInput);',
        'window.location.hash="#"+encodeURIComponent(searchInput);',
    )

    html = html.replace(
        "setClassDisplay(decodeURI(window.location.hash.slice(1)));",
        """let initialLabel=window.location.hash.slice(1);
    try{initialLabel=decodeURIComponent(initialLabel);}catch(error){}
    setClassDisplay(initialLabel||"All");""",
    )
    tag_script_pattern = re.compile(
        r'<script id="tag-form-events">.*?</script>',
        re.IGNORECASE | re.DOTALL,
    )
    if tag_script_pattern.search(html):
        html = tag_script_pattern.sub(TAG_FORM_SCRIPT, html, count=1)
    else:
        html = inject_once_before_html_end(
            html, 'id="tag-form-events"', TAG_FORM_SCRIPT
        )
    return html


def inject_seo(html: str, relative: Path) -> str:
    title = title_for_page(html, relative)
    description = description_for_page(html, relative)
    canonical = public_url(relative)
    kind = page_kind(relative)
    og_type = "article" if kind == "post" else "website"
    image = extract_meta(html, "property", "og:image") or "https://github.com/powehi12.png"

    html = set_title(html, title)
    for attribute, key in (
        ("name", "description"),
        ("name", "theme-color"),
        ("name", "color-scheme"),
        ("property", "og:title"),
        ("property", "og:description"),
        ("property", "og:type"),
        ("property", "og:url"),
        ("property", "og:image"),
        ("name", "twitter:card"),
        ("name", "twitter:title"),
        ("name", "twitter:description"),
        ("name", "twitter:image"),
    ):
        html = remove_meta(html, attribute, key)
    html = remove_link_rel(html, "canonical")
    html = remove_link_rel(html, "alternate")

    values = {
        "description": description,
        "og:title": title,
        "og:description": description,
        "og:type": og_type,
        "og:url": canonical,
        "og:image": image,
        "twitter:card": "summary",
        "twitter:title": title,
        "twitter:description": description,
        "twitter:image": image,
    }
    metadata = [
        '<meta name="theme-color" content="#262624">',
        '<meta name="color-scheme" content="dark">',
        f'<meta name="description" content="{html_module.escape(values["description"], quote=True)}">',
        f'<meta property="og:title" content="{html_module.escape(values["og:title"], quote=True)}">',
        f'<meta property="og:description" content="{html_module.escape(values["og:description"], quote=True)}">',
        f'<meta property="og:type" content="{values["og:type"]}">',
        f'<meta property="og:url" content="{html_module.escape(values["og:url"], quote=True)}">',
        f'<meta property="og:image" content="{html_module.escape(values["og:image"], quote=True)}">',
        f'<meta name="twitter:card" content="{values["twitter:card"]}">',
        f'<meta name="twitter:title" content="{html_module.escape(values["twitter:title"], quote=True)}">',
        f'<meta name="twitter:description" content="{html_module.escape(values["twitter:description"], quote=True)}">',
        f'<meta name="twitter:image" content="{html_module.escape(values["twitter:image"], quote=True)}">',
        f'<link rel="canonical" href="{html_module.escape(canonical, quote=True)}">',
        RSS_LINK,
    ]
    html = re.sub(r"[ \t\r\n]+</head>", "\n</head>", html, count=1)
    html = html.replace("</head>", "\n".join(metadata) + "\n</head>", 1)
    return html


def transform_html(source: str, relative: Path, total_pages: int = 1) -> str:
    kind = page_kind(relative)
    html = normalize_theme(source)
    html = normalize_assets(html)
    html = add_body_class(html, f"{kind}-page")
    html = add_skip_link(html)
    html = add_attributes_to_id(html, "header", {"role": "banner"})
    html = add_attributes_to_id(
        html, "content", {"role": "main", "tabindex": "-1"}
    )
    html = add_attributes_to_id(html, "footer", {"role": "contentinfo"})
    html = improve_header(html, kind)
    if kind == "post":
        html = classify_post_title(html)
    if kind == "home":
        html = improve_home_cards(html)
        html = improve_pagination(html, relative, total_pages)
    html = improve_tables(html)
    html = add_noopener(html)
    if kind == "tag":
        html = harden_tag_page(html)
    if kind == "post" and 'id="cmButton"' in html:
        html = inject_once_before_html_end(
            html, 'id="comment-load-recovery"', COMMENT_RECOVERY_SCRIPT
        )
    html = inject_seo(html, relative)
    if not html.endswith("\n"):
        html += "\n"
    return html


def build_404() -> str:
    return f"""<!DOCTYPE html>
<html data-color-mode="dark" data-dark-theme="dark" data-light-theme="dark" lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <meta name="theme-color" content="#262624">
  <meta name="color-scheme" content="dark">
  <meta name="robots" content="noindex,follow">
  <link href="https://mirrors.sustech.edu.cn/cdnjs/ajax/libs/Primer/21.0.7/primer.css" rel="stylesheet">
  <link rel="stylesheet" href="{SITE_ORIGIN}/claude.css?v={ASSET_VERSION}">
  <link rel="icon" href="https://github.com/powehi12.png">
  <meta name="description" content="这个页面不存在，可能已被移动或删除。">
  <meta property="og:title" content="页面未找到 - {SITE_NAME}">
  <meta property="og:description" content="这个页面不存在，可能已被移动或删除。">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{SITE_ORIGIN}/404.html">
  <meta property="og:image" content="https://github.com/powehi12.png">
  <meta name="twitter:card" content="summary">
  <meta name="twitter:title" content="页面未找到 - {SITE_NAME}">
  <meta name="twitter:description" content="这个页面不存在，可能已被移动或删除。">
  <meta name="twitter:image" content="https://github.com/powehi12.png">
  <link rel="canonical" href="{SITE_ORIGIN}/404.html">
  {RSS_LINK}
  <title>页面未找到 - {SITE_NAME}</title>
</head>
<body class="error-page">
  <a class="skip-link" href="#content">跳到主要内容</a>
  <div id="header" role="banner">
    <h1 class="postTitle">页面未找到</h1>
  </div>
  <div id="content" role="main" tabindex="-1">
    <div class="markdown-body">
      <p>这个页面不存在，可能已被移动或删除。</p>
      <p><a class="btn" href="{SITE_ORIGIN}/">返回博客首页</a></p>
    </div>
  </div>
  <div id="footer" role="contentinfo">Copyright © qbyang</div>
</body>
</html>
"""


class HeadTextAudit(HTMLParser):
    """Collect visible text nodes that are invalid directly inside <head>."""

    ALLOWED_TEXT_CONTAINERS = {"title", "style", "script", "noscript", "template"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_head = False
        self.allowed_stack: list[str] = []
        self.unexpected: list[str] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        del attrs
        tag = tag.casefold()
        if tag == "head":
            self.in_head = True
        elif self.in_head and tag in self.ALLOWED_TEXT_CONTAINERS:
            self.allowed_stack.append(tag)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.casefold()
        if tag == "head":
            self.in_head = False
            self.allowed_stack.clear()
        elif self.in_head and tag in self.ALLOWED_TEXT_CONTAINERS:
            for index in range(len(self.allowed_stack) - 1, -1, -1):
                if self.allowed_stack[index] == tag:
                    del self.allowed_stack[index:]
                    break

    def handle_data(self, data: str) -> None:
        if self.in_head and not self.allowed_stack:
            value = normalize_space(data)
            if value:
                self.unexpected.append(value)


def unexpected_head_text(html: str) -> list[str]:
    parser = HeadTextAudit()
    parser.feed(html)
    parser.close()
    return parser.unexpected


class NestedAnchorAudit(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.nested_count = 0

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        del attrs
        if tag.casefold() == "a":
            if self.depth:
                self.nested_count += 1
            self.depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.casefold() == "a" and self.depth:
            self.depth -= 1


def nested_anchor_count(html: str) -> int:
    parser = NestedAnchorAudit()
    parser.feed(html)
    parser.close()
    return parser.nested_count


def build_sitemap(html_paths: list[Path], docs: Path) -> str:
    urls = []
    for path in sorted(html_paths, key=lambda item: item.relative_to(docs).as_posix()):
        relative = path.relative_to(docs)
        if relative.name == "404.html":
            continue
        urls.append(f"  <url><loc>{html_module.escape(public_url(relative))}</loc></url>")
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls)
        + "\n</urlset>\n"
    )


def validate_html(html: str, relative: Path, total_pages: int = 1) -> list[str]:
    errors: list[str] = []
    kind = page_kind(relative)
    expected_class = f"{kind}-page"

    if f"claude.css?v={ASSET_VERSION}" not in html:
        errors.append("missing current stylesheet version")
    if not re.search(
        r'<html\b(?=[^>]*\bdata-color-mode="dark")'
        r'(?=[^>]*\bdata-dark-theme="dark")'
        r'(?=[^>]*\bdata-light-theme="dark")',
        html,
        re.IGNORECASE,
    ):
        errors.append("html root is not fixed to the dark theme")
    if extract_meta(html, "name", "theme-color") != "#262624":
        errors.append("theme-color does not match the dark background")
    if extract_meta(html, "name", "color-scheme") != "dark":
        errors.append("color-scheme meta is not dark")
    if "github-light" in html:
        errors.append("contains a light-mode comment theme")
    if not re.search(
        rf"<body[^>]*\bclass\s*=\s*[\"'][^\"']*\b{re.escape(expected_class)}\b",
        html,
        re.IGNORECASE,
    ):
        errors.append(f"missing body class {expected_class}")
    if 'class="skip-link"' not in html:
        errors.append("missing skip link")
    if not re.search(r'<[^>]+\bid=["\']content["\'][^>]*\brole=["\']main', html):
        errors.append("missing main landmark")
    if len(re.findall(r'\brel=["\']canonical["\']', html, re.IGNORECASE)) != 1:
        errors.append("canonical link count is not one")
    if RSS_LINK not in html:
        errors.append("missing RSS autodiscovery")
    for attribute, key in (
        ("name", "description"),
        ("name", "theme-color"),
        ("name", "color-scheme"),
        ("property", "og:title"),
        ("property", "og:description"),
        ("property", "og:type"),
        ("property", "og:url"),
        ("property", "og:image"),
        ("name", "twitter:card"),
        ("name", "twitter:title"),
        ("name", "twitter:description"),
        ("name", "twitter:image"),
    ):
        count = len(matching_meta_tags(html, attribute, key))
        if count != 1:
            errors.append(f"{key} meta count is {count}, expected one")
    stray_head_text = unexpected_head_text(html)
    if stray_head_text:
        errors.append(
            "head contains unexpected text: "
            + normalize_space(stray_head_text[0])[:80]
        )
    if nested_anchor_count(html):
        errors.append("contains nested anchor elements")
    if re.search(r"mathjax@3/", html, re.IGNORECASE):
        errors.append("contains mutable MathJax major-version URL")
    if "markdown-accessiblity-table" in html:
        errors.append("contains legacy table wrapper")
    if re.search(r"<th\b(?![^>]*\bscope\s*=)[^>]*>", html, re.IGNORECASE):
        errors.append("table header missing scope")
    for anchor in re.findall(
        r"<a\b[^>]*\btarget\s*=\s*[\"']_blank[\"'][^>]*>", html, re.I
    ):
        if not re.search(r'\brel=["\'][^"\']*\bnoopener\b', anchor, re.I):
            errors.append("target=_blank link missing noopener")
            break

    if kind == "home" and not re.search(
        r'<h1\b[^>]*class=["\'][^"\']*\btitle-left\b', html, re.I
    ):
        errors.append("home page missing real h1")
    if kind == "home" and '<nav class="SideNav' in html:
        if 'class="post-card-link ' not in html:
            errors.append("home page cards do not expose a dedicated article link")
        if re.search(r"<object>\s*<a\b", html, re.IGNORECASE):
            errors.append("home page cards retain object-wrapped label links")
    page_number = pagination_page_number(relative)
    if page_number and total_pages > 1:
        expected_indicator = (
            f'aria-label="第 {page_number} 页，共 {total_pages} 页">'
            f"{page_number} / {total_pages}</span>"
        )
        if expected_indicator not in html:
            errors.append("pagination is missing the current and total page count")
    if kind == "tag":
        required = (
            '<h1 class="tagTitle"',
            'id="site-search-form"',
            'role="status"',
            "showLabels.dataset.tag=label;",
            'showLabels.addEventListener("click"',
            'setAttribute("aria-pressed"',
            'tagTitle.textContent="Tag #"',
            'tagTitle.textContent="Search #"',
            "notFind.textContent=",
            'window.addEventListener("hashchange"',
        )
        for marker in required:
            if marker not in html:
                errors.append(f"tag page missing hardening marker: {marker}")
        if re.search(
            r"\b(?:tagTitle|notFind)\b[^\r\n;]{0,180}\.innerHTML\b",
            html,
            re.IGNORECASE,
        ):
            errors.append("tag page retains user-controlled innerHTML")
        if 'setAttribute("onclick"' in html:
            errors.append("tag page retains generated inline onclick")
    if kind == "post":
        if f"collapsible-toc.js?v={ASSET_VERSION}" not in html:
            errors.append("post missing current enhancement script")
        if classify_post_title(html) != html:
            errors.append("post title is missing its current length class")
        if 'id="cmButton"' in html:
            for marker in (
                'id="comment-load-recovery"',
                'script.addEventListener("error"',
                "10000",
                "重试加载评论",
            ):
                if marker not in html:
                    errors.append(f"comment recovery missing marker: {marker}")
            if not re.search(
                r'script\.setAttribute\("theme",\s*"github-dark"\)', html
            ):
                errors.append("comment widget is not using github-dark")
    if kind == "error" and not re.search(
        r'<meta\b(?=[^>]*\bname=["\']robots["\'])[^>]*\bnoindex\b',
        html,
        re.IGNORECASE,
    ):
        errors.append("404 page is not noindex")
    return errors


def expected_outputs(docs: Path) -> dict[Path, str]:
    outputs: dict[Path, str] = {}
    html_paths = sorted(docs.rglob("*.html"))
    total_pages = pagination_total_pages(html_paths, docs)
    for path in html_paths:
        if path.name == "404.html":
            continue
        relative = path.relative_to(docs)
        outputs[path] = transform_html(
            path.read_text(encoding="utf-8"), relative, total_pages
        )
    outputs[docs / "404.html"] = build_404()

    sitemap_paths = list(outputs)
    outputs[docs / "sitemap.xml"] = build_sitemap(sitemap_paths, docs)
    outputs[docs / "robots.txt"] = (
        "User-agent: *\n"
        "Allow: /\n"
        f"Sitemap: {SITE_ORIGIN}/sitemap.xml\n"
    )
    outputs[docs / ".nojekyll"] = ""
    return outputs


def main() -> int:
    args = parse_args()
    docs = args.docs.resolve()
    if not docs.is_dir():
        print(f"Generated site directory does not exist: {docs}", file=sys.stderr)
        return 2
    if not (docs / "index.html").is_file() or not (docs / "tag.html").is_file():
        print(f"Expected index.html and tag.html in {docs}", file=sys.stderr)
        return 2

    outputs = expected_outputs(docs)
    total_pages = pagination_total_pages(
        [path for path in outputs if path.suffix == ".html"], docs
    )
    drift: list[str] = []
    validation_errors: list[str] = []

    for path, expected in outputs.items():
        if path.suffix == ".html":
            relative = path.relative_to(docs)
            for error in validate_html(expected, relative, total_pages):
                validation_errors.append(f"{relative.as_posix()}: {error}")
        actual = path.read_text(encoding="utf-8") if path.exists() else None
        if actual != expected:
            drift.append(path.relative_to(docs).as_posix())
            if not args.check:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(expected, encoding="utf-8", newline="\n")

    if validation_errors:
        print("Post-processing validation failed:", file=sys.stderr)
        for error in validation_errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    if args.check and drift:
        print("Generated site is not fully post-processed:", file=sys.stderr)
        for relative in drift:
            print(f"  - {relative}", file=sys.stderr)
        return 1

    action = "Validated" if args.check else "Updated"
    html_count = sum(path.suffix == ".html" for path in outputs)
    print(
        f"{action} {html_count} HTML pages plus sitemap.xml, robots.txt, and .nojekyll."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
