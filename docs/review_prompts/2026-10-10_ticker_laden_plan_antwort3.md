# Antwort Codex — Ticker schneller laden, Runde 3 (2026-10-10)

Prompt: [2026-10-10_ticker_laden_plan_v3.md](2026-10-10_ticker_laden_plan_v3.md). model: gpt-6.1-sol

**Urteil**

**Mit Auflagen.** v3 erfüllt wesentliche Auflagen aus Runde 2, reicht aber noch nicht als vollständiger Bauplan. S3 ist als Schattenmodus passend abgegrenzt.
Geprüft: drei neueste Versionseinträge, Vorgängerbefunde, Produktionspfade und isolierte Gegenproben. Nichts geschrieben; keine Live-Laufzeitmessungen.

**Antworten**

1. **Auflagen vor S1 erfüllt?** Überwiegend: Projektion, Kopien, Abdeckung, TTL, vollständige Neuladung und Fehlerveröffentlichung sind geklärt. Offen bleiben Generationenschnittstelle, vollständige Migration und belastbare Abnahme.
2. **Koordinator widerspruchsfrei?** Die Serialisierung ist konsistent. Bei genau einer laufenden Ladung je Ticker kann deren Abschlussreihenfolge allerdings nicht vertauscht werden; dieser Prüfpunkt braucht einen konkret erreichbaren Fall.
3. **Verbraucherprobe ausreichend?** Nein. Gleiche Rechenfunktionen mit gleichen direkt eingespeisten Kursen prüfen weder Ladeparameter noch Einbindung, Cache-Frische oder Antwortschutz.
4. **JS-Austausch fair?** In der beschriebenen Form nein: Er erfasst die HTML-Änderungen nicht und verändert die Cachebedingungen.

**Befunde**

1. **Hoch — S0 misst nicht die vollständige Migration.** [Plan:14](/C:/dev/SeasonalEdge/docs/review_prompts/2026-10-10_ticker_laden_plan_v3.md:14)
   Die Lader und Cacheverzweigungen stehen vielfach inline im HTML. Beispielsweise bleiben [Dekadenzyklus:292](/C:/dev/SeasonalEdge/landing/pages/dekadenzyklus.html:292) und seine Scriptliste beim JS-Abfang unverändert; die neue `kurse.js` wird dort überhaupt nicht angefordert. Gemessen würde ein Mischstand.

2. **Hoch — Die Verbraucherabnahme umgeht den geänderten Produktionspfad.** [Plan:84](/C:/dev/SeasonalEdge/docs/review_prompts/2026-10-10_ticker_laden_plan_v3.md:84)
   Die genannten Plain-Vanilla-Proben laden Rechenmodule und erzeugen Eingangsreihen selbst. Eine falsch migrierte Bereichsgrenze oder ein fehlendes `open` im Seitenaufruf kann damit unentdeckt bleiben. Beabsichtigte Fehlerkorrekturen brauchen außerdem eigene korrekte Sollwerte.

3. **Mittel — Bestandsgeneration ist kein verfügbarer Rückgabevertrag.** [Plan:54](/C:/dev/SeasonalEdge/docs/review_prompts/2026-10-10_ticker_laden_plan_v3.md:54)
   Verbraucher sollen Ergebnisse nach Generation cachen; `laden` liefert aber ausschließlich kopierte Zeilen. Festlegen, wie die Generation genau dieser Rückgabe zugänglich wird. Sie muss auch nach LRU-Verdrängung eindeutig bleiben, damit alte Ergebnis-Caches nicht wieder als Treffer gelten.

4. **Mittel — Die übernommene Migrationstabelle ist unvollständig.** [Plan:52](/C:/dev/SeasonalEdge/docs/review_prompts/2026-10-10_ticker_laden_plan_v3.md:52)
   [landing/embed.html:89](/C:/dev/SeasonalEdge/landing/embed.html:89) enthält einen zusätzlichen eigenen Kurslader, den Runde 1 nicht erfasst hat. Er widerspricht dem Wächter über ganz `landing/`. Gegenprobe am echten Lader: bei `Content-Range: …/*` **1.000 statt 1.500 Sollzeilen**.

5. **Mittel — Gleiche Header ergeben noch keinen fairen Leistungsvergleich.** [Plan:14](/C:/dev/SeasonalEdge/docs/review_prompts/2026-10-10_ticker_laden_plan_v3.md:14)
   Routing deaktiviert den HTTP-Cache; nur beim Nachher-Lauf eingesetzt verfälscht es insbesondere Seitennavigation. ([Playwright-Dokumentation](https://playwright.dev/docs/api/class-page#page-route)) Der gleiche Kursinhalt und definierte localStorage-Ausgangszustände fehlen ebenfalls im Messvertrag.

6. **Mittel — Cursor-Fortschritt bleibt ungeprüft.** [Plan:31](/C:/dev/SeasonalEdge/docs/review_prompts/2026-10-10_ticker_laden_plan_v3.md:31)
   HTTP-/Arrayprüfung reicht bei wiederholten Blöcken nicht. Der bestehende Keyset-Lader fordert in der Gegenprobe denselben Cursor erneut an. Ein Timeout je Block begrenzt eine Folge schnell erfolgreicher, aber nicht fortschreitender Antworten nicht.

**Auflagen**

- S0 mit vollständigem Kandidaten-HTML einschließlich Inline-Code und Script-Einbindungen durchführen; Routing, Cachezustände und überprüften Kursinhalt zwischen den Varianten angleichen.
- Generation an die konkrete Rückgabe binden; laufende Koordinatoren bei LRU-Verdrängung erhalten und erreichbare Konkurrenz-/Fehlerfälle festlegen.
- Embed in Migration und Funktionsabnahme aufnehmen.
- Je Seite den echten Lade-/Auswahlpfad durch `SA.kurse` mit PostgREST-Fixtures prüfen: Parameter, Stichprobe, Kennzahlen, TTL, verspätete Erfolge und Fehler; DE-/EN-Einbindung kontrollieren.
- Strikt fortschreitende gültige Datums-Cursor verlangen; wiederholte, unsortierte oder fehlende Cursor müssen ablehnen und dürfen keinen Bestand veröffentlichen.
