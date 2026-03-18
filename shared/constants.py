"""
SeasonalEdge — Zentrale Konstanten

Verwendung:
  from shared.constants import SMOOTHING_WINDOW, TRADING_DAYS_PER_YEAR
"""

# ── Berechnung ───────────────────────────────────────────────
SMOOTHING_WINDOW = 5
TRADING_DAYS_PER_YEAR = 252
BASE_VALUE = 100  # Normalisierte Renditen starten bei 100

# ── Cache ────────────────────────────────────────────────────
CACHE_TTL_SECONDS = 6 * 3600  # 6 Stunden
CACHE_MAX_TICKERS = 500

# ── Rate Limits ──────────────────────────────────────────────
YAHOO_MAX_REQUESTS_PER_HOUR = 2000
STOOQ_MAX_REQUESTS_PER_HOUR = 500

# ── Download Manager ─────────────────────────────────────────
DEFAULT_START_DATE = "1950-01-01"
BATCH_WORKERS = 4

# ── Stooq Ticker Mapping ────────────────────────────────────
STOOQ_TICKER_MAP = {
    "^DJI":   "^dji",
    "^GSPC":  "^spx",
    "^GDAXI": "^dax",
    "^DAX":   "^dax",
}

# ── Presidential Cycle ───────────────────────────────────────
PRESIDENTIAL_CYCLE_BASE_YEAR = 2024  # Wahljahr als Referenz

# ── Streamlit ────────────────────────────────────────────────
PAGE_ICON = "📊"
PAGE_TITLE = "SeasonalEdge"
