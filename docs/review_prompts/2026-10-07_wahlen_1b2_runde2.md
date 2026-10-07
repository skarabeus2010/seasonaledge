# Review-Auftrag: Wahlen — Phase 1b-2 (Seite /wahlen), Runde 2

Repo `C:\dev\Seasonaledge`. Fortsetzung von `2026-10-07_wahlen_1b2_runde1.md`. Prüfe den Arbeitsstand
(`git diff`, `git status`) gegen deine neun Befunde. Antwort auf Deutsch, je Befund Schwere + Datei:Zeile +
Änderung, am Ende genau eine Zeile `FREIGABE: ja` oder `FREIGABE: nein`.

## Umsetzung
1. **EN-Erkennung:** `istEN()` liest `SA.i18n.isEN()` zur Renderzeit; Zahlen mit Punkt, Datum ISO.
2. **Übersetzungs-Timing:** `landing/js/i18n.js` meldet `sa:i18n-bereit` (auch im Fehlerfall) und bietet
   `bereit()`; `_JSON_VER` v4 → v5. Die Seite rendert erst, wenn Daten UND Wörterbuch da sind, und rendert auf das
   Ereignis neu. Parteien/Gründe sind Funktionen, die `T()` zur Renderzeit rufen.
3. **Vergleichskennzahl:** „Differenz Wahl − ohne Wahl" in **Prozentpunkten**, Untertitel „gepaart je Wahl,
   nachher · historischer Unterschied, kein p-Wert"; Kennzahl „Ø ohne Wahl (nachher)" mit „n Wahlen mit beiden
   Vergleichsjahren"; Legende der grauen Linie mit n; Chart-Hinweis erklärt, warum ihr Abstand zur goldenen Linie
   von der gepaarten Differenz abweichen kann.
4. **Datenstand:** eigene Zeile `#stand` unabhängig von Live und Filtern (letzter Schlusskurs der Reihe,
   Kalender geprüft ab, Hauptfenster/Exploration, ggf. Snapshot). Live-Box mit t0 (projiziert gekennzeichnet),
   letztem Kurs und Basisdatum.
5. **Unbelegter Kalender:** `kalenderBelegt` je Wahl (Fensterbeginn ≥ `kalender_belegt_ab`, neu im Build-Export)
   in JS und Python (Zwillingsvergleich umfasst das Feld); Zählung in der Kennzahl, Stern in der Tabelle,
   Fußnote mit Samstags-Hinweis.
6. **Begriffe:** durchgehend „Referenzschluss t0" (Achsen, Annotation, Tabelle, Buttons); die eingeblendete
   Einzelwahl trägt Wahltermin, t0 und Ergebnis im Namen (Tooltip/Legende), verspätetes Ergebnis 2000 mit Datum
   (`result_decided` neu im Build-Export).
7. **Aussagen:** FAQ (sichtbar, JSON-LD, EN) „historischer Unterschied, kein isolierter Wahleffekt"; Hauptfenster
   20/20 als vorab festgelegt gekennzeichnet, Knopf „Hauptfenster 20/20", andere Fenster als „Exploration".
8. **Snapshot:** `?snapshot=<id>` (Regex `^[a-z0-9][a-z0-9-]{0,63}$`) lädt ausschliesslich
   `/landing/data/wahlen_snapshots/<id>.json`, verlangt `snapshot_id` = id, übernimmt `ansicht`; ungültig/fehlend
   → sichtbarer Fehler, kein Rückfall auf die aktuelle Datei. (Snapshots selbst werden mit dem Blogartikel erzeugt.)
9. **Escaping:** alle Datenwerte über `esc()` in HTML, `data-id` escaped, Texte sonst per `textContent`.

## Belege
`scripts/js/probe_wahlen_seite.js` (jetzt 6 Läufe: DE, EN mit spätem Wörterbuch, XSS, Snapshot gültig/fehlend/
ungültig) 0 Fehler; 5 Seiten-Mutationen gefangen (Escaping, EN-Erkennung, Warten auf Wörterbuch, Snapshot-Rückfall,
Datenstand nur mit Live). `verify_wahlen_twin --mutationen` 12/12, `verify_en` FAIL 0, `verify_en_serverpfad` 0,
`verify_seo_html` 0, `probe_i18n_sprache` 0.
