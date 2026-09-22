#!/usr/bin/env python3
"""
render_pinning_charts.py — Charts zur Pinning-Studie.

    py -3.14 scripts/research/render_pinning_charts.py \
        --ein <pinning.json> --out blog/posts/images/pinning-verfallstag

Zwei Bilder, jedes mit genau einer Aussage:

  1_perioden  Der Vergleich Verfallsfreitag gegen übrige Freitage, gesamt und
              in den beiden vorab gesetzten Teilperioden. Das Kernbild, weil
              es die überraschende Richtung zeigt: der Effekt ist NACH 2010
              grösser, nicht kleiner.
  2_je_ticker Die Verteilung der Differenzen über alle Ticker. Sie beantwortet
              die Frage, die bei jedem gepoolten Mittelwert zu stellen ist —
              trägt das Ergebnis breit, oder hängt es an einer Handvoll Titel?

Die absoluten Quoten der beiden Teilperioden stehen bewusst NICHT
nebeneinander zum Vergleich: Kurse sind zwischen den Perioden gestiegen, damit
ist die relative Rasterweite gefallen, und die Niveaus sind nicht vergleichbar.
Vergleichbar ist nur die Differenz innerhalb einer Periode — genau die zeigt
das Bild.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import statistics
import sys

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["text.parse_math"] = False
import matplotlib.pyplot as plt                                      # noqa: E402
from matplotlib.ticker import FuncFormatter                          # noqa: E402

BG, FLAECHE = "#000000", "#0a0a0e"
GOLD, DIM, HELL, GITTER = "#e8a820", "#9ca3af", "#e5e7eb", "#1f2430"
BLAU, ROT, GRAU = "#60a5fa", "#ef4444", "#4b5563"
DPI = 110


def _p(wert) -> str:
    if wert is None:
        return "p = n/a"
    return "p < 0,001" if wert < 0.001 else ("p = %.3f" % wert).replace(".", ",")


def _achse(ax, titel="", untertitel=""):
    ax.set_facecolor(FLAECHE)
    for s in ax.spines.values():
        s.set_color(GITTER)
    ax.tick_params(colors=DIM, labelsize=9)
    ax.grid(True, color=GITTER, linewidth=0.6, alpha=0.8, axis="y")
    ax.set_axisbelow(True)
    if titel:
        # pad gross genug, dass der Untertitel bei y=1.02 darunter Platz hat.
        # Mit pad=14 lagen Titel und Untertitel uebereinander.
        ax.set_title(titel, color=HELL, fontsize=13,
                     pad=30 if untertitel else 14, loc="left")
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


def chart_perioden(d: dict, ziel: pathlib.Path) -> None:
    g = d["gesamt"]
    reihen = [("1996-2026", g["quote_opex"], g["quote_kontrolle"],
               g["differenz_pp"], g["p"], g["n_opex"])]
    for p in d.get("perioden", []):
        reihen.append((p["periode"], p["quote_opex"], p["quote_kontrolle"],
                       p["differenz_pp"], p["p"], p["n_opex"]))

    fig, ax = plt.subplots(figsize=(10.4, 5.4))
    _achse(ax, "Am Verfallstag schliessen Aktien näher am Strike",
           "Anteil der Schlusskurse innerhalb von 0,125 $ eines Strikes")

    x = range(len(reihen))
    breite = 0.36
    opex = [r[1] * 100 for r in reihen]
    kont = [r[2] * 100 for r in reihen]
    ax.bar([i - breite / 2 for i in x], opex, width=breite, color=GOLD,
           label="Verfallsfreitag")
    ax.bar([i + breite / 2 for i in x], kont, width=breite, color=GRAU,
           label="übrige Freitage")

    hoch = max(opex + kont)
    for i, r in enumerate(reihen):
        ax.text(i - breite / 2, r[1] * 100 + hoch * 0.02,
                ("%.2f" % (r[1] * 100)).replace(".", ",") + " %",
                color=GOLD, fontsize=10, ha="center", fontweight="bold")
        ax.text(i + breite / 2, r[2] * 100 + hoch * 0.02,
                ("%.2f" % (r[2] * 100)).replace(".", ",") + " %",
                color=DIM, fontsize=10, ha="center")
        # Die Differenz ist die Aussage, nicht das Niveau.
        signifikant = r[4] is not None and r[4] < 0.05
        ax.text(i, -hoch * 0.10,
                "%s pp\n%s" % (("%+.2f" % r[3]).replace(".", ","), _p(r[4])),
                color=GOLD if signifikant else DIM, fontsize=9.5, ha="center",
                fontweight="bold" if signifikant else "normal")
        ax.text(i, -hoch * 0.20, "n = %d" % r[5], color=DIM, fontsize=8, ha="center")

    ax.set_xticks(list(x))
    ax.set_xticklabels([r[0] for r in reihen], fontsize=10.5)
    ax.set_ylim(-hoch * 0.26, hoch * 1.14)
    ax.set_ylabel("Anteil am Strike", color=DIM, fontsize=9.5)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: "%.0f %%" % v if v >= 0 else ""))
    leg = ax.legend(frameon=False, loc="upper right", fontsize=9.5)
    for t in leg.get_texts():
        t.set_color(HELL)

    _fuss(fig, "158 Ticker · 369 Kalendermonate · nur Freitage gegen Freitage · "
               "Konfidenz aus Bootstrap über Monate, einseitig")
    _speichern(fig, ziel)


def chart_je_ticker(d: dict, ziel: pathlib.Path) -> None:
    """Traegt das Ergebnis breit, oder haengt es an wenigen Titeln?

    Die Frage gehoert zu jedem gepoolten Mittelwert. Beim Bitcoin-Lead-Lag hing
    ein hochsignifikantes Ergebnis an einem einzigen Handelstag; seitdem wird
    sie hier immer gestellt.

    DIE ANTWORT IST HIER ZWEISCHNEIDIG und das Bild sagt das auch: kein
    einzelner Titel traegt das Ergebnis, die Verteilung ist unimodal und leicht
    positiv. Aber nur 54 % der Ticker sind positiv, und das ist kaum mehr als
    ein Muenzwurf. Je Titel liegen 24 bis 70 Verfallstage vor — zu wenig, um
    0,35 Prozentpunkte vom Rauschen zu trennen. Genau deshalb braucht die
    Studie 158 Titel und 369 Monate.
    """
    diffs = [(t["quote_opex"] - t["quote_kontrolle"]) * 100
             for t in d.get("je_ticker", [])]
    if not diffs:
        print("  (keine Ticker-Daten)")
        return
    positiv = sum(1 for x in diffs if x > 0)
    med = statistics.median(diffs)

    fig, ax = plt.subplots(figsize=(10.4, 5.0))
    _achse(ax, "Je einzelnem Titel ist der Effekt im Rauschen",
           "Differenz Verfallsfreitag minus übrige Freitage, je Ticker")

    ax.hist(diffs, bins=36, color=GOLD, alpha=0.75, edgecolor=FLAECHE, linewidth=0.6)
    ax.axvline(0, color=HELL, linewidth=1.3, linestyle="--", alpha=0.9)
    ax.axvline(med, color=BLAU, linewidth=2.0)
    hoehe = ax.get_ylim()[1]
    ax.text(med, hoehe * 0.94,
            "  Median " + ("%+.2f" % med).replace(".", ",") + " pp", color=BLAU,
            fontsize=10, ha="left", va="top", fontweight="bold")
    ax.text(0, hoehe * 0.74, "  kein Unterschied", color=DIM, fontsize=9,
            ha="left", va="top")
    ax.set_xlabel("Prozentpunkte", color=DIM, fontsize=9.5)
    ax.set_ylabel("Anzahl Ticker", color=DIM, fontsize=9.5)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: "%+.0f" % v))

    # EHRLICHE BESCHRIFTUNG. Ein erster Entwurf trug den Titel "der Effekt
    # haengt nicht an wenigen Titeln" — das Bild zeigt aber 54 % positive
    # Ticker, also kaum mehr als ein Muenzwurf. Was es WIRKLICH zeigt: die
    # Verteilung ist unimodal und leicht nach rechts verschoben, ohne dass ein
    # einzelner Ausreisser das Ergebnis traegt. Je Titel liegen nur 24 bis 70
    # Verfallstage vor, da verschwindet ein Effekt von 0,35 Punkten im
    # Rauschen. Sichtbar wird er erst gepoolt.
    ax.text(0.99, 0.94,
            "%d von %d Tickern positiv (%.0f %%)"
            % (positiv, len(diffs), positiv / len(diffs) * 100),
            transform=ax.transAxes, color=HELL, fontsize=10.5, ha="right",
            va="top", fontweight="bold")
    ax.text(0.99, 0.86,
            "kaum mehr als ein Münzwurf — je Titel sind es nur 24 bis 70\n"
            "Verfallstage. Der Effekt wird erst über alle zusammen sichtbar.",
            transform=ax.transAxes, color=DIM, fontsize=8.5, ha="right",
            va="top", linespacing=1.5)

    _fuss(fig, "Je Ticker mindestens 24 Verfallsfreitage und 100 Kontrollfreitage · "
               "1996-2026")
    _speichern(fig, ziel)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ein", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    d = json.loads(pathlib.Path(a.ein).read_text(encoding="utf-8"))
    out = pathlib.Path(a.out)
    print("Charts nach %s:" % out)
    chart_perioden(d, out / "1_perioden.png")
    chart_je_ticker(d, out / "2_je_ticker.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
