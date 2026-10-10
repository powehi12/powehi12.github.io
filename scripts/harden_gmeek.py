"""Apply the blog's security policy to the exact pinned upstream Gmeek source.

Run after copying the blog files into the generator checkout. Fail closed if
upstream changes: review the new revision before updating these fingerprints.
"""
import argparse
import hashlib
from pathlib import Path

POLICY = "powehi12-only-v1"
SOURCE_HASHES = {
    "Gmeek.py": "83e4953943b97bab074228e20aef3f0ac88897bb9c5db0595a40db27e7869343",
    "templates/post.html": "a92a39fef6c0a456c94d7c713a3f58f04bc69b6fd9a809ad18605225373ce376",
    "templates/plist.html": "bca2d5a1b82e61c7dc712426c0e89c698025874cec103304fd6d6d416eb91364",
}


def replace_once(source, before, after):
    if source.count(before) != 1:
        raise ValueError("Pinned Gmeek source no longer matches a security patch")
    return source.replace(before, after, 1)


def harden_tree(root):
    root = Path(root)
    sources = {}
    # Validate all inputs before modifying any file. read_text normalizes CRLF.
    for name, expected in SOURCE_HASHES.items():
        source = (root / name).read_text(encoding="utf-8")
        if hashlib.sha256(source.encode("utf-8")).hexdigest() != expected:
            raise ValueError(f"Unexpected upstream source: {name}")
        sources[name] = source

    source = sources["Gmeek.py"]
    source = replace_once(
        source,
        '        self.blogBase={**dconfig,**config}.copy()\n',
        '        self.blogBase={**dconfig,**config}.copy()\n'
        f'        self.blogBase["gmeekSecurityPolicy"] = "{POLICY}"\n',
    )
    source = replace_once(
        source,
        '    def addOnePostJson(self,issue):\n        if len(issue.labels)>=1:\n',
        '    @staticmethod\n'
        '    def isTrustedIssue(issue):\n'
        '        # Author and content come from the same fetched Issue object.\n'
        '        data = issue.raw_data\n'
        '        login = (data.get("user") or {}).get("login")\n'
        '        return (isinstance(login, str)\n'
        '                and login.casefold() == "powehi12"\n'
        '                and data.get("state") == "open"\n'
        '                and "pull_request" not in data)\n'
        '\n'
        '    def addOnePostJson(self,issue):\n'
        '        if not self.isTrustedIssue(issue):\n'
        '            return None\n'
        '        if len(issue.labels)>=1:\n',
    )
    source = replace_once(
        source,
        '            listJsonName=self.addOnePostJson(issue)\n'
        '            self.createPostHtml(self.blogBase[listJsonName]["P"+number_str])',
        '            listJsonName=self.addOnePostJson(issue)\n'
        '            if listJsonName is None:\n'
        '                raise ValueError("Only labeled Issues authored by powehi12 can be published")\n'
        '            self.createPostHtml(self.blogBase[listJsonName]["P"+number_str])',
    )
    source = replace_once(
        source,
        'if not os.path.exists("blogBase.json"):\n',
        'def cache_has_current_policy():\n'
        '    try:\n'
        '        with open("blogBase.json", encoding="utf-8") as cache_file:\n'
        '            cache = json.load(cache_file)\n'
        f'        return cache.get("gmeekSecurityPolicy") == "{POLICY}"\n'
        '    except (OSError, ValueError, AttributeError):\n'
        '        return False\n'
        '\n'
        '# Never carry pre-policy articles or single pages into incremental output.\n'
        'if not cache_has_current_policy():\n',
    )
    sources["Gmeek.py"] = source

    # Escape text at its output context, preserving raw metadata and trusted HTML.
    sources["templates/post.html"] = sources["templates/post.html"].replace(
        "{{ blogBase['postTitle'] }}", "{{ blogBase['postTitle']|e }}"
    )
    source = sources["templates/plist.html"]
    source = replace_once(
        source,
        'document.getElementById("{{ blogBase[\'singeListJson\'][num][\'postTitle\'] }}")',
        'document.getElementById({{ blogBase[\'singeListJson\'][num][\'postTitle\']|tojson }})',
    )
    source = source.replace(
        "{{ blogBase['singeListJson'][num]['postTitle'] }}",
        "{{ blogBase['singeListJson'][num]['postTitle']|e }}",
    )
    sources["templates/plist.html"] = source
    for name, source in sources.items():
        (root / name).write_text(source, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("generator", type=Path)
    harden_tree(parser.parse_args().generator)
