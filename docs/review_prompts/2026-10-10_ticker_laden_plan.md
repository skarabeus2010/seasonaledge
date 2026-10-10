# Neue Ticker auf der Website schneller laden — Bestandsaufnahme und Plan (Runde 1)

<task>
Nutzerauftrag: „Entwickle mit Codex einen Plan, wie wir die Aufrufe von neuen Tickern auf der Website schneller
machen können.“ Du bist **Code-Assistent und Reviewer**: (A) erfasse vollständig, was beim Wechsel auf einen
neuen Ticker geladen wird; (B) prüfe und ergänze die Optionen unten; (C) empfiehl eine Reihenfolge. Read-only,
nichts schreiben. Messungen gegen die Live-Datenbank nur lesend und sparsam (öffentlicher Anon-Key aus der Seite).
</task>

## Gemessen (2026-10-10, lokal → Supabase, öffentlicher Anon-Key, nur lesend)
Abfrage wie `SA.fetchAllPrices` (`landing/js/app.js` ~Z. 746): `select=date,close,log_return,tdom,tdoy&order=date`,
1000er-Blöcke **nacheinander** per `Range`, jede Anfrage mit `Prefer: count=exact`.
| Ticker | Zeilen | Anfragen | seq. mit count | seq. ohne count | 6 parallel, 3-Jahres-Bereiche |
|---|---|---|---|---|---|
| SPY | 8 482 | 9 | 1,6 s | 2,6 s | 1,1 s |
| ^GDAXI | 16 871 | 17 | 4,8 s | 3,1 s | 4,9 s |
| ^DJI | 33 739 | 34 | 6,6 s | 4,1 s | 0,8 s |
| SAP.DE | 7 294 | 8 | 1,5 s | 0,9 s | 0,2 s |
Einzelne erste Blöcke mit `count=exact` dauerten bei einer früheren Messung **1,0–3,2 s** gegen **0,2–0,4 s** ohne,
und ^DJI lieferte einmal nur 100 Byte (Fehler). Die Werte schwanken stark (Netz/Supabase); das Muster: Zählung
kostet, Sequenz kostet. JSON ≈ 85 B je Zeile → ^DJI ≈ 2,8 MB unkomprimiert.

## Was ich im Code gesehen habe
- **Zwei Lader für dieselbe Historie:** `SA.fetchAllPrices` (Offset + `count=exact`, Cache `SA.cache` in
  **localStorage**, 15 min TTL, Schlüssel `ticker|extraFilter`) und `SA.decadeCompute.ladeVollHistorie`
  (`decade-compute.js:536`, Blättern per `date=gt.`, ohne count, eigener In-Memory-Cache `_vollCache`). Der
  Kommentar dort: `count=exact` bricht bei ^GSPC nach 28 s mit HTTP 500 ab. `mitHistorie` (Saison-Score) und
  `anomalieMitHistorie` (Radar) laden zusätzlich zur Seite → **die Historie wird auf manchen Seiten doppelt geladen**.
- 16 Seiten rufen `fetchAllPrices`, 22 Stellen insgesamt mit `ladeVollHistorie`/`mitHistorie`.
- localStorage hat meist ~5 MB je Ursprung; ein Cache-Eintrag für ^DJI wäre allein ~2,8 MB (Schreiben scheitert?
  wird es abgefangen?).
- Seit P2 (dieselbe Sitzung) schreiben die Schreiber `prices.tdom/tdoy` nach Börsenkalender; die Seiten lesen die
  Spalte heute kaum (Header-Fallback `app.js:877`).

## Optionen (bitte prüfen, ergänzen, bewerten)
- **O1 `count=exact` entfernen**, Ende über „Block < 1000“ erkennen (wie `ladeVollHistorie`). Klein, sofort.
- **O2 Ein gemeinsamer Lader** statt zwei; Seiten, Saison-Score und Radar teilen eine Ladung und einen Cache.
- **O3 Parallel laden**: Datumsbereiche (Jahresblöcke) gleichzeitig, begrenzte Parallelität (Rate-Limit 429).
- **O4 Statische Kursdateien**: der Nightly (und Intraday?) schreibt je Ticker eine kompakte Datei
  `landing/data/kurse/<ticker>.json` (spaltenweise Arrays statt Objekte, gzip über nginx, ETag, `no-cache`) —
  ein Abruf statt 9–34, kein Supabase-Weg im Browser. Frage: Frische (Intraday-Kurse), Speicher, gitignore,
  Schreibrechte (0644, Lesson v60.2), Atomizität, was bei fehlender Datei.
- **O5 Cache im Browser verbessern**: IndexedDB statt localStorage (Größe), Schlüssel mit Datenstand
  (letztes Datum / Version), ggf. nur Delta nachladen (`date=gt.<letztes gespeichertes Datum>`).
- **O6 Schrittweise anzeigen**: zuerst die letzten N Jahre zeichnen, Rest nachladen.
- **O7 Vorabladen**: beim Fokus/Hover im Ticker-Suchfeld oder für die beliebtesten Ticker.

## Auftrag A (Bestandsaufnahme)
Für jede Seite unter `landing/pages/` (und `landing/js/*`), die einen Ticker anzeigt: welche Abrufe passieren
beim Tickerwechsel (Tabelle/Datei, Filter, Anzahl, nacheinander/parallel, welcher Lader, welcher Cache), welche
davon die volle Historie laden, wo dieselben Daten doppelt geladen werden. Datei:Zeile.

## Fokusfragen
1. Welche Option bringt am meisten je Aufwand, und in welcher Reihenfolge? Was ist der kleinste sichere erste Schritt?
2. O4: tragfähig? Welche Datenmenge (370 Ticker), welche Frische-/Konsistenzregeln (gleiche Zahlen wie aus der
   Datenbank, Intraday)? Wie verhindert man, dass eine veraltete Datei still angezeigt wird?
3. O5: Ist der localStorage-Cache heute für große Ticker wirkungslos oder sogar schädlich (Quota-Fehler)?
4. Welche Messung soll das Ergebnis nachweisen (z. B. „Zeit bis erstes Chart“ je Seite und Ticker, kalt/warm),
   und wie wird sie reproduzierbar (Skript, Browser-Probe)?
5. Was übersehe ich (Rate-Limits, RLS, Supabase-Kosten, Zeilenlimit 1000, CDN/Cloudflare, Mobile)?

## Ausgabevertrag
**Urteil** (Kurzfassung) · **Bestandsaufnahme** (Tabelle) · **Bewertung O1–O7** (+ neue Optionen) ·
**Empfohlene Reihenfolge** mit Abnahmekriterien · **Befunde**. Länge nach Bedarf, Tabelle vollständig.
