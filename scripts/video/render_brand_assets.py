"""Rendert Kanal-Branding (Avatar 800x800 + Banner 2048x1152) im SeasonAlpha-Look.

Quelle der Marke: landing/assets/images/ (SA-Monogramm Gold/Schwarz, SeasonAlpha-Wortmarke).
YouTube: Avatar 800x800, Banner 2048x1152 (sichtbarer "Safe-Bereich" = zentrale 1235x338).

  py -3.14 scripts/video/render_brand_assets.py
Output: scripts/video/out/avatar_800.png, scripts/video/out/banner_2048x1152.png
"""
from __future__ import annotations
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

BG = "#0a0d12"
GOLD = "#e8a425"
WHITE = "#f2f5f8"
TEAL = "#00d4aa"
MUTED = "#5a6e85"

OUT = Path(__file__).resolve().parent / "out"
OUT.mkdir(parents=True, exist_ok=True)


def avatar():
    """800x800: SA-Monogramm, Gold auf Schwarz, Gold-Rahmen (wie apple-touch-icon)."""
    fig = plt.figure(figsize=(8, 8), dpi=100)
    fig.patch.set_facecolor(BG)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_axis_off()
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    # Gold-Rahmen
    ax.add_patch(Rectangle((0.04, 0.04), 0.92, 0.92, fill=False,
                           edgecolor=GOLD, linewidth=14))
    ax.text(0.5, 0.47, "SA", color=GOLD, fontsize=300, fontweight="bold",
            ha="center", va="center")
    p = OUT / "avatar_800.png"
    fig.savefig(p, facecolor=BG); plt.close(fig)
    return p


def banner():
    """2048x1152: Wortmarke + Tagline + URL, alles im zentralen Safe-Bereich."""
    fig = plt.figure(figsize=(20.48, 11.52), dpi=100)
    fig.patch.set_facecolor(BG)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_axis_off()
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)

    # dezentes Raster (wie og-image)
    for gx in [i / 16 for i in range(1, 16)]:
        ax.axvline(gx, color="white", alpha=0.025, lw=1)
    for gy in [i / 9 for i in range(1, 9)]:
        ax.axhline(gy, color="white", alpha=0.025, lw=1)

    # Safe-Bereich = zentrale 1235x338 -> y etwa 0.355..0.645. Inhalt mittig.
    # Wortmarke "SeasonAlpha" (Season weiss + Alpha gold), an x=0.5 aneinander.
    ax.text(0.5, 0.585, "Season", color=WHITE, fontsize=92, fontweight="bold",
            ha="right", va="center")
    ax.text(0.5, 0.585, "Alpha", color=GOLD, fontsize=92, fontweight="bold",
            ha="left", va="center")
    ax.text(0.5, 0.455, "Saisonale Börsenanalyse — Daten statt Bauchgefühl",
            color=MUTED, fontsize=30, ha="center", va="center")
    ax.text(0.5, 0.385, "seasonalpha.ai", color=TEAL, fontsize=30, fontweight="bold",
            ha="right", va="center")
    ax.text(0.5, 0.385, "   ·   Neue Shorts wöchentlich", color=MUTED, fontsize=26,
            ha="left", va="center")

    p = OUT / "banner_2048x1152.png"
    fig.savefig(p, facecolor=BG); plt.close(fig)
    return p


if __name__ == "__main__":
    print("[brand] Avatar ->", avatar())
    print("[brand] Banner ->", banner())
