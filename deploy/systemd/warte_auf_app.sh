#!/bin/bash
# Wartet begrenzt (max. 2 min), bis der App-Container laeuft und Befehle annimmt.
# Hintergrund: der Deploy ersetzt den Container per `docker compose up -d --build`;
# faellt ein Timer-Lauf in dieses Fenster, soll er warten statt sofort scheitern.
# Laeuft der Container danach immer noch nicht, scheitert der Lauf sichtbar
# (Exit 1 -> Service failed, im Journal und in `systemctl --failed`).
for _ in $(seq 1 24); do
  if [ "$(docker inspect -f '{{.State.Running}}' seasonalpha-app 2>/dev/null)" = "true" ] \
     && docker exec seasonalpha-app true 2>/dev/null; then
    exit 0
  fi
  sleep 5
done
echo "seasonalpha-app laeuft nicht oder nimmt keine Befehle an (2 min gewartet)" >&2
exit 1
