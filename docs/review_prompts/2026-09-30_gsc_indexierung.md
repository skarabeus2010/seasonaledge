# Review-Auftrag: GSC-Indexierung analysieren + Plan (ENTWURF, kein Code)

Repo `C:\dev\Seasonaledge`. Die Google Search Console meldet 551 nicht indexierte, 28 indexierte Seiten
(Stand GSC-Bericht ca. 21.09.; SEO-Phase-1 mit neuer Sitemap ist seit 30.09. live, Sitemap heute neu eingereicht).
Antwort auf Deutsch, je Befund Schwere + Beleg + konkrete Änderung; am Ende genau eine Zeile `FREIGABE: ja`
oder `FREIGABE: nein` (Freigabe = Analyse korrekt und Plan tragfähig).

## GSC-Gründe (Anzahl)
robots.txt blockiert 63 · 404 45 · Alternative Seite mit richtigem Canonical 36 · noindex 11 · Weiterleitung 8 ·
**Gecrawlt – zurzeit nicht indexiert 318** · Gefunden – zurzeit nicht indexiert 52 · Duplikat, Google wählte
anderes Canonical 18.

## Export „Gecrawlt – zurzeit nicht indexiert" (318 Zeilen, Datei `raw/gsc/2026-09-30_gecrawlt_nicht_indexiert.txt`
enthält nur die 33 Nicht-Dashboard-/Nicht-Analyse-Zeilen), meine Auswertung
- **~250× `/dashboard?t=<TICKER>`**, alle zuletzt gecrawlt 2026-04-12. Live: 200, `canonical` = `/dashboard`,
  robots index. Quelle der Links: `landing/pages/scanner.html:493`, `landing/pages/watchlist.html:511` (per JS
  erzeugte `<a href="/dashboard?t=…">`), außerdem `SearchAction.urlTemplate` im WebSite-Schema der Startseite.
- **~25× `/analyse/<slug>`**, zuletzt gecrawlt März/April. Live 410 (seit 2026-04-18 gewollt entfernt), aber
  `robots.txt` hat `Disallow: /analyse/` (erzeugt in `seo/programmatic_seo_builder.py::build_robots_txt`).
  Hypothese: Google darf die 410-Antwort nicht abrufen → die URLs bleiben dauerhaft als „blockiert"/„nicht
  indexiert" im Bestand; die 63 „robots.txt blockiert" sind vermutlich großteils dieselben Seiten
  (Export dafür steht noch aus).
- **31 echte Inhaltsseiten** (24 DE-Artikel, 3 EN-Seiten, `/pricing`, 6 Werkzeugseiten wie `/crash-fruehwarnung`,
  `/trifecta`, `/vixpiration`): live alle 200, in der Sitemap, Canonical = eigene URL, indexierbar; ausgelieferter
  Text ohne Script/Style: Artikel 710–1644 Wörter, Werkzeugseiten 437–885, `/pricing` 269.
  Also keine technische Sperre → Qualitäts-/Vertrauensentscheidung (junge Domain, wenige Backlinks,
  28 indexierte Seiten insgesamt). Viele zuletzt vor Wochen/Monaten gecrawlt, also vor Phase 1.
- 2 URLs ohne Schrägstrich → 301 auf die Fassung mit Schrägstrich (korrekt).
- Außerdem `/sitemap.xml`, `/landing/data/tickers.json`, `/watchlist` (noindex) in der Liste.

## Planentwurf
1. **`robots.txt`: `Disallow: /analyse/` entfernen**, damit Google die 410 sieht und die URLs verwirft.
   Prüfen, ob weitere Disallow-Pfade dasselbe Problem haben (`/app/` liefert 200 — Streamlit-Rest; `/static/`,
   `/_stcore/`, `/landing/pages/` 404, `/landing/data/`).
2. **Ticker-Varianten:** nichts ändern — Canonical ist korrekt, sie sollen nicht einzeln in den Index.
   Optional prüfen: Links im Scanner/Watchlist auf `/dashboard?t=` mit `rel="nofollow"`? (Eher nein: nofollow ist
   ein Hinweis, das Canonical reicht.)
3. **Echte Inhalte:** keine technische Änderung; stattdessen (a) GSC „Indexierung beantragen" für die wichtigsten
   ~10 Seiten, (b) Themen-Kannibalisierung im Blog prüfen (z. B. `sell-in-may-2026` + `sell-in-may-halbzeit-2026`,
   mehrere zeitgebundene „2026"-Artikel) und ggf. zusammenführen, (c) interne Verlinkung Tool↔Artikel
   (steht schon als TODO), (d) Off-Page/Backlinks (bekannter Engpass).
4. Exporte für **404 (45)** und **Duplikat (18)** anfordern, dann dieselbe Analyse.
5. Nach 2–3 Wochen GSC erneut messen (neue Sitemap, echte lastmod).

## Prüfe besonders
- Stimmt die robots.txt/410-Hypothese nach Google-Doku (robots-Sperre verhindert, dass Google 4xx/410 sieht)?
  Gibt es Nebenwirkungen, `/analyse/` freizugeben (z. B. Crawl-Budget)?
- Übersehe ich eine technische Ursache für die 31 Inhaltsseiten (Rendering, doppelte Inhalte DE/EN,
  hreflang, interne Links, Soft-404-Verdacht bei JS-lastigen Werkzeugseiten)? Prüfe Templates/Builder im Repo.
- Ist „nichts tun" bei den Ticker-Varianten richtig, oder sollten Scanner/Watchlist-Links anders gebaut werden?
- Was fehlt im Plan, was ist überflüssig?
