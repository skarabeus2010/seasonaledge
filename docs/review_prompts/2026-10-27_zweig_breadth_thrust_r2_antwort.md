# Codex-Antwort Runde 2 — Zweig Breadth Thrust (2026-10-27)

Der Entwurf ist als Grundlage tragfähig. Die Kernrechnung stimmt; vor dem Einfrieren der Spezifikation bleiben vier Korrekturen beziehungsweise Präzisierungen.

Review vollständig lesend durchgeführt: Projektstand, Vorbefunde, Entwurf und Probe gelesen; `zbt_probe2.py` mit Python 3.14 ausgeführt; Kalender, EMA, Lückenneustart und Renditen unabhängig nachgerechnet. Keine Dateien oder Daten geändert.

Die 13 Befunde aus Runde 1 sind wie folgt eingearbeitet. Zeilenangaben beziehen sich auf den [Entwurf v2](C:/dev/SeasonalEdge/docs/research/ZWEIG_BREADTH_THRUST.md).

| R1 | Status | Beleg und Bewertung |
|---|---|---|
| 1 | Teilweise erledigt | Z. 84–87 und 121–123: 38 Phantomzeilen und drei Lücken korrekt berücksichtigt. Eine Sensitivitätszahl stammt weiterhin aus der unbereinigten Rechnung, siehe Befund 14. |
| 2 | Erledigt | Z. 93–100: Auswertung ab 1971, davor ausdrücklich benannte Schnittmengen-Konvention als Vorlauf. |
| 3 | Teilweise erledigt | Z. 194–198: Neuinitialisierung und 50 Sitzungen Sperre ersetzen die falsche Zehntagesregel. Übergang und Armierungsverhalten brauchen noch eine eindeutige Festlegung, siehe Befund 16. |
| 4 | Erledigt | Z. 14–16, 27–49: acht Morris-Termine plus Zusatzsignal 2004; Listenabgleich und Definitionsentscheidung getrennt; kein unbelegtes Buchzitat. |
| 5 | Erledigt | Z. 112–117: Herkunft, Universum, Finalisierung und Tagesabweichungen ersetzen Signalgleichheit als Abnahmekriterium. |
| 6 | Erledigt | Z. 70–80: McClellan ergänzt, Pinnacle qualifiziert, Norgate vorsichtig eingeordnet und Anzeigerechte als ungeklärt behandelt. |
| 7 | Erledigt | Z. 88–91 und 224: Strukturdiagnostik und Vergleich vor/nach 2001 vorgesehen, keine Schwellenoptimierung nach Epoche. |
| 8 | Erledigt | Z. 225–227: Zufallsvergleich aus Stufe 1 entfernt; spätere Simulation ausdrücklich an ein definiertes Nullmodell gebunden. |
| 9 | Teilweise erledigt | Z. 212–224: Sitzungsachse, Renditeformel, gleicher Haltehorizont bei t+1 und getrennte Ausfallzahlen festgelegt. Ungültige Werte und überlappende Ausfallgründe bleiben offen, siehe Befund 17. |
| 10 | Erledigt | Z. 218–219: Einstieg eingeschlossen; tiefster Schluss gegenüber Einstieg und Drawdown getrennt, Intraday ausgeschlossen. |
| 11 | Teilweise erledigt | Z. 205–206, 217, 228 und 240–242: Ergebnisfrische, finale Daten, atomare Ausgabe und Fehlerexit berücksichtigt. Die Zustandsübergänge sind noch widersprüchlich, siehe Befund 16. |
| 12 | Erledigt auf Entwurfsebene | Z. 187–190 und 244–256: Pflichtartefakt, frühe analytische EMA-Werte, Produktionspfad und Mutationen ausdrücklich vorgesehen. Ihre tatsächliche Wirksamkeit gehört in den späteren Code-Review. |
| 13 | Erledigt | Z. 164: falsche SMA-Verlustbeispiele entfernt. Die Ersatzbeispiele sind reproduzierbar: −8,74 % nach 60 HT beziehungsweise −12,20 % nach 90 HT, jeweils n=1. |

Die neuen Festlegungen habe ich gesondert geprüft:

- **Lückenregel:** Neuinitialisierung ist eine vertretbare, ausdrücklich benannte Konvention. Der Faktor `(9/11)^50 = 0,00004390` stimmt. Er begrenzt den Startwerteinfluss; er garantiert keine identischen Schwellenentscheidungen bei beliebig knappen Grenzfällen. Mit 50 gesperrten gültigen Sitzungen nach jeder Lücke bleiben alle elf Standardsignale erhalten. In keiner der drei Sperrphasen entsteht ein Standardkandidat.
- **Auswertung ab 1971:** sinnvoll. Der Produktionskalender und die gespeicherte Yahoo-Achse stimmen für 1971 bis 10.02.2020 vollständig überein. Die drei verbleibenden Breitenlücken sind exakt die genannten Termine. Die Schnittmenge vor 1971 eignet sich als deklarierter Vorlauf, nicht als unabhängig belegter historischer Kalender.
- **Anzeige `ausgeloest`:** Signaltag plus fünf folgende Sitzungen sind eindeutig **sechs angezeigte Sitzungen**. Als Anzeigekonvention ist das unproblematisch; ihre Priorität gegenüber neuer Armierung ist noch offen.
- **Rückgänge:** die beiden Kennzahlen sind fachlich sinnvoll getrennt. Für den Drawdown sollte der Wächter Einstieg, Zwischenhoch und anschließenden Rückgang enthalten.
- **Wegfall des Zufallsvergleichs:** angemessen. Einzelfälle, Basisrate und Auslassen einzelner Ereignisse reichen für die beschreibende erste Stufe.
- **Quellenqualifikation:** deutlich verbessert. McClellan bestätigt ausdrücklich Unterschiede zwischen vorläufigen und finalen Zahlen sowie zwischen Datenquellen. Das stützt die neue Abnahme über Herkunft und Tagesabweichungen. [McClellan-Datennotizen](https://www.mcoscillator.com/market_breadth_data/) Die Pinnacle-Seite bestätigt die genannten Preise und A/D ab 1940; die McClellan-Bestellseite war bei dieser Nachprüfung nicht abrufbar. [Pinnacle-Angebot](https://pinnacledata2.com/idx.html)

Die Zahlen aus Abschnitt 3 stimmen überwiegend:

| Prüfung | Ergebnis |
|---|---|
| Elf Signaltermine | Alle bestätigt, auch nach Lückenneustart und Sperre |
| 55 Einzelrenditen für Einstieg t | Alle auf angegebener Genauigkeit bestätigt |
| Aggregate t und t+1 | Sämtliche Mittelwerte, Mediane und Positivzählungen bestätigt |
| Angegebene Basisraten | Für den ausdrücklich genannten Startzeitraum 1965–2020 bestätigt; n=13.832 je Horizont |
| Signalabstand 1974/1975 | 58 Sitzungen bestätigt |
| Sensitivitätszahlen 11 / 13 / 8 / 7 / 14 / 19 / 8 / 3 | Korrekt ist **11 / 13 / 8 / 7 / 14 / 19 / 7 / 3** für 1965–2020 |

Bei Beschränkung sämtlicher Varianten auf den neuen Auswertungsbeginn 1971 werden aus **14 → 13** und **19 → 18**, weil jeweils ein Signal von 1970 entfällt. Die derzeitige Tabelle bezeichnet ihren längeren Zeitraum ausdrücklich; das ist kein Rechenfehler, muss aber beim späteren Vergleich sichtbar bleiben.

Auch die Zwölfmonatsaussage habe ich separat geprüft: Bei Einstieg t sind sowohl nach 252 Sitzungen als auch am ersten Kurstag am oder nach dem Jahrestag alle elf Renditen positiv. Dieser zusätzliche Horizont braucht eine eigene dokumentierte Konvention, falls er veröffentlicht wird.

Neue Befunde:

14. **Mittel — Die bereinigte Variante „Fenster ab erstem Unterschreiten“ liefert sieben statt acht Signale.**  
    **Beleg:** [Z. 165](C:/dev/SeasonalEdge/docs/research/ZWEIG_BREADTH_THRUST.md:165). Die Originalfunktion `signals_first` auf der bereinigten EMA und meine unabhängige Schleife liefern dieselben sieben Termine. Gegenüber der Standardliste entfallen **1971, 2004, 2011 und zusätzlich 2019**.  
    **Korrektur:** Zahl und Erläuterung ändern; diese Variante im reproduzierbaren Zahlenabgleich mitführen. `zbt_probe2.py` berechnet sie bisher nicht neu.

15. **Niedrig — Die EMA des Signals vom 07.01.2019 ist falsch gerundet.**  
    **Beleg:** [Z. 139](C:/dev/SeasonalEdge/docs/research/ZWEIG_BREADTH_THRUST.md:139). Bereinigt ergibt sich **0,6258961994**, also **0,626**, nicht 0,625. Signaltermin und Renditen bleiben unverändert.  
    **Korrektur:** Tabellenwert ersetzen.

16. **Mittel — Anzeigezustand, Neuarmierung und Ende der Sperre sind noch nicht widerspruchsfrei definiert.**  
    **Beleg:** [Neuarmierung Z. 43](C:/dev/SeasonalEdge/docs/research/ZWEIG_BREADTH_THRUST.md:43), [Sperre Z. 194](C:/dev/SeasonalEdge/docs/research/ZWEIG_BREADTH_THRUST.md:194), [Anzeigeablauf Z. 205](C:/dev/SeasonalEdge/docs/research/ZWEIG_BREADTH_THRUST.md:205). Nach einem Signal kann die EMA innerhalb der Anzeigephase erneut unter 0,40 fallen. Dann muss die neue Armierung erhalten bleiben; das pauschale „danach unarmiert“ darf sie nicht löschen. Ebenso fehlt, ob Armierungen während der letzten Sperrsitzungen für spätere Signale zählen.  
    **Korrektur:** Erkennungszustand und Anzeigepriorität getrennt festlegen. Erste gesperrte und erste freie Sitzung explizit benennen; Verhalten während des Vorlaufs durch datierte Grenzfälle absichern.

17. **Mittel — Die Gültigkeitsklassen decken vorhandene, aber unbrauchbare Werte und kombinierte Ausfälle noch nicht eindeutig ab.**  
    **Beleg:** [Z. 212–221](C:/dev/SeasonalEdge/docs/research/ZWEIG_BREADTH_THRUST.md:212). Der [Produktionslader](C:/dev/SeasonalEdge/shared/data.py:220) liefert auch vorhandene Zeilen mit `close=None` oder `log_return=None`. „Fehlende Kurszeilen“ allein erfasst diese Fälle nicht. Außerdem kann ein Fenster zugleich eine interne Lücke enthalten und über den Datenstand reichen.  
    **Korrektur:** Benötigte Schluss- und Returnwerte je Kennzahl sowie deren Gültigkeit festlegen. Für kombinierte Ausfälle entweder eine eindeutige Priorität oder getrennte Gründe mit überschneidungsfreier Hauptzählung definieren. Ereignisse und Basisrate müssen dieselbe Regel verwenden.

Die Freigabe setzt die Korrektur der beiden Tabellenwerte und eindeutige Verträge für Zustandsübergänge und Gültigkeitszählung vor dem Einfrieren der Wächter voraus.

**Urteil: Freigabe mit Auflagen.**
