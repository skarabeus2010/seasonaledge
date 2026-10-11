**Urteil: mit Änderungen.** Der Bootstrap entspricht v7/v8; die Deploybindung und die dauerhafte Sperre sind noch unvollständig.

**Befunde**

- **P1 – Releasekennung erreicht den Blog-Build nicht automatisch.** `GIT_SHA` entsteht derzeit nur im separat gestarteten `inject_credentials.sh`; die aufrufende Deploy-Shell erhält diese Variable nicht. Das vorgeschlagene `-e SA_RELEASE=$GIT_SHA` kann deshalb leer bleiben. Kennung einmal im Workflow bestimmen und explizit an Injection und Builder übergeben.
- **P1 – Platzhalterfreiheit beweist keine Konsistenz.** Bereits erzeugte `landing/en/`-Dateien und `blog/output/` können alte Kennungen ohne Platzhalter enthalten. Scheitert der Build nach der JS-Injection, bleibt dieser Mischstand bestehen; Neuladen repariert ihn nicht. Prüfung erst nach allen Builds, einschließlich DE-/EN-Blog; bei Fehler konsistenten Stand wiederherstellen.
- **P1 – Sperre muss auch passende Folgeskripte ablehnen.** Nach einer Abweichung darf `SA.__release(k)` bei anschließend passender Kennung nicht wieder erfolgreich zurückkehren. `__gesperrt` muss Vorrang haben. Der Entwurf beschreibt bisher nur den Kennungsvergleich.
- **P1 – DOM-Ersatz allein beendet keine laufenden Arbeiten.** Bereits geplante Rückrufe und Chart-Renderings laufen weiter. Neue DOM-Anhänge sind möglich, etwa in `app.js`. Chart-Registry, ausstehende Renderings und spätere Ausgaben brauchen einen überprüfbaren Sperrvertrag. Der bestehende Seitenprobe-Stub hat wirkungslose `destroy()`/`exec()` und beweist keine Chart-Zerstörung.
- **P2 – Neuladeschutz ist nicht vollständig definiert.** Wechselnde Kennungspaare können weitere automatische Reloads auslösen; `sessionStorage` kann werfen. Speicherfehler dürfen Sperre/Hinweis nicht verhindern. Eine erfolgreiche konsistente Ladung und ein manueller Wiederanlauf brauchen definierte Regeln für die Marke.
- **P2 – Zwei Integrationsstellen fehlen ausdrücklich:** Die Prüfzeile für `boersenkalender.js` muss aus dessen Generator/API entstehen, sonst scheitert `--pruefen`. Die v8-Sperre direkter `/landing/`-Fetches, etwa in `kalender-compute.js`, ist durch das angekündigte V1b-2 mit ausschließlich Kurs-/Supabase-Pfaden noch nicht abgedeckt.

**Antworten auf 1–4**

1. **Streng.** Die tolerante Form umgeht bei fehlendem/fehlgeschlagenem Bootstrap die Prüfung. Gemeinsamer Harness-Helfer: echte `methode.js`, explizite HTML-Kennung, keine Ersatzfunktion.
2. **Commitkennung reicht**, sofern sie den tatsächlich ausgelieferten Stand bezeichnet und überall identisch ist. Vollständigen SHA bevorzugen; keine Zeitstempel-Ausweichkennung. Eine eigene Deploykennung ist für den beschriebenen Rückweg nicht erforderlich.
3. **Ja:** fehlgeschlagene EN-/Blog-Neuerzeugung kann dauerhaft alte HTML-Kennungen neben neue JS-Kennungen stellen. Außerdem gilt `must-revalidate` nicht überall: `/rechtliches`, `/ueber-uns` und direktes `/landing/` haben derzeit 24 Stunden Cache. Blog-Skripte ebenfalls mit Release-Cachebuster versehen.
4. **Getrennt bauen und prüfen: ja; getrennt live freigeben: derzeit nein.** V8/v9 verlangen auch nach später Abweichung keine weiteren Anfragen oder Ergebnisübernahmen. V1b-1 allein erfüllt diesen Vertrag nicht.

**Auflagen**

- Gemeinsame Kennungsquelle, vollständige Prüfung der erzeugten Ausgaben und konsistenter Fehler-/Wiederholungsweg.
- V1b-1 und V1b-2 vor gemeinsamem Deploy abnehmen; direkte Datenabrufe einschließen.
- Proben mit echten Bootstrap-/Transportpfaden, beobachtbarer Chart-Zerstörung, Speicherfehlern und erneutem passenden Skript nach Sperre; Mutationen müssen benannte Vertragsverstöße nachweisen.

Read-only geprüft; nichts geschrieben.
