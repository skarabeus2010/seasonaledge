# Plan v2: Williams True Seasonal auf /jahreszyklus

Read-only, Repo `C:\dev\Seasonaledge`. Deine Runde 1: `2026-10-16_true_seasonal_plan_antwort.md`. Hier nur die
Änderungen gegenüber v1 (`..._plan.md`). Deutsch, Datei:Zeile, am Ende **FREIGABE (Plan): ja/nein**.

## Korrektur zur Messung in v1
Die Spalte „10-J.-Fenster inkl. Zieljahr“ der Probe sind die Jahre Y−9…Y (zehn), nicht das Seitenfenster (das sind
Y−N…Y, also bis zu elf Kurven, `jahreszyklus.html:1760`). `in_alle` enthielt Jahre nach Y. Die Zahlen bleiben als
Größenordnung im Artefakt, werden aber nicht als Nachbildung der Seite bezeichnet; die Seite rechnet mit dem neuen Kern.

## 1. Vollständiges Jahr (neu, beide Zwillinge)
`jahr_vollstaendig(yd, jahr, stichtag_jahr)` / `SA.seasonal.jahrVollstaendig`: `year_covers(yd, 365, jahr, stichtag)`
**und** erste Beobachtung ≤ Kalendertag 7 **und** kein Abstand zwischen zwei Kurszeilen > 10 Kalendertage.
Begründung: 7 deckt Neujahr + Wochenende (TSE öffnet spätestens 4./5.1.); 10 lässt 11.–14.09.2001 (Lücke 10.→17.09.,
7 Tage) und Sandy durch, nicht aber Teiljahre/Datenlöcher. Der Docstring in `shared/true_seasonal.py` wird korrigiert.
Für die Lückenprüfung braucht der JS-Builder die Tage aller Zeilen — `buildExtendedYearData` (`jahreszyklus.html:579`)
und `buildYearData` (`seasonal-compute.js:368`) liefern sie unterschiedlich; der Kern bekommt die Tage als Eingabe
(`yd.days`), beide Builder setzen sie (Prüfung im Wächter).

## 2. Fenster = Kalenderjahre wie die Seite
Seitenfenster N: Jahre ≥ aktuellesJahr − N (unverändert). **True-Modus Hauptchart:** vollständige Jahre in
[aktuellesJahr − N, aktuellesJahr − 1]; bei `max` alle vollständigen Vorjahre. Fehlende Kalenderjahre werden nicht
durch ältere ersetzt (`vorjahre(..., max_jahre)` wird dafür auf ein Kalenderfenster umgestellt: `von_jahr`).
Mindestmenge: ⌈0,8·N⌉ vollständige Jahre (5 → 4, 10 → 8, …), bei `max` 10; sonst Hinweis statt Kurve.

## 3. Rückblick-Kennzahl
- **Monatsrenditen aus echten Kurszeilen:** Monatsrendite = Summe der `log_return` aller Zeilen des Kalendermonats
  (der Januar enthält den Return des ersten Handelstags gegen den letzten Dezemberschluss — dieselbe Konvention wie
  `normalize_year`, wo Zeile 0 der Referenzpunkt ist? **Nein**: dort fällt der Jahreswechsel-Return weg. Ich definiere
  den Rückblick deshalb ohne ihn: Januar = Summe ab der zweiten Zeile des Jahres, damit Kurve und Kennzahl dasselbe
  Jahr meinen). Nur vollständige Jahre (Regel 1).
- **Modell:** Mittel der Monatsrenditen der Modelljahre je Kalendermonat (exakt, keine 365er-Achse).
- **Kennzahlen je Jahr Y:** Pearson r der 12 Werte („Ähnlichkeit der zwölf Monatsänderungen“, kein Test);
  Vorzeichentreffer mit 0 = kein Treffer und **Vergleich „immer positiv“** (Treffer, wenn man jeden Monat Plus
  erwartet). Konstante Reihe → r `null`, gezählt als „nicht auswertbar“. Mittel und k/n über gültige r.
- **Vergleich:** (a) **True Seasonal Y** = vollständige Jahre in [Y − N, Y − 1] (gleiches Fenster N wie die Seite),
  optional (b) alle Vorjahre; (c) **die Kurve, die die Seite gerade zeigt** (Durchschnittsmodus, aktuelles Fenster,
  enthält Y und Jahre danach) — genau das, was der Nutzer sieht. Ausgewertet werden die vergangenen vollständigen Jahre
  im aktuellen Fenster. Kein Ausreißerfilter im Rückblick.

## 4. Abhängige Teile im True-Modus
- `renderMain` bekommt Modelljahre und das laufende Jahr **getrennt** (goldene Linie bleibt, `:1047`).
- Zyklus-Overlays (`:1021`), Perzentile/Datenzählung (`:939`), Detrend, Legenden, Einzeljahre (`:1277`): Modellmenge
  + laufendes Jahr separat. Pressure (`:626`) bleibt eigene Rechnung, Beschriftung „unabhängig vom Modus“.
- Ausreißerfilter (`:1726`): im True-Modus erst Modelljahre wählen, dann IQR **nur über diese**.
- `/embed`: Parameter `saison=true`, gleiche Auswahl über den gemeinsamen Kern (`embed.html:98`, `:1898`).
- `SA.prefs`: seitenbezogener Schlüssel `jahreszyklus.saison`, Standard/ungültig → `durchschnitt` (`app.js:545`).
- Bildunterschrift nennt Modus und Jahresmenge; im Durchschnittsmodus Hinweis „inkl. laufendem Jahr und Teiljahren“.

## 5. Laden des Rückblicks
Eigene Anfragekennung (Zähler im Seitenmodul, gebunden an Ticker), **kein** `SA.ladeKennung.start()`. Rohzeilen je
Ticker im Modul gehalten; Fensterwechsel rechnet neu ohne Ladung; Fehler → Hinweis mit „Erneut laden“; Frische folgt
dem gemeinsamen Lader (kein „genau einmal“ für immer).

## 6. Wächter (erweitert)
Zwillinge Python/JS in node: IPO-Jahr ab Juli, Jahr nur Dezember, Januar + Dezember mit Loch, innere Lücke 11 Tage,
fehlendes Kalenderjahr im Fenster, Fenstergrenzen N = 5/10/max, Schaltjahr-Monatsenden, konstante Reihe,
Zieljahr-Unabhängigkeit **mit aktivem Ausreißerfilter**. Mutationen: `<` → `<=` beim Zieljahr, Lückenregel aus,
Januar mit Jahreswechsel-Return, 0 als Treffer, Fenster „letzte N gültige“. Seitenprobe jsdom: goldene Linie bleibt im
True-Modus, Embed-Parameter, Rückblick entwertet den Hauptabruf nicht, Tickerwechsel verwirft Rückblick, Fehler
wiederholbar.

## 7. Nicht Teil
Blogartikel (Midterm-Erholung, Google-Juli): **Nutzerentscheidung 16.10. — Blogartikel werden nicht geändert**, kein
Posten. Übrige Seiten, Kalender-V4.

## Prüffragen
1. Trägt die Regel „vollständig“ (≤ Tag 7, Lücke ≤ 10, `year_covers`)? Gegenbeispiele an echten Börsen?
2. Januar ohne Jahreswechsel-Return — richtig im Sinne von „dasselbe Jahr wie die Kurve“?
3. Ist (c) „die Kurve, die die Seite gerade zeigt“ der richtige Vergleich, oder doch „Seite mit Y als jüngstem Jahr“?
4. Freigabe für den Bau?
