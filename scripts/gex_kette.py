#!/usr/bin/env python3
"""
gex_kette.py — GEX-Snapshot und Key Levels als EINE Kette, mit Statusvertrag.

WARUM eine Hülle und nicht zwei Schritte in der Unit:

1. **Der Exit-Code allein sagt nicht, was passiert ist.** „nichts getan" und
   „veröffentlicht" sind beide Exit 0. Ein Trockenlauf (`--no-write`) gibt ebenfalls 0
   zurück. Würde die Kette 0 als „veröffentlicht" lesen, löste ein Probelauf die
   **schreibenden** Key Levels aus. Deshalb meldet der Snapshot sein Ergebnis als
   MARKER auf stdout, und die Kette liest ihn.
2. **Der Marker allein genügt auch nicht.** `Gesperrt` erbt von `SystemExit` und wird
   beim EINTRITT in `produktion()` geworfen (shared/produktionssperre.py) — also bevor
   `main()` läuft und bevor ein Marker fällt. Eine Regel „fehlender Marker =
   fehlgeschlagen" hätte eine geplante Unterdrückung rot gemacht. Und ein
   `veröffentlicht`-Marker mit anschließendem Fehlerexit darf Key Levels nicht starten.
   Also entscheiden **Exit-Code und Marker gemeinsam, Exit-Code hat Vorrang.**
3. **Die Produktionssperre soll über beide Schritte halten.** Zwei getrennte Units oder
   zwei `ExecStart`-Zeilen geben den geteilten Lock zwischen den Schritten frei — ein
   Deploy könnte dann dazwischen den Container austauschen. Diese Hülle hält ihn über
   die ganze Kette; die Kindprozesse nehmen ihrerseits geteilte Locks, die sich nicht
   gegenseitig blockieren.

Entscheidungstabelle (Auflage 1 der Codex-Freigabe, Runde 4):

    Exit 75   | Marker beliebig, auch keiner  -> unterdrückt      | Key Levels: nein | 75
    Exit 0    | genau ein `veroeffentlicht`   -> veröffentlicht   | Key Levels: JA   | 0
    Exit 0    | genau ein `uebersprungen`     -> übersprungen     | Key Levels: nein | 0
    Exit 0    | genau ein `trocken`           -> trocken          | Key Levels: nein | 0
    Exit 0    | keiner / mehrere / unbekannt  -> fehlgeschlagen   | Key Levels: nein | 1
    sonst     | beliebig, auch `veroeffentlicht` -> fehlgeschlagen| Key Levels: nein | Exit

Aufruf (Argumente gehen an den Snapshot durch):
    python3 scripts/gex_kette.py                 # automatisch (Timer)
    python3 scripts/gex_kette.py --reparatur      # Nachholauf, auch an einem Feiertag
    python3 scripts/gex_kette.py --no-write       # Probelauf, Key Levels laufen NICHT
"""
from __future__ import annotations

import pathlib
import subprocess
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

if __name__ != "__main__":
    from shared.produktionssperre import modul_sperre
    modul_sperre("gex_kette")

MARKER = "[ergebnis] "
VEROEFFENTLICHT = "veroeffentlicht"
BEKANNT = (VEROEFFENTLICHT, "uebersprungen", "trocken")
EXIT_GESPERRT = 75


def _lauf(argv: list[str]) -> tuple[int, str]:
    """Teilschritt ausführen, Ausgabe durchreichen UND einsammeln.

    `-u` ist Pflicht: ohne ungepufferte Ausgabe steht der Marker erst am Prozessende im
    Puffer, und bei einem Abbruch wäre er weg.
    """
    p = subprocess.run([sys.executable, "-u", *argv], cwd=str(_ROOT),
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       text=True, encoding="utf-8", errors="replace")
    sys.stdout.write(p.stdout or "")
    sys.stdout.flush()
    return p.returncode, (p.stdout or "")


def ergebnis_aus(rc: int, ausgabe: str) -> tuple[str, int]:
    """(Ergebnis, Exit der Kette) aus Prozessstatus und Marker. Exit-Code hat Vorrang.

    Reine Funktion, damit der Wächter sie ohne Prozessstart prüfen kann.
    """
    if rc == EXIT_GESPERRT:
        # Entsteht VOR main() beim Eintritt in produktion(); ein Marker kann hier nicht
        # vorliegen. Geplante Unterdrückung, kein Fehler.
        return "unterdrueckt", EXIT_GESPERRT
    if rc != 0:
        # Auch mit `veroeffentlicht`-Marker: ein Fehler NACH dem Marker darf den
        # schreibenden Folgeschritt nicht freigeben.
        return "fehlgeschlagen", rc
    marker = [z[len(MARKER):].split(" (", 1)[0].strip()
              for z in ausgabe.splitlines() if z.startswith(MARKER)]
    if len(marker) != 1 or marker[0] not in BEKANNT:
        return "fehlgeschlagen", 1
    return marker[0], 0


def main(argv: list[str]) -> int:
    rc, ausgabe = _lauf(["scripts/snapshot_gex_massive.py", *argv])
    ergebnis, exit_kette = ergebnis_aus(rc, ausgabe)
    print(f"[kette] Snapshot: {ergebnis} (Exit {rc})", flush=True)

    if ergebnis != VEROEFFENTLICHT:
        # Key Levels braucht eine frische gex_summary.json derselben Session. Ohne sie
        # würde es auf dem alten Stand rechnen und die Seite zeigte gestrige Levels als
        # heutige — deshalb hier enden statt fortfahren.
        print(f"[kette] compute_key_levels UEBERSPRUNGEN (Snapshot: {ergebnis})", flush=True)
        return exit_kette

    rc_kl, ausgabe_kl = _lauf(["scripts/compute_key_levels.py"])
    if rc_kl == EXIT_GESPERRT:
        print("[kette] compute_key_levels unterdrueckt (Produktionssperre)", flush=True)
        return EXIT_GESPERRT
    if rc_kl != 0:
        print(f"[kette] compute_key_levels FEHLGESCHLAGEN (Exit {rc_kl})", flush=True)
        return rc_kl
    print("[kette] fertig: Snapshot veroeffentlicht, Key Levels veroeffentlicht", flush=True)
    return 0


if __name__ == "__main__":
    from shared.produktionssperre import produktion
    with produktion("gex_kette"):
        sys.exit(main(sys.argv[1:]))
