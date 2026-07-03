"""
scripts/backtest_newsletter_scoring.py — Backtest des Newsletter-Scoring-Systems
================================================================================
PER-TICKER-Edge-Profiling: "Für WELCHE Ticker sagt ein höherer Score bessere
Forward-Renditen voraus — und für welche nicht?" Ein Sammel-Pooling über alle
Ticker ist zu pauschal (positive und negative Einzel-Edges heben sich auf). Der
Score darf beim SPY funktionieren und bei EURUSD=X nicht — das ist normal.

Je Ticker × Score-Typ (SC/TS/GESAMT) × Haltedauer (1/5/10/15/20 HT):
  - Spearman ρ(Score, Forward-Rendite) + p-Wert + n  → ρ>0 = Score trägt für diesen Ticker.
  - Top-minus-Bottom-Spread: Ø-Rendite der höchsten vs niedrigsten Score-Tail (Ø-DD dazu).
  - Verdict je Ticker×Score-Typ: "funktioniert" (ρ≥ρ_min, signifikant) / "invers" / "neutral".
Ergebnis: eine Shortlist "Score-funktioniert-Ticker" vs "ignorieren" — je SC/TS/GESAMT getrennt.

Look-ahead-frei:
  - TS: kausale Indikatoren (LBR=EMA, RSI) → einmal vektorisiert, bei t ausgelesen.
        Weekly via resample('W-FRI') + kausaler ffill (letzter abgeschlossener Wochen-Bar).
  - SC: Expanding-Window PRO KALENDERJAHR — an Tag t in Jahr Y nur Bars < 01.01.Y.
  - Entry = Close[t]; Score nutzt nur Daten <= t → kein Look-ahead ins Forward-Fenster.

Ausgabe: Konsole (Leaderboard je Score-Typ) + CSV (je Ticker×Score×Haltedauer) +
JSON (landing/data/score_backtest_results.{csv,json}) mit tickers{} + shortlists{}.

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
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from shared.symbols import get_symbols_by_category, get_all_tickers          # noqa: E402
from shared.daily_report import NEWSLETTER_CORE_LIST, TDOM_STRATEGIES        # noqa: E402
from shared.data import download_data                                        # noqa: E402
from shared.yahoo_downloader import preprocess, clear_cache                  # noqa: E402
from shared.tdom_analysis import add_tdom_columns, build_tdom_stats          # noqa: E402
from shared.indicators import calc_lbr, calc_rsi                             # noqa: E402

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
    # Nicht-positive Preise = Daten-Artefakte (Stooq-Alt-Daten / additive Split-Adjustierung
    # kann sehr alte Bars auf <=0 drücken). Sie erzeugen sonst unmögliche Ratios
    # (ret < -100 %, dd < -100 %) und vergiften vor allem worst_drawdown (min → Ausreißer dominiert).
    close = df["Close"].where(df["Close"] > 0)
    low = df["Low"].where(df["Low"] > 0)
    out = {}
    for N in holdings:
        ret = (close.shift(-N) / close - 1.0) * 100.0
        dd_low = low.rolling(N).min().shift(-N)   # min(Low[t+1..t+N])
        dd = (dd_low / close - 1.0) * 100.0
        # Long-Position kann höchstens -100 % verlieren; alles darunter = Artefakt-Rest → Floor.
        dd = dd.clip(lower=-100.0)
        out[N] = (ret.to_numpy(), dd.to_numpy())
    return out


# ─────────────────────────────────────────────────────────────── Per-Ticker-Edge
def _bucket_stats(r: np.ndarray, d: np.ndarray) -> dict:
    dv = d[~np.isnan(d)]
    return {
        "n": int(r.size),
        "avg_return": _clean(r.mean()) if r.size else None,
        "win_rate": _clean((r > 0).mean() * 100) if r.size else None,
        "avg_drawdown": _clean(dv.mean()) if dv.size else None,
    }


def _tail_masks(s: np.ndarray, frac: float = 0.20):
    """Höchste vs niedrigste Score-Werte, je bis ~frac der Beobachtungen abgedeckt.
    Robust gegen wenige distinkte Score-Stufen; None,None wenn Top/Bottom überlappen."""
    uniq = np.unique(s)
    if uniq.size < 2:
        return None, None
    n = s.size
    bot = np.zeros(n, dtype=bool)
    cum = 0
    for v in uniq:
        m = s == v
        bot |= m; cum += int(m.sum())
        if cum >= frac * n:
            break
    top = np.zeros(n, dtype=bool)
    cum = 0
    for v in uniq[::-1]:
        m = s == v
        top |= m; cum += int(m.sum())
        if cum >= frac * n:
            break
    if (top & bot).any():          # zu wenig Trennschärfe (dominante Mode)
        return None, None
    return top, bot


def _verdict(rho, p, n: int, min_n: int, rho_min: float) -> str:
    if n < min_n or rho is None or p is None:
        return "n/a"
    if p < 0.05 and rho >= rho_min:
        return "funktioniert"
    if p < 0.05 and rho <= -rho_min:
        return "invers"
    return "neutral"


def _edge_for(score: np.ndarray, ret: np.ndarray, dd: np.ndarray,
              min_n: int, rho_min: float) -> dict:
    mask = ~np.isnan(score) & ~np.isnan(ret)
    s, r, d = score[mask], ret[mask], dd[mask]
    n = int(s.size)
    cell = {"n": n, "rho": None, "p": None, "spread": None,
            "top": None, "bottom": None, "verdict": "n/a"}
    if n < max(min_n, 20):
        return cell
    if not np.all(s == s[0]):
        rr, pp = spearmanr(s, r)
        cell["rho"], cell["p"] = _clean(rr, 4), _clean(pp, 6)
    top_m, bot_m = _tail_masks(s)
    if top_m is not None:
        top = _bucket_stats(r[top_m], d[top_m])
        bot = _bucket_stats(r[bot_m], d[bot_m])
        cell["top"], cell["bottom"] = top, bot
        if top["avg_return"] is not None and bot["avg_return"] is not None:
            cell["spread"] = _clean(top["avg_return"] - bot["avg_return"])
    cell["verdict"] = _verdict(cell["rho"], cell["p"], n, min_n, rho_min)
    return cell


def analyze_ticker(ticker: str, holdings: list[int], min_prior_years: int,
                   min_n: int, rho_min: float) -> "dict | None":
    df = load_history(ticker, holdings)
    if df is None:
        return None
    df = add_tdom_columns(df)
    ts = compute_ts_series(df)
    tdom_arr = df["tdom"].to_numpy()
    years_arr = df["year"].to_numpy()
    sc = compute_sc_series(df, tdom_arr, years_arr, min_prior_years)
    gesamt = np.where(~np.isnan(ts) & ~np.isnan(sc), ts + sc, np.nan)
    fwd = forward_metrics(df, holdings)

    out = {"n_bars": int(len(df)),
           "start": df["Date"].iloc[0].strftime("%Y-%m-%d") if "Date" in df.columns
                    else df.index[0].strftime("%Y-%m-%d"),
           "end": df["Date"].iloc[-1].strftime("%Y-%m-%d") if "Date" in df.columns
                  else df.index[-1].strftime("%Y-%m-%d")}
    for st, score in (("SC", sc), ("TS", ts), ("GESAMT", gesamt)):
        out[st] = {}
        for N in holdings:
            ret, dd = fwd[N]
            out[st][str(N)] = _edge_for(score, ret, dd, min_n, rho_min)
    return out


# ─────────────────── Out-of-Sample: Regime aus TRAIN, TS_adj = sign·TS im TEST ───────────────────
def _rho_sub(score: np.ndarray, ret: np.ndarray, sub: np.ndarray, min_n: int):
    """Spearman ρ auf der Teilmenge `sub` (bool), None wenn zu wenig/konstant."""
    m = sub & ~np.isnan(score) & ~np.isnan(ret)
    if int(m.sum()) < min_n:
        return None, int(m.sum())
    s, r = score[m], ret[m]
    if np.all(s == s[0]):
        return None, int(m.sum())
    rr, _ = spearmanr(s, r)
    return _clean(rr, 4), int(m.sum())


def analyze_ticker_oos(ticker: str, holdings: list[int], min_prior_years: int,
                       min_n: int, split_frac: float, class_thr: float,
                       class_holdings: list[int]) -> "dict | None":
    df = load_history(ticker, holdings)
    if df is None:
        return None
    df = add_tdom_columns(df)
    ts = compute_ts_series(df)
    sc = compute_sc_series(df, df["tdom"].to_numpy(), df["year"].to_numpy(), min_prior_years)
    gesamt = np.where(~np.isnan(ts) & ~np.isnan(sc), ts + sc, np.nan)
    fwd = forward_metrics(df, holdings)

    n = len(df)
    split_i = int(n * split_frac)
    is_train = np.arange(n) < split_i
    is_test = ~is_train

    out = {"n_bars": int(n)}
    for st, score in (("SC", sc), ("TS", ts), ("GESAMT", gesamt)):
        # Regime aus TRAIN: ø ρ über class_holdings (nur Train-Bars)
        tr = [_rho_sub(score, fwd[N][0], is_train, min_n)[0] for N in class_holdings]
        tr = [x for x in tr if x is not None]
        if len(tr) >= max(2, (len(class_holdings) + 1) // 2):
            mean_train = float(np.mean(tr))
            sign = 1 if mean_train >= class_thr else (-1 if mean_train <= -class_thr else 0)
            regime = "momentum" if sign > 0 else ("fade" if sign < 0 else "neutral")
        else:
            mean_train, sign, regime = None, 0, "n/a"
        test, adj = {}, {}
        for N in holdings:
            rt, nt = _rho_sub(score, fwd[N][0], is_test, min_n)
            test[str(N)] = rt
            adj[str(N)] = (round(sign * rt, 4) if (rt is not None and sign != 0) else None)
        out[st] = {"regime": regime, "sign": sign, "mean_rho_train": mean_train,
                   "test": test, "adj": adj}
    return out


def aggregate_oos(per: dict, holdings: list[int], class_holdings: list[int]) -> dict:
    summ = {}
    for st in ("SC", "TS", "GESAMT"):
        counts = {"momentum": 0, "fade": 0, "neutral": 0, "n/a": 0}
        for d in per.values():
            counts[d[st]["regime"]] = counts.get(d[st]["regime"], 0) + 1
        byN = {}
        for N in holdings:
            raw = [d[st]["test"][str(N)] for d in per.values() if d[st]["test"][str(N)] is not None]
            adj = [d[st]["adj"][str(N)] for d in per.values() if d[st]["adj"][str(N)] is not None]
            # Vorzeichen-Persistenz: unter nicht-neutralen Tickern, Anteil sign(test)==sign(train)
            pers = [1.0 if (np.sign(d[st]["test"][str(N)]) == d[st]["sign"]) else 0.0
                    for d in per.values()
                    if d[st]["sign"] != 0 and d[st]["test"][str(N)] is not None]
            byN[str(N)] = {
                "rho_test_raw": _clean(np.mean(raw)) if raw else None,
                "rho_test_adj": _clean(np.mean(adj)) if adj else None,
                "sign_persist": _clean(np.mean(pers) * 100, 1) if pers else None,
                "n_raw": len(raw), "n_adj": len(adj),
            }
        summ[st] = {"counts": counts, "by_holding": byN}
    return summ


def print_oos(summ: dict, per: dict, class_holdings: list[int], holdings: list[int],
              split_frac: float):
    ch = "+".join(str(h) for h in class_holdings)
    print(f"\n{'='*74}")
    print(f"  OUT-OF-SAMPLE REGIME-ADJUSTMENT  ·  Split {split_frac:.0%} Train → {1-split_frac:.0%} Test")
    print(f"  Regime aus Train (ø ρ über {ch}HT) → TS_adj = sign·Score im Test  ·  {len(per)} Ticker")
    print('='*74)
    for st in ("SC", "TS", "GESAMT"):
        c = summ[st]["counts"]
        print(f"\n═══ {st} ═══   Train-Regime: ↗ {c['momentum']} mom · ↘ {c['fade']} fade · "
              f"➖ {c['neutral']} neutral · {c.get('n/a',0)} n/a")
        print(f"  {'N':>3} | {'ρ_test RAW':>10} | {'ρ_test ADJ':>10} | {'Δ':>7} | {'sign-persist':>12} | n_adj")
        for N in holdings:
            b = summ[st]["by_holding"][str(N)]
            raw = f"{b['rho_test_raw']:+.4f}" if b["rho_test_raw"] is not None else "   n/a"
            adj = f"{b['rho_test_adj']:+.4f}" if b["rho_test_adj"] is not None else "   n/a"
            delta = (f"{b['rho_test_adj']-b['rho_test_raw']:+.4f}"
                     if (b["rho_test_adj"] is not None and b["rho_test_raw"] is not None) else "   n/a")
            sp = f"{b['sign_persist']:.1f}%" if b["sign_persist"] is not None else "  n/a"
            print(f"  {N:>3} | {raw:>10} | {adj:>10} | {delta:>7} | {sp:>12} | {b['n_adj']:>5}")


# ─────────────────────────────────────────────────────────────── Shortlists / Ausgabe
def build_shortlists(per_ticker: dict, headline: int) -> dict:
    h = str(headline)
    lists = {st: {"funktioniert": [], "invers": [], "neutral": [], "n/a": []}
             for st in ("SC", "TS", "GESAMT")}
    for tk, d in per_ticker.items():
        for st in ("SC", "TS", "GESAMT"):
            cell = d.get(st, {}).get(h)
            if not cell:
                continue
            lists[st][cell["verdict"]].append(
                {"ticker": tk, "rho": cell["rho"], "p": cell["p"],
                 "spread": cell["spread"], "n": cell["n"]})
    for st in lists:
        lists[st]["funktioniert"].sort(key=lambda e: -(e["rho"] or 0))
        lists[st]["invers"].sort(key=lambda e: (e["rho"] if e["rho"] is not None else 0))
        lists[st]["neutral"].sort(key=lambda e: -(e["rho"] or 0))
    return lists


# ── Regime-Dreiteilung: momentum (ρ konsistent > 0) / fade (ρ konsistent < 0) / neutral ──
def classify_ticker_score(cells: dict, class_holdings: list[int],
                          class_thr: float, min_n: int) -> dict:
    """Klassifiziert einen (Ticker, Score-Typ) über MEHRERE Haltedauern (N=1 ausgeschlossen,
    zu mikrostruktur-verrauscht). 'momentum' = mean ρ ≥ +thr und Vorzeichen konsistent (≥80 %
    der Horizonte gleich), 'fade' = spiegelbildlich negativ, sonst 'neutral'."""
    rhos = [cells[str(N)]["rho"] for N in class_holdings
            if cells.get(str(N)) and cells[str(N)]["rho"] is not None
            and cells[str(N)]["n"] >= min_n]
    if len(rhos) < max(2, (len(class_holdings) + 1) // 2):
        return {"label": "n/a", "mean_rho": None}
    arr = np.array(rhos, dtype=float)
    m = float(arr.mean())
    same = float((np.sign(arr) == np.sign(m)).mean()) if m != 0 else 0.0
    if m >= class_thr and same >= 0.8:
        label = "momentum"
    elif m <= -class_thr and same >= 0.8:
        label = "fade"
    else:
        label = "neutral"
    return {"label": label, "mean_rho": round(m, 4)}


def build_classification(per_ticker: dict, holdings: list[int],
                         class_thr: float, min_n: int):
    class_holdings = [h for h in holdings if h != 1] or list(holdings)
    groups = {st: {"momentum": [], "fade": [], "neutral": [], "n/a": []}
              for st in ("SC", "TS", "GESAMT")}
    for tk, d in per_ticker.items():
        d.setdefault("class", {})
        for st in ("SC", "TS", "GESAMT"):
            cls = classify_ticker_score(d.get(st, {}), class_holdings, class_thr, min_n)
            d["class"][st] = cls
            groups[st][cls["label"]].append({"ticker": tk, "mean_rho": cls["mean_rho"]})
    for st in groups:
        groups[st]["momentum"].sort(key=lambda e: -(e["mean_rho"] or 0))
        groups[st]["fade"].sort(key=lambda e: (e["mean_rho"] if e["mean_rho"] is not None else 0))
        groups[st]["neutral"].sort(key=lambda e: -(e["mean_rho"] or 0))
    return groups, class_holdings


def print_console(per_ticker: dict, classification: dict, class_holdings: list[int],
                  class_thr: float):
    hdr = "+".join(f"{h}" for h in class_holdings)
    print(f"\n{'='*72}")
    print(f"  PER-TICKER REGIME-KLASSIFIKATION  ·  ø ρ über {hdr} HT  ·  Schwelle ±{class_thr}")
    print(f"  {len(per_ticker)} Ticker  ·  momentum = Score-Follow-through · fade = Score gegenläufig")
    print('='*72)

    def fmt(e):
        m = f"{e['mean_rho']:+.3f}" if e["mean_rho"] is not None else "  n/a "
        return f"   {e['ticker']:<11} øρ {m}"

    for st in ("SC", "TS", "GESAMT"):
        g = classification[st]
        nm, nf, nn, nna = (len(g["momentum"]), len(g["fade"]),
                           len(g["neutral"]), len(g["n/a"]))
        print(f"\n═══ {st} ═══   ↗ {nm} momentum · ↘ {nf} fade · ➖ {nn} neutral · {nna} n/a")
        if nm:
            print(f"  ── momentum (Score trägt, Top {min(nm,15)}) ──")
            for e in g["momentum"][:15]:
                print(fmt(e))
        if nf:
            print(f"  ── fade (Score gegenläufig, Top {min(nf,12)}) ──")
            for e in g["fade"][:12]:
                print(fmt(e))


def write_csv(per_ticker: dict, holdings: list[int], path: Path):
    rows = []
    for tk, d in per_ticker.items():
        for st in ("SC", "TS", "GESAMT"):
            for N in holdings:
                c = d.get(st, {}).get(str(N))
                if not c:
                    continue
                top, bot = c.get("top") or {}, c.get("bottom") or {}
                cls = (d.get("class") or {}).get(st) or {}
                rows.append({
                    "ticker": tk, "score_type": st, "holding": int(N),
                    "n": c["n"], "rho": c["rho"], "p": c["p"], "spread": c["spread"],
                    "verdict": c["verdict"],
                    "class": cls.get("label"), "class_mean_rho": cls.get("mean_rho"),
                    "n_bars": d.get("n_bars"),
                    "start": d.get("start"), "end": d.get("end"),
                    "top_ret": top.get("avg_return"), "top_dd": top.get("avg_drawdown"),
                    "top_n": top.get("n"),
                    "bottom_ret": bot.get("avg_return"), "bottom_dd": bot.get("avg_drawdown"),
                    "bottom_n": bot.get("n"),
                })
    pd.DataFrame(rows).to_csv(path, index=False)


def write_json(per_ticker: dict, shortlists: dict, classification: dict,
               meta: dict, path: Path):
    path.write_text(json.dumps({"meta": meta, "tickers": per_ticker,
                                "classification": classification, "shortlists": shortlists},
                               indent=2, ensure_ascii=False), encoding="utf-8")


# ─────────────────────────────────────────────────────────────── main
def main() -> int:
    ap = argparse.ArgumentParser(description="Per-Ticker-Backtest Newsletter-Scoring (SC/TS/Gesamt → Edge je Ticker)")
    ap.add_argument("--universe", default="newsletter", choices=["newsletter", "core", "all"])
    ap.add_argument("--only", help="Komma-Liste, ueberschreibt --universe (z.B. SPY,QQQ)")
    ap.add_argument("--holding", default="1,5,10,15,20", help="Haltedauern in Handelstagen")
    ap.add_argument("--min-prior-years", type=int, default=3)
    ap.add_argument("--min-n", type=int, default=250,
                    help="Min. Paar-Beobachtungen je Ticker×Score×Haltedauer für ein Verdict")
    ap.add_argument("--rho-min", type=float, default=0.03,
                    help="|Spearman ρ|-Schwelle für 'funktioniert'/'invers'")
    ap.add_argument("--headline-holding", type=int, default=10,
                    help="Haltedauer für Shortlist/Leaderboard-Verdict")
    ap.add_argument("--class-threshold", type=float, default=0.05,
                    help="|ø ρ|-Schwelle für momentum/fade-Klassifikation (über Haltedauern >1)")
    ap.add_argument("--reclassify", metavar="JSON",
                    help="Nur neu klassifizieren aus vorhandener Ergebnis-JSON (kein Neu-Lauf)")
    ap.add_argument("--oos-split", type=float, metavar="FRAC",
                    help="Out-of-Sample-Test: Regime aus ersten FRAC der Historie, TS_adj im Rest "
                         "(z.B. 0.6). Schreibt <out>_oos.{json} statt Standard-Lauf.")
    ap.add_argument("--limit", type=int, help="max. Ticker (Sanity)")
    ap.add_argument("--progress-every", type=int, default=10)
    ap.add_argument("--out", default="landing/data/score_backtest_results",
                    help="Basispfad (→ .csv + .json)")
    a = ap.parse_args()

    holdings = [int(x) for x in a.holding.split(",") if x.strip()]

    # ── Reclassify-Modus: rohe ρ sind schwellenunabhängig → ohne 40-Min-Neulauf umgruppieren ──
    if a.reclassify:
        src = json.load(open(a.reclassify, encoding="utf-8"))
        per_ticker = src["tickers"]
        holdings = src.get("meta", {}).get("holdings", holdings)
        if a.headline_holding not in holdings:
            a.headline_holding = holdings[min(len(holdings) - 1, 2)]
        shortlists = build_shortlists(per_ticker, a.headline_holding)
        classification, class_holdings = build_classification(
            per_ticker, holdings, a.class_threshold, a.min_n)
        meta = dict(src.get("meta", {}))
        meta.update({"reclassified_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                     "class_threshold": a.class_threshold, "class_holdings": class_holdings})
        out_base = _ROOT / a.out if not Path(a.out).is_absolute() else Path(a.out)
        out_base.parent.mkdir(parents=True, exist_ok=True)
        write_csv(per_ticker, holdings, out_base.with_suffix(".csv"))
        write_json(per_ticker, shortlists, classification, meta, out_base.with_suffix(".json"))
        print_console(per_ticker, classification, class_holdings, a.class_threshold)
        print(f"\n[backtest] reclassify fertig — {len(per_ticker)} Ticker aus {a.reclassify}")
        print(f"[backtest] JSON -> {out_base.with_suffix('.json')}")
        return 0

    if a.headline_holding not in holdings:
        a.headline_holding = holdings[min(len(holdings) - 1, 2)]
    tickers = load_universe(a.universe, a.only)
    if a.limit:
        tickers = tickers[:a.limit]

    # ── Out-of-Sample-Modus: Regime aus Train, TS_adj im Test — ehrlicher Persistenz-Test ──
    if a.oos_split:
        class_holdings = [h for h in holdings if h != 1] or list(holdings)
        print(f"[backtest] OOS '{a.universe}': {len(tickers)} Ticker · Split {a.oos_split:.0%} · "
              f"Regime über {class_holdings}HT · min_n {a.min_n} · thr {a.class_threshold}")
        per: dict = {}
        t0 = time.time()
        ok = fail = skip = 0
        for i, tk in enumerate(tickers, 1):
            try:
                r = analyze_ticker_oos(tk, holdings, a.min_prior_years, a.min_n,
                                       a.oos_split, a.class_threshold, class_holdings)
                if r is None:
                    skip += 1
                else:
                    per[tk] = r; ok += 1
            except Exception as e:
                fail += 1
                print(f"  [WARN] {tk}: {type(e).__name__}: {e}", flush=True)
            finally:
                clear_cache(); gc.collect()
            if i % a.progress_every == 0 or i == len(tickers):
                print(f"  [{i}/{len(tickers)}] {tk} · {time.time()-t0:.0f}s", flush=True)
        summ = aggregate_oos(per, holdings, class_holdings)
        meta = {
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "mode": "oos", "universe": a.universe, "n_ok": ok, "n_skip": skip, "n_fail": fail,
            "holdings": holdings, "oos_split": a.oos_split, "class_holdings": class_holdings,
            "class_threshold": a.class_threshold, "min_n": a.min_n,
        }
        out_base = _ROOT / a.out if not Path(a.out).is_absolute() else Path(a.out)
        oos_path = out_base.with_name(out_base.name + "_oos").with_suffix(".json")
        oos_path.parent.mkdir(parents=True, exist_ok=True)
        oos_path.write_text(json.dumps({"meta": meta, "summary": summ, "tickers": per},
                                       indent=2, ensure_ascii=False), encoding="utf-8")
        print_oos(summ, per, class_holdings, holdings, a.oos_split)
        print(f"\n[backtest] OOS fertig — {ok} ok / {skip} skip / {fail} fail in {time.time()-t0:.0f}s")
        print(f"[backtest] JSON -> {oos_path}")
        return 0

    print(f"[backtest] Universum '{a.universe}': {len(tickers)} Ticker · Haltedauern {holdings} · "
          f"Headline {a.headline_holding}HT · min_n {a.min_n} · ρ_min {a.rho_min}")

    per_ticker: dict = {}
    t0 = time.time()
    ok = fail = skip = 0
    for i, tk in enumerate(tickers, 1):
        try:
            r = analyze_ticker(tk, holdings, a.min_prior_years, a.min_n, a.rho_min)
            if r is None:
                skip += 1
            else:
                per_ticker[tk] = r
                ok += 1
        except Exception as e:
            fail += 1
            print(f"  [WARN] {tk}: {type(e).__name__}: {e}", flush=True)
        finally:
            clear_cache()
            gc.collect()
        if i % a.progress_every == 0 or i == len(tickers):
            print(f"  [{i}/{len(tickers)}] {tk} · {time.time()-t0:.0f}s", flush=True)

    shortlists = build_shortlists(per_ticker, a.headline_holding)
    classification, class_holdings = build_classification(
        per_ticker, holdings, a.class_threshold, a.min_n)
    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "universe": a.universe, "n_tickers": len(tickers),
        "n_ok": ok, "n_skip": skip, "n_fail": fail,
        "holdings": holdings, "headline_holding": a.headline_holding,
        "min_prior_years": a.min_prior_years, "min_n": a.min_n, "rho_min": a.rho_min,
        "class_threshold": a.class_threshold, "class_holdings": class_holdings,
    }

    out_base = _ROOT / a.out if not Path(a.out).is_absolute() else Path(a.out)
    out_base.parent.mkdir(parents=True, exist_ok=True)
    write_csv(per_ticker, holdings, out_base.with_suffix(".csv"))
    write_json(per_ticker, shortlists, classification, meta, out_base.with_suffix(".json"))
    print_console(per_ticker, classification, class_holdings, a.class_threshold)
    print(f"\n[backtest] fertig — {ok} ok / {skip} skip / {fail} fail in {time.time()-t0:.0f}s")
    print(f"[backtest] CSV  -> {out_base.with_suffix('.csv')}")
    print(f"[backtest] JSON -> {out_base.with_suffix('.json')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
