#!/bin/bash
# skew_repair_runner.sh — Reparatur-Backfill der Skew-Historie in Batches.
#
# WARUM NICHT backfill_supervisor.sh: der bewacht EINEN langen Lauf und stoppt
# ihn im Cron-Fenster. Das funktioniert nur OHNE --overwrite, weil der
# Neustart fertige Ticker ueberspringen muss. Dieser Lauf braucht aber
# --overwrite: die bestehenden Rekonstruktionen stammen aus der Zeit vor der
# Skew-Reparatur vom 2026-09-11 (Volumenfilter als falsches Kriterium,
# selbstreferenzielles Delta, angepasste Optionsserien) und muessen weg. Der
# Purge in run_ticker laeuft PRO TICKER beim Start dieses Tickers — nach jeder
# Nachtpause wuerde der Supervisor fertige Ticker also erneut leeren und neu
# rechnen. Endlosschleife.
#
# WARUM NICHT ALLES VORAB LEEREN: dann waere der Radar fuer die ganze Laufzeit
# leer. Die normierten Punkte stammen fast alle aus dem Backfill; die
# Live-Punkte laufen erst seit dem 2026-09-11, das sind keine 20 je Ticker
# (MIN_NORM). Gemessen vor dem Start: 37 Ticker im Radar, 2387 Backfill-Punkte
# gegen 3867 sonstige.
#
# DESHALB BATCHWEISE: jeder Batch leert und rechnet nur seine eigenen Ticker
# neu. Die noch nicht bearbeiteten behalten ihre Punkte und bleiben im Radar,
# der Bestand wird also schrittweise ersetzt statt erst zerstoert.
#
# Ein Batch wird nur gestartet, wenn er VOR dem Cron-Fenster fertig werden
# kann. Damit wird nie mitten im Schreiben gestoppt — der Grund fuer das
# Lost-Update-Risiko entfaellt, statt ihn zu bewachen.
#
# START (transiente systemd-Unit, ueberlebt SSH-Abbruch und Entwickler-PC):
#   systemd-run --unit=sa-skewrep --description="Skew-Reparatur" \
#     /bin/bash /opt/seasonaledge/scripts/skew_repair_runner.sh
#   systemctl is-active sa-skewrep.service
#   tail -f /var/log/sa-skew-repair.log
#
# BEENDEN: systemctl stop sa-skewrep.service
# NICHT `pkill -f skew_repair_runner` — das Muster steht in der eigenen
# Kommandozeile, der Befehl killt seine eigene Shell mit.
set -uo pipefail

APP_DIR=${APP_DIR:-/opt/seasonaledge}
LOG=${RUN_LOG:-/var/log/sa-skew-repair.log}
STATE=${STATE:-/var/lib/sa-skew-repair.state}
IMAGE=${IMAGE:-seasonaledge-app}
CONT=${CONT:-sa-skewrep-batch}
JAHRE=${JAHRE:-1}
BATCH=${BATCH:-6}               # Ticker je Batch. Klein gehalten: SPY allein
                                # brauchte 50 Minuten (9038 Bars). Ein grosser
                                # Batch wuerde staendig am Fenster abgebrochen
                                # und komplett wiederholt.
MIN_MINUTEN=${MIN_MINUTEN:-240} # so viel Zeit muss bis zum Fenster bleiben.
                                # Grob BATCH x 40 Min plus Puffer — lieber warten
                                # als einen Batch anreissen, der abgebrochen wird.
MAIL_ALLE=${MAIL_ALLE:-4}       # Zwischenstand per Mail alle N Batches
PAUSE_FROM=${PAUSE_FROM:-2250}  # UTC HHMM, 10 Min vor dem options_skew-Cron
RESUME_AT=${RESUME_AT:-0010}

log() { echo "[$(date -u +%F' '%T)] $*" >> "$LOG"; }

# Zwischenstand/Abschluss per Mail. Ohne das laeuft ein Lauf ueber mehrere
# Naechte blind durch, und man erfaehrt erst am Ende, ob ueberhaupt etwas
# vorangeht — oder ob er seit Stunden im Kreis laeuft.
# Der Bericht meldet bewusst NICHT "exit 0", sondern wie viele Ticker im Radar
# erscheinen: ein Lauf kann sauber durchlaufen und trotzdem kaum Abdeckung
# bringen. Genau das ist am 2026-09-11 passiert (siehe docs/OPTIONS.md).
bericht() {
  docker run --rm \
    -v "$APP_DIR/.env":/app/.env:ro \
    -v "$APP_DIR/landing/data":/app/landing/data \
    -v "$LOG":/tmp/bf.log:ro \
    -w /app "$IMAGE" \
    python3 -u scripts/backfill_skew_report.py --log /tmp/bf.log \
      ${BASELINE:+--baseline "$BASELINE"} ${1:-} >> "$LOG" 2>&1
}

# 10# verhindert, dass 0010 als Oktalzahl gelesen wird.
now_hhmm() { echo $((10#$(date -u +%H%M))); }
im_fenster() {
  local n; n=$(now_hhmm)
  [ "$n" -ge $((10#$PAUSE_FROM)) ] || [ "$n" -lt $((10#$RESUME_AT)) ]
}
# Minuten bis zum Beginn des Fensters (grob, reicht fuer die Entscheidung).
minuten_bis_fenster() {
  local n p; n=$(now_hhmm); p=$((10#$PAUSE_FROM))
  if [ "$n" -ge "$p" ]; then echo 0; return; fi
  echo $(( (p/100*60 + p%100) - (n/100*60 + n%100) ))
}

cd "$APP_DIR" || exit 1
mkdir -p "$(dirname "$STATE")"

# Ticker-Liste aus dem Universum, NICHT aus der History: symbols.py und
# options_universe.py sind die Quelle der Wahrheit (CLAUDE.md).
mapfile -t ALLE < <(docker exec seasonalpha-app python3 -c "
import sys; sys.path.insert(0,'/app')
from shared.options_universe import all_option_tickers
for t in all_option_tickers(): print(t)
" 2>/dev/null | grep -v WARNING | tr -d '\r')

if [ "${#ALLE[@]}" -eq 0 ]; then
    log "FEHLER: keine Ticker aus dem Universum bekommen -> Abbruch"
    exit 1
fi

# Fortschritt: welche Ticker sind fertig? Ueberlebt Reboot und Neustart.
touch "$STATE"
log "Start: ${#ALLE[@]} Ticker im Universum, Batch=$BATCH, Jahre=$JAHRE"
log "bereits fertig laut $STATE: $(wc -l < "$STATE")"

OFFEN=()
for t in "${ALLE[@]}"; do
    grep -qxF "$t" "$STATE" || OFFEN+=("$t")
done
log "offen: ${#OFFEN[@]}"

I=0
FERTIG=0
while [ "$I" -lt "${#OFFEN[@]}" ]; do
    # Im Fenster gar nicht erst anfangen.
    while im_fenster; do
        log "Cron-Fenster aktiv -> warten"
        sleep 300
    done
    REST=$(minuten_bis_fenster)
    if [ "$REST" -lt "$MIN_MINUTEN" ]; then
        log "nur $REST Min bis zum Fenster (mind. $MIN_MINUTEN) -> warten, statt einen Batch anzureissen"
        sleep 600
        continue
    fi

    STAPEL=("${OFFEN[@]:$I:$BATCH}")
    log "Batch $((I/BATCH+1)): ${STAPEL[*]}  ($REST Min bis zum Fenster)"

    docker rm -f "$CONT" >/dev/null 2>&1
    # --overwrite: die alten Rekonstruktionen dieser Ticker muessen weg, nicht
    # nur ueberschrieben werden. Sonst ueberleben genau die Tage, die der neue
    # Lauf nicht reproduzieren kann.
    #
    # ABGESETZT (-d) und selbst bewacht, statt im Vordergrund: ein Batch kann
    # laenger dauern als geschaetzt (SPY allein brauchte 50 Minuten bei 9038
    # Bars), und dann liefe er ins Cron-Fenster. Der options_skew-Cron schreibt
    # dieselbe History, und der Backfill haelt sie im Speicher und schreibt
    # nach JEDEM Ticker die ganze Struktur zurueck — was der Cron dazwischen
    # anlegt, waere verloren (Lost Update). Deshalb wird der Container am
    # Fenster hart gestoppt. Die Ticker dieses Batches bleiben dann offen und
    # werden spaeter komplett wiederholt: das kostet Rechenzeit, aber keine
    # Daten, weil der Purge pro Ticker laeuft und ein abgebrochener Ticker
    # beim naechsten Anlauf ohnehin neu gerechnet wird.
    docker run -d --name "$CONT" \
         --env-file "$APP_DIR/.env" \
         -v "$APP_DIR/landing/data":/app/landing/data \
         -w /app "$IMAGE" \
         python3 -u scripts/backfill_skew_massive.py \
           --symbols "${STAPEL[@]}" --years "$JAHRE" --overwrite \
         >/dev/null 2>&1

    ABGEBROCHEN=0
    while [ "$(docker inspect -f '{{.State.Running}}' "$CONT" 2>/dev/null)" = "true" ]; do
        if im_fenster; then
            log "Cron-Fenster erreicht, Batch laeuft noch -> harter Stopp"
            docker stop "$CONT" >/dev/null 2>&1
            ABGEBROCHEN=1
            break
        fi
        sleep 60
    done

    docker logs "$CONT" >> "$LOG" 2>&1
    CODE=$(docker inspect -f '{{.State.ExitCode}}' "$CONT" 2>/dev/null)

    if [ "$ABGEBROCHEN" = "1" ]; then
        log "Batch am Fenster abgebrochen -> ${#STAPEL[@]} Ticker bleiben offen"
        # I NICHT weiterzaehlen: derselbe Stapel wird nach dem Fenster wiederholt.
    elif [ "$CODE" = "0" ]; then
        for t in "${STAPEL[@]}"; do echo "$t" >> "$STATE"; done
        FERTIG=$((FERTIG+1))
        log "Batch fertig, $((${#OFFEN[@]}-I-${#STAPEL[@]})) Ticker offen"
        if [ $((FERTIG % MAIL_ALLE)) -eq 0 ]; then
            log "Zwischenstand faellig -> Mail"
            bericht --progress
        fi
        I=$((I+BATCH))
    else
        log "Batch FEHLGESCHLAGEN (exit=$CODE) -> Ticker bleiben offen, weiter mit dem naechsten"
        I=$((I+BATCH))
        sleep 60
    fi
    docker rm -f "$CONT" >/dev/null 2>&1
done

log "ALLE BATCHES DURCH -> Abschlussbericht"
bericht
log "Bericht versendet, Runner endet"
