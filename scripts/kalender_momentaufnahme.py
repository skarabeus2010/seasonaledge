"""Eingefrorene Momentaufnahme des Börsenkalenders — Bestandsschutz für den Umbau zum Ereigniskatalog (V1c-1,
docs/KALENDER_UMSTELLUNG.md; Entwurf docs/review_prompts/2026-10-11_kalender_v1c_entwurf*.md).

    py -3.14 scripts/kalender_momentaufnahme.py --schreiben    # einmalig aus dem Stand VOR dem Umbau
    py -3.14 scripts/kalender_momentaufnahme.py --pruefen      # Wächter: aktueller Stand = Momentaufnahme

Je Börse (alle aus _EXCHANGE_FUNCTIONS, inkl. NASDAQ-Alias) und Jahr NUMMERN_VON_JAHR..NUMMERN_BIS_JAHR drei
Prüfsummen: (a) `get_holidays`-Menge (inkl. Wochenenddaten — die öffentliche API bleibt unverändert),
(b) `is_trading_day` je Kalendertag, (c) alle vier Handelstagnummern + `offen` je Tag (`handelstag_nummern`).
Die Datei ist eine Prüfsummenliste, keine zweite Kalenderquelle.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys
from datetime import date, timedelta

WURZEL = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL))
from shared import exchange_holidays as eh  # noqa: E402

ZIEL = WURZEL / "scripts" / "fixtures" / "kalender_vor_v1c.json"


def h(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:24]


def aufnahme() -> dict:
    aus = {}
    for b in sorted(eh._EXCHANGE_FUNCTIONS):
        jahre = {}
        for j in range(eh.NUMMERN_VON_JAHR, eh.NUMMERN_BIS_JAHR + 1):
            tage = [date(j, 1, 1) + timedelta(days=i) for i in range((date(j + 1, 1, 1) - date(j, 1, 1)).days)]
            feiertage = ",".join(d.isoformat() for d in sorted(eh.get_holidays(b, j, j)))
            offen = "".join("1" if eh.is_trading_day(d, b) else "0" for d in tage)
            nummern = ";".join(",".join("" if x is None else str(x) for x in n) for n in eh.handelstag_nummern(tage, b))
            jahre[str(j)] = [h(feiertage), h(offen), h(nummern)]
        aus[b] = jahre
    return aus


def main() -> int:
    if "--schreiben" in sys.argv:
        if ZIEL.exists():
            print("FEHL Momentaufnahme existiert bereits — nur einmal aus dem Stand VOR dem Umbau erzeugen")
            return 1
        daten = {"schema": 1, "von": eh.NUMMERN_VON_JAHR, "bis": eh.NUMMERN_BIS_JAHR,
                 "felder": ["get_holidays", "is_trading_day", "handelstag_nummern"], "boersen": aufnahme()}
        ZIEL.write_text(json.dumps(daten, sort_keys=True, indent=0, separators=(",", ":")) + "\n", encoding="utf-8")
        print("geschrieben: %s (%d Börsen)" % (ZIEL.relative_to(WURZEL), len(daten["boersen"])))
        return 0
    soll = json.loads(ZIEL.read_text(encoding="utf-8"))["boersen"]
    ist = aufnahme()
    fehler = []
    for b in sorted(set(soll) | set(ist)):
        if b not in ist or b not in soll:
            fehler.append("%s: Börse %s" % (b, "fehlt" if b not in ist else "neu"))
            continue
        for j in sorted(set(soll[b]) | set(ist[b])):
            s, i = soll[b].get(j), ist[b].get(j)
            if s != i:
                teile = [f for f, a, c in zip(("get_holidays", "is_trading_day", "nummern"), s or [None] * 3, i or [None] * 3) if a != c]
                fehler.append("%s %s: %s" % (b, j, "/".join(teile)))
    for f in fehler[:30]:
        print("FEHL " + f)
    n = sum(len(v) for v in ist.values())
    print("kalender_momentaufnahme: %s (%d Börsen-Jahre, %d Abweichungen)" % ("BESTANDEN" if not fehler else "DURCHGEFALLEN", n, len(fehler)))
    if not fehler:
        print("PROBE-ENDE %d" % n)
    return 0 if not fehler else 1


if __name__ == "__main__":
    sys.exit(main())
