"""Patch cloud_sync.js per aggiungere minutes_played al record di saveObservation."""
from pathlib import Path
import sys

p = Path("frontend/cloud_sync.js")
if not p.exists():
    print(f"❌ {p} non esiste"); sys.exit(1)

t = p.read_text()
original = t

# Aggiungo minutes_played al record (dopo performance_rating)
old_record = '''  const record = {
    user_id: window.cloudAuth.user.id,
    tm_player_id: obs.tm_player_id,
    match_date: obs.match_date,
    opponent: obs.opponent,
    competition: obs.competition,
    viewing_mode: obs.viewing_mode ?? null,
    performance_rating: obs.performance_rating ?? null,
    roles_played: roles,
    evaluation_tags: Array.isArray(obs.evaluation_tags) ? obs.evaluation_tags : [],
    strengths: Array.isArray(obs.strengths) ? obs.strengths : [],
    weaknesses: Array.isArray(obs.weaknesses) ? obs.weaknesses : [],
    notes: obs.notes ?? null,
    author_username: window.cloudAuth.user.email || null,
  };'''

new_record = '''  // Validazione minutes_played (opzionale, ma se presente deve essere 0-150)
  if (obs.minutes_played != null && (typeof obs.minutes_played !== "number" || obs.minutes_played < 0 || obs.minutes_played > 150)) {
    return { data: null, error: "minutes_played non valido (range 0-150)" };
  }

  const record = {
    user_id: window.cloudAuth.user.id,
    tm_player_id: obs.tm_player_id,
    match_date: obs.match_date,
    opponent: obs.opponent,
    competition: obs.competition,
    viewing_mode: obs.viewing_mode ?? null,
    performance_rating: obs.performance_rating ?? null,
    minutes_played: obs.minutes_played ?? null,
    roles_played: roles,
    evaluation_tags: Array.isArray(obs.evaluation_tags) ? obs.evaluation_tags : [],
    strengths: Array.isArray(obs.strengths) ? obs.strengths : [],
    weaknesses: Array.isArray(obs.weaknesses) ? obs.weaknesses : [],
    notes: obs.notes ?? null,
    author_username: window.cloudAuth.user.email || null,
  };'''

if old_record in t:
    t = t.replace(old_record, new_record)
    print("✅ saveObservation: aggiunto minutes_played al record (con validazione)")
elif "minutes_played: obs.minutes_played" in t:
    print("ℹ️  Già applicata, skip")
else:
    print("❌ Pattern record saveObservation non trovato"); sys.exit(1)

if t != original:
    p.write_text(t)
    g = t.count("{") - t.count("}")
    par = t.count("(") - t.count(")")
    print(f"\nSintassi: graffe diff={g}, parentesi diff={par}, righe={t.count(chr(10))+1}")
