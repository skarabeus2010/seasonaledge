# -*- coding: utf-8 -*-
"""Prüft den Wächter, nicht den Code: baut die Fehler der alten Ticker-Zuordnung und der
nachgiebigen Börsenprüfung wieder ein und verlangt, dass verify_ticker_boerse.py ROT wird —
an der benannten Prüfung.

    py -3.14 scripts/verify_ticker_boerse_mutation.py

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

EH = "shared/exchange_holidays.py"
SY = "shared/symbols.py"
PROBE = "scripts/verify_ticker_boerse.py"

MUTATIONEN = [
    ("Unbekannter Ticker fällt wieder still auf NYSE",
     SY, '        raise ValueError(f"Kein Börsenkalender für unbekannten Ticker {ticker!r}")',
     '        return "NYSE"',
     "[Regel '^XYZ']"),
    ("Suffix-Tabelle fehlt (alter Stand: nur SYMBOLS-Einträge)",
     SY, "    for suffix, boerse in SUFFIX_ZU_BOERSE:\n        if t.endswith(suffix):\n            return boerse",
     "    pass",
     "[Regel 'NEU.DE']"),
    (".BR fehlt in der Suffix-Tabelle",
     SY, '(".AS", "EURONEXT"), (".BR", "EURONEXT"), (".LS", "EURONEXT"),',
     '(".AS", "EURONEXT"), (".LS", "EURONEXT"),',
     "[Regel 'NEU.BR']"),
    (".LS fehlt in der Suffix-Tabelle",
     SY, '(".AS", "EURONEXT"), (".BR", "EURONEXT"), (".LS", "EURONEXT"),',
     '(".AS", "EURONEXT"), (".BR", "EURONEXT"),',
     "[Regel 'NEU.LS']"),
    (".F nicht mehr XETRA",
     SY, '    (".DE", "XETRA"), (".F", "XETRA"),',
     '    (".DE", "XETRA"),',
     "[Regel 'NEU.F']"),
    ("SYMBOLS wieder nur in Originalschreibweise gesucht",
     SY, "    schluessel = _symbols_gross().get(t)",
     "    schluessel = ticker if ticker in SYMBOLS else None",
     "[Regel '^gdaxi']"),   # sap.de fängt die Suffix-Tabelle auf, ^gdaxi nicht
    ("Börse ohne Kalender wird still US",
     SY, "            if code is None or code not in HOLIDAY_TO_EXCHANGE:\n                raise ValueError(",
     "            if code is None or code not in HOLIDAY_TO_EXCHANGE:\n                return \"NYSE\"\n                raise ValueError(",
     "[Regel SYMBOLS-Börse ohne Kalender]"),
    ("USDT nicht mehr Krypto",
     SY, '    if t.endswith("-USD") or t.endswith("-USDT"):',
     '    if t.endswith("-USD"):',
     "[Regel 'NEU-USDT']"),
    ("ADR ohne Suffix nach Heimatbörse statt Listing",
     SY, '        return "NYSE"\n    for suffix, boerse in SUFFIX_ZU_BOERSE:',
     '        return HOLIDAY_TO_EXCHANGE.get(EXCHANGE_TO_HOLIDAY.get(SYMBOLS[schluessel].get("exchange"), "US"), "NYSE")\n    for suffix, boerse in SUFFIX_ZU_BOERSE:',
     "[Bestand"),
    ("is_trading_day prüft die Börse erst nach dem Wochenende",
     EH, '    exchange = boerse_normalisieren(exchange)\n    if exchange == "CRYPTO":',
     '    if d.weekday() >= 5 and exchange.upper() not in ("CRYPTO",):\n        return False\n    exchange = boerse_normalisieren(exchange)\n    if exchange == "CRYPTO":',
     "[Streng is_trading_day Samstag]"),
    ("get_holidays mit NYSE-Ersatz",
     EH, "    fn = _EXCHANGE_FUNCTIONS[boerse_normalisieren(exchange)]   # unbekannt → ValueError, kein NYSE-Ersatz",
     '    fn = _EXCHANGE_FUNCTIONS.get(exchange.upper(), _EXCHANGE_FUNCTIONS["NYSE"])',
     "[Streng get_holidays]"),
    ("is_holiday mit NYSE-Ersatz",
     EH, "    return d in _EXCHANGE_FUNCTIONS[boerse_normalisieren(exchange)](d.year)",
     '    return d in _EXCHANGE_FUNCTIONS.get(exchange.upper(), _EXCHANGE_FUNCTIONS["NYSE"])(d.year)',
     "[Streng is_holiday]"),
    ("letzte_session mit NYSE-Zeiten für FOREX",
     EH, '    if ex not in _SCHLUSSZEIT:   # früher still NYSE-Zeiten (Codex R4, A3)\n        raise ValueError(f"Keine Schlusszeit für {ex} hinterlegt")\n    tz_name, stunde, minute = _SCHLUSSZEIT[ex]',
     '    tz_name, stunde, minute = _SCHLUSSZEIT.get(ex, _SCHLUSSZEIT["NYSE"])',
     "[Streng letzte_session FOREX ohne Schlusszeit]"),
    # Die Mutation muss die Schutzabfrage selbst entfernen — hinter ihr war ein NYSE-Ersatz
    # wirkungslos (erster Entwurf, korrekt als „entwischt“ gemeldet).
    ("markt_offen mit NYSE-Öffnung für XETRA",
     EH, '    if ex not in _SCHLUSSZEIT or ex not in _OEFFNUNG:   # früher still NYSE-Zeiten\n        raise ValueError(f"Keine Handelszeiten für {ex} hinterlegt")\n    tz_name, s_h, s_m = _SCHLUSSZEIT[ex]\n    o_h, o_m = _OEFFNUNG[ex]',
     '    tz_name, s_h, s_m = _SCHLUSSZEIT[ex]\n    o_h, o_m = _OEFFNUNG.get(ex, _OEFFNUNG["NYSE"])',
     "[Streng markt_offen XETRA ohne Öffnungszeit]"),
    ("Zweite Zuordnung wieder vorhanden",
     EH, "# ── Gemeinsame Helfer",
     "def get_exchange_for_ticker(ticker):\n    return \"NYSE\"\n\n\n# ── Gemeinsame Helfer",
     "[Einzig keine zweite Zuordnung]"),
]

UNGUELTIG_ERWARTET = [
    ("Ausnahme statt Verhaltensänderung", SY,
     "def get_exchange_for_holidays(ticker: str) -> str:",
     "def get_exchange_for_holidays(ticker: str) -> str:\n    None.real"),
    ("Anker existiert nicht", SY, "diese Zeile gibt es nicht", "egal"),
]

# Originalbytes erst UNTER der gemeinsamen Sperre lesen (Codex P1b R1): sonst kann ein
# paralleler Lauf mutierte Bytes als Original übernehmen.
DATEIEN = (EH, SY)
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
