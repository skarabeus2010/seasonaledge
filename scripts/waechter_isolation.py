#!/usr/bin/env python3
"""waechter_isolation.py — gemeinsame Isolation fuer Waechter, die Crons AUSFUEHREN.

Entstanden aus `verify_session_stamp.py` (acht Codex-Runden am 2026-09-25) und
herausgezogen, als `verify_skew_anzeige.py` dieselbe Isolation brauchte: eine
zweite Kopie wuerde driften wie die zwei Black-Scholes-Implementierungen mit
verschiedenen Zinssaetzen. Was hier steht, ist abgenommen — Aenderungen gehen
durch `verify_session_mutation.py`.

Zwei Teile:
  * Elternprozess: `starte_isoliert()` startet das Waechter-Skript mit
    `--isoliert <tmp>` in einem Unterprozess mit kontrollierter Umgebung und
    verlangt GENAU eine Bilanzzeile mit Nonce und vollstaendiger Probenliste.
  * Unterprozess: `nonce_sichern()` ganz am Anfang (vor jedem Cron-Import),
    `schreibsperre()` vor dem Import der Crons, `melde_bilanz()` am Ende.

Was die Schreibsperre leistet: jeder Schreibzugriff ausserhalb des
Temp-Verzeichnisses wird protokolliert UND verhindert (PermissionError aus dem
Audit-Hook) — egal ob per open, write_text, mkdir, os.replace oder Link.
Was sie nicht leistet: Schutz gegen absichtlich boesartigen Code (vererbte
Datei-Handles sind bewusst ausgeklammert). Sie ist ein Regressionsschutz.
"""
from __future__ import annotations
import os
import re
import secrets
import subprocess
import sys
import tempfile
from pathlib import Path

BILANZ_PRAEFIX = "ISOLIERT-BILANZ"

# Unter Windows ist die Konsole oft cp1252. Ein "Δ" in der Ausgabe liess den
# Elternprozess ohne PYTHONUTF8=1 mit UnicodeEncodeError abbrechen — der
# Waechter meldete dann Exit 1 ohne jeden Befund (Codex-Review 2026-09-25, R3).
# Alle Waechter importieren dieses Modul als Erstes; hier einmal umstellen.
for _strom in (sys.stdout, sys.stderr):
    try:
        _strom.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


# ── Unterprozess ─────────────────────────────────────────────────────────────
def nonce_sichern() -> str:
    """Nonce aus der Umgebung nehmen und dort LOESCHEN, bevor irgendein Cron-Modul
    importiert wird — sonst koennte eine Import-Nebenwirkung eine gruene Bilanz
    mit gueltiger Nonce faelschen (Codex-Review R6)."""
    return os.environ.pop("SA_PROBE_NONCE", "")


def melde_bilanz(nonce: str, fehler: int, proben: list[str]) -> None:
    print(f"{BILANZ_PRAEFIX} {nonce} {fehler} {','.join(proben)}", flush=True)


def schreibsperre(tmp_p: Path) -> list[str]:
    """Audit-Hook installieren; liefert die (lebende) Liste der Verstoesse.

    MUSS vor dem Import der Crons laufen: auch Import-Nebenwirkungen zaehlen.
    Ein einmal installierter Hook laesst sich nicht entfernen — deshalb nur im
    Unterprozess verwenden."""
    tmp_p = Path(tmp_p).resolve()
    verstoesse: list[str] = []

    # Das Nullgeraet ist kein Schreibzugriff auf echte Daten. Unter Windows
    # oeffnet `subprocess` es beim Import von Streamlit (ueber `platform`) mit
    # Schreibflags — ohne diese Ausnahme meldete der Hook dreimal
    # `open(nul, 130)` und der Waechter konnte umgebungsabhaengig nie gruen
    # werden (Codex-Review R7). Nur exakt das Geraet, kein Praefix-Vergleich.
    nullgeraete = {os.path.normcase(os.devnull), "nul", "/dev/null"}
    schreib_flags = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC

    def _innen(pfad) -> bool:
        roh = os.fsdecode(pfad)
        if os.path.normcase(roh) in nullgeraete:
            return True
        try:
            return Path(roh).resolve().is_relative_to(tmp_p)
        except Exception:
            return False

    def _pruefen(ereignis, args):
        if ereignis == "open":
            pfad, modus, flags = (list(args) + [None, None, None])[:3]
            if pfad is None or isinstance(pfad, int):
                return
            schreibt = (any(c in (modus or "") for c in "wax+")
                        or (modus is None and isinstance(flags, int) and flags & schreib_flags))
            if schreibt and not _innen(pfad):
                verstoesse.append(f"open({os.fsdecode(pfad)}, {modus or flags})")
        elif ereignis in ("os.mkdir", "os.remove", "os.rmdir", "os.chmod", "os.truncate"):
            if args and not isinstance(args[0], int) and not _innen(args[0]):
                verstoesse.append(f"{ereignis}({os.fsdecode(args[0])})")
        elif ereignis == "os.rename":
            # BEIDE Seiten: auch "extern -> Temp-Baum" veraendert das echte Repo
            # (die Quelle verschwindet dort). R6.
            if len(args) >= 2 and not (_innen(args[0]) and _innen(args[1])):
                verstoesse.append(f"os.rename({os.fsdecode(args[0])} -> {os.fsdecode(args[1])})")
        elif ereignis in ("os.link", "os.symlink"):
            # Ein Hardlink/Symlink im Temp-Baum auf eine echte Datei macht jede
            # spaetere Schreiboperation "innen" zu einer aussen. Kein legitimer
            # Cron-Pfad braucht Links -> grundsaetzlich sperren. R6.
            verstoesse.append(f"{ereignis}{tuple(os.fsdecode(a) for a in args[:2] if not isinstance(a, int))}")

    def _audit(ereignis, args):
        vorher = len(verstoesse)
        _pruefen(ereignis, args)
        if len(verstoesse) > vorher:
            # Nicht nur melden, sondern VERHINDERN: eine Mutation, die ins echte
            # Repo schreibt, darf im Test nichts anrichten. (In R3 hat genau so
            # eine Probe eine leere options_flow.json auf die Platte gelegt.)
            raise PermissionError(f"Waechter-Isolation: {verstoesse[-1]}")

    sys.addaudithook(_audit)
    # Temp-Dateien, die der Waechter selbst anlegt (tempfile), landen im
    # erlaubten Baum statt im System-Temp.
    tempfile.tempdir = str(tmp_p)
    return verstoesse


# ── Elternprozess ────────────────────────────────────────────────────────────
def starte_isoliert(skript: Path, erwartete_proben: tuple[str, ...], praefix: str) -> int:
    """Waechter-Skript isoliert ausfuehren; liefert die Fehlerzahl (>= 1 bei jedem
    Zweifel). Ein Unterprozess, der gar nicht erst laeuft oder keine gueltige
    Bilanz meldet, zaehlt als FEHLER — sonst waere ein blinder Lauf gruen (vier
    von fuenf "keine Freigabe" im Kern-Review waren solche Werkzeugfehler)."""
    nonce = secrets.token_hex(16)
    with tempfile.TemporaryDirectory(prefix=praefix) as tmp:
        env = {k: v for k, v in os.environ.items() if k != "MASSIVE_API_KEY"}
        env.update({"SA_OHNE_DOTENV": "1", "PYTHONDONTWRITEBYTECODE": "1",
                    "PYTHONUTF8": "1",
                    # build() ueberspringt ohne Schluessel die Ticker-Schleife —
                    # der Test waere dann stumm blind. Kein echter Schluessel.
                    "MASSIVE_API_KEY": "probe-kein-echter-schluessel",
                    "SA_PROBE_NONCE": nonce})
        r = subprocess.run([sys.executable, str(Path(skript).resolve()), "--isoliert", tmp],
                           cwd=tmp, env=env, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=600)
        for z in r.stdout.splitlines():
            if not z.startswith(BILANZ_PRAEFIX) and "streamlit" not in z and "No runtime found" not in z:
                print(z)
        # GENAU eine Bilanzzeile, striktes Format, eigene Nonce, vollstaendige
        # Probenliste, Exit passend zur Fehlerzahl. Alles andere ist kein Beweis
        # (R6: "BILANZ 8" gefolgt von "BILANZ 0" wurde als 0 Fehler akzeptiert).
        bilanz = [z for z in r.stdout.splitlines() if z.startswith(BILANZ_PRAEFIX)]
        muster = re.compile(rf"^{BILANZ_PRAEFIX} ([0-9a-f]{{32}}) (\d+) ([a-z_,]+)$")
        t = muster.match(bilanz[0]) if len(bilanz) == 1 else None
        n, grund = 0, None
        if len(bilanz) != 1:
            grund = f"{len(bilanz)} Bilanzzeilen statt genau einer"
        elif not t:
            grund = f"Bilanzzeile ohne gueltiges Format: {bilanz[0][:80]!r}"
        elif t.group(1) != nonce:
            grund = "Nonce stimmt nicht — die Zeile stammt nicht aus diesem Lauf"
        else:
            proben = t.group(3).split(",")
            n = int(t.group(2))
            if len(proben) != len(set(proben)) or set(proben) != set(erwartete_proben):
                grund = (f"Proben unvollstaendig/doppelt: fehlt "
                         f"{sorted(set(erwartete_proben) - set(proben))}, gemeldet {proben}")
            elif (n == 0) != (r.returncode == 0):
                grund = f"Bilanz {n} passt nicht zum Exit {r.returncode}"
        if grund:
            print(f"  FAIL {grund} (Exit {r.returncode}) — stderr:\n"
                  + "\n".join(r.stderr.splitlines()[-15:]))
            return 1
        return n
