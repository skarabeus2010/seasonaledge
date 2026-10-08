# -*- coding: utf-8 -*-
"""Prueft, dass Liquiditaet keine fehlende Passung ersetzt (Codex-Befund 16).

    py -3.14 scripts/verify_polymarket_discovery.py

Der Defekt: `_score_match` gab `hits + liq_score` zurueck, und
`liq_score = log10(liquidity)/6` erreicht bei **1.000 Dollar** genau 0,500 —
also die Annahmeschwelle, bei NULL Suchworttreffern. Jeder hinreichend liquide
Markt wurde angenommen, egal wovon er handelt.

Die Zahlen hier sind GEMESSEN, nicht gewaehlt: 1.000 → 0,500 · 10.000 → 0,667 ·
1.000.000 → 1,000. Ein Test, der den Fall nicht woertlich trifft, beweist
nichts — diese Lehre hat das Projekt in v65.2 bezahlt.

Keine Netzzugriffe: geprueft werden die reinen Funktionen.
"""
from __future__ import annotations

import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from scripts.polymarket_discover import (  # noqa: E402
    MIN_TREFFER,
    _score_match,
    ist_geeignet,
    kennungstext,
    markttext,
)
from shared.polymarket_data import _extract_token_ids  # noqa: E402

fehler = 0
anzahl = 0


def pruefe(b: bool, was: str) -> None:
    global fehler, anzahl
    anzahl += 1
    print(('  ok   ' if b else '  FEHL ') + was)
    if not b:
        fehler += 1


def markt(frage: str, liquiditaet: float) -> dict:
    return {"question": frage, "liquidityNum": liquiditaet}


BEGRIFFE = ["fed", "rate cut"]

print('Die gemessenen Liquiditaetswerte, die den Defekt ausmachten:')
for liq in (1000.0, 10000.0, 1000000.0):
    treffer, rang = _score_match(markt("Wird Argentinien absteigen?", liq), BEGRIFFE)
    erwartet = min(1.0, math.log10(liq) / 6.0)
    pruefe(treffer == 0, '%9.0f USD, voellig fremdes Thema -> 0 Treffer' % liq)
    pruefe(abs(rang - erwartet) < 1e-9,
           '%9.0f USD -> Liquiditaetsrang %.3f (frueher die ganze Punktzahl)' % (liq, rang))
    pruefe(not ist_geeignet(treffer, BEGRIFFE),
           '%9.0f USD gilt NICHT als geeignet' % liq)

print('Ein sachlich passender Markt bleibt geeignet, auch ohne Liquiditaet:')
treffer, rang = _score_match(markt("Will the Fed cut rates in 2026?", 0.0), BEGRIFFE)
pruefe(treffer >= MIN_TREFFER, '%d Treffer bei 0 USD Liquiditaet' % treffer)
pruefe(rang == 0.0, 'Liquiditaetsrang 0, weil keine Liquiditaet')
pruefe(ist_geeignet(treffer, BEGRIFFE), 'trotzdem geeignet — Passung entscheidet')

print('Liquiditaet ordnet nur noch:')
viel = _score_match(markt("Will the Fed cut rates?", 1000000.0), BEGRIFFE)
wenig = _score_match(markt("Will the Fed cut rates?", 100.0), BEGRIFFE)
pruefe(viel[0] == wenig[0],
       'erste Komponente ist eine reine Trefferzahl, unabhaengig von Liquiditaet')
pruefe(viel[1] > wenig[1], 'der liquidere Markt rangiert vor dem duennen')
pruefe((viel[0], viel[1]) > (wenig[0], wenig[1]),
       'die Sortierung nach (Treffer, Rang) stellt ihn voran')

print('Mehr Treffer schlagen mehr Liquiditaet:')
genau = _score_match(markt("Fed rate cut decision", 100.0), BEGRIFFE)
knapp = _score_match(markt("Fed chair speech", 1000000.0), BEGRIFFE)
pruefe(genau[0] > knapp[0], 'der passendere hat mehr Treffer')
pruefe((genau[0], genau[1]) > (knapp[0], knapp[1]),
       'der passendere gewinnt trotz 10.000-facher Liquiditaet')

print('Fail-closed ohne Suchbegriffe:')
treffer, _ = _score_match(markt("Will the Fed cut rates?", 1000000.0), [])
pruefe(not ist_geeignet(treffer, []),
       'ohne Suchbegriffe ist NICHTS geeignet (vorher fiel es auf Liquiditaet zurueck)')

print('Eine Jahreszahl im Suchbegriff ist PFLICHT:')
# Codex, Abnahme 2026-10-08: ein einziger Worttreffer genuegte, und der Lauf
# nahm reproduzierbar den Markt zum FALSCHEN Jahr an. Die Preise sehen dann
# plausibel aus und gehoeren zu einem anderen Ereignis.
BEGRIFFE_JAHR = ['fed', 'cut', '2026']
m_richtig = markt("Will the Fed cut rates in 2026?", 50000.0)
m_falsch = markt("Will the Fed cut rates in 2027?", 5000000.0)
t_r, _ = _score_match(m_richtig, BEGRIFFE_JAHR)
t_f, _ = _score_match(m_falsch, BEGRIFFE_JAHR)
pruefe(t_f >= MIN_TREFFER,
       '[Aufbau] der Markt zum falschen Jahr hat genug Worttreffer (%d)' % t_f)
pruefe(ist_geeignet(t_r, BEGRIFFE_JAHR, kennungstext(m_richtig)),
       'das richtige Jahr ist geeignet')
pruefe(not ist_geeignet(t_f, BEGRIFFE_JAHR, kennungstext(m_falsch)),
       'das falsche Jahr ist NICHT geeignet, trotz 100-facher Liquiditaet')
pruefe(ist_geeignet(1, ['fed'], kennungstext(m_falsch)),
       'ohne Jahreszahl im Suchbegriff bleibt die Regel wirkungslos')
pruefe(not ist_geeignet(t_r, BEGRIFFE_JAHR, ''),
       'ohne Markttext laesst sich das Jahr nicht belegen -> nicht geeignet')

print('Das Jahr muss in der KENNUNG stehen, nicht irgendwo im Text:')
# Codex' Gegenbeispiel Runde 2: ein 2027-Markt, dessen BESCHREIBUNG das Vorjahr
# erwaehnt. Mit der Pruefung auf den ganzen Markttext war er wieder geeignet.
m_trick = {"slug": "fed-cut-2027",
           "question": "Will the Fed cut rates in 2027?",
           "description": "Unlike 2026, this market covers 2027.",
           "liquidityNum": 5000000.0}
t_trick, _ = _score_match(m_trick, BEGRIFFE_JAHR)
pruefe(t_trick >= MIN_TREFFER,
       '[Aufbau] der Trick-Markt hat genug sachliche Treffer (%d)' % t_trick)
pruefe('2026' in markttext(m_trick),
       '[Aufbau] 2026 steht im Markttext (in der Beschreibung)')
# KEINE [Aufbau]-Kennung: dass `kennungstext` die Beschreibung auslaesst, ist
# eine Aussage ueber den PRODUKTIVCODE. Mit der Kennung galt die Mutation, die
# die Beschreibung wieder hineinnimmt, als ungueltig — zum dritten Mal derselbe
# Fehler in dieser Arbeit.
pruefe('2026' not in kennungstext(m_trick),
       'die Kennung enthaelt die Beschreibung NICHT')
pruefe(not ist_geeignet(t_trick, BEGRIFFE_JAHR, kennungstext(m_trick)),
       'der 2027-Markt ist NICHT geeignet, obwohl 2026 in seiner Beschreibung steht')

print('Die Jahreszahl allein ist kein sachlicher Treffer:')
# Richtiges Jahr, falsches Thema. Vorher zaehlte „2026" selbst als Treffer und
# erfuellte damit MIN_TREFFER = 1.
m_thema = {"slug": "oscars-2026", "question": "Who wins Best Picture 2026?",
           "liquidityNum": 5000000.0}
t_thema, _ = _score_match(m_thema, BEGRIFFE_JAHR)
pruefe(t_thema == 0,
       'ein Markt, der nur die Jahreszahl trifft, hat 0 sachliche Treffer (%d)'
       % t_thema)
pruefe(not ist_geeignet(t_thema, BEGRIFFE_JAHR, kennungstext(m_thema)),
       'und ist damit nicht geeignet, trotz richtigem Jahr und viel Liquiditaet')

print('Die Aufrufstellen geben die KENNUNG mit, nicht den ganzen Text:')
# Diese Probe prueft die FUNKTION. Ein Fix, der nur an der Aufrufstelle sitzt,
# entwischt ihr deshalb — genau das hat der eigene Mutationstest gemeldet.
# Geprueft wird daher die Verdrahtung in der Quelle. GRENZE: eine Umbenennung
# faengt das nicht, nur das Zurueckdrehen auf `markttext`.
quelle = (pathlib.Path(__file__).resolve().parent
          / 'polymarket_discover.py').read_text(encoding='utf-8')
pruefe('ist_geeignet(z[2], terms, kennungstext(z[1]))' in quelle,
       'find_candidate uebergibt kennungstext')
pruefe('ist_geeignet(treffer, terms, kennungstext(m))' in quelle,
       'find_top_candidates uebergibt kennungstext')
pruefe('ist_geeignet(z[2], terms, markttext(' not in quelle,
       'keine Aufrufstelle uebergibt mehr den ganzen Markttext')

print('Die Bewertung liefert immer ein PAAR:')
# Die Aufrufstelle entpackt mit `*`; ein float ergaebe dort TypeError und
# haette den ganzen Lauf abgebrochen.
leer = _score_match({}, BEGRIFFE_JAHR)
pruefe(isinstance(leer, tuple) and len(leer) == 2,
       'ein Markt ohne Text ergibt (0, 0.0), nicht einen float: %r' % (leer,))

print('YES und NO folgen `outcomes`, nicht der Position:')
# Eine vertauschte Reihenfolge dreht jeden Preis dieses Marktes um (1 - p).
pruefe(_extract_token_ids('["a","b"]', '["Yes","No"]') == ('a', 'b'),
       'Yes zuerst: (a, b)')
pruefe(_extract_token_ids('["a","b"]', '["No","Yes"]') == ('b', 'a'),
       'No zuerst: (b, a) — vorher waere a als YES gelaufen')
pruefe(_extract_token_ids('["a","b"]', None) == ('a', 'b'),
       'ohne outcomes bleibt die uebliche Reihenfolge als Rueckfall')
pruefe(_extract_token_ids('["a","b"]', '["Trump","Harris"]') == ('a', 'b'),
       'bei fremden Namen ebenso — und es wird nichts geraten')

print()
print('ALLE PRUEFUNGEN BESTANDEN' if fehler == 0 else '%d FEHLER' % fehler)
print('PROBE-ENDE %d Pruefungen, %d Fehler' % (anzahl, fehler))
sys.exit(0 if fehler == 0 else 1)
