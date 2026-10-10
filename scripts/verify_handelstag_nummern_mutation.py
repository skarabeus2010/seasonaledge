# -*- coding: utf-8 -*-
"""Prüft den Wächter, nicht den Code: baut typische Zählfehler in handelstag_nummern ein
und verlangt, dass verify_handelstag_nummern.py ROT wird — an der benannten Prüfung.

    py -3.14 scripts/verify_handelstag_nummern_mutation.py

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
PROBE = "scripts/verify_handelstag_nummern.py"

MUTATIONEN = [
    ("Rückwärtszahl um eins verschoben",
     EH, "            tab[d] = Nummer(tdom, tdoy, -(monat_summe[d.month] - tdom + 1), -(jahr_summe - tdoy + 1), True)",
     "            tab[d] = Nummer(tdom, tdoy, -(monat_summe[d.month] - tdom), -(jahr_summe - tdoy + 1), True)",
     "[Arithmetik"),
    ("Geschlossener Tag bekommt eine Rückwärtszahl",
     EH, "            tab[d] = Nummer(tdom, tdoy, None, None, False)",
     "            tab[d] = Nummer(tdom, tdoy, 0, 0, False)",
     "[Vertrag geschlossen ohne Rückwärtszahl]"),
    ("Geschlossener Tag zählt bei 0 statt beim Vortag",
     EH, "            tab[d] = Nummer(tdom, tdoy, None, None, False)",
     "            tab[d] = Nummer(0, 0, None, None, False)",
     "[Vertrag geschlossen = Vortag]"),
    ("TDOM wird beim Monatswechsel nicht zurückgesetzt",
     EH, "            monat, tdom = d.month, 0",
     "            monat = d.month",
     "[Arithmetik"),
    ("Cache-Schlüssel ohne Börse",
     EH, "    schluessel = (exchange, jahr)",
     "    schluessel = jahr",
     "[Vertrag Cache je Börse getrennt]"),
    ("datetime wird als Datum angenommen",
     EH, "    if type(x) is date:\n        return x",
     "    if isinstance(x, date):\n        return x if type(x) is date else x.date()",
     "[Vertrag datetime abgelehnt]"),
    ("Leere Eingabe prüft die Börse nicht",
     EH, "    e = boerse_normalisieren(exchange)\n    tage = [_als_datum(x) for x in daten]",
     "    if not daten:\n        return []\n    e = boerse_normalisieren(exchange)\n    tage = [_als_datum(x) for x in daten]",
     "[Vertrag unbekannte Börse bei leerer Eingabe]"),
    ("Rechenbereich wird nicht geprüft",
     EH, "        if not NUMMERN_VON_JAHR <= d.year <= NUMMERN_BIS_JAHR:",
     "        if False:",
     "[Vertrag Jahr außerhalb]"),
    ("NASDAQ-Alias zeigt auf die falsche Börse",
     EH, '_ALIAS_BOERSE = {"NASDAQ": "NYSE"}',
     '_ALIAS_BOERSE = {"NASDAQ": "LSE"}',
     "[Vertrag NASDAQ = NYSE"),
    ("XETRA 2001 als belegt ausgewiesen",
     EH, '    "XETRA":     ("annahme",    [(1885, 2000, "ungeprueft"), (2002, 2026, "belegt")]),',
     '    "XETRA":     ("annahme",    [(1885, 2000, "ungeprueft"), (2001, 2026, "belegt")]),',
     "[Status XETRA 2001"),
    # Codex Paket 2, Befund 3: blieb im ersten Wächter grün.
    ("XETRA bis 2100 als belegt ausgewiesen",
     EH, '    "XETRA":     ("annahme",    [(1885, 2000, "ungeprueft"), (2002, 2026, "belegt")]),',
     '    "XETRA":     ("annahme",    [(1885, 2000, "ungeprueft"), (2002, 2100, "belegt")]),',
     "[Status XETRA 1885–2100]"),
    # Codex Paket 2, Befund 1: Vergangenheit vor 1950 als Annahme.
    ("NYSE vor 1950 als Annahme statt ungeprüft",
     EH, '    "NYSE":      ("annahme",    [(1885, 1970, "ungeprueft"), (1971, 2028, "belegt")]),',
     '    "NYSE":      ("annahme",    [(1950, 1970, "ungeprueft"), (1971, 2028, "belegt")]),',
     "[Status NYSE 1885–2100]"),
    # Codex Paket 2, Befund 2: Stichproben als vollständiger Beleg.
    ("EURONEXT 2018–2026 als belegt ausgewiesen",
     EH, '    "EURONEXT":  ("annahme",    [(1885, 1999, "ungeprueft")]),',
     '    "EURONEXT":  ("annahme",    [(1885, 1999, "ungeprueft"), (2018, 2026, "belegt")]),',
     "[Status EURONEXT 1885–2100]"),
    ("Basisformat ohne Bindestriche wird angenommen",
     EH, '        if not _ISO_DATUM.fullmatch(x):',
     '        if not (_ISO_DATUM.fullmatch(x) or x.isdigit()):',
     "[Vertrag Basisformat"),
    ("Eine Börse wieder per Kurszeilen gezählt: Feiertage fehlen",
     EH, "    offen = {d: is_trading_day(d, exchange) for d in tage}",
     "    offen = {d: d.weekday() < 5 or exchange == \"CRYPTO\" for d in tage}",
     "[Sollkalender"),
]

UNGUELTIG_ERWARTET = [
    ("Ausnahme statt Verhaltensänderung", EH,
     "def handelstag_nummern(daten, exchange: str) -> list[Nummer]:",
     "def handelstag_nummern(daten, exchange: str) -> list[Nummer]:\n    None.real"),
    ("Anker existiert nicht", EH, "diese Zeile gibt es nicht", "egal"),
]

ROH = {d: io.open(d, "rb").read() for d in (EH,)}


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
