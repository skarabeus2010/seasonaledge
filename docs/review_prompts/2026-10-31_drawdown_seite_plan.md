# Bauplan v1 — Unterseite `/drawdown` (Drawdown-Analyse je Ticker)

Stand 2026-10-31. Grundlage: Methodikplan [2026-10-31_drawdown_analyse_plan.md](2026-10-31_drawdown_analyse_plan.md)
mit Codex-Antwort (FREIGABE MIT AUFLAGEN, Auflagen 1–6 umgesetzt) und das vom Nutzer abgenommene Exemplar
(Artefakt QQQ, Rechnung `scripts/research/drawdown_analyse.py`, Browser-Zwilling im Artefakt 0 Abweichungen).
Nutzerentscheidungen: Darstellung wie im Exemplar; englische Fachbegriffe auch im deutschen Text (Max Drawdown,
Drawdown-Dauer, Peak, Trough, Recovery, Peak to Trough, Time to Recovery, Drawdown-Kurve); Max-Drawdown-Auswahl
≥ 5/10/20 % als Schnellwahl plus freier Regler; Vorschlag Platzierung: Nav „Mehr“ nach der Stress-Ampel.

## 1. Dateien
- `landing/js/drawdown-compute.js` — `SA.drawdown`: reine Funktionen, kein DOM (Muster `spot-vol-compute.js`):
  `achse(rows, ticker, {jetzt})` → Sitzungsachse + Index; `episoden(achse)`; `auswerten(achse, {fenster, maxDD,
  vergleich})` → Kennzahlen/Gruppen/Überlebenskurven; `kurve(achse)`.
- `landing/pages/drawdown.html` — Seite (Standard-Header, Sidebar mit Ticker + Zeitraum + Max Drawdown, Inhalt wie
  Exemplar), Charts mit ApexCharts über `charts.js` (Seitenstandard, nicht Chart.js).
- `shared/drawdown.py` — Python-Referenz (aus `scripts/research/drawdown_analyse.py` gezogen, dieselben Verträge),
  nur für Wächter/Studien; die Seite rechnet im Browser.
- `scripts/verify_drawdown.py` — Wächter im Gate (siehe 5), `scripts/js/probe_drawdown.js` (jsdom, echte Seite).
- i18n: Keys `dd.*` in `de.json`/`en.json` (`_JSON_VER` erhöhen), `_EN_PAGE_META` + `build_en.py` → `/en/drawdown`.
- Einbindung: `landing/components/nav.html` (Mehr, nach Stress-Ampel) **und die eigene Nav-Kopie der Startseite**,
  nginx `location = /drawdown`, SEO-Seitenliste (`shared/seo_basis`) für Sitemap, Querverweis von/zu
  `/crash-fruehwarnung`.

## 2. Daten- und Achsenvertrag (Browser)
- Kurse über `SA.kurse` (Felder `date, close, log_return`, volle Historie).
- **Sitzungsachse** = offene Sitzungen der Börse des Tickers (`SA.boersenkalender`, wie `/spot-vol-beta`) von der
  ersten Zeile bis zur **letzten abgeschlossenen Sitzung** E. Zeilen nach E (laufende Sitzung, Intraday-Zeile) und
  Zeilen an Nicht-Sitzungen (Phantomzeilen) zählen nicht. Krypto: jeder Tag; Forex: Mo–Fr.
- Rendite an Sitzung s = Summe der `log_return` der Zeilen nach der vorigen Sitzung bis s (Phantomzeilen exakt
  eingerechnet). Fehlt die Zeile an s (echte Lücke): **Pfad unbekannt** → Episoden über die Lücke sind nicht
  bestimmbar (Kennzeichnung, keine stille 0); Index vor/nach der Lücke wird nicht verbunden. Frage an Codex: ganze
  Auswertung ab der letzten Lücke beginnen lassen, oder Episoden über eine Lücke einzeln sperren?
- Renditebasis: adjustierte Schlüsse des Lieferanten → Total-Return-Näherung (Text nennt das).
- Mindesthistorie: unter 2 Jahren keine Einordnung, nur Drawdown-Kurve + Hinweis.

## 3. Rechenvertrag (wie freigegebene Methodik)
Episode Peak (letzter Schluss mit DD = 0) → erste Sitzung mit Index ≥ Peak (Recovery); Trough = erste Sitzung mit
minimalem DD. Max Drawdown, Peak to Trough (T−P), Time to Recovery (R−T), Drawdown-Dauer (R−P), Kalendertage.
Laufende Episode rechtszensiert. Zeitraum = Peak im Zeitraum (10/15/20 Jahre/gesamt), grenzüberschreitende
Episoden gesondert. Max-Drawdown-Filter m ∈ [5, 40] %, Vergleiche mit ungerundetem aktuellen DD. Ränge:
`kürzer = #(Dauer < Alter)/n`, `tiefer = #(MaxDD < aktueller DD)/n`, nur wenn der aktuelle DD ≥ m erfüllt.
„TTR ab aktuellem DD“: frühere Episoden mit MaxDD ≤ aktueller DD, Sitzungen vom ersten Erreichen bis Recovery.
Überlebenskurve abgeschlossener Episoden. Zeitanteil (zeitgewichtet). Kein laufender Drawdown (Ticker am Hoch):
Seite zeigt „kein laufender Drawdown“ und nur die historischen Verteilungen.

## 4. Darstellung
Wie Exemplar: Status (aktueller Drawdown, Peak, Drawdown-Dauer, Trough bisher, Daten bis), Kurzantwort (aus den
Zahlen erzeugt, ohne Wertung jenseits der Ränge), Steuerung, Rang-Kacheln, vier Charts (Drawdown-Dauer-Kurve,
Max Drawdown × Dauer, TTR ab aktuellem DD, Handelstage bis zum aktuellen DD), Drawdown-Kurve, Episodentabelle
(sortierbar über `SA.makeSortable`), Methodik, FAQ für SEO (statischer Text, `data-i18n-html`). Ticker per `?t=`
und `SA.prefs`. Ladefehler → Fehlerbanner, keine leeren Kacheln.

## 5. Wächter `verify_drawdown.py` (Gate)
1. Rechenkern JS (node) = Python-Referenz auf synthetischen Fällen mit Sollwerten (Hand gerechnet): neue Hochs
   ohne Drawdown, Gleichstände am Trough, Recovery genau auf Peak-Niveau, laufende Episode, Phantomzeile, echte Lücke,
   laufende Sitzung, Krypto-Wochenende.
2. Echte eingefrorene Reihen (QQQ `blog/daten/qqq_2026-10-30.json`, dazu ^GDAXI und BTC-USD als Snapshot): alle
   Kennzahlen JS = Python für alle Fenster × m ∈ {5, 10, 20, 7, 33}.
3. Echte Seite in jsdom (Muster `verify_spot_vol_beta`): rendert ohne Fehlerbanner, Kacheln zeigen dieselben Zahlen
   wie der Kern, „nicht vergleichbar“ bei m > |aktueller DD|, Ticker ohne laufenden Drawdown, zu kurze Historie,
   Ladefehler → Banner; drei Zeitzonen.
4. Mutationstest (eigene Datei, isoliert), jede Mutation an der benannten Prüfung.

## Fragen an den Reviewer
1. Lückenbehandlung (Abschnitt 2) — welche Variante?
2. Reicht die Sitzungsachse aus `SA.boersenkalender` für alle 370 Ticker (V2-Fassade), oder gibt es Börsen, deren
   Kalender `ungeprueft` ist und die eine Kennzeichnung brauchen?
3. Ist es vertretbar, die Python-Referenz in `shared/` zu legen, obwohl nur Wächter sie nutzen?
4. Was fehlt am Wächter, damit er nicht nur die Fälle prüft, die ich mir ausgedacht habe?
5. Platzierung und Adresse `/drawdown` (DE/EN gleich) — Einwände aus SEO-/Nav-Sicht?
