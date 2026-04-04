# shared/calculations_decade.py
# Intra-Dekaden-Saisonalität
# Logik vollständig getrennt von UI.

import pandas as pd
import numpy as np
from typing import Optional


# ── Konstanten ────────────────────────────────────────────────────────────────

DECADE_LABELS = {i: f"{i}er Jahre (X{i})" for i in range(10)}

# Farben für 10 Dekaden-Kohorten (distinkt, farbenblind-freundlich soweit möglich)
DECADE_COLORS = [
    "#E74C3C",  # 0
    "#E67E22",  # 1
    "#F1C40F",  # 2
    "#2ECC71",  # 3
    "#1ABC9C",  # 4
    "#3498DB",  # 5
    "#9B59B6",  # 6
    "#E91E63",  # 7
    "#00BCD4",  # 8
    "#FF5722",  # 9
]


# ── Logik ─────────────────────────────────────────────────────────────────────

def get_decade_digit(year: int) -> int:
    """Letzte Ziffer des Jahres. 1995 → 5, 2020 → 0."""
    return year % 10


def build_decade_data(df: pd.DataFrame, min_days: int = 200) -> dict:
    """
    Gruppiert alle Jahre der Zeitreihe nach ihrer letzten Ziffer (0–9)
    und berechnet für jede Kohorte:
      - Normierte Jahreskurven (erster Close = 0%, log-basiert)
      - Ø-Kursverlauf (252 Punkte interpoliert)
      - Ø-Jahresrendite, Median, Win-Rate, Volatilität, n

    Args:
        df       : DataFrame mit DatetimeIndex + 'Close'-Spalte (preprocessed)
        min_days : Minimale Handelstage damit ein Jahr berücksichtigt wird

    Returns:
        dict mit keys 0–9, jeder Eintrag:
        {
            "digit":     int,
            "years":     list[int],           # Jahre in dieser Kohorte
            "curves":    list[np.ndarray],    # Einzelne normierte Kurven (252 Punkte)
            "avg_curve": list[float],         # Ø-Kurve (252 Punkte)
            "std_curve": list[float],         # ±1σ (252 Punkte)
            "avg_return":   float,            # Ø Jahresrendite %
            "median_return":float,
            "win_rate":     float,            # % positive Jahre
            "volatility":   float,            # Std der Jahresrenditen
            "returns":      list[float],      # Einzelne Jahresrenditen
            "n":            int,
        }
    """
    all_years = sorted(df.index.year.unique())
    # Kohorten aufbauen
    cohorts: dict[int, list] = {d: [] for d in range(10)}

    for year in all_years:
        ydf = df[df.index.year == year]
        if len(ydf) < min_days:
            continue  # unvollständiges Jahr überspringen

        closes = ydf["Close"].values.astype(float)
        if closes[0] <= 0:
            continue

        # Log-normierte Kurve: erster Close = 0, Einheit = %
        log_curve = (np.log(closes) - np.log(closes[0])) * 100

        # Auf 252 Punkte interpolieren (einheitliche Länge für Mittelung)
        n_orig = len(log_curve)
        x_orig = np.linspace(0, 251, n_orig)
        x_new  = np.arange(252)
        interp = np.interp(x_new, x_orig, log_curve)

        digit = get_decade_digit(year)
        cohorts[digit].append({
            "year":   year,
            "curve":  interp,
            "ret":    float((closes[-1] / closes[0] - 1) * 100),  # Simple Return (%)
        })

    # Kohorte aggregieren
    result = {}
    for digit, items in cohorts.items():
        if len(items) == 0:
            result[digit] = {
                "digit": digit, "years": [], "curves": [],
                "avg_curve": None, "std_curve": None,
                "avg_return": None, "median_return": None,
                "win_rate": None, "volatility": None,
                "returns": [], "n": 0,
            }
            continue

        curves  = np.array([it["curve"] for it in items])  # shape (n, 252)
        returns = [it["ret"] for it in items]
        years   = [it["year"] for it in items]

        avg_curve = np.mean(curves, axis=0).tolist()
        std_curve = np.std(curves,  axis=0).tolist()
        rets      = np.array(returns)

        result[digit] = {
            "digit":         digit,
            "years":         years,
            "curves":        [c.tolist() for c in curves],
            "avg_curve":     avg_curve,
            "std_curve":     std_curve,
            "avg_return":    float(np.mean(rets)),
            "median_return": float(np.median(rets)),
            "win_rate":      float((rets > 0).sum() / len(rets) * 100),
            "volatility":    float(np.std(rets)),
            "returns":       returns,
            "n":             len(items),
        }

    return result


def get_decade_summary_table(decade_data: dict) -> pd.DataFrame:
    """
    Gibt eine übersichtliche DataFrame-Tabelle aller 10 Kohorten zurück.
    Geeignet für st.dataframe().
    """
    rows = []
    for digit in range(10):
        d = decade_data[digit]
        if d["n"] == 0:
            rows.append({
                "Ziffer": digit,
                "Kohorte": f"x{digit} Jahre",
                "Anzahl Jahre": 0,
                "Ø Rendite %": None,
                "Median %": None,
                "Win-Rate %": None,
                "Volatilität %": None,
                "Jahre": "—",
            })
        else:
            rows.append({
                "Ziffer": digit,
                "Kohorte": f"x{digit} Jahre",
                "Anzahl Jahre": d["n"],
                "Ø Rendite %": round(d["avg_return"], 2),
                "Median %": round(d["median_return"], 2),
                "Win-Rate %": round(d["win_rate"], 1),
                "Volatilität %": round(d["volatility"], 2),
                "Jahre": ", ".join(str(y) for y in sorted(d["years"])),
            })
    return pd.DataFrame(rows)
