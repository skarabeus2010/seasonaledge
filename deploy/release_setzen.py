#!/usr/bin/env python3
"""Releasekennung setzen und Bootstrap sicherstellen (docs/KALENDER_UMSTELLUNG.md V1b, Entwurf v3 §1 / v4 §1).

    python3 deploy/release_setzen.py <wert> [--wurzel DIR] [--baum landing --baum blog/output ...] [--nur-pruefen]

Für jede HTML-Datei unter den Bäumen, die ein eigenes Skript (`/landing/js/<name>.js`) einbindet:
  - fehlt der Bootstrap, wird er unmittelbar vor dem ersten eigenen Skript eingefügt:
        <script>window.__SA_RELEASE='<wert>';window.__SA_METHODE='<methode>';</script>
        <script src="/landing/js/methode.js"></script>
  - jede Kennung (`window.__SA_RELEASE='…'`) wird auf <wert> gesetzt.
Für jede eigene JS-Datei unter `landing/js/` wird jede Kennung (`SA.__release('…')`, in methode.js zusätzlich
`var RELEASE = '…'`) auf <wert> gesetzt.

Grenze: Normalisieren ist nur ohne Methodenwechsel erlaubt. Trägt eine HTML eine andere Methode
(`window.__SA_METHODE`) als `methode.js`, wird NICHTS geschrieben (Exit 3) — ein Methodenwechsel läuft nur über V9.

Abschlussprüfung (immer, mit --nur-pruefen ausschließlich): jede Fundstelle trägt <wert>, jede HTML mit eigenem
Skript hat den Bootstrap und bindet methode.js vor jedem anderen eigenen Skript ein. Fehler → Exit 1.
Jede Datei wird atomar geschrieben (Temp-Datei im Zielordner + os.replace, Rechte der Zieldatei bleiben).
"""
from __future__ import annotations

import argparse
import os
import pathlib
import re
import sys
import tempfile

PLATZHALTER = "%%RELEASE%%"
STANDARD_BAEUME = ("landing", "blog/output", "seo/tools")
EIGENES_SKRIPT = re.compile(r'<script\b[^>]*\bsrc="/landing/js/([A-Za-z0-9_.-]+)\.js(?:\?v=[A-Za-z0-9]+)?"[^>]*>\s*</script>',
                            re.IGNORECASE)
HTML_KENNUNG = re.compile(r"window\.__SA_RELEASE='([^'\\]*)'")
HTML_METHODE = re.compile(r"window\.__SA_METHODE='([^'\\]*)'")
JS_KENNUNG = re.compile(r"SA\.__release\('([^'\\]*)'\)")
JS_METHODE_RELEASE = re.compile(r"var RELEASE = '([^'\\]*)';")
JS_METHODE = re.compile(r"var METHODE = '([^'\\]*)';")
GUELTIG = re.compile(r"^(%%RELEASE%%|[0-9a-f]{7,40})$")


class Verweigert(Exception):
    pass


def lesen(pfad: pathlib.Path) -> str:
    """Bytes 1:1 als Text (Zeilenenden bleiben erhalten — read_text würde CRLF in LF umwandeln)."""
    return pfad.read_bytes().decode("utf-8")


def vor_zeile(text: str, pos: int, zeile: str) -> str:
    """Fügt `zeile` als eigene Zeile vor der Zeile ein, in der `pos` liegt — mit deren Einrückung und Zeilenende."""
    anfang = text.rfind("\n", 0, pos) + 1
    einzug = text[anfang:pos] if text[anfang:pos].strip() == "" else ""
    nl = "\r\n" if "\r\n" in text else "\n"
    return text[:anfang] + einzug + zeile + nl + text[anfang:]


def atomar(pfad: pathlib.Path, text: str) -> None:
    daten = text.encode("utf-8")
    if pfad.read_bytes() == daten:
        return
    modus = pfad.stat().st_mode & 0o7777
    fd, tmp = tempfile.mkstemp(dir=str(pfad.parent), prefix=".rs-", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(daten)
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp, modus)
        os.replace(tmp, pfad)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def html_dateien(wurzel: pathlib.Path, baeume) -> list[pathlib.Path]:
    out = []
    for b in baeume:
        basis = wurzel / b
        if basis.is_dir():
            out += sorted(p for p in basis.rglob("*.html") if p.is_file())
    return out


def html_normalisieren(text: str, wert: str, methode: str) -> tuple[str, list[str]]:
    """Gibt den neuen Text und Befunde (für die Prüfung) zurück."""
    skripte = list(EIGENES_SKRIPT.finditer(text))
    if not skripte:
        return text, []
    fremd = [m.group(1) for m in HTML_METHODE.finditer(text) if m.group(1) != methode]
    if fremd:
        raise Verweigert("Methode %s statt %s" % (fremd[0], methode))
    # 1) methode.js fehlt → vor das erste eigene Skript
    if not any(m.group(1) == "methode" for m in skripte):
        text = vor_zeile(text, skripte[0].start(), '<script src="/landing/js/methode.js"></script>')
        skripte = list(EIGENES_SKRIPT.finditer(text))
    # 2) Kennung fehlt → Inline-Skript vor das erste eigene Skript
    if not HTML_KENNUNG.search(text):
        text = vor_zeile(text, skripte[0].start(),
                         "<script>window.__SA_RELEASE='%s';window.__SA_METHODE='%s';</script>" % (wert, methode))
    # 3) Werte setzen; Methode ergänzen, wo eine ältere Fassung nur die Kennung trug
    text = HTML_KENNUNG.sub("window.__SA_RELEASE='%s'" % wert, text)
    if not HTML_METHODE.search(text):
        text = HTML_KENNUNG.sub(lambda m: m.group(0) + ";window.__SA_METHODE='%s'" % methode, text, count=1)
    # Reihenfolge wird NICHT umsortiert: steht methode.js nicht vorn, meldet es die Prüfung.
    return text, []


def html_pruefen(text: str, wert: str) -> list[str]:
    befunde = []
    skripte = list(EIGENES_SKRIPT.finditer(text))
    if not skripte:
        return befunde
    kennungen = [m.group(1) for m in HTML_KENNUNG.finditer(text)]
    if not kennungen:
        befunde.append("kein window.__SA_RELEASE")
    elif any(k != wert for k in kennungen):
        befunde.append("Kennung %s statt %s" % (sorted(set(kennungen)), wert))
    if skripte[0].group(1) != "methode":
        befunde.append("erstes eigenes Skript ist %s.js, nicht methode.js" % skripte[0].group(1))
    k_pos = min((m.start() for m in HTML_KENNUNG.finditer(text)), default=None)
    if k_pos is not None and k_pos > skripte[0].start():
        befunde.append("Kennung erst nach dem ersten eigenen Skript gesetzt")
    if not HTML_METHODE.search(text):
        befunde.append("kein window.__SA_METHODE")
    return befunde


def js_normalisieren(name: str, text: str, wert: str) -> str:
    text = JS_KENNUNG.sub("SA.__release('%s')" % wert, text)
    if name == "methode.js":
        text = JS_METHODE_RELEASE.sub("var RELEASE = '%s';" % wert, text)
    return text


def js_pruefen(name: str, text: str, wert: str) -> list[str]:
    befunde = []
    kennungen = [m.group(1) for m in JS_KENNUNG.finditer(text)]
    if name == "methode.js":
        kennungen += [m.group(1) for m in JS_METHODE_RELEASE.finditer(text)]
    if not kennungen:
        befunde.append("keine Prüfzeile")
    elif any(k != wert for k in kennungen):
        befunde.append("Kennung %s statt %s" % (sorted(set(kennungen)), wert))
    return befunde


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("wert")
    ap.add_argument("--wurzel", default=str(pathlib.Path(__file__).resolve().parent.parent))
    ap.add_argument("--baum", action="append")
    ap.add_argument("--nur-pruefen", action="store_true")
    a = ap.parse_args(argv)
    if not GUELTIG.match(a.wert):
        sys.stderr.write("release_setzen: ungültiger Wert %r\n" % a.wert)
        return 2
    wurzel = pathlib.Path(a.wurzel)
    baeume = a.baum or list(STANDARD_BAEUME)
    js_ordner = wurzel / "landing" / "js"
    m = JS_METHODE.search(lesen(js_ordner / "methode.js"))
    if not m:
        sys.stderr.write("release_setzen: METHODE in methode.js nicht gefunden\n")
        return 2
    methode = m.group(1)

    html = html_dateien(wurzel, baeume)
    js = sorted(js_ordner.glob("*.js"))
    if not a.nur_pruefen:
        # erst alles berechnen (Verweigerung schreibt nichts), dann schreiben
        neu = {}
        try:
            for p in html:
                t = lesen(p)
                n, _ = html_normalisieren(t, a.wert, methode)
                if n != t:
                    neu[p] = n
        except Verweigert as e:
            sys.stderr.write("release_setzen: VERWEIGERT (%s) — nichts geschrieben; Methodenwechsel nur über V9\n" % e)
            return 3
        for p in js:
            t = lesen(p)
            n = js_normalisieren(p.name, t, a.wert)
            if n != t:
                neu[p] = n
        for p, n in neu.items():
            atomar(p, n)
        sys.stdout.write("release_setzen: %d Dateien auf %s gesetzt\n" % (len(neu), a.wert))

    fehler = []
    for p in html:
        for b in html_pruefen(lesen(p), a.wert):
            fehler.append("%s: %s" % (p.relative_to(wurzel), b))
    for p in js:
        for b in js_pruefen(p.name, lesen(p), a.wert):
            fehler.append("%s: %s" % (p.relative_to(wurzel), b))
    for f in fehler[:40]:
        sys.stderr.write("release_setzen: FEHLER %s\n" % f)
    if fehler:
        sys.stderr.write("release_setzen: %d Befunde\n" % len(fehler))
        return 1
    sys.stdout.write("release_setzen: geprüft — %d HTML, %d JS, Kennung %s\n" % (len(html), len(js), a.wert))
    return 0


if __name__ == "__main__":
    sys.exit(main())
