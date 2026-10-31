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
session id: 01a1900e-6c2a-7050-a666-6e96f82d24ff
--------
user
Du bist Reviewer. Lies docs/review_prompts/2026-10-31_drawdown_seite_plan_v2.md und die Vorgängerantwort docs/review_prompts/2026-10-31_drawdown_seite_plan_antwort.md. Prüfe, ob die Auflagen aus v1 vollständig übernommen sind, und prüfe die neuen Teile (Kaplan-Meier, Forward Returns, Drawdown-Kalender/Ulcer Index, Phase 2 Nightly/Mail, Phase 3 Price vs Total Return) methodisch und am Code (u. a. landing/js/boersenkalender.js, shared/daily_report.py, scripts/nightly_refresh.py, shared/atomic_json.py, Tabelle dividend_events-Nutzung im Repo). Keine Dateien ändern. Antwort auf Deutsch: nummerierte Befunde (blockierend/wichtig/Hinweis) mit Beleg und Planänderung; beantworte die fünf Fragen; Schluss FREIGABE, FREIGABE MIT AUFLAGEN oder NICHT TRAGFÄHIG.
codex
Ich lese zuerst die drei neuesten Versionseinträge in `CLAUDE.md`, dann den Plan, die Vorgängerantwort und die betroffenen Codepfade. Ich prüfe die Auflagen aus v1 und die neuen Methodenteile read-only.
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content CLAUDE.md -TotalCount 240' in C:\dev\SeasonalEdge
 exited -1 in 0ms:
Failed to create unified exec process: helper_unknown_error: setup refresh had errors
2026-10-31T03:43:52.923611Z ERROR codex_core::tools::router: error=exec_command failed: CreateProcess { message: "Rejected(\"Failed to create unified exec process: helper_unknown_error: setup refresh had errors\")" }
mcp: node_repl/js started
mcp: node_repl/js (completed)
mcp: node_repl/js started
mcp: node_repl/js (completed)
mcp: node_repl/js started
mcp: node_repl/js (completed)
mcp: node_repl/js started
mcp: node_repl/js (failed)
codex
Die v1-Auflagen sind weitgehend übernommen. Zwei neue Risiken zeichnen sich ab: Die Price-Return-Formel braucht eine Korrektur, und Phase 2 muss Frische und Wiederholungsversand verbindlich regeln. Ich prüfe dazu die vorhandenen Daten- und Mailpfade.
mcp: node_repl/js started
mcp: node_repl/js (completed)
mcp: node_repl/js started
mcp: node_repl/js (completed)
mcp: node_repl/js started
mcp: node_repl/js (completed)
web search: 
web search: site.statsmodels.org SurvfuncRight simultaneous censoring event confidence interval log log ...
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
Der Kalenderkern liefert auf normalen Handelstagen keine reguläre Schlusszeit. Der Plan braucht deshalb eine Ergänzung der gemeinsamen Kalenderdaten; ein bloßer API-Aufruf reicht nicht. Bei `dividend_events` kommt hinzu: Der Schreiber lädt bereits von Yahoo und setzt keine Währung. Ein erneuter Yahoo-Abruf wäre daher kein unabhängiger Nachweis.
mcp: node_repl/js started
mcp: node_repl/js (completed)
mcp: node_repl/js started
mcp: node_repl/js (completed)
codex
Die v1-Auflagen sind **weitgehend, aber noch nicht vollständig operationalisiert**. A2–A5, A7 und A8 sind im Plan übernommen; die Tempokorrektur A4 steht tatsächlich im Code. Bei A1 fehlen die benötigten regulären Schlusszeiten in der Browser-API, bei A6 die belastbare Zuordnung der Renditebasis. Die Erweiterungen sind grundsätzlich tragfähig, brauchen aber die folgenden Präzisierungen.

Read-only geprüft; keine Dateien geändert. Den echten Kalenderkern und eine Gegenrechnung zur Dividendenformel habe ich ausgeführt. Kein vollständiger Gate-Lauf, keine Live-Datenbankprüfung.

1. **Blockierend für Phase 1/2 – Der Schlusszeitvertrag lässt sich mit der genannten API noch nicht umsetzen.**

   **Beleg:** [Plan:25](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-31_drawdown_seite_plan_v2.md:25) erwartet reguläre Schlusszeiten aus dem Kalender. [boersenkalender.js:405](C:/dev/SeasonalEdge/landing/js/boersenkalender.js:405) liefert Schlusszeit und Zone jedoch nur für eingetragene Halbtage. Ausgeführt für den 30.10.2026: NYSE und XETRA liefern jeweils `schlusszeit:null`; der NYSE-Halbtag 27.11. liefert korrekt `13:00`.

   Auch Python-`letzte_session` ist kein gleichwertiger Ersatz: [exchange_holidays.py:358](C:/dev/SeasonalEdge/shared/exchange_holidays.py:358) verwendet standardmäßig 15 Minuten Puffer, berücksichtigt hier keine Halbtagsschlüsse, liefert für Krypto den laufenden Tag und unterstützt Forex nicht.

   **Planänderung:** Reguläre Schlusszeiten als gemeinsamen, belegten Kalendervertrag ergänzen und JS/Python daraus speisen; Generator und Quelldaten ändern, nicht die erzeugte JS-Datei. E an einem eingefrorenen Zeitpunkt mit 30 Minuten Puffer berechnen. Rückfallregel präzisieren: vorherige **offene Sitzung**, auch an Wochenenden und Feiertagen. Tests für regulären Schluss, Halbtag, Sommerzeitwechsel, Forex und Krypto in beiden Produktionspfaden.

2. **Blockierend für die beschriebene Phase 3 – Die Rückrechnungsformel ist falsch.**

   **Beleg:** [Plan:103](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-31_drawdown_seite_plan_v2.md:103) setzt
   `r_price = r_total − ln(1 + D/C_prev)`.

   Gegenbeispiel für eine echte Gesamtrendite: Vortagsschluss 100, Ex-Schluss 90, Dividende 10. Gesamtrendite = 0; die Planformel liefert eine Preisrendite von **−9,09 %**, tatsächlich sind es **−10 %**.

   Bei `exp(r_total) = (C_t + D)/C_prev` lautet die Umkehrung:
   `r_price = ln(exp(r_total) − D/C_prev)`.
   Ein rückwärts adjustierter Lieferantenkurs muss allerdings nicht genau dieser Gesamtrenditedefinition entsprechen. Dividendenbereinigung kann stattdessen über einen Abschlagsfaktor erfolgen; siehe die dokumentierte [Berechnung von MathWorks](https://www.mathworks.com/help/finance/adjustedclosingprices.html).

   **Planänderung:** Die Formel jetzt streichen. Phase 3 muss zuerst die tatsächliche Adjustierungsregel nachweisen und darauf die Umkehrung aufbauen. Bevorzugt konsistente, splitbereinigte Preis- und Dividendenreihen verwenden. Handfälle für Dividende, Split, Sonderausschüttung und deren Kombination verpflichtend machen.

3. **Wichtig – Der geplante unabhängige Dividendennachweis ist nicht unabhängig; die Basiszuordnung bleibt unvollständig.**

   **Beleg:** [fetch_event_data.py:25](C:/dev/SeasonalEdge/scripts/fetch_event_data.py:25) lädt die Dividendendaten bereits von Yahoo, begrenzt auf 25 Jahre. Ein Vergleich mit Yahoo prüft somit Importvollständigkeit gegenüber derselben Quelle. Der Schreiber speichert außerdem nur Ticker, Ex-Datum und Betrag ([Zeile 139](C:/dev/SeasonalEdge/scripts/fetch_event_data.py:139)); die Tabelle ergänzt standardmäßig `USD` ([create_event_tables.sql:8](C:/dev/SeasonalEdge/scripts/create_event_tables.sql:8)).

   Für A6 reichen die Kategorien ebenfalls nicht: DAX und Euro Stoxx 50 stehen beide als `EU-Index`, ohne Preis-/Performancekennzeichen ([symbols.py:569](C:/dev/SeasonalEdge/shared/symbols.py:569)). Der Kursparser kann bei fehlendem `adjclose` auf Rohschlüsse zurückfallen ([yahoo_downloader.py:111](C:/dev/SeasonalEdge/shared/yahoo_downloader.py:111)).

   **Planänderung:** Yahoo als Abgleich derselben Quelle bezeichnen; für einen unabhängigen Nachweis Emittenten-/Börsendaten hinzunehmen. Abdeckung für den **gesamten dargestellten Zeitraum je freigegebenem Ticker** prüfen, einschließlich Währung, Splitbasis und sonstiger Ausschüttungen. Renditebasis explizit je Instrument hinterlegen; bei fehlendem Nachweis neutralen Text verwenden. Aus dem Repo lässt sich der heutige Tabellenfüllstand nicht feststellen.

4. **Wichtig – Kaplan-Meier ist passend, aber Kohorte, Zensierung und Unsicherheitsdarstellung sind noch nicht hinreichend definiert.**

   **Beleg:** [Plan:58](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-31_drawdown_seite_plan_v2.md:58) definiert Zeitnull und laufende Zensierung sinnvoll, lässt aber die Verbindung zu Zeitraum und Max-Drawdown-Filter offen. Eine Auswahl abgeschlossener Episoden nach ihrer späteren Endtiefe und laufender Episoden nach ihrer bisherigen Tiefe wäre keine einheitliche Kohorte.

   **Planänderung:**

   - Alle Episoden aufnehmen, die die gewählte Schwelle erstmals erreichen; keine zusätzliche Auswahl nach späterer Endtiefe.
   - Fensterzuordnung ausdrücklich festlegen, konsistent zum bestehenden Peak-Vertrag; grenzüberschreitende Fälle separat zeigen.
   - Zensierungszeit = E minus Übertritt; bei unbekanntem Pfad keine stillschweigende Beschränkung auf zuvor abgeschlossene Fälle.
   - Bei gleicher Dauer Ereignisse und Zensierungen korrekt gemeinsam im Risikosatz behandeln.
   - Median beim ersten `S(t) ≤ 0,5`, sonst „nicht erreicht“.
   - Greenwood-Intervalle als **punktweise, nominelle 95-%-Intervalle** kennzeichnen. Ein simultanes Konfidenzband erfordert eine andere Konstruktion; die [statsmodels-Dokumentation](https://www.statsmodels.org/stable/duration.html) unterscheidet beides ausdrücklich.

   Bei wenigen, zeitlich abhängigen Episoden und nachträglich gewählter aktueller Schwelle darf die Darstellung keine präzise Restdauerprognose nahelegen.

5. **Wichtig – Forward Returns brauchen einen vollständigen Fenster- und Vergleichsvertrag.**

   **Beleg:** [Plan:62](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-31_drawdown_seite_plan_v2.md:62) verhindert durch einen Übertritt je Episode die Häufung täglicher Signale. „Basis = alle Sitzungen mit vollständigem Fenster“ lässt aber Vergleichsmenge, Kennzahlen und Ausschlüsse offen.

   **Planänderung:** Für jede Länge `h` definieren:
   `F_h = exp(Σ lr_{s+1…s+h}) − 1`.
   Vollständigkeit muss den gesamten Pfad betreffen, insbesondere für `min(0,F_1…F_h)`. Eine zwischenzeitliche Recovery beendet das Forward-Fenster nicht. Ereignisse ohne vollständigen Horizont getrennt zählen; n je Horizont anzeigen. Baseline aus demselben Ticker und Zeitraum bilden, Zusammenfassungen vorab festlegen. Überlappungen nach den tatsächlich gemeinsamen Renditesitzungen zählen.

   Der „Zwischenverlust“ ist ein Schlusskursverlust relativ zum Übertrittsschluss, kein Intraday-Verlust und kein späterer Peak-to-Trough-Drawdown. „Kein Test“ passt zur deskriptiven Darstellung; daraus keine bestätigte Überrendite ableiten.

6. **Wichtig – Der Drawdown-Kalender ist sinnvoll, seine Kennzahl heißt aber nicht ohne Zusatz „Max Drawdown je Kalenderjahr“.**

   **Beleg:** [Plan:66](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-31_drawdown_seite_plan_v2.md:66) misst den tiefsten Abstand zum historisch fortgeschriebenen Hoch. Ein Jahr kann damit einen großen Verlust ausweisen, obwohl seine Kurse ausschließlich steigen.

   **Planänderung:** Beschriften als „Tiefster Abstand zum bisherigen Hoch im Jahr“. Formel ausdrücklich:
   `min(D_t)` über die Jahressitzungen, mit Hoch aus der vollständigen verfügbaren Vorgeschichte. „Allzeithoch“ nur bei entsprechender Abdeckung, sonst „Hoch seit Datenbeginn“.

   Der jährliche Ulcer Index ist mit diesem **nicht jährlich zurückgesetzten** Hoch tragfähig. Bei Lücken wird der betroffene Jahreswert unbekannt; keinen Mittelwert nur über die verbleibenden bekannten Tage bilden. Auch ein unvollständiges erstes Jahr kennzeichnen. Fallzahl = ausgewertete Sitzungen angeben.

7. **Wichtig – Atomarität und ein Frische-Health-Check verhindern noch keine veralteten aktuellen Zahlen.**

   **Beleg:** [Plan:91](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-31_drawdown_seite_plan_v2.md:91) nennt atomare Veröffentlichung, aber keinen Fehlervertrag. [atomic_json.py:34](C:/dev/SeasonalEdge/shared/atomic_json.py:34) schützt gegen halbe Dateien, validiert weder Datenfrische noch Schema; `json.dump` erlaubt hier standardmäßig auch NaN. Nightly bietet bereits ein Muster zur Fehlerfortpflanzung über `_FEHLGESCHLAGEN` und Exit 1 ([nightly_refresh.py:538](C:/dev/SeasonalEdge/scripts/nightly_refresh.py:538)).

   **Planänderung:** Nach Kursnachladen und Renditereparatur rechnen. Snapshot mit Erzeugungszeit, Methoden-/Kalenderversion, erwartetem E, tatsächlichem Datenende und Status **für jeden** Ticker veröffentlichen. Fachlich unbekannt und technisch gescheitert unterscheiden; technische Fehler machen Nightly rot. Alte Datei darf erhalten bleiben, aber Seite und Mail müssen sie selbst gegen das beim Lesen erwartete E prüfen. Keine alten Werte für ausgefallene Ticker nachrücken lassen. Nur endliche Zahlen oder `null` veröffentlichen; HTTP-Prüfung zusätzlich zum bestehenden atomaren Schreiber.

8. **Wichtig – Die Mailregel verhindert tägliche Unterwasser-Meldungen, aber nicht alle Wiederholungen und Kalenderlücken.**

   **Beleg:** [Plan:97](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-31_drawdown_seite_plan_v2.md:97) bindet das Ereignis an E. Die Kernliste enthält Krypto und internationale Märkte ([daily_report.py:98](C:/dev/SeasonalEdge/shared/daily_report.py:98)). Der Timer läuft nur Montag bis Freitag ([sa-daily-briefing.timer:7](C:/dev/SeasonalEdge/deploy/systemd/sa-daily-briefing.timer:7)); die bestehende Versandsperre gilt je Berliner Datum ([daily_newsletter.py:249](C:/dev/SeasonalEdge/scripts/daily_newsletter.py:249)).

   Damit kann dasselbe Freitagsereignis an einem börsenfreien Montag erneut aktuell sein. Ein Krypto-Übertritt am Samstag kann dagegen bis Montag verschwunden sein.

   **Planänderung:** Bewusst wählen zwischen „nur jüngstes E, Wochenendereignisse können entfallen“ und „neue Ereignisse seit dem letzten Briefing“. Ereignisidentität aus Ticker, Peak, Schwelle und Übertrittssitzung bilden. Exakte Grenzregel `≤ −10/−20 %` festlegen; beim Sprung über beide Schwellen eine gemeinsame Zeile. Snapshot-Frische zur Versandzeit prüfen. Unbekannte Daten nicht als „kein Ereignis“ protokollieren. Bestehende Versandsperre weiterverwenden.

9. **Wichtig – Die neuen Verträge brauchen gezielte unabhängige Wächterfälle.**

   **Beleg:** [Plan:72](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-31_drawdown_seite_plan_v2.md:72) übernimmt die v1-Testauflagen gut. Für die Erweiterungen sind bislang hauptsächlich ein zensierter KM-Fall und ein unvollständiges Forward-Fenster genannt.

   **Planänderung:** Ergänzen: KM mit gleichzeitiger Recovery/Zensierung, ausschließlich zensierten Fällen, `S=0,5`, Endsprung auf null und Lücke; Forward-Fenster über Recovery/Jahreswechsel, innere Lücke und Überlappung; Jahreswerte mit Vorjahreshoch sowie Teiljahr; echte Nightly-/Mail-Leser mit altem Snapshot, Tickerfehler und Wiederholungsereignis. Die behauptete Tempokorrektur ist bestätigt: [drawdown_analyse.py:166](C:/dev/SeasonalEdge/scripts/research/drawdown_analyse.py:166) vergleicht jetzt gegen `laufend.bis_schwelle`.

Die fünf Fragen:

1. **Episodenvertrag bei unbekanntem Pfad:** Ja, konservativ und tragfähig. Bekannte abgeschlossene Episoden bleiben erhalten; spätere globale Werte werden gesperrt. Für KM zusätzlich den Umgang mit dem am Lückenbeginn noch offenen Fall festlegen.
2. **KM und eine Forward-Beobachtung je Episode:** Ja, unter Befunden 4 und 5. Die Grundidee stimmt; Kohorte, Zensierung und Fenster sind noch zu präzisieren.
3. **Jahreskalender gegen Allzeithoch:** Ja. Er zeigt fortdauernde Belastung über Jahresgrenzen sinnvoll; Bezeichnung und Historienabdeckung gemäß Befund 6 ändern.
4. **Mailregel gegen Dauer-Spam:** Gegen tägliche Wiederholung bei fortbestehendem Drawdown ja. Feiertagswiederholung, Wochenendereignisse und gleichzeitige Schwellenübertritte fehlen noch.
5. **Was fehlt oder ist zu stark?** Es fehlen ein ausführbarer gemeinsamer Schlusszeitvertrag und verbindliche Veröffentlichungs-/Leserregeln. Zu stark sind die Price-Return-Rückrechnung, Yahoo als unabhängiger Nachweis und ein unqualifiziertes „95-%-Konfidenzband“.

**FREIGABE MIT AUFLAGEN** — Befunde 1–9 verbindlich einarbeiten. Phase 3 bleibt bis zur korrigierten Methodik und belegten Datenbasis gesperrt.
tokens used
99.533
Die v1-Auflagen sind **weitgehend, aber noch nicht vollständig operationalisiert**. A2–A5, A7 und A8 sind im Plan übernommen; die Tempokorrektur A4 steht tatsächlich im Code. Bei A1 fehlen die benötigten regulären Schlusszeiten in der Browser-API, bei A6 die belastbare Zuordnung der Renditebasis. Die Erweiterungen sind grundsätzlich tragfähig, brauchen aber die folgenden Präzisierungen.

Read-only geprüft; keine Dateien geändert. Den echten Kalenderkern und eine Gegenrechnung zur Dividendenformel habe ich ausgeführt. Kein vollständiger Gate-Lauf, keine Live-Datenbankprüfung.

1. **Blockierend für Phase 1/2 – Der Schlusszeitvertrag lässt sich mit der genannten API noch nicht umsetzen.**

   **Beleg:** [Plan:25](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-31_drawdown_seite_plan_v2.md:25) erwartet reguläre Schlusszeiten aus dem Kalender. [boersenkalender.js:405](C:/dev/SeasonalEdge/landing/js/boersenkalender.js:405) liefert Schlusszeit und Zone jedoch nur für eingetragene Halbtage. Ausgeführt für den 30.10.2026: NYSE und XETRA liefern jeweils `schlusszeit:null`; der NYSE-Halbtag 27.11. liefert korrekt `13:00`.

   Auch Python-`letzte_session` ist kein gleichwertiger Ersatz: [exchange_holidays.py:358](C:/dev/SeasonalEdge/shared/exchange_holidays.py:358) verwendet standardmäßig 15 Minuten Puffer, berücksichtigt hier keine Halbtagsschlüsse, liefert für Krypto den laufenden Tag und unterstützt Forex nicht.

   **Planänderung:** Reguläre Schlusszeiten als gemeinsamen, belegten Kalendervertrag ergänzen und JS/Python daraus speisen; Generator und Quelldaten ändern, nicht die erzeugte JS-Datei. E an einem eingefrorenen Zeitpunkt mit 30 Minuten Puffer berechnen. Rückfallregel präzisieren: vorherige **offene Sitzung**, auch an Wochenenden und Feiertagen. Tests für regulären Schluss, Halbtag, Sommerzeitwechsel, Forex und Krypto in beiden Produktionspfaden.

2. **Blockierend für die beschriebene Phase 3 – Die Rückrechnungsformel ist falsch.**

   **Beleg:** [Plan:103](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-31_drawdown_seite_plan_v2.md:103) setzt
   `r_price = r_total − ln(1 + D/C_prev)`.

   Gegenbeispiel für eine echte Gesamtrendite: Vortagsschluss 100, Ex-Schluss 90, Dividende 10. Gesamtrendite = 0; die Planformel liefert eine Preisrendite von **−9,09 %**, tatsächlich sind es **−10 %**.

   Bei `exp(r_total) = (C_t + D)/C_prev` lautet die Umkehrung:
   `r_price = ln(exp(r_total) − D/C_prev)`.
   Ein rückwärts adjustierter Lieferantenkurs muss allerdings nicht genau dieser Gesamtrenditedefinition entsprechen. Dividendenbereinigung kann stattdessen über einen Abschlagsfaktor erfolgen; siehe die dokumentierte [Berechnung von MathWorks](https://www.mathworks.com/help/finance/adjustedclosingprices.html).

   **Planänderung:** Die Formel jetzt streichen. Phase 3 muss zuerst die tatsächliche Adjustierungsregel nachweisen und darauf die Umkehrung aufbauen. Bevorzugt konsistente, splitbereinigte Preis- und Dividendenreihen verwenden. Handfälle für Dividende, Split, Sonderausschüttung und deren Kombination verpflichtend machen.

3. **Wichtig – Der geplante unabhängige Dividendennachweis ist nicht unabhängig; die Basiszuordnung bleibt unvollständig.**

   **Beleg:** [fetch_event_data.py:25](C:/dev/SeasonalEdge/scripts/fetch_event_data.py:25) lädt die Dividendendaten bereits von Yahoo, begrenzt auf 25 Jahre. Ein Vergleich mit Yahoo prüft somit Importvollständigkeit gegenüber derselben Quelle. Der Schreiber speichert außerdem nur Ticker, Ex-Datum und Betrag ([Zeile 139](C:/dev/SeasonalEdge/scripts/fetch_event_data.py:139)); die Tabelle ergänzt standardmäßig `USD` ([create_event_tables.sql:8](C:/dev/SeasonalEdge/scripts/create_event_tables.sql:8)).

   Für A6 reichen die Kategorien ebenfalls nicht: DAX und Euro Stoxx 50 stehen beide als `EU-Index`, ohne Preis-/Performancekennzeichen ([symbols.py:569](C:/dev/SeasonalEdge/shared/symbols.py:569)). Der Kursparser kann bei fehlendem `adjclose` auf Rohschlüsse zurückfallen ([yahoo_downloader.py:111](C:/dev/SeasonalEdge/shared/yahoo_downloader.py:111)).

   **Planänderung:** Yahoo als Abgleich derselben Quelle bezeichnen; für einen unabhängigen Nachweis Emittenten-/Börsendaten hinzunehmen. Abdeckung für den **gesamten dargestellten Zeitraum je freigegebenem Ticker** prüfen, einschließlich Währung, Splitbasis und sonstiger Ausschüttungen. Renditebasis explizit je Instrument hinterlegen; bei fehlendem Nachweis neutralen Text verwenden. Aus dem Repo lässt sich der heutige Tabellenfüllstand nicht feststellen.

4. **Wichtig – Kaplan-Meier ist passend, aber Kohorte, Zensierung und Unsicherheitsdarstellung sind noch nicht hinreichend definiert.**

   **Beleg:** [Plan:58](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-31_drawdown_seite_plan_v2.md:58) definiert Zeitnull und laufende Zensierung sinnvoll, lässt aber die Verbindung zu Zeitraum und Max-Drawdown-Filter offen. Eine Auswahl abgeschlossener Episoden nach ihrer späteren Endtiefe und laufender Episoden nach ihrer bisherigen Tiefe wäre keine einheitliche Kohorte.

   **Planänderung:**

   - Alle Episoden aufnehmen, die die gewählte Schwelle erstmals erreichen; keine zusätzliche Auswahl nach späterer Endtiefe.
   - Fensterzuordnung ausdrücklich festlegen, konsistent zum bestehenden Peak-Vertrag; grenzüberschreitende Fälle separat zeigen.
   - Zensierungszeit = E minus Übertritt; bei unbekanntem Pfad keine stillschweigende Beschränkung auf zuvor abgeschlossene Fälle.
   - Bei gleicher Dauer Ereignisse und Zensierungen korrekt gemeinsam im Risikosatz behandeln.
   - Median beim ersten `S(t) ≤ 0,5`, sonst „nicht erreicht“.
   - Greenwood-Intervalle als **punktweise, nominelle 95-%-Intervalle** kennzeichnen. Ein simultanes Konfidenzband erfordert eine andere Konstruktion; die [statsmodels-Dokumentation](https://www.statsmodels.org/stable/duration.html) unterscheidet beides ausdrücklich.

   Bei wenigen, zeitlich abhängigen Episoden und nachträglich gewählter aktueller Schwelle darf die Darstellung keine präzise Restdauerprognose nahelegen.

5. **Wichtig – Forward Returns brauchen einen vollständigen Fenster- und Vergleichsvertrag.**

   **Beleg:** [Plan:62](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-31_drawdown_seite_plan_v2.md:62) verhindert durch einen Übertritt je Episode die Häufung täglicher Signale. „Basis = alle Sitzungen mit vollständigem Fenster“ lässt aber Vergleichsmenge, Kennzahlen und Ausschlüsse offen.

   **Planänderung:** Für jede Länge `h` definieren:
   `F_h = exp(Σ lr_{s+1…s+h}) − 1`.
   Vollständigkeit muss den gesamten Pfad betreffen, insbesondere für `min(0,F_1…F_h)`. Eine zwischenzeitliche Recovery beendet das Forward-Fenster nicht. Ereignisse ohne vollständigen Horizont getrennt zählen; n je Horizont anzeigen. Baseline aus demselben Ticker und Zeitraum bilden, Zusammenfassungen vorab festlegen. Überlappungen nach den tatsächlich gemeinsamen Renditesitzungen zählen.

   Der „Zwischenverlust“ ist ein Schlusskursverlust relativ zum Übertrittsschluss, kein Intraday-Verlust und kein späterer Peak-to-Trough-Drawdown. „Kein Test“ passt zur deskriptiven Darstellung; daraus keine bestätigte Überrendite ableiten.

6. **Wichtig – Der Drawdown-Kalender ist sinnvoll, seine Kennzahl heißt aber nicht ohne Zusatz „Max Drawdown je Kalenderjahr“.**

   **Beleg:** [Plan:66](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-31_drawdown_seite_plan_v2.md:66) misst den tiefsten Abstand zum historisch fortgeschriebenen Hoch. Ein Jahr kann damit einen großen Verlust ausweisen, obwohl seine Kurse ausschließlich steigen.

   **Planänderung:** Beschriften als „Tiefster Abstand zum bisherigen Hoch im Jahr“. Formel ausdrücklich:
   `min(D_t)` über die Jahressitzungen, mit Hoch aus der vollständigen verfügbaren Vorgeschichte. „Allzeithoch“ nur bei entsprechender Abdeckung, sonst „Hoch seit Datenbeginn“.

   Der jährliche Ulcer Index ist mit diesem **nicht jährlich zurückgesetzten** Hoch tragfähig. Bei Lücken wird der betroffene Jahreswert unbekannt; keinen Mittelwert nur über die verbleibenden bekannten Tage bilden. Auch ein unvollständiges erstes Jahr kennzeichnen. Fallzahl = ausgewertete Sitzungen angeben.

7. **Wichtig – Atomarität und ein Frische-Health-Check verhindern noch keine veralteten aktuellen Zahlen.**

   **Beleg:** [Plan:91](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-31_drawdown_seite_plan_v2.md:91) nennt atomare Veröffentlichung, aber keinen Fehlervertrag. [atomic_json.py:34](C:/dev/SeasonalEdge/shared/atomic_json.py:34) schützt gegen halbe Dateien, validiert weder Datenfrische noch Schema; `json.dump` erlaubt hier standardmäßig auch NaN. Nightly bietet bereits ein Muster zur Fehlerfortpflanzung über `_FEHLGESCHLAGEN` und Exit 1 ([nightly_refresh.py:538](C:/dev/SeasonalEdge/scripts/nightly_refresh.py:538)).

   **Planänderung:** Nach Kursnachladen und Renditereparatur rechnen. Snapshot mit Erzeugungszeit, Methoden-/Kalenderversion, erwartetem E, tatsächlichem Datenende und Status **für jeden** Ticker veröffentlichen. Fachlich unbekannt und technisch gescheitert unterscheiden; technische Fehler machen Nightly rot. Alte Datei darf erhalten bleiben, aber Seite und Mail müssen sie selbst gegen das beim Lesen erwartete E prüfen. Keine alten Werte für ausgefallene Ticker nachrücken lassen. Nur endliche Zahlen oder `null` veröffentlichen; HTTP-Prüfung zusätzlich zum bestehenden atomaren Schreiber.

8. **Wichtig – Die Mailregel verhindert tägliche Unterwasser-Meldungen, aber nicht alle Wiederholungen und Kalenderlücken.**

   **Beleg:** [Plan:97](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-31_drawdown_seite_plan_v2.md:97) bindet das Ereignis an E. Die Kernliste enthält Krypto und internationale Märkte ([daily_report.py:98](C:/dev/SeasonalEdge/shared/daily_report.py:98)). Der Timer läuft nur Montag bis Freitag ([sa-daily-briefing.timer:7](C:/dev/SeasonalEdge/deploy/systemd/sa-daily-briefing.timer:7)); die bestehende Versandsperre gilt je Berliner Datum ([daily_newsletter.py:249](C:/dev/SeasonalEdge/scripts/daily_newsletter.py:249)).

   Damit kann dasselbe Freitagsereignis an einem börsenfreien Montag erneut aktuell sein. Ein Krypto-Übertritt am Samstag kann dagegen bis Montag verschwunden sein.

   **Planänderung:** Bewusst wählen zwischen „nur jüngstes E, Wochenendereignisse können entfallen“ und „neue Ereignisse seit dem letzten Briefing“. Ereignisidentität aus Ticker, Peak, Schwelle und Übertrittssitzung bilden. Exakte Grenzregel `≤ −10/−20 %` festlegen; beim Sprung über beide Schwellen eine gemeinsame Zeile. Snapshot-Frische zur Versandzeit prüfen. Unbekannte Daten nicht als „kein Ereignis“ protokollieren. Bestehende Versandsperre weiterverwenden.

9. **Wichtig – Die neuen Verträge brauchen gezielte unabhängige Wächterfälle.**

   **Beleg:** [Plan:72](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-31_drawdown_seite_plan_v2.md:72) übernimmt die v1-Testauflagen gut. Für die Erweiterungen sind bislang hauptsächlich ein zensierter KM-Fall und ein unvollständiges Forward-Fenster genannt.

   **Planänderung:** Ergänzen: KM mit gleichzeitiger Recovery/Zensierung, ausschließlich zensierten Fällen, `S=0,5`, Endsprung auf null und Lücke; Forward-Fenster über Recovery/Jahreswechsel, innere Lücke und Überlappung; Jahreswerte mit Vorjahreshoch sowie Teiljahr; echte Nightly-/Mail-Leser mit altem Snapshot, Tickerfehler und Wiederholungsereignis. Die behauptete Tempokorrektur ist bestätigt: [drawdown_analyse.py:166](C:/dev/SeasonalEdge/scripts/research/drawdown_analyse.py:166) vergleicht jetzt gegen `laufend.bis_schwelle`.

Die fünf Fragen:

1. **Episodenvertrag bei unbekanntem Pfad:** Ja, konservativ und tragfähig. Bekannte abgeschlossene Episoden bleiben erhalten; spätere globale Werte werden gesperrt. Für KM zusätzlich den Umgang mit dem am Lückenbeginn noch offenen Fall festlegen.
2. **KM und eine Forward-Beobachtung je Episode:** Ja, unter Befunden 4 und 5. Die Grundidee stimmt; Kohorte, Zensierung und Fenster sind noch zu präzisieren.
3. **Jahreskalender gegen Allzeithoch:** Ja. Er zeigt fortdauernde Belastung über Jahresgrenzen sinnvoll; Bezeichnung und Historienabdeckung gemäß Befund 6 ändern.
4. **Mailregel gegen Dauer-Spam:** Gegen tägliche Wiederholung bei fortbestehendem Drawdown ja. Feiertagswiederholung, Wochenendereignisse und gleichzeitige Schwellenübertritte fehlen noch.
5. **Was fehlt oder ist zu stark?** Es fehlen ein ausführbarer gemeinsamer Schlusszeitvertrag und verbindliche Veröffentlichungs-/Leserregeln. Zu stark sind die Price-Return-Rückrechnung, Yahoo als unabhängiger Nachweis und ein unqualifiziertes „95-%-Konfidenzband“.

**FREIGABE MIT AUFLAGEN** — Befunde 1–9 verbindlich einarbeiten. Phase 3 bleibt bis zur korrigierten Methodik und belegten Datenbasis gesperrt.
