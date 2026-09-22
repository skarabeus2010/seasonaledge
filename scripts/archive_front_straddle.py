#!/usr/bin/env python3
"""
archive_front_straddle.py — täglich den Straddle des nächsten Verfalls festhalten.

    docker exec seasonalpha-app python3 scripts/archive_front_straddle.py

WOZU: Die Praktikerregel „Straddle des nächsten Verfalls, geteilt durch den Spot,
ergibt die erwartete Tagesspanne" lässt sich nur prüfen, wenn man den Straddle
über viele Tage hat. Wir rechnen die Options-Snapshots täglich, schreiben aber
nur IV, Skew und VRP weg — der Straddle war nie dabei. Dieses Skript schliesst
die Lücke, damit die Auswertung in einigen Monaten möglich ist. Es sammelt, es
bewertet nicht.

WARUM DER STRADDLE GERECHNET UND NICHT ABGELESEN WIRD — das muss man wissen,
bevor man die Zahlen benutzt:

    Der Snapshot des Anbieters enthält KEINE Preise. Geprüft am 22.09.2026:
    `day` ist ein leeres Objekt, `last_quote` und `last_trade` fehlen ganz.
    Vorhanden sind Greeks, implizite Vola, Open Interest und die
    Kontraktdetails.

    Der Straddle wird deshalb aus der ATM-IV per Black-Scholes zurückgerechnet.
    Das ist keine Notlösung und keine Schätzung: die IV IST die Umkehrung des
    Marktpreises, BS(IV) gibt ihn also wieder her — bis auf das Preismodell des
    Anbieters und die Frage, ob dessen IV aus Mid, Bid oder Last stammt.

    Was dadurch NICHT im Archiv steht: die Spanne zwischen Bid und Ask. Genau
    die ist bei 0DTE am Schluss weit, und wer die Regel später als Handelsidee
    liest, zahlt sie. Der rekonstruierte Straddle ist ein fairer Wert, kein
    handelbarer Preis. Das gehört an jede Auswertung dieser Daten dran.

WANN DAS SKRIPT LAUFEN MUSS — das ist keine Nebensache, sondern der Kern:

    VOR DER US-EROEFFNUNG (vor 13:30 UTC). Dann verfaellt der 0DTE-Kontrakt am
    Ende genau der Sitzung, die vorhergesagt werden soll: ein Tag, kein
    Horizont-Fehler. Zum Schlusskurs waere derselbe Kontrakt wertlos, und der
    naechste Verfall liegt je nach Wochentag ein bis drei Tage entfernt — dann
    bepreist der Straddle mehrere Tage und ueberschaetzt die Tagesspanne.

    Jeder Datensatz haelt in `vor_eroeffnung` fest, ob das beim Lauf zutraf.
    Eine spaetere Auswertung soll die uebrigen Tage ausschliessen, nicht
    mitrechnen.

ARCHIVIERT WIRD JE TICKER UND TAG: Spot, Verfallstag, Restlaufzeit, der Strike
am Geld, Call- und Put-IV dort, der daraus gerechnete Straddle, und die Anzahl
der Verfallstage, die überhaupt zur Wahl standen. Die letzte Zahl ist die
Qualitätskontrolle: steht nur ein Verfall zur Wahl, war die Kette dünn.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
from datetime import date

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from shared.atomic_json import write_json_atomic                     # noqa: E402
from shared.black_scholes import R, bs_price                         # noqa: E402

ZIEL = _ROOT / "landing" / "data" / "front_straddle_history.json"
TICKER = ["SPY", "QQQ", "IWM", "DIA"]
MAX_DTE = 7                  # weiter weg ist kein "nächster Verfall" mehr


def _skript(name: str):
    """compute_options_skew als Modul laden, um _spot/_chain/_byexp zu nutzen.

    Bewusst ueber importlib und nicht per Kopie der Funktionen: eine zweite
    Kette-Abfrage mit eigener Logik waere ein Zwilling, der driftet — genau die
    Fehlerklasse, die in diesem Projekt schon zwei Black-Scholes-Kopien mit
    verschiedenen Zinssaetzen hervorgebracht hat.
    """
    import importlib.util
    p = _ROOT / "scripts" / (name + ".py")
    spec = importlib.util.spec_from_file_location(name, str(p))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def front_straddle(mod, ticker: str, key: str) -> dict | None:
    spot = mod._spot(ticker, key)
    if not spot:
        return None
    by = mod._byexp(mod._chain(ticker, key, spot))
    if not by:
        return None

    # Naechster Verfall mit brauchbarer Kette auf BEIDEN Seiten. Ein Verfall,
    # der nur Calls hat, ergibt keinen Straddle.
    kandidaten = sorted(
        ((ex, e) for ex, e in by.items()
         if 0 <= e["dte"] <= MAX_DTE and e["call"] and e["put"]),
        key=lambda kv: kv[1]["dte"])
    if not kandidaten:
        return None
    ex, e = kandidaten[0]

    # Strike am Geld: der, dessen Abstand zum Spot am kleinsten ist und der auf
    # BEIDEN Seiten existiert.
    calls = {c[2]: c[1] for c in e["call"] if c[2]}
    puts = {p[2]: p[1] for p in e["put"] if p[2]}
    gemeinsam = [k for k in calls if k in puts]
    if not gemeinsam:
        return None
    k = min(gemeinsam, key=lambda x: abs(x - spot))
    iv_c, iv_p = calls[k], puts[k]
    if not iv_c or not iv_p:
        return None

    # T IN JAHREN — und hier haengt alles am Zeitpunkt des Laufs.
    #
    # Ein Kontrakt mit dte = 0 verfaellt HEUTE zum Schluss. Laeuft dieses
    # Skript VOR der Eroeffnung, liegt genau eine Sitzung dazwischen, und der
    # Straddle bepreist exakt den kommenden Handelstag — das ist der saubere
    # Fall fuer die Regel "Straddle durch Spot ergibt die Tagesspanne", ohne
    # jeden Horizont-Fehler. Laeuft es dagegen ZUM SCHLUSS, ist derselbe
    # Kontrakt wertlos und die Zahl Unsinn.
    #
    # dte = 0 wird deshalb als EIN Tag gerechnet, nicht als null und nicht als
    # halber. Das unterstellt den Lauf vor der Eroeffnung; `vor_eroeffnung`
    # haelt fest, ob das zum Zeitpunkt des Laufs plausibel war, damit eine
    # spaetere Auswertung die uebrigen Tage ausschliessen kann.
    from datetime import datetime, timezone
    jetzt = datetime.now(timezone.utc)
    vor_eroeffnung = (jetzt.hour * 60 + jetzt.minute) < 13 * 60 + 30   # NYSE-Open
    tage = max(e["dte"], 1)
    T = tage / 365.0

    call = bs_price(spot, k, T, iv_c, "call")
    put = bs_price(spot, k, T, iv_p, "put")
    straddle = call + put
    return {
        "spot": round(spot, 4), "exp": ex, "dte": e["dte"],
        "strike": k, "iv_call": iv_c, "iv_put": iv_p,
        "call": round(call, 4), "put": round(put, 4),
        "straddle": round(straddle, 4),
        "straddle_pct": round(straddle / spot * 100, 4),
        "t_tage": tage,
        "vor_eroeffnung": bool(vor_eroeffnung),
        "lauf_utc": jetzt.strftime("%H:%M"),
        "n_verfaelle": len(kandidaten),
        "r": R,
        "quelle": "aus Anbieter-IV per Black-Scholes zurueckgerechnet; "
                  "KEIN handelbarer Preis (keine Bid-Ask-Spanne im Snapshot)",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticker", nargs="+", default=TICKER)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    key = os.environ.get("MASSIVE_API_KEY") or os.environ.get("POLYGON_API_KEY", "")
    if not key:
        print("[straddle] MASSIVE_API_KEY fehlt — Abbruch.")
        return 1

    mod = _skript("compute_options_skew")
    heute = mod._last_session()
    print("[straddle] Session %s" % heute)

    hist = {}
    if ZIEL.exists():
        try:
            hist = json.loads(ZIEL.read_text(encoding="utf-8"))
        except Exception as e:
            print("[straddle] Bestand unlesbar (%s) — wird NICHT ueberschrieben."
                  % str(e)[:60])
            return 1

    neu = 0
    for t in a.ticker:
        try:
            d = front_straddle(mod, t, key)
        except Exception as e:
            print("  %-6s FEHLER %s" % (t, str(e)[:70]))
            continue
        if not d:
            print("  %-6s kein brauchbarer Front-Verfall" % t)
            continue
        d["date"] = heute
        reihe = hist.setdefault(t, [])
        # Dedup je Tag: ein zweiter Lauf am selben Tag ersetzt, haengt nicht an.
        reihe[:] = [p for p in reihe if p.get("date") != heute]
        reihe.append(d)
        reihe.sort(key=lambda p: p["date"])
        neu += 1
        print("  %-6s Verfall %s (dte %d)  Strike %s  Straddle %.2f  = %.3f %% "
              "des Spot%s"
              % (t, d["exp"], d["dte"], d["strike"], d["straddle"],
                 d["straddle_pct"],
                 "" if d["vor_eroeffnung"] else "  [NACH Eroeffnung gelaufen]"))

    gesamt = sum(len(v) for v in hist.values())
    if a.dry_run:
        print("[straddle] --dry-run: %d Ticker erfasst, nichts geschrieben." % neu)
        return 0
    if neu == 0:
        print("[straddle] nichts Neues — Datei bleibt unangetastet.")
        return 1
    write_json_atomic(ZIEL, hist)
    print("[straddle] %d Ticker geschrieben, Archiv jetzt %d Punkte -> %s"
          % (neu, gesamt, ZIEL))
    return 0


if __name__ == "__main__":
    sys.exit(main())
