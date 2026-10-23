#!/usr/bin/env python3
"""Mutationstest fuer verify_gex_kette_lauf.py — prueft den WAECHTER, nicht den Code.

Dieselben Beweisregeln wie ueberall: `[Aufbau]` gerissen, fehlender Endmarker oder
Exit 3 (Absturz) machen eine Mutation ungueltig, und jede Mutation BENENNT die Pruefung,
die sie reissen muss. Gearbeitet wird in einer Kopie des Projekts.

Aufruf: py -3.14 scripts/verify_gex_kette_lauf_mutation.py
"""
from __future__ import annotations

import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

_WURZEL = pathlib.Path(__file__).resolve().parents[1]

MUTATIONEN = [
    # ── Laufbindung ───────────────────────────────────────────────────────────────
    ("fremde Kennung wird durchgelassen", "scripts/gex_kette.py",
     "    if gemeldet != lauf or not session:", "    if not session:",
     "fremde Kennung"),
    ("Key Levels ohne Laufbindung gerufen", "scripts/gex_kette.py",
     '    rc_kl, _ = _lauf(["scripts/compute_key_levels.py",\n'
     '                      "--gex-datei", "landing/data/gex_summary.json", "--lauf", lauf])',
     '    rc_kl, _ = _lauf(["scripts/compute_key_levels.py"])',
     "MIT --lauf und --gex-datei"),
    ("zwei Markerzeilen werden akzeptiert", "scripts/gex_kette.py",
     "    if len(treffer) != 1:\n        return None, None",
     "    if not treffer:\n        return None, None\n    treffer = treffer[:1]",
     "ZWEI Markerzeilen"),
    ("Marker ohne Session wird akzeptiert", "scripts/gex_kette.py",
     "    if len(teile) != 2 or not teile[0] or not teile[1]:\n        return None, None",
     "    if not teile or not teile[0]:\n        return None, None\n"
     "    teile = (teile + [''])[:2]",
     "Marker ohne Session"),
    ("Kennung ohne Zufallsteil (zwei Laeufe derselben Sekunde gleich)",
     "scripts/gex_kette.py",
     '    return "%s-%s" % (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S"),\n'
     "                      os.urandom(2).hex())",
     '    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")',
     "Kennungen sind verschieden"),

    # ── Abschlussmarke ────────────────────────────────────────────────────────────
    ("Abschluss ohne Pflichtartefakte", "scripts/gex_kette.py",
     '        if fehlend:\n            # Kein Abschluss ohne alle Pflichtartefakte: die Marke wuerde sonst einen\n'
     '            # Zustand beglaubigen, den es nicht gibt.\n'
     '            eintrag["fertig"] = False\n            eintrag["fehlend"] = fehlend',
     '        if fehlend:\n            eintrag["fehlend"] = fehlend',
     "ohne Pflichtartefakte KEIN Abschluss"),
    ("fehlende Artefakte werden nicht benannt", "scripts/gex_kette.py",
     '            eintrag["fehlend"] = fehlend', '            eintrag["fehlend"] = []',
     "fehlenden Artefakte werden benannt"),
    ("Abschluss ohne Session erlaubt", "scripts/gex_kette.py",
     '    if fertig and not session:\n        raise ValueError("Abschlussmarke ohne Session — die Artefaktpfade haengen daran")',
     "    pass",
     "Abschluss ohne Session wird verweigert"),
    ("Hash wird nicht ueber den Inhalt gebildet", "scripts/gex_kette.py",
     "    h = hashlib.sha256()\n    with open(p, \"rb\") as f:\n"
     "        for stueck in iter(lambda: f.read(65536), b\"\"):\n            h.update(stueck)",
     "    h = hashlib.sha256()\n    h.update(p.name.encode())",
     "geaendertes Artefakt aendert seinen Hash"),
    ("Pfad absolut statt relativ", "scripts/gex_kette.py",
     '    return {"pfad": str(p.relative_to(_ROOT)).replace("\\\\", "/"),',
     '    return {"pfad": str(p),',
     "Pfade sind relativ"),
    ("kein Abbruch, wenn die Marke unfertig bleibt", "scripts/gex_kette.py",
     '    if not marke.get("fertig"):\n        print("[kette] FEHLGESCHLAGEN: Pflichtartefakte fehlen, kein Abschluss", flush=True)\n        return 1',
     "    pass",
     "fehlendes Pflichtartefakt"),
    ("Versuchseintrag erst NACH dem Snapshot", "scripts/gex_kette.py",
     '    lauf = neue_kennung()\n    # Versuchseintrag ZUERST: danach ist jeder Abbruch als Versuch erkennbar, und\n'
     '    # "nie versucht" unterscheidet sich von "gescheitert" (Spec Abschnitt 3).\n'
     '    marke_schreiben(lauf, None, fertig=False)\n'
     '    rc, ausgabe = _lauf(["scripts/snapshot_gex_massive.py", "--lauf", lauf, *argv])',
     '    lauf = neue_kennung()\n'
     '    rc, ausgabe = _lauf(["scripts/snapshot_gex_massive.py", "--lauf", lauf, *argv])',
     "Versuchseintrag existiert auch dann"),

    # ── Key Levels ────────────────────────────────────────────────────────────────
    ("_load_gex prueft die Kennung nicht", "scripts/compute_key_levels.py",
     '    if lauf and d.get("lauf") != lauf:', "    if False:",
     "fremde Kennung -> nichts uebernommen"),
    ("build() rechnet trotz fremder Kennung weiter", "scripts/compute_key_levels.py",
     '    if lauf and gex_status.startswith("anderer_lauf"):',
     "    if False:",
     "build() bricht bei fremder Kennung ab"),
    ("Kennung landet nicht in key_levels.json", "scripts/compute_key_levels.py",
     '        "lauf": lauf,                              # Kennung des Kettenlaufs (B2)',
     '        "lauf": None,',
     "Kennung steht in der Ausgabe von build()"),
]


def lauf(wurzel: pathlib.Path) -> tuple[int, str]:
    umg = dict(os.environ)
    umg["PYTHONUTF8"] = "1"
    umg["PYTHONPYCACHEPREFIX"] = str(wurzel / ".pyc")
    p = subprocess.run([sys.executable, str(wurzel / "scripts" / "verify_gex_kette_lauf.py")],
                       capture_output=True, text=True, env=umg, cwd=str(wurzel), timeout=900)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def main() -> int:
    kopie = pathlib.Path(tempfile.mkdtemp(prefix="sa-b2mut-"))
    ziel = kopie / "projekt"
    shutil.copytree(_WURZEL, ziel, ignore=shutil.ignore_patterns(
        ".git", "node_modules", "logs", "blog", "seo", "raw", "wiki", "lightning_logs",
        "__pycache__", "*.pyc", ".pyc"))
    print("Arbeitskopie: %s\n" % ziel)

    rc, aus = lauf(ziel)
    if rc != 0 or "PROBE-ENDE" not in aus:
        print("[ABBRUCH] Waechter in der Kopie nicht gruen (rc %s)" % rc)
        print(aus[-3000:])
        return 1
    print("Vorlauf gruen.\n")

    gefangen = entwischt = ungueltig = 0
    for name, datei, alt, neu, erwartet in MUTATIONEN:
        p = ziel / datei
        orig = p.read_text(encoding="utf-8")
        if orig.count(alt) != 1:
            print("UNGUELTIG  %-58s Anker %dx" % (name[:58], orig.count(alt)))
            ungueltig += 1
            continue
        p.write_text(orig.replace(alt, neu, 1), encoding="utf-8")
        try:
            rc, aus = lauf(ziel)
        finally:
            p.write_text(orig, encoding="utf-8")

        if rc == 3:
            print("UNGUELTIG  %-58s Absturz (Exit 3)" % name[:58])
            ungueltig += 1
            continue
        if "PROBE-ENDE" not in aus:
            print("UNGUELTIG  %-58s Endmarker nicht erreicht" % name[:58])
            ungueltig += 1
            continue
        rote = [z for z in aus.splitlines() if z.strip().startswith("FAIL")]
        if any("[Aufbau]" in z for z in rote):
            print("UNGUELTIG  %-58s [Aufbau] gerissen" % name[:58])
            ungueltig += 1
            continue
        if rc == 0:
            print("ENTWISCHT  %-58s kein Fehler gemeldet" % name[:58])
            entwischt += 1
            continue
        if not any(erwartet in z for z in rote):
            print("UNGUELTIG  %-58s andere Pruefung rot: %s"
                  % (name[:58], (rote[0][:70] if rote else "—")))
            ungueltig += 1
            continue
        print("gefangen   %-58s %d rot" % (name[:58], len(rote)))
        gefangen += 1

    print("\n%d/%d an der benannten Pruefung gefangen · %d entwischt · %d ungueltig"
          % (gefangen, len(MUTATIONEN), entwischt, ungueltig))
    shutil.rmtree(kopie, ignore_errors=True)
    return 1 if entwischt else 0


if __name__ == "__main__":
    sys.exit(main())
