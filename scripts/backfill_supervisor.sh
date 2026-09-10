#!/bin/bash
# backfill_supervisor.sh — bewacht einen langlaufenden Backfill-Container.
#
# WARUM ES DAS GIBT: Ein Skew-Backfill laeuft ueber viele Stunden und
# ueberlappt damit zwangslaeufig mit dem naechtlichen options_skew-Cron.
# Beide schreiben dieselbe options_skew_history.json -- und der Backfill haelt
# sie im Speicher und schreibt nach JEDEM Ticker die ganze Struktur zurueck.
# Alles, was der Cron in der Zwischenzeit anlegt, waere damit verloren
# (Lost Update). Deshalb: kurz vor dem Cron stoppen, danach fortsetzen.
# Ohne --overwrite kostet das fast nichts -- fertige Ticker meldet der Lauf
# beim Neustart als "bereits vollstaendig" und ueberspringt sie.
#
# Zusaetzlich: Zwischenstand per Mail, damit bei einem 18-Stunden-Lauf
# erkennbar bleibt, ob es vorangeht, und am Ende der Abschlussbericht.
#
# START (transiente systemd-Unit, ueberlebt SSH-Abbruch und Entwickler-PC):
#   systemd-run --unit=sa-bfsup --description="Backfill Supervisor" \
#     /bin/bash /opt/seasonaledge/scripts/backfill_supervisor.sh
#   systemctl is-active sa-bfsup.service    # Status
#   tail -f /var/log/sa-backfill-supervisor.log
#
# NICHT `pkill -f backfill_supervisor` zum Beenden benutzen: das Muster steht
# in der eigenen Kommandozeile, der Befehl killt seine eigene Shell mit.
# Stattdessen: systemctl stop sa-bfsup.service
#
# Konfiguration ueber Umgebungsvariablen (Defaults unten).

C=${CONTAINER:-sa-backfill-rest}
LOG=${SUP_LOG:-/var/log/sa-backfill-supervisor.log}
BFLOG=${BF_LOG:-/tmp/sa-backfill.log}
BASELINE=${BASELINE:-}          # Ticker im Radar VOR dem Lauf (Vorher/Nachher)
EVERY=${EVERY:-10800}           # Zwischenstand alle 3 Stunden (Sekunden)
APP_DIR=${APP_DIR:-/opt/seasonaledge}
IMAGE=${IMAGE:-seasonaledge-app}

# Nur der options_skew-Cron (23:00 UTC) kollidiert wirklich -- er schreibt
# dieselbe History. Der GEX-Cron (22:15) schreibt gex_*/key_levels.json und ist
# unkritisch. Der 23:00-Lauf braucht fuer ~163 Ticker rund 40 Minuten, danach
# laufen noch iv_surface + options_flow.
PAUSE_FROM=${PAUSE_FROM:-2250}  # UTC HHMM -- 10 Min vor dem Cron
RESUME_AT=${RESUME_AT:-0010}    # UTC HHMM -- gut eine Stunde nach dessen Start

STARTED=$(date +%s)

log() { echo "$(date -u +'%F %T') $*" >> "$LOG"; }

# HHMM als Dezimalzahl (10# verhindert, dass 0010 als Oktalzahl gelesen wird)
now() { echo $((10#$(date -u +%H%M))); }
in_window() {
  local n
  n=$(now)
  [ "$n" -ge $((10#$PAUSE_FROM)) ] || [ "$n" -lt $((10#$RESUME_AT)) ]
}

# Bericht im Container erzeugen und verschicken. $1 = zusaetzliche Flags.
send_report() {
  docker logs "$C" > "$BFLOG" 2>&1
  docker run --rm \
    -v "$APP_DIR/.env":/app/.env:ro \
    -v "$APP_DIR/landing/data":/app/landing/data \
    -v "$BFLOG":/tmp/bf.log:ro \
    -w /app "$IMAGE" \
    python3 -u scripts/backfill_skew_report.py \
      ${BASELINE:+--baseline "$BASELINE"} --log /tmp/bf.log --started "$STARTED" $1 \
    >> "$LOG" 2>&1
}

LAST_MAIL=$(date +%s)
log "Supervisor gestartet (Container=$C, Pause $PAUSE_FROM-$RESUME_AT UTC, Zwischenstand alle $((EVERY/3600))h)"

while true; do
  RUNNING=$(docker inspect -f '{{.State.Running}}' "$C" 2>/dev/null)

  if [ "$RUNNING" = "true" ]; then
    if in_window; then
      log "Cron-Fenster erreicht -> Backfill pausieren"
      docker stop "$C" >/dev/null 2>&1
      while in_window; do sleep 120; done
      log "Cron-Fenster vorbei -> Backfill fortsetzen"
      docker start "$C" >/dev/null 2>&1
    fi

    NOW_S=$(date +%s)
    if [ $((NOW_S - LAST_MAIL)) -ge "$EVERY" ]; then
      log "Zwischenstand faellig -> Mail"
      send_report --progress
      LAST_MAIL=$NOW_S
    fi

    sleep 60
    continue
  fi

  # Nicht laufend und nicht von uns pausiert -> Lauf ist beendet.
  CODE=$(docker inspect -f '{{.State.ExitCode}}' "$C" 2>/dev/null)
  log "Backfill beendet (exit=$CODE) -> Abschlussbericht"
  send_report
  log "Bericht versendet, Supervisor endet"
  break
done
