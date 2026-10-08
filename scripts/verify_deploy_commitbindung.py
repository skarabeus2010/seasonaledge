# -*- coding: utf-8 -*-
"""Faehrt deploy/pruefe_commit.sh offline mit einem git-Stub.

    py -3.14 scripts/verify_deploy_commitbindung.py

Worum es geht: `landing/` ist per Bind-Mount live nach nginx gebunden, und
`/polymarket` wird direkt daraus ausgeliefert. Jede Aenderung am Arbeitsbaum des
Servers ist damit SOFORT oeffentlich — ein Abbruch danach nimmt nichts zurueck.
Die Bindung an den geprueften Commit ist deshalb kein Komfort, sondern der
einzige Schutz davor, dass ein Lauf einen Stand ausrollt, den er nie geprueft
hat.

Warum als Offline-Test und nicht per Codepruefung: der entscheidende Fall ist
ein ZEITFENSTER (Push zwischen Holen und Aktualisieren). YAML- und bash-Syntax
koennen das nicht sehen. Codex hat den Test in Runde 3 ausdruecklich verlangt,
nachdem die erste Fassung genau dieses Fenster offen liess — sie verglich und
pullte danach erneut, also mit einem zweiten Netzzugriff.

Das geprueefte Skript ist das ECHTE; gestellt wird nur `git`. Eine Nachbildung
der Logik wuerde nichts ueber die Produktion sagen.
"""
from __future__ import annotations

import io
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKRIPT = REPO / "deploy" / "pruefe_commit.sh"

A = "a" * 40          # der Commit, den der Lauf geprueft hat
B = "b" * 40          # ein waehrend des Laufs gepushter Commit
ALT = "c" * 40        # der Stand, auf dem der Server steht


# ── git-Stub ─────────────────────────────────────────────────────────────────
# Verhaelt sich wie git, soweit das Skript es braucht, und protokolliert jeden
# Aufruf. Die Kennungen kommen aus Umgebungsvariablen, damit ein Fall den Stand
# ZWISCHEN zwei Aufrufen wechseln kann — das ist der Kern des Zeitfensters.
GIT_STUB = r"""#!/bin/bash
printf '%s\n' "$*" >> "$SA_PROTOKOLL"

case "$*" in
  # Eine LOKALE Referenz. Das Skript darf nicht selbst holen — ein `fetch` hier
  # waere ein zweiter Netzzugriff und damit ein neues Zeitfenster; der Stub
  # kennt ihn deshalb bewusst NICHT und der Fall verbietet ihn ausdruecklich.
  "rev-parse origin/master")
    if [ "${SA_FERN_FEHLT:-}" = "1" ]; then
      echo "fatal: ambiguous argument 'origin/master'" >&2
      exit 1
    fi
    echo "${SA_FERN:?}"
    exit 0
    ;;
  "rev-parse HEAD")
    if [ -f "$SA_ARBEIT/vorgespult" ]; then
      cat "$SA_ARBEIT/vorgespult"
    else
      echo "${SA_HEAD:?}"
    fi
    exit 0
    ;;
  "rev-parse --short HEAD")
    if [ -f "$SA_ARBEIT/vorgespult" ]; then
      cut -c1-7 < "$SA_ARBEIT/vorgespult"
    else
      printf '%s\n' "${SA_HEAD:?}" | cut -c1-7
    fi
    exit 0
    ;;
  "merge --ff-only "*)
    # $3, nicht ${*##* }: bei `$*` wirkt die Musterentfernung auf JEDES
    # Positionsargument einzeln, und da keines ein Leerzeichen enthaelt, kam die
    # ganze Zeile heraus. Der Stub schrieb dann "merge --ff-only <sha>" als
    # Commit-Kennung, und der Normalfall scheiterte an einem Fehler des Tests.
    ziel="$3"
    # Zwei UNTERSCHIEDLICHE Gruende, weil sie unterschiedliche Meldungen und
    # unterschiedliche Diagnosen nach sich ziehen. Vorher gab es nur einen und
    # der Testfall behauptete trotzdem, einen Force-Push zu pruefen.
    if [ "${SA_MERGE_FEHLER:-}" = "1" ]; then
      echo "error: Your local changes would be overwritten by merge" >&2
      exit 1
    fi
    if [ "${SA_OBJEKT_FEHLT:-}" = "1" ]; then
      echo "merge: $ziel - not something we can merge" >&2
      exit 1
    fi
    # Hier steckt das Zeitfenster: SA_MERGE_LANDET_AUF stellt den Fall, dass die
    # Aktualisierung auf einem ANDEREN Commit endet als dem geprueften — zum
    # Beispiel, weil erneut aus dem Netz geholt wurde.
    printf '%s\n' "${SA_MERGE_LANDET_AUF:-$ziel}" > "$SA_ARBEIT/vorgespult"
    exit 0
    ;;
  "status --porcelain")
    printf '%s\n' " M scripts/skewfix_status.sh"
    exit 0
    ;;
  "status --porcelain -- .")
    # Die Sauberkeitspruefung nach dem Vorspulen. SA_SCHMUTZ stellt den Fall:
    # leer = sauber, sonst die Zeilen, die git ausgeben wuerde.
    # SA_STATUS_FEHLER stellt den Fall, dass git SELBST scheitert — vorher
    # verschluckte ein `|| true` an der Pipeline genau das.
    if [ "${SA_STATUS_FEHLER:-}" = "1" ]; then
      echo "fatal: not a git repository" >&2
      exit 128
    fi
    if [ -n "${SA_SCHMUTZ:-}" ]; then
      printf '%s\n' "$SA_SCHMUTZ"
    fi
    exit 0
    ;;
esac

echo "git-Stub: unbehandelter Aufruf '$*'" >&2
exit 97
"""


@dataclass
class Fall:
    name: str
    umgebung: dict
    erwartet_exit: int
    # Diese Aufrufe MUESSEN im Protokoll stehen bzw. duerfen es nicht.
    erwartet_aufruf: list[str] = field(default_factory=list)
    verboten_aufruf: list[str] = field(default_factory=list)
    erwartet_text: str | None = None
    # Argumente an das Pruefskript. `--nur-vergleich` darf den
    # Arbeitsbaum nicht anfassen; ohne dieses Feld liesse sich die
    # Betriebsart nicht pruefen.
    argumente: list[str] = field(default_factory=list)


FAELLE = [
    Fall("Gleicher Commit -> vorspulen auf die geprueefte Kennung, Exit 0",
         {"SA_SHA": A, "SA_FERN": A, "SA_HEAD": ALT},
         0,
         erwartet_aufruf=["merge --ff-only " + A, "status --porcelain -- ."],
         # Zwei Verbote. `pull` war der Fehler der ersten Fassung. `fetch` ist
         # neu verboten, weil das Holen in den Workflow gewandert ist: holt das
         # Skript selbst, ist der zweite Netzzugriff zurueck.
         verboten_aufruf=["pull", "fetch"]),

    Fall("Anderer Commit auf master -> Abbruch VOR jeder Aenderung",
         {"SA_SHA": A, "SA_FERN": B, "SA_HEAD": ALT},
         1,
         erwartet_aufruf=["rev-parse origin/master"],
         verboten_aufruf=["merge", "pull", "checkout", "fetch"],
         erwartet_text="auf master liegt"),

    Fall("origin/master nicht lesbar (kein fetch gelaufen) -> Abbruch",
         {"SA_SHA": A, "SA_FERN": A, "SA_HEAD": ALT, "SA_FERN_FEHLT": "1"},
         1,
         verboten_aufruf=["merge", "pull", "checkout"],
         erwartet_text="origin/master nicht lesbar"),

    # Zwei getrennte Scheiterngruende, weil sie verschiedene Diagnosen brauchen.
    # Der frueher hier stehende Fall hiess „nicht erreichbar (force-push)" und
    # behauptete damit mehr, als der Stub stellte — der erzwang nur einen
    # generischen Merge-Fehler (Codex-Befund, Runde 5). Und ein Force-Push NACH
    # dem Fetch laesst ein lokal vorhandenes Objekt ohnehin mergebar.
    Fall("Lokale Aenderung blockiert das Vorspulen -> rot mit Diagnose",
         {"SA_SHA": A, "SA_FERN": A, "SA_HEAD": ALT, "SA_MERGE_FEHLER": "1"},
         1,
         erwartet_aufruf=["merge --ff-only " + A, "status --porcelain"],
         erwartet_text="eine lokale Aenderung blockiert"),

    Fall("Objekt der geprueften Kennung fehlt lokal -> rot, nichts sichtbar",
         {"SA_SHA": A, "SA_FERN": A, "SA_HEAD": ALT, "SA_OBJEKT_FEHLT": "1"},
         1,
         erwartet_aufruf=["merge --ff-only " + A],
         erwartet_text="das Objekt fehlt"),

    Fall("Vorspulen landet woanders -> Nachkontrolle schlaegt an",
         {"SA_SHA": A, "SA_FERN": A, "SA_HEAD": ALT, "SA_MERGE_LANDET_AUF": B},
         1,
         erwartet_aufruf=["merge --ff-only " + A],
         erwartet_text="geprueft war"),

    # Fail-closed: eine nicht angekommene Kennung darf nicht in den Standard
    # fallen. Der Standard waere hier „irgendetwas ausrollen".
    # Die Kennung allein beweist keinen unveraenderten Quellbaum: eine lokale
    # Aenderung, die nicht kollidiert, ueberlebt das Vorspulen (Codex, Abnahme
    # 2026-10-08). Ohne diese Faelle waere die neue Pruefung unbelegt.
    Fall("Fremde Aenderung ueberlebt das Vorspulen -> rot",
         {"SA_SHA": A, "SA_FERN": A, "SA_HEAD": ALT,
          "SA_SCHMUTZ": " M shared/polymarket_data.py"},
         1,
         erwartet_aufruf=["status --porcelain -- ."],
         erwartet_text="weicht vom geprueften Commit"),

    Fall("Nur deploy/nginx.conf geaendert -> bewusst erlaubt, Exit 0",
         {"SA_SHA": A, "SA_FERN": A, "SA_HEAD": ALT,
          "SA_SCHMUTZ": " M deploy/nginx.conf"},
         0,
         erwartet_aufruf=["status --porcelain -- ."],
         erwartet_text="Arbeitsbaum auf dem geprueften Commit"),

    Fall("Untrackte Datei allein ist kein Abbruchgrund",
         {"SA_SHA": A, "SA_FERN": A, "SA_HEAD": ALT,
          "SA_SCHMUTZ": "?? landing/data/options_skew.json"},
         0,
         erwartet_aufruf=["status --porcelain -- ."],
         erwartet_text="Arbeitsbaum auf dem geprueften Commit"),

    Fall("`git status` scheitert -> UNGEPRUEFT, und das ist nicht bestanden",
         {"SA_SHA": A, "SA_FERN": A, "SA_HEAD": ALT, "SA_STATUS_FEHLER": "1"},
         1,
         erwartet_aufruf=["status --porcelain -- ."],
         erwartet_text="UNGEPRUEFT"),

    # --nur-vergleich laeuft VOR den Reverts und darf den Baum nicht anfassen.
    Fall("--nur-vergleich bei gleicher Kennung -> Exit 0 ohne Vorspulen",
         {"SA_SHA": A, "SA_FERN": A, "SA_HEAD": ALT},
         0,
         argumente=["--nur-vergleich"],
         erwartet_aufruf=["rev-parse origin/master"],
         verboten_aufruf=["merge", "pull", "fetch", "checkout", "status"],
         erwartet_text="Baum unangetastet"),

    Fall("--nur-vergleich bei anderer Kennung -> rot, nichts angefasst",
         {"SA_SHA": A, "SA_FERN": B, "SA_HEAD": ALT},
         1,
         argumente=["--nur-vergleich"],
         verboten_aufruf=["merge", "pull", "fetch", "checkout", "status"],
         erwartet_text="auf master liegt"),

    Fall("SA_SHA ungesetzt -> Abbruch ohne einen einzigen git-Aufruf",
         {"SA_FERN": A, "SA_HEAD": ALT},
         1,
         verboten_aufruf=["rev-parse", "merge", "pull", "fetch"]),
]


def fahre(fall: Fall, arbeit: Path) -> tuple[int, list[str], str]:
    protokoll = arbeit / "aufrufe.txt"
    protokoll.write_text("", encoding="utf-8")
    stubs = arbeit / "stubs"
    stubs.mkdir(exist_ok=True)
    g = stubs / "git"
    g.write_text(GIT_STUB, encoding="utf-8", newline="\n")
    g.chmod(0o755)

    umgebung = {
        "PATH": f"{stubs}{os.pathsep}/usr/bin{os.pathsep}/bin",
        "SA_PROTOKOLL": str(protokoll),
        "SA_ARBEIT": str(arbeit),
        "HOME": str(arbeit),
    }
    umgebung.update({k: v for k, v in fall.umgebung.items() if v is not None})

    r = subprocess.run(["bash", str(SKRIPT), *fall.argumente], env=umgebung,
                       capture_output=True,
                       text=True, timeout=60, cwd=str(arbeit))
    zeilen = [z for z in protokoll.read_text(encoding="utf-8").splitlines() if z.strip()]
    return r.returncode, zeilen, (r.stdout + r.stderr)


def main() -> int:
    if not SKRIPT.is_file():
        print(f"{SKRIPT} fehlt — UNGEPRUEFT, und das ist nicht BESTANDEN.")
        return 1

    fehler = 0
    for fall in FAELLE:
        with tempfile.TemporaryDirectory(prefix="cb-") as tmp:
            code, zeilen, ausgabe = fahre(fall, Path(tmp))
        probleme = []
        if code != fall.erwartet_exit:
            probleme.append(f"Exit {code}, erwartet {fall.erwartet_exit}")
        for muss in fall.erwartet_aufruf:
            if not any(muss in z for z in zeilen):
                probleme.append(f"'{muss}' fehlt im Protokoll")
        for darf_nicht in fall.verboten_aufruf:
            if any(darf_nicht in z for z in zeilen):
                probleme.append(f"'{darf_nicht}' wurde aufgerufen, obwohl verboten")
        if fall.erwartet_text and fall.erwartet_text not in ausgabe:
            probleme.append(f"Meldung ohne '{fall.erwartet_text}'")
        if "unbehandelter Aufruf" in ausgabe:
            probleme.append("der Stub kennt einen Aufruf nicht — Fall unvollstaendig")

        if probleme:
            fehler += 1
            print(f"[FEHL] {fall.name}")
            for p in probleme:
                print(f"         {p}")
            if zeilen:
                print(f"         git-Aufrufe: {zeilen}")
            for z in (ausgabe or "").strip().splitlines()[-4:]:
                print(f"         > {z}")
        else:
            print(f"[OK  ] {fall.name}")

    print("=" * 72)
    print("alle Faelle wie erwartet" if fehler == 0
          else f"{fehler} Fall/Faelle abweichend")
    return 0 if fehler == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
