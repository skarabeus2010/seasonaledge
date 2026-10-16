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
pruef("Rank, 1 J.: A = (11, 33)", _p(_seite(seite, "rank", "rr_iv", "365")) == [("A", 11, 33)])
pruef("Percentile, 3 M.: A (2, 4), B (6, 8)", _p(_seite(seite, "pctl", "rr_iv", "92")) == [("A", 2, 4), ("B", 6, 8)])
pruef("Call/Put-Skew, Percentile, 1 J.: A = (66, 88)", _p(_seite(seite, "pctl", "cs_ps", "365")) == [("A", 66, 88)])
alt = dict(seite, rang_session="2026-10-15")
pruef("rang_session ≠ session: kein Punkt", _p(_seite(alt, "pctl", "rr_iv", "365")) == [])
t = _tabelle(_seite(seite, "pctl", "rr_iv", "365"))
pruef("Tabelle Percentile 1 J.: A IV 44%, Skew 92%; B —/—", (t.get("A"), t.get("B")) == (("44%", "92%"), ("—", "—")), t)
t = _tabelle(_seite(seite, "rank", "rr_iv", "365"))
pruef("Tabelle Rank 1 J.: A IV 33%, Skew 91%", t.get("A") == ("33%", "91%"), t.get("A"))
t = _tabelle(_seite(seite, "pctl", "rr_iv", "92"))
pruef("Tabelle Percentile 3 M.: A IV 4%, B IV 8%, Skew ohne 3-M-Rang —", (t.get("A"), t.get("B")) == (("4%", "—"), ("8%", "—")), t)
t = _tabelle(_seite(alt, "pctl", "rr_iv", "365"))
pruef("Tabelle bei rang_session ≠ session: —", t.get("A") == ("—", "—"), t.get("A"))
t = _tabelle(_seite({k: v for k, v in seite.items() if k not in ("rang", "rang_session")}, "pctl", "rr_iv", "365"))
pruef("Tabelle ohne rang (Altdatei): —", t.get("A") == ("—", "—"), t.get("A"))

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
