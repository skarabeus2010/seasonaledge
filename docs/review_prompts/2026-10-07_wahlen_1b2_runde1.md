# Review-Auftrag: Wahlen — Phase 1b-2 (Seite /wahlen), Runde 1

Repo `C:\dev\Seasonaledge`. Grundlage: freigegebener Plan `docs/review_prompts/2026-10-06_wahlen_plan.md`
(Abschnitte 10–14), freigegebener Kern `landing/js/wahlen-compute.js` + `shared/elections.py` (Phase 1b-1,
Commit a96c482). Prüfe den Arbeitsstand (`git diff`, `git status` — neue Dateien). Antwort auf Deutsch, je
Befund Schwere + Datei:Zeile + Änderung, am Ende genau eine Zeile `FREIGABE: ja` oder `FREIGABE: nein`.

## Neu / geändert
- `landing/pages/wahlen.html` — Seite unter „Events": Index (S&P 500, Dow), Wahltyp, Regler X/Y 5–60, „ab Jahr",
  rückblickender Filter Machtwechsel, Umschalter „Wahltag = 0 %" / „Start = 0 % (mit Live-Linie)". Chart:
  Streuband p25–p75, Mittel, Median, graue Linie „Jahre ohne Wahl", Live-Linie (nur in Ansicht t−X),
  Einzelwahl per Tabellenklick. KPIs inkl. Abstand zur Vergleichslinie („historischer Vergleich, kein p-Wert"),
  Tabelle je Wahl, Liste der im Fenster nicht auswertbaren Wahlen mit Grund, Methodik, FAQ (+ FAQPage-JSON-LD;
  EN-Build entfernt FAQPage automatisch). Farben nur Gold/Grau, keine Parteifarben.
- Registrierung: `deploy/nginx.conf` (`location = /wahlen`), `landing/js/i18n.js` (`_EN_PAGE_META`),
  Navigation + Footer in `landing/components/nav.html`, `footer.html` und den Kopien in `landing/index.html`,
  `nav.wahlen` in de/en.json, 84 EN-Schlüssel `wa.*`, Sitemap-Priorität in `seo/programmatic_seo_builder.py`.
- `scripts/js/probe_wahlen_seite.js` — führt das Inline-Skript der Seite mit dem echten Rechenkern gegen eine
  Studie aus (DOM-/Chart-/fetch-Stubs): Laden, Serien, t0-Basis, KPIs, Tabelle, Live-Box, Umschalten auf t−X
  mit Live-Linie, Tabellenklick, „alle", X=5-Hinweis. Mit der Live-Studie: 0 Fehler; zwei Seiten-Mutationen
  (Live-Linie entfernt, Einzelwahl entfernt) gefangen.

## Belege
`landing/verify_en.py` FAIL 0 (wahlen sauber), `scripts/verify_en_serverpfad.py` 0 Fehler,
`scripts/verify_seo_html.py` 0 Fehler, Sitemap enthält `/wahlen` und `/en/wahlen`, `verify_wahlen_twin.py`
0 Fehler / 12/12.

## Prüfe besonders
- Ob die Seite irgendwo mehr behauptet, als die Daten tragen (Texte DE+EN, FAQ, Kennzahlbeschriftungen), und ob
  der rückblickende Charakter der Filter überall klar ist.
- Ob die Darstellung dem Plan entspricht (Streuband ≠ Konfidenzband, Referenz, Live nur in t−X-Ansicht,
  Datenstand sichtbar, ausgeschlossene Wahlen gezählt).
- XSS/HTML-Injection: Tabellenzellen werden per `innerHTML` aus `wahlen_study.json` (Cron-Output aus der
  kuratierten `elections.json`) gebaut — ausreichend, oder escapen?
- i18n: fehlende Schlüssel, deutsche Reste auf `/en/wahlen`, Zahlenformat DE/EN.
