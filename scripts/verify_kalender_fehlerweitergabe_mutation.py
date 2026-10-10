# -*- coding: utf-8 -*-
"""Prüft den Wächter, nicht den Code: baut die alte, stille Fehlerbehandlung in Intraday und
Nightly wieder ein und verlangt, dass verify_kalender_fehlerweitergabe.py ROT wird —
an der benannten Prüfung.

    py -3.14 scripts/verify_kalender_fehlerweitergabe_mutation.py

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
from scripts.verify_twins_mutation import (LockBelegt, _atomar_schreiben,  # noqa: E402
                                           _exklusiver_lauf, python_probe)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

IR = "scripts/intraday_refresh.py"
NR = "scripts/nightly_refresh.py"
PROBE = "scripts/verify_kalender_fehlerweitergabe.py"

MUTATIONEN = [
    ("Intraday: Kalenderfehler fällt wieder unter die Yahoo-Toleranz",
     IR, "    if KALENDER_FEHLER:\n        # Ein Kalender-/Zuordnungsfehler ist kein Yahoo-Aussetzer",
     "    if False:\n        # Ein Kalender-/Zuordnungsfehler ist kein Yahoo-Aussetzer",
     "[Intraday Zuordnungsfehler → Exit 1]"),
    ("Intraday: Kalenderfehler wird nicht vermerkt",
     IR, "                KALENDER_FEHLER.append(ticker)\n",
     "",
     "[Intraday Zuordnungsfehler vermerkt]"),
    ("Intraday: Urzustand — TDOM/TDOY-Fehler still verschluckt",
     IR, "            except Exception as _e:\n                # Früher still `pass`",
     "            except Exception as _e:\n                continue_ok = True\n            if False:\n                # Früher still `pass`",
     "[Intraday Zuordnungsfehler"),
    ("Nightly: nicht prüfbarer Ticker wird nicht vermerkt",
     NR, "                health_ungeprueft.add(ticker)\n",
     "",
     "[Nightly unbekannter Ticker ungeprüft]"),
    ("Nightly: Phase gilt trotz ungeprüftem Ticker als gelungen",
     NR, '            gescheitert.append(f"Health-Check ({len(health_ungeprueft)} Ticker nicht prüfbar)")',
     "            pass",
     "[Nightly Phase gescheitert]"),
    ("Nightly: meldet wieder „Alle Ticker vollständig“",
     NR, "        elif not health_ungeprueft:\n            print(\"Health-Check: Alle Ticker vollständig ✓\")",
     "        else:\n            print(\"Health-Check: Alle Ticker vollständig ✓\")",
     "[Nightly nicht „vollständig“]"),
    # Codex Paket 3, Runde 2 — entkam dem ersten Wächter.
    ("Nightly-Hauptlauf: Health-Check-Fehler erreicht den Exit nicht",
     NR, '    _FEHLGESCHLAGEN.extend(_hc["gescheitert"])',
     "    pass",
     "[Hauptlauf Zuordnungsfehler → Exit 1]"),
    ("Nightly-Hauptlauf: refresh_log zählt wieder nur Lücken",
     NR, '            "tickers_success": tickers_erfolgreich(tickers, missing_details, health_ungeprueft),',
     '            "tickers_success": len(tickers) - len(missing_details),',
     "[Hauptlauf refresh_log zählt ihn nicht als Erfolg]"),
    ("Nightly: Abbruch vor der Schleife lässt alle als geprüft gelten",
     NR, "        health_ungeprueft.update(tickers)\n",
     "",
     "[Nightly Abbruch: alle ungeprüft]"),
    # „Teilnummern nach Fehler bleiben stehen“ entfällt seit P2: alle Nummern entstehen in einem
    # Aufruf (tdom_tdoy_fuer_ticker), halb berechnete gibt es nicht mehr. Die Prüfung bleibt im Wächter.
    ("Nightly: Erfolgszählung wie früher ohne ungeprüfte",
     NR, "    return len(set(tickers) - set(missing_details) - set(ungeprueft))",
     "    return len(tickers) - len(missing_details)",
     "[Nightly Erfolgszählung ohne ungeprüfte]"),
]

UNGUELTIG_ERWARTET = [
    ("Ausnahme statt Verhaltensänderung", NR,
     "def health_check(tickers: list[str]) -> dict:",
     "def health_check(tickers: list[str]) -> dict:\n    None.real"),
    ("Anker existiert nicht", NR, "diese Zeile gibt es nicht", "egal"),
]

# Originalbytes erst UNTER der gemeinsamen Sperre lesen (Codex P1b R1): sonst kann ein
# paralleler Lauf mutierte Bytes als Original übernehmen.
DATEIEN = (IR, NR)
ROH: dict = {}


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


def _main() -> int:
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


def main() -> int:
    try:
        with _exklusiver_lauf():
            ROH.update({d: io.open(d, "rb").read() for d in DATEIEN})
            return _main()
    except LockBelegt as e:
        print(f"ABBRUCH: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
