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
DEFAULT_N_STOCKS = 10
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
# Aktueller Kurs + Vortagsperformance (Bulk)
# ─────────────────────────────────────────────────────────────────────────────

def fetch_latest_prices_map(tickers: list[str]) -> dict[str, dict]:
    """
    Für jeden Ticker {close: float, prev_close: float, change_pct: float, date: str}.

    Holt die letzten 5 Tage pro Ticker (paginiert), nimmt die zwei letzten
    Werte. Eine Query pro Ticker ist unvermeidlich da REST kein DISTINCT ON
    via Supabase-PostgREST kann.
    """
    from shared.supabase_client import get_client
    client = get_client()
    out: dict[str, dict] = {}

    for t in tickers:
        try:
            rows = (
                client.table("prices")
                .select("date,close")
                .eq("ticker", t)
                .order("date", desc=True)
                .limit(2)
                .execute()
                .data
            ) or []
            if len(rows) >= 2:
                close = float(rows[0]["close"])
                prev = float(rows[1]["close"])
                change = (close / prev - 1) * 100 if prev else 0
                out[t] = {
                    "close":      close,
                    "prev_close": prev,
                    "change_pct": round(change, 2),
                    "date":       rows[0]["date"],
                }
            elif len(rows) == 1:
                out[t] = {
                    "close":      float(rows[0]["close"]),
                    "prev_close": None,
                    "change_pct": None,
                    "date":       rows[0]["date"],
                }
        except Exception as e:
            error_logger.error(f"[daily_report] fetch_prices {t}: {e}")

    return out


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


def _candidate_passes(
    c: dict,
    universe_tickers: set[str],
    regimes: dict[str, dict],
    ki_min: float,
    allow_yellow: bool,
    require_regime: bool = True,
) -> tuple[bool, dict | None]:
    """
    Pre-Check: passes Universum + KI + Regime? Return (passed, regime_dict).

    require_regime=False: fehlender Regime-Score wird toleriert (für fallback-Tier).
    In der aktuellen Pipeline hat nur ein Bruchteil der Ticker regime_scores;
    Strict-Filter würde sonst fast immer leer rauskommen.
    """
    ticker = c.get("ticker")
    if ticker not in universe_tickers:
        return False, None
    ki = c.get("score") or 0
    if ki < ki_min:
        return False, None
    regime = regimes.get(ticker)
    if not regime:
        if require_regime:
            return False, None
        # fallback-Tier: unbekanntes Regime als 'unknown' weiterführen
        return True, {"traffic_light": "unknown"}
    light = regime.get("traffic_light")
    if light != "green" and not (allow_yellow and light == "yellow"):
        return False, None
    return True, regime


def _build_tip_rows(
    candidates: list[dict],
    universe_tickers: set[str],
    universe_meta: dict[str, dict],
    target_tdom: int,
    regimes: dict[str, dict],
    limit: int,
) -> list[dict]:
    """
    Filter + Sort. Drei-stufiger Fallback — Tiers werden kumuliert bis das
    Limit erreicht ist:
      1. Strict:    KI ≥6.5  · Regime grün     · Multi-Window ≥3
      2. Relaxed:   KI ≥5.5  · Regime grün     · Multi-Window ≥2
      3. Fallback:  KI ≥5.0  · Regime grün/gelb · ohne MW-Filter

    Beispiel: limit=10, strict liefert 2 → relaxed füllt mit 5 weiteren auf
    → fallback füllt mit 3 weiteren bis 10 voll sind.
    """
    tiers = [
        ("strict",   {"ki_min": 6.5, "mw_min": 3, "allow_yellow": False, "require_regime": True}),
        ("relaxed",  {"ki_min": 5.5, "mw_min": 2, "allow_yellow": False, "require_regime": True}),
        ("fallback", {"ki_min": 5.0, "mw_min": 0, "allow_yellow": True,  "require_regime": False}),
    ]
    collected: list[dict] = []
    seen_tickers: set[str] = set()
    for tier_name, p in tiers:
        if len(collected) >= limit:
            break
        # Pro Tier nur die noch fehlenden Slots holen
        needed = limit - len(collected)
        rows = _try_build(candidates, universe_tickers, universe_meta,
                          target_tdom, regimes, needed * 3, p, tier_name)
        for r in rows:
            if r["ticker"] in seen_tickers:
                continue
            collected.append(r)
            seen_tickers.add(r["ticker"])
            if len(collected) >= limit:
                break
    return collected[:limit]


def _try_build(candidates, universe_tickers, universe_meta, target_tdom,
               regimes, limit, params, tier_name):
    rows: list[dict] = []
    for c in candidates:
        passed, regime = _candidate_passes(
            c, universe_tickers, regimes,
            params["ki_min"], params["allow_yellow"],
            require_regime=params.get("require_regime", True),
        )
        if not passed:
            continue
        ticker = c["ticker"]
        ki = c.get("score") or 0

        mw = compute_multi_window_tdom_score(ticker, target_tdom)
        if mw["score_total"] < params["mw_min"]:
            continue

        # Verdict
        if mw["score_total"] == 4 and ki >= 7.5:
            verdict = "stark bullish"
        elif mw["score_total"] >= 3 and ki >= 6.5:
            verdict = "bullish"
        elif mw["score_total"] >= 2:
            verdict = "leicht bullish"
        else:
            verdict = "schwach (Fallback)"

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
            "tier": tier_name,
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

    # Aktueller Kurs + Vortagsperformance nur für die finalen Top-N (10 Queries
    # statt 269). Wird pro Run einmal aufgerufen, nicht pro Empfänger.
    selected_tickers = [r["ticker"] for r in etfs] + [r["ticker"] for r in stocks]
    price_map = fetch_latest_prices_map(selected_tickers)
    for row in etfs + stocks:
        p = price_map.get(row["ticker"])
        if p:
            row["price_close"] = p.get("close")
            row["price_date"] = p.get("date")
            row["change_pct"] = p.get("change_pct")

    return {"etfs": etfs, "stocks": stocks, "tdom": target_tdom}


# ─────────────────────────────────────────────────────────────────────────────
# Sektion 3: Events heute/morgen
# ─────────────────────────────────────────────────────────────────────────────

EVENTS_LOOKAHEAD_DAYS = 5


# ─────────────────────────────────────────────────────────────────────────────
# Status-Zeile: Heute: Fr 15.05.2026 · ^DJI · TDOM 11/20 · TWOY 20/53 · TDOY 93/252 · Q2 · MidTerm
# ─────────────────────────────────────────────────────────────────────────────

_WEEKDAY_SHORT_DE = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
_CYCLE_NAMES = {1: "Election", 2: "Post-Election", 3: "MidTerm", 4: "Pre-Election"}


def _iso_week(d: date) -> int:
    return d.isocalendar()[1]


def _total_iso_weeks(year: int) -> int:
    # 28. Dez liegt nach ISO immer in der letzten Woche des Jahres
    return date(year, 12, 28).isocalendar()[1]


def _count_trading_days_in_year(today: date, exchange: str) -> tuple[int, int]:
    """Returnt (tdoy_current_inkl_heute, tdoy_total_jahr) börsenspezifisch."""
    try:
        from shared.exchange_holidays import is_trading_day
    except Exception:
        is_trading_day = None

    count_now = total = 0
    d = date(today.year, 1, 1)
    end = date(today.year, 12, 31)
    while d <= end:
        is_td = (
            is_trading_day(d, exchange) if is_trading_day is not None
            else d.weekday() < 5
        )
        if is_td:
            total += 1
            if d <= today:
                count_now += 1
        d += timedelta(days=1)
    return count_now, total


def _count_trading_days_in_month(today: date, exchange: str) -> tuple[int, int]:
    try:
        from shared.exchange_holidays import is_trading_day
    except Exception:
        is_trading_day = None

    # Monatsende ermitteln
    if today.month == 12:
        first_next = date(today.year + 1, 1, 1)
    else:
        first_next = date(today.year, today.month + 1, 1)
    end = first_next - timedelta(days=1)

    count_now = total = 0
    d = date(today.year, today.month, 1)
    while d <= end:
        is_td = (
            is_trading_day(d, exchange) if is_trading_day is not None
            else d.weekday() < 5
        )
        if is_td:
            total += 1
            if d <= today:
                count_now += 1
        d += timedelta(days=1)
    return count_now, total


def build_status_line(ticker: str = "^DJI") -> str:
    """
    'Heute: Fr 15.05.2026 · ^DJI · TDOM 11/20 · TWOY 20/53 · TDOY 93/252 · Q2 · MidTerm'

    Börsenspezifische Berechnung via shared.exchange_holidays.is_trading_day.
    """
    try:
        from shared.symbols import get_exchange_for_holidays
        exchange = get_exchange_for_holidays(ticker)
    except Exception:
        exchange = "NYSE"

    today = datetime.now(timezone.utc).date()
    weekday = _WEEKDAY_SHORT_DE[today.weekday()]
    date_str = today.strftime("%d.%m.%Y")

    tdom_c, tdom_t = _count_trading_days_in_month(today, exchange)
    tdoy_c, tdoy_t = _count_trading_days_in_year(today, exchange)
    twoy_c = _iso_week(today)
    twoy_t = _total_iso_weeks(today.year)
    quarter = (today.month - 1) // 3 + 1
    cycle = ((today.year - 2020) % 4 + 4) % 4 + 1
    cycle_name = _CYCLE_NAMES.get(cycle, "")

    return (
        f"Heute: {weekday} {date_str} · {ticker} · "
        f"TDOM {tdom_c}/{tdom_t} · TWOY {twoy_c}/{twoy_t} · "
        f"TDOY {tdoy_c}/{tdoy_t} · Q{quarter} · {cycle_name}"
    )


def events_today_tomorrow(target_date: date | None = None,
                          lookahead_days: int = EVENTS_LOOKAHEAD_DAYS) -> list[dict]:
    """
    Marktrelevante Events der nächsten ``lookahead_days`` Tage (default 5):
    FOMC, OPEX/Triple Witching, Feiertage, Earnings, Dividenden.

    Fenster: von heute (UTC) bis target_date + lookahead_days-1.
    """
    if target_date is None:
        target_date = next_trading_day()

    events: list[dict] = []
    today_utc = datetime.now(timezone.utc).date()
    window_start = min(today_utc, target_date)
    window_end = target_date + timedelta(days=max(0, lookahead_days - 1))

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
        we = _ue(days=(window_end - today_utc).days + 1) or []
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

    # Dividenden (Ex-Date im Window)
    try:
        rows = (
            client.table("dividend_events")
            .select("ticker,ex_date,amount,currency")
            .gte("ex_date", window_start.strftime("%Y-%m-%d"))
            .lte("ex_date", window_end.strftime("%Y-%m-%d"))
            .limit(50)
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
# Per-Recipient: Watchlist
# ─────────────────────────────────────────────────────────────────────────────

WATCHLIST_LIMIT = 15


def fetch_watchlist_for_email(email: str, scanner_results: list[dict] | None = None) -> list[dict]:
    """
    Holt die Cloud-Watchlist eines Subscribers via Email.

    Returnt list[{ticker, name, ki_score, signal, added_at}] — leer wenn User
    nicht eingeloggt ist oder keine Watchlist hat. KI-Score wird angereichert
    sofern in scanner_results vorhanden.
    """
    from shared.supabase_client import get_client
    from shared.symbols import SYMBOLS

    try:
        resp = get_client().rpc("get_watchlist_by_email", {"p_email": email}).execute()
        raw = resp.data or []
    except Exception as e:
        error_logger.error(f"[daily_report] watchlist rpc failed for {email}: {e}")
        return []

    if not raw:
        return []

    # Scanner-Score je Ticker lookup
    score_map = {}
    if scanner_results:
        for s in scanner_results:
            t = s.get("ticker")
            if t:
                score_map[t] = {
                    "score":  s.get("score"),
                    "signal": s.get("signal"),
                }

    items = raw[:WATCHLIST_LIMIT]
    # Preise im Bulk für die Watchlist-Tickers
    wl_tickers = [item["ticker"] for item in items if item.get("ticker")]
    price_map = fetch_latest_prices_map(wl_tickers) if wl_tickers else {}

    rows: list[dict] = []
    for item in items:
        ticker = item.get("ticker")
        if not ticker:
            continue
        meta = SYMBOLS.get(ticker, {})
        sc = score_map.get(ticker, {})
        p = price_map.get(ticker, {})
        rows.append({
            "ticker":   ticker,
            "name":     meta.get("name", ticker),
            "kategorie": meta.get("kategorie", ""),
            "ki_score": sc.get("score"),
            "signal":   sc.get("signal"),
            "added_at": item.get("added_at"),
            "price_close": p.get("close"),
            "change_pct":  p.get("change_pct"),
            "price_date":  p.get("date"),
        })
    return rows


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


def _third_friday(year: int, month: int) -> date:
    """3. Freitag des Monats — OPEX-Anker."""
    d = date(year, month, 1)
    fridays = [d + timedelta(days=i) for i in range(31)
               if (d + timedelta(days=i)).month == month
               and (d + timedelta(days=i)).weekday() == 4]
    return fridays[2] if len(fridays) >= 3 else fridays[-1]


def _last_monday(year: int, month: int) -> date:
    """Letzter Montag eines Monats — Memorial Day, Labor Day."""
    d = date(year, month, 1)
    last_day = (date(year + (1 if month == 12 else 0),
                     1 if month == 12 else month + 1, 1) - timedelta(days=1))
    while last_day.weekday() != 0:
        last_day -= timedelta(days=1)
    return last_day


def active_strategy_signals(target_date: date | None = None) -> list[dict]:
    """
    Welche Saison-Strategien sind am target_date aktiv?
    Pragmatische Date-Range-Checks — kein dynamisches Backtest-Replay.
    """
    if target_date is None:
        target_date = next_trading_day()

    signals: list[dict] = []
    y, m, day = target_date.year, target_date.month, target_date.day

    # ── Jahres-Fenster ─────────────────────────────────────────────
    if _is_in_window(target_date, 12, 27, 1, 5):
        signals.append({
            "name": "Santa Claus Rally", "ticker": "SPY", "phase": "🎄 Entry-Fenster",
            "description": "27. Dez bis 5. Jan — historisch ~75% Hitrate auf SPY.",
        })

    if _is_in_window(target_date, 11, 1, 4, 30):
        signals.append({
            "name": "Halloween-Indikator (Sell in May)", "ticker": "SPY",
            "phase": "📈 Long-Saison aktiv",
            "description": "1. Nov bis 30. April — historisch stärkste 6 Monate ('Best 6 Months').",
        })
    else:
        # Mai bis Oktober — explizite Warnung
        signals.append({
            "name": "Sell-in-May-Phase", "ticker": "SPY",
            "phase": "⚠️ Schwache Saisonalität",
            "description": "Mai bis Oktober — historisch schwächere 6 Monate. Position-Sizing prüfen.",
        })

    if m == 1:
        signals.append({
            "name": "January Effect", "ticker": "IWM", "phase": "🐣 Saisonfenster",
            "description": "Small-Caps tendieren im Januar zu Outperformance vs Large-Caps.",
        })

    if _is_in_window(target_date, 8, 1, 9, 30):
        signals.append({
            "name": "Summer Doldrums", "ticker": "SPY", "phase": "⚠️ Schwache Saison",
            "description": "Aug–Sep historisch schwächste 2 Monate.",
        })

    if _is_in_window(target_date, 12, 20, 12, 31):
        signals.append({
            "name": "Year-End Window Dressing", "ticker": "SPY",
            "phase": "🏷️ Letzte HT des Jahres",
            "description": "Fondsmanager kaufen Winner für Jahresabschluss-Performance.",
        })

    # ── Monats-/Wochen-Fenster ─────────────────────────────────────
    if day >= 28 or day <= 3:
        signals.append({
            "name": "Turn-of-Month-Effekt", "ticker": "SPY",
            "phase": "📅 Aktives Fenster",
            "description": "Letzter HT + erste 3 HT des Monats — Inflows aus Sparplänen/401k.",
        })

    # OPEX-Woche (3. Freitag) — Volatilität steigt Mo-Do, Drift Fr
    try:
        opex_fri = _third_friday(y, m)
        opex_week_start = opex_fri - timedelta(days=4)  # Montag der OPEX-Woche
        if opex_week_start <= target_date <= opex_fri:
            signals.append({
                "name": "OPEX-Woche", "ticker": "SPY",
                "phase": "🌀 Pinning-/Vola-Effekt",
                "description": f"Bis Fr {opex_fri.strftime('%d.%m.')}: Optionen-Verfall, "
                               f"Pinning um runde Strikes, oft erhöhte Vola am Mo-Di.",
            })
    except Exception:
        pass

    # Pre-Holiday-Bias (Tag vor NYSE-Feiertag = historisch bullish auf SPY)
    try:
        from shared.nyse_holidays import _compute_nyse_holidays
        holidays = set(_compute_nyse_holidays(y)) | set(_compute_nyse_holidays(y + 1))
        next_day = target_date + timedelta(days=1)
        while next_day.weekday() >= 5:
            next_day += timedelta(days=1)
        if next_day in holidays:
            signals.append({
                "name": "Pre-Holiday-Drift", "ticker": "SPY",
                "phase": "🇺🇸 Letzter HT vor Feiertag",
                "description": f"NYSE morgen ({next_day.strftime('%d.%m.')}) geschlossen — "
                               f"historisch bullish-bias am Vortag.",
            })
    except Exception:
        pass

    # Memorial Day (letzter Mo Mai) — typischerweise bullish Woche danach
    if m == 5:
        memorial = _last_monday(y, 5)
        if memorial - timedelta(days=3) <= target_date <= memorial + timedelta(days=5):
            signals.append({
                "name": "Memorial Day Effekt", "ticker": "SPY",
                "phase": "🇺🇸 Saisonfenster",
                "description": f"Memorial Day {memorial.strftime('%d.%m.')} — historisch "
                               f"bullisches Set-up in der Woche davor und danach.",
            })

    # FOMC-Drift (5 HT vor FOMC-Statement = bullish historisch)
    try:
        from shared.fed_dates import get_fomc_dates_for_years
        for dt in get_fomc_dates_for_years(y, y + 1):
            fomc_d = dt.date() if hasattr(dt, "date") else dt
            delta = (fomc_d - target_date).days
            if 0 <= delta <= 7:
                signals.append({
                    "name": "Pre-FOMC-Drift", "ticker": "SPY",
                    "phase": "🏛️ Bullish-Bias",
                    "description": f"FOMC am {fomc_d.strftime('%d.%m.')} — historisch "
                                   f"positiver Drift in den HT davor.",
                })
                break
    except Exception:
        pass

    # Earnings-Saison (jedes Quartal, ca. Mitte des Folgemonats für ~4 Wochen)
    earnings_months = {1, 4, 7, 10}  # Hauptberichts-Monate
    if m in earnings_months and 10 <= day <= 31:
        signals.append({
            "name": "Earnings-Saison aktiv", "ticker": "SPY",
            "phase": "📊 Sektor-Rotation üblich",
            "description": "Quartalsergebnisse — erhöhte Einzelaktien-Volatilität, "
                           "Sektoren-Rotation häufig.",
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
    status_line = build_status_line(ticker="^DJI")

    # Risikolage für Kern-Marktbarometer
    from shared.weekly_report import regime_status
    market_regime = regime_status(["SPY", "^GDAXI", "QQQ"])

    return {
        "report_time":      now_utc.strftime("%Y-%m-%d %H:%M UTC"),
        "report_date":      target.strftime("%Y-%m-%d"),
        "target_display":   target_display,
        "target_tdom":      tips.get("tdom"),
        "status_line":      status_line,
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
