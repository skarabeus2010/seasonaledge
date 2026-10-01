#!/usr/bin/env python3
"""
verify_security_mutation.py — prüft den WÄCHTER, nicht den Code.

    py -3.14 scripts/verify_security_mutation.py

Baut jeden Defekt, den `verify_security.py` fangen soll, absichtlich in eine **Kopie**
des Baums ein und verlangt, dass die zugehörige Prüfung DURCHGEFALLEN meldet. Eine
Mutation, die unbemerkt bleibt, ist eine Lücke im Wächter.

Warum das nötig ist: beim Bau dieses Wächters meldete Prüfung 9 zunächst BESTANDEN,
obwohl der Defekt da war — sie suchte das Wort „role" irgendwo in der Datei, während
der Check nur im Fallback-Zweig lag. **Ohne Mutationsprobe ist „der Test besteht" eine
Aussage über den Test.**

Es wird **keine Produktionsdatei** geschrieben. Jede Mutation läuft in einem
temporären Verzeichnis; die Prüfung richtet sich per `setze_repo()` darauf. Das
vermeidet den Windows-Fall aus v65.1, in dem eine gesperrte Datei eine mutierte
Produktionsdatei im Arbeitsbaum zurückließ.

Exit 0 = alle Mutationen gefangen. Exit 1 = mindestens eine blieb unbemerkt.
"""
from __future__ import annotations

import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

import verify_security as vs  # noqa: E402  (nach sys.path-Anpassung)

# Diese Verzeichnisse braucht der Wächter. Alles andere wird nicht kopiert —
# ein vollständiger Repo-Kopie wäre langsam und unnötig.
RELEVANT = ("scripts", ".github/workflows", "deploy", "supabase", "shared", "landing")


@dataclass
class Mutation:
    nummer: int           # Prüfungsnummer, die sie fangen muss
    name: str
    anwenden: Callable[[Path], bool]   # mutiert den Baum, True = angewandt


def _datei(baum: Path, rel: str) -> Path:
    return baum / rel


def _ersetze(baum: Path, rel: str, alt: str, neu: str) -> bool:
    p = _datei(baum, rel)
    if not p.is_file():
        return False
    s = p.read_text(encoding="utf-8", errors="replace")
    if alt not in s:
        return False
    p.write_text(s.replace(alt, neu, 1), encoding="utf-8")
    return True


def _anhaengen(baum: Path, rel: str, text: str) -> bool:
    p = _datei(baum, rel)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(text)
    return True


# ── Die Mutationen ──────────────────────────────────────────────────────────
# Je Prüfung mindestens eine. Formuliert so, dass sie der Fehler ist, den jemand
# versehentlich einbaut — nicht ein konstruierter Sonderfall.

MUTATIONEN: list[Mutation] = [
    Mutation(1, "Policy ohne TO neu eingefügt", lambda b: _anhaengen(
        b, "scripts/_mutation.sql",
        '\nCREATE POLICY "offen" ON prices FOR ALL USING (TRUE) WITH CHECK (TRUE);\n')),

    Mutation(1, "Policy ohne TO, aber in einem Kommentar DAVOR erklärt "
                "(Kommentare dürfen nicht täuschen)", lambda b: _anhaengen(
        b, "scripts/_mutation2.sql",
        '\n-- CREATE POLICY "beispiel" ON prices FOR ALL USING (TRUE);\n'
        'CREATE POLICY "echt" ON prices FOR ALL USING (TRUE);\n')),

    Mutation(2, "anon darf SELECT auf eine private Tabelle", lambda b: _anhaengen(
        b, "scripts/_mutation3.sql",
        '\nCREATE POLICY "lesen" ON subscribers FOR SELECT TO anon USING (TRUE);\n')),

    Mutation(2, "nutzerbezogene Policy OHNE auth.uid()-Bindung", lambda b: _anhaengen(
        b, "scripts/_mutation4.sql",
        '\nCREATE POLICY "alle" ON user_watchlists FOR SELECT TO authenticated\n'
        '    USING (TRUE);\n')),

    Mutation(3, "Geheimnis mit fest eingebautem Rückfall", lambda b: _anhaengen(
        b, "shared/_mutation.py",
        '\nAPI_SECRET = "irgendein-fester-wert-123"\n')),

    Mutation(4, "Workflow-Eingabe im Shellrumpf", lambda b: _anhaengen(
        b, ".github/workflows/_mutation.yml",
        'name: Mutation\n'
        'on:\n  workflow_dispatch:\n    inputs:\n      ziel:\n        type: string\n'
        'jobs:\n  lauf:\n    runs-on: ubuntu-latest\n    steps:\n'
        '      - uses: appleboy/ssh-action@v1\n        with:\n'
        '          script: |\n'
        '            ZIEL="${{ github.event.inputs.ziel }}"\n'
        '            echo "$ZIEL"\n')),

    Mutation(5, "TLS-Prüfung abgeschaltet", lambda b: _anhaengen(
        b, "scripts/_mutation_tls.py",
        '\nimport requests\n'
        'requests.get("https://example.invalid", verify=False)\n')),

    Mutation(6, "Edge Function nimmt user_id aus dem Body ohne JWT",
             lambda b: _anhaengen(
        b, "supabase/functions/_mutation/index.ts",
        'const supabase = createClient(Deno.env.get("SUPABASE_URL"),\n'
        '  Deno.env.get("SUPABASE_SERVICE_ROLE_KEY"))\n'
        'Deno.serve(async (req) => {\n'
        '  const { user_id } = await req.json()\n'
        '  return new Response(user_id)\n'
        '})\n')),

    Mutation(7, "Empfängeradresse in eine öffentliche Tabelle geschrieben",
             lambda b: _anhaengen(
        b, "scripts/_mutation_log.py",
        '\ndef schreibe(client, zeilen):\n'
        '    email = zeilen[0]["email"]\n'
        '    client.table("market_events").insert({"detail": email}).execute()\n')),

    Mutation(8, "nginx-location mit eigenem add_header ohne Schutzheader",
             lambda b: _ersetze(
        b, "deploy/nginx.conf",
        "    location = /robots.txt {",
        "    location = /mutation-test {\n"
        "        add_header Cache-Control \"public, max-age=60\";\n"
        "        return 204;\n"
        "    }\n\n"
        "    location = /robots.txt {")),

    Mutation(9, "Rollencheck des Frontend-Keys entfernt", lambda b: _ersetze(
        b, "deploy/inject_credentials.sh",
        "ROLE=$(", "ROLE_UNGENUTZT=$(")),
]


def baum_vorbereiten(ziel: Path) -> None:
    for unter in RELEVANT:
        quelle = REPO / unter
        if not quelle.exists():
            continue
        zielpfad = ziel / unter
        zielpfad.parent.mkdir(parents=True, exist_ok=True)
        if quelle.is_dir():
            shutil.copytree(
                quelle, zielpfad,
                ignore=shutil.ignore_patterns("*.json", "__pycache__", "*.png",
                                              "*.jpg", "en", "worktrees"),
                dirs_exist_ok=True)
        else:
            shutil.copy2(quelle, zielpfad)


def status_von(nummer: int) -> str:
    """Führt genau eine Prüfung aus und gibt ihren Status zurück."""
    for e in vs.alle_pruefungen(live=False):
        if e.nummer == nummer:
            return e.status
    raise AssertionError(f"Prüfung {nummer} existiert nicht")


def main() -> int:
    original = vs.REPO
    gefangen, entwischt, ohne_aussage = 0, [], []

    # Vorbedingung: ohne Mutation muss der Wächter auf dem KOPIERTEN Baum dasselbe
    # sagen wie auf dem echten. Sonst prüft der Mutationstest eine Fiktion.
    with tempfile.TemporaryDirectory(prefix="sec-basis-") as tmp:
        basis = Path(tmp)
        baum_vorbereiten(basis)
        vs.setze_repo(basis)
        basiszustand = {n: status_von(n) for n in range(1, 10)}
    vs.setze_repo(original)
    echt = {e.nummer: e.status for e in vs.alle_pruefungen(live=False)
            if e.nummer < 10}
    abweichung = {n for n in basiszustand if basiszustand[n] != echt.get(n)}
    if abweichung:
        print("WARNUNG: Kopie und Arbeitsbaum weichen ab bei Prüfung "
              f"{sorted(abweichung)} — die Mutationen prüfen dann einen anderen "
              "Zustand als die Produktion.")
        for n in sorted(abweichung):
            print(f"  {n}: Kopie {basiszustand[n]} vs. echt {echt.get(n)}")

    print("verify_security_mutation.py — prüft den Wächter")
    print("=" * 72)

    for m in MUTATIONEN:
        with tempfile.TemporaryDirectory(prefix="sec-mut-") as tmp:
            baum = Path(tmp)
            baum_vorbereiten(baum)
            if not m.anwenden(baum):
                entwischt.append((m, "Mutation konnte nicht angewandt werden"))
                print(f"[?   ] {m.nummer}. {m.name} — NICHT ANWENDBAR")
                continue
            vs.setze_repo(baum)
            try:
                status = status_von(m.nummer)
            finally:
                vs.setze_repo(original)

        # ⚠️ Der entscheidende Vorbehalt: war die Prüfung OHNE Mutation schon rot,
        # beweist ihr Rotwerden nichts. Das wäre die bequeme Selbsttäuschung —
        # 11/11 „gefangen", obwohl keine einzige Mutation gewirkt haben muss.
        vorher = basiszustand.get(m.nummer)
        aussagekraeftig = vorher == vs.BESTANDEN

        if status == vs.DURCHGEFALLEN and aussagekraeftig:
            gefangen += 1
            print(f"[OK  ] {m.nummer}. {m.name}")
        elif status == vs.DURCHGEFALLEN:
            ohne_aussage.append((m, vorher))
            print(f"[—   ] {m.nummer}. {m.name} — rot, aber Prüfung war "
                  f"vorher schon {vorher}")
        else:
            entwischt.append((m, f"Prüfung meldete {status}"))
            print(f"[FEHL] {m.nummer}. {m.name} — ENTWISCHT ({status})")

    print("=" * 72)
    pruefbar = len(MUTATIONEN) - len(ohne_aussage)
    print(f"{gefangen}/{pruefbar} aussagekräftige Mutationen gefangen "
          f"({len(ohne_aussage)} ohne Aussagekraft)")

    if ohne_aussage:
        print("\nNoch nicht nachgewiesen, weil die Prüfung ohnehin rot ist —")
        print("sobald der echte Defekt behoben ist, wird die Mutation aussagekräftig:")
        for m, vorher in ohne_aussage:
            print(f"  Prüfung {m.nummer} ({vorher}): {m.name}")

    if entwischt:
        print("\nDiese Defekte würde der Wächter NICHT melden:")
        for m, warum in entwischt:
            print(f"  Prüfung {m.nummer}: {m.name} — {warum}")
        return 1
    if gefangen == 0:
        # Nichts entwischt, aber auch nichts bewiesen. Dasselbe Prinzip wie im
        # Wächter selbst: was nicht gemessen werden konnte, ist nicht bestanden.
        print("\nDer Wächter ist damit NICHT abgenommen — es war keine Mutation "
              "aussagekräftig.")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
