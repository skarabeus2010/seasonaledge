#!/usr/bin/env python3
"""
verify_gex_session_mutation.py — prüft den Wächter verify_gex_session.py: baut bekannte Fehler wieder ein und verlangt
Rot. Mechanik aus verify_twins_mutation (Sperre, Bytes, atomares Schreiben, frischer Bytecode-Cache).
Exit des Wächters: 0 grün, 1 rot (= erkannt), 3 Absturz (= ungültig, kein Nachweis).
"""
from __future__ import annotations
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
from scripts.verify_twins_mutation import (_exklusiver_lauf, _zeilenende, _atomar_schreiben,  # noqa: E402
                                           python_probe, LF)

_WAECHTER = _ROOT / "scripts" / "verify_gex_session.py"

GM, KL, IV = "scripts/snapshot_gex_massive.py", "scripts/compute_key_levels.py", "scripts/compute_iv_surface.py"
HC = "scripts/daily_health_check.py"

# (Name, Datei, [(suchen, ersetzen), …])
MUTATIONEN = [
    ("GEX: DTE wieder ab Lauftag", GM,
     [("        dte = (date.fromisoformat(ex) - session).days\n", "        dte = (date.fromisoformat(ex) - date.today()).days\n")]),
    ("GEX: am Sessiontag verfallene Kontrakte bleiben", GM,
     [("        if dte <= 0:\n            continue\n        out.append", "        if dte < 0:\n            continue\n        out.append")]),
    ("GEX: Stempel wieder Lauftag", GM,
     [("    stamp = session.isoformat()\n", "    stamp = date.today().isoformat()\n")]),
    ("GEX: Archiv wieder im alten Ordner", GM,
     [('    hist = _DATA / "gex_history_session"\n', '    hist = _DATA / "gex_history"\n')]),
    ("GEX: kein EOD-Schutz", GM,
     [('            pruefe_eod_fenster("snapshot_gex_massive")\n', '            pass\n')]),
    ("GEX: Spot-Balken anderer Tage akzeptiert", GM,
     [("    if tag != session:\n", "    if False:\n")]),
    ("GEX: Chain-Horizont ab Lauftag", GM,
     [("    hi = (session + timedelta(days=hi_days)).isoformat()\n", "    hi = (date.today() + timedelta(days=hi_days)).isoformat()\n")]),
    ("Key Levels: GEX anderer Session übernommen", KL,
     [('    if d.get("session") != session.isoformat():\n', '    if False:\n')]),
    ("Key Levels: alter Stempel übernommen", KL,
     [('    if d.get("stempel_art") != "session":\n', '    if False:\n')]),
    ("Key Levels: kein EOD-Schutz", KL,
     [('    if write:\n        pruefe_eod_fenster("compute_key_levels")\n', '    if False:\n        pruefe_eod_fenster("compute_key_levels")\n')]),
    ("Key Levels: DTE ab Lauftag", KL,
     [("    today = session; by = {}\n", "    today = date.today(); by = {}\n")]),
    ("Key Levels: Chain-Horizont ab Lauftag", KL,
     [("    hi = (session + timedelta(days=_MAXDTE)).isoformat()", "    hi = (date.today() + timedelta(days=_MAXDTE)).isoformat()")]),
    ("IV-Surface: kein EOD-Schutz", IV,
     [('    if write:\n        pruefe_eod_fenster("compute_iv_surface")\n', '    if False:\n        pruefe_eod_fenster("compute_iv_surface")\n')]),
    ("IV-Surface: DTE ab Lauftag", IV,
     [("    today = session; by = {}; spot = None", "    today = date.today(); by = {}; spot = None")]),
    ("IV-Surface: Chain-Horizont ab Lauftag", IV,
     [("    hi = (session + timedelta(days=_MAXDTE)).isoformat()", "    hi = (date.today() + timedelta(days=_MAXDTE)).isoformat()")]),
    ("Key-Levels-Seite: Datum wieder Lauftag", "landing/pages/key-levels.html",
     [("KL_DATE=d&&(d.session||d.generated);", "KL_DATE=d&&d.generated;")]),
    ("Dealer-Seite: Profil anderer Session gezeigt", "landing/pages/dealer-positioning.html",
     [("profiles[t]=(soll&&(d.session||d.date)===soll)?d.profile:null", "profiles[t]=d.profile")]),
    ("Health: Datum nach der erwarteten Session gilt als aktuell", HC,
     [("    elif gd_d > erwartet:\n", "    elif False:\n")]),
    ("Health: Nicht-Handelstag als Session akzeptiert", HC,
     [('    elif not _itd(gd_d, "NYSE"):\n', '    elif False:\n')]),
    ("Options-Skew: pc_ratio.date wieder Lauftag", "scripts/compute_options_skew.py",
     [('"index": _pc(_is_idx), "date": session}', '"index": _pc(_is_idx), "date": date.today().isoformat()}')]),
    ("Archivleser: Lauftag-Archiv zuerst", "scripts/compare_flashalpha_gex.py",
     [('(("gex_history_session", "session"), ("gex_history", "lauftag"))',
       '(("gex_history", "lauftag"), ("gex_history_session", "session"))')]),
    ("Health: nur die Session-Bewertung zählt", HC,
     [("    return max(a_status, s_status, key=rang.get), ", "    return s_status, ")]),
    ("Health: alter Stempel ohne Folge", HC,
     [('    if gd.get("stempel_art") != "session":\n        s_status', '    if False:\n        s_status')]),
    ("Health: Kalendertage statt Sessions", HC,
     [('        rueck = (sum(1 for k in range(1, (erwartet - gd_d).days + 1) if _itd(gd_d + timedelta(days=k), "NYSE"))\n',
       '        rueck = ((erwartet - gd_d).days\n')]),
    ("Yahoo-Schreiber läuft wieder", "scripts/snapshot_gex.py",
     [("    return 1\n    results, charts, failed", "    results, charts, failed")]),
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
