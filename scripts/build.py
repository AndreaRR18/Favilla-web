#!/usr/bin/env python3
"""Build the VoiceTale static website.

Renders templates/*.html for every language in i18n/*.json, copies assets,
generates raster icons (stdlib-only PNG writer), and emits sitemap/robots.

Design tokens mirror the iOS DesignSystem package (dark-first, warm amber).
Run:  python3 scripts/build.py [--out _site] [--dry-run]
"""

import argparse
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

MOCK_COUNTRIES = {"fr": TALES[0]["country"], "de": TALES[2]["country"], "jp": TALES[4]["country"]}


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


GLYPHS = {
    "moon": lambda: svg('<path d="M12 3a9 9 0 1 0 9 9 7 7 0 0 1-9-9Z"/>'),
    "crescent": lambda: svg('<path d="M14 3.5A9 9 0 1 0 20.5 14 7.2 7.2 0 0 1 14 3.5Z"/>', size=20),
    "shield": lambda: svg('<path d="M12 3 4 6v5c0 5 3.4 8.6 8 10 4.6-1.4 8-5 8-10V6l-8-3Zm0 2.2 6 2.2V11c0 4.2-2.6 7.2-6 8.7-3.4-1.5-6-4.5-6-8.7V7.4l6-2.2Z"/>'),
    "heart": lambda: svg('<path d="M12 21s-7.5-4.6-9.3-9A5.4 5.4 0 0 1 12 6.2 5.4 5.4 0 0 1 21.3 12c-1.8 4.4-9.3 9-9.3 9Z"/>'),
    "play": lambda: svg('<path d="M8 5v14l11-7L8 5Z"/>', size=14),
    "arrow": lambda: svg('<path d="M4 12h14M13 6l6 6-6 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'),
    "noise": lambda: svg('<path d="M3 9h2.5v6H3zM7.5 6H10v12H7.5zM12 3h2.5v18H12zM16.5 7H19v10h-2.5z"/>'),
    "rain": lambda: svg('<path d="M7 14h10a4 4 0 0 0 .5-8A5.5 5.5 0 0 0 6.9 4.9 4 4 0 0 0 7 14Z"/>'),
    "heartbeat": lambda: svg('<path d="M2.5 11.5h4l1.6-4 4 9.5 2.2-5.5h6.2" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'),
    "music": lambda: svg('<path d="M9.5 17.8a2.6 2.6 0 1 1-1.4-2.3V4.6L18 3v2.1l-8.5 1.4v8.9a2.6 2.6 0 0 1 1.9-1 2.6 2.6 0 0 1 1.4 4.9l6.7-1.8v2.2L9.5 21Z"/>'),
    "timer": lambda: svg('<path d="M9 2h6v2H9zM12 3.5a8.5 8.5 0 1 0 8.5 8.5A8.5 8.5 0 0 0 12 3.5Zm0 2a6.5 6.5 0 1 1-6.5 6.5A6.5 6.5 0 0 1 12 5.5ZM11 8h2v3.6l2.7 2.7-1.4 1.4-3.3-3.3Z"/>'),
    "import": lambda: svg('<path d="M10 3H4v18h16V3h-6v2h4v14H6V5h4Zm1 4v7.6l2.3-2.3 1.4 1.4L11 17.4l-3.7-3.7 1.4-1.4L11 14.6V7Z"/>'),
    "globe": lambda: svg('<path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2Zm6.9 7h-3a15.4 15.4 0 0 0-1.1-4.4A8 8 0 0 1 18.9 9ZM12 4c.8 1.2 1.9 3.6 2.3 7H9.7C10.1 7.6 11.2 5.2 12 4ZM9.2 4.6A15.4 15.4 0 0 0 8.1 9h-3a8 8 0 0 1 4.1-4.4ZM4.3 11h3.5c-.1 1-.1 2 0 3H4.3a8 8 0 0 1 0-3Zm.8 5h3a15.4 15.4 0 0 0 1.1 4.4A8 8 0 0 1 5.1 16Zm6.9 4.4c-.8-1.2-1.9-3.6-2.3-7h4.6c-.4 3.4-1.5 5.8-2.3 7Zm3.8-.4a15.4 15.4 0 0 0 1.1-4h3a8 8 0 0 1-4.1 4.4ZM19.7 14h-3.5c.1-1 .1-2 0-3h3.5a8 8 0 0 1 0 3Z"/>'),
    "brand": lambda: svg('<path d="M13.5 3A8 8 0 1 0 20 13.4 6.4 6.4 0 0 1 13.5 3Z"/><path d="M7 17.5h1.6v-2.4H7Zm2.5 0h1.6v-4H9.5Zm2.5 0h1.6v-1.8H12Z"/>', size=26),
    "sun": lambda: svg('<circle cx="12" cy="12" r="4.2" fill="none" stroke="currentColor" stroke-width="2"/><path d="M12 2.6v2.4M12 19v2.4M2.6 12h2.4M19 12h2.4M5.5 5.5l1.7 1.7M16.8 16.8l1.7 1.7M18.5 5.5l-1.7 1.7M7.2 16.8l-1.7 1.7" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round"/>', size=16),
    "search": lambda: svg('<path d="M10.5 3a7.5 7.5 0 1 0 4.55 13.45l4.75 4.75 1.4-1.4-4.75-4.75A7.5 7.5 0 0 0 10.5 3Zm0 2a5.5 5.5 0 1 1 0 11 5.5 5.5 0 0 1 0-11Z"/>', size=15),
}


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
MINI_AMPS = {
    "a": [0.4, 0.7, 0.5, 0.85, 0.45, 0.65, 0.9, 0.5],
    "b": [0.6, 0.35, 0.8, 0.5, 0.9, 0.4, 0.7, 0.55],
    "c": [0.5, 0.85, 0.4, 0.6, 0.75, 0.35, 0.8, 0.45],
}


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


def mix(base, over, alpha):
    alpha = max(0.0, min(1.0, alpha))
    return tuple(int(base[i] + (over[i] - base[i]) * alpha + 0.5) for i in range(3)) + (255,)


def _rounded_square(x, y, big, r):
    if r <= 0:
        return 0 <= x < big and 0 <= y < big
    cx = min(max(x, r), big - r)
    cy = min(max(y, r), big - r)
    dx, dy = x - cx, y - cy
    return dx * dx + dy * dy <= r * r


def _icon_png(size, corner_radius, supersample):
    """Dark rounded square with a centered amber waveform, supersampled."""
    big = size * supersample
    bars = [0.30, 0.55, 0.85, 0.55, 0.30]
    bar_w = big * 0.082
    gap = big * 0.034
    total_w = 5 * bar_w + 4 * gap
    x0 = (big - total_w) / 2
    cy = big / 2
    bg = (28, 20, 16)
    amber = (196, 146, 63)
    hot = (232, 184, 105)
    r_sq = corner_radius * supersample

    def pixel(x, y):
        if not _rounded_square(x, y, big, r_sq):
            return (0, 0, 0, 0)
        color = bg + (255,)
        for index, amp in enumerate(bars):
            bx = x0 + index * (bar_w + gap)
            bh = big * amp * 0.17
            top, bottom = cy - bh, cy + bh
            if bx <= x <= bx + bar_w and top <= y <= bottom:
                if x - bx < bar_w * 0.28:
                    edge = (x - bx) / (bar_w * 0.28)
                else:
                    edge = (bx + bar_w - x) / (bar_w * 0.28)
                edge = min(max(edge, 0), 1)
                shade = mix(bg, amber, edge * 0.85)[:3] + (255,)
                mid = max(0.0, 1 - abs((y - cy) / (bh * 0.5)))
                color = mix(shade[:3], hot, mid * 0.5)
        return color

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
    """1200x630 night scene: gradient, amber glows, waveform bars, a crescent."""
    width, height = 1200, 630
    top, bottom = (28, 20, 16), (10, 7, 5)
    glow_cx, glow_cy, glow_r = 600.0, 470.0, 560.0
    bars = [0.30, 0.5, 0.78, 0.42, 0.9, 0.55, 0.72, 1.0, 0.62, 0.85, 0.45, 0.68,
            0.95, 0.5, 0.75, 0.38, 0.6, 0.88]
    bar_w, gap = 30.0, 12.0
    total_w = len(bars) * bar_w + (len(bars) - 1) * gap
    x0 = (width - total_w) / 2
    cy = 300.0
    moon_cx, moon_cy, moon_r = 1000.0, 148.0, 56.0

    def lerp3(a, b, t):
        return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))

    def pixel(x, y):
        t = y / height
        color = lerp3(top, bottom, t)
        d = math.hypot(x - glow_cx, y - glow_cy)
        if d < glow_r:
            falloff = 1 - d / glow_r
            color = mix(color, (196, 146, 63), falloff ** 2 * 0.30)[:3]
        d2 = math.hypot(x - 240, y - 120)
        if d2 < 300:
            color = mix(color, (196, 146, 63), (1 - d2 / 300) ** 2 * 0.12)[:3]
        dc = math.hypot(x - moon_cx, y - moon_cy)
        if dc < moon_r:
            inner = math.hypot(x - (moon_cx + 24), y - (moon_cy - 9))
            crescent_zone = dc / moon_r
            if inner > moon_r * 0.92 and crescent_zone < 1.0:
                alpha = 0.85 * (1 - abs(dc - moon_r * 0.5) / (moon_r * 0.5))
                alpha = max(0.0, min(1.0, alpha))
                if inner > moon_r:
                    color = mix(color, (245, 233, 208), alpha)[:3]
                else:
                    soft = max(0.0, (inner - moon_r * 0.8) / (moon_r * 0.2))
                    color = mix(color, (245, 233, 208), alpha * soft)[:3]
        for index, amp in enumerate(bars):
            bx = x0 + index * (bar_w + gap)
            bh = 250.0 * amp
            top_y, bottom_y = cy - bh, cy + bh
            if bx <= x < bx + bar_w and top_y <= y <= bottom_y:
                mid = 1 - abs(y - cy) / (bh * 0.9)
                bar = mix((196, 146, 63), (245, 233, 208), max(0.0, mid) * 0.55)[:3]
                edge = 1.0
                if x - bx < 4:
                    edge = (x - bx) / 4
                elif bx + bar_w - x < 4:
                    edge = (bx + bar_w - x) / 4
                cap = min(1.0, (y - top_y) / 14, (bottom_y - y) / 14)
                a = min(1.0, edge) * max(0.0, cap)
                color = mix(color, bar, a)
                break
        return (int(color[0] + 0.5), int(color[1] + 0.5), int(color[2] + 0.5), 255)

    return png_bytes(width, height, pixel)


# ---------------------------------------------------------------------------
# Page assembly


def esc(value):
    return html.escape(str(value), quote=True)


def fmt(template, values):
    out = template
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
    return ('<nav class="lang-switcher" aria-label="'
            + esc(i18n["a11y.lang_aria"]) + '">' + "".join(items) + '</nav>')


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


def build(config, strings, out_dir):
    base_url = config["base_url"].rstrip("/") + "/"
    year = date.today().year
    os.makedirs(out_dir, exist_ok=True)

    assets_src = os.path.join(ROOT, "assets")
    assets_dest = os.path.join(out_dir, "assets")
    if os.path.isdir(assets_src):
        shutil.copytree(assets_src, assets_dest, dirs_exist_ok=True)

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

            ctx = dict(i18n)

            # dotted i18n keys are also reachable in underscore form ({{privacy_cta_hint}})
            for key, value in list(ctx.items()):
                ctx[key.replace(".", "_")] = value

            # list-valued i18n keys flattened to named slots
            for tab in ("lib", "cat", "snd", "abt"):
                bullets = i18n[f"tabs.{tab}_bullets"]
                for i, text in enumerate(bullets[:3], 1):
                    ctx[f"tabs_{tab}_b{i}"] = text

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
            ctx["head_title"] = i18n[title_key]
            ctx["head_desc"] = i18n[desc_key]
            ctx["og_site"] = i18n["meta.site_name"]
            ctx["og_title"] = i18n[title_key]
            ctx["og_desc"] = i18n[desc_key]
            ctx["og_url"] = page_url
            ctx["og_image"] = base_url + "assets/img/og-image.png"
            ctx["og_locale"] = OG_LOCALES[lang]
            ctx["assets"] = assets
            ctx["year"] = year

            # navigation
            nav_file = "" if page == "index" else "index.html"
            nav_links = [
                f'<a href="{nav_file}#features">{esc(i18n["nav.features"])}</a>',
                f'<a href="{nav_file}#app">{esc(i18n["nav.app"])}</a>',
                f'<a href="{nav_file}#why">{esc(i18n["nav.why"])}</a>',
                f'<a href="{nav_file}#privacy">{esc(i18n["nav.privacy"])}</a>',
                f'<a href="support.html">{esc(i18n["nav.support"])}</a>',
            ]
            ctx["nav_links"] = "".join(nav_links)
            ctx["nav_home"] = "index.html"

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
            ctx["footer_published_note"] = i18n["footer.published"]
            ctx["footer_publisher"] = publisher_html
            ctx["privacy_cta_hint"] = i18n["privacy.cta_hint"]

            # legacy: 404 is served for any missing path under any prefix,
            # so root-relative absolute URLs are the only safe links there.
            if page == "404":
                path_prefix = urlparse(base_url).path
                ctx["assets"] = path_prefix
                ctx["nav_home"] = path_prefix
                nav_anchors_404 = [("features", "nav.features"), ("app", "nav.app"),
                                   ("why", "nav.why"), ("privacy", "nav.privacy")]
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

            # glyphs and waves
            for name, glyph in GLYPHS.items():
                ctx[f"{name}_glyph"] = glyph()
            for wave_id, amps in MINI_AMPS.items():
                ctx[f"wave_{wave_id}"] = wave_svg(f"m{wave_id}", amps, 44, 16)
            ctx["hero_wave"] = wave_svg("hero", HERO_AMPS, 800, 120)

            # store badge
            store_url = config.get("app_store_url") or ""
            ctx["badge_attributes"] = (
                f'href="{esc(store_url)}" target="_blank" rel="noopener"'
                if store_url else 'href="#app" aria-disabled="true"')
            ctx["badge_label"] = i18n["hero.badge_label"]
            ctx["hero_badge_cta"] = i18n["hero.badge_cta"]

            # tale data (mock rows and showcase)
            ctx["tale1_title"] = esc(TALES[0]["titles"][lang])
            ctx["tale2_title"] = esc(TALES[1]["titles"][lang])
            ctx["tale3_title"] = esc(TALES[2]["titles"][lang])
            ctx["tale4_title"] = esc(TALES[3]["titles"][lang])
            ctx["country_fr"] = esc(MOCK_COUNTRIES["fr"][lang])
            ctx["country_de"] = esc(MOCK_COUNTRIES["de"][lang])
            ctx["country_jp"] = esc(MOCK_COUNTRIES["jp"][lang])
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
    parser = argparse.ArgumentParser(description="Build the VoiceTale static website")
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
