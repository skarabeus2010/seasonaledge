# Methodik-Prüfung: Crash-Ampel, KI-Composite-Score, Anomalie-Radar

Stand 2026-10-08, read-only. Kennzeichnung: **[Code]** = am Code belegt, **[Messung]** = selbst nachgerechnet auf dem Kurs-Snapshot vom 07.10.2026 (`pv_kurse/*.json`, Python 3.14, sklearn 1.8.0), **[plausibel]** = Schluss ohne eigene Messung. Hilfsskripte: `scratchpad/agent_kennzahlen/{regime,jsreg,ki,ki2,anom,anom_py}.py`.

Wichtigster Einzelbefund vorab: **Der Risk-Score der Crash-Ampel ist im Vorzeichen vertauscht.** Die Seite `/crash-fruehwarnung` zeigt an Crash-Tagen Grün (Score ≈ 0) und in ruhigen Phasen Rot. Heute (07.10.2026) zeigt sie nach meiner Nachrechnung Rot (85), das Dashboard für denselben Tag Grün (13).

---

## 1. Crash-Ampel / Crash-Frühwarnung

### Definition
Es gibt **drei** Rechenwege mit demselben Namen:

| Ort | Verfahren | genutzt von |
|---|---|---|
| `scripts/compute_regime_scores.py:41-129` | Isolation Forest (IF) auf 10 Merkmalen: `ret_1d`, `vol_5/10/20d` (rollierende Std der Tagesrendite), `ret_5/10/20d`, Drawdown vom 20-Tage-Hoch (`:66-82`). `contamination=0.05`, `random_state=42` (`:87`). Training und Bewertung auf **der ganzen Historie** (`:88-91`). Score = Perzentil (`:94-97`), Ampel ≥70 rot / ≥40 gelb (`:100-107`). Nightly schreibt nur SPY, nur die letzten 7 Tage (`scripts/nightly_refresh.py:399-409`). | `/crash-fruehwarnung` (lädt `regime_scores`, `crash-fruehwarnung.html:301,313-325`), Weekly-Report (`shared/weekly_report.py:84-126`, Template `scripts/templates/weekly_report.html.j2:95,258`) |
| `landing/js/dash-compute.js:246-303` (+ Inline-Kopien `dashboard.html:763-797`, `crash-fruehwarnung.html:199-263`) | Gewichtete Summe `0,3·vol5 + 0,3·vol20 + 0,4·|DD20|` (`:280,283`), Perzentil dieses Werts unter den letzten 252 Handelstagen (`:268,284-285`), dieselben Schwellen 40/70. Die Renditen (`ret_1d/5d/20d`) werden berechnet, gehen aber nicht in den Score ein. | Dashboard (`dashboard.html:2127`), Watchlist (`watchlist.html:465`), Fallback auf `/crash-fruehwarnung` wenn die DB leer ist |
| `shared/anomaly_engine.py:141-223` (`compute_market_regime`) | IF wie oben, nur letzter Tag | nur die stillgelegte Streamlit-Seite `pages/_disabled/09_Crash_Fruehwarnung.py:55` |

### Vorzeichenfehler (Priorität HOCH)
**[Code]** `compute_regime_scores.py:91` kommentiert richtig „Negativer = anomaler" (sklearn: niedrige `decision_function` = Ausreißer). Die Umrechnung `:95` lautet aber `(1 - (raw_scores >= s).mean()) * 100` = Anteil der Tage, die **anomaler** sind als der bewertete Tag. Der anomalste Tag bekommt 0, der normalste ≈ 100. Die FAQ der Seite (`crash-fruehwarnung.html:162`) beschreibt das Gegenteil („anomaler als rund 70 Prozent"). Dieselbe Umkehr steckt in `anomaly_engine.py:197-198`.

**[Messung]** Exakter Nachbau von `compute_regime_scores` auf SPY (8.460 Tage, 1993–2026):

| Tag | Vol20 | DD vom 20T-Hoch | Risk-Score | Ampel |
|---|---|---|---|---|
| 15.10.2008 | 5,24 % | −27,5 % | 0,0 | grün |
| 16.03.2020 | 4,85 % | −29,1 % | 0,0 | grün |
| 08.04.2025 | 1,98 % | −13,7 % | 1,3 | grün |
| 14.07.2017 | 0,54 % | 0,0 % | 92,0 | **rot** |
| 07.10.2026 (letzter Tag) | 0,66 % | −0,24 % | 85,4 | **rot** |

Korrelation Risk-Score mit Vol20 = −0,62, mit |DD| = −0,58. Median-Vol20 je Ampel: grün 1,29 / gelb 0,75 / rot 0,64.

Einschränkung: Die DB-Werte selbst habe ich nicht gelesen (kein DB-Zugriff). Die Kurse im Snapshot stammen aber aus derselben öffentlichen prices-Abfrage, und der Code ist eindeutig. Der Fehler sollte vor jeder weiteren Diskussion live gegengeprüft werden (eine Zeile aus `regime_scores` für 2020-03-16 genügt).

### Zwillinge
- **[Code+Messung]** IF-Pfad und JS-Pfad messen in entgegengesetzter Richtung. Am 07.10.2026: IF 85 (rot) auf `/crash-fruehwarnung`, JS-Composite 13 (grün) auf Dashboard/Watchlist. An den Crash-Tagen umgekehrt (JS 100 = rot, IF ≈ 0 = grün).
- Auch ohne Vorzeichenfehler sind sie nicht vergleichbar: IF = Perzentil über die ganze Historie seit 1993, 10 Merkmale inkl. Renditen; JS = Perzentil über die letzten 252 Tage, 3 Merkmale, feste Gewichte.
- **[Code]** Innerhalb des JS-Pfads unterscheiden sich das Merkmal des aktuellen Tags und das der Vergleichstage: aktuell 5 bzw. 20 Renditen (`dash-compute.js:255`), historisch 6 bzw. 21 (`:270,274`); Drawdown-Fenster 20 gegenüber 21 Schlusskursen (`:263` gegenüber `:278`). Klein, aber eine Messung gegen eine leicht andere Größe.
- **[Code]** Die Seitenbeschreibung „Perzentil über die letzten 252 Handelstage" (`crash-fruehwarnung.html:158`, Meta `:8`) trifft nur auf den JS-Fallback zu, nicht auf den angezeigten IF-Wert.

### Look-ahead / Datenrand
- **[Code]** Das IF wird auf allen Tagen trainiert und das Perzentil über alle Tage gebildet (`:88,94-97`). Bei `--full` hängt jeder historische Score von späteren Kursen ab (Zukunftswissen in der Historienkurve). Im Nightly-Betrieb werden nur die letzten 7 Tage neu geschrieben (`nightly_refresh.py:405-409`), also stammt jeder ältere Tag von einem anderen, damals trainierten Modell. Die Historienkurve ist damit eine Mischung aus Modellständen, keine Zeitreihe einer festen Messung.
- **[Code]** Am rechten Rand ist der bewertete Tag Teil der Trainingsmenge (in-sample). Bei IF unkritischer als bei überwachten Modellen, aber nicht dasselbe wie eine Bewertung neuer Daten.
- **[Code]** Fehlende Daten: die Seite warnt bei > 4 Tagen Alter (`crash-fruehwarnung.html:489-493`), zeigt aber trotzdem den alten Wert als aktuelle Ampel. Ist die DB leer, fällt sie still auf den JS-Rechenweg mit anderer Methodik zurück (`:326-328`); der Wechsel steht nur klein im Score-Text.
- **[Code]** Das Dashboard rechnet live aus Kursen, die Crash-Seite liest eine Tabelle. Dieselbe Ampel kann also auch aus Aktualitätsgründen auseinanderlaufen.

### Statistische Aussagekraft
- **[Code+Messung]** Beide Ampeln sind **Perzentile mit festen Grenzen**: Rot ist per Konstruktion ~30 % aller Tage, Gelb 30 %, Grün 40 % (gemessen: IF 30,0/30,0/40,0 %; JS 30,1/30,8/39,0 %). „Stark anomal — historisch selten" (`crash-fruehwarnung.html:186`) ist damit falsch: Rot an knapp jedem dritten Handelstag ist der Normalzustand.
- **[Code]** Die Schwellen 40/70 sind gesetzt, nirgends begründet oder kalibriert. `contamination=0.05` ist ebenfalls gesetzt und wirkt sich auf die Perzentilskala nicht aus (das Perzentil hängt nur von der Rangfolge ab).
- **[Code]** Das IF ist richtungsblind: `ret_1d/5d/20d` gehen symmetrisch ein, eine starke Rally ist so „anomal" wie ein Einbruch. Für eine **Crash**-Ampel ist das die falsche Größe.
- **[Messung, in-sample, nur zur Einordnung]** Mit richtig herum gedrehtem Score hat Rot eine erhöhte Wahrscheinlichkeit für einen Rückgang ≥ 10 % in den folgenden 20 Handelstagen (8,9 % gegenüber Basisrate 3,95 %, Grün 1,3 %). Gleichzeitig ist die mittlere 20-Tage-Rendite nach Rot **höher** (+1,35 % gegenüber +0,64 % nach Grün). Das ist Volatilitäts-Clustering, keine Richtungsprognose. Mit dem tatsächlich implementierten (vertauschten) Score ist es umgekehrt: Grün geht den meisten großen Rückgängen voraus (7,4 % gegenüber Rot 1,2 %).
- **[Code]** Eine Validierung (Trefferquote, Vorlauf vor Crashs, Fehlalarme) existiert nicht. Die Meta-Beschreibung verspricht einen „historischen Backtest der Warnsignale" (`:8`); angezeigt werden nur die Score-Kurve und die Anteile der drei Farben (`:496-509`).

### Darstellung gegenüber Messung
- „Frühwarnung", „Crash", „KI", „Machine Learning" gegenüber einem Perzentil aktueller Volatilität/Drawdowns, das per Definition rückwärts schaut (die Seite sagt das in `:159` selbst). Ein Indikator, der auf bereits eingetretene Bewegungen reagiert, warnt nicht früh.
- Ampelfarben + „Stress-Regime" + Polymarket-Teaser „wenn beide rot sind, steigt die Konfidenz" (`:132`) behaupten eine Aussagekraft, die nicht gemessen ist.
- Das Dashboard trägt die Überschrift „Crash-Ampel (Port von crash-fruehwarnung.html)" (`dashboard.html:762`), rechnet aber den JS-Weg, nicht das IF.

### Urteil: **sofort abschalten bzw. Vorzeichen korrigieren (HOCH), danach Methodik ändern und umbenennen (HOCH)**
1. Sofort: Umrechnung in `compute_regime_scores.py:95` auf `(raw_scores > s).mean() * 100` drehen (und `anomaly_engine.py:197` ebenso), `--full` neu rechnen, Live-Abruf der Seite prüfen. Bis dahin die Ampel auf der Seite und im Weekly-Report ausblenden.
2. Eine einzige Definition für Seite, Dashboard, Watchlist und Report. Mein Vorschlag: den einfachen, nachvollziehbaren Weg (gerichtete Merkmale: realisierte Vola, Drawdown vom 52-Wochen- oder 20-Tage-Hoch) statt IF, mit **expandierendem** Fenster (nur Vergangenheit) für die Historie.
3. Umbenennen in „Stress-Ampel" / „Marktstress-Indikator", „KI"/„Frühwarnung" streichen, Rot-Anteil (30 %) offen nennen oder Schwellen auf seltene Zustände legen (z. B. 90./97. Perzentil).
4. Validierung vorab festlegen: Ereignis = Rückgang ≥ 10 % (bzw. ≥ 20 %) vom Hoch innerhalb 20/60 Handelstagen; Score nur aus Daten bis t; Out-of-Sample ab 2008 (SPY) bzw. ab 1960 (^GSPC); Vergleich mit naiven Basen (VIX > 25, Vol20 > Median, Kurs < 200-Tage-Linie). Kennzahlen: Trefferquote, Fehlalarmquote, Vorlauf in Tagen, Brier/Kalibrierung.

---

## 2. KI-Composite-Score

### Definition (Frontend, das der Nutzer sieht)
`landing/js/dash-compute.js:176-243` (identische Inline-Kopie `dashboard.html:706-760`, leicht abweichende Kopie `ki-saisonalitaet.html:464-532`):
- Eingaben: Jahreskurven `full_365` (je Jahr Start 100, kumulierte Log-Renditen, auf 365 Kalendertage interpoliert, `seasonal-compute.js:309-366`), Match-Jahre aus `findMatchingYears` (`dash-compute.js:112-146`): Pearson-Korrelation der **Kursniveaus** Tag 1…heute, Ähnlichkeit `(r+1)/2·100`, Top 5.
- s1 Musterpfad (`:181-182`): Anteil der Top-5-Jahre mit positiver **Gesamtjahres**-Rendite.
- s2 Trend (`:185-192`): ähnlichkeitsgewichteter Pfad der Top-5, Veränderung heute → +30 Kalendertage, linear −3 %…+3 % → 0…1.
- s3 Win-Rate (`:195-208`): Anteil aller Vorjahre mit positivem aktuellem Kalendermonat.
- s4 Tracking (`:212-226`): `0,7·max(0, r) + 0,3·(1 − MAE/Spannweite)` zwischen laufendem Jahr und Saisondurchschnitt.
- Summe × 2,5, Schwellen ≥ 6,5 bullish / ≤ 3,5 bearish (`:228-231`). Gleiche Gewichte, Schwellen und Skalierung (±3 %) sind gesetzt, nirgends begründet.

### Zwillinge — mindestens vier Fassungen
- **[Code]** Dashboard: Zeitraum-Standard 15 Jahre (`dashboard.html:248`, Filter `:2109-2112`), fest Pearson/Top 5/Glättung 5 (`:2121-2122`). KI-Seite: Standard 10 Jahre (`ki-saisonalitaet.html:130`, Filter `:805-809`), Methode/Top-N/Glättung frei wählbar (`:770-786`). Watchlist: `SA.dashCompute` mit den übergebenen Zeilen. → Derselbe Ticker hat am selben Tag auf Dashboard und KI-Seite verschiedene Scores, schon mit Standardeinstellungen.
- **[Code]** `ki-saisonalitaet.html:427-436` berechnet den Musterpfad ohne Null-Prüfung und mit `rollingMean`, `dash-compute.js:148-173` überspringt Nullwerte. Bei vollständigem `full_365` gleich, bei Lücken nicht.
- **[Code]** Backend `shared/ki_score.py` (Scanner, `scanner_results`, Nightly über `cache_manager.get_or_compute_ki_score`) rechnet etwas anderes:
  - s1 über `ai_models.find_similar_years` (DTW via `fastdtw`, `ai_models.py:32-52`). `fastdtw` steht **nicht** in `requirements.txt`, also greift im Container der Korrelations-Fallback (`ai_models.py:35-36,55-72`) — die Seite spricht trotzdem von „DTW" (`ki-saisonalitaet.html:204`). [Code; Containerinhalt nicht live geprüft]
  - s2 = Prophet-Prognose (`ki_score.py:92-130`). Das Nightly läuft mit `quick_mode=True` (`nightly_refresh.py:247`), der Full-Scanner je nach Flag (`full_scanner_run.py:218`); `prophet` steht aber ebenfalls nicht in `requirements.txt`, der Rückfall `ImportError → None` (`ai_models.py:92-94`) greift also in beiden Modi → **s2 ist konstant 0,5**, also 1,25 Punkte fix.
  - s4 nutzt `trading_days_so_far = len(days)` (Anzahl Handelstage, `ki_score.py:254`) als Index in die **Kalendertag**-Achse `full_365` (`:187-192`). Am 07.10.2026 (Kalendertag 280, 192 Handelstage) vergleicht es also nur 1.1.–11.7. **[Code+Messung der Tageszahl]** Fehler.
  - s3 über `calculate_period_stats` (nur vollständige Jahre), Frontend über alle Vorjahre ohne diese Prüfung.
  - Zeitraum 20 Jahre (`nightly_refresh.py:247`).
  → Der „KI-Score" in Scanner/Briefing und der auf Dashboard/KI-Seite sind verschiedene Größen mit gleichem Namen und gleichen Schwellen.

### Look-ahead / Datenrand
- **[Code]** Live kein Zukunftswissen: Match-Jahre sind abgeschlossene Vorjahre. Aber s1 nutzt die **Gesamtjahresrendite** der Match-Jahre, und die Match-Jahre sind gerade über ihren YTD-Verlauf ausgewählt. s1 enthält damit zu großen Teilen den bekannten YTD-Verlauf des laufenden Jahres. **[Messung]** Walk-forward auf ^GSPC: Spearman(YTD-Rendite, s1) = 0,73, (YTD, Composite) = 0,62; ^GDAXI 0,69 / 0,56. Der Score ist überwiegend ein Momentum-/YTD-Maß.
- **[Code]** Der Saisondurchschnitt `avg` enthält das laufende Jahr selbst (`calculateSeasonalAverage` mittelt über alle Schlüssel, `seasonal-compute.js:373-389`), nach dem letzten Handelstag konstant fortgeschrieben. s4 vergleicht das laufende Jahr also teilweise mit sich selbst.
- **[Code]** s4 ist richtungslos: ein Jahr, das dem Durchschnitt eng folgt, bekommt hohe Punkte — das ist eine Aussage über Musterkonformität, keine bullishe Information, wird aber in ein Bullish/Bearish-Signal addiert.
- **[Code]** `todayDoy()` kommt aus der Browseruhr, nicht aus dem letzten Datenpunkt (`dash-compute.js:102-105`). In den ersten neun Tagen des Jahres ist `currentSeg.length < 10` → keine Matches → s1 = s2 = 0,5 (`:117,182,186`).
- **[Code]** Der erste, unvollständige Datenjahrgang (z. B. SPY 1993 ab 29.01.) wird wie ein volles Jahr verwendet (Werte vor dem Start konstant, `seasonal-compute.js:469`), sofern er im Zeitraumfilter liegt.
- Ausreißerbereinigung (`outlier_manager.py`/`detect_outlier_years`): im Frontend-Score nicht beteiligt; nur in Legacy-Streamlit-Seiten genutzt. [Code, grep]

### Statistische Aussagekraft
**[Messung]** Walk-forward-Nachbau des Frontend-Scores (Dashboard-Variante: Pearson, Top 5, Glättung 5, nur die 15 Jahre **vor** dem Bewertungsjahr; Bewertung am 15. jedes Monats Jan–Nov; Ziel: Rendite der folgenden 30 Kalendertage):

| Index | n | Score Ø | Anteil Bullish / Neutral / Bearish | Spearman(Score, fwd30) |
|---|---|---|---|---|
| ^GSPC 1910–2025 | 1.276 | 5,43 | 31 % / 54 % / 15 % | 0,015 (p 0,60) |
| SPY 2008–2025 | 198 | 6,15 | 44 % / 53 % / 3 % | −0,017 (p 0,81) |
| ^GDAXI 1974–2025 | 572 | 5,52 | 31 % / 56 % / 13 % | 0,071 (p 0,09) |

Folgerendite je Signal, ^GSPC: Bullish +0,50 %, Neutral +0,60 %, Bearish −0,06 % (alle +0,47 %). ^GDAXI: +0,73 / +0,73 / +0,03 %. Bullish ist nirgends besser als Neutral. Bearish liegt bei ^GSPC und ^GDAXI etwas niedriger, bei kleinen Fallzahlen, ohne Korrektur für Mehrfachprüfung und mit p-Werten, die die Abhängigkeit innerhalb eines Jahres ignorieren — kein belastbarer Effekt. Kein einzelner Sub-Score hat eine nennenswerte Rangkorrelation (|ρ| ≤ 0,11).

Struktur: s1 hat bei Aktienindizes eine hohe Basisrate (Ø 0,70–0,87), s3 ebenfalls (Ø 0,55–0,62). Der Score ist dadurch nach oben verschoben; bei SPY liegt der Mittelwert (6,15) fast auf der Bullish-Schwelle. Die Schwellen 6,5/3,5 sind gesetzt, nicht kalibriert. Die Sub-Scores sind nicht „unabhängig" (Tooltip `ki-saisonalitaet.html:212`): s1 und s2 kommen aus denselben fünf Jahren, s1 und s4 hängen beide am YTD-Verlauf.

### Darstellung gegenüber Messung
- „KI", „Machine Learning", „DTW" (`ki-saisonalitaet.html:204`), „KI-gestützte Saisonal-Prognose" (Meta `:8`): im Frontend läuft eine Pearson-Korrelation und ein Mittelwert, kein ML, kein DTW. Im Backend ein nicht installiertes DTW/Prophet mit stillen Rückfällen.
- „Euklidische Distanz: bewertet die absolute Abweichung der Werte" (Methodik-Text): der Code z-normiert beide Reihen vorher (`dash-compute.js:129-131`), misst also ebenfalls nur die Form.
- „Bullish/Bearish" in Grün/Rot: eine Richtungsaussage, für die die Messung keine Grundlage liefert.

### Urteil: **umbenennen und anders darstellen (HOCH), Backend-Zwilling angleichen oder entfernen (HOCH), Methodik ändern (MITTEL)**
1. „KI" und „Prognose" entfernen; Bullish/Bearish-Etikett streichen, solange keine Out-of-Sample-Validierung es trägt. Passender Name z. B. „Saison-Übereinstimmung" mit den vier Bausteinen als getrennte, beschreibende Kennzahlen.
2. Eine Implementierung (`SA.dashCompute`) für Dashboard, Watchlist und KI-Seite; gleiche Standard-Zeiträume. Backend entweder exakt angleichen (inkl. Zwillingstest wie `verify_seasonal_twins.py`) oder den Scanner-Score anders benennen. Tracking-Index-Fehler (`ki_score.py:254`) und den konstanten Prophet-Teil beheben bzw. entfernen.
3. Methodik: s1 auf die **Restjahres**-Rendite der Match-Jahre ab heute umstellen (sonst Selbstbezug), s4 aus dem Richtungsscore herausnehmen, laufendes Jahr aus `avg` ausschließen. Ähnlichkeit auf Renditen statt Kursniveaus (Korrelation von Niveaus trendender Reihen ist fast immer hoch).
4. Validierung: vorab Ziel (fwd 21 HT), Bewertungstage, Universum, Out-of-Sample-Zeitraum festlegen; Vergleich mit naiver Basis (Monats-Win-Rate allein; „immer bullish"); Kennzahlen Rangkorrelation, Trefferquote je Klasse, Kalibrierungsdiagramm; Blockbootstrap nach Jahr.

---

## 3. Anomalie-Radar

### Definition
**Live (Frontend)** `landing/js/decade-compute.js:267-325` (`fromPrices`), gerendert über `renderAnomalyInto` (`:574-639`) auf Dashboard (`dashboard.html:2134-2136`), Dekaden-, Jahres-, Monatszyklus, Overnight, Risikozyklus, TDOM-Analyse:
- aktuelle Rendite = `close[letzter]/close[letzter−9] − 1` → **9** Tagesrenditen, nicht 10 (`:270-272`).
- Vergleich: je anderes Jahr mit ≥ 200 Zeilen (`:42`) das Fenster `hRows[hIdx−10 … hIdx−1]`, wobei `hIdx` der erste Tag mit Kalendertag ≥ heute − 5 ist (`:283-292`).
- Score = `min(round(|z|·30), 100)`, Populations-Std (`:296-300`); ≥ 40 „leicht anomal", ≥ 70 „stark anomal" (`:309,598-600`). Zusätzlich Perzentilrang (`:301-305`).

**Backend** `shared/anomaly_engine.py:25-134`: IF (`contamination=0.1`) auf den 9 Tagesrenditen der Fenster am gleichen Kalendertag der letzten 20 Jahre, Score = 100 − Perzentil. Genutzt nur von `scripts/generate_decade_data.py:247` (Feld `anomaly` in `DJI-decade.json`, im Frontend nicht gerendert) und den Streamlit-Seiten `pages/01_Dekadenzyklus.py:305`, `pages/02_Jahreszyklus.py:960` (über `/app/` erreichbar). **[Code, grep]**

### Zwillinge
- **[Code]** Zwei verschiedene Größen unter demselben Namen und denselben Schwellen: JS = z-Wert der 10-Tage-Summe (Höhe der Bewegung), Python = IF auf der Reihenfolge von 9 Tagesrenditen (Form).
- **[Messung]** Basisrate „anomal" (≥ 40):
  - JS, 2006–2025, Stichtage alle 3 Handelstage: SPY 17,5 % (≥ 70: 5,4 %), ^DJI 11,6 % (2,7 %), ^GDAXI 18,4 % (4,9 %).
  - Python-IF, SPY/^DJI, alle 15 Handelstage: **66–69 %** ≥ 40, **32 %** ≥ 70, Median ≈ 50–54. Bei 12–20 Vergleichsjahren und einem Perzentil-Score ist „anomal" dort der Regelfall. Die Python-Fassung ist als Anomalie-Maß unbrauchbar.
- **[Code]** Die Python-Fassung nutzt `datetime.now()` für Kalendertag und Jahresgrenze (`anomaly_engine.py:55-56,70`), nicht das Datum des letzten Kurses.

### Look-ahead / Datenrand
- **[Code+Messung]** Fensterversatz im JS: das Vergleichsfenster endet am letzten Handelstag **vor** „heute − 5 Kalendertage", also mindestens 6 Kalendertage früher als das aktuelle Fenster (gemessen am 15.10.: min 6, Median 6, max 8). Verglichen wird damit nicht „derselbe Zeitpunkt im Jahr". Wirkung moderat: der Status (≥ 40 ja/nein) ändert sich bei korrekter Ausrichtung an 2,9 % (^DJI) bis 8,3 % (SPY) der Tage, Korrelation der Scores 0,89–0,96.
- **[Code]** Kein Zukunftswissen live (alle Vergleichsjahre abgeschlossen). Die Normierung nimmt aber bei ^DJI alle Jahre seit 1897 — die 1930er-Volatilität bläht die Streuung auf, weshalb ^DJI seltener „anomal" ist als SPY. Die Referenz hängt also an der Länge der Historie, nicht an einem festen Regime.
- **[Code+Messung]** Jahresanfang: Vergleichsfenster brauchen `hIdx ≥ 10` und überschreiten die Jahresgrenze nicht. Zwischen dem 10. und 16. Handelstag des Jahres gab es in 69 von 140 Fällen (SPY) keinen Score. Die Seite meldet dann „nicht berechenbar" — kein alter Wert, das ist in Ordnung.

### Statistische Aussagekraft
- Der z-Wert ist eine einfache, nachvollziehbare Beschreibung („wie ungewöhnlich war die 10-Tage-Bewegung für diese Jahreszeit"). Die Schwellen 40/70 entsprechen |z| ≥ 1,33 bzw. ≥ 2,33 — gesetzt, nicht begründet; gemessen fallen 12–18 % bzw. 3–5 % der Tage darüber, was zur Wortwahl „leicht/stark" passt.
- Saisonaler Vergleich bringt wenig gegenüber einem unbedingten Vergleich [plausibel]: die Streuung von 10-Tage-Renditen hängt viel stärker vom Volatilitätsregime ab als vom Kalendertag. Ein Vergleich mit der eigenen jüngeren Volatilität wäre aussagekräftiger.
- Es gibt keine prognostische Behauptung im Code; die Seite nennt den Radar aber „KI Quick-Check" (`dekadenzyklus.html:133`).

### Darstellung gegenüber Messung
- Tooltip: „Der Score misst wie viele Standardabweichungen…" (`decade-compute.js:551`) — der Score ist 30 × |z|, ein Score von 40 sind 1,33 σ. Die Zahl liest sich wie ein Prozentwert.
- Überschrift „KI Quick-Check": es läuft ein z-Wert, kein Modell (der Code sagt das selbst, `:267`).
- Label „10d-Rendite": gemessen werden 9 Tagesrenditen.

### Urteil: **behalten, kleine Methodik-Korrekturen und genauere Beschriftung (MITTEL); Python-Zwilling entfernen oder angleichen (NIEDRIG–MITTEL)**
1. Fenster korrekt ausrichten (Vergleichsfenster endet am letzten Handelstag ≤ heutiger Kalendertag), 10 echte Renditen, Kalendertag aus dem letzten Kursdatum.
2. Anzeige „|z| = 1,6 σ" statt „48 / 100", „KI" streichen. Optional Normierung auf die letzten N Jahre (z. B. 30) statt die ganze Historie.
3. `anomaly_engine.compute_ticker_anomaly_score` und `compute_market_regime` löschen oder auf die JS-Logik bringen; aus `generate_decade_data.py` entfernen, solange das Feld nirgends angezeigt wird. Die Streamlit-Seiten unter `/app/` zeigen sonst einen Radar, der zwei Drittel der Zeit „anomal" meldet.

---

## Weitere Vorschläge (priorisiert)

1. **HOCH — Vorzeichen der Crash-Ampel live verifizieren und bis zur Korrektur ausblenden.** Eine Abfrage `regime_scores` für SPY am 2020-03-16 und 2017-07-14 entscheidet es. Danach Wächter: Testfall mit einem synthetischen Crashtag, der Rot ergeben **muss** (Muster: „Testfall, in dem sich genau eine Größe bewegt", Projektlehre v57).
2. **HOCH — Eine Quelle je Kennzahl.** Crash-Ampel: 3 Rechenwege, KI-Score: 4 Fassungen (dash-compute, dashboard-inline, ki-seite-inline, Python), Anomalie: 2. Inline-Kopien aus `dashboard.html`/`ki-saisonalitaet.html`/`crash-fruehwarnung.html` löschen und `SA.dashCompute` einbinden; Zwillingstest analog `verify_seasonal_twins.py` für Python/JS, wo beide bleiben.
3. **HOCH — Wortwahl „KI", „Machine Learning", „Prognose", „Frühwarnung", „DTW", „Prophet" an das anpassen, was läuft** (Seiten, Meta, JSON-LD, en.json, Newsletter). Bei einer YMYL-Finanzseite ist eine nicht gedeckte Prognosebehauptung das größte Risiko.
4. **HOCH — Bullish/Bearish-Etiketten erst nach vorab festgelegter Out-of-Sample-Validierung.** Für beide Scores ein gemeinsames Validierungsgerüst bauen (Protokoll vorab, Walk-forward, naive Basis, Blockbootstrap nach Jahr, Ergebnis veröffentlichen — auch wenn es null ist, wie bei der Intermarket-Matrix).
5. **MITTEL — Perzentil-Ampeln mit festen Anteilen nicht als „selten" bezeichnen.** Entweder die Anteile offen zeigen (30 % Rot) oder Schwellen auf seltene Zustände legen und die tatsächliche Häufigkeit daneben schreiben.
6. **MITTEL — Historienkurven nur aus Daten bis zum jeweiligen Tag** (expandierendes Fenster), damit Chart und Live-Wert dieselbe Messung sind. Bei IF hieße das tägliches Nachtrainieren; mit dem einfachen gerichteten Score entfällt das Problem.
7. **MITTEL — Backend-KI-Score:** Tracking-Index (`ki_score.py:254`) korrigieren, Prophet- und DTW-Teile entfernen (nicht installiert, stiller Rückfall), stille `except: return 0.5`-Pfade (`ki_score.py:62-63,106-110,152-153`) als Fehler sichtbar machen — ein Teil-Score von 0,5 sieht aus wie eine neutrale Messung.
8. **NIEDRIG — Datenrand der KI-Seite:** `todayDoy` aus dem letzten Kursdatum statt Browseruhr; erster unvollständiger Jahrgang aus Match-Kandidaten und `avg` ausschließen; laufendes Jahr aus `avg` ausschließen.
9. **NIEDRIG — Anomalie-Radar Jahresanfang:** Fenster über den Jahreswechsel zulassen statt Lücke, oder die Lücke im Text erklären.

### Nicht geprüft
- Live-Werte in `regime_scores`, `ki_scores`, `scanner_results` (kein DB-Zugriff).
- Ob im Container `fastdtw`/`prophet` außerhalb von `requirements.txt` installiert sind (Dockerfile installiert nur `requirements.txt`).
- Die EN-Fassungen der Seitentexte im Einzelnen.
