# Kalender-Umstellung V2 — Entwurf v1 (Browserkern: Fassade, Header, Converter, vor dem Code)

Plan: [P3/P4-Plan v9](2026-10-11_kalender_p3p4_plan_v9.md) (V2 = P3a Fassade, P3b Header, P3e Converter), Verträge
B1/B5 und Prüfplan C in der [Matrix-Antwort](2026-10-11_kalender_p3p4_matrix_antwort1.md). Vorgänger live: V1a–V1d
(Produktionssperre, Releasekennung, Ereigniskatalog, Produkttermine, Halbtage, Sitzungshelfer). Read-only.

<task>Ist der Entwurf als Bauvorlage für V2 tragfähig und vertragsgerecht (B1, B5.2/B5.8, C P3a/P3b/P3e)? Welche
Aufrufer, Rückgabeformen oder Fallen fehlen?</task>

## Bestand (gemessen 2026-10-18)
- `landing/js/holidays.js` (`SA.holidays`) ist der Kalender von **26 Seiten**. Öffentliche API: `detect`, `get`,
  `getMap`, `isTradingDay`, `nthTradingDay`, `lastTradingDay`, `nthTradingDayOfYear`, `nextTradingDay`; Helfer
  `easter`, `goodFriday`, `easterMonday`, `whitMonday`, `thanksgiving`, `_nthDow`, `_lastDow`, `_ds`, `_NYSE_SONDER`.
  Eigene Regeln nur für NYSE/XETRA/LSE, sonst `'NONE'` (= jeder Tag offen).
- **Aufrufer** (außerhalb `holidays.js`, ohne `landing/en/`): `isTradingDay` 29 · `detect` 20 · `get` 11 · `_nthDow` 8 ·
  `lastTradingDay` 6 · `nthTradingDay` 4 · `_ds` 4 · `thanksgiving` 3 · `nextTradingDay` 3 · `goodFriday` 3 ·
  `nthTradingDayOfYear` 1 · `getMap` 1 · `easter` 1 · `_lastDow` 1 · `_NYSE_SONDER` 1 — in `app.js` (Header),
  `strategy-compute.js`, `backtest-engine`, `dashboard`, `feiertage`, `monatszyklus`, `opex`, `plain-vanilla`,
  `tdom-analyse`, `vixpiration`, `watchlist`. Vollständige Liste mit Datei:Zeile: Anhang A.
- **`detect` gegen die eine Zuordnung** (`SA.boersenkalender.boerse` = `symbols.get_exchange_for_holidays`), alle 373
  Ticker aus `tickers.json`, 0 Zuordnungsfehler:

  | alt → neu | Ticker | Offenheit verschieden 2000–2026 (Tage) |
  |---|---|---|
  | NYSE → NYSE | 270 | 0 |
  | XETRA → XETRA | 43 | 0 |
  | NONE → CRYPTO | 6 | 0 |
  | NONE → FOREX | 11 | 2 818 (Wochenenden) |
  | LSE → LSE | 3 | 36 (Ersatztage, Jubiläen) |
  | NYSE → EURONEXT/MILAN/SIX/STOCKHOLM/OSLO | 21/4/6/3/1 | 247/299/350/369/364 |
  | NYSE → TSE/HKEX/KRX | 1/1/1 (^N225, ^HSI, ^KS11) | 629/368/461 |
  | NYSE → XETRA | 2 (ENR.F, RHM.F) | 290 |

  41 Ticker rechnen heute mit dem NYSE-Kalender, 11 Forex-Paare mit 7 Tagen.
- **Header** (`SA.renderTradingDayHeader`, `app.js:780`): Browserdatum (`new Date()`, lokale Zone), TDOM/TDOY durch
  Tagesschleife über `isTradingDay`; an geschlossenen Tagen **ersetzt** die letzte DB-Zeile beide Zähler (Quelle des
  „TDOM 20/20“ am Monatsanfang: der Zähler des Vormonats neben der Summe des neuen Monats). `detect('')` → NYSE;
  `sektor-rotation` übergibt „n Sektoren“ als Ticker.
- **Converter** (`seo/tools/trading-day-converter.html:237`): eigene NYSE-Feiertagsliste 2024–2027, keine Börsenwahl,
  `toISOString` auf lokalem Datum.
- **`boersenkalender.js`**: 509 434 B, gzip 53 423 B. Daten: `ereignisse` 384 KB, `schliessungen` 125 KB.
  ⚠️ **nginx liefert JS/CSS heute unkomprimiert**: der Regex-Block `location ~* ^/landing/.+\.(css|js)$`
  (`deploy/nginx.conf:165`) gewinnt gegen den Präfixblock `/landing/` mit gzip und hat selbst kein `gzip`
  (geprüft: `Content-Length: 509463`, kein `Content-Encoding` trotz `Accept-Encoding: gzip`).

## Vorschlag
### 1. Fassade `SA.holidays` (P3a)
Ein Verzweigungspunkt je öffentlicher Funktion, gelesen aus `SA.kalenderMethode` (unveränderlich, `methode.js`):
- **`alt`:** der heutige Code, **unverändert** (Wörtlichkeit per eingefrorener Momentaufnahme, s. Prüfung).
- **`kalender_v1`:** reine Delegation an `SA.boersenkalender`, keine eigene Regel:

  | Fassade | `kalender_v1` | Abweichung von `alt`, gewollt |
  |---|---|---|
  | `detect(t)` | `boerse(t)` | neues Alphabet (13 Börsen + CRYPTO/FOREX statt `NONE`); leerer/unbekannter Ticker → **Fehler** (B1.7) |
  | `isTradingDay(ds, b)` | `istHandelstag(ds, b)` | `b = 'NONE'` → Fehler (keine stille Offenheit) |
  | `get(j, b)` | `feiertagsmenge(j, b)` | = Python `get_holidays` (inkl. Wochenenddaten) |
  | `getMap(j, b)` | aus `get` | — |
  | `nthTradingDay(j, m, n, b)` | `nteImMonat` | `n < 1` → Fehler statt `null` |
  | `lastTradingDay(j, m, n, b)` | `nteVonHintenImMonat` | `n < 1` → Fehler; `n` fehlt → 1 wie heute |
  | `nthTradingDayOfYear(j, n, b)` | `nteImJahr` | `n < 1` → Fehler |
  | `nextTradingDay(j, m, d, b)` | `naechste(ds, b, true)` | keine 10-Tage-Grenze, am Kalenderende Fehler (B5.8) statt Rückgabe des Ausgangsdatums |

  Datumsarithmetik ohne Schließungsregel (`easter`, `goodFriday`, `easterMonday`, `whitMonday`, `thanksgiving`,
  `_nthDow`, `_lastDow`, `_ds`, `_pad2`) bleibt in beiden Methoden (Matrix A: „Wochentags-/Osterarithmetik darf
  Helfer bleiben“). `_NYSE_SONDER`/`_XETRA_SONDER` und `_nyse/_xetra/_lse` laufen **nur** unter `alt`; ihr
  einziger Fremdleser (`strategy-compute.js:335`, NYSE-Feiertage ohne Sonderschließungen) wird in V3 auf
  `ereignisse(j, 'NYSE')` mit `art` umgestellt — bis dahin liefert die Fassade unter `kalender_v1` dort einen
  Fehler, den der Einbindungswächter vor V9 als offen meldet.
- **Folgen des neuen Alphabets** (Namen fließen weiter): `watchlist.html:316` (`NONE` → `NYSE`),
  `strategy-compute.js:823` (Zeitzone nur NYSE/XETRA/LSE), `:900` (`NONE` → NYSE), `:1042` (`_geprueft` nur
  NYSE/XETRA), `dashboard.html:1297` (Namen nur NYSE), `plain-vanilla.html:611`, die `ex === 'NONE'`-Abkürzungen in
  `dashboard`/`monatszyklus` und die `catch → 'NONE'`-Zweige. **Nicht in V2 geändert** (gehören zu V3/V4/V5), aber in
  V2 als Inventar mit Phase festgehalten; ein neuer Wächterteil meldet jede Stelle, die unter `kalender_v1` einen
  Namen aus dem alten Alphabet erwartet, als „offen bis Phase X“ — vor V9 muss die Liste leer sein.
  Insbesondere: `catch(e){ ex='NONE' }` + `ex === 'NONE' || …` würde unter `kalender_v1` einen Zuordnungsfehler in
  „jeder Tag offen“ verwandeln, wenn die Fassade `'NONE'` noch annähme — deshalb wirft `isTradingDay(…, 'NONE')`.

### 2. Header (P3b)
Unter `kalender_v1`: Börse = `boerse(ticker)`; „heute“ = `heute(boerse, Date.now()).datum` (Börsenzone, CRYPTO/FOREX
UTC, B1.5), Datumsanzeige dieses Börsendatums statt des Browserdatums; Zähler aus `nummern([heute], boerse)`:
offen → `tdom/Monatssumme`, geschlossen → kumulierte Vorwärtszahl (NYSE 01.08.2026 = TDOM 0, TDOY 145, B1.3/B1.4)
plus Kennzeichen „geschlossen“. **Keine DB-Zeile mehr** (`rows` wird unter `kalender_v1` ignoriert). Kalenderstatus
`annahme`/`ungeprueft` sichtbar, Konvention CRYPTO („täglich“)/FOREX („Mo–Fr“) benannt (B1.6/B1.8/B1.10).
Ticker fehlt oder nicht zuordenbar → Header zeigt den Fehler statt NYSE. Sektorkorb: Aufrufer übergibt den
Referenzticker (`SPY`) und der Header nennt ihn („Kalender: SPY/NYSE“). Monats-/Jahressummen = Länge von
`sitzungen(Monats-/Jahresanfang, -ende)`. Neue i18n-Schlüssel DE/EN (`hdr.geschlossen`, `hdr.konvention_*`,
`hdr.status_*`, `hdr.kalender_von`), `_JSON_VER` erhöhen. Testbarkeit: injizierbare Uhr `SA.__uhr` (nur Tests).

### 3. Converter (P3e)
Eigene Feiertagsliste raus, `boersenkalender.js` eingebunden, Börsenwahl (alle 13 + CRYPTO/FOREX, Vorgabe NYSE),
Rechnung ausschließlich über `nummern`/`sitzungen`, Datum aus dem Eingabefeld als ISO-Zeichenkette (kein `Date`).
Die Seite hat keine Methodenkennung (SEO-Builder, nicht `landing/`) — Vorschlag: sie wechselt **mit V9** (zweiter
Zweig wie die Fassade, Schalter über `methode.js`, das dafür eingebunden wird), nicht vorher.

### 4. Einbindung und Größe
- `boersenkalender.js` auf allen 26 Seiten mit `holidays.js` **vor** `holidays.js` einbinden (Releasezeile hat er
  schon; alle 23 Header-Seiten sind darunter, `index.html`/`embed.html` nutzen weder Header noch `holidays.js`).
  Unter `alt` ungenutzt, aber geladen —
  damit V9 nur die Methode wechselt und die jsdom-Proben in V2 beide Zweige auf den echten Seiten fahren.
- **Voraussetzung:** gzip im Block `location ~* ^/landing/.+\.(css|js)$` (eigener kleiner Schritt vor V2, gleiche
  Direktiven wie im `/landing/`-Block). Damit 53 KB statt 509 KB je Erstaufruf (danach ETag/304).
- Kein Schnitt je Börse: die Fassade ist synchron, ein Tickerwechsel auf eine andere Börse bräuchte sonst eine
  asynchrone Nachladung in 29 synchronen Aufrufstellen. Optional später: Rechenbereich der Daten von 1885 auf das
  erste Kursjahr kürzen (eigene Messung, nicht V2).
- `verify_einbindung.py` erweitern: Reihenfolge `methode.js` → `boersenkalender.js` → `holidays.js` → Verbraucher
  auf jeder Seite mit `holidays.js`, generiertes EN eingeschlossen.

## Prüfung
- **Momentaufnahme `alt`** (vor dem ersten Codeschritt eingefroren, `scripts/fixtures/holidays_alt.json`): alle
  öffentlichen Funktionen und Helfer der heutigen `holidays.js` für NYSE/XETRA/LSE/NONE 1990–2035 und `detect` für
  alle Ticker + Randfälle (`''`, `^FOO`, `X.YY`). Fassade unter `alt` = Momentaufnahme **wörtlich**.
- **`kalender_v1` gegen eine unabhängige Referenz:** Python `shared.sitzungen`/`handelstag_nummern` und
  `symbols.get_exchange_for_holidays` über alle 13 Börsen + CRYPTO/FOREX, jeder Tag 1990–2035, dazu
  handgeschriebene Sollfälle (NYSE 01.08.2026 = 0/145; FOREX Sa geschlossen; `AZN`/`ASML` → NYSE; `^N225` → TSE;
  `ENR.F` → XETRA; `^FOO` → Fehler; `nextTradingDay` über TSE-Golden-Week und Jahreswechsel; Kalenderende → Fehler).
- **Header:** echte Seiten in jsdom (Muster `verify_seiten_kurse.py`) unter beiden Methoden, injizierte Uhr, sechs
  Zeitzonen mit Offsetnachweis: Monats- und Jahresanfang an geschlossenem Tag, Sonntag vor Monatsende, Berlin nach
  Mitternacht vor NYSE-Schluss (Börsendatum = Vortag), Sektorkorb, unbekannter Ticker.
- **Converter:** sechs Zeitzonen, alle Börsen, 2023 und 2028 (außerhalb der alten Liste), Schaltjahr, geschlossenes
  Datum.
- **Mutationen** (gemeinsame Mechanik `verify_boersenereignisse_mutation.auswerten`, isolierte Kopie): Fassade
  delegiert unter `kalender_v1` an den alten Zweig; `detect` fällt auf NYSE zurück; `'NONE'` wieder offen;
  10-Tage-Grenze zurück; Header nimmt Browserdatum; Header ersetzt Zähler durch DB-Zeile; Monatssumme gegen
  Jahresgrenze verschoben; Converter mit `toISOString`; Einbindung in falscher Reihenfolge.
- Gate: neuer Schritt im Deploy (`verify_holidays_fassade.py`), Seitenprobe mit Laufzeitgrenze wie `verify_sitzungen`.

## Fragen
1. Trägt „Fassade wirft unter `kalender_v1`“ (statt `null`/NYSE) bis V9, oder braucht es für Seiten, die erst in
   V3–V5 umgestellt werden, eine Zwischenform?
2. Das neue Alphabet von `detect` erreicht Verbraucher anderer Phasen. Reicht ein Inventar mit „offen bis Phase X“
   und Pflicht „leer vor V9“, oder soll `detect` unter `kalender_v1` vorerst ein Objekt `{boerse, alt}` liefern?
3. Bundle auf allen 26 Seiten schon in V2 (unter `alt` ungenutzt) — oder erst im Aktivierungscommit?
4. Header unter `kalender_v1` ohne DB-Zeile: fehlt ein Fall, in dem die DB-Zeile heute etwas Richtiges beiträgt?

## Ausgabevertrag
**Urteil** · **Befunde** (P1/P2) · **Antworten 1–4** · **Auflagen**. ≤ 40 Zeilen.

## Anhang A — Aufrufer (Datei:Zeile)
`app.js:799,801` · `strategy-compute.js:110,166,184,196,206,209,329,335,336,340` · `backtest-engine.html:546–555,596` ·
`dashboard.html:565,567,572,626,631,643,650,1148,1233,1235,1238,1284,1286,1287,1301,2154,2155,2193,2194,2228` ·
`feiertage.html:267,494,578,629` · `monatszyklus.html:442,450` · `opex.html:427,446,465,483,484` ·
`plain-vanilla.html:284,511,530–534,605,612,618,619,623,624,659` · `tdom-analyse.html:587,596,606,876,882` ·
`vixpiration.html:393,403,412,427,428` · `watchlist.html:315,320,324,328,397,399,407`.
