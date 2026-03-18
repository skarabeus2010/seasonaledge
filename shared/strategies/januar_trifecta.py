# shared/strategies/januar_trifecta.py
# Januar Trifecta Ampelsystem
#
# Die drei Bedingungen (Yale Hirsch / Stock Trader's Almanac):
#   1. Santa Claus Rally  — letzte 5 Handelstage Dez + erste 2 Jan-Tage positiv
#   2. First Five Days    — erste 5 Handelstage im Januar positiv
#   3. January Barometer  — gesamter Januar positiv
#
# Ampel:
#   Grün   = alle 3 erfüllt  → bullishes Jahressignal
#   Gelb   = 2 von 3         → leicht bullish
#   Orange = 1 von 3         → neutral / Vorsicht
#   Rot    = keine erfüllt   → bearish

import pandas as pd
from typing import Optional


# ── Farbkonstanten (Ampel) ─────────────────────────────────────────────────────

AMPEL_FARBEN = {
    "Grün":   "#2ECC71",
    "Gelb":   "#F1C40F",
    "Orange": "#E67E22",
    "Rot":    "#E74C3C",
}

AMPEL_EMOJI = {
    "Grün":   "🟢",
    "Gelb":   "🟡",
    "Orange": "🟠",
    "Rot":    "🔴",
}


# ── Hilfsfunktion: Handelstage extrahieren ─────────────────────────────────────

def _get_trading_days(df: pd.DataFrame, year: int, month: int) -> pd.DatetimeIndex:
    """Gibt alle Handelstage eines bestimmten Monats/Jahres zurück."""
    mask = (df.index.year == year) & (df.index.month == month)
    return df.index[mask]


# ── Bedingung 1: Santa Claus Rally ────────────────────────────────────────────

def check_santa_claus_rally(df: pd.DataFrame, year: int) -> dict:
    """
    Prüft die Santa Claus Rally:
    Letzte 5 Handelstage im Dezember (year) + erste 2 Handelstage im Januar (year+1).

    Args:
        df   : DataFrame mit DatetimeIndex und 'Close'-Spalte
        year : Das Dezember-Jahr (z.B. 2024 für Dez 2024 / Jan 2025)

    Returns:
        dict mit keys: erfuellt (bool), rendite (float), start_date, end_date, details
    """
    dez_days = _get_trading_days(df, year, 12)
    jan_days = _get_trading_days(df, year + 1, 1)

    if len(dez_days) < 5 or len(jan_days) < 2:
        return {"erfuellt": None, "rendite": None, "fehler": "Nicht genügend Daten"}

    scr_days = list(dez_days[-5:]) + list(jan_days[:2])
    start_date = scr_days[0]
    end_date   = scr_days[-1]

    start_price = df.loc[start_date, "Close"]
    end_price   = df.loc[end_date,   "Close"]
    rendite     = (end_price - start_price) / start_price * 100

    return {
        "erfuellt":   rendite > 0,
        "rendite":    round(rendite, 2),
        "start_date": start_date,
        "end_date":   end_date,
        "start_price": round(float(start_price), 2),
        "end_price":   round(float(end_price), 2),
        "label":      "Santa Claus Rally",
        "zeitfenster": f"Letzte 5 Handelstage Dez {year} + erste 2 Jan {year+1}",
    }


# ── Bedingung 2: First Five Days ──────────────────────────────────────────────

def check_first_five_days(df: pd.DataFrame, year: int) -> dict:
    """
    Prüft den First Five Days Indikator:
    Performance der ersten 5 Handelstage im Januar (year).

    Args:
        df   : DataFrame mit DatetimeIndex und 'Close'-Spalte
        year : Das Jahr (z.B. 2025)

    Returns:
        dict mit keys: erfuellt (bool), rendite (float), start_date, end_date, details
    """
    jan_days = _get_trading_days(df, year, 1)

    if len(jan_days) < 5:
        return {"erfuellt": None, "rendite": None, "fehler": "Nicht genügend Daten"}

    start_date = jan_days[0]
    end_date   = jan_days[4]   # 5. Handelstag (Index 4)

    # Schlusskurs des letzten Dez-Handelstags als Referenz
    dez_days = _get_trading_days(df, year - 1, 12)
    if len(dez_days) == 0:
        return {"erfuellt": None, "rendite": None, "fehler": "Kein Dez-Kurs als Referenz"}

    ref_price   = df.loc[dez_days[-1], "Close"]   # Letzter Dez-Close
    end_price   = df.loc[end_date,     "Close"]
    rendite     = (end_price - ref_price) / ref_price * 100

    return {
        "erfuellt":    rendite > 0,
        "rendite":     round(rendite, 2),
        "start_date":  start_date,
        "end_date":    end_date,
        "ref_price":   round(float(ref_price), 2),
        "end_price":   round(float(end_price), 2),
        "label":       "First Five Days",
        "zeitfenster": f"Erste 5 Handelstage Januar {year}",
    }


# ── Bedingung 3: January Barometer ────────────────────────────────────────────

def check_january_barometer(df: pd.DataFrame, year: int) -> dict:
    """
    Prüft das January Barometer:
    Performance des gesamten Januars (year).

    Args:
        df   : DataFrame mit DatetimeIndex und 'Close'-Spalte
        year : Das Jahr (z.B. 2025)

    Returns:
        dict mit keys: erfuellt (bool), rendite (float), start_date, end_date, details
    """
    jan_days = _get_trading_days(df, year, 1)
    dez_days = _get_trading_days(df, year - 1, 12)

    if len(jan_days) == 0 or len(dez_days) == 0:
        return {"erfuellt": None, "rendite": None, "fehler": "Nicht genügend Daten"}

    ref_price   = df.loc[dez_days[-1], "Close"]   # Letzter Dez-Close
    end_price   = df.loc[jan_days[-1], "Close"]   # Letzter Jan-Close
    rendite     = (end_price - ref_price) / ref_price * 100

    return {
        "erfuellt":    rendite > 0,
        "rendite":     round(rendite, 2),
        "start_date":  jan_days[0],
        "end_date":    jan_days[-1],
        "ref_price":   round(float(ref_price), 2),
        "end_price":   round(float(end_price), 2),
        "label":       "January Barometer",
        "zeitfenster": f"Gesamter Januar {year}",
    }


# ── Ampel-Auswertung ───────────────────────────────────────────────────────────

def get_ampel_signal(erfuellt_count: int) -> str:
    """
    Gibt das Ampelsignal basierend auf der Anzahl erfüllter Bedingungen zurück.

    Args:
        erfuellt_count : Anzahl erfüllter Bedingungen (0–3)

    Returns:
        str: "Grün", "Gelb", "Orange" oder "Rot"
    """
    if erfuellt_count == 3:
        return "Grün"
    elif erfuellt_count == 2:
        return "Gelb"
    elif erfuellt_count == 1:
        return "Orange"
    else:
        return "Rot"


def get_ampel_interpretation(signal: str) -> str:
    """Gibt eine kurze Interpretation des Ampelsignals zurück."""
    interpretationen = {
        "Grün":   "Alle 3 Bedingungen erfüllt — starkes bullishes Jahressignal",
        "Gelb":   "2 von 3 Bedingungen erfüllt — leicht bullishes Signal, Vorsicht",
        "Orange": "1 von 3 Bedingungen erfüllt — neutrales Signal, erhöhte Wachsamkeit",
        "Rot":    "Keine Bedingung erfüllt — bearishes Jahressignal",
    }
    return interpretationen.get(signal, "Unbekannt")


# ── Hauptfunktion ──────────────────────────────────────────────────────────────

def calculate_trifecta(
    df: pd.DataFrame,
    year: int,
    scr_year: Optional[int] = None,
) -> dict:
    """
    Berechnet das vollständige Januar Trifecta Ampelsystem für ein gegebenes Jahr.

    Args:
        df       : DataFrame mit DatetimeIndex und 'Close'-Spalte (präprozessiert)
        year     : Das Analyse-Jahr (z.B. 2025 → prüft Januar 2025)
        scr_year : Dezember-Jahr für Santa Claus Rally (Standard: year - 1)

    Returns:
        dict mit:
            signal         : "Grün" | "Gelb" | "Orange" | "Rot"
            farbe          : Hex-Farbcode
            emoji          : Ampel-Emoji
            interpretation : Kurztext
            erfuellt_count : int (0–3)
            bedingungen    : dict mit Ergebnissen der 3 Checks
            jahr           : int
    """
    if scr_year is None:
        scr_year = year - 1

    scr    = check_santa_claus_rally(df, scr_year)
    ffd    = check_first_five_days(df, year)
    jan_b  = check_january_barometer(df, year)

    # Zähle nur gültige (nicht None) Ergebnisse
    bedingungen = {
        "santa_claus_rally": scr,
        "first_five_days":   ffd,
        "january_barometer": jan_b,
    }

    erfuellt_count = sum(
        1 for b in bedingungen.values()
        if b.get("erfuellt") is True
    )

    signal = get_ampel_signal(erfuellt_count)

    return {
        "jahr":            year,
        "signal":          signal,
        "farbe":           AMPEL_FARBEN[signal],
        "emoji":           AMPEL_EMOJI[signal],
        "interpretation":  get_ampel_interpretation(signal),
        "erfuellt_count":  erfuellt_count,
        "bedingungen":     bedingungen,
    }


# ── Historische Auswertung ─────────────────────────────────────────────────────

def calculate_trifecta_history(
    df: pd.DataFrame,
    start_year: int = 1970,
    end_year: Optional[int] = None,
) -> pd.DataFrame:
    """
    Berechnet das Trifecta-Signal für alle Jahre im angegebenen Zeitraum
    und gibt eine DataFrame-Tabelle zurück.

    Args:
        df         : DataFrame mit DatetimeIndex und 'Close'-Spalte
        start_year : Erstes Analysejahr
        end_year   : Letztes Analysejahr (Standard: letztes verfügbares Jahr)

    Returns:
        pd.DataFrame mit Spalten:
            Jahr, Signal, Farbe, Anzahl_erfuellt,
            SCR_Rendite, FFD_Rendite, JanB_Rendite,
            Jahresrendite (gesamtes Jahr nach Januar)
    """
    if end_year is None:
        end_year = df.index.year.max()

    rows = []
    for year in range(start_year, end_year + 1):
        result = calculate_trifecta(df, year)

        # Jahresrendite: Feb–Dez des gleichen Jahres
        feb_days = _get_trading_days(df, year, 2)
        dez_days = _get_trading_days(df, year, 12)
        jahresrendite = None
        if len(feb_days) > 0 and len(dez_days) > 0:
            jan_days = _get_trading_days(df, year, 1)
            if len(jan_days) > 0:
                jan_end_price = df.loc[jan_days[-1], "Close"]
                dez_end_price = df.loc[dez_days[-1], "Close"]
                jahresrendite = round(
                    (dez_end_price - jan_end_price) / jan_end_price * 100, 2
                )

        b = result["bedingungen"]
        rows.append({
            "Jahr":             year,
            "Signal":           result["signal"],
            "Farbe":            result["farbe"],
            "Emoji":            result["emoji"],
            "Anzahl_erfuellt":  result["erfuellt_count"],
            "SCR_Rendite_%":    b["santa_claus_rally"].get("rendite"),
            "FFD_Rendite_%":    b["first_five_days"].get("rendite"),
            "JanB_Rendite_%":   b["january_barometer"].get("rendite"),
            "Jahresrendite_Feb_Dez_%": jahresrendite,
        })

    return pd.DataFrame(rows)
