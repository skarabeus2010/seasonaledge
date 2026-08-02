"""
scripts/build_buyback_blackout.py — Panel B der /flows-Seite: Buyback-Blackout-Saisonkurve
==========================================================================================
~4-6 Wochen vor Earnings dürfen Firmen keine eigenen Aktien zurückkaufen (Blackout). Buybacks
sind ein struktureller Dauer-Bid; im Blackout fehlt er → der Markt ist dünner. Aggregiert über
das US-Kern-Universum entsteht eine Saison-Kurve des "fehlenden Bids" (Peaks am Anfang jeder
Earnings-Saison: Mitte Jan/Apr/Jul/Okt).

DATENLAGE (ehrlich): `earnings_events` (Supabase) enthält nur VERGANGENE Quartals-Reports
(report_date = Fiskal-Quartalsende + Actual-EPS). Zukünftige Termine schätzen wir aus der
Quartals-Kadenz (~91 Tage) + typischem Ankündigungs-Versatz (~30 T nach Quartalsende).
→ Doppel-Proxy, klar gelabelt.

Schreibt `landing/data/buyback_blackout.json`.
Läuft standalone (braucht Supabase-Creds via .env/Umgebung):
  PYTHONUTF8=1 py -3.14 scripts/build_buyback_blackout.py
"""
from __future__ import annotations
import json
import os
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
sys.path.insert(0, str(_ROOT))

_DATA = _ROOT / "landing" / "data"

QUARTER_DAYS = 91          # Quartals-Kadenz
ANNOUNCE_LAG = 30          # Tage von Fiskal-Quartalsende bis Ankündigung (typisch)
BLACKOUT_PRE = 35          # Blackout beginnt ~35 T vor Ankündigung
BLACKOUT_POST = 2          # endet ~2 T nach Ankündigung
WINDOW_DAYS = 90           # ± um heute


def _load_env():
    envf = _ROOT / ".env"
    if envf.exists():
        for line in envf.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip().strip('"'))


def _latest_report_per_us_ticker(sb) -> dict[str, date]:
    """Neuestes report_date je US-gelistetem Ticker (kein Suffix = US → Buyback-relevant)."""
    cutoff = (date.today() - timedelta(days=150)).isoformat()
    rows = (sb.table("earnings_events")
            .select("ticker,report_date")
            .gte("report_date", cutoff)
            .limit(5000).execute().data)
    latest: dict[str, date] = {}
    for r in rows:
        tk = r["ticker"]
        if "." in tk or tk.startswith("^") or "-" in tk or "=" in tk:
            continue  # nur US-gelistet (Suffix-los)
        try:
            d = date.fromisoformat(r["report_date"][:10])
        except (TypeError, ValueError):
            continue
        if tk not in latest or d > latest[tk]:
            latest[tk] = d
    return latest


def _blackout_windows(last_qend: date, today: date) -> list[tuple[date, date]]:
    """Projizierte Blackout-Fenster um das Zeitfenster [today-90, today+90]."""
    first_ann = last_qend + timedelta(days=ANNOUNCE_LAG)
    wins = []
    for k in range(-2, 4):                     # ein paar Quartale um heute
        ann = first_ann + timedelta(days=QUARTER_DAYS * k)
        wins.append((ann - timedelta(days=BLACKOUT_PRE), ann + timedelta(days=BLACKOUT_POST)))
    return wins


def build() -> dict:
    _load_env()
    from shared.supabase_client import get_client
    sb = get_client()
    today = datetime.now(timezone.utc).date()
    latest = _latest_report_per_us_ticker(sb)
    n_universe = len(latest)
    if n_universe == 0:
        raise SystemExit("[buyback] kein US-Universum in earnings_events")

    # projizierte Fenster je Ticker
    ticker_wins = {tk: _blackout_windows(qend, today) for tk, qend in latest.items()}

    # Tages-Serie über [today-90, today+90]
    series = []
    entering = []
    start = today - timedelta(days=WINDOW_DAYS)
    end = today + timedelta(days=WINDOW_DAYS)
    d = start
    prev_in: set[str] = set()
    # Zustand am Vortag von start bestimmen
    day_before = start - timedelta(days=1)
    for tk, wins in ticker_wins.items():
        if any(a <= day_before <= b for a, b in wins):
            prev_in.add(tk)
    while d <= end:
        in_bo = {tk for tk, wins in ticker_wins.items() if any(a <= d <= b for a, b in wins)}
        series.append({
            "date": d.isoformat(),
            "n_in_blackout": len(in_bo),
            "pct_in_blackout": round(len(in_bo) / n_universe, 4),
        })
        # "diese Woche neu im Blackout" (erste 7 Tage ab heute)
        if today <= d <= today + timedelta(days=7):
            for tk in sorted(in_bo - prev_in):
                entering.append({"ticker": tk, "blackout_since": d.isoformat()})
        prev_in = in_bo
        d += timedelta(days=1)

    latest_pt = next((p for p in series if p["date"] == today.isoformat()), series[-1])
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "today": today.isoformat(),
        "n_universe": n_universe,
        "series": series,
        "latest": latest_pt,
        "entering_this_week": entering[:20],
        "note": ("Doppel-Proxy: (1) nächste Earnings aus Quartals-Kadenz (~91 T) + ~30 T Ankündigungs-"
                 "Versatz geschätzt, echte Termine variieren; (2) Blackout-Fenster = Ankündigung −35 bis "
                 "+2 T (Standard-Heuristik, echte Firmen-Policy variiert). Rückkauf-Autorisierung ≠ "
                 "Ausführung. Gleichgewichtet (% der US-Kern-Firmen), NICHT marktkapital-gewichtet. "
                 "Zeigt saisonal fehlenden strukturellen Bid, kein Handelssignal."),
    }


def main() -> int:
    out = build()
    _DATA.mkdir(parents=True, exist_ok=True)
    (_DATA / "buyback_blackout.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    lt = out["latest"]
    print(f"[buyback] Universum {out['n_universe']} US-Firmen · heute {lt['pct_in_blackout']:.0%} "
          f"im Blackout ({lt['n_in_blackout']}) · {len(out['entering_this_week'])} neu diese Woche", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
