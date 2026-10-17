# Codex-Review: /skew überarbeitet (2026-10-17, Runde 1)

Du prüfst einen Diff an `landing/pages/skew.html` (+ `landing/i18n/en.json`, `landing/js/i18n.js`, Wächter). Nur lesen,
nichts ändern. Diff: `git diff HEAD -- landing scripts` im Arbeitsbaum.

## Nutzerentscheidungen (nicht zur Diskussion)
1. Radar und Tabelle fest auf **1 Jahr + Percentile**; die Schalter Fenster (3M/6M/1J) und Methode (Rank/Percentile)
   sind entfernt. Der Cron (`shared/skew_rang.py`) liefert weiter alle Fenster und Rank — die Seite liest nur `365`/`pctl`.
2. Standardkategorie „Alle“ statt „Mag7“.
3. Quellenhinweise entfernt (Vol-Trigger-Note „Quelle: EOD-GEX aus Yahoo…“ war ohnehin falsch, GEX kommt aus Massive;
   `skew.source` unter der Tabelle).
4. Unter dem Radar eine Zeile „Letzte Aktualisierung: <Last-Modified der options_skew.json>, Daten der Session …,
   a von b Tickern im Radar“ + aufklappbar die fehlenden Ticker mit Grund (gescheitert aus `coverage.failed`, zu kurz
   aus `rang_status`, sonst „keine 30-Tage-Messung zur Session“).
5. Vol-Trigger-Karte unter Radar/Verlauf/Smile verschoben; Meta/OG/JSON-LD/FAQ ohne „gratis“ und „IV-Rank“.
6. Kacheln (`.sk-grid`, 2 Spalten, unter 820 px eine): Smile | Markt-Kontext, VRP | Vol-Trigger; VRP scrollt in der
   Kachel (max-height 620 px). Jede Kachel unter dem Radar nennt die aktive Kategorie + Anzahl (`_setCatTag`).
7. Block „Am Rand der eigenen Historie“: „79 %“ mit Tooltip statt „P79“, „182 Tage“ statt „n 182“, Kopfzeile, die
   Markierungen (neues Hoch/Tief, Sprung) als zweite Zeile unter dem Ticker statt eigener Spalte, 2×2-Raster
   (vorher liefen die Tabellen mit `min-width:440px` in 320-px-Spalten ineinander).

## Prüffragen
1. Liest irgendein Pfad der Seite noch Rank oder ein anderes Fenster als 365 (Radar, Tabelle, Extremlisten,
   Call-/Put-Ansicht, Tooltips)? `_rangText` zeigt bewusst „Rank · Percentile · n“ im Tooltip.
2. Zeile unter dem Radar: stimmen Zähler und Fehlliste je Kategorie und je Ansicht (rr_iv nutzt rr+iv, cs_ps zeta)?
   Wird ein Ticker doppelt gezählt (failed UND in tickers)? Was zeigt sie, wenn `rang_session ≠ session` (SKEW_RANG null)
   — sind dann alle Ticker „ohne Wert“ mit einem irreführenden Grund?
3. `Last-Modified`: richtiger Zeitpunkt (nginx liefert mtime der Datei), Formatierung DE/EN, Rückfall ohne Header.
   Zeigt die Zeile nach `sa:i18n-bereit` englisch (wird `renderQuadStand` neu gezeichnet)?
4. Kategorie-Rückfall: vorher fiel eine unbekannte Kategorie auf die erste der Liste zurück, jetzt auf „Alle“ — ok?
5. Wächter: `verify_skew_rang.py` (Seitenteil), `verify_skew_rang_mutation.py` (neue Mutationen: Rank statt Pctl,
   3-M-Fenster, Fehlliste leer, gescheiterte zählen nicht), `probe_skew_sprache.js` (Rank-Fall → Darstellungs-Schalter),
   `probe_skew_tabelle.js`. Fängt ein Test die Fehlerklasse wirklich, oder ist eine Mutation äquivalent?
6. EN: fehlt ein Schlüssel, steht irgendwo noch „IV Rank … window can be switched“, ist `_JSON_VER` erhöht?

Antwort: Befunde mit Datei:Zeile und Schwere, am Ende **FREIGABE** oder **KEINE FREIGABE**.
