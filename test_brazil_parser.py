"""
test_brazil_parser.py — Lancia parse_wikipedia_squad.py su Brazil
con --include-preliminary --dry-run, con TIMEOUT Python (90s) cosi'
non resta mai appeso. Diagnostica se si blocca e dove.

Uso:
    cd ~/Desktop/pid
    source venv/bin/activate
    python3 test_brazil_parser.py
"""
import subprocess
import sys

CMD = [sys.executable, "parse_wikipedia_squad.py",
       "--country", "Brazil", "--include-preliminary", "--dry-run"]

print("Lancio:", " ".join(CMD))
print("Timeout: 90s (se supera, lo script si impicca su Brazil)\n")

try:
    proc = subprocess.run(CMD, capture_output=True, text=True, timeout=90)
    print("=== STDOUT (ultime 45 righe) ===")
    for ln in proc.stdout.splitlines()[-45:]:
        print(ln)
    if proc.stderr.strip():
        print("\n=== STDERR (ultime 15) ===")
        for ln in proc.stderr.splitlines()[-15:]:
            print(ln)
    print(f"\n=== EXIT: {proc.returncode} ===")

    # Conta giocatori estratti, se presenti
    out = proc.stdout
    import re
    # cerca un eventuale conteggio tipo "X giocatori"
    m = re.findall(r"(\d+)\s+giocatori", out)
    if m:
        print(f"Conteggio giocatori trovato nell'output: {m}")
    # cerca nomi-chiave della rosa definitiva Brazil
    key = ["Alisson", "Marquinhos", "Casemiro", "Neymar",
           "Vinícius", "Raphinha", "Endrick", "Rayan"]
    found = [k for k in key if k in out]
    print(f"Nomi-chiave rosa definitiva presenti: {found}")
    if len(found) >= 5:
        print(" -> sembra la rosa DEFINITIVA (26)")
    elif found:
        print(" -> alcuni nomi presenti, da verificare conteggio (26 vs 55)")
    else:
        print(" -> nessun nome-chiave: rosa non estratta o formato diverso")

except subprocess.TimeoutExpired:
    print("=== TIMEOUT 90s: lo script SI IMPICCA su Brazil ===")
    print("parse_wikipedia_squad.py non riesce a processare la pagina")
    print("Wikipedia del Brasile (loop o attesa infinita). Il flag")
    print("--include-preliminary su questa pagina e' problematico.")
    print("\nNON forzare. Conviene fermarsi e affrontarlo a mente fresca")
    print("con un approccio diverso (es. parsing mirato o inserimento")
    print("controllato della rosa nota).")

print("\n[fine test - nessuna scrittura, era --dry-run]")
