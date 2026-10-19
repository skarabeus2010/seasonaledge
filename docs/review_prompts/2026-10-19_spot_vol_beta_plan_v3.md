# Review: /spot-vol-beta — Plan v3 (Runde 3)

Read-only. v2: `docs/review_prompts/2026-10-19_spot_vol_beta_plan_v2.md`, deine Antwort Runde 2:
`docs/review_prompts/2026-10-19_spot_vol_beta_plan_v2_antwort.md`. v2 gilt weiter, außer den Änderungen hier.

## R2-1 Sitzungsachse → `SA.boersenkalender` (NYSE)

Alle angebotenen Paare (^GSPC, SPY, ^NDX, QQQ, USO gegen ^VIX/^VXN/^OVX) laufen auf `NYSE` (Spot via
`SA.boersenkalender.detect`/Zuordnung; die Vol-Indizes werden ausdrücklich gegen den NYSE-Kalender gelegt).
- Achse = `sitzungen(start, ende, 'NYSE')`, start = erste gemeinsame Zeile, ende = letzte abgeschlossene Sitzung (R2-3).
- Kurszeilen an Nicht-Sitzungen (Phantomzeilen) werden verworfen.
- Rendite eines Tickers an Sitzung s gilt nur, wenn er eine Zeile an s mit endlichem `log_return` hat **und seine
  unmittelbar vorangehende eigene Zeile genau die vorige Sitzung** (`vorherige(s, 'NYSE', false)`) ist. Damit ist
  eine in beiden Reihen fehlende Sitzung kein stiller Nachbar mehr: die Sitzung steht als unbekannt auf der Achse,
  und die Folgesitzung ist ebenfalls unbekannt (ihr `log_return` überspannt die Lücke).
- Paarrendite an s gilt, wenn beide Einzelrenditen gelten.
- Rolling-60, Forward-h, RV21, Eintritt c(t−1), „nächster Tag“ zählen **Sitzungen der Achse**; jede benötigte
  Zwischenrendite muss gelten, sonst unbekannt. Forward-Zieldatum = `verschiebe(s, h, 'NYSE')`, muss ≤ Achsenende sein.

## R2-2 Fester Historienbeginn

Geladen wird **immer die volle Historie des Paares** (`ab` = 1990-01-01; die Reihen beginnen dann bei ihrem eigenen
Start: VIX 1990, VXN 2001, OVX 2007). Rolling, expandierende Stress-Schwelle, Bedingungen, Eintritte und Sperre werden
auf der vollen Achse berechnet; **erst danach** wird der Anzeigezeitraum gefiltert (Ereignisliste, Charts, Gesamt-OLS,
Buckets, Quantile für das Regime-Badge, Residuum). Der Zeitraumschalter löst keinen neuen Ladevorgang aus, nur eine
Neuberechnung der Anzeigegrößen; Stress-/Spike-Ereignisse sind damit zeitraumunabhängig. (Gesamt-OLS, Buckets,
Badge-Quantile und Residuum sind bewusst Größen **des gewählten Zeitraums** und so beschriftet.)

## R2-3 Frische

- Erwartete letzte abgeschlossene Sitzung E: h = `heute('NYSE', Date.now())`; ist h.datum offene Sitzung und die
  New-Yorker Uhrzeit (Intl, `America/New_York`) ≥ Schlusszeit + 30 min (Schlusszeit 16:00, bei belegtem Halbtag
  `sitzungInfo(...).schlusszeit`), dann E = h.datum, sonst E = `vorherige(h.datum, 'NYSE', false)`.
- Zeilen mit Datum > E (laufende Sitzung, Intraday-Refresh schreibt sie) werden verworfen.
- Angezeigt werden getrennt: Spot-Reihe endet am …, Vol-Reihe endet am …, ausgewerteter Paartag (= letzte Sitzung
  der Achse mit gültiger Paarrendite) …, erwartet E. Ist der ausgewertete Paartag < E: Warnhinweis „Daten nicht
  aktuell — ausgewertet wird der dd.mm.yyyy“. Der Residuen-Kasten wertet **genau die Sitzung E** aus; hat E keine
  gültige Paarrendite, zeigt er „für den dd.mm.yyyy nicht bestimmbar (Grund)“ statt auf einen älteren Tag
  auszuweichen. Der Scatter-Punkt „letzter Tag“ folgt derselben Regel.

## R2-4 Python: Nightly-Phase entfernen statt Zwilling pflegen

Die Tabelle `spot_vol_beta` wird nur vom Nightly geschrieben und von **niemandem gelesen** (`fetch_spot_vol_beta`
ohne Aufrufer; die Seite rechnet selbst aus `prices`). Einen zweiten Rechenweg mit Yahoo-Schlüssen auf denselben
Vertrag zu bringen, um eine ungelesene Tabelle zu füllen, ist Pflege ohne Nutzen. Daher:
`shared/spot_vol_beta.py` löschen, Nightly-Phase (nightly_refresh.py:449ff) entfernen, `upsert_/fetch_spot_vol_beta`
in `supabase_client.py` entfernen, Eintrag in `check_db_completeness.py` entfernen (sonst wird der Check rot),
Stub in `verify_kalender_fehlerweitergabe.py` anpassen, Inventare (Produktionssperre, Schreiber-Wächter) prüfen.
Die Tabelle selbst bleibt; ein `DROP` ist eine Nutzerentscheidung (SQL-Datei wird nicht angelegt).
Damit gibt es genau eine Rechnung: `spot-vol-compute.js`; der Wächter vergleicht gegen eine unabhängige
numpy-Referenz im Wächter selbst.

## R2-5 Degenerierte Fälle

OLS: N < 3, Var(x) = 0 oder Var(y) = 0 → β, α, R², Korrelation „nicht bestimmbar“. Residuen-Kasten zusätzlich: s = 0
(auch bei perfekter Linearität) → z „nicht bestimmbar“, Rang k wird trotzdem gezählt (strikt). Rolling-OLS mit
Var(x) = 0 → unbekannt. Quantile über < 2 Werte → unbekannt. Badge-Regeln aus v2 bleiben. Alles im Wächter als Fall.

## Wächter (ergänzt)

Zusätzlich: in beiden Reihen fehlende Sitzung (Achse zeigt unbekannt, Folgesitzung unbekannt, Forward über die Lücke
unbekannt), Phantomzeile am Feiertag, Zeitraumwechsel ändert Stress-/Spike-Ereignisse nicht, beidseitig veraltete
Reihen → Warnhinweis, laufende Sitzung verworfen (feste Uhr: Sitzungstag 15:00 und 16:45 New York), s = 0, N < 3.
Der Ladepfad (`verify_seiten_kurse.py`, jsdom) prüft, dass `log_return` und `ab=1990-01-01` angefordert werden und
der Zeitraumschalter keinen neuen Abruf auslöst.

## Fragen
Erfüllt v3 die fünf Auflagen aus Runde 2? Ist R2-4 (Entfernen) vertretbar? Neue Lücken?
Antwort: Befunde (Schwere, Datei:Zeile), Urteil „tragfähig“/„nicht tragfähig“ + Auflagen.
