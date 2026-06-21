# SEO — ToDo-Liste (seasonalpha.ai)

> Stand: 2026-06-21. Kontext: junge YMYL-Domain (~3-4 Mon.), GSC zeigte 468 nicht
> indexierte Seiten, davon **293 „gecrawlt, nicht indexiert"** (= Qualitäts-/Authority-
> Schwelle, kein Bug). Technik ist verifiziert sauber (0 tote Links, Sitemap vollständig,
> robots ok). Engpass: **Content-Tiefe + Off-Page-Authority**. Detail-Audit: `docs/SEO_AUDIT.md`.

## 🔴 DU (kann ich nicht — Accounts/Konsole/Server-OK)

- [ ] **Outreach posten** — versandfertiges Paket in `docs/growth/2026-06-21_..._distribution.md`
      (Reddit r/Finanzen + r/Mauerstrassenwetten, X, LinkedIn) + 7 personalisierte Pitch-Mails.
      Killer-Zahl: „DAX-September seit 1988: Ø −2 %, nur 39 % positiv." → erste Backlinks = #1-Hebel.
      ⚠️ `seasonalpha.com` ist ein FREMDES Produkt — bei Erwähnungen `.ai` sicherstellen.
- [ ] **GSC → „URLs entfernen"** für die 2 „indexiert trotz robots.txt".
- [ ] **GSC → 404-Bericht**: die historischen `/landing/pages/*.html`-Direkt-URLs als „dauerhaft
      entfernt" markieren (oder mich „nginx 404→301" machen lassen, s.u.).
- [ ] **GSC /en/-Property** einrichten + nach 2 Wochen Coverage prüfen (erste EN-Indexierung).
- [ ] **GSC-/GA4-CSV-Export** in `docs/growth/gsc_export/` ablegen → dann kann `gsc-analyst`
      datenbasiert priorisieren (Striking-Distance etc.).

## 🟡 Optional, auf dein OK (deploy-sensibel, mache ich)

- [ ] **nginx `/landing/pages/*.html` 404 → 301** auf die Clean-URL — rettet Crawl-Budget +
      Linkjuice der 43 historischen 404. (`deploy/nginx.conf`, Restart nötig.)

## 🟢 ICH — Content-Tiefe (gegen die 293) — Fortschritt

Tool-Seiten waren dünn (<300 Wörter statischer Text → Wert nur im JS-Chart, für Crawler
unsichtbar). Lösung je Seite: ~400 Wörter statischer Unique-Content (Was zeigt das Tool ·
Wie liest man es · Methodik · Einordnung) + 3 FAQ + FAQPage-Schema, i18n-sauber (DE+EN).

**Erledigt (PR #116/#117):** crash-fruehwarnung · dekadenzyklus · monatswechsel · mondphasen · sektor-rotation
**In Arbeit:** kriegszeiten · plain-vanilla · trifecta · feiertage · overnight · dividend-kalender ·
scanner · risikozyklus · zentralbanken · monatszyklus · intermarket-shocks · earnings-kalender · opex

## 🟢 ICH — laufend / nächste Schritte

- [ ] Nach den Tool-Seiten: **Pillar-Seiten** vertiefen („Was ist Saisonalität" 278→1500+ W).
- [ ] **Interne Verlinkung** Blog ↔ Tool-Seiten kontextuell verdichten.
- [ ] `wachstum-distributor` nach jedem neuen Blog-Post → Distributionspaket.
- [ ] `gsc-analyst` nach GSC-Export → Striking-Distance-Priorisierung.

## Realistische Erwartung
Die 293 lösen sich über **8–12 Wochen** — getrieben von (a) jetzt vorhandenem Unique-Content
und (b) den ersten Backlinks aus dem Outreach. Kein Config-Commit bewegt sie; nur Content + Authority.
