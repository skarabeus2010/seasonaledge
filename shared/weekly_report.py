"""
shared/weekly_report.py — Daten-Aggregation für den Weekly Newsletter

Pure Funktionen ohne Nebeneffekte — kein Email-Versand, keine Jinja2-I/O.
Das Modul liefert ein ReportContext-Dict das vom Template (scripts/templates/
weekly_report.html.j2) und vom Hauptscript (scripts/weekly_newsletter.py)
genutzt wird.

Daten-Quellen (alle Supabase):
    - scanner_results  → Top KI-Scores
    - regime_scores    → Traffic-Light pro Ticker
    - market_events    → Holidays + OPEX + Central Bank
    - tdom_stats       → Saisonaler Bias für aktuelle Handelswoche
    - fed_dates.py     → FOMC-Meetings (statisch aus Python-Konstante)
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from shared.logger import app_logger, error_logger


# ── Konfiguration ────────────────────────────────────────────────────────
DEFAULT_TOP_N = 10
DEFAULT_EVENT_DAYS = 7
BIAS_STRONG_THRESHOLD = 0.15   # > +0.15 % Tages-Ø → "stark"
BIAS_WEAK_THRESHOLD = -0.15    # < −0.15 %        → "schwach"


# ── Sektion 1: Top KI-Scores ─────────────────────────────────────────────
def top_ki_scores(limit: int = DEFAULT_TOP_N) -> list[dict]:
    """
    Die top N Ticker aus den neuesten scanner_results, sortiert nach Score DESC.

    Returns:
        list[dict] mit Feldern: ticker, score, signal, win_rate, avg_return,
        deviation, scan_date
    """
    try:
        from shared.supabase_client import fetch_scanner_results
        results = fetch_scanner_results()  # bereits sortiert nach score DESC
        if not results:
            app_logger.warning("[weekly_report] scanner_results leer")
            return []
        return results[:limit]
    except Exception as e:
        error_logger.error(f"[weekly_report] top_ki_scores failed: {e}")
        return []


# ── Sektion 2: Regime-Status ─────────────────────────────────────────────
def regime_status(tickers: list[str]) -> dict[str, dict]:
    """
    Neuester regime_scores-Record pro Ticker.

    Returns:
        {ticker: {traffic_light, risk_score, vol_20d, drawdown, date}}
        Fehlt ein Ticker → nicht im Dict enthalten.
    """
    if not tickers:
        return {}
    try:
        from shared.supabase_client import get_client
        client = get_client()
        # Wir laden alle Records der letzten 14 Tage für diese Tickers und
        # behalten pro Ticker nur den neuesten. So kriegen wir mit einer
        # einzigen Query alles und die Client-Logik filtert lokal.
        cutoff = (date.today() - timedelta(days=14)).strftime("%Y-%m-%d")
        rows = (
            client.table("regime_scores")
            .select("ticker,date,risk_score,traffic_light,vol_20d,drawdown,ret_5d")
            .in_("ticker", tickers)
            .gte("date", cutoff)
            .order("date", desc=True)
            .execute()
            .data
        ) or []

        result: dict[str, dict] = {}
        for r in rows:
            t = r["ticker"]
            if t not in result:  # Erster Treffer = neuester (weil desc sortiert)
                result[t] = {
                    "traffic_light": r.get("traffic_light", "grey"),
                    "risk_score": r.get("risk_score"),
                    "vol_20d": r.get("vol_20d"),
                    "drawdown": r.get("drawdown"),
                    "ret_5d": r.get("ret_5d"),
                    "date": r.get("date"),
                }
        return result
    except Exception as e:
        error_logger.error(f"[weekly_report] regime_status failed: {e}")
        return {}


# ── Sektion 3: Upcoming Events ───────────────────────────────────────────
def upcoming_events(days: int = DEFAULT_EVENT_DAYS) -> list[dict]:
    """
    FOMC + OPEX + Holidays in den nächsten N Tagen, chronologisch sortiert.

    Returns:
        list[dict] mit Feldern: date (str YYYY-MM-DD), weekday (str),
        type (str), name (str), emoji (str)
    """
    today = date.today()
    end = today + timedelta(days=days)
    events: list[dict] = []

    # 1. FOMC-Meetings aus shared/fed_dates.py (statisch, zuverlässig)
    try:
        from shared.fed_dates import get_fomc_dates_for_years
        for dt in get_fomc_dates_for_years(today.year, today.year + 1):
            d = dt.date() if hasattr(dt, "date") else dt
            if today <= d <= end:
                events.append({
                    "date": d.strftime("%Y-%m-%d"),
                    "weekday": _weekday_de(d),
                    "type": "fomc",
                    "name": "FOMC-Zinsentscheid",
                    "emoji": "🏦",
                })
    except Exception as e:
        error_logger.error(f"[weekly_report] FOMC lookup failed: {e}")

    # 2. Events aus market_events Tabelle (Holidays, OPEX, Central Bank etc.)
    try:
        from shared.supabase_client import fetch_market_events
        rows = fetch_market_events(
            start_date=today.strftime("%Y-%m-%d"),
            end_date=end.strftime("%Y-%m-%d"),
            event_types=["holiday", "opex", "central_bank"],
            exchanges=None,  # keine Filter → alle Börsen
        ) or []
        for r in rows:
            etype = (r.get("event_type") or "").lower()
            name = r.get("event_name") or r.get("subtype") or etype.title()
            exchange = r.get("exchange") or ""
            # Fed-Meetings kommen schon aus fed_dates.py — Dubletten vermeiden
            if etype == "central_bank" and "fomc" in name.lower():
                continue
            emoji = {"holiday": "🎉", "opex": "📊", "central_bank": "🏦"}.get(etype, "📅")
            # Border Exchange ans Name anhängen falls sinnvoll
            display_name = f"{name} ({exchange})" if exchange and exchange not in name else name
            d_str = r.get("event_date")
            try:
                d_obj = datetime.strptime(d_str, "%Y-%m-%d").date()
            except Exception:
                d_obj = today
            events.append({
                "date": d_str,
                "weekday": _weekday_de(d_obj),
                "type": etype,
                "name": display_name,
                "emoji": emoji,
            })
    except Exception as e:
        error_logger.error(f"[weekly_report] market_events lookup failed: {e}")

    # Chronologisch sortieren
    events.sort(key=lambda x: x["date"])
    return events


# ── Sektion 4: TDoM-Bias für die aktuelle Handelswoche ───────────────────
def tdom_bias_for_week(
    tickers: list[str],
    days_ahead: int = 5,
) -> dict[str, dict]:
    """
    Für jeden Ticker: aktueller TDoM + historischer Ø der nächsten
    ``days_ahead`` Handelstage ab heute.

    Returns:
        {ticker: {
            current_tdom: int,
            avg_return_5d: float (Ø der days_ahead Returns in %),
            win_rate_5d: float (Ø der days_ahead Win-Rates in %),
            verdict: "stark" | "neutral" | "schwach",
        }}
    """
    if not tickers:
        return {}

    try:
        from shared.supabase_client import fetch_tdom_stats
    except Exception as e:
        error_logger.error(f"[weekly_report] fetch_tdom_stats import failed: {e}")
        return {}

    # Simple Approximation: wir nehmen als "aktueller TDoM" einfach den Tag
    # im Monat des heutigen Datums. Für eine präzise börsen-spezifische
    # Berechnung müsste man den Exchange-Kalender nutzen, aber für den
    # Report-Zweck (Wochen-Bias, grobe Einschätzung) ist das ok.
    today = date.today()
    current_tdom = max(1, _estimate_tdom(today))

    result: dict[str, dict] = {}
    for ticker in tickers:
        try:
            rows = fetch_tdom_stats(ticker, direction="forward", strategy="open_to_close") or []
            if not rows:
                continue
            # Dict {tdom: record}
            by_tdom = {r.get("tdom"): r for r in rows if r.get("tdom") is not None}
            # Hole die nächsten ``days_ahead`` Einträge ab current_tdom
            selected = []
            for offset in range(days_ahead):
                rec = by_tdom.get(current_tdom + offset)
                if rec:
                    selected.append(rec)
            if not selected:
                continue
            avg_ret = sum((r.get("avg_return") or 0.0) for r in selected) / len(selected)
            avg_wr = sum((r.get("win_rate") or 0.0) for r in selected) / len(selected)
            verdict = _classify_bias(avg_ret)
            result[ticker] = {
                "current_tdom": current_tdom,
                "avg_return_5d": round(avg_ret, 3),
                "win_rate_5d": round(avg_wr, 1),
                "verdict": verdict,
            }
        except Exception as e:
            error_logger.debug(f"[weekly_report] tdom_bias {ticker}: {e}")

    return result


# ── Haupt-Aggregator ─────────────────────────────────────────────────────
def build_report_context(top_n: int = DEFAULT_TOP_N) -> dict[str, Any]:
    """
    Aggregiert alle 4 Sektionen in ein einziges Dict das ans Jinja2-Template
    übergeben wird.

    Returns:
        {
            report_date: str YYYY-MM-DD,
            report_date_display: str "09.04.2026",
            week_number: int,
            year: int,
            top_ki: list[dict],
            regimes: dict[ticker, dict],
            events: list[dict],
            tdom_bias: dict[ticker, dict],
            subscriber_count: int,
        }
    """
    app_logger.info("[weekly_report] Building report context...")
    today = date.today()

    # 1. Top KI-Scores
    top_ki = top_ki_scores(limit=top_n)
    top_tickers = [r["ticker"] for r in top_ki]

    # 2. Regime für Top-Tickers
    regimes = regime_status(top_tickers)

    # 3. Events
    events = upcoming_events(days=DEFAULT_EVENT_DAYS)

    # 4. TDoM-Bias für Top-Tickers
    bias = tdom_bias_for_week(top_tickers, days_ahead=5)

    # 5. Subscriber-Count für Meta-Anzeige
    try:
        from shared.supabase_client import count_subscribers
        counts = count_subscribers()
        subscriber_count = counts.get("active", 0)
    except Exception:
        subscriber_count = 0

    ctx = {
        "report_date": today.strftime("%Y-%m-%d"),
        "report_date_display": today.strftime("%d.%m.%Y"),
        "week_number": today.isocalendar()[1],
        "year": today.year,
        "top_ki": top_ki,
        "regimes": regimes,
        "events": events,
        "tdom_bias": bias,
        "subscriber_count": subscriber_count,
    }
    app_logger.info(
        f"[weekly_report] Context built: {len(top_ki)} tickers, "
        f"{len(events)} events, {len(bias)} bias entries, "
        f"{subscriber_count} active subscribers"
    )
    return ctx


# ── Helper ───────────────────────────────────────────────────────────────
_WEEKDAY_DE = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]


def _weekday_de(d: date) -> str:
    try:
        return _WEEKDAY_DE[d.weekday()]
    except Exception:
        return ""


def _estimate_tdom(d: date) -> int:
    """
    Grobe Schätzung des Trading Day of Month: zählt Mo–Fr (ohne Feiertage)
    vom 1. des Monats bis d. Ausreichend für den Newsletter-Bias — eine
    präzise börsen-spezifische Berechnung erfolgt erst wenn Watchlists +
    Exchange-Resolution pro User verfügbar sind (Feature #4).
    """
    first = d.replace(day=1)
    count = 0
    cur = first
    while cur <= d:
        if cur.weekday() < 5:  # Mo-Fr
            count += 1
        cur += timedelta(days=1)
    return count


def _classify_bias(avg_return_pct: float) -> str:
    """Liefert die verbale Einschätzung zum Wochenbias."""
    if avg_return_pct >= BIAS_STRONG_THRESHOLD:
        return "stark"
    if avg_return_pct <= BIAS_WEAK_THRESHOLD:
        return "schwach"
    return "neutral"
