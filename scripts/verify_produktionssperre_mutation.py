# -*- coding: utf-8 -*-
"""Prüft den Wächter verify_produktionssperre.py: baut Fehler ein und verlangt Rot an der benannten Prüfung.

    py -3.14 scripts/verify_produktionssperre_mutation.py

ERZWUNGEN ISOLIERT: der Test kopiert den nötigen Teil des Baums in ein frisches Temp-Verzeichnis und mutiert,
startet und prüft NUR dort. Eine Mutation wie „Marke wird nicht geprüft" lässt echte Pflicht-Skripte anlaufen —
deren Dateiausgaben landen im Temp-Baum, Datenbank/Mail/Netz sind tot. Am Ende wird nachgewiesen, dass der
Projektbaum byte-gleich geblieben ist (Hash vor/nach). Ohne Produktionsmounts: logs/ wird nicht kopiert, jede
Probe nimmt ihr eigenes Sperrverzeichnis.

Beweisregeln wie in den übrigen Mutationstests (Endmarker, benannte Prüfung, Ausnahme ≠ Nachweis, Anker genau
einmal, Gegenproben). Lock-Mutationen brauchen fcntl; ohne fcntl werden sie als „nur Linux" übersprungen und im
strengen Modus (SA_SPERRE_STRENG=1) verlangt.
"""
from __future__ import annotations

import hashlib
import os
import pathlib
import shutil
import sys
import tempfile

WURZEL = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL))
from scripts.verify_twins_mutation import _atomar_schreiben, python_probe  # noqa: E402
from scripts.verify_produktionssperre import isolierte_kopie  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PS = "shared/produktionssperre.py"
SC = "shared/supabase_client.py"
NIGHTLY = "scripts/nightly_refresh.py"
KAL = "scripts/build_calendar_data.py"
DAILY = "scripts/daily_newsletter.py"
TIMERS = "deploy/install_timers.sh"
DEPLOY = ".github/workflows/deploy.yml"
UNIT = "deploy/systemd/sa-nightly.service"
WF_SCAN = ".github/workflows/full_scanner.yml"
WF_FLOWS = ".github/workflows/flows_update.yml"
NEU = "scripts/zz_mutation_neuer_schreiber.py"
PROBE = "scripts/verify_produktionssperre.py"

try:
    import fcntl  # noqa: F401
    HAT_FCNTL = True
except ImportError:
    HAT_FCNTL = False

MUTATIONEN = [
    ("Pflicht-Skript ohne Sperre", NIGHTLY,
     '    with produktion("nightly_refresh"):\n        sys.exit(main())', '    sys.exit(main())',
     "[Einbau: nightly_refresh.py]"),
    ("Sperre mit falschem Namen", NIGHTLY,
     'with produktion("nightly_refresh"):', 'with produktion("nightly"):', "[Einbau: nightly_refresh.py]"),
    ("Kalenderbauer ohne Sperre schreibt Dateien", KAL,
     '    with produktion("build_calendar_data"):\n', '    if True:\n',
     "[Echt: gesperrte Läufe erzeugen keine Ausgabedateien]"),
    ("Marke wird nicht geprüft", PS,
     "    marke = _marke(verz)\n    if marke is None:\n        return\n    if kennung != marke:",
     "    marke = _marke(verz)\n    return\n    if kennung != marke:",
     "[Verhalten: Marke ohne Kennung"),
    ("jede Kennung wird angenommen", PS, "    if kennung != marke:", "    if not kennung:",
     "[Verhalten: falsche Kennung"),
    ("passende Kennung wird abgelehnt", PS, "    if kennung != marke:", "    if True:",
     "[Verhalten: passende Kennung läuft"),
    ("Freigabeliste ignoriert", PS, "    if not darf:", "    if False:",
     "[Verhalten: Kennung für nicht freigegebenen Lauf"),
    ("verschachtelter Lauf nicht geprüft", PS, '        _sperren(name, _kennung(), verz)\n        _zustand["tiefe"] += 1',
     '        _zustand["tiefe"] += 1',
     "[Verhalten: verschachtelter"),
    ("Import ohne Sperre", NIGHTLY, '    modul_sperre("nightly_refresh")', "    pass",
     "[Einbau: nightly_refresh.py sperrt beim Import]"),
    ("Ausführung prüft nicht", SC, "                with schreibsperre(self._kanal):", "                if True:",
     "[Schreibschutz: vor der Aktivierung aufgebaute Anfrage"),
    ("Flows prüft unterdrückte Panels", WF_FLOWS, 'geplant unterdrueckt"; continue\n', 'geplant unterdrueckt"\n',
     "[Betrieb: flows_update.yml nimmt unterdrückte Panels"),
    ("Modus nicht geprüft", PS, "    if flag is not None and flag not in sys.argv[1:]:", "    if False:",
     "[Verhalten: Kennung ohne freigegebenen Modus"),
    ("Kennung wird vererbt", PS, '_KENNUNG.append(os.environ.pop("SA_AKTIVIERUNG", ""))',
     '_KENNUNG.append(os.environ.get("SA_AKTIVIERUNG", ""))', "[Verhalten: Kennung wird nicht vererbt]"),
    ("kein Betriebsnachweis", PS, 'verz / "unterdrueckt.log", "a"', 'verz / "anderswo.log", "a"',
     "[Verhalten: Unterdrückung hinterlässt Betriebsnachweis]"),
    ("Schreibschutz aus", PS, "    marke = _marke(verz)\n    if marke is None:\n        return\n    f = _freigabe",
     "    return\n    f = _freigabe", "[Schreibschutz: Import-Einstieg"),
    ("lesende Freigabe darf schreiben", PS, 'if f is not None and f["schreiben"] and', "if f is not None and",
     "[Schreibschutz: lesende Freigabe"),
    ("prices nicht geschützt", PS, '    "prices", "tdom_stats",', '    "tdom_stats",',
     "[Schreibschutz: Import-Einstieg"),
    ("Client ungeschützt", SC, "_client = _Geschuetzt(create_client(url, key))", "_client = create_client(url, key)",
     "[Einbau: get_client() liefert den geschützten Client]"),
    ("Newsletter ohne Versandschutz", DAILY,
     '    pruefe_schreiben("daily_newsletter.versand")', '    pass',
     "[Einbau: daily_newsletter prüft vor dem Versand]"),
    ("Pflicht-Skript aus der Liste genommen", PS,
     '    "intraday_refresh.py": "Kurse + Tagesnummern",\n', '',
     "[Inventar: jedes schreibende Skript eingeordnet]"),
    ("install_timers startet trotz Marke", TIMERS,
     '  echo "install_timers: Aktivierungsmarke gesetzt — Timer werden NICHT gestartet"\n  exit 0\n',
     '  echo "install_timers: Aktivierungsmarke gesetzt — Timer werden NICHT gestartet"\n',
     "[Betrieb: install_timers.sh prüft die Marke"),
    ("Deploy ohne [ohne-deploy]-Bedingung", DEPLOY,
     "    if: ${{ !startsWith(github.event.head_commit.message, '[ohne-deploy]') }}\n", "",
     "[Betrieb: deploy.yml überspringt"),
    ("Deploy-Bedingung greift auf Erwähnung im Text", DEPLOY, "!startsWith(github.event.head_commit.message",
     "!contains(github.event.head_commit.message", "[Betrieb: deploy.yml überspringt"),
    ("Unit wertet 75 als Fehler", UNIT, "SuccessExitStatus=75\n", "",
     "[Betrieb: sa-nightly.service wertet 75 als Erfolg]"),
    ("Workflow ohne 75-Abbildung", WF_SCAN,
     '            if [ "$RC" = 75 ]; then echo "[full_scanner] Produktionssperre aktiv — Lauf geplant unterdrueckt"; RC=0; fi\n',
     "", "[Betrieb: full_scanner.yml bildet Exit 75 auf Erfolg ab]"),
]
NUR_LINUX = [
    ("Lock wird nicht genommen", PS,
     "            fcntl.flock(fd, fcntl.LOCK_SH)\n        _sperren(name, kennung, verz)",
     "            pass\n        _sperren(name, kennung, verz)",
     "[Verhalten: exklusiver Lock blockiert den Start]"),
    ("Ausführung ohne Lock", PS,
     "            fcntl.flock(fd, fcntl.LOCK_SH)\n        pruefe_schreiben(kanal)",
     "            pass\n        pruefe_schreiben(kanal)",
     "[Schreibschutz: laufende Ausführung hält aktivierung_setzen auf]"),
    ("aktivierung_setzen wartet nicht", PS, "                fcntl.flock(fd, fcntl.LOCK_EX)\n", "                pass\n",
     "[Verhalten: aktivierung_setzen wartet auf laufende Läufe]"),
    ("Modul-Sperre hält den Lock nicht", PS, "    _dauer_fds.append(dfd)", "    os.close(dfd)",
     "[Verhalten: aktivierung_setzen wartet auf einen Import-Einstieg]"),
    ("Modul-Sperre teilt den Lock mit dem Block", PS,
     "    verz.mkdir(parents=True, exist_ok=True)\n    dfd = os.open(",
     "    verz.mkdir(parents=True, exist_ok=True)\n    if _zustand[\"tiefe\"] > 0:\n"
     "        _sperren(name, _kennung(), verz)\n        return\n    dfd = os.open(",
     "[Verhalten: Import im äußeren Block hält den Lock"),
    ("Frist ignoriert", PS, "            if frist_s is None:\n", "            if True:\n",
     "[Verhalten: aktivierung_setzen mit Frist"),
]
NEUE_DATEI = ("unbekannter neuer Schreiber", NEU, 'x.table("prices").upsert([])\n',
              "[Inventar: jedes schreibende Skript eingeordnet]")
UNGUELTIG_ERWARTET = [
    ("Anker existiert nicht", PS, "diese Zeile gibt es nicht", "egal"),
    ("Absturz beim Import", PS, "EXIT_GESPERRT = 75", "EXIT_GESPERRT = 75\nnull_x = 1/0"),
]

KOPIE: pathlib.Path = pathlib.Path()
ROH: dict = {}


def _fingerabdruck(wurzel: pathlib.Path) -> str:
    """Hash über alle Dateien des Projektbaums, die ein Lauf erreichen könnte (ohne logs/ und Caches)."""
    h = hashlib.sha256()
    for teil in ("shared", "scripts", "deploy", ".github", "landing/data", "landing/js", "blog/posts"):
        basis = wurzel / teil
        if not basis.exists():
            continue
        for p in sorted(basis.rglob("*")):
            if p.is_file() and "__pycache__" not in p.parts and "node_modules" not in p.parts:
                h.update(str(p.relative_to(wurzel)).encode())
                h.update(p.read_bytes())
    return h.hexdigest()


def anker(datei, text):
    roh = ROH[datei]
    if roh.count(b"\r\n") > roh.count(b"\n") // 2:
        text = text.replace("\r\n", "\n").replace("\n", "\r\n")
    return text.encode("utf-8")


def lauf():
    env = {k: v for k, v in os.environ.items() if k not in ("SA_AKTIVIERUNG", "SA_SPERR_DIR")}
    env.update({"PYTHONUTF8": "1", "PYTHONPATH": str(KOPIE), "SUPABASE_URL": "http://127.0.0.1:9",
                "SUPABASE_KEY": "abgeschottet", "BREVO_API_KEY": ""})
    r = python_probe([KOPIE / PROBE], capture_output=True, text=True, encoding="utf-8", env=env, cwd=str(KOPIE))
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def auswerten(rc, aus, erwartet):
    if rc == 0:
        return "entwischt", "Probe blieb grün"
    if "PROBE-ENDE" not in aus and "verify_produktionssperre:" not in aus:
        return "ungueltig", "die Probe brach ab statt durchzulaufen"
    zeilen = [z for z in aus.splitlines() if z.startswith("FEHL")]
    if not zeilen:
        return "ungueltig", "rot ohne inhaltliche Prüfung"
    if erwartet and not any(erwartet in z for z in zeilen):
        return "ungueltig", "erwartete Prüfung %s blieb grün; rot war: %s" % (erwartet, zeilen[0][:70])
    return "gefangen", zeilen[0][:70]


def bewerte(datei, alt, neu, erwartet=None):
    a = anker(datei, alt)
    n = ROH[datei].count(a)
    if n != 1:
        return "ungueltig", "Anker %dx gefunden, erwartet 1x" % n
    _atomar_schreiben(KOPIE / datei, ROH[datei].replace(a, anker(datei, neu), 1))
    try:
        rc, aus = lauf()
    finally:
        _atomar_schreiben(KOPIE / datei, ROH[datei])
    return auswerten(rc, aus, erwartet)


def _main():
    rc, aus = lauf()
    if rc != 0:
        print("ABBRUCH: die Probe ist schon ohne Mutation rot.\n" + aus[-1500:])
        return 1
    print("Grundlinie: Probe ohne Mutation grün (isolierte Kopie %s)\n" % KOPIE)
    liste = list(MUTATIONEN)
    if HAT_FCNTL:
        liste += NUR_LINUX
    elif os.environ.get("SA_SPERRE_STRENG") == "1":
        print("ABBRUCH: strenger Modus ohne fcntl")
        return 1
    else:
        print("  übersprungen (nur Linux): " + ", ".join(m[0] for m in NUR_LINUX))
    gefangen, probleme, urteil_ok = 0, [], True
    for name, datei, alt, neu, erwartet in liste:
        art, warum = bewerte(datei, alt, neu, erwartet)
        print(("  gefangen       %s" % name) if art == "gefangen" else ("  %-12s   %s  (%s)" % (art.upper(), name, warum)))
        gefangen += art == "gefangen"
        if art != "gefangen":
            probleme.append(name)
    name, datei, inhalt, erwartet = NEUE_DATEI
    p = KOPIE / datei
    _atomar_schreiben(p, inhalt.encode("utf-8"))
    try:
        rc, aus = lauf()
    finally:
        p.unlink()
    art, warum = auswerten(rc, aus, erwartet)
    print(("  gefangen       %s" % name) if art == "gefangen" else ("  %-12s   %s  (%s)" % (art.upper(), name, warum)))
    gefangen += art == "gefangen"
    if art != "gefangen":
        probleme.append(name)
    print("  -- Gegenprobe am Urteil dieses Tests --")
    for name, datei, alt, neu in UNGUELTIG_ERWARTET:
        art, warum = bewerte(datei, alt, neu)
        if art == "ungueltig":
            print("  richtig verworfen  %s  (%s)" % (name, warum))
        else:
            print("  FALSCH EINGEORDNET %s  -> %s" % (name, art))
            urteil_ok = False
    rc_nach, _ = lauf()
    gesamt = len(liste) + 1
    print("\n" + ("wiederhergestellt: Probe läuft wieder grün" if rc_nach == 0 else "WARNUNG: Probe nach Wiederherstellung ROT!"))
    print("%d von %d Mutationen gefangen" % (gefangen, gesamt))
    for p in probleme:
        print("  " + p)
    return 0 if (gefangen == gesamt and urteil_ok and rc_nach == 0) else 1


def main():
    global KOPIE
    vorher = _fingerabdruck(WURZEL)
    temp = pathlib.Path(tempfile.mkdtemp(prefix="sa_sperre_mut_")).resolve()
    if temp == WURZEL or WURZEL in temp.parents:
        print("ABBRUCH: Temp-Verzeichnis liegt im Projektbaum")
        return 1
    try:
        KOPIE = isolierte_kopie(WURZEL, temp / "baum")
        ROH.update({d: (KOPIE / d).read_bytes()
                    for d in (PS, SC, NIGHTLY, KAL, DAILY, TIMERS, DEPLOY, UNIT, WF_SCAN, WF_FLOWS)})
        rc = _main()
    finally:
        shutil.rmtree(temp, ignore_errors=True)
    nachher = _fingerabdruck(WURZEL)
    if nachher != vorher:
        print("FEHL: der Projektbaum hat sich während des Tests verändert — Isolation verletzt")
        return 1
    print("Projektbaum unverändert (Hash vor = nach)")
    return rc


if __name__ == "__main__":
    sys.exit(main())
