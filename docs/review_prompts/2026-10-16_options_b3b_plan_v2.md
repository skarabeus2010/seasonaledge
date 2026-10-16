# Planprüfung B3b, Runde 2: IV/RV-Verhältnis + neutrale Extremlisten

Deine Antwort R1: `docs/review_prompts/2026-10-16_options_b3b_plan_antwort1.md` (nein, drei P2, ein P3). Plan R1:
`…_b3b_plan.md`. Read-only, Deutsch, **FREIGABE (Plan): ja/nein**. Hier nur die Änderungen gegenüber R1; alles
Übrige gilt unverändert.

## Entscheidung Frage 1: Variante (a)
IV/RV-Wert sofort im Snapshot; die History bekommt ab jetzt `rv_1m` je Live-Zeile; der Rang zählt nur Zeilen mit
gespeichertem `rv_1m`. Keine Rückrechnung aus `vrp_pts`, kein Browser-Rückfall aus IV/VRP. Das Startdatum des Rangs
ergibt sich aus 20 gültigen Beobachtungen, kein Termin wird versprochen.
Eingangsprüfung `ivrv`: `cm_iv_atm` und `rv_1m` endlich, numerisch, kein bool, `cm_iv_atm > 0`, `rv_1m ≥ 0,01`
(genau 0,01 gilt). Nur `cm`/`cm_extrap`, kein Frontmonat-Rückfall. Tooltip: „Annualisierte ATM-IV für 30
Kalendertage / annualisierte realisierte Volatilität der vergangenen 21 Handelstage.“

## Zu P2-1: `neu_rand` aus den Werten, nicht aus dem Percentile
`neu_rand = "hoch"`, wenn `x_S > max(Vorwerte)`, `"tief"`, wenn `x_S < min(Vorwerte)`, sonst fehlt das Feld.
Gleichstand ist kein neuer Rand. Vorwerte = die gültigen Werte des Fensters vor S (dieselben wie für das Percentile).
Tests: konstante Reihe (kein Rand, Percentile 0), wiederholtes Minimum/Maximum, langes Fenster mit rundungsbedingter
100 bei höherem Vorwert.

## Zu P2-2: Verfügbarkeit als eigener Block, `rang` bleibt unverändert vollständig
Neu neben `rang` im Snapshot: `rang_status = {ticker: {fenster: {metrik: {"n": k, "status": s}}}}` für jede Metrik,
die **keinen** Rang bekommt, mit `s` ∈
- `zu_kurz` (letzter gültiger Wert = S, aber n < 20; `n` = gültige Beobachtungen),
- `kein_wert` (kein gültiger Wert an S; `n` = gültige Beobachtungen davor),
- `gesperrt` (Duplikat sperrt den Ticker; dann ein Eintrag `{"*": {"status": "gesperrt"}}` je Fenster).
Ticker ohne jede normierte Zeile fehlen in beiden Blöcken. `rang`-Einträge bleiben wie in B3a (Mail-Leser und /skew
unverändert; Regressionstest: Mail-P-Wert und /skew-Spalten mit der erweiterten Datei identisch zur B3a-Datei).
/skew-Text: „Rang ab 20 gültigen Beobachtungen (n = 16)“, „kein Wert zur Session“, „Historie gesperrt (Prüfung)“.

## Zu P2-3: „Sprung zum letzten gültigen Wert“
Umbenannt. Definition: gültige Beobachtungen des Fensters x_1…x_S in Datumsfolge; Änderungen
d_i = x_i − x_{i−1} zwischen **aufeinanderfolgenden gültigen Beobachtungen**, **einschließlich** der aktuellen
d_S = x_S − x_vorher. `sprung = true`, wenn mindestens 19 Änderungen vorliegen (d. h. n ≥ 20), Median(|d|) > 0 und
|d_S| > 5 · Median(|d|). Median = 0 → Feld `sprung_beurteilbar: false`; sonst Feld fehlt bei `false`. Ausgabe dazu
`vorher_datum` (Datum von x_vorher), damit die Seite „seit 12.10.“ zeigen kann, wenn es nicht die Vorsession ist.
Text: „Sprung zum letzten gültigen Wert — Messung prüfen“. Keine Behauptung einer kalibrierten Ausreißererkennung.
Gemessen auf der Session 15.10. (deine Zählung): 3–11 von ~150 Tickern je Metrik und Fenster.

## Zu P3: Listen
- Sortierung deterministisch: Percentile (hoch: absteigend, tief: aufsteigend), dann Tickersymbol aufsteigend.
- Höchstens 8 je Seite; nur Ticker mit vollständigem Rangeintrag der Metrik und `rang_session = session`. Bei weniger als
  16 Kandidaten wird die tiefe Liste nur aus Tickern gebildet, die nicht in der hohen stehen (keine Überschneidung).
- Hinweis über dem Block: „Relative Lage in der eigenen Historie des gewählten Fensters — Spitzenlisten, kein Signal.“
  Ein Ticker mit `neu_rand` bekommt „neues Hoch/Tief im Fenster“.
- Metriknamen: „IV der 25Δ-Flügel (Mittel)“ statt „IV-Niveau“; IV/RV ausdrücklich „ATM-IV / RV“. Werte: RR und IV
  werden ×100 als Volapunkte gezeigt (intern dezimal), Skew in Punkten, IV/RV als „1,28×“.
- Sortiert wird immer nach Percentile; der Rank/Percentile-Schalter ändert die Listen nicht.
- Kategorie-Filter gilt für die Listen; ohne Kategorie nur unter „Alle“.
- Fenster-, Kategorie- und Sprachwechsel rendern Listen und Tooltips neu.
- IV/RV-Liste im Aufbau leer → Hinweis „Rang im Aufbau — noch kein Ticker mit 20 gültigen Beobachtungen“.

## Zu Frage 5: Session-Wechsel
Die Seite lädt den Snapshot einmal; angezeigt wird „Datenstand Session 2026-10-15“ (wie bisher im Kopf, jetzt auch über
den Listen). Kommt später ein Refresh, ersetzt er Snapshot, `rang`, `rang_status` und Listen in einem Schritt.

## Prüfung (ergänzt)
`verify_skew_rang.py` + JS-Referenz: die drei P2-Gegenbeispiele, RV exakt 0,01 / 0,0099, ungültige Typen (bool,
String, NaN, Inf), `rang_status` aller drei Zustände, `vorher_datum` bei Lücke, Median 0, n = 19 vs. 20.
Seitenprobe: Listen-Gleichstände, Überschneidung bei kleinem Universum, zweiter Snapshot im selben DOM (keine alten
Einträge bleiben stehen), Schalter ändert Listen nicht, Kategorie-Filter, Altdatei ohne `ivrv`/`rang_status`.
Mutationen gezielt auf diese Verletzungen (u. a. `neu_rand` aus Percentile, `≥` statt `>` an Rand/Schwelle, Median ohne
aktuelle Änderung, `vorher_datum` = Vorsession statt letzter gültiger Wert, Liste nach Rank, Überschneidung zugelassen,
Status `zu_kurz` statt `kein_wert`, ivrv mit Flügel-IV).
