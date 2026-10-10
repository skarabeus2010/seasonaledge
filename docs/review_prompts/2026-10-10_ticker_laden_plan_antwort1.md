# Antwort Codex — Ticker schneller laden, Runde 1 (2026-10-10)

Prompt: [2026-10-10_ticker_laden_plan.md](2026-10-10_ticker_laden_plan.md). model: gpt-6.1-sol

## Urteil

**Die Richtung ist tragfähig, der Plan braucht vor der Umsetzung Ergänzungen.** Der kleinste sichere Schritt ist **O1 einschließlich neuer Abbruchlogik**. Danach **O2 auf sämtliche Kurslader ausweiten**, laufende Abrufe teilen und erst dann **O4 pilotieren**. Statische Kursdateien versprechen den größten strukturellen Gewinn beim erstmaligen Aufruf eines Tickers. IndexedDB verbessert hauptsächlich Wiederholungsaufrufe.

Die Bestandsaufnahme bestätigt **16 Seiten mit `SA.fetchAllPrices`**, zusätzlich **zehn Seiten mit eigenen paginierten Kursladern** und die Watchlist mit `ladeVollHistorie`. Eine Änderung allein an `app.js` erreicht also einen erheblichen Teil der Website nicht.

Geprüft wurde der aktuelle Arbeitsbaum einschließlich der vorhandenen P2-Änderungen. **Nichts geschrieben.** Direkte HTTP-Anfragen waren durch den Netzwerkzugang dieser Umgebung blockiert; eigene Live-Laufzeiten, Live-Header und Browser-Renderzeiten liegen deshalb nicht vor. Die Messwerte im Auftrag sind Vorwerte, keine in dieser Prüfung reproduzierten Ergebnisse.

## Bestandsaufnahme

Die folgenden Anzahlen gelten für erfolgreiche Abrufe ohne Wiederholungen und ohne Cache-Treffer. `N` bezeichnet die Zeilenzahl **nach dem jeweiligen Filter**.

| Kürzel | Tatsächlicher Ladeweg |
|---|---|
| **F** | [`SA.fetchAllPrices`](/C:/dev/SeasonalEdge/landing/js/app.js:743): `prices`, `ticker=eq.…`, `select=date,close,log_return,tdom,tdoy`, aufsteigend; Range-Blöcke à 1.000 **nacheinander**, jeweils `count=exact`. Anzahl normalerweise `max(1, ceil(N/1000))`. localStorage, 15 Minuten, Schlüssel `ticker\|extraFilter`; keine Zusammenfassung laufender Abrufe. |
| **L** | Lokaler Seitenlader: ebenfalls `prices`, Tickerfilter, aufsteigend, Range-Blöcke à 1.000 **nacheinander**, `count=exact`. Felder stehen in der Tabelle. Kein gemeinsamer Cache; meist nur zuletzt geladene Daten im Seitenspeicher. |
| **V** | [`ladeVollHistorie`](/C:/dev/SeasonalEdge/landing/js/decade-compute.js:536): gleiche fünf Felder wie F, **ungefilterte Vollhistorie**, `limit=1000`, danach `date=gt.<letztes Datum>`, nacheinander, ohne Zählung. `floor(N/1000)+1` Anfragen; eigener Memory-Cache, 15 Minuten. Kein gemeinsames laufendes Promise. |
| **R** | [`anomalieMitHistorie`](/C:/dev/SeasonalEdge/landing/js/decade-compute.js:573): bedingtes Nachladen mit **F**, ab 31 Jahren vor dem letzten bereinigten Kursdatum. Entfällt nur, wenn die übergebene Reihe bereits entsprechend weit zurückreicht. Lädt das überlappende Fenster nochmals, nicht bloß fehlende ältere Zeilen. |
| **Memory** | Daten bleiben im JavaScript-Speicher der Seite. Ohne ausdrücklich genannten TTL gibt es keine zeitliche Entwertung. |

**Gemeinsame Initialabrufe:** Navigation/Footer, Analytics, Wörterbuch, Auth-/Tier-Ermittlung und gegebenenfalls Watchlist-Synchronisierung gehören zum Seitenstart, nicht zu jedem Tickerwechsel. [`initTickerInput`](/C:/dev/SeasonalEdge/landing/js/app.js:674) lädt `tickers.json` in `SA._tickerCache`. Zwei Suchfelder können vor Abschluss dieses ersten Abrufs zwei Metadatenanfragen auslösen.

### Seiten mit direkten Kursabrufen

In den Zeilen mit Zeitraumregler bezeichnet `Y` das aktuelle Jahr und `n` die gewählte Jahreszahl.

| Seite / Anker | Abrufe beim neuen Ticker: Quelle, Filter, Reihenfolge | Vollhistorie, Zusatzabrufe und Cache |
|---|---|---|
| [Dashboard](/C:/dev/SeasonalEdge/landing/pages/dashboard.html:2248) | **F**, letzte 30 Jahre. Nach Abschluss starten **V** für Saison-Score, **R** für Radar und eine einzelne `prices`-Abfrage mit `date,open,close`, Zeitraum gemäß Regler (`:2196`). Die Zusatzabrufe können überlappen. | V lädt vollständig; damit zwei bis drei überlappende Close-Historien. F/V getrennt gecacht. Overnight-Abfrage ohne Pagination und ohne eigenen Cache. |
| [Dekadenzyklus](/C:/dev/SeasonalEdge/landing/pages/dekadenzyklus.html:292) | **F**, ohne Datumsfilter; danach gegebenenfalls **R** (`:659`). | Volle Historie. Zusätzlich `tickerCache` für Daten und berechnetes Ergebnis, **ohne TTL**. R lädt bei jüngeren Reihen trotzdem nochmals. `DJI-decade.json` ist nur Startfallback bei fehlender Konfiguration. |
| [Jahreszyklus](/C:/dev/SeasonalEdge/landing/pages/jahreszyklus.html:1664) | **L**, `date,close,log_return`; ab `Y−n−1-01-01`, bei „max“ ungefiltert. Danach **R** über `rerender()` (`:1649`). | Vollständig nur bei „max“. Aktuelle Daten im Memory; keine Wiederverwendung zwischen Tickern. R überlappt. |
| [KI-Saisonalität / Saison-Score](/C:/dev/SeasonalEdge/landing/pages/ki-saisonalitaet.html:716) | **L**, `date,close,log_return`; ab `Y−n−1-01-01`, „max“ ungefiltert. Nach erstem Render **V** (`:760`). | V immer vollständig, unabhängig vom Regler. Selbst bei „max“ zweite Vollhistorienladung. L und V teilen keinen Cache. |
| [Risikozyklus](/C:/dev/SeasonalEdge/landing/pages/risikozyklus.html:857) | **L**, `date,close,log_return`; ab `Y−n−1-01-01`, „max“ ungefiltert. Danach **R** (`:851`). | Vollständig bei „max“; aktueller Memory. R überlappt. |
| [Monatszyklus](/C:/dev/SeasonalEdge/landing/pages/monatszyklus.html:2045) | **F**, letzte 30 Jahre; danach **R** (`:1966`). | Keine Vollhistorie bei älteren Tickern. F und R verwenden unterschiedliche Filter-/Cache-Schlüssel. |
| [Monatswechsel](/C:/dev/SeasonalEdge/landing/pages/monatswechsel.html:227) | **F**, letzte 30 Jahre. | localStorage F plus aktuelle Reihe im Memory. Weitere Regler rechnen daraus. |
| [Mondphasen](/C:/dev/SeasonalEdge/landing/pages/mondphasen.html:204) | **F**, letzte 30 Jahre. | Wie Monatswechsel. |
| [Kriegszeiten](/C:/dev/SeasonalEdge/landing/pages/kriegszeiten.html:268) | **F**, ab `1895-01-01`. | Sehr lange Historie, aber keine allgemeine Vollhistorie: ältere vorhandene Kurse bleiben ausgeschlossen. |
| [Plain Vanilla](/C:/dev/SeasonalEdge/landing/pages/plain-vanilla.html:312) | **F**, ab `1895-01-01`. | F-Cache; aktuelle Reihe und berechnete Strategieergebnisse im Memory. |
| [Trifecta](/C:/dev/SeasonalEdge/landing/pages/trifecta.html:276) | **F**, ab `1895-01-01`. | F-Cache plus aktuelle Reihe im Memory. |
| [Feiertage](/C:/dev/SeasonalEdge/landing/pages/feiertage.html:623) | **F**, ungefiltert. Feiertage aus bereits geladenem JS. | Volle Historie; Zeitraumänderungen rechnen auf der aktuellen Reihe. |
| [Zentralbanken](/C:/dev/SeasonalEdge/landing/pages/zentralbanken.html:568) | **F**, ungefiltert. Beim Start davor einmal `central_bank_dates`, `select=bank,date&order=date` (`:292`). | Volle Historie. Zentralbanktermine im Memory. Separater Startblock: Polymarket-Katalog, danach jüngste Fed-Preise (`:621`), nicht tickerabhängig. |
| [Dividendenkalender](/C:/dev/SeasonalEdge/landing/pages/dividend-kalender.html:477) | Parallel: ungefiltertes **F** und **eine** `dividend_events`-Abfrage, Tickerfilter, `ex_date,amount`, `order=ex_date` (`:210`). | Volle Kurshistorie. Ereignisse ohne Pagination. Eigenes `tickerCache` für Kurse und Ereignisse, **ohne TTL**; Rückwechsel überspringt beide Abrufe. |
| [Earnings-Kalender](/C:/dev/SeasonalEdge/landing/pages/earnings-kalender.html:628) | Parallel: ungefiltertes **F** und **eine** `earnings_events`-Abfrage, Tickerfilter, `report_date,eps_actual,eps_estimate,surprise_pct`, `order=report_date` (`:252`). | Volle Kurshistorie. Ereignisse ohne Pagination. Eigenes `tickerCache` **ohne TTL**. |
| [Overnight](/C:/dev/SeasonalEdge/landing/pages/overnight.html:638) | **L**, `date,open,close,tdom,tdoy`; ab `Y−n-01-01`, „max“ ungefiltert. Anschließend Open-Filter und **R** (`:672`). | Vollhistorie bei „max“, danach auf vorhandene Open-Kurse reduziert. Aktueller Memory; Radar kann Close-Daten erneut laden. |
| [TDOM-Analyse](/C:/dev/SeasonalEdge/landing/pages/tdom-analyse.html:1211) | **L**, `date,open,close,tdom,tdoy`; ab `Y−n-01-01`, „max“ ungefiltert. Anschließend Open-Filter, Anreicherung und **R** (`:1244`). | Vollhistorie bei „max“, danach gefiltert. Aktueller Memory; keine gemeinsame Wiederverwendung. |
| [Wochentage](/C:/dev/SeasonalEdge/landing/pages/wochentage.html:1811) | **L** über `fetchOHLC`, `date,open,close`, letzte 30 Jahre. | Kein gemeinsamer Cache; aktuelle Reihe im Memory. |
| [Backtest-Engine](/C:/dev/SeasonalEdge/landing/pages/backtest-engine.html:1662) | **L** über `fetchOHLC`, `date,open,close`, letzte 50 Jahre. Nach Laden automatischer Backtest. | Kein gemeinsamer Cache; aktuelle Reihe im Memory. Rechenzeit gehört zusätzlich zur Wartezeit. |
| [OPEX](/C:/dev/SeasonalEdge/landing/pages/opex.html:1223) | **L**, `date,close`; ab `Y−n−1-01-01`, „max“ ungefiltert. | Vollständig bei „max“; nur aktuelle Reihe im Memory. |
| [VIXpiration](/C:/dev/SeasonalEdge/landing/pages/vixpiration.html:1117) | **L**, `date,close`; ab `Y−n−1-01-01`, „max“ ungefiltert. | Wie OPEX. |
| [Spot-Vol-Beta](/C:/dev/SeasonalEdge/landing/pages/spot-vol-beta.html:1148) | Zwei **L**-Ladungen parallel: Spot und Vol-Index, jeweils `date,close`; letzte n Jahre, „max“ ab `1990-01-01`. Blöcke je Ticker sequenziell. | Keine ungefilterte Vollhistorie. Kein gemeinsamer Cache. Wechsel eines Partners lädt beide erneut. |
| [Intermarket-Shocks](/C:/dev/SeasonalEdge/landing/pages/intermarket-shocks.html:761) | Zwei **F**-Ladungen parallel: Trigger und Ziel, ab `Y−n-01-01`. | Beide F-gecacht. Identische Trigger-/Zielticker können kalt doppelte laufende Ladungen erzeugen. Startmetadaten über zwei Suchfelder. |
| [Sektor-Rotation](/C:/dev/SeasonalEdge/landing/pages/sektor-rotation.html:607) | Für jeden ausgewählten Ticker **F**, ab `Y−n-01-01`. Gruppen von drei Tickern parallel; nächste Gruppe erst nach Abschluss aller drei. | F-Cache. Eine Änderung startet die Ladung aller ausgewählten Ticker erneut. Fehler werden zu leeren Reihen. |
| [Watchlist](/C:/dev/SeasonalEdge/landing/pages/watchlist.html:437) | Je Watchlist-Ticker **V**. Pool mit höchstens drei gleichzeitigen Tickern (`:748`); je Ticker sequenzielle Blöcke. Hinzufügen startet `loadAll()` erneut. | Volle Historie; V-Memory-Cache 15 Minuten. Sortieren lokal. Karten werden erst nach Abschluss des gesamten Pools veröffentlicht. `tickers.json` einmal beim Start; persönliche Liste über Auth-Synchronisierung. |
| [Stress-Ampel](/C:/dev/SeasonalEdge/landing/pages/crash-fruehwarnung.html:215) | Fester Ticker SPY: parallel **F** über 13 Jahre und `stress_laeufe` für jüngsten fertigen Lauf; danach eine `stress_scores`-Abfrage ab heute minus 420 Tage. | Keine Vollhistorie. F-Cache; Lauf-/Score-Abfragen ohne eigenen Cache. Separater Startblock: Polymarket-Katalog, danach jüngste Preise und 180-Tage-Historie parallel (`:377`). |
| [Polymarket](/C:/dev/SeasonalEdge/landing/pages/polymarket.html:650) | Katalog → jüngste Preise und gewählte Historie parallel → bei Kryptoanzeige ungefiltertes **F** für BTC und ETH, beide parallel (`:519`). | Beide Kryptohistorien vollständig. Kein Tickersuchfeld; Kategorie-/Zeitraumwechsel kann diese Abrufe erneut auslösen. F-Cache; Marktquellen siehe unten. `brier_stats.json` separat beim Start. |

Die gemeinsamen Polymarket-Lader stehen in [`polymarket.js`](/C:/dev/SeasonalEdge/landing/js/polymarket.js:84):

- Katalog: eine `polymarket_markets`-Abfrage, `active=eq.true&order=category,slug`.
- Jüngste Preise: eine `polymarket_prices`-Abfrage mit `condition_id=in.(…)`, `order=ts.desc`, `limit=5×Marktzahl`.
- Historie: `condition_id=in.(…)`, `ts=gte.…`, `order=ts.asc`; `getAll` mit sequenziellen Offset-Blöcken. Keine eigenen Anwendungs-Caches.

### Seiten mit statischen Daten oder persönlichem Kalender

Dateipfade beginnen jeweils mit `/landing/data/`. „0 beim Wechsel“ bedeutet: Die Seite hat die Daten zuvor bereits geladen.

| Seite / Anker | Quelle und Reihenfolge | Tickerwechsel / Cache / Vollhistorie |
|---|---|---|
| [Dealer Positioning](/C:/dev/SeasonalEdge/landing/pages/dealer-positioning.html:310) | `gex_summary.json` → Profil des Starttickers. | Neuer Profil-Ticker: **ein** `gex_profile_<Ticker>.json`-Abruf, `no-store`; danach `profiles`-Memory ohne TTL. Keine Kurshistorie. |
| [IV-Surface](/C:/dev/SeasonalEdge/landing/pages/iv-surface.html:256) | Einmal `iv_surface.json`, `no-store`. | 0; gesamter Datensatz im Memory. |
| [Options-Flow](/C:/dev/SeasonalEdge/landing/pages/options-flow.html:279) | `options_flow.json` parallel zur Kette `options_skew.json` → `options_skew_history.json`; alle `no-store`. | 0; lokale Auswahl aus vorgeladenen Datensätzen. |
| [Key Levels](/C:/dev/SeasonalEdge/landing/pages/key-levels.html:288) | Einmal `key_levels.json`, `no-store`. | 0; Memory. |
| [Skew](/C:/dev/SeasonalEdge/landing/pages/skew.html:733) | `gex_summary.json` und `options_skew.json` parallel; nach Skew-Daten `options_skew_history.json`. Alle `no-cache`. | 0; Memory. Optionshistorie, keine `prices`-Vollhistorie. |
| [Flows](/C:/dev/SeasonalEdge/landing/pages/flows.html:754) | Sieben parallele Dateien: `flows_rebalancing`, `buyback_blackout`, `etf_flows`, `cot_positioning`, `volcontrol_proxy`, `shortvol_proxy`, `options_skew`; danach zusätzlich `options_skew_history`. Alle `.json`, `no-cache`. | Lokale Auswahl; keine tickerabhängigen Kursabrufe. |
| [Korrelationen](/C:/dev/SeasonalEdge/landing/pages/korrelationen.html:421) | Einmal `korrelationen.json`, `no-cache`. | 0 beim Paarwechsel; enthaltene Renditereihen und Referenzen im Memory. |
| [Intermarket-Matrix](/C:/dev/SeasonalEdge/landing/pages/intermarket.html:418) | Einmal `intermarket_matrix.json`, `no-cache`. | 0; lokale Auswahl vorab berechneter Ergebnisse. |
| [Vola-Saisonalität](/C:/dev/SeasonalEdge/landing/pages/vola-saisonalitaet.html:332) | Einmal `vol_saisonalitaet.json`, `no-cache`. | 0; Profile aller enthaltenen Ticker im Memory. |
| [Wahlen](/C:/dev/SeasonalEdge/landing/pages/wahlen.html:504) | Einmal `wahlen_study.json` oder ausgewähltes `wahlen_snapshots/<id>.json`, `no-cache`. | 0 beim Reihenwechsel; Wahlfenster und Ergebnisse im Memory, keine rohe Vollhistorie. |
| [Index-Effekt](/C:/dev/SeasonalEdge/landing/pages/index-effekt.html:309) | Einmal `index_effect_study.json`, `no-store`. | 0; Auswahl aus vorhandenen Aufnahmeereignissen. |
| [Congress](/C:/dev/SeasonalEdge/landing/pages/congress.html:197) | Einmal `congress_trades.json`, `no-store`. | Lokale Tickertabelle; keine Kurshistorie. |
| [Scanner](/C:/dev/SeasonalEdge/landing/pages/scanner.html:329) | Parallel `tickers.json` und: jüngstes `scanner_results.scan_date` für `saison_v1` → Ergebnisse dieses Datums, `order=score.desc.nullslast&limit=2000`. | Filtern/Sortieren lokal, kein Kursabruf. Ergebnisabfrage ohne Pagination; aktuell 370 Metadaten-Ticker. |
| [Kalender](/C:/dev/SeasonalEdge/landing/js/kalender-compute.js:80) | `market_calendar.json`; für Premium zusätzlich zwei parallele Monatsabfragen: `dividend_events` und `earnings_events`, Datumsintervall `[Monatsanfang, nächster Monatsanfang)`, `ticker in Watchlist ∪ {DIA,USO}`. | Kein Einzel-Tickerwechsel; personalisierte Monatsdaten werden nachgeladen. Keine Kurshistorie, keine Pagination dieser Ereignisabfragen. |

Damit sind sämtliche **41 Seiten mit Marktdaten/Tickern** erfasst. `apex-demo.html` zeichnet synthetische Beispieldaten; `pricing`, `profile` und `unsubscribe` haben keinen Marktkurs-Ladeweg.

## Bewertung O1–O7 und Ergänzungen

| Option | Bewertung | Erforderliche Ergänzung |
|---|---|---|
| **O1: Zählung entfernen** | **Erster Schritt, geringer Aufwand.** Entfernt unnötige Datenbankarbeit; garantiert wegen schwankender Messwerte keine Beschleunigung jedes einzelnen Aufrufs. | Nicht nur den Header löschen: über Blocklänge terminieren. `Content-Range: …/*` darf nicht als fertige Ladung gelten. Bestehende HTTP-/Array-Prüfung und Retries erhalten. |
| **O2: Gemeinsamer Lader** | **Sehr hoher Nutzen je Aufwand.** Beseitigt doppelte Historien und zehn lokale Implementierungen. | `open` unterstützen; bereits laufende Promises teilen; Vollhistorie und Teilfenster können dieselbe ausreichend große Datenbasis nutzen. Felder, Abdeckung und Revision müssen zum Cache-Vertrag gehören. |
| **O3: Parallelisierung** | Bedingt sinnvoll als Optimierung des DB-Fallbacks. **Die vorliegenden vier Ticker zeigen keinen einheitlichen Gewinn**; beim DAX war die Parallelvariante sogar langsamer als sequenziell ohne Zählung. | Nicht überlappende Intervalle `[Start, Ende)`, Pagination **innerhalb jedes Intervalls**, globale Begrenzung. Drei Kryptojahre enthalten über 1.000 Tageszeilen. Ganze Einzeljahre wären einfacher, erzeugen aber viele Anfragen bei langen Reihen. |
| **O4: Statische Kursdateien** | **Tragfähig und größter struktureller Gewinn für kalte Aufrufe.** Eine komprimierte Datei ersetzt viele DB-Roundtrips; vorhandene gemeinsame Volume-Struktur passt. | Veröffentlichungs-, Frische- und Korrekturvertrag fehlen noch. Details unten. |
| **O5: IndexedDB / Delta** | Sinnvoll für wiederholte Aufrufe und Navigation, **kein wesentlicher Gewinn für einen bisher unbekannten Ticker**. | Asynchroner Cache mit Größenbudget/LRU, Fehlerfallback und Datenrevision. `letztes Datum` allein reicht nicht. Reines `date=gt.…` verpasst Intraday-Änderungen, ältere Korrekturen und Löschungen. |
| **O6: Schrittweise Anzeige** | Sinnvoll für wahrgenommene Geschwindigkeit, aber fachlich empfindlich. | Vorläufige kurze Stichprobe ausdrücklich kennzeichnen. Saison-Score erst mit vollständiger erforderlicher Historie. Besser zunächst sichtbare Charts priorisieren und teure Folgeauswertungen später rechnen, ohne die Stichprobe zu ändern. |
| **O7: Vorabladen** | Zuletzt, begrenzter Nutzen. Kann auf Mobile Datenvolumen und auf Supabase Last erhöhen. | Erst bei konkretem Auswahlinteresse, kurze Verzögerung, kleines Budget; laufende Ladung teilen. Fokus allein auf das Suchfeld rechtfertigt keine Historienladung beliebter Ticker. |
| **O8: Globale Anfragekoordination** | Gehört praktisch zu O2, sollte ausdrücklich im Plan stehen. | Ein gemeinsamer Pool für Ticker, Jahresblöcke, Radar und Vorabladen; sonst werden aus drei Watchlist-Tickern mit sechs Teilabrufen 18 parallele Anfragen. Veraltete Arbeit abbrechen, sobald kein Verbraucher sie mehr benötigt. |
| **O9: Rechen-/Renderkosten reduzieren** | Nach Messung gezielt angehen. | Erstes sichtbares Chart vor synchronen Vollauswertungen; Watchlist-Karten einzeln veröffentlichen. Wiederholtes `concat` großer Blöcke vermeiden. Worker erst bei nachgewiesener Main-Thread-Last. |

### O1: kleinster sicherer Schritt

PostgREST liefert auch ohne Zählung einen Range-Header, beispielsweise `0-999/*`. Das ist dokumentiertes Verhalten. [`Pagination and Count`](https://docs.postgrest.org/en/stable/references/api/pagination_count.html)

Die heutige Verzweigung in [`app.js:789`](/C:/dev/SeasonalEdge/landing/js/app.js:789) nimmt den Header entgegen, liest `*` als `NaN` und überspringt anschließend die Fortsetzung. Die Gegenprobe mit dem **echten Produktionslader** und 1.500 simulierten Sollzeilen lieferte **1.000 Zeilen nach einer Anfrage**.

O1 muss daher zusammen ändern:

1. `count=exact` entfernen.
2. Nach jedem vollständigen 1.000er-Block weiterladen, unabhängig von einer Gesamtzahl.
3. Kürzeren beziehungsweise leeren Schlussblock als Ende behandeln.
4. Fehler weiterhin ablehnen; Teilhistorien weder zurückgeben noch cachen.

Bei exakt 1.000, 2.000 usw. Zeilen entsteht eine zusätzliche leere Schlussanfrage. Das ist ein vertretbarer Preis für den kleinen ersten Schritt. Keyset-Pagination kann anschließend mit O2 vereinheitlicht werden.

### O4: Datenmenge und Veröffentlichungsvertrag

**Datenmenge:** 370 Ticker sind am lokalen `tickers.json` bestätigt; eine aktuelle Gesamtzeilenzahl ist hier nicht belegt. Die vier Beispielreihen dürfen nicht ungeprüft auf alle Ticker hochgerechnet werden.

Mit den **85 Byte je Zeile aus dem Auftrag**, vor `open` und vor Komprimierung, ergeben sich folgende reine Planungsszenarien:

| Angenommener Durchschnitt über 370 Ticker | Gesamtzeilen | Objekt-JSON bei 85 B/Zeile |
|---|---:|---:|
| 7.300 Zeilen/Ticker | 2,701 Mio. | ca. 230 MB |
| 10.000 Zeilen/Ticker | 3,700 Mio. | ca. 315 MB |

Spaltenarrays sparen wiederholte Feldnamen; `open` erhöht den Inhalt. **Die tatsächliche Größe und gzip-Wirkung müssen aus dem Export gemessen werden.** Speicherplanung umfasst veröffentlichte Daten, laufende Exportgeneration, gegebenenfalls vorkomprimierte Dateien und begrenzte alte Versionen.

Für den Pilot würde ich eine vollständige Datei je Ticker mit mindestens

`date, open, close, log_return, tdom, tdoy`

verwenden. Kein Rundungsverlust, kein Ersetzen fehlender Werte durch nullartige Zahlen, keine neue Berechnung der Spalten beim Export.

Der notwendige Vertrag:

- **Quelle sind die gespeicherten DB-Zeilen.** Nightly-/Yahoo-DataFrames sind kein Ersatz: [`upsert_prices`](/C:/dev/SeasonalEdge/shared/supabase_client.py:93) erhält bei fehlenden Spalten vorhandene Werte; die gespeicherten Daten können deshalb vom Download abweichen.
- **Version und Abdeckung gehören in die Veröffentlichung:** Schema, Ticker, Inhaltsrevision, erste/letzte Sitzung, Zeilenzahl, Datenstand und Zeitpunkt der letzten erfolgreichen Aktualisierung. Veröffentlichungszeit allein beweist keine Kursfrische.
- **Nightly veröffentlicht nach den Kursänderungen einschließlich späterer Reparaturen.** Phase D aktualisiert beispielsweise `log_return` nachträglich ([`:402`](/C:/dev/SeasonalEdge/scripts/nightly_refresh.py:402)).
- **Intraday muss enthalten sein.** Der aktuelle Schreiber verändert die letzten fünf Tage ([`:118`](/C:/dev/SeasonalEdge/scripts/intraday_refresh.py:118)). Nur tägliche Dateien würden gegenüber dem heutigen Browserpfad Frische verlieren.
- **Export und Schreiber brauchen eine nachgewiesene Konsistenzregel.** Eine Datei darf keine Mischung verschiedener Schreibstände enthalten. Dafür entweder alle betroffenen Schreiber/Exporter unter derselben Sperre koordinieren oder eine konsistente DB-Lesegeneration vorsehen. Ein Metadatenvergleich nur über das letzte Datum genügt nicht.
- **Atomar veröffentlichen:** vollständig schreiben, prüfen, anschließend ersetzen. Bei mehreren zusammengehörigen Dateien zuerst die versionierten Dateien, zuletzt den Verweis darauf veröffentlichen. Fehler behalten die letzte gültige Version, verlängern aber deren Frische nicht.
- **Frische tickerabhängig prüfen:** Börsenkalender und Marktöffnung berücksichtigen; am Wochenende ist ein Freitagskurs bei einer Aktie nicht automatisch veraltet, bei Krypto gelten andere Erwartungen. Intraday-Aktualität braucht einen Zeitstempel zusätzlich zum Sitzungsdatum.
- **Fehlende, beschädigte oder zu alte Datei:** einmal auf den gemeinsamen DB-Lader zurückfallen. Scheitert auch dieser, einen Ladefehler oder ausdrücklich veralteten Stand anzeigen.
- **Alle Korrekturwege einbeziehen:** Onboarding, Backfills, Gap-Fill, Nummernkorrekturen und Löschungen. Diese Änderungen benötigen neue Revisionen, auch wenn das letzte Datum gleich bleibt.

Die Betriebsgrundlage existiert bereits: [`docker-compose.yml:24`](/C:/dev/SeasonalEdge/docker-compose.yml:24) lässt den App-Container `landing/data` schreiben; nginx liest denselben Bestand. [`write_json_atomic`](/C:/dev/SeasonalEdge/shared/atomic_json.py:26) enthält Flush, fsync, atomaren Ersatz und Rechtebehandlung. Für neue Kursdateien müssen HTTP-Lesbarkeit und erwartete Rechte dennoch geprüft werden.

**Caching muss für den neuen Pfad ausdrücklich konfiguriert werden.** Die bestehende JSON-Regel setzt **`max-age=86400`** ([`nginx.conf:221`](/C:/dev/SeasonalEdge/deploy/nginx.conf:221)). Eine gewöhnliche Prefix-Regel kann von dieser Regex-Regel überholt werden. [`nginx: location`](https://nginx.org/en/docs/http/ngx_http_core_module.html#location)

Für den Pilot: eigener passender Pfad, gzip und revalidierbare Antworten mit ETag/`no-cache`. `no-cache` erlaubt Speicherung, verlangt aber Validierung vor Wiederverwendung; es erzeugt keine frischen Daten, wenn der Export stehenbleibt. [`MDN: Cache-Control`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cache-Control)

Ein späterer Ausbau kann unveränderliche Historienversionen mit einem kleinen aktuellen Datenende verbinden. Das spart wiederholte Vollübertragungen, benötigt aber einen zusätzlichen Versions- und Zusammenführungsvertrag.

### O5: Ist localStorage heute wirkungslos oder schädlich?

**Teilweise schädlich; ein genereller Ausfall für ^DJI ist nicht bewiesen.**

[`SA.cache.set`](/C:/dev/SeasonalEdge/landing/js/app.js:48) fängt Fehler ab, löscht daraufhin **alle** `sa-cache-*`-Einträge und versucht das Schreiben erneut. Auch ein dauerhaft nicht speicherbarer großer Eintrag entfernt damit vorher funktionierende kleine Einträge. In der Gegenprobe blieben nach dem Fehlschlag nur die Nicht-Cache-Präferenzen erhalten.

Zusätzlich:

- JSON-Serialisierung, Lesen und Parsen erfolgen synchron.
- Vollhistorie und Zeitfenster belegen getrennte Einträge mit überlappenden Daten.
- Alte Einträge werden beim Zugriff entwertet; es gibt keine allgemeine Größenverwaltung.
- Der Aufrufer ignoriert den Rückgabewert `false`.
- Browserquota und UTF-8-Übertragungsgröße sind nicht dieselbe Messgröße. Aus „2,8 MB JSON“ folgt deshalb weder sicherer Erfolg noch sicherer Fehlschlag. Web Storage hat typischerweise 5 MiB localStorage je Ursprung; andere Speicherverfahren haben andere Quoten und können ebenfalls ausfallen. [`MDN: Speicherquoten`](https://developer.mozilla.org/en-US/docs/Web/API/Storage_API/Storage_quotas_and_eviction_criteria)

Vor IndexedDB würde ich bereits das globale Löschen durch begrenzte Verdrängung ersetzen und große Ergebnisse im Memory weiterverwenden. Bei O4 kann der normale HTTP-Cache schon einen großen Teil des Wiederholungsnutzens liefern.

## Empfohlene Reihenfolge mit Abnahmekriterien

| Schritt | Umsetzung | Abnahme |
|---|---|---|
| **0. Messbasis** | Seiten, Ticker, Datenrevision, Browser und Netzwerkprofil festlegen. | Vergleichbare Vorherwerte für erstes Chart, vollständige Anzeige, Anfragen, Bytes, Fehler und Rechenzeit. |
| **1. O1** | Gemeinsamen F-Lader ohne Zählung korrekt terminieren lassen. | Exakte Sollzeilen für 0/999/1000/1001/2000 Zeilen; Header mit `*` und fehlender Header; Folgeblockfehler lehnt ab, erzeugt keinen Cache. Kein `count=exact` auf diesem Pfad. |
| **2. O2 + O8** | F, V und zehn lokale Lader vereinheitlichen; Feld-/Abdeckungsvertrag, laufende Promises, globaler Pool. | Alle Tabellenzeilen migriert; unveränderte Filter und benötigte Vorlaufdaten. Identische gleichzeitige Anforderungen teilen eine Ladung. Score/Radar verwenden passende vorhandene Daten. `open` bleibt verfügbar. |
| **3. Browsercache begrenzen** | Globalen Purge entfernen; Cache-Version, Größenbudget und begrenzter Memory-Cache. | Nicht speicherbares ^DJI-Ergebnis entfernt keine anderen Ticker; Anzeige bleibt funktionsfähig. Alte Formate gelten nach Migration nicht als Treffer. |
| **4. O4-Pilot** | SPY, ^GDAXI, ^DJI, SAP.DE sowie ein Krypto-/Forex-Ticker; zunächst Shadow-Vergleich, danach ausgewählte Seiten. | Jede Zeile und jedes Feld stimmt mit dem festgelegten DB-Stand überein. Intraday, gleiches Datum mit verändertem Close, ältere Korrektur, Löschung, Exportausfall und fehlende Datei funktionieren nach Vertrag. HTTP 200/304, gzip und Cache-Header geprüft. |
| **5. O4-Rollout** | Alle 370 Ticker; Änderungen aller Schreiber berücksichtigen. | Vollständiges Exportmanifest, erkennbare Teilfehler, begrenzter Betriebsaufwand. Für lange kalte Historien vorab gesetztes Leistungsziel, beispielsweise mindestens 50 % geringerer p95 der Ladezeit im festgelegten Netzwerkprofil. |
| **6. O6/O9, danach ggf. O5** | Sichtbare Inhalte priorisieren; IndexedDB nur bei verbleibendem Wiederholungsproblem. | Erstes Chart schneller; endgültige Stichproben und Kennzahlen unverändert. Keine unmarkierten vorläufigen Scores. |
| **7. O3/O7 nach Bedarf** | Parallelisierung nur für verbleibenden DB-Fallback; begrenztes Vorabladen. | Messbarer Zusatzgewinn ohne erhöhte Fehlerquote oder unvertretbare Mehrlast. Globale Parallelitätsgrenze wird eingehalten. |

**Messverfahren:** Ein reproduzierbares Skript für Transport und Datenvergleich plus eine Browser-Probe der **echten Seiten und echten Auswahlhandler**.

- Pflichtmatrix: SPY, ^GDAXI, ^DJI, SAP.DE, BTC-USD und ein kurzer/neuer Ticker; Dashboard, Dekadenzyklus, Jahreszyklus, Saison-Score, Overnight und Watchlist. Für den Rollout alle migrierten Seiten funktional prüfen.
- Getrennte Zustände: vollständig kalt; Rückwechsel im selben Tab; Navigation auf eine zweite Seite; Wiederaufruf nach Datenänderung.
- Vorher/nachher abwechselnd, gleiche Stichprobe und Revision, beispielsweise zehn gültige Wiederholungen je Messzelle. Median, p95, Fehler und Ausreißer ausweisen.
- Transport: Anfragen inklusive Retries, TTFB, Gesamtzeit, Übertragungsbytes, dekodierte Größe, Zeilenzahl und Inhaltsvergleich.
- Browser: Auswahl → erstes tatsächlich fertig gerendertes Chart; zusätzlich Score/Radar und gesamte Ansicht. JSON-Parsing, Cachezugriff, Berechnung und Renderzeit getrennt erfassen.
- Desktop und begrenztes Mobile-Profil; auch A → B → A während laufender Abrufe testen.
- Ein 100-Byte-Fehlerkörper ist **kein schneller Messlauf**. Nur gültige, vollständige Daten zählen als erfolgreiche Wiederholung.

Die Transportprobe allein beantwortet „Zeit bis erstes Chart“ nicht. CORS-/Verbindungsaufbau, tatsächliche Komprimierung, eventuell vorgeschaltete CDN-Regeln und Main-Thread-Kosten müssen im Browser mitgemessen werden.

## Befunde

1. **Hoch — O1 wäre als bloße Headeränderung eine Datenkürzung.**  
   [`app.js:789`](/C:/dev/SeasonalEdge/landing/js/app.js:789) behandelt einen vorhandenen Range-Header mit unbekannter Gesamtzahl falsch. Produktionscode-Gegenprobe: **1.000 statt 1.500 Sollzeilen**.

2. **Hoch — Zehn lokale Lader haben die Fehlerbehandlung des gemeinsamen Laders nicht.**  
   Sie prüfen weder `r.ok` noch zuverlässig die Arrayform, bevor sie Antworten anhängen. Gegenprobe am echten [`Overnight-Lader`](/C:/dev/SeasonalEdge/landing/pages/overnight.html:278): erster Block erfolgreich, zweiter HTTP 500 → Promise **erfüllt**, Ergebnis mit **1.000 Kurszeilen plus Fehlerobjekt**. O2 muss diese Pfade ausdrücklich ablösen.

3. **Hoch — Dashboard-Overnight ist heute auf eine einzelne Antwort begrenzt.**  
   [`dashboard.html:2197`](/C:/dev/SeasonalEdge/landing/pages/dashboard.html:2197) fragt mehrere Jahre aufsteigend ab, paginiert aber nicht. Bei einer 1.000-Zeilen-Grenze fehlt das jüngere Datenende. Diese bestehende Kürzung darf nicht als Sollreferenz für den neuen Lader dienen.

4. **Hoch — Datenstand „letztes Datum“ und append-only Delta reichen nicht.**  
   Intraday verändert vorhandene Tage; Nightly repariert zusätzlich Renditen. Historische Kalender-/Kurskorrekturen können weit davor liegen. O4/O5 brauchen Inhaltsrevisionen und Korrekturinvalidation.

5. **Mittel — Die Dopplung umfasst mehr als zwei Lader.**  
   Dashboard: 30-Jahre-Ladung, Vollhistorie, Radarfenster und separater Open-Abruf. Saison-Score-Seite: Zeitraumladung plus Vollhistorie. Die Radar-Nachladung wiederholt bei kurzen Reihen auch dann Daten, wenn die erste Ladung bereits deren komplette vorhandene Historie enthält.

6. **Mittel — Laufende identische Abrufe werden nicht geteilt.**  
   Produktionscode-Gegenprobe: zwei gleichzeitige identische F-Aufrufe → **zwei Netzwerkaufrufe**. Die Caches greifen erst nach erfolgreichem Abschluss.

7. **Mittel — Cachefehler können andere Cachetreffer zerstören.**  
   Quota-Gegenprobe bestätigt den globalen Purge. Zusätzlich umgehen Dekaden-, Earnings- und Dividenden-Memory-Caches die 15-Minuten-Frischeprüfung dauerhaft innerhalb des offenen Tabs.

8. **Mittel — O3 braucht Pagination innerhalb der Datumsbereiche.**  
   Insbesondere drei Kryptojahre passen nicht in 1.000 Zeilen. Außerdem müssen parallele Bereiche dieselbe Datenrevision darstellen; ein gemeinsames Enddatum verhindert Änderungen bereits vorhandener Tage nicht.

9. **Mittel — Der heutige statische JSON-Pfad ist nicht für Intraday-Frische konfiguriert.**  
   Die getrackte nginx-Regel setzt 24 Stunden Cachezeit. Ein neuer Kursdateipfad braucht eine wirksam ausgewählte eigene Regel und HTTP-Abnahme; die aktive Live-Konfiguration konnte hier nicht geprüft werden.

10. **Offen — Infrastruktur und Menge müssen gemessen werden.**  
    Aktuelle Gesamtzeilenzahl, tatsächliche Index-/RLS-Ausführungskosten, Live-Komprimierung, CDN-Verhalten, Browserquota und Mobile-Renderzeit sind nicht belegt. Supabase-Kosten sollten anhand übertragenem Volumen und DB-Last bewertet werden: Parallelisierung verkürzt gegebenenfalls Wartezeit, beseitigt diese Kosten aber nicht.
