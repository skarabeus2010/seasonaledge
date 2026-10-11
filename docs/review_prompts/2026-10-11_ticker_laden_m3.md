# Ticker schneller laden — Schritt 3: Abrufkennung auf fünf Seiten + Dashboard-Overnight

Schritt 2 live (`4b8b6c6`, [Freigabe](2026-10-11_ticker_laden_m2_antwort2.md), deine Auflage 3).
Read-only, nichts schreiben, Mutationstests NICHT ausführen. Änderungen: `git diff`.

<task>Prüfe Schritt 3. Freigabe für den Deploy?</task>

## Änderung
wochentage, backtest-engine, opex, vixpiration, spot-vol-beta: `var _lk = SA.ladeKennung.start(<ticker bzw. Paar>)`
unmittelbar vor dem Kursabruf (nach frühen `return`s), und am Anfang von Erfolg UND Fehler
`if (!SA.ladeKennung.aktuell(_lk)) return;` — das Muster der Seiten, die es schon haben (jahreszyklus u. a.).
Einargumentige Form `start(ticker)`: jeder Aufruf ist ein neuer Abruf (Zeitraum-Regler lädt denselben Ticker neu).
Dashboard-Overnight: dieselbe Prüfung gegen die Kennung von `renderAll` (`_rk`) in Erfolg und Fehler; der
einzeilige `catch` dafür aufgeteilt.

## Nachweis — Seitenprobe, neuer Fall „wechsel"
Nach dem Start Ticker A wählen (seine Antworten kommen absichtlich 1,5 s später), 30 ms danach B; Soll =
Anzeige wie bei „direkt" (nur B gewählt). `verify_seiten_kurse.py`: **neu = direkt auf allen sechs Seiten**;
der alte Stand wird berichtet und zeigt den Fehler auf allen, u. a.: wochentage, backtest-engine, opex,
vixpiration, spot-vol-beta — „verspätete Antwort überschrieb".
Handentfernte Schutzzeile bei opex → Probe rot (Gegenprobe).

**Dashboard (dein Befund M2 R1):** eigener Fall — A erscheint (30-J-Ladung schnell), seine Nachladungen kommen
langsam (`ausser`-Untergrenze 1996-10-09), dann B. Alter Stand: die verspätete Overnight-Karte von A überschreibt
die von B (reproduziert: „Win-Rate 50 %" statt „45 %"). Neuer Stand: gleich „direkt" — aber **auch ohne die neue
Schutzzeile**: mit VORLADEN (Schritt 2) enthält die 30-J-Ladung `open`, und Overnight (höchstens 30 Jahre,
`sel-years` 5…30) wird aus diesem Bestand ohne Netzanfrage bedient, bevor B gewählt werden kann. Den Wettlauf
gibt es im neuen Code auf diesem Weg nicht mehr; die Schutzzeile bleibt als Absicherung (TTL-Ablauf zwischen
Anzeige und Overnight, Verdrängung). **Bitte prüfen, ob es einen erreichbaren Pfad gibt, den ich übersehe.**

Stand: `verify_seiten_kurse.py` **229/229** (Charts beim Wechsel über den Endstand je Chart-Element verglichen —
beim Wechsel zeichnet die Seite zusätzlich die Charts von A); alter Stand zeigt den Überschreib-Fehler auf allen
sechs Seiten, neuer auf keiner. `verify_kurse.py` unverändert grün.

## Ausgabevertrag
**Urteil** · **Befunde** · **Auflagen**. ≤ 30 Zeilen.
