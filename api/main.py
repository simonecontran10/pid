"""
FastAPI backend per la piattaforma giocatori sauditi.

Serve i JSON prodotti dallo scraper come API REST:

    GET /                           healthcheck + last_update
    GET /clubs                      lista club (entrambe le leghe)
    GET /clubs/{tm_club_id}         dettagli club
    GET /clubs/{tm_club_id}/players giocatori sauditi del club
    GET /players                    lista compatta (id, name, club, position) per autocomplete
    GET /players/{tm_player_id}     dettaglio (profilo + stats)
    GET /search?q=...               ricerca giocatori per nome / club
    GET /compare?ids=ID1,ID2        confronto fra due giocatori

Run dev:
    cd api && uvicorn main:app --reload
"""

from __future__ import annotations

import json
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

CLUBS_FILE = DATA_DIR / "clubs.json"
PLAYERS_FILE = DATA_DIR / "players_saudi.json"
STATS_FILE = DATA_DIR / "players_stats.json"
LAST_UPDATE_FILE = DATA_DIR / "last_update.json"


def _load(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


# ============ APP ============
app = FastAPI(
    title="Saudi Players Platform API",
    description="Dati Transfermarkt per i giocatori sauditi di Pro League e First Division.",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# ============ UPDATE JOB STATE ============
class UpdateJob:
    """Tiene traccia di un job run_update.py in esecuzione."""
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.running: bool = False
        self.started_at: Optional[str] = None
        self.completed_at: Optional[str] = None
        self.exit_code: Optional[int] = None
        self.stdout_tail: list[str] = []   # ultime ~200 righe di output
        self.stderr_tail: list[str] = []
        self.elapsed_seconds: int = 0

    def is_running(self) -> bool:
        with self.lock:
            return self.running

    def to_dict(self) -> dict:
        with self.lock:
            return {
                "running": self.running,
                "started_at": self.started_at,
                "completed_at": self.completed_at,
                "exit_code": self.exit_code,
                "elapsed_seconds": self.elapsed_seconds,
                "log_tail": self.stdout_tail[-50:],   # ultime 50 righe per il frontend
            }


update_job = UpdateJob()


def _run_update_subprocess() -> None:
    """Lancia run_update.py come subprocess e logga stdout/stderr."""
    update_job.lock.acquire()
    try:
        if update_job.running:
            return  # già in corso, non lanciare doppio
        update_job.running = True
        update_job.started_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        update_job.completed_at = None
        update_job.exit_code = None
        update_job.stdout_tail = []
        update_job.stderr_tail = []
        update_job.elapsed_seconds = 0
    finally:
        update_job.lock.release()

    t0 = time.monotonic()
    try:
        # Lancia run_update.py dalla root del progetto, attivando il venv.
        # PYTHONUNBUFFERED=1 + flag -u → output line-by-line invece di bloccato a 4KB,
        # così la progress bar nel frontend si aggiorna in tempo reale.
        cmd = ["bash", "-lc",
               f"cd '{ROOT}' && source venv/bin/activate && "
               f"PYTHONUNBUFFERED=1 caffeinate -i python3 -u run_update.py"]
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        # Stream output line-by-line e teniamo le ultime 200
        for line in proc.stdout:
            with update_job.lock:
                update_job.stdout_tail.append(line.rstrip("\n"))
                if len(update_job.stdout_tail) > 200:
                    update_job.stdout_tail = update_job.stdout_tail[-200:]
                update_job.elapsed_seconds = int(time.monotonic() - t0)
        proc.wait()
        with update_job.lock:
            update_job.exit_code = proc.returncode
    except Exception as e:
        with update_job.lock:
            update_job.stderr_tail.append(f"Exception: {e}")
            update_job.exit_code = -1
    finally:
        with update_job.lock:
            update_job.running = False
            update_job.completed_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            update_job.elapsed_seconds = int(time.monotonic() - t0)
        # Ricarica i dati in store
        try:
            store.reload()
        except Exception:
            pass


# ============ STATE ============
class Store:
    def __init__(self) -> None:
        self.clubs: list[dict] = _load(CLUBS_FILE, [])
        self.players: list[dict] = _load(PLAYERS_FILE, [])
        self.stats: list[dict] = _load(STATS_FILE, [])
        self.last_update: dict = _load(LAST_UPDATE_FILE, {})
        self._index()

    def _index(self) -> None:
        self.clubs_by_id = {c["tm_club_id"]: c for c in self.clubs}
        self.players_by_id = {p["tm_player_id"]: p for p in self.players}
        self.stats_by_id = {s["tm_player_id"]: s for s in self.stats}

    def reload(self) -> None:
        self.__init__()  # ricarica


store = Store()


# ============ HELPERS ============
def _player_compact(p: dict) -> dict:
    """Versione compatta per liste / autocomplete."""
    return {
        "tm_player_id": p["tm_player_id"],
        "full_name": p.get("full_name"),
        "name_arabic": p.get("name_arabic"),
        "age": p.get("age"),
        "position_general": p.get("position_general"),
        "position_specific": p.get("position_specific"),
        "current_club_id": p.get("current_club_id"),
        "current_club_name": p.get("current_club_name"),
        "shirt_number": p.get("shirt_number"),
        "photo_url": p.get("photo_url"),
        "sortitoutsi_face_url": p.get("sortitoutsi_face_url"),
        "citizenships": p.get("citizenships", []),
    }


def _player_full(p: dict) -> dict:
    """Profilo completo + stats."""
    out = dict(p)
    s = store.stats_by_id.get(p["tm_player_id"])
    out["stats"] = s if s else {"seasons": {}, "career_totals": {}}
    return out


# ============ ROUTES ============
@app.get("/")
def root() -> dict:
    return {
        "service": "saudi-players-platform",
        "n_clubs": len(store.clubs),
        "n_players": len(store.players),
        "n_with_stats": len(store.stats),
        "last_update": store.last_update,
    }


@app.post("/reload")
def reload_data() -> dict:
    store.reload()
    return {"status": "ok", "n_players": len(store.players)}


@app.post("/update")
def trigger_update(background_tasks: BackgroundTasks) -> dict:
    """Lancia run_update.py in background. Idempotente: se è già in esecuzione, ritorna lo stato corrente."""
    if update_job.is_running():
        return {"status": "already_running", **update_job.to_dict()}
    background_tasks.add_task(_run_update_subprocess)
    return {"status": "started", "started_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}


@app.get("/update/status")
def update_status() -> dict:
    """Stato del job di aggiornamento (in esecuzione, completato, exit code, log tail)."""
    return update_job.to_dict()


@app.get("/clubs")
def list_clubs(league: Optional[str] = Query(None, description="Filtra per league_id (SA1, SA2L)")) -> list[dict]:
    if league:
        return [c for c in store.clubs if c.get("league_id") == league]
    return store.clubs


@app.get("/clubs/{club_id}")
def get_club(club_id: int) -> dict:
    c = store.clubs_by_id.get(club_id)
    if not c:
        raise HTTPException(404, "Club not found")
    return c


@app.get("/clubs/{club_id}/players")
def club_players(club_id: int) -> list[dict]:
    matches = [p for p in store.players if p.get("current_club_id") == club_id]
    return [_player_compact(p) for p in matches]


@app.get("/players")
def list_players(
    q: Optional[str] = None,
    role: Optional[str] = Query(None, description="Filtra per ruolo generico (Goalkeeper, Defender, Midfield, Attack)"),
    sort: str = Query("name", description="name | age_asc | age_desc"),
    limit: int = 0,
) -> list[dict]:
    items = [p for p in store.players]
    if q:
        ql = q.lower()
        items = [p for p in items if (p.get("full_name") or "").lower().find(ql) >= 0
                 or (p.get("current_club_name") or "").lower().find(ql) >= 0]
    if role:
        items = [p for p in items if (p.get("position_general") or "").lower() == role.lower()]
    if sort == "age_asc":
        items.sort(key=lambda p: p.get("age") or 999)
    elif sort == "age_desc":
        items.sort(key=lambda p: -(p.get("age") or 0))
    else:  # name
        items.sort(key=lambda p: (p.get("full_name") or "").lower())
    if limit:
        items = items[:limit]
    return [_player_compact(p) for p in items]


@app.get("/players/{player_id}")
def get_player(player_id: int) -> dict:
    p = store.players_by_id.get(player_id)
    if not p:
        raise HTTPException(404, "Player not found")
    return _player_full(p)


@app.get("/search")
def search(q: str, limit: int = 20) -> dict:
    """Ricerca: ritorna sia giocatori che club che matchano q."""
    ql = q.lower().strip()
    if not ql:
        return {"players": [], "clubs": []}
    pl = [p for p in store.players if (p.get("full_name") or "").lower().find(ql) >= 0]
    pl.sort(key=lambda p: (p.get("full_name") or "").lower())
    cl = [c for c in store.clubs if (c.get("name") or "").lower().find(ql) >= 0]
    cl.sort(key=lambda c: (c.get("name") or "").lower())
    return {
        "players": [_player_compact(p) for p in pl[:limit]],
        "clubs": cl[:limit],
    }


@app.get("/compare")
def compare(ids: str) -> dict:
    """ids=123,456 → confronto fra 2 (o più) giocatori."""
    try:
        id_list = [int(x.strip()) for x in ids.split(",") if x.strip()]
    except ValueError:
        raise HTTPException(400, "ids deve essere lista CSV di interi, es. ?ids=195332,68626")
    out = []
    for pid in id_list:
        p = store.players_by_id.get(pid)
        if not p:
            continue
        out.append(_player_full(p))
    return {"players": out}


@app.get("/stats/{player_id}")
def player_stats(player_id: int) -> dict:
    s = store.stats_by_id.get(player_id)
    if not s:
        raise HTTPException(404, "Stats not found")
    return s
