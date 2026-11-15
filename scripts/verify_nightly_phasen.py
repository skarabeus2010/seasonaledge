#!/usr/bin/env python3
"""
Wächter: ein gescheiterter Teil des Nightly ist in refresh_log und in der Health-Mail ROT (Audit 2026-11-15 mit Codex).

Anlass: der Nightly vom 14.11. endete mit Exit 1 (Saison-Score ^GSPC, Statement-Timeout), die Health-Mail zeigte ihn
grün — refresh_log kannte nur die Kurslücken und wurde VOR Landing-Chart/Wahl-Studie geschrieben. Dazu meldete der
log_return-Backfill „keine NULL-Rows ✓“, wenn seine Abfrage scheiterte, TDOM/TDOY-Schreibfehler wurden verschluckt,
und SA.supabase.getAll gab nach einer Fehlerantwort den Teilbestand als Erfolg zurück.

Führt die ECHTEN Funktionen offline aus (Datenbank, Yahoo, Unterprozesse = Stubs):
  [Health]   daily_health_check.bewerte_nightly: PHASE-Eintrag → rot, sonstiger Fehler → gelb, sauber → grün, alt → rot
  [Haupt]    nightly_refresh.main(): Grundlinie Exit 0 + grün; je eine gescheiterte Phase (Ticker/Saison, Kalender,
             Backfill-Abfrage, Wahl-Studie nach dem alten Logpunkt, refresh_log selbst) → Exit 1 und, wo eine Zeile
             geschrieben wird, PHASE-Eintrag + Health rot
  [Cache]    cache_manager tdom/tdoy: Upsert-Fehler mit schreibfehler_werfen=True geworfen, ohne nur geloggt
  [Ticker]   nightly_refresh.refresh_ticker_data: ein tdoy-Schreibfehler macht „Ticker-Refresh“ gescheitert
  [getAll]   landing/js/app.js getAll (wörtlich): zweite Seite = Fehlerobjekt → Ablehnung, kein Teilbestand

Aufruf:  py -3.14 scripts/verify_nightly_phasen.py      Exit 0 = alles erfüllt
"""
from __future__ import annotations

import io
import json
import os
import re
import subprocess
import sys
import types
from contextlib import redirect_stdout
from datetime import date, datetime, timedelta, timezone

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, WURZEL)

FEHLER: list[str] = []
ZAEHLER = {"n": 0}


def pruefe(kennung: str, bedingung: bool, text: str = "") -> None:
    ZAEHLER["n"] += 1
    if not bedingung:
        FEHLER.append(f"[{kennung}] {text}")


# ── Supabase-Stub ─────────────────────────────────────────────────────────────────────────────────────────────────
ZUSTAND = {"insert": [], "kaputt_backfill": False, "kaputt_log": False}


class _Antwort:
    def __init__(self, data):
        self.data = data


class _Abfrage:
    def __init__(self, name):
        self._name, self._sel, self._ist_null = name, None, False

    def select(self, sel, *a, **k):
        self._sel = sel
        return self

    def is_(self, spalte, wert):
        self._ist_null = (spalte == "log_return" and wert == "null")
        return self

    def insert(self, payload, *a, **k):
        if self._name == "refresh_log" and ZUSTAND["kaputt_log"]:
            raise ConnectionError("Stub: refresh_log nicht schreibbar")
        ZUSTAND["insert"].append((self._name, payload))
        return self

    def __getattr__(self, name):
        return lambda *a, **k: self

    def execute(self):
        if self._name == "prices" and self._ist_null and ZUSTAND["kaputt_backfill"]:
            raise RuntimeError("Stub: canceling statement due to statement timeout (57014)")
        if self._name == "prices" and self._sel == "date":
            heute = date.today()
            return _Antwort([{"date": (heute - timedelta(days=i)).isoformat()} for i in range(15)])
        return _Antwort([])


class _Client:
    def table(self, name):
        return _Abfrage(name)


def _stub_module(name, **attrs):
    m = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(m, k, v)
    sys.modules[name] = m
    import shared
    setattr(shared, name.split(".")[1], m)
    return m


def _stubs_grundlage():
    _stub_module("shared.supabase_client", get_client=lambda: _Client(), upsert_prices=lambda r: None)
    _stub_module("shared.cpi_data", update_cpi_in_db=lambda: None)
    _stub_module("shared.stress_score", vollauf=lambda t, protokoll=None: {"n_scores": 1})


# ── [Health] ──────────────────────────────────────────────────────────────────────────────────────────────────────
def block_health():
    import scripts.daily_health_check as h
    heute = date(2026, 11, 15)

    def zeile(errors, run_date="2026-11-14", success=372, total=372):
        return {"run_date": run_date, "errors": json.dumps(errors), "tickers_success": success,
                "tickers_total": total, "duration_seconds": 1000}
    s, _ = h.bewerte_nightly(zeile([]), heute)
    pruefe("Health sauber → grün", s == "green", s)
    s, d = h.bewerte_nightly(zeile(["PHASE: Saison-Score (1 Lade-/Schreibfehler)"]), heute)
    pruefe("Health PHASE → rot", s == "red" and "Saison-Score" in d, f"{s} {d}")
    s, _ = h.bewerte_nightly(zeile(["UNGEKLÄRT X: kein Kurs bei Yahoo"]), heute)
    pruefe("Health sonstiger Fehler → gelb", s == "yellow", s)
    s, _ = h.bewerte_nightly(zeile([], run_date="2026-11-12"), heute)
    pruefe("Health alter Lauf → rot", s == "red", s)
    s, _ = h.bewerte_nightly(zeile(["PHASE: Wahl-Studie"] + [f"UNGEKLÄRT T{i}" for i in range(25)]), heute)
    pruefe("Health PHASE vor vielen Lückenmeldungen → rot", s == "red", s)

    # Erwarteter Lauftag (Codex 2026-11-15): scheitert das refresh_log-Insert oder bricht der Lauf vor dem Logpunkt ab,
    # steht nur die Zeile vom Vortag da — sie darf dann nicht grün sein. Start 16:45 New York + 3 h Puffer.
    def utc(*a):
        return datetime(*a, tzinfo=timezone.utc)
    for jetzt, soll in ((utc(2026, 11, 15, 5, 0), date(2026, 11, 14)),     # Morgen-Check (EST)
                        (utc(2026, 11, 15, 23, 0), date(2026, 11, 14)),    # 18:00 NY: Lauf von heute noch im Puffer
                        (utc(2026, 11, 16, 1, 0), date(2026, 11, 15)),     # 20:00 NY: Lauf von heute muss da sein
                        (utc(2026, 7, 15, 1, 0), date(2026, 7, 14))):      # Sommerzeit (EDT, Start 20:45 UTC)
        ist = h.erwarteter_nightly_tag(jetzt)
        pruefe(f"Health erwarteter Nightly-Tag {jetzt.isoformat()}", ist == soll, f"{ist} statt {soll}")
    s, d = h.bewerte_nightly(zeile([], run_date="2026-11-14"), date(2026, 11, 15), date(2026, 11, 15))   # 1 Tag alt
    pruefe("Health Vortageszeile bei fehlendem Lauf → rot", s == "red" and "ohne refresh_log" in d, f"{s} {d}")
    s, _ = h.bewerte_nightly(zeile([], run_date="2026-11-15"), date(2026, 11, 16), date(2026, 11, 15))
    pruefe("Health Zeile des erwarteten Tags → grün", s == "green", s)

    # Der echte Check-1-Aufruf (pruefe_nightly) mit Attrappe. Einziges Fenster, in dem die Altersregel allein nicht reicht:
    # Sommer, 23:50 UTC = 19:50 NY — der Lauf von heute (Start 20:45 UTC) müsste fertig sein, die Vortageszeile ist 1 Tag alt.
    class _R:
        def __init__(self, z):
            self._z = z

        def __getattr__(self, n):
            return lambda *a, **k: self

        def execute(self):
            return _Antwort([self._z])

    class _C:
        def __init__(self, z):
            self._z = z

        def table(self, n):
            return _R(self._z)
    c1 = h.pruefe_nightly(_C(zeile([], run_date="2026-07-14")), utc(2026, 7, 15, 23, 50))
    pruefe("Health Aufruf mit erwartetem Tag (Sommerfenster) → rot", c1["status"] == "red", str(c1))
    c1 = h.pruefe_nightly(_C(zeile([], run_date="2026-07-15")), utc(2026, 7, 15, 23, 50))
    pruefe("Health Aufruf mit Zeile von heute → grün", c1["status"] == "green", str(c1))

    # Dateialter + Kalenderinhalt der Nightly-Ausgaben (in einem Temp-Ordner, echte Funktion)
    import tempfile
    import time as _t
    with tempfile.TemporaryDirectory() as tmp:
        jetzt = _t.time()
        heute_iso = datetime.fromtimestamp(jetzt, timezone.utc).date()

        def lege_an(alter_tage=0.0, erstes=None):
            for n in h.NIGHTLY_AUSGABEN:
                p = os.path.join(tmp, n)
                inhalt = json.dumps([{"date": (erstes or heute_iso.replace(day=1)).isoformat()}]) \
                    if n == "market_calendar.json" else "x"
                open(p, "w", encoding="utf-8").write(inhalt)
                os.utime(p, (jetzt - alter_tage * 86400,) * 2)
        lege_an()
        s, d = h.bewerte_nightly_ausgaben(tmp, jetzt)
        pruefe("Ausgaben frisch → grün", s == "green", f"{s} {d}")
        lege_an(alter_tage=3)
        s, d = h.bewerte_nightly_ausgaben(tmp, jetzt)
        pruefe("Ausgaben 3 Tage → gelb", s == "yellow", f"{s} {d}")
        lege_an(alter_tage=6)
        s, d = h.bewerte_nightly_ausgaben(tmp, jetzt)
        pruefe("Ausgaben 6 Tage → rot", s == "red", f"{s} {d}")
        lege_an(erstes=heute_iso - timedelta(days=135))
        s, d = h.bewerte_nightly_ausgaben(tmp, jetzt)
        pruefe("Kalender frisches Datum, alter Inhalt → rot", s == "red" and "Inhalt" in d, f"{s} {d}")
        os.remove(os.path.join(tmp, "wahlen_study.json"))
        s, d = h.bewerte_nightly_ausgaben(tmp, jetzt)
        pruefe("Ausgabe fehlt → rot", s == "red" and "fehlt" in d, f"{s} {d}")


# ── [Haupt] ───────────────────────────────────────────────────────────────────────────────────────────────────────
def block_haupt():
    _stubs_grundlage()
    import scripts.nightly_refresh as nr
    import scripts.daily_health_check as h
    echt_run = subprocess.run
    echt = {"cal": nr.refresh_calendar, "td": nr.refresh_ticker_data, "hb": nr.heartbeat}

    def lauf(phase_j_rc=0, kalender_kaputt=False, saison_kaputt=False, backfill_kaputt=False, log_kaputt=False,
             phase_k_rc=0):
        nr._FEHLGESCHLAGEN.clear()
        ZUSTAND.update(insert=[], kaputt_backfill=backfill_kaputt, kaputt_log=log_kaputt)

        def kal():
            if kalender_kaputt:
                raise RuntimeError("Stub: Kalender")
            return 0

        def td(*a, **k):
            if saison_kaputt:
                nr._FEHLGESCHLAGEN.append("Saison-Score (1 Lade-/Schreibfehler, z. B. ^GSPC: 57014)")
            return 0
        nr.refresh_calendar, nr.refresh_ticker_data, nr.heartbeat = kal, td, (lambda: None)
        nr.health_check = lambda t: {"missing_total": 0, "auto_fixed": 0, "missing_details": {}, "errors": [],
                                     "ungeprueft": set(), "gescheitert": []}

        def run(args, *a, **k):
            rc = phase_j_rc if any("build_wahlen" in str(x) for x in args) else 0
            if any("build_calendar_data" in str(x) for x in args):
                aufrufe["kalender"] += 1
                rc = phase_k_rc
            return subprocess.CompletedProcess(args, rc, "", "")
        aufrufe["kalender"] = 0
        subprocess.run = run
        try:
            with redirect_stdout(io.StringIO()):
                rc = nr.main()
        finally:
            subprocess.run = echt_run
        log = [pl for t, pl in ZUSTAND["insert"] if t == "refresh_log"]
        log = log[-1] if log else None
        status = h.bewerte_nightly(log, date.today())[0] if log else None
        return rc, list(nr._FEHLGESCHLAGEN), log, status

    def phasen(log):
        return [e for e in json.loads(log["errors"]) if e.startswith("PHASE: ")] if log else []
    aufrufe = {"kalender": 0}

    try:
        rc, fg, log, st = lauf()
        pruefe("Haupt Grundlinie Exit 0", rc == 0, f"Exit {rc} {fg}")
        pruefe("Haupt Grundlinie refresh_log geschrieben + grün", log is not None and st == "green", f"{log} {st}")
        pruefe("Haupt Marktkalender wird gebaut (Phase K)", aufrufe["kalender"] == 1, f"{aufrufe['kalender']} Aufrufe")

        rc, fg, log, st = lauf(phase_k_rc=1)
        pruefe("Haupt Marktkalender scheitert → PHASE + rot",
               rc == 1 and any("Marktkalender" in p for p in phasen(log)) and st == "red", f"Exit {rc} {phasen(log)} {st}")

        rc, fg, log, st = lauf(saison_kaputt=True)
        pruefe("Haupt Saison-Score → Exit 1", rc == 1, f"Exit {rc}")
        pruefe("Haupt Saison-Score → PHASE im refresh_log", any("Saison-Score" in p for p in phasen(log)), str(log))
        pruefe("Haupt Saison-Score → Health rot", st == "red", st)

        rc, fg, log, st = lauf(phase_j_rc=1)
        pruefe("Haupt Wahl-Studie (nach altem Logpunkt) → PHASE + rot",
               rc == 1 and any("Wahl-Studie" in p for p in phasen(log)) and st == "red", f"Exit {rc} {phasen(log)} {st}")

        rc, fg, log, st = lauf(kalender_kaputt=True)
        pruefe("Haupt Kalender → Exit 1 + PHASE", rc == 1 and any("Calendar" in p for p in phasen(log)),
               f"Exit {rc} {phasen(log)}")

        rc, fg, log, st = lauf(backfill_kaputt=True)
        pruefe("Haupt Backfill-Abfrage scheitert → Exit 1 + PHASE",
               rc == 1 and any("Backfill" in p for p in phasen(log)), f"Exit {rc} {phasen(log)}")

        rc, fg, log, st = lauf(log_kaputt=True)
        pruefe("Haupt refresh_log scheitert → Exit 1", rc == 1 and "refresh_log" in fg, f"Exit {rc} {fg}")
    finally:
        nr.refresh_calendar, nr.refresh_ticker_data, nr.heartbeat = echt["cal"], echt["td"], echt["hb"]


# ── [Cache] + [Ticker] ────────────────────────────────────────────────────────────────────────────────────────────
def block_cache_und_ticker():
    import pandas as pd

    def kaputt(_records):
        raise RuntimeError("Stub: Upsert 57014")
    _stub_module("shared.supabase_client", get_client=lambda: _Client(), upsert_prices=lambda r: None,
                 fetch_tdom_stats=lambda *a, **k: [], fetch_tdoy_stats=lambda *a, **k: [],
                 upsert_tdom_stats=kaputt, upsert_tdoy_stats=kaputt,
                 fetch_monthly_stats=lambda *a, **k: [], upsert_monthly_stats=lambda s: None)
    stats = pd.DataFrame({"avg_return": [0.1], "median_return": [0.1], "win_rate": [50.0], "std_dev": [1.0],
                          "count": [10]}, index=[1])
    _stub_module("shared.tdom_analysis", build_tdom_stats=lambda df, strategy, direction: stats)
    _stub_module("shared.tdoy_analysis", build_tdoy_stats=lambda df, strategy, direction: stats)
    sys.modules.pop("shared.cache_manager", None)
    import shared.cache_manager as cm
    df = pd.DataFrame({"Close": [1.0, 2.0]}, index=pd.to_datetime(["2026-11-12", "2026-11-13"]))
    for art, fn in (("tdom", cm.get_or_compute_tdom_stats), ("tdoy", cm.get_or_compute_tdoy_stats)):
        try:
            fn("SPY", df, schreibfehler_werfen=True)
            pruefe(f"Cache {art} wirft mit schreibfehler_werfen", False, "kein Fehler geworfen")
        except RuntimeError:
            pruefe(f"Cache {art} wirft mit schreibfehler_werfen", True)
        try:
            r = fn("SPY", df)
            pruefe(f"Cache {art} ohne Flag liefert Werte", len(r) == 1, str(r))
        except Exception as e:  # noqa: BLE001
            pruefe(f"Cache {art} ohne Flag liefert Werte", False, f"{type(e).__name__}: {e}")

    # [Ticker]: der echte Ticker-Pfad zählt einen tdoy-Schreibfehler als Fehler
    _stub_module("shared.yahoo_downloader", download_data=lambda t, period="max": df, preprocess=lambda d: d)
    _stub_module("shared.saison_score_betrieb", fuer_ticker=lambda t, c: {"status": "ok"},
                 schreibe=lambda c, a, b: [], scanner_zeile=lambda *a: {}, protokoll_zeile=lambda *a: {})
    _stub_module("shared.tdom_analysis", build_tdom_stats=lambda df, strategy, direction: pd.DataFrame())
    # refresh_ticker_data importiert shared.calculations (zieht plotly, das im Deploy-Gate fehlt — Deploy 016152f rot)
    _stub_module("shared.calculations", build_year_data=lambda *a, **k: None,
                 calculate_seasonal_average=lambda *a, **k: None)
    import scripts.nightly_refresh as nr
    nr._FEHLGESCHLAGEN.clear()
    with redirect_stdout(io.StringIO()):
        nr.refresh_ticker_data(["SPY"])
    pruefe("Ticker tdoy-Schreibfehler → Ticker-Refresh gescheitert",
           any(f.startswith("Ticker-Refresh") and "tdoy_stats" in f for f in nr._FEHLGESCHLAGEN), str(nr._FEHLGESCHLAGEN))


# ── [getAll] ──────────────────────────────────────────────────────────────────────────────────────────────────────
NODE_PROBE = r"""
const SA = {}; global.SA = SA;
const SEITEN = JSON.parse(process.argv[process.argv.length - 1]);
let n = 0;
const sb = { get: () => Promise.resolve(SEITEN[n++]) };
sb.getAll = (QUELLE);
sb.getAll('polymarket_prices', 'order=ts.asc').then(
  r => console.log(JSON.stringify({ ok: true, n: r.length })),
  e => console.log(JSON.stringify({ ok: false, msg: String(e.message) })));
"""


def block_getall():
    src = open(os.path.join(WURZEL, "landing", "js", "app.js"), encoding="utf-8").read()
    m = re.search(r"\n  getAll: (function\(table, query, pageSize\) \{.*?\n  \}),\n", src, re.S)
    pruefe("getAll im Quelltext gefunden", m is not None, "Anker in app.js trifft nicht")
    if not m:
        return
    probe = NODE_PROBE.replace("(QUELLE)", "(" + m.group(1) + ")")

    def lauf(seiten):
        out = subprocess.run(["node", "-e", probe, json.dumps(seiten)], capture_output=True, text=True, timeout=60)
        try:
            return json.loads(out.stdout.strip().splitlines()[-1])
        except Exception:  # noqa: BLE001
            return {"absturz": out.stderr[-300:]}
    voll = [[{"i": i} for i in range(1000)], [{"i": 1}]]
    r = lauf(voll)
    pruefe("getAll Grundlinie 1001 Zeilen", r.get("ok") is True and r.get("n") == 1001, str(r))
    r = lauf([voll[0], {"message": "canceling statement due to statement timeout", "code": "57014"}])
    pruefe("getAll Fehlerantwort → Ablehnung statt Teilbestand", r.get("ok") is False and
           "statement timeout" in r.get("msg", ""), str(r))


def main() -> int:
    for name, block in (("Health", block_health), ("Haupt", block_haupt),
                        ("Cache/Ticker", block_cache_und_ticker), ("getAll", block_getall)):
        try:
            block()
        except Exception as e:  # eine Ausnahme ist nie ein Nachweis
            FEHLER.append(f"[Ausnahme] Block {name}: {type(e).__name__}: {e}")
    print(f"verify_nightly_phasen: {ZAEHLER['n'] - len(FEHLER)}/{ZAEHLER['n']} Prüfungen bestanden")
    for f in FEHLER:
        print("  FEHL", f)
    print(f"PROBE-ENDE {ZAEHLER['n']} Pruefungen")
    return 1 if FEHLER else 0


if __name__ == "__main__":
    sys.exit(main())
