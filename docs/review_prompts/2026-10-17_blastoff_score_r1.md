# Codex-Review: Blast-Off aus dem Mail-Score (2026-10-17)

Nur lesen. Diff: `git diff HEAD -- shared/newsletter_indicators.py scripts/templates/daily_report.html.j2 scripts/verify_kursmuster.py`.

Nutzerentscheidung: Blast-Off soll „Bewegung kommt“ anzeigen, keine Richtung; der ±1-Bonus über die LBR-Richtung
fällt weg, die Spalte BO bleibt als Info, die Legende nennt das Gemessene (Ereignisstudie H10: kein Unterschied im
Betrag der 5-Tage-Bewegung gegenüber Tagen gleicher Vorher-Vola, 2000–2023, n ≈ 308 000).

Nebenbei korrigiert: TS war als „max 6“ / Gesamt „0–10“ ausgewiesen; tatsächlich war TS schon bisher höchstens 5
(„RSI weekly > 50“ und „< 10“ schließen sich aus), jetzt −2 … +4, Gesamt −2 … 8 (Anzeige „/4“ und „/8“).
Wächterfall: kleiner und großer Körper → gleicher Score (Gegenprobe: alter Code rot, Score 4 gegen 3).

Prüffragen: Stimmen die neuen Spannen (−2 … +4, Gesamt −2 … 8)? Verlässt sich irgendein anderer Verbraucher
(Sortierung, Schwellen, Backtest `scripts/backtest_newsletter_scoring.py`, Weekly, Seiten) auf den alten Bonus oder
die alten Spannen? Ist die Legende korrekt? Am Ende **FREIGABE** oder **KEINE FREIGABE**.
