"""Seitenprobe der Kurslader-Umstellung (docs/TICKER_LADEN.md, Abnahme A4).

Fährt scripts/js/probe_seiten_kurse.js je Seite und Fall zweimal — gegen den Stand VOR der Umstellung (aktueller Baum +
wörtliche alte Dateien aus scripts/fixtures/kurse_vorher/) und gegen den Arbeitsbaum — und verlangt:
  * beide Läufe vollständig (Endmarker, Ruhe erreicht, kein Absturz, keine Seitenfehler),
  * eine nicht leere Anzeige mit den erwarteten Bausteinen (zwei leere Ergebnisse beweisen nichts),
  * GLEICHE Anzeige (sichtbarer Inhalt) und GLEICHE Chart-Serien.
Die Kursanfragen werden nur berichtet (gebündelt dürfen es weniger sein; ihren Vertrag prüft verify_kurse.py).

Fälle: normal · vollfehler (jede Abfrage der ganzen Historie scheitert) · ttl (16 min später scheitert die ganze
Historie, der Zeitraum-Regler zeichnet neu).

Aufruf: py -3.14 scripts/verify_seiten_kurse.py   (braucht: npm ci --prefix scripts/perf)
"""
import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

WURZEL = pathlib.Path(__file__).resolve().parent.parent
PROBE = WURZEL / "scripts" / "js" / "probe_seiten_kurse.js"

SEITEN = {
    # Seite: (Fälle, Bausteine, die in der Anzeige stehen MÜSSEN)
    "dashboard": (("normal", "vollfehler", "ttl"), ("Saison-Score", "Stress-Ampel", "Anomalie-Radar")),
}


FIXTURES = WURZEL / "scripts" / "fixtures" / "kurse_vorher"
EINBINDUNG = re.compile(r'[ \t]*<script src="/landing/js/kurse\.js"></script>\r?\n')


def vorher_baum(ziel):
    """Stand VOR der Umstellung ohne Git-Historie (der Deploy klont nur zwei Commits tief): aktueller landing/
    (ohne en/ und data/-Ausgaben, die die Probe nicht braucht) + die wörtlichen alten Dateien aus FIXTURES, ohne
    kurse.js und ohne dessen Einbindung."""
    alt = ziel / "landing"
    shutil.copytree(WURZEL / "landing", alt, ignore=shutil.ignore_patterns("en", "*.png", "*.jpg", "*.webp"))
    for f in FIXTURES.rglob("*"):
        if f.is_file() and f.name != "LIESMICH.md":
            shutil.copyfile(f, alt / f.relative_to(FIXTURES))
    (alt / "js" / "kurse.js").unlink()
    for html in alt.rglob("*.html"):
        roh = html.read_bytes().decode("utf-8")
        neu = EINBINDUNG.sub("", roh)
        if neu != roh:
            html.write_bytes(neu.encode("utf-8"))
    rest = [h for h in alt.rglob("*.html") if "landing/js/kurse.js" in h.read_text(encoding="utf-8")]
    if rest:
        raise SystemExit("Vorher-Baum: kurse.js noch eingebunden in %s" % rest[:3])
    return alt


def lauf(wurzel, seite, fall):
    try:
        r = subprocess.run(["node", str(PROBE), str(wurzel), seite, fall], capture_output=True, text=True,
                           encoding="utf-8", timeout=180)
    except subprocess.TimeoutExpired:
        return None, "Frist überschritten"
    if r.returncode != 0:
        return None, "Exit %d: %s" % (r.returncode, (r.stderr or r.stdout)[-300:])
    try:
        d = json.loads(r.stdout)
    except ValueError:
        return None, "kein JSON: " + (r.stdout or r.stderr)[-300:]
    if d.get("absturz"):
        return None, "Absturz: " + d["absturz"][:300]
    if d.get("ende") is not True:
        return None, "ohne Endmarker"
    return d, None


def main():
    ergebnisse, ok = [], True

    def pruefe(name, bedingung, detail=""):
        nonlocal ok
        ergebnisse.append(("ok  " if bedingung else "FEHL") + " [%s] %s" % (name, detail))
        ok = ok and bool(bedingung)

    with tempfile.TemporaryDirectory() as tmp:
        alt_wurzel = vorher_baum(pathlib.Path(tmp))
        for seite, (faelle, bausteine) in SEITEN.items():
            for fall in faelle:
                a, fa = lauf(alt_wurzel, seite, fall)
                n, fn = lauf(WURZEL / "landing", seite, fall)
                name = "%s/%s" % (seite, fall)
                pruefe(name + " alt vollständig", a is not None, fa or "")
                pruefe(name + " neu vollständig", n is not None, fn or "")
                if a is None or n is None:
                    continue
                for v, d in (("alt", a), ("neu", n)):
                    pruefe("%s %s Ruhe erreicht" % (name, v), d["ruhig"])
                    pruefe("%s %s ohne Seitenfehler" % (name, v), not d["seitenfehler"], " | ".join(d["seitenfehler"])[:300])
                    fehlt = [b for b in bausteine if b not in d["inhalt"]]
                    pruefe("%s %s Anzeige vollständig" % (name, v), not fehlt and len(d["inhalt"]) > 500, "fehlt: %s" % fehlt)
                    pruefe("%s %s Charts gezeichnet" % (name, v),
                           len(d["charts"]) >= 3 and all(c["series"] not in ("null", "[]") for c in d["charts"]),
                           "%d Charts" % len(d["charts"]))
                gleich = a["inhalt"] == n["inhalt"]
                detail = ""
                if not gleich:
                    i = next((k for k in range(min(len(a["inhalt"]), len(n["inhalt"]))) if a["inhalt"][k] != n["inhalt"][k]),
                             min(len(a["inhalt"]), len(n["inhalt"])))
                    detail = "ab Zeichen %d: alt «%s» / neu «%s»" % (i, a["inhalt"][max(0, i - 40):i + 80],
                                                                    n["inhalt"][max(0, i - 40):i + 80])
                pruefe(name + " Anzeige gleich", gleich, detail)
                pruefe(name + " Chart-Serien gleich", a["charts"] == n["charts"],
                       "alt %d / neu %d Charts" % (len(a["charts"]), len(n["charts"])))
                ergebnisse.append("     %s Kursanfragen: alt %d, neu %d" % (name, len(a["kursanfragen"]), len(n["kursanfragen"])))
    for e in ergebnisse:
        sys.stdout.write(e + "\n")
    n_pr = sum(1 for e in ergebnisse if e.startswith(("ok", "FEHL")))
    sys.stdout.write("verify_seiten_kurse: %s (%d Prüfungen)\n" % ("BESTANDEN" if ok else "DURCHGEFALLEN", n_pr))
    if ok:
        sys.stdout.write("PROBE-ENDE %d Pruefungen\n" % n_pr)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
