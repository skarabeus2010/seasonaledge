#!/bin/bash
# skewfix_status.sh — Statusmail zum laufenden Skew-Backfill, alle 2 Stunden.
#
# Laeuft der Container noch, kommt ein Zwischenstand. Ist er weg, kommt der
# Abschlussbericht UND der Timer schaltet sich selbst ab — sonst mailt er
# ewig weiter.
#
# Der Bericht meldet bewusst NICHT "exit 0", sondern wie viele Ticker im Radar
# erscheinen: ein Lauf kann sauber durchlaufen und trotzdem kaum Abdeckung
# bringen. Genau das ist beim Lauf vom 2026-09-11 passiert (siehe docs/OPTIONS.md).
#
# EINRICHTUNG auf dem Server (die Units liegen ausserhalb des Repos):
#
#   cat > /etc/systemd/system/sa-skewfix-status.service <<'EOF'
#   [Unit]
#   Description=Statusmail zum Skew-Backfill
#   [Service]
#   Type=oneshot
#   ExecStart=/opt/seasonaledge/scripts/skewfix_status.sh
#   EOF
#
#   cat > /etc/systemd/system/sa-skewfix-status.timer <<'EOF'
#   [Unit]
#   Description=Statusmail zum Skew-Backfill alle 2 Stunden
#   [Timer]
#   OnBootSec=10min
#   OnUnitActiveSec=2h
#   AccuracySec=1min
#   Unit=sa-skewfix-status.service
#   [Install]
#   WantedBy=timers.target
#   EOF
#
#   systemctl daemon-reload && systemctl enable --now sa-skewfix-status.timer
#
# Warum systemd und nicht cron: der Timer ueberlebt Reboots und laesst sich vom
# Skript selbst abschalten, wenn der Lauf durch ist.
set -uo pipefail
LOG=/app/logs/skewfix.log
cd /opt/seasonaledge || exit 1

if docker ps --format "{{.Names}}" | grep -qx sa-skewfix; then
    docker exec seasonalpha-app python3 scripts/backfill_skew_report.py \
        --progress --log "$LOG" 2>&1 | grep -v WARNING
else
    docker exec seasonalpha-app python3 scripts/backfill_skew_report.py \
        --log "$LOG" 2>&1 | grep -v WARNING
    systemctl stop  sa-skewfix-status.timer 2>/dev/null
    systemctl disable sa-skewfix-status.timer 2>/dev/null
    echo "[status] Container weg -> Abschlussbericht gesendet, Timer abgeschaltet."
fi
