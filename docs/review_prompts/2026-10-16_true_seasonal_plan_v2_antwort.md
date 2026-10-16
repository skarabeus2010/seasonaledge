**Noch keine Freigabe.** V2 schließt die meisten Lücken aus Runde 1. Zwei fachliche Probleme bleiben: Die Vollständigkeitsregel verwirft reguläre Börsenjahre und akzeptiert abgeschnittene; außerdem entspricht das Mittel der Monatsrenditen nicht der angezeigten Durchschnittskurve.

1. **„Vollständig“: Die vorgeschlagene Regel trägt so nicht.**

   Ein belegtes Gegenbeispiel ist **TSE 2019**: Die Börse war vom 27. April bis 6. Mai geschlossen. Zwischen den angrenzenden Sitzungen 26. April und 7. Mai liegen **elf Kalendertage**. Ein vollständig vorhandenes Jahr würde deshalb ausscheiden. Die Schließung ist [offiziell bei JPX dokumentiert](https://www.jpx.co.jp/english/news/1030/20190115-01.html); die Sonderfeiertage und Brückentage sind bereits im Repository berücksichtigt ([exchange_holidays.py:159](C:/dev/SeasonalEdge/shared/exchange_holidays.py:159), [boersenereignisse.py:395](C:/dev/SeasonalEdge/shared/boersenereignisse.py:395)).

   Umgekehrt akzeptiert die Regel weiterhin fehlende Sitzungen. Im echten JavaScript geprüft: Eine ansonsten regelmäßig besetzte Reihe vom **2. Januar bis 25. Dezember 2025** erfüllt alle drei Bedingungen. Die letzten Sitzungen fehlen trotzdem. `year_covers` bezeichnet seine Grenze ausdrücklich als Toleranzentscheidung ([calculations.py:208](C:/dev/SeasonalEdge/shared/calculations.py:208)). Auch einzelne fehlende Sitzungen im Inneren bleiben unter der Zehntagesgrenze.

   **Erforderliche Änderung:** Abdeckung gegen die erwarteten Sitzungen des jeweiligen Börsenkalenders prüfen, einschließlich Jahresanfang und Jahresende. Die vorhandenen Helfer liefern diese bereits ([sitzungen.py:72](C:/dev/SeasonalEdge/shared/sitzungen.py:72)). Für Kalenderbereiche mit ungeprüfter Abdeckung eine ausdrückliche Behandlung festlegen. Falls vorerst eine Heuristik bleiben soll, muss sie als solche bezeichnet werden; „vollständig“ und „keine Datenlöcher“ wären damit nicht nachgewiesen.

   Den Wächter um **TSE 2019 als zulässigen Fall**, eine fehlende innere Sitzung und ein abgeschnittenes Jahresende ergänzen. Ein pauschaler Test „elf Tage → verwerfen“ würde gerade den Fehler festschreiben.

2. **Januar ohne Jahreswechsel-Return: ja, passend zur bestehenden Normalisierung.**

   Python setzt die erste Jahreszeile auf 100 und kumuliert erst ab dem Return der zweiten Zeile ([calculations.py:106](C:/dev/SeasonalEdge/shared/calculations.py:106)). Beide JS-Builder verwenden dieselbe Referenz ([seasonal-compute.js:340](C:/dev/SeasonalEdge/landing/js/seasonal-compute.js:340), [jahreszyklus.html:562](C:/dev/SeasonalEdge/landing/pages/jahreszyklus.html:562)).

   Damit ist Januar hier die Änderung **vom ersten Januarschluss bis zum letzten Januarschluss**, keine übliche vollständige Januarrendite gegen den Dezemberschluss. Das sollte der Erklärungstext knapp sagen.

   Außerdem sind die vorgeschlagenen Summen **Logrenditen**. Das ist für den beschriebenen Vergleich zulässig, muss aber für Ist und Modell einheitlich gelten. Fehlende oder nicht endliche Returns benötigen dieselbe Rekonstruktion beziehungsweise Verwerfung wie die Normalisierung ([calculations.py:87](C:/dev/SeasonalEdge/shared/calculations.py:87)).

3. **Vergleich (c): sinnvoll als zusätzliche heutige Rückschau, aber derzeit falsch als „genau die angezeigte Kurve“ bezeichnet.**

   Die Seite mittelt **normierte Kursstände** ([jahreszyklus.html:1773](C:/dev/SeasonalEdge/landing/pages/jahreszyklus.html:1773)). V2 mittelt dagegen **monatliche Logrenditen** ([Plan v2:32](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-16_true_seasonal_plan_v2.md:32)). Diese Operationen ergeben unterschiedliche Monatsmuster.

   Mit der echten JS-Mittelwertfunktion nachgerechnet:

   | Zwei synthetische Jahrespfade | Start | Zwischenstand | Endstand |
   |---|---:|---:|---:|
   | A | 100 | 200 | 100 |
   | B | 100 | 50 | 100 |
   | Angezeigter Durchschnitt | 100 | 125 | 100 |

   Die mittleren Logrenditen beider Abschnitte sind jeweils **null**. Die Durchschnittskurve steigt dagegen zunächst und fällt anschließend. Das Problem betrifft auch die Bezeichnung der True-Seasonal-Kennzahl als Bewertung ihrer Hauptkurve.

   Zusätzlich verwendet (c) laut Plan nur vollständige Jahre und keinen Ausreißerfilter. Die sichtbare Durchschnittskurve enthält Teiljahre und kann gefiltert sein ([jahreszyklus.html:1764](C:/dev/SeasonalEdge/landing/pages/jahreszyklus.html:1764)). Die feste 365er-Achse entspricht außerdem in Schaltjahren nicht exakt den Kalendermonatsenden ([calculations.py:114](C:/dev/SeasonalEdge/shared/calculations.py:114)).

   **Meine Empfehlung:** Als Hauptvergleich weiterhin **Y als jüngstes Jahr** verwenden: True Seasonal aus `[Y−N, Y−1]` gegen den rückblickenden Durchschnitt aus `[Y−N, Y]`. Dadurch bleiben Zeitlage und Fenster vergleichbar. Die heutige Kurve kann zusätzlich zeigen, wie gut eine nachträglich bekannte Historie zu vergangenen Jahren passt.

   Für die Kennzahl eine klare Entscheidung treffen:

   - Mittlere Monatslogrenditen beibehalten und als **eigenständigen Monatsmustervergleich** beschriften.
   - Oder tatsächlich Änderungen der berechneten Kurven vergleichen und deren Achsen-, Teiljahres- und Filterkonventionen übernehmen.

4. **Freigabe für den Bau: nach diesen Präzisierungen.**

   Kalenderfenster, separate Übergabe des Ist-Jahres, IQR erst nach Modellwahl, eigene Rückblick-Anfragekennung und die erweiterten Seitenproben adressieren die wesentlichen übrigen Befunde aus Runde 1.

   Zusätzlich festlegen, ob die Mindestmenge auch **nach dem Ausreißerfilter** gelten muss; empfohlen: ja. Sonst könnte eine zunächst ausreichende Modellmenge anschließend unter die zugesagte Mindestzahl fallen.

Nur gelesen; JavaScript-Gegenproben liefen im Speicher. Keine Dateien geändert und keine Produktionsdaten neu berechnet.

**FREIGABE (Plan): nein**
