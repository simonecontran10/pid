# Player Intelligence Database (PID) — Diario tecnico

App di scouting/analisi giocatori. Fork di "Saudi Players Hub" (`~/Desktop/tm_project`) adattato per:
- **Focus iniziale**: Italia (Serie A + Serie B + Primavera 1)
- **Architettura predisposta** per altri paesi via `data/config.json`
- **Slug Vercel previsto**: `pid` → `pid.vercel.app`

Lavoriamo in `~/Desktop/pid/`. Niente `.git` ancora — verrà inizializzato a refactoring stabile.

## Decisioni architetturali confermate
- Fork separato (non multi-DB)
- Tutti i giocatori di Serie A con le loro nazionali (28+ nazionalità)
- Architettura parametrica via `data/config.json`
- Default lingua: italiano

## Stato setup
- Clonato `tm_project` → `pid`, rimosso `.git` saudita
- Pulizia: dati saudita, foto giocatori/club saudita, script saudita-specifici, temporanei
- Conservato: scraper core, frontend, API, scheduler, foto `competitions/` e `national/`
- Creato `data/config.json` con: app_name, country_focus=Italy, competizioni IT (IT1/IT2/CIT/SCI/PRIM), international (UCL/UEL/UECL), national_team_categories
- `progetto.md` saudita rinominato in `progetto_saudi_REFERENCE.md`

## Refactoring app.js — punti hardcoded mappati
~50 punti su 5 file. Suddivisi in:
- **Blocco A** (~20 punti, sostituzioni dirette): localStorage keys, nomi file JSON, title HTML, logo, stringhe i18n
- **Blocco B** (~15 punti, mapping competizioni): SA1→IT1, SA2L→IT2, SAKC→CIT, SASS→SCI, SAU21→PRIM
- **Blocco C** (~15 punti, business logic): saudis_desc/asc filtri, modulo U21→Primavera, is_saudi_eligible, mappe team_category nazionali

## Log incrementale step
- ✅ **A.1** — Rinomina chiavi localStorage e nomi file dati in `app.js`:
  - `"saudi_player_notes"` → `"pid_player_notes"`
  - `"saudi_callup_active"` → `"pid_callup_active"`
  - `"saudi_grids_v1"` → `"pid_grids_v1"`
  - `"saudi_callup_lists"` → `"pid_callup_lists"`
  - `loadJSON("players_saudi")` → `loadJSON("players_main")`
  - destructuring var `saudi` → `main`

## Pendenze
**Sera 1 (in corso)**:
- A.2 — header HTML title/icon/logo
- A.3 — i18n.js title e league labels
- A.4 — variabili stringa "Saudi Players Hub" sparse
- B — mapping codici competizione (SA1→IT1, ecc.) + colori CSS
- C — business logic (filtri "saudis_desc", U21 module, is_saudi_eligible, team_categories)

**Sera 2**: dati Italia
- `data/clubs.json` (60 club: 20 A + 20 B + 20 Primavera)
- Lista URL Transfermarkt squadre
- `add_players.py` × 3 round → ~1300 giocatori
- `run_stats.py --refresh` (notte, caffeinate)
- enrich + download foto

**Sera 3+**: branding (logo, palette), deploy Vercel pid.vercel.app

## Architettura riusabile (gratis dal saudita)
Tutto il frontend `app.js` (303KB) include già: scheda giocatore con Career by competition, Minutaggio, Convocazione, Compare, Griglie con drag&drop completo (lista→slot, slot→slot, drop preview), 5 formazioni, Note, Export PDF, multi-lingua, cloud sync, filtri avanzati, U21 cross-section.
- ✅ **A.2** — `index.html` aggiornato:
  - `<title>` → "Player Intelligence Database"
  - icon/apple-touch/shortcut icon → `data/photos/branding/logo.png` (placeholder, da creare in sera 3)
  - H1 grande splash + H1 piccolo header → "Player Intelligence Database"
  - alt img → "PID"
  - dropdown lega: `<option value="SA1">Saudi Pro League</option>` → `<option value="IT1">Serie A</option>`, idem SA2L → IT2 / Serie B
  - Creata cartella `data/photos/branding/`
- ✅ **A.3** — `i18n.js` aggiornato:
  - `title: "Saudi Players Hub"` → `"Player Intelligence Database"` in tutte le 4 lingue (IT/EN/AR/FR) — il nome prodotto non si traduce
  - `league_sa1: "Saudi Pro League"` → `"Serie A"` in tutte le lingue
  - `league_sa2: "Saudi First Division"` → `"Serie B"` in tutte le lingue
  - 0 residui "Saudi"/"SAFF" in `i18n.js` (verificato con grep)
  - Le chiavi `league_sa1`/`league_sa2` restano per ora; rinomina in `league_it1`/`league_it2` rimandata al blocco B
- ✅ **A.4** — `app.js` aggiornato:
  - Commento header riga 2: "Saudi Players Hub" → "Player Intelligence Database (PID)"
  - Path logo nazionale fallback: `photos/national/saudi_arabia.png` → `photos/branding/logo.png`
- ✅ **A.5** — Filtri "saudis_desc/asc" rinominati in modo agnostico:
  - `"saudis_desc"` → `"by_count_desc"`, `"saudis_asc"` → `"by_count_asc"` (la logica già contava giocatori per club, il nome era fuorviante)
  - Label IT: "Più sauditi" → "Più giocatori", "Meno sauditi" → "Meno giocatori"
  - Label EN: "Most saudis" → "Most players", "Fewest saudis" → "Fewest players"
- ⏸️ **A residue rimandate al blocco C** (~46 righe):
  - Modulo U21 saudita ("Saudi U21 Elite League") → diventerà modulo Primavera nel blocco C
  - Funzione `_saudiNationalTeamName()` → ridisegnare per usare la nazionalità reale del giocatore (Italia/Belgio/Brasile/...) invece di assumere una nazionale fissa
  - 2 commenti residui ("SA2P", "SAUP" → SA1") sono mappature legacy interne — non urgenti
- ✅ **B.1** — `app.js` mapping codici competizione (saudita → italiano):
  - Stringhe quoted: `"SA1"`→`"IT1"`, `"SA2L"`→`"IT2"`, `"SAKC"`→`"CIT"`, `"SASS"`→`"SCI"`
  - Chiavi oggetto: `SA1:`→`IT1:`, `SA2L:`→`IT2:`, `SAKC:`→`CIT:`, `SASS:`→`SCI:`
  - Path foto competizioni: `SA1.png`→`IT1.png`, ecc.
  - Variabili JS: `const sa1Logo`→`const it1Logo`, `const sa2l`→`const it2`, `saClubIds`→`mainClubIds`
  - CSS variables: `var(--comp-spl)`→`var(--comp-seriea)`, `var(--comp-super)`→`var(--comp-serieb)`
  - Commenti aggiornati ("SA1/SA2L"→"IT1/IT2")
  - 0 residui SA1/SA2L/SAKC/SASS in `app.js` (verificato con grep `\b...\b`)
  - **NB**: SAU21 e SAUP volutamente NON toccati (verranno gestiti nel blocco C col modulo Primavera)
- ✅ **B.2** — `index.html` CSS variables rinominate:
  - `--comp-spl: #6FE0A8` → `--comp-seriea: #6FE0A8` (verde, ex Saudi Pro League → Serie A)
  - `--comp-super: #FB923C` → `--comp-serieb: #FB923C` (arancione, ex Saudi Second → Serie B)
  - Colori conservati identici al saudita; palette palette ufficiale Serie A da rivedere in sera 3 (branding)
  - 0 residui `comp-spl`/`comp-super` in `index.html`
- ✅ **B.3** — Chiavi i18n competizioni rinominate + aggiunta Primavera:
  - `league_sa1` → `league_it1` in tutti e 4 i dizionari (en/ar/it/fr)
  - `league_sa2` → `league_it2` in tutti e 4 i dizionari
  - Valori arabi residui sostituiti con IT: `"دوري روشن السعودي"` → `"Serie A"`, `"دوري الدرجة الأولى"` → `"Serie B"`, `"أندية أخرى"` → `"Altri club"`
  - **Aggiunta nuova chiave `league_it3: "Primavera 1"`** in tutti i 4 dizionari
  - 7 riferimenti `t("league_sa1/sa2")` aggiornati in `app.js`
  - 0 residui `league_sa1`/`league_sa2` in `frontend/`
  - **Nota**: alcune traduzioni nei dizionari AR/FR sono ancora miste IT/EN — verranno ripulite nel blocco C insieme alla decisione su quali lingue mantenere (PID userà solo IT/EN)
- ✅ **B.4** — Default filter `league: "SA1"` → `league: "IT1"`: già coperto da B.1 (sostituzione `"SA1"` → `"IT1"` aveva preso anche questo punto). 0 residui.
- ✅ **B.5** — Chiavi `league_short_*` rinominate + Primavera aggiunta:
  - `league_short_spl: "SPL"` → `league_short_it1: "SA"` (4 lingue)
  - `league_short_sa2l: "SA2L"` → `league_short_it2: "SB"` (4 lingue)
  - **Aggiunta `league_short_it3: "P1"` (Primavera 1)** in tutti i 4 dizionari
  - 3 riferimenti aggiornati in `app.js` (riga 3036-3038, dropdown filtro lega Griglie)
- ✅ **Blocco B chiuso**: 0 residui codici stabili (`SA1/SA2L/SAKC/SASS`, `comp-spl/super`, `league_sa1/sa2`, `league_short_spl/sa2l`) in tutto `frontend/`.

## Blocco C — Business logic (in corso)

- ✅ **C.1** — Rimozione modulo U21 saudita da `app.js`:
  - `_u21MatchesNormalized(pid)` neutralizzata: ora ritorna `[]` (1658 chars → 185 chars). Codice di accesso al `state.u21MatchesByTmid` lasciato in piedi per compatibilità ma riceve sempre Map vuota.
  - `loadJSON("u21_matches_by_tmid")` rimosso dal `Promise.all` di bootstrap
  - Variabile `u21` rimossa dalla destrutturazione (era undefined → ReferenceError)
  - Blocco di popolamento `state.u21MatchesByTmid = new Map(); if (u21) {...}` semplificato a sola Map vuota
  - Mappa loghi competizioni (`const known = {...}`): rimosso `SAU21: "png"`
  - Rimosso blocco append riga SAU21 in renderClubBlocks (~10 righe)
  - Rimosso blocco merge SAU21 all-time in career-by-competition (~9 righe)
  - Rimosso blocco append U21 in altra sezione career
  - Rimosso `COMP_LABEL.SAU21`, voce in `KNOWN_CLUB_CODES`, voce in `CLUB_PRIORITY_ORDER`
  - Rimossi 2 mapping legacy `SAUP → IT1` (Saudi Pro League Playoff)
  - Aggiornato commento ordine colonne club: ora "Serie A → Serie B → UCL → UEL → UECL → Coppa Italia → Supercoppa → Estero"
  - **0 residui SAU21/SAUP** in `app.js`
  - Decisione: niente Excel U21/Primavera per PID. Quando in futuro servirà un modulo Primavera 1, ricostruire `_u21MatchesNormalized` come funzione attiva e aggiungere `loadJSON("primavera_matches")` al bootstrap.
- ✅ **C.2** — Rimosso `build_u21_player_matches.py` (~20KB). Dati U21 (`u21_matches_by_tmid.json`, `u21_player_matches.json`, `u21_player_matches.csv`, `sofascore_u21_calendar.json`) erano già stati rimossi nella pulizia iniziale di sera 1.
  - Script Python core rimasti (tutti riusabili): `_bootstrap.py`, `add_players.py`, `download_photos.py`, `enrich_sortitoutsi.py`, `run_static.py`, `run_stats.py`, `run_update.py`
- ✅ **C.3** — Pulizia `i18n.js` (820 → 440 righe, -46%):
  - Rimossa intera sezione AR (riga 199-388, ~190 righe) — non più supportata in PID
  - Rimossa intera sezione FR (riga 581-769, ~190 righe) — non più supportata in PID
  - `SUPPORTED_LANGS = ["en","ar","it","fr"]` → `["it","en"]`
  - localStorage chiave `"saudi_lang"` → `"pid_lang"`
  - Default lang: `localStorage.getItem("pid_lang") || "it"` (era `"en"`)
  - Fallback su chiave mancante: `I18N[currentLang] ?? I18N.it ?? I18N.en ?? key`
  - Subtitle obsoleto "Pro League · First Division · Nazionale" → `"Serie A · Serie B · Primavera"` in IT e EN
  - Verifica RTL handling (`RTL_LANGS.has(currentLang)`): ora PID non ha lingue RTL, ma il codice è innocuo se la chiave `RTL_LANGS` resta come `Set(["ar"])` → semplicemente non match mai
- ✅ **C.4** — Refactoring `_saudiNationalTeamName` → `_nationalTeamName` (parametrico):
  - La nuova funzione usa la **nazionalità reale del giocatore** invece di assumere "Saudi Arabia" hardcoded
  - Lookup ordine: `stats.nationality` → fallback `state.players.find(...).nationality` o `.citizenship` → fallback `"National"`
  - Costruisce "{Country}" per cat "A" (senior), "{Country} Olympic", "{Country} {cat}" per altre
  - Esempio: per Verratti restituisce "Italia" / "Italia U21"; per Lukaku "Belgio"
  - Aggiunto alias `_saudiNationalTeamName` → `_nationalTeamName` per compatibilità (rimovibile in futuro)
  - Variabili locali rinominate: `saudiTeam`/`saudiCat`/`saudiColor` → `natTeam`/`natCat`/`natColor`
  - Commento "Media caps nazionale A (Saudi Arabia maggiore)" → "Media caps nazionale A (senior)"
  - 0 residui `Saudi Arabia` / `saudiTeam` / `saudiCat` / `saudiColor` in `app.js`
- ✅ **C.5.a** — `scraper/config.py` riscritto in versione PID config-driven (backup salvato in `scraper/config.py.saudi_backup`):
  - Carica `data/config.json` come fonte di parametri country-specific
  - `SAUDI_NATIONALITY = "Saudi Arabia"` → `TARGET_NATIONALITY = config["country_label_en"]` (default "Italy")
  - `PLAYERS_SAUDI_FILE` → `PLAYERS_MAIN_FILE` (path `data/players_main.json`)
  - `LEAGUES = {SA1, SA2L}` → dict vuoto (verrà popolato in sera 2 con URL squadre Italia o tramite `add_players.py`)
  - `COMPETITION_NAMES`: rimosse SA1/SAKC/SASS/SAUP/AFC/Arab; aggiunte IT1/IT2/CIT/SCI/PRIM/CL/EL/UECL/EM21/U21Q/U19E/U17E
  - `NATIONAL_CLUB_IDS`: dict vuoto. PID-Italia con giocatori multi-nazionalità: Transfermarkt espone `team_category` direttamente nei profili, non serve mapping per id. Se in futuro emergono casi senza team_category, popolare qui.
  - `NATIONAL_TEAM_CATEGORY_FROM_COMP`: aggiunte EM21/U21Q/U19E/U17E (mancavano per il calcio europeo)
  - `_heuristic_category_from_comp`: aggiunto match per U21 e U19
  - `national_team_label(category, country=None)`: ora parametrico — il chiamante passa il paese del giocatore (Italia/Belgio/Brasile/...). Default fallback su `TARGET_NATIONALITY`.
  - Alias `SAUDI_NATIONALITY` e `PLAYERS_SAUDI_FILE` mantenuti come deprecati per compatibilità retroattiva durante la migrazione import (verranno rimossi dopo C.5.b/c)
  - Verifica: `from scraper import config` importa correttamente, `config.comp_name("IT1") == "Serie A"`, `config.national_team_label("A", "Belgium") == "Belgium"`
- ✅ **C.5.b** — `scraper/filter_saudi.py` → `scraper/filter_target.py`:
  - Nuovo modulo `filter_target.py` con `is_target_eligible(profile)` e `filter_target_profiles(profiles)`
  - Per PID-Italia (e in generale per uno scouting hub di una lega): **default ritorna sempre True** — vogliamo TUTTI i giocatori della lega, indipendentemente dalla cittadinanza
  - Override esplicito: `_force_target=True` (sempre incluso) o `_force_target=False` (sempre escluso)
  - `filter_saudi.py` mantenuto come alias di retrocompatibilità: riesporta `is_target_eligible as is_saudi_eligible` e `filter_target_profiles as filter_saudi_profiles`
  - Test: `is_target_eligible({})` → True, `is_target_eligible({"_force_target": False})` → False, alias `from scraper.filter_saudi import is_saudi_eligible` continua a funzionare
- ✅ **C.5.c** — Migrazione import nei moduli utilizzatori (approccio conservativo):
  - `run_static.py`, `run_update.py`: `from scraper.filter_saudi import filter_saudi_profiles` → `from scraper.filter_target import filter_target_profiles as filter_saudi_profiles`
  - `add_players.py`: `from scraper.filter_saudi import is_saudi_eligible` → `from scraper.filter_target import is_target_eligible as is_saudi_eligible`
  - `scraper/profiles.py` riga 256: `"is_saudi_eligible": "Saudi Arabia" in citizenships` → `"is_target_eligible": True, "is_saudi_eligible": True` (per PID-Italia ogni profilo è eligible perché siamo uno scouting hub di una lega; alias mantenuto)
  - **Variabili interne NON rinominate** (es. `saudi_by_id`, `n_saudi`, `step_filter_saudi`): refactoring rimandato a sera 2 quando avremo dati italiani per testare. Codice gira identico ma "modernizzato" lato import.
  - Verifica import: `scraper.config`, `scraper.filter_target`, `scraper.filter_saudi` (alias) caricano senza errori. `is_target_eligible({})` → True.
  - Nota: test completi import scraper bloccato da `ModuleNotFoundError: bs4` — non è un errore di refactoring, è solo dipendenza Python non installata in venv. Si risolve in sera 2 con `pip install -r requirements.txt` (BeautifulSoup, requests, lxml, pandas, openpyxl, curl_cffi).

## ✅ BLOCCO C CHIUSO

Ricapitolando i 3 blocchi:
| Blocco | Stato |
|---|---|
| A — sostituzioni meccaniche dirette | ✅ chiuso |
| B — mapping competizioni | ✅ chiuso |
| C — business logic ridisegnata | ✅ chiuso |

Sostituzioni totali: ~50 punti su 5 file (`app.js`, `index.html`, `i18n.js`, `scraper/config.py`, `scraper/filter_saudi.py`).

## Stato dell'app PID dopo refactoring

- ✅ Niente "Saudi" hardcoded in nessun file frontend funzionale
- ✅ Codici competizione italiani (IT1/IT2/CIT/SCI/PRIM)
- ✅ `data/config.json` come fonte di verità per parametri country-specific
- ✅ Modulo U21 saudita rimosso (Excel + script + render). Da ricostruire come "Primavera 1" se servirà
- ✅ Default lingua IT, AR/FR rimosse, fallback IT→EN
- ✅ Funzione nazionali parametrica sulla nazionalità del giocatore
- ✅ Scraper config-driven via `data/config.json`

## Pendenze sera 2

**Popolamento dati Italia**:
1. `data/clubs.json` — 60 club (20 Serie A + 20 Serie B + 20 Primavera) con `tm_club_id`
2. Lista URL Transfermarkt squadre Italia
3. Setup venv Python (`python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt`)
4. `add_players.py` × 3 round (Serie A → ~600, Serie B → ~500, Primavera → ~200)
5. `run_stats.py --refresh` (notte, `caffeinate`, ~30-40 min)
6. `enrich_sortitoutsi.py` per le foto curate
7. `download_photos.py` per le foto Transfermarkt

**UI/Branding**:
- Logo: FIGC o tricolore (oggi è placeholder `data/photos/branding/logo.png` non ancora creato)
- Palette: rivedere `--comp-seriea` / `--comp-serieb` con colori Lega Serie A ufficiali

**Deploy**:
- `git init` + repo GitHub `pid` + collegamento Vercel + dominio `pid.vercel.app`

**Cleanup futuro** (non urgente):
- Rimuovere alias deprecati in `scraper/config.py` (`SAUDI_NATIONALITY`, `PLAYERS_SAUDI_FILE`)
- Rimuovere `scraper/filter_saudi.py` (è solo alias)
- Rinominare variabili interne `saudi_by_id`, `n_saudi`, `step_filter_saudi` ecc. in `target_*` / `n_target`
- Rimuovere `scraper/config.py.saudi_backup`
- Rimuovere alias `_saudiNationalTeamName` in `app.js`

## Sera 2 — Popolamento dati Italia (in corso)

### Setup
- ✅ Creato venv Python 3.13 in `pid/venv/`
- ✅ Installato: requests, beautifulsoup4, lxml, pandas, openpyxl
- ✅ Tutti i moduli `scraper.*` importano correttamente nel venv
- ✅ `add_players.py` importa correttamente (con alias `is_target_eligible as is_saudi_eligible`)
- Transfermarkt risponde senza bisogno di `curl_cffi` (per ora)

### Lista club scrappata (3 leghe italiane 2025/26)
- ✅ Creato `scrape_serie_a_clubs.py` e `scrape_league_clubs.py` (generico, accetta slug + code)
- ✅ **Serie A (IT1)** → `data/serie_a_clubs.json` — 20 club: Inter, Juve, Milan, Roma, Napoli, Atalanta, Como, Bologna, Fiorentina, Lazio, Sassuolo, Parma, Udinese, Genoa, Cagliari, Torino, Pisa, Hellas Verona, Lecce, Cremonese
- ✅ **Serie B (IT2)** → `data/it2_clubs.json` — 20 club: Venezia, Monza, Sampdoria, Frosinone, Palermo, Catanzaro, Spezia, Empoli, Modena, Cesena, Bari, Mantova, Carrarese, Juve Stabia, Avellino, Pescara, Südtirol, Reggiana, Padova, Entella
- ✅ **Primavera 1 (IJ1)** → `data/ij1_clubs.json` — 20 club U20/Primavera. Codice TM **IJ1** (NON `PRIM` come nel config iniziale, corretto)
- ✅ `data/config.json` → `competitions.youth.code` aggiornato da `PRIM` → `IJ1`

### Pendenze immediate
- Scrappare rosters di ciascun club (`scraper/rosters.py:parse_club_roster`) per ottenere ~1300 URL profilo giocatori
- Salvare URL in `urls.txt`
- Lanciare `add_players.py urls.txt` → popola `players_main.json` + scarica stats + foto

### Scraping rosters → urls.txt
- ✅ Creato `build_urls.py`: scrappa rosters di tutti i 60 club dai 3 file JSON (serie_a, it2, ij1) usando `parse_club_roster` di `scraper/rosters.py`
- ✅ **1713 URL profilo unici** estratti (1728 giocatori scrappati, ~15 duplicati = stesso giocatore in più rose, es. nazionali in Primavera) → `urls.txt`
- ✅ Test campione con 5 giocatori → `urls_test.txt` (Abdou Diene, Aaron Martin, ecc.). `add_players.py` funziona: 4 file JSON popolati, foto scaricate (`players_tm/`, `players_sots_lookup/`)
- 🔄 **Lancio massivo** in background: `nohup caffeinate -i python3 -u add_players.py urls_remaining.txt > scraping.log 2>&1 &`
  - 1708 URL rimanenti
  - PID 32217 attivo, `PYTHONUNBUFFERED=1` per log in tempo reale
  - Stima fine: ~85 minuti puri di scraping + 20-40 min enrich/photos al termine
  - Comandi monitoraggio:
    - `tail -f scraping.log` — segui in tempo reale
    - `ps -p 32217` — verifica processo vivo
    - `kill 32217` — stop
    - `python3 -c "import json; print(len(json.load(open('data/players_main.json'))))"` — conta giocatori importati

### Sera 3+ (pendenze)
- Verificare che il giro completo `add_players.py` finisca senza errori (1708 → 1713 totali in `players_main.json`)
- `enrich_sortitoutsi.py` finale (chiamato già automaticamente alla fine di `add_players.py`)
- `download_photos.py` finale (idem)
- Eventuali giocatori falliti (403 / timeout) → ritentare con liste mirate
- `data/clubs.json` — unire in unico file i 60 club dei 3 JSON per il frontend (oggi `clubs.json` è solo `[]`)
- Branding: logo PID `data/photos/branding/logo.png` (oggi placeholder)
- Test app `cd frontend && python3 -m http.server 8000` → verificare che `players_main.json` carica
- Deploy Vercel `pid.vercel.app`

## ✅ MILESTONE — PID Italia online in locale (6 mag 2026, 10:30)

L'app è completamente funzionante in locale con dati italiani:

### Dati
- **1707 giocatori** scrappati da Transfermarkt (Serie A + Serie B + Primavera 1)
- **60 club** organizzati in 3 leghe (IT1: 20, IT2: 20, IJ1: 20)
- **1704 stats entries** (presenze, minuti, gol, assist per stagione 24/25 e 25/26)
- **1312 foto giocatori** da Transfermarkt
- **6 FAIL** nel scraping massivo (502 Bad Gateway TM, ~0.35%) — recuperabili con re-run mirato
- **9 loghi competizione** italiani/UEFA scaricati (IT1, IT2, IJ1, CIT, SCI, CL, EL)

### Frontend
- Logo PID custom in header (1254×1254 PNG, 996KB)
- Subtitle "Serie A · Serie B · Primavera"
- 3 dropdown filtri lega operativi
- Auth gate disabilitato (lavoriamo in locale, riattiveremo per deploy con nuovo Supabase)
- `cloud_sync.js` commentato
- Tutte le sezioni navigabili: Home, Lista, Club, Confronto, Convocazione, Griglie, Minutaggi

### Errori critici risolti
- `SyntaxError: Unexpected token '}'` a riga 4197 (residuo blocco U21 rimosso in C.1, 2 graffe orfane)
- `ReferenceError: sa1 is not defined` (variabili JS non rinominate in B.1)
- 5 file mancanti: creati `players_unified.json` ([]) , `opponent_club_names.json` ({}), `last_update.json` (timestamp+counts), scaricati IT1/IT2/IJ1/CIT/SCI/CL/EL.png

### Pendenze residue
- 6 giocatori falliti (502 TM) → re-run mirato in sera 3
- Warning Tailwind CDN (innocuo, eventuale ottimizzazione produzione)
- API backend `/update/status` non gira (uvicorn non avviato; `python3 api/main.py` quando serve il bottone "Aggiorna ora")
- Sera 3: deploy Vercel + nuovo progetto Supabase per cloud sync utente
- Cleanup variabili interne `saudi_*` → `target_*` (rimandato, non urgente)
- Ottimizzare logo PID (1254×1254 → 256×256, da 996KB a ~50KB)

## 6 mag 2026 (mattina/pomeriggio) — Foto SortItOutSi

### Setup foto SortItOutSi (FM-style)
- ✅ Copiati `scrape_sortitoutsi_competition.py` e `scrape_sortitoutsi_ids.py` dal saudita
- ✅ `scrape_sortitoutsi_competition.py`: aggiornate `COMPETITIONS` con URL Italia (Serie A `competition/32`, Serie B/BKT `competition/33`). Primavera 1 NON ha pagina FM26 dedicata — i giocatori Primavera che giocano in prima squadra Serie A/B vengono comunque trovati nelle rose dei rispettivi club.
- ✅ Aggiunto dizionario `SOTS_TO_TM_ALIAS` per match nomi club (SortItOutSi usa "F.C. Internazionale Milano", TM usa "Inter Milan", ecc.). Funzione `_norm()` ora rimuove tokens generici (AC, FC, SS, US, ecc.).
- ✅ Run `scrape_sortitoutsi_competition.py` → 40/40 club Serie A + Serie B mappati con `sortitoutsi_team_id`
- ✅ Run `scrape_sortitoutsi_ids.py --no-search` (no fallback by name search, troppo lento) in 7'16":
  - 40 club Serie A + Serie B processati
  - **675 giocatori match** + **677 foto scaricate** (FM-style) in `data/photos/players_sots_lookup/`
  - **169 unmatched** (giocatori in rose TM ma non SortItOutSi: prestiti recenti, transfer non riflessi, U17/U18 nei club Serie A)
  - `sortitoutsi_id_lookup.json` (149KB) salvato
  - `players_main.json` aggiornato: **675/1707 giocatori hanno `sortitoutsi_face_url`** (40%)
- ✅ Frontend: foto FM-style visibili nei giocatori Serie A/B famosi
- ⚠️ **Primavera 1**: i ~600 giocatori Primavera "puri" (non in prima squadra Serie A/B) restano con foto Transfermarkt — accettabile, le foto TM dei giovani sono comunque utili

### Override manuali SortItOutSi
- ✅ Creato `data/sots_overrides.xlsx` (template Excel: 2 colonne `name | sortitoutsi_url`)
- ✅ Creato `apply_sots_overrides.py`:
  - Legge l'Excel
  - Match per nome esatto (`full_name` da `players_main.json`)
  - Estrae sots_id dall'URL via regex `/person/(\d+)/`
  - Scarica face in `data/photos/players_sots_lookup/{sots_id}.png`
  - Aggiorna `sortitoutsi_id_lookup.json` + `players_main.json` + `players_all.json` + `players_static.json`
  - Imposta TUTTI i campi richiesti dal frontend: `sortitoutsi_person_id`, `sortitoutsi_face_url`, `sortitoutsi_profile_url`, `sortitoutsi_face_local_lookup`
  - Idempotente: re-run salta i mapping già applicati (segnati con `=`)
  - Flag `--dry-run` per simulazione
- ✅ Test: 2/2 mapping applicati (Aarón Martín, Alberto Cerri), foto SortItOutSi visibili nel frontend

### Workflow per nuovi mapping manuali
1. Apri `data/sots_overrides.xlsx`
2. Aggiungi righe con `name` (esatto come da DB) + `sortitoutsi_url`
3. `python3 apply_sots_overrides.py`
4. Hard reload browser

### Match offline aggressivo + verifica DOB
- ✅ Creato `harvest_sots_rosters.py`: scarica le 40 rose SortItOutSi (Serie A + Serie B) e salva in `data/sots_rosters.json` (5669 persons cached)
- ✅ Creato `match_unmatched_offline.py`: cerca match offline per i giocatori unmatched usando regole multiple (slug esatto, all-tokens, cognome, primo nome). Score 0.5-1.0.
  - Risultato: 18 unmatched in club Serie A/B, 17 auto-match (score>=0.7), 1 review
- ✅ Creato `verify_auto_matches_dob.py`: per ogni match candidato, fetch pagina person SortItOutSi, estrae DOB, confronta con TM
  - Risultato: **17/17 DOB confermate** (0 mismatch, 0 errori) — match offline al 100% accurato
- ✅ Creato `apply_confirmed_matches.py`: legge i match confermati, scarica foto, aggiorna 3 JSON players
  - 17 nuovi mapping applicati, lookup totale: **694 entries**
  - Stato finale foto SortItOutSi: 694/1707 (40.6%)
- 🟢 Casi notevoli risolti: greci (Dimitrios→Dimitris), africani (André-Franck Anguissa), nicknames (Benji Siegrist), nomi alternativi (Junior Onana)

### File generati per workflow ibrido
- `data/sots_rosters.json` — cache rose SortItOutSi
- `data/sots_auto_matched_preview.xlsx` — anteprima match auto (deprecato dopo verifica DOB)
- `data/sots_auto_matched_confirmed.xlsx` — match con DOB verificata
- `data/sots_dob_mismatch.xlsx` — eventuali mismatch (al run attuale: vuoto)
- `data/sots_unmatched_review.xlsx` — review manuale (1 caso: Faris Moumbagna in Cremonese)

## 6 mag 2026 (pomeriggio) — Branding Primavera + bug rilevato

### Branding Primavera 1
- ✅ Tutti i 20 club Primavera ora hanno il logo (riusato `sortitoutsi_team_id` + `sortitoutsi_logo_url` del club di prima squadra)
- ✅ 3 club rinominati: "Genoa U20" → "Genoa Primavera", "Lazio U20" → "Lazio Primavera", "Roma U20" → "Roma Primavera"
- ✅ Aggiornati 64 riferimenti a `current_club_name` / `roster_club_name` / stats nei 3 JSON players (Genoa/Lazio/Roma U20 → Primavera)
- ✅ `app.js` riga 537: aggiunto `ij1Logo = _photoUrl("photos/competitions/IJ1.png")` e passato a `sectionHtml(t("league_other"), ij1Logo, …)` (prima era `null`)
- ✅ `i18n.js`: rinominata stringa `league_other` da "Altre squadre" / "Other clubs" a **"Primavera 1"** (IT + EN)

### Foto SortItOutSi — Stato finale
- **1606/1707 = 94.1% copertura** (era 0% all'inizio della sessione, poi 675, poi 692, poi 1606)
- 101 giocatori restano con foto Transfermarkt (giovanissimi Primavera puri, nuovi acquisti recenti, nomi atipici)
- Sistema completo verificato:
  - DOB-verify obbligatorio (zero falsi positivi accettati)
  - Cross-club lookup (per giocatori "New arrival" / prestiti)
  - Override manuale via `data/sots_overrides.xlsx` per casi residui

## ⚠️ BUG RILEVATO (al rientro dalla pausa)
**AC Milan ha solo 13 giocatori**, dovrebbero essere ~25-30. Vedere `data/players_main.json` filtrando per `current_club_id == 5`.

Altri potenziali sotto-conteggi (da verificare):
- Atalanta BC: 16
- Hellas Verona: 17
- Cesena FC: 14, Virtus Entella: 14, Palermo FC: 16

### Diagnosi step by step (al rientro)
1. **Verifica giocatori Milan attualmente nel DB** (lista per nome + posizione)
2. **Rifare scraping rosa Milan** con `parse_club_roster("https://www.transfermarkt.com/ac-mailand/startseite/verein/5")` per vedere quanti URL estrae lo scraper
3. **Confrontare**: lo scraper estraeva 13 URL già allora? Oppure era un timeout / errore HTTP nel run massivo?
4. **Ipotesi probabili**:
   - Bug parser TM rosters per certe squadre (struttura HTML pagina rosa diversa)
   - Errore HTTP transitorio durante il run massivo notturno (Milan appare al posto giusto ma con rosa parziale)
   - Filtro fascia età / posizione che escludeva primavera Milan (poi presi nel club Primavera separato come `current_club_id != 5`)

### Comandi diagnostici da lanciare al rientro
```bash
cd ~/Desktop/pid && source venv/bin/activate

# 1. Lista Milan attuale
python3 -c "
import json
players = json.load(open('data/players_main.json'))
milan = [p for p in players if p.get('current_club_id') == 5]
print(f'Milan: {len(milan)} giocatori')
for p in milan:
    print(f\"  tm={p['tm_player_id']:<7}  {p.get('full_name', ''):<35}  pos={p.get('main_position', ''):<25}\")
"

# 2. Re-scrape rosa Milan
python3 -c "
import sys; sys.path.insert(0, '.')
from scraper.rosters import parse_club_roster
urls = parse_club_roster('https://www.transfermarkt.com/ac-mailand/startseite/verein/5')
print(f'URL rosa Milan: {len(urls)}')
for u in urls: print(' ', u)
"
```


## 6 mag 2026 (sera) — Bug "club misclassified" risolto

### Diagnosi
- Sintomo: AC Milan mostrava 13 giocatori, dovrebbe esserne ~23. Stesso problema su molti club.
- Cause confluite:
  1. Lo scraping notturno del 6 mag mattina aveva preso TUTTI i 1707 giocatori
  2. Ma i loro **profili individuali** TM mostravano `current_club="New arrival"` / `Returnee` / `Internal transfer: X` perché il trasferimento estivo era stato registrato in modo asincrono (la rosa era già aggiornata, ma i profili no)
  3. `add_players.py` aveva salvato sia `current_club` sia `roster_club` con il valore placeholder, perdendo l'informazione dell'origine
  4. Risultato: 793 giocatori (46% del DB) classificati con `current_club_id` di un club di provenienza random (`id=244` per Marsiglia, `id=418` per Real Madrid, ecc.)
  
### Fix applicato
- Creato `find_missing_players.py` (diagnostico): conferma 0 missing, ~284 misclassified Serie A/B + 347 misclassified Primavera = ~631 da ricollocare
- Creato `fix_misclassified_clubs.py`:
  1. Per ogni club Serie A/B/Primavera (60 totali), fetch live rosa TM
  2. Ricostruisce mapping `tm_player_id` → `(roster_club_id, roster_club_name)` (1713 mapping; per giocatori in più rose, priorità al senior over Primavera)
  3. Sovrascrive `roster_club_*` nei 3 JSON players
  4. Riusa la funzione `fix_club_placeholder()` di `enrich_sortitoutsi.py` (fase 3 fallback su roster_club)
- Risultati:
  - 794 roster_club ricostruiti
  - **793 placeholder risolti** in tutti i 3 JSON (`players_main`, `players_static`, `players_all`)
- Verifica post-fix: AC Milan 23 (era 13), Atalanta 27, Hellas Verona 30, Cesena Primavera 24, Inter Primavera 28, ecc. Tutti i 60 club ora con conteggi sani.

### Note tecniche
- I 6 nuovi giocatori scoperti (rose attuali contenevano tm_id non ancora nel DB) sono stati aggiunti agli URL ma non scrappati (richiederebbe `add_players.py` mirato). Si possono aggiungere in futuro con `python3 add_players.py missing_urls.txt`.
- Genoa CFC: TM mostra 26 ma DB ne ha 26 dopo fix (erano 31 prima, c'erano 5 ex-Genoa che ora sono altrove — ora correttamente riassegnati al loro nuovo club)

## 6 mag 2026 (sera tardi) — Override manuali + cleanup placeholder

### 14 nuovi mapping manuali via Excel
Aggiunti tramite `data/sots_overrides.xlsx`:
- David Odogu, Ange-Yoan Bonny, Alex Amorim, Faris Moumbagna, Henrik Meister, Leo Østigård, Torbjørn Heggem, Andrija Novakovich, Daniel Theiner, Davide Pio Stabile, Emanuele Adamo, Magnus Brøndbo, Papu Gómez, Alessandro Marcandalli
- Tutti applicati con `apply_sots_overrides.py` (15 face scaricate, 3 JSON aggiornati)

### Bug "quadrato bianco" risolto
**Sintomo**: 130 giocatori mostravano un quadrato bianco invece della foto SortItOutSi (visto nello screenshot Atalanta su Alessandro Rinaldi, Giovanni Percassi, Mattia Pedretti).

**Diagnosi**: SortItOutSi restituisce un **GIF 1×1 trasparente da 43 bytes** (estensione .png) quando il giocatore non ha la face caricata. Il browser lo considera un'immagine valida e non chiama `onerror`, quindi non scatta il fallback `ui-avatars.com`.

**Fix applicato**:
- Creato `/tmp/clean_placeholders.py`: scansiona `data/photos/players_sots_lookup/`, identifica file ≤200 bytes (i placeholder), li cancella, rimuove `sortitoutsi_face_local_lookup` dai 3 JSON, nullifica `face_local` nel lookup
- Risultato: **130 placeholder cancellati**, ora i giocatori senza foto SortItOutSi mostrano le iniziali (fallback `ui-avatars.com` esistente)
- Stato file foto reali: **1490** (era 1620 con 130 placeholder)

**Fix preventivo**:
- Patch a `apply_sots_overrides.py`, `apply_confirmed_matches.py`, `apply_more_matches.py`: `download_face()` ora salva solo se `len(content) > 200 bytes`
- `scrape_sortitoutsi_ids.py` aveva già il check (codice originale corretto)
- Nei prossimi run, niente più GIF spazzatura

### Stato finale foto SortItOutSi (corretto)
- **1490/1707 = 87.3% copertura reale** con foto FM-style
- 217 giocatori con fallback `ui-avatars.com` (iniziali nome+cognome su sfondo verde)

## 6 mag 2026 (sera) — Espansione Polonia COMPLETATA + Setup deploy

### Polonia (Ekstraklasa + 1 Liga)
- ✅ Scraping 1058 nuovi giocatori polacchi finito (PID 40181, ~2h)
- ✅ DB totale: **2763 giocatori** (1707 Italia + 1056 Polonia)
- ✅ Foto: 1033 nuove TM scaricate, 3617 in cache
- ✅ 96 club totali (IT1:20, IT2:20, IJ1:20, PL1:18, PL2:18)
- ✅ Sottotitolo "Serie A · Serie B · Primavera" rimosso da i18n.js + index.html
- ⏳ **Pending frontend Polonia**:
  - i18n.js: chiavi `league_pl1: "Ekstraklasa"`, `league_pl2: "1 Liga"` (IT + EN)
  - app.js renderClubs(): sezioni Ekstraklasa + 1 Liga
  - app.js filtri: option PL1, PL2 nei 3 dropdown
  - Loghi competizione PL1.png e PL2.png da TM
  - Match SortItOutSi club polacchi (rose Ekstraklasa)
  - find_more_sots_matches.py per foto FM polacchi

### Deploy: Cloudflare R2 + GitHub
- ✅ Repo GitHub creato: `https://github.com/simonecontran10/pid`
- ✅ Public, no README/license/gitignore (gestiti localmente)
- ✅ Description: "Players Intelligence Database"
- ✅ Git init + 2 commit:
  - `d4c6c70` Initial commit (3007 file)
  - `542e265` cleanup: rimuovi diario fork e backup HTML
  - `ac29164` fix: escludi players_stats.json (>100MB GitHub limit)
- ❌ Push GitHub fallito: **players_stats.json (122MB) > limite 100MB**
- ✅ Soluzione adottata: **Cloudflare R2** (gratis 10GB/mese, no egress fees)
  - Account Cloudflare creato: simonecontran10@gmail.com
  - Bucket `pid-data` creato (Eastern Europe / EEUR)
  - Account ID: `b8d30d0c945985ca7928fd7cf5548f0d`
  - Public Development URL: `https://pub-aa9d173290684b36a9f35e79d4d388c2.r2.dev`
  - CORS Policy applicata (AllowedOrigins: *, Methods: GET/HEAD)
  - API Token creato (Object Read & Write su pid-data)
  - Credenziali in `.env` LOCALE (gitignored)
- ✅ `players_stats.json` (122MB → 127.880.998 bytes) caricato su R2
- ✅ URL pubblico verificato: HTTP 200, content-type application/json
- ✅ Script `upload_to_r2.py` creato per future re-upload (pip install boto3 python-dotenv)

### TODO immediato per andare in produzione
1. ✅ Modificare `frontend/app.js` con override R2 per `players_stats` → fatto, `R2_OVERRIDES` dict aggiunto
2. ⏳ Test in locale: hard reload, verifica che stats si caricano da R2
3. ⏳ Aggiungere `data/players_stats.json` definitivamente al `.gitignore`
4. ⏳ Riscrivere cronologia git per rimuovere il file dal commit `d4c6c70` (con `git filter-repo` o reset+ricommit)
5. ⏳ Push GitHub: `git push -u origin main` (ora dovrebbe passare, ~150MB)
6. ⏳ Vercel: collega repo `simonecontran10/pid`, deploy

### Quasi-emergenza disco
- Disco esaurito a 122MB liberi su 926GB totali (905GB usati = 100% capacità)
- Liberato spazio (utente ha rimosso file pesanti)
- Lezione: monitorare lo storage, R2 è la mossa giusta proprio per non saturare

### File chiave creati oggi
- `.env` (credenziali R2, gitignored)
- `upload_to_r2.py` (script upload reusable)
- `data/pl1_clubs.json`, `data/pl2_clubs.json` (36 club polacchi)
- `urls_pl.txt` (1058 URL polacchi - già committato accidentalmente, da decidere se mantenerlo)
- `scraping_pl.log` (gitignored, log scraping)

## 6 mag 2026 (notte) — DEPLOY VERCEL ONLINE 🎉

### Pubblicazione completata
- ✅ **Sito online**: `https://pid-7goy028x5-simone-contran-s-projects.vercel.app`
- ✅ Repo GitHub pubblico: `https://github.com/simonecontran10/pid`
- ✅ Bucket R2 `pid-data` con players_stats.json (122MB) accessibile via `https://pub-aa9d173290684b36a9f35e79d4d388c2.r2.dev/players_stats.json`
- ✅ DB pubblicato: 2763 giocatori, 96 club, 5 leghe (IT1/IT2/IJ1/PL1/PL2)

### Steps completati
1. R2 setup: bucket creato, Public Development URL abilitato, CORS Policy applicata (`AllowedOrigins: *`, `AllowedMethods: GET/HEAD`)
2. API Token R2: `Object Read & Write` su pid-data, salvato in `.env` LOCALE (gitignored)
3. Script `upload_to_r2.py` creato (boto3 + python-dotenv) — upload completato in ~2 min
4. Frontend modificato: aggiunto `R2_OVERRIDES` dict in `loadJSON()` per redirect di `players_stats` verso URL R2
5. Git history pulita con orphan branch (`git checkout --orphan main-clean`):
   - 1 solo commit `fb8e6e7` (era 4 con file pesante in cronologia)
   - .git/ ridotto a 81MB
   - players_stats.json escluso definitivamente da `.gitignore`
6. Push GitHub: 4045 file, 59.73 MiB compressi, OK
7. Vercel: importato repo `pid`, deploy automatico

### Configurazione finale
- `.env` (locale, gitignored): credenziali R2
- `vercel.json`: rewrites `/` → `/frontend/index.html`, headers cache su `/data/*`
- `.gitignore`: include venv/, *.log, __pycache__, *.saudi_backup, *.bak, scraping.pid, urls_test.txt, urls_remaining.txt, .env, data/players_stats.json, progetto_saudi_REFERENCE.md
- `frontend/app.js`: `R2_OVERRIDES = {"players_stats": "https://pub-aa9d173290684b36a9f35e79d4d388c2.r2.dev/players_stats.json"}`

### Account & risorse
- Cloudflare: simonecontran10@gmail.com, account ID `b8d30d0c945985ca7928fd7cf5548f0d`
- Vercel: progetto pid (team simone-contran-s-projects, plan Hobby)
- GitHub: simonecontran10/pid (pubblico)

### TODO sistemazione sito (post-deploy)
1. **Frontend Polonia** (rimasto in sospeso):
   - i18n.js: chiavi `league_pl1: "Ekstraklasa"`, `league_pl2: "1 Liga"` (IT + EN) + short
   - app.js renderClubs(): sezioni Ekstraklasa + 1 Liga
   - app.js filtri: option PL1, PL2 nei 3 dropdown
   - Loghi competizione PL1.png e PL2.png da TM
2. **Foto SortItOutSi polacchi**:
   - Aggiornare COMPETITIONS in scrape_sortitoutsi_competition.py con URL Ekstraklasa+1 Liga
   - Lanciare match SortItOutSi club polacchi
   - find_more_sots_matches.py per foto FM polacchi (auto cattura)
3. **Branding/UI**:
   - Sottotitolo vuoto sotto logo (volutamente per multi-paese)
   - Verifica colori sezioni: Serie A verde acceso, Serie B arancione, Polonia da definire
   - Ottimizzare logo PID (1254×1254 → 256×256, 996KB → ~50KB)
4. **Cleanup pendente**:
   - Variabili interne `saudi_by_id`, `n_saudi`, `step_filter_saudi`, `is_saudi_eligible` → rinominare `target_*`
   - `scraper/filter_saudi.py` (alias deprecato verso filter_target.py)
   - Alias `_saudiNationalTeamName` in app.js
   - Label `[SAUDI ✓]` nei log scraping (cosmetico)
5. **Custom domain**:
   - URL attuale: pid-7goy028x5-simone-contran-s-projects.vercel.app (lungo)
   - Settings Vercel: rinominare progetto a `pid` per ottenere `pid.vercel.app`
   - Eventualmente custom domain
6. **Update workflow**:
   - Quando aggiungo giocatori/foto in locale: `git add -A && git commit && git push` → redeploy automatico
   - Per aggiornare players_stats.json su R2: `python3 upload_to_r2.py data/players_stats.json` (sovrascrive)

### File chiave creati oggi
- `.env` (gitignored, credenziali R2)
- `upload_to_r2.py` (script reusable upload R2)
- `frontend/app.js` modificato con R2_OVERRIDES

## 6 mag 2026 (continuazione) — Frontend Polonia COMPLETATO + backfill loghi club

### Bug emersi a sito online
Aprendo il pannello "Club" sul deploy Vercel:
1. **36 club polacchi mescolati nella sezione "Primavera 1"**, totale visibile 56 club. Causa: frontend aveva una sola sezione catch-all `OTHER` che raccoglieva tutto ciò che non era IT1/IT2 e la etichettava "Primavera 1" via `league_other` in i18n.
2. **Loghi Primavera + Polonia spariti**: tutte le 56 card mostravano l'iniziale-lettera invece del logo.

### Diagnosi loghi
Ispezione di `data/clubs.json`:
- IT1 (20) + IT2 (20): tutti con `sortitoutsi_team_id` + `sortitoutsi_logo_url` ✅
- IJ1 (20): **nessun campo logo** (zero su tutti)
- PL1 (18) + PL2 (18): **nessun campo logo**

`clubLogo()` ritornava `null` → fallback iniziale-lettera. La nota del 6 mag "tutti i 20 club Primavera con logo" non era riflessa nel `clubs.json` pushato (modifica rimasta locale o sovrascritta dall'arricchimento Polonia).

### Frontend: refactor 5 sezioni esplicite
Eliminata la logica `OTHER` come "tutto il resto", sostituita da 5 leghe esplicite + fallback solo per league_id sconosciute.

**`frontend/i18n.js`** (IT + EN):
- Aggiunto `league_ij1`, `league_pl1: "Ekstraklasa"`, `league_pl2: "1 Liga"` + short
- `league_other` ora è davvero "Altre squadre" / "Other clubs" (era erroneamente "Primavera 1")

**`frontend/index.html`**:
- 3 nuove CSS variables: `--comp-ij1: #C084FC` (viola tenue), `--comp-pl1: #EF4444` (rosso), `--comp-pl2: #60A5FA` (blu). Servono per le pillole-accent; le sezioni usano i loghi competizione, non sfondi colorati.
- Dropdown `#filter-league`: rimossa option `OTHER`, aggiunte `IJ1`, `PL1`, `PL2` esplicite.
- Counter "Leghe" stats bar: era hardcoded `2`, ora `id="stat-leagues"` popolato dinamicamente in `renderClubs()` → mostra `5`.

**`frontend/app.js`** (8 modifiche):
1. `competitionLogo()` mappa `known`: aggiunti PL1, PL2, IJ1
2. `compColor()`: nuovi case per IJ1/PL1/PL2
3. `renderClubs()`: 5 sezioni separate (`it1` → `it2` → `ij1` → `pl1` → `pl2`) + fallback `others` per league_id non riconosciute. Logo competizione caricato per ognuna.
4. `applyFilters()`: la logica `OTHER` ora controlla `KNOWN_LEAGUES = {IT1,IT2,IJ1,PL1,PL2}` invece di solo IT1/IT2
5. 4 occorrenze di `isSaudi = (lg === "IT1" || lg === "IT2")` rinominate in `isKnownLeague` ed estese alle 5 leghe (residuo legacy del refactoring B.1 saudita)
6. 4 dropdown filtro lega (Home + Lista + Convocazione + Griglie + Minutaggi) aggiornati con IJ1/PL1/PL2
7. `COMP_LABEL`: pulite le label saudite legacy (IT1: "SPL"/Saudi Pro League, IT2: "FDL"/Saudi First Division, SA2P, ACLE/ACL2 Saudi…), aggiunte mapping corrette IT1/IT2/IJ1/PL1/PL2
8. `KNOWN_CLUB_CODES` e `CLUB_PRIORITY_ORDER`: estesi a IJ1/PL1/PL2

Sintassi JS verificata con `node --check` ✅

### Backfill loghi club: `backfill_club_logos.py`
Script standalone (root del progetto) che arricchisce `clubs.json` con `sortitoutsi_team_id` + `sortitoutsi_logo_url` per i 56 club mancanti. Strategia duale:

- **IJ1 (Primavera)**: SortItOutSi non ha squadre Primavera dedicate. Riusa il `sortitoutsi_team_id` del club di prima squadra in Serie A/B, matchato per nome normalizzato. Es. "Inter Milan Primavera" → "Inter Milan" → sots=1135.
- **PL1 + PL2**: scrappa pagine competizione SortItOutSi FM26:
  - PL1: `competition/129558/pko-bank-polski-ekstraklasa`
  - PL2: `competition/129559/polish-first-division`
  - Match per nome normalizzato (con mapping per lettere polacche `ł→l`, `Ł→L`)
  - 4 alias manuali per club non presenti su pagina competizione: Wieczysta Krakow (id=2000028546), LKS Lodz (id=1454, slug `lodzki-klub-sportowy`), Polonia Warsaw (id=1300879)

**Robustezza scraping**: SortItOutSi ritorna 403 alle requests Python da alcuni IP. Aggiunto fallback su `curl` come subprocess in `_fetch_via_curl()`. Headers HTTP completi (Sec-Fetch-*, Accept-Encoding, Cache-Control).

**Download loghi**: per ogni match riuscito scarica `https://sortitoutsi.b-cdn.net/uploads/team/{sots_id}.png` in `data/photos/clubs_sots/{tm_club_id}.png`. Skip se già presente >200 bytes (anti-placeholder GIF 1×1, pattern visto il 6 mag pomeriggio).

**Sincronizzazione file individuali**: oltre a `clubs.json`, lo script aggiorna anche `data/ij1_clubs.json`, `pl1_clubs.json`, `pl2_clubs.json` per consistenza.

**Risultato run**:
- IJ1: 20/20 ✅
- PL1: 18/18 ✅
- PL2: 17/18 (manca solo Pogoń Grodzisk Mazowiecki, non presente su SortItOutSi FM26 — promosso di recente)
- **Totale: 55/56 club arricchiti, 95/96 con logo (98.9%)**

Caso noto Pogoń Grodzisk: card mostra iniziale "P" come fallback. Quando SortItOutSi lo aggiungerà, basta inserire `"Pogon Grodzisk Mazowiecki": <id>` in `SOTS_MANUAL_OVERRIDES` e rilanciare lo script.

### Loghi competizione PL1/PL2
Scaricati da Transfermarkt (URL pattern `tmssl.akamaized.net/images/logo/header/<lower>.png`):
- `data/photos/competitions/PL1.png` (PKO Bank Polski Ekstraklasa, 6.4 KB)
- `data/photos/competitions/PL2.png` (Betclic 1 Liga, 16 KB)

Entrambi 139×181 PNG RGBA, formato standard TM coerente con IT1/IT2/IJ1.png già presenti.

### File modificati/creati oggi
- `frontend/i18n.js` (chiavi PL/IJ + fix `league_other`)
- `frontend/index.html` (CSS vars, dropdown, counter dinamico)
- `frontend/app.js` (8 modifiche, refactor sezione club + filtri + mapping competizioni)
- `backfill_club_logos.py` (nuovo, root)
- `data/clubs.json` (55 record arricchiti con sots_*)
- `data/ij1_clubs.json`, `pl1_clubs.json`, `pl2_clubs.json` (sync da clubs.json)
- `data/photos/competitions/PL1.png`, `PL2.png` (nuovi)
- `data/photos/clubs_sots/*.png` (55 nuovi: 20 IJ1 + 18 PL1 + 17 PL2)

### TODO sistemazione sito (post fix Polonia)
1. ⏳ Pogoń Grodzisk Mazowiecki: cercare logo manualmente o aspettare update SortItOutSi
2. **Foto SortItOutSi giocatori polacchi** (rimasto in sospeso):
   - `find_more_sots_matches.py` per matching automatico delle 1056 face polacche
   - Apply matches confirmed → JSON aggiornati → push
3. **Branding/UI**:
   - Ottimizzare logo PID (1254×1254 → 256×256, 996KB → ~50KB)
4. **Cleanup naming legacy** (residui refactoring B.1 saudita):
   - Variabili `saudi_by_id`, `n_saudi`, `step_filter_saudi`, `is_saudi_eligible` → `target_*`
   - `scraper/filter_saudi.py` (alias deprecato)
   - Alias `_saudiNationalTeamName` in app.js
   - Label `[SAUDI ✓]` nei log scraping
5. **Custom domain**: rinominare progetto Vercel → `pid.vercel.app`
6. **Update workflow** invariato: `git add -A && git commit && git push` → Vercel redeploy auto. R2 solo se cambia `players_stats.json`.

## 6 mag 2026 (sera continuazione 2) — UI refinements

### Modifiche
1. **Lingue ridotte**: rimossi pulsanti AR (Saudi/Arabo) e FR (Francese) dall'header. Restano solo EN + IT (le uniche con dizionario completo in i18n.js, le altre erano sempre stati pulsanti morti — `SUPPORTED_LANGS = ["it","en"]` già da prima). Pulito anche blocco CSS `html[dir="rtl"] *` (~14 righe morte) + `RTL_LANGS = new Set()` svuotato.
2. **Logo PID**: sostituito `data/photos/branding/logo.png` con la versione "PID logo 2" (era nel repo come `PID logo 2.png` 1.4 MB). Pipeline: crop dei margini trasparenti, padding a quadrato, resize 256x256 LANCZOS, save ottimizzato → **33 KB** (-98% dimensione). Aggiunta variante `logo@2x.png` 512x512 per future esigenze retina (100 KB).
3. **Logo header ingrandito**: `w-10 h-10` (40px) → `w-14 h-14` (56px), rimosso box arrotondato `rounded-lg` + bg bianco + border, logo ora "fluttua" sulla barra header con sfondo trasparente.
4. **Auth-gate logo**: 140x140 con box rounded → 160x160 trasparente puro.
5. **Loghi nelle player card**: bandiere nazione (bottom-left) e logo club (bottom-right) ridotti da `w-9 h-9` (36px) a `w-8 h-8` (32px), -11%.

### Note
- Loghi competizione (`data/photos/competitions/*.png`): già RGBA con alpha=0 ai bordi (TM li serve già con trasparenza). Nessuna modifica necessaria.
- Favicon (riga 8-10 di index.html): usa lo stesso file `branding/logo.png`, quindi il favicon del browser e dell'apple-touch-icon si aggiornano automaticamente.

### File modificati
- `frontend/index.html` (header, auth-gate, CSS RTL rimosso, dropdown lingue)
- `frontend/i18n.js` (commento + RTL_LANGS svuotato)
- `frontend/app.js` (2 occorrenze di w-9 → w-8 nelle player card)
- `data/photos/branding/logo.png` (sostituito con PID logo 2 ottimizzato 256x256)
- `data/photos/branding/logo@2x.png` (nuovo, 512x512)

## 6 mag 2026 (sera 3) — Sistema Preferiti + UI tweaks finali

### Modifiche
1. **Lingue**: rimossi pulsanti AR (Saudi/Arabo) e FR (Francese) dall'header. Restano solo EN + IT (le uniche con dizionario completo). Pulito CSS `html[dir="rtl"]` morto + `RTL_LANGS` svuotato.
2. **Logo PID nuovo**: sostituito `data/photos/branding/logo.png` con "PID logo 2" ottimizzato (1.4 MB → 33 KB, 256x256 RGBA con alpha). Aggiunta variante `logo@2x.png` 512x512.
3. **Logo header ingrandito**: w-10 h-10 (40px) → w-14 h-14 (56px), sfondo trasparente puro (rimosso box bianco/border).
4. **Auth-gate logo**: 140x140 con box rounded → 160x160 trasparente puro.
5. **Loghi nelle player card**: bandiere nazione + logo club ridotti da w-9 h-9 (36px) → w-8 h-8 (32px), -11%.
6. **Logo competizione sezioni Club**: w-6 h-6 (24px) → w-9 h-9 (36px), +50%, scritta "SERIE A" etc ora leggibile.
7. **Pogoń Grodzisk Mazowiecki**: logo trovato e applicato (sots_team_id=96056623, /team/96056623/pogon-grodzisk-mazowiecki). Aggiornato `clubs.json` + `pl2_clubs.json` + scaricato logo in `data/photos/clubs_sots/30998.png`. Aggiunto a `SOTS_MANUAL_OVERRIDES` di `backfill_club_logos.py` per memoria futura. **Ora 96/96 = 100% club con logo.**

### Sistema Preferiti (Favorites)
Nuova feature completa:
- **Storage**: `localStorage["pid_favorites"]` = JSON array di tm_player_id (persistente tra sessioni, scope browser)
- **Stato**: `state.favorites = Set<number>`. Helpers: `loadFavorites()`, `saveFavorites()`, `isFavorite(pid)`, `toggleFavorite(pid)`, `updateFavoritesBadge()`.
- **UI stella sulle player card** (home grid): in alto a destra, classe `.fav-star` con varianti `.is-fav` (oro pieno) vs default (vuota). Click su stella usa stopPropagation per non aprire il modal giocatore. Tooltip i18n.
- **Sidebar**: nuova voce "⭐ Preferiti" (route=`favorites`) tra Lista e Club, con badge contatore (`#favorites-badge`) che si nasconde quando 0.
- **Pannello dedicato** (`#favorites-panel`): griglia identica alla home, filtrata su `state.favorites`. Mostra header con icona stella + count. Stato vuoto con messaggio "Nessun preferito ancora. Aggiungi i giocatori cliccando la stella sulla loro scheda."
- **Bottone nel modal giocatore**: "★ Aggiungi/Rimuovi preferiti" tra "Aggiungi al confronto" e "+ Convoca". Aggiornamento sincrono dello state della stella su card e pannello.

### File modificati/creati
- `frontend/index.html` (header, auth-gate, sidebar, pannello favorites, CSS stella, CSS RTL rimosso)
- `frontend/i18n.js` (chiavi favorites IT+EN, RTL_LANGS svuotato)
- `frontend/app.js` (modulo favorites ~50 righe + stella su card + renderFavoritesPanel ~70 righe + bottone modal + setActiveTab routing + loadFavorites in init + UI tweaks dimensioni loghi)
- `data/photos/branding/logo.png` (sostituito con PID logo 2 256x256, 33 KB)
- `data/photos/branding/logo@2x.png` (nuovo, 512x512, 100 KB)
- `data/clubs.json` (Pogon Grodzisk Mazowiecki arricchito)
- `data/pl2_clubs.json` (sync)
- `data/photos/clubs_sots/30998.png` (logo Pogoń Grodzisk Mazowiecki)
- `backfill_club_logos.py` (Pogon aggiunto a SOTS_MANUAL_OVERRIDES)

### Note
- I preferiti sono **scope browser**, non sincronizzati tra dispositivi (richiederebbe Supabase/cloud_sync).
- Loghi competizione (`data/photos/competitions/*.png`): tutti già con sfondo trasparente. Nessuna modifica necessaria.
- Stato copertura loghi club: **96/96 = 100%** (era 95/96 = 98.9%).

## 6 mag 2026 (sera continuazione 2) — UI refinements + preferiti + loghi clean

### Modifiche

**1. Lingue ridotte a IT + EN**
- Rimossi pulsanti AR (🇸🇦) e FR (🇫🇷) dall'header `index.html`. Erano già pulsanti morti (`SUPPORTED_LANGS = ["it","en"]` da prima), nessun dizionario AR/FR in `i18n.js`.
- Pulito blocco CSS `html[dir="rtl"] *` (~14 righe morte) + `RTL_LANGS = new Set()` svuotato.

**2. Logo PID nuovo**
- Sostituito `data/photos/branding/logo.png` con la versione "PID logo 2" che era nel repo come `PID logo 2.png` (1.4 MB). Pipeline: crop margini trasparenti, padding quadrato, resize 256×256 LANCZOS, save ottimizzato → **33 KB** (-98%). Aggiunta variante `logo@2x.png` 512×512 (100 KB) per retina futuro.
- Header: `w-10 h-10` (40px) con box bianco arrotondato → `w-14 h-14` (56px) puro trasparente.
- Auth-gate: 140×140 con box → 160×160 trasparente.
- Favicon (`<link rel="icon">`): aggiunto `?v=20260506` per forzare refresh browser.

**3. Loghi club + nazione nelle player card**
- Bandiere e logo club: da `w-9 h-9` (36px) a `w-8 h-8` (32px), -11%.

**4. Loghi competizione "solo stemma"**
Sostituiti tutti i loghi TM (con scritta sotto tipo "SERIE A") con versioni clean:
- IT1 (Serie A "A" triangolo) — football-logos.cc, crop scritta
- IT2 (LNPB Lega B) — football-logos.cc, scritta integrata nel logo
- IJ1 (Primavera 1 stemma) — TM esistente, crop scritta "PRIMAVERA 1"
- PL1 (Ekstraklasa "e") — football-logos.cc, già pulito
- PL2 (1 Liga) — football-logos.cc, crop scritta
- CIT (Coppa Italia) — football-logos.cc, crop scritta
- CL (Champions League pallone-stelle) — seeklogo.com, crop "UEFA CHAMPIONS LEAGUE"
- EL (Europa League trofeo) — seeklogo.com, crop "UEFA EUROPA LEAGUE"
- UECL (Conference League) — seeklogo.com, crop "UEFA EUROPA CONFERENCE LEAGUE"
- SCI (Supercoppa) — TM esistente PS5 badge, niente fonte alternativa pulita

Pipeline Python:
1. flood-fill bordo per rimuovere sfondo bianco (alpha=0)
2. `find_text_split()` per identificare gap orizzontale tra stemma e testo (search dalla metà inferiore, gap minimo 8 pixel)
3. crop alla riga di gap
4. trim margini trasparenti, padding quadrato, resize 256×256 LANCZOS
5. save PNG ottimizzato

Tutti i file sostituiti in `data/photos/competitions/*.png`.

**5. Logo Pogon Grodzisk Mazowiecki**
- SortItOutSi `team_id=96056623` (slug `/team/96056623/pogon-grodzisk-mazowiecki`)
- Scaricato `https://sortitoutsi.b-cdn.net/uploads/team/96056623.png` → `data/photos/clubs_sots/30998.png`
- Aggiornato `data/clubs.json` e `data/pl2_clubs.json`
- Aggiunto a `SOTS_MANUAL_OVERRIDES` in `backfill_club_logos.py` per future run

Risultato: ora **96/96 club hanno logo (100%)**.

**6. Sistema preferiti** (era già implementato, attivato di fatto col push)
- `state.favorites` Set + persistenza `localStorage` (chiave `pid_favorites`)
- Bottone ☆/★ "Aggiungi/Rimuovi dai preferiti" nel modale dettaglio giocatore (riga ~895 di app.js)
- Pannello dedicato `<div id="favorites-panel">` con voce sidebar ⭐ Preferiti (HTML già presente in `index.html` riga 135-139)
- `renderFavoritesPanel()` mostra le card dei giocatori favoriti con stella per rimuoverli
- Badge contatore `favorites-badge` nella sidebar
- i18n IT+EN: `nav_favorites`, `favorites_title`, `favorites_empty`, `add_to_favorites`, `remove_from_favorites`
- **Stella NON appare** nelle mini-card della Home (richiesto esplicito: distrae). Aggiunta solo nel modale e nel pannello Preferiti.
- CSS `.fav-star` con effetto hover scale e color toggle giallo/grigio

### File modificati/creati
- `frontend/index.html` (header, auth-gate, CSS RTL rimosso, dropdown lingue, favicon ?v=)
- `frontend/i18n.js` (commento + RTL_LANGS svuotato)
- `frontend/app.js` (loghi card più piccoli, stella rimossa dalla home — modale e pannello preferiti intatti)
- `data/photos/branding/logo.png` (sostituito, ottimizzato 256×256)
- `data/photos/branding/logo@2x.png` (nuovo, 512×512)
- `data/photos/competitions/*.png` (10 file: IT1, IT2, IJ1, PL1, PL2, CIT, CL, EL, UECL, SCI)
- `data/photos/clubs_sots/30998.png` (Pogoń Grodzisk)
- `data/clubs.json`, `data/pl2_clubs.json` (Pogoń arricchito con sots_id)
- `backfill_club_logos.py` (alias Pogoń aggiunto)

### Commit pushati (Vercel deploy automatico)
- `23bc55b` — feat: sistema preferiti + logo Pogon + UI tweaks (lingue, logo PID, dimensioni)
- `f38a3c3` — ui: AR/FR via, logo PID nuovo, loghi competizione clean, Pogon Grodzisk, preferiti (no stella in home)

### TODO sistemazione sito (post UI refinements)
1. **Foto SortItOutSi giocatori polacchi** — `find_more_sots_matches.py` per matching automatico delle 1056 face polacche; apply matches confirmed → JSON aggiornati → push
2. **SCI (Supercoppa Italiana)** — logo attuale è il badge PS5 2020/21, sponsorship vecchia. Cercare versione "lega serie a coppa" pulita (Wikimedia commons / pagina FIGC ufficiale) quando avrai tempo
3. **Cleanup naming legacy** (residui refactoring B.1 saudita):
   - Variabili `saudi_by_id`, `n_saudi`, `step_filter_saudi`, `is_saudi_eligible` → `target_*`
   - `scraper/filter_saudi.py` (alias deprecato)
   - Alias `_saudiNationalTeamName` in app.js
   - Label `[SAUDI ✓]` nei log scraping
4. **Custom domain** — `pid-nine.vercel.app` (già attivo). Eventualmente registrare dominio personalizzato.
5. **Update workflow** invariato: `git add -A && git commit && git push` → Vercel redeploy auto. R2 solo se cambia `players_stats.json`.

## 6 mag 2026 (sera 4) — Seconde Squadre IT3 aggiunte

### Obiettivo
Aggiungere le 4 seconde squadre italiane (riserve di Serie A che militano in Serie C) al DB come nuova lega `IT3` "Seconde Squadre":
- Inter U23 (tm=41119)
- Milan Futuro (tm=41107)
- Juventus Next Gen (tm=41101)
- Atalanta U23 (tm=41110)

### Script `add_seconde_squadre.py`
Pipeline completa in un singolo script (root del progetto):
1. Crea `data/it3_clubs.json` con i 4 club hardcoded
2. Per ogni club, scrappa rosa da Transfermarkt (29+31+29+28 = 117 player_id unici)
3. Per ogni giocatore: `scrape_player_profile` + (se eligible italiano) `scrape_player_stats`
4. Riusa il `sortitoutsi_team_id` del club di prima squadra (mappatura `parent_tm_id`):
   - Inter U23 → tm=46 (Inter Milan, sots=1135)
   - Milan Futuro → tm=5 (AC Milan, sots=1099)
   - Juventus Next Gen → tm=506 (Juventus FC, sots=1139)
   - Atalanta U23 → tm=800 (Atalanta BC, sots=1106)
5. Aggiorna `clubs.json` master + lancia `enrich_sortitoutsi.py` + `download_photos.py`

Idempotente: ogni club già presente viene aggiornato senza duplicati. Salva ogni 10 giocatori per resilienza.

### Risultati run
- **Club**: 96 → **100** (+4 IT3)
- **Giocatori (target italiani)**: 2763 → **2858** (+95 nuovi target dalle 4 seconde squadre, +23 erano già nel DB perché in prestito da prime squadre, totale 118 con roster_club_id IT3)
- **Stats**: +13 (solo 13 italiani delle U23 hanno presenze stagionali con minutaggio significativo, gli altri sono giovanissimi senza stats valide)
- **Loghi club**: 100% (4/4 IT3 riusano i loghi locali delle prime squadre)
- **Foto giocatori**: scaricate 89 nuove (`Download loghi club: dl=89 cached=4739`)

### Bug fixato post-run
Dopo lo scraping, `enrich_sortitoutsi.py` ha resettato `sortitoutsi_team_id` e `sortitoutsi_logo_url` a `None` per i 4 club IT3 (perché non trova match SortItOutSi diretto per "Inter U23" etc, e azzera i campi "vuoti"). Il `sortitoutsi_logo_local` è invece sopravvissuto, quindi il frontend ha comunque il path corretto.

**Fix manuale post-run**: script Python inline che ripristina i campi `sots_team_id` e `sots_logo_url` riusando quelli del parent club (Inter, Milan, Juve, Atalanta). Crea anche `data/it3_clubs.json` mancante.

**TODO permanente**: modificare `enrich_sortitoutsi.py` perché non azzeri campi esistenti quando un team non viene trovato — deve solo SKIP il club, non sovrascrivere. Per ora il fix manuale va rilanciato dopo ogni `enrich_sortitoutsi.py` per i club delle seconde squadre.

### Frontend update per IT3
Modifiche speculari al fix Polonia (riapplicate perché il commit `f38a3c3` aveva applicato solo parzialmente le modifiche del fix Polonia):

**`frontend/i18n.js`**:
- `league_it3: "Seconde Squadre"` (IT) / `"Italian Reserve Teams"` (EN), short `"U23"`
- Fix legacy `league_other: "Altre squadre"` / `"Other clubs"` (era `"Primavera 1"`)

**`frontend/index.html`**:
- 4 nuove CSS variables: `--comp-ij1` (viola), `--comp-it3: #38BDF8` (azzurro Serie C), `--comp-pl1` (rosso), `--comp-pl2` (blu chiaro)
- Dropdown `#filter-league` (home): da 3 opzioni (IT1/IT2/OTHER) a 6 (IT1/IT2/IT3/IJ1/PL1/PL2). OTHER rimosso.
- Counter "Leghe" stats bar: da hardcoded `2` a `id="stat-leagues"` popolato dinamicamente da `renderClubs()` (mostra `6`).

**`frontend/app.js`** (13 modifiche):
1. `competitionLogo()` mappa `known`: aggiunto IT3
2. `compColor()`: case IT3 → `var(--comp-it3)`
3. `renderClubs()`: filtro `it3` + sezione `sectionHtml(t("league_it3"), it3Logo, ...)` inserita tra IT2 e IJ1, ordine = Serie A → Serie B → Seconde Squadre → Primavera → Ekstraklasa → 1 Liga
4. `it3Logo` URL aggiunto, `leaguesCount` esteso
5. `applyFilters()`: `KNOWN_LEAGUES` esteso a 6 leghe
6. 4 occorrenze `isKnownLeague` aggiornate (5 → 6 leghe)
7. 4 dropdown filtro lega in app.js (Home, Lista, Convocazione, Griglie, Minutaggi) aggiornati con IT3
8. `COMP_LABEL.IT3 = { short: "U23", full: "Seconde Squadre" }`
9. `KNOWN_CLUB_CODES` e `CLUB_PRIORITY_ORDER` estesi a IT3

Sintassi JS verificata con `node --check` ✅

### Logo competizione IT3
`data/photos/competitions/IT3.png` — logo Serie C ufficiale Transfermarkt (139×181, 23.6 KB, RGBA con alpha). Scaricato da `tmssl.akamaized.net/images/logo/header/it3a.png` (TM usa lo stesso logo per tutti e 3 i gironi A/B/C).

### File modificati/creati
- `add_seconde_squadre.py` (nuovo, root)
- `data/it3_clubs.json` (nuovo)
- `data/clubs.json` (+4 club IT3, 96 → 100)
- `data/players_main.json` (+95 nuovi italiani target, 2763 → 2858)
- `data/players_static.json` (sync)
- `data/players_stats.json` (+13 stats)
- `data/players_all.json` (+117 nuovi profili totali, anche non-target)
- `data/photos/competitions/IT3.png` (nuovo, 24 KB)
- `frontend/index.html` (CSS vars, dropdown filtro home, counter dinamico)
- `frontend/i18n.js` (chiavi IT3 + fix league_other legacy)
- `frontend/app.js` (13 modifiche IT3)

### TODO
1. Modificare `enrich_sortitoutsi.py` perché non resetti campi sots esistenti quando il team non è trovato (per evitare il bug ricorrente sulle Seconde Squadre)
2. Verificare che le 89 nuove foto giocatori IT3 siano corrette (i 95 italiani vanno controllati a campione su SortItOutSi)

## 7 mag 2026 — ⚠️ NOTA CONCETTUALE CHIAVE: PID è country-agnostic

### Principio fondamentale (da non dimenticare)
**PID NON filtra per nazionalità dei giocatori.** Il database include TUTTI i giocatori delle leghe target (Serie A, Serie B, Seconde Squadre, Primavera, Ekstraklasa, 1 Liga), indipendentemente dalla cittadinanza.

Questo è chiaramente documentato in `scraper/filter_target.py`:
> "PID — country-agnostic: per default ogni profilo è 'eligible' perché PID raccoglie TUTTI i giocatori delle leghe target (Serie A include 28+ nazionalità diverse)."
> `is_target_eligible()` ritorna sempre `True`.

### Perché è importante ricordarlo
Il progetto **deriva** da un fork del "Saudi Players Hub" (focus solo giocatori sauditi), e ci sono ancora **alias legacy ovunque** che possono trarre in inganno:
- `is_saudi_eligible` (alias deprecato di `is_target_eligible`)
- `PLAYERS_SAUDI_FILE` (alias di `PLAYERS_MAIN_FILE`)
- `players_saudi.json` ↔ `players_main.json`
- `n_saudi`, `saudi_by_id`, `step_filter_saudi` come variabili locali in script
- `SAUDI_NATIONALITY` in config.py
- `scraper/filter_saudi.py` (alias deprecato)
- Tag `[SAUDI ✓]` nei log scraping
- Negli script "is_saudi_eligible" è usato come booleano semantico ma in realtà = "deve entrare nel DB" (cioè TRUE per tutti)

**Errore comune da evitare**: scrivere logica che ASSUME che `is_saudi_eligible/is_target_eligible` sia un filtro di nazionalità, magari perché il nome lo suggerisce. Non lo è. È un flag tecnico che vale `True` per tutti i giocatori scrappati delle leghe target.

### Implicazioni per le Seconde Squadre (IT3)
Le 4 seconde squadre italiane hanno rose miste con stranieri (sudamericani, africani, est-Europa) che il club valuta per il futuro. Il DB DEVE includere tutti, non solo gli italiani.

Numeri attesi (da rosa Transfermarkt): Inter U23 ≈29, Milan Futuro ≈31, Juventus Next Gen ≈29, Atalanta U23 ≈28 = **~117 totali**.
Numeri visti online dopo il push del 6 mag: 15 + 22 + 24 + 20 = **81**.
**Discrepanza: -36 giocatori, da debuggare.**

### TODO permanente — cleanup naming legacy
Dopo aver risolto il bug delle seconde squadre, programmare un cleanup:
1. Rinomina `is_saudi_eligible` → `is_target_eligible` ovunque (ultimo alias rimasto)
2. Rinomina `players_saudi.json` → `players_main.json` (file fisico, non solo costante Python)
3. Variabili locali `saudi_by_id` → `main_by_id`, `n_saudi` → `n_eligible`, `step_filter_saudi` → `step_filter_target`
4. Cancella `scraper/filter_saudi.py` (è solo un re-export di `filter_target.py`)
5. Tag log `[SAUDI ✓]` → `[TARGET ✓]` o rimuovi del tutto
6. Costante `SAUDI_NATIONALITY` in `scraper/config.py` → `TARGET_NATIONALITY` (solo per uso "Italy" nei nomi nazionale)

### Fix applicato (7 mag, sera)
3 modifiche in `frontend/app.js`:
1. `playersByClubCount` (riga ~568): da `current === cid` a `current === cid || roster === cid`
2. `nPlayers` card pannello Club (riga ~587): stessa logica OR
3. `applyFilters` filtro lega home (riga ~477): `leagueClubIds.has(p.current_club_id) || leagueClubIds.has(p.roster_club_id)`

Effetto: 14 club guadagnano 1-14 giocatori in più. Inter U23 passa da 15 a 29, Milan Futuro da 22 a 32, Juventus Next Gen da 24 a 29, Atalanta U23 da 20 a 28. **I numeri online ora corrispondono alla rosa Transfermarkt scrappata.**

Lasciato invariato: `applyFilters` per Lista/Convocazione/Griglie/Minutaggi (rige 1986, 2889, 3832, 4414) — lì la semantica deve restare "un giocatore in un club" via `current_club_id`, altrimenti i 71 doppi comparirebbero due volte nelle liste.

## 7 mag 2026 (sera 2) — Cloud sync Supabase riattivato + login obbligatorio

### Bug strutturale trovato
1. `cloud_sync.js` era **commentato** in `index.html` (riga 272: `<!-- ... cloud sync disabilitato -->`). Spiega perché il sito si apriva senza login e i salvataggi non andavano nel cloud.
2. **Naming bug**: `cloud_sync.js` faceva sync su chiavi `saudi_*` (legacy) ma `app.js` salva su `pid_*` (post-rename). Risultato: cloud riceveva sempre dati vuoti, e dopo il login vedevi un sito vuoto.
3. **Mancavano `pid_favorites` e `saudi_minutes_v1`** dalla mappa LS_TO_CLOUD. Anche se il sync avesse funzionato, preferiti e minutaggi sarebbero rimasti solo locali.
4. **Schema DB**: tabella `user_state` su Supabase non aveva le colonne `minutes` e `favorites`.
5. **Fallback insicuro**: `cloudInitAuth()` se Supabase non si caricava (CDN giù) sbloccava il sito senza autenticazione.

### Fix applicato
- **`frontend/index.html`**: riattivato `<script src="cloud_sync.js?v=20260507a"></script>`.
- **`frontend/cloud_sync.js`** riscritto:
  - Mappa LS_TO_CLOUD con chiavi `pid_*` corrette + `pid_favorites` + `saudi_minutes_v1`
  - Funzione `_migrateLegacyKeys()` che al primo avvio rinomina silenziosamente `saudi_player_notes` → `pid_player_notes`, `saudi_grids_v1` → `pid_grids_v1`, `saudi_callup_active` → `pid_callup_active` (per chi aveva dati legacy nel browser)
  - `_buildColumnValue()` aggiornato per legge dalle chiavi giuste
  - `_onFirstSignIn()` aggiornato per upload/download anche di minutes + favorites
  - Fallback "supabase non caricato → sblocca sito" rimosso. Ora se Supabase fallisce mostra errore esplicito sull'auth-gate.
- **Schema Supabase**: file `supabase_setup.sql` (nuovo, root) idempotente che crea/aggiorna la tabella `user_state` con tutte le colonne necessarie + Row Level Security (ogni utente vede solo i propri dati).

### Login obbligatorio
Da ora il sito richiede login all'apertura: schermata fullscreen "Accedi" con email/password. Opzioni: Crea account (signup con conferma email), Magic link, Forgot password (reset).

### Note conservate per chiavi LS legacy
`saudi_callups_v1` e `saudi_minutes_v1` restano "saudi_" nei nomi delle costanti (`CALLUP_STORAGE_KEY` e `MINUTES_STORAGE_KEY` in app.js), perché sono identificatori opachi lato utente. Rinominarle richiederebbe migrazione dati senza valore funzionale. Le altre chiavi (notes, grids, callup_active, favorites) usano nomenclatura `pid_*` corretta.

### File modificati
- `frontend/index.html` (riattivato cloud_sync.js)
- `frontend/cloud_sync.js` (riscritto, ~390 righe)
- `supabase_setup.sql` (nuovo, root, da eseguire UNA VOLTA sul dashboard Supabase)

### Esito test login (7 mag, sera 3)
- ✅ Auth-gate appare correttamente all'apertura del sito
- ✅ Connessione Supabase OK (errore "User already registered" su signup conferma che il backend risponde)
- ✅ Login con credenziali esistenti riuscito (account `simonecontran10@gmail.com` ereditato dal vecchio Saudi Players Hub Supabase project — il progetto Supabase è condiviso)
- ✅ Sito accessibile post-login

### Note importanti per il futuro
- Il progetto Supabase è "Saudi Players Hub" (org SAFF) — condiviso tra Saudi Hub originale e PID. Le credenziali sono comuni. Per ora va bene, ma se in futuro PID deve essere completamente separato dal vecchio Saudi Hub, va creato un nuovo progetto Supabase dedicato (nuova URL + nuova publishable key in `cloud_sync.js`).
- Schema `user_state` ora ha 8 colonne: `user_id, callups, notes, grids, minutes, favorites, created_at, updated_at`. Row Level Security attivo: ogni utente vede solo i propri dati.
- Tutti gli utenti del Saudi Hub originale possono accedere a PID con le loro credenziali esistenti, ma NON vedono dati Saudi (le colonne sono le stesse, ma i dati che app.js scrive sono per PID — cioè se un utente Saudi accede a PID per la prima volta vede DB vuoto e i suoi dati LS PID vengono caricati).

### TODO follow-up
- Verificare che il sync funzioni cross-device: login con stessa email su altro browser/iPhone → vedere stessi salvataggi
- Considerare separazione Supabase (project dedicato PID) quando il Saudi Hub originale verrà dismesso

## 7 mag 2026 (sera 4) — Separazione progetto Supabase PID dedicato

### Problema rilevato
Dopo l'attivazione del cloud sync, login con `simonecontran10@gmail.com` su PID ha caricato dati salvati nel **vecchio Saudi Players Hub Supabase project** (org SAFF, URL `akhmipddijvbphhguuvw.supabase.co`):
- 3 preferiti — corretti (PID)
- 2 griglie — alcune erano del Saudi Hub
- 71 giocatori in convocazione attiva — del Saudi Hub
- 2 liste convocazione — del Saudi Hub

Causa: i due siti puntavano allo stesso DB Supabase con le stesse colonne (`callups, notes, grids`). Quando l'utente esisteva già nel DB Saudi, `_onFirstSignIn()` su PID scaricava quei dati in localStorage PID.

Console mostrava warning `Multiple GoTrueClient instances detected` perché il modulo Supabase era istanziato sia dal codice Saudi (se mai caricato) sia da PID.

### Decisione: nuovo progetto Supabase dedicato a PID
- I dati Saudi Hub restano dove sono (non li tocchiamo)
- PID parte da zero con nuovo DB pulito
- Decisione: NON migrare i dati attuali — i 3 preferiti/griglie/convocazioni esistenti vengono ricreati da zero
- Setup nuovo progetto: org/account simone, region Frankfurt, plan Free

### Note configurazione setup
- **Enable Data API**: ON (necessario per supabase-js)
- **Automatically expose new tables**: ON (rende user_state disponibile via REST quando viene creata)
- **Enable automatic RLS**: OFF (l'SQL setup gestisce RLS esplicitamente con 4 policy)

### TODO immediati
- [x] Crea nuovo progetto Supabase "PID"
- [ ] Lancia `supabase_setup.sql` sul nuovo progetto (schema user_state + RLS)
- [ ] Recupera nuova URL Supabase + nuova publishable key
- [ ] Aggiorna `frontend/cloud_sync.js` riga 23-24 con nuove credenziali
- [ ] Push e nuovo signup PID

### Esito finale (7 mag, sera 4) — ✅ Cloud sync PID dedicato funzionante
- **Nuovo progetto Supabase PID** creato: URL `https://mbghahzykbsaudcpybdh.supabase.co`, region Frankfurt, plan Free
- Schema `user_state` setup tramite SQL editor (8 colonne: user_id, callups, notes, grids, minutes, favorites, created_at, updated_at + 4 RLS policy: select/insert/update/delete own)
- Credenziali aggiornate in `frontend/cloud_sync.js` riga 20-21
- Configurazione Authentication → URL Configuration:
  - Site URL: `https://pid-nine.vercel.app`
  - Redirect URLs allowlist: `https://pid-nine.vercel.app`, `https://pid-nine.vercel.app/**`, `http://localhost:8000/**`
- Signup riuscito con email `simonecontran10@gmail.com` (account nuovo nel DB PID, **separato** dal Saudi Hub)
- Email Supabase ora redirige correttamente a `pid-nine.vercel.app` post-conferma

### Conferma DB separato
Console post-login mostra `user_id: 34da1ed9-c767-40bf-844b-ecfb953f7e3b` — diverso da `c5c05e82-ae99-4e55-8323-6743a7caeb9c` del Saudi Hub. I due progetti Supabase sono completamente isolati anche se condividono l'email.

### Pulizia dati locali post-migrazione
Al primo login sul DB PID nuovo, `_onFirstSignIn()` ha trovato cloud vuoto e caricato i dati di localStorage attuali (3 preferiti, 2 griglie, 71 convocati) — ma erano residui mescolati di Saudi Hub. Eseguito reset manuale via console JavaScript:
```js
cd ~/Desktop/pid && cat >> progetto-pid.md << 'EOF_DIARY'

### Esito finale (7 mag, sera 4) — ✅ Cloud sync PID dedicato funzionante
- **Nuovo progetto Supabase PID** creato: URL `https://mbghahzykbsaudcpybdh.supabase.co`, region Frankfurt, plan Free
- Schema `user_state` setup tramite SQL editor (8 colonne: user_id, callups, notes, grids, minutes, favorites, created_at, updated_at + 4 RLS policy: select/insert/update/delete own)
- Credenziali aggiornate in `frontend/cloud_sync.js` riga 20-21
- Configurazione Authentication → URL Configuration:
  - Site URL: `https://pid-nine.vercel.app`
  - Redirect URLs allowlist: `https://pid-nine.vercel.app`, `https://pid-nine.vercel.app/**`, `http://localhost:8000/**`
- Signup riuscito con email `simonecontran10@gmail.com` (account nuovo nel DB PID, **separato** dal Saudi Hub)
- Email Supabase ora redirige correttamente a `pid-nine.vercel.app` post-conferma

### Conferma DB separato
Console post-login mostra `user_id: 34da1ed9-c767-40bf-844b-ecfb953f7e3b` — diverso da `c5c05e82-ae99-4e55-8323-6743a7caeb9c` del Saudi Hub. I due progetti Supabase sono completamente isolati anche se condividono l'email.

### Pulizia dati locali post-migrazione
Al primo login sul DB PID nuovo, `_onFirstSignIn()` ha trovato cloud vuoto e caricato i dati di localStorage attuali (3 preferiti, 2 griglie, 71 convocati) — ma erano residui mescolati di Saudi Hub. Eseguito reset manuale via console JavaScript:
```js
['pid_favorites','pid_grids_v1','pid_callup_active','pid_player_notes',
 'saudi_callups_v1','saudi_minutes_v1','saudi_player_notes','saudi_grids_v1',
 'saudi_callup_active'].forEach(k => localStorage.removeItem(k));
// + upsert riga user_state con valori vuoti
```

### Note su separazione progetti Supabase
- **Saudi Hub Supabase** (vecchio): `akhmipddijvbphhguuvw.supabase.co` (org SAFF) — non più referenziato da PID
- **PID Supabase** (nuovo): `mbghahzykbsaudcpybdh.supabase.co` — DB pulito, dedicato a PID
- I due sono completamente isolati. Login su PID NON mostra dati Saudi e viceversa.

### Sicurezza: rotazione service_role key
Durante il setup è stata accidentalmente esposta la `sb_secret_*` del nuovo progetto. Procedura: dashboard PID → Settings → API → "Roll secret" sulla service role key per invalidare l'esposizione e generare nuova chiave.

### Costo Supabase Free Tier
- 500 MB storage, 50K monthly active users, 5 GB bandwidth
- Per PID con uso personale (1-10 utenti): largamente sufficiente
- Auto-pausa dopo 1 settimana di inattività, riprende automaticamente

### TODO follow-up
- [ ] Test cross-device per conferma definitiva sync (login da iPhone con stessa credenziale → vedere stessi salvataggi)
- [ ] Nascondere bottone "🔐 Accedi" sidebar quando `cloudAuth.user` è valorizzato (residuo cosmetico legacy)
- [ ] Pulire fetch a `127.0.0.1:8000/update/status` (vecchio dev server, non serve in production)
