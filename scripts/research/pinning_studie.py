#!/usr/bin/env python3
"""
pinning_studie.py — Schliessen Aktien am Verfallstag näher an Strikes?

    py -3.14 scripts/research/pinning_studie.py --json <datei>

DIE FRAGE, und sie ist alt und gut untersucht: Wenn an einem Strike viel Open
Interest liegt, zieht das Delta-Hedging der Stillhalter den Kurs am Verfallstag
in dessen Nähe („Pinning"). Ni/Pearson/Poteshman finden für optionable Aktien
rund 19,2 % Schlusskurse innerhalb von 0,125 $ eines Strikes am Verfallsfreitag
gegen 18,0 % an anderen Tagen — ein kleiner, aber sauber identifizierter Effekt.

WARUM DIESE STUDIE UND NICHT EINE ANDERE: Sie stellt EINE Frage. Keine Matrix,
kein Screening, keine nachträglich gewählte Schwelle. Genau das hat diese Woche
gefehlt, als 470 Intermarket-Paare nach der Korrektur nichts übrig liessen.

DAS METHODISCHE PROBLEM UND SEINE LÖSUNG — das ist der Kern des Skripts:

    Wir kennen die historischen Strike-Raster nicht. Echte Strikes liegen erst
    ab 09-2025 vor, und die Raster haben sich über die Jahre geändert (1-$-
    Strikes, Penny Pilot, Splits). Jede Annahme über das Raster ist falsch.

    Gelöst wird das NICHT durch ein besseres Raster, sondern durch die
    KONTROLLGRUPPE: dieselbe Rasterannahme wird auf Verfallsfreitage UND auf
    alle übrigen Freitage derselben Ticker im selben Zeitraum angewandt. Ist
    das Raster falsch, ist es in beiden Gruppen gleich falsch — die DIFFERENZ
    bleibt aussagekräftig. Eine Kontrollgruppe, die den eigenen Messfehler
    absorbiert, ist mehr wert als eine genauere Messung.

    Aus demselben Grund werden nur Freitage mit Freitagen verglichen und nicht
    mit beliebigen Wochentagen: sonst mischte man den Wochentagseffekt hinein.

DIE VORAB FESTGELEGTE HYPOTHESE (eine, gerichtet):

    H1: Der Anteil der Schlusskurse innerhalb von 0,125 $ eines Strikes ist an
        monatlichen Verfallsfreitagen HÖHER als an übrigen Freitagen.

WARUM DER BOOTSTRAP ÜBER VERFALLSMONATE GEHT und nicht über Ticker-Tage:
163 Ticker am selben Freitag sind nicht 163 unabhängige Beobachtungen. Sie
teilen denselben Markttag, dieselbe Nachrichtenlage, dieselbe Vola. Wer über
Ticker-Tage zieht, behauptet eine Stichprobe, die es nicht gibt, und bekommt
ein absurd enges Intervall. Gezogen werden deshalb ganze MONATE.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import random
import sys
from collections import defaultdict
from datetime import date

_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))

from shared.data import KursreiheFehlt, lade_closes                  # noqa: E402
from shared.nyse_holidays import get_all_opex_dates                  # noqa: E402
from shared.options_universe import all_option_tickers               # noqa: E402
from shared.realized_vol import iso_tag                              # noqa: E402

TOLERANZ = 0.125             # "am Strike" nach Ni/Pearson/Poteshman
START_JAHR = 1996
BOOTSTRAP = 2000
MIN_KURS = 5.0               # darunter ist das Raster zu fein und zu unklar
MAX_KURS = 1000.0            # darüber sind Raster sehr breit und uneinheitlich


def raster(kurs: float) -> float:
    """Angenommener Strike-Abstand. Bewusst grob — siehe Docstring oben.

    Die Annahme muss nicht stimmen; sie muss nur für Verfalls- und
    Kontrollfreitage DIESELBE sein.
    """
    if kurs < 25.0:
        return 2.5
    if kurs < 200.0:
        return 5.0
    return 10.0


def abstand_zum_strike(kurs: float) -> float:
    r = raster(kurs)
    rest = kurs % r
    return min(rest, r - rest)


def freitags_beobachtungen(ticker: str, opex: set[str]) -> list[dict]:
    """Alle Freitags-Schlusskurse eines Tickers, markiert als OPEX oder nicht."""
    daten, closes = lade_closes(ticker)
    out = []
    for d, c in zip(daten, closes):
        if c is None or not math.isfinite(float(c)):
            continue
        kurs = float(c)
        if not (MIN_KURS <= kurs <= MAX_KURS):
            continue
        t = iso_tag(d)
        if int(t[:4]) < START_JAHR:
            continue
        if date.fromisoformat(t).weekday() != 4:          # 4 = Freitag
            continue
        out.append({
            "tag": t, "monat": t[:7], "kurs": kurs,
            "opex": t in opex,
            "gepinnt": abstand_zum_strike(kurs) <= TOLERANZ,
        })
    return out


def quote(beob: list[dict]) -> float:
    return (sum(1 for b in beob if b["gepinnt"]) / len(beob)) if beob else float("nan")


def bootstrap_differenz(beob: list[dict]) -> tuple[float, float, float]:
    """Konfidenzintervall und p-Wert der Quotendifferenz, gezogen über MONATE.

    Der p-Wert ist einseitig (H1 behauptet "höher") mit Plus-eins-Korrektur und
    misst, wie oft die gebootstrappte Differenz NICHT positiv ist — also wie
    oft die Daten die Richtung nicht tragen.
    """
    je_monat = defaultdict(list)
    for b in beob:
        je_monat[b["monat"]].append(b)
    monate = list(je_monat.values())
    if len(monate) < 30:
        return float("nan"), float("nan"), float("nan")

    rnd = random.Random(20260922)
    diffs = []
    for _ in range(BOOTSTRAP):
        zieh = [x for _ in range(len(monate))
                for x in monate[rnd.randrange(len(monate))]]
        o = [b for b in zieh if b["opex"]]
        k = [b for b in zieh if not b["opex"]]
        if len(o) < 50 or len(k) < 50:
            continue
        diffs.append(quote(o) - quote(k))
    if len(diffs) < 100:
        return float("nan"), float("nan"), float("nan")
    diffs.sort()
    nicht_positiv = sum(1 for d in diffs if d <= 0)
    p = (nicht_positiv + 1) / (len(diffs) + 1)
    return (diffs[int(0.025 * (len(diffs) - 1))],
            diffs[int(0.975 * (len(diffs) - 1))], p)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json")
    ap.add_argument("--ticker", nargs="+")
    a = ap.parse_args()

    opex = {d["date"].isoformat() if hasattr(d["date"], "isoformat") else str(d["date"])
            for d in get_all_opex_dates(START_JAHR, date.today().year)}

    ticker = a.ticker or [t for t in all_option_tickers()
                          if "." not in t and "-" not in t and "^" not in t]
    print("Pinning am Verfallsfreitag — %d Ticker, ab %d\n"
          % (len(ticker), START_JAHR))

    alle, je_ticker = [], []
    for t in ticker:
        try:
            b = freitags_beobachtungen(t, opex)
        except (KursreiheFehlt, Exception):
            continue
        o = [x for x in b if x["opex"]]
        k = [x for x in b if not x["opex"]]
        if len(o) < 24 or len(k) < 100:              # zwei Jahre Verfallstage
            continue
        alle.extend(b)
        je_ticker.append({"ticker": t, "n_opex": len(o), "n_kontrolle": len(k),
                          "quote_opex": round(quote(o), 4),
                          "quote_kontrolle": round(quote(k), 4)})

    if not alle:
        print("Keine auswertbaren Reihen.")
        return 1

    o = [b for b in alle if b["opex"]]
    k = [b for b in alle if not b["opex"]]
    q_o, q_k = quote(o), quote(k)
    lo, hi, p = bootstrap_differenz(alle)
    monate = len({b["monat"] for b in alle})

    print("=" * 74)
    print("VORAB FESTGELEGTE HYPOTHESE")
    print("  H1: Schlusskurse liegen an monatlichen Verfallsfreitagen häufiger")
    print("      innerhalb von %.3f $ eines Strikes als an übrigen Freitagen."
          % TOLERANZ)
    print("=" * 74)
    print("  Verfallsfreitage : %6d Beobachtungen, %5.2f %% am Strike"
          % (len(o), q_o * 100))
    print("  übrige Freitage  : %6d Beobachtungen, %5.2f %% am Strike"
          % (len(k), q_k * 100))
    print("  Differenz        : %+.2f Prozentpunkte" % ((q_o - q_k) * 100))
    print()
    print("  %d Ticker, %d Kalendermonate — und die MONATE sind die Stichprobe,"
          % (len(je_ticker), monate))
    print("  nicht die %d Ticker-Tage." % len(alle))
    if math.isnan(p):
        print("  Bootstrap nicht möglich (zu wenige Monate).")
    else:
        print("  95-%%-Intervall der Differenz: %+.2f bis %+.2f pp"
              % (lo * 100, hi * 100))
        print("  p = %.4f  (einseitig, Bootstrap über Monate, Plus-eins)" % p)
        print()
        if p < 0.05 and lo > 0:
            print("  H1 GESTÜTZT.")
        else:
            print("  H1 NICHT gestützt — die Differenz trägt die Richtung nicht.")

    # Teilperioden: hat der Monats-OPEX seine Sonderstellung verloren?
    # VORAB festgelegte Grenze 2010, das Jahr der breiten Einführung
    # woechentlicher Verfaelle. Keine nachträglich gesuchte Trennstelle.
    print()
    print("Teilperioden (Grenze 2010 = Verbreitung wöchentlicher Verfälle,")
    print("vorab gesetzt, nicht nachträglich gesucht):")
    perioden = []
    for name, lo_j, hi_j in (("bis 2009", START_JAHR, 2009),
                             ("ab 2010", 2010, date.today().year)):
        teil = [b for b in alle if lo_j <= int(b["tag"][:4]) <= hi_j]
        to = [b for b in teil if b["opex"]]
        tk = [b for b in teil if not b["opex"]]
        if len(to) < 100 or len(tk) < 300:
            continue
        d = quote(to) - quote(tk)
        _, _, tp = bootstrap_differenz(teil)
        perioden.append({"periode": name, "n_opex": len(to),
                         "quote_opex": round(quote(to), 4),
                         "quote_kontrolle": round(quote(tk), 4),
                         "differenz_pp": round(d * 100, 3),
                         "p": None if math.isnan(tp) else round(tp, 4)})
        print("  %-10s OPEX %5.2f %%  Kontrolle %5.2f %%  Differenz %+.2f pp"
              "  p = %s"
              % (name, quote(to) * 100, quote(tk) * 100, d * 100,
                 "n/a" if math.isnan(tp) else "%.4f" % tp))

    if a.json:
        ziel = pathlib.Path(a.json)
        ziel.parent.mkdir(parents=True, exist_ok=True)
        ziel.write_text(json.dumps({
            "toleranz_usd": TOLERANZ, "start_jahr": START_JAHR,
            "bootstrap": BOOTSTRAP,
            "n_ticker": len(je_ticker), "n_monate": monate,
            "gesamt": {
                "n_opex": len(o), "n_kontrolle": len(k),
                "quote_opex": round(q_o, 4), "quote_kontrolle": round(q_k, 4),
                "differenz_pp": round((q_o - q_k) * 100, 3),
                "ci95_pp": [None if math.isnan(lo) else round(lo * 100, 3),
                            None if math.isnan(hi) else round(hi * 100, 3)],
                "p": None if math.isnan(p) else round(p, 4),
            },
            "perioden": perioden,
            "je_ticker": sorted(je_ticker,
                                key=lambda x: -(x["quote_opex"] - x["quote_kontrolle"])),
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        print("\nJSON: %s" % ziel)
    return 0


if __name__ == "__main__":
    sys.exit(main())
