# P1b isoliert — Code-Review Runde 2 (Abnahme)

Runde 1: [Prompt](2026-10-10_kalender_p1b_code.md) · [Antwort](2026-10-10_kalender_p1b_code_antwort1.md) — mit Auflagen.

<task>Prüfe, ob die vier Auflagen erfüllt sind und nichts Neues kaputtging. Read-only. Neue Dateien + `git diff`.</task>

## Umsetzung
1. **Isolation über Generatoren**: Suche jetzt unter `landing/`, `deploy/`, `blog/`, `seo/` (ohne `output/`
   und `data/`), Endungen `.html .htm .js .json .py .sh .conf .j2 .css`; Lesefehler (`OSError`,
   `UnicodeDecodeError` bei `errors="strict"`) sind eine eigene rote Prüfung statt `pass`. Neue Mutation:
   Script-Einbindung im Kopf-Template von `landing/build_en.py` → gefangen an „Isolation keine Seite nutzt das Bundle“.
2. **Ausnahmen**: Wirft die API dort, wo ein Wert erwartet war, und die Meldung beginnt **nicht** mit
   `boersenkalender: ` (also ein Absturz, kein gewollter API-Fehler) → `[Ausnahme] API …` → die Mutation gilt
   als **ungültig**. Ein gewollter API-Fehler an falscher Stelle bleibt ein fachlicher Befund (sonst wurden
   die Mutationen „Wochentag verschoben“ und „ab einschließlich“ fälschlich verworfen — sie enden am Datenende
   regulär in „kein Handelstag bis zum Datenende“). Neue Gegenprobe: `null.x` im Golden-Week-Pfad → richtig
   verworfen.
3. **Datenende/Status**: nächster Handelstag für die letzten zwölf Tage 2100 × 13 Börsen (Soll aus Python mit
   Endgrenze, z. B. TSE 2100-12-31 → Fehler); `status` für **jedes** Jahr 1880–2105 × 13 Börsen; benannte
   Prüfungen „API naechsterHandelstag Datenende wirft“ und „Status NYSE 2028 belegt, 2029 Annahme“.
   Neue Mutationen: Endgrenze aufgeweicht, NYSE-Statusgrenze 2028 → 2029 — beide gefangen.
4. **Sperre**: alle fünf neuen Mutationstests lesen `ROH` erst **unter** `_exklusiver_lauf()` (gemeinsame
   Sperre aus `verify_twins_mutation.py`); `LockBelegt` → Abbruch mit Exit 1.
Ergebnis: Wächter **61/61**; Bundle-Mutationen **13/13** in zwei vollständigen Läufen, Gegenproben 3/3.
Die vier übrigen umgestellten Mutationstests einzeln nacheinander: Sollfälle 18/18, Nummern 15/15, Ticker 15/15, Fehlerweitergabe 11/11.

## Fragen
1. Auflagen erfüllt? 2. Ist die Abgrenzung „gewollter API-Fehler vs. Absturz“ über das Meldungspräfix
tragfähig, oder kann eine Mutation sie unterlaufen? 3. Sonst etwas vor dem Commit?

## Ausgabevertrag
**Urteil** · **Befunde** · **Antworten**. ≤ 40 Zeilen.
