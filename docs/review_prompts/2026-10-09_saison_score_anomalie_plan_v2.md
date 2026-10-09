# Plan v2: Saison-Score und Anomalie-Radar

Repo `C:\dev\Seasonaledge`. Nur lesen. v1: `2026-10-09_saison_score_anomalie_plan.md`, deine Antwort:
`..._plan_antwort1.md` (12 Befunde, FREIGABE nein). Unten nur, was sich gegenüber v1 ändert — Abschnittsnummern wie v1.
Antwort auf Deutsch, je Befund Schwere + Abschnitt + Fall + Änderung; am Ende genau eine Zeile `FREIGABE: ja` oder
`FREIGABE: nein`.

## 0. Gemeinsamer Eingabe- und Datumsvertrag (neu; gilt für C und D, Python = JS)
- **Eingabe:** vollständige, **ungefilterte** Kursreihe des Tickers `(datum ISO, close)`. Bereinigung wie Stress-Ampel:
  nicht-endliche oder ≤ 0 Schlusskurse raus, doppelte Datumswerte → letzter Wert, sortiert. Adjustierte Kurse wie
  gespeichert (kein eigenes Adjustieren). Kein Aufrufer filtert vorher (Dashboard-Zeitraumregler, KI-Seiten-Regler
  wirken nicht auf Score/Radar) → Befund 4.
- **as_of** = Datum der letzten Kurszeile nach Bereinigung (optional explizit übergeben; dann wird die Reihe **im Kern**
  auf ≤ as_of abgeschnitten, bevor irgendetwas anderes passiert). **Präfixinvarianz** ist Testfall: angehängte Zukunft
  ändert ein Ergebnis für festes as_of nicht.
- **Zieltag in Jahr y** = (Monat, Tag) von as_of in y; existiert der Tag nicht (29.02. in Nichtschaltjahr) → letzter
  gültiger Tag des Monats (28.02.). **End-Ziel** = Zieltag + 30 Kalendertage (nicht Startkurs-Datum + 30).
  Datumsarithmetik rein auf Kalenderdaten (Python `date`, JS über `Date.UTC`), keine Ortszeit.
- **Endpunkt** = letzte Kurszeile mit Datum ≤ Ziel. **Plausibilitätsregel v1 (Heuristik, ausdrücklich so dokumentiert):**
  Endpunkt höchstens *T* Kalendertage vor dem Ziel und im Fenster kein Abstand zwischen zwei Kurszeilen > *T*, mit
  *T* = 1 für Krypto (`-USD`), 3 für Forex (`=X`), **5** für Börsen (23.→28.12. XETRA = 5 KT ist damit regulär; Ostern
  Do→Di = 5). **Das erkennt grobe Datenlücken, nicht eine einzelne fehlende Sitzung** — so steht es im Methodentext
  und im Code; es wird nicht als Lückenprüfung verkauft. Eine kalendergenaue Sitzungsprüfung ist v2-Arbeit, weil die
  Kalenderzwillinge nur für NYSE/XETRA 2000–2035 nachgewiesen gleich sind (`verify_kalender_zwilling.py`) → Befund 1.
- **Rundung:** intern ungerundet; nur die Ausgabe `score` wird **halb aufwärts** auf eine Stelle gerundet,
  `floor(x·10 + 0,5)/10` in beiden Sprachen; Ampel/Status hängen nie an gerundeten Zwischenwerten.

## C — Anomalie-Radar (Änderungen gegenüber v1)
- **C1** nutzt den Vertrag oben: aktuelles Fenster = 11 Kurszeilen bis as_of, Plausibilitätsregel gilt auch für das
  **aktuelle** Fenster (sonst `nicht_berechenbar`, Grund „Kurslücke im aktuellen Fenster"); historisches Fenster =
  11 Kurszeilen bis zum Endpunkt ≤ Zieltag(y) über die ganze Reihe (Jahreswechsel erlaubt).
- **C2** „bis zu 30 gültige Vergleichsjahre" (die jüngsten 30 Jahre mit gültigem Fenster), mindestens 10; **Fallzahl
  und erstes/letztes Vergleichsjahr werden angezeigt**. Losgelöst von `fromPrices` (dessen „≥ 200 Zeilen je Jahr" und
  Systemjahreszahl gelten nicht mehr) → neue reine Funktion `SA.decadeCompute.anomalie(rows, {as_of})`.
- **C3** z mit Stichproben-Std (n−1), Mittelrang bei Gleichstand. Status |z| < 4/3 normal, ≥ 4/3 auffällig,
  ≥ 7/3 stark auffällig — **neue Festlegung**; die Statuswerte ändern sich gegenüber heute (neue Fenster, Referenz,
  Std), das wird nicht als „gleich" bezeichnet.
- **C5/C6** unverändert. **Beide Renderer** (`renderAnomalyInto` und die eigene `renderAnomalyCard` im Dashboard,
  `dashboard.html:1435`) nutzen `anomalie()` und zeigen dieselben Felder; der Wächter prüft beide DOM-Ausgaben,
  inkl. `nicht_berechenbar`.
- **C8** zusätzliche Fälle: Lücke im aktuellen Fenster; veraltetes Datenende (as_of liegt Wochen zurück → Vergleich
  am as_of, nicht an der Uhr); |z| genau 4/3 und 7/3; DOM-Ausgabe beider Renderer.

## D — Saison-Score (Änderungen gegenüber v1)
- **D1 Matching (fest, v1 „Pfadähnlichkeit"):** Kurven `full_365` aus der auf as_of abgeschnittenen Reihe mit dem
  bestehenden, zwillingsgeprüften Jahreskurvenbau (`buildYearData` / `shared.calculations`); Achse = **Tagesnummer**
  wie bisher (dokumentiert: ab März sind Schalt- und Nichtschaltjahre um einen Kalendertag versetzt). Präfix =
  Tage 1…d, d = Tagesnummer von as_of. **Kandidaten** = die Lookback-Jahre (20 jüngste abgeschlossene mit gültigem
  Fenster, ohne laufendes Jahr, ohne Jahre mit erster Kurszeile nach dem 10.01.). r = Pearson; **undefiniert**
  (Std 0) → Jahr kein Kandidat. Sortierung r absteigend, Gleichstand → jüngeres Jahr zuerst, **ungerundet**.
  Gewicht w = (r + 1)/2 ungerundet; Gewichtssumme 0 → B4 nicht berechenbar → Score null.
  **Musterkonformität** (Anzeige, nicht im Score) = Pearson r zwischen laufendem Jahrespfad und dem Mittelpfad der
  Lookback-Jahre über Tage 1…d.
- **D1 Mindestdaten:** Score erst ab dem **20. Handelstag** des Jahres (der Jahreskurvenbau verlangt ≥ 20 Zeilen;
  v1 sagte 15 → Befund 4). Tests: Handelstag 19 → null, 20 → Wert.
- **D2** unverändert, plus Tests: UI-Regler-Unabhängigkeit (Dashboard/KI-Seite liefern denselben Score wie der
  Kern auf der Vollreihe), Präfixinvarianz, Handelstag 19/20, Gewichtssumme 0, konstanter Pfad.
- **D3 Migration** `scripts/sql/scanner_saison_score_2026_10.sql`: `ALTER COLUMN score DROP NOT NULL`,
  `ALTER COLUMN signal DROP NOT NULL`; neue Spalten `methode TEXT`, `status TEXT` (`ok`/`nicht_berechenbar`),
  `grund TEXT`, `bausteine JSONB`, `as_of DATE`. Writer schreibt `signal: null` **ausdrücklich**. Nicht berechenbare
  Ticker werden als Zeile mit `status='nicht_berechenbar'` und Grund gespeichert; `score null` wird nirgends zu 0
  (Scanner sortiert sie ans Ende und zeigt „—", Mails lassen sie weg).
- **D3 Versionen/Fehler:** `methode='saison_v1'`-Filter in **Datumswahl, Ergebnisabruf und Resume-Check**
  (`fetch_scanner_results`, `full_scanner_run`). Schreibfehler werden bis zum Prozess gezählt; jeder Schreibfehler →
  Exit ≠ 0 (Rechenmangel eines Tickers ist kein Fehler, sondern eine `nicht_berechenbar`-Zeile). Der bisherige
  20-%-Toleranzerfolg des Full-Scanners gilt nur noch für Kursladefehler und wird im Log gezählt.
  **Veröffentlichung:** der Scanner zeigt den jüngsten `scan_date` der Methode **mit Abdeckung** „x von y Tickern
  (Stand as_of)" gegen das erwartete Universum (`tickers.json`) und listet fehlende Ticker; kein Ausblenden von
  Teilständen, aber ausdrückliche Kennzeichnung.
- **D4 Daily-Mail (neu festgelegt):** Auswahl der Top-Werte nach **Multi-Window-TDOM-Score** (Tiers mw ≥ 3 / ≥ 2 / alle);
  der Saison-Score sortiert nur innerhalb gleicher TDOM-Stufe, **keine** Score-Mindestgrenze (die alten 6,5/5,5/5,0
  waren KI-Score-Schwellen ohne Validierung). Das Urteil „stark bullish/bullish/leicht bullish" (hing an ki ≥ 7,5/6,5)
  wird zu einer Beschreibung „k/4 TDOM-Fenster historisch positiv". Die „Warum"-Zeile zeigt **getrennt** TDOM-Fenster
  mit ihrer Fallzahl und B1 als „Trefferquote nächste 30 T.: k/n" — nie eine Prozentzahl neben einer fremden Fallzahl.
  Watchlist-Mail-Join: Score + Bausteine, kein Signal.
- **D4 Monitoring:** `check_db_completeness` erwartet `scanner_results` mit `methode='saison_v1'` (Frische + Abdeckung)
  statt täglicher `ki_scores`; `ki_scores` wird nicht mehr geschrieben (Tabelle bleibt bis zur Nutzerentscheidung).
- **D5 Validierung (neu formuliert):**
  - Bezeichnung: **„historische Walk-forward-Auswertung nach Methodenrevision"** — kein Bestätigungstest; die Jahre
    sind durch die Berichte vom 08.10. bereits angesehen. **Prospektive Bestätigung:** die täglich gespeicherten
    `scanner_results` (`saison_v1`) sind das Protokoll; Auswertung frühestens 2027-10 mit diesem Protokoll.
  - **Vor dem Lauf festgehalten** in `scripts/research/saison_score_validierung_protokoll.json`: Codeversion (Commit),
    Snapshot-Hash, Ticker-Manifest, Bewertungsraster, Seed, Zeiträume, Kennzahlen.
  - **Manifest:** ^GSPC, ^DJI, ^GDAXI, SPY, QQQ (Snapshot) + die Research-Cache-ETFs **ohne** SPY/QQQ (dedupliziert),
    eindeutige Liste im Protokoll.
  - **Raster:** jeder 5. Handelstag 2010–2025 (Abschnitt A); ^GSPC/^DJI zusätzlich 1960–2009 (Abschnitt B, getrennt).
    Ziel = Fensterrendite as_of → Endpunkt ≤ as_of + 30 KT nach dem Vertrag oben; nur Bewertungstage, deren Ziel
    vollständig in den Daten liegt (ausgereift). Ziel wird dem Kalenderjahr von as_of zugeordnet.
  - **Primärer Test (einziger):** mittlere Spearman-Korrelation über die Reihen (je Reihe ein Spearman, **gleich
    gewichtet**) zwischen Score und Zielrendite, Abschnitt A. 95-%-Intervall per **Block-Bootstrap über Kalenderjahre,
    dieselben Jahre für alle Reihen je Ziehung**, 2000 Ziehungen, Seed 20261009, Perzentilintervall.
  - **Gepaart (sekundär, berichtet, keine Bestätigungsaussage):** Score vs. Vergleichsscore ohne Matching
    5·(B1 + B2) — Differenz der mittleren Spearman mit gepaartem Bootstrap-Intervall; Bausteine B1–B4 und
    Quintile (Gleichstände: Mittelrang, Quintile je Reihe) **explorativ**. „Immer positiv" nur als Basis der
    Positivrate.
  - **Aussage danach:** nur „Rangzusammenhang in der historischen Auswertung ja/nein" plus Zahlen. **Keine** Rückkehr
    der Bullish/Bearish-Etiketten aufgrund dieses Tests (Befund 11); dafür bräuchte es eine eigene, vorab definierte
    Prüfung konkreter Schwellen auf unabhängigen Daten.

## Reihenfolge (unverändert)
C → D1/D2 → D5 → D3 → D4. Jeder Schritt mit eigenem Code-Review.
