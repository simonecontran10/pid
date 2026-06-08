"""
finalize_coaches.py — Arricchisce wc2026_coaches.json con la nazionalità
nota di ciascun allenatore (hardcoded, sorgente: Wikipedia + FIFA).
"""
import json
from pathlib import Path
from collections import Counter

# Mapping: NazionaleFIFA → (NomeAllenatore, NazionalitàAllenatore)
COACHES = {
    "Algeria":                 ("Vladimir Petković",       "Svizzera"),
    "Argentina":               ("Lionel Scaloni",          "Argentina"),
    "Australia":               ("Tony Popovic",            "Australia"),
    "Austria":                 ("Ralf Rangnick",           "Germania"),
    "Belgium":                 ("Rudi Garcia",             "Francia"),
    "Bosnia And Herzegovina":  ("Sergej Barbarez",         "Bosnia ed Erzegovina"),
    "Brazil":                  ("Carlo Ancelotti",         "Italia"),
    "Canada":                  ("Jesse Marsch",            "Stati Uniti"),
    "Cape Verde":              ("Bubista",                 "Capo Verde"),
    "Colombia":                ("Néstor Lorenzo",          "Argentina"),
    "Congo DR":                ("Sébastien Desabre",       "Francia"),
    "Côte D'Ivoire":           ("Emerse Faé",              "Costa d'Avorio"),
    "Croatia":                 ("Zlatko Dalić",            "Croazia"),
    "Curaçao":                 ("Dick Advocaat",           "Paesi Bassi"),
    "Czechia":                 ("Miroslav Koubek",         "Repubblica Ceca"),
    "Ecuador":                 ("Sebastián Beccacece",     "Argentina"),
    "Egypt":                   ("Hossam Hassan",           "Egitto"),
    "England":                 ("Thomas Tuchel",           "Germania"),
    "France":                  ("Didier Deschamps",        "Francia"),
    "Germany":                 ("Julian Nagelsmann",       "Germania"),
    "Ghana":                   ("Otto Addo",               "Ghana"),
    "Haiti":                   ("Sébastien Migné",         "Francia"),
    "IR Iran":                 ("Amir Ghalenoei",          "Iran"),
    "Iraq":                    ("Graham Arnold",           "Australia"),
    "Japan":                   ("Hajime Moriyasu",         "Giappone"),
    "Jordan":                  ("Jamal Sellami",           "Marocco"),
    "Korea Republic":          ("Hong Myung-bo",           "Corea del Sud"),
    "Mexico":                  ("Javier Aguirre",          "Messico"),
    "Morocco":                 ("Walid Regragui",          "Marocco"),
    "Netherlands":             ("Ronald Koeman",           "Paesi Bassi"),
    "New Zealand":             ("Darren Bazeley",          "Inghilterra"),
    "Norway":                  ("Ståle Solbakken",         "Norvegia"),
    "Panama":                  ("Thomas Christiansen",     "Danimarca"),
    "Paraguay":                ("Gustavo Alfaro",          "Argentina"),
    "Portugal":                ("Roberto Martínez",        "Spagna"),
    "Qatar":                   ("Julen Lopetegui",         "Spagna"),
    "Saudi Arabia":            ("Hervé Renard",            "Francia"),
    "Scotland":                ("Steve Clarke",            "Scozia"),
    "Senegal":                 ("Pape Thiaw",              "Senegal"),
    "South Africa":            ("Hugo Broos",              "Belgio"),
    "Spain":                   ("Luis de la Fuente",       "Spagna"),
    "Sweden":                  ("Graham Potter",           "Inghilterra"),
    "Switzerland":             ("Murat Yakin",             "Svizzera"),
    "Tunisia":                 ("Sami Trabelsi",           "Tunisia"),
    "Turkey":                  ("Vincenzo Montella",       "Italia"),
    "United States":           ("Mauricio Pochettino",     "Argentina"),
    "Uruguay":                 ("Marcelo Bielsa",          "Argentina"),
    "Uzbekistan":              ("Fabio Cannavaro",         "Italia"),
}

# Mapping per match "nazione coach = nazione nazionale"
# (i nomi delle nazionali sono in inglese, i coach in italiano → traduco)
NATION_IT = {
    "Algeria":"Algeria","Argentina":"Argentina","Australia":"Australia",
    "Austria":"Austria","Belgium":"Belgio","Bosnia And Herzegovina":"Bosnia ed Erzegovina",
    "Brazil":"Brasile","Canada":"Canada","Cape Verde":"Capo Verde",
    "Colombia":"Colombia","Congo DR":"Repubblica Democratica del Congo",
    "Côte D'Ivoire":"Costa d'Avorio","Croatia":"Croazia","Curaçao":"Curaçao",
    "Czechia":"Repubblica Ceca","Ecuador":"Ecuador","Egypt":"Egitto",
    "England":"Inghilterra","France":"Francia","Germany":"Germania",
    "Ghana":"Ghana","Haiti":"Haiti","IR Iran":"Iran","Iraq":"Iraq",
    "Japan":"Giappone","Jordan":"Giordania","Korea Republic":"Corea del Sud",
    "Mexico":"Messico","Morocco":"Marocco","Netherlands":"Paesi Bassi",
    "New Zealand":"Nuova Zelanda","Norway":"Norvegia","Panama":"Panama",
    "Paraguay":"Paraguay","Portugal":"Portogallo","Qatar":"Qatar",
    "Saudi Arabia":"Arabia Saudita","Scotland":"Scozia","Senegal":"Senegal",
    "South Africa":"Sudafrica","Spain":"Spagna","Sweden":"Svezia",
    "Switzerland":"Svizzera","Tunisia":"Tunisia","Turkey":"Turchia",
    "United States":"Stati Uniti","Uruguay":"Uruguay","Uzbekistan":"Uzbekistan",
}


def main():
    out = {n: {"name": name, "country": country} for n, (name, country) in COACHES.items()}
    Path("data/wc2026_coaches.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(f"✓ {len(out)} allenatori finalizzati in data/wc2026_coaches.json")
    print()
    print("=" * 70)
    print("ALLENATORI PER NAZIONALITÀ")
    print("=" * 70)
    c = Counter(v["country"] for v in out.values())
    for cnt, n in c.most_common():
        print(f"  {n:>2}  {cnt}")

    print()
    print("=" * 70)
    print(f"NAZIONALI CON ALLENATORE STRANIERO ({sum(1 for n,v in out.items() if v['country'] != NATION_IT[n])}/48)")
    print("=" * 70)
    foreign_count = 0
    same_count = 0
    for n in sorted(out):
        coach_c = out[n]["country"]
        nation_c = NATION_IT[n]
        if coach_c != nation_c:
            foreign_count += 1
            print(f"  {n:<25s}  {out[n]['name']:<25s}  ({coach_c})")
        else:
            same_count += 1
    print()
    print(f"  Riepilogo: {foreign_count} stranieri / {same_count} connazionali")


if __name__ == "__main__":
    main()
