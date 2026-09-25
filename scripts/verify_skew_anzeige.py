#!/usr/bin/env python3
"""verify_skew_anzeige.py — Anzeige = Ranking und Frische-Filter pruefen.

WARUM (Befund 2026-09-25):
  1. Die Tabelle auf /skew zeigte bei 33 von 158 Tickern einen 25Δ-Skew, der um
     mehr als 8 pts vom gerankten 30-Tage-Wert abwich (RSP +24,1 statt +3,8,
     SO −61 statt +1,2). Ursache: der Anzeigepfad pickte ueber das Delta des
     Anbieters, und das rechnet er aus der IV desselben Kontrakts — ein falsch
     bepreister Kontrakt waehlte sich selbst ins 25Δ-Fenster. Jetzt zeigt die
     Anzeige die 30-Tage-Werte (Variante a), leer wenn der Tag nicht rankbar ist.
  2. Der Ranking-Pfad nahm `day.close` ohne Zeitpruefung — auch Wochen alte oder
     vor einem Split entstandene Kurse (BKNG −32,0 statt +3,5, SEDG −40,3 statt
     −1,4). Jetzt nur Kurse aus der Session.

Prueft AUSFUEHREND, nicht per Textsuche: die Funktionen werden mit
synthetischen Kontrakten gerufen, build() laeuft mit `_ROOT` in einem
Temp-Verzeichnis und fester Uhr. Keine Netzzugriffe, keine echten Dateien.

Aufruf: py -3.14 scripts/verify_skew_anzeige.py      (Exit 1 = Fehler)
"""
from __future__ import annotations
import os
import sys

os.environ["SA_OHNE_DOTENV"] = "1"            # keine echten Schluessel
sys.dont_write_bytecode = True

import json                                   # noqa: E402
import tempfile                               # noqa: E402
from datetime import datetime                 # noqa: E402
from pathlib import Path                      # noqa: E402
from zoneinfo import ZoneInfo                 # noqa: E402

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.waechter_isolation import (melde_bilanz, nonce_sichern,   # noqa: E402
                                        schreibsperre, starte_isoliert)

# Die Cron-Module werden ERST im isolierten Unterprozess und NACH der
# Schreibsperre importiert (Codex-Review 2026-09-25: die erste Fassung fuehrte
# das echte _enrich ohne Sperre aus — eine Regression mit Schreibzugriff ins
# Repo waere weder verhindert noch bemerkt worden).
eh = None
m = None

PROBEN: list[str] = []
ERWARTETE_PROBEN = ("kursdatum", "frische", "anzeige", "enrich", "build", "audit")

ET = ZoneInfo("America/New_York")
UTC = ZoneInfo("UTC")
SESSION = "2026-09-24"


def _ns(jahr, monat, tag, stunde, minute, tz=ET) -> int:
    return int(datetime(jahr, monat, tag, stunde, minute, tzinfo=tz).timestamp() * 1e9)


def _zeile(ok: bool, text: str) -> int:
    print(f"  {'OK  ' if ok else 'FAIL'} {text}")
    return 0 if ok else 1


def _kontrakt(typ, K, px, lu, ex="2026-10-16", vol=5):
    return {"details": {"expiration_date": ex, "contract_type": typ, "strike_price": K,
                        "ticker": f"O:SPY261016{typ[0].upper()}{int(K * 1000):08d}"},
            "day": {"close": px, "volume": vol, **({"last_updated": lu} if lu else {})}}


def _synth_chain(S: float, zeitstempel_ns: int) -> list:
    """Chain im Massive-Format, Preise aus Black-Scholes mit Put-Skew-Smile.

    Zwei Monatsverfaelle (22 und 57 Tage) klammern die 30 Tage -> cm_mode 'cm'.
    Anbieterfelder (IV, Delta) stimmen mit den Preisen ueberein, damit der
    Anzeigepfad (_byexp) und der Ranking-Pfad (_own_cands) beide rechnen koennen.
    """
    import math
    from shared.black_scholes import bs_price, bs_delta
    out = []
    for ex, dte in (("2026-10-16", 22), ("2026-11-20", 57)):
        T = dte / 365.0
        for K in range(70, 131):
            m_ = math.log(K / S)
            sig = 0.20 - 0.08 * m_ + 0.30 * m_ * m_
            for typ in ("call", "put"):
                px = round(max(bs_price(S, K, T, sig, typ), 0.01), 2)
                out.append({
                    "details": {"expiration_date": ex, "contract_type": typ, "strike_price": float(K),
                                "ticker": f"O:SYN{ex[2:4]}{ex[5:7]}{ex[8:10]}{typ[0].upper()}{K * 1000:08d}"},
                    "implied_volatility": round(sig, 4),
                    "greeks": {"delta": round(bs_delta(S, K, T, sig, typ), 4)},
                    "open_interest": 100,
                    "day": {"close": px, "volume": 10, "last_updated": zeitstempel_ns}})
    return out


def _pruefe_echtes_enrich() -> int:
    import io, contextlib
    fehler = 0
    S = 100.0
    echte = {n: getattr(m, n) for n in ("_spot", "_chain", "_realized_vol")}
    echte_uhr = eh._uhr
    try:
        eh._uhr = lambda tz: datetime(2026, 9, 24, 23, 0, tzinfo=UTC).astimezone(tz)
        m._spot = lambda sym, key: S
        m._realized_vol = lambda sym, n=21, bis=None: (0.18, S, SESSION)
        for name, lu, soll_rankbar in (("frische Kurse", _ns(2026, 9, 24, 15, 30), True),
                                        ("Kurse vom 10.09. (veraltet)", _ns(2026, 9, 10, 15, 30), False)):
            m._chain = lambda sym, key, spot=None, _lu=lu: _synth_chain(S, _lu)
            with contextlib.redirect_stdout(io.StringIO()):
                r = m._enrich("SYN", "probe-kein-echter-schluessel")
            if r is None:
                fehler += _zeile(False, f"{name}: _enrich lieferte None")
                continue
            rankbar = m._rankbar(r)
            fehler += _zeile(rankbar == soll_rankbar,
                             f"{name}: cm_mode={r.get('cm_mode')} -> rankbar={rankbar} (soll {soll_rankbar})")
            fehler += _zeile("front_provider" in r, f"{name}: front_provider vorhanden")
            if soll_rankbar:
                gleich = (r.get("skew_pts") == r.get("cm_skew_pts") and r.get("iv_atm") == r.get("cm_iv_atm")
                          and r.get("skew_pts") is not None)
                fehler += _zeile(gleich, f"{name}: Anzeige = 30-Tage-Wert "
                                 f"(skew {r.get('skew_pts')} / cm {r.get('cm_skew_pts')})")
                # Plausibilitaet: der Smile hat Put-Skew -> positiver Skew erwartet
                fehler += _zeile((r.get("skew_pts") or 0) > 0,
                                 f"{name}: Vorzeichen stimmt (Put-Skew > 0: {r.get('skew_pts')})")
            else:
                fehler += _zeile(r.get("skew_pts") is None and r.get("iv_atm") is None,
                                 f"{name}: Anzeige leer statt Anbieterwert")
    finally:
        for n, v in echte.items():
            setattr(m, n, v)
        eh._uhr = echte_uhr
    return fehler


def _proben() -> int:
    """Alle ausfuehrenden Proben. Laeuft NUR im isolierten Unterprozess."""
    fehler = 0

    print("Kursdatum eines Tagesbalkens (ET, nicht UTC)\n" + "-" * 68)
    for name, lu, soll in [
        ("16:10 ET am 24.09.",                       _ns(2026, 9, 24, 16, 10), "2026-09-24"),
        ("21:30 ET am 24.09. = 01:30 UTC am 25.09.", _ns(2026, 9, 25, 1, 30, UTC), "2026-09-24"),
        ("Winter 16:05 EST = 21:05 UTC",             _ns(2026, 12, 1, 21, 5, UTC), "2026-12-01"),
        ("ohne Zeitstempel",                         None, None),
    ]:
        ist = m._kurs_datum({"last_updated": lu} if lu else {})
        fehler += _zeile(ist == soll, f"{name:<44} -> {ist}")
    PROBEN.append("kursdatum")

    print("\nFrische-Filter in _own_cands (Session " + SESSION + ")\n" + "-" * 68)
    cs = [_kontrakt("call", 700.0, 5.0, _ns(2026, 9, 24, 15, 0)),      # frisch
          _kontrakt("call", 710.0, 26.7, _ns(2026, 9, 10, 15, 0)),     # 14 Tage alt
          _kontrakt("put", 690.0, 4.0, None),                           # ohne Zeitstempel
          _kontrakt("put", 680.0, 3.0, _ns(2026, 9, 25, 1, 0, UTC))]   # 21:00 ET am 24. -> frisch
    import io, contextlib
    with contextlib.redirect_stdout(io.StringIO()):
        by = m._own_cands(cs, s30_ref=SESSION, underlying="SPY")
    ks = sorted(c["K"] for e in by.values() for c in e["cands"])
    fehler += _zeile(ks == [680.0, 700.0],
                     f"uebrig: {ks} (erwartet [680.0, 700.0] — 710 veraltet, 690 ohne Zeit)")
    PROBEN.append("frische")

    print("\nAnzeige = Ranking (_anzeige_aus_ranking)\n" + "-" * 68)
    def _roh(cm_mode):
        r = {"ticker": "RSP", "underlying": 210.26, "dte": 22, "rv_1m": 0.10,
             # Anbieterwerte wie am 2026-09-24 bei RSP gemessen: Put-Fluegel kaputt
             "call_25d": {"strike": 215, "iv": 0.1008, "delta": 0.241},
             "put_25d": {"strike": 199, "iv": 0.3563, "delta": -0.229},
             "skew_25d": 0.2555, "skew_pts": 25.55, "iv_atm": 0.1171, "atm_delta_dev": 0.01,
             "call_zeta_pts": -1.63, "put_zeta_pts": 23.92, "vrp_pts": 1.71,
             "bfly_pts": 11.15, "pc_ratio": 3.535, "em_pct": 2.9, "em_abs": 6.1, "em_dte": 22}
        if cm_mode:
            r.update({"cm_mode": cm_mode, "cm_dte": 30, "cm_call_iv": 0.1120, "cm_put_iv": 0.1498,
                      "cm_iv_atm": 0.1309, "cm_skew_pts": 3.78, "cm_call_zeta_pts": -1.89,
                      "cm_put_zeta_pts": 1.89, "cm_bfly_pts": 0.0})
        return r

    r = _roh("cm"); m._anzeige_aus_ranking(r)
    erwartet = {"skew_pts": 3.78, "iv_atm": 0.1309, "dte": 30, "bfly_pts": 0.0,
                "call_zeta_pts": -1.89, "put_zeta_pts": 1.89}
    for k, soll in erwartet.items():
        fehler += _zeile(r.get(k) == soll, f"rankbar: {k:<14} = {r.get(k)} (soll {soll})")
    fehler += _zeile(r["put_25d"]["iv"] == 0.1498 and r["call_25d"]["iv"] == 0.112,
                     f"rankbar: put/call_25d.iv = {r['put_25d']['iv']}/{r['call_25d']['iv']}")
    fehler += _zeile(r.get("pc_ratio") == round(0.1498 / 0.1120, 3),
                     f"rankbar: pc_ratio aus 30-Tage-IVs = {r.get('pc_ratio')}")
    fehler += _zeile(r.get("vrp_pts") == round((0.1309 - 0.10) * 100, 2),
                     f"rankbar: vrp_pts aus 30-Tage-ATM = {r.get('vrp_pts')}")
    fp = r.get("front_provider") or {}
    fehler += _zeile(fp.get("skew_pts") == 25.55 and (fp.get("put_25d") or {}).get("iv") == 0.3563,
                     "rankbar: Anbieterwerte unter front_provider erhalten")

    for modus in ("single", "noatm", None):
        r = _roh(modus); m._anzeige_aus_ranking(r)
        leer = all(r.get(k) is None for k in m._ANZEIGE_FELDER)
        fp = r.get("front_provider") or {}
        fehler += _zeile(leer and fp.get("skew_pts") == 25.55,
                         f"cm_mode={modus!s:<7}: Anzeige leer, front_provider erhalten")
    PROBEN.append("anzeige")

    # Das ECHTE _enrich muss die Umstellung selbst vornehmen. Die Proben oben
    # rufen _anzeige_aus_ranking direkt — ein entfernter Aufruf in _enrich blieb
    # dort unbemerkt (erste Mutationsprobe, Fall 21).
    print("\nEchtes _enrich mit synthetischer Chain\n" + "-" * 68)
    fehler += _pruefe_echtes_enrich()
    PROBEN.append("enrich")

    print("\nbuild(): History-Fallback liest front_provider (kein Absturz)\n" + "-" * 68)
    echte = {n: getattr(m, n) for n in ("_ROOT", "_enrich", "_index_series")}
    echte_uhr = eh._uhr
    alt_key = os.environ.get("MASSIVE_API_KEY")
    try:
        with tempfile.TemporaryDirectory(prefix="sa_anzeigeprobe_") as tmp:
            eh._uhr = lambda tz: datetime(2026, 9, 24, 23, 0, tzinfo=UTC).astimezone(tz)
            os.environ["MASSIVE_API_KEY"] = "probe-kein-echter-schluessel"
            m._ROOT = Path(tmp)
            m._index_series = lambda *a, **k: None
            def _synth(sym, key=None):
                r = _roh("single" if sym == "RSP" else "cm"); r["ticker"] = sym
                r.update({"cats": ["Broad-Index"], "put_vol": 1, "call_vol": 1,
                          "put_oi": 1, "call_oi": 1, "contango": True})
                m._anzeige_aus_ranking(r)
                return r
            m._enrich = _synth
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    m.build(["RSP", "SPY"], write=True)
                hist = json.loads((Path(tmp) / "landing/data/options_skew_history.json")
                                  .read_text(encoding="utf-8"))
                rsp, spy = hist["RSP"][-1], hist["SPY"][-1]
                fehler += _zeile(rsp.get("method") == "own_bs" and rsp.get("cm_mode") == "single"
                                 and rsp.get("skew_pts") == 3.78,
                                 f"nicht rankbar (single): History wie bisher cm-Werte, "
                                 f"skew {rsp.get('skew_pts')}")
                fehler += _zeile(spy.get("cm_mode") == "cm" and spy.get("skew_pts") == 3.78,
                                 f"rankbar: History-Zeile cm, skew {spy.get('skew_pts')}")
                out = json.loads((Path(tmp) / "landing/data/options_skew.json").read_text(encoding="utf-8"))
                zeile = {t["ticker"]: t for t in out["tickers"]}
                fehler += _zeile(zeile["RSP"].get("skew_pts") is None and zeile["SPY"].get("skew_pts") == 3.78,
                                 "Output: RSP leer, SPY 30-Tage-Wert")
            except Exception as e:
                fehler += _zeile(False, f"build() scheiterte: {type(e).__name__}: {e}")
            # Nicht normierter Tag ganz ohne cm: History bekommt die Anbieterwerte
            def _ohne_cm(sym, key=None):
                r = _roh(None); r["ticker"] = sym
                r.update({"cats": [], "put_vol": 1, "call_vol": 1, "put_oi": 1, "call_oi": 1})
                m._anzeige_aus_ranking(r)
                return r
            m._enrich = _ohne_cm
            (Path(tmp) / "landing/data/options_skew_history.json").unlink()
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    m.build(["XLC"], write=True)
                hist = json.loads((Path(tmp) / "landing/data/options_skew_history.json")
                                  .read_text(encoding="utf-8"))
                x = hist["XLC"][-1]
                fehler += _zeile(x.get("method") == "provider" and x.get("skew_pts") == 25.55
                                 and x.get("put_iv") == 0.3563,
                                 f"ohne cm: History-Fallback aus front_provider "
                                 f"(skew {x.get('skew_pts')}, put_iv {x.get('put_iv')})")
            except Exception as e:
                fehler += _zeile(False, f"build() ohne cm scheiterte: {type(e).__name__}: {e}")
    finally:
        for n, v in echte.items():
            setattr(m, n, v)
        eh._uhr = echte_uhr
        if alt_key is None:
            os.environ.pop("MASSIVE_API_KEY", None)
        else:
            os.environ["MASSIVE_API_KEY"] = alt_key
    PROBEN.append("build")
    return fehler


def _isoliert(tmp: str) -> int:
    """Unterprozess: Schreibsperre VOR dem Cron-Import, dann alle Proben."""
    global eh, m
    tmp_p = Path(tmp).resolve()
    verstoesse = schreibsperre(tmp_p)
    import shared.exchange_holidays as _eh
    import scripts.compute_options_skew as _m
    eh, m = _eh, _m
    fehler = _proben()
    print("\nSchreibzugriffe ausserhalb des Temp-Verzeichnisses (Audit-Hook)\n" + "-" * 68)
    fehler += _zeile(not verstoesse, f"{len(verstoesse)} gefunden")
    for v in verstoesse[:10]:
        print(f"       {v}")
    PROBEN.append("audit")
    return fehler


def pruefe() -> int:
    """Elternprozess: fuehrt selbst nichts aus, startet nur isoliert und prueft
    die Bilanz (Mechanik: scripts/waechter_isolation.py)."""
    fehler = starte_isoliert(Path(__file__), ERWARTETE_PROBEN, "sa_anzeigeprobe_")
    print("\n" + ("ERGEBNIS: PASS" if fehler == 0 else f"ERGEBNIS: {fehler} FAIL"))
    return 1 if fehler else 0


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--isoliert":
        nonce = nonce_sichern()          # vor jedem Cron-Import
        n = _isoliert(sys.argv[2])
        melde_bilanz(nonce, n, PROBEN)
        sys.exit(1 if n else 0)
    sys.exit(pruefe())
