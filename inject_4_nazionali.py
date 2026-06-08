"""
inject_4_nazionali.py — Inserisce Brazil, Ivory Coast, Sweden, Croatia
in data/wc2026_squads_raw.json bypassando parse_wikipedia_squad.py
(che si impicca su queste pagine).

Rose definitive fornite manualmente dall'utente (Wikipedia, annunci
12-18 mag 2026). tm_player_id/tm_profile_url = None: verranno risolti
dopo con resolve_wc2026_from_squad.py.

Sicuro: backup + ABORT se una delle 4 esiste gia' o se una delle 15
gia' presenti verrebbe toccata. Idempotente (se le 4 ci sono gia',
non fa nulla).

Uso:
    cd ~/Desktop/pid
    python3 inject_4_nazionali.py
"""
import json
import time
from pathlib import Path

RAW = Path("data/wc2026_squads_raw.json")
NOW = "2026-05-19T22:30:00"

OLD15 = ['Austria', 'Belgium', 'Bosnia and Herzegovina', 'Cape Verde',
         'Curaçao', 'DR Congo', 'France', 'Haiti', 'Iraq', 'Japan',
         'New Zealand', 'Portugal', 'Scotland', 'South Korea', 'Tunisia']


def P(pos, name, dob, caps, goals, club):
    return {
        "age": None, "caps": caps, "club": club, "club_country": "",
        "dob": dob, "goals": goals, "match_method": None,
        "name": name, "pos": pos, "shirt": None,
        "tm_player_id": None, "tm_profile_url": None,
    }


BRAZIL = [
    P("GK", "Alisson", "1992-10-02", 76, 0, "Liverpool"),
    P("GK", "Ederson", "1993-08-17", 31, 0, "Fenerbahçe"),
    P("GK", "Weverton", "1987-12-13", 10, 0, "Grêmio"),
    P("DF", "Marquinhos", "1994-05-14", 104, 7, "Paris Saint-Germain"),
    P("DF", "Danilo", "1991-07-15", 68, 1, "Flamengo"),
    P("DF", "Alex Sandro", "1991-01-26", 43, 2, "Flamengo"),
    P("DF", "Gabriel Magalhães", "1997-12-19", 17, 1, "Arsenal"),
    P("DF", "Bremer", "1997-03-18", 6, 1, "Juventus"),
    P("DF", "Wesley", "2003-09-06", 6, 0, "Roma"),
    P("DF", "Roger Ibañez", "1998-11-23", 5, 0, "Al-Ahli"),
    P("DF", "Douglas Santos", "1994-03-22", 5, 0, "Zenit"),
    P("DF", "Léo Pereira", "1996-01-31", 2, 0, "Flamengo"),
    P("MF", "Casemiro", "1992-02-23", 84, 8, "Manchester United"),
    P("MF", "Lucas Paquetá", "1997-08-27", 61, 12, "Flamengo"),
    P("MF", "Bruno Guimarães", "1997-11-16", 41, 2, "Newcastle United"),
    P("MF", "Fabinho", "1993-10-23", 31, 0, "Al-Ittihad"),
    P("MF", "Danilo", "2001-04-29", 2, 1, "Botafogo"),
    P("FW", "Neymar", "1992-02-05", 128, 79, "Santos"),
    P("FW", "Vinícius Júnior", "2000-07-12", 47, 8, "Real Madrid"),
    P("FW", "Raphinha", "1996-12-14", 37, 11, "Barcelona"),
    P("FW", "Gabriel Martinelli", "2001-06-18", 22, 4, "Arsenal"),
    P("FW", "Matheus Cunha", "1999-05-27", 21, 1, "Manchester United"),
    P("FW", "Endrick", "2006-07-21", 15, 3, "Lyon"),
    P("FW", "Luiz Henrique", "2001-01-02", 13, 2, "Zenit"),
    P("FW", "Igor Thiago", "2001-06-26", 2, 1, "Brentford"),
    P("FW", "Rayan", "2006-08-03", 1, 0, "Bournemouth"),
]

IVORY_COAST = [
    P("GK", "Yahia Fofana", "2000-08-21", 34, 0, "Çaykur Rizespor"),
    P("GK", "Alban Lafont", "1999-01-23", 4, 0, "Panathinaikos"),
    P("GK", "Mohamed Koné", "2002-03-07", 0, 0, "Charleroi"),
    P("DF", "Ghislain Konan", "1995-12-27", 53, 0, "Gil Vicente"),
    P("DF", "Odilon Kossounou", "2001-01-04", 35, 0, "Atalanta"),
    P("DF", "Wilfried Singo", "2000-12-25", 33, 1, "Galatasaray"),
    P("DF", "Evan Ndicka", "1999-08-20", 28, 0, "Roma"),
    P("DF", "Emmanuel Agbadou", "1997-06-07", 19, 2, "Beşiktaş"),
    P("DF", "Guéla Doué", "2002-10-17", 19, 2, "Strasbourg"),
    P("DF", "Ousmane Diomande", "2003-12-04", 14, 1, "Sporting CP"),
    P("DF", "Clément Akpa", "2001-11-24", 5, 0, "Auxerre"),
    P("MF", "Franck Kessié", "1996-12-19", 102, 15, "Al-Ahli"),
    P("MF", "Jean Michaël Seri", "1991-07-19", 65, 4, "Maribor"),
    P("MF", "Ibrahim Sangaré", "1997-12-02", 57, 12, "Nottingham Forest"),
    P("MF", "Seko Fofana", "1995-05-07", 31, 7, "Porto"),
    P("MF", "Christ Inao Oulaï", "2006-04-06", 8, 0, "Trabzonspor"),
    P("MF", "Parfait Guiagon", "2001-02-22", 5, 0, "Charleroi"),
    P("FW", "Nicolas Pépé", "1995-05-29", 54, 12, "Villarreal"),
    P("FW", "Oumar Diakité", "2003-12-20", 28, 6, "Cercle Brugge"),
    P("FW", "Simon Adingra", "2002-01-01", 28, 5, "Monaco"),
    P("FW", "Evann Guessand", "2001-07-01", 21, 4, "Crystal Palace"),
    P("FW", "Amad Diallo", "2002-07-11", 18, 5, "Manchester United"),
    P("FW", "Yan Diomande", "2006-11-14", 9, 3, "RB Leipzig"),
    P("FW", "Bazoumana Touré", "2006-03-02", 5, 2, "TSG Hoffenheim"),
    P("FW", "Elye Wahi", "2003-01-02", 1, 0, "Nice"),
    P("FW", "Ange-Yoan Bonny", "2003-10-25", 0, 0, "Inter Milan"),
]

SWEDEN = [
    P("GK", "Kristoffer Nordfeldt", "1989-06-23", 20, 0, "AIK"),
    P("GK", "Viktor Johansson", "1998-09-14", 12, 0, "Stoke City"),
    P("GK", "Jacob Widell Zetterström", "1998-07-11", 2, 0, "Derby County"),
    P("DF", "Victor Lindelöf", "1994-07-17", 75, 3, "Aston Villa"),
    P("DF", "Isak Hien", "1999-01-13", 27, 0, "Atalanta"),
    P("DF", "Gabriel Gudmundsson", "1999-04-29", 23, 0, "Leeds United"),
    P("DF", "Carl Starfelt", "1995-06-01", 17, 0, "Celta Vigo"),
    P("DF", "Emil Holm", "2000-05-13", 16, 2, "Juventus"),
    P("DF", "Hjalmar Ekdal", "1998-10-21", 11, 0, "Burnley"),
    P("DF", "Daniel Svensson", "2002-02-12", 11, 0, "Borussia Dortmund"),
    P("DF", "Gustaf Lagerbielke", "2000-04-10", 9, 2, "Braga"),
    P("DF", "Eric Smith", "1997-01-08", 0, 0, "FC St. Pauli"),
    P("DF", "Elliot Stroud", "2002-06-22", 0, 0, "Mjällby AIF"),
    P("MF", "Mattias Svanberg", "1999-01-05", 39, 2, "VfL Wolfsburg"),
    P("MF", "Jesper Karlström", "1995-06-21", 23, 0, "Udinese"),
    P("MF", "Yasin Ayari", "2003-10-06", 19, 3, "Brighton & Hove Albion"),
    P("MF", "Lucas Bergvall", "2006-02-02", 8, 0, "Tottenham Hotspur"),
    P("MF", "Besfort Zeneli", "2002-11-21", 6, 0, "Union Saint-Gilloise"),
    P("FW", "Alexander Isak", "1999-09-21", 56, 16, "Liverpool"),
    P("FW", "Viktor Gyökeres", "1998-06-04", 32, 19, "Arsenal"),
    P("FW", "Ken Sema", "1993-09-30", 32, 5, "Pafos"),
    P("FW", "Anthony Elanga", "2002-04-27", 28, 6, "Newcastle United"),
    P("FW", "Benjamin Nygren", "2001-07-08", 9, 3, "Celtic"),
    P("FW", "Alexander Bernhardsson", "1998-09-08", 9, 0, "Holstein Kiel"),
    P("FW", "Gustaf Nilsson", "1997-05-23", 8, 3, "Club Brugge"),
    P("FW", "Taha Ali", "1998-07-01", 1, 0, "Malmö FF"),
]

CROATIA = [
    P("GK", "Dominik Livaković", "1995-01-09", 73, 0, "Dinamo Zagreb"),
    P("GK", "Dominik Kotarski", "2000-02-10", 3, 0, "Copenhagen"),
    P("GK", "Ivor Pandur", "2000-03-25", 0, 0, "Hull City"),
    P("DF", "Joško Gvardiol", "2002-01-23", 46, 4, "Manchester City"),
    P("DF", "Duje Ćaleta-Car", "1996-09-17", 38, 1, "Real Sociedad"),
    P("DF", "Josip Šutalo", "2000-02-28", 31, 0, "Ajax"),
    P("DF", "Josip Stanišić", "2000-04-02", 29, 0, "Bayern Munich"),
    P("DF", "Marin Pongračić", "1997-09-11", 18, 0, "Fiorentina"),
    P("DF", "Martin Erlić", "1998-01-24", 12, 1, "Midtjylland"),
    P("DF", "Luka Vušković", "2007-02-24", 4, 1, "Hamburger SV"),
    P("MF", "Luka Modrić", "1985-09-09", 196, 28, "Milan"),
    P("MF", "Mateo Kovačić", "1994-05-06", 111, 5, "Manchester City"),
    P("MF", "Mario Pašalić", "1995-02-09", 83, 11, "Atalanta"),
    P("MF", "Nikola Vlašić", "1997-10-04", 61, 10, "Torino"),
    P("MF", "Luka Sučić", "2002-09-08", 19, 1, "Real Sociedad"),
    P("MF", "Martin Baturina", "2003-02-16", 17, 1, "Como"),
    P("MF", "Kristijan Jakić", "1997-05-14", 16, 2, "FC Augsburg"),
    P("MF", "Petar Sučić", "2003-10-25", 15, 1, "Inter Milan"),
    P("MF", "Nikola Moro", "1998-03-12", 9, 0, "Bologna"),
    P("MF", "Toni Fruk", "2001-04-09", 7, 1, "Rijeka"),
    P("FW", "Ivan Perišić", "1989-02-02", 152, 38, "PSV Eindhoven"),
    P("FW", "Andrej Kramarić", "1991-06-19", 114, 36, "TSG Hoffenheim"),
    P("FW", "Ante Budimir", "1991-07-22", 36, 6, "Osasuna"),
    P("FW", "Marco Pašalić", "2000-09-14", 13, 1, "Orlando City"),
    P("FW", "Petar Musa", "1998-03-04", 10, 1, "FC Dallas"),
    P("FW", "Igor Matanović", "2003-03-31", 8, 2, "SC Freiburg"),
]

NEW = {
    "Brazil": ("https://en.wikipedia.org/wiki/Brazil_national_football_team", BRAZIL),
    "Ivory Coast": ("https://en.wikipedia.org/wiki/Ivory_Coast_national_football_team", IVORY_COAST),
    "Sweden": ("https://en.wikipedia.org/wiki/Sweden_national_football_team", SWEDEN),
    "Croatia": ("https://en.wikipedia.org/wiki/Croatia_national_football_team", CROATIA),
}


def main():
    if not RAW.exists():
        print("ERRORE: data/wc2026_squads_raw.json non trovato")
        return 1

    d = json.loads(RAW.read_text(encoding="utf-8"))
    print(f"Nazionali attuali nel file: {len(d)}")

    # Idempotenza / conflitti
    already = [c for c in NEW if c in d]
    if already:
        print(f"⚠️  Gia' presenti: {already}. ABORT (non sovrascrivo). "
              f"Se vuoi rigenerarle, rimuovile prima a mano.")
        return 1

    # Snapshot 15 esistenti
    pre = {}
    for c in OLD15:
        v = d.get(c, {})
        pl = v.get("players", []) if isinstance(v, dict) else []
        pre[c] = (sum(1 for p in pl if p.get("tm_player_id")), len(pl))

    # Backup
    ts = time.strftime("%Y%m%d_%H%M%S")
    bak = RAW.with_suffix(f".json.bak-inject4-{ts}")
    bak.write_text(RAW.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Backup: {bak.name}")

    # Inietta
    for country, (wiki, players) in NEW.items():
        d[country] = {
            "country": country,
            "wiki_url": wiki,
            "status": "final",
            "imported_at": NOW,
            "players": players,
        }
        print(f"  + {country}: {len(players)} giocatori (tm_id da risolvere)")

    RAW.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")

    # Verifica: 15 intatte + 4 nuove presenti
    chk = json.loads(RAW.read_text(encoding="utf-8"))
    bad = False
    for c in OLD15:
        v = chk.get(c, {})
        pl = v.get("players", []) if isinstance(v, dict) else []
        now = (sum(1 for p in pl if p.get("tm_player_id")), len(pl))
        if now != pre[c]:
            print(f"  🚨 {c} CAMBIATA: {pre[c]} -> {now}")
            bad = True
    for c in NEW:
        if c not in chk or len(chk[c]["players"]) == 0:
            print(f"  🚨 {c} NON inserita correttamente")
            bad = True

    if bad:
        print(f"\nPROBLEMA. Rollback: cp {bak} {RAW}")
        return 2

    tot = len(chk)
    print(f"\n✅ OK. Nazionali ora: {tot} (15 intatte + 4 nuove).")
    print("   Le 4 nuove hanno tm_player_id=None: prossimo step")
    print("   resolve_wc2026_from_squad.py per ciascuna (mai --reresolve).")
    print(f"   Backup: {bak.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
