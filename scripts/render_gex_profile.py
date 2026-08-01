"""
scripts/render_gex_profile.py — "Exposure By Strike / By Term" (Gamma/Vanna/Charm)
=======================================================================================
Zeichnet aus einem gex_<T>.json (mit --profile erzeugt) ein Balkendiagramm der Netto-Dealer-
Exposure: grün = positiv (vola-reduzierend), rot = negativ (vola-forcierend), Spot-Linie.

  py -3.14 scripts/compute_gamma_exposure.py --ticker "^SPX" --profile --max-days 45
  py -3.14 scripts/render_gex_profile.py --json landing/data/gex_^SPX.json --greek gamma --dim strike
  py -3.14 scripts/render_gex_profile.py --json landing/data/gex_^SPX.json --greek vanna --dim term
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["text.parse_math"] = False   # '$' in Labels nicht als LaTeX-Mathe deuten
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np

BG = "#0b0e14"; GREEN = "#22c55e"; RED = "#ff4d5e"; WHITE = "#e8edf4"; MUTED = "#6b7a90"
W, H, DPI = 1200, 680, 100
_GREEK = {"gamma": ("Gamma", "gamma_usd_mn"), "vanna": ("Vanna", "vanna_usd_mn"),
          "charm": ("Charm", "charm_usd_mn")}


def _fmt_m(v, _):
    if abs(v) >= 1000:
        return f"${v/1000:+.1f}B".replace("+", "")
    return f"${v:+.0f}M".replace("+0M", "$0M").replace("+", "")


def render(o: dict, greek: str, dim: str, out: Path, window: float = 0.08):
    label, key = _GREEK[greek]
    prof = (o.get("profile") or {}).get("by_strike" if dim == "strike" else "by_term", [])
    if not prof:
        raise SystemExit(f"[profile] kein Profil '{dim}' in {out.name} — mit --profile rechnen.")
    spot = o.get("spot")

    if dim == "strike":
        rows = [r for r in prof if abs(r["strike"] - spot) <= spot * window] or prof
        x = np.arange(len(rows))
        xlabels = [f"{r['strike']:.0f}" for r in rows]
        vals = np.array([r[key] for r in rows], float)
        strikes = [r["strike"] for r in rows]
        title_dim = "By Strike"
    else:
        rows = prof
        x = np.arange(len(rows))
        xlabels = [r["exp"][5:] for r in rows]
        vals = np.array([r[key] for r in rows], float)
        strikes = None
        title_dim = "By Term"

    fig = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI); fig.patch.set_facecolor(BG)
    ax = fig.add_axes([0.10, 0.16, 0.86, 0.72]); ax.set_facecolor(BG)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(colors=MUTED, labelsize=9, length=0)
    ax.grid(True, axis="y", color="white", alpha=0.06)
    ax.axhline(0, color="white", alpha=0.25, lw=1)
    ax.bar(x, vals, color=[GREEN if v >= 0 else RED for v in vals], width=0.8)

    if dim == "strike" and spot is not None and strikes:
        xi = float(np.interp(spot, strikes, x))          # Spot-Position auf der Kategorie-Achse
        ax.axvline(xi, color="white", alpha=0.85, lw=1.6)
        ax.text(xi, ax.get_ylim()[1], f"  Spot {spot:.0f}", color=WHITE, fontsize=10, va="top")
        cw, pw = o.get("call_wall"), o.get("put_wall")
        for wall, col, tag in ((cw, GREEN, "Call-Wall"), (pw, RED, "Put-Wall")):
            if wall and min(strikes) <= wall <= max(strikes):
                wi = float(np.interp(wall, strikes, x))
                ax.axvline(wi, color=col, alpha=0.5, ls="--", lw=1.2)
                ax.text(wi, ax.get_ylim()[0], f"{tag} {wall:.0f}", color=col, fontsize=8,
                        va="bottom", ha="center", rotation=90)

    step = max(1, len(x) // 22)
    ax.set_xticks(x[::step]); ax.set_xticklabels(xlabels[::step], rotation=90)
    ax.yaxis.set_major_formatter(FuncFormatter(_fmt_m))
    fig.text(0.10, 0.945, f"{o.get('ticker','?')}  ·  {label} Exposure  ·  {title_dim}",
             color=WHITE, fontsize=17, fontweight="bold")
    fig.text(0.10, 0.905, "Notional Hedging Requirement — grün = vola-reduzierend · rot = vola-forcierend",
             color=MUTED, fontsize=10)
    fig.text(0.96, 0.905, f"Daten: {str(o.get('generated_at',''))[:10]}", color=MUTED, fontsize=9, ha="right")
    fig.text(0.96, 0.02, "seasonalpha.ai · naive Dealer-Heuristik, EOD, kein Handelssignal",
             color=MUTED, fontsize=8, ha="right")
    fig.savefig(out, facecolor=BG); plt.close(fig)
    print(f"[profile] -> {out}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", required=True)
    ap.add_argument("--greek", default="gamma", choices=["gamma", "vanna", "charm"])
    ap.add_argument("--dim", default="strike", choices=["strike", "term"])
    ap.add_argument("--out")
    a = ap.parse_args()
    o = json.load(open(a.json, encoding="utf-8"))
    out = Path(a.out) if a.out else Path(a.json).with_name(
        f"gexprofile_{o.get('ticker','x').replace('^','')}_{a.greek}_{a.dim}.png")
    render(o, a.greek, a.dim, out)


if __name__ == "__main__":
    main()
