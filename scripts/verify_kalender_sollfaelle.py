#!/usr/bin/env python3
"""
Wächter: Börsenkalender gegen belegte Sollfälle (offen UND geschlossen).

Prüft `shared.exchange_holidays.is_trading_day` gegen eine wörtliche Liste von Tagen,
deren Status eine offizielle Quelle belegt. Die Liste ist bewusst NICHT aus dem Code
abgeleitet: ein Zwillingsvergleich oder eine Zählung mit denselben Feiertagen kann einen
falschen Feiertag nicht finden (Lesson 1B: zwei Zwillinge folgten derselben falschen Regel).

Quellen-Kürzel (Details und Links in docs/review_prompts/2026-10-10_xetra_tdoy_plan_antwort4.md):
  L1 LSE Business Days + gov.uk/bank-holidays (Ersatzregel)   L2-L4 London Gazette
  J1 NAOJ-Gesetzesänderungen  J3 JPX 2019  J4/J5 NAOJ 2020/2021 (revidiert)  J6 JPX 2020-10-01
  K1 KRX-KIND-Meldungen (Handelstag belegt)  K2 amtlicher Kalender 2016
  H1 HKEX-Wertpapierkalender 2016
  N1 NYSE "Holidays & Closings" + fehlender Tageskurs ^GSPC/^DJI (election_calendar_exceptions.json)
  X1 Deutsche Börse Handelskalender (2012 selbst gelesen, 2018 + Eurex-Rundschreiben 055/2018)

Aufruf:  py -3.14 scripts/verify_kalender_sollfaelle.py     Exit 0 = alle Sollfälle erfüllt
"""
from __future__ import annotations

import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.exchange_holidays import is_trading_day  # noqa: E402

ZU, OFFEN = False, True

# (Börse, Datum, Soll, Quelle, Anlass) — wörtlich, nicht aus dem Code erzeugt.
SOLLFAELLE: list[tuple[str, str, bool, str, str]] = [
    # ── LSE: Ersatztage und Einmaltage ──
    ("LSE", "2000-01-03", ZU, "L2", "Neujahrsersatz (1.1. Samstag)"),
    ("LSE", "2002-06-03", ZU, "L3", "Golden Jubilee, zusätzlicher Tag"),
    ("LSE", "2002-06-04", ZU, "L3", "Spring Bank Holiday verlegt"),
    ("LSE", "2004-12-28", ZU, "L1", "Boxing-Day-Ersatz (25.12. Samstag)"),
    ("LSE", "2005-01-03", ZU, "L1", "Neujahrsersatz"),
    ("LSE", "2010-12-27", ZU, "L1", "Weihnachtsersatz"),
    ("LSE", "2010-12-28", ZU, "L1", "Boxing-Day-Ersatz"),
    ("LSE", "2011-01-03", ZU, "L1", "Neujahrsersatz"),
    ("LSE", "2011-04-29", ZU, "L4", "Royal Wedding"),
    ("LSE", "2021-12-28", ZU, "L1", "Boxing-Day-Ersatz"),
    ("LSE", "2022-01-03", ZU, "L1", "Neujahrsersatz"),
    ("LSE", "2027-12-28", ZU, "L1", "Boxing-Day-Ersatz (veröffentlichter Plan)"),
    ("LSE", "2028-01-03", ZU, "L1", "Neujahrsersatz (veröffentlichter Plan)"),
    ("LSE", "2009-12-28", ZU, "L1", "Gegenprobe: Ersatz-Montag bei 26.12. Samstag"),
    ("LSE", "2016-12-27", ZU, "L1", "Gegenprobe: Weihnachtsersatz bei 25.12. Sonntag"),
    ("LSE", "2022-09-19", ZU, "L1", "Staatsbegräbnis Elizabeth II."),
    ("LSE", "2023-05-08", ZU, "L1", "Krönung Charles III."),
    ("LSE", "2010-12-29", OFFEN, "L1", "Gegenprobe: Tag nach den Ersatztagen"),
    ("LSE", "2021-12-29", OFFEN, "L1", "Gegenprobe"),
    ("LSE", "2000-04-05", OFFEN, "L1", "Ausfall nur vormittags, Nachmittag gehandelt"),
    # ── TSE: historische Regeln, Thronwechsel, Olympia, Systemausfall ──
    ("TSE", "2000-07-17", OFFEN, "J1", "Meerestag damals fest 20.7."),
    ("TSE", "2000-07-20", ZU, "J1", "Meerestag"),
    ("TSE", "2000-09-15", ZU, "J1", "Tag der Alten, fest bis 2002"),
    ("TSE", "2000-09-18", OFFEN, "J1", "Montagsregel erst ab 2003"),
    ("TSE", "2001-07-16", OFFEN, "J1", "Meerestag damals fest 20.7."),
    ("TSE", "2001-07-20", ZU, "J1", "Meerestag"),
    ("TSE", "2001-09-17", OFFEN, "J1", "15.9. Samstag, kein Montagsersatz"),
    ("TSE", "2002-07-15", OFFEN, "J1", "Montagsregel erst ab 2003"),
    ("TSE", "2003-05-06", OFFEN, "J1", "Ersatzregel vor 2007"),
    # Regelgrenzen (Codex Paket-1-Review, Befund 2): je ein Paar vor/nach dem Regelwechsel.
    ("TSE", "1971-10-11", OFFEN, "J1", "Ersatztag-Regel erst ab 1973 (10.10.1971 Sonntag)"),
    ("TSE", "1973-04-30", ZU, "J1", "erster Ersatztag (29.4.1973 Sonntag)"),
    ("TSE", "1995-07-20", OFFEN, "J1", "Meerestag erst ab 1996"),
    ("TSE", "1999-01-11", OFFEN, "J1", "Seijin no Hi bis 1999 fest 15.1."),
    ("TSE", "1999-01-15", ZU, "J1", "Seijin no Hi 1999"),
    ("TSE", "1997-10-10", ZU, "J1", "Taiiku no Hi bis 1999 fest 10.10."),
    ("TSE", "1997-10-13", OFFEN, "J1", "Taiiku no Hi erst ab 2000 am 2. Montag"),
    # Kokumin no Kyujitsu zwischen Keiro no Hi und Shubun no Hi (Befund 1).
    ("TSE", "2009-09-22", ZU, "J1", "Brückentag Silver Week"),
    ("TSE", "2015-09-22", ZU, "J1", "Brückentag Silver Week"),
    ("TSE", "2026-09-22", ZU, "J1", "Brückentag Silver Week"),
    ("TSE", "2010-09-21", OFFEN, "J1", "Gegenprobe: kein Brückentag (20.9. und 23.9.)"),
    ("TSE", "2019-04-30", ZU, "J3", "Thronwechsel (Brückentag)"),
    ("TSE", "2019-05-01", ZU, "J3", "Thronbesteigung"),
    ("TSE", "2019-05-02", ZU, "J3", "Thronwechsel (Brückentag)"),
    ("TSE", "2019-10-22", ZU, "J3", "Inthronisierung"),
    ("TSE", "2019-12-23", OFFEN, "J3", "Kaisergeburtstag 2019 entfällt"),
    ("TSE", "2020-07-20", OFFEN, "J4", "Meerestag verlegt"),
    ("TSE", "2020-07-23", ZU, "J4", "Meerestag (Olympia)"),
    ("TSE", "2020-07-24", ZU, "J4", "Sporttag (Olympia)"),
    ("TSE", "2020-08-10", ZU, "J4", "Bergtag (Olympia)"),
    ("TSE", "2020-08-11", OFFEN, "J4", "Bergtag verlegt"),
    ("TSE", "2020-10-01", ZU, "J6", "Ganztägiger Systemausfall"),
    ("TSE", "2020-10-12", OFFEN, "J4", "Sporttag verlegt"),
    ("TSE", "2021-07-19", OFFEN, "J5", "Meerestag verlegt"),
    ("TSE", "2021-07-22", ZU, "J5", "Meerestag (Olympia)"),
    ("TSE", "2021-07-23", ZU, "J5", "Sporttag (Olympia)"),
    ("TSE", "2021-08-09", ZU, "J5", "Ersatz für Bergtag am Sonntag 8.8."),
    ("TSE", "2021-08-11", OFFEN, "J5", "Bergtag verlegt"),
    ("TSE", "2021-10-11", OFFEN, "J5", "Sporttag verlegt"),
    # ── HKEX / KRX ──
    ("HKEX", "2016-01-01", ZU, "H1", "Neujahr"),
    ("KRX", "2016-01-01", ZU, "K2", "Neujahr"),
    ("KRX", "2017-09-22", OFFEN, "K1", "Handelstag laut KRX-Meldung"),
    ("KRX", "2017-12-20", OFFEN, "K1", "Handelstag laut KRX-Preisberechnung"),
    ("KRX", "2022-01-03", OFFEN, "K1", "ausdrücklich dritter Handelstag des Jahres"),
    ("KRX", "2022-05-09", OFFEN, "K1", "Handelsvolumen gemeldet"),
    ("KRX", "2026-07-17", ZU, "K1", "Verfassungstag ab 2026 wieder Feiertag"),
    # ── NYSE: Sonderschließungen ab 1971 ──
    ("NYSE", "1972-11-07", ZU, "N1", "Präsidentschaftswahl"),
    ("NYSE", "1972-12-28", ZU, "N1", "Staatstrauer Truman"),
    ("NYSE", "1973-01-25", ZU, "N1", "Staatstrauer Johnson"),
    ("NYSE", "1976-11-02", ZU, "N1", "Präsidentschaftswahl"),
    ("NYSE", "1977-07-14", ZU, "N1", "Stromausfall"),
    ("NYSE", "1980-11-04", ZU, "N1", "Präsidentschaftswahl"),
    ("NYSE", "1985-09-27", ZU, "N1", "Hurrikan Gloria"),
    ("NYSE", "1994-04-27", ZU, "N1", "Staatstrauer Nixon"),
    ("NYSE", "2025-01-09", ZU, "N1", "Staatstrauer Carter"),
    ("NYSE", "1984-11-06", OFFEN, "N1", "Gegenprobe: Wahltag ab 1984 gehandelt"),
    # ── XETRA ──
    ("XETRA", "2011-10-03", OFFEN, "X1", "Tag der Einheit 2011 gehandelt"),
    ("XETRA", "2012-10-03", OFFEN, "X1", "Tag der Einheit 2012 gehandelt"),
    ("XETRA", "2013-10-03", OFFEN, "X1", "Tag der Einheit 2013 gehandelt"),
    ("XETRA", "2012-05-28", OFFEN, "X1", "Pfingstmontag 2012 gehandelt"),
    ("XETRA", "2012-12-24", ZU, "X1", "Heiligabend"),
    ("XETRA", "2008-12-24", ZU, "X1", "Heiligabend"),
    ("XETRA", "2018-05-21", ZU, "X1", "Pfingstmontag 2018 geschlossen"),
    ("XETRA", "2018-10-03", ZU, "X1", "Tag der Einheit 2018 geschlossen"),
    # ── Projektkonventionen ──
    ("FOREX", "2026-10-10", ZU, "Konvention", "Samstag"),
    ("FOREX", "2026-12-25", OFFEN, "Konvention", "Mo–Fr ohne Feiertage"),
    ("CRYPTO", "2026-10-10", OFFEN, "Konvention", "täglich"),
]


def main() -> int:
    fehler = []
    for boerse, iso, soll, quelle, anlass in SOLLFAELLE:
        kennung = f"{boerse} {iso}"
        try:
            ist = is_trading_day(date.fromisoformat(iso), boerse)
        except Exception as e:  # eine Ausnahme ist nie ein Nachweis (Beweisregel 5)
            fehler.append(f"[Ausnahme] {kennung}: {type(e).__name__}: {e}")
            continue
        if ist != soll:
            fehler.append(f"[{kennung}] soll {'offen' if soll else 'zu'}, ist {'offen' if ist else 'zu'}"
                          f" — {anlass} ({quelle})")
    print(f"Kalender-Sollfälle: {len(SOLLFAELLE) - len(fehler)}/{len(SOLLFAELLE)} erfüllt")
    for f in fehler:
        print("  FEHL", f)
    print(f"PROBE-ENDE {len(SOLLFAELLE)} Pruefungen")
    return 1 if fehler else 0


if __name__ == "__main__":
    sys.exit(main())
