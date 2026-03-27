# SeasonAlpha — Blog, Social Media & YouTube Workflow

> Stand: 2026-03-27

---

## Schnellstart: Was mache ich konkret?

### Schritt 1: Blog-Post erstellen (waehle eine Option)

| Option | Aufwand | Wie |
|--------|---------|-----|
| **A) KI-generiert** | 15 Min | Terminal-Befehl → Review → Publish |
| **B) Selbst schreiben** | 20 Min | Markdown-Datei erstellen → Build → Publish |
| **C) Auf Vorrat mit Claude** | 30 Min/Monat | "Schreib 4 Posts fuer April" → Review → Publish |

### Schritt 2: Social Media posten (5 Min pro Plattform)

Der Builder hat automatisch fertige Texte + Bilder generiert:
1. Oeffne `blog/output/DEIN-POST/social/`
2. Kopiere `twitter_posts.txt` → Poste auf Twitter/X + Chart-Bild
3. Kopiere `linkedin_post.txt` → Poste auf LinkedIn
4. Fertig!

### Schritt 3: YouTube Video (optional, 30-60 Min)

Der Builder hat automatisch ein Video-Script generiert:
1. Oeffne `blog/output/DEIN-POST/youtube/video_script.txt`
2. Lies das Script ein (oder nutze KI-Voiceover)
3. Zeige die Charts aus der App (Screen-Recording)
4. Lade auf YouTube hoch mit `description.txt` und `tags.txt`

---

## Option A: KI-generiert (5 Min + 10 Min Review)

```bash
# 1. Entwurf generieren lassen
python blog/blog_builder.py --generate "Sell in May 2026" --ticker ^GSPC --category marktausblick

# 2. Entwurf reviewen und anpassen
#    → blog/posts/2026-04-01_sell-in-may-2026.md oeffnen und editieren

# 3. HTML + Charts + Social + YouTube generieren
python blog/blog_builder.py --build

# 4. Veroeffentlichen
git add blog/posts/ && git commit -m "Blog: Sell in May 2026" && git push
```

**Ergebnis:** Blog live + 3 Tweets + LinkedIn-Post + OG-Image + Video-Script + Thumbnail

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

## Option C: Auf Vorrat mit Claude (1x pro Monat, 30 Min)

### 1. Sage Claude in einer Session:

> "Schreib 4 Blog-Posts fuer April: 2x Marktausblick, 1x Education, 1x Tutorial"

Claude generiert 4 Markdown-Dateien:

```
blog/posts/2026-04-01_sell-in-may.md          (publish_date: 2026-04-01)
blog/posts/2026-04-08_rsi-filter.md           (publish_date: 2026-04-08)
blog/posts/2026-04-15_mai-ausblick.md         (publish_date: 2026-04-15)
blog/posts/2026-04-22_trifecta-tutorial.md    (publish_date: 2026-04-22)
```

### 2. Alle auf einmal reviewen und committen

```bash
git add blog/posts/ && git commit -m "Blog: 4 Posts fuer April" && git push
```

### 3. Automatische Veroeffentlichung

Der Nightly-Job rebuildet taeglich. Posts erscheinen am `publish_date` automatisch.

---

## Social Media Workflow (Detail)

### Twitter/X (3-5x pro Woche)

```
1. blog/output/DEIN-POST/social/twitter_posts.txt oeffnen
2. Eine der 3 Varianten auswaehlen
3. Auf Twitter/X posten
4. Chart-Bild aus social/chart_cards/ anhaengen
5. Fertig! (2 Min)
```

**Was du bekommst (automatisch generiert):**
- 3 Tweet-Varianten (verschiedene Hooks)
- Chart-Screenshots als PNG (perfekte Groesse fuer Twitter)
- Hashtag-Vorschlaege

### LinkedIn (2x pro Woche)

```
1. blog/output/DEIN-POST/social/linkedin_post.txt oeffnen
2. Text kopieren → auf LinkedIn posten
3. OG-Image wird automatisch angezeigt (via Link-Preview)
4. Fertig! (2 Min)
```

**Was du bekommst (automatisch generiert):**
- Laengerer Post-Text (3-5 Absaetze)
- Professioneller Ton
- CTA zu SeasonAlpha

### Wann posten?

| Plattform | Beste Zeit | Frequenz |
|-----------|-----------|----------|
| Twitter/X | 8-9 Uhr, 12-13 Uhr, 17-18 Uhr | 3-5x/Woche |
| LinkedIn | Di-Do, 8-10 Uhr | 2x/Woche |

---

## YouTube Workflow (Detail)

### Fuer ein vollstaendiges Video (5-10 Min)

```
1. blog/output/DEIN-POST/youtube/ oeffnen
2. video_script.txt lesen (= dein Sprechtext)
3. Screen-Recording starten (OBS Studio oder aehnlich)
4. SeasonAlpha App oeffnen, Charts zeigen wie im Script beschrieben
5. Script vorlesen oder KI-Voiceover nutzen
6. Video auf YouTube hochladen:
   - Titel: aus dem Blog-Post
   - Beschreibung: description.txt (mit Timestamps + Links)
   - Tags: tags.txt
   - Thumbnail: thumbnail.png
7. Fertig!
```

### Fuer YouTube Shorts (60 Sek)

```
1. video_script_short.txt lesen (= 60-Sek Version)
2. Einen Chart in der App zeigen + kurz erklaeren
3. Als Short hochladen
```

### Was du bekommst (automatisch generiert)

| Datei | Beschreibung |
|-------|-------------|
| `video_script.txt` | Vollstaendiger Sprechtext (5-10 Min) mit Chart-Verweisen |
| `video_script_short.txt` | 60-Sek Version fuer YouTube Shorts |
| `thumbnail.png` | YouTube Thumbnail (1280x720, SeasonAlpha Branding) |
| `description.txt` | YouTube-Beschreibung mit Timestamps + Links |
| `tags.txt` | YouTube-Tags (SEO-optimiert) |
| `chart_animations/` | Chart-GIFs fuer Screencasts |

### Video-Formate

| Format | Laenge | Frequenz | Beispiel |
|--------|--------|----------|---------|
| Monatsausblick | 5-10 Min | 1x/Monat | "April 2026: Was sagt die Saisonalitaet?" |
| Strategie erklaert | 8-15 Min | 1x/Monat | "Sell in May — 130 Jahre Daten" |
| Quick Tips (Shorts) | 60 Sek | 2-4x/Monat | "S&P 500 steigt im Dez in 78% der Jahre" |
| Tool-Demo | 5-8 Min | 1x/Monat | "Indikator-Filter in SeasonAlpha" |

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
| **Marktausblick** | `marktausblick` | Aktuelle Analysen (Mai-Saisonalitaet, Ticker) |
| **Tutorials** | `tutorials` | SeasonAlpha Features erklaeren |

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
| `publish_date` | Nein | Veroeffentlichungsdatum (fuer scheduled) |

---

## Content-Kalender (Empfehlung)

### 4 Posts pro Monat:

| Woche | Kategorie | Beispiel |
|-------|-----------|---------|
| Woche 1 | Marktausblick | "Mai 2026: Saisonaler Ausblick S&P 500" |
| Woche 2 | Education | "Was ist der Turn-of-Month Effekt?" |
| Woche 3 | Marktausblick | "OPEX-Woche Mai: Was Trader wissen muessen" |
| Woche 4 | Tutorial | "Indikator-Filter: RSI + SMA kombinieren" |

### Redaktionsplan verwalten:

Datei `blog/calendar.yaml` enthaelt den Plan:

```yaml
2026-04:
  - date: 2026-04-01
    title: "Sell in May 2026"
    category: marktausblick
    ticker: ^GSPC
    status: scheduled
  - date: 2026-04-08
    title: "Was ist Saisonalitaet?"
    category: education
    status: draft
```
