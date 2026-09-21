#!/usr/bin/env python3
"""
bond_lead_lag.py — Laufen Anleihe-Bewegungen dem Aktienmarkt voraus?

    py -3.14 scripts/research/bond_lead_lag.py
    py -3.14 scripts/research/bond_lead_lag.py --json <datei>

Dieselbe Methodik wie scripts/research/btc_lead_lag.py, deren Funktionen hier
importiert statt nachgebaut werden — zwei Kopien derselben Ereignisrechnung
wuerden auseinanderlaufen, und die Vergleichbarkeit beider Studien ist der
ganze Zweck.

WAS HIER GEMESSEN WIRD, und was nicht: TLT und HYG sind ETF-KURSE, keine
Renditen. Fuer die Frage "laufen Renditeaenderungen dem S&P voraus" ist das
eine Naeherung zweiter Guete — die Kurse enthalten Duration-Konvexitaet,
Kupon-Drift und Rebalancing des zugrundeliegenden Index. Die echten
Rendite-Indizes (^TNX, ^TYX, ^FVX, ^IRX) stehen nicht in der Datenbank.

RICHTUNGEN, die man nicht verwechseln darf:
  TLT faellt  = lange Renditen STEIGEN  (Zinsschock nach oben)
  TLT steigt  = lange Renditen fallen   (Flucht in Sicherheit oder Zinssenkung)
  HYG faellt  = Kreditaufschlaege weiten sich (Risikoabbau)
  HYG steigt  = Kreditaufschlaege gehen zurueck (Risikoappetit)
HYG ist damit weniger ein Zins- als ein Risikoappetit-Signal, und genau
deshalb interessant: es ist der naechste Verwandte des Aktienmarkts unter den
Anleihen.

SCHWELLEN NACH PERZENTIL, nicht in Prozent. Gemessen am 2026-09-21 ist eine
10-Tage-Bewegung im Median bei Bitcoin 5,58 %, bei TLT 1,64 % und bei HYG
0,78 %. Feste Prozentschwellen wuerden also bei TLT und HYG fast nie und bei
Bitcoin staendig ausloesen — verglichen wuerde Ungleiches. Ueber gleiche
PERZENTILE ist dagegen "gleich selten" vergleichbar, und die Ergebnisse stehen
neben denen der Krypto-Studie.

Nebenbefund aus dieser Kalibrierung, der die Krypto-Studie erklaert: die viel
zitierte 5-%-Schwelle bei Bitcoin ist der MEDIAN, also die normalste Bewegung
ueberhaupt. Dass dort nichts zu finden war, ist damit kein Widerspruch.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import pathlib
import statistics
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))

# Die Krypto-Studie als Modul laden: identische Ereignis-, Pfad- und
# Bootstrap-Rechnung, ohne sie zu kopieren.
_spec = importlib.util.spec_from_file_location(
    "btc_lead_lag", str(pathlib.Path(__file__).with_name("btc_lead_lag.py")))
BLL = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(BLL)

from shared.data import lade_closes                                  # noqa: E402

SIGNALE = ("TLT", "HYG")
ETFS = BLL.ETFS
L = BLL.L

# Dieselben Seltenheitsstufen fuer jedes Signal.
PERZENTILE = (0.75, 0.90, 0.95, 0.99)


def bewegungen(reihe: list[float]) -> list[float]:
    """Absolute 10-Tage-Bewegungen in Prozent, fuer die Schwellenkalibrierung."""
    lr = BLL.log_returns(reihe)
    out = []
    for i in range(L, len(lr)):
        f = lr[i - L:i]
        if not any(x is None for x in f):
            out.append(abs(math.exp(sum(f)) - 1) * 100)
    return sorted(out)


def schwellen(reihe: list[float]) -> list[tuple[str, float]]:
    b = bewegungen(reihe)
    out = []
    for q in PERZENTILE:
        wert = b[int(q * (len(b) - 1))] / 100.0
        out.append(("ab %.1f %% (%d. Pz)" % (wert * 100, q * 100), wert))
    return out


def eine_reihe(signal: str) -> dict:
    print()
    print("#" * 78)
    print("# %s   %s" % (signal, "lange Laufzeiten (20+ Jahre)" if signal == "TLT"
                         else "High-Yield-Unternehmensanleihen"))
    print("#" * 78)

    reihen = {}
    for t in (signal,) + ETFS:
        d, c = lade_closes(t)
        reihen[t] = dict(zip(d, [float(x) for x in c]))
    tage = sorted(set.intersection(*[set(v) for v in reihen.values()]))
    sig = [reihen[signal][d] for d in tage]
    kum = BLL.kumulierte(sig, L)
    print("Gemeinsame Handelstage: %d  (%s .. %s)" % (len(tage), tage[0], tage[-1]))

    bas = BLL.basisrate(tage, reihen)
    print()
    print("BASISRATE SPY (ohne jedes Signal): 1 Wo %+.2f %%  2 Wo %+.2f %%  "
          "3 Wo %+.2f %%  4 Wo %+.2f %%  (Treffer 3 Wo %.1f %%)"
          % (bas["SPY"][5]["mittel_pct"], bas["SPY"][10]["mittel_pct"],
             bas["SPY"][15]["mittel_pct"], bas["SPY"][20]["mittel_pct"],
             bas["SPY"][15]["anteil_positiv_pct"]))

    sw = schwellen(sig)
    erg = {"signal": signal, "von": tage[0], "bis": tage[-1],
           "handelstage": len(tage), "basisrate": bas,
           "schwellen": [{"name": n, "wert_pct": round(w * 100, 2)} for n, w in sw],
           "richtungen": {}}

    for richtung, was in (("auf", "KURS STEIGT" + (" (Renditen fallen)" if signal == "TLT"
                                                   else " (Risikoappetit)")),
                          ("ab", "KURS FAELLT" + (" (Renditen steigen)" if signal == "TLT"
                                                  else " (Risikoabbau)"))):
        print()
        print("  %s %s" % (signal, was))
        print("  %-22s %4s | %9s %9s %9s %9s   Treffer 3 Wo"
              % ("Schwelle", "n", "1 Wo", "2 Wo", "3 Wo", "4 Wo"))
        print("  %-22s %4d | %9.2f %9.2f %9.2f %9.2f   %.1f %%   <- ohne Signal"
              % ("Marktdurchschnitt", 0, bas["SPY"][5]["mittel_pct"],
                 bas["SPY"][10]["mittel_pct"], bas["SPY"][15]["mittel_pct"],
                 bas["SPY"][20]["mittel_pct"], bas["SPY"][15]["anteil_positiv_pct"]))
        zeilen = []
        for name, wert in sw:
            treffer, letztes = [], -10 ** 9
            for i in range(BLL.BASIS + L, len(tage)):
                k = kum[i]
                if k is None:
                    continue
                bew = math.exp(k) - 1.0
                passt = (bew >= wert) if richtung == "auf" else (bew <= -wert)
                if passt and i - letztes >= BLL.ABSTAND:
                    treffer.append(i)
                    letztes = i
            er = [reihens for reihens in [reihen["SPY"][d] for d in tage]]
            pf = [p for p in (BLL.pfad(er, i) for i in treffer) if p]
            if len(pf) < 5:
                print("  %-22s %4d | zu wenige Ereignisse" % (name, len(treffer)))
                zeilen.append({"schwelle": name, "n": len(treffer)})
                continue
            mp = BLL.mittelpfad(pf)
            null = BLL.nullband(er, treffer, len(tage))
            z = {"schwelle": name, "n": len(pf)}
            aus = []
            for k in (5, 10, 15, 20):
                ist = mp[BLL.VOR + k]
                vert = sorted(x[BLL.VOR + k] for x in null)
                p = (sum(1 for x in vert if x >= ist) if ist >= 0
                     else sum(1 for x in vert if x <= ist)) / max(1, len(vert))
                einzel = [q[BLL.VOR + k] for q in pf]
                z["t%d" % k] = {"mittel_pct": round(ist, 3), "p_wert": round(p, 4),
                                "treffer_pct": round(
                                    sum(1 for x in einzel if x > 0) / len(einzel) * 100, 1)}
                aus.append("%+9.2f" % ist)
            print("  %-22s %4d | %s   %.1f %%"
                  % (name, len(pf), " ".join(aus), z["t15"]["treffer_pct"]))
            print("  %-22s %4s | %s"
                  % ("", "p", " ".join("%9.3f" % z["t%d" % k]["p_wert"]
                                       for k in (5, 10, 15, 20))))
            zeilen.append(z)
        erg["richtungen"][richtung] = zeilen
    return erg


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json")
    a = ap.parse_args()
    print("Schwellen nach PERZENTIL, nicht in Prozent: eine 10-Tage-Bewegung ist")
    print("im Median bei TLT 1,64 %% und bei HYG 0,78 %% — feste Prozentschwellen")
    print("wuerden hier fast nie ausloesen und bei Bitcoin staendig.")
    alles = {s: eine_reihe(s) for s in SIGNALE}
    if a.json:
        pathlib.Path(a.json).write_text(
            json.dumps(alles, ensure_ascii=False, indent=2), encoding="utf-8")
        print()
        print("JSON geschrieben: %s" % a.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
