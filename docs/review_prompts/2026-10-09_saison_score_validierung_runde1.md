# Review VOR dem Lauf: Validierungsskript + Protokoll Saison-Score (D5) — Runde 1

Repo `C:\dev\Seasonaledge`. Nur lesen, **nichts ausführen, was `--lauf` startet** — das Ergebnis darf erst nach deiner
Freigabe entstehen (sonst wäre jede Korrektur am Skript eine Entscheidung nach Ansicht des Ergebnisses).
Antwort auf Deutsch, je Befund Schwere + Datei:Zeile + Fall + Änderung; am Ende genau eine Zeile `FREIGABE: ja` oder
`FREIGABE: nein`.

Gegenstand: `scripts/research/saison_score_validierung.py` und das damit geschriebene
`scripts/research/saison_score_validierung_protokoll.json` (Commit b7b01da = Rechenkern, freigegeben). Maßstab:
Plan v2 Abschnitt D5 + v3 „Zu Befund 3" (`docs/review_prompts/2026-10-09_saison_score_anomalie_plan_v2.md`, `_v3.md`).

Bitte prüfen, ob das Skript genau das festgelegte Protokoll rechnet:
- Manifest (43 Reihen: 5 Snapshot + Research-Cache ohne SPY/QQQ), Abschnitt A 2010–2025, jeder 5. Handelstag,
  Abschnitt B ^GSPC/^DJI 1960–2009 getrennt.
- Ziel: Rendite as_of → letzte Kurszeile ≤ as_of + 30 KT mit derselben Endpunkt-/Lückenregel, nur ausgereift.
- Auswertbarkeit (≥ 100 Beobachtungen, ≥ 8 Jahre, nicht konstant), Universum einmal fest.
- Primär: Mittel der Spearman je Reihe (gleich gewichtet), Score (`score_roh`) vs. Ziel; Bootstrap über
  Kalenderjahre, dieselben Jahre für alle Reihen, 2000 Ziehungen, Seed 20261009, Ziehungen mit undefinierter Reihe
  verworfen und gezählt, > 5 % → nicht auswertbar, Perzentilintervall.
- Gepaart: Score vs. 5·(B1+B2) auf denselben Tagen/Ziehungen; explorativ B1–B4, Quintile, Abschnitt B.
- Schutz: `--lauf` verweigert bei abweichendem Kern- oder Datenhash.
Besonders: Werden mehrfach gezogene Jahre korrekt mehrfach gezählt? Ist `score_roh` (ungerundet) statt `score`
richtig? Ist die Spearman-Implementierung (Ränge mit Mittelwert bei Gleichstand, dann Pearson) korrekt? Wird das
Ziel dem Kalenderjahr von as_of zugeordnet (Dezember-Ziele ragen ins Folgejahr)? Fehlt etwas, das nach dem Lauf
nicht mehr ohne Verdacht nachgezogen werden kann?
