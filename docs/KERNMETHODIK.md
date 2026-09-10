# Kern-Methodik — normalisierte Renditen & Zeitindizes

> **Kanonische Doku für das, worauf alles andere steht.** Jede Saisonkurve, jeder
> KI-Score, jeder Backtest und jede Newsletter-Zahl entsteht aus den hier
> beschriebenen Funktionen. Ein Fehler hier ist kein lokaler Fehler.
>
> Stand: 2026-09-10 nach Review-Welle 1 (PRs #265–#270).

## 1. Die Regel

Prozentuale Renditen, normiert auf 100 — **nicht** absolute Preisänderungen.
Jedes Jahr startet bei 100, tägliche Log-Returns kumulieren darauf:

```
wert_j = 100 · exp( Σ r_1..r_j )
```

**Niemals** die TradingView-Methode (`close − close[lookback]`).

### Warum die Summe bei r_1 beginnt und nicht bei r_0

`log_return` ist in der DB **rückwärts** definiert — `LN(close / prev_close)`
(nachweisbar in `scripts/fix_tdom_trigger_and_log_returns.sql:37`). Der Wert
gehört damit zu **seiner eigenen** Zeile: er beschreibt die Bewegung, die zu
diesem Schlusskurs geführt hat.

Zeile 0 eines Jahres ist der Referenzpunkt (= 100). Ihr `log_return` beschreibt
den **Jahreswechsel** (letzter Handelstag des Vorjahres → erster dieses Jahres)
und darf deshalb nicht ins Jahr hineinkumuliert werden.

## 2. Die zwei Zwillinge

Dieselbe Mathematik existiert **zweimal**:

| | Backend | Frontend |
|---|---|---|
| Normalisierung | `shared/calculations.py::normalize_year` | `landing/js/seasonal-compute.js::buildYearData` |
| 365-Tage-Raster | `interpolate_to_365` | `_interpolateTo365` |
| Turn-of-Month | `shared/calculations.py::analyze_turn_of_month` | `seasonal-compute.js::analyzeTurnOfMonth` |

**Wächter: `py -3.14 scripts/verify_seasonal_twins.py`** (Exit 0 = deckungsgleich).
Das Skript bildet die JS-Logik bewusst *wörtlich* in Python nach und vergleicht
**beide** gegen die analytisch korrekte Kurve aus den Kursen. Bei jeder Änderung
an einer der beiden Seiten laufen lassen — vor dem Deploy.

> **Wichtig:** Übereinstimmung der Zwillinge ist **kein** Beleg für Richtigkeit.
> Der Turn-of-Month-Fehler (Abschnitt 4.11) steckte in **beiden** Implementierungen;
> der JS-Kommentar sagte ausdrücklich „1:1 wie Python". Gefunden hat ihn erst der
> Vergleich gegen die Sollkurve. Genau deshalb prüft `verify_seasonal_twins.py`
> drei Größen und nicht zwei.

## 3. `full_365` ist fortgeschrieben — `last_actual_day` ist die Grenze

Hinter dem letzten echten Handelstag eines Jahres ist `full_365` **konstant
gefüllt** (flache Linie bis Slot 365). Das ist gewollt: sonst bräche die
Durchschnittskurve über alle Jahre am Jahresende ab.

**Die Filterung gehört zum Konsumenten, nicht zum Erzeuger.**

| Darf über `full_365` rechnen | Muss bei `last_actual_day` aufhören |
|---|---|
| Mittelwert, Std-Abweichung, Detrend | Perzentil, Drawdown, Heatmap |
| Durchschnitts-Saisonkurve | Signifikanztest, Anomalie-Konfidenz |
| | Periodenstatistik (`calculate_period_stats`) |

Zentrale Quelle der Grenze: **`shared/calculations.last_actual_day(yd)`**
(Python) bzw. das Feld `last_actual_day`, das `buildYearData` mitliefert (JS).
Beide klammern auf 365.

## 4. Befunde der Review-Welle 1 (2026-09-10)

Externer Reviewer (Codex): 11 Befunde, alle gegengeprüft, alle behoben.
Zusätzlich **1 Befund, den der Reviewer nicht hatte** (4.11). PRs #265–#270.

### 4.1 Normalisierung war um eine Zeile verschoben — PR #265

`normalize_year` kumulierte `Σ r_0..r_{j-1}` statt `Σ r_1..r_j`. Folge: der
**Jahreswechsel-Return landete im Jahr** (bei +10 % Auftakt stand Tag 2 auf 110
statt 101), und der Return des **letzten Handelstags fiel weg**.

Das Frontend rechnete bereits richtig → die Zwillinge lieferten systematisch
verschiedene Kurven. Der Reviewer formulierte das neutral („einigt euch auf eine
Konvention"); gegengeprüft ist eindeutig JS korrekt.

> **Folgearbeit erledigt:** Der Fix ändert JEDE serverseitig berechnete
> Saisonkurve. Abgeleitete Caches wurden am 2026-09-10 neu gerechnet
> (`full_scanner_run.py`, 366 Ticker, 364 Erfolg / 2 ohne Daten / 0 Fehler).

### 4.2 Schaltjahre verloren den 31.12. — PR #266

`interpolate_to_365` lief über `range(1, 366)` → Tag 366 wurde nie ausgegeben.
Die Kurve endete am 30.12.; der letzte Handelstag fehlte in Jahresrendite und
Dezember-Statistik — **nur in Schaltjahren**, also still und unregelmäßig.
Tag 366 wird jetzt auf Slot 365 gefaltet (spätester Wert gewinnt). In **beiden**
Zwillingen.

### 4.3 TDOY/TDOM zählte Zeilen statt Kalendertage — PR #266

`backfill_tdoy` zählte über die **gespeicherten Zeilen**. Beginnt die Historie
eines Tickers am 1. Juli, bekam dieser Tag `tdoy=1` statt 124; eine Datenlücke
schob alle folgenden Indizes nach vorn (31.03. wurde TDOM 2 statt 22).

TDOY/TDOM sind Eigenschaften des **Kalenders**, nicht der Datenlage. Jetzt wird
je Jahr einmal der Handelstags-Kalender aufgebaut und jedes Datum darauf
nachgeschlagen.

### 4.4 TDOY im Frontend war nicht filterfest — PR #266

`tdom-analyse.html` zählte `tdoy_calc` durch — auch auf den per Indikator
**gefilterten** Zeilen. Fällt der 3. Januar dem Filter zum Opfer, wird der 4. zum
Handelstag 2, und die Top-25-Tabelle gruppiert unter dem falschen Tag mit
falschem Kalenderdatum. Die DB liefert `tdoy` bereits mit — sie wird jetzt
bevorzugt.

### 4.5 Laufendes Jahr zählte als abgeschlossen — PR #267

`calculate_period_stats` zählte **jedes** Jahr mit, auch das laufende. Dessen
„Periodenende" war der konstant fortgeschriebene letzte Kurs: eine Rendite über
einen Zeitraum, den es noch nicht gab, gezählt als abgeschlossenes Jahr in
Trefferquote und Mittelwert. Das Frontend schließt das laufende Jahr explizit
aus, das Backend nicht → die Zahlen wichen systematisch voneinander ab.

Der Fix prüft schärfer als „laufendes Jahr raus": ein Jahr zählt nur, wenn seine
**echten Beobachtungen bis zum Periodenende reichen**. Das erwischt auch Jahre
mit abgeschnittenem Ende (Delisting, Datenlücken).

### 4.6 Ein NaN riss alle Jahre mit — PR #267

Ein einzelnes nicht-endliches `log_return` machte über `exp(cumsum)` die ganze
Jahreskurve zu NaN — und `calculate_seasonal_average` mittelt darüber, also wurde
der Saison-Durchschnitt **aller** Jahre NaN und der Chart leer. Das Frontend
rechnete solche Lücken aus den Closes nach und zeichnete weiter: die Zwillinge
divergierten genau dann, wenn die Daten unsauber sind.

Backend repariert jetzt ebenso aus den Closes; ist das unmöglich, wird nur
**das** Jahr verworfen statt aller anderen.

> **Korrektur an der eigenen Doku:** Die NaN-Ausbreitung war zwischenzeitlich als
> beabsichtigt dokumentiert („soll auffallen"). Das war falsch — ein NaN-Jahr
> macht den Durchschnitt **aller** Jahre unbrauchbar, und zwar unsichtbar.

### 4.7 `last_actual_day` wurde nie gesetzt — PR #268

Schärfer als gemeldet: `dashboard.html` filtert an vier Stellen mit
`yearData[y].last_actual_day || 365` — der gemeinsame Builder lieferte das Feld
aber **nie**. Der Fallback griff also immer, **die Schutzabfrage war toter Code**.
Laufender Drawdown und „aktuelle" Kurve liefen flach bis Tag 365 weiter, als
wären es echte Beobachtungen.

### 4.8 Fortschreibung floss in Statistik, Heatmap und Anomalie — PR #269

Drei produktive Stellen rechneten die flache Linie als echte Beobachtung mit:

- **`shared/anomaly_engine.py`** — Monate des laufenden Jahres, die noch gar
  nicht stattgefunden haben, lieferten exakt 0 % Rendite und gingen als
  „normaler Monat" in die Anomalie-Konfidenz ein.
- **`blog/blog_builder.py`** — die **veröffentlichte** Monats-Heatmap zeigte für
  die Restmonate des laufenden Jahres 0,00 %: nicht als Lücke erkennbar, sondern
  wie gemessene Nullmonate. Jetzt leere Zelle.
- **`landing/pages/jahreszyklus.html::renderSignificance`** — dieselbe Null floss
  in den Signifikanztest für Monat/Quartal/Zyklus. Die Seite baut
  `last_actual_day` bereits selbst und nutzt es in der Month-×-Offset-Heatmap —
  nur hier nicht.

Bewusst **nicht** angefasst: `pages/02_Jahreszyklus.py` (Streamlit-Legacy,
produktseitig ungenutzt).

### 4.9 Multi-Ticker-Verschmutzung in TDOM — PR #265

- `add_tdom_columns` gruppierte nur nach `year`/`month` → in einem DataFrame mit
  mehreren Tickern zählten die SAP-Zeilen den AAPL-Zähler weiter.
- `calc_strategy_returns` nutzte `shift(-1)` über die ganze Tabelle → die
  Overnight-Rendite am letzten AAPL-Tag war AAPL-Open gegen **SAP**-Open.

Beides gruppiert jetzt nach Ticker; der letzte Tag eines Tickers wird korrekt NaN.

### 4.10 Fehlschlag meldete sich als Erfolg — PR #265

`backfill_tdoy` verschluckte Upsert-Fehler: warnen, weiterlaufen, Exit 0,
„Fertig" melden. **Monitoring stand grün, während Zeilen veraltet blieben.**
Jetzt werden Fehlschläge gezählt und mit Exit 1 gemeldet.

### 4.11 Turn-of-Month war einen Handelstag zu spät — PR #270 ⚠️

**Nicht aus dem Reviewer-Bericht** — beim Gegenprüfen von Befund 4.1 aufgefallen.

`analyze_turn_of_month` (Python) und `analyzeTurnOfMonth` (JS) kumulierten mit
`cumsum(insert(log_rets, 0, 0)[:-1])`. Das ordnet jeden Tagesschritt der
**folgenden** Zeile zu.

Nachweis: ein Fenster, in dem sich ausschließlich Tag t+1 um +5 % bewegt, zeigte
die Bewegung auf t+2. Nach dem Fix steht sie auf t+1.

#### Es war eine Fehlerfamilie, kein Einzelfall — PR #271

PR #270 korrigierte die beiden Zwillinge, suchte aber nicht, **wo dasselbe Muster
sonst noch steht**. Es stand an fünf Stellen — offenbar beim Bau jeder neuen
Fenster-Analyse mitkopiert:

| Fundstelle | Wirkung |
|---|---|
| `monatswechsel.html::buildCurrentYearTOMCurves` | **dritte** ToM-Kopie; im selben Chart lag die Kurve des laufenden Jahres nach #270 einen Tag neben der historischen |
| `seasonal-compute.js::analyzeMoonEffect` | live auf `/mondphasen` |
| `scripts/video/render_lunar_charts.py` | Port davon — Kommentar sagte „1:1 wie JS" und war es auch: gleich falsch |
| `shared/holidays.py::analyze_holiday_effect` | Feiertags-Fenster |
| `pages/06_Mondphasen.py`, `pages/03_Monatszyklus.py` | Streamlit-Legacy, aber die dokumentierten Zwillinge der JS-Seite |

Geprüft und **nicht** betroffen: `feiertage.html` (rechnet aus rohen Closes
relativ zum Basis-Close) und `strategy-compute.js::calc_downmonth_tom` (siehe
unten).

> ### ⚠️ Offene Folge — präzisiert
> Betroffen sind die **Kurven** der Fenster-Analysen (`/monatswechsel`,
> `/mondphasen`, Feiertage, Lunar-Videos): jede Bewegung stand einen Handelstag
> zu spät. Diese Seiten rechnen live im Browser und sind mit dem Fix erledigt.
>
> **Der Backtest „SPY Down-Month ToM Reversal" ist NICHT falsch gerechnet** —
> `calc_downmonth_tom` nutzt `_nthTradingDay` und echte Closes, nicht die
> kumulierte Reihe. (Die ursprüngliche Folgenabschätzung in PR #270 war hier
> zu weit gefasst.)
>
> **Was offen bleibt:** die *Parameter* der Strategie (Einstieg TDOM 14,
> Haltedauer 13) wurden aus der verschobenen Kurve abgelesen. Sie können also um
> einen Handelstag danebenliegen. Sharpe 0,34 · WR 72 % · PF 2,39 sind damit
> korrekt gerechnet, aber möglicherweise für den falschen Einstiegstag optimiert.
> **Das ist eine Neu-Optimierung, keine Neuberechnung** — die Zahlen sind
> zitierfähig, solange dabei steht, dass der Einstiegstag noch nachoptimiert wird.

## 4b. Zweite Prüfrunde (2026-09-11) — was die erste übersehen hat

Der externe Reviewer bekam die 12 Korrekturen zur Abnahme: **7 bestätigt,
5 unvollständig**, dazu **7 neue Befunde**. Alle gegengeprüft, alle behoben
(PR #272). Zwei davon waren Fehler, die **die Korrekturen selbst** eingebaut
hatten — der wichtigste Ertrag dieser Runde.

### Lexikografische Monatsschlüssel — der schwerste Fund

`analyzeTurnOfMonth` gruppiert nach `y + '-' + m` **ohne Nullpadding** und nimmt
den nächsten *sortierten* Schlüssel als Folgemonat. Sortiert wird als String:

```
"2024-1" < "2024-10" < "2024-11" < "2024-12" < "2024-2" < … < "2024-9"
```

Damit zog der **Januar Oktober-Daten**, der **Dezember Februar-Daten** und der
**September den Januar des Folgejahres** — 3 von 12 Monaten falsch, live auf
`/monatswechsel`. Python rechnet `next_month = month + 1` explizit und war
korrekt: ein reiner Zwillings-Drift, den Welle 1 nicht gesehen hat, weil sie auf
die *Kumulation* schaute und nicht auf die *Fensterbildung*.

Behoben durch Nullpadding **plus** Nachbarschaftsprüfung — bei einer Lücke in der
Historie hätte die Sortierung sonst Januar mit März gepaart.

### Zwei Überkorrekturen aus Welle 1

**Vollständige Jahre wurden verworfen.** Fix 4.5 verlangte Beobachtungen bis
Kalendertag 365. Ein abgeschlossenes Jahr endet aber fast nie am 31.12.: XETRA
schließt am 30.12., die NYSE hatte 2006/2017/2023 ihren letzten Handelstag am
29.12. Gemessen über 2000–2025 warf die Regel **7 von 26 NYSE- und 15 von 26
XETRA-Jahren** weg. Zwischen letztem Handelstag und Silvester ist die
Fortschreibung **exakt** — es wurde nicht gehandelt.

Neu deshalb `year_end_reference()` + `year_covers()`: die Referenz ist nicht 365,
sondern **wie weit ein vollständiges Jahr dieses Tickers reicht**.
Selbstkalibrierend, ohne den Börsenkalender zu kennen. Dieselbe Überkorrektur
steckte in `blog_builder` (Dezember-Spalte) und in `jahreszyklus.html`
(Monats-/Quartals-Signifikanz).

**Die Zwillinge divergierten bei kaputten Daten.** JS setzte bei nicht
rekonstruierbarem `log_return` still `lr = 0`, Python verwarf das Jahr. Jetzt
verwerfen beide — ein stiller Nullwert ist eine erfundene Beobachtung und
verschiebt den gesamten restlichen Jahresverlauf.

### Drei Stellen, die weiter ungefiltert rechneten

- `jahreszyklus.html::periodStats` filterte **gar nicht** — das direkte
  Gegenstück zu `calculate_period_stats`, wo Welle 1 den Filter einbaute. Seite
  und Backend zeigten dadurch verschiedene Trefferquoten.
- Der Zyklus-Zweig der Signifikanz: das laufende Jahr trug seine **YTD**-Rendite
  als volle Jahresrendite in die Präsidentenzyklus-Gruppe ein.
- `blog_builder` Monatszyklus: im September flossen Oktober bis Dezember als
  exakt 0 % in den **veröffentlichten** Monatsdurchschnitt.

### Mehrticker-Verschmutzung, dritte Fundstelle

`calc_tdom_range_return` gruppierte nach `(year, month)` ohne Ticker — Welle 1
hatte das in `add_tdom_columns` und `calc_strategy_returns` behoben, diese
Funktion aber übersehen. Zwei verschachtelte Ticker ergaben eine Zeile mit
~110 % statt zwei Zeilen mit 4 % und 2 %.

### Der Wächter prüfte eine Fiktion

`verify_seasonal_twins.py` verglich Python gegen einen **handgeschriebenen
Python-Nachbau** der JS-Logik. Der kann selbst von der Quelle driften — dann
zertifiziert der Wächter etwas, das im Browser gar nicht läuft.

Neu: **Block 4 führt die echte `seasonal-compute.js` in node aus**
(`scripts/js/twin_probe.js`, ein `window`-Stub genügt). Dazu abgedeckt sind jetzt
`interpolate_to_365` und `analyze_turn_of_month` — beide vorher ungeprüft, und
genau die ToM-Lücke hat die Fehlerfamilie durchschlüpfen lassen.

Gegenprobe gemacht: entfernt man das Nullpadding, fällt Block 4 rot aus. Ein
zwischenzeitlich gebauter **textueller** Quellcode-Check hatte es **nicht**
gefangen — er traf einen unbeteiligten Datums-Helfer in derselben Datei.

## 5. Lessons

- **Zwillinge, die übereinstimmen, können beide falsch sein.** Ein
  Zwillings-Vergleich braucht eine **dritte, unabhängig hergeleitete** Referenz —
  hier die aus den Kursen gerechnete Sollkurve. Ohne die wäre 4.11 unsichtbar
  geblieben, denn der JS-Kommentar behauptete ausdrücklich Gleichheit.
- **Off-by-one in kumulierenden Reihen zeichnet plausible Kurven.** Weder 4.1
  noch 4.11 sahen im Chart falsch aus. Solche Fehler findet man nur mit einem
  Testfall, bei dem sich **genau ein** Tag bewegt.
- **Nach einem Fix nach dem MUSTER suchen, nicht nur nach der Funktion.** Der
  ToM-Versatz saß an fünf Stellen; PR #270 fixte zwei. Ein Copy-Paste-Muster
  (`cum[0]=0`, dann Schritt j auf Zeile j+1) verbreitet sich mit jeder neuen
  Fenster-Analyse. Nach jedem Fix an geteilter Mathematik: `grep` auf die
  **Code-Form**, nicht auf den Funktionsnamen.
- **Die Folgenabschätzung eines Fixes selbst gegenprüfen.** PR #270 erklärte den
  Backtest für betroffen, ohne dessen Code zu lesen — er war es nicht. Eine zu
  weit gefasste Warnung kostet echte Arbeit und macht die nächste Warnung
  unglaubwürdiger.
- **Constant-Fill ist eine Design-Entscheidung mit Konsumenten-Pflicht.** Wer
  `full_365` liest, muss wissen, ob er hinter `last_actual_day` weiterrechnen
  darf. Die Grenze gehört deshalb an **eine** Stelle (`last_actual_day()`), nicht
  in jede aufrufende Datei.
- **Eine Schutzabfrage gegen ein nie gesetztes Feld ist schlimmer als keine** —
  sie sieht im Code nach Absicherung aus (4.7).
- **Externe Befunde gegenprüfen, nicht umsetzen.** Bei 4.1 nannte der Reviewer
  zwei gleichwertige Konventionen; tatsächlich war eine Seite eindeutig falsch.
  Ungeprüftes Umsetzen hätte hier das *Frontend* kaputtgemacht.
- **Ein Fix kann schlimmer sein als der Fehler.** Zwei der Welle-1-Korrekturen
  überschossen: die Jahresfilterung warf jedes zweite abgeschlossene XETRA-Jahr
  weg. Wer eine Bedingung verschärft, muss messen, **wie viel** sie wegwirft —
  nicht nur, ob sie den gemeldeten Fall erwischt.
- **Ein Wächter, der einen Nachbau prüft, prüft eine Fiktion.** Er muss den
  Code ausführen, der wirklich läuft. Und man muss ihn absichtlich kaputt
  machen, um zu sehen, ob er rot wird — der textuelle Check hier bestand,
  während der Fehler drin war.
- **Datenkorrekturen ziehen Cache-Arbeit nach sich.** Nach 4.1 waren
  `monthly_stats`, `ki_scores` und `scanner_results` bis zum Rerun inkonsistent
  zum Frontend.

## 6. Prüfliste bei Änderungen an der Kern-Methodik

1. `PYTHONUTF8=1 py -3.14 scripts/verify_seasonal_twins.py` → Exit 0
2. `py landing/verify_en.py` → FAIL unverändert (vorbestehend: `nav.kalender`)
3. Testfall mit **genau einer** Bewegung bauen, wenn eine kumulierende Reihe
   angefasst wurde
4. Wurde eine der beiden Zwillings-Seiten geändert? → die andere mit ändern
5. Ändert sich eine serverseitig gerechnete Größe? → abgeleitete Caches neu
   rechnen (`scripts/full_scanner_run.py`)
