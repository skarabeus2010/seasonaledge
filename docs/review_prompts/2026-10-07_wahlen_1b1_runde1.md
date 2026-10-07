# Review-Auftrag: Wahlen — Phase 1b-1 (Browser-Rechenkern + Nightly), Runde 1

Repo `C:\dev\Seasonaledge`. Grundlage: freigegebener Plan `docs/review_prompts/2026-10-06_wahlen_plan.md`
(Abschnitte 10–14), freigegebener Python-Kern `shared/elections.py` (Phase 1a). Prüfe den Arbeitsstand
(`git diff`, `git status` — neue Dateien). Antwort auf Deutsch, je Befund Schwere + Datei:Zeile + Änderung,
am Ende genau eine Zeile `FREIGABE: ja` oder `FREIGABE: nein`.

## Neu
- `landing/js/wahlen-compute.js` — DOM-freier Kern der Seite `/wahlen`: Auswahl −X…+Y, konstante Stichprobe
  (nur Wahlen mit Kurs an allen Offsets), Umbasierung t0 oder t−X, Renditen als Quotienten, Mittel/Median/
  p25/p75 (linear wie numpy), Referenz nur aus vollständigen Tripeln (Kontrollpfade einzeln umbasiert → je
  Block gemittelt → über Blöcke), rückblickender Filter „Wechsel" (Präsident: Parteiwechsel; Midterm:
  Wechsel der House-Mehrheit; unbekannt fällt aus ja/nein heraus), Live-Linie auf t−X normiert (null, wenn
  t−X noch in der Zukunft liegt).
- `shared/elections.py::aggregiere` — Python-Zwilling derselben Regeln.
- `scripts/js/probe_wahlen.js` + `scripts/verify_wahlen_twin.py` — baut eine Studie aus Zufallskursen auf dem
  echten Kalender (mit zwei Datenlücken und zwei künstlich unbekannten Ergebnissen), führt die echte JS-Datei
  in node aus und vergleicht jede Zahl mit Python (8 Optionssätze); feste Fälle: Quantil = numpy,
  Basisdatum, fensterabhängige Stichprobe, unbekannter Wechsel, Live X=5 (Basis Zukunft → null) und X=25
  (−25…−21 gefüllt). `--mutationen`: 7/7 JS-Mutationen gefangen.
- `scripts/nightly_refresh.py`: Phase J ruft `build_wahlen.py` nach dem Kurs-Refresh; Exit ≠ 0 → Nightly rot.

## Prüfe besonders
- Regeltreue zum Plan (R2-4 Tripel, R4-1/R4-2 Format und fensterabhängige Stichprobe, R2-1/R4-1 Live).
- Ob der Zwillingsvergleich etwas übersieht (z. B. Live-Werte werden nur stichprobenhaft geprüft; die Listen
  `wahlen` und `ausgeschlossen` nur gezählt).
- Phase J: Reihenfolge im Nightly, Timeout, Fehlerweitergabe; was passiert am Wahltag selbst und danach,
  solange `status` in elections.json noch `scheduled` ist?
