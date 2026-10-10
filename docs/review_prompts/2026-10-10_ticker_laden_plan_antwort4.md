codex
**Urteil**

**Freigabe als Bauplan mit Auflagen.** A2, A3 und A5 schließen die entsprechenden Befunde aus Runde 3. A1 und A4 brauchen noch präzisierte Vergleichsregeln.
Geprüft: drei neueste Versionseinträge, v3/v4, frühere Antworten und Produktionspfade. Nichts geschrieben; keine Live-Messung oder vollständige jsdom-Seitenprobe.

**Antworten**

1. **Reichen A1–A5?** Für eine bedingte Freigabe ja. Koordinator, Generation, Embed-Migration und Cursor-Vertrag sind ausreichend beschrieben. Die verbleibenden Auflagen betreffen die Abnahme.
2. **Ist jsdom realistisch?** Für Ladepfade, Chart-Eingaben und DOM-Texte grundsätzlich ja. Die Seitenzahl ist kein Hindernis; Startbedingungen und externe Abhängigkeiten müssen definiert werden. jsdom führt Skripte nur mit entsprechender Konfiguration aus und berechnet kein Layout. ([jsdom-Dokumentation](https://github.com/jsdom/jsdom#executing-scripts))
   Minimale Alternative: derselbe Prüfvertrag mit Playwright auf echten lokalen Seiten, festen API-Fixtures und echten Auswahlhandlungen; Netzabfang ausschließlich für die Funktionsprobe. ([Playwright](https://playwright.dev/docs/mock))
3. **Sonst etwas?** Vorher-Fixtures brauchen eine feste Uhr, Zeitzone und einen benannten Git-Stand. S3 kann im Schattenmodus bleiben.

**Befunde**

1. **Hoch — A4 verlangt Gleichheit auf der falschen Ebene.** [v4:36](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-10_ticker_laden_plan_v4.md:36)
   Der Koordinator darf Felder vereinigen und eine frühere Grenze laden. Dashboard-Historie, Vollhistorie und Overnight haben unterschiedliche Anforderungen ([Dashboard:2196](C:/dev/SeasonalEdge/landing/pages/dashboard.html:2196)). Eine korrekte Bündelung erzeugt deshalb andere Netzabfragen als vorher.
   Gleich bleiben müssen die **Anforderungen und zurückgegebenen Sichten je Verbraucher**. Netzabfragen separat gegen den Keyset-/Vereinigungsvertrag prüfen.

2. **Mittel — A1 definiert den Inhaltsvergleich nicht unabhängig von der Bündelung.** [v4:14](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-10_ticker_laden_plan_v4.md:14)
   Zeilenzahl und Hash sämtlicher empfangener Kurszeilen können sich allein durch entfallene Doppelabrufe oder andere Feldprojektionen ändern. So könnten gerade erfolgreiche Optimierungen als ungültige Messzellen verschwinden.
   Inhalt pro fachlich benötigter Sicht kanonisch vergleichen; übertragene Zeilen, Bytes und Anfragen bleiben separate Messgrößen.

3. **Mittel — A4 lässt einen unvollständig gestarteten Seitenlauf als Vergleichsreferenz zu.** [v4:33](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-10_ticker_laden_plan_v4.md:33)
   ApexCharts und Kurs-Fixtures allein reichen nicht: `loadComponent` erwartet HTML-Antworten, Auth verwendet SDK-Methoden, und unveränderte Credential-Platzhalter führen beim Dekadenzyklus zum JSON-Fallback ([Dekadenzyklus:279](C:/dev/SeasonalEdge/landing/pages/dekadenzyklus.html:279)).
   Komponenten, Wörterbücher, Metadaten, Nebenabfragen und gegebenenfalls Auth deterministisch bedienen. Jeder Fall braucht einen nachgewiesenen Auswahl-/Ladepfad, erwartete Ausgaben und einen Abschluss mit Deadline; zwei leere Ergebnisse beweisen keine Kompatibilität.

4. **Mittel — Festgeschriebene Vorher-Werte sind ohne feste Uhr nicht reproduzierbar.** [v4:38](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-10_ticker_laden_plan_v4.md:38)
   Das Dashboard berechnet Bereichsgrenzen aus `new Date()` ([Dashboard:2259](C:/dev/SeasonalEdge/landing/pages/dashboard.html:2259)); weitere Anzeigen hängen vom aktuellen Jahr/Tag ab. Dieselben Kurs-Fixtures können später andere URLs, Serien und Kennzahlen ergeben.

**Auflagen**

- A4 auf Verbraucheranforderungen und exakte Rückgabesichten umstellen; zulässige gebündelte Netzabfragen gesondert prüfen.
- A1 einen kanonischen Inhaltsvergleich geben, der Wiederholungen und zusätzliche Transportfelder berücksichtigt, ohne widersprüchliche Werte zu verdecken.
- Für A4 Uhr, Zeitzone, Ausgangsspeicher, Baseline-Commit, Abhängigkeiten und Abschlussnachweise festlegen. Browser-Ausnahmen automatisiert mit denselben Assertions prüfen; EN-Einbindung für tatsächlich erzeugte EN-Seiten kontrollieren.
