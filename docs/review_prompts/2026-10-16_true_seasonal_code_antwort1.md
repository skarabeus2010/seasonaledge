**Noch keine Code-Freigabe.** Drei relevante Abnahmelücken bleiben:

1. **[P2] „Max“ verwirft auf der Seite weiterhin Jahre vor 1900.**  
   [jahreszyklus.html:1902](C:/dev/SeasonalEdge/landing/pages/jahreszyklus.html:1902) begrenzt auch den True-Modus auf `1900`. Plan v3 verlangt bei `max` sämtliche vollständigen Vorjahre. Embed und Rückblick verwenden dagegen die volle Historie. Gegenprobe mit vollständigen Modelljahren 1897–2025: Seite **126**, gemeinsamer Kern/Embed **129 Jahre**. Für den True-Modus muss die Untergrenze entfallen.

2. **[P2] Embed und Seite verwenden unterschiedliche Modellauswahlen.**  
   [embed.html:109](C:/dev/SeasonalEdge/landing/embed.html:109) berücksichtigt keinen Ausreißerfilter; der erzeugte Link überträgt nur `saison=true` ([jahreszyklus.html:2069](C:/dev/SeasonalEdge/landing/pages/jahreszyklus.html:2069)). Gegenprobe mit zehn vollständigen Vorjahren und einem Ausreißer: Seite mit IQR **9 Jahre, Endwert 100**, Embed **10 Jahre, Endwert 110**.  
   Auch der Rückfall unterscheidet sich: Die Seite zeigt bei unterschrittener Mindestmenge ausdrücklich den Durchschnitt; der Embed-Link bleibt auf True gestellt und liefert einen Datenfehler. Auswahl und Rückfall müssen beim Einbetten konsistent behandelt werden.

3. **[P2] Die Kennzahl besitzt keinen ausreichenden unabhängigen Sollwerttest.**  
   [verify_seasonal_twins.py:882](C:/dev/SeasonalEdge/scripts/verify_seasonal_twins.py:882) prüft konstante und identische Kurven; die übrigen Kennzahlprüfungen vergleichen hauptsächlich die Zwillinge. Ich habe ausschließlich im Speicher **in beiden Implementierungen die ersten elf Monatsgrenzen um einen Tag vorgezogen**: Block 8 blieb vollständig grün. Damit sind die zugesagten Monatsgrenzen einschließlich Schaltjahrkonvention nicht unabhängig abgesichert. Benötigt wird ein analytischer Fall mit bekannten zwölf Änderungen und daraus unabhängig berechneten Kennzahlen.

Zusätzlich fehlt die in v2 vereinbarte, durch v3 beibehaltene **sichtbare Beschriftung der Pressure-Rechnung als unabhängig vom Modus**. [jahreszyklus.html:1298](C:/dev/SeasonalEdge/landing/pages/jahreszyklus.html:1298) nennt lediglich die Lookback-Perioden; die Unabhängigkeit steht nur im Codekommentar.

Zu den Prüffragen:

1. **Kern und Builder:** Die geprüften Python-/JS-/Seitenfälle stimmen überein. Return-Rekonstruktion und Jahresverwerfung sind angeglichen. Heuristik, Teiljahre, 11-/15-Tage-Lücken, Kalenderfenster ohne Ersatz, Zieljahr-Unabhängigkeit mit IQR und Mindestmenge nach Filter werden geprüft. Der vollständige Nachweis scheitert aber an den oben genannten Produktions- und Kennzahltestlücken.

2. **Seite:** Im direkten Vergleich gegen `HEAD` waren im normalen Durchschnittsfall sämtliche aufgezeichneten Chartserien unverändert. Die geänderte Behandlung beschädigter Returns entspricht der Planauflage. Für `_rb.gen`, `rowsTicker`, `laedt`, verspätete Antworten und Fehlerwiederholung fand ich keinen Fehler; die entsprechenden Seitenproben bestehen. Der sichtbare Rückfall auf Durchschnitt ist im Seitencode korrekt umgesetzt.

3. **Embed und Texte:** Embed-Gleichheit ist nicht erfüllt. Die neuen DE-/EN-Texte enthalten keinen Prognoseanspruch und nennen ungeglättete Kurven sowie den vorsorglichen Ausschluss langer Börsenschließungen. „Jahresende ab 28.12.“ sollte präziser „ab Kalendertag 362“ heißen: Im Schaltjahr ist das der 27.12.

Validierung: **34 Seitenprüfungen bestanden**, Block 8 bestanden, `git diff --check` unauffällig. Die JSON-Übergabe des Rechenwächters und zusätzliche Gegenproben liefen im Speicher. Den dateischreibenden Mutationstest habe ich nicht ausgeführt. Keine Dateien geändert.

**FREIGABE (Code): nein**
