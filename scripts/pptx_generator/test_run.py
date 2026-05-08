#!/usr/bin/env python3
"""Test del generator con payload Juve 3-5-2."""
import json
import sys
from pathlib import Path

# Aggiungo parent dir per importare 'pptx_generator' come package
sys.path.insert(0, str(Path(__file__).parent.parent))

from pptx_generator import generator
from pptx_generator import constants as C

PAYLOAD = Path(__file__).parent / "payload_juve_3_5_2.json"
TEMPLATE = Path(__file__).parent / "assets" / "template_pid.pptx"
LOGHI_DIR = Path(__file__).parent / "assets" / "loghi_squadre"
PHOTOS_DIR = Path.home() / "Desktop/pid/data/photos/players_sots_lookup"
OUTPUT = Path(__file__).parent / "test_output" / "juve_3_5_2.pptx"

OUTPUT.parent.mkdir(exist_ok=True)

with open(PAYLOAD) as f:
    payload = json.load(f)

print(f"📥 Payload:  {PAYLOAD}")
print(f"📂 Template: {TEMPLATE}")
print(f"🖼️  Loghi:    {LOGHI_DIR}")
print(f"📷 Foto:     {PHOTOS_DIR}")
print(f"💾 Output:   {OUTPUT}")
print()

try:
    stats = generator.generate_pptx(payload, TEMPLATE, OUTPUT, loghi_dir=LOGHI_DIR, photos_dir=PHOTOS_DIR)
    print("✅ Generato con successo!")
    print()
    print("Stats:")
    for k, v in stats.items():
        print(f"  {k}: {v}")
except Exception as e:
    import traceback
    print(f"❌ ERRORE: {type(e).__name__}: {e}")
    traceback.print_exc()
    sys.exit(1)
