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
  parchment `#FAF7F2`). No pure white, no saturated orange.
- Typography: Epilogue (headings), New York / system serif (body), Manrope
  (labels) — the app's own stack. Epilogue and Manrope are self-hosted in
  `assets/fonts/` (variable woff2, latin subset, SIL OFL licenses alongside).
- Tone: short, quiet sentences. Second person singular. No exclamation
  marks, no hype words, no "transform your nights".

## config.json

| Field | Purpose |
|---|---|
| `base_url` | Canonical URL. Update if you add a custom domain (and add the `CNAME` file to `templates` handling). Also update after a repo rename. |
| `app_store_url` | **Empty while the app is not on the App Store** — the download badge renders as "coming soon". Paste the App Store URL here at launch and it becomes a live download button everywhere. |
| `contact_email` | Used in the footer, support page and privacy policy. Until set, a red placeholder is rendered so the gap is impossible to miss. |
| `publisher_name` | "Published by" in the footer and privacy policy. Same placeholder behavior. |
| `github_url` | Footer source link. |

If the GitHub repo is renamed (owner action, e.g. to `Favilla-web`), update
both `base_url` and `github_url` in one commit.

## Design

A port of the app's `DesignSystem` package (see the Favilla iOS repo):

- Dark-first night theme and the warm parchment light theme, with a
  sun/moon toggle in the top-right nav. The choice is remembered per browser
  (`localStorage`), defaults to the OS preference, and ships with an inline
  `<head>` script so there is no flash of wrong theme. The phone mockups
  always stay dark — they show the app's bedtime UI.
- Fireflies: a few ambient ones drift in the night sky (dark theme only),
  one follows the cursor like a curious companion (mouse/trackpad only, not
  on touch screens). Under Reduce Motion it behaves like the app's fireflies:
  it stays, but holds still beside the pointer — no wandering, sparks or
  blinking — and the ambient sky ones are not drawn. Like the app's forest,
  fireflies only come out at night: in light mode there is no companion.
- If `site.js` is blocked or fails, the inline head script un-hides the
  scroll-reveal content after 3 s; with JavaScript off it's never hidden.
- A visible language strip (`EN IT FR DE ES`) sits in the top-right corner of
  every page, with the current language highlighted.
- The phone mocks mirror real screens: the Library (amber mic, large title,
  search pill, play tiles) and the Forest tab at night, drawn from the app's
  `Color+Forest.swift` palette. Only describe features the shipped build has:
  Sleep Sounds is behind a feature flag that is off, so the site doesn't
  advertise it; folders and tags have no UI yet.
- Favicons, the touch icon and the social share image are generated at build
  time in `scripts/build.py` (stdlib PNG writer, no image dependencies); the
  SVG favicon in `assets/img/favicon.svg` mirrors the same drawing.

## Deployment

`.github/workflows/deploy.yml` runs on every push and pull request to `main`:

checkout → `scripts/build.py` → `scripts/check_site.py` → upload artifact →
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

The site is already published. Before the App Store submission:

1. **Fill `config.json`**: `contact_email` and `publisher_name`. Until then
   every page shows a red placeholder, and the build *refuses* to publish an
   App Store link without them (review requires reachable contact details).
2. **App Store Connect** → App Information / version page:
   - Privacy Policy URL: `https://andrearr18.github.io/Favilla-web/privacy.html`
   - Support URL: `https://andrearr18.github.io/Favilla-web/support.html`
   - Marketing URL (optional): `https://andrearr18.github.io/Favilla-web/`
3. **In the app**: set `LegalLinks.privacyPolicy` (iOS repo,
   `Library/Sources/About/LegalLinks.swift`) to the same privacy URL.
4. **Re-read the privacy policy** against the build you submit (it still lists
   imported sleep sounds, a feature that is hidden in 1.0).
5. **On launch day**: paste the App Store URL into `app_store_url`, push. The
   badge becomes a live download link in all five languages; the support
   FAQ's "coming soon" answer should be updated in the same commit.
6. Optional: a custom domain (add a `CNAME` to the build output and update
   `base_url`). Keep the github.io URLs working until App Store Connect points
   at the new ones.

## Catalog showcase data

The landing page's catalog showcase (six tales with localized titles, authors
and countries) is embedded in `scripts/build.py` as `TALES`; the six stories
match the iOS app's `catalog-seed.json`.

## License

The app repo carries the MIT LICENSE for code. The website text and images are
part of the same project.
