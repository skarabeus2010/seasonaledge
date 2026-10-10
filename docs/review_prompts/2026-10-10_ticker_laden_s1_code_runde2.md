# Ticker schneller laden — S1 Code-Runde 2: Lader `SA.kurse` nach deinen Auflagen

Runde 1: [Prompt](2026-10-10_ticker_laden_s1_code.md) · [Antwort](2026-10-10_ticker_laden_s1_code_antwort1.md) (mit Auflagen).
Read-only, nichts schreiben (der Mutationstest schreibt — bitte NICHT ausführen; Ergebnis steht unten).

<task>Prüfe, ob die Auflagen aus Runde 1 erfüllt sind und ob Lader + Wächter jetzt als Grundlage für die
Seitenmigration freigegeben werden können.</task>

## Umsetzung der Auflagen
1. **Retry-After** beide Formate (`retryAfterMs`: Sekunden oder HTTP-Datum gegen die Uhr des Laders, Obergrenze
   60 s). Probe Abschnitt 18 misst die echte Wartezeit (≥ 950 ms bei Vorgabe 1 s; Standard wäre 350–650 ms).
2. **Poolplatz bis Transportende** (`platz()` liefert eine einmalige Freigabe, `antwort.then(frei, frei)`; die
   Frist lehnt nur den Aufrufer ab). Abschnitt 19: Server ignoriert den Abbruch und antwortet nach der Frist —
   höchstens 4 offene Anfragen, Pool danach leer, verspätete Antwort veröffentlicht nichts.
3. **Request-Vertrag** über alle Anfragen des ganzen Laufs (Sortierung, Limit, `select` beginnt mit `date`, Header
   genau `apikey`+`Authorization`, kein count/offset). Deine drei Mutationen sind jetzt rot.
4. **Neue Fälle**: JSON-Fehler einmal/dauerhaft (20), wartende Ladung scheitert (21), Übergangsanfragen im
   Abschluss-Callback (22), TTL-Ablauf eines vorhandenen Bestands mit Anfrage während der Neuladung (23).

## Dazu selbst gefunden (Mutationstest)
- **Zwei Mutationen entwischten** der ersten Probe: „Vereinigung nimmt die spätere Grenze" (die wartende Ladung
  wuchs nie mit zwei Nicht-null-Grenzen) und „Generation je Ticker" — neue Abschnitte 10b/10c.
- **Neu im Lader**: letzte Sperre in `laden()` — eine Sicht nur, wenn der Bestand die Anfrage deckt, sonst
  `KursFehler`. Bei korrektem Code unerreichbar (äquivalente Mutation, bewusst nicht in der Liste).
- **Probe in 24 Abschnitte mit eigener Frist** (8 s): ein Abbruch oder Hänger ist ein benannter Fehlschlag des
  Abschnitts, die übrigen laufen weiter, Endmarker `PROBE-ENDE` erreicht. Eine Ausnahme, die aus
  `landing/js/kurse.js` stammt und kein `KursFehler` ist, gilt als `[Ausnahme]` (kein Nachweis). Erste Fassung der
  Herkunftsprüfung traf auch `probe_kurse.js` (Regex `kurse\.js`) — jetzt Pfad `landing/js/kurse.js`.
- **Cursor-Fall verschärft**: zweiter Block beginnt MIT dem Cursor-Datum, ist in sich aufsteigend und < 1000 —
  vorher fing ihn nur die Blockgrenze.

## Stand
`py -3.14 scripts/verify_kurse.py` → 80 Prüfungen grün, `PROBE-ENDE`. Mutationstest
`scripts/verify_kurse_mutation.py`: **28/28 gefangen**, je mit benannter Prüfung, Gegenproben (Anker fehlt,
Absturz, eingefangener `TypeError`) richtig verworfen.

## Fokusfragen
1. Auflagen erfüllt? 2. Ist die Abschnitts-Frist (8 s) mit der 1-s-Retry-After-Messung und `spaet:150`
robust (Fehlalarm auf langsamen Rechnern)? 3. Fehlt eine Mutation, die der Vertrag verlangt?
4. Freigabe für die Seitenmigration?

## Ausgabevertrag
**Urteil** · **Befunde** · **Auflagen**. ≤ 40 Zeilen.
