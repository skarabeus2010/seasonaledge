# Code-Review: Schritt U + Teil C — Runde 2

Repo `C:\dev\Seasonaledge`, Arbeitsstand. Vorgeschichte: `..._code_runde1.md` + `..._code_antwort1.md`. Nur lesen.
Antwort auf Deutsch: je Befund Schwere + Datei:Zeile + Fall + Änderung; am Ende genau eine Zeile `FREIGABE: ja` oder
`FREIGABE: nein`.

## Korrekturen zu deinen Befunden
1. **Erster Kurstag in den Inline-Buildern** (`jahreszyklus.html`, `risikozyklus.html`): `days.push(SA.seasonal.tagNummer(
   yRows[0].date))`. Zeitzonenwächter (`verify_seasonal_twins.py` 4b, `scripts/js/tz_probe.js`) zieht
   `buildExtendedYearData` jetzt **direkt aus beiden Seiten** (Klammerzählung) und prüft unter sechs Zeitzonen deinen
   Fall (01.–20.01.2023, 100…119: Tag 1 = 100, Tag 21 = 119, Tag 365 = 119, lad 20) sowie Gleichheit mit
   `buildYearData` — 24 Prüfungen, alle OK; Mutation „erster Kurstag lokal" in `verify_twins_mutation.py`.
   Meine erste Suche hatte das Muster verfehlt, weil sie Leerzeichen nach den Kommas verlangte.
2. **Rang in der Dashboard-Karte**: `anomalieHtml(…, 'karte')` zeigt den Rang mit Balken; Darstellungsprüfung verlangt
   in beiden Renderern z, Basis und Rang; Mutation „Karte ohne Rang".
3. **Grundcodes**: der Kern liefert `grund_code` (`zu_wenige_kurse`, `luecke_aktuell`, `zu_wenige_jahre`,
   `keine_streuung`; Renderer/Dashboard bei Ausnahme `fehler`) neben dem deutschen `grund`; der Renderer übersetzt
   über `dc.anom_g_<code>` (DE+EN in `de.json`/`en.json`). Test: konstanter Verlauf auf EN → „Not computable: no
   dispersion …", ohne deutsches Wort; Mutation „Grund auf EN unübersetzt".
4. **Overnight-Sommerzeit**: `overnight.html` setzt `doy: SA.decadeCompute._dayOfYear(rows[i].date)`.
- **Tooltip** nennt die konkreten Grenzen (7 Kalendertage, Krypto 1, Devisen 3) und sagt ausdrücklich, dass eine
  einzelne fehlende Sitzung nicht erkannt wird.
- **Exakte Grenzen**: Statuslogik als `anomalieStatus(z)`; der Wächter prüft z = ±4/3, ±7/3 und knapp darunter;
  Mutation „Grenze |z| = 4/3 zur niedrigeren Stufe".

## Belege
`verify_anomalie_radar.py --snapshot` **32/32** (966 echte Stichtage, JS = unabhängige Referenz), `--mutationen`
**16/16** + 2/2 untaugliche. `verify_seasonal_twins.py` vollständig OK inkl. 4b.
