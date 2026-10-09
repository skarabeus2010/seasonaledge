# Plan: Crash-Ampel → Stress-Ampel (v5) — zur Prüfung VOR dem Code

## v5 — Festlegungen zu den Einwänden aus Runde 4 (`..._plan_antwort4.md`), gehen v4 und älter vor

**Y1 Kein Anhängen mehr — jeder Schreiblauf ist ein Vollauf (E1, E3).** Auch der Nightly erzeugt für SPY jeden Tag eine
**vollständige neue Version** (rund 5.700 Zeilen, 12 Batches à 500; Rechnung in Python mit sortiertem Fenster
O(n log n)). Damit fließt jede historische Kurskorrektur oder entfernte Kurszeile automatisch ein, und es gibt keine
Zeilen außerhalb eines geprüften Laufs. Der Siebentagevergleich und das Anhängen aus X1 entfallen. Leser lesen nur den
jüngsten `fertig`-Lauf; eine Veröffentlichungsgrenze innerhalb eines Laufs ist nicht nötig, weil ein Lauf nach `fertig`
nie mehr verändert wird. Zusätzlich speichert jeder Lauf `kurse_hash` (SHA-256 über die bereinigte Folge `datum|close`
mit `repr`-genauen Werten) zur Nachvollziehbarkeit.

**Y2 Atomare Sperre und Veröffentlichung in der Datenbank (E2).** In der SQL-Datei:
- Partieller Unique-Index `stress_laeufe(ticker) where status = 'laeuft'` → höchstens ein laufender Lauf je Ticker,
  durch die Datenbank erzwungen.
- Spalte `laeuft_bis timestamptz` (Lease, 30 min).
- Funktion `stress_lauf_starten(p_ticker text) returns uuid` (SECURITY DEFINER, EXECUTE nur service_role): setzt in
  **einer** Transaktion abgelaufene `laeuft`-Einträge (`laeuft_bis < now()`) auf `abgebrochen` und legt den neuen Lauf mit
  `laeuft_bis = now() + 30 min` an; scheitert am Index, wenn ein gültiger Lauf existiert → Rückgabe NULL.
- Funktion `stress_lauf_veroeffentlichen(p_lauf uuid, p_n int, p_erstes date, p_letztes date, p_hash text) returns boolean`:
  `update … set status='fertig', fertig_am=now(), … where lauf_id = p_lauf and status = 'laeuft' and laeuft_bis > now()`;
  `false`, wenn der Lauf verdrängt oder abgelaufen ist → er wird nie sichtbar.
- Funktion `stress_lauf_abbrechen(p_lauf uuid)`.
- **Alle Schreiber** (Nightly, `--full`, Aufräumen) gehen über diese Funktionen; Nightly ist ein normaler Vollauf.
- **Aufräumen** nur nach erfolgreicher Veröffentlichung, nur Zeilen von Läufen mit `status = 'abgebrochen'` oder
  `fertig` außer den zwei jüngsten; nie `laeuft`. Ein verdrängter Prozess schreibt höchstens Zeilen unter seiner eigenen,
  nie veröffentlichten `lauf_id`; sie werden beim nächsten Aufräumen entfernt (sein Status ist dann `abgebrochen`).
- Wächter gegen einen Fake mit denselben Regeln **und** eine SQL-Prüfung der Funktionen nach dem Anlegen (lesend über
  RPC-Aufrufe mit einem Test-Ticker `__TEST__` auf dem Server: zweiter Start → NULL; Veröffentlichung nach Ablauf →
  false; Aufräumen lässt `laeuft` stehen); danach werden die Testzeilen entfernt.

---

## v4 — Festlegungen zu den Einwänden aus Runde 3 (`..._plan_antwort3.md`), gehen v3/v2/v1 vor

**X1 Versionierte Läufe (E1, E2; ersetzt in W2 „idempotenter Upsert" und „kein Delete").** Zwei Tabellen (SQL-Datei wie W2):
- `stress_laeufe`: `lauf_id uuid PK, ticker text, status text check (status in ('laeuft','fertig','abgebrochen')),
  gestartet_am timestamptz, fertig_am timestamptz, n_kurse int, n_scores int, erstes_datum date, letztes_datum date,
  kurse_bis date, methode text default 'stress_v1'`. RLS: anon SELECT, Schreiben service_role.
- `stress_scores`: Spalten wie W2 **plus `lauf_id uuid`**, PK `(lauf_id, date)`, Index `(ticker, lauf_id, date)`.
**Lesen (Frontend, Health-Check):** nur der jüngste Lauf mit `status = 'fertig'` des Tickers; zusätzlich gilt die
W2-Regel „lückenlos bis zur letzten Kurszeile", sonst Browserberechnung. Ein laufender, abgebrochener oder älterer Lauf
wird nie gelesen.
**Vollauf (`--full`):** (1) Sperre: kein anderer Lauf des Tickers mit `laeuft` und `gestartet_am` jünger als 2 h, sonst
Abbruch; ältere `laeuft`-Einträge werden auf `abgebrochen` gesetzt. (2) Zeile in `stress_laeufe` mit `laeuft` anlegen
**vor** dem ersten Datenwrite. (3) Eingabe- und Mengenprüfung wie W2 (exakt `max(0, n − 776)` Zeilen, Zählabfrage),
sonst `abgebrochen` ohne Datenwrite. (4) Schreiben aller Zeilen mit dieser `lauf_id`. (5) Paginierter Rücklesevergleich
gegen die Sollmenge (Datumsmenge exakt, score/s/ampel exakt). (6) Erst dann `status = 'fertig'`, `fertig_am`. Jeder Fehler
→ `abgebrochen`, Exit 1; der zuletzt fertige Lauf bleibt gültig. Wiederanlauf = neuer Vollauf mit neuer `lauf_id`.
Damit entfallen die Fälle „gemischte Kursstände" und „überzählige Zeile": eine neue Version hat genau die neue Sollmenge.
**Aufräumen:** nach einem erfolgreichen Vollauf werden Zeilen von Läufen gelöscht, die weder der neue noch der vorherige
fertige Lauf sind (abgebrochene und ältere) — betrifft nur nie gelesene Daten. `regime_scores` bleibt unangetastet.
**Nightly (täglich):** hängt an den jüngsten fertigen Lauf nur **neue** Daten an (Datum > `letztes_datum`), nachdem es
die letzten 7 bereits gespeicherten Tage neu gerechnet und **gleich** gefunden hat (|Δscore|, |Δs| ≤ 1e-9, Datumsmenge
gleich). Weichen sie ab (Kurskorrektur, entfernter Kurs) → kein Anhängen, stattdessen Vollauf mit neuer Version.
Nach dem Anhängen Rücklesen der neuen Zeilen und `letztes_datum`/`n_scores` aktualisieren; scheitert das, fehlt am Ende
ein Tag → das Frontend fällt wegen der Lückenregel auf die Browserberechnung zurück, der nächste Nightly holt nach.
Wächter: Erstlauf, Kurskorrektur in der Mitte, entfernte Kurszeile nach erfolgreichem Lauf, Batchfehler im Vollauf und beim
Anhängen, parallele Sperre — jeweils mit Fake-Client und der tatsächlich gelesenen Datumsmenge.

**X2 Lader für kurze Reihen (E3).** Alle Stress-Aufrufer nutzen einen Adapter `stress_score.lade_kurse(ticker)` =
`lade_closes(ticker, mindestens=0)`; ein echter Abruffehler (Netzwerk, leere Antwort trotz `count` > 0, `KursreiheFehlt`
bei mindestens=0) wird als `fehlt` durchgereicht, eine erfolgreich geladene Reihe mit 0–776 Schlüssen als `zu_kurz` mit den
Komponenten nach W1. Der Standard von `lade_closes` für andere Konsumenten bleibt. Adaptertests für 0, 6, 20, 21, 29, 777
Schlüsse und einen simulierten Ladefehler.

---

## v3 — Festlegungen zu den Einwänden aus Runde 2 (`..._plan_antwort2.md`), gehen v2 und v1 vor

**W1 Eine Mindesthistorie (E1).** Erster Score am **777.** bereinigten Schluss (|W| ≥ 756); volle Referenz (2520) ab dem
**2541.** Schluss — die längere Ladehistorie dient nur der vollen Referenz. Fehltext „zu kurze Historie (n von 777
benötigten Kursen)". Komponenten gestaffelt: dd20 ab 20 Schlüssen, vol5 ab 6, vol20 und S ab **21**. V2/V6 sind
insoweit ersetzt.

**W2 Neue Tabelle statt Umbau (E2, E3, E4; ersetzt V3/V4).** Über die REST-API gibt es keine Transaktion und auf dem
Server keinen direkten Datenbankzugang (geprüft: kein psql, kein psycopg, nur `SUPABASE_URL/KEY`). Deshalb wird die
bestehende Tabelle **nicht** umgeschrieben:
- Neue Tabelle `stress_scores` (SQL-Datei `scripts/sql/stress_scores_schema_2026_10.sql`, vom Nutzer einmal im
  SQL-Editor ausgeführt): `ticker text, date date, score double precision NULL, ampel text, s double precision,
  vol5 double precision, vol20 double precision, dd20 double precision, ret1d/ret5d/ret20d double precision,
  referenz_n int, methode text default 'stress_v1', berechnet_am timestamptz default now()`, PK (ticker, date),
  RLS: anon SELECT, Schreiben nur service_role (Muster `create_regime_scores.sql`). Double statt REAL → Rücklesen exakt.
- `regime_scores` bleibt **unverändert** stehen (ist damit selbst die Sicherung) und wird nach dem Deploy von keinem
  Code mehr gelesen oder geschrieben. Löschen der Altdaten = spätere Nutzerentscheidung. Kein Delete, kein Rollback-Pfad.
- Befüllen für SPY nach dem Deploy (`compute_regime_scores.py --full`, idempotenter Upsert; Wiederanlauf = derselbe
  Aufruf). **Vor dem Schreiben exakte Prüfung:** n bereinigte Schlüsse → genau `max(0, n − 776)` Zeilen, Datumsmenge =
  Schlüsse Nr. 777 … n; Eingabevollständigkeit unabhängig über eine zweite Zählabfrage (`count=exact` auf `prices`) und
  die Datumsgrenzen; Roh- und bereinigte Zeilenzahl im Protokoll; Abweichung → Abbruch ohne Schreiben. **Nach dem
  Schreiben:** paginierter Rücklesevergleich Tabelle gegen Sollmenge (Datum, score, s, ampel exakt).
- **Übergang ohne Wartungsanzeige:** Das neue Frontend nimmt DB-Werte nur, wenn sie den angezeigten Zeitraum
  **lückenlos bis zur letzten Kurszeile** abdecken; sonst rechnet es denselben Score im Browser (gleiche Formel, Quelle
  sichtbar „im Browser berechnet"). Eine leere oder halb gefüllte Tabelle zeigt damit nie falsche Werte. Bis zum Deploy
  zeigt die alte Seite die alten (falschen) Werte aus `regime_scores` — wie heute; es entsteht keine Mischung.
- Der alte Nightly schreibt bis zum Deploy weiter `regime_scores` (harmlos, niemand liest sie danach); der neue schreibt
  nur `stress_scores`. Kein Timer-Stopp nötig. Scheitert der Deploy, bleibt alles beim heutigen Stand.

**W3 Health-Check mit Methodennachweis (E5).** Check 6 liest `stress_scores` (SPY): Aktualität wie bisher, dazu
Neuberechnung `stress_aktuell(lade_closes("SPY"))` und Vergleich der letzten Zeile (Datum gleich, |score − score'| ≤ 1e-9,
|s − s'| ≤ 1e-9, ampel gleich) → rot bei Abweichung. Completeness-Check: `stress_scores` für SPY statt `regime_scores`.
`scripts/verify_security.py`: `stress_scores` in die Liste der öffentlich lesbaren Tabellen.

**W4 Wochenreport aktuell (E6).** Ergebnis je Ticker mit Kursdatum; Status `veraltet`, wenn das letzte Kursdatum mehr
als 5 Sitzungen vor `letzte_session(boerse)` liegt, `zu_kurz`, `fehlt` (Ladefehler) getrennt ausgewiesen. „Alle im
grünen Bereich" nur, wenn alle Top-Ticker einen aktuellen Score haben und alle grün sind.

---

## v2 — Festlegungen zu den Einwänden aus Runde 1 (`..._plan_antwort1.md`), gehen v1 vor

**V1 Rundung/Grenze (E1).** Der **ungerundete** Score (double) entscheidet in Python und JS über die Farbe; die Farbe wird
im Backend aus dem double bestimmt und als `traffic_light` gespeichert. Das Frontend nimmt bei DB-Werten die gespeicherte
Farbe, nicht eine Neuberechnung aus `risk_score` (Spalte bleibt `REAL`, keine Schemaänderung; float32 von k/|W|·100 kann
die Grenze nicht verschieben, weil die Farbe nicht daraus gelesen wird). Anzeige: **abgeschnitten auf eine
Nachkommastelle** (89,96 → „89,9", gelb; ≥ 90 → „≥ 90,0", rot) — nie eine Zahl, die der Farbe widerspricht. Wächter:
Grenzfälle 69,99/70,0/89,96/90,0 in beiden Sprachen und nach float32-Rücklesen.

**V2 Eingabevertrag (E2).** Quelle in **allen** Pfaden ist die Supabase-Tabelle `prices` (Spalte `close`): Python über
`shared.data.lade_closes` (ohne Yahoo-Rückfall, ohne `preprocess`), JS über `SA.fetchAllPrices`. Beide: aufsteigend
sortiert, ein Wert je Datum (Duplikate → letzter Wert, protokolliert), Bereinigung **nur** nach D (ungültiger Close raus).
Berechnung immer auf der vollen geladenen Reihe, Kürzen erst für die Anzeige. Mindestvorlauf: aktueller Wert braucht
**2541** gültige Schlüsse, Verlauf über N Tage entsprechend N + 2540. Crash-Seite lädt dafür ab „heute − 13 Jahre"
(statt 2020); Dashboard (30 J.) und Watchlist (voll) reichen. Integrationstest durch die echten Adapter (Python:
`lade_closes`-Ausgabeformat; JS: Zeilenformat von `fetchAllPrices`).

**V3 Migration (E3).** Keine Transaktion über die REST-API möglich, deshalb:
(1) Sicherung **aller** Zeilen von `regime_scores` (paginiert, Zeilenzahl + SHA-256 über die sortierte JSON-Serialisierung,
Wiederherstellung einmal auf einer Kopie im Speicher geprüft: Rücklesen = Sicherung);
(2) neue Werte vollständig berechnen und **vor** dem Schreiben validieren (Zeilenzahl ≥ 90 % der gültigen Kurstage −
2540, keine NaN, Farben = Grenzregel, Plausibilitätsdaten aus dem Wächter);
(3) schreiben, bei **jedem** Batchfehler sofort Rückspielen der Sicherung (Upsert der Altzeilen + Löschen der nur neu
geschriebenen Daten) und Abbruch mit Exit 1;
(4) erst danach Zeilen löschen, die nicht zum neuen Satz gehören.
**Ablauf und Schreibkoordination:** Migration läuft mit dem neuen Code aus einem Temp-Verzeichnis im Container (Muster aus
CLAUDE.md), nur wenn `sa-nightly.service` nicht aktiv ist und der nächste Nightly-Termin > 60 min entfernt liegt;
`sa-nightly.timer` wird für die Dauer angehalten und danach wieder gestartet. Unmittelbar danach Commit/Push/Deploy;
bis zum Deploy zeigt die alte Seite die neuen Werte samt neuer Farbe aus der DB (Richtung korrekt). Ladefehler →
Abbruch ohne Löschen; verifiziert zu kurze Historie → Altzeilen dieses Tickers löschen.

**V4 Migrationsmenge (E4).** Aus den **tatsächlich vorhandenen** DB-Tickern (paginierter Scan von `regime_scores`).
SPY wird neu gerechnet. Alle anderen Ticker (seit Wochen nicht mehr gepflegt, Nightly schreibt nur SPY): Zeilen
**entfernen** (nach Sicherung), je Ticker protokolliert — kein Ticker bleibt mit IF-Altwerten. `--all-relevant` entfällt.

**V5 Wochenreport, Betriebsprüfungen, Watchlist (E5).** Wochenreport rechnet den Stress der Top-Ticker **live** über
`stress_score.stress_aktuell(lade_closes(t))` statt aus `regime_scores` (die nur SPY enthält); Template: Text
„Stress-Ampel" ohne Isolation Forest, Einheiten ohne doppeltes ×100, „Alle im grünen Bereich" nur, wenn **alle** Top-Ticker
einen Score haben, sonst „x von y berechenbar". Completeness-Check: `regime_scores` nur für SPY erwartet. Health-Check
Check 6 zusätzlich: letzte SPY-Zeile hat `risk_score` in [0, 100] und `traffic_light` passend zur 70/90-Regel (fängt eine
Zeile der alten Methode). Watchlist-Summe „Grün: x von y berechenbaren", fehlende separat. EN-Seiten (Dashboard,
Watchlist; Crash-Seite ist DE-only) werden im Deploy aus denselben Quellen erzeugt, `verify_en.py` im Umfang.

**V6 Kein Wert (E6).** `score = null`, Status `grey`, Text „zu kurze Historie (n von 2541 benötigten Kursen)" bzw. für
den Verlauf ab dem 2541. Kurs; erster Score frühestens am Kurs Nr. **777** nur dann, wenn man |W| ≥ 756 zulässt —
festgelegt: Mindestens **756** Referenzwerte, erster Score am **777.** gültigen Schluss, Referenz „bis zu etwa zehn
Jahre" mit Anzahl und Zeitraum im Ergebnis (`referenz_n`, `referenz_von`, `referenz_bis`). Komponenten (vol5, vol20,
dd20, S) werden auch ohne Score geliefert, sobald 20 Schlüsse da sind. Nie `0/100`, nie als Grün gezählt.

**V7 Gewichtung (E7).** Formel bleibt (Nutzerentscheidung „transparent", Gewichtung 0,3/0,3/0,4 übernommen), auf der Seite
als **heuristisches Maß** beschrieben, ohne Behauptung über Einflussanteile. Wächter-Fall: monoton fallender Kurs mit
konstanter Rendite → vol = 0, S kommt nur aus dem Drawdown.

**V8 Punkt-in-Zeit (E8).** Formulierung: „nutzt nur Kurse bis zum jeweiligen Tag (bezogen auf den aktuellen
Kursdatenstand)". Nightly Phase E schreibt ab **min(letztes DB-Datum + 1 Tag, heute − 7 Tage)** und damit auch Lücken nach
Ausfällen; ein Vollauf (`--full`) bleibt für historische Kurskorrekturen.

**V9 Numerik und Wächter (E9).** Beide Sprachen: Stichproben-Std mit Zwei-Pass-Verfahren (Mittel, dann Summe der
Quadrate); Vergleich im Rang mit Toleranz **ε = 1e-9**: S_j < S_t − ε zählt kleiner, |S_j − S_t| ≤ ε zählt als
Gleichstand. Wächter zusätzlich: unabhängige Sollwerte (Hand), konstante Reihe (alle Gleichstände → 50), wiederholte
Fenster, **Präfixinvarianz** (Anhängen späterer Kurse ändert keinen früheren Score), `stress_aktuell` = letztes Element
von `stress_reihe`, 776/777 Kurse, Grenzrundung + float32-Rücklesen, Migration mit simuliertem Batchfehler (Fake-Client:
Rückspielen nachweisen) und unvollständiger Eingabe (Abbruch ohne Löschen), Backend-Adapter ohne `preprocess`.

**V10 Messung (E10).** Ereignis vorab: `min(c[t+1..t+20]) / c_t − 1 ≤ −0,10`. Rot-Quote und Basisrate auf **denselben**
auswertbaren Tagen (letzte 20 Sitzungen ausgeschlossen), mit Fallzahlen, überlappende Tage als abhängig gekennzeichnet.
Farbanteile nur über gültige Scores, Abdeckung daneben. Deine Snapshot-Anteile (Rot 7–13 %) werden so auf der Seite als
„Verteilung" gezeigt, nicht als feste 10 %.

---

Repo `C:\dev\Seasonaledge`, Stand `95209ec`. Anlass: Methodik-Prüfung vom 08.10.2026
(`docs/review_prompts/2026-10-08_kennzahlen_methodik_codex.md`, `..._claude.md`). Prüfe diesen **Plan**, bevor Code
entsteht. Antwort auf Deutsch: je Einwand Schwere + Planpunkt + konkreter Fall + Änderung; am Ende genau eine Zeile
`FREIGABE: ja` oder `FREIGABE: nein`. Python: `C:/Users/HeikoSeibel/AppData/Local/Python/pythoncore-3.14-64/python.exe`.
Kurs-Snapshot (eingefroren, `{date, close}`): `C:/Users/HEIKOS~1/AppData/Local/Temp/claude/c--dev-Seasonaledge/b1245851-7084-4449-b6ab-61b4ed04fde7/scratchpad/pv_kurse/*.json` (^DJI, ^GSPC, SPY, QQQ, ^GDAXI bis 07.10.2026).

## Befund (belegt)
- Backend `scripts/compute_regime_scores.py:95` (gleich `shared/anomaly_engine.py:197`): `(1 − (raw >= s).mean())·100`
  ist der Anteil **anomalerer** Tage → Rangfolge umgekehrt. Live in `regime_scores` (SPY): 15.10.2008 = 0/grün,
  16.03.2020 = 0/grün, 14.07.2017 = 73,4/rot, seit 05.10.2026 rot. Nightly Phase E schreibt nur SPY (letzte 7 Tage);
  in der Tabelle hat seit 01.09. nur SPY Werte (8.454 Zeilen).
- Isolation Forest auf der **ganzen** Historie trainiert, Rang über alle Tage → Zukunftswissen in historischen Werten.
- **Vier Fassungen:** Backend (IF, nur SPY, DB), `landing/js/dash-compute.js::computeRegime` (Watchlist), Inline-Kopie
  `landing/pages/dashboard.html:763` (Dashboard, jeder Ticker), Inline-Kopie `landing/pages/crash-fruehwarnung.html:199`
  (Rückfall ohne DB), dazu ein dritter Chart-Rückfall `crash-fruehwarnung.html:428` (`round(H·10)`, keine Perzentile).
  JS: Gewichtung 0,3·vol5 + 0,3·vol20 + 0,4·|DD20|, Rang gegen die letzten ≤ 252 Tage; die historischen Werte nutzen
  6/21 Renditen und 21 Schlüsse (aktuelle 5/20/20), Referenz enthält den aktuellen Tag.
- Rund 30 % aller Tage rot bei Grenzen 40/70; „Backtest"-Kacheln zählen nur Farben; Meta-Text verspricht einen
  „Backtest der Warnsignale"; Methodik-Text nennt Machine Learning und sieben statt acht Features.

## Nutzerentscheidungen (09.10.2026)
1. **Ein transparenter Stress-Score** statt Isolation Forest; Python und JS rechnen exakt dasselbe.
2. **Grenzen: Gelb ab 70, Rot ab 90** (Rang gegen die vorangegangenen zehn Jahre).
3. **Name „Stress-Ampel"**; „Frühwarnung"/„Crash-Prognose"/„Machine Learning" entfallen. Adresse `/crash-fruehwarnung` bleibt.

## D — Definition (eine Quelle je Sprache, gleiche Formel)
Eingabe: Kurszeilen eines Tickers aufsteigend, `close`. Zeilen mit ungültigem Schlusskurs (nicht endlich oder ≤ 0) werden
vorab entfernt; die Kurszeilen sind der Kalender (wie /plain-vanilla 1A/L4), keine Lückenauffüllung.
- r_i = c_i / c_{i−1} − 1.
- vol5_t = Stichproben-Standardabweichung (n − 1) von r_{t−4..t} (5 Renditen) × 100; vol20_t analog über r_{t−19..t}.
- dd20_t = (c_t / max(c_{t−19..t}) − 1) × 100 (20 Schlüsse einschließlich t, ≤ 0).
- S_t = 0,3·vol5_t + 0,3·vol20_t + 0,4·|dd20_t| (die bisherige JS-Gewichtung, jetzt mit einheitlichen Fenstern).
- Rang: Referenz W_t = S der **L = 2520** Sitzungen **vor** t (t−2520 … t−1; weniger, wenn die Historie kürzer ist).
  score_t = 100 · (#{S_j < S_t} + ½·#{S_j = S_t}) / |W_t|. Kein Wert (Zustand „zu kurze Historie"), wenn |W_t| < **756**.
- Ampel: score < 70 grün, 70 ≤ score < 90 gelb, ≥ 90 rot. Gespeichert ungerundet (eine Nachkommastelle in der DB wie
  bisher), angezeigt ganzzahlig. Grenzentscheidung auf dem gespeicherten Wert.
- Punkt-in-Zeit: S_t und W_t nutzen nur Kurse ≤ t → historische Werte sind die, die damals ausgegeben worden wären.
- Python: neues Modul `shared/stress_score.py` (`stress_reihe(df)` → DataFrame je Tag; `stress_aktuell(df)`).
  JS: `SA.dashCompute.computeStress(rows)` (aktuell) + `stressReihe(rows)` (Verlauf), ersetzt `computeRegime`.
- Rechenaufwand JS: Rang über 2520 Werte je Tag, nur für den angezeigten Zeitraum; für den aktuellen Tag einmal.

## B — Backend und Datenbank
- `scripts/compute_regime_scores.py` rechnet über `stress_score.stress_reihe`; sklearn entfällt dort.
  Spalten unverändert: `risk_score` = score, `traffic_light`, `vol_5d`, `vol_20d`, `drawdown`, `ret_1d/5d/20d` wie bisher,
  `vol_10d` weiter berechnet (Anzeige), `anomaly_score` = S_t (Rohwert des Stress-Maßes; Spaltenname bleibt, Bedeutung im
  Code und in `docs/` dokumentiert).
- `--full` für SPY: **erst** alle neuen Zeilen upserten, **danach** Zeilen dieses Tickers löschen, deren Datum nicht im
  neuen Satz ist (die ersten ~3 Jahre ohne Wert, Zeilen von Tagen, die es in der Kursreihe nicht mehr gibt). Vorher
  Sicherung der Tabelle für SPY als JSON auf dem Server. Andere Ticker mit Altwerten (vor 01.09.): ebenfalls neu rechnen
  oder ihre Zeilen entfernen — Vorschlag: neu rechnen für `--all-relevant` einmalig, Nightly bleibt bei SPY.
- Nightly Phase E: unverändert letzte 7 Tage upserten (Punkt-in-Zeit → deterministisch).
- `shared/anomaly_engine.compute_market_regime` (einziger Aufrufer `pages/_disabled/09_Crash_Fruehwarnung.py`):
  entfernen oder auf `stress_score` umleiten — Vorschlag: auf `stress_aktuell` umleiten, damit keine dritte Formel bleibt.

## F — Frontend
- `dash-compute.js::computeStress` ist die einzige JS-Rechnung; Inline-Kopien in `dashboard.html` und
  `crash-fruehwarnung.html` sowie der `round(H·10)`-Chart-Rückfall werden entfernt.
- `/crash-fruehwarnung`: Ampel und Verlauf aus der DB (SPY); Rückfall `computeStress`/`stressReihe` mit sichtbarer Quelle;
  Datenstand-Warnung bleibt. „Backtest"-Kacheln → „Verteilung" (Anteile Grün/Gelb/Rot im angezeigten Zeitraum, ohne
  Prognoseanspruch). Methodik-Text = die Definition oben, in Worten; FAQ und Meta ohne „Backtest der Warnsignale",
  „Frühwarnung", „Machine Learning", „Isolation Forest". Seite ist DE-only (kein `_EN_PAGE_META`).
- Dashboard und Watchlist: `computeStress` für jeden Ticker; bei < 756 Sitzungen Referenz „zu kurze Historie" statt
  Grün; Tooltips beschreiben Stress (Volatilität + Abstand vom 20-Tage-Hoch), keine Prognose. Grenzen 70/90 überall.
- Namen: `nav.crash_fruehwarnung` (DE+EN) → „Stress-Ampel"/„Stress light", Tour-Schritt, `price.feat_ki_crash`,
  Dashboard-/Watchlist-Labels, `flows.html`-Link, `seo/programmatic_seo_builder.py` (llms-Text), `<title>`/H1/Meta der
  Seite. `verify_seo_html.py` und `verify_en.py` müssen grün bleiben.

## P — Veröffentlichte Aussagen (Nutzerentscheidung, NICHT Teil des Codes)
Blogartikel mit inhaltlichen Aussagen über die Ampel, die schon heute nicht stimmen oder nach der Änderung nicht mehr:
`2026-05-14_dax-vs-sp500-saisonalitaet.md:89` („warnt bei DAX und S&P gleichermaßen" — gerechnet wird nur SPY),
`2026-05-14_sell-in-may-halbzeit-2026.md:79` („aggregiert mehrere Risikoindikatoren"),
`2026-04-18_fed-cuts-…:87` („Isolation-Forest-Regime-Score"), `2026-04-08_dashboard-launch.md:39` (Formelbeschreibung),
dazu die EN-Fassungen. Liste mit Vorschlagstext an den Nutzer; reine Linktexte („Crash-Frühwarnung") ebenfalls dort.

## Wächter `scripts/verify_stress_ampel.py` + `scripts/js/probe_stress_ampel.js`
- Handfall: kurze Reihe mit bekannten Renditen → vol5, vol20, dd20, S von Hand; Rangfall mit Gleichständen (½-Regel).
- Grenzen: |W| = 755 → kein Wert, 756 → Wert; Referenz endet bei t−1 (Mutation „t in der Referenz" muss reißen);
  Fenster 2520 (Wert 2521 Tage vorher fällt heraus).
- Ungültige Kurse (0, NaN, null) werden entfernt, nicht als Rendite 0 gezählt.
- Zwilling: Python `stress_reihe` = JS `stressReihe` auf allen fünf Snapshot-Tickern, jeder Tag, auf 1e-9 (score, S).
- Plausibilität auf dem Snapshot (SPY/^GSPC): score ≥ 90 am 15.10.2008, 16.03.2020, 08.04.2025; < 70 am 14.07.2017.
- Statisch: keine Inline-Rechnung mehr in `dashboard.html`/`crash-fruehwarnung.html`, kein `IsolationForest` im
  Schreibpfad, Grenzen 70/90 in Python und JS, verbotene Begriffe nicht im sichtbaren Text der Seite.
- Mutationen je Punkt + untaugliche Mutationen wie in /plain-vanilla 1A/1B.

## Messung (Information an den Nutzer, nicht auf der Seite)
Auf dem Snapshot: Anteile Grün/Gelb/Rot je Ticker; alte DB-Werte gegen neue (SPY); und als Einordnung ohne Anspruch:
Häufigkeit eines Rückgangs ≥ 10 % in den folgenden 20 Sitzungen nach Rot gegen die Basisrate.

## Prüfe besonders
- Ist die Gewichtung 0,3/0,3/0,4 auf unskalierten Größen vertretbar, oder sollten die Komponenten vor dem Mitteln selbst
  gerankt/standardisiert werden (Punkt-in-Zeit)? Die Nutzerentscheidung ist „transparent", nicht diese Gewichtung.
- L = 2520 / Mindestens 756 — sinnvoll, und was zeigt ein Ticker mit 2 Jahren Historie (Dashboard)?
- Reihenfolge Upsert → Delete beim Neurechnen; reicht die JSON-Sicherung?
- Fehlt ein Konsument (Newsletter, Health-Check, Completeness-Check, Watchlist-Summen „Im grünen Regime")?
