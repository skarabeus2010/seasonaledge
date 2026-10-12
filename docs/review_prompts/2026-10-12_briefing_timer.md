# Daily Morning Briefing: GitHub-Cron → systemd-Timer — Prüfung

Read-only, Arbeitsbaum (nicht committet). Anlass: GitHub startete `daily_newsletter.yml` (`0 6 * * 1-5`) in der Woche
vom 05.10.2026 erst zwischen 11:48 und 14:18 UTC (API: created_at der Läufe). Nutzerentscheidung 2026-10-12:
wie die stündlichen Jobs auf einen systemd-Timer (Muster sa-intraday/sa-nightly, v65.3/v65.4).

<task>Ist die Umstellung tragfähig? Insbesondere: kein Doppelversand, kein stiller Ausfall, Produktionssperre,
Deploy-Fenster.</task>

## Änderung
- `deploy/systemd/sa-daily-briefing.service`: oneshot, `warte_auf_app.sh`, `docker exec … timeout --kill-after=30s
  15m python3 -u scripts/daily_newsletter.py` (ohne Argumente = produktiver Versand wie bisher der Zeitplan),
  `TimeoutStartSec=18min`, `SuccessExitStatus=75`.
- `deploy/systemd/sa-daily-briefing.timer`: `OnCalendar=Mon..Fri *-*-* 07:30:00 Europe/Berlin` (auf dem Server mit
  `systemd-analyze calendar` geprüft: nächster Lauf Di 2026-10-13 05:30 UTC), `Persistent=true`.
- `deploy/install_timers.sh`: beide Units in SERVICES/TIMERS (verify, Kopie nur bei Änderung, enable/start, Nachweis).
- `.github/workflows/daily_newsletter.yml`: **`schedule` entfernt**, nur noch `workflow_dispatch` (Test, Trockenlauf,
  Einzelempfänger; produktiver Notauslöser mit Standardwerten bleibt möglich).
- Doku: `docs/REFRESH_MONITORING.md`, `CLAUDE.md`, Kommentar in `daily_health_check.py`
  (`DAILY_NL_MAX_AGE_WORKDAYS = 2` unverändert).
- Wächter: `verify_produktionssperre` 71/71, `verify_workflow_inputs` grün.

## Fragen
1. Doppelversand: Timer und manueller Dispatch am selben Tag sind möglich (das Skript hat keine Tagessperre). Reicht
   die Doku „nur manuell“, oder braucht `daily_newsletter.py` eine Sperre „heute schon live versandt“ (aus
   `refresh_log`)?
2. `Persistent=true` holt einen verpassten Termin nach (Server aus). Ein Deploy, der den Container um 07:30 neu baut,
   beendet den Lauf dagegen per SIGKILL ohne Wiederholung (bekannte Klasse, v66.11). Akzeptabel oder Maßnahme?
3. Übersehe ich einen Verbraucher des alten Zeitplans (Health-Check, Doku, andere Workflows)?

## Ausgabevertrag
**Urteil** · **Befunde** (P1/P2) · **Antworten 1–3** · **Auflagen**. ≤ 20 Zeilen.
