Reading additional input from stdin...
OpenAI Codex v0.162.0
--------
workdir: C:\dev\SeasonalEdge
model: gpt-6.1-sol
provider: openai
approval: never
sandbox: read-only
reasoning effort: medium
reasoning summaries: none
session id: 01a18e5b-9b25-7f62-898f-3ab44fc56c62
--------
user
Du bist Reviewer. Lies docs/review_prompts/2026-10-30_down_days_midterm_code_r1.md und arbeite den Auftrag vollständig ab. Prüfe am Code und rechne nach (Python liegt unter py -3.14 bzw. python; Daten im Repo). Keine Dateien ändern.
codex
Ich lese zuerst die drei neuesten Versionseinträge und den Review-Auftrag. Danach prüfe ich die betroffenen Codepfade und rechne die Ergebnisse mit den Repo-Daten unabhängig nach.
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content CLAUDE.md -TotalCount 240' in C:\dev\SeasonalEdge
 exited -1 in 0ms:
Failed to create unified exec process: helper_unknown_error: setup refresh had errors
2026-10-30T19:48:54.539839Z ERROR codex_core::tools::router: error=exec_command failed: CreateProcess { message: "Rejected(\"Failed to create unified exec process: helper_unknown_error: setup refresh had errors\")" }
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -NoProfile -Command 'Get-Content docs/review_prompts/2026-10-30_down_days_midterm_code_r1.md' in C:\dev\SeasonalEdge
2026-10-30T19:48:58.002943Z ERROR codex_core::tools::router: error=exec_command failed: CreateProcess { message: "Rejected(\"Failed to create unified exec process: helper_unknown_error: setup refresh had errors\")" }
 exited -1 in 0ms:
Failed to create unified exec process: helper_unknown_error: setup refresh had errors
mcp: node_repl/js started
mcp: node_repl/js (completed)
mcp: node_repl/js started
mcp: node_repl/js (completed)
mcp: node_repl/js started
mcp: node_repl/js (completed)
codex
Die Kohortenregeln sind im Code grundsätzlich erkennbar umgesetzt. Ich prüfe jetzt die Zahlen unabhängig aus den Rohdaten; bei den Grafiken fällt bereits auf, dass die Beschriftung von t0 ältere Wahlen am Vortag als „Wahltag“ bezeichnet.
mcp: node_repl/js started
mcp: node_repl/js (failed)
mcp: node_repl/js started
mcp: node_repl/js (completed)
mcp: node_repl/js started
mcp: node_repl/js (completed)
mcp: node_repl/js started
mcp: node_repl/js (completed)
mcp: node_repl/js started
mcp: node_repl/js (completed)
mcp: node_repl/js started
mcp: node_repl/js (completed)
codex
Die unabhängige Nachrechnung bestätigt die Tabellen und Rechenregeln: 648 Kennzahlvergleiche sowie Pfad-, Risiko- und Kohortenprüfungen bestehen. Inhaltlich gibt es aber relevante Probleme: Die echte Wahltagsrendite umfasst nur 14 Fälle; außerdem enthält die ausgeschlossene Corona-Kohorte ausgesprochen hohe Folgerenditen. Der grüne Wächter erkennt solche falschen Einordnungen bisher nicht.
mcp: node_repl/js started
mcp: node_repl/js (completed)
web search: 
web search: site.federalreserve.gov March 23 2020 support flow credit households businesses Treasury equity
web search: 
web search: site.ssga.com SPY largest most liquid ETF 2026 assets VOO ...
mcp: node_repl/js started
mcp: node_repl/js (completed)
mcp: node_repl/js started
mcp: node_repl/js (completed)
mcp: node_repl/js started
mcp: node_repl/js (completed)
codex
Die Nachrechnung bestätigt auch den Bezug zum älteren ±20-Artikel: Auf denselben 30 Gruppen beträgt der Abstand für die letzte Woche +0,66 Pp und für die früheren 15 Sitzungen +1,60 Pp. Die Einordnung passt damit. Offen bleiben vor allem falsche Wahltagsbeschriftungen, zu weit gehende Erklärungen und Wächterlücken, die ich mit zusätzlichen Gegenproben ohne Dateiänderungen nachgewiesen habe.
web search: 
web search: https://investor.vanguard.com/investment-products/etfs/profile/voo
mcp: node_repl/js started
mcp: node_repl/js (completed)
web search: 
web search: site.corporate.vanguard.com VOO largest ETF 2026 trillion
web search: 
web search: 
codex
Die Rechnungen stimmen weitgehend mit Plan v2 überein. **Die Artikel sind im aktuellen Stand dennoch nicht freigabefähig:** Sie verkaufen eine gemischte Referenztagsrendite als Wahltagsrendite und enthalten mehrere nicht gedeckte Erklärungen.

Geprüft wurden beide Faktenblätter, der gemeinsame Kern, der Wächter, alle vier Sprachfassungen, der bestehende Midterm-Artikel und alle zehn PNGs. Python 3.14.3: Wächter **0 Fehler**, eingebaute Mutationen **21/21**. Unabhängig aus den Repo-Daten: **648 Kennzahlvergleiche** sowie zusätzliche Pfad-, Risiko-, Kalender- und Kohortenprüfungen bestanden. Keine Dateien geändert; zusätzliche Gegenproben liefen ausschließlich im Speicher.

1. **Blockierend — „Am Wahltag“ hat die falsche Kohorte.**  
   Belege: [Midterm DE:66](C:/dev/SeasonalEdge/blog/posts/2026-10-30_sp500-letzte-woche-vor-midterm-wahl.md:66), FAQ Zeile 104; [EN:104](C:/dev/SeasonalEdge/blog/posts/en/2026-10-30_sp500-last-week-before-midterm-election.md:104); [Chartbeschriftung:54](C:/dev/SeasonalEdge/scripts/research/render_downdays_midterm_charts.py:54).

   **+0,37 %, positiv 23/31** beschreibt die Rendite bis **t0**. In **17/31 Fällen** ist t0 der Handelstag **vor** der Wahl. Für die tatsächlichen geöffneten Midterm-Wahltage ergeben sich **+0,4353 %, positiv 10/14**. Die korrekte Definition im Methodenteil beseitigt den falschen Bezug in Tabelle, Grafik und FAQ nicht.

   **Änderung:** Durchgehend „Referenztag t0“ verwenden. Die FAQ entweder entsprechend umformulieren oder die echte Wahltagskohorte mit **+0,44 %, 10/14** separat ausweisen. DE und EN einschließlich Grafikbeschriftungen angleichen.

2. **Wichtig — Der Wächter bindet Fließtextwerte weiterhin überwiegend nicht an ihren Inhalt.**  
   Beleg: [Wächter:197](C:/dev/SeasonalEdge/scripts/verify_downdays_midterm_blog.py:197), Prüfpfad ab Zeile 281. Die Tabellen sind zuverlässig gebunden; außerhalb davon dominieren Wertelisten und wenige Pflichtmuster.

   Folgende zusätzliche Gegenproben blieben jeweils **grün**:
   
   - Zusatz: „Nach −2-%-Tagen beträgt die Trefferquote nach 50 HT 73 %.“
   - „2008 gab es 39 solcher Tage“ → „… 211 solcher Tage“.
   - „die Trefferquote ist … niedriger“ → „… höher“.
   - „deutlich nur 1930“ → „deutlich nur 1946“.
   - Zusatz: „Am Wahltag lag die mittlere Rendite bei +1,47 %.“

   **Änderung:** Die relevanten Aussagen als vollständige Kontextverträge prüfen: Schwelle, Horizont, Kohorte, Kennzahl, Wert und Fallzahl. Gegenproben mit bereits anderweitig erlaubten Zahlen und umgekehrten Aussagen ergänzen. **21/21** belegt derzeit nur die vorhandenen Mutationen.

3. **Wichtig — Der Midterm-Datenstand ist nicht wie geplant per Prüfsumme eingefroren.**  
   Belege: [Plan:16](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-30_down_days_midterm_plan_v2.md:16), [Midterm-Lader:32](C:/dev/SeasonalEdge/scripts/research/midterm_letzte_woche_fakten.py:32), [Wächter:342](C:/dev/SeasonalEdge/scripts/verify_downdays_midterm_blog.py:342).

   SPY prüft SHA-256; Midterm prüft lediglich `snapshot_id == "midterm-2026-10"`. Veränderte Snapshot-Inhalte mit unveränderter Kennung werden akzeptiert. Eine Änderung außerhalb der ausgewerteten Fenster blieb auch im resultierenden Faktenblatt unsichtbar.

   **Änderung:** Erwarteten SHA-256 im Midterm-Faktenblatt hinterlegen und vor dem Parsen prüfen. Eine Inhaltsänderung bei gleicher Snapshot-Kennung muss scheitern.

4. **Wichtig — Der Ausschlussgrund beim ±20-Vergleich ist falsch beschrieben.**  
   Belege: [Midterm DE:77](C:/dev/SeasonalEdge/blog/posts/2026-10-30_sp500-letzte-woche-vor-midterm-wahl.md:77), EN ebenfalls Zeile 77.

   Die zusätzliche ausgeschlossene Gruppe ist **1930**, wegen des Kontrolljahres **1929**. Dessen Pfad wird zwischen **27.11.1929 und 02.12.1929** ab Offset +17 mit `ungeklaerte_luecke` ungültig. Das ist kein Nachweis eines fehlenden Tageskurses: Die NYSE-Schließungshistorie nennt ausdrücklich die Schließungen am **29.–30.11.1929**. [NYSE-Schließungshistorie, Seite 9](https://www.ltadvisors.net/Info/research/closings.pdf)

   **Änderung:** „… weil der eingefrorene Snapshot im längeren Nachlauf einen Kontrollpfad als ungültig markiert.“ Den behaupteten fehlenden Kurs streichen.

   Die größere Einordnung ist dagegen bestätigt: Auf **denselben 30 Gruppen** ergeben sich **+2,3311 Pp** für t−20→t0, **+0,6593 Pp** für t−5→t0 und **+1,6019 Pp** für t−20→t−5. Zum bestehenden Artikel besteht hier kein Zahlenwiderspruch.

5. **Wichtig — Die Krisenaussage verallgemeinert unterschiedliche Ergebnisse.**  
   Belege: [Down-Days DE:107](C:/dev/SeasonalEdge/blog/posts/2026-10-30_spy-down-days-was-danach-passiert.md:107), [EN:105](C:/dev/SeasonalEdge/blog/posts/en/2026-10-30_spy-down-days-what-happens-next.md:105).

   Für die nach der festgelegten Überschneidungsregel ausgeschlossenen −2-%-Fälle beträgt die mittlere 50-Sitzungs-Rendite:
   
   - Finanzkrisenblock: **−1,76 %, n = 51**.
   - Coronablock: **+13,03 %, n = 20**.

   Corona zieht das Mittel deutlich nach oben. Zudem liegt der **beste** Einzelfall ebenfalls im Coronablock: **+40,02 %** ab 23.03.2020. Zusammen drücken die beiden Blöcke zwar das Gesamtmittel gegenüber der verbleibenden Kohorte; „die Krisen … liefern die schlechtesten Einzelfälle“ vermittelt aber ein einseitiges Bild.

   **Änderung:** Präzisieren: „Zusammen senken diese beiden ausgeschlossenen Kohorten das Mittel; sie enthalten jedoch sowohl die schlechtesten als auch besonders starke Erholungsfälle.“

6. **Wichtig — Aus Sensitivitätsrechnungen werden Erklärungen abgeleitet.**  
   Belege: [Down-Days DE:105](C:/dev/SeasonalEdge/blog/posts/2026-10-30_spy-down-days-was-danach-passiert.md:105), Zeile 109; EN Zeilen 103/107.

   Die Ausdünnung zeigt ein anderes Ergebnis bei anderer Auswahl. Sie isoliert nicht, welcher Anteil des Vorsprungs **durch** die Häufung entsteht. Ebenso misst das Faktenblatt keine Wirkung von Notenbank und Staat und keine Häufigkeit solcher Unterstützung. Die Maßnahmen 2020 sind belegt; ihre Erklärungskraft für diese Renditen wurde hier nicht untersucht. [Fed-Mitteilung vom 23.03.2020](https://www.federalreserve.gov/newsevents/pressreleases/monetary20200323b.htm)

   **Änderung:** „Das Ergebnis reagiert stark auf die Auswahl innerhalb der Häufungen.“ Den Satz mit „oft mit Hilfe …“ streichen oder als mögliche, extern belegte Erklärung kennzeichnen und die fehlende Untersuchung ausdrücklich nennen.

7. **Wichtig — Fallzahlen fehlen bei Grafiken und einzelnen Horizonten.**  
   Belege: [Rendite-/Risikografik:129](C:/dev/SeasonalEdge/scripts/research/render_downdays_midterm_charts.py:129), [Tabellengenerator:91](C:/dev/SeasonalEdge/scripts/verify_downdays_midterm_blog.py:91).

   In der Rendite-/Risikografik wird `ns` berechnet, aber nicht angezeigt. Die Basiskohorten unterscheiden sich: **5 016** Fälle für 15, **5 001** für 30 und **4 981** für 50 Sitzungen. Die Pfadgrafik nennt nur die Ereigniskohorte **n = 211**, nicht ihre Basiskohorte **n = 4 981**.

   **Änderung:** Fallzahlen je Horizont beziehungsweise je dargestellter Kohorte ausgeben; insbesondere Rendite und Risiko im Vergleichsdiagramm eindeutig zuordnen.

8. **Hinweis — Zwei kleinere Textkorrekturen in beiden Sprachen.**  
   [Down-Days DE:95](C:/dev/SeasonalEdge/blog/posts/2026-10-30_spy-down-days-was-danach-passiert.md:95): Oktober 2008 hatte **15 negative Tage**, davon **11 mit mindestens 2 % Verlust**. Daher „Elf Tage mit mindestens 2 % Verlust“ schreiben.

   [DE:33](C:/dev/SeasonalEdge/blog/posts/2026-10-30_spy-down-days-was-danach-passiert.md:33), EN Zeile 31: „größter ETF“ streichen. VOO weist bereits per September 2026 mehr Vermögen aus als SPY per Oktober. „Ein ETF auf den S&P 500“ genügt. [Vanguard-Faktenblatt](https://fund-docs.vanguard.com/F0968.pdf), [SPY-Produktdaten](https://www.ssga.com/us/en/intermediary/etfs/state-street-spdr-sp-500-etf-trust-spy)

Die übrigen gezielt abgefragten Aussagen sind rechnerisch gedeckt: Trefferquote **145/211 gegenüber 3 641/4 981**, sechs negative Midterm-Wochen und nur 1930 unter −1 %, Öffnung an Midterm-Wahltagen seit 1970 sowie der deutlich größere Abstand in der zweiten SPY-Hälfte. DE und EN sind inhaltlich weitgehend deckungsgleich und teilen die genannten Fehler. Der Intervallkern und die vorgeschriebenen Kohortenregeln lieferten bei den geprüften Daten keine Rechenabweichung.

**NICHT FREIGABEFÄHIG.**
tokens used
125.921
Die Rechnungen stimmen weitgehend mit Plan v2 überein. **Die Artikel sind im aktuellen Stand dennoch nicht freigabefähig:** Sie verkaufen eine gemischte Referenztagsrendite als Wahltagsrendite und enthalten mehrere nicht gedeckte Erklärungen.

Geprüft wurden beide Faktenblätter, der gemeinsame Kern, der Wächter, alle vier Sprachfassungen, der bestehende Midterm-Artikel und alle zehn PNGs. Python 3.14.3: Wächter **0 Fehler**, eingebaute Mutationen **21/21**. Unabhängig aus den Repo-Daten: **648 Kennzahlvergleiche** sowie zusätzliche Pfad-, Risiko-, Kalender- und Kohortenprüfungen bestanden. Keine Dateien geändert; zusätzliche Gegenproben liefen ausschließlich im Speicher.

1. **Blockierend — „Am Wahltag“ hat die falsche Kohorte.**  
   Belege: [Midterm DE:66](C:/dev/SeasonalEdge/blog/posts/2026-10-30_sp500-letzte-woche-vor-midterm-wahl.md:66), FAQ Zeile 104; [EN:104](C:/dev/SeasonalEdge/blog/posts/en/2026-10-30_sp500-last-week-before-midterm-election.md:104); [Chartbeschriftung:54](C:/dev/SeasonalEdge/scripts/research/render_downdays_midterm_charts.py:54).

   **+0,37 %, positiv 23/31** beschreibt die Rendite bis **t0**. In **17/31 Fällen** ist t0 der Handelstag **vor** der Wahl. Für die tatsächlichen geöffneten Midterm-Wahltage ergeben sich **+0,4353 %, positiv 10/14**. Die korrekte Definition im Methodenteil beseitigt den falschen Bezug in Tabelle, Grafik und FAQ nicht.

   **Änderung:** Durchgehend „Referenztag t0“ verwenden. Die FAQ entweder entsprechend umformulieren oder die echte Wahltagskohorte mit **+0,44 %, 10/14** separat ausweisen. DE und EN einschließlich Grafikbeschriftungen angleichen.

2. **Wichtig — Der Wächter bindet Fließtextwerte weiterhin überwiegend nicht an ihren Inhalt.**  
   Beleg: [Wächter:197](C:/dev/SeasonalEdge/scripts/verify_downdays_midterm_blog.py:197), Prüfpfad ab Zeile 281. Die Tabellen sind zuverlässig gebunden; außerhalb davon dominieren Wertelisten und wenige Pflichtmuster.

   Folgende zusätzliche Gegenproben blieben jeweils **grün**:
   
   - Zusatz: „Nach −2-%-Tagen beträgt die Trefferquote nach 50 HT 73 %.“
   - „2008 gab es 39 solcher Tage“ → „… 211 solcher Tage“.
   - „die Trefferquote ist … niedriger“ → „… höher“.
   - „deutlich nur 1930“ → „deutlich nur 1946“.
   - Zusatz: „Am Wahltag lag die mittlere Rendite bei +1,47 %.“

   **Änderung:** Die relevanten Aussagen als vollständige Kontextverträge prüfen: Schwelle, Horizont, Kohorte, Kennzahl, Wert und Fallzahl. Gegenproben mit bereits anderweitig erlaubten Zahlen und umgekehrten Aussagen ergänzen. **21/21** belegt derzeit nur die vorhandenen Mutationen.

3. **Wichtig — Der Midterm-Datenstand ist nicht wie geplant per Prüfsumme eingefroren.**  
   Belege: [Plan:16](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-30_down_days_midterm_plan_v2.md:16), [Midterm-Lader:32](C:/dev/SeasonalEdge/scripts/research/midterm_letzte_woche_fakten.py:32), [Wächter:342](C:/dev/SeasonalEdge/scripts/verify_downdays_midterm_blog.py:342).

   SPY prüft SHA-256; Midterm prüft lediglich `snapshot_id == "midterm-2026-10"`. Veränderte Snapshot-Inhalte mit unveränderter Kennung werden akzeptiert. Eine Änderung außerhalb der ausgewerteten Fenster blieb auch im resultierenden Faktenblatt unsichtbar.

   **Änderung:** Erwarteten SHA-256 im Midterm-Faktenblatt hinterlegen und vor dem Parsen prüfen. Eine Inhaltsänderung bei gleicher Snapshot-Kennung muss scheitern.

4. **Wichtig — Der Ausschlussgrund beim ±20-Vergleich ist falsch beschrieben.**  
   Belege: [Midterm DE:77](C:/dev/SeasonalEdge/blog/posts/2026-10-30_sp500-letzte-woche-vor-midterm-wahl.md:77), EN ebenfalls Zeile 77.

   Die zusätzliche ausgeschlossene Gruppe ist **1930**, wegen des Kontrolljahres **1929**. Dessen Pfad wird zwischen **27.11.1929 und 02.12.1929** ab Offset +17 mit `ungeklaerte_luecke` ungültig. Das ist kein Nachweis eines fehlenden Tageskurses: Die NYSE-Schließungshistorie nennt ausdrücklich die Schließungen am **29.–30.11.1929**. [NYSE-Schließungshistorie, Seite 9](https://www.ltadvisors.net/Info/research/closings.pdf)

   **Änderung:** „… weil der eingefrorene Snapshot im längeren Nachlauf einen Kontrollpfad als ungültig markiert.“ Den behaupteten fehlenden Kurs streichen.

   Die größere Einordnung ist dagegen bestätigt: Auf **denselben 30 Gruppen** ergeben sich **+2,3311 Pp** für t−20→t0, **+0,6593 Pp** für t−5→t0 und **+1,6019 Pp** für t−20→t−5. Zum bestehenden Artikel besteht hier kein Zahlenwiderspruch.

5. **Wichtig — Die Krisenaussage verallgemeinert unterschiedliche Ergebnisse.**  
   Belege: [Down-Days DE:107](C:/dev/SeasonalEdge/blog/posts/2026-10-30_spy-down-days-was-danach-passiert.md:107), [EN:105](C:/dev/SeasonalEdge/blog/posts/en/2026-10-30_spy-down-days-what-happens-next.md:105).

   Für die nach der festgelegten Überschneidungsregel ausgeschlossenen −2-%-Fälle beträgt die mittlere 50-Sitzungs-Rendite:
   
   - Finanzkrisenblock: **−1,76 %, n = 51**.
   - Coronablock: **+13,03 %, n = 20**.

   Corona zieht das Mittel deutlich nach oben. Zudem liegt der **beste** Einzelfall ebenfalls im Coronablock: **+40,02 %** ab 23.03.2020. Zusammen drücken die beiden Blöcke zwar das Gesamtmittel gegenüber der verbleibenden Kohorte; „die Krisen … liefern die schlechtesten Einzelfälle“ vermittelt aber ein einseitiges Bild.

   **Änderung:** Präzisieren: „Zusammen senken diese beiden ausgeschlossenen Kohorten das Mittel; sie enthalten jedoch sowohl die schlechtesten als auch besonders starke Erholungsfälle.“

6. **Wichtig — Aus Sensitivitätsrechnungen werden Erklärungen abgeleitet.**  
   Belege: [Down-Days DE:105](C:/dev/SeasonalEdge/blog/posts/2026-10-30_spy-down-days-was-danach-passiert.md:105), Zeile 109; EN Zeilen 103/107.

   Die Ausdünnung zeigt ein anderes Ergebnis bei anderer Auswahl. Sie isoliert nicht, welcher Anteil des Vorsprungs **durch** die Häufung entsteht. Ebenso misst das Faktenblatt keine Wirkung von Notenbank und Staat und keine Häufigkeit solcher Unterstützung. Die Maßnahmen 2020 sind belegt; ihre Erklärungskraft für diese Renditen wurde hier nicht untersucht. [Fed-Mitteilung vom 23.03.2020](https://www.federalreserve.gov/newsevents/pressreleases/monetary20200323b.htm)

   **Änderung:** „Das Ergebnis reagiert stark auf die Auswahl innerhalb der Häufungen.“ Den Satz mit „oft mit Hilfe …“ streichen oder als mögliche, extern belegte Erklärung kennzeichnen und die fehlende Untersuchung ausdrücklich nennen.

7. **Wichtig — Fallzahlen fehlen bei Grafiken und einzelnen Horizonten.**  
   Belege: [Rendite-/Risikografik:129](C:/dev/SeasonalEdge/scripts/research/render_downdays_midterm_charts.py:129), [Tabellengenerator:91](C:/dev/SeasonalEdge/scripts/verify_downdays_midterm_blog.py:91).

   In der Rendite-/Risikografik wird `ns` berechnet, aber nicht angezeigt. Die Basiskohorten unterscheiden sich: **5 016** Fälle für 15, **5 001** für 30 und **4 981** für 50 Sitzungen. Die Pfadgrafik nennt nur die Ereigniskohorte **n = 211**, nicht ihre Basiskohorte **n = 4 981**.

   **Änderung:** Fallzahlen je Horizont beziehungsweise je dargestellter Kohorte ausgeben; insbesondere Rendite und Risiko im Vergleichsdiagramm eindeutig zuordnen.

8. **Hinweis — Zwei kleinere Textkorrekturen in beiden Sprachen.**  
   [Down-Days DE:95](C:/dev/SeasonalEdge/blog/posts/2026-10-30_spy-down-days-was-danach-passiert.md:95): Oktober 2008 hatte **15 negative Tage**, davon **11 mit mindestens 2 % Verlust**. Daher „Elf Tage mit mindestens 2 % Verlust“ schreiben.

   [DE:33](C:/dev/SeasonalEdge/blog/posts/2026-10-30_spy-down-days-was-danach-passiert.md:33), EN Zeile 31: „größter ETF“ streichen. VOO weist bereits per September 2026 mehr Vermögen aus als SPY per Oktober. „Ein ETF auf den S&P 500“ genügt. [Vanguard-Faktenblatt](https://fund-docs.vanguard.com/F0968.pdf), [SPY-Produktdaten](https://www.ssga.com/us/en/intermediary/etfs/state-street-spdr-sp-500-etf-trust-spy)

Die übrigen gezielt abgefragten Aussagen sind rechnerisch gedeckt: Trefferquote **145/211 gegenüber 3 641/4 981**, sechs negative Midterm-Wochen und nur 1930 unter −1 %, Öffnung an Midterm-Wahltagen seit 1970 sowie der deutlich größere Abstand in der zweiten SPY-Hälfte. DE und EN sind inhaltlich weitgehend deckungsgleich und teilen die genannten Fehler. Der Intervallkern und die vorgeschriebenen Kohortenregeln lieferten bei den geprüften Daten keine Rechenabweichung.

**NICHT FREIGABEFÄHIG.**
