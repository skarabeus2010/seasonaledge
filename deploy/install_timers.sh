#!/bin/bash
# Installiert/aktualisiert die systemd-Timer der stuendlichen Jobs (idempotent).
# Laeuft im Deploy (.github/workflows/deploy.yml) und darf manuell wiederholt werden:
#   bash /opt/seasonaledge/deploy/install_timers.sh
#
# Fasst NUR die hier gelisteten Units an. Ein laufender Job wird nicht
# unterbrochen: geaenderte Service-Units greifen ab dem naechsten Start,
# geaenderte Timer werden neu gestartet (startet keinen Job).
set -euo pipefail

SRC="$(cd "$(dirname "$0")" && pwd)/systemd"
DST=/etc/systemd/system
SERVICES=(sa-intraday.service sa-polymarket-intraday.service)
TIMERS=(sa-intraday.timer sa-polymarket-intraday.timer)

fehler() { echo "install_timers: FEHLER: $*" >&2; exit 1; }

# 1) Vor dem Kopieren pruefen, ob systemd die Dateien akzeptiert.
for u in "${SERVICES[@]}" "${TIMERS[@]}"; do
  [ -f "$SRC/$u" ] || fehler "$SRC/$u fehlt"
done
systemd-analyze verify "${SERVICES[@]/#/$SRC/}" "${TIMERS[@]/#/$SRC/}" \
  || fehler "systemd-analyze verify meldet Fehler"
for t in "${TIMERS[@]}"; do
  cal=$(sed -n 's/^OnCalendar=//p' "$SRC/$t")
  systemd-analyze calendar "$cal" >/dev/null || fehler "$t: OnCalendar '$cal' ungueltig"
done

# 2) Nur geaenderte Dateien kopieren.
geaendert_timer=()
geaendert=0
for u in "${SERVICES[@]}" "${TIMERS[@]}"; do
  if ! cmp -s "$SRC/$u" "$DST/$u"; then
    install -m 0644 "$SRC/$u" "$DST/$u"
    echo "install_timers: $u aktualisiert"
    geaendert=1
    case "$u" in *.timer) geaendert_timer+=("$u") ;; esac
  fi
done
[ "$geaendert" = 1 ] && systemctl daemon-reload

# 3) Aktivieren und laufen lassen; geaenderte Timer neu starten.
for t in "${TIMERS[@]}"; do
  systemctl enable "$t" >/dev/null 2>&1 || fehler "enable $t"
  if printf '%s\n' "${geaendert_timer[@]:-}" | grep -qx "$t"; then
    systemctl restart "$t" || fehler "restart $t"
  else
    systemctl start "$t" || fehler "start $t"
  fi
done

# 4) Nachweis statt Anzeige: jeder Timer aktiviert, aktiv, mit naechstem Termin.
for t in "${TIMERS[@]}"; do
  [ "$(systemctl is-enabled "$t")" = enabled ] || fehler "$t nicht enabled"
  [ "$(systemctl is-active "$t")" = active ]   || fehler "$t nicht active"
  sub=$(systemctl show -p SubState --value "$t")
  if [ "$sub" = running ]; then
    # Der Timer loest gerade seinen Job aus; systemd setzt den naechsten Termin
    # erst nach dessen Ende (NextElapse = unendlich). Das ist gesund, sofern der
    # zugehoerige Service tatsaechlich laeuft.
    svc=$(systemctl show -p Unit --value "$t")
    [ "$(systemctl is-active "$svc" || true)" = activating ] \
      || fehler "$t im Zustand running, aber $svc laeuft nicht"
    echo "install_timers: $t ok, $svc laeuft gerade"
    continue
  fi
  [ "$sub" = waiting ] || fehler "$t in unerwartetem Zustand '$sub'"
  naechst=$(systemctl show -p NextElapseUSecRealtime --value "$t")
  [ -n "$naechst" ] && [ "$naechst" != "n/a" ] || fehler "$t ohne naechsten Termin"
  echo "install_timers: $t ok, naechster Lauf $naechst"
done
