#!/usr/bin/env python3
"""
verify_workflow_inputs.py — fährt die Remote-Skripte der Workflows OFFLINE.

    py -3.14 scripts/verify_workflow_inputs.py

Die Skripte in `.github/workflows/*.yml` laufen per `appleboy/ssh-action` als **root**
auf dem VPS. Sie lassen sich hier nicht auslösen (und sollen es auch nicht), aber ihr
Skriptrumpf ist gewöhnliches bash — also wird er extrahiert und mit einem `docker`-Stub
gefahren, der nur seine Argumente protokolliert. Kein Netz, kein Versand, kein Deploy.

Geprüft wird die **Entscheidungsmatrix** je Eingabe: ungesetzt, gesetzt-und-leer,
`false`, `true`, gültiger Wert — und das jeweils für `schedule` und `workflow_dispatch`.

Der Fall, der das nötig macht: eine Eingabe, die unterwegs verloren geht, darf nicht
stillschweigend in den **Standard** fallen, wenn der Standard der produktive Versand
ist. Ein verlorener `dry_run` wäre sonst ein echter Massenversand. Deshalb verlangt
diese Prüfung für jede unterdrückende Eingabe, dass der Lauf **abbricht**, statt zu
senden.

Exit 0 = alle Fälle wie erwartet. Exit 1 = mindestens einer nicht.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

try:
    import yaml
except ImportError:  # pragma: no cover
    print("PyYAML fehlt — ohne sie kann dieser Wächter nichts messen.")
    print("UNGEPRÜFT ist nicht BESTANDEN, deshalb Exit 1.")
    sys.exit(1)


@dataclass
class Fall:
    name: str
    umgebung: dict          # was auf dem Server ankommt; None = ungesetzt
    erwartet_exit: int | None   # None = egal
    erwartet_args: list[str] | None = None   # Argumente an das Python-Skript
    erwartet_kein_aufruf: bool = False       # das Skript darf NICHT laufen


# ── Workflows und ihre erwartete Matrix ─────────────────────────────────────

MATRIX: dict[str, list[Fall]] = {
    "daily_newsletter.yml": [
        Fall("Zeitplan: alles leer -> normaler Versand",
             {"SA_EVENT": "schedule", "SA_DRY": "", "SA_TEST": "", "SA_TO": ""},
             0, []),
        Fall("Dispatch: dry_run=true -> --dry-run",
             {"SA_EVENT": "workflow_dispatch", "SA_DRY": "true",
              "SA_TEST": "false", "SA_TO": ""},
             0, ["--dry-run"]),
        Fall("Dispatch: test_mode=true -> --test",
             {"SA_EVENT": "workflow_dispatch", "SA_DRY": "false",
              "SA_TEST": "true", "SA_TO": ""},
             0, ["--test"]),
        Fall("Dispatch: Adresse -> --to=…",
             {"SA_EVENT": "workflow_dispatch", "SA_DRY": "false",
              "SA_TEST": "false", "SA_TO": "a.b+c@example.com"},
             0, ["--to=a.b+c@example.com"]),
        # Die tragenden Fälle: nichts darf senden, wenn etwas fehlt oder
        # verdächtig aussieht.
        Fall("FAIL-CLOSED: SA_DRY ungesetzt -> Abbruch OHNE Versand",
             {"SA_EVENT": "workflow_dispatch", "SA_DRY": None,
              "SA_TEST": "false", "SA_TO": ""},
             None, erwartet_kein_aufruf=True),
        Fall("FAIL-CLOSED: SA_TEST ungesetzt -> Abbruch OHNE Versand",
             {"SA_EVENT": "workflow_dispatch", "SA_DRY": "false",
              "SA_TEST": None, "SA_TO": ""},
             None, erwartet_kein_aufruf=True),
        Fall("FAIL-CLOSED: Dispatch mit leerem Boolean -> Abbruch",
             {"SA_EVENT": "workflow_dispatch", "SA_DRY": "",
              "SA_TEST": "false", "SA_TO": ""},
             1, erwartet_kein_aufruf=True),
        Fall("FAIL-CLOSED: Boolean ist Unsinn -> Abbruch",
             {"SA_EVENT": "workflow_dispatch", "SA_DRY": "ja",
              "SA_TEST": "false", "SA_TO": ""},
             1, erwartet_kein_aufruf=True),
        # Einschleusung: nach der Umstellung ist der Wert DATEN, kein Quelltext.
        Fall("Einschleusung: Semikolon in --to -> Abbruch, kein Befehl",
             {"SA_EVENT": "workflow_dispatch", "SA_DRY": "false",
              "SA_TEST": "false", "SA_TO": "x@y.z; touch /tmp/pwned"},
             1, erwartet_kein_aufruf=True),
        Fall("Einschleusung: Backtick in --to -> Abbruch",
             {"SA_EVENT": "workflow_dispatch", "SA_DRY": "false",
              "SA_TEST": "false", "SA_TO": "x@y.z`id`"},
             1, erwartet_kein_aufruf=True),
        Fall("Einschleusung: fuehrendes Minus -> Abbruch",
             {"SA_EVENT": "workflow_dispatch", "SA_DRY": "false",
              "SA_TEST": "false", "SA_TO": "-oProxyCommand=x@y.z"},
             1, erwartet_kein_aufruf=True),
    ],
}

STUB = """#!/bin/bash
# Protokolliert nur, was aufgerufen wurde — fuehrt nichts aus.
printf '%s\\n' "$*" >> "$SA_PROTOKOLL"
exit 0
"""


def skript_aus_workflow(datei: Path) -> str:
    d = yaml.safe_load(datei.read_text(encoding="utf-8"))
    for job in (d.get("jobs") or {}).values():
        for step in job.get("steps") or []:
            mit = step.get("with") or {}
            if "script" in mit:
                return mit["script"]
    raise AssertionError(f"{datei.name}: kein ssh-action-Skript gefunden")


def fahre(skript: str, fall: Fall, arbeitsverz: Path) -> tuple[int, list[str], str]:
    protokoll = arbeitsverz / "aufrufe.txt"
    protokoll.write_text("", encoding="utf-8")

    stubs = arbeitsverz / "stubs"
    stubs.mkdir(exist_ok=True)
    for name in ("docker", "systemctl", "curl"):
        p = stubs / name
        p.write_text(STUB, encoding="utf-8")
        p.chmod(0o755)

    umgebung = {
        "PATH": f"{stubs}{os.pathsep}/usr/bin{os.pathsep}/bin",
        "SA_PROTOKOLL": str(protokoll),
        "HOME": str(arbeitsverz),
    }
    for k, v in fall.umgebung.items():
        if v is not None:
            umgebung[k] = v

    sk = arbeitsverz / "remote.sh"
    sk.write_text(skript, encoding="utf-8", newline="\n")
    r = subprocess.run(["bash", str(sk)], env=umgebung, capture_output=True,
                       text=True, timeout=60, cwd=str(arbeitsverz))
    zeilen = [z for z in protokoll.read_text(encoding="utf-8").splitlines() if z.strip()]
    return r.returncode, zeilen, (r.stdout + r.stderr)


def args_aus_aufruf(zeilen: list[str]) -> list[str] | None:
    """Die Argumente, die das Python-Skript bekommen hätte."""
    for z in zeilen:
        if "daily_newsletter.py" in z or "scripts/" in z:
            teile = z.split()
            if "--" in z or teile:
                idx = next((i for i, t in enumerate(teile) if t.endswith(".py")), None)
                if idx is not None:
                    return teile[idx + 1:]
    return None


def main() -> int:
    if not shutil.which("bash"):
        print("bash nicht gefunden — UNGEPRÜFT, und das ist nicht BESTANDEN.")
        return 1

    fehler = 0
    for name, faelle in MATRIX.items():
        datei = REPO / ".github" / "workflows" / name
        if not datei.is_file():
            print(f"[?   ] {name} fehlt")
            fehler += 1
            continue
        skript = skript_aus_workflow(datei)
        print(f"=== {name} ===")
        for fall in faelle:
            with tempfile.TemporaryDirectory(prefix="wf-") as tmp:
                code, zeilen, ausgabe = fahre(skript, fall, Path(tmp))
            probleme = []

            gerufen = any(".py" in z for z in zeilen)
            if fall.erwartet_kein_aufruf and gerufen:
                probleme.append("das Skript wurde AUFGERUFEN, obwohl es nicht sollte")
            if not fall.erwartet_kein_aufruf and not gerufen:
                probleme.append("das Skript wurde nicht aufgerufen")
            if fall.erwartet_exit is not None and code != fall.erwartet_exit:
                probleme.append(f"Exit {code}, erwartet {fall.erwartet_exit}")
            if fall.erwartet_args is not None:
                ist = args_aus_aufruf(zeilen)
                if ist != fall.erwartet_args:
                    probleme.append(f"Argumente {ist}, erwartet {fall.erwartet_args}")
            # Eine Einschleusung darf nie einen zweiten Befehl erzeugt haben
            if any("pwned" in z or z.strip() == "id" for z in zeilen):
                probleme.append("ein eingeschleuster Befehl wurde ausgefuehrt")

            if probleme:
                fehler += 1
                print(f"[FEHL] {fall.name}")
                for p in probleme:
                    print(f"         {p}")
                if ausgabe.strip():
                    print(f"         Ausgabe: {ausgabe.strip().splitlines()[-1][:110]}")
            else:
                print(f"[OK  ] {fall.name}")

    print("=" * 72)
    print("alle Fälle wie erwartet" if fehler == 0
          else f"{fehler} Fall/Fälle abweichend")
    return 0 if fehler == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
