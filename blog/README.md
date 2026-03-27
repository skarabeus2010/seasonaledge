# SeasonAlpha Blog Engine

## Ordnerstruktur

```
blog/
  blog_builder.py        ← Generator (Markdown → HTML + Social + YouTube)
  posts/                 ← Markdown-Quelldateien
    images/              ← Screenshots & Bilder (fuer alle Posts)
  templates/             ← Jinja2 HTML-Templates
  prompts/               ← Claude API Prompt-Templates
  calendar.yaml          ← Redaktionsplan
  output/                ← Generierte HTML (.gitignore)
```

## Neuen Post erstellen

```powershell
py blog/blog_builder.py --generate "Mein Titel" --ticker ^GSPC --category marktausblick
```

Erstellt eine Vorlage in `blog/posts/2026-03-27_mein-titel.md` mit `status: draft`.

### Kategorien
- `education` — Grundlagen, Theorie
- `marktausblick` — Aktuelle Analysen
- `tutorials` — Schritt-fuer-Schritt Anleitungen

## Post bearbeiten & veroeffentlichen

1. Markdown-Datei in `blog/posts/` oeffnen
2. Frontmatter anpassen (Titel, Beschreibung, Tags)
3. `status: draft` → `status: published` setzen
4. Inhalt in Markdown schreiben

## Screenshots & Bilder einfuegen

1. Bild in `blog/posts/images/` ablegen (z.B. `dashboard.png`)
2. Im Markdown referenzieren:

```markdown
![SeasonAlpha Dashboard](images/dashboard.png)
```

Beim Build wird das Bild automatisch nach `blog/output/{slug}/images/` kopiert.

**Formate:** PNG, JPG, WebP, GIF — alles was der Browser darstellt.

**Tipps:**
- Dateinamen ohne Leerzeichen/Umlaute (z.B. `monatszyklus-screenshot.png`)
- Optimale Breite: 1200px (wird im Blog responsiv skaliert)
- Alt-Text wird als Bildunterschrift angezeigt

## Interaktive Charts einfuegen

Charts werden automatisch aus Live-Daten generiert:

```markdown
{{chart:seasonal_yearly:^GSPC:20}}
{{chart:monthly_heatmap:^DJI:10}}
```

**Format:** `{{chart:TYP:TICKER:JAHRE}}`

| Typ | Beschreibung |
|-----|-------------|
| `seasonal_yearly` | Saisonaler Jahresverlauf mit Konfidenzband |
| `monthly_heatmap` | Monats-Rendite Heatmap (10J) |

## Lokal bauen & testen

```powershell
py blog/blog_builder.py --build
```

Generiert alle Posts nach `blog/output/`. HTML-Dateien direkt im Browser oeffnen.

## Deployen

```powershell
git add blog/
git commit -m "Blog: neuer Post XYZ"
git push
```

GitHub Action baut automatisch auf dem Server:
1. `git pull`
2. `docker compose exec app python3 blog/blog_builder.py --build`
3. Nginx served sofort die neuen Dateien

**Live:** https://seasonalpha.ai/blog/

## Social Media & YouTube

Beim Build werden automatisch generiert:
- `{slug}/social/twitter_posts.txt` — 3 Tweet-Varianten
- `{slug}/social/linkedin_post.txt` — LinkedIn-Text
- `{slug}/youtube/video_script.txt` — 5-8 Min Video-Script
- `{slug}/youtube/video_script_short.txt` — 60 Sek YouTube-Short
- `{slug}/youtube/description.txt` — YouTube-Beschreibung
- `{slug}/youtube/tags.txt` — YouTube-Tags
