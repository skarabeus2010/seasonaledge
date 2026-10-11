"""Belegreihen der US-Produkttermine (V1c-2, Entwurf docs/review_prompts/2026-10-12_kalender_v1c2_entwurf_v6.md).

Drei unabhängige Reihen, je mit Quelle und Datenstand. Ein Monat ist belegt, wenn er hier steht; der Wert ist das
Datum, das die Quelle nennt. `shared/produkttermine.py` rechnet die Termine nach Regel und prüft sie gegen diese
Belege — die Daten hier sind die unabhängige Seite, nicht aus dem Code abgeleitet.

- VX:           Cboe-Historiendatei je Kontrakt `VX/VX_<Settlement>.csv` existiert (HTTP 200, per HEAD-Abruf je
                Monat 2015-09…2027-09 erhoben; ab 2027-07 HTTP 403 = kein positiver Listungsnachweis).
- SPX_STANDARD: Standardverfall „Equity, Equity Index, ETF & ETN Options" aus den Cboe-Jahreskalendern 2020–2026,
                visuell aus den PDFs abgelesen.
- VIX_OPT:      „VIX Options Standard Expiration" aus denselben Jahreskalendern, visuell abgelesen; Gegenprobe: alle
                84 Monate gleich dem VX-Settlement aus den Dateinamen.
Zweite, blinde Ablesung beider Kalenderreihen durch einen eigenen Agenten ohne Kenntnis dieser Werte (2026-10-12):
0 Abweichungen in 168 Werten; unsichere Zellen (geteilte Farben) dort benannt: 2022-03/06, 2024-06, 2025-03/04/06,
2026-05/06 — alle VIX-Ausnahme- oder Mischzellen, deren Wert beide Ablesungen gleich lasen.
Werte: {"YYYY-MM": "MMDD"} je Jahr — das Jahr des Termins ist bei allen drei Reihen das Jahr des Monats.
"""
from __future__ import annotations

_KAL = "https://cdn.cboe.com/resources/options/Cboe%dOPTIONSCalendar.pdf"


def _reihe(jahre: dict[int, str]) -> dict[str, str]:
    """{Jahr: "MMDD MMDD …" (12 Einträge Jan–Dez bzw. ab Startmonat)} → {"YYYY-MM": "YYYY-MM-DD"}."""
    out = {}
    for j, text in jahre.items():
        for eintrag in text.split():
            monat, tag = eintrag.split(":")
            out["%04d-%s" % (j, monat)] = "%04d-%s-%s" % (j, tag[:2], tag[2:])
    return out


def _kalenderjahre(werte: dict[int, str]) -> dict[str, str]:
    return _reihe({j: " ".join("%02d:%s" % (i + 1, t) for i, t in enumerate(v.split())) for j, v in werte.items()})


BELEGREIHEN: dict[str, dict] = {
    "VX": {
        "titel": "Cboe Futures Exchange, Historiendatei je VX-Kontrakt",
        "quelle": "https://cdn.cboe.com/data/us/futures/market_statistics/historical_data/VX/VX_<Settlement>.csv",
        "datenstand": "2026-10-12",
        "monate": _reihe({
            2015: "09:0916 10:1021 11:1118 12:1216",
            2016: "01:0120 02:0217 03:0316 04:0420 05:0518 06:0615 07:0720 08:0817 09:0921 10:1019 11:1116 12:1221",
            2017: "01:0118 02:0215 03:0322 04:0419 05:0517 06:0621 07:0719 08:0816 09:0920 10:1018 11:1115 12:1220",
            2018: "01:0117 02:0214 03:0321 04:0418 05:0516 06:0620 07:0718 08:0822 09:0919 10:1017 11:1121 12:1219",
            2019: "01:0116 02:0213 03:0319 04:0417 05:0522 06:0619 07:0717 08:0821 09:0918 10:1016 11:1120 12:1218",
            2020: "01:0122 02:0219 03:0318 04:0415 05:0520 06:0617 07:0722 08:0819 09:0916 10:1021 11:1118 12:1216",
            2021: "01:0120 02:0217 03:0317 04:0421 05:0519 06:0616 07:0721 08:0818 09:0915 10:1020 11:1117 12:1222",
            2022: "01:0119 02:0216 03:0315 04:0420 05:0518 06:0615 07:0720 08:0817 09:0921 10:1019 11:1116 12:1221",
            2023: "01:0118 02:0215 03:0322 04:0419 05:0517 06:0621 07:0719 08:0816 09:0920 10:1018 11:1115 12:1220",
            2024: "01:0117 02:0214 03:0320 04:0417 05:0522 06:0618 07:0717 08:0821 09:0918 10:1016 11:1120 12:1218",
            2025: "01:0122 02:0219 03:0318 04:0416 05:0521 06:0618 07:0716 08:0820 09:0917 10:1022 11:1119 12:1217",
            2026: "01:0121 02:0218 03:0318 04:0415 05:0519 06:0617 07:0722 08:0819 09:0916 10:1021 11:1118 12:1216",
            2027: "01:0120 02:0217 03:0317 04:0421 05:0518 06:0616",
        }),
    },
    "SPX_STANDARD": {
        "titel": "Cboe Options Expiration Calendar (Jahreskalender), Standardverfall",
        "quelle": _KAL % 2020 + " … " + _KAL % 2026,
        "datenstand": "2026-10-12",
        "monate": _kalenderjahre({
            2020: "0117 0221 0320 0417 0515 0619 0717 0821 0918 1016 1120 1218",
            2021: "0115 0219 0319 0416 0521 0618 0716 0820 0917 1015 1119 1217",
            2022: "0121 0218 0318 0414 0520 0617 0715 0819 0916 1021 1118 1216",
            2023: "0120 0217 0317 0421 0519 0616 0721 0818 0915 1020 1117 1215",
            2024: "0119 0216 0315 0419 0517 0621 0719 0816 0920 1018 1115 1220",
            2025: "0117 0221 0321 0417 0516 0620 0718 0815 0919 1017 1121 1219",
            2026: "0116 0220 0320 0417 0515 0618 0717 0821 0918 1016 1120 1218",
        }),
    },
    "VIX_OPT": {
        "titel": "Cboe Options Expiration Calendar (Jahreskalender), VIX Options Standard Expiration",
        "quelle": _KAL % 2020 + " … " + _KAL % 2026,
        "datenstand": "2026-10-12",
        "monate": _kalenderjahre({
            2020: "0122 0219 0318 0415 0520 0617 0722 0819 0916 1021 1118 1216",
            2021: "0120 0217 0317 0421 0519 0616 0721 0818 0915 1020 1117 1222",
            2022: "0119 0216 0315 0420 0518 0615 0720 0817 0921 1019 1116 1221",
            2023: "0118 0215 0322 0419 0517 0621 0719 0816 0920 1018 1115 1220",
            2024: "0117 0214 0320 0417 0522 0618 0717 0821 0918 1016 1120 1218",
            2025: "0122 0219 0318 0416 0521 0618 0716 0820 0917 1022 1119 1217",
            2026: "0121 0218 0318 0415 0519 0617 0722 0819 0916 1021 1118 1216",
        }),
    },
}
