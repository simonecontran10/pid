"""
wc2026_charts.py — Genera grafici WC2026 in formato 16:9 (1920×1080)
con font Avenir Next Condensed e logo SC in basso a destra.

Carica:
  • data/wc2026_squads_fifa.json (rose + altezza + club)
  • data/wc2026_national_caps.json (media caps nazionale)
  • data/wc2026_analysis.json (top club, leghe, ecc.)
  • data/wc2026_coaches.json (allenatori + nazionalità)

Output: charts/<slug>.png (1920×1080, dpi=120)
Logo: se ~/Desktop/sc_logo.png esiste lo usa, altrimenti disegna "SC"
testuale come fallback.
"""
from __future__ import annotations
import json
import math
from pathlib import Path
from collections import Counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib import font_manager, rcParams
from matplotlib.patches import Rectangle

# -------------------- FONT --------------------
FONT_TTC = "/System/Library/Fonts/Avenir Next Condensed.ttc"
font_manager.fontManager.addfont(FONT_TTC)
rcParams["font.family"] = "Avenir Next Condensed"
rcParams["font.weight"] = "medium"
rcParams["axes.titleweight"] = "bold"
rcParams["axes.labelweight"] = "medium"

# -------------------- LOGO + ASSET PATHS --------------------
IMG_ROOT = Path("/Users/simone/Desktop/Immagini")
LOGO_PATH = IMG_ROOT / "Logo SC.png"
NATION_LOGOS_ROOT = IMG_ROOT / "Loghi nazioni"
# pt69: cartelle club EXTRA fuori da IMG_ROOT (es. Saudi Pro League).
EXTRA_CLUB_ROOTS = [
    Path("/Users/simone/Desktop/Arabia Saudita/Immagini/Loghi club"),
]

# Map nation-name (chiave usata nei JSON) → filename (senza .png)
# I file vivono in Loghi nazioni/<Continente>/<filename>.png — costruisco
# un index al volo, ma alcuni nomi richiedono alias per il match.
NATION_FILE_ALIAS = {
    "Bosnia and Herzegovina": "Bosnia-Herzegovina",
    "Bosnia And Herzegovina": "Bosnia-Herzegovina",
    "Bosnia-Erzegovina": "Bosnia-Herzegovina",
    "Cape Verde": "Cape-Verde",
    "Congo DR": "Congo-Kinshasa",
    "DR Congo": "Congo-Kinshasa",
    "Côte D'Ivoire": "Cote-dIvoire",
    "Ivory Coast": "Cote-dIvoire",
    "Curaçao": "Curacao",
    "Cabo Verde": "Cape-Verde",
    "USA": "United-States",
    "Czechia": "Czech-Republic",
    "Czech Republic": "Czech-Republic",
    "IR Iran": "Iran",
    "Korea Republic": "South-Korea",
    "South Korea": "South-Korea",
    "New Zealand": "New-Zealand",
    "Saudi Arabia": "Saudi-Arabia",
    "South Africa": "South-Africa",
    "United States": "United-States",
}


# pt69: nomi mostrati nei chart — SOLO Bosnia viene accorciata (nome troppo
# lungo che si sovrapponeva alla bandiera). Tutte le altre nazioni mantengono
# il nome originale del PDF FIFA.
NATION_DISPLAY = {
    "Bosnia And Herzegovina": "Bosnia-Erz.",
    "Bosnia and Herzegovina": "Bosnia-Erz.",
}


def display_name(n: str) -> str:
    return NATION_DISPLAY.get(n, n)


def display_nations(lst: list[str]) -> list[str]:
    return [display_name(n) for n in lst]


def nation_logo_path(nation: str) -> Path | None:
    """Cerca il file logo per la nazione, prima via alias, poi via match diretto."""
    target = NATION_FILE_ALIAS.get(nation, nation).lower()
    for cont in NATION_LOGOS_ROOT.iterdir():
        if not cont.is_dir():
            continue
        for f in cont.glob("*.png"):
            if f.stem.lower() == target:
                return f
    return None


# pt69: codice nazione 3-letter (FIFA) → nome usato in NATION_FILE_ALIAS o
# direttamente file logo. Serve per chart che hanno solo codici (es. "ENG"
# per Premier League nel chart Campionati di militanza).
CODE_TO_NATION = {
    "ALG": "Algeria", "ARG": "Argentina", "AUS": "Australia", "AUT": "Austria",
    "BEL": "Belgium", "BIH": "Bosnia and Herzegovina", "BRA": "Brazil",
    "CAN": "Canada", "CIV": "Côte D'Ivoire", "COD": "DR Congo",
    "COL": "Colombia", "CPV": "Cape Verde", "CRO": "Croatia",
    "CUW": "Curaçao", "CZE": "Czech Republic", "ECU": "Ecuador",
    "EGY": "Egypt", "ENG": "England", "ESP": "Spain", "FRA": "France",
    "GER": "Germany", "GHA": "Ghana", "HAI": "Haiti", "IRN": "Iran",
    "IRQ": "Iraq", "ITA": "Italy", "JAM": "Jamaica", "JOR": "Jordan",
    "JPN": "Japan", "KOR": "South Korea", "KSA": "Saudi Arabia",
    "MAR": "Morocco", "MEX": "Mexico", "NED": "Netherlands", "NOR": "Norway",
    "NZL": "New Zealand", "PAN": "Panama", "PAR": "Paraguay",
    "POR": "Portugal", "QAT": "Qatar", "RSA": "South Africa",
    "SCO": "Scotland", "SEN": "Senegal", "SUI": "Switzerland",
    "SWE": "Sweden", "TUN": "Tunisia", "TUR": "Turkey", "URU": "Uruguay",
    "USA": "United States", "UZB": "Uzbekistan",
    # Club countries non-WC (servono per il chart campionati)
    "ARGC": "Argentina", "CHI": "Chile", "PER": "Peru", "VEN": "Venezuela",
    "BOL": "Bolivia", "URC": "Uruguay", "HON": "Honduras", "CRC": "Costa Rica",
    "GUA": "Guatemala", "MAS": "Malaysia", "THA": "Thailand", "VIE": "Vietnam",
    "INA": "Indonesia", "CHN": "China", "HKG": "Hong Kong", "SIN": "Singapore",
    "UAE": "United Arab Emirates", "BHR": "Bahrain", "KUW": "Kuwait",
    "OMA": "Oman", "LBN": "Lebanon", "SYR": "Syria", "ISR": "Israel",
    "RUS": "Russia", "UKR": "Ukraine", "POL": "Poland", "ROU": "Romania",
    "HUN": "Hungary", "BUL": "Bulgaria", "GRE": "Greece", "SRB": "Serbia",
    "SVK": "Slovakia", "SVN": "Slovenia", "DEN": "Denmark", "FIN": "Finland",
    "ISL": "Iceland", "MLT": "Malta", "CYP": "Cyprus", "ALB": "Albania",
    "AZE": "Azerbaijan", "ARM": "Armenia", "GEO": "Georgia", "KAZ": "Kazakhstan",
    "MNE": "Montenegro", "MDA": "Moldova", "MKD": "Macedonia",
    "IRL": "Ireland", "NIR": "Northern Ireland", "WAL": "Wales",
    "ALG": "Algeria", "NGA": "Nigeria", "CMR": "Cameroon", "ANG": "Angola",
    "MLI": "Mali", "BFA": "Burkina Faso", "GAB": "Gabon", "ZAM": "Zambia",
    "ZIM": "Zimbabwe", "BEN": "Benin", "TOG": "Togo", "GUI": "Guinea",
    "MTN": "Mauritania", "LBY": "Libya", "SDN": "Sudan", "KEN": "Kenya",
    "UGA": "Uganda", "ETH": "Ethiopia", "RWA": "Rwanda", "BDI": "Burundi",
    "TAN": "Tanzania", "MOZ": "Mozambique", "MAD": "Madagascar",
    "BOT": "Botswana", "NAM": "Namibia", "LES": "Lesotho", "MWI": "Malawi",
}


def code_logo_path(code: str) -> Path | None:
    """Codice 3-letter → file logo nazione."""
    nation = CODE_TO_NATION.get(code, code)
    return nation_logo_path(nation)


# Mapping club FIFA name → filename (senza .png) sotto IMG_ROOT.
# Cercato in TUTTE le subdir EXCEPT "Loghi nazioni" (per evitare di
# matchare la nazione invece del club). File trovati durante la mappa
# iniziale sono hardcoded; il fallback fa un substring search case-insensitive.
CLUB_FILE_ALIAS = {
    "Manchester City FC": "Manchester City",
    "FC Bayern München": "Bayern Monaco",
    "Arsenal FC": "Arsenal FC logo PNG",
    "Paris Saint-Germain": "Paris Saint Germain",
    "FC Barcelona": "Barcelona logo",
    "Atlético De Madrid": "Atletico Madrid logo",
    "Manchester United FC": "Manchester United FC logo PNG",
    "Crystal Palace FC": "Crystal Palace FC logo PNG",
    "Liverpool FC": "Liverpool FC logo PNG",
    "Real Madrid C. F.": "Real Madrid logo",
    "AC Milan": "Milan",
    "Aston Villa FC": "Aston Villa FC logo PNG",
    "PSV Eindhoven": "Psv.cc",
    # pt71: club italiani — file gia' presenti in Stemmi Club e Nazioni/
    "ACF Fiorentina": "Fiorentina",
    "FC Internazionale Milano": "Inter",
    "SSC Napoli": "Napoli",
    "Atalanta Bergamo": "Atalanta",
    "Juventus FC": "Juventus",
    "Bologna FC": "Bologna",
}

# Estensioni cercate
IMG_EXT = {".png", ".PNG", ".jpg", ".jpeg", ".webp"}


def _all_club_files() -> dict[str, Path]:
    """Indicizza una volta tutti i PNG di Immagini (escluso Loghi nazioni)
    + cartelle EXTRA_CLUB_ROOTS e ritorna una mappa stem-lowercase → Path."""
    if not hasattr(_all_club_files, "_cache"):
        idx: dict[str, Path] = {}
        for p in IMG_ROOT.rglob("*.png"):
            # Escludi le bandiere nazionali (già indicizzate altrove)
            if "Loghi nazioni" in p.parts:
                continue
            idx[p.stem.lower().strip()] = p
        # Aggiungi le cartelle extra
        for root in EXTRA_CLUB_ROOTS:
            if not root.exists():
                continue
            for p in root.rglob("*.png"):
                idx[p.stem.lower().strip()] = p
        _all_club_files._cache = idx
    return _all_club_files._cache  # type: ignore[attr-defined]


def _strip_accents(s: str) -> str:
    """Rimuove diacritici: 'Fenerbahçe' → 'Fenerbahce', 'Atlético' → 'Atletico'."""
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


def club_logo_path(club: str) -> Path | None:
    """Ritorna il path del logo per il club. Prima alias diretto, poi
    fuzzy substring match sul nome (rimuovendo suffissi tipo 'FC' e
    normalizzando accenti per matchare es. Fenerbahçe ↔ Fenerbahce)."""
    idx = _all_club_files()
    alias = CLUB_FILE_ALIAS.get(club)
    if alias:
        p = idx.get(alias.lower())
        if p:
            return p
    import re
    # pt69: normalizzo accenti SIA sul nome club SIA sui filename indice,
    # così Fenerbahçe match Fenerbahce.png.
    club_norm = _strip_accents(club.lower())
    tokens = re.findall(r"[a-z]+", club_norm)
    stop = {"fc", "sc", "sk", "cf", "ac", "fk", "cr", "de", "do", "of", "the", "club"}
    tokens = [t for t in tokens if t not in stop and len(t) > 2]
    if not tokens:
        return None
    # Indice normalizzato → path
    idx_norm = {_strip_accents(stem): path for stem, path in idx.items()}
    for stem, path in idx_norm.items():
        if all(t in stem for t in tokens):
            return path
    for stem, path in idx_norm.items():
        if tokens[0] in stem:
            return path
    return None

# -------------------- COLORI --------------------
COLORS = {
    "primary":   "#0f172a",  # nero/blu scuro testi
    "accent":    "#16a34a",  # verde PitchPlan
    "muted":     "#94a3b8",
    "bg":        "#ffffff",
    "grid":      "#e2e8f0",
    "bar1":      "#1e293b",
    "bar2":      "#16a34a",
    "bar3":      "#0ea5e9",
    "bar4":      "#f59e0b",
    "bar5":      "#dc2626",
}

# Palette per nazionali (10 colori ciclici)
NATION_PALETTE = ["#16a34a", "#0ea5e9", "#f59e0b", "#dc2626", "#a855f7",
                  "#06b6d4", "#84cc16", "#ec4899", "#64748b", "#8b5cf6"]


# -------------------- HELPERS --------------------
def setup_fig(figsize=(16, 9)) -> tuple[plt.Figure, plt.Axes]:
    """Crea figura 16:9 a 3840×2160 4K UHD (dpi=240). Override figsize
    per chart con tante righe (es. 48 nazionali) dove serve più altezza."""
    fig, ax = plt.subplots(figsize=figsize, dpi=240)
    fig.patch.set_facecolor(COLORS["bg"])
    ax.set_facecolor(COLORS["bg"])
    for s in ["top", "right"]:
        ax.spines[s].set_visible(False)
    for s in ["left", "bottom"]:
        ax.spines[s].set_color(COLORS["muted"])
        ax.spines[s].set_linewidth(0.8)
    ax.grid(True, axis="x", color=COLORS["grid"], linewidth=0.7, zorder=0)
    ax.tick_params(colors=COLORS["primary"], labelsize=14)
    return fig, ax


def add_logo(fig: plt.Figure) -> None:
    """Logo SC in alto a destra (più piccolo, brand discreto)."""
    if LOGO_PATH and LOGO_PATH.exists():
        img = mpimg.imread(str(LOGO_PATH))
        # Box [left, bottom, width, height] in figure-fraction.
        # Più piccolo (3.5% width × 5% height) e in alto a destra.
        ax_logo = fig.add_axes([0.945, 0.91, 0.035, 0.06], zorder=10)
        ax_logo.imshow(img)
        ax_logo.axis("off")
    else:
        fig.text(0.97, 0.94, "SC", ha="right", va="top",
                 fontsize=28, fontweight="bold",
                 color=COLORS["muted"], family="Avenir Next Condensed")


def _safe_imread(path: Path):
    """Carica un'immagine via PIL (più tollerante di mpimg sui PNG mascherati)."""
    try:
        from PIL import Image
        import numpy as np
        with Image.open(str(path)) as im:
            return np.array(im.convert("RGBA"))
    except Exception as e:
        print(f"   ⚠️  skip {path.name}: {e}")
        return None


def add_club_logos(ax: plt.Axes, clubs: list[str], size_px: int = 28,
                   xpad_points: int = -85) -> None:
    """Disegna il logo di ogni club a sinistra del label."""
    from matplotlib.offsetbox import OffsetImage, AnnotationBbox
    yticks = ax.get_yticks()
    for y, c in zip(yticks, clubs):
        lp = club_logo_path(c)
        if not lp:
            continue
        img = _safe_imread(lp)
        if img is None:
            continue
        oi = OffsetImage(img, zoom=size_px / max(img.shape[0], img.shape[1]))
        ab = AnnotationBbox(oi, (0, y),
                            xybox=(xpad_points, 0), xycoords=("axes fraction", "data"),
                            boxcoords="offset points",
                            frameon=False, box_alignment=(0.5, 0.5))
        ax.add_artist(ab)


def add_code_logos(ax: plt.Axes, codes: list[str], size_px: int = 22,
                   xpad_points: int = -80) -> None:
    """Come add_nation_logos ma input = lista di codici 3-letter (es. ENG)."""
    from matplotlib.offsetbox import OffsetImage, AnnotationBbox
    yticks = ax.get_yticks()
    for y, code in zip(yticks, codes):
        lp = code_logo_path(code)
        if not lp:
            continue
        img = mpimg.imread(str(lp))
        oi = OffsetImage(img, zoom=size_px / max(img.shape[0], img.shape[1]))
        ab = AnnotationBbox(oi, (0, y),
                            xybox=(xpad_points, 0), xycoords=("axes fraction", "data"),
                            boxcoords="offset points",
                            frameon=False, box_alignment=(0.5, 0.5))
        ax.add_artist(ab)


def add_nation_logos(ax: plt.Axes, nations: list[str], xpos_data: float | None = None,
                     size_px: int = 60) -> None:
    """Disegna il logo di ogni nazione a sinistra del proprio tick.
    nations: lista nomi nelle stesse posizioni y delle barre (in ordine
    bottom-up di matplotlib, come ax.barh fa). xpos_data: posizione in
    coordinate dati; se None usa lo 0 dell'asse (poi sposta a sinistra)."""
    from matplotlib.offsetbox import OffsetImage, AnnotationBbox

    yticks = ax.get_yticks()
    for y, n in zip(yticks, nations):
        lp = nation_logo_path(n)
        if not lp:
            continue
        img = mpimg.imread(str(lp))
        oi = OffsetImage(img, zoom=size_px / max(img.shape[0], img.shape[1]))
        # box_alignment 0.5,0.5 → centrato sul tick; xy in coord assi
        # (xytext usa axis fraction, neg per stare A SINISTRA del label).
        ab = AnnotationBbox(oi, (0, y),
                            xybox=(-110, 0), xycoords=("axes fraction", "data"),
                            boxcoords="offset points",
                            frameon=False, box_alignment=(0.5, 0.5))
        ax.add_artist(ab)


# pt71: i18n framework — switch tramite variabile globale CHART_LANG ("it"|"en").
# T(it, en) ritorna la stringa giusta. savefig() usa cartella diversa per ogni
# lingua. main() esegue il pipeline 2 volte (charts/ e charts_en/).
CHART_LANG = "it"

def T(it_text: str, en_text: str) -> str:
    return it_text if CHART_LANG == "it" else en_text


def add_footer(fig: plt.Figure, source: str | None = None):
    if source is None:
        source = T("Fonte: FIFA", "Source: FIFA")
    fig.text(0.04, 0.04, source, ha="left", va="bottom",
             fontsize=11, color=COLORS["muted"], style="italic")


def add_title(fig: plt.Figure, title: str, subtitle: str = ""):
    fig.text(0.04, 0.94, title, ha="left", va="top",
             fontsize=32, fontweight="bold", color=COLORS["primary"])
    if subtitle:
        fig.text(0.04, 0.89, subtitle, ha="left", va="top",
                 fontsize=18, color=COLORS["muted"])


def savefig(fig: plt.Figure, name: str) -> None:
    out = Path("charts") if CHART_LANG == "it" else Path("charts_en")
    out.mkdir(exist_ok=True)
    fpath = out / f"{name}.png"
    fig.savefig(fpath, dpi=240, bbox_inches=None,
                facecolor=COLORS["bg"], edgecolor="none")
    plt.close(fig)
    print(f"  ✓ {fpath}")


# -------------------- CHARTS --------------------
def chart_national_caps_avg():
    """Bar horizontal: media caps senior per nazionale (top 25)."""
    rows = json.load(open("data/wc2026_national_caps.json"))
    rows_sorted = sorted(rows, key=lambda r: r["avg"], reverse=True)[:25]
    nations = [r["nation"] for r in rows_sorted][::-1]
    avgs = [r["avg"] for r in rows_sorted][::-1]

    fig, ax = setup_fig()
    fig.subplots_adjust(left=0.26, right=0.93, top=0.85, bottom=0.10)
    bars = ax.barh(display_nations(nations), avgs, color=COLORS["bar2"], height=0.5)
    for bar, val in zip(bars, avgs):
        ax.text(val + 0.5, bar.get_y() + bar.get_height() / 2,
                f"{val:.1f}", va="center", fontsize=12,
                color=COLORS["primary"], fontweight="bold")
    ax.set_xlabel(T("Media presenze in nazionale (senior A)",
                    "Average senior A national-team caps"), fontsize=14)
    ax.set_xlim(0, max(avgs) * 1.12)
    add_nation_logos(ax, nations, size_px=18)

    add_title(fig, T("Esperienza media in nazionale",
                     "Average national-team experience"),
              T("Media caps senior A — TOP 25 rose",
                "Average senior A caps — TOP 25 squads"))
    add_footer(fig)
    add_logo(fig)
    savefig(fig, "01_caps_avg_top25")


def chart_national_caps_avg_bottom():
    """Bar horizontal: media caps senior per nazionale (BOTTOM 25 — le rose
    meno esperte in nazionale)."""
    rows = json.load(open("data/wc2026_national_caps.json"))
    # ASC sui pct → le 25 più basse. Inverto per ax.barh bottom-up
    # (la più bassa in alto, la "meno peggio" in fondo).
    rows_sorted = sorted(rows, key=lambda r: r["avg"])[:25]
    rows_sorted = rows_sorted[::-1]
    nations = [r["nation"] for r in rows_sorted]
    avgs = [r["avg"] for r in rows_sorted]

    fig, ax = setup_fig()
    fig.subplots_adjust(left=0.26, right=0.93, top=0.85, bottom=0.10)
    bars = ax.barh(display_nations(nations), avgs, color=COLORS["bar5"], height=0.5)
    for bar, val in zip(bars, avgs):
        ax.text(val + 0.5, bar.get_y() + bar.get_height() / 2,
                f"{val:.1f}", va="center", fontsize=12,
                color=COLORS["primary"], fontweight="bold")
    ax.set_xlabel(T("Media presenze in nazionale (senior A)",
                    "Average senior A national-team caps"), fontsize=14)
    ax.set_xlim(0, max(avgs) * 1.12)
    add_nation_logos(ax, nations, size_px=18)

    add_title(fig, T("Rose meno esperte in nazionale",
                     "Least experienced squads"),
              T("Media caps senior A — le 25 PIÙ BASSE",
                "Average senior A caps — BOTTOM 25"))
    add_footer(fig)
    add_logo(fig)
    savefig(fig, "01b_caps_avg_bottom25")


def chart_top_clubs():
    """Bar horizontal: top 20 club per giocatori al Mondiale."""
    data = json.load(open("data/wc2026_analysis.json"))
    top = data["top_clubs"][:20][::-1]
    clubs = [c[0] for c in top]
    cnts = [c[1] for c in top]

    fig, ax = setup_fig()
    fig.subplots_adjust(left=0.30, right=0.93, top=0.85, bottom=0.10)
    bars = ax.barh(clubs, cnts, color=COLORS["bar1"], height=0.5)
    for bar, val in zip(bars, cnts):
        ax.text(val + 0.15, bar.get_y() + bar.get_height() / 2,
                str(val), va="center", fontsize=12,
                color=COLORS["primary"], fontweight="bold")
    ax.set_xlabel(T("Giocatori al Mondiale 2026",
                    "Players at World Cup 2026"), fontsize=14)
    ax.set_xlim(0, max(cnts) + 2)
    # pt69: loghi club spostati molto più a sinistra (col label dei club)
    # con dimensione fissa uniforme — niente più sovrapposizione.
    add_club_logos(ax, clubs, size_px=22, xpad_points=-180)

    add_title(fig, T("Club che esportano più giocatori al Mondiale",
                     "Clubs sending the most players to the World Cup"),
              T("TOP 20 club per numero di convocati WC2026",
                "TOP 20 clubs by WC2026 call-ups"))
    add_footer(fig)
    add_logo(fig)
    savefig(fig, "02_top_clubs")


def chart_top_leagues():
    """Bar horizontal: top 15 campionati di militanza."""
    data = json.load(open("data/wc2026_analysis.json"))
    top = data["top_leagues"][:15][::-1]
    leagues = [c[0] for c in top]
    cnts = [c[1] for c in top]
    total = sum(c[1] for c in data["top_leagues"])

    fig, ax = setup_fig()
    fig.subplots_adjust(left=0.12, right=0.93, top=0.85, bottom=0.10)
    bars = ax.barh(leagues, cnts, color=COLORS["bar3"], height=0.5)
    for bar, val in zip(bars, cnts):
        pct = 100 * val / total
        ax.text(val + 1, bar.get_y() + bar.get_height() / 2,
                f"{val}  ({pct:.1f}%)", va="center", fontsize=12,
                color=COLORS["primary"], fontweight="bold")
    ax.set_xlabel(T("Giocatori al Mondiale (per nazione del club)",
                    "Players at the World Cup (by club country)"), fontsize=14)
    ax.set_xlim(0, max(cnts) * 1.18)
    add_code_logos(ax, leagues, size_px=28, xpad_points=-70)

    # pt69: Big 5 box (ENG+GER+ESP+ITA+FRA) in un riquadro a destra,
    # più in basso (al centro dell'asse), con valori grandi.
    BIG5 = {"ENG", "GER", "ESP", "ITA", "FRA"}
    big5_sum = sum(c for k, c in data["top_leagues"] if k in BIG5)
    big5_pct = 100 * big5_sum / total
    # Rectangle background (in figure-fraction)
    box_l, box_b, box_w, box_h = 0.78, 0.32, 0.20, 0.32
    ax_box = fig.add_axes([box_l, box_b, box_w, box_h], zorder=8)
    ax_box.set_xlim(0, 1); ax_box.set_ylim(0, 1); ax_box.axis("off")
    from matplotlib.patches import FancyBboxPatch
    ax_box.add_patch(FancyBboxPatch(
        (0.02, 0.02), 0.96, 0.96,
        boxstyle="round,pad=0.02,rounding_size=0.06",
        facecolor="#f0f9ff", edgecolor=COLORS["bar3"], linewidth=2.5, zorder=1))
    ax_box.text(0.5, 0.94, "BIG 5",
                ha="center", va="top", fontsize=20, fontweight="bold",
                color=COLORS["bar3"], family="Avenir Next Condensed",
                transform=ax_box.transAxes)
    ax_box.text(0.5, 0.60, f"{big5_sum}",
                ha="center", va="center", fontsize=72, fontweight="bold",
                color=COLORS["bar3"], family="Avenir Next Condensed",
                transform=ax_box.transAxes)
    ax_box.text(0.5, 0.30, T(f"{big5_pct:.1f}% del totale",
                              f"{big5_pct:.1f}% of total"),
                ha="center", va="center", fontsize=20, fontweight="bold",
                color=COLORS["primary"], family="Avenir Next Condensed",
                transform=ax_box.transAxes)
    ax_box.text(0.5, 0.12, "Premier · Bundesliga · LaLiga · Serie A · Ligue 1",
                ha="center", va="center", fontsize=10, style="italic",
                color=COLORS["muted"], family="Avenir Next Condensed",
                transform=ax_box.transAxes)

    add_title(fig, T("Campionati di militanza", "Leagues of origin"),
              T("TOP 15 paesi del club da cui provengono i convocati WC2026",
                "TOP 15 club countries supplying WC2026 players"))
    add_footer(fig)
    add_logo(fig)
    savefig(fig, "03_top_leagues")


def chart_avg_age():
    """Bar horizontal: età media per rosa, sortata."""
    data = json.load(open("data/wc2026_analysis.json"))
    pn = data["per_nation"]
    rows = sorted(((n, v["avg_age"]) for n, v in pn.items() if v.get("avg_age")),
                  key=lambda x: x[1], reverse=True)
    nations = [r[0] for r in rows][::-1]
    vals = [r[1] for r in rows][::-1]

    # pt69: figsize più alto per le 48 nazionali — più aria tra le righe
    # pt71: 16:9 con 48 barre — height piccola, font piccolo, loghi piccoli.
    fig, ax = setup_fig(figsize=(16, 9))
    fig.subplots_adjust(left=0.18, right=0.96, top=0.86, bottom=0.08)
    cmap = matplotlib.colormaps.get_cmap("RdYlGn_r")
    norm_vals = [(v - min(vals)) / (max(vals) - min(vals)) for v in vals]
    colors = [cmap(n) for n in norm_vals]
    bars = ax.barh(display_nations(nations), vals, color=colors, height=0.78)
    for bar, val in zip(bars, vals):
        ax.text(val + 0.05, bar.get_y() + bar.get_height() / 2,
                f"{val:.1f}", va="center", fontsize=7.5,
                color=COLORS["primary"], fontweight="bold")
    ax.set_xlabel(T("Età media rosa", "Squad average age"), fontsize=13)
    ax.set_xlim(min(vals) - 0.5, max(vals) + 0.8)
    ax.tick_params(axis="y", labelsize=7)
    add_nation_logos(ax, nations, size_px=11)

    add_title(fig, T("Età media delle 48 rose",
                     "Average age of the 48 squads"), "")
    add_footer(fig)
    add_logo(fig)
    savefig(fig, "04_avg_age")


def chart_avg_height():
    """Bar horizontal: altezza media per rosa."""
    data = json.load(open("data/wc2026_analysis.json"))
    pn = data["per_nation"]
    rows = sorted(((n, v["avg_height"]) for n, v in pn.items() if v.get("avg_height")),
                  key=lambda x: x[1], reverse=True)
    nations = [r[0] for r in rows][::-1]
    vals = [r[1] for r in rows][::-1]

    # pt69: figsize più alto per le 48 nazionali
    fig, ax = setup_fig(figsize=(16, 9))
    fig.subplots_adjust(left=0.18, right=0.96, top=0.86, bottom=0.08)
    bars = ax.barh(display_nations(nations), vals, color=COLORS["bar4"], height=0.78)
    for bar, val in zip(bars, vals):
        ax.text(val + 0.15, bar.get_y() + bar.get_height() / 2,
                f"{val:.1f} cm", va="center", fontsize=7.5,
                color=COLORS["primary"], fontweight="bold")
    ax.set_xlabel(T("Altezza media rosa (cm)",
                    "Squad average height (cm)"), fontsize=13)
    ax.set_xlim(min(vals) - 1, max(vals) + 3)
    ax.tick_params(axis="y", labelsize=7)
    add_nation_logos(ax, nations, size_px=11)

    add_title(fig, T("Altezza media delle 48 rose",
                     "Average height of the 48 squads"), "")
    add_footer(fig)
    add_logo(fig)
    savefig(fig, "05_avg_height")


def chart_coaches_by_country():
    """Bar horizontal: numero di allenatori per nazionalità."""
    coaches = json.load(open("data/wc2026_coaches.json"))
    c = Counter(v["country"] for v in coaches.values())
    top = c.most_common(15)[::-1]
    countries = [t[0] for t in top]
    counts = [t[1] for t in top]

    fig, ax = setup_fig()
    fig.subplots_adjust(left=0.20, right=0.93, top=0.85, bottom=0.10)
    bars = ax.barh(display_nations(countries), counts, color=COLORS["bar5"], height=0.5)
    for bar, val in zip(bars, counts):
        ax.text(val + 0.05, bar.get_y() + bar.get_height() / 2,
                str(val), va="center", fontsize=13,
                color=COLORS["primary"], fontweight="bold")
    ax.set_xlabel(T("Numero di allenatori al WC2026",
                    "Number of head coaches at WC2026"), fontsize=14)
    ax.set_xlim(0, max(counts) + 1)
    add_nation_logos(ax, countries, size_px=24)

    add_title(fig, T("Allenatori per nazionalità",
                     "Head coaches by nationality"),
              T("Quali paesi esportano più CT al Mondiale 2026",
                "Which countries supply the most managers at WC2026"))
    add_footer(fig)
    add_logo(fig)
    savefig(fig, "06_coaches_by_country")


def chart_home_share():
    """Bar horizontal: % giocatori che militano nel campionato di origine."""
    data = json.load(open("data/wc2026_analysis.json"))
    hs = data["home_share"]
    rows = sorted(hs.items(), key=lambda x: x[1]["pct"], reverse=True)[:25]
    rows = rows[::-1]
    nations = [r[0] for r in rows]
    vals = [r[1]["pct"] for r in rows]

    fig, ax = setup_fig()
    fig.subplots_adjust(left=0.26, right=0.93, top=0.85, bottom=0.10)
    bars = ax.barh(display_nations(nations), vals, color=COLORS["accent"], height=0.5)
    for bar, val in zip(bars, vals):
        ax.text(val + 0.6, bar.get_y() + bar.get_height() / 2,
                f"{val:.1f}%", va="center", fontsize=11,
                color=COLORS["primary"], fontweight="bold")
    ax.set_xlabel(T("% convocati che militano nel campionato del proprio paese",
                    "% of squad playing in their own country's league"), fontsize=14)
    ax.set_xlim(0, max(vals) * 1.10)
    add_nation_logos(ax, nations, size_px=18)

    add_title(fig, T("Convocati che giocano in patria",
                     "Players playing in their home country"),
              T("% giocatori della rosa che militano nel campionato di origine — TOP 25",
                "% of squad playing in their own country's league — TOP 25"))
    add_footer(fig)
    add_logo(fig)
    savefig(fig, "07_home_share")


def chart_home_share_bottom():
    """Bar horizontal: % MENO giocatori che militano nel campionato di
    origine — bottom 25 (più 'esportatrici' di talenti)."""
    data = json.load(open("data/wc2026_analysis.json"))
    hs = data["home_share"]
    # ASC sui pct → le più basse (alcune 0%). Prendo le 25 più basse
    # in ordine crescente, poi inverto perché ax.barh disegna bottom-up.
    rows = sorted(hs.items(), key=lambda x: x[1]["pct"])[:25]
    rows = rows[::-1]  # nel chart la più bassa finisce IN ALTO
    nations = [r[0] for r in rows]
    vals = [r[1]["pct"] for r in rows]

    fig, ax = setup_fig()
    fig.subplots_adjust(left=0.26, right=0.93, top=0.85, bottom=0.10)
    bars = ax.barh(display_nations(nations), vals, color=COLORS["bar5"], height=0.5)
    # Label: se 0%, scrivo "0%" appena a destra di 0; sennò appena dopo la barra.
    xmax = max(vals + [10])
    for bar, val in zip(bars, vals):
        ax.text(max(val, 0) + xmax * 0.012, bar.get_y() + bar.get_height() / 2,
                f"{val:.1f}%", va="center", fontsize=11,
                color=COLORS["primary"], fontweight="bold")
    ax.set_xlabel(T("% convocati che militano nel campionato del proprio paese",
                    "% of squad playing in their own country's league"), fontsize=14)
    ax.set_xlim(0, xmax * 1.15)
    add_nation_logos(ax, nations, size_px=18)

    add_title(fig, T("Le rose più 'esportatrici' di talenti",
                     "The most talent-exporting squads"),
              T("% giocatori della rosa che militano nel campionato di origine — le 25 PIÙ BASSE",
                "% of squad playing in their own country's league — BOTTOM 25"))
    add_footer(fig)
    add_logo(fig)
    savefig(fig, "07b_home_share_bottom")


# pt71: nomi puliti per i club italiani — tolgo prefissi/suffissi societari
# (AC, AS, FC, SSC, US, UC, ACF, CFC, Hellas, ...) che appesantiscono i ticks.
CLUB_DISPLAY_IT = {
    "AC Milan": "Milan",
    "FC Internazionale Milano": "Inter",
    "Atalanta Bergamo": "Atalanta",
    "AS Roma": "Roma",
    "Juventus FC": "Juventus",
    "Bologna FC": "Bologna",
    "US Sassuolo": "Sassuolo",
    "SSC Napoli": "Napoli",
    "Como": "Como",
    "Venezia FC": "Venezia",
    "Torino FC": "Torino",
    "Parma": "Parma",
    "Genoa CFC": "Genoa",
    "US Cremonese": "Cremonese",
    "Hellas Verona FC": "Verona",
    "Frosinone": "Frosinone",
    "UC Sampdoria": "Sampdoria",
    "Cagliari": "Cagliari",
    "ACF Fiorentina": "Fiorentina",
    "Udinese": "Udinese",
    "Pisa SC": "Pisa",
}


def chart_top_italian_clubs():
    """pt71: bar horizontal — solo i club di Serie A che esportano giocatori
    al Mondiale 2026. Conta gli iscritti FIFA con club_country == 'ITA'."""
    fifa = json.load(open("data/wc2026_squads_fifa.json"))
    counter: dict[str, int] = {}
    for nation, v in fifa.items():
        if not isinstance(v, dict): continue
        for p in v.get("players", []):
            if p.get("club_country") == "ITA":
                c = p.get("club", "???")
                counter[c] = counter.get(c, 0) + 1
    pairs = sorted(counter.items(), key=lambda x: -x[1])
    total = sum(n for _, n in pairs)
    # bottom-up per matplotlib barh
    pairs_plot = pairs[::-1]
    clubs_raw = [c for c, _ in pairs_plot]
    clubs_display = [CLUB_DISPLAY_IT.get(c, c) for c in clubs_raw]
    cnts = [n for _, n in pairs_plot]

    # pt71: figsize 16:9 con 21 barre — riduco height e font per stare in formato.
    fig, ax = setup_fig(figsize=(16, 9))
    fig.subplots_adjust(left=0.26, right=0.93, top=0.84, bottom=0.10)
    bars = ax.barh(clubs_display, cnts, color=COLORS["bar1"], height=0.65)
    for bar, val in zip(bars, cnts):
        ax.text(val + 0.12, bar.get_y() + bar.get_height() / 2,
                str(val), va="center", fontsize=11,
                color=COLORS["primary"], fontweight="bold")
    ax.set_xlabel(T("Giocatori al Mondiale 2026",
                    "Players at World Cup 2026"), fontsize=13)
    ax.set_xlim(0, max(cnts) + 2)
    ax.tick_params(axis="y", labelsize=10)
    add_club_logos(ax, clubs_raw, size_px=18, xpad_points=-110)

    add_title(fig, T("Club italiani al Mondiale",
                     "Italian clubs at the World Cup"),
              T(f"{total} convocati da {len(pairs)} club di Serie A",
                f"{total} call-ups from {len(pairs)} Serie A clubs"))
    add_footer(fig)
    add_logo(fig)
    savefig(fig, "10_italian_clubs")


# pt71: nomi club tier-1 e tier-2 2025-26 esattamente come appaiono nel PDF
# FIFA. Tutto il resto del paese va in tier3+ (League One, Serie C, ecc.).
BIG5_TOP_DIV = {
    "ENG": {
        "tier1_name": "Premier League",
        "tier2_name": "EFL Championship",
        "tier3_name": "League One / League Two / Non-League",
        "tier1": {
            "Arsenal FC", "Aston Villa FC", "AFC Bournemouth", "Brentford FC",
            "Brighton & Hove Albion FC", "Burnley FC", "Chelsea FC",
            "Crystal Palace FC", "Everton FC", "Fulham FC", "Leeds United FC",
            "Liverpool FC", "Manchester City FC", "Manchester United FC",
            "Newcastle United FC", "Nottingham Forest FC", "Sunderland AFC",
            "Tottenham Hotspur FC", "West Ham United FC",
            "Wolverhampton Wanderers FC",
        },
        "tier2": {  # EFL Championship 2025-26 (24)
            "Birmingham City FC", "Blackburn Rovers FC", "Bristol City FC",
            "Charlton Athletic FC", "Coventry City FC", "Derby County FC",
            "Hull City FC", "Ipswich Town FC", "Leicester City FC",
            "Middlesbrough FC", "Millwall FC", "Norwich City FC",
            "Oxford United FC", "Portsmouth FC", "Preston North End FC",
            "Queens Park Rangers FC", "Sheffield United FC", "Sheffield Wednesday FC",
            "Southampton FC", "Stoke City FC", "Swansea City FC", "Watford FC",
            "West Bromwich Albion FC", "Wrexham AFC", "She eld United FC",
        },
    },
    "GER": {
        "tier1_name": "Bundesliga",
        "tier2_name": "2. Bundesliga",
        "tier3_name": "3. Liga / Regionalliga",
        "tier1": {
            "1. FSV Mainz 05", "1. FC Union Berlin", "Bayer Leverkusen",
            "FC Bayern München", "Borussia Dortmund",
            "Borussia Mönchengladbach", "Eintracht Frankfurt", "FC Augsburg",
            "SC Freiburg", "1. FC Heidenheim 1846", "TSG Hoffenheim",
            "RB Leipzig", "FC St. Pauli", "VfB Stuttgart", "VfL Wolfsburg",
            "SV Werder Bremen", "Hamburger SV", "1. FC Köln",
        },
        "tier2": {  # 2. Bundesliga 2025-26 (18)
            "FC Schalke 04", "Hannover 96", "Hertha BSC", "Holstein Kiel",
            "Karlsruher SC", "Fortuna Düsseldorf", "1. FC Nürnberg",
            "SV Darmstadt 98", "SC Paderborn 07", "SV Elversberg",
            "1. FC Magdeburg", "FC Kaiserslautern", "Eintracht Braunschweig",
            "Preußen Münster", "SpVgg Greuther Fürth", "Arminia Bielefeld",
            "Dynamo Dresden", "VfL Bochum",
        },
    },
    "ESP": {
        "tier1_name": "La Liga",
        "tier2_name": "La Liga 2 (Segunda)",
        "tier3_name": "Primera RFEF / Segunda RFEF",
        "tier1": {
            "Athletic Club", "Atlético De Madrid", "FC Barcelona",
            "RC Celta Vigo", "Elche CF", "RCD Espanyol", "Getafe CF",
            "Girona FC", "Levante UD", "RCD Mallorca", "CA Osasuna",
            "Real Betis", "Real Madrid C. F.", "Real Oviedo",
            "Real Sociedad", "Sevilla FC", "Rayo Vallecano",
            "Valencia CF", "Villarreal CF", "Deportivo Alavés",
        },
        "tier2": {  # La Liga 2 (Segunda) 2025-26 (22)
            "Almería CF", "UD Almería", "Burgos CF", "Cádiz CF",
            "CD Castellón", "Córdoba CF", "Cultural Leonesa",
            "Deportivo La Coruña", "FC Andorra", "Granada CF",
            "Albacete Balompié", "Las Palmas", "UD Las Palmas",
            "CD Leganés", "Málaga CF", "CD Mirandés", "CA Pamplonista",
            "Racing Santander", "Real Sporting", "Real Valladolid",
            "Real Zaragoza", "SD Eibar", "Sociedad Deportiva Huesca",
            "CD Tenerife",
        },
    },
    "ITA": {
        "tier1_name": "Serie A",
        "tier2_name": "Serie B",
        "tier3_name": "Serie C / Lega Pro",
        "tier1": {
            "Atalanta Bergamo", "Bologna FC", "Cagliari", "Como",
            "ACF Fiorentina", "Genoa CFC", "Hellas Verona FC",
            "FC Internazionale Milano", "Juventus FC", "US Lecce", "AC Milan",
            "SSC Napoli", "Parma", "Pisa SC", "AS Roma", "US Sassuolo",
            "Torino FC", "Udinese", "US Cremonese",
        },
        "tier2": {  # Serie B 2025-26 (20)
            "Avellino Calcio", "Bari", "SS Bari", "Brescia Calcio",
            "Carrarese Calcio", "Castrum Catania", "Catanzaro",
            "Cesena", "AC Cesena", "Empoli FC", "Frosinone",
            "Juve Stabia", "Mantova", "Modena FC", "Monza",
            "AC Monza", "Padova", "Palermo FC", "Pescara", "Reggiana",
            "AC Reggiana 1919", "AC Reggiana", "SPAL", "Salernitana",
            "US Salernitana 1919", "UC Sampdoria", "Spezia", "Spezia Calcio",
            "Sudtirol", "FC Südtirol", "Ternana Calcio", "Venezia FC",
        },
    },
    "FRA": {
        "tier1_name": "Ligue 1",
        "tier2_name": "Ligue 2",
        "tier3_name": "National 1 / National 2",
        "tier1": {
            "Angers SCO", "AJ Auxerre", "AS Monaco", "Stade Brestois 29",
            "Le Havre AC", "RC Lens", "Lille OSC", "OGC Nice",
            "Olympique Lyonnais", "Olympique Marseille", "FC Lorient",
            "FC Metz", "FC Nantes", "Paris Saint-Germain", "Paris FC",
            "Stade Rennais FC", "Stade Reims", "RC Strasbourg",
            "Toulouse FC",
        },
        "tier2": {  # Ligue 2 2025-26 (18)
            "Amiens SC", "EA Guingamp", "ESTAC Troyes", "Stade Lavallois",
            "Pau FC", "Grenoble Foot 38", "AC Ajaccio", "Clermont Foot",
            "Stade de Reims", "AS Saint-Etienne", "Montpellier HSC",
            "SC Bastia", "Le Mans FC", "USL Dunkerque", "Rodez AF",
            "Annecy FC", "Red Star FC", "Boulogne sur Mer",
        },
    },
}


def chart_big5_split():
    """pt71: stacked horizontal bar — Big 5 paesi suddivisi per top division
    vs serie inferiori. Ordine per totale decrescente."""
    fifa = json.load(open("data/wc2026_squads_fifa.json"))
    from collections import Counter
    rows = []
    for cc, cfg in BIG5_TOP_DIV.items():
        tier1 = 0
        tier2 = 0
        tier3 = 0
        for nat, v in fifa.items():
            if not isinstance(v, dict): continue
            for p in v.get("players", []):
                if p.get("club_country") == cc:
                    club = p.get("club", "")
                    if club in cfg["tier1"]:
                        tier1 += 1
                    elif club in cfg.get("tier2", set()):
                        tier2 += 1
                    else:
                        tier3 += 1
        rows.append({
            "code": cc, "country_name": {
                "ENG": "Inghilterra", "GER": "Germania", "ESP": "Spagna",
                "ITA": "Italia", "FRA": "Francia",
            }[cc],
            "tier1_name": cfg["tier1_name"], "tier2_name": cfg["tier2_name"],
            "tier3_name": cfg.get("tier3_name", "Lower"),
            "tier1": tier1, "tier2": tier2, "tier3": tier3,
            "total": tier1 + tier2 + tier3,
        })
    rows.sort(key=lambda r: -r["total"])

    # Bottom-up per matplotlib barh
    rows_plot = rows[::-1]
    labels = [r["country_name"] for r in rows_plot]

    fig, ax = setup_fig(figsize=(16, 9))
    fig.subplots_adjust(left=0.10, right=0.93, top=0.83, bottom=0.18)

    y = list(range(len(rows_plot)))
    # pt71: 3 segmenti per nazione — tier1 (top div), tier2 (2nd div), tier3 (altre)
    color_t1 = COLORS["bar3"]      # blu/viola intenso
    color_t2 = "#64748b"           # grigio medio (2nd div)
    color_t3 = "#cbd5e1"           # grigio chiaro (lower)
    tier1s = [r["tier1"] for r in rows_plot]
    tier2s = [r["tier2"] for r in rows_plot]
    tier3s = [r["tier3"] for r in rows_plot]
    ax.barh(y, tier1s, color=color_t1, height=0.62)
    ax.barh(y, tier2s, left=tier1s, color=color_t2, height=0.62)
    ax.barh(y, tier3s, left=[a+b for a,b in zip(tier1s, tier2s)],
            color=color_t3, height=0.62)

    # Per ogni nazione, etichetta DENTRO ogni segmento se grande,
    # SOTTO il bar in stile didascalia se piccolo.
    for i, r in enumerate(rows_plot):
        offset = 0
        # tier1
        if r["tier1"] >= 8:
            ax.text(r["tier1"]/2, i, f"{r['tier1']}",
                    ha="center", va="center", fontsize=14, fontweight="bold",
                    color="white")
        # tier2
        if r["tier2"] >= 8:
            ax.text(r["tier1"] + r["tier2"]/2, i, f"{r['tier2']}",
                    ha="center", va="center", fontsize=13, fontweight="bold",
                    color="white")
        elif r["tier2"] > 0:
            ax.text(r["tier1"] + r["tier2"]/2, i, f"{r['tier2']}",
                    ha="center", va="center", fontsize=10, fontweight="bold",
                    color="white")
        # tier3
        if r["tier3"] >= 8:
            ax.text(r["tier1"]+r["tier2"] + r["tier3"]/2, i, f"{r['tier3']}",
                    ha="center", va="center", fontsize=13, fontweight="bold",
                    color=COLORS["primary"])
        elif r["tier3"] > 0:
            ax.text(r["tier1"]+r["tier2"] + r["tier3"]/2, i, f"{r['tier3']}",
                    ha="center", va="center", fontsize=10, fontweight="bold",
                    color=COLORS["primary"])
        # Totale + nomi delle leghe come didascalia subito sotto il nome paese
        ax.text(r["total"] + 3, i, T(f"Totale: {r['total']}",
                                      f"Total: {r['total']}"),
                va="center", fontsize=13, fontweight="bold",
                color=COLORS["primary"])

    EN_NAT = {"Inghilterra":"England", "Germania":"Germany", "Spagna":"Spain",
              "Italia":"Italy", "Francia":"France"}
    labels_disp = [EN_NAT.get(l, l) if CHART_LANG=="en" else l for l in labels]
    ax.set_yticks(y)
    ax.set_yticklabels(labels_disp, fontsize=15, fontweight="bold")
    ax.set_xlabel(T("Giocatori al Mondiale 2026",
                    "Players at World Cup 2026"), fontsize=14)
    ax.set_xlim(0, max(r["total"] for r in rows) * 1.18)

    # Per ogni nazione, didascalia "Tier1 · Tier2 · Tier3" sotto il bar
    for i, r in enumerate(rows_plot):
        caption = f"{r['tier1_name']} · {r['tier2_name']} · {r['tier3_name']}"
        ax.text(0, i - 0.42, caption, ha="left", va="top", fontsize=8.5,
                color=COLORS["muted"], style="italic",
                family="Avenir Next Condensed")

    from matplotlib.patches import Patch
    legend_handles = [
        Patch(facecolor=color_t1, label=T("Lega principale (top division)",
                                           "Top division")),
        Patch(facecolor=color_t2, label=T("Seconda divisione",
                                           "Second division")),
        Patch(facecolor=color_t3, label=T("Serie inferiori (3a divisione e oltre)",
                                           "Lower divisions (3rd tier and below)")),
    ]
    ax.legend(handles=legend_handles, loc="lower right", fontsize=11,
              frameon=True, facecolor="white", edgecolor=COLORS["muted"])

    add_title(fig, T("Big 5 — top division vs serie inferiori",
                     "Big 5 — top tier vs lower divisions"),
              T("Giocatori WC2026 per livello del campionato, all'interno di ciascun Big 5",
                "WC2026 players by tier of league, within each Big 5 country"))
    add_footer(fig)
    add_logo(fig)
    savefig(fig, "12_big5_split")

    print("  → Riepilogo:")
    for r in rows:
        print(f"     {r['country_name']:<12s} {r['tier1_name']:<14s} {r['tier1']:>3d}"
              f"  + {r['tier2_name']:<22s} {r['tier2']:>3d}"
              f"  + altre {r['tier3']:>3d}  = {r['total']:>3d}")


def chart_italian_players_by_nation():
    """pt71: bar horizontal — in quali nazionali militano i giocatori che
    giocano in Serie A. Misura quanto la Serie A è un 'campionato
    multinazionale' al Mondiale 2026."""
    fifa = json.load(open("data/wc2026_squads_fifa.json"))
    by_nation: dict[str, int] = {}
    total = 0
    for nation, v in fifa.items():
        if not isinstance(v, dict): continue
        for p in v.get("players", []):
            if p.get("club_country") == "ITA":
                by_nation[nation] = by_nation.get(nation, 0) + 1
                total += 1
    pairs = sorted(by_nation.items(), key=lambda x: -x[1])
    pairs_plot = pairs[::-1]
    nations = [n for n, _ in pairs_plot]
    cnts = [c for _, c in pairs_plot]

    # pt71: figsize 16:9 con 29 barre — height piccolo, font piccolo.
    fig, ax = setup_fig(figsize=(16, 9))
    fig.subplots_adjust(left=0.22, right=0.93, top=0.85, bottom=0.10)
    bars = ax.barh(display_nations(nations), cnts, color=COLORS["bar2"], height=0.65)
    for bar, val in zip(bars, cnts):
        ax.text(val + 0.05, bar.get_y() + bar.get_height() / 2,
                str(val), va="center", fontsize=10,
                color=COLORS["primary"], fontweight="bold")
    ax.set_xlabel(T("Giocatori in Serie A convocati con la propria nazionale",
                    "Serie A players called up with their national team"),
                  fontsize=13)
    ax.set_xlim(0, max(cnts) + 1.5)
    ax.tick_params(axis="y", labelsize=9)
    add_nation_logos(ax, nations, size_px=18)

    add_title(fig, T("Nazionali rifornite dalla Serie A",
                     "National teams supplied by Serie A"),
              T(f"{total} convocati 'italiani' distribuiti su {len(pairs)} nazionali (esclusa l'Italia, non qualificata)",
                f"{total} 'Italian-based' players across {len(pairs)} national teams (Italy did not qualify)"))
    add_footer(fig)
    add_logo(fig)
    savefig(fig, "11_italian_players_by_nation")


# =========================================================
# pt71: chart 13/14/15/16 — focus età (giovani/vecchi/distribuzione)
# e infografica riassuntiva FIFA-style.
# =========================================================
def _build_player_records():
    """Carica i 1248 player FIFA arricchiti con foto, posizione, età
    (calcolata al kickoff WC2026 = 11 giugno 2026). Usato dai chart 13/14/15."""
    import datetime as dt
    fifa = json.load(open("data/wc2026_squads_fifa.json"))
    all_pl = json.load(open("data/players_all.json"))
    raw = json.load(open("data/wc2026_squads_raw.json"))
    PID_BASE = Path("/Users/simone/Desktop/pid")

    info_by_id = {}
    for pl in all_pl:
        tid = str(pl.get("tm_player_id") or "")
        if not tid: continue
        photo_rel = pl.get("photo_local")
        photo_path = (PID_BASE / "data" / photo_rel) if photo_rel else None
        info_by_id[tid] = {
            "photo": photo_path if (photo_path and photo_path.exists()) else None,
            "full_name": pl.get("full_name", ""),
        }
    info_by_name = {info["full_name"].lower(): info
                    for info in info_by_id.values() if info.get("full_name")}

    # mapping raw nation → fifa nation (alcuni differ)
    NATION_INV = {
        "Bosnia And Herzegovina": "Bosnia and Herzegovina",
        "Korea Republic": "South Korea", "Congo DR": "DR Congo",
        "Côte D'Ivoire": "Ivory Coast", "Czechia": "Czech Republic",
        "IR Iran": "Iran",
    }

    # Raw lookup per dob → tm_player_id (per recuperare foto se serve)
    raw_dob_by_nation = {}
    for nat, v in raw.items():
        raw_dob_by_nation[nat] = {p["dob"]: p for p in v.get("players", [])
                                  if p.get("dob")}

    today = dt.date(2026, 6, 11)
    out = []
    for nat, v in fifa.items():
        if not isinstance(v, dict): continue
        nat_raw = NATION_INV.get(nat, nat)
        for p in v.get("players", []):
            dob = p.get("date_of_birth", "")
            try:
                age = (today - dt.date.fromisoformat(dob)).days / 365.25
            except Exception:
                age = None
            # nome leggibile
            short = p.get("short_name", "")
            blob = (p.get("raw_names_blob") or "").lower()
            # Pretty name: "Cristiano Ronaldo" se ricavabile da raw_names_blob
            # altrimenti short
            pretty = short.title() if short.isupper() else short
            # match per foto: per dob nel raw → tm_id → info_by_id
            photo = None
            rp = raw_dob_by_nation.get(nat_raw, {}).get(dob)
            if rp:
                tid = str(rp.get("tm_player_id") or "")
                if tid in info_by_id:
                    photo = info_by_id[tid].get("photo")
                # nome migliore se disponibile
                if rp.get("name") and len(rp.get("name","")) > len(pretty):
                    pretty = rp["name"]
            # fallback foto da info_by_name
            if photo is None:
                for nm, info in info_by_name.items():
                    if nm and nm in blob:
                        photo = info.get("photo")
                        break
            out.append({
                "nation": nat, "name": pretty, "short": short, "dob": dob,
                "age": age, "club": p.get("club",""), "position": p.get("position",""),
                "height": p.get("height_cm", 0), "photo": photo,
            })
    return out


def _pretty_player_name(rec: dict) -> str:
    """Restituisce 'Cristiano Ronaldo' invece di 'RONALDO CRISTIANO' o
    cognome+nome FIFA. Preferisce il nome 'normalizzato' dal raw_names_blob
    (full name) o dal raw match (rec['name'])."""
    nm = rec.get("name", "")
    if not nm: return ""
    # se è tutto maiuscolo (formato FIFA "RONALDO Cristiano") lo title-case
    if nm.isupper():
        return nm.title()
    return nm


def _draw_player_card_v2(ax, rec, x, y, w, h):
    """pt71 v2: card pulita con foto cerchio CLIPPED proper, età sopra,
    nome e club a destra della foto. Layout migliore."""
    from matplotlib.patches import Circle, FancyBboxPatch
    # Sfondo card con bordo morbido
    bg = FancyBboxPatch((x, y), w, h,
                        boxstyle="round,pad=0.001,rounding_size=0.008",
                        facecolor="#f8fafc", edgecolor=COLORS["muted"],
                        linewidth=1.2, zorder=1)
    ax.add_patch(bg)

    # Foto cerchio centrato verticalmente nella metà sinistra
    photo_d = h * 0.72
    photo_cx = x + photo_d/2 + h * 0.10
    photo_cy = y + h/2
    r_photo = photo_d/2

    img = _safe_imread(rec["photo"]) if rec.get("photo") else None
    if img is not None:
        # Clip rotondo via Circle + set_clip_path
        clip_circ = Circle((photo_cx, photo_cy), r_photo, transform=ax.transData)
        # extent: rettangolo che contiene il cerchio
        artist = ax.imshow(img, extent=[photo_cx-r_photo, photo_cx+r_photo,
                                         photo_cy-r_photo, photo_cy+r_photo],
                           aspect="auto", zorder=2)
        artist.set_clip_path(clip_circ)
        # Bordo cerchio sopra
        ax.add_patch(Circle((photo_cx, photo_cy), r_photo,
                            facecolor="none", edgecolor=COLORS["primary"],
                            linewidth=2.0, zorder=3))
    else:
        # Placeholder grigio rotondo
        ax.add_patch(Circle((photo_cx, photo_cy), r_photo,
                            facecolor="#cbd5e1", edgecolor=COLORS["muted"],
                            linewidth=1.5, zorder=2))
        ax.text(photo_cx, photo_cy, "?", ha="center", va="center",
                fontsize=18, color=COLORS["muted"], fontweight="bold",
                zorder=3)

    # Zona testo a destra della foto
    text_x = photo_cx + r_photo + h * 0.12

    # Età (grande, sopra)
    age_v = rec.get("age")
    age_txt = f"{age_v:.1f}" if age_v is not None else "—"
    ax.text(x + w - h*0.10, y + h*0.74, age_txt,
            ha="right", va="center", fontsize=22, fontweight="bold",
            color=COLORS["bar3"], family="Avenir Next Condensed", zorder=4)
    ax.text(x + w - h*0.10, y + h*0.50, T("anni", "yrs"),
            ha="right", va="center", fontsize=9,
            color=COLORS["muted"], family="Avenir Next Condensed", zorder=4)

    # Nome pulito
    nm = _pretty_player_name(rec)[:24]
    ax.text(text_x, y + h*0.65, nm,
            ha="left", va="center", fontsize=11.5, fontweight="bold",
            color=COLORS["primary"], family="Avenir Next Condensed", zorder=4)
    # Club
    club = rec.get("club","")[:26]
    ax.text(text_x, y + h*0.42, club,
            ha="left", va="center", fontsize=9.5,
            color=COLORS["primary"], family="Avenir Next Condensed", zorder=4)
    # Nazione (più chiara, più piccola)
    nat = rec.get("nation","")
    ax.text(text_x, y + h*0.22, nat,
            ha="left", va="center", fontsize=9, style="italic",
            color=COLORS["muted"], family="Avenir Next Condensed", zorder=4)


def _chart_age_extremes(top20: list, title: str, subtitle: str, slug: str):
    """Layout 16:9 con 20 player in griglia 5×4 (card 16:9 ratio interna)."""
    fig, ax = setup_fig(figsize=(16, 9))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    fig.subplots_adjust(left=0.025, right=0.975, top=0.85, bottom=0.06)

    cols, rows = 5, 4
    _L, _R, _T2, _B = 0.02, 0.98, 0.81, 0.07
    pad_x = 0.012
    pad_y = 0.018
    card_w = (_R - _L - (cols-1) * pad_x) / cols
    card_h = (_T2 - _B - (rows-1) * pad_y) / rows
    for i, r in enumerate(top20):
        col = i % cols
        row = i // cols
        x = _L + col * (card_w + pad_x)
        y = _T2 - card_h - row * (card_h + pad_y)
        _draw_player_card_v2(ax, r, x, y, card_w, card_h)

    add_title(fig, title, subtitle)
    add_footer(fig)
    add_logo(fig)
    savefig(fig, slug)


def chart_youngest_20():
    recs = _build_player_records()
    recs = [r for r in recs if r.get("age") is not None]
    recs.sort(key=lambda r: r["age"])
    _chart_age_extremes(
        recs[:20],
        T("I 20 giocatori più giovani al Mondiale 2026",
          "The 20 youngest players at World Cup 2026"),
        T("Età calcolata al 11 giugno 2026 (giorno d'apertura)",
          "Age computed at June 11, 2026 (opening day)"),
        "13_youngest_20",
    )


def chart_oldest_20():
    recs = _build_player_records()
    recs = [r for r in recs if r.get("age") is not None]
    recs.sort(key=lambda r: -r["age"])
    _chart_age_extremes(
        recs[:20],
        T("I 20 giocatori più vecchi al Mondiale 2026",
          "The 20 oldest players at World Cup 2026"),
        T("Età calcolata al 11 giugno 2026 (giorno d'apertura)",
          "Age computed at June 11, 2026 (opening day)"),
        "14_oldest_20",
    )


def chart_age_distribution():
    """pt71: distribuzione per anni di età — istogramma con count + %."""
    recs = _build_player_records()
    ages = [int(r["age"]) for r in recs if r.get("age") is not None]
    from collections import Counter
    counts = Counter(ages)
    total = sum(counts.values())
    ks = sorted(counts.keys())
    cs = [counts[k] for k in ks]

    fig, ax = setup_fig(figsize=(16, 9))
    fig.subplots_adjust(left=0.07, right=0.96, top=0.85, bottom=0.13)
    bars = ax.bar(ks, cs, color=COLORS["bar3"], edgecolor="white", linewidth=0.5)
    for bar, n, k in zip(bars, cs, ks):
        pct = 100 * n / total
        ax.text(bar.get_x() + bar.get_width()/2, n + max(cs)*0.018,
                f"{n}", ha="center", va="bottom", fontsize=11,
                color=COLORS["primary"], fontweight="bold")
        ax.text(bar.get_x() + bar.get_width()/2, n + max(cs)*0.06,
                f"{pct:.1f}%", ha="center", va="bottom", fontsize=9,
                color=COLORS["muted"])
    ax.set_xlabel(T("Età (anni)", "Age (years)"), fontsize=14)
    ax.set_ylabel(T("Giocatori", "Players"), fontsize=14)
    ax.set_xticks(ks)
    ax.set_xticklabels([str(k) for k in ks], fontsize=11)
    ax.set_ylim(0, max(cs) * 1.18)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Indicatori statistici (media, mediana)
    import statistics as st
    raw_ages = [r["age"] for r in recs if r.get("age") is not None]
    avg = sum(raw_ages) / len(raw_ages)
    med = st.median(raw_ages)
    ax.axvline(avg, color=COLORS["bar1"], linestyle="--", linewidth=1.5,
               alpha=0.7, zorder=1)
    ax.text(avg + 0.15, max(cs) * 1.10,
            T(f"Media: {avg:.1f} anni", f"Average: {avg:.1f} years"),
            fontsize=12, color=COLORS["bar1"], fontweight="bold")

    add_title(fig, T("Distribuzione per età dei convocati",
                     "Age distribution of the call-ups"),
              T(f"{total} giocatori, range {min(ks)}–{max(ks)} anni · media {avg:.1f} · mediana {int(med)}",
                f"{total} players, range {min(ks)}–{max(ks)} years · avg {avg:.1f} · median {int(med)}"))
    add_footer(fig)
    add_logo(fig)
    savefig(fig, "15_age_distribution")


def chart_fifa_summary_infographic():
    """pt71: infografica FIFA-style con tutti i numeri chiave del Mondiale."""
    import datetime as dt
    from collections import Counter
    fifa = json.load(open("data/wc2026_squads_fifa.json"))

    # KPI base
    all_p = [(n, p) for n, v in fifa.items() for p in v.get("players", []) if isinstance(v, dict)]
    n_players = len(all_p)
    n_nations = len([n for n, v in fifa.items() if isinstance(v, dict)])
    clubs_set = {p.get("club") for _, p in all_p}
    n_clubs = len(clubs_set)
    leagues_set = {p.get("club_country") for _, p in all_p}
    n_leagues = len(leagues_set)

    today = dt.date(2026, 6, 11)
    def age(dob):
        try: return (today - dt.date.fromisoformat(dob)).days / 365.25
        except: return None
    ages = [age(p.get("date_of_birth","")) for _, p in all_p]
    ages = [a for a in ages if a is not None]
    avg_age = sum(ages)/len(ages)
    youngest = min((p for _, p in all_p), key=lambda p: -age(p.get("date_of_birth","")) if age(p.get("date_of_birth","")) else 0)
    # corretto
    valid = [(n,p) for n,p in all_p if age(p.get("date_of_birth",""))]
    youngest_np = max(valid, key=lambda np: np[1]["date_of_birth"])
    oldest_np = min(valid, key=lambda np: np[1]["date_of_birth"])

    heights = [p.get("height_cm",0) for _,p in all_p if p.get("height_cm")]
    avg_h = sum(heights)/len(heights)
    tallest_np = max(valid, key=lambda np: np[1].get("height_cm",0))
    shortest_np = min((np for np in valid if np[1].get("height_cm")), key=lambda np: np[1]["height_cm"])

    pos_count = Counter(p.get("position","?") for _,p in all_p)

    # Big 5 share
    BIG5 = {"ENG","ESP","GER","ITA","FRA"}
    big5 = sum(1 for _,p in all_p if p.get("club_country") in BIG5)
    big5_pct = 100*big5/n_players

    # Pretty name helper
    def pretty(p): return p.get("short_name","").title() if p.get("short_name","").isupper() else p.get("short_name","")

    fig = plt.figure(figsize=(16, 9), dpi=240, facecolor="white")
    fig.text(0.04, 0.94, T("WC 2026 in numeri", "WC 2026 by the numbers"),
             ha="left", va="top",
             fontsize=36, fontweight="bold", color=COLORS["primary"],
             family="Avenir Next Condensed")
    fig.text(0.04, 0.88, T("I dati ufficiali delle 48 rose iscritte alla Coppa del Mondo 2026",
                            "Official data from the 48 squads at the 2026 World Cup"),
             ha="left", va="top", fontsize=16, color=COLORS["muted"],
             family="Avenir Next Condensed")

    KPIs = [
        (n_players, T("GIOCATORI","PLAYERS"), T("convocati ufficiali","official call-ups")),
        (n_nations, T("NAZIONALI","NATIONAL TEAMS"), T("48 squadre × 26 giocatori","48 squads × 26 players")),
        (n_clubs, "CLUB", T("rappresentati al Mondiale","represented at the World Cup")),
        (n_leagues, T("PAESI","COUNTRIES"), T("del club di militanza","of the club of registration")),
        (f"{avg_age:.1f}", T("ETÀ MEDIA","AVG AGE"), T("anni al kickoff (11/6/26)","years at kickoff (Jun 11, 2026)")),
        (f"{avg_h:.0f}", T("ALTEZZA MEDIA","AVG HEIGHT"), T("centimetri","centimeters")),
        (f"{big5}", "BIG 5", T(f"{big5_pct:.1f}% in Premier/Bundesliga/LaLiga/SerieA/Ligue1",
                                f"{big5_pct:.1f}% in Premier/Bundesliga/LaLiga/Serie A/Ligue 1")),
        (f"{pos_count.get('GK',0)}", T("PORTIERI","GOALKEEPERS"),
            f"{pos_count.get('GK',0)*100/n_players:.1f}%"),
        (f"{int(age(youngest_np[1]['date_of_birth']))}",
            T("PIÙ GIOVANE","YOUNGEST"),
            f"{pretty(youngest_np[1])} ({youngest_np[0]})"),
        (f"{int(age(oldest_np[1]['date_of_birth']))}",
            T("PIÙ VECCHIO","OLDEST"),
            f"{pretty(oldest_np[1])} ({oldest_np[0]})"),
        (f"{tallest_np[1].get('height_cm')} cm",
            T("PIÙ ALTO","TALLEST"),
            f"{pretty(tallest_np[1])} ({tallest_np[0]})"),
        (f"{shortest_np[1].get('height_cm')} cm",
            T("PIÙ BASSO","SHORTEST"),
            f"{pretty(shortest_np[1])} ({shortest_np[0]})"),
    ]
    cols, rows_ = 4, 3
    _L, _R, _T, _B = 0.04, 0.96, 0.78, 0.07
    pad = 0.018
    tile_w = (_R-_L - (cols-1)*pad) / cols
    tile_h = (_T-_B - (rows_-1)*pad) / rows_
    for i, (big, label, sub) in enumerate(KPIs):
        col = i % cols
        row = i // cols
        x = _L + col * (tile_w + pad)
        y = _T - tile_h - row * (tile_h + pad)
        ax = fig.add_axes([x, y, tile_w, tile_h])
        ax.set_xlim(0,1); ax.set_ylim(0,1); ax.axis("off")
        from matplotlib.patches import FancyBboxPatch
        ax.add_patch(FancyBboxPatch((0.01,0.02), 0.98, 0.96,
                                     boxstyle="round,pad=0.01,rounding_size=0.04",
                                     facecolor="#f8fafc",
                                     edgecolor=COLORS["bar3"], linewidth=1.5))
        # Big number
        ax.text(0.5, 0.65, str(big),
                ha="center", va="center", fontsize=42, fontweight="bold",
                color=COLORS["bar3"], family="Avenir Next Condensed")
        # Label
        ax.text(0.5, 0.28, label,
                ha="center", va="center", fontsize=15, fontweight="bold",
                color=COLORS["primary"], family="Avenir Next Condensed")
        # Subtitle
        ax.text(0.5, 0.13, sub,
                ha="center", va="center", fontsize=9.5,
                color=COLORS["muted"], family="Avenir Next Condensed")

    add_footer(fig)
    add_logo(fig)
    savefig(fig, "16_summary_infographic")


def chart_records():
    """Grafico 16:9 con 6 card statistiche: più vecchio/giovane,
    più alto/basso, top caps, esordienti (0 caps)."""
    import datetime as dt
    fifa = json.load(open("data/wc2026_squads_fifa.json"))
    stats_list = json.load(open("data/players_stats.json"))
    stats_by_id = {str(s["tm_player_id"]): s for s in stats_list}
    raw = json.load(open("data/wc2026_squads_raw.json"))
    # pt69: lookup foto + ruolo dal players_all PID
    all_pl = json.load(open("data/players_all.json"))
    PID_BASE = Path("/Users/simone/Desktop/pid")
    info_by_id = {}
    for pl in all_pl:
        tid = str(pl.get("tm_player_id") or "")
        if not tid:
            continue
        photo_rel = pl.get("photo_local")
        photo_path = (PID_BASE / "data" / photo_rel) if photo_rel else None
        info_by_id[tid] = {
            "photo": photo_path if (photo_path and photo_path.exists()) else None,
            "position": pl.get("position_specific") or pl.get("position_general") or "",
            "full_name": pl.get("full_name", ""),
        }
    # Lookup per nome (FIFA non ha tm_id direttamente)
    info_by_name_lower: dict[str, dict] = {}
    for tid, info in info_by_id.items():
        nm = (info.get("full_name") or "").lower()
        if nm:
            info_by_name_lower[nm] = info
    def fifa_info(p: dict, fallback_pos: str = "") -> dict:
        # FIFA player has raw_names_blob; cerco match parziale per cognome
        blob = (p.get("raw_names_blob") or "").lower()
        for nm, info in info_by_name_lower.items():
            if nm and (nm in blob or all(t in blob for t in nm.split()[:2])):
                return info
        return {"photo": None, "position": fallback_pos, "full_name": ""}

    today = dt.date(2026, 6, 11)
    def age_of(dob):
        try:
            return (today - dt.date.fromisoformat(dob)).days / 365.25
        except Exception:
            return None

    all_pl = [(n, p) for n, v in fifa.items() for p in v["players"]]
    tallest = max(all_pl, key=lambda np: np[1].get("height_cm", 0))
    shortest = min((np for np in all_pl if np[1].get("height_cm")),
                   key=lambda np: np[1]["height_cm"])
    oldest = min(all_pl, key=lambda np: np[1].get("date_of_birth", "9999"))
    youngest = max(all_pl, key=lambda np: np[1].get("date_of_birth", "0000"))

    # pt69: override dati nazionali per giocatori con scrape TM incompleto
    # (CR Ronaldo: TM raw ha 239 caps / 45 goal, ma la pagina TM mostra
    # 226 caps / 143 goal nel "National team career" — il scraper sta
    # leggendo solo la riga di una competizione filtrata).
    RECORD_OVERRIDES = {
        "8198": {"caps": 226, "goals": 143, "club": "Al-Nassr FC"},  # CR Ronaldo
    }

    # Top caps + top goal + (least caps) — include tm_id per recupero foto
    top_caps = ("", "", 0, "", "")    # (nation, name, caps, club, tm_id)
    top_goals = ("", "", 0, "", "")
    least_caps = ("", "", 9999, "", "")
    n_debutters = 0
    for nation, v in raw.items():
        if not isinstance(v, dict):
            continue
        for p in v.get("players", []):
            tid = str(p.get("tm_player_id") or "")
            s = stats_by_id.get(tid)
            if not s:
                continue
            override = RECORD_OVERRIDES.get(tid)
            for ent in s.get("national_career", []) or []:
                if ent.get("category") != "A":
                    continue
                caps = override["caps"] if override else int(ent.get("caps", 0) or 0)
                goals = override["goals"] if override else int(ent.get("goals", 0) or 0)
                club = override["club"] if override else p.get("club", "—")
                if caps > top_caps[2]:
                    top_caps = (nation, p.get("name", "?"), caps, club, tid)
                if goals > top_goals[2]:
                    top_goals = (nation, p.get("name", "?"), goals, club, tid)
                if caps == 0:
                    n_debutters += 1
                # least caps tra chi ha >=1 cap (no esordienti)
                if 1 <= caps < least_caps[2]:
                    least_caps = (nation, p.get("name", "?"), caps, club, tid)
                break

    fig = plt.figure(figsize=(16, 9), dpi=240, facecolor=COLORS["bg"])
    add_title(fig, T("Record del Mondiale 2026", "World Cup 2026 records"),
              T("I numeri estremi delle 48 rose ufficiali FIFA",
                "Extreme stats from the 48 official FIFA squads"))
    add_footer(fig)
    add_logo(fig)

    # 6 card in grid 2×3, area utile [0.05, 0.10, 0.90, 0.72]
    # pt69: ruolo + foto per ogni card. La foto viene presa SEMPRE via
    # tm_player_id (info_by_id) per evitare match falsi via raw_names_blob.
    POS_LBL = {
        "GK": T("Portiere", "Goalkeeper"),
        "DF": T("Difensore", "Defender"),
        "MF": T("Centrocampista", "Midfielder"),
        "FW": T("Attaccante", "Forward"),
    }

    # Mapping tm_id → player FIFA (per recuperare ruolo + raw_names_blob)
    fifa_by_tm: dict[str, dict] = {}
    for nation_name, v in raw.items():
        if not isinstance(v, dict):
            continue
        for wp in v.get("players", []):
            tid = str(wp.get("tm_player_id") or "")
            if not tid:
                continue
            # Match con FIFA player per stesso nome
            wname = (wp.get("name") or "").lower()
            for fp in fifa.get(nation_name, {}).get("players", []):
                blob = (fp.get("raw_names_blob") or "").lower()
                if wname and (wname in blob or any(t in blob for t in wname.split())):
                    fifa_by_tm[tid] = fp
                    break

    def card_for(label, value, player, nation, color):
        pos_short = (player.get("position") or "").upper()
        pos_full = POS_LBL.get(pos_short, pos_short)
        info = fifa_info(player, pos_full)
        # Nome leggibile: "Cognome Nome" estratto dal raw_names_blob
        parts = (player.get("raw_names_blob") or "").split()
        if len(parts) >= 2:
            # primi 2 token sono "COGNOME Nome" → metto "Nome Cognome"
            nice_name = f"{parts[1].title()} {parts[0].title()}"
        else:
            nice_name = player.get("name_on_shirt", "?")
        return {
            "label": label, "value": value, "name": nice_name,
            "subtitle": f"{nation} · {pos_full}" if pos_full else nation,
            "color": color, "nation": nation,
            "photo": info.get("photo"),
        }

    def caps_card(label, info_tuple, color):
        nation, _, val, club, tm_id = info_tuple
        # Foto e info dal PID via tm_id (sicuro, no name match)
        pid_info = info_by_id.get(tm_id, {})
        nice_name = pid_info.get("full_name") or "?"
        # Ruolo: prima da FIFA player matchato, altrimenti da PID
        fp = fifa_by_tm.get(tm_id, {})
        pos_short = (fp.get("position") or "").upper()
        pos_full = POS_LBL.get(pos_short, pos_short) or pid_info.get("position", "")
        return {
            "label": label, "value": f"{val}", "name": nice_name,
            "subtitle": f"{nation} · {club} · {pos_full}" if pos_full else f"{nation} · {club}",
            "color": color, "nation": nation,
            "photo": pid_info.get("photo"),
        }

    cards = [
        card_for(T("PIÙ VECCHIO","OLDEST"),
                 T(f"{age_of(oldest[1]['date_of_birth']):.1f} anni",
                   f"{age_of(oldest[1]['date_of_birth']):.1f} yrs"),
                 oldest[1], oldest[0], COLORS["bar5"]),
        card_for(T("PIÙ GIOVANE","YOUNGEST"),
                 T(f"{age_of(youngest[1]['date_of_birth']):.1f} anni",
                   f"{age_of(youngest[1]['date_of_birth']):.1f} yrs"),
                 youngest[1], youngest[0], COLORS["bar2"]),
        card_for(T("PIÙ ALTO","TALLEST"), f"{tallest[1].get('height_cm','?')} cm",
                 tallest[1], tallest[0], COLORS["bar4"]),
        card_for(T("PIÙ BASSO","SHORTEST"), f"{shortest[1].get('height_cm','?')} cm",
                 shortest[1], shortest[0], COLORS["bar3"]),
        caps_card(T("MASSIMO CAPS","MOST CAPS"), top_caps, COLORS["bar1"]),
        caps_card(T("MASSIMO GOAL NAZIONALE","TOP INT'L SCORER"),
                  top_goals, COLORS["accent"]),
    ]
    # Sostituisco la riga "Esordienti" col card di MENO PRESENZE (più utile)
    if least_caps[2] < 9999:
        cards.append(caps_card(T("MENO PRESENZE","FEWEST CAPS"),
                                least_caps, COLORS["bar3"]))

    # Grid 2 righe × 4 colonne (8 slot, 7 card + 1 vuoto)
    cols, rows = 4, 2
    pad_x, pad_y = 0.025, 0.03
    grid_left, grid_bottom = 0.03, 0.08
    grid_w, grid_h = 0.94, 0.74
    cell_w = (grid_w - pad_x * (cols - 1)) / cols
    cell_h = (grid_h - pad_y * (rows - 1)) / rows

    for i, c in enumerate(cards):
        row = i // cols
        col = i % cols
        x = grid_left + col * (cell_w + pad_x)
        y = grid_bottom + (rows - 1 - row) * (cell_h + pad_y)
        ax = fig.add_axes([x, y, cell_w, cell_h])
        ax.set_xlim(0, 1); ax.set_ylim(0, 1)
        ax.axis("off")
        # Sfondo card
        ax.add_patch(Rectangle((0, 0), 1, 1, facecolor="#f8fafc",
                               edgecolor=COLORS["grid"], linewidth=1, zorder=1))
        # Label top
        ax.text(0.04, 0.88, c["label"], fontsize=14, fontweight="bold",
                color=COLORS["muted"], family="Avenir Next Condensed",
                transform=ax.transAxes)
        # Logo nazione in alto a destra
        lp = nation_logo_path(c["nation"])
        if lp and lp.exists():
            from matplotlib.offsetbox import OffsetImage, AnnotationBbox
            img = _safe_imread(lp)
            if img is not None:
                oi = OffsetImage(img, zoom=44 / max(img.shape[0], img.shape[1]))
                ab = AnnotationBbox(oi, (0.93, 0.85), xycoords=ax.transAxes,
                                    frameon=False, box_alignment=(0.5, 0.5))
                ax.add_artist(ab)
        # pt69: foto giocatore a destra (più grande del logo nazione)
        photo = c.get("photo")
        if photo:
            from matplotlib.offsetbox import OffsetImage, AnnotationBbox
            pimg = _safe_imread(photo)
            if pimg is not None:
                zoom = 110 / max(pimg.shape[0], pimg.shape[1])
                oi = OffsetImage(pimg, zoom=zoom)
                ab = AnnotationBbox(oi, (0.86, 0.45), xycoords=ax.transAxes,
                                    frameon=False, box_alignment=(0.5, 0.5))
                ax.add_artist(ab)
        # Valore grande
        ax.text(0.04, 0.55, c["value"], fontsize=44, fontweight="bold",
                color=c["color"], family="Avenir Next Condensed",
                transform=ax.transAxes, va="center")
        # Nome giocatore
        ax.text(0.04, 0.28, c["name"], fontsize=18, fontweight="bold",
                color=COLORS["primary"], family="Avenir Next Condensed",
                transform=ax.transAxes)
        # Subtitle (nazione · club · ruolo)
        ax.text(0.04, 0.14, c["subtitle"], fontsize=11,
                color=COLORS["muted"], family="Avenir Next Condensed",
                transform=ax.transAxes, style="italic")

    # In basso al centro: conteggio esordienti totali (piccolo footer info)
    fig.text(0.5, 0.05, f"Esordienti al Mondiale (0 caps senior): {n_debutters} giocatori",
             ha="center", va="bottom", fontsize=12, fontweight="bold",
             color=COLORS["muted"], family="Avenir Next Condensed")

    savefig(fig, "09_records")


def chart_scatter_age_caps():
    """Scatter: età media (X) vs media presenze nazionale (Y) — un punto
    per nazionale, con logo nazione come marker."""
    from matplotlib.offsetbox import OffsetImage, AnnotationBbox

    age_data = json.load(open("data/wc2026_analysis.json"))["per_nation"]
    caps_data = {r["nation"]: r["avg"] for r in json.load(open("data/wc2026_national_caps.json"))}

    points = []
    for nation, v in age_data.items():
        avg_age = v.get("avg_age")
        caps = caps_data.get(nation)
        if avg_age is None or caps is None:
            continue
        points.append((nation, avg_age, caps))

    fig, ax = setup_fig()
    fig.subplots_adjust(left=0.08, right=0.95, top=0.85, bottom=0.10)

    xs = [p[1] for p in points]
    ys = [p[2] for p in points]

    # Limiti calcolati prima per posizionare le scritte negli angoli REALI
    x_min, x_max = min(xs) - 0.5, max(xs) + 0.5
    y_min, y_max = min(ys) - 5, max(ys) + 5

    # pt69: bande colorate per età sull'asse X
    #   X < 27   → verde (rosa giovane)
    #   27–29    → giallo (intermedia)
    #   X > 29   → rosso (rosa anziana)
    ax.axvspan(x_min, 27, color="#bbf7d0", alpha=0.35, zorder=0)
    ax.axvspan(27, 29, color="#fef9c3", alpha=0.45, zorder=0)
    ax.axvspan(29, x_max, color="#fecaca", alpha=0.40, zorder=0)

    # Linee medie X e Y
    x_mean = sum(xs) / len(xs)
    y_mean = sum(ys) / len(ys)
    ax.axhline(y_mean, color=COLORS["muted"], linestyle="--", linewidth=0.8, zorder=1)

    # Etichette quadranti POSIZIONATE AGLI ANGOLI REALI del chart
    pad = 0.012
    ax.text(pad, 1 - pad, "Giovani · esperte",
            color=COLORS["primary"], fontsize=12, fontweight="bold",
            ha="left", va="top", style="italic", transform=ax.transAxes,
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.7, pad=3))
    ax.text(1 - pad, 1 - pad, "Anziane · esperte",
            color=COLORS["primary"], fontsize=12, fontweight="bold",
            ha="right", va="top", style="italic", transform=ax.transAxes,
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.7, pad=3))
    ax.text(pad, pad, "Giovani · poco esperte",
            color=COLORS["primary"], fontsize=12, fontweight="bold",
            ha="left", va="bottom", style="italic", transform=ax.transAxes,
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.7, pad=3))
    ax.text(1 - pad, pad, "Anziane · poco esperte",
            color=COLORS["primary"], fontsize=12, fontweight="bold",
            ha="right", va="bottom", style="italic", transform=ax.transAxes,
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.7, pad=3))

    # Punti = loghi delle nazioni
    for nation, age, caps in points:
        lp = nation_logo_path(nation)
        if lp and lp.exists():
            img = mpimg.imread(str(lp))
            zoom = 32 / max(img.shape[0], img.shape[1])
            ab = AnnotationBbox(OffsetImage(img, zoom=zoom),
                                (age, caps), frameon=False, pad=0,
                                box_alignment=(0.5, 0.5), zorder=5)
            ax.add_artist(ab)
        else:
            ax.scatter([age], [caps], s=80, color=COLORS["bar2"], zorder=5)

    ax.set_xlabel(T("Età media rosa", "Squad average age"), fontsize=14)
    ax.set_ylabel(T("Media presenze in nazionale (senior A)",
                    "Average senior A caps"), fontsize=14)
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    ax.grid(True, color=COLORS["grid"], linewidth=0.6, zorder=0)

    add_title(fig, T("Età media × Presenze in nazionale",
                     "Average age × National caps"), "")
    add_footer(fig)
    add_logo(fig)
    savefig(fig, "08_scatter_age_caps")


def _run_all_charts():
    chart_national_caps_avg()
    chart_national_caps_avg_bottom()
    chart_top_clubs()
    chart_top_leagues()
    chart_avg_age()
    chart_avg_height()
    chart_coaches_by_country()
    chart_home_share()
    chart_home_share_bottom()
    chart_scatter_age_caps()
    chart_records()
    chart_top_italian_clubs()
    chart_italian_players_by_nation()
    chart_big5_split()
    chart_youngest_20()
    chart_oldest_20()
    chart_age_distribution()
    chart_fifa_summary_infographic()


def main():
    global CHART_LANG
    print("Generazione grafici WC2026 (1920×1080, 16:9)")
    print(f"Font: Avenir Next Condensed")
    print(f"Logo: {LOGO_PATH or 'FALLBACK testo SC'}")
    print()
    print("======== ITALIANO → charts/ ========")
    CHART_LANG = "it"
    _run_all_charts()
    print()
    print("======== ENGLISH → charts_en/ ========")
    CHART_LANG = "en"
    _run_all_charts()
    print()
    print("✓ Tutti i grafici salvati in charts/ (IT) e charts_en/ (EN)")


if __name__ == "__main__":
    main()
