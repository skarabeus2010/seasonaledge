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
    # Der Stub scheitert, sobald der Aufruf diesen Text enthaelt. Damit laesst
    # sich ein Teilfehler nachstellen, statt die Fehlerweitergabe zu behaupten.
    stub_scheitert_bei: str | None = None
    # Dieses Skript darf NACH dem Fehlschlag nicht mehr gelaufen sein. Die
    # Reihenfolge ist der eigentliche Schutz: ein gescheiterter Scrape, dem die
    # Auswertung folgt, rechnet auf veralteten Daten weiter.
    erwartet_nicht_aufgerufen: str | None = None


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
    "db_completeness.yml": [
        # Hier ist die Polaritaet UMGEKEHRT und zwar absichtlich: leer heisst an,
        # weil der Zeitplan keine Eingaben hat. Der Zeitplan-Fall muss deshalb
        # --fix und --mail bekommen.
        Fall("Zeitplan: alles leer -> --fix und --mail an",
             {"SA_EVENT": "schedule", "SA_DIMS": "", "SA_GAP_YEARS": "",
              "SA_FIX": "", "SA_DERIVED": "", "SA_MAIL": ""},
             0, ["--dim", "freshness,coverage,gaps,events", "--gap-years", "2",
                 "--fix", "--mail"]),
        Fall("Dispatch: fix=false -> KEIN --fix",
             {"SA_EVENT": "workflow_dispatch", "SA_DIMS": "freshness",
              "SA_GAP_YEARS": "2", "SA_FIX": "false", "SA_DERIVED": "false",
              "SA_MAIL": "false"},
             0, ["--dim", "freshness", "--gap-years", "2"]),
        Fall("Dispatch: fix_derived=true -> --fix-derived",
             {"SA_EVENT": "workflow_dispatch", "SA_DIMS": "gaps",
              "SA_GAP_YEARS": "5", "SA_FIX": "false", "SA_DERIVED": "true",
              "SA_MAIL": "false"},
             0, ["--dim", "gaps", "--gap-years", "5", "--fix-derived"]),
        # Der teure Fall: ein verlorenes fix=false darf NICHT in --fix kippen.
        Fall("FAIL-CLOSED: SA_FIX ungesetzt -> Abbruch, kein Backfill",
             {"SA_EVENT": "workflow_dispatch", "SA_DIMS": "gaps",
              "SA_GAP_YEARS": "2", "SA_FIX": None, "SA_DERIVED": "false",
              "SA_MAIL": "false"},
             None, erwartet_kein_aufruf=True),
        Fall("FAIL-CLOSED: Dispatch mit leerem Boolean -> Abbruch",
             {"SA_EVENT": "workflow_dispatch", "SA_DIMS": "gaps",
              "SA_GAP_YEARS": "2", "SA_FIX": "", "SA_DERIVED": "false",
              "SA_MAIL": "false"},
             1, erwartet_kein_aufruf=True),
        Fall("Freitext: unbekannte Dimension -> Abbruch",
             {"SA_EVENT": "workflow_dispatch", "SA_DIMS": "gaps,unsinn",
              "SA_GAP_YEARS": "2", "SA_FIX": "false", "SA_DERIVED": "false",
              "SA_MAIL": "false"},
             1, erwartet_kein_aufruf=True),
        Fall("Freitext: gap_years keine Zahl -> Abbruch",
             {"SA_EVENT": "workflow_dispatch", "SA_DIMS": "gaps",
              "SA_GAP_YEARS": "2; id", "SA_FIX": "false", "SA_DERIVED": "false",
              "SA_MAIL": "false"},
             1, erwartet_kein_aufruf=True),
        Fall("Einschleusung ueber dims -> Abbruch, kein Befehl",
             {"SA_EVENT": "workflow_dispatch", "SA_DIMS": "gaps`id`",
              "SA_GAP_YEARS": "2", "SA_FIX": "false", "SA_DERIVED": "false",
              "SA_MAIL": "false"},
             1, erwartet_kein_aufruf=True),
    ],
    "full_scanner.yml": [
        Fall("Zeitplan: alles leer -> keine Argumente",
             {"SA_EVENT": "schedule", "SA_QUICK": "", "SA_RESUME": "",
              "SA_LIMIT": ""}, 0, []),
        Fall("Dispatch: quick + limit=50",
             {"SA_EVENT": "workflow_dispatch", "SA_QUICK": "true",
              "SA_RESUME": "false", "SA_LIMIT": "50"},
             0, ["--quick", "--limit", "50"]),
        Fall("Freitext: limit keine Zahl -> Abbruch",
             {"SA_EVENT": "workflow_dispatch", "SA_QUICK": "false",
              "SA_RESUME": "false", "SA_LIMIT": "50; id"},
             1, erwartet_kein_aufruf=True),
        Fall("FAIL-CLOSED: SA_LIMIT ungesetzt -> Abbruch",
             {"SA_EVENT": "workflow_dispatch", "SA_QUICK": "false",
              "SA_RESUME": "false", "SA_LIMIT": None},
             None, erwartet_kein_aufruf=True),
    ],
    "event_data_daily.yml": [
        Fall("Zeitplan: leer -> --mode both, alle Ticker",
             {"SA_EVENT": "schedule", "SA_MODE": "", "SA_TICKERS": ""},
             0, ["--mode", "both"]),
        # Die Aufteilung in mehrere Ticker muss ERHALTEN bleiben.
        Fall("Dispatch: drei Ticker bleiben drei Argumente",
             {"SA_EVENT": "workflow_dispatch", "SA_MODE": "dividends",
              "SA_TICKERS": "AAPL SAP.DE ^GSPC"},
             0, ["--mode", "dividends", "--tickers", "AAPL", "SAP.DE", "^GSPC"]),
        Fall("Freitext: Semikolon in der Tickerliste -> Abbruch",
             {"SA_EVENT": "workflow_dispatch", "SA_MODE": "both",
              "SA_TICKERS": "AAPL; touch $HOME/pwned"},
             1, erwartet_kein_aufruf=True),
        Fall("Freitext: unbekannter Modus -> Abbruch",
             {"SA_EVENT": "workflow_dispatch", "SA_MODE": "alles",
              "SA_TICKERS": ""}, 1, erwartet_kein_aufruf=True),
    ],
    "weekly_newsletter_manual.yml": [
        Fall("Dispatch: mode=test -> --test",
             {"SA_MODE": "test"}, 0, ["--test"]),
        Fall("Dispatch: mode=live -> keine Argumente",
             {"SA_MODE": "live"}, 0, []),
        Fall("Unbekannter Modus -> Abbruch (bestehender sicherer Zweig)",
             {"SA_MODE": "irgendwas"}, 1, erwartet_kein_aufruf=True),
        Fall("FAIL-CLOSED: SA_MODE ungesetzt -> Abbruch",
             {"SA_MODE": None}, None, erwartet_kein_aufruf=True),
    ],
    "congress_trades.yml": [
        Fall("Zeitplan: leer -> --run",
             {"SA_EVENT": "schedule", "SA_SEED": ""}, 0, ["--run"]),
        Fall("Dispatch: seed_only=true -> --seed-only",
             {"SA_EVENT": "workflow_dispatch", "SA_SEED": "true"},
             0, ["--seed-only"]),
        Fall("FAIL-CLOSED: SA_SEED ungesetzt -> Abbruch",
             {"SA_EVENT": "workflow_dispatch", "SA_SEED": None},
             None, erwartet_kein_aufruf=True),
    ],
    "brier_compute.yml": [
        Fall("Zeitplan: tags leer -> keine Tag-Einschraenkung",
             {"SA_EVENT": "schedule", "SA_TAGS": "", "SA_SKIP": ""}, 0, []),
        Fall("Dispatch: tags=all -> keine Einschraenkung",
             {"SA_EVENT": "workflow_dispatch", "SA_TAGS": "all",
              "SA_SKIP": "false"}, 0, []),
        Fall("Dispatch: tags=fed -> --tag fed",
             {"SA_EVENT": "workflow_dispatch", "SA_TAGS": "fed",
              "SA_SKIP": "false"}, 0, ["--tag", "fed"]),
        Fall("Freitext: Backtick in tags -> Abbruch",
             {"SA_EVENT": "workflow_dispatch", "SA_TAGS": "fed`id`",
              "SA_SKIP": "false"}, 1, erwartet_kein_aufruf=True),
        # Fehlerweitergabe (Codex-Befund 4, 2026-10-07). Vorher stand hier
        # `set -uo pipefail` OHNE -e: die Pipeline meldete den Fehler, das
        # Skript lief weiter, und das letzte `echo Done` wurde zum Exit-Code.
        # Die REIHENFOLGE ist der eigentliche Schutz — laeuft die Auswertung
        # nach einem gescheiterten Scrape, rechnet sie den alten Bestand neu
        # aus und die Seite zeigt eine frische Kennzahl auf veralteten Daten.
        Fall("Scrape scheitert -> ROT und die Brier-Berechnung laeuft NICHT",
             {"SA_EVENT": "schedule", "SA_TAGS": "", "SA_SKIP": ""},
             1, stub_scheitert_bei="polymarket_scrape_resolved.py",
             erwartet_nicht_aufgerufen="compute_brier_stats.py"),
        Fall("Brier-Berechnung scheitert -> ROT",
             {"SA_EVENT": "schedule", "SA_TAGS": "", "SA_SKIP": ""},
             1, stub_scheitert_bei="compute_brier_stats.py"),
    ],
    "polymarket_daily.yml": [
        Fall("FAIL-CLOSED: SA_BACKFILL ungesetzt -> Abbruch",
             {"SA_EVENT": "workflow_dispatch", "SA_BACKFILL": None},
             None, erwartet_kein_aufruf=True),
        Fall("Dispatch: Boolean ist Unsinn -> Abbruch",
             {"SA_EVENT": "workflow_dispatch", "SA_BACKFILL": "vielleicht"},
             1, erwartet_kein_aufruf=True),
        # Fehlerweitergabe, siehe Begruendung bei brier_compute.yml.
        # Die Faelle sind bewusst WOCHENTAGSUNABHAENGIG: das Skript liest
        # `date -u +%u` fuer den Montags-Backfill. Im Fehlerfall bricht es vor
        # dieser Stelle ab, im Normalfall wird ueber den Backfill nichts
        # behauptet — sonst waere der Test montags rot.
        # Erfolgskontrolle, KEIN Nachweis der Fehlerweitergabe: dieser Fall
        # bleibt auch ohne den Fix gruen (Codex-Befund, Runde 2). Er steht hier,
        # damit eine zu scharfe Korrektur den Normalfall nicht mitreisst.
        Fall("Erfolgskontrolle (kein Fehlernachweis): normaler Lauf, Exit 0",
             {"SA_EVENT": "schedule", "SA_BACKFILL": ""}, 0, []),
        # workflow_dispatch mit SA_BACKFILL=true, damit der Backfill wirklich
        # LAUFEN WUERDE. Mein erster Entwurf nahm `schedule` mit leerem Wert —
        # dann ist der Backfill ausser montags ohnehin uebersprungen und die
        # Aussage „KEIN Backfill" beweist nichts (Codex-Befund, Runde 2).
        Fall("Snapshot scheitert -> ROT und KEIN Backfill (der sonst liefe)",
             {"SA_EVENT": "workflow_dispatch", "SA_BACKFILL": "true"},
             1, stub_scheitert_bei="polymarket_refresh.py",
             erwartet_nicht_aufgerufen="polymarket_backfill.py"),
        Fall("Backfill scheitert -> ROT",
             {"SA_EVENT": "workflow_dispatch", "SA_BACKFILL": "true"},
             1, stub_scheitert_bei="polymarket_backfill.py"),
    ],
}

STUB = """#!/bin/bash
# Protokolliert nur, was aufgerufen wurde — fuehrt nichts aus.
printf '%s\\n' "$*" >> "$SA_PROTOKOLL"
# Nachgestellter Teilfehler: enthaelt der Aufruf den gesetzten Text, endet der
# Stub mit 1. So wird die Fehlerweitergabe gemessen und nicht behauptet.
if [ -n "${SA_STUB_FEHLER:-}" ] && printf '%s' "$*" | grep -qF -- "$SA_STUB_FEHLER"; then
  echo "Stub: absichtlicher Fehlschlag fuer '$SA_STUB_FEHLER'" >&2
  exit 1
fi
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
    if fall.stub_scheitert_bei:
        umgebung["SA_STUB_FEHLER"] = fall.stub_scheitert_bei
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
            if fall.erwartet_nicht_aufgerufen:
                nach = fall.erwartet_nicht_aufgerufen
                if any(nach in z for z in zeilen):
                    probleme.append(
                        f"'{nach}' lief TROTZ des Fehlschlags — der Folgeschritt "
                        "rechnet damit auf veralteten Daten weiter")
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
