"""
scripts/research/etf_seasonal_scan.py — Saisonalitaets-Scan ueber die US-ETFs
=============================================================================
Testet jede Saisonalitaets-Strategie auf jedem US-ETF, jeweils ungefiltert und
mit den technischen Filtern LBR / RSI / Bollinger. Bewertet die Ergebnisse mit
einer Statistik, die dem Data-Mining-Problem Rechnung traegt.

WARUM SO STRENG:
  40 ETFs x 22 Strategien x 4 Varianten = 3.520 Tests. Bei alpha=0.05 liefert
  reiner Zufall daraus ~176 "signifikante" Ergebnisse. Ohne Korrektur ist jede
  Bestenliste hauptsaechlich Rauschen. Deshalb:
    1. Walk-Forward-Split: In-Sample bis SPLIT_DATE, Out-of-Sample danach.
       Ein Kandidat muss in BEIDEN Perioden liefern.
    2. Benjamini-Hochberg-FDR ueber alle Tests statt Einzel-p-Werte.
    3. Deflated Sharpe Ratio (Bailey & Lopez de Prado 2014), die den beobachteten
       Sharpe um die Anzahl der Versuche und die Nicht-Normalitaet der Renditen
       bereinigt.
    4. Mindest-Tradezahl, sonst ist der Sharpe ohnehin bedeutungslos.

Alle Indikatoren sind 1:1-Ports aus landing/js/indicators.js und greifen — wie
dort — auf Index i-1 zu, sind also look-ahead-bias-frei.

Aufruf:
  SB_URL=... SB_KEY=... PYTHONUTF8=1 py -3.14 scripts/research/etf_seasonal_scan.py
  ... --tickers SPY,QQQ        (Teilmenge, zum Debuggen)
  ... --no-cache               (Kursdaten neu laden)
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import requests

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from shared.nyse_holidays import get_nyse_holidays  # noqa: E402
from shared.symbols import SYMBOLS  # noqa: E402

CACHE = _ROOT / "scripts" / "research" / ".cache"
OUT = _ROOT / "scripts" / "research" / "out"

SPLIT_DATE = "2016-01-01"   # In-Sample davor, Out-of-Sample danach
MIN_TRADES = 20             # unter dieser Zahl ist jede Statistik Kaffeesatz
MIN_TRADES_OOS = 8


# ══════════════════════════════════════════════════════ Daten
def load_closes(ticker: str, use_cache: bool = True) -> list[dict]:
    CACHE.mkdir(parents=True, exist_ok=True)
    cf = CACHE / f"{ticker.replace('^', '_')}.json"
    if use_cache and cf.exists():
        return json.loads(cf.read_text())
    url, key = os.environ["SB_URL"], os.environ["SB_KEY"]
    h = {"apikey": key, "Authorization": "Bearer " + key}
    out, off = [], 0
    while True:
        r = requests.get(f"{url}/rest/v1/prices",
                         params={"ticker": f"eq.{ticker}", "select": "date,close",
                                 "order": "date.asc", "limit": 1000, "offset": off},
                         headers=h, timeout=60)
        if r.status_code != 200:
            return []
        b = r.json()
        out += [x for x in b if x.get("close") is not None]
        if len(b) < 1000:
            break
        off += 1000
    cf.write_text(json.dumps(out))
    return out


# ══════════════════════════════════════════════════════ Indikatoren (Port aus indicators.js)
def sma(c, p):
    out = [None] * len(c)
    s = 0.0
    for i, v in enumerate(c):
        s += v
        if i >= p:
            s -= c[i - p]
        if i >= p - 1:
            out[i] = s / p
    return out


def ema(c, p):
    out = [None] * len(c)
    if len(c) < p:
        return out
    k = 2 / (p + 1)
    out[p - 1] = sum(c[:p]) / p
    for i in range(p, len(c)):
        out[i] = c[i] * k + out[i - 1] * (1 - k)
    return out


def rsi(c, p=14):
    """Wilder-Glaettung, exakt wie calcRSI in indicators.js."""
    out = [None] * len(c)
    if len(c) < p + 1:
        return out
    gains, losses = [], []
    for i in range(1, len(c)):
        d = c[i] - c[i - 1]
        gains.append(d if d > 0 else 0.0)
        losses.append(-d if d < 0 else 0.0)
    ag = sum(gains[:p]) / p
    al = sum(losses[:p]) / p
    rs = ag / al if al > 0 else 100
    out[p] = 100 - 100 / (1 + rs)
    for i in range(p, len(gains)):
        ag = (ag * (p - 1) + gains[i]) / p
        al = (al * (p - 1) + losses[i]) / p
        rs = ag / al if al > 0 else 100
        out[i + 1] = 100 - 100 / (1 + rs)
    return out


def bollinger(c, p=20, k=2.0):
    mid = sma(c, p)
    up, lo = [None] * len(c), [None] * len(c)
    for i in range(p - 1, len(c)):
        if mid[i] is None:
            continue
        ss = sum((c[j] - mid[i]) ** 2 for j in range(i - p + 1, i + 1))
        sd = math.sqrt(ss / p)
        up[i] = mid[i] + k * sd
        lo[i] = mid[i] - k * sd
    return mid, up, lo


def macd_line(c, fast, slow, signal):
    ef, es = ema(c, fast), ema(c, slow)
    ml = [None if (ef[i] is None or es[i] is None) else ef[i] - es[i] for i in range(len(c))]
    valid = [v for v in ml if v is not None]
    start = next((i for i, v in enumerate(ml) if v is not None), -1)
    sig_e = ema(valid, signal) if valid else []
    sl = [None] * len(c)
    for i, v in enumerate(sig_e):
        if start + i < len(c):
            sl[start + i] = v
    return ml, sl


def lbr(c):
    """Linda Raschke 3-10-16 — MACD mit ihren Parametern, NICHT der Standard-MACD."""
    return macd_line(c, 3, 10, 16)


# ══════════════════════════════════════════════════════ Filter-Masken (i-1 = bias-frei)
def filter_mask(closes, kind):
    n = len(closes)
    m = [False] * n
    if kind == "none":
        return [True] * n
    if kind == "rsi_gt50":
        v = rsi(closes, 14)
        for i in range(1, n):
            if v[i - 1] is not None:
                m[i] = v[i - 1] > 50
    elif kind == "rsi_lt30":
        v = rsi(closes, 14)
        for i in range(1, n):
            if v[i - 1] is not None:
                m[i] = v[i - 1] < 30
    elif kind == "lbr_bull":
        f, _ = lbr(closes)
        for i in range(1, n):
            if f[i - 1] is not None:
                m[i] = f[i - 1] > 0
    elif kind == "lbr_bear":
        f, _ = lbr(closes)
        for i in range(1, n):
            if f[i - 1] is not None:
                m[i] = f[i - 1] < 0
    elif kind == "bb_below":
        _, _, lo = bollinger(closes, 20, 2.0)
        for i in range(1, n):
            if lo[i - 1] is not None:
                m[i] = closes[i - 1] < lo[i - 1]
    elif kind == "bb_inside":
        _, up, lo = bollinger(closes, 20, 2.0)
        for i in range(1, n):
            if up[i - 1] is not None:
                m[i] = lo[i - 1] <= closes[i - 1] <= up[i - 1]
    return m


FILTERS = ["none", "lbr_bull", "lbr_bear", "rsi_gt50", "rsi_lt30", "bb_below", "bb_inside"]


# ══════════════════════════════════════════════════════ Kalender-Helfer
def _by_month(dates):
    idx = {}
    for i, d in enumerate(dates):
        idx.setdefault(d[:7], []).append(i)
    return idx


def _td(bm, y, m):
    return bm.get("%d-%02d" % (y, m), [])


def _nth(bm, y, m, n):
    d = _td(bm, y, m)
    return d[n - 1] if len(d) >= n else -1


def _last(bm, y, m):
    d = _td(bm, y, m)
    return d[-1] if d else -1


def _nth_last(bm, y, m, n):
    d = _td(bm, y, m)
    return d[-n] if len(d) >= n else -1


def _fwd(dates, s):
    lo, hi, best = 0, len(dates) - 1, -1
    while lo <= hi:
        mid = (lo + hi) // 2
        if dates[mid] >= s:
            best, hi = mid, mid - 1
        else:
            lo = mid + 1
    return best


def _bwd(dates, s):
    lo, hi, best = 0, len(dates) - 1, -1
    while lo <= hi:
        mid = (lo + hi) // 2
        if dates[mid] <= s:
            best, lo = mid, mid + 1
        else:
            hi = mid - 1
    return best


def _pres(y):
    """1=Post-Election, 2=Midterm, 3=Vorwahl, 4=Wahljahr (Anker 2024=Wahljahr)."""
    pos = ((y - 2024) % 4 + 4) % 4
    return {0: 4, 1: 1, 2: 2}.get(pos, 3)


def _election_day(y):
    nov1 = date(y, 11, 1)
    first_mon = 1 + ((0 - nov1.weekday()) % 7)
    return "%d-11-%02d" % (y, first_mon + 1)


def _thanksgiving(y):
    """4. Donnerstag im November."""
    nov1 = date(y, 11, 1)
    first_thu = 1 + ((3 - nov1.weekday()) % 7)
    return "%d-11-%02d" % (y, first_thu + 21)


# ══════════════════════════════════════════════════════ Strategien -> [(entry, exit)]
def S_sell_in_may(dates, closes, bm, years, hol):
    return [(_last(bm, y, 10), _nth(bm, y + 1, 5, 3)) for y in years]


def S_nasdaq_trend(dates, closes, bm, years, hol):
    return [(_last(bm, y, 10), _last(bm, y + 1, 6)) for y in years]


def S_month_end(dates, closes, bm, years, hol):
    out = []
    for y in years:
        for m in range(1, 13):
            ny, nm = (y + 1, 1) if m == 12 else (y, m + 1)
            out.append((_nth_last(bm, y, m, 2), _nth(bm, ny, nm, 4)))
    return out


def S_santa_claus(dates, closes, bm, years, hol):
    out = []
    for y in years:
        ti = _bwd(dates, _thanksgiving(y))
        if ti >= 3:
            out.append((ti - 3, _nth(bm, y + 1, 1, 5)))
    return out


def _cycle(dates, ref, cycle_days, hold_days):
    out = []
    d0 = datetime.strptime(dates[0], "%Y-%m-%d").date()
    d1 = datetime.strptime(dates[-1], "%Y-%m-%d").date()
    cur = ref
    while cur < d0:
        cur += timedelta(days=cycle_days)
    while cur < d1:
        out.append((_fwd(dates, cur.isoformat()),
                    _fwd(dates, (cur + timedelta(days=hold_days)).isoformat())))
        cur += timedelta(days=cycle_days)
    return out


def S_cycle_212w(dates, closes, bm, years, hol):
    return _cycle(dates, date(1938, 5, 16), 1484, 182)


def S_cycle_40w(dates, closes, bm, years, hol):
    return _cycle(dates, date(1967, 4, 21), 280, 140)


def S_midterm(dates, closes, bm, years, hol):
    out = []
    for y in years:
        if _pres(y) != 2:
            continue
        ed = _election_day(y)
        ei, ai = _bwd(dates, ed), _fwd(dates, ed)
        if ei >= 5 and ai >= 0 and ai + 3 < len(dates):
            out.append((ei - 5, ai + 3))
    return out


def S_september_avoid(dates, closes, bm, years, hol):
    return [(_fwd(dates, "%d-09-30" % y), _bwd(dates, "%d-08-31" % (y + 1))) for y in years]


def S_first_five(dates, closes, bm, years, hol):
    out = []
    for y in years:
        j = _td(bm, y, 1)
        if len(j) >= 5 and closes[j[4]] > closes[j[0]]:
            out.append((_nth(bm, y, 2, 1), _last(bm, y, 12)))
    return out


def S_last_five(dates, closes, bm, years, hol):
    out = []
    for y in years:
        j = _td(bm, y, 1)
        if len(j) >= 5 and closes[j[-1]] > closes[j[-5]]:
            out.append((_nth(bm, y, 2, 1), _last(bm, y, 12)))
    return out


def S_jan_barometer(dates, closes, bm, years, hol):
    out = []
    for y in years:
        j = _td(bm, y, 1)
        if len(j) >= 10 and closes[j[-1]] > closes[j[0]]:
            out.append((_nth(bm, y, 2, 1), _last(bm, y, 12)))
    return out


def S_one_day_holiday(dates, closes, bm, years, hol):
    out = []
    for h in hol:
        hi = _fwd(dates, h.isoformat())
        if hi >= 2:
            out.append((hi - 2, hi - 1))
    return out


def S_uhts(dates, closes, bm, years, hol):
    out = []
    for h in hol:
        hi = _fwd(dates, h.isoformat())
        if hi >= 3 and hi + 3 < len(dates):
            out.append((hi - 3, hi + 3))
    return out


def S_post_christmas(dates, closes, bm, years, hol):
    return [(_fwd(dates, "%d-12-26" % y), _last(bm, y, 12)) for y in years]


def S_second_td(dates, closes, bm, years, hol):
    return [(_nth(bm, y, m, 1), _nth(bm, y, m, 2)) for y in years for m in range(1, 13)]


def S_mid_decade(dates, closes, bm, years, hol):
    return [(_fwd(dates, "%d-09-30" % y), _bwd(dates, "%d-03-31" % (y + 2)))
            for y in years if y % 10 == 4]


def S_cycle_20y(dates, closes, bm, years, hol):
    return [(_fwd(dates, "%d-09-30" % y), _bwd(dates, "%d-12-31" % (y + 3)))
            for y in years if y % 10 == 2 and (y // 10) % 2 == 0]


def S_election_7m(dates, closes, bm, years, hol):
    return [(_fwd(dates, "%d-05-31" % y), _last(bm, y, 12)) for y in years if _pres(y) == 4]


def S_monthly_10(dates, closes, bm, years, hol):
    out = []
    for y in years:
        for m in range(1, 13):
            d = _td(bm, y, m)
            if len(d) < 10:
                continue
            # nur TDOMs, die es in diesem Monat wirklich gibt — sonst Index-Ueberlauf
            act = {t for t in (list(range(1, 5)) + list(range(9, 13))
                               + [len(d), len(d) - 1]) if 1 <= t <= len(d)}
            srt = sorted(act)
            bs = prev = srt[0]
            for k in range(1, len(srt)):
                if srt[k] != prev + 1:
                    out.append((d[bs - 1], d[prev - 1]))
                    bs = srt[k]
                prev = srt[k]
            out.append((d[bs - 1], d[prev - 1]))
    return out


def S_downmonth_tom(dates, closes, bm, years, hol):
    """Das bestehende validierte Setup: 21d-Rueckgang vor TDOM 14, dann 13 HT halten."""
    out, STREV, ENTRY, HOLD = [], 21, 14, 13
    for y in years:
        for m in range(1, 13):
            e = _nth(bm, y, m, ENTRY)
            if e < STREV + 1:
                continue
            rev = e - 1 - STREV
            if rev < 0 or closes[rev] <= 0:
                continue
            if closes[e - 1] / closes[rev] >= 1:
                continue
            out.append((e, e + HOLD))
    return out


def S_lbr_nov_mai(dates, closes, bm, years, hol):
    """Ab Oktober rein sobald LBR-Histogramm > 0, ab April raus sobald < 0."""
    f, s = lbr(closes)
    hist = [None if (f[i] is None or s[i] is None) else f[i] - s[i] for i in range(len(closes))]
    out = []
    for y in years:
        win_in = _td(bm, y, 10) + _td(bm, y, 11) + _td(bm, y, 12)
        entry = next((i for i in win_in if hist[i] is not None and hist[i] > 0), -1)
        if entry < 0:
            continue
        win_out = _td(bm, y + 1, 4) + _td(bm, y + 1, 5) + _td(bm, y + 1, 6)
        ex = next((i for i in win_out if hist[i] is not None and hist[i] < 0), -1)
        out.append((entry, ex if ex > 0 else _last(bm, y + 1, 5)))
    return out


STRATEGIES = {
    "sell_in_may": S_sell_in_may, "nasdaq_trend": S_nasdaq_trend, "month_end": S_month_end,
    "santa_claus": S_santa_claus, "cycle_212w": S_cycle_212w, "cycle_40w": S_cycle_40w,
    "midterm_election": S_midterm, "september_avoid": S_september_avoid,
    "first_five_days": S_first_five, "last_five_days": S_last_five,
    "january_barometer": S_jan_barometer, "one_day_holiday": S_one_day_holiday,
    "uhts": S_uhts, "post_christmas": S_post_christmas, "second_trading_day": S_second_td,
    "mid_decade": S_mid_decade, "cycle_20_year": S_cycle_20y,
    "election_year_7m": S_election_7m, "monthly_10": S_monthly_10,
    "downmonth_tom": S_downmonth_tom, "lbr_november_mai": S_lbr_nov_mai,
}


# ══════════════════════════════════════════════════════ Statistik ohne scipy
_G = 0.5772156649015329  # Euler-Mascheroni


def _norm_cdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def _norm_ppf(p):
    """Inverse Standardnormalverteilung (Acklam-Approximation, |Fehler| < 1.15e-9)."""
    if p <= 0 or p >= 1:
        return float("-inf") if p <= 0 else float("inf")
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00]
    pl, ph = 0.02425, 1 - 0.02425
    if p < pl:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    if p > ph:
        q = math.sqrt(-2 * math.log(1 - p))
        return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    q = p - 0.5
    r = q * q
    return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)


def _betacf(a, b, x):
    """Kettenbruch fuer die unvollstaendige Betafunktion (Numerical Recipes)."""
    MAXIT, EPS, FPMIN = 200, 3e-14, 1e-300
    qab, qap, qam = a + b, a + 1, a - 1
    c, d = 1.0, 1 - qab * x / qap
    if abs(d) < FPMIN:
        d = FPMIN
    d = 1 / d
    h = d
    for m in range(1, MAXIT + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1 + aa * d
        if abs(d) < FPMIN:
            d = FPMIN
        c = 1 + aa / c
        if abs(c) < FPMIN:
            c = FPMIN
        d = 1 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1 + aa * d
        if abs(d) < FPMIN:
            d = FPMIN
        c = 1 + aa / c
        if abs(c) < FPMIN:
            c = FPMIN
        d = 1 / d
        de = d * c
        h *= de
        if abs(de - 1) < EPS:
            break
    return h


def _betai(a, b, x):
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    lb = (math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
          + a * math.log(x) + b * math.log(1 - x))
    bt = math.exp(lb)
    if x < (a + 1) / (a + b + 2):
        return bt * _betacf(a, b, x) / a
    return 1 - bt * _betacf(b, a, 1 - x) / b


def t_sf(t, df):
    """P(T > t) fuer Student-t. Einseitig."""
    if df <= 0:
        return 1.0
    p = 0.5 * _betai(df / 2, 0.5, df / (df + t * t))
    return p if t > 0 else 1 - p


def moments(xs):
    n = len(xs)
    if n < 2:
        return 0.0, 0.0, 0.0, 0.0
    mu = sum(xs) / n
    var = sum((x - mu) ** 2 for x in xs) / (n - 1)
    sd = math.sqrt(var) if var > 0 else 0.0
    if sd == 0:
        return mu, 0.0, 0.0, 0.0
    m3 = sum((x - mu) ** 3 for x in xs) / n
    m4 = sum((x - mu) ** 4 for x in xs) / n
    s = sd * math.sqrt((n - 1) / n)
    return mu, sd, m3 / s ** 3, m4 / s ** 4


def deflated_sharpe(sr, n_obs, skew, kurt, n_trials, sr_var):
    """Deflated Sharpe Ratio nach Bailey & Lopez de Prado (2014).

    Korrigiert den beobachteten Sharpe um (a) die Anzahl der Versuche und
    (b) die Nicht-Normalitaet der Renditen. Ergebnis ist die Wahrscheinlichkeit,
    dass der wahre Sharpe > 0 ist, GEGEBEN dass man n_trials Strategien probiert hat.
    """
    if n_obs < 3 or n_trials < 2 or sr_var <= 0:
        return None
    # erwarteter Maximal-Sharpe unter der Nullhypothese bei n_trials Versuchen
    e = math.e
    sr0 = math.sqrt(sr_var) * ((1 - _G) * _norm_ppf(1 - 1.0 / n_trials)
                               + _G * _norm_ppf(1 - 1.0 / (n_trials * e)))
    denom = 1 - skew * sr + (kurt - 1) / 4 * sr * sr
    if denom <= 0:
        return None
    z = (sr - sr0) * math.sqrt(n_obs - 1) / math.sqrt(denom)
    return _norm_cdf(z)


def bh_fdr(pvals, q=0.10):
    """Benjamini-Hochberg. Gibt die Indizes zurueck, die bei FDR q ueberleben."""
    idx = sorted(range(len(pvals)), key=lambda i: pvals[i])
    m = len(pvals)
    keep, kmax = set(), -1
    for rank, i in enumerate(idx, start=1):
        if pvals[i] <= q * rank / m:
            kmax = rank
    if kmax > 0:
        keep = {idx[r - 1] for r in range(1, kmax + 1)}
    return keep


# ══════════════════════════════════════════════════════ Backtest
def run_one(dates, closes, pairs, mask):
    """Trades bilden. Filter wird an entry-1 geprueft (look-ahead-bias-frei)."""
    n = len(closes)
    trades = []
    last_exit = -1
    for e, x in sorted(p for p in pairs if p[0] >= 0):
        if e < 0 or e >= n:
            continue
        if x < 0 or x >= n:
            continue
        if x <= e:
            continue
        if e <= last_exit:          # keine Ueberlappung
            continue
        if e > 0 and not mask[e - 1]:
            continue
        pe, px = closes[e], closes[x]
        if pe <= 0:
            continue
        trades.append((dates[e], dates[x], (px - pe) / pe * 100))
        last_exit = x
    return trades


def stats_of(trades):
    if not trades:
        return None
    rets = [t[2] for t in trades]
    mu, sd, sk, ku = moments(rets)
    wins = sum(1 for r in rets if r > 0)
    gw = sum(r for r in rets if r > 0)
    gl = abs(sum(r for r in rets if r < 0))
    return {
        "n": len(rets), "win_rate": round(wins / len(rets) * 100, 1),
        "avg": round(mu, 4), "sd": round(sd, 4),
        "sharpe": round(mu / sd, 4) if sd > 0 else 0.0,
        "pf": round(gw / gl, 2) if gl > 0 else None,
        "skew": round(sk, 3), "kurt": round(ku, 3),
        "total": round((math.prod(1 + r / 100 for r in rets) - 1) * 100, 1),
    }


def scan_ticker(ticker, use_cache=True):
    rows = load_closes(ticker, use_cache)
    if len(rows) < 500:
        return []
    dates = [r["date"] for r in rows]
    closes = [float(r["close"]) for r in rows]
    bm = _by_month(dates)
    years = sorted({int(d[:4]) for d in dates})
    hol = sorted(h for h in get_nyse_holidays(years[0], years[-1] + 1))

    masks = {f: filter_mask(closes, f) for f in FILTERS}
    out = []
    for sname, sfn in STRATEGIES.items():
        try:
            pairs = sfn(dates, closes, bm, years, hol)
        except Exception as ex:
            print(f"  [WARN] {ticker}/{sname}: {type(ex).__name__}: {ex}", flush=True)
            continue
        for fname in FILTERS:
            tr = run_one(dates, closes, pairs, masks[fname])
            is_tr = [t for t in tr if t[0] < SPLIT_DATE]
            oos_tr = [t for t in tr if t[0] >= SPLIT_DATE]
            rec = {"ticker": ticker, "strategy": sname, "filter": fname,
                   "all": stats_of(tr), "is": stats_of(is_tr), "oos": stats_of(oos_tr)}
            out.append(rec)
    return out


# ══════════════════════════════════════════════════════ Auswertung + main
def evaluate(recs, fdr_q=0.10):
    """Bewertet ALLE Tests gemeinsam — nur so ist die Multiple-Testing-Korrektur ehrlich."""
    # Kandidaten: genug Trades in beiden Perioden
    cand = [r for r in recs
            if r["is"] and r["oos"]
            and r["is"]["n"] >= MIN_TRADES and r["oos"]["n"] >= MIN_TRADES_OOS
            and r["is"]["sd"] > 0 and r["oos"]["sd"] > 0]

    n_trials = len(cand)
    if n_trials < 2:
        return {"n_tests_total": len(recs), "n_candidates": n_trials, "survivors": []}

    # Streuung der Sharpes ueber alle Versuche — Input fuer die Deflation
    all_sr = [r["oos"]["sharpe"] for r in cand]
    mu_sr = sum(all_sr) / len(all_sr)
    sr_var = sum((s - mu_sr) ** 2 for s in all_sr) / (len(all_sr) - 1)

    for r in cand:
        o = r["oos"]
        t = o["sharpe"] * math.sqrt(o["n"])          # t-Statistik fuer mu > 0
        r["p_oos"] = t_sf(t, o["n"] - 1)
        r["dsr"] = deflated_sharpe(o["sharpe"], o["n"], o["skew"], o["kurt"], n_trials, sr_var)
        r["consistent"] = r["is"]["avg"] > 0 and r["oos"]["avg"] > 0

    keep = bh_fdr([r["p_oos"] for r in cand], fdr_q)
    surv = []
    for i, r in enumerate(cand):
        r["fdr_pass"] = i in keep
        if r["fdr_pass"] and r["consistent"] and (r["dsr"] or 0) >= 0.95:
            surv.append(r)
    surv.sort(key=lambda r: -(r["dsr"] or 0))
    return {
        "n_tests_total": len(recs), "n_candidates": n_trials,
        "sr_var": round(sr_var, 5), "fdr_q": fdr_q,
        "n_fdr_pass": len(keep),
        "n_consistent": sum(1 for r in cand if r["consistent"]),
        "survivors": surv, "candidates": cand,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tickers", help="Komma-Liste statt aller US-ETFs")
    ap.add_argument("--no-cache", action="store_true")
    ap.add_argument("--fdr", type=float, default=0.10)
    a = ap.parse_args()

    tickers = ([t.strip().upper() for t in a.tickers.split(",")] if a.tickers
               else [k for k, v in SYMBOLS.items() if v.get("kategorie") == "US-ETF"])

    print(f"Scan: {len(tickers)} Ticker x {len(STRATEGIES)} Strategien x {len(FILTERS)} Varianten "
          f"= {len(tickers)*len(STRATEGIES)*len(FILTERS)} Tests")
    print(f"Walk-Forward-Split: In-Sample < {SPLIT_DATE} <= Out-of-Sample")
    print(f"Mindest-Trades: {MIN_TRADES} (IS) / {MIN_TRADES_OOS} (OOS)\n")

    recs = []
    for i, tk in enumerate(tickers, 1):
        r = scan_ticker(tk, use_cache=not a.no_cache)
        recs += r
        print(f"  [{i:>2}/{len(tickers)}] {tk:<6} {len(r):>4} Tests", flush=True)

    res = evaluate(recs, a.fdr)
    OUT.mkdir(parents=True, exist_ok=True)
    slim = {k: v for k, v in res.items() if k != "candidates"}
    (OUT / "scan_result.json").write_text(
        json.dumps(slim, indent=2, ensure_ascii=False), encoding="utf-8")
    (OUT / "scan_candidates.json").write_text(
        json.dumps(res.get("candidates", []), ensure_ascii=False), encoding="utf-8")

    print("\n" + "=" * 78)
    print(f"  Tests gesamt              {res['n_tests_total']}")
    print(f"  davon auswertbar          {res['n_candidates']}  (genug Trades in IS und OOS)")
    print(f"  IS und OOS beide positiv  {res.get('n_consistent', 0)}")
    print(f"  BH-FDR bestanden (q={a.fdr})  {res.get('n_fdr_pass', 0)}")
    print(f"  UEBERLEBENDE (zusaetzlich DSR >= 0.95)  {len(res['survivors'])}")
    print("=" * 78)
    if res["survivors"]:
        print(f"\n{'Ticker':<7}{'Strategie':<20}{'Filter':<11}"
              f"{'n_OOS':>6}{'WR':>7}{'Ø%':>8}{'SR':>7}{'p':>9}{'DSR':>7}")
        print("-" * 82)
        for r in res["survivors"][:40]:
            o = r["oos"]
            print(f"{r['ticker']:<7}{r['strategy']:<20}{r['filter']:<11}"
                  f"{o['n']:>6}{o['win_rate']:>7.1f}{o['avg']:>8.2f}{o['sharpe']:>7.2f}"
                  f"{r['p_oos']:>9.4f}{(r['dsr'] or 0):>7.3f}")
    else:
        print("\n  Kein einziger Kandidat hat alle drei Huerden ueberstanden.")
        print("  Das ist ein Ergebnis, kein Fehler.")
    print(f"\nGeschrieben: {(OUT / 'scan_result.json').relative_to(_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
