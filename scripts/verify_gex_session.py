#!/usr/bin/env python3
"""
verify_gex_session.py — Session als Stempel UND Bewertungsdatum der Options-Erzeuger
(Plan docs/review_prompts/2026-10-14_options_sofortreparaturen_plan_v3.md / _v4.md, Paket B2).

Anlass (belegt 2026-10-14): der GEX-Cron (GitHub, 22:15 UTC) startete nach Mitternacht UTC und stempelte den Lauftag —
das Archiv lag eine Session daneben, und DTE/T sowie der Ausschluss verfallener Kontrakte hingen von der Startzeit ab.

Geprüft an den ECHTEN Funktionen, ersetzt sind nur Netz (`_get`), Uhr (`exchange_holidays._uhr`) und Ausgabeordner:
  * snapshot_gex_massive: Lauf 22:30 UTC und 01:30 UTC derselben Session (Freitag mit Wochenverfall) → identische
    Ausgabe ohne Laufzeitfelder; DTE ab Session, Verfall ≤ Session draußen; Spot-Balken eines anderen Tages verworfen;
    Archiv nur in gex_history_session/; Lauf in der Handelszeit → Exit 2 ohne Abruf, ohne Datei
  * compute_key_levels: GEX nur zur selben Session (fehlt/alter Stempel/andere Session → keine Walls, Status gesetzt),
    DTE ab Session, Handelszeit → MarktOffen ohne Abruf
  * compute_iv_surface: DTE ab Session, Handelszeit → MarktOffen ohne Abruf
  * compute_options_skew: pc_ratio.date = Session
  * compare_flashalpha_gex._from_snapshot: Session-Archiv zuerst, Lauftag-Archiv als gekennzeichneter Rückfall
  * daily_health_check._gex_bewertung: Sessions statt Kalendertage, schlechter aus Abdeckung und Frische
  * snapshot_gex.main (Yahoo): stillgelegt, schreibt nichts
Exit 0 grün, 1 rot, 3 Absturz (kein Nachweis).
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import types
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.dont_write_bytecode = True
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "scripts"))
_TMP = Path(tempfile.mkdtemp(prefix="sa_gexsession_"))
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

import shared.exchange_holidays as eh                                    # noqa: E402
from shared.exchange_holidays import MarktOffen                          # noqa: E402

UTC = ZoneInfo("UTC")
FEHLER = []
S = date(2026, 10, 16)                                   # Freitag, Monatsverfall (3. Freitag)
NACH_SCHLUSS = datetime(2026, 10, 16, 22, 30, tzinfo=UTC)
NACH_MITTERNACHT = datetime(2026, 10, 17, 1, 30, tzinfo=UTC)
HANDELSZEIT = datetime(2026, 10, 16, 14, 0, tzinfo=UTC)
VERFAELLE = [S, S + timedelta(days=7), S + timedelta(days=14), S + timedelta(days=28)]


def pruef(name, ok, info=""):
    print(f"  {'ok  ' if ok else 'FAIL'} {name}" + (f"  ->  {info}" if info else ""))
    if not ok:
        FEHLER.append(name)


def _uhr(jetzt):
    eh._uhr = lambda tz: jetzt.astimezone(tz)


def _ruhig(fn, *a, **k):
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return fn(*a, **k)


def _kette(spot=700.0):
    out = []
    for ex in VERFAELLE:
        for k in range(650, 751, 5):
            for typ in ("call", "put"):
                m = (k - spot) / spot
                iv = 0.20 + (0.3 * m * m) + (0.02 if typ == "put" else 0.0)
                delta = 0.5 - m * 4 if typ == "call" else -0.5 - m * 4
                out.append({"details": {"expiration_date": ex.isoformat(), "contract_type": typ,
                                        "strike_price": float(k)},
                            "open_interest": 1000 + abs(k - 700) * 20, "implied_volatility": iv,
                            "greeks": {"delta": max(-0.99, min(0.99, delta)), "gamma": 0.01},
                            "day": {"volume": 10}, "underlying_asset": {"price": spot}})
    return out


class _Netz:
    """Attrappe für `_get`: Tagesbalken (range/1/day/<d>/<d>) und Options-Snapshot. Zählt Abrufe."""
    def __init__(self, falscher_tag=()):
        self.abrufe, self.falsch = [], set(falscher_tag)

    def __call__(self, url, key, tries=5):
        self.abrufe.append(url)
        if "/v3/snapshot/options/" in url:
            return {"status": "OK", "results": _kette(), "next_url": None}
        raise AssertionError("unerwarteter Abruf " + url)


def _ohne_laufzeit(obj):
    if isinstance(obj, dict):
        return {k: _ohne_laufzeit(v) for k, v in obj.items() if k not in ("generated_at", "generated")}
    if isinstance(obj, list):
        return [_ohne_laufzeit(x) for x in obj]
    return obj


def _ordner(name):
    d = _TMP / name
    d.mkdir(parents=True, exist_ok=True)
    return d


def _alle(d: Path):
    return sorted(str(p.relative_to(d)).replace("\\", "/") for p in d.rglob("*") if p.is_file())


# ── 1. snapshot_gex_massive ───────────────────────────────────────────────────────────────────────────────────────
print("== snapshot_gex_massive")
import snapshot_gex_massive as gm                                        # noqa: E402

gm.gc = types.SimpleNamespace(collect=lambda: 0)
_FALSCHER_TAG = set()                       # Ticker ohne Tagesbalken der Session (für ganze Läufe)
_ART = {}                                   # Ticker -> Sonderfall der Yahoo-Antwort (siehe _yahoo)


def _yahoo(sym, params, timeout, session=None):
    """Attrappe für shared.yahoo_downloader._fetch_yahoo. Normalfall: Tagesbalken (09:30 New York) bis zur Session,
    close 700 / adjclose 700, regularMarketTime = Sessionschluss 16:00. Sonderfälle über _ART[sym]:
      kein_balken      Reihe endet am Vortag              vor_session  letzter Handel am Vortag 16:00
      intraday         letzter Handel Sessiontag 14:00    rmt_fehlt    kein regularMarketTime
      folgetag         Balken S+1 mit close 999, letzter Handel S+1 10:00 (Spot muss der Sessionbalken sein)
      close_ungueltig  close der Session None             bereinigt    adjclose 690 (Spot muss close 700 sein)
      halbtag_13       letzter Handel 13:00 (für einen Halbtag richtig, sonst zu früh)"""
    ny = ZoneInfo("America/New_York")
    s = session or S
    art = _ART.get(sym, "")
    ende = s - timedelta(days=1) if (sym in _FALSCHER_TAG or art == "kein_balken") else s
    tage = [s - timedelta(days=k) for k in range(6, -1, -1) if s - timedelta(days=k) <= ende]
    closes = [700.0] * len(tage)
    if art == "folgetag":
        tage.append(s + timedelta(days=1)); closes.append(999.0)
    if art == "close_ungueltig":
        closes[-1] = None
    ts = [int(datetime(t.year, t.month, t.day, 9, 30, tzinfo=ny).timestamp()) for t in tage]
    zeit = {"vor_session": (s - timedelta(days=1), 16, 0), "intraday": (s, 14, 0),
            "folgetag": (s + timedelta(days=1), 10, 0), "halbtag_13": (s, 13, 0)}.get(art, (s, 16, 0))
    rmt = int(datetime(zeit[0].year, zeit[0].month, zeit[0].day, zeit[1], zeit[2], tzinfo=ny).timestamp())
    meta = {} if art == "rmt_fehlt" else {"regularMarketTime": rmt}
    adj = [(690.0 if art == "bereinigt" else c) for c in closes]
    return {"chart": {"result": [{"meta": meta, "timestamp": ts,
                                  "indicators": {"quote": [{"close": closes}], "adjclose": [{"adjclose": adj}]}}]}}


gm._fetch_yahoo = _yahoo


def _gex_lauf(name, jetzt, *argv, netz=None):
    netz = netz or _Netz()
    _FALSCHER_TAG.clear()
    _FALSCHER_TAG.update(netz.falsch)
    gm._get = netz
    gm._DATA = _ordner(name)
    _uhr(jetzt)
    alt = sys.argv
    sys.argv = ["snapshot_gex_massive.py", "--tickers", "SPY,QQQ,IWM", *argv]
    try:
        rc = _ruhig(gm.main)
    finally:
        sys.argv = alt
    return rc, gm._DATA, netz


m = gm._map(_kette(), S)
pruef("_map: DTE ab der Session, Verfall am Sessiontag draußen", sorted({c["dte"] for c in m}) == [7, 14, 28],
      sorted({c["dte"] for c in m}))
rc_a, da, _n = _gex_lauf("gex_a", NACH_SCHLUSS)
rc_b, db, _n = _gex_lauf("gex_b", NACH_MITTERNACHT)
sa = json.loads((da / "gex_summary.json").read_text()) if (da / "gex_summary.json").exists() else {}
sb = json.loads((db / "gex_summary.json").read_text()) if (db / "gex_summary.json").exists() else {}
pruef("beide Läufe Exit 0", (rc_a, rc_b) == (0, 0), (rc_a, rc_b))
pruef("Stempel = Session, mit stempel_art/bewertung",
      (sa.get("date"), sa.get("session"), sa.get("bewertung"), sa.get("stempel_art")) == (S.isoformat(),) * 3 + ("session",),
      {k: sa.get(k) for k in ("date", "session", "bewertung", "stempel_art")})
pruef("22:30 und 01:30 UTC derselben Session: identische Ausgabe (ohne Laufzeitfelder)",
      bool(sa) and _ohne_laufzeit(sa) == _ohne_laufzeit(sb))
pa = {f: _ohne_laufzeit(json.loads((da / f).read_text())) for f in _alle(da) if f.endswith(".json")}
pb = {f: _ohne_laufzeit(json.loads((db / f).read_text())) for f in _alle(db) if f.endswith(".json")}
pruef("... auch Profile und Archiv identisch", pa == pb and len(pa) >= 3, sorted(pa))
_n_b = _Netz()
rc_c, dc, _n_b = _gex_lauf("gex_c", NACH_MITTERNACHT, netz=_n_b)
hor = sorted({(date.fromisoformat(u.split("expiration_date.lte=")[1].split("&")[0]) - S).days
              for u in _n_b.abrufe if "expiration_date.lte=" in u})
pruef("Chain-Horizont ab der Session (45 bzw. 1200 Tage)", hor == [gm.MAX_DAYS, gm.PROFILE_MAX_DAYS], hor)
pruef("je Ticker 3 Verfälle (der verfallene Sessiontag zählt nicht)",
      [t.get("n_expiries") for t in sa.get("tickers", [])] == [3, 3, 3], [t.get("n_expiries") for t in sa.get("tickers", [])])
pruef("Archiv nur in gex_history_session/<Session>.json",
      f"gex_history_session/{S.isoformat()}.json" in _alle(da) and not any(f.startswith("gex_history/") for f in _alle(da)),
      _alle(da))
rc, d, netz = _gex_lauf("gex_handel", HANDELSZEIT)
pruef("Handelszeit: Exit 2, kein Abruf, keine Datei", rc == 2 and not netz.abrufe and not _alle(d),
      f"rc {rc}, {len(netz.abrufe)} Abrufe, {_alle(d)}")
rc, d, netz = _gex_lauf("gex_handel_lesend", HANDELSZEIT, "--no-write")
pruef("Handelszeit lesend (--no-write) erlaubt, schreibt nichts", rc == 0 and netz.abrufe and not _alle(d), f"rc {rc}")
rc, d, netz = _gex_lauf("gex_falsch", NACH_MITTERNACHT, netz=_Netz(falscher_tag={"QQQ"}))
s = json.loads((d / "gex_summary.json").read_text()) if (d / "gex_summary.json").exists() else {}
pruef("kein Tagesbalken der Session -> Ticker verworfen (QQQ fehlt)", "QQQ" in s.get("failed", [])
      and "QQQ" not in [t["ticker"] for t in s.get("tickers", [])], s.get("failed"))

print("  -- _spot: Nachweis des Sessionschlusses")
for art, soll in [("", 700.0), ("bereinigt", 700.0), ("folgetag", 700.0), ("kein_balken", None),
                  ("vor_session", None), ("intraday", None), ("rmt_fehlt", None), ("close_ungueltig", None),
                  ("halbtag_13", None)]:
    _ART.clear(); _ART["X"] = art
    ist = _ruhig(gm._spot, "X", "k", S)
    pruef(f"Spot bei {art or 'Normalfall'} -> {soll}", ist == soll, ist)
_HT = date(2026, 11, 27)                    # Tag nach Thanksgiving, NYSE-Halbtag 13:00 (belegt)
gm._fetch_yahoo = lambda sym, p, t: _yahoo(sym, p, t, session=_HT)
_ART.clear(); _ART["X"] = "halbtag_13"
pruef("Halbtag: letzter Handel 13:00 gilt als Schluss", _ruhig(gm._spot, "X", "k", _HT) == 700.0)
_ART["X"] = "intraday"
pruef("Halbtag: letzter Handel 14:00 (nach dem Schluss) ebenfalls gültig", _ruhig(gm._spot, "X", "k", _HT) == 700.0)
gm._fetch_yahoo = _yahoo
_ART.clear()

# ── 2. compute_key_levels ─────────────────────────────────────────────────────────────────────────────────────────
print("== compute_key_levels")
import compute_key_levels as kl                                          # noqa: E402

kl.gc = types.SimpleNamespace(collect=lambda: 0)
by = kl._by_exp(_kette(), S)
pruef("_by_exp: DTE ab der Session", sorted(e["dte"] for e in by.values()) == [0, 7, 14, 28],
      sorted(e["dte"] for e in by.values()))


def _kl_lauf(name, gex, jetzt=NACH_MITTERNACHT):
    w = _ordner(name)
    (w / "landing/data").mkdir(parents=True, exist_ok=True)
    if gex is not None:
        (w / "landing/data/gex_summary.json").write_text(json.dumps(gex), encoding="utf-8")
    kl._ROOT = w
    netz = _Netz()
    kl._get = netz
    _uhr(jetzt)
    try:
        out = _ruhig(kl.build, ["SPY"], write=True)
        res = "lief"
    except MarktOffen:
        out, res = {}, "MarktOffen"
    return res, out, netz, w


g_ok = {"date": S.isoformat(), "session": S.isoformat(), "bewertung": S.isoformat(), "stempel_art": "session",
        "tickers": [{"ticker": "SPY", "spot": 700.0, "zero_gamma": 690.0, "call_wall": 720.0, "put_wall": 680.0,
                     "regime": "long_gamma", "net_gex_usd_bn": 1.0}]}
res, out, _n_kl, _w = _kl_lauf("kl_ok", g_ok)
pruef("Chain-Horizont ab der Session (70 Tage)", sorted({(date.fromisoformat(u.split("expiration_date.lte=")[1].split("&")[0]) - S).days for u in _n_kl.abrufe if "expiration_date.lte=" in u}) == [kl._MAXDTE], sorted({(date.fromisoformat(u.split("expiration_date.lte=")[1].split("&")[0]) - S).days for u in _n_kl.abrufe if "expiration_date.lte=" in u}))
r0 = (out.get("tickers") or [{}])[0]
pruef("GEX derselben Session übernommen", res == "lief" and out.get("gex_status") == "ok"
      and r0.get("call_wall") == 720.0 and out.get("session") == S.isoformat(), (res, out.get("gex_status")))
g_alt = dict(g_ok, date="2026-10-15", session="2026-10-15", bewertung="2026-10-15")
res, out, _n, _w = _kl_lauf("kl_vorsession", g_alt)
r0 = (out.get("tickers") or [{}])[0]
pruef("GEX der Vorsession: keine Walls/Flip, Status andere_session",
      out.get("gex_status") == "andere_session:2026-10-15" and r0.get("call_wall") is None
      and r0.get("vol_trigger") is None and r0.get("max_pain") is not None, (out.get("gex_status"), r0.get("call_wall")))
g_stempel = {k: v for k, v in g_ok.items() if k not in ("session", "bewertung", "stempel_art")}
res, out, _n, _w = _kl_lauf("kl_stempel", g_stempel)
pruef("GEX mit altem Stempel: nicht übernommen", out.get("gex_status") == "alter_stempel"
      and (out.get("tickers") or [{}])[0].get("call_wall") is None, out.get("gex_status"))
res, out, _n, _w = _kl_lauf("kl_fehlt", None)
pruef("GEX fehlt: Status fehlt", out.get("gex_status") == "fehlt", out.get("gex_status"))
res, out, netz, w = _kl_lauf("kl_handel", g_ok, jetzt=HANDELSZEIT)
pruef("Handelszeit: MarktOffen, kein Abruf, keine Datei",
      res == "MarktOffen" and not netz.abrufe and not (w / "landing/data/key_levels.json").exists(), res)

# ── 3. compute_iv_surface ─────────────────────────────────────────────────────────────────────────────────────────
print("== compute_iv_surface")
import compute_iv_surface as ivs                                         # noqa: E402

ivs.clear_cache = lambda: None
ivs.gc = types.SimpleNamespace(collect=lambda: 0)
by, _spot = ivs._byexp(_kette(), S)
pruef("_byexp: DTE ab der Session, Sessiontag draußen", sorted(e["dte"] for e in by.values()) == [7, 14, 28],
      sorted(e["dte"] for e in by.values()))
w = _ordner("ivs_handel")
ivs._ROOT = w
netz = _Netz()
ivs._get = netz
_uhr(HANDELSZEIT)
try:
    _ruhig(ivs.build, ["SPY"], write=True)
    res = "lief"
except MarktOffen:
    res = "MarktOffen"
pruef("Handelszeit: MarktOffen, kein Abruf, keine Datei", res == "MarktOffen" and not netz.abrufe and not _alle(w), res)
w = _ordner("ivs_ok")
ivs._ROOT = w
_n_ivs = _Netz()
ivs._get = _n_ivs
_uhr(NACH_MITTERNACHT)
out = _ruhig(ivs.build, ["SPY"], write=True)
pruef("Chain-Horizont ab der Session (140 Tage)", sorted({(date.fromisoformat(u.split("expiration_date.lte=")[1].split("&")[0]) - S).days for u in _n_ivs.abrufe if "expiration_date.lte=" in u}) == [ivs._MAXDTE], sorted({(date.fromisoformat(u.split("expiration_date.lte=")[1].split("&")[0]) - S).days for u in _n_ivs.abrufe if "expiration_date.lte=" in u}))
pruef("nach Mitternacht: session = Session der Daten", out.get("session") == S.isoformat(), out.get("session"))

# ── 4. compute_options_skew: pc_ratio.date ────────────────────────────────────────────────────────────────────────
print("== compute_options_skew pc_ratio")
import scripts.compute_options_skew as cs                                # noqa: E402

cs._index_series = lambda *a, **k: None
cs._enrich = lambda sym, key=None: {
    "ticker": sym, "cats": ["Broad-Index"], "underlying": 700.0, "dte": 21, "put_vol": 100, "call_vol": 100,
    "put_oi": 1000, "call_oi": 1000, "call_25d": {"strike": 720, "iv": 0.19, "delta": 0.25},
    "put_25d": {"strike": 680, "iv": 0.22, "delta": -0.25}, "skew_pts": 3.0, "iv_atm": 0.20, "rv_1m": 0.18}
w = _ordner("skew")
(w / "landing/data").mkdir(parents=True, exist_ok=True)
(w / "landing/data/options_skew_history.json").write_text("{}", encoding="utf-8")
cs._ROOT = w
_uhr(NACH_MITTERNACHT)
out = _ruhig(cs.build, ["SPY"], write=True)
pruef("pc_ratio.date = session = Session (nicht Lauftag)",
      (out.get("pc_ratio") or {}).get("date") == out.get("session") == S.isoformat(),
      ((out.get("pc_ratio") or {}).get("date"), out.get("session")))

# ── 5. Archivleser ────────────────────────────────────────────────────────────────────────────────────────────────
print("== compare_flashalpha_gex._from_snapshot")
import compare_flashalpha_gex as cf                                      # noqa: E402

basis = _ordner("archiv")
cf._OUT_DIR = basis / "gex_history"
(basis / "gex_history").mkdir(exist_ok=True)
(basis / "gex_history_session").mkdir(exist_ok=True)
cf.requests = types.SimpleNamespace(get=lambda *a, **k: types.SimpleNamespace(status_code=404, json=lambda: None),
                                    post=cf.requests.post)
(basis / "gex_history_session" / f"{S}.json").write_text(json.dumps(
    {"date": S.isoformat(), "tickers": [{"ticker": "SPY", "net_gex_usd_bn": 1.0}]}), encoding="utf-8")
(basis / "gex_history" / f"{S}.json").write_text(json.dumps(
    {"date": S.isoformat(), "tickers": [{"ticker": "SPY", "net_gex_usd_bn": 9.0}]}), encoding="utf-8")
o = cf._from_snapshot("SPY", S.isoformat()) or {}
pruef("Session-Archiv zuerst", (o.get("_herkunft"), o.get("net_gex_usd_bn")) == ("session", 1.0), o)
(basis / "gex_history_session" / f"{S}.json").unlink()
o = cf._from_snapshot("SPY", S.isoformat()) or {}
pruef("Rückfall auf das Lauftag-Archiv, gekennzeichnet", (o.get("_herkunft"), o.get("net_gex_usd_bn")) == ("lauftag", 9.0), o)

# ── 6. Health-Check ───────────────────────────────────────────────────────────────────────────────────────────────
print("== daily_health_check._gex_bewertung")
sys.modules.setdefault("shared.supabase_client", types.SimpleNamespace(get_client=lambda: None))
import scripts.daily_health_check as hc                                  # noqa: E402


def _gd(datum, n=20, stempel=True):
    g = {"date": datum, "tickers": [{"ticker": f"T{i}", "zero_gamma": 1.0} for i in range(n)]}
    if stempel:
        g.update(session=datum, stempel_art="session")
    return g


ERW = date(2026, 10, 19)                                  # Montag; Vorsession Freitag 16.10.
for name, gd, soll in [
    ("aktuelle Session, volle Abdeckung -> grün", _gd("2026-10-19"), "green"),
    ("Freitag gegen Montag = eine Session hinter -> gelb", _gd("2026-10-16"), "yellow"),
    ("zwei Sessions hinter -> rot", _gd("2026-10-15"), "red"),
    ("aktuelle Session, aber nur 3 Ticker -> rot", _gd("2026-10-19", n=3), "red"),
    ("alter Stempel, aktuelles Datum -> gelb", _gd("2026-10-19", stempel=False), "yellow"),
    ("alter Stempel + 3 Ticker -> rot (nicht verbessert)", _gd("2026-10-19", n=3, stempel=False), "red"),
    ("ohne Datum -> rot", {"tickers": _gd("2026-10-19")["tickers"], "stempel_art": "session"}, "red"),
    ("Datum NACH der erwarteten Session -> rot", _gd("2026-10-20"), "red"),
    ("Samstag als Session -> rot", _gd("2026-10-17"), "red"),
]:
    st, det = hc._gex_bewertung(gd, ERW)
    pruef(name, st == soll, f"{st} · {det}")
for name, gd, erw, soll in [
    ("Feiertag 03.07. als Session -> rot", _gd("2026-07-03"), date(2026, 7, 6), "red"),
    ("02.07. gegen 06.07. (Feiertag dazwischen) = eine Session -> gelb", _gd("2026-07-02"), date(2026, 7, 6), "yellow"),
]:
    st, det = hc._gex_bewertung(gd, erw)
    pruef(name, st == soll, f"{st} · {det}")

# ── 6b. Seiten: /key-levels und /dealer-positioning (echtes Seiten-JS in node) ─────────────────────────────────────
print("== Seiten (node, scripts/js/probe_options_session.js)")
import shutil as _sh, subprocess as _sp                                   # noqa: E402
if _sh.which("node") is None:
    pruef("node vorhanden (Seitenprobe)", False, "node fehlt — ungeprüft ist nicht bestanden")
else:
    r = _sp.run(["node", str(_ROOT / "scripts/js/probe_options_session.js")], capture_output=True, text=True,
                encoding="utf-8")
    for z in r.stdout.splitlines():
        if z.strip().startswith(("ok", "FEHL")):
            print("    " + z.strip())
    pruef("Seitenprobe: Level-Text mit Session, Profil nur derselben Session",
          r.returncode == 0 and "ALLE PRUEFUNGEN BESTANDEN" in r.stdout, f"Exit {r.returncode}")

# ── 7. Yahoo-Schreiber stillgelegt ────────────────────────────────────────────────────────────────────────────────
print("== snapshot_gex.main (stillgelegt)")
import snapshot_gex as sg                                                # noqa: E402

aufrufe = []
sg.analyze = lambda *a, **k: aufrufe.append(a)
sg._DATA = _ordner("yahoo")
rc = _ruhig(sg.main)
pruef("Exit 1, kein Abruf, keine Datei", rc == 1 and not aufrufe and not _alle(sg._DATA), f"rc {rc}")

shutil.rmtree(_TMP, ignore_errors=True)
print()
if FEHLER:
    print(f"[FAIL] {len(FEHLER)} Prüfung(en): " + "; ".join(FEHLER))
    sys.exit(1)
print("[OK] alle Prüfungen grün")
