# Daily Briefing auf systemd-Timer — Runde 3

Read-only, Arbeitsbaum (nicht committet). Runde 2: [Antwort](2026-10-12_briefing_timer_r2_antwort.md), keine Freigabe.

<task>Sind die Auflagen aus Runde 2 erfüllt, ohne neue Lücken?</task>

## Umsetzung der Auflagen
1. **Zweistufiges Journal** (`shared/versandsperre.py`): je Empfänger `? <hash>` VOR dem Versand (fsync), danach
   `+` (angenommen) oder `-` (eindeutig nicht versandt: Anbieter liefert False, Mail ließ sich nicht bauen). `?` ohne
   `+`/`-` = ungeklärt → `uebrige()` überspringt angenommene UND ungeklärte; die Wiederaufnahme meldet die Zahl der
   Ungeklärten per Admin-Alarm. Eine Ausnahme im Versandaufruf lässt den Empfänger ungeklärt (Annahme unbekannt).
2. **Journalfehler beenden den Lauf** (`scripts/daily_newsletter.py`): `beginnen`/`notieren`/`abgelehnt` stehen
   außerhalb der try-Blöcke; die Ausnahme läuft durch, Status bleibt `laeuft`, kein refresh_log-Eintrag.
3. **Frist ohne Live-Zeile** (`scripts/daily_health_check.py` Check 5c): auch der Zweig ohne Live-Zeile wird nach der
   Frist rot.
4. **Automatischer Fristtermin:** `deploy/systemd/sa-briefing-frist.{service,timer}` Mo–Fr 10:15 Europe/Berlin
   (Server: nächster Lauf Di 08:15 UTC), `daily_health_check.py --briefing-frist` liest nur refresh_log und schickt
   ausschließlich bei Verstoß einen Admin-Alarm (Exit 1); `Persistent=false`. In `install_timers.sh` eingetragen.
5. **Wächter auf Wirkung** (`scripts/verify_briefing_versand.py`): Abbruch NACH der Annahme (Wiederaufnahme sendet
   den Empfänger nicht erneut, meldet ihn), Ablehnung + Abbruch VOR der Annahme (abgelehnter wird erneut versucht,
   ungeklärter nicht), Journal-Schreibfehler (Lauf endet mit Ausnahme, kein refresh_log, nächster Lauf gesperrt),
   Check 5c über das echte `collect_health_data()` mit Client-Attrappe und fester Uhr (nur Test heute / leer / nur
   Testzeilen nach 10 Uhr → rot; Live heute → grün; leer vor 10 → gelb), `briefing_frist()` mit Alarm-Attrappe in
   fünf Fällen, Fristtimer/-unit/Installer. Windows 57/57 (+2 nur unter Linux), **Linux im Container 59/59**.
   Mutationstest **30/30** (neu u. a.: offen nicht vorab markiert, Ungeklärte erneut versandt, Ablehnung nicht notiert,
   Journalfehler geschluckt, Frist ohne Live-Zeile, Fristprüfung ohne Alarm/vor 10 Uhr, Installer ohne Fristprüfung),
   Gegenproben richtig verworfen, Projektbaum unverändert.

## Ausgabevertrag
**Urteil** (Freigabe / keine Freigabe) · **Befunde** (P1/P2, mit Datei:Zeile) · **Auflagen**. ≤ 20 Zeilen.
