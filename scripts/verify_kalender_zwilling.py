#!/usr/bin/env python3
"""
verify_kalender_zwilling.py — Kalendervertrag JS = Python für 2000–2035 (NYSE, XETRA).

    py -3.14 scripts/verify_kalender_zwilling.py              # gegen landing/js/holidays.js
    py -3.14 scripts/verify_kalender_zwilling.py --mutationen

Vergleicht für jeden Kalendertag 2000-01-01 … 2035-12-31 `SA.holidays.isTradingDay` (echte holidays.js in node) mit
`shared.exchange_holidays.is_trading_day`. Dazu gezielte Fälle mit belegtem Sollwert, damit der Vergleich nicht zwei
gleich falsche Zwillinge bestätigt. Anlass: Befund N2 (Plan /plain-vanilla v5) — JS setzte den 31.12. als NYSE-Feiertag,
wenn Neujahr ein Samstag ist, Juneteenth vor 2022, keine Sonderschließungen, XETRA 24./31.12. vor 2011.

--mutationen baut jede Korrektur einzeln in einer Kopie zurück und verlangt, dass genau die benannte Prüfung reißt.
Jede Mutation muss ihren Anker treffen (sonst Durchfall), und die Probe muss ihren Endmarker schreiben.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile
from datetime import date, timedelta

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from shared.exchange_holidays import is_trading_day  # noqa: E402

JS = REPO / "landing" / "js" / "holidays.js"
BEREICH = (date(2000, 1, 1), date(2035, 12, 31))

# (Börse, Datum, Soll-Handelstag, Prüfungsname) — Sollwerte aus den Börsenregeln, nicht aus einem der Zwillinge
FAELLE = [
    ("NYSE", "2021-12-31", True, "neujahr_samstag"),     # 1.1.2022 Samstag: kein Ersatztag am 31.12.
    ("NYSE", "2027-12-31", True, "neujahr_samstag"),
    ("NYSE", "2023-01-02", False, "neujahr_sonntag"),    # 1.1.2023 Sonntag → Montag geschlossen
    ("NYSE", "2021-06-18", True, "juneteenth_vor_2022"), # Juneteenth erst ab 2022
    ("NYSE", "2022-06-20", False, "juneteenth_ab_2022"), # 19.6.2022 Sonntag → Montag
    ("NYSE", "2001-09-12", False, "sonderschliessung"),
    ("NYSE", "2012-10-29", False, "sonderschliessung"),
    ("NYSE", "2025-01-09", False, "sonderschliessung"),
    ("NYSE", "2000-01-17", False, "mlk"),                # MLK seit 1998
    ("XETRA", "2010-12-24", True, "xetra_vor_2011"),
    ("XETRA", "2010-12-31", True, "xetra_vor_2011"),
    ("XETRA", "2011-12-30", True, "xetra_ab_2011"),      # 31.12.2011 Samstag; 30.12. normaler Handelstag
    ("XETRA", "2014-12-24", False, "xetra_ab_2011"),
    ("XETRA", "2020-10-05", True, "xetra_regulaer"),
]

PROBE = r"""
const fs = require('fs');
const [js, von, bis] = process.argv.slice(2);
const w = {};
new Function('window', 'var SA = window.SA || {};\n' + fs.readFileSync(js, 'utf8') + '\nwindow.SA = SA;')(w);
const H = w.SA.holidays;
if (!H || !H.isTradingDay) throw new Error('[Aufbau] holidays.js nicht geladen');
const out = { NYSE: {}, XETRA: {} };
const d = new Date(von + 'T12:00:00Z'), ende = new Date(bis + 'T12:00:00Z');
for (; d <= ende; d.setUTCDate(d.getUTCDate() + 1)) {
  const s = d.toISOString().slice(0, 10);
  out.NYSE[s] = H.isTradingDay(s, 'NYSE');
  out.XETRA[s] = H.isTradingDay(s, 'XETRA');
}
process.stdout.write(JSON.stringify(out) + '\nENDE\n');
"""


def js_kalender(js_pfad: pathlib.Path) -> dict:
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
        f.write(PROBE)
        probe = f.name
    r = subprocess.run(["node", probe, str(js_pfad), BEREICH[0].isoformat(), BEREICH[1].isoformat()],
                       capture_output=True, text=True, encoding="utf-8")
    pathlib.Path(probe).unlink(missing_ok=True)
    zeilen = r.stdout.strip().splitlines()
    if r.returncode != 0 or not zeilen or zeilen[-1] != "ENDE":
        raise RuntimeError("[Aufbau] Probe ohne Endmarker: " + (r.stderr or r.stdout)[-400:])
    return json.loads(zeilen[0])


def pruefe(js_pfad: pathlib.Path = JS) -> dict[str, list[str]]:
    """Fehler je Prüfungsname ('zwilling' + Fallnamen)."""
    jsk = js_kalender(js_pfad)
    fehler: dict[str, list[str]] = {}
    d = BEREICH[0]
    while d <= BEREICH[1]:
        s = d.isoformat()
        for b in ("NYSE", "XETRA"):
            py = bool(is_trading_day(d, b))
            if jsk[b][s] != py:
                fehler.setdefault("zwilling", []).append(f"{b} {s}: JS {jsk[b][s]} ≠ Python {py}")
        d += timedelta(days=1)
    for b, s, soll, name in FAELLE:
        js_ist, py_ist = jsk[b][s], bool(is_trading_day(date.fromisoformat(s), b))
        if js_ist != soll or py_ist != soll:
            fehler.setdefault(name, []).append(f"{b} {s}: soll {soll}, JS {js_ist}, Python {py_ist}")
    return fehler


# (Name, alter Text, neuer Text, Prüfung, die reißen muss)
MUTATIONEN = [
    ("31.12.-Ersatztag zurück", "    else if (jan1dow !== 6) list.push(this._ds(y, 1, 1));",
     "    else if (jan1dow !== 6) list.push(this._ds(y, 1, 1));\n    if (new Date(y + 1, 0, 1).getDay() === 6) list.push(this._ds(y, 12, 31));",
     "neujahr_samstag"),
    ("Juneteenth ohne Jahresgrenze", "if (y >= 2022) list.push(this._observed(y, 6, 19));",
     "list.push(this._observed(y, 6, 19));", "juneteenth_vor_2022"),
    ("Sonderschließungen leer", "_NYSE_SONDER: ['2001-09-11',", "_NYSE_SONDER: [], _alt: ['2001-09-11',",
     "sonderschliessung"),
    ("XETRA 24./31.12. ohne Jahresgrenze", "if (y >= 2011) { list.push(this._ds(y, 12, 24));",
     "if (true) { list.push(this._ds(y, 12, 24));", "xetra_vor_2011"),
    ("MLK fehlt", "if (y >= 1998) list.push(this._ds(y, 1, this._nthDow(y, 1, 1, 3)));",
     "", "mlk"),
]


def mutationen() -> int:
    if pruefe():
        print("Grundzustand nicht grün — Mutationen sinnlos")
        return 1
    quelle = JS.read_text(encoding="utf-8")
    ok = 0
    for name, alt, neu, soll in MUTATIONEN:
        if quelle.count(alt) != 1:
            print(f"  DURCHFALL (Anker trifft nicht): {name}")
            continue
        with tempfile.TemporaryDirectory() as tmp:
            kopie = pathlib.Path(tmp) / "holidays.js"
            kopie.write_text(quelle.replace(alt, neu), encoding="utf-8")
            try:
                fe = pruefe(kopie)
            except RuntimeError as e:
                print(f"  UNGÜLTIG (Probe abgebrochen, kein Nachweis): {name}: {e}")
                continue
        if soll in fe:
            ok += 1
            print(f"  gefangen: {name} → {soll}")
        else:
            print(f"  VERFEHLT: {name} — erwartet {soll}, gerissen: {sorted(fe)}")
    print(f"{ok}/{len(MUTATIONEN)} Mutationen gefangen")
    return 0 if ok == len(MUTATIONEN) else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if "--mutationen" in sys.argv:
        sys.exit(mutationen())
    fe = pruefe()
    for k, v in fe.items():
        print(f"FEHLER {k}: {len(v)} — {v[:3]}")
    print(f"verify_kalender_zwilling: {sum(map(len, fe.values()))} Fehler")
    sys.exit(1 if fe else 0)
