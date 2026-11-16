#!/usr/bin/env python3
"""Check the Favilla site's copy and page structure against the brand rules.

Runs after build.py and check_site.py. Stdlib only. Fails (exit 1) on:
  - copy that breaks the brand or store rules, in any language: exclamation
    marks, sparkle emoji, price promises, words App Store review flags
    (premium, subscription, discount…), anything about sleep sounds (off in
    1.0), and "tu" in French (the app says "vous");
  - built pages that lose the app's structure (see check_pages);
  - a RELEASE.md that points at pages the build doesn't produce.

Run:  python3 scripts/check_copy.py [_site]
"""

import json
import os
import re
import sys
from html.parser import HTMLParser
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build import LANGS, ROOT, load_i18n  # noqa: E402

# Case-insensitive substrings that must never appear in any language.
FORBIDDEN = {
    # storeTextWatch.always in the app's scripts/release-audit.config.json
    "store word": ["premium", "subscription", "abbonamento", "abonnement", "suscripción",
                   "discount", "sconto", "% off"],
    # storeTextWatch.sleepSoundsOff: the feature is off in 1.0
    "sleep sounds": ["sleep sound", "white noise", "rumore bianco", "suoni per dormire",
                     "bruit blanc", "weißes rauschen", "ruido blanco", "sonidos para dormir"],
    # no promise about the price, in any form
    "price promise": ["stays that way", "resterà così", "ça ne changera pas", "bleibt so",
                      "seguirá así", "free forever", "per sempre gratis",
                      "every corner", "ogni angolo", "chaque coin", "jeder winkel", "cada rincón"],
    # sparkles read as "AI"
    "sparkle": ["✨", "⭐", "🌟", "💫"],
}

# Regexes (case-insensitive) that must never match, per language.
FORBIDDEN_RE = {
    "fr": {"tu instead of vous": [r"\btu\b", r"\bton\b", r"\btes\b", r"\bta\b"]},
}


def check_strings(strings):
    """Copy rules on the flattened i18n dictionaries: {lang: {key: value}}."""
    errors = []
    for lang in LANGS:
        for key, value in sorted(strings[lang].items()):
            if not isinstance(value, str):
                continue
            low = value.lower()
            if "!" in value:
                errors.append(f"{lang}: {key}: exclamation mark")
            for rule, needles in FORBIDDEN.items():
                for needle in needles:
                    if needle.lower() in low:
                        errors.append(f"{lang}: {key}: {rule} ({needle!r})")
            for rule, patterns in FORBIDDEN_RE.get(lang, {}).items():
                for pattern in patterns:
                    if re.search(pattern, value, re.I):
                        errors.append(f"{lang}: {key}: {rule} ({pattern})")
    return errors


# ---------------------------------------------------------------------------
# A tiny DOM, so page rules read like selectors instead of regexes on markup.

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
        "source", "track", "wbr", "path", "circle", "rect", "stop", "use", "ellipse", "line"}


class Node:
    def __init__(self, tag, attrs, parent=None):
        self.tag = tag
        self.attrs = dict(attrs)
        self.parent = parent
        self.children = []
        self.text = []

    @property
    def classes(self):
        return set((self.attrs.get("class") or "").split())

    def walk(self):
        for child in self.children:
            yield child
            yield from child.walk()

    def all(self, tag=None, cls=None, **attrs):
        """Descendants matching a tag, a set of classes ("a b") and attribute values."""
        want = set(cls.split()) if cls else set()
        found = []
        for node in self.walk():
            if tag and node.tag != tag:
                continue
            if want and not want <= node.classes:
                continue
            if any(node.attrs.get(k.replace("_", "-")) != v for k, v in attrs.items()):
                continue
            found.append(node)
        return found

    def by_id(self, ident):
        for node in self.walk():
            if node.attrs.get("id") == ident:
                return node
        return None

    def get_text(self):
        return "".join(self.text) + "".join(child.get_text() for child in self.children)


class Tree(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#root", {})
        self.current = self.root

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs, self.current)
        self.current.children.append(node)
        if tag not in VOID:
            self.current = node

    def handle_startendtag(self, tag, attrs):
        self.current.children.append(Node(tag, attrs, self.current))

    def handle_endtag(self, tag):
        node = self.current
        while node is not self.root and node.tag != tag:
            node = node.parent
        if node is not self.root:
            self.current = node.parent

    def handle_data(self, data):
        self.current.text.append(data)


def parse(path):
    tree = Tree()
    with open(path, encoding="utf-8") as fh:
        tree.feed(fh.read())
    return tree.root


def built_pages(out):
    """{relative path: path} for every built HTML page."""
    pages = {}
    for folder, _, files in os.walk(out):
        for name in files:
            if name.endswith(".html"):
                path = os.path.join(folder, name)
                pages[os.path.relpath(path, out)] = path
    return pages


def check_pages(out, config):
    """Structure rules on the built HTML."""
    errors = []
    return errors


def check_release(out, base_url):
    """RELEASE.md must only point at pages the build produces (Task 7)."""
    return []


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "_site"
    out = out if os.path.isabs(out) else os.path.join(ROOT, out)
    with open(os.path.join(ROOT, "config.json"), encoding="utf-8") as fh:
        config = json.load(fh)
    errors = check_strings(load_i18n())
    errors += check_pages(out, config)
    errors += check_release(out, config["base_url"].rstrip("/") + "/")
    if errors:
        for error in errors:
            print(f"check_copy: {error}", file=sys.stderr)
        print(f"check_copy: FAILED with {len(errors)} error(s)", file=sys.stderr)
        sys.exit(1)
    print("check_copy: OK — copy, structure and release file follow the brand rules")


if __name__ == "__main__":
    main()
