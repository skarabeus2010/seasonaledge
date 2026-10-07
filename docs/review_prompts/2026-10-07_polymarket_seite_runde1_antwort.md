# Codex-Antwort: Review /polymarket, Runde 1 (gpt-6-astra, Websuche)

> Stichproben am Code bestätigt (07.10.2026): #1 fehlender Preis = 0, #4 `set -uo pipefail` ohne `-e`, #7 Gesamt-Brier ohne Filter auf Zeitpunkte vor der Auflösung, #8 ungefilterte Seriennamen in ApexCharts, #9 „möglicher Long-Trade" (DE+EN), #11 `or` verwirft Nullpreis.
codex
**Die Seite ist in dieser Runde nicht freigabefähig.** Es gibt hohe Befunde bei Datenzuständen, Fehlerweitergabe, Methodik und XSS. Die Erweiterungen sollten auf einer korrigierten Datenbasis aufbauen.

Geprüft wurden die genannten Dateien einschließlich der Python-Berechnung im Newsletter und der Health-Checks. Isolierte Python-/Node-Prüfungen bestätigten mehrere Fehler. Die [DE-Seite](https://seasonalpha.ai/polymarket) und [EN-Seite](https://seasonalpha.ai/en/polymarket) waren als Webabruf verfügbar; dieser lieferte teilweise gecachte Inhalte. Eine gerenderte Browser-/Mobile-Prüfung war technisch nicht möglich. Aktuelle Produktionskurse und tatsächliche Jobzustände sind deshalb **nicht verifiziert**. Keine Dateien geändert.

**Teil A — Review**

**1. Hoch — Fehlende Preise erscheinen als 0 %, teilweise grün.**  
Fundstellen: [polymarket.js:95](C:/dev/Seasonaledge/landing/js/polymarket.js:95), [polymarket.js:258](C:/dev/Seasonaledge/landing/js/polymarket.js:258), [polymarket.js:489](C:/dev/Seasonaledge/landing/js/polymarket.js:489), [polymarket.js:559](C:/dev/Seasonaledge/landing/js/polymarket.js:559).

Fehlender Snapshot und echter Nullpreis werden gleichbehandelt. Der Test mit leerem Katalog erzeugte vier grüne Risikokacheln mit `0.0%`; fehlende Fed-Preise ergaben einen Erwartungswert von null. In der Divergenztabelle entsteht dadurch ein erfundener Abstand zur Historie.

**Änderung:** Fehlend, ungültig, veraltet und echte Null ausdrücklich unterscheiden. Ohne gültigen Preis „Keine Daten“ anzeigen, neutral einfärben und keine Divergenz beziehungsweise Fed-Aggregation berechnen.

**2. Hoch — Kein belastbarer Aktualitätsvertrag; „Live“ ist nicht gedeckt.**  
Fundstellen: [polymarket.js:48](C:/dev/Seasonaledge/landing/js/polymarket.js:48), [polymarket.html:461](C:/dev/Seasonaledge/landing/pages/polymarket.html:461), [polymarket.html:268](C:/dev/Seasonaledge/landing/pages/polymarket.html:268), [polymarket_refresh.py:68](C:/dev/Seasonaledge/scripts/polymarket_refresh.py:68).

Die Oberfläche prüft weder das Alter des Marktpreises noch das des Krypto-Schlusskurses. `loadLatestPrices()` lädt global nur `5 × Marktanzahl` Zeilen: Häufig aktualisierte Märkte können selten aktualisierte vollständig verdrängen. Umgekehrt kann eine vorhandene alte Zeile unbegrenzt als aktuell erscheinen. Der Snapshot-Zeitpunkt ist der Abrufzeitpunkt, kein nachgewiesener Zeitpunkt einer neuen Quote.

Die tatsächliche Konfiguration sieht tägliche Snapshots, zusätzliche stündliche Läufe im FOMC-Fenster und montäglichen Backfill vor. „Stündlich / Backfill alle 24h“ ist falsch.

**Änderung:** Neueste Zeile **pro Markt** serverseitig bestimmen. Je Preis Quellzeit, Abrufzeit, Preisart und Alter anzeigen. Vorschlag: tägliche Daten nach 30 Stunden als veraltet behandeln; im stündlichen Modus nach 90 Minuten. Alte Werte dürfen mit Datum sichtbar bleiben, aber keine aktuellen Bewertungen erzeugen. Die Grenzwerte müssen aus der vorgesehenen Kadenz stammen.

**3. Hoch — Aufgelöste, pausierte und verschwundene Märkte werden nicht zuverlässig ausgesondert.**  
Fundstellen: [polymarket_discover.py:199](C:/dev/Seasonaledge/scripts/polymarket_discover.py:199), [polymarket_discover.py:221](C:/dev/Seasonaledge/scripts/polymarket_discover.py:221), [polymarket_refresh.py:63](C:/dev/Seasonaledge/scripts/polymarket_refresh.py:63), [polymarket_data.py:206](C:/dev/Seasonaledge/shared/polymarket_data.py:206).

Der Katalogabgleich schreibt stets `active=True`, obwohl `closed` und `accepting_orders` vorliegen. API-seitig verschwundene Märkte werden lediglich übersprungen; ihr alter Datenbankstatus bleibt bestehen. Der Refresh liest auch inaktive Katalogeinträge und kontrolliert den Marktstatus nicht. Die vorgesehenen Felder `resolution` und `resolved_at` werden in diesem Pfad nicht gepflegt.

**Änderung:** Explizite Zustände `open`, `paused`, `closed`, `resolved`, `unavailable`; Metadaten regelmäßig aktualisieren. Bei API-Ausfall den Status als unbekannt kennzeichnen, nicht vorschnell aufgelöst setzen. Aufgelöste Märkte ins Archiv übernehmen und aus aktuellen Aggregaten entfernen.

**4. Hoch — Gescheiterte Workflows können erfolgreich enden.**  
Fundstellen: [polymarket_daily.yml:41](C:/dev/Seasonaledge/.github/workflows/polymarket_daily.yml:41), [polymarket_daily.yml:61](C:/dev/Seasonaledge/.github/workflows/polymarket_daily.yml:61), [brier_compute.yml:45](C:/dev/Seasonaledge/.github/workflows/brier_compute.yml:45), [brier_compute.yml:74](C:/dev/Seasonaledge/.github/workflows/brier_compute.yml:74).

`set -uo pipefail` setzt **kein** `errexit`. Eine fehlgeschlagene Pipeline liefert zwar einen Fehlerstatus, das Skript läuft aber weiter und endet mit einem erfolgreichen `echo`. Nach gescheitertem Scrape kann die Brier-Berechnung alte Daten neu auswerten.

**Änderung:** Jeden Verarbeitungsschritt explizit auf Erfolg prüfen und bei Fehler abbrechen; alternativ korrekt eingesetztes `set -euo pipefail`. Ein Fehlerprotokoll muss trotzdem geschrieben werden. Mit absichtlich fehlschlagendem Unterprozess den Workflow-Endstatus prüfen.

Positiv: Der manuelle Intraday-Workflow reicht den Service-Fehlerstatus bereits ausdrücklich weiter.

**5. Hoch — Teilfehler und leere Ergebnisse bleiben in Skripten und Health-Checks grün.**  
Fundstellen: [polymarket_refresh.py:185](C:/dev/Seasonaledge/scripts/polymarket_refresh.py:185), [polymarket_backfill.py:102](C:/dev/Seasonaledge/scripts/polymarket_backfill.py:102), [polymarket_scrape_resolved.py:332](C:/dev/Seasonaledge/scripts/polymarket_scrape_resolved.py:332), [compute_brier_stats.py:246](C:/dev/Seasonaledge/scripts/compute_brier_stats.py:246), [daily_health_check.py:139](C:/dev/Seasonaledge/scripts/daily_health_check.py:139), [daily_health_check.py:444](C:/dev/Seasonaledge/scripts/daily_health_check.py:444).

Ein erfolgreicher Snapshot genügt für Exit-Code 0 und einen grünen Intraday-Check. Der allgemeine Preischeck betrachtet nur die allerneueste Zeile, nicht die Abdeckung des Katalogs. Daily schreibt hier keinen eigenen `refresh_log`-Eintrag. API-Fehler werden beim Backfill/Scraper häufig zu leeren Listen; die Programme enden normal. Brier ohne Märkte oder Forecasts beendet sich ebenfalls erfolgreich und lässt eine vorhandene Datei bestehen. Der Brier-Health-Check prüft nur deren Änderungsdatum.

**Änderung:** Erwartete, erfolgreiche, fehlende und bewusst ausgeschlossene Märkte getrennt zählen. Unerwartete Ausfälle müssen einen Fehler-/Teilfehlerstatus erzeugen. Jeden Job protokollieren; Frische und Vollständigkeit pro Markt prüfen. Brier zusätzlich anhand von Daten-Wasserstand, Stichprobenumfang und letzter erfolgreicher Erfassung überwachen.

**6. Hoch — Der Krypto-Vergleich setzt unterschiedliche Ereignisse gleich.**  
Fundstellen: [polymarket.html:176](C:/dev/Seasonaledge/landing/pages/polymarket.html:176), [polymarket.js:413](C:/dev/Seasonaledge/landing/js/polymarket.js:413), [polymarket.js:485](C:/dev/Seasonaledge/landing/js/polymarket.js:485), [polymarket_markets.yaml:152](C:/dev/Seasonaledge/shared/polymarket_markets.yaml:152).

Berechnet wird die historische **Jahresendrendite**. Die Erklärung wechselt dagegen zwischen „bis Jahresende erreichen“ und „zum Jahresende darüber schließen“. Das sind unterschiedliche Ereignisse. Die öffentlich dokumentierte Bitcoin-Leiter verwendet ein zwischenzeitliches Erreichen anhand von Binance-Minutenhochs. Die genaue Zuordnung sämtlicher gespeicherter Condition-IDs konnte ich beim API-Abruf nicht verifizieren; gerade deshalb fehlt hier der erforderliche Regelbeleg. [Polymarket-Auflösungsregel](https://polymarket.com/event/what-price-will-bitcoin-hit-before-2027/will-bitcoin-reach-95000-by-december-31-2026-from-june-8)

**Änderung:** Pro Kontrakt Ereignistyp, Beobachtungsfenster, Preisquelle, Zeitzone und Vergleichsoperator speichern. Jahresend-Prior nur mit passenden Schlusskurskontrakten vergleichen. Für Berührungsereignisse braucht es passende Pfaddaten; bereits erreichte Schwellen sind gesondert zu behandeln. Bis dahin die Divergenzbewertung aussetzen.

**7. Hoch — Brier-Auflösung und Prognosezeitpunkt sind nicht sauber definiert.**  
Fundstellen: [polymarket_scrape_resolved.py:97](C:/dev/Seasonaledge/scripts/polymarket_scrape_resolved.py:97), [polymarket_scrape_resolved.py:199](C:/dev/Seasonaledge/scripts/polymarket_scrape_resolved.py:199), [polymarket_scrape_resolved.py:263](C:/dev/Seasonaledge/scripts/polymarket_scrape_resolved.py:263), [compute_brier_stats.py:147](C:/dev/Seasonaledge/scripts/compute_brier_stats.py:147).

`resolution_date` wird aus dem geplanten `end_date` übernommen. „Geschlossen“ plus Preis ≥99 % reicht als Auflösungsnachweis. Frühzeitige Auflösung, verzögerte Entscheidung und strittige Ergebnisse werden damit nicht sauber abgebildet.

Außerdem nimmt `flatten_forecasts()` alle Zeitpunkte auf. Nur die Zeit-Buckets filtern nachträgliche Beobachtungen heraus; Gesamt-Brier, Kategorien und Kalibrierung tun das nicht. Im synthetischen Test sank der Gesamt-Brier durch einen nachträglichen sicheren Preis von **0,25 auf 0,125**, während der Zeit-Bucket bei 0,25 blieb.

**Änderung:** Verifiziertes Ergebnis und tatsächliche Auflösung getrennt von Ereignis-/Handelsende speichern. Forecasts zentral vor allen Auswertungen filtern. Für Prognosegüte außerdem verhindern, dass bereits bekannte Ereignisausgänge während einer späteren formalen Abwicklung als Vorhersagen zählen.

**8. Hoch — XSS-Schutz endet vor ApexCharts.**  
Fundstellen: [polymarket.js:356](C:/dev/Seasonaledge/landing/js/polymarket.js:356), [polymarket.html:381](C:/dev/Seasonaledge/landing/pages/polymarket.html:381), [polymarket.html:667](C:/dev/Seasonaledge/landing/pages/polymarket.html:667).

Die Markttabelle maskiert externe Texte korrekt. Historien-Seriennamen übernehmen jedoch `question` ungefiltert. ApexCharts 4.7.0 schreibt Legendennamen über `innerHTML`; Kürzen auf 40 Zeichen verhindert HTML-Injektion nicht. Weitere ungefilterte HTML-Einfügungen betreffen Checkbox-Slugs/-IDs und Brier-Kategorien, wenn auch mit derzeit stärker kontrollierten Datenquellen. [ApexCharts-Quellcode](https://raw.githubusercontent.com/apexcharts/apexcharts.js/v4.7.0/src/modules/legend/Legend.js)

**Änderung:** Checkboxen mit DOM-Methoden und `textContent` bauen. Alle HTML-Ausgaben maskieren; externe Chartnamen an sämtlichen Legenden-/Tooltip-Ausgaben absichern. Bibliotheksversion festlegen und einen lokalen Test mit manipuliertem Marktnamen ergänzen.

**9. Hoch — Handlungsnahe Sprache ohne spezifischen Deutschland-Hinweis.**  
Fundstellen: [polymarket.html:195](C:/dev/Seasonaledge/landing/pages/polymarket.html:195), [polymarket.html:125](C:/dev/Seasonaledge/landing/pages/polymarket.html:125), [en.json:688](C:/dev/Seasonaledge/landing/i18n/en.json:688).

„Möglicher Long-Trade“ verbindet den methodisch problematischen Abstand mit einer Handlung. Im geprüften Seiten-Code fand ich **keinen Affiliate-/Referral-Link, Handelsbutton oder Kontoeröffnungsaufruf**. Der allgemeine Footer-Risikohinweis erklärt jedoch die besondere Rechtslage nicht.

Polymarket untersagt Handel aus Deutschland, lässt Marktdaten aber zugänglich. Die GGL bezeichnet Gesellschaftswetten einschließlich Teilnahme und Bewerbung als illegal beziehungsweise strafbar. Das ist keine abschließende rechtliche Einordnung jedes einzelnen Finanzkontrakts oder dieser Datenseite. [Polymarket](https://help.polymarket.com/en/articles/13364163-geographic-restrictions), [GGL](https://www.gluecksspiel-behoerde.de/de/news/ggl-warnt-vor-teilnahme-an-illegalen-gesellschaftswetten)

**Änderung:** Handelsnahe Formulierungen entfernen. Gut sichtbar, auch auf EN für deutsche Leser:

> SeasonAlpha zeigt öffentliche Marktdaten zu Informationszwecken und bietet oder vermittelt keine Wetten. Polymarket untersagt den Handel aus Deutschland. Die GGL stuft Gesellschaftswetten als illegal ein und warnt vor strafbarer Teilnahme. Angezeigte Preise sind keine Teilnahmeempfehlung.

**10. Mittel — Python und JS sind keine identischen Zwillinge.**  
Fundstellen: [polymarket.js:415](C:/dev/Seasonaledge/landing/js/polymarket.js:415), [polymarket.js:436](C:/dev/Seasonaledge/landing/js/polymarket.js:436), [weekly_report.py:299](C:/dev/Seasonaledge/shared/weekly_report.py:299), [weekly_report.py:413](C:/dev/Seasonaledge/shared/weekly_report.py:413), [supabase_client.py:615](C:/dev/Seasonaledge/shared/supabase_client.py:615).

Die Grundformeln stimmen überein: Trefferanteil und `100 × (Prior − Marktpreis)`. Unterschiede:

- JS mischt UTC-Datumsstrings und lokale Kalenderdaten. Derselbe Test ergab 50,0 % Rendite in Berlin, 36,4 % in New York.
- Am 29. Februar verwendet Python für Nichtschaltjahre den 28. Februar; JS rollt auf den 1. März. Test: 200 % gegenüber 50 % Rendite.
- Python verlangt mindestens drei Jahres-Samples; JS bewertet bereits eines.
- Python lädt jüngste Marktpreise nur innerhalb von sieben Tagen; JS ohne Altersgrenze und mit anderem Mengenlimit.

**Änderung:** Gemeinsamer fachlicher Vertrag für Stichtag, UTC-Kalenderdatum, Schalttage, gültige Samples und Preisfrische; gemeinsame Testfälle in beiden Sprachen. Brier selbst hat keinen zweiten JS-Rechenkern: Die Oberfläche zeigt Python-Aggregate an.

**11. Mittel — Nullpreise gehen verloren; Preisarten und Qualitätsgrenzen fehlen.**  
Fundstellen: [polymarket_data.py:315](C:/dev/Seasonaledge/shared/polymarket_data.py:315), [polymarket_data.py:248](C:/dev/Seasonaledge/shared/polymarket_data.py:248), [polymarket_refresh.py:45](C:/dev/Seasonaledge/scripts/polymarket_refresh.py:45), [create_polymarket_tables.sql:38](C:/dev/Seasonaledge/scripts/create_polymarket_tables.sql:38).

`pt.get("p") or pt.get("price")` verwirft einen numerischen Nullpreis — im Test bestätigt. Snapshots mischen Mittelkurs, einseitigen Bid/Ask und letzten Trade ohne Kennzeichnung. Ein gekreuztes Orderbuch mit Bid 0,8 und Ask 0,2 wurde als Preis 0,5 mit negativem Spread akzeptiert. Gamma-Snapshots werden als `source="clob"` gespeichert. Die Live-Preistabelle hat keinen Wertebereichs-Check.

**Änderung:** Auf `None` statt Wahrheit prüfen; endliche Werte und `0 ≤ Bid ≤ Ask ≤ 1` validieren. `price_kind`, Bid, Ask, Spread und Quellzeit speichern. Einseitige beziehungsweise breite Quotes sichtbar markieren und von Bewertungen ausschließen. CLOB-Historie nicht ohne belegte Semantik pauschal als historische Mittelkursreihe bezeichnen.

**12. Mittel — Die Kalibrierungsstichprobe rechtfertigt keine allgemeine Qualitätsaussage.**  
Fundstellen: [polymarket_scrape_resolved.py:72](C:/dev/Seasonaledge/scripts/polymarket_scrape_resolved.py:72), [polymarket_scrape_resolved.py:236](C:/dev/Seasonaledge/scripts/polymarket_scrape_resolved.py:236), [compute_brier_stats.py:174](C:/dev/Seasonaledge/scripts/compute_brier_stats.py:174), [compute_brier_stats.py:192](C:/dev/Seasonaledge/scripts/compute_brier_stats.py:192), [polymarket.html:227](C:/dev/Seasonaledge/landing/pages/polymarket.html:227).

Die quadratische Brier-Formel ist korrekt. Aber:

- maximal 500 Events je Tag, ausgewählte Kategorien, Mindest-Endvolumen und verfügbare Historie ergeben eine selektive Stichprobe;
- lange Märkte erhalten mehr Gewicht, weil jeder Markttag zählt;
- mehrere abhängige Kontrakte desselben Events zählen separat;
- angezeigte Marktanzahlen umfassen auch Märkte ohne verwertbare Forecasts;
- die Basisrate ist snapshotgewichtet, obwohl die UI sie als Anteil der Auflösungen bezeichnet.

„0,15–0,20 = gut kalibriert“ ist keine allgemeingültige Skala. Brier misst mehr als Kalibrierung. Auch „Polymarket schlägt die Basisrate deutlich“ ist statisch eingebaut; ein flacher Zeitverlauf beweist kein frühes Wissen über den Ausgang.

**Änderung:** Stichprobenauswahl und Ausfälle offenlegen; einen Forecast je Markt und Horizont verwenden, Ereignisabhängigkeit berücksichtigen und Unsicherheitsintervalle zeigen. Baseline auf derselben Stichprobe ausweisen; für prospektive Aussagen aus vorherigen Daten schätzen. Bewertungen aus tatsächlichen Ergebnissen ableiten.

**13. Mittel — Divergenz und Risikoampel behaupten mehr als berechnet wird.**  
Fundstellen: [polymarket.js:441](C:/dev/Seasonaledge/landing/js/polymarket.js:441), [polymarket.js:510](C:/dev/Seasonaledge/landing/js/polymarket.js:510), [polymarket.js:247](C:/dev/Seasonaledge/landing/js/polymarket.js:247), [polymarket.html:183](C:/dev/Seasonaledge/landing/pages/polymarket.html:183).

Der Prior ist ein historischer Trefferanteil, kein Nachweis einer Fehlbewertung. Unvollständige Jahre werden akzeptiert, selbst wenn der letzte vorhandene Kurs weit vor Jahresende liegt. Konfidenzintervalle fehlen. Die Risikoschwellen sind Konstanten; eine historische Herleitung für „historisch erhöht“ ist nicht hinterlegt.

**Änderung:** „Abstand zur historischen Häufigkeit“ statt „Markt unterschätzt/überschätzt“. Vollständige Vergleichsfenster verlangen, Stichprobe und Unsicherheit anzeigen. Ampelschwellen als redaktionell festgelegt kennzeichnen oder empirisch begründen. Titel „Polymarket-Marktdaten“ und Einleitung „Marktpreise im Vergleich mit historischen Daten“ sind präziser.

**14. Mittel — Fed-Verteilung und Zeitreihen können präziser wirken, als sie sind.**  
Fundstellen: [polymarket.js:97](C:/dev/Seasonaledge/landing/js/polymarket.js:97), [polymarket.js:101](C:/dev/Seasonaledge/landing/js/polymarket.js:101), [polymarket.js:223](C:/dev/Seasonaledge/landing/js/polymarket.js:223), [polymarket.html:496](C:/dev/Seasonaledge/landing/pages/polymarket.html:496).

Der Erwartungswert normalisiert über die vorhandene Preissumme; die Balken bleiben unnormalisiert. Unvollständige oder zeitlich auseinanderliegende Quotes werden nicht beanstandet. `12+` zählt genau als 12: Das ergibt bei positiver Tail-Wahrscheinlichkeit keinen exakten Erwartungswert. Die 7-Tage-Veränderung kann einen beliebig alten Vorgänger verwenden. Glatte Linien überbrücken Datenlücken.

**Änderung:** Vollständigkeit, zeitliche Nähe und Preissumme prüfen und anzeigen. Tail-Annahme beziehungsweise Untergrenze benennen; 25-Basispunkt-Einheiten anhand der Regeln erklären. Für 7-Tage-Vergleiche eine maximale Baseline-Abweichung verlangen. Lineare/Stufenlinien mit sichtbaren Lücken verwenden.

**15. Mittel — Kategorienwechsel lässt alte Inhalte stehen.**  
Fundstelle: [polymarket.html:516](C:/dev/Seasonaledge/landing/pages/polymarket.html:516).

Nicht passende Bereiche werden nicht konsequent verborgen oder geleert. Bei „Crypto“ wird beispielsweise der Fed-Pfad trotzdem aus dem gefilterten Katalog berechnet; andere Bereiche können alte Werte behalten. Schnelle Wechsel besitzen keinen Schutz gegen verspätete Antworten. Fehlermeldungen verschwinden nach acht Sekunden.

**Änderung:** Jeden Abschnitt explizit anzeigen, leeren oder verbergen. Anfragen abbrechen beziehungsweise mit einer Ladegeneration abgleichen. Fehler und alte Daten dauerhaft kennzeichnen, bis ein erfolgreicher Abruf sie ersetzt.

**16. Mittel — Discovery kann einen sachlich unpassenden Markt automatisch übernehmen.**  
Fundstellen: [polymarket_discover.py:128](C:/dev/Seasonaledge/scripts/polymarket_discover.py:128), [polymarket_discover.py:162](C:/dev/Seasonaledge/scripts/polymarket_discover.py:162), [polymarket_data.py:229](C:/dev/Seasonaledge/shared/polymarket_data.py:229).

Ein Markt ohne Suchworttreffer erreicht allein mit 10.000 Dollar Liquidität einen Score von 0,667 und überschreitet die Annahmeschwelle 0,5. Zusätzlich wird die YES/NO-Reihenfolge pauschal aus der Tokenposition abgeleitet; beim Resolved-Scraper reicht jede Zweier-Outcomeliste.

**Änderung:** Liquidität nur zum Sortieren fachlich passender Kandidaten verwenden. Ereignis, Jahr, Schwelle und Regeln verbindlich validieren. Tokens und Ergebnis explizit über Outcome-Bezeichnungen zuordnen. Neue Zuordnungen zunächst als überprüfbare Kandidaten ausgeben.

**17. Mittel — EN ist statisch übersetzt, dynamisch teilweise deutsch.**  
Fundstellen: [polymarket.html:512](C:/dev/Seasonaledge/landing/pages/polymarket.html:512), [polymarket.html:594](C:/dev/Seasonaledge/landing/pages/polymarket.html:594), [polymarket.html:633](C:/dev/Seasonaledge/landing/pages/polymarket.html:633), [polymarket.html:721](C:/dev/Seasonaledge/landing/pages/polymarket.html:721), [en.json:1226](C:/dev/Seasonaledge/landing/i18n/en.json:1226).

Lade-/Fehlermeldungen, Brier-KPIs, Achsentitel, Tabellen und Metadaten enthalten fest eingebautes Deutsch. Die EN-Build-Pipeline übersetzt markierte HTML-Inhalte, nicht diese JS-Strings. Zahlreiche DE-Texte verwenden weiterhin „auswaehlen“, „Liquiditaet“ und „unterschaetzt“; `de.json` deckt die PM-Texte weitgehend nicht ab.

**Änderung:** Alle dynamischen Texte in DE/EN-Schlüssel überführen und erst nach geladener Übersetzung rendern. Echte Umlaute, einheitlich „Märkte“ und konkrete Beschreibungen verwenden.

SEO positiv: Canonical/hreflang sind vorgesehen; der EN-Build erzeugt einen eigenen englischen Head. Ein belegter EN-Canonical-Fehler liegt hier nicht vor. Jahresgebundene Titel und Marktanzahlen benötigen aber einen geregelten Jahreswechsel.

**18. Mittel — Tastatur- und Screenreader-Zugänglichkeit ist unvollständig.**  
Fundstellen: [polymarket.html:84](C:/dev/Seasonaledge/landing/pages/polymarket.html:84), [polymarket.html:97](C:/dev/Seasonaledge/landing/pages/polymarket.html:97), [polymarket.html:221](C:/dev/Seasonaledge/landing/pages/polymarket.html:221), [app.js:957](C:/dev/Seasonaledge/landing/js/app.js:957).

Das Brier-Infoelement ist fokussierbar, der Tooltip öffnet aber nur bei Hover. Selects haben keine verknüpften Labels. Sortierköpfe reagieren auf Klick ohne entsprechende Tastaturbedienung; dynamische Statusmeldungen besitzen keine Live-Region. Charts brauchen eine zugängliche Datenalternative.

**Änderung:** Tooltip als Button/Disclosure, Labels mit `for`, Sortierbuttons mit `aria-sort`, Statusregionen und zugängliche Tabellen ergänzen. Mobile hat bereits Tabellen-Scroll und responsive Raster; die tatsächliche Bedienbarkeit bei 320/375 Pixeln, Touch und Zoom bleibt als Sichtprüfung offen.

**Teil B — priorisierte Erweiterungen**

Die Aufwandsschätzungen gelten nach Behebung der hohen Befunde: **S** = wenige Tage, **M** = etwa ein bis zwei Wochen, **L** = mehrere Wochen einschließlich Datenvalidierung.

| Priorität / Erweiterung | Nutzen für Leser | Datenquelle und Bedingungen | Aufwand | Hauptrisiko |
|---|---|---|---|---|
| **P1: Datenqualität sichtbar machen** | Preisart, Alter, Spread, Volumen, Status und Regeln erklären die Belastbarkeit jeder Zahl. Filter für breite Spreads und geringe Aktivität. | Bestehende Gamma-/CLOB-Daten; öffentliche Lesezugriffe. API-Limits beachten; öffentliche Abrufbarkeit ersetzt keine Prüfung der Weiterverwendungsbedingungen. | M | Scheingenauigkeit durch einen pauschalen Liquiditätsschwellenwert. |
| **P1: Kalibrierung 30/7/1 Tage vorher** | Verständliche Antwort darauf, wie informativ Preise in verschiedenen Horizonten waren. | Eigene archivierte Snapshots und verifizierte Ergebnisse; historische API-Verfügbarkeit als Ausschlussgrund dokumentieren. | L | Rückblickende Auswahl, fehlende Historie und bereits bekannte Ergebnisse. |
| **P1: Kleiner Kalshi-Datenvergleich** | Zeigt unterschiedliche Erwartungen und insbesondere unterschiedliche Auflösungsregeln. | Kalshi bietet öffentliche REST-Endpunkte ohne Authentifizierung für Märkte, Events und Orderbücher; Regeln über `rules_primary`/`rules_secondary`. Kostenloser öffentlicher Abruf dokumentiert, kommerzielle Weiterveröffentlichungsrechte separat klären. | M für kuratierten Pilot, L für breite Abdeckung | Falsch zugeordnete Ereignisse, asynchrone Preise, unterschiedliche Abwicklung. |
| **P2: Fed-Märkte neben FedWatch** | Vergleich zweier Marktquellen zum selben FOMC-Termin. | CME FedWatch API: EOD derzeit ab **25 US-Dollar/Monat**; öffentliche Darstellung benötigt passende Lizenz. Eigener Futures-Ansatz benötigt ebenfalls zulässige Kursdaten. | M–L | Jahres-Cut-Zahl, verbleibende Cuts und terminaler Zinskorridor sind verschiedene Größen. |
| **P2: CPI-Kontext** | Erwarteter CPI-Wert neben historischer Monatsverteilung und Veröffentlichungskalender. | Kostenlose BLS-Daten; alternativ FRED mit API-Schlüssel und serienabhängigen Bedingungen. Vorhandenes `cpi_data.py` aggregiert Jahresdurchschnitte und reicht dafür nicht. | M | Verwechslung von Gesamt-/Kerninflation, MoM/YoY, saisonbereinigt/unbereinigt und Erstwert/Revision. |
| **P2: Wahlmärkte mit `/wahlen` verbinden** | Ereigniserwartungen neben historischen Börsenverläufen rund um Wahlen. | Vorhandene eigene Studie plus kuratierte öffentliche Marktdaten. Keine zusätzliche kostenpflichtige Quelle für die reine Verknüpfung. | S–M | Historische Indexrenditen dürfen nicht als Kandidaten-Siegwahrscheinlichkeit interpretiert werden. |
| **P3: Krypto-Optionsvergleich** | Zusätzlicher Vergleich mit optionsimpliziten Verteilungen. | Bestehender kostenpflichtiger Options-Stack enthält IBIT/ETHA; direkte Krypto-Daten etwa über öffentliche Deribit-Endpunkte. Nutzungsrechte, Limits und Historienbedarf prüfen. | L | ETF-Basis, Laufzeiten, amerikanische Optionen sowie risikoneutrale statt reale Wahrscheinlichkeit. |
| **P3: Alerts, Newsletter, Blog-Snapshots** | Änderungen und historische Datenstände werden nachvollziehbar, ohne die Seite täglich aufzurufen. | Eigene versionierte Snapshots; vorhandene Newsletter-Infrastruktur. Quellenrechte müssen auch Archivierung und Weitergabe abdecken. | M | Wiederholung falscher Bewertungen, Benachrichtigungsflut, nachträglich veränderte Artikelzahlen. |

Quellen für die Datenzugänge: [Kalshi Market Data](https://docs.kalshi.com/getting_started/quick_start_market_data), [Kalshi Marktfelder](https://docs.kalshi.com/api-reference/market/get-market), [CME FedWatch API](https://www.cmegroup.com/market-data/market-data-api/fedwatch-api.html), [CME-Methodik](https://www.cmegroup.com/articles/2023/understanding-the-cme-group-fedwatch-tool-methodology.html), [BLS API](https://www.bls.gov/developers/), [Deribit-Marktdaten](https://docs.deribit.com/api-reference/market-data/public-get_book_summary_by_currency).

Für den **Kalshi-Pilot** würde ich mit fünf bis zehn manuell geprüften Ereignispaaren beginnen. Nebeneinander gehören Ereignisdefinition, Frist/Zeitzone, Quelle, Revisionsregel, vorzeitige Auflösung und Annullierung. Den Preisabstand nur bei ausreichend zeitnahen und brauchbaren Quotes berechnen. Direkt daneben: **„Ein Preisabstand ist keine Arbitrage.“** Gebühren, Spreads, verfügbare Mengen und abweichende Auszahlungen verhindern diese Gleichsetzung.

Für **30/7/1-Tage-Kalibrierung** pro Markt genau den letzten zulässigen Snapshot vor dem jeweiligen Stichtag verwenden, mit begrenztem Höchstalter. Keine nachträgliche Interpolation. Fallzahl und Ausfälle je Horizont zeigen; zusätzlich dieselbe vollständige Marktstichprobe über alle Horizonte vergleichen. Die jetzigen breiten Zeit-Buckets beantworten diese Frage noch nicht.

Beim **Optionsvergleich** genügt weder Delta noch ein einzelner IV-Wert als Ereigniswahrscheinlichkeit. Eine terminale Verteilung aus passenden Optionspreisen ist möglich; die Wahrscheinlichkeit eines zwischenzeitlichen Berührens benötigt zusätzliche Modellannahmen. Das sollte ausdrücklich als modellabhängiger Vergleich erscheinen.

Die **Newsletter-Verknüpfung existiert bereits** in `shared/weekly_report.py`. Sie sollte zuerst dieselben Frische-, Regel- und Stichprobenprüfungen wie die Seite erhalten. Später sind sachliche Alerts wie „Preisänderung seit dem letzten gültigen Datenstand“ oder „Auflösungsregel geändert“ sinnvoll. Blog-Snapshots sollten Datenstand und Methodikversion dauerhaft festhalten.

**Nicht bauen würde ich:**

- Handelsbuttons, Wallet-/Orderanbindung, Referral-Vergütung oder Umgehungshilfen.
- Einen Arbitrage-Scanner für deutsche Privatkunden oder „garantierte Rendite“-Anzeigen.
- Automatisch freigeschaltete Ereignispaare allein aufgrund ähnlicher Titel.
- Einen gemeinsamen „Alpha-Score“, der Saisonhäufigkeit, Optionsverteilung und Ereignismarktpreis ohne fachliche Gleichsetzung verrechnet.
- Eine breite Sport-/Kurzfristmarkt-Abdeckung, bevor Datenqualität und Wartung des kleinen bestehenden Katalogs zuverlässig sind.

**Top-5-Prioritäten**

1. **XSS schließen und handelsnahe Texte samt Deutschland-Hinweis korrigieren.**
2. **Kontraktregeln verbindlich modellieren; unpassende Krypto-Divergenzen aussetzen.**
3. **Fehlende, alte und geschlossene Daten korrekt behandeln und sichtbar kennzeichnen.**
4. **Fehlerstatus durchgängig bis Workflow und Health-Check weiterreichen; Vollständigkeit prüfen.**
5. **Brier-Datenbasis und 30/7/1-Tage-Auswertung neu absichern; danach Kalshi-Pilot starten.**

FREIGABE: nein
