# SeasonAlpha Blog — Workflow-Anleitung

> Stand: 2026-03-27

## Option A: KI-generiert (5 Min + 10 Min Review)

```bash
# 1. Entwurf generieren lassen
python blog/blog_builder.py --generate "Sell in May 2026" --ticker ^GSPC --category marktausblick

# 2. Entwurf reviewen und anpassen
#    → blog/posts/2026-04-01_sell-in-may-2026.md oeffnen und editieren

# 3. HTML + Charts + Social generieren
python blog/blog_builder.py --build

# 4. Veroeffentlichen
git add blog/posts/ && git commit -m "Blog: Sell in May 2026" && git push
```

**Ergebnis:** Blog-Post live + 3 Tweet-Vorschlaege + LinkedIn-Post + OG-Image

---

## Option B: Selbst schreiben (20 Min)

### 1. Neue Datei erstellen

Datei: `blog/posts/2026-04-01_sell-in-may-2026.md`

```markdown
---
title: "Sell in May 2026 — Funktioniert die Strategie noch?"
slug: sell-in-may-2026
date: 2026-04-01
category: marktausblick
tags: [sell-in-may, saisonalitaet, sp500]
description: "Analyse der Sell-in-May Strategie mit aktuellen Daten."
ticker: ^GSPC
status: published
---

## Einleitung

Die Sell-in-May Strategie besagt, dass Anleger von Mai bis Oktober
schlechtere Renditen erzielen als von November bis April.

{{chart:seasonal_yearly:^GSPC:20}}

Wie der saisonale Verlauf des S&P 500 zeigt...

## Analyse

{{chart:monthly_heatmap:^GSPC:10}}

Die Monats-Heatmap verdeutlicht...

## Fazit

...
```

### 2. Bauen und veroeffentlichen

```bash
python blog/blog_builder.py --build
git add blog/posts/ && git commit -m "Blog: Sell in May 2026" && git push
```

---

## Option C: Auf Vorrat schreiben (1x pro Monat, 30 Min)

### 1. Posts mit Claude vorproduzieren

Sage Claude: "Schreib 4 Posts fuer April"

Claude generiert 4 Markdown-Dateien mit `status: scheduled`:

```
blog/posts/2026-04-01_sell-in-may.md          (publish_date: 2026-04-01)
blog/posts/2026-04-08_rsi-filter.md           (publish_date: 2026-04-08)
blog/posts/2026-04-15_mai-ausblick.md         (publish_date: 2026-04-15)
blog/posts/2026-04-22_trifecta-tutorial.md    (publish_date: 2026-04-22)
```

### 2. Alle auf einmal reviewen und committen

```bash
# Alle Posts reviewen, dann:
git add blog/posts/ && git commit -m "Blog: 4 Posts fuer April" && git push
```

### 3. Automatische Veroeffentlichung

Der Nightly-Job (GitHub Action) rebuildet taeglich.
Posts erscheinen automatisch am `publish_date`.

---

## Verfuegbare Chart-Tags

| Tag | Beschreibung |
|-----|-------------|
| `{{chart:seasonal_yearly:TICKER:JAHRE}}` | Saisonaler Jahresverlauf |
| `{{chart:monthly_heatmap:TICKER:JAHRE}}` | Monats-Rendite Heatmap |
| `{{chart:weekday_bars:TICKER:JAHRE}}` | Wochentag-Performance |
| `{{chart:tom_effect:TICKER:JAHRE}}` | Turn-of-Month Effekt |

---

## Kategorien

| Kategorie | Slug | Wann verwenden |
|-----------|------|---------------|
| **Education** | `education` | Grundlagen, Theorie (Was ist Saisonalitaet?) |
| **Marktausblick** | `marktausblick` | Aktuelle Analysen (Mai-Saisonalitaet, Ticker-Analysen) |
| **Tutorials** | `tutorials` | SeasonAlpha Features erklaeren (Indikator-Filter nutzen) |

---

## Frontmatter-Felder

| Feld | Pflicht | Beschreibung |
|------|---------|-------------|
| `title` | Ja | Post-Titel (SEO-optimiert) |
| `slug` | Ja | URL-Pfad (z.B. sell-in-may-2026) |
| `date` | Ja | Erstelldatum (YYYY-MM-DD) |
| `category` | Ja | education, marktausblick, oder tutorials |
| `tags` | Nein | Liste von Tags fuer Filterung |
| `description` | Ja | Meta-Description (max 160 Zeichen) |
| `ticker` | Nein | Haupt-Ticker des Posts (fuer Charts) |
| `status` | Ja | draft, scheduled, oder published |
| `publish_date` | Nein | Veroeffentlichungsdatum (fuer scheduled Posts) |

---

## Automatisch generierte Social-Media Dateien

Pro Post werden automatisch erstellt:

```
blog/output/sell-in-may-2026/
  index.html                    ← Blog-Post (HTML)
  social/
    og_image.png                ← Vorschaubild fuer Link-Preview (1200x630)
    twitter_posts.txt           ← 3 Tweet-Varianten
    linkedin_post.txt           ← LinkedIn-Post
    chart_cards/                ← Chart-Screenshots als PNG
```

### Social-Media Workflow

1. Post veroeffentlichen (git push)
2. `blog/output/POST/social/` oeffnen
3. Tweet-Text kopieren → auf Twitter/X posten + Chart-Bild anhaengen
4. LinkedIn-Text kopieren → auf LinkedIn posten
5. Fertig! (~5 Min pro Plattform)
