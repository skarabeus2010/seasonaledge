#!/usr/bin/env python3
"""
render_zweig_charts.py — Charts zum Zweig Breadth Thrust (Blog 2026-10-27).

    py -3.14 -I scripts/research/render_zweig_charts.py <datenordner> \
        --out blog/posts/images/zweig-breadth-thrust

Der Datenordner enthaelt:
  unicorn/NYSE_advn.csv, unicorn/NYSE_decln.csv, unicorn/NYSE_unchn.csv
      (Format "YYYYMMDD, Zahl"; Archiv unicorn.us.com, 1965 bis 10.02.2020)
  gspc.json   Yahoo-Chart-JSON ^GSPC (Kursindex ohne Dividenden)

Rechnung = Referenzprobe (zbt_probe.py / zbt_probe2.py, von Codex geprueft):
  * Achse: Unicorn-Tage ohne Nullzeilen (A+D = 0) und ohne Tage, an denen
    ^GSPC keine Kurszeile hat.
  * Anteil A/(A+D), EMA ewm(span=10, adjust=False).
  * Signal: Anker = letzter Tag EMA < 0,40; Signal am ersten Tag EMA > 0,615
    mit i - Anker <= 10; danach Neuarmierung erst nach neuem Unterschreiten.
  * Auswertung ab 1971, Einstieg Schluss Signaltag, Horizonte in Handelstagen.

Das Skript bricht ab, wenn es nicht genau die elf erwarteten Signale findet.
Je Chart entsteht eine deutsche (_de) und eine englische (_en) Fassung.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["text.parse_math"] = False
import matplotlib.pyplot as plt                                      # noqa: E402
from matplotlib.ticker import FuncFormatter                          # noqa: E402

BG, FLAECHE = "#000000", "#0a0a0e"
GOLD, DIM, HELL, GITTER = "#e8a820", "#9ca3af", "#e5e7eb", "#1f2430"
BLAU, ROT, GRUEN = "#60a5fa", "#ef4444", "#22c55e"
DPI = 110

ERWARTET = ["1971-12-03", "1974-10-10", "1975-01-03", "1982-08-20",
            "1984-08-03", "2004-05-25", "2009-03-18", "2011-10-14",
            "2013-10-18", "2015-10-08", "2019-01-07"]
H = [10, 30, 60, 90, 120]
LO, HI, WIN = 0.40, 0.615, 10


# ---------------------------------------------------------------- Daten
def laden(d: pathlib.Path):
    def rd(n):
        s = pd.read_csv(d / "unicorn" / f"{n}.csv", header=None, names=["d", "v"],
                        skipinitialspace=True)
        s["d"] = pd.to_datetime(s["d"].astype(str))
        return s.set_index("d")["v"]
    df = pd.DataFrame({"a": rd("NYSE_advn"), "d": rd("NYSE_decln"), "u": rd("NYSE_unchn")})
    df = df[(df.a + df.d) > 0]
    df["r"] = df.a / (df.a + df.d)

    j = json.load(open(d / "gspc.json", encoding="utf-8"))["chart"]["result"][0]
    px = pd.Series(j["indicators"]["quote"][0]["close"],
                   index=pd.to_datetime(j["timestamp"], unit="s").normalize()).dropna()
    if px.index.tz is not None:
        px.index = px.index.tz_localize(None)
    px = px.groupby(px.index.date).last()
    px.index = pd.to_datetime(px.index)

    phantome = df.index.difference(px.index)
    c = df.drop(phantome)
    return df, c, px


def signale(x, lo=LO, hi=HI, win=WIN):
    out, arm = [], None
    for i, v in enumerate(x.values):
        if np.isnan(v):
            continue
        if v < lo:
            arm = i
        if arm is not None and v > hi and i - arm <= win:
            out.append(x.index[i]); arm = None
        elif arm is not None and i - arm > win:
            arm = None
    return out


def signale_erstes(x, lo=LO, hi=HI, win=WIN):
    out, start = [], None
    for i, v in enumerate(x.values):
        if start is not None and i - start > win:
            start = None
        if start is None and v < lo:
            start = i
        if start is not None and v > hi and i - start <= win:
            out.append(x.index[i]); start = None
    return out


def ema(s):
    return s.ewm(span=10, adjust=False).mean()


# ---------------------------------------------------------------- Texte
T = {
    "de": {
        "c1_t": "Breadth Thrust im Januar 2019",
        "c1_u": "10-Tage-EMA des Anteils steigender NYSE-Aktien, A/(A+D)",
        "c1_lo": "0,40 – überverkauft", "c1_hi": "0,615 – Thrust",
        "c1_sig": "Signal 07.01.2019", "c1_anker": "letzter Tag unter 0,40",
        "c1_px": "S&P 500 (rechte Achse)",
        "c2_t": "S&P 500 nach elf Signalen",
        "c2_u": "Mittlere Rendite ab Schluss des Signaltags gegen alle Starttage",
        "c2_sig": "nach Signal (n = 11)", "c2_bas": "Basisrate, alle Tage 1965–2020",
        "c2_x": "%d HT", "c2_pos": "%d/11 positiv",
        "c3_t": "Eine Regel, viele Zählungen",
        "c3_u": "Anzahl Signale 1965–2020 je Definitionsvariante",
        "fuss": "NYSE Advances/Declines: unicorn.us.com (1965 bis 10.02.2020) · "
                "^GSPC Kursindex ohne Dividenden · HT = Handelstage",
        "var": ["Standard\n0,40 / 0,615 EMA", "obere\n0,61", "obere\n0,62",
                "untere\n0,39", "untere\n0,41", "SMA\nstatt EMA",
                "Fenster ab\nerstem Tag", "Unveränderte\nim Nenner"],
        "dez": ",",
    },
    "en": {
        "c1_t": "Breadth thrust in January 2019",
        "c1_u": "10-day EMA of the share of advancing NYSE stocks, A/(A+D)",
        "c1_lo": "0.40 – oversold", "c1_hi": "0.615 – thrust",
        "c1_sig": "Signal 2019-01-07", "c1_anker": "last day below 0.40",
        "c1_px": "S&P 500 (right axis)",
        "c2_t": "S&P 500 after eleven signals",
        "c2_u": "Mean return from the signal-day close versus all start days",
        "c2_sig": "after signal (n = 11)", "c2_bas": "base rate, all days 1965–2020",
        "c2_x": "%d TD", "c2_pos": "%d/11 positive",
        "c3_t": "One rule, many counts",
        "c3_u": "Number of signals 1965–2020 per definition variant",
        "fuss": "NYSE advances/declines: unicorn.us.com (1965 to 2020-02-10) · "
                "^GSPC price index without dividends · TD = trading days",
        "var": ["Standard\n0.40 / 0.615 EMA", "upper\n0.61", "upper\n0.62",
                "lower\n0.39", "lower\n0.41", "SMA\ninstead of EMA",
                "window from\nfirst day", "unchanged in\ndenominator"],
        "dez": ".",
    },
}


def _zahl(v, fmt, lang):
    s = fmt % v
    return s.replace(".", ",") if lang == "de" else s


def _achse(ax, titel="", untertitel=""):
    ax.set_facecolor(FLAECHE)
    for s in ax.spines.values():
        s.set_color(GITTER)
    ax.tick_params(colors=DIM, labelsize=9)
    ax.grid(True, color=GITTER, linewidth=0.6, alpha=0.8, axis="y")
    ax.set_axisbelow(True)
    if titel:
        ax.set_title(titel, color=HELL, fontsize=13, pad=24, loc="left")
    if untertitel:
        ax.text(0.0, 1.02, untertitel, transform=ax.transAxes, color=DIM,
                fontsize=9, va="bottom")


def _fuss(fig, text):
    fig.text(0.01, 0.005, text, color=DIM, fontsize=7.5, ha="left")
    fig.text(0.99, 0.005, "seasonalpha.ai", color=GOLD, fontsize=7.5, ha="right")


def _speichern(fig, ziel):
    ziel.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(ziel, facecolor=BG, dpi=DPI, bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)
    print("  %s  (%.0f KB)" % (ziel.name, ziel.stat().st_size / 1024))


# ---------------------------------------------------------------- Charts
def chart_beispiel(e, px, signal, ziel, lang):
    t = T[lang]
    i = e.index.get_loc(signal)
    w = e.iloc[max(0, i - 60): i + 61]
    anker = max(k for k in range(i + 1) if e.iloc[k] < LO)
    fig, ax = plt.subplots(figsize=(11.4, 5.4))
    _achse(ax, t["c1_t"], t["c1_u"])
    ax.plot(w.index, w.values, color=GOLD, linewidth=2)
    ax.axhline(LO, color=ROT, linestyle="--", linewidth=1.1)
    ax.axhline(HI, color=GRUEN, linestyle="--", linewidth=1.1)
    box = dict(facecolor=FLAECHE, edgecolor="none", pad=1.5)
    ax.text(w.index[-1], LO - 0.012, t["c1_lo"], color=ROT, fontsize=9, va="top",
            ha="right", bbox=box, zorder=6)
    ax.text(w.index[-1], HI + 0.03, t["c1_hi"], color=GRUEN, fontsize=9, va="bottom",
            ha="right", bbox=box, zorder=6)
    ax.axvspan(e.index[anker], signal, color=GOLD, alpha=0.12)
    ax.scatter([signal], [e.loc[signal]], color=GRUEN, s=60, zorder=5)
    ax.annotate(t["c1_sig"], (signal, e.loc[signal]), xytext=(12, 10),
                textcoords="offset points", color=HELL, fontsize=10)
    ax.annotate(t["c1_anker"], (e.index[anker], e.iloc[anker]), xytext=(-30, -55),
                textcoords="offset points", color=HELL, fontsize=9, ha="right",
                arrowprops=dict(arrowstyle="-", color=DIM, lw=0.8))
    ax.set_ylim(0.25, 0.72)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: _zahl(v, "%.2f", lang)))
    ax2 = ax.twinx()
    p = px.loc[w.index[0]: w.index[-1]]
    ax2.plot(p.index, p.values, color=BLAU, linewidth=1.1, alpha=0.7, label=t["c1_px"])
    ax2.tick_params(colors=BLAU, labelsize=8.5)
    for s in ax2.spines.values():
        s.set_color(GITTER)
    ax2.legend(loc="lower right", facecolor=FLAECHE, edgecolor=GITTER,
               labelcolor=BLAU, fontsize=8.5)
    fig.autofmt_xdate()
    _fuss(fig, t["fuss"])
    _speichern(fig, ziel)


def chart_renditen(agg, ziel, lang):
    t = T[lang]
    fig, ax = plt.subplots(figsize=(11.4, 5.4))
    _achse(ax, t["c2_t"], t["c2_u"])
    x = np.arange(len(H))
    sig = [agg[h]["mittel"] for h in H]
    bas = [agg[h]["basis"] for h in H]
    ax.bar(x - 0.2, sig, width=0.38, color=GOLD, label=t["c2_sig"])
    ax.bar(x + 0.2, bas, width=0.38, color=DIM, label=t["c2_bas"])
    for k, h in enumerate(H):
        ax.text(k - 0.2, sig[k] + 0.3, _zahl(sig[k], "%+.2f %%", lang), color=GOLD,
                ha="center", fontsize=10, fontweight="bold")
        ax.text(k + 0.2, bas[k] + 0.3, _zahl(bas[k], "%+.2f %%", lang), color=DIM,
                ha="center", fontsize=9)
        ax.text(k - 0.2, -1.3, t["c2_pos"] % agg[h]["pos"], color=HELL,
                ha="center", fontsize=8.5)
    ax.set_xticks(x)
    ax.set_xticklabels([t["c2_x"] % h for h in H])
    ax.set_ylim(-2.2, 18.5)
    ax.set_yticks([0, 5, 10, 15])
    ax.axhline(0, color=GITTER, linewidth=1)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: _zahl(v, "%+.0f %%", lang)))
    ax.legend(loc="upper left", facecolor=FLAECHE, edgecolor=GITTER,
              labelcolor=HELL, fontsize=9)
    _fuss(fig, t["fuss"])
    _speichern(fig, ziel)


def chart_varianten(zahlen, ziel, lang):
    t = T[lang]
    fig, ax = plt.subplots(figsize=(11.4, 5.4))
    _achse(ax, t["c3_t"], t["c3_u"])
    x = np.arange(len(zahlen))
    farben = [GOLD] + [BLAU] * (len(zahlen) - 1)
    ax.bar(x, zahlen, width=0.6, color=farben)
    for k, z in enumerate(zahlen):
        ax.text(k, z + 0.3, str(z), color=farben[k], ha="center", fontsize=11,
                fontweight="bold")
    ax.axhline(zahlen[0], color=GOLD, linestyle="--", linewidth=1, alpha=0.6)
    ax.set_xticks(x)
    ax.set_xticklabels(t["var"], fontsize=8.5)
    ax.set_ylim(0, max(zahlen) + 3)
    ax.set_yticks(range(0, max(zahlen) + 3, 5))
    _fuss(fig, t["fuss"])
    _speichern(fig, ziel)


# ---------------------------------------------------------------- Ablauf
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("daten", type=pathlib.Path)
    ap.add_argument("--out", type=pathlib.Path,
                    default=pathlib.Path("blog/posts/images/zweig-breadth-thrust"))
    a = ap.parse_args()

    df, c, px = laden(a.daten)
    e = ema(c.r)
    sig = [s for s in signale(e) if s >= pd.Timestamp("1971-01-01")]
    gefunden = [s.strftime("%Y-%m-%d") for s in sig]
    print("Signale:", gefunden)
    if gefunden != ERWARTET:
        sys.exit("ABBRUCH: Signale weichen von der Referenz ab")
    if len(signale(e)) != 11:
        sys.exit("ABBRUCH: Signale 1965-1970 vorhanden")

    agg = {}
    for h in H:
        r = np.array([(px.iloc[px.index.get_loc(s) + h] / px.loc[s] - 1) * 100 for s in sig])
        p = px[(px.index >= "1965-03-01") & (px.index <= "2020-02-10")]
        b = (px.shift(-h) / px - 1).loc[p.index].dropna() * 100
        agg[h] = {"mittel": r.mean(), "median": float(np.median(r)),
                  "pos": int((r > 0).sum()), "basis": b.mean(),
                  "basis_pos": 100 * (b > 0).mean()}
        print("  %3d HT  Mittel %+.2f  Median %+.2f  %d/11  Basis %+.2f (%.0f %%)"
              % (h, r.mean(), np.median(r), (r > 0).sum(), b.mean(), 100 * (b > 0).mean()))
    for s in sig:
        i = px.index.get_loc(s)
        print("   ", s.date(), " ".join("%+.1f" % ((px.iloc[i + h] / px.iloc[i] - 1) * 100) for h in H))

    zahlen = [
        len(signale(e)),
        len(signale(e, hi=0.61)),
        len(signale(e, hi=0.62)),
        len(signale(e, lo=0.39)),
        len(signale(e, lo=0.41)),
        len(signale(c.r.rolling(10).mean())),
        len(signale_erstes(e)),
        len(signale(ema(c.a / (c.a + c.d + c.u)))),
    ]
    print("Varianten:", zahlen)
    if zahlen != [11, 13, 8, 7, 14, 19, 7, 3]:
        print("WARNUNG: Variantenzahlen weichen von der Referenz [11,13,8,7,14,19,7,3] ab")

    for lang in ("de", "en"):
        chart_beispiel(e, px, pd.Timestamp("2019-01-07"), a.out / f"1_ema_2019_{lang}.png", lang)
        chart_renditen(agg, a.out / f"2_renditen_{lang}.png", lang)
        chart_varianten(zahlen, a.out / f"3_varianten_{lang}.png", lang)


if __name__ == "__main__":
    main()
