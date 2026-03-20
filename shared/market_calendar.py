"""
shared/market_calendar.py — Market Calendar DB-Sync
====================================================
Sammelt Feiertage, OPEX, Zentralbank-Termine und Market Events
aus bestehenden Modulen und synchronisiert sie nach Supabase.

Kein Streamlit-Import! Reine Berechnung + DB-Sync.
"""

from datetime import date
from shared.nyse_holidays import (
    _compute_nyse_holidays,
    _observed,
    _nth_weekday,
    get_all_opex_dates,
)
from shared.exchange_holidays import (
    _compute_xetra_holidays,
    _compute_lse_holidays,
    _compute_euronext_holidays,
    _compute_tse_holidays,
)
from shared.central_banks import (
    FED_RATE_CHANGES,
    FED_MINUTES_DATES,
    ECB_MEETING_DATES,
    BOE_MEETING_DATES,
    BOJ_MEETING_DATES,
)


# ── Holidays ────────────────────────────────────────

_EXCHANGE_COMPUTE = {
    "NYSE":     _compute_nyse_holidays,
    "XETRA":    _compute_xetra_holidays,
    "LSE":      _compute_lse_holidays,
    "EURONEXT": _compute_euronext_holidays,
    "TSE":      _compute_tse_holidays,
}


def populate_holidays(year: int) -> list[dict]:
    """Berechnet Feiertage aller Börsen für ein Jahr → DB-Rows."""
    rows = []
    for exchange, fn in _EXCHANGE_COMPUTE.items():
        for d in fn(year):
            rows.append({
                "event_date": d.isoformat(),
                "event_type": "holiday",
                "event_name": f"{exchange} Holiday",
                "exchange": exchange,
                "subtype": None,
                "meta": {},
                "year": year,
            })
    # Veterans Day + Columbus Day (bond_closed, NYSE bleibt offen)
    veterans = _observed(date(year, 11, 11))
    rows.append({
        "event_date": veterans.isoformat(),
        "event_type": "market_event",
        "event_name": "Veterans Day",
        "exchange": "NYSE",
        "subtype": "bond_closed",
        "meta": {},
        "year": year,
    })
    columbus = _nth_weekday(year, 10, 0, 2)
    rows.append({
        "event_date": columbus.isoformat(),
        "event_type": "market_event",
        "event_name": "Columbus Day",
        "exchange": "NYSE",
        "subtype": "bond_closed",
        "meta": {},
        "year": year,
    })
    return rows


# ── OPEX ────────────────────────────────────────────

def populate_opex(year: int) -> list[dict]:
    """OPEX-Termine für ein Jahr → DB-Rows."""
    rows = []
    for entry in get_all_opex_dates(year, year):
        subtype = "triple_witching" if entry["is_triple"] else None
        meta = {}
        if entry["adjusted"]:
            meta["adjusted"] = True
            meta["note"] = entry["holiday_note"]
        rows.append({
            "event_date": entry["date"].isoformat(),
            "event_type": "opex",
            "event_name": entry["type"],
            "exchange": "NYSE",
            "subtype": subtype,
            "meta": meta,
            "year": year,
        })
    return rows


# ── Central Bank ────────────────────────────────────

def populate_central_bank(year: int) -> list[dict]:
    """Zentralbank-Termine für ein Jahr → DB-Rows."""
    rows = []

    # FOMC — aus fed_dates
    try:
        from shared.fed_dates import FOMC_MEETING_DATES
        for y, m, d in FOMC_MEETING_DATES:
            if y == year:
                rows.append({
                    "event_date": date(y, m, d).isoformat(),
                    "event_type": "central_bank",
                    "event_name": "FOMC Meeting",
                    "exchange": "ALL",
                    "subtype": "rate_decision",
                    "meta": {},
                    "year": year,
                })
    except ImportError:
        pass

    # Fed Rate Changes
    for (y, m, d), bps, rate in FED_RATE_CHANGES:
        if y == year:
            rows.append({
                "event_date": date(y, m, d).isoformat(),
                "event_type": "central_bank",
                "event_name": "Fed Rate Change",
                "exchange": "ALL",
                "subtype": "rate_decision",
                "meta": {"bps": bps, "rate": rate},
                "year": year,
            })

    # Fed Minutes
    for y, m, d in FED_MINUTES_DATES:
        if y == year:
            rows.append({
                "event_date": date(y, m, d).isoformat(),
                "event_type": "central_bank",
                "event_name": "Fed Minutes",
                "exchange": "ALL",
                "subtype": "minutes",
                "meta": {},
                "year": year,
            })

    # ECB
    for y, m, d in ECB_MEETING_DATES:
        if y == year:
            rows.append({
                "event_date": date(y, m, d).isoformat(),
                "event_type": "central_bank",
                "event_name": "ECB Meeting",
                "exchange": "ALL",
                "subtype": "rate_decision",
                "meta": {},
                "year": year,
            })

    # BOE
    for y, m, d in BOE_MEETING_DATES:
        if y == year:
            rows.append({
                "event_date": date(y, m, d).isoformat(),
                "event_type": "central_bank",
                "event_name": "BOE Meeting",
                "exchange": "ALL",
                "subtype": "rate_decision",
                "meta": {},
                "year": year,
            })

    # BOJ
    for y, m, d in BOJ_MEETING_DATES:
        if y == year:
            rows.append({
                "event_date": date(y, m, d).isoformat(),
                "event_type": "central_bank",
                "event_name": "BOJ Meeting",
                "exchange": "ALL",
                "subtype": "rate_decision",
                "meta": {},
                "year": year,
            })

    return rows


# ── Market Events ───────────────────────────────────

def populate_market_events(year: int) -> list[dict]:
    """Spezielle Market Events (Veterans Day, Columbus Day als bond_closed)."""
    # Bereits in populate_holidays() enthalten
    return []


# ── Sync ────────────────────────────────────────────

def sync_calendar(start_year: int, end_year: int):
    """
    Sammelt alle Events und upserted sie nach Supabase.

    Args:
        start_year: erstes Jahr (inklusiv)
        end_year: letztes Jahr (inklusiv)
    """
    from shared.supabase_client import upsert_market_events

    all_records = []
    for year in range(start_year, end_year + 1):
        all_records.extend(populate_holidays(year))
        all_records.extend(populate_opex(year))
        all_records.extend(populate_central_bank(year))

    if all_records:
        upsert_market_events(all_records)

    return len(all_records)


# ── Query API ───────────────────────────────────────

def get_events(
    start_date: str,
    end_date: str,
    event_types: list[str] = None,
    exchanges: list[str] = None,
) -> list[dict]:
    """
    Events aus Supabase laden.

    Args:
        start_date: "YYYY-MM-DD"
        end_date: "YYYY-MM-DD"
        event_types: z.B. ["holiday", "opex"]
        exchanges: z.B. ["NYSE", "ALL"]

    Returns:
        list[dict] — Events aus DB
    """
    from shared.supabase_client import fetch_market_events
    return fetch_market_events(start_date, end_date, event_types, exchanges)
