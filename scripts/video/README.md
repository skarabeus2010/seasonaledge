# scripts/video — Faceless Social-Video-Pipeline

Erzeugt aus **echten, aktuellen SeasonAlpha-Daten** vertikale (9:16) Chart-Clips für Social-Shorts
(YouTube / Instagram / TikTok / Facebook). Methodik identisch zur Website (normalisierte Renditen,
`shared.calculations`) → Text/Chart bleiben konsistent. Plan: `~/.claude/plans/tranquil-noodling-pixel.md`.

## Voraussetzungen
- `py -3.14` (Container-Python) · `ffmpeg` auf PATH · matplotlib/numpy/pandas (vorhanden).
- Outputs landen in `scripts/video/out/` (gitignored).

## Bausteine
| Datei | Zweck |
|-------|-------|
| `render_vertical_chart.py` | Daten → animierter 9:16-Chart-Clip (+ Hero-Still). Kern. |
| `render_brand_assets.py` | Kanal-Avatar (800×800) + Banner (2048×1152) im Marken-Look. |
| (geplant) `compose.py` | Chart-Clip + Branding + eingebrannte Untertitel + TTS-Voiceover → finale MP4. |
| (geplant) `publish_*.py` | Auto-Upload (YT Data API / IG Graph API / TikTok). |

## Nutzung
```bash
# Saisonaler Jahresverlauf S&P 500 (DE)
py -3.14 scripts/video/render_vertical_chart.py --type seasonal_yearly --ticker ^GSPC --years 20

# Monatszyklus DAX (EN)
py -3.14 scripts/video/render_vertical_chart.py --type monthly_cycle --ticker ^GDAXI --years 38 --lang en

# Kanal-Branding
py -3.14 scripts/video/render_brand_assets.py
```
Optionen: `--lang de|en`, `--years N`, `--fps`, `--seconds` (Animation), `--hold` (Endstand), `--out`.
Chart-Typen: `seasonal_yearly`, `monthly_cycle` (weitere folgen: heatmap/weekday/tom/decade).

## Skript-Agent
`shorts-skripter` (`.claude/agents/`) erzeugt das Skript-JSON (`scripts/video/scripts/<slug>.json`,
Hook + Beats + VO DE/EN + `chart_spec` + Caption), das `compose.py` mit dem Render-Clip kombiniert.
