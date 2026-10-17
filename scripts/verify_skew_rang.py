#!/usr/bin/env python3
"""
verify_skew_rang.py — Skew-Rang EINMAL im Cron, /skew und Mail lesen ihn (Plan v3/v4 B3).

  1. shared.skew_rang gegen Sollwerte UND gegen die unabhängige JS-Referenz (scripts/js/skew_rang_ref.js) auf
     Fixtures: konstante Reihe, Gleichstände, x,5-Werte, 19/20 Punkte je Metrik, Grenze genau S−W, fehlender aktueller
     Wert in EINER Metrik, Reihe endet vor der Session, Zeta ohne iv_atm, doppeltes Datum, nicht normierte Zeilen,
     ungültige Werte (bool, Text, None).
  2. compute_options_skew.build: `rang`/`rang_session` im Snapshot, aus der zusammengeführten History (inkl. heute).
  3. /skew (scripts/js/probe_skew_rang_seite.js, echtes Seiten-JS): Radar = Rang aus dem Snapshot je Modus/Fenster/
     Ansicht; rang_session ≠ session → kein Punkt.
  4. Mail: daily_report.skew_pctl_map liest rang 365 skew pctl nur bei rang_session == session == erwartete Session;
     Vorlage einfarbig, fehlendes Perzentil sichtbar „P—“.
Exit 0 grün, 1 rot, 3 Absturz (kein Nachweis).
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import types
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

sys.dont_write_bytecode = True
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
_TMP = Path(tempfile.mkdtemp(prefix="sa_skewrang_"))
os.environ["SA_SPERR_DIR"] = str(_TMP / "sperre")
os.environ["SA_OHNE_DOTENV"] = "1"
os.environ["MASSIVE_API_KEY"] = "probe-kein-echter-schluessel"


def _absturz(typ, wert, tb):
    import traceback
    traceback.print_exception(typ, wert, tb)
    print("[Absturz]")
    shutil.rmtree(_TMP, ignore_errors=True)
    os._exit(3)


sys.excepthook = _absturz
try:
    import streamlit  # noqa: F401
except ImportError:
    def _cache_data(*a, **k):
        def deko(f):
            f.clear = lambda: None
            return f
        return deko(a[0]) if a and callable(a[0]) else deko
    sys.modules["streamlit"] = types.SimpleNamespace(cache_data=_cache_data)

from shared.skew_rang import rang_ticker, rang_gesamt, pruefe_ticker  # noqa: E402

UTC = ZoneInfo("UTC")
FEHLER = []
S = "2026-09-18"            # bewusst NICHT heute: ein Fenster ab der Uhr muss auffallen
SC = "2026-10-09"           # Session des Cron-Falls (Uhr 09.10. 23:00 UTC)


def pruef(name, ok, info=""):
    print(f"  {'ok  ' if ok else 'FAIL'} {name}" + (f"  ->  {info}" if info else ""))
    if not ok:
        FEHLER.append(name)


def _tag(k, basis=None):           # k Tage vor S (bzw. basis)
    return (date.fromisoformat(basis or S) - timedelta(days=k)).isoformat()


def _z(k, call=0.20, put=0.25, atm=0.22, skew=None, cm="cm", basis=None, **extra):
    e = {"date": _tag(k, basis), "cm_mode": cm, "call_iv": call, "put_iv": put, "iv_atm": atm,
         "skew_pts": skew if skew is not None else round((put - call) * 100, 4)}
    e.update(extra)
    return e


def _js(hist, session=S):
    f = _TMP / "ein.json"
    f.write_text(json.dumps({"hist": hist, "session": session}), encoding="utf-8")
    r = subprocess.run(["node", str(_ROOT / "scripts/js/skew_rang_ref.js"), str(f)], capture_output=True, text=True,
                       encoding="utf-8")
    if r.returncode != 0:
        return {"_fehler": r.stderr[-300:]}
    return json.loads(r.stdout)


# ── 1. Rechenkern ─────────────────────────────────────────────────────────────────────────────────────────────────
print("== shared.skew_rang gegen Sollwerte und JS-Referenz")
if shutil.which("node") is None:
    pruef("node vorhanden (JS-Referenz)", False, "node fehlt — ungeprüft ist nicht bestanden")
F = {}
# a) steigende Reihe, 25 Punkte: aktueller Wert ist das Maximum -> Rank 100, Pctl 100
F["steigend"] = [_z(k, call=0.20 + (25 - k) * 0.001) for k in range(24, -1, -1)]
# b) konstante Reihe -> Rank 50, Pctl 0
F["konstant"] = [_z(k) for k in range(24, -1, -1)]
# c) x,5: 21 Punkte, aktueller Wert 0,5 zwischen min 0 und max 1 auf der rr-Skala -> Rank 50 (halb nach oben)
F["halb"] = ([_z(k, call=0.20, put=0.20) for k in range(20, 10, -1)] + [_z(k, call=0.21, put=0.20) for k in range(10, 0, -1)]
             + [_z(0, call=0.205, put=0.20)])
# c2) Percentile genau 12,5: 3 von 24 Vorwerten liegen unter dem aktuellen -> 13 (halb nach oben)
F["pctl_halb"] = ([_z(k, call=0.20, put=0.20) for k in range(24, 21, -1)] + [_z(k, call=0.30, put=0.20) for k in range(21, 0, -1)]
                  + [_z(0, call=0.25, put=0.20)])
# d) 19 Punkte -> kein Rang; e) 20 Punkte -> Rang
F["n19"] = [_z(k) for k in range(18, -1, -1)]
F["n20"] = [_z(k) for k in range(19, -1, -1)]
# f) Grenze genau S−92 zählt mit (21 Punkte, ältester genau 92 Tage zurück), 93 nicht
F["grenze"] = [_z(92)] + [_z(k) for k in range(19, -1, -1)] + [_z(93, call=0.99)]
# g) heutiger skew fehlt (None), rr/iv vorhanden -> skew kein Rang, rr/iv schon
F["skew_fehlt"] = [_z(k) for k in range(24, 0, -1)] + [dict(_z(0), skew_pts=None)]
# h) Reihe endet am Vortag -> nichts
F["veraltet"] = [_z(k) for k in range(25, 0, -1)]
# i) Zeta ohne iv_atm und ohne Zeta-Felder am heutigen Tag -> keine Zeta, rr/iv ja
F["zeta_ohne_atm"] = [_z(k) for k in range(24, 0, -1)] + [dict(_z(0), iv_atm=None)]
# j) doppeltes Datum -> kein Rang (None)
F["doppelt"] = [_z(k) for k in range(24, -1, -1)] + [_z(3)]
# k) nicht normierte Zeilen zählen nicht (20 cm + 10 single -> n 20)
F["single"] = [_z(k) for k in range(19, -1, -1)] + [_z(k, cm="single") for k in range(30, 20, -1)]
# l) ungültige Werte: bool und Text zählen nicht als Messwert
F["ungueltig"] = [_z(k) for k in range(24, 0, -1)] + [dict(_z(0), skew_pts=True, call_iv="0.2")]
SOLL = {
    "steigend": ("rr", {"n": 25, "rank": 100, "pctl": 100}),
    "konstant": ("rr", {"n": 25, "rank": 50, "pctl": 0}),
    "pctl_halb": ("rr", {"n": 25, "rank": 50, "pctl": 13}),
    "halb": ("rr", {"n": 21, "rank": 50, "pctl": 50}),
    "n20": ("rr", {"n": 20, "rank": 50, "pctl": 0}),
    "grenze": ("rr", {"n": 21, "rank": 50, "pctl": 0}),
    "single": ("rr", {"n": 20, "rank": 50, "pctl": 0}),
}
for name, arr in F.items():
    r92 = rang_ticker(arr, S, 92)
    if name in SOLL:
        m, soll = SOLL[name]
        ist = {k: (r92 or {}).get(m, {}).get(k) for k in soll}
        pruef(f"{name}: {m} = {soll}", ist == soll, ist)
r = rang_ticker(F["steigend"], S, 92)
pruef("iv = Mittel der Flügel (steigt mit call_iv) -> Rank 100, nicht ATM (konstant)", r["iv"]["rank"] == 100, r["iv"])
pruef("n19: kein Rang", rang_ticker(F["n19"], S, 92) == {}, rang_ticker(F["n19"], S, 92))
r = rang_ticker(F["skew_fehlt"], S, 92)
pruef("skew fehlt heute: skew ohne Rang, rr/iv mit Rang (je Metrik eigenes n)", "skew" not in r and "rr" in r and "iv" in r,
      sorted(r))
pruef("Reihe endet am Vortag: nichts", rang_ticker(F["veraltet"], S, 92) == {})
r = rang_ticker(F["zeta_ohne_atm"], S, 92)
pruef("Zeta ohne iv_atm heute: keine Zeta, rr ja", "zeta" not in r and "rr" in r, sorted(r))
pruef("doppeltes Datum: None", rang_ticker(F["doppelt"], S, 92) is None)
r = rang_ticker(F["ungueltig"], S, 92)
pruef("bool/Text heute: skew und rr ohne Rang", "skew" not in r and "rr" not in r, sorted(r))
z = rang_ticker(F["steigend"], S, 365)["zeta"]
pruef("Zeta aus (IV − iv_atm)·100: cz Rank 100, pz konstant 50", (z["cz"]["rank"], z["pz"]["rank"]) == (100, 50), z)
# m) Duplikat nur im langen Fenster (S−100): der GANZE Ticker ohne Rang, auch kein 3-M-Rang, und eine Meldung
F["dup_lang"] = [_z(k) for k in range(24, -1, -1)] + [_z(100), _z(100)]
meld = []
rg = rang_gesamt({"DUP": F["dup_lang"]}, S, meld)
pruef("Duplikat nur bei S−100: Ticker ganz ohne Rang + Meldung", "DUP" not in rg and any("DUP" in m and "doppelt" in m for m in meld),
      (sorted(rg), meld))
# n) ungültige Daten zählen nicht: 19 gültige + „2026-08-99“ + Zeitstempel -> kein Rang, Meldung
F["datum_falsch"] = [_z(k) for k in range(18, -1, -1)] + [dict(_z(30), date="2026-08-99"), dict(_z(31), date=_tag(31) + "T10:00")]
pruef("ungültiges Datum hebt 19 Punkte nicht auf 20", rang_ticker(F["datum_falsch"], S, 92) == {})
pruef("ungültiges Datum wird gemeldet", any("ungültigem Datum" in m for m in pruefe_ticker(F["datum_falsch"], S)),
      pruefe_ticker(F["datum_falsch"], S))
# o) verschiedene Stichprobenumfänge je Metrik: skew fehlt an 3 früheren Tagen -> skew n 22, rr n 25
F["n_je_metrik"] = [dict(_z(k), skew_pts=None) if k in (20, 15, 10) else _z(k) for k in range(24, -1, -1)]
r = rang_ticker(F["n_je_metrik"], S, 92)
pruef("je Metrik eigenes n: rr 25, skew 22", (r["rr"]["n"], r["skew"]["n"]) == (25, 22), (r["rr"]["n"], r["skew"]["n"]))
hist = {f"T_{k}": v for k, v in F.items()}
hist["__CORR"] = [{"date": S}]
py, js = rang_gesamt(hist, S), _js(hist)
pruef("Python = JS-Referenz auf allen Fixtures", json.loads(json.dumps(py)) == js,
      js.get("_fehler") if isinstance(js, dict) and "_fehler" in js else "")

# ── 1b. B3b: IV/RV, neuer Rand, Sprung, Verfügbarkeit ─────────────────────────────────────────────────────────────
print("== B3b: ivrv, neu_rand, vorher_datum, sprung, rang_status")
from shared.skew_rang import ivrv_wert, rang_status_gesamt, status_ticker   # noqa: E402

pruef("ivrv_wert: rv genau 0,01 gilt", ivrv_wert(0.2, 0.01) == 0.2 / 0.01)
pruef("ivrv_wert: rv 0,0099 ungültig", ivrv_wert(0.2, 0.0099) is None)
pruef("ivrv_wert: iv 0 / bool / Text / NaN ungültig",
      [ivrv_wert(0.0, 0.2), ivrv_wert(True, 0.2), ivrv_wert(0.2, "0.2"), ivrv_wert(float("nan"), 0.2)] == [None] * 4)
G = {}
# IV/RV: 25 Tage rv 0,20, heute 0,11 → 2,0 gegen 1,1 → Rank/Pctl 100, neu_rand hoch, Median der Änderungen 0
G["ivrv_hoch"] = [_z(k, rv_1m=0.20) for k in range(24, 0, -1)] + [_z(0, rv_1m=0.11)]
# IV/RV nur auf Zeilen MIT gespeichertem rv_1m: 25 Tage, rv nur in den letzten 16 → zu_kurz, n 16
G["ivrv_kurz"] = [_z(k) for k in range(24, 15, -1)] + [_z(k, rv_1m=0.20) for k in range(15, -1, -1)]
# Skew: Wechsel 3,00/3,25 (|d| = 0,25), heute +1,25 (= 5·Median, kein Sprung) bzw. +1,5 (Sprung)
_wechsel = [_z(k, skew=3.0 if k % 2 else 3.25) for k in range(24, 0, -1)]      # k = 1 → 3,0
G["sprung_genau"] = _wechsel + [_z(0, skew=4.25)]
G["sprung_drueber"] = _wechsel + [_z(0, skew=4.5)]
# neuer Rand: Gleichstand mit früherem Maximum ist kein Rand; strikt darüber hoch; unter min tief
G["rand_gleich"] = [_z(k, skew=3.0) for k in range(24, -1, -1)]
G["rand_wdh_max"] = [_z(k, skew=5.0 if k == 10 else 3.0) for k in range(24, 0, -1)] + [_z(0, skew=5.0)]
G["rand_tief"] = [_z(k, skew=3.0 + k / 100) for k in range(24, 0, -1)] + [_z(0, skew=2.0)]
# 300 Punkte, heute der zweithöchste: Pctl 298/299 → 100 (gerundet), aber kein neuer Rand
G["rand_rundung"] = [_z(k, skew=3.0 + (300 - k) / 1000, basis=None) for k in range(299, 150, -1)] + \
                    [_z(k, skew=10.0 if k == 100 else 3.0 + (300 - k) / 1000) for k in range(150, 0, -1)] + [_z(0, skew=9.0)]
# vorher_datum über eine Lücke: skew fehlt gestern → Vorgänger ist S−2
G["luecke"] = [_z(k, skew=3.0 + k / 100) for k in range(24, 1, -1)] + [dict(_z(1), skew_pts=None), _z(0, skew=3.5)]
# kein_wert: heute fehlt skew, 24 gültige davor
# Median MIT aktueller Änderung: 9× |d| = 0, 9× |d| = 1, heute +3 → Median 1, kein Sprung (ohne die aktuelle: 0,5 → Sprung)
_v = [3.0]
for _i in range(18):
    _v.append(_v[-1] + (0 if _i % 2 == 0 else (1 if (_i // 2) % 2 == 0 else -1)))
_v.append(_v[-1] + 3)
G["median_mit_aktueller"] = [_z(19 - _i, skew=_x) for _i, _x in enumerate(_v)]
G["kein_wert"] =[_z(k) for k in range(24, 0, -1)] + [dict(_z(0), skew_pts=None)]
SOLL_B = {
    "ivrv_hoch": ("ivrv", {"n": 25, "rank": 100, "pctl": 100, "neu_rand": "hoch", "sprung_beurteilbar": False}),
    "sprung_genau": ("skew", {"n": 25, "sprung": None, "sprung_beurteilbar": None, "neu_rand": "hoch"}),
    "sprung_drueber": ("skew", {"n": 25, "sprung": True}),
    "rand_gleich": ("skew", {"neu_rand": None, "pctl": 0, "sprung_beurteilbar": False}),
    "rand_wdh_max": ("skew", {"neu_rand": None, "pctl": 96}),         # 23 von 24 Vorwerten darunter, einer gleich
    "rand_tief": ("skew", {"neu_rand": "tief", "pctl": 0}),
    "luecke": ("skew", {"vorher_datum": _tag(2), "n": 24}),
    "median_mit_aktueller": ("skew", {"n": 20, "sprung": None, "sprung_beurteilbar": None}),
}
for name, (m, soll) in SOLL_B.items():
    f = 365 if name == "rand_rundung" else 92
    r = (rang_ticker(G[name], S, f) or {}).get(m, {})
    ist = {k: r.get(k) for k in soll}
    pruef(f"{name}: {m} = {soll}", ist == soll, ist)
_w = ((rang_ticker(G["ivrv_hoch"], S, 92) or {}).get("ivrv") or {}).get("wert")
pruef("ivrv_hoch: Wert = iv_atm / rv_1m = 0,22 / 0,11 (ATM-IV, nicht die Flügel)",
      _w is not None and abs(_w - 0.22 / 0.11) < 1e-12, _w)
r = (rang_ticker(G["rand_rundung"], S, 365) or {}).get("skew", {})
pruef("rand_rundung: Pctl gerundet 100, trotzdem kein neuer Rand", r.get("pctl") == 100 and "neu_rand" not in r,
      {k: r.get(k) for k in ("pctl", "neu_rand", "n")})
pruef("ivrv_kurz: kein ivrv-Rang", "ivrv" not in (rang_ticker(G["ivrv_kurz"], S, 92) or {}))
pruef("ivrv_kurz: Status zu_kurz, n 16", status_ticker(G["ivrv_kurz"], S, 92).get("ivrv") == {"n": 16, "status": "zu_kurz"},
      status_ticker(G["ivrv_kurz"], S, 92).get("ivrv"))
pruef("kein_wert: Status kein_wert, n 24", status_ticker(G["kein_wert"], S, 92).get("skew") == {"n": 24, "status": "kein_wert"},
      status_ticker(G["kein_wert"], S, 92).get("skew"))
pruef("Ticker mit Rang in allen Metriken: kein Statuseintrag dafür",
      "skew" not in status_ticker(G["sprung_drueber"], S, 92), status_ticker(G["sprung_drueber"], S, 92))
pruef("Duplikat: Status gesperrt", status_ticker(F["doppelt"], S, 92) == {"*": {"status": "gesperrt"}})
pruef("ohne normierte Zeile: kein Statuseintrag", rang_status_gesamt({"X": [_z(0, cm="single")]}, S) == {})
pruef("ohne rv_1m: ivrv kein_wert (keine Rückrechnung aus vrp_pts)",
      status_ticker([_z(k, vrp_pts=2.0) for k in range(24, -1, -1)], S, 92).get("ivrv") == {"n": 0, "status": "kein_wert"})
hist_b = {f"T_{k}": v for k, v in {**F, **G}.items()}
f2 = _TMP / "ein_status.json"
f2.write_text(json.dumps({"hist": hist_b, "session": S, "mit_status": True}), encoding="utf-8")
r2 = subprocess.run(["node", str(_ROOT / "scripts/js/skew_rang_ref.js"), str(f2)], capture_output=True, text=True,
                    encoding="utf-8")
js2 = json.loads(r2.stdout) if r2.returncode == 0 else {"_fehler": r2.stderr[-300:]}
py2 = json.loads(json.dumps({"rang": rang_gesamt(hist_b, S), "status": rang_status_gesamt(hist_b, S)}))
pruef("Python = JS-Referenz mit B3b-Feldern und Status", py2 == js2, js2.get("_fehler", ""))

# ── 2. Cron ───────────────────────────────────────────────────────────────────────────────────────────────────────
print("== compute_options_skew.build schreibt rang")
import shared.exchange_holidays as eh                                    # noqa: E402
import scripts.compute_options_skew as cs                                # noqa: E402

eh._uhr = lambda tz: datetime(2026, 10, 9, 23, 0, tzinfo=UTC).astimezone(tz)
cs._index_series = lambda *a, **k: None
cs._enrich = lambda sym, key=None: {
    "ticker": sym, "cats": ["Broad-Index"], "underlying": 700.0, "dte": 21, "put_vol": 1, "call_vol": 1,
    "put_oi": 1, "call_oi": 1, "call_25d": {"strike": 720, "iv": 0.19, "delta": 0.25},
    "put_25d": {"strike": 680, "iv": 0.22, "delta": -0.25}, "skew_pts": 3.0, "iv_atm": 0.20, "rv_1m": 0.18,
    "cm_mode": "cm", "cm_dte": 30, "cm_skew_pts": 9.0, "cm_put_iv": 0.30, "cm_call_iv": 0.20, "cm_iv_atm": 0.22,
    "cm_bfly_pts": 0.5, "cm_call_zeta_pts": -2.0, "cm_put_zeta_pts": 8.0}
w = _TMP / "cron"
(w / "landing/data").mkdir(parents=True)
_ht = [k for k in range(1, 60) if eh.is_trading_day(date.fromisoformat(_tag(k, SC)), "NYSE")][:30]   # 30 Handelstage vor SC
(w / "landing/data/options_skew_history.json").write_text(json.dumps(
    {"SPY": [_z(k, skew=3.0, basis=SC) for k in sorted(_ht, reverse=True)]}), encoding="utf-8")
cs._ROOT = w
with contextlib.redirect_stdout(io.StringIO()):
    out = cs.build(["SPY"], write=True)
snap = json.loads((w / "landing/data/options_skew.json").read_text(encoding="utf-8"))
r = ((snap.get("rang") or {}).get("SPY") or {}).get("365") or {}
pruef("Snapshot trägt rang_session = session", snap.get("rang_session") == snap.get("session") == SC,
      (snap.get("rang_session"), snap.get("session")))
pruef("Rang enthält den heutigen Punkt (skew 9 > alle 3 → Rank 100, n 31)",
      (r.get("skew") or {}).get("rank") == 100 and (r.get("skew") or {}).get("n") == 31, r.get("skew"))
_hist_c = json.loads((w / "landing/data/options_skew_history.json").read_text(encoding="utf-8"))
_heute = [e for e in _hist_c["SPY"] if e.get("date") == SC]
pruef("B3b: neue History-Zeile trägt rv_1m (0,18)", len(_heute) == 1 and _heute[0].get("rv_1m") == 0.18, _heute)
_t = (snap.get("tickers") or [{}])[0]
pruef("B3b: Snapshot ivrv = cm_iv_atm / rv_1m = 0,22/0,18", _t.get("ivrv") == round(0.22 / 0.18, 4), _t.get("ivrv"))
_enrich_cm = cs._enrich
cs._enrich = lambda sym, key=None: dict(_enrich_cm(sym, key), cm_mode="single")    # gültige cm_iv_atm, aber single
w3 = _TMP / "cron_single"
(w3 / "landing/data").mkdir(parents=True)
(w3 / "landing/data/options_skew_history.json").write_text(json.dumps(
    {"SPY": [_z(k, skew=3.0, basis=SC) for k in sorted(_ht, reverse=True)]}), encoding="utf-8")
cs._ROOT = w3
with contextlib.redirect_stdout(io.StringIO()):
    cs.build(["SPY"], write=True)
cs._enrich = _enrich_cm
_s3 = json.loads((w3 / "landing/data/options_skew.json").read_text(encoding="utf-8"))
_h3 = [e for e in json.loads((w3 / "landing/data/options_skew_history.json").read_text(encoding="utf-8"))["SPY"]
       if e.get("date") == SC]
pruef("B3b: single mit gültiger ATM-IV → kein ivrv im Snapshot, kein rv_1m in der History",
      (_s3.get("tickers") or [{}])[0].get("ivrv") is None and len(_h3) == 1 and _h3[0].get("rv_1m") is None,
      ((_s3.get("tickers") or [{}])[0].get("ivrv"), _h3))
pruef("B3b: rang_status — ivrv mit einem Wert zu kurz (n 1)",
      ((snap.get("rang_status") or {}).get("SPY") or {}).get("365", {}).get("ivrv") == {"n": 1, "status": "zu_kurz"},
      (snap.get("rang_status") or {}).get("SPY"))

# Abbruch zwischen History- und Snapshot-Schreiben: neue History, alter Snapshot bleibt in sich konsistent
w2 = _TMP / "cron_abbruch"
(w2 / "landing/data").mkdir(parents=True)
(w2 / "landing/data/options_skew_history.json").write_text(json.dumps(
    {"SPY": [_z(k, skew=3.0, basis=SC) for k in sorted(_ht, reverse=True)]}), encoding="utf-8")
alt_snap = {"session": "2026-10-08", "rang_session": "2026-10-08", "rang": {}, "tickers": []}
(w2 / "landing/data/options_skew.json").write_text(json.dumps(alt_snap), encoding="utf-8")
cs._ROOT = w2
_echt = cs.write_json_atomic


def _bricht_beim_snapshot(pfad, obj, **k):
    if str(pfad).endswith("options_skew.json"):
        raise OSError("Abbruch beim Snapshot (Probe)")
    return _echt(pfad, obj, **k)


cs.write_json_atomic = _bricht_beim_snapshot
try:
    with contextlib.redirect_stdout(io.StringIO()):
        cs.build(["SPY"], write=True)
    abbruch = "lief durch"
except OSError:
    abbruch = "OSError"
finally:
    cs.write_json_atomic = _echt
h2 = json.loads((w2 / "landing/data/options_skew_history.json").read_text(encoding="utf-8"))
s2 = json.loads((w2 / "landing/data/options_skew.json").read_text(encoding="utf-8"))
pruef("Abbruch beim Snapshot: History neu (mit SC), Snapshot alt und in sich konsistent",
      abbruch == "OSError" and any(e.get("date") == SC for e in h2["SPY"]) and s2 == alt_snap
      and s2["rang_session"] == s2["session"], abbruch)

# ── 3. Seite ──────────────────────────────────────────────────────────────────────────────────────────────────────
print("== /skew liest den Rang (echtes Seiten-JS)")
import re as _re


def _tabelle(o):
    """{ticker: (IV-Rang-Zelle, Skew-Rang-Zelle)} aus dem Tabellen-HTML der Seite (Spalten 2 und 4)."""
    out = {}
    for tk, zeile in _re.findall(r'<tr data-tk="([^"]+)">(.*?)</tr>', o.get("tabelle") or ""):
        zellen = [_re.sub(r"<[^>]+>", "", z) for z in _re.findall(r"<td[^>]*>(.*?)</td>", zeile)]
        out[tk] = (zellen[2], zellen[4]) if len(zellen) > 4 else None
    return out


seite = {"session": S, "rang_session": S, "categories": ["X"], "tickers": [
    {"ticker": t, "cats": ["X"], "skew_pts": 1.0} for t in ("A", "B")],
    "rang": {"A": {"365": {"rr": {"n": 30, "rank": 11, "pctl": 22, "wert": 0.1}, "iv": {"n": 30, "rank": 33, "pctl": 44, "wert": 0.2},
                           "skew": {"n": 28, "rank": 91, "pctl": 92, "wert": 3.0},
                           "zeta": {"n": 30, "cz": {"rank": 55, "pctl": 66, "wert": 1}, "pz": {"rank": 77, "pctl": 88, "wert": 2}}},
                   "92": {"rr": {"n": 25, "rank": 1, "pctl": 2, "wert": 0.1}, "iv": {"n": 25, "rank": 3, "pctl": 4, "wert": 0.2}}},
             "B": {"92": {"rr": {"n": 25, "rank": 5, "pctl": 6, "wert": 0.1}, "iv": {"n": 25, "rank": 7, "pctl": 8, "wert": 0.2}}}}}


def _seite(snapshot, *argv):
    f = _TMP / "snap.json"
    f.write_text(json.dumps(snapshot), encoding="utf-8")
    r = subprocess.run(["node", str(_ROOT / "scripts/js/probe_skew_rang_seite.js"), str(f), *argv], capture_output=True,
                       text=True, encoding="utf-8")
    try:
        return json.loads(r.stdout)
    except Exception:
        return {"punkte": None, "fehler": r.stderr[-300:]}


def _p(o):
    return sorted((p["tk"], p["x"], p["y"]) for p in (o.get("punkte") or []))


pruef("Percentile, 1 J., RR×IV: A = (22, 44), B ohne 1-J-Rang fehlt", _p(_seite(seite, "pctl", "rr_iv", "365")) == [("A", 22, 44)],
      _p(_seite(seite, "pctl", "rr_iv", "365")))
# Seit 2026-10-17 fest 1 J. + Percentile (Schalter entfernt): ein Wunsch nach Rank oder 3 M. ändert nichts.
pruef("ohne Rank-Schalter: Wunsch „rank“ zeigt weiter Percentile A = (22, 44)",
      _p(_seite(seite, "rank", "rr_iv", "365")) == [("A", 22, 44)], _p(_seite(seite, "rank", "rr_iv", "365")))
pruef("ohne Fenster-Schalter: Wunsch „92“ zeigt weiter 1 J. (B ohne 1-J-Rang fehlt)",
      _p(_seite(seite, "pctl", "rr_iv", "92")) == [("A", 22, 44)], _p(_seite(seite, "pctl", "rr_iv", "92")))
pruef("Call/Put-Skew, Percentile, 1 J.: A = (66, 88)", _p(_seite(seite, "pctl", "cs_ps", "365")) == [("A", 66, 88)])
alt = dict(seite, rang_session="2026-10-15")
pruef("rang_session ≠ session: kein Punkt", _p(_seite(alt, "pctl", "rr_iv", "365")) == [])
t = _tabelle(_seite(seite, "pctl", "rr_iv", "365"))
pruef("Tabelle Percentile 1 J.: A IV 44%, Skew 92%; B —/—", (t.get("A"), t.get("B")) == (("44%", "92%"), ("—", "—")), t)
t = _tabelle(_seite(seite, "rank", "rr_iv", "92"))
pruef("Tabelle ohne Schalter: Wunsch Rank/3 M. zeigt Percentile 1 J. (A 44%/92%, B —/—)",
      (t.get("A"), t.get("B")) == (("44%", "92%"), ("—", "—")), t)
_o = _seite(seite, "pctl", "rr_iv", "365")
_stand = _re.sub(r"<[^>]+>", "", _o.get("stand") or "")
pruef("Zeile unter dem Radar: Aktualisierung, Session, „1 von 2 Tickern“, B mit Grund",
      "Letzte Aktualisierung" in _stand and "18.09.2026" in _stand and "1 von 2 Tickern" in _stand
      and "1 ohne Wert" in _stand and "B keine 30-Tage-Messung" in _stand, _stand)
_o = _seite(dict(seite, coverage={"failed": [{"ticker": "C", "reason": "x"}]},
                 rang_status={"B": {"365": {"rr": {"n": 7, "status": "zu_kurz"}}}}), "pctl", "rr_iv", "365")
_stand = _re.sub(r"<[^>]+>", "", _o.get("stand") or "")
pruef("Zeile unter dem Radar: gescheiterter Ticker zählt mit, Gründe „zu kurz (n = 7)“ und „keine Kette“",
      "1 von 3 Tickern" in _stand and "B zu kurze Historie (n = 7)" in _stand
      and "C keine auswertbare Optionskette" in _stand, _stand)
# Kategorie X: gescheiterter Ticker mit cats ["X"] zählt mit, einer mit ["Y"] nicht (Codex R1: „20 von 26“ statt 28)
_ks = dict(seite, categories=["X", "Y"], coverage={"failed": [{"ticker": "C", "cats": ["X"], "reason": "x"},
                                                              {"ticker": "D", "cats": ["Y"], "reason": "x"}]})
os.environ["SA_PROBE_KAT"] = "X"
_stand = _re.sub(r"<[^>]+>", "", _seite(_ks, "pctl", "rr_iv", "365").get("stand") or "")
del os.environ["SA_PROBE_KAT"]
pruef("Zeile unter dem Radar, Kategorie X: gescheitertes C (X) zählt mit, D (Y) nicht",
      "1 von 3 Tickern" in _stand and "C keine auswertbare Optionskette" in _stand and "D " not in _stand, _stand)
# Zweiter Lauf derselben Session: C ist gescheitert, sein Rang aus dem ersten Lauf steht noch in rang (Codex R2)
_zl = json.loads(json.dumps(seite))
_zl["rang"]["C"] = {"365": {"rr": {"n": 30, "rank": 5, "pctl": 6, "wert": 0.1}, "iv": {"n": 30, "rank": 7, "pctl": 8, "wert": 0.2}}}
_zl["coverage"] = {"failed": [{"ticker": "C", "cats": ["X"], "reason": "x"}]}
_o = _seite(_zl, "pctl", "rr_iv", "365")
_stand = _re.sub(r"<[^>]+>", "", _o.get("stand") or "")
pruef("gescheiterter Ticker mit altem Rang derselben Session: nicht im Radar, nicht in Extremlisten, in der Fehlliste",
      _p(_o) == [("A", 22, 44)] and 'data-tk="C"' not in (_o.get("extrem") or "") and "1 von 3 Tickern" in _stand
      and "C keine auswertbare Optionskette" in _stand, (_p(_o), _stand))
_stand = _re.sub(r"<[^>]+>", "", _seite(alt, "pctl", "rr_iv", "365").get("stand") or "")
pruef("Zeile unter dem Radar bei rang_session ≠ session: Hinweis, keine Fehlliste",
      "noch nicht vor" in _stand and "ohne Wert" not in _stand and "Letzte Aktualisierung" in _stand, _stand)
t = _tabelle(_seite(alt, "pctl", "rr_iv", "365"))
pruef("Tabelle bei rang_session ≠ session: —", t.get("A") == ("—", "—"), t.get("A"))
t = _tabelle(_seite({k: v for k, v in seite.items() if k not in ("rang", "rang_session")}, "pctl", "rr_iv", "365"))
pruef("Tabelle ohne rang (Altdatei): —", t.get("A") == ("—", "—"), t.get("A"))

# Leser von B3a: Radar und bestehende Spalten mit B3b-Zusatzfeldern + rang_status unverändert
seite_b3b = json.loads(json.dumps(seite))
for _je in seite_b3b["rang"].values():
    for _f in _je.values():
        for _m in ("rr", "iv", "skew"):
            if _m in _f:
                _f[_m].update(neu_rand="tief", sprung=True, vorher_datum="2026-10-01")
seite_b3b["rang_status"] = {"B": {"365": {"skew": {"n": 4, "status": "zu_kurz"}}}}
for _arg in (("pctl", "rr_iv", "365"), ("pctl", "cs_ps", "365")):
    _a, _b = _seite(seite, *_arg), _seite(seite_b3b, *_arg)
    pruef(f"B3a-Leser mit B3b-Feldern unverändert ({' '.join(_arg)}): Radar + IV-/Skew-Rangspalten",
          _p(_a) == _p(_b) and _tabelle(_a) == _tabelle(_b), (_p(_b), _tabelle(_b)))

# ── 3b. /skew: Extremlisten und IV/RV-Spalte (B3b) ────────────────────────────────────────────────────────────────
print("== /skew: Am Rand der eigenen Historie + IV/RV (echtes Seiten-JS)")


def _listen(o):
    """{metrik: {"hoch": [tk…], "tief": [tk…]}} + {tk: Markierungstext} aus dem Block."""
    html, out, mark = o.get("extrem") or "", {}, {}
    for m, s, inhalt in _re.findall(r'<table class="sk-tbl sk-ex" data-m="([^"]+)" data-s="([^"]+)">(.*?)</table>', html):
        out.setdefault(m, {})[s] = _re.findall(r'<tr data-tk="([^"]+)">', inhalt)
        for tk, zeile in _re.findall(r'<tr data-tk="([^"]+)">(.*?)</tr>', inhalt):
            mark[(m, tk)] = _re.sub(r"<[^>]+>", "", zeile)
    return out, mark, html


def _r(n, rank, pctl, wert, **z):
    return dict(n=n, rank=rank, pctl=pctl, wert=wert, **z)


TK = [f"T{i:02d}" for i in range(18)]
rang_ex = {}
for i, tk in enumerate(TK):
    rang_ex[tk] = {"365": {
        # iv: Percentile i·5, Rank umgekehrt (prüft: Listen nach Percentile, Schalter ändert sie nicht)
        "iv": _r(30, 100 - i * 5, i * 5, 0.2 + i / 100),
        # skew: alle 18 mit gleichem Percentile 50 → Gleichstand nach Ticker, keine Überschneidung
        "skew": _r(30, 50, 50, 3.0)}}
rang_ex["T17"]["365"]["iv"].update(neu_rand="hoch", sprung=True, vorher_datum="2026-10-12")
rang_ex["T00"]["365"]["iv"].update(neu_rand="tief")
seite_ex = {"session": S, "rang_session": S, "categories": ["X", "Y"],
            "tickers": [{"ticker": t, "cats": ["X"] if i < 12 else ["Y"], "skew_pts": 1.0, "ivrv": 1.25 if t == "T03" else None}
                        for i, t in enumerate(TK)],
            "rang": rang_ex,
            "rang_status": {"T03": {"365": {"ivrv": {"n": 16, "status": "zu_kurz"}}},
                            "T04": {"365": {"*": {"status": "gesperrt"}}}}}
L, mk, html = _listen(_seite(seite_ex, "pctl", "rr_iv", "365"))
pruef("iv hoch: T17…T10 (Percentile absteigend)", L.get("iv", {}).get("hoch") == [f"T{i:02d}" for i in range(17, 9, -1)],
      L.get("iv", {}).get("hoch"))
pruef("iv tief: T00…T07 (aufsteigend)", L.get("iv", {}).get("tief") == [f"T{i:02d}" for i in range(8)], L.get("iv", {}).get("tief"))
pruef("skew, 18 Gleichstände: hoch T00–T07, tief T08–T15 (Ticker-Folge, keine Überschneidung)",
      L.get("skew", {}).get("hoch") == TK[:8] and L.get("skew", {}).get("tief") == TK[8:16],
      (L.get("skew", {}).get("hoch"), L.get("skew", {}).get("tief")))
pruef("Markierung neues Hoch + Sprung mit Datum (T17), Ticker bleibt in der Liste",
      "neues Hoch" in mk.get(("iv", "T17"), "") and "Sprung" in mk.get(("iv", "T17"), "") and "2026-10-12" in mk.get(("iv", "T17"), ""),
      mk.get(("iv", "T17")))
pruef("Markierung neues Tief (T00)", "neues Tief" in mk.get(("iv", "T00"), ""), mk.get(("iv", "T00")))
pruef("IV/RV ohne Rang: Hinweis „Rang im Aufbau“", "Rang im Aufbau" in html)
pruef("Hinweis „kein Signal“ und Datenstand der Session", "kein Signal" in html and S in html)
pruef("Werte: iv als %, Percentile „85 %“ und „30 Tage“", "85 %" in mk.get(("iv", "T17"), "")
      and "30 Tage" in mk.get(("iv", "T17"), "") and "P85" not in mk.get(("iv", "T17"), "")
      and "%" in mk.get(("iv", "T17"), ""), mk.get(("iv", "T17")))
L2, _, _ = _listen(_seite(seite_ex, "pctl", "cs_ps", "365"))
pruef("Darstellungs-Schalter ändert die Listen nicht", L2 == L, (L2.get("iv"), L.get("iv")))
_alt_env = os.environ.get("SA_PROBE_KAT")
os.environ["SA_PROBE_KAT"] = "Y"
L3, _, _ = _listen(_seite(seite_ex, "pctl", "rr_iv", "365"))
del os.environ["SA_PROBE_KAT"]
pruef("Kategorie Y: nur T12–T17", L3.get("iv", {}).get("hoch") == [f"T{i:02d}" for i in range(17, 11, -1)]
      and L3.get("iv", {}).get("tief") == [], L3.get("iv"))
o = _seite(seite_ex, "pctl", "rr_iv", "365")
zellen = dict(_re.findall(r'<tr data-tk="(T0[34])">(.*?)</tr>', o.get("tabelle") or ""))
pruef("IV/RV-Zelle: Wert 1.25× mit Status-Tooltip „ab 20 gültigen Beobachtungen (n = 16)“",
      "1.25×" in zellen.get("T03", "") and "n = 16" in zellen.get("T03", ""), zellen.get("T03", "")[:400])
pruef("IV/RV-Zelle gesperrter Ticker: Tooltip „gesperrt“", "gesperrt" in zellen.get("T04", ""), zellen.get("T04", "")[:300])
zweiter = dict(seite_ex, rang={"Z1": {"365": {"iv": _r(30, 1, 99, 0.3)}}}, tickers=[{"ticker": "Z1", "cats": ["X"], "skew_pts": 1.0}],
               rang_status={})
f_zw = _TMP / "snap_zweiter.json"
f_zw.write_text(json.dumps(zweiter), encoding="utf-8")
os.environ["SA_PROBE_ZWEITER"] = str(f_zw)
L4, _, html4 = _listen(_seite(seite_ex, "pctl", "rr_iv", "365"))
del os.environ["SA_PROBE_ZWEITER"]
pruef("zweiter Snapshot im selben DOM: nur Z1, keine alten Einträge", L4.get("iv", {}).get("hoch") == ["Z1"]
      and "T17" not in html4, L4.get("iv"))
os.environ["SA_PROBE_I18N"] = "1"
_oe = _seite(seite_ex, "pctl", "rr_iv", "365")
del os.environ["SA_PROBE_I18N"]
_le, _mke, _he = _listen(_oe)
pruef("Sprachwechsel (sa:i18n-bereit): Block englisch neu gezeichnet, Listen gleich",
      "At the edge of their own history" in _he and "not a signal" in _he and "Am Rand" not in _he
      and "new high in the window" in _mke.get(("iv", "T17"), "") and _le == L, _he[:200])
_ze = dict(_re.findall(r'<tr data-tk="(T03)">(.*?)</tr>', _oe.get("tabelle") or ""))
pruef("Sprachwechsel: IV/RV-Tooltip englisch", "Rank from 20 valid observations (n = 16)" in _ze.get("T03", ""),
      _ze.get("T03", "")[:300])
L5, _, html5 = _listen(_seite(dict(seite_ex, rang_session="2026-10-15"), "pctl", "rr_iv", "365"))
pruef("rang_session ≠ session: Block leer", html5 == "", html5[:120])
_o5 = _seite(dict(seite_ex, rang_session="2026-10-15"), "pctl", "rr_iv", "365")
_z5 = dict(_re.findall(r'<tr data-tk="(T03)">(.*?)</tr>', _o5.get("tabelle") or ""))
pruef("rang_session ≠ session: IV/RV-Zelle ohne Status-Tooltip", "n = 16" not in _z5.get("T03", "x n = 16"),
      _z5.get("T03", "")[:200])
pruef("Altdatei ohne rang/rang_status: Block leer",
      _listen(_seite({k: v for k, v in seite_ex.items() if k not in ("rang", "rang_status", "rang_session")},
                     "pctl", "rr_iv", "365"))[2] == "")
if _alt_env is not None:
    os.environ["SA_PROBE_KAT"] = _alt_env

# ── 4. Mail ───────────────────────────────────────────────────────────────────────────────────────────────────────
print("== Mail: skew_pctl_map + Vorlage")
import shared.daily_report as dr                                         # noqa: E402

mail_snap = {"session": "2026-10-15", "rang_session": "2026-10-15", "tickers": [],
             "rang": {"SPY": {"365": {"skew": {"n": 200, "rank": 70, "pctl": 81, "wert": 3.1}},
                              "92": {"skew": {"n": 60, "rank": 10, "pctl": 12, "wert": 3.1}}},
                      "QQQ": {"92": {"skew": {"n": 60, "rank": 10, "pctl": 12, "wert": 3.1}}}}}


def _mail(snapshot, jetzt):
    f = _TMP / "mail_snap.json"
    f.write_text(json.dumps(snapshot), encoding="utf-8")
    dr._SNAPSHOT_PFAD, dr._SKEW_PCTL_MAP = f, None
    eh._uhr = lambda tz: jetzt.astimezone(tz)
    return dr.skew_pctl_map()


VERSAND = datetime(2026, 10, 16, 5, 30, tzinfo=UTC)       # Fr 07:30 Berlin, erwartete Session Do 15.10.
pruef("Rang der erwarteten Session: SPY 81 (1 J.), QQQ ohne 1-J-Rang fehlt", _mail(mail_snap, VERSAND) == {"SPY": 81},
      _mail(mail_snap, VERSAND))
pruef("Snapshot einer älteren Session: leer", _mail(dict(mail_snap, session="2026-10-14", rang_session="2026-10-14"),
                                                    VERSAND) == {})
pruef("rang_session ≠ session: leer", _mail(dict(mail_snap, rang_session="2026-10-14"), VERSAND) == {})
_b3b = json.loads(json.dumps(mail_snap))
for _je in _b3b["rang"].values():
    for _f in _je.values():
        _f["skew"].update(neu_rand="hoch", sprung=True, vorher_datum="2026-10-14")
        _f["ivrv"] = {"n": 20, "rank": 1, "pctl": 2, "wert": 1.3, "sprung_beurteilbar": False}
_b3b["rang_status"] = {"SPY": {"365": {"ivrv": {"n": 3, "status": "zu_kurz"}}}, "DIA": {"365": {"*": {"status": "gesperrt"}}}}
pruef("Mail mit B3b-Zusatzfeldern und rang_status: identisch zu B3a", _mail(_b3b, VERSAND) == _mail(mail_snap, VERSAND),
      (_mail(_b3b, VERSAND), _mail(mail_snap, VERSAND)))
vorlage = (_ROOT / "scripts/templates/daily_report.html.j2").read_text(encoding="utf-8")
zeile = next((l for l in vorlage.splitlines() if "r.skew_pts" in l), "")
pruef("Vorlage: Skew-Zelle einfarbig (class nu), fehlendes Perzentil als „P—“",
      'class="nu"' in zeile and "P—" in zeile and "'up'" not in zeile and "'dn'" not in zeile)

shutil.rmtree(_TMP, ignore_errors=True)
print()
if FEHLER:
    print(f"[FAIL] {len(FEHLER)} Prüfung(en): " + "; ".join(FEHLER))
    sys.exit(1)
print("[OK] alle Prüfungen grün")
