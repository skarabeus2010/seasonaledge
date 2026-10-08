# -*- coding: utf-8 -*-
"""Prueft den Waechter, nicht den Code: erzeugt selbst eine Woerterbuch-
Aenderung ohne neue Cache-Kennung und verlangt, dass
verify_i18n_cache_version.py ROT wird.

    py -3.14 scripts/verify_i18n_cache_mutation.py

Die erste Fassung verglich den Arbeitsbaum gegen HEAD und beendete sich
erfolgreich, sobald beide dieselbe Kennung trugen — also genau nach dem Commit,
auf den es ankommt. „3/3 gefangen" war damit eine Aussage ueber den Zustand des
Arbeitsbaums und keine ueber den Waechter (Codex, Abnahme Runde 3). Dieser Test
stellt den Fall deshalb SELBST her: er aendert ein Woerterbuch und laesst die
Kennung, wie sie ist.

Beweisregeln wie in den uebrigen Mutationstests; zusaetzlich wird die
Wiederherstellung beider Dateien nachgewiesen.
"""
from __future__ import annotations

import io
import json
import re
import subprocess
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

JS = 'landing/js/i18n.js'
EN = 'landing/i18n/en.json'
PROBE = 'scripts/verify_i18n_cache_version.py'

ROH = {JS: io.open(JS, 'rb').read(), EN: io.open(EN, 'rb').read()}


def kennung(b: bytes) -> str:
    m = re.search(rb"var\s+_JSON_VER\s*=\s*'([^']+)'", b)
    assert m, 'ABBRUCH: _JSON_VER nicht in i18n.js gefunden.'
    return m.group(1).decode('utf-8')


def lauf() -> tuple[int, str]:
    r = subprocess.run(['py', '-3.14', PROBE], capture_output=True, text=True)
    return r.returncode, (r.stdout or '') + (r.stderr or '')


def zeilenende(b: bytes) -> bytes:
    return b'\r\n' if b.count(b'\r\n') > b.count(b'\n') // 2 else b'\n'


def en_mit_zusatz() -> bytes:
    """en.json mit einem zusaetzlichen Schluessel, Format und Zeilenende wie
    das Original — eine inhaltliche Aenderung, nicht bloss Formatierung."""
    d = json.loads(ROH[EN].decode('utf-8'))
    d['pmjs.__mutationstest__'] = 'only for the mutation test'
    text = json.dumps(d, ensure_ascii=False, indent=2) + '\n'
    rohbytes = text.encode('utf-8')
    if zeilenende(ROH[EN]) == b'\r\n':
        rohbytes = rohbytes.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
    return rohbytes


def js_mit_kennung(wert: str) -> bytes:
    alt = ("var _JSON_VER = '%s';" % kennung(ROH[JS])).encode('utf-8')
    assert ROH[JS].count(alt) == 1
    return ROH[JS].replace(alt, ("var _JSON_VER = '%s';" % wert).encode('utf-8'), 1)


rc, ausgabe = lauf()
if rc != 0:
    print('ABBRUCH: der Waechter ist schon ohne Mutation rot.')
    print(ausgabe[-1200:])
    sys.exit(1)
if 'PROBE-ENDE' not in ausgabe:
    print('ABBRUCH: der Waechter meldet keinen Endmarker.')
    sys.exit(1)
print('Grundlinie: Waechter ohne Mutation gruen.\n')

IST = kennung(ROH[JS])
# Die Kennung des HEAD-Stands: der Waechter vergleicht dagegen, also muss die
# Mutation DORTHIN zurueckdrehen. Mit der aktuellen Kennung waere der Fall
# „geaendert UND erhoeht" — und damit zu Recht gruen.
_r = subprocess.run(['git', 'show', 'HEAD:' + JS], capture_output=True)
if _r.returncode != 0:
    print('ABBRUCH: HEAD-Fassung von %s nicht lesbar — UNGEPRUEFT.' % JS)
    sys.exit(1)
KOPF = kennung(_r.stdout)

# Jede Mutation: {datei: neue Bytes}, dazu der Text, der rot werden MUSS.
MUTATIONEN = [
    # Der eigentliche Fall: ein Woerterbuch aendert sich, die Kennung nicht.
    ('Woerterbuch geaendert, Kennung auf dem HEAD-Stand',
     {EN: en_mit_zusatz(), JS: js_mit_kennung(KOPF)},
     'die Cache-Kennung wurde erhoeht'),

    # Dieselbe Aenderung MIT erhoehter Kennung muss gruen bleiben — sonst
    # prueft der Waechter nicht die Kennung, sondern bloss die Aenderung.
    ('Woerterbuch geaendert UND Kennung erhoeht (muss gruen bleiben)',
     {EN: en_mit_zusatz(), JS: js_mit_kennung(IST + 'x')},
     None),

    ('Die Kennung steckt nicht mehr im sessionStorage-Schluessel',
     {JS: ROH[JS].replace(b"'sa-i18n-' + _JSON_VER", b"'sa-i18n-fest'", 1)},
     'die Kennung steckt im sessionStorage-Schluessel'),

    ('Die Kennung haengt nicht mehr am Abruf',
     {JS: ROH[JS].replace(b"?v=' + _JSON_VER", b"?v=fest'", 1)},
     'die Kennung haengt am Abruf'),
]

gefangen, probleme = 0, []
try:
    for name, dateien, erwartet in MUTATIONEN:
        # Nur wenn KEINE der Dateien sich aendert, prueft die Mutation nichts.
        # Eine einzelne unveraenderte Datei ist in Ordnung: `js_mit_kennung`
        # ist ein Nulleingriff, wenn die Kennung schon auf dem HEAD-Stand steht
        # (also nach dem Commit) — und dann traegt die en.json-Aenderung den
        # Fall allein.
        if all(b == ROH[d] for d, b in dateien.items()):
            probleme.append('%s [kein-anker: Mutation ohne Wirkung]' % name)
            print('  KEIN-ANKER     %s (Mutation aenderte nichts)' % name)
        else:
            for d, b in dateien.items():
                io.open(d, 'wb').write(b)
            try:
                rc, ausgabe = lauf()
            finally:
                for d, b in ROH.items():
                    io.open(d, 'wb').write(b)

            if erwartet is None:
                # Gegenprobe: dieser Fall MUSS gruen bleiben.
                if rc == 0:
                    print('  richtig gruen  %s' % name)
                    gefangen += 1
                else:
                    print('  FALSCH ROT     %s' % name)
                    probleme.append('%s [faelschlich rot]' % name)
                continue

            if rc == 0:
                print('  ENTWISCHT      %s (Waechter blieb gruen)' % name)
                probleme.append('%s [entwischt]' % name)
                continue
            if 'PROBE-ENDE' not in ausgabe:
                print('  UNGUELTIG      %s (Waechter brach ab)' % name)
                probleme.append('%s [ungueltig: Abbruch]' % name)
                continue
            zeilen = [z for z in ausgabe.splitlines() if 'FEHL ' in z]
            if any('[Aufbau]' in z for z in zeilen):
                print('  UNGUELTIG      %s (Aufbaupruefung gerissen)' % name)
                probleme.append('%s [ungueltig: Aufbau]' % name)
                continue
            if not any(erwartet in z for z in zeilen):
                print('  UNGUELTIG      %s (erwartete Pruefung blieb gruen; rot '
                      'war: %s)' % (name, (zeilen or ['-'])[0].strip()[:40]))
                probleme.append('%s [ungueltig: falsche Pruefung]' % name)
                continue
            print('  gefangen       %s' % name)
            gefangen += 1
finally:
    for d, b in ROH.items():
        io.open(d, 'wb').write(b)

for d, b in ROH.items():
    assert io.open(d, 'rb').read() == b, 'WIEDERHERSTELLUNG FEHLGESCHLAGEN: ' + d
json.load(io.open(EN, encoding='utf-8'))   # muss noch gueltiges JSON sein
rc_nach, _ = lauf()

# ── Die flache Historie, als eigener Fall ───────────────────────────────────
# Codex' Reproduktion aus Runde 3: ein Checkout mit `fetch-depth: 1` hat kein
# HEAD~1. Die erste Fassung des Waechters wertete das als folgenlos und lief
# gruen durch — und `rev-list --count HEAD` liefert im flachen Klon ebenfalls 1,
# also half auch die Erkennung „erster Commit" nicht weiter.
import os
import pathlib
import shutil
import tempfile

# `git clone --depth` wird bei einem LOKALEN Pfad ignoriert (git nutzt dann
# Hardlinks und uebertraegt die ganze Historie). Nur ueber `file://` entsteht
# wirklich ein flacher Klon — ohne das lief dieser Fall gruen durch und
# bewies nichts.
_URL = pathlib.Path('.').resolve().as_uri()

print()
print('Gegenprobe: flache Historie muss UNGEPRUEFT melden')
_mit = tempfile.mkdtemp()
try:
    _flach = os.path.join(_mit, 'flach')
    _rk = subprocess.run(['git', 'clone', '--depth', '1', _URL, _flach],
                         capture_output=True, text=True)
    if _rk.returncode != 0:
        print('  UNGUELTIG      flacher Klon nicht erstellbar — Fall ungeprueft')
        probleme.append('flache Historie [ungueltig: kein Klon]')
    else:
        os.makedirs(os.path.join(_flach, 'scripts'), exist_ok=True)
        shutil.copy(PROBE, os.path.join(_flach, 'scripts'))
        _rf = subprocess.run(['py', '-3.14', PROBE], cwd=_flach,
                             capture_output=True, text=True)
        _aus = (_rf.stdout or '') + (_rf.stderr or '')
        _tief = subprocess.run(['git', 'clone', '--depth', '2', _URL,
                                os.path.join(_mit, 'tief')],
                               capture_output=True, text=True)
        _ok_tief = None
        if _tief.returncode == 0:
            os.makedirs(os.path.join(_mit, 'tief', 'scripts'), exist_ok=True)
            shutil.copy(PROBE, os.path.join(_mit, 'tief', 'scripts'))
            _rt = subprocess.run(['py', '-3.14', PROBE],
                                 cwd=os.path.join(_mit, 'tief'),
                                 capture_output=True, text=True)
            _ok_tief = _rt.returncode == 0
        if _rf.returncode != 0 and 'UNGEPRUEFT' in _aus and _ok_tief is True:
            print('  gefangen       flache Historie ist rot, Tiefe 2 ist gruen')
            gefangen += 1
        else:
            print('  ENTWISCHT      flache Historie (EXIT=%s, Tiefe-2-gruen=%s)'
                  % (_rf.returncode, _ok_tief))
            probleme.append('flache Historie [entwischt]')
finally:
    shutil.rmtree(_mit, ignore_errors=True)
ERWARTET_FAELLE = len(MUTATIONEN) + 1

print()
print('wiederhergestellt: Waechter laeuft wieder gruen' if rc_nach == 0
      else 'WARNUNG: Waechter nach der Wiederherstellung ROT!')
print('%d von %d Faellen wie erwartet' % (gefangen, ERWARTET_FAELLE))
for p in probleme:
    print('  ' + p)
sys.exit(0 if (gefangen == ERWARTET_FAELLE and rc_nach == 0) else 1)
