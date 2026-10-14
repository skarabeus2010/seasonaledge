#!/usr/bin/env python3
"""
verify_basisabweichung.py — Renditen aus gespeicherten Tagesreturns, Spot aus dem Rohschluss (Plan
docs/review_prompts/2026-10-14_options_sofortreparaturen_plan_v2.md, R1b/R1d).

Anlass: ETHA 2026-09-30, Schlusskurs 20,28 → 60,36 bei log_return −0,79 % (Wechsel der Kursbasis, Faktor 3). Aus
Schlusskursen gerechnet stand die realisierte Vola bei 380 %. Dieser Wächter schickt genau so eine Reihe durch die
ECHTEN Funktionen (Lader ersetzt, sonst nichts):
  * shared.basisabweichung.basisabweichungen        — erkennt den Sprung, Faktor, Zählung unbrauchbarer Paare
  * shared.realized_vol.rv_reihe_aus_returns        — gleich rv_reihe, solange die Kurse konsistent sind
  * scripts.compute_options_skew._realized_vol      — RV aus log_return, Spot = letzter Rohschluss + Datum
  * shared.intermarket._bewegung / _spy_vola        — Bewegung und SPY-Vola aus log_return
  * scripts.backfill_skew_vrp.nachrechnen           — VRP aus log_return
Exit 0 = alles grün.
"""
from __future__ import annotations
import math
import os
import sys
from pathlib import Path

os.environ["SA_OHNE_DOTENV"] = "1"
sys.dont_write_bytecode = True
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

# Ein unerwarteter Absturz ist KEIN Nachweis (Projektregel v66.17): Exit 3 statt 1, der Mutationstest wertet 3 als
# ungültig, nicht als gefangen.
def _absturz(typ, wert, tb):
    import traceback
    traceback.print_exception(typ, wert, tb)
    print("[Absturz]")
    os._exit(3)


sys.excepthook = _absturz

# Im Deploy-Gate fehlt streamlit; shared.yahoo_downloader braucht nur den Dekorator st.cache_data (+ .clear).
try:
    import streamlit  # noqa: F401
except ImportError:
    import types as _types

    def _cache_data(*a, **k):
        def deko(f):
            f.clear = lambda: None
            return f
        return deko(a[0]) if a and callable(a[0]) else deko
    sys.modules["streamlit"] = _types.SimpleNamespace(cache_data=_cache_data)

from shared.basisabweichung import basisabweichungen                 # noqa: E402
from shared.realized_vol import rv_reihe, rv_reihe_aus_returns, rv_aus_returns, RV_FENSTER  # noqa: E402

FEHLER = []


def pruef(name, ist, soll, tol=None):
    ok = (abs(ist - soll) <= tol) if (tol is not None and ist is not None and soll is not None) else ist == soll
    print(f"  {'ok  ' if ok else 'FAIL'} {name}  ->  {ist!r}" + ("" if ok else f"  (soll {soll!r})"))
    if not ok:
        FEHLER.append(name)


# ── Testreihe: 60 Handelstage, deterministisch, Basiswechsel ×3 an Tag 50 ──────────────────────────────────────
def _reihe(split_bei: int | None = 50, faktor: float = 3.0):
    daten, closes, returns = [], [], []
    c = 20.0
    for i in range(60):
        d = f"2026-{8 + (i // 28):02d}-{(i % 28) + 1:02d}"
        r = 0.01 * math.sin(i * 1.3) + 0.002 * ((i % 5) - 2)      # echte Tagesrendite
        if i > 0:
            c *= math.exp(r)
        daten.append(d); returns.append(r if i > 0 else None); closes.append(c)
    echte = list(closes)
    if split_bei is not None:
        closes = [x if i < split_bei else x * faktor for i, x in enumerate(closes)]   # neue Basis ab split_bei
    return daten, closes, returns, echte


daten, closes, returns, echte = _reihe()
print("== basisabweichungen")
zeilen = [{"ticker": "X", "date": d, "close": c, "log_return": r} for d, c, r in zip(daten, closes, returns)]
erg = basisabweichungen(zeilen)
pruef("genau ein Treffer", len(erg["treffer"]), 1)
pruef("Treffer am Basiswechsel", erg["treffer"][0]["datum"] if erg["treffer"] else None, daten[50])
pruef("Faktor 3,0", erg["treffer"][0]["basissprung"] if erg["treffer"] else None, 3.0, tol=1e-4)
z2 = [dict(z) for z in zeilen]; z2[30]["log_return"] = None; z2[40]["close"] = float("nan")
erg2 = basisabweichungen(z2)
pruef("fehlender Return gezählt", erg2["ohne_return"], 1)
pruef("ungültige Kurse gezählt (zwei Paare berühren den NaN-Kurs)", erg2["ungueltiger_kurs"], 2)
d_ab, c_ab, r_ab, _ = _reihe(faktor=1 / 3)
erg_ab = basisabweichungen([{"ticker": "X", "date": d, "close": c, "log_return": r} for d, c, r in zip(d_ab, c_ab, r_ab)])
pruef("Basiswechsel nach unten (Faktor 1/3) erkannt", [t["basissprung"] for t in erg_ab["treffer"]], [0.3333])
pruef("konsistente Reihe: kein Treffer", len(basisabweichungen(
    [{"ticker": "X", "date": d, "close": c, "log_return": r} for d, c, r in zip(daten, echte, returns)])["treffer"]), 0)

print("== rv_reihe_aus_returns")
d_ok, c_ok, r_ok, _ = _reihe(split_bei=None)
a, b = rv_reihe(d_ok, c_ok), rv_reihe_aus_returns(d_ok, r_ok)
pruef("ohne Basiswechsel: dieselben Tage wie rv_reihe", sorted(b.keys()), sorted(a.keys()))
pruef("ohne Basiswechsel: dieselben Werte wie rv_reihe",
      all(k in b and abs(a[k] - b[k]) < 1e-12 for k in a), True)
rv_split = rv_reihe_aus_returns(daten, returns)
pruef("mit Basiswechsel: Wert am letzten Tag = Wert der konsistenten Reihe", rv_split[daten[-1]], b[daten[-1]], tol=1e-12)
pruef("aus Schlusskursen wäre er falsch (> 1,0)", rv_reihe(daten, closes)[daten[-1]] > 1.0, True)
pruef("None im Fenster -> kein Wert", rv_reihe_aus_returns(daten, returns[:55] + [None] + returns[56:]).get(daten[-1]), None)
pruef("NaN im Fenster -> kein Wert", rv_aus_returns(returns[1:40] + [float("nan")] + returns[41:]), None)

# ── Supabase-Attrappe für den ECHTEN Lader shared.data.lade_kurse (die Verbraucher importieren ihn selbst) ──────
import types, importlib, contextlib, io                                 # noqa: E402
from shared.data import lade_kurse, KursreiheFehlt                      # noqa: E402


class _Preise:
    """prices je Ticker; eq/gte/order/range wie PostgREST (1000er-Seiten). fehler_ab/none_ab: Seite ab diesem Offset
    wirft bzw. liefert data=None."""
    def __init__(self, je_ticker, fehler_ab=None, none_ab=None):
        self.je, self.fehler_ab, self.none_ab = je_ticker, fehler_ab, none_ab
        self.f, self.von, self.bis, self.tab = {}, 0, 999, None
    def _neu(self, **k):
        q = _Preise(self.je, self.fehler_ab, self.none_ab)
        q.f, q.von, q.bis, q.tab = dict(self.f), self.von, self.bis, self.tab
        for n, v in k.items():
            setattr(q, n, v)
        return q
    def table(self, name):
        return self._neu(tab=name)
    def select(self, *a, **k):
        return self
    def order(self, *a, **k):
        return self
    def eq(self, col, v):
        return self._neu(f={**self.f, "eq": v})
    def gte(self, col, v):
        return self._neu(f={**self.f, "gte": v})
    def range(self, a, b):
        return self._neu(von=a, bis=b)
    def execute(self):
        if self.fehler_ab is not None and self.von >= self.fehler_ab:
            raise ConnectionError("Seite gescheitert")
        if self.none_ab is not None and self.von >= self.none_ab:
            return types.SimpleNamespace(data=None)
        z = sorted(self.je.get(self.f.get("eq"), []), key=lambda r: r["date"])
        if "gte" in self.f:
            z = [r for r in z if r["date"] >= self.f["gte"]]
        return types.SimpleNamespace(data=[dict(r) for r in z[self.von:self.bis + 1]])


@contextlib.contextmanager
def _db(je_ticker, **k):
    alt = sys.modules.get("shared.supabase_client")
    sys.modules["shared.supabase_client"] = types.SimpleNamespace(get_client=lambda: _Preise(je_ticker, **k))
    try:
        yield
    finally:
        if alt is None:
            sys.modules.pop("shared.supabase_client", None)
        else:
            sys.modules["shared.supabase_client"] = alt


def _zeilen(d, c, r):
    return [{"date": x, "close": y, "log_return": z} for x, y, z in zip(d, c, r)]


X = {"X": _zeilen(daten, closes, returns)}

print("== shared.data.lade_kurse (echt)")
with _db(X):
    kd, kc, kr = lade_kurse("X")
pruef("zeilentreu: Daten, Schlüsse, Returns", (kd, kc, kr), (daten, closes, returns))
# 2500 Zeilen = drei Seiten, Typumwandlung (Text, nan, negativ, None)
lang_d = [f"{2010 + i // 300}-{1 + (i % 300) // 25:02d}-{1 + i % 25:02d}" for i in range(2500)]
lang = [{"date": d, "close": str(10 + i % 7), "log_return": "0.001"} for i, d in enumerate(lang_d)]
lang[5]["close"] = "nan"; lang[6]["close"] = -1; lang[7]["log_return"] = None; lang[8]["log_return"] = "inf"
with _db({"L": lang}):
    ld, lc, lr = lade_kurse("L")
pruef("drei Seiten vollständig (2500 Zeilen)", len(ld), 2500)
pruef("Text -> Zahl", lc[0], 10.0)
pruef("ungültige Schlüsse (nan, negativ) -> None, Zeile bleibt", (lc[5], lc[6], ld[5]), (None, None, lang_d[5]))
pruef("fehlender/unendlicher Return -> None", (lr[7], lr[8]), (None, None))
with _db({"L": lang}):
    pruef("ab= filtert serverseitig", lade_kurse("L", ab=lang_d[2400])[0][0], lang_d[2400])


def _wirft(fn, typ):
    try:
        fn()
    except typ:
        return True
    except Exception as ex:                 # falsche Fehlerklasse ist ein Befund, kein Absturz
        return f"{type(ex).__name__}: {ex}"
    return False


with _db({"L": lang}, fehler_ab=1000):
    pruef("Fehler auf Seite 2 -> Ausnahme, keine Teilreihe", _wirft(lambda: lade_kurse("L"), ConnectionError), True)
with _db({"L": lang}, none_ab=1000):
    pruef("data=None auf Seite 2 -> KursreiheFehlt, keine Teilreihe",
          _wirft(lambda: lade_kurse("L"), KursreiheFehlt), True)
with _db(X):
    pruef("Mindestzahl nicht erreicht -> KursreiheFehlt", _wirft(lambda: lade_kurse("X", mindestens=61), KursreiheFehlt),
          True)
doppelt = {"D": _zeilen(daten, closes, returns) + [{"date": daten[10], "close": 1.0, "log_return": 0.0}]}
with _db(doppelt):
    pruef("doppeltes Datum -> KursreiheFehlt", _wirft(lambda: lade_kurse("D"), KursreiheFehlt), True)

print("== compute_options_skew._realized_vol (echter Lader)")
import scripts.compute_options_skew as cs                               # noqa: E402
with _db(X):
    rv, last, last_d = cs._realized_vol("X", RV_FENSTER, bis=daten[-1])
pruef("RV aus log_return (nicht 380 %)", rv, b[daten[-1]], tol=1e-12)
pruef("Spot = letzter Rohschluss", last, round(closes[-1], 2))
pruef("Spot-Datum = letzter Tag", last_d, daten[-1])
c3 = list(closes); c3[-1] = None
with _db({"X": _zeilen(daten, c3, returns)}):
    rv3, last3, d3 = cs._realized_vol("X", RV_FENSTER, bis=daten[-1])
pruef("letzter Schluss ungültig -> Spot vom Vortag", (last3, d3), (round(closes[-2], 2), daten[-2]))
pruef("... und RV-Fenster endet am Vortag", rv3, b[daten[-2]], tol=1e-12)
with _db({"X": _zeilen(daten, closes, returns[:58] + [None] + returns[59:])}):
    pruef("None im Fenster -> keine RV, Spot bleibt", cs._realized_vol("X", RV_FENSTER, bis=daten[-1])[:2],
          (None, round(closes[-1], 2)))
with _db(X):
    rv45, last45, d45 = cs._realized_vol("X", RV_FENSTER, bis=daten[45])
pruef("Kappung auf die Session: Datum", d45, daten[45])
pruef("Kappung auf die Session: Spot", last45, round(closes[45], 2))
pruef("Kappung auf die Session: RV = Referenzfenster bis dahin", rv45,
      rv_aus_returns(returns[:46], RV_FENSTER), tol=1e-12)
pruef("... und das ist nicht der Wert am Reihenende", rv45 is not None and abs(rv45 - b[daten[-1]]) > 1e-9, True)

print("== intermarket (echter Lader)")
import shared.intermarket as im                                         # noqa: E402
with _db({"TLT": X["X"], "SPY": X["X"]}):
    bew, stand = im._bewegung("TLT", 10)
    spy = im._spy_vola()
pruef("Bewegung aus log_return über den Basiswechsel", bew, math.exp(sum(returns[-10:])) - 1.0, tol=1e-12)
pruef("SPY-Vola aus log_return", spy, rv_aus_returns(returns, 21), tol=1e-12)

print("== backfill_skew_vrp.nachrechnen (echter Lader)")
import scripts.backfill_skew_vrp as bv                                  # noqa: E402
hist = {"X": [{"date": daten[-1], "iv_atm": 0.30, "cm_mode": "cm"}]}
with _db(X), contextlib.redirect_stdout(io.StringIO()):
    bv.nachrechnen(hist, nur={"X"})
vrp = hist["X"][0].get("vrp_pts")
pruef("VRP = (IV − RV aus log_return)·100", vrp, round((0.30 - b[daten[-1]]) * 100, 2))

print("== daily_health_check: Check „Kursbasis“")


class _Kette:
    """Supabase-Attrappe: prices liefert `zeilen` (seitenweise), alles andere leer."""
    def __init__(self, zeilen, tab=None, von=0):
        self.zeilen, self.tab, self.von = zeilen, tab, von
    def table(self, name):
        return _Kette(self.zeilen, name)
    def range(self, a, b):
        return _Kette(self.zeilen, self.tab, a)
    def execute(self):
        daten = self.zeilen[self.von:self.von + 1000] if self.tab == "prices" else []
        return types.SimpleNamespace(data=daten, count=0)
    def __getattr__(self, _):
        return lambda *a, **k: self


def _check7(zeilen):
    sys.modules["shared.supabase_client"] = types.SimpleNamespace(get_client=lambda: _Kette(zeilen))
    try:
        hc = importlib.import_module("scripts.daily_health_check")
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            ctx = hc.collect_health_data()
    finally:
        sys.modules.pop("shared.supabase_client", None)
    return next((c for c in ctx["checks"] if c["name"] == "Kursbasis (Basisabweichungen)"), None)


k = _check7([dict(z) for z in zeilen] * 1)
pruef("Basiswechsel -> gelb mit Ticker und Faktor", (k or {}).get("status"), "yellow")
pruef("... Detail nennt X und ×3.0", "X" in (k or {}).get("detail", "") and "3.0" in (k or {}).get("detail", ""), True)
k0 = _check7([])
pruef("keine Zeilen -> gelb (ungeprüft), nicht grün", ((k0 or {}).get("status"), "ungeprüft" in (k0 or {}).get("detail", "")),
      ("yellow", True))
konsistent = [{"ticker": "X", "date": d, "close": c, "log_return": r} for d, c, r in zip(daten, echte, returns)]
pruef("konsistente Kurse -> grün", (_check7(konsistent) or {}).get("status"), "green")
k_ohne_r = _check7([dict(z, log_return=None) for z in konsistent])
pruef("alle Returns fehlen -> gelb ungeprüft (nicht grün)",
      ((k_ohne_r or {}).get("status"), "ungeprüft" in (k_ohne_r or {}).get("detail", "")), ("yellow", True))
k_ohne_c = _check7([dict(z, close=None) for z in konsistent])
pruef("alle Schlüsse ungültig -> gelb ungeprüft (nicht grün)",
      ((k_ohne_c or {}).get("status"), "ungeprüft" in (k_ohne_c or {}).get("detail", "")), ("yellow", True))
teilw = [dict(z) for z in konsistent]; teilw[20]["log_return"] = None; teilw[30]["close"] = None
k_teil = _check7(teilw)
pruef("teilweise übersprungen -> gelb unvollständig mit Zählung",
      ((k_teil or {}).get("status"), "unvollständig" in (k_teil or {}).get("detail", ""),
       "1 ohne log_return, 2 mit ungültigem Kurs" in (k_teil or {}).get("detail", "")), ("yellow", True, True))
viele = [dict(z, ticker=f"T{i}") for i in range(30) for z in konsistent] + [dict(z, ticker="Z") for z in zeilen]
kv = _check7(viele)
pruef("Treffer jenseits der ersten 1000 Zeilen gefunden (Seitenweise)", (kv or {}).get("status"), "yellow")


class _KetteNone(_Kette):
    """Seite 2 von prices liefert data=None (keine Antwort statt leerer Liste)."""
    def table(self, name):
        return _KetteNone(self.zeilen, name)
    def range(self, a, b):
        return _KetteNone(self.zeilen, self.tab, a)
    def execute(self):
        if self.tab == "prices" and self.von >= 1000:
            return types.SimpleNamespace(data=None, count=0)
        return super().execute()


sys.modules["shared.supabase_client"] = types.SimpleNamespace(get_client=lambda: _KetteNone(
    [dict(z, ticker=f"T{i}") for i in range(30) for z in konsistent]))
try:
    _hc = importlib.import_module("scripts.daily_health_check")
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        _ctx = _hc.collect_health_data()
finally:
    sys.modules.pop("shared.supabase_client", None)
kn = next((c for c in _ctx["checks"] if c["name"] == "Kursbasis (Basisabweichungen)"), {})
pruef("data=None auf Seite 2 -> gelb ungeprüft, nicht grün", (kn.get("status"), "ungeprüft" in kn.get("detail", "")),
      ("yellow", True))

print("== daily_report.events_today_tomorrow: keine Earnings, Dividenden bleiben (R4)")
from datetime import date as _date, timedelta as _td                   # noqa: E402


class _EvKette(_Kette):
    """earnings_events und dividend_events liefern je eine Zeile im Fenster."""
    TAG = (_date(2026, 10, 14) + _td(days=1)).isoformat()
    def table(self, name):
        return _EvKette([], name)
    def execute(self):
        if self.tab == "earnings_events":
            return types.SimpleNamespace(data=[{"ticker": "EARN", "report_date": self.TAG, "eps_estimate": 1.0}])
        if self.tab == "dividend_events":
            return types.SimpleNamespace(data=[{"ticker": "DIVI", "ex_date": self.TAG, "amount": 0.5, "currency": "USD"}])
        return types.SimpleNamespace(data=[])


sys.modules["shared.supabase_client"] = types.SimpleNamespace(get_client=lambda: _EvKette([]))
try:
    import shared.daily_report as dr                                    # noqa: E402
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        ev = dr.events_today_tomorrow(_date(2026, 10, 15), lookahead_days=5)
finally:
    sys.modules.pop("shared.supabase_client", None)
pruef("kein Ereignis aus earnings_events", [e for e in ev if e.get("ticker") == "EARN" or e.get("type") == "Earnings"], [])
pruef("Dividende aus dividend_events bleibt", [e["ticker"] for e in ev if e.get("type") == "Dividende"], ["DIVI"])

print()
if FEHLER:
    print(f"[FAIL] {len(FEHLER)} Prüfung(en): " + "; ".join(FEHLER))
    sys.exit(1)
print("[OK] alle Prüfungen grün")
