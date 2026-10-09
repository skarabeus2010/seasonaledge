# Code-Review Saison-Score D3/D4 + Migration — Runde 2

Read-only, Repo `C:\dev\Seasonaledge`, uncommitteter Arbeitsbaum. Runde 1: Frage
`docs/review_prompts/2026-10-09_saison_score_d3d4_runde1.md`, deine Antwort
`docs/review_prompts/2026-10-09_saison_score_d3d4_antwort1.md` (12 Befunde, FREIGABE nein).
Deutsch, echte Umlaute. Prüfe jede Korrektur am Code (Datei:Zeile), melde neue Befunde mit Fehlerfall und Schwere,
am Ende **FREIGABE: ja/nein**.

## Korrekturen

1. **Vollhistorie:** `SA.decadeCompute.mitHistorie(rows, ticker)` lädt jetzt immer die volle Historie über
   `SA.fetchAllPrices(ticker)` ohne Datumsfilter (derselbe Cache-Schlüssel wie Watchlist), führt mit den
   übergebenen Zeilen zusammen. Aufrufer in `dashboard.html` und `ki-saisonalitaet.html` ohne Jahresparameter.
2. **Ladefehler laut:** `mitHistorie` lehnt bei Fehler oder leerer Antwort ab; die Aufrufer zeigen
   `grund_code: 'ladefehler'` („Kurse konnten nicht geladen werden", EN-Schlüssel `scan.g_ladefehler`).
3. **Resume/Protokoll:** `saison_score_betrieb.schreibe` schreibt ZUERST das Protokoll, DANN den Scanner. Resume
   überspringt nur Ticker mit Scanner-Zeile von heute — die gibt es nur, wenn das Protokoll vorher erfolgreich war
   (oder schon existierte).
4. **Nightly-Fehler im ganzen Tickerpfad:** leerer Download, leere Vorverarbeitung, Kurs-Upsert-Fehler (dann
   `continue`, kein Scanner-Eintrag aus alten Kursen) und äußere Ausnahmen landen in `ticker_fehler` →
   `_FEHLGESCHLAGEN` „Ticker-Refresh (…)".
5. **Daily:** `_candidate_passes` verlangt `status == 'ok'` und `score is not None`; Kandidaten ohne ein einziges
   auswertbares TDOM-Fenster (alle `count` leer) fallen raus.
6. **Fallzahl:** Warum-Zeile „(je Fenster mind. n=…)".
7. **Health-Check:** Check 4 filtert `methode = saison_v1`.
8. **Scanner-Teilstand:** neue Karte „Im Lauf fehlend" mit Zahl und Liste (erste 12 + Rest im Tooltip) als
   Differenzmenge `tickers.json` minus Zeilen des Laufs; Abdeckung „x von y verarbeiteten · z im Universum".
9. **Abweichungslog:** `schreibe` liest vor dem Protokoll-Insert den bestehenden Eintrag (methode, ticker, as_of)
   und gibt Abweichungen in `kurse_hash/status/score/code_version` zurück; Nightly und Full-Scanner loggen sie als
   Warnung (erster Eintrag bleibt).
10. **Watchlist:** Grund der Nichtberechenbarkeit sichtbar; vier Bausteine + Musterkonformität im Tooltip.
11. **llms.txt-Generator:** „KI-Composite-Score" und „270+" ersetzt.
12. **Full-Scanner:** Exit 2 nur, wenn weder berechnet noch als nicht berechenbar geschrieben wurde.

Bewusst nicht geändert: „Bullish-Bias" in den Strategie-Signalen der Daily (anderes Feature, nicht der Score);
Videoskript (Nutzerentscheidung); Weekly behandelt einen Abruffehler weiter als leere Liste, der Versand bricht
dann mit „kein top_ki" ab (`scripts/weekly_newsletter.py:148`) — bitte prüfen, ob das reicht. Parallelbetrieb
alter/neuer Writer: nach dem Deploy existiert kein alter Writer mehr (Streamlit abgeschaltet, alle Writer im Image);
Migration wird VOR dem Deploy ausgeführt — bitte prüfen, ob im Fenster Migration→Deploy ein alter Lauf eine neue
Zeile überschreiben kann (nach meinem Verständnis nein, weil vor dem Deploy keine neue Zeile existiert).
