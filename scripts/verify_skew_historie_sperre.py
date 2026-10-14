#!/usr/bin/env python3
"""
verify_skew_historie_sperre.py — gemeinsame Schreibsperre der Skew-History + ETHA-Reparaturmodus
(Plan docs/review_prompts/2026-10-14_options_sofortreparaturen_plan_v3.md / _v4.md, Paket B1).

Geprüft an den ECHTEN Funktionen, nur Netz/Kursquelle/Uhr ersetzt, alles in einem Temp-Verzeichnis:
  * shared.atomic_json.history_lesen / history_aktualisieren — defekt/fehlt → Abbruch ohne Schreiben,
    `aendern` → False schreibt nicht, `danach` nur nach erfolgreichem Schreiben
  * Parallelität (nur Linux, sonst UNGEPRÜFT; --streng macht UNGEPRÜFT rot): zwei Schreiber, beide Änderungen bleiben;
    belegte Sperre → SperreBelegt
  * compute_options_skew.build(write=True): defekte/fehlende History → keine der beiden Dateien geschrieben
  * backfill_skew_massive.main: Cron-Punkt, der während der Rekonstruktion entsteht, bleibt erhalten; defekte History
    → Exit 1, Datei unverändert; --overwrite ohne neue Punkte → keine Änderung
  * backfill_skew_vrp.main: dasselbe für die VRP-Nachrechnung; --dry-run schreibt nichts
  * backfill_skew_vrp --reparatur: Trockenlauf schreibt nur den Bericht; Schreiben nur gegen genau diesen Bericht;
    Abbruch bei geänderter Zielzeile, geänderter RV, anderem Bereich, fehlender Freigabe, RV außerhalb (0, 3);
    Cron-Punkt außerhalb des Bereichs bleibt; außer vrp_pts ändert sich nichts.
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
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

sys.dont_write_bytecode = True
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
STRENG = "--streng" in sys.argv
_TMP = Path(tempfile.mkdtemp(prefix="sa_histsperre_"))
os.environ["SA_SPERR_DIR"] = str(_TMP / "sperre")       # VOR jedem Import, der die Sperre nutzt
os.environ["SA_OHNE_DOTENV"] = "1"


def _absturz(typ, wert, tb):
    import traceback
    traceback.print_exception(typ, wert, tb)
    print("[Absturz]")
    shutil.rmtree(_TMP, ignore_errors=True)
    os._exit(3)


sys.excepthook = _absturz

# Im Gate fehlt streamlit; shared.yahoo_downloader braucht nur den Dekorator st.cache_data (+ .clear).
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

import shared.atomic_json as aj                                          # noqa: E402
from shared.atomic_json import (history_lesen, history_aktualisieren,   # noqa: E402
                                HistorieDefekt, SperreBelegt)

UTC = ZoneInfo("UTC")
FEHLER, UNGEPRUEFT = [], []


def pruef(name, ok, info=""):
    print(f"  {'ok  ' if ok else 'FAIL'} {name}" + (f"  ->  {info}" if info else ""))
    if not ok:
        FEHLER.append(name)


def _wirft(fn, typ):
    try:
        fn()
    except typ:
        return True
    except Exception as e:                      # falsche Klasse ist ein Befund, kein Absturz
        return f"{type(e).__name__}: {e}"
    return False


def _lies(p: Path) -> dict:
    """Datei als dict; unlesbar/kein dict -> {} (der Vergleich wird dann rot, statt den Waechter abstuerzen zu lassen)."""
    try:
        x = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return x if isinstance(x, dict) else {}


def _neu(name: str) -> Path:
    d = _TMP / name
    d.mkdir(parents=True, exist_ok=True)
    return d


def _ruhig(fn, *a, **k):
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return fn(*a, **k)


# ── 1. Helfer ─────────────────────────────────────────────────────────────────────────────────────────────────────
print("== history_lesen / history_aktualisieren")
d = _neu("helfer")
f = d / "h.json"
pruef("fehlt ohne neu_erlaubt -> HistorieDefekt", _wirft(lambda: history_lesen(f), HistorieDefekt) is True)
pruef("fehlt mit neu_erlaubt -> {}", history_lesen(f, neu_erlaubt=True) == {})
f.write_text("{kaputt", encoding="utf-8")
vorher = f.read_bytes()
aufgerufen = []
pruef("unlesbar -> HistorieDefekt", _wirft(lambda: history_aktualisieren(
    f, lambda h: h.update(x=1), danach=lambda h: aufgerufen.append(1)), HistorieDefekt) is True)
pruef("... Datei unverändert, danach nicht gerufen", f.read_bytes() == vorher and not aufgerufen)
f.write_text("[1, 2]", encoding="utf-8")
pruef("kein Objekt -> HistorieDefekt", _wirft(lambda: history_lesen(f), HistorieDefekt) is True)
f.write_text('{"a": 1}', encoding="utf-8")
vorher = f.read_bytes()
pruef("aendern -> False schreibt nicht", history_aktualisieren(f, lambda h: False,
                                                              danach=lambda h: aufgerufen.append(1)) is None
      and f.read_bytes() == vorher and not aufgerufen)
erg = history_aktualisieren(f, lambda h: h.update(b=2), danach=lambda h: aufgerufen.append(dict(h)))
pruef("Normalfall: geschrieben, danach mit dem geschriebenen Stand", json.loads(f.read_text()) == {"a": 1, "b": 2}
      and aufgerufen == [{"a": 1, "b": 2}])

# ── 2. Parallelität ───────────────────────────────────────────────────────────────────────────────────────────────
print("== zwei Schreiber gleichzeitig")
if aj.fcntl is None:
    print("  UNGEPRÜFT — kein fcntl auf diesem System (Prüfung läuft im Linux-Gate)")
    UNGEPRUEFT.append("Parallelität")
else:
    d = _neu("parallel")
    f, sperre, marke = d / "h.json", d / "x.lock", d / "a_hat_sperre"
    f.write_text("{}", encoding="utf-8")
    prog = (f"import sys,time; sys.path.insert(0,{str(_ROOT)!r})\n"
            "from shared.atomic_json import history_aktualisieren\n"
            "def a(h):\n"
            f"    open({str(marke)!r},'w').close(); time.sleep(float(sys.argv[1])); h['A']=1\n"
            f"history_aktualisieren({str(f)!r}, a, sperrdatei={str(sperre)!r})\n")

    def _starte_a(schlaf):
        marke.unlink(missing_ok=True)
        pa = subprocess.Popen([sys.executable, "-c", prog, str(schlaf)])
        ende = time.monotonic() + 20
        while not marke.exists() and time.monotonic() < ende:
            time.sleep(0.05)
        return pa

    pa = _starte_a(1.5)
    history_aktualisieren(f, lambda h: h.__setitem__("B", 1), sperrdatei=sperre)
    pa.wait(timeout=30)
    pruef("beide Änderungen erhalten (B wartete auf A)", json.loads(f.read_text()) == {"A": 1, "B": 1},
          f.read_text())
    pa = _starte_a(3)
    pruef("belegte Sperre mit kurzer Frist -> SperreBelegt",
          _wirft(lambda: history_aktualisieren(f, lambda h: None, sperrdatei=sperre, frist_s=0.5), SperreBelegt) is True)
    pa.wait(timeout=30)
    # danach (beim Cron: der Snapshot) laeuft noch UNTER der Sperre
    prog_d = (f"import sys,time; sys.path.insert(0,{str(_ROOT)!r})\n"
              "from shared.atomic_json import history_aktualisieren\n"
              "def d(h):\n"
              f"    open({str(marke)!r},'w').close(); time.sleep(2.5)\n"
              f"history_aktualisieren({str(f)!r}, lambda h: h.update(D=1), danach=d, sperrdatei={str(sperre)!r})\n")
    marke.unlink(missing_ok=True)
    pd = subprocess.Popen([sys.executable, "-c", prog_d])
    ende = time.monotonic() + 20
    while not marke.exists() and time.monotonic() < ende:
        time.sleep(0.05)
    pruef("während danach ist die Sperre noch belegt -> SperreBelegt",
          _wirft(lambda: history_aktualisieren(f, lambda h: None, sperrdatei=sperre, frist_s=0.5), SperreBelegt) is True)
    pd.wait(timeout=30)

# ── 3. Options-Cron ───────────────────────────────────────────────────────────────────────────────────────────────
print("== compute_options_skew.build(write=True)")
import shared.exchange_holidays as eh                                    # noqa: E402
import scripts.compute_options_skew as cs                                # noqa: E402

eh._uhr = lambda tz: datetime(2026, 9, 24, 23, 0, tzinfo=UTC).astimezone(tz)
os.environ["MASSIVE_API_KEY"] = "probe-kein-echter-schluessel"
cs._index_series = lambda *a, **k: None


def _synth(sym, key=None):
    return {"ticker": sym, "cats": ["Broad-Index"], "underlying": 700.0, "dte": 21,
            "put_vol": 100, "call_vol": 100, "put_oi": 1000, "call_oi": 1000,
            "call_25d": {"strike": 720, "iv": 0.19, "delta": 0.25},
            "put_25d": {"strike": 680, "iv": 0.22, "delta": -0.25},
            "skew_pts": 3.0, "call_zeta_pts": -1.0, "put_zeta_pts": 2.0,
            "iv_atm": 0.20, "vrp_pts": 2.0, "bfly_pts": 0.5, "pc_ratio": 1.15,
            "contango": True, "rv_1m": 0.18,
            "cm_mode": "cm", "cm_dte": 30, "cm_skew_pts": 3.0, "cm_put_iv": 0.22,
            "cm_call_iv": 0.19, "cm_iv_atm": 0.20, "cm_bfly_pts": 0.5,
            "cm_call_zeta_pts": -1.0, "cm_put_zeta_pts": 2.0}


cs._enrich = _synth


def _cron(name, hist_inhalt):
    w = _neu(name)
    (w / "landing/data").mkdir(parents=True, exist_ok=True)
    hp, sp = w / "landing/data/options_skew_history.json", w / "landing/data/options_skew.json"
    if hist_inhalt is not None:
        hp.write_text(hist_inhalt, encoding="utf-8")
    sp.write_text('{"ALT": true}', encoding="utf-8")
    cs._ROOT = w
    try:
        _ruhig(cs.build, ["SPY"], write=True)
        res = "lief"
    except HistorieDefekt:
        res = "HistorieDefekt"
    return res, hp, sp


res, hp, sp = _cron("cron_ok", "{}")
pruef("Normalfall: History mit SPY 2026-09-24, Snapshot neu",
      res == "lief" and json.loads(hp.read_text())["SPY"][-1]["date"] == "2026-09-24"
      and json.loads(sp.read_text()).get("session") == "2026-09-24", res)
res, hp, sp = _cron("cron_defekt", "{kaputt")
pruef("defekte History: Abbruch, History UND Snapshot unverändert",
      res == "HistorieDefekt" and hp.read_text() == "{kaputt" and sp.read_text() == '{"ALT": true}', res)
res, hp, sp = _cron("cron_fehlt", None)
pruef("fehlende History: Abbruch, keine History, Snapshot unverändert",
      res == "HistorieDefekt" and not hp.exists() and sp.read_text() == '{"ALT": true}', res)

# ── 4. Massive-Backfill ───────────────────────────────────────────────────────────────────────────────────────────
print("== backfill_skew_massive.main")
import scripts.backfill_skew_massive as bf                               # noqa: E402

bf.clear_cache = lambda: None


def _bf_lauf(name, hist, neue, *argv, cron_dazwischen=None):
    w = _neu(name)
    (w / "landing/data").mkdir(parents=True, exist_ok=True)
    hp = w / "landing/data/options_skew_history.json"
    hp.write_text(hist if isinstance(hist, str) else json.dumps(hist), encoding="utf-8")
    bf._ROOT = w

    def _rt(sym, *a, **k):
        if cron_dazwischen:                     # der Cron schreibt, waehrend der Backfill rechnet
            h = json.loads(hp.read_text())
            h.setdefault(sym, []).append(cron_dazwischen)
            hp.write_text(json.dumps(h), encoding="utf-8")
        return [dict(r) for r in neue]

    bf.run_ticker = _rt
    alt = sys.argv
    sys.argv = ["backfill_skew_massive.py", "--symbols", "SPY", *argv]
    try:
        rc = _ruhig(bf.main)
    except Exception as e:              # eine Ausnahme aus main ist ein Befund (rot), kein Absturz des Waechters
        rc = f"Ausnahme {type(e).__name__}: {e}"
    finally:
        sys.argv = alt
    return rc, hp


basis = {"SPY": [{"date": "2026-09-01", "src": "massive", "skew_pts": 1.0},
                 {"date": "2026-09-02", "method": "own_bs", "skew_pts": 2.0}]}
neu_r = [{"date": "2026-09-03", "src": "massive", "skew_pts": 3.0}]
cron_r = {"date": "2026-09-24", "method": "own_bs", "skew_pts": 9.0}
rc, hp = _bf_lauf("bf_ok", basis, neu_r, cron_dazwischen=cron_r)
daten = [e["date"] for e in _lies(hp).get("SPY", [])]
pruef("Cron-Punkt während der Rekonstruktion bleibt, neuer Punkt dazu",
      rc == 0 and daten == ["2026-09-01", "2026-09-02", "2026-09-03", "2026-09-24"], f"rc {rc}, {daten}")
rc, hp = _bf_lauf("bf_bestand", basis, [{"date": "2026-09-02", "src": "massive", "skew_pts": 99.0}] + neu_r)
x = {e["date"]: e for e in _lies(hp).get("SPY", [])}
pruef("ohne --overwrite: vorhandenes Datum bleibt (Live-Zeile nicht ersetzt)",
      (x.get("2026-09-02") or {}).get("skew_pts") == 2.0, x.get("2026-09-02"))
rc, hp = _bf_lauf("bf_over", basis, neu_r, "--overwrite", cron_dazwischen=cron_r)
daten = [e["date"] for e in _lies(hp).get("SPY", [])]
pruef("--overwrite: alte Rekonstruktion raus, Live und Cron-Punkt bleiben",
      rc == 0 and daten == ["2026-09-02", "2026-09-03", "2026-09-24"], f"rc {rc}, {daten}")
rc, hp = _bf_lauf("bf_over_leer", basis, [], "--overwrite")
pruef("--overwrite ohne neue Punkte: Datei unverändert", _lies(hp) == basis)
rc, hp = _bf_lauf("bf_defekt", "{kaputt", neu_r)
pruef("defekte History: Exit 1, Datei unverändert", rc == 1 and hp.read_text() == "{kaputt", f"rc {rc}")

# ── 5. VRP-Nachrechnung ───────────────────────────────────────────────────────────────────────────────────────────
print("== backfill_skew_vrp.main")
import scripts.backfill_skew_vrp as bv                                   # noqa: E402

RV = {"2026-09-30": 0.40, "2026-10-01": 0.41, "2026-10-02": 0.42, "2026-10-05": 0.43}


def _vrp_lauf(name, hist, *argv, cron_dazwischen=None, rv=None):
    w = _neu(name) if not (_TMP / name).exists() else _TMP / name
    hp = w / "h.json"
    if hist is not None:
        hp.write_text(hist if isinstance(hist, str) else json.dumps(hist), encoding="utf-8")
    bv.HISTORIE, bv.REPARATUR_DIR = hp, w / "reparatur"

    def _rv(h, nur, stat):
        if cron_dazwischen:
            x = json.loads(hp.read_text())
            x.setdefault(cron_dazwischen[0], []).append(cron_dazwischen[1])
            hp.write_text(json.dumps(x), encoding="utf-8")
        out = {}
        for t in h:
            if t.startswith("__") or (nur and t not in nur):
                continue
            out[t] = dict(rv or RV)
            stat["ticker"] += 1
        return out

    bv.rv_laden = _rv
    alt = sys.argv
    sys.argv = ["backfill_skew_vrp.py", *argv]
    puffer = io.StringIO()
    try:
        with contextlib.redirect_stdout(puffer):
            rc = bv.main()
    except Exception as e:
        rc = f"Ausnahme {type(e).__name__}: {e}"
    finally:
        sys.argv = alt
    return rc, hp, puffer.getvalue()


def _z(dt, vrp, cm="cm", iv=0.5, **k):
    return dict({"date": dt, "cm_mode": cm, "iv_atm": iv, "vrp_pts": vrp, "skew_pts": 1.0}, **k)


h_etha = {"ETHA": [_z("2026-09-29", 5.0), _z("2026-09-30", -333.0), _z("2026-10-01", -330.0),
                   _z("2026-10-02", -320.0, cm="single"), _z("2026-10-05", -300.0)],
          "SPY": [_z("2026-10-01", 3.0)]}
rc, hp, _o = _vrp_lauf("vrp_dry", h_etha, "--dry-run")
pruef("--dry-run: Datei unverändert", rc == 0 and json.loads(hp.read_text()) == h_etha)
rc, hp, _o = _vrp_lauf("vrp_voll", h_etha, "--ticker", "SPY", "--trotzdem",
                       cron_dazwischen=("QQQ", _z("2026-10-06", 1.0)))
x = _lies(hp)
pruef("Nachrechnung: Cron-Punkt (QQQ) bleibt, SPY gesetzt",
      rc == 0 and bool(x.get("QQQ")) and (x.get("SPY") or [{}])[0].get("vrp_pts") == round((0.5 - 0.41) * 100, 2),
      f"rc {rc}")
rc, hp, _o = _vrp_lauf("vrp_defekt", "{kaputt", "--trotzdem")
pruef("defekte History: Exit 1, unverändert", rc == 1 and hp.read_text() == "{kaputt", f"rc {rc}")

# ── 6. Reparaturmodus ─────────────────────────────────────────────────────────────────────────────────────────────
print("== backfill_skew_vrp --reparatur (R1c)")
BER = ["--reparatur", "--ticker", "ETHA", "--von", "2026-09-30", "--bis", "2026-10-05"]


def _trocken(name, hist=h_etha, **k):
    rc, hp, out = _vrp_lauf(name, hist, *BER, **k)
    berichte = sorted((hp.parent / "reparatur").glob("vrp_ETHA_*.json")) if (hp.parent / "reparatur").exists() else []
    return rc, hp, (berichte[-1] if berichte else None)


rc, hp, ber = _trocken("rep_ok")
pruef("Trockenlauf: Bericht geschrieben, History unverändert",
      rc == 0 and ber is not None and _lies(hp) == h_etha, f"rc {rc}")
b = json.loads(ber.read_text()) if ber else {"zeilen": []}
geaendert = {e["date"]: e["vrp_neu"] for e in b["zeilen"] if "vrp_neu" in e}
pruef("Bericht: nur cm-Zeilen im Bereich, single und Datum davor nicht",
      sorted(geaendert) == ["2026-09-30", "2026-10-01", "2026-10-05"], sorted(geaendert))
pruef("Bericht: vrp_neu = (iv_atm − RV)·100", geaendert.get("2026-09-30") == round((0.5 - 0.40) * 100, 2))

rc, hp, _o = _vrp_lauf("rep_ok", None, *BER, "--schreiben", "--freigabe-datei", str(ber),
                       cron_dazwischen=("ETHA", _z("2026-10-13", 7.0)))
x = _lies(hp)
nachher = {e["date"]: e for e in x.get("ETHA", [])}
pruef("Schreiben gegen den Bericht: Zielwerte gesetzt", rc == 0 and bool(geaendert) and all(
    (nachher.get(dd) or {}).get("vrp_pts") == v for dd, v in geaendert.items()), f"rc {rc}")
pruef("... Cron-Punkt außerhalb des Bereichs bleibt", "2026-10-13" in nachher)
erwartet = json.loads(json.dumps(h_etha))
for e in erwartet["ETHA"]:
    if e["date"] in geaendert:
        e["vrp_pts"] = geaendert[e["date"]]
erwartet["ETHA"].append(_z("2026-10-13", 7.0))
pruef("... sonst nichts geändert (alle übrigen Felder/Zeilen/Ticker gleich)", x == erwartet)

rc, hp, ber = _trocken("rep_zeile")
h2 = _lies(hp)
if h2.get("ETHA"):
    h2["ETHA"][1]["iv_atm"] = 0.6
hp.write_text(json.dumps(h2), encoding="utf-8")
vor = hp.read_bytes()
rc, hp, _o = _vrp_lauf("rep_zeile", None, *BER, "--schreiben", "--freigabe-datei", str(ber))
pruef("Zielzeile zwischen den Läufen geändert -> Abbruch, nichts geschrieben", rc == 2 and hp.read_bytes() == vor,
      f"rc {rc}")
rc, hp, ber = _trocken("rep_rv")
vor = hp.read_bytes()
rc, hp, _o = _vrp_lauf("rep_rv", None, *BER, "--schreiben", "--freigabe-datei", str(ber),
                       rv=dict(RV, **{"2026-10-01": 0.45}))
pruef("RV zwischen den Läufen geändert -> Abbruch", rc == 2 and hp.read_bytes() == vor, f"rc {rc}")
rc, hp, ber = _trocken("rep_bereich")
vor = hp.read_bytes()
rc, hp, _o = _vrp_lauf("rep_bereich", None, "--reparatur", "--ticker", "ETHA", "--von", "2026-09-30", "--bis",
                       "2026-10-01", "--schreiben", "--freigabe-datei", str(ber))
pruef("anderer Bereich als im Bericht -> Abbruch", rc == 2 and hp.read_bytes() == vor, f"rc {rc}")
rc, hp, _o = _vrp_lauf("rep_bereich", None, *BER, "--schreiben")
pruef("--schreiben ohne Freigabedatei -> Exit 1, nichts geschrieben", rc == 1 and hp.read_bytes() == vor, f"rc {rc}")
h_dup = json.loads(json.dumps(h_etha))
h_dup["ETHA"].insert(2, _z("2026-09-30", 1.0, cm="single"))
rc, hp, ber = _trocken("rep_dup", h_dup)
pruef("doppeltes Datum im Bereich -> nicht zulässig, kein Bericht", rc == 2 and ber is None, f"rc {rc}")
d_dup = bv.reparatur_diff(h_dup, "ETHA", "2026-09-30", "2026-10-05", RV)
h_dup2 = json.loads(json.dumps(h_dup))
pruef("reparatur_anwenden lehnt doppelte Daten selbst ab (nichts geändert)",
      _wirft(lambda: bv.reparatur_anwenden(h_dup2, d_dup), RuntimeError) is True and h_dup2 == h_dup)

h_ohne = json.loads(json.dumps(h_etha))
del h_ohne["ETHA"][1]["vrp_pts"]                 # Feld fehlt ganz
h_ohne["ETHA"][2]["vrp_pts"] = None              # Feld explizit null
rc, hp, ber = _trocken("rep_ohne", h_ohne)
rc2, hp, _o = _vrp_lauf("rep_ohne", None, *BER, "--schreiben", "--freigabe-datei", str(ber)) if ber else (None, hp, "")
x = {e["date"]: e for e in _lies(hp).get("ETHA", [])}
pruef("fehlendes und explizit leeres vrp_pts: Reparatur zulässig und gesetzt",
      rc == 0 and rc2 == 0 and (x.get("2026-09-30") or {}).get("vrp_pts") == round((0.5 - 0.40) * 100, 2)
      and (x.get("2026-10-01") or {}).get("vrp_pts") == round((0.5 - 0.41) * 100, 2), f"rc {rc}/{rc2}")

rc, hp, ber = _trocken("rep_rvgrenze", rv=dict(RV, **{"2026-10-01": 3.8}))
pruef("RV außerhalb (0, 3) -> nicht zulässig, kein Bericht", rc == 2 and ber is None, f"rc {rc}")

# ── Ergebnis ──────────────────────────────────────────────────────────────────────────────────────────────────────
shutil.rmtree(_TMP, ignore_errors=True)
print()
if UNGEPRUEFT:
    print("UNGEPRÜFT: " + ", ".join(UNGEPRUEFT))
if FEHLER or (STRENG and UNGEPRUEFT):
    print(f"[FAIL] {len(FEHLER)} Prüfung(en)" + (" + ungeprüft im strengen Modus" if STRENG and UNGEPRUEFT else "")
          + (": " + "; ".join(FEHLER) if FEHLER else ""))
    sys.exit(1)
print("[OK] alle Prüfungen grün" + (" (ohne Parallelität — nur unter Linux)" if UNGEPRUEFT else ""))
