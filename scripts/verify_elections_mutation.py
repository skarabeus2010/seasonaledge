#!/usr/bin/env python3
"""
verify_elections_mutation.py — prüft den WÄCHTER verify_elections.py, nicht die Daten.

Verändert Kopien von elections.json / election_calendar_exceptions.json im Speicher
(die Dateien bleiben unberührt) und verlangt, dass verify_elections jeden Fehler meldet.
Enthält die Gegenproben aus Codex-Runde 1 (2026-10-06), die vorher 0 Fehler ergaben.

    py -3.14 scripts/verify_elections_mutation.py     # Exit 0 = alle gefangen
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

import verify_elections as v  # noqa: E402


def _e(d, i):
    return next(x for x in d["elections"] if x["id"] == i)


def _quellen_doppelt_nur_datum(d, c):
    e = _e(d, "us-president-1960")
    q = dict(e["sources"][0], field=["date"])
    q.pop("checked", None)
    e["sources"] = [q, dict(q)]


MUTATIONEN = {
    "US-Datum um einen Tag": lambda d, c: _e(d, "us-midterm-1994").__setitem__("date", "1994-11-09"),
    "DE-Wahl kein Sonntag": lambda d, c: _e(d, "de-bundestag-2002").__setitem__("date", "2002-09-21"),
    "Wahl fehlt": lambda d, c: d["elections"].remove(_e(d, "us-president-1960")),
    "unbekannter Parteicode": lambda d, c: _e(d, "us-president-1980")["result"].__setitem__("winner_party", "US-X"),
    "US-Sieger mit DE-Partei (Codex R1)": lambda d, c: _e(d, "us-president-1980")["result"].__setitem__("winner_party", "DE-SPD"),
    "Senat vor 1914": lambda d, c: _e(d, "us-midterm-1910")["result"].__setitem__(
        "senate_before", {"party": "US-R", "as_of": "1910-11-07", "basis": "organizing_majority"}),
    "geplante Wahl mit Ergebnis": lambda d, c: _e(d, "us-midterm-2026").__setitem__("result", {}),
    "nur eine Quelle": lambda d, c: _e(d, "de-bundestag-1957").__setitem__("sources", _e(d, "de-bundestag-1957")["sources"][:1]),
    "zwei gleiche Quellen nur fürs Datum, ohne Prüfdatum (Codex R1)": _quellen_doppelt_nur_datum,
    "Kanzlernamen entfernt (Codex R1)": lambda d, c: [_e(d, "de-bundestag-2017")["result"].pop(k)
                                                      for k in ("chancellor_before", "chancellor_after")],
    "unknown, aber verified": lambda d, c: _e(d, "us-president-1984")["result"].__setitem__("winner_party", "unknown"),
    "as_of nicht Vortag": lambda d, c: _e(d, "us-midterm-1950")["result"]["house_before"].__setitem__("as_of", "1950-11-01"),
    "Kalender: Wahltag 1966 fehlt": lambda d, c: c["exceptions"].remove(
        next(x for x in c["exceptions"] if x["date"].startswith("1966-11"))),
    "Kalender: 1984 geschlossen": lambda d, c: c["exceptions"].append(
        {"calendar_id": "NYSE", "date": "1984-11-06", "closed": True, "reason": "x", "verified": True, "evidence": "x"}),
    "Kalender: Sonderschließungen entfernt (Codex R1)": lambda d, c: c.__setitem__(
        "exceptions", [x for x in c["exceptions"] if x["date"] not in v.SONDERSCHLIESSUNGEN]),
    "Kalender: belegt ab 1900 (Codex R1)": lambda d, c: c.__setitem__("calendar_documented_from", {"NYSE": "1900-01-01"}),
    "Kalender: Eintrag doppelt": lambda d, c: c["exceptions"].append(dict(c["exceptions"][0])),
    "Kalender: verified ohne evidence": lambda d, c: c["exceptions"][0].pop("evidence"),
}


def main() -> int:
    doc = json.loads(v.WAHLEN.read_text(encoding="utf-8"))
    cal = json.loads(v.AUSNAHMEN.read_text(encoding="utf-8"))
    if v.pruefe_liste(doc) or v.pruefe_ausnahmen(cal):
        print("Grundzustand nicht grün — erst verify_elections.py reparieren")
        return 1
    verfehlt = 0
    for name, mut in MUTATIONEN.items():
        d, c = copy.deepcopy(doc), copy.deepcopy(cal)
        mut(d, c)
        if d == doc and c == cal:
            print(f"  WIRKUNGSLOS  {name}")
            verfehlt += 1
            continue
        f = v.pruefe_liste(d) + v.pruefe_ausnahmen(c)
        print(("  gefangen     " if f else "  VERFEHLT     ") + name)
        verfehlt += 0 if f else 1
    print(f"verify_elections_mutation: {len(MUTATIONEN) - verfehlt}/{len(MUTATIONEN)} gefangen")
    return 1 if verfehlt else 0


if __name__ == "__main__":
    sys.exit(main())
