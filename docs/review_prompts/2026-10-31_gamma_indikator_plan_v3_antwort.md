**Schluss: TRAGFÄHIG MIT ÄNDERUNGEN.** v3 übernimmt die wesentlichen Entscheidungen aus v2. Die acht Punkte sind aber noch nicht vollständig operationalisiert. Vor dem Studiencode müssen vor allem die Jahresgewichtung, fehlende Jahreszellen und die Bootstrap-Auswertung eindeutig werden.

1. **Die Jahresgewichte können weiterhin einen scheinbaren Umfeld- oder Saisoneffekt erzeugen.**  
   [v3, Zeilen 51–57](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-31_gamma_indikator_plan_v3.md:51) gewichtet jedes `E(r,s)` nach seiner eigenen Signalzahl. Dadurch vergleichen die Kontraste unterschiedliche Jahreszusammensetzungen.

   Gegenbeispiel mit zwei Jahren: Der kontrollbereinigte Effekt beträgt im ersten Jahr in **allen vier Zellen +1 %**, im zweiten überall **+3 %**. Bei 180/20 Signalen über die beiden Jahre erhält „angespannt“ +1,2 %; bei 20/180 erhält „ruhig“ +2,8 %. Ergebnis: **ΔU = −1,6 Prozentpunkte**, obwohl innerhalb keines Jahres ein Umfeldunterschied besteht.

   **Änderung:** Zuerst die Kontraste innerhalb desselben Tickers und Jahres bilden, anschließend mit gemeinsamen Jahresgewichten aggregieren:

   ```text
   ΔU_i,y = ½ · (E_i,y(a,+) + E_i,y(a,−)
                  − E_i,y(q,+) − E_i,y(q,−))

   ΔS_i,y = ½ · (E_i,y(a,+) + E_i,y(q,+)
                  − E_i,y(a,−) − E_i,y(q,−))
   ```

   Beispielsweise gleiche Gewichte über zulässige Jahre je Ticker, danach je ein Drittel über SPY/QQQ/DIA. Die Gewichtsregel gilt unverändert im Prüfzeitraum.

2. **Die Mindestbesetzung löst fehlende Ticker-Jahr-Zellen noch nicht.**  
   [Zeilen 67–71](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-31_gamma_indikator_plan_v3.md:67) verlangen Mindestzahlen über den gesamten Zeitraum. Trotzdem kann in einem einzelnen Kalenderjahr eine benötigte Kontroll- oder Signalzelle fehlen. Dann ist bereits der jährliche Effekt undefiniert.

   **Änderung:** Eine gemeinsame Jahresmenge je Regel und Ticker festlegen, in der alle vier benötigten Signal- und Kontrollmittel bestimmbar sind. Dieselbe Jahresmenge muss sämtliche Komponenten beider Kontraste tragen. Ausgeschlossene Jahre und Gründe ausweisen; weder fehlende Effekte durch null ersetzen noch die übrigen Zellen getrennt umgewichten.

   Vor der Renditeauswertung eine **Besetzungsinventur** erstellen: gültige Saisonjahre, Signalzahlen, Kontrollzahlen und Episoden je benötigter Zelle. Die Kombination aus zehn vollständigen Saisonvorjahren, Entdeckungsende 2018 und seltenen Stresssignalen könnte den Kern stark verkleinern. Falls die Voraussetzungen nicht reichen, lautet das Ergebnis „nicht auswertbar“; Schwellen dürfen anschließend nicht ergebnisabhängig gelockert werden.

3. **Leere Bootstrap-Zellen müssen den p-Wert erhöhen.**  
   „Als extrem … konservativ hinzugenommen“ in [Zeilen 70–71](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-31_gamma_indikator_plan_v3.md:70) ist missverständlich. Ein Eintrag von null in die Verteilung wäre gerade **nicht** konservativ.

   **Änderung:** Für jede Hypothese ausdrücklich festlegen:

   ```text
   p = (1 + Anzahl gültiger Überschreitungen
          + Anzahl ungültiger Ziehungen) / (1 + B)
   ```

   Ungültig ist eine Ziehung, sobald ein für den festgelegten Schätzer benötigtes Mittel nicht bestimmbar ist – einschließlich der Jahreszellen aus Punkt 2. Nicht verwerfen, nicht nachziehen, nicht umgewichten. Bei mehr als 5 % ungültigen Ziehungen: nicht auswertbar, für Holm `p = 1`.

   Die bereits genannten nullzentrierten Überschreitungsbedingungen können für gültige Ziehungen bestehen bleiben.

4. **Bootstrap-Verfahren und Feinziehung brauchen noch einen ausführbaren Vertrag.**  
   [Zeilen 63–66](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-31_gamma_indikator_plan_v3.md:63) lassen offen, was genau neu gezogen wird.

   **Änderung:**

   - Signale, Saisonklassen und vollständig beobachtete Zielrenditen auf der ursprünglichen Sitzungsachse berechnen; anschließend gemeinsame Datumsblöcke dieser Beobachtungen ziehen. Indikatoren und Forward-Renditen nicht über künstliche Blockübergänge neu berechnen.
   - Ursprüngliche Ticker-, Jahres- und Zellzuordnung erhalten; Kontrollmittel und Kontraste aus den gezogenen Beobachtungen neu bestimmen.
   - Einen konkreten Seed nennen.
   - Am einfachsten direkt **100 000 gemeinsame Ziehungen für alle 16 Hypothesen** verwenden. Damit entfällt die unklare Auswahl über einen „Holm-Grenzbereich ±50 %“ einschließlich wechselnder Rangplätze.
   - Blocklänge 40 bleibt entscheidend; 20/60 werden als Sensitivität berichtet und dürfen kein negatives Hauptergebnis ersetzen.

   Der stationäre Bootstrap setzt geeignete Stationaritäts- und Abhängigkeitsbedingungen voraus; gemeinsame Ziehungen allein sichern seine Gültigkeit nicht. Deshalb vorab synthetische Nullfälle mit zeitlicher Abhängigkeit und wechselnden Jahresniveaus prüfen. Grundlage: [Politis und Romano, *The Stationary Bootstrap*](https://doi.org/10.1080/01621459.1994.10476870).

5. **Die Saisonverkettung ist jetzt richtig definiert.**  
   [Zeilen 35–40](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-31_gamma_indikator_plan_v3.md:35) vermeiden sowohl den künstlichen Jahreswechselverlust als auch die Verwendung des laufenden Jahres.

   Weil beide Kurven dieselben historischen Jahre, dieselbe Normierung und dieselbe 365er-Achse verwenden, sind ihre Werte hier identisch. Das kann als **eine am Signalzeitpunkt eingefrorene Kurve** implementiert werden.

   **Verbindlicher Handfall:** Kurve am Signal = 108, Jahresende = 110, Januarziel = 102:

   ```text
   (110 / 108) × (102 / 100) − 1 = +3,8889 %
   ```

   Zusätzlich müssen Änderungen an Daten ab Jahr J die Saisonklasse eines Signals aus J unverändert lassen.

   **Konkrete Integrationsfalle:** Der vorhandene [Python-Kern](C:/dev/SeasonalEdge/shared/true_seasonal.py:46) verlangt bei einem Fenster von 20 standardmäßig **16** gültige Jahre. Die Studie muss ihre abweichende Mindestzahl ausdrücklich mit `min_jahre=10` übergeben.

6. **LBR-Gleichheitsfall und Renditemaß bleiben mehrdeutig.**  
   Die LBR-Formel in [Zeilen 27–29](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-31_gamma_indikator_plan_v3.md:27) erkennt bei der Folge `−1, 0, +1` keine Kreuzung. Der Satz „erst beim strikten Vorzeichenwechsel“ kann dagegen als Vergleich mit dem letzten von null verschiedenen Vorzeichen gelesen werden.

   **Änderung:** Die vorhandene Nachbarregel ausdrücklich bestätigen: `−1,0,+1` erzeugt **kein** Signal. Alternativ den Vergleich mit dem letzten Nichtnullwert definieren; dann aber Formel und Zustandslogik ändern.

   Außerdem ausdrücklich festhalten:

   - RSI verwendet Differenzen der aus `log_return` rekonstruierten **Kursstände**, falls der klassische Wilder-RSI gemeint ist.
   - Der primäre Test verwendet entweder gerichtete Logrenditen oder gerichtete einfache Renditen. „Rendite“ allein reicht nicht; die Williams-Vorlage verwendet Logrenditen.
   - Fehlende oder unplausible OHLC-Verhältnisse machen `%R` unbekannt.

7. **Die Kontokurve braucht eine eigene Short-P&L-Definition.**  
   [Zeilen 84–90](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-31_gamma_indikator_plan_v3.md:84) regeln Einstieg und Ausstieg ausreichend. Offen bleibt die Umrechnung des Renditemaßes in tatsächliches Positionskapital.

   **Änderung:** Stückzahl beim Einstieg festsetzen, während der Haltedauer halten und Gewinn/Verlust aus der tatsächlichen Position berechnen. Negierte Logrenditen dürfen nicht einfach exponentiert und als Short-Kapitalrendite verwendet werden: Bei einem Kursanstieg um 10 % verliert ein Short mit gleichem Anfangsnominal 10 %, nicht 9,09 %.

   Zusätzlich definieren, was bei fehlendem Einstiegs-Open, fehlender Bewertung oder fehlendem Ausstiegskurs geschieht. Solche Fälle dürfen weder still verschwinden noch als unverändertes Kapital fortgeschrieben werden.

8. **Arm B ist angemessen begrenzt; eine Klarstellung fehlt.**  
   Ausschluss des nicht rekonstruierbaren Altbestands, beschreibende Auswertung und getrennte prospektive Speicherung sind sinnvoll.

   **Änderung:** Festhalten, dass `net_gex_usd_bn == 0.0` bewusst ausgeschlossen bleibt, **auch wenn** das archivierte Regime ein Vorzeichen trägt. Das ist eine konservative Studienentscheidung; ein gerundeter Nullwert beweist keinen tatsächlichen Nullzustand.

   Für das neue Protokoll Rohwert, echten Nullzustand, Session, tatsächliche Abrufzeit und Methodenversion gemeinsam speichern. Die Serverinventur konnte ich hier nicht unabhängig bestätigen; ihre Belege gehören weiterhin zum eingefrorenen Inventar.

**Schluss: TRAGFÄHIG MIT ÄNDERUNGEN.** Die Studienarchitektur und die Saisonverkettung tragen. Vor dem Studiencode müssen gemeinsame Jahresgewichte, fehlende Jahreszellen, Bootstrap-Auswertung und Rendite-/Kapitalkonvention geschlossen werden. Danach kann die Besetzungsinventur zeigen, ob die geplanten 16 Hypothesen tatsächlich auswertbar sind. Ein bestätigter Effekt aus Arm A wäre weiterhin eine Aussage über das Volatilitätsumfeld, keine Gamma-Bestätigung.

Ich habe keine Dateien verändert.
