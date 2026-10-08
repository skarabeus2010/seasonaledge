#!/usr/bin/env python3
"""
verify_docs_mutation.py — prüft den WÄCHTER `verify_docs.py`, nicht die Doku.

    py -3.14 scripts/verify_docs_mutation.py

Baut jeden Defekt, den `verify_docs.py` fangen soll, absichtlich in eine **Kopie** des
Baums ein und verlangt DURCHGEFALLEN. Eine Mutation, die unbemerkt bleibt, ist eine
Lücke im Wächter.

Warum das nötig ist: beim ersten Lauf des Wächters waren drei von vier Prüfungen rot,
und **kein einziger** dieser Treffer war echt — User-Agent-Versionen galten als
IP-Adressen, eine geplante Infrastruktur-Ebene als fremdes Verzeichnis, und
`_loaders['x'](filters)` als Markdown-Link. Ein Prüfer, der Rauschen meldet, wird
ignoriert; einer, der nichts meldet, wird geglaubt. Beide Richtungen brauchen einen Test.

Es wird **keine Datei im Arbeitsbaum** geschrieben. Jede Mutation läuft in einem
temporären Verzeichnis, auf das `setze_repo()` den Wächter richtet.

Der Wächter braucht `git ls-files`, deshalb wird die Kopie zu einem echten Git-Repo
gemacht — sonst melden die Prüfungen 1 und 2 nur UNGEPRÜFT, und der Test würde eine
Fiktion prüfen.

Exit 0 = alle aussagekräftigen Mutationen gefangen. Exit 1 = eine entwischt.
Exit 2 = keine war aussagekräftig (dann ist der Wächter nicht abgenommen).
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

REPO = Path(__file__).resolve().parent.parent
if str(REPO / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO / "scripts"))

import verify_docs as vd  # noqa: E402


@dataclass
class Mutation:
    nummer: int
    name: str
    anwenden: Callable[[Path], bool]


# Der Baum wird EINMAL gebaut und nach jeder Mutation zurückgesetzt. Ihn elfmal
# zu kopieren dauerte über zwei Minuten, und ein Test, der zu lange läuft, wird
# nicht gelaufen.
_BERUEHRT: list[tuple[Path, bytes | None]] = []


def _merken(p: Path) -> None:
    _BERUEHRT.append((p, p.read_bytes() if p.is_file() else None))


def _zuruecknehmen(baum: Path) -> None:
    """Stellt den Zustand vor der Mutation wieder her."""
    while _BERUEHRT:
        p, inhalt = _BERUEHRT.pop()
        if inhalt is None:
            if p.is_file():
                p.unlink()
        else:
            p.write_bytes(inhalt)
    # Index zurücksetzen und wieder GENAU die Originalliste stagen — `git add -A`
    # würde hier die untrackten Dateien einsammeln, die oben bewusst draußen sind.
    liste = baum / ".git" / "pathspec.txt"
    subprocess.run(["git", "reset", "-q"], cwd=baum, capture_output=True)
    if liste.is_file():
        subprocess.run(["git", "add", "--pathspec-from-file", str(liste),
                        "--pathspec-file-nul"], cwd=baum, capture_output=True)


def _schreibe(baum: Path, rel: str, text: str) -> bool:
    p = baum / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    _merken(p)
    p.write_text(text, encoding="utf-8")
    subprocess.run(["git", "add", rel], cwd=baum, capture_output=True)
    return True


def _anhaengen(baum: Path, rel: str, text: str) -> bool:
    p = baum / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    _merken(p)
    with p.open("a", encoding="utf-8") as f:
        f.write(text)
    subprocess.run(["git", "add", rel], cwd=baum, capture_output=True)
    return True


MUTATIONEN: list[Mutation] = [
    # ⚠️ Hier NICHT 192.0.2.x, 198.51.100.x oder 203.0.113.x nehmen. Das sind die
    # Dokumentationsnetze aus RFC 5737, und `is_global` meldet sie korrekt als
    # nicht öffentlich — der Wächter ignoriert sie also zu Recht. Mein erster
    # Entwurf nahm genau die, und beide Mutationen „entwischten": der Test war
    # falsch, nicht der Wächter.
    Mutation(1, "oeffentliche IP in einer Doku-Datei", lambda b: _anhaengen(
        b, "docs/_mutation.md", "\nServer: 8.8.8.8\n")), # WAECHTER-BEISPIEL

    Mutation(1, "oeffentliche IP in einem Skript", lambda b: _schreibe(
        b, "scripts/_mutation_ip.py", 'HOST = "8.8.4.4"\n')), # WAECHTER-BEISPIEL

    # Die Gegenprobe zur Entschaerfung: eine Programmversion darf NICHT greifen.
    Mutation(1, "User-Agent-Version darf NICHT als IP gelten "
                "(Gegenprobe zur Entschaerfung)", lambda b: _schreibe(
        b, "scripts/_mutation_ua.py",
        'UA = "Mozilla/5.0 (Windows NT 10.0) Chrome/131.0.0.0 Safari/537.36"\n')), # WAECHTER-BEISPIEL

    Mutation(2, "Supabase-Projekt-Host", lambda b: _anhaengen(
        b, "docs/_mutation2.md", "\nhttps://abcdefghijklmnopqrst.supabase.co/rest/v1/x\n")), # WAECHTER-BEISPIEL

    Mutation(2, "Versand-Key mit Nutzlast", lambda b: _anhaengen(
        b, "docs/_mutation3.md", "\nbrevo_api_key = xkeysib-a1b2c3d4e5f6a7b8\n")), # WAECHTER-BEISPIEL

    Mutation(2, "fremdes Server-Verzeichnis", lambda b: _anhaengen(
        b, "docs/_mutation4.md", "\nMount aus /opt/fremdprojekt/website lesen\n")), # WAECHTER-BEISPIEL

    Mutation(2, "SSH-Zugang mit konkretem Ziel", lambda b: _anhaengen(
        b, "docs/_mutation5.md", "\n    ssh -i ~/.ssh/key root@beispielhost.example\n")), # WAECHTER-BEISPIEL

    Mutation(3, "Verweis auf eine nicht existierende Datei", lambda b: _anhaengen(
        b, "docs/_mutation6.md", "\nSiehe [Plan](gibtesnicht/plan.md).\n")),

    # Gegenprobe: Code, der wie ein Link aussieht, darf NICHT greifen.
    Mutation(3, "Code in Backticks darf NICHT als Link gelten "
                "(Gegenprobe zur Entschaerfung)", lambda b: _anhaengen(
        b, "docs/_mutation7.md", "\nAufruf: `_loaders['indicator-filters'](filters)`\n")),

    Mutation(4, "Einstiegsdatei ueber der Zeilengrenze", lambda b: _schreibe(
        b, "CLAUDE.md", "\n".join(f"Zeile {i}" for i in range(400)) + "\n")),
]

# Welche Mutationen sind GEGENPROBEN? Die verlangen BESTANDEN, nicht DURCHGEFALLEN.
GEGENPROBE = {"User-Agent-Version", "Code in Backticks"}

# Die Kopie muss vollständig genug sein, dass die Verweisprüfung dieselben Ziele
# findet wie im Arbeitsbaum. Mit einer Teilkopie war Prüfung 3 im Ausgangszustand
# rot — und dann beweist weder ihre Mutation noch ihre Gegenprobe etwas.
AUSNEHMEN = shutil.ignore_patterns(
    "__pycache__", ".git", "worktrees", "node_modules", "logs",
    "*.png", "*.jpg", "*.jpeg", "*.mp4", "*.pdf", "*.zip",
    "data", "output", "en", "lightning_logs", "raw")


def baum_vorbereiten(ziel: Path) -> None:
    for eintrag in REPO.iterdir():
        if eintrag.name in (".git", "node_modules", "lightning_logs", "raw"):
            continue
        zielpfad = ziel / eintrag.name
        try:
            if eintrag.is_dir():
                shutil.copytree(eintrag, zielpfad, dirs_exist_ok=True,
                                ignore=AUSNEHMEN, symlinks=True)
            else:
                shutil.copy2(eintrag, zielpfad)
        except (OSError, shutil.Error):
            # Einzelne unlesbare Dateien machen den Test nicht ungültig.
            pass
    # Echtes Git-Repo, damit `git ls-files` etwas liefert — und zwar GENAU das, was
    # das Original trackt.
    #
    # `git add -A` wäre hier falsch: es nimmt Dateien auf, die im echten Repo
    # untracked (aber nicht ignoriert) sind — etwa eine lokale nginx-Arbeitskopie.
    # Die trägt Betriebsdetails, und die Prüfungen 1 und 2 waren in der Kopie
    # deshalb rot, während sie im Arbeitsbaum grün sind. Dann prüft der
    # Mutationstest einen anderen Zustand als die Produktion.
    subprocess.run(["git", "init", "-q"], cwd=ziel, capture_output=True)
    r = subprocess.run(["git", "ls-files", "-z"], cwd=REPO,
                       capture_output=True, timeout=60)
    liste = ziel / ".git" / "pathspec.txt"
    liste.write_bytes(r.stdout)
    subprocess.run(["git", "add", "--pathspec-from-file", str(liste),
                    "--pathspec-file-nul"], cwd=ziel, capture_output=True)


def status_von(nummer: int) -> str:
    for e in vd.alle_pruefungen():
        if e.nummer == nummer:
            return e.status
    raise AssertionError(f"Prüfung {nummer} existiert nicht")


def main() -> int:
    original = vd.REPO

    # Vorbedingung: ohne Mutation muss der Waechter auf der KOPIE dasselbe sagen wie
    # auf dem Arbeitsbaum. Sonst prueft der Mutationstest einen anderen Zustand als
    # die Produktion — derselbe Fehler, der in diesem Projekt schon dreimal Geld
    # gekostet hat.
    tmp = tempfile.mkdtemp(prefix="docs-mut-")
    basis = Path(tmp)
    try:
        baum_vorbereiten(basis)
        vd.setze_repo(basis)
        basiszustand = {n: status_von(n) for n in (1, 2, 3, 4)}
        vd.setze_repo(original)
        echt = {e.nummer: e.status for e in vd.alle_pruefungen()}
        return _lauf(basis, original, basiszustand, echt)
    finally:
        vd.setze_repo(original)
        shutil.rmtree(basis, ignore_errors=True)


def _lauf(basis: Path, original: Path, basiszustand: dict, echt: dict) -> int:

    abweichung = [n for n in basiszustand if basiszustand[n] != echt.get(n)]
    print("verify_docs_mutation.py — prüft den Wächter")
    print("=" * 72)
    if abweichung:
        print(f"HINWEIS: Kopie und Arbeitsbaum weichen ab bei Prüfung {abweichung}")
        for n in abweichung:
            print(f"  {n}: Kopie {basiszustand[n]} vs. echt {echt.get(n)}")
        print("  (Prüfung 3 darf abweichen: Verweise auf nicht kopierte Ordner.)")
        print()

    gefangen, entwischt, ohne_aussage = 0, [], []

    for m in MUTATIONEN:
        ist_gegenprobe = any(g in m.name for g in GEGENPROBE)
        erwartet = vd.BESTANDEN if ist_gegenprobe else vd.DURCHGEFALLEN

        if not m.anwenden(basis):
            entwischt.append((m, "Mutation nicht anwendbar"))
            print(f"[?   ] {m.nummer}. {m.name} — NICHT ANWENDBAR")
            _zuruecknehmen(basis)
            continue
        vd.setze_repo(basis)
        try:
            status = status_von(m.nummer)
        finally:
            vd.setze_repo(original)
            _zuruecknehmen(basis)

        # Aussagekräftig ist eine Mutation nur, wenn die Prüfung OHNE sie das
        # Gegenteil sagte. Das gilt für die Gegenprobe GENAUSO: ist die Prüfung
        # ohnehin rot, beweist ein weiteres Rot nichts über die Entschärfung.
        # Mein erster Entwurf nahm Gegenproben pauschal als aussagekräftig — und
        # meldete deshalb eine korrekt arbeitende Entschärfung als „entwischt".
        vorher = basiszustand.get(m.nummer)
        aussagekraeftig = vorher == vd.BESTANDEN

        if status == erwartet and aussagekraeftig:
            gefangen += 1
            print(f"[OK  ] {m.nummer}. {m.name}")
        elif status == erwartet:
            ohne_aussage.append((m, vorher))
            print(f"[—   ] {m.nummer}. {m.name} — richtig, aber Prüfung war "
                  f"vorher schon {vorher}")
        else:
            entwischt.append((m, f"meldete {status}, erwartet {erwartet}"))
            print(f"[FEHL] {m.nummer}. {m.name} — ENTWISCHT ({status})")

    print("=" * 72)
    pruefbar = len(MUTATIONEN) - len(ohne_aussage)
    print(f"{gefangen}/{pruefbar} aussagekräftige Mutationen korrekt "
          f"({len(ohne_aussage)} ohne Aussagekraft)")

    if ohne_aussage:
        print("\nNoch nicht nachgewiesen, weil die Prüfung ohnehin rot ist:")
        for m, vorher in ohne_aussage:
            print(f"  Prüfung {m.nummer} ({vorher}): {m.name}")

    if entwischt:
        print("\nDiese Defekte würde der Wächter NICHT melden:")
        for m, warum in entwischt:
            print(f"  Prüfung {m.nummer}: {m.name} — {warum}")
        return 1
    if gefangen == 0:
        print("\nDer Wächter ist NICHT abgenommen — keine Mutation war aussagekräftig.")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
