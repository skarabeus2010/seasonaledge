**Der Schluss „keine belastbare Ausschlussregel gefunden“ trägt. Phase 1 + 2 können als nächster Bauschritt beginnen; die Auswertung braucht jedoch Korrekturen.** Ich habe die Rohdaten unabhängig im Speicher nachgerechnet. Keine Dateien geändert, keine Server- oder DB-Zugriffe.

**1. Auswertung und Simulation**

Die Basisauswahl stimmt für alle **261 rankbaren Datensätze** mit der protokollierten Live-Auswahl überein. Median/MAD sowie die Basiszahlen **1/124** Entwicklungsfälle und **1/125** Prüffälle über 6 MAD sind reproduzierbar.

Folgende Befunde müssen korrigiert werden:

- **`waehle` bildet den Produktionspfad für Ersatzgruppen nicht vollständig ab.** Es fehlen insbesondere der Abstandsschutz von 15 Tagen und die Prüfung erfolgreicher Interpolation. Beide gültigen Legs reichen dafür nicht. [Auswertung:87](C:/dev/SeasonalEdge/scripts/research/skew_trockenlauf_auswertung.py:87), [Produktionspfad:570](C:/dev/SeasonalEdge/scripts/compute_options_skew.py:570). Konkretes Gegenbeispiel: **GS, 05.10.2026**, Regel `N ≥ 2, K ≤ 0,03`. Die Simulation akzeptiert die Gruppe mit **46/74 DTE**; Produktion verwirft sie, weil die nächste Stützstelle 16 Tage von 30 entfernt liegt. Nach Berücksichtigung dieses Schutzes ändern sich in der Prüfmenge die Ergebniszahlen von **78/810 Varianten**. Die im Plan aufgeführten Einzelregeln bleiben dabei unverändert.

- **„Mindestens 59 verlorene unauffällige Tage“ ist falsch.** `D ≤ 0,04` entfernt den Entwicklungsfall über 6 MAD bei **47/123 verlorenen unauffälligen Tagen**; **76/156 Fälle** bleiben rankbar. Die 59 stammen offenbar aus der Sortierung, die zusätzlich das Nettoergebnis über 4 MAD priorisiert. [Plan:31](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-16_skew_ausreisser_plan_v4.md:31), [Sortierung:186](C:/dev/SeasonalEdge/scripts/research/skew_trockenlauf_auswertung.py:186). Auch 47 verlorene Tage rechtfertigen hier keine Ausschlussregel.

- **Der Nenner der H-Kosten stimmt nicht.** Unter den 249 rankbaren Zufallsfällen sind zwei über 6 MAD auffällig. Somit verliert `H ≤ 0,75` **14/247 unauffällige Fälle = 5,7 %**, nicht 14/249 unauffällige Fälle. [Plan:48](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-16_skew_ausreisser_plan_v4.md:48)

- **Datensätze und unterschiedliche Fälle unterscheiden:** Die 337 Datensätze enthalten **334 unterschiedliche Ticker/Datum-Paare**, davon 333 auswertbar. C 29.10.2025 steht identisch zweimal unter `bekannt`; zwei weitere Paare überschneiden Zufallsmenge und Kontrollen. Die Entwicklungs- und Prüfzahlen werden dadurch nicht verändert. Der Lader dedupliziert nicht. [Auswertung:25](C:/dev/SeasonalEdge/scripts/research/skew_trockenlauf_auswertung.py:25)

`merkmale` behandelt die tatsächlich beitragenden Legs sinnvoll: Bei Gewicht null entfällt deren Qualitätsbeitrag; negative Extrapolationsgewichte zählen mit. **`1−w` und `w` gewichten die totale Varianz**, nicht unmittelbar die IV. Die Probe interpoliert entsprechend. [Probe:96](C:/dev/SeasonalEdge/scripts/research/skew_trockenlauf_probe.py:96), [Auswertung:66](C:/dev/SeasonalEdge/scripts/research/skew_trockenlauf_auswertung.py:66)

Die Live-Referenz ist als **deskriptiver historischer Maßstab** brauchbar. Sie macht die Prüfmenge aber nicht vollständig unabhängig: Median/MAD stammen aus dem gesamten Fenster einschließlich der Prüftage. Außerdem habe ich die behauptete Gleichheit mit dem eingefrorenen Stand vom 13.10. mangels dieser Vergleichsdatei nicht bestätigt. Für den vorsichtigen Verzicht auf eine Regel ist das kein Hindernis.

**2. „Markt statt Messfehler“**

**Als Feststellung noch nicht belegt.** Die sechs Fälle liegen überwiegend an unterschiedlichen Tagen; taggleiche Auffälligkeit zeigt die aufgeführte Liste nur für SPY/XLF am 07.04. Klammerung und höheres Volumen schließen gemeinsame Daten- oder Methodenfehler nicht aus. [Plan:27](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-16_skew_ausreisser_plan_v4.md:27)

Tragfähige Formulierung: **„Die Häufung ist mit einer Marktbewegung vereinbar; ein Messfehler ist damit nicht ausgeschlossen.“**

Für eine stärkere Aussage braucht es einen separaten Beleg: dieselben Sessions über alle acht Ticker, einschließlich unauffälliger Vergleichstage, möglichst ergänzt durch eine unabhängige Preisquelle. Ein externer Indexvergleich wäre zusätzliche Evidenz, allein aber kein Nachweis korrekter Einzel-Legs.

**3. Nächster Bauschritt**

**Ja zur gemeinsamen CM-Entscheidung zunächst im Vergleichsbetrieb und zur additiven Herkunft/Markierung**, entsprechend dem Schnitt aus Runde 2. [Vorherige Freigabe:47](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-13_skew_ausreisser_plan_v2_antwort.md:47)

Dabei konkret festhalten:

- Vollständiges Expiry-Universum, bestehende Produktionsprüfungen und Rückfallreihenfolge übernehmen; keine neue H/V/D/N/K-Ausschlussregel.
- Herkunft tatsächlich in Snapshot **und History** persistieren. Für die MAD-Markierung auch Referenzfenster, Fallzahl, Median/MAD und Version reproduzierbar festhalten.
- `auffaellig` bleibt bewertbar. Fehlende Herkunft oder Referenz ausdrücklich kennzeichnen.
- **20 Fälle über 6 MAD sind ein Anlass zur erneuten Untersuchung, keine automatische Validierungsschwelle.** Dafür weiterhin unauffällige Kontrollen sammeln, zusammenhängende Marktphasen berücksichtigen und eine neue, vorab getrennte Prüfmenge verwenden.

Bestandsmigration und „heute nicht bewertbar“ können bis zu einer validierten Ausschlussregel entfallen.

**FREIGABE (Plan): ja**
