#!/usr/bin/env python3
"""Build the Favilla static website.

Renders templates/*.html for every language in i18n/*.json, copies assets,
generates raster icons (stdlib-only PNG writer), and emits sitemap/robots.

Design tokens mirror the iOS DesignSystem package (dark-first, warm amber,
#C4923F on #100B08). The mark is the Favilla symbol exactly as the app draws
it in FireflyField: a bright dot with three flat concentric rings. Never
sparkle icons (they read as "AI") and never flames or insect drawings.
Run:  python3 scripts/build.py [--out _site] [--dry-run]
"""

import argparse
import base64
import hashlib
import html
import json
import math
import os
import re
import shutil
import struct
import sys
import zlib
from datetime import date
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LANGS = ["en", "it", "fr", "de", "es"]
LANG_NAMES = {"en": "English", "it": "Italiano", "fr": "Français", "de": "Deutsch", "es": "Español"}
LANG_CODES = {"en": "EN", "it": "IT", "fr": "FR", "de": "DE", "es": "ES"}
OG_LOCALES = {"en": "en_US", "it": "it_IT", "fr": "fr_FR", "de": "de_DE", "es": "es_ES"}
PAGES = {"index": "index.html", "privacy": "privacy.html", "support": "support.html", "404": "404.html"}

# The wordmark as it appears in nav and footer: lowercase "favilla" with the
# dot of the i in amber. The dotless i keeps the font's own dot out of the way.
WORDMARK = (
    '<span class="wordmark">fav'
    '<span class="wordmark-i">ı<span class="wordmark-dot"></span></span>'
    'lla</span>'
)

# The only inline script: it sets the theme before first paint (no flash of the
# wrong theme) and marks the page as scripted (html.js), so `.reveal` content
# is hidden for its fade-in. If site.js hasn't taken over (html.fv-ready)
# within 3 s — blocked, failed or broken — it un-hides everything. Its hash
# goes into the
# Content-Security-Policy, so the policy can forbid every other inline script.
THEME_SCRIPT = (
    '(function(){var d=document.documentElement;d.classList.add("js");'
    'setTimeout(function(){if(!d.classList.contains("fv-ready"))d.classList.remove("js");},3000);'
    'try{var c=localStorage.getItem("fv-theme");'
    'var l=c==="light"||(!c&&matchMedia("(prefers-color-scheme: light)").matches);'
    'd.dataset.theme=l?"light":"dark";}catch(e){d.dataset.theme="dark";}})();'
)
THEME_SCRIPT_HASH = base64.b64encode(hashlib.sha256(THEME_SCRIPT.encode("utf-8")).digest()).decode("ascii")

# Content-Security-Policy, delivered as a <meta> tag because GitHub Pages
# cannot send custom headers. Everything is first-party: fonts are self-hosted,
# there are no analytics, no embeds and no forms. (`frame-ancestors` is ignored
# in a <meta> policy, so it is not listed.)
CSP = "; ".join([
    "default-src 'none'",
    f"script-src 'self' 'sha256-{THEME_SCRIPT_HASH}'",
    "style-src 'self'",
    "font-src 'self'",
    "img-src 'self'",
    "connect-src 'none'",
    "manifest-src 'self'",
    "base-uri 'none'",
    "form-action 'none'",
])

# Six catalog tales shown on the landing page (titles and credits localized).
TALES = [
    {
        "titles": {"it": "Cappuccetto Rosso", "en": "Little Red Riding Hood", "fr": "Le Petit Chaperon rouge", "de": "Rotkäppchen", "es": "Caperucita Roja"},
        "author": {"it": "Charles Perrault", "en": "Charles Perrault", "fr": "Charles Perrault", "de": "Charles Perrault", "es": "Charles Perrault"},
        "country": {"it": "Francia", "en": "France", "fr": "France", "de": "Frankreich", "es": "Francia"},
        "year": {"it": "1697", "en": "1697", "fr": "1697", "de": "1697", "es": "1697"},
    },
    {
        "titles": {"it": "Il Brutto Anatroccolo", "en": "The Ugly Duckling", "fr": "Le Vilain Petit Canard", "de": "Das hässliche Entlein", "es": "El patito feo"},
        "author": {"it": "Hans Christian Andersen", "en": "Hans Christian Andersen", "fr": "Hans Christian Andersen", "de": "Hans Christian Andersen", "es": "Hans Christian Andersen"},
        "country": {"it": "Danimarca", "en": "Denmark", "fr": "Danemark", "de": "Dänemark", "es": "Dinamarca"},
        "year": {"it": "1843", "en": "1843", "fr": "1843", "de": "1843", "es": "1843"},
    },
    {
        "titles": {"it": "Hansel e Gretel", "en": "Hansel and Gretel", "fr": "Hansel et Gretel", "de": "Hänsel und Gretel", "es": "Hansel y Gretel"},
        "author": {"it": "Fratelli Grimm", "en": "The Brothers Grimm", "fr": "Frères Grimm", "de": "Brüder Grimm", "es": "Hermanos Grimm"},
        "country": {"it": "Germania", "en": "Germany", "fr": "Allemagne", "de": "Deutschland", "es": "Alemania"},
        "year": {"it": "1812", "en": "1812", "fr": "1812", "de": "1812", "es": "1812"},
    },
    {
        "titles": {"it": "La Lepre e la Tartaruga", "en": "The Tortoise and the Hare", "fr": "Le Lièvre et la Tortue", "de": "Der Hase und die Schildkröte", "es": "La liebre y la tortuga"},
        "author": {"it": "Esopo", "en": "Aesop", "fr": "Ésope", "de": "Äsop", "es": "Esopo"},
        "country": {"it": "Grecia antica", "en": "Ancient Greece", "fr": "Grèce antique", "de": "Antikes Griechenland", "es": "Antigua Grecia"},
        "year": {"it": "VI sec. a.C.", "en": "6th century BC", "fr": "VIᵉ s. av. J.-C.", "de": "6. Jh. v. Chr.", "es": "s. VI a. C."},
    },
    {
        "titles": {"it": "Momotaro, il Bambino Pesca", "en": "Momotaro, the Peach Boy", "fr": "Momotaro, l'enfant pêche", "de": "Momotaro, der Pfirsichjunge", "es": "Momotaro, el niño melocotón"},
        "author": {"it": "Fiaba popolare giapponese", "en": "Japanese folk tale", "fr": "Conte populaire japonais", "de": "Japanisches Volksmärchen", "es": "Cuento popular japonés"},
        "country": {"it": "Giappone", "en": "Japan", "fr": "Japon", "de": "Japan", "es": "Japón"},
        "year": {"it": "Periodo Edo", "en": "Edo period", "fr": "période Edo", "de": "Edo-Zeit", "es": "período Edo"},
    },
    {
        "titles": {"it": "La Scimmia e l'Uccellino", "en": "The Monkey and the Little Bird", "fr": "Le Singe et le Petit Oiseau", "de": "Der Affe und das Vöglein", "es": "El mono y el pajarito"},
        "author": {"it": "Leonardo da Vinci", "en": "Leonardo da Vinci", "fr": "Léonard de Vinci", "de": "Leonardo da Vinci", "es": "Leonardo da Vinci"},
        "country": {"it": "Italia", "en": "Italy", "fr": "Italie", "de": "Italien", "es": "Italia"},
        "year": {"it": "1490 ca.", "en": "c. 1490", "fr": "vers 1490", "de": "um 1490", "es": "h. 1490"},
    },
]

# ---------------------------------------------------------------------------
# i18n loading and validation


def flatten(obj, prefix=""):
    flat = {}
    for key, value in obj.items():
        name = f"{prefix}{key}"
        if isinstance(value, dict):
            flat.update(flatten(value, name + "."))
        else:
            flat[name] = value
    return flat


def load_i18n():
    strings = {}
    for lang in LANGS:
        path = os.path.join(ROOT, "i18n", f"{lang}.json")
        with open(path, encoding="utf-8") as handle:
            strings[lang] = flatten(json.load(handle))
    base = set(strings["en"].keys())
    for lang in LANGS[1:]:
        missing = base - set(strings[lang].keys())
        extra = set(strings[lang].keys()) - base
        if missing or extra:
            print(f"i18n parity error for '{lang}':", file=sys.stderr)
            for key in sorted(missing):
                print(f"  missing: {key}", file=sys.stderr)
            for key in sorted(extra):
                print(f"  extra:   {key}", file=sys.stderr)
            sys.exit(1)
    return strings


# ---------------------------------------------------------------------------
# SVG fragments


def svg(inner, size=24, cls=""):
    klass = f' class="{cls}"' if cls else ""
    return (
        f'<svg{klass} viewBox="0 0 24 24" width="{size}" height="{size}" '
        f'fill="currentColor" aria-hidden="true">{inner}</svg>'
    )


# The Favilla mark, exactly as the app draws a firefly in FireflyField.swift:
# a bright core with three flat concentric rings — radii 6x, 4x, 2.5x the core
# at 0.08, 0.14, 0.24 of its alpha, stacked over each other.
MARK_RINGS = ((6.0, 0.08), (4.0, 0.14), (2.5, 0.24))


def _mark_svg(cx, cy, core_r, cls="", color=""):
    """One dot-and-rings mark as inline SVG, in currentColor (or `color`, set as
    a presentation attribute: inline style attributes are blocked by the CSP)."""
    klass = (f' class="{cls}"' if cls else "") + (f' color="{color}"' if color else "")
    rings = "".join(
        f'<circle cx="{cx}" cy="{cy}" r="{core_r * scale:.1f}" fill="currentColor" fill-opacity="{weight}"/>'
        for scale, weight in MARK_RINGS)
    return f'<g{klass}>{rings}<circle cx="{cx}" cy="{cy}" r="{core_r:.1f}" fill="currentColor"/></g>'


def _firefly_glyph():
    """The Favilla mark, small: a bright dot with three flat concentric rings."""
    return svg(_mark_svg(12, 12, 1.9), size=26)


def mascot_svg():
    """The hero mark: the dot-and-rings symbol, large, with two smaller ones
    drifting nearby — the same drawing the app uses for its fireflies."""
    return (
        '<svg class="mascot" viewBox="0 0 160 160" width="150" height="150" aria-hidden="true">'
        + _mark_svg(80, 80, 13)
        + _mark_svg(34, 122, 4, cls="mascot-spark")
        + _mark_svg(128, 40, 3.2, cls="mascot-spark")
        + _mark_svg(122, 130, 2.6, cls="mascot-spark")
        + '</svg>'
    )


GLYPHS = {
    "moon": lambda: svg('<path d="M12 3a9 9 0 1 0 9 9 7 7 0 0 1-9-9Z"/>'),
    "heart": lambda: svg('<path d="M12 21s-7.5-4.6-9.3-9A5.4 5.4 0 0 1 12 6.2 5.4 5.4 0 0 1 21.3 12c-1.8 4.4-9.3 9-9.3 9Z"/>'),
    "play": lambda: svg('<path d="M8 5v14l11-7L8 5Z"/>', size=14),
    "arrow": lambda: svg('<path d="M4 12h14M13 6l6 6-6 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'),
    "firefly": _firefly_glyph,
    "brand": _firefly_glyph,
    "sun": lambda: svg('<circle cx="12" cy="12" r="4.2" fill="none" stroke="currentColor" stroke-width="2"/><path d="M12 2.6v2.4M12 19v2.4M2.6 12h2.4M19 12h2.4M5.5 5.5l1.7 1.7M16.8 16.8l1.7 1.7M18.5 5.5l-1.7 1.7M7.2 16.8l-1.7 1.7" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round"/>', size=16),
    "search": lambda: svg('<path d="M10.5 3a7.5 7.5 0 1 0 4.55 13.45l4.75 4.75 1.4-1.4-4.75-4.75A7.5 7.5 0 0 0 10.5 3Zm0 2a5.5 5.5 0 1 1 0 11 5.5 5.5 0 0 1 0-11Z"/>', size=15),
    "mic": lambda: svg('<path d="M12 3a3 3 0 0 0-3 3v6a3 3 0 0 0 6 0V6a3 3 0 0 0-3-3Z"/><path d="M6.5 11.5a5.5 5.5 0 0 0 11 0M12 17v3.5M9 20.5h6" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>', size=16),
}


# The Forest tab, drawn the way FireflyForestView draws it at night: a sky
# gradient, a haloed moon, stars, three rows of pine silhouettes, and fireflies
# in the five palette colours (Color+Forest.swift).
FOREST = {
    "sky_top": "#070B1A", "sky_bottom": "#17243D", "moon": "#EDE7D2",
    "far": "#12202F", "mid": "#0C1722", "near": "#060D14",
    "palette": ["#C4923F", "#7FE08A", "#6FD6E8", "#F08AC8", "#B592F0"],
}
FOREST_STARS = [(22, 40), (58, 92), (96, 30), (128, 76), (150, 18), (176, 120), (214, 52), (246, 98),
                (38, 150), (88, 174), (122, 138), (232, 162), (70, 60), (190, 82), (260, 30), (12, 110)]
# (x, y, core radius, palette index)
FOREST_FLIES = [(40, 110, 2.6, 2), (92, 196, 3.2, 1), (150, 150, 2.4, 4), (212, 222, 3.0, 3),
                (60, 300, 3.4, 0), (122, 262, 2.8, 2), (236, 318, 2.6, 1), (176, 348, 3.4, 4),
                (28, 396, 2.8, 3), (104, 404, 3.0, 0), (250, 410, 2.4, 2), (64, 214, 2.2, 0)]


def _pines(base_y, height, width, count, offset, color):
    step = 276 / (count - 1)
    trees = []
    for i in range(count):
        cx = offset + i * step
        h = height * (0.78 + 0.22 * ((i * 37) % 10) / 10)
        trees.append(f'M{cx - width / 2:.1f} {base_y}L{cx:.1f} {base_y - h:.1f}L{cx + width / 2:.1f} {base_y}Z')
    return f'<path fill="{color}" d="{"".join(trees)}"/>'


def forest_svg():
    f = FOREST
    stars = "".join(f'<circle cx="{x}" cy="{y}" r="0.9"/>' for x, y in FOREST_STARS)
    flies = "".join(_mark_svg(x, y, r, cls="forest-fly", color=f["palette"][hue])
                    for x, y, r, hue in FOREST_FLIES)
    return (
        '<svg class="forest" viewBox="0 0 276 470" preserveAspectRatio="xMidYMid slice" aria-hidden="true">'
        f'<defs><linearGradient id="forest-sky" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{f["sky_top"]}"/><stop offset="0.62" stop-color="{f["sky_bottom"]}"/></linearGradient></defs>'
        '<rect width="276" height="470" fill="url(#forest-sky)"/>'
        f'<g fill="{f["moon"]}" opacity="0.7">{stars}</g>'
        f'<g fill="{f["moon"]}"><circle cx="212" cy="150" r="38" fill-opacity="0.05"/>'
        '<circle cx="212" cy="150" r="26" fill-opacity="0.08"/><circle cx="212" cy="150" r="14" fill-opacity="0.9"/></g>'
        + _pines(340, 120, 46, 9, -10, f["far"])
        + _pines(392, 150, 58, 7, 6, f["mid"])
        + _pines(470, 190, 74, 6, -18, f["near"])
        + f'<rect y="440" width="276" height="30" fill="{f["near"]}"/>'
        + flies + '</svg>')


def wave_svg(uid, amps, width, height):
    """A centered, mirrored waveform of rounded bars with one vertical gradient."""
    count = len(amps)
    slot = width / count
    bar_w = slot * 0.52
    bars = []
    for index, amp in enumerate(amps):
        bar_h = max(height * amp, 5)
        x = index * slot + (slot - bar_w) / 2
        y = (height - bar_h) / 2
        r = min(bar_w / 2, 4)
        bars.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{bar_h:.1f}" rx="{r:.1f}"/>')
    grad = (
        f'<linearGradient id="w-{uid}" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#C4923F" stop-opacity="0.9"/>'
        '<stop offset="0.5" stop-color="#E8B869"/>'
        '<stop offset="1" stop-color="#C4923F" stop-opacity="0.9"/></linearGradient>'
    )
    return (
        f'<svg class="wave" viewBox="0 0 {width} {height}" preserveAspectRatio="xMidYMid meet" '
        f'aria-hidden="true">{grad}'
        f'<g fill="url(#w-{uid})">{"".join(bars)}</g></svg>'
    )


HERO_AMPS = [0.28, 0.42, 0.6, 0.38, 0.72, 0.5, 0.86, 0.64, 0.46, 0.9, 0.58, 0.34,
             0.7, 0.92, 0.52, 0.4, 0.66, 0.3, 0.78, 0.48, 0.36, 0.62, 0.44, 0.8, 0.32, 0.5]


# ---------------------------------------------------------------------------
# PNG writer (stdlib only)


def png_bytes(width, height, pixel):
    rows = bytearray()
    for y in range(height):
        rows.append(0)
        row = bytearray()
        for x in range(width):
            row += bytes(pixel(x, y))
        rows += row

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    header = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header)
            + chunk(b"IDAT", zlib.compress(bytes(rows), 6)) + chunk(b"IEND", b""))


def _rounded_square(x, y, big, r):
    if r <= 0:
        return 0 <= x < big and 0 <= y < big
    cx = min(max(x, r), big - r)
    cy = min(max(y, r), big - r)
    dx, dy = x - cx, y - cy
    return dx * dx + dy * dy <= r * r


# Favilla mark color
FF_AMBER = (196, 146, 63)


def _mixn(color, over, alpha):
    return tuple(int(color[i] + (over[i] - color[i]) * alpha + 0.5) for i in range(3)) + (255,)


def _clamp01(value):
    return max(0.0, min(1.0, value))


def _mark_alpha(d, core_r):
    """Alpha of the dot-and-rings mark at distance d from its centre.

    Mirrors the app's FireflyField: flat rings stacked source-over, so the
    combined alpha inside ring i is 1 - prod(1 - w_j) for all rings j that
    contain the point.
    """
    if d <= core_r:
        return 1.0
    transmittance = 1.0
    for scale, weight in MARK_RINGS:
        if d <= core_r * scale:
            transmittance *= (1.0 - weight)
    return 1.0 - transmittance


def _icon_png(size, corner_radius, supersample):
    """Warm dark rounded square with the Favilla mark at its centre."""
    big = size * supersample
    r_sq = corner_radius * supersample
    bg_top, bg_bottom = (32, 23, 15), (9, 6, 4)
    core_r = big * 0.11

    def pixel(x, y):
        if not _rounded_square(x, y, big, r_sq):
            return (0, 0, 0, 0)
        color = tuple(bg_top[i] + (bg_bottom[i] - bg_top[i]) * (y / big) for i in range(3))
        alpha = _mark_alpha(math.hypot(x - big / 2, y - big / 2), core_r)
        if alpha > 0.003:
            color = _mixn(color, FF_AMBER, alpha)
        return (min(255, int(color[0] + 0.5)), min(255, int(color[1] + 0.5)), min(255, int(color[2] + 0.5)), 255)

    big_img = png_bytes(big, big, pixel)
    return big_img if supersample == 1 else _shrink_png(big_img, supersample)


def _shrink_png(data, factor):
    width, height, pixels = _decode_rgba(data)
    small_w, small_h = width // factor, height // factor
    count = factor * factor
    stride = width * 4

    def pixel(x, y):
        r = g = b = a = 0
        for sy in range(y * factor, (y + 1) * factor):
            base = sy * stride
            for sx in range(x * factor, (x + 1) * factor):
                i = base + sx * 4
                pa = pixels[i + 3]
                r += pixels[i] * pa
                g += pixels[i + 1] * pa
                b += pixels[i + 2] * pa
                a += pa
        if a == 0:
            return (0, 0, 0, 0)
        return (r // a, g // a, b // a, round(a / count))

    return png_bytes(small_w, small_h, pixel)


def _decode_rgba(data):
    pos = 8
    width = height = 0
    idat = bytearray()
    while pos < len(data):
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        tag = data[pos + 4:pos + 8]
        chunk_data = data[pos + 8:pos + 8 + length]
        if tag == b"IHDR":
            width, height = struct.unpack(">II", chunk_data[:8])
        elif tag == b"IDAT":
            idat += chunk_data
        pos += length + 12
    raw = zlib.decompress(bytes(idat))
    stride = width * 4 + 1
    pixels = bytearray(width * height * 4)
    prev = bytearray(width * 4)
    for y in range(height):
        row_start = y * stride
        ftype = raw[row_start]
        row = bytearray(raw[row_start + 1:row_start + stride])
        if ftype == 1:
            for i in range(4, len(row)):
                row[i] = (row[i] + row[i - 4]) & 255
        elif ftype == 2:
            for i in range(len(row)):
                row[i] = (row[i] + prev[i]) & 255
        elif ftype == 3:
            for i in range(len(row)):
                left = row[i - 4] if i >= 4 else 0
                row[i] = (row[i] + ((left + prev[i]) >> 1)) & 255
        elif ftype == 4:
            for i in range(len(row)):
                a = row[i - 4] if i >= 4 else 0
                b = prev[i]
                c = prev[i - 4] if i >= 4 else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pred = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                row[i] = (row[i] + pred) & 255
        pixels[y * width * 4:(y + 1) * width * 4] = row
        prev = row
    return width, height, pixels


def og_image_bytes():
    """1200x630 night scene: warm dark sky, a soft glow from below, and a few
    Favilla marks (dot + concentric rings) scattered like fireflies."""
    width, height = 1200, 630
    top, bottom = (36, 26, 17), (8, 5, 3)
    # mark position (x, y), core radius, opacity multiplier
    scene = [
        (880, 235, 11.0, 1.0),
        (1005, 360, 7.0, 0.75),
        (760, 355, 5.5, 0.6),
        (300, 180, 4.5, 0.55),
        (520, 470, 5.5, 0.55),
        (150, 330, 4.0, 0.45),
        (660, 520, 4.5, 0.5),
        (1100, 150, 3.5, 0.45),
    ]

    def lerp3(a, b, t):
        return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))

    def pixel(x, y):
        color = lerp3(top, bottom, y / height)

        # broad warm glow rising from the bottom
        d = math.hypot((x - 600) / 1.35, (y - 560) / 1.0)
        if d < 500:
            color = _mixn(color, FF_AMBER, (1 - d / 500) ** 2 * 0.22)

        # the marks
        for ox, oy, core_r, mult in scene:
            alpha = _mark_alpha(math.hypot(x - ox, y - oy), core_r) * mult
            if alpha > 0.003:
                color = _mixn(color, FF_AMBER, min(1.0, alpha))

        return (min(255, int(color[0] + 0.5)), min(255, int(color[1] + 0.5)), min(255, int(color[2] + 0.5)), 255)

    return png_bytes(width, height, pixel)


# ---------------------------------------------------------------------------
# Page assembly


def esc(value):
    return html.escape(str(value), quote=True)


def fmt(template, values):
    out = esc(template)
    for key, value in values.items():
        out = out.replace("{" + key + "}", esc(value))
    return out


def todo(field):
    return f'<mark class="todo">[{field} — set it in config.json]</mark>'


def mailto(email, label=None):
    return f'<a href="mailto:{esc(email)}">{esc(label or email)}</a>'


def lang_switcher_html(i18n, lang, href_for):
    """A visible language strip: EN IT FR DE ES, current one highlighted."""
    items = []
    for other in LANGS:
        current = ' aria-current="true"' if other == lang else ""
        items.append(
            f'<a lang="{other}" hreflang="{other}" href="{href_for(other)}" '
            f'title="{esc(LANG_NAMES[other])}" aria-label="{esc(LANG_NAMES[other])}"{current}>'
            f'{LANG_CODES[other]}</a>')
    # a group, not a <nav>: it already sits inside the main navigation landmark
    return ('<div class="lang-switcher" role="group" aria-label="'
            + esc(i18n["a11y.lang_aria"]) + '">' + "".join(items) + '</div>')


def theme_toggle_html(i18n):
    """Sun/moon icon button; the visible icon follows the active theme."""
    label = esc(i18n["a11y.theme"])
    return (
        '<button type="button" class="theme-toggle" aria-pressed="false" '
        f'aria-label="{label}" title="{label}">'
        '<span class="theme-icon theme-icon-sun">' + GLYPHS["sun"]() + '</span>'
        '<span class="theme-icon theme-icon-moon">' + GLYPHS["moon"]() + '</span>'
        '</button>')


PLACEHOLDER = re.compile(r"\{\{([a-zA-Z0-9_.]+)\}\}")


def render(template, ctx, page, lang):
    def replace(match):
        key = match.group(1)
        if key not in ctx:
            raise KeyError(f"unresolved placeholder {key!r} in {page}/{lang}")
        return str(ctx[key])

    return PLACEHOLDER.sub(replace, template)


def page_set_url(base_url, page, lang):
    prefix = "" if lang == "en" else f"{lang}/"
    if page == "index":
        return base_url + prefix
    return base_url + prefix + PAGES[page]


# An App Store product link, with or without the country and the name slug:
# https://apps.apple.com/[<cc>/]app/[<name>/]id<digits>[?query]
APP_STORE_URL = re.compile(r"""^https://apps\.apple\.com/(?:[a-z]{2}/)?app/(?:[^/?#\s]+/)?id\d+(?:\?[^\s"'<>]*)?$""")


def validate_config(config):
    """Fail the build on a config that would ship a broken or unsafe site."""
    errors = []
    base = urlparse(config.get("base_url", ""))
    local = base.hostname in ("localhost", "127.0.0.1")
    if not base.netloc or not (base.scheme == "https" or (base.scheme == "http" and local)):
        errors.append("base_url must be an absolute https:// URL (http:// only for localhost)")
    store = config.get("app_store_url") or ""
    if store and not APP_STORE_URL.match(store):
        errors.append("app_store_url must look like https://apps.apple.com/[<cc>/]app/[<name>/]id<digits>")
    email = config.get("contact_email") or ""
    if email and not re.match(r"^[^@\s<>\"']+@[^@\s<>\"']+\.[a-z]{2,}$", email, re.I):
        errors.append("contact_email is not a valid address")
    github = config.get("github_url") or ""
    if github and not github.startswith("https://github.com/"):
        errors.append("github_url must start with https://github.com/")
    missing = [field for field in ("contact_email", "publisher_name") if not config.get(field)]
    if store and missing:
        # App Store review requires reachable contact details on the support
        # page: never publish the download link next to a placeholder.
        errors.append(f"app_store_url is set but {', '.join(missing)} is empty")
    elif missing:
        print(f"warning: config.json {', '.join(missing)} empty — pages show a red placeholder", file=sys.stderr)
    if errors:
        for error in errors:
            print(f"config.json: {error}", file=sys.stderr)
        sys.exit(1)


def file_version(path):
    """Short content hash, appended as ?v= so a new deploy is never served
    with the previous CSS/JS from a browser or CDN cache."""
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:10]


def build(config, strings, out_dir):
    validate_config(config)
    base_url = config["base_url"].rstrip("/") + "/"
    year = date.today().year
    os.makedirs(out_dir, exist_ok=True)

    assets_src = os.path.join(ROOT, "assets")
    assets_dest = os.path.join(out_dir, "assets")
    if os.path.isdir(assets_src):
        shutil.copytree(assets_src, assets_dest, dirs_exist_ok=True)
    drawings = {f"{name}_glyph": glyph() for name, glyph in GLYPHS.items()}
    drawings.update(hero_wave=wave_svg("hero", HERO_AMPS, 800, 120),
                    mascot_svg=mascot_svg(), forest_svg=forest_svg())
    versions = {
        "v_css": file_version(os.path.join(assets_src, "css", "site.css")),
        "v_js": file_version(os.path.join(assets_src, "js", "site.js")),
    }

    img_dir = os.path.join(assets_dest, "img")
    os.makedirs(img_dir, exist_ok=True)
    with open(os.path.join(img_dir, "favicon.png"), "wb") as fh:
        fh.write(_icon_png(64, 14, 4))
    with open(os.path.join(img_dir, "apple-touch-icon.png"), "wb") as fh:
        fh.write(_icon_png(180, 0, 2))
    with open(os.path.join(img_dir, "og-image.png"), "wb") as fh:
        fh.write(og_image_bytes())

    with open(os.path.join(ROOT, "templates", "base.html"), encoding="utf-8") as fh:
        base_tpl = fh.read()
    templates = {}
    for name in PAGES:
        with open(os.path.join(ROOT, "templates", f"{name}.html"), encoding="utf-8") as fh:
            templates[name] = base_tpl.replace("{{body}}", fh.read())

    built = []
    email_html = mailto(config["contact_email"]) if config.get("contact_email") else todo("contact_email")
    publisher_html = esc(config["publisher_name"]) if config.get("publisher_name") else todo("publisher_name")

    for lang in LANGS:
        i18n = strings[lang]
        prefix = "" if lang == "en" else f"{lang}/"
        assets = "" if lang == "en" else "../"

        for page, filename in PAGES.items():
            if page == "404" and lang != "en":
                continue

            # Translations are text, never markup: escape them once here, so a
            # quote or an ampersand in a string can never break an attribute.
            ctx = {key: esc(value) for key, value in i18n.items()}

            # dotted i18n keys are also reachable in underscore form ({{privacy_cta_hint}})
            for key, value in list(ctx.items()):
                ctx[key.replace(".", "_")] = value

            ctx["csp"] = CSP
            ctx["theme_script"] = f"<script>{THEME_SCRIPT}</script>"
            ctx.update(versions)

            # meta
            title_key = {"index": "meta.title_index", "privacy": "meta.title_privacy",
                         "support": "meta.title_support", "404": "meta.title_404"}[page]
            desc_key = {"index": "meta.desc_index", "privacy": "meta.desc_privacy",
                        "support": "meta.desc_support", "404": "meta.desc_index"}[page]
            page_url = page_set_url(base_url, page, lang)
            hreflang = []
            for alt in LANGS:
                hreflang.append(
                    f'<link rel="alternate" hreflang="{alt}" href="{page_set_url(base_url, page, alt)}">')
            hreflang.append(f'<link rel="alternate" hreflang="x-default" href="{page_set_url(base_url, page, "en")}">')
            ctx["hreflang"] = "\n    ".join(hreflang)
            ctx["og_alternates"] = "\n    ".join(
                f'<meta property="og:locale:alternate" content="{OG_LOCALES[l]}">'
                for l in LANGS if l != lang)
            ctx["canonical"] = page_url
            ctx["head_title"] = ctx[title_key]
            ctx["head_desc"] = ctx[desc_key]
            ctx["og_site"] = ctx["meta.site_name"]
            ctx["og_title"] = ctx[title_key]
            ctx["og_desc"] = ctx[desc_key]
            ctx["og_url"] = page_url
            ctx["og_image"] = base_url + "assets/img/og-image.png"
            ctx["og_locale"] = OG_LOCALES[lang]
            ctx["assets"] = assets
            ctx["year"] = year

            # navigation
            nav_file = "" if page == "index" else "index.html"
            nav_links = [
                f'<a href="{nav_file}#idea">{esc(i18n["nav.idea"])}</a>',
                f'<a href="{nav_file}#how">{esc(i18n["nav.how"])}</a>',
                f'<a href="{nav_file}#app">{esc(i18n["nav.app"])}</a>',
                f'<a href="{nav_file}#privacy">{esc(i18n["nav.privacy"])}</a>',
                f'<a href="support.html">{esc(i18n["nav.support"])}</a>',
            ]
            ctx["nav_links"] = "".join(nav_links)
            ctx["nav_home"] = "index.html"
            ctx["brand_wordmark"] = WORDMARK

            # language switcher (visible, top right) and theme toggle
            def href_for(other, page=page, lang=lang):
                name = PAGES[page] if page != "index" else "index.html"
                if lang == "en":
                    return name if other == "en" else other + "/" + name
                return ("../" if other == "en" else f"../{other}/") + name

            ctx["lang_switcher"] = lang_switcher_html(i18n, lang, href_for)
            ctx["theme_toggle"] = theme_toggle_html(i18n)

            # footer
            ctx["footer_langs"] = "".join(
                f'<li><a lang="{other}" hreflang="{other}" href="{page_set_url(base_url, "index", other)}">'
                f'{LANG_NAMES[other]}</a></li>'
                for other in LANGS)
            ctx["footer_home"] = "index.html"
            ctx["footer_privacy"] = "privacy.html"
            ctx["footer_support"] = "support.html"
            ctx["footer_email"] = email_html
            ctx["footer_github"] = config["github_url"]
            ctx["footer_gh_label"] = "GitHub"
            ctx["footer_published_note"] = ctx["footer.published"]
            ctx["footer_publisher"] = publisher_html
            ctx["privacy_cta_hint"] = ctx["privacy.cta_hint"]

            # legacy: 404 is served for any missing path under any prefix,
            # so root-relative absolute URLs are the only safe links there.
            if page == "404":
                path_prefix = urlparse(base_url).path
                ctx["assets"] = path_prefix
                ctx["nav_home"] = path_prefix
                nav_anchors_404 = [("idea", "nav.idea"), ("how", "nav.how"),
                                   ("app", "nav.app"), ("privacy", "nav.privacy")]
                ctx["nav_links"] = "".join(
                    f'<a href="{path_prefix}#{anchor}">{esc(i18n[key])}</a>'
                    for anchor, key in nav_anchors_404)
                ctx["nav_links"] += f'<a href="{path_prefix}support.html">{esc(i18n["nav.support"])}</a>'
                ctx["lang_switcher"] = lang_switcher_html(
                    i18n, lang,
                    lambda other, pp=path_prefix: pp + ("" if other == "en" else other + "/"))
                ctx["footer_home"] = path_prefix
                ctx["footer_privacy"] = path_prefix + "privacy.html"
                ctx["footer_support"] = path_prefix + "support.html"

            # glyphs, the hero wave, the mascot and the forest (built once)
            ctx.update(drawings)

            # store badge
            store_url = config.get("app_store_url") or ""
            ctx["badge_attributes"] = (
                f'href="{esc(store_url)}" rel="noopener noreferrer"'
                if store_url else 'href="#app" aria-disabled="true"')
            ctx["badge_label"] = ctx["hero.badge_label"]
            ctx["hero_badge_cta"] = ctx["hero.badge_cta"]

            # tale data (mock rows and showcase)
            ctx["tale1_title"] = esc(TALES[0]["titles"][lang])
            ctx["tale2_title"] = esc(TALES[1]["titles"][lang])
            ctx["tale3_title"] = esc(TALES[2]["titles"][lang])
            ctx["tale_cards"] = "".join(
                f'<article class="tale glass reveal">'
                f'<h3 class="tale-title">{esc(t["titles"][lang])}</h3>'
                f'<p class="tale-caption">{fmt(i18n["showcase.caption"], {"author": t["author"][lang], "country": t["country"][lang], "year": t["year"][lang]})}</p>'
                f'</article>'
                for t in TALES)

            # privacy page assembly
            ctx["privacy_page_who_body"] = (
                esc(i18n["privacy_page.who_published"]) + " " + publisher_html
                + ', <span class="nowrap">' + esc(i18n["privacy_page.who_contact"]) + " "
                + email_html + '</span>.')

            # support page contact card
            ctx["contact_email"] = email_html

            ctx["privacy_href"] = "privacy.html"

            page_html = render(templates[page], ctx, page, lang)
            target = os.path.join(out_dir, prefix, filename)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "w", encoding="utf-8") as fh:
                fh.write(page_html)
            built.append(os.path.relpath(target, out_dir))

    # sitemap: one entry per page, listing all language alternates
    today = date.today().isoformat()
    with open(os.path.join(out_dir, "sitemap.xml"), "w", encoding="utf-8") as fh:
        fh.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        fh.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
                 'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n')
        for page in ("index", "privacy", "support"):
            fh.write(f"  <url>\n    <loc>{page_set_url(base_url, page, 'en')}</loc>\n")
            for alt in LANGS:
                fh.write(f'    <xhtml:link rel="alternate" hreflang="{alt}" href="{page_set_url(base_url, page, alt)}"/>\n')
            fh.write(f'    <xhtml:link rel="alternate" hreflang="x-default" href="{page_set_url(base_url, page, "en")}"/>\n')
            fh.write(f"    <lastmod>{today}</lastmod>\n  </url>\n")
        fh.write("</urlset>\n")

    with open(os.path.join(out_dir, "robots.txt"), "w", encoding="utf-8") as fh:
        fh.write("User-agent: *\nAllow: /\n\n")
        fh.write(f"Sitemap: {base_url}sitemap.xml\n")

    return built


def main():
    parser = argparse.ArgumentParser(description="Build the Favilla static website")
    parser.add_argument("--out", default="_site")
    parser.add_argument("--base-url", default=None, help="override base URL from config.json")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    with open(os.path.join(ROOT, "config.json"), encoding="utf-8") as fh:
        config = json.load(fh)
    if args.base_url:
        config["base_url"] = args.base_url

    strings = load_i18n()
    out_dir = args.out if os.path.isabs(args.out) else os.path.join(ROOT, args.out)
    built = build(config, strings, out_dir)
    print(f"OK: built {len(built)} pages into {os.path.relpath(out_dir, ROOT)}")
    for path in built:
        print(f"  {path}")


if __name__ == "__main__":
    main()
