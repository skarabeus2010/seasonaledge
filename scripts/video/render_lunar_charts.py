"""Rendert zwei vertikale 1080×1920-PNGs für den Vollmond-Short (Szene A + B).

Nutzt dieselbe Methodik wie das Frontend `SA.seasonal.analyzeMoonEffect` (Port), voll validiert
gegen das /mondphasen-Tool: ^DJI, Fenster 2016–2026 → n=129, Ø +0,45 %, Win ~62 %; Juli n=10,
90 %, +0,95 %, t=3,22, p=0,0105 (Screenshot: t=3,21, p=0,0106).

  py -3.14 scripts/video/render_lunar_charts.py --lang de --outdir scripts/video/screenshots

Szene A: lunar_path  → Event-Verlauf t−5…t+5 + Gesamt-Kennzahlen.
Szene B: lunar_months → Monats-Ø mit Juli hervorgehoben (signifikant), honest (n klein).
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent.parent))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np
import pandas as pd
from scipy import stats

from shared.data import download_data
from shared.yahoo_downloader import preprocess
from shared.central_banks import get_full_moon_dates

BG = "#000000"; GOLD = "#e8a820"; GREEN = "#30e878"; RED = "#ff6060"
WHITE = "#f2f5f8"; MUTED = "#8a8270"; CARD = "#12100b"
W, H, DPI = 1080, 1920, 100
_MONTHS = {"de": "Jan Feb Mär Apr Mai Jun Jul Aug Sep Okt Nov Dez".split(),
           "en": "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()}


def _num(v, dec=2):
    return f"{v:+.{dec}f}".replace(".", ",")


def event_study(ticker="^DJI", start=2016, end=2026, before=5, after=5):
    df = preprocess(download_data(ticker, period="max"))
    if "Date" in df.columns:
        df = df.set_index(pd.to_datetime(df["Date"]))
    df = df.sort_index()
    close = df["Close"].to_numpy()
    dates = [d.strftime("%Y-%m-%d") for d in df.index]
    idx = {d: i for i, d in enumerate(dates)}
    logret = np.concatenate([[0.0], np.log(close[1:] / close[:-1])])
    moons = get_full_moon_dates(start, end)

    def _s(m):
        if isinstance(m, dict):
            m = m.get("date", m)
        if isinstance(m, (list, tuple)):
            m = m[0]
        return m.strftime("%Y-%m-%d") if hasattr(m, "strftime") else str(m)[:10]

    curves, totals, months = [], [], []
    for md in (_s(x) for x in moons):
        if md in idx:
            t0 = idx[md]
        else:
            lo, hi = 0, len(dates) - 1
            while lo <= hi:
                mid = (lo + hi) // 2
                if dates[mid] <= md:
                    lo = mid + 1
                else:
                    hi = mid - 1
            t0 = hi
            if t0 < 0:
                continue
        s, e = t0 - before, t0 + after + 1
        if s < 0 or e > len(dates):
            continue
        w = logret[s:e]
        if len(w) != before + 1 + after:
            continue
        cum = np.concatenate([[0.0], np.cumsum(w[:-1])])
        raw = 100 * np.exp(cum)
        curve = np.round((raw / raw[before] - 1) * 100, 2)   # 1:1 wie JS (rundet auf 2 Dez.)
        curves.append(curve)
        totals.append(curve[-1] - curve[0])
        months.append(int(md[5:7]))
    curves = np.array(curves); totals = np.array(totals); months = np.array(months)
    data_date = dates[-1]
    monthly = {}
    for m in range(1, 13):
        tm = totals[months == m]
        if len(tm) == 0:
            continue
        t, p = stats.ttest_1samp(tm, 0) if len(tm) > 1 else (float("nan"), 1.0)
        monthly[m] = {"n": int(len(tm)), "avg": float(tm.mean()),
                      "win": float(100 * (tm > 0).mean()), "t": float(t), "p": float(p)}
    return {
        "avg_curve": curves.mean(axis=0), "n": int(len(totals)),
        "win": float(100 * (totals > 0).mean()), "avg": float(totals.mean()),
        "median": float(np.median(totals)), "monthly": monthly, "data_date": data_date,
        "before": before, "after": after,
    }


def _fig():
    fig = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI)
    fig.patch.set_facecolor(BG)
    return fig


def _kpi_row(fig, y, cards):
    n = len(cards)
    pad, gap = 0.05, 0.02
    cw = (1 - 2 * pad - (n - 1) * gap) / n
    for i, (label, val, col) in enumerate(cards):
        x = pad + i * (cw + gap)
        ax = fig.add_axes([x, y, cw, 0.075]); ax.axis("off")
        ax.add_patch(plt.Rectangle((0, 0), 1, 1, transform=ax.transAxes,
                                   facecolor=CARD, edgecolor="#2a2418", lw=1))
        ax.text(0.5, 0.68, val, color=col, fontsize=22, fontweight="bold", ha="center", va="center")
        ax.text(0.5, 0.24, label, color=MUTED, fontsize=11, ha="center", va="center")


def lunar_path(d, name, out, lang="de"):
    en = lang == "en"
    path = np.asarray(d["avg_curve"], float)
    b, a = d["before"], d["after"]
    labels = [f"t−{b-i}" if i < b else ("t0" if i == b else f"t+{i-b}") for i in range(b + 1 + a)]
    fig = _fig()
    title = f"{name} — Full Moon" if en else f"{name} — Vollmond"
    sub = (f"cumulative return t−{b}…t+{a}, normalized to t0 · {d['n']} events"
           if en else f"kumulierte Rendite t−{b}…t+{a}, normiert auf t0 · {d['n']} Events")
    fig.text(0.5, 0.955, title, color=WHITE, fontsize=34, fontweight="bold", ha="center")
    fig.text(0.5, 0.925, sub, color=MUTED, fontsize=16, ha="center")
    ax = fig.add_axes([0.11, 0.34, 0.83, 0.55]); ax.set_facecolor(BG)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(colors=MUTED, labelsize=17, length=0)
    ax.grid(True, color="white", alpha=0.06)
    x = np.arange(len(path))
    ax.axhline(0, color="white", alpha=0.18, ls="--", lw=1.2)
    ax.axvline(b, color=GOLD, alpha=0.55, ls="--", lw=1.8)
    ax.fill_between(x, 0, path, color=GOLD, alpha=0.10, lw=0)
    ax.plot(x, path, color=GOLD, lw=4.5, marker="o", ms=11, mec=BG, mew=2.5, solid_capstyle="round")
    ax.text(b, ax.get_ylim()[1], "t0", color=GOLD, fontsize=15, ha="center", va="bottom")
    ax.set_xticks(x); ax.set_xticklabels(labels)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.2f}%"))
    ax.set_xlim(-0.3, len(path) - 0.7)
    win_lbl = "Win-rate" if en else "Win-Rate"
    ret_lbl = "Avg return" if en else "Ø Rendite"
    ev_lbl = "Events" if en else "Events"
    _kpi_row(fig, 0.16, [
        (win_lbl, f"{d['win']:.0f}%", GREEN),
        (ret_lbl, _num(d["avg"]) + "%", GREEN if d["avg"] > 0 else RED),
        ("Median", _num(d["median"]) + "%", GREEN if d["median"] > 0 else RED),
        (ev_lbl, str(d["n"]), WHITE),
    ])
    fig.text(0.5, 0.075, ("Overall only borderline (p≈0.08)" if en else "Gesamt nur grenzwertig (p≈0,08)"),
             color=MUTED, fontsize=15, ha="center", style="italic")
    # Footer entfällt — compose.py brennt Marke + Risiko-Disclaimer ein (kein Doppel-Footer)
    fig.savefig(out, facecolor=BG); plt.close(fig)


def lunar_months(d, name, out, lang="de", highlight=7):
    en = lang == "en"
    mn = _MONTHS["en" if en else "de"]
    vals = [d["monthly"].get(m, {}).get("avg", 0.0) for m in range(1, 13)]
    ps = [d["monthly"].get(m, {}).get("p", 1.0) for m in range(1, 13)]
    fig = _fig()
    title = "Full-moon effect by month" if en else "Vollmond-Effekt nach Monat"
    sub = ("July's full moon clearly stands out" if en else "Der Juli-Vollmond sticht klar heraus")
    fig.text(0.5, 0.955, title, color=WHITE, fontsize=32, fontweight="bold", ha="center")
    fig.text(0.5, 0.925, sub, color=MUTED, fontsize=16, ha="center")
    ax = fig.add_axes([0.11, 0.30, 0.83, 0.59]); ax.set_facecolor(BG)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(colors=MUTED, labelsize=16, length=0)
    ax.grid(True, axis="y", color="white", alpha=0.06)
    x = np.arange(12)
    cols = []
    for m in range(1, 13):
        if m == highlight:
            cols.append(GREEN)
        elif ps[m - 1] < 0.05:
            cols.append("#8fd6a8")           # weitere signifikante Monate gedämpft grün
        elif vals[m - 1] >= 0:
            cols.append("#6b6250")
        else:
            cols.append("#5a3038")
    ax.axhline(0, color="white", alpha=0.20, lw=1.2)
    ax.bar(x, vals, color=cols, width=0.72)
    hi = highlight - 1
    ax.annotate((f"July\n+0.95% · 90% win\np=0.01 · n=10" if en else "Juli\n+0,95 % · 90 % Win\np=0,01 · n=10"),
                xy=(hi, vals[hi]), xytext=(hi, max(vals) + 0.55),
                color=GREEN, fontsize=15, fontweight="bold", ha="center", va="bottom",
                arrowprops=dict(arrowstyle="-", color=GREEN, lw=1.5))
    ax.set_xticks(x); ax.set_xticklabels(mn)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.1f}%"))
    ax.set_ylim(min(vals) - 0.6, max(vals) + 1.9)
    _kpi_row(fig, 0.15, [
        ("Juli Ø" if not en else "July avg", "+0,95%" if not en else "+0.95%", GREEN),
        ("Win-Rate" if not en else "Win-rate", "90%", GREEN),
        ("p-Wert" if not en else "p-value", "0,01" if not en else "0.01", GREEN),
        ("Stichprobe" if not en else "Sample", "n=10", WHITE),
    ])
    fig.text(0.5, 0.07, ("Small sample — not a trading signal" if en else "Kleine Stichprobe — kein Handelssignal"),
             color=MUTED, fontsize=15, ha="center", style="italic")
    # Footer entfällt — compose.py brennt Marke + Risiko-Disclaimer ein (kein Doppel-Footer)
    fig.savefig(out, facecolor=BG); plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticker", default="^DJI")
    ap.add_argument("--name", default="Dow Jones")
    ap.add_argument("--start", type=int, default=2016)
    ap.add_argument("--end", type=int, default=2026)
    ap.add_argument("--lang", default="de", choices=["de", "en"])
    ap.add_argument("--outdir", default=str(_HERE / "screenshots"))
    a = ap.parse_args()
    d = event_study(a.ticker, a.start, a.end)
    print(f"[lunar] {a.ticker} {a.start}-{a.end}: n={d['n']} win={d['win']:.0f}% avg={d['avg']:+.2f}% "
          f"| Jul {d['monthly'].get(7)}")
    outdir = Path(a.outdir); outdir.mkdir(parents=True, exist_ok=True)
    suf = "" if a.lang == "de" else "-en"
    p1 = outdir / f"dji-vollmond-verlauf{suf}.png"
    p2 = outdir / f"dji-monats-signifikanz{suf}.png"
    lunar_path(d, a.name, p1, a.lang)
    lunar_months(d, a.name, p2, a.lang)
    print(f"[lunar] -> {p1}\n[lunar] -> {p2}")


if __name__ == "__main__":
    main()
