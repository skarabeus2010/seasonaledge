# Programmatic SEO Engine — SeasonAlpha

> Stand: 2026-03-25 | 94 Landingpages | Alle Ticker aus SYMBOLS

## Ueberblick

Die SEO Engine generiert automatisch suchmaschinenoptimierte HTML-Landingpages
fuer jeden Finanztitel aus `shared/symbols.py`. Ziel: Maximale Google-Sichtbarkeit
fuer Suchanfragen wie "Apple Saisonalitaet", "DAX saisonale Muster", "Bitcoin bester Monat".

**Prinzip:** Eine Seite pro Ticker. 94 Ticker = 94 Landingpages = 94 Chancen bei Google zu ranken.

## Dateien

| Datei | Beschreibung |
|-------|-------------|
| `seo/seo_template.html` | Jinja2 HTML-Template mit Platzhaltern |
| `seo/programmatic_seo_builder.py` | Generator: Pages + Sitemap + robots.txt + Disclaimer |
| `seo/output/*.html` | 94 generierte Landingpages |
| `seo/output/sitemap.xml` | 99 URLs (5 statische + 94 Analyse-Seiten) |
| `seo/output/robots.txt` | Crawler-Regeln + Sitemap-Verweis |
| `seo/output/disclaimer.html` | YMYL-konformer Haftungsausschluss (7 Abschnitte) |
| `seo/output/google*.html` | Google Search Console Verifizierungsdatei |

## Ausfuehren

```bash
# Voraussetzung: Jinja2 installiert (pip install Jinja2)
py seo/programmatic_seo_builder.py
```

Ergebnis: 94 HTML-Dateien + sitemap.xml + robots.txt + disclaimer.html in `seo/output/`

## Datenquelle

Ticker kommen automatisch aus `shared/symbols.py` (SYMBOLS-Dict, 94 Eintraege).
Der Builder generiert:
- **Slug** automatisch via `make_slug()` (z.B. "S&P 500" → "sp-500-saisonalitaet")
- **Typ** aus Kategorie-Mapping (US-Aktie → "Aktie", Krypto → "Kryptowaehrung")
- **Statistiken** aktuell als Platzhalter (deterministisch per Hash), spaeter aus Supabase

Neue Ticker hinzufuegen: Einfach in `shared/symbols.py` eintragen → naechster Build generiert die Seite.

## SEO-Strategie

### Was Google sieht (pro Seite)

| Element | Beispiel |
|---------|---------|
| **Title** | `Apple (AAPL) Saisonalitaet & historische Muster \| SeasonAlpha` |
| **Meta Description** | `Apple (AAPL) saisonale Analyse: Historisch bester Monat ist Oktober.` |
| **H1** | `Apple (AAPL) – Saisonalitaet & historische Muster` |
| **Canonical URL** | `https://seasonalpha.ai/analyse/apple-saisonalitaet` |
| **Schema.org** | JSON-LD FinancialProduct (fuer Rich Snippets) |
| **Open Graph** | Titel + Description (fuer Social Media Vorschau) |
| **Google Verification** | Meta-Tag in allen Seiten |

### Seitenstruktur

```
1. Breadcrumb Navigation (SeasonAlpha > Analysen > Apple)
2. H1 mit Suchbegriff
3. Einleitungstext (generiert aus Daten)
4. Statistik-Karten (Bester Monat, Win-Rate, Oe Rendite)
5. Chart-Platzhalter (oeffentlich sichtbar)
6. Erklaerungstext (SEO-Fuellung)
7. [GEBLURRT] KI-Prognose Bereich
8. CTA-Button: "KI-Prognose kostenlos freischalten"
9. Weiterer SEO-Text (Was ist Saisonalitaet?)
10. Footer (Impressum, Datenschutz, Disclaimer)
```

### Blur-Effekt (Conversion-Mechanismus)

Der KI-Prognose-Bereich ist per CSS `filter: blur(8px)` verschwommen:
- User sieht dass es eine KI-Analyse gibt
- Kann den Inhalt nicht lesen
- CTA-Button liegt als Overlay darueber
- Klick fuehrt zur Registrierung auf seasonalpha.ai

### Datenschutz (Legal-Tech Vorgabe)

- KEIN Google Analytics
- KEIN Facebook Pixel
- KEINE Cookies
- KEINE externen Skripte
- KEINE externen Fonts (System-Fonts)
- Alles inline CSS (kein externes Stylesheet)
- DSGVO-konform ohne Cookie-Banner

## Deployment

### Architektur (Hetzner VPS)

```
Browser → seasonalpha.ai/analyse/apple-saisonalitaet
                ↓
           Nginx (Port 80/443)
                ↓
         /app/seo/output/apple-saisonalitaet.html  ← statische HTML

Browser → seasonalpha.ai/ (alles andere)
                ↓
         Streamlit App (Port 8501)
```

### Nginx-Routen (deploy/nginx.conf)

| URL | Ziel |
|-----|------|
| `/analyse/{slug}` | `seo/output/{slug}.html` (94 Landingpages) |
| `/disclaimer` | `seo/output/disclaimer.html` |
| `/sitemap.xml` | `seo/output/sitemap.xml` |
| `/robots.txt` | `seo/output/robots.txt` |
| `/google*.html` | Google Search Console Verifizierung |
| `/` (alles andere) | Streamlit App (Reverse Proxy) |

### docker-compose.yml Volumes

```yaml
nginx:
  volumes:
    - ./seo/output:/app/seo/output:ro           # SEO-Landingpages
    - ./seo/output/sitemap.xml:/app/static/sitemap.xml:ro
    - ./seo/output/robots.txt:/app/static/robots.txt:ro
```

### Auto-Deploy (GitHub Actions)

Bei Push auf `master`:
1. `git pull origin master`
2. `python3 seo/programmatic_seo_builder.py` (Seiten neu generieren)
3. `docker compose up -d --build`

## Disclaimer (YMYL)

Die Datei `seo/output/disclaimer.html` enthaelt 7 Abschnitte:
1. Keine Anlageberatung (WpHG, KWG, §34f GewO)
2. Historische Daten & Saisonalitaet
3. KI-Modelle & Halluzinations-Hinweis
4. Datenquellen & Genauigkeit
5. Haftungsbeschraenkung
6. Interessenkonflikte
7. Anwendbares Recht

## Google Search Console

- **Property:** seasonalpha.ai (URL-Praefix)
- **Verifizierung:** DNS-TXT-Record bei STRATO + HTML-Meta-Tag in allen Seiten
- **Sitemap:** `https://seasonalpha.ai/sitemap.xml` (99 URLs)

## Erweiterung

### Echte Daten aus Supabase

In `build_titel_daten()` die Platzhalter-Statistiken durch echte Berechnungen ersetzen:

```python
from shared.supabase_client import fetch_monthly_stats

for ticker in SYMBOLS.keys():
    stats = fetch_monthly_stats(ticker)
    bester_monat = max(stats, key=lambda s: s["avg_return"])
    # ... Template fuellen
```

### Echte Charts einbetten

```python
from shared.charts import build_seasonal_chart

fig = build_seasonal_chart(...)
fig.write_image(f"seo/output/charts/{slug}.png")
```

```html
<img src="charts/{{ slug }}.png" alt="{{ name }} Saisonalitaet Chart"
     width="800" height="400" loading="lazy">
```

## Metriken & Ziele

| Metrik | Ist | Ziel |
|--------|-----|------|
| Seiten | 94 | 500+ (weitere Ticker hinzufuegen) |
| Core Web Vitals | LCP < 1s | LCP < 1s, CLS < 0.1 |
| Suchbegriffe | "[Ticker] Saisonalitaet", "[Name] saisonale Muster" | Top 10 |
| Conversion | CTA-Klick → Registrierung | >5% CTR |
| Kosten | 0 EUR (auf bestehendem VPS) | 0 EUR |
