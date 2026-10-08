# Codex-Antwort: Plan /plain-vanilla, Runde 1


codex
**Der Plan deckt alle 17 Befunde ab, ist aber noch nicht freigabefähig.** Die folgenden Einwände betreffen den geplanten Lösungsweg, keine neu implementierte Änderung. Ich habe den Bericht und die relevanten Repository-Stellen gelesen; keine Dateien geändert und keine neuen Kennzahlen berechnet.

1. **Hoch — Grundsätze / Phase 1: Ein Phasenvergleich erlaubt keine eindeutige Ursachen-Zuordnung.**  
   Offenerkennung, LBR-Timing, Santa, Rundung und Drawdown können dieselben Ergebnisse verändern. Zwei unabhängig geladene Kursstände vermischen zudem Codeänderungen mit Datenänderungen; dieselben Ausgabedateien würden spätere Phasen überschreiben.  
   **Änderung:** Pro Phase einen unveränderlichen Kurs-Snapshot für Vorher und Nachher verwenden, einschließlich Datenhash, Stichtag, Codeversion, Zeitraum und Parametern. Ergebnisse je Phase archivieren. Innerhalb Phase 1 nach jeder fachlichen Korrektur einen Zwischenvergleich speichern, einschließlich geänderter Einzeltrades und Befundnummer. Stop-aus-, Fixed-Stop- und Trailing-Konfigurationen ausdrücklich abdecken. Dann ist die Phase nachvollziehbar geschnitten.

2. **Hoch — Phase 1.1: `-1` unterscheidet Zukunft und Datenfehler nicht ausreichend.**  
   `_makeTrade` deutet einen negativen Exitindex als offenen Trade. Ein historisch fehlender Exit darf denselben Pfad nicht nehmen. Außerdem ist ein Kalenderziel nach der letzten Zeile nicht automatisch ein zukünftiger *Handelstermin*: Endet ein Monat am Sonntag, kann der Freitag bereits der abgeschlossene letzte Handelstag sein. Umgekehrt verschiebt eine fehlende Monatsanfangszeile sämtliche aus Zeilen gezählten TDOM-Termine.  
   **Änderung:** Zielauflösung mit getrennten Zuständen planen: gefunden, noch nicht fällig, historische Daten fehlen, Kalenderabdeckung unbekannt. Erst den regelgemäßen Handelstermin bestimmen, dann seine Kursabdeckung prüfen. Alle direkten Datumssuchen und Strategiezweige erfassen, nicht nur die drei Monatshilfen. Insbesondere muss LBR einen erfolgten Einstieg ohne bereits beobachteten Ausstieg erhalten; derzeit verwerfen entsprechende Zweige den Trade. Auch ein Einstieg auf der letzten Kurszeile muss als offene Position darstellbar sein.

3. **Hoch — Phase 1.1: Die Grenze „> 5 Kalendertage“ ist kein belastbarer Lückennachweis.**  
   Schon ein einzelner fehlender Handelstag kann den dritten TDOM oder einen Stop verändern. Eine längere kalenderbedingte Handelspause beweist dagegen keinen Datenfehler. Der vorhandene Kalender schließt in [holidays.js:248](C:/dev/Seasonaledge/landing/js/holidays.js:248) Samstage pauschal aus; für die angesprochenen historischen Samstagssitzungen reicht er damit nicht.  
   **Änderung:** Erwartete Sitzungen gegen vorhandene Kurse prüfen, mit Börse und historischer Kalenderabdeckung. Historische Samstagszeilen nicht durch einen modernen Kalender entfernen. Für `^GDAXI` den passenden deutschen Börsenkalender verwenden. Ohne belastbare historische Kalenderabdeckung die Unsicherheit ausweisen; fünf Tage allenfalls als Warnschwelle verwenden. Fehlende Kurse innerhalb einer Haltedauer ebenfalls behandeln, weil Stops und täglicher Drawdown davon abhängen.

4. **Mittel — Phase 1.3: Santa ist definiert; die Mittwoch-Sonderregel ist unnötig fragil.**  
   Die Registry sagt ausdrücklich **„3 HT vor Thanksgiving → 5. HT Jan“**, die EN-Fassung entsprechend „3 TDs before Thanksgiving“. Siehe [strategy-compute.js:722](C:/dev/Seasonaledge/landing/js/strategy-compute.js:722). „Python angleichen oder umgekehrt“ bleibt deshalb zu unbestimmt.  
   **Änderung:** Verbindlich die dritte Handelssitzung **streng vor** Thanksgiving wählen. Das ergibt im vorhandenen 2024-US-Test den 25.11. Eine Zählung streng vor dem Datum funktioniert auch, wenn Thanksgiving am betrachteten Handelsplatz ein Handelstag ist oder die vorherige Sitzung kein Mittwoch war. Abdeckung separat prüfen; keine Rückrechnung von einem beliebigen letzten verfügbaren Kurs.

5. **Hoch — Phase 1.1 und 1.4: Der Vertrag für täglichen Drawdown widerspricht sich.**  
   „Offene Trades zählen in keine Kennzahl“ kollidiert mit einer täglichen Equity einschließlich offener Positionen. Außerdem fehlen Regeln für Kapitalbindung, Überschneidungen, den vorhandenen Hebelfaktor und die Bewertung nach einem Stop.  
   **Änderung:** Realisierte Handelsstatistik und täglich bewertete Portfolio-Kennzahlen ausdrücklich trennen. Festlegen, ob der tägliche Max-DD auch die am Datenende offene Position umfasst — für eine bis zum Stichtag bewertete Equity sollte er das. Cash, Positionsgröße, Hebel und gleichzeitige Positionen definieren; dieselbe Equity für Chart und täglichen Drawdown verwenden. Abnahmefälle: `100 → 80 → 110`, noch offene Verlustposition und vorzeitiger Stop. Die Python-Regeln einschließlich Offenstatus mitziehen.

6. **Hoch — Phase 1.5 / Phase 3.1–2: Präzision und Zwillingstest sind noch nicht vollständig spezifiziert.**  
   Nur `_makeTrade` zu ändern genügt nicht: Stopfunktionen erzeugen eigene, gerundete Tradeobjekte; gerundete Einstiegspreise beeinflussen auch Stopgrenzen. Außerdem können Close- und OHLC-Ausführung trotz identischer Eingabedaten legitim unterschiedliche Ergebnisse liefern.  
   **Änderung:** Unrunde interne Preise und Renditen für sämtliche Erzeugungs- und Stopwege festlegen. EMA-Seed, Warm-up, MACD-Signal-Start und Verhalten bei ungültigen Werten verbindlich definieren; „SMA-Start“ allein reicht nicht. JS↔Python-Gleichheit nur bei gleichem Ausführungsmodell verlangen: ohne Stops beziehungsweise mit gemeinsamem Close-Modus. OHLC separat anhand der Gap-/Trailing-Fälle prüfen, in **beiden** betroffenen Python-Pfaden.

7. **Hoch — Phase 3.3–4: Der Maskenwechsel betrifft weitere Seiten und braucht eine eindeutige Zeitachse.**  
   `applyFilter` wird auch von Monatswechsel, Mondphasen, Opex, Overnight, TDOM, Vixpiration, Zentralbanken und Wochentagen verwendet. Nur `backtest-engine.html` anzupassen kann dort die Vortagsregel entfernen.  
   **Änderung:** Alle Konsumenten prüfen und gemeinsam umstellen. Festlegen: `mask[t]` beschreibt den nach Schluss von Tag `t` bekannten Zustand; Ausführung an `i` liest `mask[i-1]`. Beim Regime zusätzlich Referenzverteilung, Mindesthistorie und Gleichstandsbehandlung definieren. Ein Test muss beweisen, dass angehängte Zukunftsdaten frühere Zustände nicht verändern und der Konsument genau einen Handelstag Verzögerung verwendet.

8. **Mittel — Phase 2.1–3: Neutrale Farben lösen Befund 16 nur teilweise.**  
   Auch unbedingte zukünftige Termine erscheinen bislang als Handlungsaufforderungen. Bei LBR ist ein konkreter Ausstiegstermin vor dem auslösenden Indikatorzustand nicht bekannt.  
   **Änderung:** Sämtliche zukünftigen Termine neutral als Regeltermine beziehungsweise Suchfenster bezeichnen. Unbekannte, erfüllte und nicht erfüllte Bedingungen unterscheiden. Historische tatsächliche Ein-/Ausstiege dürfen so heißen. Dashboard und Signalansicht müssen dieselben Regeln und Datenstände verwenden; DE und EN gemeinsam abnehmen.

9. **Hoch — Grundsatz „Wächter je Phase“: Die Original-Strategieprobe deckt den geplanten Umfang nicht ab.**  
   Median, Dashboard-Abdeckung, Header, Signaltexte, Newsletter und Python-OHLC liegen außerhalb von `strategy-compute.js`. Ein erfolgreicher Test dieses Kerns weist deren Korrektur nicht nach.  
   **Änderung:** Ein Wächter darf die Phase orchestrieren, muss aber die jeweils echten betroffenen Module und Konsumenten ausführen. Für jeden Befund mindestens eine gezielte fachliche Prüfung samt zugehöriger Mutation festlegen. Bei Constant-Fill sowohl einzelne Tage als auch vollständige Auswertungsintervalle prüfen; unbekannte Abdeckung darf nicht als vollständig gelten.

10. **Mittel — Blog-Grundsatz / Reihenfolge und Abnahme: Die Artikelprüfung braucht eigene Reproduktionen.**  
    Der Monthly-10-Artikel verwendet SPY 1994–2025 und tägliche Risikokennzahlen; der Sell-in-May-Artikel vergleicht November–April mit Mai–Oktober. Das sind nicht automatisch die Ergebnisse des vorgesehenen 22-Strategien-Laufs.  
    **Änderung:** Die veröffentlichten Tabellen mit ihren jeweiligen Regeln, Zeiträumen und Datenbasen gesondert nachrechnen. Abweichungen samt Ursache dem Nutzer vorlegen. Außerdem die Abfolge Messlauf → Codeprüfung → Differenzprüfung → Freigabe ausdrücklich für **jede** Phase festlegen.

FREIGABE: nein
