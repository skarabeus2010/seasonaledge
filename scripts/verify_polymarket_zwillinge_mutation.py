# -*- coding: utf-8 -*-
"""Prueft den Zwillingstest, nicht den Code: baut die fuenf Abweichungen aus
Befund 10 wieder ein und verlangt, dass verify_polymarket_zwillinge.py ROT wird.

    py -3.14 scripts/verify_polymarket_zwillinge_mutation.py

Ohne diesen Nachweis ist „die Zwillinge stimmen ueberein" eine Aussage ueber den
Test und nicht ueber den Code. Die vier Beweisregeln wie in den uebrigen
Mutationstests: `[Aufbau]` gerissen = Geruest zerstoert · Endmarker muss
erreicht sein · jede Mutation benennt die Pruefung, die sie reissen muss · eine
Ausnahme gilt nie als Nachweis.
"""
from __future__ import annotations

import io
import re
import subprocess
import sys

if hasattr(sys.stdout, 'reconfigure'):          # cp1252 kann die
    sys.stdout.reconfigure(encoding='utf-8')     # Mutationsnamen nicht
if hasattr(sys.stderr, 'reconfigure'):          # ausgeben; ohne das
    sys.stderr.reconfigure(encoding='utf-8')     # bricht der Lauf ab.

JS = 'landing/js/polymarket.js'
PY = 'shared/weekly_report.py'
PROBE = 'scripts/verify_polymarket_zwillinge.py'

MUTATIONEN = [
    # 1. Der Zeitrahmen. Zurueck auf lokale Lesung — dann weichen Berlin und
    #    New York voneinander ab, genau wie von Codex gemessen.
    ('Zeitrahmen wieder lokal statt UTC (Jahr)',
     JS,     "      var y = d.getUTCFullYear();",
     "      var y = d.getFullYear();",
     'Berlin und New York liefern dasselbe'),

    ('Stichtag wieder lokal konstruiert',
     JS,     "      var refInYear = new Date(Date.UTC(yearInt, refMonth, tag));",
     "      var refInYear = new Date(yearInt, refMonth, tag);",
     'Berlin und New York liefern dasselbe'),

    ('Stichtagsmonat wieder lokal gelesen',
     JS,     "    var refMonth = ref.getUTCMonth();   // 0-11",
     "    var refMonth = ref.getMonth();   // 0-11",
     'Berlin und New York liefern dasselbe'),

    # 2. Der Schalttag. Ohne den Ersatz rollt das Datum auf den 1. Maerz.
    ('Schalttagsregel entfernt — rollt wieder auf den 1. Maerz',
     JS,     "      var tag = refDay;\n"
     "      if (refMonth === 1 && refDay === 29) {\n"
     "        var schalt = new Date(Date.UTC(yearInt, 1, 29));\n"
     "        if (schalt.getUTCMonth() !== 1) tag = VERTRAG.schalttagErsatz;\n"
     "      }",
     "      var tag = refDay;",
     'der 28.02. ist der Stichtag'),

    ('Schalttagsersatz auf den 1. Maerz gesetzt',
     JS,     "    schalttagErsatz: 28",
     "    schalttagErsatz: 1",
     'der 28.02. ist der Stichtag'),

    # 3. Die Mindeststichprobe.
    ('Mindeststichprobe auf 1 gesenkt',
     JS,     "    minStichprobe: 3,",
     "    minStichprobe: 1,",
     'wie die Python-Schwelle'),

    # 5. Endpreis <= 0.
    ('Endpreis darf wieder 0 sein',
     JS,     "      if (startPrice != null && startPrice > 0 && endPrice != null && endPrice > 0) {",
     "      if (startPrice != null && startPrice > 0 && endPrice != null) {",
     'beide verwerfen das Jahr mit Endpreis 0'),

    # 6. Befund 13: das Vergleichsfenster muss vollstaendig sein. Je eine
    #    Mutation pro Seite — faellt die Regel nur auf EINER Seite, weichen die
    #    Zahlen auseinander, und genau das muss der Zwillingstest sehen.
    ('JS nimmt wieder die letzte Zeile des Jahres, egal wann',
     JS,
     "      var endPrice = (letzte && letzte.d.getUTCMonth() === VERTRAG.jahresendeMonat)\n"
     "        ? letzte.close : null;",
     "      var endPrice = letzte ? letzte.close : null;",
     'beide verwerfen das im Juni endende Jahr'),

    ('Der Jahresendmonat wird auf Juni gesetzt',
     JS,
     "    jahresendeMonat: 11",
     "    jahresendeMonat: 5",
     'keine 0,200 aus dem Juni-Jahr'),

    # 7. Der Eingangsfilter. Nahm JS ungueltige Zeilen mit, wurde eine Zeile
    #    mit `close: null` zum Startpreis — Codex' Gegenbeispiel aus der
    #    Abnahme vom 2026-10-08.
    ('JS nimmt ungueltige Zeilen wieder mit',
     JS,
     "      if (!r || !r.date || r.close === null || r.close === undefined) return;",
     "      if (false) return;",
     'beide ueberspringen die Leerzeile'),

    ('JS prueft den Kurs nicht mehr auf eine Zahl',
     JS,
     "      var close = Number(r.close);\n      if (!isFinite(close)) return;",
     "      var close = Number(r.close);",
     'gleiche Renditen'),

    # 8. Die Richtungsbehauptung im Newsletter. Sie stand dort an drei Stellen
    #    weiter, als die Seite sie losgeworden war.
    ('Der Newsletter behauptet wieder „Markt unterschätzt"',
     PY,
     '    return "Prior über Markt" if divergence_pp > 0 else "Markt über Prior"',
     '    return "Markt unterschätzt" if divergence_pp > 0 else "Markt überschätzt"',
     'Python bei +4 pp'),

    # Abnahme-Runde 2: der Leerstring und die nicht-endlichen Werte.
    ('JS laesst den Leerstring wieder als Kurs durch',
     JS,
     "      if (typeof r.close === 'string' && r.close.trim() === '') return;",
     "      if (false) return;",
     'Leerstring: Python'),

    ('Python laesst NaN und Infinity wieder durch',
     PY,
     "        if not math.isfinite(c):\n            continue",
     "        if False:\n            continue",
     'Python'),

    ('Python nimmt wieder die letzte Zeile des Jahres, egal wann',
     PY,
     "        if letzte_zeile[0].month != JAHRESENDE_MONAT:\n"
     "            continue\n",
     "",
     'beide verwerfen das im Juni endende Jahr'),
]

UNGUELTIG_ERWARTET = [
    ('Ausnahme statt Verhaltensaenderung',
     JS,
     "    var byYear = {};",
     "    var byYear = null.x;"),
]

ROH = {JS: io.open(JS, 'rb').read(), PY: io.open(PY, 'rb').read()}


def anker(datei: str, text: str) -> bytes:
    roh = ROH[datei]
    if roh.count(b'\r\n') > roh.count(b'\n') // 2:
        text = text.replace('\r\n', '\n').replace('\n', '\r\n')
    return text.encode('utf-8')


basis = subprocess.run(['py', '-3.14', PROBE], capture_output=True, text=True)
if basis.returncode != 0:
    print('ABBRUCH: die Probe ist schon ohne Mutation rot.')
    print(basis.stdout[-1500:])
    sys.exit(1)
_m = re.search(r'PROBE-ENDE (\d+) Pruefungen', basis.stdout or '')
if not _m:
    print('ABBRUCH: die Probe meldet keinen Endmarker.')
    sys.exit(1)
print('Grundlinie: Zwillingstest ohne Mutation gruen, %s Pruefungen\n' % _m.group(1))


def bewerte(datei: str, alt: str, neu: str, erwartet: str | None = None):
    a = anker(datei, alt)
    n = ROH[datei].count(a)
    if n != 1:
        return 'kein-anker', 'Anker %dx gefunden, erwartet 1x' % n
    io.open(datei, 'wb').write(ROH[datei].replace(a, anker(datei, neu), 1))
    try:
        r = subprocess.run(['py', '-3.14', PROBE], capture_output=True, text=True)
    finally:
        io.open(datei, 'wb').write(ROH[datei])
    ausgabe = (r.stdout or '') + (r.stderr or '')
    if r.returncode == 0:
        return 'entwischt', 'Probe blieb gruen'
    if 'PROBE-ENDE' not in ausgabe:
        return 'ungueltig', 'die Probe brach ab statt durchzulaufen'
    zeilen = [z for z in ausgabe.splitlines() if 'FEHL ' in z]
    aufbau = [z for z in zeilen if '[Aufbau]' in z]
    if aufbau:
        return 'ungueltig', 'Aufbaupruefung gerissen: ' + aufbau[0].strip()[:50]
    # Fuenfte Beweisregel: eine EINGEFANGENE Ausnahme ist kein Nachweis. Die
    # vierte Regel erkannte nur den Abbruch der Probe; faengt die Probe den
    # Fehler ab und meldet ihn, sah es wie eine gefangene Mutation aus
    # (Codex, Abnahme Runde 2).
    ausnahme = [z for z in zeilen if '[Ausnahme]' in z]
    if ausnahme:
        return 'ungueltig', 'Produktivcode warf: ' + ausnahme[0].strip()[:50]
    if not zeilen:
        return 'ungueltig', 'rot ohne inhaltliche Pruefung'
    if erwartet and not any(erwartet in z for z in zeilen):
        return 'ungueltig', ('erwartete Pruefung "%s" blieb gruen; rot war: %s'
                             % (erwartet[:30], zeilen[0].strip()[:40]))
    return 'gefangen', zeilen[0].strip()[:66]


gefangen, probleme = 0, []
klassifizierer_ok = True
try:
    for name, datei, alt, neu, erwartet in MUTATIONEN:
        art, warum = bewerte(datei, alt, neu, erwartet)
        if art == 'gefangen':
            print('  gefangen       %s' % name)
            gefangen += 1
        else:
            print('  %-12s   %s  (%s)' % (art.upper(), name, warum))
            probleme.append('%s [%s: %s]' % (name, art, warum))
    if UNGUELTIG_ERWARTET:
        print('  -- Gegenprobe am Urteil dieses Tests --')
    for name, datei, alt, neu in UNGUELTIG_ERWARTET:
        art, warum = bewerte(datei, alt, neu)
        if art == 'ungueltig':
            print('  richtig verworfen  %s  (%s)' % (name, warum))
        else:
            print('  FALSCH EINGEORDNET %s  -> %s' % (name, art))
            probleme.append('%s [als %s verbucht]' % (name, art))
            klassifizierer_ok = False
finally:
    for _d, _b in ROH.items():
        io.open(_d, 'wb').write(_b)

for _d, _b in ROH.items():
    assert io.open(_d, 'rb').read() == _b, 'WIEDERHERSTELLUNG FEHLGESCHLAGEN: ' + _d
nach = subprocess.run(['py', '-3.14', PROBE], capture_output=True, text=True)

print()
print('wiederhergestellt: Zwillingstest laeuft wieder gruen' if nach.returncode == 0
      else 'WARNUNG: Zwillingstest nach der Wiederherstellung ROT!')
print('%d von %d Mutationen gefangen' % (gefangen, len(MUTATIONEN)))
for p in probleme:
    print('  ' + p)
sys.exit(0 if (gefangen == len(MUTATIONEN) and klassifizierer_ok
               and nach.returncode == 0) else 1)
