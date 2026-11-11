# VoiceTale-web

Static marketing website for **VoiceTale** (Voce di Casa) — the iOS app that lets
parents record fairy tales in their own voice for their children's bedtime.

Live at: https://andrearr18.github.io/VoiceTale-web/

Built to host the three URLs App Store Connect requires: product page,
privacy policy and support page — in all five languages the app ships
(English, Italian, French, German, Spanish).

## How it works

No web framework, no build tooling, no dependencies. A single stdlib-only
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
2. Preview locally:

   ```bash
   python3 scripts/build.py --out _site
   python3 -m http.server -d _site 8000
   ```

3. Commit to `main` and push. The workflow builds and publishes automatically.

The build fails if the five dictionaries drift out of parity (a key added to
one language and not the others) or if a placeholder in a template cannot be
resolved — so a broken translation never reaches production.

## config.json

| Field | Purpose |
|---|---|
| `base_url` | Canonical URL. Update if you add a custom domain (and add the `CNAME` file to `templates` handling). |
| `app_store_url` | **Empty while the app is not on the App Store** — the download badge renders as "coming soon". Paste the App Store URL here at launch and it becomes a live download button everywhere. |
| `contact_email` | Used in the footer, support page and privacy policy. Until set, a red placeholder is rendered so the gap is impossible to miss. |
| `publisher_name` | "Published by" in the footer and privacy policy. Same placeholder behavior. |
| `github_url` | Footer source link. |

## Design

A port of the app's `DesignSystem` package (see the VoiceTale iOS repo):

- Dark-first palette: background `#100B08`, surface `#1C1410`, warm amber accent
  `#C4923F`, parchment `#F5E9D0`, slate `#708090` for sleep-sound sections,
  text in warm creams.
- Typography: Epilogue (headings), New York / system serif (body — Apple
  devices get the real New York, like the app), Manrope (labels, uppercase
  and tracked, like the app's overlines).
- Favicons, the touch icon and the social share image are generated at build
  time in `scripts/build.py` (stdlib PNG writer, no image dependencies).

## Deployment

`.github/workflows/deploy.yml` triggers on push to `main` or `master`:

checkout → setup Python → `scripts/build.py` → upload artifact → deploy-pages.
GitHub Pages is configured with source `workflow` (set once via
`gh api` — see the repo Settings → Pages).

## Legacy import slots unlinked titles

The landing page's catalog showcase (six tales with localized titles, authors
and countries) is embedded in `scripts/build.py` as `TALES`; the six stories
match the iOS app's `catalog-seed.json`.

## License

The app repo carries the MIT LICENSE for code. The website text and images are
part of the same project.
