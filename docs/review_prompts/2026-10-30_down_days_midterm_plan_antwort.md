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
session id: 01a18e4e-d743-7741-867f-313e9b758e9c
--------
user
Du bist Reviewer für eine quantitative Finanzstudie im Repo SeasonAlpha (öffentlich). Lies docs/review_prompts/2026-10-30_down_days_midterm_plan.md vollständig. Prüfe den Plan methodisch und am Code: shared/elections.py (fenster_rendite, aggregiere, kontrolljahre), die Struktur von landing/data/wahlen_snapshots/midterm-2026-10.json, blog/daten/spy_2026-10-29.json, und den bestehenden Artikel blog/posts/2026-10-07_midterm-wahltag-boerse.md. Antworte auf Deutsch mit nummerierten Befunden (Schwere: blockierend / wichtig / Hinweis), je Befund Beleg (Datei:Zeile oder Rechnung) und konkreter Änderung am Plan. Beantworte die fünf Fragen am Ende des Plans ausdrücklich. Schließe mit: FREIGABE, FREIGABE MIT AUFLAGEN oder NICHT TRAGFÄHIG.
codex
Ich lese zuerst die aktuellen Versionseinträge und den vollständigen Review-Plan. Danach prüfe ich Rechenwege, Datenstruktur und Artikelaussagen gegen die vorgeschlagene Methodik.
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content CLAUDE.md -TotalCount 240; Get-Content docs/review_prompts/2026-10-30_down_days_midterm_plan.md' in C:\dev\SeasonalEdge
 exited -1 in 0ms:
Failed to create unified exec process: helper_unknown_error: setup refresh had errors
2026-10-30T19:34:58.257466Z ERROR codex_core::tools::router: error=exec_command failed: CreateProcess { message: "Rejected(\"Failed to create unified exec process: helper_unknown_error: setup refresh had errors\")" }
mcp: node_repl/js started
mcp: node_repl/js (completed)
mcp: node_repl/js started
mcp: node_repl/js (completed)
mcp: node_repl/js started
mcp: node_repl/js (completed)
codex
Zwei methodische Schwachstellen zeichnen sich ab: Nicht überlappende Fenster sind noch keine unabhängigen Fälle, und der Zufallsvergleich bildet die Auswahl nach Verlusttagen bisher nicht ab. Im Wahlkern prüfe ich außerdem, welche geplanten Kennzahlen die bestehenden Funktionen tatsächlich liefern.
mcp: node_repl/js started
mcp: node_repl/js (completed)
mcp: node_repl/js started
mcp: node_repl/js (completed)
mcp: node_repl/js started
mcp: node_repl/js (completed)
codex
Die direkte Python-Prüfung bestätigt einen konkreten Fallstrick: Für `(x=5, y=0)` liefert `aggregiere` Trefferquote und Vergleichsdifferenz für den leeren Nachlauf, also jeweils null. Für die Vorwoche braucht es eine Ergänzung im gemeinsamen Kern. Außerdem hat das kurze Fenster 31 vollständige Vergleichstripel; der bestehende 20-Tage-Artikel hat 30. Die SPY-Datei enthält nach dem Projektkalender keine fehlenden oder zusätzlichen Sitzungen.
mcp: node_repl/js started
mcp: node_repl/js (completed)
codex
Der Plan trägt als **beschreibende Untersuchung**, benötigt aber Änderungen am Testverfahren von Studie A und am Rechenvertrag von Studie B. Ich habe den vollständigen Plan gelesen, die genannten Dateien geprüft und die bestehende Python-Aggregation direkt ausgeführt. Dateien und Datenbank wurden nicht verändert.

1. **Blockierend — Der Zufallsvergleich liefert in dieser Form keinen kalibrierten Signifikanztest.**

   **Beleg:** [Plan:55](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-30_down_days_midterm_plan.md:55). Dieselbe Mindestdistanz macht zufällige Starttage und entzerrte Verlusttage nicht austauschbar. Letztere entstehen durch Schwellenüberschreitungen und eine chronologische Auswahl in wechselnden Marktregimen.

   Schon die Abstandsvorgabe kann den Vergleich gegen das unbedingte Basismittel verschieben: Bei vier Startpositionen, Abstand ≥ 2 und zwei gezogenen Positionen sind die zulässigen Mengen `{1,3}`, `{1,4}`, `{2,4}`. Bei gleichverteilter Auswahl dieser Mengen und Werten `[1,0,0,1]` beträgt das erwartete Stichprobenmittel **2/3**, das Basismittel aber **1/2**. „Gierige Ziehung“ legt zudem keine eindeutige Verteilung fest.

   **Planänderung:** Für diese Fassung p-Werte und Holm streichen; den Abstand zur Basis beschreibend berichten. Soll Inferenz bleiben, braucht es vor dem Ergebnislauf einen eigenen, vollständig spezifizierten und unter einer bekannten Nullhypothese geprüften Resampling-Plan. Plus-eins und Holm reparieren keine falsche Nullverteilung.

2. **Blockierend — Die bestehenden Wahlfunktionen liefern nicht alle vorgesehenen Kennzahlen.**

   **Beleg:** [elections.py:216](C:/dev/SeasonalEdge/shared/elections.py:216), [elections.py:339](C:/dev/SeasonalEdge/shared/elections.py:339), [elections.py:375](C:/dev/SeasonalEdge/shared/elections.py:375). Beim tatsächlich ausgeführten Aufruf `aggregiere(snapshot, "^GSPC", "midterm", 5, 0)` sind `nachlauf_mittel`, `trefferquote` und `differenz_mittel` jeweils **0**: Sie beziehen sich auf den leeren Nachlauf. Die Wochenrendite steht im Vorlauf beziehungsweise Gesamtfenster. Ein Fenster vollständig vor t0 wird vom bisherigen Vertrag nicht unterstützt; `fenster_rendite(p, 5, -1)` greift beispielsweise außerhalb der ausgeschnittenen Liste auf `werte[x]` zu.

   **Planänderung:** Im gemeinsamen Kern einen ausdrücklich unterstützten Vertrag für beliebige Offsetintervalle vorsehen: Rendite von Offset a bis b, Gültigkeitsprüfung aller benötigten Kurse und gepaarte Einzelwerte. Darauf Wochenmedian, Trefferquote und Differenzen berechnen. Unabhängige Sollfälle für `−5→0`, `−5→−1` und einzelne Sitzungsrenditen verlangen.

3. **Wichtig — Entzerrung verändert die untersuchte Frage; sie erzeugt keine unabhängige Stichprobe.**

   **Beleg:** [Plan:46](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-30_down_days_midterm_plan.md:46). Abstand ≥ h verhindert gemeinsame **Vorwärtsrenditen**: Die Fenster enthalten `t+1…t+h` und frühestens `t+h+1…t+2h`. Gemeinsame Krisen- und Volatilitätsregime bleiben bestehen. Die Auswahl bevorzugt frühe zulässige Schwellenereignisse; dass deren Folgekurse „meist weiter fallen“, ist hingegen keine methodisch gesicherte Tatsache.

   **Planänderung:** Die zweite Stichprobe „chronologisch ausgedünnt“ nennen und die geänderte Zielgröße erläutern. Alle Ereignisse bleiben die primäre Beschreibung. „Letzter Tag einer Häufung“ nicht als handelbare Alternative verwenden: Dafür braucht man zukünftige Ereignisse. Eine zufällige Auswahl wäre höchstens eine vorab definierte Sensitivitätsanalyse mit genauer Häufungsregel.

4. **Wichtig — Robustheitsprüfungen und Pfadchart haben noch keinen eindeutigen Stichprobenvertrag.**

   **Beleg:** [Plan:61](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-30_down_days_midterm_plan.md:61). „Ohne Krisenblöcke“ kann nur Ereignistage oder sämtliche berührten Renditefenster meinen. Ein Ereignis vor September 2008 kann beispielsweise trotzdem Krisenrenditen enthalten. Bei den Hälften ist offen, ob Vorwärtsfenster die Halbzeitgrenze überschreiten dürfen. Ein Pfad bis 50 kann mit jedem Offset andere Fälle enthalten.

   **Planänderung:** Festlegen:

   - Krisenausschluss betrifft Ereignistag **und alle Folgesitzungen** des jeweiligen Fensters; dieselbe Regel gilt für die Basis.
   - Halbzeitvergleiche verwenden vollständig innerhalb der jeweiligen Hälfte liegende Fenster.
   - Der Pfad 0…50 verwendet durchgehend dieselben vollständig beobachteten Ereignisse und dieselbe Basiskohorte.
   - Nach jeder Einschränkung werden Entzerrung und Basis neu berechnet.

   Die unterschiedlichen Verfügbarkeiten sind real: Die vollständige SPY-Basis umfasst bei h = 15/30/50 **5.016/5.001/4.981 Starttage**.

5. **Wichtig — Das alternative Wahlfenster hat vier Renditen und entfernt historisch nicht immer den Wahltag.**

   **Beleg:** [Plan:88](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-30_down_days_midterm_plan.md:88). `t−5→t−1` enthält **vier**, nicht fünf Sitzungsrenditen. Bei geschlossenem Wahltag liegt t0 bereits am Vortag; das alternative Fenster entfernt dann dessen Rendite. Außerdem ist „Wahltag ab 1984 geöffnet“ für die Midterm-Stichprobe irreführend: Der Snapshot enthält t0 am Wahltag bereits für **1970, 1974, 1978 und 1982**.

   **Planänderung:** Hauptzahl `−5→0` als „fünf Sitzungsrenditen bis zum Referenzschluss“ definieren. Die Zusatzanalyse korrekt als Vier-Sitzungs-Fenster benennen. Falls tatsächlich fünf Sitzungen vor dem Wahltag untersucht werden sollen, ein separates, datumsbezogenes Fenster definieren. Einzelrendite bei Offset j ausdrücklich als `100·(c[j]/c[j−1]−1)` festlegen; für j = −5 wird auch c[−6] benötigt.

6. **Wichtig — Fallzahlen müssen pro Fenster neu entstehen; 2026 ist im Snapshot vorhanden.**

   **Beleg:** [Plan:91](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-30_down_days_midterm_plan.md:91), [Plan:108](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-30_down_days_midterm_plan.md:108), [elections.py:331](C:/dev/SeasonalEdge/shared/elections.py:331). Die direkte Rechnung ergibt für `−5→0` **31 Wahlen und 31 vollständige Tripel**, gegenüber **31/30** im bestehenden ±20-Fenster. Seit 1971 sind es **13/13**. Der Snapshot enthält außerdem `us-midterm-2026` als Live-Pfad; `aggregiere` trennt ihn anhand des Status von historischen Fällen.

   **Planänderung:** „2026 ist nicht enthalten“ durch „2026 ist aus der historischen Stichprobe ausgeschlossen“ ersetzen. `type`, `status`, Reihenkennung und Gültigkeit ausdrücklich prüfen. Für jede Tabelle die tatsächlich verwendeten Wahl- und Kontrolljahre exportieren; beim Vergleich beider Wochenfenster zusätzlich eine gemeinsame Kohorte verwenden.

7. **Wichtig — Schlusskursrendite ist keine nachgewiesene Ausführungsmöglichkeit; der Risikobegriff ist zu weit.**

   **Beleg:** [Plan:33](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-30_down_days_midterm_plan.md:33), [Plan:65](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-30_down_days_midterm_plan.md:65). Der endgültige Schluss bestätigt das Ereignis, garantiert aber keinen anschließenden Einstieg zu genau diesem Schluss. Das Minimum eines Schlusskurspfads misst weder Intraday-Verluste noch den maximalen Rückgang von einem zwischenzeitlichen Hoch.

   **Planänderung:** Einstiegssatz ersetzen durch „beschreibende Rendite ab Ereignisschluss, ohne Ausführungsannahme“. Risikokennzahl definieren als  
   `min(0, F₁(t), …, F₁₅(t))`  
   und „größter zwischenzeitlicher Verlust gegenüber dem Ereignisschluss, anhand von Schlusskursen“ nennen. Das Einbeziehen von null verhindert positive „Verluste“.

8. **Wichtig — Unterschiedliche Fenster dürfen unterschiedliche Ergebnisse haben; die Risikoprämien-Erklärung ist unbelegt.**

   **Beleg:** [Plan:69](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-30_down_days_midterm_plan.md:69), [Plan:106](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-30_down_days_midterm_plan.md:106). Die neue Woche muss weder Richtung noch Größenordnung des bisherigen 20-Sitzungs-Vorlaufs teilen. Der bestehende Artikel grenzt Kausalität selbst ein ([Artikel:43](C:/dev/SeasonalEdge/blog/posts/2026-10-07_midterm-wahltag-boerse.md:43)). Ebenso weist der Plan nicht nach, welcher Anteil späterer Renditen eine Risikoprämie ist.

   **Planänderung:** „Darf nicht widersprechen“ durch „muss identische Größen reproduzieren und abweichende Fenster und Kohorten erklären“ ersetzen. Risikoprämie als mögliche Erklärung formulieren. Zulässig sind historische bedingte Renditebeschreibungen, keine nachgewiesene Wahlwirkung, Prognosefähigkeit oder Handelsrendite.

9. **Hinweis — Datenbasis und Wiederholbarkeit sind weitgehend plausibel, brauchen aber feste Prüfkriterien.**

   **Beleg:** Die SPY-Datei enthält **5.491** geordnete, eindeutige Zeilen ohne ungültige Zahlen. Gegen den Projektkalender fehlen keine erwarteten Sitzungen und existieren keine zusätzlichen; die **13 Nullrenditen seit 2006** sind reproduzierbar. Unter den **5.490 benachbarten Kurspaaren** beträgt die größte absolute Abweichung zwischen gespeichertem `log_return` und `log(close_t/close_{t−1})` rund **6,9·10⁻⁸**. Das bestätigt interne Konsistenz, nicht unabhängig die Dividendenbehandlung des Lieferanten.

   **Planänderung:** Dateihashes, Code-Commit, Datenprüfungen und Ausschlusslisten im Ergebnisartefakt festhalten. Adjustierte SPY-Renditen als Gesamtrendite-Näherung kennzeichnen; Studie B misst dagegen Index-Kursrenditen. Jahreshäufigkeiten zusätzlich durch beobachtete Sitzungen teilen, weil die Randjahre 2006 und 2026 unvollständig sind. Der Zahlenwächter muss Kennzahlen ihrem konkreten Fenster und ihrer Kohorte zuordnen; eine bloße Liste erlaubter Zahlen genügt dafür nicht.

Die fünf Fragen ausdrücklich beantwortet:

1. **Entzerrung:** Als vorab festgelegte beschreibende Auswahl vertretbar. Sie bevorzugt frühe zulässige Ereignisse und beseitigt Regimeabhängigkeit nicht. Letzte Häufungstage benötigen Zukunftswissen; zufällige Häufungstage sind keine grundsätzlich bessere Hauptstichprobe.

2. **Zufallsvergleich:** In der vorgeschlagenen Form nicht ausreichend. Ein Blockansatz kann zeitliche Abhängigkeit berücksichtigen, braucht aber ebenfalls eine definierte Nullhypothese und eine konsistente Behandlung von Ereignisauswahl und Folgerenditen. Für diese Artikel empfehle ich die beschreibende Variante ohne p-Werte.

3. **Adjustierte Kurse:** Die Kennzeichnung reicht für die beschreibende Studie, wenn Renditebasis und Lieferantenabhängigkeit klar bleiben. Sie reicht nicht für die Behauptung einer exakt nachgebildeten Anlegerrendite.

4. **Hauptzahl Studie B:** **`t−5→t0`**, wegen der konstanten fünf Sitzungsrenditen und Anschlussfähigkeit an den bisherigen Artikel. Als Ende gilt der Referenzschluss; „ohne Wahltag“ verlangt eine eigene kalenderbezogene Definition.

5. **Fehlendes und zu starke Aussagen:** Vor allem Testnullhypothese, unterstützte Intervallrechnung, Regeln für Robustheitskohorten, eindeutige Risikokennzahl und Ausführungsabgrenzung. Auf einen Vorzeichentest in B würde ich verzichten: Er könnte die Wahrscheinlichkeit einer positiven gepaarten Differenz prüfen, aber weder deren Mittelwert noch Kausalität; die bereits betrachtete Fensterfamilie würde durch einen nachträglich hinzugefügten Test nicht verschwinden.

**FREIGABE MIT AUFLAGEN**
tokens used
65.076
Der Plan trägt als **beschreibende Untersuchung**, benötigt aber Änderungen am Testverfahren von Studie A und am Rechenvertrag von Studie B. Ich habe den vollständigen Plan gelesen, die genannten Dateien geprüft und die bestehende Python-Aggregation direkt ausgeführt. Dateien und Datenbank wurden nicht verändert.

1. **Blockierend — Der Zufallsvergleich liefert in dieser Form keinen kalibrierten Signifikanztest.**

   **Beleg:** [Plan:55](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-30_down_days_midterm_plan.md:55). Dieselbe Mindestdistanz macht zufällige Starttage und entzerrte Verlusttage nicht austauschbar. Letztere entstehen durch Schwellenüberschreitungen und eine chronologische Auswahl in wechselnden Marktregimen.

   Schon die Abstandsvorgabe kann den Vergleich gegen das unbedingte Basismittel verschieben: Bei vier Startpositionen, Abstand ≥ 2 und zwei gezogenen Positionen sind die zulässigen Mengen `{1,3}`, `{1,4}`, `{2,4}`. Bei gleichverteilter Auswahl dieser Mengen und Werten `[1,0,0,1]` beträgt das erwartete Stichprobenmittel **2/3**, das Basismittel aber **1/2**. „Gierige Ziehung“ legt zudem keine eindeutige Verteilung fest.

   **Planänderung:** Für diese Fassung p-Werte und Holm streichen; den Abstand zur Basis beschreibend berichten. Soll Inferenz bleiben, braucht es vor dem Ergebnislauf einen eigenen, vollständig spezifizierten und unter einer bekannten Nullhypothese geprüften Resampling-Plan. Plus-eins und Holm reparieren keine falsche Nullverteilung.

2. **Blockierend — Die bestehenden Wahlfunktionen liefern nicht alle vorgesehenen Kennzahlen.**

   **Beleg:** [elections.py:216](C:/dev/SeasonalEdge/shared/elections.py:216), [elections.py:339](C:/dev/SeasonalEdge/shared/elections.py:339), [elections.py:375](C:/dev/SeasonalEdge/shared/elections.py:375). Beim tatsächlich ausgeführten Aufruf `aggregiere(snapshot, "^GSPC", "midterm", 5, 0)` sind `nachlauf_mittel`, `trefferquote` und `differenz_mittel` jeweils **0**: Sie beziehen sich auf den leeren Nachlauf. Die Wochenrendite steht im Vorlauf beziehungsweise Gesamtfenster. Ein Fenster vollständig vor t0 wird vom bisherigen Vertrag nicht unterstützt; `fenster_rendite(p, 5, -1)` greift beispielsweise außerhalb der ausgeschnittenen Liste auf `werte[x]` zu.

   **Planänderung:** Im gemeinsamen Kern einen ausdrücklich unterstützten Vertrag für beliebige Offsetintervalle vorsehen: Rendite von Offset a bis b, Gültigkeitsprüfung aller benötigten Kurse und gepaarte Einzelwerte. Darauf Wochenmedian, Trefferquote und Differenzen berechnen. Unabhängige Sollfälle für `−5→0`, `−5→−1` und einzelne Sitzungsrenditen verlangen.

3. **Wichtig — Entzerrung verändert die untersuchte Frage; sie erzeugt keine unabhängige Stichprobe.**

   **Beleg:** [Plan:46](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-30_down_days_midterm_plan.md:46). Abstand ≥ h verhindert gemeinsame **Vorwärtsrenditen**: Die Fenster enthalten `t+1…t+h` und frühestens `t+h+1…t+2h`. Gemeinsame Krisen- und Volatilitätsregime bleiben bestehen. Die Auswahl bevorzugt frühe zulässige Schwellenereignisse; dass deren Folgekurse „meist weiter fallen“, ist hingegen keine methodisch gesicherte Tatsache.

   **Planänderung:** Die zweite Stichprobe „chronologisch ausgedünnt“ nennen und die geänderte Zielgröße erläutern. Alle Ereignisse bleiben die primäre Beschreibung. „Letzter Tag einer Häufung“ nicht als handelbare Alternative verwenden: Dafür braucht man zukünftige Ereignisse. Eine zufällige Auswahl wäre höchstens eine vorab definierte Sensitivitätsanalyse mit genauer Häufungsregel.

4. **Wichtig — Robustheitsprüfungen und Pfadchart haben noch keinen eindeutigen Stichprobenvertrag.**

   **Beleg:** [Plan:61](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-30_down_days_midterm_plan.md:61). „Ohne Krisenblöcke“ kann nur Ereignistage oder sämtliche berührten Renditefenster meinen. Ein Ereignis vor September 2008 kann beispielsweise trotzdem Krisenrenditen enthalten. Bei den Hälften ist offen, ob Vorwärtsfenster die Halbzeitgrenze überschreiten dürfen. Ein Pfad bis 50 kann mit jedem Offset andere Fälle enthalten.

   **Planänderung:** Festlegen:

   - Krisenausschluss betrifft Ereignistag **und alle Folgesitzungen** des jeweiligen Fensters; dieselbe Regel gilt für die Basis.
   - Halbzeitvergleiche verwenden vollständig innerhalb der jeweiligen Hälfte liegende Fenster.
   - Der Pfad 0…50 verwendet durchgehend dieselben vollständig beobachteten Ereignisse und dieselbe Basiskohorte.
   - Nach jeder Einschränkung werden Entzerrung und Basis neu berechnet.

   Die unterschiedlichen Verfügbarkeiten sind real: Die vollständige SPY-Basis umfasst bei h = 15/30/50 **5.016/5.001/4.981 Starttage**.

5. **Wichtig — Das alternative Wahlfenster hat vier Renditen und entfernt historisch nicht immer den Wahltag.**

   **Beleg:** [Plan:88](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-30_down_days_midterm_plan.md:88). `t−5→t−1` enthält **vier**, nicht fünf Sitzungsrenditen. Bei geschlossenem Wahltag liegt t0 bereits am Vortag; das alternative Fenster entfernt dann dessen Rendite. Außerdem ist „Wahltag ab 1984 geöffnet“ für die Midterm-Stichprobe irreführend: Der Snapshot enthält t0 am Wahltag bereits für **1970, 1974, 1978 und 1982**.

   **Planänderung:** Hauptzahl `−5→0` als „fünf Sitzungsrenditen bis zum Referenzschluss“ definieren. Die Zusatzanalyse korrekt als Vier-Sitzungs-Fenster benennen. Falls tatsächlich fünf Sitzungen vor dem Wahltag untersucht werden sollen, ein separates, datumsbezogenes Fenster definieren. Einzelrendite bei Offset j ausdrücklich als `100·(c[j]/c[j−1]−1)` festlegen; für j = −5 wird auch c[−6] benötigt.

6. **Wichtig — Fallzahlen müssen pro Fenster neu entstehen; 2026 ist im Snapshot vorhanden.**

   **Beleg:** [Plan:91](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-30_down_days_midterm_plan.md:91), [Plan:108](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-30_down_days_midterm_plan.md:108), [elections.py:331](C:/dev/SeasonalEdge/shared/elections.py:331). Die direkte Rechnung ergibt für `−5→0` **31 Wahlen und 31 vollständige Tripel**, gegenüber **31/30** im bestehenden ±20-Fenster. Seit 1971 sind es **13/13**. Der Snapshot enthält außerdem `us-midterm-2026` als Live-Pfad; `aggregiere` trennt ihn anhand des Status von historischen Fällen.

   **Planänderung:** „2026 ist nicht enthalten“ durch „2026 ist aus der historischen Stichprobe ausgeschlossen“ ersetzen. `type`, `status`, Reihenkennung und Gültigkeit ausdrücklich prüfen. Für jede Tabelle die tatsächlich verwendeten Wahl- und Kontrolljahre exportieren; beim Vergleich beider Wochenfenster zusätzlich eine gemeinsame Kohorte verwenden.

7. **Wichtig — Schlusskursrendite ist keine nachgewiesene Ausführungsmöglichkeit; der Risikobegriff ist zu weit.**

   **Beleg:** [Plan:33](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-30_down_days_midterm_plan.md:33), [Plan:65](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-30_down_days_midterm_plan.md:65). Der endgültige Schluss bestätigt das Ereignis, garantiert aber keinen anschließenden Einstieg zu genau diesem Schluss. Das Minimum eines Schlusskurspfads misst weder Intraday-Verluste noch den maximalen Rückgang von einem zwischenzeitlichen Hoch.

   **Planänderung:** Einstiegssatz ersetzen durch „beschreibende Rendite ab Ereignisschluss, ohne Ausführungsannahme“. Risikokennzahl definieren als  
   `min(0, F₁(t), …, F₁₅(t))`  
   und „größter zwischenzeitlicher Verlust gegenüber dem Ereignisschluss, anhand von Schlusskursen“ nennen. Das Einbeziehen von null verhindert positive „Verluste“.

8. **Wichtig — Unterschiedliche Fenster dürfen unterschiedliche Ergebnisse haben; die Risikoprämien-Erklärung ist unbelegt.**

   **Beleg:** [Plan:69](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-30_down_days_midterm_plan.md:69), [Plan:106](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-30_down_days_midterm_plan.md:106). Die neue Woche muss weder Richtung noch Größenordnung des bisherigen 20-Sitzungs-Vorlaufs teilen. Der bestehende Artikel grenzt Kausalität selbst ein ([Artikel:43](C:/dev/SeasonalEdge/blog/posts/2026-10-07_midterm-wahltag-boerse.md:43)). Ebenso weist der Plan nicht nach, welcher Anteil späterer Renditen eine Risikoprämie ist.

   **Planänderung:** „Darf nicht widersprechen“ durch „muss identische Größen reproduzieren und abweichende Fenster und Kohorten erklären“ ersetzen. Risikoprämie als mögliche Erklärung formulieren. Zulässig sind historische bedingte Renditebeschreibungen, keine nachgewiesene Wahlwirkung, Prognosefähigkeit oder Handelsrendite.

9. **Hinweis — Datenbasis und Wiederholbarkeit sind weitgehend plausibel, brauchen aber feste Prüfkriterien.**

   **Beleg:** Die SPY-Datei enthält **5.491** geordnete, eindeutige Zeilen ohne ungültige Zahlen. Gegen den Projektkalender fehlen keine erwarteten Sitzungen und existieren keine zusätzlichen; die **13 Nullrenditen seit 2006** sind reproduzierbar. Unter den **5.490 benachbarten Kurspaaren** beträgt die größte absolute Abweichung zwischen gespeichertem `log_return` und `log(close_t/close_{t−1})` rund **6,9·10⁻⁸**. Das bestätigt interne Konsistenz, nicht unabhängig die Dividendenbehandlung des Lieferanten.

   **Planänderung:** Dateihashes, Code-Commit, Datenprüfungen und Ausschlusslisten im Ergebnisartefakt festhalten. Adjustierte SPY-Renditen als Gesamtrendite-Näherung kennzeichnen; Studie B misst dagegen Index-Kursrenditen. Jahreshäufigkeiten zusätzlich durch beobachtete Sitzungen teilen, weil die Randjahre 2006 und 2026 unvollständig sind. Der Zahlenwächter muss Kennzahlen ihrem konkreten Fenster und ihrer Kohorte zuordnen; eine bloße Liste erlaubter Zahlen genügt dafür nicht.

Die fünf Fragen ausdrücklich beantwortet:

1. **Entzerrung:** Als vorab festgelegte beschreibende Auswahl vertretbar. Sie bevorzugt frühe zulässige Ereignisse und beseitigt Regimeabhängigkeit nicht. Letzte Häufungstage benötigen Zukunftswissen; zufällige Häufungstage sind keine grundsätzlich bessere Hauptstichprobe.

2. **Zufallsvergleich:** In der vorgeschlagenen Form nicht ausreichend. Ein Blockansatz kann zeitliche Abhängigkeit berücksichtigen, braucht aber ebenfalls eine definierte Nullhypothese und eine konsistente Behandlung von Ereignisauswahl und Folgerenditen. Für diese Artikel empfehle ich die beschreibende Variante ohne p-Werte.

3. **Adjustierte Kurse:** Die Kennzeichnung reicht für die beschreibende Studie, wenn Renditebasis und Lieferantenabhängigkeit klar bleiben. Sie reicht nicht für die Behauptung einer exakt nachgebildeten Anlegerrendite.

4. **Hauptzahl Studie B:** **`t−5→t0`**, wegen der konstanten fünf Sitzungsrenditen und Anschlussfähigkeit an den bisherigen Artikel. Als Ende gilt der Referenzschluss; „ohne Wahltag“ verlangt eine eigene kalenderbezogene Definition.

5. **Fehlendes und zu starke Aussagen:** Vor allem Testnullhypothese, unterstützte Intervallrechnung, Regeln für Robustheitskohorten, eindeutige Risikokennzahl und Ausführungsabgrenzung. Auf einen Vorzeichentest in B würde ich verzichten: Er könnte die Wahrscheinlichkeit einer positiven gepaarten Differenz prüfen, aber weder deren Mittelwert noch Kausalität; die bereits betrachtete Fensterfamilie würde durch einen nachträglich hinzugefügten Test nicht verschwinden.

**FREIGABE MIT AUFLAGEN**
