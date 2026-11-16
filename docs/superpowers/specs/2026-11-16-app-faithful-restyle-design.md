# Favilla-web — restyle fedele all'app (design)

Data: 2026-11-16 · Stato: **bozza da approvare** · Repo: `Favilla-web` (branch di partenza `main`)
Bozze approvate in chat: `docs/superpowers/specs/mockups/2026-11-16-restyle/` (`home-a.html`, `privacy-a.html`, `support-a.html`; servirle con `python3 -m http.server` dalla radice del repo e aprire quel percorso).

## 1. Intento e perché

Il sito oggi funziona ma **sembra generato da un'AI**. Lo schema è quello di una landing page qualsiasi:
- hero centrato con la seconda riga in ambra
- un'etichetta maiuscola spaziata sopra ogni titolo
- griglie uniformi di card in vetro da 3 o 4 colonne
- passi numerati dentro cerchi
- ogni blocco che appare allo scroll

L'autore vuole che il sito **sembri l'app Favilla**, non una pagina che la descrive. Un genitore che arriva dal link dell'App Store deve riconoscere le stesse forme che troverà sul telefono.

Nello stesso lavoro il sito diventa **pronto per il rilascio**: privacy, supporto, home e metadati si allineano al codice dell'app 1.0, e un file `RELEASE.md` raccoglie tutto ciò che va incollato in App Store Connect.

Fonte: il prompt "Favilla-web pronto per il rilascio", incollato dall'autore in chat il 2026-11-16, d'ora in poi **il prompt di rilascio**. Sostituisce per questo sito `docs/website-privacy-prompt.md`. I testi di partenza nelle 5 lingue sono quelli della bozza `docs/privacy-policy.md` e di `docs/support-page.md` nel repo dell'app. Se sito e codice divergono, vince il codice.

## 2. Obiettivi, non-obiettivi, anti-obiettivi

**Obiettivi**
- Ogni pagina è costruita con i componenti dell'app:
  - titolo grande allineato a sinistra
  - liste raggruppate con riquadro icona da 44 pt, titolo serif, sottotitolo e freccina
  - pulsanti tondi e capsule in vetro
  - barra delle schede a pillola
  - lucciola a punto più tre anelli
  - Foresta notturna con la sua palette
- Privacy, supporto e home contengono esattamente i fatti delle sezioni B, C e D del prompt di rilascio, in 5 lingue. Ogni frase ha riscontro nel codice o nella bozza dell'app.
- `build.py` e `check_site.py` restano verdi. La CSP resta quella di oggi.

**Non-obiettivi**
- Nessun nuovo stack: restano HTML scritto a mano, CSS, `build.py` stdlib e GitHub Pages.
- Nessuna nuova palette o font. Restano i token dell'app (tabella in `.vibe/skills/favilla-site-brand/SKILL.md`) ed Epilogue, New York e Manrope.
- Nessuna nuova pagina oltre a index, privacy, support e 404, in 5 lingue. I contatti vivono in supporto e privacy, non in una pagina `/contact/` a parte.
- Favicon, apple-touch-icon e immagine OG restano invariati.

**Anti-obiettivi** (un fallimento anche con la build verde)
- Tornare a hero centrato, kicker maiuscoli sopra i titoli, griglie di card uguali o animazioni di comparsa allo scroll.
- Icone sparkle (✨), fiamme o candele, bianco puro, arancione saturo, colori inventati.
- Descrivere funzioni che la build non ha: suoni per dormire e acquisti sono spenti, cartelle e tag non hanno interfaccia.
- Promesse di prezzo ("gratis per sempre", "e resterà così") o parole vietate da `storeTextWatch` (premium, abbonamento, sconto…).
- Inventare dati del titolare: restano segnaposto rossi finché `config.json` non li ha.
- Promettere più di quanto il codice mantiene. Scrivere "non abbiamo accesso" e "nessun SDK di terzi", mai "sicuro al 100%".

## 3. Vincoli

- **CSP** (`build.py`): nessuno stile inline e nessuno script inline, tranne lo script del tema autorizzato via hash. Le bozze usano `style="left:..."` per posizionare le lucciole: nella build vanno sostituiti con classi (`.fly-pos-1`… in CSS). `check_site.py` lo blocca comunque.
- **Nessuna richiesta a terzi**: font self-hosted, niente CDN.
- **Telefono e Foresta sempre scuri** in entrambi i temi: mostrano l'interfaccia notturna dell'app.
- **Accessibilità**: AA sul testo, focus visibile, skip link, "Riduci movimento" rispettato, nessun contenuto dipendente da JavaScript.
- **Lingue**: 5 dizionari in parità. In francese il registro è *vous*, nelle altre lingue *tu/du/tú*.
- **Lavoro non committato su `main`** (allineamento palette, copy FR, iOS 26.5, README, SKILL.md). Decisione dell'autore: si porta nel branch del restyle e si committa lì come **primo commit, separato**, così da non mescolarlo con il restyle.
- **Dati personali sul sito** (decisione dell'autore): sul sito compaiono solo l'**email** e il **nome del titolare** (privacy e footer). Telefono e indirizzo vanno solo in App Store Connect, cioè nel file `docs/app-store-connect.md`, non pubblicato.

## 4. Approcci considerati

| Approccio | Cosa comporta | Esito |
|---|---|---|
| **A. Fedele all'app** | Pagine composte come schermate iOS: liste raggruppate, titoli grandi, tab bar a pillola, telefono con la schermata di registrazione | **Scelto dall'autore** dopo aver visto le bozze |
| B. Editoriale caldo | Sito da libro della buonanotte, molta tipografia serif, poca interfaccia | Scartato: più lontano dall'app, rischio di un altro genere "da template" |
| C. Solo CSS, template invariati | Ristilizzare le classi esistenti senza toccare la struttura | Scartato: la struttura (griglie di card, passi numerati) è proprio ciò che sembra AI |

Come costruirlo: si riscrivono `site.css`, i template e la parte di `build.py` che genera i disegni. La pipeline (template + i18n → `_site`) resta invariata, perché funziona ed è già protetta dai controlli.

## 5. Design deciso

### 5.1 Componenti (da `mockups/.../app.css` e `pages.css`)

| Componente | Origine nell'app | Regole |
|---|---|---|
| Titolo grande | Large title di Catalogo | Epilogue 700, allineato a sinistra, nessun accento ambra nel titolo |
| Titolo di sezione | Intestazioni di gruppo | Epilogue 600, ~24 px (`heading2`), niente maiuscolo né tracking |
| Gruppo / riga | Liste del Catalogo | Raggio 16, sfondo `--bg-secondary`. Separatore inset che parte dopo il riquadro (76 px), oppure a 16 px se la riga non ha riquadro. Freccina solo sulle righe che sono link |
| Riquadro icona | `StoryEmojiView` (44 pt, raggio 23 %, AccentSoft) | Icone SVG stile SF Symbols in `--accent`. Le fiabe usano la propria emoji resa come sagoma ambra con `color: transparent; text-shadow: 0 0 0 var(--accent)` |
| Nota sotto il gruppo | Footer di sezione iOS | Testo piccolo sotto il gruppo, al posto delle `section-footnote` |
| Pulsante tondo in vetro | Barra superiore | 44 px: lingua e tema in alto a destra |
| Capsula in vetro | — | Pulsante App Store con riquadro lucciola, titolo e nota |
| Pulsante indietro | Barra di navigazione push | Capsula "‹ Favilla" sulle pagine interne |
| Tab bar | `AppTabView` | Pillola di vetro fissa in basso **a ogni larghezza** (vista e approvata). Voci: Favilla (lucciola), Catalogo (`index#catalogo`), Privacy, Supporto. Voce attiva in ambra su capsula scura |
| Lucciola | `FireflyField` | Nucleo `#C4923F` più anelli piatti 0.24 / 0.14 / 0.08 |
| Foresta | `Color+Forest.swift` | Card con raggio 16, cielo `#070B1A`→`#17243D`, tre file di pini, luna `#EDE7D2`, lucciole nei 5 colori, pulsazione lenta |
| Telefono | Schermata di registrazione | Timer monospace 00:08, onda a puntini ambra in un pozzetto di vetro, REC in corallo, Pausa (vetro più ambra) e Fine (corallo). Nascosto sotto gli 860 px |
| FAQ | Disclosure group | `<details>`/`<summary>` con freccina che ruota di 90°. Nessun JavaScript |
| Riga chiave/valore | Scheda contatto | Etichetta a sinistra, valore a destra. Segnaposto rossi "da compilare" |

Tema: resta il meccanismo di oggi. Lo script inline imposta `data-theme`, la scelta si ricorda con `localStorage` e il pulsante luna/sole la cambia. Il trucco `:has(#theme:checked)` delle bozze **non** va in produzione.

Lingua: il pulsante tondo "IT" apre un `<details>` con le 5 lingue (lingua corrente in ambra). Il footer riporta anche la fila `EN IT FR DE ES`.

### 5.2 Home (ordine approvato)

1. Barra superiore: wordmark "favilla" (puntino della *i* in ambra), pulsanti lingua e tema.
2. Hero: titolo grande (`hero.h1a`), sottotitolo serif (`hero.h1b`), lead, capsula App Store, nota. A destra il telefono con la registrazione. La nota perde la promessa di prezzo: "Gratis · niente pubblicità · nessun tracciamento", senza "e resterà così".
3. **Come funziona**: gruppo di 3 righe (Registra, Resta tua, Buonanotte) con icone microfono, nuvola e luna.
4. **Catalogo** (`id="catalogo"`): le 6 fiabe di `TALES` come righe, con sagoma emoji, titolo e "Paese · Autore, anno". Sotto, la nota "…e altre 40".
5. **Foresta**: card notturna con titolo e testo.
6. **Dentro l'app**: 4 righe, una per scheda dell'app (Storie, Catalogo, Foresta, Info) con le icone della tab bar dell'app.
7. **Privacy in 30 secondi** (sezione D del prompt): 3 righe (nessun account; nessun tracciamento; le registrazioni restano tue e nel tuo iCloud privato), poi una riga-link "Leggi l'informativa completa" e sotto la nota "In una riga…". Sostituisce le 4 righe della bozza; "Niente IA" resta nel lead dell'hero.

Ogni affermazione della home va confrontata con `docs/app-store-metadata.md` e con il codice. Esempio: "46 fiabe, e altre a ogni aggiornamento" va verificato o tolto.
8. **Fatta da una sola persona.**: lucciola centrata, titolo e paragrafo, come la schermata Info.
9. Footer: ©, link Privacy e Supporto, lingue, nota "non affiliato ad Apple" e "iCloud è un marchio".

**Tolte dalla home** rispetto a oggi (bozza approvata e decisione confermata dall'autore):
- "L'idea" (`idea.*`)
- "Per due persone" (`personas.*`)
- "Perché conta" (`science.*`)
- l'onda decorativa sotto l'hero
- l'indicatore di scroll
- i link testuali nella nav

Le chiavi i18n non più usate si rimuovono dai 5 dizionari.

### 5.3 Privacy (pagina `privacy.html`)

Ordine:
1. Titolo grande "Privacy", poi la riga "Aggiornata il <giorno mese anno> · Favilla 1.0" (data reale dell'ultima modifica, giorno compreso) e il lead.
2. **In 30 secondi**: 3 righe con icona. È lo stesso riepilogo richiesto per la home dalla §3.4 del prompt; in home lo rappresenta il gruppo "Resta in famiglia".
3. **In questa pagina**: indice a righe con freccina, che punta alle ancore.
4. Chi siamo (righe chiave/valore: titolare ed email; niente indirizzo né telefono).
5. Quali dati, e dove stanno. Visivamente sono righe dato / perché / dove: è la stessa tabella del prompt, in forma di lista. Sotto vanno due note:
   - **notifiche silenziose**: iOS può usarle per allineare i dispositivi; non contengono dati e lo sviluppatore non le riceve
   - **copia di backup**: i file audio stanno nella cartella Documenti dell'app, inclusa nel backup iCloud del dispositivo se l'utente lo usa. La voce può quindi stare in tre posti dell'utente (dispositivo, database privato iCloud, backup iCloud), tutti nel suo account Apple e nessuno accessibile allo sviluppatore
6. Le sezioni in prosa:
   - Microfono
   - Condivisione e schermata di blocco: foglio di condivisione dietro controllo parentale; titolo e avanzamento nella Live Activity e nei controlli multimediali, solo sul dispositivo
   - Cosa non facciamo (con gli appunti letti solo su "Incolla")
   - Bambini, con tre punti:
     - app in cui registra il genitore: microfono del genitore, dati nel suo iCloud privato, niente dal bambino
     - link esterni, acquisti e condivisione dietro un controllo parentale (somma di due numeri a due cifre)
     - giochi della Foresta senza link, acquisti né pubblicità
   - Conservazione e cancellazione: resta "sparisce anche dagli altri dispositivi", senza tempi esatti
   - Diagnostica
   - I tuoi diritti: 30 giorni, autorità del proprio Paese; in Italia il Garante, in Francia la CNIL come nella bozza
   - Acquisti: la 1.0 non ha acquisti; in futuro solo tramite Apple e pagina aggiornata prima. Niente "ogni suono"
   - **Questo sito**: nessun cookie né analisi, hosting GitHub Pages, IP solo a GitHub
   - Modifiche

Cambi di contenuto rispetto a oggi (sezione B del prompt):
- via la riga "Suoni che importi"
- preferenze complete: lingua, introduzione, interruttore Lucciole, volume dei suoni dei giochi. **Niente** cache di acquisto
- nuove: condivisione e schermata di blocco, notifiche silenziose, backup iCloud, Questo sito
- Bambini estesa
- Garante
- data con il giorno

Ogni frase che non si può verificare nel codice o nella bozza dell'app si toglie.

### 5.4 Supporto (pagina `support.html`)

- Titolo grande e lead.
- **Domande**: `<details>`, risposte brevi, testo base da `docs/support-page.md` dell'app e dalla sezione C del prompt.
  - Già oggi sul sito (si tengono):
    - quando possiamo usarla (finché `app_store_url` è vuoto)
    - serve un account
    - dove finiscono le registrazioni
    - spegnere le lucciole
    - come elimino una storia
  - Nuove:
    - microfono negato / non registra: "Apri Impostazioni" nell'app è dietro il controllo parentale, poi Impostazioni › Favilla › Microfono; chiamate in corso
    - perché mi chiede una somma: controllo per adulti, mai dati personali
    - registrare con lo schermo bloccato
    - le storie non compaiono su un altro dispositivo
    - come condivido un audio
    - testo troppo lungo: titolo 100 caratteri, testo 20.000
    - voci sintetiche o IA
    - lingue
    - Foresta vuota: serve l'aspetto scuro e l'interruttore Lucciole
  - Va via la domanda di oggi "si possono ascoltare anche altrove", coperta dalla sincronizzazione.
- **Contatti**: una riga Email (link `mailto:`), con nota sui tempi di risposta. Niente telefono né indirizzo.
- Riga-link all'informativa sulla privacy.

### 5.5 404

Card Foresta notturna con titolo "Persi nel bosco", lead e capsula "‹ Torna a casa". Nessuna onda.

### 5.6 JavaScript (`site.js`)

**Resta:**
- cambio tema
- lucciola che segue il cursore (solo puntatore fine, solo tema scuro; con "Riduci movimento" sta ferma)
- poche lucciole d'ambiente nel cielo in tema scuro

**Va via:**
- `.reveal` e tutto il meccanismo `html.js` / `fv-ready` / timeout di 3 s, sia nello script inline sia in CSS. Cambiando lo script inline cambia anche l'hash: lo ricalcola già `build.py`.
- le stelle

Senza JavaScript il sito è completo, a parte la lucciola che segue il cursore.

### 5.7 `config.json` e build

- `config.json` non cambia: sul sito servono solo `contact_email` e `publisher_name`, già gestiti con segnaposto rosso e blocco di `app_store_url`.
- `TALES` in `build.py` guadagna il campo `emoji`: 🧺 🦢 🏠 🐢 🍑 🐒, da `catalog-seed.json`.
- I disegni generati (`mascot_svg`, `wave_svg`, l'hero wave, il mock della Libreria) lasciano il posto a: telefono di registrazione, Foresta (riusa `forest_svg` aggiornato), icone di tab bar e righe.
- Nessuna dipendenza nuova.

### 5.8 Fuori dal sito, nello stesso lavoro

- **`RELEASE.md`** nella radice del sito (non pubblicato: `build.py` copia solo `assets/`). Contenuto della sezione E del prompt di rilascio:
  - URL di privacy e supporto per ciascuna delle 5 lingue, letti da `_site/` dopo la build
  - Marketing URL e copyright
  - titolare, indirizzo, email e telefono per lo stato di trader UE, come segnaposto `[...]`
  - App Privacy "Data Not Collected" e tracking No
  - note Kids (fascia consigliata "5 e meno")
  - note per il reviewer
  - gli elenchi "Prima di inviare" e "Il giorno del lancio"
- **Metadati**: `meta.desc_*` di privacy e supporto descrivono quello che la pagina dice.
- **README**: "Going live" aggiornato (il punto 4 sui suoni importati non vale più; regola "`app_store_url` vuoto finché l'app non è approvata"), più la sezione Design del restyle.
- **Nessun push** e nessuna modifica a GitHub Pages: il lavoro si ferma ai commit locali sul branch `restyle-app-faithful`. Il prompt suggeriva `release-readiness`, ma il branch esisteva già.

## 6. Scelte fatte da Claude (da rivedere)

1. **Contrasto dei sottotitoli.** `TextTertiary` dell'app è sotto AA come testo piccolo: 2,9:1 al buio su `#1C1410`, 3,4:1 in chiaro su `#F0EBE3`. Sottotitoli delle righe, note e didascalie usano quindi `--text-secondary`. `--text-tertiary` resta per elementi non testuali (freccine, separatori). È il terzo adattamento documentato e va aggiunto a SKILL.md.
2. **Sagome emoji.** Il colore della sagoma dipende dal font emoji del sistema. Su Windows e Android la forma cambia ma resta ambra, ed è accettato.
3. **Indice nella privacy.** È solo una lista di ancore, nessuno scroll-spy.
4. **Risposte FAQ**: vengono tutte da `docs/support-page.md` o dalla sezione C del prompt. Le tre che nella bozza erano di Claude risultano confermate da `support-page.md`.
5. **Traduzioni FR/DE/ES** del nuovo testo: dove esiste, si parte dalla bozza dell'app (già in 5 lingue); il resto è scritto da Claude, marcate "da far verificare a un madrelingua" nella consegna.
6. **README e SKILL.md** si aggiornano nello stesso lavoro (sezione Design, componenti, adattamento del contrasto, niente `.reveal`).
7. **Indirizzo sul sito.** Il prompt di rilascio chiede `publisher_address` in privacy e footer se l'indirizzo è fornito. In chat l'autore ha scelto "solo email sul sito", e vale questa scelta. L'indirizzo va solo in `RELEASE.md` e non si aggiunge il campo in `config.json`. Da riconfermare con l'autore, perché le due indicazioni divergono.

## 7. Verifica (criteri di "fatto")

- `python3 scripts/build.py --out _site && python3 scripts/check_site.py _site` verdi.
- `./run.sh`: index, privacy, support e 404 in 5 lingue, ciascuna in tema scuro e chiaro, a 1280 px e 375 px. Nessuno scroll orizzontale; la tab bar non copre il footer.
- Nessuna richiesta a domini esterni (scheda Rete).
- Le frasi della privacy coincidono con la §2 del prompt: nessun dato aggiunto, nessuno omesso. Nessun "suoni per dormire".
- Con JavaScript disattivato tutto il contenuto è visibile, FAQ comprese.
- "Riduci movimento": nessuna lucciola che si muove.
- Nessun telefono né indirizzo in `_site` (`grep`).
- Nessun punto esclamativo; francese con *vous*; nessuna parola di `storeTextWatch`; "suoni", "importa" e "acquisto" mai riferiti a funzioni presenti.
- URL invariati: `/privacy.html`, `/support.html` e le versioni per lingua.
- Consegna anche: le differenze rispetto a `docs/privacy-policy.md` dell'app (in particolare la frase sul backup iCloud, che lì manca) e le cose del sito in contrasto con il codice lasciate com'erano.
- Consegna finale: file toccati, elenco "Da compilare" (sito: titolare, email; App Store Connect: anche indirizzo, telefono, dominio), traduzioni da verificare e risposte FAQ da verificare.

## 8. Lasciato al costruttore

- Nomi esatti delle classi CSS e organizzazione di `site.css`.
- Disegno preciso delle icone SVG, purché in stile SF Symbols, monocromatiche e in `currentColor`.
- Posizioni delle lucciole d'ambiente.
- Ordine dei commit dopo il primo (consigliati: componenti CSS → home → privacy/supporto/contatti → 404 → pulizia i18n e documentazione).

Nota: le bozze in `mockups/` mostrano ancora telefono, indirizzo e il trucco `:has()` per il tema. Fa fede questo documento.
