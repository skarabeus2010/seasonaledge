**Schluss: TRAGFÄHIG MIT ÄNDERUNGEN.** v2 übernimmt die wesentlichen Korrekturen aus v1. Die Trennung von Volatilitätsumfeld und GEX, der spätere Einstieg und der kleinere konfirmatorische Kern sind sinnvoll. Vor dem Bau fehlen aber noch eindeutige Definitionen für die Haupttests, einige Rechenregeln und die Behandlung nicht auswertbarer Daten.

1. **Die formulierte Umfelddifferenz ist noch keine Indikator-Interaktion.**  
   [v2, Zeilen 36–39](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-31_gamma_indikator_plan_v2.md:36) vergleicht die Rendite derselben Regel zwischen angespanntem und ruhigem Umfeld. Diese Differenz kann bereits durch unterschiedliche allgemeine Marktrenditen entstehen.

   **Änderung:** Zuerst den bedingten Indikatoreffekt definieren:

   `E(r,s) = mittlere gerichtete Signalrendite − mittlere gerichtete Kontrollrendite`

   Dabei stammen Signal und Kontrolle aus demselben Ticker, Zeitabschnitt, Umfeld `r` und derselben Saisonklasse `s`. Ob Kontrolltage alle zulässigen Tage oder ausschließlich Tage ohne Signal umfassen, muss ebenfalls feststehen.

   Der Umfeld-Zusatznutzen ist anschließend die Differenz dieser **kontrollbereinigten Effekte** zwischen angespannt und ruhig. Zeitabschnitte und Gewichte vorab festlegen; beide Umfelder müssen mit derselben Zusammensetzung verglichen werden.

2. **16 Hypothesen sind sinnvoll – sofern die Saisonfrage genau einen Kontrast erhält.**  
   „Innerhalb desselben Umfelds“ kann zwei getrennte Saisontests bedeuten. Dann ergeben sich je Regel ein Umfeldtest und zwei Saisontests, insgesamt **24 statt 16 Hypothesen**.

   **Mein Vorschlag für weiterhin 16:** Pro Regel genau zwei Tests:
   
   - Umfeldunterschied des kontrollbereinigten Indikatoreffekts, mit festen Gewichten über die Saisonklassen.
   - Saisonunterschied dieses Effekts, mit festen Gewichten über die beiden Umfelder.

   Die umfeldspezifischen Saisonergebnisse bleiben beschreibend. Ein signifikanter gemittelter Saisoneffekt bestätigt keinen Effekt in jedem einzelnen Umfeld.

   Zusätzlich die Handelsrichtungen festschreiben, beispielsweise RSI/%R niedrig → Long, hoch → Short; LBR-Kreuzung aufwärts → Long, abwärts → Short. Bei Shorts bedeutet saisonale Unterstützung eine fallende Saisonkurve. Ein zweiseitig signifikanter Unterschied zeigt zunächst eine Abhängigkeit; „Verbesserung“ verlangt die vorab erwartete Richtung.

3. **Bootstrap und Auswertbarkeit brauchen einen vollständigen Vertrag.**  
   Gemeinsame Datumsziehungen, Blocklänge 40 und Holm sind passende Bausteine. „p aus Bootstrap“ definiert jedoch noch keinen Test.

   **Änderung:** Den zweiseitigen Test ausdrücklich festlegen, beispielsweise entsprechend der Williams-Vorlage anhand der nullzentrierten Abweichung `T* − T`. Außerdem einfrieren:
   
   - Anzahl der Ziehungen, Seed und gegebenenfalls vorab geregelte Feinziehung;
   - Mindestbesetzung aller benötigten Signal- und Kontrollzellen;
   - Umgang mit Bootstrap-Ziehungen, in denen eine Zelle leer bleibt;
   - Bestätigungskriterium im historischen Prüfzeitraum einschließlich Richtung und Holm-Korrektur.

   Eine nicht auswertbare Hypothese bleibt Bestandteil der 16er-Familie und kann nicht verworfen werden. Fehlende Ticker dürfen nicht still die gleichen Gewichte in andere Gewichte verwandeln.

   „Unabhängige Episoden“ würde ich durch **zeitlich getrennte Episoden nach festgelegter Zusammenfassungsregel** ersetzen. Zeitlicher Abstand allein belegt keine Unabhängigkeit.

4. **Indikator- und Saisondefinitionen sind noch nicht vollständig eingefroren.**  
   [Zeilen 28–35](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-31_gamma_indikator_plan_v2.md:28) nennen wichtige Entscheidungen, lassen andere offen:

   - LBR: SMA oder EMA für jede Linie, Initialisierung, Warm-up und Gleichheitsfall beim Kreuzen.
   - RSI: flache Reihe ausdrücklich vor „keine Verluste“ behandeln; sonst widersprechen sich die Nullfallregeln.
   - Datenlücken: Mindestzahl zusammenhängender Sitzungen bis zur erneuten Gültigkeit.
   - Kursbasis: konsistente OHLC-Basis, besonders für `%R`; keine Indikatorsprünge durch Basiswechsel.

   Bei der Saison würde ich **das feste Kalenderfenster der letzten 20 Vorjahre mit mindestens zehn gültigen Jahren** wählen. Das ist etwas anderes als die letzten 20 verfügbaren vollständigen Jahre.

   Der Jahreswechsel braucht eine Verkettung über den Jahresendwert und den Jahresanfang bei 100. Ein direkter Quotient „Januarwert/Dezemberwert“ würde den jährlichen Neustart der Kurve als Kursbewegung behandeln. Schalttagabbildung und Saisonänderung exakt null müssen ebenfalls feststehen. Die Vollständigkeitsprüfung des bestehenden True-Seasonal-Kerns ist zudem eine dokumentierte Heuristik; das sollte der Plan ausdrücklich übernehmen oder verschärfen.

5. **Prüfzeitraum und Horizonte müssen feste Grenzen bekommen.**  
   „Letzte abgeschlossene Sitzung“ ist als Testende beweglich. Außerdem sind für die jüngsten Signale noch keine vollständigen Forward-Renditen vorhanden.

   **Änderung:** Ein konkretes Datenende samt Export-Hash einfrieren. Pro Horizont nur Ereignisse mit vollständig beobachteter Zielperiode auswerten; offene Ereignisse separat zählen. Kein Halteintervall darf Entdeckungs- und Prüfzeitraum verbinden.

   Vergangene Daten dürfen den Warm-up im Prüfzeitraum speisen. Spätere Daten dürfen keine Eingabe früherer Entdeckungsergebnisse werden. Die Aussagen „reservierter historischer Test“ und spätere prospektive Bestätigung bleiben richtig.

6. **Der GEX-Altbestand lässt sich aus den hier vorhandenen Archiven nicht neu rechnen.**  
   Die lokal vorhandene Altdatei enthält zusammengefasste Kennzahlen, keine Rohketten. Auch die vorhandenen Sessionarchive enthalten gerundetes Netto-GEX. Der Produktionspfad rundet auf drei Nachkommastellen in Milliarden Dollar und setzt das Regime separat anhand des ungerundeten Werts: [snapshot_gex_massive.py](C:/dev/SeasonalEdge/scripts/snapshot_gex_massive.py:465).

   **Änderung für Arm B:** Das archivierte Regime darf als Klassifikation verwendet werden, wenn seine Herleitung aus dem ungerundeten Wert für die jeweilige Methodenversion belegt ist. Aus einem gerundeten Nullwert darf kein Vorzeichen konstruiert werden. Für neue Forschungsprotokolle Rohwert und einen gesonderten Nullzustand speichern.

   **Zur Neubewertung alter Dateien:** Eine begrenzte Inventur lohnt sich. Eine Neuberechnung lohnt sich nur bei tatsächlich vorhandenen kontraktweisen Eingaben einschließlich Strike, Verfall, Typ, OI, IV und belegtem Erhebungszeitpunkt. Die vorhandenen aggregierten Strike- und Laufzeitprofile reichen dafür nicht: Sie verlieren die gemeinsame Zuordnung dieser Größen. Ein neuer Spot allein repariert außerdem weder einen falschen Zeitstempel noch eine unpassende Restlaufzeit.

   Die Serverbestände und die neue Massive-Messung konnte ich hier nicht unabhängig bestätigen; ihre Belege gehören in das eingefrorene Inventar.

7. **Das Handelsmodell braucht noch Ausstieg und Kapitallogik.**  
   [Zeilen 64–72](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-31_gamma_indikator_plan_v2.md:64) regeln den Einstieg, aber noch nicht eindeutig das Ende einer Position.

   **Änderung:** Für die primäre Kontokurve beispielsweise festlegen: Einstieg nächstes zulässiges Open, Ausstieg am Schluss der fünften gehaltenen Sitzung. Andere Horizonte bekommen getrennte beschreibende Kurven. Zusätzlich bestimmen:
   
   - Verhalten bei Gegensignal und Wiederanlage nach dem Ausstieg;
   - Einsatz je Ticker, Behandlung freier Liquidität und Rebalancing;
   - Belastungstest ausdrücklich **10 Bp je Seite** oder insgesamt;
   - MAE und Drawdown aus der tatsächlichen Long-/Short-Position einschließlich Einstiegspunkt.

   Für den DAX „Vortag“ durch „letzter nachweislich verfügbarer US-Wert vor dem Entscheidungszeitpunkt“ ersetzen; Feiertage verhindern eine einfache Verschiebung um einen Kalendertag.

   Den Zusatz „alle Arme“ streichen: Arm B soll laut eigener Definition keine Handelsaussage erhalten. Shorts ohne Leihekosten bleiben beschreibend.

8. **Arm C würde ich für diesen Auftrag weglassen.**  
   Er beantwortet die fehlende historische Positionierungsfrage nicht und bringt ein weiteres Messmodell mit eigener Datenqualität und Variantenwahl hinzu. Falls später ein eigenständiges Interesse an Optionsaktivität besteht, kann er separat untersucht werden. Dann wären unter anderem Kontraktauswahl, Gewichtung und die Gültigkeit der IV-Inversion vorab zu prüfen.

**Schluss:** Die Studienarchitektur ist tragfähig. Die zehn früheren Punkte sind weitgehend aufgenommen, aber noch nicht vollständig operationalisiert. Vor dem Studiencode würde ich die zwei Hauptkontraste, Bootstrap-Regeln, Saisonverkettung und Handelslogik verbindlich ergänzen. Die kleine GEX-Inventur kann bereits erfolgen. Arm A prüft anschließend den Zusatznutzen des Volatilitätsumfelds; eine Gamma-Aussage bleibt Arm B und seiner prospektiven Datensammlung vorbehalten.

Ich habe keine Dateien verändert.
