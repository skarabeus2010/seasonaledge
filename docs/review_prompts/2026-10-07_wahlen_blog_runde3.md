# Review-Auftrag: Blogartikel Midterm 2026, Runde 3

Repo `C:\dev\Seasonaledge`. Vorgeschichte: `docs/review_prompts/2026-10-07_wahlen_blog_runde{1,2}.md`. Prüfe den
Arbeitsstand, Schwerpunkt deine drei Befunde aus Runde 2. Antwort auf Deutsch, je Befund Schwere + Datei:Zeile +
Änderung, am Ende genau eine Zeile `FREIGABE: ja` oder `FREIGABE: nein`.
Python: `C:/Users/HeikoSeibel/AppData/Local/Python/pythoncore-3.14-64/python.exe`.

## Umsetzung
1. **Fehlendes Minus:** Zahlen ohne Vorzeichen gelten als positiv; `1,02 %` statt `−1,02 %` ist rot.
2. **Typisierung:** `_werte()` ordnet Faktenblatt-Felder nach Schlüssel: `trefferquote` → Quote, Schlüssel mit
   `differenz` → Pp, übrige Gleitkommawerte → %; Ganzzahlen (Fallzahlen) und `_KEINE_RENDITE` (Offsets, Indexstand,
   Zähler) sind ausgeschlossen. Eine %-Zahl muss ein %-Wert sein, eine Pp-Zahl ein Abstand.
   Neue Mutationen je Sprache: Minus fehlt an einer Stelle, `+31,00 %`, `+0,72 Prozentpunkte` statt `+0,33` → 31/31.
3. **Fazit** DE+EN trennt Gesamtmittel (31 Wahlen) und gepaarten Vergleich (30 Tripel, +0,72/+0,39/+0,33).
