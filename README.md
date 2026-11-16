# Favilla website

Static marketing website for **Favilla** — the iOS app that lets parents
record fairy tales in their own voice for their children's bedtime.

Live at: https://andrearr18.github.io/Favilla-web/

Built to host the three URLs App Store Connect requires: product page,
privacy policy and support page — in all five languages the app ships
(English, Italian, French, German, Spanish).

## How it works

No web framework, no build tooling beyond stdlib. A single stdlib-only
Python script renders hand-written HTML templates with translations from
JSON dictionaries. GitHub Actions runs it and deploys the result to
GitHub Pages on every merge to `main` (also triggers on `master`).

```
templates/            HTML skeletons, {{placeholders}} only, no logic
i18n/{en,it,fr,de,es}.json   every string on the site, per language
assets/               css/js/img, copied verbatim
scripts/build.py      renderer: templates x 5 languages -> _site
scripts/check_site.py post-build gate: links, assets, #fragments, CSP rules
scripts/check_copy.py post-build gate: brand and store copy rules, page structure, RELEASE.md
RELEASE.md            App Store Connect values (not published)
.github/workflows/deploy.yml   build + check + deploy to GitHub Pages
config.json           site-level facts (see below)
```

## Editing content

1. Edit `i18n/<lang>.json` (or a template, or the assets).
2. Preview locally with a single command:

   ```bash
   ./run.sh          # builds into _site/ and serves on http://localhost:8000
   ./run.sh 3000     # custom port
   ```

   `run.sh` is just a wrapper around the two steps below, if you prefer them
   separately:

   ```bash
   python3 scripts/build.py --out _site
   python3 scripts/check_site.py _site
   python3 scripts/check_copy.py _site
   python3 -m http.server -d _site 8000
   ```

3. Commit to `main` and push. The workflow builds and publishes automatically.

The build fails if the five dictionaries drift out of parity (a key added to
one language and not the others) or if a placeholder in a template cannot be
resolved, and `check_site.py` fails on a broken link, a missing asset, a
`#fragment` with no target, an inline style/script the CSP would block, or
anything loaded from another origin — so none of these reach production.

## Brand rules

The site must stay faithful to the app's identity (see the rebrand spec in the
iOS repo, `docs/superpowers/specs`). In short:

- Name: **Favilla**, one word, no accent, written the same in all five
  languages. The wordmark is lowercase "favilla" with the dot of the i in
  amber (built in `scripts/build.py` as `WORDMARK`).
- Mascot: the firefly. A small light that stays lit in the dark — never
  sparkle icons (✨ and friends read as "AI") and never realistic flames
  or candles.
- Palette: amber `#C4923F` on warm black `#100B08` (light mode: warm
  parchment `#FAF7F2`). No pure white, no saturated orange. Every colour in
  `site.css` is an app token or an alpha of one — no invented hexes. The two
  deliberate exceptions are documented in the skill: light-mode lines are
  dark (the app's cream line is invisible on parchment) and light-mode amber
  text uses `#8A6428` (the app's light `#B07D3A` fails AA).
- Typography: Epilogue (headings), New York / system serif (body), Manrope
  (labels) — the app's own stack. Epilogue and Manrope are self-hosted in
  `assets/fonts/` (variable woff2, latin subset, SIL OFL licenses alongside).
- Tone: short, quiet sentences. No exclamation marks, no hype words, no
  "transform your nights". The register follows the app per language: *tu*
  in Italian, *du* in German, *tú* in Spanish, and **vous** in French — the
  app addresses the parent as *vous* throughout, so the site does too.
- Scope: describe only what the shipped build has. Check
  `FAVILLA_FEATURE_*` in the iOS scheme before claiming a feature; both
  `paywall` and `sleepSounds` are off today.

The full rules — token map, phrasebook, anti-goals, verification — live in
`.vibe/skills/favilla-site-brand/SKILL.md`. Load it before changing design or
copy.

## config.json

| Field | Purpose |
|---|---|
| `base_url` | Canonical URL. Update if you add a custom domain (and add the `CNAME` file to `templates` handling). Also update after a repo rename. |
| `app_store_url` | **Empty while the app is not on the App Store** — the download badge renders as "coming soon". Paste the App Store URL here at launch and it becomes a live download button everywhere. |
| `contact_email` | Used in the footer, support page and privacy policy. Until set, a red placeholder is rendered so the gap is impossible to miss. |
| `publisher_name` | "Published by" in the footer and privacy policy. Same placeholder behavior. |

Only the publisher's name and email ever appear on the site. The address and
phone number App Store Connect asks for (EU trader status) live in
`RELEASE.md`, never in `config.json` or a template.
| `github_url` | Footer source link. |

If the GitHub repo is renamed (owner action, e.g. to `Favilla-web`), update
both `base_url` and `github_url` in one commit.

## Design

Every page is drawn with the app's own components (`DesignSystem` in the
Favilla iOS repo), so the site reads as the app at desk size, not as a
landing page. The approved design is
`docs/superpowers/specs/2026-11-16-app-faithful-restyle-design.md`.

- **Screens, not sections.** Each page opens with a large left-aligned title.
  Content sits in inset grouped lists: a 44 pt amber tile (`StoryEmojiView`),
  a serif title, a secondary line, a chevron only on rows that link. Long
  text reads like a group footer. No uppercase kickers, no card grids, no
  scroll-reveal.
- **Glass.** Round 44 px buttons (language, theme), a back capsule on pushed
  pages, the App Store capsule, and the floating glass tab bar at the bottom
  (Favilla, Catalog, Privacy, Support) at every width.
- **The home** shows the app's recording screen in a phone, the catalog as
  the app lists it (each tale's emoji flattened to an amber silhouette), the
  Forest as a night card in its own palette (`Color+Forest.swift`), the four
  tabs, and "Privacy in 30 seconds". The phone and the forest stay dark in
  both themes.
- **The firefly** (a core and three flat rings, as `FireflyField` draws it)
  is the dot on the wordmark's i, the Favilla tab, a few lights in the night
  sky and the companion that follows the cursor (mouse/trackpad, dark theme
  only; under Reduce Motion it holds still and nothing else moves).
- **Themes.** Dark-first, with the warm parchment light theme. The choice is
  remembered per browser and set by the inline head script before first
  paint. Nothing waits for JavaScript: with scripts blocked the site follows
  the OS theme and every page is complete; the FAQ is plain `<details>`.
- **Contrast.** `TextTertiary` fails AA as small text, so subtitles, notes and
  captions use `TextSecondary`; tertiary is kept for chevrons and other
  non-text. Light mode also uses dark lines and `#8A6428` amber text (see the
  brand skill).
- Only describe what the shipped build has: Sleep Sounds and purchases are
  off, folders and tags have no UI, and the site makes no promise about the
  price. `check_copy.py` enforces the wording.
- Favicons, the touch icon and the social share image are generated at build
  time in `scripts/build.py` (stdlib PNG writer, no image dependencies); the
  SVG favicon in `assets/img/favicon.svg` mirrors the same drawing.

## Deployment

`.github/workflows/deploy.yml` runs on every push and pull request to `main`:

checkout → `scripts/build.py` → `scripts/check_site.py` → `scripts/check_copy.py` →
upload artifact →
deploy-pages. Pull requests only build and check; only `main` deploys.
GitHub Pages is configured with source `workflow` (Settings → Pages), HTTPS
enforced.

## Security

GitHub Pages can't send custom response headers, so the site protects itself
from the inside:

- **Content-Security-Policy** as a `<meta>` tag on every page: everything
  first-party, no inline code except the one theme script, allowed by its
  SHA-256 hash (computed in `build.py`, so editing `THEME_SCRIPT` keeps the
  policy in sync automatically). No `unsafe-inline`, no `eval`, no forms, no
  `<base>` hijacking. (No `upgrade-insecure-requests`: every URL is relative
  and Pages forces HTTPS, and it would break the http://localhost preview.)
- **Nothing third-party**: fonts are self-hosted, there are no analytics,
  embeds or CDNs. Visitors' IP addresses go to GitHub and nobody else — the
  same promise the app makes.
- **Referrer policy** `strict-origin-when-cross-origin`; external links carry
  `rel="noopener noreferrer"`.
- **Escaping**: every translation string is HTML-escaped by the renderer, so
  a quote or `&` in a translation can't break markup.
- **CI supply chain**: actions pinned to commit SHAs (Dependabot proposes
  updates monthly), `permissions: {}` by default with per-job grants,
  checkout without persisted credentials.
- **What a meta CSP can't do**: `frame-ancestors` (clickjacking) only works as
  a header. The site has no forms or actions to hijack, so the risk is
  cosmetic; a custom domain behind a CDN that sets headers would close it.
- HTTPS and HSTS are provided by GitHub Pages.

## Going live

The site is already published. Everything App Store Connect needs — URLs per
language, App Privacy answers, Kids notes, reviewer notes, the "before you
submit" and "launch day" lists — is in `RELEASE.md`. In short:

1. **Fill `config.json` → `publisher_name`** (`contact_email` is set). Until
   then the pages show a red placeholder, and the build *refuses* an App Store
   link without both.
2. **`app_store_url` stays empty until the app is approved.** The badge reads
   "coming soon" meanwhile.
3. **In the app**: set `LegalLinks.privacyPolicy` (iOS repo,
   `Library/Sources/About/LegalLinks.swift`) to the privacy URL.
4. **On launch day**: paste the App Store URL into `app_store_url`, replace the
   "when can we use it" support answer in five languages, push.
5. Optional: a custom domain (add a `CNAME` to the build output and update
   `base_url`). Keep the github.io URLs working until App Store Connect points
   at the new ones.

## Catalog showcase data

The home's catalog list (six tales with emoji, localized titles, authors
and countries) is embedded in `scripts/build.py` as `TALES`; the six stories
match the iOS app's `catalog-seed.json`.

## License

The app repo carries the MIT LICENSE for code. The website text and images are
part of the same project.
