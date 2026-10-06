# Review-Auftrag: „Buy/Sell the Election" — ENTWURF Runde 8 (noch kein Code)

Repo `C:\dev\Seasonaledge`. Runde 1 ergab 13 Befunde [R1-n], Runde 2 sieben [R2-n]; alle übernommen. Neu/geändert gegenüber Runde 2 ist mit [R2-n] markiert. Prüfe den
überarbeiteten Entwurf. Antwort auf Deutsch, je Befund Schwere + Begründung + konkrete Änderung, am Ende genau
eine Zeile `FREIGABE: ja` oder `FREIGABE: nein`. Relevante Dateien wie Runde 1: `landing/pages/zentralbanken.html`,
`landing/pages/kriegszeiten.html`, `scripts/build_index_effect.py`, `landing/js/strategy-compute.js`
(`_electionDay`, `calc_midterm_election`, `SA.STRATEGIES`), `shared/strategies/plain_vanilla.py`,
`landing/pages/backtest-engine.html`, `landing/js/fomc-dates.js`, `landing/js/holidays.js`,
`scripts/build_calendar_data.py`, `shared/nyse_holidays.py`.

## Nutzerwunsch
Chart: Wahltermin + Indexverlauf X Handelstage vor bis Y nach der Wahl (S&P 500, Dow, DAX). Start US
(Präsident + Midterm, nächste 03.11.2026), später Deutschland und andere Länder. Daraus „Buy/Sell the election".

## 1. Termin- und Ergebnisdaten [R1-7, R1-11, R1-12]
**Einzige redaktionelle Quelle:** `landing/data/elections.json` (kuratiert, committet, kein Cron-Output).
```
{ "schema": 1, "data_version": "2026-10-06",
  "coverage": {"US": {"president": [1896, 2028], "midterm": [1898, 2026]}, "DE": {"bundestag": [1949, 2025]}},  // Terminabdeckung, NICHT Kursauswertbarkeit
  "parties": {"US-D": "Democratic", "US-R": "Republican", "DE-CDU": "CDU/CSU", ...},
  "elections": [ {
    "id": "us-midterm-2026", "country": "US", "type": "midterm", "date": "2026-11-03",
    "status": "scheduled" | "held" | "result_disputed",
    "schedule_known_from": "YYYY-MM-DD",          // ab wann der Termin feststand (regulär: gesetzlich, Jahre vorher)
    "early": false,                               // vorgezogene Wahl (DE 1972, 1983, 2005, 2025)
    "result": { ... typspezifisch, siehe unten ... } | null,
    "result_note": "2000: Entscheidung Bush v. Gore 12.12.2000",
    "sources": [ {"url": "...", "field": "date|result", "checked": "YYYY-MM-DD"} ] } ] }
```
Typspezifische Ergebnisse, `"unknown"`/`"n/a"` ausdrücklich erlaubt, Partei-IDs statt Text:
- `president`: `{winner_party, prior_party}` (Machtwechsel = abgeleitet, nicht gespeichert).
- `midterm`: `{house_before, house_after, senate_before, senate_after}` — Definition siehe Abschnitt 10 [R3-4] (ersetzt R2-6).
- `bundestag`: `{strongest_party, chancellor_party_before, chancellor_party_after, chancellor_change_date}`.
Wochentag wird abgeleitet, nicht gespeichert. Quellen: National Archives, House History (ab 1920), Senate,
Bundeswahlleiterin; frühe Kongresswahlen eigener Abgleich.
Fallzahlen vor Datenausschlüssen berechnet, nicht geschätzt: 33 Präsidentschaftswahlen 1896–2024,
32 Midterms 1898–2022, 18 Bundestagswahlen 1961–2025.
**Kein stiller Formel-Rückfall:** fehlt ein Termin, fehlt er sichtbar. Die Formeln `_electionDay` /
`_get_election_day` werden entfernt bzw. lesen die Liste; ein Wächter prüft, dass jede US-Regelwahl in der Liste
der Regel „erster Dienstag nach dem ersten Montag im November" folgt (Abweichung = Datenfehler).
JS-Zugriff nur über einen Lader auf dieselbe JSON (keine zweite Liste nach `fomc-dates.js`-Muster).

## 2. Index-Reihen [R1-11]
Pro Reihe dokumentiert (in `elections.json` oder einer Begleitdatei, angezeigt im Methodik-Abschnitt):
Quelle (Supabase/Yahoo/Stooq-Verkettung), tatsächlicher Datenbeginn, Kurs- vs. Performanceindex, Währung,
Rückrechnung/Quellenwechsel. Dow: Epochen 12 Werte (bis 1916) / 20 (bis 1928) / 30 getrennt ausweisbar.
S&P 500 ab 1928 (Index existiert seit 1957, vorher Rückrechnung). DAX: Variante zuerst messen (Kursindex-Historie
bis 1959 vs. Performanceindex ab 1987, `^GDAXI` = Performance) — keine Zusage „ab 1961", bevor die Reihe in
unserer DB geprüft ist. Blog und Seite rechnen auf demselben eingefrorenen Datenstand (Python-Referenz mit
Datenstand-Stempel).

## 3. Anker und Renditen — ein verbindlicher Vertrag [R1-1, R1-2, R1-3, R1-9]
- `anchorIdx` = Index des letzten gültigen Börsenschlusses **am oder vor** dem Wahltermin in der Kursreihe des
  gewählten Index („Referenzschluss t0"). US mit offenem Wahltag: der Wahltag selbst; geschlossen (alle Wahltage
  bis 1968, Präsidentschaftswahlen 1972–1980): der Handelstag davor. DE (Sonntag): Freitag/Samstag davor je nach
  Kalender der Reihe.
- Gültigkeit: Abstand Wahltermin − t0 ≤ 4 Kalendertage, sonst Ausschluss mit Grund (z. B. Börsenschließung 1914).
  Fehlende Kurse werden nicht als Schließung gedeutet: Lücken > 4 Kalendertage im Fenster → Ausschluss, gezählt.
  Historischer Samstagshandel: Kurszeilen sind die Sitzungsfolge, keine Mo–Fr-Annahme.
- `entryIdx = anchorIdx − X`, `exitIdx = anchorIdx + Y` — **für Seite, Strategie und Backtest-Engine gleich.**
- Renditen (nie Differenzen normierter Kurven):
  Vorlauf `100·(P0/P−X − 1)`, Nachlauf `100·(P+Y/P0 − 1)`, Fenster/Strategie `100·(P+Y/P−X − 1)`.
- Chart-Linie heißt „Referenzschluss t0", Tooltip zeigt Wahltermin UND t0-Datum. Verzögerte Ergebnisse (2000)
  markiert, nicht verschoben; eine Ergebnis-Zeitpunkt-Studie wäre eine eigene Untersuchung.
- **Bestehende Midterm-Strategie migrieren:** JS (`calc_midterm_election`, heute bei geschlossenem Wahltag t−5→t+4),
  Python (t−4→t+3) und Engine (Anker „erster HT ab Datum", 5/3 → t−4→t+4) auf den Vertrag umstellen; die
  geänderten historischen Ergebnisse vorher/nachher dokumentieren. Die Engine bekommt eine Ankerregel je
  Ereignistyp (`on_or_before` für Wahlen; bestehende Typen unverändert).

## 4. Darstellung `/wahlen` [R1-4, R1-6, R1-13]
- **Historische Studie:** x = Handelstage −X…+Y relativ zu t0, Normierung 100 bei t0, Kurven Mittel + Median,
  „Streuband p25–p75 der historischen Verläufe" (ausdrücklich kein Konfidenzband), Einzellinien zuschaltbar
  (grau, Hover: Jahr, Ergebnis). Nur Wahlen mit vollständigem Fenster; Zählung „verfügbar / ausgeschlossen
  (Grund) / ausgewertet".
- **Live-Vergleich** (separate Umschaltung, nur wenn eine Wahl bevorsteht oder läuft): alle Pfade bei t−X normiert,
  erst danach aggregiert; die laufende Wahl als eigene Linie bis zum letzten abgeschlossenen Handelstag, Zukunft
  `null`; künftige Sitzungen über den Indexkalender projiziert. Laufende Wahl nie in Aggregaten/Tabellen.
- **Saisonale Referenz** (siehe 5) als gestrichelte Linie im selben Chart.
- Regler X 5–60, Y 5–60; **vorab festgelegtes Hauptfenster X=20, Y=20** (je ~1 Monat) — die Kennzahlen im Text
  und im Blog beziehen sich nur darauf; Regler sind Exploration.
- Tabelle je Wahl: t0-Datum, Vorlauf, Nachlauf, Fenster, Ergebnis.
- Ergebnisfilter (Sieger, Machtwechsel, Kammerkontrolle) sind als „rückblickende Teilmenge — zum Einstieg
  nicht bekannt" beschriftet.
- Farbe: Gold + Grau, keine Partei- oder Richtungsfarben.

## 5. Saisonale Referenz und Statistik [R1-5, R1-6]
- US-Referenz: **ungerade Jahre** (keine reguläre Bundeswahl), je Jahr ein Pseudotermin nach derselben Regel
  (erster Dienstag nach dem ersten Montag im November), gleicher Anker-/Renditevertrag. Zuordnung in feste
  Vierjahresblöcke je Wahltyp (Präsidentschaftswahl t ↔ t−1 und t+1; Midterm t ↔ t−1 und t+1), beide ungeraden
  Jahre im Block gleich gewichtet, jeder Block gleich gewichtet; wiederverwendete Kontrolljahre zählen nicht als
  zusätzliche unabhängige Beobachtungen. Schließungsregime (bis 1968 / 1972–1980 / ab 1981) getrennt ausweisbar.
- DE-Referenz: je Wahl zwei Kontrolljahre ohne Bundestagswahl im Abstand ≤ 2 Jahre, Pseudotermin = Sonntag
  am nächsten zum selben Monatstag. Sensitivität: gleicher Kalendertag.
- Phase 1 **deskriptiv**: Mittel, Median, Trefferquote, n, gematchte Differenz Wahl − Referenz je Block.
  Kein p-Wert. Optional Intervall durch Resampling ganzer Blöcke, mit offen genannten Annahmen; nie Handelstage
  innerhalb von Pfaden resamplen. Text: „historischer Vergleich, kein isolierter Wahleffekt" (Konjunktur,
  Zyklus, FOMC bleiben Einflussgrößen). Ein Test kommt erst, wenn Nullhypothese, Statistik, zulässige
  Permutationen und Abhängigkeit vorab festgeschrieben sind.

## 6. Strategie und Menü [R1-8, R1-10, R1-13]
- `/wahlen` unter **Events** (Ereignisstudie). Link „Als Strategie testen" erst, wenn die Engine die Parameter
  übernimmt.
- Backtest-Engine (Phase 3): Ereignistyp `election`, Filter nur Land/Typ (Ergebnisfilter werden NICHT
  übergeben); je Einstieg Prüfung `schedule_known_from ≤ Einstiegsdatum`, sonst kein Trade; `entryIdx = 0`
  ohne Vorgeschichte → kein informationsabhängiger Trade.
- Begriffe getrennt: „Buy the election" = **long im Fenster** (Phase 3). „Sell the election" = **raus aus einer
  Buy-and-Hold-Position im Fenster, danach Wiedereinstieg**, verglichen mit Buy-and-Hold, mit Cash-Rendite 0
  (offen benannt) und Kosten — erst wenn die Engine einen Benchmark-Vergleich kann. Echter Short: nicht im Umfang.
- `/kalender`: Typ `election`, JSON + ICS, ICS-UID aus der stabilen `id`.

## 7. Code-Aufbau und Abnahme [R1-13]
- DOM-freier Rechenkern `landing/js/election-compute.js` (Anker, Fenster, Renditen, Aggregation, Referenz),
  den Seite UND node-Probe importieren. Python-Referenz `shared/elections.py` + `scripts/research/build_wahlen.py`
  auf denselben Eingaben, gleiche Quantildefinition (linear wie numpy), Rundung erst bei der Ausgabe.
- Wächter `scripts/js/probe_wahlen.js` + Python-Gegenstück, Pflichtfälle: offener Dienstag, geschlossener
  Dienstag, Sonntag (DE), Datenlücke, lange Schließung (1914), zukünftiges t0, unvollständiger Nachlauf,
  unbekanntes Ergebnis, vor Einstieg unbekannter Termin; dazu eine handgerechnete Mini-Reihe mit
  vorgegebenen Indizes und Renditen; Mutationstest des Wächters.
- Auslieferung: nginx-Route, `nav.html` + `index.html`-Nav-Kopie + Footer, de/en.json, `_EN_PAGE_META`,
  Sitemap-Priorität, `verify_en` und `verify_seo_html` grün.
- Nebenbefund (eigenes TODO, nicht Teil dieses Plans): zwei Nummerierungen des Präsidentenzyklus; die neue
  Funktion verwendet keine Zykluszahlen.

## 8. Phasen
1. US: `elections.json` (Präsident + Midterm, mit Quellen), Rechenkern, `/wahlen` DE+EN (historisch + Live +
   Referenz), Wächter, Midterm-Migration. Blogartikel zur Midterm 2026 mit Hauptfenster 20/20.
2. Deutschland: Bundestag, DAX-Reihe geprüft, DE-Referenz.
3. Backtest-Ereignistyp (Long), Kalender, Dashboard-Hinweis vor Wahlen; „Sell" als Ausstiegsvariante, wenn
   Benchmark-Vergleich vorhanden.
4. Weitere Länder mit eigenem Kalender und Index.

## 9. Nachträge aus Runde 2
- **[R2-1] Live-Vertrag:** Für eine künftige Wahl ist t0 eine *projizierte Sitzung* (aus dem Indexkalender), kein
  Kursindex. Beobachtete Kurse werden über die Sitzungsfolge relativ dazu positioniert (Offset = −(Anzahl erwarteter
  Sitzungen zwischen Kursdatum und projiziertem t0)). Erst wenn die t0-Sitzung abgeschlossen ist, wird sie zum
  Referenzschluss. Vor Vorliegen von t−X bleibt die Live-Linie leer. Die 4-Tage-Regel gilt nicht zwischen künftigem
  Wahltermin und Datenende. Angezeigt: Kalenderstand und letzter abgeschlossener Börsentag.
- **[R2-2] Datenlücken:** Erwartete Sitzungen (Kalender der Reihe) und vorhandene Kurszeilen werden getrennt
  validiert; jede fehlende erwartete Sitzung im Fenster → Ausschluss mit Grund. Für Zeiträume, in denen unsere
  Kalender historisch nicht stimmen (Samstagshandel bis 1952, Wahltags-Schließungen bis 1980, Sonderschließungen),
  gilt eine belegte Ausnahmeliste `historical_sessions` (Schließungen am Wahltag als Datenpunkte in
  `elections.json`: `exchange_closed_on_election_day: true|false`, mit Quelle). Wo der erwartete Kalender nicht
  belegt ist, wird nur die Kurszeilen-Folge genutzt und das Fenster als „Kalender unbelegt" gekennzeichnet; diese
  Fenster laufen in der Hauptauswertung mit, sind aber separat zählbar. Pflichtfälle: einzelner fehlender
  Handelstag, fehlender offener Wahltag (→ Ausschluss, nicht Montag als t0), gültiger historischer Samstag.
- **[R2-3] Migration aller Verbraucher:** `calc_midterm_election` (JS+Python), `calc_uecs` (JS+Python), Python-KTI
  (`plain_vanilla.py` ~597, `except Exception: pass` dort wird beseitigt bzw. meldet) und die Engine nutzen denselben
  Fensterkern und die Terminliste. Bestehende Midterm-Strategie bleibt **X=5/Y=3**; 20/20 nur für die neue Studie.
  Vorher/Nachher-Vergleich je Strategie dokumentiert. Der JSON-Lader läuft vor den synchronen Strategieberechnungen;
  Ladefehler → sichtbarer Fehler, nie „keine Trades".
- **[R2-4] Stichprobenvertrag Referenz:** Der gematchte Vergleich nutzt nur vollständige Tripel (Wahl + beide
  Kontrollen), separat gezählt von der allgemeinen Studie. Normierung je Kontrolljahr → Mittel innerhalb des Blocks →
  Mittel über dieselben Wahlblöcke. DE: Kontrolljahre = die beiden nächstgelegenen Jahre ohne Bundestagswahl, Abstand
  ≤ 2 Jahre; bei Gleichstand das frühere; fehlt eines → Tripel unvollständig, Wahl nicht im Vergleich.
  Resampling ist abgeschaltet, solange Kontrolljahre zwischen Wahltypen geteilt werden („alle US-Wahlen") —
  Phase 1 zeigt dort nur die deskriptive Differenz.
- **[R2-5] Engine-Sperre:** Für Ereignistyp `election` sind p-Werte, Signifikanzlabels und der Relevanzscore
  (`scoreEventRelevance`) gesperrt, bis ein Testprotokoll beschlossen ist. Abnahmekriterium für Phase 3.
- **[R2-6] Kammerkontrolle:** `house_before` = Mehrheit nach Sitzen am Tag vor der Wahl, `house_after` = Mehrheit
  zu Beginn des neuen Kongresses (3. Januar bzw. historischer Termin), Kontrollbegriff = Partei des Speakers bzw.
  Senats-Mehrheitsführers (organisatorische Kontrolle); Gleichstand im Senat → Partei des Vizepräsidenten, als
  `tie_vp` gekennzeichnet. Senatsauswertung beginnt bewusst 1914 (Abdeckungsgrenze, nicht `n/a`). `unknown` ≠ `n/a`;
  unbekannte Ergebnisse fallen aus Ergebnisfiltern heraus (nie als „kein Wechsel").
- **[R2-7] Bekanntgabe:** `schedule_known_from` bekommt eigene Quellen (`field: "schedule"`). Reguläre US-Termine:
  gesetzlich seit 1845 (Präsident) bzw. 1872/1875 (House) → `schedule_known_from` = Gesetzesdatum. DE: Datum der
  Anordnung durch den Bundespräsidenten (Bundesgesetzblatt). Ausführungsregel: Bekanntgabe nur tagesgenau → Einstieg
  frühestens in der folgenden Sitzung; fehlende Bekanntgabe-Historie → „Handelbarkeit nicht nachgewiesen", kein
  Trade. Testfall: Bekanntgabe am Einstiegstag.
- **Datenhistorie (Nutzerwunsch):** Die Terminliste wird zuerst und eigenständig angelegt (USA Präsident ab 1896,
  Midterms ab 1898, Deutschland Bundestag ab 1949), jeder Termin mit Quelle und zweiter Gegenprüfung; Sonderfall
  Maine (House-Wahl im September bis 1958) wird dokumentiert — maßgeblich ist der bundesweite November-Termin.

## 10. Nachträge aus Runde 3 — und eine Zuschnitt-Entscheidung
**Zuschnitt (beantwortet R3-1, R3-2, R3-3 strukturell):** Runde 3 zeigt, dass Phase 1 nicht gleichzeitig eine neue
Studie bauen UND alle bestehenden Wahlstrategien umziehen darf. Deshalb:
- **Die Studie rechnet nur in Python, serverseitig, auf festen Reihen** (Muster `/index-effekt`):
  `scripts/build_wahlen.py` → `landing/data/wahlen_study.json` (Cron-Output, gitignored, Schreibweg wie die anderen
  Cron-Dateien, danach HTTP-Abruf). Reihen Phase 1: `^GSPC`, `^DJI`; Phase 2: DAX-Reihe nach Prüfung. Gespeichert
  werden je Wahl der Pfad −60…+60 (Renditen auf t0 bezogen), Anker-Metadaten und Ausschlussgründe, plus die
  Referenzpfade je Kontrolljahr. Der Browser **rechnet nicht nach**, er wählt nur X/Y aus den gespeicherten Pfaden und
  aggregiert (Mittel/Median/Quantile linear) — diese Aggregation ist der einzige JS-Rechenschritt und wird per node
  gegen die Python-Aggregation geprüft. Kein freier Ticker in Phase 1.
- **Kalender (R3-1):** Erwartete Sitzungen kommen ausschließlich aus Python (`shared/nyse_holidays.py`,
  `shared/exchange_holidays.py`), JS braucht keinen Kalender für die Studie. Historische Ausnahmen als Datei
  `landing/data/election_calendar_exceptions.json` mit Schlüssel `(calendar_id, date)` und Quelle, deckt auch
  Pseudotermine ab (NYSE-Wahltagsschließungen, Samstagshandel bis 1952, 1914). `exchange_closed_on_election_day`
  entfällt im Wahl-Eintrag (gehört zum Markt). Regel: belegte Schließung → Anker rückt, kein Ausschluss;
  ungeklärte fehlende Sitzung → Ausschluss mit Grund; die 4-Tage-Grenze gilt nur für ungeklärte Lücken.
  Kalender-Abdeckung je calendar_id dokumentiert; Fenster außerhalb belegter Abdeckung → „Kalender unbelegt",
  gezählt. Die JS/Python-Abweichung 31.12. vor Samstag-Neujahr (holidays.js:143 vs. nyse_holidays.py:112) wird
  als eigener Nebenbefund behoben, Testfall Y=60 über 01.01.2028.
- **Live-Linie:** Python projiziert künftige Sitzungen aus demselben Kalender; Vertrag wie [R2-1]. Aktualisierung
  im Nightly (nach dem Kurs-Refresh), Datenstand im JSON.
- **Bestehende Strategien bleiben in Phase 1–3 unverändert** (`calc_midterm_election`, `calc_uecs` JS+Python,
  KTI, Signalvorschau in `plain-vanilla.html` DE/EN, `_electionDay`/`_get_election_day` werden NICHT entfernt).
  Stattdessen ein Wächter, der prüft, dass `_electionDay(y)` und `_get_election_day(y)` für alle Jahre der Liste
  dasselbe Datum wie `elections.json` liefern (Termin-Parität, kein Fensterumbau). Die bekannte Fenster-Uneinigkeit
  (t−5→t+4 / t−4→t+3 / t−4→t+4 bei geschlossenem Wahltag) wird als TODO mit den R2-3/R3-2/R3-3-Anforderungen
  (gemeinsamer Fensterkern, Signal ≠ vollständige Auswertung, KTI `[entry, exit)`, Signalvorschau = historischer
  Trade) dokumentiert und bekommt **eine eigene Phase M mit eigenem Review**. Seit 1981 ist die NYSE am Wahltag offen;
  die Abweichung betrifft also nur Wahlen bis 1980 — wird im TODO mit Zahl belegt.
- **Backtest-Engine (Phase 3):** Ereignistyp `election` liest Termine aus `elections.json`, nutzt den Anker
  `on_or_before` aus der Python-Studie als vorberechnete Liste `{id, anchor_date}` je Reihe (keine eigene Ankerlogik
  im JS); gilt nur für die Reihen, für die die Studie rechnet. Sperre der Tests wie [R2-5].

**[R3-4] Kammerkontrolle (ersetzt R2-6 und Abschnitt 1):** beide Kammern, vor und nach der Wahl dieselbe
organisatorische Größe: `{party, as_of, basis}` mit `basis ∈ {speaker, majority_leader, tie_vp, unknown}`.
`*_before.as_of` = Tag vor der Wahl, `*_after.as_of` = Beginn des neu gewählten Kongresses. Sitzmehrheit optional als
separates Feld `seat_majority`. Senat: Auswertung ab 1914 (Abdeckungsgrenze in `coverage`), vorher Feld fehlt.
`unknown` fällt aus Ergebnisfiltern heraus.

**[R3-5] Datenphase 0 (vor allem anderen, Nutzerwunsch):** `elections.json` mit USA Präsident 1896–2028,
Midterms 1898–2026 und Bundestag 1949–2025, jeder Termin mit Quelle + zweiter Gegenprüfung (`sources[]` mit
`field ∈ {date, result, schedule}`, `checked`-Datum, `verified: true` nur bei Übereinstimmung zweier Quellen).
Terminabdeckung (Liste) und Kursauswertbarkeit (Studie, z. B. DAX-Reihe) werden getrennt modelliert; die Zahl
der auswertbaren Wahlen ergibt sich in der Studie aus Kursdaten + Ausschlüssen, nicht aus der Liste. Wächter
`scripts/verify_elections.py`: Schema, Eindeutigkeit, US-Regel, Wochentag DE = Sonntag, Quellenpflicht,
Termin-Parität zu `_electionDay`/`_get_election_day`.

**Phasen neu:** 0 Daten → 1 US-Studie `/wahlen` (S&P 500, Dow; historisch + Referenz + Live) → 2 DAX/Bundestag →
3 Engine-Typ `election` (Long, Tests gesperrt) + Kalender + Dashboard-Hinweis → M Migration bestehender
Wahlstrategien (eigener Plan/Review).

## 11. Nachträge aus Runde 4 (Abschnitt 10 + 11 sind maßgeblich)
- **[R4-1] Exportformat = Kurse, nicht normierte Pfade.** `wahlen_study.json` enthält je Wahl und Reihe für die
  Offsets −60…+60 die **Schlusskurse mit Datum** (`[{offset, date, close, valid, reason}]`), dazu Anker-Metadaten.
  Live-Wahl: dieselbe Struktur, Offsets relativ zur projizierten t0-Sitzung, Zukunft `close: null`; das jeweilige
  Basisdatum (t−X) ist im Browser aus den Daten ablesbar. Der Browser macht genau drei Dinge: Auswahl der Offsets
  −X…+Y, Umbasierung jedes Einzelpfads (t0 = 100 für die historische Ansicht, t−X = 100 für den Live-Vergleich),
  Renditequotienten und Aggregation. Anker, Sitzungszuordnung und Gültigkeit bleiben Python. Alle Browser-
  Transformationen werden in node gegen Python geprüft. Pflichtfälle: Live vor t0; Wechsel X=5 ↔ X=20.
- **[R4-2] Gültigkeit je Offset, Stichprobe je Fenster.** `valid`/`reason` stehen pro Offset. Für das gewählte X/Y
  gilt eine Wahl als auswertbar, wenn alle Offsets −X…+Y gültig sind; nur diese Wahlen gehen in Mittel, Median,
  Band und Tabelle, und die Stichprobe ist über alle angezeigten Offsets konstant. Referenztripel werden ebenso je
  X/Y neu bestimmt (vollständig = Wahl + beide Kontrollen gültig über −X…+Y). Pflichtfälle: Lücke bei +45 und
  Datenende bei +25, jeweils mit 20/20 (beide auswertbar bzw. +25-Fall auswertbar) und 60/60 (beide ausgeschlossen,
  Grund sichtbar).
- **[R4-3] Engine-Parität (Phase 3):** Der Ereignistyp `election` lädt **keine eigene Kursreihe**, sondern nutzt die
  Kurse aus `wahlen_study.json` (gleicher Datenstand, gleiche Sitzungen, gleiche Gültigkeit). Ein-/Ausstieg =
  Offsets −X/+Y aus dem Export; ungültig → kein Trade, sichtbar gezählt, kein Vor-/Zurückschieben. Zusatzfilter,
  Stops und Eröffnungskurse sind für diesen Typ in Phase 3 abgeschaltet. Abnahme: Trade-Daten und Bruttorenditen
  Close/Close identisch mit der Studie.
- **[R4-4] Snapshots.** Die Nightly-Ausgabe ist die *aktuelle* Ansicht. Für Veröffentlichungen (Blog) wird ein
  unveränderlicher Snapshot `landing/data/wahlen_snapshots/<snapshot_id>.json` erzeugt und **committet** (eindeutiger
  Name, wird nie vom Cron überschrieben — daher mit der Regel „Cron-Outputs nicht committen" vereinbar) mit
  `snapshot_id`, Kursdatenstand (letztes Datum je Reihe), Version/Hash von `elections.json`,
  `election_calendar_exceptions.json` und Berechnungscode (git-SHA). Die Seite kann per `?snapshot=<id>` die
  historische Ansicht des Snapshots zeigen; der Blog verlinkt genau diese. Wächter prüft, dass jeder im Blog
  zitierte Snapshot existiert und dessen Kennzahlen mit dem Text übereinstimmen.

## 12. Nachträge aus Runde 5
- **[R5-1] Snapshot = vollständiges Auswertungspaket.** Ein Snapshot enthält: Kurse/Gültigkeit je Offset (wie
  Studie), die verwendeten Wahl- und Ergebnismetadaten (Kopie, nicht Verweis), Kontrollzuordnungen und
  Referenzpfade, Reihenmetadaten, `schema_version`, `calc_version`, Code-SHA, sowie die zitierte **Ansicht**
  `{series, election_type, filters, X, Y}`. Die Snapshot-Ansicht lädt ausschließlich den Snapshot, nie die aktuelle
  `elections.json`. Der Bloglink ist `?snapshot=<id>` und die Ansicht kommt aus dem Snapshot. Abnahme: nach einer
  Änderung der aktuellen Ergebnisdaten bleiben Stichprobe und Kennzahlen des alten Links gleich; der Wächter rechnet
  die Snapshot-Kennzahlen mit dem *aktuellen* Browser-Rechenkern nach und vergleicht mit den im Snapshot und im
  Blogtext gespeicherten Werten. Ändert sich der Rechenkern so, dass alte Snapshots abweichen, schlägt der Wächter
  an (bewusste Entscheidung nötig: Kern-Fix oder `calc_version`-Weiche).
- **[R5-2] Reichweite der Fenster-Uneinigkeit:** Die Aussage „nur bis 1980" gilt ausschließlich für lückenlose
  NYSE-Reihen. Das TODO für Phase M erfasst alle Kombinationen aus Wahltermin und Reihe/Handelskalender, an denen der
  Wahltag geschlossen ist, ausdrücklich auch heutige Nicht-US-Reihen (z. B. `^N225`, Tokio, 03.11. = Feiertag
  „Kulturtag", also auch 03.11.2026). Pflichtfall in Phase M: geschlossener Wahltag nach 1980 auf einer
  Nicht-US-Reihe. Bis Phase M wird in `plain-vanilla` ein Hinweis angezeigt, wenn der Wahltag auf der gewählten Reihe
  kein Handelstag ist.

## 13. Nachträge aus Runde 6 (Phase-3-Abnahme)
- **[R6-1] Annualisierung:** Für `election` blendet die Engine Sharpe aus (bis eine periodische Portfoliorendite-
  reihe existiert). CAGR wird nur über einen **explizit angezeigten Auswertungszeitraum** gerechnet
  (Kalenderzeit vom ersten möglichen Einstieg bis zum letzten Ausstieg der gewählten Stichprobe, alle Jahre ohne
  Trade eingeschlossen, Cash dazwischen 0 % — offen benannt). Abnahmefall: zwei Wahltrades mit vier Jahren Abstand
  und vorgegebenem Zeitraum → CAGR aus Kalenderzeit, nicht aus Trade-Jahren.
- **[R6-2] Drawdown:** Für `election` wird die Kapitalkurve **täglich zum Schlusskurs** aus den exportierten Kursen
  bewertet (in Position: Kurs; zwischen Trades: Cash konstant), Max Drawdown und Calmar daraus, beschriftet
  „schlusskursbasiert". Pflichtfall: Einstieg 100, Zwischenstand 60, Ausstieg 110 → Drawdown 40 %.
- Beides ist Abnahmekriterium für Phase 3; Phasen 0–2 sind davon nicht berührt.

## 14. Nachtrag aus Runde 7
- **[R7-1]** Für `election` sind in Phase 3 **Optimierung und Walk-Forward vollständig deaktiviert** (auch wegen
  Mehrfachtests über X/Y). Sharpe ist in Berechnung, Tabellen und Exporten `null` (nicht 0). Direkte Aufrufe von
  Optimierung/Walk-Forward mit diesem Ereignistyp werden mit sichtbarer Meldung abgewiesen; `best_by_objective`
  entsteht nicht. Abnahme: direkter Aufruf mit `objective: "sharpe"` liefert keine Parameterwahl.
