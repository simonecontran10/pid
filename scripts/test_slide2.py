"""test_slide2.py — Test locale del generatore slide 2.

Genera /tmp/test_slide2_juve.pptx con la slide 2 della Juventus 4-3-3.
Lancia con:
    cd ~/Desktop/pid/scripts/
    ~/Desktop/pid/venv/bin/python3 test_slide2.py

Apre il PPT con:
    open /tmp/test_slide2_juve.pptx
"""
import sys
from pathlib import Path

# Setup path: la cartella scripts/ contiene pptx_generator/
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

from pptx import Presentation
from pptx.util import Inches

from pptx_generator import style as st
from pptx_generator import slide2_lineup

# Payload Juve 4-3-3 con riserve per testare la logica
payload = {
    "team_name": "juventus",
    "system": "4-3-3",
    "match_info": {
        "coach": "Igor Tudor"
    },
    "players": {
        "GK_T":  [{"name": "Di Gregorio",  "number": "29", "height": 195, "foot": "right"}],
        "DIF_1": [{"name": "Cambiaso",     "number": "27", "height": 183, "foot": "left"},
                  {"name": "Joao Mario",   "number": "11", "height": 178, "foot": "right"}],
        "DIF_2": [{"name": "Bremer",       "number": "3",  "height": 188, "foot": "right"}],
        "DIF_3": [{"name": "Gatti",        "number": "4",  "height": 190, "foot": "right"},
                  {"name": "Rugani",       "number": "24", "height": 190, "foot": "right"}],
        "DIF_4": [{"name": "Kalulu",       "number": "15", "height": 183, "foot": "right"}],
        "CC_1":  [{"name": "Locatelli",    "number": "5",  "height": 185, "foot": "right"}],
        "CC_2":  [{"name": "Thuram",       "number": "19", "height": 192, "foot": "right"},
                  {"name": "Fagioli",      "number": "44", "height": 178, "foot": "right"},
                  {"name": "Adzic",        "number": "30", "height": 187, "foot": "right"}],
        "CC_3":  [{"name": "Koopmeiners",  "number": "8",  "height": 184, "foot": "right"}],
        "ATT_1": [{"name": "Yildiz",       "number": "10", "height": 185, "foot": "left"},
                  {"name": "Conceição",    "number": "7",  "height": 172, "foot": "right"}],
        "ATT_2": [{"name": "Vlahovic",     "number": "9",  "height": 190, "foot": "right"},
                  {"name": "David",        "number": "20", "height": 185, "foot": "right"}],
        "ATT_3": [{"name": "Mbangula",     "number": "14", "height": 178, "foot": "right"}],
    }
}

# Crea presentazione vuota 10x5.62
prs = Presentation()
prs.slide_width  = Inches(st.SLIDE_WIDTH_INCH)
prs.slide_height = Inches(st.SLIDE_HEIGHT_INCH)

stats = slide2_lineup.add_lineup_slide(prs, payload)

print("Stats:")
for k, v in stats.items():
    print(f"  {k}: {v}")

OUT = "/tmp/test_slide2_juve.pptx"
prs.save(OUT)
print(f"\n✅ Salvato: {OUT}")
print(f"   Apri con:  open {OUT}")
