"""Probe: Williams True Seasonal gegen den Jahreszyklus der Seite — QQQ, SPY, ^GDAXI (rein lesend).

Stand 16.10. (Artefakt „True Seasonal Probe“): gerechnet mit der ERSTEN Fassung von shared/true_seasonal.py (Vorjahr =
year_covers, „in_10“ = Jahre Y−9…Y, nicht das Seitenfenster Y−N…Y, „in_alle“ inkl. Jahre nach Y). Die Seite rechnet mit
dem Kern nach Plan v3 (Heuristik „vollständig“, Kalenderfenster) — die Zahlen sind eine Größenordnung, keine Nachbildung.

Läuft auf dem Server (Kurse aus Supabase):
  docker exec -e PYTHONPATH=/tmp/ts:/app seasonalpha-app python3 /tmp/ts/true_seasonal_probe.py > ergebnis.json

Ausgabe (JSON):
  kurven[ticker]   — 2026 auf der 365er-Achse: Jahreszyklus wie /jahreszyklus (10 J. und max, inkl. laufendem Jahr mit
                     fortgeschriebenem Endwert, Ausreißerfilter aus), True Seasonal 2026 (alle Vorjahre / 10 Vorjahre),
                     Ist-Verlauf 2026 bis zum letzten Kurstag.
  zeitreihe[ticker]— je Jahr 2016–2026: True-Seasonal-Segment auf den Jahresanfangskurs skaliert (Williams' Darstellung)
                     und Monatsend-Schlusskurse.
  test[ticker]     — je Jahr Y: Monatsrenditen des Ist-Jahres gegen die Monatsrenditen von
                       ts_alle  = True Seasonal (alle abgeschlossenen Jahre < Y)
                       ts_10    = True Seasonal (10 Vorjahre)
                       in_alle  = Mittel ALLER abgeschlossenen Jahre inkl. Y (die Kurve, die man heute rückblickend sieht)
                       in_10    = 10-Jahres-Fenster bis einschließlich Y (wie die Seite mit Y als letztem Jahr)
                     Kennzahlen: Pearson-Korrelation der 12 Monatsrenditen und Vorzeichentreffer (von 12).
"""
import json
import math
import sys
from datetime import date

import numpy as np
import pandas as pd

from shared.calculations import build_year_data, last_actual_day, year_covers
from shared.data import lade_kurse
from shared.true_seasonal import true_seasonal

TICKER = ["QQQ", "SPY", "^GDAXI"]
STICHTAG = date(2026, 10, 16)
MONATS_ENDE = [31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334, 365]   # Tag auf der 365er-Achse


def df_aus(ticker):
    daten, closes, rets = lade_kurse(ticker)
    df = pd.DataFrame({"date": pd.to_datetime(daten), "close": closes, "log_return": rets})
    df = df[df["date"].dt.date <= STICHTAG]
    df["year"] = df["date"].dt.year
    df["day_of_year"] = df["date"].dt.dayofyear
    return df


def monatsrenditen(kurve):
    werte, vor = [], 100.0
    for e in MONATS_ENDE:
        v = kurve[e - 1]
        werte.append(v / vor - 1)
        vor = v
    return np.array(werte)


def kennzahlen(ist, modell):
    a, b = monatsrenditen(ist), monatsrenditen(modell)
    r = float(np.corrcoef(a, b)[0, 1]) if a.std() > 0 and b.std() > 0 else float("nan")
    treffer = int(np.sum(np.sign(a) == np.sign(b)))
    return r, treffer


def mittel(yd, jahre):
    return np.array([yd[j]["full_365"] for j in jahre], dtype=float).mean(axis=0).tolist()


def main():
    out = {"stichtag": str(STICHTAG), "kurven": {}, "zeitreihe": {}, "test": {}, "zusammenfassung": {}}
    for t in TICKER:
        df = df_aus(t)
        jahre_alle = sorted(df["year"].unique().tolist())
        yd = build_year_data(df, jahre_alle)
        lj = STICHTAG.year
        abgeschl = [j for j in sorted(yd) if year_covers(yd[j], 365, j, lj)]

        # --- 2026: Seite gegen True Seasonal
        seite10 = [j for j in sorted(yd) if j >= lj - 10]          # wie jahreszyklus.html: minYear = Jahr − 10
        seitemax = sorted(yd)
        ts_alle, j_alle = true_seasonal(yd, lj)
        ts_10, j_10 = true_seasonal(yd, lj, fenster_n=10)
        ist = yd[lj]["full_365"][: last_actual_day(yd[lj])] if lj in yd else []
        out["kurven"][t] = {
            "seite_10": {"jahre": [seite10[0], seite10[-1]], "n": len(seite10), "werte": mittel(yd, seite10)},
            "seite_max": {"jahre": [seitemax[0], seitemax[-1]], "n": len(seitemax), "werte": mittel(yd, seitemax)},
            "ts_alle": {"jahre": [j_alle[0], j_alle[-1]], "n": len(j_alle), "werte": ts_alle},
            "ts_10": {"jahre": [j_10[0], j_10[-1]], "n": len(j_10), "werte": ts_10},
            "ist_2026": ist,
            "erstes_jahr": jahre_alle[0],
        }

        # --- Zeitreihe à la Williams: je Jahr Segment ab Jahresanfangskurs
        zr = []
        for j in range(2016, lj + 1):
            if j not in yd:
                continue
            kurve, benutzt = true_seasonal(yd, j)
            if kurve is None:
                continue
            jdf = yd[j]["df"]
            start = float(jdf["close"].iloc[0])
            monate = (jdf.set_index("date")["close"].resample("ME").last().dropna())
            zr.append({"jahr": j, "start": start, "n_vorjahre": len(benutzt),
                       "ts_monatsende": [start * kurve[e - 1] / 100 for e in MONATS_ENDE],
                       "ist_monatsende": [[d.strftime("%Y-%m"), float(v)] for d, v in monate.items()]})
        out["zeitreihe"][t] = zr

        # --- Test je abgeschlossenem Jahr
        zeilen = []
        for y in abgeschl:
            m_ts, vj = true_seasonal(yd, y, min_jahre=10)
            if m_ts is None:
                continue
            m_ts10, _ = true_seasonal(yd, y, fenster_n=10, min_jahre=10)
            m_in = mittel(yd, abgeschl)
            fenster = [j for j in abgeschl if y - 9 <= j <= y]
            m_in10 = mittel(yd, fenster)
            ist_y = yd[y]["full_365"]
            z = {"jahr": y, "n_vorjahre": len(vj)}
            for name, m in (("ts_alle", m_ts), ("ts_10", m_ts10), ("in_alle", m_in), ("in_10", m_in10)):
                r, tr = kennzahlen(ist_y, m)
                z[name] = {"r": r, "treffer": tr}
            zeilen.append(z)
        out["test"][t] = zeilen
        zs = {"jahre": len(zeilen), "von": zeilen[0]["jahr"] if zeilen else None,
              "bis": zeilen[-1]["jahr"] if zeilen else None}
        for name in ("ts_alle", "ts_10", "in_alle", "in_10"):
            rs = [z[name]["r"] for z in zeilen if not math.isnan(z[name]["r"])]
            trs = [z[name]["treffer"] for z in zeilen]
            zs[name] = {"r_mittel": float(np.mean(rs)) if rs else None,
                        "r_positiv": int(sum(1 for r in rs if r > 0)),
                        "treffer_mittel": float(np.mean(trs)) if trs else None}
        out["zusammenfassung"][t] = zs
    json.dump(out, sys.stdout)


if __name__ == "__main__":
    main()
