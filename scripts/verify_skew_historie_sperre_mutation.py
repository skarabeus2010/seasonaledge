#!/usr/bin/env python3
"""
verify_skew_historie_sperre_mutation.py — prüft den Wächter verify_skew_historie_sperre.py: baut bekannte Fehler wieder
ein und verlangt Rot. Mechanik (Sperre, Bytes, atomares Schreiben, frischer Bytecode-Cache) aus verify_twins_mutation.
Eine Mutation darf mehrere Stellen ändern (Liste von Paaren). Mutationen mit `nur_linux` greift nur die
Parallelitätsprüfung; ohne fcntl werden sie als UNGEPRÜFT ausgewiesen (mit --streng rot).
Exit des Wächters: 0 grün, 1 rot (= erkannt), 3 Absturz (= ungültig, kein Nachweis).
"""
from __future__ import annotations
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
from scripts.verify_twins_mutation import (_exklusiver_lauf, _zeilenende, _atomar_schreiben,  # noqa: E402
                                           python_probe, LF)

try:
    import fcntl  # noqa: F401
    LINUX = True
except ImportError:
    LINUX = False
STRENG = "--streng" in sys.argv
_WAECHTER = _ROOT / "scripts" / "verify_skew_historie_sperre.py"

# (Name, Datei, [(suchen, ersetzen), …], nur_linux)
MUTATIONEN = [
    ("unlesbare History wird wieder zur leeren", "shared/atomic_json.py",
     [("        raise HistorieDefekt(f\"{p.name} ist nicht lesbar: {str(e)[:120]}\") from e",
       "        return {}")], False),
    ("fehlende History immer neu angelegt", "shared/atomic_json.py",
     [("        if neu_erlaubt:\n            return {}", "        if True:\n            return {}")], False),
    ("aendern -> False wird ignoriert", "shared/atomic_json.py",
     [("        if aendern(hist) is False:\n            return None", "        aendern(hist)")], False),
    ("Sperre wird nicht genommen", "shared/atomic_json.py",
     [("                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)\n                    break",
       "                    break")], True),
    ("Lesen vor der Sperre", "shared/atomic_json.py",
     [("    fd = os.open(str(sp), os.O_RDWR | os.O_CREAT, 0o644)\n",
       "    _vorab = history_lesen(pfad, neu_erlaubt=True)\n    fd = os.open(str(sp), os.O_RDWR | os.O_CREAT, 0o644)\n"),
      ("        hist = history_lesen(pfad, neu_erlaubt=neu_erlaubt)\n        if aendern(hist) is False:",
       "        hist = _vorab\n        if aendern(hist) is False:")], True),
    ("Sperre vor danach gelöst (Snapshot ohne Sperre)", "shared/atomic_json.py",
     [("        write_json_atomic(pfad, hist)\n        if danach is not None:",
       "        write_json_atomic(pfad, hist)\n        if fcntl is not None:\n            fcntl.flock(fd, fcntl.LOCK_UN)\n"
       "        if danach is not None:")], True),
    ("Cron: Snapshot wieder vor der History", "scripts/compute_options_skew.py",
     [("        hist = history_aktualisieren(hp, _zusammenfuehren, danach=lambda _h: write_json_atomic(p, out))",
       "        write_json_atomic(p, out)\n        hist = history_aktualisieren(hp, _zusammenfuehren)")], False),
    ("Cron: fehlende History wird angelegt", "scripts/compute_options_skew.py",
     [("        hist = history_aktualisieren(hp, _zusammenfuehren, danach=lambda _h: write_json_atomic(p, out))",
       "        hist = history_aktualisieren(hp, _zusammenfuehren, danach=lambda _h: write_json_atomic(p, out), "
       "neu_erlaubt=True)")], False),
    ("Backfill: alte Gesamtstruktur zurückschreiben", "scripts/backfill_skew_massive.py",
     [("            neue = run_ticker(sym, key, a.years, a.every_n_td, history_lesen(hp, neu_erlaubt=neu_erlaubt),",
       "            _plan = history_lesen(hp, neu_erlaubt=neu_erlaubt)\n"
       "            neue = run_ticker(sym, key, a.years, a.every_n_td, _plan,"),
      ("                history_aktualisieren(hp, _anwenden, neu_erlaubt=neu_erlaubt)",
       "                _anwenden(_plan); write_json_atomic(hp, _plan)")], False),
    ("Backfill: ohne overwrite ersetzt ein vorhandenes Datum", "scripts/backfill_skew_massive.py",
     [("        uebernehmen = [r for r in neue if r.get(\"date\") not in da]", "        uebernehmen = list(neue)")],
     False),
    ("Backfill: overwrite ohne Punkte purgt trotzdem", "scripts/backfill_skew_massive.py",
     [("        if not neue:\n            alt = sum(", "        if False:\n            alt = sum(")], False),
    ("Backfill: defekte History -> weiter statt Abbruch", "scripts/backfill_skew_massive.py",
     [("            print(f\"[ABBRUCH] {e}\", flush=True)\n            return 1",
       "            print(f\"[ABBRUCH] {e}\", flush=True)\n            continue")], False),
    ("VRP: Planungsstand statt frischem Stand geschrieben", "scripts/backfill_skew_vrp.py",
     [("        geschrieben = history_aktualisieren(HISTORIE, _aendern)",
       "        _aendern(plan); write_json_atomic(HISTORIE, plan); geschrieben = plan")], False),
    ("VRP: --dry-run schreibt", "scripts/backfill_skew_vrp.py",
     [("        print(\"--dry-run: nichts geschrieben.\")\n        return 0",
       "        print(\"--dry-run: nichts geschrieben.\")\n        write_json_atomic(HISTORIE, plan)\n        return 0")],
     False),
    ("Reparatur: kein Abgleich mit der Freigabedatei", "scripts/backfill_skew_vrp.py",
     [("        if _kanonisch(frisch) != _kanonisch(vergleich):", "        if False:")], False),
    ("Reparatur: Anwenden setzt ein weiteres Feld", "scripts/backfill_skew_vrp.py",
     [("            arr[i][\"vrp_pts\"] = e[\"vrp_neu\"]\n",
       "            arr[i][\"vrp_pts\"] = e[\"vrp_neu\"]; arr[i][\"vrp_rv\"] = 0.0\n")], False),
    ("Reparatur: Zeilen wieder über das Datum statt über die Position", "scripts/backfill_skew_vrp.py",
     [("    if doppelt:", "    if False:"),
      ("            arr[i][\"vrp_pts\"] = e[\"vrp_neu\"]\n",
       "            for _z in arr:\n                if _z.get(\"date\") == e[\"date\"]:\n"
       "                    _z[\"vrp_pts\"] = e[\"vrp_neu\"]\n")], False),
    ("Reparatur: auch nicht normierte Zeilen", "scripts/backfill_skew_vrp.py",
     [("        if z.get(\"cm_mode\") not in (\"cm\", \"cm_extrap\"):", "        if False:")], False),
    ("Reparatur: doppelte Daten nicht geprüft", "scripts/backfill_skew_vrp.py",
     [("    if doppelt:", "    if False:")], False),
    ("Reparatur: fehlendes Feld wird zu null", "scripts/backfill_skew_vrp.py",
     [("            pruef[diff[\"ticker\"]][i].pop(\"vrp_pts\", None)",
       "            pruef[diff[\"ticker\"]][i][\"vrp_pts\"] = None")], False),
    ("Reparatur: RV-Grenze fehlt", "scripts/backfill_skew_vrp.py",
     [("        if \"vrp_neu\" in e and not (_RV_GRENZEN[0] < e[\"rv_neu\"] < _RV_GRENZEN[1]):", "        if False:")],
     False),
    ("Reparatur: Trockenlauf schreibt die History", "scripts/backfill_skew_vrp.py",
     [("        write_json_atomic(ziel, dict(diff, erstellt=zeit))",
       "        write_json_atomic(ziel, dict(diff, erstellt=zeit))\n        write_json_atomic(HISTORIE, {})")], False),
]


def main() -> int:
    unbemerkt, ungueltig, ungeprueft = [], [], []
    with _exklusiver_lauf():
        r0 = python_probe([_WAECHTER], capture_output=True, text=True, cwd=str(_ROOT))
        if r0.returncode != 0:
            print("[FAIL] Wächter ist schon ohne Mutation rot:\n" + r0.stdout[-2000:])
            return 1
        for nr, (name, datei, paare, nur_linux) in enumerate(MUTATIONEN, 1):
            if nur_linux and not LINUX:
                print(f"{nr:>2}. [UNGEPRÜFT] {name} — nur unter Linux prüfbar")
                ungeprueft.append(name); continue
            pfad = _ROOT / datei
            original = pfad.read_bytes()
            le = _zeilenende(original)
            neu = original
            ok = True
            for such, ersatz in paare:
                s, e = such.encode("utf-8").replace(LF, le), ersatz.encode("utf-8").replace(LF, le)
                if neu.count(s) != 1:
                    print(f"{nr:>2}. [UNGUELTIG] {name} — Anker {neu.count(s)}x: {such[:60]!r}")
                    ok = False; break
                neu = neu.replace(s, e, 1)
            if not ok:
                ungueltig.append(name); continue
            try:
                _atomar_schreiben(pfad, neu)
                r = python_probe([_WAECHTER], capture_output=True, text=True, cwd=str(_ROOT))
            finally:
                _atomar_schreiben(pfad, original)
                assert pfad.read_bytes() == original, f"{datei} nicht wiederhergestellt"
            if r.returncode == 1:
                print(f"{nr:>2}. [erkannt]   {name}")
            elif r.returncode == 3:
                print(f"{nr:>2}. [Absturz]   {name} — kein Nachweis"); ungueltig.append(name)
            else:
                print(f"{nr:>2}. [UNBEMERKT] {name}"); unbemerkt.append(name)
    print()
    if unbemerkt or ungueltig or (STRENG and ungeprueft):
        print(f"[FAIL] unbemerkt {len(unbemerkt)}, ungültig {len(ungueltig)}, ungeprüft {len(ungeprueft)} "
              f"von {len(MUTATIONEN)}")
        return 1
    print(f"[OK] {len(MUTATIONEN) - len(ungeprueft)} Mutationen erkannt"
          + (f", {len(ungeprueft)} ungeprüft (nur Linux)" if ungeprueft else "") + ".")
    return 0


if __name__ == "__main__":
    sys.exit(main())
