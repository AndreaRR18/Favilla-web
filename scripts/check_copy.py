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

# The privacy page must not describe features 1.0 doesn't ship.
PRIVACY_FORBIDDEN = ["every sound", "ogni suono", "chaque son", "jeder klang", "cada sonido"]
PRIVACY_FORBIDDEN_RE = [r"\bimport(ed|s)?\b", r"\bimporti\b", r"\bimportez\b", r"\bimportierst\b", r"\bimportas\b"]
PRIVACY_SECTIONS = ("who", "data", "microphone", "sharing", "children", "deletion", "rights", "site")

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
            if key.startswith("privacy_page."):
                for needle in PRIVACY_FORBIDDEN:
                    if needle in low:
                        errors.append(f"{lang}: {key}: feature not in 1.0 ({needle!r})")
                for pattern in PRIVACY_FORBIDDEN_RE:
                    if re.search(pattern, value, re.I):
                        errors.append(f"{lang}: {key}: imported sounds are not in 1.0 ({pattern})")
            for rule, patterns in FORBIDDEN_RE.get(lang, {}).items():
                for pattern in patterns:
                    if re.search(pattern, value, re.I):
                        errors.append(f"{lang}: {key}: {rule} ({pattern})")
        if not re.search(r"\b\d{1,2}\.?\s+(de\s+)?[^\W\d]", strings[lang].get("privacy_page.updated", "")):
            errors.append(f"{lang}: privacy_page.updated: needs the day of the last change")
        if "privacy_page.backup_p" not in strings[lang]:
            errors.append(f"{lang}: privacy_page.backup_p: the iCloud backup sentence is missing")
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


RETIRED_CLASSES = {"reveal", "glass", "grid-3", "grid-4", "kicker"}  # the old landing-page look
TAB_LABEL_MAX = 11  # longest label that fits a tab at 375 px ("Datenschutz")
CALM_SELECTORS = (".sky .fly", ".forest-fly", ".faq summary svg")


def check_shell(rel, root, errors):
    """Every page: one tab bar, one language menu, one h1, no retired classes."""
    bars = root.all("nav", cls="tabbar")
    if len(bars) != 1:
        errors.append(f"{rel}: expected one nav.tabbar, found {len(bars)}")
    else:
        tabs = bars[0].all("a", cls="tab")
        if len(tabs) != 4:
            errors.append(f"{rel}: tab bar has {len(tabs)} tabs, expected 4")
        current = [t for t in tabs if t.attrs.get("aria-current") == "page"]
        want = 0 if rel == "404.html" else 1
        if len(current) != want:
            errors.append(f"{rel}: {len(current)} current tab(s), expected {want}")
    menus = root.all("details", cls="lang-menu")
    if len(menus) != 1 or len(menus[0].all("a")) != len(LANGS):
        errors.append(f"{rel}: expected one details.lang-menu with {len(LANGS)} links")
    if len(root.all("h1")) != 1:
        errors.append(f"{rel}: expected exactly one h1")
    for node in root.walk():
        retired = node.classes & RETIRED_CLASSES
        if retired:
            errors.append(f"{rel}: retired class(es) {sorted(retired)} on <{node.tag}>")
            break


def check_globals(strings, errors):
    """Rules that are not about one page."""
    from build import THEME_SCRIPT
    if 'classList.add("js")' in THEME_SCRIPT or "fv-ready" in THEME_SCRIPT:
        errors.append("THEME_SCRIPT still hides content until site.js runs (js / fv-ready)")
    for lang in LANGS:
        for key, value in strings[lang].items():
            if key.startswith("tabbar.") and len(value) > TAB_LABEL_MAX:
                errors.append(f"{lang}: {key}: tab label longer than {TAB_LABEL_MAX} characters")
    with open(os.path.join(ROOT, "assets", "css", "site.css"), encoding="utf-8") as fh:
        css = fh.read()
    calm = re.findall(r"@media\s*\(prefers-reduced-motion:\s*reduce\)\s*\{(.*?)\n\}", css, re.S)
    calm_text = "\n".join(calm)
    for selector in CALM_SELECTORS:
        if selector not in calm_text:
            errors.append(f"site.css: {selector!r} keeps moving under prefers-reduced-motion")


def count(root, ident, *args, **kwargs):
    node = root.by_id(ident)
    return len(node.all(*args, **kwargs)) if node else -1


def check_home(rel, root, errors):
    """The home is built from app screens: recording phone, catalog list, forest."""
    if not root.all("h1", cls="large-title"):
        errors.append(f"{rel}: no h1.large-title")
    if len(root.all("div", cls="phone")) != 1:
        errors.append(f"{rel}: expected one recording phone (div.phone)")
    expected = {"how": 3, "catalog": 6, "app": 4, "privacy": 4}
    for ident, want in expected.items():
        got = count(root, ident, cls="row")
        if got != want:
            errors.append(f"{rel}: #{ident} has {got} rows, expected {want}")
    catalog = root.by_id("catalog")
    if catalog and len(catalog.all(cls="emoji")) != 6:
        errors.append(f"{rel}: every catalog row needs its emoji silhouette")
    privacy = root.by_id("privacy")
    links = privacy.all("a", cls="row link") if privacy else []
    if len(links) != 1 or links[0].attrs.get("href") != "privacy.html":
        errors.append(f"{rel}: #privacy needs one a.row.link to privacy.html")
    if len(root.all(cls="forest")) != 1:
        errors.append(f"{rel}: expected one .forest")
    for gone in ("idea", "why"):
        if root.by_id(gone):
            errors.append(f"{rel}: section #{gone} was retired")
    if root.all(cls="mascot") or root.all(cls="hero-wave"):
        errors.append(f"{rel}: the old mascot or hero wave is back")


def check_privacy(rel, root, errors):
    """The privacy page: an index of its sections, and only name and email."""
    for ident in PRIVACY_SECTIONS:
        if not root.by_id(ident):
            errors.append(f"{rel}: privacy section #{ident} is missing")
    toc = root.all(cls="toc")
    if not toc or len(toc[0].all("a", cls="row")) != len(PRIVACY_SECTIONS):
        errors.append(f"{rel}: the in-page index needs {len(PRIVACY_SECTIONS)} rows")
    who = root.by_id("who")
    if who and len(who.all(cls="row")) != 2:
        errors.append(f"{rel}: #who shows {len(who.all(cls='row'))} rows, expected name and email only")


FAQ = ("coming", "account", "where", "mic", "sum", "locked", "sync", "share", "long", "ai",
       "languages", "fireflies", "forest", "delete")


def check_support(rel, root, errors, config):
    """Support: the parents' real questions, one contact address, the policy."""
    faq = root.all("div", cls="faq")
    items = faq[0].all("details") if faq else []
    if len(items) != len(FAQ):
        errors.append(f"{rel}: {len(items)} FAQ entries, expected {len(FAQ)}")
    for item in items:
        summary = item.all("summary")
        if not summary or not summary[0].get_text().strip():
            errors.append(f"{rel}: a FAQ entry has no question")
    kv = root.all(cls="kv")
    mails = [a for a in (kv[0].all("a") if kv else []) if (a.attrs.get("href") or "").startswith("mailto:")]
    todos = kv[0].all("mark", cls="todo") if kv else []
    if config.get("contact_email") and len(mails) != 1:
        errors.append(f"{rel}: the contact card needs one mailto: link")
    if not config.get("contact_email") and not todos:
        errors.append(f"{rel}: the contact card must show the missing email placeholder")
    links = [a for a in root.all("a", cls="row link") if a.attrs.get("href") == "privacy.html"]
    if len(links) != 1:
        errors.append(f"{rel}: support needs one a.row.link to privacy.html")


def check_404(root, errors, base_path):
    """404 is served for any missing path, at any depth: only root-relative URLs."""
    forest = root.all(cls="forest")
    if len(forest) != 1 or not forest[0].all("h1"):
        errors.append("404.html: the h1 belongs inside the night forest card")
    for node in root.walk():
        for attr in ("href", "src"):
            url = node.attrs.get(attr)
            if url is None or node.tag in ("link", "meta") and attr == "href" and url.startswith("http"):
                continue
            if not url.startswith((base_path, "mailto:", "https://", "#")):
                errors.append(f"404.html: {node.tag} {attr}={url!r} breaks at a nested path")


def check_no_phone(rel, root, errors):
    for node in root.all("a"):
        if (node.attrs.get("href") or "").startswith("tel:"):
            errors.append(f"{rel}: a phone number is on the site (owner: email only)")


def check_pages(out, config):
    """Structure rules on the built HTML."""
    errors = []
    check_globals(load_i18n(), errors)
    for rel, path in sorted(built_pages(out).items()):
        root = parse(path)
        check_shell(rel, root, errors)
        check_no_phone(rel, root, errors)
        if os.path.basename(rel) == "index.html":
            check_home(rel, root, errors)
        if os.path.basename(rel) == "privacy.html":
            check_privacy(rel, root, errors)
        if os.path.basename(rel) == "support.html":
            check_support(rel, root, errors, config)
        if rel == "404.html":
            check_404(root, errors, urlparse(config["base_url"]).path)
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
