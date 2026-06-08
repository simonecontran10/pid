"""
diff_belgium.py — Confronta la rosa Belgium PRE e POST scrape per capire
se il calo 27->26 e' un legittimo cambio-rosa Wikipedia o un glitch parser.

Confronta:
  - PRE : data/wc2026_squads_raw.json.bak-scrape-20260519_154803  (backup di stamattina)
  - POST: data/wc2026_squads_raw.json                              (dopo scrape)

Per Belgium elenca: giocatori presenti in entrambi (con stato tm_id),
solo-PRE (spariti), solo-POST (nuovi). Cosi' si vede ESATTAMENTE cosa
e' cambiato e se qualche tm_id e' stato perso su un giocatore ancora in rosa.

Uso:
    cd ~/Desktop/pid
    python3 diff_belgium.py
"""
import json
import glob
from pathlib import Path

POST = Path("data/wc2026_squads_raw.json")
# il backup piu' recente bak-scrape-*
baks = sorted(glob.glob("data/wc2026_squads_raw.json.bak-scrape-*"))


def players_of(d, country):
    v = d.get(country, {})
    pl = v.get("players", []) if isinstance(v, dict) else []
    out = {}
    for p in pl:
        name = p.get("name") or p.get("player_name") or "?"
        out[name] = p.get("tm_player_id")
    return out


def main():
    if not baks:
        print("ERRORE: nessun backup bak-scrape-* trovato.")
        return 1
    bak = baks[-1]
    print(f"PRE : {bak}")
    print(f"POST: {POST}\n")

    d_pre = json.loads(Path(bak).read_text(encoding="utf-8"))
    d_post = json.loads(POST.read_text(encoding="utf-8"))

    for country in ["Belgium", "Bosnia and Herzegovina"]:
        pre = players_of(d_pre, country)
        post = players_of(d_post, country)
        print(f"===== {country} =====")
        print(f"  PRE: {len(pre)} giocatori | POST: {len(post)} giocatori")

        only_pre = [n for n in pre if n not in post]
        only_post = [n for n in post if n not in pre]
        common = [n for n in post if n in pre]

        # Il check che conta: qualche giocatore COMUNE ha perso il tm_id?
        lost_tmid = [n for n in common if pre[n] and not post[n]]

        print(f"  Giocatori spariti (solo PRE): {len(only_pre)}")
        for n in only_pre:
            print(f"    - {n}  (tm_id era: {pre[n]})")
        print(f"  Giocatori nuovi (solo POST): {len(only_post)}")
        for n in only_post:
            print(f"    + {n}  (tm_id: {post[n] or 'da risolvere'})")
        print(f"  Giocatori in entrambi: {len(common)}")
        if lost_tmid:
            print(f"  🚨 PERDITA tm_id su giocatori ANCORA in rosa: {len(lost_tmid)}")
            for n in lost_tmid:
                print(f"    !! {n}: PRE tm_id={pre[n]} -> POST tm_id={post[n]}")
            print("  => Questo SI sarebbe un bug del parser. Va indagato.")
        else:
            print("  ✅ Nessun giocatore comune ha perso il tm_id.")
            print("     Il calo e' dovuto a cambio-rosa su Wikipedia (legittimo),")
            print("     NON a un overwrite/bug del parser.")
        print()

    print("CONCLUSIONE:")
    print("  Se per Belgium 'Nessun giocatore comune ha perso il tm_id' e")
    print("  i spariti/nuovi sono cambi-rosa reali -> e' un FALSO ALLARME")
    print("  dello script prudente. Si puo' procedere al resolve.")
    print("  Altrimenti -> rollback dal backup e indagine parser.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
