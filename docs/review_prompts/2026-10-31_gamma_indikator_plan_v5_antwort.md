**Schluss: TRAGFÄHIG MIT ÄNDERUNGEN.** Die Ergänzungen zur Kontokurve und zu den 40 Strategievarianten schließen die entsprechenden Punkte aus v4. Die Kalibrierung braucht noch folgende Präzisierungen.

1. **Die Nullhypothese ist in N3 noch nicht eindeutig hergestellt.**  
   [v5, Zeilen 10–16](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-31_gamma_indikator_plan_v5.md:10): Die echten Signalmasken unabhängig von simulierten Renditeinnovationen zu halten, ist für N1 und einen mittelwertfreien N2 ein sinnvoller Ansatz. Bei N3 kommt jedoch ein zeitabhängiger Erwartungswert hinzu.

   Innerhalb eines Jahres hebt sich ein konstanter Mittelwert im Signal-Kontroll-Vergleich auf. **Zielperioden über den Jahreswechsel können einen anderen Erwartungswert haben.** Liegen Signale häufiger an dieser Grenze als Kontrollen, kann ein Kontrast bei festgehaltenen Jahresmitteln ungleich null sein. Symmetrisch zufällige Jahressprünge können das im Mittel über Simulationen aufheben; das ist eine andere Nullhypothese als die bedingte Null für einen gegebenen Jahresverlauf.

   **Konkrete Änderung:** Für jede simulierte Beobachtung den theoretischen Erwartungswert ihrer vollständigen Forward-Logrendite berechnen und daraus mit den unveränderten Masken und Gewichten die wahren ΔU/ΔS bestimmen. Der Nullfall muss diese Kontraste auf null setzen. Eine einfache Variante ist:
   
   > In N3 werden die Zielrenditen um die Summe der bekannten simulierten Tagesmittel ihrer Zielperiode zentriert. Ein zusätzlicher Handfall mit einem Jahreswechsel prüft die Nullzentrierung.

   Soll N3 ausdrücklich *unbereinigte* Jahresniveauwechsel prüfen, muss dafür ein eigener Generator mit nachgewiesenem Nullkontrast definiert werden.

2. **A1 braucht einen eindeutigen Eingriff und einen eindeutigen Powermaßstab.**  
   [v5, Zeilen 21–23](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-31_gamma_indikator_plan_v5.md:21): Die Erhöhung der gerichteten Signalzielrenditen in beiden unterstützenden Zellen um 20 Bp ergibt tatsächlich **ΔS = +20 Bp und ΔU = 0**, sofern die Ausgangskontraste null sind.

   Offen bleibt, ob dafür die gemeinsamen Tagesrenditen verändert werden oder die bereits berechneten Zielrenditen. Bei überlappenden Ereignissen und mehreren Regeln ist das nicht dasselbe.

   **Konkrete Änderung:**
   
   > A1 verändert ausschließlich die berechneten gerichteten Zielrenditen der unterstützenden Signalbeobachtungen um +0,002; Kontrollen bleiben unverändert. Dies ist ein synthetischer Test des Kontrast- und Bootstrapverfahrens, kein konsistenter handelbarer Kurspfad.

   Außerdem festlegen: Gelten die mindestens 50 % **für jede auswertbare H_S einzeln**? Das wäre meine Empfehlung. Für H_U ist in A1 keine Erkennungsrate zu verlangen, weil dessen wahrer Effekt null bleibt. Nicht auswertbare Hypothesen separat ausweisen; eine vollständig nicht auswertbare Familie darf die Kalibrierung nicht als bestanden melden.

3. **Den Datengenerator reproduzierbar festschreiben.**  
   [v5, Zeilen 7–12](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-31_gamma_indikator_plan_v5.md:7) lassen mehrere Implementierungen zu: Bezieht sich Korrelation 0,9 auf die Innovationen oder die Renditen? Gibt es eine gemeinsame oder drei eigene GARCH-Varianzen? Welche Varianz verwendet N1?

   **Konkrete Änderung:** Beispielsweise gemeinsame GARCH-Varianz mit normalverteilten Innovationen
   `z_i,t = √0,9·f_t + √0,1·e_i,t`, sämtlichen Faktoren unabhängig über die Zeit. Bei 252 Sitzungen pro Jahr:
   `v = 0,16²/252`, `ω = (1−0,08−0,90)·v`, Startvarianz `v`. N1 ebenfalls mit Tagesvarianz `v`. Für N3 zusätzlich Wahrscheinlichkeit, gemeinsame oder tickerspezifische Jahressprünge und deren Umrechnung in tägliche **Logmittelwerte** festlegen.

   Generator, Zielgröße und Leistungskriterien getrennt festzuschreiben entspricht auch dem empfohlenen Simulationsaufbau bei [Morris, White und Crowther](https://doi.org/10.1002/sim.8086).

4. **Die reduzierte Bootstrapzahl auch an den Holm-Schwellen prüfen.**  
   [v5, Zeilen 24–26](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-31_gamma_indikator_plan_v5.md:24): Für Holm über 16 ist die erste Schwelle **0,003125**, nicht 0,05. Mit B = 2 000 ist diese Schwelle grundsätzlich erreichbar, die Auflösung dort aber grob.

   **Konkrete Änderung:** Die günstige Hauptkalibrierung beibehalten, zusätzlich eine vorab festgelegte Teilmenge derselben Simulationsdatensätze mit B = 100 000 rechnen und Unterschiede bei Verwerfungsraten und Holm-Entscheidungen berichten. Die Aussage „Auflösung reicht für α = 0,05“ entsprechend ersetzen.

**Schluss: TRAGFÄHIG MIT ÄNDERUNGEN.** Der Studienkern kann gebaut werden. Vor der verbindlichen Kalibrierung und dem Öffnen des Prüfzeitraums müssen insbesondere N3 und A1 eindeutig definiert sein. Kontokurve und Strategieliste benötigen aus dieser Runde keine weitere Änderung.

Keine Dateien verändert und keine Datenläufe ausgeführt.
