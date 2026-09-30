# Review-Auftrag: SEO Phase 1b — CODE, Runde 2

Repo `C:\dev\Seasonaledge`. Runde 1: `docs/review_prompts/2026-09-30_seo_phase1b_code_runde1.md`, FREIGABE nein, 3 Befunde.

**Neuer Beleg vom Nutzer:** das von Google gerenderte HTML für `/scanner` (GSC-Live-Test) ist `<html lang="en">`
mit Canonical `/en/scanner` — die Sprachweiterleitung traf Googlebot tatsächlich. Außerdem zeigte die gerenderte
Seite „Fehler beim Laden: … Unexpected end of JSON input" und eine leere Tabelle: `/landing/data/tickers.json`
war per robots.txt gesperrt. Beides adressiert diese Änderung (G1, G4).

Umsetzung deiner Befunde:
1. **Blog/hreflang:** `_injectHreflang` ersetzt keine vorhandenen (vom Build gebackenen) Sprachpaare mehr und
   fügt ohne vorhandene nur für bekannte Seiten welche ein. `_zielFuer('de')` fällt nur noch auf Seiten aus
   `_EN_PAGE_META` zurück, sonst `null` (Knopf deaktiviert). Hinweis: die Blog-Templates laden `i18n.js` nicht; dort
   regeln die gebackenen hreflang-Tags den Sprachbezug — eine Blog-Integration des Umschalters ist nicht Ziel dieser Änderung.
2. **Dynamische Links:** neu `SA.i18n.pfad(dePfad)` (EN-Präfix nur auf EN-Seiten und nur mit EN-Fassung);
   Scanner (`landing/pages/scanner.html:493`) und Watchlist (`landing/pages/watchlist.html:511`) bauen
   `dashHref` damit. Per grep: keine weiteren per JS gebauten internen Links.
3. **Regressionstest:** `en.json` wird jetzt geladen (voller Pfad `_applyAll`/`_injectHreflang`), Komponenten
   vor und nach dem JSON nachgeladen, DOM-Nachbau liest auch Eigenschaften; neue Fälle: gebackenes Paar mit
   abweichendem Slug bleibt nach JSON-Laden erhalten und ist Ziel von `switchTo('de')`; EN-Seite ohne DE-Paar →
   kein Wechsel + Knopf aus; `pfad()` auf EN/DE, mit/ohne EN-Fassung. Neu 0 Fehler, alt (`39556ab`) 25 Fehler.

Zum CI-Hinweis: es gibt keine CI-Stufe vor dem Deploy (Deploy = Push auf master); der Test läuft im lokalen
Mutationstest — dauerhaft absichern ließe sich das mit einem GitHub-Action-Job mit node vor dem Deploy
(Vorschlag, nicht Teil dieser Änderung).

Prüfe erneut. Antwort auf Deutsch, je Befund Schwere + Datei:Zeile + Änderung, am Ende genau eine Zeile
`FREIGABE: ja` oder `FREIGABE: nein`.
