#!/usr/bin/env python3
"""verify_kursmuster_mutation.py — prüft verify_kursmuster.py: baut bekannte Fehler in shared/kursmuster.py, die
Mailvorlage und daily_report.py ein und verlangt Rot. Mechanik aus verify_twins_mutation. Exit des Wächters:
0 grün, 1 rot (= erkannt), 3 Absturz (= ungültig)."""
from __future__ import annotations
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
from scripts.verify_twins_mutation import (_exklusiver_lauf, _zeilenende, _atomar_schreiben,  # noqa: E402
                                           python_probe, LF)

_WAECHTER = _ROOT / "scripts" / "verify_kursmuster.py"
M, V = "shared/kursmuster.py", "scripts/templates/daily_report.html.j2"

MUTATIONEN = [
    ("Smash mit ≤ statt <", M, [("    if c < lv:\n", "    if c <= lv:\n")]),
    ("Kauf/Verkauf vertauscht", M, [("        return KAUF\n    if c > hv:\n        return VERKAUF\n",
                                     "        return VERKAUF\n    if c > hv:\n        return KAUF\n")]),
    ("Kursbasis nicht geprüft", M, [("    if not (gueltige_kerze(vorher) and gueltige_kerze(jetzt) and gleiche_basis(vorher, jetzt)):",
                                     "    if not (gueltige_kerze(vorher) and gueltige_kerze(jetzt)):")]),
    ("Volumen nicht geprüft", M, [("and v is not None and v > 0", "")]),
    ("Session nicht geprüft", M, [("    if str(jetzt.get(\"date\")) != s:\n        return None", "    if False:\n        return None")]),
    ("Lücke nicht geprüft", M, [("        if vorherige(s, boerse, einschliesslich=False).isoformat() != str(vorher.get(\"date\")):",
                                 "        if False:")]),
    ("Universum nicht geprüft", M, [("    if not im_universum(ticker) or not kerzen", "    if not kerzen")]),
    ("Vorlage: Kauf rot", V, [("class=\"{{ 'up' if r.muster == 'kauf' else 'dn' if r.muster == 'verkauf' else 'nu' }}\"",
                               "class=\"{{ 'dn' if r.muster == 'kauf' else 'up' if r.muster == 'verkauf' else 'nu' }}\"")]),
    ("Vorlage: Spalte fehlt im Kopf", V, [('Nicht im Score.">Muster</th>', 'Nicht im Score.">BO2</th>')]),
]


def main() -> int:
    unbemerkt, ungueltig = [], []
    with _exklusiver_lauf():
        r0 = python_probe([_WAECHTER], capture_output=True, text=True, cwd=str(_ROOT))
        if r0.returncode != 0:
            print("[FAIL] Wächter ist schon ohne Mutation rot:\n" + r0.stdout[-2000:])
            return 1
        for nr, (name, datei, paare) in enumerate(MUTATIONEN, 1):
            pfad = _ROOT / datei
            original = pfad.read_bytes()
            le = _zeilenende(original)
            neu, ok = original, True
            for such, ersatz in paare:
                s, e = such.encode("utf-8").replace(LF, le), ersatz.encode("utf-8").replace(LF, le)
                if neu.count(s) != 1:
                    print(f"{nr:>2}. [UNGUELTIG] {name} — Anker {neu.count(s)}x: {such[:60]!r}")
                    ok = False
                    break
                neu = neu.replace(s, e, 1)
            if not ok:
                ungueltig.append(name)
                continue
            try:
                _atomar_schreiben(pfad, neu)
                r = python_probe([_WAECHTER], capture_output=True, text=True, cwd=str(_ROOT))
            finally:
                _atomar_schreiben(pfad, original)
                assert pfad.read_bytes() == original, f"{datei} nicht wiederhergestellt"
            if r.returncode == 1:
                print(f"{nr:>2}. [erkannt]   {name}")
            elif r.returncode == 3:
                print(f"{nr:>2}. [Absturz]   {name} — kein Nachweis")
                ungueltig.append(name)
            else:
                print(f"{nr:>2}. [UNBEMERKT] {name}")
                unbemerkt.append(name)
    print()
    if unbemerkt or ungueltig:
        print(f"[FAIL] unbemerkt {len(unbemerkt)}, ungültig {len(ungueltig)} von {len(MUTATIONEN)}")
        return 1
    print(f"[OK] Alle {len(MUTATIONEN)} Mutationen erkannt.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
