# Code-Review: Blog-Cache-Buster (Search Console „Seite mit Weiterleitung“), ATKR aus dem Universum, robots.txt

Read-only, Deutsch, **FREIGABE (Code): ja/nein**, Befunde P1/P2/P3. Code uncommittet (`git diff`).

## 1. Blog-Seiten ohne Cache-Buster → Release-Sperre im Google-Renderer
Befund (nginx-Log, Googlebot): jede Blogseite (Index, Kategorie, Tag, auch Artikel) wurde wenige Sekunden nach dem
Abruf erneut mit `?r=<Zeitstempel>` geholt (eingefrorene Renderer-Uhr 2026-10-04/11-03 00:00). Das ist
`methode.js::neuladen()` — die Release-Sperre greift, ersetzt das Dokument durch den Hinweis und lädt neu. Ursache:
`deploy/inject_credentials.sh` hängt `?v=<RELEASE>` nur in `landing/` und `seo/tools/` an; der Blog entsteht erst
danach (`blog_builder.py --build` im Container) und band `/landing/js/methode.js` und `app.js` ohne `?v=` ein
(live geprüft DE/EN). Googles Renderer cacht Skripte lange → frische HTML + Skript eines alten Releases.
Feature-Seiten (`/skew` …) tragen `?v=<RELEASE>` und sind nicht betroffen.

Änderung `deploy/release_setzen.py` (läuft im Deploy als letzter Schritt aller HTML-Erzeuger über landing,
blog/output, seo/tools):
- `ASSET` = `(src|href)="/landing/(js|css)/….(js|css)(?v=…)?"`; `assets_setzen(text, wert)` setzt `?v=<wert>`, nur bei
  echter Kennung (beim Normalisieren mit `%%RELEASE%%` bleibt die Adresse unverändert).
- Abschlussprüfung `assets_pruefen`: mit echter Kennung muss jede eigene JS/CSS-Adresse `?v=<wert>` tragen, sonst
  Exit 1 (Deploy rot).
- Wächter `scripts/verify_einbindung.py` (im Gate): Simulation — alte Blogseite ohne `?v=` bekommt ihn, EN-Seite mit
  `?v=abc1234` wird umgeschrieben, Platzhalter verlangt keinen Cache-Buster, Asset ohne/mit fremdem `?v=` (JS und
  CSS) → rot, erneutes Setzen repariert. 29/29.
- `scripts/verify_release_mutation.py`: zwei neue Mutationen (Setzen fehlt, Befund fehlt) → 28/28 gefangen.
  **Nebenbefund:** der Mutationstest war seit Kalender V2 (`30b8abf`) kaputt — die isolierte Kopie enthielt weder
  `scripts/fixtures/einbindung_manifest.json` noch `seo/tools/`, die Grundlinie war rot und brach vor der ersten
  Mutation ab (nicht im Gate, deshalb unbemerkt). Beides wird jetzt mitkopiert.
Frage: Berührt der Cache-Buster etwas, das ihn nicht verträgt (z. B. Templates, die `/landing/js/…` in Inline-Code
oder in `<link rel=preload>` nennen; Blog-RSS; E-Mail-Vorlagen außerhalb der Bäume)? Ist `[A-Za-z0-9%]*` im alten
`?v=` ausreichend?

## 2. ATKR aus dem Universum
Atkore wurde von Prysmian übernommen (Abschluss 19.10.2026, 95 USD in bar, NYSE-Delisting; letzte Sitzung 16.10.).
- `shared/symbols.py`: Eintrag aus `SYMBOLS` entfernt (372 Ticker); neu `AUSGESCHIEDEN = {"ATKR": {…}}` — nicht in
  `get_all_tickers()`, Kurse bleiben als Historie in `prices`.
- `scripts/check_db_completeness.py`: Orphan-Check nimmt `AUSGESCHIEDEN` aus (sonst ab Sonntag rot), nennt sie im
  grünen Text.
- `landing/data/tickers.json` und `landing/js/boersenkalender.js` neu erzeugt (ATKR fehlt).
- Bewusst unverändert: `landing/data/vol_saisonalitaet.json` (eingefrorene Studie, „333 Profile“ geprüft von
  verify_seo_html), `scripts/fixtures/ticker_boerse_2026-10-10.json` (Bestandsmomentaufnahme; ATKR ohne Suffix löst
  weiter auf NYSE auf).
Frage: Liest irgendein Pfad ATKR noch so, dass ein fehlender SYMBOLS-Eintrag scheitert (Mail-Watchlists einzelner
Nutzer mit ATKR, Scanner-Altzeilen, Options-Universum)?

## 3. robots.txt
`seo/programmatic_seo_builder.py`: `Disallow: /landing/data/*/$` — nur Ordneradressen (nginx 403, Google las
`/landing/data/wahlen_snapshots/` aus dem Seiten-JS). Die JSON-Dateien bleiben abrufbar (Render-Ressourcen); der
Wächter verify_seo_html verbietet weiter nur `Disallow: /landing/data/`.
Frage: Matcht Googles robots-Syntax `*/$` so, wie beabsichtigt (Ordner ja, `…/x.json` nein)?
