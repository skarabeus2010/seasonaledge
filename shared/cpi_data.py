"""
shared/cpi_data.py — US Consumer Price Index (CPI) Daten
=========================================================
Quelle: Bureau of Labor Statistics / FRED (CPIAUCSL)
Basis: 1982-84 = 100

- Historische Jahresdurchschnitte 1886–2025
- FRED API Update (optional, ab 1913)
- Supabase Persistenz (Tabelle: historical_cpi)
- Inflationsbereinigung: Real = Nominal / CPI * 100
"""

import pandas as pd
import numpy as np
import requests

from shared.logger import app_logger

# ── Historische CPI Jahresdurchschnitte (BLS, 1982-84=100) ──────────
# 1886–1912: Rekonstruiert aus BLS Historical CPI (pre-series, cost of living index)
# 1913–2025: Offizielle BLS CPI-U Jahresdurchschnitte
# Quellen: Minneapolis Fed, BLS, measuringworth.com
HISTORICAL_CPI = {
    1886: 8.0, 1887: 8.0, 1888: 8.0, 1889: 7.7, 1890: 7.7,
    1891: 7.7, 1892: 7.7, 1893: 7.5, 1894: 7.1, 1895: 7.1,
    1896: 7.1, 1897: 7.1, 1898: 7.1, 1899: 7.1, 1900: 7.4,
    1901: 7.4, 1902: 7.7, 1903: 7.9, 1904: 7.9, 1905: 7.7,
    1906: 7.9, 1907: 8.3, 1908: 8.0, 1909: 8.0, 1910: 8.5,
    1911: 8.5, 1912: 8.7,
    # Ab hier: offizielle BLS CPI-U Jahresdurchschnitte
    1913: 9.9, 1914: 10.0, 1915: 10.1, 1916: 10.9, 1917: 12.8,
    1918: 15.1, 1919: 17.3, 1920: 20.0, 1921: 17.9, 1922: 16.8,
    1923: 17.1, 1924: 17.1, 1925: 17.5, 1926: 17.7, 1927: 17.4,
    1928: 17.1, 1929: 17.1, 1930: 16.7, 1931: 15.2, 1932: 13.7,
    1933: 13.0, 1934: 13.4, 1935: 13.7, 1936: 13.9, 1937: 14.4,
    1938: 14.1, 1939: 13.9, 1940: 14.0, 1941: 14.7, 1942: 16.3,
    1943: 17.3, 1944: 17.6, 1945: 18.0, 1946: 19.5, 1947: 22.3,
    1948: 24.1, 1949: 23.8, 1950: 24.1, 1951: 26.0, 1952: 26.5,
    1953: 26.7, 1954: 26.9, 1955: 26.8, 1956: 27.2, 1957: 28.1,
    1958: 28.9, 1959: 29.1, 1960: 29.6, 1961: 29.9, 1962: 30.2,
    1963: 30.6, 1964: 31.0, 1965: 31.5, 1966: 32.4, 1967: 33.4,
    1968: 34.8, 1969: 36.7, 1970: 38.8, 1971: 40.5, 1972: 41.8,
    1973: 44.4, 1974: 49.3, 1975: 53.8, 1976: 56.9, 1977: 60.6,
    1978: 65.2, 1979: 72.6, 1980: 82.4, 1981: 90.9, 1982: 96.5,
    1983: 99.6, 1984: 103.9, 1985: 107.6, 1986: 109.6, 1987: 113.6,
    1988: 118.3, 1989: 124.0, 1990: 130.7, 1991: 136.2, 1992: 140.3,
    1993: 144.5, 1994: 148.2, 1995: 152.4, 1996: 156.9, 1997: 160.5,
    1998: 163.0, 1999: 166.6, 2000: 172.2, 2001: 177.1, 2002: 179.9,
    2003: 184.0, 2004: 188.9, 2005: 195.3, 2006: 201.6, 2007: 207.3,
    2008: 215.3, 2009: 214.5, 2010: 218.1, 2011: 224.9, 2012: 229.6,
    2013: 233.0, 2014: 236.7, 2015: 237.0, 2016: 240.0, 2017: 245.1,
    2018: 251.1, 2019: 255.7, 2020: 258.8, 2021: 270.9, 2022: 292.7,
    2023: 304.7, 2024: 314.2, 2025: 320.0,
}


def get_cpi_dataframe() -> pd.DataFrame:
    """
    CPI als DataFrame zurueckgeben (year, cpi).
    Versucht zuerst Supabase, dann Fallback auf HISTORICAL_CPI.
    """
    # Supabase-Versuch
    try:
        from shared.supabase_client import fetch_historical_cpi
        db_records = fetch_historical_cpi()
        if db_records and len(db_records) > 50:
            df = pd.DataFrame(db_records)
            app_logger.debug(f"CPI aus Supabase geladen: {len(df)} Jahre")
            return df[["year", "cpi"]].sort_values("year").reset_index(drop=True)
    except Exception as e:
        app_logger.debug(f"CPI Supabase-Fallback: {e}")

    # Fallback: Eingebettete Daten
    df = pd.DataFrame(
        [(y, v) for y, v in sorted(HISTORICAL_CPI.items())],
        columns=["year", "cpi"],
    )
    return df


def fetch_cpi_from_fred(api_key: str = None) -> pd.DataFrame | None:
    """
    CPI-Daten von FRED API laden (CPIAUCSL, monatlich → Jahresdurchschnitt).
    Benoetigt FRED API Key (kostenlos registrierbar).

    Returns:
        DataFrame mit Spalten [year, cpi] oder None bei Fehler
    """
    import os
    key = api_key or os.environ.get("FRED_API_KEY", "")
    if not key:
        try:
            import streamlit as st
            key = st.secrets.get("FRED_API_KEY", "")
        except Exception:
            pass

    if not key:
        app_logger.debug("Kein FRED_API_KEY gesetzt — verwende eingebettete CPI-Daten")
        return None

    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": "CPIAUCSL",
        "api_key": key,
        "file_type": "json",
        "observation_start": "1913-01-01",
        "frequency": "a",  # Annual
        "aggregation_method": "avg",
    }

    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        rows = []
        for obs in data.get("observations", []):
            if obs["value"] != ".":
                year = int(obs["date"][:4])
                cpi = float(obs["value"])
                rows.append({"year": year, "cpi": cpi})

        if rows:
            df = pd.DataFrame(rows)
            app_logger.debug(f"CPI von FRED geladen: {len(df)} Jahre ({df['year'].min()}–{df['year'].max()})")
            return df
    except Exception as e:
        app_logger.debug(f"FRED API Fehler: {e}")

    return None


def update_cpi_in_db(api_key: str = None):
    """
    CPI von FRED holen und in Supabase speichern.
    Kombiniert pre-1913 Daten mit FRED-Daten.
    Fuer Nightly-Job / GitHub Actions.
    """
    from shared.supabase_client import upsert_historical_cpi

    # Basis: Eingebettete historische Daten (1886–1912)
    records = [
        {"year": y, "cpi": v, "source": "bls_historical"}
        for y, v in HISTORICAL_CPI.items()
        if y < 1913
    ]

    # FRED-Daten ab 1913
    fred_df = fetch_cpi_from_fred(api_key)
    if fred_df is not None:
        for _, row in fred_df.iterrows():
            records.append({
                "year": int(row["year"]),
                "cpi": round(float(row["cpi"]), 1),
                "source": "fred_cpiaucsl",
            })
    else:
        # Fallback: Eingebettete Daten ab 1913
        for y, v in HISTORICAL_CPI.items():
            if y >= 1913:
                records.append({"year": y, "cpi": v, "source": "bls_embedded"})

    upsert_historical_cpi(records)
    app_logger.debug(f"CPI in DB gespeichert: {len(records)} Jahre")


# ── Inflationsbereinigung ──────────────────────────────────────────

def calculate_real_prices(
    nominal_prices: dict[int, float],
    base_year: int = 2024,
) -> dict[int, float]:
    """
    Nominale Preise inflationsbereinigen.

    Formel: Real = Nominal / CPI_jahr * CPI_basisjahr

    Args:
        nominal_prices: {year: price} — z.B. Dow Jones Jahresschlusskurse
        base_year: Basisjahr fuer Kaufkraft (Default: 2024)

    Returns:
        {year: real_price} — in Kaufkraft des Basisjahres
    """
    cpi_df = get_cpi_dataframe()
    cpi_map = dict(zip(cpi_df["year"], cpi_df["cpi"]))

    base_cpi = cpi_map.get(base_year)
    if base_cpi is None:
        base_cpi = cpi_map.get(max(cpi_map.keys()))

    real_prices = {}
    for year, price in nominal_prices.items():
        cpi_val = cpi_map.get(year)
        if cpi_val and cpi_val > 0:
            real_prices[year] = price / cpi_val * base_cpi

    return real_prices


def build_nominal_vs_real_df(
    nominal_prices: dict[int, float],
    base_year: int = 2024,
) -> pd.DataFrame:
    """
    DataFrame mit nominal + real Preisen + Inflation aufbauen.

    Returns:
        DataFrame: year, nominal, real, cpi, inflation_pct
    """
    real_prices = calculate_real_prices(nominal_prices, base_year)
    cpi_df = get_cpi_dataframe()
    cpi_map = dict(zip(cpi_df["year"], cpi_df["cpi"]))

    rows = []
    for year in sorted(nominal_prices.keys()):
        if year in real_prices:
            cpi_val = cpi_map.get(year, np.nan)
            rows.append({
                "year": year,
                "nominal": nominal_prices[year],
                "real": real_prices[year],
                "cpi": cpi_val,
            })

    df = pd.DataFrame(rows)
    if not df.empty:
        df["inflation_pct"] = df["cpi"].pct_change() * 100
    return df
