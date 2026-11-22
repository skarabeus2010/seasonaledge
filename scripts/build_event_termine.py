"""Termine für /event-chart: erzeugt landing/data/event_termine.json aus den gemeinsamen Kalendermodulen.

Aufruf:  py -3.14 scripts/build_event_termine.py            → schreibt die Datei
         py -3.14 scripts/build_event_termine.py --pruefen  → vergleicht nur (Exit 1 bei Abweichung)

Die Datei ist committet (kein Cron-Ausgang): sie ändert sich nur, wenn sich eine Quelle hier ändert. Das Prüfdatum
ist fest, damit der Vergleich im Gate reproduzierbar ist (produkttermine verlangt eines).

Quellen je Terminart:
  OPEX/TW  bis 2019 nach Regel (3. Freitag, bei NYSE-Schließung der Handelstag davor), ab 2020 Cboe-Katalog
           (shared/produkttermine.py); Großer Verfall = März/Juni/September/Dezember
  Q        letzter NYSE-Handelstag im Quartal (shared/sitzungen.py)
  VIX      Cboe-Katalog ab Kontrakt 2015-09 (davor nicht belegt)
  FOMC     shared/fed_dates.FOMC_MEETING_DATES (federalreserve.gov), Strategietreffen ausgenommen
  FOMCX    außerplanmäßige Sitzungen mit Zinsbeschluss (federalreserve.gov)
  MIN      veröffentlichte Protokolle laut federalreserve.gov (abgeglichen 2026-11-19, PROTOKOLLE_ALT +
           shared/central_banks.FED_MINUTES_DATES); künftige: Sitzung + 21 Tage, nächster NYSE-Handelstag
  JOBS     Arbeitsmarktbericht nach BLS-Regel, Ausnahmen 2013 und 2025 (Shutdown)
  EZB      shared/central_banks.ECB_MEETING_DATES (ab 2015)
"""
from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL))

from shared import produkttermine as pt, sitzungen as s  # noqa: E402
from shared.central_banks import ECB_MEETING_DATES, FED_MINUTES_DATES  # noqa: E402
from shared.fed_dates import FOMC_MEETING_DATES, FOMC_STRATEGIE_TREFFEN  # noqa: E402

ZIEL = WURZEL / "landing" / "data" / "event_termine.json"
PRUEFDATUM = "2026-11-22"
VON, BIS = 2000, 2027

UNGEPLANT = {date(2001, 1, 3), date(2001, 4, 18), date(2001, 9, 17), date(2007, 8, 17), date(2008, 1, 22),
             date(2008, 3, 11), date(2008, 10, 8), date(2020, 3, 3), date(2020, 3, 15)}

# Veröffentlichte Protokolle 2000–2021 (federalreserve.gov, FOMC-Historienseiten, abgeglichen 2026-11-19).
# 2020-04-08 = Protokoll der außerplanmäßigen Sitzungen vom 03. und 15.03.2020.
PROTOKOLLE_ALT = {
    2000: "0323 0518 0629 0824 1005 1116 1221", 2001: "0201 0322 0517 0628 0823 1004 1108 1213",
    2002: "0131 0321 0509 0627 0815 0926 1107 1212", 2003: "0130 0320 0508 0626 0814 0918 1030 1211",
    2004: "0129 0318 0506 0701 0812 0923 1111 1216", 2005: "0104 0223 0412 0524 0721 0830 1011 1122",
    2006: "0103 0221 0418 0531 0720 0829 1011 1115", 2007: "0103 0221 0411 0530 0719 0828 1009 1120",
    2008: "0102 0220 0408 0521 0716 0826 1007 1119", 2009: "0106 0218 0408 0520 0715 0902 1014 1124",
    2010: "0106 0217 0406 0519 0714 0831 1012 1123", 2011: "0104 0216 0405 0518 0712 0830 1012 1122",
    2012: "0103 0215 0403 0516 0711 0822 1004 1114", 2013: "0103 0220 0410 0522 0710 0821 1009 1120",
    2014: "0108 0219 0409 0521 0709 0820 1008 1119", 2015: "0107 0218 0408 0520 0708 0819 1008 1118",
    2016: "0106 0217 0406 0518 0706 0817 1012 1123", 2017: "0104 0222 0405 0524 0705 0816 1011 1122",
    2018: "0103 0221 0411 0523 0705 0822 1017 1129", 2019: "0109 0220 0410 0522 0710 0821 1009 1120",
    2020: "0103 0219 0408 0520 0701 0819 1007 1125", 2021: "0106 0217 0407 0519 0707 0818 1013 1124",
}

# BLS: verschobene Termine (Shutdown 2013 und 2025); der Bericht für Oktober 2025 entfiel
JOBS_ERSATZ = {date(2013, 10, 4): date(2013, 10, 22), date(2013, 11, 1): date(2013, 11, 8),
               date(2025, 10, 3): date(2025, 11, 20), date(2025, 12, 5): date(2025, 12, 16)}
JOBS_ENTFALLEN = {date(2025, 11, 7)}


def _d(x) -> date:
    return x if isinstance(x, date) else date.fromisoformat(str(x))


def termine() -> list[list[str]]:
    ev: set[tuple[date, str]] = set()

    for j in range(VON, 2020):
        for m in range(1, 13):
            ev.add((_d(pt.opex_regel(j, m)["verfallstermin"]), "TW" if m in (3, 6, 9, 12) else "OPEX"))
    for e in pt.produkttermine("2020-01", f"{BIS}-12", "opex", pruefdatum=PRUEFDATUM):
        ev.add((_d(e["verfallstermin"]), "TW" if e["triple_witching"] else "OPEX"))

    for e in pt.produkttermine("2015-09", f"{BIS + 1}-12", "vix", pruefdatum=PRUEFDATUM):
        ev.add((_d(e["settlement"]), "VIX"))

    for j in range(VON, BIS + 1):
        for m in (3, 6, 9, 12):
            ende = date(j, m + 1, 1) - timedelta(1) if m < 12 else date(j, 12, 31)
            ev.add((_d(s.vorherige(ende, "NYSE", einschliesslich=True)), "Q"))

    strategie = {date(*x) if not isinstance(x, date) else x for x in FOMC_STRATEGIE_TREFFEN}
    fomc = sorted({date(*x) for x in FOMC_MEETING_DATES} - strategie)
    for f in fomc:
        ev.add((f, "FOMCX" if f in UNGEPLANT else "FOMC"))
    for f in UNGEPLANT:
        ev.add((f, "FOMCX"))

    protokolle = {date(j, int(t[:2]), int(t[2:])) for j, ts in PROTOKOLLE_ALT.items() for t in ts.split()}
    protokolle |= {date(*x) for x in FED_MINUTES_DATES}
    letzte_sitzung = max(f for f in fomc if f < max(protokolle))
    for f in fomc:
        if f > letzte_sitzung and f not in UNGEPLANT:
            protokolle.add(_d(s.naechste(f + timedelta(21), "NYSE", einschliesslich=True)))
    for p in protokolle:
        ev.add((p, "MIN"))

    for j in range(VON, BIS + 1):
        for m in range(1, 13):
            zw = date(j, m, 12)
            samstag = zw + timedelta((5 - zw.weekday()) % 7)
            r = samstag + timedelta(20)
            if r.month == 1 and r.day <= 3:
                r += timedelta(7)
            if r.month == 7 and r.day in (3, 4):
                r -= timedelta(1)
            if r in JOBS_ENTFALLEN:
                continue
            ev.add((JOBS_ERSATZ.get(r, r), "JOBS"))

    for y, m, t in ECB_MEETING_DATES:
        ev.add((date(y, m, t), "EZB"))

    return [[d.isoformat(), c] for d, c in sorted(ev) if VON <= d.year <= BIS]


def inhalt() -> str:
    daten = {
        "schema": 1,
        "zweck": "Termine für /event-chart, erzeugt von scripts/build_event_termine.py — nicht von Hand ändern.",
        "pruefdatum": PRUEFDATUM,
        "termine": termine(),
    }
    return json.dumps(daten, ensure_ascii=False, separators=(",", ":")) + "\n"


def main() -> int:
    neu = inhalt()
    if "--pruefen" in sys.argv:
        alt = ZIEL.read_text(encoding="utf-8") if ZIEL.exists() else ""
        if alt != neu:
            sys.stderr.write("event_termine.json weicht vom Erzeuger ab — scripts/build_event_termine.py ausführen\n")
            return 1
        return 0
    ZIEL.write_text(neu, encoding="utf-8", newline="\n")
    n = json.loads(neu)["termine"]
    zaehl: dict[str, int] = {}
    for _, c in n:
        zaehl[c] = zaehl.get(c, 0) + 1
    sys.stdout.write(f"{len(n)} Termine {zaehl}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
