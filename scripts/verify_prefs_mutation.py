# -*- coding: utf-8 -*-
"""Prueft den Test, nicht den Code: baut die behobenen Fehler wieder ein und
verlangt, dass t_prefs.js rot wird. Ein Test, der die Mutation nicht faengt,
hat den Fehler nie geprueft.

Arbeitet auf Bytes und stellt die Datei in jedem Fall wieder her.
"""
import io, os, subprocess, sys

APP = 'landing/js/app.js'
TEST = os.path.join('scripts', 'js', 'verify_prefs.js')

MUTATIONEN = [
    ('B1 Slider-Label: Ereignis weglassen',
     "      _feuere(el, 'input');\n",
     ""),
    ('B1 Slider-Label: falsches Ereignis (change statt input)',
     "      _feuere(el, 'input');",
     "      _feuere(el, 'change');"),
    ('B2 Eignung: wieder die Zeichen-Heuristik statt der Kategorie',
     "    var k = art();\n    if (k) return /Aktie$/.test(k);\n",
     ""),
    ('B2 Eignung: Krypto aus dem Rueckfall entfernen',
     " || /-USD$/.test(t)",
     ""),
    ('B5 Nachpruefung: unbekannten Ticker nicht vergessen',
     "  if (!e) SA.prefs.vergessen();",
     "  if (!e) { /* nichts */ }"),
    ('Zeitraum: statt des naechstliegenden immer die erste Option',
     "    if (best == null) return null;\n    el.value = best;\n    return best;",
     "    el.value = opts[0].value;\n    return el.value;"),
    ('Ticker: Kategorie nicht mitspeichern',
     "    schreib(K_ART, kategorie || '');",
     "    /* Kategorie weggelassen */"),
    ('Ticker: Gross-/Kleinschreibung nicht normalisieren',
     "    t = String(t || '').trim().toUpperCase();\n    if (!t) return;",
     "    t = String(t || '').trim();\n    if (!t) return;"),
]

roh = io.open(APP, 'rb').read()
gefangen, entwischt = 0, []
try:
    for name, alt, neu in MUTATIONEN:
        a = alt.encode('utf-8')
        if roh.count(a) != 1:
            print('  UEBERSPRUNGEN  %s  (Anker %dx gefunden)' % (name, roh.count(a)))
            entwischt.append(name + ' [Anker fehlt]')
            continue
        io.open(APP, 'wb').write(roh.replace(a, neu.encode('utf-8'), 1))
        r = subprocess.run(['node', TEST], capture_output=True, text=True)
        if r.returncode == 0:
            print('  ENTWISCHT      %s' % name)
            entwischt.append(name)
        else:
            print('  gefangen       %s' % name)
            gefangen += 1
finally:
    io.open(APP, 'wb').write(roh)

# Wiederherstellung nachweisen, nicht annehmen
assert io.open(APP, 'rb').read() == roh, 'WIEDERHERSTELLUNG FEHLGESCHLAGEN'
r = subprocess.run(['node', TEST], capture_output=True, text=True)
print()
print('wiederhergestellt: Test laeuft wieder gruen' if r.returncode == 0
      else 'WARNUNG: Test nach Wiederherstellung rot!')
print('%d von %d Mutationen gefangen' % (gefangen, len(MUTATIONEN)))
for e in entwischt:
    print('  ENTWISCHT: ' + e)
sys.exit(0 if (gefangen == len(MUTATIONEN) and r.returncode == 0) else 1)
