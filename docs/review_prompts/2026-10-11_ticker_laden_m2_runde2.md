# Ticker schneller laden — Migration Schritt 2, Runde 2

Runde 1: [Prompt](2026-10-11_ticker_laden_m2.md) · [Antwort](2026-10-11_ticker_laden_m2_antwort1.md) (keine Freigabe).
Read-only, nichts schreiben, Mutationstests NICHT ausführen.

<task>Prüfe die drei Auflagen aus Runde 1. Freigabe für den Deploy von Schritt 2?</task>

## Auflage 1 — Rückfall auch bei zusätzlichen Spalten
`kurse.js` (`laden`, `geteilt`): wieder `if (!b || deckt(anfrage, b.felder, b.ab)) throw e;` — Rückfall, sobald die
gescheiterte Ladung mehr verlangte (Zeitraum ODER Spalten, also auch VORLADEN), kein zweiter Versuch nur bei genau
dem eigenen Bedarf. Folge: eine typische Anfrage (`date,close…`) gegen eine gescheiterte VORLADEN-Ladung lädt ihren
Bedarf einmal selbst — im Fehlerfall doppelte Last, wie von dir in M1 R2 als regelkonform bewertet.
Für Beobachtung zählt `eigeneAktiv` laufende Rückfall-Ladungen (`_intern.eigene()`), die Seitenprobe wartet darauf
(sie meldete sonst zwischen den Wiederholungen der Rückfall-Ladung zu früh „fertig").

## Auflage 2 — Regressionstests
Probe Abschnitt 19g: (a) VORLADEN scheitert an `open` (feldabhängige 500), `close`-Anfrage gelingt über den Rückfall;
(b) nach TTL trug der Bestand `high`, die Neuladung scheitert an `high`, `close`-Anfrage gelingt. Mutation
„Rückfall nur bei längerem Zeitraum" (meine verworfene Regel) ist rot. Fälle, die einen Fehlerpfad OHNE Rückfall
prüfen (404, 500 nach Wiederholungen, kaputte Blöcke, 19e), fordern jetzt genau den VORLADEN-Feldsatz an.

## Auflage 3 — Dashboard-Overnight
Kommt mit der Abrufkennung in den nächsten Schritt (zusammen mit wochentage, backtest-engine, opex, vixpiration,
spot-vol-beta), einschließlich Fehlerabschluss — vorbestehend, nicht Teil dieses Deploys.

## Stand
`verify_kurse.py` 125/125 + Hüllen 65/65; Mutationstest 39/39 (zweimal vor der letzten Zähler-Änderung, einmal
danach); `verify_seiten_kurse.py` 205/205 (alle zwölf Seiten normal gleich, Dashboard-Overnight gegen den alten
Code ohne Kürzung, zwölf Blockfehlerfälle zeigen `prices 500`), Dashboard 36 → 26 Anfragen.

## Ausgabevertrag
**Urteil** · **Befunde** · **Auflagen**. ≤ 30 Zeilen.
