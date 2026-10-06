#!/usr/bin/env python3
"""
verify_elections.py — Wächter für die Wahltermin-Liste.

Prüft landing/data/elections.json und landing/data/election_calendar_exceptions.json
(Plan: docs/review_prompts/2026-10-06_wahlen_plan.md, Phase 0):

  1. Schema: Pflichtfelder, eindeutige IDs, bekannte Typen/Parteien, Status.
  2. Termine: US = erster Dienstag nach dem ersten Montag im November; DE = Sonntag;
     Abdeckung lückenlos (US-Präsident alle 4, Midterm alle 4 Jahre, versetzt).
  3. Ergebnisse: gehaltene Wahlen haben ein Ergebnis, geplante keines; Kammer-Felder
     mit party/as_of/basis; Senat erst ab 1914; Quellenpflicht (≥ 2) und verified.
  4. Termin-Parität: die bestehenden Formeln strategy-compute.js::_electionDay (node)
     und plain_vanilla.py::_get_election_day liefern für jedes US-Jahr dasselbe Datum
     wie die Liste — bis Phase M rechnen die alten Strategien noch mit diesen Formeln.
  5. Kalender-Ausnahmen: jeder NYSE-Wahltag bis 1968 (auch ungerade Jahre) sowie
     1972/1976/1980 ist als Schließung eingetragen, danach keiner.

    py -3.14 scripts/verify_elections.py            # Exit 0 = grün
    py -3.14 scripts/verify_elections.py --ohne-node  # Termin-Parität JS bewusst überspringen
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
WAHLEN = REPO / "landing" / "data" / "elections.json"
AUSNAHMEN = REPO / "landing" / "data" / "election_calendar_exceptions.json"

TYPEN = {"US": {"president", "midterm"}, "DE": {"bundestag"}}
STATUS = {"held", "scheduled"}
KAMMER_BASIS = {"speaker", "organizing_majority", "tie_vp", "unknown"}


def us_wahltag(jahr: int) -> date:
    """Unabhängige Referenz: erster Dienstag nach dem ersten Montag im November."""
    d = date(jahr, 11, 2)  # frühester möglicher Dienstag ist der 2.
    while d.weekday() != 1:
        d += timedelta(days=1)
    return d


def pruefe_liste(doc: dict) -> list[str]:
    f: list[str] = []
    parteien = set(doc.get("parties", {}))
    wahlen = doc.get("elections", [])
    ids = [e.get("id") for e in wahlen]
    for doppelt in {i for i in ids if ids.count(i) > 1}:
        f.append(f"ID doppelt: {doppelt}")
    heute = date.today()
    for e in wahlen:
        i = e.get("id", "?")
        for k in ("id", "country", "type", "date", "status", "sources", "verified", "result", "early"):
            if k not in e:
                f.append(f"{i}: Feld {k} fehlt")
        if e.get("type") not in TYPEN.get(e.get("country"), set()):
            f.append(f"{i}: Typ {e.get('type')} passt nicht zu Land {e.get('country')}")
            continue
        if e.get("status") not in STATUS:
            f.append(f"{i}: Status {e.get('status')!r}")
        try:
            d = date.fromisoformat(e["date"])
        except Exception:  # noqa: BLE001
            f.append(f"{i}: Datum {e.get('date')!r} ungültig")
            continue
        if e["country"] == "US" and d != us_wahltag(d.year):
            f.append(f"{i}: {d} ist nicht der US-Wahltag {us_wahltag(d.year)}")
        if e["country"] == "DE" and d.weekday() != 6:
            f.append(f"{i}: {d} ist kein Sonntag")
        if e["id"] != f"{e['country'].lower()}-{e['type']}-{d.year}":
            f.append(f"{i}: ID passt nicht zu Land/Typ/Jahr")
        # Status gegen Datum
        if e["status"] == "held" and d > heute:
            f.append(f"{i}: 'held', liegt aber in der Zukunft")
        if e["status"] == "scheduled" and d < heute:
            f.append(f"{i}: 'scheduled', liegt aber in der Vergangenheit — Ergebnis nachtragen")
        r = e.get("result")
        if e["status"] == "scheduled":
            if r is not None:
                f.append(f"{i}: geplante Wahl mit Ergebnis")
        else:
            if not isinstance(r, dict):
                f.append(f"{i}: gehaltene Wahl ohne Ergebnis")
                continue
            f += pruefe_ergebnis(i, e, r, d, parteien)
            if len(e.get("sources", [])) < 2:
                f.append(f"{i}: weniger als zwei Quellen")
            if e.get("verified") is not True:
                f.append(f"{i}: nicht aus zwei Quellen bestätigt (verified != true)")
        for s in e.get("sources", []):
            if not s.get("url") or not s.get("field"):
                f.append(f"{i}: Quelle ohne url/field")
        # Termin bekannt seit
        skf = e.get("schedule_known_from")
        if skf is not None and skf > e["date"]:
            f.append(f"{i}: schedule_known_from {skf} nach dem Wahltermin")
        if e["country"] == "US" and skf is None:
            f.append(f"{i}: US-Termin ohne schedule_known_from")
        if e.get("early") and skf is None:
            f.append(f"{i}: vorgezogene Wahl ohne schedule_known_from")
    f += pruefe_abdeckung(doc, wahlen)
    return f


def pruefe_ergebnis(i: str, e: dict, r: dict, d: date, parteien: set) -> list[str]:
    f: list[str] = []

    def partei(wert, feld):
        if wert not in parteien:
            f.append(f"{i}: {feld} = {wert!r} ist keine bekannte Partei")

    if e["type"] == "president":
        partei(r.get("winner_party"), "winner_party")
        partei(r.get("prior_party"), "prior_party")
        if not r.get("winner"):
            f.append(f"{i}: winner fehlt")
    elif e["type"] == "midterm":
        for kammer in ("house", "senate"):
            for seite in ("before", "after"):
                k = f"{kammer}_{seite}"
                if kammer == "senate" and d.year < 1914:
                    if k in r:
                        f.append(f"{i}: {k} vor 1914 (Abdeckungsgrenze)")
                    continue
                v = r.get(k)
                if not isinstance(v, dict):
                    f.append(f"{i}: {k} fehlt")
                    continue
                if v.get("party") != "unknown":
                    partei(v.get("party"), k)
                if v.get("basis") not in KAMMER_BASIS:
                    f.append(f"{i}: {k}.basis {v.get('basis')!r}")
                as_of = v.get("as_of", "")
                if seite == "before" and as_of != (d - timedelta(days=1)).isoformat():
                    f.append(f"{i}: {k}.as_of {as_of} ist nicht der Tag vor der Wahl")
                if seite == "after" and not (d.isoformat() < as_of <= f"{d.year + 1}-03-04"):
                    f.append(f"{i}: {k}.as_of {as_of} ist kein plausibler Kongressbeginn")
    else:
        partei(r.get("strongest_party"), "strongest_party")
        if not (d.year == 1949 and r.get("chancellor_party_before") == "n/a"):
            partei(r.get("chancellor_party_before"), "chancellor_party_before")
        partei(r.get("chancellor_party_after"), "chancellor_party_after")
        wechsel = r.get("chancellor_before") != r.get("chancellor_after")
        if d.year > 1949 and r.get("chancellor_change") is not wechsel:
            f.append(f"{i}: chancellor_change passt nicht zu den Namen")
    return f


def pruefe_abdeckung(doc: dict, wahlen: list[dict]) -> list[str]:
    f: list[str] = []
    for (land, typ), (von, bis) in (
        (("US", "president"), doc["coverage"]["US"]["president"]),
        (("US", "midterm"), doc["coverage"]["US"]["midterm"]),
    ):
        soll = set(range(von, bis + 1, 4))
        ist = {int(e["date"][:4]) for e in wahlen if e["country"] == land and e["type"] == typ}
        for j in sorted(soll - ist):
            f.append(f"{land}-{typ} {j} fehlt")
        for j in sorted(ist - soll):
            f.append(f"{land}-{typ} {j} ausserhalb der Abdeckung")
    de = sorted(int(e["date"][:4]) for e in wahlen if e["country"] == "DE")
    von, bis = doc["coverage"]["DE"]["bundestag"]
    if not de or de[0] != von or de[-1] != bis:
        f.append(f"DE-Abdeckung {de[:1]}…{de[-1:]} passt nicht zu coverage {von}–{bis}")
    for a, b in zip(de, de[1:]):
        if b - a > 4:
            f.append(f"DE: Lücke zwischen {a} und {b} (> 4 Jahre)")
    return f


def pruefe_ausnahmen(cal: dict) -> list[str]:
    f: list[str] = []
    ist = {(x["calendar_id"], x["date"]) for x in cal.get("exceptions", []) if x.get("closed")}
    for x in cal.get("exceptions", []):
        if not x.get("reason") or "verified" not in x:
            f.append(f"Ausnahme {x.get('date')}: reason/verified fehlt")
    for jahr in range(1896, 2030):
        tag = us_wahltag(jahr).isoformat()
        soll_zu = jahr <= 1968 or jahr in (1972, 1976, 1980)
        if soll_zu and ("NYSE", tag) not in ist:
            f.append(f"NYSE-Schließung am Wahltag {tag} fehlt")
        if not soll_zu and ("NYSE", tag) in ist:
            f.append(f"NYSE-Schließung am Wahltag {tag} eingetragen, die NYSE war offen")
    return f


def pruefe_paritaet(doc: dict, mit_node: bool) -> list[str]:
    """Die alten Formeln rechnen bis Phase M weiter — sie müssen dieselben US-Termine liefern."""
    from shared.strategies.plain_vanilla import _get_election_day

    f: list[str] = []
    jahre = sorted({int(e["date"][:4]) for e in doc["elections"] if e["country"] == "US"})
    soll = {int(e["date"][:4]): e["date"] for e in doc["elections"] if e["country"] == "US"}
    for j in jahre:
        if _get_election_day(j).isoformat() != soll[j]:
            f.append(f"plain_vanilla._get_election_day({j}) = {_get_election_day(j)} statt {soll[j]}")
    if not mit_node:
        return f
    if not shutil.which("node"):
        return f + ["node fehlt — Termin-Parität für strategy-compute.js nicht geprüft (bewusst: --ohne-node)"]
    js = (
        "global.window={SA:{i18n:{t:function(k,d){return d||k;},lang:'de',getLang:function(){return 'de';}}}};"
        "global.SA=window.SA;"
        f"require({json.dumps(str(REPO / 'landing' / 'js' / 'strategy-compute.js'))});"
        f"var J={json.dumps(jahre)};"
        "console.log(JSON.stringify(J.map(function(y){return [y, window.SA.strategy._electionDay(y)];})));"
    )
    p = subprocess.run(["node", "-e", js], capture_output=True, text=True, timeout=60)
    if p.returncode != 0:
        return f + [f"node-Lauf gescheitert: {p.stderr.strip()[:300]}"]
    for j, d in json.loads(p.stdout.strip().splitlines()[-1]):
        if d != soll[j]:
            f.append(f"strategy-compute._electionDay({j}) = {d} statt {soll[j]}")
    return f


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ohne-node", action="store_true")
    a = ap.parse_args()
    doc = json.loads(WAHLEN.read_text(encoding="utf-8"))
    cal = json.loads(AUSNAHMEN.read_text(encoding="utf-8"))
    fehler = pruefe_liste(doc) + pruefe_ausnahmen(cal) + pruefe_paritaet(doc, not a.ohne_node)
    for x in fehler[:40]:
        print("  FEHLER " + x)
    n = len(doc["elections"])
    print(f"verify_elections: {n} Wahlen, {len(cal['exceptions'])} Kalender-Ausnahmen, {len(fehler)} Fehler")
    return 1 if fehler else 0


if __name__ == "__main__":
    sys.exit(main())
