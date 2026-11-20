"""
Wächter: vorübergehende Supabase-Fehler werden wiederholt — und nur diese (Nightly rot an 10 von 15 Abenden, 2026-11).

Prüft die ECHTEN Funktionen `shared.stress_score.lade_kurse`, `shared.supabase_client._upsert_wiederholt`,
`shared.tdom_analysis.calc_strategy_returns` gegen eine zustandsbehaftete Attrappe. Die Fehler sind die echten Klassen
aus den Logs: `postgrest.exceptions.APIError` mit Code 57014 und `httpx.RemoteProtocolError` (HTTP/2-GOAWAY,
„ConnectionTerminated … last_stream_id:19999").

Fälle (Codex-Testplan, docs/review_prompts/2026-11-20_nightly_rot_diagnose_antwort.md):
  1  57014 bei der Zählung, dann Erfolg → vollständige Reihe
  2  57014 auf Seite 2 → vollständiger Neustart, keine Dubletten
  3  GOAWAY auf Client A (dauerhaft tot) → Factory mit force_new=True, Client B liefert
  4  GOAWAY ohne Factory → LadeFehler, A nur einmal benutzt
  5  42501 / ValueError → genau ein Versuch
  6  57014 in jedem Versuch → genau 3 Versuche, dann LadeFehler
  7  Zählung falsch → LadeFehler;  Zählung 0 + leer → zulässig
  8  1000 / 1001 / 2000 Zeilen → vollständig (Keyset-Seitenende)
  9  Datum rückläufig / doppelt an der Seitengrenze → LadeFehler
 10  Upsert: GOAWAY → zweiter Versuch mit neuem Client; 42501 → sofort weiter
 11  calc_strategy_returns: Kurs 0 / NaN → keine unendliche Rendite, NaN statt −100 %
 12  Nightly reicht eine Factory durch (Quelltext)
Exit 1 bei einem Fehler.
"""
from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("SUPABASE_URL", "http://attrappe.invalid")
os.environ.setdefault("SUPABASE_KEY", "attrappe")

import httpx  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from postgrest.exceptions import APIError  # noqa: E402

from shared import db_wiederholung as dw  # noqa: E402
from shared import stress_score as ss  # noqa: E402

dw.warte = lambda v: None       # kein echtes Warten im Test

FEHLER = []


def pruef(name, ok, detail=""):
    print(f"  [{'OK ' if ok else 'FEHLER'}] {name}{'' if ok else '  — ' + str(detail)}")
    if not ok:
        FEHLER.append(name)


def timeout():
    return APIError({"message": "canceling statement due to statement timeout", "code": "57014", "hint": None,
                     "details": None})


def goaway():
    return httpx.RemoteProtocolError("<ConnectionTerminated error_code:0, last_stream_id:19999, additional_data:None>")


def rechte():
    return APIError({"message": "permission denied for table prices", "code": "42501", "hint": None, "details": None})


# ── Attrappe: prices mit count, eq, gt, order, limit ──
class Antwort:
    def __init__(self, data, count=None):
        self.data, self.count = data, count


class Abfrage:
    def __init__(self, cl):
        self.cl, self.f_gt, self.mit_count, self.lim = cl, None, False, None

    def select(self, *_a, count=None):
        self.mit_count = count == "exact"
        return self

    def eq(self, *_a):
        return self

    def gt(self, _k, v):
        self.f_gt = v
        return self

    def order(self, *_a, **_k):
        return self

    def limit(self, n):
        self.lim = n
        return self

    def range(self, *_a):
        raise AssertionError("Offset-Paginierung benutzt (range) — Keyset erwartet")

    def execute(self):
        return self.cl.ausfuehren(self)


class Client:
    def __init__(self, zeilen, name="A", fehler=None, zaehlung=None, tot=False):
        self.zeilen, self.name, self.fehler, self.tot = zeilen, name, list(fehler or []), tot
        self.zaehlung = zaehlung
        self.aufrufe = 0

    def table(self, _t):
        return Abfrage(self)

    def ausfuehren(self, q):
        self.aufrufe += 1
        if self.tot:
            raise goaway()
        if self.fehler:
            art = self.fehler.pop(0)
            if art is not None:
                raise art()
        if q.mit_count:
            return Antwort([], len(self.zeilen) if self.zaehlung is None else self.zaehlung)
        z = [r for r in self.zeilen if q.f_gt is None or r["date"] > q.f_gt]
        return Antwort([dict(r) for r in z[:q.lim]], None)


def reihe(n):
    start = pd.Timestamp("1950-01-02")
    return [{"date": (start + pd.Timedelta(days=i)).strftime("%Y-%m-%d"), "close": 100.0 + i} for i in range(n)]


def lade(cl, factory=None):
    return ss.lade_kurse("T", cl, client_factory=factory, log=lambda m: None)


def sicher(cl, factory=None):
    """Wie lade, aber eine Ausnahme wird zum Ergebnis ([], …) — die Prüfung meldet sich dann mit Namen statt Absturz."""
    try:
        return lade(cl, factory)
    except Exception as e:  # noqa: BLE001
        return [f"[Ausnahme] {type(e).__name__}"], [], {}


def wirft(fn, klasse):
    try:
        fn()
        return False
    except klasse:
        return True


def main():
    z = reihe(2500)

    print("Kurslader")
    cl = Client(z, fehler=[timeout])
    d, c, _ = sicher(cl)
    pruef("1 57014 bei der Zählung → vollständig", len(d) == 2500 and d[-1] == z[-1]["date"], len(d))

    # Aufrufe: count, s1, s2(Fehler) → neuer Versuch: count, s1, s2, s3
    cl = Client(z, fehler=[None, None, timeout])
    d, c, _ = sicher(cl)
    pruef("2 57014 auf Seite 2 → vollständig, keine Dubletten", len(d) == 2500 and len(set(d)) == 2500, len(d))

    a, b = Client(z, "A", tot=True), Client(z, "B")
    rufe = []

    def factory(force_new=False):
        rufe.append(force_new)
        return b
    d, c, _ = sicher(a, factory)
    pruef("3 GOAWAY auf A → Factory(force_new=True), B liefert vollständig",
          rufe == [True] and len(d) == 2500 and a.aufrufe == 1, (rufe, len(d), a.aufrufe))

    a = Client(z, "A", tot=True)
    pruef("4 GOAWAY ohne Factory → LadeFehler", wirft(lambda: lade(a), ss.LadeFehler) and a.aufrufe == 1, a.aufrufe)

    cl = Client(z, fehler=[rechte])
    pruef("5a 42501 → genau ein Versuch, LadeFehler", wirft(lambda: lade(cl), ss.LadeFehler) and cl.aufrufe == 1,
          cl.aufrufe)
    cl = Client(z, fehler=[lambda: ValueError("kaputt")])
    pruef("5b ValueError → genau ein Versuch", wirft(lambda: lade(cl), ss.LadeFehler) and cl.aufrufe == 1, cl.aufrufe)

    cl = Client(z, fehler=[timeout] * 10)
    pruef("6 57014 dauerhaft → 3 Versuche, dann LadeFehler",
          wirft(lambda: lade(cl), ss.LadeFehler) and cl.aufrufe == 3, cl.aufrufe)

    pruef("7a Zählung zu hoch → LadeFehler", wirft(lambda: lade(Client(z, zaehlung=2501)), ss.LadeFehler))
    pruef("7b Zählung zu niedrig → LadeFehler", wirft(lambda: lade(Client(z, zaehlung=2499)), ss.LadeFehler))
    d, _, _ = sicher(Client([]))
    pruef("7c Zählung 0 + leer → zulässig", d == [], d)

    for n in (1000, 1001, 2000):
        d, _, _ = sicher(Client(reihe(n)))
        pruef(f"8 {n} Zeilen → vollständig", len(d) == n, len(d))

    kaputt = reihe(1500)
    kaputt[1000] = dict(kaputt[999])          # Dublette genau an der Seitengrenze
    cl = Client(kaputt)
    pruef("9a doppeltes Datum an der Seitengrenze → LadeFehler", wirft(lambda: lade(cl), ss.LadeFehler))
    rueck = reihe(10)
    rueck[5], rueck[6] = rueck[6], rueck[5]
    pruef("9b rückläufiges Datum → LadeFehler", wirft(lambda: lade(Client(rueck)), ss.LadeFehler))

    print("Klassifikation")
    pruef("13a httpx.ReadTimeout → vorübergehend + Transport",
          dw.voruebergehend(httpx.ReadTimeout("t")) and dw.transportfehler(httpx.ReadTimeout("t")))
    pruef("13b httpx.ReadError (NetworkError) → vorübergehend + Transport",
          dw.voruebergehend(httpx.ReadError("r")) and dw.transportfehler(httpx.ReadError("r")))
    try:
        try:
            raise goaway()
        except Exception as inner:
            raise RuntimeError("Hülle") from inner
    except RuntimeError as e:
        pruef("13c GOAWAY als __cause__ einer Hülle → erkannt", dw.transportfehler(e))
    try:
        try:
            raise timeout()
        except Exception:
            raise RuntimeError("Hülle ohne from")
    except RuntimeError as e:
        pruef("13d 57014 als __context__ → erkannt", dw.voruebergehend(e) and not dw.transportfehler(e))
    pruef("13e ValueError / 42501 → nicht vorübergehend",
          not dw.voruebergehend(ValueError("x")) and not dw.voruebergehend(rechte()))
    e = timeout()
    e.add_note("stress_score.lade_kurse T: count")
    pruef("13f Log nennt die Ladestufe", "count" in dw.beschreibe(e), dw.beschreibe(e))

    print("Saison-Score-Pfad (echter Aufruf wie im Nightly)")
    from shared import saison_score_betrieb as sb
    a, b = Client(z, "A", tot=True), Client(z, "B")
    neu = []

    def fac(force_new=False):
        neu.append(force_new)
        return b if force_new else a
    try:
        r = sb.fuer_ticker("T", client_factory=fac)
        ok = isinstance(r, dict) and "status" in r and r.get("kurse_bis") == z[-1]["date"]
    except Exception as ex:  # noqa: BLE001
        ok, r = False, ex
    pruef("14a fuer_ticker(client_factory=…) erholt sich von GOAWAY", ok and neu == [False, True], (neu, r))

    def fac_tot(force_new=False):
        return Client(z, "X", tot=True)
    pruef("14b dauerhaft GOAWAY → LadeFehler erreicht den Aufrufer (Nightly zählt ihn)",
          wirft(lambda: sb.fuer_ticker("T", client_factory=fac_tot), ss.LadeFehler))

    print("Upsert")
    import shared.supabase_client as sc
    ziel = []

    class UpClient:
        def __init__(self, fehler):
            self.fehler = fehler

        def table(self, t):
            me = self

            class Q:
                def upsert(self, zeilen, on_conflict):
                    self.z = zeilen
                    return self

                def execute(self):
                    if me.fehler:
                        raise me.fehler()
                    ziel.append(len(self.z))
                    return Antwort([])
            return Q()

    alt = sc.get_client
    try:
        reihenfolge = [UpClient(goaway), UpClient(None)]
        neu_flags = []

        def gc(force_new=False):
            neu_flags.append(force_new)
            return reihenfolge.pop(0) if force_new or len(neu_flags) == 1 else reihenfolge[0]
        sc.get_client = gc
        sc._upsert_wiederholt("tdom_stats", [{"x": 1}, {"x": 2}], "a")
        pruef("10a GOAWAY beim Upsert → zweiter Versuch mit force_new=True", neu_flags == [False, True] and ziel == [2],
              (neu_flags, ziel))

        aufrufe = []

        def gc2(force_new=False):
            aufrufe.append(force_new)
            return UpClient(rechte)
        sc.get_client = gc2
        pruef("10b 42501 beim Upsert → sofort weiter, ein Versuch",
              wirft(lambda: sc._upsert_wiederholt("tdom_stats", [{}], "a"), APIError) and aufrufe == [False], aufrufe)
        # Die ÖFFENTLICHEN Schreiber (Codex Code-R2: ein Rückbau auf Upsert ohne Wiederholung blieb sonst grün)
        for name, fn, n, fehler_bei in (("upsert_monthly_stats", sc.upsert_monthly_stats, 12, 1),
                                        ("upsert_tdoy_stats", sc.upsert_tdoy_stats, 300, 1),
                                        ("upsert_tdom_stats", sc.upsert_tdom_stats, 1200, 2)):
            ziel.clear()
            stand = {"aufruf": 0, "neu": []}

            class Zaehl(UpClient):
                def table(self, t):
                    q = UpClient.table(self, t)
                    stand["aufruf"] += 1
                    if stand["aufruf"] == fehler_bei:      # genau dieser Batch scheitert einmal mit GOAWAY
                        self.fehler = goaway
                    else:
                        self.fehler = None
                    return q

            def gc3(force_new=False):
                stand["neu"].append(force_new)
                return Zaehl(None)
            sc.get_client = gc3
            try:
                fn([{"i": i} for i in range(n)])
                ok = sum(ziel) == n and True in stand["neu"]
            except Exception as ex:  # noqa: BLE001
                ok, ziel[:] = False, [repr(ex)[:80]]
            pruef(f"10c {name}: GOAWAY im Batch {fehler_bei} → wiederholt mit neuem Client, alle {n} Zeilen geschrieben",
                  ok, (ziel, stand))
    finally:
        sc.get_client = alt

    print("TDOM/TDOY-Renditen")
    from shared.tdom_analysis import calc_strategy_returns
    df = pd.DataFrame({"Open": [100.0, 0.0, 110.0, np.nan, 120.0], "Close": [101.0, 0.0, 111.0, 115.0, 0.0]},
                      index=pd.date_range("2026-01-05", periods=5))
    for strat in ("open_to_close", "open_to_next_open", "open_to_next_close", "close_to_next_close"):
        r = calc_strategy_returns(df, strat)["strat_return"]
        pruef(f"11 {strat}: keine unendliche Rendite", not np.isinf(r).any(), list(r))
    r = calc_strategy_returns(df, "open_to_next_open")["strat_return"].tolist()
    pruef("11 open_to_next_open: Einstieg 0 → NaN, Ausstieg 0 → NaN, gültige Werte richtig",
          math.isnan(r[0]) and math.isnan(r[1]) and math.isnan(r[2]) and math.isnan(r[3]) and math.isnan(r[4]), r)
    r = calc_strategy_returns(df, "open_to_close")["strat_return"].tolist()
    pruef("11 open_to_close: 100→101 = +1 %, Schluss 0 → NaN statt −100 %",
          abs(r[0] - 1.0) < 1e-12 and math.isnan(r[4]) and abs(r[2] - 100 / 110) < 1e-12, r)

    print("Nightly")
    q = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "nightly_refresh.py"), encoding="utf-8").read()
    pruef("12 Nightly reicht client_factory an den Saison-Score", "fuer_ticker(ticker, client_factory=_get_client)" in q)

    print(f"\n{len(FEHLER)} Fehler" if FEHLER else "\nAlle Prüfungen bestanden")
    return 1 if FEHLER else 0


if __name__ == "__main__":
    sys.exit(main())
