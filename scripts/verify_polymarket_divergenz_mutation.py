# -*- coding: utf-8 -*-
"""Prueft den Waechter, nicht den Code: baut die Teile von Befund 13 wieder ein
und verlangt, dass probe_polymarket_divergenz.js ROT wird.

    py -3.14 scripts/verify_polymarket_divergenz_mutation.py

Was dieser Test NICHT leisten kann: pruefen, ob ein Text zu viel behauptet. Das
ist Sache des Lesens. Geprueft wird, dass die Fallzahl an der Zahl steht, dass
der Prior in ganzen Prozent erscheint, dass die redaktionelle Schwelle aus dem
Vertrag kommt und wirkt, und dass ein unvollstaendiges Vergleichsjahr nicht
mitzaehlt.

Vier Beweisregeln wie in den uebrigen Mutationstests: `[Aufbau]` gerissen =
Geruest zerstoert · Endmarker muss erreicht sein · jede Mutation BENENNT die
Pruefung, die sie reissen muss · eine Ausnahme gilt nie als Nachweis. Dazu
`UNGUELTIG_ERWARTET`, das das Urteil dieses Tests selbst prueft.
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
PROBE = 'scripts/js/probe_polymarket_divergenz.js'

MUTATIONEN = [
    # Der Urzustand des Befundes: die Richtungsbehauptung.
    ('Urzustand — „Markt unterschaetzt" statt der Richtung des Abstands',
     JS,
     "          verdict = SA.i18n.t('pmjs.verdict_seasonal_above', 'Prior über Markt'); cls = 'pos';",
     "          verdict = SA.i18n.t('pmjs.verdict_seasonal_above', "
     "'Saisonal > Markt · Markt unterschaetzt'); cls = 'pos';",
     'Abstand 4 pp nennt eine Richtung'),

    # Die Fallzahl.
    ('Die Fallzahl verschwindet hinter dem Prior',
     JS,
     "        ? (Math.round(r.priorProb * 100) + '% <span style=\"color:var(--muted)\">('\n"
     "           + r.priorK + '/' + r.priorN + ')</span>')",
     "        ? (Math.round(r.priorProb * 100) + '%')",
     'die Fallzahl 2/5 steht an der Zahl'),

    ('Die Fallzahl wird nicht mehr gezaehlt',
     JS,
     "      var priorK = (priorProb != null)\n"
     "        ? empiricalAboveCount(histData.samples, requiredRet) : null;",
     "      var priorK = null;",
     'die Fallzahl 2/5 steht an der Zahl'),

    ('Die Zaehlung nimmt alle Jahre statt der Treffer',
     JS,
     "  function empiricalAboveCount(samples, targetReturn) {\n"
     "    return samples.filter(function(s) { return s.ret >= targetReturn; }).length;",
     "  function empiricalAboveCount(samples, targetReturn) {\n"
     "    return samples.length;",
     'die Fallzahl 2/5 steht an der Zahl'),

    # Die Rundung.
    ('Der Prior bekommt wieder eine Dezimalstelle',
     JS,
     "        ? (Math.round(r.priorProb * 100) + '% <span style=\"color:var(--muted)\">('",
     "        ? ((r.priorProb * 100).toFixed(1) + '% <span style=\"color:var(--muted)\">('",
     'keine Dezimalstelle am Prior'),

    # Die redaktionelle Schwelle.
    ('Die Schwelle steht wieder als Zahl im Code statt im Vertrag',
     JS,
     "        if (Math.abs(diverge) < VERTRAG.divergenzSchwellePp) {",
     "        if (Math.abs(diverge) < 3) {",
     'die Schwelle wird aus dem Vertrag gelesen'),

    ('Die Schwelle auf 0 — jeder Abstand nennt eine Richtung',
     JS,
     "    divergenzSchwellePp: 3",
     "    divergenzSchwellePp: 0",
     'Abstand 2 pp bleibt ohne Richtung'),

    ('Die Schwelle auf 50 — kein Abstand nennt mehr eine Richtung',
     JS,
     "    divergenzSchwellePp: 3",
     "    divergenzSchwellePp: 50",
     'Abstand 4 pp nennt eine Richtung'),

    # Die Richtung selbst.
    ('Die beiden Richtungen werden vertauscht',
     JS,
     "          verdict = SA.i18n.t('pmjs.verdict_seasonal_above', 'Prior über Markt'); cls = 'pos';",
     "          verdict = SA.i18n.t('pmjs.verdict_market_above', 'Markt über Prior'); cls = 'pos';",
     'VERSCHIEDENEN Bewertungen'),

    # Das vollstaendige Vergleichsfenster (der substanzielle Teil).
    ('Das im Juni endende Jahr zaehlt wieder mit',
     JS,
     "      var endPrice = (letzte && letzte.d.getUTCMonth() === VERTRAG.jahresendeMonat)\n"
     "        ? letzte.close : null;",
     "      var endPrice = letzte ? letzte.close : null;",
     'endet es im Juni, zaehlt es NICHT'),
]

UNGUELTIG_ERWARTET = [
    # Eine Ausnahme ist kein Nachweis: der Test muss sie als ungueltig
    # verbuchen, nicht als gefangene Mutation.
    ('Ausnahme statt Verhaltensaenderung',
     JS,
     "      var diverge = null, verdict = '—', cls = '';",
     "      var diverge = null.x, verdict = '—', cls = '';"),
]

ROH = {JS: io.open(JS, 'rb').read()}


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
