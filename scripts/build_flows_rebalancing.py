"""
scripts/build_flows_rebalancing.py — Panel A der /flows-Seite: Index-Rebalancing-Kalender
========================================================================================
Reine Kalender-Arithmetik, KEINE externe Datenquelle:
  * S&P DJI Quartals-Rebalance = 3. Freitag Mar/Jun/Sep/Dez  (deckungsgleich mit Triple Witching)
  * FTSE Russell Reconstitution = letzter Freitag im Juni, wirksam nach Schluss (Jahres-Event)

Schreibt `landing/data/flows_rebalancing.json` mit den nächsten ~18 Monaten + Handelstag-Countdown.
Läuft standalone:  PYTHONUTF8=1 py -3.14 scripts/build_flows_rebalancing.py
"""
from __future__ import annotations
import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
sys.path.insert(0, str(_ROOT))

from shared.nyse_holidays import get_opex_date, is_trading_day  # noqa: E402

_DATA = _ROOT / "landing" / "data"


def _last_friday_of_june(year: int) -> date:
    """Letzter Freitag im Juni (Russell-Reconstitution effective day)."""
    d = date(year, 6, 30)
    while d.weekday() != 4:  # 4 = Freitag
        d -= timedelta(days=1)
    # auf Handelstag zurückziehen, falls Feiertag
    while not is_trading_day(d):
        d -= timedelta(days=1)
    return d


def _trading_days_until(target: date, today: date) -> int:
    """Anzahl Handelstage von morgen bis einschließlich target (0 wenn heute/vergangen)."""
    if target <= today:
        return 0
    n = 0
    d = today + timedelta(days=1)
    while d <= target:
        if is_trading_day(d):
            n += 1
        d += timedelta(days=1)
    return n


def build(today: date | None = None) -> dict:
    today = today or datetime.now(timezone.utc).date()
    events: list[dict] = []

    # Fenster: heute .. +18 Monate
    end = date(today.year + 2, today.month, 1)

    # S&P Quartals-Rebalance (= Triple Witching), Mar/Jun/Sep/Dez
    for year in range(today.year, end.year + 1):
        for month in (3, 6, 9, 12):
            d = get_opex_date(year, month)
            if today <= d <= end:
                events.append({
                    "date": d.isoformat(),
                    "type": "sp_rebalance",
                    "name": "S&P Quartals-Rebalance",
                    "detail": "S&P Dow Jones Indices Quartals-Rebalance — fällt auf denselben 3. Freitag wie Triple Witching.",
                    "emoji": "⚖️",
                    "trading_days_until": _trading_days_until(d, today),
                })

    # FTSE Russell Reconstitution — jährlich, letzter Freitag im Juni
    for year in range(today.year, end.year + 1):
        d = _last_friday_of_june(year)
        if today <= d <= end:
            events.append({
                "date": d.isoformat(),
                "type": "russell_recon",
                "name": "Russell Reconstitution",
                "detail": "FTSE Russell Jahres-Rekonstitution — wirksam nach Börsenschluss. Eines der volumenstärksten Handelsminuten des Jahres.",
                "emoji": "⚖️",
                "trading_days_until": _trading_days_until(d, today),
            })

    events.sort(key=lambda e: e["date"])
    nxt = events[0] if events else None

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "today": today.isoformat(),
        "events": events,
        "next": nxt,
        "note": ("Termine sind fix (Kalender-Arithmetik). Die GRÖSSE der Umschichtung schätzt die Seite "
                 "nicht — dafür bräuchte es Index-Gewichtsänderungen aus Bezahl-Feeds. Kein Handelssignal."),
    }


def main() -> int:
    out = build()
    _DATA.mkdir(parents=True, exist_ok=True)
    (_DATA / "flows_rebalancing.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    nxt = out["next"]
    print(f"[rebalancing] {len(out['events'])} Events · nächstes: "
          f"{nxt['name']} am {nxt['date']} (in {nxt['trading_days_until']} HT)" if nxt else
          "[rebalancing] keine Events", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
