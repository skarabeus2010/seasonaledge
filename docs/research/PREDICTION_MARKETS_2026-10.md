# Prediction Markets: Anbieter, Wettarten, Zugang aus Deutschland, Arbitrage nach Kosten

> Stand 07.10.2026. Zwei unabhängige Recherchen (Claude mit Websuche, Codex `gpt-6-astra` mit Websuche), danach
> abgeglichen, an Primärquellen nachgeprüft und von Codex gegengelesen (Prüfrunden in
> `docs/review_prompts/2026-10-07_prediction_markets_*.md`). Keine Konten eröffnet, keine Orders ausgeführt.
> **Keine Rechts- oder Steuerberatung.** Wege zur Umgehung von Geo-Sperren (VPN, fremde Identität, falscher Wohnsitz)
> sind nicht Gegenstand dieser Recherche; sie verstoßen gegen die AGB der Anbieter und ändern nichts an der deutschen
> Rechtslage. Bezug zu SeasonAlpha: `/polymarket` zeigt Polymarket-Wahrscheinlichkeiten als Daten
> ([docs/POLYMARKET.md](../POLYMARKET.md)).

## Ergebnis in drei Sätzen

1. **Unter den untersuchten Angeboten wurde für deutsche Privatkunden keine belastbar legal zugängliche Kombination
   zweier Echtgeld-Prediction-Markets nachgewiesen** — damit fehlt die Voraussetzung für plattformübergreifende
   Arbitrage. Polymarket sperrt Deutschland, IBKR schließt MiFID-Privatkunden von Forecast Contracts aus, keine der
   großen Wettbörsen steht auf der GGL-Whitelist, und die GGL stuft Gesellschaftswetten einschließlich der Teilnahme
   als illegal und strafbar ein. Für Kontrakte, die als Finanzinstrument einzuordnen wären, ist das eine eigene,
   hier nicht abschließend geklärte Prüfung.
2. **Preisabstände zwischen Plattformen sind dokumentiert** — eine Studie misst bei semantisch abgeglichenen Märkten
   im Mittel 2–4 % Abweichung nach modellierten Kosten —, aber nicht als tatsächlich ausgeführte Gewinne, und „dasselbe"
   Ereignis kann je Plattform nach anderen Regeln, Stichtagen und Quellen aufgelöst werden.
3. **Allein die Taker-Gebühren des Modellpaars Kalshi + Polymarket International verlangen bei Kursen um 50 Cent eine
   Preislücke von rund 2,75–3,00 Cent** je Kontraktpaar; Umtausch, Transfers, Kapitalbindung, Steuern und Auflösungs-
   risiko kommen hinzu.

## 1. Anbieter

| Anbieter | Aufsicht / Rechtsform | Abwicklung | Deutschland (Privatkunde) |
|---|---|---|---|
| Polymarket International | Adventure One QSS Inc., keine deutsche Erlaubnis | Orderbuch, on-chain (Polygon, USDC-gedecktes pUSD); Auflösung meist UMA Optimistic Oracle, Krypto-Up/Down per Chainlink | **Nein** — „Trading is prohibited", Bestandspositionen bis zur Auflösung halten, dann auszahlen ([Polymarket, 14.08.2026](https://help.polymarket.com/en/articles/13364163-geographic-restrictions)) |
| Polymarket US | QCX LLC, CFTC-DCM | zentrales Orderbuch, USD | **Nein** — US-Angebot |
| Kalshi | KalshiEX LLC, CFTC-DCM | Orderbuch, USD | **Keine deutsche Handelsfreigabe nachgewiesen.** Deutschland fehlt in der Sperrliste in Abschnitt VI des Member Agreement vom 01.10.2026 (von Codex abgerufen; der eigene Abruf scheiterte am Bot-Schutz). Derselbe Vertrag verbietet Handel, der nach lokalem Recht unzulässig ist; Kalshis Zugangspolitik bleibt vorbehalten. Für politische und gesellschaftliche Kontrakte gilt die GGL-Einordnung. Zinsen auf Guthaben nur für berechtigte US-Nutzer. |
| PredictIt | CFTC-No-Action-Sonderrahmen, Limit 3.500 $ je Kontrakt | USD | **Nein** (Gesellschaftswette) |
| IBKR ForecastTrader / ForecastEx | ForecastEx LLC (CFTC-DCM/DCO); in der EU über IB Ireland | USD, voll besichert, 0,01 $ je Kontrakt | **Nein für Forecast Contracts:** „all MiFID retail clients are prohibited from trading forecast contracts" (IB Ireland, Produktseite, selbst abgerufen 07.10.2026). Die Aussage gilt für Forecast Contracts; professionelle Kunden sind eine andere Kategorie. |
| Robinhood, Crypto.com (CDNA), CME Event Contracts | CFTC | USD | **Nein** — US-Wohnsitz bzw. institutionelle Kunden |
| Betfair Exchange, BETDAQ, Matchbook | UKGC / Alderney / Irland | Fiat-Wettbörse, Back/Lay | **Kein legaler DE-Zugang belegt** — kein Eintrag auf der GGL-Whitelist; Betfair schränkt die Exchange für DE ein, BETDAQ führt DE nicht in der Länderliste |
| Smarkets | MGA / UKGC / Irland | Fiat-Wettbörse, Back/Lay | **Kein legaler DE-Zugang belegt** — technisch/AGB: DE fehlt in der Beispiel-Sperrliste, die AGB verlangen aber Rechtmäßigkeit nach lokalem Recht; deutsche Erlaubnis: kein Whitelist-Eintrag |
| Limitless, Myriad | Panama bzw. Stiftung, keine EU-Erlaubnis belegt | Krypto, AMM/Orderbuch | **Unklar, keine Freigabe** (lokales Recht zwingend) |
| Drift BET | — | Solana | Betrieb nach Exploit vom 01.04.2026 nicht belegt |
| Manifold | — | Spielgeld (Mana), nicht auszahlbar | Ja, aber kein Echtgeld |

**Mehrere Apps ≠ mehrere Märkte:** Robinhood vermittelt u. a. Kalshi- und ForecastEx-Kontrakte. Vor jedem Vergleich
muss feststehen, an welcher Börse ausgeführt wird.

## 2. Wettarten

- **Themen:** Politik und Wahlen, Wirtschaftsdaten (CPI, Fed-Zins, BIP), Sport, Krypto-Preise (auch Kurzfrist-Up/Down),
  Wetter/Klima, Kultur und Unterhaltung, „Mentions" (fällt ein Wort in einer Rede).
- **Bauformen:** binär (1 $ oder 0), Mehrfachausgang als Bündel binärer Kontrakte (Summe nur dann 1, wenn die
  Ausgänge vollständig und gegenseitig ausschließend sind), Schwellen- und Bereichsleitern (weiterhin binär — ein
  echter skalarer Kontrakt war bei keinem Anbieter belegt), Back/Lay an Wettbörsen.
- **Auflösung ist Teil des Produkts.** Polymarket International: UMA mit Einspruch und Token-Abstimmung (Streitfälle
  u. a. Ukraine-Mineralienabkommen 03/2025, [The Block, 26.03.2025](https://www.theblock.co/news/ecosystems/2025-03-26-polymarket-says-governance-attack-by-uma-whale-to-hijack-a-bets-resolution-is-unprecedented-348171));
  Kalshi und Polymarket US: börsenseitig nach Regelwerk; Manifold: Marktersteller.

## 3. Rechtslage für Kunden in Deutschland

- **GGL, 05.09.2025:** Gesellschaftswetten — ausdrücklich auch Polymarket — sind „nicht erlaubnisfähig und damit
  illegal"; „Sowohl das Veranstalten oder Vermitteln … als auch die Teilnahme daran … sind strafbar". Glücksspiel-
  rechtlich erlaubt sind Wetten auf definierte Sportereignisse bei Anbietern auf der Whitelist
  ([GGL](https://www.gluecksspiel-behoerde.de/de/news/ggl-warnt-vor-teilnahme-an-illegalen-gesellschaftswetten)).
  § 285 StGB stellt die Teilnahme an unerlaubtem öffentlichem Glücksspiel unter Strafe (bis sechs Monate oder
  Geldstrafe); **ob seine Voraussetzungen im Einzelfall erfüllt sind, bedarf gesonderter Prüfung** — die Behörden-
  position ersetzt sie nicht. *Hinweis:* Mehrere Sekundärseiten datieren die GGL-Klarstellung auf August 2026; die
  Primärquelle ist vom 05.09.2025.
- **Wettbörsen:** GlüStV 2021 definiert Sportwetten als Wetten zu festen Quoten; keine der großen Börsen steht auf der
  Whitelist.
- **Finanzinstrumente:** Ereigniskontrakte auf Zinsen, Inflation oder Klima können Derivate sein. Dann greift MiFID/
  BaFin; die BaFin-Allgemeinverfügung von 2019 beschränkt Vermarktung, Vertrieb und Verkauf binärer Optionen an
  Kleinanleger, mit eng gefassten Ausnahmen — sie ist kein unterschiedsloses Verbot jedes binären Produkts. Eine
  US-Zulassung (CFTC) ersetzt keine deutsche Erlaubnis.
- **Steuern, grob und nicht verbindlich:** private Sportwettgewinne grundsätzlich nicht einkommensteuerbar;
  Ereigniskontrakte als Termingeschäft → § 20 EStG (Einordnung der konkreten Plattformkontrakte ungeklärt);
  Krypto-/Stablecoin-Tausch kann zusätzlich § 23 EStG auslösen. **Gewinn auf der einen und Verlust auf der anderen
  Plattform können steuerlich in verschiedene Einkunftsarten fallen** — eine Arbitrage kann vor Steuern positiv und
  nach Steuern negativ sein.

## 4. Arbitrage: was die Daten zeigen

| Quelle | Befund | Grenze |
|---|---|---|
| Gebele/Matthes, *Semantic Non-Fungibility and Violations of the Law of One Price in Prediction Markets*, [arXiv 2601.01706](https://arxiv.org/abs/2601.01706) (05.01.2026) | Datensatz: >100.000 Ereignisse auf zehn Plattformen 2018–2025, ~6 % parallel gelistet. Ausführungsanalyse auf sieben Plattformen: bei semantisch abgeglichenen Märkten im Mittel **2–4 % Abweichung nach modellierten Gebühren und Spreads**; Ursache laut Autoren strukturelle Reibung, nicht Informationsunterschiede | modellierte, nicht tatsächlich ausgeführte Trades; historische Kostenannahmen; Übertragbarkeit auf die Gebühren von Oktober 2026 eingeschränkt |
| Saguillo u. a., *Unravelling the Probabilistic Forest*, [arXiv 2508.03474](https://arxiv.org/abs/2508.03474) (2025) | geschätzt ca. **40 Mio. $** realisierte Arbitragegewinne 01.04.2024–01.04.2025 | **nur innerhalb von Polymarket** (Rebalancing, kombinatorisch) — wird oft fälschlich als Polymarket-Kalshi-Arbitrage zitiert |
| Krause, *Same Bet, Different Markets*, SSRN 6861841 (06/2026) | CLARITY-Act-Markt: Abstand Kalshi/Polymarket bis 26,1 Prozentpunkte (Abstract) | Mean-Reversion-Simulation; Ausführbarkeit nicht verifiziert |
| Shutdown-Märkte ([OddsShopper, 15.08.2026](https://www.oddsshopper.com/articles/prediction-markets/kalshi-vs-polymarket-settlement-rules)) | Kalshi-Bedingungen lesen die Quelle zu einem Stichtag 11:00 ET, ein Polymarket-Markt bis 23:59 ET — ein Ereignis am Nachmittag fällt auf beiden Plattformen in verschiedene Tage; dazu zwei Polymarket-Märkte mit unterschiedlicher Definition („Shutdown" vs. „Appropriations Lapse") | belegt unterschiedliche **Regeln**, kein identifiziertes Kontraktpaar mit tatsächlich gegensätzlicher Auszahlung |

**Prüfliste vor jeder Gleichsetzung:** Ereignis, Stichtag und Zeitzone, Datenquelle, Erstveröffentlichung vs. Revision,
„größer" vs. „größer gleich", Verlängerung/Abbruch/Verschiebung, Annullierung mit Rückzahlung, Teilauszahlung, Regel
bei Mehrdeutigkeit. Identische Ereignis- und Auflösungsregeln erleichtern den Nachweis komplementärer Auszahlungen.
Entscheidend bleibt die **Mindestgesamtauszahlung beider Positionen in jedem denkbaren Szenario** (auch bei
gemeinsamer Annullierung mit bloßer Einsatzrückzahlung): Sie muss sämtliche Kosten decken, für einen garantierten
Gewinn übersteigen.

## 5. Transaktionskosten

| Kostenart | Größenordnung (Quelle) |
|---|---|
| Kalshi | Taker `0,07 × M × C × p × (1−p)`, M serienabhängig (Standard 1); Maker-Gebühr `0,0175 × M × …` nur in einzelnen Serien, Standard-Maker-Multiplikator 0; keine Settlement-Gebühr; bis 2 % Karteneinzahlung. Rundung laut Fee Schedule (07.07.2026) nicht ganz eindeutig — die Ordervorschau ist maßgeblich ([Kalshi](https://kalshi.com/docs/kalshi-fee-schedule.pdf)) |
| Polymarket International | nur Taker `C × r × p × (1−p)`: r = 0,04 Politik/Finanzen/Tech, 0,05 Sport/Wirtschaft/Kultur/Wetter, 0,07 Krypto, 0 Geopolitik; einzelne Serien abweichend; Maker 0 plus Rebate ([Docs](https://docs.polymarket.com/trading/fees)) |
| Polymarket US | Taker `0,0695 × C × p(1−p)`, Maker-Rebate `0,0125 × C × p(1−p)` für einschlägige Standardgeschäfte; Sonderänderungen zum 07.10.2026, u. a. Tischtennis 0,10 ([Polymarket US](https://docs.polymarket.us/fees)) |
| Wettbörsen | Provision auf den Markt-Nettogewinn. Smarkets Standard 2 %; **Pro/Select stattdessen 1 % bzw. 3 % auf Gewinn oder Verlust je Wette** — für Arbitrage wesentlich ([Smarkets-AGB, Abschnitt 3](https://help.smarkets.com/hc/en-gb/articles/213469085-Smarkets-Terms-and-Conditions)); BETDAQ/Matchbook beworben ~2 %; Betfair kontoabhängig plus Expert Fee |
| Spread / Slippage | nur dann in der Rechnung enthalten, wenn mengenabhängige Ausführungspreise über die Orderbuchtiefe verwendet werden — bester Ask, Mittelkurs oder letzter Trade reichen nicht |
| EUR→USD bzw. →Stablecoin, Ein-/Auszahlung, Gas | **Szenarioannahme**, keine gemessene Größe; hängt von Zahlungsweg, Betrag und Hin- und Rücktransfer ab. Dazu das Risiko, dass Stablecoin und Dollar nicht genau gleich viel wert sind, der EUR-Kurs zwischen Ein- und Auszahlung und das Plattform-/Auszahlungsrisiko |
| Kapitalbindung | bei einer Haltestrategie bis zur jeweiligen Auszahlung (vorzeitiger Verkauf hängt von Zugang und Liquidität ab, Auszahlungstermine können sich unterscheiden): 4 % p. a. entsprechen 0,333 Cent je Dollar und Monat, 0,986 Cent bei 90 Tagen; Guthabenzinsen/Coupons nur wo berechtigt |
| Steuern | siehe Abschnitt 3 — Verrechenbarkeit nicht gesichert |

**Eigene Rechnung — nötige Preislücke, nur Handelsgebühren.** Modellpaar: YES bei Kalshi zum Preis p (Taker,
Standard-Multiplikator, 100er-Order, Gesamtgebühr auf Cent aufgerundet), NO bei Polymarket International (Taker,
ohne Rundung). Werte in Cent je Kontraktpaar, **auf 0,01 Cent gerundet** — für die Gewinnprüfung die ungerundete
Schwelle (z. B. 1,022295… Cent bei p = 0,10, r = 0,04) und die tatsächlich handelbaren Tickgrößen verwenden:

| p | Polymarket r = 0,04 | r = 0,05 |
|---|---|---|
| 0,10 | 1,02 | 1,12 |
| 0,30 | 2,35 | 2,57 |
| 0,50 | 2,75 | 3,00 |
| 0,70 | 2,27 | 2,47 |
| 0,90 | 0,96 | 1,04 |

**Beispiel (Codex, nachgerechnet):** 1.000 YES zu 0,44 $ bei Kalshi, 1.000 NO zu 0,50 $ bei Polymarket (Wirtschaft),
beide voll ausgeführt, Dollar und Stablecoin gleich viel wert angenommen — 6 Cent Bruttolücke = 60 $.
Handelsgebühren 29,75 $, angenommene Slippage/FX/Transfers/Gas 11,58 $ → **18,67 $ Cash-Gewinn vor Steuern**.
Mit 90 Tagen Kapitalbindung bei 4 % (Opportunitätskosten, nicht zahlungswirksam) **8,99 $**. Steuer, falls die
18,67 $ vollständig als verrechenbarer Gewinn nach § 20 EStG gelten, der Sparer-Pauschbetrag ausgeschöpft ist und
keine Kirchensteuer anfällt: 26,375 % = 4,92 $ → **4,07 $** wirtschaftlich übrig. Schon das Paar 0,48 + 0,50 läge nach
Gebühren bei −9,98 $. Wettbörsen analog im Smarkets-Standardtarif: zweimal Quote 2,10 bei 2 % Provision bringen
7,80 € auf 200 €, zweimal 2,02 bereits −0,04 €.

**Was eine Rechnung auf dem Papier nicht abbildet:** beide Konten müssen vorab finanziert sein; die beiden Orders
laufen nicht gleichzeitig und unteilbar — eine Seite kann ganz oder teilweise ausgeführt werden und die andere nicht;
die Tiefe des Orderbuchs begrenzt die Stückzahl; eine ungesicherte Position zurückzudrehen kostet erneut Spread und
Gebühr.

## 6. Bewertung

- **Für deutsche Privatkunden ist der Engpass nicht die Rechnung, sondern der Zugang:** Beide Seiten müssten legal
  erreichbar sein, und das ist für keinen untersuchten Echtgeldanbieter nachgewiesen.
- **Wo Zugang besteht, bleibt nach Kosten ein garantierter Überschuss, wenn** beide Positionen zu den kalkulierten
  Preisen vollständig aufgebaut werden und die Mindestauszahlung in jedem Auflösungsszenario Erwerbskosten, sämtliche
  Gebühren und die laufzeitabhängigen Kapitalbindungskosten übersteigt. Eine lange Laufzeit schließt das nicht aus,
  verlangt aber einen entsprechend größeren Abschlag. Das Beispiel zeigt, wie
  aus 6 Cent Bruttolücke rund 4 $ auf 1.000 Kontrakte werden.
- **Sportwetten bei GGL-lizenzierten Anbietern** (feste Quoten) wären die glücksspielrechtlich erlaubte Umgebung; das
  ist kein Prediction Market und wurde hier nicht untersucht. Die Sportwettensteuer beträgt gesetzlich 5,3 % des
  Einsatzes abzüglich der Steuer (rechnerisch ~5,03 % eines steuerinklusiven Betrags, [§ 17](https://www.gesetze-im-internet.de/rennwlottg_2021/__17.html) /
  [§ 18 RennwLottG](https://www.gesetze-im-internet.de/rennwlottg_2021/__18.html)); wie viel davon Kunden tragen und ob
  Konten begrenzt werden, ist anbieterabhängig und nicht untersucht.
- **Für SeasonAlpha (Produktentscheidung, keine Rechtsauskunft):** Prediction-Market-Preise bleiben Daten
  (Wahrscheinlichkeiten, Vergleich mit Saisonalität), kein Handels- oder Arbitrageangebot. Eine Funktion, die
  deutschen Nutzern Arbitrage zwischen diesen Plattformen anzeigt, bräuchte vorher eine eigene rechtliche Prüfung.

## Offene bzw. unsichere Punkte

1. Kalshi-Member-Agreement nur über Codex gelesen (eigener Abruf am Bot-Schutz gescheitert).
2. Steuerliche Einordnung der konkreten Plattformkontrakte nicht verbindlich geklärt; ob planmäßiges Handeln
   gewerblich wird, nicht spezifisch belegt.
3. Keine synchronen Orderbuchdaten; keine belegte, real ausgeführte Zwei-Plattform-Arbitrage mit Gebührenbeleg; kein
   identifiziertes Kontraktpaar mit tatsächlich gegensätzlicher Auszahlung (nur unterschiedliche Regeln belegt).
4. Krause (SSRN) nur Abstract geprüft.
5. Transfer- und Umtauschkosten nur als Szenario; Sportwetten bei deutschen Lizenznehmern nicht untersucht.

## Quellen (Auswahl, Primärquellen bevorzugt)

- Polymarket, Geographic Restrictions (14.08.2026): https://help.polymarket.com/en/articles/13364163-geographic-restrictions
- Polymarket, Fees: https://docs.polymarket.com/trading/fees · Polymarket US, Fees: https://docs.polymarket.us/fees
- Kalshi, Fee Schedule (07.07.2026): https://kalshi.com/docs/kalshi-fee-schedule.pdf · Member Agreement (01.10.2026): https://kalshi.com/docs/kalshi-member-agreement.pdf · Outside the US (20.03.2026): https://help.kalshi.com/en/articles/14026044-can-i-trade-on-kalshi-from-outside-the-united-states · APY: https://help.kalshi.com/en/articles/13823847-apy-on-kalshi
- IB Ireland, Prediction Markets (Fußnote MiFID-Privatkunden): https://www.interactivebrokers.ie/predictionmarkets/en/home.php
- GGL, Warnung Gesellschaftswetten (05.09.2025): https://www.gluecksspiel-behoerde.de/de/news/ggl-warnt-vor-teilnahme-an-illegalen-gesellschaftswetten · Whitelist: https://www.gluecksspiel-behoerde.de/de/fuer-spielende/uebersicht-erlaubter-anbieter-whitelist
- § 285 StGB: https://www.gesetze-im-internet.de/stgb/__285.html · BaFin, binäre Optionen (01.07.2019): https://bafin.de/SharedDocs/Veroeffentlichungen/EN/Aufsichtsrecht/Verfuegung/vf_190701_allgvfg_Binaere_Optionen_en.html · § 20 / § 32d EStG
- Gebele/Matthes, arXiv 2601.01706 · Saguillo u. a., arXiv 2508.03474 · Krause, SSRN 6861841
- Smarkets AGB: https://help.smarkets.com/hc/en-gb/articles/213469085-Smarkets-Terms-and-Conditions · BETDAQ Länderliste: https://betdaq.zendesk.com/hc/en-gb/articles/360016974980-Accepted-countries-list
- OddsShopper, Settlement-Regeln (15.08.2026): https://www.oddsshopper.com/articles/prediction-markets/kalshi-vs-polymarket-settlement-rules
- Codex-Rohbericht mit allen Einzelbelegen: [PREDICTION_MARKETS_2026-10_codex.md](PREDICTION_MARKETS_2026-10_codex.md)

## Lessons aus der Recherche

- **Sekundärseiten zu Prediction Markets sind oft KI-generiert und falsch datiert** — die GGL-Klarstellung stand auf
  mehreren Seiten mit „August 2026", die Primärquelle ist vom 05.09.2025; ein Halbzeit-Auszahlungsfall (0,26/0,74) stand
  in einer Suchzusammenfassung, aber nicht auf der verlinkten Seite. Zahlen nur aus Primärquellen übernehmen.
- **Die 40 Mio. $ „Arbitrage" sind innerhalb einer Plattform entstanden**, nicht zwischen Plattformen.
- **Aufrunden mit Fließkommazahlen ist falsch:** `ceil(0,07·100·0,1·0,9·100)` ergibt in Gleitkomma 64 statt 63 —
  sechs von zehn Tabellenwerten waren um 0,01 Cent zu hoch. Gebührenrechnung mit Dezimalzahlen.
