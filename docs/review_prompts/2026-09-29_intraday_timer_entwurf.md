# Review-Auftrag: Stündliche Jobs vom GitHub-Cron auf systemd-Timer (ENTWURF, noch kein Code)

Du prüfst einen **Entwurf**, bevor Code geschrieben wird. Repo: `C:\dev\Seasonaledge`.
Antworte auf Deutsch. Am Ende genau eine Zeile `FREIGABE: ja` oder `FREIGABE: nein`.

## Befund (gemessen, 2026-09-29)

- `.github/workflows/intraday_update.yml` (Cron `17 * * * *`) und
  `.github/workflows/polymarket_intraday.yml` (Cron `23 * * * *`) tun nur eines:
  per `appleboy/ssh-action` auf den VPS und `docker exec seasonalpha-app python3 <skript>`.
- GitHub führt sie seit **2026-08-26** nur noch 4–8× pro Tag aus statt 23–24×
  (bis 25.08.: 22–23/Tag; 26.08.: 16; seitdem 2–8). Workflow-Datei seit April unverändert.
  Alle ausgeführten Läufe `success`. Tägliche Workflows laufen vollständig, aber 2–4 h verspätet.
- `scripts/daily_health_check.py` Check 6b zählt `refresh_log` mit `run_type='intraday'`
  der letzten 24 h: werktags ≥10 grün, 5–9 gelb, <5 rot. Heute 4 → Mail rot.
- `scripts/intraday_refresh.py`: entscheidet selbst anhand der UTC-Uhrzeit, welche Gruppen
  aktiv sind (Krypto immer) und schreibt pro Lauf eine `refresh_log`-Zeile.
  Laufzeit 2,4–102 s (größter Lauf 363 Ticker).
- `scripts/polymarket_refresh.py --near-fomc-only`: beendet sich sauber außerhalb des FOMC-Fensters.
- Server: Ubuntu, Zeitzone UTC, systemd. Root-Crontab enthält bereits
  `30 20 * * * docker exec seasonalpha-app python3 scripts/nightly_refresh.py >> /var/log/seasonalpha-refresh.log 2>&1`
  sowie einen zweimonatlichen Zentralbank-Job. Es gibt schon eigene Units (`sa-skewfix-status.*`).
- Deploy (`.github/workflows/deploy.yml`): `git pull`, dann `docker compose up -d --build`
  → der App-Container wird bei jedem Push neu erstellt; ein `docker exec` in diesem Moment scheitert.

## Entwurf

1. **Units im Repo** unter `deploy/systemd/`:
   - `sa-intraday.service` — `Type=oneshot`,
     `ExecStart=/usr/bin/docker exec seasonalpha-app python3 scripts/intraday_refresh.py`,
     `TimeoutStartSec=10min`, Ausgabe ins Journal.
   - `sa-intraday.timer` — `OnCalendar=*-*-* *:17:00`, `Persistent=false`, `AccuracySec=1min`.
   - `sa-polymarket-intraday.service` / `.timer` analog mit `--near-fomc-only` und `*:23:00`.
   - Keine Überlappung desselben Jobs: ein oneshot-Service, der noch aktiv ist, wird vom Timer nicht erneut gestartet.
2. **Installationsskript** `deploy/install_timers.sh` (idempotent): Units nach
   `/etc/systemd/system/` kopieren, `systemctl daemon-reload`, `enable --now` beider Timer,
   Ausgabe von `systemctl list-timers sa-*`. Einmal manuell per SSH ausführen.
   Offene Frage: zusätzlich im Deploy aufrufen, damit geänderte Units nicht driften?
3. **GitHub-Workflows:** `schedule:` entfernen, `workflow_dispatch:` behalten (manueller Notauslöser).
   Reihenfolge: erst Timer auf dem Server aktiv und ein Lauf in `refresh_log` gesehen,
   dann Schedule entfernen (sonst Lücke; kurzzeitig doppelte Läufe sind harmlos,
   beide Skripte sind idempotent — Upsert der Kurse).
4. **Health-Check unverändert** — er misst bereits das Richtige (`refresh_log`),
   und nach dem Umzug sollten wieder ≥20 Läufe pro Werktag ankommen.
5. **Doku:** CLAUDE.md-Deployment-Regel + TODO, kurzer Abschnitt in `docs/REFRESH_MONITORING.md`.

## Bewusst NICHT im Umfang (bitte nur bewerten, nicht einfordern)

- Nightly Refresh läuft **doppelt**: Server-Crontab 20:30 UTC **und** GitHub-Workflow
  `nightly_refresh.yml` (Cron `30 20 * * 1-5` / `30 17 * * 0`, real 23:00–00:30).
  `refresh_log` zeigt je Tag zwei `nightly`-Zeilen, am 27.09. um 20:34 und 20:39 überlappend.
  Soll dem Nutzer als separater Befund gemeldet werden.
- Andere tägliche GitHub-Crons (verspätet, aber vollständig).

## Deine Prüfaufgaben

1. Ist systemd-Timer + `docker exec` auf dem Host der richtige Mechanismus, oder gibt es
   ein Risiko, das ich übersehe (Container-Neustart während Deploy, Zombie-`docker exec`,
   Journal-Wachstum, Timeout, Zeitumstellung — Server ist UTC)?
2. Fehlt etwas, damit ein Ausfall des Timers **sich als Fehler meldet** statt still zu verschwinden?
   (Health-Check zählt `refresh_log` — reicht das? Was, wenn der Timer nach Reboot nicht aktiv ist?)
3. Units im Repo + manuelles Installskript vs. Aufruf im Deploy: was ist robuster?
4. Die Reihenfolge des Umstiegs (Punkt 3).
5. Alles andere, was am Entwurf nicht trägt.

Nenne je Befund Schwere (HOCH/MITTEL/NIEDRIG), Begründung, konkrete Änderung.
