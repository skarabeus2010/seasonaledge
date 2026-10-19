"""Wächter für /spot-vol-beta (landing/js/spot-vol-compute.js, Plan v3 mit Codex-Freigabe 2026-10-19).

Führt den echten Rechenkern in node aus (scripts/js/probe_spot_vol.js, echter Börsenkalender) und vergleicht mit
einer UNABHÄNGIGEN Referenz in numpy + shared.sitzungen + shared.realized_vol. Fälle:
  * Achse: in einer Reihe fehlende Sitzung, in beiden fehlende Sitzung, Phantomzeile am Feiertag, log_return null,
    Kursbasis-Wechsel (Close ×3 bei unverändertem log_return), laufende Sitzung nach E wird verworfen
  * Rolling-60 (erster Wert erst mit 60 gültigen Renditen), expandierende Stress-Schwelle (< 252 Vorwerte → keine)
  * Ereignisse (Eintritt nur nach bekanntem „falsch“, Sperre ohne Nachholen) und Zeitraumunabhängigkeit
  * Forward-Renditen mit eigenem n, Buckets „nächster Tag“, VRP/RV21 = shared.realized_vol.rv_reihe_aus_returns
  * Gesamt-OLS, Badge-Quantile, Residuum des letzten Tages (Linie ohne diesen Tag, Rang strikt)
  * Frische: letzte abgeschlossene Sitzung (15:00/16:45 New York, Halbtag 13:00 + 30 min, Wochenende), beidseitig
    veraltete Reihen, unter drei Zeitzonen des Prozesses
  * Degeneriert: N < 3, konstantes x bzw. y, perfekte Linearität (s = 0 → z nicht bestimmbar)
Mutationstest (--mutation): baut bekannte Fehler in eine Kopie von landing/js ein und verlangt jeweils Rot.

Aufruf: py -3.14 scripts/verify_spot_vol_beta.py [--mutation]
"""
from __future__ import annotations

import json
import math
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import numpy as np

WURZEL = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL))
from shared import sitzungen as SZ            # noqa: E402
from shared.realized_vol import rv_reihe_aus_returns   # noqa: E402

PROBE = WURZEL / "scripts" / "js" / "probe_spot_vol.js"
NY = ZoneInfo("America/New_York")
TOL = 1e-9


# ── Referenz ────────────────────────────────────────────────────────────────────────────────────────────────────
def ref_E(jetzt_ms: int) -> str:
    t = datetime.fromtimestamp(jetzt_ms / 1000, tz=timezone.utc).astimezone(NY)
    d = t.date()
    if SZ.offen(d, "NYSE"):
        info = SZ.sitzung_info(d, "NYSE")
        schluss = info["schlusszeit"] if info.get("halbtag") is True and info.get("schlusszeit") else "16:00"
        h, m = map(int, schluss.split(":"))
        if t.hour * 60 + t.minute >= h * 60 + m + 30:
            return d.isoformat()
    return SZ.vorherige(d, "NYSE", einschliesslich=False).isoformat()


def ref_achse(spot, vol, E):
    def index(zeilen):
        z = sorted((r for r in zeilen if r["date"] <= E), key=lambda r: r["date"])
        idx = {}
        for r in z:
            if r["date"] in idx:
                continue
            c = r.get("close")
            lr = r.get("log_return")
            idx[r["date"]] = (c if c is not None and c > 0 else None, lr if lr is not None and math.isfinite(lr) else None)
        return idx, (min(idx) if idx else None), (max(idx) if idx else None)

    def rendite(idx, s, vs):
        # Sitzungsrendite = Summe der log_return aller eigenen Zeilen in (vs, s]; beide Endzeilen Pflicht
        if s not in idx or vs not in idx:
            return None
        teile = [idx[d][1] for d in idx if vs < d <= s]
        return None if any(x is None for x in teile) else float(sum(teile))
    si, s0, s1 = index(spot)
    vi, v0, v1 = index(vol)
    start = max(s0, v0)
    sess = [d.isoformat() for d in SZ.sitzungen("NYSE", start, E)]
    vor0 = SZ.vorherige(sess[0], "NYSE", einschliesslich=False).isoformat()
    sp, vo, spc, voc = [], [], [], []
    for i, d in enumerate(sess):
        vs = vor0 if i == 0 else sess[i - 1]
        a, b = si.get(d), vi.get(d)
        spc.append(a[0] if a else None)
        voc.append(b[0] if b else None)
        sp.append(rendite(si, d, vs))
        vo.append(rendite(vi, d, vs))
    return dict(E=E, spotEnde=s1, volEnde=v1, sitzungen=sess, spLR=sp, voLR=vo, spClose=spc, voClose=voc)


def ref_ols(xs, ys):
    xs, ys = np.asarray(xs, float), np.asarray(ys, float)
    if len(xs) < 3 or np.ptp(xs) == 0 or np.ptp(ys) == 0:
        return None
    beta, alpha = np.polyfit(xs, ys, 1)
    corr = float(np.corrcoef(xs, ys)[0, 1])
    res = ys - (alpha + beta * xs)
    return dict(beta=float(beta), alpha=float(alpha), corr=corr, r2=corr * corr,
                s=float(np.sqrt((res ** 2).sum() / (len(xs) - 2))), n=len(xs))


def ref_rolling(x, y, w=60):
    out = [None] * len(x)
    for i in range(w - 1, len(x)):
        fx, fy = x[i - w + 1:i + 1], y[i - w + 1:i + 1]
        if any(v is None for v in fx) or any(v is None for v in fy):
            continue
        fx, fy = np.asarray(fx), np.asarray(fy)
        if np.var(fx) > 0:
            out[i] = float(np.cov(fx, fy, bias=True)[0, 1] / np.var(fx))
    return out


def ref_expandierend(werte, p, mind=252):
    out, vor = [], []
    for v in werte:
        out.append(float(np.quantile(vor, p)) if len(vor) >= mind else None)
        if v is not None:
            vor.append(v)
    return out


def ref_eintritte(c, sperre=10):
    ev, letzt = [], None
    for i in range(1, len(c)):
        if c[i] is True and c[i - 1] is False and (letzt is None or i - letzt >= sperre):
            ev.append(i)
            letzt = i
    return ev


def ref_forward(lr, i, h):
    if i + h >= len(lr):
        return None
    f = lr[i + 1:i + h + 1]
    return None if any(v is None for v in f) else float(np.expm1(sum(f)) * 100)


def ref_auswertung(spot, vol, opts):
    E = ref_E(opts["jetztMs"])
    a = ref_achse(spot, vol, E)
    n = len(a["sitzungen"])
    lg = opts["log"]
    conv = (lambda r: r) if lg else (lambda r: math.expm1(r))
    x = [None if r is None else conv(r) for r in a["spLR"]]
    y = [None if r is None else conv(r) for r in a["voLR"]]
    xe = [None if r is None else math.expm1(r) for r in a["spLR"]]
    ye = [None if r is None else math.expm1(r) for r in a["voLR"]]
    roll = ref_rolling(x, y)
    sq = ref_expandierend(roll, opts["stressP"])
    j = opts["jahre"]
    if j == "max":
        start = None
    else:
        jj, md = int(E[:4]) - int(j), E[5:]
        start = f"{jj}-{'02-28' if md == '02-29' else md}"
    anz = [i for i in range(n) if start is None or a["sitzungen"][i] >= start]
    im = set(anz)
    ok = [i for i in anz if x[i] is not None and y[i] is not None]
    fit = ref_ols([x[i] for i in ok], [y[i] for i in ok])

    def ereig(c):
        return [i for i in ref_eintritte(c) if i in im]
    c_spike = [None if v is None else v >= opts["spike"] for v in a["voClose"]]
    c_low = [None if v is None else v <= opts["low"] for v in a["voClose"]]
    c_str = [None if r is None or q is None else r <= q for r, q in zip(roll, sq)]
    ev = {k: ereig(c) for k, c in (("spike", c_spike), ("low", c_low), ("stress", c_str))}

    iE = n - 1 if n and a["sitzungen"][-1] == E else -1
    rw = sorted(roll[i] for i in anz if roll[i] is not None)
    akt = roll[iE] if iE >= 0 else None
    badge = "nicht_bestimmbar"
    q20 = q80 = None
    if len(rw) >= 60 and akt is not None:
        q20, q80 = float(np.quantile(rw, .2)), float(np.quantile(rw, .8))
        if q20 != q80:
            badge = "positiv" if akt > 0 else "staerker" if akt <= q20 else "schwaecher" if akt >= q80 else "ueblich"

    res = None
    if iE >= 0 and xe[iE] is not None and ye[iE] is not None:
        tr = [i for i in anz if i != iE and xe[i] is not None and ye[i] is not None]
        f = ref_ols([xe[i] for i in tr], [ye[i] for i in tr])
        if f:
            rE = ye[iE] - (f["alpha"] + f["beta"] * xe[iE])
            resid = [ye[i] - (f["alpha"] + f["beta"] * xe[i]) for i in tr]
            kg = None
            if xe[iE] < 0 and ye[iE] > 0:
                kg = sum(1 for i in tr if xe[iE] < xe[i] < 0 and ye[i] > ye[iE])
            res = dict(residuum=rE * 100, z=(rE / f["s"] if f["s"] > 0 else None), k=sum(1 for r in resid if r > rE),
                       N=len(tr), k_grafik=kg, erwartet=(f["alpha"] + f["beta"] * xe[iE]) * 100)

    vols = sorted(a["voClose"][i] for i in anz if a["voClose"][i] is not None)
    buckets = None
    if len(vols) >= 50:
        th = [float(np.quantile(vols, q)) for q in (.2, .4, .6, .8)]
        fw = {h: [[] for _ in range(5)] for h in (1, 5, 20, 60)}
        tage = [0] * 5
        for i in anz:
            v = a["voClose"][i]
            if v is None:
                continue
            b = int(np.searchsorted(th, v, side="right"))
            tage[b] += 1
            for h in fw:
                fw[h][b].append(ref_forward(a["spLR"], i, h))
        buckets = dict(grenzen=th, tage=tage, fw={h: [[w for w in L if w is not None] for L in fw[h]] for h in fw})

    # rv_reihe_aus_returns liefert Dezimal, auf 4 Stellen gerundet → Toleranz 0,005 Vol-Punkte
    rvmap = rv_reihe_aus_returns(a["sitzungen"], a["spLR"], 21)
    vrp = [(a["sitzungen"][i], a["voClose"][i] - 100 * rvmap[a["sitzungen"][i]]) for i in anz
           if a["sitzungen"][i] in rvmap and a["voClose"][i] is not None]
    letzter = next((a["sitzungen"][i] for i in range(n - 1, -1, -1) if x[i] is not None and y[i] is not None), None)
    return dict(achse=a, anzeige=anz, rolling=roll, stress=sq, ols=fit, ev=ev, badge=badge, q20=q20, q80=q80,
                aktuell=akt, res=res, buckets=buckets, vrp=vrp, letzter=letzter)


# ── Testdaten ──────────────────────────────────────────────────────────────────────────────────────────────────
def daten(ende="2026-10-16", start="2012-01-03", seed=7):
    rng = np.random.default_rng(seed)
    sess = [d.isoformat() for d in SZ.sitzungen("NYSE", start, ende)]
    spot, vol = [], []
    cs, lv = 100.0, math.log(15.0)
    for i, d in enumerate(sess):
        r = float(rng.normal(0.0004, 0.011))
        dv = -4.5 * r + float(rng.normal(0, 0.045)) + 0.03 * (math.log(16) - lv)
        cs *= math.exp(r)
        lv += dv
        spot.append({"date": d, "close": cs, "log_return": r if i else None})
        vol.append({"date": d, "close": math.exp(lv), "log_return": dv if i else None})
    # letzter Tag wie am 16.10.2026: Spot -1,1 %, Vol +21 % (sonst bleibt die Zaehlung im Stil der Grafik ungeprueft)
    spot[-1]["log_return"], vol[-1]["log_return"] = math.log(1 - 0.011), math.log(1.12)
    # Gleichstand im Spot mit groesserem Vol-Anstieg: zaehlt nur bei strikter Grenze NICHT (x_heute < x < 0)
    k = sess.index("2025-03-04")
    spot[k]["log_return"], vol[k]["log_return"] = math.log(1 - 0.011), math.log(1.30)
    # exakter Gleichstand im Residuum: ein frueherer Tag mit denselben Renditen wie der letzte (Rang strikt)
    k = sess.index("2024-07-09")
    spot[k]["log_return"], vol[k]["log_return"] = spot[-1]["log_return"], vol[-1]["log_return"]
    # Sperre ueber die Zeitraumgrenze (3 Jahre ab 2023-10-16): Eintritt 5 Sitzungen davor, zweiter 3 danach
    g = sess.index("2023-10-16")
    for off, v in ((-6, 20.0), (-5, 31.0), (-4, 20.0), (2, 20.0), (3, 31.0), (4, 20.0)):
        vol[g + off]["close"] = v
    return sess, spot, vol


def manipulieren(sess, spot, vol):
    """Lücken, Phantomzeile, null-Rendite, Basiswechsel, laufende Sitzung. Gibt die betroffenen Daten zurück."""
    def pos(d):
        return sess.index(d)
    phantom_soll = next(r for r in spot if r["date"] > "2020-12-25")["log_return"]
    nur_vol = "2019-03-12"
    beide = "2021-06-15"
    null_vol = "2023-02-08"
    basis = "2024-05-01"
    # (1) in Vol fehlt eine Sitzung: Folgezeile behält ihren (über die Lücke gerechneten) log_return
    i = pos(nur_vol)
    vol[i + 1]["log_return"] += vol[i]["log_return"]
    del vol[i]
    # (2) in beiden fehlt eine Sitzung
    for reihe in (spot, vol):
        k = next(j for j, r in enumerate(reihe) if r["date"] == beide)
        reihe[k + 1]["log_return"] += reihe[k]["log_return"]
        del reihe[k]
    # (3) Phantomzeile am Feiertag (Weihnachten 2020) in Spot mit eigener Rendite +0,4 %; die Folgezeile bezieht
    #     sich auf die Phantomzeile (−0,4 % weniger). Die Sitzungsrendite muss trotzdem die echte sein.
    k = next(j for j, r in enumerate(spot) if r["date"] > "2020-12-25")
    spot.insert(k, {"date": "2020-12-25", "close": spot[k - 1]["close"] * math.exp(0.004), "log_return": 0.004})
    spot[k + 1]["log_return"] -= 0.004
    # (4) null-Rendite in Vol
    next(r for r in vol if r["date"] == null_vol)["log_return"] = None
    # (5) Basiswechsel: ab hier Close ×3, log_return unverändert
    for r in spot:
        if r["date"] >= basis:
            r["close"] *= 3
    # (6) laufende Sitzung nach dem letzten Datenstand
    spot.append({"date": "2026-10-19", "close": spot[-1]["close"] * 0.9, "log_return": math.log(0.9)})
    vol.append({"date": "2026-10-19", "close": vol[-1]["close"] * 1.5, "log_return": math.log(1.5)})
    return dict(nur_vol=nur_vol, beide=beide, null_vol=null_vol, basis=basis, phantom_soll=phantom_soll)


def ms(iso):
    return int(datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp() * 1000)


# ── Vergleich ──────────────────────────────────────────────────────────────────────────────────────────────────
def gleich(a, b, tol=TOL):
    if a is None or b is None:
        return a is None and b is None
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(a - b) <= tol * max(1.0, abs(a), abs(b))
    return a == b


def listen_gleich(a, b, tol=TOL):
    return len(a) == len(b) and all(gleich(u, v, tol) for u, v in zip(a, b))


def probe(eingabe, wurzel, tz=None):
    env = dict(os.environ)
    if tz:
        env["TZ"] = tz
    r = subprocess.run(["node", str(PROBE), str(wurzel)], input=json.dumps(eingabe), capture_output=True, text=True,
                       encoding="utf-8", timeout=300, env=env)
    if r.returncode != 0:
        raise RuntimeError("probe Exit %d: %s" % (r.returncode, r.stderr[-400:]))
    return json.loads(r.stdout)


def pruefen(wurzel: pathlib.Path, leise=False, render=False) -> bool:
    ergebnisse, ok = [], True

    def pr(name, bed, detail=""):
        nonlocal ok
        ergebnisse.append(("ok  " if bed else "FEHL") + " [%s] %s" % (name, detail))
        ok = ok and bool(bed)

    sess, spot, vol = daten()
    marken = manipulieren(sess, spot, vol)
    jetzt = ms("2026-10-19T19:00:00Z")   # Montag 15:00 New York → E = Freitag 16.10.
    faelle = {
        "max_einfach": dict(jahre="max", log=False),
        "5j_einfach": dict(jahre="5", log=False),
        "3j_log": dict(jahre="3", log=True),
        "3j_einfach": dict(jahre="3", log=False),
    }
    gem = dict(jetztMs=jetzt, boerse="NYSE", spike=30, low=13, stressP=0.1)
    ausw = [dict(name=k, spot=spot, vol=vol, opts=dict(gem, **v)) for k, v in faelle.items()]
    # beidseitig veraltet: Daten enden am 14.10., jetzt Freitag 16.10. 21:00 UTC (17:00 New York)
    sp_alt = [r for r in spot if r["date"] <= "2026-10-14"]
    vo_alt = [r for r in vol if r["date"] <= "2026-10-14"]
    sp_k = [dict(r) for r in spot if "2025-01-01" <= r["date"] <= "2025-06-30"]
    for r in sp_k:
        r["log_return"] = 0.001
    vo_k = [r for r in vol if "2025-01-01" <= r["date"] <= "2025-06-30"]
    ausw.append(dict(name="konstant", spot=sp_k, vol=vo_k, opts=dict(gem, jahre="max", log=False, jetztMs=ms("2025-07-01T21:00:00Z"))))
    ausw.append(dict(name="veraltet", spot=sp_alt, vol=vo_alt, opts=dict(gem, jahre="5", log=False, jetztMs=ms("2026-10-16T21:00:00Z"))))
    frische_zeiten = ["2026-10-19T19:00:00Z", "2026-10-19T20:29:00Z", "2026-10-19T20:31:00Z", "2026-10-18T15:00:00Z",
                      "2026-11-27T18:29:00Z", "2026-11-27T18:31:00Z", "2026-07-03T21:00:00Z", "2026-01-02T04:00:00Z"]
    eintritte = [
        [[False] + [True] * 25, 10],
        [[None, True, True, False, True], 10],
        [[False, True, False, True, False, False, True], 3],
        [[False, True, False, False, True, True, False, False, False, False, False, False, True], 10],
    ]
    ols = [[[1, 1, 1, 1], [1, 2, 3, 4]], [[1, 2], [3, 4]], [[1, 2, 3, 4], [5, 5, 5, 5]], [[1, 2, 3, 4], [3, 5, 7, 9]],
           [[0.1, 0.1, 0.1], [0.3, 0.1, 0.7]], [[0.3, 0.1, 0.7], [0.1, 0.1, 0.1]]]
    eingabe = dict(auswertungen=ausw, frische=[ms(z) for z in frische_zeiten], eintritte=eintritte, ols=ols,
                   zeitraum=[["2026-10-16", "5"], ["2028-02-29", "3"], ["2026-10-16", "max"]],
                   quantil=[[[1, 2, 3, 4], 0.1], [[5], 0.5], [[2, 2, 2, 7], 0.8]])

    for tz in ("Europe/Berlin", "America/Los_Angeles", "Asia/Tokyo"):
        try:
            try:
                p = probe(eingabe, wurzel, tz)
            except Exception as e:   # noqa: BLE001
                pr("probe %s" % tz, False, str(e)[:300])
                continue
            pr("[%s] Zonenwechsel wirksam" % tz, p["tz_offset_min"] == {"Europe/Berlin": -60, "America/Los_Angeles": 480, "Asia/Tokyo": -540}[tz],
               "Offset %s" % p["tz_offset_min"])
            soll = [ref_E(ms(z)) for z in frische_zeiten]
            pr("[%s] letzte abgeschlossene Sitzung" % tz, p["frische"] == soll, "%s / %s" % (p["frische"], soll))
            pr("[%s] Zeitraumstart" % tz, p["zeitraum"] == ["2021-10-16", "2025-02-28", None], str(p["zeitraum"]))
            if tz != "Europe/Berlin":
                continue
            pr("Eintritte", p["eintritte"] == [ref_eintritte(c, s) for c, s in eintritte],
               "%s / %s" % (p["eintritte"], [ref_eintritte(c, s) for c, s in eintritte]))
            pr("Eintritte: 25 wahre Tage = 1 Ereignis", p["eintritte"][0] == [1])
            pr("Eintritte: unbekannt → wahr ist kein Eintritt", p["eintritte"][1] == [4])
            o = p["ols"]
            pr("OLS konstantes x nicht bestimmbar", o[0]["bestimmbar"] is False)
            pr("OLS N < 3 nicht bestimmbar", o[1]["bestimmbar"] is False)
            pr("OLS konstantes y nicht bestimmbar", o[2]["bestimmbar"] is False)
            pr("OLS perfekt linear: β = 2, s = 0", o[3]["bestimmbar"] and gleich(o[3]["beta"], 2.0) and o[3]["s"] == 0, str(o[3]))
            pr("OLS konstante Dezimalwerte x = 0,1 nicht bestimmbar", o[4]["bestimmbar"] is False, str(o[4]))
            pr("OLS konstante Dezimalwerte y = 0,1 nicht bestimmbar", o[5]["bestimmbar"] is False, str(o[5]))
            pr("Quantil wie numpy", listen_gleich(p["quantil"], [float(np.quantile([1, 2, 3, 4], .1)), None,
                                                                  float(np.quantile([2, 2, 2, 7], .8))]), str(p["quantil"]))

            for name in list(faelle) + ["veraltet"]:
                r = p["faelle"][name]
                if "fehler" in r:
                    pr(name + " läuft", False, r["fehler"])
                    continue
                fo = next(x for x in ausw if x["name"] == name)
                ref = ref_auswertung(fo["spot"], fo["vol"], fo["opts"])
                a, ra = r["achse"], ref["achse"]
                pr(name + " E", a["E"] == ra["E"], "%s / %s" % (a["E"], ra["E"]))
                pr(name + " Reihenenden", (a["spotEnde"], a["volEnde"]) == (ra["spotEnde"], ra["volEnde"]),
                   "%s %s / %s %s" % (a["spotEnde"], a["volEnde"], ra["spotEnde"], ra["volEnde"]))
                pr(name + " Sitzungsachse", a["sitzungen"] == ra["sitzungen"], "%d / %d" % (len(a["sitzungen"]), len(ra["sitzungen"])))
                pr(name + " Spot-Renditen", listen_gleich(a["spLR"], ra["spLR"]))
                pr(name + " Vol-Renditen", listen_gleich(a["voLR"], ra["voLR"]))
                pr(name + " Anzeigezeitraum", r["anzeige"] == ref["anzeige"], "%d / %d" % (len(r["anzeige"]), len(ref["anzeige"])))
                pr(name + " Rolling-60", listen_gleich(r["rolling"], ref["rolling"], 1e-8))
                pr(name + " Stress-Schwelle expandierend", listen_gleich(r["stressSchwelle"], ref["stress"], 1e-8))
                fo_ = r["ols"]
                pr(name + " Gesamt-OLS", (fo_["bestimmbar"] and ref["ols"] is not None
                                           and all(gleich(fo_[k], ref["ols"][k], 1e-8) for k in ("beta", "alpha", "corr", "r2", "s", "n"))),
                   "β %s / %s" % (fo_.get("beta"), ref["ols"] and ref["ols"]["beta"]))
                for k in ("spike", "low", "stress"):
                    jd = [e["datum"] for e in r["ereignisse"][k]]
                    rd = [ra["sitzungen"][i] for i in ref["ev"][k]]
                    pr("%s Ereignisse %s" % (name, k), jd == rd, "%d / %d" % (len(jd), len(rd)))
                    fw = [e["fwd_20"] for e in r["ereignisse"][k]]
                    rfw = [ref_forward(ra["spLR"], i, 20) for i in ref["ev"][k]]
                    pr("%s Forward 20 %s" % (name, k), listen_gleich(fw, rfw, 1e-8))
                st = r["ereignisse"]["stats_spike"]
                rv60 = [v for v in (ref_forward(ra["spLR"], i, 60) for i in ref["ev"]["spike"]) if v is not None]
                pr(name + " Forward-n je Horizont", (st["60"] is None and not rv60) or (st["60"] and st["60"]["n"] == len(rv60)),
                   "%s / %d" % (st["60"] and st["60"]["n"], len(rv60)))
                b = r["badge"]
                pr(name + " Badge", b["regime"] == ref["badge"] and gleich(b["q20"], ref["q20"], 1e-8) and gleich(b["q80"], ref["q80"], 1e-8),
                   "%s / %s" % (b["regime"], ref["badge"]))
                q, rq = r["residuum"], ref["res"]
                if rq is None:
                    pr(name + " Residuum nicht bestimmbar", q["bestimmbar"] is False, str(q))
                else:
                    pr(name + " Residuum", q["bestimmbar"] and all(gleich(q[k], rq[k], 1e-8) for k in ("residuum", "z", "erwartet"))
                       and (q["k"], q["N"], q["k_grafik"]) == (rq["k"], rq["N"], rq["k_grafik"]),
                       "k %s/%s N %s/%s kg %s/%s" % (q.get("k"), rq["k"], q.get("N"), rq["N"], q.get("k_grafik"), rq["k_grafik"]))
                bk, rb = r["buckets"], ref["buckets"]
                if rb is None:
                    pr(name + " Buckets leer", bk is None)
                else:
                    pr(name + " Bucket-Grenzen", listen_gleich(bk["grenzen"], rb["grenzen"], 1e-10))
                    pr(name + " Bucket-Tage", [e["tage"] for e in bk["eimer"]] == rb["tage"], "%s / %s" % ([e["tage"] for e in bk["eimer"]], rb["tage"]))
                    for h in (1, 5, 20, 60):
                        def st_ok(s, L):
                            if not L:
                                return s is None
                            v = sorted(L)
                            return (s is not None and s["n"] == len(v) and gleich(s["avg"], float(np.mean(v)), 1e-8)
                                    and gleich(s["median"], float(np.median(v)), 1e-8)
                                    and gleich(s["win_rate"], 100.0 * sum(1 for w in v if w > 0) / len(v), 1e-8)
                                    and gleich(s["max"], v[-1], 1e-8) and gleich(s["min"], v[0], 1e-8))
                        pr("%s Bucket +%d (Ø, Median, Trefferquote, Extreme, n)" % (name, h),
                           all(st_ok(e["f%d" % h], L) for e, L in zip(bk["eimer"], rb["fw"][h])))
                jv = [(v["datum"], v["vrp"]) for v in r["vrp"]]
                pr(name + " VRP = Vol − rv_reihe_aus_returns", len(jv) == len(ref["vrp"]) and all(
                    u[0] == w[0] and abs(u[1] - w[1]) <= 0.0051 for u, w in zip(jv, ref["vrp"])), "%d / %d" % (len(jv), len(ref["vrp"])))
                pr(name + " letzter Paartag", r["aktuell"]["letzterPaartag"] == ref["letzter"],
                   "%s / %s" % (r["aktuell"]["letzterPaartag"], ref["letzter"]))

            # Gezielte Aussagen zu den Manipulationen (zusätzlich zur Referenz)
            a = p["faelle"]["max_einfach"]["achse"]
            S = a["sitzungen"]
            def nach(d):
                return S.index(next(s for s in S if s > d))
            pr("Lücke nur Vol: Folgesitzung unbekannt", a["voLR"][nach(marken["nur_vol"])] is None and marken["nur_vol"] in S)
            pr("Lücke in beiden: Sitzung auf der Achse, Rendite unbekannt",
               marken["beide"] in S and a["spLR"][S.index(marken["beide"])] is None and a["spLR"][nach(marken["beide"])] is None)
            pr("Phantomzeile: Feiertag nicht auf der Achse, Folgesitzung = echte Sitzungsrendite",
               "2020-12-25" not in S and gleich(a["spLR"][nach("2020-12-25")], marken["phantom_soll"]),
               "%s / %s" % (a["spLR"][nach("2020-12-25")], marken["phantom_soll"]))
            i_b = S.index(marken["basis"])
            pr("Basiswechsel ohne Wirkung auf Renditen", a["spLR"][i_b] is not None and abs(a["spLR"][i_b]) < 0.2)
            pr("laufende Sitzung verworfen", S[-1] == "2026-10-16" and a["spotEnde"] == "2026-10-16")
            m = p["faelle"]["max_einfach"]["rolling"]
            erst = next(i for i, v in enumerate(m) if v is not None)
            pr("erster Rolling-Wert erst mit 60 Renditen", erst == 60, "Index %d" % erst)
            ss = p["faelle"]["max_einfach"]["stressSchwelle"]
            pr("Stress-Schwelle erst ab 252 Vorwerten", sum(1 for v in m[:next(i for i, v in enumerate(ss) if v is not None)] if v is not None) == 252)
            d3 = {k: [e["datum"] for e in p["faelle"]["3j_einfach"]["ereignisse"][k]] for k in ("spike", "low", "stress")}
            st3 = p["faelle"]["3j_einfach"]["achse"]["sitzungen"][p["faelle"]["3j_einfach"]["anzeige"][0]]
            dm = {k: [e["datum"] for e in p["faelle"]["max_einfach"]["ereignisse"][k] if e["datum"] >= st3] for k in d3}
            pr("Zeitraumwechsel ändert Ereignisse nicht", d3 == dm and sum(map(len, d3.values())) > 0,
               "%s" % {k: len(v) for k, v in d3.items()})
            s3 = [e["datum"] for e in p["faelle"]["3j_einfach"]["ereignisse"]["spike"]]
            g3 = sess.index("2023-10-16")
            pr("Sperre wirkt über die Zeitraumgrenze", sess[g3 + 3] not in s3 and sess[g3 - 5] in
               [e["datum"] for e in p["faelle"]["max_einfach"]["ereignisse"]["spike"]], str(s3))
            kr = p["faelle"]["konstant"]
            pr("konstante Dezimal-Spotrenditen: kein Rolling-Beta, OLS nicht bestimmbar",
               "fehler" not in kr and all(x is None for x in kr["rolling"]) and kr["ols"]["bestimmbar"] is False,
               str(kr.get("fehler") or kr["ols"]))
            v = p["faelle"]["veraltet"]
            pr("beidseitig veraltet: erkannt", v["achse"]["E"] == "2026-10-16" and v["aktuell"]["letzterPaartag"] == "2026-10-14"
               and v["residuum"]["bestimmbar"] is False, "%s %s" % (v["achse"]["E"], v["aktuell"]["letzterPaartag"]))
        except Exception as e:   # noqa: BLE001 — eine abstürzende Auswertung ist rot, nicht grün und nicht „gefangen"
            pr("[%s] Auswertung ohne Absturz" % tz, False, "%s: %s" % (type(e).__name__, e))

    if render:
        for fall in ("normal", "kurz"):
            r = subprocess.run(["node", str(WURZEL / "scripts" / "js" / "probe_seiten_kurse.js"), str(wurzel), "spot-vol-beta", fall],
                               capture_output=True, text=True, encoding="utf-8", timeout=300)
            try:
                d = json.loads(r.stdout)
            except ValueError:
                pr("Seite %s läuft" % fall, False, (r.stderr or r.stdout)[-300:])
                continue
            pr("Seite %s: Ende, Ruhe, keine Seitenfehler" % fall, d.get("ende") is True and d.get("ruhig") and not d.get("seitenfehler")
               and not d.get("absturz"), " | ".join(d.get("seitenfehler") or [])[:300] + (d.get("absturz") or ""))
            pr("Seite %s: fordert log_return und volle Historie an" % fall,
               bool(d["kursanfragen"]) and all("log_return" in u and "date=gte.1990-01-01" in u for u in d["kursanfragen"]),
               str(d["kursanfragen"][:1]))
            inhalt = d.get("inhalt", "")
            pr("Seite %s: kein Fehlerbanner" % fall, "Fehler beim Laden" not in inhalt, inhalt[inhalt.find("Fehler beim Laden"):][:160])
            soll = ["Letzter Handelstag gegen die Regression", "Mittelwert"] + (["Keine Ereignisse"] if fall == "kurz" else ["Rolling-60-Beta am"])
            pr("Seite %s: Bausteine" % fall, all(s in inhalt for s in soll), str([s for s in soll if s not in inhalt]))
            if fall == "kurz":
                pr("Seite kurz: Buckets melden zu wenige Tage, kein NaN/undefined", "Zu wenige Tage im Zeitraum" in inhalt
                   and "NaN" not in inhalt and "undefined" not in inhalt)

    if not leise:
        for e in ergebnisse:
            sys.stdout.write(e + "\n")
    n = sum(1 for e in ergebnisse if e.startswith(("ok", "FEHL")))
    sys.stdout.write("verify_spot_vol_beta: %s (%d Prüfungen)\n" % ("BESTANDEN" if ok else "DURCHGEFALLEN", n))
    return ok


MUTATIONEN = [
    ("Lücke zusammengezogen", "if (j == null || k == null || k >= j) return null;", "if (j == null) return null; if (k == null) k = j - 1;"),
    ("Phantomrendite ignoriert", "for (var m = k + 1; m <= j; m++)", "for (var m = j; m <= j; m++)"),
    ("Rolling mit 59", "if (i - luecke < w) continue;", "if (i - luecke < w - 1) continue;"),
    ("Stress ohne Mindestzahl", "mind = mind || STRESS_MIN;", "mind = 1;"),
    ("Stress mit Look-ahead", "        sortiert.splice(lo, 0, v);\n      }\n",
     "        sortiert.splice(lo, 0, v);\n      }\n      if (out[i] != null) out[i] = quantil(sortiert, p);\n"),
    ("unbekannt gilt als falsch", "c[i - 1] !== false", "c[i - 1] === true"),
    ("Sperre fehlt", "if (i - letztes < sperre) continue;", ""),
    ("RV mit ÷N", "Math.sqrt(252 / (n - 1) * q)", "Math.sqrt(252 / n * q)"),
    ("Rang nicht strikt", "> rE) k++", ">= rE) k++"),
    ("Training mit heutigem Tag", "anz.filter(function (i) { return i !== iE; })", "anz"),
    ("Frische ohne 30 min", "+ (+sm[1]) + 30;", "+ (+sm[1]) + 0;"),
    ("Börse ignoriert", "Kal.sitzungen(start, E, boerse)", "Kal.sitzungen(start, E, 'XETRA')"),
    ("Halbtag ignoriert", "info.halbtag === true && info.schlusszeit ? info.schlusszeit : '16:00'", "'16:00'"),
    ("laufende Sitzung zählt", "z && typeof z.date === 'string' && z.date <= E", "z && typeof z.date === 'string'"),
    ("Forward über Lücke", "if (spLR[k] == null) return null; s += spLR[k];", "if (spLR[k] == null) continue; s += spLR[k];"),
    ("Bucket gleicher Tag", "bk[b].f1.push(forward(a.spLR, i, 1));", "bk[b].f1.push(forward(a.spLR, i - 1, 1));"),
    ("Bucket +5 verschoben", "bk[b].f5.push(forward(a.spLR, i, 5));", "bk[b].f5.push(forward(a.spLR, i - 1, 5));"),
    ("Bucket +60 als +20", "bk[b].f60.push(forward(a.spLR, i, 60));", "bk[b].f60.push(forward(a.spLR, i, 20));"),
    ("Median falsch", "(v[v.length / 2 - 1] + v[v.length / 2]) / 2", "v[v.length / 2]"),
    ("OLS Konstanz nur über sxx", "if (x0 === x1 || y0 === y1) return", "if (false) return"),
    ("Rolling Konstanz nur über sxx", "if (x0 === x1) continue;", ""),
    ("Ereignisse auf Zeitraum begrenzt", "var ix = eintritte(c, SPERRE).filter(imZeitraum);",
     "var ix = eintritte(c.map(function (v, i) { return imZeitraum(i) ? v : null; }), SPERRE);"),
    ("Residuum-Grafikzählung inklusiv", "tr.xs[t] > xE && tr.xs[t] < 0 && tr.ys[t] > yE", "tr.xs[t] >= xE && tr.xs[t] < 0 && tr.ys[t] > yE"),
]


def mutation() -> bool:
    quelle = (WURZEL / "landing" / "js" / "spot-vol-compute.js").read_text(encoding="utf-8")
    ok_alle = True
    for name, alt, neu in MUTATIONEN:
        if quelle.count(alt) != 1:
            sys.stdout.write("UNGÜLTIG [%s] Anker %d-mal\n" % (name, quelle.count(alt)))
            ok_alle = False
            continue
        with tempfile.TemporaryDirectory() as tmp:
            w = pathlib.Path(tmp) / "landing"
            (w / "js").mkdir(parents=True)
            shutil.copyfile(WURZEL / "landing" / "js" / "boersenkalender.js", w / "js" / "boersenkalender.js")
            (w / "js" / "spot-vol-compute.js").write_text(quelle.replace(alt, neu), encoding="utf-8")
            try:
                gruen = pruefen(w, leise=True)
            except Exception as e:   # noqa: BLE001 — ein Absturz des Wächters zählt nicht als gefangen
                sys.stdout.write("ABSTURZ [%s] %s\n" % (name, e))
                ok_alle = False
                continue
        sys.stdout.write(("gefangen " if not gruen else "ENTWISCHT") + " [%s]\n" % name)
        ok_alle = ok_alle and not gruen
    return ok_alle


if __name__ == "__main__":
    if "--mutation" in sys.argv:
        g = mutation()
        sys.stdout.write("Mutationstest: %s (%d Mutationen)\n" % ("BESTANDEN" if g else "DURCHGEFALLEN", len(MUTATIONEN)))
        sys.exit(0 if g else 1)
    sys.exit(0 if pruefen(WURZEL / "landing", render=True) else 1)
