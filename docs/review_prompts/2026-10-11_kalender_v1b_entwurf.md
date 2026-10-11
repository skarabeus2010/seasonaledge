# Kalender-Umstellung V1b — Entwurf: Methodenschalter, Releasekennung, Seitensperre (vor dem Code)

Bauplan: [docs/KALENDER_UMSTELLUNG.md](../KALENDER_UMSTELLUNG.md), Plan v2 §Grundsatz, v3 §1, v6 §1, v7 §1, v8, v9
(alle in `docs/review_prompts/2026-10-11_kalender_p3p4_plan_v*.md`). V1a (Produktionssperre) ist live (`e4ee675`).
Read-only. Bitte den **Entwurf** prüfen, bevor Code entsteht.

<task>Ist der Entwurf tragfähig? Wo widerspricht er dem freigegebenen Plan, wo fehlt etwas, und welche Fallen
(Seite bleibt gesperrt, Gate prüft eine freundlichere Welt) siehst du?</task>

## Fakten (gemessen)
- 24 eigene JS-Dateien unter `landing/js/`; 45 HTML unter `landing/` binden `app.js` ein, dazu `landing/embed.html`.
  Das Inline-Skript `window.__SA_SB_URL=…;window.__SA_SB_KEY=…` steht vor allen eigenen Skripten.
- `deploy/inject_credentials.sh` ersetzt Platzhalter nur in `landing/**/*.html` und hängt `?v=<GIT_SHA>` an
  `/landing/(css|js)/…`. Danach `build_en.py` (Host) → `landing/en/` erbt die Ersetzung.
- `blog/templates/blog_post.html` + `blog_index.html` binden `/landing/js/app.js` ein (ohne `?v=`, ohne
  Zugangsdaten); gebaut im Container (`blog_builder.py --build`) NACH der Injection; `blog/output/` gitignored.
- ~49 Prüf-Harnesse (`scripts/js/*.js`, `scripts/verify_*.py`) laden echte Dateien aus `landing/js/` in node/jsdom.

## Aufteilung
- **V1b-1 Bootstrap + Seitensperre** (dieser Entwurf, Hauptteil) · **V1b-2 Transportsperre** (`kurse.js`,
  `SA.supabase.get/getAll`, Plan v9) als eigener Schritt danach. V1c Ereigniskatalog, V1d Sitzungshelfer folgen.

## V1b-1
1. **`landing/js/methode.js`** (neu, einzige Ausnahme laut v8): `window.SA = window.SA || {}`; `SA.kalenderMethode =
   'alt'` (unveränderbar per `defineProperty`), `SA.release = '%%RELEASE%%'`, `class ReleaseFehler`,
   `SA.__sperre(grund)` (v8 §2: `__gesperrt` nicht rücksetzbar; Charts über eine Registry zerstören;
   `document.body.replaceChildren(hinweis)`; einmaliges Neuladen mit `?r=<zeit>`, Marke in `sessionStorage` je
   Kennungspaar; beim zweiten Mal „bitte neu laden"), `SA.__release(k)` (vergleicht `k` mit `window.__SA_RELEASE`,
   bei Abweichung `__sperre` + `throw new ReleaseFehler`). **Letzte Anweisung:** `SA.__release('%%RELEASE%%');`.
2. **Erste Anweisung jeder anderen eigenen JS-Datei:** `SA.__release('%%RELEASE%%');` — Frage 1 unten zur Form.
3. **HTML:** das Inline-Skript bekommt `window.__SA_RELEASE='%%RELEASE%%';`; `methode.js` ist das erste eigene
   Skript (vor `auth.js`/`i18n.js`/`app.js`), CDN-Skripte dürfen davor stehen.
4. **Injection:** `inject_credentials.sh` ersetzt `%%RELEASE%%` mit `GIT_SHA` (derselben Variable wie der
   Cache-Buster) in `landing/**/*.html` **und** `landing/js/*.js`; danach Prüfung: kein `%%RELEASE%%` mehr unter
   `landing/` → sonst Deploy-Abbruch (`scheitern`). Lokal bleibt `%%RELEASE%%` auf beiden Seiten → gleich → keine
   Sperre (Entwicklung und Harnesse unverändert lauffähig).
5. **Blog:** Templates bekommen Inline-Skript + `methode.js`; `blog_builder.py` setzt die Kennung aus der Umgebung
   `SA_RELEASE` (Deploy: `docker compose exec -e SA_RELEASE=$GIT_SHA …`), fehlt sie im Deploy → Abbruch.
6. **Python:** `shared/kalender_methode.py` mit `LESER = "alt"` (Konstante), `METHODEN = ("alt", "kalender_v1")`,
   `pruefe(m)`; Tests über ein Argument, nicht über die Umgebung (Produktion darf nicht umschaltbar sein).
7. **Einbindungswächter** `scripts/verify_einbindung.py` (ersetzt das Isolations-Gate C P3a): jede eigene JS-Datei
   beginnt mit der Prüfzeile (AST/Tokenizer, Kommentare übersprungen), `methode.js` hat sie als letzte; jedes HTML
   unter `landing/` und jedes Blog-Template mit eigenem Skript setzt `__SA_RELEASE` im Inline-Skript und bindet
   `methode.js` vor jedem anderen eigenen Skript ein; `boersenkalender.js` weiterhin von keiner Seite eingebunden;
   Injection auf einer Kopie ausgeführt → kein Platzhalter übrig, alle Kennungen gleich.
8. **Probe (jsdom, echte Seiten inkl. Dashboard + Backtest-Engine, Muster `verify_seiten_kurse.py`):** gleiche
   Kennung → Seite rechnet wie vorher (Seitenprobe-Fixtures unverändert); (a) HTML alt + Skript neu, (b) umgekehrt,
   (c) Abweichung erst bei einem spät geladenen Skript während laufender Rechnung, (d) zweiter Ladeversuch → kein
   Rechenergebnis im DOM, kein Chart mit Serien, genau ein Neuladen, beim zweiten Mal Hinweis. Mutationen v7/v8.

## Fragen
1. **Form der Prüfzeile.** Streng `SA.__release('…')` bricht jeden Harness, der eine Datei ohne `methode.js`
   lädt (~49) → alle Harnesse laden künftig `methode.js` zuerst (ein Helfer, viele Stellen). Alternative tolerant:
   `window.SA && SA.__release ? SA.__release('…') : 0;` — begründbar, weil nach V1b jedes HTML `methode.js` hat
   (Wächter) und eine Seite ohne `methode.js` nur ein Vor-V1b-HTML sein kann (Methode dort ebenfalls `alt`).
   Welche Form? Mein Vorschlag: **streng**, Harnesse laden `methode.js` über einen gemeinsamen Helfer.
2. Reicht `GIT_SHA` (kurzer Hash) als Kennung, oder braucht es eine eigene Deploy-Kennung (ein Revert-Commit mit
   `[ohne-deploy]` deployt nicht — Rückweg V9 spielt die gesicherten Dateien zurück, deren Kennung konsistent ist)?
3. HTML-Cache: nginx liefert Seiten `must-revalidate`; `?v=` an JS. Siehst du einen Weg, auf dem HTML und Skripte
   dauerhaft (nicht nur im Deploy-Fenster) auseinanderlaufen und die Seite immer sperrt?
4. Ist V1b-1 ohne V1b-2 deploybar (Seitensperre ohne Transportsperre), oder muss beides zusammen live gehen?

## Ausgabevertrag
**Urteil** (tragfähig / mit Änderungen / nicht) · **Befunde** · **Antworten auf 1–4** · **Auflagen**. ≤ 40 Zeilen.
