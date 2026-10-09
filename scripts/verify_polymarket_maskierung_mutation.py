# -*- coding: utf-8 -*-
"""Prueft den Waechter, nicht den Code: baut die behobenen Maskierungsfehler
wieder ein und verlangt, dass probe_polymarket_maskierung.js ROT wird.

Eine Probe, die eine Mutation nicht faengt, hat diesen Fehler nie geprueft —
und „die Probe besteht" ist dann eine Aussage ueber die Probe, nicht ueber den
Code. Genau dieser Fall ist in diesem Projekt schon dreimal aufgetreten.

Zwei Vorsichtsmassnahmen aus eigenen Fehlern:
  * Es wird auf BYTES gearbeitet und in jedem Fall wiederhergestellt; die
    Wiederherstellung wird danach NACHGEWIESEN, nicht angenommen (unter Windows
    ist das Zurueckschreiben schon einmal gescheitert und eine Produktionsdatei
    blieb mutiert im Arbeitsbaum liegen).
  * Ein Anker, der nicht genau einmal vorkommt, gilt als ENTWISCHT und nicht
    als uebersprungen — sonst meldet der Test gruen, weil er nichts getan hat.

Lauf: py -3.14 scripts/verify_polymarket_maskierung_mutation.py
"""
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
PROBE = 'scripts/js/probe_polymarket_maskierung.js'

# (Beschreibung, Datei, alt, neu)
MUTATIONEN = [
    ('Seriennamen wieder roh durchreichen (der urspruengliche Befund 8)',
     JS,
     "        name: esc((byCid[cid].question || byCid[cid].slug).slice(0, 40)),",
     "        name: (byCid[cid].question || byCid[cid].slug).slice(0, 40),",
     'keine rohe oeffnende Klammer im Seriennamen'),

    ('Seriennamen erst maskieren, dann kuerzen (zerschneidet eine Entitaet)',
     JS,
     "        name: esc((byCid[cid].question || byCid[cid].slug).slice(0, 40)),",
     "        name: esc(byCid[cid].question || byCid[cid].slug).slice(0, 40),",
     'Entitaet am Schnittpunkt nicht zerschnitten'),

    # Von Codex als Gegenbeispiel geliefert: maskiert nur den question-Zweig und
    # laesst den slug-Rueckfall roh. Blieb vorher gruen.
    ('nur der question-Zweig maskiert, der slug-Rueckfall nicht',
     JS,
     "        name: esc((byCid[cid].question || byCid[cid].slug).slice(0, 40)),",
     "        name: byCid[cid].question\n"
     "          ? esc(byCid[cid].question.slice(0, 40))\n"
     "          : byCid[cid].slug.slice(0, 40),",
     'keine rohe oeffnende Klammer im Rueckfall'),

    # Bewusst so und nicht „Export entfernen": das Entfernen laesst den
    # Seiten-Aufruf an einem TypeError sterben, zerstoert also das Geruest und
    # beweist nichts. Die Maskierung stillzulegen ist der realistische
    # Rueckfall — nichts wirft, die Ausgabe ist nur wieder unmaskiert.
    ('esc stillgelegt (gibt die Eingabe unveraendert zurueck)',
     JS,
     "    return String(s == null ? '' : s).replace(/[&<>\"']/g, function(c) {",
     "    return String(s == null ? '' : s).replace(/[\\u0000]/g, function(c) {",
     'esc maskiert'),

    ('Maskierungstabelle: die oeffnende Klammer vergessen',
     JS,
     "'&': '&amp;', '<': '&lt;'",
     "'&': '&amp;', '<': '<'",
     'keine rohe oeffnende Klammer'),

    ('Checkboxen wieder per Zeichenkette in innerHTML bauen',
     HTML,
     "      var box = document.getElementById('market-checkboxes');\n      box.textContent = '';",
     # Kein oeffnender Block: der originale DOM-Teil folgt direkt danach und ist
     # fuer sich gueltiges JS. Er laeuft dann zusaetzlich — entscheidend ist,
     # dass innerHTML wieder benutzt wird, und genau das prueft die Probe.
     "      var box = document.getElementById('market-checkboxes');\n"
     "      box.innerHTML = state.markets.map(function(m) {\n"
     "        return '<label><input type=\"checkbox\" data-cid=\"' + m.condition_id +\n"
     "               '\"> ' + m.slug + '</label>';\n"
     "      }).join('');",
     'Liste nicht per innerHTML gebaut'),

    ('condition_id wieder in ein Attribut einsetzen statt per setAttribute',
     HTML,
     "        cb.setAttribute('data-cid', String(m.condition_id == null ? '' : m.condition_id));",
     "        cb.outerHTML = '<input data-cid=\"' + m.condition_id + '\">';",
     'condition_id als Attributwert'),

    ('Kategorie wieder unmaskiert in die Tabelle',
     HTML,
     "               '<td><b>' + SA.polymarket.esc(c.category) + '</b></td>' +",
     "               '<td><b>' + c.category + '</b></td>' +",
     'keine rohe oeffnende Klammer in der Kategorie'),

    # Gegenprobe: eine Mutation, die die Maskierung UEBERTREIBT. Faengt der
    # Waechter sie nicht, prueft er nur „irgendwas ist maskiert" und wuerde
    # auch eine Fassung durchlassen, die harmlose Texte zerstoert.
    ('Gegenprobe: harmlose Kategorie zusaetzlich doppelt maskieren',
     HTML,
     "               '<td><b>' + SA.polymarket.esc(c.category) + '</b></td>' +",
     "               '<td><b>' + SA.polymarket.esc(SA.polymarket.esc(c.category)) + '</b></td>' +",
     'harmlose Kategorie nicht doppelt maskiert'),
]

# Mutationen, die NICHT als Erfolg zaehlen duerfen. Sie pruefen den
# Klassifizierer dieses Tests selbst: eine Mutation, die bloss eine Ausnahme
# ausloest, hat keine Maskierungspruefung ausgeloest und darf nicht als
# „gefangen" durchgehen. Von Codex in Runde 2 als Gegenmutation geliefert —
# vorher zaehlte genau dieser Fall als Erfolg.
UNGUELTIG_ERWARTET = [
    ('Ausnahme statt Maskierungsfehler (null.category)',
     HTML,
     "               '<td><b>' + SA.polymarket.esc(c.category) + '</b></td>' +",
     "               '<td><b>' + SA.polymarket.esc(null.category) + '</b></td>' +"),
    # Zweite Gegenmutation von Codex (Runde 3): wirft NUR fuer den Entitaetsfall.
    # Vorher wurde sie als gefangen verbucht, weil der leere Name die
    # Maskierungspruefung riss — ohne dass die Maskierung nachgegeben hatte.
    ('Ausnahme nur im Entitaetsfall (wirft fuer c3)',
     JS,
     "        name: esc((byCid[cid].question || byCid[cid].slug).slice(0, 40)),",
     "        name: cid === 'c3' ? null.category\n"
     "          : esc((byCid[cid].question || byCid[cid].slug).slice(0, 40)),"),
    # Dritte Gegenmutation von Codex (Runde 4): wirft nur fuer `c2`, also im
    # HARMLOSEN Fall. Dort fehlte die Aufbau-Vorbedingung ebenfalls — dieselbe
    # Luecke an der dritten Stelle. Deshalb traegt jetzt jede inhaltliche
    # Pruefung ihre Vorbedingung.
    ('Ausnahme nur im harmlosen Fall (wirft fuer c2)',
     JS,
     "        name: esc((byCid[cid].question || byCid[cid].slug).slice(0, 40)),",
     "        name: cid === 'c2' ? null.category\n"
     "          : esc((byCid[cid].question || byCid[cid].slug).slice(0, 40)),"),
    # Vierte Gegenmutation von Codex (Runde 5): setzt HINTER allen
    # Aufbaupruefungen an — Label und Eingabe existieren, nur der Textknoten
    # fehlt. Mit Vorbedingungen allein war das nicht zu fangen; es gab immer eine
    # Stelle dahinter. Gefangen wird es jetzt durch die generelle Regel „eine
    # echte Maskierungsregression wirft nicht".
    ('Ausnahme hinter allen Aufbaupruefungen (Textknoten faellt aus)',
     HTML,
     "        label.appendChild(document.createTextNode(' ' + String(m.slug == null ? '' : m.slug)));\n"
     "        box.appendChild(label);",
     "        box.appendChild(label); null.category;"),
]

ROH = {JS: io.open(JS, 'rb').read(), HTML: io.open(HTML, 'rb').read()}


def anker(datei: str, text: str) -> bytes:
    """Zeilenenden der ZIELDATEI uebernehmen.

    Beide Dateien liegen mit CRLF im Baum. Ein mehrzeiliger Anker mit "\\n"
    trifft darin NIE — und ohne diese Umsetzung meldete der Mutationstest
    „Anker fehlt" fuer Mutationen, die voellig richtig formuliert waren. Das
    ist derselbe Fehler, nur eine Ebene hoeher: der Test prueft dann einen
    anderen Zustand als die Datei hat.
    """
    roh = ROH[datei]
    if roh.count(b'\r\n') > roh.count(b'\n') // 2:
        text = text.replace('\r\n', '\n').replace('\n', '\r\n')
    return text.encode('utf-8')

# Grundlinie zuerst: eine Mutation auf einer schon roten Probe beweist nichts.
basis = subprocess.run(['node', PROBE], capture_output=True, text=True)
if basis.returncode != 0:
    print('ABBRUCH: die Probe ist schon ohne Mutation rot — dann sagt der')
    print('Mutationstest nichts aus. Ausgabe:')
    print(basis.stdout[-2000:])
    sys.exit(1)
_m = re.search(r'PROBE-ENDE (\d+) Pruefungen', basis.stdout or '')
if not _m:
    print('ABBRUCH: die Probe meldet keinen Endmarker — dann kann der Test nicht')
    print('unterscheiden, ob eine Mutation eine Pruefung ausgeloest oder die Probe')
    print('nur zum Absturz gebracht hat.')
    sys.exit(1)
SOLL_PRUEFUNGEN = int(_m.group(1))
print('Grundlinie: Probe ohne Mutation gruen, %d Pruefungen durchlaufen\n'
      % SOLL_PRUEFUNGEN)

def bewerte(name, datei, alt, neu, erwartet=None):
    """Fuehrt eine Mutation und gibt zurueck, WAS sie bewiesen hat:
    'gefangen'   — die Probe ist an einer echten Pruefung rot geworden
    'entwischt'  — die Probe blieb gruen
    'ungueltig'  — rot, aber keine Pruefung sprach an oder die Probe brach ab;
                   das beweist nichts ueber den geprueften Fall
    'kein-anker' — die Mutation traf nicht
    """
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
    # Rot genuegt NICHT als Beweis, und zwar aus zwei Gruenden.
    # (1) Eine Mutation, die den Code zerstoert, laesst node abbrechen — rot,
    #     ohne dass eine Pruefung angesprochen hat.
    # (2) Eine Mutation kann eine Ausnahme ausloesen, die ein try/catch als FEHL
    #     meldet, waehrend die Probe danach abbricht — dann wurde der
    #     beabsichtigte Fall nie geprueft.
    # Beide Faelle standen hier (Codex, Runde 1 und 2). Verlangt werden deshalb
    # eine echte FEHL-Zeile UND ein vollstaendiger Durchlauf.
    if 'PROBE-ENDE' not in ausgabe:
        return 'ungueltig', 'die Probe brach ab statt durchzulaufen'
    # Eine Ausnahme ist KEIN Maskierungsbefund. Die Probe meldet sie als
    # FEHL-Zeile, damit sie nicht stirbt — aber als Nachweis zaehlt nur eine
    # FEHL-Zeile, die aus einer inhaltlichen Pruefung kommt. Ohne diese
    # Unterscheidung wuerde jede Mutation, die irgendwo einen TypeError
    # ausloest, als Erfolg verbucht (Codex-Befund, Runde 2).
    fehlzeilen = [z for z in ausgabe.splitlines() if 'FEHL ' in z]
    # Eine gerissene AUFBAU-Pruefung heisst: die Mutation hat das Geruest
    # zerstoert, nicht die Maskierung umgangen. Dann ist das Rot kein Nachweis.
    # Das ist der Grund, warum die Maskierungspruefungen „nichts gerendert" und
    # „unmaskiert gerendert" nicht mehr verwechseln duerfen — vorher tat die
    # Pruefung `kat.includes('&lt;b')` genau das, und eine Mutation, die die
    # Tabelle bloss leerte, galt als gefangen (Codex-Befund, Runde 2).
    aufbau_gerissen = [z for z in fehlzeilen if '[Aufbau]' in z]
    if aufbau_gerissen:
        return 'ungueltig', 'Aufbaupruefung gerissen: ' + aufbau_gerissen[0].strip()[:55]
    # Fuenfte Beweisregel: eine EINGEFANGENE Ausnahme ist kein Nachweis. Die
    # vierte Regel erkannte nur den Abbruch der Probe; faengt die Probe den
    # Fehler ab und meldet ihn, sah es wie eine gefangene Mutation aus
    # (Codex, Abnahme Runde 2).
    ausnahme = [z for z in fehlzeilen if '[Ausnahme]' in z]
    if ausnahme:
        return 'ungueltig', 'Produktivcode warf: ' + ausnahme[0].strip()[:50]
    # Eine echte Maskierungsregression WIRFT NICHT. Taucht irgendwo eine
    # Ausnahme auf, hat die Mutation den Code zerstoert und nicht die Maskierung
    # umgangen — dann beweist das Rot nichts. Diese Regel ersetzt das Stapeln
    # weiterer Vorbedingungen: Codex hat vier Mal hintereinander eine Mutation
    # gefunden, die knapp HINTER der jeweils letzten Vorbedingung ansetzt
    # (null.category, c3, c2, Textknoten). Mit jeder neuen Vorbedingung gab es
    # eine neue Stelle dahinter. Hier endet die Schleife.
    ausnahmen = [z for z in fehlzeilen if 'warf eine Ausnahme' in z]
    if ausnahmen:
        return 'ungueltig', 'Ausnahme statt Maskierungsfehler: ' + ausnahmen[0].strip()[:50]
    sachliche = [z for z in fehlzeilen if 'warf eine Ausnahme' not in z]
    if not sachliche:
        return 'ungueltig', 'rot ohne inhaltliche Pruefung'
    # Zweite Regel: die Mutation muss die von ihr BENANNTE Pruefung reissen.
    # Sonst ist sie rot aus einem unbeteiligten Grund — eine Aussage ueber
    # irgendetwas, nicht ueber den geprueften Fall.
    if erwartet and not any(erwartet in z for z in sachliche):
        return 'ungueltig', ('erwartete Pruefung "%s" blieb gruen; rot war: %s'
                             % (erwartet[:34], sachliche[0].strip()[:40]))
    return 'gefangen', sachliche[0].strip()[:70]


gefangen, entwischt = 0, []
try:
    for name, datei, alt, neu, erwartet in MUTATIONEN:
        art, warum = bewerte(name, datei, alt, neu, erwartet)
        if art == 'gefangen':
            print('  gefangen       %s' % name)
            gefangen += 1
        else:
            kennz = {'entwischt': 'ENTWISCHT   ', 'ungueltig': 'UNGUELTIG   ',
                     'kein-anker': 'KEIN ANKER  '}[art]
            print('  %s   %s  (%s)' % (kennz, name, warum))
            entwischt.append('%s [%s: %s]' % (name, art, warum))

    # Gegenprobe am Klassifizierer: diese Mutationen MUESSEN als ungueltig
    # erkannt werden. Zaehlen sie als gefangen, ist das Urteil dieses Tests
    # wertlos — er wuerde Abstuerze als Nachweis verbuchen.
    if UNGUELTIG_ERWARTET:
        print('  -- Gegenprobe am Urteil dieses Tests --')
    klassifizierer_ok = True
    for name, datei, alt, neu in UNGUELTIG_ERWARTET:
        art, warum = bewerte(name, datei, alt, neu)
        if art == 'ungueltig':
            print('  richtig verworfen  %s  (%s)' % (name, warum))
        else:
            print('  FALSCH EINGEORDNET %s  -> %s' % (name, art))
            entwischt.append('%s [als %s verbucht, erwartet ungueltig]' % (name, art))
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
for e in entwischt:
    print('  ENTWISCHT: ' + e)
sys.exit(0 if (gefangen == len(MUTATIONEN) and klassifizierer_ok
              and nach.returncode == 0) else 1)
