codex
Ich lese zuerst die drei neuesten Versionseinträge in `CLAUDE.md` und den Review-Prompt. Anschließend führe ich das Review nach dessen Vorgaben read-only durch.
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content CLAUDE.md -TotalCount 220; Get-Content docs/review_prompts/2026-10-17_williams_muster_code_r2.md' in C:\dev\SeasonalEdge
 exited -1 in 0ms:
Failed to create unified exec process: helper_unknown_error: setup refresh had errors
2026-10-17T13:42:30.987813Z ERROR codex_core::tools::router: error=exec_command failed: CreateProcess { message: "Rejected(\"Failed to create unified exec process: helper_unknown_error: setup refresh had errors\")" }
mcp: node_repl/js started
mcp: node_repl/js (completed)
mcp: node_repl/js started
mcp: node_repl/js (completed)
mcp: node_repl/js started
mcp: node_repl/js (completed)
mcp: node_repl/js started
mcp: node_repl/js (completed)
codex
Die Shell ist ausgefallen; ich lese die Dateien wie gewünscht über Node. Die Korrekturen sind im Code vorhanden. Ich prüfe jetzt die Holm-Schwellen der N-Familie, die kompakte Matrixrechnung und den verbleibenden Speicherbedarf mit gezielten Proben.
mcp: node_repl/js started
mcp: node_repl/js (failed)
mcp: node_repl/js started
mcp: node_repl/js (completed)
mcp: node_repl/js started
mcp: node_repl/js (completed)
mcp: node_repl/js started
mcp: node_repl/js (completed)
codex
Die unabhängige Nachrechnung bestätigt die kompakte Bootstrap-Matrix bis auf Rundungsfehler. Ein Befund bleibt bei der Feinziehung: Die Entscheidung verwendet die bereinigte N-Familie, die Prüfung auf 100.000 Replikate dagegen die unbereinigten p-Werte. Ein Gegenbeispiel lässt dadurch die vorgeschriebene Feinziehung aus. Die Laufzeitprobe benötigte lokal rund zwölf Sekunden für 500 Replikate bei voller Datums- und Tickergröße.
mcp: node_repl/js started
mcp: node_repl/js (completed)
codex
**Ein verbleibender Befund (Mittel): Die Feinziehung der N-Familie verwendet die falschen Holm-Schwellen.**

In [williams_muster.py:681](/C:/dev/SeasonalEdge/scripts/research/williams_muster.py:681) prüft `nahe_schwelle()` gegen `holm(nps)`. Die eigentliche Entscheidung verwendet dagegen `netto_familie()`, die Hypothesen ohne erfülltes (b) vor Holm sperrt. Dadurch kann die vorgeschriebene Feinziehung auf 100.000 Replikate ausbleiben.

Reproduziertes Beispiel:

- N2: p = 0,007, (b) erfüllt.
- N4: p = 0,00001, (b) nicht erfüllt.
- N6/N8: p = 0,3/0,4.

Die maßgebliche N2-Schwelle beträgt **0,0125**. Damit liegt p im Feinziehungsbereich **0,00625–0,025**. Die unbereinigte Familie verschiebt die Schwelle auf 0,01667 und löst keine Feinziehung aus. Eine Probe durch den echten `pruefzeitraum()`-Ablauf mit kontrollierten Statistik-Ergebnissen bestätigte: **nur ein Bootstrap-Aufruf mit 20.000 Replikaten**.

Die Feinziehungsprüfung muss dieselbe bereinigte N-Familie einschließlich ihrer Schwellen verwenden wie die Entscheidung. Dem Wächter fehlt hierfür ein Test des Phasenablaufs.

Die übrigen Prüffragen:

- **R1-Befunde:** Speicherstruktur, N-Entscheidung, Sitzungsachse, Phasentrennung, Quintil inklusive t, ergänzte Berichte und exklusives Einfrieren sind umgesetzt. Befund 4 bleibt wegen des obigen Falls teilweise offen.
- **Matrixrechnung:** korrekt. Eine unabhängige direkte Summierung mit ungleichen Datumsgewichten, dünnen Zellen und Lücken in der Zellnummerierung wich maximal um **8,33 × 10⁻¹⁷** ab.
- **Speicher:** deutlich verbessert. Für die genannte Größenordnung erscheint ein Bedarf von ungefähr **1,2–1,8 GiB** plausibel; 2 GB bleiben knapp. Das ist eine grobe Abschätzung, keine Messung des vollständigen Serverlaufs.
- **Laufzeit:** Die synthetische Probe mit 300 Tickern, 6.000 Tagen und zehn H- plus vier N-Hypothesen benötigte lokal **11,9 Sekunden für 500 Replikate**. Linear hochgerechnet etwa **8 Minuten für 20.000**, **40 Minuten für 100.000**. Vorlauf und Sensitivitätsläufe kommen hinzu. Für einen einmaligen Forschungslauf vertretbar; die Serverlaufzeit bleibt ungemessen.

Die schreibfreien Wächter-Teile bestanden unter Python 3.14. Den temporär schreibenden Block und die Mutationstests habe ich ausschließlich gelesen. Dateien und Datenbank blieben unverändert.

**KEINE FREIGABE**
