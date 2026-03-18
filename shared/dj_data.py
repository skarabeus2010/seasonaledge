# shared/dj_data.py  — v3
# ============================================================
# Daten für Split-Slider (^DJI)
# Strategie: Live-Daten (Yahoo/Stooq) + synthetischer Backfill
# sodass IMMER mindestens 1980–heute verfügbar sind.
# ============================================================

from __future__ import annotations
import os, importlib.util
import numpy as np
import pandas as pd
import streamlit as st


# ── Eingebettete DOW-Jahresrenditen als Basis-Backfill ────────────────────────
_DJ_ANNUAL: dict[int, float] = {
    1950: 17.63, 1951: 14.37, 1952:  8.42, 1953: -3.77, 1954: 43.96,
    1955: 20.77, 1956:  2.27, 1957:-12.77, 1958: 34.00, 1959: 16.40,
    1960: -9.34, 1961: 18.71, 1962:-10.81, 1963: 17.00, 1964: 14.57,
    1965: 10.88, 1966:-18.94, 1967: 15.20, 1968:  4.27, 1969:-15.19,
    1970:  4.82, 1971:  6.11, 1972: 14.58, 1973:-16.58, 1974:-27.57,
    1975: 38.32, 1976: 17.86, 1977:-17.27, 1978: -3.15, 1979:  4.19,
    1980: 14.93, 1981: -9.23, 1982: 19.60, 1983: 20.27, 1984: -3.74,
    1985: 27.66, 1986: 22.58, 1987:  2.26, 1988: 11.85, 1989: 26.96,
    1990: -4.34, 1991: 20.32, 1992:  4.17, 1993: 13.72, 1994:  2.14,
    1995: 33.45, 1996: 26.01, 1997: 22.64, 1998: 16.10, 1999: 25.22,
    2000: -6.18, 2001: -7.10, 2002:-16.76, 2003: 25.32, 2004:  3.15,
    2005:  1.72, 2006: 16.29, 2007:  6.43, 2008:-33.84, 2009: 18.82,
    2010: 11.02, 2011:  5.53, 2012:  7.26, 2013: 26.50, 2014:  7.52,
    2015: -2.23, 2016: 13.42, 2017: 25.08, 2018: -5.63, 2019: 22.34,
    2020:  7.25, 2021: 18.73, 2022: -8.78, 2023: 13.70, 2024: 12.48,
}
_TD = 252  # Handelstage pro Jahr (synthetisch)


def _synthetic_df() -> pd.DataFrame:
    """
    Synthetischer Backfill 1950–2024 aus Jahresrenditen.
    Intra-year Verteilung folgt historischem DOW-Monatsmuster
    (keine linearen Kurven — realistische Saisonalität).
    """
    import numpy as np

    # Historisches DOW-Monatsmuster: relative monatliche Gewichte (normiert)
    # Basiert auf durchschnittlichen Monatsrenditen DOW 1950-2020
    # Jan  Feb   Mar   Apr   May   Jun   Jul   Aug   Sep   Oct   Nov   Dec
    _MONTH_W = np.array([
        0.8,  0.3,  1.1,  1.4,  0.2, -0.1,  1.2,  0.6, -0.8,  0.5,  1.5,  1.3
    ])
    # Handelstage pro Monat (Näherung, gesamt=252)
    _MONTH_TD = [21, 19, 22, 21, 21, 21, 22, 22, 20, 23, 20, 20]

    # Normierte tägliche Gewichte pro Monat → summiert auf 1.0 über Jahr
    _w_total = sum(w * td for w, td in zip(_MONTH_W, _MONTH_TD))

    rows = []
    rng = np.random.default_rng(42)  # reproduzierbar

    for yr, ap in sorted(_DJ_ANNUAL.items()):
        td = 0
        cum = 0.0
        for m_idx, (m_w, m_days) in enumerate(zip(_MONTH_W, _MONTH_TD)):
            # Monatsrendite: Anteil am Jahres-Return proportional zum Gewicht
            if _w_total != 0:
                month_ret = ap * (m_w * m_days) / _w_total
            else:
                month_ret = ap / 12.0
            daily_base = month_ret / m_days

            # Leichtes Rauschen für natürlich aussehende Kurven
            noise = rng.normal(0, abs(ap) * 0.003 + 0.05, m_days)

            for i in range(m_days):
                cum += daily_base + noise[i]
                td  += 1
                rows.append({"year": yr, "trading_day": td, "cum_return_pct": round(cum, 4)})

        # Letzten Wert auf exakte Jahresrendite normieren (kein Drift)
        if rows and rows[-1]["year"] == yr:
            last_val = rows[-1]["cum_return_pct"]
            drift    = ap - last_val
            # Drift gleichmäßig korrigieren (unsichtbar)
            start_idx = len(rows) - td
            for i in range(td):
                rows[start_idx + i]["cum_return_pct"] = round(
                    rows[start_idx + i]["cum_return_pct"] + drift * (i + 1) / td, 4
                )

    return pd.DataFrame(rows)


def _get_downloader(project_dir: str):
    """Importiert yahoo_downloader — 2 Wege, kein Crash."""
    try:
        from shared.yahoo_downloader import download_data, preprocess
        return download_data, preprocess
    except ImportError:
        pass
    path = os.path.join(project_dir, "shared", "yahoo_downloader.py")
    if not os.path.exists(path):
        return None, None
    spec = importlib.util.spec_from_file_location("yahoo_downloader", path)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.download_data, mod.preprocess


def _live_df(project_dir: str) -> pd.DataFrame | None:
    """
    Versucht Live-Daten zu laden. Gibt None zurück bei Fehler.
    Gibt DataFrame mit year, trading_day, cum_return_pct zurück.
    """
    download_data, preprocess = _get_downloader(project_dir)
    if download_data is None:
        return None
    try:
        raw = download_data("^DJI")
        if raw.empty:
            raw = download_data("^GSPC")
        if raw.empty:
            return None

        df = preprocess(raw)
        df = df.sort_values("Date").reset_index(drop=True)
        df["trading_day"]    = df.groupby("year").cumcount() + 1
        df["cum_return_pct"] = df.groupby("year")["log_return"].cumsum() * 100

        # Nur Jahre mit genug Daten
        valid = df.groupby("year")["trading_day"].max()
        df = df[df["year"].isin(valid[valid >= 20].index)].reset_index(drop=True)

        if df["year"].nunique() < 2:
            return None

        return df[["year", "trading_day", "cum_return_pct"]]
    except Exception:
        return None


def load_dj_data(project_dir: str) -> tuple[pd.DataFrame, str]:
    """
    Lädt DOW-Daten. IMMER mindestens 1950–heute verfügbar.

    Strategie:
      1. Live-Daten holen (Yahoo/Stooq)
      2. Synthetischen Backfill für alle Jahre VOR den Live-Daten einfügen
      3. Ergebnis: maximale historische Tiefe + aktuelle Daten

    Returns: (df, source)
      df     — year, trading_day, cum_return_pct
      source — "live+synthetic" | "synthetic"
    """
    synth = _synthetic_df()
    live  = _live_df(project_dir)

    if live is not None:
        live_min_year = int(live["year"].min())
        # Synthetische Daten nur für Jahre VOR den Live-Daten
        synth_back = synth[synth["year"] < live_min_year]
        if len(synth_back) > 0:
            df = pd.concat([synth_back, live], ignore_index=True)
        else:
            df = live
        return df.sort_values(["year","trading_day"]).reset_index(drop=True), "live+synthetic"

    # Kein Internet / Fehler → nur synthetische Daten
    return synth, "synthetic"
