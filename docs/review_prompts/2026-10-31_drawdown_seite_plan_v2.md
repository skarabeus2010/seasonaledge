# Bauplan v2 — Unterseite `/drawdown`, Nightly-Übersicht, Morgen-Mail

Antwort v1: [2026-10-31_drawdown_seite_plan_antwort.md](2026-10-31_drawdown_seite_plan_antwort.md) — FREIGABE MIT
AUFLAGEN. Alle Befunde sind unten eingearbeitet (Verweis „[A n]“). **Neu gegenüber v1 (Nutzerentscheidung
2026-10-31):** alle Zusatzideen werden gebaut — Kaplan-Meier, Price Return gegen Total Return, Forward Returns nach
einem Drawdown, Drawdown-Kalender mit Ulcer Index, Mehrticker-Vergleich, Hinweis in der Morgen-Mail. Gebaut wird in
drei Phasen; jede bekommt eine eigene Code-Prüfung.

Der Tempofehler [A 4] ist in `scripts/research/drawdown_analyse.py` behoben (Vergleich gegen `laufend.bis_schwelle`);
für QQQ unverändert, weil dort Alter = Handelstage bis zur Schwelle = 18.

## Phase 1 — Seite `/drawdown` (Einzelticker im Browser)

### 1.1 Dateien
- `landing/js/drawdown-compute.js` (`SA.drawdown`, reine Funktionen, kein DOM).
- `shared/drawdown.py` — Fachkern Python (für Nightly/Mail in Phase 2 produktiv, hier Referenz); das
  Forschungsskript verwendet ihn danach. **Unabhängige Testreferenz getrennt** im Wächter (eigene, schlichte
  numpy-Rechnung, nicht aus `shared/drawdown.py`) [A 7].
- `landing/pages/drawdown.html` (ApexCharts über `charts.js`), i18n `dd.*` DE/EN (`_JSON_VER`), `_EN_PAGE_META` →
  `/en/drawdown`, Nav „Mehr“ nach Stress-Ampel in `nav.html` **und** `index.html`, Querverweis Stress-Ampel ↔
  Drawdown, nginx `location = /drawdown` mit HTML-Neuvalidierung wie die übrigen Seiten. Sitemap kommt automatisch
  aus der Seitenentdeckung, EN aus `_EN_PAGE_META` — geprüft werden tatsächlicher DE-Head, gebackener EN-Head,
  reziproke hreflang und Sitemap-Einträge [A 8].

### 1.2 Letzte abgeschlossene Sitzung E je Markt [A 1]
Direkter Aufruf `SA.boersenkalender` (nicht `SA.holidays`, das unter `alt` noch die alte Logik hat) [A 3].
- Börsen: E = letzte Sitzung, deren regulärer Schluss in der Börsenzeitzone (aus dem Kalender: Zone, Schlusszeit,
  belegter Halbtagsschluss) plus 30 min Datenpuffer vorbei ist.
- Krypto: E = letzter vollständig abgeschlossener UTC-Kalendertag (laufender UTC-Tag zählt nicht).
- Forex: E = letzter abgeschlossener Werktag nach UTC-Tagesgrenze (Konvention, so gekennzeichnet).
- Kennt der Kalender für eine Börse keine Schlusszeit: konservativ der Vortag der heutigen Sitzung, mit Hinweis.
Zeilen nach E zählen nicht. Das Datum E steht auf der Seite.

### 1.3 Achse, Lücken, Kalenderstatus [A 2, A 3, A 6]
- Achse = offene Sitzungen bis E. Sitzungsrendite = Summe der `log_return` der Zeilen nach der vorigen Sitzung bis
  s. **Unbekannt**, wenn an s keine Zeile ist ODER eine beteiligte Rendite fehlt/nicht endlich ist.
- **Episodenvertrag bei unbekanntem Pfad:** Episoden, die vollständig vor der ersten unbekannten Rendite
  abgeschlossen sind, bleiben gültig. Die Episode, in der die Lücke liegt, und **alle späteren** globalen Kennzahlen
  (laufender Drawdown, Ränge, Zeitanteil ab dort) sind „nicht bestimmbar“ — es wird nie neu basiert und kein
  Segmentanfang als neues Hoch behandelt. Optional als ausdrücklich lokale Auswertung „seit <Datum>, Vorgeschichte
  unbekannt“ (eigene Kennzeichnung, keine Ränge gegen die globale Historie).
- **Kalenderstatus:** `kalender_status` je Jahr über die gesamte für die Hochs benötigte Historie; enthält sie
  `ungeprueft`/`annahme`, steht ein Hinweis („Handelskalender für 1999–2010 ungeprüft; entfernte Zeilen an
  Nicht-Sitzungen gelten dort als Annahme“). Die Zahl entfernter Zeilen wird ausgewiesen.
- **Renditebasis je Instrumententyp** aus `symbols.py`-Kategorien: Aktie/ETF „adjustierte Schlüsse des Lieferanten
  (Näherung an Total Return)“; Index „Kursindex“ bzw. Performanceindex nach Typ; Krypto/Forex/Futures/Vola neutral
  „aus gespeicherten logarithmischen Renditen“ mit Einschränkung. Nie pauschal „Total Return“.

### 1.4 Rechenvertrag (freigegebene Methodik + Korrekturen)
Wie Methodikplan: Peak/Trough/Recovery, Max Drawdown, Peak to Trough, Time to Recovery (Trough → Recovery),
Drawdown-Dauer, Kalendertage, Zeitraum über Peak, grenzüberschreitende Episoden gesondert, Max-Drawdown-Filter
5–40 % (Schnellwahl 5/10/20), ungerundeter aktueller DD. Ränge nur bei erfülltem Filter, mit n; `n = 0` →
„nicht bestimmbar“, `n < 5` → Einzelwerte statt Quartile [A 5]. Tempo = erster Übertritt − Peak für beide [A 4].
Bezeichnung im sichtbaren Text [A 5]: **„Historische Dauer ab erstmaligem Erreichen von −x %“** (Kurzform in der
Tabelle „TTR ab −x %“ mit Tooltip); kein Satz über die Restdauer der laufenden Episode.

### 1.5 Zusatzanalysen (neu)
- **Kaplan-Meier ab Schwelle:** Zeitnull = erster Übertritt von −x % (x = aktueller DD, Regler „Vergleich ab x %“
  5–40 %); Ereignis = Recovery; laufende Episode als rechtszensierte Beobachtung bei ihrem Alter seit Übertritt.
  Treppenkurve mit Zahl der Fälle unter Risiko an jedem Schritt (`at risk`), Greenwood-Konfidenzband 95 % nur als
  Band, Median nur wenn die Kurve 50 % unterschreitet. Text: beschreibt frühere Episoden, keine Prognose.
- **Forward Returns nach Drawdown von x %:** Ereignis = erster Übertritt von −x % je Episode (eine Beobachtung pro
  Episode → keine Häufung durch Folgetage); Rendite nach 20/60/120 Sitzungen ab Schluss des Übertrittstags; Basis =
  alle Sitzungen mit vollständigem Fenster; dazu Zwischenverlust `min(0, F1…Fh)`; Fallzahl; kein Test.
  Überlappung: Episoden mit Abstand < h können überlappen → Anzahl überlappender Paare wird angezeigt.
- **Drawdown-Kalender:** Max Drawdown je Kalenderjahr (gegen das laufende Allzeithoch, nicht gegen das Jahreshoch —
  beides beschriftet; Wahl: Allzeithoch), Balken; **Ulcer Index** je Jahr = √(Mittel der quadrierten Drawdowns in %)
  über die Sitzungen des Jahres. Laufendes Jahr als „bis E“ gekennzeichnet.
- **Price Return gegen Total Return:** in Phase 3 (Datenfrage, siehe unten); Phase 1 zeigt nur die gespeicherte
  Basis mit Typtext.

### 1.6 Wächter `scripts/verify_drawdown.py` (Gate) [A 7]
- **Dritte Referenz:** unabhängige numpy-Rechnung im Wächter (Laufmaximum, Episoden über Vorzeichenwechsel,
  Quantile `np.quantile`, KM aus Formel), plus **handgerechnete Sollwerte** für kleine Reihen.
- Grenzfälle: keine Episode, Gleichstand am Trough (frühere), Recovery genau auf Peak-Niveau (≥), laufende Episode,
  Ticker am Hoch, `n = 0/1`, exakte Filterschwelle, fehlende Endsession, laufende Sitzung, ungültige Rendite,
  aufeinanderfolgende Lücken, mehrere Phantomzeilen, Schalttag, Krypto-Wochenende, Forex-Freitag, XETRA- und
  Krypto-Schlusszeit unter drei Prozesszeitzonen, Tempo mit zwischenzeitlicher Erholung und erneutem Übertritt,
  KM mit zensierter Beobachtung (Sollwert per Hand), Forward Return mit unvollständigem Fenster.
- **Invarianten:** Fensterwechsel ändert keine Peaks/Episoden; Filterwechsel ändert nicht die laufende Episode;
  Skalierung des Index um einen Faktor ändert keinen Drawdown; Anhängen einer Phantomzeile ändert nichts.
- **Echte Reihen** (eingefroren mit SHA-256): QQQ, ^GDAXI, BTC-USD, EURUSD=X — JS = Python = numpy für alle Fenster
  × m ∈ {5, 7, 10, 20, 33}.
- **Echte Seite** DE und gebaute EN in jsdom: Produktionsanfrage mit voller Historie (kein Startdatum), Kacheln =
  Kern, „nicht vergleichbar“, n = 0, Ticker am Hoch, zu kurze Historie, Ladefehler → Banner (auch nach vorheriger
  erfolgreicher Darstellung), schneller Tickerwechsel mit vertauschter Antwortreihenfolge, Chartdaten mit Lücken.
- Gate-Aufruf ohne Sonderflag = alle Pflichtprüfungen. Mutationstest isoliert: eindeutiger Anker, Kontrolle grün,
  Fang an der benannten Prüfung; Absturz/Ausnahme zählt nicht als Fang.

## Phase 2 — Nightly-Übersicht, Mehrticker-Vergleich, Morgen-Mail
- Nightly-Phase schreibt `landing/data/drawdown_uebersicht.json` (gitignored, atomar, HTTP-Prüfung) über alle
  Ticker aus `symbols.py` mit `shared/drawdown.py` und demselben Sitzungs-/Lückenvertrag: aktueller DD, Peak,
  Dauer, Ränge (10 J, ≥ 5 %), Status bestimmbar/nicht bestimmbar mit Grund, E je Ticker. Health-Check auf Frische.
- **Zwillingsgleichheit:** Wächter vergleicht für eine Stichprobe von Tickern die Übersicht (Python) mit dem
  Browserkern (JS) auf denselben Kursen.
- Seite: Tabelle „Drawdown im Vergleich“ (sortierbar, Filter Kategorie), Klick lädt den Ticker.
- **Morgen-Mail:** Abschnitt nur, wenn ein Ticker der Kernliste in der letzten Sitzung erstmals in der laufenden
  Episode −10 % oder −20 % unterschritten hat (Übertritt am Tag E, nicht „liegt darunter“); mit aktuellem DD,
  Dauer, Rang und Link `/drawdown?t=…`. Leerer Abschnitt entfällt. Mailgröße und Vorlage im
  `verify_*`-Mailwächter.

## Phase 3 — Price Return gegen Total Return
Wir speichern nur adjustierte Schlüsse. Price Return ließe sich aus `dividend_events` (Ex-Tag, Betrag)
zurückrechnen: `r_price = r_total − ln(1 + D/C_{t-1})` am Ex-Tag. Vorab Datenprüfung: Abdeckung je Ticker gegen eine
unabhängige Quelle (Yahoo-Dividendenhistorie) für eine Stichprobe; Vergleich nur für Ticker mit nachgewiesen
vollständiger Historie, sonst ausgeblendet mit Grund. Eigener Plan, wenn die Datenprüfung vorliegt.

## Fragen an den Reviewer
1. Trägt der Episodenvertrag bei unbekanntem Pfad (1.3)?
2. KM-Definition (Zeitnull Übertritt, zensierte laufende Episode, Greenwood-Band) und Forward Returns „eine
   Beobachtung pro Episode“ — tragfähig?
3. Drawdown-Kalender gegen Allzeithoch statt Jahreshoch — sinnvolle Wahl?
4. Phase-2-Mailregel „erstmaliger Übertritt am Tag E“ — richtig gegen Dauer-Spam abgegrenzt?
5. Was fehlt, was ist zu stark?
