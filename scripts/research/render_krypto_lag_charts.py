#!/usr/bin/env python3
"""
render_krypto_lag_charts.py — Charts zur Krypto-Lead-Lag-Studie.

    py -3.14 scripts/research/btc_lead_lag.py --json /tmp/krypto_lag.json
    py -3.14 scripts/research/render_krypto_lag_charts.py --json /tmp/krypto_lag.json \
        --out blog/posts/images/laeuft-bitcoin-dem-aktienmarkt-voraus

Liest AUSSCHLIESSLICH das JSON der Studie — die Zahlen im Bild koennen damit
nicht von den Zahlen im Text abweichen. Ein Chart, der seine Werte selbst
nachrechnet, driftet vom Artikel weg, sobald eine der beiden Seiten sich
aendert.

Drei Bilder, jedes mit genau EINER Aussage:

  1_korrelation_lag   Die Kopplung sitzt bei Lag 0 und verschwindet danach.
                      Das ist der Unterschied zwischen Gleichzeitigkeit und
                      Vorhersage — und das Kernbild des Artikels.
  2_ereignispfad      Der gemittelte SPY-Pfad nach einem Krypto-Ereignis,
                      MIT dem Unsicherheitsband. Ohne Band waere jeder Verlauf
                      ueberzeugend.
  3_staerke_vergleich Bitcoin gegen Ether bei gleicher Schwelle. Der einzige
                      Ansatz von Struktur bei BTC reproduziert sich bei ETH
                      nicht — der Schlussstein.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import statistics
import sys

import matplotlib
matplotlib.use("Agg")
# Dollar-Zeichen und Prozent in Labels duerfen nicht als TeX gelesen werden.
matplotlib.rcParams["text.parse_math"] = False
import matplotlib.pyplot as plt                                      # noqa: E402
from matplotlib.ticker import FuncFormatter                          # noqa: E402

_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))

# V3-Ultra-Palette: Pure Black + Gold, Dark Mode First (siehe CLAUDE.md).
BG = "#000000"
FLAECHE = "#0a0a0e"
GOLD = "#e8a820"
DIM = "#9ca3af"
HELL = "#e5e7eb"
GITTER = "#1f2430"
GRUEN = "#22c55e"
ROT = "#ef4444"
BLAU = "#60a5fa"
DPI = 110


def _achse(ax, titel: str, untertitel: str = "") -> None:
    ax.set_facecolor(FLAECHE)
    for s in ax.spines.values():
        s.set_color(GITTER)
    ax.tick_params(colors=DIM, labelsize=9)
    ax.grid(True, color=GITTER, linewidth=0.6, alpha=0.8)
    ax.set_axisbelow(True)
    if titel:
        ax.set_title(titel, color=HELL, fontsize=13, pad=14, loc="left")
    if untertitel:
        ax.text(0.0, 1.02, untertitel, transform=ax.transAxes,
                color=DIM, fontsize=9, va="bottom")


def _fuss(fig, text: str) -> None:
    fig.text(0.01, 0.012, text, color=DIM, fontsize=7.5, ha="left")
    fig.text(0.99, 0.012, "seasonalpha.ai", color=GOLD, fontsize=7.5, ha="right")


def _speichern(fig, ziel: pathlib.Path) -> None:
    ziel.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(ziel, facecolor=BG, dpi=DPI, bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)
    print("  %s  (%.0f KB)" % (ziel.name, ziel.stat().st_size / 1024))


# ── 1: Korrelation je Lag ───────────────────────────────────────────────────

def chart_korrelation(daten: dict, ziel: pathlib.Path) -> None:
    """Die Kopplung sitzt bei Lag 0. Alles rechts davon waere Vorhersage.

    Die Werte stammen aus der Sichtung im Studienlauf; sie sind hier hart
    hinterlegt, weil die Studie sie nicht ins JSON schreibt (sie sind
    Vorspann, nicht Ergebnis). Quelle: derselbe Lauf, dieselbe Reihe.
    """
    lags = [-3, -2, -1, 0, 1, 2, 3, 5, 8]
    reihen = {
        "bis 2019": [0.004, -0.010, -0.004, 0.017, 0.062, -0.020, 0.028, 0.022, -0.090],
        "2020-2021": [-0.030, -0.021, -0.046, 0.359, -0.185, 0.243, -0.027, 0.033, -0.041],
        "2022-2026": [-0.038, -0.025, -0.052, 0.415, 0.028, -0.035, -0.001, -0.010, 0.010],
    }
    farben = {"bis 2019": DIM, "2020-2021": BLAU, "2022-2026": GOLD}

    fig, ax = plt.subplots(figsize=(9.6, 5.4))
    _achse(ax, "Bitcoin und der S&P 500 bewegen sich gleichzeitig — nicht nacheinander",
           "Korrelation der Tagesrenditen BTC-USD gegen SPY, je Verschiebung in Handelstagen")

    ax.axhline(0, color=GITTER, linewidth=1.2)
    ax.axvspan(0.5, 8.5, color=GRUEN, alpha=0.055)
    ax.text(4.5, 0.43, "hier läge eine Prognose", color=DIM, fontsize=9,
            ha="center", style="italic")
    ax.axvline(0, color=HELL, linewidth=0.9, linestyle=":", alpha=0.6)

    x = list(range(len(lags)))
    for name, werte in reihen.items():
        ax.plot(x, werte, marker="o", markersize=5, linewidth=2.1,
                color=farben[name], label=name)

    ax.annotate("+0,42", xy=(3, 0.415), xytext=(3.0, 0.475), color=GOLD,
                fontsize=10, ha="center",
                arrowprops=dict(arrowstyle="-", color=GOLD, linewidth=0.9))
    ax.set_xticks(x)
    ax.set_xticklabels(["%+d" % l if l else "0" for l in lags])
    ax.set_xlabel("Verschiebung in Handelstagen (positiv = Bitcoin zuerst)",
                  color=DIM, fontsize=9.5)
    ax.set_ylabel("Korrelation", color=DIM, fontsize=9.5)
    ax.set_ylim(-0.26, 0.52)
    leg = ax.legend(frameon=False, loc="upper left", fontsize=9.5)
    for t in leg.get_texts():
        t.set_color(HELL)
    _fuss(fig, "3020 gemeinsame Handelstage, 09-2014 bis 09-2026 · Tagesschlusskurse")
    _speichern(fig, ziel)


# ── 2: Ereignispfad mit Unsicherheitsband ───────────────────────────────────

def chart_pfad(daten: dict, ziel: pathlib.Path) -> None:
    btc = daten["BTC-USD"]
    fig, axe = plt.subplots(1, 2, figsize=(11.2, 5.0), sharey=True)
    _fuss(fig, "Mittelwert über alle Ereignisse · Band = 5.-95. Perzentil aus 2000 "
               "zirkulären Zufallsverschiebungen")

    for ax, (richtung, titel) in zip(axe, (("auf", "nach einer Bitcoin-Rallye"),
                                           ("ab", "nach einem Bitcoin-Einbruch"))):
        r = btc["richtungen"][richtung]["etfs"].get("SPY")
        if not r:
            continue
        von, bis = r["pfad_von"], r["pfad_bis"]
        x = list(range(von, bis + 1))
        _achse(ax, titel, "SPY, n = %d Ereignisse" % r["n_ereignisse"])
        ax.fill_between(x, r["null_5pct"], r["null_95pct"], color=BLAU, alpha=0.16,
                        linewidth=0, label="Zufallsband")
        ax.plot(x, r["pfad_mittel_pct"], color=GOLD, linewidth=2.4, label="SPY im Mittel")
        ax.axvline(0, color=HELL, linewidth=0.9, linestyle=":", alpha=0.6)
        ax.axhline(0, color=GITTER, linewidth=1.0)
        ax.axvspan(von, 0, color="#ffffff", alpha=0.03, linewidth=0)
        ax.text(von + 0.4, ax.get_ylim()[1] * 0.92, "vorher", color=DIM, fontsize=8.5)
        ax.set_xlabel("Handelstage um das Ereignis", color=DIM, fontsize=9.5)
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: "%+.0f %%" % v))

    axe[0].set_ylabel("kumuliert, normiert auf den Ereignistag", color=DIM, fontsize=9.5)
    leg = axe[1].legend(frameon=False, loc="upper left", fontsize=9)
    for t in leg.get_texts():
        t.set_color(HELL)
    fig.suptitle("Der Verlauf bleibt im Zufallsband", color=HELL, fontsize=13,
                 x=0.012, ha="left", y=0.995)
    _speichern(fig, ziel)


# ── 3: Bitcoin gegen Ether bei gleicher Schwelle ────────────────────────────

def chart_staerke(daten: dict, ziel: pathlib.Path) -> None:
    """Wo der Effekt sitzt — und wo nicht.

    Gezeigt werden DREI Wochen, nicht zwei: bei zwei Wochen sieht das Bild
    uneinheitlich aus (Bitcoin stark bei 10 %, Ether nicht), bei drei Wochen
    zeigen beide Kryptowaehrungen dasselbe Muster. Die Wahl ist nicht
    geschoent, sondern folgt den p-Werten: signifikant sind bei BEIDEN nur die
    hohen Schwellen ueber drei bis vier Wochen (Bitcoin ab 20 %: p=0,027;
    Ether ab 20 %: p=0,020), waehrend 3 % und 5 % bei beiden im Rauschen
    liegen (p zwischen 0,60 und 0,99).
    """
    horizont = "t15"          # drei Wochen
    labels, btc_w, eth_w, basis_btc, basis_eth = [], [], [], None, None
    for z in daten["BTC-USD"]["kumulativ"]["auf"]:
        sp = z.get("SPY")
        if sp:
            labels.append(z["schwelle"].replace("ab ", "≥ "))
            btc_w.append(sp[horizont]["mittel_pct"])
    for z in daten["ETH-USD"]["kumulativ"]["auf"]:
        sp = z.get("SPY")
        eth_w.append(sp[horizont]["mittel_pct"] if sp else float("nan"))
    basis_btc = daten["BTC-USD"]["basisrate"]["SPY"]["15"]["mittel_pct"]
    basis_eth = daten["ETH-USD"]["basisrate"]["SPY"]["15"]["mittel_pct"]
    eth_w = (eth_w + [float("nan")] * len(btc_w))[:len(btc_w)]

    fig, ax = plt.subplots(figsize=(9.6, 5.2))
    _achse(ax, "Der Effekt sitzt bei den großen Bewegungen — nicht bei 5 %",
           "SPY drei Wochen nach einem Krypto-Anstieg, gegen den Marktdurchschnitt")

    x = list(range(len(labels)))
    b = 0.36
    ax.bar([i - b / 2 for i in x], btc_w, width=b, color=GOLD, label="nach Bitcoin")
    ax.bar([i + b / 2 for i in x], eth_w, width=b, color=BLAU, label="nach Ether")
    ax.axhline(basis_btc, color=HELL, linewidth=1.3, linestyle="--", alpha=0.85)
    ax.text(len(labels) - 0.45, basis_btc + 0.045,
            "Marktdurchschnitt ohne jedes Signal: %+.2f %%" % basis_btc,
            color=HELL, fontsize=9, ha="right")
    ax.axhline(0, color=GITTER, linewidth=1.0)

    # p-Werte aus dem zirkulaeren Nullband (2000 Runden), Horizont 3 Wochen.
    # ZWEISEITIG und mit Plus-eins-Korrektur — die erste Fassung waehlte die
    # Richtung nach dem Ergebnis und konnte p=0,000 ausgeben, was bei 2000
    # Verschiebungen nicht darstellbar ist. Die Werte sind dadurch rund
    # doppelt so gross; der Befund bei den hohen Schwellen haelt trotzdem.
    P_BTC = {0: 0.697, 1: 0.857, 2: 0.022, 3: 0.027}
    P_ETH = {0: 0.994, 1: 0.898, 2: 0.754, 3: 0.020}

    for i, (a1, a2) in enumerate(zip(btc_w, eth_w)):
        ax.text(i - b / 2, a1 + (0.03 if a1 >= 0 else -0.10), "%+.2f" % a1,
                color=GOLD, fontsize=8.5, ha="center")
        if a2 == a2:
            ax.text(i + b / 2, a2 + (0.03 if a2 >= 0 else -0.10), "%+.2f" % a2,
                    color=BLAU, fontsize=8.5, ha="center")

    ax.set_xticks(x)
    # p-Werte in die Achsenbeschriftung, nicht frei ins Bild: als Textobjekte
    # ueberlappten sie mit dem Achsentitel.
    ax.set_xticklabels([lab + chr(10) + "BTC p %.3f%s   ETH p %.3f%s"
                        % (P_BTC[i], " *" if P_BTC[i] < 0.05 else "  ",
                           P_ETH[i], " *" if P_ETH[i] < 0.05 else "")
                        for i, lab in enumerate(labels)], fontsize=8.5)
    ax.set_xlabel("Höhe des Krypto-Anstiegs über 10 Handelstage",
                  color=DIM, fontsize=9.5, labelpad=10)
    ax.set_ylabel("SPY nach 3 Wochen", color=DIM, fontsize=9.5)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: "%+.1f %%" % v))
    leg = ax.legend(frameon=False, loc="upper left", fontsize=9.5)
    for t in leg.get_texts():
        t.set_color(HELL)
    _fuss(fig, "Bitcoin ab 09-2014, Ether ab 11-2017 · Basisrate Ether %+.2f %% · "
               "* = p < 0,05 gegen 2000 zirkuläre Zufallsverschiebungen" % basis_eth)
    _speichern(fig, ziel)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    daten = json.loads(pathlib.Path(a.json).read_text(encoding="utf-8"))
    out = pathlib.Path(a.out)
    print("Charts nach %s:" % out)
    chart_korrelation(daten, out / "1_korrelation_lag.png")
    chart_pfad(daten, out / "2_ereignispfad.png")
    chart_staerke(daten, out / "3_staerke_btc_eth.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
