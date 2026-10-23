#!/usr/bin/env python3
"""Waechter B1: Kettenvollstaendigkeit, Feldzustaende, Strike-Stufe.

Geprueft wird der ECHTE Produktionspfad, nicht ein Nachbau: `_fetch_chain` und `_chain`
mit einer Antwort-Attrappe an `_get`, `analyze_massive` und `_one` im Original, und
`main()` beider Erzeuger, damit Summary, Archiv und `key_levels.json` wirklich entstehen.
Nur der Netzabruf, die Session und das EOD-Fenster sind Attrappen.

Hintergrund: docs/KEY_LEVELS_CHART.md, Abschnitte 2.2a, 3 und 8 (Stufe B1).

Aufruf: py -3.14 scripts/verify_niveau_felder.py   — Exit 0 gruen, 1 rot, 3 Absturz.
"""
from __future__ import annotations

import json
import os
import pathlib
import sys
import tempfile
import traceback

_WURZEL = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_WURZEL))
sys.path.insert(0, str(_WURZEL / "scripts"))

_TMP = pathlib.Path(tempfile.mkdtemp(prefix="sa-b1-"))
os.environ["SA_SPERR_DIR"] = str(_TMP / "sperre")
os.environ["SA_OHNE_DOTENV"] = "1"
os.environ["MASSIVE_API_KEY"] = "probe-kein-echter-schluessel"

# Ein Absturz ist kein Nachweis: eigener Exit-Code, damit ein Mutationstest ihn nicht
# als "gefangen" verbucht.
def _absturz(t, w, tb):
    print("\n[ABSTURZ] %s: %s" % (t.__name__, w))
    traceback.print_tb(tb)
    sys.exit(3)


sys.excepthook = _absturz

# streamlit fehlt im Gate-Runner, shared.yahoo_downloader importiert es (st.cache_data).
# Hausmuster aus verify_gex_session.py: Attrappe im Modulcache UND als Datei auf dem
# PYTHONPATH, damit auch Unterprozesse sie sehen.
try:                                           # noqa: SIM105
    import streamlit  # noqa: F401
except ImportError:
    import types
    st = types.ModuleType("streamlit")
    st.cache_data = lambda *a, **k: (lambda f: f)
    st.secrets = {}
    sys.modules["streamlit"] = st
    (_TMP / "stub").mkdir(parents=True, exist_ok=True)
    (_TMP / "stub" / "streamlit.py").write_text(
        "def cache_data(*a, **k):\n    return lambda f: f\n\n\nsecrets = {}\n",
        encoding="utf-8")
    os.environ["PYTHONPATH"] = str(_TMP / "stub") + os.pathsep + os.environ.get("PYTHONPATH", "")

from datetime import date, timedelta                                     # noqa: E402

from shared.niveau_felder import (Z_KEIN_NIVEAU, Z_NICHT_EINDEUTIG,      # noqa: E402
                                  Z_OK, Z_QUELLE_FEHLT, Z_TEILKETTE,
                                  ZUSTAENDE, feldzustand, strike_stufe,
                                  zeichenbar)

_SESSION = date(2026, 10, 21)
_fehler = 0
_n = 0


def pruef(name, ok, info=None):
    global _fehler, _n
    _n += 1
    print("  %s %s%s" % ("ok  " if ok else "FAIL", name,
                         "" if info is None else "  ->  %s" % (info,)))
    if not ok:
        _fehler += 1


# ───────────────────────── 1 Der gemeinsame Kern ─────────────────────────────────
print("\n[1] shared/niveau_felder.py")
pruef("Wert da, Kette ganz -> ok", feldzustand(5.0, True) == Z_OK)
pruef("kein Wert, Kette ganz -> kein_niveau", feldzustand(None, True) == Z_KEIN_NIVEAU)
pruef("Wert da, Kette abgeschnitten -> teilkette", feldzustand(5.0, False) == Z_TEILKETTE)
pruef("kein Wert, Kette abgeschnitten -> teilkette (NICHT kein_niveau)",
      feldzustand(None, False) == Z_TEILKETTE)
pruef("Ladezustand unbekannt (None) -> teilkette", feldzustand(5.0, None) == Z_TEILKETTE)
pruef("keine Quelle schlaegt alles -> quelle_fehlt",
      feldzustand(5.0, False, quelle_da=False) == Z_QUELLE_FEHLT)
pruef("mehrdeutig -> nicht_eindeutig",
      feldzustand(5.0, True, mehrdeutig=True) == Z_NICHT_EINDEUTIG)
pruef("mehrdeutig schlaegt nicht die Teilkette",
      feldzustand(5.0, False, mehrdeutig=True) == Z_TEILKETTE)
pruef("gezeichnet werden genau ok und nicht_eindeutig",
      [z for z in ZUSTAENDE if zeichenbar(z)] == [Z_OK, Z_NICHT_EINDEUTIG])

pruef("Stufe ganzzahlig", strike_stufe([100, 101, 103]) == 1.0)
pruef("Stufe halbe Punkte", strike_stufe([10.0, 10.5, 11.0]) == 0.5)
pruef("Stufe 0,1 trotz Gleitkommarest", strike_stufe([10.0, 10.1, 10.2]) == 0.1,
      strike_stufe([10.0, 10.1, 10.2]))
pruef("Stufe = KLEINSTER Abstand, nicht der haeufigste",
      strike_stufe([100, 105, 110, 110.5]) == 0.5)
pruef("doppelte Strikes ergeben keinen Abstand 0",
      strike_stufe([100, 100, 105]) == 5.0)
# Der `d > 0`-Filter ist nur ueber die Rundung erreichbar: zwei VERSCHIEDENE
# Gleitkommazahlen haben nie den Abstand 0, zwei naeher als 1e-6 liegende runden
# aber darauf. Ohne den Filter waere die Stufe hier 0,0 — und eine Stufe 0 macht die
# Preispruefung in Spec 2.2a sinnlos (jede Abweichung waere zu gross).
pruef("fast gleiche Strikes ergeben keine Stufe 0",
      strike_stufe([100.0, 100.0000001, 105.0]) == 5.0,
      strike_stufe([100.0, 100.0000001, 105.0]))
pruef("ein einziger Strike -> None", strike_stufe([100]) is None)
pruef("leer -> None", strike_stufe([]) is None)
pruef("nicht endlich -> None", strike_stufe([1.0, float("inf")]) is None)
pruef("unbrauchbare Eintraege werden uebersprungen",
      strike_stufe([100, None, "x", 102]) == 2.0)
# [Aufbau] Eigenschaften der Pruefvorrichtung, nicht des Produktivcodes. 0,5 ist in
# Gleitkomma exakt (meine erste Fassung behauptete das Gegenteil und bestaetigte sich
# selbst) - ein Rest entsteht erst bei 0,1.
pruef("[Aufbau] 0,5-Schritte sind exakt, 0,1-Schritte nicht",
      (10.5 - 10.0) == 0.5 and (10.1 - 10.0) != 0.1)


# ───────────────────── 2 Attrappe fuer die Kettenabrufe ──────────────────────────
def _kette(n_strikes=12, exp="2026-10-23", typ_beide=True, oi=500, iv=0.25,
           strike0=100.0, schritt=1.0):
    """Synthetische Polygon-Kontrakte: je Strike Call und Put."""
    out = []
    for i in range(n_strikes):
        K = strike0 + i * schritt
        typen = ("call", "put") if typ_beide else ("call",)
        for ty in typen:
            out.append({"details": {"expiration_date": exp, "contract_type": ty,
                                    "strike_price": K},
                        "open_interest": oi,
                        "implied_volatility": iv,
                        "greeks": {"gamma": 0.01},
                        "day": {"volume": 10, "close": 1.0}})
    return out


print("\n[2] _fetch_chain gibt den Ladezustand zurueck (echte Funktion)")
import snapshot_gex_massive as sgm                                       # noqa: E402

_echt_get = sgm._get


def _get_seiten(seiten):
    """Attrappe: liefert die Seiten der Reihe nach."""
    zustand = {"i": 0}

    def f(url, key, tries=4):
        i = zustand["i"]
        zustand["i"] += 1
        return seiten[i] if i < len(seiten) else {"status": "ERROR", "results": []}
    return f


sgm._get = _get_seiten([{"status": "OK", "results": _kette(), "next_url": None}])
roh, ganz = sgm._fetch_chain("TEST", 45, "k", _SESSION)
pruef("Paginierung zu Ende -> vollstaendig", ganz is True and len(roh) == 24, len(roh))

sgm._get = _get_seiten([{"status": "OK", "results": _kette(4), "next_url": "u2"},
                        {"status": "ERROR", "results": []}])
roh, ganz = sgm._fetch_chain("TEST", 45, "k", _SESSION)
pruef("unbrauchbare Folgeseite -> abgeschnitten", ganz is False and len(roh) == 8, len(roh))

_alt_cap = sgm._MAX_PAGES
sgm._MAX_PAGES = 2
sgm._get = _get_seiten([{"status": "OK", "results": _kette(2), "next_url": "u2"},
                        {"status": "OK", "results": _kette(2), "next_url": "u3"}])
roh, ganz = sgm._fetch_chain("TEST", 45, "k", _SESSION)
pruef("Seiten-Cap gerissen -> abgeschnitten (next_url war noch da)",
      ganz is False and len(roh) == 8, len(roh))
sgm._MAX_PAGES = _alt_cap


# ──────────────── 3 analyze_massive: die echten Felder in der Zeile ──────────────
print("\n[3] analyze_massive (echte Funktion, nur Netz und Spot als Attrappe)")
sgm._spot = lambda sym, key, session: 105.0

sgm._get = _get_seiten([{"status": "OK", "results": _kette(20), "next_url": None}])
obj = sgm.analyze_massive("TEST", "k", 45, session=_SESSION)
pruef("Zeile entsteht", isinstance(obj, dict))
if isinstance(obj, dict):
    pruef("gex_kette_vollst = True", obj.get("gex_kette_vollst") is True)
    pruef("gex_horizont_tage = 45", obj.get("gex_horizont_tage") == 45)
    pruef("strike_stufe gemessen (1,0)", obj.get("strike_stufe") == 1.0,
          obj.get("strike_stufe"))
    pruef("strike_stufe_quelle benannt", obj.get("strike_stufe_quelle") == "gex_kette")
    f = obj.get("felder") or {}
    pruef("felder tragen alle drei Niveaus",
          set(f) == {"call_wall", "put_wall", "vol_trigger"}, sorted(f))
    pruef("jeder Zustand ist ein vertraglicher", all(v in ZUSTAENDE for v in f.values()), f)
    pruef("Wall mit Wert -> ok, Wall ohne Wert -> kein_niveau",
          all((f[k] == Z_OK) == (obj.get(k if k != "vol_trigger" else "zero_gamma") is not None)
              for k in ("call_wall", "put_wall", "vol_trigger")), f)

sgm._get = _get_seiten([{"status": "OK", "results": _kette(20), "next_url": "u2"},
                        {"status": "ERROR", "results": []}])
obj2 = sgm.analyze_massive("TEST", "k", 45, session=_SESSION)
pruef("abgeschnittene Kette -> alle drei Zustaende teilkette",
      isinstance(obj2, dict) and obj2.get("gex_kette_vollst") is False
      and set((obj2.get("felder") or {}).values()) == {Z_TEILKETTE},
      (obj2 or {}).get("felder"))

# Strikes nur OBERHALB des Spots: unterhalb kann es keine Put-Wall geben -> regulaer
# kein Niveau, nicht "Fehler".
sgm._get = _get_seiten([{"status": "OK", "results": _kette(20, strike0=200.0),
                         "next_url": None}])
obj3 = sgm.analyze_massive("TEST", "k", 45, session=_SESSION)
if isinstance(obj3, dict):
    f3 = obj3.get("felder") or {}
    pruef("kein Strike unter dem Spot -> put_wall kein_niveau (nicht quelle_fehlt)",
          f3.get("put_wall") == Z_KEIN_NIVEAU and obj3.get("put_wall") is None, f3)

# Profil-Ticker holen die Kette ueber 1200 Tage, die Zeile muss aber den
# SUMMARY-Horizont ausweisen (45) - sonst stehen Niveaus und Horizont nicht zusammen.
sgm._get = _get_seiten([{"status": "OK", "results": _kette(20) + _kette(6, exp="2027-06-18"),
                         "next_url": None}])
obj4 = sgm.analyze_massive("TEST", "k", 45, profile_days=1200, session=_SESSION)
pruef("Profil-Ticker: Horizont bleibt der des Summary (45, nicht 1200)",
      isinstance(obj4, dict) and obj4.get("gex_horizont_tage") == 45,
      (obj4 or {}).get("gex_horizont_tage"))
pruef("Profil-Ticker: Stufe aus der Summary-Kette, nicht aus der Profil-Kette",
      isinstance(obj4, dict) and obj4.get("strike_stufe") == 1.0,
      (obj4 or {}).get("strike_stufe"))

sgm._get = _echt_get


# ─────────────── 4 main(): Summary und Archiv entstehen wirklich ─────────────────
print("\n[4] main() des Snapshots schreibt Summary und Archiv mit den neuen Feldern")
_daten = _TMP / "data"
_daten.mkdir(parents=True, exist_ok=True)
sgm._DATA = _daten
sgm._spot = lambda sym, key, session: 105.0
sgm._get = lambda url, key, tries=4: {"status": "OK", "results": _kette(20),
                                      "next_url": None}
sgm.letzte_session = lambda boerse: _SESSION
sgm.pruefe_eod_fenster = lambda name: None
sgm.is_trading_day = lambda d, boerse: True
_argv = sys.argv
sys.argv = ["snapshot_gex_massive.py", "--tickers", "TEST1,TEST2"]
rc = sgm.main()
sys.argv = _argv
pruef("Lauf endet mit 0", rc == 0, rc)

summary = _daten / "gex_summary.json"
archiv = _daten / "gex_history_session" / ("%s.json" % _SESSION.isoformat())
pruef("Summary geschrieben", summary.exists())
pruef("Archiv der Session geschrieben", archiv.exists(), archiv.name)
if summary.exists():
    s = json.loads(summary.read_text(encoding="utf-8"))
    z0 = (s.get("tickers") or [{}])[0]
    pruef("Summary-Zeile traegt felder + Stufe + Horizont + Ladezustand",
          all(k in z0 for k in ("felder", "strike_stufe", "gex_horizont_tage",
                                "gex_kette_vollst")), sorted(set(z0) & {
              "felder", "strike_stufe", "gex_horizont_tage", "gex_kette_vollst"}))
if archiv.exists():
    a = json.loads(archiv.read_text(encoding="utf-8"))
    z1 = (a.get("tickers") or [{}])[0]
    pruef("Archivzeile traegt dieselben vier Felder",
          all(k in z1 for k in ("felder", "strike_stufe", "gex_horizont_tage",
                                "gex_kette_vollst")), sorted(z1))
    pruef("Archiv bleibt session-gestempelt", a.get("stempel_art") == "session")


# ─────────────── 5 compute_key_levels: Zustaende der Zeile ───────────────────────
print("\n[5] compute_key_levels (echte Funktionen)")
import compute_key_levels as ckl                                         # noqa: E402

_gex_zeile = {
    "spot": 105.0, "zero_gamma": 104.5, "regime": "short_gamma",
    "call_wall": 110.0, "put_wall": 100.0, "net_gex_usd_bn": -1.0,
    "gex_kette_vollst": True, "gex_horizont_tage": 45,
    "strike_stufe": 1.0, "strike_stufe_quelle": "gex_kette",
    "felder": {"call_wall": Z_OK, "put_wall": Z_KEIN_NIVEAU, "vol_trigger": Z_OK},
}

ckl._get = lambda url, key, tries=4: {"status": "OK", "results": _kette(20),
                                      "next_url": None}
r = ckl._one("TEST", "k", {"TEST": _gex_zeile}, _SESSION)
pruef("Zeile entsteht", isinstance(r, dict))
if isinstance(r, dict):
    pruef("mp_kette_vollst = True", r.get("mp_kette_vollst") is True)
    pruef("Stufe und Horizont aus der GEX-Zeile uebernommen",
          r.get("strike_stufe") == 1.0 and r.get("gex_horizont_tage") == 45)
    pruef("Wall-Zustaende werden UEBERNOMMEN, nicht neu erfunden",
          (r.get("felder") or {}).get("put_wall") == Z_KEIN_NIVEAU,
          (r.get("felder") or {}).get("put_wall"))
    pruef("max_pain hat einen eigenen Zustand",
          (r.get("felder") or {}).get("max_pain") in ZUSTAENDE,
          (r.get("felder") or {}).get("max_pain"))

ckl._get = _get_seiten([{"status": "OK", "results": _kette(20), "next_url": "u2"},
                        {"status": "ERROR", "results": []}])
r2 = ckl._one("TEST", "k", {"TEST": _gex_zeile}, _SESSION)
pruef("abgeschnittene Max-Pain-Kette -> max_pain teilkette, Walls unberuehrt",
      isinstance(r2, dict) and (r2.get("felder") or {}).get("max_pain") == Z_TEILKETTE
      and (r2.get("felder") or {}).get("call_wall") == Z_OK,
      (r2 or {}).get("felder"))


def _wirft(url, key, tries=4):
    raise RuntimeError("Abruf gescheitert")


ckl._get = _wirft
r3 = ckl._one("TEST", "k", {"TEST": _gex_zeile}, _SESSION)
pruef("gescheiterter Abruf -> max_pain quelle_fehlt (NICHT kein_niveau)",
      isinstance(r3, dict) and (r3.get("felder") or {}).get("max_pain") == Z_QUELLE_FEHLT
      and r3.get("mp_kette_vollst") is None,
      (r3 or {}).get("felder"))

# Abruf wieder herstellen: mit der Ausnahme-Attrappe von oben entstuende gar keine
# Zeile, und "r4 is None or ..." waere immer wahr — eine Pruefung, die wegen eines
# fehlenden Objekts gruen ist (vom Mutationstest gefangen).
ckl._get = lambda url, key, tries=4: {"status": "OK", "results": _kette(20),
                                      "next_url": None}
r4 = ckl._one("TEST", "k", {}, _SESSION)
pruef("[Aufbau] ohne GEX-Zeile entsteht trotzdem eine Zeile (Max Pain aus der Kette)",
      isinstance(r4, dict), type(r4).__name__)
pruef("ohne GEX-Zeile sind alle drei Wall-Zustaende quelle_fehlt",
      isinstance(r4, dict) and all((r4.get("felder") or {}).get(k) == Z_QUELLE_FEHLT
                                   for k in ("call_wall", "put_wall", "vol_trigger")),
      (r4 or {}).get("felder"))

n = ckl._nur_gex("TEST", _gex_zeile)
pruef("ohne Schluessel: max_pain quelle_fehlt, Walls uebernommen",
      n["felder"]["max_pain"] == Z_QUELLE_FEHLT
      and n["felder"]["put_wall"] == Z_KEIN_NIVEAU, n["felder"])

# Mehrdeutiges Max Pain: Calls unten, Puts oben, gleiche Stueckzahl — dann ist die
# Auszahlungssumme zwischen 101 und 103 KONSTANT (600), und die Kandidaten 101 und 103
# liegen beide im Minimum. Drei Strikes mit je Call und Put haetten dagegen ein
# eindeutiges Minimum in der Mitte (erste Fassung dieser Fixture, vom Waechter gefangen).
_calls, _puts = (100.0, 101.0), (103.0, 104.0)
ckl._get = lambda url, key, tries=4: {
    "status": "OK", "next_url": None,
    "results": [{"details": {"expiration_date": "2026-10-23", "contract_type": "call",
                             "strike_price": K}, "open_interest": 100} for K in _calls]
               + [{"details": {"expiration_date": "2026-10-23", "contract_type": "put",
                               "strike_price": K}, "open_interest": 100} for K in _puts]}
r5 = ckl._one("TEST", "k", {"TEST": _gex_zeile}, _SESSION)
if isinstance(r5, dict) and r5.get("max_pain_non_unique"):
    pruef("mehrdeutiges Max Pain -> nicht_eindeutig",
          (r5.get("felder") or {}).get("max_pain") == Z_NICHT_EINDEUTIG,
          (r5.get("felder") or {}).get("max_pain"))
else:
    pruef("[Aufbau] Fixture erzeugt kein mehrdeutiges Max Pain — Fall nicht geprueft",
          False, (r5 or {}).get("max_pain_non_unique"))


# ─────────────── 6 build(): key_levels.json traegt die Felder ────────────────────
print("\n[6] build() schreibt key_levels.json mit den Zustaenden")
ckl._get = lambda url, key, tries=4: {"status": "OK", "results": _kette(20),
                                      "next_url": None}
ckl._ROOT = _TMP
ckl.letzte_session = lambda boerse: _SESSION
ckl.pruefe_eod_fenster = lambda name: None
ckl._load_gex = lambda session, datei=None, lauf=None: ({"TEST": _gex_zeile}, "ok")
(_TMP / "landing" / "data").mkdir(parents=True, exist_ok=True)
out = ckl.build(["TEST"], write=True)
kl = _TMP / "landing" / "data" / "key_levels.json"
pruef("key_levels.json geschrieben", kl.exists())
if kl.exists():
    d = json.loads(kl.read_text(encoding="utf-8"))
    z = (d.get("tickers") or [{}])[0]
    pruef("Zeile traegt felder mit vier Niveaus",
          set(z.get("felder") or {}) == {"call_wall", "put_wall", "vol_trigger",
                                         "max_pain"}, sorted(z.get("felder") or {}))
    pruef("Zeile traegt Stufe, Quelle, Horizont und beide Ladezustaende",
          all(k in z for k in ("strike_stufe", "strike_stufe_quelle",
                              "gex_horizont_tage", "gex_kette_vollst",
                              "mp_kette_vollst")), sorted(z))

print("\nPROBE-ENDE %d" % _n)
if _fehler:
    print("\n[FEHLER] %d von %d Pruefungen rot" % (_fehler, _n))
    sys.exit(1)
print("\n[OK] alle %d Pruefungen gruen" % _n)
