#!/usr/bin/env python3
"""
verify_kursreihe_basis.py — Wächter für die basisgleiche Kursreihe der Morgen-Mail (shared/daily_report.py).

WARUM (2026-10-16, Folgeposten zu Paket A): `fetch_daily_close_history` lieferte die gespeicherten Schlusskurse.
Wechselt die Kursbasis innerhalb der Reihe (ETHA 30.09.2026: 20,28 → 60,36 nach Reverse-Split, gespeicherter
`log_return` −0,79 %), zeigten Tagesänderung, Sektor-Monatsmittel, RSI und LBR einen Sprung von +198 %, den es nicht
gab. Jetzt beginnt die Reihe hinter dem jüngsten Widerspruch zwischen Kursen und `log_return` (Abweichung >
basisabweichung.SCHWELLE); die Werte bleiben die echten Kurse, nichts wird umgerechnet (Codex-Review 16.10.: eine
Korrektur mit log_return übernähme auch einen falschen Return).

Geprüft (gegen einen Attrappen-Client, der die Zeilen so liefert wie PostgREST):
  1. Basiswechsel: Reihe beginnt am Wechseltag, Werte = echte Kurse; Abfrage mit Gesamtordnung.
  2. Falscher log_return (100 → 101, lr 0,2): Reihe beginnt bei 101, keine erfundene Rendite.
  3. Unterhalb der Schwelle (Forex-Doppelspanne, Dividende, 0,049) bleibt alles, 0,051 schneidet.
  4. Zwei Widersprüche: geschnitten wird am jüngeren.
  5. Kurslose Zeile: über sie hinweg wird nicht verglichen; am Ende zählt der letzte gültige Kurs; ungültige Typen.
  6. Leser: Tagesänderung (`_signal_row_from_series`) und Sektor-Monatsmittel.
Exit 0 = alles grün, 1 = Befund.
"""
from __future__ import annotations

import math
import sys
import types
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

FEHLER: list[str] = []
ORDNUNG: list[str] = []


def pruef(name: str, ok: bool, info="") -> None:
    print(f"  {'ok  ' if ok else 'FEHL'} {name}" + (f"  ->  {info}" if info != "" else ""))
    if not ok:
        FEHLER.append(name)


class _Abfrage:
    def __init__(self, zeilen):
        self._z = zeilen
        self._von, self._bis = 0, None

    def select(self, *_a, **_k): return self
    def in_(self, *_a, **_k): return self
    def gte(self, *_a, **_k): return self
    def order(self, spalte, *_a, **_k):
        ORDNUNG.append(spalte)
        return self

    def range(self, a, b):
        self._von, self._bis = a, b
        return self

    def execute(self):
        return types.SimpleNamespace(data=self._z[self._von:self._bis + 1])


class _Client:
    def __init__(self, zeilen):
        self.zeilen = zeilen

    def table(self, _name):
        return _Abfrage(self.zeilen)


def _lade(zeilen):
    import shared.supabase_client as sc
    sc.get_client = lambda: _Client(zeilen)
    import shared.daily_report as dr
    return dr.fetch_daily_close_history(["X"], lookback_days=10_000), dr


def _z(d, c, lr, t="X"):
    return {"ticker": t, "date": d, "close": c, "log_return": lr}


def nah(a, b, tol=1e-9):
    return a is not None and b is not None and abs(a - b) <= tol * max(1.0, abs(b))


def daten(s):
    return list(s["X"].index.strftime("%Y-%m-%d")) if "X" in s else []


def werte(s):
    return [float(v) for v in s["X"].values] if "X" in s else []


print("== 1. Basiswechsel (ETHA-Muster)")
zeilen = [_z("2026-09-28", 20.00, 0.0), _z("2026-09-29", 20.28, math.log(20.28 / 20.00)),
          _z("2026-09-30", 60.36, math.log(0.9921)), _z("2026-10-01", 61.00, math.log(61.00 / 60.36))]
s, dr = _lade(zeilen)
pruef("Reihe beginnt am Wechseltag", daten(s) == ["2026-09-30", "2026-10-01"], daten(s))
pruef("Werte = echte Kurse", werte(s) == [60.36, 61.00], werte(s))
pruef("Abfrage sortiert nach date UND ticker (Gesamtordnung für die Seitenabfrage)",
      ORDNUNG[:2] == ["date", "ticker"], ORDNUNG[:2])

print("== 2. Falscher log_return")
s, _ = _lade([_z("2026-01-02", 100.0, 0.0), _z("2026-01-05", 101.0, 0.2)])
pruef("100 → 101 bei lr 0,2: Reihe beginnt bei 101 (keine +22 %)", werte(s) == [101.0], werte(s))

print("== 3. Schwelle")
s, _ = _lade([_z("2026-10-14", 0.6978, 0.0), _z("2026-10-15", 0.6922, math.log(0.6922 / 0.6978)),
              _z("2026-10-16", 0.6964, -0.00208149)])
pruef("Forex-Doppelspanne (0,8 %) bleibt ganz", werte(s) == [0.6978, 0.6922, 0.6964], werte(s))
s, _ = _lade([_z("2026-05-01", 100.0, 0.0), _z("2026-05-04", 99.0, math.log(0.99) + 0.004)])
pruef("Dividendenschritt bleibt", werte(s) == [100.0, 99.0], werte(s))
for abw, schnitt in ((0.049, False), (0.051, True)):
    s, _ = _lade([_z("2026-06-01", 100.0, 0.0), _z("2026-06-02", 110.0, math.log(1.1) - abw)])
    pruef(f"Abweichung {abw:.3f} → {'Schnitt' if schnitt else 'kein Schnitt'}",
          werte(s) == ([110.0] if schnitt else [100.0, 110.0]), werte(s))

print("== 4. Zwei Widersprüche")
s, _ = _lade([_z("2026-07-01", 10.0, 0.0), _z("2026-07-02", 30.0, 0.0), _z("2026-07-03", 31.0, math.log(31 / 30)),
              _z("2026-07-06", 93.0, 0.0), _z("2026-07-07", 94.0, math.log(94 / 93))])
pruef("geschnitten am jüngeren (06.07.)", daten(s) == ["2026-07-06", "2026-07-07"], daten(s))

print("== 5. Kurslose Zeilen, ungültige Typen")
s, _ = _lade([_z("2026-02-02", 100.0, 0.0), _z("2026-02-03", None, math.log(1.10)), _z("2026-02-04", 300.0, 0.05)])
pruef("über eine kurslose Zeile wird nicht verglichen, sie erscheint nicht",
      daten(s) == ["2026-02-02", "2026-02-04"], daten(s))
s, _ = _lade([_z("2026-03-02", 50.0, 0.0), _z("2026-03-03", 51.0, math.log(1.02)), _z("2026-03-04", None, 0.01)])
pruef("am Ende zählt der letzte gültige Kurs", werte(s) == [50.0, 51.0], werte(s))
s, _ = _lade([_z("2026-04-01", 10.0, 0.0), _z("2026-04-02", True, 0.0), _z("2026-04-03", "x", 0.0),
              _z("2026-04-06", 12.0, float("nan")), _z("2026-04-07", 0.0, 0.0), _z("2026-04-08", 13.0, "y")])
pruef("bool, Text, 0, NaN sind keine Kurse/Returns", daten(s) == ["2026-04-01", "2026-04-06", "2026-04-08"], daten(s))

print("== 6. Leser: Tagesänderung und Sektor-Monatsmittel")
import shared.newsletter_indicators as ni                               # noqa: E402
ni.compute_ticker_signals = lambda series, last_bar=None: {}
s, dr = _lade(zeilen)
row = dr._signal_row_from_series("X", s["X"], with_mw=False)
pruef("change_pct am Folgetag = (61,00/60,36 − 1)·100",
      row is not None and row["change_pct"] == round((61 / 60.36 - 1) * 100, 2), row and row["change_pct"])
pruef("price_close = echter Schluss", row is not None and row["price_close"] == 61.0, row and row["price_close"])
s, dr = _lade([_z("2026-01-02", 100.0, 0.0), _z("2026-01-05", 101.0, 0.2)])
row = dr._signal_row_from_series("X", s["X"], with_mw=False)
pruef("Gegenbeispiel: keine Tagesänderung statt +22 %", row is not None and row["change_pct"] is None,
      row and row["change_pct"])
mz = [_z("2025-12-31", 10.0, 0.0), _z("2026-01-30", 11.0, math.log(1.1)), _z("2026-02-27", 33.0, 0.0),
      _z("2026-03-31", 36.3, math.log(1.1))]
import shared.sector_rotation as sr                                    # noqa: E402
sr.SECTOR_ETFS = {"X": "Test"}
import shared.supabase_client as sc                                    # noqa: E402
sc.get_client = lambda: _Client(mz)
mon = dr._sector_monthly_avg_returns(lookback_days=10_000).get("X", {})
pruef("Monatsmittel: Februar (Basiswechsel) fehlt, März +10 %, kein +200 %", mon == {3: 10.0}, mon)

print()
if FEHLER:
    print(f"[FEHLER] {len(FEHLER)} Befund(e): " + "; ".join(FEHLER))
    sys.exit(1)
print("[OK] alle Prüfungen grün")
