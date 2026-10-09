#!/usr/bin/env python3
"""
verify_stress_ampel.py — Wächter der Stress-Ampel (Plan docs/review_prompts/2026-10-09_stress_ampel_plan.md, v5).

    py -3.14 scripts/verify_stress_ampel.py --snapshot <ordner>     # alle Prüfungen inkl. Kurs-Snapshot
    py -3.14 scripts/verify_stress_ampel.py --ohne-snapshot          # ausdrücklich ohne Snapshot-Teil
    py -3.14 scripts/verify_stress_ampel.py --mutationen

Teile:
  1. Rechnung: Python (`shared/stress_score.py`) und JS (`landing/js/dash-compute.js`, echte Datei in node) gegen eine
     DRITTE, absichtlich naive Referenz (statistics.stdev, Rang per Schleife) — Zwillingsgleichheit allein beweist nichts.
     Fälle: Zufallsreihe mit Gleichständen, 776/777 Kurse, Fenster 2520, ungültige Kurse, konstante und monoton fallende
     Reihe, Präfixinvarianz, aktuell = letzte Zeile, Grenz- und Anzeigeregel (auch nach float32), Anzeige-Regel DB/Browser.
  2. Datenbankablauf (`vollauf`, `lade_kurse`, `aufraeumen`) gegen einen Fake mit denselben Regeln wie die SQL-Funktionen:
     Erfolg, Batchfehler, Rücklesefehler, belegte Sperre, abgelaufene Lease, verlorene Antwort nach Veröffentlichung,
     Aufräumen, unvollständige Eingabe, kurze Reihen; Wochenreport-Status.
  3. Statisch: keine Inline-Rechnung mehr, Seiten nutzen dash-compute, Grenzen 70/90, keine IF-Reste im Schreibweg,
     verbotene Begriffe nicht im Text, SQL-Regeln (Unique-Index, Lease, Abbrechen nur aus `laeuft`).
  4. Snapshot (nur mit --snapshot): Python = JS jeden Tag auf allen Tickern; SPY/^GSPC: 15.10.2008, 16.03.2020,
     08.04.2025 ≥ 90, 14.07.2017 < 70.
Ohne Snapshot und ohne --ohne-snapshot: UNGEPRÜFT (Exit 1).
--mutationen: jede Mutation benennt die Prüfung, die reißen MUSS; [Aufbau]-Risse oder Probeabbruch = UNGÜLTIG.
"""
from __future__ import annotations

import importlib.util
import json
import math
import pathlib
import random
import re
import shutil
import statistics
import struct
import subprocess
import sys
import tempfile
import uuid
from datetime import date, datetime, timedelta, timezone

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
PROBE = REPO / "scripts" / "js" / "probe_stress_ampel.js"
PY = "shared/stress_score.py"
JS = "landing/js/dash-compute.js"
CRASH = "landing/pages/crash-fruehwarnung.html"
DASH = "landing/pages/dashboard.html"
WL = "landing/pages/watchlist.html"
SQL = "scripts/sql/stress_scores_schema_2026_10.sql"
CRS = "scripts/compute_regime_scores.py"
NIGHT = "scripts/nightly_refresh.py"
HEALTH = "scripts/daily_health_check.py"
WEEK_T = "scripts/templates/weekly_report.html.j2"
EPS = 1e-9


def lade_modul(pfad, name):
    spec = importlib.util.spec_from_file_location(name, pfad)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ── unabhängige Referenz ───────────────────────────────────────────────────────
def naiv(daten, closes):
    """Bewusst andere Bauart: statistics.stdev, Rang per voller Schleife über die Vorgänger."""
    paare = sorted({d: c for d, c in zip(daten, closes) if isinstance(c, (int, float)) and math.isfinite(c) and c > 0}.items())
    c = [p[1] for p in paare]
    r = [None] + [(c[i] / c[i - 1] - 1) * 100 for i in range(1, len(c))]
    s = []
    for i in range(len(c)):
        if i < 20:
            s.append(None)
            continue
        v5 = statistics.stdev(r[i - 4:i + 1])
        v20 = statistics.stdev(r[i - 19:i + 1])
        dd = (c[i] / max(c[i - 19:i + 1]) - 1) * 100
        s.append(0.3 * v5 + 0.3 * v20 + 0.4 * abs(dd))
    out = []
    for i in range(len(c)):
        if s[i] is None:
            out.append((paare[i][0], None, None))
            continue
        ref = [x for x in s[max(0, i - 2520):i] if x is not None]
        if len(ref) < 756:
            out.append((paare[i][0], None, s[i]))
            continue
        kl = sum(1 for x in ref if x < s[i] - EPS)
        gl = sum(1 for x in ref if abs(x - s[i]) <= EPS)
        out.append((paare[i][0], 100.0 * (kl + 0.5 * gl) / len(ref), s[i]))
    return out


def tage(n, start="2000-01-03"):
    d, out = date.fromisoformat(start), []
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def zufall(n, seed, gleich=True):
    rnd = random.Random(seed)
    c, x = [], 100.0
    for i in range(n):
        if gleich and 300 <= i < 360:
            pass                            # konstanter Abschnitt → viele Gleichstände bei S
        else:
            x *= 1 + rnd.gauss(0.0003, 0.012 if i % 700 < 600 else 0.035)
        c.append(round(x, 4))
    return c


# ── Fake-Datenbank mit den Regeln der SQL-Funktionen ───────────────────────────
class Antwort:
    def __init__(self, data=None, count=None):
        self.data, self.count = data, count


class Abfrage:
    def __init__(self, db, tab):
        self.db, self.tab, self.filter, self.op, self.payload = db, tab, [], "select", None
        self.ordnung, self.desc, self.rng, self.lim, self.mit_count = None, False, None, None, False

    def select(self, *_a, count=None):
        self.mit_count = count == "exact"
        return self

    def eq(self, k, v):
        self.filter.append((k, v))
        return self

    def neq(self, k, v):
        self.filter.append((k, ("≠", v)))
        return self

    def order(self, k, desc=False):
        self.ordnung, self.desc = k, desc
        return self

    def range(self, a, b):
        self.rng = (a, b)
        return self

    def limit(self, n):
        self.lim = n
        return self

    def insert(self, zeilen):
        self.op, self.payload = "insert", zeilen
        return self

    def delete(self):
        self.op = "delete"
        return self

    def execute(self):
        return self.db.ausfuehren(self)


class FakeDB:
    def __init__(self, kurse):
        self.t = {"prices": [dict(z) for z in kurse], "stress_laeufe": [], "stress_scores": []}
        self.inserts = 0
        self.fehler_insert_nach = None      # Batchfehler nach k erfolgreichen Inserts
        self.fehler_lesen = False           # Netzwerkfehler beim Lesen von prices
        self.zaehlung_falsch = False
        self.rueck_verfaelschen = False
        self.lease_ablaufen = False         # Lease läuft vor der Veröffentlichung ab
        self.antwort_verloren = False       # Veröffentlichung gelingt, Antwort geht verloren
        self.jetzt = datetime(2026, 10, 9, 12, 0, tzinfo=timezone.utc)
        self.rpc_log = []
        self.ereignisse = []

    def table(self, name):
        return Abfrage(self, name)

    def rpc(self, name, params):
        db = self

        class R:
            def execute(self_):
                return Antwort(db.rpc_ausfuehren(name, params))
        return R()

    def rpc_ausfuehren(self, name, p):
        self.rpc_log.append(name)
        self.ereignisse.append(("rpc", name))
        L = self.t["stress_laeufe"]
        if name == "stress_lauf_starten":
            for l in L:
                if l["ticker"] == p["p_ticker"] and l["status"] == "laeuft" and l["laeuft_bis"] < self.jetzt:
                    l["status"] = "abgebrochen"
            if any(l["ticker"] == p["p_ticker"] and l["status"] == "laeuft" for l in L):
                return None
            lid = str(uuid.uuid4())
            L.append({"lauf_id": lid, "ticker": p["p_ticker"], "status": "laeuft", "laeuft_bis": self.jetzt + timedelta(minutes=30),
                      "fertig_am": None, "letztes_datum": None, "kurse_bis": None, "n_scores": None})
            return lid
        if name == "stress_lauf_veroeffentlichen":
            if self.lease_ablaufen:
                self.jetzt += timedelta(minutes=31)
            for l in L:
                if l["lauf_id"] == p["p_lauf"] and l["status"] == "laeuft" and l["laeuft_bis"] > self.jetzt:
                    self.jetzt += timedelta(seconds=1)
                    l.update(status="fertig", fertig_am=self.jetzt.isoformat(), n_scores=p["p_n"], letztes_datum=p["p_letztes"],
                             kurse_bis=p["p_kurse_bis"])
                    if self.antwort_verloren:
                        raise ConnectionError("Antwort verloren")
                    return True
            return False
        if name == "stress_lauf_abbrechen":
            for l in L:
                if l["lauf_id"] == p["p_lauf"] and l["status"] == "laeuft":
                    l["status"] = "abgebrochen"
                    return True
            return False
        raise KeyError(name)

    def ausfuehren(self, q):
        rows = self.t[q.tab]
        if q.op == "insert":
            if self.fehler_insert_nach is not None and self.inserts >= self.fehler_insert_nach:
                raise ConnectionError("Batch fehlgeschlagen")
            self.inserts += 1
            rows.extend(dict(z) for z in q.payload)
            return Antwort([])
        def passt(r):
            for k, v in q.filter:
                if isinstance(v, tuple) and v[:1] == ("≠",):
                    if r.get(k) == v[1]:
                        return False
                elif r.get(k) != v:
                    return False
            return True
        treffer = [r for r in rows if passt(r)]
        self.ereignisse.append((q.tab, q.op))
        if q.op == "delete":
            self.t[q.tab] = [r for r in rows if r not in treffer]
            return Antwort(treffer)
        if q.tab == "prices" and self.fehler_lesen:
            raise ConnectionError("Netzwerk")
        if q.ordnung:
            treffer = sorted(treffer, key=lambda r: r.get(q.ordnung) or "", reverse=q.desc)
        n = len(treffer)
        if q.mit_count and self.zaehlung_falsch:
            n += 5
        if q.rng:
            treffer = treffer[q.rng[0]:q.rng[1] + 1]
        if q.lim is not None:
            treffer = treffer[:q.lim]
        if q.rng is None and q.lim is None:
            treffer = treffer[:1000]               # PostgREST liefert ohne Range höchstens 1000 Zeilen
        if q.tab == "stress_scores":
            # wie PostgREST/PostgreSQL: double precision kommt nur auf 15 signifikante Stellen zurück
            treffer = [{k: (float(f"{v:.15g}") if isinstance(v, float) else v) for k, v in r.items()} for r in treffer]
        if q.tab == "stress_scores" and self.rueck_verfaelschen and treffer:
            treffer = [dict(r) for r in treffer]
            treffer[-1]["score"] = (treffer[-1]["score"] or 0) + 1e-6
        return Antwort([dict(r) for r in treffer], n if q.mit_count else None)


def kurse_zeilen(ticker, daten, closes):
    return [{"ticker": ticker, "date": d, "close": c} for d, c in zip(daten, closes)]


# ── JS ─────────────────────────────────────────────────────────────────────────
def js_lauf(basis, eingabe):
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(eingabe, f)
        pfad = f.name
    r = subprocess.run(["node", str(PROBE), str(basis), pfad], capture_output=True, text=True, encoding="utf-8")
    pathlib.Path(pfad).unlink(missing_ok=True)
    zeilen = r.stdout.strip().splitlines()
    if r.returncode != 0 or len(zeilen) < 2 or zeilen[-1] != "ENDE":
        raise RuntimeError("Probe ohne Endmarker: " + (r.stderr or r.stdout)[-300:])
    return json.loads(zeilen[0])


def gleich(a, b, tol=1e-9):
    if a is None or b is None:
        return a is None and b is None
    return abs(a - b) <= tol


def pruefe_alles(basis=REPO, snap=None):
    ss = lade_modul(basis / PY, "stress_pruef")
    P = {}

    def pruefe(name, fn):
        try:
            r = fn()
            P[name] = True if r is True else str(r)
        except Exception as e:  # noqa: BLE001
            P[name] = f"Ausnahme: {type(e).__name__}: {e}"

    # Eingaben
    D3 = tage(3200)
    C3 = zufall(3200, 7)
    faelle = {
        "zufall": [{"date": d, "close": c} for d, c in zip(D3, C3)],
        "k776": [{"date": d, "close": c} for d, c in zip(D3[:776], C3[:776])],
        "k777": [{"date": d, "close": c} for d, c in zip(D3[:777], C3[:777])],
        "konstant": [{"date": d, "close": 100.0} for d in D3[:900]],
        "fallend": [{"date": d, "close": 100.0 * 0.999 ** i} for i, d in enumerate(D3[:900])],
        "ungueltig": [{"date": d, "close": (0 if i == 500 else (None if i == 800 else ("NaN" if i == 1200 else c)))}
                      for i, (d, c) in enumerate(zip(D3[:1500], C3[:1500]))],
        "ohne_ungueltig": [{"date": d, "close": c} for i, (d, c) in enumerate(zip(D3[:1500], C3[:1500])) if i not in (500, 800, 1200)],
        "praefix": [{"date": d, "close": c} for d, c in zip(D3[:2000], C3[:2000])],
    }
    # Anzeige-Regel DB/Browser
    reihe_py = ss.stress_reihe(D3, C3)
    db_voll = [{"date": z["date"], "score": z["score"], "ampel": z["ampel"], "s": z["s"]} for z in reihe_py[-300:]]
    db_luecke = [z for z in db_voll if z["date"] != reihe_py[-100]["date"]]
    db_alt = db_voll[:-1]
    anzeige = [{"name": "voll", "reihe": "zufall", "db": db_voll, "n": 252},
               {"name": "luecke", "reihe": "zufall", "db": db_luecke, "n": 252},
               {"name": "alt", "reihe": "zufall", "db": db_alt, "n": 252},
               {"name": "leer", "reihe": "zufall", "db": [], "n": 252}]
    j = js_lauf(basis, {"faelle": faelle, "anzeige": anzeige})
    P["[Aufbau] probe"] = True if j.get("reihen") else "Probe leer"

    def py_reihe(name):
        return ss.stress_reihe([z["date"] for z in faelle[name]], [z["close"] for z in faelle[name]])

    def gegen_naiv():
        ref = naiv(D3, C3)
        py = reihe_py
        js = j["reihen"]["zufall"]
        if len(ref) != len(py) or len(py) != len(js):
            return f"Längen {len(ref)}/{len(py)}/{len(js)}"
        for (d, sc, s), zp, zj in zip(ref, py, js):
            if not (gleich(sc, zp["score"]) and gleich(sc, zj[1])):
                return f"{d}: Referenz {sc}, Python {zp['score']}, JS {zj[1]}"
            if not (gleich(s, zp["s"]) and gleich(s, zj[2])):
                return f"{d}: S Referenz {s}, Python {zp['s']}, JS {zj[2]}"
        if not any(zp["score"] is not None and abs(zp["score"] - round(zp["score"])) > 0 and
                   (zp["score"] * 2 * zp["referenz_n"] / 100) % 2 == 1 for zp in py):
            pass
        return True
    pruefe("rechnung_gegen_naiv", gegen_naiv)

    def gleichstand():
        r = py_reihe("konstant")
        z = r[-1]
        js = j["reihen"]["konstant"][-1]
        return True if (z["score"] == 50.0 and js[1] == 50.0 and z["s"] == 0.0) else f"konstant: Python {z['score']}, JS {js[1]}, S {z['s']}"
    pruefe("gleichstand_halb", gleichstand)

    def fallend():
        z = py_reihe("fallend")[-1]
        js = j["reihen"]["fallend"][-1]
        if not (abs(z["vol5"]) < 1e-9 and abs(z["vol20"]) < 1e-9):
            return f"Vol nicht 0: {z['vol5']}, {z['vol20']}"
        return True if gleich(z["s"], 0.4 * abs(z["dd20"])) and gleich(z["s"], js[2]) else f"S {z['s']} ≠ 0,4·|dd20|"
    pruefe("fallend_nur_drawdown", fallend)

    def grenze_777():
        a = py_reihe("k776")[-1]["score"]
        b = py_reihe("k777")[-1]
        ja, jb = j["aktuell"]["k776"], j["aktuell"]["k777"]
        if a is not None or ja["score"] is not None or ja["status"] != "zu_kurz":
            return f"776 Kurse: Python {a}, JS {ja}"
        if b["score"] is None or b["referenz_n"] != 756 or jb["score"] is None:
            return f"777 Kurse: Python {b['score']} (ref {b['referenz_n']}), JS {jb['score']}"
        return True
    pruefe("grenze_777", grenze_777)

    def fenster():
        z = reihe_py[2700]
        if z["referenz_n"] != 2520:
            return f"Referenz {z['referenz_n']} statt 2520"
        # unabhängig: Rang gegen S[180..2699] (2520 Werte)
        s = [x["s"] for x in reihe_py]
        ref = s[2700 - 2520:2700]
        kl = sum(1 for x in ref if x < s[2700] - EPS)
        gl = sum(1 for x in ref if abs(x - s[2700]) <= EPS)
        soll = 100 * (kl + 0.5 * gl) / 2520
        return True if gleich(z["score"], soll) and gleich(j["reihen"]["zufall"][2700][1], soll) else f"{z['score']} ≠ {soll}"
    pruefe("fenster_2520", fenster)

    def ungueltig():
        a = {z["date"]: z for z in py_reihe("ungueltig")}
        b = {z["date"]: z for z in py_reihe("ohne_ungueltig")}
        if set(a) != set(b):
            return f"Datumsmenge {len(a)} ≠ {len(b)} — ungültige Kurse nicht entfernt"
        ja = {z[0]: z for z in j["reihen"]["ungueltig"]}
        for d in b:
            if not (gleich(a[d]["score"], b[d]["score"]) and gleich(ja[d][1], b[d]["score"])):
                return f"{d}: mit ungültigen Kursen {a[d]['score']} / JS {ja[d][1]} ≠ {b[d]['score']}"
        return True
    pruefe("ungueltige_kurse", ungueltig)

    def praefix():
        kurz = {z["date"]: z["score"] for z in py_reihe("praefix")}
        lang = {z["date"]: z["score"] for z in reihe_py}
        jk = {z[0]: z[1] for z in j["reihen"]["praefix"]}
        falsch = [d for d in kurz if not (gleich(kurz[d], lang[d]) and gleich(jk[d], lang[d]))]
        return True if not falsch else f"Präfix verändert: {falsch[:3]}"
    pruefe("praefixinvarianz", praefix)

    def aktuell():
        a = ss.stress_aktuell(D3, C3)
        ja = j["aktuell"]["zufall"]
        return True if (a["score"] == reihe_py[-1]["score"] and ja["score"] == j["reihen"]["zufall"][-1][1]
                        and a["status"] == "ok") else "aktuell ≠ letzte Zeile"
    pruefe("aktuell_gleich_letzte", aktuell)

    def grenzen():
        f32 = struct.unpack("f", struct.pack("f", 89.96))[0]
        py = [ss.ampel(x) for x in (69.99999, 70, 89.96, 90, None)]
        pa = [ss.anzeige(x) for x in (89.96, 90, 69.99999, f32, 25.753968253968253)]
        soll_a, soll_z = ["green", "yellow", "yellow", "red", "grey"], [89.9, 90.0, 69.9, 89.9, 25.7]
        if py != soll_a or j["hilfs"]["ampel"] != soll_a:
            return f"Ampel Python {py}, JS {j['hilfs']['ampel']}"
        if pa != soll_z or j["hilfs"]["anzeige"] != soll_z:
            return f"Anzeige Python {pa}, JS {j['hilfs']['anzeige']}"
        k = j["hilfs"]["konstanten"]
        if (k["GELB"], k["ROT"], k["REF_MAX"], k["REF_MIN"]) != (ss.GRENZE_GELB, ss.GRENZE_ROT, ss.REFERENZ_MAX, ss.REFERENZ_MIN):
            return f"Konstanten JS {k} ≠ Python"
        return True
    pruefe("grenzen_anzeige", grenzen)

    def anzeigeregel():
        a = j["anzeige"]
        if a["voll"]["quelle"] != "db":
            return "vollständiger DB-Lauf nicht genutzt"
        for k in ("luecke", "alt", "leer"):
            if a[k]["quelle"] != "browser":
                return f"{k}: DB-Werte trotz Lücke/veraltet genutzt"
        return True
    pruefe("anzeige_db_oder_browser", anzeigeregel)

    # ── Datenbankablauf ──
    DK, CK = tage(2000), zufall(2000, 11)   # 1224 Scores → drei Batches à 500 (Batchfehler mitten im Lauf)

    def neue_db():
        return FakeDB(kurse_zeilen("SPY", DK, CK))

    def still(_m):
        pass

    def gelesen(db):
        l = ss.letzter_fertiger_lauf(db, "SPY")
        return [] if not l else [r["date"] for r in db.t["stress_scores"] if r["lauf_id"] == l["lauf_id"]]

    def db_erfolg():
        db = neue_db()
        r = ss.vollauf("SPY", db, still)
        soll = DK[776:]
        if r["n_scores"] != len(soll) or sorted(gelesen(db)) != soll:
            return f"{r['n_scores']} Scores, gelesen {len(gelesen(db))}, soll {len(soll)}"
        # zweiter Lauf nach Kurskorrektur in der Mitte + entfernter Kurs: neue Version mit exakt neuer Sollmenge
        db.t["prices"][500]["close"] *= 1.2
        del db.t["prices"][900]
        ss.vollauf("SPY", db, still)
        neu_soll = [d for d in DK if d != DK[900]][776:]
        return True if sorted(gelesen(db)) == neu_soll else f"nach Korrektur gelesen {len(gelesen(db))}, soll {len(neu_soll)}"
    pruefe("db_vollauf", db_erfolg)

    def db_grosses_s():
        # Codex Code-R4: 776 Kurse zu 100, danach 10.000 → S ≈ 1992; muss das 15-stellige Rücklesen bestehen
        d = tage(900)
        c = [100.0] * 776 + [10000.0] * 124
        db = FakeDB(kurse_zeilen("SPY", d, c))
        r = ss.vollauf("SPY", db, still)
        groesstes = max(z["s"] for z in ss.stress_reihe(d, c) if z["s"] is not None)
        return True if r["status"] == "fertig" and groesstes > 1000 else f"Lauf {r}, größtes S {groesstes}"
    pruefe("db_grosses_s", db_grosses_s)

    def db_fehler(setze, name):
        db = neue_db()
        ss.vollauf("SPY", db, still)
        vorher = gelesen(db)
        vorher_lauf = ss.letzter_fertiger_lauf(db, "SPY")["lauf_id"]
        setze(db)
        try:
            ss.vollauf("SPY", db, still)
            return f"{name}: kein Fehler gemeldet"
        except Exception:  # noqa: BLE001
            pass
        l = ss.letzter_fertiger_lauf(db, "SPY")
        if l["lauf_id"] != vorher_lauf or gelesen(db) != vorher:
            return f"{name}: sichtbarer Lauf verändert"
        if any(x["status"] == "laeuft" for x in db.t["stress_laeufe"]):
            return f"{name}: Lauf bleibt auf 'laeuft'"
        return True

    pruefe("db_batchfehler", lambda: db_fehler(lambda db: setattr(db, "fehler_insert_nach", db.inserts + 1), "Batchfehler"))
    pruefe("db_rueckleseprobe", lambda: db_fehler(lambda db: setattr(db, "rueck_verfaelschen", True), "Rücklesefehler"))
    pruefe("db_lease_abgelaufen", lambda: db_fehler(lambda db: setattr(db, "lease_ablaufen", True), "Lease"))

    def db_eingabe():
        for setze, name in ((lambda db: setattr(db, "zaehlung_falsch", True), "Zählung"),
                            (lambda db: setattr(db, "fehler_lesen", True), "Netzwerk")):
            db = neue_db()
            setze(db)
            try:
                ss.vollauf("SPY", db, still)
                return f"{name}: kein Abbruch"
            except ss.LadeFehler:
                pass
            # Sperre wird vor dem Laden erworben (Code-R1 Befund 1) → Lauf existiert, aber abgebrochen, ohne Zeilen
            if db.t["stress_scores"] or [l["status"] for l in db.t["stress_laeufe"]] != ["abgebrochen"]:
                return f"{name}: trotz Ladefehler geschrieben oder Lauf nicht abgebrochen"
        return True
    pruefe("db_unvollstaendige_eingabe", db_eingabe)

    def db_sperre():
        db = neue_db()
        db.rpc_ausfuehren("stress_lauf_starten", {"p_ticker": "SPY"})
        try:
            ss.vollauf("SPY", db, still)
            return "zweiter Lauf trotz Sperre"
        except RuntimeError:
            pass
        if db.t["stress_scores"]:
            return "trotz Sperre geschrieben"
        db.jetzt += timedelta(minutes=31)          # Lease abgelaufen → Übernahme erlaubt
        ss.vollauf("SPY", db, still)
        return True if gelesen(db) else "nach Lease-Ablauf kein Lauf"
    pruefe("db_sperre", db_sperre)

    def db_antwort_verloren():
        db = neue_db()
        db.antwort_verloren = True
        try:
            ss.vollauf("SPY", db, still)
        except Exception:  # noqa: BLE001
            pass
        st = [l["status"] for l in db.t["stress_laeufe"]]
        return True if st == ["fertig"] else f"Status nach verlorener Antwort {st} (fertig darf nicht abgebrochen werden)"
    pruefe("db_abbrechen_nur_laufend", db_antwort_verloren)

    def db_aufraeumen():
        db = neue_db()
        for _ in range(4):
            ss.vollauf("SPY", db, still)
        laufend = db.rpc_ausfuehren("stress_lauf_starten", {"p_ticker": "SPY"})
        db.t["stress_scores"].append({"lauf_id": laufend, "ticker": "SPY", "date": DK[-1], "score": 1.0, "s": 1.0, "ampel": "green"})
        ss.aufraeumen(db, "SPY")
        ids = {r["lauf_id"] for r in db.t["stress_scores"]}
        fertig = sorted((l for l in db.t["stress_laeufe"] if l["status"] == "fertig"), key=lambda l: l["fertig_am"], reverse=True)
        if laufend not in ids:
            return "Zeilen eines laufenden Laufs gelöscht"
        if ids != {laufend, fertig[0]["lauf_id"], fertig[1]["lauf_id"]}:
            return f"falsche Läufe behalten: {len(ids)}"
        return True
    pruefe("db_aufraeumen", db_aufraeumen)

    def db_sperre_vor_laden():
        # Codex Code-R1 Befund 1: die Sperre muss VOR dem Laden der Kurse erworben sein
        db = neue_db()
        ss.vollauf("SPY", db, still)
        erst_rpc = db.ereignisse.index(("rpc", "stress_lauf_starten"))
        erst_kurse = next(i for i, e in enumerate(db.ereignisse) if e[0] == "prices")
        if erst_rpc > erst_kurse:
            return "Kurse vor dem Sperrerwerb geladen"
        # Ladefehler nach dem Sperrerwerb → Lauf abgebrochen, nicht 'laeuft'
        db2 = neue_db()
        db2.fehler_lesen = True
        try:
            ss.vollauf("SPY", db2, still)
        except ss.LadeFehler:
            pass
        st = [l["status"] for l in db2.t["stress_laeufe"]]
        return True if st == ["abgebrochen"] else f"nach Ladefehler: {st}"
    pruefe("db_sperre_vor_laden", db_sperre_vor_laden)

    def db_aufraeumen_viele():
        # Codex Code-R1 Befund 3: 1003 fertige Läufe — alle Metadaten paginiert lesen, nur die zwei neuesten behalten
        db = neue_db()
        basis = datetime(2026, 1, 1, tzinfo=timezone.utc)
        for k in range(1003):
            lid = f"{k:05d}-x"
            db.t["stress_laeufe"].append({"lauf_id": lid, "ticker": "SPY", "status": "fertig", "fertig_am": (basis + timedelta(hours=k)).isoformat(),
                                          "laeuft_bis": basis, "letztes_datum": None, "kurse_bis": None, "n_scores": 1})
            db.t["stress_scores"].append({"lauf_id": lid, "ticker": "SPY", "date": DK[-1], "score": 1.0, "s": 1.0, "ampel": "green"})
        ss.aufraeumen(db, "SPY")
        rest_l = sorted(l["lauf_id"] for l in db.t["stress_laeufe"])
        rest_s = sorted({r["lauf_id"] for r in db.t["stress_scores"]})
        soll = ["01001-x", "01002-x"]
        return True if rest_l == soll and rest_s == soll else f"übrig: Läufe {len(rest_l)}, Score-Versionen {len(rest_s)}"
    pruefe("db_aufraeumen_paginiert", db_aufraeumen_viele)

    def kurze_reihen():
        for n, soll in ((0, "leer"), (6, "zu_kurz"), (20, "zu_kurz"), (21, "zu_kurz"), (29, "zu_kurz"), (777, "ok")):
            db = FakeDB(kurse_zeilen("X", DK[:n], CK[:n]))
            z = ss.stress_fuer_ticker("X", db, aktuell_bis=date.fromisoformat(DK[max(n - 1, 0)]))
            if z["status"] != soll:
                return f"{n} Kurse: {z['status']} statt {soll}"
            if n == 21 and z.get("s") is None:
                return "21 Kurse: S fehlt"
            if n == 20 and (z.get("s") is not None or z.get("dd20") is None):
                return "20 Kurse: S vorhanden oder dd20 fehlt"
        db = FakeDB(kurse_zeilen("X", DK[:900], CK[:900]))
        db.fehler_lesen = True
        if ss.stress_fuer_ticker("X", db)["status"] != "fehlt":
            return "Ladefehler nicht als fehlt"
        db = FakeDB(kurse_zeilen("X", DK[:900], CK[:900]))
        alt = ss.stress_fuer_ticker("X", db, aktuell_bis=date.fromisoformat(DK[899]) + timedelta(days=30))
        return True if alt["status"] == "veraltet" else f"veraltete Reihe: {alt['status']}"
    pruefe("kurze_reihen_und_status", kurze_reihen)

    def sql_live_anon():
        live = lade_modul(basis / "scripts/verify_stress_sql_live.py", "sql_live_pruef")

        class Fehler(Exception):
            def __init__(self, code):
                super().__init__({"code": code, "message": "x"})
                self.code = code

        def fabrik(verhalten):
            class C:
                def rpc(self, *_a):
                    class E:
                        def execute(self_):
                            if verhalten == "ok":
                                class A:
                                    data = "uuid-1"
                                return A()
                            raise verhalten
                    return E()
            return lambda url, key: C()
        env = {"SUPABASE_URL": "u", "SUPABASE_ANON_KEY": "k"}
        faelle = [
            ("Schlüssel fehlt", {"SUPABASE_URL": "u"}, fabrik(Fehler("42501")), False),
            ("Verbindungsfehler", env, fabrik(ConnectionError("weg")), False),
            ("anderer Code", env, fabrik(Fehler("PGRST301")), False),
            ("anon darf starten", env, fabrik("ok"), False),
            ("Verweigerung 42501", env, fabrik(Fehler("42501")), True),
        ]
        for name, e, f, soll_ok in faelle:
            ist_ok = live.anon_pruefung(e, f) is None
            if ist_ok != soll_ok:
                return f"{name}: bestanden={ist_ok}, soll {soll_ok}"
        return True
    pruefe("sql_live_rechtepruefung", sql_live_anon)

    P.update(statisch(basis))
    if snap:
        P.update(snapshot(basis, snap, ss))
    return P


def statisch(basis):
    P = {}

    def t(rel):
        return (basis / rel).read_text(encoding="utf-8-sig") if (basis / rel).exists() else (REPO / rel).read_text(encoding="utf-8-sig")
    crash, dash, wl, js = t(CRASH), t(DASH), t(WL), t(JS)
    P["seiten_eine_rechnung"] = True if (
        "function computeRegime" not in crash and "function computeRegime" not in dash
        and "SA.dashCompute.computeStress(rawRows)" in dash and "SA.dashCompute.computeStress(rows)" in wl
        and "SA.dashCompute.stressReihe(rawRows)" in crash and "/landing/js/dash-compute.js" in dash
        and "/landing/js/dash-compute.js" in crash and "computeRegime" not in js.replace("computeRegime-Ausgabe", "")) \
        else "Inline-Rechnung oder fehlende Einbindung von dash-compute.js"
    P["crash_ladezeitraum"] = True if "SA.fetchAllPrices('SPY','&date=gte.'+isoVor(13,0))" in crash else "Crash-Seite lädt nicht 13 Jahre"
    sichtbar = re.sub(r"<script[\s\S]*?</script>", " ", crash)
    verboten = [w for w in ("Isolation", "Machine Learning", "Machine-Learning", "Frühwarn", "Fr&uuml;hwarn", "Backtest der Warnsignale", "sklearn")
                if w in sichtbar or w in crash.split("<script>\n  !function(){")[-1].split("</script>")[0]]
    P["crash_begriffe"] = True if not verboten else f"verbotene Begriffe: {verboten}"
    crs, night, health, week = t(CRS), t(NIGHT), t(HEALTH), t(WEEK_T)
    P["schreibweg_ohne_if"] = True if ("IsolationForest" not in crs and "compute_regime_scores import compute_regime_scores" not in night
                                       and "stress_score.vollauf" in crs and "_stress.vollauf" in night) else "Schreibweg nutzt noch IF"
    P["health_methodennachweis"] = True if ("stress_score.stress_aktuell" in health and "letzter_fertiger_lauf" in health) \
        else "Health-Check ohne Nachrechnung"
    abschnitt = week.split("SEKTION 4")[1].split("CTA ═")[0] if "SEKTION 4" in week else ""
    P["wochenreport"] = True if (abschnitt and "Isolation" not in abschnitt and "* 100" not in abschnitt
                                 and "{% elif not ohne %}" in abschnitt) \
        else "Wochenreport: IF-Text, doppeltes ×100 oder 'alles grün' ohne Abdeckung"
    comp = t("scripts/check_db_completeness.py")
    P["completeness_nur_fertig"] = True if ('if table == "stress_scores":' in comp and "letzter_fertiger_lauf" in comp) \
        else "Completeness prüft stress_scores nicht über den veröffentlichten Lauf"
    sql = t(SQL)
    sql_ok = ("ON stress_laeufe (ticker) WHERE status = 'laeuft'" in sql
              and "WHERE lauf_id = p_lauf AND status = 'laeuft' AND laeuft_bis > NOW();" in sql
              and "UPDATE stress_laeufe SET status = 'abgebrochen' WHERE lauf_id = p_lauf AND status = 'laeuft';" in sql
              and "TO anon USING (true)" in sql and "FROM PUBLIC, anon, authenticated" in sql)
    P["sql_regeln"] = True if sql_ok else "SQL: Index, Lease, Abbrechen-Regel oder Rechte fehlen"
    return P


def snapshot(basis, snap, ss):
    P = {}
    faelle = {}
    for f in sorted(pathlib.Path(snap).glob("*.json")):
        if f.name == "snapshot.json":
            continue
        rows = json.loads(f.read_text(encoding="utf-8"))
        faelle[f.stem.replace("_", "^")] = [{"date": r["date"], "close": r["close"]} for r in rows]
    j = js_lauf(basis, {"faelle": faelle})
    falsch = []
    for tk, rows in faelle.items():
        py = ss.stress_reihe([r["date"] for r in rows], [r["close"] for r in rows])
        js = j["reihen"][tk]
        if len(py) != len(js):
            falsch.append(f"{tk}: Länge {len(py)} ≠ {len(js)}")
            continue
        for a, b in zip(py, js):
            if a["date"] != b[0] or not gleich(a["score"], b[1]) or not gleich(a["s"], b[2]) or a["ampel"] != b[3]:
                falsch.append(f"{tk} {a['date']}: Python {a['score']} ≠ JS {b[1]}")
                break
    P["snap_zwilling"] = True if not falsch else "; ".join(falsch)
    fehl = []
    for tk in ("SPY", "^GSPC"):
        if tk not in faelle:
            continue
        by = {z["date"]: z["score"] for z in ss.stress_reihe([r["date"] for r in faelle[tk]], [r["close"] for r in faelle[tk]])}
        for d in ("2008-10-15", "2020-03-16", "2025-04-08"):
            if d in by and not (by[d] is not None and by[d] >= 90):
                fehl.append(f"{tk} {d} = {by[d]}")
        if "2017-07-14" in by and not (by["2017-07-14"] is not None and by["2017-07-14"] < 70):
            fehl.append(f"{tk} 2017-07-14 = {by['2017-07-14']}")
    P["snap_plausibel"] = True if not fehl else "; ".join(fehl)
    return P


MUTATIONEN = [
    ("Referenz enthält den heutigen Tag (Python)", PY, "        score = None\n        ref_n = len(fenster)\n",
     "        score = None\n        if s is not None: bisect.insort(fenster, s)\n        ref_n = len(fenster)\n", "rechnung_gegen_naiv"),
    ("Gleichstand voll statt halb (Python)", PY, "kleiner + 0.5 * (bis_gleich - kleiner)", "kleiner + 1.0 * (bis_gleich - kleiner)", "gleichstand_halb"),
    ("Gleichstand voll statt halb (JS)", JS, "kleiner + 0.5 * (bisGleich - kleiner)", "kleiner + 1.0 * (bisGleich - kleiner)", "gleichstand_halb"),
    ("Populations- statt Stichproben-Std (JS)", JS, "return Math.sqrt(q / (n - 1));", "return Math.sqrt(q / n);", "rechnung_gegen_naiv"),
    ("Fenster 21 statt 20 Schlüsse für dd20 (JS)", JS, "var hoch = c[i - 19];\n        for (k = i - 18; k <= i; k++)",
     "var hoch = c[Math.max(0, i - 20)];\n        for (k = Math.max(0, i - 19); k <= i; k++)", "rechnung_gegen_naiv"),
    ("Mindestreferenz 755 (Python)", PY, "REFERENZ_MIN = 756", "REFERENZ_MIN = 755", "grenze_777"),
    ("Fenster ohne Abbau (JS)", JS, "        if (altI >= 0 && sFolge[altI] != null) fenster.splice(_lowerBound(fenster, sFolge[altI]), 1);\n", "",
     "fenster_2520"),
    ("ungültiger Kurs als 0-Rendite behalten (Python)", PY, "        if not math.isfinite(w) or w <= 0:\n            continue\n",
     "        if not math.isfinite(w) or w < 0:\n            continue\n", "ungueltige_kurse"),
    ("Grenze Gelb 60 (JS)", JS, "GELB: 70, ROT: 90", "GELB: 60, ROT: 90", "grenzen_anzeige"),
    ("Anzeige gerundet statt abgeschnitten (Python)", PY, "math.floor(score * 10) / 10", "round(score, 1)", "grenzen_anzeige"),
    ("DB-Werte trotz Lücke (JS)", JS, "    if (!voll || !db[letzte.date]) return { zeilen: anzeige, quelle: 'browser' };\n", "",
     "anzeige_db_oder_browser"),
    ("Veröffentlichen ohne Rücklesen", PY, "        _vergleiche(soll, rueck)\n", "", "db_rueckleseprobe"),
    ("Score ungerundet gespeichert", PY, "score = round(100.0 * (kleiner + 0.5 * (bis_gleich - kleiner)) / ref_n, STELLEN_SCORE)",
     "score = 100.0 * (kleiner + 0.5 * (bis_gleich - kleiner)) / ref_n", "db_vollauf"),
    ("S nur auf Nachkommastellen gerundet", PY, '"s": None if s is None else float(f"{s:.{SIGNIFIKANT_S}g}")',
     '"s": None if s is None else round(s, 12)', "db_grosses_s"),
    ("Kein Abbruch bei Fehler", PY, "            _rpc(client, \"stress_lauf_abbrechen\", {\"p_lauf\": lauf_id})\n", "            pass\n",
     "db_batchfehler"),
    ("Zählung nicht geprüft", PY, "    if quell_n is None or len(zeilen) != quell_n:\n", "    if quell_n is None:\n", "db_unvollstaendige_eingabe"),
    ("Aufräumen löscht alle anderen Läufe", PY, "    weg = [l[\"lauf_id\"] for l in laeufe if l[\"status\"] == \"abgebrochen\"] + [l[\"lauf_id\"] for l in fertig[behalten:]]",
     "    weg = [l[\"lauf_id\"] for l in laeufe if l[\"lauf_id\"] not in [f[\"lauf_id\"] for f in fertig[:behalten]]]", "db_aufraeumen"),
    ("Kurze Reihe als Ladefehler", PY, "    if quell_n is None or len(zeilen) != quell_n:\n",
     "    if quell_n is None or len(zeilen) != quell_n or len(zeilen) < 30:\n", "kurze_reihen_und_status"),
    ("Sperre erst nach dem Laden", PY,
     "    lauf_id = _rpc(client, \"stress_lauf_starten\", {\"p_ticker\": ticker})\n    if not lauf_id:\n        raise RuntimeError(f\"{ticker}: ein anderer Lauf ist aktiv (Sperre) — nichts geschrieben\")\n    try:\n        daten, closes, info = lade_kurse(ticker, client)\n",
     "    daten, closes, info = lade_kurse(ticker, client)\n    lauf_id = _rpc(client, \"stress_lauf_starten\", {\"p_ticker\": ticker})\n    if not lauf_id:\n        raise RuntimeError(f\"{ticker}: ein anderer Lauf ist aktiv (Sperre) — nichts geschrieben\")\n    try:\n",
     "db_sperre_vor_laden"),
    ("Aufräumen ohne Paginierung", PY,
     "                .order(\"lauf_id\").range(offset, offset + 999).execute().data) or []\n        laeufe += teil\n        if len(teil) < 1000:\n            break\n        offset += 1000\n",
     "                .order(\"lauf_id\").execute().data) or []\n        laeufe += teil\n        break\n",
     "db_aufraeumen_paginiert"),
    ("Completeness über alle Zeilen", "scripts/check_db_completeness.py", 'if table == "stress_scores":', 'if table == "__nie__":',
     "completeness_nur_fertig"),
    ("Live-Test: jeder Fehler gilt als Verweigerung", "scripts/verify_stress_sql_live.py", "        if code in VERWEIGERT:\n",
     "        if True:\n", "sql_live_rechtepruefung"),
    ("Live-Test: fehlender Schlüssel bestanden", "scripts/verify_stress_sql_live.py",
     "        return \"SUPABASE_URL/SUPABASE_ANON_KEY fehlt — Rechte nicht prüfbar\"", "        return None", "sql_live_rechtepruefung"),
    ("Crash-Seite lädt ab 2020", CRASH, "SA.fetchAllPrices('SPY','&date=gte.'+isoVor(13,0))", "SA.fetchAllPrices('SPY','&date=gte.2020-01-01')",
     "crash_ladezeitraum"),
    ("Dashboard mit eigener Rechnung", DASH, "      var regime = SA.dashCompute.computeStress(rawRows);",
     "      function computeRegime(r){return SA.dashCompute.computeStress(r);}\n      var regime = computeRegime(rawRows);", "seiten_eine_rechnung"),
    ("Wochenreport 'alle grün' ohne Abdeckung", WEEK_T, "{% elif not ohne %}", "{% else %}", "wochenreport"),
    ("SQL: Abbrechen auch aus fertig", SQL, "UPDATE stress_laeufe SET status = 'abgebrochen' WHERE lauf_id = p_lauf AND status = 'laeuft';",
     "UPDATE stress_laeufe SET status = 'abgebrochen' WHERE lauf_id = p_lauf;", "sql_regeln"),
]

UNGUELTIG_ERWARTET = [
    ("Syntaxfehler (Probe muss abbrechen)", JS, "  function stressReihe(rows) {", "  function stressReihe(rows) {{", "rechnung_gegen_naiv"),
    ("Anker trifft nicht", JS, "DIESER TEXT STEHT NICHT IN DER DATEI", "x", "rechnung_gegen_naiv"),
    ("trifft das Gerüst", JS, "    stressAnzeigeWerte: stressAnzeigeWerte,\n", "", "anzeige_db_oder_browser"),
]


def _kopie(tmp):
    for rel in (PY, JS, CRASH, DASH, WL, SQL, CRS, NIGHT, HEALTH, WEEK_T, "scripts/check_db_completeness.py",
                "scripts/verify_stress_sql_live.py"):
        (tmp / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(REPO / rel, tmp / rel)


def _bewerte(name, datei, alt, neu, soll):
    quelle = (REPO / datei).read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    if quelle.count(alt) != 1:
        return "ungueltig", "Anker trifft nicht"
    with tempfile.TemporaryDirectory() as t:
        tmp = pathlib.Path(t)
        _kopie(tmp)
        (tmp / datei).write_text(quelle.replace(alt, neu), encoding="utf-8")
        try:
            P = pruefe_alles(tmp)
        except RuntimeError as e:
            return "ungueltig", f"Probe abgebrochen: {str(e)[:120]}"
    gerissen = sorted(k for k, v in P.items() if v is not True)
    if any(k.startswith("[Aufbau]") for k in gerissen):
        return "ungueltig", f"Aufbau gerissen: {gerissen}"
    if soll not in gerissen:
        return "verfehlt", f"erwartet {soll}, gerissen {gerissen}"
    andere = [k for k in gerissen if k != soll]
    return "gefangen", (f"auch: {andere}" if andere else "")


def mutationen():
    grund = pruefe_alles()
    rot = [k for k, v in grund.items() if v is not True]
    if rot:
        print("Grundzustand nicht grün — Mutationen sinnlos:", rot)
        return 1
    ok = 0
    for m in MUTATIONEN:
        u, info = _bewerte(*m)
        ok += u == "gefangen"
        print(f"  {u.upper():9s} {m[0]} → {m[4]} {info}")
    falsch = 0
    for m in UNGUELTIG_ERWARTET:
        u, info = _bewerte(*m)
        richtig = u == "ungueltig"
        falsch += not richtig
        print(f"  {'OK' if richtig else 'FALSCH'}: als ungültig erkannt? {m[0]} → {u} {info}")
    print(f"{ok}/{len(MUTATIONEN)} Mutationen gefangen, {len(UNGUELTIG_ERWARTET) - falsch}/{len(UNGUELTIG_ERWARTET)} untaugliche richtig verworfen")
    return 0 if ok == len(MUTATIONEN) and not falsch else 1


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if "--mutationen" in sys.argv:
        return mutationen()
    snap = None
    if "--snapshot" in sys.argv:
        snap = pathlib.Path(sys.argv[sys.argv.index("--snapshot") + 1])
    elif "--ohne-snapshot" not in sys.argv:
        print("UNGEPRÜFT: ohne --snapshot <ordner> fehlen Zwillings- und Plausibilitätsprüfung (bewusst: --ohne-snapshot)")
        return 1
    P = pruefe_alles(REPO, snap)
    rot = {k: v for k, v in P.items() if v is not True}
    for k, v in rot.items():
        print(f"FEHLER {k}: {v}")
    print(f"verify_stress_ampel: {len(P) - len(rot)}/{len(P)} Prüfungen bestanden" + ("" if snap else " (ohne Snapshot)"))
    return 0 if not rot else 1


if __name__ == "__main__":
    sys.exit(main())
