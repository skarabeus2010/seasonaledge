#!/usr/bin/env python3
"""
render_opex_november_charts.py — zwei Charts zum Blogartikel „Optionsverfall im November und die
Thanksgiving-Woche“ (2026-11-15). Alle Werte aus dem Faktenblatt
scripts/research/out/opex_november_thanksgiving_fakten.json (vorher opex_november_thanksgiving.py laufen lassen).

    PYTHONUTF8=1 py -3.14 scripts/research/render_opex_november_charts.py

Ausgabe: blog/posts/images/opex-november-thanksgiving/{1_pfad,2_woche_danach}_{de,en}.png
"""
from __future__ import annotations

import json
import textwrap
import pathlib
import sys

HIER = pathlib.Path(__file__).resolve().parent
REPO = HIER.parent.parent
sys.path.insert(0, str(HIER))
sys.path.insert(0, str(REPO))

import matplotlib                                                     # noqa: E402
matplotlib.use("Agg")
matplotlib.rcParams["text.parse_math"] = False
import matplotlib.pyplot as plt                                       # noqa: E402
from matplotlib.ticker import FuncFormatter                           # noqa: E402

from render_zweig_charts import _achse, _fuss, _speichern, _zahl, GOLD, DIM, HELL, GITTER, BLAU   # noqa: E402

FAKTEN = HIER / "out" / "opex_november_thanksgiving_fakten.json"
OUT = REPO / "blog" / "posts" / "images" / "opex-november-thanksgiving"

T = {
    "de": {
        "p_t": "S&P 500 rund um den Optionsverfall: November gegen übrige Monate",
        "p_u": "Mittlerer kumulierter Verlauf, Schluss 5 Handelstage vor dem Verfall = 100, 1973–2025",
        "p_nov": "November mit Thanksgiving in der Folgewoche (n = %d)",
        "p_rest": "übrige Monate (n = %d)",
        "p_x": "Handelstage relativ zum Verfallstag (0 = Verfallsfreitag)",
        "p_v": "Verfall", "p_tg": "Thanksgiving-Woche\n(im November)",
        "b_t": "Die Woche nach dem Optionsverfall",
        "b_u": "Rendite vom Schluss des Verfallstags bis Ende der Folgewoche, 1973–2025 · Balken: Mittel · Punkt: Median",
        "b_kat": ["November, Folgewoche = Thanksgiving", "November, 13 Tage Abstand", "übrige Monate, Woche nach Verfall", "alle Kalenderwochen"],
        "b_m": "Mittel", "b_med": "Median",
        "fuss": "^GSPC Kursindex ohne Dividenden, Datenstand 13.11.2026 · Verfall ab 02/2015 belegt, davor 3. Freitag nach Regel",
    },
    "en": {
        "p_t": "S&P 500 around options expiration: November versus other months",
        "p_u": "Mean cumulative path, close 5 trading days before expiration = 100, 1973–2025",
        "p_nov": "November with Thanksgiving in the following week (n = %d)",
        "p_rest": "other months (n = %d)",
        "p_x": "Trading days relative to expiration (0 = expiration Friday)",
        "p_v": "expiration", "p_tg": "Thanksgiving week\n(in November)",
        "b_t": "The week after options expiration",
        "b_u": "Return from the expiration close to the end of the following week, 1973–2025 · bars: mean · dot: median",
        "b_kat": ["November, next week = Thanksgiving", "November, 13-day gap", "other months, week after expiration", "all calendar weeks"],
        "b_m": "mean", "b_med": "median",
        "fuss": "^GSPC price index without dividends, data as of 2026-11-13 · expiration documented from 02/2015, before that 3rd Friday by rule",
    },
}


def pfad(f, lang):
    t = T[lang]
    x = f["pfad_offsets"]
    nov, rest = f["pfad_november_6"], f["pfad_uebrige"]
    fig, ax = plt.subplots(figsize=(11.4, 5.4))
    _achse(ax, t["p_t"], t["p_u"])
    ax.axvspan(0.5, 4.5, color=GOLD, alpha=0.07, lw=0)
    ax.text(2.5, 0.97, t["p_tg"], transform=ax.get_xaxis_transform(), color=GOLD, fontsize=8.5,
            ha="center", va="top", alpha=0.9)
    ax.axvline(0, color=DIM, lw=0.8, ls="--")
    ax.text(0.05, 0.03, t["p_v"], transform=ax.get_xaxis_transform(), color=DIM, fontsize=8.5)
    ax.axhline(100, color=GITTER, lw=0.8)
    ax.plot(x, nov["pfad"], color=GOLD, lw=2.4, marker="o", ms=4, label=t["p_nov"] % nov["n"])
    ax.plot(x, rest["pfad"], color=BLAU, lw=1.8, marker="o", ms=3, label=t["p_rest"] % rest["n"])
    for serie, farbe in ((nov["pfad"], GOLD), (rest["pfad"], BLAU)):
        ax.annotate(_zahl(serie[-1], "%.2f", lang), (x[-1], serie[-1]), xytext=(8, 0), textcoords="offset points",
                    color=farbe, fontsize=9, va="center")
    ax.set_xticks(x)
    ax.set_xticklabels([("t%+d" % k if k else "t0").replace("-", "−") for k in x])
    ax.set_xlim(x[0] - 0.3, x[-1] + 0.8)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _p: _zahl(v, "%.1f", lang)))
    ax.set_xlabel(t["p_x"], color=DIM, fontsize=9)
    fig.subplots_adjust(bottom=0.16)
    ax.legend(loc="upper left", frameon=False, labelcolor=HELL, fontsize=9)
    _fuss(fig, t["fuss"])
    _speichern(fig, OUT / ("1_pfad_%s.png" % lang))


def balken(f, lang):
    t = T[lang]
    gruppen = [f["B_woche_danach_nov6_gegen_rest"]["november_6"], f["D_13_woche_danach"],
               f["B_woche_danach_nov6_gegen_rest"]["uebrige"], f["C_alle_wochen"]]
    farben = [GOLD, GOLD, BLAU, DIM]
    fig, ax = plt.subplots(figsize=(11.4, 5.8))
    _achse(ax, t["b_t"], t["b_u"])
    xs = range(len(gruppen))
    mittel = [g["mittel"] for g in gruppen]
    bars = ax.bar(xs, mittel, color=farben, width=0.56, alpha=0.9)
    bars[1].set_alpha(0.45)
    ax.scatter(xs, [g["median"] for g in gruppen], color=HELL, zorder=3, s=28, label=t["b_med"])
    ax.axhline(0, color=GITTER, lw=0.9)
    for i, g in enumerate(gruppen):
        y = g["mittel"]
        txt = _zahl(y, "%+.2f %%", lang) if lang == "de" else ("%+.2f%%" % y)
        ax.text(i, y + (0.04 if y >= 0 else -0.04), txt.replace("-", "−"), color=HELL, ha="center", va="bottom" if y >= 0 else "top", fontsize=10)
    ax.set_xticks(list(xs))
    ax.set_xticklabels(["%s\nn = %s" % (textwrap.fill(k, 24), ("{:,}".format(g["n"]).replace(",", " " if lang == "de" else ",")))
                        for k, g in zip(t["b_kat"], gruppen)], color=DIM, fontsize=8.5)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _p: _zahl(v, "%.1f", lang) + (" %" if lang == "de" else "%")))
    lo = min(min(mittel), min(g["median"] for g in gruppen), 0)
    hi = max(max(mittel), max(g["median"] for g in gruppen))
    ax.set_ylim(lo - 0.25, hi + 0.3)
    ax.legend(loc="upper right", frameon=False, labelcolor=HELL, fontsize=9)
    fig.subplots_adjust(bottom=0.2)
    _fuss(fig, t["fuss"])
    _speichern(fig, OUT / ("2_woche_danach_%s.png" % lang))


def main():
    f = json.loads(FAKTEN.read_text(encoding="utf-8"))
    for lang in ("de", "en"):
        pfad(f, lang)
        balken(f, lang)


if __name__ == "__main__":
    main()
