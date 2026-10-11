# -*- coding: utf-8 -*-
"""Prüft den Wächter der US-Produkttermine (scripts/verify_produkttermine.py): baut Fehler in Regel, Einstufung,
Belege, Generator und JS-API ein und verlangt Rot an der benannten Prüfung.

    py -3.14 scripts/verify_produkttermine_mutation.py

Nutzt die isolierte Mechanik von scripts/verify_boersenereignisse_mutation.py (Temp-Kopie, Bundle bei JS-/Generator-
Mutationen in der Kopie neu erzeugt, Projektbaum-Hash vor = nach, Gegenproben).
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from scripts import verify_boersenereignisse_mutation as M  # noqa: E402

PT = "shared/produkttermine.py"
LI = "shared/produkttermine_listung.py"
API = "scripts/boersenkalender/api.js"
GEN = "scripts/build_boersenkalender_js.py"

M.WAECHTER = "verify_produkttermine"
M.MUTATIONEN = [
    ("VIX: Ersatz nicht rekursiv", [
        (PT, "    settlement = nominal if (offen(nominal) and offen(ref)) else _vorher(nominal, offen)\n",
         "    settlement = nominal if (offen(nominal) and offen(ref)) else nominal - timedelta(days=1)\n")],
     False, "[Synthetisch]"),
    ("VIX: Referenzfreitag ignoriert", [
        (PT, "    settlement = nominal if (offen(nominal) and offen(ref)) else _vorher(nominal, offen)\n",
         "    settlement = nominal if offen(nominal) else _vorher(nominal, offen)\n")], False, "[Beleg]"),
    ("OPEX: Ersatz nur ein Kalendertag", [
        (PT, "    verfall = regel if offen(regel) else _vorher(regel, offen)\n",
         "    verfall = regel if offen(regel) else regel - timedelta(days=1)\n")], False, "[Synthetisch]"),
    ("Einstufung >= statt >", [(PT, "    if regelwert > pruefdatum:\n", "    if regelwert >= pruefdatum:\n")],
     False, "[Grenze]"),
    ("Einstufung gegen Datenstand statt Prüfdatum", [
        (PT, "    if regelwert > pruefdatum:\n",
         '    if regelwert > date.fromisoformat(belege[reihe]["datenstand"]):\n')], False, "[Grenze]"),
    ("Optionshandelsende aus VX statt aus Optionsbeleg", [
        (PT, "    he_opt = None if v_opt is None else _vorher(v_opt, offen)\n",
         '    he_opt = _vorher(r["settlement"], offen)\n')], False, "[Abhängigkeit]"),
    ("Prüfdatum mit Standardwert", [
        (PT, "def produkttermine(von: str, bis: str, art: str, *, pruefdatum, ",
         'def produkttermine(von: str, bis: str, art: str, *, pruefdatum="2026-10-12", ')], False, "[Pflicht]"),
    ("Beleg falsch abgelesen (Karfreitag 2022)", [
        (LI, '2022: "0121 0218 0318 0414 0520', '2022: "0121 0218 0318 0415 0520')], False, "[Beleg]"),
    ("VX-Beleg fehlt (ein Monat)", [(LI, '2016: "01:0120 02:0217 03:0316 04:0420 05:0518 06:0615 07:0720 ', '2016: "01:0120 02:0217 03:0316 04:0420 05:0518 06:0615 ')],
     False, "[Beleg]"),
    # ── JS / Generator (Bundle in der Kopie neu erzeugt) ──
    ("JS: Einstufung >= statt >", [(API, "    if (regelIso > p) return [regelIso, 'projektion', null];",
                                    "    if (regelIso >= p) return [regelIso, 'projektion', null];")], True, "[Zwilling]"),
    ("JS: VIX ohne Referenzfreitag", [(API, "    var s = (offenNr(nominal) && offenNr(ref)) ? nominal : vorherNr(nominal);",
                                       "    var s = offenNr(nominal) ? nominal : vorherNr(nominal);")], True, "[Zwilling]"),
    ("JS: Prüfdatum nicht Pflicht", [(API, "    if (p === undefined || p === null) fehler('pruefdatum fehlt (Pflichtangabe, YYYY-MM-DD)');\n    datumZerlegen(p);\n",
                                      "    if (p === undefined || p === null) return '2026-10-12';\n")], True, "[Pflicht]"),
    ("JS: Optionshandelsende aus Settlement", [(API, "handelsende_optionen: op[0] === null ? null : vorherIso(op[0]),",
                                                "handelsende_optionen: vorherIso(r.settlement),")], True, "[Zwilling]"),
    ("JS: Triple Witching falsch", [(API, "triple_witching: PR.triple_monate.indexOf(m) >= 0,", "triple_witching: PR.triple_monate.indexOf(m) < 0,")], True, "[Zwilling]"),
    ("Generator ohne Optionsbelege", [(GEN, '"belege": BELEGREIHEN,',
                                       '"belege": {k: (dict(v, monate={}) if k == "VIX_OPT" else v) for k, v in BELEGREIHEN.items()},')],
     True, "[Zwilling]"),
]
M.MUTATIONEN += [
    # Die Triple-Monate stecken doppelt im Hash (je Monat und als Konstante) — nur beide zu entfernen ist eine Lücke
    ("Triple-Monate nicht in der Version", [
        (PT, '"grenzen": [OPEX_AB, VIX_AB, BIS, VIX_BIS], "triple": TRIPLE_MONATE,', '"grenzen": [OPEX_AB, VIX_AB, BIS, VIX_BIS],'),
        (PT, "                                            m in TRIPLE_MONATE]\n", "                                            ]\n")],
     True, "[Version]"),
    ("Kalenderannahme fehlt am Ereignis (Python und JS)", [
        (PT, '        "regelstand": REGELSTAND_OPEX, "quelle": _quelle(listung, "SPX_STANDARD"),\n'
             '        "kalenderannahme": KALENDERANNAHME, "kalenderstatus": KALENDERSTATUS,\n',
         '        "regelstand": REGELSTAND_OPEX, "quelle": _quelle(listung, "SPX_STANDARD"),\n'),
        (API, "      regelstand: PR.regelstand_opex, quelle: quelleVon(e[1], 'SPX_STANDARD'),\n"
              "      kalenderannahme: PR.kalenderannahme, kalenderstatus: PR.kalenderstatus,\n",
         "      regelstand: PR.regelstand_opex, quelle: quelleVon(e[1], 'SPX_STANDARD'),\n")], True, "[Herkunft]"),
    ("JS: Optionsquelle aus VX", [(API, "quelle_optionen: quelleVon(op[1], 'VIX_OPT'),",
                                   "quelle_optionen: quelleVon(vx[1], 'VIX_OPT'),")], True, "[Zwilling]"),
]
M.UNGUELTIG_ERWARTET = [
    ("Anker existiert nicht", [(PT, "diese Zeile gibt es nicht", "egal")], False),
    ("Absturz: Modul nicht importierbar", [(PT, "ARTEN = (", "ARTEN = ((")], False),
]

if __name__ == "__main__":
    sys.exit(M.main())
