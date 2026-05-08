"""constants.py — mappature SISTEMA → SLIDE_INDEX e altre costanti."""

SYSTEM_TO_SLIDE_INDEX = {
    "3-5-2":   1,
    "3-4-3":   2,
    "3-4-2-1": 3,
    "4-4-2":   4,
    "4-3-3":   5,
    "4-2-3-1": 6,
}

COVER_SLIDE_INDEX    = 0
PRESSING_SLIDE_INDEX = 7

TITOLARI_3_5_2 = ["GK1", "RCB1", "CB1", "LCB1", "RFB1", "LFB1",
                   "RCM1", "CM1", "LCM1", "ST1", "ST1B"]

TITOLARI_3_4_3 = ["GK1", "RCB1", "CB1", "LCB1", "RFB1", "LFB1",
                   "RCM1", "LCM1", "RW1", "ST1", "LW1"]

TITOLARI_3_4_2_1 = ["GK1", "RCB1", "CB1", "LCB1", "RFB1", "LFB1",
                     "RCM1", "LCM1", "RW1", "ST1", "LW1"]

TITOLARI_4_3_3 = ["GK1", "RCB1", "LCB1", "RFB1", "LFB1",
                   "RCM1", "CM1", "LCM1", "RW1", "ST1", "LW1"]

TITOLARI_4_2_3_1 = ["GK1", "RCB1", "LCB1", "RFB1", "LFB1",
                     "CM1", "LCM1",
                     "RCM1", "RW1", "LW1",
                     "ST1"]

TITOLARI_4_4_2 = ["GK1", "RCB1", "LCB1", "RFB1", "LFB1",
                   "RCM1", "RCM2", "LCM1", "LCM2",
                   "ST1", "ST1B"]

TITOLARI_PER_SISTEMA = {
    "3-5-2":   TITOLARI_3_5_2,
    "3-4-3":   TITOLARI_3_4_3,
    "3-4-2-1": TITOLARI_3_4_2_1,
    "4-3-3":   TITOLARI_4_3_3,
    "4-2-3-1": TITOLARI_4_2_3_1,
    "4-4-2":   TITOLARI_4_4_2,
}

R2_BASE_URL = "https://pub-aa9d173290684b36a9f35e79d4d388c2.r2.dev"
R2_PHOTO_PATH_TEMPLATE = "/players_sots/{sots_id}.png"
