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

# Polymarket-Divergenz: Ranking-Parameter
POLY_DIV_MIN_PP = 5.0           # Mindest-|Divergenz| in pp für Inklusion
POLY_DIV_MIN_SAMPLES = 3        # Mindest-Historie-Jahre für einen Prior
POLY_DIV_TOP_N = 5              # maximale Top-Einträge im Report
POLY_CRYPTO_TICKERS = {
    "btc": "BTC-USD",
    "eth": "ETH-USD",
}

# Historisches Sample-Fenster für Fed-Baseline (2000-2024, letztes vollständiges Jahr)
FED_HISTORY_START = 2000
FED_HISTORY_END = 2024

# Hartkodierte Basisraten für Markets ohne direkt ableitbare Historie.
# Format: slug -> (base_rate 0..1, rationale).
# Rationale bleibt schlank — wir dokumentieren das WARUM in docs/POLYMARKET.md.
FED_MACRO_STATIC_BASELINES: dict[str, tuple[float, str]] = {
    "fed-emergency-cut-2027": (
        0.12,
        "3 Emergency-Events 2001/2008/2020 auf 25 Jahre Historie = 12%",
    ),
    "us-recession-2026": (
        0.16,
        "NBER: ~12 Recessions 1950-2024, 16%/yr Basisrate",
    ),
    "us-gdp-negative-2026": (
        0.08,
        "BEA: annualer GDP negativ 2001/2008/2009/2020 — 4 in ~76y ≈ 5%, hochkorrigiert für 2026-Unsicherheit",
    ),
}


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


# ── Sektion 5: Polymarket Top-Divergenzen ────────────────────────────────
import re as _re


_POLY_SLUG_RE = _re.compile(r"^(btc|eth)-above-(\d+)k-2026$")


def _collect_year_end_returns(price_rows: list[dict], as_of: date) -> list[float]:
    """
    Portiert aus landing/js/polymarket.js::collectYearEndReturns.
    Für jedes vergangene Jahr: (close am Stichtag X.Y) → (letzter close des Jahrs).
    Liefert Liste der Returns (ret = end/start - 1).
    """
    if not price_rows:
        return []
    by_year: dict[int, list[tuple[date, float]]] = {}
    for r in price_rows:
        ds = r.get("date")
        close = r.get("close")
        if not ds or close is None:
            continue
        try:
            d = datetime.strptime(ds[:10], "%Y-%m-%d").date()
        except Exception:
            continue
        try:
            c = float(close)
        except (TypeError, ValueError):
            continue
        by_year.setdefault(d.year, []).append((d, c))

    samples: list[float] = []
    current_year = as_of.year
    for y, rows in by_year.items():
        if y >= current_year:
            continue
        rows.sort(key=lambda x: x[0])
        try:
            ref_in_year = date(y, as_of.month, as_of.day)
        except ValueError:
            # z.B. 29.02. in Nicht-Schaltjahr → einen Tag zurück
            ref_in_year = date(y, as_of.month, 28)
        start_price = None
        for d, c in rows:
            if d >= ref_in_year:
                start_price = c
                break
        if start_price is None or start_price <= 0:
            continue
        end_price = rows[-1][1]
        if end_price is None or end_price <= 0:
            continue
        samples.append(end_price / start_price - 1.0)
    return samples


def _empirical_above_probability(samples: list[float], target_return: float) -> float | None:
    if not samples:
        return None
    above = sum(1 for r in samples if r >= target_return)
    return above / len(samples)


def top_polymarket_divergences(
    top_n: int = POLY_DIV_TOP_N,
    min_pp: float = POLY_DIV_MIN_PP,
) -> list[dict]:
    """
    Liefert die stärksten Divergenzen zwischen Polymarket-YES und Saisonal-Prior.

    Aktuell nur Crypto-Targets (BTC/ETH). Fed/Macro brauchen andere Baselines
    (TODO, siehe docs/POLYMARKET.md Phase 3b).

    Returns:
        list[dict] sortiert nach |divergence_pp| DESC, mit Feldern:
            asset        "BTC" / "ETH"
            target       "$150k"
            target_price int
            current_price float
            required_ret float   (benötigter Kurs-Return)
            market_prob  float   (Polymarket YES, 0..1)
            prior_prob   float   (Saisonal-Prior, 0..1)
            divergence_pp float  (prior - market) * 100
            samples      int     (# Jahre im Prior)
            verdict      str     "Markt unterschätzt" / "Markt überschätzt"
            slug         str     Polymarket-Slug (für Debug)
    """
    try:
        from shared.supabase_client import (
            fetch_polymarket_markets,
            fetch_polymarket_latest_prices,
            fetch_prices,
        )
    except Exception as e:
        error_logger.error(f"[weekly_report] polymarket imports failed: {e}")
        return []

    try:
        markets = fetch_polymarket_markets(category="crypto", active_only=True) or []
    except Exception as e:
        error_logger.error(f"[weekly_report] fetch_polymarket_markets failed: {e}")
        return []
    if not markets:
        return []

    # Crypto-Above-Markets filtern
    target_markets: list[tuple[str, int, dict]] = []  # (asset, k, market)
    for m in markets:
        match = _POLY_SLUG_RE.match(m.get("slug") or "")
        if not match:
            continue
        asset = match.group(1)
        k = int(match.group(2))
        target_markets.append((asset, k, m))
    if not target_markets:
        return []

    # Latest Prices für alle relevanten condition_ids
    cids = [m["condition_id"] for _, _, m in target_markets]
    try:
        latest_list = fetch_polymarket_latest_prices(cids) or []
    except Exception as e:
        error_logger.error(f"[weekly_report] fetch_polymarket_latest_prices failed: {e}")
        return []
    latest_by_cid = {r.get("condition_id"): r for r in latest_list}

    # Ticker-Historien einmalig pro Asset laden + Prior-Samples berechnen
    today = date.today()
    samples_by_asset: dict[str, list[float]] = {}
    current_by_asset: dict[str, float] = {}
    for asset, ticker in POLY_CRYPTO_TICKERS.items():
        try:
            rows = fetch_prices(ticker) or []
        except Exception as e:
            error_logger.error(f"[weekly_report] fetch_prices {ticker} failed: {e}")
            rows = []
        if not rows:
            continue
        samples_by_asset[asset] = _collect_year_end_returns(rows, today)
        # aktuellster close
        try:
            rows_sorted = sorted(rows, key=lambda r: r.get("date") or "")
            last_close = rows_sorted[-1].get("close")
            current_by_asset[asset] = float(last_close) if last_close is not None else 0.0
        except Exception:
            current_by_asset[asset] = 0.0

    # Divergenzen berechnen
    out: list[dict] = []
    for asset, k, m in target_markets:
        current = current_by_asset.get(asset) or 0.0
        samples = samples_by_asset.get(asset) or []
        if current <= 0 or len(samples) < POLY_DIV_MIN_SAMPLES:
            continue
        target_price = k * 1000
        required_ret = target_price / current - 1.0
        prior_prob = _empirical_above_probability(samples, required_ret)
        if prior_prob is None:
            continue
        snap = latest_by_cid.get(m["condition_id"])
        try:
            market_prob = float(snap.get("yes_price")) if snap else 0.0
        except (TypeError, ValueError):
            market_prob = 0.0
        divergence_pp = (prior_prob - market_prob) * 100.0
        if abs(divergence_pp) < min_pp:
            continue
        verdict = "Markt unterschätzt" if divergence_pp > 0 else "Markt überschätzt"
        out.append({
            "asset": asset.upper(),
            "target": f"${k}k",
            "target_price": target_price,
            "current_price": current,
            "required_ret": required_ret,
            "market_prob": market_prob,
            "prior_prob": prior_prob,
            "divergence_pp": divergence_pp,
            "samples": len(samples),
            "verdict": verdict,
            "slug": m.get("slug"),
        })

    out.sort(key=lambda r: abs(r["divergence_pp"]), reverse=True)
    return out[:top_n]


# ── Fed/Macro Baselines ──────────────────────────────────────────────────
def _historical_fed_cuts_per_year() -> dict[int, int]:
    """Count Cut-Entscheidungen pro Jahr aus shared.central_banks.FED_RATE_CHANGES.
    Jahre ohne Cut werden mit 0 gefüllt (sonst verzerrt sich die Basisrate)."""
    try:
        from shared.central_banks import FED_RATE_CHANGES
    except Exception as e:
        error_logger.error(f"[weekly_report] FED_RATE_CHANGES import failed: {e}")
        return {}
    from collections import Counter
    cuts: Counter = Counter()
    for (y, _m, _d), bps, _rate in FED_RATE_CHANGES:
        if y < FED_HISTORY_START or y > FED_HISTORY_END:
            continue
        if bps < 0:
            cuts[y] += 1
    for y in range(FED_HISTORY_START, FED_HISTORY_END + 1):
        cuts.setdefault(y, 0)
    return dict(cuts)


def _historical_fed_hike_rate() -> float:
    """Anteil Jahre mit mindestens einem Hike im Sample-Fenster."""
    try:
        from shared.central_banks import FED_RATE_CHANGES
    except Exception:
        return 0.0
    hike_years: set[int] = set()
    all_years: set[int] = set(range(FED_HISTORY_START, FED_HISTORY_END + 1))
    for (y, _m, _d), bps, _rate in FED_RATE_CHANGES:
        if y < FED_HISTORY_START or y > FED_HISTORY_END:
            continue
        if bps > 0:
            hike_years.add(y)
    return len(hike_years) / max(1, len(all_years))


def _fed_cuts_bucket_distribution() -> dict[str, float]:
    """Polymarket-Bucket-Verteilung (0..11, 12plus) als Anteil der Sample-Jahre."""
    cpy = _historical_fed_cuts_per_year()
    n = len(cpy)
    if n == 0:
        return {}
    buckets: dict[str, int] = {str(i): 0 for i in range(12)}
    buckets["12plus"] = 0
    for count in cpy.values():
        if count >= 12:
            buckets["12plus"] += 1
        else:
            buckets[str(count)] += 1
    return {k: v / n for k, v in buckets.items()}


def top_fed_macro_divergences(
    top_n: int = POLY_DIV_TOP_N,
    min_pp: float = POLY_DIV_MIN_PP,
) -> list[dict]:
    """
    Divergenz-Ranking für Fed/Macro-Polymarket-Markets.

    Baselines:
    - fed-cuts-2026-N: historisches Bucket-Histogramm aus FED_RATE_CHANGES (2000-2024)
    - fed-hike-2026: Anteil Jahre mit mindestens einem Hike (2000-2024)
    - fed-emergency-cut / us-recession / us-gdp-negative: hartkodierte Basisraten
      (FED_MACRO_STATIC_BASELINES) — keine kausale Predictor-Logik, rein historisch.

    Returns:
        list[dict] sortiert nach |divergence_pp| DESC, mit Feldern:
            category     "fed" / "macro"
            label        "3 Cuts" / "US Recession 2026" / ...
            slug         Polymarket-Slug
            market_prob  float (0..1)
            prior_prob   float (0..1)
            divergence_pp float
            verdict      "Markt unterschätzt" / "Markt überschätzt"
            rationale    Kurzbegründung der Baseline
    """
    try:
        from shared.supabase_client import (
            fetch_polymarket_markets,
            fetch_polymarket_latest_prices,
        )
    except Exception as e:
        error_logger.error(f"[weekly_report] polymarket imports failed: {e}")
        return []

    fed_markets = fetch_polymarket_markets(category="fed", active_only=True) or []
    macro_markets = fetch_polymarket_markets(category="macro", active_only=True) or []
    if not fed_markets and not macro_markets:
        return []

    all_markets = fed_markets + macro_markets
    cids = [m["condition_id"] for m in all_markets]
    latest_list = fetch_polymarket_latest_prices(cids) or []
    latest_by_cid = {r.get("condition_id"): r for r in latest_list}

    cuts_buckets = _fed_cuts_bucket_distribution()
    fed_hike_rate = _historical_fed_hike_rate()
    sample_n = FED_HISTORY_END - FED_HISTORY_START + 1
    cuts_rationale = f"Historisches Bucket-Histogramm {FED_HISTORY_START}-{FED_HISTORY_END} ({sample_n}y)"
    hike_rationale = f"{FED_HISTORY_START}-{FED_HISTORY_END}: Anteil Jahre mit mind. einem Hike"

    def _market_prob(m: dict) -> float:
        snap = latest_by_cid.get(m.get("condition_id"))
        if not snap:
            return 0.0
        try:
            return float(snap.get("yes_price") or 0.0)
        except (TypeError, ValueError):
            return 0.0

    out: list[dict] = []
    cuts_re = _re.compile(r"^fed-cuts-2026-(\d+|12plus)$")

    for m in fed_markets:
        slug = m.get("slug") or ""
        match = cuts_re.match(slug)
        if match:
            bucket = match.group(1)
            prior = cuts_buckets.get(bucket)
            if prior is None:
                continue
            label = ("12+ Cuts" if bucket == "12plus" else f"{bucket} Cuts")
            rat = cuts_rationale
        elif slug == "fed-hike-2026":
            prior = fed_hike_rate
            label = "Fed Hike 2026"
            rat = hike_rationale
        elif slug in FED_MACRO_STATIC_BASELINES:
            prior, rat = FED_MACRO_STATIC_BASELINES[slug]
            label = slug.replace("-", " ").title()
        else:
            continue
        market_prob = _market_prob(m)
        divergence_pp = (prior - market_prob) * 100.0
        if abs(divergence_pp) < min_pp:
            continue
        out.append({
            "category": "fed",
            "label": label,
            "slug": slug,
            "market_prob": market_prob,
            "prior_prob": prior,
            "divergence_pp": divergence_pp,
            "verdict": "Markt unterschätzt" if divergence_pp > 0 else "Markt überschätzt",
            "rationale": rat,
        })

    for m in macro_markets:
        slug = m.get("slug") or ""
        if slug not in FED_MACRO_STATIC_BASELINES:
            continue
        prior, rat = FED_MACRO_STATIC_BASELINES[slug]
        label_map = {
            "us-recession-2026": "US Recession 2026",
            "us-gdp-negative-2026": "Neg. GDP 2026",
        }
        label = label_map.get(slug, slug)
        market_prob = _market_prob(m)
        divergence_pp = (prior - market_prob) * 100.0
        if abs(divergence_pp) < min_pp:
            continue
        out.append({
            "category": "macro",
            "label": label,
            "slug": slug,
            "market_prob": market_prob,
            "prior_prob": prior,
            "divergence_pp": divergence_pp,
            "verdict": "Markt unterschätzt" if divergence_pp > 0 else "Markt überschätzt",
            "rationale": rat,
        })

    out.sort(key=lambda r: abs(r["divergence_pp"]), reverse=True)
    return out[:top_n]


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

    # 5. Polymarket Top-Divergenzen (BTC/ETH)
    poly_divs = top_polymarket_divergences()

    # 5b. Fed/Macro Top-Divergenzen
    fed_divs = top_fed_macro_divergences()

    # 6. Subscriber-Count für Meta-Anzeige
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
        "poly_divergences": poly_divs,
        "fed_divergences": fed_divs,
        "subscriber_count": subscriber_count,
    }
    app_logger.info(
        f"[weekly_report] Context built: {len(top_ki)} tickers, "
        f"{len(events)} events, {len(bias)} bias entries, "
        f"{len(poly_divs)} crypto divergences, {len(fed_divs)} fed/macro divergences, "
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
