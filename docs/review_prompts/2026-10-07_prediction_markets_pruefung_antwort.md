# Codex-Antwort (gpt-6-astra, Websuche)


codex
Der Bericht ist noch nicht freigabefähig. Die Beispielrechnung stimmt unter ihren Annahmen; wesentliche Korrekturen betreffen die Gewinnschwellen, die Studieninterpretation und pauschale rechtliche Schlussfolgerungen. Alle Zeilenangaben beziehen sich auf [PREDICTION_MARKETS_2026-10.md](C:/dev/Seasonaledge/docs/research/PREDICTION_MARKETS_2026-10.md).

1. **Hoch — Z. 16–18, 73, 118–120: Studie falsch interpretiert und Kosten doppelt angesetzt.**  
   Gebele/Matthes untersuchen ausdrücklich semantisch abgeglichene Märkte. Die Behauptung, ihre Abweichungen seien überwiegend wegen unterschiedlicher Auszahlungen keine Arbitrage, gibt den Befund nicht richtig wieder. Die Ausführungsanalyse umfasst sieben der zehn Plattformen und berücksichtigt bereits modellierte Gebühren und Spreads.  
   **Korrektur:** Datensatzumfang und Ausführungssample trennen; 2–4 % als modellbereinigte Abweichungen beschreiben. Den pauschalen Vergleich mit einer zusätzlich abzuziehenden heutigen 3-Cent-Gebührenschwelle streichen. Stattdessen historische Kostenannahmen, fehlende tatsächliche Fills und eingeschränkte Übertragbarkeit auf Oktober 2026 nennen. [Studie, § 5.4 und Anhang I](https://arxiv.org/html/2601.01706v1)

2. **Mittel — Z. 95–104: Sechs Tabellenwerte sind falsch.**  
   Nach der vorgegebenen Rundung gilt bei \(C=100\):
   \[
   F_K=\frac{\lceil100\cdot0{,}07Cp(1-p)\rceil}{100},\qquad
   p+q_{\max}+F_K/C+r q_{\max}(1-q_{\max})=1.
   \]
   **Korrektur:** Folgende Gewinnschwellen verwenden; Werte in Cent je Kontraktpaar:

   | p | r = 0,04 | r = 0,05 |
   |---|---:|---:|
   | 0,10 | 1,022295 → **1,02** | 1,124342 → **1,12** |
   | 0,30 | 2,345325 → **2,35** | 2,568064 → **2,57** |
   | 0,50 | 2,746982 → **2,75** | 2,995513 → **3,00** |
   | 0,70 | 2,271591 → **2,27** | 2,467603 → **2,47** |
   | 0,90 | 0,958946 → **0,96** | 1,037944 → **1,04** |

   Die exakten Schwellen sind \(100(1-p-q_{\max})\). Für positiven Gewinn muss die Lücke darüber liegen; gerundete Tabellenwerte sind keine ausführbaren Limitpreise. Tickgrößen separat berücksichtigen.

3. **Hoch — Z. 11–15, 114–126: Fehlender Legalitätsnachweis wird zum allgemeinen Verbotsnachweis.**  
   „Keine belegte legale Kombination“ trägt weder „keine legal ausführbare Arbitrage“ noch die pauschale Einordnung jeder Arbitrage-Funktion als Anleitung zu illegalem Glücksspiel. „Die einzige legale Parallele“ ist ebenfalls nicht belegt.  
   **Korrektur:** „Unter den untersuchten Angeboten wurde keine für deutsche Privatkunden belastbar legal zugängliche Kombination nachgewiesen.“ Für SeasonAlpha eine Produktentscheidung formulieren; die rechtliche Bewertung einer konkreten Funktion separat prüfen. Die GGL-Warnung betrifft Gesellschaftswetten; Finanzinstrumente erfordern eine eigene Einordnung. [GGL](https://www.gluecksspiel-behoerde.de/de/news/ggl-warnt-vor-teilnahme-an-illegalen-gesellschaftswetten), [BaFin-Verfügung](https://bafin.de/SharedDocs/Veroeffentlichungen/EN/Aufsichtsrecht/Verfuegung/vf_190701_allgvfg_Binaere_Optionen_en.html)

4. **Mittel — Z. 28, 130–131: Kalshi-Primärquelle ist direkt prüfbar.**  
   Das Member Agreement vom 01.10.2026 ist abrufbar. Deutschland fehlt tatsächlich in Abschnitt VI; örtliche Verbote und Kalshis eigene Zugangspolitik bleiben vorbehalten.  
   **Korrektur:** „Laut Codex“ durch direkten Primärbeleg ersetzen. Den Abrufvorbehalt aktualisieren; angeblich widersprechende Sekundärquellen konkret benennen oder streichen. Ergebnis weiterhin: **keine deutsche Handelsfreigabe nachgewiesen**. [Member Agreement, Abschnitt VI](https://kalshi.com/docs/kalshi-member-agreement.pdf)

5. **Mittel — Z. 30, 32, 62: Zugangsaussagen müssen produktspezifisch bleiben.**  
   Der IBKR-Ausschluss für MiFID-Retail-*Forecast Contracts* ist bestätigt. Daraus folgt nicht pauschal „IBKR lässt Privatkunden nicht zu“; die Seite unterscheidet Forecast und Event Contracts. Bei Smarkets ist keine ausdrückliche DE-Listensperre dokumentiert, wohl aber die Pflicht zur örtlichen Rechtmäßigkeit.  
   **Korrektur:** IBKR-Aussage auf Forecast Contracts begrenzen. Für Smarkets „kein legaler DE-Exchange-Zugang belegt“ verwenden und technische Zugänglichkeit, AGB und deutsche Erlaubnis getrennt ausweisen. [IBKR](https://www.interactivebrokers.ie/predictionmarkets/en/home.php), [Smarkets-AGB](https://help.smarkets.com/hc/en-gb/articles/213469085-Smarkets-Terms-and-Conditions)

6. **Mittel — Z. 53–62: Einzelfallvorbehalt des Rohberichts fehlt.**  
   GGL-Datum und Strafrahmen des § 285 StGB stimmen. Die Behördenposition ersetzt aber keine Prüfung sämtlicher Voraussetzungen einer individuellen Strafbarkeit.  
   **Korrektur:** Ergänzen: „Ob § 285 StGB im Einzelfall erfüllt ist, bedarf gesonderter Prüfung.“ Die Sportwettenaussage ausdrücklich im glücksspielrechtlichen Kontext belassen. Bei BaFin die eng gefasste Ausnahme der Verfügung erwähnen; sie ist kein unterschiedsloses Verbot sämtlicher binärer Finanzprodukte. [§ 285 StGB](https://www.gesetze-im-internet.de/stgb/__285.html), [BaFin](https://bafin.de/SharedDocs/Veroeffentlichungen/EN/Aufsichtsrecht/Verfuegung/vf_190701_allgvfg_Binaere_Optionen_en.html)

7. **Hoch — Z. 76: Konkrete Settlement-Beispiele sind so nicht belegt.**  
   Die verlinkte OddsShopper-Seite enthält aktuell keinen Halbzeitfall mit 0,26/0,74. Beim Shutdown vergleicht sie unter anderem allgemeine Kalshi-Erstiterationsbedingungen mit einem konkreten Polymarket-Markt; das belegt keine nachträgliche Stichtagsverschiebung eines identifizierten Kontraktpaares. Zudem bedeuten abweichende Auszahlungen nicht automatisch „doppelten Verlust“.  
   **Korrektur:** Konkrete Markt-IDs, damalige Regeln und Settlement-Belege nachreichen oder die Fälle entsprechend einschränken beziehungsweise entfernen. Gewinn/Verlust erfordert zusätzlich Kaufpreise und Positionsrichtung. [Verlinkter Artikel](https://www.oddsshopper.com/articles/prediction-markets/kalshi-vs-polymarket-settlement-rules)

8. **Mittel — Z. 19–20, 86–89: Gebührenübersicht zu pauschal.**  
   Die 2,75–3-Cent-Schwelle gilt für das modellierte Kalshi-/Polymarket-International-Taker-Paar, nicht allgemein. Kalshi-Maker-Gebühren gelten serienabhängig; der Standard-Maker-Multiplikator ist null. Polymarket US nennt zum 07.10.2026 Sonderänderungen, darunter Tischtennis \(0{,}10\).  
   **Korrektur:** Modellpaar ausdrücklich nennen. Maker-Rebate bei Polymarket US als \(0{,}0125Cp(1-p)\) für einschlägige Standardgeschäfte ausweisen, Rundung und Ausnahmen ergänzen. [Kalshi](https://kalshi.com/docs/kalshi-fee-schedule.pdf), [Polymarket US](https://docs.polymarket.us/fees)

9. **Mittel — Z. 89, 109–110: Smarkets-Sondertarife fehlen.**  
   Die 2 % gelten nur im Standardtarif. Pro/Select können 1 % beziehungsweise 3 % auf Gewinn **oder Verlust je Wette** erheben. Das ist gerade für Arbitragestrategien wesentlich.  
   **Korrektur:** Tarifvorbehalt und abweichende Bemessungsgrundlage wieder aus dem Rohbericht übernehmen. Die Beispiele +7,80 € und −0,04 € stimmen ausschließlich unter der genannten Standardprovision. [Smarkets, Abschnitt 3](https://help.smarkets.com/hc/en-gb/articles/213469085-Smarkets-Terms-and-Conditions)

10. **Mittel — Z. 90–91: Unbelegte Erfahrungswerte.**  
    Für „oft nur Sekunden“ und „je Kette 0,5–1 % realistisch“ fehlen belastbare Belege und Bezugsgrößen.  
    **Korrektur:** Sekundenbehauptung streichen oder mit konkreten Messdaten belegen. Transferkosten als **Szenarioannahme** kennzeichnen und Zahlungsweg, Betrag sowie Ein- oder Hin-und-Rücktransfer festlegen. Slippage ist nur dann bereits enthalten, wenn mengenabhängige Ausführungspreise statt bloßer bester Asks verwendet werden.

11. **Mittel — Z. 92, 108: Kapitalbindung zu absolut beschrieben.**  
    Bei angenommenen 4 % sind 0,333 Cent pro Dollar und Monat sowie 0,986 Cent für 90 Tage korrekt. „Beide Seiten bis zur Auflösung gesperrt“ ist jedoch keine allgemeine Produkteigenschaft.  
    **Korrektur:** „Für die modellierte Haltestrategie bis zur jeweiligen Auszahlung gebunden; vorzeitiger Verkauf abhängig von Zugang und Liquidität.“ Unterschiedliche Auszahlungstermine und gegebenenfalls Guthabenzinsen/Coupons berücksichtigen. Kalshis Zinsprogramm ist tatsächlich auf berechtigte US-Nutzer beschränkt. [Kalshi APY](https://help.kalshi.com/en/articles/13823847-apy-on-kalshi)

12. **Mittel — Z. 63–67, 106–108: Steuerannahmen wurden zu stark verkürzt.**  
    Die etwa 4 $ sind rechnerisch nachvollziehbar: \(18{,}67×26{,}375\%=4{,}92\) $ Steuer; nach 9,68 $ Zinsentgang bleiben **4,07 $**. Dafür fehlen aber die Rohbericht-Annahmen: ausgeschöpfter Sparer-Pauschbetrag, keine Kirchensteuer und 18,67 $ vollständig als steuerlicher Nettogewinn anerkannt. Nicht sämtliche wirtschaftlichen Nebenkosten sind automatisch steuerlich abziehbar.  
    **Korrektur:** Diese Bedingungen wieder aufnehmen, Opportunitätskosten als nicht zahlungswirksam kennzeichnen und die behauptete Gewerblichkeit allein aufgrund „planmäßigen Handels“ nicht ohne spezifischen Beleg stehen lassen. [§ 20 EStG](https://www.gesetze-im-internet.de/estg/__20.html), [§ 32d EStG](https://www.gesetze-im-internet.de/estg/__32d.html)

13. **Mittel — Z. 122–123: Sportwettensteuer mit falscher Bezugsgröße.**  
    Gesetzlich sind es 5,3 % des Einsatzes **abzüglich Sportwettensteuer**. Bei steuerinklusive geleistetem Betrag entspricht das rechnerisch etwa 5,033 %.  
    **Korrektur:** Gesetzliche Bemessungsgrundlage nennen; die tatsächliche Kundenbelastung anhand des jeweiligen Anbietertarifs berechnen. „Häufig weitergegeben“ und Kontolimitierungen belegen oder als nicht untersucht kennzeichnen. [§ 17](https://www.gesetze-im-internet.de/rennwlottg_2021/__17.html), [§ 18 RennwLottG](https://www.gesetze-im-internet.de/rennwlottg_2021/__18.html)

14. **Hoch — Z. 78–80, 95–120: Wesentliche Bedingungen praktischer Nettoarbitrage fehlen.**  
    **Korrektur:** Ergänzen: Vorfinanzierung beider Konten; nicht atomare Ausführung und einseitige/partielle Fills; mengenabhängige Orderbuchtiefe; Kosten des Rückabwickelns einer ungehedgten Position; USD-/Stablecoin-Parität, EUR-Wechselkurs und Plattform-/Auszahlungsrisiko. Die im Rohbericht ausdrücklich angenommene Wertgleichheit von Dollar und Stablecoin muss wieder sichtbar werden. Settlement-Prüfung um Annullierung, Rückzahlung und Teilzahlungen erweitern. Identische Regeln sind eine hinreichende Bedingung; entscheidend ist letztlich die Mindestgesamtauszahlung in **jedem** relevanten Szenario.

Bestätigt sind die Beispielwerte **29,75 $ Gebühren, 18,67 $ Cash-Gewinn, 9,68 $ Zinsentgang und 8,99 $ wirtschaftlicher Vorsteuergewinn** sowie **−9,98 $** beim Paar 0,48 + 0,50. Auch Polymarkets DE-Sperre ist belegt. Die rund 40 Mio. $ bei Saguillo sind als **geschätzte** realisierte Gewinne innerhalb Polymarkets korrekt; Zeitraum 01.04.2024–01.04.2025. Krauses 26,1 Prozentpunkte sind im Abstract bestätigt, weiterhin ohne verifizierten Ausführungsnachweis. [Polymarket-Zugang](https://help.polymarket.com/en/articles/13364163-geographic-restrictions), [Saguillo](https://arxiv.org/html/2508.03474v1), [Krause](https://papers.ssrn.com/sol3/Delivery.cfm/6861841.pdf?abstractid=6861841&mirid=1)

FREIGABE: nein
