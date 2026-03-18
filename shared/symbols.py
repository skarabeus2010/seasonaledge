# shared/symbols.py
# Zentrale Ticker-Datenbank für SeasonalEdge.
#
# Felder pro Symbol:
#   name       : Anzeigename (Deutsch)
#   kategorie  : Gruppe für Filterung/Dropdown
#   währung    : "USD" | "EUR" | "GBP" | "JPY" | ...
#   exchange   : Börse (informativ)
#   beschreibung: Kurzbeschreibung (optional, für Tooltips)
#
# Neue Symbole einfach unten in die passende Gruppe eintragen.
# Import-Beispiel:
#   from shared.symbols import SYMBOLS, get_symbols_by_category, KATEGORIEN

# ── Symboldatenbank ────────────────────────────────────────────────────────────

SYMBOLS = {

    # ── US-INDIZES ─────────────────────────────────────────────────────────────
    "^GSPC": {
        "name":         "S&P 500",
        "kategorie":    "US-Index",
        "währung":      "USD",
        "exchange":     "NYSE",
        "beschreibung": "S&P 500 Index — 500 größte US-Unternehmen",
    },
    "^DJI": {
        "name":         "Dow Jones",
        "kategorie":    "US-Index",
        "währung":      "USD",
        "exchange":     "NYSE",
        "beschreibung": "Dow Jones Industrial Average — 30 Blue Chips",
    },
    "^IXIC": {
        "name":         "Nasdaq Composite",
        "kategorie":    "US-Index",
        "währung":      "USD",
        "exchange":     "NASDAQ",
        "beschreibung": "Nasdaq Composite — alle Nasdaq-gelisteten Aktien",
    },
    "^NDX": {
        "name":         "Nasdaq 100",
        "kategorie":    "US-Index",
        "währung":      "USD",
        "exchange":     "NASDAQ",
        "beschreibung": "Nasdaq 100 — Top 100 Nicht-Finanzwerte",
    },
    "^RUT": {
        "name":         "Russell 2000",
        "kategorie":    "US-Index",
        "währung":      "USD",
        "exchange":     "NYSE",
        "beschreibung": "Russell 2000 — 2000 Small-Cap US-Aktien",
    },
    "^VIX": {
        "name":         "VIX Volatilitätsindex",
        "kategorie":    "US-Index",
        "währung":      "USD",
        "exchange":     "CBOE",
        "beschreibung": "CBOE Volatility Index — Angst-Barometer",
    },

    # ── US-ETFs ────────────────────────────────────────────────────────────────
    "SPY": {
        "name":         "SPDR S&P 500 ETF",
        "kategorie":    "US-ETF",
        "währung":      "USD",
        "exchange":     "NYSE",
        "beschreibung": "Größter S&P 500 ETF — sehr hohe Liquidität",
    },
    "QQQ": {
        "name":         "Invesco Nasdaq 100 ETF",
        "kategorie":    "US-ETF",
        "währung":      "USD",
        "exchange":     "NASDAQ",
        "beschreibung": "Nasdaq 100 ETF — Tech-lastig",
    },
    "IWM": {
        "name":         "iShares Russell 2000 ETF",
        "kategorie":    "US-ETF",
        "währung":      "USD",
        "exchange":     "NYSE",
        "beschreibung": "Small-Cap US-Aktien ETF",
    },
    "DIA": {
        "name":         "SPDR Dow Jones ETF",
        "kategorie":    "US-ETF",
        "währung":      "USD",
        "exchange":     "NYSE",
        "beschreibung": "Dow Jones Industrial Average ETF",
    },
    "TLT": {
        "name":         "iShares 20+ Year Treasury ETF",
        "kategorie":    "US-ETF",
        "währung":      "USD",
        "exchange":     "NYSE",
        "beschreibung": "Langläufer US-Staatsanleihen ETF",
    },
    "GLD": {
        "name":         "SPDR Gold ETF",
        "kategorie":    "US-ETF",
        "währung":      "USD",
        "exchange":     "NYSE",
        "beschreibung": "Gold ETF — physisch hinterlegt",
    },
    "SLV": {
        "name":         "iShares Silver ETF",
        "kategorie":    "US-ETF",
        "währung":      "USD",
        "exchange":     "NYSE",
        "beschreibung": "Silber ETF",
    },
    "USO": {
        "name":         "United States Oil ETF",
        "kategorie":    "US-ETF",
        "währung":      "USD",
        "exchange":     "NYSE",
        "beschreibung": "Rohöl ETF (WTI)",
    },
    "XLF": {
        "name":         "Financial Select Sector ETF",
        "kategorie":    "US-ETF",
        "währung":      "USD",
        "exchange":     "NYSE",
        "beschreibung": "US-Finanzsektor ETF",
    },
    "XLK": {
        "name":         "Technology Select Sector ETF",
        "kategorie":    "US-ETF",
        "währung":      "USD",
        "exchange":     "NYSE",
        "beschreibung": "US-Technologiesektor ETF",
    },
    "XLE": {
        "name":         "Energy Select Sector ETF",
        "kategorie":    "US-ETF",
        "währung":      "USD",
        "exchange":     "NYSE",
        "beschreibung": "US-Energiesektor ETF",
    },
    "XLV": {
        "name":         "Health Care Select Sector ETF",
        "kategorie":    "US-ETF",
        "währung":      "USD",
        "exchange":     "NYSE",
        "beschreibung": "US-Gesundheitssektor ETF",
    },
    "XLU": {
        "name":         "Utilities Select Sector ETF",
        "kategorie":    "US-ETF",
        "währung":      "USD",
        "exchange":     "NYSE",
        "beschreibung": "US-Versorgungssektor ETF",
    },

    # ── US-EINZELAKTIEN ────────────────────────────────────────────────────────
    "AAPL": {
        "name":         "Apple",
        "kategorie":    "US-Aktie",
        "währung":      "USD",
        "exchange":     "NASDAQ",
        "beschreibung": "Apple Inc. — Consumer Electronics & Software",
    },
    "MSFT": {
        "name":         "Microsoft",
        "kategorie":    "US-Aktie",
        "währung":      "USD",
        "exchange":     "NASDAQ",
        "beschreibung": "Microsoft Corp. — Software & Cloud",
    },
    "NVDA": {
        "name":         "Nvidia",
        "kategorie":    "US-Aktie",
        "währung":      "USD",
        "exchange":     "NASDAQ",
        "beschreibung": "Nvidia Corp. — GPUs & KI-Chips",
    },
    "AMZN": {
        "name":         "Amazon",
        "kategorie":    "US-Aktie",
        "währung":      "USD",
        "exchange":     "NASDAQ",
        "beschreibung": "Amazon.com — E-Commerce & Cloud (AWS)",
    },
    "GOOGL": {
        "name":         "Alphabet (Google)",
        "kategorie":    "US-Aktie",
        "währung":      "USD",
        "exchange":     "NASDAQ",
        "beschreibung": "Alphabet Inc. — Suchmaschine & Werbung",
    },
    "META": {
        "name":         "Meta Platforms",
        "kategorie":    "US-Aktie",
        "währung":      "USD",
        "exchange":     "NASDAQ",
        "beschreibung": "Meta Platforms — Facebook, Instagram, WhatsApp",
    },
    "TSLA": {
        "name":         "Tesla",
        "kategorie":    "US-Aktie",
        "währung":      "USD",
        "exchange":     "NASDAQ",
        "beschreibung": "Tesla Inc. — Elektrofahrzeuge & Energie",
    },
    "JPM": {
        "name":         "JPMorgan Chase",
        "kategorie":    "US-Aktie",
        "währung":      "USD",
        "exchange":     "NYSE",
        "beschreibung": "JPMorgan Chase — größte US-Bank",
    },
    "XOM": {
        "name":         "ExxonMobil",
        "kategorie":    "US-Aktie",
        "währung":      "USD",
        "exchange":     "NYSE",
        "beschreibung": "ExxonMobil Corp. — Öl & Gas",
    },

    # ── EUROPÄISCHE INDIZES ────────────────────────────────────────────────────
    "^GDAXI": {
        "name":         "DAX 40",
        "kategorie":    "EU-Index",
        "währung":      "EUR",
        "exchange":     "XETRA",
        "beschreibung": "Deutscher Leitindex — 40 größte deutsche Unternehmen",
    },
    "^MDAXI": {
        "name":         "MDAX",
        "kategorie":    "EU-Index",
        "währung":      "EUR",
        "exchange":     "XETRA",
        "beschreibung": "Mid-Cap Deutschen Aktien — 50 Unternehmen",
    },
    "^STOXX50E": {
        "name":         "Euro Stoxx 50",
        "kategorie":    "EU-Index",
        "währung":      "EUR",
        "exchange":     "Euronext",
        "beschreibung": "50 größte Eurozone-Unternehmen",
    },
    "^FTSE": {
        "name":         "FTSE 100",
        "kategorie":    "EU-Index",
        "währung":      "GBP",
        "exchange":     "LSE",
        "beschreibung": "Britischer Leitindex — 100 größte UK-Unternehmen",
    },
    "^FCHI": {
        "name":         "CAC 40",
        "kategorie":    "EU-Index",
        "währung":      "EUR",
        "exchange":     "Euronext Paris",
        "beschreibung": "Französischer Leitindex — 40 Unternehmen",
    },
    "^SSMI": {
        "name":         "SMI (Schweiz)",
        "kategorie":    "EU-Index",
        "währung":      "CHF",
        "exchange":     "SIX",
        "beschreibung": "Swiss Market Index — 20 größte Schweizer Unternehmen",
    },

    # ── ASIATISCHE INDIZES ─────────────────────────────────────────────────────
    "^N225": {
        "name":         "Nikkei 225",
        "kategorie":    "Asien-Index",
        "währung":      "JPY",
        "exchange":     "TSE",
        "beschreibung": "Japanischer Leitindex — 225 Unternehmen",
    },
    "^HSI": {
        "name":         "Hang Seng",
        "kategorie":    "Asien-Index",
        "währung":      "HKD",
        "exchange":     "HKEX",
        "beschreibung": "Hongkonger Leitindex",
    },
    "^KS11": {
        "name":         "KOSPI (Korea)",
        "kategorie":    "Asien-Index",
        "währung":      "KRW",
        "exchange":     "KRX",
        "beschreibung": "Koreanischer Aktienindex",
    },

    # ── ROHSTOFFE / FUTURES ────────────────────────────────────────────────────
    "GC=F": {
        "name":         "Gold Futures",
        "kategorie":    "Rohstoff",
        "währung":      "USD",
        "exchange":     "COMEX",
        "beschreibung": "Gold Front-Month Futures ($/oz)",
    },
    "SI=F": {
        "name":         "Silber Futures",
        "kategorie":    "Rohstoff",
        "währung":      "USD",
        "exchange":     "COMEX",
        "beschreibung": "Silber Front-Month Futures ($/oz)",
    },
    "CL=F": {
        "name":         "WTI Rohöl Futures",
        "kategorie":    "Rohstoff",
        "währung":      "USD",
        "exchange":     "NYMEX",
        "beschreibung": "West Texas Intermediate Crude Oil ($/barrel)",
    },
    "BZ=F": {
        "name":         "Brent Rohöl Futures",
        "kategorie":    "Rohstoff",
        "währung":      "USD",
        "exchange":     "ICE",
        "beschreibung": "Brent Crude Oil ($/barrel)",
    },
    "NG=F": {
        "name":         "Natural Gas Futures",
        "kategorie":    "Rohstoff",
        "währung":      "USD",
        "exchange":     "NYMEX",
        "beschreibung": "Natural Gas Front-Month Futures",
    },
    "ZC=F": {
        "name":         "Corn Futures (Mais)",
        "kategorie":    "Rohstoff",
        "währung":      "USD",
        "exchange":     "CBOT",
        "beschreibung": "Corn (Mais) Front-Month Futures (cents/bushel)",
    },
    "ZW=F": {
        "name":         "Wheat Futures (Weizen)",
        "kategorie":    "Rohstoff",
        "währung":      "USD",
        "exchange":     "CBOT",
        "beschreibung": "Wheat (Weizen) Front-Month Futures",
    },
    "ES=F": {
        "name":         "E-Mini S&P 500 Futures",
        "kategorie":    "Futures",
        "währung":      "USD",
        "exchange":     "CME",
        "beschreibung": "E-Mini S&P 500 Front-Month Futures",
    },
    "NQ=F": {
        "name":         "E-Mini Nasdaq 100 Futures",
        "kategorie":    "Futures",
        "währung":      "USD",
        "exchange":     "CME",
        "beschreibung": "E-Mini Nasdaq 100 Front-Month Futures",
    },

    # ── KRYPTOWÄHRUNGEN ────────────────────────────────────────────────────────
    "BTC-USD": {
        "name":         "Bitcoin (USD)",
        "kategorie":    "Krypto",
        "währung":      "USD",
        "exchange":     "Crypto",
        "beschreibung": "Bitcoin / US-Dollar",
    },
    "ETH-USD": {
        "name":         "Ethereum (USD)",
        "kategorie":    "Krypto",
        "währung":      "USD",
        "exchange":     "Crypto",
        "beschreibung": "Ethereum / US-Dollar",
    },
    "SOL-USD": {
        "name":         "Solana (USD)",
        "kategorie":    "Krypto",
        "währung":      "USD",
        "exchange":     "Crypto",
        "beschreibung": "Solana / US-Dollar",
    },

    # ── FX / DEVISEN ───────────────────────────────────────────────────────────
    "EURUSD=X": {
        "name":         "EUR/USD",
        "kategorie":    "FX",
        "währung":      "USD",
        "exchange":     "Forex",
        "beschreibung": "Euro / US-Dollar Wechselkurs",
    },
    "GBPUSD=X": {
        "name":         "GBP/USD",
        "kategorie":    "FX",
        "währung":      "USD",
        "exchange":     "Forex",
        "beschreibung": "Britisches Pfund / US-Dollar",
    },
    "USDJPY=X": {
        "name":         "USD/JPY",
        "kategorie":    "FX",
        "währung":      "JPY",
        "exchange":     "Forex",
        "beschreibung": "US-Dollar / Japanischer Yen",
    },
    "USDCHF=X": {
        "name":         "USD/CHF",
        "kategorie":    "FX",
        "währung":      "CHF",
        "exchange":     "Forex",
        "beschreibung": "US-Dollar / Schweizer Franken",
    },
}


# ── Konstanten ─────────────────────────────────────────────────────────────────

# Alle verfügbaren Kategorien (geordnet für Dropdowns)
KATEGORIEN = [
    "US-Index",
    "US-ETF",
    "US-Aktie",
    "EU-Index",
    "Asien-Index",
    "Rohstoff",
    "Futures",
    "Krypto",
    "FX",
]

# Standard-Ticker
DEFAULT_SYMBOL = "SPY"


# ── Hilfsfunktionen ────────────────────────────────────────────────────────────

def get_symbols_by_category(kategorie: str) -> dict:
    """Gibt alle Symbole einer Kategorie zurück."""
    return {k: v for k, v in SYMBOLS.items() if v["kategorie"] == kategorie}


def get_all_tickers() -> list[str]:
    """Gibt alle Ticker-Symbole als sortierte Liste zurück."""
    return sorted(SYMBOLS.keys())


def get_display_name(ticker: str) -> str:
    """Gibt den Anzeigenamen für einen Ticker zurück.
    Fallback: Ticker selbst wenn nicht in SYMBOLS."""
    return SYMBOLS.get(ticker, {}).get("name", ticker)


def get_dropdown_label(ticker: str) -> str:
    """Gibt einen kombinierten Label für Streamlit-Dropdowns zurück.
    Format: 'SPY — SPDR S&P 500 ETF'"""
    name = get_display_name(ticker)
    return f"{ticker} — {name}"


def get_symbols_grouped() -> dict[str, dict]:
    """Gibt alle Symbole gruppiert nach Kategorie zurück.
    Nützlich für gruppierte Streamlit-Selectboxen."""
    grouped = {kat: {} for kat in KATEGORIEN}
    for ticker, info in SYMBOLS.items():
        kat = info["kategorie"]
        if kat in grouped:
            grouped[kat][ticker] = info
    # Leere Kategorien entfernen
    return {k: v for k, v in grouped.items() if v}


def search_symbols(query: str) -> dict:
    """Sucht Symbole nach Ticker oder Name (case-insensitive).
    Nützlich für eine Suchbox."""
    q = query.lower().strip()
    return {
        k: v for k, v in SYMBOLS.items()
        if q in k.lower() or q in v["name"].lower()
        or q in v.get("beschreibung", "").lower()
    }
