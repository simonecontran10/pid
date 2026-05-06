"""
Import dei file Wyscout (.xlsx) in JSON normalizzato.

Wyscout esporta ~115 colonne; teniamo solo i campi rilevanti per la UI:
identità, anagrafica, stats di alto livello (Goals, xG, Assists, xA, ecc.)
e alcune stats per-90 utili.

Output: data/wyscout_players.json
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Optional

try:
    import pandas as pd
except ImportError:  # pragma: no cover
    pd = None  # type: ignore


# Solo i campi che ci interessano davvero (su 115)
KEEP_FIELDS: dict[str, str] = {
    # identity
    "Player": "wyscout_name",
    "Team": "wyscout_team",
    "Team within selected timeframe": "wyscout_team_period",
    "Position": "wyscout_positions",
    # anagrafic
    "Age": "age_wyscout",
    "Birth country": "birth_country",
    "Passport country": "passport_country",
    "Foot": "foot_wyscout",
    "Height": "height_wyscout",
    "Weight": "weight_wyscout",
    "Market value": "market_value_eur",
    "Contract expires": "contract_expires",
    "On loan": "on_loan",
    # season totals
    "Matches played": "wyscout_apps",
    "Minutes played": "wyscout_minutes",
    "Goals": "wyscout_goals",
    "Assists": "wyscout_assists",
    "Yellow cards": "wyscout_yellow",
    "Red cards": "wyscout_red",
    "Clean sheets": "wyscout_clean_sheets",
    "Conceded goals": "wyscout_conceded",
    "xG": "xg_total",
    "xA": "xa_total",
    "Shots": "shots_total",
    # per-90 metrics più rilevanti
    "Goals per 90": "goals_p90",
    "xG per 90": "xg_p90",
    "Assists per 90": "assists_p90",
    "xA per 90": "xa_p90",
    "Shots per 90": "shots_p90",
    "Shots on target, %": "shots_on_target_pct",
    "Goal conversion, %": "goal_conversion_pct",
    "Duels per 90": "duels_p90",
    "Duels won, %": "duels_won_pct",
    "Defensive duels per 90": "def_duels_p90",
    "Defensive duels won, %": "def_duels_won_pct",
    "Aerial duels per 90": "aerial_duels_p90",
    "Aerial duels won, %": "aerial_duels_won_pct",
    "Dribbles per 90": "dribbles_p90",
    "Successful dribbles, %": "dribbles_success_pct",
    "Offensive duels per 90": "off_duels_p90",
    "Offensive duels won, %": "off_duels_won_pct",
    "Interceptions per 90": "interceptions_p90",
    "Sliding tackles per 90": "sliding_tackles_p90",
    "Touches in box per 90": "touches_in_box_p90",
    "Progressive runs per 90": "prog_runs_p90",
    "Accelerations per 90": "accelerations_p90",
    "Passes per 90": "passes_p90",
    "Accurate passes, %": "passes_accuracy_pct",
    "Forward passes per 90": "fwd_passes_p90",
    "Accurate forward passes, %": "fwd_passes_acc_pct",
    "Long passes per 90": "long_passes_p90",
    "Accurate long passes, %": "long_passes_acc_pct",
    "Smart passes per 90": "smart_passes_p90",
    "Key passes per 90": "key_passes_p90",
    "Passes to final third per 90": "passes_to_final_third_p90",
    "Passes to penalty area per 90": "passes_to_box_p90",
    "Through passes per 90": "through_passes_p90",
    "Progressive passes per 90": "prog_passes_p90",
    "Crosses per 90": "crosses_p90",
    "Accurate crosses, %": "crosses_accuracy_pct",
    "Shot assists per 90": "shot_assists_p90",
    "Fouls per 90": "fouls_p90",
    "Fouls suffered per 90": "fouls_suffered_p90",
    # goalkeeper
    "Conceded goals per 90": "conceded_p90",
    "Save rate, %": "save_rate_pct",
    "xG against": "xg_against_total",
    "xG against per 90": "xg_against_p90",
    "Prevented goals": "prevented_goals_total",
    "Prevented goals per 90": "prevented_goals_p90",
    "Exits per 90": "exits_p90",
}


def _slugify_name(name: str) -> str:
    """Slug per matching: lowercase, no accents, no punctuation, single spaces."""
    if not name:
        return ""
    nfkd = unicodedata.normalize("NFKD", name)
    no_accents = "".join(ch for ch in nfkd if not unicodedata.combining(ch))
    cleaned = re.sub(r"[^a-zA-Z\s\-']", " ", no_accents).lower()
    return re.sub(r"\s+", " ", cleaned).strip()


def _parse_height(s: Any) -> Optional[int]:
    """Wyscout fornisce altezza in cm come float (es. 178.0)."""
    if s is None or (isinstance(s, float) and pd is not None and pd.isna(s)):
        return None
    try:
        return int(float(s))
    except (ValueError, TypeError):
        return None


def _parse_market_value(s: Any) -> Optional[int]:
    """Wyscout: '€ 250,000', '€ 1.50M' → int EUR. Wyscout di solito esporta numerici."""
    if s is None or (isinstance(s, float) and pd is not None and pd.isna(s)):
        return None
    if isinstance(s, (int, float)):
        return int(s)
    txt = str(s).replace("€", "").replace(",", "").replace(" ", "").strip()
    if not txt:
        return None
    mult = 1
    if txt.endswith("M") or txt.endswith("m"):
        mult = 1_000_000
        txt = txt[:-1]
    elif txt.endswith("k") or txt.endswith("K"):
        mult = 1_000
        txt = txt[:-1]
    try:
        return int(float(txt) * mult)
    except ValueError:
        return None


def _parse_passport_countries(s: Any) -> list[str]:
    """'Tunisia, Saudi Arabia' → ['Tunisia', 'Saudi Arabia']"""
    if s is None or (isinstance(s, float) and pd is not None and pd.isna(s)):
        return []
    return [c.strip() for c in str(s).split(",") if c.strip()]


def _safe_value(v: Any):
    """Converte NaN/inf in None per JSON-safety."""
    if v is None:
        return None
    if pd is not None and isinstance(v, float):
        if pd.isna(v):
            return None
    return v


def parse_wyscout_row(row: dict) -> dict:
    """Estrae i campi rilevanti da una riga Excel Wyscout."""
    out: dict = {}
    for src, dst in KEEP_FIELDS.items():
        if src in row:
            out[dst] = _safe_value(row[src])

    # post-processing
    out["height_cm"] = _parse_height(out.get("height_wyscout"))
    out.pop("height_wyscout", None)
    out["market_value_eur"] = _parse_market_value(out.get("market_value_eur"))
    out["citizenships_wyscout"] = _parse_passport_countries(out.get("passport_country"))
    out["positions_list"] = [
        p.strip() for p in re.split(r"[,/]", str(out.get("wyscout_positions") or ""))
        if p.strip()
    ]
    out["name_slug"] = _slugify_name(str(out.get("wyscout_name") or ""))
    out["team_slug"] = _slugify_name(str(out.get("wyscout_team") or ""))
    return out


def load_wyscout_files(paths: list[Path], league_hints: list[str]) -> list[dict]:
    """Carica e unifica più file Wyscout. league_hints: stessa len di paths."""
    if pd is None:
        raise RuntimeError("pandas non installato. pip install pandas openpyxl")
    rows: list[dict] = []
    for path, league in zip(paths, league_hints):
        df = pd.read_excel(path, sheet_name=0)
        for _, raw in df.iterrows():
            r = parse_wyscout_row(raw.to_dict())
            r["wyscout_source_file"] = path.name
            r["wyscout_league_hint"] = league
            rows.append(r)
    return rows


if __name__ == "__main__":
    # Standalone CLI: legge i file dagli uploads se presenti
    import sys
    paths = [Path(p) for p in sys.argv[1:]]
    if not paths:
        print("uso: python -m scraper.wyscout file1.xlsx [file2.xlsx ...]")
        sys.exit(1)
    rows = load_wyscout_files(paths, ["unknown"] * len(paths))
    print(f"Loaded {len(rows)} Wyscout rows")
