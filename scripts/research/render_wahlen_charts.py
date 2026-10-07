#!/usr/bin/env python3
"""
render_wahlen_charts.py — Blog-Charts zur Wahlstudie, gezeichnet aus einem Snapshot.

    py -3.14 scripts/research/render_wahlen_charts.py \
        --snapshot landing/data/wahlen_snapshots/midterm-2026-10.json \
        --out blog/posts/images/wahlen-midterm-2026

Liest AUSSCHLIESSLICH den eingefrorenen Snapshot und rechnet mit shared.elections.aggregiere —
derselben Funktion, gegen die der Browser-Kern der Seite /wahlen geprüft wird. Damit zeigt das
Bild dieselben Zahlen wie /wahlen?snapshot=<id>.

Zwei Bilder je Sprache, jedes mit einer Aussage:
  1_midterm   Midterm-Wahlen, S&P 500, Hauptfenster 20/20, auf t0 normiert: Mittel, Median,
              Streuband der mittleren Hälfte und die Vergleichslinie „Jahre ohne Wahl".
  2_live      Dieselben Wahlen ab 40 Handelstagen vorher auf den Fensterbeginn normiert, dazu der
              bisherige Verlauf vor der Midterm 2026 (Stand des Snapshots).
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["text.parse_math"] = False
import matplotlib.pyplot as plt                                      # noqa: E402
from matplotlib.ticker import FuncFormatter                          # noqa: E402

_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))
from shared import elections as el                                    # noqa: E402

BG, FLAECHE = "#000000", "#0a0a0e"
GOLD, DIM, HELL, GITTER, GRAU = "#e8a820", "#9ca3af", "#e5e7eb", "#1f2430", "#9ca3af"
LIVE = "#f2d9a0"
DPI = 110

TEXTE = {
    "de": {
        "t1": "Midterm-Wahlen: S&P 500 vor und nach dem Wahltag",
        "u1": "{n} Midterms 1898–2022 · Referenzschluss t0 = 0 % · Hauptfenster 20 Handelstage vor/nach",
        "t2": "Midterm 2026 im Vergleich: der bisherige Verlauf",
        "u2": "{n} Midterms 1898–2022, normiert auf 40 Handelstage vor der Wahl · 2026: Stand {stand}",
        "band": "mittlere Hälfte der Wahlen (25.–75. Perzentil)", "mittel": "Mittel", "median": "Median",
        "ref": "dieselben Wochen in Jahren ohne Wahl (n={n})", "live": "2026 bis {stand}",
        "x": "Handelstage relativ zum Referenzschluss t0", "y1": "Veränderung gegenüber t0", "y2": "Veränderung seit Fensterbeginn",
        "t0": "Referenzschluss t0", "wahl": "Midterm 03.11.2026",
        "quelle": "Quelle: SeasonAlpha (seasonalpha.ai/wahlen), eingefrorener Datenstand {id}. Historische Auswertung, kein Signal.",
        "dez": ",",
    },
    "en": {
        "t1": "Midterm elections: S&P 500 before and after election day",
        "u1": "{n} midterms 1898–2022 · reference close t0 = 0% · main window 20 trading days before/after",
        "t2": "The 2026 midterm in comparison: the path so far",
        "u2": "{n} midterms 1898–2022, normalised to 40 trading days before the election · 2026: as of {stand}",
        "band": "middle half of elections (25th–75th percentile)", "mittel": "Mean", "median": "Median",
        "ref": "same weeks in years without an election (n={n})", "live": "2026 up to {stand}",
        "x": "Trading days relative to the reference close t0", "y1": "Change from t0", "y2": "Change since start of window",
        "t0": "Reference close t0", "wahl": "Midterm 3 Nov 2026",
        "quelle": "Source: SeasonAlpha (seasonalpha.ai/en/elections), frozen data snapshot {id}. Historical analysis, not a signal.",
        "dez": ".",
    },
}


def _datum(iso: str, sprache: str) -> str:
    j, m, t = iso.split("-")
    return f"{t}.{m}.{j}" if sprache == "de" else f"{int(t)} {['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][int(m) - 1]} {j}"


def _achse(ax, sprache: str):
    ax.set_facecolor(FLAECHE)
    for s in ax.spines.values():
        s.set_color(GITTER)
    ax.tick_params(colors=DIM, labelsize=9)
    ax.grid(True, color=GITTER, linewidth=0.6, alpha=0.8)
    ax.set_axisbelow(True)
    dez = TEXTE[sprache]["dez"]
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: (f"{v:+.1f} %" if sprache == "de" else f"{v:+.1f}%").replace(".", dez)))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{int(v):+d}" if v else "0"))


def _figur(titel: str, untertitel: str):
    fig, ax = plt.subplots(figsize=(10, 5.6), dpi=DPI)
    fig.patch.set_facecolor(BG)
    fig.text(0.06, 0.95, titel, color=HELL, fontsize=14, weight="bold")
    fig.text(0.06, 0.905, untertitel, color=DIM, fontsize=9.5)
    fig.subplots_adjust(left=0.08, right=0.97, top=0.85, bottom=0.2)
    return fig, ax


def bild_1(st: dict, sprache: str, ziel: pathlib.Path) -> dict:
    T = TEXTE[sprache]
    a = st["ansicht"]
    r = el.aggregiere(st, a["reihe"], a["typ"], a["x"], a["y"], a["basis"])
    k, kv = r["kennzahlen"], r["kurven"]
    off = list(range(-a["x"], a["y"] + 1))
    m = lambda xs: [None if v is None else v - 100 for v in xs]      # noqa: E731
    fig, ax = _figur(T["t1"], T["u1"].format(n=k["n"]))
    _achse(ax, sprache)
    ax.fill_between(off, m(kv["p25"]), m(kv["p75"]), color=GOLD, alpha=0.16, linewidth=0, label=T["band"])
    ax.plot(off, m(kv["mittel"]), color=GOLD, linewidth=2.6, label=T["mittel"])
    ax.plot(off, m(kv["median"]), color=GOLD, linewidth=1.6, linestyle=(0, (5, 3)), label=T["median"])
    ax.plot(off, m(kv["referenz"]), color=GRAU, linewidth=1.8, linestyle=(0, (3, 3)), label=T["ref"].format(n=k["n_tripel"]))
    ax.axhline(0, color="#ffffff", alpha=0.25, linewidth=0.8)
    ax.axvline(0, color=GOLD, linewidth=1)
    ax.text(0.4, ax.get_ylim()[1], T["t0"], color=GOLD, fontsize=9, va="top")
    ax.set_xlabel(T["x"], color=DIM, fontsize=9)
    ax.set_ylabel(T["y1"], color=DIM, fontsize=9)
    leg = ax.legend(loc="upper left", fontsize=8.5, frameon=False)
    for t in leg.get_texts():
        t.set_color(HELL)
    fig.text(0.06, 0.04, T["quelle"].format(id=st["snapshot_id"]), color=DIM, fontsize=8)
    fig.savefig(ziel, facecolor=BG)
    plt.close(fig)
    return k


def bild_2(st: dict, sprache: str, ziel: pathlib.Path) -> dict:
    T = TEXTE[sprache]
    a = st["weitere_ansichten"]["live"]["ansicht"]
    r = el.aggregiere(st, a["reihe"], a["typ"], a["x"], a["y"], a["basis"])
    k, kv, lv = r["kennzahlen"], r["kurven"], r["live"]
    off = list(range(-a["x"], a["y"] + 1))
    m = lambda xs: [None if v is None else v - 100 for v in xs]      # noqa: E731
    stand = _datum(lv["letzter_kurs"], sprache)
    fig, ax = _figur(T["t2"], T["u2"].format(n=k["n"], stand=stand))
    _achse(ax, sprache)
    ax.fill_between(off, m(kv["p25"]), m(kv["p75"]), color=GOLD, alpha=0.16, linewidth=0, label=T["band"])
    ax.plot(off, m(kv["mittel"]), color=GOLD, linewidth=2.4, label=T["mittel"])
    ax.plot(off, m(kv["referenz"]), color=GRAU, linewidth=1.6, linestyle=(0, (3, 3)), label=T["ref"].format(n=k["n_tripel"]))
    live = m(lv["kurve"])
    punkte = [(o, v) for o, v in zip(off, live) if v is not None]
    ax.plot([p[0] for p in punkte], [p[1] for p in punkte], color=LIVE, linewidth=2.6, label=T["live"].format(stand=stand))
    ax.scatter([punkte[-1][0]], [punkte[-1][1]], color=LIVE, s=28, zorder=5)
    ax.axhline(0, color="#ffffff", alpha=0.25, linewidth=0.8)
    ax.axvline(0, color=GOLD, linewidth=1)
    ax.text(0.4, ax.get_ylim()[1], T["wahl"], color=GOLD, fontsize=9, va="top")
    ax.set_xlabel(T["x"], color=DIM, fontsize=9)
    ax.set_ylabel(T["y2"], color=DIM, fontsize=9)
    leg = ax.legend(loc="upper left", fontsize=8.5, frameon=False)
    for t in leg.get_texts():
        t.set_color(HELL)
    fig.text(0.06, 0.04, T["quelle"].format(id=st["snapshot_id"]), color=DIM, fontsize=8)
    fig.savefig(ziel, facecolor=BG)
    plt.close(fig)
    return {"live_letzter_offset": punkte[-1][0], "live_letzter_wert": punkte[-1][1],
            "mittel_am_selben_offset": m(kv["mittel"])[off.index(punkte[-1][0])]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    st = json.loads(pathlib.Path(a.snapshot).read_text(encoding="utf-8"))
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for sprache in ("de", "en"):
        k1 = bild_1(st, sprache, out / f"1_midterm_{sprache}.png")
        k2 = bild_2(st, sprache, out / f"2_live_{sprache}.png")
    print(json.dumps({"bild1": k1, "bild2": k2}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
