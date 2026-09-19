#!/usr/bin/env python3
"""
backfill_skew_vrp.py — VRP in options_skew_history.json nachrechnen.

    python3 scripts/backfill_skew_vrp.py --dry-run          nur zeigen
    python3 scripts/backfill_skew_vrp.py --ticker SPY,QQQ   einzelne Ticker
    python3 scripts/backfill_skew_vrp.py                    alle, schreibend

WARUM: das VRP (Variance Risk Premium = IV minus realisierte Vola) stand in der
Historie nur in 793 von 6271 Zeilen — der Live-Lauf schreibt es, der Backfill
(backfill_skew_massive.py) nicht. Der geplante IV/RealVol-Radar braucht ein
ticker-internes VRP-PERZENTIL; bei 87 % der Ticker gab es dafuer keine Reihe.

Es braucht dafuer keinen einzigen neuen API-Abruf: `iv_atm` steht in 3173
Zeilen, und die realisierte Vola ist aus unserer eigenen Kursreihe fuer jeden
vergangenen Handelstag rueckwaerts rechenbar.

WARUM ALLE ZEILEN NEU GERECHNET WERDEN, auch die 793 vorhandenen:
Eine Reihe, in der 12 % der Punkte aus der damaligen Kursreihe und 88 % aus
einer Nachrechnung stammen, ist genau die Methodenmischung, die in diesem
Projekt schon einmal das Perzentil zerstoert hat — am 2026-09-09 lag der
Live-Punkt im 99. Perzentil, weil die Historie BS-rekonstruiert war und der
Tagespunkt aus der Provider-IV kam (docs/OPTIONS.md, v54.0). Der Versatz war
damals so gross wie der gesamte Interquartilsabstand. Ein Perzentil ist nur
so gut wie die Gleichartigkeit der Reihe, aus der es kommt.

Gegengerechnet wird das: `--dry-run` zeigt, wie weit die vorhandenen Werte von
der Neurechnung abweichen. Gemessen ueber sieben Ticker: Median 0,55 pp,
95. Perzentil 2,71 pp, max 3,43 pp — MEHR als die Adjustierung erklaeren kann.
Nachgeprueft an GOOGL/2026-09-15 ergeben Supabase UND Yahoo rv21 = 0,225,
waehrend der gespeicherte Wert 0,191 impliziert; er passt zu keiner der beiden
Quellen, und der Daten-/Codestand seiner Entstehung ist nicht rekonstruierbar.
Das ist das eigentliche Argument fuer die Neurechnung: nicht dass die alten
Werte anders sind, sondern dass sie nicht nachvollziehbar sind.

QUELLE: Supabase ueber shared.data.lade_closes — kein Yahoo. Begruendung dort;
kurz: Yahoos Adjustierung wandert mit jeder Dividende, dieselbe Abfrage ergibt
an verschiedenen Tagen verschiedene Reihen. Der Live-Lauf nutzt seit
2026-09-19 dieselbe Quelle, damit Historie und Tagespunkt vergleichbar sind.

FORMEL: identisch zum Live-Lauf, weil BEIDE shared/realized_vol.py benutzen —
vrp_pts = (iv_atm − rv21) · 100, rv21 = annualisierte realisierte Vola der
21 Handelstage bis einschliesslich des jeweiligen Tages.

BETRIEB: der Live-Cron schreibt dieselbe Datei um 23:00 UTC und haelt sie im
Speicher. Dieses Skript darf nicht daneben laufen — sonst geht ein Schreibvorgang
verloren (Lost Update, siehe docs/OPTIONS.md). Es laeuft in Sekunden, also
einfach ausserhalb des Fensters starten.
"""
from __future__ import annotations

import argparse
import gc
import json
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from shared.atomic_json import write_json_atomic                     # noqa: E402
from shared.data import KursreiheFehlt, lade_closes                  # noqa: E402
from shared.realized_vol import RV_FENSTER, rv_reihe                 # noqa: E402

HISTORIE = _ROOT / "landing/data/options_skew_history.json"

# Schluessel, die keine Ticker sind (vorwaerts akkumulierte Reihen).
KEINE_TICKER = {"__CORR", "__PCR"}


def _kursfenster(daten: list[str]) -> str:
    """Fruehestes Ladedatum: das aelteste Historien-Datum minus Puffer.

    Der erste Punkt braucht 21 Handelstage VOR sich, sonst bekommt er kein
    VRP. Ein Jahr Vorlauf deckt das mit Reserve fuer Feiertage ab.
    """
    aeltestes = min(daten)
    return "%04d-%s" % (int(aeltestes[:4]) - 1, aeltestes[5:])


def nachrechnen(hist: dict, nur: set[str] | None = None) -> dict:
    """Rechnet das VRP fuer alle Zeilen mit iv_atm neu. Gibt eine Statistik zurueck.

    Verandert `hist` an Ort und Stelle.
    """
    stat = {"ticker": 0, "uebersprungen": 0, "zeilen_mit_iv": 0, "gesetzt": 0,
            "kein_rv": 0, "vorher_vorhanden": 0, "abweichungen": [],
            "ohne_reihe": [], "invariant_alt": [], "invariant_neu_gleich": [],
            "invariant_neu_dazu": []}

    for t in sorted(hist):
        if t in KEINE_TICKER:
            continue
        if nur and t not in nur:
            continue
        zeilen = hist.get(t) or []
        mit_iv = [z for z in zeilen if isinstance(z, dict) and z.get("iv_atm")]
        if not mit_iv:
            stat["uebersprungen"] += 1
            continue
        daten = [z["date"] for z in mit_iv if z.get("date")]
        if not daten:
            stat["uebersprungen"] += 1
            continue

        try:
            kd, kc = lade_closes(t, ab=_kursfenster(daten),
                                 mindestens=RV_FENSTER + 5)
        except KursreiheFehlt as e:
            # Kein VRP ist besser als ein aus fremder Quelle gerechnetes.
            stat["ohne_reihe"].append(f"{t}: {e}")
            stat["uebersprungen"] += 1
            continue

        rv_je_tag = rv_reihe(kd, kc)
        stat["ticker"] += 1

        for z in zeilen:
            if not isinstance(z, dict) or not z.get("iv_atm") or not z.get("date"):
                continue
            stat["zeilen_mit_iv"] += 1
            rv = rv_je_tag.get(z["date"])
            if rv is None:
                # Handelstag ohne volles, lueckenfreies 21-Tage-Fenster. Das
                # Feld wird BEWUSST geleert, falls vorher ein Wert stand: ein
                # nicht nachvollziehbarer Wert in einer sonst einheitlichen
                # Reihe ist schlimmer als eine Luecke.
                if z.get("vrp_pts") is not None:
                    stat["vorher_vorhanden"] += 1
                    z["vrp_pts"] = None
                stat["kein_rv"] += 1
                continue
            neu = round((float(z["iv_atm"]) - rv) * 100, 2)
            alt = z.get("vrp_pts")
            if alt is not None:
                stat["vorher_vorhanden"] += 1
                stat["invariant_alt"].append(float(alt))
                stat["invariant_neu_gleich"].append(neu)
                stat["abweichungen"].append((t, z["date"], float(alt), neu))
            else:
                stat["invariant_neu_dazu"].append((neu, bool(z.get("reconstructed"))))
            z["vrp_pts"] = neu
            z["vrp_rv"] = rv            # Nachvollziehbarkeit: welche RV war es?
            z["vrp_quelle"] = "supabase21"
            stat["gesetzt"] += 1

        gc.collect()
    return stat


def bericht(stat: dict) -> None:
    print()
    print("=" * 70)
    print("Ticker gerechnet        : %d" % stat["ticker"])
    print("Ticker uebersprungen    : %d" % stat["uebersprungen"])
    print("Zeilen mit iv_atm       : %d" % stat["zeilen_mit_iv"])
    print("VRP gesetzt             : %d" % stat["gesetzt"])
    print("ohne volles RV-Fenster  : %d" % stat["kein_rv"])
    print("vorher schon vorhanden  : %d" % stat["vorher_vorhanden"])

    ab = stat["abweichungen"]
    if ab:
        d = sorted(abs(n - a) for _, _, a, n in ab)
        print()
        print("Abweichung Neurechnung gegen die bestehenden %d Werte (pp):" % len(ab))
        print("  Median %.2f | 95. Perzentil %.2f | max %.2f"
              % (d[len(d) // 2], d[int(len(d) * 0.95)], d[-1]))
        print("  Die groessten fuenf:")
        for t, dt, a, n in sorted(ab, key=lambda x: -abs(x[3] - x[2]))[:5]:
            print("    %-7s %s  %7.2f -> %7.2f  (%+.2f pp)" % (t, dt, a, n, n - a))
        print()
        print("  Eine Abweichung ungleich null ist erwartet — aber sie ist")
        print("  GROESSER als durch Adjustierung erklaerbar, und das ist der")
        print("  Grund fuer die Neurechnung: die alten Werte lassen sich nicht")
        print("  reproduzieren, auch nicht mit der Yahoo-Reihe. Nachgemessen an")
        print("  GOOGL/2026-09-15: Supabase und Yahoo ergeben beide rv21 0,225,")
        print("  der gespeicherte Wert impliziert 0,191 — er passt zu keiner der")
        print("  beiden Quellen. Aus welchem Daten- und Codestand er stammt, ist")
        print("  nicht mehr rekonstruierbar. Eine Reihe aus nicht")
        print("  nachvollziehbaren Werten taugt nicht fuer ein Perzentil.")

    _invariant(stat)

    if stat["ohne_reihe"]:
        print()
        print("Ohne Kursreihe in Supabase (%d):" % len(stat["ohne_reihe"]))
        for z in stat["ohne_reihe"][:10]:
            print("  " + z)


def _verteilung(werte):
    w = sorted(werte)
    n = len(w)
    if not n:
        return None
    return (n, w[n // 2], sum(w) / n, sum(1 for v in w if v > 0) / n * 100)


def _invariant(stat: dict) -> None:
    """Prueft den Domaenen-Invariant: das VRP ist im Mittel POSITIV.

    Optionskaeufer zahlen eine Praemie fuer Absicherung, die implizite Vola
    liegt deshalb im Schnitt ueber der realisierten. Eine Reihe, deren VRP im
    Mittel negativ ist, taugt nicht fuer ein Perzentil — dann stimmt etwas mit
    der IV oder der Vola nicht.

    Verglichen wird auf der GLEICHEN Teilmenge. Ein Vergleich der 772 alten
    Live-Zeilen gegen 3152 Zeilen inklusive Backfill waere wertlos, weil die
    Grundmengen verschieden sind — beim ersten Lauf sah die Neurechnung dadurch
    schlechter aus, obwohl sie auf den vergleichbaren Zeilen besser ist.
    """
    a = _verteilung(stat["invariant_alt"])
    b = _verteilung(stat["invariant_neu_gleich"])
    if a and b:
        print()
        print("Domaenen-Invariant (VRP im Mittel positiv), SELBE Zeilen:")
        print("  alt  n=%4d  Median %+6.2f  Mittel %+6.2f  positiv %5.1f %%" % a)
        print("  neu  n=%4d  Median %+6.2f  Mittel %+6.2f  positiv %5.1f %%" % b)
        if b[2] >= a[2] and b[3] >= a[3]:
            print("  -> die Neurechnung verbessert Mittel UND Anteil positiver Werte.")
        else:
            print("  -> ACHTUNG: die Neurechnung ist auf diesem Pruefstein NICHT besser.")
            print("     Nicht schreiben, bevor die Ursache geklaert ist.")

    dazu = stat["invariant_neu_dazu"]
    if dazu:
        d = _verteilung([v for v, _ in dazu])
        anteil_recon = sum(1 for _, r in dazu if r) / len(dazu) * 100
        print()
        print("Neu hinzugekommene Zeilen:")
        print("  n=%4d  Median %+6.2f  Mittel %+6.2f  positiv %5.1f %%" % d)
        print("  davon aus dem Backfill (reconstructed): %.0f %%" % anteil_recon)
        if d[2] < 0:
            print()
            print("  !! DAS VRP DIESER ZEILEN IST IM MITTEL NEGATIV.")
            print("  Das ist KEIN Fehler dieser Nachrechnung — die realisierte Vola")
            print("  kommt aus unserer gepflegten Kursreihe. Es liegt am gespeicherten")
            print("  iv_atm: die Backfill-Zeilen stammen aus der Zeit VOR der")
            print("  Skew-Reparatur vom 2026-09-11 (Volumenfilter als falsches")
            print("  Kriterium, selbstreferenzielles Delta, angepasste Optionsserien —")
            print("  siehe CLAUDE.md v61.0). Ein VRP-Perzentil ueber diese Reihe waere")
            print("  unbrauchbar, egal wie gut die Vola-Seite gerechnet ist.")
            print("  -> Erst den Reparatur-Backfill mit der korrigierten Methodik")
            print("     fahren, dann diese Nachrechnung.")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true",
                    help="nur rechnen und berichten, nichts schreiben")
    ap.add_argument("--ticker", help="Komma-Liste statt aller Ticker")
    args = ap.parse_args()

    if not HISTORIE.exists():
        print("FEHLER: %s fehlt" % HISTORIE)
        return 1
    hist = json.loads(HISTORIE.read_text(encoding="utf-8"))
    print("Historie: %d Ticker, %d Punkte"
          % (len(hist), sum(len(v) for v in hist.values() if isinstance(v, list))))

    nur = None
    if args.ticker:
        nur = {x.strip().upper() for x in args.ticker.split(",") if x.strip()}
        print("nur: %s" % ", ".join(sorted(nur)))

    stat = nachrechnen(hist, nur)
    bericht(stat)

    if args.dry_run:
        print()
        print("--dry-run: nichts geschrieben.")
        return 0
    if not stat["gesetzt"]:
        print()
        print("Kein Wert gesetzt -> nicht geschrieben (eine Datei ohne Grund zu")
        print("ersetzen ist ein unnoetiges Risiko).")
        return 1

    write_json_atomic(HISTORIE, hist)
    print()
    print("geschrieben: %s" % HISTORIE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
