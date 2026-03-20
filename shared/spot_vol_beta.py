"""
shared/spot_vol_beta.py — Spot-Vol Beta Berechnung
====================================================
Berechnet die Spot-Volatilitaets-Korrelation zwischen einem Index (SPX)
und dem VIX. OLS-Regression + Rolling Beta.

Kein Streamlit-Import! Reine Berechnung.
"""

import numpy as np
import pandas as pd
import statsmodels.api as sm


def load_spot_vol_data(
    ticker_spot: str = "^GSPC",
    ticker_vol: str = "^VIX",
) -> pd.DataFrame | None:
    """
    Laedt Spot- und Vol-Daten via yahoo_downloader.

    Returns:
        DataFrame mit: spx_close, vix_close (DatetimeIndex)
        oder None bei Fehler
    """
    from shared.yahoo_downloader import download_data

    spot_raw = download_data(ticker_spot, period="max")
    vol_raw = download_data(ticker_vol, period="max")

    if spot_raw is None or vol_raw is None:
        return None
    if spot_raw.empty or vol_raw.empty:
        return None

    spx = spot_raw[["Close"]].rename(columns={"Close": "spx_close"})
    vix = vol_raw[["Close"]].rename(columns={"Close": "vix_close"})

    # Indizes auf Datum normalisieren (Zeitkomponente entfernen)
    spx.index = pd.to_datetime(spx.index).normalize()
    vix.index = pd.to_datetime(vix.index).normalize()

    df = spx.join(vix, how="inner").dropna()
    df.index = pd.to_datetime(df.index)

    return df


def compute_spot_vol_beta(
    df: pd.DataFrame,
    rolling_window: int = 60,
    use_log_returns: bool = False,
) -> tuple[pd.DataFrame, dict]:
    """
    Berechnet Spot-Vol Beta (OLS-Regression SPX-Rendite vs. VIX-Aenderung).

    Args:
        df: DataFrame mit spx_close, vix_close
        rolling_window: Fenster fuer Rolling Beta (Handelstage)
        use_log_returns: Log-Returns statt einfacher Returns

    Returns:
        (DataFrame mit Renditen + Rolling Beta, Metriken-Dict)
    """
    out = df.copy().sort_index()

    # Renditen berechnen
    if use_log_returns:
        out["spx_ret"] = np.log(out["spx_close"] / out["spx_close"].shift(1))
        out["vix_chg"] = np.log(out["vix_close"] / out["vix_close"].shift(1))
    else:
        out["spx_ret"] = out["spx_close"].pct_change()
        out["vix_chg"] = out["vix_close"].pct_change()

    # Taeglicher Spot-Vol Beta: SPX-Rendite * VIX-Aenderung
    # Negativ = normale inverse Beziehung, positiv = anomal
    out["daily_beta"] = out["spx_ret"] * out["vix_chg"]

    # Gesamt-Regression
    x = out["spx_ret"]
    y = out["vix_chg"]
    mask = x.notna() & y.notna()
    X = sm.add_constant(x[mask])
    model = sm.OLS(y[mask], X).fit()
    beta = float(model.params["spx_ret"])
    alpha = float(model.params["const"])
    r2 = float(model.rsquared)
    corr = float(out[["spx_ret", "vix_chg"]].corr().iloc[0, 1])

    # Rolling Beta
    rolling_beta = pd.Series(np.nan, index=out.index)
    for i in range(rolling_window - 1, len(out)):
        seg = out.iloc[i - rolling_window + 1: i + 1][["spx_ret", "vix_chg"]].dropna()
        if len(seg) < max(10, rolling_window // 2):
            continue
        try:
            Xr = sm.add_constant(seg["spx_ret"])
            rolling_beta.iloc[i] = sm.OLS(seg["vix_chg"], Xr).fit().params["spx_ret"]
        except Exception:
            pass

    out["rolling_beta"] = rolling_beta

    metrics = {
        "beta": round(beta, 4),
        "alpha": round(alpha, 6),
        "r2": round(r2, 4),
        "corr": round(corr, 4),
        "n": int(mask.sum()),
        "regime": classify_beta(beta),
        "rolling_window": rolling_window,
    }

    return out, metrics


def classify_beta(beta: float) -> str:
    """Klassifiziert den Beta-Wert in ein Regime."""
    if beta <= -0.8:
        return "stark negativ"
    if beta <= -0.3:
        return "negativ"
    if beta < 0.3:
        return "nahe null"
    return "positiv"


def sync_spot_vol_to_db(df_calc: pd.DataFrame):
    """
    Schreibt den berechneten daily + rolling Beta nach Supabase.

    Args:
        df_calc: Output von compute_spot_vol_beta()
    """
    from shared.supabase_client import upsert_spot_vol_beta

    records = []
    for dt, row in df_calc.iterrows():
        if pd.isna(row.get("spx_ret")) or pd.isna(row.get("vix_chg")):
            continue
        records.append({
            "event_date": dt.strftime("%Y-%m-%d"),
            "spx_close": round(float(row["spx_close"]), 2),
            "vix_close": round(float(row["vix_close"]), 2),
            "spx_ret": round(float(row["spx_ret"]), 6),
            "vix_chg": round(float(row["vix_chg"]), 6),
            "daily_beta": round(float(row.get("daily_beta", 0)), 6),
            "rolling_beta_60": round(float(row["rolling_beta"]), 4) if pd.notna(row.get("rolling_beta")) else None,
        })

    if records:
        upsert_spot_vol_beta(records)

    return len(records)


def regime_color(regime: str) -> str:
    """Farbe fuer das Regime."""
    if "stark" in regime:
        return "#ff4757"
    if "negativ" in regime:
        return "#e8a425"
    if "null" in regime:
        return "#5a6e85"
    return "#00d4aa"


# ── Regime-Wechsel & Wendepunkt-Analyse ─────────────

def analyze_vix_extremes(
    df: pd.DataFrame,
    vix_spike_threshold: float = 30.0,
    vix_low_threshold: float = 15.0,
    beta_stress_threshold: float = -1.0,
    forward_days: list[int] = None,
) -> dict:
    """
    Analysiert was historisch nach VIX-Extremen und Beta-Stress passiert.

    Untersucht:
    1. VIX-Spikes (VIX > threshold): Wie entwickelt sich der SPX danach?
    2. VIX-Tiefs (VIX < threshold): Warnsignal fuer Complacency?
    3. Beta-Stress (Rolling Beta < threshold): Wendepunkt-Statistik

    Args:
        df: DataFrame mit spx_close, vix_close, rolling_beta
        vix_spike_threshold: Ab welchem VIX-Level = Spike
        vix_low_threshold: Unter welchem VIX-Level = Complacency
        beta_stress_threshold: Ab welchem Beta = Stress
        forward_days: Vorausschau-Fenster [5, 10, 20, 60]

    Returns:
        dict mit: vix_spikes, vix_lows, beta_stress — jeweils Statistiken
    """
    if forward_days is None:
        forward_days = [5, 10, 20, 60]

    results = {}

    # Forward Returns berechnen
    for fd in forward_days:
        df[f"fwd_{fd}d"] = (
            df["spx_close"].shift(-fd) / df["spx_close"] - 1
        ) * 100

    # ── 1. VIX-Spikes ──
    spike_mask = df["vix_close"] >= vix_spike_threshold
    spike_entries = _first_day_of_regime(df, spike_mask)
    results["vix_spikes"] = _compute_forward_stats(
        df, spike_entries, forward_days, f"VIX >= {vix_spike_threshold}"
    )

    # ── 2. VIX-Tiefs ──
    low_mask = df["vix_close"] <= vix_low_threshold
    low_entries = _first_day_of_regime(df, low_mask)
    results["vix_lows"] = _compute_forward_stats(
        df, low_entries, forward_days, f"VIX <= {vix_low_threshold}"
    )

    # ── 3. Beta-Stress ──
    if "rolling_beta" in df.columns:
        beta_mask = df["rolling_beta"] <= beta_stress_threshold
        beta_entries = _first_day_of_regime(df, beta_mask)
        results["beta_stress"] = _compute_forward_stats(
            df, beta_entries, forward_days, f"Beta <= {beta_stress_threshold}"
        )
    else:
        results["beta_stress"] = {"label": "Beta-Stress", "n": 0, "events": []}

    # Cleanup
    for fd in forward_days:
        if f"fwd_{fd}d" in df.columns:
            df.drop(columns=[f"fwd_{fd}d"], inplace=True)

    return results


def _first_day_of_regime(df: pd.DataFrame, mask: pd.Series, min_gap_days: int = 10) -> list:
    """
    Findet den ersten Tag jeder Regime-Phase (mit Mindestabstand).
    Verhindert dass aufeinanderfolgende Tage als separate Events gezaehlt werden.
    """
    entries = []
    last_entry = None

    for idx in df[mask].index:
        if last_entry is None or (idx - last_entry).days >= min_gap_days:
            entries.append(idx)
            last_entry = idx

    return entries


def _compute_forward_stats(
    df: pd.DataFrame,
    entry_dates: list,
    forward_days: list[int],
    label: str,
) -> dict:
    """Berechnet Forward-Return-Statistiken nach Trigger-Events."""
    if not entry_dates:
        return {"label": label, "n": 0, "stats": {}, "events": []}

    stats = {}
    events = []

    for fd in forward_days:
        col = f"fwd_{fd}d"
        if col not in df.columns:
            continue

        returns = []
        for dt in entry_dates:
            if dt in df.index:
                val = df.loc[dt, col]
                if pd.notna(val):
                    returns.append(val)

        if returns:
            wins = [r for r in returns if r > 0]
            stats[fd] = {
                "avg_return": round(float(np.mean(returns)), 2),
                "median_return": round(float(np.median(returns)), 2),
                "win_rate": round(len(wins) / len(returns) * 100, 1),
                "max_gain": round(float(max(returns)), 2),
                "max_loss": round(float(min(returns)), 2),
                "n": len(returns),
            }

    # Event-Liste fuer Tabelle
    for dt in entry_dates:
        row = df.loc[dt] if dt in df.index else None
        if row is not None:
            event = {
                "date": dt.strftime("%Y-%m-%d"),
                "spx": round(float(row.get("spx_close", 0)), 2),
                "vix": round(float(row.get("vix_close", 0)), 2),
            }
            for fd in forward_days:
                col = f"fwd_{fd}d"
                if col in df.columns and pd.notna(row.get(col)):
                    event[f"fwd_{fd}d"] = round(float(row[col]), 2)
            events.append(event)

    return {"label": label, "n": len(entry_dates), "stats": stats, "events": events}
