#!/usr/bin/env python3
"""
export_intermarket.py — Matrix-Ergebnis in die Form bringen, die /intermarket lädt.

    py -3.14 scripts/research/export_intermarket.py \
        --ein <matrix.json> --aus landing/data/intermarket_matrix.json

Das Rohergebnis von intermarket_matrix.py ist 369 KB, weil jede der 556 Zellen
ihre Feldnamen mitschleppt. Hier werden die Zellen zu ZEILEN, und die Feldnamen
stehen EINMAL unter "felder" — dieselbe Information, ein Fünftel der Groesse.
Das ist kein reiner Schoenheitsfix: die Datei wird bei jedem Seitenaufruf
geladen, und /flows hat schon einmal gehangen, weil eine 2,6-MB-Datei
unkomprimiert durchging.

WAS BEWUSST MITGEHT, obwohl es die Datei groesser macht: Zeitraum (von/bis),
Beobachtungen und Ereignisse je Zeithaelfte. Ohne diese vier Zahlen kann ein
Leser nicht erkennen, dass eine Zelle mit n=35 und 21/14 Ereignissen je Haelfte
etwas anderes ist als eine mit n=52 und 26/26 — und genau an dieser
Unterscheidung haengt auf dieser Seite, was ein Befund sein darf.
"""
from __future__ import annotations

import argparse
import io
import json
import pathlib
import sys

# Reihenfolge der Spalten in "zeilen". Wer hier etwas einfuegt, muss es im
# Frontend an derselben Stelle einfuegen — deshalb steht die Liste auch in der
# Datei selbst, damit das Frontend nicht auf Positionen raten muss.
FELDER = [
    "signal", "ziel", "richtung", "n", "h1_n", "h2_n",
    "effekt_pct", "basis_pct", "ueberschuss_pp", "t_wert", "p_max_t",
    "schwelle_pct", "h1_pp", "h2_pp", "von", "bis", "beob",
    "primaer", "haelt_beide", "genug_je_haelfte", "status",
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ein", required=True)
    ap.add_argument("--aus", required=True)
    a = ap.parse_args()

    roh = json.load(io.open(a.ein, encoding="utf-8"))
    zellen = roh["zellen"]

    # Die Maerkte aus den Zellen selbst ableiten, nicht aus einer zweiten
    # Liste: so kann die Seite keine Kategorie anzeigen, die in den Daten
    # nicht vorkommt.
    maerkte: dict[str, dict] = {}
    for z in zellen:
        for rolle in ("signal", "ziel"):
            t = z[rolle]
            if t not in maerkte:
                maerkte[t] = {"t": t, "name": z[rolle + "_name"],
                              "gruppe": z[rolle + "_gruppe"],
                              "ist_signal": False, "ist_ziel": False}
            maerkte[t]["ist_" + rolle] = True

    zeilen = []
    for z in zellen:
        zeilen.append([z.get(f) for f in FELDER])

    aus = {
        "stand": roh["stand"],
        "horizont_tage": roh["horizont_tage"],
        "signalfenster_tage": roh["signalfenster_tage"],
        "perzentil": roh["perzentil"],
        "min_ereignisse": roh["min_ereignisse"],
        "min_je_haelfte": roh["min_je_haelfte"],
        "runden": roh["runden"],
        "schranke_t": roh["max_t_schranke_t"],
        "n_zellen": roh["n_zellen"],
        "n_primaer": roh["primaerfamilie"],
        "n_befunde": roh["n_befunde"],
        "maerkte": sorted(maerkte.values(), key=lambda m: (m["gruppe"], m["name"])),
        "felder": FELDER,
        "zeilen": zeilen,
    }

    ziel = pathlib.Path(a.aus)
    ziel.parent.mkdir(parents=True, exist_ok=True)
    io.open(ziel, "w", encoding="utf-8", newline="\n").write(
        json.dumps(aus, ensure_ascii=False, separators=(",", ":")))
    print("%s  (%.0f KB, %d Zellen, %d Märkte)"
          % (ziel, ziel.stat().st_size / 1024, len(zeilen), len(maerkte)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
