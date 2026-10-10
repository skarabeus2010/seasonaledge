#!/usr/bin/env python3
"""
Wächter P2: jeder Schreiber von `prices.tdom/tdoy` schreibt Nummern nach Börsenkalender (Plan v7, Codex R7).

Führt die ECHTEN Schreibwege offline aus — Supabase und Yahoo sind Stubs, sonst nichts — und vergleicht die
TATSÄCHLICH übergebenen Datensätze mit einer unabhängigen Zählung (numpy.busday_count über die
Feiertage des Produktionskalenders; dieselbe Referenz wie verify_handelstag_nummern.py):

  [Nightly]     refresh_ticker_data: die geschriebenen Zeilen der letzten 7 Tage, Lücke im Fenster
  [Lücke]       health_check: nachgeladen (mit Nummern), ungeklärt (gemeldet, kein Erfolg), Lade-/Upsertfehler
  [Intraday]    refresh_tickers: Lücke, Monats-/Jahreswechsel, geschlossener Tag (0-Werte)
  [Onboarding]  backfill_ticker: Historie ab 1. Juli, bestehende Zeilen OHNE Nummern, Upsertfehler → ok=False;
                onboard_ticker.main → Exit 1, wenn der Backfill scheitert
  [Lückenfüller] fix_missing_days: Nummern mit, Batchfehler → Exit 1
  [Reparatur]   backfill_tdoy: Trockenlauf schreibt nichts; Grenzen (Ticker, Bereich, 2001, Status, Menge)
                vor dem ersten Request; nur tdom/tdoy; Bestätigung je Zeile
  [Bestand]     jede Python-Datei, die in `prices` schreibt, ist hier bekannt; die übrigen Schreiber senden
                keine Nummernspalten

Aufruf:  py -3.14 scripts/verify_schreiber_nummern.py      Exit 0 = alles erfüllt (braucht pandas + numpy)
"""
from __future__ import annotations

import ast
import io
import os
import re
import sys
import types
from contextlib import redirect_stdout
from datetime import date, timedelta

import numpy as np
import pandas as pd

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, WURZEL)


def _kein_client(*_a, **_k):
    raise RuntimeError("Stub: kein echter Supabase-Client im Wächter")


# Gleiches Verhalten mit und ohne installiertes supabase-Paket: das Deploy-Gate hat es nicht, und dann wirft
# supabase_client.py beim Import einen ABGEFANGENEN ImportError, den die Absturzwache als Absturz zählte
# (Deploy d63fdf1, 2026-10-10 — lokal unsichtbar, weil das Paket dort installiert ist). Der Client selbst kommt
# ohnehin aus stub_supabase().
_sb = types.ModuleType("supabase")
_sb.create_client = _kein_client
sys.modules["supabase"] = _sb

from shared.exchange_holidays import get_holidays  # noqa: E402
from shared.symbols import get_exchange_for_holidays  # noqa: E402

FEHLER: list[str] = []
ZAEHLER = {"n": 0}


def pruefe(kennung: str, bedingung: bool, text: str = "") -> None:
    ZAEHLER["n"] += 1
    if not bedingung:
        FEHLER.append(f"[{kennung}] {text}")


# Abstürze über ihre echte Klasse erkennen — auch abgefangene (Codex P2 R1: die Ausgabe enthielt den
# Klassennamen nicht, „'NoneType' object has no attribute 'real'“). sys.monitoring meldet JEDE in den
# Schreiberdateien ausgelöste Ausnahme; erlaubt ist nur ValueError (der gewollte Kalender-/Zuordnungsfehler).
# Stubs lösen ihre Fehler in DIESER Datei aus und zählen deshalb nicht.
WACH = {os.path.normcase(os.path.join(WURZEL, rel)) for rel in (
    "scripts/nightly_refresh.py", "scripts/intraday_refresh.py", "scripts/backfill_new_ticker.py",
    "scripts/onboard_ticker.py", "scripts/fix_missing_days.py", "scripts/backfill_tdoy.py",
    "shared/exchange_holidays.py", "shared/supabase_client.py")}
ABSTUERZE: list[str] = []
_WERKZEUG = 3


_GESEHEN: list = []   # starke Referenzen, damit id() während des Laufs eindeutig bleibt


def _beim_ausloesen(code, offset, exc):
    # RAISE feuert in JEDEM Frame, durch den eine Ausnahme läuft — gewertet wird nur ihr Ursprung
    # (das erste Auftreten). Ein Stub-Fehler, der durch upsert_prices hindurchläuft, ist kein Absturz.
    if any(e is exc for e in _GESEHEN):
        return
    _GESEHEN.append(exc)
    # NUR die ausdrücklich erlaubte Umhüllung `raise UpsertTeilfehler(...) from e` mit bereits gesehenem e gilt als
    # Weitergabe (sie trägt einen Stub-Fehler weiter und nennt den bestätigten Teil). Jede andere verkettete
    # Ausnahme ist ein neuer Ursprung — sonst verdeckte `raise AttributeError(...) from e` einen echten Absturz
    # (Codex P2 R3).
    if type(exc).__name__ == "UpsertTeilfehler" and exc.__cause__ is not None \
            and any(e is exc.__cause__ for e in _GESEHEN):
        return
    if os.path.normcase(os.path.abspath(code.co_filename)) in WACH and not isinstance(exc, (ValueError, StopIteration)):
        ABSTUERZE.append(f"{type(exc).__name__} in {os.path.basename(code.co_filename)}:{code.co_name}: {str(exc)[:80]}")


def absturzwache_an() -> None:
    sys.monitoring.use_tool_id(_WERKZEUG, "verify_schreiber_nummern")
    sys.monitoring.register_callback(_WERKZEUG, sys.monitoring.events.RAISE, _beim_ausloesen)
    sys.monitoring.set_events(_WERKZEUG, sys.monitoring.events.RAISE)


def absturzwache_aus() -> None:
    sys.monitoring.set_events(_WERKZEUG, 0)
    sys.monitoring.free_tool_id(_WERKZEUG)


def referenz(ticker: str, daten: list[str]) -> dict[str, tuple[int, int]]:
    """Unabhängige Zählung: numpy.busday_count, Endpunkt d+1 (busday_count schließt das Ende aus)."""
    b = get_exchange_for_holidays(ticker)
    jahre = sorted({int(d[:4]) for d in daten})
    fei = np.array(sorted(get_holidays(b, jahre[0], jahre[-1])), dtype="datetime64[D]")
    kw = dict(weekmask="1111111" if b == "CRYPTO" else "1111100", holidays=fei)
    d = np.array(daten, dtype="datetime64[D]")
    tdoy = np.busday_count(d.astype("datetime64[Y]").astype("datetime64[D]"), d + 1, **kw)
    tdom = np.busday_count(d.astype("datetime64[M]").astype("datetime64[D]"), d + 1, **kw)
    return {daten[i]: (int(tdom[i]), int(tdoy[i])) for i in range(len(daten))}


def vergleiche(kennung: str, ticker: str, records: list[dict], mit_nummern: set[str] | None = None,
               soll_daten: list[str] | None = None) -> None:
    """Jede Zeile mit Nummern == Referenz; Zeilen in `mit_nummern` MÜSSEN Nummern tragen, alle übrigen nicht.
    `soll_daten`: die unabhängig festgelegte, VOLLSTÄNDIGE Liste der zu schreibenden Daten (mit Duplikaten) —
    sonst bliebe ein Schreiber grün, der nur einen Teil schreibt (Codex P2 R1)."""
    soll = referenz(ticker, [r["date"] for r in records]) if records else {}
    falsch, fehlt, zuviel = [], [], []
    if soll_daten is not None and sorted(r["date"] for r in records) != sorted(soll_daten):
        falsch.append(f"Datumsmenge {len(records)} statt {len(soll_daten)}")
    for r in records:
        hat = "tdom" in r or "tdoy" in r
        if mit_nummern is not None:
            if r["date"] in mit_nummern and not hat:
                fehlt.append(r["date"])
            if r["date"] not in mit_nummern and hat:
                zuviel.append(r["date"])
        if hat and (r.get("tdom"), r.get("tdoy")) != soll[r["date"]]:
            falsch.append(f"{r['date']}: {(r.get('tdom'), r.get('tdoy'))} statt {soll[r['date']]}")
    pruefe(kennung, records and not falsch and not fehlt and not zuviel,
           f"{len(records)} Zeilen; falsch {falsch[:3]}, ohne Nummern {fehlt[:3]}, unerlaubt mit Nummern {zuviel[:3]}")


# ── Stubs ─────────────────────────────────────────────────────────────────────

class Speicher:
    upsert: list[dict] = []                       # jeder gesendete Datensatz, wie gesendet
    anfragen: list[list[str]] = []                # Spaltenliste je Upsert-Anfrage
    update: list[tuple[dict, dict]] = []
    db_daten: dict[str, list[dict]] = {}          # ticker → gespeicherte Zeilen
    upsert_fehler = False
    fehler_bei_anfrage: int | None = None         # n-te Upsert-Anfrage (1-basiert) scheitert
    fehler_wenn = None                            # Bedingung über die Datensätze einer Anfrage
    update_treffer = 1


class _Antwort:
    def __init__(self, data, count=None):
        self.data, self.count = data, count


class _Abfrage:
    def __init__(self, tabelle):
        self.t, self.filter, self.sel, self.bereich, self.upd, self.ups = tabelle, {}, None, None, None, None
        self.gte_, self.lte_ = None, None

    def select(self, sel, *a, **k):
        self.sel = sel
        return self

    def eq(self, k, v):
        self.filter[k] = v
        return self

    def gte(self, k, v):
        self.gte_ = v
        return self

    def lte(self, k, v):
        self.lte_ = v
        return self

    def range(self, a, b):
        self.bereich = (a, b)
        return self

    def update(self, werte):
        self.upd = werte
        return self

    def upsert(self, records, *a, **k):
        self.ups = list(records)
        return self

    def __getattr__(self, name):
        return lambda *a, **k: self

    def execute(self):
        if self.ups is not None:
            return self._upsert_wie_postgrest()
        if self.upd is not None:
            Speicher.update.append((dict(self.filter), dict(self.upd)))
            return _Antwort([{"ok": 1}] * Speicher.update_treffer)
        if self.t != "prices":
            return _Antwort([])
        zeilen = Speicher.db_daten.get(self.filter.get("ticker"), [])
        if self.gte_:
            zeilen = [z for z in zeilen if z["date"] >= self.gte_]
        if self.lte_:
            zeilen = [z for z in zeilen if z["date"] <= self.lte_]
        if self.bereich:
            zeilen = zeilen[self.bereich[0]:self.bereich[1] + 1]
        return _Antwort([dict(z) for z in zeilen])

    def _upsert_wie_postgrest(self):
        """Spaltenliste = Vereinigung ALLER Schlüssel der Anfrage; fehlende Werte werden NULL
        (PostgREST merge-duplicates) — genau der Transportvertrag, an dem Codex P2 R1 den Fehler fand."""
        if self.t != "prices":
            return _Antwort([])
        Speicher.anfragen.append(sorted({k for r in self.ups for k in r}))
        if Speicher.upsert_fehler or Speicher.fehler_bei_anfrage == len(Speicher.anfragen) or \
                (Speicher.fehler_wenn is not None and Speicher.fehler_wenn(self.ups)):
            raise RuntimeError("Stub: Upsert abgelehnt")
        spalten = set(Speicher.anfragen[-1])
        for r in self.ups:
            Speicher.upsert.append(dict(r))
            zeile = {c: r.get(c) for c in spalten}
            tab = Speicher.db_daten.setdefault(r["ticker"], [])
            alt = next((z for z in tab if z["date"] == r["date"]), None)
            if alt is None:
                tab.append(zeile)
                tab.sort(key=lambda z: z["date"])
            else:
                alt.update(zeile)
        return _Antwort([])


class _Client:
    def table(self, name):
        return _Abfrage(name)


def stub_supabase():
    """Das ECHTE shared.supabase_client (inkl. upsert_prices) — nur der Client ist ein Stub."""
    if isinstance(sys.modules.get("shared.supabase_client"), types.ModuleType) and \
            getattr(sys.modules["shared.supabase_client"], "__file__", None) is None:
        del sys.modules["shared.supabase_client"]
    import shared.supabase_client as sbc
    sbc.get_client = lambda force_new=False: _Client()


def zuruecksetzen():
    Speicher.upsert, Speicher.anfragen, Speicher.update, Speicher.db_daten = [], [], [], {}
    Speicher.upsert_fehler, Speicher.fehler_bei_anfrage, Speicher.update_treffer = False, None, 1
    Speicher.fehler_wenn = None


def kursframe(daten: list[str]) -> pd.DataFrame:
    idx = pd.DatetimeIndex([pd.Timestamp(d) for d in daten])
    werte = np.linspace(100, 110, len(daten))
    return pd.DataFrame({"Open": werte, "High": werte + 1, "Low": werte - 1, "Close": werte,
                         "Volume": [1000] * len(daten)}, index=idx)


def handelstage(ticker: str, von: date, bis: date) -> list[str]:
    from shared.exchange_holidays import is_trading_day
    b, d, out = get_exchange_for_holidays(ticker), von, []
    while d <= bis:
        if is_trading_day(d, b):
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


# ── Blöcke ────────────────────────────────────────────────────────────────────

def block_nightly() -> None:
    zuruecksetzen()
    stub_supabase()
    heute = date.today()
    tage = handelstage("SAP.DE", heute - timedelta(days=12), heute - timedelta(days=1))
    tage = [t for i, t in enumerate(tage) if i != len(tage) - 3]          # eine Lücke im Fenster
    yd = types.ModuleType("shared.yahoo_downloader")
    yd.download_data = lambda ticker, period="max": kursframe(tage)

    def preprocess(df):
        df = df.copy()
        df["log_return"] = np.log(df["Close"] / df["Close"].shift(1))
        df["tdoy"] = range(1, len(df) + 1)      # Zeilenzählung wie preprocess() — darf NICHT geschrieben werden
        df["tdom"] = range(1, len(df) + 1)
        return df
    yd.preprocess = preprocess
    sys.modules["shared.yahoo_downloader"] = yd
    for name, attrs in (("shared.cache_manager", ("get_or_compute_monthly_stats", "get_or_compute_tdom_stats",
                                                  "get_or_compute_tdoy_stats")),
                        ("shared.calculations", ("build_year_data", "calculate_seasonal_average"))):
        m = types.ModuleType(name)
        for a in attrs:
            setattr(m, a, lambda *x, **k: None)
        sys.modules[name] = m
    sb = types.ModuleType("shared.saison_score_betrieb")
    def _kein_score(*a, **k):
        raise ValueError("Stub: kein Saison-Score")      # gewollter Fehler, kein Absturz
    sb.fuer_ticker = _kein_score
    sb.scanner_zeile = lambda *a, **k: {}
    sb.protokoll_zeile = lambda *a, **k: {}
    sb.schreibe = lambda *a, **k: []
    sys.modules["shared.saison_score_betrieb"] = sb
    import shared
    shared.saison_score_betrieb = sb
    sys.modules.pop("scripts.nightly_refresh", None)
    import scripts.nightly_refresh as nr
    with redirect_stdout(io.StringIO()) as aus:
        nr.refresh_ticker_data(["SAP.DE"], years_back=1, quick_mode=True)
    geschrieben = [r for r in Speicher.upsert if r["ticker"] == "SAP.DE"]
    fenster = [t for t in tage if t >= (heute - timedelta(days=7)).isoformat()]   # Soll unabhängig vom Code
    vergleiche("Nightly Kalendernummern trotz Lücke", "SAP.DE", geschrieben, set(fenster), soll_daten=fenster)


def block_luecke() -> None:
    import scripts.nightly_refresh as nr
    heute = date.today()
    soll = handelstage("SPY", heute - timedelta(days=7), heute - timedelta(days=1))
    if len(soll) < 3:
        FEHLER.append("[Aufbau] Lückenfüller: zu wenige Handelstage im Fenster")
        return
    fehlend = soll[-2:]

    def lauf(yahoo, upsert_fehler=False):
        zuruecksetzen()
        stub_supabase()
        Speicher.db_daten["SPY"] = [{"date": d} for d in soll if d not in fehlend]
        Speicher.upsert_fehler = upsert_fehler
        yd = types.ModuleType("shared.yahoo_downloader")
        yd.download_data = yahoo
        sys.modules["shared.yahoo_downloader"] = yd
        with redirect_stdout(io.StringIO()) as aus:
            r = nr.health_check(["SPY"])
        return r, aus.getvalue()

    r, _ = lauf(lambda t, period="1mo": kursframe(fehlend))
    vergleiche("Lücke nachgeladen mit Kalendernummern", "SPY", Speicher.upsert, set(fehlend), soll_daten=fehlend)
    pruefe("Lücke nachgeladen ist vollständig", not r["missing_details"] and not r["ungeprueft"], f"{r}")

    r, aus = lauf(lambda t, period="1mo": kursframe(fehlend[:1]))
    pruefe("Lücke ungeklärt wird gemeldet", r["missing_details"].get("SPY") == fehlend[1:]
           and any(e.startswith("UNGEKLÄRT SPY") for e in r["errors"]) and "vollständig" not in aus,
           f"missing={r['missing_details']}, errors={r['errors']}")
    pruefe("Lücke ungeklärt ist kein Erfolg", nr.tickers_erfolgreich(["SPY"], r["missing_details"], r["ungeprueft"]) == 0)

    r, _ = lauf(lambda t, period="1mo": pd.DataFrame())
    pruefe("Lücke leeres Yahoo ist ungeklärt, nicht „Börse zu“", r["missing_details"].get("SPY") == fehlend,
           f"{r['missing_details']}")

    def kaputt(t, period="1mo"):
        raise ConnectionError("Stub: Yahoo weg")
    r, _ = lauf(kaputt)
    pruefe("Lücke Ladefehler ist Fehler", "SPY" in r["ungeprueft"] and any("Yahoo-Nachladen" in e for e in r["errors"]),
           f"{r['errors']}")

    r, _ = lauf(lambda t, period="1mo": kursframe(fehlend), upsert_fehler=True)
    pruefe("Lücke Upsertfehler ist Fehler", "SPY" in r["ungeprueft"] and any("Nachlade-Upsert" in e for e in r["errors"]),
           f"{r['errors']}")


def block_intraday() -> None:
    zuruecksetzen()
    stub_supabase()
    sys.modules.pop("scripts.intraday_refresh", None)
    import scripts.intraday_refresh as ir
    # Jahreswechsel mit Feiertag (1.1. als Füllzeile → 0/0), Lücke (2.1. fehlt), Monatswechsel
    daten = ["2025-12-30", "2025-12-31", "2026-01-01", "2026-01-05", "2026-01-30", "2026-02-02"]
    ir.download_data = lambda ticker, period="5d": kursframe(daten)
    ir.KALENDER_FEHLER.clear()
    with redirect_stdout(io.StringIO()) as aus:
        ir.refresh_tickers(["SAP.DE"], "test")
    vergleiche("Intraday Kalendernummern über Lücke/Jahreswechsel", "SAP.DE", Speicher.upsert, set(daten),
               soll_daten=daten)
    null = [r for r in Speicher.upsert if r["date"] == "2026-01-01"]
    pruefe("Intraday 0-Werte werden geschrieben", null and (null[0].get("tdom"), null[0].get("tdoy")) == (0, 0),
           f"{null}")


def block_onboarding() -> None:
    import scripts.backfill_new_ticker as bn
    import shared.supabase_client as sbc
    daten = handelstage("SAP.DE", date(2019, 7, 1), date(2025, 9, 30))
    daten = [d for d in daten if d != "2025-08-14"] + ["2025-12-24"]     # Lücke + geschlossener Tag
    vorhanden = daten[:1100]                                             # > 1000: Seitenumbruch beim Lesen
    MARKE = (99, 999)                                                    # Bestandswerte, die bleiben müssen

    def lauf(upsert_fehler=False, fehler_bei=None, fehler_wenn=None):
        zuruecksetzen()
        stub_supabase()
        Speicher.db_daten["SAP.DE"] = [{"ticker": "SAP.DE", "date": d, "tdom": MARKE[0], "tdoy": MARKE[1]}
                                       for d in vorhanden]
        Speicher.upsert_fehler, Speicher.fehler_bei_anfrage = upsert_fehler, fehler_bei
        Speicher.fehler_wenn = fehler_wenn
        bn.get_client = lambda: _Client()
        bn.upsert_prices = sbc.upsert_prices                            # der ECHTE Schreibweg
        bn.upsert_tickers = lambda rows: None
        bn.download_data = lambda ticker, period="max": kursframe(daten)
        with redirect_stdout(io.StringIO()):
            return bn.backfill_ticker("SAP.DE")

    r = lauf()
    neu = [d for d in daten if d not in set(vorhanden)]
    vergleiche("Onboarding nur neue Zeilen mit Kalendernummern", "SAP.DE", Speicher.upsert, set(neu),
               soll_daten=daten)
    db = {z["date"]: z for z in Speicher.db_daten["SAP.DE"]}
    verloren = [d for d in vorhanden if (db[d].get("tdom"), db[d].get("tdoy")) != MARKE]
    pruefe("Onboarding Bestand behält seine Nummern (echter Transport)", not verloren,
           f"{len(verloren)} Bestandszeilen verändert, z. B. {verloren[:2]} → "
           f"{[(db[d].get('tdom'), db[d].get('tdoy')) for d in verloren[:2]]}")
    pruefe("Onboarding ab 1. Juli zählt ab Jahresbeginn",
           any(rec.get("tdoy", 0) > 120 for rec in Speicher.upsert if rec["date"].startswith("2025-07")))
    pruefe("Onboarding Erfolg", r.get("ok") is True and r.get("rows") == len(daten), f"{r}")
    r = lauf(upsert_fehler=True)
    pruefe("Onboarding Upsertfehler → ok=False", r.get("ok") is False and r.get("rows") == 0, f"{r}")
    r = lauf(fehler_bei=3)                                               # Teilfehler in einem späteren Chunk
    # Ein Chunk zu 500 Zeilen scheitert (Anfrage 3), alle übrigen sind bestätigt → genau 500 weniger.
    pruefe("Onboarding Teilfehler → ok=False, nur Bestätigtes gezählt",
           r.get("ok") is False and r.get("rows") == len(daten) - 500, f"{r} (Soll rows={len(daten) - 500})")
    # Codex P2 R2: Fehler in der ZWEITEN Gruppe DESSELBEN Chunks. Chunk 3 (Zeilen 1000–1499) zerfällt in den
    # Bestand (1000–1099, ohne Nummern) und die neuen Zeilen (1100–1499, mit Nummern); nur die zweite scheitert.
    # Die 100 bestätigten Bestandszeilen müssen mitgezählt werden — vorher: rows ohne den ganzen Chunk.
    erste_neue = daten[1100]
    r = lauf(fehler_wenn=lambda recs: any(x["date"] == erste_neue for x in recs))
    pruefe("Onboarding Teilfehler in einer Chunk-Gruppe zählt den bestätigten Teil",
           r.get("ok") is False and r.get("rows") == len(daten) - 400, f"{r} (Soll rows={len(daten) - 400})")

    import scripts.onboard_ticker as ob
    ob._run = lambda script, args: script != "backfill_new_ticker.py"
    ob._yahoo_has_data = lambda t: True
    alt = sys.argv
    sys.argv = ["onboard_ticker.py", "SAP.DE", "--skip-validate"]
    try:
        with redirect_stdout(io.StringIO()):
            rc = ob.main()
    finally:
        sys.argv = alt
    pruefe("Onboarding Aufrufer Exit 1 bei gescheitertem Backfill", rc == 1, f"Exit {rc}")


def block_lueckenfueller() -> None:
    import scripts.fix_missing_days as fm
    tage = handelstage("SAP.DE", date(2026, 3, 2), date(2026, 3, 31))
    fehlend = [tage[5], tage[6]]

    def lauf(upsert_fehler=False):
        zuruecksetzen()
        stub_supabase()
        Speicher.db_daten["SAP.DE"] = [{"date": d} for d in tage if d not in fehlend]
        Speicher.upsert_fehler = upsert_fehler
        yd = types.ModuleType("shared.yahoo_downloader")
        yd.download_data = lambda ticker, period="1mo": kursframe(tage)
        sys.modules["shared.yahoo_downloader"] = yd
        fm.get_client = lambda: _Client()
        import shared.supabase_client as sbc
        fm.upsert_prices = sbc.upsert_prices
        fm.get_db_dates = lambda client, t, a, b: {d for d in tage if d not in fehlend}
        fm.FEHLER.clear()
        alt = sys.argv
        sys.argv = ["fix_missing_days.py", "--ticker", "SAP.DE", "--year", "2026"]
        try:
            with redirect_stdout(io.StringIO()) as aus:
                rc = fm.main()
            return rc
        finally:
            sys.argv = alt

    rc = lauf()
    vergleiche("Lückenfüller Kalendernummern", "SAP.DE", Speicher.upsert, set(fehlend), soll_daten=fehlend)
    pruefe("Lückenfüller Exit 0", rc == 0, f"Exit {rc}")
    rc = lauf(upsert_fehler=True)
    pruefe("Lückenfüller Batchfehler → Exit 1", rc == 1, f"Exit {rc}")


def block_reparatur() -> None:
    import scripts.backfill_tdoy as bt
    tage = handelstage("SAP.DE", date(2026, 9, 1), date(2026, 9, 30))
    ref = referenz("SAP.DE", tage)

    def db(falsch: dict):
        Speicher.db_daten["SAP.DE"] = [{"date": d, "tdom": falsch.get(d, ref[d])[0], "tdoy": falsch.get(d, ref[d])[1]}
                                       for d in tage]

    def lauf(argv, falsch=None, treffer=1):
        zuruecksetzen()
        db(falsch or {tage[3]: (4, 174), tage[4]: (4, 174)})
        Speicher.update_treffer = treffer
        with redirect_stdout(io.StringIO()) as aus:
            rc = bt.main(argv, client=_Client())
        return rc

    rc = lauf(["--ticker", "SAP.DE"])
    pruefe("Reparatur Trockenlauf schreibt nichts", rc == 0 and not Speicher.update and not Speicher.upsert, f"{Speicher.update}")
    rc = lauf(["--ticker", "SAP.DE", "--von", "2026-09-01", "--bis", "2026-09-30", "--schreiben"])
    soll = {(tage[3], ref[tage[3]]), (tage[4], ref[tage[4]])}
    ist = {(f["date"], (u["tdom"], u["tdoy"])) for f, u in Speicher.update}
    pruefe("Reparatur schreibt genau die Abweichungen", rc == 0 and ist == soll, f"Exit {rc}, {ist}")
    pruefe("Reparatur nur tdom/tdoy", all(set(u) == {"tdom", "tdoy"} for _, u in Speicher.update), f"{Speicher.update[:2]}")
    # Vor 2001 mit BELEGTEM Kalender (NYSE 1999): nur die 2001-Grenze darf hier verweigern — bei XETRA
    # 1999 griff schon die Statusgrenze, und die 2001-Grenze blieb ungeprüft (eigener Mutationstest).
    zuruecksetzen()
    t99 = handelstage("SPY", date(1999, 3, 1), date(1999, 3, 31))
    r99 = referenz("SPY", t99)
    Speicher.db_daten["SPY"] = [{"date": d, "tdom": r99[d][0] + (1 if i == 2 else 0), "tdoy": r99[d][1]}
                                for i, d in enumerate(t99)]
    with redirect_stdout(io.StringIO()) as aus:
        rc = bt.main(["--ticker", "SPY", "--von", "1999-03-01", "--bis", "1999-03-31", "--schreiben"], client=_Client())
    pruefe("Reparatur vor 2001 verweigert", rc == 1 and not Speicher.update, f"Exit {rc}")
    rc = lauf(["--ticker", "SAP.DE", "--schreiben"])
    pruefe("Reparatur ohne Bereich verweigert", rc == 1 and not Speicher.update, f"Exit {rc}")
    rc = lauf(["--von", "2026-09-01", "--bis", "2026-09-30", "--schreiben"])
    pruefe("Reparatur ohne Ticker verweigert", rc == 1 and not Speicher.update, f"Exit {rc}")
    rc = lauf(["--ticker", "SAP.DE", "--von", "2026-09-01", "--bis", "2026-09-30", "--schreiben",
               "--max-aenderungen", "1"])
    pruefe("Reparatur Mengengrenze verweigert", rc == 1 and not Speicher.update, f"Exit {rc}")
    rc = lauf(["--ticker", "SAP.DE", "--von", "2026-09-01", "--bis", "2026-09-30", "--schreiben"], treffer=0)
    pruefe("Reparatur ohne Bestätigung → Exit 1", rc == 1, f"Exit {rc}")
    # Kalender ungeprüft: HKEX 2010
    zuruecksetzen()
    Speicher.db_daten["^HSI"] = [{"date": "2010-03-01", "tdom": 9, "tdoy": 9}]
    with redirect_stdout(io.StringIO()) as aus:
        rc = bt.main(["--ticker", "^HSI", "--von", "2010-03-01", "--bis", "2010-03-31", "--schreiben"], client=_Client())
    pruefe("Reparatur ungeprüfter Kalender verweigert", rc == 1 and not Speicher.update, f"Exit {rc}")


# Bekannte Schreiber von prices (Python). Jede andere Datei mit einem prices-Schreibaufruf ist ein Befund.
SCHREIBER_MIT_NUMMERN = {"scripts/nightly_refresh.py", "scripts/intraday_refresh.py", "scripts/backfill_new_ticker.py",
                         "scripts/fix_missing_days.py", "scripts/backfill_tdoy.py"}
SCHREIBER_OHNE_NUMMERN = {"scripts/backfill_ohlc.py", "scripts/backfill_log_return.py", "scripts/fix_ohlc_adjustment.py",
                          "scripts/fix_log_returns_may2026.py"}   # einmalige log_return-Korrektur ^GDAXI
SCHREIB_MUSTER = re.compile(r"upsert_prices\s*\(|table\(\s*[\"']prices[\"']\s*\)\s*\.\s*(upsert|update|insert)\s*\(")


def block_bestand() -> None:
    gefunden = set()
    for wurzel, verz, dateien in os.walk(WURZEL):
        verz[:] = [v for v in verz if v not in (".git", ".claude", "node_modules", "__pycache__", "lightning_logs")]
        for f in dateien:
            if not f.endswith(".py"):
                continue
            rel = os.path.relpath(os.path.join(wurzel, f), WURZEL).replace(os.sep, "/")
            if rel.startswith(("scripts/verify_", "scripts/research/")) or rel == "shared/supabase_client.py":
                continue
            with open(os.path.join(wurzel, f), encoding="utf-8", errors="replace") as fh:
                if SCHREIB_MUSTER.search(fh.read()):
                    gefunden.add(rel)
    unbekannt = gefunden - SCHREIBER_MIT_NUMMERN - SCHREIBER_OHNE_NUMMERN
    pruefe("Bestand kein unbekannter prices-Schreiber", not unbekannt, f"{sorted(unbekannt)}")
    pruefe("Bestand Bulk-Lader entfernt", not os.path.exists(os.path.join(WURZEL, "bulk_load_supabase.py")))
    for rel in sorted(SCHREIBER_OHNE_NUMMERN):
        baum = ast.parse(open(os.path.join(WURZEL, rel), encoding="utf-8").read())
        literale = {n.value for n in ast.walk(baum) if isinstance(n, ast.Constant) and isinstance(n.value, str)}
        pruefe(f"Bestand {rel} sendet keine Nummern", not ({"tdom", "tdoy"} & literale))


def main() -> int:
    absturzwache_an()
    for name, block in (("Nightly", block_nightly), ("Lücke", block_luecke), ("Intraday", block_intraday),
                        ("Onboarding", block_onboarding), ("Lückenfüller", block_lueckenfueller),
                        ("Reparatur", block_reparatur), ("Bestand", block_bestand)):
        try:
            block()
        except Exception as e:  # eine Ausnahme ist nie ein Nachweis
            FEHLER.append(f"[Ausnahme] Block {name}: {type(e).__name__}: {str(e)[:160]}")
    absturzwache_aus()
    for a in ABSTUERZE[:10]:
        FEHLER.append(f"[Ausnahme] {a}")
    print(f"verify_schreiber_nummern: {ZAEHLER['n'] - len(FEHLER)}/{ZAEHLER['n']} Prüfungen bestanden")
    for f in FEHLER:
        print("  FEHL", f)
    print(f"PROBE-ENDE {ZAEHLER['n']} Pruefungen")
    return 1 if FEHLER else 0


if __name__ == "__main__":
    sys.exit(main())
