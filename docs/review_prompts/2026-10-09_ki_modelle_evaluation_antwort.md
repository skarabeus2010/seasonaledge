# Codex-Antwort (Schlussantwort; Rohprotokoll nicht im Repo)

**Am sinnvollsten erscheinen mir drei Vorhaben: überprüfbare Erklärtexte aus eigenen Kennzahlen, eine kleine Volatilitätsprognose mit starken einfachen Vergleichsmodellen und eine rein beschreibende Ähnlichkeitssuche.** Ein neuer „KI prognostiziert den Markt“-Baustein wäre dagegen derzeit nicht gedeckt.

Die lokale Messung liefert einen konkreten Ansatzpunkt: Ein HAR-artiges Modell verbessert bei SPY den Varianzfehler gegenüber der 20-Tage-Vola. **Gegen EWMA ist der Vorteil aber nicht statistisch eindeutig; beim Fehler der angezeigten Volatilität gewinnt EWMA.** Das rechtfertigt eine Untersuchung, noch keine Produktbehauptung.

Ich habe ausschließlich gelesen und Berechnungen im Arbeitsspeicher ausgeführt, mit dem angegebenen Python. Keine Datenbank, keine Modell-API, keine Netzwerk-Schreibzugriffe. Externe Quellen wurden gelesen. Der Checkout wurde während der Prüfung offenbar parallel umgebaut: Unter anderem verschwanden die Streamlit-Seiten; die abschließende Docker-Datei beschreibt jetzt einen reinen Cron-Container. Aussagen zur tatsächlichen VPS-Ausführung bleiben deshalb ausdrücklich **nicht geprüft**.

**Was im Repo tatsächlich steckt**

| Baustein | Befund und Einordnung |
|---|---|
| Chronos, NeuralProphet, MSTL | Stillgelegt; die entfernten Module und Workflows sind dokumentiert. Kein aktueller Produktionspfad gefunden. [CHANGELOG.md:19](C:/dev/Seasonaledge/docs/CHANGELOG.md:19) |
| Python-Ähnlichkeitssuche | `fastdtw`, falls installiert; sonst stiller Wechsel zu Pearson-Korrelation. Das ist eine andere Methode, kein gleichwertiger Implementierungsersatz. [ai_models.py:32](C:/dev/Seasonaledge/shared/ai_models.py:32) |
| Prophet | Implementierung vorhanden, bei fehlendem Paket Rückgabe `None`. Prophet, fastdtw und anthropic fehlen in den deklarierten Abhängigkeiten. [ai_models.py:92](C:/dev/Seasonaledge/shared/ai_models.py:92), [requirements.txt:1](C:/dev/Seasonaledge/requirements.txt:1) |
| Backend-„KI-Score“ | Weiterhin im Nightly aufgerufen. Dessen Standard ist `quick_mode=True`; die Prophet-Komponente wird dann neutral auf 0,5 gesetzt, entsprechend 1,25 Gesamtpunkten. Also kein aktiver Prophet-Forecast. [nightly_refresh.py:49](C:/dev/Seasonaledge/scripts/nightly_refresh.py:49), [nightly_refresh.py:125](C:/dev/Seasonaledge/scripts/nightly_refresh.py:125), [ki_score.py:273](C:/dev/Seasonaledge/shared/ki_score.py:273) |
| Frontend-Score/TruePath | Handgeschriebene Statistik: ähnliche Jahresverläufe, gewichteter Musterpfad, Monatsquote, Tracking. Der alternative Matching-Zweig nutzt standardisierte euklidische Distanz, kein DTW. Frontend und Python-Score sind zudem unterschiedliche Berechnungen. [dash-compute.js:112](C:/dev/Seasonaledge/landing/js/dash-compute.js:112), [dash-compute.js:176](C:/dev/Seasonaledge/landing/js/dash-compute.js:176) |
| Claude-Kommentare | Zwei echte API-Implementierungen existieren, aber ich fand keine Aufrufer. Beide liefern bei fehlendem SDK bzw. Fehlern still `None`. Der vorgesehene Schlüssel allein aktiviert nichts. Modellvorgabe ist `claude-sonnet-4-20250514`; dessen heutige Verfügbarkeit habe ich nicht geprüft. [ai_models.py:151](C:/dev/Seasonaledge/shared/ai_models.py:151), [ai_models.py:208](C:/dev/Seasonaledge/shared/ai_models.py:208), [docker-compose.yml:17](C:/dev/Seasonaledge/docker-compose.yml:17) |
| Isolation Forest | Echte ML-Implementierungen für Ausreißerjahre, Musterbrüche und „Confidence“ bleiben vorhanden. Die Dekaden-Exportfunktion ruft den Anomaliescore auf. Das belegt Berechnungscode, keine Prognosekraft oder aktuelle Frontend-Nutzung. [ai_models.py:119](C:/dev/Seasonaledge/shared/ai_models.py:119), [anomaly_engine.py:291](C:/dev/Seasonaledge/shared/anomaly_engine.py:291), [generate_decade_data.py:247](C:/dev/Seasonaledge/scripts/generate_decade_data.py:247) |
| Stress-Ampel | Jetzt transparente Formel aus kurzfristiger Vola und Drawdown, mit ausschließlich vorherigen Beobachtungen als Rangreferenz. Der Nightly verwendet diese Implementierung. Keine ML-Prognose. [stress_score.py:7](C:/dev/Seasonaledge/shared/stress_score.py:7), [nightly_refresh.py:393](C:/dev/Seasonaledge/scripts/nightly_refresh.py:393) |
| `scripts/ml/regime_clustering.py` | Echtes KMeans, aber Forschungsstand: Skalierung und Cluster werden auf der gesamten übergebenen Historie geschätzt. Das vorgeschaltete `shift(1)` verhindert diesen späteren Zukunftseinfluss nicht. [regime_clustering.py:93](C:/dev/Seasonaledge/scripts/ml/regime_clustering.py:93), [regime_clustering.py:118](C:/dev/Seasonaledge/scripts/ml/regime_clustering.py:118) |
| `compute_regime_nightly.py` und Dashboard | Trotz Namen kein gelerntes Clustering: feste Regeln auf Rendite-/Vola-Perzentilen. Kein Aufruf im geprüften Nightly gefunden; lokale Ergebnisdatei fehlt. Das Dashboard rechnet dieselbe Regel selbst und nennt die Variable `kmeansRegime`. [compute_regime_nightly.py:25](C:/dev/Seasonaledge/scripts/ml/compute_regime_nightly.py:25), [dashboard.html:2097](C:/dev/Seasonaledge/landing/pages/dashboard.html:2097) |
| ToM-ML und Filtertests | Logistische Regression mit tatsächlich zeitlich getrenntem Training/Testing vorhanden; kein Produktionsaufruf gefunden. Die Kalendermerkmale zählen vorhandene Monatszeilen rückwärts. `backtest_new_filters.py` prüft dagegen feste Regeln und zählt Wochentage ohne Börsenfeiertage. Beides vor Wiederverwendung überprüfen. [tom_ml_filter.py:49](C:/dev/Seasonaledge/scripts/ml/tom_ml_filter.py:49), [tom_ml_filter.py:198](C:/dev/Seasonaledge/scripts/ml/tom_ml_filter.py:198), [backtest_new_filters.py:30](C:/dev/Seasonaledge/scripts/ml/backtest_new_filters.py:30) |
| Blog und Video | Blog-`--generate` erzeugt lediglich ein Markdown-Gerüst mit TODOs, keinen LLM-Text. Redaktionelle Claude-Agenten sind separat konfiguriert. Die Video-Pipeline enthält hingegen einen echten ElevenLabs-TTS-Aufruf mit `eleven_multilingual_v2`. [blog_builder.py:1711](C:/dev/Seasonaledge/blog/blog_builder.py:1711), [blogger.md:10](C:/dev/Seasonaledge/.claude/agents/blogger.md:10), [tts.py:22](C:/dev/Seasonaledge/scripts/video/tts.py:22), [tts.py:69](C:/dev/Seasonaledge/scripts/video/tts.py:69) |

Drei Darstellungsprobleme sind besonders relevant:

- **Die Umbenennung muss auch SEO, Übersetzungen und vorhandene Medien erfassen.** Scanner-FAQ/JSON-LD behaupten weiterhin Prophet; die englischen Metadaten beschreiben sogar andere Score-Komponenten als der Code. [scanner.html:47](C:/dev/Seasonaledge/landing/pages/scanner.html:47), [i18n.js:331](C:/dev/Seasonaledge/landing/js/i18n.js:331).
- **Das QQQ-Video ist riskanter als ein falsches KI-Etikett:** „KI-Saisonalität sieht +40 %“ macht aus ausgewählten historischen Gesamtjahresrenditen eine aktuelle Prognose. Ein Disclaimer korrigiert diese Kernaussage nicht. [qqq-truepath-ki-saisonalitaet.json:8](C:/dev/Seasonaledge/scripts/video/scripts/qqq-truepath-ki-saisonalitaet.json:8).
- **„Confidence“ ist keine kalibrierte Sicherheit.** Die betreffende IF-Funktion verwendet unter anderem den Anteil als normal klassifizierter Jahre bei vorgegebener `contamination`. Daraus folgt weder eine Trefferwahrscheinlichkeit noch ein statistisches Konfidenzniveau. [anomaly_engine.py:459](C:/dev/Seasonaledge/shared/anomaly_engine.py:459).

Die vorhandenen Claude-Funktionen würde ich nicht einfach einschalten: Sie formatieren **jeden Float als Prozentwert**, auch etwa einen Score, und fordern einen nächsten Katalysator ohne verpflichtenden Quellenbeleg. [ai_models.py:247](C:/dev/Seasonaledge/shared/ai_models.py:247), [ai_models.py:269](C:/dev/Seasonaledge/shared/ai_models.py:269).

**Die Datenlage ist brauchbar, aber deutlich ungleichmäßiger als „370 Ticker plus Optionshistorie“ vermuten lässt.**

| Daten | Lokal überprüfter Stand | Konsequenz |
|---|---|---|
| Kursuniversum | 370 Einträge in `tickers.json`; im ignorierten Research-Cache **40 Schlusskursreihen**, insgesamt 8,85 MB. SPY: 8.444 Beobachtungen, 29.01.1993–17.08.2026. [tickers.json:1](C:/dev/Seasonaledge/landing/data/tickers.json:1), [SPY.json:1](C:/dev/Seasonaledge/scripts/research/.cache/SPY.json:1) | Lokale Volatilitäts- und Ähnlichkeitstests möglich. Vollständige OHLC-Abdeckung für 370 Ticker und Historien seit 1928 ohne DB **nicht bestätigt**. |
| Optionsuniversum | **163 eindeutige Ticker**, aus den Kategorien gezählt. Snapshot-Code verarbeitet IV, Greeks und OI. [options_universe.py:17](C:/dev/Seasonaledge/shared/options_universe.py:17), [compute_options_skew.py:226](C:/dev/Seasonaledge/scripts/compute_options_skew.py:226) | Konfiguration und Beschaffungspfad vorhanden; erfolgreiche tägliche Abdeckung nicht belegt. |
| IV-/Skew-Historie | Lokale `options_skew*.json` fehlen. Ein bestehendes Research-Skript dokumentiert für SPY 165 Punkte bis September 2026 — ausdrücklich zu wenig für belastbare Monatskalibrierung. [expected_move_kalibrierung.py:17](C:/dev/Seasonaledge/scripts/research/expected_move_kalibrierung.py:17) | Beschaffbar bzw. serverseitig vorgesehen, aktuell nicht nachgemessen. |
| Optionsflows/GEX | Lokale Outputs vorhanden, aber unterschiedliche alte Stände. OI-Verzeichnis leer; der Code bewahrt ohnehin nur etwa **30 Snapshots** auf. [compute_options_flow.py:7](C:/dev/Seasonaledge/scripts/compute_options_flow.py:7), [compute_options_flow.py:45](C:/dev/Seasonaledge/scripts/compute_options_flow.py:45), [gex_summary.json:2](C:/dev/Seasonaledge/landing/data/gex_summary.json:2) | Kein belegter mehrjähriger Trainingsbestand für Flow-Prognosen. |
| COT | 170 wöchentliche Beobachtungen im lokalen Output, Mai 2023–Juli 2026. [cot_positioning.json:4](C:/dev/Seasonaledge/landing/data/cot_positioning.json:4) | Beschreibend brauchbar; für Prognosen Veröffentlichungsdatum statt Berichtsstichtag verwenden. |
| ETF-Flows | Lokal **ein Snapshot**, `ready:false`, keine Wochenhistorie. [etf_flows.json:4](C:/dev/Seasonaledge/landing/data/etf_flows.json:4), [etf_flows.json:52](C:/dev/Seasonaledge/landing/data/etf_flows.json:52) | Derzeit kein lokal belegter ML-Datensatz. |
| Polymarket | Preis-/Historienzugriff und Brier-/Kalibrierungslogik vorhanden. Umfang aufgelöster Märkte nicht geprüft. [polymarket_data.py:588](C:/dev/Seasonaledge/shared/polymarket_data.py:588), [brier_score.py:5](C:/dev/Seasonaledge/shared/brier_score.py:5) | Zuerst bestehende Kalibrierung nutzen; Marktpreise nicht als objektive Wahrscheinlichkeiten ausgeben. |
| Wahlen/Fed/CPI | Wahlkalender lokal vorhanden; Fed-Termine kodiert; CPI-Modul enthält historische Jahreswerte und einen FRED-Pfad. Das ist noch kein zeitpunktgetreuer Datensatz aus Veröffentlichungen und damaligen Erwartungen. [elections.json:1](C:/dev/Seasonaledge/landing/data/elections.json:1), [fed_dates.py:97](C:/dev/Seasonaledge/shared/fed_dates.py:97), [cpi_data.py:83](C:/dev/Seasonaledge/shared/cpi_data.py:83) | Für Erklärungen gut; „Überraschungseffekte“ benötigen zusätzliche Daten. |

Die Intermarket-Datei bestätigt den veröffentlichten Nullbefund: **470 primär getestete Zellen, null Befunde**. [intermarket_matrix.json:1](C:/dev/Seasonaledge/landing/data/intermarket_matrix.json:1). Diese Art Ergebnis sollte ausdrücklich als erfolgreiche Forschung gelten.

**Eigene Messung: Volatilität lässt sich sinnvoll untersuchen — der Modellname entscheidet aber nicht.**

Verwendet wurden ausschließlich die lokalen [SPY](C:/dev/Seasonaledge/scripts/research/.cache/SPY.json:1)-, [QQQ](C:/dev/Seasonaledge/scripts/research/.cache/QQQ.json:1)- und [GLD](C:/dev/Seasonaledge/scripts/research/.cache/GLD.json:1)-Dateien. Keine doppelten Datumswerte oder nichtpositiven Schlusskurse in diesen drei Reihen. Corporate-Action-Korrekturen und Börsenkalender-Vollständigkeit wurden nicht unabhängig verifiziert.

Methode:

- Tagesrendite \(r_t=\log(C_t/C_{t-1})\); Ziel ist der Durchschnitt der **zukünftigen quadrierten Tagesrenditen** über 5 bzw. 21 Sitzungen.
- Lineares HAR-artiges Modell mit Konstante sowie heutigem \(r_t^2\), 5- und 22-Tage-Mittel von \(r^2\).
- Jährliches Neuschätzen auf den vorherigen fünf Jahren; nur bereits vollständig beobachtete Trainingsziele.
- Test 2015–2025; 2.761 beziehungsweise 2.745 Prognosezeitpunkte je Ticker.
- Basen: vergangene 20-Tage-Stichprobenvarianz und EWMA mit vorab festem \(\lambda=0{,}94\).
- Primär hier QLIKE: \(y/\hat y-\log(y/\hat y)-1\), kleiner ist besser. Zusätzlich Fehler der annualisierten Vola.
- Unsicherheit: 2.000 gemeinsame Block-Bootstrap-Ziehungen mit 63 Sitzungen pro Block.

Das ist **kein klassisches HAR-RV aus Intraday-Daten**. Die klassische HAR-Idee bündelt realisierte Volatilität unterschiedlicher Zeitskalen; hier ersetzt ein deutlich verrauschterer Tagesdaten-Proxy diese Messung. [Corsi, HAR-RV](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1365738).

| Ticker / Horizont | QLIKE: 20T | QLIKE: EWMA | QLIKE: HAR-artig | HAR gegenüber 20T |
|---|---:|---:|---:|---:|
| SPY / 5 Sitzungen | 0,6754 | 0,5775 | **0,5267** | −22,0 % |
| SPY / 21 Sitzungen | 0,7188 | 0,6112 | **0,5223** | −27,3 % |
| QQQ / 5 Sitzungen | 0,5663 | 0,4867 | **0,4519** | −20,2 % |
| QQQ / 21 Sitzungen | 0,5042 | 0,4344 | **0,3891** | −22,8 % |
| GLD / 5 Sitzungen | 0,4521 | **0,3748** | 0,3958 | −12,5 % |
| GLD / 21 Sitzungen | 0,3158 | **0,2288** | 0,2342 | −25,8 % |

Die Einschränkungen sind entscheidend:

- SPY/21: Der mittlere absolute Fehler der annualisierten Vola beträgt **6,06 Prozentpunkte bei HAR**, 5,74 bei 20T und **5,50 bei EWMA**. HAR gewinnt also nicht jede sinnvolle Zielgröße.
- SPY/21: Die QLIKE-Differenz HAR minus EWMA hat ein geschätztes 95%-Intervall von **−0,2304 bis +0,0310**. Kein eindeutiger Vorteil gegenüber EWMA.
- Gegen einen zur Zieldefinition passenden 20-Tage-Mittelwert von \(r^2\) bleibt der SPY-Vorteil bestehen: QLIKE 0,5223 gegenüber 0,6771. Er entsteht somit nicht nur aus Zentrierung und Stichprobenkorrektur der ersten Basis.
- Der Rechenkern einschließlich Bootstrap benötigte lokal rund **2,2 Sekunden** nach den Imports. Das ist kein VPS-Benchmark.
- Diese einmalige Exploration hat den Testzeitraum jetzt verbraucht. Weitere Modellwahl auf denselben Jahren wäre keine unabhängige Bestätigung.

Eine zweite Messung betrifft Regime: Die reine Funktion aus [compute_regime_nightly.py:25](C:/dev/Seasonaledge/scripts/ml/compute_regime_nightly.py:25) klassifizierte SPY zunächst mit Daten 2010–2020, dann mit Daten 2010–2025. Für die identischen Tage 2015–2020 änderten sich **36 von 1.511 Labels, also 2,38 %**. Ursache sind Gesamtserien-Perzentile. Ein `shift(1)` repariert das nicht.

**Für neue Vorhaben würde ich vorab dieselben Grundregeln festlegen.**

Alle nachfolgenden Erfolgsschwellen sind **Vorschläge für ein festzuschreibendes Protokoll**, keine bestehenden Ergebnisse: Zeitliche Trennung statt zufälliger Splits; Trainingsziele müssen am Prognosetag ausgereift sein; Skalierung und Auswahl nur im Training; überlappende Horizonte bei Unsicherheit berücksichtigen; ein primärer Endpunkt; Ergebnisse je Markt und Zeitabschnitt; bei mehreren Modellversuchen Mehrfachtests berücksichtigen. Für Kursmodelle zusätzlich heutige Universumsauswahl, Datenrevisionen und bei vortrainierten Modellen mögliche Trainingsdatenüberschneidungen dokumentieren.

**Sprachmodelle sind für Faktenvermittlung der beste erste KI-Einsatz.**

Auf `/dashboard` und Tickerseiten könnten Leser einen kurzen DE/EN-Absatz sehen: Was zeigen Saisonmuster, Stress, IV und Datenfrische? Jede Aussage bekommt eine Kennzahlenreferenz, Beobachtungszeit und Stichprobengröße. Statische Methodenerklärungen werden einmal redaktionell geprüft; dynamische Texte entstehen aus einem typisierten Faktenblatt.

Als konkrete Vergleichskandidaten würde ich **Claude Haiku 5.5**, **Claude Sonnet 5.5** und **Gemini 2.5 Flash-Lite** testen. Ihre Qualität für eure deutschen Finanztexte ist **nicht geprüft**; Herstellerbenchmarks ersetzen diesen Test nicht. Die veröffentlichten Textpreise betragen bei kurzen Prompts:

| Modell | USD je Mio. Input-/Output-Tokens | Geplante Rolle |
|---|---:|---|
| Claude Haiku 5.5 | 0,10 / 0,50 | Zusammenfassung, Übersetzung |
| Claude Sonnet 5.5 | 2,00 / 10,00 | Schwierige Formulierungen und zusätzliche Prüfung |
| Gemini 2.5 Flash-Lite | 0,10 / 0,40 | Unabhängiger günstiger Vergleich |

Quellen: [Anthropic-Preistabelle](https://www.anthropic.com/claude-haiku-5-5), [Google-Preisliste](https://ai.google.dev/gemini-api/docs/pricing). Preise ohne Steuern, Zusatzwerkzeuge und Wiederholungen.

Rechenbeispiel: 20 Ticker × 30 Tage × zwei Sprachen, jeweils 3.000 Input- und 600 Output-Tokens, ergeben **0,72 USD Haiku**, **14,40 USD Sonnet** oder **0,65 USD Gemini** monatlich für einen Durchlauf. Bei allen 370 Tickern wären es rund **13,32 / 266,40 / 11,99 USD**. Für den kleinen Pilot einschließlich Prüfungen würde ich **5–25 USD/Monat** reservieren. Der redaktionelle Prüfaufwand ist wichtiger als der Tokenpreis.

Die Aufgaben brauchen unterschiedliche Abnahmekriterien:

| Aufgabe und Lesernutzen | Vorab festgelegte Prüfung | Erfolg / Abbruch |
|---|---|---|
| Tages-/Tickerzusammenfassung | 200 eingefrorene Faktenblätter mit normalen, fehlenden, veralteten und widersprüchlichen Daten; DE/EN gegen deterministische Textvorlage; anschließend 30 Tage Parallelbetrieb ohne automatische Veröffentlichung | Null kritische Zahl-, Einheiten-, Richtungs- oder Prognosefehler im Abnahmesatz; mindestens 95 % vollständig belegte Aussagen; mindestens 30 % weniger Bearbeitungszeit. Sonst Vorlage beibehalten. |
| Übersetzung | 100 getrennte Textpaare; bilinguale Prüfung von Zahlen, Negationen, Einschränkungen und Begriffen | Null bedeutungsverändernde Finanzfehler; Glossar konsequent eingehalten. Sonst nur redaktionelle Unterstützung. |
| Faktenprüfung von Texten | 200 Fälle mit gezielt eingebauten Fehlern, getrennt vom Prompt-Tuning; Vergleich mit Zahlen-/Einheitenregeln | Mindestens 95 % der kritischen Fehler erkennen, höchstens 5 % Fehlalarme. Sonst nicht als Veröffentlichungsfreigabe verwenden. |
| Fragen zu eigenen Daten | Später `/dashboard`: 200 zurückgehaltene Fragen einschließlich unbeantwortbarer Fragen; strukturierte Datenabfrage gegen fest definierte FAQ | Mindestens 95 % richtige, belegte Antworten und 95 % korrekte Enthaltung bei fehlender Datenbasis; null erfundene Quellen. Sonst keine freie Chatfunktion. |

Das LLM sollte weder Kennzahlen rechnen noch den faktischen Freigabetest allein durchführen. Zahlen, Einheiten, Stand und zulässige Aussagen werden deterministisch geprüft. Bei Fehlern erscheint eine geprüfte Vorlage oder kein Text.

**Volatilitätsmodelle verdienen einen begrenzten Forschungsauftrag.**

Lesernutzen auf `/skew` und `/dashboard`: „Geschätzte Schwankungsbreite für die nächsten fünf Sitzungen“, daneben historische Prognosegüte, Vergleich mit EWMA und später ein kalibriertes Band. **Keine Aussage über die Richtung.**

- **HAR-artige Regression:** Passt zu den vorhandenen Tageskursen und ist leicht erklärbar. Echtes HAR-RV benötigt eine bessere tägliche RV-Messung, typischerweise Intraday-Daten; deren Zugang ist hier nicht belegt.
- **GARCH(1,1):** Sinnvoller Vergleich auf Tagesrenditen. Unterstützt mehrschrittige Varianzprognosen; `arch` ist im Repo nicht deklariert. [Offizielle arch-Dokumentation](https://arch.readthedocs.io/en/stable/univariate/forecasting.html).
- **Lineare Quantilregression:** Sinnvoll, wenn die Frage „Wie breit ist ein 80%-Bereich?“ lautet. Mit denselben wenigen Merkmalen anfangen; Pinball Loss und Intervallgüte messen. [scikit-learn QuantileRegressor](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.QuantileRegressor.html).
- **EWMA ergänzen:** Die eigene Messung macht sie zur Pflichtbasis, nicht nur zum optionalen Vergleich.

Protokoll: Primär fünf Sitzungen, sekundär 21. Historische Walk-forward-Auswertung 2015–2025 jetzt als Exploration behandeln; danach festgeschriebene Bestätigung auf bisher nicht verwendeten 2026-Daten und prospektiv. HAR/GARCH müssen mindestens **5 % geringeren QLIKE als die stärkste einfache Basis** erreichen, mit blockbasiertem Unsicherheitsintervall unter null, ohne mehr als 5 % Verschlechterung der Vola-MAE. Quantilregression entsprechend mindestens 5 % bessere Pinball-/Intervallverluste gegenüber historischen bzw. EWMA-skalierten Quantilen.

Abbruch: Vorteil nur gegen die schwache Basis, nur in einer Krise oder nur nach nachträglicher Modellauswahl. Dann bleibt EWMA das Produktmodell.

Implizite Vola gehört dazu, sobald eine hinreichende, zeitlich saubere Historie existiert. **IV ist aber keine unverzerrte physische Vola-Prognose**; rohe IV und eine ausschließlich im Training angepasste IV-Basis getrennt vergleichen. Horizont und Annualisierung müssen übereinstimmen — ein Problem, das das Repo bereits ausdrücklich dokumentiert. [realized_vol.py:17](C:/dev/Seasonaledge/shared/realized_vol.py:17).

**Chronos-Bolt, TimesFM und Moirai wären nachgelagerte Herausforderer.**

| Kandidat | Fachliche und praktische Bewertung |
|---|---|
| Chronos-Bolt Tiny/Mini | 9 bzw. 21 Mio. Parameter, direkte Quantilprognosen; unter den drei Familien mein erster kleiner Versuch. Herstellerangaben zu Geschwindigkeit beziehen sich auf ursprüngliches Chronos, nicht auf HAR oder euren VPS. [Amazon-Repository](https://github.com/amazon-science/chronos-forecasting) |
| TimesFM 2.5 | 200 Mio. Parameter, optionaler Quantilkopf; deutlich größeres Betriebsbudget. **Version festschreiben:** Laut aktuellem Repository bleiben Gewichte bis 2.5 Apache-2.0; selbst gehostete 3.0-Gewichte sind nicht für kommerziellen Produktionsbetrieb freigegeben. [Google-Repository](https://github.com/google-research/timesfm) |
| Moirai 1.1-R Small | 13,8 Mio. Parameter, aber die geprüfte Modellkarte nennt **CC-BY-NC-4.0** und Forschungsnutzung. Für SeasonAlpha würde ich diesen Checkpoint ohne entsprechende zusätzliche Rechte nicht einplanen. Andere Moirai-Versionen wurden nicht geprüft. [Salesforce-Modellkarte](https://huggingface.co/Salesforce/moirai-1.1-R-small) |

Datenziel bleibt Vola, nicht Kursniveau. Kein Fine-Tuning zum Einstieg. Gleicher zeitlicher Test wie oben, zusätzlich ein Zeitraum nach dem jeweiligen Trainingsdatenstichtag; ein historischer „Zero-shot“-Test kann sonst durch vortrainierte Datenkenntnis belastet sein.

Erfolg: mindestens **10 % Verbesserung gegenüber dem besten bereits akzeptierten klassischen Modell**, einschließlich Intervallgüte und Betriebskosten. Abbruch: kein robuster Zusatznutzen, unbekannte Datenkontamination, fehlende Nutzungsrechte oder Überschreitung des RAM-/Zeitbudgets. Für SeasonAlpha-spezifische Überlegenheit dieser Modelle liegt derzeit **kein Beleg** vor.

**Regime-Erkennung ist als Beschreibung möglich, aber zunächst nicht nötig.**

Ein kleines Gaussian-HMM oder KMeans könnte auf dem Dashboard Zustände wie „ruhig“, „hohe Schwankung“ und „Trend mit hoher Schwankung“ erklären. Tageskurse reichen; HMM-Implementierungen sind verfügbar. [hmmlearn-Dokumentation](https://hmmlearn.readthedocs.io/en/stable/api.html).

Protokoll: Zwei oder drei Zustände vorab festlegen; Training bis 2014, rollende Auswertung 2015–2025; ausschließlich vorwärts gefilterte Zustände, keine rückblickende Glättung. Skalierung ebenfalls nur aus Vergangenheit. Vergleich mit einfachen Vola-/Drawdown-Perzentilen. Seeds, Trainingsfenster und kleine Datenstörungen variieren; Zustandslabels vor Vergleichen zuordnen.

Erfolg: beispielsweise Adjusted Rand Index ≥0,8 bei kleinen Trainingsänderungen und klare zusätzliche Information gegenüber den Regeln. Abbruch bei instabilen Zuständen oder fehlendem Mehrwert. Vergangene veröffentlichte Zustände werden eingefroren. Gedeckt wäre „ähnelt historisch einem Hochvolatilitätszustand“; ungedeckt „Bear-Regime kündigt fallende Kurse an“.

**Kalibrierung ist wertvoller als ein weiteres „Confidence“-Etikett.**

Auf `/skew` könnte eine Karte zeigen, wie oft das angezeigte Expected-Move-Band tatsächlich gehalten hat. Auf einer späteren Vola-Karte wären rollend kalibrierte 80%-Intervalle sinnvoll.

Konforme Verfahren sind kein automatischer Garant für jeden einzelnen Markttag: Klassische Austauschbarkeitsannahmen passen nicht ohne Weiteres zu Finanzzeitreihen. Adaptive Verfahren adressieren Verteilungsänderungen, ihre langfristige Deckung ist aber keine bedingte Garantie für jede Krise. [Gibbs/Candès](https://arxiv.org/abs/2106.00170).

Protokoll: Ziel und Horizont zuerst definieren; beispielsweise zukünftige 5-Tage-Vola oder 21-Tage-Endrendite. Kalibrierung ausschließlich mit bereits ausgereiften Fehlern. OOS 2015–2025 plus prospektive Fortsetzung. Vergleich mit historischem Quantilband und EWMA-Band; Deckung **und Breite/Intervallscore** prüfen.

Erfolg: beim 80%-Band beispielsweise 77–83 % Gesamtdeckung, mindestens 5 % besserer Intervallscore und keine klare Unterdeckung in vorab festgelegten Stressabschnitten. Abbruch bei kleinen effektiven Stichproben oder „guter Deckung“ nur durch nutzlos breite Intervalle. Keine Konformalisierung eines dimensionslosen Saison-Scores ohne eindeutig definiertes zukünftiges Ziel.

Eine bestehende Research-Annahme muss dabei korrigiert werden: [expected_move_kalibrierung.py:26](C:/dev/Seasonaledge/scripts/research/expected_move_kalibrierung.py:26) setzt VIX und ATM-IV konzeptionell gleich. **VIX aggregiert Optionen über viele Strikes; ATM-IV ist etwas anderes.** VIX eignet sich als externe Referenz, nicht als identische Messung. [Cboe-Methodik](https://cdn.cboe.com/resources/vix/VIX_Methodology.pdf).

**Textmodelle auf Fed-Statements sind realistisch; flächendeckende Nachrichtenmodelle derzeit nicht.**

Die erste sinnvolle Anwendung wäre auf der Zentralbankseite: „Was hat sich gegenüber dem vorherigen Statement geändert?“ mit Originalpassage, Datum und DE/EN-Erklärung. Fed-Statements und historische Materialien sind offiziell zugänglich; ein lokaler Textkorpus wurde nicht gefunden. [Federal Reserve](https://www.federalreserve.gov/monetarypolicy/fomc_historical.htm).

FinBERT ist ein englisches Finanz-Sentimentmodell, **kein fertiger Hawkish-/Dovish-Klassifikator und keine Renditeprognose**. [ProsusAI-Modellkarte](https://huggingface.co/ProsusAI/finbert). Für diese Aufgabe würde ich zuerst Textvergleich plus LLM-Extraktion testen.

Protokoll: Entwicklung an älteren Statements, Test 2020–2025, zeitlich getrennt und manuell annotiert. Basis ist ein einfacher Satzvergleich. Erfolg: ≥95 % richtige Quellenzuordnung und mindestens 90 % der materiellen Änderungen erkannt, null erfundene geldpolitische Entscheidungen. Abbruch, wenn die Erklärung keinen Mehrwert gegenüber dem Originalvergleich bringt.

Earnings-Calls sind über Anbieter bzw. Investor-Relations-Seiten beschaffbar; beispielsweise existiert eine FMP-Transcript-API. Vollständigkeit, historische Verfügbarkeit und kommerzielle Weiterverwendungsrechte für euren Bedarf sind **nicht geprüft**. [FMP-Dokumentation](https://site.financialmodelingprep.com/developer/docs). Nachrichtenfeed ebenso: kein belegter Bestand und kein geklärter Beschaffungsvertrag. Daher zunächst keine entsprechenden Prognoseprojekte und keine erfundenen Monatskosten für Datenlizenzen.

**Ähnlichkeitssuche liefert direkten Nutzen ohne Prognoseversprechen.**

Auf `/scanner` oder einer Tickerseite: „Welche fünf Werte haben sich in den letzten 60 Sitzungen ähnlich bewegt?“ Dazu 20-/60-/120-Tage-Vergleich, Korrelation der Renditen, eigene Vola und gegebenenfalls marktbereinigte Ähnlichkeit.

Für 370 Ticker sind nur **68.265 eindeutige Paare** zu vergleichen. Dafür braucht es weder Transformer noch Vektordatenbank. Zunächst normalisierte Renditevektoren und Korrelation/euklidische Distanz; DTW nur, falls zeitversetzte Formähnlichkeit einen nachgewiesenen Zusatznutzen hat. Die vorhandene Jahresmustersuche ist fachlich verwandt, beantwortet aber eine andere Frage. [dash-compute.js:112](C:/dev/Seasonaledge/landing/js/dash-compute.js:112).

Protokoll: Kein Zukunftshorizont, sondern aktuelle Beschreibung. Historische Stichtage 2020–2025; Basis einfache 60-Tage-Renditekorrelation. 100 kuratierte Vergleichsfälle, Ausschluss von Datenlücken/Split-Artefakten, Stabilität gegenüber kleinen Fensteränderungen. Erfolg: ≥80 % nützliche Top-5-Treffer in verblindeter Beurteilung und zusätzlicher Nutzen der komplexeren Variante. Sonst die einfache Korrelation verwenden.

Anomaliesuche getrennt behandeln: zuerst robuste Abweichungen/MAD und Datenfehlerregeln, dann gegebenenfalls Isolation Forest. Auf 200 bestätigten oder injizierten Fehlerfällen ≥95 % Erkennung kritischer Datenfehler und ≤5 % Fehlalarme verlangen. Ein statistisch ungewöhnlicher Marktverlauf ist kein Datenfehler und kein bevorstehender Crash.

**Betriebsseitig passen die kleinen Verfahren gut zur Architektur.** Die folgenden Werte sind konservative Planungsschätzungen für einen einzelnen Prozess, keine gemessenen VPS-Werte. Laufzeiten gelten für kleine Piloten; bestehende Dienste brauchen zusätzlichen RAM.

| Vorhaben | RAM / CPU | Geschätzte Laufzeit | Zusätzliche API-Kosten |
|---|---|---|---|
| Fakten-LLM, Übersetzung, Textprüfung | 0,1–0,4 GB; CPU gering | 1–10 min für 20 Ticker DE/EN, abhängig von API | Pilot etwa 5–25 USD/Monat |
| Fragen zu Daten | 0,2–0,5 GB für schmalen Dienst | Pro Anfrage; kein Nightly nötig | Bei 10.000 Fragen mit obigem Tokenansatz etwa 6 USD Haiku bzw. 120 USD Sonnet, vor Zusatzaufrufen |
| HAR/EWMA | 0,1–0,4 GB; ein Kern | Sekunden bis wenige Minuten für 370 Reihen | 0 |
| GARCH | 0,2–0,6 GB; ein Kern | Pilot <5 min; gesamtes Universum grob 5–30 min bei Neuschätzung | 0 |
| Quantilregression | 0,2–0,8 GB; ein Kern | Pilot 1–10 min; Training besser separat | 0 |
| Chronos-Bolt Tiny/Mini | grob 0,7–1,5 GB; 1–2 Kerne | Für 20 Reihen etwa 1–10 min, zu messen | 0 bei lokaler Inferenz |
| TimesFM 2.5 | grob 1,5–3+ GB; 1–2 Kerne | Für 20 Reihen etwa 5–30 min, zu messen | 0 lokal; auf diesem VPS ungünstig |
| Moirai Small | grob 0,7–1,5 GB; 1–2 Kerne | Minutenbereich, nicht gemessen | Lizenzfrage verhindert aktuelle Produktionsempfehlung |
| HMM/KMeans | 0,2–0,6 GB; ein Kern | Sekunden bis wenige Minuten für wenige Indizes | 0 |
| Rollende Kalibrierung | 0,1–0,4 GB; ein Kern | Sekunden bis wenige Minuten | 0 |
| Fed-Textvergleich | API-Variante <0,4 GB | Nur bei Veröffentlichung, Minuten | Grob <5 USD/Monat im kleinen Umfang; andere Textlizenzen offen |
| Ähnlichkeit/Datenqualität | 0,1–0,5 GB; ein Kern | Sekunden bis wenige Minuten | 0 |

PyTorch-Modelle würde ich zunächst außerhalb des Produktionscontainers testen. Ein Bestand von 3,8 GB RAM ist kein verfügbares Modellbudget von 3,8 GB. Downloads, Paketkompatibilität und Spitzenverbrauch wurden nicht ausprobiert.

Die priorisierte Liste lautet:

1. **P0 — Bestehende Aussagen bereinigen und Faktenvertrag definieren.** Prophet-/DTW-/KI-Behauptungen in Seite, FAQ, englischen Metadaten und Video prüfen; Frontend-/Backend-Abweichungen sichtbar machen. Zahlen bekommen Einheit, Zeitraum, Stichprobe, Quelle und Stand. Das verhindert, dass ein LLM bereits falsche Fakten überzeugender formuliert.
2. **P1 — Erklärtexte plus Faktenprüfung, erster Ausbau in 2–4 Tagen.** Zehn bis zwanzig Ticker, zwei Sprachen, drei kurze Aussagen, keine Zukunftsrichtung; deterministische Vorlage als Basis und Rückfall. Haiku gegen Sonnet/Gemini auf dem festgelegten Testsatz vergleichen. Zunächst redaktionelle Freigabe; kein freier Chat.
3. **P2 — Volatilitätslabor, erster Ausbau in 3–5 Tagen.** SPY, QQQ und GLD; EWMA, HAR-artig und GARCH; fünf Sitzungen als Hauptziel. Zunächst ein reproduzierbarer Vergleichsbericht und intern archivierte Prognosen. **Die erste Ausbaustufe kann in Tagen entstehen, ein belastbarer prospektiver Nachweis nicht.** Öffentliches Prognosemodul erst nach Bestehen der Kriterien.
4. **P3 — Beschreibende Ähnlichkeitssuche, erster Ausbau in 2–3 Tagen.** Erst die 40 lokal belegten Reihen, anschließend freigegebene vollständige Daten. „Ähnlich verlaufen“ mit Zeitraum und Metrik; keine Fortsetzung des Musters versprechen. Das ist der schnellste zusätzliche Leserbaustein.
5. **Danach — Kalibrierung bestehender Expected Moves und gegebenenfalls Fed-Änderungsvergleich.** Beides stärkt die belegbare kleine Aussage; eigene Optionshistorie und Veröffentlichungstimestamps zuerst prüfen.
6. **Vorerst zurückstellen — HMM, große Zeitreihenmodelle, allgemeiner Finanzchat, Earnings-/News-Sentimentprognosen.** Entweder fehlt ein bewiesener Zusatznutzen, die Datenbasis oder ein passender Betriebs-/Lizenzrahmen.
7. **Finger lassen — neuer Rendite-„KI-Score“, Crashwahrscheinlichkeit aus Anomalierang, „100 % Trefferquote“ aus ausgewählten ähnlichen Jahren und automatische Prognosetexte.** Dafür liefern weder der untersuchte Code noch die vorhandenen Ergebnisse eine tragfähige Grundlage.
