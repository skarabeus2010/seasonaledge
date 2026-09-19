"""
SeasonAlpha - Data Layer (Supabase-First)
==========================================
Lädt Kursdaten primär aus Supabase (schnell, ~0.5s).
Fallback auf Yahoo Finance + Stooq (langsam, ~3-7s).

Alle Pages importieren: from shared.data import download_data, preprocess
"""
from __future__ import annotations

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from shared.yahoo_downloader import (
    download_data as _yahoo_download,
    preprocess,
)

# Maximales Alter der Supabase-Daten bevor Yahoo-Fallback greift
_MAX_STALE_DAYS = 5  # Wochenende + Feiertage abdecken


def _load_from_supabase(ticker: str) -> pd.DataFrame | None:
    """
    Versucht Kursdaten aus Supabase zu laden.

    Returns:
        DataFrame im Yahoo-Format (DatetimeIndex, OHLCV) oder None bei Fehler.
    """
    try:
        from shared.supabase_client import fetch_prices
        records = fetch_prices(ticker)

        if not records or len(records) < 50:
            return None

        # Jahresspanne pruefen: Saisonalanalyse braucht mindestens 3 Jahre Daten.
        # Nightly-Refresh schreibt nur 5 Tage → Supabase kann nur wenige Monate haben.
        _dates = [r.get("date", "") for r in records if r.get("date")]
        if _dates:
            _min_year = int(min(_dates)[:4])
            _max_year = int(max(_dates)[:4])
            if _max_year - _min_year < 3:
                return None  # Zu wenig Historie → Yahoo-Fallback

        df = pd.DataFrame(records)

        # Spalten normalisieren (Supabase: lowercase, Yahoo: Title)
        col_map = {"date": "Date", "open": "Open", "high": "High",
                   "low": "Low", "close": "Close", "volume": "Volume"}
        df = df.rename(columns=col_map)

        if "Close" not in df.columns or "Date" not in df.columns:
            return None

        df["Date"] = pd.to_datetime(df["Date"])
        df = df.set_index("Date").sort_index()
        df.index.name = "Date"

        # Numerische Spalten sicherstellen
        for col in ["Open", "High", "Low", "Close"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        if "Volume" in df.columns:
            df["Volume"] = pd.to_numeric(df["Volume"], errors="coerce").fillna(0).astype(int)
        else:
            df["Volume"] = 0

        # OHLCV + log_return behalten
        keep_cols = [c for c in ["Open", "High", "Low", "Close", "Volume", "log_return"] if c in df.columns]
        df = df[keep_cols].dropna(subset=["Close"])

        # Frische prüfen: Letzter Eintrag < _MAX_STALE_DAYS alt?
        last_date = df.index[-1]
        cutoff = datetime.now() - timedelta(days=_MAX_STALE_DAYS)
        if last_date < pd.Timestamp(cutoff):
            return None  # Zu alt → Yahoo-Fallback

        # OHLC-Qualität prüfen: Open muss für >90% der Zeilen vorhanden sein.
        if "Open" in df.columns:
            open_fill_rate = df["Open"].notna().mean()
            if open_fill_rate < 0.9:
                return None  # Zu viele fehlende Open-Werte → Yahoo-Fallback

        # OHLC-Konsistenz prüfen: Erkennt fehlende Split- ODER Dividend-Adjustierung.
        #
        # Check 1 (Split): Open/Close Ratio > 1.5 oder < 0.67 bei >0.5% der Tage
        # Check 2 (Dividend): Mittlere Intraday-Rendite (Close/Open) zu weit von 0
        #   → Wenn Close dividend-adjustiert ist aber Open nicht, ist Close systematisch
        #     niedriger als Open → mittlere Intraday-Rendite stark negativ (~-3%)
        #   → Bei korrekter Adjustierung: mittlere Intraday < ±0.15%
        if "Open" in df.columns and len(df) > 200:
            ratio = (df["Open"] / df["Close"]).dropna()
            if len(ratio) > 200:
                # Split-Check
                extreme_pct = ((ratio > 1.5) | (ratio < 0.67)).mean()
                if extreme_pct > 0.005:
                    return None

                # Dividend-Check: mittlere Intraday-Rendite
                # Nur NEGATIVE Bias ist verdaechtig (Close div-adjustiert < Open nicht-adjustiert)
                # Positive Werte koennen bei Growth-Stocks legitim sein
                mean_intraday = (1 / ratio - 1).mean() * 100  # = mean(Close/Open - 1)
                if mean_intraday < -0.5:
                    return None  # Dividend-Adjustierung fehlt → Yahoo-Fallback

        return df

    except Exception:
        return None


def download_data(ticker: str, period: str = "max", interval: str = "1d",
                  timeout: int = 15) -> pd.DataFrame:
    """
    Lädt Kursdaten: Supabase-First, Yahoo-Fallback.

    Signatur identisch zu yahoo_downloader.download_data().
    """
    # 1. Supabase versuchen (nur für period="max" oder "5y"+ sinnvoll)
    if period in ("max", "5y", "10y", "20y"):
        db_df = _load_from_supabase(ticker)
        if db_df is not None and len(db_df) > 100:
            return db_df

    # 2. Fallback: Yahoo Finance + Stooq
    return _yahoo_download(ticker, period=period, interval=interval, timeout=timeout)


def append_today_if_missing(df: pd.DataFrame, ticker: str) -> pd.DataFrame:
    """
    Hängt heutigen Intraday-Close an wenn er fehlt.

    Wird auf der Wochentage-Page genutzt damit die goldene
    "Diese Woche"-Linie auch vor dem Intraday-Refresh angezeigt wird.
    Schreibt den Kurs sofort in Supabase (erster User zahlt Yahoo-Call,
    alle weiteren laden aus DB).
    """
    if df is None or df.empty:
        return df

    today = pd.Timestamp(datetime.now().date())

    # Schon vorhanden?
    if today in df.index:
        return df

    # Wochenende?
    if today.weekday() >= 5:
        return df

    # Feiertag? (boersenspezifisch)
    try:
        from shared.exchange_holidays import is_trading_day
        from shared.symbols import get_exchange_for_holidays
        exchange = get_exchange_for_holidays(ticker)
        if not is_trading_day(today.date(), exchange):
            return df
    except Exception:
        pass  # Im Zweifel trotzdem versuchen

    # Yahoo-Call: nur letzter Close
    try:
        fresh = _yahoo_download(ticker, period="5d", timeout=10)
        if fresh is None or fresh.empty:
            return df

        # Normalisiere Index auf Date-only (Yahoo hat manchmal Uhrzeiten)
        fresh.index = fresh.index.normalize()

        if today not in fresh.index:
            return df

        # Nur Close extrahieren, Rest NaN
        last_close = float(fresh.loc[today, "Close"])
        new_row = pd.DataFrame(
            {"Open": [np.nan], "High": [np.nan], "Low": [np.nan],
             "Close": [last_close], "Volume": [0]},
            index=pd.DatetimeIndex([today])
        )
        new_row.index.name = df.index.name

        # An DataFrame anhängen
        df = pd.concat([df, new_row]).sort_index()

        # TDOM/TDOY berechnen
        tdom_val = None
        tdoy_val = None
        try:
            from shared.exchange_holidays import is_trading_day as _is_td
            _exchange = get_exchange_for_holidays(ticker)
            _today_d = today.date() if hasattr(today, 'date') else today

            # TDOY: letzten bekannten Wert aus df + 1
            year_df = df[df.index.year == _today_d.year].sort_index()
            if "tdoy" in year_df.columns and year_df["tdoy"].notna().any():
                tdoy_val = int(year_df["tdoy"].dropna().iloc[-1]) + 1
            # TDOM: letzten bekannten Wert aus df + 1 (oder 1 bei neuem Monat)
            month_df = year_df[year_df.index.month == _today_d.month]
            if "tdom" in month_df.columns and month_df["tdom"].notna().any():
                tdom_val = int(month_df["tdom"].dropna().iloc[-1]) + 1
            elif len(month_df) == 0:
                tdom_val = 1  # Erster Tag im neuen Monat
        except Exception:
            pass

        # In Supabase schreiben (fire-and-forget)
        try:
            from shared.supabase_client import upsert_prices
            record = {
                "ticker": ticker,
                "date": today.strftime("%Y-%m-%d"),
                "close": last_close,
            }
            if tdom_val is not None:
                record["tdom"] = tdom_val
            if tdoy_val is not None:
                record["tdoy"] = tdoy_val
            upsert_prices([record])
        except Exception:
            pass  # Nicht kritisch

    except Exception:
        pass  # Yahoo-Fehler → DataFrame unverändert zurückgeben

    return df


# ── Explizite Kursreihe fuer Vola-Rechnungen ────────────────────────────────

class KursreiheFehlt(RuntimeError):
    """Supabase hat keine brauchbare Kursreihe. Bewusst ein Fehler, kein Fallback."""


def lade_closes(ticker: str, ab: str | None = None, mindestens: int = 30):
    """Schlusskurse eines Tickers aus Supabase. (daten, closes) als Listen.

    KEIN YAHOO-FALLBACK — im Unterschied zu download_data() oben. Wer eine
    Zeitreihe baut, aus der Perzentile gebildet werden, darf die Quelle nicht
    stillschweigend wechseln: genau diese Mischung hat am 2026-09-09 den
    Live-Punkt ins 99. Perzentil gehoben (Provider-IV neben BS-Rekonstruktion,
    siehe docs/OPTIONS.md). Fehlt die Reihe, ist ein Fehler die richtige
    Antwort, kein anders gerechneter Wert.

    WARUM SUPABASE UND NICHT YAHOO — gemessen am 2026-09-19: `download_data`
    liefert ADJUSTIERTE Kurse (shared/yahoo_downloader.py:111 nimmt `adjclose`),
    und diese Adjustierung wandert mit JEDER Dividende, weil Yahoo die gesamte
    Historie nachtraeglich nach unten korrigiert. Dieselbe Abfrage ergibt
    dadurch an verschiedenen Tagen verschiedene Reihen — fuer eine Historie,
    aus der ein ticker-internes Perzentil gebildet wird, ist das unbrauchbar:
    der heutige Punkt verschiebt sich gegen die gespeicherten.

    WAS DAFUER IN KAUF GENOMMEN WIRD, ehrlich benannt: Supabase haelt den
    Adjustierungsstand des Schreibzeitpunkts (der Nightly Refresh schreibt nur
    ein 7-Tage-Fenster), also traegt die Reihe an jedem Ex-Dividenden-Tag einen
    kuenstlichen Abschlag in Dividendenhoehe. Gemessen ueber ein Jahr: das
    Verhaeltnis Supabase/Yahoo ist zwischen zwei Ex-Tagen konstant und springt
    genau an ihnen (SPY 1,005066 -> 1,002483 am 2026-06-12 -> 1,000000 am
    2026-09-18; JNJ am 2026-05-20 und 2026-08-19; KO durchgehend konstant).
    Fuer die 21-Tage-Vola heisst das ein zusaetzlicher Return von etwa 0,25 %
    je Quartal — klein, und er trifft alle Punkte der Reihe gleichmaessig,
    waehrend Yahoos Wandern gerade den Vergleich zwischen heute und gestern
    zerstoert. Sauber loesen liesse sich das nur mit echten Dividendendaten
    (Tabelle `dividend_events` ist noch leer, siehe TODO in CLAUDE.md).

    Fuer den Spot der laufenden Session ist die Adjustierung unkritisch: die
    jeweils letzte Zeile ist immer unadjustiert (Faktor 1,0).

    @param ab: fruehestes Datum (ISO). None = ganze Historie.
    @param mindestens: weniger Zeilen gelten als "keine brauchbare Reihe".
    @raises KursreiheFehlt
    """
    from shared.supabase_client import get_client
    client = get_client()
    if client is None:
        raise KursreiheFehlt(f"{ticker}: kein Supabase-Client")

    zeilen, offset = [], 0
    while True:
        q = (client.table("prices").select("date,close").eq("ticker", ticker)
             .order("date").range(offset, offset + 999))
        if ab:
            q = q.gte("date", ab)
        antwort = q.execute()
        teil = antwort.data or []
        zeilen += teil
        if len(teil) < 1000:
            break
        offset += 1000

    daten, closes = [], []
    for z in zeilen:
        d, c = z.get("date"), z.get("close")
        if not d or c is None:
            continue
        try:
            closes.append(float(c))
        except (TypeError, ValueError):
            continue
        daten.append(str(d)[:10])

    if len(closes) < mindestens:
        raise KursreiheFehlt(
            f"{ticker}: nur {len(closes)} Schlusskurse in Supabase "
            f"(mindestens {mindestens} erwartet)")
    return daten, closes
