# -*- coding: utf-8 -*-
"""Zwingt die Zwillinge auf /polymarket zu denselben Zahlen (Codex-Befund 10).

    py -3.14 scripts/verify_polymarket_zwillinge.py

Dieselbe Rechnung lief in `landing/js/polymarket.js::collectYearEndReturns` und
in `shared/weekly_report.py::_collect_year_end_returns` — und kam zu
verschiedenen Ergebnissen. Fuenf Abweichungen, alle am Code bestaetigt:

  1. **Zeitrahmen.** `new Date("2024-03-15")` parst UTC-Mitternacht, aber
     `getFullYear/getMonth/getDate` lesen LOKAL. Codex hat gemessen: dieselbe
     Eingabe ergab in Berlin 50,0 % und in New York 36,4 %. Python rechnet mit
     `date`, also zonenlos.
  2. **Schalttag.** Python nimmt den 28. Februar, JS rollte auf den 1. Maerz.
  3. **Mindeststichprobe.** Python verlangt 3 Jahre, JS rechnete mit EINEM.
  4. **Preisfrische.** Python laedt nur 7 Tage, JS hatte keine Grenze.
  5. **Endpreis <= 0.** Python verwirft, JS liess es durch (selbst gefunden).

Dieser Test vergleicht nicht die Implementierungen, sondern die ZAHLEN: beide
Seiten bekommen dieselben Eingaben, und die Ergebnisse muessen uebereinstimmen.
Fuer Punkt 1 laeuft die JS-Seite zusaetzlich unter ZWEI Zeitzonen — nur wenn
beide Laeufe dasselbe liefern, ist der Rahmen wirklich zonenfest. Eine Pruefung,
die den Fall nicht woertlich trifft, beweist nichts (Lehre aus v65.2).

Node ist Pflicht: fehlt es, ist das UNGEPRUEFT und damit nicht bestanden.
"""
from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import sys
from datetime import date

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from shared.weekly_report import (  # noqa: E402
    POLY_DIV_MIN_SAMPLES,
    divergenz_urteil,
    _collect_year_end_returns,
    _empirical_above_probability,
)

fehler = 0
anzahl = 0


def pruefe(b: bool, was: str) -> None:
    global fehler, anzahl
    anzahl += 1
    print(('  ok   ' if b else '  FEHL ') + was)
    if not b:
        fehler += 1


# ── Die JS-Seite fahren ──────────────────────────────────────────────────────
TREIBER = r"""
global.window = {};
const fs = require('fs');
eval(fs.readFileSync(process.argv[2], 'utf8'));
const PM = global.window.SA.polymarket;
const ein = JSON.parse(process.argv[3]);
// JSON kennt weder NaN noch Infinity. Die Reihe tragt deshalb Kennungen, die
// hier in die echten Werte uebersetzt werden — anders laesst sich der Fall
// ueber die Prozessgrenze nicht stellen.
const SONDER = { __NAN__: NaN, __INF__: Infinity, __NEGINF__: -Infinity };
(ein.reihen || []).forEach(function (z) {
  if (typeof z.close === 'string' && Object.prototype.hasOwnProperty.call(SONDER, z.close)) {
    z.close = SONDER[z.close];
  }
});
const stichtag = new Date(Date.UTC(ein.jahr, ein.monat, ein.tag));
const r = PM.collectYearEndReturns(ein.reihen, stichtag);
const aus = {
  n: r.n,
  zuDuenn: r.zuDuenn,
  renditen: r.samples.map(s => s.ret),
  wkt: ein.ziel == null ? null
       : PM.empiricalAboveProbability(r.samples, ein.ziel)
};
process.stdout.write(JSON.stringify(aus));
"""
TREIBER_PFAD = REPO / 'scripts' / 'js' / '_zwilling_treiber.js'


def js_seite(reihen, stichtag: date, ziel=None, zone: str | None = None) -> dict:
    ein = {
        "reihen": reihen,
        "jahr": stichtag.year,
        "monat": stichtag.month - 1,   # JS zaehlt Monate ab 0
        "tag": stichtag.day,
        "ziel": ziel,
    }
    umgebung = dict(os.environ)
    if zone:
        umgebung['TZ'] = zone
    r = subprocess.run(
        ['node', str(TREIBER_PFAD), str(REPO / 'landing/js/polymarket.js'),
         json.dumps(ein)],
        capture_output=True, text=True, env=umgebung, timeout=60)
    if r.returncode != 0:
        raise RuntimeError('node-Lauf scheiterte: ' + (r.stderr or '')[-400:])
    return json.loads(r.stdout)


def reihe(jahre, start_tag='03-15', start=100.0, ende=150.0):
    """Je Jahr zwei Zeilen: Stichtagspreis und Jahresende."""
    aus = []
    for y in jahre:
        aus.append({"date": f"{y}-{start_tag}", "close": start})
        aus.append({"date": f"{y}-12-31", "close": ende})
    return aus


def main() -> int:
    global fehler
    if not shutil.which('node'):
        print('node fehlt — UNGEPRUEFT, und das ist nicht BESTANDEN.')
        return 1
    TREIBER_PFAD.write_text(TREIBER, encoding='utf-8', newline='\n')
    try:
        return _pruefungen()
    finally:
        TREIBER_PFAD.unlink(missing_ok=True)


def _pruefungen() -> int:
    print('Der Zeitrahmen: dieselbe Eingabe unter zwei Zeitzonen')
    # Genau der Fall, den Codex gemessen hat. Der 1. Januar ist der haerteste
    # Stichtag: wer UTC-Mitternacht lokal liest, landet in New York im Vorjahr.
    r_jahr = reihe([2020, 2021, 2022], start_tag='01-01')
    berlin = js_seite(r_jahr, date(2026, 1, 1), zone='Europe/Berlin')
    newyork = js_seite(r_jahr, date(2026, 1, 1), zone='America/New_York')
    pruefe(berlin == newyork,
           'Berlin und New York liefern dasselbe: n=%s/%s, Renditen %s/%s'
           % (berlin['n'], newyork['n'],
              [round(x, 4) for x in berlin['renditen']],
              [round(x, 4) for x in newyork['renditen']]))
    py = _collect_year_end_returns(r_jahr, date(2026, 1, 1))
    pruefe([round(x, 12) for x in py] == [round(x, 12) for x in berlin['renditen']],
           'Python und JS stimmen ueberein: %s vs %s'
           % ([round(x, 4) for x in py], [round(x, 4) for x in berlin['renditen']]))

    print('Der Schalttag: 29.02. als Stichtag, Vergleichsjahre ohne 29.')
    # 2021 und 2022 sind keine Schaltjahre. Der Preis am 28.02. unterscheidet
    # sich bewusst vom Preis am 01.03., damit die beiden Regeln verschiedene
    # Zahlen ergeben — sonst traefe der Test den Fall nicht.
    # Die Zeile am 01.02. ist entscheidend: ohne sie trifft ein zu frueh
    # gesetzter Stichtag denselben Preis wie der 28.02., und der Test kann die
    # Regeln nicht unterscheiden. Genau das hat der Mutationstest gemeldet —
    # `schalttagErsatz: 1` blieb gruen.
    r_schalt = []
    for y in (2021, 2022, 2023):
        r_schalt.append({"date": f"{y}-02-01", "close": 50.0})
        r_schalt.append({"date": f"{y}-02-28", "close": 100.0})
        r_schalt.append({"date": f"{y}-03-01", "close": 200.0})
        r_schalt.append({"date": f"{y}-12-31", "close": 300.0})
    js = js_seite(r_schalt, date(2024, 2, 29))
    py = _collect_year_end_returns(r_schalt, date(2024, 2, 29))
    pruefe([round(x, 12) for x in py] == [round(x, 12) for x in js['renditen']],
           'Schalttagsregel gleich: Python %s, JS %s'
           % ([round(x, 4) for x in py], [round(x, 4) for x in js['renditen']]))
    pruefe(all(abs(x - 2.0) < 1e-12 for x in js['renditen']),
           'der 28.02. ist der Stichtag (300/100-1 = 2.0), nicht der 01.03. (0.5)')

    print('Die Mindeststichprobe: %d Jahre' % POLY_DIV_MIN_SAMPLES)
    for n_jahre in (1, 2, POLY_DIV_MIN_SAMPLES):
        jahre = list(range(2026 - n_jahre, 2026))
        js = js_seite(reihe(jahre), date(2026, 3, 15))
        py = _collect_year_end_returns(reihe(jahre), date(2026, 3, 15))
        pruefe(js['n'] == len(py), '%d Jahr(e): beide zaehlen %d' % (n_jahre, js['n']))
        erwartet_duenn = n_jahre < POLY_DIV_MIN_SAMPLES
        pruefe(js['zuDuenn'] is erwartet_duenn,
               '%d Jahr(e): zuDuenn=%s wie die Python-Schwelle'
               % (n_jahre, js['zuDuenn']))

    print('Endpreis <= 0 wird auf beiden Seiten verworfen:')
    r_null = reihe([2020, 2021, 2022])
    r_null[-1] = {"date": "2022-12-31", "close": 0.0}
    js = js_seite(r_null, date(2026, 3, 15))
    py = _collect_year_end_returns(r_null, date(2026, 3, 15))
    pruefe(js['n'] == len(py) == 2,
           'beide verwerfen das Jahr mit Endpreis 0 (n=%d/%d)' % (js['n'], len(py)))

    print('Ein unvollstaendiges Vergleichsjahr wird verworfen (Befund 13):')
    # Der Fall muss UNTERSCHEIDEN koennen: 2021 endet am 30.06. mit einem
    # ANDEREN Preis als die vollstaendigen Jahre. Nahm man einfach die letzte
    # Zeile, zaehlte 0,200 als „Jahresend"-Rendite neben 0,500.
    r_teil = reihe([2020, 2021, 2022, 2023])
    r_teil[3] = {"date": "2021-06-30", "close": 120.0}   # statt 2021-12-31
    js = js_seite(r_teil, date(2026, 3, 15))
    py = _collect_year_end_returns(r_teil, date(2026, 3, 15))
    pruefe(js['n'] == len(py) == 3,
           'beide verwerfen das im Juni endende Jahr (n=%d/%d, erwartet 3)'
           % (js['n'], len(py)))
    pruefe(all(abs(x - 0.5) < 1e-12 for x in js['renditen']),
           'keine 0,200 aus dem Juni-Jahr in der Reihe: %s'
           % [round(x, 4) for x in js['renditen']])
    pruefe([round(x, 12) for x in py] == [round(x, 12) for x in js['renditen']],
           'Python und JS gleich: %s vs %s'
           % ([round(x, 4) for x in py], [round(x, 4) for x in js['renditen']]))

    print('Ungueltige Zeilen werden auf beiden Seiten gleich verworfen:')
    # Codex' Gegenbeispiel aus der Abnahme, woertlich: der Stichtagskurs ist
    # leer, der Folgetag gueltig. Python verwarf die Leerzeile und nahm den
    # Folgetag als Startpreis (drei Renditen 0,5), JS nahm die Leerzeile als
    # Startpreis und kam auf keine einzige Stichprobe.
    r_leer = []
    for y in (2021, 2022, 2023):
        r_leer.append({"date": f"{y}-03-15", "close": None})
        r_leer.append({"date": f"{y}-03-16", "close": 100.0})
        r_leer.append({"date": f"{y}-12-31", "close": 150.0})
    js = js_seite(r_leer, date(2026, 3, 15))
    py = _collect_year_end_returns(r_leer, date(2026, 3, 15))
    pruefe(js['n'] == len(py) == 3,
           'beide ueberspringen die Leerzeile und nehmen den Folgetag '
           '(n=%d/%d, erwartet 3)' % (js['n'], len(py)))
    pruefe([round(x, 12) for x in py] == [round(x, 12) for x in js['renditen']],
           'gleiche Renditen: Python %s, JS %s'
           % ([round(x, 4) for x in py], [round(x, 4) for x in js['renditen']]))
    # Ein unlesbarer Kurs ist kein Kurs — auch hier muessen beide gleich
    # entscheiden, sonst verschiebt sich die Stichprobe zwischen Seite und Mail.
    r_muell = [dict(z) for z in r_leer]
    r_muell[1] = {"date": "2021-03-16", "close": "keine Zahl"}
    # Was dabei herauskommt, ist NICHT geraten: 2021 behaelt seine
    # Dezember-Zeile, also wird sie zugleich Start- und Endpreis und die
    # Rendite ist genau 0. Entscheidend ist, dass beide Seiten dasselbe sagen —
    # meine erste Erwartung („das Jahr faellt aus") war falsch, und der Test
    # haette den Code beschuldigt.
    js2 = js_seite(r_muell, date(2026, 3, 15))
    py2 = _collect_year_end_returns(r_muell, date(2026, 3, 15))
    pruefe(js2['n'] == len(py2),
           'gleiche Stichprobengroesse trotz unlesbarem Kurs (n=%d/%d)'
           % (js2['n'], len(py2)))
    pruefe([round(x, 12) for x in py2] == [round(x, 12) for x in js2['renditen']],
           'gleiche Renditen: Python %s, JS %s'
           % ([round(x, 4) for x in py2], [round(x, 4) for x in js2['renditen']]))
    pruefe(any(abs(x) < 1e-12 for x in py2),
           'die verworfene Zeile macht Start = Ende, also genau 0 — '
           'auf beiden Seiten')

    print('Leerstring und nicht-endliche Werte, beide Seiten gleich:')
    # Codex' Gegenbeispiele aus Abnahme-Runde 2, woertlich. `close: ""` ergab
    # vorher Python [0.5, 0.5, 0.5] und JS [] — weil `Number("")` 0 ist und
    # 0 endlich. NaN liess Python durch und rechnete damit weiter.
    r_leerstring = []
    for y in (2021, 2022, 2023):
        r_leerstring.append({"date": f"{y}-03-15", "close": ""})
        r_leerstring.append({"date": f"{y}-03-16", "close": 100.0})
        r_leerstring.append({"date": f"{y}-12-31", "close": 150.0})
    js = js_seite(r_leerstring, date(2026, 3, 15))
    py = _collect_year_end_returns(r_leerstring, date(2026, 3, 15))
    pruefe([round(x, 12) for x in py] == [round(x, 12) for x in js['renditen']],
           'Leerstring: Python %s, JS %s'
           % ([round(x, 4) for x in py], [round(x, 4) for x in js['renditen']]))
    pruefe(len(py) == 3,
           'der Leerstring wird uebersprungen, der Folgetag zaehlt (n=%d)' % len(py))

    for name, wert, kennung in (('NaN', float('nan'), '__NAN__'),
                                ('Infinity', float('inf'), '__INF__')):
        r_py = [{"date": "2021-03-15", "close": wert},
                {"date": "2021-12-31", "close": 150.0}]
        r_js = [{"date": "2021-03-15", "close": kennung},
                {"date": "2021-12-31", "close": 150.0}]
        js = js_seite(r_js, date(2026, 3, 15))
        py = _collect_year_end_returns(r_py, date(2026, 3, 15))
        pruefe([round(x, 12) for x in py] == [round(x, 12) for x in js['renditen']],
               '%s: Python %s, JS %s'
               % (name, [round(x, 4) for x in py],
                  [round(x, 4) for x in js['renditen']]))
        pruefe(all(x == x for x in py),
               '%s erzeugt keine Rendite, die selbst NaN ist' % name)

    print('Seite und Newsletter sagen dasselbe Urteil:')
    # Die Richtungsbehauptung („Markt unterschätzt") stand an DREI Stellen in
    # shared/weekly_report.py und blieb dort stehen, als die Seite sie schon
    # losgeworden war (Codex, Abnahme 2026-10-08). Jetzt eine Quelle je Seite —
    # und dieser Test haelt sie aneinander.
    js_quelle = (REPO / 'landing/js/polymarket.js').read_text(encoding='utf-8')
    for vorzeichen, erwartet in ((4.0, 'Prior über Markt'),
                                 (-4.0, 'Markt über Prior')):
        urteil = divergenz_urteil(vorzeichen)
        pruefe(urteil == erwartet,
               'Python bei %+.0f pp: %r' % (vorzeichen, urteil))
        pruefe(("'" + erwartet + "'") in js_quelle,
               'dieselbe Formulierung steht als Ersatztext in polymarket.js: %r'
               % erwartet)
    pruefe('unterschätzt' not in js_quelle.replace('behauptete', ''),
           'die Richtungsbehauptung steht nicht mehr als Ausgabe im Frontend')

    print('Die Wahrscheinlichkeit aus denselben Stichproben:')
    r3 = reihe([2020, 2021, 2022])
    js = js_seite(r3, date(2026, 3, 15), ziel=0.2)
    py_s = _collect_year_end_returns(r3, date(2026, 3, 15))
    py_w = _empirical_above_probability(py_s, 0.2)
    # KEINE [Aufbau]-Kennung: dass die JS-Seite ueberhaupt eine Zahl liefert,
    # ist eine Aussage ueber den Produktivcode. Mit der Kennung haette eine
    # echte Mutation als „ungueltig" gegolten.
    pruefe(js['wkt'] is not None, 'die JS-Seite liefert eine Wahrscheinlichkeit')
    # Der Vergleich darf nicht STERBEN, wenn die Zahl fehlt — ein Absturz ist
    # kein Befund.
    pruefe(js['wkt'] is not None and abs(js['wkt'] - py_w) < 1e-12,
           'identisch: Python %.6f, JS %s' % (py_w, js['wkt']))

    print()
    print('ALLE PRUEFUNGEN BESTANDEN' if fehler == 0 else '%d FEHLER' % fehler)
    print('PROBE-ENDE %d Pruefungen, %d Fehler' % (anzahl, fehler))
    return 0 if fehler == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
