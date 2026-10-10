"""Wächter für den Kurslader SA.kurse (Plan: docs/TICKER_LADEN.md, S1).

1. Probe: führt die ECHTE landing/js/kurse.js in node gegen einen PostgREST-Nachbau aus
   (scripts/js/probe_kurse.js) und verlangt jede Prüfung grün und mindestens MIN_PRUEFUNGEN Prüfungen.
2. Bestand: kein Kursabruf an /rest/v1/prices außerhalb von kurse.js in landing/ (DE-Quellen; landing/en/ wird
   daraus gebaut), keine Aufrufe der alten Lader, und jede Seite, die SA.kurse nutzt, bindet kurse.js VOR ihrem
   ersten Inline-Skript ein. Bis die Migration abgeschlossen ist, meldet --bestand nur (Exit 0); mit --streng
   ist jeder Fund ein Fehler.

Aufruf: py -3.14 scripts/verify_kurse.py [--bestand] [--streng]
"""
import argparse
import json
import pathlib
import re
import subprocess
import sys

WURZEL = pathlib.Path(__file__).resolve().parent.parent
LANDING = WURZEL / "landing"
MIN_PRUEFUNGEN = 119
MIN_HUELLEN = 65

ALTE_LADER = re.compile(r"\b(?:SA\.)?fetchAllPrices\s*\(|\bladeVollHistorie\s*\(")
DIREKT = re.compile(r"rest/v1/prices|supabase\.get\(\s*['\"]prices['\"]|getAll\(\s*['\"]prices['\"]")
NUTZT = re.compile(r"\bSA\.kurse\.")
EINBINDUNG = re.compile(r"<script[^>]+src=[\"'][^\"']*/landing/js/kurse\.js(?:\?[^\"']*)?[\"']", re.I)


FRIST_S = 20          # je Abschnitt; die längste reale Wartezeit im Abschnitt ist 1 s Retry-After (gesamt ~2 s)


def _node(*args):
    try:
        r = subprocess.run(["node", str(WURZEL / "scripts" / "js" / "probe_kurse.js"), *args],
                           capture_output=True, text=True, encoding="utf-8", timeout=FRIST_S)
    except subprocess.TimeoutExpired:
        return "haengt", "Frist %d s überschritten" % FRIST_S
    if r.returncode != 0:
        return None, "Exit %d: %s" % (r.returncode, (r.stderr or r.stdout)[-300:])
    try:
        return json.loads(r.stdout), None
    except ValueError:
        return None, "kein JSON: %s" % (r.stdout or r.stderr)[-300:]


def probe():
    """Jeder Abschnitt der Probe in einem eigenen node-Prozess (Isolation, Codex S1 R2). Verlangt je Abschnitt
    Exit 0, gültiges JSON und den Endmarker `ende` — ein Hänger oder Abbruch ist ein benannter Fehlschlag.
    Ausgabeformat der Mutationstests: "FEHL [Name] Detail", Abstürze als [Ausnahme]."""
    liste, fehler = _node("--liste")
    if fehler or not liste.get("abschnitte"):
        return False, ["  FEHL [Liste] " + (fehler or "keine Abschnitte")]
    meldungen, alle, vollstaendig, ausnahmen = [], [], True, False
    for nr, name in enumerate(liste["abschnitte"]):
        d, fehler = _node("--abschnitt", str(nr))
        # Ein HÄNGER ist ein benannter Befund dieses Abschnitts (er ist isoliert, die übrigen liefen) — der Lauf
        # gilt trotzdem als vollständig. Ein Abbruch (Exit ≠ 0, kein JSON, kein Endmarker, Absturz) nicht.
        if d == "haengt":
            meldungen.append("  FEHL [Abschnitt hängt: %s] %s" % (name, fehler))
            alle.append({"name": "Abschnitt hängt: " + name, "ok": False, "detail": fehler})
            continue
        if fehler:
            meldungen.append("  FEHL [Abschnitt bricht ab: %s] %s" % (name, " | ".join(fehler.splitlines())))
            vollstaendig = False
            continue
        if d.get("haengt"):
            meldungen.append("  FEHL [Abschnitt hängt: %s] Ereignisschleife leer, Abschnitt nicht beendet" % name)
            alle.append({"name": "Abschnitt hängt: " + name, "ok": False, "detail": "Ereignisschleife leer"})
        if d.get("absturz"):
            meldungen.append("  FEHL [Ausnahme] " + " | ".join(d["absturz"][:300].splitlines()))
        for a in d.get("ausnahmen", []):
            meldungen.append("  FEHL [Ausnahme] " + " | ".join(a.splitlines()))
        if d.get("ende") is not True:
            meldungen.append("  FEHL [Abschnitt ohne Endmarker: %s]" % name)
            vollstaendig = False
        if d.get("absturz"):
            vollstaendig = False
        if d.get("ausnahmen"):
            ausnahmen = True
        alle += d.get("pruefungen", [])
    rot = [x for x in alle if not x["ok"]]
    for x in rot:
        if not x["name"].startswith("Abschnitt hängt: "):
            meldungen.append("  FEHL [%s] %s" % (x["name"], x["detail"]))
    if len(alle) < MIN_PRUEFUNGEN:
        meldungen.append("  FEHL [Anzahl] nur %d Prüfungen (mindestens %d)" % (len(alle), MIN_PRUEFUNGEN))
    ok = vollstaendig and not ausnahmen and not rot and len(alle) >= MIN_PRUEFUNGEN
    meldungen.append("Probe: %d Abschnitte, %d Prüfungen, %d rot" % (len(liste["abschnitte"]), len(alle), len(rot)))
    # Endmarker nur, wenn JEDER Abschnitt vollständig durchlief — sonst gilt der Lauf als abgebrochen
    if vollstaendig:
        meldungen.append("PROBE-ENDE %d Pruefungen" % len(alle))
    return ok, meldungen


def huellen():
    """Rückgabe je Aufrufer vor/nach der Umstellung gleich: alte Lader (wörtlich, scripts/fixtures/
    kurse_alte_lader.js) gegen die Hüllen aus den echten Dateien (scripts/js/probe_kurse_huellen.js)."""
    try:
        r = subprocess.run(["node", str(WURZEL / "scripts" / "js" / "probe_kurse_huellen.js")],
                           capture_output=True, text=True, encoding="utf-8", timeout=120)
    except subprocess.TimeoutExpired:
        return False, ["  FEHL [Hüllen hängen]"]
    try:
        d = json.loads(r.stdout)
    except ValueError:
        return False, ["  FEHL [Hüllen: kein JSON] Exit %d %s" % (r.returncode, (r.stderr or r.stdout)[-300:])]
    meldungen = []
    if d.get("absturz"):
        meldungen.append("  FEHL [Ausnahme] Hüllen: " + " | ".join(d["absturz"][:300].splitlines()))
    rot = [x for x in d.get("pruefungen", []) if not x["ok"]]
    for x in rot:
        meldungen.append("  FEHL [%s] %s" % (x["name"], x["detail"]))
    n = len(d.get("pruefungen", []))
    ok = r.returncode == 0 and d.get("ende") is True and not d.get("absturz") and not rot and n >= MIN_HUELLEN
    if n < MIN_HUELLEN:
        meldungen.append("  FEHL [Anzahl Hüllen] nur %d (mindestens %d)" % (n, MIN_HUELLEN))
    meldungen.append("Hüllen: %d Prüfungen, %d rot" % (n, len(rot)))
    return ok, meldungen


def dateien():
    for f in sorted(LANDING.rglob("*")):
        if f.suffix not in (".html", ".js") or not f.is_file():
            continue
        rel = f.relative_to(LANDING).as_posix()
        if rel.startswith("en/") or rel.startswith("vendor/") or rel == "js/kurse.js":
            continue
        yield f, rel


def bestand():
    funde = []
    for f, rel in dateien():
        text = f.read_text(encoding="utf-8")
        for nr, zeile in enumerate(text.splitlines(), 1):
            if DIREKT.search(zeile):
                funde.append("%s:%d direkter Kursabruf" % (rel, nr))
            if ALTE_LADER.search(zeile) and not re.search(r"^\s*(\*|//)", zeile):
                funde.append("%s:%d alter Lader" % (rel, nr))
        if f.suffix == ".html" and NUTZT.search(text):
            m = EINBINDUNG.search(text)
            inline = re.search(r"<script(?![^>]*\bsrc=)[^>]*>", text, re.I)
            if not m:
                funde.append("%s nutzt SA.kurse, bindet kurse.js nicht ein" % rel)
            elif inline and inline.start() < m.start() and NUTZT.search(text[inline.start():m.start()]):
                funde.append("%s nutzt SA.kurse vor der Einbindung" % rel)
    return funde


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--bestand", action="store_true")
    ap.add_argument("--streng", action="store_true")
    a = ap.parse_args(argv)
    ok, meldungen = probe()
    ok_h, meldungen_h = huellen()
    ok = ok and ok_h
    meldungen = meldungen_h + meldungen      # Endmarker der Probe zuletzt
    for m in meldungen:
        sys.stdout.write(m + "\n")
    if a.bestand or a.streng:
        funde = bestand()
        for m in funde:
            sys.stdout.write("BESTAND  " + m + "\n")
        sys.stdout.write("Bestand: %d Funde%s\n" % (len(funde), "" if a.streng else " (nur gemeldet)"))
        if a.streng and funde:
            ok = False
    sys.stdout.write("verify_kurse: %s\n" % ("BESTANDEN" if ok else "DURCHGEFALLEN"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
