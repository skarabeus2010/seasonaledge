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

WARUM ÜBER VERFALLSMONATE UND NICHT ÜBER TICKER-TAGE: 163 Ticker am selben
Freitag sind nicht 163 unabhängige Beobachtungen. Sie teilen denselben
Markttag, dieselbe Nachrichtenlage, dieselbe Vola. Wer über Ticker-Tage zieht,
behauptet eine Stichprobe, die es nicht gibt, und bekommt ein absurd enges
Intervall.

DER p-WERT KOMMT AUS EINER PERMUTATION, NICHT AUS DEM BOOTSTRAP — und der
Unterschied ist keine Feinheit. Ein Bootstrap zieht die Monate MIT ihren
Etiketten neu; seine Verteilung liegt um den gemessenen Effekt, nicht um null.
Der Anteil nicht-positiver Ziehungen misst damit die Streuung der Schätzung,
nicht die Wahrscheinlichkeit eines solchen Ergebnisses, WENN es keinen Effekt
gibt. Eine erste Fassung dieser Studie hat genau diesen Anteil als p-Wert
veröffentlicht; das war falsch und ist korrigiert.

Der Test lost jetzt je Monat einen Freitag als Pseudo-Verfallstag aus. Das ist
die Nullhypothese in Reinform: der Verfallsfreitag ist kein besonderer
Freitag. Das Bootstrap-Intervall bleibt daneben stehen — als Intervall für die
Schätzung, wofür es gültig ist.
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


def _je_monat_und_tag(beob: list[dict]):
    """{Monat: [(Tag, n, gepinnt, ist_opex), …]} — die Grundlage beider Tests.

    Aggregiert wird auf (Monat, Tag), weil ALLE Ticker denselben Verfallstag
    teilen. Das macht die Permutation unten nicht nur schnell, sondern richtig:
    sie muss ganze TAGE umetikettieren, nicht einzelne Ticker-Beobachtungen.
    """
    roh = defaultdict(lambda: defaultdict(lambda: [0, 0, False]))
    for b in beob:
        z = roh[b["monat"]][b["tag"]]
        z[0] += 1
        z[1] += 1 if b["gepinnt"] else 0
        z[2] = z[2] or b["opex"]
    return {m: [(t, v[0], v[1], v[2]) for t, v in sorted(tage.items())]
            for m, tage in roh.items()}


def _diff_aus_wahl(monate: list, wahl: list) -> float | None:
    """Quotendifferenz, wenn je Monat `wahl[i]` der Verfallstag wäre."""
    n_o = k_o = n_k = k_k = 0
    for tage, idx in zip(monate, wahl):
        for j, (_t, n, k, _o) in enumerate(tage):
            if j == idx:
                n_o += n; k_o += k
            else:
                n_k += n; k_k += k
    if n_o < 50 or n_k < 50:
        return None
    return k_o / n_o - k_k / n_k


def permutationstest(beob: list[dict]) -> tuple[float, float, float, int]:
    """Konfidenzintervall UND ein echter p-Wert unter der Nullhypothese.

    WARUM DER ALTE p-WERT FALSCH WAR — das ist der Kern dieser Funktion:

        Der erste Entwurf zog Monate MIT ihren Etiketten neu und zählte, wie
        oft die gebootstrappte Differenz nicht positiv war. Damit liegt die
        Verteilung um den GEMESSENEN Effekt herum, nicht um null. Der Anteil
        misst die Streuung der Schätzung, nicht die Wahrscheinlichkeit eines
        solchen Ergebnisses, WENN es keinen Effekt gibt. Eine Plus-eins-
        Korrektur macht daraus keinen Nullverteilungstest. Von Codex gefunden;
        die so veröffentlichten p-Werte 0,0075 / 0,0015 waren keine p-Werte.

    DIE NULLHYPOTHESE, sauber formuliert: der Verfallsfreitag ist kein
    besonderer Freitag. Dann ist es zufällig, WELCHER Freitag eines Monats das
    Etikett trägt. Also wird je Monat ein Freitag ausgelost und so behandelt,
    als wäre er der Verfallstag.

    Das erhält alles, was erhalten bleiben muss: die Monatsstruktur, die Zahl
    der Verfallstage, die Zusammensetzung der Ticker, das Kursniveau der
    Epoche. Randomisiert wird ausschliesslich die eine Sache, um die es geht.

    Nur Monate mit MINDESTENS ZWEI Freitagen und einem echten Verfallstag
    gehen ein — in einem Monat mit nur einem Freitag gibt es nichts zu
    vertauschen, und ohne echten Verfallstag (er kann auf einen Feiertag
    fallen und vorverlegt werden) gibt es nichts zu vergleichen.

    Rückgabe: (ci_lo, ci_hi, p, n_monate).
    """
    je_monat = _je_monat_und_tag(beob)
    monate, wahl = [], []
    for m in sorted(je_monat):
        tage = je_monat[m]
        opex_idx = [j for j, t in enumerate(tage) if t[3]]
        if len(tage) < 2 or len(opex_idx) != 1:
            continue
        monate.append(tage)
        wahl.append(opex_idx[0])
    if len(monate) < 30:
        return float("nan"), float("nan"), float("nan"), len(monate)

    ist = _diff_aus_wahl(monate, wahl)
    if ist is None:
        return float("nan"), float("nan"), float("nan"), len(monate)

    rnd = random.Random(20260922)

    # ── p-Wert: Permutation unter H0 ───────────────────────────────────────
    # Gelost wird UNIFORM ueber alle Freitage des Monats, den echten
    # eingeschlossen — er ist unter H0 eine Moeglichkeit wie jede andere.
    extremer = 0
    for _ in range(BOOTSTRAP):
        zufall = [rnd.randrange(len(t)) for t in monate]
        d = _diff_aus_wahl(monate, zufall)
        if d is not None and d >= ist:
            extremer += 1
    p = (extremer + 1) / (BOOTSTRAP + 1)

    # ── Konfidenzintervall: Bootstrap ueber Monate ─────────────────────────
    # Das bleibt, was es war — ein Intervall fuer die Schaetzung, und als
    # solches gueltig. Es ist NICHT die Grundlage des p-Werts.
    diffs = []
    for _ in range(BOOTSTRAP):
        idx = [rnd.randrange(len(monate)) for _ in range(len(monate))]
        d = _diff_aus_wahl([monate[i] for i in idx], [wahl[i] for i in idx])
        if d is not None:
            diffs.append(d)
    if len(diffs) < 100:
        return float("nan"), float("nan"), p, len(monate)
    diffs.sort()
    return (diffs[int(0.025 * (len(diffs) - 1))],
            diffs[int(0.975 * (len(diffs) - 1))], p, len(monate))


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
    lo, hi, p, n_perm = permutationstest(alle)
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
        print("  p = %.4f  (einseitig, Permutation über %d Monate, Plus-eins)"
              % (p, n_perm))
        print("  Der Test lost je Monat einen Freitag als Pseudo-Verfallstag")
        print("  aus. Das ist die Nullhypothese: der Verfallstag ist kein")
        print("  besonderer Freitag.")
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
        _, _, tp, _ = permutationstest(teil)
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
                "p_methode": "Permutation: je Monat ein ausgeloster Freitag",
                "n_monate_permutation": n_perm,
            },
            "perioden": perioden,
            "je_ticker": sorted(je_ticker,
                                key=lambda x: -(x["quote_opex"] - x["quote_kontrolle"])),
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        print("\nJSON: %s" % ziel)
    return 0


if __name__ == "__main__":
    sys.exit(main())
