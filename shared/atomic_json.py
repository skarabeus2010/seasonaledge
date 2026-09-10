#!/usr/bin/env python3
"""
atomic_json.py — JSON schreiben, ohne bei einem Abbruch eine halbe Datei zu hinterlassen.

WARUM: `Path.write_text()` kürzt die Zieldatei zuerst auf 0 und schreibt dann.
Wird der Prozess genau dazwischen beendet, bleibt eine abgeschnittene Datei
zurück. Bei `options_skew_history.json` (mehrere MB, Jahre an Punkten) ist das
ein Totalverlust: Der nächste Leser findet unparsbares JSON, behandelt es als
leere Historie und überschreibt sie mit einem Bruchteil.

Das ist kein theoretisches Risiko — der Backfill-Supervisor beendet den
Container per `docker stop` zu einem festen Zeitpunkt, unabhängig davon, ob
gerade geschrieben wird.

`os.replace()` ist auf POSIX und Windows atomar, solange Quelle und Ziel im
selben Dateisystem liegen. Deshalb wird die Temp-Datei im Zielverzeichnis
angelegt, nicht in /tmp.
"""
from __future__ import annotations
import json
import os
import tempfile
from pathlib import Path


def write_json_atomic(path: str | Path, obj, *, indent: int | None = 2,
                      ensure_ascii: bool = False) -> Path:
    """JSON atomar nach `path` schreiben. Gibt den Zielpfad zurück.

    Erst vollständig in eine Temp-Datei im selben Verzeichnis schreiben,
    flush + fsync (sonst liegt der Inhalt evtl. nur im OS-Puffer und ein
    Stromausfall/Container-Kill trifft trotzdem), dann atomar umbenennen.
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(p.parent), prefix=f".{p.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=ensure_ascii, indent=indent)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, p)          # atomar: entweder alte oder neue Datei, nie halbe
        return p
    except BaseException:
        # Auch bei KeyboardInterrupt/SIGTERM aufräumen — sonst sammeln sich
        # .tmp-Reste im Datenverzeichnis, die der Deploy mit ausliefert.
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
