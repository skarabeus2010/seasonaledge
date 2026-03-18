# shared/strategies/januar_trifecta.py
# Januar Trifecta Ampelsystem (Yale Hirsch / Stock Trader's Almanac)
#
# Drei Bedingungen:
#   1. Santa Claus Rally  — letzte 5 Handelstage Dez (year-1) + erste 2 Jan (year) positiv
#   2. First Five Days    — erste 5 Handelstage Januar (year) positiv
#   3. January Barometer  — gesamter Januar (year) positiv
#
# Ampel:
#   Grün   = alle 3 erfüllt  → starkes bullishes Jahressignal
#   Gelb   = 2 von 3         → leicht bullish
#   Orange = 1 von 3         → neutral / Vorsicht
#   Rot    = keine erfüllt   → bearish

import pandas as pd
import numpy as np
from typing import Optional

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

def _get_trading_days(df, year, month):
    mask = (df.index.year == year) & (df.index.month == month)
    return df.index[mask]

def check_santa_claus_rally(df, year):
    dez_days = _get_trading_days(df, year - 1, 12)
    jan_days = _get_trading_days(df, year, 1)
    if len(dez_days) < 6 or len(jan_days) < 2:
        return {"erfuellt": None, "rendite": None, "fehler": "Nicht genügend Daten"}
    ref_date   = dez_days[-6]
    start_date = dez_days[-5]
    end_date   = jan_days[1]
    ref_price  = float(df.loc[ref_date,  "Close"])
    end_price  = float(df.loc[end_date,  "Close"])
    rendite    = (end_price - ref_price) / ref_price * 100
    return {
        "erfuellt":    rendite > 0,
        "rendite":     round(rendite, 2),
        "start_date":  start_date,
        "end_date":    end_date,
        "ref_price":   round(ref_price, 2),
        "end_price":   round(end_price, 2),
        "label":       "Santa Claus Rally",
        "zeitfenster": f"Letzte 5 Handelstage Dez {year-1} + erste 2 Jan {year}",
    }

def check_first_five_days(df, year):
    jan_days = _get_trading_days(df, year, 1)
    dez_days = _get_trading_days(df, year - 1, 12)
    if len(jan_days) < 5 or len(dez_days) == 0:
        return {"erfuellt": None, "rendite": None, "fehler": "Nicht genügend Daten"}
    ref_price  = float(df.loc[dez_days[-1], "Close"])
    end_price  = float(df.loc[jan_days[4],  "Close"])
    rendite    = (end_price - ref_price) / ref_price * 100
    return {
        "erfuellt":    rendite > 0,
        "rendite":     round(rendite, 2),
        "start_date":  jan_days[0],
        "end_date":    jan_days[4],
        "ref_price":   round(ref_price, 2),
        "end_price":   round(end_price, 2),
        "label":       "First Five Days",
        "zeitfenster": f"Erste 5 Handelstage Januar {year}",
    }

def check_january_barometer(df, year):
    jan_days = _get_trading_days(df, year, 1)
    dez_days = _get_trading_days(df, year - 1, 12)
    if len(jan_days) == 0 or len(dez_days) == 0:
        return {"erfuellt": None, "rendite": None, "fehler": "Nicht genügend Daten"}
    ref_price  = float(df.loc[dez_days[-1], "Close"])
    end_price  = float(df.loc[jan_days[-1], "Close"])
    rendite    = (end_price - ref_price) / ref_price * 100
    return {
        "erfuellt":    rendite > 0,
        "rendite":     round(rendite, 2),
        "start_date":  jan_days[0],
        "end_date":    jan_days[-1],
        "ref_price":   round(ref_price, 2),
        "end_price":   round(end_price, 2),
        "label":       "January Barometer",
        "zeitfenster": f"Gesamter Januar {year}",
    }

def get_ampel_signal(n):
    return ["Rot","Orange","Gelb","Grün"][n]

def get_ampel_interpretation(signal):
    return {
        "Grün":   "Alle 3 Bedingungen erfüllt — starkes bullishes Jahressignal",
        "Gelb":   "2 von 3 Bedingungen erfüllt — leicht bullishes Signal",
        "Orange": "1 von 3 Bedingungen erfüllt — neutrales Signal, Vorsicht",
        "Rot":    "Keine Bedingung erfüllt — bearishes Jahressignal",
    }[signal]

def calculate_trifecta(df, year):
    scr   = check_santa_claus_rally(df, year)
    ffd   = check_first_five_days(df, year)
    jan_b = check_january_barometer(df, year)
    bedingungen = {
        "santa_claus_rally": scr,
        "first_five_days":   ffd,
        "january_barometer": jan_b,
    }
    n = sum(1 for b in bedingungen.values() if b.get("erfuellt") is True)
    signal = get_ampel_signal(n)
    return {
        "jahr":           year,
        "signal":         signal,
        "farbe":          AMPEL_FARBEN[signal],
        "emoji":          AMPEL_EMOJI[signal],
        "interpretation": get_ampel_interpretation(signal),
        "erfuellt_count": n,
        "bedingungen":    bedingungen,
    }

def calculate_trifecta_history(df, start_year=1990, end_year=None):
    if end_year is None:
        end_year = df.index.year.max()
    rows = []
    for year in range(start_year, end_year + 1):
        try:
            result = calculate_trifecta(df, year)
        except Exception:
            continue
        feb_days    = _get_trading_days(df, year, 2)
        dez_days_yr = _get_trading_days(df, year, 12)
        jan_days    = _get_trading_days(df, year, 1)
        jahresrendite = None
        if len(feb_days) > 0 and len(dez_days_yr) > 0 and len(jan_days) > 0:
            jan_end = float(df.loc[jan_days[-1],    "Close"])
            dez_end = float(df.loc[dez_days_yr[-1], "Close"])
            jahresrendite = round((dez_end - jan_end) / jan_end * 100, 2)
        b = result["bedingungen"]
        rows.append({
            "Jahr":                    year,
            "Signal":                  result["signal"],
            "Farbe":                   result["farbe"],
            "Emoji":                   result["emoji"],
            "Anzahl_erfuellt":         result["erfuellt_count"],
            "SCR_Rendite_%":           b["santa_claus_rally"].get("rendite"),
            "FFD_Rendite_%":           b["first_five_days"].get("rendite"),
            "JanB_Rendite_%":          b["january_barometer"].get("rendite"),
            "Jahresrendite_Feb_Dez_%": jahresrendite,
        })
    return pd.DataFrame(rows)

def calculate_seasonal_curves_by_signal(df, history_df):
    """
    Kumulative Ø-Jahreskurven gruppiert nach Trifecta-Signal.
    Normiert: Erster Close des Jahres = 0%, Achse zeigt % Abweichung.
    Gibt 252-Punkte-Kurven zurück (Handelstage interpoliert).
    """
    result = {}
    for signal in ["Grün", "Gelb", "Orange", "Rot"]:
        years = history_df[history_df["Signal"] == signal]["Jahr"].tolist()
        curves = []
        for year in years:
            ydf = df[df.index.year == year]
            if len(ydf) < 20:
                continue
            closes = ydf["Close"].values.astype(float)
            if closes[0] == 0:
                continue
            norm = (closes / closes[0] - 1) * 100
            x_orig = np.linspace(0, 251, len(norm))
            interp = np.interp(np.arange(252), x_orig, norm)
            curves.append(interp)
        if len(curves) < 2:
            result[signal] = None
            continue
        result[signal] = {
            "curve": np.mean(curves, axis=0).tolist(),
            "n":     len(curves),
            "years": years,
        }
    return result
