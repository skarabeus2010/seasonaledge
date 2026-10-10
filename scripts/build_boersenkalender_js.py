#!/usr/bin/env python3
"""
Erzeugt landing/js/boersenkalender.js — Daten aus Python + API aus scripts/boersenkalender/api.js.

Eine Quelle für Python und Seiten (Plan v5/v6, Weg A): die Schließtage kommen aus
shared.exchange_holidays.get_holidays, die Ticker-Zuordnung aus shared.symbols, der Status aus
KALENDER_GUELTIG. Deterministisch (sortierte Schlüssel, LF, kein Zeitstempel).

    py -3.14 scripts/build_boersenkalender_js.py            # schreibt die Datei
    py -3.14 scripts/build_boersenkalender_js.py --pruefen  # vergleicht ohne zu schreiben mit der
                                                            # Arbeitsdatei UND git HEAD; Exit 1 bei Abweichung

Schema 1: {schema, version, pruefdatum, von, bis, woche, schliessungen, status, ticker, suffix, ereignisse}.
`ereignisse` ist für Schema 2 reserviert (stabile Feiertagskennungen für /feiertage und Dashboard, P4)
und in Schema 1 leer — die Schließtage allein tragen keine Ereignisidentität.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, WURZEL)

from shared.exchange_holidays import (  # noqa: E402
    _EXCHANGE_FUNCTIONS, KALENDER_GUELTIG, KALENDER_PRUEFDATUM, NUMMERN_BIS_JAHR, NUMMERN_VON_JAHR, get_holidays,
)
from shared.symbols import SUFFIX_ZU_BOERSE, SYMBOLS, get_exchange_for_holidays  # noqa: E402

ZIEL = os.path.join(WURZEL, "landing", "js", "boersenkalender.js")
ZIEL_REL = "landing/js/boersenkalender.js"
API = os.path.join(WURZEL, "scripts", "boersenkalender", "api.js")
PLATZHALTER = "/*__DATEN__*/null"


def daten() -> dict:
    boersen = sorted(b for b in _EXCHANGE_FUNCTIONS if b != "NASDAQ")
    schliessungen = {}
    for b in boersen:
        jahre = {}
        for j in range(NUMMERN_VON_JAHR, NUMMERN_BIS_JAHR + 1):
            tage = sorted(get_holidays(b, j, j))
            if tage:
                jahre[str(j)] = "".join(d.strftime("%m%d") for d in tage)
        schliessungen[b] = jahre
    nutz = {
        "schema": 1,
        "pruefdatum": KALENDER_PRUEFDATUM,
        "von": NUMMERN_VON_JAHR,
        "bis": NUMMERN_BIS_JAHR,
        "woche": {b: ("taeglich" if b == "CRYPTO" else "MoFr") for b in boersen},
        "schliessungen": schliessungen,
        "status": {b: [KALENDER_GUELTIG[b][0], [list(i) for i in KALENDER_GUELTIG[b][1]]] for b in boersen},
        "ticker": {t.upper(): get_exchange_for_holidays(t) for t in SYMBOLS},
        "suffix": [list(s) for s in SUFFIX_ZU_BOERSE],
        "ereignisse": {},
    }
    kanon = json.dumps(nutz, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    nutz["version"] = hashlib.sha256(kanon.encode("utf-8")).hexdigest()
    return nutz


def erzeugen() -> bytes:
    with open(API, encoding="utf-8") as fh:
        api = fh.read().replace("\r\n", "\n")
    if api.count(PLATZHALTER) != 1:
        raise SystemExit(f"Platzhalter {PLATZHALTER} fehlt oder ist mehrfach in {API}")
    json_text = json.dumps(daten(), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    kopf = ("// ERZEUGT von scripts/build_boersenkalender_js.py — nicht von Hand ändern.\n"
            "// Quelle: shared/exchange_holidays.py, shared/symbols.py, scripts/boersenkalender/api.js\n")
    return (kopf + api.replace(PLATZHALTER, json_text)).encode("utf-8")


def main() -> int:
    neu = erzeugen()
    if "--pruefen" in sys.argv:
        fehler = []
        try:
            with open(ZIEL, "rb") as fh:
                if fh.read() != neu:
                    fehler.append("Arbeitsdatei weicht ab (neu erzeugen und committen)")
        except FileNotFoundError:
            fehler.append("Arbeitsdatei fehlt")
        r = subprocess.run(["git", "show", f"HEAD:{ZIEL_REL}"], cwd=WURZEL, capture_output=True)
        if r.returncode != 0:
            fehler.append("in git HEAD nicht vorhanden")
        elif r.stdout != neu:
            fehler.append("git HEAD weicht ab (Zeilenenden? .gitattributes eol=lf)")
        for f in fehler:
            print("FEHL", f)
        print("boersenkalender.js aktuell" if not fehler else "boersenkalender.js NICHT aktuell")
        return 1 if fehler else 0
    with open(ZIEL, "wb") as fh:
        fh.write(neu)
    print(f"{ZIEL_REL}: {len(neu)} Bytes geschrieben")
    return 0


if __name__ == "__main__":
    sys.exit(main())
