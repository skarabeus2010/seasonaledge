#!/usr/bin/env python3
"""
Wächter: Ein Kalender- oder Zuordnungsfehler macht die Jobs ROT (Paket 3, Codex Runde 1).

Führt die ECHTEN Funktionen offline aus — Datenbank und Yahoo sind Stubs, sonst nichts:
  [Intraday]  intraday_refresh.main() mit neun gültigen Tickern und einem unbekannten (^SA_XYZ):
              Exit 1, obwohl ein Fehler unter zehn Tickern unter der Yahoo-Toleranz liegt; alle gültig → Exit 0.
  [Nightly]   nightly_refresh.health_check() mit einem gültigen und einem unbekannten Ticker: der
              unbekannte ist „ungeprüft“ und macht die Phase gescheitert; tickers_erfolgreich zählt ihn nicht;
              Datenbank vor der Schleife weg → alle ungeprüft.
  [Hauptlauf] nightly_refresh.main() (übrige Phasen gestubbt): Exit 1 und refresh_log ohne den Ticker als Erfolg.
  Intraday zusätzlich: Kalenderfehler am zweiten Datum → keine Zeile mit Teilnummern.

Aufruf:  py -3.14 scripts/verify_kalender_fehlerweitergabe.py      Exit 0 = alles erfüllt
"""
from __future__ import annotations

import io
import os
import sys
import types
from contextlib import redirect_stdout
from datetime import date, timedelta

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, WURZEL)

FEHLER: list[str] = []
ZAEHLER = {"n": 0}


def pruefe(kennung: str, bedingung: bool, text: str = "") -> None:
    ZAEHLER["n"] += 1
    if not bedingung:
        FEHLER.append(f"[{kennung}] {text}")


class _Antwort:
    def __init__(self, data):
        self.data = data


GESCHRIEBEN: dict[str, list] = {"upsert": [], "insert": []}


class _Abfrage:
    """Jede Kettenmethode liefert sich selbst; execute() liefert die vorbereiteten Daten.
    Nur `select("date")` auf prices bekommt Daten (Health-Check), alles andere eine leere Liste."""
    def __init__(self, name, daten):
        self._name, self._daten, self._sel = name, daten, None

    def select(self, sel, *a, **k):
        self._sel = sel
        return self

    def insert(self, payload, *a, **k):
        GESCHRIEBEN["insert"].append((self._name, payload))
        return self

    def __getattr__(self, name):
        return lambda *a, **k: self

    def execute(self):
        return _Antwort(self._daten if (self._name == "prices" and self._sel == "date") else [])


class _Client:
    def __init__(self, daten):
        self._daten = daten

    def table(self, name):
        return _Abfrage(name, self._daten)


def _stub_supabase(daten, kaputt: bool = False):
    mod = types.ModuleType("shared.supabase_client")

    def get_client():
        if kaputt:
            raise ConnectionError("Stub: Datenbank nicht erreichbar")
        return _Client(daten)
    mod.get_client = get_client
    mod.upsert_prices = lambda records: GESCHRIEBEN["upsert"].extend(records)
    sys.modules["shared.supabase_client"] = mod


GUELTIG = ["SPY", "QQQ", "AAPL", "MSFT", "NVDA", "SAP.DE", "^GDAXI", "BTC-USD", "EURUSD=X"]
UNBEKANNT = "^SA_XYZ"


def block_intraday() -> None:
    import pandas as pd
    _stub_supabase([])   # keine Vorzeile in der DB
    import scripts.intraday_refresh as ir

    tage = pd.DatetimeIndex([pd.Timestamp("2026-10-06"), pd.Timestamp("2026-10-07"), pd.Timestamp("2026-10-08")])
    ir.download_data = lambda ticker, period="5d": pd.DataFrame({"Close": [100.0, 101.0, 102.0]}, index=tage)

    def lauf(tickers):
        ir.KALENDER_FEHLER.clear()
        ir.get_active_groups = lambda now, force=None: {"test": {"tickers": tickers}}
        alt_argv = sys.argv
        sys.argv = ["intraday_refresh.py"]
        try:
            with redirect_stdout(io.StringIO()):
                return ir.main()
        finally:
            sys.argv = alt_argv

    pruefe("Intraday alle gültig → Exit 0", lauf(GUELTIG) == 0, "Grundlinie ist schon rot")
    rc = lauf(GUELTIG + [UNBEKANNT])
    pruefe("Intraday Zuordnungsfehler → Exit 1", rc == 1,
           f"Exit {rc} — ein Kalenderfehler darf nicht unter die Yahoo-Toleranz fallen")
    pruefe("Intraday Zuordnungsfehler vermerkt", ir.KALENDER_FEHLER == [UNBEKANNT], f"KALENDER_FEHLER = {ir.KALENDER_FEHLER}")

    # Kalenderfehler erst am ZWEITEN Datum: die Nummer des ersten darf nicht veröffentlicht werden.
    import shared.exchange_holidays as eh
    echt = eh.is_trading_day
    zaehler = {"n": 0}

    def wackelig(d, ex="NYSE"):
        zaehler["n"] += 1
        if zaehler["n"] == 2:
            raise ValueError("Stub: Kalenderfehler am zweiten Datum")
        return echt(d, ex)
    GESCHRIEBEN["upsert"].clear()
    eh.is_trading_day = wackelig
    try:
        rc = lauf(["SPY"])
    finally:
        eh.is_trading_day = echt
    mit_nummer = [r for r in GESCHRIEBEN["upsert"] if "tdoy" in r or "tdom" in r]
    pruefe("Intraday keine Teilnummern nach Fehler", rc == 1 and bool(GESCHRIEBEN["upsert"]) and not mit_nummer,
           f"Exit {rc}, {len(mit_nummer)} von {len(GESCHRIEBEN['upsert'])} Zeilen tragen trotzdem Nummern")


def block_nightly() -> None:
    heute = date.today()
    alle = [{"date": (heute - timedelta(days=i)).isoformat()} for i in range(15)]
    _stub_supabase(alle)   # keine Lücke für gültige Ticker
    import scripts.nightly_refresh as nr

    with redirect_stdout(io.StringIO()) as aus:
        r = nr.health_check(["SPY", UNBEKANNT])
    pruefe("Nightly unbekannter Ticker ungeprüft", r["ungeprueft"] == {UNBEKANNT}, f"ungeprueft = {r['ungeprueft']}")
    pruefe("Nightly Phase gescheitert", bool(r["gescheitert"]), "Health-Check meldet keinen Fehlschlag")
    pruefe("Nightly nicht „vollständig“", "Alle Ticker vollständig" not in aus.getvalue(),
           "meldet trotz ungeprüftem Ticker Vollständigkeit")
    pruefe("Nightly Erfolgszählung ohne ungeprüfte",
           nr.tickers_erfolgreich(["SPY", UNBEKANNT], r["missing_details"], r["ungeprueft"]) == 1,
           f"zählt {nr.tickers_erfolgreich(['SPY', UNBEKANNT], r['missing_details'], r['ungeprueft'])} statt 1")
    with redirect_stdout(io.StringIO()):
        r2 = nr.health_check(["SPY", "SAP.DE"])
    pruefe("Nightly Grundlinie gültig", not r2["ungeprueft"] and not r2["gescheitert"], f"{r2['gescheitert']}")

    # Abbruch VOR der Schleife (Datenbank nicht erreichbar): niemand ist geprüft.
    _stub_supabase(alle, kaputt=True)
    with redirect_stdout(io.StringIO()):
        r3 = nr.health_check(["SPY", "SAP.DE"])
    pruefe("Nightly Abbruch: alle ungeprüft",
           r3["ungeprueft"] == {"SPY", "SAP.DE"} and bool(r3["gescheitert"]) and bool(r3["errors"]),
           f"ungeprueft={r3['ungeprueft']}, errors={r3['errors']}")
    _stub_supabase(alle)


def block_nightly_hauptlauf() -> None:
    """Der ECHTE main(): Exit-Code und refresh_log-Zeile, alle übrigen Phasen gestubbt."""
    import subprocess
    import shared
    import shared.symbols as sy
    heute = date.today()
    _stub_supabase([{"date": (heute - timedelta(days=i)).isoformat()} for i in range(15)])
    stubs = (("shared.cpi_data", {"update_cpi_in_db": lambda: None}),
             ("shared.stress_score", {"vollauf": lambda t, protokoll=None: {"n_scores": 1}}),
             ("shared.spot_vol_beta", {"load_spot_vol_data": lambda: None,
                                       "compute_spot_vol_beta": lambda df: (df, None),
                                       "sync_spot_vol_to_db": lambda df: 0}))
    for name, attrs in stubs:
        m = types.ModuleType(name)
        for k, v in attrs.items():
            setattr(m, k, v)
        sys.modules[name] = m
        setattr(shared, name.split(".")[1], m)
    import scripts.nightly_refresh as nr
    nr.refresh_calendar = lambda: 0
    nr.refresh_ticker_data = lambda *a, **k: 0
    nr.heartbeat = lambda: None
    echt_run = subprocess.run
    subprocess.run = lambda *a, **k: subprocess.CompletedProcess(a, 0, "", "")

    def lauf():
        nr._FEHLGESCHLAGEN.clear()
        GESCHRIEBEN["insert"].clear()
        with redirect_stdout(io.StringIO()):
            rc = nr.main()
        log = [pl for t, pl in GESCHRIEBEN["insert"] if t == "refresh_log"]
        return rc, list(nr._FEHLGESCHLAGEN), (log[-1] if log else None)

    try:
        n = len(sy.SYMBOLS)
        rc0, fg0, log0 = lauf()
        pruefe("Hauptlauf Grundlinie Exit 0", rc0 == 0, f"Exit {rc0}, gescheitert: {fg0}")
        pruefe("Hauptlauf Grundlinie alle erfolgreich", log0 is not None and log0["tickers_success"] == n,
               f"refresh_log: {None if log0 is None else log0['tickers_success']} von {n}")
        sy.SYMBOLS[UNBEKANNT] = {"exchange": "Mondbörse"}
        sy._SYMBOLS_GROSS = None
        try:
            rc1, fg1, log1 = lauf()
        finally:
            del sy.SYMBOLS[UNBEKANNT]
            sy._SYMBOLS_GROSS = None
        pruefe("Hauptlauf Zuordnungsfehler → Exit 1", rc1 == 1, f"Exit {rc1}")
        pruefe("Hauptlauf Health-Check als gescheitert gemeldet",
               any(f.startswith("Health-Check") for f in fg1), f"{fg1}")
        pruefe("Hauptlauf refresh_log zählt ihn nicht als Erfolg", log1 is not None and log1["tickers_success"] == n,
               f"{None if log1 is None else log1['tickers_success']} statt {n} (von {n + 1})")
    finally:
        subprocess.run = echt_run


def main() -> int:
    for name, block in (("Intraday", block_intraday), ("Nightly", block_nightly),
                        ("Nightly-Hauptlauf", block_nightly_hauptlauf)):
        try:
            block()
        except Exception as e:  # eine Ausnahme ist nie ein Nachweis
            FEHLER.append(f"[Ausnahme] Block {name}: {type(e).__name__}: {e}")
    print(f"verify_kalender_fehlerweitergabe: {ZAEHLER['n'] - len(FEHLER)}/{ZAEHLER['n']} Prüfungen bestanden")
    for f in FEHLER:
        print("  FEHL", f)
    print(f"PROBE-ENDE {ZAEHLER['n']} Pruefungen")
    return 1 if FEHLER else 0


if __name__ == "__main__":
    sys.exit(main())
