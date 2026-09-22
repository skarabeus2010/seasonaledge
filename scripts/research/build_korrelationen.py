#!/usr/bin/env python3
"""
build_korrelationen.py — rollierende Korrelationen für /korrelationen.

    py -3.14 scripts/research/build_korrelationen.py --json landing/data/korrelationen.json

WAS DIE SEITE ZEIGT: Für ein Paar aus dem festen Universum die rollierende
Korrelation der Tagesbewegungen über die gemeinsame Historie, dazu der
aktuelle Wert, sein Perzentil in der eigenen Historie und das Maximum des
gemeinsamen Zeitraums.

WAS SIE BEWUSST NICHT ZEIGT — und das ist nach dem Codex-Review die wichtigste
Festlegung: keinen p-Wert, keine Signifikanzklasse, kein „Rekord seit X
Jahren" als Auszeichnung, keine Aussage über Stabilität oder Ursache. Wer aus
20 Reihen zwei aussucht und dann „höchster Wert seit 35 Jahren" liest,
verwechselt eine Datenbeschreibung mit einem Ereignis. Der Höchstwert einer
rollierenden Reihe ist ein Extremwert aus Hunderten überlappender Fenster — er
existiert immer irgendwo.

DREI FESTLEGUNGEN, die man kennen muss, bevor man die Zahlen benutzt:

1. GERECHNET WIRD AUF BEWEGUNGEN, NICHT AUF NIVEAUS. Zwei steigende Kurse
   korrelieren fast immer hoch, ohne dass das etwas bedeutet — das ist die
   klassische Scheinkorrelation trendbehafteter Reihen. Preisreihen gehen als
   Log-Renditen ein.

2. RENDITEN SIND KEINE KURSE. ^TNX & Co. sind Zinssätze in Prozent. Eine
   Log-Rendite darauf wäre sinnlos: die Reihe kann null werden, und die
   prozentuale Änderung einer Prozentzahl ist keine ökonomisch sinnvolle
   Grösse. Diese Reihen gehen als TÄGLICHE ÄNDERUNG IN BASISPUNKTEN ein.
   Wichtig fürs Lesen: eine steigende Rendite heisst fallende Anleihekurse.

3. ES WIRD NICHT VORWÄRTSGEFÜLLT. Krypto handelt an sieben Tagen, die NYSE
   nicht, und XETRA hat wieder andere Feiertage. Gerechnet wird auf der
   Schnittmenge der Handelstage, und die Renditen werden ERST DANACH über
   aufeinanderfolgende gemeinsame Termine gebildet. Wer stattdessen füllt,
   vergleicht einen Bitcoin-Sonntag mit einem Freitagsschluss.

ZWEI FENSTER, nicht eines: 63 Handelstage als Hauptansicht (rund drei Monate),
252 als langsamere Gegenprobe. Ein 63-Tage-Fenster allein ist zu verrauscht,
um daraus einen Höchstwert einzuordnen.

WAS AUSGELIEFERT WIRD — und warum nicht das Naheliegende: Ein erster Entwurf
rechnete alle 210 Paare vor und legte jeden rollierenden Punkt ab. Ergebnis:
52 MB. Das ist der falsche Zuschnitt, und zwar zweimal — die Datei wäre
unzumutbar, und sie legte zugleich fest, welche Paare überhaupt ansehbar sind.

Ausgeliefert werden deshalb die BEWEGUNGEN je Reihe, und die Korrelation
rechnet das Frontend. Das ist kleiner, und es lässt den Nutzer jedes Paar
wählen, ohne dass jemand vorher entscheiden muss, welche Kombination
interessant ist.

Die Bewegungen liegen auf einem GEMEINSAMEN Datumsraster (Vereinigung aller
Handelstage) mit null an den Tagen, an denen eine Reihe nicht handelte. Das
Frontend schneidet daraus paarweise die Tage heraus, an denen BEIDE Reihen
einen Wert haben. Die Ausrichtung passiert damit dort, wo das Paar feststeht —
vorher ginge es gar nicht.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import statistics
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))

from shared.data import KursreiheFehlt, lade_closes                  # noqa: E402
from shared.realized_vol import iso_tag                              # noqa: E402

FENSTER = (63, 252)
MIN_GEMEINSAM = 400          # weniger trägt keine rollierende Reihe

# Das eingefrorene Universum. Bewusst klein und vorab festgelegt: wer aus 370
# Tickern frei kombiniert, sucht sich Auffälligkeiten zusammen. Keine
# Einzelaktien, keine gehebelten Produkte, keine zweite fast identische
# ETF-Variante je Segment.
#
# `art` steuert die Rechnung: "preis" -> Log-Rendite, "rendite" -> Änderung in
# Basispunkten. Die Unterscheidung ist nicht kosmetisch (siehe Kopf).
UNIVERSUM = [
    ("SPY",      "S&P 500",           "Aktien",     "preis"),
    ("QQQ",      "Nasdaq 100",        "Aktien",     "preis"),
    ("IWM",      "Russell 2000",      "Aktien",     "preis"),
    ("EEM",      "Schwellenländer",   "Aktien",     "preis"),
    ("^GDAXI",   "DAX",               "Aktien",     "preis"),
    ("GLD",      "Gold",              "Rohstoffe",  "preis"),
    ("SLV",      "Silber",            "Rohstoffe",  "preis"),
    ("CL=F",     "Rohöl (WTI)",       "Rohstoffe",  "preis"),
    ("HG=F",     "Kupfer",            "Rohstoffe",  "preis"),
    ("NG=F",     "Erdgas",            "Rohstoffe",  "preis"),
    ("BTC-USD",  "Bitcoin",           "Krypto",     "preis"),
    ("ETH-USD",  "Ether",             "Krypto",     "preis"),
    ("^TNX",     "US 10J-Rendite",    "Zinsen",     "rendite"),
    ("^IRX",     "US 13W-Rendite",    "Zinsen",     "rendite"),
    ("TLT",      "Anleihen 20J+",     "Zinsen",     "preis"),
    ("HYG",      "High Yield",        "Zinsen",     "preis"),
    ("EURUSD=X", "EUR/USD",           "Währungen",  "preis"),
    ("USDJPY=X", "USD/JPY",           "Währungen",  "preis"),
    ("XLE",      "Energie",           "Sektoren",   "preis"),
    ("XLF",      "Finanzen",          "Sektoren",   "preis"),
    ("XLK",      "Technologie",       "Sektoren",   "preis"),
]


def lade(ticker: str) -> dict[str, float]:
    daten, closes = lade_closes(ticker)
    out = {}
    for d, c in zip(daten, closes):
        try:
            v = float(c)
        except (TypeError, ValueError):
            continue
        if math.isfinite(v):
            out[iso_tag(d)] = v
    return out


def bewegungen(tage: list[str], reihe: dict[str, float], art: str):
    """Tagesbewegungen ÜBER DIE GEMEINSAMEN TERMINE.

    Der Reihenfolge wegen: erst die Termine schneiden, DANN differenzieren.
    Andersherum entstünden Renditen über Lücken hinweg, die es im Schnitt gar
    nicht gibt.
    """
    out = []
    for i in range(1, len(tage)):
        a, b = reihe[tage[i - 1]], reihe[tage[i]]
        if art == "rendite":
            # Zinssatz in Prozent -> Änderung in Basispunkten
            out.append((b - a) * 100.0)
        else:
            if a <= 0 or b <= 0:
                out.append(None)
                continue
            out.append(math.log(b / a))
    return out


def korrelation(x: list[float], y: list[float]) -> float | None:
    paare = [(a, b) for a, b in zip(x, y)
             if a is not None and b is not None
             and math.isfinite(a) and math.isfinite(b)]
    if len(paare) < 10:
        return None
    xs = [p[0] for p in paare]
    ys = [p[1] for p in paare]
    try:
        return statistics.correlation(xs, ys)
    except statistics.StatisticsError:
        return None          # eine Seite ohne Streuung


def rollierend(x: list, y: list, tage: list[str], fenster: int):
    """[(Tag, Korrelation), …] — der Wert an Tag t nutzt die letzten `fenster`
    gemeinsamen Beobachtungen BIS EINSCHLIESSLICH t."""
    out = []
    for i in range(fenster, len(x) + 1):
        r = korrelation(x[i - fenster:i], y[i - fenster:i])
        if r is not None:
            out.append((tage[i], round(r, 4)))
    return out


def perzentil(werte: list[float], wert: float) -> float:
    if not werte:
        return float("nan")
    return sum(1 for w in werte if w <= wert) / len(werte) * 100


def _unbenutzt_paar_auswerten(a, b, reihen) -> dict | None:
    """NICHT MEHR IM EXPORT-PFAD — bleibt als Referenzrechnung stehen, gegen
    die sich die Frontend-Implementierung prüfen lässt. Genau diese Art
    Zwilling ist in diesem Projekt schon auseinandergelaufen, deshalb steht
    hier ausdrücklich, dass es einer ist."""
    (ta, na, _ga, arta) = a
    (tb, nb, _gb, artb) = b
    ra, rb = reihen.get(ta), reihen.get(tb)
    if not ra or not rb:
        return None

    tage = sorted(set(ra) & set(rb))
    if len(tage) < MIN_GEMEINSAM:
        return None

    bx = bewegungen(tage, ra, arta)
    by = bewegungen(tage, rb, artb)
    tage_r = tage[1:]                       # Bewegung i gehört zu tage[i]

    ergebnis = {"a": ta, "b": tb, "von": tage[0], "bis": tage[-1],
                "n_gemeinsam": len(tage), "fenster": {}}
    for f in FENSTER:
        reihe = rollierend(bx, by, [None] + tage_r, f)
        if len(reihe) < 30:
            continue
        werte = [r for _, r in reihe]
        ergebnis["fenster"][str(f)] = {
            "punkte": reihe,
            "aktuell": werte[-1],
            "perzentil": round(perzentil(werte, werte[-1]), 1),
            "max": max(werte), "min": min(werte),
            "median": round(statistics.median(werte), 4),
            "n": len(werte),
        }
    return ergebnis if ergebnis["fenster"] else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", required=True)
    ap.add_argument("--nur", nargs="+", help="nur diese Ticker")
    a = ap.parse_args()

    auswahl = [u for u in UNIVERSUM if not a.nur or u[0] in a.nur]
    print("Rollierende Korrelationen — %d Reihen, Fenster %s\n"
          % (len(auswahl), " und ".join(str(f) for f in FENSTER)))

    reihen, meta = {}, []
    for t, name, gruppe, art in auswahl:
        try:
            reihen[t] = lade(t)
        except (KursreiheFehlt, Exception) as e:
            print("  %-10s ENTFÄLLT (%s)" % (t, str(e)[:55]))
            continue
        tage = sorted(reihen[t])
        meta.append({"ticker": t, "name": name, "gruppe": gruppe, "art": art,
                     "von": tage[0], "bis": tage[-1], "n": len(tage)})
        print("  %-10s %-18s %-10s %s ab %s (%d Tage)"
              % (t, name, gruppe,
                 "Änderung in bp" if art == "rendite" else "Log-Rendite",
                 tage[0], len(tage)))

    vorhanden = [u for u in auswahl if u[0] in reihen]

    # ── Gemeinsames Datumsraster + Bewegungen je Reihe ────────────────────
    alle_tage = sorted({t for u in vorhanden for t in reihen[u[0]]})
    idx = {t: i for i, t in enumerate(alle_tage)}
    print()
    print("Gemeinsames Raster: %d Handelstage, %s bis %s"
          % (len(alle_tage), alle_tage[0], alle_tage[-1]))

    daten = []
    for t, name, gruppe, art in vorhanden:
        r = reihen[t]
        tage = sorted(r)
        bew = bewegungen(tage, r, art)          # bew[i] gehoert zu tage[i+1]
        werte = [None] * len(alle_tage)
        for i, v in enumerate(bew):
            if v is not None and math.isfinite(v):
                # Auf sechs Nachkommastellen: Log-Renditen brauchen nicht mehr,
                # und jede weitere Stelle kostet Dateigroesse ohne Nutzen.
                werte[idx[tage[i + 1]]] = round(v, 6)
        n_gueltig = sum(1 for v in werte if v is not None)
        daten.append({"ticker": t, "name": name, "gruppe": gruppe, "art": art,
                      "von": tage[0], "bis": tage[-1], "n": n_gueltig,
                      "bewegungen": werte})
        print("  %-10s %5d Bewegungen im Raster" % (t, n_gueltig))

    # Eine Stichprobe als Gegenprobe zur Referenzrechnung — damit ein Fehler in
    # der Frontend-Formel auffaellt, statt still falsche Zahlen zu zeigen.
    print()
    print("Referenzwerte zur Gegenprobe (Frontend muss dasselbe liefern):")
    stich = [("SPY", "QQQ"), ("^TNX", "TLT"), ("GLD", "SLV"), ("CL=F", "^TNX")]
    referenz = []
    for pa, pb in stich:
        ua = next((u for u in vorhanden if u[0] == pa), None)
        ub = next((u for u in vorhanden if u[0] == pb), None)
        if not ua or not ub:
            continue
        p = _unbenutzt_paar_auswerten(ua, ub, reihen)
        if not p:
            continue
        f = p["fenster"].get(str(FENSTER[0]))
        if not f:
            continue
        referenz.append({"a": pa, "b": pb, "fenster": FENSTER[0],
                         "aktuell": f["aktuell"], "perzentil": f["perzentil"],
                         "n": f["n"]})
        print("  %-9s %-9s  %+.4f   Perzentil %5.1f   (%d Punkte)"
              % (pa, pb, f["aktuell"], f["perzentil"], f["n"]))

    ziel = pathlib.Path(a.json)
    ziel.parent.mkdir(parents=True, exist_ok=True)
    ziel.write_text(json.dumps({
        "stand": max(d["bis"] for d in daten) if daten else None,
        "fenster": list(FENSTER),
        "min_gemeinsam": MIN_GEMEINSAM,
        "hinweis": ("Rein beschreibend. Keine Signifikanzaussage, keine "
                    "Prognose. Der Höchstwert einer rollierenden Reihe ist ein "
                    "Extremwert aus vielen überlappenden Fenstern."),
        "tage": alle_tage,
        "reihen": daten,
        "referenz": referenz,
    }, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("\nJSON: %s  (%.0f KB)" % (ziel, ziel.stat().st_size / 1024))
    return 0


if __name__ == "__main__":
    sys.exit(main())
