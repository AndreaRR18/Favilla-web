# Favilla website

Static marketing website for **Favilla** — the iOS app that lets parents
record fairy tales in their own voice for their children's bedtime.

Live at: https://andrearr18.github.io/VoiceTale-web/

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
.github/workflows/deploy.yml   build + deploy to GitHub Pages
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
   python3 -m http.server -d _site 8000
   ```

3. Commit to `main` and push. The workflow builds and publishes automatically.

The build fails if the five dictionaries drift out of parity (a key added to
one language and not the others) or if a placeholder in a template cannot be
resolved — so a broken translation never reaches production.

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
  (labels) — the app's own stack.
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
  one follows the cursor like a curious companion — pointer-fine devices
  only, and everything that makes them move is disabled when the visitor
  asks for reduced motion.
- A visible language strip (`EN IT FR DE ES`) sits in the top-right corner of
  every page, with the current language highlighted.
- Favicons, the touch icon and the social share image are generated at build
  time in `scripts/build.py` (stdlib PNG writer, no image dependencies); the
  SVG favicon in `assets/img/favicon.svg` mirrors the same drawing.

## Deployment

`.github/workflows/deploy.yml` triggers on push to `main` or `master`:

checkout → setup Python → `scripts/build.py` → upload artifact → deploy-pages.
GitHub Pages is configured with source `workflow` (set once via
`gh api` — see the repo Settings → Pages).

## Catalog showcase data

The landing page's catalog showcase (six tales with localized titles, authors
and countries) is embedded in `scripts/build.py` as `TALES`; the six stories
match the iOS app's `catalog-seed.json`.

## License

The app repo carries the MIT LICENSE for code. The website text and images are
part of the same project.
