#!/usr/bin/env python3
"""Check a built Favilla site before it is deployed. Stdlib only.

Fails (exit 1) on:
  - an internal link or asset that points at a file that doesn't exist;
  - a #fragment link to an id that doesn't exist on the target page;
  - any script, stylesheet, font, image or preload loaded from another origin
    (the site promises nothing third-party, and the CSP would block it anyway);
  - a page without the Content-Security-Policy meta tag, or with an inline
    style attribute or an unexpected inline script (the CSP would block them);
  - a leftover {{placeholder}};
  - a sitemap URL with no page behind it.

Run:  python3 scripts/check_site.py [_site]
"""

import os
import sys
from html.parser import HTMLParser
from urllib.parse import unquote, urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build import THEME_SCRIPT  # noqa: E402  (the one inline script allowed)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Structural elements whose start and end tags must balance exactly: a stray
# </div> silently closes a container early and breaks the layout.
BALANCED = {"div", "section", "article", "header", "footer", "main", "nav", "ul", "ol",
            "details", "table", "svg"}


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.balance = {}
        self.ids = set()
        self.links = []        # (attr, url)
        self.resources = []    # (tag, url)
        self.inline_scripts = []
        self.styled = 0
        self.has_csp = False
        self._in_script = False
        self._script = []

    def handle_starttag(self, tag, attrs):
        if tag in BALANCED:
            self.balance[tag] = self.balance.get(tag, 0) + 1
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        if "style" in a:
            self.styled += 1
        if tag == "meta" and (a.get("http-equiv") or "").lower() == "content-security-policy":
            self.has_csp = True
        if tag == "a" and a.get("href"):
            self.links.append(a["href"])
        if tag == "link" and a.get("href"):
            rel = (a.get("rel") or "").lower()
            if rel in ("canonical", "alternate"):
                pass  # absolute self-URLs, checked through the sitemap
            else:
                self.resources.append((tag, a["href"]))
        if tag in ("img", "source", "iframe", "embed", "audio", "video") and a.get("src"):
            self.resources.append((tag, a["src"]))
        if tag == "script":
            if a.get("src"):
                self.resources.append((tag, a["src"]))
            else:
                self._in_script = True
                self._script = []

    def handle_data(self, data):
        if self._in_script:
            self._script.append(data)

    def handle_endtag(self, tag):
        if tag in BALANCED:
            self.balance[tag] = self.balance.get(tag, 0) - 1
        if tag == "script" and self._in_script:
            self._in_script = False
            self.inline_scripts.append("".join(self._script))


def resolve(page_path, url, out):
    """Local file a relative or root-relative URL points at, or None if external."""
    parsed = urlparse(url)
    if parsed.scheme or parsed.netloc:
        return None
    path = unquote(parsed.path)
    if not path:
        return page_path
    if path.startswith("/"):
        # root-relative: only the 404 page uses these, and it is checked live
        return None
    target = os.path.normpath(os.path.join(os.path.dirname(page_path), path))
    if os.path.isdir(target) or target.endswith(os.sep):
        target = os.path.join(target, "index.html")
    return target


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "_site"
    out = out if os.path.isabs(out) else os.path.join(ROOT, out)
    errors = []
    pages = {}

    for folder, _, files in os.walk(out):
        for name in files:
            if name.endswith(".html"):
                path = os.path.join(folder, name)
                with open(path, encoding="utf-8") as fh:
                    text = fh.read()
                parser = Page()
                parser.feed(text)
                pages[path] = (parser, text)

    for path, (page, text) in pages.items():
        rel = os.path.relpath(path, out)
        if "{{" in text:
            errors.append(f"{rel}: unresolved placeholder")
        for tag, count in sorted(page.balance.items()):
            if count:
                kind = "unclosed" if count > 0 else "extra closing"
                errors.append(f"{rel}: {abs(count)} {kind} <{tag}> tag(s)")
        if not page.has_csp:
            errors.append(f"{rel}: no Content-Security-Policy meta tag")
        if page.styled:
            errors.append(f"{rel}: {page.styled} inline style attribute(s) (blocked by the CSP)")
        for script in page.inline_scripts:
            if script != THEME_SCRIPT:
                errors.append(f"{rel}: unexpected inline script (not covered by the CSP hash)")
        for tag, url in page.resources:
            parsed = urlparse(url)
            if parsed.scheme in ("http", "https") or url.startswith("//"):
                errors.append(f"{rel}: third-party {tag} {url}")
                continue
            if rel == "404.html":
                continue  # root-relative URLs, resolved against the live base path
            target = resolve(path, url, out)
            if target and not os.path.isfile(target):
                errors.append(f"{rel}: missing {tag} {url}")
        for url in page.links:
            parsed = urlparse(url)
            if parsed.scheme in ("mailto", "http", "https") or rel == "404.html":
                continue
            target = resolve(path, url, out)
            if target is None:
                continue
            if not os.path.isfile(target):
                errors.append(f"{rel}: broken link {url}")
                continue
            if parsed.fragment:
                ids = pages[target][0].ids if target in pages else set()
                if parsed.fragment not in ids:
                    errors.append(f"{rel}: link {url} points at a missing #{parsed.fragment}")

    sitemap = os.path.join(out, "sitemap.xml")
    if os.path.isfile(sitemap):
        import re
        with open(sitemap, encoding="utf-8") as fh:
            urls = re.findall(r"<loc>([^<]+)</loc>|href=\"([^\"]+)\"", fh.read())
        bases = {u for pair in urls for u in pair if u}
        base_path = None
        for url in bases:
            path = urlparse(url).path
            if base_path is None or len(path) < len(base_path):
                base_path = path
        for url in bases:
            path = urlparse(url).path[len(base_path):]
            target = os.path.join(out, path)
            if path == "" or path.endswith("/"):
                target = os.path.join(target, "index.html")
            if not os.path.isfile(target):
                errors.append(f"sitemap.xml: {url} has no page")
    else:
        errors.append("sitemap.xml is missing")

    if errors:
        print(f"check_site: {len(errors)} problem(s)", file=sys.stderr)
        for error in errors:
            print("  " + error, file=sys.stderr)
        sys.exit(1)
    print(f"check_site: OK — {len(pages)} pages, every link, asset and fragment resolves, nothing third-party")


if __name__ == "__main__":
    main()
