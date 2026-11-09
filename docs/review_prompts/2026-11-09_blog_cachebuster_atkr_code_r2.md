# Code-Review Runde 2: Blog-Cache-Buster, ATKR, robots.txt

Read-only, Deutsch, **FREIGABE (Code): ja/nein**, Befunde P1/P2/P3. Runde 1:
[2026-11-09_blog_cachebuster_atkr_code.md](2026-11-09_blog_cachebuster_atkr_code.md) — nicht freigegeben (P2 Watchlist,
P3 Query-Formen). Code uncommittet (`git diff`).

## Umgesetzt
- **P2:** `shared/daily_report.py::fetch_watchlist_for_email` filtert `AUSGESCHIEDEN` VOR dem Limit und vor
  Historienabruf/Signalen; die gespeicherte Watchlist bleibt unverändert. Probe mit echter Funktion und Attrappen-RPC
  (ATKR + SPY): Zeilen `['SPY']`, Historie nur für SPY; Gegenprobe mit leerem `AUSGESCHIEDEN` → ATKR erscheint (rot).
- **P3:** `deploy/release_setzen.py` — `ASSET` erfasst jede Query (`\?[^"]*`); ersetzt wird nur bei fehlender oder
  schlichter `?v=[A-Za-z0-9%]*`-Query (`ASSET_VERSION`), jede andere Form bleibt stehen und `assets_pruefen` meldet sie
  (Prüfung: Query ≠ `?v=<wert>`). Neuer Fall in `verify_einbindung.py` (`?v=1.2&amp;x=1` bleibt unverändert, Exit 1,
  genannt) → 30/30; neue Mutation „fremde Query-Form wird überschrieben“ → 29/29 gefangen, Projektbaum unverändert.

## Im vollen Gate gefunden (nicht von Runde 1)
`verify_holidays_fassade` war rot: die eingefrorene Momentaufnahme `scripts/fixtures/holidays_alt.json` hasht
`detect()` über die LIVE `landing/data/tickers.json` — ATKR fehlt, Prüfsumme verschoben. Nachgewiesen: die Probe mit
`tickers.json + ['ATKR']` ergibt exakt die eingefrorene Prüfsumme (`ca2414196b8e0858177e2803`). Die Momentaufnahme
darf nicht neu erzeugt werden (nur aus dem Stand vor der Fassade). Lösung: neue Fixture
`scripts/fixtures/holidays_alt_ticker.json` (373 Ticker = Eingabeliste zum Zeitpunkt der Aufnahme),
`scripts/js/holidays_alt_probe.js` liest sie statt `tickers.json` → 840 Gruppen, 0 Abweichungen.
Der Live-Vergleich Fassade ↔ Börsenkalender (`holidays_fassade_probe.js`) liest weiter `tickers.json` — gewollt.
Frage: Gibt es weitere eingefrorene Momentaufnahmen, die eine live Tickerliste als Eingabe lesen
(`kalender_momentaufnahme`, `opex_momentaufnahme`, `header_alt_seiten`, `converter_alt`, Ticker-Börse-Fixture)?

Übriges Gate lokal: grün bis auf die bekannten Windows-Fälle (flock: briefing_versand, skew_historie_sperre,
produktionssperre) und `build_boersenkalender_js --pruefen` (vergleicht mit HEAD, grün nach dem Commit).
`build_en --write`, `blog_builder --build`, SEO-Builder, `verify_seo_html`: 0 Fehler; robots enthält
`Disallow: /landing/data/*/$`.
