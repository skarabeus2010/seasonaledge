# -*- coding: utf-8 -*-
"""Prueft den Waechter, nicht den Code: baut die behobenen Fehler aus Befund 15
wieder ein und verlangt, dass probe_polymarket_abschnitte.js ROT wird.

    py -3.14 scripts/verify_polymarket_abschnitte_mutation.py

Vier Regeln entscheiden, ob das Rot einer Mutation etwas BEWEIST. Sie sind in
fuenf Codex-Runden am Maskierungs-Waechter entstanden und hier uebernommen:

  1. Reisst eine Pruefung mit der Kennung `[Aufbau]`, hat die Mutation das
     Geruest zerstoert und nicht das Verhalten geaendert.
  2. Die Probe muss ihren Endmarker erreichen — bricht sie unterwegs ab, war der
     beabsichtigte Fall nie geprueft.
  3. Jede Mutation BENENNT die Pruefung, die sie reissen muss. Reisst eine
     andere, ist sie rot aus unbeteiligtem Grund.
  4. Eine Ausnahme gilt nie als Nachweis — eine echte Regression wirft nicht.

Dazu `UNGUELTIG_ERWARTET`: Mutationen, die als ungueltig erkannt werden MUESSEN.
Sie pruefen das Urteil dieses Tests selbst.

Mehrzeilige Anker uebernehmen die Zeilenenden der Zieldatei — sie liegt mit
CRLF im Baum, und ein Anker mit "\\n" trifft darin nie.
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

HTML = 'landing/pages/polymarket.html'
PROBE = 'scripts/js/probe_polymarket_abschnitte.js'

# (Beschreibung, Datei, alt, neu, erwartete Pruefung)
MUTATIONEN = [
    ('Der Fed-Pfad wird wieder gerechnet, obwohl er nicht gezeigt wird',
     HTML,
     "          if (showFed) renderFedPath(state.history);",
     "          renderFedPath(state.history);",
     'renderFedPath NICHT gerufen'),

    ('Abschnitte werden nicht mehr geschaltet (der urspruengliche Befund 15)',
     HTML,
     "          abschnittSichtbar('fed', showFed);",
     "          /* abschnittSichtbar('fed', showFed); */",
     'Fed-Abschnitt verborgen'),

    ('Die leere Kategorie laesst die Abschnitte der vorigen stehen',
     HTML,
     "          abschnittSichtbar('fed', false);\n"
     "          abschnittSichtbar('risiko', false);\n"
     "          abschnittSichtbar('krypto', false);",
     "          /* nichts verbergen */",
     'nichts aus der vorigen Kategorie bleibt stehen'),

    ('Die Schleife laeuft ueber die naechste Ueberschrift hinaus',
     HTML,
     "        if (el && el.classList && el.classList.contains('section-hdr')) break;",
     "        /* keine Abbruchbedingung */",
     'der naechste Abschnitt bleibt sichtbar'),

    ('Die Fehlermeldung raeumt sich wieder selbst weg',
     HTML,
     "          clearError();\n          hideLoading();",
     "          hideLoading();",
     'nach Erfolg geraeumt'),

    # Die beiden Generationspruefungen einzeln, weil sie verschiedene
    # Zeitfenster schliessen. Dass die zweite ueberhaupt fehlte, ist beim
    # Schreiben der Probe aufgefallen.
    # Vom Mutationstest selbst aufgedeckt: diese Mutation blieb GRUEN, weil die
    # Schaltung bei unbekannter Kennung still zurueckkehrte. Sie gehoert damit
    # nicht zu den Gegenproben, sondern zu den echten Mutationen.
    ('Kennung einer Ueberschrift umbenannt — die Schaltung verpufft',
     HTML,
     'data-abschnitt="fed"',
     'data-abschnitt="fed-umbenannt"',
     'alle vier Abschnitte sind ueber ihre Kennung auffindbar'),

    # Die zwei Befunde, die Codex an den unveraenderten Seitenfunktionen
    # reproduziert hat — beide trafen meinen eigenen Fix.
    ('Generationspruefung im FEHLERPFAD entfernt',
     HTML,
     "        if (meineGeneration !== ladeGeneration) return;\n"
     "        hideLoading();\n"
     "        console.error('Polymarket load error', err);",
     "        hideLoading();\n"
     "        console.error('Polymarket load error', err);",
     'die verspaetete Ablehnung setzt KEINE Fehlermeldung'),

    ('Divergenz-Abschnitt nicht geschaltet (trug keine Kennung)',
     HTML,
     "          abschnittSichtbar('divergenz', showCrypto);",
     "          /* abschnittSichtbar('divergenz', showCrypto); */",
     'Divergenz-Abschnitt verborgen (haengt an Krypto)'),

    ('Erste Generationspruefung entfernt (Katalog)',
     HTML,
     "        if (meineGeneration !== ladeGeneration) return;   // ueberholt\n"
     "        var all = (catalog || [])",
     "        var all = (catalog || [])",
     'A hat state.markets NICHT ueberschrieben'),

    ('Generationspruefung wieder HINTER die Zustandsaenderung geschoben',
     HTML,
     "        if (meineGeneration !== ladeGeneration) return;   // ueberholt\n"
     "        var all = (catalog || []).filter(function(m) { return m.active !== false; });\n"
     "        state.allMarkets = all;\n"
     "        state.markets = applyCategoryFilter(all, cat);",
     "        var all = (catalog || []).filter(function(m) { return m.active !== false; });\n"
     "        state.allMarkets = all;\n"
     "        state.markets = applyCategoryFilter(all, cat);\n"
     "        if (meineGeneration !== ladeGeneration) return;   // ueberholt",
     'A hat state.markets NICHT ueberschrieben'),

    # Nachtrag aus der Abnahme 2026-10-08: die Divergenz-Tabelle hat ihre
    # eigene asynchrone Stufe, und die war ungeprueft.
    # Die Generation ERST NACH dem Warten lesen — dann ist sie immer die
    # aktuelle und die Sperre kann nie greifen. Genau so war der Fehler gebaut.
    # (Die naheliegendere Mutation — die Zeile ganz entfernen — erzeugt nur
    # einen ReferenceError und beweist nichts; sie wird von der fuenften
    # Beweisregel verworfen, siehe `ausnahme` in bewerte().)
    ('Die Divergenz-Tabelle liest die Generation erst nach dem Warten',
     HTML,
     "        if (meineGeneration !== ladeGeneration) return;   // ueberholt\n"
     "        if (!rows || !rows.length) {",
     "        meineGeneration = ladeGeneration;\n"
     "        if (meineGeneration !== ladeGeneration) return;   // ueberholt\n"
     "        if (!rows || !rows.length) {",
     'ueberschreibt den neuen Inhalt NICHT'),

    # Abnahme Runde 6: Codex' zwei Gegenproben an der Einbindung. Beide
    # kamen durch die frueher nur suchende Pruefung.
    ('Der Aufruf im Start wird auskommentiert',
     HTML,
     "      verdrahteUebersetzung();\n    }",
     "      // verdrahteUebersetzung();\n    }",
     'der AUSGEFUEHRTE Start registriert den Uebersetzungs-Zuhoerer'),

    ('Der Aufruf im Start wird unerreichbar gemacht',
     HTML,
     "      verdrahteUebersetzung();\n    }",
     "      if (false) verdrahteUebersetzung();\n    }",
     'der AUSGEFUEHRTE Start registriert den Uebersetzungs-Zuhoerer'),

    ('Der DOMContentLoaded-Block ruft den Start nicht mehr',
     HTML,
     "    document.addEventListener('DOMContentLoaded', starteSeite);",
     "    document.addEventListener('nie-gesendet', starteSeite);",
     'die Quelle registriert starteSeite auf DOMContentLoaded'),

    # Abnahme Runde 4: die Uebersetzung kommt spaeter als der erste Aufbau.
    ('Der Zuhoerer auf sa:i18n-bereit wird entfernt',
     HTML,
     "      document.addEventListener('sa:i18n-bereit', function() {",
     "      document.addEventListener('nie-gesendet', function() {",
     'registriert einen Zuhoerer auf sa:i18n-bereit'),

    ('Der Zuhoerer stoesst den Aufbau nicht mehr an',
     HTML,
     "        reload();\n        loadBrierStats();",
     "        void 0;",
     'stoesst den Aufbau erneut an'),

    ('Der Zuhoerer laesst die Brier-Ausgabe aus',
     HTML,
     "        reload();\n        loadBrierStats();",
     "        reload();",
     'Brier-Ausgabe ebenfalls, genau einmal'),

    ('Die Generationspruefung im FEHLERPFAD der Tabelle faellt weg',
     HTML,
     "      }).catch(function(err) {\n"
     "        if (meineGeneration !== ladeGeneration) return;   // ueberholt\n"
     "        console.error('Divergenz ' + ticker + ':', err);",
     "      }).catch(function(err) {\n"
     "        console.error('Divergenz ' + ticker + ':', err);",
     'setzt KEINE Fehlermeldung'),

    ('Die ZWEITE Generationspruefung im Ladelauf faellt weg',
     HTML,
     "          if (meineGeneration !== ladeGeneration) return;   // ueberholt\n"
     "          state.latest = results[0] || {};",
     "          state.latest = results[0] || {};",
     'E hat state.latest NICHT ueberschrieben'),

    ('Die Generationspruefung im Erfolgspfad der Tabelle faellt weg',
     HTML,
     "      SA.fetchAllPrices(ticker).then(function(rows) {\n"
     "        if (meineGeneration !== ladeGeneration) return;   // ueberholt",
     "      SA.fetchAllPrices(ticker).then(function(rows) {",
     'ueberschreibt den neuen Inhalt NICHT'),
]

# Diese muessen als UNGUELTIG erkannt werden, nicht als Erfolg.
UNGUELTIG_ERWARTET = [
    # Loest nur eine Ausnahme aus.
    ('Ausnahme statt Verhaltensaenderung',
     HTML,
     "      var kopf = document.querySelector('.section-hdr[data-abschnitt=\"' + name + '\"]');",
     "      var kopf = null.querySelector('x');"),
]

ROH = {HTML: io.open(HTML, 'rb').read()}


def anker(datei: str, text: str) -> bytes:
    """Zeilenenden der ZIELDATEI uebernehmen (die Datei liegt mit CRLF im Baum)."""
    roh = ROH[datei]
    if roh.count(b'\r\n') > roh.count(b'\n') // 2:
        text = text.replace('\r\n', '\n').replace('\n', '\r\n')
    return text.encode('utf-8')


basis = subprocess.run(['node', PROBE], capture_output=True, text=True)
if basis.returncode != 0:
    print('ABBRUCH: die Probe ist schon ohne Mutation rot — dann sagt dieser')
    print('Test nichts aus. Ausgabe:')
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
        return 'ungueltig', 'Aufbaupruefung gerissen: ' + aufbau[0].strip()[:55]
    # Fuenfte Beweisregel: eine EINGEFANGENE Ausnahme ist kein Nachweis. Die
    # vierte Regel erkannte nur den Abbruch der Probe; faengt die Probe den
    # Fehler ab und meldet ihn, sah es wie eine gefangene Mutation aus
    # (Codex, Abnahme Runde 2).
    ausnahme = [z for z in zeilen if '[Ausnahme]' in z]
    if ausnahme:
        return 'ungueltig', 'Produktivcode warf: ' + ausnahme[0].strip()[:50]
    ausnahmen = [z for z in zeilen if 'warf eine Ausnahme' in z]
    if ausnahmen:
        return 'ungueltig', 'Ausnahme statt Verhaltensaenderung'
    sachliche = [z for z in zeilen if 'warf eine Ausnahme' not in z]
    if not sachliche:
        return 'ungueltig', 'rot ohne inhaltliche Pruefung'
    if erwartet and not any(erwartet in z for z in sachliche):
        return 'ungueltig', ('erwartete Pruefung "%s" blieb gruen; rot war: %s'
                             % (erwartet[:30], sachliche[0].strip()[:40]))
    return 'gefangen', sachliche[0].strip()[:70]


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
            probleme.append('%s [als %s verbucht, erwartet ungueltig]' % (name, art))
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
