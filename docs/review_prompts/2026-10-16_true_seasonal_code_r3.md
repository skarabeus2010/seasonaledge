# Code-Review R3: Williams True Seasonal — Rückfall im Embed

Read-only, Repo `C:\dev\Seasonaledge`, Arbeitsbaum. Deine Runde 2: `2026-10-16_true_seasonal_code_r2_antwort.md`.
Deutsch, Datei:Zeile, am Ende **FREIGABE (Code): ja/nein**.

## Behoben
`landing/embed.html`: Bei `saison=true` und unterschrittener Mindestmenge rechnet der Rückfall wie die Seite — Jahre im
Seitenfenster (≥ Jahr − N, bei Max ≥ 1900), derselbe Jahresfilter `SA.outlier.filterJahre(…, filter)`, Mittel über
`SA.seasonal.mittelKurve` — statt des ungefilterten Durchschnitts aller geladenen Jahre (Embed lädt ab Jahr − N − 1).

## Absicherung
`scripts/verify_true_seasonal_seite.py` (48): neue Testreihe `LUECKE` (ab 2010, in 2017–2020 fehlt je der März →
6/8 vollständige Vorjahre; /embed lädt ab 2015, die Seite ab 2016). Prüft Seite (`saison_true_neu`) und Embed
(`embed_true_wenig`) auf gleiche Reihe „Saisonaler Ø (11J)“ und gleiche Werte an Tag 31/101/201. Gegenprobe in einer
Kopie mit dem alten Rückfall: Embed „Saisonaler Ø (12J)“, Tag 31/101/201 = 100,55 / 103,35 / 108,05 statt
100,14 / 102,95 / 107,88 → der Vergleich wird rot.

Unverändert: Mutationstest 55/55, `verify_seiten_kurse.py` 313/313 (läuft erneut, nur weil die Testdatenfunktion der
Probe um `LUECKE` erweitert wurde).

## Prüffragen
1. Rückfall Seite = Embed auch mit aktivem Jahresfilter (dein Fall aus R2: IQR, drei Ausreißer, 7/8)?
2. Freigabe?
