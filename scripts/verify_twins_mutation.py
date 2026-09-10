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
`verify_seasonal_twins.py` daraufhin rot wird.

SICHERHEIT BEIM SCHREIBEN — dieses Skript veraendert Produktionsdateien:
  * Exklusiver Lock: zwei parallele Laeufe wuerden sich gegenseitig den
    mutierten Stand als "Original" zurueckschreiben.
  * BYTES statt Text: kein Encoding-Fehler, keine stille CRLF/LF-Normalisierung.
  * Atomares Ersetzen (Temp-Datei IM ZIELVERZEICHNIS + os.replace): ein Abbruch
    mitten im Schreiben hinterlaesst keine halbe Datei.
  * Nach jeder Mutation wird nachgewiesen, dass die Datei wieder dem Original
    entspricht — nicht nur versucht.

Nutzung:  PYTHONUTF8=1 py -3.14 scripts/verify_twins_mutation.py
Exit 0 = jede Mutation wurde erkannt, 1 = mindestens eine blieb unbemerkt.
"""
from __future__ import annotations
import contextlib
import os
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_WAECHTER = _ROOT / "scripts" / "verify_seasonal_twins.py"
_LOCK = _ROOT / ".mutationstest.lock"

CRLF = bytes([13, 10])
LF = bytes([10])

# (Beschreibung, Datei, Suchtext, Ersatztext)
# Jede Zeile baut einen Fehler nach, der in Welle 1 oder den Pruefrunden real war.
# Suchtexte sind EINZEILIG: mehrzeilige Anker muessten gegen CRLF/LF normalisiert
# werden und greifen sonst still ins Leere — ein Mutationstest, der nichts
# trifft, beweist nichts.
MUTATIONEN = [
    ("Nullpadding im ToM-Monatsschluessel entfernt (Jan zieht Oktober)",
     "landing/js/seasonal-compute.js",
     "var key = y + '-' + (m < 10 ? '0' : '') + m;",
     "var key = y + '-' + m;"),

    ("Nachbarschaftspruefung im ToM-Fenster entfernt",
     "landing/js/seasonal-compute.js",
     "if (nxt.month !== expMonth || nxt.year !== expYear) continue;",
     "if (false) continue;"),

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
     '    _keys = (["ticker", "year", "month"] if "ticker" in df.columns',
     '    _keys = (["year", "month"] if "ticker" in df.columns'),

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

    # ── aus der Endabnahme: Pfade, die vorher von keinem Waechterfall
    #    beruehrt wurden. Ohne diese Faelle war der gruene Lauf dort ohne Aussage.
    ("Perioden-Endtag um einen Kalendertag verschoben (Wert, nicht Anzahl)",
     "shared/calculations.py",
     '        end_val = yd["full_365"][min(end_day - 1, 364)]',
     '        end_val = yd["full_365"][min(end_day, 364)]'),

    ("buildMonthlyStats liest den Monat falsch aus (bricht Okt-Dez)",
     "landing/js/seasonal-compute.js",
     "      var m = parseInt(rows[i].date.substring(5, 7));",
     "      var m = parseInt(rows[i].date.substring(6, 7));"),

    ("buildTOMHeatmap zeigt die aeltesten statt der neuesten Jahre",
     "landing/js/seasonal-compute.js",
     "years = years.slice(-nYears);",
     "years = years.slice(0, nYears);"),

    ("yearCovers faellt bei fehlendem last_actual_day auf 365 zurueck (fail-open)",
     "landing/js/seasonal-compute.js",
     "    var lad = yd.last_actual_day;\n    lad = (typeof lad === 'number' && isFinite(lad)) ? lad : 0;",
     "    var lad = yd.last_actual_day;\n    lad = (typeof lad === 'number' && isFinite(lad)) ? lad : 365;"),
]


class LockBelegt(RuntimeError):
    pass


@contextlib.contextmanager
def _exklusiver_lauf():
    """Verhindert zwei gleichzeitige Laeufe.

    Ohne Lock schreibt Lauf B den MUTIERTEN Stand von Lauf A als sein
    "Original" fest — und stellt am Ende genau den Fehler wieder her, den er
    testen sollte.
    """
    try:
        fd = os.open(str(_LOCK), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        raise LockBelegt(
            f"{_LOCK.name} existiert bereits — laeuft der Test schon? Wurde ein "
            f"frueherer Lauf hart abgebrochen, ZUERST `git status` pruefen, "
            f"dann die Lock-Datei loeschen.")
    try:
        os.write(fd, ("pid=%d" % os.getpid()).encode())
        os.close(fd)
        yield
    finally:
        _LOCK.unlink(missing_ok=True)


def _zeilenende(inhalt: bytes) -> bytes:
    """CRLF oder LF? Die Suchtexte oben sind mit LF geschrieben, im
    Arbeitsverzeichnis liegen die Dateien wegen core.autocrlf aber als CRLF."""
    return CRLF if CRLF in inhalt else LF


def _atomar_schreiben(pfad: Path, inhalt: bytes) -> None:
    """Temp-Datei IM ZIELVERZEICHNIS + os.replace — sonst ist es nicht atomar."""
    tmp = pfad.with_suffix(pfad.suffix + ".mutation-tmp")
    with open(tmp, "wb") as fh:
        fh.write(inhalt)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, pfad)


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

    unbemerkt, beschaedigt = [], []
    for nr, (beschreibung, datei, suchen, ersetzen) in enumerate(MUTATIONEN, 1):
        pfad = _ROOT / datei
        original = pfad.read_bytes()
        le = _zeilenende(original)
        such_b = suchen.encode("utf-8").replace(LF, le)
        ersatz_b = ersetzen.encode("utf-8").replace(LF, le)

        treffer = original.count(such_b)
        if treffer != 1:
            print(f"{nr:>2}. [UNGUELTIG] {beschreibung}")
            print(f"      Suchtext {treffer}x in {datei}, erwartet genau 1x —")
            print(f"      die Mutation greift ins Leere und beweist nichts.")
            unbemerkt.append(f"{beschreibung} (Suchtext {treffer}x)")
            continue

        try:
            _atomar_schreiben(pfad, original.replace(such_b, ersatz_b, 1))
            erkannt = not waechter_laeuft_durch()
        finally:
            _atomar_schreiben(pfad, original)
            if pfad.read_bytes() != original:          # nachweisen, nicht hoffen
                beschaedigt.append(datei)
                print(f"      [ALARM] {datei} nicht wiederhergestellt — "
                      f"`git checkout -- {datei}` ausfuehren!")

        print(f"{nr:>2}. {'[erkannt]  ' if erkannt else '[UNBEMERKT]'} {beschreibung}")
        if not erkannt:
            unbemerkt.append(beschreibung)

    print("\n" + "=" * 78)
    if beschaedigt:
        print(f"[FAIL] Nicht wiederhergestellt: {', '.join(sorted(set(beschaedigt)))}")
        return 1
    if not waechter_laeuft_durch():
        print("[FAIL] Nach dem Test ist der Waechter rot — `git diff` pruefen!")
        return 1
    if unbemerkt:
        print(f"[FAIL] {len(unbemerkt)} von {len(MUTATIONEN)} Mutationen blieben "
              f"unbemerkt — dort ist der Waechter Scheinsicherheit:")
        for u in unbemerkt:
            print(f"   - {u}")
        return 1
    print(f"[OK] Alle {len(MUTATIONEN)} Mutationen wurden erkannt. Der Waechter "
          f"kann rot werden — und wird es bei jedem bekannten Fehler.")
    return 0


if __name__ == "__main__":
    try:
        with _exklusiver_lauf():
            sys.exit(main())
    except LockBelegt as e:
        print(f"[ABBRUCH] {e}")
        sys.exit(1)
