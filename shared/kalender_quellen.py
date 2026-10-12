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
    "NYSE.halbtage_archiv20131129": (
        'NYSE-Kalenderseite (Holidays & Trading Hours), Stand 2013-11-29, Jahre 2013–2014',
        'Archiv https://web.archive.org/web/20131129003407id_/http://www.nyx.com/holidays-and-hours/nyse; SHA-256 8cec5115e043156ecaf8fb9955524694645e24e583ebfc74243f92731f880fb5 (42317 Byte); Sicherung docs/belege/nyse_halbtage_2026-10-12.md',
        "2026-10-12"),
    "NYSE.halbtage_archiv20150210": (
        'NYSE-Kalenderseite (Holidays & Trading Hours), Stand 2015-02-10, Jahre 2015–2016',
        'Archiv https://web.archive.org/web/20150210033400id_/https://www.nyse.com/markets/hours-calendars; SHA-256 edc8799a85cec668ed966f4246a5b0aff133142843047ac9d97f595270e61fb3 (30312 Byte); Sicherung docs/belege/nyse_halbtage_2026-10-12.md',
        "2026-10-12"),
    "NYSE.halbtage_archiv20160204": (
        'NYSE-Kalenderseite (Holidays & Trading Hours), Stand 2016-02-04, Jahre 2016–2017',
        'Archiv https://web.archive.org/web/20160204112739id_/https://www.nyse.com/markets/hours-calendars; SHA-256 0af4c54b4ee2f0fcbbd6f738e9db8183b270a01781bb76b6eec2dbd29243534f (78758 Byte); Sicherung docs/belege/nyse_halbtage_2026-10-12.md',
        "2026-10-12"),
    "NYSE.halbtage_archiv20170303": (
        'NYSE-Kalenderseite (Holidays & Trading Hours), Stand 2017-03-03, Jahre 2017–2019',
        'Archiv https://web.archive.org/web/20170303135722id_/https://www.nyse.com/markets/hours-calendars; SHA-256 81e984b95a909a42e01ab9da823894991a1b133a92ec363651fd906ca04afa39 (232865 Byte); Sicherung docs/belege/nyse_halbtage_2026-10-12.md',
        "2026-10-12"),
    "NYSE.halbtage_archiv20200219": (
        'NYSE-Kalenderseite (Holidays & Trading Hours), Stand 2020-02-19, Jahre 2020–2022',
        'Archiv https://web.archive.org/web/20200219200315id_/https://www.nyse.com/markets/hours-calendars; SHA-256 902b381d9b42c81e96e26f80f6123e9743434232f60be1c7e2e1d5857e0d0137 (183790 Byte); Sicherung docs/belege/nyse_halbtage_2026-10-12.md',
        "2026-10-12"),
    "NYSE.halbtage_archiv20210208": (
        'NYSE-Kalenderseite (Holidays & Trading Hours), Stand 2021-02-08, Jahre 2021–2023',
        'Archiv https://web.archive.org/web/20210208220700id_/https://www.nyse.com/markets/hours-calendars; SHA-256 a43a686cbfad9c362dd5594a96718f5fabb207aa2e691517271d8c0f2bd1e582 (93533 Byte); Sicherung docs/belege/nyse_halbtage_2026-10-12.md',
        "2026-10-12"),
    "NYSE.halbtage_archiv20240111": (
        'NYSE-Kalenderseite (Holidays & Trading Hours), Stand 2024-01-11, Jahre 2024–2026',
        'Archiv https://web.archive.org/web/20240111002222id_/https://www.nyse.com/markets/hours-calendars; SHA-256 9b02f75db96aa8f0bf4ebfae2c991ed5a19c391ca703974b49176b5d1ae4bc40 (127218 Byte); Sicherung docs/belege/nyse_halbtage_2026-10-12.md',
        "2026-10-12"),
    "NYSE.halbtage_nyse20261012": (
        'NYSE-Kalenderseite (Holidays & Trading Hours), Abruf 2026-10-12, Jahre 2026–2028',
        'Archiv https://web.archive.org/web/20261009200946id_/https://www.nyse.com/trade/hours-calendars; SHA-256 79602f7be5a8f1d39c2b1cac4dd02c4c07f18cf9f92d70602834069154719bad (109229 Byte); Sicherung docs/belege/nyse_halbtage_2026-10-12.md',
        "2026-10-12"),
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
