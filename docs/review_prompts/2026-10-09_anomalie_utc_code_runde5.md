# Code-Review Anomalie-Radar — Runde 5

Repo `C:\dev\Seasonaledge`, Arbeitsstand gegen HEAD (92c0103). Vorgeschichte: `..._code_runde4.md` + Antwort. Nur lesen.
Antwort auf Deutsch, je Befund Schwere + Datei:Zeile + Fall + Änderung; am Ende genau eine Zeile `FREIGABE: ja` oder
`FREIGABE: nein`. (Im Baum liegen außerdem `landing/js/saison-score.js` und `shared/saison_score.py` — Teil D, noch
nicht verdrahtet, nicht Gegenstand dieser Runde.)

## Korrekturen zu R4
1. **Ticker-Rennen:** neu `SA.ladeKennung` in `landing/js/app.js` (Zähler je Seite). Alle sieben Ticker-Seiten
   (`tdom-analyse`, `overnight`, `jahreszyklus`, `risikozyklus`, `monatszyklus`, `dekadenzyklus`, `dashboard`)
   vergeben in `loadTicker` als erste Zeile `var _lk = SA.ladeKennung.neu();` und brechen im Rückruf des Seitenabrufs
   mit `if (!SA.ladeKennung.aktuell(_lk)) return;` ab — ein verspäteter Abruf A zeichnet nicht mehr über B, und im
   Dashboard setzt er `currentTicker` nicht zurück. Dashboard-Radar: `renderAll` hält `_rk = _seitenKennung` fest
   (gesetzt in `loadTicker`), das Nachladen zeichnet nur bei `SA.ladeKennung.aktuell(_rk)` **und** gleichem Ticker.
2. **Altes Radar sichtbar:** `renderAnomalyInto` und die Dashboard-Karte setzen beim Start sofort einen Ladezustand
   (`anomalieLadeHtml`, `dc.anom_laden` DE/EN).
3. **Älterer Cache:** nachgeladene und übergebene Kurse werden **zusammengeführt** (`voll.concat(rows)` →
   `_bereinigen`, späterer Eintrag je Datum gewinnt = übergebene Kurse).
4. **Schalttag:** Startdatum über `_zielTag(jahr − 31, monat, tag)` → `2024-02-29` lädt ab `1993-02-28`.

## Belege
`verify_anomalie_radar.py --snapshot` **37/37** (neu: `historie_cache_aelter` — Stub endet 30.05., übergeben bis
30.06. → as_of 30.06., z = Referenz; `historie_schalttag` — genau ein Aufruf `&date=gte.1993-02-28`, 30 Jahre;
`abrufkennung` — statisch alle sieben Seiten + Dashboard-Radar), Mutationen **21/21**. `node --check` aller
Inline-Skripte der geänderten Seiten: 0 Syntaxfehler.
