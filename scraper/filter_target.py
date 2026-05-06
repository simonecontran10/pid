"""Filtra i profili giocatori secondo il country focus configurato.

PID — country-agnostic: per default ogni profilo è 'eligible' perché PID raccoglie
TUTTI i giocatori delle leghe target (Serie A include 28+ nazionalità diverse).
Il filtro per nazionalità del Saudi Players Hub originale qui non si applica.

Manteniamo l'API per:
- Compatibilità con `run_static.py`, `add_players.py`, `run_update.py` (chiamano `is_target_eligible`)
- Override esplicito via flag `_force_target` nel profilo (non usato oggi ma utile per estensioni)
- Rendere facile l'aggiunta di filtri country-based in futuro (es. PID Spagna che vuole solo
  giocatori spagnoli + naturalizzati)
"""

from .config import TARGET_NATIONALITY


def is_target_eligible(profile: dict) -> bool:
    """True se il profilo deve essere incluso nei dati PID.

    Per PID-Italia (e in generale per uno scouting hub di una lega): TRUE per default,
    perché vogliamo tutti i giocatori della lega indipendentemente dalla cittadinanza.

    Override:
    - `_force_target=True`: sempre incluso
    - `_force_target=False`: sempre escluso (anche se cittadinanza target)
    """
    forced = profile.get("_force_target")
    if forced is True:
        return True
    if forced is False:
        return False
    return True


def filter_target_profiles(profiles: list[dict]) -> list[dict]:
    """Filtra una lista di profili."""
    return [p for p in profiles if is_target_eligible(p)]


# === Compatibilità retroattiva ===
# Alias per moduli che ancora importano `is_saudi_eligible` / `filter_saudi_profiles`.
# Da rimuovere dopo aver migrato run_static.py, run_update.py, add_players.py.
is_saudi_eligible = is_target_eligible
filter_saudi_profiles = filter_target_profiles
