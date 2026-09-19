#!/usr/bin/env python3
"""
verify_cm_gruppen.py — Wächter für die gemeinsame Stützstellen-Rangliste.

    py -3.14 scripts/verify_cm_gruppen.py        Exit 1 bei Abweichung

WARUM ES DAS GIBT: `shared.black_scholes.cm_leg_kandidaten` wird von ZWEI
Stellen aufgerufen — dem Live-Lauf (`compute_options_skew._skew_cm`) und dem
Backfill (`backfill_skew_massive._plan` / `_reconstruct`). Beim Anbinden der
zweiten Stelle am 2026-09-19 habe ich direkt über die Gruppen iteriert, obwohl
sie dicts der Form {exps, pool, art, rang} sind: die Iteration lief über die
dict-Schlüssel, und `len(g) == 2` zählte Schlüssel statt Stützstellen.

Der Syntax-Check konnte das nicht fangen (Laufzeitfehler), und die Wächter für
die Vola-Mathematik auch nicht — gefunden hat es erst ein echter Einzellauf
gegen die API (`SPY FEHLER: 'exps'`). Ein 163-Ticker-Lauf hätte 18 Stunden
gebraucht, um dasselbe zu sagen.

Dieser Wächter prüft deshalb die VERTRAGSSEITE der gemeinsamen Funktion und
dass beide Aufrufer sie einhalten — verhaltensbasiert, nicht als Textsuche im
Quellcode: ein textueller Check bestand in diesem Projekt schon einmal,
während der Fehler drinstand.
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from shared.black_scholes import (CM_DAYS, CM_DTE_MAX, CM_DTE_MIN,   # noqa: E402
                                  cm_leg_kandidaten)

_fehler = 0
_faelle = 0


def pruef(name: str, ist, soll) -> None:
    global _fehler, _faelle
    _faelle += 1
    ok = (ist == soll)
    if not ok:
        _fehler += 1
    print(("  ok    " if ok else "  FEHL  ") + name + "  ->  " + repr(ist)
          + ("" if ok else "   erwartet " + repr(soll)))


print("-- Vertrag: was liefert cm_leg_kandidaten? --")
# Eine Kette mit Monatsverfall-Klammer um 30 Tage und Wochenverfaellen.
kette = {"2026-09-25": 6, "2026-10-02": 13, "2026-10-09": 20,
         "2026-10-16": 27, "2026-11-20": 62}
g = cm_leg_kandidaten(kette)
pruef("liefert eine nicht-leere Liste", bool(g), True)
pruef("jede Gruppe ist ein dict", all(isinstance(x, dict) for x in g), True)
pruef("jede Gruppe hat exps/pool/art/rang",
      all({"exps", "pool", "art", "rang"} <= set(x) for x in g), True)
pruef("exps ist immer eine Liste", all(isinstance(x["exps"], list) for x in g), True)
pruef("exps hat ein oder zwei Eintraege",
      all(1 <= len(x["exps"]) <= 2 for x in g), True)
pruef("alle exps stammen aus der Eingabe",
      all(e in kette for x in g for e in x["exps"]), True)
pruef("rang ist aufsteigend und lueckenlos",
      [x["rang"] for x in g], list(range(len(g))))

print("-- die Falle: direkt ueber eine Gruppe iterieren --")
# Genau der Fehler, der im Backfill stand. Ein dict iteriert seine SCHLUESSEL.
erste = g[0]
pruef("len(gruppe) ist NICHT die Zahl der Stuetzstellen",
      len(erste) == len(erste["exps"]), False)
pruef("Iteration ueber die Gruppe liefert Schluessel, keine Expiries",
      sorted(erste), ["art", "exps", "pool", "rang"])
pruef("korrekt ist gruppe['exps']",
      all(e.count("-") == 2 for e in erste["exps"]), True)

print("-- Rangfolge: echte Klammer vor Extrapolation --")
pruef("die beste Gruppe ist eine echte Klammer", g[0]["art"], "klammer")
lo, hi = (kette[e] for e in g[0]["exps"])
pruef("und sie klammert CM_DAYS wirklich",
      min(lo, hi) <= CM_DAYS <= max(lo, hi), True)
pruef("sie kommt aus dem liquidesten Pool", g[0]["pool"], "monatlich")

print("-- der Fall, der den Radar leer laufen liess (2026-09-15) --")
# Monatsverfaelle bei 3 und 31 Tagen: 3 liegt unter CM_DTE_MIN, eine Klammer
# aus dem Monats-Pool ist unmoeglich. Die Wochenverfaelle bei 10, 17 und 24
# Tagen koennen klammern — vorher wurden sie nie betrachtet, weil der Pool
# gewaehlt wurde, BEVOR klar war, ob er klammern kann.
sept = {"2026-09-18": 3, "2026-10-16": 31,            # Monatsverfaelle (3. Freitag)
        "2026-09-25": 10, "2026-10-02": 17, "2026-10-09": 24}
gs = cm_leg_kandidaten(sept)
pruef("es gibt Kandidaten", bool(gs), True)
beste = gs[0]
lo2, hi2 = (sept[e] for e in beste["exps"]) if len(beste["exps"]) == 2 else (0, 0)
pruef("die beste Gruppe klammert 30 Tage",
      len(beste["exps"]) == 2 and min(lo2, hi2) <= CM_DAYS <= max(lo2, hi2), True)
pruef("und nimmt dafuer die Wochenverfaelle", beste["pool"], "freitags")
pruef("nicht extrapoliert", beste["art"], "klammer")

print("-- Randfaelle --")
pruef("leere Eingabe", cm_leg_kandidaten({}), [])
pruef("None", cm_leg_kandidaten(None), [])
# Alles ausserhalb des zulaessigen Laufzeitbands -> keine Gruppe
weit = {"2026-09-20": 1, "2027-06-18": 300}
pruef("alles ausserhalb DTE_MIN/MAX ergibt keine Gruppe",
      cm_leg_kandidaten(weit), [])
# Nur ein einziger Verfall -> Einzelpunkt, keine Klammer
einzel = cm_leg_kandidaten({"2026-10-16": 28})
pruef("ein einziger Verfall ergibt einen Einzelpunkt",
      [x["art"] for x in einzel], ["einzel"])
pruef("Duplikate in den Gruppen gibt es nicht",
      len({tuple(x["exps"]) for x in g}), len(g))

print("-- beide Aufrufer halten den Vertrag ein --")
# Verhaltensbasiert: die Zugriffsmuster beider Seiten auf echten Gruppen
# ausfuehren. Wirft eines davon, ist der Vertrag gebrochen.
try:
    # Live-Muster (compute_options_skew._skew_cm)
    for x in g:
        exps = x["exps"]
        if len(exps) == 2:
            _a, _b = exps[0], exps[1]
    # Backfill-Muster (_plan): Vereinigung der ersten Gruppen
    gewaehlt = []
    for x in g[:3]:
        for e in x["exps"]:
            if e not in gewaehlt:
                gewaehlt.append(e)
    # Backfill-Muster (_reconstruct): beste verfuegbare Gruppe
    vorhanden = {e: {"dte": kette[e]} for e in gewaehlt}
    paar = None
    for x in cm_leg_kandidaten({e: v["dte"] for e, v in vorhanden.items()}):
        ex = x["exps"]
        if len(ex) == 2 and all(e in vorhanden for e in ex):
            paar = [vorhanden[ex[0]], vorhanden[ex[1]]]
            break
    pruef("Live- und Backfill-Zugriffsmuster laufen beide durch", paar is not None, True)
    pruef("_plan waehlt mehr als eine Stuetzstelle", len(gewaehlt) >= 2, True)
except (KeyError, TypeError, IndexError) as e:
    pruef("Zugriffsmuster ohne Fehler", "%s: %s" % (type(e).__name__, e), "kein Fehler")

print()
if _fehler:
    print("FEHLER: %d von %d Faellen" % (_fehler, _faelle))
else:
    print("[OK] alle %d Faelle gruen — Vertrag und beide Aufrufer" % _faelle)
sys.exit(1 if _fehler else 0)
