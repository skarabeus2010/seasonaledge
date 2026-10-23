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

import hashlib
import json
import os
import pathlib
import subprocess
import sys
from datetime import datetime, timezone

_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

if __name__ != "__main__":
    from shared.produktionssperre import modul_sperre
    modul_sperre("gex_kette")

from shared.atomic_json import write_json_atomic  # noqa: E402

MARKER = "[ergebnis] "
LAUF_MARKER = "[lauf] "
VEROEFFENTLICHT = "veroeffentlicht"
BEKANNT = (VEROEFFENTLICHT, "uebersprungen", "trocken")
EXIT_GESPERRT = 75
EXIT_PARALLEL = 4          # eine zweite Kette laeuft schon

_MARKE = _ROOT / "landing" / "data" / "gex_lauf.json"
_SPERRE = _ROOT / "logs" / "sperre" / "gex_kette.lock"

# Was ein abgeschlossener Lauf hinterlassen muss. Die Marke nennt jedes Artefakt mit
# Inhaltshash: ohne die Bindung an konkrete Versionen koennte eine alte Marke Artefakte
# beglaubigen, die inzwischen ein anderer Lauf ersetzt hat (docs/KEY_LEVELS_CHART.md,
# Abschnitt 4). Die vier Profildateien stehen NICHT drin — sie tragen kein Niveau, und
# ein Leser der Niveaus wartet nicht auf sie.
PFLICHTARTEFAKTE = ("landing/data/gex_summary.json",
                    "landing/data/gex_history_session/{session}.json",
                    "landing/data/key_levels.json")


def neue_kennung() -> str:
    """Kennung dieses Kettenlaufs: Startzeit (UTC) und Zufall.

    Sie entsteht in der KETTE, nicht im Snapshot — nur so kann der Versuchseintrag vor
    dem ersten Teilschritt stehen. Der Zufallsteil trennt zwei Laeufe derselben Sekunde.
    """
    return "%s-%s" % (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S"),
                      os.urandom(2).hex())


def _hash(p: pathlib.Path) -> dict:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for stueck in iter(lambda: f.read(65536), b""):
            h.update(stueck)
    return {"pfad": str(p.relative_to(_ROOT)).replace("\\", "/"),
            "sha256": h.hexdigest(), "bytes": p.stat().st_size}


def marke_schreiben(lauf: str, session: str | None, fertig: bool) -> None:
    """Versuchs- bzw. Abschlusseintrag des Kettenlaufs.

    Der Versuchseintrag entsteht VOR dem ersten Teilschritt, nicht danach: ein getoeteter
    Prozess kann hinterher nichts mehr schreiben, und dann saehe ein Abbruch wie "nie
    versucht" aus. Erst die Abschlussmarke (fertig=True) macht den Lauf fuer Leser
    auswaehlbar — Exit 0 genuegt dafuer nicht, weil Key Levels Kettenfehler abfaengt.
    """
    eintrag = {"lauf": lauf, "session": session, "fertig": fertig,
               "stand": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    if fertig and not session:
        raise ValueError("Abschlussmarke ohne Session — die Artefaktpfade haengen daran")
    if fertig:
        artefakte, fehlend = [], []
        for muster in PFLICHTARTEFAKTE:
            p = _ROOT / muster.format(session=session)
            if p.exists():
                artefakte.append(_hash(p))
            else:
                fehlend.append(muster.format(session=session))
        if fehlend:
            # Kein Abschluss ohne alle Pflichtartefakte: die Marke wuerde sonst einen
            # Zustand beglaubigen, den es nicht gibt.
            eintrag["fertig"] = False
            eintrag["fehlend"] = fehlend
        eintrag["artefakte"] = artefakte
    _MARKE.parent.mkdir(parents=True, exist_ok=True)
    write_json_atomic(_MARKE, eintrag, indent=2)
    zustand = "fertig" if eintrag["fertig"] else "versuch"
    print(f"[kette] Marke {zustand}: Lauf {lauf}"
          + (" — fehlend: %s" % ", ".join(eintrag.get("fehlend", []))
             if eintrag.get("fehlend") else ""), flush=True)


def lauf_aus(ausgabe: str) -> tuple[str | None, str | None]:
    """(Laufkennung, Session) aus der Snapshot-Ausgabe.

    Genau eine Markerzeile mit zwei Feldern, sonst (None, None) — mehrere Zeilen
    bedeuten, dass zwei Snapshots in dieselbe Ausgabe geschrieben haben, und dann ist
    keine Zuordnung mehr sicher. Reine Funktion, damit der Waechter sie ohne Prozessstart
    pruefen kann.
    """
    treffer = [z[len(LAUF_MARKER):].strip() for z in ausgabe.splitlines()
               if z.startswith(LAUF_MARKER)]
    if len(treffer) != 1:
        return None, None
    teile = treffer[0].split()
    if len(teile) != 2 or not teile[0] or not teile[1]:
        return None, None
    return teile[0], teile[1]


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
    lauf = neue_kennung()
    # Versuchseintrag ZUERST: danach ist jeder Abbruch als Versuch erkennbar, und
    # "nie versucht" unterscheidet sich von "gescheitert" (Spec Abschnitt 3).
    marke_schreiben(lauf, None, fertig=False)
    rc, ausgabe = _lauf(["scripts/snapshot_gex_massive.py", "--lauf", lauf, *argv])
    ergebnis, exit_kette = ergebnis_aus(rc, ausgabe)
    gemeldet, session = lauf_aus(ausgabe)
    print(f"[kette] Snapshot: {ergebnis} (Exit {rc})", flush=True)

    if ergebnis != VEROEFFENTLICHT:
        # Key Levels braucht eine frische gex_summary.json derselben Session. Ohne sie
        # würde es auf dem alten Stand rechnen und die Seite zeigte gestrige Levels als
        # heutige — deshalb hier enden statt fortfahren.
        print(f"[kette] compute_key_levels UEBERSPRUNGEN (Snapshot: {ergebnis})", flush=True)
        return exit_kette
    if gemeldet != lauf or not session:
        # Der Snapshot muss GENAU die uebergebene Kennung melden. Weicht sie ab, lief ein
        # anderer Prozess oder ein alter Stand — dann ist die Summary nicht zuordenbar.
        print(f"[kette] ABBRUCH: Snapshot meldete Kennung {gemeldet!r}, erwartet {lauf!r}",
              flush=True)
        return 1

    marke_schreiben(lauf, session, fertig=False)

    rc_kl, _ = _lauf(["scripts/compute_key_levels.py",
                      "--gex-datei", "landing/data/gex_summary.json", "--lauf", lauf])
    if rc_kl == EXIT_GESPERRT:
        print("[kette] compute_key_levels unterdrueckt (Produktionssperre)", flush=True)
        return EXIT_GESPERRT
    if rc_kl != 0:
        print(f"[kette] compute_key_levels FEHLGESCHLAGEN (Exit {rc_kl})", flush=True)
        return rc_kl
    marke_schreiben(lauf, session, fertig=True)
    marke = json.loads(_MARKE.read_text(encoding="utf-8"))
    if not marke.get("fertig"):
        print("[kette] FEHLGESCHLAGEN: Pflichtartefakte fehlen, kein Abschluss", flush=True)
        return 1
    print("[kette] fertig: Snapshot veroeffentlicht, Key Levels veroeffentlicht", flush=True)
    return 0


if __name__ == "__main__":
    from shared.atomic_json import SperreBelegt, exklusive_sperre
    from shared.produktionssperre import produktion
    with produktion("gex_kette"):
        # Die Produktionssperre ist GETEILT (LOCK_SH) — sie schuetzt gegen den
        # Container-Austausch, nicht gegen eine zweite Kette. Ohne diese exklusive Sperre
        # konnte Lauf B die Summary ueberschreiben, waehrend Lauf A sie noch las.
        try:
            with exklusive_sperre(_SPERRE, frist_s=0, name="gex_kette"):
                sys.exit(main(sys.argv[1:]))
        except SperreBelegt as e:
            print(f"[kette] ABBRUCH: {e} — eine zweite Kette laeuft", flush=True)
            sys.exit(EXIT_PARALLEL)
