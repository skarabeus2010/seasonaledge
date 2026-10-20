#!/usr/bin/env python3
"""verify_mail_events_mutation.py — prueft verify_mail_events.py.

Jede Mutation BENENNT die Pruefung, die sie reissen muss. Mechanik aus
verify_twins_mutation. Exit des Waechters: 0 gruen, 1 rot (= erkannt), 3 Absturz
(= ungueltig).
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
from scripts.verify_twins_mutation import (_atomar_schreiben, _exklusiver_lauf,  # noqa: E402
                                           _zeilenende, python_probe, LF)

_WAECHTER = _ROOT / "scripts" / "verify_mail_events.py"
D = "shared/daily_report.py"
MIND_PRUEFUNGEN = 16


def _umfang(ausgabe: str) -> int:
    treffer = [z for z in (ausgabe or "").splitlines() if z.startswith("PROBE-ENDE")]
    if not treffer:
        return -1
    try:
        return int(treffer[-1].split()[1])
    except (IndexError, ValueError):
        return -1


MUTATIONEN = [
    ("VIX-Ereignis gar nicht angelegt", D,
     [('            events.append({\n                "date": sett,\n                "type": "VIXPIRATION",\n',
       '            continue\n            events.append({\n                "date": sett,\n                "type": "VIXPIRATION",\n')],
     "am 20.10. steht genau ein VIX-Settlement im Fenster"),

    ("Fensterpruefung entfernt", D,
     [("            if not (window_start <= sett_d <= window_end):\n                continue\n",
       "            if False:\n                continue\n")],
     "am 1.10. liegt der 21.10. nicht im 5-Tage-Fenster"),

    ("nominaler Termin statt Settlement", D,
     [('            sett = e.get("settlement")\n', '            sett = e.get("nominal")\n')],
     "die Mail nennt den 19.05., nicht den nominalen 20.05."),

    ("Typ als OPEX getarnt", D,
     [('                "type": "VIXPIRATION",\n', '                "type": "OPEX",\n')],
     "der Ereignistyp ist eigenstaendig, nicht OPEX"),

    ("Ausfall der Quelle wird verschluckt", D,
     [('    except Exception as e:\n        error_logger.error(f"[daily_report] VIXpiration: {e}")\n',
       '    except Exception as e:\n        pass\n')],
     "aber eine Logzeile — der Ausfall ist nicht stumm"),
]

UNGUELTIG_ERWARTET = [
    ("Kommentar geaendert (wirkungslos)", D,
     [("    # VIXpiration — Nutzerentscheidung 2026-10-20: aufnehmen.",
       "    # VIXpiration — Nutzerentscheidung vom 20.10.2026: aufnehmen.")]),
]


def _anwenden(original: bytes, paare, nr: int, name: str):
    le = _zeilenende(original)
    neu = original
    for such, ersatz in paare:
        s = such.encode("utf-8").replace(LF, le)
        e = ersatz.encode("utf-8").replace(LF, le)
        if neu.count(s) != 1:
            print(f"{nr:>2}. [UNGUELTIG] {name} — Anker {neu.count(s)}x: {such[:70]!r}")
            return None
        neu = neu.replace(s, e, 1)
    return neu


def main() -> int:
    unbemerkt, ungueltig = [], []
    with _exklusiver_lauf():
        r0 = python_probe([_WAECHTER], capture_output=True, text=True, cwd=str(_ROOT))
        if r0.returncode != 0:
            print("[FAIL] Waechter ist schon ohne Mutation rot:\n" + (r0.stdout or "")[-2000:])
            return 1
        if _umfang(r0.stdout) < MIND_PRUEFUNGEN:
            print("[FAIL] Ausgangslauf unvollstaendig (%d)" % _umfang(r0.stdout))
            return 1
        print("Ausgangslauf: %d Pruefungen, Endmarker erreicht." % _umfang(r0.stdout))

        for nr, (name, datei, paare, pruefung) in enumerate(MUTATIONEN, 1):
            pfad = _ROOT / datei
            original = pfad.read_bytes()
            neu = _anwenden(original, paare, nr, name)
            if neu is None:
                ungueltig.append(name)
                continue
            try:
                _atomar_schreiben(pfad, neu)
                r = python_probe([_WAECHTER], capture_output=True, text=True, cwd=str(_ROOT))
            finally:
                _atomar_schreiben(pfad, original)
                assert pfad.read_bytes() == original, f"{datei} nicht wiederhergestellt"
            if r.returncode == 3:
                print(f"{nr:>2}. [Absturz]   {name} — kein Nachweis")
                ungueltig.append(name)
                continue
            if r.returncode != 1:
                print(f"{nr:>2}. [UNBEMERKT] {name} (Exit {r.returncode})")
                unbemerkt.append(name)
                continue
            if _umfang(r.stdout) < MIND_PRUEFUNGEN:
                print(f"{nr:>2}. [UNGUELTIG] {name} — Lauf unvollstaendig "
                      f"({_umfang(r.stdout)})")
                ungueltig.append(name)
                continue
            if [z for z in (r.stdout or "").splitlines()
                    if z.startswith("  FEHL") and pruefung in z]:
                print(f"{nr:>2}. [erkannt]   {name}  ->  {pruefung}")
            else:
                print(f"{nr:>2}. [UNBEMERKT] {name} — rot, aber nicht an "
                      f"\"{pruefung}\"; rot war:")
                for z in (r.stdout or "").splitlines():
                    if z.startswith("  FEHL"):
                        print("        " + z.strip())
                unbemerkt.append(name)

        for nr, (name, datei, paare) in enumerate(UNGUELTIG_ERWARTET, len(MUTATIONEN) + 1):
            pfad = _ROOT / datei
            original = pfad.read_bytes()
            neu = _anwenden(original, paare, nr, name)
            if neu is None:
                ungueltig.append(name)
                continue
            try:
                _atomar_schreiben(pfad, neu)
                r = python_probe([_WAECHTER], capture_output=True, text=True, cwd=str(_ROOT))
            finally:
                _atomar_schreiben(pfad, original)
                assert pfad.read_bytes() == original, f"{datei} nicht wiederhergestellt"
            if r.returncode == 0 and _umfang(r.stdout) >= MIND_PRUEFUNGEN:
                print(f"{nr:>2}. [wirkungslos, richtig] {name}")
            else:
                print(f"{nr:>2}. [FALSCHALARM] {name} (Exit {r.returncode})")
                unbemerkt.append(name)

    gesamt = len(MUTATIONEN) + len(UNGUELTIG_ERWARTET)
    print()
    if unbemerkt or ungueltig:
        print(f"[FAIL] unbemerkt {len(unbemerkt)}, ungueltig {len(ungueltig)} von {gesamt}")
        return 1
    print(f"[OK] Alle {len(MUTATIONEN)} Mutationen an der benannten Pruefung erkannt, "
          f"{len(UNGUELTIG_ERWARTET)} wirkungslose richtig durchgelassen.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
