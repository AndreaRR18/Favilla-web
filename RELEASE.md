# Favilla — valori per App Store Connect

Non è una pagina del sito: `build.py` pubblica solo `templates/` e `assets/`. Qui c'è tutto ciò che va incollato in App Store Connect per l'invio della 1.0, più cosa fare prima dell'invio e il giorno del lancio. `scripts/check_copy.py` verifica che ogni URL qui sotto abbia una pagina dietro.

I campi tra parentesi quadre `[...]` sono ancora da compilare.

## URL

L'inglese è alla radice, le altre lingue in una sottocartella.

| Lingua | Privacy Policy URL | Support URL |
|---|---|---|
| English | https://andrearr18.github.io/Favilla-web/privacy.html | https://andrearr18.github.io/Favilla-web/support.html |
| Italiano | https://andrearr18.github.io/Favilla-web/it/privacy.html | https://andrearr18.github.io/Favilla-web/it/support.html |
| Français | https://andrearr18.github.io/Favilla-web/fr/privacy.html | https://andrearr18.github.io/Favilla-web/fr/support.html |
| Deutsch | https://andrearr18.github.io/Favilla-web/de/privacy.html | https://andrearr18.github.io/Favilla-web/de/support.html |
| Español | https://andrearr18.github.io/Favilla-web/es/privacy.html | https://andrearr18.github.io/Favilla-web/es/support.html |

- **Marketing URL** (facoltativo): https://andrearr18.github.io/Favilla-web/
- **Copyright:** `© 2026 [TITOLARE]`
- **Nell'app:** `LegalLinks.privacyPolicy` (repo iOS, `Library/Sources/About/LegalLinks.swift`) va impostato sull'URL della privacy in inglese, o su quello della lingua dell'utente se l'app lo sceglie per lingua.

## Titolare e stato di "trader" UE

Apple li chiede per lo stato di trader (Digital Services Act) e li mostra nella pagina dell'app. Sul sito compaiono solo il nome del titolare e l'email.

**Questo repo è pubblico:** indirizzo e telefono si scrivono solo in App Store Connect, mai in questo file né in `config.json`.

- Titolare (nome o ragione sociale): da mettere in `config.json` → `publisher_name` e in App Store Connect.
- Email: strofa.tarsali.3p@icloud.com (già in `config.json`).
- Indirizzo e telefono: solo in App Store Connect.

## App Privacy (etichetta)

- **Data Not Collected.**
- **Tracking: No.**
- Motivo: le registrazioni e i testi restano sul dispositivo o nel database privato iCloud dell'utente, a cui lo sviluppatore non ha accesso. Nessun SDK di terzi, nessuna analisi, nessun identificativo, nessun account, nessun server.

## Kids

- Nessuna pubblicità, nessuna analisi, nessun SDK di terzi, nessun dato raccolto dai bambini.
- Link esterni (la privacy policy), condivisione e Impostazioni sono dietro un controllo parentale: la somma di due numeri a due cifre. La 1.0 non ha acquisti.
- I giochi della Foresta non hanno link, acquisti né pubblicità.
- Fascia d'età da scegliere in App Store Connect: consigliata **5 anni e meno**.

## Note per il reviewer (da incollare, in inglese)

```
Favilla needs no login and has no account.

How to record: open the Catalog tab, pick any tale, tap the microphone
button and read aloud; tap Finish to save it to Stories. You can also write your own text
from the + button in Catalog.

Microphone: used only while recording. The app declares the "audio"
background mode so a recording keeps going if the parent locks the screen
or leaves the app; iOS shows the microphone indicator and a Live Activity
with Pause and Finish.

Parental gate (sum of two two-digit numbers): About › Privacy › privacy
policy link; Share in the player; Record › microphone denied › Open
Settings.

Silent remote notifications and aps-environment are used only by CloudKit
to sync the user's private database between their own devices. The
developer receives no tokens and no data.
```

## Da verificare nella build dell'app

Il sito descrive come già presenti queste modifiche dell'app, che il 16 novembre 2026 erano ancora **non committate** sul branch `release-readiness` del repo iOS. Vanno committate e incluse nella build che si invia; se una manca, la risposta di supporto o la nota per il reviewer che la cita va cambiata prima di pubblicare.

| Comportamento | File nell'app | Dove lo cita il sito |
|---|---|---|
| Controllo parentale prima di "Apri Impostazioni" quando il microfono è negato | `App/Sources/App/Recording/RecordingScreen.swift`, `AppTabViewStore*.swift` | supporto `faq_mic_a`, `faq_sum_a`; note per il reviewer |
| Limiti di 100 caratteri (titolo) e 20.000 (testo) | `Library/Sources/StoryCatalog/CreateStoryStore.swift` | supporto `faq_long_a` |
| Pulizia dei file audio orfani dopo una cancellazione su un altro dispositivo | `Favilla/FavillaApp.swift` | privacy `retain_p`, supporto `faq_delete_a` |

## Prima di inviare

1. Compilare `config.json` → `publisher_name`. La build mostra un segnaposto rosso finché è vuoto, e rifiuta un `app_store_url` senza titolare ed email.
2. In App Store Connect: titolare, copyright, e indirizzo e telefono per lo stato di trader (solo lì, non in questo repo).
3. Far rileggere a un madrelingua i testi FR, DE ed ES di privacy e supporto.
4. Rileggere la privacy contro la build che si invia: se cambia un comportamento (acquisti, suoni per dormire, analisi), cambiano insieme la pagina, la data in testa e l'etichetta App Privacy.
5. Per un'app Kids conviene una rilettura finale di un legale: queste pagine non sono un parere legale.
6. `python3 scripts/build.py --out _site && python3 scripts/check_site.py _site && python3 scripts/check_copy.py _site`, poi push su `main`.

## Il giorno del lancio

1. Incollare l'URL dell'App Store in `config.json` → `app_store_url`: il badge diventa un link vero in tutte e 5 le lingue.
2. Sostituire o togliere, in 5 lingue, la domanda di supporto "Quando possiamo iniziare a usarla?" (`support_page.faq_coming_*`). Il gate conta 14 domande: aggiornare `FAQ` in `scripts/check_copy.py` se si toglie.
3. Aggiornare la data in testa alla privacy se è cambiato qualcosa.
4. Push su `main`: il workflow costruisce, controlla e pubblica.
