#!/usr/bin/env python3
"""
render_bond_lag_charts.py — Charts zur Anleihen-Lead-Lag-Studie.

    py -3.14 scripts/research/render_bond_lag_charts.py \
        --out blog/posts/images/anleihen-fruehindikator-aktienmarkt

Zwei Bilder, jedes mit genau einer Aussage:

  1_regime   Der Effekt existiert nur im Stress. Das ist das Kernbild: in
             ruhigen Phasen liegt er exakt auf der Basisrate, in unruhigen beim
             Siebenfachen. Wer nur den Mittelwert ueber alle Faelle zeigt,
             verschweigt genau das.
  2_pfad     Der SPY-Verlauf um das Ereignis, VOR und nach. Der Teil vor t=0
             gehoert unbedingt ins Bild: SPY faellt vorher (Median -1,31 %),
             und ohne diese Haelfte laese man eine Vorhersage, wo eine
             Erholung steht.

Die Werte sind hier hart hinterlegt und stammen aus scripts/research/
bond_lead_lag.py und bond_kontrollen.py, Lauf vom 2026-09-21. Sie stehen
zusammen mit ihrer Herkunft im Docstring, damit ein spaeterer Leser sie
nachrechnen kann.
"""
from __future__ import annotations

import argparse
import math
import pathlib
import sys

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["text.parse_math"] = False
import matplotlib.pyplot as plt                                      # noqa: E402
from matplotlib.ticker import FuncFormatter                          # noqa: E402

_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))

BG, FLAECHE = "#000000", "#0a0a0e"
GOLD, DIM, HELL, GITTER = "#e8a820", "#9ca3af", "#e5e7eb", "#1f2430"
BLAU, ROT, GRUEN = "#60a5fa", "#ef4444", "#22c55e"
DPI = 110

# Aus bond_kontrollen.py, Lauf 2026-09-21. SPY zwei Wochen nach einem
# TLT-Kursanstieg ab 4,1 % ueber 10 Handelstage.
BASIS = 0.48
REGIME = [("ruhige Phasen\n(Vola unter Median)", 0.53, 0.935, 25, 68),
          ("unruhige Phasen\n(Vola über Median)", 3.65, 0.000, 25, 80)]
PERIODEN = [("2003-2019", 1.72, 0.019, 34), ("2020-2025", 2.87, 0.008, 16)]


def _p(wert: float) -> str:
    """p-Wert fuer die Anzeige. Unter der Aufloesung des Verfahrens wird nicht
    gerundet, sondern die Grenze genannt: bei 2000 Verschiebungen ist der
    kleinste darstellbare Wert 1/2001, "p = 0,000" waere eine Behauptung ueber
    Genauigkeit, die das Verfahren nicht hergibt."""
    return "p < 0,001" if wert < 0.001 else ("p = %.3f" % wert).replace(".", ",")


def _achse(ax, titel="", untertitel=""):
    ax.set_facecolor(FLAECHE)
    for s in ax.spines.values():
        s.set_color(GITTER)
    ax.tick_params(colors=DIM, labelsize=9)
    ax.grid(True, color=GITTER, linewidth=0.6, alpha=0.8, axis="y")
    ax.set_axisbelow(True)
    if titel:
        ax.set_title(titel, color=HELL, fontsize=13, pad=14, loc="left")
    if untertitel:
        ax.text(0.0, 1.02, untertitel, transform=ax.transAxes, color=DIM,
                fontsize=9, va="bottom")


def _fuss(fig, text):
    fig.text(0.01, 0.012, text, color=DIM, fontsize=7.5, ha="left")
    fig.text(0.99, 0.012, "seasonalpha.ai", color=GOLD, fontsize=7.5, ha="right")


def _speichern(fig, ziel):
    ziel.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(ziel, facecolor=BG, dpi=DPI, bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)
    print("  %s  (%.0f KB)" % (ziel.name, ziel.stat().st_size / 1024))


def chart_regime(ziel: pathlib.Path) -> None:
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(11.4, 5.2),
                                  gridspec_kw={"width_ratios": [1.35, 1]})
    _achse(ax, "Das Signal wirkt nur im Stress",
           "S&P 500 zwei Wochen nach einem starken Anstieg langlaufender Staatsanleihen")

    x = [0, 1]
    werte = [r[1] for r in REGIME]
    farben = [DIM, GOLD]
    ax.bar(x, werte, width=0.5, color=farben)
    ax.axhline(BASIS, color=HELL, linewidth=1.3, linestyle="--", alpha=0.9)
    ax.text(1.42, BASIS + 0.12, "Marktdurchschnitt\nohne Signal: +0,48 %",
            color=HELL, fontsize=9, ha="right", va="bottom")
    for i, (lab, w, p, n, tr) in enumerate(REGIME):
        ax.text(i, w + 0.12, "%+.2f %%" % w, color=farben[i], fontsize=12,
                ha="center", fontweight="bold")
        ax.text(i, -0.42, "n = %d   %s   Treffer %d %%" % (n, _p(p), tr),
                color=DIM, fontsize=8.5, ha="center")
    ax.set_xticks(x)
    ax.set_xticklabels([r[0] for r in REGIME], fontsize=9.5)
    ax.set_ylim(-0.6, 4.3)
    ax.set_yticks([0, 1, 2, 3, 4])
    ax.set_ylabel("S&P 500 nach 2 Wochen", color=DIM, fontsize=9.5)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: "%+.0f %%" % v))

    _achse(ax2, "In beiden Zeiträumen", "dieselbe Messung, vorab geteilt")
    x2 = [0, 1]
    ax2.bar(x2, [p[1] for p in PERIODEN], width=0.5, color=BLAU)
    ax2.axhline(BASIS, color=HELL, linewidth=1.3, linestyle="--", alpha=0.9)
    for i, (lab, w, p, n) in enumerate(PERIODEN):
        ax2.text(i, w + 0.08, "%+.2f %%" % w, color=BLAU, fontsize=11,
                 ha="center", fontweight="bold")
        ax2.text(i, -0.30, "n = %d   %s" % (n, _p(p)), color=DIM,
                 fontsize=8.5, ha="center")
    ax2.set_xticks(x2)
    ax2.set_xticklabels([p[0] for p in PERIODEN], fontsize=9.5)
    ax2.set_ylim(-0.45, 3.4)
    ax2.set_yticks([0, 1, 2, 3])
    ax2.yaxis.set_major_formatter(FuncFormatter(lambda v, _: "%+.0f %%" % v))

    _fuss(fig, "TLT-Kursanstieg ab 4,1 % über 10 Handelstage · 2002-2026 · "
               "p aus 2000 zirkulären Zufallsverschiebungen, zweiseitig")
    _speichern(fig, ziel)


def chart_pfad(ziel: pathlib.Path) -> None:
    """Der Verlauf VOR dem Ereignis gehoert ins Bild.

    Ohne die linke Haelfte liest man eine Vorhersage, wo eine Erholung steht:
    SPY faellt vor dem Ereignis (Median -1,31 %, in 62 % der Faelle negativ).
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "b", str(pathlib.Path(__file__).with_name("btc_lead_lag.py")))
    B = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(B)
    from shared.data import lade_closes

    reihen = {}
    for t in ("TLT", "SPY"):
        d, c = lade_closes(t)
        reihen[t] = dict(zip(d, [float(x) for x in c]))
    tage = sorted(set(reihen["TLT"]) & set(reihen["SPY"]))
    spy = [reihen["SPY"][d] for d in tage]
    kum = B.kumulierte([reihen["TLT"][d] for d in tage], B.L)
    tr, letztes = [], -10 ** 9
    for i in range(B.BASIS + B.L, len(tage)):
        k = kum[i]
        if k is None:
            continue
        if math.exp(k) - 1.0 >= 0.041 and i - letztes >= B.ABSTAND:
            tr.append(i)
            letztes = i
    pf = [p for p in (B.pfad(spy, i) for i in tr) if p]
    m = B.mittelpfad(pf)
    null = B.nullband(spy, tr, len(tage))
    lo = [B.perzentil(sorted(x[j] for x in null), 0.05) for j in range(len(m))]
    hi = [B.perzentil(sorted(x[j] for x in null), 0.95) for j in range(len(m))]

    fig, ax = plt.subplots(figsize=(9.8, 5.4))
    _achse(ax, "Erst fällt der S&P 500 — dann kommt die Erholung",
           "Verlauf um einen starken Anstieg langlaufender Staatsanleihen, n = %d" % len(pf))
    x = list(range(-B.VOR, B.NACH + 1))
    ax.fill_between(x, lo, hi, color=BLAU, alpha=0.15, linewidth=0,
                    label="Zufallsband (5.-95. Perzentil)")
    ax.plot(x, m, color=GOLD, linewidth=2.6, label="S&P 500 im Mittel")
    ax.axvline(0, color=HELL, linewidth=1.0, linestyle=":", alpha=0.7)
    ax.axhline(0, color=GITTER, linewidth=1.0)
    ax.axvspan(-B.VOR, 0, color=ROT, alpha=0.05, linewidth=0)
    ax.text(-B.VOR + 0.4, min(m) - 0.35, "davor: Kursrückgang", color=DIM, fontsize=9)
    ax.text(1.0, max(m) * 0.55, "danach: Erholung", color=DIM, fontsize=9)
    ax.set_xlabel("Handelstage um das Ereignis", color=DIM, fontsize=9.5)
    ax.set_ylabel("kumuliert, normiert auf den Ereignistag", color=DIM, fontsize=9.5)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: "%+.1f %%" % v))
    leg = ax.legend(frameon=False, loc="upper left", fontsize=9.5)
    for t in leg.get_texts():
        t.set_color(HELL)
    _fuss(fig, "TLT-Kursanstieg ab 4,1 % über 10 Handelstage · 2002-2026 · "
               "Tagesschlusskurse")
    _speichern(fig, ziel)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = pathlib.Path(a.out)
    print("Charts nach %s:" % out)
    chart_regime(out / "1_regime.png")
    chart_pfad(out / "2_pfad.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
