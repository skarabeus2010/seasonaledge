# -*- coding: utf-8 -*-
"""Prueft den Waechter, nicht den Code: baut Befund 12 wieder ein und verlangt,
dass probe_polymarket_kalibrierung.js ROT wird.

    py -3.14 scripts/verify_polymarket_kalibrierung_mutation.py

Was dieser Test NICHT leisten kann: pruefen, ob ein Text zu viel behauptet. Das
ist Sache des Lesens. Geprueft wird, dass die Einstufung aus den DATEN kommt,
dass die Basisrate richtig beschriftet ist und dass die Offenlegung der
Stichprobe die tatsaechlichen Auswahlkriterien nennt.

Vier Beweisregeln wie in den uebrigen Mutationstests.
"""
from __future__ import annotations

import io
import json
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

HTML = 'landing/pages/polymarket.html'
EN = 'landing/i18n/en.json'
PROBE = 'scripts/js/probe_polymarket_kalibrierung.js'

MUTATIONEN = [
    # NICHT der Urzustand — das hat Codex an HEAD widerlegt: die Einstufung war
    # dort schon aus `delta` gerechnet. Der Fall bleibt wertvoll (er haelt sie
    # datengetrieben), aber der Name behauptete mehr als er prueft.
    ('Die Einstufung wird fest eingebaut',
     HTML,
     "      var verdict = delta > 0.02 ? t('pmjs.brier_informativ', 'informativ')",
     "      var verdict = true ? t('pmjs.brier_informativ', 'informativ')",
     'alle drei Datensaetze fuehren zu VERSCHIEDENEN Einstufungen'),

    ('Die Schwelle fuer „deutlich" auf 0 — knapp wird zu deutlich',
     HTML,
     "      var verdict = delta > 0.02 ? t('pmjs.brier_informativ', 'informativ')",
     "      var verdict = delta > 0 ? t('pmjs.brier_informativ', 'informativ')",
     'ergibt nur'),

    ('Schlechter als die Basisrate gilt wieder als informativ',
     HTML,
     "        : (delta > 0 ? t('pmjs.brier_schwach', 'schwach informativ')\n"
     "                     : t('pmjs.brier_nicht_besser', 'nicht besser als Basisrate'));",
     "        : t('pmjs.brier_schwach', 'schwach informativ');",
     'Brier 0,30 gegen 0,25'),

    ('Der Abstand zur Basisrate verschwindet aus den Kennzahlen',
     HTML,
     "        [t('pmjs.brier_vs_basis', 'vs. Basisrate'),",
     "        [t('pmjs.brier_weg', 'weg'),",
     'der Abstand zur Basisrate ist eine eigene Kennzahl'),

    # Der ECHTE Urzustand von Befund 12: ein fester Bereich als Qualitaetsurteil,
    # ohne Bezug auf die Basisrate der Stichprobe.
    ('Urzustand — absolutes Qualitaetsband zurueck im Fliesstext',
     HTML,
     "          <b>Woran man ihn messen muss:</b> an der Basisrate <b>dieser</b> Stichprobe.",
     "          <span style=\"color:var(--accent)\">0.15&ndash;0.20</span> = gut kalibriert &middot;",
     'behauptet keinen festen Bereich'),

    # Abnahme Runde 5: die verdoppelten Diagramme.
    ('Das Kalibrierungs-Diagramm wird nicht mehr festgehalten',
     HTML,
     "      destroyChart('calibration');",
     "      void 0;",
     'zerstoert dabei genau das alte'),

    ('Das Zeitfaecher-Diagramm wird nicht mehr festgehalten',
     HTML,
     "      destroyChart('timeBuckets');",
     "      void 0;",
     'Zeitfaecher: der zweite Aufbau zerstoert das alte'),

    ('Die Offenlegung der Stichprobe wird von der Seite entfernt',
     HTML,
     'data-i18n-html="pm.calibration_stichprobe"',
     'data-i18n-html="pm.calibration_entfernt"',
     'die deutsche Seite traegt den Offenlegungsblock'),

    # Die Beschriftung der Basisrate, auf der EN-Seite.
    ('Die EN-Beschriftung behauptet wieder „resolutions"',
     EN,
     '"pmjs.brier_anteil": "share of YES per forecast day"',
     '"pmjs.brier_anteil": "share of YES resolutions"',
     'die EN-Beschriftung sagt NICHT'),

    ('Die Offenlegung nennt die Volumenschwelle nicht mehr',
     EN,
     'at least $10,000 in volume',
     'with sufficient volume',
     'EN nennt die Volumenschwelle'),

    ('Die Offenlegung verschweigt die Gewichtung je Prognosetag',
     EN,
     'the share of YES across all <b>forecast days</b>',
     'the share of YES across all resolutions',
     'EN nennt die Gewichtung je Prognosetag'),
]

UNGUELTIG_ERWARTET = [
    ('Ausnahme statt Verhaltensaenderung',
     HTML,
     "      var delta = (o.baseline_brier - o.brier);",
     "      var delta = null.x - o.brier;"),
]

ROH = {HTML: io.open(HTML, 'rb').read(), EN: io.open(EN, 'rb').read()}


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
# Die EN-Datei muss nach allem noch gueltiges JSON sein.
json.load(io.open(EN, encoding='utf-8'))
nach = subprocess.run(['node', PROBE], capture_output=True, text=True)

print()
print('wiederhergestellt: Probe laeuft wieder gruen' if nach.returncode == 0
      else 'WARNUNG: Probe nach der Wiederherstellung ROT!')
print('%d von %d Mutationen gefangen' % (gefangen, len(MUTATIONEN)))
for p in probleme:
    print('  ' + p)
sys.exit(0 if (gefangen == len(MUTATIONEN) and klassifizierer_ok
               and nach.returncode == 0) else 1)
