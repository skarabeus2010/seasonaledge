#!/usr/bin/env python3
"""verify_kursmuster.py — Smash Day der Morgen-Mail (shared/kursmuster.py).

1. Einzelfälle mit Sollwert: Kauf/Verkauf/kein Muster, Grenzfall C = L_{t−1}, ungültige Kerzen, Basisbruch, Universum,
   falsche Session, Lücke zwischen den Kerzen.
2. Zwilling: auf zufälligen Kerzenreihen erkennt die Mail an jedem gültigen Tagespaar dasselbe Muster wie die Studie
   (scripts/research/williams_muster.py: muster_roh + Gültigkeit + Glied).
Exit: 0 grün, 1 rot, 3 Absturz.
"""
from __future__ import annotations

import math
import sys
import traceback
from datetime import date, timedelta
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
FEHLER: list[str] = []


def pruef(name, ok, detail=""):
    print(("  ok   " if ok else "  FEHL ") + name + ("" if ok else f"  ->  {detail}"))
    if not ok:
        FEHLER.append(name)


def k(d, o, h, l, c, v=1000, lr=None, vor=None):
    if lr is None:
        lr = math.log(c / vor) if vor else 0.0
    return {"date": d, "open": o, "high": h, "low": l, "close": c, "volume": v, "log_return": lr}


def main() -> int:
    import numpy as np
    from shared import kursmuster as K
    from scripts.research import williams_muster as W

    print("== Einzelfälle")
    a = k("2026-10-15", 100, 102, 99, 101)
    pruef("Kauf-Setup: Schluss 98,5 unter Vortagestief 99", K.smash_day(a, k("2026-10-16", 100.5, 101, 98, 98.5, vor=101)) == K.KAUF)
    pruef("Verkauf-Setup: Schluss 102,5 über Vortageshoch 102", K.smash_day(a, k("2026-10-16", 101, 103, 100.5, 102.5, vor=101)) == K.VERKAUF)
    pruef("innerhalb der Vortagesspanne: kein Muster", K.smash_day(a, k("2026-10-16", 101, 101.8, 99.5, 100, vor=101)) is None)
    pruef("Grenzfall C = L_{t−1} (99): kein Muster", K.smash_day(a, k("2026-10-16", 100, 100.5, 98.5, 99, vor=101)) is None)
    pruef("Volumen 0 (Kopie/kein Handel): kein Muster", K.smash_day(a, k("2026-10-16", 100.5, 101, 98, 98.5, v=0, vor=101)) is None)
    pruef("High = Low: kein Muster", K.smash_day(a, k("2026-10-16", 98.5, 98.5, 98.5, 98.5, vor=101)) is None)
    pruef("Schluss über dem Hoch (unmögliche Kerze): kein Muster",
          K.smash_day(a, k("2026-10-16", 100, 101, 98, 101.5, vor=101)) is None)
    pruef("Basisbruch (log_return passt nicht zum Kursverhältnis): kein Muster",
          K.smash_day(a, k("2026-10-16", 100.5, 101, 98, 98.5, lr=0.01)) is None)
    pruef("Vorkerze ohne log_return (Studie verwirft das Paar): kein Muster",
          K.smash_day(dict(a, log_return=None), k("2026-10-16", 100.5, 101, 98, 98.5, vor=101)) is None)
    pruef("Vorkerze ungültig (None): kein Muster",
          K.smash_day(dict(a, high=None), k("2026-10-16", 100.5, 101, 98, 98.5, vor=101)) is None)
    zwei = [a, k("2026-10-16", 100.5, 101, 98, 98.5, vor=101)]
    pruef("muster_fuer: Aktie, Session 16.10. (Fr), Vorsitzung 15.10. → Kauf", K.muster_fuer("AAPL", zwei, date(2026, 10, 16)) == K.KAUF)
    pruef("muster_fuer: falsche Session (veraltete Kerze) → kein Muster", K.muster_fuer("AAPL", zwei, date(2026, 10, 19)) is None)
    # nur die Sessionprüfung greift: Vorkerze 15.10. = direkte Vorsitzung der Session 16.10., aber die jüngste Kerze
    # trägt ein anderes Datum als die erwartete Session
    pruef("muster_fuer: jüngste Kerze ≠ erwartete Session (Vorkerze passt) → kein Muster",
          K.muster_fuer("AAPL", [a, dict(zwei[1], date="2026-10-19")], "2026-10-16") is None)
    pruef("muster_fuer: Lücke (Vorkerze 14.10.) → kein Muster",
          K.muster_fuer("AAPL", [dict(a, date="2026-10-14"), zwei[1]], "2026-10-16") is None)
    pruef("muster_fuer: Krypto/Futures/Index/Devisen nicht im Universum",
          all(K.muster_fuer(t, zwei, "2026-10-16") is None for t in ("BTC-USD", "GC=F", "^GSPC", "EURUSD=X")))
    pruef("muster_fuer: XETRA-Titel mit XETRA-Kalender", K.muster_fuer("SAP.DE", zwei, "2026-10-16") == K.KAUF)

    print("== Zwilling Mail ↔ Studie")
    rng = np.random.default_rng(5)
    d, tage = date(2015, 1, 5), []
    while len(tage) < 1500:
        if d.weekday() < 5:
            tage.append(d.isoformat())
        d += timedelta(days=1)
    rows, c = [], 50.0
    for i, t in enumerate(tage):
        o = c * math.exp(rng.normal(0, 0.006))
        c2 = o * math.exp(rng.normal(0, 0.014))
        h = max(o, c2) * math.exp(abs(rng.normal(0, 0.006)))
        l = min(o, c2) * math.exp(-abs(rng.normal(0, 0.006)))
        v = 0 if i % 97 == 0 else 1000                 # vereinzelt ungültige Kerzen
        lr = math.log(c2 / c) + (0.01 if i % 131 == 0 else 0.0)   # vereinzelt Basisbrüche
        rows.append([t, o, h, l, c2, v, lr])
        c = c2
    r = W.aufbereiten(rows, tage)
    roh = W.muster_roh(r)
    abw, geprueft = [], 0
    for t in range(1, len(rows)):
        studie = None
        if r["glied"][t]:                              # beide Kerzen gültig, Folge-Sitzung, gleiche Basis
            studie = K.KAUF if roh["SMASH_K"][t] else (K.VERKAUF if roh["SMASH_V"][t] else None)
        kz = lambda x: {"date": x[0], "open": x[1], "high": x[2], "low": x[3], "close": x[4], "volume": x[5], "log_return": x[6]}
        mail = K.smash_day(kz(rows[t - 1]), kz(rows[t]))
        geprueft += 1
        if mail != studie:
            abw.append((rows[t][0], mail, studie))
    pruef(f"gleiches Muster an allen {geprueft} Tagespaaren", not abw, abw[:5])
    treffer = sum(1 for t in range(1, len(rows)) if r["glied"][t] and (roh["SMASH_K"][t] or roh["SMASH_V"][t]))
    pruef("die Reihe enthält genug Smash-Tage für den Vergleich (> 100)", treffer > 100, treffer)

    print("== Blast-Off nicht im Score (Nutzerentscheidung 2026-10-17)")
    import pandas as pd
    from shared.newsletter_indicators import compute_ticker_signals
    reihe = pd.Series(100 + np.cumsum(0.3 + np.random.default_rng(1).normal(0, 0.5, 400)),
                      index=pd.bdate_range("2022-01-03", periods=400))
    c_ = float(reihe.iloc[-1])
    klein = compute_ticker_signals(reihe, last_bar={"open": c_, "high": c_ * 1.02, "low": c_ * 0.98, "close": c_ * 1.001})
    gross = compute_ticker_signals(reihe, last_bar={"open": c_ * 0.98, "high": c_ * 1.02, "low": c_ * 0.98, "close": c_ * 1.02})
    pruef("kleiner Körper (BO < 20) und großer Körper ergeben denselben Score; BO bleibt als Wert",
          klein["blastoff"] < 20 <= gross["blastoff"] and klein["score"] == gross["score"] == compute_ticker_signals(reihe)["score"],
          (klein, gross))

    print("== Mailvorlage")
    from scripts.daily_newsletter import _load_template
    mod = _load_template().make_module({})
    zeile = dict(ticker="AAA", name="A", price_close=1.0, change_pct=0.1, mw_score=2, lbr_weekly=1, lbr_daily=1,
                 rsi_daily=50, rsi_weekly=50, rsi3_daily=50, blastoff=30, score=1, total_score=3, skew_pts=None,
                 skew_pctl=None, why=None)
    html = str(mod.signal_table([dict(zeile, ticker="KKK", muster=K.KAUF), dict(zeile, ticker="VVV", muster=K.VERKAUF),
                                 dict(zeile, ticker="NNN", muster=None)]))
    import re
    zellen = {tk: re.search(r'<td class="tk">' + tk + r'.*?</tr>', html, re.S).group(0) for tk in ("KKK", "VVV", "NNN")}
    pruef("Kauf-Setup: grün „Smash ↑“", 'class="up" style="font-weight:700;white-space:nowrap;">Smash&nbsp;↑' in zellen["KKK"])
    pruef("Verkauf-Setup: rot „Smash ↓“", 'class="dn" style="font-weight:700;white-space:nowrap;">Smash&nbsp;↓' in zellen["VVV"])
    pruef("kein Muster: „—“ neutral", 'class="nu" style="font-weight:700;white-space:nowrap;">—' in zellen["NNN"])
    pruef("Spaltenkopf „Muster“ vorhanden, Spaltenzahl Kopf = Zeile",
          '>Muster</th>' in html and len(re.findall(r"<th[\s>]", html.split("</thead>")[0])) == zellen["KKK"].count("<td"),
          (len(re.findall(r"<th[\s>]", html.split("</thead>")[0])), zellen["KKK"].count("<td")))
    return 0


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        print("[Absturz]")
        sys.exit(3)
    print()
    if FEHLER:
        print(f"[FAIL] {len(FEHLER)} Prüfung(en): " + "; ".join(FEHLER))
        sys.exit(1)
    print("[OK] alle Prüfungen grün")
    sys.exit(0)
