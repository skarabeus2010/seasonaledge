#!/usr/bin/env python3
"""
Wächter: Handelstag-Nummern (TDOM/TDOY) nach Börsenkalender — `shared.exchange_holidays.handelstag_nummern`.

Zwei getrennte Referenzen (Codex Runde 4, Auflage 8):
  [Arithmetik]  numpy.busday_count über die Feiertage des Produktionskalenders, jede Börse, jeder Tag
                1950–2035, alle fünf Felder. Prüft das ZÄHLEN, nicht den Kalender — derselbe falsche
                Feiertag stünde auf beiden Seiten.
  [Sollkalender] wörtliche offizielle Feiertagslisten einzelner Jahre (nicht aus dem Code), mit numpy
                gezählt und für JEDEN Tag des Jahres gegen die Produktion verglichen. Prüft Kalender
                und Zählung zusammen.
Dazu [Vertrag] (Validierung, Reihenfolge, Duplikate, Periodensummen, geschlossene Tage) und [Status].

Aufruf:  py -3.14 scripts/verify_handelstag_nummern.py      Exit 0 = alles erfüllt
"""
from __future__ import annotations

import os
import sys
from datetime import date, datetime, timedelta

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.exchange_holidays import (  # noqa: E402
    _EXCHANGE_FUNCTIONS, handelstag_nummern, kalender_status, get_holidays,
)

FEHLER: list[str] = []
ZAEHLER = {"n": 0}


def pruefe(kennung: str, bedingung: bool, text: str = "") -> None:
    ZAEHLER["n"] += 1
    if not bedingung:
        FEHLER.append(f"[{kennung}] {text}")


def wochenmaske(boerse: str) -> str:
    return "1111111" if boerse == "CRYPTO" else "1111100"


def numpy_nummern(tage: list[date], feiertage, maske: str) -> list[tuple]:
    """Unabhängige Zählung: busday_count schließt das Enddatum aus → vorwärts bis d+1."""
    fei = np.array(sorted(feiertage), dtype="datetime64[D]") if feiertage else np.array([], dtype="datetime64[D]")
    d = np.array(tage, dtype="datetime64[D]")
    jahr0 = d.astype("datetime64[Y]").astype("datetime64[D]")
    jahr1 = (d.astype("datetime64[Y]") + 1).astype("datetime64[D]")
    mon0 = d.astype("datetime64[M]").astype("datetime64[D]")
    mon1 = (d.astype("datetime64[M]") + 1).astype("datetime64[D]")
    kw = dict(weekmask=maske, holidays=fei)
    offen = np.is_busday(d, **kw)
    tdoy = np.busday_count(jahr0, d + 1, **kw)
    tdom = np.busday_count(mon0, d + 1, **kw)
    tdoy_rev = -np.busday_count(d, jahr1, **kw)    # zählt d selbst mit, wenn offen
    tdom_rev = -np.busday_count(d, mon1, **kw)
    out = []
    for i in range(len(tage)):
        o = bool(offen[i])
        out.append((int(tdom[i]), int(tdoy[i]),
                    int(tdom_rev[i]) if o else None, int(tdoy_rev[i]) if o else None, o))
    return out


def block_arithmetik() -> None:
    tage = [date(1950, 1, 1) + timedelta(days=i) for i in range((date(2036, 1, 1) - date(1950, 1, 1)).days)]
    for boerse in _EXCHANGE_FUNCTIONS:
        if boerse == "NASDAQ":
            continue
        fei = get_holidays(boerse, 1950, 2035)
        soll = numpy_nummern(tage, fei, wochenmaske(boerse))
        ist = handelstag_nummern(tage, boerse)
        abw = [(t, tuple(i), s) for t, i, s in zip(tage, ist, soll) if tuple(i) != s]
        pruefe(f"Arithmetik {boerse}", not abw,
               f"{len(abw)} Abweichungen, erste: {abw[0] if abw else ''}")


# Wörtliche offizielle Schließtage (Werktage) — NICHT aus dem Code. Quellen wie in
# scripts/verify_kalender_sollfaelle.py.
SOLLKALENDER = {
    # Deutsche Börse Handelskalender 2012 (Blatt selbst gelesen 2026-10-10)
    ("XETRA", 2012): ["2012-04-06", "2012-04-09", "2012-05-01", "2012-12-24", "2012-12-25",
                      "2012-12-26", "2012-12-31"],
    # Deutsche Börse Handelskalender 2018 (+ Eurex-Rundschreiben 055/2018)
    ("XETRA", 2018): ["2018-01-01", "2018-03-30", "2018-04-02", "2018-05-01", "2018-05-21",
                      "2018-10-03", "2018-12-24", "2018-12-25", "2018-12-26", "2018-12-31"],
    # NYSE 2025 (inkl. Staatstrauer Carter 9.1.)
    ("NYSE", 2025): ["2025-01-01", "2025-01-09", "2025-01-20", "2025-02-17", "2025-04-18",
                     "2025-05-26", "2025-06-19", "2025-07-04", "2025-09-01", "2025-11-27", "2025-12-25"],
    # LSE 2022 (gov.uk/bank-holidays: Neujahrsersatz, Jubiläum, Staatsbegräbnis, Weihnachtsersatz)
    ("LSE", 2022): ["2022-01-03", "2022-04-15", "2022-04-18", "2022-05-02", "2022-06-02",
                    "2022-06-03", "2022-08-29", "2022-09-19", "2022-12-26", "2022-12-27"],
    # TSE 2021 (NAOJ 2021 revidiert + JPX-Regel 31.12./2.–3.1.; 2.1./3.1. waren Wochenende)
    ("TSE", 2021): ["2021-01-01", "2021-01-11", "2021-02-11", "2021-02-23", "2021-04-29",
                    "2021-05-03", "2021-05-04", "2021-05-05", "2021-07-22", "2021-07-23",
                    "2021-08-09", "2021-09-20", "2021-09-23", "2021-11-03", "2021-11-23",
                    "2021-12-31"],
}


def block_sollkalender() -> None:
    for (boerse, jahr), schliess in SOLLKALENDER.items():
        tage = [date(jahr, 1, 1) + timedelta(days=i) for i in range((date(jahr + 1, 1, 1) - date(jahr, 1, 1)).days)]
        soll = numpy_nummern(tage, [date.fromisoformat(x) for x in schliess], wochenmaske(boerse))
        ist = handelstag_nummern(tage, boerse)
        abw = [(t.isoformat(), tuple(i), s) for t, i, s in zip(tage, ist, soll) if tuple(i) != s]
        pruefe(f"Sollkalender {boerse} {jahr}", not abw,
               f"{len(abw)} Tage weichen ab, erster: {abw[0] if abw else ''}")
    # Einzelwerte, die ein Leser nachzählen kann
    pruefe("Sollkalender XETRA 2018-10-04", tuple(handelstag_nummern(["2018-10-04"], "XETRA")[0])
           == (3, 193, -20, -59, True), "erwartet (3, 193, -20, -59, offen)")
    pruefe("Sollkalender CRYPTO 2026-01-31", tuple(handelstag_nummern(["2026-01-31"], "CRYPTO")[0])
           == (31, 31, -1, -335, True), "Krypto zählt jeden Kalendertag")


def wirft(f) -> bool:
    try:
        f()
    except ValueError:
        return True
    return False


def block_vertrag() -> None:
    h = handelstag_nummern
    pruefe("Vertrag unbekannte Börse", wirft(lambda: h(["2026-01-02"], "FOO")))
    pruefe("Vertrag unbekannte Börse bei leerer Eingabe", wirft(lambda: h([], "FOO")))
    pruefe("Vertrag Börse leer/None", wirft(lambda: h([], "")) and wirft(lambda: h([], None)))
    pruefe("Vertrag NASDAQ = NYSE, Groß/Klein", h(["2025-01-09"], "nasdaq") == h(["2025-01-09"], "NYSE"))
    pruefe("Vertrag datetime abgelehnt", wirft(lambda: h([datetime(2026, 1, 2)], "NYSE")))
    pruefe("Vertrag Basisformat 20260102 abgelehnt", wirft(lambda: h(["20260102"], "NYSE")))
    pruefe("Vertrag Wochenformat abgelehnt", wirft(lambda: h(["2026-W01-5"], "NYSE")))
    pruefe("Vertrag Zahl abgelehnt", wirft(lambda: h([20260102], "NYSE")))
    pruefe("Vertrag Jahr außerhalb", wirft(lambda: h(["1800-01-02"], "NYSE")) and wirft(lambda: h(["2101-01-03"], "NYSE")))
    pruefe("Vertrag leer → leer", h([], "NYSE") == [])
    # Reihenfolge, Duplikate, unsortiert, mehrjährig
    eingabe = ["2026-03-02", "2024-12-31", "2026-03-02", "2025-01-02"]
    einzeln = [h([x], "XETRA")[0] for x in eingabe]
    pruefe("Vertrag Reihenfolge/Duplikate/mehrjährig", h(eingabe, "XETRA") == einzeln)
    pruefe("Vertrag date == ISO-Text", h([date(2026, 3, 2)], "XETRA") == h(["2026-03-02"], "XETRA"))
    # Geschlossene Tage
    n = h(["2026-01-01", "2026-02-01", "2026-10-03"], "XETRA")   # Neujahr, Sonntag nach Monatsbeginn, Samstag
    pruefe("Vertrag geschlossen vor erstem Handelstag = 0", (n[0].tdom, n[0].tdoy, n[0].offen) == (0, 0, False))
    pruefe("Vertrag geschlossen nach Monatswechsel tdom 0, tdoy läuft weiter", (n[1].tdom, n[1].offen) == (0, False)
           and n[1].tdoy == h(["2026-01-30"], "XETRA")[0].tdoy)
    pruefe("Vertrag geschlossen ohne Rückwärtszahl", all(x.tdom_rev is None and x.tdoy_rev is None for x in n))
    pruefe("Vertrag geschlossen = Vortag", (n[2].tdom, n[2].tdoy) == tuple(h(["2026-10-02"], "XETRA")[0][:2]))
    # Periodensummen: am letzten Handelstag −1, am ersten −Summe
    for boerse in ("NYSE", "XETRA", "TSE", "LSE", "HKEX", "FOREX", "CRYPTO"):
        for jahr in (2001, 2016, 2024, 2026):
            tage = [date(jahr, 1, 1) + timedelta(days=i) for i in range((date(jahr + 1, 1, 1) - date(jahr, 1, 1)).days)]
            nn = [x for x in h(tage, boerse) if x.offen]
            pruefe(f"Vertrag Jahressumme {boerse} {jahr}",
                   nn[0].tdoy == 1 and nn[-1].tdoy_rev == -1 and nn[0].tdoy_rev == -len(nn) and nn[-1].tdoy == len(nn))
    # Ein Ergebnis darf den Cache nicht verändern können
    a = h(["2026-03-02"], "XETRA")[0]
    pruefe("Vertrag Ergebnis unveränderlich", wirft_typ(lambda: a.__setitem__(0, 99)))
    pruefe("Vertrag Cache je Börse getrennt", h(["2026-12-24"], "XETRA")[0].offen is False
           and h(["2026-12-24"], "NYSE")[0].offen is True)


def wirft_typ(f) -> bool:
    try:
        f()
    except (TypeError, AttributeError):
        return True
    return False


# Wörtliche Soll-Spezifikation des Kalenderstatus als Bruchpunkte: ab Jahr X gilt Status S
# (bis zum nächsten Bruchpunkt). Bewusst NICHT aus KALENDER_GUELTIG abgeleitet — jede
# verschobene Grenze (Codex Paket 2: XETRA „belegt“ bis 2100 blieb grün) muss hier auffallen.
STATUS_SOLL = {
    "NYSE":      [(1885, "ungeprueft"), (1971, "belegt"), (2029, "annahme")],
    "XETRA":     [(1885, "ungeprueft"), (2001, "annahme"), (2002, "belegt"), (2027, "annahme")],
    "LSE":       [(1885, "ungeprueft"), (2000, "annahme"), (2026, "belegt"), (2029, "annahme")],
    "TSE":       [(1885, "ungeprueft"), (2000, "annahme"), (2001, "belegt"), (2028, "annahme")],
    "EURONEXT":  [(1885, "ungeprueft"), (2000, "annahme")],
    "SIX":       [(1885, "ungeprueft"), (2000, "annahme")],
    "MILAN":     [(1885, "ungeprueft"), (2000, "annahme")],
    "STOCKHOLM": [(1885, "ungeprueft"), (2000, "annahme")],
    "OSLO":      [(1885, "ungeprueft"), (2000, "annahme")],
    "HKEX":      [(1885, "ungeprueft"), (2016, "annahme"), (2026, "belegt"), (2027, "ungeprueft")],
    "KRX":       [(1885, "ungeprueft"), (2016, "annahme"), (2027, "ungeprueft")],
    "FOREX":     [(1885, "konvention")],
    "CRYPTO":    [(1885, "konvention")],
}


def block_status() -> None:
    pruefe("Status alle Börsen erfasst", set(STATUS_SOLL) == set(_EXCHANGE_FUNCTIONS) - {"NASDAQ"},
           f"Soll {sorted(STATUS_SOLL)} gegen Kalender {sorted(_EXCHANGE_FUNCTIONS)}")
    for boerse, bruch in STATUS_SOLL.items():
        abw = []
        for jahr in range(1885, 2101):
            soll = [s for von, s in bruch if von <= jahr][-1]
            ist = kalender_status(boerse, jahr)
            if ist != soll:
                abw.append(f"{jahr}: soll {soll}, ist {ist}")
        pruefe(f"Status {boerse} 1885–2100", not abw, f"{len(abw)} Jahre, erstes: {abw[0] if abw else ''}")
    pruefe("Status NASDAQ = NYSE", kalender_status("nasdaq", 2020) == kalender_status("NYSE", 2020))
    pruefe("Status XETRA 2001 Annahme", kalender_status("XETRA", 2001) == "annahme")
    pruefe("Status HKEX außerhalb Tabelle", kalender_status("HKEX", 2010) == "ungeprueft")
    pruefe("Status KRX 2026 nur Annahme", kalender_status("KRX", 2026) == "annahme")
    pruefe("Status Konvention", kalender_status("FOREX", 2000) == "konvention" and kalender_status("CRYPTO", 2030) == "konvention")
    pruefe("Status unbekannte Börse", wirft(lambda: kalender_status("FOO", 2020)))


def main() -> int:
    for name, block in (("Arithmetik", block_arithmetik), ("Sollkalender", block_sollkalender),
                        ("Vertrag", block_vertrag), ("Status", block_status)):
        try:
            block()
        except Exception as e:  # eine Ausnahme ist nie ein Nachweis
            FEHLER.append(f"[Ausnahme] Block {name}: {type(e).__name__}: {e}")
    print(f"verify_handelstag_nummern: {ZAEHLER['n'] - len(FEHLER)}/{ZAEHLER['n']} Prüfungen bestanden")
    for f in FEHLER:
        print("  FEHL", f)
    print(f"PROBE-ENDE {ZAEHLER['n']} Pruefungen")
    return 1 if FEHLER else 0


if __name__ == "__main__":
    sys.exit(main())
