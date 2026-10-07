# Review-Auftrag: Blogartikel Midterm 2026 (DE+EN) + Snapshot/Fakten/Wächter + Bildpfad-Fix, Runde 1

Repo `C:\dev\Seasonaledge`. Antwort auf Deutsch, je Befund Schwere + Datei:Zeile + Änderung, am Ende genau eine
Zeile `FREIGABE: ja` oder `FREIGABE: nein`. Python: `C:/Users/HeikoSeibel/AppData/Local/Python/pythoncore-3.14-64/python.exe`.

## Gegenstand (alles uncommittet, `git status`)
- Artikel `blog/posts/2026-10-07_midterm-wahltag-boerse.md`, `blog/posts/en/2026-10-07_midterm-election-day-stock-market.md`
  (Bilder `blog/posts/images/wahlen-midterm-2026/*.png`), Rücklinks in vier bestehenden Midterm-Artikeln.
- Snapshot `landing/data/wahlen_snapshots/midterm-2026-10.json` (unveränderlich, erzeugt mit `scripts/wahlen_snapshot.py`
  aus Code d6d4999, Kurse bis 06.10.2026). Die Seite zeigt ihn unter `/wahlen?snapshot=midterm-2026-10`.
- `scripts/research/wahlen_fakten.py` (Faktenblatt aus dem Snapshot, Rechenkern `shared.elections.aggregiere`),
  `scripts/research/render_wahlen_charts.py` (Charts aus dem Snapshot).
- Wächter `scripts/verify_wahlen_blog.py` (+ `--mutationen`, 8/8): Snapshot-Kennzahlen neu gerechnet = gespeichert,
  Pflichtzahlen im Text, Snapshot-Link, Bilder.
- `blog/blog_builder.py::_bild_src`: relative Bilder in EN-Artikeln zeigten auf `/blog/<en-slug>/images/…` (404 sobald
  EN- und DE-Slug abweichen, live belegt), jetzt `/en/blog/<slug>/images/…`; `lang` wird an `_inline` durchgereicht.

## Verbindliche Kernaussage (aus dem freigegebenen Plan docs/WAHLEN.md)
Kein Signal, kein p-Wert in Phase 1, „Sell" ≠ Leerverkauf, Vergleich gegen die angrenzenden ungeraden Jahre, rückblickende
Filter (Mehrheitswechsel) als solche kennzeichnen. Der Abstand zu Jahren ohne Wahl liegt im Vorlauf, nachher klein, ab 1971 ≈ 0.

## Prüfe besonders
1. **Jede Zahl** im Text gegen `wahlen_fakten.py <snapshot>` (inkl. abgeleiteter Formulierungen wie „knapp zwei von drei",
   „kein Vorsprung über einem halben Prozentpunkt", „18 der 31 Fenster vor 1971", n=30/13).
2. **Zu starke Aussagen** (die teuerste Fehlerklasse unserer Erklärartikel): Kausalbehauptungen, Absolutheiten,
   historische Kontextsätze (1914, 1962 Kubakrise, 1974, NYSE am Wahltag geschlossen bis 1968), „November eher freundlich".
3. DE und EN inhaltlich deckungsgleich; Links existieren (Slugs, `/en/elections`).
4. Wächter: kann er grün sein, obwohl eine Zahl im Text falsch ist (z. B. falsches Vorzeichen, Zahl nur in der FAQ,
   Rundung)? Sind die Mutationen wirksam?
5. Bildpfad-Fix: Nebenwirkungen auf andere EN-Artikel, Inline-Bilder, Chart-Bilder (`_build_chart_image`).
