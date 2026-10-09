# -*- coding: utf-8 -*-
"""Prueft die Preisqualitaet am Erzeuger (Phase B1, Befunde 11 und 1).

    py -3.14 scripts/verify_polymarket_preisqualitaet.py

Gegenstand sind die Zustaende, die aus einer Gamma-Antwort entstehen duerfen,
und die Spalten, die daraus in der Datenbank landen. Alles hier laeuft OHNE
Datenbank: geprueft werden die Erzeuger, nicht der Server.

Was das NICHT leistet, und das steht bewusst zuerst: ob die Migration gelaufen
ist, kann dieser Waechter nicht sehen. Er prueft, dass der Code die richtigen
Felder liefert — nicht, dass eine Spalte dafuer existiert. Der Nachweis dafuer
sind die Abnahmeabfragen am Ende von
scripts/sql/polymarket_schema_2026_10.sql, und die laufen auf dem Server.

REGEL ZUR KENNUNG `[Aufbau]`: nur fuer Eigenschaften der Testvorrichtung.
REGEL ZUR KENNUNG `[Ausnahme]`: nur dafuer, dass der Produktivcode nicht wirft.
"""
from __future__ import annotations

import io
import pathlib
import re
import sys
from datetime import datetime, timedelta, timezone

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from shared.polymarket_data import (  # noqa: E402
    PREISARTEN_BEWERTBAR,
    PREISART_HISTORIE,
    PREISART_MID,
    SPREAD_GRENZE,
    bewerte_quote,
    market_to_price_snapshot,
    quote_zu_breit,
)
from scripts.polymarket_refresh import build_price_record  # noqa: E402
from scripts.polymarket_backfill import history_to_records  # noqa: E402

fehler = 0
anzahl = 0


def pruefe(b: bool, was: str) -> None:
    global fehler, anzahl
    anzahl += 1
    print(('  ok   ' if b else '  FEHL ') + was)
    if not b:
        fehler += 1


# ── 1: Die drei Zustaende eines Abrufs ──────────────────────────────────────
# „kein Preis" und „Preis verworfen" sind verschiedene Lagen: nur die zweite
# sagt, dass die Quelle etwas geliefert hat, dem nicht zu glauben ist. Vorher
# endeten beide im selben `continue`.
print('Ein Abruf endet in genau einem von drei Zustaenden:')
FAELLE = [
    ('Gebot und Nachfrage',       {'bestBid': 0.48, 'bestAsk': 0.52},  'ok',         PREISART_MID,  0.50),
    ('gekreuztes Buch',           {'bestBid': 0.80, 'bestAsk': 0.20},  'verworfen',  None,          None),
    ('nur Gebot',                 {'bestBid': 0.33},                   'ok',         'bid_only',    0.33),
    ('nur Nachfrage',             {'bestAsk': 0.71},                   'ok',         'ask_only',    0.71),
    ('nur letzter Trade',         {'lastTradePrice': 0.41},            'ok',         'last_trade',  0.41),
    ('nichts davon',              {},                                  'kein_preis', None,          None),
    ('Gebot ausserhalb 0..1',     {'bestBid': -0.1, 'bestAsk': 0.5},   'verworfen',  None,          None),
    ('Nachfrage ausserhalb 0..1', {'bestBid': 0.4, 'bestAsk': 1.4},    'verworfen',  None,          None),
    ('Trade ausserhalb 0..1',     {'lastTradePrice': 1.2},             'verworfen',  None,          None),
    ('kein dict',                 None,                                'kein_preis', None,          None),
]
for name, markt, soll_status, soll_art, soll_preis in FAELLE:
    r = bewerte_quote(markt)
    s = r.get('snapshot')
    ok = r.get('status') == soll_status
    if soll_art is not None:
        ok = ok and s and s.get('price_kind') == soll_art
    if soll_preis is not None:
        ok = ok and s and abs(s['yes_price'] - soll_preis) < 1e-9
    pruefe(bool(ok),
           '%-26s -> %-10s %s %s'
           % (name, r.get('status'), (s or {}).get('price_kind') or '',
              '' if soll_preis is None else '%.3f' % (s or {})['yes_price']))

pruefe(len({f[2] for f in FAELLE}) == 3,
       '[Aufbau] die Faelle decken alle drei Zustaende ab')

# ── 2: Das gekreuzte Buch wird nicht gemittelt ──────────────────────────────
# Der Fall, der den Befund ausgeloest hat: Bid 0,80 / Ask 0,20 ergab vorher
# einen Preis von 0,50 mit einer Spannweite von -0,60.
print('Ein gekreuztes Buch ergibt keinen Preis und keine negative Spannweite:')
r = bewerte_quote({'bestBid': 0.80, 'bestAsk': 0.20})
pruefe(r['status'] == 'verworfen' and r['grund'] == 'buch_gekreuzt',
       'Bid 0,80 / Ask 0,20 wird verworfen (%s/%s)' % (r['status'], r['grund']))
pruefe(r['snapshot'] is None,
       'und liefert keinen Mittelkurs von 0,50')
pruefe(market_to_price_snapshot({'bestBid': 0.80, 'bestAsk': 0.20}) is None,
       'auch der alte Rueckgabevertrag liefert dafuer None')

# ── 3: Eine echte Null bleibt eine Null ─────────────────────────────────────
# Das ist die andere Haelfte von Befund 1: fehlender Preis und echte Null
# wurden gleich behandelt. Hier muss die Null ANKOMMEN.
print('Eine echte Null unterscheidet sich von „kein Preis":')
null = bewerte_quote({'bestBid': 0.0, 'bestAsk': 0.0})
pruefe(null['status'] == 'ok', 'Bid 0 / Ask 0 ist ein gueltiger Abruf')
# Jeden Zugriff auf das Snapshot-dict absichern: nimmt eine Mutation es weg,
# soll die Probe MELDEN und nicht an einem TypeError sterben.
_ns = null.get('snapshot') or {}
pruefe(_ns.get('yes_price') == 0.0,
       'und der Preis ist 0,0 (nicht None): %r' % _ns.get('yes_price'))
pruefe(_ns.get('price_kind') == PREISART_MID,
       'mit Preisart mid, weil beide Quotes da sind (%r)' % _ns.get('price_kind'))
leer = bewerte_quote({})
pruefe(leer['status'] == 'kein_preis',
       'ein leerer Markt ist dagegen „kein_preis" und NICHT 0,0')

# ── 4: Die Spannweitengrenze behaelt ihre Herleitung ────────────────────────
# SPREAD_GRENZE ist aus der Divergenzschwelle der Seite abgeleitet: ein
# Mittelkurs traegt eine Unsicherheit von ± Spannweite/2, und die darf nicht
# groesser sein als der kleinste Abstand, den wir als Richtung ausweisen.
# Wird die Schwelle auf der Seite geaendert, muss diese Zahl mitgehen — sonst
# ist die Herleitung nur noch ein Kommentar.
print('Die Spannweitengrenze bleibt an die Divergenzschwelle gebunden:')
js = (REPO / 'landing/js/polymarket.js').read_text(encoding='utf-8')
m = re.search(r'divergenzSchwellePp:\s*([0-9.]+)', js)
pruefe(m is not None, '[Aufbau] die Divergenzschwelle ist in der Seite lesbar')
if m:
    schwelle_pp = float(m.group(1))
    pruefe(abs(SPREAD_GRENZE - 2 * schwelle_pp / 100.0) < 1e-12,
           'SPREAD_GRENZE %.4f = 2 x %.1f Punkte — die Herleitung haelt'
           % (SPREAD_GRENZE, schwelle_pp))

print('Eine zu breite Quote wird gespeichert, aber gekennzeichnet:')
breit = bewerte_quote({'bestBid': 0.30, 'bestAsk': 0.60})
pruefe(breit['status'] == 'ok',
       'sie ist kein Messfehler und wird nicht verworfen')
pruefe(quote_zu_breit(breit['snapshot']),
       'aber als zu breit erkannt (Spannweite %.2f > %.2f)'
       % (breit['snapshot']['spread'], SPREAD_GRENZE))
knapp = bewerte_quote({'bestBid': 0.48, 'bestAsk': 0.52})
pruefe(not quote_zu_breit(knapp['snapshot']),
       'eine Spannweite von 0,04 gilt nicht als zu breit')
pruefe(PREISART_MID in PREISARTEN_BEWERTBAR
       and 'bid_only' not in PREISARTEN_BEWERTBAR
       and 'last_trade' not in PREISARTEN_BEWERTBAR,
       'bewertbar ist nur der Mittelkurs, nicht die einseitige Quote '
       'und nicht der letzte Trade')

# ── 5: Was in die Datenbank geht ────────────────────────────────────────────
print('Die Preiszeile traegt Preisart, Quotes und Abrufzeit:')
jetzt = datetime(2026, 10, 9, 12, 0, tzinfo=timezone.utc)
rec = build_price_record('0xabc', bewerte_quote(
    {'bestBid': 0.48, 'bestAsk': 0.52, 'volume24hr': 1234})['snapshot'], jetzt)
for feld, soll in (('price_kind', PREISART_MID), ('bid', 0.48), ('ask', 0.52)):
    pruefe(rec.get(feld) == soll, 'Feld %s = %r' % (feld, rec.get(feld)))
pruefe(rec.get('fetched_at') == jetzt.isoformat(),
       'fetched_at ist der Abrufzeitpunkt')
pruefe(rec.get('ts') == rec.get('fetched_at'),
       'beim Snapshot sind ts und fetched_at gleich — Gamma nennt keine '
       'Quotenzeit, und ein Abrufzeitpunkt ist kein Quotenalter')
pruefe(rec.get('source') == 'gamma-snapshot',
       'die Quelle heisst gamma-snapshot und nicht clob (Regressionsschutz)')

print('Historienzeilen sind als Historie gekennzeichnet:')
t0 = int(datetime(2024, 3, 15, tzinfo=timezone.utc).timestamp())
hist = history_to_records('0xabc', [{'t': t0, 'p': 0.42}, {'t': t0 + 86400, 'p': 0.0}],
                          abgerufen_am=jetzt.isoformat())
pruefe(len(hist) == 2,
       'ein Punkt mit p = 0 bleibt erhalten (%d von 2) — Regressionsschutz'
       % len(hist))
pruefe(all(h['price_kind'] == PREISART_HISTORIE for h in hist),
       'alle Zeilen tragen price_kind = history')
# Index- und Feldzugriffe abgesichert, aus demselben Grund.
_h0 = hist[0] if len(hist) > 0 else {}
_h1 = hist[1] if len(hist) > 1 else {}
pruefe(bool(_h0.get('ts')) and _h0.get('ts') != _h0.get('fetched_at'),
       'ts ist die Quellzeit, fetched_at der Abruf — beim Backfill '
       'verschieden (%s vs %s)'
       % (str(_h0.get('ts'))[:10], str(_h0.get('fetched_at'))[:10]))
pruefe(_h1.get('yes_price') == 0.0,
       'und der Nullpreis kommt als 0,0 an (%r)' % _h1.get('yes_price'))

# ── 6: Der Abrufzustand geht an den Katalog, ohne ihn anzulegen ─────────────
# Ein Upsert auf condition_id wuerde bei einem unbekannten Markt eine halbe
# Katalogzeile anlegen (slug, question, category sind NOT NULL).
print('Der Abrufzustand wird aktualisiert, nicht eingefuegt:')
import shared.supabase_client as sc  # noqa: E402

aufrufe: list[tuple] = []


class _Tab:
    def __init__(self, name):
        self.name = name

    def update(self, daten):
        aufrufe.append(('update', self.name, daten))
        return self

    def upsert(self, *a, **k):
        aufrufe.append(('upsert', self.name, a, k))
        return self

    def eq(self, *a):
        aufrufe.append(('eq', *a))
        return self

    def execute(self):
        return type('R', (), {'data': []})()


_echt = sc.get_client
sc.get_client = lambda: type('C', (), {'table': staticmethod(lambda n: _Tab(n))})()
try:
    sc.update_polymarket_fetch_state([{
        'condition_id': '0xabc', 'last_fetch_state': 'verworfen',
        'last_fetch_at': jetzt.isoformat()}])
finally:
    sc.get_client = _echt

arten = [a[0] for a in aufrufe]
pruefe('update' in arten and 'upsert' not in arten,
       'es wird update verwendet, kein upsert (%s)' % arten)
pruefe(any(a[0] == 'eq' and a[1] == 'condition_id' for a in aufrufe),
       'und auf die condition_id eingeschraenkt')
daten = next((a[2] for a in aufrufe if a[0] == 'update'), {})
pruefe(set(daten) == {'last_fetch_state', 'last_fetch_at'},
       'geschrieben werden GENAU die zwei Felder: %s' % sorted(daten))

# ── 7: Kein stiller Rueckfall bei fehlender Datenbankfunktion ──────────────
print('Fehlt die Datenbankfunktion, gibt es eine Meldung statt eines Rueckfalls:')


class _ClientOhneRpc:
    @staticmethod
    def rpc(*a, **k):
        raise Exception('Could not find the function public.polymarket_latest_prices')


sc.get_client = lambda: _ClientOhneRpc()
try:
    try:
        sc.fetch_polymarket_latest_prices(['0xabc'])
        gemeldet = None
    except RuntimeError as e:
        gemeldet = str(e)
    except Exception as e:                      # jede andere Ausnahme
        gemeldet = 'FALSCHER TYP: ' + type(e).__name__
finally:
    sc.get_client = _echt

pruefe(gemeldet is not None and not gemeldet.startswith('FALSCHER TYP'),
       'der Aufruf scheitert mit RuntimeError statt still zurueckzufallen')
pruefe(gemeldet is not None and 'polymarket_schema_2026_10.sql' in gemeldet,
       'und die Meldung nennt die Migrationsdatei')
pruefe(gemeldet is not None and 'reload schema' in gemeldet,
       'und den Schema-Cache von PostgREST — der zweite haeufige Grund')

print()
print('ALLE PRUEFUNGEN BESTANDEN' if fehler == 0 else '%d FEHLER' % fehler)
print('PROBE-ENDE %d Pruefungen, %d Fehler' % (anzahl, fehler))
sys.exit(0 if fehler == 0 else 1)
