# Kalender-Umstellung V1a — Produktionssperre (Code-Runde 4)

Runde 3: [Prompt](2026-10-11_kalender_v1a_code_r3.md) · [Antwort](2026-10-11_kalender_v1a_code_antwort3.md) (1 Befund).
Read-only, nichts schreiben, Mutationstest NICHT ausführen. Änderungen: `git diff` + neue Dateien.

<task>Ist der Befund aus Runde 3 behoben, und kann V1a deployt werden?</task>

## Umsetzung
- `modul_sperre(name)` nimmt den geteilten Lock auf einem **eigenen** Deskriptor (`dfd`), prüft darunter die Marke
  (`_sperren`) und legt `dfd` in `_dauer_fds` — nie geschlossen, das Betriebssystem gibt den Lock beim
  Prozessende frei. Unabhängig von `produktion()`: das Ende eines äußeren Blocks schließt nur dessen eigenen
  Deskriptor. Scheitert die Prüfung, wird `dfd` geschlossen und `Gesperrt` weitergereicht.
- Die Kennung wird einmal je Prozess gelesen und aus der Umgebung entfernt (`_kennung()`), damit ein Import vor
  `__main__` dieselbe Kennung sieht wie der spätere Lauf (vorher hätte der erste Eintritt sie verbraucht).
- `schreibsperre`: hält der Prozess einen Modul-Lock (`_dauer_fds`) oder ist in `produktion()`, nur Markenprüfung.
- Wächter (Linux): `with produktion("probe_aussen"): modul_sperre("probe_import")`, Blockende, dann
  `aktivierung_setzen(…, frist_s=0.8)` → muss `TimeoutError` liefern und keine Marke setzen.
  Neue Mutationen: „Modul-Sperre teilt den Lock mit dem Block" (der alte Weg: im Block nur prüfen) und
  „Modul-Sperre hält den Lock nicht" (`os.close(dfd)`).

## Nachweise
Windows-Wächter 71/71 (Lock-Prüfungen UNGEPRÜFT). Linux-Wächter streng + Mutationstest (24 + 6 Linux-Mutationen):
Ergebnisse folgen unten bzw. im Antworttext des Auftraggebers.

## Fokus
Bleibt ein Pfad, auf dem ein Prozess nach dem Import eines Pflicht-Moduls ohne gehaltenen Lock schreiben kann?
Stört der dauerhaft offene Deskriptor den Normalbetrieb (Kindprozesse via `subprocess` erben ihn nicht — Python
setzt O_CLOEXEC; `fork` ohne exec?)?

## Ausgabevertrag
**Urteil** · **Befunde** · **Auflagen**. ≤ 25 Zeilen.
