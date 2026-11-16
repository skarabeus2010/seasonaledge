"""
scripts/verify_strategie_renditen.py — Wächter: Strategierenditen mit Platzhalterkursen
=========================================================================================
Anlass (Nightly 2026-11-15, rot): Yahoo liefert für ^MDAXI am 1997-01-06 eine Zeile mit Open=High=Low=Close=0.
`calc_strategy_returns` teilte durch 0 → ±inf → der Upsert von tdom_stats/tdoy_stats scheiterte („Out of range float
values are not JSON compliant: inf“). Bis 2026-11-15 wurde dieser Fehler verschluckt, die Statistik blieb still alt.
Zweiter, stiller Defekt derselben Zeile: der VORTAG bekam eine Rendite von −100 % (Kurs gegen 0) — endlich, also
unsichtbar für jede inf-/NaN-Prüfung.

Geprüft (echte Funktionen aus shared/, synthetische Reihe mit einer Nullzeile und einem NaN-Kurs):
  1. keine Strategie liefert ±inf
  2. keine Rendite ≤ −100 % (die erfundene Vortagsrendite)
  3. die Renditen, an denen ein Platzhalter beteiligt ist, sind NaN — alle übrigen unverändert gegen eine Handrechnung
  4. build_tdom_stats / build_tdoy_stats liefern nur endliche Werte, die Datensätze sind strikt JSON-serialisierbar
     (json.dumps(allow_nan=False), wie der Supabase-Client)
  5. Mutation: derselbe Lauf mit der alten Funktion (Platzhalterbehandlung entfernt) MUSS durchfallen — sonst trifft
     der Testfall den Fehler nicht.

Aufruf: py -3.14 scripts/verify_strategie_renditen.py   (Exit 0 = bestanden)
"""

import json
import math
import sys
import types
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from shared import tdom_analysis as _tdom  # noqa: E402

STRATEGIEN = ["open_to_close", "open_to_next_open", "open_to_next_close", "close_to_next_close"]
MARKER = "    # Ein Kurs ≤ 0 oder nicht endlich ist kein Kurs"


def _reihe() -> pd.DataFrame:
    """Drei Monate Handelstage, Kurse steigen gleichmäßig; Platzhalter: eine Nullzeile + ein NaN-Schluss."""
    idx = pd.bdate_range("1997-01-01", "1997-03-31")
    n = len(idx)
    opn = 100.0 + np.arange(n, dtype=float)
    cls = opn + 0.5
    df = pd.DataFrame({"Open": opn, "High": cls + 1, "Low": opn - 1, "Close": cls}, index=idx)
    df.index.name = "Date"
    df.loc[pd.Timestamp("1997-01-06"), ["Open", "High", "Low", "Close"]] = 0.0     # wie Yahoo ^MDAXI
    df.loc[pd.Timestamp("1997-02-12"), "Close"] = np.nan
    return df


def _erwartet(df: pd.DataFrame, strategie: str) -> pd.Series:
    """Unabhängige Handrechnung: Kurs gültig nur, wenn endlich und > 0."""
    o = df["Open"].where(np.isfinite(df["Open"]) & (df["Open"] > 0))
    c = df["Close"].where(np.isfinite(df["Close"]) & (df["Close"] > 0))
    if strategie == "open_to_close":
        return (c - o) / o * 100
    if strategie == "open_to_next_open":
        return (o.shift(-1) - o) / o * 100
    if strategie == "open_to_next_close":
        return (c.shift(-1) - o) / o * 100
    return (c.shift(-1) - c) / c * 100


def pruefe(modul) -> list[str]:
    fehler: list[str] = []
    df = _reihe()
    for s in STRATEGIEN:
        r = modul.calc_strategy_returns(df, s)["strat_return"].astype(float)
        if np.isinf(r).any():
            fehler.append(f"{s}: ±inf in {int(np.isinf(r).sum())} Zeilen")
        if (r <= -100).any():
            fehler.append(f"{s}: Rendite ≤ −100 % (erfundene Vortagsrendite) in {int((r <= -100).sum())} Zeilen")
        soll = _erwartet(df, s)
        beide_nan = r.isna() & soll.isna()
        gleich = np.isclose(r.fillna(0), soll.fillna(0), rtol=0, atol=1e-12) & (r.isna() == soll.isna())
        if not (gleich | beide_nan).all():
            fehler.append(f"{s}: weicht in {int((~(gleich | beide_nan)).sum())} Zeilen von der Handrechnung ab")
        # höchstens 5 verworfen: letzte Zeile (kein Folgetag) + je Platzhalter er selbst und sein Vortag
        if r.notna().sum() < len(r) - 5:
            fehler.append(f"{s}: zu viele Zeilen verworfen ({int(r.isna().sum())})")

        # Statistiken wie im Nightly (cache_manager baut daraus die Datensätze)
        from shared.tdoy_analysis import build_tdoy_stats
        for art, st in (("tdom", modul.build_tdom_stats(df, strategy=s)), ("tdoy", build_tdoy_stats(df, strategy=s))):
            werte = st[["avg_return", "median_return", "win_rate", "max_return", "min_return"]].to_numpy(dtype=float)
            if not np.isfinite(werte).all():
                fehler.append(f"{art}_stats {s}: nicht endliche Werte")
            datensaetze = [{k: (None if (isinstance(v, float) and math.isnan(v)) else float(v))
                            for k, v in zeile.items()} for _, zeile in st.reset_index().iterrows()]
            try:
                json.dumps(datensaetze, allow_nan=False)
            except ValueError as e:
                fehler.append(f"{art}_stats {s}: nicht JSON-konform ({e})")
    return fehler


def _alte_fassung():
    """shared/tdom_analysis.py ohne die Platzhalterbehandlung (Stand vor 2026-11-16) als eigenes Modul."""
    quelle = (ROOT / "shared" / "tdom_analysis.py").read_text(encoding="utf-8")
    start = quelle.find(MARKER)
    ende = quelle.find("    # shift(-1) holt", start)
    if start < 0 or ende < 0:
        return None
    m = types.ModuleType("tdom_alt")
    exec(compile(quelle[:start] + quelle[ende:], "tdom_alt", "exec"), m.__dict__)
    return m


def main() -> int:
    fehler = pruefe(_tdom)
    for f in fehler:
        print("  FEHLER", f)

    alt = _alte_fassung()
    if alt is None:
        fehler.append("Mutation: Anker der Platzhalterbehandlung nicht gefunden (ungültig)")
        print("  FEHLER Mutation: Anker nicht gefunden")
    else:
        alt_fehler = pruefe(alt)
        if not alt_fehler:
            fehler.append("Mutation: alte Fassung besteht — der Testfall trifft den Fehler nicht")
            print("  FEHLER Mutation nicht gefangen")
        else:
            print(f"  ok Mutation gefangen ({len(alt_fehler)} Befunde, z. B. {alt_fehler[0]})")

    print("verify_strategie_renditen:", "BESTANDEN" if not fehler else f"DURCHGEFALLEN ({len(fehler)})")
    return 0 if not fehler else 1


if __name__ == "__main__":
    sys.exit(main())
