Der Plan ist sinnvoll, aber noch nicht freigabefähig. Wesentliche Lücken sind die Definition vollständiger Jahre, die Fensterlogik und die Trennung zwischen Modelljahren und angezeigtem Ist-Jahr.

1. **Kennzahl: als beschreibender Vergleich brauchbar.** Pearson auf zwölf Werten misst die Ähnlichkeit des Monatsmusters, keine Vorhersagegüte der Renditehöhe. Einzelne starke Monate können das Ergebnis prägen. Ich würde Pearson behalten, ausdrücklich als „Ähnlichkeit der zwölf Monatsänderungen“, ohne Signifikanzbehauptung.

   Vorzeichentreffer sind anschaulicher, brauchen aber einen Vergleich mit „immer positiv“: Sonst kann schon die überwiegend positive Marktrichtung als Erfolg erscheinen. Nullrenditen müssen ausdrücklich behandelt werden; die Probe zählt derzeit auch `0 == 0` als Treffer ([Probe:54](C:/dev/SeasonalEdge/scripts/research/true_seasonal_probe.py:54)). Für Ø r und positive Jahre jeweils die Anzahl **gültiger Korrelationen** verwenden; konstante Reihen separat als nicht auswertbar zählen.

   **Die geplanten „Monatsrenditen“ sind außerdem keine exakten Kalendermonatsrenditen.** In Schaltjahren bezeichnet Slot 59 den 28. Februar und Slot 90 den 30. März. Die bestehende Interpolation verschiebt die übrigen Tage nicht, sondern faltet nur Tag 366 ([calculations.py:111](C:/dev/SeasonalEdge/shared/calculations.py:111)). Interpolation über einen Monatswechsel kann zudem spätere Kurse einbeziehen. Empfehlung: Für den Rückblick tatsächliche Monatsend-Beobachtungen verwenden und die Januar-Referenz ausdrücklich definieren. Andernfalls „Änderungen zwischen festen Saisonachsenpunkten“ schreiben.

2. **`year_covers` allein reicht für „keine Teiljahre“ nicht.** Die Funktion prüft vergangenes Jahr und letzte Beobachtung ab Tag 359. IPO-Anfang und innere Lücken bleiben ausdrücklich ungeprüft ([calculations.py:189](C:/dev/SeasonalEdge/shared/calculations.py:189)). `true_seasonal.py` übernimmt genau diese Regel, verspricht im Kommentar aber den Ausschluss von Teiljahren ([true_seasonal.py:10](C:/dev/SeasonalEdge/shared/true_seasonal.py:10)).

   Im echten JavaScript nachgerechnet:

   - Ein Jahr mit ausschließlich 20 Zeilen vom 12.–31. Dezember wird akzeptiert.
   - Ein Jahr mit einer Januarzeile und 19 Dezemberzeilen wird ebenfalls akzeptiert; dazwischen entstehen interpolierte Saisonwerte.

   Der Plan braucht daher eine zusätzliche Abdeckungsregel für Jahresanfang und Datenlücken. Die vorhandenen Builder liefern dafür noch unterschiedliche Metadaten ([seasonal-compute.js:368](C:/dev/SeasonalEdge/landing/js/seasonal-compute.js:368), [Jahreszyklus:579](C:/dev/SeasonalEdge/landing/pages/jahreszyklus.html:579)).

   **Der Durchschnitt-Modus darf wie entschieden unverändert bleiben**, einschließlich IPO-Teiljahr und fortgeschriebenem laufendem Jahr. Seine Beschriftung sollte diese Zusammensetzung erklären.

3. **Für den Hauptvergleich dasselbe Fenster verwenden; alle Vorjahre optional ergänzen.** Sonst ändern sich gleichzeitig Zukunftswissen und Historienlänge.

   Allerdings widerspricht die geplante Vergleichskurve dem Produktionscode: `minYear = aktuellesJahr − N` ergibt **N Vorjahre plus Zieljahr**, bei N=10 also bis zu elf Jahreskurven ([Jahreszyklus:1759](C:/dev/SeasonalEdge/landing/pages/jahreszyklus.html:1759)). Der Plan definiert dagegen `Y−N+1…Y`, also zehn. Die Probe verwendet für `in_10` ebenfalls diese zehn Jahre ([Probe:113](C:/dev/SeasonalEdge/scripts/research/true_seasonal_probe.py:113)). Die Messung darf daher nicht als exakte Nachbildung des heutigen Seitenfensters bezeichnet werden.

   Vor Umsetzung festlegen:

   - Kalenderjahrfenster oder letzte N gültige Beobachtungsjahre? `vorjahre(..., max_jahre=N)` verwendet Letzteres und greift bei Lücken weiter zurück ([true_seasonal.py:25](C:/dev/SeasonalEdge/shared/true_seasonal.py:25)).
   - „Mindestens zehn Vorjahre vorhanden“ getrennt von „N Jahre tatsächlich verwendet“ behandeln, damit die vorhandene Fünfjahresoption sinnvoll funktioniert.
   - Bei `max` ausschließlich Jahre bis Y zulassen. Die Probe `in_alle` mittelt derzeit auch Jahre **nach Y** ([Probe:112](C:/dev/SeasonalEdge/scripts/research/true_seasonal_probe.py:112)).

4. **Ja, mehrere Abhängigkeiten fehlen oder brauchen eine ausdrückliche Entscheidung.**

   - **Ist-Jahr separat übergeben:** Wenn `renderMain` nur die True-Seasonal-Jahre erhält, verschwindet die goldene aktuelle Kurve, weil sie aus demselben `yearData` gelesen wird ([Jahreszyklus:1047](C:/dev/SeasonalEdge/landing/pages/jahreszyklus.html:1047)).
   - **Zyklus-Overlays:** Sie werden ebenfalls aus `yearData` berechnet. Im True-Modus sollten sie dieselbe zulässige historische Jahresmenge verwenden ([Jahreszyklus:1021](C:/dev/SeasonalEdge/landing/pages/jahreszyklus.html:1021)).
   - **Perzentile, Datenzählung, Detrend und Legenden:** Modelljahre konsistent durchreichen. Die tatsächliche tägliche Perzentil-Fallzahl darf wegen des bestehenden Beobachtungsfilters weiterhin variieren ([Jahreszyklus:939](C:/dev/SeasonalEdge/landing/pages/jahreszyklus.html:939)).
   - **Einzeljahre:** Historische Linien aus der Modellmenge; aktuelles Jahr separat erhalten ([Jahreszyklus:1277](C:/dev/SeasonalEdge/landing/pages/jahreszyklus.html:1277)).
   - **Pressure:** Schließt das laufende Jahr bereits aus, prüft aber keine vollständige Jahresabdeckung und verwendet eigene Lookbacks. Entweder zulässige Jahre entsprechend filtern oder ausdrücklich als unabhängige Berechnung kennzeichnen ([Jahreszyklus:626](C:/dev/SeasonalEdge/landing/pages/jahreszyklus.html:626)).
   - **Ausreißerfilter:** True-Seasonal-Jahre **vor** der IQR-Berechnung auswählen. Aktuell wird zunächst über alle Jahre gefiltert; dadurch kann das Zieljahr mittelbar beeinflussen, welche Vorjahre übrig bleiben ([Jahreszyklus:1726](C:/dev/SeasonalEdge/landing/pages/jahreszyklus.html:1726)). Im Rückblick keine über die Gesamthistorie bestimmten Filter verwenden.
   - **Embed:** Überträgt bislang nur Ticker, Zeitraum und Sprache; `/embed` berechnet immer den Durchschnitt. Modusparameter und identische Jahresauswahl ergänzen ([Jahreszyklus:1898](C:/dev/SeasonalEdge/landing/pages/jahreszyklus.html:1898), [embed.html:98](C:/dev/SeasonalEdge/landing/embed.html:98)).
   - **Präferenz:** Ja, seitenbezogen speichern; fehlender oder ungültiger Wert bleibt `durchschnitt`. `SA.prefs` unterstützt bisher nur Ticker und Zeitraum ([app.js:545](C:/dev/SeasonalEdge/landing/js/app.js:545)).

   **Ladezustand:** Für den Rückblick eine eigene Anfragekennung verwenden, gebunden an den aktuellen Seiten-/Tickerstand. Ein zusätzliches `SA.ladeKennung.start()` würde laufende Hauptchart-Rückrufe entwerten ([app.js:736](C:/dev/SeasonalEdge/landing/js/app.js:736)). Rohdaten pro Ticker teilen, Ergebnisse bei Fensterwechsel neu berechnen. Fehler müssen wiederholbar bleiben. Dauerhaft „genau einmal“ widerspricht der 15-Minuten-Frische des gemeinsamen Laders ([kurse.js:35](C:/dev/SeasonalEdge/landing/js/kurse.js:35)).

5. **Ja, gezielt markieren; historische Häufigkeiten nicht pauschal als Zukunftswissen einstufen.** „In X von Y Jahren positiv“ ist zunächst eine gültige rückblickende Beschreibung. Problematisch wird die Übertragung auf künftige Trefferwahrscheinlichkeiten oder eine nachträglich ausgewählte Erfolgsperiode.

   Zwei konkrete Prüfstellen:

   - **Midterm-Erholung:** Der Einstieg wird am nachträglich bestimmten Jahrestief angesetzt; anschließend werden 14/14 positive Fälle hervorgehoben. Das Tief war am Einstiegstag nicht als Jahrestief bekannt ([Artikel:62](C:/dev/SeasonalEdge/blog/posts/2026-09-02_zwischenwahljahr-2026-erholung-praesidentenzyklus.md:62)).
   - **Google-Juli:** Der stärkste von zwölf Monaten wird anhand derselben Historie ausgewählt und mit 14/15 positiven Jahren beworben. Das ist eine rückblickende Auswahl, keine unabhängig bestätigte Trefferquote ([Artikel:22](C:/dev/SeasonalEdge/blog/posts/2026-06-14_google-juli-saisonalitaet.md:22)).

Für die Abnahme den geplanten Wächter um IPO-Anfang, innere Lücke, Kalenderjahrlücke, exakte Fenstergrenzen, Schaltjahr-Monatsenden, konstante Reihen und Zieljahr-Unabhängigkeit **mit aktiviertem Ausreißerfilter** erweitern. Die Seitenprobe muss zusätzlich nachweisenisen, dass das Ist-Jahr sichtbar bleibt, Embed denselben Modus verwendet und Rückblickladen den Hauptabruf nicht entwertet. Das vorhandene Muster prüft bereits echte Seitenfunktionen gegen fachliche Sollwerte ([Wächter:601](C:/dev/SeasonalEdge/scripts/verify_seasonal_twins.py:601)).

Nur gelesen; ergänzende JavaScript-Proben liefen im Speicher. Die Produktionsmesswerte wurden mangels Serverdaten nicht neu berechnet.

**FREIGABE (Plan): nein**
