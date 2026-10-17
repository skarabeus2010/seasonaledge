# Codex-Review: /skew überarbeitet (2026-10-17, Runde 3)

Runde 2: [2026-10-17_skew_seite_r2.md](2026-10-17_skew_seite_r2.md) — ein Befund (P2: ein zweiter Lauf derselben
Session lässt einen gescheiterten Ticker mit altem Rang im Radar erscheinen). Nur lesen. Diff: `git diff HEAD -- landing scripts`.

## Seit Runde 2 geändert
`renderSkew` beschränkt `SKEW_RANG` auf Ticker aus `tickers` des Laufs (alle Leser — Radar, Extremlisten, Tabelle,
Zeile unter dem Radar — gehen über `SKEW_RANG`). Wächterfall „gescheiterter Ticker mit altem Rang derselben Session:
nicht im Radar, nicht in Extremlisten, in der Fehlliste“, neue Mutation „Rang ohne Messwert bleibt im Radar“.

## Prüffragen
1. Ist der Befund aus Runde 2 vollständig behoben, auch für `rang_status` (Status eines gescheiterten Tickers)?
2. Bricht die Beschränkung etwas, das vorher richtig war (z. B. Tabelle, Sprachwechsel, zweiter Snapshot im selben DOM)?
3. Offene Punkte aus Runde 1/2, sofern berührt.

Antwort: Befunde mit Datei:Zeile und Schwere, am Ende **FREIGABE** oder **KEINE FREIGABE**.
