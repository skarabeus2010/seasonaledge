#!/usr/bin/env python3
"""verify_sektor_rotation_mutation.py — prueft verify_sektor_rotation.py.

Baut jeden der gefundenen Defekte absichtlich wieder ein und verlangt Rot. Jede
Mutation BENENNT die Pruefung, die sie reissen muss — sonst waere nicht belegt,
dass der Waechter die Wirkung messt und nicht nur irgendetwas.

Mechanik aus verify_twins_mutation (atomares Schreiben, exklusiver Lauf, frischer
Bytecode-Pfad). Exit des Waechters: 0 gruen, 1 rot (= erkannt), 3 Absturz
(= ungueltig, eine Ausnahme ist kein Nachweis).
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
from scripts.verify_twins_mutation import (_atomar_schreiben, _exklusiver_lauf,  # noqa: E402
                                           _zeilenende, python_probe, LF)

_WAECHTER = _ROOT / "scripts" / "verify_sektor_rotation.py"
D = "shared/daily_report.py"
V = "scripts/templates/daily_report.html.j2"

# (Name, Datei, [(suchen, ersetzen)], Pruefung-die-reissen-muss)
MUTATIONEN = [
    ("laufender Monat zaehlt wieder mit", D,
     [("                    if yr == heute.year and mo == heute.month:\n",
       "                    if False and yr == heute.year and mo == heute.month:\n")],
     "der laufende 2026 zaehlt NICHT"),

    ("Fallzahl nicht mehr ausgegeben", D,
     [('"avg_return_pct": m[month]["avg"], "n": m[month]["n"]}',
       '"avg_return_pct": m[month]["avg"]}')],
     "jede Zeile traegt ihre Fallzahl"),

    ("Mindest-Fallzahl entfernt", D,
     [('                if month in m and m[month]["n"] >= SEKTOR_MIN_JAHRE\n',
       '                if month in m\n')],
     "XLC fuehrt NICHT"),

    ("berechenbar immer True", D,
     [('"berechenbar": bool(current_top or next_top),',
       '"berechenbar": True,')],
     "berechenbar ist False"),

    ("stummer Zweig ohne Logzeile", D,
     [('        error_logger.error(\n'
       '            "[daily_report] Sektor-Rotation: keine Kurshistorie fuer die "\n'
       '            f"{len(SECTOR_ETFS)} Sektor-ETFs — die Sektion bleibt ohne Werte"\n'
       '        )\n',
       '        pass\n')],
     "der stumme Zweig schreibt jetzt eine Logzeile"),

    ("Ersatztabelle wieder eingebaut", D,
     [("        if not monthly:\n            return []\n",
       '        if not monthly:\n'
       '            return [{"ticker": "XLK", "name": "Technology",\n'
       '                     "avg_return_pct": 1.7, "n": 15}]\n')],
     "kein Rueckgabewert setzt avg_return_pct auf eine feste Zahl"),

    ("aufsteigend sortiert", D,
     [('            key=lambda r: r["avg_return_pct"],\n            reverse=True,\n',
       '            key=lambda r: r["avg_return_pct"],\n            reverse=False,\n')],
     "absteigend sortiert"),

    ("Universums-Schutz entfernt", D,
     [("        if im_universum(ticker) and last_bar and last_bar.get(\"kerzen\"):",
       "        if last_bar and last_bar.get(\"kerzen\"):")],
     "der Universums-Schutz steht im Code"),

    ("Vorlage: Plus wieder fest verdrahtet", V,
     [("""            {% for s in rotation.current_top %}
            <div style="padding:6px 0;border-bottom:1px solid rgba(255,255,255,0.04);font-size:13px;">
              <span style="color:#e8a820;font-family:'JetBrains Mono',monospace;font-weight:700;">{{ s.ticker }}</span>
              <span style="color:#cbd5e1;margin-left:6px;">{{ s.name }}</span>
              <span style="color:{{ '#30e878' if s.avg_return_pct >= 0 else '#ff5c5c' }};float:right;font-variant-numeric:tabular-nums;font-weight:600;">{{ '%+.1f' % s.avg_return_pct }}% <span style="color:#a89878;font-weight:400;">({{ s.n }})</span></span>
""",
       """            {% for s in rotation.current_top %}
            <div style="padding:6px 0;border-bottom:1px solid rgba(255,255,255,0.04);font-size:13px;">
              <span style="color:#e8a820;font-family:'JetBrains Mono',monospace;font-weight:700;">{{ s.ticker }}</span>
              <span style="color:#cbd5e1;margin-left:6px;">{{ s.name }}</span>
              <span style="color:{{ '#30e878' if s.avg_return_pct >= 0 else '#ff5c5c' }};float:right;font-variant-numeric:tabular-nums;font-weight:600;">+{{ '%.1f' % s.avg_return_pct }}% <span style="color:#a89878;font-weight:400;">({{ s.n }})</span></span>
""")],
     "kein fest verdrahtetes Plus vor einem negativen Wert"),

    ("Vorlage: Farbe immer gruen", V,
     [("""              <span style="color:{{ '#30e878' if s.avg_return_pct >= 0 else '#ff5c5c' }};float:right;font-variant-numeric:tabular-nums;font-weight:600;">{{ '%+.1f' % s.avg_return_pct }}% <span style="color:#a89878;font-weight:400;">({{ s.n }})</span></span>
            </div>
            {% endfor %}
          </td>
          {# ── Folgemonat ── #}""",
       """              <span style="color:#30e878;float:right;font-variant-numeric:tabular-nums;font-weight:600;">{{ '%+.1f' % s.avg_return_pct }}% <span style="color:#a89878;font-weight:400;">({{ s.n }})</span></span>
            </div>
            {% endfor %}
          </td>
          {# ── Folgemonat ── #}""")],
     "der negative Wert ist rot, nicht gruen"),

    ("Vorlage: Fallzahl nicht gerendert", V,
     [("""{{ '%+.1f' % s.avg_return_pct }}% <span style="color:#a89878;font-weight:400;">({{ s.n }})</span></span>
            </div>
            {% endfor %}
          </td>
          {# ── Folgemonat ── #}""",
       """{{ '%+.1f' % s.avg_return_pct }}%</span>
            </div>
            {% endfor %}
          </td>
          {# ── Folgemonat ── #}""")],
     "die Fallzahl steht in der gerenderten Mail"),

    ("Vorlage: Sektion verschwindet wieder stumm", V,
     [("    {% if rotation %}\n",
       "    {% if rotation and (rotation.current_top or rotation.next_top) %}\n")],
     "die Sektion verschwindet nicht, wenn nichts berechenbar ist"),

    ("Vorlage: Hinweiszeile entfernt", V,
     [("        Heute nicht berechenbar — keine Kurshistorie für die Sektor-ETFs verfügbar.\n",
       "        &nbsp;\n")],
     "sie sagt stattdessen, dass es heute nicht berechenbar ist"),
]

# Mutationen, die der Waechter NICHT fangen kann und auch nicht soll. Sie pruefen das
# Urteil des Tests selbst: wird hier etwas als „erkannt" gemeldet, misst der Waechter
# etwas anderes als er behauptet.
UNGUELTIG_ERWARTET = [
    ("Kommentar geaendert (wirkungslos)", D,
     [("# Wie viele abgeschlossene Monate ein Durchschnitt mindestens braucht",
       "# Wie viele abgeschlossene Monate ein Mittelwert mindestens braucht")]),
]


def _anwenden(pfad: Path, original: bytes, paare, nr: int, name: str):
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
            print("[FAIL] Waechter ist schon ohne Mutation rot:\n" + (r0.stdout or "")[-2500:])
            return 1

        for nr, (name, datei, paare, pruefung) in enumerate(MUTATIONEN, 1):
            pfad = _ROOT / datei
            original = pfad.read_bytes()
            neu = _anwenden(pfad, original, paare, nr, name)
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
                print(f"{nr:>2}. [UNBEMERKT] {name}")
                unbemerkt.append(name)
                continue
            # Rot allein genuegt nicht: es muss GENAU die benannte Pruefung sein.
            getroffen = [z for z in (r.stdout or "").splitlines()
                         if z.startswith("  FEHL") and pruefung in z]
            if getroffen:
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
            neu = _anwenden(pfad, original, paare, nr, name)
            if neu is None:
                print(f"{nr:>2}. [UNGUELTIG] {name} — Anker nicht eindeutig, Testfall "
                       "selbst untauglich")
                ungueltig.append(name)
                continue
            try:
                _atomar_schreiben(pfad, neu)
                r = python_probe([_WAECHTER], capture_output=True, text=True, cwd=str(_ROOT))
            finally:
                _atomar_schreiben(pfad, original)
                assert pfad.read_bytes() == original, f"{datei} nicht wiederhergestellt"
            if r.returncode == 0:
                print(f"{nr:>2}. [wirkungslos, richtig] {name}")
            else:
                print(f"{nr:>2}. [FALSCHALARM] {name} — der Waechter wird rot, obwohl "
                      f"sich nichts Wirksames geaendert hat (Exit {r.returncode})")
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
