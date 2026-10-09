#!/usr/bin/env python3
"""
verify_plain_vanilla_1a.py — Wächter Phase 1A der Seite /plain-vanilla (Plan v5, Codex-Freigabe Runde 5).

    py -3.14 scripts/verify_plain_vanilla_1a.py              # alle Prüfungen
    py -3.14 scripts/verify_plain_vanilla_1a.py --mutationen

Drei Teile:
  1. JS: `scripts/js/probe_plain_vanilla_1a.js` führt die echten Module aus (Fälle aus Codex-Runde 1 und E1–E9).
  2. Seiten statisch: Kennzahlen und Signalansicht nutzen `SA.strategy.auswerten`, die Streak kommt aus derselben
     Auswertung, das Dashboard nimmt Termine aus `SA.strategy.regeltermine` und kennt kein `3*5`, PF über `formatPF`.
  3. Python-Zwilling `shared/strategies/plain_vanilla.py`: dieselben Eingaben (Sep-Vermeidung offen, LBR mit
     identischem Histogrammvektor, Santa 2024, NaN-Ausstieg, PF None, offene Trades nicht in Statistik/Equity).
Der Kalendervertrag 2000–2035 hat einen eigenen Wächter: scripts/verify_kalender_zwilling.py.

--mutationen: jede Mutation ändert eine Kopie und benennt die Prüfung, die reißen MUSS. Reißt eine andere, eine
[Aufbau]-Prüfung, oder bricht die Probe ab (kein Endmarker), ist die Mutation UNGÜLTIG, nicht gefangen.
`UNGUELTIG_ERWARTET` enthält bewusst untaugliche Mutationen; der Test muss sie als ungültig erkennen.
"""
from __future__ import annotations

import json
import math
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import date, timedelta

REPO = pathlib.Path(__file__).resolve().parent.parent
PROBE = REPO / "scripts" / "js" / "probe_plain_vanilla_1a.js"
JS = "landing/js/strategy-compute.js"
IND = "landing/js/indicators.js"
SEAS = "landing/js/seasonal-compute.js"
PV = "landing/pages/plain-vanilla.html"
DASH = "landing/pages/dashboard.html"
PYZ = "shared/strategies/plain_vanilla.py"


# ── 1. JS-Probe ──────────────────────────────────────────────────────────────
def js_pruefungen(basis: pathlib.Path) -> dict:
    r = subprocess.run(["node", str(PROBE), str(basis)], capture_output=True, text=True, encoding="utf-8")
    zeilen = r.stdout.strip().splitlines()
    if r.returncode != 0 or len(zeilen) < 2 or zeilen[-1] != "ENDE":
        raise RuntimeError("Probe ohne Endmarker: " + (r.stderr or r.stdout)[-300:])
    return json.loads(zeilen[0])["pruefungen"]


# ── 2. Seiten statisch ───────────────────────────────────────────────────────
def seiten_pruefungen(basis: pathlib.Path) -> dict:
    pv = (basis / PV).read_text(encoding="utf-8")
    da = (basis / DASH).read_text(encoding="utf-8")
    P = {}
    streak = re.search(r"function getStreak\(key\)\s*\{(.*?)\n      \}", pv, re.S)
    P["seite_streak"] = True if (streak and "calcStrategy(key)" in streak.group(1) and "tradeCache" not in pv) \
        else "getStreak nutzt nicht calcStrategy(key) bzw. tradeCache vorhanden"
    calc = re.search(r"function calcStrategy\(key\)\{(.*?)\n    \}", pv, re.S)
    P["seite_auswerten"] = True if (calc and "SA.strategy.auswerten(" in calc.group(1)
                                    and "SA.strategy[s.func](" not in calc.group(1)) else "calcStrategy rechnet nicht über auswerten"
    P["seite_pf"] = True if ("SA.strategy.formatPF(st.profit_factor)" in pv and ">=999" not in pv) else "PF-Anzeige nicht über formatPF"
    P["dash_regeltermine"] = True if ("SA.strategy.regeltermine(" in da and "3*5" not in da) else "Dashboard: regeltermine fehlt oder 3*5"
    alle = {f.name: f.read_text(encoding="utf-8") for f in sorted((basis / "landing/pages").glob("*.html"))}
    roh = [n for n, t in alle.items() if re.search(r"profit_factor\s*>=\s*999|\bstats?\.sharpe\.toFixed|\bst\.sharpe\.toFixed", t)]
    P["seiten_formatierung"] = True if not roh else f"PF/Sharpe ohne formatPF/formatZahl: {roh}"
    handler = re.findall(r"addEventListener\('(?:change|input)',function\(\)\{(.*?)\n    \}\);", pv, re.S)
    stop_h = [h for h in handler if "renderSelected()" in h]
    P["seite_stop_signale"] = True if (len(stop_h) == 3 and all("renderSignals(rawRows)" in h for h in stop_h)) \
        else f"Stop-Handler ohne renderSignals: {len(stop_h)} gefunden"
    sig = re.search(r"function renderSignals\(rows\) \{(.*?)var signals = \[\];", pv, re.S)
    # die BEDINGUNG prüfen, nicht nur das Wort: der Zweig muss auf genau diese Variable reagieren und zurückkehren
    veraltet_ok = bool(sig and re.search(r"var _veraltet = SA\.strategy\._datenVeraltet\(rows\);", sig.group(1))
                       and re.search(r"if \(_veraltet\) \{\n(?:(?!\n      \}).)*?el\.innerHTML(?:(?!\n      \}).)*?return;\s*\n      \}",
                                     sig.group(1), re.S))
    P["seite_veraltet"] = True if veraltet_ok else "renderSignals unterdrückt Signale bei veraltetem Bestand nicht"
    # Streamlit-Seite (pages/09) seit 2026-10-09 entfernt — ihre zwei Prüfungen entfallen mit ihr.
    P["dash_streak"] = True if ("SA.strategy.auswerten(rawRows" in da and "calcStrategyStreak" not in da) else "Dashboard-Streak nicht aus auswerten"
    return P


# ── 3. Python-Zwilling ───────────────────────────────────────────────────────
def py_pruefungen(basis: pathlib.Path) -> dict:
    import importlib.util
    import pandas as pd
    sys.path.insert(0, str(REPO))
    from shared.exchange_holidays import is_trading_day
    spec = importlib.util.spec_from_file_location("pv_zwilling", basis / PYZ)
    pv = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pv)

    def df_aus(von, bis, fn, boerse="NYSE"):
        d, z = date.fromisoformat(von), []
        while d <= date.fromisoformat(bis):
            if is_trading_day(d, boerse):
                z.append((pd.Timestamp(d), fn(d, len(z))))
            d += timedelta(days=1)
        return pd.DataFrame({"Close": [c for _, c in z]}, index=pd.DatetimeIndex([t for t, _ in z]))

    P = {}

    def pruefe(name, fn):
        try:
            r = fn()
            P[name] = True if r is True else str(r)
        except Exception as e:  # noqa: BLE001
            P[name] = f"Ausnahme: {e}"
        finally:
            pv.set_kontext()

    def sep():
        df = df_aus("2025-09-30", "2025-10-08", lambda d, i: 100 + 10 * i)
        pv.set_kontext(date(2025, 10, 8), "NYSE")
        tr = pv.calc_september_avoid(df)
        if len(tr) != 1 or not tr[0].get("open"):
            return f"erwartet 1 offenen Trade, ist {tr}"
        return True if pv.compute_strategy_stats(tr) == {} else "offener Trade in der Statistik"
    pruefe("py_sep_offen", sep)

    def lbr():
        df = df_aus("2024-09-03", "2025-07-01", lambda d, i: 100.0)
        idx = list(df.index)
        i_okt, i_apr = idx.index(pd.Timestamp("2024-10-01")), idx.index(pd.Timestamp("2025-04-01"))
        hist = pd.Series([1.0 if i_okt <= i < i_apr else (-1.0 if i >= i_apr else 0.0) for i in range(len(idx))], index=df.index)
        import shared.indicators as ind
        orig = ind.calc_lbr
        ind.calc_lbr = lambda close, *a, **k: {"histogram": hist}
        try:
            pv.set_kontext(date(2025, 7, 1), "NYSE")
            tr = pv.calc_lbr_november_mai(df)
        finally:
            ind.calc_lbr = orig
        if len(tr) != 1:
            return f"erwartet 1 Trade, ist {len(tr)}"
        if tr[0]["entry_date"] != idx[i_okt + 1] or tr[0]["exit_date"] != idx[i_apr + 1]:
            return f"Ein/Aus {tr[0]['entry_date'].date()}/{tr[0]['exit_date'].date()}, soll {idx[i_okt+1].date()}/{idx[i_apr+1].date()}"
        return True
    pruefe("py_lbr_vortag", lbr)

    def santa():
        df = df_aus("2024-11-01", "2025-01-10", lambda d, i: 100.0 if d < date(2024, 11, 25) else 110.0)
        pv.set_kontext(date(2025, 1, 10), "NYSE")
        tr = [t for t in pv.calc_santa_claus(df) if t["entry_date"].year == 2024]
        if not tr or tr[0]["entry_date"] != pd.Timestamp("2024-11-25"):
            return f"Einstieg {tr[0]['entry_date'].date() if tr else None}, soll 2024-11-25"
        return True
    pruefe("py_santa_2024", santa)

    def nan():
        df = df_aus("2024-10-01", "2025-05-09", lambda d, i: 100.0)
        mai = [t for t in df.index if t.month == 5 and t.year == 2025]
        df.loc[mai[2], "Close"] = float("nan")
        pv.set_kontext(date(2025, 5, 9), "NYSE")
        tr = pv.calc_sell_in_may(df)
        return True if tr == [] else f"Trade trotz NaN-Ausstieg: {tr}"
    pruefe("py_nan_exit", nan)

    def pf():
        tr = [{"entry_date": pd.Timestamp("2020-01-02"), "exit_date": pd.Timestamp("2020-02-03"), "return_pct": 1.0},
              {"entry_date": pd.Timestamp("2021-01-04"), "exit_date": pd.Timestamp("2021-02-01"), "return_pct": 2.0}]
        st = pv.compute_strategy_stats(tr)
        return True if st["profit_factor"] is None else f"PF {st['profit_factor']}"
    pruefe("py_pf_none", pf)

    def sharpe():
        tr = [{"entry_date": pd.Timestamp(f"{2010+i}-01-04"), "exit_date": pd.Timestamp(f"{2010+i}-06-01"), "return_pct": r}
              for i, r in enumerate([11.847357614314383, 11.845068971653427])]
        st = pv.compute_strategy_stats(tr)
        return True if st["sharpe"] is None else f"Sharpe aus 2 Trades: {st['sharpe']}"
    pruefe("py_sharpe_min", sharpe)

    def offen_equity():
        tr = [{"entry_date": pd.Timestamp("2020-01-02"), "exit_date": pd.Timestamp("2020-02-03"), "return_pct": 10.0},
              {"entry_date": pd.Timestamp("2020-03-02"), "exit_date": pd.Timestamp("2020-03-05"), "return_pct": -50.0, "open": True}]
        kurve = pv.build_equity_curve(tr)
        st = pv.compute_strategy_stats(tr)
        if st["n_trades"] != 1:
            return f"n_trades {st['n_trades']}"
        return True if math.isclose(kurve[-1][1], 1100.0) else f"Equity-Ende {kurve[-1][1]}"
    pruefe("py_offen_nicht_in_stats", offen_equity)

    def df_rand():
        df = df_aus("2026-01-02", "2026-10-07", lambda d, i: 100 + 0.1 * i)
        df["year"], df["month"] = df.index.year, df.index.month
        return df

    def santa_rand():
        pv.set_kontext(date(2026, 10, 7), "NYSE")
        tr = pv.calc_santa_claus(df_rand())
        return True if not tr else f"Santa-Einstieg am Datenrand: {[t['entry_date'].date() for t in tr]}"
    pruefe("py_santa_rand", santa_rand)

    def alle_laufen():
        pv.set_kontext(date(2026, 10, 7), "NYSE")
        kaputt = []
        for k, v in pv.STRATEGIES.items():
            try:
                v["func"](df_rand())
            except Exception as e:  # noqa: BLE001
                kaputt.append(f"{k}: {type(e).__name__}")
        return True if not kaputt else f"Strategien brechen ab: {kaputt}"
    pruefe("py_strategien_laufen", alle_laufen)

    def e8():
        df = df_aus("2025-09-30", "2025-10-08", lambda d, i: 100 + 10 * i)
        pv.set_kontext(date(2025, 10, 8), "NYSE")
        t = pv.calc_september_avoid(df)[0]
        soll = {"zustand_einstieg": "gefunden", "zustand_ausstieg": "noch_nicht_faellig",
                "regeltermin_ausstieg": date(2026, 8, 31), "letzte_kurszeile": date(2025, 10, 8)}
        falsch = {k: t.get(k) for k, v in soll.items() if t.get(k) != v}
        return True if not falsch else f"E8-Felder: {falsch}"
    pruefe("py_e8_felder", e8)

    def month_end_unv():
        df = df_aus("2026-09-01", "2026-10-29", lambda d, i: 110.0 if d == date(2026, 10, 29) else 100.0)
        pv.set_kontext(date(2026, 10, 29), "NYSE")
        tr = [t for t in pv.calc_month_end(df) if t["entry_date"] >= pd.Timestamp("2026-10-01")]
        if len(tr) != 1 or tr[0]["entry_date"] != pd.Timestamp("2026-10-29") or not tr[0].get("open"):
            return f"Oktober-Einstieg {[ (t['entry_date'].date(), t.get('open')) for t in tr]}, soll 2026-10-29 offen"
        return True
    pruefe("py_month_end_unvollstaendig", month_end_unv)

    def m10_rand():
        df = df_aus("2026-10-01", "2026-10-21", lambda d, i: 100.0 + i)
        df["year"], df["month"] = df.index.year, df.index.month
        pv.set_kontext(date(2026, 10, 21), "NYSE")
        zu = [f"{t['entry_date'].date()}>{t['exit_date'].date()}" for t in pv.calc_monthly_10(df) if not t.get("open")]
        soll = ["2026-10-01>2026-10-06", "2026-10-13>2026-10-16"]
        return True if zu == soll else f"geschlossene Blöcke {zu}, soll {soll}"
    pruefe("py_monthly10_rand", m10_rand)

    # Codex Code-R3: XETRA-Ticker über den Rechenweg der Seite (auswerten) — 29.12.=117, 30.12.=118, geschlossen +0,8547 %
    def xetra_kontext():
        kurs = {date(2025, 12, 29): 117.0, date(2025, 12, 30): 118.0}
        df = df_aus("2025-12-01", "2025-12-30", lambda d, i: kurs.get(d, 100.0), boerse="XETRA")
        df["year"], df["month"] = df.index.year, df.index.month
        vor = {"stichtag": date(2020, 1, 1), "boerse": "NYSE"}
        pv.set_kontext(**vor)   # fremder Vorkontext: muss danach unverändert zurück sein
        r = pv.auswerten(df, "post_christmas", boerse="XETRA", stichtag=date(2025, 12, 31))
        if pv._kontext() != vor:
            return f"Kontext nicht zurückgesetzt: {pv._kontext()}"
        tr = [t for t in r["trades"] if t["entry_date"].year == 2025]
        if len(tr) != 1 or tr[0].get("open") or tr[0]["exit_date"] != pd.Timestamp("2025-12-30"):
            return f"Trade {[(t['exit_date'].date(), t.get('open')) for t in tr]}, soll geschlossen am 30.12."
        if abs(tr[0]["return_pct"] - (118 / 117 - 1) * 100) > 1e-9:
            return f"Rendite {tr[0]['return_pct']:.6f}, soll {(118 / 117 - 1) * 100:.6f}"
        if not r["stats"]:
            return "Statistik leer — abgeschlossener Trade fehlt in den Kennzahlen"
        try:
            pv.auswerten(df, "gibt_es_nicht", boerse="XETRA", stichtag=date(2025, 12, 31))
        except KeyError:
            pass
        if pv._kontext() != vor:
            return f"Kontext nach Ausnahme nicht zurückgesetzt: {pv._kontext()}"
        return True
    pruefe("py_xetra_kontext", xetra_kontext)

    # Codex Code-R4 Befund 1: zwei überlappende Auswertungen (XETRA / NYSE) in eigenen Threads — beide setzen ihren
    # Kontext, warten aufeinander und rechnen erst dann. Mit einem gemeinsamen Kontext rechnet eine mit der falschen Börse.
    def parallel():
        import threading
        kurs = {date(2025, 12, 29): 117.0, date(2025, 12, 30): 118.0}
        df = df_aus("2025-12-01", "2025-12-30", lambda d, i: kurs.get(d, 100.0), boerse="XETRA")
        df["year"], df["month"] = df.index.year, df.index.month
        sperre = threading.Barrier(2, timeout=20)
        orig = pv.STRATEGIES["post_christmas"]["func"]

        def wartend(d):
            # zwei Barrieren: beide rechnen, während BEIDE Kontexte gesetzt sind — ohne die zweite könnte ein Thread
            # fertig werden und den Wert des anderen zurückschreiben, und die Mutation fiele zufällig durch
            sperre.wait()
            r = orig(d)
            sperre.wait()
            return r
        pv.STRATEGIES["__parallel"] = {**pv.STRATEGIES["post_christmas"], "func": wartend}
        erg = {}

        def lauf(b):
            try:
                tr = pv.auswerten(df, "__parallel", boerse=b, stichtag=date(2025, 12, 31))["trades"]
                erg[b] = [(t["exit_date"].date(), bool(t.get("open"))) for t in tr if t["entry_date"].year == 2025]
            except Exception as e:  # noqa: BLE001
                erg[b] = f"Ausnahme {e}"
        vor = pv._kontext()
        try:
            th = [threading.Thread(target=lauf, args=(b,)) for b in ("XETRA", "NYSE")]
            [t.start() for t in th]
            [t.join(30) for t in th]
        finally:
            pv.STRATEGIES.pop("__parallel", None)
        soll = {"XETRA": [(date(2025, 12, 30), False)], "NYSE": [(date(2025, 12, 30), True)]}
        if erg != soll:
            return f"überlappend {erg}, soll {soll}"
        return True if pv._kontext() == vor else f"Hauptkontext verändert: {pv._kontext()}"
    pruefe("py_kontext_parallel", parallel)

    # Codex Code-R4 Befund 2: veralteter Bestand — offene Kandidaten heraus, durch Stop geschlossene bleiben.
    # NYSE-Kurse bis 31.12.2025; ab dort 10 Sitzungen = 15.01.2026, 11 Sitzungen = 16.01.2026 (MLK 19.01. erst danach).
    def veraltet():
        df = df_aus("2025-09-01", "2025-12-31", lambda d, i: 100.0)
        df["year"], df["month"] = df.index.year, df.index.month
        r10 = pv.auswerten(df, "september_avoid", boerse="NYSE", stichtag=date(2026, 1, 15))
        if r10["veraltet"] or not any(t.get("open") for t in r10["trades"]):
            return f"10 Sitzungen: veraltet={r10['veraltet']}, offener Trade fehlt"
        r11 = pv.auswerten(df, "september_avoid", boerse="NYSE", stichtag=date(2026, 1, 16))
        if not r11["veraltet"] or any(t.get("open") for t in r11["trades"]) or len(r11["unvollstaendig"]) != 1:
            return f"11 Sitzungen: veraltet={r11['veraltet']}, offen={[t['entry_date'].date() for t in r11['trades'] if t.get('open')]}"
        rc = pv.auswerten(df, "september_avoid", boerse="NYSE", stichtag=date(2026, 10, 8))
        if any(t.get("open") for t in rc["trades"]):
            return "Codex-Fall 08.10.2026: offener Trade trotz veraltetem Bestand"
        # Stop schließt vor dem Filter: fallender Kurs ab Oktober → Stop-Trade bleibt realisiert
        df2 = df_aus("2025-09-01", "2025-12-31", lambda d, i: 100.0 if d < date(2025, 10, 15) else 80.0)
        df2["year"], df2["month"] = df2.index.year, df2.index.month
        df2["Open"] = df2["High"] = df2["Low"] = df2["Close"]   # Python-Stop arbeitet auf OHLC (E4)
        rs = pv.auswerten(df2, "september_avoid", boerse="NYSE", stichtag=date(2026, 10, 8), stop_df=df2, stop_pct=8.0)
        zu = [t for t in rs["trades"] if t["entry_date"].year == 2025 and not t.get("open")]
        return True if zu else f"Stop-Trade vom Filter entfernt: {rs['trades']}"
    pruefe("py_veraltet", veraltet)
    return P


def pruefe_alles(basis: pathlib.Path = REPO) -> dict:
    P = {}
    P.update(js_pruefungen(basis))
    P.update(seiten_pruefungen(basis))
    P.update(py_pruefungen(basis))
    return P


# (Name, Datei, alter Text, neuer Text, Prüfung, die reißen muss)
MUTATIONEN = [
    ("LBR mit Wert des Ausführungstags", JS, "if (gueltig(hist[i - 1]) && hist[i - 1] > 0) { entry = i; break; }",
     "if (gueltig(hist[i]) && hist[i] > 0) { entry = i; break; }", "lbr_vortag"),
    ("stiller Rückfall auf Sell in May", JS,
     "if (!SA.indicators || !SA.indicators.calcMACD) throw new Error('LBR: SA.indicators.calcMACD fehlt (indicators.js nicht geladen)');",
     "if (!SA.indicators || !SA.indicators.calcMACD) return this.calc_sell_in_may(rows);", "n1_kein_rueckfall"),
    ("Santa vier Sitzungen vorher", JS, "var entry = this._sitzung(rows, thxDate, -3, 'nach');",
     "var entry = this._sitzung(rows, thxDate, -4, 'nach');", "santa_2024"),
    ("NaN-Preis akzeptiert", JS, "if (!(typeof pe === 'number' && isFinite(pe) && pe > 0 && typeof px === 'number' && isFinite(px) && px > 0)) {",
     "if (!(pe > 0)) {", "nan_exit"),
    ("PF 999 statt null", JS, "Math.round(grossProfit / grossLoss * 100) / 100 : null", "Math.round(grossProfit / grossLoss * 100) / 100 : 999",
     "pf_null"),
    ("Rendite gerundet gespeichert", JS, "      return_pct: (px - pe) / pe * 100\n    };",
     "      return_pct: Math.round((px - pe) / pe * 10000) / 100\n    };", "ungerundet"),
    ("SMA ohne Gültigkeitsprüfung", IND, "for (var i = 1; i < n; i++) if (ok(closes[i - 1], sma[i - 1])) mask[i] = cond === 'Close > SMA'",
     "for (var i = 1; i < n; i++) mask[i] = cond === 'Close > SMA'", "sma_warmup"),
    ("Stop zum Stopniveau", JS, "    neu.exit_date = rows[i].date;\n    neu.exit_price = c;",
     "    c = t.entry_price * 0.92;\n    neu.exit_date = rows[i].date;\n    neu.exit_price = c;", "stop_gap"),
    ("Stop ohne regulären Ausstiegstag", JS,
     "      var stopPrice = t.entry_price * (1 - stopPct / 100);\n      for (var i = entryIdx + 1; i <= exitIdx; i++) {",
     "      var stopPrice = t.entry_price * (1 - stopPct / 100);\n      for (var i = entryIdx + 1; i < exitIdx; i++) {", "stop_am_exit"),
    ("gestoppter offener Trade bleibt offen", JS, "    delete neu.open; delete neu.regeltermin_ausstieg;", "", "stop_offen"),
    ("Hebel geht beim Stop verloren", JS, "    else neu.return_pct = (c / t.entry_price - 1) * 100 * (t.leverage || 1);",
     "    else { neu.return_pct = (c / t.entry_price - 1) * 100; delete neu.leverage; }", "stop_hebel"),
    ("Trailing-Peak nur Einstieg", JS, "        if (c > peak) peak = c;\n        if (c <= peak * (1 - stopPct / 100)) return self._stopAusstieg(t, rows, i);",
     "        if (c <= peak * (1 - stopPct / 100)) return self._stopAusstieg(t, rows, i);", "trailing_close"),
    ("veraltet ab 9 Sitzungen", JS, "    while (n <= 10) {", "    while (n <= 9) {", "datenende_veraltet"),
    ("Einstieg auf letzter Zeile verworfen", JS, "    if (exitIdx < entryIdx || (exitIdx === entryIdx && !open)) return null;",
     "    if (exitIdx <= entryIdx) return null;", "einstieg_letzte_zeile"),
    ("Streak zählt offene Trades", JS, "  streak: function(trades) {\n    var zu = (trades || []).filter(function(t) { return !t.open && typeof t.return_pct",
     "  streak: function(trades) {\n    var zu = (trades || []).filter(function(t) { return typeof t.return_pct", "streak_konfig"),
    ("Median per Floor-Index", SEAS, "    return sorted[lo] + (sorted[hi] - sorted[lo]) * (h - lo);", "    return sorted[Math.floor(n * p)];", "median"),
    ("Regeltermin 3*5", JS, "      add('sell_in_may', 'exit', nth(y, 5, 3));", "      add('sell_in_may', 'exit', nth(y, 5, 3*5));", "regeltermine"),
    ("Datenrand: letzte Zeile als Termin", JS,
     "      if (t != null && t > c.letzte) return this._terminZustand(rows, t);", "", "sep_offen"),
    ("Monatsrand aus Zeilen", JS, "    return ym >= c.letzte.slice(0, 7) && this._imKalender(ym + '-01');", "    return false;", "month_end_rand"),
    ("Seite: Streak aus eigenem Cache", PV, "        var r = calcStrategy(key);", "        var tradeCache = {}; var r = calcStrategy(key);",
     "seite_streak"),
    ("Seite: PF ∞ zurück", PV, "SA.strategy.formatPF(st.profit_factor)", "(st.profit_factor>=999?'inf':st.profit_factor.toFixed(2))", "seite_pf"),
    ("Dashboard: 3*5 inline", DASH, "      SA.strategy.regeltermine(todayS, exD).forEach(function(r){ add(r.key, r.type, r.date); });",
     "      SA.strategy.regeltermine(todayS, exD).forEach(function(r){ add(r.key, r.type, r.date); }); add('sell_in_may','exit',null && 3*5);",
     "dash_regeltermine"),
    ("Sharpe ohne Mindestzahl", JS, "    var sharpe = (n >= this.MIN_TRADES_SHARPE && stdRet > 0) ?",
     "    var sharpe = (stdRet > 0) ?", "sharpe_min"),
    ("Opex: PF-Anzeige roh", "landing/pages/opex.html", "SA.strategy.formatPF(stats.profit_factor)",
     "(stats.profit_factor >= 999 ? 'inf' : stats.profit_factor.toFixed(2))", "seiten_formatierung"),
    ("Vixpiration: Sharpe roh", "landing/pages/vixpiration.html", "SA.strategy.formatZahl(stats.sharpe, 2)",
     "stats.sharpe.toFixed(2)", "seiten_formatierung"),
    ("Python: Sharpe ohne Mindestzahl", PYZ, "if (n >= MIN_TRADES_SHARPE and std_ret > 0) else None", "if std_ret > 0 else None",
     "py_sharpe_min"),
    ("Sonderschließung als Feiertag", JS, "    return SA.holidays.get(y, 'NYSE').filter(function(d) { return sonder.indexOf(d) < 0; });",
     "    return SA.holidays.get(y, 'NYSE');", "sonder_kein_feiertag"),
    ("Rand: Kalender auch für vergangene Termine", JS, "    if (d <= c.letzte) return zeilenbasiert();", "", "rand_historisch"),
    ("Stop mit ungültigem Kurs", JS,
     "        if (!(typeof c === 'number' && isFinite(c) && c > 0)) { self._notiere('stop_kurs_ungueltig', rows[i].date); continue; }\n        if (c <= stopPrice)",
     "        if (c <= stopPrice)", "stop_ungueltig"),
    ("E8: Regeltermin fehlt am Trade", JS, "    if (open) { trade.open = true; trade.regeltermin_ausstieg = regeltermin; }",
     "    if (open) { trade.open = true; }", "e8_felder"),
    ("Seite: Stop ohne Signal-Neuzeichnen", PV, "cachedResults={};renderSelected();if(rawRows)renderSignals(rawRows);\n    });\n    document.getElementById('sel-stop-type')",
     "cachedResults={};renderSelected();\n    });\n    document.getElementById('sel-stop-type')", "seite_stop_signale"),
    ("Seite: Signale trotz veraltetem Bestand", PV, "      if (_veraltet) {", "      if (false) {", "seite_veraltet"),
    ("Python: Santa am Rand aus letzter Zeile", PYZ, '        entry = _sitzung(df, thanksgiving, -3, "nach")',
     '        entry = df[df.index < pd.Timestamp(thanksgiving)].index[-3]', "py_santa_rand"),
    ("Python: Zustand in Datumsvergleich", PYZ, "        jan5_next = _als_datum(_nth_trading_day(df2, year + 1, 1, 5))",
     "        jan5_next = _nth_trading_day(df2, year + 1, 1, 5)", "py_strategien_laufen"),
    ("Python: E8-Regeltermin fehlt", PYZ, '        t["regeltermin_ausstieg"] = regeltermin', '        pass', "py_e8_felder"),
    ("Month-End rückwärts von letzter Zeile", JS,
     "      if (d != null && monatsEnde != null && monatsEnde > this._ctx(rows).letzte) return this._terminZustand(rows, d);", "",
     "month_end_unvollstaendig"),
    ("Monthly 10: Rand nur aus Zeilen", JS, "        if (self._amRand(rows, y, m)) {\n          var letzte = self._ctx(rows).letzte;",
     "        if (false) {\n          var letzte = self._ctx(rows).letzte;", "monthly10_rand"),
    ("Python: Month-End rückwärts von letzter Zeile", PYZ,
     '        if d is not None and k and k[-1] > _ctx(df)["letzte"]:\n            return _termin_zustand(df, d)', "",
     "py_month_end_unvollstaendig"),
    ("Python: Monthly 10 ohne Randlogik", PYZ, "            if _am_rand(df, year, month):\n                # laufender Monat",
     "            if False:\n                # laufender Monat", "py_monthly10_rand"),
    ("Python: auswerten ohne Börsenkontext", PYZ,
     "    token = set_kontext(stichtag if stichtag is not None else heute(boerse), boerse)",
     "    token = set_kontext(stichtag if stichtag is not None else heute(boerse))", "py_xetra_kontext"),
    ("Python: Kontext nicht zurückgesetzt", PYZ, "        _KONTEXT_VAR.reset(token)", "        pass",
     "py_xetra_kontext"),
    ("Python: gemeinsamer Kontext statt ContextVar", PYZ,
     '_KONTEXT_VAR: ContextVar = ContextVar("plain_vanilla_kontext", default=None)',
     """class _Geteilt:
    _w = None
    def get(self): return self._w
    def set(self, k): t = self._w; self._w = k; return t
    def reset(self, t): self._w = t
_KONTEXT_VAR = _Geteilt()""", "py_kontext_parallel"),
    ("Python: kein Veraltet-Filter", PYZ, "        veraltet = _daten_veraltet(df)\n", "        veraltet = False\n", "py_veraltet"),
    ("Python: Veraltet-Grenze 10 statt mehr als 10", PYZ, "    while n <= 10:\n        ds = _kalender_sitzung(",
     "    while n < 10:\n        ds = _kalender_sitzung(", "py_veraltet"),
    ("Python: Filter vor dem Stop", PYZ,
     '        trades = STRATEGIES[key]["func"](df) or []\n        if stop_pct',
     '        trades = [t for t in (STRATEGIES[key]["func"](df) or []) if not (t.get("open") and _daten_veraltet(df))]\n        if stop_pct',
     "py_veraltet"),
    ("Python: LBR mit Wert des Tages", PYZ, "    vortag = hist.shift(1)", "    vortag = hist", "py_lbr_vortag"),
    ("Python: PF 999", PYZ, "        ) if sum(r for r in returns if r < 0) != 0 else None,", "        ) if sum(r for r in returns if r < 0) != 0 else 999,",
     "py_pf_none"),
    ("Python: offene Trades in der Statistik", PYZ,
     '    trades = [t for t in (trades or []) if not t.get("open") and np.isfinite(t["return_pct"])]',
     '    trades = [t for t in (trades or []) if np.isfinite(t["return_pct"])]', "py_offen_nicht_in_stats"),
    ("Python: Datenrand-Logik aus", PYZ, '        if t is not None and t > c["letzte"]:\n            return _termin_zustand(df, t)', "", "py_sep_offen"),
]

# Bewusst untaugliche Mutationen — das Urteil des Tests selbst wird geprüft
UNGUELTIG_ERWARTET = [
    ("Syntaxfehler (Probe muss abbrechen)", JS, "  heute: function(boerse) {", "  heute: function(boerse) {{", "lbr_vortag"),
    ("Anker trifft nicht", JS, "DIESER TEXT STEHT NICHT IN DER DATEI", "x", "lbr_vortag"),
    ("trifft das Gerüst, nicht das Verhalten", JS, "  streak: function(trades) {", "  streak_weg: function(trades) {", "streak_konfig"),
]


def _kopie(tmp: pathlib.Path):
    for rel in ("landing/js", "landing/pages"):
        shutil.copytree(REPO / rel, tmp / rel)
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


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if "--mutationen" in sys.argv:
        sys.exit(mutationen())
    P = pruefe_alles()
    for k, v in P.items():
        if v is not True:
            print("FEHLER", k, v)
    n = sum(v is not True for v in P.values())
    print(f"verify_plain_vanilla_1a: {len(P) - n}/{len(P)} Prüfungen bestanden")
    sys.exit(1 if n else 0)
