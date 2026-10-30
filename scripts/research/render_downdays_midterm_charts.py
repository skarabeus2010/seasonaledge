#!/usr/bin/env python3
"""
render_downdays_midterm_charts.py — Charts zu den Blogartikeln vom 2026-10-30:
„Down-Days im SPY“ und „S&P 500 in der letzten Woche vor der Midterm-Wahl“.

    py -3.14 scripts/research/render_downdays_midterm_charts.py

Alle Werte kommen aus den Faktenblättern (down_days_fakten.py, midterm_letzte_woche_fakten.py), also aus
denselben eingefrorenen Datenständen wie der Text. Je Chart eine deutsche (_de) und eine englische (_en) Fassung.
Ausgabe: blog/posts/images/spy-down-days/ und blog/posts/images/midterm-letzte-woche/.
"""
from __future__ import annotations

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

from render_zweig_charts import (_achse, _fuss, _speichern, _zahl,    # noqa: E402
                                 GOLD, DIM, HELL, GITTER, BLAU, ROT, FLAECHE)
import down_days_fakten as DD                                         # noqa: E402
import midterm_letzte_woche_fakten as MW                              # noqa: E402

OUT_DD = REPO / "blog" / "posts" / "images" / "spy-down-days"
OUT_MW = REPO / "blog" / "posts" / "images" / "midterm-letzte-woche"

T = {
    "de": {
        "d1_t": "Wie oft der SPY um 2 % oder mehr fiel",
        "d1_u": "Anteil der Handelstage je Jahr mit einem Tagesverlust von mindestens 2 % (2006 und 2026 unvollständig)",
        "d2_t": "SPY nach einem Tagesverlust von mindestens 2 %",
        "d2_u": "Rendite ab Schluss des Verlusttags, gleiche Fälle für jeden Tag (n = %d) gegen alle Handelstage (n = %s)",
        "d2_m": "Mittel nach −2-%-Tagen", "d2_med": "Median nach −2-%-Tagen", "d2_b": "Mittel aller Handelstage",
        "d2_x": "Handelstage nach dem Verlusttag",
        "d3_t": "Rendite nach 50 Handelstagen: Mittel und schlechtester Zwischenstand",
        "d3_u": "Balken: mittlere Rendite nach 50 HT (n an der Achse) · Punkte: mittlerer größter Zwischenverlust in den ersten 15 HT (alle Tage n = 5\u202f016)",
        "d3_kat": ["alle Tage","≤ −1 %", "≤ −2 %", "≤ −3 %", "≤ −4 %"],
        "d3_l1": "Rendite nach 50 HT (Mittel)", "d3_l2": "größter Zwischenverlust bis 15 HT (Mittel)",
        "fuss_d": "SPY, adjustierte Schlusskurse (Gesamtrendite-Näherung), 30.10.2006–29.10.2026 · HT = Handelstage",
        "m1_t": "S&P 500 in der letzten Woche vor der Midterm-Wahl",
        "m1_u": "Rendite der fünf Handelstage bis zum Schluss am Wahltag (bzw. Vortag), 31 Wahlen 1898–2022",
        "m1_m": "Mittel %s %%",
        "m2_t": "Tag für Tag: Wahljahre gegen dieselben Tage ohne Wahl",
        "m2_u": "Mittlere Tagesrendite, 31 Wahlen und je zwei Vergleichsjahre (Pseudotermin im November)",
        "m2_kat": ["t−4", "t−3", "t−2", "t−1", "t0\n(Referenztag)", "Tag nach\nder Wahl"],
        "m2_w": "Midterm-Jahr", "m2_k": "Vergleichsjahre ohne Wahl",
        "fuss_m": "^GSPC Kursindex (vor 1957 zurückgerechnet), Datenstand 06.10.2026 · t0 = letzter Schluss am/vor dem Wahltag",
    },
    "en": {
        "d1_t": "How often SPY fell 2% or more",
        "d1_u": "Share of trading days per year with a daily loss of at least 2% (2006 and 2026 incomplete)",
        "d2_t": "SPY after a daily loss of at least 2%",
        "d2_u": "Return from the close of the down day, same cases for every day (n = %d) versus all trading days (n = %s)",
        "d2_m": "Mean after −2% days", "d2_med": "Median after −2% days", "d2_b": "Mean of all trading days",
        "d2_x": "Trading days after the down day",
        "d3_t": "Return after 50 trading days: mean and worst interim level",
        "d3_u": "Bars: mean return after 50 TD (n on the axis) · dots: mean largest interim loss in the first 15 TD (all days n = 5,016)",
        "d3_kat": ["all days","≤ −1%", "≤ −2%", "≤ −3%", "≤ −4%"],
        "d3_l1": "return after 50 TD (mean)", "d3_l2": "largest interim loss within 15 TD (mean)",
        "fuss_d": "SPY, adjusted closes (total-return approximation), 2006-10-30 to 2026-10-29 · TD = trading days",
        "m1_t": "S&P 500 in the last week before the midterm election",
        "m1_u": "Return of the five trading days up to the close on election day (or the day before), 31 elections 1898–2022",
        "m1_m": "mean %s%%",
        "m2_t": "Day by day: election years versus the same days without an election",
        "m2_u": "Mean daily return, 31 elections and two comparison years each (pseudo date in November)",
        "m2_kat": ["t−4", "t−3", "t−2", "t−1", "t0\n(reference day)", "day after\nthe election"],
        "m2_w": "midterm year", "m2_k": "comparison years without an election",
        "fuss_m": "^GSPC price index (back-calculated before 1957), data as of 2026-10-06 · t0 = last close on/before election day",
    },
}


def _pct(lang, nk=1, vz=False):
    def f(v, _):
        s = _zahl(v, ("%+." if vz else "%.") + f"{nk}f", lang)
        return s + (" %" if lang == "de" else "%")
    return FuncFormatter(f)


def chart_haeufigkeit(f, lang, ziel):
    t = T[lang]
    q = f["stufen"]["2"]["je_jahr_quote"]
    jahre = sorted(q)
    fig, ax = plt.subplots(figsize=(11.4, 5.0))
    _achse(ax, t["d1_t"], t["d1_u"])
    werte = [100 * q[j] for j in jahre]
    ax.bar(jahre, werte, color=[GOLD if j not in ("2006", "2026") else DIM for j in jahre], width=0.7)
    for j, v in zip(jahre, werte):
        if v >= 4:
            ax.text(j, v + 0.3, _zahl(v, "%.1f", lang), color=HELL, fontsize=8, ha="center")
    ax.yaxis.set_major_formatter(_pct(lang, 0))
    ax.tick_params(axis="x", rotation=60)
    _fuss(fig, t["fuss_d"])
    _speichern(fig, ziel)


def chart_pfad(f, lang, ziel):
    t, p = T[lang], f["pfad"]
    x = list(range(len(p["ereignis_mittel"])))
    fig, ax = plt.subplots(figsize=(11.4, 5.4))
    _achse(ax, t["d2_t"], t["d2_u"] % (p["n_ereignisse"], f"{p['n_basis']:,}".replace(",", "\u202f" if lang == "de" else ",")))
    ax.plot(x, p["ereignis_mittel"], color=GOLD, linewidth=2.2, label=t["d2_m"])
    ax.plot(x, p["ereignis_median"], color=GOLD, linewidth=1.3, linestyle="--", label=t["d2_med"])
    ax.plot(x, p["basis_mittel"], color=BLAU, linewidth=1.8, label=t["d2_b"])
    ax.axhline(0, color=DIM, linewidth=0.8)
    for h in (15, 30, 50):
        ax.axvline(h, color=GITTER, linewidth=1)
        for serie, farbe, dy in ((p["ereignis_mittel"], GOLD, 8), (p["basis_mittel"], BLAU, -14)):
            ax.annotate(_zahl(serie[h], "%+.2f", lang) + (" %" if lang == "de" else "%"), (h, serie[h]),
                        xytext=(-4, dy), textcoords="offset points", color=farbe, fontsize=9, ha="right")
    ax.set_xlabel(t["d2_x"], color=DIM, fontsize=9)
    ax.yaxis.set_major_formatter(_pct(lang, 0, vz=True))
    ax.legend(loc="upper left", facecolor=FLAECHE, edgecolor=GITTER, labelcolor=HELL, fontsize=9)
    _fuss(fig, t["fuss_d"])
    _speichern(fig, ziel)


def chart_rendite_risiko(f, lang, ziel):
    t = T[lang]
    rend = [f["basis"]["50"]["alle"]["mittel"]] + [f["stufen"][s]["h"]["50"]["alle"]["mittel"] for s in ("1", "2", "3", "4")]
    ris = [f["basis_risiko15"]["mittel"]] + [f["stufen"][s]["risiko15"]["mittel"] for s in ("1", "2", "3", "4")]
    ns = [f["basis"]["50"]["alle"]["n"]] + [f["stufen"][s]["h"]["50"]["alle"]["n"] for s in ("1", "2", "3", "4")]
    x = list(range(5))
    fig, ax = plt.subplots(figsize=(11.4, 5.4))
    _achse(ax, t["d3_t"], t["d3_u"])
    ax.bar(x, rend, color=[BLAU] + [GOLD] * 4, width=0.55, label=t["d3_l1"])
    ax.scatter(x, ris, color=ROT, s=70, zorder=5, label=t["d3_l2"])
    for i in x:
        ax.text(i, rend[i] + 0.35, _zahl(rend[i], "%+.2f", lang) + (" %" if lang == "de" else "%"),
                color=HELL, fontsize=9.5, ha="center")
        ax.text(i, ris[i] - 0.9, _zahl(ris[i], "%+.2f", lang) + (" %" if lang == "de" else "%"),
                color=ROT, fontsize=9, ha="center", va="top")
    ax.axhline(0, color=DIM, linewidth=0.8)
    ax.set_xticks(x, [f"{k}\nn = {n:,}".replace(",", "\u202f" if lang == "de" else ",") for k, n in zip(t["d3_kat"], ns)])
    ax.set_ylim(min(ris) - 2.5, max(rend) + 1.5)
    ax.yaxis.set_major_formatter(_pct(lang, 0, vz=True))
    ax.legend(loc="upper left", facecolor=FLAECHE, edgecolor=GITTER, labelcolor=HELL, fontsize=9)
    _fuss(fig, t["fuss_d"])
    _speichern(fig, ziel)


def chart_wochen(f, lang, ziel):
    t, a = T[lang], f["alle"]
    jahre, werte = a["jahre"], [a["wochen_werte"][str(j)] for j in a["jahre"]]
    fig, ax = plt.subplots(figsize=(11.4, 5.2))
    _achse(ax, t["m1_t"], t["m1_u"])
    ax.bar([str(j) for j in jahre], werte, color=[GOLD if v > 0 else ROT for v in werte], width=0.7)
    m = a["woche"]["mittel"]
    ax.axhline(m, color=BLAU, linestyle="--", linewidth=1.2)
    ax.text(len(jahre) - 0.5, m + 0.2, t["m1_m"] % _zahl(m, "%+.2f", lang).replace("%", ""), color=BLAU,
            fontsize=9, ha="right")
    ax.axhline(0, color=DIM, linewidth=0.8)
    ax.yaxis.set_major_formatter(_pct(lang, 0, vz=True))
    ax.tick_params(axis="x", rotation=60)
    _fuss(fig, t["fuss_m"])
    _speichern(fig, ziel)


def chart_tage(f, lang, ziel):
    t, a = T[lang], f["alle"]
    w = [a["tage"][str(j)]["mittel"] for j in MW.TAGE]
    d = [a["gepaart"]["tage_differenz"][str(j)] for j in MW.TAGE]
    k = [wi - di for wi, di in zip(w, d)]                 # Kontrollmittel = Wahl − Differenz (gleiche Kohorte)
    x = list(range(len(MW.TAGE)))
    fig, ax = plt.subplots(figsize=(11.4, 5.2))
    _achse(ax, t["m2_t"], t["m2_u"])
    ax.bar([i - 0.19 for i in x], w, width=0.36, color=GOLD, label=t["m2_w"])
    ax.bar([i + 0.19 for i in x], k, width=0.36, color=BLAU, label=t["m2_k"])
    for i in x:
        ax.text(i - 0.19, max(w[i], 0) + 0.02, _zahl(w[i], "%+.2f", lang), color=HELL, fontsize=8.5, ha="center")
        ax.text(i + 0.19, max(k[i], 0) + 0.02, _zahl(k[i], "%+.2f", lang), color=DIM, fontsize=8.5, ha="center")
    ax.axvspan(3.5, 4.5, color=GOLD, alpha=0.07)
    ax.axhline(0, color=DIM, linewidth=0.8)
    ax.set_xticks(x, t["m2_kat"])
    ax.yaxis.set_major_formatter(_pct(lang, 1, vz=True))
    ax.legend(loc="upper left", facecolor=FLAECHE, edgecolor=GITTER, labelcolor=HELL, fontsize=9)
    _fuss(fig, t["fuss_m"])
    _speichern(fig, ziel)


def main():
    fd = DD.fakten(DD.lade())
    fm = MW.fakten(MW.lade())
    if fm["alle"]["gepaart"]["n_tripel"] != fm["alle"]["woche"]["n"]:
        raise SystemExit("Chart 2 (Midterm) setzt voraus, dass alle Wahlen ein vollständiges Tripel haben")
    for lang in ("de", "en"):
        chart_haeufigkeit(fd, lang, OUT_DD / f"1_haeufigkeit_{lang}.png")
        chart_pfad(fd, lang, OUT_DD / f"2_pfad_{lang}.png")
        chart_rendite_risiko(fd, lang, OUT_DD / f"3_rendite_risiko_{lang}.png")
        chart_wochen(fm, lang, OUT_MW / f"1_wochen_{lang}.png")
        chart_tage(fm, lang, OUT_MW / f"2_tage_{lang}.png")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
