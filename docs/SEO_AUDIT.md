# SEO-Audit & 90-Tage-Plan — seasonalpha.ai

> Stand: 2026-06-15 · Erstellt vom `seo-experte`-Agenten · Living Doc.
> Kontext: Domain ~3 Monate alt, **0 Backlinks, 0 externe Klicks**, GSC meldet
> **293 „gecrawlt – nicht indexiert"**. Diagnose: kein technisches, sondern ein
> **Authority- + Trust- (YMYL) + Content-Tiefe-Problem**.

## Bewertung nach Disziplin

| Disziplin | Note | Befund |
|---|---|---|
| Technical SEO | **B+** | Canonicals, hreflang, robots.txt, Sitemap (114 URLs) korrekt. Schema solide (Organization/WebSite/FAQPage/SoftwareApplication/Breadcrumb). |
| **E-E-A-T / YMYL** | **F 🔴** | **KEIN Impressum, KEINE Datenschutzerklärung, KEIN Über-uns, KEIN realer Autor.** Rechtlich Pflicht (DDG §5/DSGVO) + größter Trust-Blocker. |
| Content | **C** | Blog median ~1050 W (ok), aber Pillar-Seiten dünn (z.B. „was-ist-saisonalitaet" 278 W). 32 Tool-Seiten mit nur ~300 W statischem Text (Wert im JS-Chart, für Googlebot unsichtbar). |
| **Off-Page / Authority** | **F 🔴** | 0 Backlinks, 0 externe Klicks. Der eigentliche Wachstums-Blocker. |
| Strukturierte Daten | **B–** | Vorhanden, aber Autor = Marke statt **Person**; **`Dataset`-Schema fehlt** (großer Hebel für eine Datenplattform → Google Dataset Search + Rich Results). |

**Warum „crawled not indexed" (293):** Junge Domain × YMYL-Finanzthema × kein Impressum/
Autor (Trust) × dünner statischer Content × 0 externe Signale = Google crawlt, stuft als
„nicht vertrauenswürdig/wertvoll genug" ein und hält die Indexierung zurück. Technik ist
NICHT die Ursache.

## 90-Tage-Plan (priorisiert nach Impact × Aufwand)

### Phase 1 — Fundament & Trust (Tag 1–30) · P0
*Unblockt YMYL-Indexierung + schafft Rechtssicherheit. Höchster Hebel, kleiner Aufwand.*
- [ ] **Impressum** (`/impressum`) — rechtlich Pflicht (DDG §5).
- [ ] **Datenschutzerklärung** (`/datenschutz`) — DSGVO-Pflicht (Supabase/Brevo/Stripe nennen).
- [ ] **Über-uns / Autor** (`/ueber-uns`) — **realer Mensch mit Credentials** (Trading-/
      Daten-Hintergrund), Foto, was die Methodik seriös macht. Kern-E-E-A-T-Signal.
- [ ] **Author-Schema** — Blog-Autor von `Organization` auf **`Person`** mit `sameAs`
      (LinkedIn/X), in `blog_post.html` + Über-uns verlinkt.
- [ ] **Disclaimer-Konsistenz** — „Analyse/Bildung, keine Anlageberatung" sichtbar (YMYL).
- [ ] **GSC/GA4-Baseline** — aktuelle Impressions/Index-Quote als Startwert festhalten.
- [ ] Footer + Nav: Links auf Impressum/Datenschutz/Über-uns (Trust + interne Verlinkung).

### Phase 2 — Content-Tiefe & erstes Linkable Asset (Tag 31–60) · P1
- [ ] **Pillar-Seiten vertiefen** — „Was ist Saisonalität" 278→1500+ W, einzigartig, mit
      Beispielen/Daten; als Hub für Themen-Cluster (intern verlinkt).
- [ ] **Tool-Seiten** (monatszyklus/opex/…): statischen Erklär-/Methodik-Text 300→800+ W
      + **FAQPage-Schema** (echte Fragen) → gegen „thin", Chance auf Rich Results.
- [ ] **Internes Cluster-Linking** — Pillar ↔ Tool ↔ Blog kontextuell verknüpfen.
- [ ] **1. Daten-Studie bauen** (zitierfähiges Asset, aus `shared/`+DB): z.B. „30 Jahre DAX —
      die statistisch 5 schlechtesten Handelstage" mit Chart + Methodik + `Dataset`-Schema.

### Phase 3 — Authority / Digital PR (Tag 61–90) · P1
*Das eigentliche Defizit. Asset → Distribution → Backlinks + erste Klicks.*
- [ ] Outreach-Zielliste: r/Finanzen, r/Mauerstrassenwetten, DE-Finanz-Blogger,
      finanzen.net/boerse-online-Redaktion, Trading-Newsletter, relevante Verzeichnisse.
- [ ] Pitch-Vorlagen je Zielgruppe (Daten-Hook, kein Werbe-Spam).
- [ ] Asset seeden + Brand-Mentions tracken; 2.–3. Studie nachlegen.
- [ ] Backlink-Monitoring etablieren (Ziel: 5–10 thematische Links in 90 Tagen).

### Laufend
GSC wöchentlich (Index-Quote, Queries) · 1 Daten-Studie + 2–4 Blog-Posts/Monat ·
Rankings für 3–5 Kern-Keywords tracken.

## KPIs (Erfolg messbar)
- **Index-Quote** (indexiert / eingereicht) — Hauptindikator, soll 30→90 Tage steigen.
- **GSC-Impressions** > 0 → wachsend; **erste externe Klicks**.
- **Backlinks**: 0 → 5–10 thematische (90 Tage).
- **Rankings**: 3–5 Kern-Keywords (z.B. „DAX Saisonalität", „Sell in May Backtest",
  „saisonale Aktien") in Top 50 → Top 20.

## Wichtigste Erkenntnis
Technik weiter optimieren bringt **fast nichts**, solange Trust (P0) + Authority (P1) fehlen.
Reihenfolge zwingend: **erst Impressum/Autor/Trust, dann Content-Tiefe, dann Backlinks.**
