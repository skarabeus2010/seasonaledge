# Review-Auftrag: Wahlen — Phase 1b-2 (Seite /wahlen), Runde 3

Repo `C:\dev\Seasonaledge`. Fortsetzung von `2026-10-07_wahlen_1b2_runde2.md`. Deine offenen Punkte 2, 6, 8, 9
sind umgesetzt — prüfe den Arbeitsstand (`git diff`). Antwort auf Deutsch, je Befund Schwere + Datei:Zeile +
Änderung, am Ende genau eine Zeile `FREIGABE: ja` oder `FREIGABE: nein`.

- **9 Escaping (hoch):** In `serien()` wird `push` so überschrieben, dass JEDER Serienname durch `esc()` läuft
  (Legende/Tooltip von ApexCharts setzen innerHTML). Test: nach Tabellenklick auf eine Wahl mit
  `<img src=x onerror=…>` als Siegername enthält kein Serienname `<img`.
- **8 Snapshot:** Parameter wird unabhängig vom Wert erkannt (`/[?&]snapshot(?:=([^&]*))?(?:&|$)/`),
  `decodeURIComponent` im try; leer, `%`, `..%2F…`, ohne `=` und mitten in anderen Parametern → sichtbarer Fehler,
  kein Abruf. Tests für alle fünf Formen.
- **2 Übersetzungs-Timing:** Fehler werden als `{k, d}` gemerkt und bei `sa:i18n-bereit` neu übersetzt.
  Test: fehlender Snapshot mit spätem EN-Wörterbuch → englische Meldung.
- **6 Ergebnisdatum 2000:** Export enthält `result_decided` (Code war schon da; die Live-Datei wird nach dem
  Deploy neu gebaut). Tests: `verify_wahlen_build.py` prüft `contested` + `result_decided = 2000-12-12` und
  `kalender_belegt_ab` im Export; der Seitentest prüft den Hinweis „Ergebnis erst am 12.12.2000" in der Tabelle.

Belege: `probe_wahlen_seite.js` 0 Fehler; Gegenproben (Escaping der Serien entfernt, Fehler-Neuübersetzung
entfernt, alte Snapshot-Regex) jeweils rot. `verify_wahlen_build.py` 0 Fehler.
