# Review-Auftrag Runde 1: Stündliche Jobs auf systemd-Timer — CODE

Repo `C:\dev\Seasonaledge`. Du hast den Entwurf geprüft (`docs/review_prompts/2026-09-29_intraday_timer_entwurf.md`,
FREIGABE nein, 7 Befunde). Jetzt liegt Code vor. Antworte auf Deutsch, je Befund Schwere + Datei:Zeile +
konkrete Änderung. Am Ende genau eine Zeile `FREIGABE: ja` oder `FREIGABE: nein`.

Geänderte/neue Dateien (siehe `git status` / `git diff`):
- `scripts/intraday_refresh.py`, `scripts/polymarket_refresh.py`, `scripts/daily_health_check.py`
- `deploy/systemd/sa-intraday.{service,timer}`, `deploy/systemd/sa-polymarket-intraday.{service,timer}`,
  `deploy/systemd/warte_auf_app.sh`, `deploy/install_timers.sh`, `.github/workflows/deploy.yml`
- Schritt 2 (noch NICHT im Arbeitsbaum, wird erst nach Nachweis eines Timer-Laufs committet):
  die beiden Workflows werden zu reinen Notauslösern, Inhalt unten.

## Umgang mit deinen 7 Befunden

1. **Timeout im Container:** `docker exec seasonalpha-app timeout --kill-after=30s 8m python3 -u …`,
   außen `TimeoutStartSec=10min`. `timeout` ist im Image (`/usr/bin/timeout`, coreutils 9.7).
   **Nachweis auf dem Server** (transiente Unit, `TimeoutStartSec=3s`, innen `timeout --kill-after=2s 10s python3 -c sleep(100)`):
   nach dem systemd-Abbruch liefen `timeout` + Python im Container weiter (dein Befund bestätigt),
   nach 15 s war kein Prozess mehr da.
2. **Health-Check:** Intraday: grün ≥20, gelb 12–19, rot <12 an JEDEM Wochentag (Krypto-Gruppe 24/7 →
   jeder Lauf schreibt eine Zeile); zusätzlich rot, wenn der letzte Lauf >2,5 h alt ist; gelb bei ≥3 Läufen
   mit ausgefallenen Tickern (`bewerte_intraday`). Polymarket: das Skript schreibt im `--near-fomc-only`-Modus
   IMMER eine `refresh_log`-Zeile `run_type='polymarket_intraday'` (auch den Skip); neuer Check 6c rot, wenn
   die letzte älter als 2,5 h ist oder keine existiert. `run_type` ist Freitext; alle anderen Leser filtern auf ihren eigenen Typ.
   **Grenze, bewusst:** der Health-Check selbst ist ein GitHub-Cron (täglich, verspätet, aber bisher vollständig). Er sieht
   einen ausgefallenen Timer spätestens am nächsten Morgen. Kein separater Alarm auf dem Host (würde eine
   zweite Mail-Strecke brauchen) — bewerte, ob das für stündliche Kurs-Snapshots vertretbar ist.
3. **Fehler als Fehler:** intraday: leerer Download und DB-Schreibfehler zählen nicht mehr als Erfolg;
   Exit 1, wenn `refresh_log` nicht geschrieben wurde oder `fehlschlag(total, fehler)` = mehr als max(2, total//10)
   Ticker ausfallen; Exit 2 bei unbekannter `--group`. Die `refresh_log`-Zeile wird VOR der Exit-Entscheidung
   geschrieben, der Health-Check sieht also auch gescheiterte Läufe. Polymarket: Exception in Abruf/Upsert
   wird gefangen und als Fehler gezählt; Exit 1, wenn kein Snapshot geschrieben wurde oder das Log scheitert.
   Einzelne Märkte ohne Preis bleiben Exit 0 (Dauerzustand, z. B. nicht im Katalog).
4. **Deploy-Kollision:** `Requires/After=docker.service`; `ExecStartPre` = `warte_auf_app.sh` (max. 2 min
   warten, bis der Container läuft UND `docker exec … true` geht, sonst Exit 1). Keine automatischen
   Wiederholungen: ein verlorener Stundenslot ist akzeptiert, der Health-Check toleriert ihn (≥20 von 24,
   Alter ≤2,5 h).
5. **Idempotenz/Notauslöser:** Die Behauptung „beide idempotent" ist gestrichen. Notauslöser starten dieselbe
   Unit (`systemctl start`) mit weitergereichtem Exit-Code. Parallelbetrieb in Schritt 1 (GitHub-Cron + Timer)
   dauert nur bis zum Nachweis; Polymarket ist heute außerhalb des FOMC-Fensters (nur Skips), Intraday-Upsert
   auf `ticker,date` mit Minuten Abstand.
6. **Installation im Deploy:** `deploy/install_timers.sh` (`set -euo pipefail`): `systemd-analyze verify` +
   `calendar` VOR dem Kopieren, nur geänderte Dateien kopieren, `daemon-reload` nur bei Änderung, `enable`,
   geänderte Timer `restart`, sonst `start`; Nachweis je Timer `is-enabled`/`is-active`/`NextElapseUSecRealtime`.
   Im Deploy am Ende mit `if ! …; then exit 1`. `verify` auf dem Server geprüft: rc 0, systemd 255,
   `*-*-* *:17:00 UTC` normalisiert korrekt. Laufende Services werden nicht neu gestartet.
7. **Kalender/Journal:** `OnCalendar=… UTC`, `python3 -u`, `Persistent=false`, kein `RemainAfterExit`.
   Journal ist persistent (3,9 GB, Default-Limits; unsere Ausgabe ist ~30 Zeilen/Lauf).

## Tests
Lokaler Test `bewerte_intraday` (11 Fälle inkl. „4 Runs" = heutige Mail → rot, „letzter Lauf 3 h alt" → rot,
`Z`-Zeitstempel) und `fehlschlag` (6 Grenzfälle): alle wie erwartet.

## Schritt 2 (Inhalt der beiden Workflows nach dem Umstieg)
```yaml
name: Intraday Price Update

# Kurs-Update fuer die gerade offenen Boersen (scripts/intraday_refresh.py).
# Der Zeitplan liegt seit 2026-09-29 auf dem VPS als systemd-Timer
# (deploy/systemd/sa-intraday.timer), weil GitHub die stuendlichen
# Crons seit 2026-08-26 nur noch 4-8x pro Tag startete. Dieser Workflow ist nur
# noch der manuelle Notausloeser. Er startet DIESELBE Unit: laeuft gerade ein
# Timer-Lauf, wartet systemctl auf dessen Ende statt einen zweiten zu starten.

on:
  workflow_dispatch:

jobs:
  run:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - name: sa-intraday.service auf dem VPS starten
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.VPS_HOST }}
          username: root
          key: ${{ secrets.VPS_SSH_KEY }}
          command_timeout: 13m
          script: |
            rc=0
            systemctl start sa-intraday.service || rc=$?
            journalctl -u sa-intraday.service -n 30 --no-pager
            exit $rc
```

`polymarket_intraday.yml` identisch aufgebaut mit `sa-polymarket-intraday.service`.

## Prüfe besonders
- Stimmt die Aussage, dass `systemctl start` auf eine gerade laufende oneshot-Unit auf deren Ende wartet
  und keinen zweiten Lauf startet?
- `install_timers.sh`: Fehlerpfade, `set -u` mit leerem Array `geaendert_timer`, Verhalten beim allerersten Lauf.
- Verdeckt irgendein Pfad weiterhin einen Fehler (Exit 0 trotz Ausfall)?
- Regressionen im täglichen Polymarket-Lauf (`polymarket_daily.yml` ruft dasselbe Skript ohne `--near-fomc-only`).
