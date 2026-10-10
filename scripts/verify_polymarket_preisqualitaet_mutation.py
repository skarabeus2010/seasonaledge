# -*- coding: utf-8 -*-
"""Prueft den Waechter, nicht den Code: baut die Befunde 11 und 1 wieder ein
und verlangt, dass verify_polymarket_preisqualitaet.py ROT wird.

    py -3.14 scripts/verify_polymarket_preisqualitaet_mutation.py

Fuenf Beweisregeln wie in den uebrigen Mutationstests: `[Aufbau]` gerissen =
Geruest zerstoert · Endmarker `PROBE-ENDE` muss erreicht sein · jede Mutation
BENENNT die Pruefung, die sie reissen muss · eine Ausnahme gilt nie als
Nachweis · auch eine EINGEFANGENE Ausnahme (`[Ausnahme]`) nicht. Dazu
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
from scripts.verify_twins_mutation import _atomar_schreiben, python_probe  # noqa: E402

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

PD = 'shared/polymarket_data.py'
RF = 'scripts/polymarket_refresh.py'
BF = 'scripts/polymarket_backfill.py'
SC = 'shared/supabase_client.py'
PROBE = 'scripts/verify_polymarket_preisqualitaet.py'

MUTATIONEN = [
    # Der Urzustand von Befund 11: das gekreuzte Buch wird gemittelt.
    ('Urzustand — das gekreuzte Buch wird wieder gemittelt',
     PD,
     "        if best_bid > best_ask:\n"
     "            return {\"status\": \"verworfen\", \"grund\": \"buch_gekreuzt\", \"snapshot\": None}",
     "        pass",
     'wird verworfen'),

    ('Der Wertebereich 0..1 wird nicht mehr geprueft',
     PD,
     "    def _im_band(x):\n        return x is not None and 0.0 <= x <= 1.0",
     "    def _im_band(x):\n        return x is not None",
     'ausserhalb 0..1'),

    # Der Urzustand von Befund 1, erste Haelfte: die Wahrheitspruefung macht
    # aus zwei Nullquoten eine EINSEITIGE Quote (0.0 ist falsch, also greift
    # der naechste Zweig). Der Preis bleibt 0,0 — die Preisart wird falsch.
    # Hier stand zuerst die Erwartung „der Preis ist 0,0"; die blieb gruen,
    # und der eigene Mutationstest hat das gemeldet.
    ('Die Wahrheitspruefung macht aus zwei Nullquoten eine einseitige',
     PD,
     "    if best_bid is not None and best_ask is not None:",
     "    if best_bid and best_ask:",
     'mit Preisart mid'),

    # Die Gegenrichtung von Befund 1: ein leerer Markt darf NICHT zu 0,0
    # werden. (Hier stand zuerst eine Mutation der ganzen Wahrheitskette —
    # die haette alle drei Zweige treffen muessen und riss dieselbe Pruefung
    # wie die vorige. Gemeldet vom eigenen Mutationstest.)
    ('Ein leerer Markt ergibt wieder einen Preis von 0,0',
     PD,
     '        return {"status": "kein_preis", "grund": "keine_quote", "snapshot": None}',
     '        preis, art = 0.0, PREISART_MID',
     'ein leerer Markt ist dagegen'),

    ('Die Spannweitengrenze loest sich von der Divergenzschwelle',
     PD,
     "SPREAD_GRENZE = 0.06",
     "SPREAD_GRENZE = 0.2",
     'die Herleitung haelt'),

    ('Zu breite Quoten werden nicht mehr erkannt',
     PD,
     "    return sp is not None and sp > SPREAD_GRENZE",
     "    return False",
     'als zu breit erkannt'),

    ('Die einseitige Quote gilt wieder als bewertbar',
     PD,
     "PREISARTEN_BEWERTBAR = frozenset({PREISART_MID})",
     "PREISARTEN_BEWERTBAR = frozenset({PREISART_MID, PREISART_BID})",
     'bewertbar ist nur der Mittelkurs'),

    # Die Spalten, die in der Datenbank landen.
    ('Die Preisart wird nicht mehr in die Zeile geschrieben',
     RF,
     '        "price_kind": snap.get("price_kind"),',
     '        "price_kind": None,',
     'Feld price_kind'),

    ('Die Quotes werden nicht mehr mitgeschrieben',
     RF,
     '        "bid": snap.get("bid"),',
     '        "bid": None,',
     'Feld bid'),

    ('Der Abrufzeitpunkt fehlt in der Zeile',
     RF,
     '        "fetched_at": ts.isoformat(),',
     '        "fetched_at": None,',
     'fetched_at ist der Abrufzeitpunkt'),

    ('Die Quellenangabe faellt auf clob zurueck',
     RF,
     '        "source": "gamma-snapshot",',
     '        "source": "clob",',
     'gamma-snapshot und nicht clob'),

    ('Historienzeilen werden nicht als Historie gekennzeichnet',
     BF,
     '            "price_kind": PREISART_HISTORIE,',
     '            "price_kind": None,',
     'price_kind = history'),

    ('Beim Backfill wird die Quellzeit als Abrufzeit ausgegeben',
     BF,
     '            "fetched_at": abgerufen_am,',
     '            "fetched_at": ts.isoformat(),',
     'ts ist die Quellzeit'),

    ('Der Nullpunkt der Historie wird wieder per Wahrheitspruefung verworfen',
     BF,
     "        p = pt.get(\"p\")\n        if p is None:\n            continue",
     "        p = pt.get(\"p\")\n        if not p:\n            continue",
     'bleibt erhalten'),

    # Die beiden Helfer.
    ('Der Abrufzustand wird per upsert geschrieben und kann Katalogzeilen anlegen',
     SC,
     '        client.table("polymarket_markets").update({\n'
     '            "last_fetch_state": r.get("last_fetch_state"),\n'
     '            "last_fetch_at": r.get("last_fetch_at"),\n'
     '        }).eq("condition_id", cid).execute()',
     '        client.table("polymarket_markets").upsert({\n'
     '            "condition_id": cid,\n'
     '            "last_fetch_state": r.get("last_fetch_state"),\n'
     '            "last_fetch_at": r.get("last_fetch_at"),\n'
     '        }).execute()',
     'kein upsert'),

    # Hier stand zuerst `return [] or RuntimeError(` — das ergab mit dem
    # folgenden `from e` ungueltige Syntax, die Probe scheiterte am Import und
    # der Fall war ungeprueft. Jetzt ein syntaktisch gueltiger Rueckfall.
    # Der ganze raise-Block wird ersetzt, samt `from e`. Zuerst hatte ich nur
    # die erste Zeile getauscht — das `from e` blieb stehen, ergab ungueltige
    # Syntax, und die Probe scheiterte am Import statt den Fall zu pruefen.
    ('Fehlt die Datenbankfunktion, wird still eine leere Liste geliefert',
     SC,
     "        raise RuntimeError(",
     "        return []\n    if False:\n        raise RuntimeError(",
     'scheitert mit RuntimeError'),
]

UNGUELTIG_ERWARTET = [
    # Loest nur eine Ausnahme aus, aendert kein Verhalten.
    ('Ausnahme statt Verhaltensaenderung',
     PD,
     "    best_bid = _safe_float(market.get(\"bestBid\"))",
     "    best_bid = None.real"),
]

ROH = {d: io.open(d, 'rb').read() for d in (PD, RF, BF, SC)}


def anker(datei: str, text: str) -> bytes:
    roh = ROH[datei]
    if roh.count(b'\r\n') > roh.count(b'\n') // 2:
        text = text.replace('\r\n', '\n').replace('\n', '\r\n')
    return text.encode('utf-8')


def lauf() -> tuple[int, str]:
    r = python_probe([PROBE], capture_output=True, text=True)
    return r.returncode, (r.stdout or '') + (r.stderr or '')


rc, ausgabe = lauf()
if rc != 0:
    print('ABBRUCH: die Probe ist schon ohne Mutation rot.')
    print(ausgabe[-1500:])
    sys.exit(1)
_m = re.search(r'PROBE-ENDE (\d+) Pruefungen', ausgabe)
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
        rc_, aus = lauf()
    finally:
        _atomar_schreiben(pathlib.Path(datei), ROH[datei])
    if rc_ == 0:
        return 'entwischt', 'Probe blieb gruen'
    if 'PROBE-ENDE' not in aus:
        return 'ungueltig', 'die Probe brach ab statt durchzulaufen'
    zeilen = [z for z in aus.splitlines() if 'FEHL ' in z]
    if any('[Aufbau]' in z for z in zeilen):
        return 'ungueltig', 'Aufbaupruefung gerissen'
    if any('[Ausnahme]' in z for z in zeilen):
        return 'ungueltig', 'Produktivcode warf'
    if not zeilen:
        return 'ungueltig', 'rot ohne inhaltliche Pruefung'
    if erwartet and not any(erwartet in z for z in zeilen):
        return 'ungueltig', ('erwartete Pruefung "%s" blieb gruen; rot war: %s'
                             % (erwartet[:34], zeilen[0].strip()[:40]))
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
rc_nach, _ = lauf()

print()
print('wiederhergestellt: Probe laeuft wieder gruen' if rc_nach == 0
      else 'WARNUNG: Probe nach der Wiederherstellung ROT!')
print('%d von %d Mutationen gefangen' % (gefangen, len(MUTATIONEN)))
for p in probleme:
    print('  ' + p)
sys.exit(0 if (gefangen == len(MUTATIONEN) and klassifizierer_ok
               and rc_nach == 0) else 1)
