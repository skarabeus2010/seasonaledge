# Code-Review: Schritt U (UTC-Tagesnummer) + Teil C (Anomalie-Radar) — Runde 1

Repo `C:\dev\Seasonaledge`, Arbeitsstand (uncommittet; im Baum liegen außerdem die bereits freigegebenen Pakete
A/B — Streamlit/Mails — die hier nicht Gegenstand sind). Plan: `2026-10-09_saison_score_anomalie_plan.md` + v2 + v3
(Freigabe nach v3). Nur lesen. Python: `C:/Users/HeikoSeibel/AppData/Local/Python/pythoncore-3.14-64/python.exe`.
Antwort auf Deutsch: je Befund Schwere + Datei:Zeile + konkreter Eingabefall + Änderung; am Ende genau eine Zeile
`FREIGABE: ja` oder `FREIGABE: nein`.

## Schritt U — Tagesnummer rein in UTC
- `landing/js/seasonal-compute.js`: neu `SA.seasonal.tagNummer(iso)` (Date.UTC aus dem Datumstext);
  `buildYearData` nutzt sie. `landing/js/decade-compute.js::_dayOfYear` gleich gerechnet (die Datei wird auch ohne
  seasonal-compute geladen). Ersetzt an `dashboard.html` (Vola-Tag), `jahreszyklus.html`/`risikozyklus.html`
  (`buildExtendedYearData`-Kopien), `trifecta.html` (letzter Kalendertag).
- **Gemessen:** alte Rechnung unter `America/New_York` an 16 801 von 16 801 Tagen 1990–2035 falsch (1. Januar → 365),
  unter UTC/Berlin/Tokio 0 Abweichungen.
- Wächter: `verify_seasonal_twins.py` Block 4b führt `scripts/js/tz_probe.js` unter sechs Zeitzonen aus (Zeitzone im
  Prozess gesetzt + Offset-Nachweis, weil Git Bash `TZ=Europe/Berlin` als Pfad umbiegt) und vergleicht gegen pandas
  `dayofyear`; dazu identische `buildYearData`-Kurve unter allen Zonen. `verify_twins_mutation.py` +2 Mutationen.
- Bewusst NICHT angefasst: `todayDoy()`-Kopien, die die Uhr lesen (`dashboard.html:456`, `jahreszyklus.html:385`,
  `risikozyklus.html:284`, `wochentage.html:325`, `ki-saisonalitaet.html:467`, `dash-compute.js:104`) — Teil D
  ersetzt die Score-relevanten; `app.js:847` rechnet durchgehend lokal und ist in sich stimmig.

## Teil C — Anomalie-Radar
- `landing/js/decade-compute.js`: `marktklasse(ticker)`, `_epochTag`, `_zielTag` (29.02. → 28.02.), `_bereinigen`,
  `anomalie(rows, ticker, {as_of})`, `anomalieHtml(a, ticker, 'zeile'|'karte')`; `renderAnomalyInto` und die
  Dashboard-Karte nutzen beide; `fromPrices` ruft den Kern statt eigener Rechnung. Rang-Balken einfarbig.
- **Abweichung vom freigegebenen Plan (bitte bewerten):** Börsen-Toleranz **T = 7** statt 5. Gemessen: ^GDAXI am
  12.01.2026 war mit T = 5 „nicht berechenbar", weil XETRA vom 23.12. (Di) bis 29.12.2025 (Mo) 6 Kalendertage ohne
  fehlende Sitzung hat (24.–26.12. Mi–Fr geschlossen); über die Wochentage durchgerechnet maximal 6 bei XETRA,
  asiatische Feiertagsblöcke (Neujahrsfest, Chuseok, Golden Week) länger. Krypto 1, Forex 3 unverändert.
- Gelöscht: `shared/anomaly_engine.py` (keine Aufrufer mehr), Feld `anomaly` aus `scripts/generate_decade_data.py`.
- Texte: „KI Quick-Check" aus 6 Seiten + `section.anomaly_radar`; Tooltip/Methodik DE/EN ohne „Contrarian";
  neue `dc.anom_*`-Schlüssel, alte `dc.status_*`/`dc.percentile_*` entfernt; `_JSON_VER` v9 → v10.
- Wächter `scripts/verify_anomalie_radar.py` (+ `scripts/js/probe_anomalie_radar.js`): 15 konstruierte Fälle gegen
  eine unabhängige Python-Referenz, gezielte Sollwerte (30 Jahre, 29.02., Gleichstand halb, veraltetes Datenende),
  Darstellung beider Renderer, statische Prüfungen; mit `--snapshot`: 966 Stichtage SPY/^GDAXI/^DJI ab 2000, JS =
  Referenz (z/Rang 1e-9). **29/29.** Status dort: 771 normal, 123 auffällig, 34 stark, 38 nicht berechenbar (alle
  SPY 2000–2003: Historie ab 1993 → < 10 Vergleichsjahre). Mutationstest auf Kopien (13 + 2 untaugliche) läuft.

## Bitte besonders prüfen
1. Gibt es eine Seite, die das Radar noch anders rendert oder `decade.anomaly` mit alten Feldern (`score`,
   `return_10d`, `percentile_rank`) liest?
2. Ist die Referenz im Wächter wirklich unabhängig (oder teilt sie eine Annahme mit dem JS, die beide falsch machen
   könnten — z. B. Jahresschleife, Abbruch bei `e < 10`)?
3. Der Abbruch der Jahresschleife bei `e < F` (Reihe reicht nicht mehr): kann er gültige ältere Jahre überspringen,
   wenn ein Jahr mitten in der Historie eine Lücke hat?
4. T = 7: vertretbar, oder eine andere Lösung (kalendergenau für NYSE/XETRA, Heuristik nur für den Rest)?
5. UTC-Umstellung: übersehene Stelle, an der ein ISO-Datum mit lokaler Mitternacht verrechnet wird und in eine
   angezeigte Zahl eingeht?
