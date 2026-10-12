# -*- coding: utf-8 -*-
"""Prüft den Wächter der Sitzungshelfer (scripts/verify_sitzungen.py): baut Fehler in Python-Helfer, JS-Zwilling und
Generator ein und verlangt Rot an der benannten Prüfung.

    py -3.14 scripts/verify_sitzungen_mutation.py

Nutzt die isolierte Mechanik von scripts/verify_boersenereignisse_mutation.py (Temp-Kopie, Bundle bei JS-/Generator-
Mutationen in der Kopie neu erzeugt, frischer Bytecodepfad, Projektbaum-Hash vor = nach, Gegenproben). Ein Absturz oder
eine abgefangene Ausnahme zählt nicht als gefangen.
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from scripts import verify_boersenereignisse_mutation as M  # noqa: E402

SZ = "shared/sitzungen.py"
API = "scripts/boersenkalender/api.js"
GEN = "scripts/build_boersenkalender_js.py"

M.WAECHTER = "verify_sitzungen"
M.MUTATIONEN = [
    ("einschließlich/strikt vertauscht", [(SZ, "    if not einschliesslich:\n        d = _schritt(d, richtung)\n",
                                          "    if einschliesslich:\n        d = _schritt(d, richtung)\n")], False, "[Referenz]"),
    ("Rand ohne Fehler", [(SZ, "    if not UNTEN <= n <= OBEN:\n        raise ValueError(\"Keine Sitzung bis zum Rand",
                           "    if False:\n        raise ValueError(\"Keine Sitzung bis zum Rand")], False, "[Sollfall]"),
    ("Halbtag ungeprüft als voller Tag", [(SZ, 'halbtag=False if status == "belegt" else None)', "halbtag=False)")],
     False, "[Sollfall]"),
    ("heute in UTC statt Börsenzone", [(SZ, "    lokal = jetzt.astimezone(ZoneInfo(ZONEN[b]))",
                                        "    lokal = jetzt.astimezone(timezone.utc)")], False, "[Sollfall]"),
    ("naive Zeit angenommen", [(SZ, "    if not isinstance(jetzt, datetime) or jetzt.tzinfo is None or jetzt.utcoffset() is None:",
                                "    if not isinstance(jetzt, datetime):")], False, "[Sollfall]"),
    ("verschiebe zählt Kalendertage", [(SZ, "        d = _schritt(d, richtung)\n        while not is_trading_day(d, b):\n            d = _schritt(d, richtung)\n    return d\n",
                                        "        d = _schritt(d, richtung)\n    return d\n")], False, "[Referenz]"),
    ("einschliesslich ohne Typprüfung", [(SZ, '    _bool(einschliesslich, "einschliesslich")\n', "")], False, "[Sollfall]"),
    ("Position 0 erlaubt", [(SZ, "def nte_im_monat(j, m, n, boerse):\n    \"\"\"n-te offene Sitzung (n ≥ 1) eines Monats; None, wenn es sie nicht gibt.\"\"\"\n    _monat_pruefen(j, m)\n    _ganz(n, \"Position\")\n    if n < 1:",
                              "def nte_im_monat(j, m, n, boerse):\n    \"\"\"n-te offene Sitzung (n ≥ 1) eines Monats; None, wenn es sie nicht gibt.\"\"\"\n    _monat_pruefen(j, m)\n    _ganz(n, \"Position\")\n    if n < 0:")],
     False, "[Sollfall]"),
    # ── JS / Generator (Bundle in der Kopie neu erzeugt) ──
    ("JS: einschließlich/strikt vertauscht", [(API, "    if (!einschliesslich) n = schrittNr(n, r);", "    if (einschliesslich) n = schrittNr(n, r);")],
     True, "[Zwilling]"),
    ("JS: Hülle naechsterHandelstag strikt", [(API, "naechsterHandelstag: function (datum, boerse) { return suche(datum, boerse, true, 1); },",
                                               "naechsterHandelstag: function (datum, boerse) { return suche(datum, boerse, false, 1); },")],
     True, "[Zwilling]"),
    ("JS: heute immer UTC", [(API, "    var zone = DATEN.zonen[b];", "    var zone = 'UTC';")], True, "[Zwilling]"),
    ("JS: ungeprüfter Halbtag als voll", [(API, "      leer.halbtag = status === 'belegt' ? false : null;", "      leer.halbtag = false;")],
     True, "[Zwilling]"),
    ("JS: verschiebe zählt Kalendertage", [(API, "t = schrittNr(t, r); while (!offenNrB(b, t)) t = schrittNr(t, r);", "t = schrittNr(t, r);")],
     True, "[Zwilling]"),
    ("Generator ohne Zonen", [(GEN, '    nutz["zonen"] = {b: ZONEN[b] for b in boersen if b in ZONEN}\n', '    nutz["zonen"] = {}\n')],
     True, "[Zwilling]"),
]
M.MUTATIONEN += [
    ("JS: sitzungen lässt den Rand weg", [(API, "    for (var n = na; n <= ne; n++) if (offenNrB(b, n)) out.push(isoNr(n));",
                                           "    for (var n = na; n < ne; n++) if (offenNrB(b, n)) out.push(isoNr(n));")],
     True, "[Zwilling]"),
    ("JS: heute rollt ungültiges Datum", [(API, "      if (mon < 1 || mon > 12 || tag < 1 || tag > monatsTage(+dz[0], mon)) fehler('Kein gültiges Datum in jetzt: ' + jetzt);\n", "")],
     True, "[Zwilling]"),
]
M.UNGUELTIG_ERWARTET = [
    ("Absturz im Helfer (abgefangen)", [(SZ, '    status = BE.halbtag_status(b, d.year)\n',
                                         '    status = BE.halbtag_status(b, d.year)\n    raise RuntimeError("Absturz-Gegenprobe")\n')], False),
    ("JS-Absturz in der Suche (abgefangen)", [(API, "    var b = boerseNormalisieren(boerse), d = datumZerlegen(datum);\n    if (typeof einschliesslich !== 'boolean')",
                                               "    var b = boerseNormalisieren(boerse), d = datumZerlegen(datum);\n    if (datum === '2026-07-02') throw new Error('Absturz-Gegenprobe');\n    if (typeof einschliesslich !== 'boolean')")], True),
    ("Anker existiert nicht", [(SZ, "diese Zeile gibt es nicht", "egal")], False),
    ("Absturz: Modul nicht importierbar", [(SZ, "ZIELARTEN = (", "ZIELARTEN = ((")], False),
]

if __name__ == "__main__":
    sys.exit(M.main())
