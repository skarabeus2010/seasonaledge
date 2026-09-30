# SEO-Umsetzungsplan nach externem Review (2026-09-30)

Grundlage: externes SEO-Review (ChatGPT), jede Behauptung live und am Code geprüft, danach von Codex
(gpt-6-astra) gegengeprüft. Review-Aufträge: `docs/review_prompts/2026-09-30_seo_review_plan*.md`.

## Befundlage

| # | Befund | Quelle | Stand |
|---|---|---|---|
| B1 | Meta-Description/OG/Twitter und BlogPosting-JSON-LD kaputt bei `/blog/p-wert-erklaert/` und `/en/blog/p-value-explained/` (gerade Anführungszeichen im Front Matter). Alle anderen 188 geprüften URLs sauber. | Review, bestätigt | Ursache: `blog/templates/blog_post.html` setzt Felder unmaskiert ein und baut JSON-LD per Text; `blog_index.html` gleich; ebenso `scripts/upgrade_page_meta.py:107-129`. Die kaputte Description zerstört auch `data-search` der Blogkarten. |
| B2 | Sitemap unvollständig: `/en/`, `/ueber-uns` und **alle 49 indexierbaren EN-Artikel** fehlen, EN-Blog-Startseite fehlt, DE-Posts ohne hreflang | Review (teilweise), erweitert | `seo/programmatic_seo_builder.py::build_sitemap` |
| B3 | Sitemap enthält 6 URLs ohne 200 (404 `/en/crash-fruehwarnung`; 301 `/en/congress`, `/en/dealer-positioning`, `/en/flows`, `/en/index-effekt`, `/en/kalender`) und `noindex`-Seiten (`/kalender`, `dashboard-launch`, `willkommen-bei-seasonalpha.ai`) | neu | `has_en` pauschal; Sitemap- und Blog-Builder haben verschiedene Status-/Indexregeln |
| B4 | `lastmod` = Build-Datum für jede URL; `dateModified` = Veröffentlichungsdatum | Review, bestätigt | |
| B5 | 3 EN-Artikel mit falschem `de_slug` (april-seasonality-sp500, tesla-apple-may-comparison, welcome-to-seasonalpha) → hreflang ins Leere; DE-Landing-Heads mit hreflang auf nicht existierende EN-Seiten (`dealer-positioning`, `crash-fruehwarnung`) | neu (Codex) | |
| B6 | Blog-Kategorieseiten kanonisch auf `/blog/` bzw. `/en/blog/` | neu (Codex) | `canonical_path` wird nie übergeben (`blog_builder.py:1343`) |
| B7 | Startseite: FAQPage nur im Markup, nicht sichtbar; inhaltlich falsch („15 KI-Modelle", „alle Module frei", „über 500 Basiswerte"); KI-Versprechen auch im SoftwareApplication-Markup und in Blog-CTAs | Review, erweitert | |
| B8 | Produktzahlen widersprüchlich: DE „über 500", EN „270+", Bestand 370 (`symbols.py`, `tickers.json`) | Review, bestätigt | EN-Schema wird über deutsche Volltextschlüssel übersetzt → DE-Textänderung kann Deutsch im EN-Schema hinterlassen |
| B9 | Deploy bricht bei Build-/Prüffehlern nicht ab (EN-Build „non-fatal", dessen nginx-Fallback existiert nicht mehr); Sitemap entsteht vor dem Blog-Build | neu (Codex) | `.github/workflows/deploy.yml:47-55` |
| B10 | H1 „The Beauty of Noise" beschreibt das Thema nicht | Review | Nutzerentscheidung |
| B11 | Autor nur `Organization`, keine Byline/Autorenseite; `/en/ueber-uns` fehlt | Review | Nutzerentscheidung. `Organization` ist technisch zulässig — Transparenzgewinn, keine Schema-Reparatur |
| B12 | Scanner-Ergebnisse nur per JS | Review | nur GSC klärt, ob Google rendert |
| B13 | Google zeigt FAQ-Rich-Results seit 07.05.2026 nicht mehr | Review, bestätigt | FAQPage-Markup bringt keine Darstellung mehr; sichtbarer FAQ-Text bleibt Inhalt |

## Phase 1 — Defekte beheben (ohne Nutzerentscheidung)

> **Erledigt 2026-09-30** (Commit `857126a`, Codex-Freigabe nach 3 Code-Runden, Review-Aufträge
> `docs/review_prompts/2026-09-30_seo_phase1_runde*.md`). Live nachgewiesen: Sitemap 184 URLs (vorher 139),
> alle 200 ohne Redirect, 33 verschiedene `lastmod` statt einem; p-Wert-Artikel DE+EN mit gültigen Metadaten;
> Startseite ohne FAQPage; Kategorien mit eigener Canonical. `verify_seo_html.py` läuft im Deploy (auf dem
> Server 0 Fehler), `verify_seo_mutation.py` fängt 28/28 Mutationen.
>
> **Abweichungen vom Plan / Zusatzfunde:** `/disclaimer` ist `noindex` und stand trotzdem in der Sitemap — der
> Wächter fand es beim ersten Lauf. Die Blog-Artikel verlinkten per hreflang nur EN→DE, nie DE→EN (jetzt
> reziprok; HTML und Sitemap nutzen dieselbe Funktion `blog_hreflang_ziele`, die nur indexierbare Gegenstücke
> zulässt). Die Blog-Übersichten hatten gar kein hreflang. Weitere veraltete Zahlen auf `/pricing` („270
> Ticker", „130 Jahre"), in der Tour („269 Ticker") und in den EN-Beschreibungen. Ohne `date` scheitert der
> Blog-Build jetzt, statt das Tagesdatum einzusetzen.
>
> **Lessons:** (1) Zwei Werkzeugschichten haben Backslash-Escapes beim Schreiben still umgedeutet — einmal
> entstand eine Escape-Tabelle, die `<` auf `<` abbildete, also nichts schützte, bei weiterhin laufendem Code.
> Getestet wird deshalb die AUSGABE (Rundlauf + „kein `</` im Ergebnis"), nicht der Quelltext. (2) Eine
> Mutation, die nichts ändert, prüft nichts — die erste Doppelmaskierungs-Mutation traf eine Beschreibung ohne
> maskierbare Zeichen; der Test bricht jetzt bei wirkungsloser Mutation ab. (3) Codex fand in jeder Runde
> Prüflücken des Wächters, nicht des Produktivcodes: leere Sitemap bestand, fehlende noindex-Pflichtseiten
> fielen durch einen Existenzfilter, ein zusätzliches `unescape` verdeckte Doppelmaskierung.

**1a. Sichere Serialisierung**
- Blog-Builder: `autoescape` für HTML/XML. Als sicher markiert werden NUR die drei bewusst erzeugten
  HTML-Fragmente `content`, `disclaimer_short`, `disclaimer_long`. UI-Strings/Template-Defaults, die heute
  HTML-Entities enthalten (`&uuml;`, `&hellip;`), auf echtes Unicode umstellen (sonst Doppelmaskierung).
- JSON-LD (BlogPosting, BreadcrumbList) im Builder als dict, Ausgabe über einen Helfer, der `json.dumps`
  plus Script-Kontext-Schutz macht: die Zeichen kleiner-als, größer-als und kaufmännisches Und werden als
  JSON-Unicode-Escapes ausgegeben (Backslash-u-003c, -003e, -0026), damit ein `</script>` im Text den Block
  nicht beendet. Die so serialisierte Ausgabe wird danach NICHT noch einmal HTML-maskiert.
  Derselbe Helfer für `blog_index.html` und `scripts/upgrade_page_meta.py`. Dort zusätzlich: Eingaben erst
  dekodieren, dann für HTML-Text bzw. Attribute getrennt maskieren (das Blog-Autoescape greift in diesem
  Skript nicht). Regressionsfälle: die p-Wert-Beschreibung UND ein Wert mit `</script>`.
- Die p-Wert-Beschreibungen bleiben wie sie sind — sie sind der Regressionsfall.

**1b. Sprachverfügbarkeit und Indexierbarkeit aus einer Quelle**
- EN-Verfügbarkeit von Landing-Seiten: `_EN_PAGE_META` (steht in `landing/js/i18n.js`, `build_en.py` liest es).
  Sitemap-Builder und die hreflang-Tags in den DE-Heads richten sich danach. Nicht existierende EN-Ziele raus.
- Blog: ZWEI getrennte, gemeinsam genutzte Prüfungen. „veröffentlicht" (Status, fällige Planung) steuert die
  HTML-Erzeugung — veröffentlichte `noindex`-Artikel (Willkommen, Dashboard-Launch, je DE+EN) werden weiter
  gebaut, bewusst mit `noindex, follow`. „veröffentlicht UND indexierbar" steuert die Aufnahme in alle drei
  Sitemaps (Sitemap-Builder + beide Blog-Sitemaps). `noindex`-Seiten (auch `/kalender`) nicht in die Sitemap.
- `de_slug` der drei EN-Artikel korrigieren; Build schlägt fehl, wenn ein `de_slug` auf keinen
  veröffentlichten DE-Artikel zeigt (unabhängig von dessen Indexierbarkeit).

**1c. Sitemap vervollständigen**
- `/en/`, `/ueber-uns`, EN-Blog-Startseite, alle indexierbaren EN-Artikel, reziprokes hreflang DE↔EN für Posts.
- Kategorieseiten: `canonical_path` + eigene Metadaten übergeben (Kategorien bleiben indexierbar, weil sie
  Themen bündeln). EN-Kategorien nur, wenn sie eigenständig existieren.
- `lastmod`: Datum der letzten wesentlichen Änderung. Blog: neues optionales `updated:` im Front Matter,
  sonst `date` — einheitlich für Sitemap, `dateModified` und `article:modified_time`. Landing-Seiten: letzter
  Commit der Quelldatei, **auf dem Host** ermittelt (im Container gibt es kein `.git`); liefert Git nichts
  Verlässliches, `lastmod` weglassen statt „heute". Gemeinsame Templates lösen bewusst KEIN neues `lastmod`
  aus (keine wesentliche Inhaltsänderung).

**1d. Deploy-Reihenfolge und Abbrüche**
- Reihenfolge: Blog + EN-Seiten bauen → Sitemap erzeugen → Wächter → erst dann „Deploy done".
- EN-Build und Blog-Build nicht mehr „non-fatal"; Fehler im Build oder im Wächter → Deploy rot
  (Muster wie `install_timers.sh`). Veralteten Kommentar zum nginx-Laufzeitfallback entfernen.

**1e. Wächter `scripts/verify_seo_html.py`**
- Grundlage ist eine ausdrückliche Zuordnung **öffentliche URL → Artefakt** (erwartete Liste; fehlende Seite = rot):
  `landing/*.html`, `landing/pages/*.html`, `landing/en/*.html`, `blog/output/**` (DE+EN, Artikel, Übersichten,
  Kategorien), `seo/output/disclaimer.html` und `seo/tools/`.
- Syntaxprüfung für ALLE Dateien: keine Fremdattribute in `<meta>`; JSON-LD parsebar; dekodierte Attribut- und
  JSON-Werte gleich den Eingaben (Front Matter).
- Seitentyp-abhängig: indexierbare Seiten brauchen Canonical = eigene URL und existierende hreflang-Ziele;
  Farbvorschauen (`landing/colorscheme-*.html`) und `embed.html` sind ausdrücklich ausgenommen (kein Canonical,
  nicht in der Sitemap); `noindex`-Seiten nicht in der Sitemap.
- `--live`: alle Sitemap-URLs 200 ohne Redirect.
- Regressionstest in einer isolierten Testfassung (kein Mutieren produktiver Dateien): der alte Template-Stand
  mit der p-Wert-Beschreibung muss rot sein, der neue grün.

**1f. Startseiten-Markup bereinigen**
- FAQPage-Markup der Startseite entfernen (unsichtbar, falsch, ohne Rich Result).
- Falsche Aussagen korrigieren, soweit sie Fakten sind (keine neue Positionierung): „15 KI-Modelle" und
  weitere KI-Versprechen in SoftwareApplication-Markup, Blog-CTAs und Meta; Basiswerte-Zahl aus `symbols.py`
  beim Build (gerundet „über 350"/„350+"), gleich in DE/EN, Meta, Schema und sichtbarem Text.
  Kalender korrekt beschreiben (Anmeldung nötig, kostenlose Termintypen + Premium-Funktionen, siehe
  `landing/js/kalender-compute.js`) — das ist eine Korrektur des heutigen Angebots, keine Positionierung.
- Auch die übrigen Kennzahlen gegen den Bestand prüfen und mit Geltungsbereich dokumentieren: „22 Tools",
  „24 Strategien", „131 Jahre" (`landing/index.html:9`). „131 Jahre" gilt nur für einzelne Reihen (^DJI) und
  darf nicht als Historie aller Basiswerte gelesen werden können.
- EN-Schema der Startseite aus sprachabhängigen Daten erzeugen statt über deutsche Volltextschlüssel.

Danach: Sitemap in der GSC neu einreichen (Nutzer).

## Phase 2 — Entscheidungen des Nutzers

- **H1** (B10): Vorschlag „Saisonale Börsenanalyse für Aktien, ETFs und Indizes", Slogan als Zeile darüber. DE+EN mit `data-i18n`.
- **Preise, Leistungsumfang, Vermarktung** (B8): nur Änderungen daran warten auf den Nutzer. Das heutige
  Angebot korrekt zu beschreiben, gehört dagegen in Phase 1f.
- **Autorenschaft** (B11): echte Person(en) mit Qualifikation, sichtbare Byline, Autorenseite, redaktioneller Prüfprozess auf `/ueber-uns`; `/en/ueber-uns` anlegen.

## Phase 3 — Messung und Inhalte (parallel möglich)

- GSC: URL-Prüfung `/scanner` (gerendertes HTML), Coverage `/en/`, Suchanfragen für die Review-Themen
  (DAX September, Sell in May, Monatswechsel, „Saisonalität Aktien").
- Die Themenvorschläge des Reviews existieren großteils (`dax-september-signifikanz`, Sell-in-May-Artikel,
  `/monatswechsel`) → keine neuen Seiten, sondern Verlinkung Artikel↔Tool, priorisiert nach GSC-Daten
  (steht teilweise schon als TODO „Rückverweise aus den Tool-Seiten").
