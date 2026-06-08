"""
extract_sots_assets.py — estrazione selettiva dai megapack SortItOutSi.

Workflow:
  1. Legge data/players_all.json + data/clubs.json
  2. Per ogni player con sortitoutsi_face_local_lookup, estrae
     sortitoutsi/faces/face_<sots_id>.png dal cutout megapack →
     data/photos/players_sots_lookup/<sots_id>.png
  3. Per ogni club con sortitoutsi_team_id, estrae
     sortitoutsi Metallic Logos/media/media_<sots_id>.png dal logo pack →
     data/photos/clubs_sots/<tm_club_id>.png
  4. Idempotente: skippa file gia' presenti (puoi rilanciare).

Uso:
  python3 extract_sots_assets.py --faces-rar <path> --logos-rar <path>
  python3 extract_sots_assets.py --faces-only --faces-rar <path>
  python3 extract_sots_assets.py --logos-only --logos-rar <path>

Default paths (se omessi):
  faces: /Volumes/BACK UP/Altro/sortitoutsi_cutout_megapack_2026.06.rar
  logos: /Volumes/BACK UP/Altro/metallic_logos_2026.01.rar

Requisiti:
  brew install unar  # serve `unar` per estrarre dal .rar
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / "data"
PLAYERS_FILE = DATA / "players_all.json"
CLUBS_FILE = DATA / "clubs.json"
FACES_OUT = DATA / "photos" / "players_sots_lookup"
LOGOS_OUT = DATA / "photos" / "clubs_sots"

DEFAULT_FACES_RAR = "/Volumes/BACK UP/Altro/sortitoutsi_cutout_megapack_2026.06.rar"
DEFAULT_LOGOS_RAR = "/Volumes/BACK UP/Altro/metallic_logos_2026.01.rar"


def _load(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def _check_unar() -> None:
    if subprocess.run(["which", "unar"], capture_output=True).returncode != 0:
        print("ERRORE: `unar` non installato. Esegui: brew install unar")
        sys.exit(1)


def extract_from_rar(rar_path: str, archive_paths_to_files: dict[str, Path], desc: str) -> int:
    """
    Estrae i file specificati dal rar e li salva con il nome target.
    2026-06-08: ottimizzato — chiamata UNICA a unar con tutti i path
    (vs N chiamate, ~2000x più veloce).
    """
    if not Path(rar_path).exists():
        print(f"[error] rar non trovato: {rar_path}")
        return 0

    # Filtra giâ presenti
    to_extract: dict[str, Path] = {}
    skip = 0
    for arc, out in archive_paths_to_files.items():
        if out.exists() and out.stat().st_size > 0:
            skip += 1
        else:
            to_extract[arc] = out

    print(f"[{desc}] {len(archive_paths_to_files)} totali, {len(to_extract)} da estrarre, {skip} già presenti")
    if not to_extract:
        print(f"[{desc}] tutto già presente, niente da fare")
        return 0

    t0 = time.monotonic()
    import tempfile
    with tempfile.TemporaryDirectory(prefix="pid_extract_") as tmp:
        tmp_path = Path(tmp)
        # Chiama unar UNA VOLTA con tutti gli archive paths come arg list
        # -q quiet, -o outdir, -D no-dir-struct (estrae senza ricreare path),
        # -f force overwrite. Lista path in coda al comando.
        archive_paths = list(to_extract.keys())
        print(f"[{desc}] estraggo {len(archive_paths)} file in una singola chiamata unar...")
        # In batch per evitare argv overflow (limite OS ~256KB)
        BATCH_SIZE = 500
        n_batches = (len(archive_paths) + BATCH_SIZE - 1) // BATCH_SIZE
        for bi in range(n_batches):
            batch = archive_paths[bi * BATCH_SIZE:(bi + 1) * BATCH_SIZE]
            cmd = ["unar", "-q", "-o", str(tmp_path), "-D", "-f", rar_path] + batch
            try:
                r = subprocess.run(cmd, capture_output=True, timeout=1800)
                elapsed = int(time.monotonic() - t0)
                done = (bi + 1) * BATCH_SIZE
                print(f"  batch {bi+1}/{n_batches} ({done}/{len(archive_paths)}) — {elapsed}s — rc={r.returncode}")
            except subprocess.TimeoutExpired:
                print(f"  batch {bi+1} TIMEOUT")

        # Sposta i file estratti (tmp_path/<basename>) in destination con rename
        ok = 0
        fail = 0
        for arc_path, out_file in to_extract.items():
            extracted = tmp_path / Path(arc_path).name
            if extracted.exists():
                out_file.parent.mkdir(parents=True, exist_ok=True)
                try:
                    extracted.rename(out_file)
                    ok += 1
                except Exception as e:
                    print(f"  [rename fail] {arc_path}: {e}")
                    fail += 1
            else:
                fail += 1
    print(f"[{desc}] DONE: ok={ok}, skip={skip}, fail={fail} in {int(time.monotonic()-t0)}s")
    return ok


def extract_faces(rar_path: str) -> int:
    players = _load(PLAYERS_FILE)
    # Estrae sots_id dal campo sortitoutsi_face_local_lookup ("photos/players_sots_lookup/<id>.png")
    mapping: dict[str, Path] = {}
    for p in players:
        lookup = p.get("sortitoutsi_face_local_lookup") or ""
        m = re.search(r"players_sots_lookup/(\d+)\.png", lookup)
        if not m:
            continue
        sots_id = m.group(1)
        archive_path = f"sortitoutsi/faces/face_{sots_id}.png"
        out_file = FACES_OUT / f"{sots_id}.png"
        mapping[archive_path] = out_file
    return extract_from_rar(rar_path, mapping, "faces")


def extract_logos(rar_path: str) -> int:
    clubs = _load(CLUBS_FILE)
    mapping: dict[str, Path] = {}
    for c in clubs:
        sots_team_id = c.get("sortitoutsi_team_id")
        tm_club_id = c.get("tm_club_id")
        if not sots_team_id or not tm_club_id:
            continue
        archive_path = f"sortitoutsi Metallic Logos/media/media_{sots_team_id}.png"
        out_file = LOGOS_OUT / f"{tm_club_id}.png"
        mapping[archive_path] = out_file
    return extract_from_rar(rar_path, mapping, "logos")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--faces-rar", default=DEFAULT_FACES_RAR)
    ap.add_argument("--logos-rar", default=DEFAULT_LOGOS_RAR)
    ap.add_argument("--faces-only", action="store_true")
    ap.add_argument("--logos-only", action="store_true")
    args = ap.parse_args()

    _check_unar()
    n_faces = n_logos = 0
    if not args.faces_only:
        n_logos = extract_logos(args.logos_rar)
    if not args.logos_only:
        n_faces = extract_faces(args.faces_rar)
    print()
    print(f"SUMMARY: {n_logos} loghi + {n_faces} faces estratti")
    print("Prossimo step: git add data/photos/ && git commit && git push")
    return 0


if __name__ == "__main__":
    sys.exit(main())
