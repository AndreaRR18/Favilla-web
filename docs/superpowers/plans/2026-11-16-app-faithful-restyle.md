# App-faithful restyle and release readiness — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the Favilla site so every page looks like a screen of the app, and make privacy, support, home and `RELEASE.md` ready for the App Store submission.

**Architecture:** The pipeline stays as it is: `templates/*.html` plus `i18n/*.json` go through `scripts/build.py` into `_site`, which `scripts/check_site.py` then checks. A new stdlib gate, `scripts/check_copy.py`, encodes the spec's copy and structure rules. Each task first adds the rules for its own deliverable to that gate, sees it fail, then makes it pass. `site.css` is rewritten around the app's components; `site.js` shrinks to the theme toggle and the fireflies.

**Tech Stack:** HTML, CSS, Python 3 stdlib, vanilla JS (theme and fireflies only), GitHub Pages.

**Spec:** `docs/superpowers/specs/2026-11-16-app-faithful-restyle-design.md`. Approved mockups: `docs/superpowers/specs/mockups/2026-11-16-restyle/` (`app.css` and `pages.css` are the visual reference for every component).

## Global Constraints

- Branch `restyle-app-faithful`. Local commits only: **no push**, no GitHub Pages change.
- Every colour is an app token or an alpha of one (table in `.vibe/skills/favilla-site-brand/SKILL.md`). The only literals allowed are the forest palette (`Color+Forest.swift`) and the recording coral `#FF4B4B` / `#E03030`.
- Fonts: Epilogue (headings), New York / `ui-serif` (body), Manrope (labels). No fourth family.
- CSP unchanged: no `style=""` attribute, no inline script except `THEME_SCRIPT` (its hash is recomputed automatically).
- Nothing third-party: no CDN, analytics, cookies or forms.
- Phone mockup and Forest stay dark in both themes.
- Small text never uses `--text-tertiary` (fails AA). Subtitles, notes and captions use `--text-secondary`.
- Copy in all 5 languages in the same commit. Registers: tu (it), du (de), tú (es), **vous** (fr). No `!`. No sparkle emoji.
- Never describe sleep sounds, purchases as present, folders or tags as visible features, or price promises.
- On the site: only the publisher's **email** and **name**. Never phone or address (those go only in `RELEASE.md`).
- URLs stay stable: `index.html`, `privacy.html`, `support.html`, `404.html`, with `<lang>/` prefixes for it, fr, de, es.
- Full gate after every task: `python3 scripts/build.py --out _site && python3 scripts/check_site.py _site && python3 scripts/check_copy.py _site`

## Review Focus

1. **Long German and French labels at 375 px.** A tab label like "Datenschutz", or a row title, must not overflow the pill or push the page sideways. Test: Task 2 caps tab labels at 11 characters in the gate; Task 7 checks for horizontal scroll in every language.
2. **JavaScript blocked.** All content must be visible, FAQs must open, and the theme falls back to the OS setting. Test: Task 2's gate forbids `reveal` and the `js` class in `THEME_SCRIPT`; Task 7 loads pages with JS off.
3. **404 at a nested path** (e.g. `/Favilla-web/it/missing/x`). The tab bar, back capsule and assets must use root-relative URLs. Test: Task 6's gate requires every `href`/`src` on `404.html` to start with the base path or `mailto:`.
4. **Light theme.** The phone and forest must stay dark, and row text must keep its contrast on `#F0EBE3`. Test: Task 7 visual pass in light mode at both widths.
5. **Reduce Motion.** Nothing may drift or pulse. Test: Task 2's gate checks that `site.css` contains a `prefers-reduced-motion: reduce` block naming every animated selector (`.sky .fly`, `.ff`, `.faq summary svg`).

---

### Task 1: Copy gate and the price promise

**Files:**
- Create: `scripts/check_copy.py`
- Modify: `i18n/{en,it,fr,de,es}.json` (`hero.badge_note`), `run.sh`, `.github/workflows/deploy.yml`

**Interfaces:**
- Produces, in `scripts/check_copy.py` (stdlib; imports `LANGS`, `PAGES`, `load_i18n`, `ROOT` from `build`):
  - `check_strings(strings: dict[str, dict[str, str]]) -> list[str]` — copy rules on the flattened dictionaries
  - `check_pages(out: str, config: dict) -> list[str]` — structure rules on built HTML; parse with `html.parser`, no regex on markup
  - `check_release(out: str, base_url: str) -> list[str]` — empty until Task 7
  - `main()` — reads `config.json`, runs all three, prints each error, exits 1 if any (same style as `check_site.py`)
  - `FORBIDDEN: dict[str, list[str]]` — the lists below, so later tasks can extend them

- [ ] **Step 1: Write the rules in `check_strings`.** Error text is `"<lang>: <key>: <rule>"`. Matching is case-insensitive substring unless a word boundary is noted.
  - no `!` in any value
  - none of `storeTextWatch.always`: `premium`, `subscription`, `abbonamento`, `abonnement`, `suscripción`, `discount`, `sconto`, `% off`
  - none of `storeTextWatch.sleepSoundsOff`: `sleep sound`, `white noise`, `rumore bianco`, `suoni per dormire`, `bruit blanc`, `weißes rauschen`, `ruido blanco`, `sonidos para dormir`
  - no price promise: `stays that way`, `resterà così`, `ça ne changera pas`, `bleibt so`, `seguirá así`, `free forever`, `per sempre gratis`
  - French only: no `\btu\b`, `\bton\b`, `\btes\b`, `\bta\b` (word boundaries)
  - no ✨ ⭐ 🌟 💫 characters
- [ ] **Step 2: Wire the gate.** Add `python3 scripts/check_copy.py _site` after `check_site.py` in `run.sh` and as a step after the "check" step in `deploy.yml`, keeping the job's `permissions` as they are.
- [ ] **Step 3: Run the gate and see it fail.** Run the full gate. Expected: FAIL, 5 errors on `hero.badge_note`, one per language ("price promise").
- [ ] **Step 4: Fix `hero.badge_note` in all 5 languages.** Drop the last clause and keep the rest, e.g. it "Gratis · niente pubblicità · nessun tracciamento", en "Free · no ads · no tracking".
- [ ] **Step 5: Run the full gate.** Expected: PASS, three "OK" lines.
- [ ] **Step 6: Commit** `Add copy gate; drop the price promise from the hero note`.

### Task 2: Components, shell, tab bar and lean JS

**Files:**
- Rewrite: `assets/css/site.css` (port `mockups/.../app.css` + `pages.css`, tokens on `:root[data-theme]` as today)
- Modify: `templates/base.html`, `scripts/build.py` (`THEME_SCRIPT`, `ICONS`, `tab_bar_html`, `lang_menu_html`, nav context), `assets/js/site.js`, `i18n/*.json` (new `tabbar.*`, `a11y.back`; drop `nav.*`)
- Test: `scripts/check_copy.py` (`check_pages`)

**Interfaces:**
- Consumes: `check_pages` (Task 1).
- Produces, all in `scripts/build.py`:
  - `ICONS: dict[str, str]` — 24×24 SF-Symbols-style paths in `currentColor`. Keys: `mic`, `cloud`, `moon`, `sun`, `book`, `books`, `tree`, `info`, `shield`, `person_slash`, `eye_slash`, `chevron`, `back`, `pause`, `waveform`, `phone`. Exposed to templates as `{{icon_<key>}}`; take the path data from the mockups.
  - `tab_bar_html(i18n: dict, current: str, home: str, privacy: str, support: str) -> str` — `current` is one of `"index"`, `"catalog"`, `"privacy"`, `"support"`, `""`. Renders `<nav class="tabbar" aria-label="{a11y.tabs}">` with 4 `a.tab`: Favilla (firefly mark), Catalogo (`{home}#catalog`), Privacy, Supporto. The current one gets `aria-current="page"`.
  - `lang_menu_html(i18n: dict, lang: str, href_for: Callable[[str], str]) -> str` — `<details class="lang-menu">` whose `<summary class="round">` shows the current code, plus a list of 5 links (current one `aria-current="true"`). Replaces `lang_switcher_html`.
  - Template context keys: `{{tab_bar}}`, `{{lang_menu}}`, `{{theme_toggle}}` (now `button.round`), `{{back_link}}` (empty on index; on other pages `<a class="back" href="…">{icon_back}Favilla</a>`).
  - CSS classes (names from the mockups, reused by Tasks 3–6): `page`, `page-wide`, `toolbar`, `navbar`, `round`, `back`, `wordmark`, `large-title`, `hero-sub`, `hero-lead`, `capsule`, `caption`, `section`, `section-title`, `group`, `row`, `row.link`, `t`, `s`, `tile`, `emoji`, `chev`, `group-footer`, `prose`, `data`, `kv`, `faq`, `answer`, `forest`, `phone`, `screen`, `fly`, `fly-sm`, `sky`, `tabbar`, `tab`, `footer`, `todo`.

- [ ] **Step 1: Add the structure rules to `check_pages`.** For every built page:
  - exactly one `nav.tabbar` with 4 `a.tab`
  - exactly one `aria-current="page"` inside it, except on `404.html` (zero)
  - one `details.lang-menu` holding 5 links
  - no element with class `reveal`, `glass`, `grid-3`, `grid-4` or `kicker`
  - one `h1`

  Plus three global rules:
  - `THEME_SCRIPT` contains neither `classList.add("js")` nor `fv-ready`
  - every `tabbar.*` value is ≤ 11 characters
  - `site.css` has a `prefers-reduced-motion: reduce` block that mentions `.sky .fly`, `.ff` and `.faq summary svg`
- [ ] **Step 2: Run the gate and see it fail.** Expected: FAIL, missing tab bar and present `reveal`/`kicker` on every page.
- [ ] **Step 3: Rewrite `THEME_SCRIPT`.** It only sets `data-theme` from `localStorage["fv-theme"]` or the OS setting. Remove the `js` / `fv-ready` / 3-second machinery from the script, CSS and `site.js`.
- [ ] **Step 4: Add `ICONS`, `tab_bar_html` and `lang_menu_html`, and the new context keys, in `build.py`.** Delete `lang_switcher_html` and the `nav_links` building, including the 404 branch. On 404 every href in the shell is `path_prefix + …`.
  - Tab bar labels (`tabbar.home`, `tabbar.catalog`, `tabbar.privacy`, `tabbar.support`, `a11y.tabs`) in 5 languages: en Favilla/Catalog/Privacy/Support · it Favilla/Catalogo/Privacy/Supporto · fr Favilla/Catalogue/Vie privée/Aide · de Favilla/Katalog/Datenschutz/Hilfe · es Favilla/Catálogo/Privacidad/Ayuda.
  - Add `a11y.back` with the accessible label of the back link.
- [ ] **Step 5: Rewrite `templates/base.html`.**
  - Toolbar: wordmark, spacer, `{{lang_menu}}`, `{{theme_toggle}}`. On pushed pages `{{back_link}}` comes first.
  - A `div.sky` with 4 `span.fly.fly-sm.fly-pos-1…4`, positions in CSS.
  - Footer: ©, publisher, Privacy, Support, the 5 language codes, the two legal notes.
  - `{{tab_bar}}` and the cursor firefly.
  - Keep the skip link and `id="main"`.
- [ ] **Step 6: Rewrite `site.css` from the mockups.**
  - Keep the `@font-face` blocks and both theme token sets.
  - Add the documented light-mode adaptations (dark lines, `#8A6428` amber text).
  - Apply the AA rule above.
  - Add `body { padding-bottom: 120px }` so the tab bar never covers the footer.
  - Style `details.lang-menu` as a small glass popover under the round button.
  - Keep the cursor-firefly styles.
- [ ] **Step 7: Trim `site.js`.** Keep: theme toggle (`button.round` with `aria-pressed`), cursor firefly with its current rules (fine pointer, dark only, still under Reduce Motion), and a click outside an open `details.lang-menu` closes it. Remove the reveal observer and the stars.
- [ ] **Step 8: Run the full gate.** Expected: PASS. Then open `./run.sh` and check that the shell renders on all four pages. Page bodies are still the old markup until Tasks 3–6.
- [ ] **Step 9: Commit** `Rebuild the shell on the app's components: toolbar, tab bar, lean JS`.

### Task 3: Home

**Files:**
- Rewrite: `templates/index.html`
- Modify: `scripts/build.py` (`TALES[*]["emoji"]`, `catalog_rows_html`, `recording_phone_html`, `forest_svg` sizing), `i18n/*.json` (home keys)
- Test: `scripts/check_copy.py`

**Interfaces:**
- Consumes: `ICONS`, all component classes (Task 2).
- Produces:
  - `catalog_rows_html(lang: str) -> str` — one `div.row` per tale: `span.tile > span.emoji`, `span.t` with the title, `span.s` with `showcase.caption` formatted from country, author and year (caption order "Paese · Autore, anno").
  - `recording_phone_html(i18n: dict) -> str` — `div.phone[aria-hidden=true]` with the recording screen from `home-a.html`. Fly positions are classes, not `style=""`. Pause and Finish labels come from new keys `home.rec_pause` / `home.rec_finish`, copying the app's own strings from `Localizable.xcstrings` (it Pausa/Fine).
  - Context keys `{{catalog_rows}}` and `{{recording_phone}}`.
  - Section ids: `how`, `catalog`, `forest`, `app`, `privacy`.

- [ ] **Step 1: Add the home rules to `check_pages` for `index.html` in every language.**
  - `h1.large-title`
  - `div.phone`
  - `#catalog .row` count = 6, each containing `.emoji`
  - `#how .row` count = 3
  - `#app .row` count = 4
  - `#privacy .row` count = 4: 3 plain rows plus 1 `a.row.link` pointing at `privacy.html`
  - one `.forest`
  - no ids `idea` or `why`
  - no `<svg class="mascot">` or `hero-wave`
- [ ] **Step 2: Run the gate and see it fail.** Expected: FAIL on missing `.phone`, `#catalog .row` and the rest.
- [ ] **Step 3: Update `TALES` and add the two helpers in `build.py`.** Emoji, in `TALES` order: 🧺 🦢 🏠 🐢 🍑 🐒 (from `catalog-seed.json`). Remove `TALES`' `tale1/2/3_title` and the `tale_cards` context. Change `showcase.caption` in all 5 languages to `{country} · {author}, {year}`, the order the mockup shows.
- [ ] **Step 4: Rewrite `templates/index.html` in the spec's order (§5.2).** Hero, how, catalog plus footnote, forest card (copy `tabs.frs_name` and `tabs.frs_body`), app (Stories, Catalog, Forest, Info rows), privacy "in 30 seconds" plus link row plus one-line note, "Made by one person." with a centred `.fly`.
- [ ] **Step 5: Update the home copy in 5 languages.**
  - Delete `idea.*`, `personas.*`, `science.*`, `mock.*`, the `*.kicker` keys and `tabs.*_b1..b3`.
  - Rename `privacy.s1..s4` to the three summary rows: `privacy.sum_account_t/_b`, `privacy.sum_tracking_t/_b`, `privacy.sum_yours_t/_b`. Text: no account / no tracking, ads or analytics / recordings stay yours, on your device and in your private iCloud. Use the app draft's "In breve" wording in each language.
  - Check every claim against `/Users/andrea/developer/iOS/Favilla/docs/app-store-metadata.md`. Drop "and more with every update" unless that file says it.
  - Stories row body: no folders or tags.
- [ ] **Step 6: Run the full gate.** Expected: PASS.
- [ ] **Step 7: Commit** `Rebuild the home as app screens: recording hero, catalog list, forest`.

### Task 4: Privacy page

**Files:**
- Rewrite: `templates/privacy.html`
- Modify: `i18n/*.json` (`privacy_page.*`, `meta.desc_privacy`), `scripts/build.py` (privacy context)
- Test: `scripts/check_copy.py`

**Interfaces:**
- Consumes: shell and components (Task 2), `privacy.sum_*` keys (Task 3) for the "In 30 seconds" group.
- Produces: section ids `who`, `data`, `microphone`, `sharing`, `children`, `deletion`, `rights`, `site`, linked from the in-page index (`check_site.py` already fails on a dangling `#fragment`).

- [ ] **Step 1: Add the privacy rules to `check_pages` and `FORBIDDEN`.** For `privacy.html` in every language:
  - the 8 ids exist
  - `.toc a.row` count = 8
  - `#who .kv .row` count = 2 (name, email)
  - no `tel:` href anywhere in `_site`

  For the `privacy_page.*` strings:
  - none of: it `ogni suono`, en `every sound`, fr `chaque son`, de `jeder Klang`, es `cada sonido`
  - no imported-sounds wording, matched with word boundaries so "important"/"importante" pass: `\bimport(ed|s)?\b`, `\bimporti\b`, `\bimportez\b`, `\bimportierst\b`, `\bimportas\b`
  - `privacy_page.updated` contains a digit day (regex `\b\d{1,2}\b`)
  - key `privacy_page.backup_p` exists
- [ ] **Step 2: Run the gate and see it fail.**
- [ ] **Step 3: Write the copy in 5 languages from `/Users/andrea/developer/iOS/Favilla/docs/privacy-policy.md`.** Keep one key per paragraph, under `privacy_page.*`. Delta per spec §5.3:
  - `updated`: "16 November 2026 · App 1.0", or the actual day of the commit
  - `data_r1..r3` rows: recordings/titles/folders/tags; texts; preferences (language, intro seen, Fireflies switch, game sound volume — no purchase cache). Remove the old `r3` imported sounds row and renumber.
  - `data_note` with the silent notifications
  - new `backup_p`: Documents folder → device iCloud backup; three places, all in the user's Apple account, none reachable by the developer
  - `sharing_t/_p` (share sheet behind the grown-up check; lock screen and media controls stay on the device)
  - `children_p`: parent records, parental gate (sum of two two-digit numbers) for links, purchases and sharing; Forest games without links, purchases or ads
  - `rights_p` with the local authority: it Garante, fr CNIL, others generic as in the draft
  - `purch_p`: no purchases in 1.0, Apple-only if ever, page updated first
  - new `site_t/_p`: no cookies or analytics, GitHub Pages, IP only to GitHub
  - `meta.desc_privacy` matches the page
  - Drop any sentence the draft or the code doesn't back.
- [ ] **Step 4: Rewrite `templates/privacy.html` per spec §5.3 and `privacy-a.html`.** The data section is `div.group.data` with `dl` rows. The "Chi siamo" group shows only name and email: `{{publisher}}`, `{{contact_email}}`.
- [ ] **Step 5: Run the full gate.** Expected: PASS.
- [ ] **Step 6: Commit** `Align the privacy policy with the 1.0 build, in the app's list style`.

### Task 5: Support page

**Files:**
- Rewrite: `templates/support.html`
- Modify: `i18n/*.json` (`support_page.*`, `meta.desc_support`)
- Test: `scripts/check_copy.py`

**Interfaces:**
- Consumes: shell and components (Task 2).
- Produces: FAQ keys `support_page.faq_<slug>_q/_a`, rendered in this order: `coming`, `account`, `where`, `mic`, `sum`, `locked`, `sync`, `share`, `long`, `ai`, `languages`, `fireflies`, `forest`, `delete`.

- [ ] **Step 1: Add the support rules to `check_pages`.**
  - `.faq details` count = 14 and each `summary` has text
  - one `a[href^="mailto:"]` inside `.kv` when `contact_email` is set, otherwise a `mark.todo`
  - one `a.row.link` pointing at `privacy.html`
  - no `tel:`
- [ ] **Step 2: Run the gate and see it fail.**
- [ ] **Step 3: Write the 14 Q&As in 5 languages.** Base text is `/Users/andrea/developer/iOS/Favilla/docs/support-page.md` (en, it) plus the release prompt's section C:
  - `mic`: "Open Settings" is behind the grown-up check, then Settings › Favilla › Microphone; finish a call first
  - `sum`: grown-up check for anything leaving the app, never asks for personal data
  - `locked`: recording continues, microphone indicator plus Pause/Finish
  - `long`: title up to 100 characters, text up to 20,000
  - `forest`: dark appearance plus the Fireflies switch
  - `coming` keeps today's text.
  - Remove the old `q6` "listen elsewhere".
  - `meta.desc_support` matches the page.
- [ ] **Step 4: Rewrite `templates/support.html` per `support-a.html`.** The contacts group has the email row only. The note under it reuses `contact_hint`.
- [ ] **Step 5: Run the full gate.** Expected: PASS.
- [ ] **Step 6: Commit** `Rebuild support with the parents' real questions`.

### Task 6: 404 in the forest

**Files:**
- Rewrite: `templates/404.html`
- Modify: `scripts/build.py` (404 context)
- Test: `scripts/check_copy.py`

**Interfaces:**
- Consumes: `forest_svg()`, the `forest` class, `back_link`, `tab_bar_html(current="")`.

- [ ] **Step 1: Add the 404 rules to `check_pages`.**
  - `404.html` has one `.forest` containing the `h1`
  - every `href`/`src` value starts with the base path from `config.json` (`urlparse(base_url).path`) or is `mailto:`
- [ ] **Step 2: Run the gate and see it fail.**
- [ ] **Step 3: Rewrite `templates/404.html`.** A forest card with `notfound.title` as `h1`, `notfound.lead`, and a capsule link home with `notfound.cta`. No wave.
- [ ] **Step 4: Run the full gate.** Expected: PASS.
- [ ] **Step 5: Commit** `Lose the 404 in the night forest`.

### Task 7: Release file, docs, cleanup and visual pass

**Files:**
- Create: `RELEASE.md`
- Modify:
  - `README.md` ("Going live" and "Design")
  - `.vibe/skills/favilla-site-brand/SKILL.md` (third adaptation: small text on `--text-secondary`; component list; no `.reveal`). Untracked, so edit it but don't commit it.
  - `scripts/build.py`: delete everything with no caller left (`mascot_svg`, `wave_svg`, `HERO_AMPS`, unused `GLYPHS`, `TALES`' old fields). The OG image and favicon code stays.
  - `scripts/check_copy.py` (`check_release`)

**Interfaces:**
- Consumes: built `_site` (URLs).

- [ ] **Step 1: Implement `check_release(out, base_url)`.**
  - Every `base_url…` URL in `RELEASE.md` resolves to a file in `out`.
  - The file contains a privacy URL and a support URL for each of the 5 languages.
  - It contains no `{{`.
- [ ] **Step 2: Run the gate and see it fail** (no `RELEASE.md` yet).
- [ ] **Step 3: Write `RELEASE.md`, with the content of the release prompt's section E plus its §3 and §4.**
  - Privacy and Support URLs for en (root), it, fr, de, es
  - Marketing URL and `© 2026 [TITOLARE]`
  - publisher, address, email and phone as `[...]` for the EU trader status
  - App Privacy "Data Not Collected", tracking No, with the reason
  - Kids notes, age band recommended "5 and under"
  - reviewer notes: no login; how to record; microphone and background audio; where the parental gate is (About › Privacy › policy link; Record › microphone denied › Open Settings); silent notifications and `aps-environment` only for CloudKit
  - "Before submitting" and "Launch day" lists
- [ ] **Step 4: Update `README.md`.**
  - Going live point 4: imported sounds are gone; `app_store_url` stays empty until approval; phone and address only in `RELEASE.md`.
  - Design section: components, tab bar, no reveal.
  - Security: unchanged CSP.
- [ ] **Step 5: Delete dead code in `build.py`.** Run the full gate. Expected: PASS.
- [ ] **Step 6: Visual pass with `./run.sh`.** Pages: index, privacy, support in en, it, de, plus 404, each at 1280 px and 375 px, dark and light. Check:
  - no horizontal scroll (`document.documentElement.scrollWidth === innerWidth`)
  - tab bar doesn't cover the footer
  - phone and forest dark in light mode
  - with JavaScript disabled, everything shows and FAQs open
  - with Reduce Motion, nothing moves
  - Network tab: only same-origin requests

  Fix what fails within this task.
- [ ] **Step 7: Commit** `Add RELEASE.md, update README, drop dead drawing code`.
- [ ] **Step 8: Hand-over note to the owner.** Not a file; this goes in the final message. List:
  - files and commits
  - final URLs per language
  - "Da compilare": `publisher_name`, `contact_email` in `config.json`; address, phone and domain in `RELEASE.md`
  - FR/DE/ES sections to check with a native speaker
  - differences from the app's `docs/privacy-policy.md`, especially the iCloud backup sentence, which the app draft lacks
  - site-vs-code contradictions left as they are
