**Schluss: TRAGFÄHIG MIT ÄNDERUNGEN.** v4 übernimmt die wesentlichen Korrekturen aus der vorigen Runde richtig. Jahresgewichtung, gemeinsame Jahresmenge, konservative Behandlung ungültiger Ziehungen, Saisonverkettung und Renditemaß sind jetzt ausreichend definiert. Vor der endgültigen Festschreibung bleiben drei Punkte.

1. **Die Bootstrap-Kalibrierung braucht einen vollständigen Prüfvertrag.**  
   [v4, Zeilen 33–36](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-31_gamma_indikator_plan_v4.md:33) nennen AR(1)-Nullfälle und eine maximale Verwerfungsrate von 7 %. Offen bleiben Simulationszahl, Parameter, Bezug der Verwerfungsrate und deren Zufallsunsicherheit.

   Außerdem bedeutet „kein Signaleffekt“ im Datengenerator nicht automatisch, dass die getesteten Kontraste null sind: Bei autokorrelierten Renditen können aus vergangenen Kursbewegungen gebildete Signale zukünftige Renditen unterscheiden. Die Simulation muss deshalb die **Nullhypothesen für ΔU und ΔS** herstellen beziehungsweise unabhängig nachweisen.

   **Konkrete Ergänzung:**

   - Szenarien, Parameter und Simulationsseeds vorab festlegen; gemeinsame Marktbewegungen der drei ETFs, wechselnde Volatilität und ungleiche Zellbesetzung berücksichtigen.
   - Beispielsweise **2 000 unabhängige Datensätze je Szenario** simulieren. Das ist eine andere Größe als die 100 000 Bootstrap-Ziehungen je Datensatz.
   - Verwerfungsraten je Hypothese vor Holm und die Wahrscheinlichkeit mindestens einer falschen Verwerfung nach Holm getrennt berichten. Nicht auswertbare Läufe separat zählen.
   - Das Akzeptanzkriterium einschließlich Monte-Carlo-Unsicherheit festlegen, etwa: obere einseitige 95-%-Binomialgrenze höchstens 7 % je Nullszenario.
   - Einen klaren Alternativfall ergänzen, der einen bekannten Kontrast erkennt. Ein Verfahren, das immer `p = 1` liefert, darf die Kalibrierung nicht bestehen.

   Der stationäre Bootstrap wurde für schwach abhängige stationäre Beobachtungen entwickelt; Jahreswechsel und wechselnde Marktbedingungen brauchen daher diese zusätzliche Prüfung. [Politis und Romano](https://doi.org/10.1080/01621459.1994.10476870). Die getrennte Planung von Simulationswiederholungen und Monte-Carlo-Unsicherheit entspricht der methodischen Empfehlung von [Morris, White und Crowther](https://doi.org/10.1002/sim.8086).

2. **Verschobene Ausstiege lösen fehlende tägliche Bewertungen noch nicht.**  
   [v4, Zeilen 48–52](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-31_gamma_indikator_plan_v4.md:48) regeln den späteren Ausstieg, aber nicht den Kapitalwert während der Lücke. Ohne Bewertung ist auch der tatsächliche Drawdown unbekannt. Außerdem muss die Verschiebung an den Grenzen von Entdeckung und Prüfzeitraum enden.

   **Konkrete Ergänzung:**

   > Fehlt während einer offenen Position ein gültiger Bewertungskurs, bleibt der tägliche Kapitalwert unbekannt. Drawdown und MAE über diese Lücke werden als nicht vollständig bestimmbar gekennzeichnet; keine Interpolation oder Fortschreibung. Die Position bleibt bis zum ersten gültigen Schluss offen und blockiert weitere Einstiege. Liegt dieser Schluss außerhalb des jeweiligen Auswertungszeitraums, bleibt der Trade offen beziehungsweise zensiert; spätere Daten werden nicht zur Vervollständigung herangezogen.

   „Barbestand + P&L“ außerdem eindeutig als Kapitalrechnung definieren, beispielsweise:

   ```text
   Kapital(t) = Kapital unmittelbar vor Einstieg
                − bisherige Kosten
                + Richtung × Stückzahl × (Bewertungskurs(t) − Einstiegskurs)
   ```

   Dies gilt auf derselben rekonstruierten Kursbasis wie der Einstieg. Handfall ohne Kosten: Anfangskapital 100, Einstieg 100, Bewertung 110 → Long-Kapital 110, Short-Kapital 90. Kostenbasis und Behandlung eines aufgebrauchten Reihenkapitals ebenfalls festschreiben.

3. **Die tatsächlich gehandelten Filterkombinationen fehlen noch.**  
   Die übernommenen Regeln nennen eine Kontokurve „je Regel“. Damit bleibt offen, ob nur die acht ungefilterten Indikatorregeln oder auch ihre Kombinationen mit Umfeld und Saison gehandelt werden. Gerade diese Kombinationen gehören zur ursprünglichen Fragestellung.

   **Konkrete Ergänzung:** Vor Öffnung des Prüfzeitraums eine feste Strategieliste aufnehmen, beispielsweise je gerichteter Regel:

   - ungefilterte Regel als Vergleich;
   - vier Varianten für `angespannt/ruhig × Saison unterstützt/gegen`.

   Jede Variante erhält eine eigene Positionsführung mit den bereits definierten Kosten und Haltezeiten. Keine nachträgliche Auswahl der besten Kombination als bestätigtes Ergebnis. Die Kontokurven bleiben beschreibend; ein signifikanter Zusatznutzen gegenüber Kontrollen beweist noch keine positive Nettorendite der Handelsregel.

**Schluss: TRAGFÄHIG MIT ÄNDERUNGEN.** Die Studienarchitektur trägt; die bisherigen Hauptbefunde sind geschlossen. Nach diesen Ergänzungen kann der Studienkern gebaut und anhand der Besetzungsinventur entschieden werden, welche Hypothesen überhaupt auswertbar sind. Arm A untersucht weiterhin das Volatilitätsumfeld; eine Gamma-Bestätigung lässt sich daraus nicht ableiten.

Ich habe keine Dateien verändert und keine Datenläufe ausgeführt.
