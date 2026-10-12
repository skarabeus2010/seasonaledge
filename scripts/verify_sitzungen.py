#!/usr/bin/env python3
"""
Wächter: Sitzungshelfer (shared/sitzungen.py ↔ SA.boersenkalender, V1d; Entwurf
docs/review_prompts/2026-10-12_kalender_v1d_entwurf_v2.md, Codex-Freigabe).

  [Referenz]  unabhängige Sitzungsfolge je Börse aus numpy.busday_offset (Wochenmaske + get_holidays) — andere Logik
              als die Helfer; Python-Helfer == Referenz für JEDEN Tag 1885–2100 (naechste/vorherige × einschließlich/
              strikt), `verschiebe` mit n ∈ {±1, ±5, ±21, ±252, ±2520} auf jeder 7. Sitzung, Positionsfunktionen.
  [Rand]      Suchen und Verschiebungen über 1885-01-01 / 2100-12-31 hinaus → Fehler, nie ein Datum.
  [Sollfall]  handgeschrieben: TSE Golden Week 2019, NYSE 3. Juli 2026, XETRA Weihnachten 2026, Jahreswechsel,
              CRYPTO, FOREX; `heute` an Sommerzeitwechseln und Mitternacht in sechs Zonen; `zieltermin`;
              `sitzung_info` (Halbtag, belegt voll, ungeprüft → None, geschlossen).
  [Eingabe]   ungültige Eingaben → gewollter Fehler (Python TypeError/ValueError, JS KalenderFehler); ein Absturz
              oder ein Ergebnis gilt nicht.
  [Zwilling]  dieselben Raster und Fälle in node (echte landing/js/boersenkalender.js) unter UTC und
              Pacific/Kiritimati, `heute` zusätzlich unter America/Adak; JS == Python.

Aufruf:  py -3.14 scripts/verify_sitzungen.py      Exit 0 = alles erfüllt (braucht node + numpy)
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import date, datetime, timedelta, timezone

import numpy as np

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, WURZEL)

from shared import boersenereignisse as BE  # noqa: E402
from shared import sitzungen as S  # noqa: E402
from shared.exchange_holidays import get_holidays  # noqa: E402

PROBE = os.path.join(WURZEL, "scripts", "js", "probe_sitzungen.js")
UNTEN, OBEN = S.UNTEN, S.OBEN
BOERSEN = list(BE.BOERSEN)
NS = (1, 5, 21, 252, 2520, -1, -5, -21, -252, -2520)
FEHLER: list[str] = []
ZAEHLER = {"n": 0}


def pruefe(kennung, bedingung, text=""):
    ZAEHLER["n"] += 1
    if not bedingung:
        FEHLER.append("[%s] %s" % (kennung, text))


ABSTUERZE: list[str] = []   # unerwartete Ausnahmen — gelten nie als gewollter Fehler (Codex V1d R1)


def alle_tage():
    d, out = UNTEN, []
    while d <= OBEN:
        out.append(d)
        d += timedelta(days=1)
    return out


TAGE = alle_tage()
TAGE_NP = np.array([np.datetime64(d.isoformat()) for d in TAGE])


def referenz(b):
    """Offene Tage + die vier Suchen je Tag aus numpy (unabhängig von shared/sitzungen.py)."""
    maske = "1111111" if b == "CRYPTO" else "1111100"
    feiertage = np.array(sorted(np.datetime64(d.isoformat()) for d in get_holidays(b, UNTEN.year, OBEN.year)),
                         dtype="datetime64[D]")
    kal = np.busdaycalendar(weekmask=maske, holidays=feiertage)
    eins = np.timedelta64(1, "D")
    vor_e = np.busday_offset(TAGE_NP, 0, roll="forward", busdaycal=kal)
    vor_s = np.busday_offset(TAGE_NP + eins, 0, roll="forward", busdaycal=kal)
    rueck_e = np.busday_offset(TAGE_NP, 0, roll="backward", busdaycal=kal)
    rueck_s = np.busday_offset(TAGE_NP - eins, 0, roll="backward", busdaycal=kal)
    lo, hi = np.datetime64(UNTEN.isoformat()), np.datetime64(OBEN.isoformat())
    teile = []
    for i in range(len(TAGE)):
        z = []
        for arr in (vor_e, vor_s, rueck_e, rueck_s):
            r = arr[i]
            z.append("E" if (r < lo or r > hi) else str(int((r - TAGE_NP[i]).astype(int))))
        teile.append(",".join(z))
    offen_tage = [TAGE[i] for i in np.nonzero(np.is_busday(TAGE_NP, busdaycal=kal))[0]]
    return ";".join(teile), offen_tage


def py_abstand(f, basis):
    try:
        return str((f() - basis).days)
    except (ValueError, TypeError):
        return "E"
    except Exception as e:  # noqa: BLE001
        ABSTUERZE.append("Python: %r" % e)
        return "X"


def py_raster(b):
    teile = []
    for d in TAGE:
        teile.append(",".join([
            py_abstand(lambda: S.naechste(d, b, einschliesslich=True), d),
            py_abstand(lambda: S.naechste(d, b, einschliesslich=False), d),
            py_abstand(lambda: S.vorherige(d, b, einschliesslich=True), d),
            py_abstand(lambda: S.vorherige(d, b, einschliesslich=False), d)]))
    return ";".join(teile)


def verschiebe_auftrag(offen_tage):
    """Kleine Offsets auf jeder 7., ±252 auf jeder 49., ±2520 auf jeder 343. Sitzung (Laufzeit im Gate)."""
    out = []
    for i in range(0, len(offen_tage), 7):
        ns = [n for n in NS if abs(n) <= 21]
        if i % 49 == 0:
            ns += [252, -252]
        if i % 343 == 0:
            ns += [2520, -2520]
        out += [(offen_tage[i], n) for n in ns]
    return out


def verschiebe_ref(offen_tage, auftrag):
    idx = {d: i for i, d in enumerate(offen_tage)}
    out = []
    for d, n in auftrag:
        k = idx[d] + n
        out.append(str((offen_tage[k] - d).days) if 0 <= k < len(offen_tage) else "E")
    return ";".join(out)


def positionen_auftrag():
    out = []
    for j in range(UNTEN.year, OBEN.year + 1):
        for m in range(1, 13):
            for n in (1, 2, 10, 20, 23, 24):
                out.append(("m", j, m, n))
                out.append(("h", j, m, n))
        for n in (1, 100, 250, 262):
            out.append(("j", j, 1, n))
    return out


def positionen_ref(offen_tage, auftrag):
    je_monat, je_jahr = {}, {}
    for d in offen_tage:
        je_monat.setdefault((d.year, d.month), []).append(d)
        je_jahr.setdefault(d.year, []).append(d)
    out = []
    for art, j, m, n in auftrag:
        s = je_jahr.get(j, []) if art == "j" else je_monat.get((j, m), [])
        if n > len(s):
            out.append("N")
        else:
            out.append((s[-n] if art == "h" else s[n - 1]).isoformat())
    return ";".join(out)


def positionen_py(b, auftrag):
    out = []
    for art, j, m, n in auftrag:
        f = {"m": lambda: S.nte_im_monat(j, m, n, b), "h": lambda: S.nte_von_hinten_im_monat(j, m, n, b),
             "j": lambda: S.nte_im_jahr(j, n, b)}[art]
        try:
            r = f()
            out.append("N" if r is None else r.isoformat())
        except (ValueError, TypeError):
            out.append("E")
    return ";".join(out)


# ── Fälle: (Name, JS-Funktion, JS-Argumente, Python-Aufruf, Soll) — Soll "FEHLER" = gewollter Fehler ─────────────
def U(*a):
    return datetime(*a, tzinfo=timezone.utc)


def ms(t):
    return int(t.timestamp() * 1000)


FAELLE = [
    # Sollfälle Suche (Quellen: TSE-Kalender 2019, NYSE 2026, Xetra 2026)
    ("TSE Golden Week", "naechste", ["2019-04-27", "TSE", True], lambda: S.naechste("2019-04-27", "TSE", einschliesslich=True), "2019-05-07"),
    ("NYSE 2.7.→6.7. strikt", "naechste", ["2026-07-02", "NYSE", False], lambda: S.naechste("2026-07-02", "NYSE", einschliesslich=False), "2026-07-06"),
    ("NYSE 2.7. einschließlich", "naechste", ["2026-07-02", "NYSE", True], lambda: S.naechste("2026-07-02", "NYSE", einschliesslich=True), "2026-07-02"),
    ("XETRA Weihnachten", "naechste", ["2026-12-23", "XETRA", False], lambda: S.naechste("2026-12-23", "XETRA", einschliesslich=False), "2026-12-28"),
    ("NYSE Jahreswechsel", "naechste", ["2025-12-31", "NYSE", False], lambda: S.naechste("2025-12-31", "NYSE", einschliesslich=False), "2026-01-02"),
    ("CRYPTO Samstag", "naechste", ["2026-07-04", "CRYPTO", False], lambda: S.naechste("2026-07-04", "CRYPTO", einschliesslich=False), "2026-07-05"),
    ("FOREX Fr→Mo", "naechste", ["2026-07-03", "FOREX", False], lambda: S.naechste("2026-07-03", "FOREX", einschliesslich=False), "2026-07-06"),
    ("NYSE vorherige strikt", "vorherige", ["2026-07-06", "NYSE", False], lambda: S.vorherige("2026-07-06", "NYSE", einschliesslich=False), "2026-07-02"),
    ("Hülle naechsterHandelstag", "naechsterHandelstag", ["2026-07-02", "NYSE"], lambda: S.naechste("2026-07-02", "NYSE", einschliesslich=True), "2026-07-02"),
    ("Hülle nterHandelstag", "nterHandelstag", [2026, 7, 3, "NYSE"], lambda: S.nte_im_monat(2026, 7, 3, "NYSE"), "2026-07-06"),   # 1., 2., (3. zu), 6.
    ("NASDAQ = NYSE", "naechste", ["2026-07-03", "NASDAQ", True], lambda: S.naechste("2026-07-03", "NASDAQ", einschliesslich=True), "2026-07-06"),
    ("verschiebe Monatsgrenze", "verschiebe", ["2026-06-30", 3, "NYSE"], lambda: S.verschiebe("2026-06-30", 3, "NYSE"), "2026-07-06"),
    ("verschiebe Jahresgrenze rückwärts", "verschiebe", ["2026-01-02", -1, "NYSE"], lambda: S.verschiebe("2026-01-02", -1, "NYSE"), "2025-12-31"),
    ("sitzungen Juli-Anfang", "sitzungen", ["2026-07-01", "2026-07-07", "NYSE"], lambda: [d.isoformat() for d in S.sitzungen("NYSE", "2026-07-01", "2026-07-07")],
     ["2026-07-01", "2026-07-02", "2026-07-06", "2026-07-07"]),
    # Rand
    ("Rand oben strikt", "naechste", ["2100-12-31", "NYSE", False], lambda: S.naechste("2100-12-31", "NYSE", einschliesslich=False), "FEHLER"),
    ("Rand unten strikt", "vorherige", ["1885-01-01", "NYSE", False], lambda: S.vorherige("1885-01-01", "NYSE", einschliesslich=False), "FEHLER"),
    ("Rand unten einschließlich (Feiertag)", "vorherige", ["1885-01-01", "NYSE", True], lambda: S.vorherige("1885-01-01", "NYSE", einschliesslich=True), "FEHLER"),
    ("vor dem Rechenbereich", "naechste", ["1884-12-31", "NYSE", True], lambda: S.naechste("1884-12-31", "NYSE", einschliesslich=True), "FEHLER"),
    # Eingaben
    ("einschliesslich fehlt", "naechste", ["2026-07-02", "NYSE"], lambda: S.naechste("2026-07-02", "NYSE"), "FEHLER"),
    ("einschliesslich keine Boolean", "naechste", ["2026-07-02", "NYSE", 1], lambda: S.naechste("2026-07-02", "NYSE", einschliesslich=1), "FEHLER"),
    ("verschiebe n=0", "verschiebe", ["2026-07-02", 0, "NYSE"], lambda: S.verschiebe("2026-07-02", 0, "NYSE"), "FEHLER"),
    ("verschiebe n Boolean", "verschiebe", ["2026-07-02", True, "NYSE"], lambda: S.verschiebe("2026-07-02", True, "NYSE"), "FEHLER"),
    ("verschiebe n=1.5", "verschiebe", ["2026-07-02", 1.5, "NYSE"], lambda: S.verschiebe("2026-07-02", 1.5, "NYSE"), "FEHLER"),
    ("verschiebe ab geschlossenem Tag", "verschiebe", ["2026-07-03", 1, "NYSE"], lambda: S.verschiebe("2026-07-03", 1, "NYSE"), "FEHLER"),
    ("Position 0", "nteImMonat", [2026, 7, 0, "NYSE"], lambda: S.nte_im_monat(2026, 7, 0, "NYSE"), "FEHLER"),
    ("Monat 13", "nteImMonat", [2026, 13, 1, "NYSE"], lambda: S.nte_im_monat(2026, 13, 1, "NYSE"), "FEHLER"),
    ("von nach bis", "sitzungen", ["2026-07-07", "2026-07-01", "NYSE"], lambda: S.sitzungen("NYSE", "2026-07-07", "2026-07-01"), "FEHLER"),
    ("unbekannte Börse", "naechste", ["2026-07-02", "FOO", True], lambda: S.naechste("2026-07-02", "FOO", einschliesslich=True), "FEHLER"),
    # heute (Sommerzeit, Mitternacht, Zonen) — Soll handgerechnet
    ("NYSE vor DST-Beginn", "heute", ["NYSE", "2026-03-08T04:30:00Z"], lambda: S.heute("NYSE", U(2026, 3, 8, 4, 30)), "2026-03-07"),
    ("NYSE Mitternacht EST", "heute", ["NYSE", "2026-03-08T05:00:00Z"], lambda: S.heute("NYSE", U(2026, 3, 8, 5, 0)), "2026-03-08"),
    ("NYSE vor DST-Ende", "heute", ["NYSE", "2026-11-01T03:59:00Z"], lambda: S.heute("NYSE", U(2026, 11, 1, 3, 59)), "2026-10-31"),
    ("NYSE Mitternacht EDT", "heute", ["NYSE", "2026-11-01T04:00:00Z"], lambda: S.heute("NYSE", U(2026, 11, 1, 4, 0)), "2026-11-01"),
    ("XETRA nach Mitternacht CEST", "heute", ["XETRA", "2026-10-24T22:30:00Z"], lambda: S.heute("XETRA", U(2026, 10, 24, 22, 30)), "2026-10-25"),
    ("XETRA nach DST-Ende", "heute", ["XETRA", "2026-10-25T22:59:00Z"], lambda: S.heute("XETRA", U(2026, 10, 25, 22, 59)), "2026-10-25"),
    ("NYSE aus Berliner Zeit", "heute", ["NYSE", "2026-07-01T05:30:00+02:00"],
     lambda: S.heute("NYSE", datetime(2026, 7, 1, 3, 30, tzinfo=timezone.utc)), "2026-06-30"),
    ("TSE nach Mitternacht", "heute", ["TSE", "2026-07-01T15:30:00Z"], lambda: S.heute("TSE", U(2026, 7, 1, 15, 30)), "2026-07-02"),
    ("CRYPTO UTC", "heute", ["CRYPTO", "2026-07-01T23:59:00-05:00"], lambda: S.heute("CRYPTO", U(2026, 7, 2, 4, 59)), "2026-07-02"),
    ("FOREX UTC", "heute", ["FOREX", "2026-07-01T23:59:00-05:00"], lambda: S.heute("FOREX", U(2026, 7, 2, 4, 59)), "2026-07-02"),
    ("Epoch-ms", "heute", ["NYSE", ms(U(2026, 1, 1))], lambda: S.heute("NYSE", U(2026, 1, 1)), "2025-12-31"),
    ("heute ohne Zone", "heute", ["NYSE", "2026-07-01T10:00:00"], lambda: S.heute("NYSE", datetime(2026, 7, 1, 10, 0)), "FEHLER"),
    ("heute Text", "heute", ["NYSE", "gestern"], lambda: S.heute("NYSE", "gestern"), "FEHLER"),
    ("heute Boolean", "heute", ["NYSE", True], lambda: S.heute("NYSE", True), "FEHLER"),
    ("heute 30. Februar", "heute", ["NYSE", "2026-02-30T12:00:00Z"], lambda: S.heute("NYSE", "2026-02-30T12:00:00Z"), "FEHLER"),
    ("heute 24 Uhr", "heute", ["NYSE", "2026-07-01T24:00:00Z"], lambda: S.heute("NYSE", "2026-07-01T24:00:00Z"), "FEHLER"),
    ("heute Versatz 25 h", "heute", ["NYSE", "2026-07-01T12:00:00+25:00"], lambda: S.heute("NYSE", "2026-07-01T12:00:00+25:00"), "FEHLER"),
    ("heute Epoch außerhalb", "heute", ["NYSE", 8640000000000001], lambda: S.heute("NYSE", 8640000000000001), "FEHLER"),
    ("heute Epoch Bruchzahl", "heute", ["NYSE", 1.5], lambda: S.heute("NYSE", 1.5), "FEHLER"),
    # zieltermin (B5.3, B5.6)
    ("Ziel offen heute", "zieltermin", ["NYSE", "2026-07-02T14:00:00Z", "heutige_sitzung_oder_naechste"],
     lambda: S.zieltermin("NYSE", U(2026, 7, 2, 14), art="heutige_sitzung_oder_naechste"), "2026-07-02"),
    ("Ziel offen nächste", "zieltermin", ["NYSE", "2026-07-02T14:00:00Z", "naechste_nach_heute"],
     lambda: S.zieltermin("NYSE", U(2026, 7, 2, 14), art="naechste_nach_heute"), "2026-07-06"),
    ("Ziel geschlossen", "zieltermin", ["NYSE", "2026-07-03T14:00:00Z", "heutige_sitzung_oder_naechste"],
     lambda: S.zieltermin("NYSE", U(2026, 7, 3, 14), art="heutige_sitzung_oder_naechste"), "2026-07-06"),
    ("Ziel geschlossen nächste", "zieltermin", ["NYSE", "2026-07-03T14:00:00Z", "naechste_nach_heute"],
     lambda: S.zieltermin("NYSE", U(2026, 7, 3, 14), art="naechste_nach_heute"), "2026-07-06"),
    ("Ziel falsche Art", "zieltermin", ["NYSE", "2026-07-02T14:00:00Z", "morgen"],
     lambda: S.zieltermin("NYSE", U(2026, 7, 2, 14), art="morgen"), "FEHLER"),
    # sitzung_info
    ("Halbtag belegt", "sitzungInfo", ["2025-11-28", "NYSE"], lambda: S.sitzung_info("2025-11-28", "NYSE"),
     {"offen": True, "halbtag": True, "halbtag_status": "belegt", "schlusszeit": "13:00", "zeitzone": "America/New_York",
      "sitzung": "nyse_aktien_kernhandel"}),
    ("voller Tag belegt", "sitzungInfo", ["2025-11-26", "NYSE"], lambda: S.sitzung_info("2025-11-26", "NYSE"),
     {"offen": True, "halbtag": False, "halbtag_status": "belegt", "schlusszeit": None, "zeitzone": None, "sitzung": None}),
    ("Halbtag ungeprüft NYSE 2012", "sitzungInfo", ["2012-11-23", "NYSE"], lambda: S.sitzung_info("2012-11-23", "NYSE"),
     {"offen": True, "halbtag": None, "halbtag_status": "ungeprueft", "schlusszeit": None, "zeitzone": None, "sitzung": None}),
    ("XETRA ungeprüft", "sitzungInfo", ["2025-12-23", "XETRA"], lambda: S.sitzung_info("2025-12-23", "XETRA"),
     {"offen": True, "halbtag": None, "halbtag_status": "ungeprueft", "schlusszeit": None, "zeitzone": None, "sitzung": None}),
    ("geschlossen", "sitzungInfo", ["2025-12-25", "NYSE"], lambda: S.sitzung_info("2025-12-25", "NYSE"),
     {"offen": False, "halbtag": None, "halbtag_status": "belegt", "schlusszeit": None, "zeitzone": None, "sitzung": None}),
]


def py_fall(f):
    try:
        return {"ok": f()}
    except (ValueError, TypeError) as e:
        return {"fehler": "api", "text": str(e)}
    except Exception as e:  # noqa: BLE001
        ABSTUERZE.append("Python: %r" % e)
        return {"fehler": "absturz", "text": repr(e)}


def kern(r):
    """Vergleichswert eines Ergebnisses: Datum-Objekte → ISO, heute/zieltermin → Zieldatum."""
    if "fehler" in r:
        return "FEHLER" if r["fehler"] == "api" else "ABSTURZ"
    v = r["ok"]
    if isinstance(v, date):
        return v.isoformat()
    if isinstance(v, dict) and "datum" in v and "offen" not in v:
        return v["datum"]
    return v


def main() -> int:
    nur_python = "--ohne-node" in sys.argv
    auftrag = {"raster": {"boersen": BOERSEN, "tage": [d.isoformat() for d in TAGE]}, "verschiebe": {},
               "positionen": {}, "faelle": [{"f": f, "a": a} for _, f, a, _, _ in FAELLE]}
    pos = positionen_auftrag()
    soll, referenzfolge = {}, {}
    for b in BOERSEN:
        ref_raster, offen_tage = referenz(b)
        referenzfolge[b] = offen_tage
        vs = verschiebe_auftrag(offen_tage)
        soll[b] = (ref_raster, verschiebe_ref(offen_tage, vs), positionen_ref(offen_tage, pos))
        auftrag["verschiebe"][b] = [(d.isoformat(), n) for d, n in vs]
        auftrag["positionen"][b] = [list(p) for p in pos]
        ist = py_raster(b)
        pruefe("Referenz", ist == ref_raster, "%s: Suchen weichen ab (erste Stelle %s)" % (
            b, next((TAGE[i].isoformat() for i, (x, y) in enumerate(zip(ist.split(";"), ref_raster.split(";"))) if x != y), "?")))
        v_ist = ";".join(py_abstand(lambda d=d, n=n: S.verschiebe(d, n, b), d) for d, n in vs)
        pruefe("Referenz", v_ist == soll[b][1], "%s: verschiebe weicht ab" % b)
        pruefe("Referenz", positionen_py(b, pos) == soll[b][2], "%s: Positionsfunktionen weichen ab" % b)
        pruefe("Referenz", [d for d in S.sitzungen(b, UNTEN, OBEN)] == offen_tage, "%s: sitzungen ≠ Referenzfolge" % b)
    for name, _, _, f, s in FAELLE:
        k = kern(py_fall(f))
        pruefe("Sollfall", k == s, "Python %s: Ist %r, Soll %r" % (name, k, s))
    # Zielergebnis vollständig: Kalenderstatus und Referenzzeitpunkt
    z = S.zieltermin("NYSE", U(2026, 7, 2, 14), art="naechste_nach_heute")
    pruefe("Sollfall", z["kalenderstatus"] == "belegt" and z["referenzzeitpunkt"] == "2026-07-02T14:00:00.000Z"
           and z["heute"] == "2026-07-02" and z["zeitzone"] == "America/New_York", "zieltermin-Felder %r" % z)
    if nur_python:
        FEHLER.append("[Zwilling] UNGEPRÜFT (--ohne-node)")
    else:
        py_faelle = [py_fall(f) for _, _, _, f, _ in FAELLE]
        with tempfile.TemporaryDirectory() as td:
            pfad = os.path.join(td, "a.json")
            with open(pfad, "w", encoding="utf-8") as fh:
                json.dump(auftrag, fh)
            leicht = os.path.join(td, "b.json")
            with open(leicht, "w", encoding="utf-8") as fh:
                json.dump({"faelle": auftrag["faelle"]}, fh)
            laeufe = [(zone, subprocess.Popen(["node", "--max-old-space-size=4096", PROBE, zone, datei],
                                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                              encoding="utf-8"))
                      for zone, datei in (("UTC", pfad), ("Pacific/Kiritimati", pfad), ("America/Adak", leicht))]
            for zone, proc in laeufe:          # parallel gestartet, nacheinander ausgewertet
                aus, err = proc.communicate()
                r = subprocess.CompletedProcess(proc.args, proc.returncode, aus, err)
                if r.returncode != 0 or not r.stdout.rstrip().endswith("PROBE-ENDE"):
                    pruefe("Zwilling", False, "%s: Probe ohne Endmarker: %s" % (zone, r.stderr[-300:]))
                    continue
                ist = json.loads(r.stdout.rstrip()[: -len("PROBE-ENDE")])
                for b in (BOERSEN if ist["raster"] else []):
                    felder = re.split(r"[;,]", ";".join([ist["raster"][b], ist["verschiebe"][b], ist["positionen"][b]]))
                    if "X" in felder:   # je Tag vier Werte "a,b,c,d" — an ; UND , trennen (Codex V1d R2)
                        ABSTUERZE.append("JS %s %s: Absturz im Raster" % (zone, b))
                    pruefe("Zwilling", ist["sitzungen"][b] == ";".join(d.isoformat() for d in referenzfolge[b]),
                           "%s %s: JS-sitzungen(1885–2100) ≠ Referenzfolge" % (zone, b))
                    pruefe("Zwilling", ist["raster"][b] == soll[b][0], "%s %s: JS-Suchen ≠ Referenz" % (zone, b))
                    pruefe("Zwilling", ist["verschiebe"][b] == soll[b][1], "%s %s: JS-verschiebe ≠ Referenz" % (zone, b))
                    pruefe("Zwilling", ist["positionen"][b] == soll[b][2], "%s %s: JS-Positionen ≠ Referenz" % (zone, b))
                for (name, _, _, _, s), j, p in zip(FAELLE, ist["faelle"], py_faelle):
                    if j.get("fehler") == "absturz":
                        ABSTUERZE.append("JS %s %s: %s" % (zone, name, j.get("text")))
                    kj = kern(j)
                    pruefe("Zwilling", kj == s, "%s JS %s: Ist %r, Soll %r" % (zone, name, kj, s))
                    if "ok" in j and "ok" in p and isinstance(p["ok"], dict):
                        pruefe("Zwilling", j["ok"] == p["ok"], "%s %s: JS-Objekt ≠ Python %r / %r" % (zone, name, j["ok"], p["ok"]))
    for a in ABSTUERZE[:10]:
        FEHLER.append("[Absturz] %s" % a)
    for f in FEHLER:
        print("FEHL", f)
    print("verify_sitzungen: %d/%d Prüfungen bestanden (%d Börsen × %d Tage)" % (
        ZAEHLER["n"] - len(FEHLER), ZAEHLER["n"], len(BOERSEN), len(TAGE)))
    if not FEHLER:
        print("PROBE-ENDE %d Pruefungen" % ZAEHLER["n"])
    return 0 if not FEHLER else 1


if __name__ == "__main__":
    sys.exit(main())
