"""
SeasonAlpha — Zentraler Download-Manager

Architektur:
  TickerQueue   — priorisierte Download-Warteschlange
  RateLimiter   — Yahoo: max 2000 Req/h, Stooq: max 500 Req/h
  CacheLayer    — lokaler In-Memory-Cache (TTL 6h)
  DBSync        — schreibt fertige Daten nach Supabase

Verwendung:
  from shared.download_manager import DownloadManager
  dm = DownloadManager()
  df = dm.get(ticker="SPY", start="1993-01-01")
  results = dm.batch(tickers=["SPY", "QQQ"], workers=4)
  status = dm.status()

Batch-Modus (CLI / GitHub Action):
  python -m shared.download_manager --batch-all
"""

import time
import threading
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta

import pandas as pd

from shared.logger import app_logger, error_logger

# ── Lazy Import: yahoo_downloader existiert evtl. noch nicht lokal ───
try:
    from shared.yahoo_downloader import download_data, preprocess
except ImportError:
    download_data = None
    preprocess = None
    app_logger.warning("yahoo_downloader nicht gefunden — Downloads deaktiviert")

try:
    from shared.supabase_client import upsert_prices
except ImportError:
    upsert_prices = None


# ── Rate Limiter ─────────────────────────────────────────────

class RateLimiter:
    """Thread-safe Token-Bucket Rate Limiter."""

    def __init__(self, max_requests: int, period_seconds: int = 3600):
        self.max_requests = max_requests
        self.period = period_seconds
        self._timestamps: list[float] = []
        self._lock = threading.Lock()

    def acquire(self) -> None:
        """Blockiert bis ein Request erlaubt ist."""
        while True:
            with self._lock:
                now = time.time()
                # Alte Timestamps entfernen
                self._timestamps = [
                    t for t in self._timestamps if now - t < self.period
                ]
                if len(self._timestamps) < self.max_requests:
                    self._timestamps.append(now)
                    return
            # Warten bis ältester Eintrag abläuft
            time.sleep(0.5)


# ── In-Memory Cache (TTL) ───────────────────────────────────

class CacheLayer:
    """Einfacher TTL-basierter In-Memory-Cache."""

    def __init__(self, ttl_seconds: int = 6 * 3600):
        self.ttl = ttl_seconds
        self._data: OrderedDict[str, tuple[datetime, pd.DataFrame]] = OrderedDict()
        self._lock = threading.Lock()
        self._max_size = 500  # Max Ticker im Cache

    def get(self, key: str) -> pd.DataFrame | None:
        with self._lock:
            if key in self._data:
                ts, df = self._data[key]
                if datetime.now() - ts < timedelta(seconds=self.ttl):
                    # Move to end (LRU)
                    self._data.move_to_end(key)
                    return df.copy()
                else:
                    del self._data[key]
        return None

    def put(self, key: str, df: pd.DataFrame) -> None:
        with self._lock:
            self._data[key] = (datetime.now(), df.copy())
            # Evict älteste wenn zu voll
            while len(self._data) > self._max_size:
                self._data.popitem(last=False)

    def clear(self) -> None:
        with self._lock:
            self._data.clear()


# ── Prioritäten ──────────────────────────────────────────────

PRIORITY_LIVE = 1       # Ticker gerade im Frontend angefragt
PRIORITY_TOP100 = 2     # Top-100 Ticker (täglich)
PRIORITY_BATCH = 3      # Alle weiteren (wöchentlich)


# ── Download Manager ─────────────────────────────────────────

class DownloadManager:
    """Zentraler Download-Manager mit Cache, Rate-Limiting und DB-Sync."""

    def __init__(self):
        self.yahoo_limiter = RateLimiter(max_requests=2000, period_seconds=3600)
        self.stooq_limiter = RateLimiter(max_requests=500, period_seconds=3600)
        self.cache = CacheLayer(ttl_seconds=6 * 3600)
        self._stats = {"queued": 0, "done": 0, "failed": 0}
        self._lock = threading.Lock()

    def get(
        self,
        ticker: str,
        start: str = "1950-01-01",
        priority: int = PRIORITY_LIVE,
    ) -> pd.DataFrame | None:
        """
        Einzelnen Ticker laden.
        1. Cache prüfen
        2. Yahoo downloaden (mit Rate-Limit)
        3. In Cache + optional DB schreiben
        """
        # 1. Cache
        cached = self.cache.get(ticker)
        if cached is not None:
            app_logger.info(f"Cache-Hit: {ticker}")
            return cached

        # 2. Download
        if download_data is None:
            error_logger.error("yahoo_downloader nicht verfügbar")
            return None

        try:
            self.yahoo_limiter.acquire()
            app_logger.info(f"Download gestartet: {ticker} (Priorität {priority})")
            df = download_data(ticker, start=start)

            if df is None or df.empty:
                app_logger.warning(f"Keine Daten für {ticker}")
                with self._lock:
                    self._stats["failed"] += 1
                return None

            if preprocess:
                df = preprocess(df)

            # 3. Cache
            self.cache.put(ticker, df)

            # 4. DB-Sync (optional, non-blocking)
            self._sync_to_db(ticker, df)

            with self._lock:
                self._stats["done"] += 1

            app_logger.info(f"Download abgeschlossen: {ticker} ({len(df)} Zeilen)")
            return df

        except Exception as e:
            error_logger.error(f"Download fehlgeschlagen: {ticker} — {e}", exc_info=True)
            with self._lock:
                self._stats["failed"] += 1
            return None

    def batch(
        self,
        tickers: list[str],
        workers: int = 4,
        start: str = "1950-01-01",
        priority: int = PRIORITY_BATCH,
    ) -> dict[str, pd.DataFrame | None]:
        """Mehrere Ticker parallel downloaden."""
        results: dict[str, pd.DataFrame | None] = {}

        with self._lock:
            self._stats["queued"] = len(tickers)

        app_logger.info(f"Batch-Download gestartet: {len(tickers)} Ticker, {workers} Worker")

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(self.get, ticker, start, priority): ticker
                for ticker in tickers
            }
            for future in as_completed(futures):
                ticker = futures[future]
                try:
                    results[ticker] = future.result()
                except Exception as e:
                    error_logger.error(f"Batch-Fehler: {ticker} — {e}", exc_info=True)
                    results[ticker] = None

        app_logger.info(
            f"Batch abgeschlossen: {self._stats['done']} OK, "
            f"{self._stats['failed']} fehlgeschlagen"
        )
        return results

    def status(self) -> dict:
        """Aktueller Status des Download-Managers."""
        with self._lock:
            return dict(self._stats)

    def _sync_to_db(self, ticker: str, df: pd.DataFrame) -> None:
        """Daten nach Supabase schreiben (stilles Fallback)."""
        if upsert_prices is None:
            return
        try:
            records = []
            for _, row in df.iterrows():
                record = {
                    "ticker": ticker,
                    "date": row.get("Date", row.name).strftime("%Y-%m-%d")
                    if hasattr(row.get("Date", row.name), "strftime")
                    else str(row.get("Date", row.name)),
                    "close": float(row["Close"]),
                    "source": "yahoo",
                }
                for col in ["Open", "High", "Low"]:
                    if col in row and pd.notna(row[col]):
                        record[col.lower()] = float(row[col])
                if "Volume" in row and pd.notna(row["Volume"]):
                    record["volume"] = int(row["Volume"])
                records.append(record)

            if records:
                upsert_prices(records)
        except Exception as e:
            # DB-Sync darf App nicht crashen
            error_logger.error(f"DB-Sync fehlgeschlagen: {ticker} — {e}", exc_info=True)


# ── CLI Batch-Modus ──────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="SeasonAlpha Download Manager")
    parser.add_argument("--batch-all", action="store_true", help="Alle Ticker updaten")
    parser.add_argument("--tickers", nargs="+", help="Bestimmte Ticker updaten")
    parser.add_argument("--workers", type=int, default=4, help="Anzahl Worker-Threads")
    args = parser.parse_args()

    dm = DownloadManager()

    if args.batch_all:
        try:
            from shared.symbols import ALL_TICKERS
            tickers = ALL_TICKERS
        except ImportError:
            tickers = ["SPY", "QQQ", "DIA", "IWM", "^GSPC", "^DJI", "^IXIC"]
            app_logger.warning("symbols.py nicht gefunden — verwende Standard-Ticker")
        dm.batch(tickers=tickers, workers=args.workers)
    elif args.tickers:
        dm.batch(tickers=args.tickers, workers=args.workers)
    else:
        parser.print_help()

    print(f"Status: {dm.status()}")
