# Code-Abnahme Runde 2: NE/Term/Smile (Commit auf master, `git log -1`)

Runde 1 (`docs/review_prompts/2026-09-25_ne_term_smile_code.md`): FREIGABE nein. Offen waren:

1. **HOCH** — NE wurde nach dem Frische-Filter bestimmt; weggefilterte Verfälle machten einen
   späteren Verfall zum regulären NE. Umsetzung: `_enrich` bestimmt `roh_dte` aus der UNGEFILTERTEN
   Kette und übergibt ihn an `_laufzeiten_eigen`; jeder andere Verfall ist Ersatz, ≤ 10 Tage.
2. **MITTEL** — Tick-Rauschen kann das Vorzeichen drehen. Umsetzung: `shared/black_scholes.tick_unsicherheit_pts`
   (halber Tick / Vega je gewähltem 25Δ-Kontrakt, Summe), `skew_ne_richtung_unsicher = U >= |Skew|`,
   Tabelle „≈" + ±U. Messung auf 40 echten Ketten: 1 Tag Median 0,19, max 1,00 pts (XLE bei Skew
   7,15 → richtungsfest). Real markiert: nur AAPL (−0,02 ± 0,21). Die 25Δ-Auswahl liegt in
   `_waehle_delta`, geteilt mit `leg_from_prices` und `smile_from_prices` — bit-identisch auf
   574 echten Expiries.
3. **MITTEL** — Wächter-Lücken. Neu: weggefilterte NE-Verfälle, Tick-Richtung, Contango-Gleichstand,
   Term 0/1 Punkte, `renderSkewCurve` in node ausgeführt. Dabei gefunden: `_smile(None)` warf
   `KeyError` → ganzer Ticker fiel aus (behoben).

Prüfe: (a) je Punkt behoben / unvollständig / neu kaputt, (b) ob die Regel „U ≥ |Skew|" fachlich
trägt oder eine andere Form sinnvoller ist, (c) ob `tick_unsicherheit_pts` die Unsicherheit richtig
modelliert (halber Tick, Summe statt Wurzel der Quadratsumme, Vega je 1,0 Vol), (d) neue Befunde.

Werkzeug wie Runde 1 (Python-Pfad, TMP/TEMP auf `.codex_tmp`, Git-Status-Hash vorher/nachher,
Mutationstest NICHT ausführen, nichts ändern). Ausgabe: Tabelle, Antworten (b)(c), Befunde
`DATEI:ZEILE | SCHWERE | Was | Reproduktion | Vorschlag`, Exit-Codes der drei Wächter, Hash,
`FREIGABE: ja/nein` + ein Satz.
