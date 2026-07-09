"""Rendert einen vertikalen 1080×1920-Chart für den BTC-Midterm-Zyklus-Short.

Reproduziert die /ki-saisonalitaet-Projektion: Seasonal Avg (11J) vs. Midterm-Jahre (3J: 2014/2018/2022)
vs. laufendes Jahr — normiert (Start=100). Validiert gegen das Tool: Seasonal ~280, Midterm ~44.

  py -3.14 scripts/video/render_cycle_chart.py --ticker BTC-USD --outdir scripts/video/screenshots
"""
from __future__ import annotations
import argparse
import sys
from datetime import date
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent.parent))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from shared.data import download_data
from shared.yahoo_downloader import preprocess
from shared.calculations import build_year_data, calculate_seasonal_average

BG = "#000000"; BLUE = "#4a9dff"; RED = "#ff5b6e"; GOLD = "#e8a820"
GREEN = "#30e878"; WHITE = "#f2f5f8"; MUTED = "#8a8270"; CARD = "#12100b"
W, H, DPI = 1080, 1920, 100
_MONTHS_DE = "Jan Feb Mär Apr Mai Jun Jul Aug Sep Okt Nov Dez".split()
_MONTH_START = [1, 32, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335]


def _num(v, dec=0):
    return f"{v:+.{dec}f}".replace(".", ",")


def compute(ticker="BTC-USD", n_years=12):
    df = preprocess(download_data(ticker))
    data_date = str(df["Date"].iloc[-1])[:10] if "Date" in df.columns else str(df.index[-1])[:10]
    cy = date.today().year
    years = sorted(int(y) for y in df["year"].unique())
    full = [y for y in years if cy - n_years <= y < cy]
    yd = build_year_data(df, full)
    avg, _ = calculate_seasonal_average(yd)
    avg = np.asarray(avg, float)
    mid_years = [y for y in years if y < cy and ((y - 2024) % 4 + 4) % 4 == 2]
    mid_paths = [np.asarray(build_year_data(df, [y])[y]["full_365"], float) for y in mid_years]
    mid = np.mean(mid_paths, axis=0)
    cur = None; cur_last = 0
    if cy in years:
        cp = np.asarray(build_year_data(df, [cy])[cy]["full_365"], float)
        # full_365 wird forward-gefüllt → echten letzten Handelstag aus 'day_of_year' nehmen
        cur_rows = df[df["year"] == cy]
        last_doy = (int(cur_rows["day_of_year"].iloc[-1]) if len(cur_rows)
                    else int(np.nonzero(cp > 0)[0].max()) + 1)
        cur_last = min(last_doy, 365) - 1
        cur = cp.copy(); cur[cur_last + 1:] = np.nan
    return {"avg": avg, "mid": mid, "mid_years": mid_years, "cur": cur, "cur_last": cur_last,
            "n_full": len(yd), "data_date": data_date, "cy": cy}


def draw(d, name, out):
    fig = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI); fig.patch.set_facecolor(BG)
    fig.text(0.5, 0.955, f"{name} — Midterm-Jahr", color=WHITE, fontsize=34,
             fontweight="bold", ha="center")
    fig.text(0.5, 0.925, f"Ø-Jahr vs. Midterm-Zyklus · normiert (Start=100) · {d['n_full']} Jahre",
             color=MUTED, fontsize=16, ha="center")
    ax = fig.add_axes([0.12, 0.34, 0.82, 0.53]); ax.set_facecolor(BG)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(colors=MUTED, labelsize=15, length=0)
    ax.grid(True, color="white", alpha=0.06)
    x = np.arange(1, 366)
    ax.axhline(100, color="white", alpha=0.18, ls="--", lw=1)
    ax.plot(x, d["avg"], color=BLUE, lw=4, label=f"Ø {d['n_full']} Jahre")
    ax.plot(x, d["mid"], color=RED, lw=3.5, ls=(0, (5, 3)),
            label=f"Midterm ({len(d['mid_years'])} J.)")
    if d["cur"] is not None:
        ax.plot(x, d["cur"], color=GOLD, lw=4, label=str(d["cy"]))
        ax.axvline(d["cur_last"] + 1, color=GOLD, alpha=0.4, ls="--", lw=1.4)
        ax.text(d["cur_last"] + 1, ax.get_ylim()[1], "Heute", color=GOLD, fontsize=13,
                ha="center", va="bottom")
    ax.set_xticks(_MONTH_START); ax.set_xticklabels(_MONTHS_DE)
    ax.set_xlim(1, 365)
    ax.legend(loc="upper left", facecolor=CARD, edgecolor="#2a2418", labelcolor=WHITE,
              fontsize=15, framealpha=0.9)
    # KPI-Karten
    avg_ret = d["avg"][-1] - 100
    mid_ret = d["mid"][-1] - 100
    cards = [("Ø-Jahr", _num(avg_ret) + "%", GREEN if avg_ret > 0 else RED),
             ("Midterm Ø", _num(mid_ret) + "%", GREEN if mid_ret > 0 else RED),
             ("Midterm-Jahre", str(len(d["mid_years"])), WHITE),
             (str(d["cy"]), _num(d["cur"][d["cur_last"]] - 100) + "%" if d["cur"] is not None else "—",
              GOLD)]
    n = len(cards); pad, gap = 0.05, 0.02
    cw = (1 - 2 * pad - (n - 1) * gap) / n
    for i, (lab, val, col) in enumerate(cards):
        xx = pad + i * (cw + gap)
        cax = fig.add_axes([xx, 0.17, cw, 0.075]); cax.axis("off")
        cax.add_patch(plt.Rectangle((0, 0), 1, 1, transform=cax.transAxes,
                                    facecolor=CARD, edgecolor="#2a2418", lw=1))
        cax.text(0.5, 0.68, val, color=col, fontsize=21, fontweight="bold", ha="center", va="center")
        cax.text(0.5, 0.24, lab, color=MUTED, fontsize=11, ha="center", va="center")
    fig.text(0.5, 0.085, "nur 3 Midterm-Jahre · wohl der Halving-Zyklus · kein Handelssignal",
             color=MUTED, fontsize=14, ha="center", style="italic")
    fig.text(0.97, 0.885, f"Daten: {d['data_date']}", color=MUTED, fontsize=11, ha="right", va="top")
    fig.savefig(out, facecolor=BG); plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticker", default="BTC-USD")
    ap.add_argument("--name", default="Bitcoin")
    ap.add_argument("--outdir", default=str(_HERE / "screenshots"))
    a = ap.parse_args()
    d = compute(a.ticker)
    print(f"[cycle] {a.ticker}: Ø-Jahr {d['avg'][-1]:.0f} · Midterm {d['mid'][-1]:.0f} "
          f"(Jahre {d['mid_years']}) · {d['cy']} @day{d['cur_last']+1}="
          f"{d['cur'][d['cur_last']]:.0f}" if d['cur'] is not None else "")
    outdir = Path(a.outdir); outdir.mkdir(parents=True, exist_ok=True)
    out = outdir / "btc-midterm-zyklus-native.png"
    draw(d, a.name, out)
    print(f"[cycle] -> {out}")


if __name__ == "__main__":
    main()
