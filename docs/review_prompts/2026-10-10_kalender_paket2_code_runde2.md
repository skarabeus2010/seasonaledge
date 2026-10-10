# Paket 2 (K2+K5) — Code-Review Runde 2 (Abnahme)

Runde 1: [Prompt](2026-10-10_kalender_paket2_code.md) · [Antwort](2026-10-10_kalender_paket2_code_antwort1.md) — keine Freigabe (Status).

<task>Prüfe, ob die drei Befunde behoben sind und nichts Neues kaputtging. Read-only. `git diff` + neue Dateien.</task>

## Umsetzung
1. Ungeprüfte Vergangenheit reicht jetzt bis 1885 (= Rechenbeginn) für NYSE, XETRA, LSE, TSE, EURONEXT, SIX,
   MILAN, STOCKHOLM, OSLO.
2. EURONEXT, MILAN, OSLO **und** SIX, STOCKHOLM ohne `belegt` (nur Stichproben) → `annahme` ab 2000.
   `belegt` bleibt: NYSE 1971–2028, XETRA 2002–2026, LSE 2026–2028, TSE 2001–2027, HKEX 2026; kommentiert,
   woraus sich der Vollabgleich jeweils ergibt.
3. Der Wächter vergleicht `kalender_status` für **jedes Jahr 1885–2100 und jede Börse** gegen eine wörtliche
   Bruchpunkt-Tabelle `STATUS_SOLL` (nicht aus `KALENDER_GUELTIG` abgeleitet) und prüft, dass sie alle Börsen
   abdeckt. Neue Mutationen: XETRA belegt bis 2100 (deine), NYSE ab 1950, EURONEXT 2018–2026 belegt.
   Ergebnis: Wächter **86/86**, Mutationen **15/15**, zwei Läufe identisch, Gegenproben 2/2.

## Fragen
1. Befunde behoben? 2. Ist „belegt“ für NYSE 1971–2025 haltbar, oder fehlt dafür ein Vollabgleich wie bei
TSE/LSE? 3. Sonst etwas vor dem Commit?

## Ausgabevertrag
**Urteil** · **Befunde** · **Antworten**. ≤ 40 Zeilen.
