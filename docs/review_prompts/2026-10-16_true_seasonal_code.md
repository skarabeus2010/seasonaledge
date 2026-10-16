# Code-Review R1: Williams True Seasonal auf /jahreszyklus

Read-only, Repo `C:\dev\Seasonaledge`, Arbeitsbaum (uncommittet, `git diff` + neue Dateien). Plan v3 mit deiner
Freigabe: `2026-10-16_true_seasonal_plan_v3.md` + `_antwort.md` (Auflagen: Ausschluss langer Schließungen benennen,
„Änderungen zwischen den Monatsgrenzen der Chart-Achse“ auf ungeglätteten Kurven, Return-Behandlung des
Seiten-Builders angleichen). Deutsch, Datei:Zeile, am Ende **FREIGABE (Code): ja/nein**.

## Geändert / neu
- `landing/js/seasonal-compute.js`: `_kumuliere` (gemeinsam für `buildYearData` und den Seiten-Builder), `days` im
  Ergebnis von `buildYearData`, Konstanten `JAHRESANFANG_GRENZE`/`JAHRESENDE_VOLL`/`LUECKE_MAX`/`MONATSENDE_SLOT`,
  `jahrVollstaendig`, `trueSeasonalMindest`, `trueSeasonalJahre`, `mittelKurve`, `monatsAenderungen`, `vergleich12`,
  `rueckblick`.
- `shared/true_seasonal.py`: Python-Zwilling derselben Funktionen.
- `landing/pages/jahreszyklus.html`: Builder über `_kumuliere`; Sidebar `sel-saison` (localStorage
  `sa.jahreszyklus.saison`, Standard Durchschnitt); `trueSeasonalModell` (Vorjahre → IQR nur über diese → Mindestmenge
  nach dem Filter); `rerender` mit Modellmenge und getrennt übergebenem laufendem Jahr (`renderMain`,
  `renderIndividualYears` neue Parameter), Hinweis bei zu wenigen Jahren (Rückfall auf Durchschnitt, sichtbar);
  Bildunterschrift mit Modus; Abschnitt „Rückblick“ (`sec-rueckblick`) mit eigener Ladekennung `_rb`, volle Historie
  über `SA.kurse.zeilen` erst beim Aufklappen, Tickerwechsel verwirft, Fensterwechsel rechnet ohne neue Ladung,
  Fehler mit „Erneut laden“; Embed-Knopf hängt `&saison=true` an.
- `landing/embed.html`: Parameter `saison=true` über denselben Kern.
- `landing/i18n/en.json` (24 Schlüssel), `landing/js/i18n.js` `_JSON_VER` v19.
- Wächter: `scripts/verify_seasonal_twins.py` Block 8 (+ `--nur-true-seasonal` fürs Gate),
  `scripts/js/true_seasonal_probe.js`, `scripts/verify_twins_mutation.py` (+14 Mutationen, eine alte Anker-Mutation in
  `_kumuliere` aufgegangen; 52/52 erkannt), `scripts/js/probe_seiten_kurse.js` (Fälle `saison_true`, `rueckblick*`),
  `scripts/verify_true_seasonal_seite.py` (34 Prüfungen), `.github/workflows/deploy.yml` (beide im Gate),
  `scripts/fixtures/kurse_vorher/pages/jahreszyklus.html` (Anzeigeänderungen nachgezogen, damit „vorher = nachher“
  nur den Lader vergleicht).
- `scripts/research/true_seasonal_probe.py` (Probe für das Artefakt, an die neue Signatur angepasst, als Größenordnung
  gekennzeichnet).

## Bewusst so
- Pressure, Monats-/Quartalsstatistik, Signifikanz, Zyklus-Match und Heatmap rechnen unabhängig vom Modus.
- `SA.outlier.detectIQR` nimmt Quartile per Floor-Index (vorbestehend, nicht Teil dieser Arbeit).
- Im True-Modus ist die gemerkte Wahl auch in der EN-Fassung wirksam (gleicher Schlüssel).

## Prüffragen
1. Rechnen JS-Kern, Seiten-Builder und Python nachweislich dasselbe; deckt der Wächter die Zusagen aus v3 ab
   (Heuristik inkl. TSE 2019 zulässig, Teiljahre/Ende 27.12./Lücke 15 T. nicht, Kalenderfenster ohne Ersatz,
   Zieljahr-Unabhängigkeit mit Ausreißerfilter, Mindestmenge nach dem Filter, Kennzahl)?
2. Seite: bleibt im Durchschnittsmodus alles wie vorher (außer Bildunterschrift/neuer Abschnitt)? Fehlerpfade beim
   Rückblick (Wettlauf `_rb.gen`, `rowsTicker`, `laedt`), Rückfall bei zu wenigen Jahren — korrekt?
3. Embed und Seite gleich? Texte DE/EN ohne Prognoseanspruch?
