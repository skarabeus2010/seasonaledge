# Daily Briefing auf systemd-Timer — Runde 2

Read-only, Arbeitsbaum (nicht committet). Runde 1: [Antwort](2026-10-12_briefing_timer_antwort1.md), keine Freigabe.
Nutzerentscheidung zu P1 „Deploy“: **Deploy wartet** auf laufende Pflicht-Läufe.

<task>Sind alle Befunde aus Runde 1 behoben, ohne neue Lücken? Insbesondere die Versandsperre, die Deploy-Sperre
und ob der Wächter die Wirkung prüft.</task>

## Umsetzung
1. **`shared/versandsperre.py` (neu):** `Versand(name, wiederaufnahme=False)` — Berliner Datum; `logs/versand/<name>_<datum>.{lock,json,gesendet}`
   (./logs ist in den Container gemountet). Exklusiver `flock … LOCK_NB` → `parallel`; Status `fertig` → `schon_versandt`;
   Status `laeuft` ohne Wiederaufnahme → `abgebrochen`. Je erfolgreicher Mail `notieren()` (Hash, fsync), am Ende
   `abschliessen()`. Keine Adressen auf Platte.
2. **`scripts/daily_newsletter.py`:** nur im Live-Modus; `schon_versandt` → Exit 0 ohne Versand und ohne refresh_log,
   `abgebrochen` → Admin-Alarm + Exit 6, `parallel` → Exit 6; `--wiederaufnahme` überspringt bediente Empfänger
   (außerhalb live → Exit 2). Fehlgeschlagene Empfänger werden nicht notiert. `refresh_log.missing_details.modus` ∈ live/test/einzel.
3. **`scripts/daily_health_check.py` Check 5c:** nur Live-Zeilen (Altzeilen ohne Modus = live, letzte 30 Zeilen);
   werktags ab 10:00 Berlin ohne Live-Lauf mit heutigem Berliner Datum → rot.
4. **`.github/workflows/deploy.yml`:** `docker compose build`, dann
   `flock -x -w 2700 logs/sperre/produktion.lock docker compose up -d || scheitern …`; `command_timeout: 75m` der
   ssh-action (Standard wäre 10 min). Nicht erfasst: Läufe außerhalb des Pflicht-Inventars (Brier) — dokumentiert.
5. **Wächter:** `scripts/verify_briefing_versand.py` führt `daily_newsletter.main()` echt aus (Attrappen nur für Daten,
   Empfänger, Brevo, refresh_log): Abbruch per SystemExit mitten im Versand (Sperre wie bei Prozessende freigegeben),
   kein blinder Neustart, Wiederaufnahme ohne Doppelte, zweiter Lauf nach Abschluss ohne Versand, Test/Einzel unberührt
   mit eigenem Modus, paralleler Lauf (nur Linux; `--streng` macht UNGEPRÜFT rot). Health-Helfer und Betrieb (Timer,
   Unit, Installer, Workflow ohne `schedule`). Windows 41/41 + 2 ungeprüft, **Linux im Container 43/43**.
   Mutationstest `verify_briefing_versand_mutation.py` **21/21**, Gegenproben richtig verworfen, Projektbaum unverändert.
   `verify_produktionssperre.py`: jede Unit, die ein Pflicht-Skript startet, braucht `SuccessExitStatus=75`;
   Deploy-Sperre + ssh-Frist > Wartefrist geprüft; Mutationen ergänzt. Gate-Schritt „Waechter - Briefing-Versand“.
6. Doku: ARCHITECTURE-Zeile, Kopf `daily_newsletter.py`, Kommentar Health-Check.

## Fragen
1. Writer-Starvation: neue `LOCK_SH`-Läufe können einen wartenden `flock -x` überholen. Bei Intraday (stündlich ~1 min)
   unkritisch? Reicht die 45-min-Obergrenze mit rotem Deploy?
2. Ist „fertig auch bei Fehlschlägen“ richtig (fehlgeschlagene Empfänger nicht automatisch erneut — >10 % → Admin-Alarm
   und Exit 5 wie bisher)?
3. Die Sperre greift erst nach `build_daily_context` (Minuten). Ein paralleler zweiter Lauf rechnet also umsonst — Problem?

## Ausgabevertrag
**Urteil** (Freigabe / keine Freigabe) · **Befunde** (P1/P2, mit Datei:Zeile) · **Antworten 1–3** · **Auflagen**. ≤ 25 Zeilen.
