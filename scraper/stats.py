"""
Stats giocatore: usa l'API JSON /ceapi/performance-game/{id}?seasonId=XXXX.

L'endpoint restituisce TUTTA la carriera del giocatore (tutte le partite di tutte
le stagioni). Aggreghiamo lato Python per (seasonId, competitionId, isNationalGame)
filtrando solo participationState='played'.
"""

from collections import defaultdict
from datetime import datetime
from typing import Optional

from .config import (
    BASE_URL,
    CURRENT_SEASON,
    SEASONS,
    comp_name,
    national_team_category,
    national_team_label,
)
from .http_client import TransfermarktClient

RECENT_MATCHES_COUNT = 100  # quante partite tenere per la timeline (≈ 2 stagioni complete)


def _season_from_date(date_raw) -> Optional[int]:
    """Ricalcola la stagione (luglio→giugno) dalla data del match.

    Transfermarkt a volte etichetta i tornei con `seasonId` errato (es. U20
    World Cup ottobre 2025 → seasonId=2024 invece di 2025). Per evitare di
    propagare l'errore lato frontend, usiamo la data come fonte di verità.

    - Match disputato in luglio-dicembre (mesi 7-12) → season = anno della data
    - Match disputato in gennaio-giugno (mesi 1-6) → season = anno - 1
    """
    if date_raw is None:
        return None
    if isinstance(date_raw, dict):
        date_raw = date_raw.get("dateTimeUTC") or date_raw.get("dateTimeLocalized") or date_raw.get("timestamp")
    if date_raw is None:
        return None
    try:
        if isinstance(date_raw, (int, float)):
            ts = float(date_raw)
            dt = datetime.fromtimestamp(ts / 1000.0 if ts > 1e10 else ts)
        else:
            s = str(date_raw)
            # ISO 8601: "2025-10-05T23:00:00+00:00" o "2025-10-05" o "2025-10-05T23:00:00"
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None
    return dt.year if dt.month >= 7 else dt.year - 1


def _safe_int(v, default: int = 0) -> int:
    """Converte sicuramente in int. Gestisce None, dict, str, float, NaN."""
    if v is None or v is False:
        return default
    if v is True:
        return 1
    if isinstance(v, dict):
        # Alcuni campi Wyscout/TM tornano dict tipo {"received": True, "minute": 90}
        # Trattiamo come 1 se ha indicazioni di "ricevuto"
        for k in ("count", "value", "total"):
            if k in v:
                return _safe_int(v[k], default)
        if v.get("received") or v.get("minute") is not None or v.get("actionId"):
            return 1
        return default
    try:
        n = int(v)
        return n
    except (TypeError, ValueError):
        try:
            return int(float(v))
        except (TypeError, ValueError):
            return default


def _empty_stats() -> dict:
    return {
        "apps": 0,
        "goals": 0,
        "assists": 0,
        "yellow_cards": 0,
        "second_yellow_cards": 0,
        "red_cards": 0,
        "minutes_played": 0,
    }


def aggregate_performance(payload: dict, seasons_filter: Optional[list[int]] = None) -> dict:
    """
    Aggrega le partite per (seasonId, competitionId, isNationalGame).

    Output:
    {
        "seasons": {
            "2025": {
                "club":     { "SA1":  {"apps":22, ...}, "ACLE": {...}, ... },
                "national": { "FS":   {"apps":3,  ...} }
            },
            "2024": { ... }
        },
        "career_totals": { "apps_club":..., "apps_national":..., "goals":..., ... }
    }
    """
    matches = (payload or {}).get("data", {}).get("performance", []) or []

    # season -> 'club'/'national' -> compId -> stats
    by_bucket: dict[int, dict[str, dict[str, dict]]] = defaultdict(lambda: {"club": {}, "national": {}})

    career = _empty_stats()
    career_apps_club = 0
    career_apps_national = 0

    for m in matches:
        gi = m.get("gameInformation") or {}
        stats = m.get("statistics") or {}
        general = stats.get("generalStatistics") or {}
        if general.get("participationState") != "played":
            continue
        # Stagione: prima prova a calcolarla dalla data del match (più affidabile);
        # solo se la data manca, fallback a gi["seasonId"] di Transfermarkt.
        date_raw = gi.get("date")
        season = _season_from_date(date_raw)
        if season is None:
            season = gi.get("seasonId")
        if seasons_filter and season not in seasons_filter:
            continue
        comp = gi.get("competitionId") or "UNK"
        is_national = bool(gi.get("isNationalGame"))
        bucket = "national" if is_national else "club"

        # I campi stanno in sotto-oggetti diversi
        goal_stats = stats.get("goalStatistics") or {}
        card_stats = stats.get("cardStatistics") or {}
        time_stats = stats.get("playingTimeStatistics") or {}

        apps = 1
        # TM ha 2 campi: goalsScoredTotalOfficial (ufficiali senior) e goalsScoredTotal (totale,
        # include tutte le competizioni). Per la First Division spesso il primo è 0 mentre il
        # secondo ha il vero valore. Usiamo il massimo dei due.
        goals = max(
            _safe_int(goal_stats.get("goalsScoredTotalOfficial")),
            _safe_int(goal_stats.get("goalsScoredTotal")),
        )
        assists = max(
            _safe_int(goal_stats.get("assistsOfficial")),
            _safe_int(goal_stats.get("assists")),
        )
        yellow = _safe_int(card_stats.get("yellowCardNet"))
        sec_yellow = _safe_int(card_stats.get("secondYellowCardNet") or card_stats.get("secondYellowCard"))
        red = _safe_int(card_stats.get("redCardNet") or card_stats.get("redCard"))
        mins = _safe_int(time_stats.get("playedMinutes"))

        comp_dict = by_bucket[season][bucket].setdefault(comp, _empty_stats() | {"competition_name": comp_name(comp)})
        comp_dict["apps"] += apps
        comp_dict["goals"] += goals
        comp_dict["assists"] += assists
        comp_dict["yellow_cards"] += yellow
        comp_dict["second_yellow_cards"] += sec_yellow
        comp_dict["red_cards"] += red
        comp_dict["minutes_played"] += mins

        # Per le partite di nazionale, traccia anche la categoria della squadra (A, U23, U20, U17, Olympic).
        # Determinata dal clubId nella clubsInformation. Se il giocatore ha più categorie nello stesso
        # comp/seasonId (raro), prevale la più frequente per match conteggiati.
        if is_national:
            clubs_info = m.get("clubsInformation") or {}
            club_team_id = (clubs_info.get("club") or {}).get("clubId")
            cat = national_team_category(club_team_id, comp)
            counts = comp_dict.setdefault("_team_category_counts", {})
            counts[cat] = counts.get(cat, 0) + 1
            comp_dict["team_category"] = max(counts.items(), key=lambda x: x[1])[0]

        career["goals"] += goals
        career["assists"] += assists
        career["yellow_cards"] += yellow
        career["second_yellow_cards"] += sec_yellow
        career["red_cards"] += red
        career["minutes_played"] += mins
        if is_national:
            career_apps_national += 1
        else:
            career_apps_club += 1

    # Riformatta come dict serializzabile (chiavi int → str)
    seasons_out: dict[str, dict] = {}
    for season, buckets in sorted(by_bucket.items()):
        # rimuovi i counter temporanei usati per la categoria nazionale
        for bucket in buckets.values():
            for entry in bucket.values():
                entry.pop("_team_category_counts", None)
        seasons_out[str(season)] = buckets

    career_totals = {
        k: v for k, v in career.items() if k != "apps"
    } | {
        "apps_club": career_apps_club,
        "apps_national": career_apps_national,
        "apps_total": career_apps_club + career_apps_national,
    }

    # === ALL-TIME aggregations (no filter) ===
    # Career by competition (club + national separati)
    by_comp_club: dict[str, dict] = {}
    by_comp_nat: dict[str, dict] = {}
    by_nat_team: dict[str, dict] = {}     # category -> {team_name, caps, goals, ...}
    recent_played: list[dict] = []

    for m in matches:
        gi = m.get("gameInformation") or {}
        stats = m.get("statistics") or {}
        general = stats.get("generalStatistics") or {}
        if general.get("participationState") != "played":
            continue
        comp = gi.get("competitionId") or "UNK"
        is_national = bool(gi.get("isNationalGame"))

        goal_stats = stats.get("goalStatistics") or {}
        card_stats = stats.get("cardStatistics") or {}
        time_stats = stats.get("playingTimeStatistics") or {}
        goals = _safe_int(goal_stats.get("goalsScoredTotalOfficial"))
        assists = _safe_int(goal_stats.get("assistsOfficial"))
        yellow = _safe_int(card_stats.get("yellowCardNet"))
        sec_yellow = _safe_int(card_stats.get("secondYellowCardNet") or card_stats.get("secondYellowCard"))
        red = _safe_int(card_stats.get("redCardNet") or card_stats.get("redCard"))
        mins = _safe_int(time_stats.get("playedMinutes"))

        bucket_dict = by_comp_nat if is_national else by_comp_club
        comp_dict = bucket_dict.setdefault(comp, _empty_stats() | {"competition_name": comp_name(comp)})
        comp_dict["apps"] += 1
        comp_dict["goals"] += goals
        comp_dict["assists"] += assists
        comp_dict["yellow_cards"] += yellow
        comp_dict["second_yellow_cards"] += sec_yellow
        comp_dict["red_cards"] += red
        comp_dict["minutes_played"] += mins

        # clubs_info ci serve sia per nazionale che per recent_matches
        clubs_info = m.get("clubsInformation") or {}

        if is_national:
            club_team_id = (clubs_info.get("club") or {}).get("clubId")
            cat = national_team_category(club_team_id, comp)
            # Chiave per CATEGORY (non team_id): le varianti TM dello stesso livello
            # nazionale (es. U23 con team_id 32240 e 89250) vanno raggruppate insieme.
            nat = by_nat_team.setdefault(cat, {
                "category": cat,
                "team_id": str(club_team_id) if club_team_id else None,
                "team_name": national_team_label(cat),
                "caps": 0, "goals": 0, "assists": 0, "minutes": 0,
                "_team_id_caps": {},  # internal: traccia il team_id più frequente
            })
            nat["caps"] += 1
            nat["goals"] += goals
            nat["assists"] += assists
            nat["minutes"] += mins
            if club_team_id:
                nat["_team_id_caps"][str(club_team_id)] = nat["_team_id_caps"].get(str(club_team_id), 0) + 1

        # Recent matches (collect all played, sort+slice later)
        club_team = clubs_info.get("club") or {}
        opp_team = clubs_info.get("opponent") or {}
        # Normalizza la data: estrai dateTimeUTC se è dict
        date_raw = gi.get("date")
        if isinstance(date_raw, dict):
            date_norm = date_raw.get("dateTimeUTC") or date_raw.get("dateTimeLocalized")
        else:
            date_norm = date_raw
        # Stagione corretta basata sulla data (luglio-giugno), fallback al seasonId TM
        season_for_match = _season_from_date(date_norm)
        if season_for_match is None:
            season_for_match = gi.get("seasonId")
        recent_played.append({
            "date": date_norm,
            "season": season_for_match,
            "competition_id": comp,
            "competition_name": comp_name(comp),
            "is_national": is_national,
            "venue": club_team.get("venue"),  # "home"/"away"
            "result_for": club_team.get("goalsTotal"),
            "result_against": opp_team.get("goalsTotal"),
            "opponent_club_id": opp_team.get("clubId"),
            "goals": goals,
            "assists": assists,
            "yellow_cards": yellow,
            "red_cards": red,
            "minutes": mins,
            "is_starting": time_stats.get("isStarting", False),
            "shirt_number": general.get("shirtNumber"),
        })

    # Sort recent: data più recente prima. Le date Transfermarkt sono Unix timestamp ms o ISO?
    def _date_key(m):
        d = m.get("date")
        if not d:
            return 0
        # Transfermarkt API ritorna timestamp Unix in millisecondi (di solito)
        try:
            return int(d)
        except (TypeError, ValueError):
            try:
                return datetime.fromisoformat(str(d).replace("Z", "+00:00")).timestamp()
            except Exception:
                return 0

    recent_played.sort(key=_date_key, reverse=True)
    recent_matches = recent_played[:RECENT_MATCHES_COUNT]

    # National career as list ordered by caps desc.
    # Imposta team_id come quello con più caps tra le varianti TM, poi rimuovi il counter interno.
    for nat in by_nat_team.values():
        tid_counts = nat.pop("_team_id_caps", None)
        if tid_counts:
            nat["team_id"] = max(tid_counts.items(), key=lambda x: x[1])[0]
    national_career_list = sorted(by_nat_team.values(), key=lambda x: -x["caps"])

    return {
        "seasons": seasons_out,
        "career_totals": career_totals,
        "career_by_competition": {
            "club": by_comp_club,
            "national": by_comp_nat,
        },
        "national_career": national_career_list,
        "recent_matches": recent_matches,
    }


def scrape_player_stats(
    player_id: int,
    client: Optional[TransfermarktClient] = None,
    seasons: Optional[list[int]] = None,
) -> dict:
    """Scarica e aggrega le stats per un singolo giocatore."""
    client = client or TransfermarktClient()
    seasons = seasons or SEASONS
    referer = f"{BASE_URL}/-/profil/spieler/{player_id}"
    # seasonId=CURRENT_SEASON è sufficiente: l'API ritorna comunque tutta la carriera
    url = f"{BASE_URL}/ceapi/performance-game/{player_id}?seasonId={CURRENT_SEASON}"
    payload = client.get_json(url, referer=referer)
    agg = aggregate_performance(payload, seasons_filter=seasons)
    return {
        "tm_player_id": player_id,
        "fetched_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        **agg,
    }
