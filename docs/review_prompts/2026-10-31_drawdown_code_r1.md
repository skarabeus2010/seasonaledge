# Code-Prüfung R1 — Drawdown-Analyse Phase 1 (`/drawdown`)

Grundlage: Bauplan v3 (+ v2, Methodik) und Nachtrag 3 „beobachtete Schlusskurse“ (FREIGABE MIT AUFLAGEN, Auflage
„Handelstage mit Kurs“ umgesetzt). Alle Pläne/Antworten: `docs/review_prompts/2026-10-31_drawdown_*`.

Zu prüfen:
- `shared/drawdown.py` (Python-Kern, auch für Phase 2 Nightly/Mail) und `landing/js/drawdown-compute.js`
  (`SA.drawdown`, Zwilling): E-Regel, Achse inkl. Vertrag B (Brücke, ≤ 2 in Folge, CRYPTO nie, belegtes Jahr =
  Lücke, Reihenende = nicht aktuell), Episoden, Gruppen/Ränge, vergleich_ab, Kaplan-Meier (Gleichstände, Greenwood,
  log-log, Ränder S=0/1, Zensierung laufend/Lücke), Forward Returns, Kalender/Ulcer, Toleranz EPS = 1e-12 an Schwellen
  (log/exp runden in Python und JS verschieden — am Fall „genau −10 %“ gefunden), RENDITEBASIS nur belegt.
- `landing/pages/drawdown.html`: Rendern, Kurzantwort-Bausteine je Fall, Kennzeichnungen, Fehlerverhalten
  (Banner, Reset nach vorherigem Erfolg), überholte Antworten, volle Historie (`ab: null`), EN über `en.json`
  (`_JSON_VER` v28), Nav (`nav.html` + `index.html` Nav und Footer), nginx `location = /drawdown`, `_EN_PAGE_META`.
- `scripts/verify_drawdown.py` (Gate, 185 Prüfungen: A Handfälle, B unabhängige Referenz, C Zwilling auf vier
  eingefrorenen Reihen in drei Zeitzonen, D Invarianten, E Stichtag, F echte Seite DE/EN in jsdom über
  `scripts/js/probe_drawdown_seite.js`) und `scripts/verify_drawdown_mutation.py` (20/20; „Krypto-Ausnahme entfernt“
  als äquivalent begründet herausgenommen).
- `.github/workflows/deploy.yml` (Gate-Schritt), `scripts/fixtures/drawdown/*` (SHA-256 im Wächter).

Fragen: Rechnen die Zwillinge den Vertrag? Welche falsche Anzeige/Zahl käme durch den Wächter? Was fehlt an
Grenzfällen (z. B. KM-Gleichstand Ereignis/Zensur, `n = 1`, exakte Filterschwelle m, Schalttag in minus_jahre,
Krypto-Wochenende, Forex-Freitag)? Stimmen die Texte (DE/EN) mit den Zahlen und dem Vertrag überein?
Schluss: FREIGABE, FREIGABE MIT AUFLAGEN oder NICHT FREIGABEFÄHIG.
