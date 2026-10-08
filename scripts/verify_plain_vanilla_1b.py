#!/usr/bin/env python3
"""
verify_plain_vanilla_1b.py — Wächter Phase 1B der Seite /plain-vanilla (Plan v3, Codex-Freigabe Plan-Runde 3).

    py -3.14 scripts/verify_plain_vanilla_1b.py --snapshot <ordner>     # alle Prüfungen inkl. Snapshot
    py -3.14 scripts/verify_plain_vanilla_1b.py --ohne-snapshot          # ohne die Snapshot-Prüfungen (ausdrücklich)
    py -3.14 scripts/verify_plain_vanilla_1b.py --mutationen

Teile:
  1. JS: `scripts/js/probe_plain_vanilla_1b.js` (echte Module): Termine (T), Hebelpfad (H), Stops auf dem Pfad (S2),
     Lücken und Näherung (L/V1), tägliche Equity (E), Ergebnisvertrag (E2).
  2. Python-Zwilling: dieselben Eingaben, Werte gegen JS auf 1e-9; Feiertagsanker 2000–2035 = JS; Close-Stop statt
     OHLC (S3, Codex-Fall Open 100/Low 90/Close 105); Legacy-Konsumenten (Ultimate Monthly, KTI) gegen den Stand 1A
     unverändert (V2).
  3. Kalender: `verify_kalender_zwilling.pruefe()` mit festen Sollwerten (K3/V4).
  4. Statisch: Seite und Streamlit lesen die Tageswerte ausdrücklich aus `taeglich` (E2/E4).
  5. Snapshot (nur mit --snapshot): Monthly 10 SPY 1994–2025 gegen die Referenzlogik von
     `scripts/research/monthly10_blogzahlen.py` auf denselben Zeilen (1e-9, beide CAGR-Konventionen); der veröffentlichte
     Wert wird nur berichtet. ^GDAXI 0 fehlende Sitzungen 2000–2025 (unter der dokumentierten Annahme 24.12.2001).
     Python = JS über `plain_vanilla_zwilling.py` für alle Strategien außer den Phase-3-Fällen (LBR, Midterm, UECS).
Ohne Snapshot und ohne --ohne-snapshot ist das Ergebnis UNGEPRÜFT (Exit 1) — fehlender Zugriff ist nie bestanden.

--mutationen: wie in 1A — jede Mutation benennt die Prüfung, die reißen MUSS; eine gerissene [Aufbau]-Prüfung oder
eine abgebrochene Probe macht sie UNGÜLTIG; `UNGUELTIG_ERWARTET` prüft das Urteil des Tests selbst.
"""
from __future__ import annotations

import importlib.util
import json
import math
import pathlib
import shutil
import subprocess
import sys
import tempfile
from datetime import date, timedelta

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
PROBE = REPO / "scripts" / "js" / "probe_plain_vanilla_1b.js"
JS = "landing/js/strategy-compute.js"
HOL = "landing/js/holidays.js"
PV = "landing/pages/plain-vanilla.html"
ST = "pages/09_Plain_Vanilla_Strategien.py"
PYZ = "shared/strategies/plain_vanilla.py"
STAND_1A = "6170252"
PHASE3 = {"lbr_november_mai", "midterm_election", "uecs"}


def nah(a, b, tol=1e-9):
    return a is not None and b is not None and math.isclose(a, b, rel_tol=tol, abs_tol=tol)


# ── 1. JS ────────────────────────────────────────────────────────────────────
def js_lauf(basis: pathlib.Path, spy: pathlib.Path | None = None) -> dict:
    cmd = ["node", str(PROBE), str(basis)] + ([str(spy)] if spy else [])
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    zeilen = r.stdout.strip().splitlines()
    if r.returncode != 0 or len(zeilen) < 2 or zeilen[-1] != "ENDE":
        raise RuntimeError("Probe ohne Endmarker: " + (r.stderr or r.stdout)[-300:])
    return json.loads(zeilen[0])


# ── 2. Python ────────────────────────────────────────────────────────────────
def lade_modul(pfad: pathlib.Path, name: str):
    spec = importlib.util.spec_from_file_location(name, pfad)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def py_pruefungen(basis: pathlib.Path, W: dict) -> dict:
    import pandas as pd
    from shared.exchange_holidays import is_trading_day
    pv = lade_modul(basis / PYZ, "pv_1b")
    P = {}

    def df_aus(von, bis, fn, boerse="NYSE", ohne=()):
        d, z = date.fromisoformat(von), []
        while d <= date.fromisoformat(bis):
            if is_trading_day(d, boerse) and d.isoformat() not in ohne:
                z.append((pd.Timestamp(d), fn(d.isoformat(), len(z))))
            d += timedelta(days=1)
        df = pd.DataFrame({"Close": [c for _, c in z]}, index=pd.DatetimeIndex([t for t, _ in z]))
        df["year"], df["month"] = df.index.year, df.index.month
        return df

    def zeilen(liste):
        df = pd.DataFrame({"Close": [c for _, c in liste]}, index=pd.DatetimeIndex([pd.Timestamp(d) for d, _ in liste]))
        df["year"], df["month"] = df.index.year, df.index.month
        return df

    def trade(e, x, pe=100.0, px=100.0, r=0.0, **kw):
        return {"entry_date": pd.Timestamp(e), "exit_date": pd.Timestamp(x), "entry_price": pe, "exit_price": px,
                "return_pct": r, **kw}

    def nov(tr):
        return [t for t in tr if pd.Timestamp("2024-11-01") <= t["entry_date"] <= pd.Timestamp("2024-11-30")]

    def mit(stichtag, boerse, fn):
        tok = pv.set_kontext(date.fromisoformat(stichtag), boerse)
        try:
            return fn()
        finally:
            pv._KONTEXT_VAR.reset(tok)

    def pruefe(name, fn):
        try:
            r = fn()
            P[name] = True if r is True else str(r)
        except Exception as e:  # noqa: BLE001
            P[name] = f"Ausnahme: {type(e).__name__}: {e}"

    def ts(t):
        return f"{t['entry_date'].date()}→{t['exit_date'].date()}"

    def t_thx():
        df = df_aus("2024-11-01", "2024-12-31", lambda s, i: 100.0)
        u = nov(mit("2024-12-31", "NYSE", lambda: pv.calc_uhts(df)))
        if len(u) != 1 or ts(u[0]) != "2024-11-25→2024-12-03":
            return f"UHTS {[ts(t) for t in u]}, soll 2024-11-25→2024-12-03"
        o = nov(mit("2024-12-31", "NYSE", lambda: pv.calc_one_day_holiday(df)))
        return True if [ts(t) for t in o] == ["2024-11-26→2024-11-27"] else f"One-Day {[ts(t) for t in o]}"
    pruefe("py_t_thanksgiving", t_thx)

    def t_xetra():
        df = df_aus("2024-11-01", "2024-12-31", lambda s, i: 100.0, boerse="XETRA")
        u = nov(mit("2024-12-31", "XETRA", lambda: pv.calc_uhts(df)))
        if len(u) != 1:
            return f"erwartet 1 Trade, ist {len(u)}"
        h = {d.date().isoformat(): x for d, x in u[0]["hebel"]}
        return True if (h.get("2024-11-27") == 1 and h.get("2024-11-28") == 2) else f"Hebel {h}"
    pruefe("py_t_xetra_feiertag_offen", t_xetra)

    treppe = {"2024-11-25": 100, "2024-11-26": 110, "2024-11-27": 99, "2024-11-29": 108.9, "2024-12-02": 119.79,
              "2024-12-03": 107.811}

    def h_treppe():
        df = df_aus("2024-11-01", "2024-12-31", lambda s, i: float(treppe.get(s, 100)))
        u = nov(mit("2024-12-31", "NYSE", lambda: pv.calc_uhts(df)))[0]
        soll = (1.1 * 0.9 * 1.2 * 1.2 * 0.8 - 1) * 100
        if not nah(u["return_pct"], soll):
            return f"Rendite {u['return_pct']}, soll {soll}"
        return True if nah(u["return_pct"], W.get("h_treppe")) else f"Python {u['return_pct']} ≠ JS {W.get('h_treppe')}"
    pruefe("py_h_treppe", h_treppe)

    stopk = {"2024-11-25": 100, "2024-11-26": 101, "2024-11-27": 100, "2024-11-29": 90}

    def h_stop():
        df = df_aus("2024-11-01", "2024-12-31", lambda s, i: float(stopk.get(s, 90)))
        for typ in ("fixed", "trailing"):
            r = pv.auswerten(df, "uhts", boerse="NYSE", stichtag=date(2024, 12, 31), stop_pct=8.0, stop_type=typ)
            t = nov(r["trades"])[0]
            if not t.get("stopped") or t["exit_date"] != pd.Timestamp("2024-11-29"):
                return f"{typ}: kein Stop am 29.11. ({ts(t)})"
            if not nah(t["return_pct"], -20) or not nah(t["return_pct"], W.get("h_stop_" + typ)):
                return f"{typ}: Rendite {t['return_pct']} (JS {W.get('h_stop_' + typ)}, soll −20)"
            if len(t["hebel"]) != 3:
                return f"{typ}: Pfad nicht gekürzt ({len(t['hebel'])})"
        return True
    pruefe("py_h_stop", h_stop)

    def h_offen():
        df = df_aus("2024-11-01", "2024-11-26", lambda s, i: 100.0 + i)
        r = pv.auswerten(df, "uhts", boerse="NYSE", stichtag=date(2024, 11, 26))
        t = nov(r["trades"])
        if not t or not t[0].get("open"):
            return "kein offener Trade"
        if any(h != 1 for _, h in t[0]["hebel"]):
            return "Hebel vor der Aufstockung ≠ 1"
        zu = [x for x in r["trades"] if not x.get("open")]
        return True if (not r["stats"] or r["stats"]["n_trades"] == len(zu)) else "offener Trade in den Kennzahlen"
    pruefe("py_h_offen_rand", h_offen)

    def l_fall(rows, e, x, stichtag, boerse="NYSE"):
        t = trade(e, x)
        mit(stichtag, boerse, lambda: pv._luecken_markieren(zeilen([(d, 100.0) for d in rows]), [t]))
        return [t["fehlende_sitzungen"], t["auffaellige_abstaende"]]

    def l_2015():
        rows = [d for d in ("2015-01-12", "2015-01-13", "2015-01-15", "2015-01-16")]
        ist = l_fall(rows, "2015-01-12", "2015-01-16", "2015-01-16")
        return True if ist == [1, 0] == W.get("l_2015") else f"Python {ist}, JS {W.get('l_2015')}, soll [1, 0]"
    pruefe("py_l_2015", l_2015)

    def l_vor2000():
        rows = ["1995-01-05", "1995-01-06", "1995-01-11", "1995-01-13", "1995-01-17"]
        a = l_fall(rows, "1995-01-05", "1995-01-11", "1995-01-17")[1]
        b = l_fall(rows, "1995-01-13", "1995-01-17", "1995-01-17")[1]
        return True if [a, b] == [1, 0] == W.get("l_vor2000") else f"Python {[a, b]}, JS {W.get('l_vor2000')}"
    pruefe("py_l_vor2000", l_vor2000)

    def l_jw():
        rows = ["1999-12-28", "1999-12-29", "1999-12-31", "2000-01-03", "2000-01-05"]
        ist = l_fall(rows, "1999-12-28", "2000-01-05", "2000-01-05")
        return True if ist == [1, 0] == W.get("l_jahreswechsel") else f"Python {ist}, JS {W.get('l_jahreswechsel')}"
    pruefe("py_l_jahreswechsel", l_jw)

    def l_naeh():
        ka = {"2024-11-22": 100, "2024-11-25": 100, "2024-11-26": 100, "2024-11-29": 121}
        df = df_aus("2024-11-01", "2024-12-31", lambda s, i: float(ka.get(s, 121)), ohne={"2024-11-27"})
        a = nov(pv.auswerten(df, "uhts", boerse="NYSE", stichtag=date(2024, 12, 31))["trades"])[0]
        if not a.get("naeherung") or a["fehlende_sitzungen"] != 1 or not nah(a["return_pct"], 42):
            return f"(a) naeherung {a.get('naeherung')}, fehlend {a['fehlende_sitzungen']}, Rendite {a['return_pct']}"
        ja = W.get("l_naeherung_a") or [None, None, None]
        if ts(a) != f"{ja[0]}→{ja[1]}" or not nah(a["return_pct"], ja[2]):
            return f"(a) Python {ts(a)} {a['return_pct']} ≠ JS {ja}"
        df_b = df_aus("2024-11-01", "2024-12-31", lambda s, i: 100.0, ohne={"2024-11-26"})
        b = nov(pv.auswerten(df_b, "uhts", boerse="NYSE", stichtag=date(2024, 12, 31))["trades"])[0]
        return True if b.get("naeherung") else "(b) Lücke im 1x-Teil eines gehebelten Trades ohne Näherung"
    pruefe("py_l_naeherung", l_naeh)

    def l_1x():
        df = df_aus("2024-11-01", "2024-12-31", lambda s, i: 100.0, ohne={"2024-11-26"})
        tr = mit("2024-12-31", "NYSE", lambda: pv._luecken_markieren(df, pv.calc_one_day_holiday(df)))
        return True if not any(t.get("naeherung") for t in tr) else "1x-Trade über Lücke als Näherung markiert"
    pruefe("py_l_1x_exakt", l_1x)

    def e_ueb():
        df = zeilen([("2024-01-02", 100.0), ("2024-01-03", 110.0), ("2024-01-04", 121.0)])
        t1 = trade("2024-01-02", "2024-01-04", 100, 121, 21)
        t2 = trade("2024-01-02", "2024-01-04", 100, 121, 44, leverage=2,
                   hebel=[[pd.Timestamp("2024-01-03"), 2], [pd.Timestamp("2024-01-04"), 2]])
        e = pv.tages_equity(df, [t1, t2], 1000.0)
        t3 = trade("2024-01-02", "2024-01-03", 100, 110, 20, leverage=2, hebel=[[pd.Timestamp("2024-01-03"), 2]], stopped=True)
        f = pv.tages_equity(df, [t1, t3], 1000.0)
        ist = [e["final_equity"], f["final_equity"]]
        js = W.get("e_ueberlappung") or [None, None]
        if not (nah(ist[0], 1440, 1e-6) and nah(ist[1], 1320, 1e-6)):
            return f"Endwerte {ist}, soll [1440, 1320]"
        return True if (nah(ist[0], js[0]) and nah(ist[1], js[1])) else f"Python {ist} ≠ JS {js}"
    pruefe("py_e_ueberlappung", e_ueb)

    def e_tief():
        df = zeilen([("2024-01-02", 100.0), ("2024-01-03", 70.0), ("2024-01-04", 105.0), ("2024-01-05", 50.0)])
        t = trade("2024-01-02", "2024-01-04", 100, 105, 5)
        o = trade("2024-01-04", "2024-01-05", 105, 50, -52.38, open=True)
        e = pv.tages_equity(df, [t, o], 1000.0)
        st = pv.compute_strategy_stats([t, o])
        js = W.get("e_zwischentief") or [None, None]
        if st["max_drawdown"] != 0 or not nah(e["max_dd"], -30) or not nah(e["final_equity"], 1050):
            return f"Trade-DD {st['max_drawdown']}, täglich {e['max_dd']}, Endwert {e['final_equity']}"
        return True if (nah(e["max_dd"], js[0]) and nah(e["final_equity"], js[1])) else f"Python ≠ JS {js}"
    pruefe("py_e_zwischentief", e_tief)

    def e_ohne_pfad():
        df = zeilen([("2024-01-02", 100.0), ("2024-01-03", 110.0)])
        return True if pv.tages_equity(df, [trade("2024-01-02", "2024-01-03", 100, 110, 15, leverage=1.5)], 1000.0) is None \
            else "Tageskurve trotz Hebel ohne Pfad"
    pruefe("py_e_hebel_ohne_pfad", e_ohne_pfad)

    def e_ungueltig():
        for x in (0.0, float("nan")):
            df = zeilen([("2024-01-02", 100.0), ("2024-01-03", x), ("2024-01-04", 110.0), ("2024-01-05", 121.0)])
            t = trade("2024-01-02", "2024-01-05", 100, 121, 21)
            mit("2024-01-05", "NYSE", lambda: pv._luecken_markieren(df, [t]))
            if t["fehlende_sitzungen"] != 1:
                return f"Close {x}: fehlende Sitzungen {t['fehlende_sitzungen']}, soll 1"
            e = pv.tages_equity(df, [t], 1000.0)
            if not e or not nah(e["final_equity"], 1210) or not nah(e["final_equity"], W.get("e_ungueltiger_kurs")):
                return f"Close {x}: Endwert {e and e['final_equity']}, soll 1210 (JS {W.get('e_ungueltiger_kurs')})"
            t1 = trade("2024-01-02", "2024-01-04", 100, 110, 10)
            t2 = trade("2024-01-03", "2024-01-05", 100, 121, 0, leverage=2,
                       hebel=[[pd.Timestamp("2024-01-04"), 2], [pd.Timestamp("2024-01-05"), 2]])
            info = {}
            if pv.tages_equity(df, [t1, t2], 1000.0, info) is not None or info.get("grund") != "ungueltiger_kurs":
                return f"Close {x}: Exposure-Wechsel nicht ausgesetzt ({info})"
        return True
    pruefe("py_e_ungueltiger_kurs", e_ungueltig)

    def e_vertrag():
        import math as _m
        df = df_aus("2023-01-02", "2024-12-31", lambda s, i: 100 + _m.sin(i / 7) * 10)
        r = pv.auswerten(df, "sell_in_may", boerse="NYSE", stichtag=date(2024, 12, 31))
        alt = pv.compute_strategy_stats(r["trades"])
        if not r["stats"].get("taeglich"):
            return "taeglich fehlt"
        for k in ("max_drawdown", "final_equity", "total_return", "cagr"):
            if r["stats"][k] != alt[k]:
                return f"{k} hat die Bedeutung gewechselt"
        return True if r["stats"].get("luecken", {}).get("von") == len([t for t in r["trades"] if not t.get("open")]) \
            else "luecken-Zähler fehlt"
    pruefe("py_e_vertrag", e_vertrag)

    def s_close():
        # Codex-Fall: Einstieg 100; Folgetag Open 100, Low 90, Close 105; Fixed-Stop 8 % → Close-Modus: kein Stop
        df = df_aus("2024-11-01", "2024-12-31", lambda s, i: 100.0)
        df["Open"] = df["High"] = df["Low"] = df["Close"]
        df.loc[pd.Timestamp("2024-11-26"), ["Low", "Close"]] = [90.0, 105.0]
        r = pv.auswerten(df, "uhts", boerse="NYSE", stichtag=date(2024, 12, 31), stop_df=df, stop_pct=8.0)
        t = nov(r["trades"])[0]
        return True if not t.get("stopped") else f"Stop im Close-Modus ausgelöst ({t['return_pct']} %) — OHLC-Stop aktiv?"
    pruefe("py_s_close_modus", s_close)

    def anker():
        js = W.get("anker") or {}
        falsch = [y for y in range(2000, 2036) if sorted(d.isoformat() for d in pv._nyse_feiertage(y)) != js.get(str(y))]
        return True if not falsch else f"Anker Python ≠ JS in {falsch[:6]}"
    pruefe("py_anker", anker)

    def legacy():
        # V2: Ultimate Monthly und KTI nutzen die Legacy-Liste weiter → Trades gegen den Stand 1A unverändert
        import math as _m
        alt_src = subprocess.run(["git", "show", f"{STAND_1A}:{PYZ}"], capture_output=True, text=True, encoding="utf-8",
                                 cwd=REPO).stdout
        if not alt_src:
            return "Stand 1A nicht lesbar (git show)"
        with tempfile.TemporaryDirectory() as tmp:
            p = pathlib.Path(tmp) / "pv_alt.py"
            p.write_text(alt_src, encoding="utf-8")
            alt = lade_modul(p, "pv_alt_1a")
        df = df_aus("2016-01-04", "2024-12-31", lambda s, i: 100 * _m.exp(0.0004 * i + 0.05 * _m.sin(i / 11)))
        abw = []
        for key in ("ultimate_monthly", "kti_long_only", "kti_leveraged"):
            if key not in pv.STRATEGIES:
                continue
            a = mit("2024-12-31", "NYSE", lambda: pv.STRATEGIES[key]["func"](df))
            tok = alt.set_kontext(date(2024, 12, 31), "NYSE")
            try:
                b = alt.STRATEGIES[key]["func"](df)
            finally:
                alt._KONTEXT_VAR.reset(tok)
            fa = [(str(t["entry_date"].date()), str(t["exit_date"].date()), round(t["return_pct"], 9)) for t in a]
            fb = [(str(t["entry_date"].date()), str(t["exit_date"].date()), round(t["return_pct"], 9)) for t in b]
            if fa != fb:
                abw.append(f"{key}: {len(fa)} vs {len(fb)} Trades")
        return True if not abw else f"Legacy-Konsumenten geändert: {abw}"
    pruefe("py_legacy_unveraendert", legacy)
    return P


# ── 3. Kalender ──────────────────────────────────────────────────────────────
def kalender_pruefung(basis: pathlib.Path) -> dict:
    kz = lade_modul(REPO / "scripts" / "verify_kalender_zwilling.py", "kalender_zwilling")
    fe = kz.pruefe(basis / HOL)
    return {"kalender": True if not fe else f"{sum(map(len, fe.values()))} Fehler: {sorted(fe)}"}


# ── 4. Statisch ──────────────────────────────────────────────────────────────
def statisch(basis: pathlib.Path) -> dict:
    import re
    pv = (basis / PV).read_text(encoding="utf-8")
    st = (basis / ST).read_text(encoding="utf-8")
    py = (basis / PYZ).read_text(encoding="utf-8")
    P = {}
    P["seite_kpi"] = True if re.search(r"kpi\(_T\('pv\.kpi_max_dd_tag',[^\n]*?\),tg\?tg\.max_dd\.toFixed", pv) \
        else "Hauptwert Max DD nicht aus taeglich.max_dd"
    P["seite_chart"] = True if ("data.stats.taeglich.kurve" in pv and "buildEquityCurve" not in pv) \
        else "Chart nicht aus der Tageskurve"
    P["seite_karten"] = True if "var _tg=cachedResults[key].stats&&cachedResults[key].stats.taeglich;" in pv \
        else "Kachel-CAGR nicht aus taeglich"
    P["streamlit_vertrag"] = True if ("build_equity_curve" not in st and "_tg(sel_stats)" in st) \
        else "Streamlit liest nicht taeglich bzw. nutzt die Trade-Equity"
    m = re.search(r"def auswerten\(.*?\n(?=def )", py, re.S)
    P["py_auswerten_close_stop"] = True if (m and "apply_stop_close(" in m.group(0) and "apply_stop_loss(" not in m.group(0)) \
        else "auswerten ruft nicht den Close-Stop"
    return P


# ── 5. Snapshot ──────────────────────────────────────────────────────────────
def snapshot_pruefungen(snap: pathlib.Path, W: dict) -> dict:
    import pandas as pd
    P = {}
    sys.path.insert(0, str(REPO / "scripts" / "research"))
    import monthly10_blogzahlen as ref
    roh = json.loads((snap / "SPY.json").read_text(encoding="utf-8"))
    rows = [(r["date"], float(r["close"])) for r in roh if "1994-01-01" <= r["date"] <= "2025-12-31"]
    bl = ref.bloecke(rows)
    aktiv = set()
    for a, b, _ in bl:
        aktiv.update(range(a + 1, b + 1))
    ret = [0.0] + [rows[i][1] / rows[i - 1][1] - 1 for i in range(1, len(rows))]
    eq = [1.0]
    for i in range(1, len(rows)):
        eq.append(eq[-1] * (1 + (ret[i] if i in aktiv else 0.0)))
    _, cagr32, dd = ref.kennzahlen(eq, ref.JAHR_BIS - ref.JAHR_VON + 1)
    pv = lade_modul(REPO / PYZ, "pv_snap")
    df = pd.DataFrame({"Close": [c for _, c in rows]}, index=pd.DatetimeIndex([pd.Timestamp(d) for d, _ in rows]))
    df["year"], df["month"] = df.index.year, df.index.month
    r = pv.auswerten(df, "monthly_10", boerse="NYSE", stichtag=date(2025, 12, 31))
    tg = r["stats"]["taeglich"]
    js = W.get("m10") or {}
    spanne = (max(t["exit_date"] for t in r["trades"]) - min(t["entry_date"] for t in r["trades"])).days / 365.25
    fehler = []
    for wer, faktor, mdd, cg in (("Python", tg["final_equity"] / 1000, tg["max_dd"], tg["cagr"]),
                                 ("JS", js.get("faktor"), js.get("max_dd"), js.get("cagr"))):
        if not nah(faktor, eq[-1]):
            fehler.append(f"{wer} Endfaktor {faktor} ≠ Referenz {eq[-1]}")
        if not nah(mdd, dd * 100):
            fehler.append(f"{wer} Max-DD {mdd} ≠ Referenz {dd * 100}")
        if faktor and not nah((faktor ** (1 / 32) - 1) * 100, cagr32 * 100):
            fehler.append(f"{wer} CAGR (32 J.) ≠ Referenz")
        if faktor and not nah(cg, (eq[-1] ** (1 / spanne) - 1) * 100):
            fehler.append(f"{wer} CAGR (Handelsspanne) {cg} ≠ {(eq[-1] ** (1 / spanne) - 1) * 100}")
    if js.get("offen"):
        fehler.append(f"JS: {js['offen']} offene Trades auf vollständigen Jahren")
    P["snap_monthly10_referenz"] = True if not fehler else "; ".join(fehler)
    print(f"  Info: Monthly 10 SPY 1994–2025 Snapshot — aus 10.000: {10000 * eq[-1]:,.2f} (veröffentlicht 56.883), "
          f"Max-DD {dd * 100:.2f} % (veröffentlicht −41,0 %), CAGR 32 J. {cagr32 * 100:.2f} % (veröffentlicht 5,58 %)")

    from shared.exchange_holidays import is_trading_day
    dax = {r["date"] for r in json.loads((snap / "_GDAXI.json").read_text(encoding="utf-8"))}
    d, fehlt = date(2000, 1, 1), []
    while d <= date(2025, 12, 31):
        if is_trading_day(d, "XETRA") and d.isoformat() not in dax:
            fehlt.append(d.isoformat())
        d += timedelta(days=1)
    P["snap_gdaxi_luecken"] = True if not fehlt else f"{len(fehlt)} fehlende Sitzungen: {fehlt[:5]}"

    with tempfile.TemporaryDirectory() as tmp:
        ml = pathlib.Path(tmp) / "messlauf.json"
        r1 = subprocess.run(["node", str(REPO / "scripts/js/probe_plain_vanilla_messlauf.js"), str(snap), str(ml),
                             "10,max", "aus,fixed8,trailing8"], capture_output=True, text=True, encoding="utf-8")
        if r1.returncode != 0 or "ENDE" not in r1.stdout:
            P["snap_zwilling"] = "Messlauf abgebrochen: " + (r1.stderr or r1.stdout)[-300:]
            return P
        meta = json.loads(ml.read_text(encoding="utf-8"))
        gemeinsam = sorted(set(meta["ticker"]["SPY"]["je"]["max|aus"]) - PHASE3)
        r2 = subprocess.run([sys.executable, str(REPO / "scripts/research/plain_vanilla_zwilling.py"), str(snap), str(ml),
                             "--strategien", ",".join(gemeinsam)], capture_output=True, text=True, encoding="utf-8")
        abw = [z for z in r2.stdout.splitlines() if z.startswith("ABWEICH") and z.split()[1] in gemeinsam]
        P["snap_zwilling"] = True if (r2.returncode == 0 and not abw) else ("; ".join(abw) or r2.stderr[-300:])
    return P


def pruefe_alles(basis: pathlib.Path = REPO, snap: pathlib.Path | None = None) -> dict:
    erg = js_lauf(basis, (snap / "SPY.json") if snap else None)
    P = dict(erg["pruefungen"])
    P.update(py_pruefungen(basis, erg["werte"]))
    P.update(kalender_pruefung(basis))
    P.update(statisch(basis))
    if snap:
        P.update(snapshot_pruefungen(snap, erg["werte"]))
    return P


# (Name, Datei, alter Text, neuer Text, Prüfung, die reißen muss)
MUTATIONEN = [
    ("UHTS-Ausstieg S⁺4 (Stand 1A)", JS, "self._sitzung(rows, self._plusTage(F, 1), 2, 'nach')", "self._sitzung(rows, F, 3, 'nach')",
     "t_thanksgiving"),
    ("Hebel 1,5 pauschal", JS, "      var h = (aufstock != null && rows[i - 1].date >= aufstock) ? 2 : 1;", "      var h = 1.5;",
     "h_treppe"),
    ("2x ab Einstieg", JS, "rows[i - 1].date >= aufstock) ? 2 : 1;", "rows[i - 1].date >= t.entry_date) ? 2 : 1;", "h_treppe"),
    ("Stop ohne Pfadkürzung", JS, "    if (t.hebel) this._hebelPfad(rows, neu, t.aufstockung);\n    else neu.return_pct",
     "    neu.return_pct", "h_stop"),
    ("Stapelung statt Maximum", JS, "        if (!(exp[i] >= h)) exp[i] = h;", "        exp[i] = (exp[i] || 0) + h;", "e_ueberlappung"),
    ("offene Trades in der Tageskurve", JS,
     "    var zu = (trades || []).filter(function(t) { return !t.open && typeof t.return_pct === 'number' && isFinite(t.return_pct); });\n    if (!zu.length) return null;\n    var exp",
     "    var zu = (trades || []).filter(function(t) { return typeof t.return_pct === 'number' && isFinite(t.return_pct); });\n    if (!zu.length) return null;\n    var exp",
     "e_zwischentief"),
    ("Lückengrenze 5 statt 4 Tage", JS, "} else if (self._tageZwischen(a, z) > 4) {", "} else if (self._tageZwischen(a, z) > 5) {", "l_vor2000"),
    ("Kalenderzähler aus", JS, "while (d != null && d < z) { fs++;", "while (false) { fs++;", "l_2015"),
    ("Näherung nur bei 2x im Lückenintervall", JS, "      t.naeherung = self._gehebelt(t) && (fs + aa) > 0;",
     "      t.naeherung = (fs + aa) > 0 && !!t.hebel && t.hebel.some(function(x) { var j = self._exakt(rows, x[0]);"
     " return x[1] === 2 && j > 0 && self._kalenderSitzung(self._plusTage(rows[j - 1].date, 1), 1, b) < x[0]; });",
     "l_naeherung"),
    ("Hebel ohne Pfad als 1x", JS,
     "      if (!t.hebel && t.leverage != null && t.leverage !== 1) { info.grund = 'hebel_ohne_pfad'; return null; }\n", "",
     "e_hebel_ohne_pfad"),
    ("max_drawdown wechselt die Bedeutung", JS, "        stats.taeglich = this.tagesEquity(rows, trades, 1000, tgInfo);",
     "        stats.taeglich = this.tagesEquity(rows, trades, 1000, tgInfo);\n        if (stats.taeglich) stats.max_drawdown = stats.taeglich.max_dd;",
     "e_vertrag"),
    ("XETRA 24./31.12. erst ab 2011", HOL, "if (y >= 2001) { list.push(this._ds(y, 12, 24));", "if (y >= 2011) { list.push(this._ds(y, 12, 24));",
     "kalender"),
    ("XETRA-Sonderschließung fehlt", HOL, "'2017-10-03', '2017-10-31', '2018-05-21'", "'2017-10-03', '2018-05-21'", "kalender"),
    ("Seite: Trade-DD als Hauptwert", PV, "tg?tg.max_dd.toFixed(1)+'%':strich,'red')", "st.max_drawdown.toFixed(1)+'%','red')",
     "seite_kpi"),
    ("Seite: Chart aus Trade-Equity", PV, "var _kurve=data&&data.stats&&data.stats.taeglich&&data.stats.taeglich.kurve;",
     "var _kurve=data&&data.trades&&SA.strategy.buildEquityCurve(data.trades,1000);", "seite_chart"),
    ("Seite: Kachel-CAGR trade-basiert", PV, "var _tg=cachedResults[key].stats&&cachedResults[key].stats.taeglich;",
     "var _tg=cachedResults[key].stats;", "seite_karten"),
    ("Streamlit: Trade-Equity im Chart", ST, '        equity = (_tg(sel_stats) or {}).get("kurve") or []',
     "        equity = build_equity_curve(sel_trades, start_capital=1000.0)", "streamlit_vertrag"),
    ("Python: Wochenend-Feiertage als Anker", PYZ, "and d.weekday() < 5]", "]", "py_anker"),
    ("Python: UHTS-Ausstieg S⁺4", PYZ, '_sitzung(df, F + timedelta(days=1), 2, "nach")', '_sitzung(df, F, 3, "nach")',
     "py_t_thanksgiving"),
    ("Python: Hebel 1,5", PYZ, "        h = 2 if (aufstock is not None and idx[i - 1].date() >= aufstock) else 1", "        h = 1.5",
     "py_h_treppe"),
    ("Python: Stapelung", PYZ, "            exp[i] = max(exp.get(i, 0), h)", "            exp[i] = exp.get(i, 0) + h",
     "py_e_ueberlappung"),
    ("Python: offene Trades in der Tageskurve", PYZ,
     '    zu = [t for t in (trades or []) if not t.get("open") and np.isfinite(t["return_pct"])]\n    if not zu:\n        return None\n    idx = df.index',
     '    zu = [t for t in (trades or []) if np.isfinite(t["return_pct"])]\n    if not zu:\n        return None\n    idx = df.index',
     "py_e_zwischentief"),
    ("Python: Lückengrenze 5", PYZ, "                elif (z - a).days > 4:", "                elif (z - a).days > 5:", "py_l_vor2000"),
    ("Python: keine Näherung", PYZ, '        t["naeherung"] = _gehebelt(t) and (fs + aa) > 0', '        t["naeherung"] = False',
     "py_l_naeherung"),
    ("Python: OHLC-Stop in auswerten", PYZ, "            trades = apply_stop_close(df, trades, stop_pct, stop_type)",
     "            trades = apply_stop_loss(stop_df if stop_df is not None else df, trades, stop_pct, stop_type)",
     "py_s_close_modus"),
    ("Python: Hebel ohne Pfad als 1x", PYZ,
     '        if not t.get("hebel") and t.get("leverage") is not None and t.get("leverage") != 1:\n            info["grund"] = "hebel_ohne_pfad"\n            return None',
     "        if False:\n            return None", "py_e_hebel_ohne_pfad"),
    ("ungültiger Kurs als Rendite null", JS, "      if (!this._gueltigerKurs(rows[j].close)) continue;\n      var h = exp[vor + 1] || 0;",
     "      if (!this._gueltigerKurs(rows[j].close)) { vor = j; continue; }\n      var h = exp[vor + 1] || 0;", "e_ungueltiger_kurs"),
    ("ungültiger Kurs: Exposure-Wechsel nicht ausgesetzt", JS,
     "        if ((exp[k] || 0) !== h) { info.grund = 'ungueltiger_kurs'; return null; }", "", "e_ungueltiger_kurs"),
    ("ungültiger Kurs ohne Lückenmarke", JS, "        if (!self._gueltigerKurs(rows[i].close)) continue;\n        var a = rows[vor].date",
     "        var a = rows[vor].date", "e_ungueltiger_kurs"),
    ("Python: ungültiger Kurs als Rendite null", PYZ, "        if not _gueltiger_kurs(closes[j]):\n            continue\n        h = exp.get(vor + 1, 0)",
     "        if not _gueltiger_kurs(closes[j]):\n            vor = j\n            continue\n        h = exp.get(vor + 1, 0)",
     "py_e_ungueltiger_kurs"),
    ("Python: ungültiger Kurs ohne Lückenmarke", PYZ, "                if not _gueltiger_kurs(closes[i]):\n                    continue\n                a, z = idx[vor].date()",
     "                a, z = idx[vor].date()", "py_e_ungueltiger_kurs"),
    ("Python: Legacy-Anker verändert", PYZ, "    (11, 25), # Thanksgiving (ca.)", "    (11, 28), # Thanksgiving (ca.)",
     "py_legacy_unveraendert"),
]

UNGUELTIG_ERWARTET = [
    ("Syntaxfehler (Probe muss abbrechen)", JS, "  _hebelPfad: function(rows, t, aufstock) {", "  _hebelPfad: function(rows, t, aufstock) {{", "h_treppe"),
    ("Anker trifft nicht", JS, "DIESER TEXT STEHT NICHT IN DER DATEI", "x", "h_treppe"),
    ("trifft das Gerüst, nicht das Verhalten", JS, "  tagesEquity: function(rows, trades, start) {",
     "  tagesEquity_weg: function(rows, trades, start) {", "e_zwischentief"),
]


def _kopie(tmp: pathlib.Path):
    for rel in ("landing/js", "landing/pages"):
        shutil.copytree(REPO / rel, tmp / rel)
    (tmp / "pages").mkdir()
    shutil.copy(REPO / ST, tmp / ST)
    (tmp / "shared/strategies").mkdir(parents=True)
    shutil.copy(REPO / PYZ, tmp / PYZ)


def _bewerte(name, datei, alt, neu, soll):
    quelle = (REPO / datei).read_text(encoding="utf-8")
    if quelle.count(alt) != 1:
        return "ungueltig", "Anker trifft nicht"
    with tempfile.TemporaryDirectory() as t:
        tmp = pathlib.Path(t)
        _kopie(tmp)
        (tmp / datei).write_text(quelle.replace(alt, neu), encoding="utf-8")
        try:
            P = pruefe_alles(tmp)
        except RuntimeError as e:
            return "ungueltig", f"Probe abgebrochen: {e}"
    gerissen = sorted(k for k, v in P.items() if v is not True)
    if any(k.startswith("[Aufbau]") for k in gerissen):
        return "ungueltig", f"Aufbau gerissen: {gerissen}"
    if soll not in gerissen:
        return "verfehlt", f"erwartet {soll}, gerissen {gerissen}"
    andere = [k for k in gerissen if k != soll]
    return "gefangen", (f"auch: {andere}" if andere else "")


def mutationen() -> int:
    grund = pruefe_alles()
    rot = [k for k, v in grund.items() if v is not True]
    if rot:
        print("Grundzustand nicht grün — Mutationen sinnlos:", rot)
        return 1
    ok = 0
    for m in MUTATIONEN:
        urteil, info = _bewerte(*m)
        ok += urteil == "gefangen"
        print(f"  {urteil.upper():9s} {m[0]} → {m[4]} {info}")
    falsch = 0
    for m in UNGUELTIG_ERWARTET:
        urteil, info = _bewerte(*m)
        richtig = urteil == "ungueltig"
        falsch += not richtig
        print(f"  {'OK' if richtig else 'FALSCH'}: als ungültig erkannt? {m[0]} → {urteil} {info}")
    print(f"{ok}/{len(MUTATIONEN)} Mutationen gefangen, {len(UNGUELTIG_ERWARTET) - falsch}/{len(UNGUELTIG_ERWARTET)} "
          f"untaugliche richtig verworfen")
    return 0 if ok == len(MUTATIONEN) and not falsch else 1


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if "--mutationen" in sys.argv:
        return mutationen()
    snap = None
    if "--snapshot" in sys.argv:
        snap = pathlib.Path(sys.argv[sys.argv.index("--snapshot") + 1])
    elif "--ohne-snapshot" not in sys.argv:
        print("UNGEPRÜFT: ohne --snapshot <ordner> fehlen Referenz- und Zwillingsprüfungen (bewusst: --ohne-snapshot)")
        return 1
    P = pruefe_alles(REPO, snap)
    rot = {k: v for k, v in P.items() if v is not True}
    for k, v in rot.items():
        print(f"FEHLER {k}: {v}")
    print(f"verify_plain_vanilla_1b: {len(P) - len(rot)}/{len(P)} Prüfungen bestanden"
          + ("" if snap else " (ohne Snapshot)"))
    return 0 if not rot else 1


if __name__ == "__main__":
    sys.exit(main())
