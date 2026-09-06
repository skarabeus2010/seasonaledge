#!/usr/bin/env python3
"""
options_universe.py — thematisch gegliedertes US-Options-Universum.

Optionen gibt es nur auf US-gelistete Werte (unsere .DE/.OL/.L-Werte haben keine
US-Optionen). Dieses Universum ist die Quelle der Wahrheit für die Options-
Analysen (Skew-Radar, GEX/Vol-Trigger, IV-Surface …). Jeder Ticker kann in
mehreren Kategorien stehen (z.B. NVDA in "Mag7" UND "AI & Semis") — das Frontend
filtert je Kategorie, damit der Radar übersichtlich bleibt (Wald vor Bäumen).

Alle Ticker sind in shared/symbols.py vorhanden → Kursreihen (für realisierte
Vola/VRP) sind verfügbar.
"""
from __future__ import annotations

# Reihenfolge = Anzeige-Reihenfolge der Kategorie-Filter im Frontend.
OPTIONS_CATEGORIES: dict[str, list[str]] = {
    "Broad-Index": [
        "SPY", "QQQ", "IWM", "DIA", "RSP", "MAGS",
    ],
    "Sektor-ETF": [
        "XLF", "XLK", "XLE", "XLV", "XLU", "XLI", "XLY", "XLP", "XLB", "XLC",
        "XLRE", "SMH", "SOXX", "IGV", "XBI", "ITB", "KRE", "GDX", "XOP",
    ],
    "Rohstoff & Bond": [
        "GLD", "SLV", "USO", "TLT", "IEF", "HYG", "URA", "TAN", "IBIT", "ETHA",
    ],
    "Mag7": [
        "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA",
    ],
    "AI & Semis": [
        "NVDA", "AMD", "AVGO", "MU", "ARM", "ASML", "QCOM", "INTC", "TXN",
        "LRCX", "KLAC", "AMAT", "ADI", "ANET", "DELL", "PLTR", "CRWD", "PANW",
        "NOW", "ORCL", "CRM", "ADBE", "INTU", "CSCO", "APP", "SMCI",
    ],
    "Energie & Grid": [
        "XOM", "CVX", "COP", "EQT", "WMB", "CEG", "VST", "NRG", "NEE", "DUK",
        "SO", "GEV", "OKLO", "SMR", "CCJ", "UEC", "UUUU", "NXE", "LEU",
        "FSLR", "ENPH", "SEDG", "ARRY", "BE", "POWL", "PWR", "ETN", "GE",
    ],
    "Finanzen": [
        "JPM", "BAC", "GS", "MS", "WFC", "C", "SCHW", "COF", "BLK", "BX",
        "AXP", "V", "MA", "ICE", "CME", "SPGI", "PGR", "CB", "TRV",
    ],
    "Healthcare": [
        "LLY", "UNH", "JNJ", "ABBV", "MRK", "PFE", "TMO", "ABT", "DHR", "ISRG",
        "VRTX", "AMGN", "GILD", "BSX", "SYK", "MDT", "HCA",
    ],
    "Consumer & Growth": [
        "WMT", "COST", "HD", "LOW", "MCD", "KO", "PEP", "PG", "NKE", "SBUX",
        "TJX", "BKNG", "MAR", "DIS", "UBER", "TMUS", "NFLX", "SPOT", "BA",
        "CAT", "DE", "HON", "RTX", "LMT", "UNP",
    ],
}

# Reihenfolge der Kern-Ticker, die im Vol-Trigger/GEX priorisiert werden.
CORE_OPTIONS = ["SPY", "QQQ", "IWM", "DIA", "NVDA", "AAPL", "MSFT", "TSLA", "META", "AMZN", "GOOGL"]


def all_option_tickers() -> list[str]:
    """Deduplizierte Union aller Kategorien (Reihenfolge stabil)."""
    seen, out = set(), []
    for tickers in OPTIONS_CATEGORIES.values():
        for t in tickers:
            if t not in seen:
                seen.add(t); out.append(t)
    return out


def categories_for(ticker: str) -> list[str]:
    """Alle Kategorien, in denen ein Ticker steht."""
    return [cat for cat, ts in OPTIONS_CATEGORIES.items() if ticker in ts]


def category_map() -> dict[str, list[str]]:
    """Ticker → Liste seiner Kategorien (fürs Frontend-Tagging)."""
    return {t: categories_for(t) for t in all_option_tickers()}
