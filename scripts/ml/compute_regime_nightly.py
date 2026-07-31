"""
scripts/ml/compute_regime_nightly.py
Tägliche Regime-Berechnung für Major-Indizes (SPY, ^GDAXI, QQQ, GLD).

Logik: Percentil-Clustering auf rolling Return (20T) + annualisierter Vola.
       Identisch mit SA.indicators.calcRegime() im Frontend.

Ergebnis: landing/data/market_regimes.json (wird vom Server serviert)
Einbindung: in nightly_refresh.py aufrufen oder standalone per Cron.

Ausführen: py -3.14 scripts/ml/compute_regime_nightly.py
"""
import sys, os, pathlib, gc, json
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))

from datetime import datetime, timezone
import numpy as np
from shared.yahoo_downloader import download_data

TICKERS = ['SPY', '^GDAXI', 'QQQ', 'GLD']
PERIOD = 20
OUT_PATH = pathlib.Path(__file__).resolve().parent.parent.parent / 'landing' / 'data' / 'market_regimes.json'


def calc_regime(closes: np.ndarray, period: int = 20) -> list:
    """Percentil-basiertes Regime — 'Bull' / 'Sideways' / 'Bear' / None."""
    n = len(closes)
    ret_arr = [None] * n
    vol_arr = [None] * n

    for i in range(period, n):
        daily_log = np.diff(np.log(closes[i - period:i + 1]))
        if len(daily_log) < 2:
            continue
        ret_arr[i] = closes[i] / closes[i - period] - 1
        vol_arr[i] = float(np.std(daily_log, ddof=0) * np.sqrt(252))

    s_ret = sorted(v for v in ret_arr if v is not None)
    s_vol = sorted(v for v in vol_arr if v is not None)
    if not s_ret:
        return [None] * n

    def pct_rank(arr, val):
        lo, hi = 0, len(arr)
        while lo < hi:
            mid = (lo + hi) // 2
            if arr[mid] < val:
                lo = mid + 1
            else:
                hi = mid
        return lo / len(arr)

    regimes = [None] * n
    for i in range(period, n):
        if ret_arr[i] is None:
            continue
        rp = pct_rank(s_ret, ret_arr[i])
        vp = pct_rank(s_vol, vol_arr[i])
        if rp > 0.60 and vp < 0.70:
            regimes[i] = 'Bull'
        elif rp < 0.33 or vp > 0.75:
            regimes[i] = 'Bear'
        else:
            regimes[i] = 'Sideways'
    return regimes


def compute_for_ticker(ticker: str) -> dict | None:
    df = download_data(ticker, period='5y')
    if df is None or df.empty:
        return None
    closes = df['Close'].dropna().to_numpy()
    if len(closes) < PERIOD + 20:
        return None

    regimes = calc_regime(closes, PERIOD)
    current = next((r for r in reversed(regimes) if r is not None), None)
    valid = [r for r in regimes if r is not None]
    total = len(valid)

    return {
        'ticker': ticker,
        'regime': current,
        'bull_pct': round(valid.count('Bull') / total * 100, 1) if total else 0,
        'sideways_pct': round(valid.count('Sideways') / total * 100, 1) if total else 0,
        'bear_pct': round(valid.count('Bear') / total * 100, 1) if total else 0,
        'computed_at': datetime.now(timezone.utc).isoformat(),
    }


def main():
    results = {}
    for ticker in TICKERS:
        result = compute_for_ticker(ticker)
        if result:
            results[ticker] = result
            print(f"[{ticker:10s}] Regime: {result['regime']:10s}  "
                  f"Bull {result['bull_pct']}% / Sideways {result['sideways_pct']}% / Bear {result['bear_pct']}%")
        else:
            print(f"[{ticker:10s}] FEHLER: keine Daten")
        download_data.clear()
        gc.collect()

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"\nGeschrieben: {OUT_PATH}")
    return results


if __name__ == '__main__':
    main()
