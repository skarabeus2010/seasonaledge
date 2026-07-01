"""Rendert Landscape-PNGs für Blog-Posts (16:9) — hier: Feiertags-Effekt + Signifikanz-Gauge.

Nutzt dieselben Echtdaten/Methodik wie der Video-Renderer (_load_holiday). Ergebnis-PNGs landen in
blog/posts/images/<slug>/ und werden im Markdown per ![]() eingebunden.

  py -3.14 scripts/video/render_blog_charts.py --ticker QQQ --holiday july4 --slug independence-day-qqq
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
from matplotlib.patches import Wedge
from matplotlib.ticker import FuncFormatter
import numpy as np

from scripts.video.render_vertical_chart import _load_holiday, _disp, _HOLIDAYS  # noqa: E402

BG = "#0b0f16"; ACCENT = "#00d4aa"; WARM = "#e8a425"; GREEN = "#22c55e"; RED = "#ff5b6e"
WHITE = "#f2f5f8"; MUTED = "#5a6e85"
W, H, DPI = 1280, 720, 100


def _fig():
    fig = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI)
    fig.patch.set_facecolor(BG)
    return fig


def _pstr(p):
    return f"{p:.4f}".replace(".", ",")


def holiday_path(data, name, hol_name, out):
    path = np.asarray(data["path"], float)
    labels = ["t−3", "t−2", "t−1", "t0", "t+1", "t+2", "t+3"]
    fig = _fig()
    fig.text(0.5, 0.94, f"{name} — {hol_name}: Verlauf um den Feiertag", color=WHITE,
             fontsize=20, fontweight="bold", ha="center")
    fig.text(0.5, 0.885, f"kumulierte Rendite, normiert (t−3 = 0) · {data['n']} Jahre",
             color=MUTED, fontsize=13, ha="center")
    ax = fig.add_axes([0.09, 0.14, 0.87, 0.68])
    ax.set_facecolor(BG)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(colors=MUTED, labelsize=12, length=0)
    ax.grid(True, color="white", alpha=0.05)
    x = np.arange(7)
    ax.axhline(0, color="white", alpha=0.18, ls="--", lw=1)
    ax.axvline(3, color=WARM, alpha=0.5, ls="--", lw=1.4)
    ax.fill_between(x, 0, path, color=ACCENT, alpha=0.10, lw=0)
    ax.plot(x, path, color=ACCENT, lw=3.5, marker="o", ms=8, mec=BG, mew=2, solid_capstyle="round")
    ax.text(3, path.max() * 1.02 + 0.05, "Feiertag", color=WARM, fontsize=12, ha="center")
    ax.set_xticks(x); ax.set_xticklabels(labels)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.1f}%"))
    ax.set_xlim(-0.2, 6.2)
    fig.text(0.99, 0.02, f"seasonalpha.ai · Daten: {data['data_date']}", color=MUTED,
             fontsize=9, ha="right")
    fig.savefig(out, facecolor=BG); plt.close(fig)


def significance_gauge(data, name, hol_name, out):
    sig = data["significant"]
    col = GREEN if sig else RED
    rel = data["relevance"]
    fig = _fig()
    fig.text(0.5, 0.93, f"Signifikanz-Test — {name} · {hol_name}", color=WHITE,
             fontsize=20, fontweight="bold", ha="center")
    fig.text(0.5, 0.875, "Ist die Fenster-Rendite statistisch von Null verschieden?",
             color=MUTED, fontsize=13, ha="center")
    ax = fig.add_axes([0.30, 0.20, 0.40, 0.55]); ax.set_axis_off()
    ax.set_xlim(-1.2, 1.2); ax.set_ylim(-0.25, 1.2); ax.set_aspect("equal")
    # Halbkreis-Gauge: grau Hintergrund + farbiger Fortschritt (0..1 -> 180°..0°)
    ax.add_patch(Wedge((0, 0), 1.0, 0, 180, width=0.32, facecolor="#1c2430"))
    ang = 180 * (1 - max(0.0, min(1.0, rel)))
    ax.add_patch(Wedge((0, 0), 1.0, ang, 180, width=0.32, facecolor=col))
    ax.text(0, 0.28, f"{rel:.2f}", color=WHITE, fontsize=40, fontweight="bold", ha="center", va="center")
    ax.text(0, -0.08, "Signifikant" if sig else "Zufall wahrscheinlich", color=col,
            fontsize=17, fontweight="bold", ha="center")
    # Stats-Zeile (DE-Komma)
    def _c(x, dec=2):
        return f"{x:.{dec}f}".replace(".", ",")
    stats = (f"t = {_c(data['t'])}      p = {_pstr(data['p'])}      Ø +{_c(data['avg'])} %"
             f"      Win {data['win']:.0f} %      n = {data['n']}")
    fig.text(0.5, 0.12, stats, color=WHITE, fontsize=15, ha="center")
    fig.text(0.5, 0.05, "Relevance = 50%·(1−p) + 30%·Win-Rate + 20%·Effektstärke (Cohen’s d)",
             color=MUTED, fontsize=10, ha="center")
    fig.savefig(out, facecolor=BG); plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticker", required=True)
    ap.add_argument("--holiday", default="july4")
    ap.add_argument("--years", type=int, default=20)
    ap.add_argument("--slug", required=True)
    a = ap.parse_args()
    h = _HOLIDAYS.get(a.holiday, (7, 4, "Independence Day"))
    data = _load_holiday(a.ticker, a.years, h[0], h[1])
    if not data:
        sys.exit("keine Daten")
    out_dir = _HERE.parent.parent / "blog" / "posts" / "images" / a.slug
    out_dir.mkdir(parents=True, exist_ok=True)
    holiday_path(data, _disp(a.ticker), h[2], out_dir / "holiday-verlauf.png")
    significance_gauge(data, _disp(a.ticker), h[2], out_dir / "signifikanz.png")
    print(f"[blog-charts] OK -> {out_dir}/holiday-verlauf.png + signifikanz.png")
    print(f"[blog-charts] Zahlen: Ø +{data['avg']:.2f}% Win {data['win']:.0f}% n={data['n']} "
          f"t={data['t']:.2f} p={data['p']:.4f} d={data['cohen']:.2f} rel={data['relevance']:.2f}")


if __name__ == "__main__":
    main()
