"""Quellentabelle des Ereigniskatalogs (`shared/boersenereignisse.py`, Vertrag B4).

Kennung → (Titel, Beleg, Prüfstand). Übernommen aus den Belegkommentaren in `shared/exchange_holidays.py` und
`shared/nyse_holidays.py`; wo nur ein Regelwerk ohne Einzelbeleg vorliegt, sagt der Beleg genau das. Eine
Kennung `…konvention` bzw. `…tabelle` ist ausdrücklich KEIN Beleg des einzelnen Tages (siehe `kalender_status`).
"""
from __future__ import annotations

QUELLEN: dict[str, tuple[str, str, str]] = {
    "NYSE.regelwerk": (
        "NYSE-Feiertagsregeln",
        "NYSE Rule 7.2 / Holiday Calendar; MLK ab 1998, Juneteenth ab 2022; Abgleich ab 1971 (Wahlen-Arbeit, Paket 1)",
        "2026-10-10"),
    "NYSE.sonderschliessungen": (
        "NYSE-Sonderschließungen",
        "Einzelbelege je Tag in shared/nyse_holidays.py::_NYSE_SPECIAL_CLOSURES; 1972–1980 Wahltage durch Kurslücken "
        "^GSPC/^DJI (docs/WAHLEN.md)",
        "2026-10-10"),
    "XETRA.regelwerk": (
        "Xetra-Handelskalender",
        "Handelskalender 2003, 2004, 2007–2010, Eurex-Rundschreiben 087/02; 24.12.2001 dokumentierte Annahme; vor 2001 "
        "ungeprüft",
        "2026-10-08"),
    "XETRA.sonderschliessungen": (
        "Xetra-Sonderschließungen",
        "FWB-Rundschreiben 18/2006, Eurex-Rundschreiben 128/16, Xetra-Handelskalender 2014–2021 (je Tag in "
        "exchange_holidays.XETRA_SONDER)",
        "2026-10-08"),
    "LSE.regelwerk": (
        "Bank Holidays England und Wales",
        "gov.uk/bank-holidays; Ersatz am nächsten freien Werktag bei Wochenende",
        "2026-10-10"),
    "LSE.verlegungen": (
        "Verlegte Bank Holidays (Proklamation)",
        "gov.uk: Early May 2020 → 8.5. (VE Day 75); Spring Bank 2002/2012/2022 verlegt für Thronjubiläen",
        "2026-10-10"),
    "LSE.sonderschliessungen": (
        "Einmalige Bank Holidays",
        "gov.uk: 29.04.2011 Royal Wedding, 19.09.2022 Staatsbegräbnis, 08.05.2023 Krönung",
        "2026-10-10"),
    "EURONEXT.regelwerk": ("Euronext-Handelskalender", "Regelwerk ohne Einzelbeleg je Jahr (Stichproben)", "2026-10-10"),
    "MILAN.regelwerk": ("Borsa-Italiana-Handelskalender", "Regelwerk ohne Einzelbeleg je Jahr (Stichproben)", "2026-10-10"),
    "SIX.regelwerk": ("SIX-Handelskalender", "Regelwerk ohne Einzelbeleg je Jahr (Stichproben)", "2026-10-10"),
    "STOCKHOLM.regelwerk": ("Nasdaq-Stockholm-Handelskalender", "Regelwerk ohne Einzelbeleg je Jahr (Stichproben)",
                            "2026-10-10"),
    "OSLO.regelwerk": ("Oslo-Børs-Handelskalender", "Regelwerk ohne Einzelbeleg je Jahr (Stichproben)", "2026-10-10"),
    "TSE.regelwerk": (
        "Japanisches Feiertagsgesetz und JPX-Handelskalender",
        "国民の祝日に関する法律 (Furikae ab 1973, ab 2007 über aufeinanderfolgende Feiertage, Kokumin no Kyujitsu); "
        "Tagesvergleich 2001–2027 (Codex R4)",
        "2026-10-10"),
    "TSE.olympia": ("Olympia-Sondergesetz 2020/2021", "NAOJ-Kalender 2020/2021 (revidiert)", "2026-10-10"),
    "TSE.einmalig": ("Thronwechsel 2019", "JPX-Mitteilung 2019-01-15", "2026-10-10"),
    "TSE.sonderschliessungen": ("TSE-Systemausfall", "JPX-Mitteilung 2020-10-01 (arrowhead)", "2026-10-10"),
    "TSE.jahreswechsel": ("JPX-Jahreswechsel", "JPX-Handelskalender: 31.12., 2.1., 3.1. geschlossen", "2026-10-10"),
    "HKEX.tabelle": (
        "HKEX-Tabelle 2016–2026",
        "Datumstabelle exchange_holidays._HKEX_HOLIDAYS (teils aus Kurslücken); 2026 gegen Wertpapierkalender belegt — "
        "Identität der Einzeltage nicht belegt",
        "2026-10-10"),
    "HKEX.konvention": ("HKEX-Rückfallregel", "feste gregorianische Feiertage außerhalb der Tabelle — Konvention, "
                                              "kein Beleg", "2026-10-10"),
    "KRX.tabelle": (
        "KRX-Tabelle 2016–2026",
        "Datumstabelle exchange_holidays._KRX_HOLIDAYS (Paket 1 korrigiert) — Identität der Einzeltage nicht belegt",
        "2026-10-10"),
    "KRX.konvention": ("KRX-Rückfallregel", "feste gregorianische Feiertage außerhalb der Tabelle — Konvention, "
                                            "kein Beleg", "2026-10-10"),
}
