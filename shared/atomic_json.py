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
import sys
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path

try:
    import fcntl  # POSIX
except ImportError:      # Windows-Entwicklung: keine Sperre (siehe history_aktualisieren)
    fcntl = None


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
        # WICHTIG: tempfile.mkstemp() legt die Datei bewusst mit 0600 an, und
        # os.replace() uebertraegt diesen Modus aufs Ziel. Cron-Ausgaben unter
        # landing/data/ werden von nginx als ANDEREM Nutzer gelesen -> 403,
        # die Seite laedt keine Daten mehr. (Live aufgetreten 2026-09-11:
        # options_skew.json und options_skew_history.json waren 403, die vier
        # Dateien ohne atomares Schreiben 200.)
        # Deshalb die Rechte der Zieldatei erhalten, sonst die des normalen
        # Schreibwegs (umask) nachbilden.
        try:
            modus = os.stat(p).st_mode & 0o777
        except FileNotFoundError:
            maske = os.umask(0); os.umask(maske)
            modus = 0o666 & ~maske
        os.chmod(tmp, modus)
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


# ── Gemeinsame Schreibsperre für Dateien mit mehreren Schreibern (2026-10-14) ──────────────────────────────────────
# WARUM: `options_skew_history.json` hat vier Schreiber (Options-Cron, Massive-Backfill, VRP-Nachrechnung, früher der
# marketdata-Backfill). Atomares Ersetzen verhindert halbe Dateien, aber keine verlorenen Änderungen: wer die Datei
# liest, lange rechnet und dann seine alte Gesamtstruktur zurückschreibt, löscht alles, was ein anderer dazwischen
# angelegt hat (dokumentiert in scripts/backfill_supervisor.sh). Und alle Schreiber machten aus einer unlesbaren Datei
# `{}` und überschrieben damit die ganze Historie. Plan: docs/review_prompts/2026-10-14_options_sofortreparaturen_plan_v3/v4.

class SperreBelegt(RuntimeError):
    """Die Sperre war innerhalb der Frist nicht zu bekommen — nichts geschrieben."""


class HistorieDefekt(RuntimeError):
    """Die Datei fehlt (ohne `neu_erlaubt`) oder ist kein lesbares JSON-Objekt — nichts geschrieben."""


def sperrdatei_skew_historie() -> Path:
    """`logs/sperre/skew_historie.lock` — dasselbe Verzeichnis wie die Produktionssperre (Host und Container teilen es)."""
    from shared.produktionssperre import sperr_verzeichnis
    return sperr_verzeichnis() / "skew_historie.lock"


def history_lesen(pfad: str | Path, *, neu_erlaubt: bool = False) -> dict:
    """JSON-Objekt lesen. Fehlt die Datei: `{}` nur mit `neu_erlaubt`, sonst HistorieDefekt. Unlesbar oder kein
    Objekt: immer HistorieDefekt — eine defekte Datei ist nie eine leere."""
    p = Path(pfad)
    if not p.exists():
        if neu_erlaubt:
            return {}
        raise HistorieDefekt(f"{p.name} fehlt (Neuanlage nur ausdrücklich erlaubt)")
    try:
        obj = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        raise HistorieDefekt(f"{p.name} ist nicht lesbar: {str(e)[:120]}") from e
    if not isinstance(obj, dict):
        raise HistorieDefekt(f"{p.name} ist kein JSON-Objekt ({type(obj).__name__})")
    return obj


_WINDOWS_GEWARNT = False


@contextmanager
def exklusive_sperre(sperrdatei: str | Path, *, frist_s: float = 600, name: str | None = None):
    """Haelt eine exklusive Dateisperre, solange der Block laeuft.

    Herausgeloest aus `history_aktualisieren`, damit es die Mechanik nur EINMAL gibt: die
    GEX-Kette braucht dieselbe Sperre ueber zwei Teilschritte hinweg (docs/KEY_LEVELS_CHART.md,
    Abschnitt 4), und eine zweite Umsetzung wuerde driften.

    Nicht binnen `frist_s` zu bekommen -> SperreBelegt, der Block laeuft dann gar nicht.
    Ohne fcntl (Windows-Entwicklung) gibt es keine Sperre, nur eine einmalige Warnung —
    die Parallelitaet prueft der Waechter unter Linux.
    """
    global _WINDOWS_GEWARNT
    sp = Path(sperrdatei)
    sp.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(sp), os.O_RDWR | os.O_CREAT, 0o644)
    try:
        if fcntl is not None:
            ende = time.monotonic() + frist_s
            while True:
                try:
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    if time.monotonic() >= ende:
                        raise SperreBelegt(
                            f"{name or sp.name}: nach {frist_s:.0f} s noch belegt — nichts getan")
                    time.sleep(0.5)
        elif not _WINDOWS_GEWARNT:
            _WINDOWS_GEWARNT = True
            print(f"[sperre] ungeprüft: kein fcntl auf diesem System, {sp.name} wird nicht gesperrt",
                  file=sys.stderr)
        yield sp
    finally:
        if fcntl is not None:
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
            except OSError:
                pass
        os.close(fd)


def history_aktualisieren(pfad: str | Path, aendern, *, danach=None, frist_s: float = 600,
                          neu_erlaubt: bool = False, sperrdatei: str | Path | None = None):
    """Liest `pfad` UNTER einer exklusiven Sperre frisch, wendet `aendern(hist)` an und schreibt atomar zurück.

    * `aendern(hist)` ändert das Objekt an Ort und Stelle; gibt es `False` zurück, wird NICHT geschrieben
      (z. B. Gate rot) und auch `danach` nicht aufgerufen.
    * `danach(hist)` läuft nach dem Schreiben noch unter der Sperre (Options-Cron: den Snapshot zur History).
    * Sperre nicht binnen `frist_s` → SperreBelegt; Datei defekt/fehlt → HistorieDefekt. In beiden Fällen ist nichts
      geschrieben.
    Rückgabe: das geschriebene Objekt oder None, wenn `aendern` False lieferte.
    Ohne fcntl (Windows-Entwicklung) gibt es keine Sperre — einmalige Warnung; Parallelität prüft der Wächter nur
    unter Linux.
    """
    sp = Path(sperrdatei) if sperrdatei else sperrdatei_skew_historie()
    with exklusive_sperre(sp, frist_s=frist_s):
        hist = history_lesen(pfad, neu_erlaubt=neu_erlaubt)
        if aendern(hist) is False:
            return None
        # Ohne Einrückung (2026-10-16): 11,0 → 8,1 MB roh, über gzip 1,07 → 1,01 MB; Leser parsen JSON, nicht Zeilen.
        write_json_atomic(pfad, hist, indent=None)
        if danach is not None:
            danach(hist)
        return hist
