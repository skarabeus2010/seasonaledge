"""
bulk_load_supabase.py — Full History Load: alle Ticker nach Supabase
=====================================================================
Laedt vollstaendige Kurshistorie (Yahoo + Stooq-Fallback) und schreibt
OHLCV + log_return + tdom + tdoy nach Supabase.

Nutzt shared/yahoo_downloader.py (adj_factor, Stooq-Fallback) direkt.

Aufruf:
  py bulk_load_supabase.py                    # Alle 263 Ticker (skip wenn >80% da)
  py bulk_load_supabase.py --force            # Alles neu laden (kein Skip)
  py bulk_load_supabase.py --ticker ETH-USD BTC-USD
  py bulk_load_supabase.py --category Krypto
  py bulk_load_supabase.py --missing-only     # Nur Ticker ohne DB-Daten
  py bulk_load_supabase.py --audit            # Nur Uebersicht (kein Upload)
"""

import sys
import os
import pathlib
import argparse
import time
import gc

_project_dir = str(pathlib.Path(__file__).resolve().parent.parent)
if _project_dir not in sys.path:
    sys.path.insert(0, _project_dir)

# Windows Console Encoding
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import numpy as np
import pandas as pd
from shared.symbols import SYMBOLS
from shared.yahoo_downloader import download_data, preprocess


# ── Supabase ─────────────────────────────────────────────────────────────────

def _get_supabase():
    """Lazy Supabase-Client (liest Credentials aus secrets.toml oder env)."""
    try:
        from shared.supabase_client import get_client
        return get_client()
    except Exception:
        pass
    # Fallback: direkt laden
    try:
        import tomllib
        with open(os.path.join(_project_dir, ".streamlit", "secrets.toml"), "rb") as f:
            _secrets = tomllib.load(f)
        url = _secrets["SUPABASE_URL"]
        key = _secrets["SUPABASE_KEY"]
    except Exception:
        url = os.environ.get("SUPABASE_URL", "")
        key = os.environ.get("SUPABASE_KEY", "")
    if not url or not key:
        print("FEHLER: SUPABASE_URL / SUPABASE_KEY nicht gefunden!")
        sys.exit(1)
    from supabase import create_client
    return create_client(url, key)


_sb = None

def sb():
    global _sb
    if _sb is None:
        _sb = _get_supabase()
    return _sb


# ── Bestandspruefung ─────────────────────────────────────────────────────────

def check_existing(ticker):
    """Prueft Supabase-Bestand: count, first_date, last_date, lr_null_pct."""
    try:
        client = sb()
        first = client.table("prices").select("date").eq("ticker", ticker) \
            .order("date", desc=False).limit(1).execute()
        last = client.table("prices").select("date").eq("ticker", ticker) \
            .order("date", desc=True).limit(1).execute()
        count = client.table("prices").select("id", count="exact") \
            .eq("ticker", ticker).execute()

        first_date = first.data[0]["date"] if first.data else None
        last_date = last.data[0]["date"] if last.data else None
        n_rows = count.count if count.count else 0

        # log_return NULL-Quote (letzte 50 Zeilen)
        lr = client.table("prices").select("log_return") \
            .eq("ticker", ticker).order("date", desc=True).limit(50).execute()
        lr_null = sum(1 for r in (lr.data or []) if r.get("log_return") is None)
        lr_pct = (lr_null / len(lr.data) * 100) if lr.data else 0

        return {"count": n_rows, "first": first_date, "last": last_date,
                "lr_null_pct": lr_pct}
    except Exception as e:
        return {"count": 0, "error": str(e)}


# ── Upload ───────────────────────────────────────────────────────────────────

def upload_ticker(ticker, df, source="yahoo"):
    """Schreibt DataFrame nach Supabase: OHLCV + log_return + tdom + tdoy.

    Args:
        df: Preprocessed DataFrame (nach preprocess(), hat alle Spalten).
    Returns:
        int: Anzahl geschriebener Rows.
    """
    if df is None or df.empty:
        return 0

    records = []
    for idx, row in df.iterrows():
        rec = {
            "ticker": ticker,
            "date": idx.strftime("%Y-%m-%d") if hasattr(idx, 'strftime') else str(idx),
            "close": round(float(row["Close"]), 4),
            "source": source,
        }
        for col in ["Open", "High", "Low"]:
            if col in row and pd.notna(row[col]):
                rec[col.lower()] = round(float(row[col]), 4)
        if "Volume" in row and pd.notna(row["Volume"]):
            rec["volume"] = int(row["Volume"])
        if "log_return" in row and pd.notna(row["log_return"]):
            rec["log_return"] = round(float(row["log_return"]), 8)
        if "tdom" in row and pd.notna(row["tdom"]):
            rec["tdom"] = int(row["tdom"])
        if "tdoy" in row and pd.notna(row["tdoy"]):
            rec["tdoy"] = int(row["tdoy"])
        records.append(rec)

    # Batch-Upsert in Chunks
    uploaded = 0
    chunk_size = 500
    for i in range(0, len(records), chunk_size):
        chunk = records[i:i + chunk_size]
        try:
            sb().table("prices").upsert(chunk, on_conflict="ticker,date").execute()
            uploaded += len(chunk)
        except Exception as e:
            print(f"    Upload-Fehler Chunk {i}: {e}")
    return uploaded


# ── Hauptprogramm ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Bulk Load: Full History nach Supabase")
    parser.add_argument("--ticker", nargs="+", help="Nur bestimmte Ticker laden")
    parser.add_argument("--category", help="Nur Kategorie (z.B. Krypto, US-Aktien)")
    parser.add_argument("--force", action="store_true", help="Alles neu laden (kein Skip)")
    parser.add_argument("--missing-only", action="store_true",
                        help="Nur Ticker ohne DB-Daten laden")
    parser.add_argument("--audit", action="store_true",
                        help="Nur Uebersicht anzeigen (kein Upload)")
    parser.add_argument("--skip-threshold", type=float, default=0.8,
                        help="Skip wenn DB >= X%% der Yahoo-Daten hat (default: 0.8)")
    args = parser.parse_args()

    # Ticker-Liste
    if args.ticker:
        tickers = args.ticker
    elif args.category:
        tickers = [t for t, info in SYMBOLS.items()
                    if info.get("kategorie", "").lower() == args.category.lower()]
        if not tickers:
            print(f"Keine Ticker fuer Kategorie '{args.category}' gefunden.")
            print(f"Verfuegbare: {sorted(set(i.get('kategorie','') for i in SYMBOLS.values()))}")
            return
    else:
        tickers = list(SYMBOLS.keys())

    print("=" * 90)
    print(f"  SeasonAlpha Bulk Load — {len(tickers)} Ticker")
    if args.audit:
        print("  MODUS: Audit (nur Uebersicht, kein Upload)")
    if args.force:
        print("  MODUS: Force (kein Skip)")
    print("=" * 90)

    stats = {"ok": 0, "skip": 0, "fail": 0, "rows": 0}
    audit_results = []

    for i, ticker in enumerate(tickers, 1):
        info = SYMBOLS.get(ticker, {})
        name = info.get("name", ticker)
        kat = info.get("kategorie", "?")

        print(f"\n[{i}/{len(tickers)}] {ticker} — {name} ({kat})")

        # 1. Supabase-Bestand pruefen
        existing = check_existing(ticker)
        db_count = existing.get("count", 0)
        db_first = existing.get("first", "-")
        db_last = existing.get("last", "-")
        lr_null = existing.get("lr_null_pct", 0)

        print(f"    DB: {db_count:>6,} Zeilen ({db_first} -> {db_last})"
              f" | LR-NULL: {lr_null:.0f}%")

        # 2. Yahoo Download
        print(f"    Yahoo download ...", end=" ", flush=True)
        t0 = time.time()
        raw_df = download_data(ticker, period="max", timeout=20)
        dt = time.time() - t0

        if raw_df is None or raw_df.empty:
            print(f"KEINE DATEN ({dt:.1f}s)")
            stats["fail"] += 1
            audit_results.append({"ticker": ticker, "kat": kat,
                                  "yh": 0, "db": db_count, "status": "NO_DATA"})
            continue

        yh_count = len(raw_df)
        yh_first = str(raw_df.index[0].date())
        yh_last = str(raw_df.index[-1].date())
        yh_years = raw_df.index[-1].year - raw_df.index[0].year + 1
        print(f"{yh_count:,} Zeilen ({yh_first} -> {yh_last}) = {yh_years}J ({dt:.1f}s)")

        audit_results.append({
            "ticker": ticker, "kat": kat,
            "yh": yh_count, "yh_first": yh_first, "yh_last": yh_last,
            "db": db_count, "db_first": db_first, "db_last": db_last,
            "lr_null": lr_null,
            "gap": yh_count - db_count,
        })

        # Audit-Modus: kein Upload
        if args.audit:
            continue

        # 3. Skip-Logik
        if not args.force and db_count > 0:
            ratio = db_count / yh_count if yh_count > 0 else 0
            if args.missing_only:
                print(f"    SKIP (bereits in DB, {ratio:.0%})")
                stats["skip"] += 1
                continue
            if ratio >= args.skip_threshold and lr_null < 20:
                print(f"    SKIP ({ratio:.0%} vorhanden, LR-NULL {lr_null:.0f}%)")
                stats["skip"] += 1
                continue
            print(f"    RELOAD ({ratio:.0%} vorhanden, Ziel: {args.skip_threshold:.0%})")

        # 4. Preprocess (log_return, tdom, tdoy)
        df = preprocess(raw_df)
        if df is None or df.empty:
            print(f"    Preprocess fehlgeschlagen")
            stats["fail"] += 1
            continue

        # 5. Upload
        print(f"    Upload {len(df):,} Zeilen ...", end=" ", flush=True)
        t0 = time.time()
        n = upload_ticker(ticker, df)
        dt = time.time() - t0
        print(f"OK ({n:,} Rows, {dt:.1f}s)")

        stats["ok"] += 1
        stats["rows"] += n

        # Memory freigeben
        del raw_df, df
        gc.collect()

        # Rate-Limit
        time.sleep(1.0)

    # ── Zusammenfassung ──────────────────────────────────────────────────────

    print("\n" + "=" * 90)

    if args.audit:
        # Audit-Tabelle
        print(f"\n{'Ticker':<12} {'Kat':<12} {'Yahoo':>7} {'Supabase':>8} "
              f"{'Luecke':>7} {'LR-NULL':>7} {'Yahoo Start':<12} {'DB Start':<12}")
        print("-" * 90)
        for r in sorted(audit_results, key=lambda x: x.get("gap", 0), reverse=True):
            gap = r.get("gap", 0)
            marker = " <<<" if gap > 500 else ""
            print(f"{r['ticker']:<12} {r['kat']:<12} {r['yh']:>7,} {r['db']:>8,} "
                  f"{gap:>7,} {r.get('lr_null',0):>6.0f}% "
                  f"{r.get('yh_first','-'):<12} {r.get('db_first','-'):<12}{marker}")

        n_gap = sum(1 for r in audit_results if r.get("gap", 0) > 500)
        n_lr = sum(1 for r in audit_results if r.get("lr_null", 0) > 20)
        print(f"\nLuecken >500 Zeilen: {n_gap} Ticker")
        print(f"LR-NULL >20%%: {n_lr} Ticker")
    else:
        print(f"  FERTIG!")
        print(f"  Geladen:       {stats['ok']}")
        print(f"  Uebersprungen: {stats['skip']}")
        print(f"  Fehler:        {stats['fail']}")
        print(f"  Gesamt-Rows:   {stats['rows']:,}")

    print("=" * 90)


if __name__ == "__main__":
    main()
