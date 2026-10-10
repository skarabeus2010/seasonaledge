# Antwort Codex Runde 5 — P1b (2026-10-10)

Prompt: [2026-10-10_xetra_tdoy_plan_v5.md](2026-10-10_xetra_tdoy_plan_v5.md). model: gpt-6.1-sol

**Urteil: mit Auflagen.** Die gemeinsame Datenquelle ist tragfähig; der globale Austausch verändert jedoch bereits Tagesnummern, Statistikzuordnungen und Strategien. Diese Folgen sind im Plan noch nicht ausreichend begrenzt.

**Antworten**

1. Forex kann als ausdrücklich benannte Legacy-Ausnahme bis P4 bleiben: `boerse()` und `isTradingDay(..., 'FOREX')` müssen bereits korrekt sein. Vollständige Kalendergleichheit aller Seiten erreicht P1b damit noch nicht. Die globale Aktivierung der 40 geänderten Zuordnungen braucht die unten genannten Auflagen (`2026-10-10_xetra_tdoy_plan_v5.md:43`).
2. Es ändern sich Tagesköpfe, Monatsmarker, Dashboard-Mini-Statistiken, ausgewählte Wochentags-/Overnight-Werte, Feiertagsauswertungen und Strategietermine. Schlechter werden können Zuordnungen zu alten Nummern und historische Feiertagsvergleiche (`app.js:877`, `dashboard.html:1295`). Die Messmenge muss außerdem NYSE/LSE einschließen.
3. Nicht auflösbare Ticker müssen **in P1b** sichtbar scheitern. Sonst wird der neue strenge Vertrag wieder durch Ersatzkalender aufgehoben (`dashboard.html:562`, `monatszyklus.html:439`, `watchlist.html:314`). Unbekannte einfache US-Symbole bleiben gemäß Python-Regel zulässig.
4. Ein reproduzierbar erzeugtes Bundle aus Daten und API ist robuster: eine Anfrage, gemeinsame Generation, keine zusätzliche Einbindung. Getrennte Dateien sind möglich, benötigen aber einen geprüften Lade-/Versionsvertrag. Der vorhandene Cache-Buster erfasst beide (`inject_credentials.sh:79`); EN wird aus DE erzeugt (`build_en.py:515`).
5. Es fehlen insbesondere Ereigniskennungen/Sonderlisten, Verbraucherprüfungen, Gültigkeitsanzeige, vollständige API-Fehlerverträge, Zeitzonentests und eine LF-Festlegung für Git. Belege folgen.

**Befunde**

1. **Hoch — Die behauptete Grenze zu P3/P4 wird bereits überschritten.**  
   Der Tageskopf zählt sofort mit dem neuen Kalender; Dashboard und Monatszyklus verwenden neue Kalenderpositionen auf weiterhin zeilennummerierten Historien ([dashboard.html:472](/C:/dev/SeasonalEdge/landing/pages/dashboard.html:472), `dashboard.html:578`, `monatszyklus.html:416`).  
   Speicherprobe mit echtem Header: AIR.PA am 01.05.2026 und letzter Aprilzeile mit TDOM 20 ergibt nach dem Wechsel **TDOM 20/20**, obwohl im Mai noch keine Sitzung stattfand. Ursache: periodenfremder DB-Ersatz ([app.js:877](/C:/dev/SeasonalEdge/landing/js/app.js:877)).

2. **Hoch — B4 beschreibt den Strategiepfad und die Änderungsmenge unzutreffend.**  
   Ein-Tages-Feiertag und UHTS bleiben ausdrücklich auf **NYSE-Ereignissen**; `get()` wird dort nicht auf die Tickerbörse umgestellt ([strategy-compute.js:335](/C:/dev/SeasonalEdge/landing/js/strategy-compute.js:335), `strategy-compute.js:539,552`). Der Kontextkalender beeinflusst hingegen Randtermine sämtlicher Strategien.  
   Zusätzlich ändern sich NYSE-/LSE-Listen bei unveränderter Zuordnung: Python führt etwa Samstag, 01.01.2000, anders als das bisherige JS. Mit identischen synthetischen NYSE-Kursen 1999–2001 erzeugte die echte Feiertagsstrategie **26 statt 25 Trades**; zusätzlicher Trade: 30.–31.12.1999. Messung nur für 40 Ticker reicht deshalb nicht.

3. **Hoch — Das Dashboard behält den positionsbasierten Ereignisvergleich.**  
   B4 behandelt nur `/feiertage`; das Dashboard verbindet historische Feiertage weiterhin über denselben Listenindex ([dashboard.html:1295](/C:/dev/SeasonalEdge/landing/pages/dashboard.html:1295)).  
   Gegenprobe: Der nächste TSE-Feiertag am 12.10.2026 hat Index 17; derselbe Index liefert **31.12.2011**, **22.09.2020** und **03.11.2021**. Daraus entstehen Renditen und Trefferquoten für unterschiedliche Ereignisse.

4. **Hoch — `nextTradingDay()` kann mit den neuen Kalendern einen geschlossenen Tag liefern.**  
   Die aktuelle Suche prüft nur zehn Tage und gibt danach den Ausgangstag zurück ([holidays.js:326](/C:/dev/SeasonalEdge/landing/js/holidays.js:326)).  
   Mit der Python-TSE-Liste liefert die echte API für **27.04.2019 → 27.04.2019**, geschlossen; korrekt ist **07.05.2019**. B5 prüft diese API bisher nicht.

5. **Hoch — Die strengen Fehler verschwinden in Verbrauchern.**  
   Neben `catch → NONE` existiert `catch → NYSE` in der Watchlist ([watchlist.html:310](/C:/dev/SeasonalEdge/landing/pages/watchlist.html:310)). Andere Stellen verschlucken Fehler oder lassen alte Anzeige stehen (`dashboard.html:1305,2028`).  
   Eine geworfene Ausnahme im Kalender genügt daher nicht: Kalenderfehler brauchen einen sichtbaren Zustand und müssen abhängige Werte zurücknehmen.

6. **Mittel — B1 enthält nicht die Informationen, die B2/B4 benötigen.**  
   Aus einer unmarkierten Schließungsliste lässt sich `_NYSE_SONDER` nicht eindeutig ableiten; Python pflegt diese Unterscheidung ausdrücklich ([nyse_holidays.py:139](/C:/dev/SeasonalEdge/shared/nyse_holidays.py:139)).  
   Auch „Zuordnung über Datum“ benötigt Ereignisidentität über Jahre hinweg: Ostern, Ersatztermine und Jubiläen haben wechselnde Daten. Sonderlisten und stabile Ereigniskennungen müssen in den Datenvertrag.

7. **Mittel — Gespeicherter Gültigkeitsstatus erreicht noch keinen Leser.**  
   B1 exportiert `status`, definiert aber weder eine JS-Abfrage noch die Behandlung in Seiten. HKEX/KRX rechnen außerhalb ihrer Tabellen mit ausdrücklich ungeprüften Ersatzregeln ([exchange_holidays.py:457](/C:/dev/SeasonalEdge/shared/exchange_holidays.py:457), `exchange_holidays.py:693`).  
   Python-Gleichheit darf diese Ergebnisse nicht zu uneingeschränkten Börsenaussagen aufwerten; Kennzeichnung beziehungsweise Ausschluss muss je Verbraucher feststehen.

8. **Mittel — B5 lässt Zeitzonenfehler und Teile des API-Vertrags offen.**  
   Die echte `isTradingDay()` liefert unter `Pacific/Apia` für **30.12.2011/NYSE false**, Python **true**: lokale Datumsnormalisierung überspringt dort diesen Tag ([holidays.js:269](/C:/dev/SeasonalEdge/landing/js/holidays.js:269)).  
   Erforderlich sind zeitzonenfreie Kalenderarithmetik sowie Prüfungen aller sieben APIs, ungültiger Datums-/Zahlentypen, Börsenaliase und Bereichsüberschreitungen. Validierung muss auch vor Wochenend-/CRYPTO-Abkürzungen greifen.

9. **Mittel — Der Bytevergleich benötigt eine Git-Zeilenendenregel.**  
   Lokal ist `core.autocrlf=true`; `.gitattributes` fehlt, und `eol` ist für beide Kalenderdateien nicht gesetzt. LF-Ausgabe und byteweiser Arbeitsbaum-/HEAD-Vergleich können nach einem Windows-Checkout auseinanderlaufen.  
   Für erzeugte Dateien `text eol=lf` festlegen; Hashumfang einschließlich Wochenmasken, Zuordnungen, Status und Sonderdaten sowie Schema-Version definieren (`2026-10-10_xetra_tdoy_plan_v5.md:27`).

**Auflagen vor dem Code**

- Aktivierungsumfang verbindlich festlegen: isolierter Daten-/API-Aufbau bis P4 oder ausdrücklich erweiterter P1b-Umfang mit bereinigten Nummern-/Statistikverbrauchern.
- Ereignistermine, tatsächliche Börsenschließungen und Sonderschließungen im Datenvertrag unterscheiden; stabile Ereigniskennungen in Feiertagsseite **und Dashboard** verwenden.
- Änderungsmessung auf alle betroffenen Kalender und Verbraucher erweitern: Trades, Randzustände, Kennzahlen, Marker und Termine; reale Kurs-Snapshots einfrieren.
- `nextTradingDay()` bis zum ersten offenen Tag suchen; bei erschöpftem Datenbereich ausdrücklich scheitern.
- Fehleranzeige und Entfernen alter abhängiger Werte für alle Aufrufer festlegen; keine Fehlerersatzkalender.
- Gültigkeitsstatus für Börse/Jahr öffentlich abfragbar machen und seine Darstellung bestimmen.
- Bundle-/Ladevertrag samt Cache-Version, EN-Erzeugung und LF-Regel festlegen; echte Seiteneinbindungen prüfen, nicht nur im Test die Abhängigkeit hinzufügen.
- B5 um sämtliche APIs, echte Verbraucher, Zeitzonen und fehlende/beschädigte Daten ergänzen; Mutationen mit Ankern und benannten fachlichen Prüfungen verbinden.

Prüfung ausschließlich lesend, Gegenproben im Speicher; vorhandener Python-Sollfallwächter **86/86 bestanden**. Keine Dateien geschrieben.
