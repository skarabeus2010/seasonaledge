# Kalender-Umstellung V1b — Code-Abnahme Runde 2

Runde 1: [Prompt](2026-10-11_kalender_v1b_code.md) · [Antwort](2026-10-11_kalender_v1b_code_antwort1.md) („nicht freigegeben", 5 Befunde).
Read-only, nichts schreiben, Mutationstest NICHT ausführen. Änderungen: `git diff` + neue Dateien.

<task>Sind die fünf Befunde aus Runde 1 behoben? Kann V1b (V1b-1 + V1b-2 gemeinsam) deployt werden?</task>

## Umsetzung
1. **Fehlerweg (P1):** `release_falle` + `trap … EXIT` stehen jetzt VOR `git checkout -- landing/`; die Falle bestimmt
   die Kennung beim Auslösen (`$(git rev-parse HEAD)`: nach dem Vorspulen der neue, sonst der alte Commit) und läuft
   nur, wenn `deploy/release_setzen.py` in diesem Stand existiert (vor V1b keine Kennungen). Damit gedeckt:
   gescheitertes Vorspulen, Fehler der ersten Normalisierung, jeder spätere Fehler. Wächter prüft die Reihenfolge
   Falle < Reset < Vorspulen < RELEASE und dass die Falle `rev-parse HEAD` nutzt.
2. **Request-Signal (P2):** `aufrufer = opt.signal || eingabe.signal`; Probe `transport g_request_signal` (mit und
   ohne Hülle, Kontrolle: ohne Abbruch bleibt offen).
3. **/tools/ (P2):** `max-age=0, must-revalidate`; Wächter prüft `location /tools/` mit.
4. **Exit-Code (P2):** `verify_release_sperre.lauf` lehnt jeden Exit ≠ 0 ab, auch nach vollständiger Ausgabe.
5. **Nachweise (P2):** zweite echte Seite (Backtest-Engine: gleich, a, c, je Kontrolle); `f2_body_waehrend` (Sperre
   WÄHREND des Body-Lesens, Kontrolle); Tour-Lader nach Sperre (driver.js/CSS, Kontrolle lädt beides); echte
   Bibliotheken ApexCharts 4.7.0 + supabase-js 2.117.3 (fest in `scripts/perf/package.json`, Gate installiert per
   `npm ci`) in `probe_release_bibliotheken.js`: Normalbetrieb ohne / mit methode.js / mit methode.js VOR den
   Bibliotheken (Setter-Pfad) gleich (supabase-Daten, SVG, Statics), Kontrolle ohne methode.js liefert Daten + SVG;
   nach Sperre keine Anfrage aus supabase-js, render/Konstruktor `ReleaseFehler`. SVG-Messung in jsdom per gleicher
   Ersatzfunktion in allen drei Läufen.
Dazu eigener Befund: der Mutationstest ordnete „methode.js kaputt" als gefangen ein — die Seitenprobe bricht jetzt
ohne Endmarker ab, wenn methode.js nicht geladen ist.

## Nachweise (Windows lokal, ein Durchlauf ohne Änderungen dazwischen)
37 Wächter grün, u. a. `verify_einbindung` 24/24, `verify_release_sperre` (Transport 8 Fälle × 4 Modi, Seite 20
Fälle, Bibliotheken 7), `verify_seiten_kurse` 313/313, `verify_kurse`, `verify_produktionssperre`, alle Harnesse.
Rot nur, was schon vorher rot war bzw. erst nach dem Commit grün wird (build_boersenkalender_js --pruefen gegen HEAD;
verify_seo_html an veralteten lokalen blog/output; verify_en_translation auf HEAD ebenfalls Exit 1; Snapshot-Wächter
ohne Snapshot-Ordner — mit `--ohne-snapshot` grün). Mutationstest 26/26, Gegenproben 2/2 verworfen, Projektbaum-Hash
vor = nach.

## Ausgabevertrag
**Urteil** · **Befunde** · **Auflagen**. ≤ 25 Zeilen.
