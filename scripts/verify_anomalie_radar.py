#!/usr/bin/env python3
"""
verify_anomalie_radar.py — Wächter für das Anomalie-Radar (Plan v3 Teil C, Codex-Freigabe 2026-10-09).

Prüft die ECHTE landing/js/decade-compute.js (in node, scripts/js/probe_anomalie_radar.js) gegen eine unabhängige,
naive Python-Referenz, die den Vertrag direkt aus Rohkursen nachrechnet (ohne die JS-Hilfsfunktionen):

  1. Randfälle: konstante Kurse, Sprung im aktuellen Fenster, 29.02., Fenster über den Jahreswechsel, Gleichstände
     im Rang, Lücke im aktuellen/historischen Fenster, < 10 Jahre, nur die 30 jüngsten Jahre, Marktklasse,
     fehlender Ticker, Präfixinvarianz (as_of), veraltetes Datenende.
  2. Echte Reihen (mit --snapshot <ordner>): SPY, ^GDAXI, ^DJI an jedem 21. Handelstag ab 2000 — Status/n exakt,
     z/Rang auf 1e-9.
  3. Darstellung: beide Renderer (Seite 'zeile', Dashboard 'karte') für ok und nicht_berechenbar; keine Grün/Rot-
     Klassen; Dashboard und alle Seiten nutzen die eine Rechnung; „KI Quick-Check" und der Python-Zwilling sind weg.

Nutzung:
    py -3.14 scripts/verify_anomalie_radar.py --snapshot <ordner>     # alles
    py -3.14 scripts/verify_anomalie_radar.py --ohne-snapshot         # ohne echte Reihen (bewusst)
    py -3.14 scripts/verify_anomalie_radar.py --mutationen            # prüft den Wächter (auf Kopien, nie im Baum)
Exit 0 = alles bestanden.
"""
from __future__ import annotations
import datetime as dt
import json
import math
import pathlib
import re
import shutil
import statistics
import subprocess
import sys
import tempfile

REPO = pathlib.Path(__file__).resolve().parent.parent
DC = "landing/js/decade-compute.js"
DASH = "landing/pages/dashboard.html"
SEITEN = ["dekadenzyklus", "jahreszyklus", "monatszyklus", "overnight", "risikozyklus", "tdom-analyse"]
PROBE = "scripts/js/probe_anomalie_radar.js"
TOL = {"krypto": 1, "forex": 3, "boerse": 7}


# ── unabhängige Referenz ─────────────────────────────────────────────────────
def klasse(ticker):
    if not ticker or not str(ticker).strip():
        raise ValueError("Ticker fehlt")
    t = str(ticker).strip().upper()
    return "krypto" if t.endswith("-USD") else "forex" if t.endswith("=X") else "boerse"


def referenz(rows, ticker, as_of=None):
    T = TOL[klasse(ticker)]
    m = {}
    for r in rows:
        c = r["close"]
        if c is None or not isinstance(c, (int, float)) or not math.isfinite(c) or c <= 0:
            continue
        d = str(r["date"])[:10]
        if as_of and d > as_of:
            continue
        m[d] = float(c)
    daten = sorted(m)
    if len(daten) < 11:
        return {"status": "nicht_berechenbar"}
    tage = [dt.date.fromisoformat(d) for d in daten]
    closes = [m[d] for d in daten]

    def ok(e):
        return e >= 10 and all((tage[i] - tage[i - 1]).days <= T for i in range(e - 9, e + 1))

    n = len(daten) - 1
    if not ok(n):
        return {"status": "nicht_berechenbar"}
    R = (closes[n] / closes[n - 10] - 1) * 100
    a = tage[n]
    hist = []
    y = a.year - 1
    while len(hist) < 30:
        tag = min(a.day, [31, 29 if (y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)) else 28, 31, 30, 31, 30,
                              31, 31, 30, 31, 30, 31][a.month - 1])
        ziel = dt.date(y, a.month, tag)
        kand = [i for i in range(len(tage)) if tage[i] <= ziel]
        if not kand or kand[-1] < 10:
            break
        e = kand[-1]
        if (ziel - tage[e]).days <= T and ok(e):
            hist.append((y, (closes[e] / closes[e - 10] - 1) * 100))
        y -= 1
    if len(hist) < 10:
        return {"status": "nicht_berechenbar"}
    werte = [h[1] for h in hist]
    mu, s = statistics.mean(werte), statistics.stdev(werte)
    if not s > 0:
        return {"status": "nicht_berechenbar"}
    z = (R - mu) / s
    rang = 100 * (sum(w < R for w in werte) + 0.5 * sum(w == R for w in werte)) / len(werte)
    st = "stark_auffaellig" if abs(z) >= 7 / 3 else "auffaellig" if abs(z) >= 4 / 3 else "normal"
    return {"status": st, "z": z, "rang": rang, "n": len(werte), "jahr_von": hist[-1][0], "jahr_bis": hist[0][0],
            "rendite": R, "mittel": mu}


# ── Fallbau ──────────────────────────────────────────────────────────────────
def werktage(von, bis, closes_fn, ohne=()):
    rows, d, i = [], dt.date.fromisoformat(von), 0
    ende = dt.date.fromisoformat(bis)
    while d <= ende:
        if d.weekday() < 5 and d.isoformat() not in ohne:
            rows.append({"date": d.isoformat(), "close": closes_fn(i, d)})
            i += 1
        d += dt.timedelta(days=1)
    return rows


def welle(i, d):
    return 100 * math.exp(0.0004 * i + 0.02 * math.sin(i / 7.0) + 0.01 * math.sin(i / 2.3))


def faelle():
    F = []
    F.append({"id": "konstant", "ticker": "SPY", "rows": werktage("2000-01-03", "2025-06-30", lambda i, d: 50.0),
              "soll": "nicht_berechenbar"})
    F.append({"id": "konstant_en", "ticker": "SPY", "rows": werktage("2000-01-03", "2025-06-30", lambda i, d: 50.0),
              "soll": "nicht_berechenbar", "en": True})
    basis = werktage("1990-01-02", "2025-06-30", welle)
    sprung = [dict(r) for r in basis]
    sprung[-3]["close"] *= 1.15
    sprung[-2]["close"] *= 1.15
    sprung[-1]["close"] *= 1.15
    F.append({"id": "sprung", "ticker": "SPY", "rows": sprung, "soll": "ref"})
    F.append({"id": "schalttag", "ticker": "SPY", "rows": werktage("1985-01-02", "2024-02-29", welle), "soll": "ref"})
    F.append({"id": "jahreswechsel", "ticker": "SPY", "rows": werktage("1985-01-02", "2025-01-08", welle), "soll": "ref"})
    # Rechteckwelle mit Periode 20 Handelstagen: jede 10-Tage-Rendite ist exakt +10 % oder 100/110−1 → echte
    # Gleichstände zwischen aktuellem Fenster und Vergleichsjahren, aber Streuung > 0
    gleich = werktage("1990-01-02", "2025-06-30", lambda i, d: 110.0 if (i // 10) % 2 else 100.0)
    F.append({"id": "gleichstand", "ticker": "SPY", "rows": gleich, "soll": "ref"})
    luecke = [r for r in basis if not ("2025-06-16" <= r["date"] <= "2025-06-25")]
    F.append({"id": "luecke_aktuell", "ticker": "SPY", "rows": luecke, "soll": "nicht_berechenbar"})
    luecke_hist = [r for r in basis if not ("2010-06-14" <= r["date"] <= "2010-06-25")]
    F.append({"id": "luecke_historisch", "ticker": "SPY", "rows": luecke_hist, "soll": "ref"})
    F.append({"id": "zu_wenig_jahre", "ticker": "SPY", "rows": werktage("2017-01-02", "2025-06-30", welle),
              "soll": "nicht_berechenbar"})
    F.append({"id": "nur_30_jahre", "ticker": "SPY", "rows": werktage("1970-01-02", "2025-06-30", welle), "soll": "ref"})
    # gleiche Datumsreihe mit einer zweitägigen Lücke im aktuellen Fenster (Mi fehlt): Krypto verwirft, Börse nicht
    tage = werktage("1990-01-02", "2025-06-30", welle, ohne={"2025-06-25"})
    F.append({"id": "klasse_boerse", "ticker": "SPY", "rows": tage, "soll": "ref"})
    F.append({"id": "klasse_krypto", "ticker": "BTC-USD", "rows": tage, "soll": "nicht_berechenbar"})
    F.append({"id": "ohne_ticker", "ticker": "", "rows": basis, "soll": "fehler"})
    zukunft = basis + werktage("2025-07-01", "2025-12-31", lambda i, d: 999.0)
    F.append({"id": "praefix", "ticker": "SPY", "rows": zukunft, "as_of": "2025-06-30", "soll": "gleich:sprung_basis"})
    F.append({"id": "sprung_basis", "ticker": "SPY", "rows": basis, "soll": "ref"})
    alt = werktage("1980-01-02", "2019-11-15", welle)       # veraltetes Datenende: Vergleich am as_of, nicht an der Uhr
    F.append({"id": "veraltet", "ticker": "SPY", "rows": alt, "soll": "ref"})
    return F


STATUS_Z = [4 / 3, -4 / 3, 4 / 3 - 1e-12, 7 / 3, -7 / 3, 7 / 3 - 1e-12, 0.0]
STATUS_SOLL = ["auffaellig", "auffaellig", "normal", "stark_auffaellig", "stark_auffaellig", "auffaellig", "normal"]


def node_probe(basis: pathlib.Path, fl, tmp, reihen=None, mit_status=False, historie=None):
    p = pathlib.Path(tmp) / "faelle.json"
    p.write_text(json.dumps({"reihen": reihen or {}, "status_z": STATUS_Z if mit_status else [],
                             "historie": historie or [],
                             "faelle": [{k: v for k, v in f.items() if k not in ("soll", "ref_rows")} for f in fl]}),
                 encoding="utf-8")
    r = subprocess.run(["node", str(basis / PROBE), str(basis / DC), str(p), str(basis / "landing/i18n/en.json")],
                       capture_output=True, text=True, encoding="utf-8")
    if r.returncode:
        raise RuntimeError("Probe abgebrochen: " + r.stderr[-400:])
    o = json.loads(r.stdout)
    erg = {x["id"]: x for x in o["faelle"]}
    erg["__status__"] = o["status"]
    erg["__css__"] = o.get("css", [])
    erg["__historie__"] = {h["id"]: h for h in o.get("historie", [])}
    return erg


def vergleiche(js, ref):
    e = js.get("ergebnis") or {}
    if ref["status"] == "nicht_berechenbar":
        return e.get("status") == "nicht_berechenbar", f"JS {e.get('status')}, Referenz nicht_berechenbar"
    gut = (e.get("status") == ref["status"] and e.get("n") == ref["n"] and e.get("jahr_von") == ref["jahr_von"]
           and e.get("jahr_bis") == ref["jahr_bis"] and abs(e.get("z", 1e9) - ref["z"]) < 1e-9
           and abs(e.get("rang", 1e9) - ref["rang"]) < 1e-9)
    return gut, (f"JS {e.get('status')} z={e.get('z')} n={e.get('n')} {e.get('jahr_von')}–{e.get('jahr_bis')} rang={e.get('rang')} | "
                 f"Ref {ref['status']} z={ref['z']} n={ref['n']} {ref['jahr_von']}–{ref['jahr_bis']} rang={ref['rang']}")


# ── Prüfungen ────────────────────────────────────────────────────────────────
def pruefen(basis: pathlib.Path, snap: pathlib.Path | None) -> dict:
    P = {}
    with tempfile.TemporaryDirectory() as tmp:
        fl = faelle()
        voll = werktage("1985-01-02", "2025-06-30", welle)
        schalt = werktage("1985-01-02", "2024-02-29", welle)
        js = node_probe(basis, fl, tmp, mit_status=True, reihen={"voll": voll, "schalt": schalt},
                        historie=[{"id": "nur_10_jahre", "ticker": "SPY", "voll": "voll", "ab": "2015-06-01"},
                                  {"id": "schon_voll", "ticker": "SPY", "voll": "voll", "ab": "1985-01-01"},
                                  {"id": "cache_aelter", "ticker": "SPY", "voll": "voll", "ab": "2015-06-01",
                                   "voll_bis": "2025-05-30"},
                                  {"id": "schalttag_filter", "ticker": "SPY", "voll": "schalt", "ab": "2015-06-01"}])
        hist = js.pop("__historie__")
        ref = referenz(voll, "SPY")
        k, v = hist.get("nur_10_jahre", {}), hist.get("schon_voll", {})
        P["historie_regler_unabhaengig"] = True if (k.get("ergebnis", {}).get("n") == ref["n"] == 30
                                                    and abs(k["ergebnis"]["z"] - ref["z"]) < 1e-9
                                                    and k.get("aufrufe") == [["SPY", "&date=gte.1994-06-30"]]
                                                    and v.get("aufrufe") == []
                                                    and v.get("ergebnis") == k.get("ergebnis"))             else f"10-Jahre-Seite: {k.get('ergebnis', {}).get('n')} Jahre, Aufrufe {k.get('aufrufe')}; volle Seite Aufrufe {v.get('aufrufe')}"
        c = hist.get("cache_aelter", {}).get("ergebnis", {})
        P["historie_cache_aelter"] = True if (c.get("as_of") == "2025-06-30" and abs(c.get("z", 1e9) - ref["z"]) < 1e-9) \
            else f"älterer Cache verdrängt das Datenende: as_of {c.get('as_of')}"
        sh = hist.get("schalttag_filter", {})
        P["historie_schalttag"] = True if (sh.get("aufrufe") == [["SPY", "&date=gte.1993-02-28"]]
                                           and sh.get("ergebnis", {}).get("n") == 30) \
            else f"29.02.: Aufrufe {sh.get('aufrufe')}, n {sh.get('ergebnis', {}).get('n')}"
        st = js.pop("__status__")
        css = js.pop("__css__")
        P["css_von_der_darstellung"] = True if css == ["sa-anomaly-css"] else f"CSS-Einbindung: {css}"
        falsch = [(z, s_) for (z, s_), soll in zip(st, STATUS_SOLL) if s_ != soll]
        P["status_grenzen"] = True if (len(st) == len(STATUS_SOLL) and not falsch) else f"Grenzen falsch: {falsch}"
        for f in fl:
            o = js[f["id"]]
            if f["soll"] == "fehler":
                P[f"fall_{f['id']}"] = True if "fehler" in o else f"kein Fehler bei fehlendem Ticker: {o}"
            elif f["soll"].startswith("gleich:"):
                a, b = o.get("ergebnis"), js[f["soll"].split(":")[1]].get("ergebnis")
                P[f"fall_{f['id']}"] = True if a == b else f"as_of nicht präfixinvariant: {a} ≠ {b}"
            elif "fehler" in o:
                P[f"fall_{f['id']}"] = f"Probe warf: {o['fehler']}"
            else:
                ref = referenz(f["rows"], f["ticker"], f.get("as_of"))
                if f["soll"] == "nicht_berechenbar" and ref["status"] != "nicht_berechenbar":
                    P[f"fall_{f['id']}"] = f"[Aufbau] Referenz erwartet nicht_berechenbar, hat {ref['status']}"
                    continue
                gut, txt = vergleiche(o, ref)
                P[f"fall_{f['id']}"] = True if gut else txt
        # gezielte Sollwerte (nicht nur JS == Referenz)
        e = js["nur_30_jahre"].get("ergebnis", {})
        P["soll_30_jahre"] = True if (e.get("n") == 30 and e.get("jahr_von") == 1995) else f"n={e.get('n')} von={e.get('jahr_von')}"
        e = js["schalttag"].get("ergebnis", {})
        P["soll_schalttag"] = True if (e.get("status") != "nicht_berechenbar" and e.get("jahr_bis") == 2023) \
            else f"29.02.: {e}"
        e = js["sprung"].get("ergebnis", {})
        P["soll_sprung_auffaellig"] = True if (e.get("status") == "stark_auffaellig" and e.get("z", 0) > 0) else f"{e}"
        e = js["veraltet"].get("ergebnis", {})
        P["soll_veraltet_asof"] = True if (e.get("as_of") == "2019-11-15" and e.get("jahr_bis") == 2018) else f"{e}"
        e = js["gleichstand"].get("ergebnis", {})
        P["soll_gleichstand_halb"] = True if (e.get("rang") is not None and abs(e["rang"] * e["n"] / 100 * 2 % 1) < 1e-9
                                             and e["rang"] not in (0, 100)) else f"Rang {e.get('rang')}"
        # Darstellung
        for fid in ("sprung", "konstant"):
            o = js[fid]
            for form in ("html_zeile", "html_karte"):
                h = o.get(form, "")
                if fid == "konstant":
                    P[f"html_{fid}_{form}"] = True if ("Nicht berechenbar" in h and "Streuung" in h and "z =" not in h) \
                        else f"nicht_berechenbar falsch dargestellt: {h[:120]}"
                else:
                    farbe = re.search(r'class="kpi-value (green|red)"|#34d399|#f87171|#30e878|#ff4040', h)
                    P[f"html_{fid}_{form}"] = True if ("z = +" in h and "Vergleichsjahre" in h and "Rang" in h
                                                      and "sa-anom-prank-mark" in h and not farbe) \
                        else f"Darstellung (z, Basis, Rang, keine Grün/Rot-Klasse): {h[:160]}"
        h = js["konstant_en"].get("html_zeile", "")
        P["html_en_grund"] = True if ("Not computable" in h and "no dispersion" in h and "Streuung" not in h) \
            else f"EN-Fehlertext: {h[:160]}"
        # echte Reihen
        if snap:
            fl2, reihen = [], {}
            for t, datei in (("SPY", "SPY.json"), ("^GDAXI", "_GDAXI.json"), ("^DJI", "_DJI.json")):
                rows = [{"date": z["date"], "close": z["close"]} for z in json.loads((snap / datei).read_text())]
                reihen[t] = rows
                daten = [r["date"] for r in rows if r["date"] >= "2000-01-01"]
                for d in daten[::21]:
                    fl2.append({"id": f"{t}@{d}", "ticker": t, "reihe": t, "as_of": d, "ohne_html": True})
            js2 = node_probe(basis, fl2, tmp, reihen)
            abw, stati = [], {}
            for f in fl2:
                ref = referenz(reihen[f["reihe"]], f["ticker"], f["as_of"])
                gut, txt = vergleiche(js2[f["id"]], ref)
                stati[ref["status"]] = stati.get(ref["status"], 0) + 1
                if not gut:
                    abw.append(f"{f['id']}: {txt}")
            P["echte_reihen"] = True if not abw else f"{len(abw)}/{len(fl2)} abweichend, z. B. {abw[:2]}"
            print(f"  Info: echte Reihen {len(fl2)} Stichtage, Status {stati}")
    # statisch
    dash = (basis / DASH).read_text(encoding="utf-8")
    P["dashboard_eine_rechnung"] = True if ("SA.decadeCompute.anomalieMitHistorie(rawRows, _radarTicker)" in dash
                                            and "anomalieHtml(anom, currentTicker, 'karte')" in dash
                                            and "anom.score" not in dash) else "Dashboard rechnet/rendert selbst"
    dc = (basis / DC).read_text(encoding="utf-8")
    P["fromprices_nutzt_kern"] = True if ("anomaly = SA.decadeCompute.anomalie(rows, ticker)" in dc
                                          and "zScore * 30" not in dc) else "fromPrices rechnet eigene Anomalie"
    # Abrufkennung: jede Ticker-Seite vergibt sie in loadTicker und prüft sie im Rückruf (Codex Anomalie R4)
    ohne = []
    for seite in SEITEN + ["dashboard"]:
        q = (basis / f"landing/pages/{seite}.html").read_text(encoding="utf-8")
        rumpf = q[q.index("function loadTicker("):]
        rumpf = rumpf[:rumpf.index("\n    }\n")]
        # Kennung beim Start, Prüfung im Erfolgs- UND im Fehler-Rückruf (Codex R5)
        if "SA.ladeKennung.start(ticker" not in rumpf or len(re.findall(r"SA\.ladeKennung\.aktuell\(_lk\)\)\s*return", rumpf)) < 2 \
                or not re.search(r"catch\(function\(\w+\)\s*\{\s*(?://[^\n]*\n)?\s*if\s*\(!SA\.ladeKennung\.aktuell\(_lk\)\)\s*return", rumpf):
            ohne.append(seite)
    if "SA.ladeKennung.aktuell(_rk)) renderAnomalyCard(a)" not in dash or "var _rk = _seitenKennung;" not in dash:
        ohne.append("dashboard-radar")
    P["abrufkennung"] = True if not ohne else f"ohne Abrufkennung: {ohne}"
    # Verhalten von SA.ladeKennung (aus app.js gezogen): A → B → A entwertet B und lädt A; A erneut ohne Wechsel = null
    app = (basis / "landing/js/app.js").read_text(encoding="utf-8")
    a0 = app.index("SA.ladeKennung = (function() {")
    a1 = app.index("})();", a0) + len("})();")
    js_code = "var SA={};" + app[a0:a1] + """
var L=SA.ladeKennung, o=[];
var k1=L.start('A', null); o.push(L.aktuell(k1));
var k2=L.start('B','A');  o.push(L.aktuell(k1), L.aktuell(k2));
var k3=L.start('A','A');  o.push(k3===null, L.aktuell(k2), L.aktuell(k3));
var k4=L.start('A','A');  o.push(k4===null, L.aktuell(k3));
console.log(JSON.stringify(o));"""
    r = subprocess.run(["node", "-e", js_code], capture_output=True, text=True)
    soll = [True, False, True, False, False, True, True, True]
    try:
        ist = json.loads(r.stdout)
    except Exception:  # noqa: BLE001
        ist = r.stderr[:200]
    P["ladekennung_verhalten"] = True if ist == soll else f"ist {ist}, soll {soll}"
    # Verhalten am echten loadTicker des Dekadenzyklus: A geladen, B unterwegs, A erneut (Cache) → Ansicht A, kein
    # Ladeoverlay; B kommt danach an (Erfolg bzw. Fehler) → ändert nichts (Codex R6)
    dek = (basis / "landing/pages/dekadenzyklus.html").read_text(encoding="utf-8")
    l0 = dek.index("    function loadTicker(ticker){")
    l1 = dek.index("\n    }\n", l0) + len("\n    }")
    for ausgang in ("erfolg", "fehler"):
        js_code = "var SA={};" + app[a0:a1] + """
var overlay=null, fehler=null, inits=[], tickerCache={}, D=null, rawRows=null, currentTicker=null, offen=null;
function showLoading(t){overlay=t;} function hideLoading(){overlay=null;} function showError(t){fehler=t;}
function init(){inits.push(currentTicker);}
var document={getElementById:function(){return {value:'20'};}};
SA.supabase={url:'x'};
SA.decadeCompute={fromPrices:function(rows,t){return {t:t};}};
SA.fetchAllPrices=function(t){return new Promise(function(res,rej){offen={t:t,res:res,rej:rej};});};
""" + dek[l0:l1] + """
var rowsA=[]; for(var i=0;i<250;i++) rowsA.push({close:'1'});
loadTicker('A'); var a=offen; a.res(rowsA);
setTimeout(function(){
  loadTicker('B'); var b=offen;
  loadTicker('A');
  var vorher={overlay:overlay, ticker:currentTicker};
  if('""" + ausgang + """'==='erfolg') b.res(rowsA); else b.rej('netz');
  setTimeout(function(){console.log(JSON.stringify({vorher:vorher, overlay:overlay, ticker:currentTicker, fehler:fehler}));},0);
},0);"""
        r = subprocess.run(["node", "-e", js_code], capture_output=True, text=True)
        try:
            ist = json.loads(r.stdout)
        except Exception:  # noqa: BLE001
            ist = r.stderr[:200]
        soll = {"vorher": {"overlay": None, "ticker": "A"}, "overlay": None, "ticker": "A", "fehler": None}
        P[f"dekaden_rueckwechsel_{ausgang}"] = True if ist == soll else f"ist {ist}"
    rest = [s for s in SEITEN if "KI Quick-Check" in (basis / f"landing/pages/{s}.html").read_text(encoding="utf-8")]
    for j in ("de", "en"):
        if "Quick-Check" in (basis / f"landing/i18n/{j}.json").read_text(encoding="utf-8"):
            rest.append(f"{j}.json")
    P["kein_ki_quickcheck"] = True if not rest else f"noch in: {rest}"
    P["python_zwilling_weg"] = True if not (basis / "shared/anomaly_engine.py").exists() else "shared/anomaly_engine.py existiert"
    return P


# ── Mutationen (auf Kopien) ──────────────────────────────────────────────────
MUTATIONEN = [
    ("Populations- statt Stichproben-Std", DC, "    var s = Math.sqrt(q / (nh - 1));", "    var s = Math.sqrt(q / nh);", "fall_sprung"),
    ("Rang ohne halbe Gleichstände", DC, "if (hist[i].rendite < R) kleiner++; else if (hist[i].rendite === R) gleich++;",
     "if (hist[i].rendite <= R) kleiner++;", "soll_gleichstand_halb"),
    ("Kein Lückencheck im Fenster", DC, "for (var i = e - F + 1; i <= e; i++) if (tage[i] - tage[i - 1] > T) return false;",
     "", "fall_luecke_aktuell"),
    ("Börse wie Krypto (T=1)", DC, "TOLERANZ: { krypto: 1, forex: 3, boerse: 7 }", "TOLERANZ: { krypto: 1, forex: 3, boerse: 1 }",
     "fall_klasse_boerse"),
    ("Alle Jahre statt 30", DC, "ANOMALIE: { FENSTER: 10, MAX_JAHRE: 30,", "ANOMALIE: { FENSTER: 10, MAX_JAHRE: 999,", "soll_30_jahre"),
    ("Mindestens 5 statt 10 Jahre", DC, "MIN_JAHRE: 10,", "MIN_JAHRE: 5,", "fall_zu_wenig_jahre"),
    ("29.02. ohne Begrenzung auf Monatsende", DC,
     "    return Math.round(Date.UTC(y, m - 1, Math.min(d, letzter)) / 86400000);",
     "    return Math.round(Date.UTC(y, m - 1, d) / 86400000);", "fall_schalttag"),
    ("as_of nicht zuerst angewandt", DC, "      if (asOf && d > asOf) continue;\n", "", "fall_praefix"),
    ("9 statt 10 Renditen", DC, "ANOMALIE: { FENSTER: 10,", "ANOMALIE: { FENSTER: 9,", "fall_sprung"),
    ("nicht berechenbar als normal", DC, "      var o = { status: 'nicht_berechenbar', grund_code: code,",
     "      var o = { status: 'normal', grund_code: code,", "fall_konstant"),
    ("Grenze |z| = 4/3 zur niedrigeren Stufe", DC, "(az >= K.AUFFAELLIG ? 'auffaellig' : 'normal')",
     "(az > K.AUFFAELLIG ? 'auffaellig' : 'normal')", "status_grenzen"),
    ("CSS nur über renderAnomalyInto", DC, "    if (typeof document !== 'undefined' && document.head) this._ensureAnomalyCss();\n", "",
     "css_von_der_darstellung"),
    ("Karte ohne Rang", DC, "        '<div class=\"kpi sa-anom-rang\"><div class=\"kpi-label\">' + esc(t('dc.anom_rang', 'Rang')) + '</div>' + rangHtml + '</div>' +\n",
     "", "html_sprung_html_karte"),
    ("Grund auf EN unübersetzt", DC, "(a && a.grund ? ': ' + esc(a.grund_code ? t('dc.anom_g_' + a.grund_code, a.grund) : a.grund) : '')",
     "(a && a.grund ? ': ' + esc(a.grund) : '')", "html_en_grund"),
    ("Fehlender Ticker still als Börse", DC, "    if (ticker == null || String(ticker).trim() === '') throw new Error('Ticker fehlt');\n",
     "", "fall_ohne_ticker"),
    ("Grün/Rot nach Richtung im Renderer", DC,
     "'Rendite 10 Handelstage')) + '</div><div class=\"kpi-value\">' + dez(a.rendite, 2)",
     "'Rendite 10 Handelstage')) + '</div><div class=\"kpi-value ' + (a.rendite >= 0 ? 'green' : 'red') + '\">' + dez(a.rendite, 2)",
     "html_sprung_html_karte"),
    ("Radar mit Seitenausschnitt statt eigener Historie", DC,
     "    if (r[0].date <= start || !(window.SA && SA.fetchAllPrices)) return",
     "    if (true || r[0].date <= start || !(window.SA && SA.fetchAllPrices)) return", "historie_regler_unabhaengig"),
    ("Nachladen ersetzt statt zusammenzuführen", DC, "      return rechne((voll || []).concat(rows || []));",
     "      return rechne(voll && voll.length >= r.length ? voll : rows);", "historie_cache_aelter"),
    ("Schalttag-Startdatum ungeprüft", DC,
     "    var start = new Date(this._zielTag(+letzte.substring(0, 4) - this.RADAR_HISTORIE_JAHRE, +letzte.substring(5, 7),\n"
     "                                       +letzte.substring(8, 10)) * 86400000).toISOString().substring(0, 10);",
     "    var start = (+letzte.substring(0, 4) - this.RADAR_HISTORIE_JAHRE) + letzte.substring(4);", "historie_schalttag"),
    ("Fehler-Rückruf ohne Kennung", "landing/pages/overnight.html",
     "        if (!SA.ladeKennung.aktuell(_lk)) return;   // veralteter Abruf: keine Fehlermeldung in die neue Ansicht\n",
     "", "abrufkennung"),
    ("Dekaden-Cachepfad ohne hideLoading", "landing/pages/dekadenzyklus.html",
     "        hideLoading();   // ein Rückwechsel A → B → A kommt hierher, während „Lade B …“ noch steht (Codex R6)\n",
     "", "dekaden_rueckwechsel_erfolg"),
    ("Rückwechsel ohne Entwertung", "landing/js/app.js",
     "      if (ticker && angezeigt && ticker === angezeigt && angefordert === angezeigt) return null;",
     "      if (ticker && angezeigt && ticker === angezeigt) return null;", "ladekennung_verhalten"),
    ("Dashboard mit eigener Karte", DASH, "      el.innerHTML = SA.decadeCompute.anomalieHtml(anom, currentTicker, 'karte');",
     "      el.innerHTML = '<div>' + anom.score + ' / 100</div>';", "dashboard_eine_rechnung"),
]
UNGUELTIG = [
    ("Anker trifft nicht", DC, "DIESER TEXT STEHT NICHT IN DER DATEI", "x", "fall_sprung"),
    ("Syntaxfehler (Probe muss abbrechen)", DC, "  anomalie: function(rows, ticker, opts) {", "  anomalie: function(rows, ticker, opts) {{", "fall_sprung"),
]


def _kopie(tmp: pathlib.Path):
    for rel in (DC, DASH, PROBE, "landing/js/app.js", "landing/pages/dekadenzyklus.html", "landing/i18n/de.json", "landing/i18n/en.json") + tuple(f"landing/pages/{s}.html" for s in SEITEN):
        (tmp / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(REPO / rel, tmp / rel)


def _bewerte(datei, alt, neu, soll):
    quelle = (REPO / datei).read_text(encoding="utf-8").replace("\r\n", "\n")
    if quelle.count(alt) != 1:
        return "ungueltig", "Anker trifft nicht"
    with tempfile.TemporaryDirectory() as t:
        tmp = pathlib.Path(t)
        _kopie(tmp)
        (tmp / datei).write_text(quelle.replace(alt, neu), encoding="utf-8")
        try:
            P = pruefen(tmp, None)
        except Exception as e:  # noqa: BLE001
            return "ungueltig", f"Probe abgebrochen: {str(e)[:120]}"
    rot = [k for k, v in P.items() if v is not True]
    if any(str(P[k]).startswith("[Aufbau]") for k in rot):
        return "ungueltig", f"Aufbau gerissen: {rot}"
    return ("gefangen" if soll in rot else "entwischt"), (f"auch: {[k for k in rot if k != soll]}" if soll in rot and len(rot) > 1 else str(rot))


def mutationen() -> int:
    ok = 0
    for name, datei, alt, neu, soll in MUTATIONEN:
        urteil, info = _bewerte(datei, alt, neu, soll)
        print(f"  {urteil.upper():9} {name} → {soll} {info if urteil != 'gefangen' else ''}")
        ok += urteil == "gefangen"
    u = 0
    for name, datei, alt, neu, soll in UNGUELTIG:
        urteil, info = _bewerte(datei, alt, neu, soll)
        print(f"  {'OK' if urteil == 'ungueltig' else 'FEHLER'}: als ungültig erkannt? {name} → {urteil} {info}")
        u += urteil == "ungueltig"
    print(f"{ok}/{len(MUTATIONEN)} Mutationen gefangen, {u}/{len(UNGUELTIG)} untaugliche richtig verworfen")
    return 0 if ok == len(MUTATIONEN) and u == len(UNGUELTIG) else 1


def main() -> int:
    if not shutil.which("node"):
        print("DURCHGEFALLEN: node fehlt — ohne node prüft dieser Wächter nichts")
        return 1
    if "--mutationen" in sys.argv:
        return mutationen()
    snap = None
    if "--snapshot" in sys.argv:
        snap = pathlib.Path(sys.argv[sys.argv.index("--snapshot") + 1])
    elif "--ohne-snapshot" not in sys.argv:
        print("UNGEPRÜFT: ohne --snapshot <ordner> fehlen die echten Reihen (bewusst: --ohne-snapshot)")
        return 1
    P = pruefen(REPO, snap)
    for k, v in P.items():
        if v is not True:
            print(f"  FEHLER {k}: {v}")
    n_ok = sum(v is True for v in P.values())
    print(f"verify_anomalie_radar: {n_ok}/{len(P)} Prüfungen bestanden")
    return 0 if n_ok == len(P) else 1


if __name__ == "__main__":
    sys.exit(main())
