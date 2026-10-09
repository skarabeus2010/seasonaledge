# Code-Review Anomalie-Radar — Runde 4 (Nachtrag nach Freigabe R3, U+C ist als 92c0103 deployt)

Repo `C:\dev\Seasonaledge`, Arbeitsstand gegen HEAD. Nur lesen. Antwort auf Deutsch, je Befund Schwere + Datei:Zeile +
Fall + Änderung; am Ende genau eine Zeile `FREIGABE: ja` oder `FREIGABE: nein`.

## Befund nach dem Deploy (selbst gefunden, Live-Prüfung)
Das Dashboard zeigte für SPY „29 Vergleichsjahre (1997–2025)" statt 30: es lädt nur 30 Jahre Kurse
(`dashboard.html` `startDate − 30`). Schlimmer: Jahres-, Risikozyklus, Overnight und TDOM-Analyse laden je nach
**Zeitraum-Regler** (Standard **10 Jahre**) — das Radar sah dort höchstens ~10 Vergleichsjahre und war mal knapp
berechenbar, mal nicht. Dieselbe Fehlerklasse, die du für den Saison-Score (Plan v2, Befund 4) benannt hast.

## Änderung
`SA.decadeCompute.anomalieMitHistorie(rows, ticker)` → Promise: reichen die übergebenen (bereinigten) Kurse nicht
`RADAR_HISTORIE_JAHRE = 31` Jahre vor das letzte Datum zurück, lädt es über `SA.fetchAllPrices(ticker,
'&date=gte.<Datum−31J>')` (15-min-Cache in app.js) nach; schlägt das fehl, rechnet es mit den übergebenen Kursen (die
angezeigte Basis „n Vergleichsjahre" macht das sichtbar). `renderAnomalyInto` nutzt es mit einer Marke am Element
(späterer Aufruf gewinnt), das Dashboard mit Ticker-Vergleich vor dem Zeichnen.

## Belege
`verify_anomalie_radar.py --snapshot` **34/34**: neue Prüfung `historie_regler_unabhaengig` (Probe mit
fetchAllPrices-Stub: 10 Jahre übergeben → 30 Vergleichsjahre, z = Referenz, genau ein Aufruf
`&date=gte.1994-06-30`; volle Reihe übergeben → kein Aufruf, gleiches Ergebnis). Mutationen **18/18**.

## Bitte prüfen
Rennen beim schnellen Tickerwechsel, Fehlerpfade (fetch lehnt ab / liefert weniger Zeilen), Krypto/Forex mit kurzer
Historie (jedes Mal ein unnötiger Abruf? Cache?), und ob irgendein Radar-Aufrufer noch synchron `anomalie()` auf einem
Seitenausschnitt rechnet.
