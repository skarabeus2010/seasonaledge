"""Einbindungswächter für Releasekennung und Kalendermethode (docs/KALENDER_UMSTELLUNG.md V1b; ersetzt das
Isolations-Gate C P3a). Statische Prüfungen + eine Simulation von deploy/release_setzen.py auf einer Kopie.

    py -3.14 scripts/verify_einbindung.py

1. Jede eigene JS-Datei unter landing/js/ hat `window.SA.__release('…')` als ERSTE Anweisung; methode.js als LETZTE.
2. Jede HTML unter landing/ (ohne en/) und jedes Blog-Template mit eigenem Skript: Kennung + Methode im
   Inline-Skript vor dem ersten eigenen Skript, methode.js ist das erste eigene Skript; ApexCharts (falls
   eingebunden) steht VOR methode.js (sonst greift die Chart-Hülle nicht). boersenkalender.js bindet keine Seite ein.
3. Eine Methode überall: methode.js `METHODE` = shared/kalender_methode.LESER = `__SA_METHODE` jeder Seite.
4. Keine Datenwege an der fetch-Hülle vorbei: XMLHttpRequest, sendBeacon, EventSource, WebSocket, indexedDB,
   caches.open, `.body.getReader`, Speicherzugriff per Zuweisung (`localStorage.x =`, `localStorage[…] =`).
5. Jeder dynamische Lader (`createElement('script'|'link'|'img'|'iframe')`) prüft `__gesperrt` im selben Block.
6. Betrieb: deploy.yml bestimmt RELEASE einmal, normalisiert nach dem Vorspulen, setzt die Kennung als letzten
   Schritt nach allen HTML-Erzeugern und stellt sie in der EXIT-Falle her; inject_credentials.sh nimmt RELEASE als
   Cache-Buster; nginx liefert /rechtliches, /ueber-uns und /landing/*.html mit must-revalidate.
7. Simulation release_setzen.py auf einer Kopie: Normalisieren alter Ausgaben ohne Bootstrap, Setzen einer Kennung,
   Abschlussprüfung grün; eine Ausgabe mit fremder Methode → Exit 3 und keine Datei verändert.
"""
from __future__ import annotations

import hashlib
import importlib.util
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

WURZEL = pathlib.Path(__file__).resolve().parent.parent
JS = WURZEL / "landing" / "js"
sys.path.insert(0, str(WURZEL))
_spec = importlib.util.spec_from_file_location("release_setzen", WURZEL / "deploy" / "release_setzen.py")
rs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rs)

ERGEBNIS, OK = [], True
PRUEFZEILE = re.compile(r"window\.SA\.__release\('[^'\\]*'\);")


def pruefe(name, bedingung, detail=""):
    global OK
    ERGEBNIS.append(("ok  " if bedingung else "FEHL") + " [%s] %s" % (name, detail))
    OK = OK and bool(bedingung)


def lesen(p):
    return p.read_bytes().decode("utf-8")


def ohne_kommentare_anfang(text: str) -> int:
    i, n = 0, len(text)
    while i < n:
        if text[i] in " \t\r\n\ufeff":
            i += 1
        elif text.startswith("//", i):
            j = text.find("\n", i)
            i = n if j < 0 else j + 1
        elif text.startswith("/*", i):
            j = text.find("*/", i + 2)
            i = n if j < 0 else j + 2
        else:
            return i
    return n


def letzte_anweisung(text: str) -> str:
    zeilen = [z.strip() for z in text.replace("\r\n", "\n").split("\n")]
    zeilen = [z for z in zeilen if z and not z.startswith("//")]
    return zeilen[-1] if zeilen else ""


def js_dateien():
    return sorted(JS.glob("*.js"))


def html_dateien():
    out = [p for p in sorted((WURZEL / "landing").rglob("*.html")) if "en" not in p.relative_to(WURZEL / "landing").parts[:1]]
    out += sorted((WURZEL / "blog" / "templates").glob("*.html"))
    return out


def pruefzeilen():
    fehlt = []
    for p in js_dateien():
        t = lesen(p)
        if p.name == "methode.js":
            pruefe("Prüfzeile: methode.js prüft sich als letzte Anweisung",
                   PRUEFZEILE.fullmatch(letzte_anweisung(t)) is not None, letzte_anweisung(t)[:60])
            vorn = t[ohne_kommentare_anfang(t):]
            pruefe("Prüfzeile: methode.js beginnt NICHT mit der Prüfung (Bootstrap)", not PRUEFZEILE.match(vorn))
            continue
        vorn = t[ohne_kommentare_anfang(t):]
        if not PRUEFZEILE.match(vorn):
            fehlt.append(p.name)
    pruefe("Prüfzeile: jede andere eigene JS-Datei beginnt mit ihr", not fehlt, fehlt)


def seiten():
    methode_js = rs.JS_METHODE.search(lesen(JS / "methode.js")).group(1)
    from shared import kalender_methode
    pruefe("Methode: methode.js = shared/kalender_methode.LESER", methode_js == kalender_methode.LESER,
           "%s / %s" % (methode_js, kalender_methode.LESER))
    befunde, apex, boerse, methoden = [], [], [], set()
    anzahl = 0
    for p in html_dateien():
        t = lesen(p)
        skripte = list(rs.EIGENES_SKRIPT.finditer(t))
        if not skripte:
            continue
        anzahl += 1
        for b in rs.html_pruefen(t, "%%RELEASE%%"):
            befunde.append("%s: %s" % (p.relative_to(WURZEL), b))
        methoden.update(m.group(1) for m in rs.HTML_METHODE.finditer(t))
        m_pos = next((m.start() for m in skripte if m.group(1) == "methode"), None)
        a = re.search(r'<script[^>]*src="[^"]*apexcharts[^"]*"', t)
        if a and m_pos is not None and a.start() > m_pos:
            apex.append(str(p.relative_to(WURZEL)))
        if any(m.group(1) == "boersenkalender" for m in skripte):
            boerse.append(str(p.relative_to(WURZEL)))
    pruefe("Seiten: Bootstrap vollständig und methode.js zuerst (%d Seiten)" % anzahl, not befunde, befunde[:5])
    # ApexCharts steht auf einigen Seiten HINTER den eigenen Skripten. methode.js hüllt es deshalb über einen
    # Setter auf window.ApexCharts (auch späte Zuweisung); die Wirkung belegt die Sperrprobe mit echten Seiten.
    mj = lesen(JS / "methode.js")
    pruefe("Seiten: Chart-Hülle unabhängig von der Ladereihenfolge (%d Seiten laden ApexCharts später)" % len(apex),
           "Object.defineProperty(window, 'ApexCharts'" in mj and "set: function (v) { apexWert = huelleCharts(v); }" in mj)
    pruefe("Seiten: boersenkalender.js von keiner Seite eingebunden (bis zur Umschaltung)", not boerse, boerse[:3])
    pruefe("Methode: jede Seite trägt die Methode aus methode.js", methoden == {methode_js}, sorted(methoden))


VERBOTEN = [
    (r"\bXMLHttpRequest\b", "XMLHttpRequest"), (r"\bsendBeacon\s*\(", "sendBeacon"), (r"\bnew\s+EventSource\b", "EventSource"),
    (r"\bnew\s+WebSocket\b", "WebSocket"), (r"\bindexedDB\b", "indexedDB"), (r"\bcaches\.open\b", "Cache-API"),
    (r"\.body\.getReader\b", "Body-Stream"), (r"\b(?:local|session)Storage\s*\.\s*(?!getItem|setItem|removeItem|clear|key|length)\w+\s*=[^=]", "Speicher per Zuweisung"),
    (r"\b(?:local|session)Storage\s*\[[^\]]+\]\s*=[^=]", "Speicher per Index"),
]


def datenwege():
    treffer = []
    quellen = [(p, lesen(p)) for p in js_dateien()]
    for p in html_dateien():
        t = lesen(p)
        inline = "\n".join(re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", t, re.S | re.I))
        quellen.append((p, inline))
    for p, t in quellen:
        for muster, name in VERBOTEN:
            if re.search(muster, t):
                treffer.append("%s: %s" % (p.relative_to(WURZEL), name))
    pruefe("Datenwege: nur fetch (keine XHR/Beacon/WebSocket/IndexedDB/Speicherzuweisung)", not treffer, treffer[:6])


LADER = re.compile(r"createElement\(\s*['\"](script|link|img|iframe)['\"]\s*\)")


def lader():
    ohne = []
    quellen = [(p, lesen(p)) for p in js_dateien() if p.name != "methode.js"]
    quellen += [(p, lesen(p)) for p in html_dateien()]
    gesamt = 0
    for p, t in quellen:
        for m in LADER.finditer(t):
            gesamt += 1
            # Prüfung im selben Funktionsblock: die nächste vorangehende `function` bis zum Treffer
            start = t.rfind("function", 0, m.start())
            block = t[start if start >= 0 else 0:m.start()]
            if "__gesperrt" not in block:
                ohne.append("%s:%d (%s)" % (p.relative_to(WURZEL), t.count("\n", 0, m.start()) + 1, m.group(1)))
    pruefe("Lader: jeder dynamische Ressourcenlader prüft __gesperrt (%d Stellen)" % gesamt, not ohne, ohne[:6])


def betrieb():
    dy = lesen(WURZEL / ".github" / "workflows" / "deploy.yml")
    i_rel = dy.find("RELEASE=$(git rev-parse HEAD)")
    i_norm = dy.find("python3 deploy/release_setzen.py '%%RELEASE%%'")
    i_trap = dy.find("trap release_falle EXIT")
    i_reset = dy.find("git checkout -- landing/ 2>/dev/null || true")
    i_vorspulen = dy.find('if ! bash "$SA_TMP/pruefe_commit.sh"; then')
    i_inject = dy.find('bash deploy/inject_credentials.sh /opt/seasonaledge "$RELEASE"')
    i_seo = dy.find("python3 seo/programmatic_seo_builder.py")
    i_blog = dy.find("blog/blog_builder.py --build")
    i_en = dy.find("python3 landing/build_en.py --write")
    i_final = dy.find('python3 deploy/release_setzen.py "$RELEASE" || scheitern')
    pruefe("Betrieb: EXIT-Falle vor dem ersten Eingriff in landing/ (deckt Vorspulen + Normalisieren)",
           0 <= i_trap < i_reset < i_vorspulen < i_rel, (i_trap, i_reset, i_vorspulen, i_rel))
    pruefe("Betrieb: Kennung einmal bestimmt, sofort normalisiert, dann injiziert",
           0 <= i_rel < i_norm < i_inject, (i_rel, i_norm, i_inject))
    pruefe("Betrieb: Kennung als letzter Schritt nach allen HTML-Erzeugern",
           i_final > max(i_seo, i_blog, i_en, i_inject) and min(i_seo, i_blog, i_en) >= 0, i_final)
    falle = re.search(r"release_falle\(\)\s*\{(.*?)\r?\n\s*\}\r?\n", dy, re.S)
    pruefe("Betrieb: EXIT-Falle setzt die Kennung des dann aktuellen Commits",
           bool(falle) and 'release_setzen.py "$(git rev-parse HEAD)"' in falle.group(1))
    inj = lesen(WURZEL / "deploy" / "inject_credentials.sh")
    pruefe("Betrieb: inject_credentials nimmt RELEASE als Cache-Buster", "GIT_SHA=${2:-" in inj)
    ng = lesen(WURZEL / "deploy" / "nginx.conf")
    for loc in ("location = /rechtliches", "location = /ueber-uns", r"location ~* ^/landing/[^/]+\.html$",
                "location /tools/"):
        i = ng.find(loc)
        block = ng[i:ng.find("}", i)] if i >= 0 else ""
        pruefe("Betrieb: nginx %s must-revalidate" % loc, "max-age=0, must-revalidate" in block)


def baum_hash(wurzel):
    h = hashlib.sha256()
    for p in sorted(wurzel.rglob("*")):
        if p.is_file():
            h.update(str(p.relative_to(wurzel)).encode())
            h.update(p.read_bytes())
    return h.hexdigest()


def simulation():
    with tempfile.TemporaryDirectory() as t:
        k = pathlib.Path(t)
        shutil.copytree(WURZEL / "landing" / "js", k / "landing" / "js")
        for p in (WURZEL / "landing").glob("*.html"):
            (k / "landing").mkdir(exist_ok=True)
            shutil.copy2(p, k / "landing" / p.name)
        shutil.copytree(WURZEL / "landing" / "pages", k / "landing" / "pages")
        # alte EN-/Blog-Ausgaben OHNE Bootstrap (Stand vor V1b) und mit alter Kennung
        (k / "landing" / "en").mkdir()
        (k / "landing" / "en" / "alt.html").write_text(
            '<html><body><script src="/landing/js/app.js?v=abc1234"></script></body></html>', encoding="utf-8")
        (k / "blog" / "output" / "post").mkdir(parents=True)
        (k / "blog" / "output" / "post" / "index.html").write_text(
            "<html><body><script>window.__SA_RELEASE='abc1234';window.__SA_METHODE='alt';</script>\n"
            '<script src="/landing/js/methode.js"></script>\n<script src="/landing/js/app.js"></script></body></html>',
            encoding="utf-8")
        def lauf(*args):
            return subprocess.run([sys.executable, str(WURZEL / "deploy" / "release_setzen.py"), *args,
                                   "--wurzel", str(k)], capture_output=True, text=True, encoding="utf-8")
        r = lauf("%%RELEASE%%")
        pruefe("Simulation: Normalisieren alter Ausgaben (mit/ohne Bootstrap) → konsistent", r.returncode == 0,
               (r.stdout + r.stderr)[-200:])
        sha = "0123456789abcdef0123456789abcdef01234567"
        r = lauf(sha)
        roh_en = (k / "landing" / "en" / "alt.html").read_text(encoding="utf-8")
        pruefe("Simulation: Kennung gesetzt und geprüft", r.returncode == 0 and ("window.__SA_RELEASE='%s'" % sha) in roh_en,
               (r.stdout + r.stderr)[-200:])
        js_ok = all(("SA.__release('%s')" % sha) in lesen(p) for p in (k / "landing" / "js").glob("*.js"))
        pruefe("Simulation: jede JS-Datei trägt die Kennung", js_ok)
        # Methodenwechsel: eine Ausgabe trägt eine andere Methode → Verweigerung, nichts geschrieben
        fremd = k / "blog" / "output" / "post" / "index.html"
        fremd.write_text(lesen(fremd).replace("window.__SA_METHODE='alt'", "window.__SA_METHODE='kalender_v1'"),
                         encoding="utf-8")
        vorher = baum_hash(k)
        r = lauf("fedcba9876543210fedcba9876543210fedcba98")
        pruefe("Simulation: fremde Methode → Exit 3, nichts geschrieben", r.returncode == 3 and baum_hash(k) == vorher,
               "Exit %s" % r.returncode)
        r = lauf("kaputt;rm")
        pruefe("Simulation: ungültige Kennung abgelehnt", r.returncode == 2, "Exit %s" % r.returncode)


def main():
    pruefzeilen()
    seiten()
    datenwege()
    lader()
    betrieb()
    simulation()
    for e in ERGEBNIS:
        sys.stdout.write(e + "\n")
    n = len(ERGEBNIS)
    sys.stdout.write("verify_einbindung: %s (%d Prüfungen)\n" % ("BESTANDEN" if OK else "DURCHGEFALLEN", n))
    if OK:
        sys.stdout.write("PROBE-ENDE %d Pruefungen\n" % n)
    return 0 if OK else 1


if __name__ == "__main__":
    sys.exit(main())
