"""Wächter: der Health-Check vergleicht den gespeicherten Stress-Score mit der Nachrechnung AM gespeicherten Datum.

Anlass 24.11.2026: der Health-Check (GitHub-Cron 05:00 UTC) startete erst 15:29 UTC, `prices` trug schon die
Intraday-Zeile von SPY für den 24.11., die Nachrechnung lief bis dorthin und meldete eine Abweichung zum Lauf vom
23.11. — ein Fehlalarm. `stress_score.stress_bis` schneidet die Reihe am Stichtag.

Fälle (synthetische Reihe, keine Datenbank):
  1. Lauf bis T, Reihe hat eine Intraday-Zeile T+1  → stress_bis(T) = gespeicherter Wert von T.
  2. Der Schnitt ändert den Score nicht            → stress_bis(T) = stress_reihe(volle Reihe)[T].
  3. Gespeichertes Datum fehlt in den Kursen        → stress_bis liefert ein ANDERES Datum (Prüfung wird rot).
  4. Health-Check nutzt stress_bis mit dem gespeicherten Datum.
Mutation: stress_bis durch stress_aktuell (ohne Schnitt) ersetzt → Fall 1 muss rot werden.
"""
import math
import pathlib
import sys
from datetime import date, timedelta

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from shared import stress_score as ss  # noqa: E402


def reihe(n=900):
    d, daten, closes, c = date(2020, 1, 1), [], [], 100.0
    while len(daten) < n:
        if d.weekday() < 5:
            c *= math.exp(0.012 * math.sin(len(daten) * 0.37) + 0.004 * math.cos(len(daten) * 1.3))
            daten.append(d.isoformat())
            closes.append(round(c, 4))
        d += timedelta(days=1)
    return daten, closes


def pruefen(bis_fn):
    fehler = []
    daten, closes = reihe()
    gespeichert = ss.stress_aktuell(daten[:-1], closes[:-1])        # der Lauf von gestern (bis T)
    t = gespeichert["date"]
    intraday = closes[:-1] + [closes[-2] * 0.94]                     # heutige Intraday-Zeile, deutlich anders
    neu = bis_fn(daten, intraday, t)
    if neu.get("date") != t or neu.get("score") != gespeichert["score"] or neu.get("s") != gespeichert["s"]:
        fehler.append(f"Fall 1: Nachrechnung {neu.get('date')}/{neu.get('score')} statt {t}/{gespeichert['score']}")
    voll = {z["date"]: z for z in ss.stress_reihe(daten, closes)}
    mitte = daten[700]
    m = bis_fn(daten, closes, mitte)
    if m.get("score") != voll[mitte]["score"] or m.get("s") != voll[mitte]["s"]:
        fehler.append("Fall 2: Schnitt ändert den Score")
    if gespeichert["score"] is None:
        fehler.append("Fall 1: Testreihe zu kurz, Score unbestimmt")
    luecke = daten[:700] + daten[701:]
    lc = closes[:700] + closes[701:]
    if bis_fn(luecke, lc, daten[700]).get("date") == daten[700]:
        fehler.append("Fall 3: fehlendes Datum wird nicht erkannt")
    return fehler


def main():
    fehler = pruefen(ss.stress_bis)
    health = (ROOT / "scripts" / "daily_health_check.py").read_text(encoding="utf-8")
    if "stress_score.stress_bis(daten, closes, last_date_str)" not in health:
        fehler.append("Fall 4: Health-Check vergleicht nicht am gespeicherten Datum")
    # Mutation: ohne Schnitt (alter Stand) muss Fall 1 rot werden
    mutiert = pruefen(lambda d, c, t: ss.stress_aktuell(d, c))
    if not any(f.startswith("Fall 1") for f in mutiert):
        fehler.append("Mutation ohne Schnitt nicht gefangen")
    for f in fehler:
        print("FEHLER:", f)
    print("verify_stress_stichtag:", "BESTANDEN" if not fehler else "DURCHGEFALLEN", "(4 Fälle + 1 Mutation)")
    return 1 if fehler else 0


if __name__ == "__main__":
    sys.exit(main())
