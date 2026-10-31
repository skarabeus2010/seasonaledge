**Schluss: TRAGFÄHIG MIT ÄNDERUNGEN.** N3 stellt die bedingte Nullhypothese jetzt nachvollziehbar her; A1 definiert den synthetischen Eingriff eindeutig. Der Kalibrierungsvertrag braucht noch drei konkrete Korrekturen.

1. **Die 2-%-Regel durch eine feste Abnahmeregel ersetzen.**  
   [v6, Zeilen 29–32](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-31_gamma_indikator_plan_v6.md:29): „Holm-Entscheidungen“ kann einzelne Hypothesen oder die gesamte Familie meinen. Zudem können die Holm-Entscheidungen übereinstimmen, während die ebenfalls vorgeschriebenen Verwerfungsraten **vor Holm** unterschiedlich ausfallen.

   **Änderungsvorschlag:**

   > Die ersten 200 Datensätze je Nullszenario und Zeitraum werden zusätzlich mit B = 100 000 ausgewertet. Beide Bootstrapzahlen müssen ihre jeweiligen Akzeptanzgrenzen erfüllen. Verglichen werden je Hypothese Entscheidungen vor und nach Holm sowie je Datensatz das Auftreten mindestens einer falschen Holm-Verwerfung. Abweichungen werden berichtet; sie bestimmen nicht nachträglich das maßgebliche Abnahmekriterium.

   Die kleinere Stichprobe macht die Abnahme strenger: Bei **10 Verwerfungen aus 200 Datensätzen** liegt die einseitige obere 95-%-Clopper-Pearson-Grenze bei **8,33 %**, also über den erlaubten 7 %. Bei **100 aus 2 000** beträgt sie **5,88 %**. Diese Werte habe ich unabhängig nachgerechnet. Falls 200 Wiederholungen deshalb zu wenig sind, die größere Anzahl vorher festlegen. Die Berücksichtigung dieser Monte-Carlo-Unsicherheit entspricht [Morris, White und Crowther](https://doi.org/10.1002/sim.8086).

2. **N1 widerspruchsfrei formulieren.**  
   [v6, Zeilen 7–9](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-31_gamma_indikator_plan_v6.md:7): Aus der allgemeinen Formel folgt bei `f_t ≡ 0` zunächst `z_i,t = √0,1 · e_i,t`, nicht `e_i,t`. Eine wörtliche Implementierung hätte dadurch nur ein Zehntel der vorgesehenen Varianz.

   **Ersetzen durch:**

   > N1 verwendet unabhängig von der Faktorformel direkt `z_i,t = e_i,t` und `r_i,t = √v · e_i,t`. Die Faktorformel gilt ausschließlich für N2/N3.

   N2 ist als gemeinsamer, durch den Marktfaktor getriebener Volatilitätsprozess ausreichend definiert.

3. **Auswertbarkeit und Nenner verbindlich festlegen.**  
   [v6, Zeilen 20–27](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-31_gamma_indikator_plan_v6.md:20): „Für jede auswertbare H_S“ lässt offen, was geschieht, wenn gerade schwache Saisonhypothesen während der Simulation nicht auswertbar werden. Die Sperre für eine *vollständig* nicht auswertbare Familie verhindert diesen Fall nicht.

   **Ergänzen:**

   > Die Besetzungsinventur legt je Zeitraum vorab fest, welche Hypothesen kalibriert werden müssen. Für A1 ist die Erkennungsrate jeder dieser H_S die Zahl der Verwerfungen geteilt durch alle 2 000 Simulationsdatensätze; nicht auswertbare Läufe zählen als Nichterkennung. Gibt es keine kalibrierbare H_S, ist die Leistung des Saisonverfahrens nicht nachgewiesen. Für Nullverwerfungsraten und FWER werden ebenfalls alle geplanten Datensätze als Nenner verwendet; Ausfälle und bedingte Raten unter auswertbaren Läufen werden zusätzlich berichtet.

**Schluss: TRAGFÄHIG MIT ÄNDERUNGEN.** Der Studienkern kann gebaut werden. Vor der verbindlichen Kalibrierung müssen insbesondere die feste Abnahmeregel und die Nenner ergänzt werden. Kontokurve und Strategieliste benötigen aus dieser Runde keine weitere Änderung.

Keine Dateien verändert und keine Datenläufe ausgeführt.
