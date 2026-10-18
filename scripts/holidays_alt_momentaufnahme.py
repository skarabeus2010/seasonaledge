"""Eingefrorene Momentaufnahme von SA.holidays (landing/js/holidays.js) — Bestandsschutz für die Fassade (Kalender
V2, docs/review_prompts/2026-10-18_kalender_v2_entwurf*.md, Codex-Freigabe R3).

    py -3.14 scripts/holidays_alt_momentaufnahme.py --schreiben   # einmalig aus dem Stand VOR der Fassade
    py -3.14 scripts/holidays_alt_momentaufnahme.py --pruefen     # Wächter: Fassade unter 'alt' = Momentaufnahme

Die Probe (scripts/js/holidays_alt_probe.js) läuft unter drei Zeitzonen (UTC, America/New_York,
Pacific/Kiritimati) und wird JE ZONE festgehalten: die alte Datei ist nicht zeitzonenfrei — in Pacific/Kiritimati
fehlt der 31.12.1994 (Datumsgrenzwechsel), `new Date(j, m, t)` rollt weiter, und 1994/95 weichen ab (gemessen
2026-10-18). Bestandsschutz heißt: `alt` bleibt in JEDER Zone wie vorher. Prüfsummenliste, keine Kalenderquelle.
"""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys

WURZEL = pathlib.Path(__file__).resolve().parent.parent
ZIEL = WURZEL / "scripts" / "fixtures" / "holidays_alt.json"
PROBE = WURZEL / "scripts" / "js" / "holidays_alt_probe.js"
ZONEN = ("UTC", "America/New_York", "Pacific/Kiritimati")


def lauf(zone: str, methode: str = "alt") -> dict:
    umg = dict(os.environ, TZ=zone)
    p = subprocess.run(["node", str(PROBE), str(WURZEL), methode], capture_output=True, text=True,
                       encoding="utf-8", env=umg, timeout=600)
    if p.returncode != 0:
        raise RuntimeError(f"Probe {zone} Exit {p.returncode}: {p.stderr[-400:]}")
    return json.loads(p.stdout)["gruppen"]


def aufnahme() -> dict:
    """{zone|gruppe: prüfsummen} über alle Zonen."""
    aus = {}
    for z in ZONEN:
        for k, v in lauf(z).items():
            aus[z + "|" + k] = v
    return aus


def main() -> int:
    if "--schreiben" in sys.argv:
        if ZIEL.exists():
            print("FEHL Momentaufnahme existiert bereits — nur einmal aus dem Stand VOR der Fassade erzeugen")
            return 1
        daten = {"schema": 1, "quelle": "landing/js/holidays.js vor V2", "zonen": list(ZONEN), "gruppen": aufnahme()}
        ZIEL.write_text(json.dumps(daten, sort_keys=True, indent=0, separators=(",", ":")) + "\n", encoding="utf-8")
        print("geschrieben: %s (%d Gruppen)" % (ZIEL.relative_to(WURZEL), len(daten["gruppen"])))
        return 0
    soll = json.loads(ZIEL.read_text(encoding="utf-8"))["gruppen"]
    ist = aufnahme()
    fehler = sorted(k for k in set(soll) | set(ist) if soll.get(k) != ist.get(k))
    for k in fehler[:20]:
        print("FEHL", k, soll.get(k), "->", ist.get(k))
    print("holidays_alt_momentaufnahme: %d Gruppen, %d Abweichungen" % (len(soll), len(fehler)))
    return 1 if fehler else 0


if __name__ == "__main__":
    sys.exit(main())
