# Codex-Antwort (Schlussantwort; Rohprotokoll nicht im Repo)

v2 schließt die meisten bisherigen Befunde. Vier Punkte bleiben offen. Ausschließlich gelesen; keine Dateien geändert.

1. **HOCH — Abschnitt 0, C2, D2: Die tickerabhängige Toleranz fehlt im Funktionsvertrag.**  
   **Fall:** `anomalie(rows, {as_of})` und `berechne(rows, {as_of})` erhalten nur Datum und Schlusskurs. Damit können sie nicht erkennen, ob eine zweitägige Unterbrechung bei Krypto ungültig oder bei Börsenkursen zulässig ist. Auch der beschriebene Python-Eingang enthält keinen Ticker.  
   **Änderung:** Ticker oder eine explizite Marktklasse als Pflichtparameter beider Kerne festlegen, einschließlich Zuordnung und Verhalten bei unbekannten Werten. Alle Aufrufer und die D5-Zielberechnung müssen denselben Parameter verwenden. Test: identische Datumsreihe, unterschiedliche Marktklasse → unterschiedliche Fensterzulässigkeit.

2. **HOCH — Abschnitt 0, D1/D2: Der bestehende Jahreskurvenbauer erfüllt den UTC-Vertrag nicht.**  
   **Fall:** [buildYearData](/C:/dev/Seasonaledge/landing/js/seasonal-compute.js:342) verwendet `getFullYear()` und einen lokalen Jahresbeginn. Ein rein lesender Node-Test mit denselben 20 Januarzeilen ergab unter UTC/Berlin `last_actual_day=20`, unter `America/New_York` dagegen `19`; auch die interpolierten Werte verschieben sich. Die bisherige Zwillingsprüfung garantiert somit keine Zeitzonenunabhängigkeit. Zusätzlich verlangt D1 am 31.12. eines Schaltjahres Tage 1…366, obwohl `full_365` den Tag 366 auf Slot 365 faltet.  
   **Änderung:** Die UTC-Korrektur des gemeinsam verwendeten Jahreskurvenbauers ausdrücklich in D1/D2 aufnehmen. Für den Matching-Präfix `d = min(Tagesnummer(as_of), 365)` festlegen, sofern die bestehende Faltung bleiben soll. Echte JS-/Python-Vergleiche unter mehreren Zeitzonen sowie für den 30./31.12. eines Schaltjahres ergänzen.

3. **HOCH — D5: Der primäre Mittelwert ist für das vorgesehene Manifest noch nicht vollständig definiert.**  
   **Fall:** Die vorhandenen Research-Caches beginnen bei ETHA/IBIT 2024, MAGS 2023 und XLC 2018. Diese Reihen können bis Ende 2025 keine zehn abgeschlossenen Vergleichsjahre liefern. Ihr Spearman ist mangels Score-Beobachtungen undefiniert. Andere Reihen können erst sehr spät auswertbar werden; einzelne Bootstrap-Ziehungen enthalten dann möglicherweise keine gültigen Beobachtungen für sie. „Je Reihe ein Spearman, gleich gewichtet“ beantwortet diese Fälle nicht.  
   **Änderung:** Vor dem Lauf Mindestfallzahl und Mindestjahresabdeckung, Ausschlussregeln sowie den Umgang mit konstanten Werten und undefinierten Bootstrap-Replikaten festlegen. Das auswertbare Universum anschließend festhalten; keine unbemerkte Änderung seiner Zusammensetzung je Ziehung durch `nanmean`. Für den gepaarten Vergleich exakt dieselben Bewertungstage verwenden. Ausschlüsse und tatsächliche Fallzahlen je Reihe berichten. Diese Ergänzung schließt den noch offenen Teil von Befund 10.

4. **MITTEL — D3/D5: Die Scanner-Tabelle ist noch kein unveränderliches prospektives Protokoll.**  
   **Fall:** Das [Schema](/C:/dev/Seasonaledge/scripts/create_market_tables.sql:76) identifiziert Zeilen durch `(ticker, scan_date)`; der [Writer](/C:/dev/Seasonaledge/shared/supabase_client.py:409) überschreibt sie per Upsert. Ein Wiederholungslauf am selben Tag kann damit einen bereits protokollierten Score ersetzen. `methode='saison_v1'` allein hält weder die konkrete Codeversion noch den ursprünglichen Datenstand fest.  
   **Änderung:** Vor Beginn der prospektiven Sammlung eine unveränderliche Archivierung definieren, beispielsweise einen separaten Laufdatensatz mit Codeversion, Erstellungszeit und Datenreferenz sowie unveränderlichen Ergebnissen. Festlegen, welcher Lauf pro Bewertungstag zählt und wie wiederholte `as_of`-Werte behandelt werden. Die Scanner-Anzeige kann weiterhin aus der aktualisierbaren Tabelle lesen; die spätere Bestätigungsauswertung braucht das festgehaltene Protokoll.

FREIGABE: nein
