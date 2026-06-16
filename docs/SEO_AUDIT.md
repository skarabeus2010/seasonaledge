# SEO-Audit & 90-Tage-Plan — seasonalpha.ai

> Stand: 2026-06-15 · Erstellt vom `seo-experte`-Agenten · Living Doc.
> Kontext: Domain ~3 Monate alt, **0 Backlinks, 0 externe Klicks**, GSC meldet
> **293 „gecrawlt – nicht indexiert"**. Diagnose: kein technisches, sondern ein
> **Authority- + Trust- (YMYL) + Content-Tiefe-Problem**.

## Bewertung nach Disziplin

| Disziplin | Note | Befund |
|---|---|---|
| Technical SEO | **B+** | Canonicals, hreflang, robots.txt, Sitemap (114 URLs) korrekt. Schema solide (Organization/WebSite/FAQPage/SoftwareApplication/Breadcrumb). |
| **Recht / Pflichtseiten** | **B+** ✅ | **`/rechtliches` ist vollständig**: Impressum (§5 DDG, Betreiberin genannt + Anschrift), Datenschutz (14 §§, DSGVO), Risikohinweis DE+EN. Footer-verlinkt, in Sitemap. *(Korrektur: frühere „F"-Bewertung war ein Audit-Fehler — Datei liegt in `landing/` statt `landing/pages/`.)* Offen: nur EN-Version der Seite. |
| **E-E-A-T (Expertise/Autor)** | **C** | Rechtlich ok, aber das **Vertrauens-/Expertise-Signal** fehlt: keine „Über-uns/Methodik"-Seite (wer/wie wird gerechnet), Blog-Autor = Marke „SeasonAlpha" statt Person/Redaktion mit nachvollziehbarer Kompetenz, kein Person-Schema. |
| Content | **C** | Blog median ~1050 W (ok), aber Pillar-Seiten dünn (z.B. „was-ist-saisonalitaet" 278 W). 32 Tool-Seiten mit nur ~300 W statischem Text (Wert im JS-Chart, für Googlebot unsichtbar). |
| **Off-Page / Authority** | **F 🔴** | 0 Backlinks, 0 externe Klicks. **Der eigentliche Wachstums-Blocker.** |
| Strukturierte Daten | **B–** | Vorhanden, aber Autor = Marke statt **Person/Redaktion**; **`Dataset`-Schema fehlt** (großer Hebel für eine Datenplattform → Google Dataset Search + Rich Results). |

**Warum „crawled not indexed" (293):** Junge Domain × YMYL-Finanzthema × **0 externe
Signale/Backlinks** × dünner statischer Content × schwaches Expertise-Signal = Google crawlt,
stuft als „nicht autoritativ/wertvoll genug" ein und hält die Indexierung zurück. **Rechtlich
ist alles da** — der Engpass ist **Authority + Content-Tiefe**, nicht die Pflichtseiten.

## 90-Tage-Plan (priorisiert nach Impact × Aufwand)

### Phase 1 — Trust/Expertise-Signal (Tag 1–30) · P1
*Pflichtseiten ✅ bereits vorhanden (Impressum/Datenschutz/Risikohinweis auf `/rechtliches`,
Footer-verlinkt). Es fehlt nur noch das **Expertise-/Vertrauenssignal** + Baseline.*
- [x] ~~Impressum / Datenschutz / Disclaimer~~ — **erledigt** (`/rechtliches`).
- [x] ~~**Über-uns / Methodik-Seite** (`/ueber-uns`)~~ — **erledigt** (2026-06-15): Datenquellen,
      „wie wir rechnen" (normalisierte Renditen, Handelstags-Kalender), Qualitätssicherung.
      Stärkstes E-E-A-T-Signal für eine *Daten*plattform, ohne öffentliches Gesicht.
- [ ] **Author/Redaktion-Schema** — Blog-Autor als `Person`/`Organization` „Redaktion
      SeasonAlpha" mit Verweis auf die Methodik-Seite (statt nacktem Marken-String).
- [ ] **`/rechtliches` EN-Version** (`/en/rechtliches` o. Legal-Anker im EN-Build).
- [ ] **GSC/GA4-Baseline** — aktuelle Impressions/Index-Quote als Startwert festhalten.

### Phase 2 — Content-Tiefe & erstes Linkable Asset (Tag 31–60) · P1
- [ ] **Pillar-Seiten vertiefen** — „Was ist Saisonalität" 278→1500+ W, einzigartig, mit
      Beispielen/Daten; als Hub für Themen-Cluster (intern verlinkt).
- [ ] **Tool-Seiten** (monatszyklus/opex/…): statischen Erklär-/Methodik-Text 300→800+ W
      + **FAQPage-Schema** (echte Fragen) → gegen „thin", Chance auf Rich Results.
- [ ] **Internes Cluster-Linking** — Pillar ↔ Tool ↔ Blog kontextuell verknüpfen.
- [x] ~~**1. Daten-Studie bauen**~~ — **erledigt** (2026-06-15): Blog „Schlechtester DAX-Monat"
      (DAX-September seit 1988, DE+EN) als zitierfähiger Link-Hook. Embed-Backlink-Asset (`/embed`)
      + `wachstum-distributor`-Agent für die Distribution dazu. Nächste Studien nachlegen.

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
Rechtliche Pflichtseiten sind **bereits da** (sauber). Technik weiter optimieren bringt
trotzdem **fast nichts**, solange **Authority (0 Backlinks)** + Content-Tiefe + Expertise-
Signal fehlen. Reihenfolge: **Expertise/Methodik-Seite (klein) → Content-Tiefe →
Backlinks/Digital-PR (das eigentliche, größte Stück Arbeit).**
