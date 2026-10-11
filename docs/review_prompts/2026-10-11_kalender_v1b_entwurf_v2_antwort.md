**Urteil: mit Änderungen.** Runde 1 ist weitgehend aufgegriffen; Fehlerweg und Sperre laufender Arbeit sind noch nicht vollständig als Bauvertrag definiert.

**Befunde**

- **P1 – Kennungen ersetzen repariert den ersten fehlgeschlagenen Rollout nicht** ([Z. 23](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-11_kalender_v1b_entwurf_v2.md:23)). Scheitert der erste Blog-Build, enthalten die bisherigen Blog-Ausgaben weder Kennung noch `methode.js`. Der Abschlussprüfer wird rot, stellt aber keine Auslieferbarkeit her. Neue streng prüfende JS-Dateien treffen weiterhin auf HTML ohne Bootstrap. Dafür braucht es einen Wiederherstellungsweg.
- **P1 – Bereits gestartete Chart-Operationen bleiben offen** ([Z. 45](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-11_kalender_v1b_entwurf_v2.md:45)). Die Hülle verhindert neue Aufrufe; ein vorher gestartetes asynchrones `render()`/Update wird dadurch nicht beendet. Ein `destroy()`-Zähler beweist nicht, dass dessen spätere Fortsetzung keine Serien wiederherstellt. Dieser Befund aus Runde 1 ist damit noch nicht aufgelöst.
- **P2 – Fetch-Abschluss und Ergebnisübernahme brauchen getrennte Regeln** ([Z. 35](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-11_kalender_v1b_entwurf_v2.md:35)). `fetch()` erfüllt sein Promise bereits bei verfügbaren Antwortheadern. Registrierung bis zum Body-Ende und Sperrprüfung vor späteren Rückrufen fehlen ausdrücklich für direkte Abrufe. Ein bereits erfülltes Promise lässt sich durch `abort()` nicht zurücknehmen; beispielsweise hängt `app.js` nach `r.text()` Skripte an `document.head` an, außerhalb des Body-Wächters.
- **P2 – `load` kann den Neuladeschutz zu früh löschen** ([Z. 54](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-11_kalender_v1b_entwurf_v2.md:54)). Kommt die Abweichung jeweils durch ein nach `load` geladenes Skript, löscht jeder Wiederanlauf zuvor die Marke. Dadurch sind wiederholte automatische Reloads innerhalb der 120 Sekunden möglich.

**Auflagen**

- Fehlerprobe ausdrücklich mit bisherigen Blog-/EN-Ausgaben **ohne Bootstrap**; bei Fehlschlag einen vollständig auslieferbaren Stand wiederherstellen.
- Chart-Probe mit verzögertem Render-/Update-Abschluss nach Sperre und beobachtbaren Serien; Sperre muss auch nach dessen Abschluss bestehen.
- Direkten Fetch zwischen Headern, Body-Abschluss und Ergebnisübernahme sperren; auch spätere Aktionen im `head` prüfen.
- Neulademarke über automatische Wiederanläufe erhalten; Probe mit wiederholter Abweichung **nach `load`** ergänzen.

Read-only geprüft; nichts geschrieben.
