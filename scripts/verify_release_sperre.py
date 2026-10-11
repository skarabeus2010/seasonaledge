"""Wächter für die Release-Sperre (docs/KALENDER_UMSTELLUNG.md V1b; Plan v8/v9, Entwurf v1–v6).

    py -3.14 scripts/verify_release_sperre.py [--basis <ordner>]

Führt jeden Fall der beiden Proben in einem EIGENEN Prozess aus (die Sperre ist nicht rücksetzbar) und verlangt
Endmarker, die erwarteten Prüfungen und kein Rot:
  - scripts/js/probe_release_transport.js — echte methode.js + kurse.js + SA.supabase: Sperre (a) zwischen
    Blöcken, (b) in der Poolwartezeit, (c) in einer Wiederholungspause, (d) während einer Rückfall-Ladung,
    (e) vor der Übernahme, (f) supabase.get/getAll — jeweils keine weitere Anfrage, kein Bestand, ReleaseFehler.
  - scripts/js/probe_release_seite.js — das echte Dashboard in jsdom: Abweichung in beide Richtungen und spät
    während der Rechnung, zweiter Versuch, Speicherfehler, fetch-Phasen, Skript/Einfügung/Speicher/Analytics nach
    der Sperre.
Zu jedem Sperrfall läuft die positive Kontrolle (`:kontrolle` bzw. `gleich`): ohne Sperre MUSS die beobachtete
Wirkung eintreten — sonst wäre ein grünes Ergebnis wertlos.
"""
from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import sys

WURZEL = pathlib.Path(__file__).resolve().parent.parent

TRANSPORT = ["a_zwischen_bloecken", "b_poolwarte", "c_wiederholung", "d_rueckfall", "d2_kein_rueckfall",
             "e_vor_uebernahme", "f_supabase", "g_request_signal"]
# Jeder Transportfall zweimal: mit der fetch-Hülle aus methode.js (Zusammenspiel) und OHNE sie — dann trägt nur
# der Lader selbst; sonst bliebe eine fehlende Prüfung in kurse.js/SA.supabase hinter der Hülle unsichtbar.
TRANSPORT_MODI = ("sperre", "kontrolle", "sperre:ohne_huelle", "kontrolle:ohne_huelle")
SEITE = ["gleich", "a_skript_neu", "a_skript_neu:kontrolle", "b_html_neu", "c_spaet", "c_spaet:kontrolle",
         "d_zweiter_versuch", "d_zweiter_versuch:kontrolle", "e_speicherfehler", "f_fetch_phasen",
         "f_fetch_phasen:kontrolle", "f2_body_waehrend", "f2_body_waehrend:kontrolle", "g_nach_sperre",
         "g_nach_sperre:kontrolle",
         # zweite echte Seite (Plan v8: u. a. Backtest-Engine und Dashboard)
         "gleich@backtest-engine", "a_skript_neu@backtest-engine", "a_skript_neu:kontrolle@backtest-engine",
         "c_spaet@backtest-engine", "c_spaet:kontrolle@backtest-engine"]
# Mindestzahl Prüfungen je Fall (ein Fall, der still weniger prüft, ist rot)
MINDEST = {"a_zwischen_bloecken": 3, "b_poolwarte": 2, "c_wiederholung": 2, "d_rueckfall": 3, "e_vor_uebernahme": 2,
           "f_supabase": 3, "d2_kein_rueckfall": 2, "gleich": 4, "a_skript_neu": 7, "b_html_neu": 7, "c_spaet": 7, "d_zweiter_versuch": 3,
           "e_speicherfehler": 2, "f_fetch_phasen": 1, "f2_body_waehrend": 2, "g_nach_sperre": 7,
           "g_request_signal": 1}


def lauf(skript, args, basis, kennung='{"fall"'):
    env = {**os.environ}
    r = subprocess.run(["node", str(WURZEL / "scripts" / "js" / skript), *args], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=env, timeout=180, cwd=str(basis))
    aus = r.stdout or ""
    zeile = next((z for z in aus.splitlines() if z.startswith(kennung)), None)
    if "PROBE-ENDE" not in aus or zeile is None:
        return None, "kein Endmarker (Exit %s): %s" % (r.returncode, (aus + (r.stderr or ""))[-300:])
    if r.returncode != 0:            # Ausgabe da, aber der Prozess scheiterte danach — kein Nachweis
        return None, "kein Endmarker (Exit %s nach der Ausgabe): %s" % (r.returncode, (r.stderr or "")[-200:])
    return json.loads(zeile), ""


def main():
    basis = pathlib.Path(sys.argv[sys.argv.index("--basis") + 1]) if "--basis" in sys.argv else WURZEL
    # --nur <teil>: nur Fälle, deren Name den Teil enthält (Mutationstest; im Gate immer alle)
    nur = sys.argv[sys.argv.index("--nur") + 1].split(",") if "--nur" in sys.argv else None
    passt = lambda name: nur is None or any(t in name for t in nur)
    if not shutil.which("node"):
        print("FEHL [Aufbau] node fehlt — UNGEPRÜFT ist nicht BESTANDEN")
        return 1
    fehler, n = [], 0
    for fall in TRANSPORT:
        for modus in TRANSPORT_MODI:
            if not passt("transport %s:%s" % (fall, modus)):
                continue
            d, f = lauf("probe_release_transport.js", ["%s:%s" % (fall, modus), str(basis)], basis)
            name = "transport %s:%s" % (fall, modus)
            if d is None:
                fehler.append("%s: %s" % (name, f)); continue
            soll = MINDEST.get(fall, 1) if modus.startswith("sperre") else 1
            if len(d["pruefungen"]) < soll:
                fehler.append("%s: nur %d Prüfungen (Soll ≥ %d)" % (name, len(d["pruefungen"]), soll))
            for p in d["pruefungen"]:
                n += 1
                print(("ok   " if p["ok"] else "FEHL ") + "[%s] %s %s" % (name, p["name"], p["detail"][:80]))
                if not p["ok"]:
                    fehler.append("%s: %s" % (name, p["name"]))
    for fall in SEITE:
        if not passt("seite %s" % fall):
            continue
        f_name, _, seite = fall.partition("@")
        d, f = lauf("probe_release_seite.js", [str(basis / "landing"), f_name] + ([seite] if seite else []), basis)
        name = "seite %s" % fall
        if d is None:
            fehler.append("%s: %s" % (name, f)); continue
        soll = MINDEST.get(f_name, 1) if ":kontrolle" not in fall else 1
        if len(d["pruefungen"]) < soll:
            fehler.append("%s: nur %d Prüfungen (Soll ≥ %d)" % (name, len(d["pruefungen"]), soll))
        for p in d["pruefungen"]:
            n += 1
            print(("ok   " if p["ok"] else "FEHL ") + "[%s] %s %s" % (name, p["name"], p["detail"][:80]))
            if not p["ok"]:
                fehler.append("%s: %s" % (name, p["name"]))
    # Echte Bibliotheken (ApexCharts 4.7.0, supabase-js 2.117.3): Normalbetrieb ohne/mit methode.js gleich (auch
    # wenn ApexCharts NACH methode.js lädt — Setter-Pfad), nach der Sperre keine Anfrage, render/Konstruktor lehnen ab.
    if passt("bibliotheken"):
        ergebnisse = {}
        for modus in ("ohne", "mit", "mit_spaet"):
            d, f = lauf("probe_release_bibliotheken.js", [str(basis / "landing"), modus], basis, kennung='{"modus"')
            if d is None:
                fehler.append("bibliotheken %s: %s" % (modus, f)); continue
            ergebnisse[modus] = d
        if len(ergebnisse) == 3:
            o = ergebnisse["ohne"]["normal"]
            pr = [
                ("Kontrolle: ohne methode.js liefert supabase Daten und ApexCharts ein SVG",
                 bool(o["supabase"]["data"]) and o["chart"]["svg"] > 0 and not o["chart"]["fehler"]),
                ("Normalbetrieb mit methode.js unverändert (danach geladen)", ergebnisse["mit"]["normal"] == o),
                ("Normalbetrieb mit methode.js unverändert (Bibliotheken danach — Setter-Pfad)", ergebnisse["mit_spaet"]["normal"] == o),
            ]
            for m in ("mit", "mit_spaet"):
                sp = ergebnisse[m]["sperre"]
                pr.append(("%s: nach Sperre keine Anfrage aus supabase-js, keine Daten" % m,
                           sp.get("supabaseAnfragen") == 0 and sp.get("supabaseDaten") is None and sp.get("nachSperre") == 0))
                pr.append(("%s: nach Sperre lehnen render und Konstruktor ab" % m,
                           sp.get("renderFehler") == "ReleaseFehler" and sp.get("neuFehler") == "ReleaseFehler"))
            for name, ok in pr:
                n += 1
                print(("ok   " if ok else "FEHL ") + "[bibliotheken] " + name)
                if not ok:
                    fehler.append("bibliotheken: " + name)
    for f in fehler:
        print("FEHL " + f)
    print("verify_release_sperre: %s (%d Prüfungen)" % ("BESTANDEN" if not fehler else "DURCHGEFALLEN", n))
    if not fehler:
        print("PROBE-ENDE %d Pruefungen" % n)
    return 0 if not fehler else 1


if __name__ == "__main__":
    sys.exit(main())
