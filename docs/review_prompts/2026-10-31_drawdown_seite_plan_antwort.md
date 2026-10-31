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
session id: 01a1900b-3f6c-7881-b531-1287011949fd
--------
user
Du bist Reviewer. Lies docs/review_prompts/2026-10-31_drawdown_seite_plan.md und prüfe den Bauplan am Code des Repos: landing/js/spot-vol-compute.js, landing/pages/spot-vol-beta.html, scripts/verify_spot_vol_beta.py, landing/js/kurse.js, landing/js/boersenkalender.js (Fassade SA.holidays/SA.boersenkalender), landing/build_en.py, landing/js/i18n.js, shared/seo_basis.py, deploy/nginx.conf, landing/components/nav.html und die Startseite landing/index.html, sowie scripts/research/drawdown_analyse.py und docs/review_prompts/2026-10-31_drawdown_analyse_plan_antwort.md. Keine Dateien ändern. Antwort auf Deutsch: nummerierte Befunde (blockierend/wichtig/Hinweis) mit Beleg (Datei:Zeile) und konkreter Planänderung; beantworte die fünf Fragen; Schluss FREIGABE, FREIGABE MIT AUFLAGEN oder NICHT TRAGFÄHIG.
codex
Ich lese zuerst die drei neuesten Versionseinträge in `CLAUDE.md` und den Review-Prompt. Danach prüfe ich den Bauplan gegen die genannten Codepfade. Alle Dateien bleiben unverändert.
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content CLAUDE.md -TotalCount 230; Get-Content docs/review_prompts/2026-10-31_drawdown_seite_plan.md; Get-Content docs/REVIEW_MIT_CODEX.md' in C:\dev\SeasonalEdge
 exited -1 in 0ms:
Failed to create unified exec process: helper_unknown_error: setup refresh had errors
2026-10-31T03:40:26.193688Z ERROR codex_core::tools::router: error=exec_command failed: CreateProcess { message: "Rejected(\"Failed to create unified exec process: helper_unknown_error: setup refresh had errors\")" }
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
Die Spot-Vol-Vorlage behandelt den Sitzungsschluss ausdrücklich nur für US-Titel. Für Drawdown über alle Ticker braucht der Plan daher einen eigenen Schlusszeitvertrag. Außerdem ist die Behandlung von Lücken noch entscheidend: Ein Neustart nach der letzten Lücke würde ein neues Hoch setzen und könnte dadurch eine scheinbar vollständige Drawdown-Historie erzeugen.
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
mcp: node_repl/js started
mcp: node_repl/js (completed)
codex
Die Kalenderdaten unterscheiden nach Börse und Jahr zwischen „belegt“, „Annahme“, „ungeprüft“ und „Konvention“. Der Plan muss diese Einschränkungen sichtbar machen. In der Studienreferenz habe ich zudem zwei Punkte gefunden, die beim Herausziehen nach `shared/` korrigiert werden müssen: Sie erkennt fehlende Sitzungszeilen nicht, und ihr Tempovergleich verwendet das aktuelle Episodenalter statt der Zeit bis zum ersten Schwellenübertritt.
mcp: node_repl/js started
mcp: node_repl/js (completed)
codex
Der Bauplan ist als deskriptive Drawdown-Seite tragfähig, aber noch nicht unverändert umsetzungsreif. Kritisch sind der marktübergreifende Sitzungsschluss und die Fortsetzung nach Datenlücken. Die Studienreferenz enthält außerdem einen reproduzierbaren Tempofehler.

Geprüft wurden die genannten Codepfade, ergänzt durch gezielte Ausführung des echten JS-Kerns und der Python-Studienfunktionen. Keine Dateien geändert; kein vollständiger Gate-Lauf.

1. **Blockierend – Die US-Schlusszeitregel darf nicht für alle Ticker übernommen werden.**

   **Beleg:** [spot-vol-compute.js:41](C:/dev/SeasonalEdge/landing/js/spot-vol-compute.js:41) verwendet regulär **16:00 New York plus 30 Minuten**, unabhängig vom übergebenen Börsenparameter. Das ist für die angebotenen Spot-Vol-Paare ausdrücklich beabsichtigt. Der Kalender liefert zwar Börsendatum und Sitzungsinformationen, aber keine vollständige marktübergreifende Schlusszeitregel: [boersenkalender.js:394](C:/dev/SeasonalEdge/landing/js/boersenkalender.js:394).

   Gegenprobe am 30.10.2026 um 18:00 UTC: Die Vorlage liefert auch für XETRA noch den 29.10. Eine Übernahme für Krypto könnte umgekehrt den laufenden UTC-Tagesbalken vor Tagesende zulassen.

   **Planänderung:** E ausdrücklich je Markt definieren: Börsenzeitzone, regulärer Schluss, belegte Halbtagsschlüsse, Datenverfügbarkeitspuffer; für Krypto abgeschlossene UTC-Tagesbalken, für Forex eine dokumentierte Tagesbalkenkonvention. Fehlende Schlusszeitkenntnis braucht eine konservative Rückfallregel und Kennzeichnung.

2. **Blockierend – Ein Neustart nach der letzten Lücke stellt die globale Drawdown-Historie nicht wieder her.**

   **Beleg:** Der Plan lässt die Entscheidung offen: [Bauplan:29](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-31_drawdown_seite_plan.md:29). Die Studienreferenz prüft nur vorhandene Zeilen, deren Reihenfolge und Renditen: [drawdown_analyse.py:42](C:/dev/SeasonalEdge/scripts/research/drawdown_analyse.py:42). Zwei Zeilen vom 26. und 28.10. mit endlicher Folgerendite werden tatsächlich verbunden; die fehlende Sitzung wird nicht erkannt.

   Nach einer unbekannten Rendite fehlen außerdem die Verbindung zum früheren Hoch und möglicherweise ein zwischenzeitlicher Peak oder eine Recovery. Das betrifft auch spätere Episoden. Anders als beim Rolling-Beta heilt das nicht nach einer festen Anzahl Sitzungen.

   **Planänderung:** Vollständig bestimmbare, abgeschlossene Episoden vor der Lücke erhalten. Betroffene und nachfolgende globale Episodenkennzahlen sperren, solange keine belegte Rekonstruktion möglich ist. Nachfolgende Segmente allenfalls als ausdrücklich lokale Auswertung mit unbekannter Vorgeschichte zeigen. Einen Segmentanfang niemals still als neues historisches Hoch behandeln. Dasselbe gilt für fehlende oder nicht endliche `log_return`, nicht nur fehlende Zeilen.

3. **Wichtig – Kalenderzuordnung und belegte Kalenderabdeckung sind verschiedene Dinge.**

   **Beleg:** [boersenkalender.js:499](C:/dev/SeasonalEdge/landing/js/boersenkalender.js:499) unterscheidet `belegt`, `annahme`, `ungeprueft` und `konvention`. Die eingebetteten Daten in [boersenkalender.js:21](C:/dev/SeasonalEdge/landing/js/boersenkalender.js:21) liefern beispielsweise:

   - XETRA 1999: ungeprüft; 2026: belegt.
   - HKEX 1999: ungeprüft; 2026: belegt.
   - KRX 2026: Annahme.
   - Krypto und Forex: Konvention.

   Halbtagabdeckung ist separat: [boersenkalender.js:485](C:/dev/SeasonalEdge/landing/js/boersenkalender.js:485). Zudem delegiert `SA.holidays` nur unter `kalender_v1` an den neuen Kern: [holidays.js:337](C:/dev/SeasonalEdge/landing/js/holidays.js:337). Die Spot-Vol-Seite läuft ausdrücklich unter `alt`, verwendet für ihre Rechnung aber direkt `SA.boersenkalender`: [spot-vol-beta.html:283](C:/dev/SeasonalEdge/landing/pages/spot-vol-beta.html:283).

   **Planänderung:** Den direkten Kalenderaufruf verbindlich festlegen. Kalenderstatus über die gesamte zur Hochberechnung benötigte Historie ausweisen. Bei ungeprüften Zeiträumen dürfen entfernte Zeilen nicht vorbehaltlos als erwiesene Phantomzeilen gelten; Ergebnisse entsprechend einschränken oder kennzeichnen.

4. **Wichtig – Die Python-Referenz hat einen Tempofehler außerhalb des aktuellen QQQ-Sonderfalls.**

   **Beleg:** Historische Zeiten bis zum ersten Erreichen der aktuellen Tiefe werden korrekt berechnet. Der Vergleich erfolgt jedoch gegen `seit_hoch`, also das gesamte aktuelle Episodenalter: [drawdown_analyse.py:158](C:/dev/SeasonalEdge/scripts/research/drawdown_analyse.py:158).

   Reproduzierbarer Fall: Historische Episode erreicht die Schwelle nach **2 Sitzungen**, aktuelle nach **1 Sitzung**, aktuelles Alter **3 Sitzungen**. Der Code meldet **0 von 1** historischen Episoden langsamer; korrekt sind **1 von 1**.

   **Planänderung:** Tempo ausdrücklich als `erster_Schwellenübertritt − Peak` definieren, für historische und laufende Episode identisch. Vergleich gegen `laufend.bis_schwelle`. Einen Fall mit zwischenzeitlicher Erholung und erneutem Erreichen der heutigen Tiefe aufnehmen. „0 Abweichungen“ zwischen Zwillingen schützt vor diesem gemeinsamen Fehler nicht.

5. **Wichtig – Die frühere Auflage zur Interpretation muss in die sichtbaren Texte übernommen werden.**

   **Beleg:** Der Bauplan nennt weiterhin „TTR ab aktuellem DD“: [Bauplan:42](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-31_drawdown_seite_plan.md:42). Die frühere Reviewantwort verlangt ausdrücklich „Historische Dauer ab erstmaligem Erreichen der heutigen Verlustschwelle“ und trennt dies von einer Restdauerprognose: [Analyse-Reviewantwort:1150](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-31_drawdown_analyse_plan_antwort.md:1150).

   **Planänderung:** Diese vollständige Bedeutung in Charttitel, Kurzantwort und Tooltip festlegen. Die Dauer-Kurve beschreibt ausschließlich abgeschlossene, rückblickend nach Tiefe ausgewählte Episoden. Fallzahlen gehören an Ränge, Quartile und Kurven; keine Aussage über die verbleibende Dauer der laufenden Episode. Zwei Jahre Historie ersetzen keine Mindestfallzahl: `n=0` braucht „nicht bestimmbar“, kleine Gruppen sichtbare Einzelwerte.

6. **Wichtig – „Adjustiert ⇒ Total Return“ ist für das gesamte Tickerangebot kein ausreichender Vertrag.**

   **Beleg:** [Bauplan:33](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-31_drawdown_seite_plan.md:33) übernimmt diese Aussage pauschal. Bereits die frühere Reviewauflage fordert einen Nachweis der Adjustierungsbasis: [Analyse-Reviewantwort:1178](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-31_drawdown_analyse_plan_antwort.md:1178). Der Kurslader prüft Feldvorhandensein und Datumsfolge, aber keine wirtschaftliche Renditebasis: [kurse.js:207](C:/dev/SeasonalEdge/landing/js/kurse.js:207).

   **Planänderung:** Instrumentabhängigen Basistext vorsehen. Eine gespeicherte Index-, Volatilitäts-, Rendite- oder Futures-Reihe darf nicht automatisch als Dividenden-Gesamtrendite dargestellt werden. Bei ungeklärter Herkunft neutral „aus gespeicherten logarithmischen Renditen“ schreiben und die Einschränkung nennen. Numerische Gültigkeit muss der Rechenkern selbst prüfen.

7. **Wichtig – Der Wächter braucht eine dritte Referenz und einen verbindlichen Integrationsvertrag.**

   **Beleg:** [Bauplan:54](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-31_drawdown_seite_plan.md:54) plant überwiegend JS/Python-Gleichheit. Der Tempofehler zeigt deren Grenze. Der bestehende Spot-Vol-Wächter enthält zusätzlich unabhängige Rechnungen und Frischegrenzen: [verify_spot_vol_beta.py:335](C:/dev/SeasonalEdge/scripts/verify_spot_vol_beta.py:335). Seine Seitenprobe prüft echte Kursanfragen: [verify_spot_vol_beta.py:491](C:/dev/SeasonalEdge/scripts/verify_spot_vol_beta.py:491).

   **Planänderung:** Ergänzen:

   - Unabhängige Sollwerte für Episodenzuordnung, Fenstergrenzen, Ränge, Quantile, Zeitanteil und sämtliche Kurvenstützpunkte.
   - Grenzfälle: `n=0/1`, fehlende Endsession, ungültige Rendite, aufeinanderfolgende Lücken, mehrere Phantomzeilen, Schalttag, Gleichstände und exakte Filterschwellen.
   - Produktionsanfrage mit voller Historie (`ab:null`); den Spot-Vol-Start 1990 nicht übernehmen.
   - Echte DE- und erzeugte EN-Seite, schnelle Tickerwechsel mit vertauschter Antwortreihenfolge, Fehler nach zuvor erfolgreicher Darstellung und Chartdaten samt Lücken.
   - Invarianten: Fensterwechsel verändert keine Peaks; Filterwechsel verändert keine aktuelle Episode; Skalierung des Index verändert keine Drawdowns.
   - Gate-Aufruf ohne Sonderflag aktiviert alle Pflichtprüfungen. Mutationen benötigen eindeutigen Anker, erfolgreiche Kontrolle und die erwartete fachliche Fehlprüfung; Ausnahme oder Prozessabsturz zählen nicht als Fang.

8. **Hinweis – Adresse und Platzierung passen; die behauptete SEO-Seitenliste existiert so nicht.**

   **Beleg:** `shared/seo_basis.py` liest die EN-Seiten aus `_EN_PAGE_META`: [seo_basis.py:198](C:/dev/SeasonalEdge/shared/seo_basis.py:198). Die Sitemap entdeckt Feature-Seiten automatisch: [programmatic_seo_builder.py:234](C:/dev/SeasonalEdge/seo/programmatic_seo_builder.py:234). `/en/drawdown` wird bereits vom allgemeinen EN-Routing abgedeckt: [nginx.conf:134](C:/dev/SeasonalEdge/deploy/nginx.conf:134).

   **Planänderung:** „SEO-Seitenliste in shared/seo_basis ändern“ streichen. Stattdessen `_EN_PAGE_META`, vollständigen DE-Head, gebackenen EN-Head, reziproke Sprachverweise und tatsächliche Sitemap-Einträge prüfen. DE-Route mit HTML-Neuvalidierung analog [nginx.conf:483](C:/dev/SeasonalEdge/deploy/nginx.conf:483). Die beiden Nav-Stellen sind korrekt erkannt: [nav.html:27](C:/dev/SeasonalEdge/landing/components/nav.html:27), [index.html:320](C:/dev/SeasonalEdge/landing/index.html:320).

Die fünf Fragen:

1. **Lückenbehandlung:** Episodenabhängig sperren und bekannte frühere Ergebnisse erhalten. Nach der letzten Lücke keine globale Historie durch bloßes Neubasieren vortäuschen; siehe Befund 2.
2. **Kalender für alle Ticker:** Als Zuordnungs- und Rechen-API nutzbar, aber nicht für jede Börse und jedes historische Jahr gleichermaßen belegt. Status- und Schlusszeitbehandlung sind Pflicht.
3. **Python in `shared/`:** Ja. Als importierbarer, nebenwirkungsfreier Fachkern sinnvoll. Das Forschungsskript sollte ihn anschließend verwenden; die unabhängige Testreferenz muss davon getrennt bleiben.
4. **Fehlendes am Wächter:** Dritte Referenz, Invarianten, marktübergreifende Frische, unbekannte Pfade, kleine/leere Gruppen sowie echte DE/EN-Integration und Ladewechsel; siehe Befund 7.
5. **Adresse und Navigation:** Keine grundsätzlichen Einwände gegen `/drawdown` und `/en/drawdown` oder „Mehr“ nach der Stress-Ampel. Die SEO-Integration muss dem tatsächlichen automatischen Inventar folgen.

**FREIGABE MIT AUFLAGEN** — Befunde 1–7 verbindlich in den Bauplan übernehmen; Integrationsbeschreibung gemäß Befund 8 berichtigen.
tokens used
114.045
Der Bauplan ist als deskriptive Drawdown-Seite tragfähig, aber noch nicht unverändert umsetzungsreif. Kritisch sind der marktübergreifende Sitzungsschluss und die Fortsetzung nach Datenlücken. Die Studienreferenz enthält außerdem einen reproduzierbaren Tempofehler.

Geprüft wurden die genannten Codepfade, ergänzt durch gezielte Ausführung des echten JS-Kerns und der Python-Studienfunktionen. Keine Dateien geändert; kein vollständiger Gate-Lauf.

1. **Blockierend – Die US-Schlusszeitregel darf nicht für alle Ticker übernommen werden.**

   **Beleg:** [spot-vol-compute.js:41](C:/dev/SeasonalEdge/landing/js/spot-vol-compute.js:41) verwendet regulär **16:00 New York plus 30 Minuten**, unabhängig vom übergebenen Börsenparameter. Das ist für die angebotenen Spot-Vol-Paare ausdrücklich beabsichtigt. Der Kalender liefert zwar Börsendatum und Sitzungsinformationen, aber keine vollständige marktübergreifende Schlusszeitregel: [boersenkalender.js:394](C:/dev/SeasonalEdge/landing/js/boersenkalender.js:394).

   Gegenprobe am 30.10.2026 um 18:00 UTC: Die Vorlage liefert auch für XETRA noch den 29.10. Eine Übernahme für Krypto könnte umgekehrt den laufenden UTC-Tagesbalken vor Tagesende zulassen.

   **Planänderung:** E ausdrücklich je Markt definieren: Börsenzeitzone, regulärer Schluss, belegte Halbtagsschlüsse, Datenverfügbarkeitspuffer; für Krypto abgeschlossene UTC-Tagesbalken, für Forex eine dokumentierte Tagesbalkenkonvention. Fehlende Schlusszeitkenntnis braucht eine konservative Rückfallregel und Kennzeichnung.

2. **Blockierend – Ein Neustart nach der letzten Lücke stellt die globale Drawdown-Historie nicht wieder her.**

   **Beleg:** Der Plan lässt die Entscheidung offen: [Bauplan:29](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-31_drawdown_seite_plan.md:29). Die Studienreferenz prüft nur vorhandene Zeilen, deren Reihenfolge und Renditen: [drawdown_analyse.py:42](C:/dev/SeasonalEdge/scripts/research/drawdown_analyse.py:42). Zwei Zeilen vom 26. und 28.10. mit endlicher Folgerendite werden tatsächlich verbunden; die fehlende Sitzung wird nicht erkannt.

   Nach einer unbekannten Rendite fehlen außerdem die Verbindung zum früheren Hoch und möglicherweise ein zwischenzeitlicher Peak oder eine Recovery. Das betrifft auch spätere Episoden. Anders als beim Rolling-Beta heilt das nicht nach einer festen Anzahl Sitzungen.

   **Planänderung:** Vollständig bestimmbare, abgeschlossene Episoden vor der Lücke erhalten. Betroffene und nachfolgende globale Episodenkennzahlen sperren, solange keine belegte Rekonstruktion möglich ist. Nachfolgende Segmente allenfalls als ausdrücklich lokale Auswertung mit unbekannter Vorgeschichte zeigen. Einen Segmentanfang niemals still als neues historisches Hoch behandeln. Dasselbe gilt für fehlende oder nicht endliche `log_return`, nicht nur fehlende Zeilen.

3. **Wichtig – Kalenderzuordnung und belegte Kalenderabdeckung sind verschiedene Dinge.**

   **Beleg:** [boersenkalender.js:499](C:/dev/SeasonalEdge/landing/js/boersenkalender.js:499) unterscheidet `belegt`, `annahme`, `ungeprueft` und `konvention`. Die eingebetteten Daten in [boersenkalender.js:21](C:/dev/SeasonalEdge/landing/js/boersenkalender.js:21) liefern beispielsweise:

   - XETRA 1999: ungeprüft; 2026: belegt.
   - HKEX 1999: ungeprüft; 2026: belegt.
   - KRX 2026: Annahme.
   - Krypto und Forex: Konvention.

   Halbtagabdeckung ist separat: [boersenkalender.js:485](C:/dev/SeasonalEdge/landing/js/boersenkalender.js:485). Zudem delegiert `SA.holidays` nur unter `kalender_v1` an den neuen Kern: [holidays.js:337](C:/dev/SeasonalEdge/landing/js/holidays.js:337). Die Spot-Vol-Seite läuft ausdrücklich unter `alt`, verwendet für ihre Rechnung aber direkt `SA.boersenkalender`: [spot-vol-beta.html:283](C:/dev/SeasonalEdge/landing/pages/spot-vol-beta.html:283).

   **Planänderung:** Den direkten Kalenderaufruf verbindlich festlegen. Kalenderstatus über die gesamte zur Hochberechnung benötigte Historie ausweisen. Bei ungeprüften Zeiträumen dürfen entfernte Zeilen nicht vorbehaltlos als erwiesene Phantomzeilen gelten; Ergebnisse entsprechend einschränken oder kennzeichnen.

4. **Wichtig – Die Python-Referenz hat einen Tempofehler außerhalb des aktuellen QQQ-Sonderfalls.**

   **Beleg:** Historische Zeiten bis zum ersten Erreichen der aktuellen Tiefe werden korrekt berechnet. Der Vergleich erfolgt jedoch gegen `seit_hoch`, also das gesamte aktuelle Episodenalter: [drawdown_analyse.py:158](C:/dev/SeasonalEdge/scripts/research/drawdown_analyse.py:158).

   Reproduzierbarer Fall: Historische Episode erreicht die Schwelle nach **2 Sitzungen**, aktuelle nach **1 Sitzung**, aktuelles Alter **3 Sitzungen**. Der Code meldet **0 von 1** historischen Episoden langsamer; korrekt sind **1 von 1**.

   **Planänderung:** Tempo ausdrücklich als `erster_Schwellenübertritt − Peak` definieren, für historische und laufende Episode identisch. Vergleich gegen `laufend.bis_schwelle`. Einen Fall mit zwischenzeitlicher Erholung und erneutem Erreichen der heutigen Tiefe aufnehmen. „0 Abweichungen“ zwischen Zwillingen schützt vor diesem gemeinsamen Fehler nicht.

5. **Wichtig – Die frühere Auflage zur Interpretation muss in die sichtbaren Texte übernommen werden.**

   **Beleg:** Der Bauplan nennt weiterhin „TTR ab aktuellem DD“: [Bauplan:42](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-31_drawdown_seite_plan.md:42). Die frühere Reviewantwort verlangt ausdrücklich „Historische Dauer ab erstmaligem Erreichen der heutigen Verlustschwelle“ und trennt dies von einer Restdauerprognose: [Analyse-Reviewantwort:1150](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-31_drawdown_analyse_plan_antwort.md:1150).

   **Planänderung:** Diese vollständige Bedeutung in Charttitel, Kurzantwort und Tooltip festlegen. Die Dauer-Kurve beschreibt ausschließlich abgeschlossene, rückblickend nach Tiefe ausgewählte Episoden. Fallzahlen gehören an Ränge, Quartile und Kurven; keine Aussage über die verbleibende Dauer der laufenden Episode. Zwei Jahre Historie ersetzen keine Mindestfallzahl: `n=0` braucht „nicht bestimmbar“, kleine Gruppen sichtbare Einzelwerte.

6. **Wichtig – „Adjustiert ⇒ Total Return“ ist für das gesamte Tickerangebot kein ausreichender Vertrag.**

   **Beleg:** [Bauplan:33](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-31_drawdown_seite_plan.md:33) übernimmt diese Aussage pauschal. Bereits die frühere Reviewauflage fordert einen Nachweis der Adjustierungsbasis: [Analyse-Reviewantwort:1178](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-31_drawdown_analyse_plan_antwort.md:1178). Der Kurslader prüft Feldvorhandensein und Datumsfolge, aber keine wirtschaftliche Renditebasis: [kurse.js:207](C:/dev/SeasonalEdge/landing/js/kurse.js:207).

   **Planänderung:** Instrumentabhängigen Basistext vorsehen. Eine gespeicherte Index-, Volatilitäts-, Rendite- oder Futures-Reihe darf nicht automatisch als Dividenden-Gesamtrendite dargestellt werden. Bei ungeklärter Herkunft neutral „aus gespeicherten logarithmischen Renditen“ schreiben und die Einschränkung nennen. Numerische Gültigkeit muss der Rechenkern selbst prüfen.

7. **Wichtig – Der Wächter braucht eine dritte Referenz und einen verbindlichen Integrationsvertrag.**

   **Beleg:** [Bauplan:54](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-31_drawdown_seite_plan.md:54) plant überwiegend JS/Python-Gleichheit. Der Tempofehler zeigt deren Grenze. Der bestehende Spot-Vol-Wächter enthält zusätzlich unabhängige Rechnungen und Frischegrenzen: [verify_spot_vol_beta.py:335](C:/dev/SeasonalEdge/scripts/verify_spot_vol_beta.py:335). Seine Seitenprobe prüft echte Kursanfragen: [verify_spot_vol_beta.py:491](C:/dev/SeasonalEdge/scripts/verify_spot_vol_beta.py:491).

   **Planänderung:** Ergänzen:

   - Unabhängige Sollwerte für Episodenzuordnung, Fenstergrenzen, Ränge, Quantile, Zeitanteil und sämtliche Kurvenstützpunkte.
   - Grenzfälle: `n=0/1`, fehlende Endsession, ungültige Rendite, aufeinanderfolgende Lücken, mehrere Phantomzeilen, Schalttag, Gleichstände und exakte Filterschwellen.
   - Produktionsanfrage mit voller Historie (`ab:null`); den Spot-Vol-Start 1990 nicht übernehmen.
   - Echte DE- und erzeugte EN-Seite, schnelle Tickerwechsel mit vertauschter Antwortreihenfolge, Fehler nach zuvor erfolgreicher Darstellung und Chartdaten samt Lücken.
   - Invarianten: Fensterwechsel verändert keine Peaks; Filterwechsel verändert keine aktuelle Episode; Skalierung des Index verändert keine Drawdowns.
   - Gate-Aufruf ohne Sonderflag aktiviert alle Pflichtprüfungen. Mutationen benötigen eindeutigen Anker, erfolgreiche Kontrolle und die erwartete fachliche Fehlprüfung; Ausnahme oder Prozessabsturz zählen nicht als Fang.

8. **Hinweis – Adresse und Platzierung passen; die behauptete SEO-Seitenliste existiert so nicht.**

   **Beleg:** `shared/seo_basis.py` liest die EN-Seiten aus `_EN_PAGE_META`: [seo_basis.py:198](C:/dev/SeasonalEdge/shared/seo_basis.py:198). Die Sitemap entdeckt Feature-Seiten automatisch: [programmatic_seo_builder.py:234](C:/dev/SeasonalEdge/seo/programmatic_seo_builder.py:234). `/en/drawdown` wird bereits vom allgemeinen EN-Routing abgedeckt: [nginx.conf:134](C:/dev/SeasonalEdge/deploy/nginx.conf:134).

   **Planänderung:** „SEO-Seitenliste in shared/seo_basis ändern“ streichen. Stattdessen `_EN_PAGE_META`, vollständigen DE-Head, gebackenen EN-Head, reziproke Sprachverweise und tatsächliche Sitemap-Einträge prüfen. DE-Route mit HTML-Neuvalidierung analog [nginx.conf:483](C:/dev/SeasonalEdge/deploy/nginx.conf:483). Die beiden Nav-Stellen sind korrekt erkannt: [nav.html:27](C:/dev/SeasonalEdge/landing/components/nav.html:27), [index.html:320](C:/dev/SeasonalEdge/landing/index.html:320).

Die fünf Fragen:

1. **Lückenbehandlung:** Episodenabhängig sperren und bekannte frühere Ergebnisse erhalten. Nach der letzten Lücke keine globale Historie durch bloßes Neubasieren vortäuschen; siehe Befund 2.
2. **Kalender für alle Ticker:** Als Zuordnungs- und Rechen-API nutzbar, aber nicht für jede Börse und jedes historische Jahr gleichermaßen belegt. Status- und Schlusszeitbehandlung sind Pflicht.
3. **Python in `shared/`:** Ja. Als importierbarer, nebenwirkungsfreier Fachkern sinnvoll. Das Forschungsskript sollte ihn anschließend verwenden; die unabhängige Testreferenz muss davon getrennt bleiben.
4. **Fehlendes am Wächter:** Dritte Referenz, Invarianten, marktübergreifende Frische, unbekannte Pfade, kleine/leere Gruppen sowie echte DE/EN-Integration und Ladewechsel; siehe Befund 7.
5. **Adresse und Navigation:** Keine grundsätzlichen Einwände gegen `/drawdown` und `/en/drawdown` oder „Mehr“ nach der Stress-Ampel. Die SEO-Integration muss dem tatsächlichen automatischen Inventar folgen.

**FREIGABE MIT AUFLAGEN** — Befunde 1–7 verbindlich in den Bauplan übernehmen; Integrationsbeschreibung gemäß Befund 8 berichtigen.
