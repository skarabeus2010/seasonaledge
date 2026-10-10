# -*- coding: utf-8 -*-
"""Prüft den Wächter, nicht den Code: baut Fehler in die erzeugte landing/js/boersenkalender.js
ein (und einmal in eine Seite) und verlangt, dass verify_boersenkalender_js.py ROT wird — an der
benannten FACHLICHEN Prüfung, nicht nur am Aktualitätsvergleich.

    py -3.14 scripts/verify_boersenkalender_js_mutation.py

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

BK = "landing/js/boersenkalender.js"
DB = "landing/pages/dashboard.html"
EN = "landing/build_en.py"
PROBE = "scripts/verify_boersenkalender_js.py"

MUTATIONEN = [
    ("Wochentag um einen Tag verschoben",
     BK, "  function wochentag(j, m, t) { return ((tagNr(j, m, t) % 7) + 7 + 3) % 7; }",
     "  function wochentag(j, m, t) { return ((tagNr(j, m, t) % 7) + 7 + 4) % 7; }",
     "[Python istHandelstag NYSE]"),
    ("Wochentag über lokale Zeit (der alte holidays.js-Weg)",
     BK, "  function wochentag(j, m, t) { return ((tagNr(j, m, t) % 7) + 7 + 3) % 7; }",
     "  function wochentag(j, m, t) { return (new Date(j, m - 1, t).getDay() + 6) % 7; }",
     "[Zeitzone Pacific/Apia gleich UTC]"),
    ("Rückwärtszahl im Monat um eins verschoben",
     BK, "tdom_rev: -(monatSumme[m] - tdom + 1),",
     "tdom_rev: -(monatSumme[m] - tdom),",
     "[NumPy nummern NYSE]"),
    ("Krypto nicht mehr täglich",
     BK, "    if (DATEN.woche[b] === 'taeglich') return true;",
     "    if (DATEN.woche[b] === 'nie') return true;",
     "[Python istHandelstag CRYPTO]"),
    ("Nächster Handelstag gibt nach acht Tagen auf (der alte 10-Tage-Fehler)",
     BK, "      for (;;) {\n        if (offen(b, j, m, t)) return iso(j, m, t);",
     "      for (var k = 0; ; k++) {\n        if (k === 8) return datum;\n        if (offen(b, j, m, t)) return iso(j, m, t);",
     "[API naechsterHandelstag TSE Golden Week]"),
    ("Nächster Handelstag schließt das Datum selbst aus",
     BK, "      var j = d[0], m = d[1], t = d[2];\n      for (;;) {",
     "      var j = d[0], m = d[1], t = d[2] + 1;\n      if (t > monatsTage(j, m)) { t = 1; m++; }\n      if (m > 12) { m = 1; j++; }\n      for (;;) {",
     "[API naechsterHandelstag ab einschließlich]"),
    ("Leere Liste prüft die Börse nicht",
     BK, "      var b = boerseNormalisieren(boerse);\n      if (!Array.isArray(daten)) fehler('Daten müssen eine Liste sein');",
     "      if (Array.isArray(daten) && !daten.length) return [];\n      var b = boerseNormalisieren(boerse);\n      if (!Array.isArray(daten)) fehler('Daten müssen eine Liste sein');",
     "[Validierung leere Liste prüft Börse]"),
    ("Unbekannter Index fällt auf NYSE",
     BK, "      if (t.charAt(0) === '^' || t.indexOf('.') >= 0 || t.indexOf('=') >= 0) fehler('Kein Börsenkalender für unbekannten Ticker ' + ticker);",
     "",
     "[Ticker unbekannter Index wirft]"),
    ("Status nur noch der Standardwert",
     BK, "      for (var i = 0; i < s[1].length; i++) if (s[1][i][0] <= j && j <= s[1][i][1]) return s[1][i][2];",
     "",
     "[Status NYSE 1960 ungeprueft]"),
    # Codex P1b R1: drei Lücken des ersten Wächters.
    ("Datenende ohne Grenze: nächster Handelstag läuft über 2100 hinaus",
     BK, "        if (j > DATEN.bis) fehler('Kein Handelstag bis zum Datenende ' + DATEN.bis + ' (ab ' + datum + ')');",
     "        if (j > DATEN.bis + 1) fehler('Kein Handelstag bis zum Datenende ' + DATEN.bis + ' (ab ' + datum + ')');\n        if (j > DATEN.bis) return iso(j, m, t);",
     "[API naechsterHandelstag Datenende wirft]"),
    ("Statusgrenze NYSE um ein Jahr verschoben",
     BK, '"NYSE":["annahme",[[1885,1970,"ungeprueft"],[1971,2028,"belegt"]]]',
     '"NYSE":["annahme",[[1885,1970,"ungeprueft"],[1971,2029,"belegt"]]]',
     "[Status NYSE 2028 belegt, 2029 Annahme]"),
    ("Der EN-Generator bindet das Bundle ein",
     EN, '  <script type="application/ld+json">{jd(webpage)}</script>',
     '  <script src="/landing/js/boersenkalender.js"></script>\n  <script type="application/ld+json">{jd(webpage)}</script>',
     "[Isolation keine Seite nutzt das Bundle]"),
    ("Eine Seite bindet das Bundle vor der Umschaltung ein",
     DB, "</head>",
     "<script src=\"/landing/js/boersenkalender.js\"></script>\n</head>",
     "[Isolation keine Seite nutzt das Bundle]"),
]

UNGUELTIG_ERWARTET = [
    ("Ausnahme statt Verhaltensänderung", BK,
     "  var DATEN = ",
     "  null.x;\n  var DATEN = "),
    ("Anker existiert nicht", BK, "diese Zeile gibt es nicht", "egal"),
    # Codex P1b R2: Absturz an einer Stelle, an der ein FEHLER erwartet ist — darf nicht als gefangen zählen.
    ("Absturz statt Datenende-Fehler", BK,
     "        if (j > DATEN.bis) fehler('Kein Handelstag bis zum Datenende ' + DATEN.bis + ' (ab ' + datum + ')');",
     "        if (j > DATEN.bis) null.x;"),
    # Codex P1b R2: Absturz mit gefälschtem Meldungspräfix — die Klasse entscheidet, nicht der Text.
    ("Absturz mit gefälschtem Präfix", BK,
     "        if (offen(b, j, m, t)) return iso(j, m, t);",
     "        if (j === 2019 && m === 4 && t === 28) throw new TypeError('boersenkalender: getarnt');\n        if (offen(b, j, m, t)) return iso(j, m, t);"),
    # Codex P1b R3: Absturz nur in einer Zone (Pacific/Apia, Offset −780) — muss ebenso ungültig sein.
    ("Absturz nur unter Pacific/Apia", BK,
     "        if (offen(b, j, m, t)) return iso(j, m, t);",
     "        if (new Date(2026, 0, 15).getTimezoneOffset() === -780 && j === 2019 && m === 4 && t === 28) throw new TypeError('boersenkalender: getarnt');\n        if (offen(b, j, m, t)) return iso(j, m, t);"),
    # Ein Absturz mitten im Golden-Week-Pfad ist kein fachlicher Nachweis (Codex P1b R1).
    ("Absturz im nächsten-Handelstag-Pfad", BK,
     "        if (offen(b, j, m, t)) return iso(j, m, t);",
     "        if (j === 2019 && m === 4 && t === 28) null.x;\n        if (offen(b, j, m, t)) return iso(j, m, t);"),
]

# Originalbytes erst UNTER der gemeinsamen Sperre lesen (Codex P1b R1): sonst kann ein
# paralleler Lauf mutierte Bytes als Original übernehmen.
DATEIEN = (BK, DB, EN)
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
