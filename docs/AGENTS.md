# SeasonAlpha-Agenten — Einsatz-Anleitung

> Übersicht aller Subagenten (`.claude/agents/`), wann man welchen einsetzt, der
> Wachstums-Flywheel und ein Automatisierungs-Vorschlag (was ohne Eingreifen läuft).
> Stand: 2026-06-15.

## Die 8 Agenten im Überblick

| Agent | Zweck | Trigger (Beispiele) | Output | Modell |
|---|---|---|---|---|
| **blogger** | SEO-Blog-Artikel DE+EN mit echten Charts schreiben | „schreib einen Blog", „Artikel über X", „Daten-Studie" | `blog/posts/` (+ `en/`) | opus |
| **saisonalitaet-scout** | Web nach Saisonalitäts-Forschung scannen → Blog-Ideen | „was gibt's Neues zu Sell in May", „Research-Radar" | `docs/research-radar/` | sonnet |
| **seo-experte** | SEO-Strategie/Audit (technical, E-E-A-T, Backlinks) | „SEO-Audit", „warum ranken wir nicht", „Backlink-Strategie" | Audit/Plan-Reports | opus |
| **daten-auditor** | Supabase-Daten auf Frische/Vollständigkeit prüfen | „ist die DB aktuell", „fehlen Ticker", „Daten-Audit" | Ampel-Reports | sonnet |
| **wachstum-distributor** ⭐neu | Content-Distribution (Reddit/Social/Outreach) + **einbettbare Charts mit Backlink** anbieten → Backlinks | „verteile den Post", „Outreach für die DAX-Studie", „Chart-Embed anbieten", „Backlink-Check" | `docs/growth/…_distribution.md` + `backlinks.md` | opus |
| **frontend-qa** ⭐neu | 30+ Pages crawlen: tote Links, i18n, hreflang, Meta, A11y | „QA das Frontend", „tote Links prüfen", „i18n-Check" | `docs/qa/…_frontend_qa.md` | sonnet |
| **seo-seiten-bauer** ⭐neu | Daten-reiche Ticker-/Themen-Seiten für Long-Tail bauen | „SEO-Seite für AAPL", „programmatic SEO skalieren" | `seo/` / `landing/pages/` | opus |
| **gsc-analyst** ⭐neu | GSC/GA4 auswerten → priorisierte To-dos für blogger/seo-experte | „was als Nächstes schreiben", „GSC auswerten", „Striking-Distance" | `docs/growth/…_gsc_priorities.md` | sonnet |

Aufruf: per Agent/Task-Tool mit dem Agent-Namen, oder die Trigger-Phrasen im Chat.

## Der Wachstums-Flywheel (Reihenfolge)

Die Agenten greifen ineinander — so dreht sich die Wachstums-Schleife:

```
  saisonalitaet-scout      →  blogger            →  wachstum-distributor  →  [DU postest]
  (findet Forschung/Hook)     (schreibt Studie)     (Reddit/Social/Outreach)   (Accounts/Beziehungen)
        ↑                                                                          │
        │                                                                          ▼
  gsc-analyst   ←──────────────────────────────────────────────────────────  Reichweite/Backlinks
  (misst, was wirkt → priorisiert nächste Themen)
```

**Quer dazu (laufend):**
- **seo-experte** — setzt die Strategie / macht Audits (alle paar Wochen).
- **frontend-qa** — hält die 60+ Pages technisch sauber (wöchentlich).
- **seo-seiten-bauer** — skaliert den Long-Tail mit echten Daten-Seiten (gezielt, mit Review).
- **daten-auditor** — stellt sicher, dass die Datenbasis stimmt (läuft via Cron).

**Kern-Idee:** Die alten Agenten *erzeugen* Wert (Content/Daten), die neuen *verteilen* ihn
(distributor), *messen* ihn (gsc-analyst), *skalieren* ihn (seo-seiten-bauer) und *sichern die
Qualität* (frontend-qa). Das schließt die Lücke zwischen „guter Content" und „0 Backlinks/Klicks".

## Entscheidungs-Tabelle — „Ich will …"

| Ich will … | Agent |
|---|---|
| einen Artikel/eine Daten-Studie schreiben | **blogger** |
| wissen, was es Neues in der Forschung gibt | **saisonalitaet-scout** |
| einen frischen Post verbreiten / Backlinks anstoßen | **wachstum-distributor** |
| wissen, was ich als Nächstes schreiben/optimieren soll | **gsc-analyst** |
| prüfen, ob das Frontend sauber ist (Links/i18n/SEO-Tags) | **frontend-qa** |
| viele Ticker-Seiten für Long-Tail-Rankings | **seo-seiten-bauer** |
| eine SEO-Gesamtstrategie / einen Audit | **seo-experte** |
| wissen, ob die Daten/DB stimmen | **daten-auditor** |

## Automatisierungs-Vorschlag (ohne dein Eingreifen)

Was als Hintergrund-Routine laufen kann vs. was on-demand bleibt:

| Agent | Modus | Kadenz | Mensch nötig? |
|---|---|---|---|
| daten-auditor + Kalender-Prüfagent | **läuft schon** — Cron `db_completeness.yml` | wöchentl. So 05:00 UTC | nein (Mail bei Problem) |
| saisonalitaet-scout | **läuft schon** — Cloud-Routine | monatlich | nein (Digest) |
| **frontend-qa** | Cloud-Routine (neu, vorgeschlagen) | wöchentlich (So) | nein (nur Report) |
| **gsc-analyst** | Cloud-Routine (neu, vorgeschlagen) | monatlich (1.) | CSV-Export bereitstellen |
| **wachstum-distributor** | Cloud-Routine (neu, vorgeschlagen) | wöchentlich (Fr) | **ja** — Posten bleibt manuell |
| seo-experte | on-demand (+ opt. Quartals-Audit) | quartalsweise | nein (Report) |
| seo-seiten-bauer | **on-demand** (Review vor Publish!) | manuell | ja (Thin-Content-Schutz) |
| blogger | on-demand (+ opt. monatl. Entwurf) | manuell | ja (Freigabe) |

**Cloud-Routinen einrichten:** über `/schedule` (Cloud-Agenten = isolierte Sessions, NICHT lokale
Crons). Empfohlene erste drei:
1. **frontend-qa** wöchentlich So (nach `db_completeness`) → QA-Report.
2. **gsc-analyst** monatlich am 1. → Prioritäten-Report (sobald GSC-Export bereitliegt).
3. **wachstum-distributor** wöchentlich Fr → Distributions-Pakete für neue Posts der Woche.

> Hinweis: Cloud-Routinen laufen in Anthropics Cloud (eigener git-Checkout), ohne Zugriff auf
> deinen lokalen Rechner. Posten auf Social/Reddit bleibt aus API-/Account-Gründen manuell —
> die Agenten liefern versandfertige Entwürfe.

## Wichtige Grenzen (ehrlich)
- **wachstum-distributor** postet NICHT selbst (keine Social-/Reddit-APIs) → bereitet Entwürfe vor.
- **gsc-analyst** braucht GSC-/GA4-Daten (CSV-Export in `docs/growth/gsc_export/` oder später API).
- **seo-seiten-bauer** erzeugt nur Seiten über der Daten-Tiefe-Schwelle (sonst wieder Thin-Content).
- Agenten committen/deployen **nicht ungefragt** — Review/Freigabe bleibt bei dir.
