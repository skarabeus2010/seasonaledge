# Code-Review B2-Nachtrag, Runde 3 — GEX-Spot + Radar-Quadranten + drei VIX-Indizes

Deine Antwort R2: `docs/review_prompts/2026-10-15_options_b2_spot_r2_antwort.md` (nein: `regularMarketTime` am
Sessiontag reicht nicht, Intraday-Zeit + nicht finalisierter Kurs würde bestehen; Wächterlücke). Code uncommittet im
Arbeitsbaum (`git diff` + `scripts/verify_radar_quadranten.py`). Read-only, Deutsch, **FREIGABE (Code): ja/nein**.

## 1. Spot-Nachweis (dein P1)
`scripts/snapshot_gex_massive.py`: neu `_sessionschluss(session)` = regulärer NYSE-Schluss als Zeitpunkt (16:00 New York;
an einem Halbtag die Schlusszeit aus `shared.sitzungen.sitzung_info`, nur bei `halbtag is True`; unbekannt → 16:00,
strenger). `_spot` verlangt `regularMarketTime` ≥ diesem Zeitpunkt (Zahl, sonst verworfen). Ein Ticker mit Handel nur am
Vormittag (Handelsstopp) fällt damit bewusst aus — konservativ, wie von dir als Option genannt.
Wächter (`verify_gex_session.py`), direkt auf `_spot` mit einer `_fetch_yahoo`-Attrappe: Normalfall 700; `adjclose`
690 → 700; Folgetagsbalken mit close 999 und letztem Handel S+1 10:00 → 700 (Sessionbalken); kein Sessionbalken,
letzter Handel am Vortag, **letzter Handel Sessiontag 14:00**, `regularMarketTime` fehlt, `close` None, letzter Handel
13:00 an einem normalen Tag → jeweils None; Halbtag 27.11.2026 (Kalender 13:00): 13:00 und 14:00 → 700.
Mutationen: Nachweis entfernt, **Nachweis nur über das Datum (deine R2-Lage)**, Halbtag ignoriert (immer 16:00), letzter
Balken statt Sessionbalken, `adjclose` statt `close` — Ergebnis siehe Nachtrag. Echter Lesetest (isolierter Container,
`--no-write`, 15.10. 14:49 UTC): alle 20 Ticker mit Spot.

## 2. Radar-Quadranten (Nutzerhinweis, Nutzerentscheidung „Richtung + Vola“)
X-Achse auf `/skew` und `/flows` = Rang von `call_iv − put_iv` (rechts Calls relativ teuer). Einheitlich: oben (teure
Vola) die teure Seite verkaufen, unten (billige) die günstige kaufen — oben links Sell Put Spread, oben rechts Sell Call
Spread, unten links Buy Call Spread, unten rechts Buy Put Spread. Vorher: `/skew` rechts vertauscht (oben „Buy Put
Spread“), `/flows` untere Zeile vertauscht, Blogtabelle DE/EN untere Zeilen vertauscht. Korrigiert in
`landing/pages/skew.html`, `landing/pages/flows.html`, Blog DE/EN (Tabelle + Erklärsatz, `updated: 2026-10-15`). Neuer
Wächter `scripts/verify_radar_quadranten.py` (Beschriftung mit Position aus beiden Seiten, X-Achsen-Definition,
Blogtabelle), am alten Stand beider Seiten rot nachgewiesen; im Gate.
Frage dazu: Ist die Lesart mit der Seitenbeschriftung „Bullish links / Bearish rechts“ auf `/skew` und der
„Angst/Gier“-Achse auf `/flows` widerspruchsfrei?

## 3. Drei Indizes in `shared/symbols.py`
`^VIX9D`, `^VIX3M`, `^VIX1D` (Kategorie Volatility, exchange CBOE → Kalender NYSE wie `^VIX`), Onboarding nach dem Deploy
per `scripts/onboard_ticker.py` auf dem Server, danach Abgleich der Yahoo-Reihen gegen die amtlichen Cboe-CSV.
Bekannt: Yahoo führt ^VIX3M ab 2006 (Cboe-Datei ab 2009, Vorläufer VXV), ^VIX1D ab 2023 (Cboe ab 2022).

Nachweise: `verify_gex_session` grün, `verify_radar_quadranten` grün, `verify_seiten_kurse` 313, `verify_seo_html` 0,
`verify_produktionssperre` 75, `verify_einbindung` 24, `verify_en` FAIL 0.

## Nachtrag
Mutationstest `verify_gex_session_mutation.py`: **29/29** erkannt (inkl. „Nachweis nur über das Datum“ und „Halbtag ignoriert“).
