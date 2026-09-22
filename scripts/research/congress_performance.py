#!/usr/bin/env python3
"""
congress_performance.py — Taugen die Congress-Trades etwas, wenn man sie liest?

    py -3.14 scripts/research/congress_performance.py --trades <congress_trades.json>

DIE FRAGE IST NICHT, was der Abgeordnete verdient hat. Sie lautet: Hätte es
etwas gebracht, ihm zu FOLGEN? Das ist etwas anderes, weil die Meldefrist nach
dem STOCK Act 30 bis 45 Tage beträgt. Wer am Transaktionstag einsteigt, rechnet
mit Wissen, das er damals nicht hatte. Einstieg ist deshalb der erste
Handelstag NACH der Offenlegung.

Gemessen wird marktbereinigt gegen SPY: eine Aktie, die in einem steigenden
Markt steigt, hat nichts gezeigt.

DIE VORAB FESTGELEGTE HYPOTHESE:

    H1: Ein Aktienkauf, gekauft am ersten Handelstag nach der Offenlegung und
        20 Handelstage gehalten, liefert eine positive marktbereinigte Rendite.

⚠ ZUM STAND DER DATEN — bitte vor jeder Interpretation lesen:

    Der Tracker läuft erst seit 09-2026, und das Roster umfasst neun Personen.
    Nach Filterung auf echte AKTIENkäufe (keine Optionen) und Clustern je
    Politiker/Ticker/Filing bleiben derzeit rund 36 Ereignisse, davon etwa
    vier Fünftel von einer einzigen Person.

    Das ist keine Stichprobe, das ist eine Anekdote. Das Skript rechnet
    trotzdem — aber es gibt kein Urteil aus, solange die Mindestzahl nicht
    erreicht ist, und es sagt selbst, was fehlt. Ein p-Wert auf 36 Ereignissen
    aus zwei Quellen wäre genau die Sorte Zahl, die diese Woche schon die
    Intermarket-Matrix gekostet hat.

    Was es brauchbar machen würde: ein Backfill des House-Clerk-Index über
    mehrere Jahre (der Index liegt weiter zurück als unsere Auswertung) und ein
    breiteres Roster in scripts/congress_roster.json.

WARUM DER BOOTSTRAP NACH POLITIKER CLUSTERT: Wenn eine Person 29 der 36
Ereignisse liefert, sind das nicht 36 unabhängige Beobachtungen. Sie teilen
einen Entscheider, einen Berater, eine Strategie. Gezogen werden deshalb ganze
POLITIKER mit allen ihren Ereignissen.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import random
import statistics
import sys
from collections import defaultdict

_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))

from shared.data import KursreiheFehlt, lade_closes                  # noqa: E402
from shared.realized_vol import iso_tag                              # noqa: E402

HALTEDAUER = 20              # Handelstage
MIN_EREIGNISSE = 100         # darunter kein Urteil — siehe Docstring
MIN_POLITIKER = 5            # und nicht aus zu wenigen Quellen
BOOTSTRAP = 2000
MARKT = "SPY"


def reihe(ticker: str) -> tuple[list[str], list[float]] | None:
    try:
        d, c = lade_closes(ticker)
    except (KursreiheFehlt, Exception):
        return None
    tage, kurse = [], []
    for x, y in zip(d, c):
        if y is None or not math.isfinite(float(y)) or float(y) <= 0:
            continue
        tage.append(iso_tag(x))
        kurse.append(float(y))
    return (tage, kurse) if len(tage) > HALTEDAUER + 5 else None


def rendite_ab(tage: list[str], kurse: list[float], ab: str) -> float | None:
    """Rendite über HALTEDAUER, Einstieg am ersten Handelstag NACH `ab`."""
    i = next((j for j, t in enumerate(tage) if t > ab), None)
    if i is None or i + HALTEDAUER >= len(tage):
        return None
    return math.log(kurse[i + HALTEDAUER] / kurse[i])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trades", required=True,
                    help="congress_trades.json (live gezogen, die lokale ist "
                         "gitignored und meist veraltet)")
    ap.add_argument("--json")
    a = ap.parse_args()

    daten = json.loads(pathlib.Path(a.trades).read_text(encoding="utf-8"))
    trades = daten.get("trades", [])

    # Nur echte Aktienkäufe. Optionen fallen raus: ein Optionskauf über
    # 250.000 $ Nominal ist eine völlig andere Positionsgrösse als ein
    # Aktienkauf desselben Betrags, und wir kennen weder Strike noch Laufzeit.
    kaeufe = [t for t in trades
              if t.get("is_buy") and not t.get("is_option") and t.get("ticker")]

    # Clustern: mehrere Zeilen desselben Politikers zum selben Ticker im selben
    # Filing sind EIN Ereignis, keine drei.
    gruppen = {}
    for t in kaeufe:
        gruppen.setdefault((t["politician"], t["ticker"], t["filing_date"]), t)
    ereignisse = list(gruppen.values())

    markt = reihe(MARKT)
    if markt is None:
        print("Marktreihe %s fehlt." % MARKT)
        return 1

    ergebnisse = []
    ohne_kurs = []
    for e in ereignisse:
        r = reihe(e["ticker"])
        if r is None:
            ohne_kurs.append(e["ticker"])
            continue
        r_titel = rendite_ab(r[0], r[1], e["filing_date"])
        r_markt = rendite_ab(markt[0], markt[1], e["filing_date"])
        if r_titel is None or r_markt is None:
            continue
        ergebnisse.append({
            "politiker": e["politician"], "ticker": e["ticker"],
            "tx_date": e.get("tx_date"), "filing_date": e["filing_date"],
            "rendite_pct": round((math.exp(r_titel) - 1) * 100, 3),
            "markt_pct": round((math.exp(r_markt) - 1) * 100, 3),
            "ueber_markt_pp": round((math.exp(r_titel) - math.exp(r_markt)) * 100, 3),
        })

    print("Congress-Trades: bringt es etwas, nach der OFFENLEGUNG zu kaufen?\n")
    print("  %d Trades insgesamt" % len(trades))
    print("  %d Aktienkäufe (Optionen ausgeschlossen)" % len(kaeufe))
    print("  %d Ereignisse nach Clustern je Politiker/Ticker/Filing" % len(ereignisse))
    print("  %d davon auswertbar (Kursreihe + %d Handelstage vorhanden)"
          % (len(ergebnisse), HALTEDAUER))
    if ohne_kurs:
        print("  ohne Kursreihe: %s" % ", ".join(sorted(set(ohne_kurs))[:12]))
    if not ergebnisse:
        print("\nNichts auswertbar.")
        return 1

    je_politiker = defaultdict(list)
    for r in ergebnisse:
        je_politiker[r["politiker"]].append(r)
    print()
    print("  Verteilung auf Personen:")
    for p, rs in sorted(je_politiker.items(), key=lambda kv: -len(kv[1])):
        print("    %-24s %3d Ereignisse, Median %+6.2f pp über Markt"
              % (p, len(rs), statistics.median(x["ueber_markt_pp"] for x in rs)))

    ueber = [r["ueber_markt_pp"] for r in ergebnisse]
    mittel, median = statistics.fmean(ueber), statistics.median(ueber)
    positiv = sum(1 for x in ueber if x > 0) / len(ueber)

    print()
    print("=" * 74)
    print("ERGEBNIS")
    print("=" * 74)
    print("  marktbereinigt über %d Handelstage: Mittel %+.2f pp, Median %+.2f pp"
          % (HALTEDAUER, mittel, median))
    print("  positiv in %.0f %% der Fälle" % (positiv * 100))

    reicht = (len(ergebnisse) >= MIN_EREIGNISSE
              and len(je_politiker) >= MIN_POLITIKER)
    ci = [None, None]
    if reicht:
        # Cluster-Bootstrap: ganze Politiker ziehen, nicht einzelne Ereignisse.
        rnd = random.Random(20260922)
        namen = list(je_politiker)
        werte = []
        for _ in range(BOOTSTRAP):
            zieh = [x["ueber_markt_pp"] for _ in range(len(namen))
                    for x in je_politiker[namen[rnd.randrange(len(namen))]]]
            if zieh:
                werte.append(statistics.fmean(zieh))
        werte.sort()
        ci = [round(werte[int(0.025 * (len(werte) - 1))], 3),
              round(werte[int(0.975 * (len(werte) - 1))], 3)]
        print("  95-%%-Intervall (Bootstrap über Politiker): %+.2f bis %+.2f pp"
              % tuple(ci))
        print()
        print("  H1 %s" % ("GESTÜTZT." if ci[0] > 0 else "NICHT gestützt."))
    else:
        print()
        print("  KEIN URTEIL. Die Stichprobe reicht nicht:")
        print("    Ereignisse %d (nötig %d) · Personen %d (nötig %d)"
              % (len(ergebnisse), MIN_EREIGNISSE, len(je_politiker), MIN_POLITIKER))
        print("  Die Zahlen oben sind BESCHREIBUNG einer Handvoll Fälle, kein")
        print("  Ergebnis. Ein p-Wert darauf wäre eine Behauptung über")
        print("  Genauigkeit, die diese Daten nicht hergeben.")
        print()
        print("  Was es brauchbar machen würde:")
        print("    · Backfill des House-Clerk-Index über mehrere Jahre")
        print("      (der Index reicht weiter zurück als unsere Auswertung)")
        print("    · breiteres Roster in scripts/congress_roster.json")

    if a.json:
        ziel = pathlib.Path(a.json)
        ziel.parent.mkdir(parents=True, exist_ok=True)
        ziel.write_text(json.dumps({
            "haltedauer_ht": HALTEDAUER, "markt": MARKT,
            "min_ereignisse": MIN_EREIGNISSE, "min_politiker": MIN_POLITIKER,
            "n_trades": len(trades), "n_kaeufe": len(kaeufe),
            "n_ereignisse": len(ereignisse), "n_auswertbar": len(ergebnisse),
            "n_politiker": len(je_politiker),
            "urteil_moeglich": bool(reicht),
            "mittel_pp": round(mittel, 3), "median_pp": round(median, 3),
            "positiv_anteil": round(positiv, 4),
            "ci95_pp": ci,
            "ereignisse": sorted(ergebnisse, key=lambda r: r["filing_date"]),
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        print("\nJSON: %s" % ziel)
    return 0


if __name__ == "__main__":
    sys.exit(main())
