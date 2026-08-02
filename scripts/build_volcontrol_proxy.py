"""
scripts/build_volcontrol_proxy.py — Panel E der /flows-Seite: Vol-Control-Leverage-Proxy
=======================================================================================
Target-Vol-/Risk-Parity-Fonds skalieren ihr Exposure invers zur realisierten Vola.
Modell-Proxy (KEINE echten Fonds-Bücher):
  realisierte 20-Tage-Vola(^GSPC, annualisiert) → impliziertes Leverage = Ziel-Vol / realisierte Vol (gekappt).

Zusatz-Serien (aus ^GSPC + ^VIX + ^VIX3M, alle frei):
  * vol_risk_premium = VIX − realisierte 20T-Vola (Pp)  → Vola-Risiko-Aufschlag (negativ = Stress)
  * regime_band      = ruhig/normal/stress/de-risk (aus RV20-Schwellen)
  * leverage_change_5d + est_dollar_flow_scenario (Szenario, angenommene AUM)
  * vix_ratio (VIX3M/VIX) je Tag → Re-Leveraging-Ampel als Zeitreihe

Schreibt `landing/data/volcontrol_proxy.json`.
Läuft standalone:  PYTHONUTF8=1 py -3.14 scripts/build_volcontrol_proxy.py
"""
from __future__ import annotations
import gc
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
sys.path.insert(0, str(_ROOT))

from shared.yahoo_downloader import download_data  # noqa: E402

_DATA = _ROOT / "landing" / "data"

TARGET_VOL = 0.15      # 15 % annualisierte Ziel-Vola (typische Target-Vol-Kalibrierung)
WINDOW = 20            # Handelstage für realisierte Vola
LEV_CAP = 1.5          # Leverage-Deckel (150 %)
TRADING_DAYS = 252
HISTORY_DAYS = 900     # ~3,5 Jahre Ausgabe
AUM_ASSUMED = 350e9    # angenommene Vol-Control-AUM (öffentliche Fremd-Schätzungsgröße) — NUR Szenario
# RV20-Regime-Schwellen
RB_RUHIG, RB_NORMAL, RB_STRESS = 0.12, 0.20, 0.25


def _dateclose_map(ticker: str) -> dict[str, float]:
    df = download_data(ticker)
    out: dict[str, float] = {}
    if df is not None and not df.empty:
        if "Date" not in df.columns:
            df = df.reset_index()
        df = df.dropna(subset=["Close"])
        for d, c in zip(df["Date"].astype("datetime64[ns]").dt.strftime("%Y-%m-%d"), df["Close"].astype(float)):
            out[d] = c
    return out


def _regime_band(rv: float) -> str:
    if rv < RB_RUHIG:
        return "ruhig"
    if rv < RB_NORMAL:
        return "normal"
    if rv < RB_STRESS:
        return "stress"
    return "de-risk"


def _series_from(df, vix: dict, vix3m: dict) -> list[dict]:
    df = df.copy()
    if "Date" not in df.columns:            # download_data kann Date als Index liefern (quellenabhängig)
        df = df.reset_index()
    df["Date"] = df["Date"].astype("datetime64[ns]")
    df = df.dropna(subset=["Close"]).sort_values("Date")
    close = df["Close"].astype(float).to_numpy()
    dates = df["Date"].dt.strftime("%Y-%m-%d").tolist()
    logret = np.diff(np.log(close))
    out = []
    for i in range(WINDOW, len(logret) + 1):
        win = logret[i - WINDOW:i]
        rv = float(np.std(win, ddof=1) * np.sqrt(TRADING_DAYS))
        if rv <= 0:
            continue
        lev = min(TARGET_VOL / rv, LEV_CAP)
        dt = dates[i]                          # logret[i-1] gehört zu dates[i]
        row = {
            "date": dt,
            "realized_vol_20d": round(rv, 4),
            "implied_leverage": round(lev, 3),
            "regime_band": _regime_band(rv),
        }
        vc = vix.get(dt)
        if vc is not None:
            row["vol_risk_premium"] = round(vc - rv * 100.0, 2)   # VIX(%) − RV20(%) in Pp
            v3 = vix3m.get(dt)
            if v3 is not None and vc > 0:
                row["vix_ratio"] = round(v3 / vc, 3)
        out.append(row)
    out = out[-HISTORY_DAYS:]
    # 5-Tage-Leverage-Momentum + Szenario-$-Flow (nach dem Trunkieren, konsistent mit Anzeige)
    for i, row in enumerate(out):
        if i >= 5:
            chg = row["implied_leverage"] - out[i - 5]["implied_leverage"]
            row["leverage_change_5d"] = round(chg, 3)
            row["est_dollar_flow_scenario"] = round(chg * AUM_ASSUMED, 0)
        else:
            row["leverage_change_5d"] = None
            row["est_dollar_flow_scenario"] = None
    return out


def build() -> dict:
    df = download_data("^GSPC")
    if df is None or df.empty:
        raise SystemExit("[volcontrol] ^GSPC leer")
    vix = _dateclose_map("^VIX")
    vix3m = _dateclose_map("^VIX3M")
    series = _series_from(df, vix, vix3m)
    download_data.clear()
    gc.collect()
    latest = series[-1] if series else None
    vt = None
    # jüngster Punkt mit vollständiger VIX-Term-Struktur (^VIX3M kann 1 Tag nachlaufen)
    vt_ref = next((p for p in reversed(series) if p.get("vix_ratio") is not None), None)
    if vt_ref:
        vc = vix.get(vt_ref["date"]); v3 = vix3m.get(vt_ref["date"])
        if vc and v3:
            vt = {"date": vt_ref["date"], "vix": round(vc, 2), "vix3m": round(v3, 2),
                  "ratio_3m_1m": round(v3 / vc, 3),
                  "structure": "contango" if v3 > vc else "backwardation"}
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "target_vol": TARGET_VOL,
        "window_days": WINDOW,
        "leverage_cap": LEV_CAP,
        "aum_assumed_usd": AUM_ASSUMED,
        "regime_thresholds": {"ruhig": RB_RUHIG, "normal": RB_NORMAL, "stress": RB_STRESS},
        "series": series,
        "latest": latest,
        "vix_term": vt,
        "note": ("Modell-Proxy: Ziel-Vol / realisierte 20-Tage-Vola(^GSPC). Zeigt die RICHTUNG des "
                 "De-/Re-Leveragings (fällt = Verkaufsdruck, steigt = Rückkauf), NICHT die $-Menge "
                 "oder echte Fonds-Bücher. Der geschätzte $-Flow ist ein SZENARIO (Annahme ~350 Mrd $ "
                 "AUM, öffentliche Fremd-Schätzung), keine Messung. Vola-Risiko-Aufschlag = VIX − "
                 "realisierte Vola (negativ = akuter Stress). Kein Handelssignal."),
    }


def main() -> int:
    out = build()
    _DATA.mkdir(parents=True, exist_ok=True)
    (_DATA / "volcontrol_proxy.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    lt = out["latest"]
    if lt:
        vrp = lt.get("vol_risk_premium")
        print(f"[volcontrol] {len(out['series'])} Punkte · RV20 {lt['realized_vol_20d']:.1%} "
              f"→ Leverage {lt['implied_leverage']:.2f}x · Regime {lt['regime_band']}"
              + (f" · VRP {vrp:+.1f}Pp" if vrp is not None else ""), flush=True)
    else:
        print("[volcontrol] leer", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
