# Marktanalyse KI-Funktionen — Ergebnis Rechercheur „Agent" (2026-10-09)

Auftrag: [2026-10-09_ki_markt_analyse.md](2026-10-09_ki_markt_analyse.md). Unabhängig vom zweiten Rechercheur erstellt.

**Lesehilfe zur Belegqualität.** Ich unterscheide drei Stufen:
- **[P]** Primärquelle (Anbieterseite, Behörde, Gesetzestext, Paper) selbst abgerufen.
- **[S]** Sekundärquelle (Testportal, Fachpresse, Kanzlei-Newsletter). Testportale wie liberatedstocktrader, daytradingtoolkit, walnutinvest oder stork.ai arbeiten oft mit Affiliate-Links — ihre Zahlen sind ungeprüft übernommen und können veraltet sein.
- **[V]** Vermutung oder eigene Schlussfolgerung, nicht belegt.

Preise stehen nur dort, wo eine Quelle sie nennt. Wo eine Anbieterseite keinen Preis lieferte (z. B. Seasonax zeigt beim Abruf „$0.00"), steht „unklar".

---

## 1. Anbieter × KI-Funktion × Preisstufe × Validierung

„Validierung veröffentlicht" heißt: Der Anbieter zeigt Out-of-sample- oder Live-Ergebnisse oder eine unabhängige Prüfung. Ein Backtest, den der Anbieter selbst rechnet, zählt als **„nein (nur eigener Backtest)"**.

### 1a. Saisonalität (direkte Wettbewerber)

| Anbieter | KI-/ML-Funktion | Preisstufe | Validierung | Quelle |
|---|---|---|---|---|
| **Seasonax** | **Keine KI-Funktion beworben.** Die Preisseite nennt Saisonkurven, Detrending, Screener, 100 Event-Studien und Alerts, aber kein KI- oder ML-Feature. Das Produkt stützt sich auf „Dimitri Specks Saisonalitätsforschung", also einen statistischen Algorithmus. Ein FFG-Förderprojekt von 2015/16 beschreibt eine Software, die saisonale Muster findet und bewertet, ebenfalls ohne ML. | Basic/Professional, Jahresabo, 30 Tage gratis. **Preis beim Abruf nicht lesbar (Seite zeigt $0.00)** → unklar. Eine Suchmaschinen-Zusammenfassung nannte 415 bzw. 800 $/Jahr — **nicht verifiziert**. | n/a (keine Prognose-KI) | [P] https://www.seasonax.com/pricing/ · [P] https://seasonax.com/?p=11603 (Interview 2018) · [P] https://projekte.ffg.at/projekt/1410404/pdf |
| **Equity Clock** | **Keine KI-Funktion.** Rund 7000 Saisonprofile mit „optimalen" Kauf-/Verkaufsdaten, Monatsausblick, Newsletter | 24,95 $/Monat oder 249,95 $/Jahr | n/a. Es werden Kauf-/Verkaufsfenster als „tested" bezeichnet, ein Out-of-sample-Nachweis findet sich nicht. | [P] https://charts.equityclock.com/subscribe |
| **StockCharts Seasonality** | **Keine KI-Funktion** am Seasonality-Tool: Anteil positiver Monate und Durchschnittsrendite ab 1990 | Mitgliedschaft nötig, 1 Monat Test; Preis nicht geprüft | n/a | [P] https://stockcharts.com/freecharts/seasonality · [P] https://help.stockcharts.com/charts-and-tools/sharpcharts/chartlists/seasonality-view |
| **TradingView** | **Seasonals** (Jahreskurven, Durchschnittslinie, Tabelle) **ohne KI**. **Getrennt davon KI seit 2026:** Zusammenfassungen von SEC-Dokumenten (März 2026), KI-Unternehmensnachrichten (April 2026), „AI Chart Copilot" (Beta April 2026, seit September 2026 nativ in Supercharts; technische Analyse, Alerts, Watchlist-Scans) | Seasonals: welche Stufe, ist unklar. KI-Funktionen laut Blog kostenlos, Copilot mit Tageslimit („to keep it sustainable and free"). Planpreise laut Sekundärquelle 14,95–239,95 $/Monat | **nein** (beschreibende bzw. Assistenzfunktionen, keine Prognoseangabe) | [P] https://www.tradingview.com/blog/en/tradingview-seasonality-charts-49444 · [P] https://in.tradingview.com/support/solutions/43000745201-seasonals/ · [P] https://www.tradingview.com/blog/en/tradingview-ai-chart-copilot-beta-57730/ · [S] https://blog.traderspost.io/article/tradingview-ai-features-chart-copilot-documents-news · [S] Preise: https://blog.traderspost.io/article/tradingview-free-vs-paid-for-trading |
| **Moore Research (MRCI)** | **Keine KI.** Monatlich je 15 Saison- und Spread-Strategien mit „mindestens 80 % historischer Trefferquote" | Abo; Preis nicht geprüft | **nein.** Die 80 % sind eine In-sample-Trefferquote, was genau die Data-Mining-Falle ist, vor der SeasonAlpha warnt. | [P] https://mrci.com/catalog |
| **SentimenTrader** (Nachbar) | Keine KI, aber **Analogjahre per Korrelation** (z. B. „2021 ähnelt 1995 am stärksten seit 1928") | Abo; Preis nicht geprüft | Der Anbieter benennt selbst das „data-mining risk" der Analogien. | [P] https://sentimentrader.com/blog/only-one-other-year-can-truly-compare-to-2021 |
| **Market Chameleon** | Seasonality-Screener (Monatsstatistik), Kursmuster um Earnings. **Keine KI-Funktion gefunden.** Eine Vergleichsseite eines Wettbewerbers nennt das Fehlen von SDK/MCP. | Laut Sekundärquelle Starter 0 $, Stock Trader 39 $, Options Trader 69 $, Earnings Trader 79 $, Total Access 99 $/Monat | n/a | [P] https://marketchameleon.com/Learn/Stock-Seasonality · [S] https://tradersunion.com/interesting-articles/market-chameleon-review/ · [S] https://www.optionsanalysissuite.com/vs/market-chameleon |
| **Barchart** | Saisonalitätscharts in Premier. **Keine KI-Saisonfunktion gefunden** — eine Lücke in meiner Suche ist möglich. | Premier laut Sekundärquelle 29,95 $/Monat, 239,95 $/Jahr | n/a | [P] https://www.barchart.com/etfs-funds/quotes/GAPR/seasonality-chart · [S] https://pricingsaas.com/companies/barchart |
| **stock3** (ex Godmode-Trader/Guidants) | KI-Assistent „3AI"/stock3 AI im Terminal: Onboarding, Desktops bauen, Charting (Trendkanäle, Fibonacci, Unterstützungen), Bilanzanalyse mit Erklärung, Alarme. **Keine Saisonalitätsfunktion in der KI-Meldung erwähnt.** | Free: 75 KI-Anfragen/Monat, stock3 Ultimate: 500/Monat (Meldung vom 07.10.2026) | **nein** (Assistenz, keine Prognose) | [P] https://stock3.com/news/stock3-ag-innovationen-dank-ki-juengste-produktentwicklungen-17322596 · [P] https://stock3.com/news/stock3-ag-3ai-ki-sprachassistent-von-stock3-revolutioniert-die-plattform-17012581 |
| **boerse.de, finanzen.net, onvista** | **Nicht prüfbar.** Meine Suchen fanden keine KI-Funktion von boerse.de oder onvista. Zu finanzen.net fand ich nur die Übernahme des Fintechs Vickii, um finanzen.net zero mit KI auszustatten — **ohne Primärbeleg, Datum unklar**. | unklar | unklar | [S] Suchtreffer ohne Primärquelle — **als offen behandeln** |

### 1b. KI-Signale und Scores

| Anbieter | KI-/ML-Funktion | Preisstufe | Validierung | Quelle |
|---|---|---|---|---|
| **Danelfin** | „AI Score" 1–10 je Aktie/ETF, Wahrscheinlichkeit der Outperformance über 3 Monate | Freemium, Pro-Stufen; Preisseite liefert 403 → **unklar** | **nein (nur eigener Backtest).** Beworben werden z. B. +376 % gegen +166 % S&P 500 von 01/2017 bis 06/2025. Eine Sekundärquelle hält fest, dass das „Audit" von Danelfin selbst auf eigenen historischen Scores erstellt wurde und keine unabhängige Live-Replikation ist. | [S] https://pineify.app/danelfin/danelfin-review · [S] https://walnutinvest.com/resources/danelfin-review · Anbieterseite danelfin.com: 403 |
| **Tickeron** | „AI Robots" (über 350), Trend Prediction Engine mit Konfidenz in %, Mustererkennung | laut Sekundärquelle 0–250 $/Monat, „AI Robots Unlimited" ca. 125 $/Monat | **teilweise.** Tickeron wirbt mit „audited track records" und veröffentlicht je Robot die abgeschlossenen Trades. Wer prüft, war nicht feststellbar → **unklar, ob unabhängig**. | [S] https://www.liberatedstocktrader.com/tickeron-review/ · [S] https://www.liberatedstocktrader.com/tickeron-benchmark-lab-test/ |
| **Kavout** | „Kai Score", „InvestGPT", 7–8 KI-Research-Agenten | laut Sekundärquelle Free, Pro 16 $, Premium 39 $/Monat | nicht gefunden → **unklar** | [S] https://walnutinvest.com/resources/kavout-review · [S] https://tooliverse.ai/tools/kavout |
| **Trade Ideas (Holly)** | „Holly": nächtlicher Backtest vieler Strategien, Trade-Ideen mit Konfidenz | Premium laut Sekundärquelle 254 $/Monat bzw. 178 $/Monat jährlich | Sekundärquelle spricht von einem „audited track record" — **Prüfer unbekannt → unklar** | [S] https://www.liberatedstocktrader.com/trade-ideas-review/ · [S] https://toolradar.com/tools/trade-ideas/pricing |
| **Zacks Rank** | Quantitatives Ranking über Gewinnrevisionen. Wird nicht als „KI" vermarktet, sondern als Modell. | Premium/Ultimate; Preis nicht geprüft | **teilweise.** Zacks nennt +23,94 % p. a. seit 1988 (Stand 06.07.2026), monatlich gleichgewichtet und ohne Transaktionskosten. Die Performance-Seite war per Bot-Sperre nicht abrufbar. | [S/P] Suchauszug von zacks.com: https://www.zacks.com/topics/zacks-rank?page=2 |
| **TipRanks Smart Score** | Score 1–10 aus 8 Faktoren (Analysten nach Trefferquote gewichtet, Blogger, Hedgefonds, Insider, News-Sentiment, Fundamentaldaten, Technik) | Premium (Paywall); Preis nicht geprüft | **nein (nur eigener Backtest)**, ausdrücklich als „backtested" gekennzeichnet, Rückrechnung ab 2011 | [P] https://www.tipranks.com/news/labs/measure-stock-potential-with-tipranks-smart-score · [S] https://freenance.io/products/tipranks-review-2026-analyst-ratings-stock-research-tool/ |
| **Seeking Alpha Quant Ratings** | Quant-Rating aus 5 Faktorgruppen. Dazu **„Virtual Analyst Report"**: LLM-Zusammenfassung aus Seiteninhalt, Quant-Rating und Firmenberichten. Nach eigener Angabe **„nicht von Redakteuren geprüft, kann Fehler enthalten"**. | Premium; Sekundärquelle nennt 299 $/Jahr | **teilweise:** Eigener Backtest ab 2010 plus eine **akademische Studie** (Jame/Guo, University of Kentucky, 2024), die Seeking Alpha selbst veröffentlicht. Die Hilfeseite sagt nüchtern: „a useful input, not a guarantee". | [P] https://help.seekingalpha.com/how-accurate-are-seeking-alpha-quant-ratings · [P] https://help.seekingalpha.com/what-is-the-virtual-analyst-report · [P] https://help.seekingalpha.com/does-seeking-alpha-use-ai-to-generate-these-reports · [P] https://seekingalpha.com/article/4683185-university-of-kentucky-study-finds-seeking-alpha-quant-ratings-beat-the-market-sa-quant · [S] https://financer.com/invest/seeking-alpha-premium-review/ |
| **Composer** | „Trade With AI" (10/2025): Strategie aus natürlicher Sprache → automatisch gebacktestet und handelbar | laut Sekundärquellen ca. 30 $/Monat (widersprüchliche Angaben) | **nein** (der Backtest ist das Produkt, kein Nachweis) | [S] https://neuronfeed.com/startups/composer · [S] https://www.futuretools.io/tools/composer |
| **Fiscal.ai (ex FinChat)** | „Copilot" (LLM über Fundamentaldaten, KPIs, Transkripte) | Free (10 Prompts/Monat), Pro 39 $/Monat (250 Prompts), Max 79 $/Monat — Sekundärquelle | n/a (Research-Assistent, keine Prognose) | [S] https://www.matchmybroker.com/tools/fiscal-ai-review · [S] https://daytradingtoolkit.com/reviews/finchat-review |
| **Koyfin** | **Keine KI-Funktion gefunden**; eine Sekundärquelle beschreibt Koyfin als „less centered on AI chat" | nicht geprüft | n/a | [S] https://daytradingtoolkit.com/reviews/finchat-review |
| **Perplexity Finance** | Chat plus Dashboard, Earnings-Transkripte, Quellenlinks, Daten aus SEC EDGAR, FactSet, LSEG u. a. | Grundfunktionen kostenlos, Pro 20 $/Monat — Sekundärquelle | n/a | [S] https://techpoint.africa/guide/perplexity-finance-review/ · [S] https://aiwiki.ai/wiki/perplexity_finance |

### 1c. Optionen und Flows

| Anbieter | KI-/ML-Funktion | Preisstufe | Validierung | Quelle |
|---|---|---|---|---|
| **SpotGamma** | HIRO, TRACE (Heatmap der Dealer-Positionierung), Equity Hub. **Ein KI-Assistent war nicht nachweisbar** (gezielte Suche ohne Treffer). SpotGamma veröffentlicht eine eigene Auswertung „TRACE the market — excess returns". | nicht geprüft | **teilweise** (eigene Auswertung, nicht unabhängig) | [P] https://spotgamma.com/trace-the-market-excess-returns/ |
| **Unusual Whales** | Optionsflow, Dark Pool, Insider. **Kein KI-Feature nachweisbar.** | 48 $/Monat oder 399 $/Jahr (Anbieter-Landingpage laut Suchauszug) | n/a | [S/P] https://unusualwhales.com/lp/affordable-options-flow-platform |
| Market Chameleon, Barchart | siehe 1a | | | |

### 1d. Broker und Plattformen mit KI-Assistent

| Anbieter | KI-/ML-Funktion | Preisstufe | Validierung | Quelle |
|---|---|---|---|---|
| **Robinhood Cortex** | „Digests": Klartext-Erklärung, was den Kurs **gerade** treibt (News, Analysten, Daten). Dazu ein Assistent, Scanner-Bau per Prompt. Der Assistent hat laut Disclosure keinen Webzugang. | Robinhood Gold (5 $/Monat, 50 $/Jahr) | n/a. Robinhood meldet selbst „95 % positives Feedback" von Befragten — eine Zufriedenheitszahl, keine Validierung. | [P] https://www.robinhood.com/us/en/support/articles/cortex-digests · [P] https://cdn.robinhood.com/assets/robinhood/legal/cortex_assistant_disclosure.pdf · [S] https://benzinga.com/markets/tech/25/08/47252402/robinhood-unveils-cortex-ai-tool-digests-in-uk-bringing-real-time-stock-explanations-to-everyday-investors-after-95-us-approval |
| **Yahoo Finance** | „Ask Yahoo Scout" (Juni 2026), laut Bericht auf Claude aufgebaut; „AlphaSpace" als Gold-Workspace | Scout frei; AlphaSpace Gold | n/a | [S] https://axios.com/2026/06/03/yahoo-scout-ai-sports-finance |
| **Moomoo** | „Moomoo AI" (LLM-Assistent: Filings zusammenfassen, Handelsspanne aus Fundamental- und Technikdaten); zuerst in Singapur/Malaysia (06/2025) | nicht geprüft | n/a | [P] https://www.moomoo.com/sg/events/ai-features |
| **Webull** | „Vega Analyst" (individuelle KI-Researchberichte), Agentic Trading per MCP | nicht geprüft | n/a | [S] https://www.financemagnates.com/forex/retail-traders-get-custom-ai-stock-research-as-webull-launches-vega-analyst/ |
| **Scalable Capital** | „Agentic Investing" (25.08.2026): Depot per MCP an ChatGPT/Claude/Grok anbinden, jede Order wird manuell bestätigt | ohne Aufpreis | n/a | [S] https://www.it-finanzmagazin.de/scalable-capital-oeffnet-seine-brokerage-plattform-fuer-ki-assistenten-249755/ · [S] https://www.boersen-zeitung.de/banken-finanzen/scalable-capital-startet-agentic-investing-fuer-ki-trading |
| **Trade Republic** | Laut Sekundärquelle (Stand 25.08.2026) **keine offizielle KI-Schnittstelle**, nur ein inoffizieller Community-MCP | — | — | [S] https://www.it-finanzmagazin.de/?p=249755 |
| **Bloomberg** (Referenz) | KI-Zusammenfassungen von Earnings Calls (01/2024), News Summaries, Document Insights (Fragen an Dokumente). Analysten trainieren die Modelle mit, dazu „guardrail systems". | Terminal | n/a | [P] https://www.bloomberg.com/company/press/bloomberg-launches-ai-powered-earnings-call-summaries |

### Muster aus der Tabelle

1. **Die Saisonalitäts-Anbieter haben keine KI.** Bei Seasonax, Equity Clock, StockCharts, MRCI und den TradingView-Seasonals fand ich keine KI-Funktion [P, siehe oben]. KI im Markt sitzt in **Signal-/Score-Produkten** und in **Assistenten/Zusammenfassungen**.
2. **Score-Produkte belegen ihre Werbezahlen fast nur mit eigenen Backtests** (Danelfin, TipRanks, Zacks, Seeking Alpha). Ausnahmen mit etwas mehr Gewicht: die Kentucky-Studie zu Seeking Alpha und Tickerons Trade-Historien je Robot (Prüfer unklar).
3. **Die Assistenten werben ohne Prognoseversprechen**, sondern mit „erklärt", „fasst zusammen", „findet". Bei Robinhood Digests („what may be driving the price"), Seeking Alpha Virtual Analyst, Bloomberg und TradingView ist das die gemeinsame Linie.

---

## 2. Regulierung und Werbung

### USA (Referenz, nicht direkt anwendbar)
- **SEC „AI washing", 18.03.2024:** Delphia (250.000 $) und Global Predictions (175.000 $) haben KI-Fähigkeiten beworben, die sie nicht hatten. Global Predictions nannte sich „first regulated AI financial advisor" und warb mit „Expert AI driven forecasts". [S] https://www.dandodiary.com/2024/03/articles/artificial-intelligence/sec-hits-two-investment-advisers-with-ai-washing-enforcement-actions/ · [S] https://omm.com/insights/alerts-publications/sec-targets-ai-washing-in-charges-against-two-investment-advisers
- **Fortsetzung 2025:** Presto Automation (14.01.2025, erste Sache gegen ein börsennotiertes Unternehmen), Albert Saniger/Nate (09.04.2025, parallel strafrechtlich). Die SEC nennt das Ausräumen von AI-washing eine „immediate priority". [S] https://www.dlapiper.com/en/insights/publications/ai-outlook/2025/sec-emphasizes-focus-on-ai-washing
- **FINRA Regulatory Notice 24-09 (27.06.2024):** keine neuen Regeln — Rule 2210 (Kommunikation) und 3110 (Aufsicht) gelten für KI-Ausgaben genauso, auch bei eingebetteten Funktionen von Drittanbietern. [P] https://finra.org/sites/default/files/2024-06/regulatory-notice-24-09.pdf

### EU / Deutschland
- **ESMA, Public Statement vom 30.05.2024 (ESMA35-335435667-5924):** Wertpapierfirmen, die KI für Privatkunden einsetzen, bleiben an MiFID II gebunden. Marketing über KI muss „fair, clear and not misleading" sein, die Geschäftsleitung bleibt verantwortlich, und Kunden sollen über den KI-Einsatz informiert werden. **Gilt für beaufsichtigte Firmen.** SeasonAlpha ist keine — als Maßstab, was Aufseher für irreführend halten, ist die Erklärung trotzdem brauchbar. [P] https://www.esma.europa.eu/sites/default/files/2024-05/ESMA35-335435667-5924__Public_Statement_on_AI_and_investment_services.pdf
- **BaFin-Merkblatt Anlageberatung (aktualisiert 02/2025):** Anlageberatung setzt eine **persönliche Empfehlung** voraus, die auf die Verhältnisse des Anlegers gestützt oder als für ihn geeignet dargestellt wird **und nicht ausschließlich über Informationsverbreitungskanäle oder die Öffentlichkeit** verbreitet wird. Finfluencer fallen deshalb in der Regel nicht darunter. [S] https://www.gvw.com/aktuelles/blog/detail/aktualisiertes-merkblatt-der-bafin-zur-anlageberatung-und-einordnung-von-finfluencern · [S] Vergleichsfassung: https://paytechlaw.com/wp-content/uploads/Vergleichsversion-Merkblatt-Hinweise-zum-Tatbestand-der-Anlageberatung-Stand-02-2025.pdf
  - **[V] Folge für SeasonAlpha:** Ein Text je Ticker für alle ist öffentliche Information. Ein **Chat**, der auf die Watchlist oder das Depot des Nutzers eingeht und „passt zu dir"-Aussagen macht, rückt an die persönliche Empfehlung heran. Diese Grenze liegt genau bei der Personalisierung — das heutige watchlist-personalisierte Morning Briefing ist bereits ein Grenzfall, den ein Anwalt ansehen sollte.
- **MAR Art. 20 / Art. 3 Abs. 1 Nr. 35 (Anlageempfehlung):** Wer öffentlich Informationen verbreitet, die eine Anlagestrategie ausdrücklich oder implizit empfehlen (einschließlich einer Einschätzung des künftigen Werts), muss sie **objektiv darstellen** und Interessenkonflikte offenlegen. Unabhängige Ersteller müssen sich bei der BaFin melden. [P] https://lxgesetze.de/mar/20 · [P] https://bafin.de/EN/Aufsicht/BoersenMaerkte/Marktmissbrauch/Anlagestrategie/anlagestrategie_node_en.html
  - **[V]** Ein LLM-Text wie „historisch steigt X im November, guter Einstiegszeitpunkt" wäre eine implizite Empfehlung. Ein Text, der nur Häufigkeiten und Spannweiten beschreibt, ist es eher nicht. Das spricht für Erklärtexte, die **aus einem Faktenblatt erzeugt und auf Empfehlungswörter geprüft** werden.
- **BaFin/ESMA Finfluencer-Factsheet (09.01.2026)** und eine BaFin-Veröffentlichung „fünf Punkte" (08/2026, Volltext nicht abrufbar, 403): Offenlegung von Vergütung und eigenen Positionen, Trennung von Fakten und Meinung, Verantwortung für Aussagen auch ohne Zulassung. [P] https://www.esma.europa.eu/sites/default/files/2026-01/DE_Germany_de_-_Finfluencers_factsheet.pdf · [S] https://www.roedl.com/insights/bafin-und-ema-nehmen-finfluencer-staerker-in-den-fokus-wie-muss-zukuenftig-finanzcontent-gestaltet-werden/
- **UWG §§ 5, 5a (irreführende Werbung):** Ein konkreter Fall „KI-Werbung im Finanzbereich" war **nicht auffindbar**. Die Wettbewerbszentrale berichtet allgemein, dass Irreführung und Transparenz mehr als 56 % ihrer Fälle ausmachen. [P] https://www.wettbewerbszentrale.de/wp-content/uploads/2026/06/Jahresbericht-2025-V1.1.pdf — **[V]** Ein „KI-Score" mit Bullish/Bearish ohne Validierung wäre ein naheliegendes Abmahnziel. Den entfernt zu haben senkt das Risiko.

### EU AI Act (Stand nach dem Digital-Omnibus)
- **Art. 50 Transparenz gilt ab 02.08.2026.** (1) Ein Chatbot muss sich spätestens bei der ersten Interaktion als KI zu erkennen geben, „unless this is already obvious". (4) Wer KI-erzeugten Text „zur Information der Öffentlichkeit über Angelegenheiten von öffentlichem Interesse" veröffentlicht, muss das offenlegen — **außer** bei substanzieller menschlicher redaktioneller Prüfung mit benannter redaktioneller Verantwortung. Ein flüchtiges Abnicken reicht dafür nicht. Bußgeld bis 15 Mio. € oder 3 % des Umsatzes. [S] https://www.cooley.com/news/insight/2026/2026-08-03-eu-ai-act-transparency-obligations-take-effect-2-august-2026 · [S] https://artificialintelligenceact.eu/transparency-rules-article-50/
- **Omnibus:** In Kraft seit 27.07.2026. Wasserzeichenpflicht Art. 50(2) für Bestandssysteme ab 02.12.2026 (Pflicht der **Anbieter** generativer Modelle, nicht von SeasonAlpha). Art. 50(1) unverändert. [S] https://www.williamfry.com/knowledge/eu-ai-act-omnibus-deal-reached-postponed-deadlines-watermarking-compromise-and-the-nudificiation-prohibition · [S] https://www.simmons-simmons.com/en/publications/cmoveo6ke00icuxskpgueb0od/ai-omnibus-update
- **Art. 4 KI-Kompetenz:** gilt seit 02.02.2025 für Betreiber, vom Omnibus abgeschwächt zu „Maßnahmen ergreifen", ohne ein bestimmtes Niveau zu garantieren. [S] https://ki-campus.org/en/blog/eu-ai-act-ai-omnibus-recalibrates-article-4-ai-literacy-remains-mandatory
- **[V] Einordnung für SeasonAlpha:** Erklärtexte, Volatilitätsprognose und Ähnlichkeitssuche sind **kein Hochrisiko-System** nach Anhang III (dort steht im Finanzbereich Kreditwürdigkeit, nicht Marktinformation). Es bleiben Art. 50 und Art. 4. Ob tägliche Ticker-Texte eine „Angelegenheit von öffentlichem Interesse" sind, ist **ungeklärt**. Die sichere Variante ist ein sichtbarer Hinweis „automatisch erstellt aus unseren Daten" — kostet nichts und ist ohnehin die ehrliche Kennzeichnung. Keine Rechtsberatung.

---

## 3. Was Nutzer wollen

**Nutzung wächst, ist aber Recherche statt Delegation:**
- **eToro Retail Investor Beat (Opinium, 5.–19.08.2025, 11.000 Befragte in 13 Ländern, davon 1.000 in DE):** 19 % nutzen KI-Tools, um Investments auszuwählen oder zu ändern (Vorjahr 13 %), 39 % sind offen dafür. USA: 30 %. Als Motiv nannten in der US-Fassung 48 % Zeitersparnis bei der Recherche. [P] https://www.etoro.com/news-and-analysis/etoro-updates/retail-investors-flock-to-ai-tools-with-usage-up-46-in-one-year/ · [P] https://www.etoro.com/en-us/news-and-analysis/press-release/us-retail-investors-flock-to-ai-tools-with-usage-surging-75-in-one-year/
- **Bitkom (2026, 1.004 Personen ab 16, repräsentativ für DE):** 25 % haben Chatbots um Finanzrat gefragt, 56 % sehen KI bei der Geldanlage als Chance, 40 % als Risiko, 62 % fürchten mehr Betrug. Der Bitkom-Präsident fordert, KI im Finanzbereich müsse „transparent, sicher und in ihren Aussagen nachvollziehbar" sein. [S] https://www.channelpartner.de/article/4177038/ki-statt-bankberater-jeder-vierte-holt-sich-finanzrat-bei-chatbots.html
- **FINRA Foundation (Feb. 2024, über 1.000 US-Erwachsene):** Nur 5 % nutzten KI für Finanzrat. Bei Aussagen zur Aktienentwicklung vertrauten die Befragten KI aber fast so stark wie einem Berater. [S] https://financial-planning.com/news/finra-study-shows-consumers-trust-ai-about-the-same-as-an-advisor-in-some-situations

**Was gelobt und was abgetan wird** (Belege dünn, Foren kaum zugänglich):
- Scores gelten als **„Screening-Hilfe, nicht als Kaufentscheidung"**. So fasst eine Danelfin-Besprechung den Konsens zusammen, und Seeking Alpha formuliert es auf der eigenen Hilfeseite genauso. [S] https://pineify.app/danelfin/danelfin-review · [P] https://help.seekingalpha.com/how-accurate-are-seeking-alpha-quant-ratings
- Erklär- und Zusammenfassungsfunktionen werden angenommen: Robinhood meldet „hunderttausende" Cortex-Nutzer (eigene Angabe). [S] Benzinga-Link oben. Unabhängige Nutzerstimmen (Reddit) **konnte ich nicht abrufen → offen.**
- **Warnsignal Genauigkeit:** Which? testete im November 2025 sechs Chatbots mit 40 Verbraucherfragen. ChatGPT erreichte 64 % Genauigkeit, Meta AI gut 50 %. ChatGPT und Copilot übersahen einen falschen ISA-Freibetrag in der Frage und rechneten damit weiter. [S] https://www.giskard.ai/knowledge/when-ai-financial-advice-goes-wrong-chatgpt-copilot-and-gemini-failed-uk-consumers · [S] https://www.tomsguide.com/ai/ai-could-be-costing-you-money-new-study-finds-chatbots-get-most-financial-questions-wrong
- **FinanceBench (Patronus, 2023):** GPT-4-Turbo mit Retrieval beantwortete 81 % der Fragen zu Geschäftsberichten falsch oder gar nicht, mit langem Kontext 21 %. [P] https://patronus.ai/announcements/patronus-ai-launches-financebench-the-industrys-first-benchmark-for-llm-performance-on-financial-questions — **[V]** Das ist ein älterer Modellstand. Der Kern bleibt: Freie Fragen über Rohdaten sind fehleranfällig, Texte aus einem **vorgerechneten, kleinen Faktenblatt** sind es deutlich weniger.
- **Für Saisonalität besonders relevant:** Chen/Green/Gulen/Zhou (09/2024) zeigen, dass LLMs aus historischen Renditen **übermäßig extrapolieren**, zu optimistisch sind und Ausreißer unterschätzen. Ein LLM, dem man eine Saisonkurve gibt, neigt also dazu, eine Prognose daraus zu machen. [P] https://arxiv.org/pdf/2409.11540

---

## 4. Bewertung der drei Kandidaten aus der früheren Runde

| Kandidat | Gibt es das am Markt? | Besser/schlechter als SeasonAlpha könnte | Urteil |
|---|---|---|---|
| **(1) Erklärtexte per LLM aus Faktenblättern** | **Ja, aber nicht für Saisonalität.** Robinhood Digests erklären, „was den Kurs gerade treibt" (News). Seeking Alpha Virtual Analyst fasst Analystenmeinungen zusammen, ungeprüft und mit Fehlerhinweis. Bloomberg und TradingView fassen Filings und Earnings zusammen. **Kein Saisonanbieter erklärt seine Kurven per Text** (siehe 1a). | Die Wettbewerber fassen **fremden Text** zusammen. SeasonAlpha hätte **eigene, geprüfte Zahlen** (Faktenblatt mit Fallzahl, Streuung, p-Wert) und könnte jede Zahl im Text gegen das Blatt prüfen — so, wie es der Zahlenwächter bei den Wahlen schon tut. Das wäre strenger als Seeking Alpha („not reviewed by editors"). | **Echte Lücke, beste Passung.** Risiko: LLM-Extrapolation (Chen et al.) → Text darf nur beschreiben, Empfehlungs- und Prognosewörter sperren, Zahlenwächter verpflichtend. |
| **(2) Volatilitätsprognose HAR/EWMA** | **Ja, frei und gut:** NYU V-Lab veröffentlicht GARCH-Prognosen (12 Modelle, GJR-GARCH als Standard) für sehr viele Titel, mit Parametern. Dazu zeigen Optionsseiten (Market Chameleon, Barchart, SpotGamma) implizite Volatilität, und die ist selbst eine Marktprognose. | Eine eigene HAR-Prognose ist kein Alleinstellungsmerkmal und konkurriert mit der IV, die SeasonAlpha auf `/skew` schon hat. Neu wäre nur die **Verbindung mit Kalenderereignissen** (erwartete Vola um OPEX/FOMC/Wahltag aus eigener Historie gegen die aktuelle IV). | **Gibt es schon, teils besser (V-Lab gratis, IV als Marktmaß).** Nur als Kalender-Vola-Vergleich interessant, nicht als „KI-Prognose" vermarkten. [P] https://vlab.stern.nyu.edu/help/volatility_analysis |
| **(3) Beschreibende Ähnlichkeitssuche** (welche Jahre verliefen bisher ähnlich) | **Ja, als redaktionelles Format:** SentimenTrader veröffentlicht Analogjahre per Korrelation und benennt das Data-Mining-Risiko selbst. TradingView Seasonals lassen Einzeljahre übereinanderlegen, aber ohne Ähnlichkeitsmaß. **Als interaktives Werkzeug mit Ehrlichkeitsrahmen nicht gefunden.** | Besser ginge es mit **Fallzahl, Streuung der Folgepfade und einer Zufallsreferenz** (wie ähnlich wären zufällige Jahre?) statt eines einzelnen Analogjahrs. Damit wird aus der beliebten, aber verführerischen Analogie-Grafik etwas Prüfbares. | **Teilweise vorhanden, als Werkzeug eine Lücke.** Risiko: Analogien lesen sich als Prognose → Folgepfade nur als Bandbreite, nie als Linie zeigen. |

---

## 5. Eigene Vorschläge (höchstens fünf)

1. **„Was diese Kurve sagt — und was nicht": LLM-Erklärung je Ticker/Seite aus dem Faktenblatt, mit Zahlenwächter.**
   *Warum Lücke:* Kein Saisonanbieter hat Erklärtexte (Abschnitt 1a). Die vorhandenen KI-Zusammenfassungen anderswo sind ungeprüft (Seeking Alpha: „not curated or reviewed by editors").
   *Ohne Prognose:* Der Text nennt Fallzahl, Trefferquote, Streuung und Signifikanzstatus und sagt ausdrücklich, was nicht belegt ist. Wegen Chen et al. (2024) per Wortliste und Wächter gegen Extrapolation sichern.
   *Kennzeichnung:* „automatisch erstellt aus unseren Daten" (Art. 50, sicher ausgelegt).

2. **„Hält der Effekt?" — Erklärung der Belastbarkeit in Klartext**, also eine Übersetzung von p-Wert, Teilperioden-Stabilität und Mehrfachtest-Korrektur in eine Sprache wie „in 2 von 3 Jahrzehnten gleichgerichtet, nach Korrektur nicht signifikant".
   *Warum Lücke:* MRCI wirbt mit „80 % historisch zuverlässig", Equity Clock mit „optimal" getesteten Daten, Score-Anbieter mit eigenen Backtests (Abschnitt 1). Niemand im Saisonsegment sagt dem Nutzer, **wie wenig** eine Trefferquote beweist.
   *Ohne Prognose:* Das ist reine Methodik. Es baut auf den vorhandenen Artikeln `p-wert-erklärt` und `boersenregeln-nachgerechnet` auf.

3. **Analogjahre mit Zufallsreferenz** (Kandidat 3, geschärft): die ähnlichsten Jahre bis heute plus die **Bandbreite** ihrer Folgepfade und daneben, wie stark zufällig gewählte Jahre auseinanderlaufen.
   *Warum Lücke:* SentimenTrader zeigt Analogien als Blogformat, TradingView ohne Ähnlichkeitsmaß; eine Referenz gegen Zufall habe ich nirgends gefunden.
   *Ohne Prognose:* Gezeigt wird eine Bandbreite, keine Linie.

4. **Kalender-Vola gegen implizite Vola** (Kandidat 2, umgedeutet): Wie stark schwankte der Titel historisch in der Woche um OPEX, FOMC oder Wahltag, und was preist die IV heute ein?
   *Warum Lücke:* V-Lab prognostiziert Vola ohne Kalender, Optionsseiten zeigen IV ohne saisonale Referenz. Die Verbindung gibt es meines Wissens nicht **[V — nicht erschöpfend geprüft]**.
   *Ohne Prognose:* Ein Vergleich zweier Messungen. Kein ML nötig, also auch nicht als „KI" bewerben (AI-washing-Risiko).

5. **Fragen an die eigenen Daten statt an das Web** — ein schmaler Assistent nur über SeasonAlphas veröffentlichte Faktenblätter und Studien, mit Quellenlink je Antwort, ohne Watchlist-Bezug.
   *Warum Lücke:* stock3, Robinhood, Moomoo, Yahoo und Perplexity antworten über Kurse, News und Filings; **keiner über geprüfte Kalenderstatistik**.
   *Grenzen:* KI-Hinweis Pflicht (Art. 50(1)). **Keine Personalisierung** (BaFin-Merkblatt: persönliche Empfehlung). Teurer und fehleranfälliger als Vorschlag 1 (Which?, FinanceBench) → frühestens nach Vorschlag 1 und nur, wenn Nutzer danach fragen.

**Ausdrücklich nicht vorgeschlagen:** ein neuer Score mit Kauf-/Verkaufsfarbe. Der Markt ist voll davon (Danelfin, TipRanks, Zacks, Seeking Alpha, Kavout), belegt wird fast nur per eigenem Backtest, und genau diese Werbung ist das Ziel der SEC-Fälle. Ein junges Portal kann dort nur verlieren.

---

## 6. Kosten und Machbarkeit (grob)

**LLM-Kosten für Erklärtexte, 370 Ticker täglich.** Preise laut Anthropic-Preisseite, abgerufen am 09.10.2026 [P] https://platform.claude.com/docs/en/about-claude/pricing. Annahme **[V]**: je Ticker 2.000 Eingabe-Token (Faktenblatt plus Anweisung) und 300 Ausgabe-Token, eine Sprache, Batch-API (50 % Rabatt):

| Modell (Batch) | Eingabe/Ausgabe je MTok | pro Tag (370 Ticker) | pro Monat (~30 Tage) |
|---|---|---|---|
| Claude Haiku 5.5 (Prompt < 100k) | 0,05 $ / 0,25 $ | 740k × 0,05 + 111k × 0,25 ≈ **0,06 $** | **≈ 2 $** |
| Claude Haiku 4.5 | 0,50 $ / 2,50 $ | ≈ 0,37 + 0,28 = **0,65 $** | **≈ 20 $** |
| Claude Sonnet 5 / 5.5 | 1 $ / 5 $ | ≈ 0,74 + 0,56 = **1,30 $** | **≈ 40 $** |

- DE + EN verdoppelt die Ausgabe-Kosten ungefähr. Der gemeinsame Anweisungsteil lässt sich cachen (Cache-Lesen 0,1× bzw. 0,05× des Eingabepreises).
- Laut Preisseite erzeugt der neue Tokenizer ab den 4.7er-Modellen etwa 30 % mehr Token für denselben Text → ca. +30 % einrechnen.
- **[V]** Die Token-Kosten sind vernachlässigbar. Teuer ist die **Prüfung**: Zahlenwächter, Wortlisten und Stichproben-Review — so wie bei den Wahlartikeln.
- **Andere Anbieter (OpenAI, Google) nicht geprüft** — bewusst keine Preise genannt.

**Haftung/Regulierung (Zusammenfassung von Abschnitt 2, keine Rechtsberatung):**
- Öffentliche, nicht personalisierte Texte → in der Regel **keine Anlageberatung** (BaFin-Merkblatt 02/2025). Mit Personalisierung (Watchlist/Depot) steigt das Risiko.
- Implizite Empfehlungen in Texten → **MAR Art. 20** (objektive Darstellung, Interessenkonflikte, ggf. BaFin-Meldung). Beschreibende Texte ohne Wertung meiden das.
- **AI Act:** kein Hochrisiko. Art. 50 seit 02.08.2026 (Chatbot-Hinweis, ggf. Kennzeichnung von Text), Art. 4 KI-Kompetenz als Verhaltenspflicht.
- **Werbung:** „KI" nur dort sagen, wo ein Sprachmodell tatsächlich arbeitet, und **nie** mit Treffer- oder Renditeversprechen verbinden (SEC-Fälle, ESMA „fair, clear and not misleading", UWG § 5).

---

## 7. Unsichere oder nicht prüfbare Punkte

- **Seasonax-Preise:** Die Seite zeigte beim Abruf 0,00 $. Die genannten 415/800 $ stammen aus einer Suchmaschinen-Zusammenfassung und sind **nicht verifiziert**.
- **Danelfin, Zacks, BaFin-„fünf Punkte", G2/„Seasonality AI":** Primärseiten lieferten 403 oder eine Bot-Sperre. Die Angaben stammen aus Sekundärquellen. Ein Produkt „Seasonality AI" (G2-Eintrag) existiert offenbar, **Anbieter und KI-Gehalt ungeklärt** — könnte ein direkter Wettbewerber mit KI-Etikett sein und sollte nachgeprüft werden.
- **boerse.de, onvista, finanzen.net:** keine KI-Funktion belegbar. „Nicht gefunden" heißt nicht „gibt es nicht".
- **Tickeron und Trade Ideas „audited":** Wer prüft, ist unbekannt.
- **Reddit- und Forenstimmen:** nicht direkt abrufbar. Die Aussagen zu „Gimmick vs. nützlich" stützen sich auf Testportale und Anbieterangaben, also schwach.
- **Preise von Kavout, Composer, Fiscal.ai, Perplexity, Market Chameleon, Barchart, TradingView** stammen aus Sekundärquellen, teils widersprüchlich (Composer 29/30 $).
- **Art. 50(4) „öffentliches Interesse"** bei täglichen Tickertexten: rechtlich ungeklärt.
- **Bitkom-Umfrage:** Das genaue Veröffentlichungsdatum 2026 ist nur über die Sekundärquelle belegt.
