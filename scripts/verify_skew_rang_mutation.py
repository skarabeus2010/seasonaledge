#!/usr/bin/env python3
"""
verify_skew_rang_mutation.py — prüft den Wächter verify_skew_rang.py: baut bekannte Fehler wieder ein und verlangt Rot.
Mechanik aus verify_twins_mutation (Sperre, Bytes, atomares Schreiben, frischer Bytecode-Cache).
Exit des Wächters: 0 grün, 1 rot (= erkannt), 3 Absturz (= ungültig, kein Nachweis).
"""
from __future__ import annotations
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
from scripts.verify_twins_mutation import (_exklusiver_lauf, _zeilenende, _atomar_schreiben,  # noqa: E402
                                           python_probe, LF)

_WAECHTER = _ROOT / "scripts" / "verify_skew_rang.py"
K, SEITE, MAIL = "shared/skew_rang.py", "landing/pages/skew.html", "shared/daily_report.py"

MUTATIONEN = [
    ("Fenster ab der Uhr statt ab der Session", K,
     [("    ab = (date.fromisoformat(session) - timedelta(days=fenster)).isoformat()",
       "    ab = (date.today() - timedelta(days=fenster)).isoformat()")]),
    ("Fenstergrenze S−W ausgeschlossen", K,
     [('for e in alle if ab <= e["date"])', 'for e in alle if ab < e["date"])')]),
    ("Session-Regel vor dem Metrikfilter (ältere Werte rücken nach)", K,
     [("        if reihe and reihe[-1][0] == session and len(reihe) >= MIN_NORM:",
       "        if reihe and w and w[-1][0] == session and len(reihe) >= MIN_NORM:")]),
    ("Python-round statt halb nach oben", K,
     [("    return int(math.floor(v + 0.5))", "    return int(round(v))")]),
    ("Mindestzahl 19", K, [("MIN_NORM = 20", "MIN_NORM = 19")]),
    ("IV aus ATM statt Mittel der Flügel", K,
     [('"iv": (ci + pi) / 2 if gueltig(ci) and gueltig(pi) else None,', '"iv": atm,')]),
    ("nicht normierte Zeilen zählen mit", K, [('and e.get("cm_mode") in NORMIERT and ', "and ")]),
    ("Put-Zeta über die alte Näherung ohne ATM-Anker", K,
     [('else _diff(pi, atm, 100.0)', 'else _diff(pi, ci, 50.0)')]),
    ("doppelte Daten erlaubt", K, [('    if len({e["date"] for e in alle}) != len(alle):\n        return None',
                                    "    if False:\n        return None")]),
    ("bool gilt als Messwert", K,
     [("return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)",
       "return isinstance(x, (int, float)) and math.isfinite(x)")]),
    ("gemeinsames n statt je Metrik", K,
     [("            aus[m] = _einzeln(reihe)\n", "            aus[m] = dict(_einzeln(reihe), n=len(w))\n")]),
    ("Duplikat sperrt nur das betroffene Fenster", K,
     [('    if len({e["date"] for e in alle}) != len(alle):',
       '    if len({e["date"] for e in alle if e["date"] >= ab}) != len([e for e in alle if e["date"] >= ab]):')]),
    ("ungültiges Kalenderdatum zählt", K,
     [("        return date.fromisoformat(d).isoformat() == d", "        return True")]),
    ("Duplikat ohne Meldung", K,
     [('        meld.append("doppelte Daten: " + ", ".join(doppelt[:5]))', "        pass")]),
    ("Seite: Skew-Spalte liest den IV-Rang", SEITE,
     [("function _skewMetric(tk){ var r=_rangOf(tk); return r?_pick(r.skew):null; }",
       "function _skewMetric(tk){ var r=_rangOf(tk); return r?_pick(r.iv):null; }")]),
    ("Cron: rang_session = Lauftag", "scripts/compute_options_skew.py",
     [('            out["rang_session"] = today\n', '            out["rang_session"] = date.today().isoformat()\n')]),
    ("Seite: Rang ohne Session-Abgleich", SEITE,
     [("SKEW_RANG=(d.rang&&d.rang_session&&d.rang_session===d.session)?d.rang:null;", "SKEW_RANG=d.rang||null;")]),
    ("Seite: Modus ignoriert (immer Rank)", SEITE,
     [("return m?(SKEW_MODE==='pctl'?m.pctl:m.rank):null;", "return m?m.rank:null;")]),
    ("Seite: Fenster ignoriert (immer 1 J.)", SEITE, [("r[String(SKEW_WIN)]", "r['365']")]),
    ("Mail: ohne Session-Abgleich", MAIL,
     [('                if d.get("rang_session") == d.get("session") == erwartet:', "                if True:")]),
    ("Mail: 3-M-Fenster statt 1 J.", MAIL, [('pc = ((je.get("365") or {})', 'pc = ((je.get("92") or {})')]),
    ("Vorlage: wieder grün/rot", "scripts/templates/daily_report.html.j2",
     [('<td align="center" class="nu" style="font-weight:700;">{% if r.skew_pts is not none %}',
       '<td align="center" class="{{ \'up\' if r.skew_pts is not none and r.skew_pts >= 0 else \'dn\' }}" style="font-weight:700;">{% if r.skew_pts is not none %}')]),
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
