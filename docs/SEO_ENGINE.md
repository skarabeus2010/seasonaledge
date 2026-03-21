# Programmatic SEO Engine — SeasonalEdge

> Stand: 2026-03-20 | 10 Landingpages | Erweiterbar auf 500+

## Ueberblick

Die SEO Engine generiert automatisch suchmaschinenoptimierte HTML-Landingpages
fuer jeden Finanztitel. Ziel: Maximale Google-Sichtbarkeit fuer Suchanfragen wie
"Apple Saisonalitaet", "DAX saisonale Muster", "Bitcoin bester Monat".

**Prinzip:** Eine Seite pro Ticker. Jede Seite rankt fuer ihren spezifischen
Suchbegriff. Bei 500 Tickern = 500 Landingpages = 500 Chancen bei Google zu ranken.

## Dateien

| Datei | Beschreibung |
|-------|-------------|
| `seo/seo_template.html` | Jinja2 HTML-Template mit Platzhaltern |
| `seo/programmatic_seo_builder.py` | Python-Skript das die Pages generiert |
| `seo/output/*.html` | Generierte HTML-Dateien (nicht in Git) |

## Ausfuehren

```bash
# Voraussetzung: Jinja2 installiert (pip install Jinja2)
py seo/programmatic_seo_builder.py
```

Ergebnis: 10 HTML-Dateien in `seo/output/`, z.B.:
- `apple-saisonalitaet.html`
- `dax-saisonalitaet.html`
- `bitcoin-saisonalitaet.html`

## SEO-Strategie

### Was Google sieht (pro Seite)

| Element | Beispiel |
|---------|---------|
| **Title** | `Apple (AAPL) Saisonalitaet & historische Muster \| SeasonalEdge` |
| **Meta Description** | `Apple (AAPL) saisonale Analyse: Historisch bester Monat ist Oktober. Kostenlos KI-Prognose freischalten.` |
| **H1** | `Apple (AAPL) – Saisonalitaet & historische Muster` |
| **Canonical URL** | `https://seasonaledge.app/apple-saisonalitaet.html` |
| **Schema.org** | JSON-LD FinancialProduct (fuer Rich Snippets) |
| **Open Graph** | Titel + Description (fuer Social Media Vorschau) |

### Seitenstruktur

```
1. Breadcrumb Navigation (SeasonalEdge > Analysen > Apple)
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
- Klick fuehrt zur Registrierung auf seasonaledge.app

```css
.premium-content {
    filter: blur(8px);
    user-select: none;      /* Kein Markieren */
    pointer-events: none;   /* Kein Klicken */
}
```

### Datenschutz (Legal-Tech Vorgabe)

- KEIN Google Analytics
- KEIN Facebook Pixel
- KEINE Cookies
- KEINE externen Skripte
- KEINE externen Fonts (System-Fonts)
- Alles inline CSS (kein externes Stylesheet)
- DSGVO-konform ohne Cookie-Banner

## Template-Variablen

Das Template `seo_template.html` erwartet folgende Variablen:

| Variable | Typ | Beispiel | Beschreibung |
|----------|-----|---------|-------------|
| `ticker` | str | `AAPL` | Ticker-Symbol |
| `name` | str | `Apple` | Anzeigename |
| `slug` | str | `apple-saisonalitaet` | URL-Pfad (keine Umlaute/Leerzeichen) |
| `typ` | str | `Aktie` | Aktie, ETF, Index, Krypto, Rohstoff |
| `bester_monat` | str | `Oktober` | Historisch bester Monat |
| `win_rate` | str | `72` | Win-Rate in % (als String) |
| `avg_return` | str | `+3.2%` | Durchschnittsrendite im besten Monat |
| `jahre` | str | `20` | Anzahl analysierter Jahre |
| `datum` | str | `20.03.2026` | Aktualisierungsdatum (wird vom Skript gesetzt) |
| `ki_count` | int | `15` | Anzahl KI-Features (wird vom Skript gesetzt) |

## Aktuelle Titel (10)

| Ticker | Name | Slug | Typ | Bester Monat |
|--------|------|------|-----|-------------|
| AAPL | Apple | apple-saisonalitaet | Aktie | Oktober |
| ^GDAXI | DAX | dax-saisonalitaet | Index | November |
| BMW.DE | BMW | bmw-saisonalitaet | Aktie | April |
| BTC-USD | Bitcoin | bitcoin-saisonalitaet | Krypto | November |
| TSLA | Tesla | tesla-saisonalitaet | Aktie | Januar |
| GC=F | Gold | gold-saisonalitaet | Rohstoff | September |
| CL=F | Oel (WTI) | oel-saisonalitaet | Rohstoff | Februar |
| QQQ | Nasdaq 100 ETF | nasdaq-100-saisonalitaet | ETF | November |
| DIA | Dow Jones ETF | dow-jones-saisonalitaet | ETF | Dezember |
| SAP.DE | SAP | sap-saisonalitaet | Aktie | Oktober |

## Erweiterung

### Mehr Titel hinzufuegen

In `programmatic_seo_builder.py` einfach weitere Eintraege zu `TITEL_DATEN` hinzufuegen:

```python
{
    "ticker":       "MSFT",
    "name":         "Microsoft",
    "slug":         "microsoft-saisonalitaet",
    "typ":          "Aktie",
    "bester_monat": "November",
    "win_rate":     "71",
    "avg_return":   "+3.5%",
    "jahre":        "25",
},
```

### Daten aus DB statt hardcodiert

Spaeter koennen die Daten aus Supabase geladen werden:

```python
from shared.supabase_client import fetch_monthly_stats

# Statt hardcodierter Liste:
for ticker in SYMBOLS.keys():
    stats = fetch_monthly_stats(ticker)
    bester_monat = max(stats, key=lambda s: s["avg_return"])
    # ... Template fuellen
```

### Echte Charts einbetten

Der Chart-Platzhalter kann durch statische Chart-Bilder ersetzt werden:

```python
# In programmatic_seo_builder.py:
from shared.data import download_data, preprocess
from shared.calculations import build_year_data, calculate_seasonal_average
from shared.charts import build_seasonal_chart

fig = build_seasonal_chart(...)
fig.write_image(f"seo/output/charts/{slug}.png")
```

Dann im Template:
```html
<img src="charts/{{ slug }}.png" alt="{{ name }} Saisonalitaet Chart"
     width="800" height="400" loading="lazy">
```

### Deployment

Die generierten HTML-Dateien koennen deployed werden als:
- **Subdirectory** auf seasonaledge.app (z.B. `/analysen/apple-saisonalitaet.html`)
- **GitHub Pages** (kostenlos, automatisch via GitHub Actions)
- **Netlify / Vercel** (Static Site Hosting, kostenlos)
- **S3 + CloudFront** (fuer Scale)

### Sitemap generieren

Fuer Google Search Console eine `sitemap.xml` generieren:

```python
# Am Ende von build_seo_pages():
sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n'
sitemap += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
for titel in TITEL_DATEN:
    sitemap += f'  <url><loc>https://seasonaledge.app/{titel["slug"]}.html</loc></url>\n'
sitemap += '</urlset>'
```

## Metriken & Ziele

| Metrik | Ziel |
|--------|------|
| Seiten | 500+ (alle Ticker aus SYMBOLS) |
| Core Web Vitals | LCP < 1s, CLS < 0.1 (kein externes CSS/JS) |
| Suchbegriffe | "[Ticker] Saisonalitaet", "[Name] saisonale Muster" |
| Conversion | CTA-Klick → Registrierung auf seasonaledge.app |
| Kosten | 0 EUR (Static HTML, kein Server noetig) |
