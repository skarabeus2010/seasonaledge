# SeasonalEdge "Light Live" — Launch-Plan

> Erstellt: 2026-03-20 | Status: Geplant

## Ziel
Schnellstmöglich eine reduzierte "Light"-Version von SeasonalEdge mit eigener Domain live bringen.
- Sprache: Deutsch (EN kommt später)
- Newsletter-Signup muss funktionieren (Brevo API)
- Professionelle Custom Domain (kein streamlit.app in der URL)
- Sofortige Sichtbarkeit durch SEO-Basics + Paid/Organic Marketing

---

## 1. Light Pages (5 + Home)

| Page | Datei | Begründung | SEO-Keyword |
|------|-------|------------|-------------|
| **Home** | `pages/0_🏠_Home.py` | Landing Page, Newsletter — Pflicht | seasonaledge, saisonalität börse |
| **Turn of the Month** | `pages/2_🔄_Turn_of_the_Month.py` | Kürzeste Page, sauberer Code, bekannter Effekt | turn of the month strategie |
| **Weekday Analyse** | `pages/4_📅_Weekday_Analyse.py` | Leicht verständlich, gute Visuals | wochentagseffekt aktien |
| **Monthly Performance** | `pages/5_📆_Monthly_Performance.py` | Heatmaps, TDOM — starke Showcase | sell in may, saisonalität dax |
| **Mondphasen** | `pages/7_🌕_Mondphasen.py` | Unique Differentiator, kein Wettbewerber hat das | mondphasen börse |
| **Overnight vs Intraday** | `pages/12_🌙_Overnight_vs_Intraday.py` | Institutional-grade Insight | overnight performance dax |

### Deaktivierte Pages
Alle anderen Pages werden nach `pages/_disabled/` verschoben (Streamlit ignoriert Unterordner):
- `1_📊_Erweiterte_Analyse.py`
- `3_📅_Feiertags_Effekt.py`
- `6_🏛️_Zentralbanken.py`
- `8_🧠_TruePath.py`
- `9_🚦_Strategien.py`
- `10_📅_OPEX.py`
- `11_Intra_Decade_Seasonality_1.py`
- `13_💥_Shock_Analyzer.py`
- `14_🔄_Sector_Rotation.py`
- `15_🧠_KI_Score.py`
- `16_🔍_Market_Scanner.py`
- `17_⭐_Premium_Dashboard.py`
- `18_📅_TDOM_Analyse.py`
- `19_📉_Spot_Vol_Beta.py`
- `unsubscribe.py`

---

## 2. Home Page Überarbeitung

### Bugs fixen
- **`_PAGES` Array** referenziert falsche Dateinamen → alle `st.page_link()` kaputt
- Nur Light Pages im Module Grid anzeigen

### Änderungen
| Was | Aktion |
|-----|--------|
| Module Grid | Nur 5 Light Pages + 2-3 "Coming Soon" Karten (ausgegraut) |
| Newsletter CTA | Email-Input sofort sichtbar (Button-Gate entfernen), Benefit-Bullets daneben |
| Dow Jones Wars Iframe | Entfernen (900px base64 HTML iframe — zu langsam für Launch) |
| Stats | Zahlen an Light-Version anpassen |
| Footer | Impressum/Datenschutz/Risikohinweis als echte Links (rechtlich Pflicht DE) |
| Page Title | `st.set_page_config(page_title="SeasonalEdge – Saisonale Börsenanalyse")` |

---

## 3. Deployment mit Custom Domain

### Empfehlung: Railway.app
- **~5$/Monat**, Custom Domain, SSL inklusive, GitHub-Deployment
- Kein "streamlit.app" in der URL — professioneller Eindruck
- Alternative: Fly.io (~3-5$/Monat) oder eigener VPS (Hetzner ~4€/Monat)

### Dockerfile
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "seasonal_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### .dockerignore
```
logs/
.git/
__pycache__/
pages/_disabled/
.github/
docs/
```

### .streamlit/config.toml
```toml
[theme]
primaryColor = "#4d9fff"
backgroundColor = "#080c12"
secondaryBackgroundColor = "#0f1923"
textColor = "#c8d6e5"

[server]
headless = true
enableCORS = false
enableXsrfProtection = true
enableStaticServing = true

[browser]
gatherUsageStats = false
```

> **Wichtig:** `enableStaticServing = true` ermöglicht das Ausliefern von
> `static/robots.txt` und `static/sitemap.xml` unter der Root-URL.

### Deployment-Schritte
1. `Dockerfile` + `.dockerignore` + `.streamlit/config.toml` erstellen
2. `requirements.txt` vervollständigen (nur Light-Dependencies)
3. Railway-Projekt anlegen → GitHub-Repo verbinden
4. Environment Variables setzen: `brevo_api_key`, `brevo_list_id`
5. Custom Domain konfigurieren + DNS-Einträge
6. Deploy + Smoke Test

---

## 4. Requirements (Light Version)

```
streamlit>=1.30.0
pandas>=2.0.0
numpy>=1.24.0
plotly>=5.18.0
requests>=2.28.0
python-dateutil>=2.8.0
```

**Bewusst NICHT enthalten** (nur für Premium/deaktivierte Pages):
- `supabase` — nur für DB-Persistence (Light braucht das noch nicht)
- `scipy`, `scikit-learn` — nur für AI-Modelle (TruePath, KI Score)
- `prophet`, `xgboost` — nur für Forecasting

---

## 5. Infrastruktur-Fixes

### Logger (shared/logger.py)
- Schreibt in `logs/` Verzeichnis
- Docker hat beschreibbares Filesystem → kein Problem
- Trotzdem: Fallback auf stdout als Sicherheit einbauen

### seasonal_app.py
- Entrypoint prüfen, ggf. vereinfachen für Light-Version

---

## 6. SEO & Technische Sichtbarkeit

### Realistische SEO-Einschätzung
> **Streamlit ist keine SEO-Plattform.** Es ist eine JavaScript-SPA — Google rendert
> JS zwar, aber verzögert und unzuverlässig. Organisches SEO wird **nicht der
> Haupt-Traffic-Kanal** sein. Trotzdem: die folgenden Basics kosten wenig und
> helfen bei Nischen-Keywords mit geringer Konkurrenz.

### Nischen-Vorteil
Die Ziel-Keywords haben niedriges Suchvolumen aber hohe Kauf-/Interesse-Intention:
- „mondphasen börse" — kaum Konkurrenz deutschsprachig
- „turn of the month strategie" — keine großen Player
- „wochentagseffekt aktien" — Nische
- „overnight performance dax" — fast kein Content vorhanden
- „saisonalität dax" — moderate Konkurrenz

### Technische SEO-Maßnahmen (Launch-Tag)

| # | Maßnahme | Details | Aufwand |
|---|----------|---------|---------|
| S1 | **Page Titles** | `st.set_page_config(page_title="...")` pro Page mit Keyword | S |
| S2 | **robots.txt** | `static/robots.txt` → `User-agent: * Allow: /` | S |
| S3 | **sitemap.xml** | `static/sitemap.xml` mit allen 6 URLs | S |
| S4 | **Google Search Console** | Domain verifizieren (DNS), Sitemap einreichen, Pages zur Indexierung anfordern | S |
| S5 | **Bing Webmaster Tools** | Gleich wie S4, Bing indexiert oft schneller | S |
| S6 | **PageSpeed Check** | Google PageSpeed Insights direkt nach Launch → Baseline messen | S |

### Page Titles (S1 — konkreter Plan)
```python
# Home
st.set_page_config(page_title="SeasonalEdge – Saisonale Börsenanalyse", page_icon="📊")

# Turn of the Month
st.set_page_config(page_title="Turn of the Month Effekt – SeasonalEdge", page_icon="🔄")

# Weekday
st.set_page_config(page_title="Wochentagseffekt Aktien & ETFs – SeasonalEdge", page_icon="📅")

# Monthly
st.set_page_config(page_title="Monatliche Saisonalität DAX & S&P 500 – SeasonalEdge", page_icon="📆")

# Mondphasen
st.set_page_config(page_title="Mondphasen & Börse – Vollmond-Effekt Analyse – SeasonalEdge", page_icon="🌕")

# Overnight
st.set_page_config(page_title="Overnight vs Intraday Performance – SeasonalEdge", page_icon="🌙")
```

### robots.txt (S2)
```
User-agent: *
Allow: /
Sitemap: https://seasonaledge.app/static/sitemap.xml
```

### sitemap.xml (S3)
```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://seasonaledge.app/</loc><priority>1.0</priority></url>
  <url><loc>https://seasonaledge.app/Turn_of_the_Month</loc><priority>0.8</priority></url>
  <url><loc>https://seasonaledge.app/Weekday_Analyse</loc><priority>0.8</priority></url>
  <url><loc>https://seasonaledge.app/Monthly_Performance</loc><priority>0.8</priority></url>
  <url><loc>https://seasonaledge.app/Mondphasen</loc><priority>0.8</priority></url>
  <url><loc>https://seasonaledge.app/Overnight_vs_Intraday</loc><priority>0.8</priority></url>
</urlset>
```
> **Hinweis:** Die exakten URLs müssen nach Deployment geprüft werden. Streamlit
> generiert URLs aus den Dateinamen (ohne Emoji-Prefixe).

### Was NICHT funktioniert bei Streamlit (Erwartungen managen)
- ❌ `<meta name="description">` via `st.markdown()` — wird von Crawlern nicht zuverlässig gelesen
- ❌ Schema.org/JSON-LD — gleiche Einschränkung (JS-rendered)
- ❌ Server-Side Rendering — Streamlit rendert alles client-side
- ❌ Statische HTML-Seiten — nicht möglich ohne Migration

→ **Fazit:** Organisches SEO ist ein Bonus, nicht die Strategie. Der echte Traffic kommt über Paid + Social.

---

## 7. Vermarktung & Traffic (ab Launch-Tag)

### Strategie
Streamlit-SEO ist limitiert → **Paid Ads + Social Media sind die Haupt-Traffic-Quellen.**
Die Nischen-Keywords haben geringe Konkurrenz und hohe Intention — perfekt für Google Ads.

### Google Ads (Top-Priorität)
| Kampagne | Keywords | CPC (geschätzt) | Landing Page |
|----------|----------|-----------------|--------------|
| Mondphasen | mondphasen börse, vollmond aktien | 0,30–0,80 € | Mondphasen-Page |
| Saisonalität | saisonalität dax, sell in may | 0,50–1,20 € | Monthly-Page |
| Wochentagseffekt | wochentagseffekt aktien, montag börse | 0,30–0,60 € | Weekday-Page |
| Turn of Month | turn of the month strategie | 0,30–0,50 € | TotM-Page |
| Overnight | overnight performance dax, gap trading | 0,50–1,00 € | Overnight-Page |

- **Test-Budget:** 50–100 €/Woche zum Start
- **Ziel:** Newsletter-Signups messen (Conversion Tracking über Brevo)
- **Jede Ad verlinkt auf die passende Analyse-Page mit Newsletter-CTA**

### Social Media (organisch + bezahlt)
| Plattform | Strategie | Frequenz | Budget |
|-----------|-----------|----------|--------|
| **LinkedIn** | Mini-Insights + Chart-Screenshots + Link | 3x/Woche | 10–20 €/Woche Boost |
| **X (Twitter)** | Threads: "5 Börsen-Saisonalitäten die niemand kennt" | 3x/Woche | organisch |
| **Instagram** | Reels: Kurze Chart-Animationen, "Wusstest du...?" | 2x/Woche | 10–20 €/Woche |
| **Reddit** | r/Finanzen, r/mauerstrassenwetten — echte Insights teilen | 1x/Woche | organisch |

### Content-Ideen für Social (erste Woche)
1. "Der Montag-Effekt 2026 – stimmt er noch?" → Screenshot Weekday-Page + Link
2. "Kauft die Börse bei Vollmond? Die Daten sagen..." → Mondphasen-Chart
3. "Turn of the Month: Warum die letzten 3 + ersten 3 Handelstage entscheidend sind"
4. "Overnight vs. Intraday: Wo steckt die echte Rendite?" → Gap-Analyse Chart
5. "Sell in May 2026 — was sagen 100 Jahre Daten?" → Monthly Heatmap

### Newsletter Launch-Kampagne
- Bestandsabonnenten (Brevo): "SeasonalEdge ist live!" Announcement
- Jede Page hat Newsletter-CTA
- Lead-Magnet Idee (Woche 2): "Kostenloser Saisonalitäts-Report 2026" als PDF → Email-Gate

### Weitere Quick Wins
- **Gastartikel:** 1-2 Beiträge auf deutschen Finance-Blogs ("Die 5 besten Saisonalitäts-Strategien 2026")
- **X/Twitter Thread:** Mondphasen-Analyse mit Charts → virales Potenzial
- **Finance-Communities:** Trading-Gruppen (Facebook, Telegram, Discord)

---

## 8. Implementierungs-Reihenfolge

### Phase A: Infrastruktur (~1h, alles parallel möglich)
| # | Task | Aufwand |
|---|------|---------|
| A1 | `.streamlit/config.toml` erstellen (inkl. `enableStaticServing`) | S |
| A2 | `requirements.txt` vervollständigen | S |
| A3 | Pages nach `pages/_disabled/` verschieben | S |
| A4 | `Dockerfile` + `.dockerignore` erstellen | S |
| A5 | Logger Fallback prüfen/fixen | S |
| A6 | `static/robots.txt` + `static/sitemap.xml` erstellen | S |

### Phase B: Home Page (~2h)
| # | Task | Aufwand |
|---|------|---------|
| B1 | `_PAGES` Array fixen (nur Light Pages) | S |
| B2 | Dow Jones Wars Iframe entfernen | S |
| B3 | Newsletter CTA optimieren (immer sichtbar) | S |
| B4 | Module Grid: Light Pages + Coming Soon Karten | M |
| B5 | Stats + Footer updaten | S |
| B6 | SEO Page Titles in allen 6 Pages setzen | S |

### Phase C: Deploy (~1h)
| # | Task | Aufwand |
|---|------|---------|
| C1 | Lokaler Test aller Light Pages | M |
| C2 | Railway Setup + GitHub verbinden | S |
| C3 | Custom Domain + DNS konfigurieren | S |
| C4 | Smoke Test Production | S |

### Phase D: Sichtbarkeit (~2-3h, parallel zu Phase C)
| # | Task | Aufwand |
|---|------|---------|
| D1 | Google Search Console: Domain verifizieren + Sitemap einreichen | S |
| D2 | Bing Webmaster Tools: Domain verifizieren | S |
| D3 | Google Ads Kampagne aufsetzen (50 € Test-Budget) | M |
| D4 | 3 Social-Media-Posts erstellen + posten | M |
| D5 | Newsletter "Wir sind live!" an Brevo-Liste senden | S |
| D6 | PageSpeed Insights Check + ggf. Optimierung | S |

### Gesamt: ~6-7 Stunden (4h Technik + 2-3h Marketing)

---

## 9. Später (NICHT Teil des Light Launch)

### Technik
- [ ] EN-Übersetzung (i18n-System mit JSON + `t()` Helper)
- [ ] Premium-Gating (TruePath, Strategies, KI Score)
- [ ] Stripe Freemium/Abo-Integration
- [ ] Impressum/Datenschutz als eigene Pages mit Inhalt
- [ ] Error Tracking (Sentry)

### SEO & Marketing
- [ ] Blog/Content-Hub (statische Seiten neben Streamlit für echtes SEO)
- [ ] Schema.org strukturierte Daten (erst sinnvoll nach Next.js Migration)
- [ ] Analytics (Mixpanel/PostHog oder Google Analytics)
- [ ] Lead-Magnet: "Saisonalitäts-Report 2026" PDF
- [ ] Retargeting-Pixel (Meta, Google)
- [ ] Domain: seasonaledge.app registrieren

---

## 10. Verification Checklist

### Technik
- [ ] Alle 5 Light Pages laden ohne Fehler
- [ ] Newsletter Signup funktioniert (Brevo API Test mit echter Email)
- [ ] Deaktivierte Pages sind NICHT in der Sidebar sichtbar
- [ ] Charts rendern korrekt (`apply_se_theme()`)
- [ ] Kein `import yfinance` in aktiven Pages
- [ ] Custom Domain erreichbar mit SSL
- [ ] Footer: Impressum/Datenschutz Links vorhanden
- [ ] Mobile: Seite ist benutzbar auf Smartphone

### SEO & Marketing
- [ ] `robots.txt` erreichbar unter `domain.app/static/robots.txt`
- [ ] `sitemap.xml` erreichbar und URLs korrekt
- [ ] Google Search Console: Domain verifiziert, Sitemap eingereicht
- [ ] Alle 6 Pages haben aussagekräftige `page_title`
- [ ] Google Ads: Mindestens 1 Kampagne aktiv
- [ ] Erster Social-Media-Post veröffentlicht
- [ ] PageSpeed Score >= 70 (Mobile)
