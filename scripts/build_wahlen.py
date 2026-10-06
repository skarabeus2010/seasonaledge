#!/usr/bin/env python3
"""
build_wahlen.py — Ereignisstudie „Wahlen und Börse" (Phase 1: USA, S&P 500 und Dow).

Schreibt landing/data/wahlen_study.json (Cron-Output, gitignored): je US-Wahl und Reihe
die Schlusskurse der Offsets −60…+60 um den Referenzschluss t0, Gültigkeit je Offset,
die beiden Kontrolljahre (ungerade Jahre, Pseudotermin nach derselben Regel) und für
die nächste Wahl einen Live-Pfad mit projiziertem t0. Rechenkern: shared/elections.py.
Doku: docs/WAHLEN.md.

    docker exec seasonalpha-app python3 scripts/build_wahlen.py            # schreiben
    docker exec seasonalpha-app python3 scripts/build_wahlen.py --no-write # nur prüfen

Exit 1, wenn eine Reihe fehlt oder eine Wahl unerwartet ohne Pfad bleibt — ein leerer
Lauf darf sich nicht als Erfolg melden.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from shared import elections as el  # noqa: E402

AUSGABE = REPO / "landing" / "data" / "wahlen_study.json"
SERIEN = {
    "^GSPC": {"name": "S&P 500", "hinweis": "Vor 1957 Rückrechnung des Index; bis 1952 mit Samstagssitzungen."},
    "^DJI": {"name": "Dow Jones Industrial Average",
             "hinweis": "12 Werte bis 1916, 20 bis 1928, danach 30; vor 1928 ohne Samstagskurse in unserer Reihe."},
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def _meta(w: dict) -> dict:
    """Ergebnis-Felder für Anzeige und rückblickende Filter (kein Signal am Einstiegstag)."""
    r = w.get("result") or {}
    m = {"id": w["id"], "type": w["type"], "date": w["date"], "status": w["status"]}
    if w["type"] == "president" and r:
        m.update(winner=r.get("winner"), winner_party=r.get("winner_party"), prior_party=r.get("prior_party"),
                 machtwechsel=r.get("winner_party") != r.get("prior_party"), contested=bool(r.get("contested")))
    elif w["type"] == "midterm" and r:
        for k in ("house_before", "house_after", "senate_before", "senate_after"):
            if k in r:
                m[k] = r[k]["party"]
    return m


def baue(laden=None, letzte=None) -> dict:
    """Baut die Studie. `laden(ticker) -> (daten, closes)` und `letzte` sind für Tests injizierbar."""
    if laden is None:
        from shared.data import lade_closes as laden  # noqa: N813
    if letzte is None:
        from shared.exchange_holidays import letzte_session
        letzte = letzte_session("NYSE")
    ist_sitzung = el.lade_kalender("NYSE")
    doc = el.lade_wahlen()
    us = [w for w in doc["elections"] if w["country"] == "US"]

    reihen = {}
    for t in SERIEN:
        daten, closes = laden(t)
        # Nur abgeschlossene Sitzungen: der Intraday-Refresh schreibt die laufende Zeile.
        while daten and daten[-1] > letzte.isoformat():
            daten.pop()
            closes.pop()
        reihen[t] = (daten, closes)

    wahlen = []
    for w in us:
        e = _meta(w)
        e["reihen"] = {t: el.studie_fuer_reihe(w, *reihen[t], ist_sitzung, letzte) for t in SERIEN}
        wahlen.append(e)

    return {
        "schema": 1,
        "erzeugt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "fenster": el.FENSTER,
        "letzte_session": letzte.isoformat(),
        "quellen": {"elections.json": _sha(el.WAHLEN_JSON),
                    "election_calendar_exceptions.json": _sha(el.AUSNAHMEN_JSON),
                    "code": os.environ.get("GIT_SHA")},
        "reihen": {t: {**SERIEN[t], "erster_kurs": reihen[t][0][0], "letzter_kurs": reihen[t][0][-1]}
                   for t in SERIEN},
        "wahlen": wahlen,
    }


def pruefe(st: dict) -> list[str]:
    """Plausibilität vor dem Schreiben."""
    """Ab 1971 (belegter Kalender) muss jede Wahl einen Pfad haben; ältere Ausschlüsse
    (z. B. 1914: Börse vom 31.07. bis 27.11. geschlossen) sind erwartbar und werden gezählt."""
    f = []
    for w in st["wahlen"]:
        for t, r in w["reihen"].items():
            if w["date"] >= "1971-01-01" and "pfad" not in r:
                f.append(f"{w['id']} {t}: kein Pfad ({r.get('ausgeschlossen')})")
    if not any(w["status"] == "scheduled" and "pfad" in w["reihen"]["^GSPC"] for w in st["wahlen"]):
        f.append("keine Live-Linie für die nächste Wahl")
    return f


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-write", action="store_true")
    a = ap.parse_args()
    st = baue()
    fehler = pruefe(st)
    n = sum(1 for w in st["wahlen"] for r in w["reihen"].values() if "pfad" in r)
    print(f"build_wahlen: {len(st['wahlen'])} Wahlen, {n} Pfade, letzte Session {st['letzte_session']}")
    for x in fehler:
        print("  FEHLER " + x)
    if fehler:
        return 1
    if not a.no_write:
        from shared.atomic_json import write_json_atomic
        write_json_atomic(AUSGABE, st, indent=None)
        print(f"  geschrieben: {AUSGABE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
