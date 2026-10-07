# Codex-Antwort (gpt-6-astra, Websuche)


codex
Die genannten Überarbeitungen sind überwiegend korrekt. **Es bleiben zwei sachliche Fehler in den Arbitragebedingungen und eine kleine Präzisierung zur Tabelle.**

Einschränkung des Rückvergleichs: [Die angegebene Vorgeschichte](C:/dev/Seasonaledge/docs/review_prompts/2026-10-07_prediction_markets_pruefung.md) enthält nur den Prüfauftrag, nicht die damalige Antwort mit 14 Befunden. Eine vollständige Bestätigung „14 von 14 erledigt“ ist damit nicht belegbar.

Die konkret genannten Änderungen habe ich geprüft:

- **Z. 106–125: Rechnung bestätigt.** Alle zehn Tabellenwerte stimmen auf zwei Nachkommastellen mit der Dezimalrechnung überein. Auch 29,75 $ Handelsgebühren, 18,67 $ Cash-Gewinn und 4,07 $ nach angenommenen Opportunitätskosten und Steuern stimmen. Die Zinsrechnung verwendet dabei 981,33 $ Kapitalbasis.
- **Z. 19–20, 82: Studie korrekt präzisiert.** Zehn Plattformen im Datensatz, sieben in der kostenberücksichtigenden Analyse; modellierte Kosten und keine tatsächlich ausgeführten Trades sind angemessen abgegrenzt. [Studie einschließlich Anhang I](https://arxiv.org/html/2601.01706v1)
- **Z. 85, 154–155, 175–176: Fallbeispiele bereinigt.** Der Halbzeit-Fall wird nicht mehr als Beleg verwendet; Shutdown wird zutreffend als Regelunterschied ohne nachgewiesene gegensätzliche Auszahlung eingeordnet. [Verlinkter Shutdown-Bericht](https://www.oddsshopper.com/articles/prediction-markets/kalshi-vs-polymarket-settlement-rules)
- **Z. 32, 34, 100: Anbieterpräzisierungen bestätigt.** Kalshi Abschnitt VI, Beschränkung der IBKR-Aussage auf Forecast Contracts sowie Smarkets Pro/Select entsprechen den Quellen. [Kalshi](https://kalshi.com/docs/kalshi-member-agreement.pdf), [IBKR](https://www.interactivebrokers.ie/predictionmarkets/en/home.php), [Smarkets](https://help.smarkets.com/hc/en-gb/articles/213469085-Smarkets-Terms-and-Conditions)
- **Z. 62–76, 121–123, 141–144: Recht und Steuern angemessen eingeschränkt.** Einzelfallvorbehalt, BaFin-Ausnahmen und Steuerannahmen sind enthalten; 5,3 % auf die steuerbereinigte Bemessungsgrundlage entsprechen rund 5,03 % des steuerinklusiven Einsatzes. [§ 285 StGB](https://www.gesetze-im-internet.de/stgb/__285.html), [BaFin](https://bafin.de/SharedDocs/Veroeffentlichungen/EN/Aufsichtsrecht/Verfuegung/vf_190701_allgvfg_Binaere_Optionen_en.html), [§ 17](https://www.gesetze-im-internet.de/rennwlottg_2021/__17.html), [§ 18 RennwLottG](https://www.gesetze-im-internet.de/rennwlottg_2021/__18.html)
- **Z. 101–103, 127–130:** Transferkosten sind als Szenario gekennzeichnet; Kapitalbindung, Teilausführungen, Orderbuchtiefe und Rückabwicklungskosten sind berücksichtigt. Die unbelegte Sekundenbehauptung ist entfernt.

Verbleibende Befunde:

1. **Mittel — [Z. 89–91](C:/dev/Seasonaledge/docs/research/PREDICTION_MARKETS_2026-10.md:89): Identische Regeln sind keine hinreichende Arbitragebedingung.**  
   Sie garantieren weder günstige Erwerbskosten noch Kostendeckung bei einer gemeinsamen Annullierung mit bloßer Einsatzrückzahlung. Der letzte Satz relativiert damit die unmittelbar zuvor korrekt formulierte Szenarioprüfung.  
   **Korrektur:** „Identische Ereignis- und Auflösungsregeln erleichtern den Nachweis komplementärer Auszahlungen. Entscheidend bleibt, dass die Gesamtauszahlung in jedem Szenario sämtliche Kosten deckt; für einen garantiert positiven Gewinn muss sie diese übersteigen.“

2. **Mittel — [Z. 136–138](C:/dev/Seasonaledge/docs/research/PREDICTION_MARKETS_2026-10.md:136): Kurze Laufzeit wird fälschlich zur notwendigen Gewinnbedingung.**  
   Auch eine lange Laufzeit kann bei ausreichendem Preisabschlag rentabel sein. Maßgeblich sind die tatsächlichen Kapitalbindungskosten. Außerdem genügt die dort genannte Deckung des bloßen „Einsatzes“ nicht.  
   **Korrektur:** „Nach Kosten bleibt ein garantierter Überschuss, wenn beide Positionen zu den kalkulierten Preisen vollständig aufgebaut werden und die Mindestauszahlung Erwerbskosten, sämtliche Gebühren und laufzeitabhängige Kapitalbindungskosten übersteigt.“

3. **Niedrig — [Z. 108–116](C:/dev/Seasonaledge/docs/research/PREDICTION_MARKETS_2026-10.md:108): Gerundete Tabellenwerte werden als exakte Entscheidungsgrenzen beschrieben.**  
   Bei `p = 0,10`, `r = 0,04` beträgt die tatsächliche Modellschwelle **1,022295… Cent**, angezeigt werden 1,02 Cent. Eine Lücke knapp darüber muss also noch keinen Gewinn ergeben. Die Tabellenwerte selbst sind richtig.  
   **Korrektur:** „Tabellenwerte auf 0,01 Cent gerundet; für die Gewinnprüfung die ungerundete Schwelle und tatsächlich handelbare Tickgrößen verwenden.“

FREIGABE: nein
