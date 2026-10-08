#!/usr/bin/env bash
# Bindet den Arbeitsbaum an GENAU den Commit, den dieser Deploy-Lauf geprueft hat.
#
# WICHTIG: dieses Skript holt NICHT selbst. Das Holen passiert im Workflow, denn
# erst danach liegt dieses Skript in der geprueften Fassung vor (es wird mit
# `git show "$SA_SHA:deploy/pruefe_commit.sh"` aus dem geholten Commit gezogen).
# Zwei Gruende dafuer, beide von Codex gefunden:
#   * Beim ERSTEN Lauf nach Einfuehrung existiert die Datei auf dem Serverstand
#     noch nicht — ein Aufruf aus dem Arbeitsbaum haette den Deploy blockiert und
#     damit verhindert, dass sich der neue Stand selbst installiert.
#   * Danach liefe die Fassung des SERVERS, waehrend das Gate auf dem Runner die
#     neue Fassung geprueft hat. Zwei verschiedene Dateien, ein Urteil.
#
# Das Zeitfenster, um das es ueberhaupt geht: `landing/` ist per Bind-Mount live
# nach nginx gebunden, `/polymarket` wird direkt daraus ausgeliefert. Jede
# Aenderung am Arbeitsbaum ist damit SOFORT oeffentlich, und ein Abbruch danach
# nimmt nichts zurueck. Deshalb wird verglichen, BEVOR etwas angefasst wird, und
# dann auf die feste Kennung vorgespult statt erneut zu pullen (ein zweiter Pull
# geht wieder ins Netz und kann einen inzwischen gepushten Commit holen).
#
# Was dieses Skript NICHT leistet, und das steht hier, damit es niemand annimmt:
# das Aktualisieren eines live gebundenen Verzeichnisses ist keine atomare
# Veroeffentlichung. Zwischen einzelnen Dateiaenderungen kann ein Mischstand
# sichtbar sein. Dagegen hilft nur ein Wechsel des ausgelieferten Verzeichnisses,
# und das ist eine eigene Entscheidung.
#
# Erwartet: SA_SHA gesetzt, `git fetch` bereits gelaufen, Arbeitsverzeichnis = Repo.
# Exit 0 = Arbeitsbaum steht auf SA_SHA. Exit 1 = nichts Ungepruefte sichtbar.
set -euo pipefail

: "${SA_SHA?Uebertragung fehlgeschlagen: SA_SHA fehlt}"

# Betriebsart `--nur-vergleich`: prueft die Kennung und endet, ohne den
# Arbeitsbaum anzufassen. Sie laeuft VOR den Reverts, damit ein Abbruch die live
# gebundene Seite nicht mit Platzhaltern zurueckliess (Codex, Abnahme
# 2026-10-08). Der zweite Aufruf ohne Schalter spult dann vor.
NUR_VERGLEICH=0
if [ "${1:-}" = "--nur-vergleich" ]; then
  NUR_VERGLEICH=1
fi

# `origin/master` ist eine LOKALE Referenz, die der vorangegangene fetch
# aktualisiert hat — kein Netzzugriff, also kein neues Zeitfenster.
if ! FERN=$(git rev-parse origin/master 2>/dev/null); then
  echo "::error::origin/master nicht lesbar — lief der fetch?"
  exit 1
fi

if [ "$FERN" != "$SA_SHA" ]; then
  echo "::error::Dieser Lauf hat $SA_SHA geprueft, auf master liegt $FERN."
  echo "Waehrend des Laufs wurde gepusht. Abbruch VOR jeder Aenderung am"
  echo "Arbeitsbaum, damit kein ungepruefter Stand sichtbar wird. Der Lauf des"
  echo "neueren Commits prueft und rollt ihn selbst aus — es geht keine"
  echo "Auslieferung verloren. Ein Lauf, der hier rot wird, ist deshalb kein"
  echo "Fehler, sondern der ueberholte Vorgaenger."
  exit 1
fi

if [ "$NUR_VERGLEICH" = "1" ]; then
  echo "[deploy] Kennung geprueft: origin/master == $SA_SHA. Baum unangetastet."
  exit 0
fi

# --ff-only: ein Merge-Commit auf dem Server waere ein Stand, den niemand
# geprueft hat. Scheitert, wenn eine lokale Aenderung blockiert, wenn das Objekt
# fehlt, oder wenn der Serverstand von der Zielkennung abweicht.
# KEIN Scheiterngrund (Codex-Korrektur, Runde 5): ein force-push auf dem Remote
# NACH dem Fetch. Das Objekt liegt dann lokal und bleibt mergebar — blosse
# Unerreichbarkeit vom Remote-Branch macht es nicht unmergebar.
if ! git merge --ff-only "$SA_SHA"; then
  echo "::error::Vorspulen auf $SA_SHA fehlgeschlagen — Server bleibt auf" \
       "$(git rev-parse --short HEAD)."
  echo "Moegliche Gruende: eine lokale Aenderung blockiert, das Objekt fehlt,"
  echo "oder der Serverstand weicht von der Zielkennung ab."
  echo "Blockierende Dateien ausserhalb von landing/ und seo/output/:"
  git status --porcelain | grep -v '^??' | grep -vE ' (landing|seo/output)/' || true
  echo "Aufloesen: auf dem Server pruefen (git diff <datei>), dann"
  echo "  git checkout -- <datei>   (nur wenn die Aenderung verzichtbar ist)"
  exit 1
fi

IST=$(git rev-parse HEAD)
if [ "$IST" != "$SA_SHA" ]; then
  echo "::error::Nach dem Vorspulen steht der Server auf $IST, geprueft war $SA_SHA."
  exit 1
fi

# Die Kennung allein beweist NICHT, dass der Quellbaum dem Commit entspricht:
# eine lokale Aenderung, die mit dem Vorspulen nicht kollidiert, ueberlebt es
# unbemerkt. Danach laeuft Code, den kein Gate gesehen hat (Codex, Abnahme
# 2026-10-08). Deshalb wird hier auf Sauberkeit geprueft.
#
# Erlaubt bleibt GENAU eine Datei: deploy/nginx.conf. Der Server wird mit einem
# zweiten Projekt geteilt, und Aenderungen daran sollen den Deploy bewusst
# ueberleben (siehe CLAUDE.md). Alles andere ist ein Abbruchgrund.
# landing/ und seo/output/ sind an dieser Stelle zurueckgesetzt; die
# In-Place-Aenderungen von inject_credentials.sh kommen erst DANACH.
# Erst die Ausgabe holen UND den Exit-Code dieses Aufrufs pruefen. Vorher hing
# ein `|| true` an der ganzen Pipeline — nur damit grep ohne Treffer nicht rot
# wird. Scheiterte dabei `git status` selbst (Exit 128), kam eine leere Ausgabe
# heraus und das Skript bestaetigte einen "sauberen" Baum, den es nie gesehen
# hat (Codex, Abnahme Runde 2). Ein Pruefer, der seinen eigenen Fehlschlag als
# Bestanden meldet, ist keiner.
if ! STATUS_ROH=$(git status --porcelain -- .); then
  echo "::error::\`git status\` fehlgeschlagen — die Sauberkeit des Arbeitsbaums"
  echo "ist damit UNGEPRUEFT, und ungeprueft ist nicht bestanden."
  exit 1
fi
# grep ohne Treffer liefert 1; nur DIESER Fall wird abgefangen, nicht der
# Fehlschlag von git.
SCHMUTZ=$(printf '%s\n' "$STATUS_ROH" \
          | grep -v '^??' \
          | grep -v ' deploy/nginx\.conf$' || true)
if [ -n "$SCHMUTZ" ]; then
  echo "::error::Der Quellbaum weicht vom geprueften Commit $SA_SHA ab."
  echo "Die Kennung stimmt, der Inhalt nicht — es wuerde ungepruefter Code laufen."
  echo "$SCHMUTZ"
  echo "Aufloesen: auf dem Server pruefen (git diff <datei>), dann"
  echo "  git checkout -- <datei>   (nur wenn die Aenderung verzichtbar ist)"
  exit 1
fi

echo "[deploy] Arbeitsbaum auf dem geprueften Commit $SA_SHA."
