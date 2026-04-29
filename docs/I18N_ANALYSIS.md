# SeasonAlpha — Internationalisierung (EN) — Analyse & Plan

> Version 1.0 | 2026-04-23 | Planungsdokument für EN-Lokalisierung

## Executive Summary

Die EN-Lokalisierung von SeasonAlpha ist technisch mittelgroß (ca. 3-5 Personentage für Setup + i18n-Refactor), inhaltlich jedoch der Löwenanteil (40-80h KI-gestützte Übersetzung + Review). Für die ~20 HTML-Pages, Blog-Artikel, JS-Module (Tour, Tooltips, Chart-Labels) und Email-Templates empfehle ich ein **JSON-basiertes Key-Value-System mit i18next-ähnlicher Dot-Notation** und ein `/en/`-Pfad-Schema (keine Subdomain). **Rechtlich kritisch:** Impressum, Datenschutz, AGB, Financial Disclaimer und Risikohinweis MÜSSEN juristisch professionell lokalisiert werden — KI-Übersetzung ist hier haftungsrechtlich grob fahrlässig, besonders wegen der Finanzmarkt-Thematik (MiFID II, SEC-Disclaimer-Pflichten bei US-Reichweite).

---

## 1. Technisches Setup

### Empfohlene Struktur

```
landing/
├── i18n/
│   ├── de.json         ← Default, Masterdatei
│   ├── en.json         ← Übersetzung
│   └── _schema.md      ← Key-Conventions
├── js/
│   └── i18n.js         ← SA.i18n Loader + t()-Helper
```

### Key-Konventionen (Dot-Notation, nach Seite gruppiert)

```json
{
  "nav": {
    "dashboard": "Dashboard",
    "tour_btn": "Geführte Tour",
    "cta_login": "Anmelden"
  },
  "dashboard": {
    "title": "Dashboard",
    "subtitle": "Saisonaler Überblick für $t(common.ticker)",
    "cards": {
      "ki_score": {
        "label": "KI-Score",
        "tooltip": "Composite aus 4 Sub-Scores (0-10)..."
      }
    }
  },
  "common": {
    "ticker": "Ticker",
    "trading_day": "Handelstag",
    "loading": "Lade…"
  },
  "tour": {
    "steps": {
      "1": { "title": "…", "body": "…" }
    }
  }
}
```

### Warum Key-Value statt Template-Duplikation

- **DRY:** 20 HTML-Pages × 2 Sprachen = 40 Dateien → Chaos. 20 Templates + 2 JSON = maintainable.
- **Blog bleibt separat:** Markdown-Posts pro Sprache als eigene Dateien (`blog/en/*.md`), NICHT in JSON — zu lang.
- **Build-time vs. runtime:** Für Streamlit-Pages (Python) Build-time via `gettext`/`babel` oder simpler dict-Lookup. Für landing/ runtime via fetch+cache.

### Minimaler Helper (ohne Framework)

```javascript
// landing/js/i18n.js
SA.i18n = {
  _dict: {},
  _lang: 'de',
  async load(lang) {
    const r = await fetch(`/landing/i18n/${lang}.json`);
    this._dict = await r.json();
    this._lang = lang;
    document.documentElement.lang = lang;
    this._applyDOM();
  },
  t(key, vars = {}) {
    const val = key.split('.').reduce((o, k) => o?.[k], this._dict) || key;
    return val.replace(/\{(\w+)\}/g, (_, k) => vars[k] ?? '');
  },
  _applyDOM() {
    document.querySelectorAll('[data-i18n]').forEach(el => {
      el.textContent = this.t(el.dataset.i18n);
    });
  }
};
```

HTML-Markup: `<h1 data-i18n="dashboard.title">Dashboard</h1>` — Default-Text bleibt als Fallback.

### Spezialfälle

- **Zahlen/Datum:** `Intl.NumberFormat(lang)` und `Intl.DateTimeFormat(lang)` statt hartcodiert.
- **Chart-Achsen (ApexCharts):** `xaxis.labels.formatter` aus i18n-Dict.
- **Python-Side (Streamlit):** `shared/i18n.py` mit `dict[lang][key]`, triggert via `st.session_state.lang`. Browser-Lang-Detect aus `Accept-Language` via `st.context.headers`.
- **Tour-Config:** `tour-config.js` bereits JSON-artig → direkt in `de.json`/`en.json` auslagern.

---

## 2. Content-Migration via KI

### Prozess in 5 Stufen

**Stufe 1 — Extraktion**

Skript `scripts/extract_i18n_keys.py`:
- Parst alle `.html`/`.js`/`.py` Dateien, findet strings in `data-i18n=""`, `t("…")`, `st.write("…")`.
- Für **Altbestand ohne data-i18n:** halbautomatisch — regex findet `<h1>…</h1>`, `<p>…</p>` mit deutschem Text, User reviewt und markiert.
- Output: `de.json` (Masterdatei mit allen Keys).

**Stufe 2 — DB-Content-Extraktion**

```sql
SELECT id, title, slug, content_md, meta_description
FROM blog_posts
WHERE lang = 'de';

SELECT key, text_de FROM info_texts;  -- falls info_texts.yaml migriert
```

Export als JSON pro Record → Batch-Input für Claude.

**Stufe 3 — Batch-Übersetzung via Claude API**

Empfehlung: **Anthropic Message Batches API** (50% Rabatt, bis zu 100k Requests):

```python
from anthropic import Anthropic
client = Anthropic()

SYSTEM = """You are translating a German finance-market seasonality web app to English.
Audience: retail traders, intermediate finance literacy.
Terminology: keep 'TDOM', 'TDOY', 'OPEX', 'VIX' untranslated.
'Handelstag' → 'trading day', 'Saisonalität' → 'seasonality', 'Feiertag' → 'holiday'.
Preserve JSON structure, {variables}, markdown, HTML tags.
Tone: professional, concise, US financial English."""

batch = client.messages.batches.create(requests=[
    {"custom_id": key,
     "params": {"model": "claude-opus-4-7",
                "max_tokens": 2000,
                "system": SYSTEM,
                "messages": [{"role": "user", "content": f"Translate to EN:\n{text}"}]}}
    for key, text in de_dict.items()
])
```

**Stufe 4 — Glossary & Review**

- **Glossary-File** (`i18n/_glossary.md`): 50-80 Fachbegriffe manuell fixieren (z.B. "Dekadenzyklus" → "Decade Cycle", "Musterpfad" → "Pattern Path"). In jedem Batch-Prompt mitsenden.
- **2-stufiges Review:** (a) Diff-Tool `de.json` ↔ `en.json` — fehlende Keys, Längen-Anomalien (EN > 2× DE = verdächtig). (b) Native-Speaker-Stichprobe auf Marketing-Texte (Landing, CTAs).

**Stufe 5 — Re-Import**

- Frontend: `en.json` committen, CI deployed.
- DB: `UPDATE blog_posts SET content_md_en = ... WHERE id = ...`, oder neue Zeilen `lang='en'`.
- Post-Deploy: alle `/en/*`-URLs via Sitemap crawlen, 404-Check.

### Kosten-Schätzung

Grob 200k Token DE-Content (HTML + JS + Blog + Email): Opus 4.7 Batch: ~$2 Input + ~$10 Output = **~$12 einmalig**. Vernachlässigbar.

---

## 3. International SEO

### URL-Struktur: `/en/` gewinnt

| Option | Pro | Contra |
|---|---|---|
| **`/en/dashboard`** ✅ | 1 Domain = 1 Authority-Pool, einfaches Hosting, gleiche SSL | Root = Standardsprache |
| `en.seasonalpha.ai` | Klare Trennung, geo-targeting via GSC | Teilt Backlink-Juice, eigene DNS/SSL |
| `seasonalpha.com` | Stärkstes Geo-Signal | Zweite Domain kaufen+verwalten |

Für SeasonAlpha: **`/en/` Pfad-Prefix**. Default (ohne Prefix) bleibt DE. Vorteil: alle bestehenden Backlinks bleiben wertvoll.

### Hreflang — PFLICHT

In **jedem** `<head>`:

```html
<link rel="alternate" hreflang="de" href="https://seasonalpha.ai/dashboard" />
<link rel="alternate" hreflang="en" href="https://seasonalpha.ai/en/dashboard" />
<link rel="alternate" hreflang="x-default" href="https://seasonalpha.ai/dashboard" />
```

+ Sitemap.xml mit `<xhtml:link rel="alternate">` pro URL-Paar.

### Zusätzlich

- `<html lang="en">` setzen (aktuell `lang="de"`).
- Open-Graph `og:locale` + `og:locale:alternate`.
- GSC: Beide Varianten als **separate Properties** eintragen, Performance nach Sprache segmentieren.
- nginx: `Vary: Accept-Language` Header + optional 302-Redirect auf `/en/…` wenn `Accept-Language: en*` UND User auf `/` landet (aber **nie** auf Deep-Links automatisch redirecten — das bricht User-Intent und SEO).

---

## 4. Ressourcen-Planung

### (a) Technische Umstellung

| Task | Aufwand |
|---|---|
| i18n-Helper JS + Python | 0.5 d |
| 20 HTML-Pages mit `data-i18n` annotieren | 1.5 d |
| Nav/Footer/Components + Email-Template | 0.5 d |
| Streamlit-Pages i18n | 0.5 d |
| Language-Switcher-UI + Browser-Detect + Cookie | 0.5 d |
| Hreflang + Sitemap + nginx-Config | 0.5 d |
| Testing über alle Pages (Charts, Tooltips, Tour) | 1 d |
| **Subtotal** | **~5 PT** |

### (b) Inhaltliche Übersetzung

| Bereich | Keys/Wörter | Aufwand (KI + Review) |
|---|---|---|
| UI-Strings (20 Pages + Nav/Tour) | ~1.500 Keys / 8k Wörter | 2 d (Batch + Diff-Review) |
| Info-Tooltips + Methodik-Seite | ~300 Keys / 12k Wörter | 1 d |
| Blog-Artikel (~20 Posts × 1.500 W) | ~30k Wörter | 3 d (inkl. Stil-Politur) |
| Email-Template + CTAs | ~500 Wörter | 0.5 d |
| SEO-Meta (Title/Description × 20) | ~40 Keys | 0.5 d |
| Native-Speaker-Stichprobe (Marketing) | - | 1 d (extern, ~€300-500) |
| **Subtotal** | | **~8 PT + externes Review** |

### Gesamtschätzung

**~13 Personentage netto** (≈ 2-3 Kalenderwochen bei Einzel-Dev, parallelisierbar wenn extern).

---

## 5. Legal & Compliance — ⚠️ NIEMALS nur KI

### Zwingend professionell lokalisiert

| Dokument | Warum |
|---|---|
| **Impressum** | §5 TMG (DE) hat kein EN-Äquivalent. Für US/UK-Reichweite: "Legal Notice"/"Imprint" mit angepassten Pflichtangaben. **Fachanwalt**. |
| **Datenschutzerklärung** | DSGVO-Text ≠ CCPA ≠ UK-GDPR. Wenn `/en/` auch an US-User gerichtet ist, braucht es zusätzlich CCPA-Disclosures (Right to Know/Delete, "Do Not Sell"). **Datenschutz-Fachanwalt oder spezialisierter Dienst** (iubenda, termly.io). |
| **AGB / Terms of Service** | Rechtsraum-abhängig: Gerichtsstand, Haftungsbeschränkung, Widerruf — in DE/EU anders als US/UK. **Fachanwalt**. |
| **Financial Disclaimer** | **Kritisch wegen Finanzmarkt-Content.** Bei US-Reichweite potentiell SEC-relevant (Investment Advisers Act). UK: FCA. Mindestens: "Not financial advice / No solicitation / Past performance…"-Klauseln im jeweiligen Standard. |
| **Risikohinweis** | MiFID II (EU) vs. US-Standards. Wording für Leverage, Verlustrisiko ist jurisdiktionsabhängig. |
| **Cookie Banner / Consent** | Consent-Modi DE (TTDSG) ≠ US (Opt-out-Modell) ≠ UK (PECR). Tool wie Usercentrics/Cookiebot nutzen, nicht selbst stricken. |

### Unkritisch (KI reicht + 1× menschliches Review)

- UI-Strings, Tooltips, Chart-Labels
- Blog-Artikel (Marketing/Edukation)
- Methodik-Seite (fachlich, nicht rechtlich)
- Email-Templates (solange keine Opt-in-Claims)

### Empfehlung

1. Für Impressum/Datenschutz/AGB: **einmalig Fachanwalt oder template-service** (~€500-1.500).
2. Financial Disclaimer: Fachanwalt mit Kapitalmarkt-Erfahrung — NICHT sparen. Bei US-Reichweite: US-Securities-Lawyer-Review (~$1.000-2.000).
3. Falls Budget eng: **Geo-Restriction** — `/en/` explizit NICHT an US-IPs ausspielen (via nginx geo-Block) und das dokumentieren. Reduziert rechtliches Risiko erheblich.

---

# Schritt-für-Schritt Checkliste

### Phase 0 — Vorbereitung (0.5 d)
- [ ] Entscheidung: `/en/`-Pfad bestätigen, Default-DE bleiben
- [ ] Geo-Scope klären: nur EU/UK oder auch US? (beeinflusst Legal-Budget)
- [ ] Rechts-Budget freigeben (Impressum/DSGVO/AGB/Disclaimer)
- [ ] Glossary anlegen (50-80 Fachbegriffe DE→EN)

### Phase 1 — Technisches Fundament (2 d)
- [ ] `landing/i18n/de.json` + `en.json` (leer) anlegen
- [ ] `landing/js/i18n.js` mit `SA.i18n.load/t/_applyDOM` bauen
- [ ] `shared/i18n.py` für Streamlit-Pages
- [ ] Language-Switcher in `components/nav.html` (DE/EN-Toggle, Cookie `sa_lang`)
- [ ] `<html lang="xx">` dynamisch setzen
- [ ] Browser-Detect (nur auf `/` Landing, nicht auf Deep-Links)

### Phase 2 — String-Extraktion (1.5 d)
- [ ] `scripts/extract_i18n_keys.py` gegen alle HTML/JS
- [ ] `data-i18n`-Attribute in allen 20 HTML-Pages setzen
- [ ] `tour-config.js` → in `de.json` umziehen
- [ ] `info_texts.yaml` → in `de.json` umziehen
- [ ] DB-Content exportieren (Blog + info_texts)

### Phase 3 — Übersetzung (3-4 d)
- [ ] Claude Batches API: UI-Strings + Tooltips mit Glossary im System-Prompt
- [ ] Claude Batches API: Blog-Artikel (niedrigere Priorität)
- [ ] Diff-Review `de.json` ↔ `en.json` (fehlende Keys, Längen-Anomalien)
- [ ] Native-Speaker-Stichprobe auf Landing + Dashboard
- [ ] SEO-Meta (Title/Description × 20 Pages) manuell polieren

### Phase 4 — Legal (parallel, extern)
- [ ] Impressum/Legal Notice vom Fachanwalt
- [ ] Datenschutz EN (ggf. mit CCPA bei US-Scope)
- [ ] AGB/ToS lokalisiert
- [ ] Financial Disclaimer + Risikohinweis — **Kapitalmarkt-Anwalt**
- [ ] Cookie-Banner-Tool mit EN-Locale konfigurieren

### Phase 5 — SEO (0.5 d)
- [ ] Hreflang-Tags in `<head>` aller Pages (via Component-Include)
- [ ] Sitemap.xml mit `xhtml:link`-Alternates erweitern
- [ ] `og:locale` + `og:locale:alternate`
- [ ] nginx: `/en/`-Location-Block, `Vary: Accept-Language`
- [ ] GSC: `seasonalpha.ai/en/` als separate Property einreichen
- [ ] IndexNow-Ping für alle neuen `/en/`-URLs

### Phase 6 — Testing & Launch (1 d)
- [ ] Alle 20 Pages in EN durchklicken (Charts, Tooltips, Tour)
- [ ] Tour komplett auf EN testen (23 Steps)
- [ ] Email-Template-Preview in EN
- [ ] 404-Crawl auf `/en/*`
- [ ] Rich Results Test für 3-5 Key-Pages
- [ ] Soft-Launch: nur Landing + Dashboard EN, Rest folgt
- [ ] Blog-Post "SeasonAlpha now available in English"

### Phase 7 — Post-Launch (laufend)
- [ ] GSC Coverage nach 2 Wochen prüfen
- [ ] EN-Traffic-Quellen analysieren (US/UK/Intl?)
- [ ] CTR `/en/` vs `/` vergleichen
- [ ] Feedback-Widget für Übersetzungs-Fehler

---

**Empfehlung für CLAUDE.md TODO-Update:** EN-Übersetzung in 3 TODO-Blöcke aufteilen: (1) Legal-Vorbereitung (User-Action, extern), (2) Technisches i18n-Framework (1 Sprint), (3) Content-Migration (nachgelagert, wenn Framework steht).
