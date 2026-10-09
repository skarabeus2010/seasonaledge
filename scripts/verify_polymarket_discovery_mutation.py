# -*- coding: utf-8 -*-
"""Prueft den Waechter, nicht den Code: baut Befund 16 wieder ein und verlangt,
dass verify_polymarket_discovery.py ROT wird.

    py -3.14 scripts/verify_polymarket_discovery_mutation.py

Vier Regeln entscheiden, ob das Rot einer Mutation etwas BEWEIST (Mechanik aus
der Maskierungs-Runde): eine gerissene `[Aufbau]`-Pruefung bedeutet ein
zerstoertes Geruest; die Probe muss ihren Endmarker erreichen; jede Mutation
benennt die Pruefung, die sie reissen muss; und eine Ausnahme gilt nie als
Nachweis, weil eine echte Regression nicht wirft.
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

DISC = 'scripts/polymarket_discover.py'
DATA = 'shared/polymarket_data.py'
PROBE = 'scripts/verify_polymarket_discovery.py'

MUTATIONEN = [
    # Der Urzustand: Summe statt Paar. Damit ersetzt Liquiditaet die Passung.
    ('Urzustand — Summe aus Treffern und Liquiditaet',
     DISC,
     "    return hits, liq_score",
     "    return hits + liq_score, 0.0",
     'erste Komponente ist eine reine Trefferzahl'),

    ('Eignung nicht mehr an Treffern gemessen',
     DISC,
     '    if treffer < MIN_TREFFER:',
     '    if False:',
     '1000 USD gilt NICHT als geeignet'),

    ('Fail-closed ohne Suchbegriffe aufgehoben',
     DISC,
     "    if not search_terms:\n        return False",
     "    if not search_terms:\n        return True",
     'ohne Suchbegriffe ist NICHTS geeignet'),

    ('Mindestzahl auf 0 gesenkt — jeder Markt passt',
     DISC,
     "MIN_TREFFER = 1",
     "MIN_TREFFER = 0",
     '1000 USD gilt NICHT als geeignet'),

    ('Liquiditaetsrang verworfen — die Ordnung verschwindet',
     DISC,
     "    liq_score = min(1.0, math.log10(max(1.0, liquidity)) / 6.0) if liquidity > 0 else 0.0",
     "    liq_score = 0.0",
     'der liquidere Markt rangiert vor dem duennen'),

    # Nachtrag aus der Abnahme 2026-10-08.
    ('Die Jahreszahl ist wieder nur einer von mehreren Treffern',
     DISC,
     '    jahre = jahresbegriffe(search_terms)',
     '    jahre = []',
     'das falsche Jahr ist NICHT geeignet'),

    ('Ohne Markttext gilt der Kandidat wieder als geeignet',
     DISC,
     '        if not any(j.lower() in text for j in jahre):',
     '        if text and not any(j.lower() in text for j in jahre):',
     'ohne Markttext laesst sich das Jahr nicht belegen'),

    # Abnahme Runde 2.
    ('Die Jahrespruefung liest wieder den ganzen Markttext',
     DISC,
     'if ist_geeignet(z[2], terms, kennungstext(z[1]))]',
     'if ist_geeignet(z[2], terms, markttext(z[1]))]',
     'keine Aufrufstelle uebergibt mehr den ganzen Markttext'),

    ('Die Kennung enthaelt wieder die Beschreibung',
     DISC,
     '        str(market.get("groupItemTitle", "")),\n    ]).lower()\n\n\ndef markttext',
     '        str(market.get("groupItemTitle", "")),\n        str(market.get("description", "")),\n    ]).lower()\n\n\ndef markttext',
     'die Kennung enthaelt die Beschreibung NICHT'),

    ('Die Jahreszahl zaehlt wieder als sachlicher Treffer',
     DISC,
     'if term.lower() not in jahre and term.lower() in text)',
     'if term.lower() in text)',
     'hat 0 sachliche Treffer'),

    ('Die Bewertung liefert bei leerem Text wieder einen float',
     DISC,
     '        return 0, 0.0',
     '        return 0.0',
     'ergibt (0, 0.0), nicht einen float'),

    ('YES und NO werden wieder nach der Position zugeordnet',
     DATA,
     '        if i_ja is not None and i_nein is not None and i_ja != i_nein:',
     '        if False:',
     'No zuerst'),
]

UNGUELTIG_ERWARTET = [
    # Loest nur eine Ausnahme aus, aendert kein Verhalten.
    ('Ausnahme statt Verhaltensaenderung',
     DISC,
     "    liquidity = 0.0\n    try:",
     "    liquidity = None.real\n    try:"),
]

ROH = {DISC: io.open(DISC, 'rb').read(), DATA: io.open(DATA, 'rb').read()}


def anker(datei: str, text: str) -> bytes:
    roh = ROH[datei]
    if roh.count(b'\r\n') > roh.count(b'\n') // 2:
        text = text.replace('\r\n', '\n').replace('\n', '\r\n')
    return text.encode('utf-8')


basis = subprocess.run(['py', '-3.14', PROBE], capture_output=True, text=True)
if basis.returncode != 0:
    print('ABBRUCH: die Probe ist schon ohne Mutation rot.')
    print(basis.stdout[-1200:])
    sys.exit(1)
_m = re.search(r'PROBE-ENDE (\d+) Pruefungen', basis.stdout or '')
if not _m:
    print('ABBRUCH: die Probe meldet keinen Endmarker.')
    sys.exit(1)
print('Grundlinie: Probe ohne Mutation gruen, %s Pruefungen\n' % _m.group(1))


def bewerte(datei: str, alt: str, neu: str, erwartet: str | None = None):
    a = anker(datei, alt)
    n = ROH[datei].count(a)
    if n != 1:
        return 'kein-anker', 'Anker %dx gefunden, erwartet 1x' % n
    _atomar_schreiben(pathlib.Path(datei), ROH[datei].replace(a, anker(datei, neu), 1))
    try:
        r = subprocess.run(['py', '-3.14', PROBE], capture_output=True, text=True)
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
        return 'ungueltig', ('erwartete Pruefung "%s" blieb gruen' % erwartet[:34])
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
        _atomar_schreiben(pathlib.Path(_d), _b)
for _d, _b in ROH.items():
    assert io.open(_d, 'rb').read() == _b, 'WIEDERHERSTELLUNG FEHLGESCHLAGEN: ' + _d
nach = subprocess.run(['py', '-3.14', PROBE], capture_output=True, text=True)

print()
print('wiederhergestellt: Probe laeuft wieder gruen' if nach.returncode == 0
      else 'WARNUNG: Probe nach der Wiederherstellung ROT!')
print('%d von %d Mutationen gefangen' % (gefangen, len(MUTATIONEN)))
for p in probleme:
    print('  ' + p)
sys.exit(0 if (gefangen == len(MUTATIONEN) and klassifizierer_ok
               and nach.returncode == 0) else 1)
