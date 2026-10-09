# Code-Review Anomalie-Radar — Runde 6

Repo `C:\dev\Seasonaledge`, Arbeitsstand gegen HEAD (92c0103). Vorgeschichte: `..._code_runde4/5.md` + Antworten.
Nur lesen; Teil D (`saison-score.js`, `shared/saison_score.py`, `verify_saison_score.py`) ist nicht Gegenstand.
Antwort auf Deutsch, je Befund Schwere + Datei:Zeile + Fall + Änderung; am Ende genau eine Zeile `FREIGABE: ja` oder
`FREIGABE: nein`.

## Korrekturen zu R5
1. **Rückwechsel / gleicher Ticker:** `SA.ladeKennung.start(ticker, angezeigt)` merkt den zuletzt **angeforderten**
   Ticker. `null` („nichts zu tun") nur, wenn `ticker === angezeigt` **und** `angefordert === angezeigt` — also kein
   anderer Abruf unterwegs. A → B → A entwertet B und lädt A (aus dem 15-min-Cache) neu; A erneut wählen, während A
   angezeigt ist und das Radar nachlädt, ändert die Kennung nicht. Dashboard (`currentTicker`), Monatszyklus
   (`MZ.getCurrentTicker()`), Dekadenzyklus (`D ? currentTicker : null`) prüfen erst `!ticker`, dann `start`; die vier
   Seiten ohne Abkürzung rufen `start(ticker)`.
2. **Fehler-Rückrufe:** jeder `.catch` in den sieben `loadTicker` beginnt mit `if (!SA.ladeKennung.aktuell(_lk)) return;`.

## Belege
`verify_anomalie_radar.py --snapshot` **38/38**: `abrufkennung` liest jetzt den Rumpf von `loadTicker` und verlangt
`start(ticker…)`, die Prüfung im Erfolgs- **und** im Fehler-Rückruf; neu `ladekennung_verhalten` führt den aus
`app.js` gezogenen Helfer in node aus (A; A→B; B→A entwertet B; A erneut = null, A bleibt gültig). Mutationen
**22/22** (neu: „Fehler-Rückruf ohne Kennung", „Rückwechsel ohne Entwertung"). `node --check` aller Inline-Skripte: 0.
