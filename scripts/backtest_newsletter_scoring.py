"""
scripts/backtest_newsletter_scoring.py — Backtest des Newsletter-Scoring-Systems
================================================================================
Misst den empirischen Edge je Score-Stufe: "Wenn ein Ticker an Tag t Score X hatte,
wie lief er die naechsten 1/5/10/15/20 Handelstage (Oe-Rendite, Trefferquote,
Drawdown)?" — getrennt nach SC (Saisonal, 0-4), TS (LBR/RSI/RSI3/BlastOff) und
GESAMT (SC+TS).

Look-ahead-frei:
  - TS: kausale Indikatoren (LBR=EMA, RSI) → einmal vektorisiert, bei t ausgelesen.
        Weekly via resample('W-FRI') + kausaler ffill (letzter abgeschlossener Wochen-Bar).
  - SC: Expanding-Window PRO KALENDERJAHR — an Tag t in Jahr Y nur Bars < 01.01.Y.
  - Entry = Close[t]; Score nutzt nur Daten <= t → kein Look-ahead ins Forward-Fenster.

Ausgabe: Konsole + CSV + JSON (landing/data/score_backtest_results.{csv,json}) +
Signifikanz je Bucket (t/p/Cohen d/Relevance).

Aufruf (Windows):
  PYTHONUTF8=1 py -3.14 scripts/backtest_newsletter_scoring.py --universe newsletter
  PYTHONUTF8=1 py -3.14 scripts/backtest_newsletter_scoring.py --only SPY --holding 1,5,10
"""
from __future__ import annotations

import argparse
import gc
import json
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from shared.symbols import get_symbols_by_category, get_all_tickers          # noqa: E402
from shared.daily_report import NEWSLETTER_CORE_LIST, TDOM_STRATEGIES        # noqa: E402
from shared.data import download_data                                        # noqa: E402
from shared.yahoo_downloader import preprocess, clear_cache                  # noqa: E402
from shared.tdom_analysis import add_tdom_columns, build_tdom_stats          # noqa: E402
from shared.indicators import calc_lbr, calc_rsi                             # noqa: E402
from shared.significance_gauge import run_significance_test                  # noqa: E402

_MIN_DAILY = 40      # analog newsletter_indicators._MIN_DAILY_BARS
_MIN_WEEKLY = 30     # analog _MIN_WEEKLY_BARS
DEFAULT_HOLDINGS = [1, 5, 10, 15, 20]


def _clean(v, dec: int = 4):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    if np.isnan(f) or np.isinf(f):
        return None
    return round(f, dec)


# ─────────────────────────────────────────────────────────────── Universum
def load_universe(which: str, only: str | None = None) -> list[str]:
    if only:
        return [t.strip() for t in only.split(",") if t.strip()]
    if which == "core":
        return list(NEWSLETTER_CORE_LIST)
    if which == "all":
        return get_all_tickers()
    # "newsletter" (default): Kernliste + genau die Kategorien, aus denen top_daily_tips waehlt
    tickers = set(NEWSLETTER_CORE_LIST)
    for cat in ("US-ETF", "US-Aktie", "EU-Aktie"):
        try:
            d = get_symbols_by_category(cat)
        except Exception:
            continue
        tickers.update(d.keys() if isinstance(d, dict) else d)
    return sorted(tickers)


# ─────────────────────────────────────────────────────────────── Daten
def load_history(ticker: str, holdings: list[int]) -> "pd.DataFrame | None":
    try:
        raw = download_data(ticker, period="max")
    except Exception:
        return None
    if raw is None or len(raw) == 0:
        return None
    df = preprocess(raw)
    if "Date" in df.columns:
        df = df.set_index(pd.to_datetime(df["Date"]))
    else:
        df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    for c in ("Open", "High", "Low", "Close", "year", "month"):
        if c not in df.columns:
            return None
    if len(df) < _MIN_DAILY + max(holdings) + 5:
        return None
    return df


# ─────────────────────────────────────────────────────────────── TS (vektorisiert, kausal)
def compute_ts_series(df: "pd.DataFrame") -> np.ndarray:
    close = df["Close"]
    lbr_d = calc_lbr(close)["fastline"]
    rsi_d = calc_rsi(close, period=14)
    rsi3 = calc_rsi(close, period=3)

    weekly = close.resample("W-FRI").last().dropna()
    if len(weekly) >= _MIN_WEEKLY:
        lbr_w_s = calc_lbr(weekly)["fastline"].copy()
        rsi_w_s = calc_rsi(weekly, period=14).copy()
        lbr_w_s.iloc[:_MIN_WEEKLY] = np.nan   # erste Wochen unzuverlaessig
        rsi_w_s.iloc[:_MIN_WEEKLY] = np.nan
        lbr_w = lbr_w_s.reindex(df.index, method="ffill")   # letzter abgeschl. Wochen-Bar (kausal)
        rsi_w = rsi_w_s.reindex(df.index, method="ffill")
    else:
        lbr_w = pd.Series(np.nan, index=df.index)
        rsi_w = pd.Series(np.nan, index=df.index)

    hl = df["High"] - df["Low"]
    bo = (np.abs(df["Open"] - df["Close"]) / hl.where(hl > 0)) * 100.0

    ld, lw = lbr_d.to_numpy(), lbr_w.to_numpy()
    rd, rw, r3 = rsi_d.to_numpy(), rsi_w.to_numpy(), rsi3.to_numpy()
    b = bo.to_numpy()

    # Score-Formel 1:1 aus shared/newsletter_indicators.py (NaN-Vergleich → False = "None skippen")
    ts = np.zeros(len(df), dtype=float)
    ts += (lw > 0)
    ts += (ld > 0)
    ts += (rw > 50)
    ts -= (rd > 90) & (rw > 90)
    ts += (rd < 10) & (rw < 10)
    ts += (r3 <= 20) & (ld > 0)
    ts -= (r3 >= 80) & (ld < 0)
    ts += (b < 20) & (ld > 0)
    ts -= (b < 20) & (ld < 0)

    valid = (np.arange(len(df)) >= _MIN_DAILY) & ~np.isnan(ld)
    return np.where(valid, ts, np.nan)


# ─────────────────────────────────────────────────────────────── SC (Expanding-Window pro Jahr)
def compute_sc_series(df: "pd.DataFrame", tdom_arr: np.ndarray, years_arr: np.ndarray,
                      min_prior_years: int) -> np.ndarray:
    uniq_years = sorted({int(y) for y in years_arr})
    first_year = uniq_years[0]
    sc_by_year: dict[int, dict[int, int]] = {}
    for Y in uniq_years:
        if Y - first_year < min_prior_years:
            continue
        prior = df[df.index < pd.Timestamp(Y, 1, 1)]
        if len(prior) < _MIN_DAILY * 3:
            continue
        hits: dict[int, int] = {}
        ok = True
        for strat in TDOM_STRATEGIES:
            try:
                stats = build_tdom_stats(prior, strat, direction="forward")
            except Exception:
                ok = False
                break
            for tdom, row in stats.iterrows():
                hits[int(tdom)] = hits.get(int(tdom), 0) + (1 if row["avg_return"] > 0 else 0)
        if ok and hits:
            sc_by_year[Y] = hits

    sc = np.full(len(df), np.nan)
    for i in range(len(df)):
        y, td = int(years_arr[i]), int(tdom_arr[i])
        tbl = sc_by_year.get(y)
        if tbl is not None and td in tbl:
            sc[i] = tbl[td]
    return sc


# ─────────────────────────────────────────────────────────────── Forward-Metriken (vektorisiert)
def forward_metrics(df: "pd.DataFrame", holdings: list[int]) -> dict:
    close, low = df["Close"], df["Low"]
    out = {}
    for N in holdings:
        ret = (close.shift(-N) / close - 1.0) * 100.0
        dd_low = low.rolling(N).min().shift(-N)   # min(Low[t+1..t+N])
        dd = (dd_low / close - 1.0) * 100.0
        out[N] = (ret.to_numpy(), dd.to_numpy())
    return out


def _new_collectors():
    return {st: defaultdict(lambda: defaultdict(lambda: {"ret": [], "dd": []}))
            for st in ("SC", "TS", "GESAMT")}


def process_ticker(ticker: str, holdings: list[int], collectors: dict, min_prior_years: int) -> int:
    df = load_history(ticker, holdings)
    if df is None:
        return 0
    df = add_tdom_columns(df)
    ts = compute_ts_series(df)
    tdom_arr = df["tdom"].to_numpy()
    years_arr = df["year"].to_numpy()
    sc = compute_sc_series(df, tdom_arr, years_arr, min_prior_years)
    fwd = forward_metrics(df, holdings)

    n = len(df)
    added = 0
    for i in range(n):
        ts_i, sc_i = ts[i], sc[i]
        ts_ok = not np.isnan(ts_i)
        sc_ok = not np.isnan(sc_i)
        if not (ts_ok or sc_ok):
            continue
        for N in holdings:
            ret, dd = fwd[N]
            r, d = ret[i], dd[i]
            if np.isnan(r):
                continue
            if ts_ok:
                c = collectors["TS"][int(ts_i)][N]
                c["ret"].append(float(r)); c["dd"].append(float(d))
            if sc_ok:
                c = collectors["SC"][int(sc_i)][N]
                c["ret"].append(float(r)); c["dd"].append(float(d))
            if ts_ok and sc_ok:
                c = collectors["GESAMT"][int(ts_i) + int(sc_i)][N]
                c["ret"].append(float(r)); c["dd"].append(float(d))
                added += 1
    return added


# ─────────────────────────────────────────────────────────────── Aggregation / Signifikanz
def aggregate(collectors: dict, min_n: int) -> dict:
    res = {}
    for st, buckets in collectors.items():
        res[st] = {}
        for bucket in sorted(buckets):
            byN = buckets[bucket]
            res[st][str(bucket)] = {}
            for N in sorted(byN):
                rets = np.asarray(byN[N]["ret"], dtype=float)
                dds = np.asarray(byN[N]["dd"], dtype=float)
                if rets.size == 0:
                    continue
                res[st][str(bucket)][str(N)] = {
                    "n": int(rets.size),
                    "avg_return": _clean(rets.mean()),
                    "median": _clean(np.median(rets)),
                    "win_rate": _clean((rets > 0).mean() * 100),
                    "avg_drawdown": _clean(dds.mean()),
                    "worst_drawdown": _clean(dds.min()),
                    "std": _clean(rets.std(ddof=1)) if rets.size > 1 else None,
                    "low_sample": bool(rets.size < min_n),
                }
    return res


def compute_significance(collectors: dict, holdings: list[int]) -> dict:
    out = {}
    for st, buckets in collectors.items():
        out[st] = {}
        for N in holdings:
            groups = {}
            for bucket in sorted(buckets):
                rets = buckets[bucket].get(N, {}).get("ret", [])
                if len(rets) >= 5:
                    groups[f"{st}={bucket}"] = list(rets)
            if groups:
                try:
                    out[st][str(N)] = run_significance_test(groups)
                except Exception:
                    out[st][str(N)] = []
    return out


# ─────────────────────────────────────────────────────────────── Ausgabe
def print_console(res: dict, holdings: list[int]):
    for st in ("SC", "TS", "GESAMT"):
        if st not in res or not res[st]:
            continue
        print(f"\n═══ {st} — Ø Forward-Rendite % (Win-Rate %) je Haltedauer ═══")
        hdr = "Bucket │ " + " │ ".join(f"{N:>2}d" for N in holdings) + " │      n"
        print(hdr); print("─" * len(hdr))
        for bucket in sorted(res[st], key=lambda x: int(x)):
            cells, nmax = [], 0
            for N in holdings:
                s = res[st][bucket].get(str(N))
                if s:
                    cells.append(f"{s['avg_return']:+5.2f}({s['win_rate']:.0f})")
                    nmax = max(nmax, s["n"])
                else:
                    cells.append("   —   ")
            print(f"{bucket:>6} │ " + " │ ".join(f"{c:>10}" for c in cells) + f" │ {nmax:>7}")
        # Drawdown-Block
        print(f"   ── {st} · Worst-Drawdown % je Haltedauer ──")
        for bucket in sorted(res[st], key=lambda x: int(x)):
            cells = []
            for N in holdings:
                s = res[st][bucket].get(str(N))
                cells.append(f"{s['worst_drawdown']:+6.1f}" if s else "   —  ")
            print(f"{bucket:>6} │ " + " │ ".join(f"{c:>7}" for c in cells))


def write_csv(res: dict, path: Path):
    rows = []
    for st, buckets in res.items():
        for bucket, byN in buckets.items():
            for N, s in byN.items():
                rows.append({"score_type": st, "bucket": bucket, "holding": int(N), **s})
    pd.DataFrame(rows).to_csv(path, index=False)


def write_json(res: dict, sig: dict, meta: dict, path: Path):
    path.write_text(json.dumps({"meta": meta, "results": res, "significance": sig},
                               indent=2, ensure_ascii=False), encoding="utf-8")


# ─────────────────────────────────────────────────────────────── main
def main() -> int:
    ap = argparse.ArgumentParser(description="Backtest Newsletter-Scoring (SC/TS/Gesamt → Forward-Perf/Drawdown)")
    ap.add_argument("--universe", default="newsletter", choices=["newsletter", "core", "all"])
    ap.add_argument("--only", help="Komma-Liste, ueberschreibt --universe (z.B. SPY,QQQ)")
    ap.add_argument("--holding", default="1,5,10,15,20", help="Haltedauern in Handelstagen")
    ap.add_argument("--min-prior-years", type=int, default=3)
    ap.add_argument("--min-n", type=int, default=30)
    ap.add_argument("--limit", type=int, help="max. Ticker (Sanity)")
    ap.add_argument("--progress-every", type=int, default=10)
    ap.add_argument("--out", default="landing/data/score_backtest_results",
                    help="Basispfad (→ .csv + .json)")
    a = ap.parse_args()

    holdings = [int(x) for x in a.holding.split(",") if x.strip()]
    tickers = load_universe(a.universe, a.only)
    if a.limit:
        tickers = tickers[:a.limit]
    print(f"[backtest] Universum '{a.universe}': {len(tickers)} Ticker · Haltedauern {holdings}")

    collectors = _new_collectors()
    t0 = time.time()
    ok = fail = 0
    for i, tk in enumerate(tickers, 1):
        try:
            added = process_ticker(tk, holdings, collectors, a.min_prior_years)
            ok += 1 if added or True else 0
        except Exception as e:
            fail += 1
            print(f"  [WARN] {tk}: {type(e).__name__}: {e}", flush=True)
        finally:
            clear_cache()
            gc.collect()
        if i % a.progress_every == 0 or i == len(tickers):
            print(f"  [{i}/{len(tickers)}] {tk} · {time.time()-t0:.0f}s", flush=True)

    res = aggregate(collectors, a.min_n)
    sig = compute_significance(collectors, holdings)
    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "universe": a.universe, "n_tickers": len(tickers), "n_ok": ok, "n_fail": fail,
        "holdings": holdings, "min_prior_years": a.min_prior_years, "min_n": a.min_n,
    }

    out_base = _ROOT / a.out if not Path(a.out).is_absolute() else Path(a.out)
    out_base.parent.mkdir(parents=True, exist_ok=True)
    write_csv(res, out_base.with_suffix(".csv"))
    write_json(res, sig, meta, out_base.with_suffix(".json"))
    print_console(res, holdings)
    print(f"\n[backtest] fertig — {ok} ok / {fail} fail in {time.time()-t0:.0f}s")
    print(f"[backtest] CSV  -> {out_base.with_suffix('.csv')}")
    print(f"[backtest] JSON -> {out_base.with_suffix('.json')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
