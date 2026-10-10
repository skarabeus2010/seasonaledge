# Ticker schneller laden — Migration Schritt 1: alte Lader als Hüllen auf `SA.kurse`

Plan [docs/TICKER_LADEN.md](../TICKER_LADEN.md); Lader freigegeben in [S1 Runde 4](2026-10-10_ticker_laden_s1_code_antwort4.md),
committet `05e6310`. Read-only, nichts schreiben, Mutationstest NICHT ausführen.

<task>Prüfe Migration Schritt 1 (Arbeitsbaum, `git diff`): ändert er für irgendeinen Aufrufer, was zurückkommt,
oder wann/ob er abgelehnt wird? Danach soll er deployt werden.</task>

## Was geändert ist
- `landing/js/app.js`: `SA.fetchAllPrices(ticker, extraFilter)` ist eine Hülle auf
  `SA.kurse.zeilen(ticker, {felder: date,close,log_return,tdom,tdoy, ab})`; `extraFilter` nur `''`/`undefined` oder
  `&date=gte.YYYY-MM-DD` (alle 18 Aufrufstellen haben eine dieser Formen, `grep -rn "fetchAllPrices(" landing`),
  alles andere lehnt ab. Der alte localStorage-Kurscache entfällt; `kurse.js` entfernt `sa-cache-prices:*` einmal.
- `landing/js/decade-compute.js`: `ladeVollHistorie` ist eine Hülle (`ab: null`, dieselben Felder), `_vollCache`
  entfällt. `mitHistorie`/`anomalieMitHistorie` unverändert — sie laufen jetzt über den gemeinsamen Koordinator
  (Dashboard: 30-J-Ladung → danach EINE wartende Vollladung, die Radar und Saison-Score bedient).
- `<script src="/landing/js/kurse.js">` direkt nach `app.js` in allen 44 DE-Seiten mit `app.js`; der EN-Build
  übernimmt es (lokal gebaut: alle 37 EN-Seiten mit `app.js` binden `kurse.js` ein, `verify_en` FAIL 0).
- Noch NICHT migriert (kommt in Schritt 2 mit Seitenproben): die zehn lokalen Lader, Dashboard-Overnight, Embed.

## Nachweis „gleiche Rückgabe je Aufrufer"
`scripts/js/probe_kurse_huellen.js`: die alten Lader **wörtlich** aus `05e6310` (`scripts/fixtures/kurse_alte_lader.js`)
gegen die Hüllen, die aus den **echten** Dateien geschnitten werden (Schnitt muss eindeutig treffen), gegen einen
PostgREST-Nachbau, der Range + `count=exact` (alt) und Keyset (neu) bedient. Reihen 0/1/999/1000/1001/2000/2500/
33 739 × 7 Filterformen (ohne, leer, 1895, Mitte, nach dem Ende, erstes Datum, letztes Datum) + Vollhistorie:
**65/65 identisch** (`JSON.stringify` der Rückgabe). Im Wächter `verify_kurse.py` (Gate), dazu vier Mutationen an den
Hüllen (Grenze ignoriert, Feld fehlt, unbekannter Filter still, Vollhistorie mit Grenze).

## Bewusste Verhaltensänderungen (bitte prüfen, ob noch eine fehlt)
- Ladefehler: alt warf je nach Pfad `Error('prices 500 (T)')`; neu `KursFehler` mit gleichem Muster. Aufrufer
  prüfen nur, OB abgelehnt wird (`catch`), nicht die Klasse — bitte gegenprüfen.
- Alter Cache: localStorage, 15 min, je Filter; neu im Speicher, 15 min, je Ticker — Seitenwechsel lädt neu
  (vorher localStorage-Treffer). Das ist im Plan gemessen/angekündigt (S0 „zweite Seite").
- Rückgabe sind Kopien (alt: frische Objekte aus Netz bzw. JSON.parse) — Seiten verändern Zeilen (`parseFloat`),
  das bleibt folgenlos.

## Fokusfragen
1. Gibt es einen Aufrufer, dessen Rückgabe oder Ablehnung sich ändert (z. B. `crash-fruehwarnung` mit
   `Promise.all`, `sektor-rotation` „Fehler werden zu leeren Reihen", `polymarket` BTC/ETH parallel)?
2. Reicht der Hüllen-Nachweis für diesen Schritt (Seitencode unverändert), oder braucht es schon jetzt die
   Seitenprobe aus Plan A4?
3. Freigabe für den Deploy?

## Ausgabevertrag
**Urteil** · **Befunde** · **Auflagen**. ≤ 40 Zeilen.
