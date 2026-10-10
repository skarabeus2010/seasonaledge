# Handelstag-Nummern — Plan v5: P1b „ein Kalender für die Seiten“ (Runde 5)

Stand: P1a ist fertig und lokal committet — `4d88ac6` (Kalenderkorrekturen), `d6b683e`
(`handelstag_nummern`, `kalender_status`), `7264366` (eine Ticker-Zuordnung, strenge Börse, keine stillen
Ersatzkalender). Vorgänger: [v3](2026-10-10_xetra_tdoy_plan_v3.md) + [Antwort 3](2026-10-10_xetra_tdoy_plan_antwort3.md)
(deine neun Befunde zu P1 — v5 beantwortet sie für den JS-Teil).

<task>
Prüfe den Entwurf für P1b, bevor Code entsteht. Ziel: Die Seiten beantworten „ist Tag X an Börse B offen?“
aus **denselben Daten** wie Python. Nicht Ziel: Tagesnummern oder Statistiken umstellen (das ist P3/P4, mit
gemeinsamer Aktivierung). Read-only.
</task>

## Gemessen (lokal)
- 51 HTML-Dateien binden `landing/js/holidays.js` ein (25 unter `landing/pages`, 25 unter `landing/en`
  — dort aus `build_en.py` erzeugt —, dazu Startseite/andere); 19 Aufrufe von `detect()`.
- `detect()` kennt nur NYSE/XETRA/LSE/NONE. Gegen `shared.symbols`: **40 von 370** Tickern bekommen einen
  anderen Kalender, dazu die 11 Forex-Ticker als 7-Tage-Woche (`NONE`) statt Mo–Fr.
- Aufrufer verzweigen auf den **Rückgabewert** `'NONE'` (dashboard.html 562/564/569/623/628/640/647/1282/
  2149/2150/2188/2189, monatszyklus.html 439/447, watchlist.html 313/395, strategy-compute.js 899/914/931).
- Datumshelfer werden als Ereignisalgorithmen genutzt (nicht als Kalender): `goodFriday`, `thanksgiving`,
  `_nthDow`, `_lastDow`, `_ds`, `easter`, `whitMonday`, `_NYSE_SONDER` (strategy-compute.js 328/334/339,
  backtest-engine.html 541–591, opex/vixpiration, plain-vanilla.html 596–619, watchlist.html 410).

## Entwurf P1b
**B1 Datendatei.** `scripts/build_boersenkalender_js.py` erzeugt `landing/js/boersenkalender-daten.js`
(getrackt, deterministisch, sortierte Schlüssel, `\n`-Zeilenenden): `SA.KALENDER_DATEN = {version: sha256
der Nutzdaten, von: 1885, bis: 2100, woche: {...}, feiertage: {BÖRSE: {JAHR: "MMDDMMDD…"}}, ticker:
{370 Einträge}, suffix: [...], status: {aus KALENDER_GUELTIG}}`. `--pruefen` erzeugt im Speicher und
vergleicht byteweise mit Arbeitsdatei **und** `git show HEAD:` (Muster `_JSON_VER`), ohne zu schreiben;
Deploy-Gate auf dem Runner vor dem SSH-Schritt. Größe 1885–2100 geschätzt ~120 KB roh / ~13 KB gzip.

**B2 `holidays.js` liest nur noch die Daten** für `get`, `getMap`, `isTradingDay`, `nthTradingDay`,
`lastTradingDay`, `nthTradingDayOfYear`, `nextTradingDay`. Die eigenen Kalenderregeln `_nyse/_xetra/_lse`
entfallen. **Die Datumshelfer bleiben** (`easter`, `goodFriday`, `thanksgiving`, `_nthDow`, `_lastDow`,
`_ds`, `whitMonday`, `_NYSE_SONDER`) — sie berechnen Ereignistermine, keine Börsenkalender. `_NYSE_SONDER`
wird aus den Daten abgeleitet (Liste der NYSE-Sonderschließungen), damit es nicht ein zweites Mal gepflegt wird.
Fehlende Datendatei, unbekannte Börse oder Jahr außerhalb 1885–2100 → `throw` (kein stiller NYSE-Ersatz).
Eingabe-Alias: `'NONE'` = CRYPTO (bestehende Aufrufer übergeben ihn).

**B3 `detect()` verträglich, `boerse()` neu.**
- `SA.holidays.boerse(ticker)` = exakt die Python-Regel (Daten-Map + Suffix-Tabelle + gleiche Fehlerfälle).
- `detect(ticker)` bleibt für die bestehenden `'NONE'`-Verzweigungen: CRYPTO **und FOREX** → `'NONE'`
  (wie heute), alle anderen → `boerse(ticker)`. Damit bekommen die **40** Ticker sofort ihren Kalender;
  Forex bleibt auf den Seiten vorerst 7-Tage (bekannte Lücke, wird mit P4 behoben, wenn die Verbraucher auf
  `boerse()` umgestellt sind und ihre `'NONE'`-Zweige neu entschieden werden). Unbekannter Ticker: `detect`
  wirft wie `boerse`; die Aufrufer fangen das heute mit `catch → 'NONE'` (dashboard/monatszyklus) — Frage 3.

**B4 Folgen in Verbrauchern, die P1b mitziehen muss** (deine Runde-3-Befunde 4/5/7):
- `/feiertage`: `HOL_NAMES` kennt nur NYSE/XETRA/LSE/NONE; neue Kennungen ergäben falsche Namen per
  Listenposition. Vorschlag: Namen nur für NYSE/XETRA/LSE wie bisher; für andere Börsen „Börsenfeiertag“
  ohne Namen, Zuordnung über Datum statt Position.
- `strategy-compute.js` Feiertagsstrategien (`boerse !== 'NONE'`): für EU/Asien-Ticker liefert `get()`
  künftig deren Kalender statt NYSE. **Vorher messen**, welche Strategie-Ergebnisse sich für die 40 Ticker
  ändern (eingefrorene Kurse), und mit dir entscheiden, ob P1b das ausliefert.
- Bestehende Node-Proben (`probe_plain_vanilla_1a/1b.js`, `verify_kalender_zwilling.py`, Mutationskopien)
  laden die Datendatei vor `holidays.js`.

**B5 Prüfung.** `scripts/verify_boersenkalender_js.py`: (a) Datei aktuell (`--pruefen`); (b) node führt die
echte `holidays.js` mit der echten Datendatei aus: `isTradingDay` == Python `is_trading_day` für alle 13
Börsen × jeden Tag 1885–2100; `nthTradingDay`/`lastTradingDay`/`nthTradingDayOfYear` gegen
`handelstag_nummern`; (c) `boerse()` == Python für 370 Ticker + Regelfälle, `detect()` == boerse außer
CRYPTO/FOREX → 'NONE'; (d) Fehlerfälle (fehlende Daten, Jahr 1884/2101, unbekannte Börse); (e) die
Sollfälle aus `verify_kalender_sollfaelle.py` auch in JS. Mutationstest deterministisch.

## Fokusfragen
1. B1–B5 tragfähig? Insbesondere: Ist „`detect()` liefert für FOREX weiter `'NONE'`“ als Zwischenstand
   vertretbar, oder muss Forex in P1b mit?
2. B4: Welche sichtbaren Werte ändern sich für die 40 Ticker durch P1b (Seiten, Strategien, Marker)?
   Gibt es eine Stelle, an der der Wechsel NYSE → eigener Kalender eine schlechtere Aussage ergibt?
3. Unbekannte Ticker: heute fangen Aufrufer `detect()`-Fehler mit `'NONE'` (7 Tage) ab — gleiches Problem wie
   in Python. In P1b mit beheben (Fehler anzeigen) oder P4?
4. Ladevertrag: ein zusätzliches `<script>` vor `holidays.js` in allen Seiten — oder die Daten in
   `holidays.js` selbst erzeugen (eine Datei, eine Anfrage)? Was ist robuster gegen Cache/EN-Build?
5. Was fehlt?

## Ausgabevertrag
**Urteil** (tragfähig / mit Auflagen / nicht tragfähig) · **Antworten** (je ≤ 8 Zeilen, Datei:Zeile) ·
**Befunde** · **Auflagen vor dem Code**. ≤ 100 Zeilen.
