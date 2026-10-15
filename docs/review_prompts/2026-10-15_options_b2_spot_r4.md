# Code-Review B2-Nachtrag, Runde 4

Deine Antwort R3: `docs/review_prompts/2026-10-15_options_b2_spot_r3_antwort.md` (nein, nur [P2]: Blog erklärte den
Rang als absolute Teuerung). GEX-Spot und VIX-Einträge hattest du ohne weitere Beanstandung.

Umsetzung: Erklärsatz DE/EN neu — „welche Seite im Vergleich zur eigenen Historie teurer ist als üblich: rechts die
Call-Seite (der Put-Skew ist flacher als sonst) … Absolut können die Puts dabei weiter die höhere IV haben — der Rang
misst nur die Abweichung vom Gewohnten … bewusst eine konträre Lesart, keine Aussage über die künftige Richtung.“
`scripts/verify_radar_quadranten.py` prüft zusätzlich je Sprache, dass die Erklärung „relativ zur eigenen Historie“ steht
und die falsche Formulierung („rechts sind die Calls teuer“ / „on the right calls are rich“) nicht.
Unverändert grün: Radar-Wächter, `verify_seo_html` 0. Code uncommittet (`git diff`). Read-only, Deutsch,
**FREIGABE (Code): ja/nein** für das ganze Paket (GEX-Spot, Radar, drei VIX-Indizes).
