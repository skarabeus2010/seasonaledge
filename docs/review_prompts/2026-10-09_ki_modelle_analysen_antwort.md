# KI-Modelle und Analysen für SeasonAlpha

**Stand: 9. Oktober 2026 · Entscheidungsgrundlage für Forschung, Studien, Seitenfunktionen und Blogartikel**

**Empfehlung:** SeasonAlpha sollte zuerst die Belastbarkeit seiner Daten und Aussagen untersuchen: Datenqualität, Stabilität saisonaler Befunde, Kalenderabhängigkeit von Volatilität, Kalibrierung von Optionsbändern und Polymarket-Preisen. Dafür reichen überwiegend kleine CPU-Verfahren. Zeitreihen-Foundation-Modelle sind interessante Vergleichskandidaten, aber bisher kein begründeter Ersatz für einfache Referenzen.

Dieses Dokument erweitert die vorhandene Modellevaluation und Marktanalyse. Es enthält **Vorschläge, keine neu berechneten Studienergebnisse**. Das Repo wurde ausschließlich gelesen; `docs/KI_ANALYSEN.md` wurde nicht angelegt. Anbieterangaben wurden mit Webquellen geprüft. Modelle wurden weder installiert noch auf dem VPS getestet.

## 1. Ausgangslage und tatsächlich nachweisbare Daten

Die Saison-Score-Validierung ergibt einen mittleren Spearman-Zusammenhang von **0,01899**, mit 95%-Intervall **−0,03454 bis +0,08390**. Das widerlegt nicht jede denkbare saisonale Hypothese, trägt aber keine Renditeprognose durch den geprüften Score. Das Protokoll bezeichnet die Auswertung selbst als historische Walk-forward-Auswertung nach Methodenrevision, **nicht als Bestätigungstest**. [Ergebnis](/C:/dev/Seasonaledge/scripts/research/saison_score_validierung_ergebnis.json), [Protokoll](/C:/dev/Seasonaledge/scripts/research/saison_score_validierung_protokoll.json)

| Datenbereich | Im Checkout geprüft | Konsequenz für neue Analysen |
|---|---|---|
| Kursuniversum | `landing/data/tickers.json` enthält **370 Einträge**. Unter `scripts/research/.cache` liegen **40 JSON-Dateien**. | 370 katalogisierte Ticker sind nicht automatisch 370 vollständige, vergleichbare Zeitreihen. |
| Kurse und Renditen | Supabase-Abfrage von `prices`; Verarbeitung von OHLCV und `log_return`. Rückfall auf andere Datenquellen ist implementiert. | Quelle, Kursanpassung, Lücken und tatsächlichen verfügbaren Zeitraum pro Ticker erfassen. [Datenzugriff](/C:/dev/Seasonaledge/shared/data.py:27), [Supabase](/C:/dev/Seasonaledge/shared/supabase_client.py:69) |
| Sehr lange Historien | Code verbindet teilweise ältere Stooq-Daten mit Yahoo-Daten. Wahlstudien dokumentieren historische Indexänderungen und frühere Samstagssitzungen. | „Seit 1895“ nicht als homogenen OHLC-Datensatz behandeln. Den frühesten Live-Datenbankeintrag habe ich nicht geprüft. [Downloader](/C:/dev/Seasonaledge/shared/yahoo_downloader.py), [Wahlstudie](/C:/dev/Seasonaledge/scripts/build_wahlen.py:35) |
| TDOM/TDOY | Tabellen und Berechnungswege sind vorhanden; mehrere Renditedefinitionen und Zählrichtungen. | Für zeitliche Validierung Statistiken aus damaligen Rohdaten neu berechnen. Heute aggregierte Tabellen können Zukunftsinformation enthalten. [Schema](/C:/dev/Seasonaledge/scripts/create_market_tables.sql:89) |
| Optionen | Code für 25-Delta-Skew, konstante Laufzeiten, ATM-IV, Term-Struktur, Expected Move und Historienexport vorhanden. **`options_skew_history.json` fehlt im lokalen Checkout.** | Optionsstudien benötigen zunächst einen Export mit Zeitstempeln, Qualitätskennzeichen und dokumentierter Historie. [Berechnung](/C:/dev/Seasonaledge/scripts/compute_options_skew.py) |
| GEX und OI | GEX wird mit der festen Konvention **Call positiv, Put negativ** berechnet. | Modellierte Exposure-Schätzung; tatsächliche Dealer-Bestände werden damit nicht beobachtet. Historische Rohketten sind gesondert nachzuweisen. [GEX-Code](/C:/dev/Seasonaledge/scripts/compute_gamma_exposure.py:7) |
| Polymarket | Getrennte Tabellen für laufende und aufgelöste Märkte sowie Preiszeitreihen; Brier-Auswertung vorhanden. | Auflösungszeit, Preisfrische, Marktdefinition und gemeinsame Ereigniszugehörigkeit prüfen. Tageszeilen sind keine unabhängigen Ereignisse. [Schema](/C:/dev/Seasonaledge/scripts/create_polymarket_resolved_tables.sql), [Auswertung](/C:/dev/Seasonaledge/scripts/compute_brier_stats.py) |
| Intermarket | Lokaler Export vom **22.09.2026**: 556 Zellen, 470 primär getestet, **0 Befunde**. | Kein bestehender Beleg für prognostischen Vorlauf. Neue Fragestellungen von Wiederholungen derselben Suche unterscheiden. [Export](/C:/dev/Seasonaledge/landing/data/intermarket_matrix.json), [Methodik](/C:/dev/Seasonaledge/scripts/research/intermarket_matrix.py) |
| Ereignisse, Wahlen, Stress | Börsenereignisschema, Wahlkalender und Stress-Formel vorhanden. Stress kombiniert Vola und Drawdown relativ zur Vergangenheit. | Gute Basis für beschreibende Forschung. Stress ist keine Crashwahrscheinlichkeit. [Kalenderschema](/C:/dev/Seasonaledge/scripts/create_market_tables.sql), [Stress](/C:/dev/Seasonaledge/shared/stress_score.py:7) |

**Nicht geprüft:** Live-Vollständigkeit in Supabase, Produktionszustand des VPS, historische Datenrevisionen, sämtliche Datenverträge und Weiterverwendungsrechte. Ein vorhandener Berechnungspfad beweist weder vollständige Historie noch veröffentlichungsfähige Datenrechte.

## 2. Modellkatalog

### Leseschlüssel für Kosten, Versionen und Hardware

Die Tabellen nennen verfügbare **Modellgenerationen beziehungsweise Paketversionen**. Ein Modellname wie „Chronos-2“ ist keine Python-Paketversion. Für reproduzierbare Experimente müssen zusätzlich Paket-Lockfile, Modellrevision und Gewichte-Hash gespeichert werden.

**Hardwareangaben sind eigene Planungsschätzungen, keine Messungen:**

| Kürzel | Bedeutung für den VPS mit insgesamt 4 GB RAM |
|---|---|
| **CPU-gut** | Kleine Studien voraussichtlich gut machbar; meist etwa 0,2–1 GB Prozessspeicher. Reihen nacheinander verarbeiten. |
| **CPU-begrenzt** | Kleine Batches beziehungsweise kurze Kontexte plausibel; grob 1–3 GB möglich. Spitzenverbrauch und bestehende Dienste entscheiden. |
| **Extern** | Für diesen Produktions-VPS nicht sinnvoll eingeplant; größerer Rechner oder API. GPU nicht grundsätzlich immer erforderlich, aber oft praktisch nötig. |
| **API** | Auf dem VPS läuft nur der Client; kein lokaler Modellbetrieb. |

Bei frei nutzbarer Software bedeutet **0 USD Lizenzgebühr**, nicht kostenloser Betrieb. Arbeitszeit, Strom, RAM, Datenlizenzen und gegebenenfalls Cloud-Rechenzeit bleiben separat. Bei nichtkommerziellen Gewichten ist ein kostenloser Download **keine Freigabe für SeasonAlphas kommerzielle Nutzung**, auch nicht automatisch für interne Produktforschung.

### 2.1 Zeitreihen-Foundation-Modelle

Diese Modelle prognostizieren numerische Reihen. Ihre allgemeinen Benchmark-Ergebnisse sind **kein Nachweis für Aktienrenditen, Optionspreise oder SeasonAlphas Daten**.

| Modell / verfügbare Version | Wofür geeignet? | Lizenz und Kosten | 4-GB-CPU-Eignung | Primärquelle |
|---|---|---|---|---|
| **Chronos-T5**: Tiny, Mini, Small, Base, Large | Univariate probabilistische Prognosen; ursprüngliche, tokenbasierte Generation. | Apache-2.0; lokal 0 USD Lizenzgebühr. | Tiny/Mini **CPU-begrenzt**; große Varianten extern. Für einen neuen Piloten eher Bolt verwenden. | [Amazon-Repository](https://github.com/amazon-science/chronos-forecasting) |
| **Chronos-Bolt**: Tiny **9M**, Mini **21M**, Small **48M**, Base **205M** Parameter | Direkte Mehrschritt-Quantilprognosen; insbesondere kleine Modelle als günstige Referenz für Vola-Reihen. | Apache-2.0; 0 USD Lizenzgebühr. | Tiny/Mini gute erste **CPU-begrenzte** Kandidaten; Base auf dem gemeinsamen VPS ungünstig. | [Modelle und Implementierung](https://github.com/amazon-science/chronos-forecasting) |
| **Chronos-2**, `amazon/chronos-2`, **120M** | Univariate und multivariate Prognosen, historische und bekannte zukünftige Kovariaten. Kalendermerkmale sind damit grundsätzlich nutzbar. | Apache-2.0; 0 USD Lizenzgebühr. | **CPU-begrenzt**, zunächst kurze Kontexte und wenige Reihen. | [Modellkarte](https://huggingface.co/amazon/chronos-2) |
| **Chronos-2 Small**, `autogluon/chronos-2-small`, **28M**; außerdem **Chronos-2 Synth**, **120M** | Small ist für das kleine Budget besonders interessant; Synth als gesonderter Benchmark-Kandidat. | Beide Modellkarten: Apache-2.0; 0 USD Lizenzgebühr. | Small **CPU-begrenzt**, eher passend als 120M. Synth nicht zusätzlich ohne eigene Forschungsfrage testen. | [Small](https://huggingface.co/autogluon/chronos-2-small), [Synth](https://huggingface.co/autogluon/chronos-2-synth) |
| **TimesFM 2.5**, `google/timesfm-2.5-200m-pytorch`, **200M** | Univariate Prognosen und Quantile; Kovariaten über zusätzliche Regression. | Code und Gewichte bis einschließlich 2.5: Apache-2.0; 0 USD Lizenzgebühr. | **CPU-begrenzt**, auf 4 GB wenig Reserve; kein bevorzugter Produktionskandidat. | [Google-Repository](https://github.com/google-research/timesfm) |
| **TimesFM 3.0**, `google/timesfm-3.0-pytorch` | Neuere Generation mit nativer multivariater Verarbeitung und Kovariaten. | Code Apache-2.0, **Gewichte TimesFM Non-Commercial License v1.0**: kein kommerzieller oder produktiver Eigenbetrieb. Kommerzielle Nutzung über autorisierte Google-Cloud-Dienste möglich; konkreten Gesamtpreis hier nicht verifiziert. | **Extern**; Lizenzfrage geht vor Hardwarefrage. | [Lizenzabgrenzung](https://github.com/google-research/timesfm), [Google Cloud](https://docs.cloud.google.com/bigquery/docs/timesfm-model) |
| **Moirai 1.1-R Small** und **Moirai 2.0-R Small** | Universal-Forecasting-Familie; 2.0 ist eine kleinere, geänderte Architektur. Fähigkeiten nicht zwischen Generationen gleichsetzen. | `uni2ts`-Code Apache-2.0; geprüfte Gewichte **CC-BY-NC-4.0**. Kommerzielle Freigabe und Preis nicht verifiziert. | Small technisch **CPU-begrenzt**; für SeasonAlpha vorerst keine Produktionsempfehlung. | [1.1-Modellkarte](https://huggingface.co/Salesforce/moirai-1.1-R-small), [2.0-Modellkarte](https://huggingface.co/Salesforce/moirai-2.0-R-small), [Code](https://github.com/SalesforceAIResearch/uni2ts) |
| **Lag-Llama**, veröffentlichter Checkpoint `time-series-foundation-models/Lag-Llama` | Univariate Verteilungsprognosen über verzögerte Beobachtungen. Keine Sprachmodell-Anwendung trotz Namen. | Code und Modellkarte Apache-2.0; 0 USD Lizenzgebühr. Numerische Modell-Releaseversion/Commit hier nicht festgehalten. | Kleiner CPU-Pilot plausibel, **CPU-begrenzt**; Sampling und Abhängigkeiten erhöhen Aufwand. | [Repository](https://github.com/time-series-foundation-models/lag-llama), [Gewichte](https://huggingface.co/time-series-foundation-models/Lag-Llama) |
| **TiRex**, erste Generation | Univariate xLSTM-Prognosen. | **NXAI Community License**, einschließlich Attribution; zusätzliche kommerzielle Lizenz bei den dort definierten Umsatzbedingungen, insbesondere über 100 Mio. EUR konsolidiertem Jahresumsatz. Kein allgemeines Apache-Modell. | **CPU-begrenzt**, aber für neue Versuche eher Version 2 prüfen. | [Lizenztext](https://github.com/NX-AI/tirex/blob/main/LICENSE) |
| **TiRex-2**, `NX-AI/TiRex-2` | Multivariat, vergangene und bekannte zukünftige Kovariaten; 38,4M aktive Parameter univariat, zusätzliche 44,1M multivariat. | **Apache-2.0**; 0 USD Lizenzgebühr für öffentliche Version. Pro-Funktionen wie optimiertes Streaming separat; Preis nicht veröffentlicht/verifiziert. | CPU ausdrücklich vorgesehen; **CPU-begrenzt**. Windows kann selbst im CPU-Betrieb MSVC-Build-Werkzeuge benötigen. | [Repository und Plattformhinweise](https://github.com/NX-AI/tirex-2) |
| **Toto 1.0**, `Datadog/Toto-Open-Base-1.0`, **151M** | Multivariate Verteilungsprognosen; Ursprung in Observability-Daten. | Apache-2.0; 0 USD Lizenzgebühr. | **CPU-begrenzt bis extern**; Sampling und mehrere Variablen belasten Speicher/Laufzeit. | [Repository](https://github.com/DataDog/toto) |
| **Toto 2.0**: **4M, 22M, 313M, 1B, 2,5B** | Neuere multivariate Quantilmodelle. Laut Repository sind Fine-Tuning und exogene Variablen für 2.0 noch nicht verfügbar. | Repository Apache-2.0; Lizenz des **22M-Checkpoints** ebenfalls direkt geprüft. Weitere Checkpoints vor Auswahl einzeln festhalten. | 4M/22M interessante **CPU-begrenzte** Kandidaten; große Varianten extern. CPU-Beispiel vorhanden, Anforderungen empfehlen zugleich CUDA: praktisch testen. | [Versionen und Einschränkungen](https://github.com/DataDog/toto), [22M-Modellkarte](https://huggingface.co/Datadog/Toto-2.0-22m) |
| **TabPFN-TS** mit ausdrücklich gewählter TabPFN-Version | Transformiert Zeitreihenprognosen in Tabellenaufgaben mit Zeit- und Lag-Merkmalen. Kein eigenständiger universeller „TS-Checkpoint“. | TS-Code Apache-2.0. **Gewichtelizenz hängt vom TabPFN-Modell ab**; siehe nächste Tabelle. Cloud-Preise nicht belastbar quantifiziert. | Lokal nur sehr kleine Aufgaben **CPU-begrenzt**; kein erster Kandidat für täglich 370 Reihen. | [TabPFN-TS](https://github.com/PriorLabs/tabpfn-time-series), [TabPFN-Lizenzen](https://github.com/PriorLabs/TabPFN) |

**Kleine Shortlist für einen späteren Vergleich:** Chronos-Bolt Tiny, Chronos-2 Small und gegebenenfalls TiRex-2 oder Toto 2.0 22M. Nicht alle gleichzeitig ausprobieren: Jeder zusätzliche Modellversuch erhöht Auswahlaufwand und das Risiko, einen Zufallssieger zu veröffentlichen.

### 2.2 Klassische Statistik und Ökonometrie

Diese Verfahren sind für viele SeasonAlpha-Fragen die sachlich passendere erste Wahl. Sie benötigen kein vortrainiertes Großmodell.

| Familie | Konkrete Bibliothek / Version | Analysen | Lizenz / Kosten | Hardware |
|---|---|---|---|---|
| **EWMA, historische Varianz, HAR-artige Regression** | Eigene kleine Berechnung; Regression über **statsmodels 0.15.0** | Vola-Persistenz, Mehrskalen-Vola, Kalenderzusätze. Mit Tagesrenditen nur HAR-artiger Proxy, kein klassisches Intraday-HAR-RV. | BSD-3-Clause für statsmodels; 0 USD. [Paket](https://pypi.org/project/statsmodels/0.15.0/) | **CPU-gut** |
| **ARCH/GARCH, GJR-GARCH, EGARCH, FIGARCH, APARCH, HARCH** | **arch 8.0.0** | Bedingte Varianz, asymmetrische Reaktion auf negative Renditen, Persistenz, Verteilungsprognosen. | NCSA-Lizenz; 0 USD. [Version/Lizenz](https://pypi.org/project/arch/8.0.0/), [Modellfamilien](https://arch.readthedocs.io/en/stable/univariate/volatility.html) | **CPU-gut**, Fit-Schleifen können dauern |
| **ARIMA/SARIMAX, Zustandsraum, Kalman-Filter, Unobserved Components** | **statsmodels 0.15.0** | Zeitlich veränderliche Mittelwerte, Trends und Messfehler; kleine dynamische Regressionsmodelle. | BSD-3-Clause; 0 USD. [Dokumentation](https://www.statsmodels.org/stable/tsa.html) | **CPU-gut** bei wenigen Zuständen |
| **Markov-Switching** | `MarkovRegression`, `MarkovAutoregression` in **statsmodels 0.15.0** | Unterschiedliche Rendite-/Vola-Zustände und Übergänge. | BSD-3-Clause; 0 USD. [Dokumentation](https://www.statsmodels.org/stable/tsa.html) | **CPU-gut** bei 2–3 Zuständen |
| **Gaussian HMM** | **hmmlearn 0.3.3** | Zustände aus mehreren Merkmalen, etwa Vola, Drawdown und Rendite. | BSD; 0 USD; Projekt weist auf begrenzte Wartung hin. [Paket](https://pypi.org/project/hmmlearn/0.3.3/) | **CPU-gut** |
| **Offline-Changepoints: PELT, Binary Segmentation, Kernelverfahren** | **ruptures 1.1.10** | Historische Strukturbrüche in Vola, Datenquellen oder saisonalen Effekten. | BSD-2-Clause; 0 USD. [Paket](https://pypi.org/project/ruptures/) | **CPU-gut** mit einfachen Kostenfunktionen; Kernelvarianten begrenzen |
| **Bayesian Online Changepoint Detection** | `hildensia/bayesian_changepoint_detection`; **Release/Commit nicht verifiziert** | Laufende Wahrscheinlichkeit eines Strukturwechsels und Länge des aktuellen Abschnitts. | MIT im Repository; 0 USD. [Repository](https://github.com/hildensia/bayesian_changepoint_detection) | **CPU-gut** nur mit begrenzter Run-Length; unbeschränkte Historie vermeiden |
| **Quantilregression** | `QuantReg` in **statsmodels 0.15.0**; `QuantileRegressor` in **scikit-learn 1.9.1** | Untere/obere Renditequantile, Vola-Bänder, robuste bedingte Verteilungen. | BSD-3-Clause; 0 USD. [statsmodels](https://pypi.org/project/statsmodels/0.15.0/), [scikit-learn](https://scikit-learn.org/) | **CPU-gut** für kleine Merkmalszahl |
| **Conformal Prediction / adaptive Kalibrierung** | **MAPIE 1.5.0**, ergänzend explizite zeitliche Kalibrierung | Prognoseintervalle und Deckungsprüfung; Ergänzung eines Prognosemodells. | BSD-3-Clause; 0 USD. [Paket](https://pypi.org/project/MAPIE/), [Lizenz](https://github.com/scikit-learn-contrib/MAPIE/blob/master/pyproject.toml) | **CPU-gut**, Aufwand hängt vom Basismodell ab |

**Wichtige Grenze:** Konforme Intervalle sind bei Finanzzeitreihen keine automatische bedingte Garantie für jeden Marktzustand. Adaptive Verfahren adressieren Verteilungsänderungen; langfristige Deckung ersetzt keine Prüfung der Krisenabschnitte. [Gibbs/Candès](https://arxiv.org/abs/2106.00170)

### 2.3 Machine Learning auf Tabellen und Erklärbarkeit

Aus Kursen, Kalendern, IV und Skew entstehen Tabellenzeilen mit Merkmalen, die **zum jeweiligen Prognosezeitpunkt bekannt waren**. Für diese Aufgaben sind Baumverfahren oft leichter zu betreiben als Transformer.

| Modell / Version | Sinnvoller Einsatz | Lizenz / Kosten | 4 GB CPU? |
|---|---|---|---|
| **Random Forest, Extra Trees, HistGradientBoosting; scikit-learn 1.9.1** | Nichtlineare Zusammenhänge, robuste Vergleichsmodelle, Klassifikation ungewöhnlicher Zustände. | BSD-3-Clause; 0 USD. [Projekt](https://scikit-learn.org/) | **CPU-gut**, Baumtiefe, Baumzahl und Parallelität begrenzen |
| **LightGBM 4.7.0** | Kleine bis mittlere Tabellen, Quantilregression, Vola-/Kalenderinteraktionen. | MIT; 0 USD. [Version](https://pypi.org/project/lightgbm/), [Lizenz](https://github.com/lightgbm-org/LightGBM/blob/main/LICENSE) | **CPU-gut**; bevorzugter zusätzlicher Boosting-Kandidat |
| **XGBoost 3.4.1** | Vergleich zu LightGBM; Regression und Klassifikation mit regulierten Bäumen. | Apache-2.0; 0 USD. [Paket](https://pypi.org/project/xgboost/) | **CPU-gut** mit begrenzter Tabelle und Histogrammverfahren |
| **CatBoost 1.2.10** | Daten mit Kategorien wie Markt, Ereignistyp und Instrumentklasse. | Apache-2.0; 0 USD. [Paket](https://pypi.org/project/catboost/) | **CPU-gut bis begrenzt**; Kategorien erlauben keine zufällige Zeitaufteilung |
| **TabPFN-2** | Kleine Tabellen als Foundation-Modell-Vergleich ohne großes Hyperparameter-Tuning. | Prior Labs License: Apache-2.0 mit zusätzlicher Attribution; keine pauschale Gleichsetzung mit unverändertem Apache. | Kleine Fälle **CPU-begrenzt**; größerer Kontext und Ensembles teuer. [Quelle](https://github.com/PriorLabs/TabPFN) |
| **TabPFN-2.5, 2.6 und 3** | Neuere Generationen; Repository verwendet inzwischen Version 3 standardmäßig. | **Nichtkommerzielle Gewichtelizenzen**; kommerzielle Lizenz/API separat. Konkreter SeasonAlpha-Tarif nicht verifiziert. | Lokal kein bevorzugter VPS-Kandidat. Automatische Standardauswahl nicht ungeprüft übernehmen. [Lizenzen](https://github.com/PriorLabs/TabPFN), [Preise/Zugang](https://priorlabs.ai/pricing) |
| **SHAP 0.53.0** | Beiträge von Eingaben zur Modellvorhersage; bevorzugt TreeSHAP für kleine Baumensembles. | MIT; 0 USD. Version 0.53.0 am 09.10.2026 veröffentlicht. [Paket](https://pypi.org/project/shap/) | **CPU-gut** für begrenzte Stichproben; allgemeines KernelSHAP kann teuer werden |

SHAP erklärt ein Modell, **nicht die Ursache einer Marktbewegung**. Bei stark korrelierten Merkmalen können sich Zuschreibungen ändern, obwohl die Vorhersage ähnlich bleibt. [SHAP-Dokumentation zur Kausalitätsgrenze](https://shap.readthedocs.io/en/latest/example_notebooks/overviews/Be%20careful%20when%20interpreting%20predictive%20models%20in%20search%20of%20causal%20insights.html)

### 2.4 Unüberwachtes Lernen und Ähnlichkeit

| Verfahren / Version | Anwendung | Lizenz / Kosten | Hardware |
|---|---|---|---|
| **KMeans, Gaussian Mixture, hierarchisches Clustering, PCA; scikit-learn 1.9.1** | Marktgruppen, ähnliche Risikocharakteristika, Konzentration gemeinsamer Bewegungen. | BSD-3-Clause; 0 USD. [Projekt](https://scikit-learn.org/) | **CPU-gut** für 370 Ticker |
| **Korrelation / standardisierte euklidische Distanz** | Transparente erste Ähnlichkeitssuche für Renditevektoren. | Eigene Berechnung; keine Modellgebühr. | **CPU-gut**; 370 Ticker ergeben 68.265 eindeutige Paare |
| **DTW; dtaidistance 2.5.1** | Ähnliche Formen trotz begrenzter zeitlicher Verschiebung. | Apache-2.0; 0 USD. [Paket](https://pypi.org/project/dtaidistance/) | **CPU-gut** für kurze Fenster und begrenzten Warping-Korridor |
| **Matrix Profile; STUMPY 1.14.1** | Wiederkehrende Teilmuster und ungewöhnliche Abschnitte innerhalb langer Reihen. | BSD-3-Clause; 0 USD. [Paket](https://pypi.org/project/stumpy/) | Speicher oft beherrschbar, CPU-Zeit kann groß werden; zunächst einzelne Reihen |
| **Isolation Forest; scikit-learn 1.9.1** | Mehrdimensionale Datenauffälligkeiten und ungewöhnliche Marktbeobachtungen. | BSD-3-Clause; 0 USD. [Projekt](https://scikit-learn.org/) | **CPU-gut** |

Für Kursähnlichkeit werden **numerische Renditevektoren** verglichen. Text-Embeddings sind dafür kein sinnvoller Standardersatz.

### 2.5 Sprachmodelle für Analysen und Forschung

Geeignete Aufgaben: Quellenpassagen extrahieren, Studien strukturieren, Methoden erklären, Faktenblätter formulieren, Übersetzungen prüfen und Forschungscode entwerfen. Kennzahlen und statistische Tests werden weiterhin deterministisch berechnet.

**Preise: USD je 1 Mio. Eingabe-/Ausgabe-Tokens**, Standardverarbeitung, ohne Cache, Tools, Steuern oder Sonderverträge. Bei OpenAI gilt die unten ausgewiesene kurze Kontextstufe, bei Haiku höchstens 100.000 Eingabe-Tokens.

| Modellversion | Einsatz bei SeasonAlpha | Preis Input / Output | Lizenz und Hardware |
|---|---|---:|---|
| **GPT-6 Luna**, `gpt-6-luna` | Extraktion, Klassifikation, kurze Faktenblatt-Texte. | **0,10 / 0,50** | Proprietäre API; **API**, kein lokaler Betrieb |
| **GPT-6.1 Sol**, `gpt-6.1-sol` | Forschungsassistenz, Code, anspruchsvollere Erklärungen und Prüfungen. | **2,00 / 10,00** | Proprietäre API; **API** |
| **GPT-6 Astra**, `gpt-6-astra` | Einzelne schwierige Methoden- und Codeprüfungen. | **10,00 / 50,00** | Proprietäre API; **API**, für Massenberichte unnötig teuer |

Versionen und Preise laut [offizieller OpenAI-Preisliste](https://developers.openai.com/api/docs/pricing). Kontospezifischer Zugang und unveränderliche Snapshot-IDs wurden nicht praktisch geprüft.

| Modellversion | Einsatz bei SeasonAlpha | Preis Input / Output | Lizenz und Hardware |
|---|---|---:|---|
| **Claude Haiku 5.5** | Kurze Extraktionen, Routing, Faktenblatt-Texte. | **0,10 / 0,50** | Proprietäre API; **API** |
| **Claude Sonnet 5.5** | Redaktionelle Analyse, Quellenvergleich, Codeassistenz. | **2,00 / 10,00** | Proprietäre API; **API** |
| **Claude Opus 5.5** | Schwierige Forschungs- und Methodikprüfungen. | **4,00 / 20,00** | Proprietäre API; **API** |

Preise laut [Anthropic-Dokumentation](https://platform.claude.com/docs/en/about-claude/pricing). Haiku wird oberhalb der genannten Kontextgrenze teurer. Modellgenerationen sind geprüft; konkrete API-Snapshot-IDs und Kontozugang bleiben vor Implementierung zu prüfen.

| Modellversion | Einsatz bei SeasonAlpha | Preis Input / Output | Lizenz und Hardware |
|---|---|---:|---|
| **Gemini 3.1 Flash-Lite**, `gemini-3.1-flash-lite` | Günstige Extraktion und Übersetzung als Vergleichskandidat. | **0,25 / 1,50** | Proprietäre API; **API** |
| **Gemini 3.5 Flash-Lite**, `gemini-3.5-flash-lite` | Neuere kleine Variante; Qualität gegen 3.1 messen. | **0,30 / 2,50** | Proprietäre API; **API** |
| **Gemini 3.8 Flash**, `gemini-3.8-flash` | Anspruchsvollere Text- und Codeaufgaben. | **0,75 / 3,75** bis 31.12.2026; danach laut Liste **1,50 / 7,50** | Proprietäre API; **API** |

Preise einschließlich der Behandlung von Thinking-Tokens laut [Google-Preisliste](https://ai.google.dev/gemini-api/docs/pricing). Bezahlte API-Nutzung und kostenlose Testangebote haben unterschiedliche Bedingungen.

**Kostenbeispiel:** 1.000 Analysen mit jeweils 2.000 Input- und 500 abgerechneten Output-Tokens kosten rechnerisch **0,45 USD** bei GPT-6 Luna oder Haiku 5.5, **9 USD** bei GPT-6.1 Sol oder Sonnet 5.5 und **3,38 USD** bei Gemini 3.8 Flash zum Einführungspreis. Das ist eine eigene Rechnung aus den genannten Tarifen, ohne Wiederholungen und Prüfaufrufe. Gleiche Texte erzeugen je Anbieter unterschiedlich viele Tokens.

#### Offene beziehungsweise herunterladbare Sprachmodelle

| Konkreter Checkpoint | Lizenz / Kosten | 4-GB-CPU-Eignung und Einsatz |
|---|---|---|
| **`Qwen/Qwen3.5-0.8B`** | Apache-2.0; 0 USD Lizenzgebühr. [Modellkarte](https://huggingface.co/Qwen/Qwen3.5-0.8B) | Quantisiert und mit kurzem Kontext plausibel **CPU-begrenzt**. Für enges Tagging testen; Qualität für deutsche Finanztexte nicht nachgewiesen. |
| **`meta-llama/Llama-3.2-1B-Instruct`**, alternativ 3B | Llama-3.2-Community-Lizenz mit Nutzungsbedingungen; keine unveränderte Open-Source-Lizenz. [Modellkarte/Lizenz](https://huggingface.co/meta-llama/Llama-3.2-1B-Instruct) | 1B quantisiert plausibel; 3B auf gemeinsamem VPS enger. Kleine lokale Extraktionsaufgaben, kein Ersatz für geprüfte Fakten. |
| **`mistralai/Ministral-3-3B-Instruct-2512-BF16`** | Apache-2.0; 0 USD Lizenzgebühr. [Modellkarte](https://huggingface.co/mistralai/Ministral-3-3B-Instruct-2512-BF16) | Original-BF16-Gewichte passen nicht sinnvoll in 4 GB. Quantisierte Variante mit kurzem Kontext eventuell; konkrete Quantisierung und Laufzeit nicht geprüft. |
| **Llama 4 Scout**, `Llama-4-Scout-17B-16E-Instruct` | Eigene Llama-4-Community-Lizenz, zusätzliche Nutzungs- und regionale Bedingungen beachten. [Modellkarte](https://huggingface.co/meta-llama/Llama-4-Scout-17B-16E-Instruct) | **Extern**. Aktive Parameter sind nicht gleich insgesamt zu ladende Gewichte. Kein Kandidat für diesen VPS. |

Ein selbst betriebenes kleines LLM ist bei geringem Textvolumen nicht automatisch wirtschaftlicher als die API. Es bindet RAM, benötigt Pflege und muss dieselben Qualitätsprüfungen bestehen.

#### Embeddings

| Modell | Einsatz | Lizenz / Preis | Hardware |
|---|---|---|---|
| **`text-embedding-3-small`** | Semantische Suche über eigene Studien, Methodenseiten und Quellenpassagen. | Proprietäre API, **0,02 USD/Mio. Tokens**. [OpenAI-Modellseite](https://developers.openai.com/api/docs/models/text-embedding-3-small) | **API** |
| **`intfloat/multilingual-e5-small`** | Lokale deutsch-englische Dokumentensuche. | MIT; 0 USD Lizenzgebühr. [Modellrevision](https://huggingface.co/intfloat/multilingual-e5-small/tree/fd1525a9fd15316a2d503bf26ab031a61d056e98) | Kleine Batches **CPU-begrenzt**, grundsätzlich passend |
| **`BAAI/bge-m3`** | Mehrsprachige Suche mit mehreren Retrieval-Verfahren. | MIT; 0 USD Lizenzgebühr. [Modellkarte](https://huggingface.co/BAAI/bge-m3) | Für den VPS deutlich schwerer; zunächst außerhalb testen |

Bei einem kleinen Dokumentbestand zuerst Volltextsuche beziehungsweise TF-IDF vergleichen. Eine zusätzliche Vektordatenbank ist nicht automatisch erforderlich.

### 2.6 Ereignisstudien und kausale Methoden

| Methode / Implementierung | Nutzen | Lizenz / Kosten / Hardware | Einschränkung |
|---|---|---|---|
| **Ereignisstudie mit Marktmodell**, statsmodels 0.15.0 | Rendite oder Vola um OPEX, FOMC, Wahlen und Indexereignisse relativ zu einer Referenz untersuchen. | BSD-3-Clause; 0 USD; **CPU-gut**. [Bibliothek](https://www.statsmodels.org/stable/tsa.html) | Ein zeitlicher Zusammenhang beweist keine Verursachung. |
| **Synthetic Control**, **pysyncon 1.7.0** | Vergleichspfad aus mehreren unbehandelten Reihen für eine klar definierte Intervention. | MIT; 0 USD; **CPU-gut** bei kleinem Kontrollpool. [Paket](https://pypi.org/project/pysyncon/) | Kontrollmärkte dürfen nicht ebenfalls wesentlich betroffen sein; guter Vorperioden-Fit erforderlich. |
| **Difference-in-Differences**, R-Paket **did 2.3.0** | Unterschiedliche Veränderungen bei behandelten und geeigneten unbehandelten Gruppen, auch mit verschiedenen Behandlungszeitpunkten. | GPL-3; 0 USD; **CPU-gut** für kleine Panels. [Release](https://github.com/bcallaway11/did/releases), [Projekt/Lizenz](https://bcallaway11.github.io/did/) | Paralleltrend-Annahme, keine Vorwegnahme und geeignete Vergleichsgruppen begründen. |

Mit dem heutigen Datenbestand sind **Ereignisstudien unmittelbar plausibler als kausale Studien**. Ein FOMC-Termin betrifft viele Märkte gleichzeitig; „DAX als unbehandelte Kontrolle für SPY“ ist deshalb nicht ohne Weiteres tragfähig. Die Voraussetzungen für DiD sind Teil der Identifikation, nicht etwas, das ein leistungsfähigeres Modell ersetzt. [Callaway/Sant’Anna](https://arxiv.org/abs/1803.09015)

## 3. Gemeinsames Forschungsprotokoll

Die folgenden Regeln gelten für alle vorgeschlagenen Analysen. Abweichungen müssen **vor** der jeweiligen Auswertung feststehen.

1. **Eine Hauptfrage und eine primäre Zielgröße.** Universum, Horizonte, Ausschlüsse, Modellvarianten und Abbruchkriterium vorab festhalten. Alle ausprobierten Varianten protokollieren, auch erfolglose.

2. **Historische Entwicklung und echte Bestätigung trennen.** Standard für Kursstudien: Entwicklung auf verfügbaren Daten 2000–2014, historische Walk-forward-Auswertung 2015–2025, neuere Daten bis zum eingefrorenen Stichtag separat. Bereits untersuchte Jahre gelten nicht erneut als unberührter Test. Echte prospektive Prüfung beginnt erst nach Protokollfreigabe und Daten-Freeze.

3. **Nur damals verfügbare Informationen.** Beispiel: Prognose nach Schluss von Tag \(t\); Merkmale dürfen höchstens bis zu diesem Zeitpunkt reichen. Trainingsziele müssen vollständig beobachtet sein. Für einen Horizont von 21 Sitzungen fallen entsprechend die jüngsten noch nicht ausgereiften Trainingslabels weg. Skalierung, Cluster, Quantile und Merkmalsauswahl werden ausschließlich im Training bestimmt.

4. **Walk-forward passend zur Aufgabe.** Standard: fünf Jahre rollendes Training, jährliches Neuschätzen; komplexere Modelle mit innerer zeitlicher Validierung. Bei kurzen Options-/Polymarket-Historien chronologisch 60 % Entwicklung, 20 % Auswahl, 20 % eingefrorene Auswertung, sofern ausreichend unabhängige Fälle existieren. Andernfalls nur beschreiben und prospektiv sammeln.

5. **Abhängigkeiten und Mehrfachtests berücksichtigen.** Kursstudien: gemeinsames Block-Bootstrap über die beteiligten Märkte, beispielsweise 63 Sitzungen bei Horizonten bis 21 Tagen, mit vorab festgelegter Sensitivitätsprüfung. Ereignisse nach Ereignisdatum, Polymarket nach gemeinsamem Ereignis clustern. Primäre Testfamilien mit Holm oder gemeinsamem Max-T kontrollieren; explorative Karten gegebenenfalls mit FDR kennzeichnen. Keine 370 Einzelergebnisse unbereinigt nach „Signifikanz“ sortieren.

6. **Gegen eine starke einfache Referenz prüfen.** Rendite: Nullprognose beziehungsweise historische Basisrate; Vola: EWMA und historische Varianz; Intervalle: historische Quantile und EWMA-Band; Polymarket: unveränderter Marktpreis und ausschließlich aus früheren Ereignissen geschätzte Basisrate.

7. **Reproduzierbarkeit und Betrieb mitbewerten.** Daten-Hash, Datenstand, Zeitkonvention, Modellrevision, Lizenzstand, Seeds, Paketversionen, Laufzeit und maximalen RAM speichern. Ein Modellgewinn, der auf einen Markt, ein Krisenjahr oder einen zufälligen Seed beschränkt bleibt, ist kein allgemeiner Produktnachweis.

Diese Regeln adressieren insbesondere die Auswahlverzerrung durch wiederholte Backtests. Eine nachträgliche Korrektur einzelner p-Werte repariert nicht beliebig viele undokumentierte Forschungsentscheidungen. [Bailey et al.](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf)

## 4. Analysekatalog

**Status:** **B** = beschreibend; **P** = prognostisch; **K** = kausaler Anspruch nur bei erfüllten Voraussetzungen.  
**Aufwand:** eigene Schätzung in Entwicklertagen für einen ersten reproduzierbaren Forschungsstand, ohne Beschaffung fehlender Daten und ohne Wartezeit für prospektive Beobachtungen.

### A1. Datenqualität: Welche Auffälligkeiten sind Fehler, welche echte Marktbewegungen? — B

- **Daten/Modelle:** OHLC, Close, `log_return`, Handelskalender, Quellenwechsel; Konsistenzregeln, robuste MAD-Abweichungen, optional Isolation Forest.
- **Referenz/Zielgröße:** Regeln allein; primär Erkennung bestätigter kritischer Fehler, zusätzlich Fehlalarmrate und Prüfaufwand.
- **Protokoll:** Gesamte verfügbare Historie; Entwicklungsfälle bis 2023, eingefrorener Test 2024–Stichtag. Reale Fälle plus klar markierte künstliche Fehler; bestimmte Fehlertypen und Ticker vollständig zurückhalten. Schwellen nur im Entwicklungssatz wählen.
- **Nutzen:** Datenqualitätskarte und Blog „Wie zuverlässig sind sehr lange Börsenhistorien?“.
- **Aufwand/Risiko:** **3–5 Tage**. Seltene echte Sprünge dürfen nicht automatisch gelöscht werden; synthetische Fehler bilden reale Fehler nur teilweise ab.

### A2. Stabilität saisonaler Muster statt erneuter Score-Prognose — B

- **Frage:** Bleiben Monats-, TDOM- und ausgewählte TDOY-Effekte über Jahrzehnte, Quellen und Märkte ähnlich?
- **Daten/Modelle:** Rohkurse, Kalender, neu berechnete Saisonstatistiken; robuste Regression, Shrinkage und Block-Bootstrap.
- **Referenz/Zielgröße:** Unbedingte Rendite desselben Instruments; primär geschrumpfte Effektgröße und ihre Stabilität zwischen Teilperioden.
- **Protokoll:** 2000–2025 als Hauptfenster, ältere Historien separat. Jährliche Schätzung nur mit Vergangenheit; vorab beispielsweise zwölf Monatsfragen und ein ToM-Fenster festlegen. Max-T/Holm über alle primären Märkte und Fenster.
- **Nutzen:** „Stabilität des historischen Musters“ mit Fallzahl und Unsicherheit.
- **Aufwand/Risiko:** **4–6 Tage**. Sehr viele Fenster erzeugen Scheinfunde; ein stabiler historischer Mittelwert ist noch keine rentable Strategie.

### A3. Wo entsteht ein Kalendereffekt: über Nacht oder während der Sitzung? — B

- **Daten/Modelle:** Konsistent angepasste OHLC-Reihen; getrennte Close-to-Open- und Open-to-Close-Renditen, robuste Regression.
- **Referenz/Zielgröße:** Alle vergleichbaren Handelstage; Differenz der mittleren Renditen je Teil der Sitzung.
- **Protokoll:** Ab erstem nachweislich konsistentem OHLC-Jahr, Zielbereich 2005–2025; Entwicklung bis 2014, jährliche Fortschreibung danach. Ein festes ToM-Fenster, beide Renditekomponenten gemeinsam korrigieren.
- **Nutzen:** Studie „Monatswechsel: Nacht- oder Tageseffekt?“.
- **Aufwand/Risiko:** **3–5 Tage**. Gemischte Adjustierungen können einen künstlichen Overnight-Effekt erzeugen; keine Handelskosten- oder Ausführbarkeitsbehauptung ohne Zusatzprüfung.

### A4. Kalenderabhängige Volatilität — B, später P

- **Frage:** Sind Schwankungen um OPEX, FOMC und Feiertage anders als an vergleichbaren Tagen?
- **Daten/Modelle:** Tagesrenditen, optional OHLC-Spannen, Ereigniskalender; Ereignisregression, EWMA/HAR mit Kalenderindikatoren.
- **Referenz/Zielgröße:** Tage mit ähnlichem Wochentag, Monat und vorheriger Vola; primär Verhältnis zukünftiger Fünf-Tage-Varianz.
- **Protokoll:** 2000–2025, jährliches Walk-forward ab 2015. Drei vorab definierte Ereignisklassen, ein Horizont; gemeinsame Ereignisse und überlappende Fenster berücksichtigen, Holm-Korrektur.
- **Nutzen:** Kalender-Risikokontext und Studien über Ereigniswochen.
- **Aufwand/Risiko:** **4–6 Tage**. Geplanter Termin ist nicht gleich Überraschung; täglich gemessene Renditen isolieren keinen FOMC-Intraday-Effekt.

### A5. Vola-Prognose mit nachvollziehbarem Zusatznutzen — P

- **Daten/Modelle:** Close-Renditen; EWMA, HAR-artige Regression, GARCH/GJR-GARCH; später genau ein Boosting-Modell.
- **Referenz/Zielgröße:** EWMA mit vorab festem Parameter und 20-Tage-Mittel der quadrierten Renditen; primär QLIKE für zukünftige Fünf-Tage-Varianz, sekundär Vola-MAE.
- **Protokoll:** Standard-Walk-forward; SPY, QQQ, GLD sowie vorab ergänzte weitere Assetklassen. Der bereits untersuchte Zeitraum bleibt Entwicklungsevidenz. Modelle/Horizonte gemeinsam korrigieren; prospektive Prognosen archivieren.
- **Nutzen:** Forschungsbericht; später gegebenenfalls kalibrierte Risikoanzeige.
- **Aufwand/Risiko:** **4–7 Tage**. Fehlermaß entscheidet über Rangfolge; geringe Varianzfehler bedeuten weder Renditeprognose noch profitable Optionsstrategie.

### A6. Haben Expected-Move-Bänder tatsächlich die angezeigte Deckung? — B über Prognosen

- **Daten/Modelle:** Historische, zeitgestempelte ATM-IV, Spot, genaue Laufzeit und spätere Kurse; empirische Deckung, Quantilkalibrierung, optional adaptive Conformal-Verfahren.
- **Referenz/Zielgröße:** Historisches Quantilband und EWMA-Band; primär Deckung **gemeinsam mit Breite/Intervallscore**.
- **Protokoll:** Vollständige geprüfte Optionshistorie bis Stichtag, chronologische Aufteilung nach Abschnitt 3. Endkurs innerhalb des Bandes und zwischenzeitliche Berührung als verschiedene Fragen behandeln. Reife Horizonte und gemeinsame Markttage berücksichtigen.
- **Nutzen:** `/skew`: „So häufig hielt dieses Band historisch“.
- **Aufwand/Risiko:** **4–7 Tage nach Export**. `IV × √Zeit` ist ohne Verteilungsannahmen kein garantiertes 68%-Band. Optionen verwenden Kalenderzeit; Zielkurse müssen exakt dazu passen.

### A7. IV gegen später realisierte Schwankung — B, optional P

- **Frage:** Wie unterscheiden sich heutige implizite und anschließend realisierte Varianz?
- **Daten/Modelle:** IV konstanter Laufzeit, spätere Tagesrenditen; robuste Regression, Quantilregression.
- **Referenz/Zielgröße:** Vorherige realisierte Vola und EWMA; primär Differenz zwischen IV² und laufzeitgerecht gemessener späterer Varianz.
- **Protokoll:** Geprüfte Optionshistorie; ein Hauptzeitraum, beispielsweise 30 Kalendertage, quartalsweise Walk-forward-Neuschätzung. Ticker gemeinsam korrigieren, überlappende Laufzeiten blockweise auswerten.
- **Nutzen:** Verständlicher Vergleich von eingepreister und eingetretener Schwankung.
- **Aufwand/Risiko:** **4–6 Tage**. Das im Code vorhandene `vrp_pts = IV − vergangene RV` ist ein anderer Messwert. ATM-IV² minus spätere Varianz ist zudem nur ein Proxy, keine modellfreie Varianzrisikoprämie. [Bestehende Berechnung](/C:/dev/Seasonaledge/scripts/compute_options_skew.py:858)

### A8. Enthält Skew zusätzliche Information über linke Verteilungsränder? — P

- **Daten/Modelle:** 25-Delta-Skew, IV, vorherige Vola und Renditen; lineare Quantilregression, später kleines LightGBM.
- **Referenz/Zielgröße:** Identisches Modell ohne Skew; primär Pinball-Loss des unteren 10%-Quantils der Fünf-Tage-Rendite.
- **Protokoll:** Nur konstante, qualitätsgeprüfte Laufzeitdefinition; chronologischer Split, quartalsweise Walk-forward. Ein Quantil, ein Horizont, begrenztes Universum; Korrektur über Modellvergleiche.
- **Nutzen:** Studie „Was sagt teurer Abwärtsschutz tatsächlich?“.
- **Aufwand/Risiko:** **5–8 Tage**. Skew kann Absicherungsnachfrage und Risikoprämien widerspiegeln; extreme Verluste sind selten. Fehlender Zusatznutzen ist ein veröffentlichungsfähiger Befund.

### A9. GEX und OI: Sensitivität der Modellannahmen — B

- **Frage:** Wie stark hängt die GEX-Aussage von Vorzeichen, OI-Alter, IV und einbezogenen Verfällen ab?
- **Daten/Modelle:** Optionsketten, OI je Strike, Spot und IV; deterministische Szenarien, keine KI erforderlich.
- **Referenz/Zielgröße:** Bestehende Call-plus/Put-minus-Konvention; primär Anteil der Fälle, in denen Vorzeichen oder zentrale Levels unter plausiblen Annahmen wechseln.
- **Protokoll:** Alle verfügbaren archivierten Ketten bis Stichtag; zusätzlich vier Wochen tägliche Snapshots. Sensitivitätsszenarien vorher festlegen; keine nachträgliche Auswahl nach Kursverlauf.
- **Nutzen:** „Annahmen hinter GEX“ und Unsicherheitsanzeige.
- **Aufwand/Risiko:** **3–5 Tage**. Ohne Rohkettenhistorie zunächst nur Snapshot-Studie. Alternative Vorzeichen sind Szenarien, keine beobachteten Dealer-Bücher.

### A10. Regime: Liefert ein gelerntes Modell mehr als die Stress-Ampel? — B

- **Daten/Modelle:** Vola, Drawdown, Rendite; Gaussian HMM mit 2–3 Zuständen oder Gaussian Mixture.
- **Referenz/Zielgröße:** Bestehende Stress-Regeln; primär Zustandsstabilität und zusätzlicher beschreibender Informationsgehalt.
- **Protokoll:** Training 2000–2014, jährliche Walk-forward-Auswertung 2015–2025. Nur gefilterte Zustände; keine rückblickend geglätteten Echtzeitlabels. Seeds und kleine Datenänderungen vorab definieren; Zustände für Vergleiche zuordnen.
- **Nutzen:** Beschreibung ähnlicher Risikoumgebungen.
- **Aufwand/Risiko:** **4–6 Tage**. Labels wie „Bärenmarkt“ verleiten zu Prognosen; nachträglich wechselnde Regime können historische Charts irreführend verbessern.

### A11. Strukturbrüche in Vola und Saisonmustern — B

- **Daten/Modelle:** Renditen, Vola-Proxies, rollende Saisonparameter; PELT und optional BOCPD.
- **Referenz/Zielgröße:** Feste Dekaden beziehungsweise einfache CUSUM-/Schwellenregel; primär Fehlalarmrate und Erkennungsverzögerung bei kontrollierten Veränderungen.
- **Protokoll:** Simulierte Reihen zur Schwellenwahl, anschließend historische Auswertung 2000–2025. Onlineverfahren Tag für Tag wiedergeben; Offline-Brüche ausdrücklich als rückblickend markieren. Korrektur über Reihen und getestete Merkmale.
- **Nutzen:** Studie „Wann änderte sich ein historischer Befund?“.
- **Aufwand/Risiko:** **4–6 Tage**. Ein Bruch ist keine Erklärung seiner Ursache; Quellenwechsel können wie Marktregime aussehen.

### A12. Intermarket: Gemeinsame Risiken statt vermeintlicher Vorläufersignale — B

- **Daten/Modelle:** Synchronisierte Renditen der vorhandenen Märkte; rollende Korrelation, Shrinkage-Kovarianz, PCA und Clustering.
- **Referenz/Zielgröße:** Einfache 60-Tage-Korrelation; primär Stabilität von Gruppen und Konzentration gemeinsamer Bewegungen.
- **Protokoll:** 2005–2025; monatliche Stichtage, Merkmale jeweils nur aus vorangegangenen 60/252 Sitzungen. Fenster vorher festlegen. Globale Strukturtests statt nachträglicher Jagd nach einzelnen Paaren.
- **Nutzen:** „Welche Märkte bewegen sich derzeit ähnlich?“ und historische Diversifikationsstudien.
- **Aufwand/Risiko:** **3–5 Tage**. Unterschiedliche Börsenschlusszeiten erzeugen scheinbaren Vorlauf; Korrelation ist keine Kausalität oder stabile Absicherung.

### A13. Historische Analogien mit Zufallsreferenz — B

- **Daten/Modelle:** Standardisierte 60-Tage-Renditepfade; Korrelation, DTW, optional Matrix Profile.
- **Referenz/Zielgröße:** Korrelation und passend gezogene zufällige historische Fenster; primär Nützlichkeit/Stabilität der Treffer, nicht spätere Rendite.
- **Protokoll:** Monatliche historische Suchstichtage 2015–2025. Nur damals vergangene Fenster; überlappende Nachbarfenster ausschließen. Distanz und Warping-Korridor vorher festlegen; 100 verblindet beurteilte Fälle.
- **Nutzen:** Forschungsnavigation mit ähnlichen und unähnlichen Beispielen.
- **Aufwand/Risiko:** **3–5 Tage**. Sobald Folgeverläufe gezeigt werden, kann auch ein Band als Prognose verstanden werden. Eine Nutzung zur Zukunftsaussage benötigt einen separaten Prognosetest.

### A14. Polymarket: Wie gut sind Preise nach Horizont und Ereignisklasse kalibriert? — B über Prognosen

- **Daten/Modelle:** Vor Auflösung gespeicherte Preise, Ergebnis, Ereignis-ID und Zeitstempel; Reliability-Diagramme, Brier-Score, optional logistische Kalibrierung.
- **Referenz/Zielgröße:** Unveränderter Marktpreis, frühere Klassenbasisrate und 50/50 als zusätzliche Referenz; primär Brier-Score je unabhängiges Ereignis.
- **Protokoll:** Alle geprüften aufgelösten Märkte bis Stichtag; Hauptmessung sieben Tage vor festgelegtem Ereignistermin, weitere Horizonte sekundär. Nur vorher bekannte Preise, keine nachträgliche Interpolation. Chronologische Ereignissplits, Bootstrap nach Ereignisfamilie, Holm über Kategorien.
- **Nutzen:** `/polymarket`: empirische Verlässlichkeit statt bloßer Prozentanzeige.
- **Aufwand/Risiko:** **4–7 Tage**. Viele verwandte Verträge sind kein großes unabhängiges Sample; administrative Auflösung kann später als das Bekanntwerden des Ergebnisses liegen.

### A15. Polymarket: Welche scheinbaren Unterschiede sind nur Preis- oder Definitionsprobleme? — B

- **Daten/Modelle:** Preise, Alter der letzten Beobachtung, verfügbare Liquiditätsdaten, Markttexte und Auflösungsregeln; Regeln, robuste Ausreißerprüfung, LLM nur zur belegten Textextraktion.
- **Referenz/Zielgröße:** Ungefilterte Anzeige; primär Anteil korrekt erkannter veralteter oder semantisch unvereinbarer Vergleiche.
- **Protokoll:** Historische Stichprobe bis 2025 entwickeln, 2026 bis Stichtag zurückhalten; 200 manuell beurteilte Fälle, ganze Ereignisfamilien trennen. Reine Qualitätsprüfung benötigt keinen Rendite-Walk-forward; Schwellen dennoch zeitlich einfrieren.
- **Nutzen:** Frische- und Vergleichbarkeitshinweise.
- **Aufwand/Risiko:** **3–5 Tage**. Fehlende Bid-/Ask-Historie begrenzt das Urteil. Angezeigter Preis kann Midpoint oder letzter Handel sein. [Polymarket-Preismethodik](https://help.polymarket.com/en/articles/13364488-how-are-prices-calculated)

### A16. Wahlen und Börse: Wie viel bleibt nach geeigneten Vergleichsjahren? — B

- **Daten/Modelle:** Wahlkalender, Indexkurse und vorhandene Kontrolljahre; Ereignisstudie, robuste Mittelwerte, Leave-one-election-out.
- **Referenz/Zielgröße:** Nach identischer Kalenderregel bestimmte Pseudotermine; primär 20-Sitzungs-Renditedifferenz, Vola sekundär.
- **Protokoll:** US-Wahlen ab 1950 bis 2024 als Hauptstudie; ältere Wahlen gesondert. Frühere Wahlzyklen schätzen, späteren Zyklus auswerten; Korrektur über Wahlarten und Indizes.
- **Nutzen:** Fortführung der Wahlseite mit Einfluss einzelner Wahlen und Unsicherheitsband.
- **Aufwand/Risiko:** **3–5 Tage**. Wenige unabhängige Wahlen, sich wandelnde Indizes und historische Börsenschließungen; kein Nachweis, dass eine Partei Renditen verursacht.

### A17. Kontrollierter Vergleich kleiner Foundation-Modelle — P

- **Daten/Modelle:** Wöchentliche Vola-Proxies aus Kursen; Chronos-Bolt Tiny, Chronos-2 Small und genau ein weiterer Kandidat.
- **Referenz/Zielgröße:** EWMA, HAR und kleines LightGBM; primär gleicher probabilistischer Score, beispielsweise WIS, plus Laufzeit/RAM.
- **Protokoll:** Zunächst höchstens zehn vorab gewählte Reihen. Historisches Walk-forward nur als Benchmark; mögliche Überschneidung mit Vortrainingsdaten dokumentieren. Prospektive Auswertung nach Modell-Freeze, gemeinsame Korrektur über Kandidaten.
- **Nutzen:** Technisch gehaltvolle Studie „Hilft ein Foundation-Modell bei Börsenvolatilität?“.
- **Aufwand/Risiko:** **5–10 Tage**. Modellquantile sind nicht automatisch kalibriert; unbekannte Trainingsdaten erschweren unabhängige historische Nachweise.

### A18. Faktenblätter und Forschungsbefunde verständlich erklären — B

- **Daten/Modelle:** Ausschließlich berechnete Kennzahlen, Methoden und Quellen; kleines API-LLM, optional Embeddings für bereits freigegebene Dokumente.
- **Referenz/Zielgröße:** Deterministische Textvorlage; primär belegte Aussagekorrektheit, sekundär Bearbeitungszeit und Leserverständnis.
- **Protokoll:** 100 unterschiedliche Faktenblätter; 60 zur Entwicklung, 40 eingefroren testen, darunter Nullbefunde, fehlende Werte und widersprüchliche Teilperioden. Ticker/Studientypen gruppenweise trennen; zusätzlich neue Wochenstände prospektiv prüfen. Anbieter paarweise auf denselben Fällen vergleichen.
- **Nutzen:** Methodenerklärungen und redaktionelle Forschungsassistenz.
- **Aufwand/Risiko:** **3–5 Tage**. Zahlenprüfung allein erkennt keine falsche Kausalaussage. Kein autonomes Erfinden von Marktgründen oder Quellen.

### Bedingter Ausbau: Synthetic Control oder DiD

**Mögliche Frage:** Veränderte eine genau definierte Indexaufnahme, Handelsregel oder landesspezifische Intervention die betroffenen Instrumente gegenüber einem glaubwürdigen Kontrollpool?

Die Kursdaten können das Ergebnis messen. Zusätzlich benötigt werden jedoch überprüfte historische Behandlungszeitpunkte, damalige Gruppenzugehörigkeit und eine begründete Kontrollgruppe. Diese vollständige Grundlage ist hier **nicht nachgewiesen**.

Erster Entwurf: Vorperiode −250 bis −21 Sitzungen, getrenntes Antizipationsfenster, Nachperiode 0 bis +20; einfacher Marktvergleich als Referenz; Placebozeitpunkte und Placeboinstrumente; simultane Unsicherheit. **6–10 Tage nach Datenfreigabe.** Ohne tragfähige Identifikation bleibt das Ergebnis eine beschreibende Ereignisstudie. [DiD-Methodik](https://arxiv.org/abs/1803.09015), [Synthetic-Control-Implementierungen](https://pypi.org/project/pysyncon/)

## 5. Top 5 und jeweils ein erstes Experiment

Die Reihenfolge priorisiert den **Nutzen der Analyse**, nicht die Neuheit des Modells. Alle Schwellen unten sind vorgeschlagene, vorab festzuschreibende Entscheidungskriterien.

Eine Woche reicht für Datenprüfung, Protokoll und einen reproduzierbaren Pilotbericht. Sie reicht nicht, um langfristige Prognosegüte prospektiv nachzuweisen.

### 1. Datenqualität und Herkunft — A1

**Warum zuerst:** Fehler bei Adjustierung, Kalender und Quellenübergängen verfälschen fast jede weitere Studie.

**Erste Woche:** 20 Ticker verschiedener Assetklassen, darunter lange Historien und jüngere ETFs; verfügbare Close-Reihen prüfen, OHLC-Verfügbarkeit inventarisieren. 100 bestätigte beziehungsweise realistisch injizierte kritische Fehler und 100 plausible Marktauffälligkeiten getrennt beurteilen. Regeln gegen Regeln plus Isolation Forest vergleichen.

**Abbruch-/Rückfallkriterium:** Kein ML-Ausbau, wenn Isolation Forest bei höchstens 5 % Fehlalarmen keinen relevanten Zusatznutzen bietet. Betroffene Analysen pausieren, wenn Adjustierungen oder Quellenübergänge ungeklärt bleiben.

**Auf der Seite zulässig:** Beschreibend: „Historie geprüft bis …“, Lücken, Quellenabschnitte und bekannte Einschränkungen. Keine allgemeine Aussage „Daten garantiert fehlerfrei“.

### 2. Stabilität saisonaler Befunde — A2

**Warum:** Direkter Bezug zum Kernprodukt; beantwortet eine andere Frage als der gescheiterte Rendite-Score.

**Erste Woche:** Zehn vorab festgelegte liquide Instrumente, zwölf Monatsbefunde und ein ToM-Fenster. Roh- und geschrumpfte Effekte, Teilperioden und gemeinsame Mehrfachtest-Korrektur berechnen. Zusätzlich zeigen, wie stark ein einzelnes Jahr das Ergebnis verändert.

**Abbruchkriterium:** Keine weitere Suche nach anderen Fenstern, um einen positiven Befund zu erzwingen. Bei fehlender Stabilität endet der Pilot mit diesem Ergebnis.

**Auf der Seite zulässig:** Beschreibend: Effektgröße, Fallzahl, Teilperioden und Korrekturstatus. „Nach Berücksichtigung aller geprüften Fenster kein belastbarer Unterschied“ ist ein vollständiges Ergebnis. Keine neue Kauf-/Verkaufsfarbe.

### 3. Kalender-Vola und ihr Zusatznutzen — A4/A5

**Warum:** Verbindet vorhandene Kalenderdaten mit einer messbaren Risikofrage und erweitert den bisherigen HAR/EWMA-Vergleich sinnvoll.

**Erste Woche:** SPY, QQQ, GLD und TLT; Fünf-Tage-Varianz als Hauptziel. EWMA, HAR ohne Kalender und HAR mit vorab fixierten OPEX-/FOMC-/Feiertagsmerkmalen. Historische Auswertung und prospektives Prognosearchiv vorbereiten.

**Abbruchkriterium:** Kalender-Prognosezweig beenden, wenn er nicht mindestens 5 % besseren aggregierten QLIKE gegenüber der starken Referenz liefert oder der Vorteil nur aus einem Markt/Zeitblock stammt. Unsicherheit der Differenz mitbewerten; Schwelle ist keine Garantie statistischer Aussagekraft.

**Auf der Seite zulässig:** Sofort nach Prüfung beschreibende historische Ereignisvergleiche. Eine aktuelle Vola-Prognose erst nach zusätzlicher Kalibrierung und prospektiver Bestätigung, ausdrücklich als Schätzung.

### 4. Expected-Move-Kalibrierung — A6

**Warum:** Prüft eine bereits leicht als Wahrscheinlichkeit verstandene Anzeige. Eine korrekte Unsicherheitsaussage ist wertvoller als ein weiteres Prognosemodell.

**Erste Woche:** Export auditieren; zwei liquide Underlyings, genau eine Laufzeitdefinition. Historische IV-Bänder gegen späteren Endkurs und separat gegen zwischenzeitliche Berührung prüfen. EWMA- und historische Quantilbänder danebenstellen.

**Abbruchkriterium:** Keine Deckungsbehauptung bei unklaren Zeitstempeln, methodisch gemischten IV-Reihen oder weniger als 100 ausgereiften, nicht überlappenden Zeitfenstern. Auch darüber keine präzise Quote, wenn das Konfidenzintervall zu breit bleibt. Dann nur Datenlage veröffentlichen und weiter sammeln.

**Auf der Seite zulässig:** Historisch gemessene Deckung mit Unsicherheit, Stichprobe, Zeitraum und genauer Bedeutung. Kein ungeprüftes „68 % Wahrscheinlichkeit“.

### 5. Polymarket-Kalibrierung und Preisqualität — A14/A15

**Warum:** Ein klarer, eigenständiger Forschungsbereich mit vorhandenen Preisen und Auflösungen. Der Nutzen liegt im Verständnis der Prozentwerte, nicht in einer neuen Wettstrategie.

**Erste Woche:** Ein klar abgegrenzter Ereignistyp; Märkte nach zugrunde liegendem Ereignis bündeln. Sieben-Tage-Snapshot reproduzieren, veraltete Preise kennzeichnen und Brier-Score gegen frühere Basisrate berechnen. Prüfen, ob Ergebnisse durch einzelne Großereignisse dominiert werden.

**Abbruchkriterium:** Keine automatische Rekalibrierung bei weniger als 200 unabhängigen Ereignissen oder unzureichender Besetzung der Wahrscheinlichkeitsbereiche. Abbruch des historischen Vergleichs bei unklarer Trennung zwischen Ergebnisbekanntwerden und Preisbeobachtung.

**Auf der Seite zulässig:** „Bei vergleichbaren, abgeschlossenen Ereignissen …“ mit Fallzahl und Intervall; Preisfrische und Definitionshinweise. Keine Behauptung eines sicheren Arbitrage- oder Renditevorteils.

## 6. Was wir nicht tun sollten

| Nicht tun | Begründung und Beleg |
|---|---|
| **Einen neuen Rendite-„KI-Score“ durch Durchprobieren vieler Modelle suchen.** | Der geprüfte Score zeigt keinen belastbaren Rangzusammenhang. Wiederholte Auswahl auf derselben Historie erhöht Backtest-Overfitting. [Eigenes Ergebnis](/C:/dev/Seasonaledge/scripts/research/saison_score_validierung_ergebnis.json), [Forschung](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf) |
| **Ein Foundation-Modell wegen seines allgemeinen Leaderboard-Rangs für Börsenprognosen übernehmen.** | Die Modellquellen belegen Verfügbarkeit und Fähigkeiten, keinen SeasonAlpha-spezifischen Vorteil. Vortraining kann historische Evaluationen zusätzlich belasten. Der lokale Vergleich und ein späterer prospektiver Test bleiben erforderlich. [Chronos-Modellbeschreibung](https://huggingface.co/amazon/chronos-2) |
| **Code-Lizenz und Gewichtelizenz gleichsetzen.** | Besonders relevant für TimesFM 3.0, Moirai und neuere TabPFN-Versionen. „Nur Forschung“ ist innerhalb eines kommerziellen Projekts nicht automatisch nichtkommerziell. [TimesFM](https://github.com/google-research/timesfm), [Moirai](https://huggingface.co/Salesforce/moirai-2.0-R-small), [TabPFN](https://github.com/PriorLabs/TabPFN) |
| **GEX als gemessene Dealer-Position oder IV als objektive Wahrscheinlichkeit darstellen.** | Der eigene GEX-Code verwendet eine feste Vorzeichenannahme. IV ist ein aus Optionspreisen abgeleiteter Modellparameter. Auch VIX und ATM-IV sind nicht identisch: VIX aggregiert Optionen über Strikes. [GEX-Code](/C:/dev/Seasonaledge/scripts/compute_gamma_exposure.py:7), [Cboe-Methodik](https://cdn.cboe.com/resources/vix/VIX_Methodology.pdf) |
| **Regime rückblickend glätten und anschließend als damals bekannte Signale präsentieren.** | Glättung beziehungsweise vollständige Sequenzdecodierung kann spätere Beobachtungen verwenden. Für damalige Entscheidungen benötigt werden gefilterte, damals gespeicherte Zustände. [Zustandsraummethoden](https://www.statsmodels.org/stable/tsa.html) |
| **SHAP-Werte als Ursachen oder Conformal-Bänder als krisenfeste Garantien bewerben.** | Erklärung einer Modellvorhersage und kausale Identifikation sind verschiedene Aufgaben; langfristige Deckung ist keine bedingte Tagesgarantie. [SHAP](https://shap.readthedocs.io/en/latest/example_notebooks/overviews/Be%20careful%20when%20interpreting%20predictive%20models%20in%20search%20of%20causal%20insights.html), [Adaptive Conformal Inference](https://arxiv.org/abs/2106.00170) |
| **Polymarket-Tageszeilen als unabhängige Prognosen zählen oder Preise nach Ergebnisbekanntwerden einbeziehen.** | Viele Zeilen können auf dasselbe Ereignis und dieselbe Information zurückgehen. Der vorhandene Auswertungscode aggregiert tägliche Snapshots; für neue Forschung muss die Ereigniseinheit explizit festgelegt werden. [Code](/C:/dev/Seasonaledge/scripts/compute_brier_stats.py:140) |
| **Mit den Tagesdaten Intraday-OPEX-, 0DTE- oder FOMC-Handelsstrategien behaupten.** | Schlusskurse und Tages-OHLC liefern weder vollständige Intraday-Ausführung noch historische Bid-/Ask-Kosten. Die hier geprüfte Datenbasis trägt diesen Nachweis nicht. |
| **LLMs frei Ursachen, Zahlen oder Anlageempfehlungen formulieren lassen.** | Öffentliche Anlageempfehlungen können auch ohne Personalisierung regulatorische Anforderungen auslösen. Tatsächliche Funktionen und Werbeaussagen müssen übereinstimmen. [ESMA](https://www.esma.europa.eu/press-news/esma-news/requirements-when-posting-investments-recommendations-social-media), [§ 5 UWG](https://www.gesetze-im-internet.de/uwg_2004/__5.html) |
| **„Beschreibend“ als pauschale rechtliche Freistellung verstehen.** | Entscheidend sind Inhalt und Verwendung. Bei KI-Interaktion und bestimmten veröffentlichten KI-Texten sind Transparenzpflichten einschließlich der Regeln zur redaktionellen Verantwortung zu prüfen. Dieses Dokument ersetzt keine konkrete rechtliche Einordnung. [Art. 50 AI Act](https://ai-act-service-desk.ec.europa.eu/en/ai-act/article-50) |

## 7. Umsetzung mit kleinem Budget

**Empfohlener erster Werkzeugbestand:** vorhandene NumPy-/pandas-Berechnungen, statsmodels, scikit-learn und bei Bedarf `arch`. Erst bei einer konkreten offenen Frage kommen LightGBM, MAPIE, DTW oder ein kleines Foundation-Modell hinzu.

Die bestehende [requirements.txt](/C:/dev/Seasonaledge/requirements.txt) enthält überwiegend Mindestversionen. Die oben recherchierten Versionen sind **keine bereits geprüfte gemeinsame Installationskombination**. Für Forschung zunächst eine separate Umgebung mit festgeschriebenen Abhängigkeiten vorsehen; insbesondere Python-Kompatibilität, NumPy, Numba und PyTorch gemeinsam prüfen.

Für den VPS vorgeschlagene Betriebsgrenzen:

- Nur ein rechenintensiver Forschungsjob gleichzeitig.
- Zunächst höchstens 20 Reihen je Pilot; große Rohdaten nicht mehrfach in DataFrames duplizieren.
- Maximalen Prozessspeicher und Laufzeit messen; **2 GB zusätzlicher Prozessspeicher** als anfängliche Obergrenze, sofern die übrigen Dienste ausreichend Reserve behalten.
- Ergebnisse als kleine versionierte Dateien bereitstellen; Modelle nicht für jeden Seitenaufruf neu berechnen.
- LLM-Nutzung zunächst auf einen redaktionellen Pilot mit **10 USD Monatslimit** begrenzen. Das ist eine Budgetvorgabe, keine Kostenprognose.
- Keine GPU-Anschaffung und kein eigenes Fine-Tuning vor belegtem Zusatznutzen eines einfachen Piloten.

**Vor einem Produktentscheid noch offen:** Options- und Polymarket-Historienexport, Datenrechte, tatsächlich freie VPS-Ressourcen, Paketkompatibilität unter Windows/Linux, Modell-Hashes, API-Zugang sowie reale Qualität deutscher Ausgaben. Bis dahin sind Hardwareangaben und Entwicklungsaufwände Planungswerte; die Tabellenpreise und Lizenzen gelten ausschließlich für die jeweils genannten Versionen und Quellen.
