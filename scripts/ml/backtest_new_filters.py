"""
scripts/ml/backtest_new_filters.py
Repliziert die JS Backtest-Engine (backtest-engine.html) in Python.

Strategie: TDOM 17-22, daysBefore=3, daysAfter=10, stopPct=0
Filter G: Momentum (12M-1M) > 0   → ^GDAXI
Filter H: StRev (21d) < 0         → SPY

Ausführen: PYTHONUTF8=1 py -3.14 scripts/ml/backtest_new_filters.py
"""
import sys, os, pathlib, gc
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))

import numpy as np
import pandas as pd
from datetime import datetime
from shared.yahoo_downloader import download_data

# ── Parameter ────────────────────────────────────────────────────────────────
TDOM_START  = 17
TDOM_END    = 22
DAYS_BEFORE = 3
DAYS_AFTER  = 10
MIN_GAP     = 5      # Handelstage Mindestabstand zwischen Trades
YEARS_BACK  = 15


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_tdom_dates(year: int, tdom_start: int, tdom_end: int) -> list[str]:
    """Generiert TDOM-Datumsliste per einfachem Wochentag-Zaehlen (identisch JS)."""
    dates = []
    for m in range(1, 13):
        trading_days = []
        d = datetime(year, m, 1)
        while d.month == m:
            if d.weekday() < 5:  # Mon=0 .. Fri=4
                trading_days.append(d.strftime('%Y-%m-%d'))
            d = d.replace(day=d.day + 1) if d.day < 28 else datetime(year if m < 12 else year+1,
                                                                       m+1 if m < 12 else 1, 1) if d.day >= 28 and (d + pd.Timedelta(days=1)).month != m else d.replace(day=d.day+1)
        # Simpler: einfach alle Wochentage des Monats zählen
        trading_days = []
        cur = pd.Timestamp(year, m, 1)
        while cur.month == m:
            if cur.dayofweek < 5:
                trading_days.append(cur.strftime('%Y-%m-%d'))
            cur += pd.Timedelta(days=1)
        for td in range(tdom_start, tdom_end + 1):
            if td <= len(trading_days):
                dates.append(trading_days[td - 1])
    return dates


def run_backtest(df: pd.DataFrame, filter_mask: np.ndarray | None,
                 label: str = '', years_back: int = YEARS_BACK) -> dict:
    """
    Portiert runBacktest() aus backtest-engine.html.
    df: DataFrame mit columns ['date', 'close'] sortiert aufsteigend.
    filter_mask: boolean array gleiche Laenge wie df, oder None.
    """
    rows   = df.reset_index(drop=True)
    closes = rows['close'].to_numpy()
    dates  = rows['date'].to_list()
    n      = len(rows)
    date2i = {d: i for i, d in enumerate(dates)}

    cur_year  = datetime.now().year
    start_year = cur_year - years_back
    years = sorted({int(d[:4]) for d in dates if start_year <= int(d[:4]) <= cur_year})

    # TDOM-Events fuer alle Jahre sammeln
    all_events = []
    for y in years:
        for tdom_date in get_tdom_dates(y, TDOM_START, TDOM_END):
            all_events.append((tdom_date, y))
    all_events.sort(key=lambda x: x[0])

    trades = []
    last_exit_date = None

    for ev_date, year in all_events:
        # t0 = erster Index >= ev_date
        t0 = None
        for k in range(n):
            if dates[k] >= ev_date:
                t0 = k
                break
        if t0 is None:
            continue
        entry_idx = t0 - DAYS_BEFORE
        exit_idx  = t0 + DAYS_AFTER
        if entry_idx < 0 or exit_idx >= n:
            continue

        entry_date = dates[entry_idx]
        exit_date  = dates[exit_idx]

        # Technischer Filter an entryIdx-1 prüfen (look-ahead-bias-frei)
        if filter_mask is not None and entry_idx > 0:
            if not filter_mask[entry_idx - 1]:
                continue

        # Mindestabstand
        if last_exit_date is not None:
            gap = (pd.Timestamp(entry_date) - pd.Timestamp(last_exit_date)).days
            if gap < MIN_GAP:
                continue

        entry_price = closes[entry_idx]
        exit_price  = closes[exit_idx]
        if entry_price <= 0:
            continue

        ret = (exit_price - entry_price) / entry_price * 100
        trades.append({
            'year': year,
            'entry_date': entry_date,
            'exit_date': exit_date,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'return_pct': ret,
            'holding_days': exit_idx - entry_idx,
        })
        last_exit_date = exit_date

    return compute_stats(trades, label)


def compute_stats(trades: list, label: str = '') -> dict:
    if not trades:
        return {'label': label, 'n': 0}
    rets = np.array([t['return_pct'] for t in trades])
    wins = (rets > 0).sum()
    gross_win  = rets[rets > 0].sum() if (rets > 0).any() else 0
    gross_loss = abs(rets[rets < 0].sum()) if (rets < 0).any() else 0
    pf   = gross_win / gross_loss if gross_loss > 0 else float('inf')
    mu   = rets.mean()
    sd   = rets.std(ddof=1) if len(rets) > 1 else 0
    sharpe = mu / sd if sd > 0 else 0

    # Max Drawdown auf kumulierter Equity (Start=100)
    eq = 100.0
    peak = 100.0
    max_dd = 0.0
    for r in rets:
        eq *= (1 + r / 100)
        if eq > peak:
            peak = eq
        dd = (peak - eq) / peak * 100
        if dd > max_dd:
            max_dd = dd

    return {
        'label': label,
        'n': len(trades),
        'win_rate': round(wins / len(rets) * 100, 1),
        'avg_ret': round(mu, 3),
        'std_ret': round(sd, 3),
        'sharpe': round(sharpe, 3),
        'profit_factor': round(pf, 2) if pf != float('inf') else 'inf',
        'max_drawdown': round(max_dd, 1),
        'total_return': round((np.prod(1 + rets / 100) - 1) * 100, 1),
        'trades': trades,
    }


# ── Filter-Berechnungen (1:1 Port aus indicators.js) ─────────────────────────

def calc_momentum(closes: np.ndarray, long_p: int = 252, short_p: int = 21) -> np.ndarray:
    """Carhart UMD: 12M-Return minus 1M-Return (Skip-1M)."""
    n = len(closes)
    result = np.full(n, np.nan)
    for i in range(long_p, n):
        if closes[i - long_p] > 0 and closes[i - short_p] > 0:
            ret12 = closes[i] / closes[i - long_p] - 1
            ret1  = closes[i] / closes[i - short_p] - 1
            result[i] = ret12 - ret1
    return result


def calc_strev(closes: np.ndarray, period: int = 21) -> np.ndarray:
    """Short-Term Reversal: 21-Tage-Return."""
    n = len(closes)
    result = np.full(n, np.nan)
    for i in range(period, n):
        if closes[i - period] > 0:
            result[i] = closes[i] / closes[i - period] - 1
    return result


def build_filter_mask(closes: np.ndarray, filter_type: str, **kwargs) -> np.ndarray:
    """Gibt boolean mask zurueck (identisch JS _evalSingleFilter + shift(1))."""
    n = len(closes)
    mask = np.zeros(n, dtype=bool)

    if filter_type == 'momentum_bull':
        mom = calc_momentum(closes, kwargs.get('long_p', 252), kwargs.get('short_p', 21))
        for i in range(1, n):
            if not np.isnan(mom[i - 1]):
                mask[i] = mom[i - 1] > 0

    elif filter_type == 'strev_down':
        strev = calc_strev(closes, kwargs.get('period', 21))
        for i in range(1, n):
            if not np.isnan(strev[i - 1]):
                mask[i] = strev[i - 1] < 0

    return mask


# ── Baseline (kein Filter) ────────────────────────────────────────────────────

def run_pair(ticker: str, filter_type: str | None, filter_label: str, label: str):
    print(f"\nLade {ticker}...")
    df_raw = download_data(ticker, period='max')
    download_data.clear(); gc.collect()
    if df_raw is None or df_raw.empty:
        print(f"  FEHLER: keine Daten fuer {ticker}")
        return None

    df = df_raw[['Close']].copy()
    df.index = pd.to_datetime(df.index)
    df = df.dropna().reset_index()
    df.columns = ['date', 'close']
    df['date'] = df['date'].dt.strftime('%Y-%m-%d')
    df = df.sort_values('date').reset_index(drop=True)

    closes = df['close'].to_numpy()

    mask = None
    if filter_type:
        if filter_type == 'momentum_bull':
            mask = build_filter_mask(closes, 'momentum_bull')
        elif filter_type == 'strev_down':
            mask = build_filter_mask(closes, 'strev_down')
        filter_pct = mask.sum() / len(mask) * 100
        print(f"  Filter '{filter_label}': {filter_pct:.1f}% der Tage aktiv")

    result = run_backtest(df, mask, label=label)
    return result


def print_result(r: dict):
    if not r or r.get('n', 0) == 0:
        print(f"  {r.get('label','?')}: Keine Trades")
        return
    pf_str = f"{r['profit_factor']:.2f}" if isinstance(r['profit_factor'], float) else r['profit_factor']
    print(f"  {r['label']:45s}  "
          f"n={r['n']:3d}  WR={r['win_rate']:5.1f}%  "
          f"Sharpe={r['sharpe']:+.3f}  "
          f"PF={pf_str:>5s}  "
          f"Avg={r['avg_ret']:+.3f}%  "
          f"MaxDD={r['max_drawdown']:.1f}%  "
          f"Total={r['total_return']:+.1f}%")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 90)
    print(f"BACKTEST: TDOM {TDOM_START}-{TDOM_END}, Entry-{DAYS_BEFORE}d / Exit+{DAYS_AFTER}d, "
          f"letzte {YEARS_BACK} Jahre, kein Stop")
    print("=" * 90)

    results = {}

    # ── G: ^GDAXI + Momentum-Filter ──────────────────────────────────────────
    print("\n[G] DAX MOMENTUM-TOM (^GDAXI)")
    r_dax_base = run_pair('^GDAXI', None, None, 'DAX B&H ToM (Baseline)')
    r_dax_mom  = run_pair('^GDAXI', 'momentum_bull', 'Momentum>0', 'DAX ToM + Momentum>0 (12M-1M)')
    print_result(r_dax_base)
    print_result(r_dax_mom)
    results['dax_base'] = r_dax_base
    results['dax_mom']  = r_dax_mom

    # ── H: SPY + StRev-Filter ────────────────────────────────────────────────
    print("\n[H] SPY DOWN-MONTH REVERSAL (SPY)")
    r_spy_base  = run_pair('SPY', None, None, 'SPY B&H ToM (Baseline)')
    r_spy_strev = run_pair('SPY', 'strev_down', 'StRev<0', 'SPY ToM + StRev<0 (Down-Monat)')
    print_result(r_spy_base)
    print_result(r_spy_strev)
    results['spy_base']  = r_spy_base
    results['spy_strev'] = r_spy_strev

    # ── Zusammenfassung ───────────────────────────────────────────────────────
    print("\n" + "=" * 90)
    print("ZUSAMMENFASSUNG (Verbesserung ggü. Baseline)")
    print("=" * 90)
    for tag, base_key, filt_key, ticker in [
        ('G', 'dax_base', 'dax_mom',  '^GDAXI'),
        ('H', 'spy_base', 'spy_strev', 'SPY'),
    ]:
        b = results.get(base_key, {}); f = results.get(filt_key, {})
        if b.get('n') and f.get('n'):
            dsharpe = f['sharpe'] - b['sharpe']
            dwr     = f['win_rate'] - b['win_rate']
            print(f"  [{tag}] {ticker}: Sharpe {b['sharpe']:+.3f} → {f['sharpe']:+.3f} "
                  f"(+{dsharpe:+.3f})  WR {b['win_rate']:.1f}% → {f['win_rate']:.1f}% "
                  f"({dwr:+.1f}pp)  n_trades: {b['n']} → {f['n']}")

    return results


if __name__ == '__main__':
    main()
