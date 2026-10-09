# Plan: Saison-Score (statt „KI-Score") und Anomalie-Radar — v1

Repo `C:\dev\Seasonaledge`. **Planprüfung vor der ersten Codezeile.** Nur lesen.
Python: `C:/Users/HeikoSeibel/AppData/Local/Python/pythoncore-3.14-64/python.exe`.
Antwort auf Deutsch: je Befund Schwere + Planabschnitt + konkreter Fall + Änderungsvorschlag; am Ende genau eine Zeile
`FREIGABE: ja` oder `FREIGABE: nein`.

Grundlage: eure Methodik-Prüfung vom 08.10. (`docs/review_prompts/2026-10-08_kennzahlen_methodik_codex.md`,
`..._claude.md`) und die KI-Modell-Evaluation (`2026-10-09_ki_modelle_evaluation_antwort.md`, P0).

## Nutzerentscheidungen (2026-10-09, verbindlich)
1. Name **„Saison-Score"** (statt „KI-Score"), Skala 0–10 bleibt.
2. **Bullish/Bearish entfernen** bis zur Validierung — überall (Scanner, Mails, Dashboard, Watchlist, KI-Seite).
3. **Methodik korrigieren + eine Rechnung (Python = JS) + Walk-forward-Validierung** mit vorab festgelegtem Protokoll.
4. Anomalie-Radar: behalten, korrigieren (aus „alles angehen").
5. Blogartikel bleiben unverändert (Entscheidung zur Ampel; gilt sinngemäß, ich fasse Blogposts nicht an).

---

## Teil C — Anomalie-Radar

Heute: eine JS-Rechnung `landing/js/decade-compute.js:267-313` (`fromPrices`), gerendert über `renderAnomalyInto`
(`:574-639`) auf Dashboard, Dekaden-, Jahres-, Monats-, Risikozyklus, Overnight, TDOM-Analyse. Der Python-Zwilling
`shared/anomaly_engine.py` läuft nur noch in `scripts/generate_decade_data.py:247` (Feld `anomaly` in
`DJI-decade.json`, im Frontend nur im nie aktiven Fallback ohne Supabase gelesen; der rendert zudem selbst neu).

**C1 Fenster.** Aktuelles Fenster: die letzten **11 Schlusskurse = 10 Tagesrenditen**, Ende = letzte Kurszeile
(`as_of`). Vergleich je früherem Jahr y: Endpunkt = letzte Kurszeile mit Datum ≤ (Monat/Tag von `as_of` in Jahr y)
— Vergleich über Monat/Tag statt Kalendertag-Nummer (Schaltjahre). Fenster = die 11 Kurse bis dort **über die
gesamte Reihe**, also über den Jahreswechsel hinweg (heute: Lücke in den ersten Handelstagen des Jahres).
Ein Jahr zählt nur, wenn der Endpunkt höchstens 4 Kalendertage vor dem Ziel liegt und das Fenster keine
Kurslücke > 4 Kalendertage hat (sonst ist es ein anderer Zeitraum).

**C2 Referenz.** Die **letzten 30** solcher Vergleichsjahre (nicht die ganze Historie — ^DJI seit 1897 bläht die
Streuung mit 1930er-Volatilität auf), mindestens **10**. Laufendes Jahr nie.

**C3 Kennzahl.** R = 10-Tage-Rendite (C_t/C_{t-10} − 1)·100. z = (R − Mittel)/s mit **Stichproben**-Std (n−1).
Dazu empirischer Rang mit Mittelrang bei Gleichstand: (#{<R} + ½·#{=R})/n·100. Anzeige: **„z = +1,6"** (mit
Vorzeichen) und Rang; die alte Zahl „48 / 100" entfällt. Status nach |z|: unter 4/3 „normal", ab 4/3 „auffällig",
ab 7/3 „stark auffällig" (= die alten Schwellen 40/70 bei Faktor 30, also kein Verhaltenssprung beim Status).

**C4 Fehlend.** Zu wenig Vergleichsjahre, s = 0 oder keine 11 Kurse → Status `nicht_berechenbar` mit Grund, nie
„normal" und nie Score 0 (heute zeigt das Dashboard dann „Normal", `dashboard.html:1467`).

**C5 Farbe.** Eine Farbe (Gold), Intensität nach |z|; Richtung nur als Vorzeichen/Text („ungewöhnlich stark" /
„ungewöhnlich schwach"). Grün/Rot nach Stärke statt Richtung (heute) widerspricht dem Tooltip.

**C6 Texte.** „Anomalie-Radar (KI Quick-Check)" → „Anomalie-Radar" (7 Seiten + `section.anomaly_radar` DE/EN);
Tooltip ohne „Contrarian"; Label „Rendite 10 Handelstage"; Methodentext mit Fenster, Referenz (30 Jahre),
z-Formel und Fallzahl.

**C7 Python-Zwilling löschen:** `shared/anomaly_engine.py` komplett (die übrigen Funktionen — TDOM-Anomalien,
Confidence — haben laut Importgraph keinen Aufrufer mehr, seit die Streamlit-Seiten weg sind); Feld `anomaly`
aus `generate_decade_data.py`.

**C8 Wächter** `scripts/js/probe_anomalie_radar.js` + `scripts/verify_anomalie_radar.py`: führt die echte
`decade-compute.js` in node aus (Muster `twin_probe.js`). Fälle: konstante Kurse → nicht berechenbar; ein
einzelner Sprung im aktuellen Fenster → z exakt aus unabhängiger Rechnung; Schaltjahr (29.02. als `as_of`);
Januar-Fenster über den Jahreswechsel; Gleichstände im Rang; Lücke > 4 Tage → Jahr fällt raus; < 10 Jahre →
nicht berechenbar; nur 30 jüngste Jahre. Mutationstest (atomar, mit `_atomar_schreiben`).

---

## Teil D — Saison-Score

### D1 Definition (eine, für Python und JS)

Parameter fest: **Horizont H = 30 Kalendertage** ab `as_of` (= Datum der letzten Kurszeile, **nicht** die Uhr),
**Lookback = die 20 jüngsten abgeschlossenen Jahre** mit Abdeckung des Fensters, **Top-N = 5** Musterjahre,
Matching Pearson auf dem Jahrespfad (`full_365`, normiert, wie heute) vom Jahresanfang bis `as_of`.

Fensterrendite eines früheren Jahres y: aus **Rohkursen**, nicht aus der interpolierten Kurve —
Start = letzte Kurszeile ≤ Monat/Tag(as_of) in y, Ende = letzte Kurszeile ≤ Start-Ziel + 30 Kalendertage
(darf in y+1 liegen → Jahreswechsel ohne Sonderfall); beide höchstens 4 Kalendertage vor ihrem Ziel, sonst zählt
das Jahr nicht.

Vier Bausteine, **alle auf demselben Fenster**, je 0…1:
- **B1 Trefferquote alle Jahre** = Anteil der Lookback-Jahre mit positiver Fensterrendite.
- **B2 Ø-Fensterrendite alle Jahre** → clip((R̄ + 3)/6, 0, 1) (die ±3-%-Abbildung wie heute; gesetzt, als solche
  dokumentiert).
- **B3 Trefferquote Musterjahre** = Anteil der Top-5-Musterjahre mit positiver Fensterrendite
  (heute: positive **Gesamtjahres**rendite → Selbstbezug zum bekannten YTD-Verlauf; gemessen Spearman(YTD, alt-B1)
  0,73).
- **B4 Ø-Fensterrendite Musterjahre** (ähnlichkeitsgewichtet) → clip((R̄ + 3)/6). Ersetzt den „Trend" aus dem
  geglätteten TruePath (Glättung und Interpolation entfallen in der Zahl).

**Score = 2,5·(B1 + B2 + B3 + B4)**, eine Nachkommastelle. **Tracking** (Musterkonformität) fliegt aus der Summe
(richtungslos — ein fallendes Muster perfekt zu verfolgen gab „bullishe" Punkte) und wird separat als
„Musterkonformität" angezeigt, berechnet gegen den Durchschnitt **ohne** das laufende Jahr, bis `as_of`.

**Nicht berechenbar statt 0,5:** weniger als 10 Lookback-Jahre mit Fenster, weniger als 5 Musterjahre, oder
`as_of` vor dem 15. Handelstag des Jahres (zu kurzer Pfad fürs Matching) → `score = null`, Grund angeben. Keine
neutralen Ersatzwerte mehr (heute `return 0.5` in mehreren `except`-Zweigen, `ki_score.py:62,106,152`).

Ausschlüsse: laufendes Jahr nie als Vergleichsjahr; ein Jahr, dessen erste Kurszeile nach dem 10.01. liegt
(unvollständiger erster Jahrgang, z. B. SPY 1993), nicht als Musterjahr (sein Pfad wäre bis zum Start konstant).

### D2 Eine Implementierung
- JS: neue Datei `landing/js/saison-score.js` (`SA.saisonScore.berechne(rows, {as_of?})` → `{status, score,
  bausteine:{b1:{wert,k,n},…}, musterjahre:[…], konformitaet, as_of, parameter}`). Dashboard, Watchlist,
  KI-Seite nutzen sie; die Inline-Kopien in `dashboard.html:650-760` und `ki-saisonalitaet.html:387-532` werden
  gelöscht. `dash-compute.js` behält nur, was andere brauchen (Stress), `computeKiScore` entfällt.
- Python: `shared/saison_score.py`, gleiche Funktion auf `(daten, closes)`; ersetzt `shared/ki_score.py` und die
  KI-Teile in `shared/ai_models.py` (Prophet/DTW/Claude-Kommentare ohne Aufrufer → löschen; `find_similar_years`
  hat dann keinen Nutzer mehr). `cache_manager.get_or_compute_ki_score` → `saison_score` direkt (schnell, kein
  Cache nötig).
- Zwillingstest `scripts/verify_saison_score.py`: echte JS in node gegen Python auf dem Snapshot (SPY, QQQ, ^DJI,
  ^GSPC, ^GDAXI) an jedem 5. Handelstag 2005–2025, Toleranz 1e-9 auf Bausteine, exakt auf `status`; dazu eine
  **dritte, naive Referenz** (direkt aus Rohkursen, ohne die geteilten Hilfsfunktionen) und analytische Fälle
  (ein Sprung genau im Fenster, Jahreswechsel-Fenster, Schaltjahr, < 10 Jahre, Gleichstand bei der Ähnlichkeit).
  Mutationstest.

### D3 Speicherung
`scanner_results` (Spalten heute: ticker, score, signal, win_rate, avg_return, deviation, scan_date).
Migration `scripts/sql/scanner_saison_score_2026_10.sql` (Nutzer führt aus): neue Spalten `methode TEXT`,
`bausteine JSONB`, `as_of DATE`; `signal` wird nicht mehr geschrieben (NULL). Der Scanner liest nur Zeilen
`methode = 'saison_v1'` des jüngsten `scan_date` und meldet, wenn für einen Ticker keine da ist. `win_rate`/
`avg_return` bedeuten künftig B1/R̄ des **30-Tage-Fensters** (heute: Kalendermonat) — die Seite beschriftet
sie neu. `ki_scores` (Cache-Tabelle) wird nicht mehr geschrieben; Löschen ist Nutzerentscheidung.
Nebenbei: `cache_manager.store_scanner_results` verschluckt Schreibfehler auf Debug-Ebene (`:231`) → Fehler
nach oben reichen, Nightly/Full-Scanner melden Exit ≠ 0.

### D4 Oberfläche und Texte
- Scanner: Spalten „Saison-Score", „Trefferquote 30 T. (k/n)", „Ø 30 T.", Musterjahre-Trefferquote; Filter nach
  Score-Bereich statt Signal; Zähler Bullish/Neutral/Bearish → Verteilung des Scores. FAQ/JSON-LD neu (heute:
  „DTW", „Prophet", „Bullish ab 6,5").
- Dashboard-/Watchlist-Karte: Score + vier Bausteine mit k/n, Musterkonformität separat, „nicht berechenbar"
  mit Grund. Keine Farbe nach Richtung (Score einfarbig Gold nach Höhe).
- KI-Seite `/ki-saisonalitaet` (URL bleibt): Titel „Saison-Score & Musterjahre"; Score immer mit den festen
  Standardparametern; die Regler (Methode, Top-N, Glättung, Zeitraum) wirken nur auf Musterjahr-Chart/TruePath und
  sind als Erkundung gekennzeichnet. „Machine Learning", „DTW", „Wahrscheinlichkeit", „unabhängig" raus.
- Mails: Daily (`daily_report.py` Sortierung/„Warum"-Zeile nutzen `ki_score`) und Weekly Abschnitt 1 („Top
  KI-Scores", Spalte Signal) → Saison-Score ohne Signal.
- Überall: Meta, JSON-LD, `de.json`/`en.json` (+ `_JSON_VER`), `tour-config.js`, `index.html`, `pricing`,
  `profile`, `seo/programmatic_seo_builder.py`, `i18n.js`-Metadaten (`:331`). Wächter `verify_en`,
  `verify_seo_html`, `verify_i18n_cache_version`.
- Nicht angefasst: Blogposts; das Video-Skript `qqq-truepath-ki-saisonalitaet.json` melde ich dem Nutzer.

### D5 Validierung — Protokoll jetzt festgelegt, vor dem ersten Lauf
- **Frage:** Hat der Saison-Score (und jeder Baustein einzeln) eine Rangbeziehung zur Rendite der folgenden
  30 Kalendertage?
- **Daten:** ^GSPC, ^DJI, ^GDAXI, SPY, QQQ (Snapshot) + die 40 ETF-Reihen im Research-Cache. Nur Daten bis
  `as_of`; Score exakt mit der Produktionsfunktion.
- **Bewertungstage:** jeder 5. Handelstag; Ziel = Rendite vom Schluss `as_of` bis letzte Kurszeile ≤ as_of+30 KT.
- **Zeitraum:** primär **2010–2025** (Out-of-sample im Sinne: Parameter oben sind vor dem Lauf fixiert und werden
  danach nicht verändert); ^GSPC/^DJI zusätzlich 1960–2009 als zweiter Abschnitt, getrennt berichtet.
- **Kennzahlen:** Spearman je Reihe; gepoolt über Reihen; Quintil-Spreizung (oberstes − unterstes Quintil der
  Fensterrendite). Unsicherheit per **Block-Bootstrap nach Kalenderjahr** (2000 Ziehungen), weil sich die
  30-Tage-Fenster überlappen und Reihen korreliert sind.
- **Basen:** B1 allein (reine Saison-Trefferquote) und „immer positiv" (unbedingte Rate).
- **Kriterium für die Rückkehr von Richtungsetiketten** (alle drei müssen gelten): gepoolter Spearman 2010–2025
  mit 95-%-Intervall > 0; in mindestens 3 der 5 Indexreihen Spearman > 0; Quintil-Spreizung mit Intervall > 0
  **und** besser als B1 allein. Sonst bleiben die Etiketten weg, und das Ergebnis (auch „kein Zusammenhang")
  wird im Methodentext der Seite mit Zahlen genannt.
- Ergebnis wird **nach** dem Bau einmal gerechnet und unverändert berichtet; keine Parametersuche danach.

### Reihenfolge
1. A+B (Streamlit/Mails, separat im Review) → 2. **C** → 3. **D1+D2** (Kern + Zwilling) → 4. **D5** Validierung
(mit dem fertigen Kern, vor der Oberfläche — damit die Texte das Ergebnis kennen) → 5. **D3** Migration + Nightly →
6. **D4** Oberfläche/Texte/Mails.

## Fragen an dich
1. Ist ein 30-Kalendertage-Fenster aus Rohkursen mit „≤ Ziel, höchstens 4 Tage davor" robust (Feiertage,
   Wochenenden, Kurslücken, Krypto 24/7, XETRA-Sonderschließungen)?
2. Matching bleibt Pearson auf dem normierten Jahrespfad (Kursniveau). Eure Berichte bemängeln, dass Niveaus
   trendender Reihen fast immer hoch korrelieren. Reicht es, das in der Validierung (B3/B4 gegen B1/B2) zu sehen,
   oder gehört eine Änderung (Korrelation der Wochenrenditen, z-normierter Pfad) jetzt in die Definition — vor dem
   Test, nicht danach?
3. Ist das Validierungskriterium scharf genug, oder fehlt eine Korrektur für die vier Bausteine + Score (fünf Tests)?
4. Übersehe ich einen Verbraucher des Scores (Supabase-RPCs, Views, Edge Functions, Weekly/Daily, Watchlist-Sync
   `user_watchlists`, Premium-Gates)?
5. Teil C: 30 Jahre / mindestens 10 — vertretbar? Und ist „Monat/Tag ≤ Ziel" am 29.02. sauber definiert?
