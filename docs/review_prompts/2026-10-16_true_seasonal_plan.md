# Plan v1: Williams True Seasonal auf /jahreszyklus (Entwurf, vor dem Code)

Read-only, Repo `C:\dev\Seasonaledge`. Deutsch, Datei:Zeile, am Ende **FREIGABE (Plan): ja/nein**.

## Anlass und Messung
Larry Williams, „Larry Williams Indicators“ (LNL 2020, S. 15): die Saisonkurve für ein Jahr nur aus Daten bis dahin,
„then pushed forward on charts for the next year“; andere Studien „include data from 2011, 2012, 2013“ für 2010.
Probe 16.10. (`scripts/research/true_seasonal_probe.py`, `shared/true_seasonal.py`, beide neu und uncommittet; Ergebnis
im Artefakt): Korrelation der 12 Monatsrenditen Ist-Jahr gegen Saisonkurve, Mittel über Jahre mit ≥ 10 Vorjahren:

| | Jahre | nur Vorjahre (alle) | nur 10 Vorjahre | 10-J.-Fenster inkl. Zieljahr |
|---|---|---|---|---|
| QQQ | 2009–2025 | 0,02 | 0,03 | 0,29 |
| SPY | 2003–2025 | 0,06 | 0,05 | 0,31 |
| ^GDAXI | 1969–2025 | 0,06 | 0,08 | 0,33 |

Die rückblickende Kurve enthält das Zieljahr zu 1/10 → scheinbare Passung. Die Seite verspricht keine Prognose, zeigt
aber nur die rückblickende Sicht.

## Nutzerentscheidungen (16.10.)
1. Hauptkurve: **Umschalter „Durchschnitt / True Seasonal“, Standard bleibt der heutige Durchschnitt** (inkl. laufendem
   Jahr mit fortgeschriebenem Endwert, `jahreszyklus.html` ~1759–1781).
2. Rückblick-Abschnitt lädt die **volle Historie erst beim Aufklappen**.

## Bauplan
**A. Rechenkern (Zwilling).** `shared/true_seasonal.py` (vorhanden: `vorjahre`, `true_seasonal(year_data, ziel_jahr,
max_jahre, min_jahre=5)`; Vorjahr = abgeschlossen nach `year_covers(yd, 365, jahr, ziel_jahr)`) und neu
`SA.seasonal.trueSeasonal(yearData, zielJahr, {maxJahre, minJahre})` in `landing/js/seasonal-compute.js` auf
`yearCovers` (~414). Dazu `rueckblick(year_data, {max_jahre, min_vorjahre=10, fenster})` in beiden: je abgeschlossenem
Jahr Y die Korrelation der 12 Monatsrenditen (Monatsgrenzen 31,59,…,365 auf der 365er-Achse, Januar gegen 100) und
Vorzeichentreffer gegen (a) True Seasonal, (b) die Kurve, die die Seite bei Fenster N mit Y als jüngstem Jahr zeigt
(Jahre Y−N+1…Y). Rückgabe je Jahr + Mittel, Anzahl positiver Korrelationen, n. Korrelation `null`, wenn eine Seite
konstant ist.

**B. Hauptchart.** Neuer Schalter in der Sidebar (`sel-saison`: `durchschnitt` | `true`), gemerkt über `SA.prefs`
wie die anderen Seitenoptionen? (offen, siehe Frage 4). Bei `true`: `avg` = True Seasonal für das laufende Jahr aus
den abgeschlossenen Jahren im gewählten Fenster (kein laufendes Jahr, keine Teiljahre), `std`/Bänder aus denselben
Jahren. Was davon abhängt (`renderMain`, `renderDetrend`, Perzentilband, Bildunterschrift „Jahre · n“), rechnet mit
derselben Jahresmenge; Monats-/Quartalsstatistik, Signifikanz, Zyklus-Match, Heatmap bleiben unverändert (beschreibende
Statistik bzw. Test über die Historie, keine Projektion; Zyklus-Match schließt das laufende Jahr schon aus, ~1601).
Bildunterschrift nennt den Modus.

**C. Rückblick-Abschnitt** (neu, eingeklappt, unter dem Hauptchart): beim ersten Aufklappen
`SA.kurse.zeilen(ticker, {felder:['date','close','log_return']})` ohne `ab` (volle Historie, gemeinsamer Lader,
Ladekennung wie `loadTicker` ~1808, Tickerwechsel verwirft das Ergebnis). Inhalt: Balken je Jahr (r True Seasonal vs. r
rückblickend), zwei Kennzahlen (Ø r, positive Jahre k/n) für beide, ein erklärender Satz ohne Prognoseanspruch.
Fenster der rückblickenden Kurve = gewähltes `sel-years` (bei `max`: alle Jahre bis Y). True Seasonal mit allen
Vorjahren (Williams) — oder ebenfalls N Vorjahre? (Frage 3). Fehler/zu kurze Historie → Hinweis „nicht auswertbar,
n Jahre mit ≥ 10 Vorjahren“, kein leerer Chart.

**D. Texte.** DE/EN über `data-i18n` + `en.json`/`de.json`, `_JSON_VER` erhöhen, dynamische Texte über `SA.i18n.t`,
`verify_en` FAIL 0. Kein „Prognose“, kein „Signal“.

**E. Wächter.** `verify_seasonal_twins.py` neuer Block: Python `true_seasonal`/`rueckblick` gegen die echte JS-Datei in
node (Muster Block 4) auf synthetischen Reihen mit analytischer Sollkurve (u. a. Teiljahr am Ende, Lücke, Jahr mit
Ende Tag 362, Schaltjahr) + einem Fall, in dem nur das Zieljahr abweicht (True Seasonal darf sich nicht bewegen,
rückblickend muss). Mutationen in `verify_twins_mutation.py`: Zieljahr eingeschlossen (`<` → `<=`), Teiljahr nicht
ausgeschlossen, Monatsgrenze verschoben, Fenster ohne Zieljahr. Seitenprobe in jsdom (Muster `verify_seiten_kurse.py`):
Schalter setzt die Jahresmenge der Hauptkurve; Rückblick lädt erst beim Aufklappen genau einmal; Tickerwechsel während
der Ladung verwirft das Ergebnis.

**F. Nicht Teil:** Umbau der übrigen Seiten (Risikozyklus, Dashboard, Saison-Score), Kalender-Umstellung (V4).

## Prüffragen
1. Ist die Rückblick-Kennzahl (Pearson auf 12 Monatsrenditen, Vorzeichentreffer) für die Seite tragfähig, oder
   irreführend bei 12 Werten je Jahr? Bessere einfache Kennzahl?
2. Teilmengen-Regel: Ist „abgeschlossen = `year_covers(…,365,…)`“ für die True-Seasonal-Jahre richtig, und darf der
   Durchschnitt-Modus die Teiljahre (IPO-Jahr, laufendes Jahr) weiter mitnehmen?
3. True Seasonal im Rückblick: alle Vorjahre (Williams) oder dasselbe Fenster N wie die Seite (fairer Vergleich mit der
   rückblickenden Kurve)? Oder beide?
4. Fehlt ein abhängiger Teil der Seite, der beim Umschalten mitrechnen müsste (Pressure, Perzentile, Einzeljahre,
   Embed `/embed`)? Schalter in `SA.prefs` merken?
5. Gibt es Stellen, wo dieselbe Rückblickfrage sonst auftaucht (Blog-Aussagen „in X von Y Jahren“), die man markieren
   sollte?
