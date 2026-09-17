#!/usr/bin/env python3
"""
monthly10_charts.py — Blog-Charts zur Monthly-10-Strategie (DE + EN).

Nutzt exakt die Logik aus monthly10_blogzahlen.py (= Produktivlogik
landing/js/strategy-compute.js::calc_monthly_10), damit Chart und Text
dieselben Zahlen zeigen.

Erzeugt nach blog/posts/images/monthly-10-strategie/:
  monthly10-equity-spy-{de,en}.png     Equity-Kurven, log-Y
  monthly10-bloecke-spy-{de,en}.png    Beitrag je Block + Trefferquote
  monthly10-jahre-spy-{de,en}.png      Jahresvergleich als Balkenpaar

Nutzung: PYTHONUTF8=1 py -3.14 scripts/research/monthly10_charts.py
"""
from __future__ import annotations
import statistics as st
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["text.parse_math"] = False
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
from scripts.research.monthly10_blogzahlen import lade, bloecke, TICKER  # noqa: E402

BG = "#0b0e14"; GOLD = "#e8a820"; BLUE = "#4d9dff"; GREEN = "#22c55e"
RED = "#ff4d5e"; WHITE = "#e8edf4"; MUTED = "#6b7a90"
W, H, DPI = 1200, 680, 100
OUT = _ROOT / "blog" / "posts" / "images" / "monthly-10-strategie"

TXT = {
    "de": {
        "eq_title": "Monthly 10 vs. Buy & Hold — SPY 1994–2025",
        "eq_sub": "Wert aus 10.000 USD, logarithmische Skala · Adjusted Close (Dividenden enthalten)",
        "strat": "Monthly 10", "bh": "Buy & Hold",
        "bl_title": "Woher der Ertrag kommt: Beitrag je Block — SPY 1994–2025",
        "bl_sub": "Kumulierter Beitrag über je 384 Trades, darunter die Trefferquote",
        "blocks": ["Monatsanfang\nTDOM 1–4", "Monatsmitte\nTDOM 9–12", "Monatsende\nletzte 2 Tage"],
        "yr_title": "Jahresrendite: Monthly 10 vs. Buy & Hold — SPY 1994–2025",
        "yr_sub": "Die Strategie glänzt in Baissejahren und fällt in Haussejahren zurück",
        "hit": "Treffer",
        "src": "Quelle: seasonalpha.ai · SPY Adjusted Close",
        "bl_note": "Hinweis: Einstieg zum Schluss des ersten Blocktages — der Monatsend-Block dreht bei einem Tag früherem Einstieg auf +14 %.",
    },
    "en": {
        "eq_title": "Monthly 10 vs. Buy & Hold — SPY 1994–2025",
        "eq_sub": "Value of USD 10,000, log scale · adjusted close (dividends included)",
        "strat": "Monthly 10", "bh": "Buy & Hold",
        "bl_title": "Where the return comes from: contribution per block — SPY 1994–2025",
        "bl_sub": "Cumulative contribution across 384 trades each, hit rate below",
        "blocks": ["Start of month\nTDOM 1–4", "Mid-month\nTDOM 9–12", "End of month\nlast 2 days"],
        "yr_title": "Annual return: Monthly 10 vs. Buy & Hold — SPY 1994–2025",
        "yr_sub": "The strategy shines in bear years and lags in strong bull years",
        "hit": "hit rate",
        "src": "Source: seasonalpha.ai · SPY adjusted close",
        "bl_note": "Note: entry at the close of the first day of each block — entering one day earlier turns the end-of-month block to +14%.",
    },
}


def _fig():
    fig = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI)
    fig.patch.set_facecolor(BG)
    ax = fig.add_axes([0.085, 0.13, 0.80, 0.70])
    ax.set_facecolor(BG)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(colors=MUTED, labelsize=9, length=0)
    return fig, ax


def _head(fig, title, sub, t):
    fig.text(0.085, 0.935, title, color=WHITE, fontsize=17, fontweight="bold", va="top")
    fig.text(0.085, 0.875, sub, color=MUTED, fontsize=10, va="top")
    fig.text(0.085, 0.025, t["src"], color=MUTED, fontsize=8)


def daten():
    rows = lade(TICKER)
    bl = bloecke(rows)
    aktiv = set()
    for a, b, _ in bl:
        aktiv.update(range(a + 1, b + 1))
    ret = [0.0] + [rows[i][1] / rows[i - 1][1] - 1 for i in range(1, len(rows))]
    eq_s, eq_b = [1.0], [1.0]
    for i in range(1, len(rows)):
        eq_s.append(eq_s[-1] * (1 + (ret[i] if i in aktiv else 0.0)))
        eq_b.append(eq_b[-1] * (1 + ret[i]))
    return rows, bl, aktiv, ret, eq_s, eq_b


def chart_equity(rows, eq_s, eq_b, lang):
    t = TXT[lang]
    x = [int(d[:4]) + (int(d[5:7]) - 1) / 12 + (int(d[8:10]) - 1) / 365 for d, _ in rows]
    fig, ax = _fig()
    ax.set_yscale("log")
    ax.grid(True, which="major", color="white", alpha=0.07)
    ax.plot(x, [v * 10000 for v in eq_b], color=BLUE, lw=1.7, label=t["bh"])
    ax.plot(x, [v * 10000 for v in eq_s], color=GOLD, lw=1.9, label=t["strat"])
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}".replace(",", ".")))
    ax.set_yticks([10000, 20000, 50000, 100000, 200000, 500000])
    ax.set_ylim(7000, 400000)
    ax.set_xlim(min(x), max(x))
    leg = ax.legend(loc="upper left", frameon=False, fontsize=11)
    for txt, col in zip(leg.get_texts(), (BLUE, GOLD)):
        txt.set_color(col)
    for val, col, lbl in ((eq_b[-1] * 10000, BLUE, t["bh"]), (eq_s[-1] * 10000, GOLD, t["strat"])):
        ax.text(max(x), val, f"  {val:,.0f}".replace(",", "."), color=col,
                fontsize=10, va="center", fontweight="bold")
    _head(fig, t["eq_title"], t["eq_sub"], t)
    p = OUT / f"monthly10-equity-spy-{lang}.png"
    fig.savefig(p, facecolor=BG); plt.close(fig)
    return p


def chart_bloecke(rows, bl, lang):
    t = TXT[lang]
    typen = ("Monatsanfang (TDOM 1-4)", "Monatsmitte (TDOM 9-12)", "Monatsende (letzte 2)")
    kum, hit, n = [], [], []
    for typ in typen:
        rr = [rows[b][1] / rows[a][1] - 1 for a, b, ty in bl if ty == typ]
        k = 1.0
        for r in rr:
            k *= (1 + r)
        kum.append((k - 1) * 100)
        hit.append(100 * sum(1 for r in rr if r > 0) / len(rr))
        n.append(len(rr))
    fig, ax = _fig()
    ax.grid(True, axis="y", color="white", alpha=0.07)
    ax.axhline(0, color="white", alpha=0.3, lw=1)
    x = np.arange(3)
    ax.bar(x, kum, width=0.55, color=[GREEN if v >= 0 else RED for v in kum])
    ax.set_xticks(x)
    ax.set_xticklabels(t["blocks"], color=WHITE, fontsize=11)
    ax.tick_params(axis="x", labelcolor=WHITE)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:+.0f}%"))
    ax.set_ylim(min(kum) - 70, max(kum) + 70)
    for xi, (v, h) in enumerate(zip(kum, hit)):
        off = 18 if v >= 0 else -34
        ax.text(xi, v + off, f"{v:+.0f}%", color=WHITE, fontsize=15,
                fontweight="bold", ha="center")
        ax.text(xi, v + off + (34 if v >= 0 else -30), f"{h:.0f}% {t['hit']}",
                color=MUTED, fontsize=10, ha="center")
    _head(fig, t["bl_title"], t["bl_sub"], t)
    fig.text(0.085, 0.065, t["bl_note"], color=MUTED, fontsize=8.5)
    p = OUT / f"monthly10-bloecke-spy-{lang}.png"
    fig.savefig(p, facecolor=BG); plt.close(fig)
    return p


def chart_jahre(rows, aktiv, ret, lang):
    t = TXT[lang]
    jahre = sorted({int(d[:4]) for d, _ in rows})
    s_j, b_j = [], []
    for y in jahre:
        idx = [i for i, (d, _) in enumerate(rows) if int(d[:4]) == y and i > 0]
        s = b = 1.0
        for i in idx:
            s *= (1 + (ret[i] if i in aktiv else 0.0))
            b *= (1 + ret[i])
        s_j.append((s - 1) * 100); b_j.append((b - 1) * 100)
    fig, ax = _fig()
    ax.grid(True, axis="y", color="white", alpha=0.07)
    ax.axhline(0, color="white", alpha=0.3, lw=1)
    x = np.arange(len(jahre))
    ax.bar(x - 0.21, b_j, width=0.42, color=BLUE, label=t["bh"])
    ax.bar(x + 0.21, s_j, width=0.42, color=GOLD, label=t["strat"])
    ax.set_xticks(x)
    ax.set_xticklabels([str(y) for y in jahre], rotation=90, fontsize=8)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:+.0f}%"))
    leg = ax.legend(loc="lower left", frameon=False, fontsize=11, ncol=2)
    for txt, col in zip(leg.get_texts(), (BLUE, GOLD)):
        txt.set_color(col)
    _head(fig, t["yr_title"], t["yr_sub"], t)
    p = OUT / f"monthly10-jahre-spy-{lang}.png"
    fig.savefig(p, facecolor=BG); plt.close(fig)
    return p


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    rows, bl, aktiv, ret, eq_s, eq_b = daten()
    print(f"{TICKER} {rows[0][0]}..{rows[-1][0]}  {len(rows)} HT  "
          f"Quote {100*len(aktiv)/(len(rows)-1):.1f}%")
    for lang in ("de", "en"):
        for p in (chart_equity(rows, eq_s, eq_b, lang),
                  chart_bloecke(rows, bl, lang),
                  chart_jahre(rows, aktiv, ret, lang)):
            print("  ok", p.name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
