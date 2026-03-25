"""
shared/ai_models.py — KI-Modelle für SeasonalEdge

Phase 1: DTW Pattern Matching, Prophet, Isolation Forest, Claude API
Phase 1.5: KI-Zusammenfassung, Anomalie-Heatmap
Phase 2: LSTM, XGBoost (TODO)
Phase 3: Transformer (TODO)
"""
import numpy as np
import pandas as pd
from typing import Optional


# ── DTW Pattern Matching ────────────────────────────

def find_similar_years(
    current_pattern: list[float],
    all_years_data: dict[int, list[float]],
    top_n: int = 3,
) -> list[tuple[int, float]]:
    """
    Findet historische Jahre mit ähnlichstem Kursverlauf.

    Args:
        current_pattern: Normalisierte Kursreihe des aktuellen Jahres
        all_years_data: {year: normalisierte Kursreihe}
        top_n: Anzahl ähnlichster Jahre

    Returns:
        [(year, distance), ...] sortiert nach Ähnlichkeit (niedrig = ähnlich)
    """
    try:
        from fastdtw import fastdtw
        from scipy.spatial.distance import euclidean
    except ImportError:
        # Fallback: einfache Korrelation
        return _find_similar_correlation(current_pattern, all_years_data, top_n)

    scores = {}
    for year, pattern in all_years_data.items():
        # Auf gleiche Länge trimmen
        min_len = min(len(current_pattern), len(pattern))
        if min_len < 10:
            continue
        dist, _ = fastdtw(
            current_pattern[:min_len],
            pattern[:min_len],
            dist=euclidean,
        )
        scores[year] = dist

    return sorted(scores.items(), key=lambda x: x[1])[:top_n]


def _find_similar_correlation(
    current_pattern: list[float],
    all_years_data: dict[int, list[float]],
    top_n: int = 3,
) -> list[tuple[int, float]]:
    """Fallback: Korrelationsbasierte Ähnlichkeit (ohne fastdtw)."""
    scores = {}
    for year, pattern in all_years_data.items():
        min_len = min(len(current_pattern), len(pattern))
        if min_len < 10:
            continue
        corr = np.corrcoef(current_pattern[:min_len], pattern[:min_len])[0, 1]
        # Negieren, damit niedrigerer Wert = ähnlicher (wie bei DTW)
        scores[year] = -corr if not np.isnan(corr) else 999

    return sorted(scores.items(), key=lambda x: x[1])[:top_n]


# ── Prophet Forecast ────────────────────────────────

def forecast_seasonal(
    df_prices: pd.DataFrame,
    periods: int = 60,
    yearly: bool = True,
    weekly: bool = False,
) -> Optional[pd.DataFrame]:
    """
    Saisonale Prognose mit Facebook Prophet.

    Args:
        df_prices: DataFrame mit Date und Close
        periods: Anzahl Tage in die Zukunft
        yearly/weekly: Saisonalitätskomponenten

    Returns:
        DataFrame mit ds, yhat, yhat_lower, yhat_upper (oder None bei Fehler)
    """
    try:
        from prophet import Prophet
    except ImportError:
        return None

    df = df_prices.copy()
    if "Date" in df.columns:
        df = df.rename(columns={"Date": "ds", "Close": "y"})
    elif df.index.name == "Date":
        df = df.reset_index().rename(columns={"Date": "ds", "Close": "y"})

    df = df[["ds", "y"]].dropna()

    m = Prophet(
        yearly_seasonality=yearly,
        weekly_seasonality=weekly,
        daily_seasonality=False,
    )
    m.fit(df)
    future = m.make_future_dataframe(periods=periods)
    forecast = m.predict(future)

    return forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail(periods)


# ── Isolation Forest (Ausreißer-Jahre) ──────────────

def detect_outlier_years(
    year_returns: dict[int, list[float]],
    contamination: float = 0.1,
) -> list[int]:
    """
    Erkennt Jahre die nicht ins typische saisonale Muster passen.

    Args:
        year_returns: {year: [daily_returns]}
        contamination: Anteil erwarteter Ausreißer (0.05-0.2)

    Returns:
        Liste der Ausreißer-Jahre
    """
    try:
        from sklearn.ensemble import IsolationForest
    except ImportError:
        return []

    # Alle auf gleiche Länge bringen
    min_len = min(len(v) for v in year_returns.values())
    years = list(year_returns.keys())
    matrix = np.array([year_returns[y][:min_len] for y in years])

    clf = IsolationForest(contamination=contamination, random_state=42)
    labels = clf.fit_predict(matrix)

    return [y for y, label in zip(years, labels) if label == -1]


# ── Claude API (Natural Language Kommentar) ─────────

def generate_seasonal_commentary(
    ticker: str,
    month: str,
    avg_return: float,
    win_rate: float,
    similar_years: list[tuple[int, float]] = None,
    model: str = "claude-sonnet-4-20250514",
) -> Optional[str]:
    """
    Generiert einen KI-Kommentar zur Saisonalität.

    Args:
        ticker: z.B. "SPY"
        month: z.B. "März"
        avg_return: Durchschnittliche Rendite in %
        win_rate: Win-Rate in %
        similar_years: Output von find_similar_years()
        model: Claude-Modell

    Returns:
        Kommentar als String (oder None bei Fehler)
    """
    try:
        import anthropic
    except ImportError:
        return None

    similar_str = ""
    if similar_years:
        similar_str = f"- Ähnlichste historische Jahre: {', '.join(str(y) for y, _ in similar_years)}"

    prompt = f"""Analysiere kurz das saisonale Muster für {ticker} im Monat {month}:
- Durchschnittliche Rendite: {avg_return:.1f}%
- Win-Rate: {win_rate:.0f}%
{similar_str}
Antworte in 2-3 Sätzen auf Deutsch. Keine Anlageempfehlung."""

    try:
        import os
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            try:
                import streamlit as st
                api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
            except Exception:
                pass

        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model=model,
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text
    except Exception:
        return None


# ── KI-Zusammenfassung (Page Summary) ────────────────

def generate_page_summary(
    ticker: str,
    page_name: str,
    stats: dict,
    model: str = "claude-sonnet-4-20250514",
) -> Optional[str]:
    """
    Generiert eine KI-Zusammenfassung fuer eine beliebige Page.

    Args:
        ticker: z.B. "SPY"
        page_name: z.B. "Saisonale Analyse", "TDOM", "Feiertags-Effekt"
        stats: Dict mit relevanten Kennzahlen der Analyse, z.B.:
            {"avg_return": 1.2, "win_rate": 68, "period": "Maerz",
             "best_year": 2019, "worst_year": 2020, "n_years": 20,
             "current_tracking": "ueber Durchschnitt",
             "next_event": "FOMC am 19.03."}
        model: Claude-Modell

    Returns:
        3-Satz-Zusammenfassung auf Deutsch (oder None bei Fehler)
    """
    try:
        import anthropic
    except ImportError:
        return None

    # Stats in lesbaren Text umwandeln
    stats_lines = []
    key_labels = {
        "avg_return": "Oe-Rendite",
        "median_return": "Median-Rendite",
        "win_rate": "Win-Rate",
        "period": "Zeitraum/Monat",
        "n_years": "Anzahl Jahre",
        "best_year": "Bestes Jahr",
        "worst_year": "Schlechtestes Jahr",
        "current_tracking": "Aktuelles Jahr vs Muster",
        "next_event": "Naechster Katalysator",
        "score": "KI-Score",
        "signal": "Signal",
        "std_dev": "Volatilitaet (Std)",
        "total_return": "Gesamt-Rendite",
        "strategy": "Strategie",
    }
    for k, v in stats.items():
        label = key_labels.get(k, k)
        if isinstance(v, float):
            stats_lines.append(f"- {label}: {v:+.2f}%")
        else:
            stats_lines.append(f"- {label}: {v}")

    stats_text = "\n".join(stats_lines)

    prompt = f"""Du bist ein Finanzmarkt-Analyst bei SeasonalEdge. Fasse die folgende saisonale Analyse kurz zusammen.

Ticker: {ticker}
Analyse: {page_name}
Kennzahlen:
{stats_text}

Regeln:
- Genau 3 Saetze auf Deutsch
- Satz 1: Historisches Muster (bullish/bearish/neutral + Kennzahl)
- Satz 2: Aktueller Kontext (wie verhaelt sich das aktuelle Jahr)
- Satz 3: Was kommt als naechstes (naechster Katalysator oder worauf achten)
- Keine Anlageempfehlung, keine Emojis
- Sachlich, praezise, datenbasiert"""

    try:
        import os
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            try:
                import streamlit as st
                api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
            except Exception:
                pass

        if not api_key:
            return None

        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model=model,
            max_tokens=250,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text
    except Exception:
        return None


# ── Anomalie-Heatmap (Monat x Dekade) ────────────────

def build_anomaly_matrix(
    df: pd.DataFrame,
    contamination: float = 0.1,
) -> tuple[np.ndarray, list[str], list[str]]:
    """
    Berechnet eine Anomalie-Heatmap: Monat (Y) x Dekaden-Endziffer (X).

    Methode: Isolation Forest ueber ALLE Monatsrenditen trainiert,
    dann Anomalie-Score pro Zelle (Monat x Dekade) gemittelt.
    So entsteht ein differenziertes Bild statt einheitlicher 10%-Werte.

    Args:
        df: DataFrame mit DatetimeIndex + Close
        contamination: Anteil erwarteter Ausreisser

    Returns:
        (matrix[12x10], month_labels, digit_labels)
    """
    try:
        from sklearn.ensemble import IsolationForest
    except ImportError:
        return np.zeros((12, 10)), [], []

    MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "Mai", "Jun",
                    "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]
    DIGIT_LABELS = [f"x{d}" for d in range(10)]

    # Monatsrenditen berechnen
    monthly = df["Close"].resample("ME").last().pct_change().dropna() * 100
    monthly_df = pd.DataFrame({
        "year": monthly.index.year,
        "month": monthly.index.month,
        "digit": monthly.index.year % 10,
        "return": monthly.values,
    })

    if len(monthly_df) < 24:
        return np.zeros((12, 10)), MONTH_LABELS, DIGIT_LABELS

    # Isolation Forest ueber ALLE Renditen trainieren (global)
    X_all = monthly_df["return"].values.reshape(-1, 1)
    clf = IsolationForest(contamination=contamination, random_state=42)
    monthly_df["anomaly_score"] = -clf.fit(X_all).decision_function(X_all)

    # Normalisiere Scores auf 0-100
    s_min = monthly_df["anomaly_score"].min()
    s_max = monthly_df["anomaly_score"].max()
    if s_max > s_min:
        monthly_df["anomaly_norm"] = (
            (monthly_df["anomaly_score"] - s_min) / (s_max - s_min) * 100
        )
    else:
        monthly_df["anomaly_norm"] = 0

    # Matrix: Mittlerer Anomalie-Score pro Zelle
    anomaly_matrix = np.zeros((12, 10))

    for month in range(1, 13):
        for digit in range(10):
            cell = monthly_df[
                (monthly_df["month"] == month) & (monthly_df["digit"] == digit)
            ]["anomaly_norm"]

            if len(cell) >= 2:
                anomaly_matrix[month - 1, digit] = round(cell.mean(), 1)

    return anomaly_matrix, MONTH_LABELS, DIGIT_LABELS


def build_anomaly_heatmap_figure(
    matrix: np.ndarray,
    month_labels: list[str],
    digit_labels: list[str],
    ticker: str = "",
) -> "go.Figure":
    """
    Erstellt die Plotly-Heatmap-Figur fuer die Anomalie-Matrix.

    Args:
        matrix: 12x10 Anomalie-Scores (% Ausreisser)
        month_labels: ["Jan", ..., "Dez"]
        digit_labels: ["X0", ..., "X9"]
        ticker: Fuer Titel

    Returns:
        go.Figure
    """
    import plotly.graph_objects as go
    from shared.constants import SE_COLORS
    from shared.charts import apply_se_theme

    fig = go.Figure(go.Heatmap(
        z=matrix,
        x=digit_labels,
        y=month_labels,
        colorscale=[
            [0.0, SE_COLORS["surface"]],
            [0.25, "#1a3a5c"],
            [0.5, SE_COLORS["accent_blue"]],
            [0.75, SE_COLORS["accent_warm"]],
            [1.0, SE_COLORS["negative"]],
        ],
        zmin=0,
        zmax=max(np.max(matrix), 1),  # Verhindere Division by zero
        text=np.round(matrix, 0).astype(int).astype(str),
        texttemplate="%{text}",
        textfont=dict(size=10, color="#FFFFFF"),
        hovertemplate=(
            "<b>%{y} / %{x}</b><br>"
            "Anomalie-Score: %{z:.1f}<extra></extra>"
        ),
        colorbar=dict(
            title=dict(
                text="Anomalie",
                font=dict(color=SE_COLORS["text_muted"]),
            ),
            tickfont=dict(color=SE_COLORS["text_muted"]),
        ),
    ))

    title = f"{ticker} — Anomalie-Heatmap (Monat x Dekade)" if ticker else "Anomalie-Heatmap"
    fig = apply_se_theme(fig, title=title, height=420)
    fig.update_xaxes(title="Dekaden-Endziffer", side="bottom")
    fig.update_yaxes(title="Monat", autorange="reversed")

    # "We are here" — aktuellen Monat + Dekade markieren
    from datetime import datetime as _dt
    now = _dt.now()
    current_month_idx = now.month - 1  # 0-basiert
    current_digit = now.year % 10
    fig.add_shape(
        type="rect",
        x0=current_digit - 0.5, x1=current_digit + 0.5,
        y0=current_month_idx - 0.5, y1=current_month_idx + 0.5,
        line=dict(color="#F1C40F", width=3),
        fillcolor="rgba(0,0,0,0)",
        layer="above",
    )
    from shared.we_are_here import annotation_offset as _wah_offset
    fig.add_annotation(**_wah_offset(current_digit, current_month_idx))

    return fig
