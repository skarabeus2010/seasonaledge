"""Belegte Halbtage (verkürzte Handelstage) — V1c-3, Entwurf docs/review_prompts/2026-10-12_kalender_v1c3_entwurf_v2.md.

Nur Belege, keine Regelableitung: Halbtage beschließen die Börsen jährlich. Ein Halbtag existiert nur, wenn eine
Quelle ihn nennt. `abdeckung` ist ein eigener Beleg: nur dort nennt eine Quelle die Halbtage des GANZEN Jahres
(`halbtag_status = belegt`), sonst gilt ein Jahr als `ungeprueft` — auch wenn einzelne Halbtage belegt sind.

Quellen: die amtliche Kalenderseite der NYSE (bis 2014 nyx.com), je Stand als **unveränderliche Archivfassung**
(web.archive.org, Inhalt per SHA-256 gesichert; Kennungen und Prüfsummen in shared/kalender_quellen.py, Sicherung
docs/belege/nyse_halbtage_2026-10-12.md). Die Seite listet jeweils zwei bis drei Kalenderjahre.

NYSE: `schlusszeit` = regulärer Schluss des Aktien-Kernhandels (13:00 ET). Optionen (13:15), Late Sessions (17:00)
und Crossing Sessions sind nicht Inhalt des Feldes. Zukunftsjahre sind belegte Ankündigungen.
Übrige Börsen (u. a. LSE): ungeprüft, keine Halbtagsereignisse. Abruf: 2026-10-12.
"""
from __future__ import annotations

# Kurzname → (Name DE, Name EN)
NAMEN = {
    "vor_independence_day": ("Halbtag vor dem Unabhängigkeitstag", "Early close (day before Independence Day)"),
    "tag_nach_thanksgiving": ("Halbtag nach Thanksgiving", "Early close (day after Thanksgiving)"),
    "heiligabend": ("Halbtag Heiligabend", "Early close (Christmas Eve)"),
}

# Jahr → Quelle (Archivfassung), deren Kalender das ganze Jahr nennt. Jedes Ereignis trägt die Quelle seines Jahres.
_ABDECKUNG = {
    2013: "NYSE.halbtage_archiv20131129", 2014: "NYSE.halbtage_archiv20131129",
    2015: "NYSE.halbtage_archiv20150210", 2016: "NYSE.halbtage_archiv20150210",
    2017: "NYSE.halbtage_archiv20160204",
    2018: "NYSE.halbtage_archiv20170303", 2019: "NYSE.halbtage_archiv20170303",
    2020: "NYSE.halbtage_archiv20200219",
    2021: "NYSE.halbtage_archiv20200219", 2022: "NYSE.halbtage_archiv20200219",
    2023: "NYSE.halbtage_archiv20210208",
    2024: "NYSE.halbtage_archiv20240111", 2025: "NYSE.halbtage_archiv20240111",
    2026: "NYSE.halbtage_nyse20261012", 2027: "NYSE.halbtage_nyse20261012", 2028: "NYSE.halbtage_nyse20261012",
}

_TAGE = {   # Datum → Kurzname (je Jahr vollständig, wie die Quelle des Jahres sie nennt)
    "2013-07-03": "vor_independence_day", "2013-11-29": "tag_nach_thanksgiving", "2013-12-24": "heiligabend",
    "2014-07-03": "vor_independence_day", "2014-11-28": "tag_nach_thanksgiving", "2014-12-24": "heiligabend",
    "2015-11-27": "tag_nach_thanksgiving", "2015-12-24": "heiligabend",
    "2016-11-25": "tag_nach_thanksgiving",
    "2017-07-03": "vor_independence_day", "2017-11-24": "tag_nach_thanksgiving",
    "2018-07-03": "vor_independence_day", "2018-11-23": "tag_nach_thanksgiving", "2018-12-24": "heiligabend",
    "2019-07-03": "vor_independence_day", "2019-11-29": "tag_nach_thanksgiving", "2019-12-24": "heiligabend",
    "2020-11-27": "tag_nach_thanksgiving", "2020-12-24": "heiligabend",
    "2021-11-26": "tag_nach_thanksgiving",
    "2022-11-25": "tag_nach_thanksgiving",
    "2023-07-03": "vor_independence_day", "2023-11-24": "tag_nach_thanksgiving",
    "2024-07-03": "vor_independence_day", "2024-11-29": "tag_nach_thanksgiving", "2024-12-24": "heiligabend",
    "2025-07-03": "vor_independence_day", "2025-11-28": "tag_nach_thanksgiving", "2025-12-24": "heiligabend",
    "2026-11-27": "tag_nach_thanksgiving", "2026-12-24": "heiligabend",
    "2027-11-26": "tag_nach_thanksgiving",
    "2028-07-03": "vor_independence_day", "2028-11-24": "tag_nach_thanksgiving",
}

HALBTAGE: dict[str, dict] = {
    "NYSE": {
        "schlusszeit": "13:00",
        "zeitzone": "America/New_York",
        "sitzung": "nyse_aktien_kernhandel",
        "abruf": "2026-10-12",
        # Datum → (Kurzname, Quellenkennung in shared/kalender_quellen.py)
        "ereignisse": {d: (k, _ABDECKUNG[int(d[:4])]) for d, k in _TAGE.items()},
        "abdeckung": dict(_ABDECKUNG),
        "sicherung": "docs/belege/nyse_halbtage_2026-10-12.md",
    },
}
