# -*- coding: utf-8 -*-
"""Prüft den Wächter, nicht den Code: baut die am 2026-10-10 behobenen Kalenderfehler
wieder ein und verlangt, dass verify_kalender_sollfaelle.py ROT wird — und zwar an der
benannten Prüfung.

    py -3.14 scripts/verify_kalender_sollfaelle_mutation.py

Beweisregeln wie in den übrigen Mutationstests: Endmarker `PROBE-ENDE` muss erreicht sein ·
jede Mutation BENENNT die Prüfung, die sie reißen muss · eine Ausnahme gilt nie als
Nachweis, auch eine eingefangene (`[Ausnahme]`) nicht · ein Anker, der nicht genau einmal
trifft, macht die Mutation ungültig · `UNGUELTIG_ERWARTET` prüft das Urteil dieses Tests.
"""
from __future__ import annotations

import io
import os
import pathlib
import re
import sys

# Atomares Schreiben mit Wiederholung — IMPORTIERT, nicht kopiert (deterministisch, v65.1/v66.5).
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from scripts.verify_twins_mutation import _atomar_schreiben, python_probe  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

EH = "shared/exchange_holidays.py"
NY = "shared/nyse_holidays.py"
PROBE = "scripts/verify_kalender_sollfaelle.py"

MUTATIONEN = [
    ("LSE: Neujahrsersatz wieder nur bei Sonntag",
     EH, "    holidays.append(neujahr + timedelta(days=(7 - neujahr.weekday()) % 7) if neujahr.weekday() >= 5 else neujahr)",
     "    holidays.append(neujahr + timedelta(days=1) if neujahr.weekday() == 6 else neujahr)",
     "[LSE 2022-01-03]"),
    ("LSE: Boxing Day auf Sonntag ohne Ersatz-Dienstag",
     EH, "        holidays.append(date(year, 12, 28))  # weil der Montag schon Weihnachts-Ersatz ist",
     "        pass",
     "[LSE 2021-12-28]"),
    ("LSE: Royal Wedding 2011 fehlt",
     EH, "        holidays.append(date(2011, 4, 29))  # Royal Wedding",
     "        pass  # Royal Wedding",
     "[LSE 2011-04-29]"),
    ("LSE: Golden-Jubilee-Zusatztag 2002 fehlt",
     EH, "        holidays.append(date(2002, 6, 3))  # Golden Jubilee",
     "        pass  # Golden Jubilee",
     "[LSE 2002-06-03]"),
    ("TSE: Olympia-Verlegung 2021 fehlt",
     EH, "    2021: (date(2021, 7, 22), date(2021, 7, 23), date(2021, 8, 8)),",
     "",
     "[TSE 2021-07-22]"),
    ("TSE: Meerestag wieder immer 3. Montag",
     EH, "        if year >= 2003:\n            national.add(_nth_weekday(year, 7, 0, 3))",
     "        if year >= 1996:\n            national.add(_nth_weekday(year, 7, 0, 3))",
     "[TSE 2000-07-17]"),
    ("TSE: Ersatzregel vor 2007 wie danach",
     EH, "            if year >= 2007:\n                while sub in national:",
     "            if year >= 1973:\n                while sub in national:",
     "[TSE 2003-05-06]"),
    ("TSE: Kaisergeburtstag 2019 wieder vorhanden",
     EH, "    elif 1989 <= year <= 2018:",
     "    elif 1989 <= year <= 2019:",
     "[TSE 2019-12-23]"),
    # Ergänzt nach Codex-Review Paket 1 (fünf Mutationen entkamen dem ersten Wächter).
    ("TSE: Brückentag nur noch im Thronwechseljahr",
     EH, "        if (h + timedelta(days=2)) in national and mid not in national and mid.weekday() < 5:",
     "        if year == 2019 and (h + timedelta(days=2)) in national and mid not in national and mid.weekday() < 5:",
     "[TSE 2015-09-22]"),
    ("TSE: Ersatztag schon vor 1973",
     EH, "        if h.weekday() == 6 and year >= 1973:",
     "        if h.weekday() == 6:",
     "[TSE 1971-10-11]"),
    ("TSE: Meerestag schon vor 1996",
     EH, "        elif year >= 1996:\n            national.add(date(year, 7, 20))",
     "        elif year >= 1950:\n            national.add(date(year, 7, 20))",
     "[TSE 1995-07-20]"),
    ("TSE: Seijin no Hi immer am 2. Montag",
     EH, "    national.add(_nth_weekday(year, 1, 0, 2) if year >= 2000 else date(year, 1, 15))",
     "    national.add(_nth_weekday(year, 1, 0, 2))",
     "[TSE 1999-01-11]"),
    ("TSE: Taiiku no Hi auch historisch am 2. Montag",
     EH, "        elif year >= 1966:\n            national.add(date(year, 10, 10))",
     "        elif year >= 1966:\n            national.add(_nth_weekday(year, 10, 0, 2))",
     "[TSE 1997-10-13]"),
    ("TSE: Systemausfall 2020-10-01 fehlt",
     EH, "    2020: (date(2020, 10, 1),),",
     "",
     "[TSE 2020-10-01]"),
    ("KRX: 2022-01-03 wieder als Feiertag (aus Kurslücke)",
     EH, "    2022: [(1,31),(2,1),(2,2),(3,1),(3,9),(5,5),(6,1),",
     "    2022: [(1,3),(1,31),(2,1),(2,2),(3,1),(3,9),(5,5),(6,1),",
     "[KRX 2022-01-03]"),
    ("HKEX: Neujahr 2016 fehlt",
     EH, "    2016: [(1,1),(2,8),(2,9),(2,10),(3,25),",
     "    2016: [(2,8),(2,9),(2,10),(3,25),",
     "[HKEX 2016-01-01]"),
    ("NYSE: Hurrikan Gloria fehlt",
     NY, "    date(1985, 9, 27),   # Hurrikan Gloria",
     "    # Hurrikan Gloria",
     "[NYSE 1985-09-27]"),
    ("XETRA: 3. Oktober 2012 als geschlossen eingetragen (der Fehlschluss aus der Kurslücke)",
     EH, "    date(2014, 10, 3),    # Handelskalender 2014",
     "    date(2012, 10, 3),\n    date(2014, 10, 3),    # Handelskalender 2014",
     "[XETRA 2012-10-03]"),
]

UNGUELTIG_ERWARTET = [
    # Ändert kein Verhalten, sondern lässt nur jeden Aufruf werfen.
    ("Ausnahme statt Verhaltensänderung", EH,
     "def is_trading_day(d: date, exchange: str = \"NYSE\") -> bool:",
     "def is_trading_day(d: date, exchange: str = \"NYSE\") -> bool:\n    None.real"),
    # Anker trifft nicht → ungültig, nicht gefangen.
    ("Anker existiert nicht", EH, "diese Zeile gibt es nicht", "egal"),
]

ROH = {d: io.open(d, "rb").read() for d in (EH, NY)}


def anker(datei: str, text: str) -> bytes:
    roh = ROH[datei]
    if roh.count(b"\r\n") > roh.count(b"\n") // 2:
        text = text.replace("\r\n", "\n").replace("\n", "\r\n")
    return text.encode("utf-8")


def lauf() -> tuple[int, str]:
    # Eigener, leerer Bytecode-Cache je Lauf — siehe python_probe (sonst prüft eine
    # Mutation gleicher Länge die .pyc ihrer Vorgängerin; beobachtet 2026-10-10).
    r = python_probe([PROBE], capture_output=True, text=True, encoding="utf-8",
                     env={**os.environ, "PYTHONUTF8": "1"})
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def bewerte(datei, alt, neu, erwartet=None):
    a = anker(datei, alt)
    n = ROH[datei].count(a)
    if n != 1:
        return "ungueltig", f"Anker {n}x gefunden, erwartet 1x"
    _atomar_schreiben(pathlib.Path(datei), ROH[datei].replace(a, anker(datei, neu), 1))
    try:
        rc_, aus = lauf()
    finally:
        _atomar_schreiben(pathlib.Path(datei), ROH[datei])
    if rc_ == 0:
        return "entwischt", "Probe blieb grün"
    if "PROBE-ENDE" not in aus:
        return "ungueltig", "die Probe brach ab statt durchzulaufen"
    zeilen = [z for z in aus.splitlines() if "FEHL " in z]
    if any("[Ausnahme]" in z for z in zeilen):
        return "ungueltig", "Produktivcode warf"
    if not zeilen:
        return "ungueltig", "rot ohne inhaltliche Prüfung"
    if erwartet and not any(erwartet in z for z in zeilen):
        return "ungueltig", f"erwartete Prüfung {erwartet} blieb grün; rot war: {zeilen[0].strip()[:50]}"
    return "gefangen", zeilen[0].strip()[:70]


def main() -> int:
    rc, ausgabe = lauf()
    if rc != 0:
        print("ABBRUCH: die Probe ist schon ohne Mutation rot.")
        print(ausgabe[-1500:])
        return 1
    m = re.search(r"PROBE-ENDE (\d+) Pruefungen", ausgabe)
    if not m:
        print("ABBRUCH: die Probe meldet keinen Endmarker.")
        return 1
    print(f"Grundlinie: Probe ohne Mutation grün, {m.group(1)} Prüfungen\n")

    gefangen, probleme, urteil_ok = 0, [], True
    try:
        for name, datei, alt, neu, erwartet in MUTATIONEN:
            art, warum = bewerte(datei, alt, neu, erwartet)
            if art == "gefangen":
                print(f"  gefangen       {name}")
                gefangen += 1
            else:
                print(f"  {art.upper():12s}   {name}  ({warum})")
                probleme.append(f"{name} [{art}: {warum}]")
        print("  -- Gegenprobe am Urteil dieses Tests --")
        for name, datei, alt, neu in UNGUELTIG_ERWARTET:
            art, warum = bewerte(datei, alt, neu)
            if art == "ungueltig":
                print(f"  richtig verworfen  {name}  ({warum})")
            else:
                print(f"  FALSCH EINGEORDNET {name}  -> {art}")
                probleme.append(f"{name} [als {art} verbucht]")
                urteil_ok = False
    finally:
        for d, b in ROH.items():
            _atomar_schreiben(pathlib.Path(d), b)
    for d, b in ROH.items():
        assert io.open(d, "rb").read() == b, "WIEDERHERSTELLUNG FEHLGESCHLAGEN: " + d
    rc_nach, _ = lauf()
    print()
    print("wiederhergestellt: Probe läuft wieder grün" if rc_nach == 0
          else "WARNUNG: Probe nach der Wiederherstellung ROT!")
    print(f"{gefangen} von {len(MUTATIONEN)} Mutationen gefangen")
    for p in probleme:
        print("  " + p)
    return 0 if (gefangen == len(MUTATIONEN) and urteil_ok and rc_nach == 0) else 1


if __name__ == "__main__":
    sys.exit(main())
