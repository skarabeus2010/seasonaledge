# Kalender-Umstellung V1b — Entwurf v2 (vor dem Code)

Runde 1: [Entwurf](2026-10-11_kalender_v1b_entwurf.md) · [Antwort](2026-10-11_kalender_v1b_entwurf_antwort1.md) („mit Änderungen").
Alles aus v1 gilt, außer den folgenden Punkten. Read-only.

<task>Sind die Befunde aus Runde 1 im Entwurf aufgelöst? Ist er jetzt als Bauvorlage tragfähig?</task>

## Entscheidungen aus Runde 1
- **Prüfzeile streng**: `SA.__release('%%RELEASE%%');` als erste Anweisung. Alle Harnesse laden über einen
  gemeinsamen Helfer (`scripts/js/release_harness.js`: echte `methode.js` + explizite HTML-Kennung) — keine
  Ersatzfunktion. `boersenkalender.js`: die Zeile erzeugt `build_boersenkalender_js.py` (sonst scheitert `--pruefen`).
- **V1b-1 und V1b-2 werden getrennt gebaut und abgenommen, aber in EINEM Deploy ausgerollt.**
- **Kennung = vollständiger Commit-Hash**, keine Zeitstempel-Ausweichkennung.

## 1 Eine Kennungsquelle, Ersetzung als letzter Schritt (P1 Blog, P1 Mischstand)
- `deploy.yml` bestimmt `RELEASE=$(git rev-parse HEAD)` **einmal** nach dem Vorspulen und übergibt sie explizit
  (`inject_credentials.sh` bekommt sie als Argument; kein eigenes `git rev-parse` dort mehr für die Kennung).
- Alle Erzeuger (Injection der Zugangsdaten, `build_en.py`, `blog_builder.py`) lassen den Platzhalter
  `%%RELEASE%%` **stehen**. Erst ein letzter Schritt `deploy/release_setzen.py <RELEASE>` ersetzt in `landing/`
  (inkl. `landing/en/`), `blog/output/` und `seo/tools/` **jeden** Kennungswert — den Platzhalter **und** jede
  frühere Kennung (Muster `__SA_RELEASE='…'` und `SA.__release('…')`) — durch `RELEASE`, danach Abschlussprüfung:
  jede Fundstelle trägt `RELEASE`, kein Platzhalter, jede HTML mit eigenem Skript setzt `__SA_RELEASE` → sonst rot.
- **Fehlerweg:** schlägt ein Schritt vor dem letzten fehl, läuft `release_setzen.py` trotzdem (Bash-`trap` auf
  `ERR`/`EXIT` im Deploy-Skript) und stellt **Konsistenz** her (alle Fundstellen = `RELEASE`, auch alte Blog-/EN-
  Ausgaben). Der Deploy bleibt rot, aber keine Seite sperrt dauerhaft. (In V9 gilt stattdessen der Rückweg aus
  v5–v7; dort ist ein veralteter Bau ein Abbruchgrund.)
- **Cache:** nginx liefert jede HTML-Antwort mit `max-age=0, must-revalidate` — neu: `/landing/*.html` (eigene
  Regex-Location vor `location /landing/`), `/rechtliches`, `/ueber-uns`, `/tools/` (Converter). Blog-Skripte
  bekommen `?v=<RELEASE>` wie die Seiten. Wächter liest `deploy/nginx.conf` und verlangt das für alle HTML-Wege.

## 2 Sperre ist endgültig und umfassend (P1 Folgeskripte, P1 laufende Arbeit, P2 direkte Fetches)
`SA.__sperre(grund)` in `methode.js`:
1. `__gesperrt` (nicht rücksetzbar) hat **Vorrang**: `SA.__release(k)` wirft bei `__gesperrt` immer
   `ReleaseFehler`, auch bei passender Kennung.
2. **Netz:** `methode.js` hüllt `window.fetch` beim Laden (vor allen anderen eigenen Skripten): jede Anfrage bekommt
   einen eigenen `AbortController` (mit dem Signal des Aufrufers verkettet) und wird registriert; bei `__gesperrt`
   lehnt die Hülle **neue** Anfragen sofort mit `ReleaseFehler` ab, `__sperre` bricht **alle laufenden** ab
   (Abbruch → `ReleaseFehler`). Deckt `kurse.js`, `SA.supabase.get/getAll`, `kalender-compute.js` und jeden
   direkten `/landing/`-Abruf ab, auch supabase-js (nutzt `fetch`). XHR kommt in eigenen Dateien nicht vor (Wächter).
3. **Endgültigkeit im Lader (V1b-2):** `kurse.js` und `SA.supabase.get/getAll` behandeln `ReleaseFehler` als
   endgültig — keine Wiederholung, kein Rückfall auf den eigenen Bedarf, keine wartende Ladung, kein Veröffentlichen;
   alle offenen Anfragen des Koordinators lehnen mit `ReleaseFehler` ab (Plan v9 Punkte 1–3).
4. **DOM:** `document.body.replaceChildren(hinweis)`; ein `MutationObserver` auf `body` entfernt danach jeden
   anderen hinzugefügten Knoten (spätere Ausgaben aus Rückrufen/`app.js` erscheinen nicht).
5. **Charts:** `methode.js` hüllt `ApexCharts` (CDN-Skript steht davor): Konstruktor registriert jede Instanz;
   `render`/`updateSeries`/`updateOptions`/`appendData` lehnen bei `__gesperrt` ab; `__sperre` ruft `destroy()` auf
   allen. Seiten ohne ApexCharts: Hülle entfällt.
6. **Zeitgeber:** keine Hülle (laufende Rückrufe finden weder Netz noch DOM-Ziel noch Chart).

## 3 Neuladen (P2)
Schlüssel `sa-release-neuladen` = Zeitstempel. Bei Sperre: kein Eintrag oder älter als 120 s → Eintrag setzen,
`location.replace` mit `?r=<zeit>`; sonst Hinweis „bitte neu laden" ohne Automatik. Speicherfehler (Zugriff wirft)
→ **kein** automatisches Neuladen, Hinweis sofort; die Sperre selbst greift immer vor dem Speicherzugriff.
Ein vollständig geladener, nicht gesperrter Stand (`load`-Ereignis ohne `__gesperrt`) löscht den Eintrag; ein
manueller Neuladeversuch nach 120 s darf wieder automatisch neu laden.

## Proben (zusätzlich zu v1 §8)
Chart-Stub mit **beobachtbarer** Zerstörung (Zähler) und Ablehnung nach Sperre; erneut passendes Skript nach Sperre
→ `ReleaseFehler`; `sessionStorage` wirft → Hinweis ohne Neuladen; später DOM-Anhang nach Sperre entfernt; direkter
`/landing/`-Fetch (`kalender-compute.js`) nach Sperre → keine Anfrage; supabase-js-Pfad über `fetch`; Deploy-Skript
auf einer Kopie: Fehler nach der Injection → alle Kennungen gleich. Mutationen je Vertragspunkt (benannte Prüfung).

## Ausgabevertrag
**Urteil** · **Befunde** · **Auflagen**. ≤ 30 Zeilen.
