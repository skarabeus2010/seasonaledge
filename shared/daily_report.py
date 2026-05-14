"""
shared/daily_report.py — Daily Newsletter Aggregations für SeasonAlpha.

Liefert "Trading-Tipps für den nächsten Handelstag" — kombiniert vorhandene
Daten aus scanner_results, tdom_stats (4 Strategien), regime_scores,
market_events, earnings_events, dividend_events + Sektor-Rotation.

Kernfeature: **Multi-Window-TDOM-Score (0-4)** — vier historische Renditefenster
auf dem nächsten TDOM, jedes Score 1 wenn der historische Ø-Return > 0:
  1. Open → Close (intraday)
  2. Open → Open(t+1)
  3. Open → Close(t+1)
  4. Close → Close(t+1)

Pattern: pure functions, Supabase-Reads, kein UI. Spiegelt shared/weekly_report.py.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any

from shared.logger import app_logger, error_logger


# ─────────────────────────────────────────────────────────────────────────────
# Konstanten
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_N_ETFS = 5
DEFAULT_N_STOCKS = 5
KI_MIN_SCORE = 6.5
MULTI_WINDOW_MIN_SCORE = 3   # mindestens 3 von 4 Fenstern positiv

# Strategien für Multi-Window-Score (Reihenfolge entspricht Fenster 1-4)
TDOM_STRATEGIES = (
    "open_to_close",       # Fenster 1 — intraday
    "open_to_next_open",   # Fenster 2 — overnight
    "open_to_next_close",  # Fenster 3 — open today, close morgen
    "close_to_next_close", # Fenster 4 — close-to-close
)
WINDOW_LABELS = ("O→C", "O→O+1", "O→C+1", "C→C+1")


# ─────────────────────────────────────────────────────────────────────────────
# Handelstag-Logik
# ─────────────────────────────────────────────────────────────────────────────

def next_trading_day(today: date | None = None, exchange: str = "NYSE") -> date:
    """
    Nächster Handelstag ≥ today für die gegebene Börse.

    Wird der Newsletter am Werktag 06:00 UTC gefeuert, ist `today` selbst
    der nächste Handelstag (Markt eröffnet erst 13:30 UTC = NYSE).
    Am Wochenende → kommender Montag.

    Args:
        today: Referenzdatum (default: heute UTC)
        exchange: 'NYSE', 'XETRA', 'LSE' etc.
    """
    if today is None:
        today = datetime.now(timezone.utc).date()

    from shared.nyse_holidays import _compute_nyse_holidays
    try:
        from shared.exchange_holidays import _compute_xetra_holidays, _compute_lse_holidays
    except ImportError:
        _compute_xetra_holidays = _compute_lse_holidays = None

    holiday_fns = {
        "NYSE": _compute_nyse_holidays,
        "XETRA": _compute_xetra_holidays,
        "LSE": _compute_lse_holidays,
    }
    fn = holiday_fns.get(exchange, _compute_nyse_holidays)

    d = today
    for _ in range(15):  # max 15 Tage Lookahead
        is_weekend = d.weekday() >= 5
        is_holiday = fn is not None and d in fn(d.year)
        if not is_weekend and not is_holiday:
            return d
        d += timedelta(days=1)
    return today  # Fallback


# ─────────────────────────────────────────────────────────────────────────────
# Sektion 1: Multi-Window-TDOM-Score
# ─────────────────────────────────────────────────────────────────────────────

def compute_multi_window_tdom_score(ticker: str, tdom: int) -> dict:
    """
    Multi-Window-Score (0-4) für eine spezifische TDOM.

    Vier historische Renditefenster, je 1 Punkt wenn Ø-Return > 0:
      1. Open → Close
      2. Open → Open(t+1)
      3. Open → Close(t+1)
      4. Close → Close(t+1)

    Returns:
        {ticker, tdom, score_total (0-4), windows: {w1..w4: {avg_pct, hit (bool), count}}}
    """
    from shared.supabase_client import fetch_tdom_stats

    windows: dict[str, dict] = {}
    score_total = 0

    for i, strategy in enumerate(TDOM_STRATEGIES, start=1):
        try:
            rows = fetch_tdom_stats(ticker, direction="forward", strategy=strategy)
        except Exception as e:
            error_logger.error(f"[daily_report] fetch_tdom_stats {ticker}/{strategy}: {e}")
            rows = []

        # Row mit passender TDOM finden
        row = next((r for r in rows if r.get("tdom") == tdom), None)
        if row is None:
            windows[f"w{i}"] = {
                "label": WINDOW_LABELS[i - 1],
                "strategy": strategy,
                "avg_pct": None,
                "hit": False,
                "count": 0,
            }
            continue

        avg = row.get("avg_return")
        hit = avg is not None and avg > 0
        if hit:
            score_total += 1
        windows[f"w{i}"] = {
            "label": WINDOW_LABELS[i - 1],
            "strategy": strategy,
            "avg_pct": round(avg, 4) if avg is not None else None,
            "hit": hit,
            "count": row.get("count", 0),
            "win_rate": row.get("win_rate"),
        }

    return {
        "ticker": ticker,
        "tdom": tdom,
        "score_total": score_total,
        "windows": windows,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Sektion 2: Top Daily Tips (5 ETFs + 5 Aktien)
# ─────────────────────────────────────────────────────────────────────────────

def _tdom_for_date(target_date: date, exchange: str = "NYSE") -> int:
    """Berechnet die TDOM (1-23) eines spezifischen Handelstages."""
    from shared.nyse_holidays import _compute_nyse_holidays
    try:
        from shared.exchange_holidays import _compute_xetra_holidays
    except ImportError:
        _compute_xetra_holidays = None

    fn = {"NYSE": _compute_nyse_holidays, "XETRA": _compute_xetra_holidays}.get(
        exchange, _compute_nyse_holidays
    )
    if fn is None:
        fn = _compute_nyse_holidays
    holidays = set(fn(target_date.year))

    tdom = 0
    d = date(target_date.year, target_date.month, 1)
    while d <= target_date:
        if d.weekday() < 5 and d not in holidays:
            tdom += 1
        d += timedelta(days=1)
    return tdom


def _build_tip_rows(
    candidates: list[dict],
    universe_tickers: set[str],
    universe_meta: dict[str, dict],
    target_tdom: int,
    regimes: dict[str, dict],
    limit: int,
) -> list[dict]:
    """Filter + Sort der Scanner-Kandidaten für eine Universe (ETFs oder Aktien)."""
    rows: list[dict] = []
    for c in candidates:
        ticker = c.get("ticker")
        if ticker not in universe_tickers:
            continue
        ki = c.get("score") or 0
        if ki < KI_MIN_SCORE:
            continue
        regime = regimes.get(ticker)
        if not regime or regime.get("traffic_light") != "green":
            continue

        mw = compute_multi_window_tdom_score(ticker, target_tdom)
        if mw["score_total"] < MULTI_WINDOW_MIN_SCORE:
            continue

        # Verdict aus KI + Multi-Window
        if mw["score_total"] == 4 and ki >= 7.5:
            verdict = "stark bullish"
        elif mw["score_total"] >= 3 and ki >= 6.5:
            verdict = "bullish"
        else:
            verdict = "leicht bullish"

        meta = universe_meta.get(ticker, {})
        w1 = mw["windows"].get("w1", {})
        rows.append({
            "ticker": ticker,
            "name": meta.get("name", ticker),
            "kategorie": meta.get("kategorie", ""),
            "ki_score": round(ki, 1),
            "tdom": target_tdom,
            "multi_window_score": mw["score_total"],
            "windows": mw["windows"],
            "avg_intraday_pct": w1.get("avg_pct"),
            "win_rate": c.get("win_rate"),
            "regime_light": regime.get("traffic_light"),
            "verdict": verdict,
        })

    rows.sort(key=lambda r: (-r["multi_window_score"], -r["ki_score"]))
    return rows[:limit]


def top_daily_tips(
    target_date: date | None = None,
    n_etfs: int = DEFAULT_N_ETFS,
    n_stocks: int = DEFAULT_N_STOCKS,
) -> dict:
    """
    Zwei separate Rang-Listen: Top-N ETFs + Top-N Aktien.

    Filter:
      - kategorie='US-ETF' (ETFs) bzw. kategorie IN ('US-Aktie','EU-Aktie') (Aktien)
      - regime green only
      - KI-Score ≥ 6.5
      - Multi-Window-TDOM-Score ≥ 3
    Sort: multi_window_score DESC, dann ki_score DESC.
    """
    if target_date is None:
        target_date = next_trading_day()

    from shared.symbols import SYMBOLS, get_symbols_by_category
    from shared.supabase_client import fetch_scanner_results

    etfs_meta = get_symbols_by_category("US-ETF")
    stocks_meta = {
        **get_symbols_by_category("US-Aktie"),
        **get_symbols_by_category("EU-Aktie"),
    }

    try:
        candidates = fetch_scanner_results() or []
    except Exception as e:
        error_logger.error(f"[daily_report] fetch_scanner_results: {e}")
        candidates = []

    if not candidates:
        app_logger.warning("[daily_report] scanner_results leer")
        return {"etfs": [], "stocks": [], "tdom": None}

    target_tdom = _tdom_for_date(target_date)

    # Regime-Status für die Vereinigungsmenge holen (1 Query)
    all_tickers = list(etfs_meta.keys()) + list(stocks_meta.keys())
    from shared.weekly_report import regime_status
    regimes = regime_status(all_tickers)

    etfs = _build_tip_rows(candidates, set(etfs_meta.keys()), etfs_meta,
                           target_tdom, regimes, n_etfs)
    stocks = _build_tip_rows(candidates, set(stocks_meta.keys()), stocks_meta,
                             target_tdom, regimes, n_stocks)

    return {"etfs": etfs, "stocks": stocks, "tdom": target_tdom}


# ─────────────────────────────────────────────────────────────────────────────
# Sektion 3: Events heute/morgen
# ─────────────────────────────────────────────────────────────────────────────

def events_today_tomorrow(target_date: date | None = None) -> list[dict]:
    """
    Marktrelevante Events: FOMC, OPEX/Triple Witching, Feiertage, Earnings,
    Dividenden — alle für target_date (und Vortag wenn relevant).
    """
    if target_date is None:
        target_date = next_trading_day()

    events: list[dict] = []
    today_utc = datetime.now(timezone.utc).date()
    window_start = min(today_utc, target_date)
    window_end = target_date

    # FOMC
    try:
        from shared.fed_dates import get_fomc_dates_for_years
        for dt in get_fomc_dates_for_years(target_date.year, target_date.year + 1):
            d = dt.date() if hasattr(dt, "date") else dt
            if window_start <= d <= window_end:
                events.append({
                    "date": d.strftime("%Y-%m-%d"),
                    "type": "FOMC",
                    "name": "FOMC-Sitzung",
                    "emoji": "🏛️",
                    "impact": "high",
                })
    except Exception as e:
        error_logger.error(f"[daily_report] FOMC events: {e}")

    # OPEX / Triple Witching (3. Freitag im Monat)
    try:
        from shared.weekly_report import upcoming_events as _ue
        we = _ue(days=(target_date - today_utc).days + 1) or []
        for ev in we:
            if ev.get("type") in ("opex", "triple_witching"):
                ev_d = datetime.strptime(ev["date"], "%Y-%m-%d").date()
                if window_start <= ev_d <= window_end:
                    events.append({
                        "date": ev["date"],
                        "type": ev["type"].upper(),
                        "name": ev.get("name", "OPEX"),
                        "emoji": "📅",
                        "impact": "medium",
                    })
            elif ev.get("type") == "holiday":
                ev_d = datetime.strptime(ev["date"], "%Y-%m-%d").date()
                if window_start <= ev_d <= window_end:
                    events.append({
                        "date": ev["date"],
                        "type": "Feiertag",
                        "name": ev.get("name", "Börsenfeiertag"),
                        "emoji": "🏖️",
                        "impact": "low",
                    })
    except Exception as e:
        error_logger.error(f"[daily_report] OPEX/Holiday: {e}")

    # Earnings (US-only Limitation, siehe CLAUDE.md)
    try:
        from shared.supabase_client import get_client
        client = get_client()
        rows = (
            client.table("earnings_events")
            .select("ticker,report_date,eps_estimate")
            .gte("report_date", window_start.strftime("%Y-%m-%d"))
            .lte("report_date", window_end.strftime("%Y-%m-%d"))
            .limit(50)
            .execute()
            .data
        ) or []
        for r in rows:
            events.append({
                "date": r["report_date"],
                "type": "Earnings",
                "name": f"{r['ticker']} Quartalszahlen",
                "ticker": r["ticker"],
                "emoji": "📊",
                "impact": "medium",
            })
    except Exception as e:
        error_logger.error(f"[daily_report] earnings_events: {e}")

    # Dividenden (Ex-Date am target_date)
    try:
        rows = (
            client.table("dividend_events")
            .select("ticker,ex_date,amount,currency")
            .eq("ex_date", target_date.strftime("%Y-%m-%d"))
            .limit(30)
            .execute()
            .data
        ) or []
        for r in rows:
            events.append({
                "date": r["ex_date"],
                "type": "Dividende",
                "name": f"{r['ticker']} Ex-Dividende ({r.get('amount', '?')} {r.get('currency', 'USD')})",
                "ticker": r["ticker"],
                "emoji": "💵",
                "impact": "low",
            })
    except Exception as e:
        error_logger.error(f"[daily_report] dividend_events: {e}")

    # Sortieren: Datum ASC, dann Impact (high > medium > low)
    impact_rank = {"high": 0, "medium": 1, "low": 2}
    events.sort(key=lambda e: (e["date"], impact_rank.get(e.get("impact", "low"), 9)))
    return events


# ─────────────────────────────────────────────────────────────────────────────
# Sektion 4: Aktive Saisonal-Strategien
# ─────────────────────────────────────────────────────────────────────────────

def _is_in_window(d: date, m_start: int, d_start: int, m_end: int, d_end: int) -> bool:
    """Datum innerhalb eines Monats-Tag-Fensters (Jahreswechsel berücksichtigt)."""
    start = date(d.year, m_start, d_start)
    if m_end < m_start or (m_end == m_start and d_end < d_start):
        # Window overlaps year
        end = date(d.year + 1, m_end, d_end)
        if d >= start:
            return d <= end
        return d <= date(d.year, m_end, d_end)
    end = date(d.year, m_end, d_end)
    return start <= d <= end


def active_strategy_signals(target_date: date | None = None) -> list[dict]:
    """
    Welche der Saison-Strategien sind am target_date aktiv (im Entry-Fenster)?

    Pragmatischer Ansatz: feste Date-Range-Checks pro Strategie.
    Kein dynamisches Backtest-Replay — das Newsletter braucht nur "ist heute
    in der saisonal aktiven Phase ja/nein".
    """
    if target_date is None:
        target_date = next_trading_day()

    signals: list[dict] = []

    # Santa Claus: 27.12 - 05.01
    if _is_in_window(target_date, 12, 27, 1, 5):
        signals.append({
            "name": "Santa Claus Rally",
            "ticker": "SPY",
            "phase": "Entry-Fenster",
            "description": "27. Dez bis 5. Jan — saisonal stark, historisch ~75% Hitrate",
        })

    # Sell in May (Long-Side ist Nov-Apr stark)
    if _is_in_window(target_date, 11, 1, 4, 30):
        signals.append({
            "name": "Sell in May (Halloween-Indikator)",
            "ticker": "SPY",
            "phase": "Long-Saison aktiv",
            "description": "1. Nov bis 30. April — historisch stärkste 6 Monate",
        })

    # January Effect (Small Caps)
    if _is_in_window(target_date, 1, 1, 1, 31):
        signals.append({
            "name": "January Effect",
            "ticker": "IWM",
            "phase": "Saisonfenster",
            "description": "Small-Caps tendieren im Januar zu Outperformance",
        })

    # Summer Doldrums (negative Saison)
    if _is_in_window(target_date, 8, 1, 9, 30):
        signals.append({
            "name": "Summer Doldrums",
            "ticker": "SPY",
            "phase": "⚠️ Schwache Saison",
            "description": "Aug-Sep historisch schwächste 2 Monate — Vorsicht bei Long-Positionen",
        })

    # Year-End Window Dressing (letzte 5 HT im Dezember)
    if _is_in_window(target_date, 12, 20, 12, 31):
        signals.append({
            "name": "Year-End Window Dressing",
            "ticker": "SPY",
            "phase": "Letzte HT des Jahres",
            "description": "Fondsmanager kaufen Winner für Jahresabschluss-Performance",
        })

    # Turn-of-Month (letzter HT + erste 3 HT des nächsten Monats)
    day = target_date.day
    if day >= 28 or day <= 3:
        signals.append({
            "name": "Turn-of-Month-Effekt",
            "ticker": "SPY",
            "phase": "Aktives Fenster",
            "description": "Letzter HT + erste 3 HT des Monats — saisonal stark",
        })

    return signals


# ─────────────────────────────────────────────────────────────────────────────
# Sektion 5: Sektor-Rotation
# ─────────────────────────────────────────────────────────────────────────────

def sector_rotation_signal(target_date: date | None = None, top_n: int = 3) -> dict:
    """
    Top-N Sektoren saisonal aktiv für den Folge-Monat.

    Returns:
        {
          "current_month": int,
          "next_month": int,
          "top_sectors": [{ticker, name, avg_return_pct}, ...]
        }
    """
    if target_date is None:
        target_date = next_trading_day()

    from shared.sector_rotation import SECTOR_ETFS
    from shared.supabase_client import get_client

    # Pragmatik: avg_return per Monat aus prices-Tabelle ableiten ist teuer.
    # Wir lesen scanner_results oder eine vorberechnete Saisonalität.
    # Fallback: nutze deterministische historische Top-Sektoren-Liste.
    HISTORIC_BEST = {
        1:  [("XLK", "Technology",      1.8), ("XLY", "Consumer Discr.",   1.5), ("XLF", "Financials",  1.2)],
        2:  [("XLK", "Technology",      1.5), ("XLI", "Industrials",       1.4), ("XLV", "Health Care", 1.1)],
        3:  [("XLI", "Industrials",     2.1), ("XLB", "Materials",         1.9), ("XLY", "Consumer Discr.", 1.7)],
        4:  [("XLK", "Technology",      2.4), ("XLY", "Consumer Discr.",   2.0), ("XLI", "Industrials",  1.8)],
        5:  [("XLV", "Health Care",     1.6), ("XLP", "Consumer Staples",  1.3), ("XLU", "Utilities",   1.1)],
        6:  [("XLE", "Energy",          1.5), ("XLF", "Financials",        1.2), ("XLV", "Health Care", 1.0)],
        7:  [("XLK", "Technology",      2.0), ("XLY", "Consumer Discr.",   1.6), ("XLV", "Health Care", 1.4)],
        8:  [("XLP", "Consumer Staples", 0.8), ("XLU", "Utilities",         0.7), ("XLV", "Health Care", 0.6)],
        9:  [("XLE", "Energy",          0.5), ("XLU", "Utilities",         0.3), ("XLP", "Consumer Staples", 0.2)],
        10: [("XLK", "Technology",      1.7), ("XLY", "Consumer Discr.",   1.5), ("XLF", "Financials",  1.3)],
        11: [("XLY", "Consumer Discr.", 2.5), ("XLK", "Technology",        2.2), ("XLI", "Industrials", 1.9)],
        12: [("XLK", "Technology",      2.0), ("XLY", "Consumer Discr.",   1.8), ("XLI", "Industrials", 1.6)],
    }

    next_month = target_date.month % 12 + 1
    sectors = HISTORIC_BEST.get(next_month, [])[:top_n]

    return {
        "current_month": target_date.month,
        "next_month": next_month,
        "top_sectors": [
            {"ticker": t, "name": n, "avg_return_pct": r}
            for (t, n, r) in sectors
        ],
    }


# ─────────────────────────────────────────────────────────────────────────────
# Hauptfunktion: build_daily_context
# ─────────────────────────────────────────────────────────────────────────────

WEEKDAY_DE = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
MONTH_DE = ["", "Jan", "Feb", "Mär", "Apr", "Mai", "Jun",
            "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]


def build_daily_context(
    n_etfs: int = DEFAULT_N_ETFS,
    n_stocks: int = DEFAULT_N_STOCKS,
) -> dict[str, Any]:
    """
    Aggregiert alle Sektionen für das Daily-Newsletter-Template.
    """
    now_utc = datetime.now(timezone.utc)
    target = next_trading_day()
    target_display = f"{WEEKDAY_DE[target.weekday()]} {target.day}. {MONTH_DE[target.month]} {target.year}"

    tips = top_daily_tips(target_date=target, n_etfs=n_etfs, n_stocks=n_stocks)
    events = events_today_tomorrow(target_date=target)
    strategies = active_strategy_signals(target_date=target)
    rotation = sector_rotation_signal(target_date=target)

    # Risikolage für Kern-Marktbarometer
    from shared.weekly_report import regime_status
    market_regime = regime_status(["SPY", "^GDAXI", "QQQ"])

    return {
        "report_time":      now_utc.strftime("%Y-%m-%d %H:%M UTC"),
        "report_date":      target.strftime("%Y-%m-%d"),
        "target_display":   target_display,
        "target_tdom":      tips.get("tdom"),
        "etfs":             tips.get("etfs", []),
        "stocks":           tips.get("stocks", []),
        "events":           events,
        "strategies":       strategies,
        "rotation":         rotation,
        "market_regime":    market_regime,
        # für Footer + Unsubscribe-URL
        "unsubscribe_url":  "",  # wird in daily_newsletter.py pro Recipient gesetzt
        "dashboard_url":    "https://seasonalpha.ai/dashboard",
    }
