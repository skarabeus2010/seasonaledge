#!/usr/bin/env python3
"""
Wächter: US-Produkttermine OPEX und VIX (shared/produkttermine.py, V1c-2; Entwurf
docs/review_prompts/2026-10-12_kalender_v1c2_entwurf*.md, Codex-Freigabe v6).

  [Beleg]       jeder belegte Monat (Cboe-Dateien/Jahreskalender) == Regelergebnis — die Belege sind die unabhängige
                Seite; eine Abweichung heißt: Regel oder Kalenderannahme falsch.
  [Sollfall]    handgeschriebene Fälle mit Quelle (OCC/Cboe), festes Prüfdatum 2026-10-12.
  [Grenze]      Einstufung belegt/projektion/Lücke mit festem Prüfdatum: Datenstand alt, Gleichheitsfall, Zukunft.
  [Synthetisch] eingeschleuster Kalender: zusätzliche Donnerstags-/Mittwochsschließungen, Codex-Fall 17.04.2025.
  [Abhängigkeit] VX belegt, Optionen nicht → Futures gefüllt, Optionsfelder None mit Grund.
  [Pflicht]     pruefdatum ohne Standardwert (Python TypeError, JS KalenderFehler).
  [Zwilling]    landing/js/boersenkalender.js: vollständige Objektgleichheit OPEX/VIX/Abdeckung/Version für drei
                Prüfdaten unter zwei Zeitzonen.
  [Abdeckung]   Lücken je Belegreihe werden AUSGEGEBEN (nicht still grün); Datenstand > 200 Tage → Warnung.

Aufruf:  py -3.14 scripts/verify_produkttermine.py      Exit 0 = alles erfüllt (braucht node)
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from datetime import date

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, WURZEL)

from shared import produkttermine as P  # noqa: E402
from shared.produkttermine_listung import BELEGREIHEN  # noqa: E402

PRUEF = "2026-10-12"
PROBE = os.path.join(WURZEL, "scripts", "js", "probe_produkttermine.js")
ZONEN = {"UTC": [0, 0], "America/Adak": [600, 540]}
FEHLER: list[str] = []
ZAEHLER = {"n": 0}


def pruefe(kennung: str, bedingung: bool, text: str = "") -> None:
    ZAEHLER["n"] += 1
    if not bedingung:
        FEHLER.append(f"[{kennung}] {text}")


def opex(monat, pd=PRUEF, **kw):
    r = P.produkttermine(monat, monat, "opex", pruefdatum=pd, **kw)
    return r[0] if r else None


def vix(monat, pd=PRUEF, **kw):
    r = P.produkttermine(monat, monat, "vix", pruefdatum=pd, **kw)
    return r[0] if r else None


def belege_leer(datenstand="2025-06-30", vx=None):
    return {"SPX_STANDARD": {"datenstand": datenstand, "monate": {}},
            "VX": {"datenstand": datenstand, "monate": dict(vx or {})},
            "VIX_OPT": {"datenstand": datenstand, "monate": {}}}


def belegt_gleich_regel() -> None:
    abw = []
    for art, bis in (("opex", "2100-12"), ("vix", "2100-11")):
        for e in P.produkttermine("2015-01", bis, art, pruefdatum=PRUEF):
            if e["regel_abweichung"]:
                abw.append(e["ereignis_id"])
    n = sum(len(v["monate"]) for v in BELEGREIHEN.values())
    pruefe("Beleg", not abw, "Beleg ≠ Regel: %s" % abw[:8])
    pruefe("Beleg", n == 84 + 142 + 84, "Anzahl Belege %d" % n)


def sollfaelle() -> None:
    def feld(e, k, soll, kenn):
        pruefe("Sollfall", e is not None and e.get(k) == soll, "%s.%s: Ist %r, Soll %r" % (kenn, k, e and e.get(k), soll))
    # OCC: 3. Freitag, bei Feiertag vorangehender Geschäftstag
    feld(opex("2025-04"), "verfallstermin", "2025-04-17", "OPEX 2025-04 (Karfreitag)")
    feld(opex("2025-04"), "ersatzgrund", "feiertag", "OPEX 2025-04")
    feld(opex("2026-06"), "verfallstermin", "2026-06-18", "OPEX 2026-06 (Juneteenth)")
    feld(opex("2026-03"), "verfallstermin", "2026-03-20", "OPEX 2026-03")
    feld(opex("2026-03"), "triple_witching", True, "OPEX 2026-03")
    feld(opex("2022-04"), "verfallstermin", "2022-04-14", "OPEX 2022-04")
    feld(opex("2025-04"), "listung", "belegt", "OPEX 2025-04")
    pruefe("Sollfall", opex("2015-01") is None, "OPEX 2015-01 vor dem Regelbereich")
    pruefe("Sollfall", P.opex_regel(2015, 2)["verfallstermin"] == date(2015, 2, 20), "OPEX-Regel 2015-02 → 20.02.2015")
    pruefe("Sollfall", opex("2015-02") is None, "OPEX 2015-02 unbelegt und vergangen → Lücke, kein Ereignis")
    feld(opex("2027-01"), "listung", "projektion", "OPEX 2027-01")
    feld(opex("2027-01"), "verfallstermin", "2027-01-15", "OPEX 2027-01")
    # Cboe/CFE: VIX
    pruefe("Sollfall", vix("2015-08") is None, "VIX 2015-08 vor dem Regelbereich")
    e = vix("2015-09")
    feld(e, "settlement", "2015-09-16", "VIX 2015-09")
    feld(e, "handelsende_futures", "2015-09-16", "VIX 2015-09")
    feld(e, "verfall_optionen", None, "VIX 2015-09 (Optionen unbelegt)")
    feld(e, "grund_optionen", "nicht_belegt", "VIX 2015-09")
    feld(vix("2025-03"), "settlement", "2025-03-18", "VIX 2025-03 (Karfreitag-Referenz)")
    feld(vix("2025-03"), "handelsende_optionen", "2025-03-17", "VIX 2025-03")
    feld(vix("2024-06"), "settlement", "2024-06-18", "VIX 2024-06 (Juneteenth-Mittwoch)")
    feld(vix("2026-04"), "settlement", "2026-04-15", "VIX 2026-04 Normalfall")
    feld(vix("2026-04"), "ersatzgrund", "keiner", "VIX 2026-04")
    feld(vix("2026-05"), "settlement", "2026-05-19", "VIX 2026-05 (Referenz Juneteenth)")
    e = vix("2027-01")
    feld(e, "listung_futures", "belegt", "VIX 2027-01")
    feld(e, "listung_optionen", "projektion", "VIX 2027-01")
    e = vix("2027-07")
    feld(e, "listung_futures", "projektion", "VIX 2027-07")


def herkunft_und_version() -> None:
    e, v = opex("2025-04"), vix("2015-09")
    pruefe("Herkunft", e["quelle"] == "SPX_STANDARD" and opex("2027-01")["quelle"] == "regel", "OPEX-Quelle")
    pruefe("Herkunft", v["quelle_futures"] == "VX" and v["quelle_optionen"] is None, "VIX 2015-09 Quellen je Feldgruppe")
    w = vix("2027-07")
    pruefe("Herkunft", w["quelle_futures"] == "regel" and w["quelle_optionen"] == "regel", "VIX 2027-07 Projektion")
    for x in (e, v, w):
        pruefe("Herkunft", x.get("kalenderannahme") == "cboe_rth_gleich_nyse" and x.get("kalenderstatus") == "annahme",
               "%s: Kalenderannahme/-status fehlt" % x["ereignis_id"])
    # jede Produktregel steckt in der Version (Codex V1c-2 R1)
    basis = P.produktversion()
    for name, wert in (("TRIPLE_MONATE", (1, 4, 7, 10)), ("KALENDERSTATUS", "belegt"), ("VIX_BIS", (2100, 10)),
                       ("REGELSTAND_OPEX", "x")):
        alt = getattr(P, name)
        setattr(P, name, wert)
        P.produktversion.cache_clear()
        try:
            pruefe("Version", P.produktversion() != basis, "%s geändert, produktversion gleich" % name)
        finally:
            setattr(P, name, alt)
            P.produktversion.cache_clear()
    pruefe("Version", P.produktversion() == basis, "Version nach den Tests nicht wiederhergestellt")


def grenzen() -> None:
    b = belege_leer("2025-06-30")
    pruefe("Grenze", opex("2025-09", belege=b) is None, "unbelegt 2025-09 bei Datenstand 2025-06 → Lücke")
    e = opex("2026-10", belege=b)
    pruefe("Grenze", e is not None and e["listung"] == "projektion", "2026-10 (16.10. > Prüfdatum) → Projektion")
    pruefe("Grenze", opex("2026-10", pd="2026-10-16", belege=b) is None, "Regeltermin = Prüfdatum → Lücke")
    e = opex("2026-10", pd="2026-10-15", belege=b)
    pruefe("Grenze", e is not None and e["listung"] == "projektion", "Prüfdatum einen Tag vor Regeltermin → Projektion")
    e = opex("2027-01", belege=b)
    pruefe("Grenze", e is not None and e["listung"] == "projektion", "2027-01 → Projektion")
    ab = P.abdeckung(pruefdatum=PRUEF, belege=b)
    pruefe("Grenze", "2025-09" in ab["luecken"]["SPX_STANDARD"] and "2026-10" not in ab["luecken"]["SPX_STANDARD"],
           "abdeckung meldet 2025-09, nicht 2026-10")


def synthetisch() -> None:
    from shared.exchange_holidays import is_trading_day

    def zu(*tage):
        extra = {date.fromisoformat(t) for t in tage}
        return lambda d: d not in extra and is_trading_day(d, "NYSE")
    b = belege_leer("2000-01-01")
    e = opex("2025-04", pd="2000-01-01", offen=zu("2025-04-17"), belege=b)
    pruefe("Synthetisch", e and e["verfallstermin"] == "2025-04-16", "Do zusätzlich zu → Mittwoch: %r" % (e and e["verfallstermin"]))
    e = vix("2025-03", pd="2000-01-01", offen=zu("2025-04-17"), belege=b)
    pruefe("Synthetisch", e and e["settlement"] == "2025-03-18", "Codex-Fall 17.04.2025 zu → 18.03.2025: %r" % (e and e["settlement"]))
    e = vix("2025-03", pd="2000-01-01", offen=zu("2025-03-19"), belege=b)
    pruefe("Synthetisch", e and e["settlement"] == "2025-03-18", "Mi und Fr zu → einmal vor dem Mittwoch: %r" % (e and e["settlement"]))
    e = vix("2025-03", pd="2000-01-01", offen=zu("2025-03-19", "2025-03-18"), belege=b)
    pruefe("Synthetisch", e and e["settlement"] == "2025-03-17", "Mi, Di, Fr zu → Montag: %r" % (e and e["settlement"]))
    e = vix("2026-04", pd="2000-01-01", offen=zu("2026-04-15"), belege=b)
    pruefe("Synthetisch", e and e["settlement"] == "2026-04-14" and e["ersatzgrund"] == "feiertag",
           "nur Mi zu → Dienstag: %r" % (e and e["settlement"]))
    e = vix("2026-04", pd="2000-01-01", offen=zu("2026-04-14"), belege=b)
    pruefe("Synthetisch", e and e["settlement"] == "2026-04-15" and e["handelsende_optionen"] == "2026-04-13",
           "Di zu: Settlement bleibt, Optionshandel endet Montag: %r" % (e and e["handelsende_optionen"]))


def abhaengigkeit() -> None:
    b = belege_leer("2026-10-12", vx={"2025-03": "2025-03-18"})
    e = vix("2025-03", belege=b)
    pruefe("Abhängigkeit", e and e["settlement"] == "2025-03-18" and e["listung_futures"] == "belegt",
           "Futures gefüllt")
    pruefe("Abhängigkeit", e and e["verfall_optionen"] is None and e["handelsende_optionen"] is None
           and e["grund_optionen"] == "nicht_belegt", "Optionsfelder None mit Grund (auch das abgeleitete Handelsende)")


def pflicht() -> None:
    for name, f in (("produkttermine", lambda: P.produkttermine("2025-01", "2025-02", "opex")),
                    ("abdeckung", lambda: P.abdeckung())):
        try:
            f()
            pruefe("Pflicht", False, "%s ohne pruefdatum lief durch" % name)
        except TypeError:
            pruefe("Pflicht", True)
    for name, f in (("Art", lambda: P.produkttermine("2025-01", "2025-02", "foo", pruefdatum=PRUEF)),
                    ("VIX 2100-12", lambda: P.produkttermine("2100-12", "2100-12", "vix", pruefdatum=PRUEF))):
        try:
            f()
            pruefe("Pflicht", False, "%s ohne Fehler" % name)
        except ValueError:
            pruefe("Pflicht", True)


def zwilling() -> None:
    from scripts.build_boersenkalender_js import ZIEL, erzeugen
    with open(ZIEL, "rb") as fh:
        pruefe("Zwilling", fh.read() == erzeugen(), "landing/js/boersenkalender.js nicht aktuell")
    # 2027-01-15 = OPEX-Regeltermin ohne Beleg: der Gleichheitsfall muss auch im JS-Vergleich vorkommen
    pruefdaten = [PRUEF, "2020-06-15", "2027-01-15", "2031-01-01"]
    soll = {p: {"opex": P.produkttermine("2015-01", "2100-12", "opex", pruefdatum=p),
                "vix": P.produkttermine("2015-01", "2100-11", "vix", pruefdatum=p),
                "abdeckung": P.abdeckung(pruefdatum=p)} for p in pruefdaten}
    with tempfile.TemporaryDirectory() as td:
        auftrag = os.path.join(td, "a.json")
        with open(auftrag, "w", encoding="utf-8") as fh:
            json.dump({"pruefdaten": pruefdaten}, fh)
        for zone, offs in ZONEN.items():
            r = subprocess.run(["node", PROBE, zone, auftrag], capture_output=True, text=True, encoding="utf-8")
            if r.returncode != 0 or not r.stdout.rstrip().endswith("PROBE-ENDE"):
                pruefe("Zwilling", False, "%s: Probe ohne Endmarker: %s" % (zone, r.stderr[-300:]))
                continue
            ist = json.loads(r.stdout.rstrip()[: -len("PROBE-ENDE")])
            pruefe("Zwilling", ist["offsets"] == offs, "%s: Zone wirkt nicht" % zone)
            pruefe("Zwilling", ist["produktversion"] == P.produktversion(), "%s: produktversion" % zone)
            pruefe("Zwilling", ist["eingefroren"] is True, "%s: Objekte veränderlich" % zone)
            for k, v in ist["fehler"].items():
                pruefe("Pflicht", v == "api", "%s JS %s: %s statt KalenderFehler" % (zone, k, v))
            for p in pruefdaten:
                for teil in ("opex", "vix", "abdeckung"):
                    a, s = ist["je"][p][teil], soll[p][teil]
                    if a != s and isinstance(a, list):
                        i = next((i for i, (x, y) in enumerate(zip(a, s)) if x != y), min(len(a), len(s)))
                        pruefe("Zwilling", False, "%s %s %s #%d: JS %.200r ≠ Py %.200r" % (
                            zone, p, teil, i, a[i] if i < len(a) else None, s[i] if i < len(s) else None))
                    else:
                        pruefe("Zwilling", a == s, "%s %s %s ungleich" % (zone, p, teil))


def main() -> int:
    belegt_gleich_regel()
    sollfaelle()
    herkunft_und_version()
    grenzen()
    synthetisch()
    abhaengigkeit()
    pflicht()
    if "--ohne-node" not in sys.argv:
        zwilling()
    else:
        FEHLER.append("[Zwilling] UNGEPRÜFT (--ohne-node)")
    ab = P.abdeckung(pruefdatum=PRUEF)
    for reihe, l in ab["luecken"].items():
        if l:
            print("ABDECKUNGSLÜCKE %s: %d Monate %s–%s ohne Beleg (keine Ereignisse/Felder)" % (reihe, len(l), l[0], l[-1]))
    print("NICHT MODELLIERT: OPEX vor %s, VIX vor %s (frühe Regelgrenzen nicht belegbar)" % (
        ab["nicht_modelliert"]["opex_vor"], ab["nicht_modelliert"]["vix_vor"]))
    for reihe, ds in ab["datenstand"].items():
        alter = (date.fromisoformat(PRUEF) - date.fromisoformat(ds)).days
        if alter > 200:
            print("WARNUNG Datenstand %s ist %d Tage alt" % (reihe, alter))
    for f in FEHLER:
        print("FEHL", f)
    print("verify_produkttermine: %d/%d Prüfungen bestanden" % (ZAEHLER["n"] - len(FEHLER), ZAEHLER["n"]))
    if not FEHLER:
        print("PROBE-ENDE %d Pruefungen" % ZAEHLER["n"])
    return 0 if not FEHLER else 1


if __name__ == "__main__":
    sys.exit(main())
