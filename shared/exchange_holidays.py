# shared/exchange_holidays.py
# Börsenfeiertage für internationale Märkte.
#
# Unterstützte Börsen:
#   NYSE     — US (in nyse_holidays.py, hier als Wrapper)
#   XETRA    — Deutschland (DAX, MDAX, SDAX, TecDAX)
#   LSE      — London (FTSE 100, FTSE 250)
#   EURONEXT — Paris (CAC 40)
#   TSE      — Tokyo (Nikkei 225, TOPIX)
#
# Logik:
#   - Feste Feiertage regelbasiert berechnet
#   - Variable Feiertage (Ostern, Goldene Woche etc.) algorithmisch
#   - Auto-Erweiterung: funktioniert für jedes Jahr ohne Update
#   - Ticker → Börse: shared.symbols.get_exchange_for_holidays (einzige Zuordnung)
#
# Import-Beispiel:
#   from shared.exchange_holidays import get_holidays, is_holiday, is_trading_day, handelstag_nummern
#   Ticker → Börse: shared.symbols.get_exchange_for_holidays

from datetime import date, timedelta
import calendar
import re
from shared.nyse_holidays import (
    _easter_sunday,
    _good_friday,
    _nth_weekday,
    _observed,
    _monday_if_sunday,
    get_nyse_holidays,
)

# Ticker → Börse: NUR über shared.symbols.get_exchange_for_holidays. Hier stand bis
# 2026-10-10 eine zweite Zuordnung (TICKER_TO_EXCHANGE/_TICKER_MAP) mit NYSE-Ersatz, die
# `SAP.DE` als NYSE und `SAP` (US-ADR) als XETRA führte (Codex Runde 3, Befund 3).


# ── Gemeinsame Helfer ──────────────────────────────────────────────────────────

def _whit_monday(year: int) -> date:
    """Pfingstmontag = Ostersonntag + 50 Tage (Pfingstsonntag + 1)."""
    return _easter_sunday(year) + timedelta(days=50)

def _easter_monday(year: int) -> date:
    """Ostermontag = Ostersonntag + 1."""
    return _easter_sunday(year) + timedelta(days=1)

def _ascension_day(year: int) -> date:
    """Christi Himmelfahrt = Ostersonntag + 39 Tage."""
    return _easter_sunday(year) + timedelta(days=39)

def _corpus_christi(year: int) -> date:
    """Fronleichnam = Ostersonntag + 60 Tage."""
    return _easter_sunday(year) + timedelta(days=60)


# ── XETRA (Deutschland) ────────────────────────────────────────────────────────

def _compute_xetra_holidays(year: int) -> list[date]:
    """
    XETRA/Frankfurt handelsfreie Tage (Deutsche Börse Cash Market).

    Regel: Neujahr, Karfreitag, Ostermontag, 1. Mai, 25./26. Dezember, ab 2001 auch 24./31. Dezember.
    In der Regel HANDELT Xetra an Pfingstmontag, Christi Himmelfahrt, Fronleichnam und am 3. Oktober —
    mit belegten Ausnahmejahren in XETRA_SONDER.
    ⚠️ KEIN Observed-Shift: fällt ein Feiertag aufs Wochenende, gibt es KEINEN
       Montags-Ersatz (anders als NYSE/LSE). Daher feste Daten, kein _observed.

    Korrektur 2026-10-08 (Codex-Recherche, Plan /plain-vanilla 1B): die frühere Regel „24./31.12. erst ab 2011"
    war falsch — die offiziellen Handelskalender 2003, 2004, 2007–2010 und das Eurex-Rundschreiben 087/02 (2002)
    führen beide Tage als geschlossen. 2001: 31.12. durch eine zeitgenössische UPI-Meldung belegt, für den
    24.12.2001 gibt es KEINE Primärquelle — geschlossen geführt als dokumentierte Annahme (Kalender 2002–2010,
    Kursbestand ohne Zeile). Vor 2001 bleibt das bisherige Verhalten (offen), weil dafür nichts geprüft ist.
    Zwilling: landing/js/holidays.js::_xetra, Prüfung scripts/verify_kalender_zwilling.py (feste Sollwerte).
    """
    # Regeln seit V1c-1 im Ereigniskatalog (Vertrag B4); diese Funktion ist die Kompatibilitätsprojektion.
    from shared.boersenereignisse import kompat
    return sorted(kompat("XETRA", year))


# Belegte einmalige Xetra-Schließungen (Quellen: Codex-Recherche 2026-10-08,
# docs/review_prompts/2026-10-08_plain_vanilla_1b_plan_antwort1.md). Zwilling: holidays.js::_XETRA_SONDER.
XETRA_SONDER = [
    date(2000, 10, 3),    # 10 Jahre Deutsche Einheit — Mitteilung Deutsche Börse (Mondo Visione)
    date(2007, 5, 28),    # Pfingstmontag — FWB-Rundschreiben 18/2006
    date(2014, 10, 3),    # Handelskalender 2014
    date(2015, 5, 25),    # Pfingstmontag — Handelskalender 2015
    date(2016, 5, 16),    # Pfingstmontag — Handelskalender 2016
    date(2016, 10, 3),    # Handelskalender 2016
    date(2017, 6, 5),     # Pfingstmontag — Eurex-Rundschreiben 128/16 (FWB-Beschluss)
    date(2017, 10, 3),    # Eurex-Rundschreiben 128/16
    date(2017, 10, 31),   # Reformationstag (500 Jahre) — Eurex-Rundschreiben 128/16
    date(2018, 5, 21),    # Pfingstmontag — Handelskalender 2018
    date(2018, 10, 3),    # Handelskalender 2018
    date(2019, 6, 10),    # Pfingstmontag — Xetra-Handelskalender 2019
    date(2019, 10, 3),    # Xetra-Handelskalender 2019
    date(2020, 6, 1),     # Pfingstmontag — Xetra-Handelskalender 2020
    date(2021, 5, 24),    # Pfingstmontag — Xetra-Handelskalender 2021
]


# ── LSE (London) ───────────────────────────────────────────────────────────────

def _compute_lse_holidays(year: int) -> list[date]:
    """
    LSE London Stock Exchange Feiertage (England & Wales Bank Holidays).
    """
    # Regeln seit V1c-1 im Ereigniskatalog (Vertrag B4); diese Funktion ist die Kompatibilitätsprojektion.
    from shared.boersenereignisse import kompat
    return sorted(kompat("LSE", year))


# ── Euronext Paris (CAC 40) ────────────────────────────────────────────────────

def _compute_euronext_holidays(year: int) -> list[date]:
    """
    Euronext-Handelskalender (Paris, Amsterdam, Brüssel, Lissabon, seit 2021
    auch Mailand/Borsa Italiana).

    WICHTIG: Euronext ist seit der Harmonisierung NUR an 6 Tagen geschlossen —
    NICHT an den nationalen Feiertagen der einzelnen Länder. Insbesondere wird
    DURCHGEHANDELT an: Pfingstmontag, Christi Himmelfahrt, 8. Mai, 14. Juli
    (Bastille), 15. August (Mariä Himmelfahrt), 1. November (Allerheiligen),
    11. November (Waffenstillstand). Diese fälschlich als Feiertag zu führen
    erzeugte Geister-Lücken + falsche TDOM/TDOY für alle .PA/.MI/.AS-Ticker.

    KEIN Observed-Shift: fällt ein Feiertag aufs Wochenende, kein Montags-Ersatz.
    """
    # Regeln seit V1c-1 im Ereigniskatalog (Vertrag B4); diese Funktion ist die Kompatibilitätsprojektion.
    from shared.boersenereignisse import kompat
    return sorted(kompat("EURONEXT", year))


# ── Borsa Italiana (Mailand) ───────────────────────────────────────────────────

def _compute_milan_holidays(year: int) -> list[date]:
    """
    Borsa Italiana (Mailand) — seit 2021 Teil von Euronext, handelt daher den
    Euronext-Kern. ABER drei italienische Besonderheiten, an denen Mailand
    ZUSÄTZLICH schließt (datenbestätigt für .MI-Ticker): Ferragosto (15.8.),
    Heiligabend (24.12.) und Silvester (31.12.). Andere ital. Feiertage
    (6.1./25.4./2.6./8.12.) handelt Mailand durch (Euronext-Harmonisierung).
    """
    # Regeln seit V1c-1 im Ereigniskatalog (Vertrag B4); diese Funktion ist die Kompatibilitätsprojektion.
    from shared.boersenereignisse import kompat
    return sorted(kompat("MILAN", year))


# ── TSE (Tokyo Stock Exchange) ─────────────────────────────────────────────────

# Olympia 2020/2021: Meeres-, Sport- und Bergtag per Sondergesetz verlegt
# (NAOJ-Kalender 2020/2021, revidiert). Ersetzt die Regeltermine dieser drei Feiertage.
_TSE_OLYMPIA = {
    2020: (date(2020, 7, 23), date(2020, 7, 24), date(2020, 8, 10)),
    2021: (date(2021, 7, 22), date(2021, 7, 23), date(2021, 8, 8)),   # 8.8. Sonntag → Ersatz 9.8.
}
# Einmalige nationale Feiertage (zählen für Ersatz- und Brückentage mit).
_TSE_EINMALIG_FEIERTAG = {
    2019: (date(2019, 5, 1), date(2019, 10, 22)),   # Thronbesteigung, Inthronisierung (JPX 2019-01-15)
}
# Börse geschlossen ohne Feiertag.
_TSE_BOERSE_GESCHLOSSEN = {
    2020: (date(2020, 10, 1),),   # ganztägiger Systemausfall arrowhead (JPX-Mitteilung 2020-10-01)
}



def _compute_tse_holidays(year: int) -> list[date]:
    """
    TSE Tokyo Stock Exchange Feiertage (japanische Nationalfeiertage).
    Japanische Besonderheit: Wenn Feiertag auf Sonntag fällt → Montag (振替休日).
    Wenn zwei Feiertage einen normalen Tag einschließen → auch dieser ist frei (国民の休日).
    """
    # Regeln seit V1c-1 im Ereigniskatalog (Vertrag B4); diese Funktion ist die Kompatibilitätsprojektion.
    from shared.boersenereignisse import kompat
    return sorted(kompat("TSE", year))


# ── SIX (Schweiz) ──────────────────────────────────────────────────────────────

def _compute_six_holidays(year: int) -> list[date]:
    """SIX Swiss Exchange Feiertage — Schweizer Bundesfeiertage."""
    # Regeln seit V1c-1 im Ereigniskatalog (Vertrag B4); diese Funktion ist die Kompatibilitätsprojektion.
    from shared.boersenereignisse import kompat
    return sorted(kompat("SIX", year))


# ── Nasdaq Stockholm ───────────────────────────────────────────────────────────

def _compute_stockholm_holidays(year: int) -> list[date]:
    """Nasdaq Stockholm handelsfreie Tage — KEIN Observed-Shift (feste Daten)."""
    # Regeln seit V1c-1 im Ereigniskatalog (Vertrag B4); diese Funktion ist die Kompatibilitätsprojektion.
    from shared.boersenereignisse import kompat
    return sorted(kompat("STOCKHOLM", year))


def _compute_oslo_holidays(year: int) -> list[date]:
    """Oslo Børs (Euronext-Oslo) handelsfreie Tage — Norwegen-Kalender, KEIN
    Observed-Shift (feste Daten). Weicht vom Stockholm-Proxy an mehreren Tagen ab:
    Oslo schließt **Skjærtorsdag (Gründonnerstag)** + **2. pinsedag (Pfingstmontag)**
    (Stockholm handelt beide), Oslo HANDELT dagegen am 6.1., 6.6. und Midsommar
    (Stockholm zu). Grunnlovsdag 17.5. ist Oslo-spezifisch."""
    # Regeln seit V1c-1 im Ereigniskatalog (Vertrag B4); diese Funktion ist die Kompatibilitätsprojektion.
    from shared.boersenereignisse import kompat
    return sorted(kompat("OSLO", year))


# ── HKEX (Hongkong) + KRX (Korea) ──────────────────────────────────────────────
# Mondkalender-Feiertage (Lunar New Year, Buddha's Birthday, Mid-Autumn, Chuseok,
# Seollag …) + unregelmäßige Schließungen (Taifune, Wahltage) sind NICHT regel-
# basiert berechenbar → Tabelle. Sie stammte ursprünglich aus Kurslücken in ^HSI/^KS11
# — und eine fehlende Kurszeile ist KEIN Schließungsbeleg: KRX trug so vier Handelstage
# als Feiertag (2017-09-22, 2017-12-20, 2022-01-03, 2022-05-09; Gegenbelege aus KRX-KIND),
# beiden fehlte der 1.1.2016. Korrigiert 2026-10-10 (plan_antwort4.md). Neue Einträge NUR
# aus dem offiziellen HKEX/KRX-Kalender, nie aus fehlenden Kursen.

_HKEX_HOLIDAYS = {
    2016: [(1,1),(2,8),(2,9),(2,10),(3,25),(3,28),(4,4),(5,2),(6,9),(7,1),(8,2),(9,16),(10,10),(10,21),(12,26),(12,27)],
    2017: [(1,2),(1,30),(1,31),(4,4),(4,14),(4,17),(5,1),(5,3),(5,30),(8,23),(10,2),(10,5),(12,25),(12,26)],
    2018: [(1,1),(2,16),(2,19),(3,30),(4,2),(4,5),(5,1),(5,22),(6,18),(7,2),(9,25),(10,1),(10,17),(12,25),(12,26)],
    2019: [(1,1),(2,5),(2,6),(2,7),(4,5),(4,19),(4,22),(5,1),(5,13),(6,7),(7,1),(10,1),(10,7),(12,25),(12,26)],
    2020: [(1,1),(1,27),(1,28),(4,10),(4,13),(4,30),(5,1),(6,25),(7,1),(10,1),(10,2),(10,13),(10,26),(12,25)],
    2021: [(1,1),(2,12),(2,15),(4,2),(4,5),(4,6),(5,19),(6,14),(7,1),(9,22),(10,1),(10,13),(10,14),(12,27)],
    2022: [(2,1),(2,2),(2,3),(4,5),(4,15),(4,18),(5,2),(5,9),(6,3),(7,1),(9,12),(10,4),(12,26),(12,27)],
    2023: [(1,2),(1,23),(1,24),(1,25),(4,5),(4,7),(4,10),(5,1),(5,26),(6,22),(7,17),(9,1),(9,8),(10,2),(10,23),(12,25),(12,26)],
    2024: [(1,1),(2,12),(2,13),(3,29),(4,1),(4,4),(5,1),(5,15),(6,10),(7,1),(9,6),(9,18),(10,1),(10,11),(12,25),(12,26)],
    2025: [(1,1),(1,29),(1,30),(1,31),(4,4),(4,18),(4,21),(5,1),(5,5),(7,1),(10,1),(10,7),(10,29),(12,25),(12,26)],
    # 2026 vollständig (Quelle: calendarlabs.com/hkex + gov.hk). Sa-Einträge (9,26),(12,26)
    # sind im is_trading_day()-Pfad harmlos (weekday >= 5 filtert sie bereits raus).
    2026: [(1,1),(2,17),(2,18),(2,19),(4,3),(4,6),(4,7),(5,1),(5,25),(6,19),(7,1),(9,26),(10,1),(10,19),(12,25),(12,26)],
}

_KRX_HOLIDAYS = {
    2016: [(1,1),(2,8),(2,9),(2,10),(3,1),(4,13),(5,5),(5,6),(6,6),(8,15),(9,14),(9,15),(9,16),(10,3),(12,30)],
    2017: [(1,27),(1,30),(3,1),(5,1),(5,3),(5,5),(5,9),(6,6),(8,15),(10,2),(10,3),(10,4),(10,5),(10,6),(10,9),(12,25),(12,29)],
    2018: [(1,1),(2,15),(2,16),(3,1),(5,1),(5,7),(5,22),(6,6),(6,13),(8,15),(9,24),(9,25),(9,26),(10,3),(10,9),(12,25),(12,31)],
    2019: [(1,1),(2,4),(2,5),(2,6),(3,1),(5,1),(5,6),(6,6),(8,15),(9,12),(9,13),(10,3),(10,9),(12,25),(12,31)],
    2020: [(1,1),(1,24),(1,27),(4,15),(4,30),(5,1),(5,5),(8,17),(9,30),(10,1),(10,2),(10,9),(12,25),(12,31)],
    2021: [(1,1),(2,11),(2,12),(3,1),(5,5),(5,19),(8,16),(9,20),(9,21),(9,22),(10,4),(10,11),(12,31)],
    2022: [(1,31),(2,1),(2,2),(3,1),(3,9),(5,5),(6,1),(6,6),(8,15),(9,9),(9,12),(10,3),(10,10),(12,30)],
    2023: [(1,23),(1,24),(3,1),(5,1),(5,5),(5,29),(6,6),(8,15),(9,28),(9,29),(10,2),(10,3),(10,9),(12,25),(12,29)],
    2024: [(1,1),(2,9),(2,12),(3,1),(4,10),(5,1),(5,6),(5,15),(6,6),(8,15),(9,16),(9,17),(9,18),(10,1),(10,3),(10,9),(12,25),(12,31)],
    2025: [(1,1),(1,27),(1,28),(1,29),(1,30),(3,3),(5,1),(5,5),(5,6),(6,3),(6,6),(8,15),(10,3),(10,6),(10,7),(10,8),(10,9),(12,25),(12,31)],
    # 2026 vollständig (Quelle: calendarlabs.com/krx + kstockguide.com). Highlights:
    # (7,17) 제헌절 Constitution Day (ab 2026 wieder Feiertag), (8,17) Vertretungstag
    # für 광복절 15.8. (Samstag→Montag), (10,5) Vertretungstag für 개천절 3.10. (Samstag→Montag).
    2026: [(1,1),(2,16),(2,17),(2,18),(3,2),(5,1),(5,5),(5,25),(6,3),(7,17),(8,17),(9,24),(9,25),(10,5),(10,9),(12,25),(12,31)],
}


def _compute_hkex_holidays(year: int) -> list[date]:
    """HKEX (Hongkong). Tabellengestützt; Fallback = fixe gregorianische Feiertage."""
    # Regeln seit V1c-1 im Ereigniskatalog (Vertrag B4); diese Funktion ist die Kompatibilitätsprojektion.
    from shared.boersenereignisse import kompat
    return sorted(kompat("HKEX", year))


def _compute_krx_holidays(year: int) -> list[date]:
    """KRX (Korea). Tabellengestützt; Fallback = fixe gregorianische Feiertage."""
    # Regeln seit V1c-1 im Ereigniskatalog (Vertrag B4); diese Funktion ist die Kompatibilitätsprojektion.
    from shared.boersenereignisse import kompat
    return sorted(kompat("KRX", year))


# ── Haupt-API ──────────────────────────────────────────────────────────────────

_EXCHANGE_FUNCTIONS = {
    "NYSE":      lambda year: list(get_nyse_holidays(year, year)),
    "NASDAQ":    lambda year: list(get_nyse_holidays(year, year)),  # gleich wie NYSE
    "XETRA":     _compute_xetra_holidays,
    "LSE":       _compute_lse_holidays,
    "EURONEXT":  _compute_euronext_holidays,
    "TSE":       _compute_tse_holidays,
    "SIX":       _compute_six_holidays,         # Schweiz — eigener Kalender (Christi Himmelfahrt!)
    "MILAN":     _compute_milan_holidays,       # Borsa Italiana — Euronext + Ferragosto/24./31.12.
    "STOCKHOLM": _compute_stockholm_holidays,   # Schweden — eigener Kalender
    "OSLO":      _compute_oslo_holidays,        # Norwegen — eigener Kalender (Skjærtorsdag/Pfingstmontag!)
    "HKEX":      _compute_hkex_holidays,        # Hongkong — Mondkalender-Tabelle
    "KRX":       _compute_krx_holidays,         # Korea — Mondkalender-Tabelle
    "FOREX":     lambda year: [],               # Keine Feiertage (Mo-Fr 24h)
    "CRYPTO":    lambda year: [],               # Keine Feiertage (24/7)
}


def get_holidays(
    exchange: str,
    start_year: int,
    end_year: int,
) -> set[date]:
    """
    Gibt alle Börsenfeiertage einer Börse für einen Zeitraum zurück.

    Args:
        exchange   : Börsen-Kürzel ("NYSE","XETRA","LSE","EURONEXT","TSE")
        start_year : erstes Jahr (inklusiv)
        end_year   : letztes Jahr (inklusiv)

    Returns:
        set[date] — alle Feiertage im Zeitraum
    """
    fn = _EXCHANGE_FUNCTIONS[boerse_normalisieren(exchange)]   # unbekannt → ValueError, kein NYSE-Ersatz
    holidays = set()
    for year in range(start_year, end_year + 1):
        holidays.update(fn(year))
    return holidays


def is_holiday(d: date, exchange: str = "NYSE") -> bool:
    """Prüft ob ein Datum ein Feiertag an der gegebenen Börse ist (unbekannte Börse → ValueError)."""
    return d in _EXCHANGE_FUNCTIONS[boerse_normalisieren(exchange)](d.year)


def is_trading_day(d: date, exchange: str = "NYSE") -> bool:
    """Prüft ob ein Datum ein Handelstag ist (kein Wochenende, kein Feiertag).

    Sonderfaelle:
      - CRYPTO: 24/7, immer True (auch Sa/So)
      - FOREX:  Mo-Fr 24h, keine Feiertage (Sa/So geschlossen)
    Die Börse wird ZUERST geprüft — vorher lieferte eine unbekannte Börse am Samstag
    still False und unter der Woche den NYSE-Kalender.
    """
    exchange = boerse_normalisieren(exchange)
    if exchange == "CRYPTO":
        return True  # 24/7
    if d.weekday() >= 5:
        return False
    return not is_holiday(d, exchange)


# Handelsschluss je Börse in LOKALER Börsenzeit. Bewusst lokal und nicht in UTC:
# sonst muss die Sommerzeit zweimal im Jahr von Hand nachgezogen werden (NYSE
# schliesst 20:00 UTC im Sommer, 21:00 im Winter).
_SCHLUSSZEIT = {
    "NYSE": ("America/New_York", 16, 0),
    "XETRA": ("Europe/Berlin", 17, 30),
    "LSE": ("Europe/London", 16, 30),
    "EURONEXT": ("Europe/Paris", 17, 30),
    "MILAN": ("Europe/Rome", 17, 30),
    "SIX": ("Europe/Zurich", 17, 30),
    "STOCKHOLM": ("Europe/Stockholm", 17, 30),
    "OSLO": ("Europe/Oslo", 16, 20),
    "TSE": ("Asia/Tokyo", 15, 0),
    "HKEX": ("Asia/Hong_Kong", 16, 0),
    "KRX": ("Asia/Seoul", 15, 30),
}
_PUFFER_MIN = 15          # Kulanz für verzögerte EOD-Daten des Anbieters


def _uhr(tz):
    """Aktuelle Zeit in `tz`. Eigene Funktion, damit Wächter die Uhr festsetzen
    und die Sperren in den Crons tatsächlich AUSFÜHREN können — eine reine
    Quelltext-Suche ließ eine auskommentierte oder wirkungslose Sperre
    durch (Codex-Review 2026-09-25, R3)."""
    from datetime import datetime
    return datetime.now(tz)


def letzte_session(exchange: str = "NYSE", jetzt=None, puffer_min: int = _PUFFER_MIN) -> date:
    """Letzter Handelstag, dessen Schluss VORBEI ist.

    Unterschied zu „letzter Handelstag ≤ heute": der laufende Tag zählt erst,
    wenn an der Börse Schluss ist. Genau das fehlte und hat am 2026-09-25 den
    Skew-Radar geleert:

    Der Options-Cron steht auf 23:00 UTC, GitHub startet ihn aber mit ein bis
    zwei Stunden Verzug (gemessen 00:44 bis 01:20 UTC). Nach Mitternacht UTC ist
    `date.today()` der FOLGETAG; ist der ein Handelstag, wurden die Daten der
    abgelaufenen Session auf eine Session gestempelt, die noch nicht gehandelt
    hatte. Die Kursreihe endete (korrekt) einen Tag früher, der Frische-Wächter
    verweigerte daraufhin die Laufzeit-Normierung — für ALLE 161 Ticker — und
    das Ranking im Frontend fiel auf 0 Ticker.

    `jetzt` darf ein aufgelöster `datetime` mit Zeitzone sein (für Tests).
    CRYPTO handelt durchgehend und hat keinen Schluss → dort ist der laufende
    Tag immer die aktuelle Session.
    """
    from datetime import datetime
    from zoneinfo import ZoneInfo

    ex = boerse_normalisieren(exchange)
    if ex == "CRYPTO":
        return (jetzt or _uhr(ZoneInfo("UTC"))).date()
    if ex not in _SCHLUSSZEIT:   # früher still NYSE-Zeiten (Codex R4, A3)
        raise ValueError(f"Keine Schlusszeit für {ex} hinterlegt")
    tz_name, stunde, minute = _SCHLUSSZEIT[ex]
    tz = ZoneInfo(tz_name)
    jetzt_lokal = (jetzt.astimezone(tz) if jetzt is not None else _uhr(tz))
    d = jetzt_lokal.date()
    grenze = stunde * 60 + minute + puffer_min
    if jetzt_lokal.hour * 60 + jetzt_lokal.minute < grenze:
        d -= timedelta(days=1)
    for _ in range(12):               # Brückentage/Feiertagsketten
        if is_trading_day(d, ex):
            return d
        d -= timedelta(days=1)
    return d


_OEFFNUNG = {"NYSE": (9, 30)}      # nur dort gebraucht; weitere Börsen bei Bedarf


class MarktOffen(RuntimeError):
    """Ein EOD-Job wurde während der laufenden Handelszeit gestartet."""


def markt_offen(exchange: str = "NYSE", jetzt=None, puffer_min: int = _PUFFER_MIN) -> bool:
    """Läuft an `exchange` gerade eine Session, deren Schluss noch aussteht?

    Grund (Codex-Review 2026-09-25, Runde 2): `letzte_session()` ordnet einen
    Lauf während der Handelszeit korrekt der VORSESSION zu — der Options-Snapshot
    ist dann aber schon ein Intraday-Stand des laufenden Tages. Datum und Daten
    passten nicht zusammen, und weder der Kurs-Frischewächter noch die Dedup-
    Regel können das sehen (die Kursreihe endet korrekt am Vortag).
    Vor der Öffnung liefert der Snapshot noch den EOD-Stand der Vorsession,
    nach Schluss den des Tages — beides passt. Nur dieses Fenster nicht.

    Verkürzte Handelstage (Schluss 13:00 ET, z. B. 24.12.) gelten bewusst bis
    16:15 ET als „offen". Geprüft im Codex-Review R3: kein Datenverlust — der
    Cron läuft um 23:00 UTC (18:00/19:00 ET), gesperrt wird nur ein früher
    Handlauf, und zwar vor jedem Schreibzugriff. Wer das ändern will, muss die
    verkürzten Schlusszeiten in `markt_offen()` UND `letzte_session()`
    gemeinsam einführen, sonst driften beide.
    """
    from datetime import datetime
    from zoneinfo import ZoneInfo

    ex = boerse_normalisieren(exchange)
    if ex == "CRYPTO":
        return True
    if ex not in _SCHLUSSZEIT or ex not in _OEFFNUNG:   # früher still NYSE-Zeiten
        raise ValueError(f"Keine Handelszeiten für {ex} hinterlegt")
    tz_name, s_h, s_m = _SCHLUSSZEIT[ex]
    o_h, o_m = _OEFFNUNG[ex]
    tz = ZoneInfo(tz_name)
    j = (jetzt.astimezone(tz) if jetzt is not None else _uhr(tz))
    if not is_trading_day(j.date(), ex):
        return False
    minute = j.hour * 60 + j.minute
    return o_h * 60 + o_m <= minute < s_h * 60 + s_m + puffer_min


def pruefe_eod_fenster(job: str, exchange: str = "NYSE", jetzt=None) -> None:
    """Bricht mit `MarktOffen` ab, wenn ein EOD-Job in der Handelszeit SCHREIBEN will.

    Bewusst im Erzeuger aufgerufen (build), nicht an der Aufrufstelle: ein
    Schutz an der Aufrufstelle deckt nur diesen einen Aufrufer ab (v60.1).
    Lesende Läufe (--no-write) bleiben erlaubt.
    """
    if markt_offen(exchange, jetzt):
        raise MarktOffen(
            f"{job}: {exchange} handelt gerade. Der Snapshot wäre ein Intraday-"
            f"Stand, gestempelt würde die Vorsession — Datum und Daten passen nicht "
            f"zusammen. Nach Handelsschluss erneut starten oder --no-write nutzen.")


# ── Kalenderstatus je Börse und Jahr ───────────────────────────────────────────
# Auskunft, wie belastbar ein Kalenderjahr ist — die Funktionen rechnen trotzdem für
# jedes Jahr (lange Historien, Plan v4 K2). Leser nutzen den Status, um Aussagen zu
# kennzeichnen oder auszuschließen. Quellen: docs/review_prompts/2026-10-10_xetra_tdoy_plan_antwort4.md
# (A2) und 2026-10-08_plain_vanilla_1b_plan_antwort1.md (XETRA).
#   belegt      die implementierte Fassung stimmt mit einer offiziellen Quelle überein
#               (bei künftigen Jahren: mit dem zum Prüfdatum veröffentlichten Plan)
#   annahme     dokumentierte Regel, Einzelfälle nicht vollständig gegen Quellen geprüft
#   ungeprueft  bekannte Lücken oder Ersatzregeln (z. B. HKEX/KRX ohne Tabelle)
#   konvention  Projektkonvention, keine Börsenaussage (FOREX Mo–Fr, CRYPTO täglich)
# Je Börse: Liste (von, bis, status) — Jahre außerhalb aller Intervalle: Standardstatus.
KALENDER_PRUEFDATUM = "2026-10-10"
KALENDER_GUELTIG: dict[str, tuple[str, list[tuple[int, int, str]]]] = {
    # „belegt“ nur, wo ein VOLLSTÄNDIGER Abgleich gegen offizielle Quellen vorliegt:
    # NYSE ab 1971 (Wahlen-Arbeit + Paket 1), XETRA 2002–2026 (1B), LSE 2026–2028 und
    # TSE 2001–2027 (Tagesvergleich Codex R4), HKEX 2026 (Wertpapierkalender).
    # EURONEXT/SIX/MILAN/STOCKHOLM/OSLO sind nur stichprobenhaft geprüft → Annahme.
    # Ungeprüfte Vergangenheit reicht bis zum Rechenbeginn 1885 (Codex Paket 2, Befund 1).
    "NYSE":      ("annahme",    [(1885, 1970, "ungeprueft"), (1971, 2028, "belegt")]),
    "XETRA":     ("annahme",    [(1885, 2000, "ungeprueft"), (2002, 2026, "belegt")]),
    "LSE":       ("annahme",    [(1885, 1999, "ungeprueft"), (2026, 2028, "belegt")]),
    "TSE":       ("annahme",    [(1885, 1999, "ungeprueft"), (2001, 2027, "belegt")]),
    "EURONEXT":  ("annahme",    [(1885, 1999, "ungeprueft")]),
    "SIX":       ("annahme",    [(1885, 1999, "ungeprueft")]),
    "MILAN":     ("annahme",    [(1885, 1999, "ungeprueft")]),
    "STOCKHOLM": ("annahme",    [(1885, 1999, "ungeprueft")]),
    "OSLO":      ("annahme",    [(1885, 1999, "ungeprueft")]),
    "HKEX":      ("ungeprueft", [(2016, 2025, "annahme"), (2026, 2026, "belegt")]),
    "KRX":       ("ungeprueft", [(2016, 2026, "annahme")]),
    "FOREX":     ("konvention", []),
    "CRYPTO":    ("konvention", []),
}

# Rechenbereich der Nummernfunktion. Außerhalb → ValueError (kein stilles Ergebnis).
NUMMERN_VON_JAHR, NUMMERN_BIS_JAHR = 1885, 2100

_ALIAS_BOERSE = {"NASDAQ": "NYSE"}


def boerse_normalisieren(exchange) -> str:
    """Kanonische Börsenkennung oder ValueError. NASDAQ → NYSE, Groß/Klein egal."""
    if not isinstance(exchange, str) or not exchange.strip():
        raise ValueError(f"Börse fehlt oder ist kein Text: {exchange!r}")
    e = exchange.strip().upper()
    e = _ALIAS_BOERSE.get(e, e)
    if e not in _EXCHANGE_FUNCTIONS:
        raise ValueError(f"Unbekannte Börse: {exchange!r}")
    return e


def kalender_status(exchange: str, jahr: int) -> str:
    """'belegt' | 'annahme' | 'ungeprueft' | 'konvention' für Börse und Jahr."""
    e = boerse_normalisieren(exchange)
    standard, intervalle = KALENDER_GUELTIG[e]
    for von, bis, status in intervalle:
        if von <= jahr <= bis:
            return status
    return standard


# ── Handelstag-Nummern (TDOM/TDOY) nach Börsenkalender ─────────────────────────

class Nummer(tuple):
    """(tdom, tdoy, tdom_rev, tdoy_rev, offen) — unveränderlich, Felder auch per Name."""
    __slots__ = ()
    _felder = ("tdom", "tdoy", "tdom_rev", "tdoy_rev", "offen")

    def __new__(cls, tdom, tdoy, tdom_rev, tdoy_rev, offen):
        return tuple.__new__(cls, (tdom, tdoy, tdom_rev, tdoy_rev, offen))

    tdom = property(lambda s: s[0])
    tdoy = property(lambda s: s[1])
    tdom_rev = property(lambda s: s[2])
    tdoy_rev = property(lambda s: s[3])
    offen = property(lambda s: s[4])

    def __repr__(self):
        return "Nummer(" + ", ".join(f"{k}={v!r}" for k, v in zip(self._felder, self)) + ")"


_NUMMERN_CACHE: dict[tuple[str, int], dict[date, Nummer]] = {}

_ISO_DATUM = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")   # \d ließe auch nicht-lateinische Ziffern zu


def _als_datum(x) -> date:
    """Nur `date` (kein `datetime`) oder strenges 'YYYY-MM-DD'."""
    if isinstance(x, str):
        if not _ISO_DATUM.fullmatch(x):
            raise ValueError(f"Datum nicht im Format YYYY-MM-DD: {x!r}")
        return date.fromisoformat(x)
    # datetime ist eine Unterklasse von date — ausdrücklich ablehnen (Zeitzone/Uhrzeit
    # haben hier keine Bedeutung, und ein UTC-Zeitstempel kann den Börsentag verschieben).
    if type(x) is date:
        return x
    raise ValueError(f"Datum muss date oder 'YYYY-MM-DD' sein, nicht {type(x).__name__}: {x!r}")


def _jahresnummern(exchange: str, jahr: int) -> dict[date, Nummer]:
    """Nummern für jeden Kalendertag eines Jahres, gecacht je (Börse, Jahr)."""
    schluessel = (exchange, jahr)
    tab = _NUMMERN_CACHE.get(schluessel)
    if tab is not None:
        return tab
    tage = [date(jahr, 1, 1) + timedelta(days=i)
            for i in range((date(jahr + 1, 1, 1) - date(jahr, 1, 1)).days)]
    offen = {d: is_trading_day(d, exchange) for d in tage}
    jahr_summe = sum(offen.values())
    monat_summe: dict[int, int] = {}
    for d in tage:
        if offen[d]:
            monat_summe[d.month] = monat_summe.get(d.month, 0) + 1
    tab = {}
    tdoy = tdom = 0
    monat = None
    for d in tage:
        if d.month != monat:
            monat, tdom = d.month, 0
        if offen[d]:
            tdoy += 1
            tdom += 1
            tab[d] = Nummer(tdom, tdoy, -(monat_summe[d.month] - tdom + 1), -(jahr_summe - tdoy + 1), True)
        else:
            tab[d] = Nummer(tdom, tdoy, None, None, False)
    _NUMMERN_CACHE[schluessel] = tab
    return tab


def handelstag_nummern(daten, exchange: str) -> list[Nummer]:
    """Handelstag des Monats/Jahres nach Börsenkalender, je Eingabedatum.

    Vertrag (Plan v3/v4, Codex-Runden 3+4):
      - Börse wird ZUERST geprüft, auch bei leerer Eingabe (unbekannt → ValueError).
      - Eingabe: Folge aus `date` (kein `datetime`) oder strengem 'YYYY-MM-DD'.
        Reihenfolge und Duplikate bleiben erhalten; unsortiert und über mehrere
        Jahre ist erlaubt. Jahr außerhalb NUMMERN_VON_JAHR..NUMMERN_BIS_JAHR → ValueError.
      - tdom/tdoy: Anzahl Handelstage vom Periodenbeginn bis EINSCHLIESSLICH des Datums,
        auch wenn der Tag selbst geschlossen ist (dann = letzter Handelstag davor in der
        Periode, vor dem ersten Handelstag 0).
      - tdom_rev/tdoy_rev nur für offene Tage: −(Periodensumme − vorwärts + 1), also −1
        am letzten Handelstag; geschlossene Tage: None. Periodensumme = ganzer Monat bzw.
        ganzes Jahr, unabhängig vom übergebenen Ausschnitt.
      - offen: Kalenderstatus des Tages, unabhängig davon, ob ein Kurs existiert.
    Der Kalenderstatus des Jahres (belegt/annahme/…) steht in kalender_status().
    """
    e = boerse_normalisieren(exchange)
    tage = [_als_datum(x) for x in daten]
    for d in tage:
        if not NUMMERN_VON_JAHR <= d.year <= NUMMERN_BIS_JAHR:
            raise ValueError(f"Jahr außerhalb des Rechenbereichs {NUMMERN_VON_JAHR}–{NUMMERN_BIS_JAHR}: {d}")
    return [_jahresnummern(e, d.year)[d] for d in tage]


def tdom_tdoy_fuer_ticker(ticker: str, daten) -> list[tuple[int, int]]:
    """(tdom, tdoy) je Datum für die Spalten `prices.tdom/tdoy` — der EINE Weg für alle Schreiber (P2).

    Nach Börsenkalender des Tickers (shared.symbols.get_exchange_for_holidays), Reihenfolge wie die Eingabe,
    0 ist ein gültiger Wert (geschlossener Tag vor der ersten Sitzung der Periode). Zuordnungs- oder
    Bereichsfehler → ValueError; der Schreiber schreibt dann KEINE Nummern und meldet den Fehler.
    Ersetzt „Vorzeile + 1“ (Intraday), `cumcount` (preprocess/Nightly) und die Zählung ab der ersten Zeile
    (Onboarding) — Plan v7, Codex Runde 7.
    """
    from shared.symbols import get_exchange_for_holidays
    return [(n.tdom, n.tdoy) for n in handelstag_nummern(daten, get_exchange_for_holidays(ticker))]


# ── Selbsttest ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Börsenfeiertage 2025 im Vergleich:")
    print("=" * 60)

    exchanges = ["NYSE", "XETRA", "LSE", "EURONEXT", "TSE"]
    for ex in exchanges:
        fn = _EXCHANGE_FUNCTIONS[ex]
        holidays = fn(2025)
        print(f"\n{ex} ({len(holidays)} Feiertage):")
        for h in holidays:
            print(f"  {h.strftime('%d.%m.%Y')} ({h.strftime('%A')})")

    print("\n\nExchange-Erkennung via Ticker:")
    print("=" * 60)
    from shared.symbols import get_exchange_for_holidays
    for t in ["SPY", "^GDAXI", "^FTSE", "^FCHI", "^N225", "AAPL"]:
        print(f"  {t:12} → {get_exchange_for_holidays(t)}")
