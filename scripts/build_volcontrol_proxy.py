"""
scripts/build_volcontrol_proxy.py — Panel E der /flows-Seite: Vol-Control-Leverage-Proxy
=======================================================================================
Target-Vol-/Risk-Parity-Fonds skalieren ihr Exposure invers zur realisierten Vola.
Modell-Proxy (KEINE echten Fonds-Bücher):
  realisierte 20-Tage-Vola(^GSPC, annualisiert) → impliziertes Leverage = Ziel-Vol / realisierte Vol (gekappt).
Optional VIX-Term-Struktur (^VIX3M/^VIX) als Zusatz-Kontext.

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


def _series_from(df) -> list[dict]:
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
        out.append({
            "date": dates[i],                      # i (nicht i-1): logret[i-1] gehört zu dates[i]
            "realized_vol_20d": round(rv, 4),
            "implied_leverage": round(lev, 3),
        })
    return out[-HISTORY_DAYS:]


def _vix_term() -> dict | None:
    try:
        vix = download_data("^VIX")
        vix3m = download_data("^VIX3M")
        if vix is None or vix.empty or vix3m is None or vix3m.empty:
            return None
        v = float(vix.dropna(subset=["Close"]).iloc[-1]["Close"])
        v3 = float(vix3m.dropna(subset=["Close"]).iloc[-1]["Close"])
        if v <= 0:
            return None
        ratio = v3 / v
        return {
            "vix": round(v, 2),
            "vix3m": round(v3, 2),
            "ratio_3m_1m": round(ratio, 3),
            "structure": "contango" if ratio > 1 else "backwardation",
        }
    except Exception:
        return None


def build() -> dict:
    df = download_data("^GSPC")
    if df is None or df.empty:
        raise SystemExit("[volcontrol] ^GSPC leer")
    series = _series_from(df)
    download_data.clear()
    gc.collect()
    vix = _vix_term()
    latest = series[-1] if series else None
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "target_vol": TARGET_VOL,
        "window_days": WINDOW,
        "leverage_cap": LEV_CAP,
        "series": series,
        "latest": latest,
        "vix_term": vix,
        "note": ("Modell-Proxy: Ziel-Vol / realisierte 20-Tage-Vola(^GSPC). Zeigt die RICHTUNG des "
                 "De-/Re-Leveragings (fällt = Verkaufsdruck, steigt = Rückkauf), NICHT die $-Menge "
                 "oder echte Fonds-Bücher. Kein Handelssignal."),
    }


def main() -> int:
    out = build()
    _DATA.mkdir(parents=True, exist_ok=True)
    (_DATA / "volcontrol_proxy.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    lt = out["latest"]
    print(f"[volcontrol] {len(out['series'])} Punkte · aktuell RV20 {lt['realized_vol_20d']:.1%} "
          f"→ Leverage {lt['implied_leverage']:.2f}x" if lt else "[volcontrol] leer", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
