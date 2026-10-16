# Planprüfung B3b: IV/RV-Verhältnis + neutrale Extremlisten auf /skew

Read-only, Deutsch. Bitte am Ende **FREIGABE (Plan): ja/nein** und je Befund P1/P2/P3.
Vorgeschichte: B3a ist live (`shared/skew_rang.py` = `scripts/js/skew_rang_ref.js`, Cron schreibt `rang` +
`rang_session` in `options_skew.json`, /skew und Morgen-Mail lesen nur das; Freigabe
`docs/review_prompts/2026-10-16_options_b3a_code_r2.md`). Nutzerwunsch vom 15.10.: das IV/RV-Verhältnis je Ticker und
neutrale Extremlisten („welche Ticker stehen am Rand ihrer eigenen Historie“), ohne Kauf-/Verkaufswortlaut.

## Datenlage (gemessen 16.10., lokale Kopie der Live-History)
- Live-Zeilen (`method=own_bs`, ohne `src`) tragen `iv_atm` (30-Tage-CM, eigene Inversion) und
  `vrp_pts = round((cm_iv_atm − rv_1m)·100, 2)` (`compute_options_skew.py:1289`), aber **nicht** `rv_1m` selbst.
  `rv_1m` steht nur im Snapshot (150/163 Ticker mit `iv_atm` + `rv_1m`).
- Backfill-Zeilen (`src=massive`) haben **kein** VRP (VRP-Nachrechnung ist bewusst zurückgestellt, Nutzerentscheidung
  25.09.: die neuen Backfill-VRPs lagen im Mittel bei +0,54 statt ≈ +3,7 pts — Mischungsgefahr).
- Normierte Zeilen mit VRP je Ticker: 0–4: 5 Ticker, 5–9: 6, 10–14: 24, 15–19: 128, **≥ 20: keiner.**
  Mit `MIN_NORM = 20` wäre ein IV/RV-Rang frühestens ab etwa 22.10. für die meisten Ticker rechenbar.

## Plan
### 1. IV/RV-Wert
- Snapshot je Ticker: `ivrv = cm_iv_atm / rv_1m`, nur wenn beide gültig und `rv_1m ≥ 0,01` (sonst fehlt der Wert);
  gerechnet im Cron an derselben Stelle wie `vrp_pts`, gleiche Eingänge (also gleiche Session, gleiche RV-Formel
  `shared/realized_vol.py`, 21 HT).
- History: **ab jetzt `rv_1m` in jede Live-Zeile schreiben** (neues Feld), damit die Reihe nicht aus gerundeten Größen
  zurückgerechnet werden muss.
- Für die vorhandenen Live-Zeilen ohne `rv_1m`: Vorschlag (a) **nicht** zurückrechnen — der Rang startet, sobald 20
  Zeilen mit gespeichertem `rv_1m` vorliegen (≈ Mitte November); oder (b) einmalig `rv = iv_atm − vrp_pts/100`
  ableiten (Rundungsfehler von `vrp_pts` ≤ 0,005 pts → Fehler im Verhältnis < 0,1 % bei RV ≥ 0,05), als eigener
  Reparaturlauf mit Bericht wie beim ETHA-VRP. Ich tendiere zu (a): eine Quelle, keine zweite Herleitung im Rechenkern.
  **Bitte entscheiden, ob (b) vertretbar ist**, und ob die abgeleiteten Zeilen gekennzeichnet werden müssten.
- Rang: neue Metrik `ivrv` in `rang_ticker` (gleicher Vertrag: eigenes n, letzter gültiger Wert = Session, n ≥ 20,
  Rank/Percentile wie die anderen). Nur Zeilen mit gespeichertem `rv_1m` (bei (a)). JS-Referenz gleich.
- /skew: neue Spalte „IV/RV“ (Wert mit zwei Stellen, z. B. 1,28×) und im Tooltip Rang/Percentile + n, wenn vorhanden,
  sonst „Rang ab 20 Tagen (n = 16)“. Einfarbig Gold wie die übrigen Spalten.

### 2. Neutrale Extremlisten
- Unter dem Radar ein Block „Am Rand der eigenen Historie“: je Metrik (IV-Niveau, Skew, Risk Reversal, IV/RV) die
  höchsten und niedrigsten 8 Ticker nach Percentile im gewählten Fenster, mit Wert, Percentile, n. Nur Ticker mit
  `rang` derselben Session. Überschriften „höchste / niedrigste Lage“, kein „teuer/billig/kaufen/verkaufen“.
- **Fragwürdige Tage markieren statt ausblenden** (der Skew-Ausreißerfilter, Plan v4, existiert noch nicht):
  der Cron setzt je Ticker, Fenster und Metrik `sprung: true`, wenn |x_S − x_vorher| > 5 · Median(|Δ|) über die
  Tagesänderungen des Fensters (mind. 19 Änderungen; Median = 0 → kein Urteil, Feld fehlt). `x_vorher` = der
  vorangehende gültige Wert. Listen zeigen dann „Tagessprung — Messung prüfen“ neben dem Ticker; der Ticker bleibt
  in der Liste. Zusätzlich `neu_rand: true`, wenn Percentile 0 oder 100 (neuer Extremwert im Fenster).
  Beide Felder stehen in `rang` (Python = JS-Referenz).
- DE+EN (`data-i18n`-Keys), `_JSON_VER` erhöhen.

### 3. Prüfung
- `verify_skew_rang.py` erweitert: `ivrv` mit Sollwerten, Grenzfälle (rv < 0,01, rv fehlt, ivrv nur an S−1),
  `sprung` (genau an der Schwelle, Median 0, 18 statt 19 Änderungen, Sprung an S−1 statt S), `neu_rand`.
- Mutationen (Ziel ≥ 30): Schwelle 5 → 4, `>` → `≥`, Median über Werte statt Änderungen, `x_vorher` = erster statt
  letzter, ivrv-Untergrenze weg, ivrv aus `iv` (Flügelmittel) statt `iv_atm`, gemeinsames n mit `iv`, Liste nimmt
  Rank statt Percentile, Liste ignoriert `rang_session`, Liste blendet `sprung`-Ticker aus.
- Seitenprobe: Liste und Spalte in jsdom gegen eine Fixture.

## Fragen an dich
1. (a) oder (b) für die alten Live-Zeilen?
2. Ist `cm_iv_atm / rv_1m` die richtige Paarung (30 Kalendertage gegen 21 Handelstage, wie beim VRP), oder gehört
   der Laufzeitunterschied in den Text?
3. Ist die Sprungregel (5 · Median |Δ|) als *Hinweis* tragfähig, oder erzeugt sie bei kurzen Reihen zu viele
   Markierungen? Bessere Regel bei gleicher Einfachheit?
4. Gehört die Liste in die Morgen-Mail (jetzt nicht geplant)?
5. Fehlt etwas an Zuständen (Ticker ohne Kategorie, Session-Wechsel während die Seite offen ist, Altdatei ohne
  `ivrv`)?
