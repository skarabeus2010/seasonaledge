#!/usr/bin/env python3
"""
verify_twins_mutation.py — prueft den Waechter, nicht den Code.

WARUM ES DAS GIBT: Ein Test, der strukturell nicht rot werden kann, ist
schlimmer als kein Test — er erzeugt Sicherheit, wo keine ist. Genau das ist in
dieser Codebasis passiert: ein Padding-Check verglich selbst erzeugte Schluessel
miteinander und bestand, waehrend der Fehler im Produktionscode stand. Ein
frueherer textueller Check traf einen unbeteiligten Datums-Helfer und bestand
ebenfalls.

Dieses Skript baut jeden bekannten Fehler ABSICHTLICH wieder ein und prueft, ob
`verify_seasonal_twins.py` daraufhin rot wird. Jede Mutation wird danach exakt
zurueckgenommen (Originalinhalt im Speicher, `finally`-Block).

Nutzung:  PYTHONUTF8=1 py -3.14 scripts/verify_twins_mutation.py
Exit 0 = jede Mutation wurde erkannt, 1 = mindestens eine blieb unbemerkt.
"""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_WAECHTER = _ROOT / "scripts" / "verify_seasonal_twins.py"

# (Beschreibung, Datei, Suchtext, Ersatztext)
# Jede Zeile baut einen Fehler nach, der in Welle 1 oder den Pruefrunden real war.
MUTATIONEN = [
    ("Nullpadding im ToM-Monatsschluessel entfernt (Jan zieht Oktober)",
     "landing/js/seasonal-compute.js",
     "var key = y + '-' + (m < 10 ? '0' : '') + m;",
     "var key = y + '-' + m;"),

    ("ToM-Kumulation wieder verschoben (Bewegung einen Tag zu spaet)",
     "landing/js/seasonal-compute.js",
     "      var cumLog = [];\n      var run = 0;\n      for (var ci = 0; ci < logRets.length; ci++) {\n        run += logRets[ci];\n        cumLog.push(run);\n      }",
     "      var cumLog = [0];\n      for (var ci = 0; ci < logRets.length - 1; ci++) cumLog.push(cumLog[ci] + logRets[ci]);"),

    ("Mondphasen-Kumulation wieder verschoben",
     "landing/js/seasonal-compute.js",
     "      var cumLog = [];\n      var run = 0;\n      for (var ci = 0; ci < logRets.length; ci++) { run += logRets[ci]; cumLog.push(run); }",
     "      var cumLog = [0];\n      for (var ci = 0; ci < logRets.length - 1; ci++) cumLog.push(cumLog[ci] + logRets[ci]);"),

    ("yearEndRef ohne Sperre gegen Zirkelschluss (JS)",
     "landing/js/seasonal-compute.js",
     "    return ref >= SA.seasonal.JAHRESENDE_UNTERGRENZE ? ref : 0;",
     "    return ref;"),

    ("yearEndRef zaehlt auch das laufende Jahr mit (JS)",
     "landing/js/seasonal-compute.js",
     "      if (parseInt(y, 10) >= jetzt) continue;",
     "      if (false) continue;"),

    ("yearCovers ohne ref>0-Schutz (winkt bei fehlender Referenz alles durch)",
     "shared/calculations.py",
     "    return ref > 0 and lad >= ref",
     "    return lad >= ref"),

    ("year_end_reference ohne Plausibilitaets-Untergrenze (Python)",
     "shared/calculations.py",
     "    return ref if ref >= JAHRESENDE_UNTERGRENZE else 0",
     "    return ref"),

    ("Feiertags-Kumulation wieder verschoben",
     "shared/holidays.py",
     "                cum_log = np.cumsum(log_rets)",
     "                cum_log = np.cumsum(np.insert(log_rets, 0, 0)[:-1])"),

    ("TDoM-Range gruppiert wieder ohne Ticker",
     "shared/tdom_analysis.py",
     '    _keys = (["ticker", "year", "month"] if "ticker" in df.columns\n             else ["year", "month"])',
     '    _keys = ["year", "month"]'),

    ("Normalisierung wieder um eine Zeile verschoben",
     "shared/calculations.py",
     "    steps = np.concatenate(([0.0], log_returns[1:]))",
     "    steps = np.concatenate(([0.0], log_returns[:-1]))"),

    ("Schaltjahr-Faltung entfernt (Tag 366 faellt weg)",
     "landing/js/seasonal-compute.js",
     "    if (days.length && days[days.length - 1] > 365) {",
     "    if (false) {"),

    ("buildYearData verwirft nicht mehr, sondern setzt still lr = 0",
     "landing/js/seasonal-compute.js",
     "          } else { verwerfen = true; break; }",
     "          } else { lr = 0; }"),
]


def waechter_laeuft_durch() -> bool:
    r = subprocess.run([sys.executable, str(_WAECHTER)],
                       capture_output=True, text=True, cwd=str(_ROOT))
    return r.returncode == 0


def main() -> int:
    print("=" * 78)
    print("Mutationstest: wird der Waechter rot, wenn der Fehler zurueckkommt?")
    print("=" * 78)

    if not waechter_laeuft_durch():
        print("\n[ABBRUCH] Der Waechter ist schon vor der ersten Mutation ROT.")
        print("          Erst den echten Fehler beheben, dann mutationstesten.")
        return 1
    print("\nAusgangslage: Waechter gruen. Jetzt Fehler einzeln wieder einbauen.\n")

    unbemerkt = []
    for nr, (beschreibung, datei, suchen, ersetzen) in enumerate(MUTATIONEN, 1):
        pfad = _ROOT / datei
        original = pfad.read_text(encoding="utf-8")
        treffer = original.count(suchen)
        if treffer != 1:
            print(f"{nr:>2}. [UNGUELTIG] {beschreibung}")
            print(f"      Suchtext {treffer}x in {datei} gefunden, erwartet genau 1x.")
            print(f"      Die Mutation greift ins Leere — sie beweist nichts.")
            unbemerkt.append(f"{beschreibung} (Suchtext {treffer}x)")
            continue
        try:
            pfad.write_text(original.replace(suchen, ersetzen, 1), encoding="utf-8")
            erkannt = not waechter_laeuft_durch()
        finally:
            pfad.write_text(original, encoding="utf-8")   # IMMER zuruecknehmen
        print(f"{nr:>2}. {'[erkannt]  ' if erkannt else '[UNBEMERKT]'} {beschreibung}")
        if not erkannt:
            unbemerkt.append(beschreibung)

    print("\n" + "=" * 78)
    if not waechter_laeuft_durch():
        print("[FAIL] Nach dem Test ist der Waechter rot — eine Datei wurde nicht "
              "sauber zurueckgesetzt. `git diff` pruefen!")
        return 1
    if unbemerkt:
        print(f"[FAIL] {len(unbemerkt)} von {len(MUTATIONEN)} Mutationen blieben "
              f"unbemerkt — an diesen Stellen ist der Waechter Scheinsicherheit:")
        for u in unbemerkt:
            print(f"   - {u}")
        return 1
    print(f"[OK] Alle {len(MUTATIONEN)} Mutationen wurden erkannt. Der Waechter "
          f"kann rot werden — und wird es bei jedem bekannten Fehler.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
