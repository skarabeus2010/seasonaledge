#!/usr/bin/env python3
"""verify_williams_muster_mutation.py — prüft den Wächter verify_williams_muster.py: baut bekannte Fehler in
scripts/research/williams_muster.py ein und verlangt Rot. Mechanik aus verify_twins_mutation (Sperre, Bytes,
atomares Schreiben, frischer Bytecode-Cache). Wächter-Exit: 0 grün, 1 rot (= erkannt), 3 Absturz (= ungültig).
"""
from __future__ import annotations
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
from scripts.verify_twins_mutation import (_exklusiver_lauf, _zeilenende, _atomar_schreiben,  # noqa: E402
                                           python_probe, LF)

_WAECHTER = _ROOT / "scripts" / "verify_williams_muster.py"
S = "scripts/research/williams_muster.py"

MUTATIONEN = [
    ("Kursbasis nicht geprüft", S, [("        basis = diff <= tol\n", "        basis = np.ones_like(diff, dtype=bool)\n")]),
    ("Kopie nicht ausgeschlossen", S,
     [("    gueltig = endlich & positiv & geometrie & vol_ok & handelstag & ~kopie\n",
       "    gueltig = endlich & positiv & geometrie & vol_ok & handelstag\n")]),
    ("Lücke im Börsenkalender ignoriert", S,
     [("        folge = pos[1:] == pos[:-1] + 1\n", "        folge = np.ones(n - 1, dtype=bool)\n")]),
    ("Fenster eine Sitzung zu kurz", S,
     [("        fenster[t] = (pre[t + H_MAX + 1] - pre[t]) == H_MAX + 1\n",
       "        fenster[t] = (pre[t + H_MAX] - pre[t]) == H_MAX\n")]),
    ("Smash mit ≤ statt <", S, [('        z["SMASH_K"] = c < lv\n', '        z["SMASH_K"] = c <= lv\n')]),
    ("BODY mit ≤ 20", S, [("round(abs(o[t] - c[t]) / (h[t] - l[t]) * 100, 1) < 20",
                           "round(abs(o[t] - c[t]) / (h[t] - l[t]) * 100, 1) <= 20")]),
    ("Stopp-Kurs immer Schwelle (Lücke ignoriert)", S,
     [("            kurs = np.maximum(o[t + 1], h[t])\n", "            kurs = h[t]\n")]),
    ("Stopp löst bei Gleichstand aus", S,
     [("            ausgeloest = h[t + 1] > h[t]\n", "            ausgeloest = h[t + 1] >= h[t]\n")]),
    ("Short-Sicht bei R_bek vergessen", S, [("        y[t] = sicht * bek\n", "        y[t] = bek\n")]),
    ("Open-Einstieg zählt den Tag t+1 doppelt", S,
     [("    rest = P[t + hz + 1] - P[t + 2]", "    rest = P[t + hz + 1] - P[t + 1]")]),
    ("Abschnitt prüft t+10 nicht", S,
     [('        if r["d"][k] >= a and r["d"][k + H_MAX] <= b:', '        if r["d"][k] >= a and r["d"][k] <= b:')]),
    ("Mindestkontrolle 19", S, [("MIN_KONTROLLE = 20", "MIN_KONTROLLE = 19")]),
    ("Bootstrap: Kontrollmittel nicht neu geschätzt (Originalgewichte)", S,
     [("            SW, NW, EYW, EW = S @ W, N @ W, EY @ W, E @ W\n",
       "            SW, NW, EYW, EW = S @ np.ones_like(W), N @ np.ones_like(W), EY @ W, E @ W\n")]),
    ("p zweiseitig ohne +1", S,
     [("    return float((1 + np.sum(np.abs(Ts - T) >= abs(T))) / (1 + len(Ts)))",
       "    return float(np.sum(np.abs(Ts - T) >= abs(T)) / len(Ts))")]),
    ("p einseitig ohne Richtung", S,
     [("    return float((1 + np.sum(d * (Ts - T) >= d * T)) / (1 + len(Ts)))",
       "    return float((1 + np.sum((Ts - T) >= T)) / (1 + len(Ts)))")]),
    ("Holm ohne Abbruch", S, [("        if not verworfen:\n            weiter = False\n",
                               "        if False:\n            weiter = False\n")]),
    ("Quintil mit zu kurzer Vorgeschichte (100)", S, [("RV_VORGESCHICHTE = 250", "RV_VORGESCHICHTE = 100")]),
    ("Universum mit Futures", S, [('t.endswith("=F") or ', "")]),
    ("Quintil ohne t (Rang vor dem Einfügen)", S,
     [("        genug = len(hist) >= RV_VORGESCHICHTE\n        insort(hist, rv)\n        if genug:\n"
       "            lo, hi = bisect_left(hist, rv), bisect_right(hist, rv)\n"
       "            quintil[t] = min(4, int((lo + hi) / 2.0 / len(hist) * 5))\n",
       "        if len(hist) >= RV_VORGESCHICHTE:\n"
       "            lo, hi = bisect_left(hist, rv), bisect_right(hist, rv)\n"
       "            quintil[t] = min(4, int((lo + hi) / 2.0 / len(hist) * 5))\n        insort(hist, rv)\n")]),
    ("N-Familie ohne Sperre für fehlendes (b)", S,
     [("    return {k: (p if b_erfuellt.get(k) else None) for k, p in nps.items()}", "    return dict(nps)")]),
    ("Feinziehung mit unbereinigter N-Familie", S,
     [("    return nahe_schwelle(ps, hl) or nahe_schwelle(netto_ps(nps, b_erfuellt), netto_familie(nps, b_erfuellt))",
       "    return nahe_schwelle(ps, hl) or nahe_schwelle(nps, holm(nps))")]),
    ("Entdeckung nicht gekürzt", S,
     [("    return rows if bis is None else [r for r in rows if r[0] <= bis]", "    return rows")]),
    ("Einfrieren überschreibt", S,
     [('        with open(AUSGABE / "einfrieren.json", "x", encoding="utf-8") as f:',
       '        with open(AUSGABE / "einfrieren.json", "w", encoding="utf-8") as f:')]),
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
