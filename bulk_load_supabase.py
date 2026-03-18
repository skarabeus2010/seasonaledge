"""
bulk_load_supabase.py — Massiver Initial-Load aller Ticker nach Supabase
=========================================================================
Lädt historische Kursdaten von Yahoo Finance + Stooq-Fallback
und schreibt sie in die Supabase `prices` Tabelle.

Aufruf:  py bulk_load_supabase.py
"""

import io
import os
import sys
import time
import datetime

import numpy as np
import requests

# Fix Windows Console Encoding
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")
import pandas as pd
from supabase import create_client

# ── Supabase Credentials ─────────────────────────────────────────────────────
# Versuche erst Streamlit Secrets, dann Umgebungsvariablen
try:
    import tomllib
    with open(os.path.join(os.path.dirname(__file__), ".streamlit", "secrets.toml"), "rb") as f:
        _secrets = tomllib.load(f)
    SUPABASE_URL = _secrets["SUPABASE_URL"]
    SUPABASE_KEY = _secrets["SUPABASE_KEY"]
except Exception:
    SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ SUPABASE_URL / SUPABASE_KEY nicht gefunden!")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ── Alle Ticker aus symbols.py ────────────────────────────────────────────────

SYMBOLS = {
    # US-Indizes
    "^GSPC":      "S&P 500",
    "^DJI":       "Dow Jones",
    "^IXIC":      "Nasdaq Composite",
    "^NDX":       "Nasdaq 100",
    "^RUT":       "Russell 2000",
    "^VIX":       "VIX",
    # US-ETFs
    "SPY":        "SPDR S&P 500 ETF",
    "QQQ":        "Invesco Nasdaq 100 ETF",
    "IWM":        "iShares Russell 2000 ETF",
    "DIA":        "SPDR Dow Jones ETF",
    "TLT":        "iShares 20+ Year Treasury",
    "GLD":        "SPDR Gold ETF",
    "SLV":        "iShares Silver ETF",
    "USO":        "United States Oil ETF",
    "XLF":        "Financial Select ETF",
    "XLK":        "Technology Select ETF",
    "XLE":        "Energy Select ETF",
    "XLV":        "Health Care Select ETF",
    "XLU":        "Utilities Select ETF",
    # US-Aktien
    "AAPL":       "Apple",
    "MSFT":       "Microsoft",
    "NVDA":       "Nvidia",
    "AMZN":       "Amazon",
    "GOOGL":      "Alphabet",
    "META":       "Meta Platforms",
    "TSLA":       "Tesla",
    "JPM":        "JPMorgan Chase",
    "XOM":        "ExxonMobil",
    # EU-Indizes
    "^GDAXI":     "DAX 40",
    "^MDAXI":     "MDAX",
    "^STOXX50E":  "Euro Stoxx 50",
    "^FTSE":      "FTSE 100",
    "^FCHI":      "CAC 40",
    "^SSMI":      "SMI (Schweiz)",
    # Asien-Indizes
    "^N225":      "Nikkei 225",
    "^HSI":       "Hang Seng",
    "^KS11":      "KOSPI",
    # Rohstoffe
    "GC=F":       "Gold Futures",
    "SI=F":       "Silber Futures",
    "CL=F":       "WTI Rohöl",
    "BZ=F":       "Brent Rohöl",
    "NG=F":       "Natural Gas",
    "ZC=F":       "Corn (Mais)",
    "ZW=F":       "Wheat (Weizen)",
    # Futures
    "ES=F":       "E-Mini S&P 500",
    "NQ=F":       "E-Mini Nasdaq 100",
    # Krypto
    "BTC-USD":    "Bitcoin",
    "ETH-USD":    "Ethereum",
    "SOL-USD":    "Solana",
    # FX
    "EURUSD=X":   "EUR/USD",
    "GBPUSD=X":   "GBP/USD",
    "USDJPY=X":   "USD/JPY",
    "USDCHF=X":   "USD/CHF",
}

# ── Stooq-Mapping für Langzeitdaten (ab ~1928) ───────────────────────────────
# Stooq liefert für bestimmte Indizes viel längere Historien als Yahoo
STOOQ_MAP = {
    "^GSPC":    "^spx",
    "^DJI":     "^dji",
    "^GDAXI":   "^dax",
    "^FTSE":    "^ukx",
    "^FCHI":    "^cac",
    "^N225":    "^nkx",
    "^STOXX50E": "^sx5e",
    "^SSMI":    "^smi",
    "GC=F":     "gc.f",
    "SI=F":     "si.f",
    "CL=F":     "cl.f",
    "NG=F":     "ng.f",
    "EURUSD=X": "eurusd",
    "GBPUSD=X": "gbpusd",
    "USDJPY=X": "usdjpy",
    "USDCHF=X": "usdchf",
}

# Priorisierte Ticker: Diese zuerst laden (Langzeitdaten)
PRIORITY_TICKERS = ["^DJI", "^GSPC", "^GDAXI", "^FTSE", "^N225", "GC=F", "CL=F", "EURUSD=X"]


# ── Download-Funktionen ──────────────────────────────────────────────────────

_YAHOO_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
}

def download_yahoo(ticker: str) -> pd.DataFrame | None:
    """Lädt maximale Historie von Yahoo Finance JSON-API (v8/chart)."""
    params = {
        "interval": "1d",
        "period1":  0,
        "period2":  int(time.time()),
    }
    for base in [
        "https://query1.finance.yahoo.com/v8/finance/chart/",
        "https://query2.finance.yahoo.com/v8/finance/chart/",
    ]:
        try:
            resp = requests.get(
                base + ticker.upper(),
                headers=_YAHOO_HEADERS,
                params=params,
                timeout=30,
                allow_redirects=True,
            )
            if resp.status_code != 200:
                continue
            data = resp.json()
            chart = data.get("chart", {})
            if chart.get("error") is not None or not chart.get("result"):
                continue

            result     = chart["result"][0]
            timestamps = result.get("timestamp", [])
            if not timestamps:
                continue

            quotes   = result["indicators"]["quote"][0]
            adj_list = result["indicators"].get("adjclose", [{}])
            adjclose = adj_list[0].get("adjclose") if adj_list else None
            close_data = adjclose if adjclose is not None else quotes.get("close")

            dates = pd.to_datetime(timestamps, unit="s", utc=True).tz_localize(None)
            df = pd.DataFrame({
                "Date":   dates,
                "Open":   quotes.get("open",   [np.nan] * len(timestamps)),
                "High":   quotes.get("high",   [np.nan] * len(timestamps)),
                "Low":    quotes.get("low",    [np.nan] * len(timestamps)),
                "Close":  close_data,
                "Volume": quotes.get("volume", [np.nan] * len(timestamps)),
            })
            for col in ["Open", "High", "Low", "Close"]:
                df[col] = pd.to_numeric(df[col], errors="coerce")
            df["Volume"] = pd.to_numeric(df["Volume"], errors="coerce").fillna(0).astype(int)
            df = df.dropna(subset=["Close"])
            df = df[df["Close"] > 0]
            if len(df) > 0:
                return df
        except Exception as e:
            print(f"    ⚠️  Yahoo Fehler für {ticker}: {e}")
            continue
    return None


def download_stooq(stooq_ticker: str) -> pd.DataFrame | None:
    """Lädt Langzeitdaten von Stooq.com (CSV)."""
    try:
        url = f"https://stooq.com/q/d/l/?s={stooq_ticker}&i=d"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=30)
        if resp.status_code != 200 or len(resp.text) < 100:
            return None
        df = pd.read_csv(io.StringIO(resp.text), parse_dates=["Date"])
        if "Close" not in df.columns or len(df) < 10:
            return None
        df = df.dropna(subset=["Close"])
        df = df[df["Close"] > 0]
        # Stooq hat manchmal keine Volume-Spalte
        if "Volume" not in df.columns:
            df["Volume"] = None
        return df
    except Exception as e:
        print(f"    ⚠️  Stooq Fehler für {stooq_ticker}: {e}")
        return None


def merge_yahoo_stooq(yahoo_df: pd.DataFrame | None, stooq_df: pd.DataFrame | None) -> pd.DataFrame | None:
    """Merged Yahoo + Stooq Daten: Stooq füllt ältere Lücken auf."""
    if yahoo_df is None and stooq_df is None:
        return None
    if yahoo_df is None:
        return stooq_df
    if stooq_df is None:
        return yahoo_df

    # Stooq-Daten die VOR dem ältesten Yahoo-Datum liegen
    yahoo_min_date = yahoo_df["Date"].min()
    stooq_older = stooq_df[stooq_df["Date"] < yahoo_min_date].copy()

    if len(stooq_older) == 0:
        return yahoo_df

    # Spalten angleichen
    common_cols = ["Date", "Open", "High", "Low", "Close", "Volume"]
    for col in common_cols:
        if col not in stooq_older.columns:
            stooq_older[col] = None
        if col not in yahoo_df.columns:
            yahoo_df[col] = None

    merged = pd.concat([stooq_older[common_cols], yahoo_df[common_cols]], ignore_index=True)
    merged = merged.sort_values("Date").drop_duplicates(subset=["Date"], keep="last")
    return merged


# ── Supabase Upload ──────────────────────────────────────────────────────────

def upload_to_supabase(ticker: str, df: pd.DataFrame, source: str = "yahoo") -> int:
    """Lädt DataFrame in Supabase `prices` Tabelle. Returns: Anzahl Rows."""
    if df is None or len(df) == 0:
        return 0

    records = []
    for _, row in df.iterrows():
        rec = {
            "ticker": ticker,
            "date":   row["Date"].strftime("%Y-%m-%d"),
            "close":  round(float(row["Close"]), 4),
            "source": source,
        }
        if pd.notna(row.get("Open")):
            rec["open"] = round(float(row["Open"]), 4)
        if pd.notna(row.get("High")):
            rec["high"] = round(float(row["High"]), 4)
        if pd.notna(row.get("Low")):
            rec["low"] = round(float(row["Low"]), 4)
        if pd.notna(row.get("Volume")):
            rec["volume"] = int(row["Volume"])
        records.append(rec)

    # Batch-Upsert in Chunks von 1000
    uploaded = 0
    chunk_size = 1000
    for i in range(0, len(records), chunk_size):
        chunk = records[i:i + chunk_size]
        try:
            supabase.table("prices").upsert(
                chunk, on_conflict="ticker,date"
            ).execute()
            uploaded += len(chunk)
        except Exception as e:
            print(f"    ❌ Upload-Fehler bei Chunk {i}: {e}")
    return uploaded


# ── Bestandsprüfung ──────────────────────────────────────────────────────────

def check_existing(ticker: str) -> dict | None:
    """Prüft ob und wie viele Daten für einen Ticker bereits in Supabase liegen."""
    try:
        # Anzahl Rows + Datum-Range abfragen
        result = supabase.table("prices").select("date") \
            .eq("ticker", ticker) \
            .order("date", desc=False).limit(1).execute()
        first_date = result.data[0]["date"] if result.data else None

        result2 = supabase.table("prices").select("date") \
            .eq("ticker", ticker) \
            .order("date", desc=True).limit(1).execute()
        last_date = result2.data[0]["date"] if result2.data else None

        count_result = supabase.table("prices").select("id", count="exact") \
            .eq("ticker", ticker).execute()
        count = count_result.count if count_result.count else 0

        if count > 0:
            return {"count": count, "first": first_date, "last": last_date}
        return None
    except Exception:
        return None


# ── Hauptprogramm ────────────────────────────────────────────────────────────

MIN_ROWS_THRESHOLD = 100  # Weniger als 100 Rows = nochmal laden

def main():
    print("=" * 70)
    print("🚀 SeasonalEdge — Bulk Data Load → Supabase")
    print(f"   {len(SYMBOLS)} Ticker | {datetime.datetime.now():%Y-%m-%d %H:%M}")
    print("=" * 70)

    # Priorisierte Ticker zuerst, dann den Rest
    ordered = PRIORITY_TICKERS + [t for t in SYMBOLS if t not in PRIORITY_TICKERS]

    stats = {"ok": 0, "fail": 0, "rows": 0, "skipped": 0}

    for idx, ticker in enumerate(ordered, 1):
        name = SYMBOLS[ticker]
        print(f"\n[{idx}/{len(ordered)}] {ticker} — {name}")

        # 0. Prüfe ob Daten schon in Supabase liegen
        existing = check_existing(ticker)
        if existing and existing["count"] >= MIN_ROWS_THRESHOLD:
            print(f"    ⏭️  SKIP — bereits {existing['count']:,} Rows in DB "
                  f"({existing['first']} → {existing['last']})")
            stats["skipped"] += 1
            stats["rows"] += existing["count"]
            continue

        # 1. Yahoo Download
        print("    📥 Yahoo Finance ...", end=" ", flush=True)
        yahoo_df = download_yahoo(ticker)
        if yahoo_df is not None:
            y_start = yahoo_df["Date"].min().strftime("%Y-%m-%d")
            y_end = yahoo_df["Date"].max().strftime("%Y-%m-%d")
            print(f"✅ {len(yahoo_df)} Tage ({y_start} → {y_end})")
        else:
            print("❌ keine Daten")

        # 2. Stooq Fallback (für Langzeitdaten)
        stooq_df = None
        if ticker in STOOQ_MAP:
            stooq_ticker = STOOQ_MAP[ticker]
            print(f"    📥 Stooq ({stooq_ticker}) ...", end=" ", flush=True)
            stooq_df = download_stooq(stooq_ticker)
            if stooq_df is not None:
                s_start = stooq_df["Date"].min().strftime("%Y-%m-%d")
                s_end = stooq_df["Date"].max().strftime("%Y-%m-%d")
                print(f"✅ {len(stooq_df)} Tage ({s_start} → {s_end})")
            else:
                print("❌ keine Daten")
            time.sleep(1)  # Rate-Limit Stooq

        # 3. Merge
        merged = merge_yahoo_stooq(yahoo_df, stooq_df)
        if merged is not None:
            source = "yahoo+stooq" if stooq_df is not None and yahoo_df is not None else (
                "stooq" if yahoo_df is None else "yahoo"
            )
            m_start = merged["Date"].min().strftime("%Y-%m-%d")
            m_end = merged["Date"].max().strftime("%Y-%m-%d")
            years = (merged["Date"].max() - merged["Date"].min()).days / 365.25
            print(f"    📊 Merged: {len(merged)} Tage ({m_start} → {m_end}) = {years:.0f} Jahre")

            # 4. Upload
            print(f"    ☁️  Upload nach Supabase ...", end=" ", flush=True)
            n = upload_to_supabase(ticker, merged, source)
            print(f"✅ {n} Rows")
            stats["ok"] += 1
            stats["rows"] += n
        else:
            print(f"    ❌ Keine Daten verfügbar — übersprungen")
            stats["fail"] += 1

        # Rate-Limit Yahoo
        time.sleep(1.5)

    # Zusammenfassung
    print("\n" + "=" * 70)
    print(f"✅ FERTIG!")
    print(f"   Neu geladen:    {stats['ok']}")
    print(f"   Übersprungen:   {stats['skipped']} (bereits in DB)")
    print(f"   Fehlgeschlagen: {stats['fail']}")
    print(f"   Gesamt-Rows:    {stats['rows']:,}")
    print("=" * 70)


if __name__ == "__main__":
    main()
