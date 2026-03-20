"""
shared/anomaly_engine.py — Anomalie-Erkennung mit Isolation Forest
===================================================================
4 Features:
  1. Anomalie-Radar: Ticker-Abweichung vom Saisonalmuster (aktuell)
  2. Crash-Fruehwarnung: Markt-Regime-Erkennung (Ampel)
  3. TDoM-Anomalien: Ungewoehnliche Trading Days
  4. Saisonale Muster-Brueche: Jahre mit gebrochenem Muster + Kontext

Kein Streamlit-Import! Reine Berechnung.
"""

import numpy as np
import pandas as pd
from datetime import datetime, date


# ══════════════════════════════════════════════════════
# 1. ANOMALIE-RADAR
# ══════════════════════════════════════════════════════

def compute_ticker_anomaly_score(
    df: pd.DataFrame,
    lookback_days: int = 10,
    history_years: int = 20,
) -> dict:
    """
    Berechnet wie stark ein Ticker aktuell vom saisonalen Muster abweicht.

    Methode: Isolation Forest trainiert auf historischen Fenster-Renditen
    gleicher Laenge am gleichen Kalenderzeitpunkt. Score des aktuellen
    Fensters zeigt, wie "normal" das aktuelle Verhalten ist.

    Args:
        df: Preprocessed DataFrame mit DatetimeIndex + Close
        lookback_days: Fensterlaenge (letzte N Handelstage)
        history_years: Wie viele Jahre als Referenz

    Returns:
        dict mit: anomaly_score (0-100), percentile, direction, details
    """
    try:
        from sklearn.ensemble import IsolationForest
    except ImportError:
        return {"anomaly_score": 0, "percentile": 50, "direction": "neutral",
                "error": "sklearn nicht installiert"}

    if len(df) < lookback_days * 2:
        return {"anomaly_score": 0, "percentile": 50, "direction": "neutral",
                "error": "Zu wenig Daten"}

    now = datetime.now()
    current_doy = now.timetuple().tm_yday

    # Aktuelles Fenster: letzte N Tage Renditen
    recent = df.tail(lookback_days)
    if len(recent) < lookback_days:
        return {"anomaly_score": 0, "percentile": 50, "direction": "neutral",
                "error": "Zu wenig aktuelle Daten"}

    current_returns = recent["Close"].pct_change().dropna().values * 100

    # Historische Fenster: gleicher Zeitraum im Jahr (±10 Tage)
    cutoff_year = now.year - history_years
    hist_windows = []

    for year in range(cutoff_year, now.year):
        year_df = df[df.index.year == year]
        if len(year_df) < 50:
            continue
        # Finde den Handelstag der dem aktuellen DOY am naechsten liegt
        year_df = year_df.copy()
        year_df["_doy"] = year_df.index.dayofyear
        close_idx = (year_df["_doy"] - current_doy).abs().idxmin()
        pos = year_df.index.get_loc(close_idx)

        start = max(0, pos - lookback_days + 1)
        end = pos + 1
        window = year_df.iloc[start:end]

        if len(window) >= lookback_days - 2:
            rets = window["Close"].pct_change().dropna().values * 100
            if len(rets) >= lookback_days - 2:
                # Auf gleiche Laenge padden/trimmen
                target_len = len(current_returns)
                if len(rets) > target_len:
                    rets = rets[-target_len:]
                elif len(rets) < target_len:
                    rets = np.pad(rets, (target_len - len(rets), 0), constant_values=0)
                hist_windows.append(rets)

    if len(hist_windows) < 5:
        return {"anomaly_score": 0, "percentile": 50, "direction": "neutral",
                "error": "Zu wenig historische Vergleichsdaten"}

    # Isolation Forest
    X = np.array(hist_windows)
    X_current = current_returns.reshape(1, -1)

    clf = IsolationForest(contamination=0.1, random_state=42)
    clf.fit(X)

    # Score: negativer = anomaler
    raw_score = clf.decision_function(X_current)[0]
    all_scores = clf.decision_function(X)

    # Normalisieren auf 0-100 (100 = maximale Anomalie)
    percentile = (all_scores < raw_score).mean() * 100
    anomaly_score = round(max(0, min(100, (1 - percentile / 100) * 100)), 1)

    # Richtung: positiv oder negativ anomal?
    current_total = current_returns.sum()
    hist_totals = [w.sum() for w in hist_windows]
    hist_mean = np.mean(hist_totals)

    if current_total > hist_mean + np.std(hist_totals):
        direction = "bullish_anomaly"
    elif current_total < hist_mean - np.std(hist_totals):
        direction = "bearish_anomaly"
    else:
        direction = "normal"

    return {
        "anomaly_score": anomaly_score,
        "percentile": round(percentile, 1),
        "direction": direction,
        "current_return": round(current_total, 2),
        "historical_avg": round(hist_mean, 2),
        "historical_std": round(float(np.std(hist_totals)), 2),
        "n_comparisons": len(hist_windows),
    }


# ══════════════════════════════════════════════════════
# 2. CRASH-FRUEHWARNUNG
# ══════════════════════════════════════════════════════

def compute_market_regime(
    df: pd.DataFrame,
    windows: list[int] = None,
) -> dict:
    """
    Erkennt das aktuelle Markt-Regime via Isolation Forest.

    Features pro Tag: Rendite, Volatilitaet (5d, 10d, 20d),
    Drawdown, Volumen-Anomalie.

    Returns:
        dict mit: regime ("calm"/"caution"/"stress"),
                  risk_score (0-100), traffic_light, details
    """
    if windows is None:
        windows = [5, 10, 20]

    try:
        from sklearn.ensemble import IsolationForest
    except ImportError:
        return {"regime": "unknown", "risk_score": 0,
                "traffic_light": "grey", "error": "sklearn nicht installiert"}

    if len(df) < 60:
        return {"regime": "unknown", "risk_score": 0,
                "traffic_light": "grey", "error": "Zu wenig Daten"}

    # Features berechnen
    feat_df = pd.DataFrame(index=df.index)
    feat_df["return_1d"] = df["Close"].pct_change() * 100

    for w in windows:
        feat_df[f"vol_{w}d"] = feat_df["return_1d"].rolling(w).std()
        feat_df[f"ret_{w}d"] = df["Close"].pct_change(w) * 100

    # Drawdown vom 20d-Hoch
    feat_df["high_20d"] = df["Close"].rolling(20).max()
    feat_df["drawdown"] = (df["Close"] - feat_df["high_20d"]) / feat_df["high_20d"] * 100

    feat_df = feat_df.dropna()
    if len(feat_df) < 100:
        return {"regime": "unknown", "risk_score": 0,
                "traffic_light": "grey", "error": "Zu wenig berechnete Features"}

    feature_cols = [c for c in feat_df.columns if c != "high_20d"]
    X = feat_df[feature_cols].values

    # IF trainieren
    clf = IsolationForest(contamination=0.05, random_state=42)
    clf.fit(X)

    # Aktueller Tag bewerten
    current_score = clf.decision_function(X[-1:].reshape(1, -1))[0]
    all_scores = clf.decision_function(X)

    # Percentile (niedrigeres Percentile = anomaler)
    percentile = (all_scores >= current_score).mean() * 100
    risk_score = round(max(0, min(100, (1 - percentile / 100) * 100)), 1)

    # Ampel
    if risk_score >= 70:
        regime = "stress"
        traffic_light = "red"
    elif risk_score >= 40:
        regime = "caution"
        traffic_light = "yellow"
    else:
        regime = "calm"
        traffic_light = "green"

    # Details
    latest = feat_df.iloc[-1]

    return {
        "regime": regime,
        "risk_score": risk_score,
        "traffic_light": traffic_light,
        "volatility_5d": round(float(latest.get("vol_5d", 0)), 3),
        "volatility_20d": round(float(latest.get("vol_20d", 0)), 3),
        "drawdown": round(float(latest.get("drawdown", 0)), 2),
        "return_5d": round(float(latest.get("ret_5d", 0)), 2),
        "return_20d": round(float(latest.get("ret_20d", 0)), 2),
    }


TRAFFIC_LIGHT_LABELS = {
    "green": {"emoji": "🟢", "label": "Ruhig", "color": "#00d4aa",
              "desc": "Markt verhaelt sich normal — keine Auffaelligkeiten."},
    "yellow": {"emoji": "🟡", "label": "Erhoehte Vorsicht", "color": "#e8a425",
               "desc": "Ungewoehnliche Muster erkannt — erhoehte Aufmerksamkeit empfohlen."},
    "red": {"emoji": "🔴", "label": "Stress-Regime", "color": "#ff4757",
            "desc": "Stark anomales Marktverhalten — historisch selten."},
    "grey": {"emoji": "⚪", "label": "Unbekannt", "color": "#5a6e85",
             "desc": "Nicht genug Daten fuer Regime-Erkennung."},
}


# ══════════════════════════════════════════════════════
# 3. TDOM-ANOMALIEN
# ══════════════════════════════════════════════════════

def detect_tdom_anomalies(
    df: pd.DataFrame,
    strategy: str = "open_to_close",
    recent_months: int = 3,
) -> list[dict]:
    """
    Erkennt TDoMs die sich aktuell anomal verhalten vs. historisch.

    Vergleicht die letzten N Monate mit dem historischen Durchschnitt.
    Isolation Forest erkennt welche TDoMs am staerksten abweichen.

    Args:
        df: DataFrame mit OHLC + year, month
        strategy: Strategie fuer Renditeberechnung
        recent_months: Wie viele aktuelle Monate vergleichen

    Returns:
        list[dict] sortiert nach Anomalie-Staerke
    """
    from shared.tdom_analysis import add_tdom_columns, calc_strategy_returns

    df = add_tdom_columns(df)
    df = calc_strategy_returns(df, strategy)

    valid = df[df["strat_return"].notna()].copy()
    valid = valid[valid["tdom"].between(1, 23)]

    if len(valid) < 100:
        return []

    now = datetime.now()
    cutoff = pd.Timestamp(now.year, max(1, now.month - recent_months), 1)

    recent = valid[valid.index >= cutoff]
    historical = valid[valid.index < cutoff]

    if len(recent) < 10 or len(historical) < 100:
        return []

    results = []
    for tdom in range(1, 24):
        hist_data = historical[historical["tdom"] == tdom]["strat_return"]
        recent_data = recent[recent["tdom"] == tdom]["strat_return"]

        if len(hist_data) < 10 or len(recent_data) < 1:
            continue

        hist_mean = hist_data.mean()
        hist_std = hist_data.std()
        recent_mean = recent_data.mean()

        if hist_std == 0:
            continue

        # Z-Score: wie viele Std weicht der aktuelle Durchschnitt ab?
        z_score = (recent_mean - hist_mean) / hist_std
        anomaly_strength = abs(z_score)

        if anomaly_strength < 0.5:
            continue

        direction = "bullish" if z_score > 0 else "bearish"

        results.append({
            "tdom": tdom,
            "z_score": round(z_score, 2),
            "anomaly_strength": round(anomaly_strength, 2),
            "direction": direction,
            "recent_avg": round(recent_mean, 4),
            "historical_avg": round(hist_mean, 4),
            "historical_std": round(hist_std, 4),
            "recent_n": len(recent_data),
            "historical_n": len(hist_data),
        })

    results.sort(key=lambda x: x["anomaly_strength"], reverse=True)
    return results


# ══════════════════════════════════════════════════════
# 4. SAISONALE MUSTER-BRUECHE
# ══════════════════════════════════════════════════════

# Historische Ereignisse fuer Kontext
_KNOWN_EVENTS = {
    2001: "9/11 + Dotcom-Crash",
    2002: "WorldCom/Enron-Skandale",
    2008: "Lehman-Pleite / Finanzkrise",
    2009: "Finanzkrise-Erholung",
    2011: "Euro-Schuldenkrise / US-Downgrade",
    2015: "China-Crash / Yuan-Abwertung",
    2018: "Volmageddon / Fed-Straffung",
    2020: "COVID-19 Pandemie",
    2022: "Ukraine-Krieg / Zinswende",
}


def detect_pattern_breaks(
    year_data: dict,
    avg: list[float],
    top_n: int = 5,
) -> list[dict]:
    """
    Erkennt Jahre in denen das saisonale Muster am staerksten gebrochen wurde.

    Methode: Korrelation + MAE jedes Jahres vs. Saisonaldurchschnitt.
    Isolation Forest identifiziert die groessten Ausreisser.

    Args:
        year_data: Output von build_year_data()
        avg: Saisonaler Durchschnitt (365 Werte)
        top_n: Anzahl Ergebnisse

    Returns:
        list[dict] sortiert nach Bruch-Staerke (staerkster zuerst)
    """
    if not year_data or not avg or len(avg) < 365:
        return []

    try:
        from sklearn.ensemble import IsolationForest
    except ImportError:
        return []

    avg_arr = np.array(avg)
    features = []
    years = []

    for year, yd in year_data.items():
        curve = np.array(yd["full_365"])
        if len(curve) < 365:
            continue

        # Feature 1: Korrelation mit Durchschnitt
        corr = np.corrcoef(curve, avg_arr)[0, 1]
        if np.isnan(corr):
            corr = 0

        # Feature 2: Normalisierte MAE
        avg_range = max(avg_arr) - min(avg_arr)
        mae = np.mean(np.abs(curve - avg_arr))
        norm_mae = mae / avg_range if avg_range > 0 else 0

        # Feature 3: Jahresrendite
        year_return = (curve[-1] / curve[0] - 1) * 100 if curve[0] != 0 else 0

        # Feature 4: Max Drawdown im Jahr
        peak = np.maximum.accumulate(curve)
        drawdown = ((curve - peak) / peak * 100)
        max_dd = float(drawdown.min())

        features.append([corr, norm_mae, year_return, max_dd])
        years.append(year)

    if len(features) < 5:
        return []

    X = np.array(features)
    clf = IsolationForest(contamination=0.15, random_state=42)
    labels = clf.fit_predict(X)
    scores = clf.decision_function(X)

    results = []
    for i, (year, feat, label, score) in enumerate(zip(years, features, labels, scores)):
        corr, norm_mae, year_return, max_dd = feat

        # Bruch-Staerke: Kombination aus niedriger Korrelation + hoher MAE
        break_strength = round((1 - corr) * 50 + norm_mae * 50, 1)

        event = _KNOWN_EVENTS.get(year, "")

        results.append({
            "year": year,
            "is_outlier": label == -1,
            "break_strength": break_strength,
            "correlation": round(corr, 3),
            "mae": round(norm_mae, 3),
            "year_return": round(year_return, 1),
            "max_drawdown": round(max_dd, 1),
            "anomaly_score": round(-score, 3),
            "event": event,
        })

    # Sortiere nach Bruch-Staerke (staerkster zuerst)
    results.sort(key=lambda x: x["break_strength"], reverse=True)
    return results[:top_n]
