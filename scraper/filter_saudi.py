"""DEPRECATO — usare scraper.filter_target invece.

Manteniamo questo modulo solo come alias per retrocompatibilità con import
ancora presenti in run_static.py, add_players.py, run_update.py.
Verrà rimosso una volta migrati tutti gli import (step C.5.c).
"""
from .filter_target import (
    is_target_eligible as is_saudi_eligible,
    filter_target_profiles as filter_saudi_profiles,
)
