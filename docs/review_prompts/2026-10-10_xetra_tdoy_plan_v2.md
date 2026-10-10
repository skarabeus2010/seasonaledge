# Handelstag-Nummern nach Börsenkalender — Plan v2 (Runde 2)

Vorgänger: [Plan v1](2026-10-10_xetra_tdoy_plan.md), [Antwort Runde 1](2026-10-10_xetra_tdoy_plan_antwort1.md)
(„nicht tragfähig“). Alle Auflagen aus Runde 1 sind unten eingearbeitet oder ausdrücklich offen.

<task>
**Nutzerentscheidung 2026-10-10: „Die Tage werden nach dem Börsenkalender ausgewiesen.“** Das gilt nicht nur
für die gespeicherte Spalte `prices.tdom/tdoy`, sondern für jede Stelle, die einen Handelstag des Monats/Jahres
nummeriert — Statistiken (`tdom_stats`/`tdoy_stats`), Seiten, Mails, Strategien. Heute zählen die meisten
Stellen **Kurszeilen** (`cumcount`, Zähler über die Zeilenliste), einige den **Kalender**; bei Datenlücken und
Füllzeilen meinen beide mit „Tag 194“ verschiedene Tage.

Du bist in dieser Runde **Reviewer und Code-Assistent**: (1) erstelle die vollständige Bestandsliste (unten
Abschnitt „Auftrag Bestandsliste“), (2) prüfe den Plan. Nichts schreiben (read-only).
</task>

## Geklärt in Runde 1 (übernommen)
- Der Kalender stimmt: 3.10.2011–2013 waren Handelstage (Handelskalender 2011/2012/2013 der Deutschen Börse;
  das Blatt 2012 habe ich selbst gelesen). Den Aktien fehlen dort die Kurszeilen → Datenlücke, keine Schließung.
- Fehlende Quelldaten sind nie ein Schließungsbeleg (auch nicht im Nightly-Lückenfüller, Befund 6).
- Rückschreiben vor 2001 nicht in diesem Vorhaben (Kalender für den Parketthandel unbelegt); 3.10.2000 später.
- Mein Muster-Check der Klasse `korrektur` war tautologisch (Befund 5) → Abnahme über unabhängige Referenz.

## Vertrag (V)
**V1 Nummer.** Für Börse `X` und Datum `d`: `tdom(d)` = Anzahl Handelstage von `X` vom 1. des Monats bis
einschließlich `d`; `tdoy(d)` analog ab 1.1. Rückwärts: `tdom_rev(d)` = −(Anzahl Handelstage von `d` bis
Monatsende einschließlich), `tdoy_rev` analog. Für einen geschlossenen Tag ist die Vorwärtszahl die des letzten
Handelstags davor in derselben Periode, sonst 0 (Runde 1, Frage 4); eine Rückwärtszahl hat er nicht (`None`).
Krypto 24/7 = jeder Kalendertag; Forex Mo–Fr. Quelle der Wahrheit: `shared/exchange_holidays.is_trading_day`
bzw. JS `SA.holidays.isTradingDay` (Zwillingstest `scripts/verify_kalender_zwilling.py` existiert).

**V2 Eine Funktion je Sprache.**
- Python: `shared/exchange_holidays.handelstag_nummern(daten, exchange) -> list[(tdom, tdoy, tdom_rev, tdoy_rev)]`,
  Kalender je (Jahr, Börse) gecacht. Ersetzt `backfill_tdoy.compute_tdoy_tdom`,
  `backfill_new_ticker.compute_tdoy_tdom`, die Zähler in `intraday_refresh`, `preprocess()`, `add_tdom_columns`,
  `add_tdoy_columns`, `daily_report._tdom_for_ticker/_tdom_for_date`.
- JS: `SA.holidays.handelstagNummern(dates, ex)` in `landing/js/holidays.js`, gleiche Rückgabe.
- Zwillingstest gegen eine **dritte, unabhängige Referenz**: `numpy.busday_count` mit der Feiertagsmenge der
  Börse (anderer Algorithmus, dieselbe Feiertagsquelle) plus feste Sollfälle aus den offiziellen Kalendern
  (XETRA 2012: 3.10. = Handelstag; 2018: 21.5. und 3.10. geschlossen → 4.10.2018 = (3, 193)).

**V3 Füllzeilen.** Eine Kurszeile an einem geschlossenen Tag (Quelle liefert `volume=0`, `close`=Vortag) zählt
in keiner Tagesstatistik und in keiner Kurve als Handelstag. Sie bleibt in `prices` (Kursdaten unberührt).

**V4 Renditen über eine Datenlücke.** Fehlt zwischen zwei Kurszeilen eine Sitzung, deckt die Rendite der
späteren Zeile zwei Sitzungen ab. **Vorschlag:** in Tagesstatistiken (Ø/Win-Rate je TDOM/TDOY) wird diese
Rendite **nicht** dem späteren Tag zugeschlagen, sondern ausgelassen und gezählt (`n_luecke`); Kurven
(kumulierte Monats-/Jahrespfade) behalten sie, weil der Pfad sonst springt. Frage an dich unten.

**V5 Gespeicherte Spalte.** `prices.tdom/tdoy` folgt V1. Leser, die sie nutzen (`app.js:877` Fallback,
`decade-compute.js`), bekommen dieselbe Zahl, die sie selbst rechnen würden; mittelfristig rechnet jeder
Leser selbst über V2 und die Spalte ist nur noch Abkürzung.

## Phasen (je Phase: Code → Codex-Review bis Freigabe → Commit)
- **P1** V2-Funktionen + Zwillingstest + unabhängige Referenz + Mutationstest (deterministisch, `_atomar_schreiben`).
- **P2 Schreiber:** Nightly (`preprocess` → V2 mit Ticker/Börse), Intraday, Onboarding (`backfill_new_ticker`,
  auch 0 schreiben statt nur `> 0`), `backfill_tdoy`, Nightly-Lückenfüller, `fix_missing_days.py`,
  `shared/data.append_today_if_missing` (kein Aufrufer → löschen, wenn bestätigt). Ein Schreiber, der V2 nicht
  rechnen kann, schreibt `NULL`, nie eine Zeilenzählung.
- **P3 Python-Leser:** `tdom_analysis`/`tdoy_analysis` (inkl. Rückwärtszahlen, V3, V4), `cache_manager`,
  `daily_report`, `weekly_report`, `plain_vanilla` (nutzt `add_tdom_columns` an drei Stellen — **Wirkung auf
  veröffentlichte Strategie-Zahlen vorher messen**, Liste der geänderten Trades), `backtest_newsletter_scoring`.
- **P4 JS-Leser:** Dashboard (`assignTdom` Zeilen ↔ `getCurrentTdom` Kalender), `/tdom-analyse` (Builder
  verliert `tdoy`, Runde 1 Befund 2), `/monatszyklus`, `/monatswechsel`, `/overnight`, `/backtest-engine`
  (TDOM = Mo–Fr!), `strategy-compute.js`, `decade-compute.js`, `app.js`.
- **P5 Rückschreiben `prices`** ab 2001 für alle Börsen, deren Kalender ab 2001 geprüft ist (zunächst XETRA,
  NYSE; Rest nur Bericht): Trockenlauf-Skript im Repo (vollständige Pagination, exakte Schlüsselmenge,
  Teil-NULLs, Klassen getrennt, unabhängige Referenz), danach **ein** SQL-`UPDATE … FROM` in einer Transaktion
  mit alten Sollwerten als Bedingung, Trefferzahl = Soll oder `ROLLBACK`; Lauf außerhalb der Cron-Fenster,
  Nightly/Intraday-Timer währenddessen gestoppt. **Freigabe durch den Nutzer.**
- **P6** `tdom_stats`/`tdoy_stats` neu rechnen (Nightly-Pfad), vorher/nachher-Bericht der größten
  Verschiebungen; Mails/Seiten danach im Browser bzw. per `--dry-run` ansehen.
- **P7** Andere Börsen nur lesend berichten.

## Auftrag Bestandsliste (Code-Assistent)
Liste **jede** Stelle im Repo (Python, JS, HTML-Inline-Skripte, SQL), die einen Handelstag des Monats oder
Jahres (vorwärts oder rückwärts) **berechnet, speichert oder liest**, als Tabelle:
`Datei:Zeile | Funktion | schreibt/rechnet/liest | Zählweise heute (Zeilen / Kalender / Mo–Fr / DB-Spalte) |
Börse berücksichtigt? | Füllzeilen/Lücken berücksichtigt? | sichtbar wo (Seite, Mail, Blog, intern)`.
Dazu: welche dieser Stellen speisen **veröffentlichte Zahlen** (Blogartikel, Strategie-Kennzahlen auf Seiten)?
Suche auch nach Schreibvarianten (`trading_day_of_month`, `tdom`, `TDOM`, `tdoy`, `handelstag`, `nthTradingDay`,
`cumcount`, Zähler in Schleifen über `rows`), nicht nur nach Funktionsnamen.

## Fokusfragen
1. V1–V5: tragfähig? Insbesondere V4 (Lückenrendite auslassen in Statistiken, behalten in Kurven) — oder
   besser die Rendite auf die fehlenden Sitzungen verteilen / die Lücke aus der Kursquelle schließen?
2. Reihenfolge: P2 vor P3/P4 richtig? Gibt es einen Zwischenstand, in dem Seiten inkonsistenter sind als heute?
3. P3 `plain_vanilla`: welche Strategien hängen an `add_tdom_columns`, und wie misst man die Wirkung so, dass
   veröffentlichte Zahlen nicht still wandern (Muster 1A: Trades bis Ende 2025 auf zwei Stellen vergleichen)?
4. P5: Reicht SQL-Editor-Ausführung durch den Nutzer, oder ein Server-Skript über eine `SECURITY DEFINER`-RPC?
   Welche Vorbedingungen machen „Schreibruhe“ prüfbar statt behauptet?
5. Was fehlt?

## Ausgabevertrag
**Urteil** (ein Satz) · **Bestandsliste** (Tabelle, vollständig — Länge egal) · **Antworten Fokusfragen**
(je ≤ 8 Zeilen, mit Datei:Zeile) · **Befunde** (nummeriert, mit Beleg) · **Auflagen vor P1** (Liste).
