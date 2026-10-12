# Daily Briefing auf systemd-Timer — Codex-Antwort Runde 1 (zusammengefasst)

**Urteil:** keine Freigabe.

**Befunde**
- **P1 Doppelversand:** Timer und manueller Dispatch am selben Tag ohne Sperre; ein abgebrochener Teilversand hat
  keine Wiederaufnahme (neu starten = alle Empfänger erneut).
- **P1 Deploy beendet den Versand:** ein Push, der um 07:30 den Container neu baut, beendet den Lauf per SIGKILL.
- **P2 Health-Check:** Test- und Einzelversand schreiben denselben `refresh_log`-`run_type` → ein Testversand kann
  einen fehlenden Live-Versand grün erscheinen lassen; keine Frist für den heutigen Live-Versand.
- **Veraltete Verweise:** `docs/ARCHITECTURE.md` (Zeitplan `0 6 * * 1-5`), Kopf von `scripts/daily_newsletter.py`,
  Kommentar in `scripts/daily_health_check.py`.
- **Wächter:** `verify_produktionssperre.py` prüft `SuccessExitStatus=75` nur für Nightly und Intraday.

**Auflagen:** Konkurrenz und Teilabbruch absichern; fehlenden Live-Abschluss nach einer festgelegten Frist alarmieren;
neue Unit und entfernten GitHub-Zeitplan mit gezielten Prüfungen abdecken.

**Nutzerentscheidung danach (2026-10-12):** „Deploy wartet“ — der Container-Austausch wartet unter der
Produktionssperre auf laufende Pflicht-Läufe (Obergrenze 45 min, danach rot).
