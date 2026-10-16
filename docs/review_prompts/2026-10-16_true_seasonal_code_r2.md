# Code-Review R2: Williams True Seasonal auf /jahreszyklus

Read-only, Repo `C:\dev\Seasonaledge`, Arbeitsbaum. Deine Runde 1: `2026-10-16_true_seasonal_code_antwort1.md`.
Deutsch, Datei:Zeile, am Ende **FREIGABE (Code): ja/nein**.

## Behoben
1. **„Max“ ohne Untergrenze 1900 im True-Modus:** `jahreszyklus.html` `rerender` baut für `fensterN == null` die
   Modelljahre aus allen geladenen Zeilen (`JZ.buildExtendedYearData(_cachedRows)`); der Durchschnittsmodus behält
   die 1900-Grenze (unverändert).
2. **Embed = Seite:** Modellauswahl gemeinsam in `SA.seasonal.trueSeasonalModell(yearDataRoh, stichtag, N, filterFn)`
   (Vorjahre → Filter nur über diese → Mindestmenge nach dem Filter); Jahresfilter gemeinsam in
   `SA.outlier.filterJahre(yearData, methode)` (Jahresrendite aus `full_365`, daher gleich für den gerundeten
   `simpleReturn` von `buildYearData` und den ungerundeten des Seiten-Builders). Die Seite delegiert
   (`applyOutlierFilter`, `trueSeasonalModell` als dünne Hüllen), `/embed` lädt `outlier.js`, liest `filter=` und
   fällt bei zu wenigen Jahren wie die Seite auf den Durchschnitt zurück — mit Hinweis im Titel
   („True Seasonal nicht verfügbar (n/m Vorjahre)“). Der Embed-Link der Seite überträgt `filter=` bei True Seasonal.
3. **Kennzahl unabhängig:** Block 8 baut zwei Kurven aus vorgegebenen zwölf Änderungen (Monatsgrenzen wörtlich, nicht
   aus `TS.MONATSENDE_SLOT`, linear im Monat), Soll über `statistics.correlation` und Vorzeichen direkt: JS und Python
   müssen r = 0,6914, 8 Treffer, 7× Plus und die Änderungen selbst treffen. Schaltjahr-Achse: 29.02.2024 → März-Slot,
   28.02.2023 → Februar-Slot (Seiten-Builder). Neue Mutationen: Monatsgrenzen um einen Tag vorgezogen (JS, Python),
   Filter über alle Jahre, Mindestmenge vor dem Filter (beide jetzt in `seasonal-compute.js`), Seite reicht den Filter
   nicht durch.
4. **Sichtbar:** `jz.ts_mode_desc` nennt Pressure, Monats-/Quartalsstatistik, Signifikanz, Zyklus-Match und Heatmap als
   unabhängig vom Modus; Jahresende „ab Kalendertag 362 – 28.12., im Schaltjahr 27.12.“ (DE + EN, Fixture).

Seitenprobe `verify_true_seasonal_seite.py` (43): zusätzlich `/embed?saison=true` = Seitenkurve (vier Stichtage) und
Rückfall bei junger Reihe (NEU ab 2022: 4/8). Mutationstest 55/55 erkannt, `verify_seiten_kurse.py` 313/313 bestanden (Arbeitsbaum).

## Vorbestehend, nicht Teil
`/embed` lädt im Durchschnittsmodus ab Jahr − N − 1 (bis zu N + 2 Jahre), die Seite ab Jahr − N; Embed ohne
Ausreißerfilter im Durchschnittsmodus. Unverändert gelassen, weil eingebettete Fremdseiten sonst still eine andere
Kurve zeigen — eigener Posten, falls gewünscht.

## Prüffragen
1. Sind die drei Befunde behoben, ohne neue Abweichung zwischen Seite und Embed?
2. Ist der analytische Kennzahltest unabhängig genug (würde deine Mutation „ersten elf Monatsgrenzen −1“ jetzt rot)?
3. Freigabe?
