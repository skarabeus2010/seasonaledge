# -*- coding: utf-8 -*-
"""Prüft die Wächter der Releasekennung (verify_einbindung.py, verify_release_sperre.py): baut Fehler ein und
verlangt Rot an der benannten Prüfung.

    py -3.14 scripts/verify_release_mutation.py

ERZWUNGEN ISOLIERT: alles geschieht in einer frischen Temp-Kopie (landing/ ohne en/ und große Ausgaben, shared/,
deploy/, .github/, blog/templates/, der Einbindungswächter). Der Einbindungswächter läuft AUS der Kopie, die Proben
der Sperre laufen aus dem Arbeitsbaum gegen die Kopie (`--basis`). Abschluss: Hash des Projektbaums vor = nach.

Beweisregeln wie in den übrigen Mutationstests: Endmarker, benannte Prüfung, ein Abbruch/fehlender Endmarker ist
kein Nachweis, Anker genau einmal, Gegenproben. Doppelt abgesicherte Stellen (z. B. Body-Prüfung vor UND nach dem
Lesen) werden gemeinsam mutiert — eine einzelne Linie zu entfernen bleibt dort zu Recht grün.
"""
from __future__ import annotations

import hashlib
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

WURZEL = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL))
from scripts.verify_twins_mutation import _atomar_schreiben, python_probe  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

MJ = "landing/js/methode.js"
KU = "landing/js/kurse.js"
APP = "landing/js/app.js"
DASH = "landing/pages/dashboard.html"
NG = "deploy/nginx.conf"
DY = ".github/workflows/deploy.yml"
RS = "deploy/release_setzen.py"
KM = "shared/kalender_methode.py"
PZ = "window.SA.__release('%%RELEASE%%');   // Releasekennung (landing/js/methode.js) — muss erste Anweisung bleiben\n"

# (Name, Lauf, Filter, [(Datei, alt, neu), …], erwartete Prüfung)
MUTATIONEN = [
    ("Prüfzeile fehlt in charts.js", "einbindung", None, [("landing/js/charts.js", PZ, "")], "[Prüfzeile: jede andere"),
    ("methode.js prüft sich nicht zuletzt", "einbindung", None,
     [(MJ, "})(window);\nwindow.SA.__release('%%RELEASE%%');", "})(window);")], "[Prüfzeile: methode.js prüft sich als letzte"),
    ("Seite ohne methode.js", "einbindung", None, [(DASH, '  <script src="/landing/js/methode.js"></script>\n', "")], "[Seiten: Bootstrap"),
    ("Analytics-Lader ohne Sperrprüfung", "einbindung", None,
     [(APP, "      if (SA.__gesperrt) return;   // Release-Sperre (methode.js): nach der Sperre nichts mehr nachladen\n", "")], "[Lader:"),
    ("nginx cacht /rechtliches 24 h", "einbindung", None,
     [(NG, '        # HTML immer neu validieren: Seite und Skripte tragen dieselbe Releasekennung (landing/js/methode.js)\n'
           '        add_header Cache-Control "public, max-age=0, must-revalidate";',
       '        add_header Cache-Control "public, max-age=86400";')], "[Betrieb: nginx location = /rechtliches"),
    ("Deploy ohne letzten Kennungsschritt", "einbindung", None,
     [(DY, '            python3 deploy/release_setzen.py "$RELEASE" || scheitern "release_setzen meldet abweichende Kennungen"\n', "")],
     "[Betrieb: Kennung als letzter Schritt"),
    ("EXIT-Falle setzt keine Kennung", "einbindung", None,
     [(DY, '                python3 deploy/release_setzen.py "$(git rev-parse HEAD)" >/dev/null 2>&1 \\', '                true \\')],
     "[Betrieb: EXIT-Falle"),
    ("Normalisieren trotz fremder Methode", "einbindung", None,
     [(RS, '        raise Verweigert("Methode %s statt %s" % (fremd[0], methode))', "        pass")], "[Simulation: fremde Methode"),
    ("Methoden laufen auseinander", "einbindung", None, [(KM, 'LESER = "alt"', 'LESER = "kalender_v1"')], "[Methode: methode.js = shared"),
    ("XHR an der Hülle vorbei", "einbindung", None,
     [(DASH, '  <script src="/landing/js/methode.js"></script>\n',
       '  <script src="/landing/js/methode.js"></script>\n  <script>var x = new XMLHttpRequest();</script>\n')], "[Datenwege"),
    # ── Transport (je Lader, ohne Hülle — sonst trüge methode.js) ──
    ("kurse: keine Prüfung vor fetch", "sperre", "transport b_poolwarte:sperre:ohne_huelle",
     [(KU, "        if (gesperrt()) throw sperrFehler('Anfrage nach Sperre');   // auch nach Poolwartezeit\n", "")],
     "(b) nach der Sperre keine weitere Anfrage"),
    ("kurse: Rückfall bei ReleaseFehler", "sperre", "transport d2_kein_rueckfall:sperre:ohne_huelle",
     [(KU, "          if (istRelease(e) || gesperrt()) throw istRelease(e) ? e : sperrFehler('kein Rückfall nach Sperre');\n", "")],
     "(d2) kein Rückfall nach der Sperre"),
    ("kurse: Übernahme ohne Prüfung", "sperre", "transport e_vor_uebernahme:sperre",
     [(KU, "      if (gesperrt()) throw sperrFehler('Bestand nach Sperre');   // nie veröffentlichen\n", "")], "(e) kein Bestand veröffentlicht"),
    ("supabase.get ohne Prüfung", "sperre", "transport f_supabase:sperre:ohne_huelle",
     [(APP, "    if (SA.__gesperrt) return Promise.reject(SA.ReleaseFehler ? new SA.ReleaseFehler('supabase.get nach Sperre') : new Error('Release-Sperre'));\n", "")],
     "(f) get nach Sperre"),
    # ── Seite ──
    ("Sperre ohne DOM-Ersatz", "sperre", "seite a_skript_neu",
     [(MJ, "      doc.body.replaceChildren(hinweis);", "      doc.body.appendChild(hinweis);")], "Dokument enthält nur den Hinweis"),
    ("Speicher-Hülle fehlt", "sperre", "seite g_nach_sperre",
     [(MJ, "        if (gesperrt && !intern) throw new ReleaseFehler('Speicher nach Sperre');\n", "")], "localStorage.setItem nach Sperre wirft"),
    ("Prüfzeile ohne Vorrang der Sperre", "sperre", "seite g_nach_sperre",
     [(MJ, "    if (gesperrt) throw new ReleaseFehler('Seite gesperrt');\n", "")], "nachgeladenes eigenes Skript läuft nicht"),
    ("Body nach Sperre lesbar", "sperre", "seite f_fetch_phasen",
     [(MJ, "          if (gesperrt) { abmelden(eintrag); return Promise.reject(new ReleaseFehler('Body nach Sperre')); }\n", ""),
      (MJ, "            abmelden(eintrag);\n            if (gesperrt) throw new ReleaseFehler('Body nach Sperre');\n", "            abmelden(eintrag);\n")],
     "(i) Body nach Sperre"),
    ("Neulademarke ignoriert", "sperre", "seite d_zweiter_versuch",
     [(MJ, "    if (alt && jetzt - alt < NEULADEN_SPERRE_MS) return false;\n", "")], "(d) Marke jünger"),
    ("Einfügehülle fehlt", "sperre", "seite g_nach_sperre",
     [(MJ, "      if (gesperrt && !intern) throw new ReleaseFehler(name + ' nach Sperre');\n      return orig.apply(this, arguments);\n    };\n  }\n  function huelleSetter",
       "      return orig.apply(this, arguments);\n    };\n  }\n  function huelleSetter")], "Einfügung nach Sperre wirft"),
    ("Chart-Hülle fehlt", "sperre", "seite g_nach_sperre",
     [(MJ, "      if (gesperrt) throw new ReleaseFehler('Chart nach Sperre');\n      var c = new Orig(el, opts);",
       "      var c = new Orig(el, opts);")], "neues Chart nach Sperre wirft"),
    ("fetch-Hülle lässt neue Anfragen durch", "sperre", "seite f2_body_waehrend",
     [(MJ, "      if (gesperrt) return Promise.reject(new ReleaseFehler('fetch nach Sperre'));\n", "")], "neuer fetch nach Sperre"),
    ("Request-Signal wird ersetzt", "sperre", "transport g_request_signal:sperre",
     [(MJ, "        var aufrufer = opt.signal || (eingabe && typeof eingabe === 'object' && eingabe.signal) || null;",
       "        var aufrufer = opt.signal;")], "(g) Abbruch über das Request-Signal"),
    ("nginx cacht /tools/ 24 h", "einbindung", None,
     [(NG, '        # HTML immer neu validieren (Releasekennung/Kalendermethode, V1b) — der Converter rechnet inline\n'
           '        add_header Cache-Control "public, max-age=0, must-revalidate";',
       '        add_header Cache-Control "public, max-age=86400";')], "[Betrieb: nginx location /tools/"),
    ("Tour-Lader ohne Sperrprüfung", "einbindung", None,
     [("landing/js/tour.js", "      if (window.SA && window.SA.__gesperrt) { reject(new Error('Seite gesperrt')); return; }\n", "")], "[Lader:"),
    ("ApexCharts-Setter umgeht die Hülle", "sperre", "bibliotheken",
     [(MJ, "      set: function (v) { apexWert = huelleCharts(v); }", "      set: function (v) { apexWert = v; }")],
     "mit_spaet: nach Sperre lehnen render und Konstruktor ab"),
]
UNGUELTIG_ERWARTET = [
    ("Anker existiert nicht", "einbindung", None, [(MJ, "diese Zeile gibt es nicht", "egal")]),
    ("Absturz: methode.js kaputt", "sperre", "seite gleich", [(MJ, "  'use strict';\n  var SA = window.SA", "  'use strict';\n  }}}\n  var SA = window.SA")]),
]

KOPIE = pathlib.Path()
ROH: dict = {}


def isolierte_kopie(ziel: pathlib.Path) -> pathlib.Path:
    ign = shutil.ignore_patterns("__pycache__", "en", "*.png", "*.jpg", "*.webp", "*.mp4", "gex_history")
    shutil.copytree(WURZEL / "landing", ziel / "landing", ignore=ign)
    for f in (ziel / "landing" / "data").glob("*"):
        if f.is_file() and f.stat().st_size > 2_000_000 and f.name != "tickers.json":
            f.unlink()
    for teil in ("shared", "deploy", ".github"):
        shutil.copytree(WURZEL / teil, ziel / teil, ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(WURZEL / "blog" / "templates", ziel / "blog" / "templates")
    (ziel / "scripts").mkdir()
    shutil.copy2(WURZEL / "scripts" / "verify_einbindung.py", ziel / "scripts" / "verify_einbindung.py")
    return ziel


def _fingerabdruck(w: pathlib.Path) -> str:
    h = hashlib.sha256()
    for teil in ("shared", "scripts", "deploy", ".github", "landing/js", "landing/pages", "blog/templates"):
        b = w / teil
        if not b.exists():
            continue
        for p in sorted(b.rglob("*")):
            if p.is_file() and "__pycache__" not in p.parts and "node_modules" not in p.parts:
                h.update(str(p.relative_to(w)).encode())
                h.update(p.read_bytes())
    for p in sorted(w.glob("landing/*.html")):
        h.update(p.read_bytes())
    return h.hexdigest()


def anker(datei, text):
    roh = ROH.setdefault(datei, (KOPIE / datei).read_bytes())
    if roh.count(b"\r\n") > roh.count(b"\n") // 2:
        text = text.replace("\r\n", "\n").replace("\n", "\r\n")
    return text.encode("utf-8")


def lauf(art, filt):
    env = {**os.environ, "PYTHONUTF8": "1"}
    if art == "einbindung":
        r = python_probe([KOPIE / "scripts" / "verify_einbindung.py"], capture_output=True, text=True, encoding="utf-8",
                         env=env, cwd=str(KOPIE))
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    befehl = [WURZEL / "scripts" / "verify_release_sperre.py", "--basis", str(KOPIE)] + (["--nur", filt] if filt else [])
    r = python_probe(befehl, capture_output=True, text=True, encoding="utf-8", env=env, cwd=str(WURZEL))
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def auswerten(rc, aus, erwartet):
    if rc == 0:
        return "entwischt", "Probe blieb grün"
    if "verify_einbindung:" not in aus and "verify_release_sperre:" not in aus:
        return "ungueltig", "die Probe brach ab statt durchzulaufen"
    if "kein Endmarker" in aus:
        return "ungueltig", "ein Fall brach ab (kein Endmarker) — kein Nachweis"
    zeilen = [z for z in aus.splitlines() if z.startswith("FEHL")]
    if not zeilen:
        return "ungueltig", "rot ohne inhaltliche Prüfung"
    if erwartet and not any(erwartet in z for z in zeilen):
        return "ungueltig", "erwartete Prüfung %s blieb grün; rot war: %s" % (erwartet, zeilen[0][:80])
    return "gefangen", zeilen[0][:80]


def bewerte(art, filt, aenderungen, erwartet=None):
    neu = {}
    for datei, alt, ne in aenderungen:
        a = anker(datei, alt)
        basis = neu.get(datei, ROH[datei])
        n = basis.count(a)
        if n != 1:
            return "ungueltig", "Anker %dx gefunden in %s, erwartet 1x" % (n, datei)
        neu[datei] = basis.replace(a, anker(datei, ne), 1)
    for d, b in neu.items():
        _atomar_schreiben(KOPIE / d, b)
    try:
        rc, aus = lauf(art, filt)
    finally:
        for d in neu:
            _atomar_schreiben(KOPIE / d, ROH[d])
    return auswerten(rc, aus, erwartet)


def _main():
    for art in ("einbindung", "sperre"):
        rc, aus = lauf(art, "seite gleich" if art == "sperre" else None)
        if rc != 0:
            print("ABBRUCH: %s ist schon ohne Mutation rot.\n%s" % (art, aus[-1200:]))
            return 1
    print("Grundlinie: beide Wächter ohne Mutation grün (isolierte Kopie %s)\n" % KOPIE)
    gefangen, probleme, urteil_ok = 0, [], True
    for name, art, filt, aend, erwartet in MUTATIONEN:
        ergebnis, warum = bewerte(art, filt, aend, erwartet)
        print(("  gefangen       %s" % name) if ergebnis == "gefangen" else ("  %-12s   %s  (%s)" % (ergebnis.upper(), name, warum)), flush=True)
        gefangen += ergebnis == "gefangen"
        if ergebnis != "gefangen":
            probleme.append(name)
    print("  -- Gegenprobe am Urteil dieses Tests --")
    for name, art, filt, aend in UNGUELTIG_ERWARTET:
        ergebnis, warum = bewerte(art, filt, aend)
        if ergebnis == "ungueltig":
            print("  richtig verworfen  %s  (%s)" % (name, warum))
        else:
            print("  FALSCH EINGEORDNET %s  -> %s" % (name, ergebnis))
            urteil_ok = False
    rc1, _ = lauf("einbindung", None)
    rc2, _ = lauf("sperre", "seite gleich")
    print("\n" + ("wiederhergestellt: beide Wächter wieder grün" if rc1 == 0 and rc2 == 0 else "WARNUNG: nach Wiederherstellung ROT!"))
    print("%d von %d Mutationen gefangen" % (gefangen, len(MUTATIONEN)))
    for p in probleme:
        print("  " + p)
    return 0 if (gefangen == len(MUTATIONEN) and urteil_ok and rc1 == 0 and rc2 == 0) else 1


def main():
    global KOPIE
    vorher = _fingerabdruck(WURZEL)
    temp = pathlib.Path(tempfile.mkdtemp(prefix="sa_release_mut_")).resolve()
    if temp == WURZEL or WURZEL in temp.parents:
        print("ABBRUCH: Temp-Verzeichnis liegt im Projektbaum")
        return 1
    try:
        KOPIE = isolierte_kopie(temp / "baum")
        rc = _main()
    finally:
        shutil.rmtree(temp, ignore_errors=True)
    if _fingerabdruck(WURZEL) != vorher:
        print("FEHL: der Projektbaum hat sich während des Tests verändert — Isolation verletzt")
        return 1
    print("Projektbaum unverändert (Hash vor = nach)")
    return rc


if __name__ == "__main__":
    sys.exit(main())
