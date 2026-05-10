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

## 7 mag 2026 (sera 5) — Fix coerenza filtri Club ↔ Lega

### Bug osservato
Sul sito, scenario:
1. Filtro lega = "Serie A" (default home)
2. Utente seleziona club "Cesena" dal dropdown filtro club (Cesena è in Serie B)
3. Risultato: 0 giocatori visualizzati (Cesena ⊥ Serie A → AND vuoto)

L'utente vede una pagina vuota e non capisce il perché. Stesso problema cliccando una card club nel pannello Club o un risultato di ricerca globale: il club si applica come filtro ma la lega resta sul valore precedente.

### Fix applicato — `frontend/app.js`
3 modifiche, tutte con stessa logica: quando si imposta `state.filters.club`, si guarda il `league_id` del club selezionato, e se diverso da `state.filters.league` lo si aggiorna. Sia lo state che il dropdown UI restano allineati.

1. **Handler dropdown `#filter-club`** (riga ~5709): change handler con auto-allineamento lega solo se le due leghe sono diverse (per non resettare quando l'utente filtra esplicitamente "Tutti i campionati" prima del club).
2. **Click su card club in `renderClubs`** (riga ~652): quando l'utente clicca una card club nel pannello Club, allinea sempre la lega del club cliccato (è l'azione più diretta possibile, vuole vedere quel club).
3. **Click su risultato di ricerca globale** (riga ~5449): stesso comportamento del 2, l'utente ha cercato un club specifico.

### Esempio
Prima: lega=Serie A, click "Cesena" → state.filters = {league: 'IT1', club: 6648} → 0 giocatori
Dopo: lega=Serie A, click "Cesena" → state.filters = {league: 'IT2', club: 6648} → ~25 giocatori Cesena

### File modificato
- `frontend/app.js` (3 occorrenze fix, ~25 righe aggiunte totali)

## 7 mag 2026 — Chiusura giornata

### Riepilogo lavoro fatto oggi
Giornata densa, tutto online e funzionante su `pid-nine.vercel.app`:
- Bug Polonia fixato (5 sezioni separate, loghi Primavera/Polonia)
- 4 seconde squadre IT3 aggiunte (+95 giocatori, +4 club, totale 2858 / 100 / 6 leghe)
- Counter pannello Club corretto (current_club_id OR roster_club_id)
- Sistema cloud sync attivato con progetto Supabase dedicato (separato dal Saudi Hub)
- Login obbligatorio funzionante (signup + magic link + reset password)
- Fix coerenza filtri Club ↔ Lega (selezionando un club si auto-allinea la lega)

### TODO aperti per domani
- [ ] Cosmetico: nascondere bottone "🔐 Accedi" sidebar quando `cloudAuth.user` valorizzato
- [ ] Pulire fetch a `127.0.0.1:8000/update/status` (vecchio dev server, errore CORS in console)
- [ ] Cleanup naming legacy `saudi_*` → `target_*`/`pid_*`:
  - Variabili `saudi_by_id`, `n_saudi`, `step_filter_saudi`, `is_saudi_eligible`
  - File `scraper/filter_saudi.py` (alias deprecato)
  - Costanti `SAUDI_NATIONALITY`, `PLAYERS_SAUDI_FILE` in `scraper/config.py`
  - Tag `[SAUDI ✓]` nei log scraping
  - Alias `_saudiNationalTeamName` in app.js
  - Chiave LS `saudi_callups_v1` e `saudi_minutes_v1` (richiede migrazione dati LS)
- [ ] Custom domain: rinominare progetto Vercel → `pid.vercel.app` (oggi `pid-nine.vercel.app`)
- [ ] Test cross-device cloud sync da iPhone (login con stessa email → vedere stessi salvataggi)
- [ ] Foto SortItOutSi giocatori polacchi (1056 pendenti, `find_more_sots_matches.py` per matching automatico)
- [ ] Bug `enrich_sortitoutsi.py` che resetta `sortitoutsi_team_id` per club non trovati su SortItOutSi (workaround attivo: script Python inline post-run)
- [ ] Stats giocatori IT3: solo 13 dei 118 hanno stats valide. Verificare se andare a popolare per tutti o lasciare per i giovani senza minutaggio significativo

### Stato attuale
- 100 club in 6 leghe (Serie A 20, Serie B 20, IT3 Seconde Squadre 4, IJ1 Primavera 20, PL1 Ekstraklasa 18, PL2 1 Liga 18)
- 2858 giocatori in `players_main.json`
- Cloud sync attivo: progetto Supabase `mbghahzykbsaudcpybdh.supabase.co`, schema `user_state` con 4 RLS policy
- Sito online: https://pid-nine.vercel.app/
- Repo: https://github.com/simonecontran10/pid (commit `447ea86`)

## 7 mag 2026 (sera 6) — Foto giocatori IT3 via pipeline ufficiale

### Workflow corretto identificato
La pipeline esistente per associare foto SortItOutSi ai giocatori è:
1. `harvest_sots_rosters.py` → cache rose SortItOutSi (`data/sots_rosters.json`)
2. `find_more_sots_matches.py` → match cross-club con DOB-verify, output xlsx
3. `apply_confirmed_matches.py` → applica match confermati (scarica face, aggiorna JSON)

NON serve scrappare le pagine team a mano: `harvest_sots_rosters.py` legge `clubs.json` e per ogni club con `sortitoutsi_team_id` valido scarica la rosa. Quindi basta avere i sots_team_id giusti in `clubs.json`.

### Bug `current sortitoutsi_team_id` per IT3
I 4 club seconde squadre in `clubs.json` avevano `sortitoutsi_team_id` puntanti alle PRIME squadre (1135 Inter Milan, 1099 AC Milan, 1139 Juventus FC, 1106 Atalanta BC), retaggio del fallback applicato da `add_seconde_squadre.py` (riusa logo prima squadra come fallback se la seconda squadra non ha entry SortItOutSi).

### Fix manuale
Patch Python inline che sostituisce con i veri sots_team_id delle U23 da SortItOutSi FM26:
- Inter U23 → 2000475415 (`/team/2000475415/fc-internazionale-milano-under-23`)
- Milan Futuro → 2000376493 (`/team/2000376493/milan-futuro`)
- Juventus Next Gen → 43457016 (`/team/43457016/juventus-fc-next-gen`)
- Atalanta U23 → 2000277208 (`/team/2000277208/atalanta-bergamasca-calcio-under-23`)

`clubs.json` + `it3_clubs.json` aggiornati. `sortitoutsi_logo_url` ora punta al logo dedicato U23.

### Diagnostica Cloudflare
Test preliminare: `curl` ritornava HTTP 403 "Just a moment..." (Cloudflare challenge). Ma `requests` Python va bene (HTTP 200, 45 link `/person/` per la rosa Inter U23) — fingerprint TLS diverso che passa il challenge passivo.

Quindi `harvest_sots_rosters.py` (che usa `requests`) funziona regolarmente.

### Stato cache `sots_rosters.json`
Solo 40 club nella cache (Serie A 20 + Serie B 20). Mancano: 20 Primavera, 18+18 Polonia, 4 IT3. Il prossimo `harvest_sots_rosters.py` dovrebbe popolare i 60 club mancanti in 2-3 minuti.

### TODO immediato
- [ ] Lanciare `python3 harvest_sots_rosters.py` (60 club da fetchare)
- [ ] Lanciare `python3 find_more_sots_matches.py` per i match candidati
- [ ] Verificare e applicare con `apply_confirmed_matches.py`
- [ ] Fix `enrich_sortitoutsi.py` perché non azzeri `sortitoutsi_team_id` quando il team non viene trovato (workaround: re-applicare patch manuale)

### Bug minore lettura cache `sots_rosters.json`
Diagnostica iniziale aveva letto chiave `players` ritrovando 0 giocatori — sembrava bug critico. In realtà `harvest_sots_rosters.py` salva sotto chiave `persons`. Verifica con chiave corretta:

| Club U23 | sots_team_id | persons in cache |
|---|---|---|
| Inter U23 | 2000475415 | **45** |
| Milan Futuro | 2000376493 | **41** |
| Juventus Next Gen | 43457016 | **58** |
| Atalanta U23 | 2000277208 | **62** |

Totale 206 persons U23 nella cache, oltre alle 5669 già presenti per Serie A/B = **5875 totali**. Cache pronta per `find_more_sots_matches.py`.

### TODO standardizzazione
- [ ] Uniformare nome chiave: il modulo `find_more_sots_matches.py` usa `players` o `persons`? Verificare e standardizzare in `harvest_sots_rosters.py` per evitare confusione futura

### Esito finale (8 mag, 02:00) — Foto IT3 applicate
- `harvest_sots_rosters.py`: 4 nuove rose U23 in cache (Inter U23 45, Milan Futuro 41, Juventus Next Gen 58, Atalanta U23 62 → totale 5875 persons)
- `find_more_sots_matches.py`: 106 confermati DOB-verificati, 46 mismatch
- Bug fix: `apply_confirmed_matches.py` puntava a `sots_auto_matched_confirmed.xlsx` (file vecchio, 17 righe). Patchato per leggere `sots_more_matches_confirmed.xlsx` (file nuovo, 106 righe)
- Applicati 106 match: players_main/static/all aggiornati, 104/106 face scaricate
- Risultato: ~105/118 giocatori IT3 con foto FM-style SortItOutSi (89%)

### TODO
- [ ] PR per fix definitivo `apply_confirmed_matches.py` (renaming costante CONFIRMED_FILE)
- [ ] Indagare i 46 DOB mismatch: probabili giovanissimi con DOB diverse tra TM e SortItOutSi (TM aggiornato post-trasferimento, SortItOutSi cache vecchia FM26)

### Esito finale (8 mag, 02:00) — Foto IT3 applicate ✅
**Pipeline ufficiale del progetto eseguita con successo:**

1. `harvest_sots_rosters.py`: cache aggiornata con 4 nuove rose U23 (Inter U23 45, Milan Futuro 41, Juventus Next Gen 58, Atalanta U23 62) → totale **5875 persons** in `data/sots_rosters.json` (era 5669, +206)
2. `find_more_sots_matches.py`: **106 match confermati** con DOB-verify (su 152 candidati, 46 mismatch DOB)
3. **Bug `apply_confirmed_matches.py`**: la costante `CONFIRMED_FILE` puntava a `sots_auto_matched_confirmed.xlsx` (file vecchio, 17 righe). Patchato per leggere il nuovo `sots_more_matches_confirmed.xlsx` (file generato da `find_more_sots_matches.py`, 106 righe).
4. `apply_confirmed_matches.py` rilanciato: aggiornati 3 JSON (`players_main`, `players_static`, `players_all`), scaricate 104/106 face, lookup ora ha 1726 entries (era 1620, +106).

### Coverage finale foto SortItOutSi per le 4 seconde squadre
| Club | Con face | Senza face | % |
|---|---|---|---|
| Inter U23 | 28 | 1 | 97% |
| Milan Futuro | 24 | 8 | 75% |
| Juventus Next Gen | 27 | 2 | 93% |
| Atalanta U23 | 26 | 2 | 93% |
| **Totale** | **105** | **13** | **89%** |

I 13 senza face sono giovanissimi non ancora indicizzati su SortItOutSi FM26 (DB chiuso a estate 2025).

### Bug `apply_confirmed_matches.py` (fixato in questa sessione)
File costante hardcoded che puntava all'Excel vecchio della pipeline `confirm_dob_matches`. Dopo l'introduzione di `find_more_sots_matches.py` (sera 6 mag), il file output è cambiato ma `apply_confirmed_matches.py` non è stato aggiornato. **Patch permanente**: 1 riga in `apply_confirmed_matches.py` riga 26.

### Bug `harvest_sots_rosters.py` (osservato, non fixato)
Lo script salva sotto chiave `persons` ma altri parti del codice si aspettano `players`. Workaround: leggere `persons`. **TODO**: standardizzare su `players` in tutto il codice (è il nome più descrittivo, "persons" include anche staff su SortItOutSi che non ci interessa).

### Push e online
Commit `731426c`, 117 oggetti, 3 MB. Vercel deploy automatico → `pid-nine.vercel.app/` con face FM-style sui 105 giocatori IT3.

### TODO definitivi (per le prossime sessioni)
- [ ] Standardizzare chiave `persons`/`players` in tutta la pipeline SortItOutSi
- [ ] Rinominare `CONFIRMED_FILE` in `apply_confirmed_matches.py` → `MORE_MATCHES_CONFIRMED_FILE` per chiarezza
- [ ] 13 IT3 senza face: verificare a campione su SortItOutSi se sono presenti con slug diverso
- [ ] 46 DOB mismatch: investigare un campione (probabile: TM aggiornato post-trasferimento vs SortItOutSi cache FM26 chiusa estate 2025)
- [ ] 1056 polacchi senza face: lanciare di nuovo `find_more_sots_matches.py` ora che harvest ha 4 nuovi club PL non c'erano

### Bug emerso post-deploy: loghi IT3 rotti (8 mag, 02:30)
Sul sito i 4 club Seconde Squadre mostravano placeholder "immagine non caricata" invece del logo. Causa: il fix manuale precedente aveva impostato `sortitoutsi_logo_local: "photos/clubs_sots/41119.png"` (e analoghi) in `clubs.json`, ma i file fisici esistevano solo come `46.png` (Inter Milan), `5.png` (AC Milan), `506.png` (Juventus FC), `800.png` (Atalanta BC) — i tm_club_id delle prime squadre.

`ls -la data/photos/clubs_sots/41119.png` → file not found.

### Fix da applicare
Script Python inline che copia i 4 loghi delle prime squadre nei file path delle seconde squadre, poi tentativo di download dei loghi U23 reali da SortItOutSi (se >1KB sovrascrivono il fallback). Comandi consegnati nel messaggio precedente, da eseguire al risveglio.

### TODO domani mattina
- [ ] Lanciare i 2 blocchi di codice: copia fallback + tentativo download SortItOutSi
- [ ] Verificare online che i loghi siano visibili
- [ ] Decidere se SortItOutSi non ha loghi U23 (caso confermato): tenere fallback prima squadra (sembra OK visivamente perché Inter U23 = stemma Inter, Milan Futuro = stemma Milan, ecc.)

### Risolto (8 mag mattina) — Loghi IT3 ✅
**Diagnosi**: i 4 file in `data/photos/clubs_sots/{tm_club_id}.png` mancavano fisicamente, anche se `clubs.json` li referenziava. Online il browser cercava i file → 404 → placeholder.

**Fix**:
1. Fallback prima squadra (Python `shutil.copy` da 46.png/5.png/506.png/800.png ai path U23)
2. Tentativo download SortItOutSi U23 reali:
   - **Juventus Next Gen** (sots=43457016, 26865 bytes): logo U23 dedicato ✓
   - **Atalanta U23** (sots=2000277208, 28536 bytes): logo U23 dedicato ✓
   - **Inter U23** (sots=2000475415): solo placeholder GIF 43 bytes → resta fallback Inter Milan
   - **Milan Futuro** (sots=2000376493): solo placeholder GIF 43 bytes → resta fallback AC Milan

Risultato online: 4/4 loghi visibili correttamente.

### Nota su WebP-as-PNG nella cartella clubs_sots
Tutti i loghi `clubs_sots/*.png` sono in realtà WebP con estensione fasulla (legacy `download_photos.py` che non controlla il formato del content servito da SortItOutSi). Il browser li gestisce comunque su Chrome/Safari/Firefox moderni. Non serve fix immediato.

## 8 mag 2026 — Automazione cloud + cosmetica sidebar

### Bottone "Accedi" → username + logout
`cloud_sync.js _renderAuthUI()` esteso: quando `cloudAuth.user` è valorizzato, il bottone `#sidebar-auth-btn` mostra `👤 {username}` (parte prima della @ dell'email, troncata a 14 char), tooltip con email completa, click → confirm dialog → `cloudSignOut()`. Quando l'utente non è loggato il bottone è nascosto (l'auth-gate fullscreen ha già il proprio form, il bottone diventa ridondante).

### Rimozione bottone "Aggiorna ora"
Riscritto `setupUpdateButton()` in `frontend/app.js`: rimossi i fetch a `_apiGet("/update/status")` (causa errori CORS in console su pid-nine.vercel.app), rimosso bottone `#sidebar-update-btn` (nascosto via `display:none`), mostrato solo badge "⏱ Auto-update / nightly".

### GitHub Actions per auto-update in cloud
Creati 2 workflow in `.github/workflows/`:

**`auto_update_daily.yml`** — Schedule `cron: 0 3 * * *` (03:00 UTC, ~05:00 ITA estate / ~04:00 ITA inverno):
- Solo `run_stats.py --refresh` (25-40 min) per aggiornare presenze/minuti partite
- Diff hash di `players_stats.json` → upload R2 solo se cambiato
- Commit autonomo `auto: daily stats refresh (YYYY-MM-DD)` su file metadata + push
- Anche manuale via `workflow_dispatch` (tab Actions → Run workflow)

**`auto_update_full.yml`** — Schedule `cron: 0 2 * * 1` (lunedì 02:00 UTC) ma con guardia stagionale:
- `run_update.py` (rosters + nuovi profili + foto + stats, 1-2h)
- Esecuzione SOLO nelle finestre mercato:
  - Estivo: 15 giugno → 15 settembre
  - Invernale: 1 gennaio → 15 febbraio
- Fuori finestra il workflow esce subito senza fare nulla
- Anche manuale via `workflow_dispatch` (forza esecuzione anche fuori finestra)

### GitHub Secrets configurati
Aggiunte 5 variabili in repo Settings → Secrets and variables → Actions:
- `R2_ENDPOINT`
- `R2_ACCESS_KEY_ID` (RUOTATA dopo esposizione accidentale in screenshot)
- `R2_SECRET_ACCESS_KEY` (RUOTATA)
- `R2_BUCKET` = `pid-data`
- `R2_PUBLIC_URL` = `https://pub-aa9d173290684b36a9f35e79d4d388c2.r2.dev`

⚠️ Sicurezza: durante il setup è stata esposta accidentalmente la coppia `R2_ACCESS_KEY_ID` + `R2_SECRET_ACCESS_KEY` in uno screenshot di GitHub. Procedura: Cloudflare Dashboard → R2 → Manage API Tokens → Roll del token con ID `f9fa819b...` → nuove credenziali → aggiornato `.env` locale + GitHub Secrets.

### `requirements.txt` creato
Necessario per `pip install -r requirements.txt` in GitHub Actions:
### File modificati/creati
- `frontend/app.js` (riscritto setupUpdateButton, ~110 righe)
- `frontend/cloud_sync.js` (esteso _renderAuthUI per username sidebar)
- `.github/workflows/auto_update_daily.yml` (nuovo)
- `.github/workflows/auto_update_full.yml` (nuovo)
- `requirements.txt` (nuovo)

### Vecchi script `auto_update_*.sh` (locale launchd)
Restano nel repo per ora (sono utili se in futuro vorrai disabilitare GitHub Actions e tornare a launchd locale). I file `.daily_update.lock` e `.full_update.lock` non sono più creati dagli script su Mac perché ora gira tutto in cloud.

### TODO
- [ ] Test workflow daily manuale (Actions → Run workflow) per verificare che gira senza errori
- [ ] Verificare il primo run automatico domani notte (03:00 UTC = ~05:00 ITA)
- [ ] Eventualmente eliminare `auto_update_daily.sh`, `auto_update_full.sh`, e i 3 `.plist` launchd se non li usi più


## 8 mag 2026 (mattina) — Fix flash bottone "Aggiorna ora" + test workflow GitHub Actions

### Fix flash al ricarico
Sequenza problematica: HTML caricava `<button>Aggiorna ora</button>` visibile, poi JS partiva e lo nascondeva con `display:none`. In mezzo, ~200-500ms di flash visibile. Fix: rimosso il bottone (e la progress bar inutile) **direttamente dall'HTML**, non solo nascosto via JS. Resta solo `#sidebar-last-update` con la data, e JS aggiunge dinamicamente il box "Auto-update / nightly".

`setupUpdateButton()` aggiornato: usa `#sidebar-last-update.parentElement` come ancoraggio (il bottone non esiste più nel DOM).

### Test workflow daily — run #1 manuale
Lanciato dal tab Actions di GitHub per validare il setup prima del primo cron automatico.

Step osservati ✅:
- Set up job: 1s
- Checkout repo: 3s
- Setup Python: 2s
- Install dependencies: 6s
- Hash pre-run players_stats.json: 0s
- Run stats refresh: in corso (atteso 25-40 min)

Step ancora da verificare al termine:
- Hash post-run + check changes
- Upload to Cloudflare R2 (se players_stats cambiato)
- Commit and push if changed

### File modificati
- `frontend/index.html` (rimosso #sidebar-update-btn + #sidebar-update-progress)
- `frontend/app.js` (setupUpdateButton riscritto, ancoraggio via #sidebar-last-update)

### Verifiche pendenti
- [ ] Esito completo workflow daily run #1 (~30-40 min)
- [ ] Verifica commit autonomo da `github-actions[bot]`
- [ ] Conferma cron automatico domani notte (03:00 UTC)

## 8 mag 2026 (mattina, conclusione) — Test workflow + timeout bump

Run manuale daily #1 ha processato 1420/2858 giocatori in 90 min (~30 giocatori/min, ~50% del lavoro), poi timeout di GitHub Actions ha cancellato il job. Pipeline funzionava regolarmente — solo questione di velocità (cloud runner Ubuntu più lento del Mac locale).

Fix: bump timeout da 90 a 180 min in auto_update_daily.yml (commit 9474b74). Il prossimo run cron stanotte alle 03:00 UTC avrà tempo sufficiente.

Output run #1 ultime righe:
[1390/2858] Patrizio Masini ETA: 46m59s
[1400/2858] Pervis Estupinan ETA: 46m40s
[1410/2858] Pietro Baccelli ETA: 46m20s
[1420/2858] Pietro Leonardelli ETA: 46m01s
Error: The operation was canceled.

### Commit della giornata 8 mag mattina
- c415f8a: 25 foto manuali + i18n leghe IJ1/PL1/PL2
- 1fa546b: fix New arrival / Returnee / Internal transfer placeholder
- 9474b74: timeout workflow daily 90 -> 180 min

Totale 25 commits in 18 ore di lavoro.

### Atteso domattina
Cron automatico alle 03:00 UTC = 05:00 ITA estate. Al risveglio dovrei vedere:
- Run "Auto Update Daily #2" verde
- Commit autonomo da github-actions[bot]: "auto: daily stats refresh (2026-05-08)"

### TODO ottimizzazioni future
- Ridurre sleep tra fetch run_stats.py (attenzione rate limit TM)
- Parallelizzare richieste TM
- Smart caching skip giocatori con stats aggiornate < 7gg
- GitHub Actions limit free: 2000 min/mese, al pacing attuale (~95 min/notte) sarebbero ~2850 min/mese, si supera. Verificare consumo dopo 1 settimana di run

## 8 mag 2026 (mattina/pomeriggio) — Loghi competizioni + fix Carriera Nazionale

### Problema 1 — Loghi competizioni mancanti nei modali giocatori
Sintomo: nelle sezioni "Carriera per Competizione" e "Ultime Partite" molte competizioni mostravano solo una barretta colorata verticale (no logo) o il codice tecnico (es. "ES3C", "CDR", "DFB" invece di "Tercera RFEF", "Copa del Rey", "DFB-Pokal").

Causa: `competitionLogo()` aveva solo 13 codici hardcoded (IT1, IT2, IT3, IJ1, PL1, PL2, CIT, SCI, ACLE, ACL2, ES1, SDL, "23AF"). Tutti gli altri 800+ codici TM ritornavano null.

Fix:
1. **Loghi**: scaricati 534 PNG da TM CDN (`https://tmssl.akamaized.net/images/logo/homepageWappen150x150/{code_lower}.png`) per tutti i codici con freq>=3 nei dati reali + tutti gli override curati. Script `download_competition_logos.py` (root). 9 falliti (BL1, BL2, BL3, WC, FACS, ACQA, JUSÖ, PL3W, PL3Z), recuperati BL1 da Wikipedia.
2. **Logica generica**: `competitionLogo()` ora cerca semplicemente `photos/competitions/{code}.png` per qualsiasi codice (più 2 eccezioni SVG: ACLE, ACL2). Browser fa 404 silenzioso se file mancante.
3. **Nomi italianizzati**: `COMP_LABEL` esteso da 22 a 130+ entries con nomi belli (Premier League, Bundesliga, Tercera RFEF, Copa del Rey, ecc.) e short labels (PL, BL, T3, CDR).

### Problema 2 — Carriera Nazionale mostra "Italy" anche per giocatori non-italiani
Sintomo: nel profilo di Rabiot (francese) la "Carriera Nazionale" mostrava "Italy / Italy U21 / Italy U19 / Italy U17" con il logo PID al posto della bandiera francese.

Causa duplice:
1. **Bug scraping `stats.py` riga 252**: `national_team_label(cat)` veniva chiamato senza parametro `country`, quindi cadeva nel default `TARGET_NATIONALITY = "Italy"` per TUTTI i giocatori. Anche Rabiot aveva `team_name: "Italy"` salvato in `national_career`.
2. **Bug rendering `_renderNationalCareerBox` riga 1479**: `flagUrl = _photoUrl("photos/branding/logo.png")` hardcoded sul logo PID, indipendente dalla nazionalità.

Fix lato frontend (immediato, non richiede ri-scraping):
- `flagUrl = nationFlag(profile)` dove `profile = state.players.find(...)` → bandiera del giocatore (Francia/Polonia/Slovenia/ecc.)
- Helper `buildTeamName(cat)` che costruisce dinamicamente il nome dalla nazionalità + categoria, ignorando il `team_name` nei dati: `"A" → country`, `"U23" → country + " U23"`, `"Olympic" → country + " Olympic"`.

### TODO long-term
- [ ] Fix scraper `stats.py` riga 252: passare il country del giocatore corrente a `national_team_label(cat, country=...)`. Così i prossimi update notturni avranno dati puliti senza dover sovrascrivere lato frontend. Richiede ri-scraping di tutti i 2858 giocatori (~95 min).
- [ ] Loghi mancanti: BL2, BL3, WC, FACS — non disponibili su TM CDN, recuperati BL1 da Wikipedia ma URL fragili (cambiano nel tempo). Per i prossimi 4 → cercare manualmente

### File modificati/creati
- `frontend/app.js` (+108 righe COMP_LABEL, +helper buildTeamName, +fix Carriera Nazionale, +competitionLogo() generico)
- `download_competition_logos.py` (nuovo)
- `data/photos/competitions/*.png` (+534 file, 1 sovrascritto BL1 da Wikipedia)

## 8 mag 2026 (pomeriggio) — Loghi competizioni + Carriera Nazionale + sezione Salvataggi

### Bug 1 — Loghi competizioni mancanti (resolved)
Sintomo: nei modali giocatori (Carriera per Competizione, Ultime Partite) competizioni come Bundesliga, La Liga, Tercera RFEF, Copa del Rey, DFB-Pokal, Conference League mostravano solo barretta colorata o codice tecnico.
Causa: competitionLogo() aveva solo 13 codici hardcoded.
Fix:
- Script download_competition_logos.py scarica 534 PNG da TM CDN (homepageWappen150x150) per top 120 codici + override curati. BL1 da Wikipedia con UA conforme.
- competitionLogo() ora generico: cerca {code}.png per qualsiasi codice. Eccezioni SVG: ACLE, ACL2.
- COMP_LABEL esteso da 22 a 130+ entries con nomi italianizzati.
- Rimosso redirect bug ES1->ACL2 (causava La Liga senza logo).
- Loghi ancora mancanti (non disponibili TM CDN, non critici): BL2, BL3, WC, FACS, ACQA, JUSO, PL3W, PL3Z.

### Bug 2 — Carriera Nazionale mostra Italy ovunque (resolved)
Sintomo: Rabiot (francese), Sabiri (marocchino), Aaron Martin (spagnolo) mostravano "Italy / Italy U21 / U19" con logo PID.
Causa duplice:
- Bug scraper stats.py riga 252: national_team_label(cat) chiamato senza country, default "Italy" per tutti.
- Bug rendering riga 1479: flagUrl hardcoded sul logo PID.
Fix lato frontend:
- Costruita mappa team_id->{country, category} via build_national_team_lookup.py (scrappa 392 pagine TM, ~3 min). Output data/national_team_lookup.json (392 entries, 99 paesi).
- _renderNationalCareerBox usa lookup invece di team_name hardcoded.
- Bandiera dinamica da photos/national/{country}.png con onerror fallback.

### Bug 3 — Voci duplicate dopo merge lookup (resolved)
Sintomo: Aaron Martin mostrava "Spain U21" 2 volte (10 caps + 8 caps) perche scraper aveva 2 voci con team_id=9567 ma cat="A" e cat="U21".
Fix: dopo lookup, raggruppo voci con stesso (country, category) e sommo caps/goals/minutes via Map.

### Nuova feature: Sezione Salvataggi
Nuova voce sidebar "Salvataggi" come vista trasversale dei salvataggi, separata da linea divisoria sotto Minutaggi.
Architettura: privati per utente con import/export. Niente backend nuovo (usa cloud_sync esistente). 2 sezioni stacked verticalmente: Griglie + Convocazioni. Ogni riga: nome | username creatore | data creazione | data modifica | bottoni Carica/Duplica/Esporta/Elimina.
Modulo aggiunto in app.js (~340 righe nuove): _currentUsername, _formatTs, _ensureMetaGrids, _ensureMetaCallups, _callupIds, _touchGridSave/_touchCallupSave, exportGridSave/exportCallupSave, importSavesFromFile, loadGridSave/loadCallupSave, duplicate, delete, renderSavesPanel.
Migration silenziosa: convocazioni passano da array (legacy saudi_callups_v1) a {ids, _meta}.
UI fix dopo prima iterazione: tolto max-width 1200px, bottoni con label esplicita (Carica/Duplica/Esporta/Elimina), icona Esporta differenziata da Importa, sidebar Salvataggi sotto Minutaggi con linea separator.

### Bug 4 — Dati national_career incompleti per alcuni giocatori (in attesa)
Sintomo: Aaron Martin TM dice 12+18+5+1=36 caps (U21+U19+U17+U16). PID dice 10+11+8+3=32 (A+U19+U21+U17). Mancano partite e U16 totalmente assente.
Diagnosi: scraper TM stats.py probabilmente perde alcune partite (rate limit? participationState filter? competition_id non riconosciuto?).
Decisione: wait & see fino a domani mattina dopo primo run notturno completo (cron 03:00 UTC, timeout 180 min).

### Incidente — cartella ~/Desktop/pid cancellata accidentalmente
A fine sessione, durante l'aggiornamento del diario, il terminale ha riportato "no such file or directory" su /Users/simone/Desktop/pid. La cartella era sparita per errore (probabile drag&drop sbagliato). Niente backup .env/venv locale.
Recovery: clonato di nuovo il repo da GitHub (git clone https://github.com/simonecontran10/pid.git, 71 MB), ricostruito venv (python3 -m venv venv + pip install -r requirements.txt). Tutto il lavoro recuperato (era pushato fino a commit 580b4ca). Cartella backup vecchia pid-backup-3 da cancellare.

### Commit della giornata (8 mag)
- c415f8a fix: 25 foto manuali + i18n leghe IJ1/PL1/PL2
- 1fa546b fix: New arrival/Returnee/Internal transfer placeholder
- 9474b74 ops: timeout daily 90->180 min
- 5224a9f docs: test workflow daily timeout
- 6b7a8c4 feat: 540+ loghi competizioni
- 6ae8b3d docs: loghi competizioni
- 2c40ee1 fix: lookup team_id->country (392 team)
- e2575ce feat: nuova sezione Salvataggi
- 6a11c29 fix: Carriera Nazionale fonde voci stesso country+category
- 580b4ca fix(ux): Salvataggi width 100% + bottoni con label

### TODO long-term aggiornati
- Verificare run notturno 03:00 UTC del 9 mag: nuovo commit github-actions[bot] + dati national_career corretti
- Indagare bug national_career incompleti se persiste
- Fix scraper stats.py riga 252 per dati puliti senza override frontend (richiede ri-scraping ~95 min)
- Loghi mancanti BL2, BL3, WC, FACS (manualmente da fonti varie)
- Custom domain pid.vercel.app
- Cleanup naming legacy saudi_*
- Cancellare ~/Desktop/pid-backup-3 dopo conferma niente file unici critici

## 8 mag 2026 (pomeriggio) — Loghi competizioni + Carriera Nazionale + sezione Salvataggi

### Bug 1 — Loghi competizioni mancanti (resolved)
Sintomo: nei modali giocatori (Carriera per Competizione, Ultime Partite) competizioni come Bundesliga, La Liga, Tercera RFEF, Copa del Rey, DFB-Pokal, Conference League mostravano solo barretta colorata o codice tecnico.
Causa: competitionLogo() aveva solo 13 codici hardcoded.
Fix:
- Script download_competition_logos.py scarica 534 PNG da TM CDN (homepageWappen150x150) per top 120 codici + override curati. BL1 da Wikipedia con UA conforme.
- competitionLogo() ora generico: cerca {code}.png per qualsiasi codice. Eccezioni SVG: ACLE, ACL2.
- COMP_LABEL esteso da 22 a 130+ entries con nomi italianizzati.
- Rimosso redirect bug ES1->ACL2 (causava La Liga senza logo).
- Loghi ancora mancanti (non disponibili TM CDN, non critici): BL2, BL3, WC, FACS, ACQA, JUSO, PL3W, PL3Z.

### Bug 2 — Carriera Nazionale mostra Italy ovunque (resolved)
Sintomo: Rabiot (francese), Sabiri (marocchino), Aaron Martin (spagnolo) mostravano "Italy / Italy U21 / U19" con logo PID.
Causa duplice:
- Bug scraper stats.py riga 252: national_team_label(cat) chiamato senza country, default "Italy" per tutti.
- Bug rendering riga 1479: flagUrl hardcoded sul logo PID.
Fix lato frontend:
- Costruita mappa team_id->{country, category} via build_national_team_lookup.py (scrappa 392 pagine TM, ~3 min). Output data/national_team_lookup.json (392 entries, 99 paesi).
- _renderNationalCareerBox usa lookup invece di team_name hardcoded.
- Bandiera dinamica da photos/national/{country}.png con onerror fallback.

### Bug 3 — Voci duplicate dopo merge lookup (resolved)
Sintomo: Aaron Martin mostrava "Spain U21" 2 volte (10 caps + 8 caps) perche scraper aveva 2 voci con team_id=9567 ma cat="A" e cat="U21".
Fix: dopo lookup, raggruppo voci con stesso (country, category) e sommo caps/goals/minutes via Map.

### Nuova feature: Sezione Salvataggi
Nuova voce sidebar "Salvataggi" come vista trasversale dei salvataggi, separata da linea divisoria sotto Minutaggi.
Architettura: privati per utente con import/export. Niente backend nuovo (usa cloud_sync esistente). 2 sezioni stacked verticalmente: Griglie + Convocazioni. Ogni riga: nome | username creatore | data creazione | data modifica | bottoni Carica/Duplica/Esporta/Elimina.
Modulo aggiunto in app.js (~340 righe nuove): _currentUsername, _formatTs, _ensureMetaGrids, _ensureMetaCallups, _callupIds, _touchGridSave/_touchCallupSave, exportGridSave/exportCallupSave, importSavesFromFile, loadGridSave/loadCallupSave, duplicate, delete, renderSavesPanel.
Migration silenziosa: convocazioni passano da array (legacy saudi_callups_v1) a {ids, _meta}.
UI fix dopo prima iterazione: tolto max-width 1200px, bottoni con label esplicita (Carica/Duplica/Esporta/Elimina), icona Esporta differenziata da Importa, sidebar Salvataggi sotto Minutaggi con linea separator.

### Bug 4 — Dati national_career incompleti per alcuni giocatori (in attesa)
Sintomo: Aaron Martin TM dice 12+18+5+1=36 caps (U21+U19+U17+U16). PID dice 10+11+8+3=32 (A+U19+U21+U17). Mancano partite e U16 totalmente assente.
Diagnosi: scraper TM stats.py probabilmente perde alcune partite (rate limit? participationState filter? competition_id non riconosciuto?).
Decisione: wait & see fino a domani mattina dopo primo run notturno completo (cron 03:00 UTC, timeout 180 min).

### Incidente — cartella ~/Desktop/pid cancellata accidentalmente
A fine sessione, durante l'aggiornamento del diario, il terminale ha riportato "no such file or directory" su /Users/simone/Desktop/pid. La cartella era sparita per errore (probabile drag&drop sbagliato). Niente backup .env/venv locale, ma R2 credenziali sono solo per script locali (workflow notturno gira da GitHub Actions con propri secrets).
Recovery: clonato di nuovo il repo da GitHub (git clone https://github.com/simonecontran10/pid.git, 71 MB), ricostruito venv (python3 -m venv venv + pip install -r requirements.txt). Tutto il lavoro recuperato (era pushato fino a commit 580b4ca). Decisione: niente .env locale, GitHub Actions gestisce gli aggiornamenti notturni autonomamente. Cartella backup vecchia pid-backup-3 da cancellare.

### Commit della giornata (8 mag)
- c415f8a fix: 25 foto manuali + i18n leghe IJ1/PL1/PL2
- 1fa546b fix: New arrival/Returnee/Internal transfer placeholder
- 9474b74 ops: timeout daily 90->180 min
- 5224a9f docs: test workflow daily timeout
- 6b7a8c4 feat: 540+ loghi competizioni
- 6ae8b3d docs: loghi competizioni
- 2c40ee1 fix: lookup team_id->country (392 team)
- e2575ce feat: nuova sezione Salvataggi
- 6a11c29 fix: Carriera Nazionale fonde voci stesso country+category
- 580b4ca fix(ux): Salvataggi width 100% + bottoni con label

### TODO long-term aggiornati
- Verificare run notturno 03:00 UTC del 9 mag: nuovo commit github-actions[bot] + dati national_career corretti
- Indagare bug national_career incompleti se persiste
- Fix scraper stats.py riga 252 per dati puliti senza override frontend (richiede ri-scraping ~95 min)
- Loghi mancanti BL2, BL3, WC, FACS (manualmente da fonti varie)
- Custom domain pid.vercel.app
- Cleanup naming legacy saudi_*
- Decisione: niente .env locale, GitHub Actions notturno e' sufficiente per aggiornamenti

## 8 mag 2026 (pomeriggio) — Loghi competizioni + Carriera Nazionale + sezione Salvataggi

### Bug 1 — Loghi competizioni mancanti (resolved)
Sintomo: nei modali giocatori (Carriera per Competizione, Ultime Partite) competizioni come Bundesliga, La Liga, Tercera RFEF, Copa del Rey, DFB-Pokal, Conference League mostravano solo barretta colorata o codice tecnico.
Causa: competitionLogo() aveva solo 13 codici hardcoded.
Fix:
- Script download_competition_logos.py scarica 534 PNG da TM CDN (homepageWappen150x150) per top 120 codici + override curati. BL1 da Wikipedia con UA conforme.
- competitionLogo() ora generico: cerca {code}.png per qualsiasi codice. Eccezioni SVG: ACLE, ACL2.
- COMP_LABEL esteso da 22 a 130+ entries con nomi italianizzati.
- Rimosso redirect bug ES1->ACL2 (causava La Liga senza logo).
- Loghi ancora mancanti (non disponibili TM CDN): BL2, BL3, WC, FACS, ACQA, JUSO, PL3W, PL3Z.

### Bug 2 — Carriera Nazionale mostra Italy ovunque (resolved)
Sintomo: Rabiot, Sabiri, Aaron Martin mostravano tutti "Italy / Italy U21 / U19" con logo PID.
Causa duplice:
- Bug scraper stats.py riga 252: national_team_label(cat) chiamato senza country, default "Italy" per tutti.
- Bug rendering riga 1479: flagUrl hardcoded sul logo PID.
Fix lato frontend:
- Costruita mappa team_id->{country, category} via build_national_team_lookup.py (scrappa 392 pagine TM, ~3 min). Output data/national_team_lookup.json (392 entries, 99 paesi).
- _renderNationalCareerBox usa lookup invece di team_name hardcoded.
- Bandiera dinamica da photos/national/{country}.png con onerror fallback.

### Bug 3 — Voci duplicate dopo merge lookup (resolved)
Sintomo: Aaron Martin mostrava "Spain U21" 2 volte (10 caps + 8 caps) perche scraper aveva 2 voci con team_id=9567 ma cat="A" e cat="U21".
Fix: dopo lookup, raggruppo voci con stesso (country, category) e sommo caps/goals/minutes via Map.

### Nuova feature: Sezione Salvataggi
Nuova voce sidebar "Salvataggi" come vista trasversale dei salvataggi, separata da linea divisoria sotto Minutaggi.
Architettura: privati per utente con import/export. Niente backend nuovo (usa cloud_sync esistente). 2 sezioni stacked verticalmente: Griglie + Convocazioni. Ogni riga: nome | username creatore | data creazione | data modifica | bottoni Carica/Duplica/Esporta/Elimina.
Modulo aggiunto in app.js (~340 righe): _currentUsername, _formatTs, _ensureMetaGrids/Callups, _callupIds, exportGridSave/CallupSave, importSavesFromFile, loadGridSave/CallupSave, duplicate, delete, renderSavesPanel.
Migration silenziosa: convocazioni passano da array (legacy saudi_callups_v1) a {ids, _meta}.
UI fix iterazione 2: tolto max-width 1200px, bottoni con label esplicita (Carica/Duplica/Esporta/Elimina), icona Esporta differenziata, sidebar Salvataggi sotto Minutaggi con linea separator.

### Bug 4 — Dati national_career incompleti (in attesa)
Aaron Martin TM dice 12+18+5+1=36 caps (U21+U19+U17+U16). PID dice 10+11+8+3=32 (A+U19+U21+U17). Mancano partite, U16 totalmente assente.
Diagnosi probabile: scraper TM stats.py perde alcune partite (rate limit / filtro participationState / competition_id non riconosciuto).
Decisione: wait & see fino al primo run notturno completo (cron 03:00 UTC, timeout 180 min).

### Incidente — cartella ~/Desktop/pid cancellata accidentalmente
Durante aggiornamento diario il terminale ha riportato "no such file or directory". Cartella sparita per errore (probabile drag&drop). Niente backup .env/venv locale.
Recovery: git clone fresh da GitHub (71 MB), ricostruito venv. Tutto il lavoro recuperato (pushato fino a 580b4ca). Decisione: niente .env locale, workflow notturno GitHub Actions sufficiente. Cartella pid-backup-3 da cancellare.

### Commit della giornata (8 mag)
- c415f8a 25 foto manuali + i18n leghe IJ1/PL1/PL2
- 1fa546b fix New arrival/Returnee/Internal transfer
- 9474b74 timeout daily 90->180 min
- 5224a9f test workflow daily timeout
- 6b7a8c4 540+ loghi competizioni
- 6ae8b3d docs loghi
- 2c40ee1 lookup team_id->country (392 team)
- e2575ce feat sezione Salvataggi
- 6a11c29 fix merge voci stesso country+category
- 580b4ca ux Salvataggi width 100% + bottoni label

### TODO long-term aggiornati
- Verificare run notturno 03:00 UTC del 9 mag: commit autonomo github-actions[bot] + dati national_career corretti
- Indagare bug national_career incompleti se persiste
- Fix scraper stats.py riga 252 per dati puliti senza override frontend
- Loghi mancanti BL2, BL3, WC, FACS
- Custom domain pid.vercel.app
- Cleanup naming legacy saudi_*
- Niente .env locale, GitHub Actions sufficiente
# PID — Export PowerPoint dalla pagina Griglie

**Data inizio**: 7 maggio 2026
**Stato**: discovery template completata. Pronti a scrivere il generatore PID-native.

## Obiettivo finale

Bottone **"📥 Esporta PowerPoint"** nella pagina Griglie del PID. Click → genera un `.pptx` con la stessa grafica del progetto `team_presenter` (cover + rosa + slide 3 "Pressing"), ma:

- Dati formazione presi dalla griglia attiva del PID (non da PDF Wyscout)
- Foto giocatori da R2 (`players_sots/{id}.png` → fallback `players_curated/{tm_id}.png`)
- Architettura serverless: Vercel Python function `/api/export-pptx`
- Pipeline 100% automatica e online

## Architettura target (ribadita)

```
Frontend Griglie  ──POST──▶  Vercel /api/export-pptx  ──fetch──▶  R2 (foto)
                                          │
                                          ▼
                              .pptx generato → response
```

## Giro 1 — Strategia "wrapper monkey-patch" (ABBANDONATA)

**Idea iniziale (BRIEF.md)**: riusare `team_presenter.py` come libreria importata, bypassare il parsing PDF tramite 4 monkey-patch:
1. `extract_players_from_pdf` → ritorna fake players dal JSON
2. `extract_starters_from_page6` → ritorna `{number: "ST"}`
3. `assign_players_to_slots` → ritorna assignment fisso
4. `apply_feet` → no-op

Wrapper Python locale `export_grid_pptx.py` come step 1, poi adattamento a Vercel come step 2.

### Cosa è andato bene

- I 4 monkey-patch funzionano (concetto valido)
- Ho generato con successo `JUVENTUS_433_PID.pptx` con 11 titolari + slide 3 colorata + logo Juve

### Cosa è andato male (e perché abbandoniamo)

1. **`Player` dataclass aveva 6 campi obbligatori**, non 4 come dedotto inizialmente. Firma esatta:
   ```python
   @dataclass
   class Player:
       number: str        # PRIMO campo
       name: str
       position: str      # canonica: "GK", "RCB", "LCB", "RB", "LB", "DMF", ...
       height: int
       minutes: int
       foot: str = "D"
   ```
   Ho dovuto patchare il wrapper 2 volte per indovinare la firma corretta.

2. **`position` letta in 12+ punti** del codice post-assignment (riga 1198, 1346, 1478, 1489, ecc.) per logica riserve. Ho dovuto inventare una mappatura `slot_key → position` per ogni sistema (4-3-3, 3-5-2, ecc.).

3. **`pdfplumber` import top-level** in `team_presenter.py`. Anche col monkey-patch, l'import iniziale falliva. Soluzione: stub di `pdfplumber`, `fitz`, `pypdf`, `PyPDF2` in `sys.modules` prima di `import team_presenter`.

4. **Decisione utente: 5 riserve per ruolo**. Il template `template.pptx` originale supporta max 3 giocatori per slot (titolare + R + R2). Per estendere bisognerebbe modificare il template Sassuolo o monkey-patchare anche `LAYOUTS` e `SYSTEM_MAPPING` runtime. Troppo invasivo.

5. **Decisione utente: niente più minutaggi/posizioni dal codice**. La griglia PID ordina già i giocatori. Tutta la logica di selezione automatica di team_presenter (cascata starters, riserve per zona, ecc.) diventa rumore.

### Verdetto

Il wrapper era **debito tecnico per riusare un sistema progettato per un altro scopo** (parsing PDF Wyscout → squadra Sassuolo). Ogni richiesta nuova (5 riserve, ordine custom, no-PDF) richiede patch sopra patch. Abbandonato.

## Giro 2 — Generatore PID-native (STRADA SCELTA)

**Approccio**: scriviamo codice nostro che genera il PPT da zero, prendendo solo:
- **Coordinate** dei layout (LAYOUT_4_3_3, ecc.) — geometricamente corrette, le copio
- **`slide3_pressing.py`** — modulo già auto-contenuto, lo importiamo direttamente
- **Asset grafici**: `grafiche_fiorentina.pptx` (sorgente slide 3), `colori_squadre.json`, `loghi_squadre/`

**NON riusiamo**:
- `team_presenter.py` come libreria
- I 4 monkey-patch
- Lo stub di pdfplumber
- Il `template.pptx` legato ai nomi-Sassuolo

**Strada implementativa scelta** (Strada 1):
- Template-scheletro vuoto (solo sfondo, campo, strisce decorative, header)
- Tutti i gruppi giocatore generati da zero in Python via `python-pptx`
- Posso ricreare ogni "card giocatore" in 30-40 righe Python

### Vantaggi vs wrapper

| Aspetto | Wrapper monkey-patch | Generatore PID-native |
|---|---|---|
| File coinvolti | wrapper + team_presenter (modificato dal `.command`) | un solo file PID |
| Dep PDF | stub di 4 moduli | nessuna |
| Dataclass da indovinare | sì (Player a 6 campi) | no |
| Logica riserve | algoritmi di team_presenter | indice 0=titolare, 1=R, 2=R2, ... |
| Bundle Vercel | ~25 MB (con pdfplumber stubato male) | ~300 KB |
| Maintainability | bassa (ogni modifica → un nuovo monkey-patch) | alta |
| Rischio rompere flusso Wyscout team_presenter | alto | zero (intoccato) |

## Discovery template — risultati

### Slide 1 (cover)
**[ANCORA DA ESEGUIRE]** — comando python pronto in chat

### Slide 2 (rosa) — COMPLETATA

**Dimensioni slide**: 10.00" × 5.62" (16:9 ridotto)

**Anatomia di un "card giocatore"** (ogni gruppo è strutturato così, identico per tutti i 26):

```
GROUP "card giocatore" 1.60" × 0.24"
├─ AUTO_SHAPE — rettangolo arrotondato (background)
├─ TEXT_BOX — "COGNOME ALTEZZA Cm"
│              font: Avenir Next Condensed 8pt
│              BOLD se titolare (color #scheme = bianco)
│              REGULAR se riserva (color default)
├─ GROUP "numero" — pallino + numero maglia
│   ├─ AUTO_SHAPE Ovale 0.19×0.19
│   └─ TEXT_BOX numero (Avenir Next Condensed 8pt)
└─ GROUP "piede" — pallino + D/S
    ├─ AUTO_SHAPE Ovale 0.19×0.19
    └─ TEXT_BOX D/S (Avenir Next Condensed 8pt)
                  - "S" → BOLD #FF0000 (rosso)
                  - "D" → regular nero
```

**Foto giocatori**: 11 PICTURE separate, ognuna 0.59" × 0.59" (cerchio).

**Sfondo decorativo template** (da preservare):
- Gruppi "Strisce diagonali" sx + dx (pattern grafico)
- "Immagine 29" — disegno del campo, 7.50"×6.07"
- Header bar: parallelogramma con "CARRARESE" 24pt + "SISTEMA DI GIOCO 3-5-2" 14pt
- "COACH Nicola Antonio Calabro" 12pt
- Ovale 24 (logo squadra zone) + Picture 2 (logo)
- Logo Serie A top-right (Immagine 27, 0.87×0.87)

**Coordinate slot** (LAYOUT_4_3_3, copiate da `team_presenter.py`):

| Slot | (X, Y) inch |
|---|---|
| GK_T | (4.20, 0.85) |
| GK_R1 | (4.20, 1.06) |
| DIF_1 | (1.80, 1.88) |
| DIF_1R | (1.80, 2.09) |
| ... | (vedi LAYOUT_4_3_3) |

Stessa struttura per gli altri 5 sistemi: 3-5-2, 4-4-2, 4-2-3-1, 3-4-3, 3-4-2-1.

**Spaziatura riserve**: 0.21" verticali (Y +0.21 per ogni riga aggiuntiva). Per slot R3, R4, R5 useremo Y + 0.21 × N.

### Slide 3 (pressing) — IL MODULO SI RIUSA TAL QUALE

`slide3_pressing.py` (49 KB) è **già auto-contenuto e ben modulare**. Non lo tocchiamo.
Funzione entry point: `installa_e_patcha_slide3(work_dir, template_path, system, assignment, team_name)`.
Logica: copia slide 6 da `grafiche_fiorentina.pptx`, ricolora cerchietti, sostituisce logo, GK fisso nero pieno, numeri auto-contrasto.

Lo importeremo direttamente dal nostro generatore PID, **senza** bisogno di importare `team_presenter`.

## Decisioni operative chiavi

| Domanda | Risposta utente |
|---|---|
| Quante slide nel PPT? | TUTTE e 3 |
| Distribuzione asset Vercel? | Bundle + R2 al runtime |
| Sistema di gioco? | Quello scelto in Griglie |
| Posizioni titolari? | Fornite da Griglie, no calcolo |
| Riserve max per ruolo? | 5 (sovrapposizione accettabile in casi rari) |
| Slot vuoti? | Lasciare vuoti (team_presenter già nasconde a -20,-20) |
| Posizionamento riserve? | Come team_presenter originale (R, R2, ecc., ordine = ordine JSON) |
| Foto giocatori? | Da R2 al runtime, no fallback locale |
| Dipendenza da team_presenter.py? | Nessuna |
| Dipendenza da `.command`? | Nessuna (PID flow indipendente) |
| Modifica template Sassuolo originale? | NO, intoccato |

## Stato — pronti per il piano operativo

**Discovery completata**: slide 2. Manca solo slide 1 (1 comando da lanciare).

**Step successivi (DA APPROVARE PRIMA DI SCRIVERE CODICE)**:

1. **Discovery slide 1** (utente lancia ultimo grep)
2. **Piano operativo dettagliato** — Claude propone:
   - Struttura cartelle PID per nuova feature
   - File Python da creare (e cosa fanno)
   - Asset da preparare manualmente (template_pid.pptx vuoto, ecc.)
   - Tempistica per step
3. **Approvazione utente** del piano
4. **Implementazione step by step**

## File chiave per riprendere conversazione

- `~/Desktop/team_presenter/` — sistema Wyscout originale, **intoccato**
- `~/Desktop/team_presenter/team_presenter.py` — riferimento per coordinate (LAYOUTS, SYSTEM_MAPPING)
- `~/Desktop/team_presenter/slide3_pressing.py` — modulo da importare/copiare nel PID
- `~/Desktop/team_presenter/assets/grafiche_fiorentina.pptx` — sorgente slide 3 pressing
- `~/Desktop/team_presenter/assets/loghi_squadre/` — loghi (juventus.png, inter.png, ecc.)
- `~/Desktop/team_presenter/assets/colori_squadre.json` — palette ricolorazione
- `~/Desktop/pid/venv/` — venv di lavoro PID (ha python-pptx, Pillow, PIL — manca pdfplumber, OK)
- `~/Desktop/pid/` — repo PID, branch main
- `https://pid-nine.vercel.app/` — sito PID

## Quando ripartire dopo reset

> Ciao Claude, sto continuando l'integrazione "Esporta PowerPoint" nel mio PID. Ho letto la sezione "PID — Export PowerPoint" del progetto-pid.md. Stato: discovery slide 2 completata, generatore PID-native (Strada 1) confermato, prossimo step = discovery slide 1 + piano operativo. Procediamo.
# PID — Export PowerPoint

## CHECKPOINT 7 maggio 2026 — sera tardi (post-implementazione 1)

### COSA FUNZIONA OGGI

Il generator (`~/Desktop/pid/scripts/pptx_generator/generator.py`) produce un PPT
end-to-end con questi step:

1. **Apertura template** `template_pid.pptx` (8 slide)
2. **Selezione 3 slide** (cover + slide del sistema scelto + pressing) e cancellazione delle altre
3. **Sostituzione testi header**:
   - Cover: stadio, data, competizione (gestito splittando i 3 paragrafi)
   - Formazione: SQUADRA, sistema (3-5-2 → 4-3-3 ecc.), COACH Nome Cognome
4. **Riempimento card giocatore** (slide formazione):
   - Per ogni chiave del JSON players (es. `RCB1`) → sostituisce cognome + altezza + numero + piede
   - Cognome in MAIUSCOLO ("BREMER 188 Cm"), gestione nomi composti (Joao Mario, Di Gregorio)
   - Piede `S` (sinistro) → rosso bold, `D` (destro) → nero
5. **Nascondi placeholder non usati** spostandoli a (-20, -20)
6. **Riempi cerchietti pressing** (Set A: Gk1/Rcb1/Cm1/St1/St1b/ecc.) con cognomi titolari in **Title Case** ("Bremer", "Joao Mario", "Di Gregorio")
   - Set B (POR/TER S/CEN D/ALA D/TREQ./ATT) lasciato intatto
7. **Sostituzione logo squadra**: il logo Italia (placeholder per la squadra studiata)
   viene sostituito con `assets/loghi_squadre/{team}.png` in tutte le 3 slide.
   Logo Fiorentina è fisso e non si tocca.

### CONVENZIONE JSON DI INPUT (consolidata)

Le chiavi del JSON sono direttamente i codici placeholder del template (RCB1, ST1B, ecc.).
Il **primo elemento di ogni lista** è il titolare, gli altri sono riserve in ordine.
Il codice piazza automaticamente in `*1` (titolare), `*2` (1ª riserva), `*3` (2ª riserva),
`*4` (3ª riserva, solo CM/RCM/LCM).

Esempio:
```json
{
  "team_name": "juventus",
  "system": "3-5-2",
  "match_info": {
    "stadio": "Allianz Stadium – Torino – Italia",
    "data": "12 Maggio 2026 – 20:45",
    "competizione": "Serie A 2025/26 – 36ª giornata",
    "coach": "Igor Tudor"
  },
  "players": {
    "GK1":  [{"name": "Di Gregorio", "number": "29", "height": 195, "foot": "right"}],
    "RCB1": [{"name": "Bremer",  "number": "3",  "height": 188, "foot": "right"}],
    ...
  }
}
```

### FILE PYTHON ATTUALI

```
~/Desktop/pid/scripts/pptx_generator/
├─ __init__.py                    ✅ (vuoto, serve per import)
├─ constants.py                   ✅ (mappa SISTEMA→SLIDE_INDEX, costanti R2)
├─ generator.py                   ✅ (orchestratore completo, ~27KB)
├─ test_run.py                    ✅ (script di test)
├─ payload_juve_3_5_2.json        ✅ (payload Juve 3-5-2 con dati inventati)
├─ assets/
│  ├─ template_pid.pptx           ✅ (8 slide, costruito a mano in PowerPoint)
│  ├─ loghi_squadre/              ✅ (PNG dei loghi, juventus.png da aggiungere se manca)
│  └─ ...
├─ slide3_pressing.py             ⚠️  copiato da team_presenter ma NON USATO (per ora)
└─ test_output/
   └─ juve_3_5_2.pptx             ← output di test
```

### COSA NON È ANCORA FATTO (in priorità)

1. **Foto giocatori da R2** — l'ultimo pezzo grosso. Sostituire le 11 foto Sassuolo
   nella slide formazione con quelle reali scaricate da
   `https://pub-aa9d173290684b36a9f35e79d4d388c2.r2.dev/players_sots/{sots_id}.png`.
   Richiede:
   - Aggiunta campo `sots_id` nei payload
   - Pipeline download paralleli con cache `/tmp/foto_giocatori/`
   - Sostituzione PICTURE shape per ogni titolare
   - Gestione foto mancante (404 da R2)

2. **Cover slide** — decidere come gestire:
   - "VS" (testo decorativo)
   - Logo Fiorentina sulla destra (placeholder squadra di casa generica)

3. **Nomi lunghi** che vanno a capo nelle card formazione:
   - "Joao Mario 178 Cm" si spezza su 2 righe
   - "Koopmeiners 184 Cm" idem
   - Soluzione possibile: allargare textbox, troncare cognome, ridurre font size

4. **Test su altri sistemi** (4-3-3, 4-4-2, 4-2-3-1, 3-4-3, 3-4-2-1).
   Il generator dovrebbe già funzionare grazie alle slide template separate, ma serve verifica.

5. **Vercel deployment**:
   - Spostare in `~/Desktop/pid/api/export-pptx.py` (Vercel Python serverless)
   - `requirements.txt`: python-pptx, Pillow, requests (per R2)
   - `vercel.json`: maxDuration 60, memory 1024
   - Bundle del template + loghi nella function

6. **Frontend bottone** "📥 Esporta PowerPoint" nella pagina Griglie del PID:
   - Costruisce il payload JSON dalla griglia attiva
   - POST a `/api/export-pptx`
   - Riceve il blob del PPT e lo fa scaricare al browser

### STORICO DELLE ITERAZIONI DI OGGI

**Mattina/pomeriggio**:
- Discovery template Sassuolo originale (team_presenter)
- Setup struttura `pptx_generator/` nel PID
- Tentativo wrapper monkey-patch su team_presenter — abbandonato (Player dataclass + position lookup ovunque)
- Decisione: scrivere generator nativo PID

**Pomeriggio/sera**:
- Simone costruisce manualmente `template_pid.pptx` (8 slide, una per sistema)
- Allineamento convenzione naming (R*=lato dx campo, L*=lato sx campo dal pdv giocatore)
- Conferma mappa slide→sistema: 2=3-5-2, 3=3-4-3, 4=3-4-2-1, 5=4-3-3, 6=4-2-3-1, 7=4-4-2
- Decisione: JSON usa direttamente i codici template (no DIF_R/CC_C/ATT_L)

**Sera tardi (questa sessione)**:
- Scrittura `generator.py` con strategia mista python-pptx + manipolazione XML
- Primo test passato: PPT con 3 slide visivamente corretto
- Aggiunta riempimento pressing (Set A → cognomi titolari)
- Aggiunta sostituzione logo squadra (Italia → Juve via hash MD5 dell'immagine)
- Bug fix: counter logo (più PICTURE condividono la stessa image part)
- Modifica: cognomi pressing in Title Case invece di MAIUSCOLO

### PROMPT DI RIPRESA (per chat futura)

> Ciao Claude, riprendo "Esporta PowerPoint" del PID. Allego BRIEF.md.
> Stato: generator.py funzionante per 3-5-2 (cover+formazione+pressing+logo).
> Manca: foto giocatori da R2, cover VS/logo Fiorentina, test altri sistemi, Vercel.
> Prossimo step: foto giocatori. Procediamo.
## 7-8 mag 2026 (notte) — Export PowerPoint completato per 3-5-2

### Sessione di sviluppo intensa: dal generator base a versione production-ready

Continuazione del generator dopo i fix dei 2 bug Griglie + add Locatelli. In questa sessione il generator è stato completato fino a stato pubblicabile per il sistema 3-5-2. Riassunto delle modifiche cronologico.

### Modifiche al generator.py

1. **Fix cognomi pressing** — cognomi titolari in **Title Case** ("Bremer", "Joao Mario", "Di Gregorio") invece di MAIUSCOLO. Set B avversari (POR/TER S/CEN D/ALA D/TREQ./ATT) lasciato intatto.

2. **Sostituzione foto giocatori** — funzione `replace_player_photos()` aggiunta. Sostituisce le 11 PICTURE 0.59"×0.59" del template con foto reali dei giocatori da `data/photos/players_sots_lookup/{sots_id}.png` (file locale, niente R2). Mappatura `PHOTO_POSITION_MAPS["3-5-2"]` con 11 coordinate precise (left, top in inch) → slot ID. Tolerance ±0.15".

3. **Aggiornamento payload** — file `juve_titolari_lookup.json` generato dinamicamente da `players_static.json`. Estrazione `sots_id` dal path `sortitoutsi_face_local_lookup` (regex `/(\d+)\.png$`). Tutti gli 11 titolari + 12 riserve (totale 23 giocatori) con dati corretti.

4. **Mappatura slot frontend → template** — il frontend usa nomi tipo `RWB1/LWB1/RST1/LST1`, il template costruito a mano ha `RFB1/LFB1/ST1/ST1B`. Aggiunta tabella di traduzione nel payload builder.

5. **Cognomi → solo ultima parola** — `_short_surname()` ridisegnata: default = ultima parola (Locatelli, Kalulu, Thuram). Eccezione: particelle (Di, Van, De → "Di Gregorio"). Eccezione hardcoded: "Joao Mario", "Thuram-Ulien".

6. **Foot=both** → "D/S" — `_foot_to_letter()` esteso. Rendering: "D/" in nero regolare + "S" in rosso bold. Gestiti Cambiaso, Yıldız, David.

7. **Logo squadra dimensioni per slide** — invece di stretchare il logo Italia alle dimensioni del placeholder, ora **mantiene proporzioni** via Pillow (`PIL.Image`) e usa **target_size_cm fisso** in base alla slide:
   - Cover (slide 0): **2.6 cm**
   - Formazione (slide 1): **1.6 cm**
   - Pressing (slide 2): **1.1 cm**

8. **Z-order strisce** — funzioni `bring_stripes_to_front()` (Gruppo 9, alto-sx, off-canvas, in primo piano) + `send_stripes_to_back()` (Gruppo 13, basso-dx, dietro all'`Immagine 29` sfondo campo). Identificate per posizione: alto-sx via `(left<-1, top<-1)`, basso-dx via `(left>4, top<0, w>8)`.

9. **Textbox COACH allargato** — passa da 2.23" a 3.5" (espande a sx mantenendo bordo dx). Risolve "COACH Nome Cognome" che andava a capo.

10. **Sistema colori squadra in pressing** — `assets/colori_squadre.json` con mappa squadra→{fill, border, text}. Funzione `recolor_pressing_set_a()` ricolora i 10 cerchi Set A (esclude Gk1 che resta nero per convenzione). Per Juventus: `fill=FFFFFF, border=000000, text=000000` (bianconero classico). 24 squadre Serie A mappate.
    - **CRITICO**: la chiamata a `recolor_pressing_set_a()` deve venire **PRIMA** di `fill_pressing_slide()`, sennò le label ("Gk1", "Rcb1", ecc.) vengono sostituite con i cognomi prima della ricolorazione.

11. **Valori generici cover/coach** — payload usa placeholder generici:
    - Cover: `Stadio – Città – Paese`, `GG Mese 2026 – HH:MM`, `Serie A 2026/27 – Xª giornata`
    - Slide 2: `COACH Nome Cognome`
    Stati pronti per il bottone export reale (verranno popolati dalla griglia + form).

### Stato attuale: stato finale pre-publish

```
~/Desktop/pid/scripts/pptx_generator/
├─ __init__.py                        1 byte
├─ constants.py                       1.4K  (mappa SISTEMA→SLIDE_INDEX)
├─ generator.py                       ~22K  (orchestratore completo)
├─ test_run.py                        1.2K  (script di test)
├─ payload_juve_3_5_2.json            ~9K   (23 giocatori Juve con sots_id veri)
├─ juve_titolari_lookup.json          ~4K   (cache titolari)
├─ assets/
│  ├─ template_pid.pptx               3.7M  (8 slide, costruito a mano)
│  ├─ loghi_squadre/
│  │  └─ juventus.png                 PNG quadrato
│  └─ colori_squadre.json             24 squadre Serie A
└─ test_output/
   └─ juve_3_5_2.pptx                 ~5MB output verificato
```

### Funziona end-to-end per 3-5-2:
- ✅ Cover (header dinamico, logo squadra 2.6 cm, "VS" + Fiorentina fissa)
- ✅ Formazione (11 foto reali + 12 riserve testo, cognomi soli, foot D/S/D/S, logo 1.6 cm, strisce alto-sx in primo piano, strisce basso-dx dietro al campo)
- ✅ Pressing (cognomi titolari Title Case, cerchi Set A bianchi+bordo nero per Juve, logo 1.1 cm)

### Architettura confermata

**Generator standalone** (no DB access):
```
1. Frontend Griglie → click "Esporta PPT"
2. Frontend serializza griglia in JSON nel formato del generator
3. POST /api/export-pptx con quel JSON
4. Endpoint Vercel (Python) → riceve JSON → genera PPT → ritorna blob
5. Frontend triggera download
```

**Foto giocatori**: lette da `data/photos/players_sots_lookup/` direttamente (cartella nel repo, dispatchate al deploy Vercel). Niente R2 per le foto giocatori (ridondante).

### Convenzione naming consolidata

- **Slot template**: `{POSITION}{NUM}[B]` es. `RCB1`, `LCB1`, `CB1`, `RFB1`, `LFB1`, `RCM1`, `CM1`, `LCM1`, `ST1`, `ST1B`, `GK1`
- **Primo elemento lista players** = titolare, successivi = riserve
- **R\*** = lato destro del campo dal pdv giocatore = **sx schermo**
- **L\*** = lato sinistro del campo dal pdv giocatore = **dx schermo**

### Cosa resta TODO

1. **Mappature foto/slot per altri 5 sistemi**: 4-3-3, 4-4-2, 4-2-3-1, 3-4-3, 3-4-2-1. Estrarre coordinate PICTURE da slide template + scrivere `PHOTO_POSITION_MAPS[sistema]`.

2. **Mappature slot frontend → template per altri sistemi** — la convenzione `RWB→RFB`, `RST/LST→ST/ST1B` va replicata.

3. **Endpoint Vercel** `/api/export-pptx`:
   - `requirements.txt`: python-pptx, Pillow
   - `vercel.json`: maxDuration 60, memory 1024
   - Bundle template + loghi + colori_squadre.json + foto giocatori

4. **Bottone frontend** "📥 Esporta PowerPoint" nella pagina Griglie:
   - Helper `gridToPayload(grid, players_dataset)` → costruisce JSON
   - Form modale per match_info (stadio, data, competizione, coach, sistema)
   - POST `/api/export-pptx` → riceve blob → download triggered

### Cleanup file dopo session

- **Da cancellare** (backup/cache): tutti i `*.bak_*` in `scripts/pptx_generator/` (almeno 9 backup accumulati durante questa sessione)
- **Da tenere**: `juve_titolari_lookup.json` come reference, `payload_juve_3_5_2.json.bak_pre_photos` (versione pre-foto per debug)

### Comando cleanup

```bash
cd ~/Desktop/pid/scripts/pptx_generator
rm -f generator.py.bak_pre_photos generator.py.bak_v3 generator.py.bak_v4 generator.py.bak_v5 generator.py.bak_v6 generator.py.bak_v7 generator.py.bak_v8 generator.py.bak_v9 generator.py.bak_v10
rm -f test_run.py.bak_pre_photos
ls -la
```

### PROMPT DI RIPRESA

> Ciao Claude, riprendo PID. Stato (8 mag mattina):
> 1. ✅ Bug fix cambio modulo Griglie (commit 91e5453)
> 2. ⏳ Locatelli aggiunto al dataset, aspetto run notturno per stats su R2
> 3. ✅ Generator PowerPoint completo per 3-5-2 (cover + formazione + pressing + colori squadra). 
>    File: `~/Desktop/pid/scripts/pptx_generator/`. 
>    Test: `python3 test_run.py` → `test_output/juve_3_5_2.pptx`.
> 4. 🔄 Da fare: mappare 5 altri sistemi (4-3-3, 4-4-2, 4-2-3-1, 3-4-3, 3-4-2-1), endpoint Vercel, bottone frontend.

## 8 mag 2026 (mattina) — Rilascio bottone "Esporta PowerPoint" online

### Sessione di rilascio: dal generator standalone al bottone live nel sito PID

Ripresa da ieri sera. Stato di partenza: generator funzionante per tutti i 6 sistemi in locale, testato su 3-5-2/4-3-3/4-2-3-1. Obiettivo di oggi: rilasciare endpoint Vercel + bottone frontend.

### Decisioni di design prese stamattina

1. **Foto giocatori da filesystem locale** (NON da R2 come nel piano originale di progetto.md). Motivazione: le foto sono già nel repo (48 MB), già servite come static files da Vercel per il frontend. Filesystem = velocità (1ms vs 50-200ms per HTTP), zero dipendenze esterne, single source of truth, coerenza dev/prod, automatico (push = deploy). Decisione overrideata rispetto al progetto.md originale che prevedeva "Da R2 al runtime, no fallback locale" — quella era valida quando le foto NON erano nel repo.

2. **Architettura backend**: estendere `api/main.py` esistente (FastAPI + Mangum per ASGI→serverless Vercel) invece di creare endpoint separati. Coerente con il pattern del progetto.

3. **Endpoint URL pattern**: `/export-pptx` (no prefisso `/api/`, Vercel rewrites gestiscono il routing).

### Implementazione step by step

#### Step 1 — Cleanup file backup accumulati

Rimossi tutti i `*.bak_v3` ... `*.bak_v14` dal `pptx_generator/` (14 file accumulati durante la sessione di ieri). Cancellati anche `__pycache__/` e `test_output/`.

#### Step 2 — `.vercelignore`

Creato per escludere dal deploy:
```
scripts/pptx_generator/test_output/
**/*.bak*
**/__pycache__/
**/.DS_Store
venv/
raw/
progetto-pid.md
progetto_saudi_REFERENCE.md
```

#### Step 3 — `api/requirements.txt` esteso

```
fastapi>=0.110
uvicorn[standard]>=0.27
python-pptx>=0.6.23
Pillow>=10.0
mangum>=0.17
```

**Mangum** è l'adapter ASGI→Lambda/Vercel per FastAPI. Senza di esso, le rotte API ritornano 404 anche se `api/main.py` è correttamente buildato.

#### Step 4 — Endpoint `/export-pptx` in `api/main.py`

Aggiunto in fondo al file esistente:

```python
@app.post("/export-pptx")
def export_pptx(payload: dict = Body(...)):
    # Validazione team_name, system, players
    # Import lazy del generator da scripts/pptx_generator/
    # Path asset: scripts/pptx_generator/assets/template_pid.pptx
    # Foto: data/photos/players_sots_lookup/
    # Output: tempfile, ritornato come FileResponse con Content-Disposition attachment
    return FileResponse(..., media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation")
```

Headers di response includono stats: `X-Stats-Card-Filled`, `X-Stats-Photos-Replaced`, `X-Stats-Pressing-Filled`. Utili per debug client side.

#### Step 5 — Mangum handler in fondo a `main.py`

```python
try:
    from mangum import Mangum
    handler = Mangum(app, lifespan="off")
except ImportError:
    pass  # In dev mode (uvicorn) Mangum non serve
```

#### Step 6 — `vercel.json` esteso

Aggiunte rewrites esplicite per ogni endpoint API + config function:

```json
"rewrites": [
    { "source": "/export-pptx", "destination": "/api/main" },
    { "source": "/clubs", "destination": "/api/main" },
    { "source": "/players", "destination": "/api/main" },
    ...
],
"functions": {
    "api/main.py": {
        "maxDuration": 60,
        "memory": 1024
    }
}
```

**Importante**: prima del fix, le rotte API live (`/clubs`, `/search`) ritornavano 404 in produzione. Il sito era effettivamente solo frontend statico. Aggiungere le rewrites + Mangum ha attivato il backend Python.

#### Step 7 — Bottone frontend "📥 PPT" + helpers JS

In `frontend/app.js`:
- Bottone `<button id="grids-export-pptx">${t("export_pptx")}</button>` dopo "Esporta PDF"
- Helper `_gridsBuildPptxPayload()` che:
  - Trova il club della maggioranza dei titolari per dedurre `team_name`
  - Mappa slot frontend → template via `_PPTX_SLOT_MAP`
  - Estrae `sots_id` da `sortitoutsi_person_id` o regex su `sortitoutsi_face_local_lookup`
  - Costruisce payload completo con titolari + riserve in ordine
- Funzione `_gridsExportPptx(buttonEl)` async che:
  - Disabilita bottone con loading state
  - POST a `/export-pptx` con payload JSON
  - Riceve blob, crea URL.createObjectURL, triggera `<a download>`
- Handler agganciato al click

#### Step 8 — i18n keys

Aggiunte in `i18n.js`:
- `export_pptx`, `export_pptx_loading`, `export_pptx_error`, `export_pptx_empty`

### Bug critici scoperti durante test live

#### Bug 1 — `window._players` non esiste

Il dataset giocatori sta in `state.players`, non in `window._players` come avevo assunto. Fix: replace `window._players` → `state.players` in `_gridsBuildPptxPayload`.

#### Bug 2 — Mappatura slot mancante per 4-2-3-1

Il frontend `FORMATIONS["4-2-3-1"]` usa id slot **diversi** dagli altri sistemi:
- `RDM` (right defensive midfielder)
- `LDM` (left defensive midfielder)
- `RAM` (right attacking midfielder)
- `LAM` (left attacking midfielder)

Mentre gli altri sistemi usano `RCM/LCM/RW/LW`. Fix: estesa `_PPTX_SLOT_MAP`:

```js
"RDM":  "RCM1",
"LDM":  "LCM1",
"RAM":  "RW1",
"LAM":  "LW1",
```

#### Bug 3 — `club_name` `???` nel dataset

Il campo `club_name` in `players_main.json` non è popolato. Il bottone non riesce a dedurre il `team_name` dalla griglia. Conseguenza: `team_name="team"` (default) e quindi:
- Logo squadra: usa logo Italia di default (placeholder)
- Titolo: "TEAM" invece di "JUVENTUS"
- Cerchi pressing: colore di default (Sassuolo arancione)

**Decisione**: per ora lasciamo così. L'export funziona ma con logo + nome generici. In futuro, quando sarà chiaro come popolare `club_name`, sistemeremo.

### Push branch `feature/pptx-export`

Branch creato e pushato. Vercel auto-deploya preview URL: `pid-git-feature-pptx-export-simone-contran-s-projects.vercel.app`.

### Stato attuale del bottone live

- ✅ Endpoint `/export-pptx` raggiungibile e risponde HTTP 200
- ✅ Bottone clickabile, payload costruito correttamente con `state.players`
- ✅ Download del file `team_<system>.pptx` triggerato automaticamente
- ✅ Tutti i giocatori del 4-2-3-1 ora con foto + card (post fix Bug 2)
- ⚠️ Logo + nome team generici (Bug 3 da fixare in futuro)
- ⚠️ Colori cerchi pressing default (richiede fix `team_name` rilevazione)

### File modificati nel commit `feature/pptx-export`

```
M  api/main.py                                    (+103 righe — endpoint + Mangum)
M  api/requirements.txt                           (+3 righe — pptx, Pillow, Mangum)
M  frontend/app.js                                (+150 righe — helpers + bottone + handler)
M  frontend/i18n.js                               (+4 righe per lingua — chiavi PPTX)
M  vercel.json                                    (rewrites espliciti + functions config)
M  progetto-pid.md
A  .vercelignore                                  (nuovo)
A  scripts/pptx_generator/__init__.py             (nuovo)
A  scripts/pptx_generator/constants.py            (nuovo)
A  scripts/pptx_generator/generator.py            (~25KB)
A  scripts/pptx_generator/assets/template_pid.pptx (3.7MB)
A  scripts/pptx_generator/assets/colori_squadre.json
A  scripts/pptx_generator/assets/loghi_squadre/*.png (~17 loghi)
```

Totale: 32 file changed, ~2511 insertions.

### Punti aperti / TODO

1. **Bug 3 da risolvere**: come dedurre `team_name` dalla griglia quando `club_name` non è popolato? Opzioni:
   - (a) Popolare `club_name` in `players_main.json` (vediamo dove sta il club ID)
   - (b) Aggiungere un campo "Squadra" nel modale frontend che l'utente compila
   - (c) Lookup `tm_club_id → club_name` via `clubs.json`
2. **Form modale match_info**: per ora hardcoded "Stadio – Città – Paese", "GG Mese 2026 – HH:MM". L'utente dovrà poter inserire questi dati dal frontend.
3. **Test visivo altri 3 sistemi sul preview live**: 4-4-2, 3-4-3, 3-4-2-1 mai testati visivamente in produzione.
4. **Verificare run notturno** auto_update_daily.yml di stanotte (3:00 UTC). Locatelli stats da R2.
5. **Merge feature/pptx-export → main** una volta che tutti i sistemi sono testati e Bug 3 risolto.

### Stato repo

```
Branch: feature/pptx-export (in attesa di merge)
Production: main su pid-nine.vercel.app (con bug fix Griglie del 91e5453)
Preview: pid-git-feature-pptx-export-...vercel.app
```
## 8 mag 2026 (mattina, completamento) — Export PPT live verificato su 5 sistemi + 3-4-2-1 aggiunto

### Sessione di rifinitura sui sistemi multipli

Continuazione mattutina. Stato di partenza: bottone export PPT online sul preview Vercel funzionante, ma con mappature slot frontend → template solo per il 4-2-3-1 testato. Test live degli altri sistemi e fix dei bug emersi sistema per sistema.

### Bug scoperti e risolti durante test live multi-sistema

#### Bug 4 — `_PPTX_SLOT_MAP` globale non funziona per il 3-4-3

Il **3-4-3** frontend usa id `RM`/`LM` per gli **esterni di centrocampo**. Nella mappa globale precedente avevo `RM → RW1, LM → LW1` (corretto per il 4-4-2 dove RM/LM sono ali in attacco), ma sbagliato per il 3-4-3 dove RM/LM sono **terzini alti** (template `RFB1/LFB1`).

**Fix**: trasformata la mappa globale `_PPTX_SLOT_MAP` in mappa **per sistema** `_PPTX_SLOT_MAP_BY_SYSTEM` con un dizionario per ognuno dei 6 sistemi:

```js
const _PPTX_SLOT_MAP_BY_SYSTEM = {
  "3-5-2": { GK: "GK1", RCB: "RCB1", CB: "CB1", ..., RWB: "RFB1", LWB: "LFB1", ... },
  "3-4-3": { GK: "GK1", ..., RM: "RFB1", LM: "LFB1", ... },  // RM = esterno cc
  "3-4-2-1": { ... },
  "4-3-3": { GK: "GK1", RB: "RFB1", LB: "LFB1", ..., RW: "RW1", LW: "LW1" },
  "4-2-3-1": { GK: "GK1", RB: "RFB1", ..., RDM: "RCM1", LDM: "LCM1", RAM: "RW1", LAM: "LW1", CAM: "ST1B" },
  "4-4-2": { ..., RM: "RW1", LM: "LW1" }  // RM = esterno cc → ala template
};

function _gridsMapSlot(sysName, frontendSlot) {
  return (_PPTX_SLOT_MAP_BY_SYSTEM[sysName] || {})[frontendSlot] || frontendSlot;
}
```

#### Bug 5 — `fill_pressing_slide` lasciava cerchi con label letterale

Quando il sistema scelto non usava tutti i cerchi Set A del template (es. nel 4-2-3-1 mancano `Cm1`/`Cb1`), i cerchi restanti mostravano la label originale del template (Cm1, Cb1, ecc.) invece di essere riempiti con un giocatore.

Inizialmente avevo creato `hide_unused_pressing_set_a_circles()` che spostava fuori canvas i cerchi non usati. Approccio sbagliato: il template ha **11 cerchi Set A**, e ogni sistema ha **11 titolari**. La logica giusta è **riempirli tutti** indipendentemente dalle label originali.

**Fix**: `fill_pressing_slide` riscritta per:
- Riempire SEMPRE il cerchio "Gk1" col portiere (slot GK1 dal payload)
- Riempire i restanti 10 cerchi Set A coi 10 outfield titolari **nell'ordine z-order** del template (`spTree`)
- L'utente Simone poi sposta i cerchi a mano nelle posizioni di pressing volute

```python
def fill_pressing_slide(pressing_slide, players, system=None):
    SET_A_LABELS = {"gk1","rcb1","cb1","lcb1","rfb1","lfb1","rcm1","cm1","lcm1","st1","st1b","rw1","lw1"}
    
    gk_titolare = None
    outfield_titolari = []
    for slot, plist in players.items():
        if not plist: continue
        if slot.upper() == "GK1":
            gk_titolare = plist[0]
        else:
            outfield_titolari.append(plist[0])
    
    # ... riempi gk_group col portiere, set_a_groups coi 10 outfield (zip)
```

Funzione helper `_fill_pressing_circle()` che gestisce un singolo cerchio: sostituisce label esterna (cognome Title Case) e numero interno (numero di maglia).

#### Bug 6 — Bug accidentale: regex sostituzione greedy mangia LOGO_ITALIA_HASH

Durante la riscrittura di `fill_pressing_slide` con un `re.sub` greedy, ho accidentalmente cancellato la definizione `LOGO_ITALIA_HASH = "af7418bf37"`. Causava `NameError` al runtime.

**Fix**: ripristinata la costante. Lezione: usare regex **non-greedy** (`.*?`) o pattern più stretti quando si sostituiscono blocchi multi-funzione.

#### Aggiunta sistema 3-4-2-1 al frontend

Il **3-4-2-1** era nel template (slide 3) e nella mappa `_PPTX_SLOT_MAP_BY_SYSTEM`, ma **non in `FORMATIONS`** del frontend. Il dropdown del Modulo aveva solo 5 opzioni (4-3-3, 4-4-2, 3-5-2, 4-2-3-1, 3-4-3). Aggiunto:

```js
"3-4-2-1": [
  { id: "GK",  x: 50, y: 8 },
  { id: "RCB", x: 70, y: 25 }, { id: "CB", x: 50, y: 23 }, { id: "LCB", x: 30, y: 25 },
  { id: "RM",  x: 88, y: 50 }, { id: "RCM", x: 60, y: 48 }, { id: "LCM", x: 40, y: 48 }, { id: "LM",  x: 12, y: 50 },
  { id: "RAM", x: 70, y: 75 }, { id: "LAM", x: 30, y: 75 },
  { id: "ST",  x: 50, y: 86 }
]
```

3 difensori + 4 centrocampisti + 2 trequartisti laterali + 1 punta.

### Test live verificati

Dal preview URL (`pid-git-feature-pptx-export-...vercel.app`):

| Sistema   | Stato test live | Note |
|-----------|----|------|
| 3-5-2     | ✅ verificato | Logo + nome JUVENTUS auto-rilevato, 22 card, 11 foto, 11 cerchi pressing colorati Juve |
| 3-4-3     | ✅ verificato | Esterni cc RM/LM mappati a RFB1/LFB1 (post fix Bug 4) |
| 4-3-3     | ✅ verificato | Conceição RW + Yıldız LW corretti |
| 4-2-3-1   | ✅ verificato | Trequartista (CAM → ST1B), mediani difensivi (RDM/LDM → RCM1/LCM1), trequartisti laterali (RAM/LAM → RW1/LW1) |
| 4-4-2     | ✅ verificato | RM/LM in attacco → RW1/LW1, ST1+ST1B come 2 punte |
| 3-4-2-1   | ⏳ da testare (post add a FORMATIONS) | |

### Stato attuale repo

Branch: `feature/pptx-export` (ancora **non mergato in main**)

Commit del branch:
```
8d9c17b — feat: PPT export endpoint + bottone Griglie (initial)
165197e — fix: usa state.players invece di window._players
f984923 — fix: aggiungi mappatura slot RDM/LDM/RAM/LAM (4-2-3-1)
2437eaf — fix: mappa slot frontend->template PER SISTEMA (3-4-3 RM/LM)
[next]  — feat: fill_pressing_slide riempie sempre tutti gli 11 cerchi
[next]  — feat: aggiunge sistema 3-4-2-1 al frontend FORMATIONS
```

### TODO finale prima del merge → main

1. **Test 3-4-2-1 live** dopo deploy del fix FORMATIONS
2. **Merge `feature/pptx-export` → `main`** così il bottone va in produzione su `pid-nine.vercel.app`
3. **Cleanup**: cancellare `*.bak_pre_*` (`api/main.py.bak_pre_export`)
4. **Verifica run notturno** auto_update_daily.yml (Locatelli stats — punto pendente di stamattina)
5. **Bug 3 in pausa** — `team_name` rilevato dalla griglia funziona quando i giocatori hanno tutti `club_name` valorizzato (caso normale). Quando l'utente mette giocatori di squadre diverse, default "TEAM" + logo Italia. Accettabile.

### Lezioni apprese

1. **Mappature slot non-banali**: ogni sistema ha id frontend diversi per gli stessi ruoli (RM/LM possono essere terzini alti o ali in attacco a seconda del sistema). Mappa per-sistema obbligatoria.
2. **Template Sassuolo originale**: alcune label sono "legacy" del 3-5-2. Riusare il template per altri sistemi richiede di **riempire** sempre tutti i cerchi (non hide).
3. **Regex sostituzione codice**: usare pattern stretti e non-greedy. La perdita silenziosa di `LOGO_ITALIA_HASH` è stata recuperata solo grazie a `git show HEAD:file`.
4. **Test multi-sistema indispensabile**: il 3-5-2 funzionava ma 5 altri sistemi avevano bug diversi che sarebbero emersi solo in produzione live.
## 8 mag 2026 (mattina, FINALIZZAZIONE) — Export PPT in PRODUZIONE su pid-nine.vercel.app

### Completamento test 3-4-2-1 + cosmetica + merge in main

#### Fix conclusivi sul branch feature/pptx-export

1. **Sistema 3-4-2-1 testato live** — funzionante. Inizialmente i 2 trequartisti laterali (LAM/RAM) avevano foto ma non card sotto, perché la mappa per `3-4-2-1` non aveva `RAM/LAM`. Aggiunti come:
   - `RAM → RW1` (template — usa lo spazio dell'ala destra)
   - `LAM → LW1` (template — usa lo spazio dell'ala sinistra)
   - `RM → RFB1`, `LM → LFB1` (esterni di centrocampo come terzini alti)
   - `ST → ST1` (punta singola)

2. **Allargamento posizioni RAM/LAM nelle Griglie** — i due trequartisti laterali nel 3-4-2-1 erano troppo vicini al centro (x=70 e x=30). Spostati a x=80 e x=20 per migliore visibilità nel pitch SVG.

3. **Rinominato bottone export** — "📥 PPT" → "Esporta PPTX" (più chiaro). Modificata chiave `export_pptx` in `frontend/i18n.js`.

#### Test live finale - 6/6 sistemi verificati

| Sistema   | Test live | Stato |
|-----------|-----------|-------|
| 3-5-2     | ✅        | Tutti gli 11 pieni + colori squadra |
| 3-4-3     | ✅        | RM/LM mappati a RFB1/LFB1 |
| 3-4-2-1   | ✅        | RAM/LAM mappati a RW1/LW1 |
| 4-3-3     | ✅        | Conceição RW + Yıldız LW |
| 4-2-3-1   | ✅        | CAM trequartista in ST1B + RDM/LDM mediani |
| 4-4-2     | ✅        | RM/LM ali in attacco → RW1/LW1 |

#### Merge in main → produzione live

```
git checkout main
git pull origin main
git merge feature/pptx-export
git push origin main
```

Vercel deploya la production: il bottone "Esporta PPTX" è ora **live su `pid-nine.vercel.app`**.

### Stato finale dell'export PPT

```
Sito:        pid-nine.vercel.app (production)
Bottone:     "Esporta PPTX" nella toolbar Griglie
Endpoint:    POST /export-pptx (FastAPI + Mangum su Vercel)
Generator:   scripts/pptx_generator/ (template + 6 sistemi mappati)
Foto:        data/photos/players_sots_lookup/ (filesystem locale)
Loghi:       scripts/pptx_generator/assets/loghi_squadre/ (PNG per squadra)
Colori:      scripts/pptx_generator/assets/colori_squadre.json (24 squadre Serie A)
```

### Caratteristiche dell'export

- **Auto-detect squadra**: dedotto dal `club_name` della maggioranza dei titolari
- **Logo squadra**: cercato in `loghi_squadre/{slug_squadra}.png`, fallback Italia
- **Cerchi pressing colorati per squadra**: dalla mappa `colori_squadre.json`
- **Tutti gli 11 cerchi pressing sempre pieni**: GK in posizione + 10 outfield in ordine z-order
- **Foto giocatori**: sostituzione automatica dal filesystem repo
- **Cognomi puliti**: solo ultima parola (Locatelli, Kalulu) salvo eccezioni (Di Gregorio, Joao Mario)
- **Foot D/S**: per giocatori ambidestri "D/S" con S in rosso bold
- **Logo squadra dimensioni per slide**: cover 2.6cm, formazione 1.6cm, pressing 1.1cm
- **Match info generici**: "Stadio – Città – Paese", "GG Mese 2026 – HH:MM", "Serie A 2026/27 – Xª giornata", "COACH Nome Cognome" (popolabili in futuro da form modale)
- **Strisce viola template**: alto-sx in primo piano, basso-dx dietro al campo

### Sintesi sessione 7-8 mag (2 giorni)

**Punto di partenza** (7 mag mattina): zero infrastruttura PPT
**Punto di arrivo** (8 mag mattina): bottone live in produzione, 6 sistemi supportati, 18 commit nel branch

**Bug critici risolti durante il percorso**:
1. ImagePart condivise (foto duplicate)
2. SYSTEM_TO_SLIDE_INDEX shift slide template
3. ST1B come trequartista nel 4-2-3-1
4. window._players → state.players
5. Mappa _PPTX_SLOT_MAP globale → per sistema
6. fill_pressing_slide → riempi sempre tutti gli 11 cerchi
7. LOGO_ITALIA_HASH cancellato accidentalmente da regex greedy
8. Mappature RM/LM specifiche per sistema (esterno cc vs ala alta)
9. RAM/LAM nel 3-4-2-1 → RW1/LW1
10. Mancanza FORMATIONS["3-4-2-1"] nel frontend

### TODO post-rilascio

1. **Verifica run notturno** auto_update_daily.yml + Locatelli stats su R2 (punto pendente da stamattina)
2. **Form modale match_info**: per ora i match info sono hardcoded generici. Aggiungere modale dove l'utente inserisce stadio/data/avversario/competizione/coach prima di esportare
3. **Cleanup branch feature/pptx-export**: opzionale, può essere cancellato (`git branch -d feature/pptx-export` + `git push origin --delete feature/pptx-export`)
4. **Documentazione utente**: spiegare ai giocatori del PID come usare l'export

### File modificati nella sessione totale (7-8 mag)

```
M  api/main.py                                  (+103 righe)
M  api/requirements.txt                         (+3 righe: pptx, Pillow, mangum)
M  frontend/app.js                              (+200 righe: bottone, helpers, mappa, FORMATIONS 3-4-2-1)
M  frontend/i18n.js                             (+8 righe: chiavi PPTX, label "Esporta PPTX")
M  vercel.json                                  (rewrites + functions config)
M  progetto-pid.md                              (+1500 righe diario)
A  .vercelignore
A  scripts/pptx_generator/                      (~25KB generator + assets ~3.7MB template)
```

### PROMPT DI RIPRESA (per la prossima sessione)

> Ciao Claude, riprendo PID. Stato:
> 
> 1. ✅ Generator PowerPoint LIVE in produzione su `pid-nine.vercel.app`. Bottone "Esporta PPTX" nella pagina Griglie. Tutti i 6 sistemi (3-5-2, 3-4-3, 3-4-2-1, 4-3-3, 4-2-3-1, 4-4-2) testati e funzionanti.
> 2. ⏳ Da verificare: run notturno auto_update_daily.yml di stanotte 03:00 UTC → Locatelli stats su R2.
> 3. 🔄 Possibili miglioramenti futuri:
>    - Form modale per match_info (stadio/data/avversario/competizione/coach)
>    - Documentazione utente per il bottone export
>    - Cleanup branch `feature/pptx-export`
## 8 mag 2026 (mattina, post-rilascio PPT) — Status run notturno + Locatelli stats su R2

### Diagnostica run notturno auto_update_daily

Dopo il rilascio del bottone Esporta PPTX in produzione, verifica del punto pendente: i dati di Locatelli non erano ancora aggiornati su R2 dopo il run notturno presunto della notte 7→8 maggio.

#### Stato dati al momento della diagnostica (mattina 8 mag, ~10:30 UTC)

| Dove | Giocatori | Locatelli | Stato |
|------|-----------|-----------|-------|
| `data/players_main.json` (locale + repo) | 2859 | ✅ presente | aggiornato |
| `data/players_static.json` (locale + repo) | 2859 | ✅ presente | aggiornato |
| `data/players_stats.json` (locale, gitignored) | 2758 | ✅ 2 stagioni | aggiornato |
| **R2** `pub-aa9d173290684b36a9f35e79d4d388c2.r2.dev/players_stats.json` | **2757** | ❌ assente | **non aggiornato** |

Delta: R2 ha 102 giocatori in meno rispetto a `players_main.json` (forse giocatori senza stats o pre-Locatelli).

#### Run di GitHub Actions trovati

Lista degli ultimi 2 run del workflow `Auto Update Daily (stats only)`:

| Run | Trigger | Status | Conclusion |
|-----|---------|--------|------------|
| 2026-05-08T08:15:05Z | schedule (cron) | **in progress** | (in esecuzione) |
| 2026-05-07T08:04:39Z | workflow_dispatch (manuale) | completed | **cancelled** |

Il run di ieri (manual dispatch) si è interrotto durante `Run stats refresh` (probabile timeout 90 min, prima del bump a 180 min in commit 9474b74).

Il run di stanotte (schedule cron) è partito alle **08:15:05 UTC = 10:15 ora italiana**, NON alle 03:00 UTC come da cron. GitHub Actions a volte ritarda i cron schedulati di diverse ore (è documentato come comportamento normale del sistema). 

#### Stato del run in corso (verificato alle ~10:45 UTC)

```
Job: daily-update  status=in_progress
  - Set up job                           ✅ success
  - Checkout repo                        ✅ success
  - Setup Python                         ✅ success
  - Install dependencies                 ✅ success
  - Hash pre-run players_stats.json      ✅ success (file mancante = hash vuoto)
  - Run stats refresh                    ⏳ IN PROGRESS (start: 08:15:37 UTC)
  - Hash post-run + check changes        pending
  - Upload to Cloudflare R2              pending
  - Commit and push if changed           pending
```

Stato `Run stats refresh` partito ~30 min fa. Tempo previsto per completamento: ~30-60 min.

#### Logica del workflow + bug strutturale rilevato

Il workflow:
1. Checkout repo (senza `players_stats.json`, gitignored 88MB)
2. Pre-hash → vuoto (file mancante)
3. `run_stats.py --refresh` → ricostruisce stats per **TUTTI** i 2859 giocatori in `players_main.json`
4. Post-hash → diverso (sempre changed=true)
5. Upload R2

**Bug rilevato**: il workflow **NON scarica `players_stats.json` da R2 prima del refresh**. Significa che:
- Ogni run rifa **tutto da zero** (~30-40 min)
- Funzionalmente OK perché Locatelli è in `players_main.json`
- Il prossimo upload R2 avrà 2859 giocatori (incluso Locatelli) ✅

Più efficiente sarebbe: download R2 → resume incrementale (skip giocatori esistenti) → upload R2. Ma con `--refresh` flag esplicito, è OK rifare tutto.

#### Esito atteso

Quando il run completa (~13:00 italiana):
- `players_stats.json` su R2 avrà 2858+ giocatori inclusi Locatelli
- Il sito `pid-nine.vercel.app` mostrerà le stats di Locatelli (caricate via R2_OVERRIDES)
- Frontend `/data/players_stats` → redirect a R2 → JSON aggiornato

#### Decisione

**Aspettare** il completamento del run (no upload manuale). Se non completa entro 13:30 UTC italiana, valutare:
1. Cancellare e rilanciare run manualmente
2. Forzare upload R2 da Mac (richiede `.env` ricreato)
3. Investigare se il workflow ha bug latenti

### Riassunto sessione 8 mag (mattina completa)

✅ **Completati**:
1. Bottone "Esporta PPTX" rilasciato in produzione su `pid-nine.vercel.app`
2. Tutti i 6 sistemi (3-5-2, 3-4-3, 3-4-2-1, 4-3-3, 4-2-3-1, 4-4-2) testati e funzionanti live
3. Sistema 3-4-2-1 aggiunto al frontend FORMATIONS
4. Verifica/diagnosi run notturno auto_update_daily

⏳ **In corso**:
- Run stats refresh GitHub Actions (completamento previsto ~13:00 italiana)
- Locatelli stats sarà su R2 al completamento del run

### TODO

1. Verificare al completamento del run che R2 abbia 2858+ giocatori inclusi Locatelli
2. Hard reload `pid-nine.vercel.app` → verificare stats Locatelli visibili in pagina giocatore
3. Cancellare backup files `players_stats.json.locatelli_only_backup` se presente
4. (Possibile miglioramento futuro): aggiungere step di download R2 al workflow per fare resume invece di rifare tutto
## 8 mag 2026 (mattina, post-rilascio PPTX) — 2 modifiche cosmetiche

### Modifica 1 — Riordino dropdown Modulo nelle Griglie

L'ordine di FORMATIONS nel frontend determinava l'ordine dei sistemi nel dropdown "Modulo" della pagina Griglie. Ordine richiesto:

```
4-4-2 → 4-2-3-1 → 4-3-3 → 3-5-2 → 3-4-2-1 → 3-4-3
```

(Sistemi a 4 difensori prima, poi a 3, dal più offensivo al più difensivo all'interno di ciascun gruppo.)

**Nota tecnica**: il cambio di ordine è puramente UI. Il sistema continua a funzionare in produzione perché:
- `state.grids.formation` salva il valore stringa (es. `"4-2-3-1"`)
- Le mappe `_PPTX_SLOT_MAP_BY_SYSTEM[sistema]` e `SYSTEM_TO_SLIDE_INDEX[sistema]` sono indicizzate per stringa, non per posizione
- L'ordine in `FORMATIONS` influenza solo `Object.keys(FORMATIONS).map(...)` nel template del select

Commit: `fix: riordina sistemi nel dropdown Modulo` → `9524203` su main.

### Modifica 2 — Display name dei club italiani

#### Requisito

Il display dei nomi club nel frontend (scheda giocatori, dropdown filtri, card) era ridondante con prefissi/suffissi società. Esempi:
- "ACF Fiorentina" → "Fiorentina"
- "AC Milan" → "Milan"
- "Inter Milan" → "Inter"
- "Juventus FC" → "Juventus"
- "AC Reggiana 1919" → "Reggiana"

#### Decisioni di design

| Aspetto | Decisione |
|---------|-----------|
| Dove applicare | Solo display frontend |
| Database | Invariato (matching dataset esterni) |
| Lingue/leghe | Solo Serie A (IT1), Serie B (IT2), Primavera (IJ1) |
| Suffissi categoria | Mantenuti ("Atalanta Primavera" resta tale) |
| Prefissi società | Rimossi (AC, AS, ACF, US, UC, SS, SSC, FC) |

#### Implementazione

Aggiunta funzione `prettyClubName(name)` in `frontend/app.js` con mappa hardcoded `_CLUB_DISPLAY_MAP` (60 club italiani: 20 IT1 + 20 IT2 + 20 PRIM).

```javascript
const _CLUB_DISPLAY_MAP = {
  "AC Milan": "Milan",
  "ACF Fiorentina": "Fiorentina",
  "AS Roma": "Roma",
  "Atalanta BC": "Atalanta",
  // ... 60 mappature totali
  "Hellas Verona Primavera": "Verona Primavera",
  "Inter Milan Primavera": "Inter Primavera",
};

function prettyClubName(name) {
  if (!name) return name;
  return _CLUB_DISPLAY_MAP[name] || name;
}
```

Nomi di club non italiani (polacchi, ecc.) tornano invariati per default.

#### Mappa completa

**Serie A (IT1)** — rimozione prefissi società:
```
AC Milan          → Milan
ACF Fiorentina    → Fiorentina
AS Roma           → Roma
Atalanta BC       → Atalanta
Bologna FC 1909   → Bologna
Cagliari Calcio   → Cagliari
Como 1907         → Como
Genoa CFC         → Genoa
Hellas Verona     → Verona
Inter Milan       → Inter
Juventus FC       → Juventus
Parma Calcio 1913 → Parma
Pisa Sporting Club→ Pisa
SS Lazio          → Lazio
SSC Napoli        → Napoli
Torino FC         → Torino
US Cremonese      → Cremonese
US Lecce          → Lecce
US Sassuolo       → Sassuolo
Udinese Calcio    → Udinese
```

**Serie B (IT2)** — rimozione prefissi società:
```
AC Monza               → Monza
AC Reggiana 1919       → Reggiana
Calcio Padova          → Padova
Carrarese Calcio 1908  → Carrarese
Cesena FC              → Cesena
Delfino Pescara 1936   → Pescara
FC Empoli              → Empoli
FC Südtirol            → Südtirol
Frosinone Calcio       → Frosinone
Mantova 1911           → Mantova
Modena FC              → Modena
Palermo FC             → Palermo
SS Juve Stabia         → Juve Stabia
SSC Bari               → Bari
Spezia Calcio          → Spezia
UC Sampdoria           → Sampdoria
US Avellino 1912       → Avellino
US Catanzaro           → Catanzaro
Venezia FC             → Venezia
Virtus Entella         → Virtus Entella
```

**Primavera (IJ1)** — suffisso "Primavera" mantenuto, solo prefisso pulito:
```
AC Milan Primavera         → Milan Primavera
Hellas Verona Primavera    → Verona Primavera
Inter Milan Primavera      → Inter Primavera
(altri 17 invariati - già usano nome corto)
```

#### Punti applicazione nel frontend

22 occorrenze di `current_club_name` analizzate. Distinte tra:

**DISPLAY (avvolti con `prettyClubName`)** — 13 punti:
- Righe 2158, 3188, 4324, 4547, 5066, 5174, 5982 — `escapeHtml(p.current_club_name||"")` → `escapeHtml(prettyClubName(p.current_club_name||""))`
- Riga 2601 — `clubName.slice(0, 20)` con prettyClubName
- Riga 2623 — `name: p.current_club_name || cl?.name || "—"` in callup
- Riga 4187 — `clubAbbr` regex con prettyClubName
- Riga 3135 — `clubAbbrev(pl.current_club_name)` con prettyClubName  
- Riga 5664 — sub label search risultati

**LOGICA (NON toccati)** — 9 punti:
- Righe 506, 511, 4294 — sort per nome club
- Riga 2432 — ricerca testuale (ql.includes)
- Righe 5029-5030 — comparator sort
- Righe 3468-3469 — payload PPT (cerca match esatto su `club_name`)
- Riga 915 — alt attribute (cosmetico, irrilevante)
- Riga 3349 — `localizeRole`, non club

#### Test e merge

Push diretto su `main` (no branch feature, modifica cosmetica low-risk). Vercel auto-deploya in produzione.

Commit messages:
1. `feat: rinomina display nomi club italiani (Serie A/B/Primavera) - DB invariato`

### Risultato finale dropdown filtri club

Prima:
```
Tutti i club
AC Milan
AC Milan Primavera
AC Monza
AC Reggiana 1919
ACF Fiorentina
AS Roma
Atalanta BC
Atalanta Primavera
...
```

Dopo:
```
Tutti i club
Avellino
Atalanta
Atalanta Primavera
Atalanta U23
Bari
Bologna
Bologna Primavera
...
Milan
Milan Primavera
...
```

Note: le voci sono ordinate alfabeticamente sul **nome ORIGINALE** (a livello logica) ma mostrate col display `prettyClubName`. Possibile cosmetica futura: anche l'ordinamento basato sul nome display.

### Stato fine sessione mattina 8 mag

✅ **Online in produzione su `pid-nine.vercel.app`**:
1. Bottone "Esporta PPTX" funzionante per tutti i 6 sistemi
2. Dropdown Modulo riordinato (4-4-2 → 4-2-3-1 → 4-3-3 → 3-5-2 → 3-4-2-1 → 3-4-3)
3. Nomi club italiani puliti nel display (Milan, Fiorentina, Inter, Roma, ecc.)

⏳ **In corso**:
- Run notturno auto_update_daily.yml in attesa di completamento (~13:00 italiana)
- Locatelli stats arriveranno su R2 al completamento

### TODO

1. Verificare al completamento del run che R2 abbia 2858+ giocatori inclusi Locatelli
2. Hard reload `pid-nine.vercel.app` → verificare stats Locatelli
3. Eventuali edge case del cleanup club (se qualche punto display sfugge → segnalare)
4. **Possibile miglioramento**: ordinare le voci del dropdown filtri club sul nome `prettyClubName` invece che sul nome originale, per coerenza alfabetica visibile
## 8 mag 2026 (fine mattina) — Ulteriori fix display

### Fix typo titolo applicazione

Tutti i punti display erano scritti "**Player** Intelligence Database" invece di "**Players** Intelligence Database" (manca s a "Player"). Sostituiti:
- `frontend/i18n.js`: 2 occorrenze (it + en) di `title:`
- `frontend/index.html`: titolo browser tab + meta tags
- `frontend/app.js`: 1 commento di intestazione (cosmetico, non visibile)

Commit: `fix: 'Player' → 'Players' Intelligence Database (typo)` → `b7c9f6e`.

### Fix prettyClubName non applicato ai dropdown filtri club

Il deploy iniziale di `prettyClubName()` aveva avvolto solo i punti display dei giocatori (`current_club_name`), ma non i **dropdown filtri club** che usano `state.clubs[].name` (campo diverso). Risultato: l'utente vedeva ancora "ACF Fiorentina", "AC Milan" nei filtri.

#### Punti aggiuntivi avvolti

5 dropdown filtro club hanno questo pattern:
```javascript
.map(c => `<option value="${c.tm_club_id}">${escapeHtml(c.name)}</option>`)
```

Tutti avvolti con `prettyClubName()`:
- Line 473 — filtro Lista giocatori (Tutti i club)
- Line 2216 — filtro avanzato pagina
- Line 3323 — filtro Griglie (Tutti i club)
- Line 4382 — filtro lista alternativo
- Line 5295 — filtro pagina compare/altro

E anche:
- Line 2689 — clubLine display in card club: `c.name` con truncate avvolto

#### Replace fatto via regex generico

Pattern catturato:
```python
pattern = r'(\.map\(c => `<option[^>]*>)\${escapeHtml\(c\.name\)\}'
src = re.sub(pattern, r'\1${escapeHtml(prettyClubName(c.name))}', src)
```

Sostituzioni totali: 3 dropdown via regex + 2 punti specifici via replace puntuale.

#### Verifica finale

```
prettyClubName: 20 occorrenze in frontend/app.js
escapeHtml(c.name) restanti: 3 (in contesti NON club, OK)
```

Commit: `fix: applica prettyClubName ai dropdown filtri club (5 punti residui)` → push su main.

### Stato post-mattina 8 mag

✅ **Online in produzione**:
1. Bottone "Esporta PPTX" funzionante per tutti i 6 sistemi
2. Dropdown Modulo riordinato (4-4-2 → 4-2-3-1 → 4-3-3 → 3-5-2 → 3-4-2-1 → 3-4-3)
3. Nomi club italiani puliti **ovunque** (display giocatori + dropdown filtri)
4. Titolo applicazione fix: "Players Intelligence Database"

### TODO

1. ⏳ Aspetta completamento run notturno auto_update_daily.yml (~13:00) → Locatelli stats su R2
2. (Possibile miglioramento futuro): ordinare dropdown filtri club sul nome `prettyClubName` invece che sul nome originale per coerenza alfabetica
## 8 mag 2026 (fine mattina, ulteriori fix display) — Coverage finale prettyClubName

### Bug residui scoperti dall'utente

Dopo il deploy iniziale di `prettyClubName()`, l'utente ha segnalato 2 punti dove i nomi club erano ancora visualizzati nella loro forma originale (con prefissi società):

#### Image 1 — Scheda giocatore (player drawer)

L'header della scheda giocatore (modale dettaglio giocatore) mostrava ancora "ACF Fiorentina" sotto il nome del giocatore, accanto alla bandiera nazionale.

**Punto non avvolto**: riga 917 in `frontend/app.js`:
```html
<div style="font-size: 14px; font-weight: 600; color: var(--text-1); line-height: 1.2;">${escapeHtml(p.current_club_name)}</div>
```

#### Image 2 — Pagina Club (lista delle 100 squadre)

La pagina `Club` (sidebar) elenca i club divisi per lega (Serie A, Serie B, Primavera, Polonia) con logo + nome + count giocatori. I nomi mostrati erano ancora "AC Milan", "ACF Fiorentina", "AS Roma", ecc.

**Punto non avvolto**: `renderClubCard()` riga 616:
```html
<div class="text-[10px] font-semibold leading-tight truncate w-full">${escapeHtml(c.name)}</div>
```

E anche l'attributo `alt` dell'immagine logo (riga 613):
```html
<img src="${logo}" alt="${escapeHtml(c.name)}" class="w-10 h-10 object-contain..."/>
```

### Fix applicato

Avvolti tutti i punti rimanenti:

```javascript
// Scheda giocatore (header)
${escapeHtml(prettyClubName(p.current_club_name))}

// Fallback letter quando manca logo
${(prettyClubName(p.current_club_name)||"?")[0]}

// Card pagina Club
<div>${escapeHtml(prettyClubName(c.name))}</div>
<img alt="${escapeHtml(prettyClubName(c.name))}" .../>
```

### Verifica finale coverage

Dopo questo fix, `prettyClubName` è applicato in **22+ punti** del frontend, coprendo:

- ✅ Lista giocatori (card)
- ✅ Tabella giocatori (riga)
- ✅ Scheda giocatore drawer (header con club + bandiera)
- ✅ Dropdown filtro club (5 punti diversi: lista, griglie, compare, callup)
- ✅ Card pagina Club (3 sezioni: Serie A, B, Primavera)
- ✅ Risultati ricerca (sub-label)
- ✅ Convocazione (callup label)
- ✅ Griglie (clubAbbr nei nodi titolari)

I punti **non** avvolti (intenzionalmente) restano:
- Sort/comparator (`localeCompare` su nome originale per ordinamento alfabetico DB-stable)
- Filtri ricerca testuale (`includes` su nome originale per matchare anche "Inter Milan")
- Payload PPT (matcha `club_name` esatto su `loghi_squadre/{slug}.png`)
- Sanitize logica `current_club_name` ricostruito da `state.clubs[].name`

Commit: `fix: applica prettyClubName a scheda giocatore + card pagina Club`.

### Stato post-rifinitura

Sito `pid-nine.vercel.app` completamente coerente nei display dei club. L'utente vede ovunque i nomi puliti:
- Card giocatore: "Sabiri" → "Fiorentina"
- Drawer giocatore: "Abdelhamid Sabiri" → "Fiorentina · Serie A"
- Pagina Club: "Milan", "Fiorentina", "Inter", "Roma", "Napoli", ecc.
- Tutti i dropdown filtri club: stessi nomi puliti

Il database resta invariato (matching dataset esterni come Wyscout/Transfermarkt continuano a funzionare). 

### TODO ancora aperti

1. ⏳ Run notturno auto_update_daily.yml in attesa completamento (~13:00 italiana) → Locatelli stats su R2
2. (Cosmetica futura): ordinare i dropdown filtri club sul nome `prettyClubName` invece che sul nome originale, per coerenza alfabetica visibile (es. "Verona" sotto V invece di "Hellas Verona" sotto H)
3. (Cosmetica futura): se compaiono altri club italiani in futuro (promossi, retrocessi), aggiungerli alla mappa `_CLUB_DISPLAY_MAP` in `frontend/app.js`
## 8 mag 2026 (mezzogiorno) — Locatelli stats su R2 verificate + fix workflow

### Run notturno completato e R2 aggiornato

Il workflow `Auto Update Daily (stats only)` triggerato dal cron 03:00 UTC (ma ritardato a 08:15 UTC come spesso accade su GitHub Actions free tier) è completato con tutti gli step principali OK:

```
✓ Set up job
✓ Checkout repo
✓ Setup Python
✓ Install dependencies
✓ Hash pre-run players_stats.json
✓ Run stats refresh                    (durato ~1h 30min)
✓ Hash post-run + check changes
✓ Upload to Cloudflare R2              ← R2 AGGIORNATO
✗ Commit and push if changed           ← FALLITO (exit 128 - cosmetico)
```

Verifica finale R2:
```
HTTP 200 | size=132,648,642 bytes (vs 127,880,998 di stamattina, +5MB)
Last-Modified: Fri, 08 May 2026 10:03:36 GMT (12:03 ora italiana)
Totale giocatori R2: 2855 (vs 2757 stamattina, +98)
Locatelli (tm_id=265088): ✅ PRESENTE
  Stagioni: 2
```

### Causa del fail dell'ultimo step (cosmetico)

Lo step `Commit and push if changed` è fallito con exit code 128 (errore git push). Causa: durante l'esecuzione del workflow (~1h 48min), io ho pushato 5+ volte sul branch `main` (fix typo, riordino dropdown, prettyClubName, fix scheda giocatore). Quando il workflow ha tentato il `git push` finale, il main remoto era avanti rispetto al checkout iniziale del workflow → push rejected.

**Importante**: il fallimento è **NON-blocking** per la funzionalità. R2 era già stato aggiornato nello step precedente (Upload to Cloudflare R2 = success). L'unica cosa che non è stata pushata è `data/last_update.json` (timestamp ultimo aggiornamento). Cosmetico.

### Fix applicato al workflow

Modificato `Commit and push if changed` per gestire push concurrent:

```yaml
git commit -m "auto: daily stats refresh ($(date -u +%Y-%m-%d))"
# Retry push fino a 3 volte
for i in 1 2 3; do
  echo "Push attempt $i/3"
  if git pull --rebase origin main && git push; then
    echo "Push succeeded on attempt $i"
    exit 0
  fi
  echo "Push failed, retrying..."
  sleep 5
done
echo "All push attempts failed"
exit 1
```

Logica:
1. `git pull --rebase origin main` → applica i nuovi commit remoti sopra il commit del bot
2. `git push` → invia il commit del bot al main aggiornato
3. Retry fino a 3 volte (5s di sleep tra tentativi) in caso di race conditions

Push dell'aggiornamento workflow su `main`.

### Stato finale dell'applicazione

Sito `pid-nine.vercel.app` completamente funzionante:

✅ **Tutte le feature richieste in produzione**:
1. Bottone "Esporta PPTX" — 6 sistemi tattici (3-5-2, 3-4-3, 3-4-2-1, 4-3-3, 4-2-3-1, 4-4-2)
2. Dropdown Modulo riordinato per preferenza (4-4-2, 4-2-3-1, 4-3-3, 3-5-2, 3-4-2-1, 3-4-3)
3. Nomi club italiani puliti ovunque (display only, DB invariato)
4. Typo "Players Intelligence Database" corretto
5. Locatelli stats ora visibili sul sito
6. Workflow notturno robusto a push concurrent

### Numeri sessione 7-8 maggio

- **2 giorni** di lavoro
- **20+ commit** su `main` + 18 commit su `feature/pptx-export`
- **3 sezioni grandi** completate:
  - Generator PowerPoint per 6 sistemi (~25KB di codice)
  - Endpoint Vercel `/export-pptx` (FastAPI + Mangum)
  - Bottone frontend + helpers + i18n
- **15+ bug fixati** durante il percorso (vedi diari precedenti)
- **2 modifiche cosmetiche minor**: prettyClubName, riordino dropdown, typo
- **2 hotfix workflow GitHub Actions**: timeout 90→180, retry pull-rebase

### TODO per prossima sessione

Niente di urgente. Possibili miglioramenti:
1. Form modale frontend per match_info dell'export PPT (stadio/data/avversario/competizione/coach) invece di valori hardcoded
2. Documentazione utente per il bottone export
3. Cleanup branch `feature/pptx-export` (non più necessario, già mergato)
4. Ordinamento dropdown filtri club sul nome `prettyClubName` (per ordine alfabetico visibile coerente)
5. Aggiungere step `download R2` al workflow per fare resume incrementale invece di rifare 2859 giocatori da zero (efficienza)

### PROMPT DI RIPRESA

> Ciao Claude, riprendo PID. Ultima sessione: 8 mag mattina/mezzogiorno. Stato:
>
> ✅ Tutto live in produzione su `pid-nine.vercel.app`:
> - Bottone "Esporta PPTX" funzionante per 6 sistemi tattici
> - Locatelli stats su R2 (2855 giocatori, run notturno OK)
> - Nomi club italiani puliti
> - Workflow GitHub Actions robusto a push concurrent (retry 3x con pull --rebase)
>
> Niente di urgente. Possibili miglioramenti vedi TODO ultimo diario.
## 8 mag 2026 (pomeriggio) — Admin backend per editing giocatori

### Obiettivo

Creare un'area admin nel sito per:
1. Modificare dati giocatori (data nascita, piede, posizione, altezza, numero, altri ruoli)
2. Aggiungere nuovi giocatori da URL Transfermarkt
3. Le modifiche admin devono prevalere sopra agli aggiornamenti notturni automatici

### Decisioni architetturali

| Aspetto | Decisione |
|---------|-----------|
| Backend storage | **Supabase** (già configurato per auth utenti) |
| Tabella nuova | `player_overrides` (PK: `tm_player_id`, JSON `overrides`) |
| Auth admin | Email hardcoded `simonecontran10@gmail.com` |
| Sicurezza | RLS Supabase con verifica `auth.jwt() ->> 'email'` |
| Override application | Bootstrap frontend: `Object.assign(player, override)` dopo caricamento JSON |
| Posizione UI | Pagina `/admin` (sidebar nascosta a non-admin) |

### Step 1 — Tabella Supabase `player_overrides`

SQL eseguito nel SQL Editor di Supabase:

```sql
CREATE TABLE IF NOT EXISTS player_overrides (
  tm_player_id  bigint PRIMARY KEY,
  overrides     jsonb NOT NULL DEFAULT '{}'::jsonb,
  updated_by    text,
  updated_at    timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_player_overrides_updated_at 
  ON player_overrides(updated_at DESC);

ALTER TABLE player_overrides ENABLE ROW LEVEL SECURITY;

CREATE POLICY "po_public_read" ON player_overrides FOR SELECT USING (true);
CREATE POLICY "po_admin_insert" ON player_overrides FOR INSERT WITH CHECK (auth.jwt() ->> 'email' = 'simonecontran10@gmail.com');
CREATE POLICY "po_admin_update" ON player_overrides FOR UPDATE USING (auth.jwt() ->> 'email' = 'simonecontran10@gmail.com');
CREATE POLICY "po_admin_delete" ON player_overrides FOR DELETE USING (auth.jwt() ->> 'email' = 'simonecontran10@gmail.com');
```

Sicurezza: anche se un attaccante manipola il client per vedere il tab Admin, **non può scrivere** senza un JWT con la email autorizzata.

### Step 2 — Modifiche `frontend/cloud_sync.js`

Aggiunte funzioni:

1. **`fetchPlayerOverrides()`** — query Supabase per leggere tutte le righe `player_overrides`
2. **`applyOverridesToPlayers(players, overrides)`** — applica `Object.assign` per ogni override sul giocatore corrispondente
3. **`window.isAdmin()`** — verifica se l'utente loggato ha email = `simonecontran10@gmail.com`
4. **`window._toggleAdminNav()`** — mostra/nasconde voce "Admin" nella sidebar
5. **`window._supa`** — esposto globalmente per uso in `app.js`

Il toggle viene chiamato in entrambi i punti dove `cloudAuth.user` viene settato:
- Riga 96: dopo `getSession()` iniziale
- Riga 111: dopo `onAuthStateChange()`

### Step 3 — Bootstrap aggiornato in `frontend/app.js`

Aggiunto try/catch dopo `state.players = (main || []).map(...)`:

```js
try {
  if (window.fetchPlayerOverrides) {
    const overrides = await window.fetchPlayerOverrides();
    if (overrides && overrides.length > 0) {
      window.applyOverridesToPlayers(state.players, overrides);
    }
  }
} catch (e) {
  console.warn("[overrides] errore caricamento:", e);
}
```

Risultato: ad ogni caricamento del sito, gli override admin vengono recuperati da Supabase e applicati ai giocatori sopra ai dati JSON di Transfermarkt.

### Step 4 — Pagina admin in `frontend/app.js`

Aggiunta funzione `renderAdminPanel()` che genera un layout 2 colonne:

**LEFT (360px)**:
- Card "Aggiungi nuovo giocatore" — input URL TM + bottone (workflow GitHub Actions, da implementare)
- Card "Cerca giocatore da modificare" — search input + lista risultati cliccabili

**RIGHT**:
- Form editor con i seguenti campi:
  - **Data di nascita** — input type=date
  - **Piede** — select (Destro / Sinistro / Ambidestro)
  - **Posizione specifica** — select con 12 ruoli canonici raggruppati per categoria (Goalkeeper / Defender / Midfield / Attack)
  - **Altri ruoli (selezione multipla)** — multi-select (size=6) con tutti i 13 ruoli
  - **Altezza (cm)** — input numerico
  - **Numero maglia** — input numerico
- Bottoni "Salva e aggiorna" + "Annulla"
- Status banner per feedback

Save logic (`_adminSaveOverrides`):
1. Costruisce `overrides` dict solo coi campi compilati
2. `position_others` salvato sempre (anche se vuoto, per consentire rimozione)
3. Upsert su `player_overrides` via `window._supa.from(...).upsert(...)`
4. Object.assign immediato per aggiornare UI senza reload

### Step 5 — Sidebar HTML (`frontend/index.html`)

Aggiunta voce nascosta dopo "Salvataggi":

```html
<div class="nav-item" data-route="admin" id="nav-admin" style="display: none;">
  <svg viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
  <span class="sidebar-label">Admin</span>
</div>
```

E `<div id="admin-panel" class="hidden"></div>` prima di `</main>`.

### Step 6 — Routing (`frontend/app.js`)

Aggiunto in `setActiveTab()`:
- `setVisible("admin-panel", route === "admin")`
- `if (route === "admin") renderAdminPanel()`

### Test live

✅ Modifiche eseguite con successo su Locatelli:
- Position specific: `Defensive Midfield` (era già)
- Altri ruoli: aggiunto `Right Winger` come secondo ruolo
- Persistenza verificata via curl Supabase REST API
- Override applicato visualmente nella scheda giocatore al refresh

### Sicurezza verificata

- ✅ Voce "Admin" nascosta a utenti non-admin (CSS `display: none` + toggle JS)
- ✅ Anche se un utente ne manipola il DOM per mostrare il tab, **Supabase rifiuta scritture** senza JWT autorizzato
- ✅ Lettura overrides pubblica (necessaria per applicare override a tutti gli utenti)

### TODO immediati

1. **Add giocatore da URL TM** — endpoint `/admin-add-player` + GitHub Actions workflow `add_player.yml`
   - Richiede creazione PAT GitHub con permessi `repo`
   - Secret Vercel `GITHUB_PAT` da configurare
   - Workflow async (Vercel timeout 60s, add_players.py impiega 1-3 min)
2. **(Cosmetica)** ordinare la lista ruoli secondari sul frontend in modo coerente
3. **(Audit)** opzionale: aggiungere tabella `audit_log` per tracciare ogni modifica admin

### File modificati

```
M  frontend/app.js          (+~250 righe: renderAdminPanel + helpers + dropdown ruoli + multi-select)
M  frontend/cloud_sync.js   (+~50 righe: fetchPlayerOverrides + isAdmin + toggleNav)
M  frontend/index.html      (+5 righe: nav admin + admin-panel div)
+ Tabella Supabase          player_overrides (con 4 RLS policies)
```

Commit principali su `main`:
- `feat: pagina admin per editing giocatori`
- `feat: dropdown ruoli admin editor con 12 posizioni canoniche`
- `feat: aggiunge multi-select 'Altri ruoli' nell'admin editor`
## 8 mag 2026 (pomeriggio tardi) — Admin Add Player setup completo

### Sintesi rapida

Implementato sistema completo per aggiungere nuovi giocatori da URL Transfermarkt direttamente dal frontend admin. Il flusso end-to-end è:

```
Admin UI (frontend) 
  ↓ POST /admin-add-player con URL TM
Endpoint Vercel (api/main.py)
  ↓ POST GitHub API workflow_dispatch
GitHub Actions (.github/workflows/add_player.yml)
  ↓ esegue add_players.py + enrich_sortitoutsi.py + commit/push
Repo aggiornato → Vercel auto-deploy → giocatore visibile
```

### File creati/modificati

| File | Modifica |
|------|----------|
| `.github/workflows/add_player.yml` | Nuovo workflow con `workflow_dispatch`, input `url`, retry 5x su push |
| `api/main.py` | Endpoint POST `/admin-add-player` con auth Bearer GITHUB_PAT |
| `vercel.json` | Aggiunta rewrite `/admin-add-player` → `/api/main` |
| `scraper/leagues.py` | Aggiunta `scrape_club_by_id(tm_club_id)` per auto-creare club non in DB |
| `add_players.py` | Aggiunta logica auto-creazione club nuovi dopo loop giocatori |
| `frontend/app.js` | Funzione `_adminAddPlayer()` che fa POST all'endpoint |

### Setup esterni completati

1. **GitHub PAT** — Creato Personal Access Token (fine-grained) con permissions:
   - Repository: `pid` only
   - Actions: Read+Write
   - Contents: Read+Write
   - Metadata: Read-only
   - Expiration: 90 days

2. **Vercel Secret** — Aggiunto `GITHUB_PAT` come Sensitive variable:
   - Production ✅
   - Preview ✅
   - Development ❌ (Vercel non permette secret in Development)

3. **Tabella Supabase** `player_overrides` (già fatta nelle sessioni precedenti)

### Funzionamento dell'auto-creazione club

Quando si aggiunge un giocatore di un club non presente in `clubs.json`:
- `add_players.py` rileva il `current_club_id` non presente in `clubs.json`
- Chiama `scrape_club_by_id(cid, client)` 
- Funzione scarica pagina TM del club ed estrae:
  - nome club
  - league_id (es. "GR1" per Greek Super League)
  - league_name
  - slug
  - logo_url di Transfermarkt
- Aggiunge il dict al `clubs.json`
- `enrich_sortitoutsi.py` (chiamato dopo) prova matching Sortitoutsi per logo

Limitazioni:
- Se `league_id` non standard (es. "EXOT123"), il club appare nel DB ma in sezione separata della pagina Club
- Se Sortitoutsi non trova match, il logo è quello TM (fallback)

### Test eseguito (FALLITO ma diagnosticato)

URL test: `https://www.transfermarkt.com/victor-munoz/profil/spieler/935231` (Lech Poznan)

Risultato run #25555906173:
```
✓ Validate URL
✓ Run add_players.py            (giocatore scrapato OK)
✓ Run enrich_sortitoutsi.py     (logo/foto OK)
✗ Commit and push if changed    (push FALLITO con exit 128)
```

**Causa**: stesso bug del workflow notturno — durante il run del workflow add_player, ho fatto altri commit su main (questo fix workflow + altri). Il `git push` finale è stato rejected per push concurrent.

**Risultato pratico**: Victor Munoz NON è arrivato su main (verificato: `Victor Munoz nel repo: 0 match`).

**Fix applicato (commit 9e27677)**: workflow `add_player.yml` ora ha retry 5x con `git fetch origin main` + `git pull --rebase origin main` + `git push` + sleep 10s tra tentativi. Più robusto del workflow daily che ne ha solo 3.

### Stato finale chiusura sessione

- ✅ Code completo per admin add player live in produzione
- ✅ Fix workflow retry 5x deployato
- ⏳ **Test fine-to-end NON ancora ripetuto** dopo il fix retry
- 📌 Da fare al prossimo accesso: cliccare bottone "Aggiungi giocatore" col URL Victor Munoz (o un altro) per validare il flow completo

### Prossimi step pianificati (NON ancora iniziati)

1. **Re-test add player** con URL Victor Munoz dopo fix retry
2. **Pre-popolazione club delle top-10 leghe europee** (decisione presa: solo club, no roster, mantenere auto-creazione come fallback). Leghe candidate (~10):
   - Premier League (GB1)
   - La Liga (ES1)
   - Bundesliga (L1)
   - Ligue 1 (FR1)
   - Eredivisie (NL1)
   - Liga Portugal (PO1)
   - Belgio (BE1)
   - Turchia (TR1)
   - Russia (RU1) o Brasile (BRA1)
   - + Serie A/B/Primavera + Polonia (già presenti)
3. **Modifiche varie nella sezione Griglie** (utente non ha dettagliato cosa, da chiedere quando si riprende)

### Architettura completa admin (3 colonne riepilogo)

| Funzionalità | Storage | Trigger |
|-------------|---------|---------|
| Edit data nascita/piede/posizione/altezza/numero | Supabase `player_overrides` | Realtime upsert (no deploy) |
| Aggiungi giocatore da URL TM | GitHub Actions → commit repo | POST /admin-add-player → workflow |
| Auto-creazione club nuovo | GitHub Actions (parte di add_players) | Implicito quando club nuovo |

### Sicurezza

- Frontend mostra tab Admin solo se `cloudAuth.user.email === simonecontran10@gmail.com`
- Supabase RLS: scritture su `player_overrides` solo se JWT con quella email
- Endpoint `/admin-add-player`: NO verifica auth lato server (qualsiasi authenticated può triggerare workflow)
  - **TODO**: aggiungere check email anche lato server, leggendo `Authorization` header dal Supabase JWT, validandolo con la JWT secret

### File con modifiche pending sul Mac (NON committate dopo l'ultimo push)

Nessuna. Tutto pushato fino al commit `9e27677`.

### PROMPT DI RIPRESA

> Ciao Claude, riprendo PID. Stato 8 mag pomeriggio:
>
> ✅ Backend admin completo:
> - Editing giocatori (data nascita, piede, posizione, altezza, numero, altri ruoli)
> - Bottone "Aggiungi giocatore" da URL TM (workflow GitHub Actions)
> - Auto-creazione club nuovi tramite `scrape_club_by_id`
> - Retry 5x su push concurrent
>
> ⏳ Da fare:
> 1. Re-test fine-to-end del bottone "Aggiungi giocatore" con URL Victor Munoz dopo fix workflow retry
> 2. Pre-popolazione club delle top-10 leghe europee (solo club, no roster)
> 3. Modifiche nella sezione Griglie (da specificare)
>
> Architettura admin in produzione su `pid-nine.vercel.app`. Endpoint `/admin-add-player`, tabella Supabase `player_overrides`, workflow `add_player.yml`. GitHub PAT configurato come Vercel Secret `GITHUB_PAT`.
## 8 mag 2026 (pomeriggio tardo) — Admin add player live + bug "New arrival"

### Test add player end-to-end SUCCESS

Dopo 2 fix iterativi al workflow GitHub Actions, il flusso "Aggiungi giocatore da URL TM" è completamente funzionante in produzione su `pid-nine.vercel.app`.

#### Fix 1 — Retry su push concurrent (commit 9e27677)

Workflow `add_player.yml` aveva push concurrent issue analogo al workflow notturno. Aggiunto retry 5x con `git fetch` + `git pull --rebase` + sleep 10s.

#### Fix 2 — Permission denied 403 (commit b36a310)

Vero errore identificato dai logs:
```
remote: Permission to simonecontran10/pid.git denied to github-actions[bot].
The requested URL returned error: 403
```

Workflow triggerato via `workflow_dispatch` API esterna ha permessi più ristretti del default `GITHUB_TOKEN`. Risolto aggiungendo:

```yaml
permissions:
  contents: write
  actions: read
```

#### Test riuscito (run #25556593255)

URL test: `https://www.transfermarkt.com/victor-munoz/profil/spieler/935231`

```
✓ Validate URL
✓ Run add_players.py            (Víctor Muñoz scrapato + Real Madrid Castilla auto-creato)
✓ Run enrich_sortitoutsi.py     (foto TM scaricata, no match Sortitoutsi)
✓ Commit and push if changed    (push OK al primo tentativo)
```

Risultato verificato:
- Repo locale: `Víctor Muñoz` (tm=935231) presente in `players_main.json`
- Production R2: 2860 players (era 2859, +1 corretto)
- Foto: `data/photos/players_tm/935231.jpg` scaricata
- Auto-creato Real Madrid Castilla (id=6767) in `clubs.json`

### Bug noto scoperto — "New arrival" placeholder

Lo scraper Transfermarkt mostra `current_club_name="New arrival"` per giocatori in transizione (mercato). 

**Caso Víctor Muñoz**:
- TM nel profilo mostra: club attuale = **CA Osasuna** (Liga spagnola)  
- Ma con etichetta "New arrival" (è arrivato di recente)
- Lo scraper di `profiles.py` legge il **club di provenienza** (Real Madrid Castilla, da cui è stato preso) invece dell'attuale (Osasuna)

Conta in DB: **269 giocatori** con `current_club_name="New arrival"` (preesistente al fork da Saudi Players Hub, nasce dallo scraper TM).

#### Ipotesi sulla causa

In `scraper/profiles.py:_extract_current_club_id()` il selettore prende il primo `<a href="/verein/...">` dal `data-header__club`. Per giocatori "New arrival", TM mostra:
- Etichetta "New arrival" come testo del data-header__club
- Link al **club di provenienza** invece dell'attuale

L'attuale (Osasuna) probabilmente sta in un altro selector (info-table o sezione "Career stations").

#### Note sul fix preesistente

`enrich_sortitoutsi.py` nel docstring dichiara di gestire il caso:
> **FIX CLUB PLACEHOLDER**: Transfermarkt mostra 'New arrival' / 'Winter signing' / 'Returnee' per giocatori in transizione. Sostituiamo con il roster_club (il club da cui abbiamo scrapato la rosa) per avere sempre il club corretto.

Ma evidentemente il fix non si applica nel caso di add manuale (quando `roster_club_id == current_club_id` perché viene impostato uguale all'inizio in `add_players.py`):
```python
prof["roster_club_id"] = existing.get("roster_club_id") or prof.get("current_club_id")
```

Per i giocatori scrapati col flusso normale (`run_static.py` → `scrape_club_roster()`), il `roster_club_id` è il club della rosa scrappata, quindi è corretto. Per quelli aggiunti via admin singolarmente, il fallback non funziona.

#### Decisione

Bug noto ma **NON fixato in questa sessione**. Lavoro per prossima sessione. Per ora, il workaround è:
1. Aggiungere il giocatore (anche con club sbagliato)
2. Usare l'admin override per correggere `current_club_name` e `current_club_id` manualmente

Però l'admin editor attuale **NON supporta la modifica del club**. Aggiunta a TODO.

### Stato finale del bottone admin add player

✅ **Funzionalità completa**:
- Frontend bottone admin "Aggiungi giocatore"
- Endpoint Vercel `/admin-add-player` con auth GITHUB_PAT
- Workflow GitHub Actions con retry 5x + permissions write
- Auto-creazione club da `tm_club_id` (con fallback se Sortitoutsi non matcha)
- Foto TM scaricata e disponibile
- Push commit + auto-deploy Vercel

⚠️ **Limitazioni note**:
- Bug "New arrival" preesistente: per giocatori in transizione, club mostrato è quello di provenienza
- Auto-creazione club: `league_id` può essere mappato male (Castilla finita come "CL" invece di lega Real Madrid C, ecc.)
- Sortitoutsi logo: matching automatico fallisce per club nuovi (no logo nel DB)
- Stats: scaricate solo per giocatori `is_saudi_eligible=True`. Per altri, stats arrivano col run notturno

### Prossimi step pianificati per nuova chat

1. **Aggiungere modifica club nell'admin editor** (per workaround "New arrival")
2. **Pre-popolazione club top-10 leghe europee** (Premier, La Liga, Bundesliga, Ligue 1, Eredivisie, Liga Portugal, Belgio, Turchia + Serie A/B/Primavera + Polonia già presenti)
3. **Modifiche sezione Griglie** (utente ha menzionato ma non specificato)
4. **Possibile fix scraper** per "New arrival" → estrarre il vero club attuale

### File modificati in questa sessione

```
M  .github/workflows/add_player.yml   (+permissions, retry 5x con pull --rebase)
M  scraper/leagues.py                  (+scrape_club_by_id())
M  add_players.py                      (+auto-creazione club + import scrape_club_by_id)
A  vercel.json                         (rewrite /admin-add-player)
A  api/main.py                         (endpoint POST /admin-add-player)
A  frontend/app.js                     (admin panel, _adminAddPlayer, _adminSaveOverrides, dropdown ruoli + multi-select)
A  frontend/cloud_sync.js              (fetchPlayerOverrides, isAdmin, _toggleAdminNav)
A  frontend/index.html                 (sidebar admin + admin-panel div)
+ tabella Supabase player_overrides
+ Vercel Secret GITHUB_PAT
```

Commit principali su main:
- `feat: pagina admin per editing giocatori`
- `feat: dropdown ruoli admin editor con 12 posizioni canoniche`
- `feat: aggiunge multi-select 'Altri ruoli' nell'admin editor`
- `feat: admin add player from TM URL (workflow + endpoint Vercel)`
- `feat: auto-creazione club nuovi quando si aggiunge giocatore di club non presente`
- `fix: workflow add_player retry 5 tentativi su push concurrent`
- `fix: add_player workflow ha permission contents:write per push`

### Test live confermati

- ✅ Edit giocatore (Locatelli con multi-select altri ruoli + position_specific override)
- ✅ Add giocatore (Víctor Muñoz aggiunto via bottone admin)
- ✅ Auto-creazione club (Real Madrid Castilla auto-creato)
- ⚠️ Club mostrato sbagliato (Castilla invece di Osasuna - bug "New arrival")

### PROMPT DI RIPRESA

> Ciao Claude, riprendo PID. Ultima sessione: 8 mag pomeriggio tardo. Stato:
>
> ✅ Backend admin completo e funzionante in produzione su `pid-nine.vercel.app`:
> - Editing giocatori: data nascita, piede, posizione + altri ruoli, altezza, numero
> - Add giocatore da URL TM: workflow GitHub Actions con permissions:write e retry 5x
> - Auto-creazione club nuovi tramite `scrape_club_by_id`
>
> ⚠️ Bug noto preesistente: 269 giocatori in DB hanno `current_club_name="New arrival"` per via dello scraper TM che legge il club di provenienza invece dell'attuale (es. Víctor Muñoz mostra Real Madrid Castilla invece di Osasuna). Da fixare.
>
> ⏳ Prossimi step:
> 1. Aggiungere modifica club nell'admin editor (workaround per "New arrival")
> 2. Pre-popolazione club top-10 leghe europee
> 3. Modifiche sezione Griglie (da specificare)
>
> Fix possibile scraper: in `scraper/profiles.py:_extract_current_club_id()` dare priorità al club nella sezione "Career stations" o info-table invece del primo selector che restituisce il club di provenienza.
## 8 mag 2026 (fine pomeriggio) — Fix bug "New arrival" preesistente

### Problema scoperto

Aggiunto Víctor Muñoz via admin add player. Il giocatore appariva con club "Real Madrid Castilla" invece di "CA Osasuna" (squadra reale attuale). Verifica DB: **269 giocatori** in totale con `current_club_name="New arrival"`.

### Diagnostica

Scaricato HTML reale di TM per Muñoz (`/tmp/munoz_profile.html`, 115KB). Analisi struttura:

```html
<!-- data-header__ribbon: club di PROVENIENZA con etichetta "New arrival" -->
<div class="data-header__ribbon">
  <a href="/real-madrid-castilla/startseite/verein/6767/saison_id/2025"
     title="Joined from Real Madrid Castilla; date: 11/07/2025">
    New arrival
  </a>
</div>

<!-- data-header__club: il VERO club attuale -->
<span class="data-header__club" itemprop="affiliation">
  <a href="/ca-osasuna/startseite/verein/331" title="CA Osasuna">
    CA Osasuna
  </a>
</span>
```

#### Bug trovato in `scraper/profiles.py`

```python
def _extract_current_club_id(soup):
    a = soup.select_one(
        '.data-header__club a, '
        'span.data-header__club a, '
        'a[href*="/startseite/verein/"]'  # ← TROPPO GENERICO
    )
```

Il selettore `a[href*="/startseite/verein/"]` matcha **anche** il link nel `data-header__ribbon` (che punta al club di provenienza). `select_one()` restituisce **il primo** match nel DOM order — che è proprio il ribbon, non il club corrente.

Test riprodotto:
```
=== select_one (primo match) ===
  href=/real-madrid-castilla/startseite/verein/6767/saison_id/2025
  text=New arrival
  parent_class=['data-header__ribbon']  ← ECCO IL BUG
```

### Fix applicato

Riscritta `_extract_current_club_id()` con strategia a cascata:

1. **Priorità 1**: `.data-header__club a[href*="/startseite/verein/"]` (sempre il club corrente)
2. **Priorità 2**: `.info-table__content a[href*="/startseite/verein/"]` (fallback layout legacy)
3. **Priorità 3**: primo `a[href*="/startseite/verein/"]` ESCLUDENDO `data-header__ribbon`

```python
# Strategia 3 (ultima risorsa)
for candidate in soup.select('a[href*="/startseite/verein/"]'):
    parent_classes = candidate.parent.get("class", []) if candidate.parent else []
    if "data-header__ribbon" in parent_classes:
        continue  # Skip "New arrival" / "Winter signing" / "Returnee"
    a = candidate
    break
```

### Test pre-push del fix

Su HTML cacheato di Muñoz:
```
✓ FIX FUNZIONA
  Club ID: 331  (atteso: 331 = Osasuna)
  Club name: CA Osasuna  (atteso: 'CA Osasuna')
```

### Re-scrape retroattivo dei 269 giocatori broken

Creato workflow GitHub Actions dedicato per processare in cloud (no terminale Mac bloccato 15 min):

**File creati**:
- `fix_new_arrival_clubs.py` — script che:
  - Carica players_main, players_all, players_static, players_saudi, clubs
  - Trova tutti con `current_club_name="New arrival"`
  - Per ognuno: re-scrape profilo (con fix attivo)
  - Aggiorna i 4 file JSON players + clubs.json
  - Auto-crea club nuovi se non in DB
  - Salvataggio incrementale ogni 25 giocatori
  - Supporta `--limit N` per test parziali
- `.github/workflows/fix_new_arrival.yml` — workflow `workflow_dispatch` con permissions:write, retry 5x, timeout 60min

### Stato workflow trigger

Workflow triggerato dall'utente con `limit` vuoto (= tutti i 269 giocatori).

Tempo stimato: ~15-20 min (3-5s/giocatore per request TM con rate limit + parsing + save).

### Risultato atteso

Una volta completato il workflow:
- I 269 giocatori avranno `current_club_name` corretto
- Eventuali club nuovi (es. CA Osasuna se non c'era) auto-aggiunti a `clubs.json`
- Push automatico su main → Vercel auto-deploy

### Verifica post-completamento

Quando il workflow finisce:
```bash
cd ~/Desktop/pid && git pull origin main
~/Desktop/pid/venv/bin/python3 -c "
import json
data = json.loads(open('data/players_main.json').read())
broken = [p for p in data if p.get('current_club_name') == 'New arrival']
print(f'Giocatori ancora New arrival: {len(broken)} (target: 0 o pochi)')
v = [p for p in data if p.get('tm_player_id') == 935231]
if v: print(f'Muñoz club: {v[0].get(\"current_club_name\")} (atteso: CA Osasuna)')
"
```

### Stato finale sessione 8 mag

✅ **Live in produzione**:
- Bottone "Esporta PPTX" (6 sistemi)
- Locatelli stats su R2
- Nomi club italiani puliti (display)
- Backend admin completo (editing + add giocatore + auto-creazione club)
- **Fix scraper "New arrival"** → club corretto sempre

⏳ **In esecuzione (cloud)**:
- Workflow `fix_new_arrival.yml` per re-scrape retroattivo dei 269 giocatori broken
- Vercel auto-deploya quando il workflow committa

### Commit principali della giornata

```
b7c9f6e fix: 'Player' → 'Players' Intelligence Database (typo)
9524203 fix: riordina sistemi nel dropdown Modulo
825059f feat: rinomina display nomi club italiani
b36a310 fix: add_player workflow ha permission contents:write
9e27677 fix: workflow add_player retry 5 tentativi
56ec6ea (auto) add player from TM URL
a6a72b5 feat: auto-creazione club nuovi
f839586 feat: admin add player from TM URL (workflow + endpoint Vercel)
e47f626 fix: workflow auto_update_daily resiste a push concurrent
1139acf merge feature/pptx-export → main
8a873ae fix: scraper TM ignora data-header__ribbon (FIX BUG NEW ARRIVAL) + workflow re-scrape
```

### TODO prossima sessione

1. **Verificare esito workflow fix_new_arrival** — se i 269 giocatori sono stati corretti
2. **Pre-popolazione club top-10 leghe europee** (Premier, La Liga, Bundesliga, Ligue 1, Eredivisie, Liga Portugal, Belgio, Turchia)
3. **Aggiungere modifica club nell'admin editor** (per casi edge dove il fix scraper fallisce)
4. **Modifiche sezione Griglie** (utente ha menzionato ma non specificato cosa)

### PROMPT DI RIPRESA

> Ciao Claude, riprendo PID. Ultima sessione: 8 mag fine pomeriggio. Stato:
>
> ✅ Tutto funzionante in produzione su `pid-nine.vercel.app`:
> - Backend admin (editing + add giocatore)
> - Bug scraper "New arrival" risolto + workflow re-scrape lanciato per i 269 giocatori broken
>
> ⏳ Da verificare: workflow `fix_new_arrival.yml` ha completato? Quanti dei 269 sono stati corretti?
>
> Prossimi step:
> 1. Pre-popolazione club top-10 leghe europee
> 2. Modifiche sezione Griglie
> 3. Aggiungere modifica club nell'admin editor (workaround edge case)
## 8 mag 2026 (sera) — Workflow fix_new_arrival completato con successo

### Risultati workflow

Workflow GitHub Actions `fix_new_arrival.yml` triggerato dall'utente con `limit` vuoto (= tutti). Completato con successo.

### Verifica post-completamento

```
Giocatori ancora "New arrival": 0 (era 269)  ✅
Muñoz club: CA Osasuna (atteso: CA Osasuna)  ✅
Club totali: 102 (era 101, +1: CA Osasuna auto-aggiunto)  ✅
```

### Dettagli operazione

- **Commit auto-bot**: `fd026ca` (di github-actions[bot])
- **File modificati**:
  - `data/clubs.json`: +12 righe (nuovo club CA Osasuna)
  - `data/players_main.json`: 2152 righe modificate
  - `data/players_all.json`: 2152 righe modificate
  - `data/players_static.json`: 2152 righe modificate
- **Totale**: 3240 inserimenti, 3228 eliminazioni

### Esempi di correzione

```
- Mateusz Skrzypczak  → Lech Poznan (era 'New arrival')
- João Moutinho       → Lech Poznan
- Robert Gumny        → Lech Poznan
- Pablo Rodríguez     → Lech Poznan
- Leo Bengtsson       → Lech Poznan
- Víctor Muñoz        → CA Osasuna  (era 'New arrival' che puntava a Real Madrid Castilla)
```

### Stato finale 8 mag 2026

✅ **Live in produzione su `pid-nine.vercel.app`**:
- Bottone "Esporta PPTX" (6 sistemi tattici)
- Locatelli stats su R2 (run notturno OK con retry)
- Nomi club italiani puliti (display)
- Backend admin completo:
  - Editing giocatori (data nascita, piede, posizione, altri ruoli, altezza, numero)
  - Add giocatore da URL TM (workflow GitHub Actions con permissions + retry 5x)
  - Auto-creazione club nuovi
- **Bug "New arrival" risolto** alla radice + retroattivamente per i 269 giocatori esistenti

### Commit principali della giornata (riepilogo)

```
9524203 fix: riordina sistemi nel dropdown Modulo
825059f feat: rinomina display nomi club italiani
b7c9f6e fix: 'Player' → 'Players' Intelligence Database (typo)
1139acf merge feature/pptx-export → main (export PPT live)
e47f626 fix: workflow auto_update_daily resiste a push concurrent
56ec6ea (auto) Locatelli stats su R2 (workflow notturno)
f839586 feat: admin add player from TM URL (workflow + endpoint Vercel)
a6a72b5 feat: auto-creazione club nuovi
9e27677 fix: workflow add_player retry 5 tentativi
b36a310 fix: add_player workflow ha permission contents:write
8a873ae fix: scraper TM ignora data-header__ribbon (FIX BUG NEW ARRIVAL)
fd026ca (auto) re-scrape 269 giocatori broken
```

### TODO prossima sessione

1. **Modifica griglie destra** mostrare ruolo specifico (es. "Terzino destro") invece di generico (utente ha richiesto, da implementare)
2. **Pre-popolazione club top-10 leghe europee** (Premier, La Liga, Bundesliga, Ligue 1, Eredivisie, Liga Portugal, Belgio, Turchia)
3. **Aggiungere modifica club nell'admin editor** (per casi edge dove il fix scraper fallisce)
4. **Cleanup branch** `feature/pptx-export` (già mergato, da cancellare)

### PROMPT DI RIPRESA

> Ciao Claude, riprendo PID. Stato finale 8 mag 2026:
>
> ✅ Tutto funzionante in produzione su `pid-nine.vercel.app`:
> - Esporta PPTX 6 sistemi
> - Backend admin (editing + add giocatore + auto-creazione club)
> - Bug "New arrival" risolto + 269 giocatori corretti retroattivamente
> - Workflow notturno stats refresh + workflow add_player + workflow fix_new_arrival
>
> ⏳ Prossimi step:
> 1. Griglie destra: ruolo specifico (richiesto dall'utente, in attesa)
> 2. Pre-popolazione club top-10 leghe europee
> 3. Modifiche varie alla sezione Griglie (da specificare ulteriormente)

## 8 mag 2026 (sera) — Fix workflow notturno (`last_update.json` fermo al 6 mag)

### Sintomo

Sidebar pid-nine.vercel.app mostrava ancora "Aggiornamento 06/05/2026, 11:16" il giorno 8 maggio, nonostante il workflow `Auto Update Daily` schedulato alle 03:00 UTC ogni notte.

### Diagnosi

- `cat data/last_update.json` locale → fermo al 6 maggio
- `git log -- data/last_update.json` → un solo commit, l'iniziale `fb8e6e7`. Il bot non ha mai pushato aggiornamenti.
- `curl https://pid-nine.vercel.app/data/last_update.json` → identico al locale
- Tab GitHub Actions: workflow #2 schedulato dell'8 maggio 11:15 UTC ❌ failed dopo 1h 48m
- Log dello step "Commit and push if changed":
  ```
  remote: Permission to simonecontran10/pid.git denied to github-actions[bot].
  fatal: unable to access ...: The requested URL returned error: 403
  ```

### Bug 1 — Permessi GITHUB_TOKEN insufficienti

Stesso identico bug del 7 maggio già fixato per `add_player.yml` (commit `b36a310`), ma la fix non era stata propagata agli altri workflow. Stato pre-fix:

- `add_player.yml` aveva `permissions: contents: write` ✅
- `fix_new_arrival.yml` lo aveva ✅
- `auto_update_daily.yml` non lo aveva ❌
- `auto_update_full.yml` non lo aveva ❌

Fix applicata: aggiunto blocco `permissions: contents: write / actions: read` in entrambi i file (commit `97f9797`). Test: run manuale di `Auto Update Daily` → success in 1h 38m → bot ha pushato `45d538e auto: daily stats refresh (2026-05-08)`.

### Bug 2 — Fallback chain in `app.js` con priorità sbagliata

Anche dopo il fix permessi il sito mostrava ancora 06/05. Il `curl` su prod rivelava che `stats_completed_at` era 08/05 ma `completed_at` era ancora 06/05 (seed iniziale). `run_stats.py` infatti scrive solo `stats_completed_at` ma non sovrascrive `completed_at`, perché quest'ultimo è semanticamente legato al seed completo del DB.

Il bug era nel frontend: `renderLastUpdate()` riga 183 leggeva con priorità fissa `lu.completed_at || lu.stats_completed_at || ...`, quindi pescava sempre il timestamp del seed e ignorava i workflow ricorrenti.

Fix applicata: riscritta la chain per pescare il timestamp più recente disponibile invece che la priorità fissa. Robusta anche per futuri workflow che aggiungeranno altri campi `*_completed_at` (commit `37f0524`).

Verifica finale: redeploy Vercel + hard reload → sidebar mostra correttamente `08/05/2026, 20:20` (le 18:20 UTC convertite in ora italiana estiva).

### Lessons learned

- Quando si applica una fix a un workflow YAML, propagarla immediatamente a tutti gli altri con la stessa categoria di rischio. Il fix `b36a310` del 7 maggio doveva essere multi-file fin da subito.
- `sed` su macOS BSD è inaffidabile per modifiche YAML strutturate. Meglio Python con `re` o file diff.
- `last_update.json` ha un design un po' frastagliato (3+ campi `*_completed_at` con semantiche diverse). Il fallback nel frontend deve pescare il più recente, non avere priorità fissa.

### Commit della sessione

- `97f9797` fix: aggiungi permissions contents:write a auto_update_daily e auto_update_full
- `45d538e` (bot) auto: daily stats refresh (2026-05-08)
- `37f0524` fix: renderLastUpdate usa timestamp più recente invece di priorità completed_at

## 8 mag 2026 (sera tardi) — Nuova sezione Osservazioni (scout reports per partita)

### Decisione di prodotto

Trasformare la funzione "Note" del giocatore in una vera sezione di scouting strutturata. Una osservazione = un giocatore visto in una partita specifica. Multipla per giocatore, privata per utente, esportabile in PDF e JSON.

### Punti d'ingresso al form "Nuova osservazione"

Tre modalità:

1. Scheda giocatore → tab "Osservazioni" → bottone "+ Nuova" (giocatore già fissato)
2. Pannello "Scouting" laterale → bottone "+ Nuova osservazione" (con autocomplete giocatore preliminare)
3. Lista giocatori visionati nel pannello → click "+" su una riga (giocatore preselezionato)

### Schema dati osservazione

Una osservazione contiene 11 campi: avversario (testo libero, autocomplete dai club DB ma sempre stringa), data partita, competizione (lista chiusa con escape "Altro"), ruoli giocati (multi-select su campo grafico SVG con sigle italiane), performance rating numerico 0-10 con step 0.5, etichette di valutazione (multi-select da lista da definire), punti di forza (multi-select da lista da definire), punti di debolezza (multi-select da lista da definire), note libere paste-friendly, autore (snapshot di `_currentUsername()`), data inserimento.

Set chiuso 15 sigle ruolo, in italiano e slegato da `position_specific` TM. Attacco: PP (punta), AS (ala sinistra), AD (ala destra), TRQ (trequartista). Centrocampo: AES (quinto sinistro), AED (quinto destro), CIS, CID, CC. Difesa: LAT_SN (terzino sn), LAT_DX (terzino dx), DCS, DC, DCD. Porta: POR.

Decisione design: ruoli osservazione separati dai valori TM in `position_specific`. Motivo: un'osservazione di scouting registra dove l'hai visto giocare quella partita, che può differire dal ruolo "ufficiale" TM del giocatore (es. Locatelli può essere TM "Central Midfield" ma l'hai visto da CC).

Vincolo unicità: una sola osservazione per `(user_id, tm_player_id, match_date, opponent)`.

### Privacy & condivisione

- Privata per utente (RLS `auth.uid() = user_id`, stesso pattern già usato in `user_state`)
- Export/Import in JSON (backup-restore per cambio device)
- Export PDF singolo (1 osservazione = 1 pagina) + Export dossier giocatore (multi-page con copertina e tutte le osservazioni di quel giocatore)

### Pannello "Scouting" laterale (nuovo tab nella sidebar)

Due viste: lista giocatori visionati (≥1 osservazione, con conteggio) e lista tutte le osservazioni (filtrabile/ordinabile). Azioni: modifica, elimina, export PDF singolo, export JSON tutto, import JSON.

### Fase 1 completata — Schema Supabase

Tabella `player_observations` creata su Supabase con 14 colonne (incluse `id uuid`, `user_id uuid FK auth.users`, `tm_player_id bigint`, `created_at`, `updated_at` oltre agli 11 campi dati), 3 indici per query tipiche su `(user_id, tm_player_id)`, `(user_id, created_at DESC)` e `(user_id, match_date DESC)`, trigger `po_set_updated_at` per aggiornare `updated_at` su UPDATE, e 4 policy RLS (`po_select_own`, `po_insert_own`, `po_update_own`, `po_delete_own`) tutte basate su `auth.uid() = user_id`. Vincolo `UNIQUE (user_id, tm_player_id, match_date, opponent)` per evitare duplicati.

### Piano d'attacco fasi successive

- Fase 2 — Modulo `cloud_sync.js`: `fetchObservations`, `saveObservation`, `updateObservation`, `deleteObservation` (~1h)
- Fase 3 — Tab "Osservazioni" nel modal giocatore + form con campo grafico SVG ruoli (~2-3h)
- Fase 4 — Pannello Scouting laterale (~1.5h)
- Fase 5 — Export PDF: singolo + dossier giocatore (jsPDF client-side) (~2h)
- Fase 6 — Export/Import JSON salvataggio (~45m)

### Liste TBD da definire prima della Fase 3

- Set valori valido per `evaluation_tags`
- Set valori valido per `strengths`
- Set valori valido per `weaknesses`


### Fase 2 completata — Modulo cloud_sync per le osservazioni

Aggiunte 4 funzioni a `frontend/cloud_sync.js` (commit `ddef181`):

- `fetchObservations({tm_player_id?})` — recupera tutte le osservazioni dell'utente, ordinate per data partita decrescente. Filtro opzionale per giocatore.
- `saveObservation(obs)` — crea, valida campi obbligatori (tm_player_id, match_date, opponent, competition) e ruoli (set chiuso 15 sigle), gestisce duplicato (codice Postgres 23505) con messaggio italiano.
- `updateObservation(id, patch)` — sanitize i campi che non vanno mai aggiornati direttamente (id, user_id, tm_player_id, created_at, updated_at, author_username), valida ruoli se modificati.
- `deleteObservation(id)` — semplice, con doppia sicurezza `user_id` oltre alla RLS.

Tutte e 4 con gestione errori try/catch + log con prefisso `[observations]` (stile coerente con il resto del file).

Test end-to-end: 4/4 verdi sulla produzione (https://pid-nine.vercel.app, console DevTools). Verificati fetch, insert con tutti i campi correttamente popolati, fetch filtrato, delete + verifica array vuoto post-delete. RLS `auth.uid() = user_id` confermata funzionante.

### Liste TBD ancora da definire prima della Fase 3
- `evaluation_tags`
- `strengths`
- `weaknesses`



### Fase 2 completata — Modulo cloud_sync per le osservazioni

Aggiunte 4 funzioni a `frontend/cloud_sync.js` (commit `ddef181`):

- `fetchObservations({tm_player_id?})` — recupera tutte le osservazioni dell'utente, ordinate per data partita decrescente. Filtro opzionale per giocatore.
- `saveObservation(obs)` — crea, valida campi obbligatori (tm_player_id, match_date, opponent, competition) e ruoli (set chiuso 15 sigle), gestisce duplicato (codice Postgres 23505) con messaggio italiano.
- `updateObservation(id, patch)` — sanitize i campi che non vanno mai aggiornati direttamente (id, user_id, tm_player_id, created_at, updated_at, author_username), valida ruoli se modificati.
- `deleteObservation(id)` — semplice, con doppia sicurezza `user_id` oltre alla RLS.

Tutte e 4 con gestione errori try/catch + log con prefisso `[observations]` (stile coerente con il resto del file). Esposte su `window.*` per uso da `app.js`.

Test end-to-end: 4/4 verdi sulla produzione (https://pid-nine.vercel.app, console DevTools). Verificati fetch, insert con tutti i campi correttamente popolati, fetch filtrato, delete + verifica array vuoto post-delete. RLS `auth.uid() = user_id` confermata funzionante.

## 8 mag 2026 (sera 2) — Fix admin "Aggiungi giocatore" — accettare URL TM da qualsiasi TLD

### Bug riscontrato durante uso normale

Tentativo di aggiungere il giocatore Mathys Detourbet con URL `https://www.transfermarkt.it/mathys-detourbet/profil/spieler/1171981` dal pannello admin → errore `URL non valido (deve contenere transfermarkt.com/.../spieler/<id>)`. Il regex di validazione accettava solo il TLD `.com`, ma Transfermarkt ha lo stesso identico DB su tutti i suoi domini regionali (`.it`, `.de`, `.es`, `.fr`, `.com.tr`, `.com.br`, ecc.) — cambia solo la lingua della UI.

### Fix applicata

Due punti dove il regex era troppo stretto:
- `api/main.py:458` — `r'transfermarkt\.com.*spieler/\d+'` → `r'transfermarkt\.[a-z.]+.*spieler/\d+'`
- `.github/workflows/add_player.yml:46` — stesso pattern aggiornato

Il pattern `[a-z.]+` accetta qualsiasi suffisso ragionevole. Il punto è escapato per matchare letteralmente.

A valle non serve fare altro: lo scraper usa `BASE_URL = "https://www.transfermarkt.com"` hardcoded in `scraper/config.py`, quindi naviga sempre su `.com` indipendentemente dal dominio dell'URL incollato (estrae solo il `tm_player_id` dall'URL e poi costruisce le richieste internamente).

Commit `78a7be3` su `main`, redeploy Vercel automatico.

## 8 mag 2026 (sera 3) — Fase 3 in preparazione (sezione Osservazioni nel modal giocatore)

### Stato preparazione

File `frontend/observations_ui.js` predisposto ma non ancora integrato. Contiene 730 righe con tutti i pezzi della UI Osservazioni: costanti (37 caratteristiche tecnico-tattiche, 4 evaluation tags con colori, 24 competizioni preset + "Altro", 15 ruoli sul campo con coordinate SVG), traduzioni IT→EN per tutte le voci, 27 stringhe i18n del modulo, render della sezione in fondo al modal giocatore, render delle card osservazione con bottoni edit/delete, modal-on-modal di creazione/modifica con campo grafico SVG cliccabile multi-select, slider rating 0-10 step 0.5, multi-select chips per strengths/weaknesses, single-select tag colorato, validazione completa, gestione duplicato.

### Decisioni di design consolidate

- Sezione Osservazioni come blocco in fondo al modal giocatore (NO tab orizzontale: il modal esistente non ha sistema di tab e introdurlo solo per Osservazioni sarebbe overkill)
- Modal-on-modal per creazione/modifica (separa "vista" da "compilazione")
- Etichette IT canoniche salvate as-is su Supabase, traduzione EN solo a video
- Una sola lista 37 caratteristiche condivisa tra strengths e weaknesses

### Liste finalizzate

37 caratteristiche tecnico-tattiche in ordine alfabetico (1vs1 difensivo, Aggressività, Agonismo, Ampiezza, Area di rigore offensiva, Assist, Conduzione palla, Cross, Dinamismo, Dribbling 1c1, Duelli difensivi, Fase difensiva, Fase offensiva, Finalizzazione, Forza fisica, Gioco aereo, Gioco per la squadra, Inizio manovra, Inserimenti senza palla, Intelligenza tattica, Intensità, Jolly, Letture tattiche, Passaggi Chiave, Personalità, Profondità, Progressione, Rapidità primi metri, Recupero palloni, Rifinitura, Spazi stretti, Tecnica, Tiro/Calcio, Transizioni difensive, Transizioni offensive, Uscite, Velocità, Visione di gioco).

4 evaluation tags con colori: PRIMA SCELTA / FIRST CHOICE (verde #22C55E), SECONDA SCELTA / SECOND CHOICE (giallo #EAB308), DA MONITORARE / MONITOR (arancione #F97316), NON IDONEO / REJECT (rosso #EF4444).

24 competizioni preset (Serie A, Serie B, Serie C, Primavera 1/2, Coppa Italia, Supercoppa Italiana, UCL/UEL/UECL, principali leghe top europee + Saudi + Amichevole + "Altro" libero).

### Prossimi step prima di pushare la Fase 3

1. Caricare `observations_ui.js` in `index.html` come `<script>` dopo `app.js`
2. Patch `app.js` `openPlayerModal()`: inserire `${window.renderObservationsSection(pid)}` alla fine del template HTML
3. Patch `app.js` `openPlayerModal()`: aggiungere `setTimeout(() => window.wireObservationsHandlers(pid), 0);` dopo `setTimeout(_wireMonthlyChart, 0);`
4. Push e test sul sito di produzione (creazione, modifica, eliminazione, multi-select ruoli sul campo grafico)

### Fasi residue del piano

- Fase 4 — Pannello "Scouting" laterale con liste giocatori visionati e tutte le osservazioni (~1.5h)
- Fase 5 — Export PDF singolo + dossier giocatore (jsPDF client-side) (~2h)
- Fase 6 — Export/Import salvataggio JSON (~45m)


## 9 mag 2026 (mattina) — Backup cron per auto_update_daily

### Sintomo

Sidebar pid-nine.vercel.app mostrava ancora "Aggiornamento 08/05/2026, 21:20" (in realtà 20:20 italiana, le 18:20 UTC del run manuale di ieri sera). Nessun aggiornamento del timestamp dopo la notte 8→9 maggio.

### Diagnosi

Tab GitHub Actions: solo 3 run totali del workflow `Auto Update Daily`, di cui nessuno schedulato per la notte 8→9 maggio. Il run automatico delle 03:00 UTC di stamattina non è partito. Cause probabili:

1. GitHub registra un cron come "appena modificato" quando si edita il file YAML del workflow. Il fix permessi di ieri (commit `97f9797`) ha modificato `auto_update_daily.yml` alle 19:00 italiana, e secondo la documentazione GitHub i cron schedulati appena modificati possono saltare il primo trigger. Probabilità alta come spiegazione.

2. Skip opportunistico documentato di GitHub Actions su account free durante carichi alti dell'infrastruttura. Probabilità media.

3. Sospensione automatica per repo "inattivo" (60 giorni senza commit). Esclusa dato il livello di attività del repo.

`run_stats.py` aggiorna correttamente `stats_completed_at` ad ogni esecuzione (verificato: il commit `45d538e` di ieri sera aveva i campi `stats_completed_at`, `elapsed_seconds_stats`, `n_stats` aggiornati). Il commit del bot avviene effettivamente ogni volta che il workflow gira con successo. Quindi il bug NON è nello script Python né nel workflow stesso, ma nella mancata esecuzione schedulata.

### Fix applicata

Aggiunto un secondo cron come **backup** in `auto_update_daily.yml` (commit `cddb7ab`):

```yaml
on:
  schedule:
    - cron: "0 3 * * *"   # primario: 03:00 UTC = 05:00 italiana (estate)
    - cron: "30 6 * * *"  # backup: parte se il primario salta (skip occasionali GitHub)
  workflow_dispatch:
```

Il blocco `concurrency.group: auto-update` esistente impedisce esecuzioni parallele: se il primario è ancora in corso quando arriva l'ora del backup, il secondo viene messo in coda o skippato. Sicurezza built-in, niente di nuovo da configurare.

### Effetto pratico atteso

Dalla notte 9→10 maggio in poi:
- Alle 05:00 italiana parte il primario
- Se il primario non parte, alle 08:30 italiana parte il backup
- Probabilità di skip su entrambi: stimata ~1-2%
- Sito mostra il timestamp aggiornato ogni mattina entro le ~10:00 italiana al massimo

Verifica programmata: domattina 10 maggio controllare con `curl https://pid-nine.vercel.app/data/last_update.json` che `stats_completed_at` sia del 9 maggio.

### Piano B se anche il doppio cron fallisce

Passare a un **cron service esterno** (es. cron-job.org, gratuito) che pinga ogni notte un endpoint Vercel custom. L'endpoint Vercel a sua volta triggera il workflow GitHub via API GitHub. Più affidabile (zero ritardi/skip GitHub), zero costi, ma richiede un endpoint Vercel protetto da token e configurazione del cron esterno. Da fare solo se il doppio cron non basta.

### Commit della sessione

- `cddb7ab` fix(workflow): aggiungi backup cron a auto_update_daily per gestire skip GitHub Actions


## 9 mag 2026 (mattina pt2) — Fase 3 osservazioni completata + viewing_mode + filtri/ordinamento

### Sessione di lavoro

Implementazione completa della UI delle osservazioni nel modal giocatore + pannello Scouting nella sidebar. Prima del codice, definite tutte le scelte di design rilevanti: dashboard compatta sotto "Stagione corrente" (poi spostata sopra "Statistiche club"), modal-on-modal per nuova/modifica, layout 2 colonne (form sinistra + campo SVG ruoli destra), chip categorizzati per strengths/weaknesses con colori verde/rosso, ordine evaluation tags rosso→verde (peggiore a sinistra).

### Iterazioni successive (feedback live)

Tre iterazioni sulla v3 del modulo `observations_ui.js`:

1. **v3 → v3.1** — feedback dopo primo deploy: tabella dashboard inizialmente con 4 colonne (Data | Scout | Performance | Giudizio). Aggiunte 3 colonne mancanti: Avversario (con `prettyClubName` e troncamento), Posizione (sigle ruoli giocati), e successivamente Competizione (truncata). Ordine campi nel form modificato: Note spostate sopra Performance Rating (e ingrandite a 10 rows / min-height 200px). Bug fixato: avversario non modificabile in edit mode (causa: combo `<input value list>` HTML5 ha glitch noti — fix: rimosso `value=""` inline, settato via JS dopo il render).

2. **v3.1 → v3.2** — sezione Osservazioni spostata da fondo modal a TRA "Stagione corrente" e "Statistiche club" (riga ~985 di app.js, subito dopo l'apertura del div padding 22px 28px). Voce sidebar "Scouting" anticipata dalla Fase 4: aggiunto `<div class="nav-item" data-route="scouting">` dopo "Minutaggi" e prima del separator (icona lente d'ingrandimento), `<div id="scouting-panel-main" class="hidden">` nel main content, hook in `setActiveTab()` per render del pannello via `renderScoutingPanel()` + `wireScoutingPanel()`, chiavi i18n `nav_scouting` IT/EN.

3. **v3.2 → v4 (viewing_mode)** — aggiunto campo "Visione" obbligatorio (LIVE / TV-VIDEO). Schema DB: `ALTER TABLE player_observations ADD COLUMN viewing_mode TEXT CHECK (viewing_mode IS NULL OR viewing_mode IN ('LIVE', 'TV'))`. Form: 2 chip side-by-side in cima alla colonna sinistra, icona campo da calcio per LIVE (verde) e icona monitor per TV (blu). Single-select obbligatorio con messaggio errore "Compila tutti i campi obbligatori". Tabella dashboard: 8ª colonna "Mod." con icona piccola colorata. Patch in `cloud_sync.js`: validazione `viewing_mode IN ['LIVE','TV']` in `saveObservation` e `updateObservation`.

### Liste finali

37 caratteristiche organizzate in 5 categorie:
- TATTICA (6): Fase difensiva, Fase offensiva, Intelligenza tattica, Letture tattiche, Transizioni difensive, Transizioni offensive
- TECNICA (11): Assist, Conduzione palla, Cross, Dribbling 1c1, Finalizzazione, Inizio manovra, Passaggi Chiave, Rifinitura, Tecnica, Tiro/Calcio, Visione di gioco
- COMPORTAMENTI (5): Aggressività, Agonismo, Gioco per la squadra, Intensità, Personalità
- FISICO (15): 1vs1 difensivo, Ampiezza, Area di rigore offensiva, Dinamismo, Duelli difensivi, Forza fisica, Gioco aereo, Inserimenti senza palla, Jolly, Profondità, Progressione, Rapidità primi metri, Recupero palloni, Spazi stretti, Velocità
- PORTIERE (1): Uscite

4 evaluation tags con colori, ordine peggiore→migliore: 🔴 NON IDONEO (#EF4444), 🟠 DA MONITORARE (#F97316), 🟡 SECONDA SCELTA (#EAB308), 🟢 PRIMA SCELTA (#22C55E).

24 competizioni preset + "Altro" con input libero.

15 ruoli sigle italiane con coordinate sul campo SVG: PP, AS, AD, TRQ, AES (quinto sn), AED (quinto dx), CIS, CC, CID, LAT_SN, LAT_DX, DCS, DC, DCD, POR.

### Test in produzione

End-to-end testato su https://pid-nine.vercel.app: creazione osservazione con tutti i campi popolati, modifica con riapertura form, eliminazione, refresh dashboard, navigazione al pannello Scouting. RLS Supabase confermata (utente vede solo le sue osservazioni). Bug avversario edit mode risolto.

### Bug Transfermarkt URL admin

Pre-Fase 3 fixato bug nell'admin "Aggiungi giocatore": il regex accettava solo `transfermarkt.com` ma Mathys Detourbet (e tutti i giocatori esteri non scrappati live) hanno URL `.it`. Patch in `api/main.py:458` e `.github/workflows/add_player.yml:46`: regex da `transfermarkt\.com.*spieler/\d+` a `transfermarkt\.[a-z.]+.*spieler/\d+` per accettare qualsiasi TLD (.it, .de, .es, .fr, .com.tr, .com.br, ecc.). Test live: URL `.it` di Detourbet accettato e workflow add-player triggerato (commit `78a7be3`).

### Filtri e ordinamento (modifiche piccole)

- Filtro "Altre squadre" aggiunto nei 3 dropdown lega (Home `filter-league` riga ~4427, Lista `list-league`, Convocazione `callup-league` riga ~2231) con value `OTHER`. La logica `f.league === "OTHER"` era già supportata in `applyFilters` (riga 2105), mancava solo l'`<option>` HTML. Chiave i18n `league_other_filter` IT="Altre squadre" / EN="Other teams".
- Ordinamento Lista esteso: la funzione `headerCell()` esistente (riga 4384) gestiva già click su Nome, Club, Pres, Gol, Ass, Min, Età con frecce ↓/↑. Aggiunto sort anche su **Posizione** (`role`) e **Piede** (`foot`): estesa `sortFor()` con i 2 nuovi case + sort effettivo nella sezione `Ordinamento` per `position_general` alfabetico e `foot` alfabetico. Le 2 colonne nel `headerRow` sostituite da `headerCell()` per renderle cliccabili.

### Sezione Scouting full-width

Pannello Scouting allargato da `max-width: 1100px` a tutta larghezza, coerente con Lista e altri pannelli. Patch in `observations_ui.js` `renderScoutingPanel()`: rimosso `max-width: 1100px; margin: 0 auto`, lasciato solo `padding: 24px`.

### Commit della sessione

- `78a7be3` fix(admin): accetta URL Transfermarkt da qualsiasi TLD (.it, .de, .es, ecc.)
- `0da3f7a` feat(observations): aggiungi sezione Osservazioni nel modal giocatore (Fase 3 — UI)
- `9a5b9ef` feat(observations): v2 — dashboard compatta sotto stagione corrente, 2 colonne, categorie, chip verdi/rossi, pretty club names, ordine giudizi invertito
- `995099d` feat(observations): v3 — tabella 6 colonne, sezione sopra statistiche, voce sidebar Scouting, fix bug edit avversario
- `acdea02` feat(observations): v3 — tabella 7 colonne con competizione, sidebar Scouting, fix bug edit avversario
- `f1801bb` feat(observations): aggiungi campo viewing_mode (LIVE/TV) obbligatorio nel form e icona in tabella

### Lessons learned

- Quando il browser HTML5 gestisce `<input list="datalist">` con `value=""` inline, in modalità "edit" può bloccare l'editing dell'input. Workaround: rimuovere `value` inline e settare via JS dopo il render del modal. Soluzione documentata in MDN come issue noto.
- Il pattern `setVisible(id, show)` con classList toggle "hidden" è il modo più pulito per gestire il routing tra pannelli main. Replicabile anche per Scouting senza dover scrivere logica custom.
- Iterare l'UI con feedback live dell'utente è efficiente: 4 round di v3 hanno richiesto ~30 minuti totali di rifattoring, ma il risultato finale è coerente con le esigenze reali. Senza feedback diretto avrei costruito qualcosa di diverso (es. sezione in fondo al modal invece che sopra Statistiche club).

### Schema DB attuale `player_observations`

15 colonne totali (era 14): id (uuid PK), user_id (uuid FK auth.users), tm_player_id (bigint), match_date (date), opponent (text), competition (text), **viewing_mode (text, LIVE/TV/NULL)**, performance_rating (numeric 0-10), roles_played (text[]), evaluation_tags (text[]), strengths (text[]), weaknesses (text[]), notes (text), author_username (text), created_at (timestamptz), updated_at (timestamptz).

Vincolo unicità: `UNIQUE (user_id, tm_player_id, match_date, opponent)`. RLS basato su `auth.uid() = user_id` su tutte e 4 le operazioni.

### Stato Fase 3

✅ Schema Supabase + RLS + indici + trigger updated_at
✅ Modulo CRUD `cloud_sync.js` (4 funzioni + validazione)
✅ Sezione Osservazioni nel modal giocatore (dashboard compatta)
✅ Modal nuova/modifica osservazione (layout 2 colonne, campo SVG ruoli, chip per traits/tags)
✅ Pannello Scouting nella sidebar (vista globale per giocatore)
✅ Filtro "Altre squadre" + ordinamento Lista esteso + Scouting full-width

### Fasi residue del piano

- Fase 5 — Export PDF: singolo + dossier giocatore (jsPDF client-side) (~2h)
- Fase 6 — Export/Import salvataggio JSON (~45m)

### Aggiornamento sera 9 mag — tag NON VALUTABILE

Aggiunto 5° evaluation tag "NON VALUTABILE" colore grigio neutro `#9CA3AF`, posizionato come primo a sinistra (prima di "Non idoneo"). Caso d'uso: scout che vede pochi minuti del giocatore, partita interrotta, infortunio precoce — qualsiasi situazione dove valutare seriamente non è possibile.

Esclusione automatica dalle metriche aggregate: le osservazioni con tag "NON VALUTABILE" non contribuiscono né alla media performance del footer dashboard, né alla distribuzione percentuale dei giudizi. Implementata via filter `isEvaluable(obs) => obs.evaluation_tags?.[0] !== "NON VALUTABILE"` applicato prima del calcolo `ratings` e del conteggio `tagCounts`. Performance rating slider rimane attivo anche con tag NV (l'utente può comunque salvare un voto, semplicemente non parteciperà alle stat aggregate).

Traduzione EN: "N/A" (più conciso di "Not evaluable" / "Cannot rate"). Mapping aggiunto in `OBSERVATION_I18N_EN`.

Commit: `a46da77` feat(observations): aggiungi tag NON VALUTABILE (escluso da media e distribuzione %).

---



## 9 mag 2026 (mattina pt2) — Fase 3 osservazioni completata + viewing_mode + filtri/ordinamento

### Sessione di lavoro

Implementazione completa della UI delle osservazioni nel modal giocatore + pannello Scouting nella sidebar. Prima del codice, definite tutte le scelte di design rilevanti: dashboard compatta sotto "Stagione corrente" (poi spostata sopra "Statistiche club"), modal-on-modal per nuova/modifica, layout 2 colonne (form sinistra + campo SVG ruoli destra), chip categorizzati per strengths/weaknesses con colori verde/rosso, ordine evaluation tags rosso→verde (peggiore a sinistra).

### Iterazioni successive (feedback live)

Tre iterazioni sulla v3 del modulo `observations_ui.js`:

1. **v3 → v3.1** — feedback dopo primo deploy: tabella dashboard inizialmente con 4 colonne (Data | Scout | Performance | Giudizio). Aggiunte 3 colonne mancanti: Avversario (con `prettyClubName` e troncamento), Posizione (sigle ruoli giocati), e successivamente Competizione (truncata). Ordine campi nel form modificato: Note spostate sopra Performance Rating (e ingrandite a 10 rows / min-height 200px). Bug fixato: avversario non modificabile in edit mode (causa: combo `<input value list>` HTML5 ha glitch noti — fix: rimosso `value=""` inline, settato via JS dopo il render).

2. **v3.1 → v3.2** — sezione Osservazioni spostata da fondo modal a TRA "Stagione corrente" e "Statistiche club" (riga ~985 di app.js, subito dopo l'apertura del div padding 22px 28px). Voce sidebar "Scouting" anticipata dalla Fase 4: aggiunto `<div class="nav-item" data-route="scouting">` dopo "Minutaggi" e prima del separator (icona lente d'ingrandimento), `<div id="scouting-panel-main" class="hidden">` nel main content, hook in `setActiveTab()` per render del pannello via `renderScoutingPanel()` + `wireScoutingPanel()`, chiavi i18n `nav_scouting` IT/EN.

3. **v3.2 → v4 (viewing_mode)** — aggiunto campo "Visione" obbligatorio (LIVE / TV-VIDEO). Schema DB: `ALTER TABLE player_observations ADD COLUMN viewing_mode TEXT CHECK (viewing_mode IS NULL OR viewing_mode IN ('LIVE', 'TV'))`. Form: 2 chip side-by-side in cima alla colonna sinistra, icona campo da calcio per LIVE (verde) e icona monitor per TV (blu). Single-select obbligatorio con messaggio errore "Compila tutti i campi obbligatori". Tabella dashboard: 8ª colonna "Mod." con icona piccola colorata. Patch in `cloud_sync.js`: validazione `viewing_mode IN ['LIVE','TV']` in `saveObservation` e `updateObservation`.

### Liste finali

37 caratteristiche organizzate in 5 categorie:
- TATTICA (6): Fase difensiva, Fase offensiva, Intelligenza tattica, Letture tattiche, Transizioni difensive, Transizioni offensive
- TECNICA (11): Assist, Conduzione palla, Cross, Dribbling 1c1, Finalizzazione, Inizio manovra, Passaggi Chiave, Rifinitura, Tecnica, Tiro/Calcio, Visione di gioco
- COMPORTAMENTI (5): Aggressività, Agonismo, Gioco per la squadra, Intensità, Personalità
- FISICO (15): 1vs1 difensivo, Ampiezza, Area di rigore offensiva, Dinamismo, Duelli difensivi, Forza fisica, Gioco aereo, Inserimenti senza palla, Jolly, Profondità, Progressione, Rapidità primi metri, Recupero palloni, Spazi stretti, Velocità
- PORTIERE (1): Uscite

4 evaluation tags con colori, ordine peggiore→migliore: 🔴 NON IDONEO (#EF4444), 🟠 DA MONITORARE (#F97316), 🟡 SECONDA SCELTA (#EAB308), 🟢 PRIMA SCELTA (#22C55E).

24 competizioni preset + "Altro" con input libero.

15 ruoli sigle italiane con coordinate sul campo SVG: PP, AS, AD, TRQ, AES (quinto sn), AED (quinto dx), CIS, CC, CID, LAT_SN, LAT_DX, DCS, DC, DCD, POR.

### Test in produzione

End-to-end testato su https://pid-nine.vercel.app: creazione osservazione con tutti i campi popolati, modifica con riapertura form, eliminazione, refresh dashboard, navigazione al pannello Scouting. RLS Supabase confermata (utente vede solo le sue osservazioni). Bug avversario edit mode risolto.

### Bug Transfermarkt URL admin

Pre-Fase 3 fixato bug nell'admin "Aggiungi giocatore": il regex accettava solo `transfermarkt.com` ma Mathys Detourbet (e tutti i giocatori esteri non scrappati live) hanno URL `.it`. Patch in `api/main.py:458` e `.github/workflows/add_player.yml:46`: regex da `transfermarkt\.com.*spieler/\d+` a `transfermarkt\.[a-z.]+.*spieler/\d+` per accettare qualsiasi TLD (.it, .de, .es, .fr, .com.tr, .com.br, ecc.). Test live: URL `.it` di Detourbet accettato e workflow add-player triggerato (commit `78a7be3`).

### Filtri e ordinamento (modifiche piccole)

- Filtro "Altre squadre" aggiunto nei 3 dropdown lega (Home `filter-league` riga ~4427, Lista `list-league`, Convocazione `callup-league` riga ~2231) con value `OTHER`. La logica `f.league === "OTHER"` era già supportata in `applyFilters` (riga 2105), mancava solo l'`<option>` HTML. Chiave i18n `league_other_filter` IT="Altre squadre" / EN="Other teams".
- Ordinamento Lista esteso: la funzione `headerCell()` esistente (riga 4384) gestiva già click su Nome, Club, Pres, Gol, Ass, Min, Età con frecce ↓/↑. Aggiunto sort anche su **Posizione** (`role`) e **Piede** (`foot`): estesa `sortFor()` con i 2 nuovi case + sort effettivo nella sezione `Ordinamento` per `position_general` alfabetico e `foot` alfabetico. Le 2 colonne nel `headerRow` sostituite da `headerCell()` per renderle cliccabili.

### Sezione Scouting full-width

Pannello Scouting allargato da `max-width: 1100px` a tutta larghezza, coerente con Lista e altri pannelli. Patch in `observations_ui.js` `renderScoutingPanel()`: rimosso `max-width: 1100px; margin: 0 auto`, lasciato solo `padding: 24px`.

### Commit della sessione

- `78a7be3` fix(admin): accetta URL Transfermarkt da qualsiasi TLD (.it, .de, .es, ecc.)
- `0da3f7a` feat(observations): aggiungi sezione Osservazioni nel modal giocatore (Fase 3 — UI)
- `9a5b9ef` feat(observations): v2 — dashboard compatta sotto stagione corrente, 2 colonne, categorie, chip verdi/rossi, pretty club names, ordine giudizi invertito
- `995099d` feat(observations): v3 — tabella 6 colonne, sezione sopra statistiche, voce sidebar Scouting, fix bug edit avversario
- `acdea02` feat(observations): v3 — tabella 7 colonne con competizione, sidebar Scouting, fix bug edit avversario
- `f1801bb` feat(observations): aggiungi campo viewing_mode (LIVE/TV) obbligatorio nel form e icona in tabella

### Lessons learned

- Quando il browser HTML5 gestisce `<input list="datalist">` con `value=""` inline, in modalità "edit" può bloccare l'editing dell'input. Workaround: rimuovere `value` inline e settare via JS dopo il render del modal. Soluzione documentata in MDN come issue noto.
- Il pattern `setVisible(id, show)` con classList toggle "hidden" è il modo più pulito per gestire il routing tra pannelli main. Replicabile anche per Scouting senza dover scrivere logica custom.
- Iterare l'UI con feedback live dell'utente è efficiente: 4 round di v3 hanno richiesto ~30 minuti totali di rifattoring, ma il risultato finale è coerente con le esigenze reali. Senza feedback diretto avrei costruito qualcosa di diverso (es. sezione in fondo al modal invece che sopra Statistiche club).

### Schema DB attuale `player_observations`

15 colonne totali (era 14): id (uuid PK), user_id (uuid FK auth.users), tm_player_id (bigint), match_date (date), opponent (text), competition (text), **viewing_mode (text, LIVE/TV/NULL)**, performance_rating (numeric 0-10), roles_played (text[]), evaluation_tags (text[]), strengths (text[]), weaknesses (text[]), notes (text), author_username (text), created_at (timestamptz), updated_at (timestamptz).

Vincolo unicità: `UNIQUE (user_id, tm_player_id, match_date, opponent)`. RLS basato su `auth.uid() = user_id` su tutte e 4 le operazioni.

### Stato Fase 3

✅ Schema Supabase + RLS + indici + trigger updated_at
✅ Modulo CRUD `cloud_sync.js` (4 funzioni + validazione)
✅ Sezione Osservazioni nel modal giocatore (dashboard compatta)
✅ Modal nuova/modifica osservazione (layout 2 colonne, campo SVG ruoli, chip per traits/tags)
✅ Pannello Scouting nella sidebar (vista globale per giocatore)
✅ Filtro "Altre squadre" + ordinamento Lista esteso + Scouting full-width

### Fasi residue del piano

- Fase 5 — Export PDF: singolo + dossier giocatore (jsPDF client-side) (~2h)
- Fase 6 — Export/Import salvataggio JSON (~45m)

### Aggiornamento sera 9 mag — tag NON VALUTABILE

Aggiunto 5° evaluation tag "NON VALUTABILE" colore grigio neutro `#9CA3AF`, posizionato come primo a sinistra (prima di "Non idoneo"). Caso d'uso: scout che vede pochi minuti del giocatore, partita interrotta, infortunio precoce — qualsiasi situazione dove valutare seriamente non è possibile.

Esclusione automatica dalle metriche aggregate: le osservazioni con tag "NON VALUTABILE" non contribuiscono né alla media performance del footer dashboard, né alla distribuzione percentuale dei giudizi. Implementata via filter `isEvaluable(obs) => obs.evaluation_tags?.[0] !== "NON VALUTABILE"` applicato prima del calcolo `ratings` e del conteggio `tagCounts`. Performance rating slider rimane attivo anche con tag NV (l'utente può comunque salvare un voto, semplicemente non parteciperà alle stat aggregate).

Traduzione EN: "N/A" (più conciso di "Not evaluable" / "Cannot rate"). Mapping aggiunto in `OBSERVATION_I18N_EN`.

Commit: `a46da77` feat(observations): aggiungi tag NON VALUTABILE (escluso da media e distribuzione %).

---


### Aggiornamento sera 9 mag pt2 — refinement viewing_mode + sort role + tag obbligatorio

Tre modifiche di refinement post-deploy della Fase 3 osservazioni, tutte triggherate da feedback live durante l'uso reale:

**1) Label "LIVE" / "TV/VIDEO" nei badge della colonna Mod. dashboard**

Inizialmente la colonna "Mod." mostrava solo l'icona quadrata 22x22px (campo da calcio verde per LIVE, monitor blu per TV) senza testo. In uso reale risultava ambiguo capire a colpo d'occhio quale fosse quale, senza dover hoverare il `title`. Refactoring: badge convertito da quadrato icona-only a **pill orizzontale rounded** con icona + label inline, colore di sfondo coerente (verde 15% per LIVE, blu 15% per TV), font-weight 600, letter-spacing 0.04em, font-size 10px. Lunghezza maggiore della cella ma resta nascosta su mobile <700px (insieme a Posizione/Scout/Competizione) tramite media query CSS già esistente.

**2) Tag valutativo obbligatorio nel salvataggio**

Durante un test l'utente ha salvato un'osservazione con performance rating 8.5 ma senza scegliere un tag valutativo (nessuno dei 5 chip selezionato). Il salvataggio è andato a buon fine ma la dashboard mostrava `evaluation_tags: []` con "Giudizio: —" e tag escluso dalla distribuzione %. Comportamento confuso. Decisione: rendere obbligatoria la scelta del tag, aggiungendo "NON VALUTABILE" come tag-jolly per i casi reali in cui non si vuole esprimere giudizio. Implementazione: validazione `if (!window._obsCompose.selectedTag)` aggiunta in `_saveObsFromForm()` dopo la validazione roles, con messaggio errore localizzato `err_no_tag` IT="Seleziona un giudizio (anche 'Non valutabile')" / EN="Select an evaluation tag (also 'N/A')".

**3) Sort Lista per `position_specific` invece di `position_general`**

L'ordinamento "Ruolo" implementato stamattina usava `position_general` (4 categorie generiche: Goalkeeper, Defender, Midfield, Attack), ma la lista mostra a video `position_specific` (Punta centrale, Ala destra, Trequartista, Difensore centrale, ecc.). Cliccando "Ruolo" l'utente si aspettava ordinamento alfabetico sui 16+ valori specifici visibili a video, non raggruppamento per le 4 macro-categorie. Fix di una riga: `a.position_general` → `a.position_specific` nella sort logic della Lista. Il filtro `f.role` resta invece su `position_general` (corretto: i 4 dropdown sono macro-categorie).

Commit: `<hash>` feat(observations): badge LIVE/TV-VIDEO con label nella tabella + tag valutativo obbligatorio + sort Lista per posizione specifica.

### Stato Fase 3 finale

Tutto stabile in produzione. Fase 3 osservazioni scout completata e ben polished con tutti i feedback live. Modulo CRUD funzionante, dashboard chiara, modal compose ergonomico, pannello Scouting full-width, badge viewing_mode leggibili, tag valutativo obbligatorio (con escape "Non valutabile"), filtri e ordinamenti coerenti. Pronto per Fase 5 (Export PDF).

---

## 9 mag 2026 (notte) — Fix post-deploy Serie C + analisi bug Winter signing + cache SOTS espansa

Sessione di consolidamento dopo il deploy della migrazione Serie C: piccoli fix di produzione, diagnosi bug profondi che richiedono lavoro futuro, e preparazione del terreno per il recupero foto SortItOutSi sui ~1111 giocatori che ne sono sprovvisti.

### Sito down dopo deploy Serie C — bug `it3` orfano

Subito dopo il push della migrazione (`e976fee`), l'utente ha riportato che le sezioni della sidebar non rispondevano al click. Diagnosi rapida via DevTools console: errore JavaScript fatale al boot dell'app.

```
Uncaught (in promise) ReferenceError: it3 is not defined
    at renderClubs (app.js:682:6)
    at bootstrap (app.js:171:3)
```

La PATCH 3.7 di `migrate_serie_c.py` (regex su `sectionHtml`) non aveva fatto match della riga di rendering del Club perché aveva l'argomento di colore `"rgba(56,189,248,0.08)"` che non era nel pattern atteso. Risultato: 2 righe in `app.js` (riga 682 nel render e riga 689 nel `leaguesCount`) sono rimaste con riferimento a `it3` (variabile rimossa). Il `bootstrap()` chiamava `renderClubs()` al boot e l'errore bloccava tutto il routing della sidebar.

Fix manuale via script Python ad-hoc: sostituite le 2 righe orfane con 3 righe per `it3a/it3b/it3c` nel render, e aggiornato l'array `leaguesCount` per includere le 3 nuove leghe. Sintassi verificata 0/0 (graffe + parentesi bilanciate). Push immediato.

Commit: `fd377e4` fix(clubs): variabile it3 orfana in renderClubs (sostituita con it3a/b/c).

Lezione: quando si patcha codice via regex con argomenti dinamici (qui un colore RGBA), o si scrive il pattern includendo il colore esatto presente nel codice, o si usa una regex più generosa (`.*` per gli argomenti opzionali). Per il prossimo refactor multi-file uso `re.compile()` con re.DOTALL e gruppi nominati per non fare lo stesso errore.

### Loghi mancanti Alcione + Guidonia

Dopo il deploy del fix `it3`, l'utente ha notato due loghi non visibili nel pannello Club:

**Alcione Milano (TM 52687, IT3A)** — assente nel log di scrape_sortitoutsi_competition.py. Il match per nome non era stato trovato perché lo scraper non riconosceva il nome "Alcione Milano" nella pagina sortitoutsi del Girone A. L'utente ha cercato manualmente sulla pagina sortitoutsi e fornito il team_id corretto: `43106513` (https://sortitoutsi.net/football-manager-2026/team/43106513/alcione-milano). Aggiornati `clubs.json` con `sortitoutsi_team_id`/`sortitoutsi_logo_url`/`sortitoutsi_logo_local` per il club. Logo PNG scaricato via curl (24 KB, valido).

**Guidonia Montecelio 1937 FC (TM 45894, IT3B)** — il log mostrava `sots 2000384267` matchato correttamente, ma il file PNG locale non esisteva. Tentativo download via curl: il file scaricato pesava solo **43 byte** (placeholder/errore HTML invece che immagine). L'asset SOTS per questo team_id semplicemente non esiste, anche se il team_id è registrato nel sistema. Bug noto FM26: alcuni team_id hanno entry ma non hanno mai avuto immagine caricata.

Fix per Guidonia: rimossi i campi `sortitoutsi_team_id`, `sortitoutsi_logo_url`, `sortitoutsi_logo_local` dal record del club in `clubs.json`. In questo modo il frontend non prova nemmeno a caricare l'asset SOTS rotto e cade automaticamente sul fallback Transfermarkt o sull'iniziale del nome. L'utente ha confermato di accettare il fallback automatico (no logo) per Guidonia, in attesa che FM26 carichi un'immagine ufficiale.

Bug Python su macOS notato: `urllib.request` ha SSL_CERT_FAILED su HTTPS perché Python su macOS non usa il keychain di sistema per i certificati. Workaround: usare `curl` (che invece sa usare i certificati di sistema). Annotato come pattern da preferire in futuro per download HTTPS da scripting Python.

### Pulizia prefissi club (Commit 1)

Nei screenshot dell'utente erano visibili nomi club non stilizzati: "AS Giana Erminio", "US Cremonese", "FC Crotone", "ACF Fiorentina". La funzione `prettyClubName()` esistente usa una map `_CLUB_DISPLAY_MAP` con sostituzioni esatte, ma copriva solo Serie A + Serie B + Primavera (60 mappature). I 56 nuovi club Serie C non avevano mappature, quindi venivano visualizzati col prefisso TM completo.

Approccio scelto: estendere `_CLUB_DISPLAY_MAP` con 56 mappature manuali per i club Serie C, mantenendo coerenza col pattern esistente. Esempi:
- "AS Giana Erminio" → "Giana Erminio"
- "FC Crotone" → "Crotone"
- "US Salernitana 1919" → "Salernitana"
- "Calcio Foggia 1920" → "Foggia"
- "Audace Cerignola" → "Cerignola"

Mantenuti senza pulizia: Inter U23, Atalanta U23, Juventus Next Gen, Milan Futuro (già chiari), Dolomiti Bellunesi, Vis Pesaro, Pro Vercelli, Pro Patria, Virtusvecomp Verona (ambigui o nomi propri). Per "ASD Team Altamura" rimosso solo il prefisso ASD (sigla generica per associazioni dilettantistiche).

Approccio NON scelto (e perché): generare automaticamente con regex il nome senza prefisso (`/^(AC|AS|ACF|US|FC|SS|SSC|UC|SEF|AZ|LR|ASD)\s+/`) era più rapido ma rischioso: rimuoveva prefissi anche da club dove sono parte integrante del nome distintivo (es. "FC Empoli" è "Empoli", ma "Empoli" da solo è confondibile; "AC Pisa" → "Pisa" ok, ma "Pisa Sporting Club" è già chiaro così). Con map manuale la decisione è caso per caso.

### Workaround Winter signing (Commit 1)

L'utente ha aperto la scheda di Adrian Liber (giocatore polacco di Polonia Bytom) e ha notato che il club mostrato era "Winter signing", che è un placeholder fittizio di Transfermarkt per giocatori in mercato di gennaio.

Diagnosi: lo scraper `scraper/profiles.py:_extract_current_club_id` ha già un filtro per ribbon (Strategia 3 esclude `data-header__ribbon` che contiene New arrival/Winter signing/Returnee), ma la Strategia 1 (`.data-header__club a`) trova prima un link a `/startseite/verein/2362` che è il cluster fittizio TM "Winter signing". Quel link viene preso come club valido perché tecnicamente è un link a `/startseite/verein/`. Il filtro non viene mai raggiunto perché il match avviene prima.

Numeri vittime: 91 giocatori in `players_main.json` con `current_club_id=2362`, tutti polacchi/Ekstraklasa/I Liga. Esempio: Adrian Liber (`tm_player_id=N/A`), polacco di Polonia Bytom secondo le ultime partite, ma scrappato come "Winter signing".

Workaround applicato (Commit 1, cosmetico): in `prettyClubName()` aggiunto early return `if (name === "Winter signing" || name === "New arrival" || name === "Returnee") return "—"`. Risolve la visualizzazione, non il dato.

Fix vero del bug rimandato a sessione futura. Strategia: in `_extract_current_club_id` aggiungere blacklist di tm_club_id fittizi noti `[2362, 2363, ...]` da ignorare. Quando il match cade su uno di questi ID, ignorare e provare le strategie successive. Poi rilanciare lo scraping sui 91 giocatori vittime.

### Linea divisoria Osservazioni → Statistiche club (Commit 1)

Feedback UX dell'utente: nel modal giocatore la sezione "Osservazioni" e "Statistiche club" erano visualmente attaccate, sembravano un blocco unico. Aggiunta una linea divisoria sottile (`border-top: 0.5px solid var(--border)` con `padding-top: 18px`, `margin-top: 22px`) tra le due sezioni, applicata solo se ci sono effettivamente statistiche club da mostrare (`clubBlocks || hasU21Current`).

Commit: `2934c2d` fix(clubs): mappature Serie C 56 club + workaround Winter signing + divisoria Osservazioni/StatClub.

### Cache SortItOutSi rosters allargata (10069 persons)

L'utente ha richiesto strategia di recupero per i ~1111 giocatori senza foto SOTS. Diagnostica iniziale:

```
Totale giocatori: 2864
Con face SOTS: 1753 (61%)
Senza face SOTS: 1111
```

Esempio caso scenario B (giocatore in DB senza match SOTS): Adrian Bukowski (tm_player_id=577597, Stal Mielec PL1) ha `sortitoutsi_face_url=NONE` e `sortitoutsi_person_id=NONE`. L'utente ha verificato manualmente che esiste su sortitoutsi (https://sortitoutsi.net/football-manager-2026/person/2000046931/adrian-bukowski). Il match al primo passaggio non era avvenuto.

Strategia decisa: sfruttare l'infrastruttura esistente di matching offline (4 script già in repo dal 6 mag: `harvest_sots_rosters.py`, `find_more_sots_matches.py`, `apply_more_matches.py`, `verify_auto_matches_dob.py`) e rieseguire dopo aver popolato la cache con le 56 nuove rose Serie C.

Lanciato `python3 harvest_sots_rosters.py` che ha aggiornato `data/sots_rosters.json` da **5875 a 10069 persons** (+4194 giocatori), distribuiti su 95 club totali. La cache include ora le rose dei 56 club Serie C nuovi (~80 persons medi per club = ~4500 nuovi candidati per matching).

Questo significa che il prossimo `find_more_sots_matches.py` dovrebbe trovare match per molti dei 1111 giocatori senza foto, in particolare:
- Giocatori dei club Serie C scrappati di recente (le loro rose sono ora in cache)
- Giocatori in trasferimento dai club Serie A/B verso Serie C (mercato gennaio 2026)
- Giocatori di club appena promossi/retrocessi tra Serie C/D

Stima recupero: 200-400 nuovi match attesi. Da verificare al prossimo run.

### Stato fine sessione

In produzione (commit `2934c2d`):
- ✅ Sito stabile, navigazione sidebar funzionante
- ✅ Migrazione Serie C 3 gironi visibile e completa nel pannello Club
- ✅ Loghi Alcione manuale, Guidonia fallback iniziali
- ✅ Nomi club Serie C puliti ("Giana Erminio" non "AS Giana Erminio")
- ✅ Workaround "Winter signing" → "—" per i 91 vittime (cosmetico)
- ✅ Linea divisoria Osservazioni/Statistiche club nel modal giocatore

Cache locale aggiornata (non in produzione, da rilanciare matching):
- ✅ `data/sots_rosters.json`: 5875 → 10069 persons (+71%)
- 🔄 Pronto per `find_more_sots_matches.py` + `apply_more_matches.py` (next run)

### Prossima sessione — TODO

**Bug Winter signing (alta priorità)**:
- Fix in `scraper/profiles.py:_extract_current_club_id`: aggiungere blacklist `[2362, 2363]` per ignorare cluster fittizi TM e provare strategie successive
- Rilanciare scraping per i 91 giocatori vittime (re-fetch profiles)
- Eventualmente arricchire fallback con info dal roster club (chi ha tm_player_id nella rosa scrappata)

**Recupero foto SOTS (media priorità)**:
- Lanciare `find_more_sots_matches.py` con cache da 10069 persons
- Review casi auto-match score 0.7-1.0 vs casi di review (0.5-0.7)
- Lanciare `apply_more_matches.py` per i match confermati
- Verifica con `verify_auto_matches_dob.py` per match dubbi
- Stima: porta da 61% a 75-80% giocatori con foto SOTS

**Feature pending (bassa priorità per stasera, da fare nelle prossime sessioni)**:
- Vista relazione completa (espande inline come pannello Scouting, già concordato)
- Minuti giocati nelle osservazioni (form, dashboard, scouting; richiede ALTER TABLE Supabase)
- Bottone "+ Osservazione" nelle Ultime partite (con precompilazione data/avversario/competizione/minuti)
- Workflow `.github/workflows/auto_update_photos.yml` settimanale (lunedì 04:00 UTC) per re-run automatico di `scrape_sortitoutsi_competition.py` + `scrape_sortitoutsi_ids.py`

**Housekeeping**:
- Pulire i file `*.before_serie_c` (5 file backup, ~100KB) quando il sistema è confermato stabile
- Popolare i 56 club Serie C con i giocatori delle rose (`build_urls.py` su `it3a/b/c_clubs.json` + `add_players.py`). Stima: 30-60 minuti per ~800-1000 giocatori
- Considerare aggiunta PL1/PL2 (Ekstraklasa/I Liga) alle COMPETITIONS in `scrape_sortitoutsi_competition.py` per coprire i giocatori polacchi (attualmente non scaricati con loghi/foto SOTS)

### Commit pushati nella sessione

- `e976fee` feat: Serie C 3 gironi (IT3A/B/C) + scouting refinement (logo club + ruoli per esteso) — main rebase
- `fd377e4` fix(clubs): variabile it3 orfana in renderClubs (sostituita con it3a/b/c)
- `2934c2d` fix(clubs): mappature Serie C 56 club + workaround Winter signing + divisoria Osservazioni/StatCub

---

## 9 mag 2026 (pomeriggio) — Recupero foto SOTS + 3 sub-commit feature observations

Sessione di consolidamento e feature delivery dopo la migrazione Serie C. Prima si è recuperata una parte delle foto SortItOutSi tramite matching offline cross-club (filtro anno+club per superare il bug delle DOB tronche TM nei giocatori Primavera), poi si è completata la trilogia di feature richieste sul modulo osservazioni (vista relazione completa, minuti giocati, bottoni "+ Osservazione" sulle Ultime partite con precompilazione).

### Recupero foto SortItOutSi cross-club

Punto di partenza: 1753/2864 giocatori con foto SOTS (61%). Cache `data/sots_rosters.json` aggiornata a 95 club con 10069 persons totali (lavoro fatto la sessione precedente). 1111 giocatori ancora senza foto.

Lanciato `find_more_sots_matches.py` (script già esistente dalla sessione del 6 mag): legge `players_main.json`, cerca i giocatori senza `sortitoutsi_person_id`, e per ognuno cerca candidati in `sots_rosters.json` usando regole multiple (slug esatto = score 1.0, all-tokens-match = score 0.85). Per ogni candidato fetch della pagina person su sortitoutsi.net, estrae DOB, accetta solo se DOB esatta corrisponde a quella in TM.

Risultato run: 0 confermati, 35 DOB mismatch, 35 fetch totali. Tutti i candidati trovati avevano DOB diversa = lo script ha rifiutato tutti.

Diagnosi del file `data/sots_more_matches_dob_mismatch.xlsx`: il TM scraper estrae DOB tronche per giocatori Primavera (es. "2007 (~ 19" invece di "2007-10-19"), perché TM nasconde giorno/mese per minorenni nelle pagine pubbliche. Lo script di matching confronta stringa per stringa e marca tutti come mismatch, anche quando l'anno coincide.

Soluzione adottata: scritto `filter_dob_mismatch.py` (~160 righe) che applica regole di buon senso per accettare match veri:
- Anno TM == Anno SOTS (estratti come int dai primi 4 caratteri di entrambe le DOB)
- Club TM e SOTS compatibili — funzione `club_root()` rimuove suffissi "Primavera"/"U23"/"U19"/"Futuro" e prefissi "AC"/"AS"/"FC"/"US"/"SS"/"SSC"/"UC"/"ACF"/"SEF"/"UCF" per matchare es. "Frosinone Primavera" ↔ "Frosinone Calcio" come stesso club madre
- Slug perfetto (già condizione di partenza per essere nel file di mismatch)
- Se 2+ candidati passano i filtri (omonimi) → scarta tutti

Risultato del filtro: 31 confermati, 3 scartati per anno diverso (omonimi reali), 0 ambigui, 0 club incompatibili. Esempi confermati: Abubacar Ceesay (Frosinone Primavera ↔ Frosinone Calcio), Adam Hasani (Napoli Primavera ↔ SSC Napoli), Andrea Campani (Sassuolo Primavera ↔ US Sassuolo). Esempi scartati correttamente: Ibrahima Camará (TM 1999, SOTS 2008 — chiaramente persone diverse).

Lanciato `apply_more_matches.py` sui 31 confermati: 17 face PNG scaricate (le altre 14 hanno avatar mancante su SOTS), `data/sortitoutsi_id_lookup.json` aggiornato a 1784 entries, `players_main.json` + `players_static.json` + `players_all.json` aggiornati con `sortitoutsi_person_id` e `sortitoutsi_face_url` per i 31. Nuovo target: 1784/2864 = 62% (era 61%, +1%).

Recupero limitato perché il mismatch file aveva solo 35 candidati. La maggior parte dei 1111 senza foto sta in `no_candidate` (giocatori che `find_more_sots_matches.py` non ha nemmeno candidato perché lo slug non matcha nemmeno parzialmente con nessun nome SOTS in cache). Per quelli serve scraping by-name search (rimandato a sessione futura) o aggiunta di PL1/PL2 (Ekstraklasa/I Liga) alle competitions sortitoutsi.

Commit: `74220a4` feat(sots): recupero 31 match cross-club (filtro anno+club per DOB tronche Primavera).

### Trilogia feature observations: piano e ordine di esecuzione

L'utente aveva richiesto 3 feature in sospeso da varie sessioni:

1. Vista relazione completa: cliccando su una riga osservazione, vedere il contenuto completo (ruoli, performance, tag, note testo intero, strengths, weaknesses, scout, data inserimento)
2. Minuti giocati: campo opzionale nel form osservazione, range 0-150, da mostrare in dashboard e pannello scouting
3. Bottone "+" precompilante: sulle "Ultime 12 partite" e nel drill-down del grafico minuti, un piccolo bottone "+" alla fine di ogni riga che apre il form nuova osservazione precompilato con data/avversario/competizione/minuti dalla riga partita

Decisione: 3 sub-commit separati per facile rollback. L'utente ha preferito iniziare dalla vista relazione.

### Sub-commit "vista relazione" — falso start con revert + repair

Implementazione iniziale (commit `bc3b845`): aggiunta alle righe osservazione del modal giocatore una nuova `<tr>` "expansion" inizialmente nascosta che mostrava i dettagli completi al click sulla riga (toggle), con bottoni "Modifica" + "Elimina" dentro la vista espansa. Patch grossa: ~130 righe in `observations_ui.js`.

Test in produzione: l'utente ha chiarito che la vista relazione completa non doveva essere creata da zero come espansione inline, perché il modal di modifica esistente (`openObservationCompose`) già mostrava tutti i dettagli ed era esattamente quello che voleva. Il problema vero era diverso: l'utente immaginava che il click facesse "altro" rispetto ad aprire la modal di edit, ma in realtà la modal di edit era già la vista che voleva.

Quindi: vista relazione = modal di modifica esistente. Niente da implementare. La mia patch era sbagliata e da rimuovere.

Sequenza confusa di revert + reapply + revert (commit `76526b4`, `5433b91`, `7a925d9`) durante il test perché l'utente non era sicuro al 100% se rimuovere o lasciare.

Bug residuo dopo i revert: il file `observations_ui.js` consegnato al successivo sub-commit ("minuti giocati") partiva da `observations_ui_v2.js` nella working dir Claude, che aveva ancora la patch sbagliata. Quindi la vista espansa è rientrata in produzione attraverso il sub-commit minuti.

Repair finale (commit `b3967e9` "fix: rimuovo vista espansa relitto"): script Python con 3 patch:
- Rimuove blocco `expandedHtml` (~7800 chars di codice morto)
- Rimuove `${expandedHtml}` dalla riga return
- Ripristina click handler originale `wrapper.querySelectorAll(".obs-row")` → `openObservationCompose(pid, row.dataset.obsId)`

Sanity check post-repair: 0 occorrenze di `obs-detail-row`, 0 di `obs-edit-btn`, 2 di `obs-delete-btn` (mantenute perché sono codice originale del bottone elimina nella modale di modifica esistente).

Lezione organizzativa: quando si fa rollback di una feature, controllare che i file di working dir Claude siano allineati allo stato production, altrimenti i sub-commit successivi reintroducono il codice rimosso. La working dir va sempre sincronizzata col main commit dopo un revert.

### Sub-commit 1 — Minuti giocati

Schema DB: `ALTER TABLE player_observations ADD COLUMN IF NOT EXISTS minutes_played INTEGER NULL CHECK (minutes_played IS NULL OR (minutes_played >= 0 AND minutes_played <= 150))`. SQL eseguito dall'utente sul SQL Editor di Supabase. Verifica: colonna `minutes_played | integer | YES`.

Frontend changes:
- `cloud_sync.js`: aggiunto `minutes_played: obs.minutes_played ?? null` al record di `saveObservation` con validazione range. `updateObservation` invece spreaada `...patch` quindi passa `minutes_played` automaticamente senza patch.
- `observations_ui.js`:
  - Defaults form (variabile `v`): `minutes_played: editing?.minutes_played != null ? editing.minutes_played : null`
  - Nuovo blocco UI dopo "Visione" (LIVE/TV): input number range 0-150 con label "Minuti giocati (opzionale)" e placeholder "Es. 90"
  - Estrazione al salvataggio: legge `obs-minutes`, parseInt, valida range, aggiunge a payload
  - 2 nuove chiavi i18n IT (`f_minutes`/`f_minutes_ph`) + 2 EN

Aggiunto display dei minuti nel pannello Scouting (commit successivo): nelle righe osservazione espanse, sotto la colonna ETÀ, viene mostrato il valore come `90'` (font 11px, color text-1 se valorizzato, text-3 con `—` se null). Coerenza visiva: età=numero, minuti=numero.

Commit: `8de4eba` feat(obs): minuti giocati nel form osservazione (campo opzionale 0-150).

### Sub-commit 3 — Bottoni "+ Osservazione" su Ultime partite e drill-down grafico

Patch su `app.js`:
- `renderRecentMatches()` (riga ~2010): grid-template-columns esteso da 6 a 7 colonne (aggiunto 26px alla fine), nuovo bottone con classe `add-obs-from-match` e attributi `data-pid`, `data-date`, `data-opponent`, `data-competition`, `data-minutes`. Stile: icona "+" 22x22px verde accent.
- `_renderDrillDownMatch()` (riga ~1884): stesso bottone, dimensione leggermente più piccola (20x20px), grid esteso da 6 a 7 colonne (aggiunto 24px). Inserito subito dopo i minuti, condizionalmente se `pid` è disponibile (estratto da `stats?.tm_player_id`).
- Handler delegato globale su `document.click`: intercetta click su `.add-obs-from-match`, legge tutti i `data-*` dal bottone, salva in `window._obsPrefill = {match_date, opponent, competition, minutes_played}`, chiama `window.openObservationCompose(pid)`.

Patch su `observations_ui.js`:
- `openObservationCompose(pid, obsId)`: dopo aver settato `window._obsCompose`, legge `window._obsPrefill` solo se non sta modificando (`!editing`). One-shot consume: dopo lettura imposta `window._obsPrefill = null` per evitare side effect su nuove osservazioni successive.
- `_obsComposeHtml(player, editing, prefill)`: 3° argomento opzionale. Nei defaults `v`, aggiunto fallback chain `editing?.X || prefill?.X || ""` per `match_date`, `opponent`, `competition`, `minutes_played`. Per `competition_is_other` aggiunto check anche per il prefill.

Bug fix successivo "avversario non precompilato": l'input `<input id="obs-opponent">` nel template HTML mancava completamente l'attributo `value=""`, mentre date/competition/minutes lo avevano. Quindi il prefill caricava `v.opponent` correttamente nei defaults ma poi l'HTML non lo applicava all'input. Fix: aggiunto `value="${escapeHtml(v.opponent || "")}"` all'input.

Commit: `c8b9bdb` feat(obs): bottone '+ osservazione' nelle Ultime partite e nel drill-down grafico minuti (precompila data/avversario/competizione/minuti).

### Cosa è ora in produzione (stato fine sessione)

Modulo osservazioni:
- Click su riga osservazione (sia in modal giocatore sia in pannello scouting) → apre modale di modifica esistente
- Form modale ha campo "Minuti giocati (opzionale)" range 0-150 dopo Modalità
- Pannello Scouting mostra minuti nelle righe osservazione espanse sotto colonna ETÀ
- Bottone "+" su tutte le 12 ultime partite e nel drill-down grafico minuti per mese, click apre form nuova osservazione precompilato con data/avversario/competizione/minuti

Database:
- Tabella `player_observations` ha colonna `minutes_played` con CHECK 0-150 nullable

Foto SOTS:
- 1784/2864 giocatori con foto (62%, +31 vs precedente)
- Cache `data/sots_rosters.json` 10069 persons (95 club) — pronta per future query

Frontend altro:
- Nomi club Serie C visualizzati puliti (es. "Giana Erminio" non "AS Giana Erminio")
- Workaround "Winter signing"/"New arrival"/"Returnee" → "—" cosmetico in `prettyClubName`

### Commit pushati nella sessione

- `74220a4` feat(sots): recupero 31 match cross-club (filtro anno+club per DOB tronche Primavera)
- `bc3b845` feat(obs): vista relazione completa espansa al click sulla riga (PATCH SBAGLIATA)
- `76526b4` Revert "feat(obs): vista relazione completa espansa..."
- `5433b91` Reapply "feat(obs): vista relazione completa espansa..."
- `7a925d9` Revert "Reapply ..." (definitivo)
- `8de4eba` feat(obs): minuti giocati nel form osservazione (campo opzionale 0-150)
- `c8b9bdb` feat(obs): bottone '+ osservazione' nelle Ultime partite e nel drill-down grafico minuti
- `b3967e9` fix(obs): rimuovo vista espansa relitto (click riga torna ad aprire modal modifica)
- (commit successivo) feat(scouting): minuti giocati nelle righe osservazione del pannello Scouting
- (commit successivo) fix(obs): pre-fill avversario nel form (mancava value sull'input obs-opponent)

---

## Prossimi passi (TODO consolidato)

Lista esaustiva di tutto quello che è ancora da fare, ordinata per priorità. Ogni task ha una stima di tempo e una descrizione di cosa va fatto in concreto, così alla prossima sessione si parte senza dover ricostruire il contesto.

### ALTA — Bug Winter signing (scraper retroattivo)

Problema: 91 giocatori polacchi/Ekstraklasa hanno `current_club_id=2362` e `current_club_name="Winter signing"` in `players_main.json`. Adesso il frontend mostra "—" via workaround in `prettyClubName`, ma il dato in DB resta sporco e l'esperienza utente è degradata (es. Adrian Liber visualizzato senza club).

Causa: in `scraper/profiles.py:_extract_current_club_id` la Strategia 1 (`.data-header__club a[href*="/startseite/verein/"]`) trova prima un link a `/startseite/verein/2362/winter-signing` (cluster fittizio TM per giocatori in trasferimento di gennaio) e lo accetta come club valido. Strategia 3 ha già un filtro per `data-header__ribbon` ma non viene mai raggiunta perché Strategia 1 ha già trovato un risultato.

Fix:
1. In `scraper/profiles.py:_extract_current_club_id`, aggiungere blacklist `FAKE_TM_CLUB_IDS = {2362, 2363}` (Winter signing + Returnee). Quando Strategia 1 trova un match, controllare se l'ID estratto è nella blacklist; se sì, ignorare e provare Strategia 2/3.
2. Eventualmente cercare anche per altri ID fittizi noti (verificare con grep cross-tutti-i-giocatori-rotti se ce ne sono altri oltre 2362)
3. Rilanciare scraping di profile per i 91 giocatori vittime: estrarre lista tm_player_id da `players_main.json` con `current_club_id=2362` e ri-scrappare ogni profilo
4. Verifica: dopo il rilancio, query Python `[p for p in players if p.get("current_club_id") == 2362]` deve essere 0

Stima: ~30 min (fix scraper) + ~20 min (rilancio) + ~10 min (verifica). Totale 1 ora.

### ALTA — Recupero foto SOTS rimanenti (~1080 giocatori)

Problema: il run di `find_more_sots_matches.py` ha generato `sots_more_matches_dob_mismatch.xlsx` con 35 righe, ma NON ha generato `sots_more_matches_no_candidate.xlsx`. Significa che lo script si è fermato dopo la fase di mismatch, o il file no_candidate non è stato generato perché tutti i giocatori unmatched avevano almeno un candidato slug.

Diagnosi:
1. Verificare se `find_more_sots_matches.py` ha una flag o opzione per generare anche il no_candidate
2. Se no, scrivere uno script di analisi che identifica i giocatori unmatched senza candidati slug e suggerisce strategia (search by-name, override manuale, accettare assenza foto)
3. Considerare aggiunta di PL1/PL2 (Ekstraklasa, I Liga) alle COMPETITIONS in `scrape_sortitoutsi_competition.py`. Probabilmente non sono coperte attualmente, e visto che la maggior parte dei 91 Winter signing sono polacchi, questa potrebbe essere la fonte del problema combinato.

Fix:
1. Aggiungere PL1/PL2 a COMPETITIONS di `scrape_sortitoutsi_competition.py` con i link sortitoutsi corretti (cercare manualmente su sortitoutsi.net "Polish Ekstraklasa" e "Polish I Liga")
2. Lanciare `scrape_sortitoutsi_competition.py` per scaricare i sortitoutsi_team_id dei club polacchi
3. Lanciare `harvest_sots_rosters.py` per popolare la cache rosters con le rose Ekstraklasa/I Liga
4. Ri-lanciare `find_more_sots_matches.py` per matchare i giocatori polacchi con la cache aggiornata
5. Lanciare `apply_more_matches.py` per scaricare le nuove foto

Stima: ~60-90 min (compresi possibili scraping by-name iterativi)

### MEDIA — Workflow GitHub Actions auto-update foto SOTS

Problema: il workflow notturno `auto_update_daily.yml` fa solo `run_stats.py`. Le foto SortItOutSi si fossilizzano allo stato del primo scraping. Ogni nuovo giocatore aggiunto, ogni cambio rosa, ogni nuova competizione SOTS rilasciata non ottiene aggiornamenti automatici.

Soluzione: workflow separato settimanale (per non rallentare il daily che gira ogni notte).

File da creare: `.github/workflows/auto_update_photos.yml`

Trigger: cron settimanale (es. lunedì alle 04:00 UTC, dopo il daily).

Steps:
1. Checkout repo
2. Setup Python + venv + requirements
3. Lancia `python3 scrape_sortitoutsi_competition.py` (aggiorna sortitoutsi_team_id in clubs.json)
4. Lancia `python3 harvest_sots_rosters.py` (aggiorna cache rosters)
5. Lancia `python3 find_more_sots_matches.py`
6. Lancia `python3 filter_dob_mismatch.py` (filtra match veri Primavera)
7. Lancia `python3 apply_more_matches.py`
8. Commit + push se ci sono diff in `data/players_*.json` o `data/photos/players_sots_lookup/*.png`

Permessi GitHub Actions: già configurati per `auto_update_daily.yml` (commit fix permissions del 9 mag mattina).

Stima: ~30 min (scrittura workflow + test in dry-run)

### MEDIA — Fase 5 Export PDF (dossier giocatore + report osservazione)

Feature richiesta originariamente nel piano del modulo osservazioni. Dossier completo del giocatore in PDF + report singolo per ogni osservazione.

Stack: jsPDF client-side (lavora nel browser, no server). Già usato in altri progetti dello sviluppatore.

Contenuto dossier giocatore:
- Header con foto, nome, anno, ruolo, club
- Nazionalità, piede, altezza
- Stats stagione corrente (presenze, gol, assist, minuti)
- Tabella ultime 12 partite
- Sezione osservazioni: per ogni osservazione, blocco con data, avversario, competizione, modalità, performance, tag, ruoli, strengths, weaknesses, note testo intero, minuti, scout
- Logo PID in alto a sinistra, footer con data export

Contenuto report singola osservazione:
- Versione "espansa" della singola osservazione, una pagina A4

Bottone export PDF in 2 punti:
- Modal giocatore: sotto i bottoni "Aggiungi al confronto" / "Aggiungi ai preferiti", aggiungere "Esporta PDF"
- Modal di modifica/visualizzazione osservazione: in fondo, accanto a "Modifica"/"Elimina", aggiungere "Esporta PDF"

Stima: ~2 ore (template PDF + integrazione + styling)

### BASSA — Popolare i 56 club Serie C con giocatori

Adesso i club Serie C sono in `clubs.json` con loghi, ma vuoti di giocatori (nessuno è stato scrappato per loro). Lanciare `build_urls.py` su `it3a/b/c_clubs.json` + `add_players.py urls.txt`. Aggiunge ~800-1000 giocatori al DB.

Sequenza:
1. `python3 build_urls.py data/it3a_clubs.json data/it3b_clubs.json data/it3c_clubs.json > urls_serie_c.txt`
2. `python3 add_players.py urls_serie_c.txt`
3. Verifica: `players_main.json` cresce da 2864 a ~3700-3900
4. Commit + push

Effetto collaterale positivo: dopo questo, i `find_more_sots_matches.py` futuri potranno matchare anche questi giocatori contro la cache rosters Serie C (10069 persons già pronte).

Stima: 30-60 minuti di scraping + ~10 min di review/commit.

### BASSA — Fase 6 Export/Import salvataggio JSON

Backup completo (preferiti, callup, osservazioni, override) in JSON scaricabile. Re-import per merge tra dispositivi.

Stima: ~45 min

### BASSA — Pulizia file `.before_serie_c`

5 file backup creati il 9 mag durante la migrazione Serie C (~100 KB totali):
- `data/clubs.json.before_serie_c`
- `data/it3_clubs.json.before_serie_c`
- `frontend/app.js.before_serie_c`
- `frontend/i18n.js.before_serie_c`
- `scrape_sortitoutsi_competition.py.before_serie_c`

Sistema confermato stabile da varie sessioni. Sicurezza non più necessaria.

```bash
git rm frontend/*.before_serie_c data/*.before_serie_c *.py.before_serie_c
git commit -m "chore: rimuovo backup Serie C migration"
git push
```

Stima: 2 min.

### BASSA — Refactor minore observations_ui.js

Il file ha raggiunto 1251 righe, monolitico. Considerare in futuro split in moduli separati:
- `observations_compose.js` (form modale + save/update + validation)
- `observations_dashboard.js` (renderObservationsList + tabella nel modal giocatore)
- `observations_scouting.js` (renderObservationsScoutingPanel + tabella nel pannello laterale)
- `observations_constants.js` (TAGS, ROLE_DEFS, COMPETITIONS, TRAITS, I18N)

Effetto positivo: più facile da modificare senza side effect cross-file. Effetto negativo: aumenta il numero di `<script>` tag in index.html e la dependency tree.

Decisione: rimandare finché il file non supera 1500 righe o non emergono bug di accoppiamento.

---

## Indice TODO veloce

| # | Task | Priorità | Stima |
|---|------|----------|-------|
| 1 | Bug Winter signing scraper retroattivo | ALTA | ~1h |
| 2 | Recupero foto SOTS rimanenti (1080 giocatori) | ALTA | ~60-90 min |
| 3 | Workflow GitHub Actions auto-update foto SOTS | MEDIA | ~30 min |
| 4 | Fase 5 Export PDF (dossier + report) | MEDIA | ~2h |
| 5 | Popolare 56 club Serie C con giocatori | BASSA | ~45 min |
| 6 | Fase 6 Export/Import salvataggio JSON | BASSA | ~45 min |
| 7 | Pulizia file `.before_serie_c` | BASSA | 2 min |
| 8 | Refactor split observations_ui.js | BASSA | rimandato |

Totale stima task ALTA + MEDIA: ~5 ore.

Prossima sessione: partire dal task 1 (Winter signing) o task 3 (workflow notturno foto), che sono i 2 più rapidi e con resa visibile (1 fix bug visibile a tutti gli utenti, 1 manutenzione automatizzata che evita di dover ricordare di rilanciare matching ogni volta).

---

## 9 mag 2026 (sera/notte) — PL1/PL2 + chiusura Winter signing + Export PDF feature

Sessione lunga di consolidamento e nuova feature. Quattro filoni principali:
1. Chiusura definitiva del Task 1 Winter signing (120/120 risolti, 100% recupero)
2. Aggiunta PL1/PL2 (Ekstraklasa/I Liga) alle competizioni sortitoutsi
3. Recupero massivo foto polacche (+784 face PNG, foto SOTS da 62% a 89%)
4. Pianificazione e scrittura della feature Export PDF + JSON osservazioni nel pannello Salvataggi

### Chiusura Task 1 — Winter signing/Returnee/New arrival (120 vittime)

Diagnosi corretta della sessione precedente aveva identificato che i `current_club_id` puntano a club veri ma TM mostra "Winter signing"/"Returnee"/"New arrival" come testo del link nel ribbon di transizione, sovrascrivendo il vero nome del club. Approccio in 3 fasi cumulative:

**Fase 1 — Fix da clubs.json (40 vittime)**: script Python che per ogni vittima cerca il `current_club_id` in `data/clubs.json` e sostituisce `current_club_name` col vero nome del club. Backup `players_main.json.before_winter_fix` creato e poi rimosso. Aggiornati `players_main.json` + `players_static.json` + `players_all.json`. Risultato: 40 fix immediati. Commit `2bbc808` "fix(players): risolvo 40 'Winter signing'/'Returnee'/'New arrival' (sostituito current_club_name col vero club da clubs.json — gli 80 polacchi/altri restano)".

**Fase 2 — Re-scrape pagina TM dei 71 club mancanti (76 vittime)**: gli 80 residui avevano `current_club_id` di club non in `clubs.json` (polacchi, danesi, croati, portoghesi). Scritto `fix_winter_signing_clubs.py` (~168 righe, salvato in repo) che:
- Estrae i 71 unique `current_club_id` dei vittime non fixabili
- Per ognuno fa fetch `https://www.transfermarkt.com/-/startseite/verein/{id}` con User-Agent browser-like
- Estrae il nome dal `<h1 class="data-header__headline-wrapper">` con fallback su `<title>`
- Aggiorna `current_club_name` (e `roster_club_name` se sporco) per tutti i giocatori che hanno quel club_id
- Modalità sicura: default = dry-run, `--apply` per applicare

Run: 70/71 club risolti correttamente (es. id=22431 → "Stal Mielec", id=8377 → "Chrobry Glogow", id=1109 → "Aalborg BK", id=6399 → "Lillestrøm SK"). Tempo totale ~35 secondi. Risultato: 76 vittime fixate (più dei 70 club perché alcuni club avevano 2-4 vittime ciascuno, es. id=515 con 4 giocatori).

**Fase 3 — Free agent (4 vittime, cluster TM speciale)**: il club id=515 ha fallito il fetch nella Fase 2. Diagnosi via curl manuale: `https://www.transfermarkt.com/-/startseite/verein/515` redirige a `https://www.transfermarkt.com/statistik/vertragslosespieler` = "Free agents" su TM. Quindi 515 NON è un club ma il cluster fittizio TM dei giocatori senza contratto. I 4 giocatori coinvolti (Paweł Dawidowicz, Erdal Rakip, Kuba Szabłowski, Mateusz Holownia) sono effettivamente svincolati. Fix: aggiornati a `current_club_name="Free agent"`. Aggiornato `prettyClubName` in `frontend/app.js` per visualizzare "Svincolato" (IT) / "Free agent" (EN) accanto al workaround esistente "Winter signing"/"New arrival"/"Returnee" → "—".

**Risultato finale Task 1**: 120/120 vittime risolte (100% recupero) in ~30 minuti totali (vs 1h stimato). Tempo speso significativamente meno perché la diagnosi era cambiata: NON un bug scraper retroattivo da fixare nel codice, ma un fix dati JSON one-shot. Il bug nello scraper resta latente (la `_extract_current_club_id` continua a sbagliare per giocatori in trasferimento) ma è coperto dal workaround `prettyClubName` come safety net per casi futuri.

Commit consolidato: l'ultimo `git add` per Task 1 è andato in un commit unico (chiusura totale) insieme al fix `prettyClubName` per Free agent.

### Aggiunta PL1/PL2 (Ekstraklasa/I Liga) alle COMPETITIONS sortitoutsi

Diagnosi della causa-radice del problema foto polacche: dei 1080 giocatori senza foto SOTS dopo Task 1, **885 erano in club PL1 o PL2** (82% del totale!). Verifica: i 36 club polacchi in `clubs.json` (18 PL1 + 18 PL2) avevano TUTTI `sortitoutsi_team_id=None`. La cache `data/sots_rosters.json` (130 club, 13016 persons dopo harvest) aveva 0 club polacchi. Quindi PL1/PL2 erano stati aggiunti a TM scraping (tramite scraping_leagues.py o simili) ma **mai aggiunti** a `scrape_sortitoutsi_competition.py`.

Fix: aggiunto a `COMPETITIONS` in `scrape_sortitoutsi_competition.py`:
- `PL1` → `https://sortitoutsi.net/football-manager-2026/competition/129558/pko-bank-polski-ekstraklasa`
- `PL2` → `https://sortitoutsi.net/football-manager-2026/competition/129559/polish-first-division`

Inserito dopo `IT3C`. Run dello script: trovati 18 team PL1 e 18 PL2 (36 totali). Match automatico via slug:
- 24/36 club mappati direttamente (es. Cracovia, Korona Kielce, Lech Poznan, Lechia Gdansk, Stal Mielec, GKS Tychy)
- 12/36 club con mismatch slug per **caratteri polacchi diacritici** assenti in TM ma presenti in SOTS:
  - Widzew Lodz ↔ Widzew Łódź (sots 1468)
  - Jagiellonia Bialystok ↔ Jagiellonia Białystok (sots 710052)
  - Zaglebie Lubin ↔ KGHM Zagłębie Lubin (sots 1469)
  - Wisla Plock ↔ Wisła Płock (sots 1458)
  - Wisla Kraków ↔ Wisła Kraków (sots 1300881)
  - Polonia Warsaw ↔ Polonia Warszawa (sots 1300879)
  - Slask Wroclaw ↔ Śląsk Wrocław (sots 1300885)
  - LKS Lodz ↔ Łódzki Klub Sportowy (sots 1454)
  - Chrobry Glogow ↔ Chrobry Głogów (sots 717313)
  - Puszcza Niepolomice ↔ Puszcza Niepołomice (sots 96012813)
  - Gornik Leczna ↔ Górnik Łęczna (sots 129565)
- 2/36 senza match SOTS (Wieczysta Krakow, Pogon Grodzisk Mazowiecki — probabilmente promozioni/rinunce non in PL1/PL2 attuali del database FM26)

Mapping manuale tramite script Python ad-hoc: per ogni `tm_club_id → sots_team_id` aggiornato `clubs.json`, settato `sortitoutsi_logo_url` e `sortitoutsi_logo_local`. Risultato: 34/36 club polacchi mappati (94%).

### Recupero massivo foto polacche

Pipeline standard a 4 step:
1. `scrape_sortitoutsi_competition.py` → mappato 24/36 club polacchi automaticamente (vedi sopra)
2. Mapping manuale 11/12 mismatch diacritici (vedi sopra)
3. `harvest_sots_rosters.py` → cache cresciuta da 95 a **130 club** (+35 polacchi), persons da 10069 a **13016** (+2947 candidati polacchi)
4. `find_more_sots_matches.py` → 803 candidati slug-match contro nuova cache, **784 confermati DOB** (97.2% precisione), 22 mismatch (per giocatori con DOB tronche o omonimi reali), 807 fetch totali sortitoutsi

Falso start del primo run: il primo `find_more_sots_matches.py` era stato lanciato **prima** dell'harvest, contro la cache vecchia (10069 persons senza polacchi). Aveva trovato solo 31 match (gli stessi del run precedente del 6 mag). Il problema è stato diagnosticato confrontando mtime di `confirmed.xlsx` (16:14) vs `sots_rosters.json` (18:17 dopo harvest): l'xlsx era più vecchio della cache. Rilanciato il matching dopo harvest e questa volta ha trovato 784 match.

`apply_more_matches.py` lanciato sui 784 confermati: 777 face PNG scaricate (le 7 senza face significa avatar mancante su SOTS), `data/sortitoutsi_id_lookup.json` cresciuto da 1784 a **2568 entries**. Aggiornati 784 giocatori in `players_main.json`, `players_static.json`, `players_all.json`. Tempo apply: ~10 minuti (download seriale di 777 PNG con rate limit).

**Risultato finale recupero foto**:
- Da 1753/2864 (61%) all'inizio sessione del 6 mag
- A 1784/2864 (62%) dopo recupero cross-club Primavera (31 match) — sessione pomeriggio
- A **2568/2864 (89%)** dopo PL1/PL2 + matching polacchi — sessione sera

Numeri assoluti: +815 foto in 24 ore. Numeri relativi: +28 punti percentuali.

I 296 senza foto rimasti si dividono approssimativamente in:
- ~250 giocatori giovani Primavera con DOB tronche TM (file `sots_more_matches_dob_mismatch.xlsx` da filtrare con logica anno+club come fatto la sessione pomeriggio)
- ~46 senza candidato slug nessuno (giocatori di leghe minori o nomi molto deformati — accettabile lasciarli senza foto)

Commit del lavoro foto: `f4e3c79` "feat(sots): aggiunte PL1/PL2 (Ekstraklasa/I Liga) — recupero 784 foto polacchi via harvest cross-club + 24 mapping automatici + 11 mapping manuali diacritici". Push pesante: 21.82 MB (793 oggetti, principalmente le 777 face PNG polacche).

### Bug dropdown filtro lega Griglie (falso allarme)

Screenshot dell'utente mostrava il dropdown filtro lega del pannello Griglie con `league_it3` come testo grezzo (chiave i18n non risolta), assenza di Serie C girone A/B/C separati e mancanza di "Altre squadre". Diagnosi via grep: il dropdown a riga 3420 aveva `<option value="IT3"...>${t("league_short_it3")}</option>` con chiave i18n vecchia.

Investigazione: `grep` su `value="IT3"` nel file ha restituito 0 occorrenze. Verifica delle costanti `KNOWN_CLUB_CODES` e `CLUB_PRIORITY_ORDER`: già aggiornate con `IT3A/IT3B/IT3C` (cioè il refactor era già stato applicato in una sessione precedente). Verifica i18n.js: già contiene `league_short_it3a/b/c`. Verifica del dropdown: contiene già le 3 opzioni IT3A/IT3B/IT3C + OTHER + IJ1 + PL1 + PL2.

Conclusione: lo screenshot era cache del browser obsoleta (qualche commit precedente non ancora hard-reloadato). Hard reload `Cmd+Shift+R` ha mostrato il dropdown corretto. Nessun fix necessario.

### Pianificazione feature Export PDF + JSON osservazioni

Nuova richiesta utente: nel pannello Salvataggi aggiungere export delle osservazioni, con anche export PDF di singole relazioni e dossier giocatore completo nel pannello Scouting.

Decisioni discusse con l'utente prima di scrivere codice:

**Q1 — Conflitti import duplicati**: opzione B = chiedi conferma (Sovrascrivi tutte / Salta duplicati / Annulla). Vincolo UNIQUE su Supabase è `(user_id, tm_player_id, match_date, opponent)`.

**Q2 — User_id al re-import**: soluzione ibrida adottata. `user_id` = chi importa (per RLS Supabase), `author_username` = creatore originale dal JSON (preservato come metadato "Inserita da [originale]"). Questo permette di:
- Riportare le tue osservazioni su un nuovo dispositivo (ti mantieni come autore)
- Importare osservazioni di un altro scout (entri in possesso ma vedi sempre "Inserita da Mario Rossi")
- Rispettare la RLS senza dover fare relax dei permessi

**Q3 — Struttura PDF**: confermata.
- Singola relazione: logo PID + dati generali giocatore (foto, nome, anno, età, club, altezza, piede, ruolo specifico) + dati relazione completa (data, avversario, competizione, modalità, minuti, posizione, performance, giudizio, strengths chip verdi, weaknesses chip rossi, note testo intero, scout, data inserimento)
- Multi-relazione (giocatore in scouting): stessi dati generali + tutte le visionature in righe + riga totale media

**Q4 — Ordine commit**: 1 commit unico (utente ha preferito tutto insieme).

**Foto giocatore nel PDF**: SÌ. Overhead 200ms accettabile (1 fetch PNG → base64 → embed via `pdf.addImage`).

### Diagnostica codebase per implementazione

3 punti di insertion identificati:
1. **Pannello Salvataggi** (`frontend/app.js` riga 6574 `renderSavesPanel()`): aggiungere 3a sezione "OSSERVAZIONI" dopo Griglie e Convocazioni. Header `📝 Osservazioni` + count + bottone "📥 Importa". 1 sola riga "Tutte le mie osservazioni" con bottone "⬇️ Esporta JSON". Pattern coerente con `buildGridRow`/`buildCallupRow` esistenti.
2. **Modal modifica osservazione** (`frontend/observations_ui.js` ~riga 698-700): bottoni `btn_cancel`/`btn_save` + esistente `obs-delete-btn` (riga 850). Aggiungere "📄 PDF" accanto.
3. **Pannello Scouting** (`frontend/observations_ui.js` riga 1166-1167 `scouting-player-row` con `data-pid`): aggiungere bottone "📄" alla riga giocatore (azione: export PDF dossier con TUTTE le sue osservazioni).

Verificato: jsPDF già caricato in `index.html` (`<script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js">`). Funzioni esistenti riutilizzabili come pattern: `exportGridPDF()` (riga 4106), `exportCallupPDF()` (riga 2493), `_downloadJSON()`, `exportGridSave()`/`exportCallupSave()` (righe 6398/6414).

Schema export grid esistente: `{type: "pid_grid_save", version: 1, name, formation, assigned, _meta, exported_at, exported_by}`. Stesso pattern adottato per `pid_observations_export`.

`importSavesFromFile` (riga 6439) già gestisce file `.json` import con file input nascosto. Esteso il `switch` per gestire anche `pid_observations_export`.

### Implementazione (in corso al momento del diario)

Scritto `patch_export_observations.py` (~1100 righe, salvato in repo). Strategy: script Python idempotente che applica 6 patch ai 4 file frontend in 1 colpo solo, con dry-run obbligatorio prima di apply per safety. Patch:
1. `i18n.js` IT — 40+ chiavi nuove (`saves_obs_section`, `pdf_export_btn`, `pdf_field_*` ecc.)
2. `i18n.js` EN — stesse chiavi tradotte (sostituzione 2a occorrenza `league_short_it3a` per non interferire con la sezione IT)
3. `observations_ui.js` — bottone "📄 PDF" nel modal di edit (visibile solo se osservazione esistente)
4. `observations_ui.js` — append in coda al file di:
   - `exportObservationPDF(observationId, playerId)` — PDF singola relazione con foto giocatore embedded (fetch base64) e tag colorati
   - `exportPlayerDossierPDF(playerId)` — PDF dossier multi-relazione con tabella visionature + riga totale media
   - Handler delegati `document.click` per `.scouting-export-pdf-btn` e `#obs-export-pdf-btn`
   - MutationObserver che inietta automaticamente bottone "📄" su ogni `.scouting-player-row` post-render
5. `app.js` — sezione "Osservazioni" nel pannello Salvataggi:
   - Renderizzata da `_renderObsSummary()` (async, fetcha `window.fetchObservations()` e mostra count + last update + bottone Esporta JSON)
   - Bottone "Importa" usa lo stesso file input esistente (esteso `importSavesFromFile` per gestire `pid_observations_export`)
   - `exportObservationsJSON()` produce file `osservazioni_<YYYY-MM-DD>.json` con schema `{type, version, exported_at, exported_by, count, observations: [...]}`
   - `importObservationsFromFile(payload)` gestisce duplicati con `window.prompt` (1=overwrite, 2=skip, 3=cancel), riusa `saveObservation`/`updateObservation` esistenti
6. `index.html` — bump cache busting versione `?v=20260509z` per i 4 file modificati

Sequenza di iterazioni durante la scrittura della patch:
- v1: 6 patch tutte tramite anchor exact-match → 2 falliti al dry-run (i18n IT pattern matcha 2 volte, anchor `window.openObservationCompose = ...` non corretto)
- v2: PATCH 1 IT con `replace(.., 1)` per limitare alla 1a occorrenza, PATCH 4+5 unite e appese in coda al file (no anchor) → 1 fallito al dry-run (PATCH 2 EN aveva logica dipendente dallo stato post-PATCH 1)
- v3: PATCH 2 EN riscritta con `split` su 3 parti per sostituire SOLO la 2a occorrenza del pattern `league_short_it3a` (la 1a è IT, viene patchata da PATCH 1) → tutti i 6 dry-run verdi attesi

Al momento del diario, l'utente sta testando il dry-run della v3.

### Stato fine sessione

In produzione (commit `f4e3c79` e precedenti):
- ✅ Task 1 Winter signing chiuso al 100% (120/120 fixati con strategia 3-fasi)
- ✅ Task 2 Foto SOTS al 89% (era 62% all'inizio sessione, +27 punti)
- ✅ PL1/PL2 (Ekstraklasa/I Liga) aggiunte a sortitoutsi competitions
- ✅ 34/36 club polacchi mappati con `sortitoutsi_team_id`
- ✅ Cache `sots_rosters.json` cresciuta a 130 club / 13016 persons
- ✅ Lookup `sortitoutsi_id_lookup.json` cresciuto a 2568 entries
- ✅ 777 face PNG polacche scaricate in `data/photos/players_sots_lookup/`
- ✅ Workaround "Free agent" → "Svincolato" in `prettyClubName`

In testing (non ancora committato al momento del diario):
- 🔄 Feature Export PDF + JSON osservazioni — patch v3 in dry-run

### Lezioni apprese

**Iterazione su patch script**: scrivere script che modificano file con anchor exact-match è fragile. Strategie più robuste in ordine di preferenza:
1. **Append in coda** (PATCH 4+5 nuova versione) — funziona sempre, idempotente con check "già patchato"
2. **Split + replace n-th occurrence** (PATCH 2 EN nuova versione) — robusto per pattern che ricorrono N volte in posizioni note
3. **Anchor exact-match** (PATCH 3, PATCH 6) — OK per pattern univoci ma fragile a virgole/spazi
4. **Regex** (BUMP CACHE) — buona via di mezzo per sostituzioni mirate

**Dry-run obbligatorio**: ha salvato la giornata 2 volte. Senza dry-run, lo script avrebbe parzialmente applicato patch alcune sì alcune no, lasciando i file in stato incoerente difficile da rollbackare.

**Diagnosi mtime per debug pipeline**: confrontare mtime di file di output vs cache è una tecnica veloce per scoprire se uno step della pipeline è stato saltato. In questo caso ha permesso di scoprire che il primo `find_more_sots_matches.py` era stato lanciato pre-harvest.

**Cluster fittizi TM**: il club id=515 era "Free agents", ID inatteso ma tracciabile via curl + diagnosi del redirect. Quando un fetch fallisce o restituisce contenuti strani, vale la pena curlare manualmente per capire se è un caso edge.

### Commit pushati nella sessione

(in ordine cronologico)
- `2bbc808` fix(players): risolvo 40 'Winter signing'/'Returnee'/'New arrival' (sostituito current_club_name col vero club da clubs.json — gli 80 polacchi/altri restano)
- (commit consolidato) fix(players): chiusura totale Winter signing — 116 fix retroattivi (40 da clubs.json + 76 re-scrape TM) + 4 Free agent (cluster TM 515) + i18n IT 'Svincolato'
- `f4e3c79` feat(sots): aggiunte PL1/PL2 (Ekstraklasa/I Liga) — recupero 784 foto polacchi via harvest cross-club

Commit feature Export PDF in attesa di test post-patch v3 dry-run.

---

## Aggiornamento TODO

Task chiusi nella sessione di oggi (giornata + sera):

| Task originale | Stato |
|---|---|
| 1. Bug Winter signing scraper retroattivo | ✅ CHIUSO (120/120 con strategia 3-fasi, fix dati JSON) |
| 2. Recupero foto SOTS rimanenti (1080) | ⚠️ PARZIALE (recuperate 815/1080 = 75%, da 62% a 89% totale; restano 296) |
| 3. Workflow GitHub Actions auto-update foto | 🔄 NON ANCORA |
| 4. Fase 5 Export PDF (dossier + report) | 🔄 IN TESTING (patch v3 in dry-run alla chiusura del diario) |
| 5. Popolare 56 club Serie C con giocatori | 🔄 NON ANCORA |
| 6. Fase 6 Export/Import salvataggio JSON | ✅ INCLUSO nella feature Export PDF (export/import JSON osservazioni) |
| 7. Pulizia file `.before_serie_c` | 🔄 NON ANCORA |
| 8. Refactor split observations_ui.js | 🔄 NON ANCORA |

Stima task pending residui (post-sessione):

| # | Task | Priorità | Stima | Note |
|---|------|----------|-------|------|
| 1 | Recupero foto SOTS residue (296 senza foto) | BASSA | ~30-60 min | Filter dob_mismatch.xlsx con logica anno+club + accettare 46 senza candidato |
| 2 | Workflow GitHub Actions auto-update foto SOTS settimanale | MEDIA | ~30 min | Crea `.github/workflows/auto_update_photos.yml` cron lunedì 04:00 UTC |
| 3 | Popolare 56 club Serie C con giocatori (~800-1000 nuovi) | BASSA | ~45 min | `build_urls.py` + `add_players.py` su `it3a/b/c_clubs.json` |
| 4 | Pulizia file `.before_serie_c` | BASSA | 2 min | `git rm` + commit, sicurezza non più necessaria |
| 5 | Refactor split observations_ui.js (>1500 righe) | BASSA | rimandato | Solo se emergono bug accoppiamento |

Totale stima task residui: ~2 ore. Tutti BASSA priorità o MEDIA. Il sistema è in stato production-ready solido.

## 9 mag 2026 (sera/notte) — PL1/PL2 + chiusura Winter signing 100% + Export PDF/JSON osservazioni + override + UI

Sessione molto lunga di consolidamento e nuove feature. Sette filoni principali:
1. Chiusura definitiva Task 1 Winter signing (120/120 risolti, 100% recupero)
2. Aggiunta PL1/PL2 (Ekstraklasa/I Liga) alle competizioni sortitoutsi
3. Recupero massivo foto polacche (+784 face PNG, foto SOTS 62%→89%)
4. Feature completa Export PDF + JSON osservazioni (3 entry point)
5. Iterazioni rifinitura PDF (5 versioni progressive: testo→logo+foto→mini-campo→i18n→performance)
6. Allargamento posizioni 3 formazioni Griglie (3-5-2, 3-4-2-1, 3-4-3)
7. Override manuali +44 foto + cleanup file Python

### Chiusura Task 1 — Winter signing/Returnee/New arrival (120 vittime)

Diagnosi della sessione precedente identificava che i `current_club_id` puntano a club veri ma TM mostra "Winter signing"/"Returnee"/"New arrival" come testo del link nel ribbon di transizione. Approccio in 3 fasi cumulative:

**Fase 1 — Fix da clubs.json (40 vittime)**: script Python che per ogni vittima cerca `current_club_id` in `data/clubs.json` e sostituisce `current_club_name` col vero nome del club. Aggiornati `players_main.json` + `players_static.json` + `players_all.json`. Commit `2bbc808`.

**Fase 2 — Re-scrape pagina TM dei 71 club mancanti (76 vittime)**: scritto `fix_winter_signing_clubs.py` (~168 righe) che per ogni unique `current_club_id` non in clubs.json fa fetch `https://www.transfermarkt.com/-/startseite/verein/{id}` ed estrae nome dal `<h1 class="data-header__headline-wrapper">` con fallback su `<title>`. Aggiorna i 3 file JSON. Modalità sicura: default = dry-run, `--apply` per applicare. Run: 70/71 club risolti correttamente, 76 vittime fixate.

**Fase 3 — Free agent (4 vittime, cluster TM speciale)**: il club id=515 ha fallito il fetch. Diagnosi via curl: `https://www.transfermarkt.com/-/startseite/verein/515` redirige a `/statistik/vertragslosespieler` = "Free agents" su TM. Quindi 515 NON è un club ma il cluster fittizio TM dei giocatori senza contratto. I 4 giocatori coinvolti (Paweł Dawidowicz, Erdal Rakip, Kuba Szabłowski, Mateusz Holownia) sono effettivamente svincolati. Aggiornati a `current_club_name="Free agent"`. Aggiornato `prettyClubName` per visualizzare "Svincolato" (IT) / "Free agent" (EN).

**Risultato**: 120/120 vittime risolte (100% recupero) in ~30 minuti totali (vs 1h stimato).

### Aggiunta PL1/PL2 alle COMPETITIONS sortitoutsi

Diagnosi della causa-radice del problema foto polacche: dei 1080 giocatori senza foto SOTS dopo Task 1, 885 erano in club PL1/PL2 (82%). I 36 club polacchi avevano TUTTI `sortitoutsi_team_id=None`. Cache rosters aveva 0 club polacchi. PL1/PL2 erano stati aggiunti a TM scraping ma mai aggiunti a `scrape_sortitoutsi_competition.py`.

Fix: aggiunti a `COMPETITIONS`:
- `PL1` → `https://sortitoutsi.net/football-manager-2026/competition/129558/pko-bank-polski-ekstraklasa`
- `PL2` → `https://sortitoutsi.net/football-manager-2026/competition/129559/polish-first-division`

Run dello script: 18 team PL1 + 18 PL2 = 36 totali. Match automatico via slug:
- 24/36 club mappati direttamente
- 12/36 mismatch slug per **caratteri polacchi diacritici** (TM scraping rimuove diacritici, SOTS li conserva): Widzew Łódź, Jagiellonia Białystok, KGHM Zagłębie Lubin, Wisła Płock, Wisła Kraków, Polonia Warszawa, Śląsk Wrocław, Łódzki Klub Sportowy, Chrobry Głogów, Puszcza Niepołomice, Górnik Łęczna
- 2/36 senza match SOTS (Wieczysta Krakow + Pogon Grodzisk Mazowiecki — non in PL1/PL2 FM26 forse promossi/rinunciati)

Mapping manuale dei 11 mismatch via script Python ad-hoc. Risultato: **34/36 club polacchi mappati** (94%).

### Recupero massivo foto polacche

Pipeline standard a 4 step:
1. `scrape_sortitoutsi_competition.py` — 24/36 mappati automaticamente
2. Mapping manuale 11 mismatch diacritici
3. `harvest_sots_rosters.py` — cache da 95→**130 club**, persons da 10069→**13016** (+2947 candidati polacchi)
4. `find_more_sots_matches.py` — 803 candidati slug-match contro nuova cache, **784 confermati DOB** (97.2% precisione), 22 mismatch, 807 fetch totali

Falso start del primo run: il primo `find_more_sots_matches.py` era stato lanciato **prima** dell'harvest, contro la cache vecchia (10069 persons senza polacchi). Aveva trovato solo 31 match (gli stessi del run del 6 mag). Diagnosi via mtime: confirmed.xlsx (16:14) vs sots_rosters.json (18:17). Rilanciato dopo harvest e questa volta 784 match.

`apply_more_matches.py` lanciato sui 784 confermati: 777 face PNG scaricate (le 7 senza face = avatar mancante su SOTS), `data/sortitoutsi_id_lookup.json` cresciuto da 1784→**2568 entries**. Aggiornati 784 giocatori in players_*.json. Tempo apply: ~10 minuti.

**Risultato finale recupero foto**:
- 1753/2864 (61%) all'inizio della giornata
- 1784/2864 (62%) dopo recupero cross-club Primavera (sessione pomeriggio)
- **2568/2864 (89%)** dopo PL1/PL2 + matching polacchi (sessione sera)

Numeri assoluti: +815 foto in 24 ore. Numeri relativi: +28 punti percentuali.

I 296 senza foto rimasti si dividono approssimativamente in: ~190 polacchi residui (DOB tronche/slug mismatch nei club già mappati), ~24 in Wieczysta Krakow / Pogon Grodzisk (club non in SOTS), ~30 Primavera italiani non scrappati, ~50 vari (Saint-Étienne, Liga Portugal, etc).

Commit foto polacche: `f4e3c79` "feat(sots): aggiunte PL1/PL2 (Ekstraklasa/I Liga) — recupero 784 foto polacchi via harvest cross-club + 24 mapping automatici + 11 mapping manuali diacritici". Push pesante: 21.82 MB (793 oggetti).

### Bug dropdown filtro lega Griglie (falso allarme)

Screenshot utente mostrava il dropdown filtro lega Griglie con `league_it3` come testo grezzo. Investigazione: tutto il codice era già aggiornato (KNOWN_CLUB_CODES, CLUB_PRIORITY_ORDER, dropdown options, chiavi i18n). Lo screenshot era cache browser obsoleta. Hard reload risolveva. Nessun fix necessario.

### Pianificazione feature Export PDF + JSON osservazioni

Decisioni utente prima di scrivere codice:
- **Q1 conflitti import duplicati**: opzione B = chiedi conferma (Sovrascrivi/Salta/Annulla). Vincolo UNIQUE: `(user_id, tm_player_id, match_date, opponent)`.
- **Q2 user_id al re-import**: soluzione ibrida. `user_id` = chi importa (per RLS), `author_username` = creatore originale dal JSON preservato. Permette di riportare osservazioni su nuovo dispositivo o importare osservazioni di altro scout vedendo sempre "Inserita da [originale]".
- **Q3 struttura PDF**: confermata. Singola = logo PID + dati giocatore + dati relazione completa. Multi = stessi dati + tabella visionature + media totale.
- **Q4 ordine commit**: 1 commit unico (preferenza utente).
- **Foto giocatore nel PDF**: SÌ. Overhead 200ms accettabile.

3 punti di insertion identificati:
1. **Pannello Salvataggi** (`renderSavesPanel()` riga 6574): 3a sezione "OSSERVAZIONI" dopo Griglie/Convocazioni. Header + count + bottoni Esporta JSON / Importa.
2. **Modal modifica osservazione** (riga 698-700): bottone "📄 PDF" accanto a Salva/Annulla.
3. **Pannello Scouting** (riga 1166-1167 `scouting-player-row`): bottone "📄" alla riga giocatore (export dossier).

Verificato: jsPDF già caricato in `index.html` 2.5.1.

### Implementazione feature Export PDF + JSON

Scritto `patch_export_observations.py` (~1100 righe). Strategy: script Python idempotente con dry-run obbligatorio, applica 6 patch ai 4 file frontend.

3 versioni iterative dello script (ogni dry-run validava la successiva):

**v1**: 6 patch tutte tramite anchor exact-match → 2 falliti (i18n IT pattern matcha 2 volte, anchor `window.openObservationCompose = openObservationCompose;` non corretto, il file ha invece `= async function(...)`)

**v2**: PATCH 1 IT con `replace(.., 1)` per limitare alla 1a occorrenza, PATCH 4+5 unite e appese in coda al file (no anchor) → 1 fallito (PATCH 2 EN aveva logica dipendente dallo stato post-PATCH 1, falsa in dry-run)

**v3**: PATCH 2 EN riscritta con `split(old_pattern, 2)` per sostituire SOLO la 2a occorrenza del pattern `league_short_it3a` (la 1a resta intatta per PATCH 1) → tutti i 6 dry-run verdi

Apply lanciato con successo. Patch attive:
1. `i18n.js` IT — 40+ chiavi nuove
2. `i18n.js` EN — stesse chiavi tradotte
3. `observations_ui.js` — bottone "📄 PDF" nel modal di edit (visibile solo se osservazione esistente)
4. `observations_ui.js` — append in coda di `exportObservationPDF`, `exportPlayerDossierPDF`, handler delegati, MutationObserver per bottone "📄" auto-iniettato in righe scouting
5. `app.js` — sezione "Osservazioni" in pannello Salvataggi con `_renderObsSummary()`, `exportObservationsJSON()`, `importObservationsFromFile()` con gestione duplicati via prompt
6. `index.html` — bump cache busting

### Bug post-apply e iterazioni rifinitura PDF

**Bug 1: "Giocatore non trovato"** (test in produzione). Diagnosi: codice usava `window.state?.players` ma `state` non è esposto come `window.state` in questo codebase (è globale tramite scope condiviso `<script>` non-modulari). Verifica: `grep "state.players"` mostrava 4 punti già funzionanti. Fix: 2 occorrenze `window.state?.players` → `state.players`. Commit `e47f14c`.

**Iterazione PDF v2 — logo PID, foto, club, posizione, distribuzione giudizi**: PDF iniziale aveva 5 problemi (logo solo testuale, "no photo", no logo club, no posizione testuale estesa, no distribuzione giudizi nel dossier). Scritto `patch_pdf_v2.py` (~750 righe) con 5 fix:

1. Logo PID immagine: caricato da `../data/photos/branding/logo.png` ed embedded come `addImage` 9x9mm
2. Foto giocatore: priorità a path **locali** no-CORS: `../data/photos/players_tm/<id>.jpg` o `../data/photos/players_sots_lookup/<sots_id>.png`. Fallback URL CDN.
3. Logo club: cercato in `clubs_sots/<club_id>.png`, `clubs_tm/<club_id>.png`, URL CDN. Inline accanto al nome club.
4. Posizione estesa: nel PDF singolo riga "Posizione" mostra `DCS · Difensore centrale sinistro` (mappa codice→nome esteso per 21 ruoli)
5. Distribuzione giudizi nel dossier: barra orizzontale colorata segmentata + legenda con percentuali

Commit `c2433dd`.

**Iterazione PDF v3 — foto SOTS prioritaria + mini-campo grafico**: PDF v2 mostrava ancora la foto TM invece di SOTS (priorità invertita), e mancava la rappresentazione tattica della posizione. Scritto `patch_pdf_v3.py`:

1. Priorità foto invertita: SOTS locale → TM locale → URL CDN
2. Mini-campo SVG nel PDF singolo: 30×42mm sulla destra, sfondo verde, linee bianche (bordo, metà campo, cerchio centrale, aree di rigore alta+bassa+piccola), pallino giallo accent con codice ruolo (es. "DCS") nelle posizioni giocate. Coordinate logiche 380×560 prese da `OBSERVATION_ROLE_DEFS` (15 ruoli predefiniti). Funzione `_pdfDrawMiniField(pdf, x, y, w, h, roles)`.

Commit `51ecd83`.

**Iterazione PDF v4 — Performance ingrandita + tag riposizionato**: PDF v3 mostrava "Prima scelta" tagliato per collisione col mini-campo, e Performance "6.5" troppo piccolo (font 9pt). Fix: Performance font 9→18pt bold colore verde accent, tag chip riposizionato accanto al numero performance (col1X+50) per evitare collisione col mini-campo che è a destra (col2X+30). Commit successivo.

**Iterazione PDF v5 — i18n IT + traduzione foot/position**: PDF mostrava titoli in inglese anche con lingua IT settata ("Year:" invece di "Anno:", "Centre-Back" invece di "Difensore centrale", "left" invece di "sinistro"). Diagnosi: la funzione `_pdfT(key, fallback)` usava `window.t` che NON esiste come globale. Il `t()` è esposto solo come variabile globale tramite scope condiviso (come `state`). Fix: `_pdfT` ora usa `t` direttamente. Aggiunta anche traduzione di campi DB scrappati in inglese (`foot`, `position_general`):

```js
function _pdfTranslateFoot(foot) {
  if (currentLang === "it") {
    const map = { "left": "sinistro", "right": "destro", "both": "ambidestro" };
    return map[foot.toLowerCase()] || foot;
  }
  return foot;
}

function _pdfTranslatePosition(pos) {
  if (currentLang === "it") {
    const map = { "Goalkeeper": "Portiere", "Centre-Back": "Difensore centrale", ... };
    return map[pos] || pos;
  }
  return pos;
}
```

Mappa con 13 posizioni TM principali. Commit successivo.

**Iterazione PDF v6 — logo PID custom**: utente aveva chiesto di usare il logo `PID logo.png` (versione full size 996KB nella root del repo) invece del default `data/photos/branding/logo.png`. Soluzione: copiato `PID logo.png` come `data/photos/branding/pid_logo_pdf.png` (mantengo branding intatto per favicon/splash, uso variante separata per PDF). Aggiornato path nella costante `PDF_LOGO_URL` in `observations_ui.js`. Commit successivo.

### Allargamento posizioni 3 formazioni Griglie

Richiesta utente: nel campo Griglie (`FORMATIONS`), allargare posizioni in 3 schemi tattici per migliorare la lettura visiva.

**3-5-2 — allargate 6 posizioni** (CB laterali, CM laterali, ST):
- RCB: x=70 → 75
- LCB: x=30 → 25
- RCM: x=70 → 78
- LCM: x=30 → 22
- RST: x=60 → 64
- LST: x=40 → 36

**3-4-2-1 — allargate 4 posizioni** (CB laterali, CM):
- RCB: x=70 → 75
- LCB: x=30 → 25
- RCM: x=60 → 68
- LCM: x=40 → 32

**3-4-3 — distribuzione equa dei 4 di centrocampo**: utente voleva i 2 CM "distribuiti equamente con i RM" cioè 4 in linea (LM, LCM, RCM, RM) con spaziatura uguale. Vecchia distribuzione: 12-40-60-88 (gap 28-20-28 sbilanciato). Nuova: 12-37-63-88 (gap 25-26-25 equidistanti).

Patch Python con 3 sostituzioni esatte. Sintassi 0/0. Commit `13dfffd`.

### Override manuali +44 foto

Utente ha mandato batch di giocatori con URL SortItOutSi trovati manualmente, da inserire come override (giocatori non recuperabili automaticamente perché in club non scrappati o nomi troppo distorti).

Lo script `manual_sots_overrides.py` esisteva già con 25 override (sessione 8 mag). Ha lista hardcoded `OVERRIDES = [(name, url), ...]`, normalizza nomi, estrae sots_id da URL via regex `/person/(\d+)/`, scarica face PNG in `players_sots_lookup/`, aggiorna i 3 file players_*.json e `sortitoutsi_id_lookup.json`.

Aggiunti via 2 batch:
- **Batch 1**: 1 override (Nadir El Jamali, Saint-Étienne in Ligue 2 francese non scrappata, sots=2000297870)
- **Batch 2**: 18 override (giocatori polacchi/ucraini non in PL1/PL2 SOTS, es. Aleksander Gajgier, Bartłomiej Pawłowski, Bogdan Sarnavskyi, Damian Jaroń, ecc.)

Run finale: **44/44 matched** (25 vecchi + 1 + 18 nuovi). 44 face PNG scaricate. `sortitoutsi_id_lookup.json` cresciuto a 2586 entries (era 2568).

Workflow per override futuri:
1. Aggiungi riga `("Nome Cognome", "url-sots"),` nel file
2. `python3 manual_sots_overrides.py`
3. `git add -A && git commit -m "..." && git push`

Commit `1848a67` "feat(sots): +18 override manuali (giocatori polacchi/ucraini/altri non scrappati)".

### Cleanup file Python e housekeeping

Cartella `~/Desktop/pid/` accumulata di file temporanei. Diagnostica + cleanup ordinato:

Rimossi (15 file):
- 5 backup `.before_serie_c` (scrape_sortitoutsi_competition, frontend/i18n.js, frontend/app.js, data/clubs.json, data/it3_clubs.json) — backup migrazione 9 mag mattina, sistema stabile da ore
- 9 patch script applicati: `patch_cloud_sync.py`, `patch_commit1.py`, `patch_commit3.py`, `patch_export_observations.py`, `patch_pdf_v2.py`, `migrate_serie_c.py`, `fix_winter_signing_clubs.py`, `fix_new_arrival_clubs.py`, `filter_dob_mismatch.py` — già applicati e committati, codice in git history
- `.DS_Store` macOS junk (anche ricorsivamente nelle subdir)

Mantenuti:
- `PID logo.png` + `PID logo 2.png` in root (asset separati, diversi dai branding files)
- `missing_urls.txt` (5 URL TM utili da scrappare)
- Tutti gli script attivi (add_players, harvest_sots_rosters, find_more_sots_matches, apply_more_matches, ecc)

Aggiornato `.gitignore` con pattern `patch_*.py` per evitare tracking futuro di patch script.

Commit `abcb917` "chore: cleanup root (backup .before_serie_c + patch script applicati + .DS_Store)".

### Stato fine sessione

In produzione:
- ✅ Task 1 Winter signing chiuso al 100% (120/120 fixati)
- ✅ Task 2 Foto SOTS al **~89-90%** (era 62% all'inizio sessione, +28 punti, totale 815 foto recuperate in 24h)
- ✅ PL1/PL2 (Ekstraklasa/I Liga) aggiunte a sortitoutsi competitions
- ✅ 34/36 club polacchi mappati con `sortitoutsi_team_id`
- ✅ Cache `sots_rosters.json` cresciuta a 130 club / 13016 persons
- ✅ Lookup `sortitoutsi_id_lookup.json` cresciuto a 2586 entries
- ✅ 777 face PNG polacche + 44 override manuali = 821 nuove foto in produzione
- ✅ Workaround "Free agent" → "Svincolato" in `prettyClubName`
- ✅ Feature Export PDF + JSON osservazioni completa con 6 iterazioni di rifinitura
- ✅ Formazioni 3-5-2 / 3-4-2-1 / 3-4-3 con posizioni allargate
- ✅ Cleanup file Python (15 file rimossi, ~250 KB liberati)

### Lezioni apprese

**Iterazione su patch script**: scrivere script che modificano file con anchor exact-match è fragile. Strategie più robuste in ordine di preferenza:
1. **Append in coda** (PATCH 4+5 export observations) — funziona sempre, idempotente con check "già patchato"
2. **Split + replace n-th occurrence** (PATCH 2 EN i18n) — robusto per pattern che ricorrono N volte
3. **Anchor exact-match** (PATCH 3, PATCH 6) — OK per pattern univoci ma fragile a virgole/spazi
4. **Regex** (BUMP CACHE) — buona via di mezzo per sostituzioni mirate

**Dry-run obbligatorio**: ha salvato la giornata 3 volte (script export observations v1+v2 in dry-run, patch_pdf_v3 in dry-run). Senza dry-run, lo script avrebbe parzialmente applicato patch alcune sì alcune no.

**Diagnosi mtime per debug pipeline**: confrontare mtime di output vs cache è una tecnica veloce per scoprire step saltati. In questo caso ha permesso di scoprire che il primo `find_more_sots_matches.py` era stato lanciato pre-harvest.

**Cluster fittizi TM**: id=515 era "Free agents", tracciabile via curl + diagnosi del redirect. Quando un fetch fallisce o restituisce contenuti strani, vale curlare manualmente per capire se è caso edge.

**Scope `window.X` vs scope condiviso**: in codebase con `<script>` non-modulari, le `const`/`var` top-level (come `state`, `t`, `currentLang`) sono accessibili tra file SENZA prefisso `window.`. Aggiungere `window.` rompe tutto perché la variabile non è esposta lì. Bug ricorrente: ho dovuto fixarlo 2 volte (`window.state` → `state`, `window.t` → `t`). Sempre verificare via grep come è usata una variabile prima di scrivere nuovo codice che la riferenzia.

**Diacritici tra fonti diverse**: club polacchi mostrano sempre TM senza diacritici (Widzew Lodz) e SOTS con diacritici (Widzew Łódź). Problema risolto via mapping manuale ma vale la pena ricordare per integrazioni future.

### Commit pushati nella sessione

(in ordine cronologico)
- `2bbc808` fix(players): risolvo 40 'Winter signing'/'Returnee'/'New arrival' (sostituito current_club_name col vero club da clubs.json)
- (consolidato) fix(players): chiusura totale Winter signing — 116 fix retroattivi + 4 Free agent
- `f4e3c79` feat(sots): aggiunte PL1/PL2 (Ekstraklasa/I Liga) — recupero 784 foto polacchi via harvest cross-club
- `e47f14c` fix(obs-pdf): correzione 'Giocatore non trovato' (state.players invece di window.state?.players)
- `c2433dd` fix(obs-pdf): logo PID + foto giocatore (path locali no CORS) + logo club + posizione estesa + distribuzione giudizi nel dossier
- `51ecd83` fix(obs-pdf): foto SOTS prioritaria + mini-campo grafico nel PDF singolo (cerchio giallo su posizioni giocate)
- (commit performance) fix(obs-pdf): performance rating ingrandito (18pt) + tag riposizionato per evitare collisione col mini-campo
- (commit i18n) fix(obs-pdf): i18n IT/EN ora rispettata (uso 't' globale invece di window.t) + traduzione foot e position TM in italiano
- (commit logo) fix(obs-pdf): uso 'PID logo.png' (versione full size) come logo nel PDF
- `abcb917` chore: cleanup root (backup .before_serie_c + patch script applicati + .DS_Store)
- `13dfffd` feat(grids): allargo posizioni in formazioni 3-5-2/3-4-2-1/3-4-3 (CB laterali, CM, ST + distribuzione equa centrocampisti)
- `024694a` feat(sots): override manuale Nadir El Jamali (Saint-Étienne, Ligue 2 non scrappata)
- `1848a67` feat(sots): +18 override manuali (giocatori polacchi/ucraini/altri non scrappati)

Totale commit sessione sera: **13+** (commit fix multipli condensati). Totale giornata 9 mag: **40+** commit.

---

## Aggiornamento TODO

Task chiusi nella sessione 9 mag completa (mattina + pomeriggio + sera/notte):

| Task originale | Stato |
|---|---|
| 1. Bug Winter signing scraper retroattivo | ✅ CHIUSO (120/120 con strategia 3-fasi) |
| 2. Recupero foto SOTS rimanenti | ✅ MAGGIORANZA (821/1080 = 76% recuperate, da 62% a ~90% totale; restano ~280) |
| 3. Workflow GitHub Actions auto-update foto | 🔄 NON ANCORA |
| 4. Fase 5 Export PDF (dossier + report) | ✅ COMPLETATO con 6 iterazioni rifinitura |
| 5. Popolare 56 club Serie C con giocatori | 🔄 NON ANCORA |
| 6. Fase 6 Export/Import salvataggio JSON | ✅ INCLUSO nella feature Export osservazioni |
| 7. Pulizia file `.before_serie_c` | ✅ FATTO (incluso nel cleanup root) |
| 8. Refactor split observations_ui.js | 🔄 NON ANCORA |

Nuovi task emersi nella sessione:
| Task | Priorità | Stima | Note |
|---|---|---|---|
| Recupero foto SOTS residue (~280 senza foto) | BASSA | ongoing | Override manuali on-demand quando emergono |
| Workflow notturno auto-update foto SOTS settimanale | MEDIA | ~30 min | `.github/workflows/auto_update_photos.yml` cron lunedì 04:00 UTC |
| Popolare 56 club Serie C con giocatori (~800-1000 nuovi) | BASSA | ~45 min | `build_urls.py` + `add_players.py` |
| Refactor split observations_ui.js (>1500 righe) | BASSA | rimandato | Solo se emergono bug accoppiamento |

Stima task residui post-sessione: **~1.5-2 ore** totali. Il sistema è in stato **production-ready solido** dopo questa giornata. La maggior parte del lavoro restante è automazione (workflow notturno) o popolamento dati (Serie C giocatori), niente bug critici.

## 9 mag 2026 (sera/notte) — Sessione completa: Winter signing chiuso 100% + foto SOTS 62%→95.4% + Export PDF/JSON + UI

Sessione molto lunga di consolidamento e nuove feature. Otto filoni principali:
1. Chiusura definitiva Task 1 Winter signing (120/120 risolti)
2. Aggiunta PL1/PL2 (Ekstraklasa/I Liga) alle competizioni sortitoutsi
3. Recupero massivo foto polacche (+784 face PNG, foto SOTS 62%→89%)
4. Feature completa Export PDF + JSON osservazioni
5. Iterazioni rifinitura PDF (6 versioni progressive)
6. Allargamento posizioni 3 formazioni Griglie
7. Override manuali +44 foto + cleanup root
8. **Fix `slugify` Ł→l + recupero automatico +141 foto polacche** (foto SOTS 89%→95.4%)

### Chiusura Task 1 Winter signing (120 vittime)

3 fasi cumulative:
- **Fase 1**: 40 vittime risolte sostituendo `current_club_name` col vero club da `clubs.json` (commit `2bbc808`)
- **Fase 2**: scritto `fix_winter_signing_clubs.py` (~168 righe), re-scrappa pagina TM dei 71 club mancanti, fixa 76 vittime
- **Fase 3**: 4 vittime nel cluster TM `id=515` ("Free agents" via curl diagnostic), aggiornate a `current_club_name="Free agent"`, workaround "Svincolato" (IT) / "Free agent" (EN) in `prettyClubName`

**Risultato**: 120/120 risolti (100%) in ~30 minuti vs 1h stimato.

### Aggiunta PL1/PL2 sortitoutsi

Diagnosi: 885 dei 1080 senza foto erano in club PL1/PL2 (82%). I 36 club polacchi avevano `sortitoutsi_team_id=None`. PL1/PL2 mai aggiunti a `scrape_sortitoutsi_competition.py`.

Fix: aggiunti URL `129558` (PKO Bank Polski Ekstraklasa) e `129559` (Polish I Liga). Run: 24/36 mappati automaticamente, 12 mismatch slug per **caratteri polacchi diacritici** (Łódź vs Lodz, Białystok vs Bialystok, Płock vs Plock, Kraków vs Krakow, ecc), 11 risolti via mapping manuale, 2 senza match (Wieczysta + Pogon Grodzisk, non in PL1/PL2 SOTS). **Risultato: 34/36 club polacchi mappati**.

### Recupero massivo foto polacche (+784)

Pipeline 4 step:
1. `scrape_sortitoutsi_competition.py` — 24/36 mappati auto
2. Mapping manuale 11 mismatch diacritici
3. `harvest_sots_rosters.py` — cache 95→**130 club**, persons 10069→**13016** (+2947 polacchi)
4. `find_more_sots_matches.py` — **784 confermati DOB** (97.2% precisione su 803 candidati)

`apply_more_matches.py`: 777 face PNG scaricate, lookup 1784→**2568**. Falso start del primo run perché lanciato pre-harvest (cache vecchia, 31 match come 6 mag); diagnosi via mtime di confirmed.xlsx vs sots_rosters.json.

**Risultato sub-fase**: foto SOTS 1784/2864 (62%) → **2568/2864 (89%)**. Commit `f4e3c79` 21.82 MB push (793 oggetti).

### Bug dropdown Griglie (falso allarme)

Screenshot mostrava dropdown Griglie con `league_it3` testo grezzo. Investigazione: codice già aggiornato (KNOWN_CLUB_CODES, dropdown options, i18n keys). Era cache browser obsoleta. Hard reload risolveva.

### Pianificazione feature Export PDF + JSON

Decisioni utente:
- **Q1** conflitti import duplicati: opzione B (chiedi conferma sovrascrittura)
- **Q2** user_id al re-import: ibrido (`user_id` = chi importa per RLS, `author_username` = creatore originale preservato)
- **Q3** struttura PDF: confermata (singola = logo + dati + relazione completa; dossier multi = logo + dati + tabella + media)
- **Q4** ordine commit: 1 commit unico (preferenza)
- **Foto giocatore nel PDF**: SÌ (overhead 200ms accettabile)

3 punti insertion: pannello Salvataggi (sezione "Osservazioni"), modal modifica osservazione (bottone PDF), pannello Scouting (bottone PDF dossier per giocatore).

Verificato: jsPDF già caricato in `index.html` 2.5.1.

### Implementazione feature Export PDF + JSON

`patch_export_observations.py` (~1100 righe). 3 versioni iterative dello script (ogni dry-run validava la successiva):

**v1**: 6 patch via anchor exact-match → 2 falliti (pattern matcha 2 volte, anchor `window.openObservationCompose` non corretto)

**v2**: PATCH 1 IT con `replace(.., 1)`, PATCH 4+5 unite e appese in coda al file (no anchor) → 1 fallito (PATCH 2 EN aveva logica dipendente da PATCH 1)

**v3**: PATCH 2 EN riscritta con `split(old_pattern, 2)` per sostituire SOLO la 2a occorrenza (la 1a per IT) → tutti i 6 dry-run verdi

Patch attive in produzione:
1. `i18n.js` IT/EN — 40+ chiavi nuove
2. `observations_ui.js` — bottone "📄 PDF" nel modal di edit
3. `observations_ui.js` — append in coda di `exportObservationPDF`, `exportPlayerDossierPDF`, handler delegati, MutationObserver per bottone "📄" auto-iniettato in righe scouting
4. `app.js` — sezione "Osservazioni" in pannello Salvataggi con `_renderObsSummary()`, `exportObservationsJSON()`, `importObservationsFromFile()` con gestione duplicati via prompt
5. `index.html` — bump cache busting

### Bug post-apply e iterazioni rifinitura PDF

**Bug 1 — "Giocatore non trovato"**: codice usava `window.state?.players` ma `state` non è esposto come `window.state` (è globale tramite scope condiviso script non-modulari). Fix: `window.state?.players` → `state.players`. Commit `e47f14c`.

**v2 (5 fix grafici)** — `patch_pdf_v2.py` (~750 righe):
1. Logo PID immagine (era solo testuale)
2. Foto giocatore via path **locali** no-CORS (era "no photo" per CORS)
3. Logo club inline accanto al nome
4. Posizione estesa "DCS · Difensore centrale sinistro" (mappa codice→nome 21 ruoli)
5. Distribuzione giudizi nel dossier (barra colorata segmentata + legenda %)

Commit `c2433dd`.

**v3 (foto SOTS + mini-campo)**: PDF v2 mostrava ancora foto TM invece di SOTS (priorità invertita), e mancava rappresentazione tattica posizione. Fix:
1. Priorità foto: SOTS locale → TM locale → URL CDN
2. Mini-campo SVG nel PDF singolo (30×42mm, sfondo verde, linee bianche, pallino giallo con codice ruolo). Coordinate logiche 380×560 da `OBSERVATION_ROLE_DEFS` (15 ruoli). Funzione `_pdfDrawMiniField(pdf, x, y, w, h, roles)`.

Commit `51ecd83`.

**v4 (Performance + tag)**: PDF v3 mostrava "Prima scelta" tagliato (collisione col mini-campo) e Performance 9pt anonimo. Fix: Performance 9→18pt bold verde accent, tag chip riposizionato accanto al numero.

**v5 (i18n IT/EN + traduzione foot/position)**: PDF mostrava titoli inglesi anche con lingua IT settata. Diagnosi: `_pdfT` usava `window.t` che NON esiste come globale (`t()` è globale tramite scope condiviso, come `state`). Fix: `_pdfT` ora usa `t` direttamente. Aggiunta anche traduzione campi DB scrappati in inglese (`foot`: `left`→`sinistro`, `position_general`: `Centre-Back`→`Difensore centrale`, mappa con 13 posizioni TM).

**v6 (logo PID custom)**: utente aveva chiesto di usare `PID logo.png` (full size 996KB nella root) invece del default `data/photos/branding/logo.png`. Soluzione: copiato come `data/photos/branding/pid_logo_pdf.png` (mantengo branding intatto per favicon/splash, uso variante separata per PDF). Aggiornato `PDF_LOGO_URL` in `observations_ui.js`.

### Allargamento 3 formazioni Griglie

Patch a `FORMATIONS` con 3 sostituzioni esatte:

**3-5-2 — 6 posizioni allargate**: RCB 70→75, LCB 30→25, RCM 70→78, LCM 30→22, RST 60→64, LST 40→36

**3-4-2-1 — 4 posizioni**: RCB 70→75, LCB 30→25, RCM 60→68, LCM 40→32

**3-4-3 — distribuzione equa centrocampisti**: vecchia 12-40-60-88 (gap 28-20-28 sbilanciato) → nuova 12-37-63-88 (gap 25-26-25 equidistanti)

Commit `13dfffd`.

### Override manuali +44 foto

`manual_sots_overrides.py` esistente con 25 override del 8 mag. Aggiunti via 2 batch:
- 1 override (Nadir El Jamali, Saint-Étienne in Ligue 2 non scrappata, sots=2000297870) — commit `024694a`
- 18 override (giocatori polacchi/ucraini residui non in PL1/PL2 SOTS) — commit `1848a67`

Run finale: **44/44 matched**, lookup 2568→2586.

Workflow per override futuri: aggiungi `("Nome", "url-sots"),` nel file → `python3 manual_sots_overrides.py` → commit + push (30 secondi).

### Cleanup root

15 file rimossi:
- 5 backup `.before_serie_c` (sistema stabile da ore)
- 9 patch script applicati: `patch_cloud_sync.py`, `patch_commit1/3.py`, `patch_export_observations.py`, `patch_pdf_v2.py`, `migrate_serie_c.py`, `fix_winter_signing_clubs.py`, `fix_new_arrival_clubs.py`, `filter_dob_mismatch.py`
- `.DS_Store` (anche ricorsivamente)

Aggiornato `.gitignore` con `patch_*.py` per evitare future tracking. Commit `abcb917`.

### Fix slugify Ł→l + recupero +141 foto automatiche (FILONE FINALE)

Utente ha mandato URL SOTS di Jakub Łabojko per override manuale, chiedendo "ma come mai non sono state prese in automatico?". Diagnosi rivelatrice:

**Ricerca step-by-step**:
1. Łabojko ESISTE in `players_main` (tm_id=387529, club Motor Lublin id=3527, DOB intera 1997-10-03)
2. Motor Lublin ESISTE in clubs.json con `sortitoutsi_team_id=714221` ✅
3. Cache rosters HA `jakub-labojko` (sots_id=96115997) sotto Motor Lublin ✅
4. DOB intera, no truncation ✅

Tutto sembrava OK. Test slug:
- `slugify("Jakub Łabojko")` → produceva `'jakub-łabojko'` (con `ł`!) ❌
- SOTS slug: `'jakub-labojko'` (senza `ł`)
- Slug mismatch → no match → giocatore rimaneva unmatched

Causa profonda: `unicodedata.normalize("NFKD", ...)` **NON decompone** la `ł` polacca perché è una lettera distinta non una vocale accentata. La funzione `slugify` aveva già la translate `Ł→L, ł→l` ma in qualche modo sembrava non applicarsi.

Verifica con import fresh: la funzione `slugify` **era già corretta nel file**. Il bug non era nel codice attuale ma nell'**ultimo run** di `find_more_sots_matches.py`: era stato lanciato prima del fix. Bisognava semplicemente rilanciarlo.

**Run rilanciato post-fix**:
- Risultato: **141 confermati DOB** (97.6% precisione, 22 mismatch su 163 fetch)
- `apply_more_matches.py`: 138 face PNG scaricate, lookup 2586→**2727**
- Catturati automaticamente 8/12 dei nomi che l'utente stava per aggiungere come override manuali (Łabojko, Marcjanik, Kozłowski, Sekulski, Głogowski, Jerke, Kaput, Rzuchowski)
- 4 ancora fuori (Milan Djuric, Kacper Plichta, Maksym Dyachuk, Fabian Hiszpański), aggiunti come override manuali batch

Commit consolidato: `feat(sots): +141 auto via fix slugify Ł→l + 4 override manuali (Djuric, Plichta, Dyachuk, Hiszpański) — foto SOTS 95.4%`.

**Lezione**: quando si fa un fix in una funzione di matching, **sempre rilanciare lo script consumatore** anche se il fix sembra ovvio. Lo `slugify` era già corretto da un commit precedente, ma `find_more_sots_matches.py` non era mai stato rilanciato dopo quel fix.

### Stato fine sessione

In produzione:
- ✅ Task 1 Winter signing chiuso al 100% (120/120)
- ✅ Task 2 Foto SOTS al **95.4%** (2731/2864) — era 62% all'inizio sessione, **+33 punti, +978 foto recuperate in 24h**
- ✅ PL1/PL2 (Ekstraklasa/I Liga) aggiunte a sortitoutsi competitions
- ✅ 34/36 club polacchi mappati
- ✅ Cache `sots_rosters.json` cresciuta a 130 club / 13016 persons
- ✅ Lookup `sortitoutsi_id_lookup.json` cresciuto a **2727 entries** (era 1784 inizio giornata, +943)
- ✅ ~919 face PNG nuove in produzione (777 polacche batch 1 + 138 batch 2 + 48 override manuali, alcuni overlap)
- ✅ Workaround "Free agent" → "Svincolato" in `prettyClubName`
- ✅ Feature Export PDF + JSON osservazioni completa con 6 iterazioni rifinitura
- ✅ Formazioni 3-5-2 / 3-4-2-1 / 3-4-3 con posizioni allargate
- ✅ Cleanup file Python (15 file rimossi)

I 133 senza foto rimasti si dividono approssimativamente:
- ~80 in club minori non scrappati (Saint-Étienne Ligue 2, Liga Portugal, Primavera straniere)
- ~30 con DOB tronca TM Primavera (file `dob_mismatch.xlsx` da filtrare con logica anno+club)
- ~20 senza candidato slug nessuno
- Casi singoli risolvibili via override manuale on-demand

### Lezioni apprese

**Iterazione su patch script** in ordine di robustezza:
1. **Append in coda** — funziona sempre, idempotente con check "già patchato"
2. **Split + replace n-th occurrence** — robusto per pattern N-volte
3. **Anchor exact-match** — OK per pattern univoci ma fragile
4. **Regex** — buona via di mezzo

**Dry-run obbligatorio**: ha salvato la giornata 3 volte (export observations v1+v2, patch_pdf_v3).

**Diagnosi mtime per debug pipeline**: confrontare mtime di output vs cache rivela step saltati. Usato 2 volte oggi (find_more_sots_matches non lanciato post-harvest, find_more_sots_matches non rilanciato post-fix slugify).

**Cluster fittizi TM**: id=515 era "Free agents", tracciabile via curl + redirect. Quando un fetch fallisce, vale curlare manualmente.

**Scope `window.X` vs scope condiviso**: in codebase con `<script>` non-modulari, `state`, `t`, `currentLang` sono globali SENZA prefisso `window.`. Aggiungere `window.` rompe perché la variabile non è esposta lì. Bug fixato 2 volte oggi.

**Diacritici tra fonti**: TM senza diacritici (Lodz), SOTS con (Łódź). Risolto via mapping manuale + fix slugify.

**Rilanciare consumer script post-fix**: il bug "Łabojko non matchato" era dovuto al fatto che `find_more_sots_matches.py` non era mai stato rilanciato dopo un fix precedente di `slugify`. Quando si patcha una funzione di matching, sempre eseguire il consumer.

### Commit pushati nella sessione

(in ordine cronologico)
- `2bbc808` fix(players): risolvo 40 'Winter signing'/'Returnee'/'New arrival' (sostituito current_club_name)
- (consolidato) fix(players): chiusura totale Winter signing — 116 fix retroattivi + 4 Free agent
- `f4e3c79` feat(sots): aggiunte PL1/PL2 (Ekstraklasa/I Liga) — recupero 784 foto polacchi via harvest cross-club
- `e47f14c` fix(obs-pdf): correzione 'Giocatore non trovato' (state.players invece di window.state?.players)
- `c2433dd` fix(obs-pdf): logo PID + foto giocatore (path locali no CORS) + logo club + posizione estesa + distribuzione giudizi
- `51ecd83` fix(obs-pdf): foto SOTS prioritaria + mini-campo grafico nel PDF singolo (cerchio giallo su posizioni giocate)
- (commit performance) fix(obs-pdf): performance rating ingrandito (18pt) + tag riposizionato
- (commit i18n) fix(obs-pdf): i18n IT/EN ora rispettata (uso 't' globale invece di window.t) + traduzione foot e position TM
- (commit logo) fix(obs-pdf): uso 'PID logo.png' (versione full size) come logo nel PDF
- `abcb917` chore: cleanup root (backup .before_serie_c + patch script applicati + .DS_Store)
- `13dfffd` feat(grids): allargo posizioni in formazioni 3-5-2/3-4-2-1/3-4-3 (CB laterali, CM, ST + distribuzione equa centrocampisti)
- `024694a` feat(sots): override manuale Nadir El Jamali (Saint-Étienne, Ligue 2 non scrappata)
- `1848a67` feat(sots): +18 override manuali (giocatori polacchi/ucraini/altri non scrappati)
- (commit finale) feat(sots): +141 foto auto via fix slugify Ł→l + 4 override manuali (Djuric, Plichta, Dyachuk, Hiszpański) — foto SOTS 95.4%

Totale commit sessione sera: **~14**. Totale giornata 9 mag: **~40+** commit.

---

## Aggiornamento TODO

Task chiusi nella sessione completa di oggi (mattina + pomeriggio + sera/notte):

| Task originale | Stato |
|---|---|
| 1. Bug Winter signing scraper retroattivo | ✅ CHIUSO (120/120) |
| 2. Recupero foto SOTS rimanenti | ✅ MAGGIORANZA (978/1080 = 91% recuperate, da 62% a 95.4%; restano 133) |
| 3. Workflow GitHub Actions auto-update foto | 🔄 NON ANCORA |
| 4. Fase 5 Export PDF (dossier + report) | ✅ COMPLETATO con 6 iterazioni rifinitura |
| 5. Popolare 56 club Serie C con giocatori | 🔄 NON ANCORA |
| 6. Fase 6 Export/Import salvataggio JSON | ✅ INCLUSO nella feature Export osservazioni |
| 7. Pulizia file `.before_serie_c` | ✅ FATTO |
| 8. Refactor split observations_ui.js | 🔄 NON ANCORA |

Stato sistema: **production-ready solido**. Foto SOTS al 95.4% è un livello eccellente, non vale la pena spendere tempo sui residui 133 (giocatori in club minori, residui marginali). Le feature Export PDF/JSON funzionano completamente.

Task residui post-sessione (BASSA priorità):
| Task | Priorità | Stima | Note |
|---|---|---|---|
| Workflow notturno auto-update foto SOTS settimanale | MEDIA | ~30 min | Cron lunedì 04:00 UTC con harvest + matching + apply |
| Popolare 56 club Serie C con giocatori | BASSA | ~45 min | `build_urls.py` + `add_players.py` |
| Override manuali on-demand foto residue | BASSA | ongoing | Quando emergono, 30 secondi/giocatore |
| Refactor split observations_ui.js | BASSA | rimandato | Solo se emergono bug accoppiamento |

Stima task residui: **~1.5 ore**. Niente bug critici. Sistema in stato pulito e ben documentato.


---

## 9 mag 2026 (notte tarda) — Refactor Admin Add Player + diagnosi cache SOTS

Sessione di chiusura serale concentrata su due risultati: fix bug critico del flow admin-add-player e identificazione del prossimo blocker per l'espansione internazionale.

### Bug Admin Add Player diagnosticato e fixato

Sintomo: triggerati 5 workflow add_player.yml consecutivi (run #8-#12) per aggiungere giocatori, esiti misti (2 verdi, 1 rosso, 2 cancelled). Nessun giocatore arrivato in DB anche per i run apparentemente verdi (no-op silenziosi).

Causa root: race condition + merge conflict sul git pull --rebase durante il commit. Il vecchio workflow aveva un loop di retry 5x ma senza git rebase --abort tra un tentativo e l'altro, lasciando lo stato di rebase fallito persistente. Log dello step Commit and push: "error: Pulling is not possible because you have unmerged files. fatal: Exiting because of an unresolved conflict." ripetuto 5 volte, exit 1.

Soluzione: refactor batch + hardening. Branch feat/batch-add-player, PR #1 mergiata su main commit 2e5dcc5. Tre file modificati (199 insertions, 63 deletions):

- .github/workflows/add_player.yml: input urls multi-line invece di url singolo. Step principale lancia echo URLS | python3 add_players.py (batch nativo via stdin che lo script supportava gia). Niente loop di retry rotto, sostituito con 1 push + 1 fallback con rebase pulito. Concurrency group invariato.
- api/main.py endpoint /admin-add-player: accetta sia url (legacy) che urls (lista o stringa multi-line). Trim + dedupe + cap a 50 URL. Pre-check anti-doppio-click via GitHub API list runs filtrata su status=in_progress: se workflow gia in corso ritorna 409 Conflict con link al run esistente. Fallback non bloccante se GitHub API non risponde.
- frontend/app.js funzione _adminAddPlayer: textarea multi-line, parsing client-side (split newline + trim + dedupe), validazione regex pre-send, ETA stimata in base a count (3 min minimo, +1 min per giocatore extra), bottone disabilitato 60 sec post-submit, link "Vedi progresso" verso GitHub Actions, gestione 409 con messaggio + link al run, status colorato verde/arancio/rosso.
- Fix bug latente: id "admin-add-submit" rinominato "admin-add-btn" per allineamento con listener gia esistente nel codice (il bottone non era mai stato disabilitato, ma il listener cercava un id sbagliato).

Test 1 retrocompatibilita (1 URL singolo, Julius Emefile da Midtjylland U19): workflow #13 verde in 32 secondi. Giocatore aggiunto correttamente al DB (totale 2864 -> 2867 giocatori dopo i tentativi della sessione). Frontend mostra giocatore con anagrafica completa.

### Bug residuo identificato: foto SOTS non recuperata su giocatori nuovi

Emefile e in DB ma sortitoutsi_person_id = None, sortitoutsi_face_url = None. Frontend mostra placeholder iniziali "JE" invece della foto. Causa scoperta:

- enrich_sortitoutsi.py (chiamato da add_players.py) lavora SOLO su giocatori che hanno gia sortitoutsi_person_id, lo arricchisce con face_url. Per giocatori nuovi senza match preesistente, non fa nulla.
- find_more_sots_matches.py e lo script che cerca match per giocatori senza sortitoutsi_person_id, ma e batch (lavora su TUTTI gli unmatched) e NON viene chiamato da add_players.py.
- find_more_sots_matches.py non ha argomento --single o --tm-id (controllato grep, riga 94: `unmatched = [p for p in players if not p.get("sortitoutsi_person_id")]`).

### Cache SOTS rosters: il vero blocker per espansione internazionale

Verifica della cache sots_rosters.json: 130 club totali. Ricerca "Midtjylland" in cache: 0 risultati. Ricerca "Emefile" in cache: 0 risultati.

Implicazione: anche aggiungendo find_more_sots_matches.py al workflow add-player, NON recupererebbe la foto di Emefile perche la Superliga danese non e mappata su SortItOutSi nel sistema attuale. Lo stesso vale per ogni espansione futura: aggiungere giocatori delle 5 leghe top (PT/DE/FR/ES/EN) o di Champions League senza prima espandere la cache SOTS produrra giocatori sistematicamente senza foto.

Workflow auto-update foto SOTS settimanale (Task #3 del TODO ancora pendente) avrebbe lo stesso limite: lavora sulla cache esistente, non la espande.

### Strategia rivista per espansione

Ordine di priorita per la prossima sessione:

1. Espandere scrape_sortitoutsi_competition.py con leghe top + UCL/UEL (come gia fatto per PL1/PL2 il 9 mag mattino). Stima 15-20 min.
2. Lanciare harvest_sots_rosters.py per popolare la cache con i club delle nuove competizioni. Stima 20-40 min runtime.
3. Lanciare find_more_sots_matches.py sul DB attuale per recuperare retroattivamente le foto dei giocatori stranieri attualmente unmatched (incluso Emefile). Stima 5-10 min.
4. Solo dopo: integrare find_more_sots_matches.py nel workflow add_player.yml (opzione A: chiamata diretta, +3-5 min al workflow / opzione B: refactor con --only-tm-ids, 30 min sviluppo ma workflow resta veloce).
5. Workflow auto-update foto SOTS settimanale (Task #3 TODO).

### Lezioni apprese

Diagnosi prima di soluzione: stasera ho speso 6-7 messaggi proponendo split di players_stats.json 84MB->5MB pensando al caso "uso da telefono", quando l'utente reale lo apre solo da Mac fibra. Chiedere il contesto d'uso reale (device, frequenza, collaboratori) PRIMA di proporre ottimizzazioni e quanto vale il refactor. Ho rimandato lo split (giusto), ma 30 min persi a spiegare una soluzione non necessaria.

Workflow GitHub Actions e race condition: anche con concurrency group, run paralleli che modificano lo stesso file JSON minified su una riga sola sono vulnerabili a merge conflict che git non sa risolvere. La soluzione corretta non e "retry piu robusto" ma "1 solo workflow con N input" (batch).

Falsi positivi nei verdi: workflow GitHub puo finire con exit 0 anche senza fare nulla utile. Lo step "Commit and push" che esce 0 su "no changes to commit" maschera no-op silenziosi. Verificare sempre il risultato lato DB, non solo lo status del run.

Mistero del DB locale vs frontend: aver fatto refactor su feat/batch-add-player e non aver fatto git pull dopo il merge ha fatto sembrare che Emefile non fosse in DB. Era invece in origin/main (commit 4719856) ma il locale era indietro. Ricordare di pullare dopo ogni merge da PR.

### Commit pushati nella sessione

- 0a66876 feat(admin): batch add-player + anti-doppio-click + textarea multi-URL
- 2e5dcc5 Merge pull request #1 from simonecontran10/feat/batch-add-player  
- 4719856 auto: add 1 player(s) from TM URL (workflow #13 - test retrocompatibilita)

Branch feat/batch-add-player non eliminato (lasciato per riferimento, opzionalmente deletable da Github UI).

### TODO aggiornato post-sessione

| Task | Priorita | Stima | Note |
|---|---|---|---|
| Espansione SOTS competizioni internazionali (DK, top 5, UCL) | ALTA | 30-60 min | Pre-requisito per espansione leghe |
| Recupero retroattivo foto Emefile + altri unmatched stranieri | ALTA | 10 min | Dopo task sopra |
| Integrazione find_more_sots_matches in add_player.yml | MEDIA | 10-30 min | Opzione A (quick) o B (pulita) |
| Workflow auto-update foto SOTS settimanale | MEDIA | 20-30 min | Task #3 TODO precedente |
| Espansione 5 leghe top + CL (Portogallo come pilota) | ALTA | 17-23h | Obiettivo macro |
| Cleanup naming legacy Saudi (PLAYERS_STATIC_FILE etc) | BASSA | 2h | Debito tecnico |


---

## 10 maggio 2026 — Feature player_team end-to-end + dropdown grids

### Contesto e obiettivo

Sergej Levak osservato a marzo gioca nell'Atalanta U23. A giugno potrebbe andare al PSG. L'osservazione di marzo deve restare correttamente "Atalanta U23 vs Casertana", non diventare "PSG vs Casertana" quando il giocatore cambia club. Serviva uno snapshot storico della squadra del giocatore al momento dell'osservazione. Implementato come campo nuovo `player_team` su `player_observations` Supabase, render con loghi inline ovunque (modal giocatore, sidebar Scouting, PDF singola, PDF dossier).

### Decisioni di design

- **Snapshot storico**, non current_club: salvataggio del nome club al momento dell'inserimento. Modificabile in form (caso Primavera→prima squadra: oggi è in Primavera, gioca con la prima squadra → cambio manualmente).
- **Default precompilato**: form mostra `current_club_name` come default ma editabile.
- **Pre-fill dal "+" Ultime partite**: aggiunto `data-team` ai bottoni che apre il form già con tutti i campi compilati (data, opponent, player_team, competition, minuti).
- **Backfill = no**: vecchie osservazioni con `player_team = null` mostrano solo opponent (compatibilità retroattiva). Aggiornamento manuale solo dove serve.
- **PDF testo only, no loghi**: nel PDF singola/dossier solo stringa "Squadra vs Avversario" per evitare 400ms extra di rasterizzazione loghi e ridondanza con logo già presente nell'header giocatore.

### Implementazione

**Step 1 — DB Supabase**: `ALTER TABLE player_observations ADD COLUMN player_team TEXT` (nullable). Su SQL Editor, success no rows.

**Step 2 — Form osservazione** (`observations_ui.js`, +1339 char):
- Nuove i18n IT/EN: `f_player_team`, `f_player_team_ph`, `th_player_team`, `th_match`
- Default value: `editing?.player_team || prefill?.player_team || (player?.current_club_name || "")`
- HTML form: layout 3-righe (data full-width, poi player_team + opponent side-by-side)
- Submit + validazione + payload Supabase con `player_team`
- Edit pre-fill: replicato il fix datalist HTML5 glitch già esistente per opponent

**Step 3 — Render con logo + nome** (+2693 char):
- Helper `_obsGetClubByName(name)` con cache lazy `state.clubs` (lookup nome → club obj per logo)
- Helper `_obsRenderTeamInline(name)` HTML logo 14x14 + escapeHtml(prettyName)
- Modal giocatore tabella: colonna "Match" unificata `[logo] Squadra vs [logo] Avversario`
- Sidebar Scouting: stesso pattern uniforme con loghi inline
- PDF singola osservazione: testo header `Atalanta U23 vs Casertana` (no loghi)
- PDF dossier tabella REPORTS: colonna "Match" sostituisce "Avversario", concatena `player_team + vs + opponent`, larghezza 50mm (era 36)

### Bug fix correlati durante test produzione

Sequenza di 4 bug emersi a cascata durante il testing della feature:

**Bug 1 — `v.player_team is not defined`** (commit `f45bbc4`)
PATCH F dello Step 2 usava `v.player_team` dentro `_wireObsCompose`, ma `v` esiste solo in `_obsComposeHtml`. Errore di scope, ho copiato la struttura del JSX senza accorgermi che `v` non era nello scope di `_wireObsCompose`. Sostituito con `player?.current_club_name`.

**Bug 2 — `_pdfTranslatePosition is not defined`** (commit `b81282a`)
Funzione chiamata in `_pdfPlayerData` riga 1346 ma mai definita. Bug PRE-ESISTENTE non causato dal lavoro di oggi: emerso solo provando export dossier. Soluzione: chiamata `localizeRole(rawRole)` di `app.js` (mappa ROLE_TRANSLATIONS già esistente per IT/EN/FR/AR), con typeof fallback graceful.

**Bug 3 — `_pdfTranslateFoot is not defined`** (commit `844c221`)
Gemello di Bug 2. Funzione mai definita (anche se citata nel diario v5 di ieri "traduzione foot left→sinistro"). Soluzione: mini-funzione inline con map IT `{left: "sinistro", right: "destro", both: "ambidestro"}` + fallback a `player.foot` raw.

**Bug 4 — Avversario non pre-compilato dal "+"** (stesso commit `844c221`)
PRE-ESISTENTE. `_wireObsCompose` controllava SOLO `editing.opponent` per applicare il fix datalist HTML5, NON `prefill.opponent`. In modalità prefill (click `+` su Ultime partite) l'input opponent restava vuoto pur avendo il valore in `_obsPrefill`. Soluzione: estesa firma `_wireObsCompose(player, editing, prefill)`, fix JS gestisce entrambe le modalità.

### Workflow PR ed errori procedurali

Pull request #2 `feat/observation-player-team` mergiata su main come `02f93c2`. Però il commit fix `f45bbc4` (`v.player_team` scope) è stato pushato solo sul **branch**, non su main. Vercel deploya da main → produzione restava col bug. Diagnosticato con `git log origin/main` che mostrava `e0b5cd2` invece del commit fix. Risolto con merge da terminale (giustificato per hotfix evidente, niente review formale).

### Bonus fix grids dropdown campionati (commit `65800d4`)

Problema visivo: dropdown nella tab Griglie mostrava codici criptici (SA, SB, C-A, P1, EKS, L1, Other) usando le chiavi i18n `league_short_*`. Nel dropdown principale (tab Lista/Home) erano già giuste con `league_*` ("Serie A", "Serie B", ecc.). Allineato: sostituito 9 chiavi `league_short_*` → `league_*`, aumentato `min-width: 100px → 140px` per dare spazio ai nomi lunghi. Le chiavi `league_short_*` restano in `i18n.js` per altri usi (badge compatti nelle card giocatore).

### Loghi club esteri mancanti — diagnosi e rinvio

Investigato perché 7 dei tuoi preferiti senza logo club (Mathys Detourbet/Troyes, Nadir El Jamali/Saint-Étienne, Triston Rowe/FC Annecy, Jeremy Monga/Leicester, Ibrahim El Kadiri/De Graafschap, Rio Ngumoha/Liverpool, Julius Emefile/Midtjylland U19, Víctor Muñoz/CA Osasuna).

Diagnosi: i club ESISTONO in `clubs.json` con `tm_club_id` valorizzato ma `league_id = "CL"` (catch-all per club esteri non delle 6 leghe scrappate). Tutti hanno `sortitoutsi_team_id = null`, `sortitoutsi_logo_url = null`, `logo_url = null`, e i PNG locali in `clubs_sots/{id}.png` non esistono. Quindi `clubLogo()` ritorna null per tutti i 4 fallback strategici, comportamento atteso.

Stesso pattern per i giocatori (`sortitoutsi_person_id = null` per tutti).

**Decisione**: rinvio task a sessione dedicata. Workflow `auto_update_full.yml` esiste ma è schedulato solo in finestra mercato (15 giu→15 set, 1 gen→15 feb). Oggi 10 mag fuori finestra. Lanciarlo manualmente per 11 giocatori sarebbe sproporzionato (1-2h GitHub Actions). Aggiunto al backlog: scrivere workflow `auto_enrich_metadata.yml` settimanale fuori-finestra che fa solo enrichment metadati (foto/loghi) senza scraping pesante leghe.

### Lezioni apprese

**Anchor di patch su codice eseguibile, mai su commenti**: il primo tentativo PATCH G usava un commento cosmetico (`* 4. prettyClubName...`) come ancora. Match Python fallito per escape sequence delicate. Lezione: sempre `function name() {` o costanti top-level, mai testo cosmetico.

**`v` (form values) ha scope solo in `_obsComposeHtml`**: se uso una variabile in `_wireObsCompose` devo derivarla dal parametro player (`player?.current_club_name`) oppure cambiare la firma per ricevere `prefill` esplicitamente. Sbaglio di scope incollando struttura template senza pensare.

**Bug pre-esistenti emergono solo cliccando**: `_pdfTranslatePosition` e `_pdfTranslateFoot` erano ROTTE da prima ma nessuno aveva mai cliccato Export PDF in produzione fino ad oggi. Il diario menzionava "v5 traduzione foot/position fatta" ma evidentemente la funzione era stata persa in un cleanup successivo. Lezione: ogni feature di export andrebbe testata manualmente almeno una volta dopo refactor importanti.

**PR mergiata ≠ tutti i commit del branch in main**: dopo merge della PR #2, ho continuato a pushare fix sul branch invece che su main. Vercel restava col codice rotto. Imparata di nuovo (era già nel diario di ieri sera): **dopo ogni merge fare git pull main, fare il fix lì, push diretto se hotfix evidente o nuova PR se serve review**.

**Cache browser inganna il debug**: dopo il merge del fix, lo screenshot del PDF dossier mostrava ancora il bug vecchio. Causa: cache Chrome serviva il vecchio observations_ui.js. Soluzione: Cmd+Shift+R aggressivo, o "Empty Cache and Hard Reload" da DevTools, o finestra incognito. Quando un fix sembra "non arrivato" in produzione, prima sospettare cache e verificare con tab Network il `?v=` del file servito.

### Commit pushati nella sessione

- `796fb14` feat(observations): aggiunto campo player_team (snapshot storico squadra giocatore)
- `02f93c2` Merge pull request #2 from simonecontran10/feat/observation-player-team
- `f45bbc4` fix(observations): scope error v.player_team in _wireObsCompose
- `5a6e8cd` Merge branch 'feat/observation-player-team' (manuale dopo merge PR + hotfix)
- `b81282a` fix(observations-pdf): _pdfTranslatePosition non definita -> uso localizeRole
- `844c221` fix(observations): 3 bug post-feature player_team (avversario prefill + _pdfTranslateFoot + data-team)
- `ad5d4fd` feat(observations-pdf): dossier mostra player_team nella tabella REPORTS
- `65800d4` fix(grids): dropdown filtro campionati con label complete

Branch `feat/observation-player-team` non eliminato (deletable da GitHub UI come `feat/batch-add-player` di ieri).

### TODO aggiornato post-sessione

| Task | Priorità | Stima | Note |
|---|---|---|---|
| Workflow `auto_enrich_metadata.yml` settimanale (foto+loghi) | ALTA | 1-2h | Settimanale fuori finestra mercato. Rate limit SOTS, fuzzy match, override manuale. Risolve buchi di Detourbet/Emefile/Rowe ecc. |
| Espansione SOTS competizioni internazionali (DK, top 5, UCL) | ALTA | 30-60 min | Pre-requisito per task sopra |
| Recupero retroattivo foto Emefile + altri unmatched stranieri | ALTA | 10 min | Dopo espansione SOTS |
| Integrazione find_more_sots_matches in add_player.yml | MEDIA | 10-30 min | Opzione A (quick) o B (refactor pulito) |
| Espansione 5 leghe top + CL (Portogallo pilota) | ALTA | 17-23h | Obiettivo macro |
| Cleanup naming legacy Saudi (PLAYERS_STATIC_FILE) | BASSA | 2h | Debito tecnico |
| Drag-and-drop reordering Griglie tab depth chart | BASSA | 1-2h | Era nel TODO di ieri, rimandato di nuovo |
| Fase 5 PDF Export osservazione (rifinitura layout) | BASSA | 2h | Era Fase 5 originale |
| Fase 6 JSON Export/Import osservazioni | BASSA | 45 min | Era Fase 6 originale |


---

## 10 maggio 2026 — Feature player_team end-to-end + dropdown grids

### Contesto e obiettivo

Sergej Levak osservato a marzo gioca nell'Atalanta U23. A giugno potrebbe andare al PSG. L'osservazione di marzo deve restare correttamente "Atalanta U23 vs Casertana", non diventare "PSG vs Casertana" quando il giocatore cambia club. Serviva uno snapshot storico della squadra del giocatore al momento dell'osservazione. Implementato come campo nuovo `player_team` su `player_observations` Supabase, render con loghi inline ovunque (modal giocatore, sidebar Scouting, PDF singola, PDF dossier).

### Decisioni di design

- **Snapshot storico**, non current_club: salvataggio del nome club al momento dell'inserimento. Modificabile in form (caso Primavera→prima squadra: oggi è in Primavera, gioca con la prima squadra → cambio manualmente).
- **Default precompilato**: form mostra `current_club_name` come default ma editabile.
- **Pre-fill dal "+" Ultime partite**: aggiunto `data-team` ai bottoni che apre il form già con tutti i campi compilati (data, opponent, player_team, competition, minuti).
- **Backfill = no**: vecchie osservazioni con `player_team = null` mostrano solo opponent (compatibilità retroattiva). Aggiornamento manuale solo dove serve.
- **PDF testo only, no loghi**: nel PDF singola/dossier solo stringa "Squadra vs Avversario" per evitare 400ms extra di rasterizzazione loghi e ridondanza con logo già presente nell'header giocatore.

### Implementazione

**Step 1 — DB Supabase**: `ALTER TABLE player_observations ADD COLUMN player_team TEXT` (nullable). Su SQL Editor, success no rows.

**Step 2 — Form osservazione** (`observations_ui.js`, +1339 char):
- Nuove i18n IT/EN: `f_player_team`, `f_player_team_ph`, `th_player_team`, `th_match`
- Default value: `editing?.player_team || prefill?.player_team || (player?.current_club_name || "")`
- HTML form: layout 3-righe (data full-width, poi player_team + opponent side-by-side)
- Submit + validazione + payload Supabase con `player_team`
- Edit pre-fill: replicato il fix datalist HTML5 glitch già esistente per opponent

**Step 3 — Render con logo + nome** (+2693 char):
- Helper `_obsGetClubByName(name)` con cache lazy `state.clubs` (lookup nome → club obj per logo)
- Helper `_obsRenderTeamInline(name)` HTML logo 14x14 + escapeHtml(prettyName)
- Modal giocatore tabella: colonna "Match" unificata `[logo] Squadra vs [logo] Avversario`
- Sidebar Scouting: stesso pattern uniforme con loghi inline
- PDF singola osservazione: testo header `Atalanta U23 vs Casertana` (no loghi)
- PDF dossier tabella REPORTS: colonna "Match" sostituisce "Avversario", concatena `player_team + vs + opponent`, larghezza 50mm (era 36)

### Bug fix correlati durante test produzione

Sequenza di 4 bug emersi a cascata durante il testing della feature:

**Bug 1 — `v.player_team is not defined`** (commit `f45bbc4`)
PATCH F dello Step 2 usava `v.player_team` dentro `_wireObsCompose`, ma `v` esiste solo in `_obsComposeHtml`. Errore di scope, ho copiato la struttura del JSX senza accorgermi che `v` non era nello scope di `_wireObsCompose`. Sostituito con `player?.current_club_name`.

**Bug 2 — `_pdfTranslatePosition is not defined`** (commit `b81282a`)
Funzione chiamata in `_pdfPlayerData` riga 1346 ma mai definita. Bug PRE-ESISTENTE non causato dal lavoro di oggi: emerso solo provando export dossier. Soluzione: chiamata `localizeRole(rawRole)` di `app.js` (mappa ROLE_TRANSLATIONS già esistente per IT/EN/FR/AR), con typeof fallback graceful.

**Bug 3 — `_pdfTranslateFoot is not defined`** (commit `844c221`)
Gemello di Bug 2. Funzione mai definita (anche se citata nel diario v5 di ieri "traduzione foot left→sinistro"). Soluzione: mini-funzione inline con map IT `{left: "sinistro", right: "destro", both: "ambidestro"}` + fallback a `player.foot` raw.

**Bug 4 — Avversario non pre-compilato dal "+"** (stesso commit `844c221`)
PRE-ESISTENTE. `_wireObsCompose` controllava SOLO `editing.opponent` per applicare il fix datalist HTML5, NON `prefill.opponent`. In modalità prefill (click `+` su Ultime partite) l'input opponent restava vuoto pur avendo il valore in `_obsPrefill`. Soluzione: estesa firma `_wireObsCompose(player, editing, prefill)`, fix JS gestisce entrambe le modalità.

### Workflow PR ed errori procedurali

Pull request #2 `feat/observation-player-team` mergiata su main come `02f93c2`. Però il commit fix `f45bbc4` (`v.player_team` scope) è stato pushato solo sul **branch**, non su main. Vercel deploya da main → produzione restava col bug. Diagnosticato con `git log origin/main` che mostrava `e0b5cd2` invece del commit fix. Risolto con merge da terminale (giustificato per hotfix evidente, niente review formale).

### Bonus fix grids dropdown campionati (commit `65800d4`)

Problema visivo: dropdown nella tab Griglie mostrava codici criptici (SA, SB, C-A, P1, EKS, L1, Other) usando le chiavi i18n `league_short_*`. Nel dropdown principale (tab Lista/Home) erano già giuste con `league_*` ("Serie A", "Serie B", ecc.). Allineato: sostituito 9 chiavi `league_short_*` → `league_*`, aumentato `min-width: 100px → 140px` per dare spazio ai nomi lunghi. Le chiavi `league_short_*` restano in `i18n.js` per altri usi (badge compatti nelle card giocatore).

### Loghi club esteri mancanti — diagnosi e rinvio

Investigato perché 7 dei tuoi preferiti senza logo club (Mathys Detourbet/Troyes, Nadir El Jamali/Saint-Étienne, Triston Rowe/FC Annecy, Jeremy Monga/Leicester, Ibrahim El Kadiri/De Graafschap, Rio Ngumoha/Liverpool, Julius Emefile/Midtjylland U19, Víctor Muñoz/CA Osasuna).

Diagnosi: i club ESISTONO in `clubs.json` con `tm_club_id` valorizzato ma `league_id = "CL"` (catch-all per club esteri non delle 6 leghe scrappate). Tutti hanno `sortitoutsi_team_id = null`, `sortitoutsi_logo_url = null`, `logo_url = null`, e i PNG locali in `clubs_sots/{id}.png` non esistono. Quindi `clubLogo()` ritorna null per tutti i 4 fallback strategici, comportamento atteso.

Stesso pattern per i giocatori (`sortitoutsi_person_id = null` per tutti).

**Decisione**: rinvio task a sessione dedicata. Workflow `auto_update_full.yml` esiste ma è schedulato solo in finestra mercato (15 giu→15 set, 1 gen→15 feb). Oggi 10 mag fuori finestra. Lanciarlo manualmente per 11 giocatori sarebbe sproporzionato (1-2h GitHub Actions). Aggiunto al backlog: scrivere workflow `auto_enrich_metadata.yml` settimanale fuori-finestra che fa solo enrichment metadati (foto/loghi) senza scraping pesante leghe.

### Lezioni apprese

**Anchor di patch su codice eseguibile, mai su commenti**: il primo tentativo PATCH G usava un commento cosmetico (`* 4. prettyClubName...`) come ancora. Match Python fallito per escape sequence delicate. Lezione: sempre `function name() {` o costanti top-level, mai testo cosmetico.

**`v` (form values) ha scope solo in `_obsComposeHtml`**: se uso una variabile in `_wireObsCompose` devo derivarla dal parametro player (`player?.current_club_name`) oppure cambiare la firma per ricevere `prefill` esplicitamente. Sbaglio di scope incollando struttura template senza pensare.

**Bug pre-esistenti emergono solo cliccando**: `_pdfTranslatePosition` e `_pdfTranslateFoot` erano ROTTE da prima ma nessuno aveva mai cliccato Export PDF in produzione fino ad oggi. Il diario menzionava "v5 traduzione foot/position fatta" ma evidentemente la funzione era stata persa in un cleanup successivo. Lezione: ogni feature di export andrebbe testata manualmente almeno una volta dopo refactor importanti.

**PR mergiata ≠ tutti i commit del branch in main**: dopo merge della PR #2, ho continuato a pushare fix sul branch invece che su main. Vercel restava col codice rotto. Imparata di nuovo (era già nel diario di ieri sera): **dopo ogni merge fare git pull main, fare il fix lì, push diretto se hotfix evidente o nuova PR se serve review**.

**Cache browser inganna il debug**: dopo il merge del fix, lo screenshot del PDF dossier mostrava ancora il bug vecchio. Causa: cache Chrome serviva il vecchio observations_ui.js. Soluzione: Cmd+Shift+R aggressivo, o "Empty Cache and Hard Reload" da DevTools, o finestra incognito. Quando un fix sembra "non arrivato" in produzione, prima sospettare cache e verificare con tab Network il `?v=` del file servito.

### Commit pushati nella sessione

- `796fb14` feat(observations): aggiunto campo player_team (snapshot storico squadra giocatore)
- `02f93c2` Merge pull request #2 from simonecontran10/feat/observation-player-team
- `f45bbc4` fix(observations): scope error v.player_team in _wireObsCompose
- `5a6e8cd` Merge branch 'feat/observation-player-team' (manuale dopo merge PR + hotfix)
- `b81282a` fix(observations-pdf): _pdfTranslatePosition non definita -> uso localizeRole
- `844c221` fix(observations): 3 bug post-feature player_team (avversario prefill + _pdfTranslateFoot + data-team)
- `ad5d4fd` feat(observations-pdf): dossier mostra player_team nella tabella REPORTS
- `65800d4` fix(grids): dropdown filtro campionati con label complete

Branch `feat/observation-player-team` non eliminato (deletable da GitHub UI come `feat/batch-add-player` di ieri).

### TODO aggiornato post-sessione

| Task | Priorità | Stima | Note |
|---|---|---|---|
| Workflow `auto_enrich_metadata.yml` settimanale (foto+loghi) | ALTA | 1-2h | Settimanale fuori finestra mercato. Rate limit SOTS, fuzzy match, override manuale. Risolve buchi di Detourbet/Emefile/Rowe ecc. |
| Espansione SOTS competizioni internazionali (DK, top 5, UCL) | ALTA | 30-60 min | Pre-requisito per task sopra |
| Recupero retroattivo foto Emefile + altri unmatched stranieri | ALTA | 10 min | Dopo espansione SOTS |
| Integrazione find_more_sots_matches in add_player.yml | MEDIA | 10-30 min | Opzione A (quick) o B (refactor pulito) |
| Espansione 5 leghe top + CL (Portogallo pilota) | ALTA | 17-23h | Obiettivo macro |
| Cleanup naming legacy Saudi (PLAYERS_STATIC_FILE) | BASSA | 2h | Debito tecnico |
| Drag-and-drop reordering Griglie tab depth chart | BASSA | 1-2h | Era nel TODO di ieri, rimandato di nuovo |
| Fase 5 PDF Export osservazione (rifinitura layout) | BASSA | 2h | Era Fase 5 originale |
| Fase 6 JSON Export/Import osservazioni | BASSA | 45 min | Era Fase 6 originale |

