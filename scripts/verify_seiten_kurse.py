"""Seitenprobe der Kurslader-Umstellung (docs/TICKER_LADEN.md, Abnahme A4).

Fährt scripts/js/probe_seiten_kurse.js je Seite und Fall zweimal — gegen den Stand VOR der Umstellung (aktueller Baum +
wörtliche alte Dateien aus scripts/fixtures/kurse_vorher/) und gegen den Arbeitsbaum — und verlangt:
  * beide Läufe vollständig (Endmarker, Ruhe erreicht, kein Absturz, keine Seitenfehler),
  * eine nicht leere Anzeige mit den erwarteten Bausteinen (zwei leere Ergebnisse beweisen nichts),
  * GLEICHE Anzeige (sichtbarer Inhalt) und GLEICHE Chart-Serien.
Die Kursanfragen werden nur berichtet (gebündelt dürfen es weniger sein; ihren Vertrag prüft verify_kurse.py).

Fälle: normal · vollfehler (jede Abfrage der ganzen Historie scheitert) · ttl (16 min später scheitert die ganze
Historie, der Zeitraum-Regler zeichnet neu) · blockfehler (ab dem zweiten Block scheitert jede Ladung dauerhaft).

Beabsichtigte Korrekturen haben ein eigenes Soll statt „gleich wie vorher":
  * Dashboard-Overnight lud ohne Pagination nur die ersten 1000 Zeilen. Soll = der ALTE Code auf vollständigen
    Daten (Nachbau mit --ohne-obergrenze) — dieselbe Rechnung, nur ohne die Kürzung.
  * blockfehler: die alten lokalen Lader hängten den Fehlerkörper als „Zeile" an und rechneten weiter. Soll = die
    Seite zeigt den Ladefehler (`prices 500`) — der alte Stand wird nur berichtet.

Aufruf: py -3.14 scripts/verify_seiten_kurse.py   (braucht: npm ci --prefix scripts/perf)
"""
import concurrent.futures
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

WURZEL = pathlib.Path(__file__).resolve().parent.parent
PROBE = WURZEL / "scripts" / "js" / "probe_seiten_kurse.js"

SEITEN = {
    # Seite: (Fälle, Bausteine, die in der Anzeige stehen MÜSSEN, mindestens n Charts)
    "dashboard": (("wechsel", "zeitraum", "normal", "vollfehler", "ttl", "blockfehler"), ("Saison-Score", "Stress-Ampel", "Anomalie-Radar"), 3),
    "jahreszyklus": (("normal", "blockfehler"), (), 1),
    "ki-saisonalitaet": (("normal", "blockfehler"), ("Saison-Score",), 1),
    "risikozyklus": (("normal", "blockfehler"), (), 1),
    "overnight": (("normal", "blockfehler"), (), 1),
    "tdom-analyse": (("normal", "blockfehler"), (), 1),
    "wochentage": (("wechsel", "rueckwechsel", "normal", "blockfehler"), (), 1),
    "backtest-engine": (("wechsel", "rueckwechsel", "normal", "blockfehler"), (), 1),
    "opex": (("wechsel", "normal", "blockfehler"), (), 1),
    "vixpiration": (("wechsel", "normal", "blockfehler"), (), 1),
    "spot-vol-beta": (("wechsel", "normal", "blockfehler"), (), 1),
    "embed": (("normal", "blockfehler"), ("Saisonalitäts-Chart",), 1),
}
# Seiten, deren Vorher-Stand eine beabsichtigte Kürzung hatte: Vergleich gegen den alten Code ohne Kürzung
OHNE_OBERGRENZE_ALT = {"dashboard"}


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


def endstand(charts):
    """Was zuletzt in jedem Chart-Element steht: die letzte Erzeugung bzw. deren letzte Aktualisierung. Beim
    Wechsel zeichnet die Seite zusätzlich die Charts von A — verglichen wird, was am Ende zu sehen ist."""
    aus = {}
    for c in charts:
        aus[c["el"]] = c["updates"][-1] if c["updates"] else c["series"]
    return aus


def unterschied(a, n):
    i = next((k for k in range(min(len(a), len(n))) if a[k] != n[k]), min(len(a), len(n)))
    return "ab Zeichen %d: «%s» / «%s»" % (i, a[max(0, i - 40):i + 80], n[max(0, i - 40):i + 80])


def vollstaendig(pruefe, name, d, bausteine, min_charts, seite):
    """Ruhe, keine Seitenfehler, Anzeige mit Bausteinen, gefüllte Charts — für JEDEN verglichenen Lauf (Codex M3 R1:
    ein Endmarker allein genügt nicht)."""
    pruefe(name + " Ruhe erreicht", d["ruhig"])
    pruefe(name + " ohne Seitenfehler", not d["seitenfehler"], " | ".join(d["seitenfehler"])[:300])
    fehlt = [b for b in bausteine if b not in d["inhalt"]]
    pruefe(name + " Anzeige vollständig", not fehlt and len(d["inhalt"]) > (40 if seite == "embed" else 200),
           "fehlt: %s, %d Zeichen" % (fehlt, len(d["inhalt"])))
    gez = [c for c in d["charts"] if c["series"] not in ("null", "[]", None)]
    pruefe(name + " Charts gezeichnet", len(gez) >= min_charts, "%d von %d Charts mit Serien" % (len(gez), len(d["charts"])))


def _lauf_direkt(wurzel, seite, fall, *extra):
    try:
        r = subprocess.run(["node", str(PROBE), str(wurzel), seite, fall, *extra], capture_output=True, text=True,
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


_LAEUFE = {}
PARALLEL = int(os.environ.get("SEITEN_PARALLEL", "4"))


def lauf(wurzel, seite, fall, *extra):
    """Ergebnis eines node-Laufs — aus dem parallel vorab gefüllten Speicher, sonst direkt."""
    k = (str(wurzel), seite, fall) + tuple(extra)
    if k not in _LAEUFE:
        _LAEUFE[k] = _lauf_direkt(wurzel, seite, fall, *extra)
    return _LAEUFE[k]


def benoetigte_laeufe(alt_wurzel):
    """Jeder node-Lauf, den die Auswertung in main() braucht — dieselbe Fallunterscheidung."""
    neu, jobs = WURZEL / "landing", []
    soll = {"wechsel": "direkt", "rueckwechsel": "normal", "zeitraum": "zeitraum_direkt"}
    for seite, (faelle, _b, _m) in SEITEN.items():
        for fall in faelle:
            jobs.append((neu, seite, fall))
            if fall in soll:
                jobs += [(neu, seite, soll[fall]), (alt_wurzel, seite, fall), (alt_wurzel, seite, soll[fall])]
            elif fall == "blockfehler":
                jobs.append((alt_wurzel, seite, fall))
            else:
                extra = ("--ohne-obergrenze",) if seite in OHNE_OBERGRENZE_ALT else ()
                jobs.append((alt_wurzel, seite, fall) + extra)
                if extra and fall == "normal":
                    jobs.append((alt_wurzel, seite, fall))
    return list(dict.fromkeys(jobs))


def main():
    ergebnisse, ok = [], True

    def pruefe(name, bedingung, detail=""):
        nonlocal ok
        ergebnisse.append(("ok  " if bedingung else "FEHL") + " [%s] %s" % (name, detail))
        ok = ok and bool(bedingung)

    with tempfile.TemporaryDirectory() as tmp:
        alt_wurzel = vorher_baum(pathlib.Path(tmp))
        # Die Läufe sind voneinander unabhängig (je eigener node-Prozess) → parallel vorab; ausgewertet wird danach
        # in fester Reihenfolge. SEITEN_PARALLEL=1 erzwingt den seriellen Lauf.
        jobs = benoetigte_laeufe(alt_wurzel)
        with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, PARALLEL)) as ex:
            for job, erg in zip(jobs, ex.map(lambda j: _lauf_direkt(*j), jobs)):
                _LAEUFE[(str(job[0]),) + tuple(job[1:])] = erg
        for seite, (faelle, bausteine, min_charts) in SEITEN.items():
            for fall in faelle:
                name = "%s/%s" % (seite, fall)
                n, fn = lauf(WURZEL / "landing", seite, fall)
                pruefe(name + " neu vollständig", n is not None, fn or "")
                if fall in ("wechsel", "rueckwechsel", "zeitraum"):
                    # Abrufkennung: ein verspäteter Abschluss darf die neuere Ansicht nicht überschreiben. Soll je Fall:
                    #   wechsel → „nur B gewählt", rueckwechsel → „normal", zeitraum → „nur 5 Jahre gewählt".
                    # Der alte Stand wird nur berichtet.
                    soll_fall = {"wechsel": "direkt", "rueckwechsel": "normal", "zeitraum": "zeitraum_direkt"}[fall]
                    d, fd = lauf(WURZEL / "landing", seite, soll_fall)
                    pruefe(name + " Soll-Lauf (%s) vollständig" % soll_fall, d is not None, fd or "")
                    for v, x in (("neu", n), ("soll", d)):
                        if x is not None:
                            vollstaendig(pruefe, "%s %s" % (name, v), x, bausteine, min_charts, seite)
                    if n is not None and d is not None:
                        pruefe(name + " Anzeige nach Wechsel = direkt gewählt", n["inhalt"] == d["inhalt"],
                               "" if n["inhalt"] == d["inhalt"] else unterschied(d["inhalt"], n["inhalt"]))
                        pruefe(name + " Charts nach Wechsel = direkt gewählt", endstand(n["charts"]) == endstand(d["charts"]),
                               "%d / %d Chart-Elemente" % (len(endstand(n["charts"])), len(endstand(d["charts"]))))
                    a, _ = lauf(alt_wurzel, seite, fall)
                    ad, _ = lauf(alt_wurzel, seite, soll_fall)
                    ergebnisse.append("     %s alter Stand nach Wechsel = direkt: %s" % (
                        name, "ja" if a and ad and a["inhalt"] == ad["inhalt"] else "NEIN (verspätete Antwort überschrieb)"))
                    continue
                if fall == "blockfehler":
                    # beabsichtigte Korrektur: der neue Stand zeigt den Ladefehler; der alte wird nur berichtet
                    a, _ = lauf(alt_wurzel, seite, fall)
                    if n is not None:
                        pruefe(name + " neu zeigt den Ladefehler", "prices 500" in n["inhalt"],
                               n["inhalt"][:160])
                        pruefe(name + " neu ohne Seitenfehler", not n["seitenfehler"], " | ".join(n["seitenfehler"])[:300])
                    ergebnisse.append("     %s alt zeigte den Fehler: %s" % (name, "ja" if a and "prices 500" in a["inhalt"] else "nein"))
                    continue
                extra = ("--ohne-obergrenze",) if seite in OHNE_OBERGRENZE_ALT else ()
                a, fa = lauf(alt_wurzel, seite, fall, *extra)
                pruefe(name + " alt vollständig", a is not None, fa or "")
                if a is None or n is None:
                    continue
                for v, d in (("alt", a), ("neu", n)):
                    pruefe("%s %s Ruhe erreicht" % (name, v), d["ruhig"])
                    pruefe("%s %s ohne Seitenfehler" % (name, v), not d["seitenfehler"], " | ".join(d["seitenfehler"])[:300])
                    fehlt = [b for b in bausteine if b not in d["inhalt"]]
                    pruefe("%s %s Anzeige vollständig" % (name, v), not fehlt and len(d["inhalt"]) > (40 if seite == "embed" else 200),
                           "fehlt: %s, %d Zeichen" % (fehlt, len(d["inhalt"])))
                    gez = [c for c in d["charts"] if c["series"] not in ("null", "[]", None)]
                    pruefe("%s %s Charts gezeichnet" % (name, v), len(gez) >= min_charts,
                           "%d von %d Charts mit Serien" % (len(gez), len(d["charts"])))
                gleich = a["inhalt"] == n["inhalt"]
                detail = ""
                if not gleich:
                    i = next((k for k in range(min(len(a["inhalt"]), len(n["inhalt"]))) if a["inhalt"][k] != n["inhalt"][k]),
                             min(len(a["inhalt"]), len(n["inhalt"])))
                    detail = "ab Zeichen %d: alt «%s» / neu «%s»" % (i, a["inhalt"][max(0, i - 40):i + 80],
                                                                    n["inhalt"][max(0, i - 40):i + 80])
                soll = " (Soll: alter Code ohne Kürzung)" if extra else ""
                pruefe(name + " Anzeige gleich" + soll, gleich, detail)
                pruefe(name + " Chart-Serien gleich" + soll, a["charts"] == n["charts"],
                       "alt %d / neu %d Charts" % (len(a["charts"]), len(n["charts"])))
                ergebnisse.append("     %s Kursanfragen: alt %d, neu %d" % (name, len(a["kursanfragen"]), len(n["kursanfragen"])))
                if extra and fall == "normal":
                    # Nachweis, dass die Korrektur etwas korrigiert: der alte Stand MIT Kürzung zeigt anderes
                    k, _ = lauf(alt_wurzel, seite, fall)
                    pruefe(name + " alter Stand mit Kürzung weicht ab (Korrektur wirkt)", k is not None and k["inhalt"] != n["inhalt"])
    for e in ergebnisse:
        sys.stdout.write(e + "\n")
    n_pr = sum(1 for e in ergebnisse if e.startswith(("ok", "FEHL")))
    sys.stdout.write("verify_seiten_kurse: %s (%d Prüfungen)\n" % ("BESTANDEN" if ok else "DURCHGEFALLEN", n_pr))
    if ok:
        sys.stdout.write("PROBE-ENDE %d Pruefungen\n" % n_pr)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
