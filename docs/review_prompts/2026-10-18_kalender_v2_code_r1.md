# Kalender-Umstellung V2 — Code Runde 1 (Browserkern)

Bauvorlage: [Entwurf v1](2026-10-18_kalender_v2_entwurf.md) + [v2](2026-10-18_kalender_v2_entwurf_v2.md) +
[v3](2026-10-18_kalender_v2_entwurf_v3.md), [Freigabe](2026-10-18_kalender_v2_entwurf_v3_antwort.md). Arbeitsbaum
(nicht committet, `git diff` + neue Dateien). Read-only.

<task>Setzt der Code die Bauvorlage vertragsgerecht um? Prüfe am Code und durch Ausführen der Wächter. Insbesondere:
bleibt `alt` überall unverändert, und gibt es unter `kalender_v1` einen Weg zu einem stillen Falschergebnis?</task>

## Umfang
- **Schritt 0 (live, `0c3a545`/`1fdd32f`):** gzip im Block `location ~* ^/landing/.+\.(css|js)$` — HTTP-Nachweis
  `Content-Encoding: gzip` auf `app.js`, `app.css`, `boersenkalender.js`.
- **Schritt 1 — Momentaufnahmen `alt`:** `scripts/holidays_alt_momentaufnahme.py` + `scripts/js/holidays_alt_probe.js`
  → `scripts/fixtures/holidays_alt.json` (840 Gruppen, je Zone UTC/New_York/Kiritimati; die alte Datei ist NICHT
  zeitzonenfrei: in Kiritimati fehlt der 31.12.1994, 1994/95 weichen ab). Converter: `scripts/js/converter_probe.js`
  → `scripts/fixtures/converter_alt.json` (jeder Tag 2023-12-25…2028-01-05 + Randtage, je Zone; gemessen: alt
  rechnet in New York CDOY in der Sommerzeit um 1 zu klein, in Kiritimati zählt der 03.07.2026 als Handelstag).
  Gegenprobe der Momentaufnahme: drei Mutationen der alten Datei, eine äquivalente (10→9-Tage-Grenze: maximal
  6 geschlossene Tage am Stück) durch Grenze 5 ersetzt → rot.
- **Schritt 2 — Fassade** (`landing/js/holidays.js`, IIFE am Ende): nur unter `kalender_v1`, reine Delegation,
  werfende Getter für `_nyse/_xetra/_lse/_cache/_getCachedMap/_NYSE_SONDER/_XETRA_SONDER`.
- **Schritt 3 — Einbindung:** `boersenkalender.js` vor `holidays.js` auf 26 Seiten + Converter;
  `scripts/fixtures/einbindung_manifest.json`; `verify_boersenkalender_js.isolation_scan` und `verify_einbindung.seiten`
  auf den Einbindungsvertrag umgestellt (Manifest, Reihenfolge, Generatoren, Lesefehler; `seo/tools` jetzt in
  `html_dateien`).
- **Schritt 4 — Fehlerfänger** in `dashboard` (5), `monatszyklus` (1), `watchlist` (4) werfen unter `kalender_v1`
  weiter; Inventar `scripts/fixtures/kalender_v2_inventar.json` (31 Stellen: V3 9, V4 15, V5 2, Aufräumen 5).
- **Schritt 5 — Header** `SA._headerKalenderV1` in `app.js` (+ 4. Parameter `kalenderTicker`, `sektor-rotation`
  übergibt den ersten Sektorticker), EN-Schlüssel `app.hdr_*`, `_JSON_VER` v22. TWOY-Summe aus dem ISO-Jahr der
  Woche (alt: 01.01.2027 = „53/52“).
- **Schritt 6 — Converter** (`seo/tools/trading-day-converter.html`): Bootstrap + `methode.js` + Bundle, Börsenwahl
  (unter `alt` verborgen), `kalender_v1`-Zweig vor dem unveränderten alten Rechner, Texte ohne feste Grenzen.
  Deploy: `git checkout -- seo/tools/` vor dem Vorspulen (sonst bricht die Sauberkeitsprüfung von
  `pruefe_commit.sh` am Folgedeploy an der gesetzten Kennung), Cache-Buster in `inject_credentials.sh` auf
  `seo/tools/`.
- **Wächter** `scripts/verify_holidays_fassade.py` (242 Prüfungen, ~1 min): alt = Momentaufnahme, Delegation
  (602 247 Vergleiche), 86 Sollfälle mit Quelle durch die Fassade, Fehlervertrag B5 (52 Fälle), 57 Statusfälle,
  Header (16 Fälle, Werte mit `numpy.busday_count` nachgerechnet), Converter alt + 10 Fälle, sechs Zeitzonen,
  Inventar. Mutationstest `scripts/verify_holidays_fassade_mutation.py` (18 + 2 Gegenproben).

## Offen (bewusst, mit Grund)
- **Handgeschriebene Monatslisten je Börse** (v2 B4.2, v3) fehlen noch: sie verlangen das Ablesen der veröffentlichten
  Börsenkalender je Börse (Quelle als Archivfassung wie bei den NYSE-Halbtagen). Bis dahin trägt Ebene 2 die 86
  Sollfälle mit Quelle; der Posten steht vor V9 auf der Liste. Ist das als Restposten tragbar, oder Bedingung für V2?
- **jsdom-Proben auf echten Seiten** (Header in allen 23 Header-Seiten, A→B→A-Tickerwechsel) noch nicht gebaut;
  Header und Converter sind über die herausgelöste Funktion bzw. ein Minimal-DOM geprüft.
- NYSE vor 1971 ist `ungeprueft`; dabei aufgefallen: 1960 Presidents Day am 15.02. (damals 22.02.) und kein
  Wahltag-Schluss (08.11.1960, belegt in `election_calendar_exceptions.json`) — eigener Posten, nicht V2.
- Gate-Schritt für `verify_holidays_fassade.py` wird mit dieser Runde eingetragen.

## Ausgabevertrag
**Urteil** · **Befunde** (P1/P2 mit Datei:Zeile) · **Antworten zu „Offen“** · **Auflagen**. ≤ 40 Zeilen.
