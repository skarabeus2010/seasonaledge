# Codex-Review: Reparatur kopierter Kurszeilen, Runde 2 (2026-10-17)

Nur lesen. Runde 1: [Antwort, 4 Befunde](2026-10-17_repair_kopien_r1_antwort.md). Skript `scripts/repair_kopierte_zeilen.py`.

## Behandlung
1. [P1] DOGE-Rundung: Reparatur nur noch für Aktien/ETFs (`im_universum`, sonst Abbruch Exit 2). DOGE-USD steht in
   der DB durchgehend auf 4 Nachkommastellen (2019: 0,0024) — seine „flachen“ Tage sind Rundungsartefakte, keine
   Kopien (eigener Posten); GC=F wegen ungeklärter Rollzuordnung ebenfalls ausgenommen. Zusätzlich Schutz: relativer
   Rundungsfehler > 1e-4 → Kandidat übersprungen. Ziel jetzt: die 8 DAX-Titel (313 Zeilen laut Messung).
2. [P1] Phantom-Folgezeile: Vor- und Folgezeile einer Kette müssen `sauber` sein — kein Kandidat, nicht flach,
   Yahoo echt UND Handelstag laut `is_trading_day`; sonst `nachbar_ungeklaert`. Test: Folgezeile 24.12.2025 (XETRA zu)
   → nichts geschrieben.
3. [P1] Atomar: die Folgezeile trägt ihre unveränderten O/H/L/C/Volumen mit → alle Datensätze haben denselben
   Spaltensatz → `upsert_prices` sendet EINE Anfrage (ein PostgREST-Upsert = eine Anweisung); vor dem Schreiben wird
   geprüft, dass es genau ein Spaltensatz ist, sonst Abbruch. Plan wird vor dem Upsert gespeichert
   (`logs/reparatur/kopierte_zeilen_plan_<ts>.json`), Sicherung der alten Zeilen ebenso. Obergrenze 400 Kandidaten,
   Abbruch bei > 25 % übersprungen.
4. [P2] Abgeleitete Statistiken: `monthly_stats`/`tdom_stats`/`tdoy_stats` rechnet der Nightly aus dem frischen
   Yahoo-Download (`scripts/nightly_refresh.py:77` `download_data` → `preprocess` → `get_or_compute_*`), nicht aus den
   DB-Zeilen — sie ändern sich durch die Reparatur nicht. Betroffen sind die Seiten (rechnen im Browser aus `prices`);
   die lesen nach der Reparatur sofort die neuen Werte. Bitte gegenprüfen.
Außerdem `log_return` auf 8 Stellen wie der Nightly.

Befunde behoben? Neue Probleme? Am Ende **FREIGABE** oder **KEINE FREIGABE**.
