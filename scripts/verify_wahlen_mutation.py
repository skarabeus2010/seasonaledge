#!/usr/bin/env python3
"""
verify_wahlen_mutation.py — prüft den WÄCHTER verify_wahlen_build.py, nicht den Code.

Baut bekannte Fehler in shared/elections.py ein (nur im Speicher, die Datei bleibt unberührt)
und verlangt, dass verify_wahlen_build.py jeden davon rot meldet.

    py -3.14 scripts/verify_wahlen_mutation.py     # Exit 0 = alle Mutationen gefangen
"""
from __future__ import annotations

import contextlib
import importlib
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

MUTATIONEN = {
    "Anker strikt vor dem Wahltag":
        ("bisect.bisect_right(daten, termin.isoformat()) - 1", "bisect.bisect_left(daten, termin.isoformat()) - 1"),
    "fehlender Wahltag → Vortag als t0":
        ('return None, "kurs_am_wahltag_fehlt"', "pass"),
    "keine Prüfung auf fehlende Sitzungen":
        ("    if _fehlende_sitzung(a, b, ist_sitzung):\n", "    if False:\n"),
    "Kurs an Nicht-Sitzung erlaubt":
        ("    if sa is False or sb is False:\n        return G_NICHT_SITZUNG", "    if False:\n        return G_NICHT_SITZUNG"),
    "nur der hintere Endpunkt geprüft (Codex R1)":
        ("    if sa is False or sb is False:", "    if sb is False:"),
    "Lückenregel auch im belegten Kalender":
        ("    if (sa is None or sb is None) and (b - a).days > MAX_LUECKE:", "    if (b - a).days > MAX_LUECKE:"),
    "Lückengrenze 10 statt 4 Tage":
        ("MAX_LUECKE = 4 ", "MAX_LUECKE = 10 "),
    "Live-Position um eine Sitzung verschoben":
        ("            tage[n + off] = (x - t0).days\n            if x > stichtag:",
         "            tage[n + off] = (x - t0).days\n            off += richtung\n            if x > stichtag:"),
    "Live: fehlende Session als Zukunft (Codex R1)":
        ("            if x > stichtag:", "            if x > stichtag or x.isoformat() not in kurs:"),
    "Datumsversatz im Pfad falsch":
        ("            tage[n + off] = (_d(daten[j]) - t0).days", "            tage[n + off] = off"),
    "Nachlauf auf t−X bezogen":
        ('"nachlauf": 100 * (pp / p0 - 1)', '"nachlauf": 100 * (pp / pm - 1)'),
    "Gültigkeit nur am Fensterrand geprüft":
        ("            if kaputt is None:\n                a, b", "            if kaputt is None and k == n:\n                a, b"),
    "Kontrolljahre = Wahljahr ± 2":
        ("return [jahr - 1, jahr + 1]", "return [jahr - 2, jahr + 2]"),
    "Anker-Abstand unbegrenzt":
        ("if (termin - t0).days > MAX_ANKER_ABSTAND:", "if False:"),
}


def main() -> int:
    import shared.elections as el
    import verify_wahlen_build as vw

    quelle = (REPO / "shared" / "elections.py").read_text(encoding="utf-8")
    verfehlt = 0
    for name, (alt, neu) in MUTATIONEN.items():
        if alt not in quelle:
            print(f"  WIRKUNGSLOS  {name} (Muster nicht gefunden)")
            verfehlt += 1
            continue
        importlib.reload(el)
        exec(compile(quelle.replace(alt, neu, 1), "mutation", "exec"), el.__dict__)  # noqa: S102
        vw.FEHLER.clear()
        with contextlib.redirect_stdout(io.StringIO()):
            rc = vw.main()
        print(("  gefangen     " if rc else "  VERFEHLT     ") + name)
        verfehlt += 0 if rc else 1
    importlib.reload(el)
    print(f"verify_wahlen_mutation: {len(MUTATIONEN) - verfehlt}/{len(MUTATIONEN)} gefangen")
    return 1 if verfehlt else 0


if __name__ == "__main__":
    sys.exit(main())
