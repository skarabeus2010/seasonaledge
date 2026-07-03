#!/usr/bin/env python3
"""
Generates landing/data/market_calendar.json + market_calendar.ics
Run during deploy: python3 scripts/build_calendar_data.py

Covers 18 months from today:
- FOMC, ECB, BoE, BoJ, SNB, BoC, RBA, RBNZ
- NYSE OPEX / Triple Witching
- NYSE, XETRA, LSE holidays
- Full moon + New moon
"""
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from shared.fed_dates import get_fomc_dates_for_years
from shared.central_banks import (
    get_ecb_dates, get_boe_dates, get_boj_dates,
    get_snb_dates, get_boc_dates, get_rba_dates, get_rbnz_dates,
    get_full_moon_dates, get_new_moon_dates,
)
from shared.nyse_holidays import get_all_opex_dates
from shared.exchange_holidays import get_holidays

BASE = Path(__file__).resolve().parent.parent
OUT_JSON = BASE / "landing" / "data" / "market_calendar.json"
OUT_ICS  = BASE / "landing" / "data" / "market_calendar.ics"


def _to_date(d):
    """Normalize datetime / pd.Timestamp / date to date."""
    if hasattr(d, 'date'):
        result = d.date()
        # pd.Timestamp.date() returns Python date
        return result if isinstance(result, date) else result
    return d


def main():
    today = date.today()
    start_year = today.year
    end_year = today.year + 2

    # Window: last month to +18 months
    wstart = date(today.year, today.month, 1)
    wend_raw = date(today.year + 1, today.month, 1) + timedelta(days=32)
    wend = date(wend_raw.year, wend_raw.month, 1)

    events = []

    def add(raw_date, etype, name, detail="", **kwargs):
        d = _to_date(raw_date)
        if not isinstance(d, date):
            return
        if wstart <= d <= wend:
            ev = {"date": d.isoformat(), "type": etype, "name": name, "detail": detail}
            ev.update(kwargs)
            events.append(ev)

    # ── FOMC ──────────────────────────────────────────────────────────
    for dt in get_fomc_dates_for_years(start_year, end_year):
        add(dt, "fomc", "FOMC", "Zinsentscheidung · Fed", bank="Fed", emoji="🏦")

    # ── EZB ───────────────────────────────────────────────────────────
    for dt in get_ecb_dates():
        add(dt, "ecb", "EZB", "Zinsentscheidung · EZB", bank="EZB", emoji="🇪🇺")

    # ── BoE ───────────────────────────────────────────────────────────
    for dt in get_boe_dates():
        add(dt, "boe", "BoE", "Zinsentscheidung · Bank of England", bank="BoE", emoji="🇬🇧")

    # ── BoJ ───────────────────────────────────────────────────────────
    for dt in get_boj_dates():
        add(dt, "boj", "BoJ", "Zinsentscheidung · Bank of Japan", bank="BoJ", emoji="🇯🇵")

    # ── SNB ───────────────────────────────────────────────────────────
    for dt in get_snb_dates():
        add(dt, "snb", "SNB", "Zinsentscheidung · Schweizer Nationalbank", bank="SNB", emoji="🇨🇭")

    # ── BoC ───────────────────────────────────────────────────────────
    for dt in get_boc_dates():
        add(dt, "boc", "BoC", "Zinsentscheidung · Bank of Canada", bank="BoC", emoji="🇨🇦")

    # ── RBA ───────────────────────────────────────────────────────────
    for dt in get_rba_dates():
        add(dt, "rba", "RBA", "Zinsentscheidung · Reserve Bank of Australia", bank="RBA", emoji="🇦🇺")

    # ── RBNZ ──────────────────────────────────────────────────────────
    for dt in get_rbnz_dates():
        add(dt, "rbnz", "RBNZ", "Zinsentscheidung · Reserve Bank of New Zealand", bank="RBNZ", emoji="🇳🇿")

    # ── OPEX / Triple Witching ─────────────────────────────────────────
    for opex in get_all_opex_dates(start_year, end_year):
        d = opex["date"]
        is_triple = opex.get("is_triple", False)
        etype = "triple" if is_triple else "opex"
        name = "Triple Witching" if is_triple else "OPEX"
        add(d, etype, name, "Optionsverfall", triple=is_triple)

    # ── Börsenfeiertage ───────────────────────────────────────────────
    seen_hols = set()
    for exchange in ("NYSE", "XETRA", "LSE"):
        for d in get_holidays(exchange, start_year, end_year):
            key = (d.isoformat(), exchange)
            if key not in seen_hols:
                seen_hols.add(key)
                add(d, "holiday", f"Börsenfeiertag", f"{exchange} geschlossen", exchange=exchange)

    # ── Vollmond ──────────────────────────────────────────────────────
    for moon in get_full_moon_dates(start_year, end_year):
        d = _to_date(moon["date"])
        add(d, "fullmoon", "Vollmond", "", emoji="🌕")

    # ── Neumond ───────────────────────────────────────────────────────
    for moon in get_new_moon_dates(start_year, end_year):
        d = _to_date(moon["date"])
        add(d, "newmoon", "Neumond", "", emoji="🌑")

    events.sort(key=lambda e: e["date"])

    # ── JSON ──────────────────────────────────────────────────────────
    import json
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(events, ensure_ascii=False), encoding="utf-8")
    print(f"[calendar] JSON: {len(events)} Events → {OUT_JSON.name}")

    # ── ICS ───────────────────────────────────────────────────────────
    _write_ics(events)
    print(f"[calendar] ICS  → {OUT_ICS.name}")


def _write_ics(events):
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//SeasonAlpha//MarktKalender//DE",
        "CALSCALE:GREGORIAN",
        "X-WR-CALNAME:SeasonAlpha Marktkalender",
        "X-WR-TIMEZONE:Europe/Berlin",
    ]
    for ev in events:
        d = date.fromisoformat(ev["date"])
        dtstart = d.strftime("%Y%m%d")
        dtend = (d + timedelta(days=1)).strftime("%Y%m%d")
        bank = ev.get("bank", "")
        summary = f"{bank} — {ev['detail']}" if bank and ev.get("detail") else ev.get("detail") or ev["name"]
        uid = f"{ev['type']}-{dtstart}-{ev.get('exchange','')[:3]}@seasonalpha.ai"
        lines += [
            "BEGIN:VEVENT",
            f"DTSTART;VALUE=DATE:{dtstart}",
            f"DTEND;VALUE=DATE:{dtend}",
            f"SUMMARY:{summary}",
            f"UID:{uid}",
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    OUT_ICS.write_text("\r\n".join(lines) + "\r\n", encoding="utf-8")


if __name__ == "__main__":
    main()
