"""
update_diario_pid.py — Appende la sessione 19 maggio al diario PID.

Idempotente: se la sezione "## 19 maggio 2026" esiste gia', non duplica.
Fa backup prima.

Uso:
    cd ~/Desktop/pid
    python3 update_diario_pid.py
"""
import time
from pathlib import Path

F = Path("progetto-pid.md")
SECTION_TAG = "## 19 maggio 2026 (martedi) — WC2026 espansione +10 nazionali (9→19, 496/496)"

ENTRY = f"""

---

{SECTION_TAG}

Sessione di espansione WC2026 da 9 a 19 nazionali (235 → 496 giocatori, tutti
risolti). Tre commit pushati: `e893066` (+6 nazionali via pipeline standard),
`6f19129` (8 override → 393/393), `92ad8e5` (+4 nazionali via bypass parser →
496/496). Verifica cron notturno: il fix conflitti `last_update.json` ha retto
al primo giro reale in produzione (2 commit bot del 18 mag verdi).

### Fase 1 — +6 nazionali via pipeline standard (commit e893066)

Stato iniziale: 9 nazionali (Bosnia, France, Iraq, Japan, New Zealand, Belgium,
Haiti, Tunisia, South Korea), 235 giocatori, tutti risolti.

`parse_wikipedia_squad.py --all` ha aggiunto 6 nuove final: **Austria, Cape
Verde, Curaçao, DR Congo, Portugal, Scotland**. La patch anti-overwrite ha
funzionato perfettamente: nessun tm_id perso su giocatori comuni delle 9
preesistenti.

Falso allarme Belgium (`27/27 → 26/26`): diagnosticato come cambio-rosa
legittimo Wikipedia. Il portiere Vandevoordt (tm_id 486046) e' uscito dalla
rosa, nessun giocatore comune ha perso il tm_id. Lo script di scrape sicuro
(`wc2026_scrape_safe.py`) aveva alzato un allarme prudente "rosa cambiata" che
e' stato gestito con script diagnostico `diff_belgium.py` (confronto nominale
pre/post). Confermato che e' un comportamento corretto e additivo del parser.

Resolve per-nazione via `resolve_wc2026_from_squad.py` (mai `--reresolve`):
Austria 26/26, Curaçao 26/26 perfette al primo colpo; Cape Verde 25/26,
Scotland 25/26, DR Congo 24/26, Portugal 25/28 con qualche non risolto.

### Fase 2 — 8 override manuali → 393/393 (commit 6f19129)

I non risolti erano tutti casi di mismatch DOB Wikipedia↔TM o assenza dalla
pagina-rosa TM `saison_id=2026` (sorprendentemente, anche titolari del calibro
di Diogo Costa, Ruben Dias, Nelson Semedo non comparivano sulla pagina-rosa
nazionale di TM). Diagnosticato via `debug_tm_squad_page.py` che la pagina-rosa
del Portogallo conteneva 26 portoghesi ma diversi dai 28 della convocazione WC.

8 tm_id recuperati e verificati via Transfermarkt (DOB controllata):
- Portugal: Diogo Costa 357153, Ruben Dias 258004, Nelson Semedo 231572
- DR Congo: Gedeon Kalulu 395685, Gael Kakuta 74297
- Scotland: Findlay Curtis 1082993 (DOB Wiki 09/06/06 vs TM 01/10/06, identita
  certa: nome completo/club/nazionale/anno coerenti)
- Cape Verde: Sidny Lopes Cabral 611855 (JSON 2003 vs fonti 2002, identita certa)
- Bosnia: Arjan Malic 805534 (nuovo da cambio-rosa, +1 a 27/27)

**Scoperta meccanismo override**: `resolve_wc2026_from_squad.py` (alternativo,
per non-latini) NON legge `wc2026_overrides.json`. Solo `resolve_wc2026_urls.py`
lo carica (load_overrides righe 384+ e applica via override_key=f"{{country}}|{{name}}"
righe 451-462). Senza `--reresolve`, lo script processa solo i non risolti e
preserva i gia risolti. Testato dry-run su Portugal: 3 override applicati, 25
gia risolti preservati, dry-run NON scrive. Esteso a Croatia/DR Congo/Scotland/
Cape Verde/Bosnia: 10 non-target verificate INTATTE, 5 target a 100%, totale
393/393.

`urls_wc2026.txt` troncato dal loop per-nazione (`resolve_wc2026_urls.py --country`
sovrascrive il file con i soli URL dell'ultima nazione processata). Riparato
con `rigen_urls_wc2026.py` che lo ricostruisce completo dal raw JSON.

### Fase 3 — +4 nazionali via bypass parser (commit 92ad8e5)

Nuove rose final pubblicate tra 12-18 mag: **Brazil, Croatia, Ivory Coast, Sweden**.
`parse_wikipedia_squad.py --all` non le ha importate (status `[unknown]` per
Brazil/Ivory Coast/Sweden, `[preliminary]` per Croatia, tutte skippate).

`--include-preliminary` su Brazil: **timeout** (90s di test via subprocess Python
in `test_brazil_parser.py`). Parser si impicca o entra in loop sulla pagina
Wikipedia del Brasile in modalita preliminary. Bug strutturale del parser su
formato pagina delle rose appena annunciate.

**Soluzione: bypass parser**. Le 4 rose definitive (incollate dall'utente da
Wikipedia) iniettate direttamente nel formato JSON via `inject_4_nazionali.py`
(104 giocatori, schema country/wiki_url/status=final/imported_at/players con
campi name/dob/pos/caps/goals/club, tm_player_id=None). Lo script: backup,
abort se le 4 esistono gia o se una delle 15 viene toccata, verifica finale.

Resolve via `resolve_wc2026_from_squad.py` per-nazione (URL-rosa TM cercati
via web): Brazil ID 3439 → 26/26, Sweden 3557 → 26/26 (perfette al primo colpo,
nomi latini + DOB note), Croatia 3556 → 25/26 (Toni Fruk mismatch DOB), Ivory
Coast 3591 → 25/26 (Agbadou mismatch DOB).

**Portugal cambiato sotto di noi**: lo scrape `--all` della sessione serale
ha rinfrescato la rosa portoghese (Wikipedia aggiornata): rimossi Diogo Costa,
Ruben Dias, Nelson Semedo (i 3 override di stamattina); aggiunti Bernardo Silva,
Cristiano Ronaldo, Rafael Leao. Stesso fenomeno: 3 titolari assenti dalla
pagina-rosa TM. Override aggiornati:

- Portugal: Bernardo Silva 241641, Cristiano Ronaldo 8198, Rafael Leao 357164
- Croatia: Toni Fruk 432758 (Wiki 09/04 vs TM 09/03)
- Ivory Coast: Emmanuel Agbadou 683895 (Wiki 07/06 vs TM 17/06)

5 override aggiunti (wc2026_overrides.json 21→26), applicati con
`resolve_wc2026_urls.py --country` senza `--reresolve`, verifica 19 nazionali
tutte a 100%: **TOTALE 496/496**.

Merge con origin/main (3 add-player Admin del giorno + 2 daily refresh):
nessun conflitto reale (file diversi), merge commit `5ea9fc6`, push pulito.

### Lezioni della sessione

1. **`--reresolve` resta vietato, ma `resolve_wc2026_urls.py --country` senza
   il flag e' sicuro e additivo**. Lo script applica gli override come primo
   check e salta i gia risolti. Testato dry-run + verifica prima/dopo che le
   non-target restino intatte: i 10 target/non-target di stamattina e i 16
   non-target di stasera tutti preservati.

2. **`urls_wc2026.txt` e' un file derivato volatile**. Il loop
   `resolve_wc2026_urls.py --country` lo riscrive con i soli URL dell'ultima
   nazione processata. Va SEMPRE rigenerato da `wc2026_squads_raw.json` dopo
   un batch di per-nazione (script `rigen_urls_wc2026.py`). Mai committarlo
   senza prima un `wc -l` di verifica.

3. **Le rose cambiano su Wikipedia anche tra una sessione e l'altra**. Portugal
   stamattina 28 (Diogo Costa/Dias/Semedo non risolti), stasera 27 (Bernardo
   Silva/Ronaldo/Leao non risolti). Non e' bug: e' la realta che muta. Gli
   override vanno aggiornati ad ogni scrape, non sono "una tantum".

4. **`parse_wikipedia_squad.py` ha un bug strutturale**: si impicca con
   `--include-preliminary` su rose appena annunciate (status [unknown]).
   Da indagare e fixare in sessione dedicata - col 2 giugno come deadline FIFA,
   le ~29 nazionali restanti continueranno a produrre lo stesso problema, e il
   bypass manuale (incolla-rosa + inject) non scala bene.

5. **L'iniezione manuale e' una valida fallback** quando il parser fallisce:
   schema noto, validazione a valle (match-DOB nel resolve), idempotente,
   isolata (non tocca le altre nazionali). Pattern riusabile.

6. **L'Admin di PID funziona benissimo in produzione**: l'utente ha aggiunto
   3 giocatori durante la sessione (`64a7b82`), il workflow add_player.yml ha
   committato e pushato senza problemi. Il merge con i nostri commit WC2026
   pulito.

### Backlog aggiornato post-sessione 19 mag

**Priorita alta**:
1. **Automazione cron WC2026**: integrare `parse_wikipedia_squad.py --all` +
   `resolve_wc2026_from_squad.py` nel `auto_update_daily.yml` per pescare le
   ~29 rose restanti man mano che escono (deadline 2 giugno). Tocca workflow
   di produzione: sessione dedicata, attenta, mai `--reresolve`.
2. **Fix bug parser timeout**: `parse_wikipedia_squad.py` si impicca con
   `--include-preliminary` su Brazil (e probabilmente altre pagine simili).
   Da indagare il punto di loop/attesa infinita. Se non fixato, ogni nuovo
   gruppo di rose richiedera bypass manuale.

**Priorita media**:
3. tag_wc2026.py (campi wc2026_squad/shirt/pos su players_all)
4. Frontend filter "Mondiale 2026"
5. Import nel DB se ancora rilevante (235 player import gia documentato 16-17 mag)

**Backlog precedente invariato**: Megapack SOTS, auto_enrich_metadata settimanale,
espansione SOTS internazionali, espansione 5 leghe top, bug SOTS face/person_id,
drag-drop Griglie, Fase 5 PDF / Fase 6 JSON osservazioni, bug enrich_sortitoutsi.

### Stato infra post-sessione 19 mag

- **Conflitti cron daily refresh**: il fix definitivo (merge driver newer-json)
  ha retto al primo giro reale (run 18 mag verdi su GitHub Actions). Tre cron
  verdi nelle ultime 24h (`bac4acd`, `0674a2f`, `cb6aa3f`, `7e8239c`).
- **WC2026**: 19/48 nazionali, 496 player tutti risolti, 26 override manuali.
  Pipeline robusta MA con bug parser noto su nuove rose [unknown]/[preliminary].
- **Admin add-player**: funzionante in produzione (3 giocatori aggiunti
  durante la sessione, commit `64a7b82`).

### File chiave / script generati

Versionati (committati): `data/wc2026_squads_raw.json` (19 naz / 496 player),
`data/wc2026_overrides.json` (26 override), `urls_wc2026.txt` (496 URL).

Non versionati (utility one-shot, restano nella root come `.py` untracked):
`wc2026_scrape_safe.py`, `wc2026_scrape_safe_v2.py`, `diff_belgium.py`,
`add_overrides_wc2026.py`, `add_overrides_5.py`, `apply_overrides_real.py`,
`safe_apply_overrides_test.py`, `diag_overrides.py`, `inspect_overrides.py`,
`rigen_urls_wc2026.py`, `inject_4_nazionali.py`, `test_brazil_parser.py`.

Backup .bak-* di sicurezza presenti in `data/` e radice (utili per rollback
selettivi, mai versionati).
"""


def main():
    if not F.exists():
        print(f"ERRORE: {F} non trovato")
        return 1
    s = F.read_text(encoding="utf-8")
    if SECTION_TAG in s:
        print(f"Sezione '{SECTION_TAG}' gia presente. Nothing to do.")
        return 0
    ts = time.strftime("%Y%m%d_%H%M%S")
    bak = F.with_suffix(f".md.bak-diario-{ts}")
    bak.write_text(s, encoding="utf-8")
    F.write_text(s.rstrip() + ENTRY, encoding="utf-8")
    new_lines = len(F.read_text(encoding="utf-8").splitlines())
    print(f"OK: sezione 19 mag aggiunta a {F}. Righe ora: {new_lines}")
    print(f"Backup: {bak.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
