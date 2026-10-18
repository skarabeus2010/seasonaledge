# -*- coding: utf-8 -*-
"""Prüft den Wächter der Fassade (scripts/verify_holidays_fassade.py): baut Vertragsverletzungen in Fassade,
Header, Converter und Seiten ein und verlangt Rot an der benannten Prüfung (Kalender V2, Entwurf v2/v3).

    py -3.14 scripts/verify_holidays_fassade_mutation.py

Nutzt die isolierte Mechanik von scripts/verify_boersenereignisse_mutation.py (Temp-Kopie, Projektbaum-Hash vor =
nach, Gegenproben). Die Kopie wird um die Dateien ergänzt, die der Wächter liest (Seiten, Converter, Ticker, en.json).
"""
from __future__ import annotations

import pathlib
import shutil
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from scripts import verify_boersenereignisse_mutation as M  # noqa: E402

H = "landing/js/holidays.js"
A = "landing/js/app.js"
C = "seo/tools/trading-day-converter.html"
D = "landing/pages/dashboard.html"

_kopie_basis = M.isolierte_kopie


def isolierte_kopie(ziel: pathlib.Path) -> pathlib.Path:
    _kopie_basis(ziel)
    w = M.WURZEL
    shutil.copytree(w / "landing" / "pages", ziel / "landing" / "pages")
    shutil.copytree(w / "landing" / "i18n", ziel / "landing" / "i18n")
    (ziel / "landing" / "data").mkdir()
    shutil.copy2(w / "landing" / "data" / "tickers.json", ziel / "landing" / "data" / "tickers.json")
    (ziel / "seo").mkdir()
    shutil.copytree(w / "seo" / "tools", ziel / "seo" / "tools")
    # jsdom für die Seitenprobe (die Basiskopie lässt scripts/perf aus)
    shutil.copytree(w / "scripts" / "perf" / "node_modules", ziel / "scripts" / "perf" / "node_modules")
    return ziel


M.isolierte_kopie = isolierte_kopie
M.WAECHTER = "verify_holidays_fassade"
M.MUTATIONEN = [
    # ── Fassade (B5) ──
    ("detect fällt auf NYSE zurück", [(H, "H.detect = function (ticker) { return K.boerse(ticker); };",
                                       "H.detect = function (ticker) { try { return K.boerse(ticker); } catch (e) { return 'NYSE'; } };")],
     False, "[Vertrag"),
    ("NONE wieder offen", [(H, "H.isTradingDay = function (dateStr, exchange) { return K.istHandelstag(dateStr, exchange); };",
                            "H.isTradingDay = function (dateStr, exchange) { return exchange === 'NONE' || K.istHandelstag(dateStr, exchange); };")],
     False, "[Vertrag"),
    ("nextTradingDay streng statt ab einschließlich", [(H, "return K.naechste(this._ds(y, m, d), exchange, true);",
                                                        "return K.naechste(this._ds(y, m, d), exchange, false);")],
     False, "[Delegation"),
    ("nextTradingDay mit 10-Tage-Grenze", [(H, "return K.naechste(this._ds(y, m, d), exchange, true);",
                                            "var z = K.naechste(this._ds(y, m, d), exchange, true); return z > this._ds(y, m, Math.min(d + 4, 28)) ? this._ds(y, m, d) : z;")],
     False, "[Vertrag"),
    ("lastTradingDay ohne Vorgabe n = 1", [(H, "return K.nteVonHintenImMonat(y, m, nFromEnd === undefined ? 1 : nFromEnd, exchange);",
                                            "return K.nteVonHintenImMonat(y, m, nFromEnd, exchange);")],
     False, "[Vertrag"),
    ("Sonderliste unter kalender_v1 lesbar", [(H, "['_nyse', '_xetra', '_lse', '_cache', '_getCachedMap', '_NYSE_SONDER', '_XETRA_SONDER']",
                                               "['_nyse', '_xetra', '_lse', '_cache', '_getCachedMap', '_XETRA_SONDER']")],
     False, "[Vertrag"),
    ("Fassade greift auch unter alt", [(H, "  if (SA.kalenderMethode !== 'kalender_v1') return;\n  var K = SA.boersenkalender;",
                                        "  if (SA.kalenderMethode !== 'kalender_v1' && !SA.boersenkalender) return;\n  var K = SA.boersenkalender;")],
     False, "[alt = Momentaufnahme"),
    ("alter Zweig verändert", [(H, "    if (exchange === 'NONE') return [];", "    if (exchange === 'NONE') return ['2026-01-01'];")],
     False, "[alt = Momentaufnahme"),
    # ── Header (B1) ──
    ("Header nimmt das Browserdatum", [(A, "    heute = K.heute(b, SA.__uhr ? SA.__uhr() : Date.now()).datum;",
                                        "    var _j = new Date(SA.__uhr ? SA.__uhr() : Date.now()); heute = _j.getUTCFullYear() + '-' + pad(_j.getUTCMonth() + 1) + '-' + pad(_j.getUTCDate());")],
     False, "[Header"),
    ("Header ohne Kennzeichen geschlossen", [(A, "  if (!n.offen) zusatz.push(t('app.hdr_geschlossen', 'geschlossen'));\n", "")],
     False, "[Header"),
    ("Header ohne Kalenderstatus", [(A, "  else if (status === 'ungeprueft') zusatz.push(", "  else if (false) zusatz.push(")],
     False, "[Header"),
    ("Header-Monatssumme ohne letzten Monatstag", [(A, "y + '-' + pad(m) + '-' + pad(monatsLetzter), b).length;",
                                                    "y + '-' + pad(m) + '-' + pad(monatsLetzter - 1), b).length;")],
     False, "[Header"),
    ("Header-Wochensumme aus dem Kalenderjahr", [(A, "isoWoche(woche[1], 12, 28)[0]", "isoWoche(y, 12, 28)[0]")],
     False, "[Header"),
    # (refTicker = ticker allein wäre äquivalent: alle Sektor-ETFs handeln an der NYSE — Lauf 2026-10-18)
    ("Korb übergibt keinen Kalenderticker", [("landing/pages/sektor-rotation.html",
                                               "sectorData[firstTicker].rows, firstTicker);", "sectorData[firstTicker].rows);")],
     False, "[Seite sektor-rotation: Header nennt"),
    ("Seite lädt das Bundle nicht", [(D, '  <script src="/landing/js/boersenkalender.js"></script>\n', "")],
     False, "[Seite dashboard"),
    # ── Converter (B3) ──
    ("Converter-Wochentag aus lokalem Date", [(C, "        var wd = ((tag % 7) + 11) % 7;\n",
                                               "        var wd = new Date(y, m - 1, d - 1).getDay();\n")],
     False, "[Converter"),
    ("Converter-Jahressumme fest 252", [(C, "            jSumme = K.sitzungen(y + '-01-01', y + '-12-31', b).length;",
                                         "            jSumme = 252;")],
     False, "[Converter"),
    ("Converter ohne Konvention", [(C, "        var hinweis = KONVENTION[b] || STATUS[K.status(b, y)] || '';",
                                    "        var hinweis = STATUS[K.status(b, y)] || '';")],
     False, "[Converter"),
    ("Converter alt verändert", [(C, "' <span class=\"sep\">&middot;</span> TDOY ' + tdoy + '<span class=\"sub\">/~252</span>';",
                                  "' <span class=\"sep\">&middot;</span> TDOY ' + tdoy + '<span class=\"sub\">/~253</span>';")],
     False, "[Converter alt"),
    # ── Monatsreferenz (Codex Code R4): ein falscher belegter Nachfolger muss auffallen ──
    ("Nachfolger Mailand verfälscht", [("scripts/fixtures/kalender_monatslisten_2026.json",
                                         '"datum": "2026-12-01",\n    "status": "belegt",\n    "quelle": "Euronext-Tabelle 2026, Spalte Milan',
                                         '"datum": "2026-12-02",\n    "status": "belegt",\n    "quelle": "Euronext-Tabelle 2026, Spalte Milan')],
     False, "[Monatsliste MILAN 2026-11 Übergang"),
    # ── Seiten (B1 Inventar) ──
    ("Fehlerfänger wieder still", [(D, "try{ex=SA.holidays.detect(ticker||'');}catch(e){if (SA.kalenderMethode !== 'alt') throw e; ex='NONE';}",
                                    "try{ex=SA.holidays.detect(ticker||'');}catch(e){ex='NONE';}")],
     False, "[Inventar"),
]
M.UNGUELTIG_ERWARTET = [
    ("Anker existiert nicht", [(H, "diese Zeile gibt es nicht", "egal")], False),
    ("Absturz: Fassade wirft beim Laden", [(H, "  var H = SA.holidays;\n  H.detect =", "  var H = SA.holidays;\n  throw new Error('Absturz-Gegenprobe');\n  H.detect =")], False),
]

if __name__ == "__main__":
    sys.exit(M.main())
