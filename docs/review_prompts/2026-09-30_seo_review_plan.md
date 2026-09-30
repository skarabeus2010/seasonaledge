# Review-Auftrag: Externes SEO-Review prüfen + Umsetzungsplan (ENTWURF, noch kein Code)

Repo `C:\dev\Seasonaledge`. Ein externes SEO-Review (ChatGPT) hat seasonalpha.ai bewertet. Ich habe jede
Behauptung gegen die Live-Seite und den Code geprüft. Deine Aufgabe: (1) meine Prüfung am Code gegenprüfen,
(2) den Plan kritisieren — Reihenfolge, fehlende Risiken, falsche Annahmen, Überflüssiges.
Antwort auf Deutsch, je Befund Schwere (HOCH/MITTEL/NIEDRIG) + Datei:Zeile + konkrete Änderung.
Am Ende genau eine Zeile `FREIGABE: ja` oder `FREIGABE: nein` (Freigabe = Plan tragfähig).

## Review-Behauptungen und mein Prüfergebnis (Live gemessen 2026-09-30)

| # | Behauptung des Reviews | Ergebnis |
|---|---|---|
| 1 | p-Wert-Artikel: Anführungszeichen beenden Meta-Description, OG/Twitter betroffen, BlogPosting-JSON ungültig | **Bestätigt, DE und EN.** Scan aller 139 Sitemap-URLs + aller 51 EN-Blog-URLs mit HTMLParser + `json.loads`: genau `/blog/p-wert-erklaert/` und `/en/blog/p-value-explained/` kaputt (Front Matter `description: "... \"no effect\" ..."`). **Ursache:** `blog/templates/blog_post.html` setzt `{{ description }}`, `{{ title }}`, `{{ tag }}` usw. unmaskiert in Attribute (Z. 8–37) und baut JSON-LD per Texteinsetzung (Z. 40–66, 81, 96); `blog/blog_builder.py:1183,1274` `Environment(...)` ohne `autoescape`. `blog_index.html` gleiches Muster. `landing/build_en.py:171` macht es richtig (`jd()` = JSON-Serializer). |
| 2 | Autorenschaft nur `Organization` | Bestätigt (steht schon als TODO in CLAUDE.md). Braucht Nutzerentscheidung (echte Person, Qualifikation). |
| 3 | H1 der Startseite „The Beauty of Noise" | Bestätigt: `landing/index.html:368` `<h1 class="hero__h1"><em>The Beauty of Noise</em></h1>`. |
| 4 | Sitemap: `/en/` und „Über uns" fehlen, alle `lastmod` gleich | **Bestätigt und größer:** `seo/programmatic_seo_builder.py::build_sitemap`. (a) `/en/` fehlt (statische Startseite ohne EN-Zweig, Z. 126); (b) `landing/ueber-uns.html` liegt nicht in `landing/pages/` → Auto-Discovery findet sie nicht (Z. 196); (c) **alle 51 EN-Blogartikel fehlen** (nur `blog/posts/*.md`, Z. 259), DE-Posts ohne hreflang; (d) `has_en` wird pauschal angenommen (Z. 226) → **6 Sitemap-URLs nicht 200**: 404 `/en/crash-fruehwarnung`, 301 `/en/congress`, `/en/dealer-positioning`, `/en/flows`, `/en/index-effekt`, `/en/kalender`; (e) `lastmod = heute` für jede URL (Z. 121). Blog-Posts haben kein `updated`-Feld, nur `date`. |
| 5 | FAQ nur im JSON-LD der Startseite, nicht sichtbar | Bestätigt (Text der 4 Fragen im sichtbaren Inhalt nicht vorhanden). **Zusätzlich inhaltlich falsch:** „15 KI-Modelle" (ML-Pipeline seit 04/2026 stillgelegt), „Alle Analyse-Module … frei verfügbar" (`/kalender` ist Premium-gated), „Über 500 Basiswerte". |
| 6 | Uneinheitliche Produktangaben (DE 500+, EN 270+, Free & Premium) | Bestätigt; **keine Zahl stimmt**: `shared/symbols.py` hat 370 Einträge. |
| 7 | Scanner-Ergebnisse nur per JS | Plausibel, nicht geprüft; braucht GSC-URL-Prüfung (Nutzer). |
| 8 | Google zeigt FAQ-Rich-Results seit Mai 2026 nicht mehr | **Bestätigt** (developers.google.com/search/updates: Deprecation 08.05.2026, Feature weg ab 07.05.2026, Doku entfernt 15.06.2026). Folge für uns: die FAQPage-Offensive (docs/SEO_TODO.md) bringt keine Rich Results mehr; sichtbarer FAQ-Text bleibt als Inhalt wertvoll. |

Nebenbefund, nicht SEO: lokale Python-TLS-Prüfung meldete „certificate has expired" — die Live-Kette ist gültig
(Leaf bis 10.11.2026, YE2 bis 2028, Root YE bis 2032); Ursache ist der lokale Zertifikatsspeicher, nicht die Seite.

## Planentwurf

**Phase 1 — Defekte (kein Nutzer-Input nötig)**
1. Blog-Templates: `autoescape` für HTML-Attribute (Body-HTML bewusst `|safe`), JSON-LD über `|tojson`
   (oder im Builder als dict + `json.dumps`, wie `build_en.py`). Gilt für `blog_post.html` und `blog_index.html`.
2. Sitemap-Builder:
   - `/en/` und `/ueber-uns` aufnehmen (EN-Über-uns existiert nicht → nur DE).
   - EN-Blogartikel aus `blog/posts/en/` mit reziprokem hreflang über `de_slug`.
   - `has_en` aus EINER Quelle: `_EN_PAGE_META` in `landing/build_en.py` (statt pauschal), damit DE-only-Seiten
     und 301-Ziele nicht mehr drinstehen.
   - `lastmod` aus dem letzten Commit der Quelldatei (`git log -1 --format=%cs -- <datei>`), für Blog-Posts
     optional `updated:` im Front Matter, sonst `date`/Commit. Deploy-Server hat das Git-Repo.
3. Wächter `scripts/verify_seo_html.py`: parst die GEBAUTEN Seiten (`blog/output/`, `landing/en/`, `landing/*.html`)
   auf fremde Attribute in `<meta>` und gültiges JSON-LD; `--live` prüft alle Sitemap-URLs auf 200 ohne Redirect.
   Mutationstest: das kaputte Front Matter vorher/nachher (muss rot → grün).

**Phase 2 — Konsistenz (Nutzer-Input bei 2 Punkten)**
4. Produktzahlen aus einer Quelle (Zähler aus `symbols.py` beim Build) → Meta DE/EN, sichtbarer Text, Schema.
   „22 Tools", „24 Strategien", „131 Jahre" gegen den Bestand prüfen. **Kostenmodell (frei/Premium): Nutzerentscheidung.**
5. Startseiten-FAQPage-Markup entfernen (unsichtbar, inhaltlich falsch, Rich Result existiert nicht mehr) —
   alternativ sichtbare FAQ-Sektion mit korrigiertem Text. Empfehlung: entfernen, weil kein Nutzen mehr.
6. H1: beschreibend („Saisonale Börsenanalyse für Aktien, ETFs und Indizes"), Slogan als Zeile darüber.
   **Nutzerentscheidung (Marke/Design).** DE+EN, `data-i18n`.

**Phase 3 — Vertrauen (Nutzerentscheidung)**
7. Autor als `Person` + sichtbare Byline + Autorenseite, Prüfprozess auf `/ueber-uns` beschreiben.
8. `/en/ueber-uns` anlegen (E-E-A-T-Seite fehlt auf Englisch).

**Phase 4 — Inhalte/Messung (Nutzer)**
9. Review-Themenvorschläge existieren großteils schon (`dax-september-signifikanz`, Sell-in-May-Artikel,
   `/monatswechsel`) → keine neuen Seiten, sondern interne Verlinkung Artikel↔Tool; Priorisierung erst mit GSC-Daten.
10. GSC: URL-Prüfung `/scanner` (gerendertes HTML), Sitemap neu einreichen nach Phase 1.

## Prüfe besonders
- Stimmt meine Ursachenanalyse zu 1 und 4 am Code? Gibt es weitere Stellen mit unmaskierten Attributen
  oder handgebautem JSON-LD (Landing-Seiten, `build_en.py`-Fallback `localize_head_targeted`)?
- Ist `autoescape` im Blog-Builder riskant (Stellen, die HTML als Variable übergeben und dann doppelt maskiert würden)?
- `lastmod` aus Git: trägt das auf dem Server (Clone-Tiefe, Deploy-Revert `git checkout -- landing/`)?
- Reihenfolge und Abgrenzung: fehlt etwas Wichtigeres? Ist etwas überflüssig?
