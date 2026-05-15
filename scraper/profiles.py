"""Estrae i dati fissi di un giocatore dalla scheda profilo Transfermarkt."""

import re
from datetime import datetime
from typing import Optional

from bs4 import BeautifulSoup, Tag

from .config import BASE_URL
from .http_client import TransfermarktClient


# === Helpers ===
def _clean(s: Optional[str]) -> Optional[str]:
    if s is None:
        return None
    s = re.sub(r"\s+", " ", str(s)).strip()
    return s or None


def _parse_dob_age(text: Optional[str]) -> tuple[Optional[str], Optional[int]]:
    """
    'Date of birth/Age:' value: '19/08/1991 (34)' → ('1991-08-19', 34)
    """
    if not text:
        return None, None
    age = None
    m_age = re.search(r"\((\d{1,2})\)", text)
    if m_age:
        age = int(m_age.group(1))
    m_date = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", text)
    if m_date:
        d, mo, y = m_date.groups()
        return f"{y}-{mo.zfill(2)}-{d.zfill(2)}", age
    # fallback nessun pattern: tieni testo grezzo
    return _clean(text), age


def _parse_height(text: Optional[str]) -> Optional[int]:
    """'1,71 m' / '1.71 m' → 171 cm; None se non parsabile."""
    if not text:
        return None
    t = text.replace("\xa0", " ").replace(",", ".")
    m = re.search(r"(\d+\.\d+)\s*m", t)
    if m:
        return int(round(float(m.group(1)) * 100))
    m2 = re.search(r"(\d+)\s*cm", t)
    if m2:
        return int(m2.group(1))
    return None


def _parse_position(text: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    """'Attack - Left Winger' → ('Attack', 'Left Winger')."""
    if not text:
        return None, None
    if " - " in text:
        gen, spec = text.split(" - ", 1)
        return _clean(gen), _clean(spec)
    return _clean(text), None


def _extract_other_positions(soup: BeautifulSoup) -> list[str]:
    """
    Estrae le 'Other position(s)' dal box "Main position" sulla pagina TM.

    Strategia robusta: prova vari selettori CSS perché TM cambia spesso le
    classi. Il pattern stabile è: cercare un <dt>/<th>/<span> che contiene
    "other position" (case-insensitive) e prendere tutti i <dd>/<td> testuali
    successivi, fino al prossimo <dt>/<th> o fine container.

    Ritorna lista di ruoli secondari (es. ["Left Winger", "Central Midfield"]).
    """
    out: list[str] = []

    # Strategia 1: selettori "classici" del box detail-position
    selector_groups = [
        (".detail-position__inner-box", ".detail-position__title", ".detail-position__position"),
        (".detail-position__box",       ".detail-position__title", ".detail-position__position"),
        (".detail-position",            "dt",                       "dd"),
    ]
    for box_sel, title_sel, value_sel in selector_groups:
        for box in soup.select(box_sel):
            title_el = box.select_one(title_sel)
            if not title_el:
                continue
            title = (title_el.get_text(" ", strip=True) or "").lower()
            if "other" not in title:
                continue
            for dd in box.select(value_sel):
                txt = _clean(dd.get_text(" ", strip=True))
                if txt and "other" not in txt.lower() and txt.lower() != title:
                    out.append(txt)
            if out:
                return _dedup_keep_order(out)

    # Strategia 2: cerca generico <dt> con "Other position" e prendi i <dd> successivi
    for dt in soup.find_all(["dt", "th", "span"]):
        txt = (dt.get_text(" ", strip=True) or "").lower()
        if "other position" not in txt:
            continue
        # Naviga i siblings finché non trovo un altro dt/th
        sib = dt.find_next_sibling()
        while sib is not None:
            if sib.name in ("dt", "th"):
                break
            if sib.name in ("dd", "td"):
                t = _clean(sib.get_text(" ", strip=True))
                if t and t.lower() not in ("other position:", "other position", ""):
                    out.append(t)
            sib = sib.find_next_sibling()
        if out:
            return _dedup_keep_order(out)

    # Strategia 3: regex sul testo HTML (ultimo fallback) — cerca pattern noti
    import re
    full_text = soup.get_text(" ", strip=False)
    # Pattern: "Other position(s):" seguito da uno o più ruoli su righe successive
    # Notice: euristica fragile, da usare solo se le altre strategie falliscono
    m = re.search(r"Other position[s]?:\s*([\w\s\-]+(?:\n[\w\s\-]+)?)", full_text, re.IGNORECASE)
    if m:
        block = m.group(1).strip()
        for part in re.split(r"[\n,]", block):
            t = _clean(part)
            if t and len(t) < 40 and "main" not in t.lower():
                out.append(t)

    return _dedup_keep_order(out)


def _dedup_keep_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    res: list[str] = []
    for x in items:
        if x not in seen:
            seen.add(x)
            res.append(x)
    return res


def _extract_info_table(soup: BeautifulSoup) -> dict[str, Tag]:
    """
    Costruisce mapping label -> span value (Tag, così possiamo leggere img bandiere).
    Logica corretta: 'info-table__content--regular' = label, sibling '--bold' = valore.
    """
    out: dict[str, Tag] = {}
    for label_el in soup.select("span.info-table__content--regular"):
        label = label_el.get_text(strip=True).rstrip(":").strip()
        val_el = label_el.find_next_sibling("span", class_="info-table__content--bold")
        if val_el and label:
            out[label] = val_el
    return out


def _extract_citizenships(val_el: Optional[Tag]) -> list[str]:
    """Estrae nazioni dalle bandiere img.flaggenrahmen (per dual-nationality)."""
    if val_el is None:
        return []
    out: list[str] = []
    for img in val_el.find_all("img", class_="flaggenrahmen"):
        country = img.get("title") or img.get("alt")
        if country:
            country = _clean(country)
        if country and country not in out:
            out.append(country)
    if not out:
        # fallback al testo grezzo
        text = _clean(val_el.get_text(" ", strip=True))
        if text:
            out.append(text)
    return out


def _extract_photo(soup: BeautifulSoup) -> Optional[str]:
    """URL della foto profilo del giocatore (ad alta qualità)."""
    img = soup.select_one("img.data-header__profile-image")
    if img:
        return img.get("src") or img.get("data-src")
    return None


def _extract_shirt_number(soup: BeautifulSoup) -> Optional[int]:
    """Estrarre PRIMA di chiamare _extract_full_name (che decompose lo span)."""
    el = soup.select_one(".data-header__shirt-number, [class*='shirt-number']")
    if not el:
        return None
    txt = el.get_text(strip=True).lstrip("#").strip()
    if txt.isdigit():
        return int(txt)
    return None


def _extract_full_name(soup: BeautifulSoup) -> Optional[str]:
    h1 = soup.find("h1", class_=re.compile(r"data-header__headline"))
    if h1 is None:
        h1 = soup.find("h1")
    if h1 is None:
        return None
    # Rimuovi span numero maglia (deve essere già stato letto)
    for s in h1.select(".data-header__shirt-number, [class*='shirt-number']"):
        s.decompose()
    return _clean(h1.get_text(" ", strip=True))


def _extract_current_club_id(soup: BeautifulSoup) -> tuple[Optional[int], Optional[str]]:
    """Estrae il club CORRENTE del giocatore.
    
    IMPORTANTE: Transfermarkt mostra giocatori in transizione con 'New arrival' /
    'Winter signing' / 'Returnee' nel data-header__ribbon — quel link punta al
    CLUB DI PROVENIENZA, non quello attuale. Diamo priorità a .data-header__club
    che contiene sempre il club corrente, e ignoriamo data-header__ribbon.
    """
    # Strategia 1 (priorità): .data-header__club (sempre il club corrente)
    a = soup.select_one('.data-header__club a[href*="/startseite/verein/"]')
    
    # Strategia 2: info-table-content (fallback per layout legacy)
    if a is None:
        a = soup.select_one('.info-table__content a[href*="/startseite/verein/"]')
    
    # Strategia 3 (ultima risorsa): primo link a /startseite/verein/ NON in ribbon
    if a is None:
        for candidate in soup.select('a[href*="/startseite/verein/"]'):
            parent_classes = candidate.parent.get("class", []) if candidate.parent else []
            # Escludi i link "New arrival/Winter signing/Returnee" del ribbon
            if "data-header__ribbon" in parent_classes:
                continue
            a = candidate
            break
    
    if a is None:
        return None, None
    
    href = a.get("href", "")
    m = re.search(r"/verein/(\d+)", href)
    name = _clean(a.get_text(" ", strip=True)) or _clean(a.get("title") or "")
    return (int(m.group(1)) if m else None), name


def parse_profile(html: str, player_id: int) -> dict:
    """Parsa l'HTML della scheda profilo di un giocatore."""
    soup = BeautifulSoup(html, "lxml")
    info = _extract_info_table(soup)

    def _val_text(key: str) -> Optional[str]:
        el = info.get(key)
        return _clean(el.get_text(" ", strip=True)) if el else None

    # IMPORTANTE: shirt_number prima di full_name (che decompose lo span)
    shirt = _extract_shirt_number(soup)
    full_name = _extract_full_name(soup)
    name_arabic = _val_text("Name in home country")
    dob_iso, age = _parse_dob_age(_val_text("Date of birth/Age"))
    height_cm = _parse_height(_val_text("Height"))
    foot = _val_text("Foot")
    pos_general, pos_specific = _parse_position(_val_text("Position"))
    pos_others = _extract_other_positions(soup)
    place_of_birth = _val_text("Place of birth")
    citizenships = _extract_citizenships(info.get("Citizenship"))

    # Club: preferisci dal data-header (con id), fallback a info-table
    club_id, club_name_h = _extract_current_club_id(soup)
    if not club_name_h:
        club_name_h = _val_text("Current club")

    photo_url = _extract_photo(soup)

    return {
        "tm_player_id": player_id,
        "full_name": full_name,
        "name_arabic": name_arabic,
        "date_of_birth": dob_iso,
        "age": age,
        "height_cm": height_cm,
        "foot": foot,
        "position_general": pos_general,
        "position_specific": pos_specific,
        "position_others": pos_others,
        "place_of_birth": place_of_birth,
        "citizenships": citizenships,
        # PID: è_eligible vale sempre True (siamo uno scouting hub di una lega, includiamo tutti).
        "is_target_eligible": True,
        "current_club_id": club_id,
        "current_club_name": club_name_h,
        "shirt_number": shirt,
        "photo_url": photo_url,
        "tm_profile_url": f"{BASE_URL}/-/profil/spieler/{player_id}",
        "fetched_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def scrape_player_profile(
    player_id: int,
    client: Optional[TransfermarktClient] = None,
) -> dict:
    client = client or TransfermarktClient()
    url = f"{BASE_URL}/-/profil/spieler/{player_id}"
    html = client.get_html(url)
    return parse_profile(html, player_id)
