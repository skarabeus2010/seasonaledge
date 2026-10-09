# -*- coding: utf-8 -*-
"""Prueft den Waechter, nicht den Code: baut die vier Teile von Befund 14 wieder
ein und verlangt, dass probe_polymarket_fedverteilung.js ROT wird.

    py -3.14 scripts/verify_polymarket_fedverteilung_mutation.py

Vier Beweisregeln: `[Aufbau]` gerissen = Geruest zerstoert · Endmarker muss
erreicht sein · jede Mutation BENENNT die Pruefung, die sie reissen muss · eine
Ausnahme gilt nie als Nachweis. Dazu `UNGUELTIG_ERWARTET`, das das Urteil dieses
Tests selbst prueft.
"""
from __future__ import annotations

import io
import re
import subprocess
import pathlib
import sys

# Atomares Schreiben mit Wiederholung — IMPORTIERT, nicht kopiert.
# Ohne flush/fsync/os.replace liest der Unterprozess unter Windows
# gelegentlich noch den alten Inhalt, und der Test wird nicht
# deterministisch (beobachtet am 2026-10-09).
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from scripts.verify_twins_mutation import _atomar_schreiben  # noqa: E402

if hasattr(sys.stdout, 'reconfigure'):          # cp1252 kann die
    sys.stdout.reconfigure(encoding='utf-8')     # Mutationsnamen nicht
if hasattr(sys.stderr, 'reconfigure'):          # ausgeben; ohne das
    sys.stderr.reconfigure(encoding='utf-8')     # bricht der Lauf ab.

JS = 'landing/js/polymarket.js'
HTML = 'landing/pages/polymarket.html'
PROBE = 'scripts/js/probe_polymarket_fedverteilung.js'

MUTATIONEN = [
    # Teil 1: Balken wieder auf rohen Preisen.
    ('Urzustand — das Chart zeichnet wieder die ROHEN Preise',
     JS,
     "    var quelle = fedStats.distNorm || fedStats.dist || {};",
     "    var quelle = fedStats.dist || {};",
     'der Balken fuer 2 Cuts zeigt'),

    ('Die normierte Verteilung wird nicht mehr geliefert',
     JS,
     "      distNorm: distNorm,",
     "      distNorm: null,",
     'eine normierte Verteilung wird geliefert'),

    ('Normierung durch 1 statt durch die Preissumme',
     JS,
     "      distNorm[k] = totalProb > 0 ? dist[k] / totalProb : 0;",
     "      distNorm[k] = dist[k];",
     'die normierte Verteilung summiert zu 1'),

    # Teil 2: Untergrenze.
    ('Der Erwartungswert gilt wieder als exakt',
     JS,
     "      istUntergrenze: tail > 0,",
     "      istUntergrenze: false,",
     'mit 5 % auf 12+ ist es eine Untergrenze'),

    ('Die Untergrenze gilt immer, auch ohne Masse auf 12+',
     JS,
     "      istUntergrenze: tail > 0,",
     "      istUntergrenze: true,",
     'ohne Masse auf 12+ ist es exakt'),

    # Teil 3: Luecken.
    ('Luecken werden nicht mehr eingesetzt',
     JS,
     "        data: mitLuecken(byKey[c] || []),",
     "        data: byKey[c] || [],",
     'Lueckenpunkt'),

    ('Lueckenschwelle so hoch, dass keine Luecke mehr erkannt wird',
     JS,
     "    lueckeTage: 2",
     "    lueckeTage: 999",
     'Lueckenpunkt'),

    ('Lueckenschwelle so niedrig, dass JEDER Tag eine Luecke ist',
     JS,
     "    lueckeTage: 2",
     "    lueckeTage: 0",
     'kein eingefuegter Nullwert'),

    # Die Hoehe 340 gehoert nur zum Fed-Trend-Chart. Ohne sie traf der Anker
    # BEIDE Charts — und ein Anker, der zweimal passt, wird nicht angewandt,
    # die Mutation prueefte also nichts.
    ('Die Kurve glaettet wieder',
     JS,
     "height: 340, zoom: { enabled: false } }, SA.chartTheme.chart),\n"
     "      stroke: { width: 2, curve: 'straight' },",
     "height: 340, zoom: { enabled: false } }, SA.chartTheme.chart),\n"
     "      stroke: { width: 2, curve: 'smooth' },",
     'die Linie erfindet keine Kruemmung'),

    # Nachtrag aus der Abnahme 2026-10-08: beide Luecken gehoeren geprueft, und
    # das ≥-Zeichen muss SICHTBAR werden, nicht nur im Rueckgabewert stehen.
    ('Der allgemeine Historien-Renderer verbindet wieder ueber Luecken',
     JS,
     "        data: mitLuecken(buckets[cid]),",
     "        data: buckets[cid],",
     'Punkte (allgemein)'),

    ('Die Chart-Annotation verliert die Untergrenze',
     JS,
     # Die Datei traegt die ESCAPE-FORM `\\u2265`, nicht das Zeichen. Ein Anker
     # mit dem Zeichen trifft nicht — gemeldet als „Anker 0x gefunden".
     "            text: (fedStats.istUntergrenze ? '\\u2265 ' : '')",
     "            text: ('')",
     'beginnt die Annotation mit dem Groesser-gleich'),

    ('Die Annotation traegt die Untergrenze immer',
     JS,
     "            text: (fedStats.istUntergrenze ? '\\u2265 ' : '')",
     "            text: ('\\u2265 ')",
     'steht kein Groesser-gleich davor'),

    ('Das Groesser-gleich-Zeichen verschwindet aus der sichtbaren Kennzahl',
     HTML,
     "      var vorz = fedStats.istUntergrenze ? '≥ ' : '';",
     "      var vorz = '';",
     'wird aus istUntergrenze abgeleitet'),

    ('Das Groesser-gleich-Zeichen steht nur noch vor einer Kennzahl',
     HTML,
     "            vorz + expBps.toFixed(0) + ' bps', '') +",
     "            expBps.toFixed(0) + ' bps', '') +",
     'es steht vor BEIDEN Erwartungswert-Kennzahlen'),

    # Teil 4: Altersgrenze der Grundlinie.
    ('Urzustand — die Grundlinie darf beliebig alt sein',
     HTML,
     "        if (t < stichtag && t >= aeltesteErlaubt) {",
     "        if (t < stichtag) {",
     'ein 60 Tage alter Punkt gilt NICHT'),

    ('Toleranz so gross, dass die Grenze wirkungslos ist',
     HTML,
     "      var TOLERANZ_TAGE = 3;   // Kadenz ist taeglich; drei Tage deckt einen Ausfall",
     "      var TOLERANZ_TAGE = 365;   // Kadenz ist taeglich; drei Tage deckt einen Ausfall",
     'ein 60 Tage alter Punkt gilt NICHT'),

    ('Der Stichtag entfaellt — auch jüngere Punkte zaehlen',
     HTML,
     "        if (t < stichtag && t >= aeltesteErlaubt) {",
     "        if (t >= aeltesteErlaubt) {",
     'ein 2 Tage alter Punkt gilt nicht'),
]

UNGUELTIG_ERWARTET = [
    ('Ausnahme statt Verhaltensaenderung',
     JS,
     "    var dist = {};\n    var totalProb = 0, weighted = 0;",
     "    var dist = null.x;\n    var totalProb = 0, weighted = 0;"),
]

ROH = {JS: io.open(JS, 'rb').read(), HTML: io.open(HTML, 'rb').read()}


def anker(datei: str, text: str) -> bytes:
    roh = ROH[datei]
    if roh.count(b'\r\n') > roh.count(b'\n') // 2:
        text = text.replace('\r\n', '\n').replace('\n', '\r\n')
    return text.encode('utf-8')


basis = subprocess.run(['node', PROBE], capture_output=True, text=True)
if basis.returncode != 0:
    print('ABBRUCH: die Probe ist schon ohne Mutation rot.')
    print(basis.stdout[-1500:])
    sys.exit(1)
_m = re.search(r'PROBE-ENDE (\d+) Pruefungen', basis.stdout or '')
if not _m:
    print('ABBRUCH: die Probe meldet keinen Endmarker.')
    sys.exit(1)
print('Grundlinie: Probe ohne Mutation gruen, %s Pruefungen\n' % _m.group(1))


def bewerte(datei, alt, neu, erwartet=None):
    a = anker(datei, alt)
    n = ROH[datei].count(a)
    if n != 1:
        return 'kein-anker', 'Anker %dx gefunden, erwartet 1x' % n
    _atomar_schreiben(pathlib.Path(datei), ROH[datei].replace(a, anker(datei, neu), 1))
    try:
        r = subprocess.run(['node', PROBE], capture_output=True, text=True)
    finally:
        _atomar_schreiben(pathlib.Path(datei), ROH[datei])
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
    for d, b in ROH.items():
        _atomar_schreiben(pathlib.Path(d), b)
for d, b in ROH.items():
    assert io.open(d, 'rb').read() == b, 'WIEDERHERSTELLUNG FEHLGESCHLAGEN: ' + d
nach = subprocess.run(['node', PROBE], capture_output=True, text=True)

print()
print('wiederhergestellt: Probe laeuft wieder gruen' if nach.returncode == 0
      else 'WARNUNG: Probe nach der Wiederherstellung ROT!')
print('%d von %d Mutationen gefangen' % (gefangen, len(MUTATIONEN)))
for p in probleme:
    print('  ' + p)
sys.exit(0 if (gefangen == len(MUTATIONEN) and klassifizierer_ok
               and nach.returncode == 0) else 1)
