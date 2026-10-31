#!/usr/bin/env python3
"""
verify_drawdown.py — Wächter für die Drawdown-Analyse (/drawdown): shared/drawdown.py = landing/js/drawdown-compute.js
= unabhängige Referenz = handgerechnete Sollwerte, dazu die echte Seite (DE + gebaute EN) in jsdom.

    py -3.14 scripts/verify_drawdown.py            # alle Pflichtprüfungen (so im Deploy-Gate)
    py -3.14 scripts/verify_drawdown.py --ohne-seite   # ohne jsdom (nur lokal, z. B. wenn landing/en fehlt)

Plan: docs/review_prompts/2026-10-31_drawdown_seite_plan_v3.md (+ Nachtrag 3 „beobachtete Schlusskurse“).
Blöcke: A Handfälle (Achse, Episoden, Ränge, KM, Kalender) · B unabhängige Referenz auf vier eingefrorenen Reihen ·
C Zwilling Python = JS (alle Funktionen, alle Zeiträume × Max Drawdown 5/7/10/20/33) · D Invarianten ·
E Stichtag E in drei Zeitzonen (Python und JS) · F echte Seite in jsdom (normal, am Hoch, kurz, Lücke, Ladefehler,
Fehler nach Erfolg, schneller Tickerwechsel, EN).
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import tempfile
from datetime import date, datetime, timedelta, timezone

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, WURZEL)
from shared import drawdown as DD                     # noqa: E402
from shared import sitzungen as SZ                    # noqa: E402

FIX = os.path.join(WURZEL, "scripts", "fixtures", "drawdown")
REIHEN = {  # Datei: (Börse, SHA-256)
    "qqq": ("NYSE", "b96e6d6e7f4d5ae7cccf65991dcc95f8789564a99c5de6dc5c7732599a6b46ad"),
    "gdaxi": ("XETRA", "34f451713d2501f9c65642b43d23fdfb35462e9fe1a38aa69e3831da78761265"),
    "btc_usd": ("CRYPTO", "1d99d355ccae93cba6d1acaadc64acb602b1243bed7ef1cc51d4650fd6cff519"),
    "eurusd": ("FOREX", "2af1eaf421c0cb5aea7244a53c09fa7b9b610fa716f654abe0240e14e8cc82bb"),
}
JETZT = datetime(2026, 10, 31, 12, tzinfo=timezone.utc)
ergebnisse, OK = [], [True]


def pr(name, bedingung, detail=""):
    ergebnisse.append(("ok   " if bedingung else "FEHL ") + name + ("" if bedingung else "  — " + str(detail)[:400]))
    if not bedingung:
        OK[0] = False


def nah(a, b, tol=1e-9):
    if a is None or b is None:
        return a is b
    return math.isclose(a, b, rel_tol=1e-12, abs_tol=tol)


def lade(name):
    p = os.path.join(FIX, name + "_2026-10-30.json")
    roh = open(p, "rb").read()
    if hashlib.sha256(roh).hexdigest() != REIHEN[name][1]:
        raise SystemExit(f"{p}: Prüfsumme weicht ab — eingefrorener Datenstand verändert")
    return json.loads(roh)["zeilen"]


# ───────────────────────────── JS-Ausführung ─────────────────────────────
JS_KERN = r"""
global.window={SA:{__release:()=>{}}};
const W=process.argv[1];require(W+'/landing/js/boersenkalender.js');require(W+'/landing/js/drawdown-compute.js');
const D=window.SA.drawdown, inp=JSON.parse(require('fs').readFileSync(0,'utf8'));
function alles(zeilen,boerse,jetzt,xs,ms){
  const r=D.analyse(zeilen,boerse,jetzt);
  const out={status:r.status,d_heute:r.d_heute===undefined?null:r.d_heute,laufend:r.laufend===undefined?null:r.laufend,achse:{}};
  for(const k of Object.keys(r.achse)) out.achse[k]=r.achse[k];
  if(r.status==='zu_wenig_daten') return out;
  out.kurve=D.kurve(r); out.kalender=D.kalender(r); out.fenster={};
  for(const n of [10,15,20,null]){const st=n===null?r.achse.daten[0]:D.minusJahre(r.achse.e,n);const f={st};
    for(const m of ms) f['g'+m]=D.gruppe(r,st,m);
    for(const x of xs){f['v'+x]=D.vergleichAb(r,st,x);f['km'+x]=D.kaplanMeier(r,st,x);f['fr'+x]=D.forwardReturns(r,st,x);}
    f.gr=D.grenzueberschreitend(r,st); f.za=D.zeitanteil(r,st); out.fenster[n===null?'None':String(n)]=f;}
  return out;}
const res=inp.faelle.map(f=>{try{return alles(f.zeilen,f.boerse,f.jetzt,f.xs,f.ms);}catch(e){return {fehler:String(e&&e.message||e)};}});
const st=(inp.stichtage||[]).map(s=>{try{return D.stichtag(s[0],s[1]);}catch(e){return 'FEHLER '+e.message;}});
const gr=(inp.grenz||[]).map(g=>{try{return D.grenzueberschreitend(D.analyse(g[0],g[1],g[2]),g[3]);}catch(e){return 'FEHLER '+e.message;}});
const mj=[['2024-02-29',20],['2024-02-29',1],['2024-02-29',4],['2026-10-30',10],['2000-02-29',100]].map(p=>D.minusJahre(p[0],p[1]));
process.stdout.write(JSON.stringify({res,st,mj,gr}));
"""


def js(faelle, stichtage=(), tz="Europe/Berlin", grenz=()):
    env = dict(os.environ, TZ=tz)
    p = subprocess.run(["node", "-e", JS_KERN, WURZEL], input=json.dumps({"faelle": faelle, "stichtage": list(stichtage), "grenz": list(grenz)}),
                       capture_output=True, text=True, encoding="utf-8", env=env, timeout=600)
    if p.returncode:
        raise RuntimeError(p.stderr[-800:])
    return json.loads(p.stdout)


def py_alles(zeilen, boerse, jetzt, xs, ms):
    r = DD.analyse(zeilen, boerse, jetzt)
    out = {"status": r["status"], "d_heute": r.get("d_heute"), "laufend": r.get("laufend"), "achse": r["achse"]}
    if r["status"] == "zu_wenig_daten":
        return out
    out["kurve"] = DD.kurve(r)
    out["kalender"] = DD.kalender(r)
    out["fenster"] = {}
    for n in (10, 15, 20, None):
        st = r["achse"]["daten"][0] if n is None else DD.minus_jahre(r["achse"]["e"], n)
        f = {"st": st}
        for m in ms:
            f[f"g{m}"] = DD.gruppe(r, st, m)
        for x in xs:
            f[f"v{x}"] = DD.vergleich_ab(r, st, x)
            f[f"km{x}"] = DD.kaplan_meier(r, st, x)
            f[f"fr{x}"] = DD.forward_returns(r, st, x)
        f["gr"] = DD.grenzueberschreitend(r, st)
        f["za"] = DD.zeitanteil(r, st)
        out["fenster"][str(n)] = f
    return json.loads(json.dumps(out))


def vergleiche(a, b, pfad="", fehler=None):
    fehler = [] if fehler is None else fehler
    if isinstance(a, dict) and isinstance(b, dict):
        for k in set(a) | set(b):
            if k not in a or k not in b:
                fehler.append(f"{pfad}.{k}: nur in {'py' if k in a else 'js'}")
            else:
                vergleiche(a[k], b[k], f"{pfad}.{k}", fehler)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            fehler.append(f"{pfad}: Länge {len(a)} ≠ {len(b)}")
        else:
            for i, (x, y) in enumerate(zip(a, b)):
                vergleiche(x, y, f"{pfad}[{i}]", fehler)
    elif isinstance(a, bool) or isinstance(b, bool):
        if a != b:
            fehler.append(f"{pfad}: {a} ≠ {b}")
    elif isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if not nah(a, b):
            fehler.append(f"{pfad}: {a} ≠ {b}")
    elif a != b:
        fehler.append(f"{pfad}: {a!r} ≠ {b!r}")
    return fehler


def blaetter(x):
    return sum(blaetter(v) for v in x.values()) if isinstance(x, dict) else sum(blaetter(v) for v in x) if isinstance(x, list) else 1


# ───────────────────────────── Bausteine für Handfälle ─────────────────────────────

def reihe(boerse, closes, start="2024-01-02", fehlen=(), lr_ueber=None):
    """Kurszeilen auf den Sitzungen der Börse ab start, Renditen aus den Schlüssen (fehlende Sitzungen: Rendite der
    Folgezeile überbrückt, sofern lr_ueber nicht anders gesetzt ist)."""
    sitz, d = [], date.fromisoformat(start)
    while len(sitz) < len(closes):
        if SZ.offen(d, boerse):
            sitz.append(d.isoformat())
        d += timedelta(days=1)
    zeilen, vor = [], None
    for i, (s, c) in enumerate(zip(sitz, closes)):
        if i in fehlen:
            continue
        lr = None if vor is None else math.log(c / vor)
        if lr_ueber and s in lr_ueber:
            lr = lr_ueber[s]
        zeilen.append({"date": s, "close": c, "log_return": lr})
        vor = c
    return zeilen, sitz


def jetzt_nach(sitz, boerse):
    """Mittag UTC des Kalendertags nach der letzten Sitzung — dort ist das Börsendatum (NYSE, XETRA, UTC) der Folgetag,
    E also die letzte Sitzung. Bewusst OHNE DD.stichtag: der Wächter darf nicht an der Funktion hängen, die er prüft
    (Mutationstest: ein mutierter Stichtag ließ ihn vorher abstürzen statt rot werden)."""
    d = date.fromisoformat(sitz[-1]) + timedelta(days=1)
    return datetime(d.year, d.month, d.day, 12, tzinfo=timezone.utc)


def block_a(alle_faelle):
    """Handfälle mit Sollwerten — Python direkt, JS über alle_faelle (gesammelt, ein node-Lauf)."""
    soll = []

    def fall(name, boerse, zeilen, sitz, pruef, jetzt=None):
        j = jetzt or jetzt_nach(sitz, boerse)
        r = py_alles(zeilen, boerse, j, [10, 20], [5, 10])
        alle_faelle.append({"name": name, "zeilen": zeilen, "boerse": boerse, "jetzt": int(j.timestamp() * 1000),
                            "xs": [10, 20], "ms": [5, 10], "py": r, "pruef": pruef})
        soll.append((name, r, pruef))

    # A1: zwei abgeschlossene Episoden, Recovery genau auf Peak-Niveau (≥), dann neues Hoch
    z, s = reihe("NYSE", [100, 110, 99, 121, 110, 121, 125])
    fall("A1 zwei Episoden", "NYSE", z, s, lambda r, s=s: (
        r["status"] == "ok" and r["laufend"] is None and nah(r["d_heute"], 0) and
        [(e["peak"], e["trough"], e["recovery"], round(e["max_dd"], 9), e["peak_to_trough"], e["ttr"], e["dauer"])
         for e in r["fenster"]["None"]["g5"]["einzel"]] ==
        [(s[1], s[2], s[3], -10.0, 1, 1, 2), (s[3], s[4], s[5], round(100 * (110 / 121 - 1), 9), 1, 1, 2)]))
    # A2: Gleichstand am Trough → frühere Sitzung
    z, s = reihe("NYSE", [100, 90, 90, 100])
    fall("A2 Gleichstand am Trough", "NYSE", z, s, lambda r, s=s: r["fenster"]["None"]["g5"]["einzel"][0]["trough"] == s[1])
    # A3: laufende Episode, Ränge
    z, s = reihe("NYSE", [100, 90, 100, 120, 108])
    fall("A3 laufend", "NYSE", z, s, lambda r, s=s: (
        r["status"] == "ok" and r["laufend"]["peak"] == s[3] and r["laufend"]["seit_peak"] == 1 and nah(r["d_heute"], -10.0)
        and r["fenster"]["None"]["g5"]["n"] == 1 and r["fenster"]["None"]["g5"]["laufend_erfuellt"] is True
        and r["fenster"]["None"]["g5"]["kuerzer_als_laufend"] == 0 and r["fenster"]["None"]["g5"]["tiefer_als_laufend"] == 0
        and r["fenster"]["None"]["g10"]["laufend_erfuellt"] is True))
    # A4: echte Lücke in belegtem Jahr (NYSE 2024)
    z, s = reihe("NYSE", [100, 105, 95, 90, 100, 110], fehlen=(2,))
    fall("A4 Lücke belegtes Jahr", "NYSE", z, s, lambda r, s=s: r["status"] == "luecke" and r["achse"]["erste_luecke"] == s[2]
         and r["laufend"] is None and r["d_heute"] is None)
    # A5: Krypto — fehlende Zeile ist immer echte Lücke (Codex-Gegenbeispiel −50 %)
    z, s = reihe("CRYPTO", [100, 50, 90, 100, 101], start="2024-03-01", fehlen=(1,))
    fall("A5 Krypto ohne Ausnahme", "CRYPTO", z, s, lambda r, s=s: r["status"] == "luecke")
    # A6: ungeprüftes Jahr (XETRA 1999), fehlender neuer Hochpunkt mit korrekter Brücke → beobachtete Schlüsse
    z, s = reihe("XETRA", [100, 200, 90, 100, 105], start="1999-01-04", fehlen=(1,))
    fall("A6 beobachtete Schlüsse (Vertrag B)", "XETRA", z, s, lambda r, s=s: (
        r["status"] == "ok" and r["achse"]["n_ueberbrueckt"] == 1 and r["achse"]["ueberbrueckt_jahre"] == [1999]
        and [round(e["max_dd"], 9) for e in r["fenster"]["None"]["g5"]["einzel"]] == [-10.0]))
    # A7: Brücke inkonsistent → Lücke
    z, s = reihe("XETRA", [100, 200, 90, 100, 105], start="1999-01-04", fehlen=(1,))
    z[1]["log_return"] += 1e-3
    fall("A7 Brücke verletzt", "XETRA", z, s, lambda r, s=s: r["status"] == "luecke")
    # A8: drei fehlende Sitzungen in Folge → Lücke
    z, s = reihe("XETRA", [100, 101, 102, 103, 104, 105], start="1999-01-04", fehlen=(1, 2, 3))
    fall("A8 drei in Folge", "XETRA", z, s, lambda r, s=s: r["status"] == "luecke")
    # A9: fehlende Endzeilen → nicht aktuell
    z, s = reihe("NYSE", [100, 90, 95, 96, 97], fehlen=(3, 4))
    fall("A9 Reihenende fehlt", "NYSE", z, s, lambda r, s=s: r["status"] == "nicht_aktuell" and r["laufend"] is None
         and r["d_heute"] is None and r["achse"]["ende_fehlt"] is True)
    # A10: Kaplan-Meier — drei Episoden erreichen −20 %: Recovery nach 2 und 4 HT, laufende zensiert bei 3
    closes = [100, 80, 90, 100, 79, 85, 90, 95, 100, 80, 85, 90, 95]
    z, s = reihe("NYSE", closes)
    s_t1 = 2 / 3
    se1 = math.sqrt(1 / 6) / abs(math.log(s_t1))
    ll = math.log(-math.log(s_t1))
    lo1, hi1 = math.exp(-math.exp(ll + DD.Z95 * se1)), math.exp(-math.exp(ll - DD.Z95 * se1))

    def km_pruef(r, s=s):
        km = r["fenster"]["None"]["km20"]
        k = km["kurve"]
        return (km["n"] == 3 and km["ereignisse"] == 2 and km["zensiert"] == [3] and km["median"] == 4
                and [p["t"] for p in k] == [0, 2, 4] and nah(k[1]["s"], s_t1) and k[1]["risiko"] == 3
                and nah(k[1]["lo"], lo1) and nah(k[1]["hi"], hi1) and k[2]["s"] == 0 and k[2]["risiko"] == 1
                and k[2]["lo"] is None and k[2]["hi"] is None)
    fall("A10 Kaplan-Meier Handfall (Greenwood, log-log)", "NYSE", z, s, km_pruef)
    # A11: Tempo = erster Übertritt − Peak, NICHT das Alter: die laufende Episode erreicht −10 % nach 1 Sitzung,
    # ist aber schon 3 Sitzungen alt (frühere Episode: Übertritt nach 1, mit Erholung dazwischen)
    z, s = reihe("NYSE", [100, 88, 95, 85, 100, 110, 98, 99, 97])
    fall("A11 Tempo = erster Übertritt", "NYSE", z, s, lambda r, s=s: (
        nah(r["d_heute"], 100 * (97 / 110 - 1)) and r["laufend"]["seit_peak"] == 3
        and r["fenster"]["None"]["v10"]["tempo_laufend"] == 1
        and [e["bis_uebertritt"] for e in r["fenster"]["None"]["v10"]["einzel"]] == [1]
        and r["fenster"]["None"]["v10"]["langsamer_als_laufend"] == 0))
    # A13: Rundungsrest beim Wiedererreichen: 100 → 102 → 74 → 102 → 74 → 102 = zwei abgeschlossene Episoden je 2 HT
    z, s = reihe("NYSE", [100, 102, 74, 102, 74, 102, 103])
    fall("A13 Recovery trotz Rundungsrest", "NYSE", z, s, lambda r, s=s: (
        [(e["peak"], e["recovery"], e["dauer"]) for e in r["fenster"]["None"]["g5"]["einzel"]] == [(s[1], s[3], 2), (s[3], s[5], 2)]
        and r["laufend"] is None))
    # A15: Forward-Fenster mit gleichem Start- und Endkurs (Codex Code-R3): 100 → 90 → 110 → 19 × 90, Krypto.
    # Ereignis bei 90, nach 20 Tagen wieder 90 → Rendite 0, NICHT positiv; Basis (100→90, 90→90) ebenfalls 0 % positiv
    z, s = reihe("CRYPTO", [100, 90, 110] + [90] * 19)
    fall("A15 Nullrendite nicht positiv", "CRYPTO", z, s, lambda r: (
        r["fenster"]["None"]["fr10"]["h"]["20"]["ereignisse"]["n"] == 1
        and r["fenster"]["None"]["fr10"]["h"]["20"]["ereignisse"]["anteil_positiv"] == 0
        and nah(r["fenster"]["None"]["fr10"]["h"]["20"]["ereignisse"]["mittel"], 0)
        and r["fenster"]["None"]["fr10"]["h"]["20"]["basis"]["n"] == 2
        and r["fenster"]["None"]["fr10"]["h"]["20"]["basis"]["anteil_positiv"] == 0))
    # A16: Rendite +1e-10 liegt über der Nulltoleranz (1e-12) → positiv (Codex Code-R4: Grenzfall zwischen 1e-12 und 1e-9)
    z, s = reihe("CRYPTO", [100, 90, 110] + [90] * 18 + [90 * (1 + 1e-10)])
    fall("A16 Kleinstrendite positiv", "CRYPTO", z, s, lambda r: (
        r["fenster"]["None"]["fr10"]["h"]["20"]["ereignisse"]["n"] == 1
        and r["fenster"]["None"]["fr10"]["h"]["20"]["ereignisse"]["anteil_positiv"] == 1
        and r["fenster"]["None"]["fr10"]["h"]["20"]["basis"]["n"] == 2
        and r["fenster"]["None"]["fr10"]["h"]["20"]["basis"]["anteil_positiv"] == 0.5))
    # A12: Drawdown-Kalender über Jahreswechsel mit Vorjahreshoch
    z, s = reihe("NYSE", [100, 120, 90, 96, 108, 132], start="2024-12-27")
    jahre = {}
    for d_, c in zip(s, [100, 120, 90, 96, 108, 132]):
        jahre.setdefault(d_[:4], []).append(c)
    hoch, erw = 0, {}
    for d_, c in zip(s, [100, 120, 90, 96, 108, 132]):
        hoch = max(hoch, c)
        erw.setdefault(int(d_[:4]), []).append(100 * (c / hoch - 1))
    fall("A12 Kalender mit Vorjahreshoch", "NYSE", z, s, lambda r, s=s: all(
        nah(k["tiefster"], min(erw[k["jahr"]])) and nah(k["ulcer"], math.sqrt(sum(x * x for x in erw[k["jahr"]]) / len(erw[k["jahr"]])))
        and k["teiljahr"] is True for k in r["kalender"]))
    return soll


# ───────────────────────────── B: unabhängige Referenz ─────────────────────────────

def referenz(daten, lr, start, m, x):
    """Schlichte Nachrechnung auf der gemeinsamen Achse (nicht aus shared/drawdown): Episoden über das Laufmaximum."""
    n = lr.index(None) if None in lr else len(lr)
    idx, k = [], 0.0
    for i in range(n):
        k += lr[i]
        idx.append(math.exp(k))
    eps, peak, i = [], 0, 1
    while i < n:
        if idx[i] >= idx[peak]:
            peak = i
            i += 1
            continue
        j = i
        while j < n and idx[j] < idx[peak]:
            j += 1
        seg = idx[i:j]
        t = i + seg.index(min(seg))
        eps.append({"p": peak, "t": t, "r": j if j < n else None, "dd": idx[t] / idx[peak] - 1})
        if j < n:
            peak = j
        i = j + 1 if j < n else n
    fertig = [e for e in eps if e["r"] is not None and daten[e["p"]] >= start and -100 * e["dd"] >= m]
    dauer = sorted(e["r"] - e["p"] for e in fertig)

    def q(v, p):
        if not v:
            return None
        s = sorted(v)
        pos = (len(s) - 1) * p
        lo = int(math.floor(pos))
        return s[lo] + (s[min(lo + 1, len(s) - 1)] - s[lo]) * (pos - lo)
    ab = []
    for e in eps:
        if e["r"] is None or daten[e["p"]] < start:
            continue
        for c in range(e["p"] + 1, e["r"]):
            if idx[c] / idx[e["p"]] - 1 <= -x / 100:
                ab.append(e["r"] - c)
                break
    return {"n": len(fertig), "median": q(dauer, .5), "q25": q(dauer, .25), "q75": q(dauer, .75),
            "ab_n": len(ab), "ab_median": q(ab, .5)}


def referenz_forward(daten, lr, start, x, h):
    """Forward Returns unabhängig nachgerechnet (Codex Code R1, Befund 3): Ereignis = erster Übertritt je Episode."""
    n = lr.index(None) if None in lr else len(lr)
    idx, k = [], 0.0
    for i in range(n):
        k += lr[i]
        idx.append(math.exp(k))
    ereig, peak, offen_ab = [], 0, None
    for i in range(1, n):
        if idx[i] >= idx[peak] * (1 - DD.EPS):
            peak, offen_ab = i, None
            continue
        if offen_ab is None and daten[peak] >= start and idx[i] / idx[peak] - 1 <= -x / 100 + DD.EPS:
            ereig.append(i)
            offen_ab = peak
    # ein Ereignis je Episode: nach dem ersten Übertritt bis zur Recovery kein zweites
    rein, gesehen = [], set()
    for c in ereig:
        p = max(j for j in range(c) if idx[j] >= max(idx[:j + 1]) * (1 - DD.EPS))
        if p not in gesehen:
            gesehen.add(p)
            rein.append(c)

    def F(i):
        if i + h > n - 1:
            return None
        kum, mn = 0.0, 0.0
        for j in range(i + 1, i + h + 1):
            kum += lr[j]
            mn = min(mn, math.exp(kum) - 1)
        return 100 * (math.exp(kum) - 1), 100 * mn, math.exp(kum) - 1 > 1e-12  # fachlicher Grenzwert wie der Kern (EPS)
    ev = [w for w in (F(c) for c in rein) if w is not None]
    bas = [w for w in (F(i) for i in range(n) if daten[i] >= start) if w is not None]
    return {"n": len(ev), "unv": len(rein) - len(ev), "mittel": sum(w[0] for w in ev) / len(ev) if ev else None,
            "zw": sum(w[1] for w in ev) / len(ev) if ev else None, "basis_n": len(bas),
            "basis_mittel": sum(w[0] for w in bas) / len(bas) if bas else None,
            "ue": sum(1 for x in rein for y in rein if x < y and y + h <= n - 1 and y - x < h),
            "pos": sum(1 for w in ev if w[2]), "basis_pos": sum(1 for w in bas if w[2])}


# ───────────────────────────── Hauptlauf ─────────────────────────────

def main(seite=True):
    faelle = []
    soll = block_a(faelle)
    for name, r, pruef in soll:
        try:
            pr(f"[A] {name} (Python)", pruef(r), json.dumps(r.get("fenster", {}).get("None", {}).get("g5", {}).get("einzel", r.get("status")))[:300])
        except Exception as e:      # noqa: BLE001 — Absturz der Prüfung ist rot
            pr(f"[A] {name} (Python)", False, f"{type(e).__name__}: {e}")

    # echte Reihen für B/C
    reihen = {n: lade(n) for n in REIHEN}
    ms, xs_basis = [5, 7, 10, 20, 33], [10, 20]
    for n, (b, _) in REIHEN.items():
        r = DD.analyse(reihen[n], b, JETZT)
        x_akt = -r["d_heute"] if r.get("d_heute") else None
        xs = xs_basis + ([x_akt] if x_akt else [])
        py = py_alles(reihen[n], b, JETZT, xs, ms)
        faelle.append({"name": "C " + n, "zeilen": reihen[n], "boerse": b, "jetzt": int(JETZT.timestamp() * 1000),
                       "xs": xs, "ms": ms, "py": py})
        # B: unabhängige Referenz
        a = r["achse"]
        for fen in ("10", "None"):
            st = a["daten"][0] if fen == "None" else DD.minus_jahre(a["e"], int(fen))
            for m in (5, 10, 20):
                ref = referenz(a["daten"], a["lr"], st, m, 10)
                g = py["fenster"][fen][f"g{m}"]
                v = py["fenster"][fen]["v10"]
                pr(f"[B] {n} Zeitraum {fen} MaxDD {m}: Episoden/Quartile = Referenz",
                   g["n"] == ref["n"] and nah(g["dauer_median"], ref["median"]) and nah(g["dauer_q25"], ref["q25"])
                   and nah(g["dauer_q75"], ref["q75"]), f"{g['n']} {g['dauer_median']} gegen {ref}")
            pr(f"[B] {n} Zeitraum {fen}: ab −10 % bis Recovery = Referenz", v["n"] == ref["ab_n"] and nah(v["ab_median"], ref["ab_median"]),
               f"{v['n']} {v['ab_median']} gegen {ref}")
            for h in DD.HORIZONTE:
                rf = referenz_forward(a["daten"], a["lr"], st, 10, h)
                z_ = py["fenster"][fen]["fr10"]["h"][str(h)]
                e_, b_ = z_["ereignisse"] or {}, z_["basis"] or {}
                pr(f"[B] {n} Zeitraum {fen}: Forward {h} HT = Referenz",
                   (e_.get("n") or 0) == rf["n"] and z_["unvollstaendig"] == rf["unv"] and nah(e_.get("mittel"), rf["mittel"], 1e-7)
                   and nah(e_.get("zwischenverlust_mittel"), rf["zw"], 1e-7) and (b_.get("n") or 0) == rf["basis_n"]
                   and nah(b_.get("mittel"), rf["basis_mittel"], 1e-7) and z_["ueberlappende_paare"] == rf["ue"]
                   and (not e_ or round(e_["anteil_positiv"] * e_["n"]) == rf["pos"])
                   and (not b_ or round(b_["anteil_positiv"] * b_["n"]) == rf["basis_pos"]),
                   f"{e_} {z_['unvollstaendig']} {b_.get('n')} {z_['ueberlappende_paare']} gegen {rf}")

    # E: Stichtage (Sollwerte) — Python + JS in drei Zeitzonen
    E_FAELLE = [("NYSE", "2026-10-30T22:00:00Z", "2026-10-29"), ("NYSE", "2026-10-31T04:30:00Z", "2026-10-30"),
                ("NYSE", "2026-07-03T18:00:00Z", "2026-07-02"), ("NYSE", "2026-11-28T06:00:00Z", "2026-11-27"),
                ("XETRA", "2026-10-30T18:00:00Z", "2026-10-29"), ("XETRA", "2026-10-31T00:30:00Z", "2026-10-30"),
                ("CRYPTO", "2026-10-31T23:59:00Z", "2026-10-30"), ("CRYPTO", "2026-11-01T00:01:00Z", "2026-10-31"),
                ("FOREX", "2026-10-31T12:00:00Z", "2026-10-30"), ("FOREX", "2026-11-02T12:00:00Z", "2026-10-30"),
                ("NYSE", "2026-03-09T03:30:00Z", "2026-03-06")]
    for b, t, s_ in E_FAELLE:
        ist = DD.stichtag(b, datetime.fromisoformat(t.replace("Z", "+00:00")))
        pr(f"[E] Python {b} {t} → {s_}", ist == s_, ist)

    # A14: Episode über den Zeitraumstart, Tiefe genau −5 % mit Rundungsrest (Codex Code-R2): 100 → 102 → 96,9 → 102 → 103,
    # Start am dritten Schluss — muss wie die abgeschlossene Episode unter „mindestens 5 %“ genannt werden
    _g14z, _g14s = reihe("NYSE", [100, 102, 96.9, 102, 103])
    _g14j = jetzt_nach(_g14s, "NYSE")
    GRENZ = [[_g14z, "NYSE", int(_g14j.timestamp() * 1000), _g14s[2]]]
    GRENZ_PY = json.loads(json.dumps(DD.grenzueberschreitend(DD.analyse(_g14z, "NYSE", _g14j), _g14s[2])))

    # ein node-Lauf je Zeitzone: Handfälle + echte Reihen + Stichtage
    for tz in ("Europe/Berlin", "America/Los_Angeles", "UTC"):
        try:
            out = js([{k: f[k] for k in ("zeilen", "boerse", "jetzt", "xs", "ms")} for f in faelle],
                     [[b, int(datetime.fromisoformat(t.replace("Z", "+00:00")).timestamp() * 1000)] for b, t, _ in E_FAELLE], tz, grenz=GRENZ)
        except Exception as e:      # noqa: BLE001
            pr(f"[C] JS-Lauf {tz}", False, e)
            continue
        for f, j in zip(faelle, out["res"]):
            if "fehler" in j:
                pr(f"[C] {tz} {f['name']}: JS ohne Absturz", False, j["fehler"])
                continue
            fe = vergleiche(f["py"], j)
            pr(f"[C] {tz} {f['name']}: Python = JS ({blaetter(f['py'])} Werte)", not fe, "; ".join(fe[:5]))
            if f.get("pruef") and tz == "UTC":
                try:
                    pr(f"[A] {f['name']} (JS)", f["pruef"](j))
                except Exception as e:  # noqa: BLE001
                    pr(f"[A] {f['name']} (JS)", False, f"{type(e).__name__}: {e}")
        for (b, t, s_), ist in zip(E_FAELLE, out["st"]):
            pr(f"[E] JS {tz} {b} {t} → {s_}", ist == s_, ist)
        pr(f"[A] A14 periodenübergreifend trotz Rundungsrest (JS {tz})", len(out["gr"]) == 1 and not vergleiche(GRENZ_PY, out["gr"][0]) and len(out["gr"][0]) == 1,
           f"{out['gr']} / {GRENZ_PY}")
        mj_soll = ["2004-02-29", "2023-02-28", "2020-02-29", "2016-10-30", "1900-02-28"]
        pr(f"[E] JS {tz} minusJahre mit Schalttag", out["mj"] == mj_soll, out["mj"])
    pr("[A] A14 periodenübergreifend trotz Rundungsrest (Python)", len(GRENZ_PY) == 1 and GRENZ_PY[0]["peak"] == _g14s[1],
       GRENZ_PY)
    pr("[E] Python minus_jahre mit Schalttag", [DD.minus_jahre(d_, n_) for d_, n_ in
       [("2024-02-29", 20), ("2024-02-29", 1), ("2024-02-29", 4), ("2026-10-30", 10), ("2000-02-29", 100)]]
       == ["2004-02-29", "2023-02-28", "2020-02-29", "2016-10-30", "1900-02-28"])

    # D: Invarianten (Python; JS ist über C gleich)
    q = reihen["qqq"]
    basis = py_alles(q, "NYSE", JETZT, [10], [5, 10])
    skal = [dict(z, close=z["close"] * 7) for z in q]
    pr("[D] Skalierung der Kurse ändert nichts", not vergleiche(basis, py_alles(skal, "NYSE", JETZT, [10], [5, 10])))
    ph = copy.deepcopy(q)
    k = next(i for i, z in enumerate(ph) if z["date"] == "2024-06-14")
    ph.insert(k + 1, {"date": "2024-06-15", "close": ph[k]["close"], "log_return": 0.0})       # Samstag
    mit_ph = py_alles(ph, "NYSE", JETZT, [10], [5, 10])
    mit_ph_ohne_zaehler = copy.deepcopy(mit_ph); mit_ph_ohne_zaehler["achse"]["n_phantom"] -= 1
    pr("[D] Phantomzeile (Samstag, Rendite 0) ändert nur den Zähler", not vergleiche(basis, mit_ph_ohne_zaehler))
    r = DD.analyse(q, "NYSE", JETZT)
    eps_vorher = json.dumps(r["eps"])
    for fen in (10, 15, 20):
        DD.gruppe(r, DD.minus_jahre(r["achse"]["e"], fen), 5)
    pr("[D] Zeitraum/Filter ändern keine Episoden", json.dumps(r["eps"]) == eps_vorher)
    pr("[D] Laufende Episode unabhängig vom Filter", basis["laufend"] == py_alles(q, "NYSE", JETZT, [10], [33])["laufend"])

    if seite:
        block_f(reihen)

    for e in ergebnisse:
        sys.stdout.write(e + "\n")
    sys.stdout.write("verify_drawdown: %s (%d Prüfungen)\n" % ("BESTANDEN" if OK[0] else "DURCHGEFALLEN", len(ergebnisse)))
    return OK[0]


# ───────────────────────────── F: echte Seite ─────────────────────────────

def block_f(reihen):
    q = reihen["qqq"]
    hoch, c = [], 100.0
    for i, z in enumerate(q):
        neu = c * math.exp(0.001) if i else c
        hoch.append({"date": z["date"], "close": neu, "log_return": 0.001 if i else None})
        c = neu
    def kurz_reihe(closes):
        sitz = [z["date"] for z in q[-len(closes):]]
        return [{"date": d_, "close": c_, "log_return": (math.log(c_ / closes[i - 1]) if i else None)}
                for i, (d_, c_) in enumerate(zip(sitz, closes))]
    fix = {"QQQ": q, "HOCH": hoch, "KURZ": q[-1:], "LUECKE": [z for z in q if z["date"] != "2020-03-16"], "SPY": q,
           "N0": kurz_reihe([100, 90, 85, 80]), "N1": kurz_reihe([100, 80, 100, 80]), "S5": kurz_reihe([100, 102, 96.9, 96.9]),
           "NULL": kurz_reihe([100, 90, 110] + [90] * 18 + [90 * (1 + 1e-10)] * 3)}  # Kleinstrendite: gerundet 0,00 %
    tmp = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
    json.dump(fix, tmp); tmp.close()
    r = DD.analyse(q, "NYSE", JETZT)
    a = r["achse"]
    st = DD.minus_jahre(a["e"], 10)
    g = DD.gruppe(r, st, 5)
    v = DD.vergleich_ab(r, st, -r["d_heute"])
    km = DD.kaplan_meier(r, st, -r["d_heute"])
    en_seite = os.path.join(WURZEL, "landing", "en", "drawdown.html")
    if True:
        # Immer neu bauen: im Deploy-Gate ist landing/en noch nicht gebaut (das macht der Server nach
        # inject_credentials), und lokal kann eine veraltete Fassung liegen (gitignored) — dann prüfte der Wächter
        # eine Seite, die es so nicht mehr gibt.
        bau = subprocess.run([sys.executable, os.path.join(WURZEL, "landing", "build_en.py"), "--write"], capture_output=True,
                             text=True, encoding="utf-8", timeout=600)
    en_gebaut = bau.returncode == 0 and os.path.exists(en_seite)
    pr("[F] EN-Seite frisch gebaut (build_en.py --write Exit 0, landing/en/drawdown.html)", en_gebaut,
       f"Exit {bau.returncode}: {(bau.stderr or bau.stdout or '')[-300:]}")
    for fall in ("normal", "hoch", "kurz", "luecke", "fehler", "fehler_nach_erfolg", "wechsel", "en",
                 "kurz_nach_erfolg", "n0", "n1", "schwelle", "null"):
        if fall == "en" and not en_gebaut:
            continue
        p = subprocess.run(["node", os.path.join(WURZEL, "scripts", "js", "probe_drawdown_seite.js"),
                            os.path.join(WURZEL, "landing"), fall, tmp.name], capture_output=True, text=True, encoding="utf-8", timeout=300)
        try:
            d = json.loads(p.stdout)
        except ValueError:
            pr(f"[F] {fall}: Probe läuft", False, (p.stderr or p.stdout)[-300:])
            continue
        pr(f"[F] {fall}: ohne Absturz, ruhig, keine Seitenfehler", not d.get("absturz") and d.get("ruhig") and not d.get("seitenfehler"),
           (d.get("absturz") or "") + " | ".join(d.get("seitenfehler") or []))
        de = fall != "en"
        if fall in ("normal", "en"):
            pr(f"[F] {fall}: volle Historie angefordert (kein Startdatum), mit log_return",
               d["kursanfragen"] and "date=gte." not in d["kursanfragen"][0] and "log_return" in d["kursanfragen"][0], d["kursanfragen"][:1])
            pr(f"[F] {fall}: kein Fehlerbanner", not d.get("fehler"), d.get("fehler"))
            dd_txt = ("−" + f"{-r['d_heute']:.2f}".replace(".", ",") + " %") if de else ("−" + f"{-r['d_heute']:.2f}" + "%")
            pr(f"[F] {fall}: Status = Kern", d["status_dd"] == dd_txt and str(r["laufend"]["seit_peak"]) in d["dauer"], f"{d['status_dd']} | {d['dauer']}")
            k = d["kacheln"]
            von = "von" if de else "of"
            pr(f"[F] {fall}: Kachel Rang Dauer/Tiefe = Kern",
               f"{g['kuerzer_als_laufend']} {von} {g['n']}" in k and f"{g['tiefer_als_laufend']} {von} {g['n']}" in k, k[:300])
            med = f"{v['ab_median']:.1f}"
            pr(f"[F] {fall}: Kachel/Antwort ab aktuellem DD = Kern", (med.replace(".", ",") if de else med) in k
               and (med.replace(".", ",") if de else med) in d["antwort"], d["antwort"][:300])
            pr(f"[F] {fall}: Episodentabelle = Gruppe + laufende Zeile", d["tabelle_zeilen"] == g["n"] + 1, d["tabelle_zeilen"])
            fr = DD.forward_returns(r, st, -r["d_heute"])
            b60 = fr["h"]["60"]["basis"]["n"]
            b60_txt = f"{b60:,}".replace(",", ".") if de else f"{b60:,}"
            pr(f"[F] {fall}: Forward-Tabelle zeigt Basis-n", d["fr_zeilen"] == 3 and b60_txt in d["fr"], d["fr"][:200])
            charts = {c["el"]: c for c in d["charts"]}
            pr(f"[F] {fall}: sieben Charts", set(charts) == {"c-dauer", "c-streu", "c-ab", "c-tempo", "c-km", "c-kal", "c-kurve"}, list(charts))
            if "c-km" in charts:
                ser = json.loads(charts["c-km"]["series"])
                pr(f"[F] {fall}: KM-Serie = Kern", len(ser[0]["data"]) == len(km["kurve"])
                   and all(nah(p_[1], round(100 * k_["s"], 2), 1e-6) for p_, k_ in zip(ser[0]["data"], km["kurve"])), str(ser[0]["data"][:3]))
            if "c-kurve" in charts:
                ser = json.loads(charts["c-kurve"]["series"])
                pr(f"[F] {fall}: Drawdown-Kurve vollständig", len(ser[0]["data"]) == len(a["daten"]), len(ser[0]["data"]))
            if fall == "en":
                pr("[F] en: englisch (kein deutscher Einordnungssatz)", "Handelstage" not in d["antwort"] and "trading days" in d["antwort"], d["antwort"][:200])
        elif fall == "hoch":
            pr("[F] hoch: kein laufender Drawdown", d["status_dd"] == "0,00 %" and "Kein laufender Drawdown" in d["antwort"], d["antwort"][:200])
        elif fall == "kurz":
            pr("[F] kurz: nicht bestimmbar", d["status_dd"] == "nicht bestimmbar" and "Zu wenig" in d["antwort"], d["status_dd"])
        elif fall in ("luecke", "wechsel"):
            pr(f"[F] {fall}: Lücke erkannt (LUECKE)", d["titel"] == "LUECKE" and d["status_dd"] == "nicht bestimmbar"
               and "16.03.2020" in d["antwort"], f"{d['titel']} {d['status_dd']} {d['antwort'][:120]}")
        elif fall == "fehler":
            pr("[F] fehler: Banner, keine Werte", bool(d.get("fehler")) and d["status_dd"] == "–" and d["tabelle_zeilen"] == 0, d.get("fehler"))
        elif fall == "kurz_nach_erfolg":
            pr("[F] kurz_nach_erfolg: alte Ergebnisse verschwinden", d["vorher"]["tabelle_zeilen"] > 0 and d["titel"] == "KURZ"
               and d["tabelle_zeilen"] == 0 and d["fr_zeilen"] == 0 and d["kacheln"] == "" and d["status_dd"] == "nicht bestimmbar",
               f"{d['titel']} {d['tabelle_zeilen']} {d['fr_zeilen']} {d['kacheln'][:80]}")
        elif fall == "n0":
            pr("[F] n0: keine Vergleichsepisode → nicht bestimmbar statt „0 von 0“", "0 von 0" not in d["kacheln"]
               and "nicht bestimmbar" in d["kacheln"], d["kacheln"][:300])
            pr("[F] n0: Kurzantwort ohne „0 von 0“, mit „kein Vergleich“", "von 0" not in d["antwort"]
               and "nicht möglich" in d["antwort"], d["antwort"][:300])
        elif fall == "n1":
            pr("[F] n1: Einzelwerte statt Quartile", "mittlere Hälfte" not in d["kacheln"] and "Einzelwerte" in d["kacheln"], d["kacheln"][:300])
        elif fall == "schwelle":
            pr("[F] schwelle: −5,00 % gilt als erreicht (Toleranz wie der Kern)", "Kleiner Rücksetzer" not in d["antwort"]
               and d["status_dd"] == "−5,00 %", f"{d['status_dd']} | {d['antwort'][:160]}")
        elif fall == "null":
            pr("[F] null: gerundet 0,00 % ohne Vorzeichen und nicht rot", d["fr_zeilen"] == 3 and "0,00 %" in d["fr"]
               and "+0,00" not in d["fr"] and "−0,00" not in d["fr"] and d["fr_neg"] == 0, f"{d['fr'][:200]} | neg {d['fr_neg']}")
        elif fall == "fehler_nach_erfolg":
            pr("[F] fehler_nach_erfolg: vorher Werte, danach Banner und nichts Altes", d["vorher"]["tabelle_zeilen"] > 0
               and bool(d.get("fehler")) and d["titel"] == "SPY" and d["status_dd"] == "–" and d["tabelle_zeilen"] == 0
               and d["kacheln"] == "" and d["peak"] == "–", f"{d['titel']} {d['status_dd']} {d['tabelle_zeilen']}")
    os.unlink(tmp.name)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    try:
        gruen = main(seite="--ohne-seite" not in sys.argv)
    except Exception as e:                     # noqa: BLE001 — ein Absturz ist kein Nachweis (Mutationstest: ungültig)
        import traceback
        traceback.print_exc()
        sys.stdout.write(f"verify_drawdown: ABSTURZ ({type(e).__name__}: {e})\n")
        sys.exit(3)
    sys.exit(0 if gruen else 1)
