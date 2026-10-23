#!/usr/bin/env python3
"""Mutationstest fuer verify_niveau_felder.py — prueft den WAECHTER, nicht den Code.

Jede Mutation baut einen bekannten Fehler absichtlich ein und BENENNT die Pruefung, die
daran reissen muss. Reisst eine andere, ist die Mutation ungueltig: dann hat der Waechter
den gemeinten Fehler nicht gefangen, sondern einen Nebeneffekt.

Beweisregeln des Hauses:
* `[Aufbau]` gerissen  -> Geruest zerstoert, Mutation ungueltig
* Endmarker `PROBE-ENDE` nicht erreicht -> ungueltig (abgebrochen statt gefangen)
* Exit 3 (Absturz)     -> ungueltig, ein Absturz ist kein Nachweis
* Anker trifft nicht   -> ungueltig, nicht "gefangen"

Gearbeitet wird in einer KOPIE des Projekts (Temp), damit kein Produktivstand mutiert
im Arbeitsbaum liegen bleibt.

Aufruf: py -3.14 scripts/verify_niveau_felder_mutation.py
"""
from __future__ import annotations

import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

_WURZEL = pathlib.Path(__file__).resolve().parents[1]

# (Name, Datei, alt, neu, erwartete Pruefung im Fehlertext)
MUTATIONEN = [
    # ── Der gemeinsame Kern ───────────────────────────────────────────────────────
    ("Teilkette wird zu kein_niveau verharmlost", "shared/niveau_felder.py",
     "    if not kette_vollstaendig:\n        return Z_TEILKETTE",
     "    if not kette_vollstaendig and wert is not None:\n        return Z_TEILKETTE",
     "kein Wert, Kette abgeschnitten"),
    ("unbekannter Ladezustand gilt als vollstaendig", "shared/niveau_felder.py",
     "    if not kette_vollstaendig:\n        return Z_TEILKETTE",
     "    if kette_vollstaendig is False:\n        return Z_TEILKETTE",
     "Ladezustand unbekannt"),
    ("fehlende Quelle wird erst nach der Kette geprueft", "shared/niveau_felder.py",
     "    if not quelle_da:\n        return Z_QUELLE_FEHLT\n    if not kette_vollstaendig:",
     "    if not kette_vollstaendig and quelle_da:\n        return Z_TEILKETTE\n    if not quelle_da:",
     "keine Quelle schlaegt alles"),
    ("Mehrdeutigkeit schlaegt die Teilkette", "shared/niveau_felder.py",
     "    if not kette_vollstaendig:\n        return Z_TEILKETTE\n    if wert is None:",
     "    if mehrdeutig:\n        return Z_NICHT_EINDEUTIG\n    if not kette_vollstaendig:\n"
     "        return Z_TEILKETTE\n    if wert is None:",
     "mehrdeutig schlaegt nicht die Teilkette"),
    ("teilkette gilt als zeichenbar", "shared/niveau_felder.py",
     "ZEICHENBAR = (Z_OK, Z_NICHT_EINDEUTIG)",
     "ZEICHENBAR = (Z_OK, Z_NICHT_EINDEUTIG, Z_TEILKETTE)",
     "gezeichnet werden genau"),
    ("Strike-Stufe nimmt den haeufigsten statt den kleinsten Abstand",
     "shared/niveau_felder.py",
     "    return min(positiv) if positiv else None",
     "    return max(positiv) if positiv else None",
     "KLEINSTER Abstand"),
    ("Strike-Stufe ohne Rundung (Gleitkommarest)", "shared/niveau_felder.py",
     "    abstaende = [round(b - a, 6) for a, b in zip(sortiert, sortiert[1:])]",
     "    abstaende = [b - a for a, b in zip(sortiert, sortiert[1:])]",
     "0,1 trotz Gleitkommarest"),
    # Die Entdoppelung selbst ist durch den Filter abgedeckt (eine Mutation auf die
    # Menge waere aequivalent) — mutiert wird deshalb der Filter, der den Abstand 0
    # wirklich verhindert.
    ("Abstand 0 wird als Stufe zugelassen", "shared/niveau_felder.py",
     "    positiv = [d for d in abstaende if d > 0]", "    positiv = list(abstaende)",
     "fast gleiche Strikes"),
    ("Strike-Stufe laesst nicht endliche Werte durch", "shared/niveau_felder.py",
     "        if math.isfinite(f):\n            sauber.add(f)",
     "        sauber.add(f)",
     "nicht endlich"),
    ("Strike-Stufe raet einen Standardwert", "shared/niveau_felder.py",
     "    if len(sauber) < 2:\n        return None",
     "    if len(sauber) < 2:\n        return 1.0",
     "ein einziger Strike"),

    # ── GEX-Snapshot ──────────────────────────────────────────────────────────────
    ("Seiten-Cap gilt als vollstaendig", "scripts/snapshot_gex_massive.py",
     "    if url:                      # Seiten-Cap gerissen, es gaebe noch eine Seite\n"
     "        vollstaendig = False\n    return out, vollstaendig",
     "    return out, vollstaendig",
     "Seiten-Cap gerissen"),
    # BEWUSST KEINE Mutation auf die innere `vollstaendig = False` vor dem break: beim
    # Abbruch an der Statuspruefung ist `url` noch gesetzt (es wird erst danach
    # fortgeschrieben), die nachgelagerte Pruefung `if url:` greift also ohnehin. Die
    # Mutation waere aequivalent und wuerde als "entwischt" gezaehlt, obwohl sich nichts
    # aendert. Die Zeile bleibt im Code als zweite Linie, falls die Reihenfolge je
    # umgestellt wird.
    ("Ladezustand wird in der Zeile verschwiegen", "scripts/snapshot_gex_massive.py",
     '        "gex_kette_vollst": kette_vollstaendig,',
     '        "gex_kette_vollst": True,',
     "abgeschnittene Kette"),
    ("Strike-Stufe aus der falschen Grundmenge", "scripts/snapshot_gex_massive.py",
     '    stufe = strike_stufe(c["K"] for c in summary_c)',
     '    stufe = strike_stufe([])',
     "strike_stufe gemessen"),
    ("Archivzeile verliert die neuen Felder", "scripts/snapshot_gex_massive.py",
     '                                           "gex_kette_vollst", "gex_horizont_tage",\n'
     '                                           "strike_stufe", "felder")} for o in results]}',
     '                                           )} for o in results]}',
     "Archivzeile traegt dieselben vier Felder"),
    ("Horizont falsch ausgewiesen", "scripts/snapshot_gex_massive.py",
     '        "gex_horizont_tage": max_days,', '        "gex_horizont_tage": horizon,',
     "Horizont bleibt der des Summary"),

    # ── Key Levels ────────────────────────────────────────────────────────────────
    ("gescheiterter Abruf gilt als abgeschlossene Kette", "scripts/compute_key_levels.py",
     "        contracts, mp_kette_vollst = [], None",
     "        contracts, mp_kette_vollst = [], True",
     "gescheiterter Abruf"),
    ("Wall-Zustaende werden neu erfunden statt uebernommen",
     "scripts/compute_key_levels.py",
     '        "call_wall": g_felder.get("call_wall", Z_QUELLE_FEHLT),\n'
     '        "put_wall": g_felder.get("put_wall", Z_QUELLE_FEHLT),',
     '        "call_wall": feldzustand(row.get("call_wall"), True),\n'
     '        "put_wall": feldzustand(row.get("put_wall"), True),',
     "UEBERNOMMEN"),
    ("fehlende GEX-Zeile wird zu kein_niveau", "scripts/compute_key_levels.py",
     '        "vol_trigger": g_felder.get("vol_trigger", Z_QUELLE_FEHLT),\n'
     '        "max_pain": feldzustand(row.get("max_pain"), mp_kette_vollst,',
     '        "vol_trigger": g_felder.get("vol_trigger", "kein_niveau"),\n'
     '        "max_pain": feldzustand(row.get("max_pain"), mp_kette_vollst,',
     "ohne GEX-Zeile"),
    ("Mehrdeutigkeit wird nicht durchgereicht", "scripts/compute_key_levels.py",
     '                                mehrdeutig=bool(row.get("max_pain_non_unique"))),',
     '                                mehrdeutig=False),',
     "mehrdeutiges Max Pain"),
    ("Stufe wird nicht uebernommen", "scripts/compute_key_levels.py",
     '    row["strike_stufe"] = g.get("strike_stufe")',
     '    row["strike_stufe"] = None',
     "Stufe und Horizont aus der GEX-Zeile"),
    ("ohne Schluessel sieht Max Pain wie ein Ergebnis aus",
     "scripts/compute_key_levels.py",
     '            "max_pain": Z_QUELLE_FEHLT,\n        },\n    }',
     '            "max_pain": "kein_niveau",\n        },\n    }',
     "ohne Schluessel"),
]


def lauf(wurzel: pathlib.Path) -> tuple[int, str]:
    umg = dict(os.environ)
    umg["PYTHONUTF8"] = "1"
    umg["PYTHONPYCACHEPREFIX"] = str(wurzel / ".pyc")   # keine alte .pyc der Vormutation
    p = subprocess.run([sys.executable, str(wurzel / "scripts" / "verify_niveau_felder.py")],
                       capture_output=True, text=True, env=umg, cwd=str(wurzel), timeout=600)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def main() -> int:
    kopie = pathlib.Path(tempfile.mkdtemp(prefix="sa-b1mut-"))
    ziel = kopie / "projekt"
    shutil.copytree(_WURZEL, ziel, ignore=shutil.ignore_patterns(
        ".git", "node_modules", "logs", "blog", "seo", "raw", "wiki", "lightning_logs",
        "__pycache__", "*.pyc", ".pyc"))
    print("Arbeitskopie: %s\n" % ziel)

    rc, aus = lauf(ziel)
    if rc != 0 or "PROBE-ENDE" not in aus:
        print("[ABBRUCH] Der Waechter ist in der Kopie nicht gruen (rc %s)." % rc)
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

    gesamt = len(MUTATIONEN)
    print("\n%d/%d an der benannten Pruefung gefangen · %d entwischt · %d ungueltig"
          % (gefangen, gesamt, entwischt, ungueltig))
    shutil.rmtree(kopie, ignore_errors=True)
    return 1 if entwischt else 0


if __name__ == "__main__":
    sys.exit(main())
