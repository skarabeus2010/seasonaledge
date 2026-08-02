"""
scripts/build_cot_positioning.py — Panel D der /flows-Seite: COT Managed-Money-Net (CTA-Proxy)
=============================================================================================
CFTC "Traders in Financial Futures" (TFF), wöchentlich, freie Socrata-API. Beste FREIE Näherung
für systematische Trendfolger (CTAs): Leveraged-Funds & Asset-Manager Net im E-mini S&P 500.
Dazu ein einfaches Trend-Overlay (^GSPC 50/200-Tage-SMA) als "CTA-Ampel".

Schreibt `landing/data/cot_positioning.json`.
Läuft standalone:  PYTHONUTF8=1 py -3.14 scripts/build_cot_positioning.py
"""
from __future__ import annotations
import gc
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
sys.path.insert(0, str(_ROOT))

from shared.yahoo_downloader import download_data  # noqa: E402

_DATA = _ROOT / "landing" / "data"

_TFF = "https://publicreporting.cftc.gov/resource/gpe5-46if.json"
# E-mini S&P 500 (Reihenfolge = Fallback: erster mit Daten gewinnt)
_CONTRACTS = [
    "E-MINI S&P 500 - CHICAGO MERCANTILE EXCHANGE",
    "E-MINI S&P 500 STOCK INDEX - CHICAGO MERCANTILE EXCHANGE",
]
_LIMIT = 170   # ~3,25 Jahre Wochen


def _fetch_cot(contract: str) -> list[dict]:
    fields = ("report_date_as_yyyy_mm_dd,lev_money_positions_long,lev_money_positions_short,"
              "asset_mgr_positions_long,asset_mgr_positions_short,open_interest_all")
    url = (f"{_TFF}?market_and_exchange_names={quote(contract)}"
           f"&$select={quote(fields)}"
           f"&$order={quote('report_date_as_yyyy_mm_dd DESC')}"
           f"&$limit={_LIMIT}")
    req = Request(url, headers={"User-Agent": "SeasonAlpha/flows"})
    with urlopen(req, timeout=40) as r:
        rows = json.loads(r.read().decode("utf-8"))
    series = []
    for row in rows:
        try:
            d = row["report_date_as_yyyy_mm_dd"][:10]
            ll = int(float(row["lev_money_positions_long"]))
            ls = int(float(row["lev_money_positions_short"]))
            al = int(float(row["asset_mgr_positions_long"]))
            as_ = int(float(row["asset_mgr_positions_short"]))
        except (KeyError, ValueError, TypeError):
            continue
        series.append({
            "date": d,
            "lev_funds_net": ll - ls,
            "asset_mgr_net": al - as_,
            "open_interest": int(float(row.get("open_interest_all", 0) or 0)),
        })
    series.sort(key=lambda x: x["date"])
    return series


def _trend_overlay() -> dict:
    df = download_data("^GSPC")
    out = {"sma50_above_sma200": None, "last_close": None, "sma50": None, "sma200": None, "bias": "neutral"}
    if df is not None and not df.empty:
        c = df.dropna(subset=["Close"]).sort_values("Date")["Close"].astype(float)
        if len(c) >= 200:
            sma50 = float(c.tail(50).mean())
            sma200 = float(c.tail(200).mean())
            last = float(c.iloc[-1])
            above = sma50 > sma200
            out.update({
                "sma50_above_sma200": above,
                "last_close": round(last, 2),
                "sma50": round(sma50, 2),
                "sma200": round(sma200, 2),
                "bias": "long" if (above and last > sma50) else ("short" if (not above and last < sma50) else "neutral"),
            })
    download_data.clear()
    gc.collect()
    return out


def build() -> dict:
    series: list[dict] = []
    used = None
    for c in _CONTRACTS:
        series = _fetch_cot(c)
        if series:
            used = c
            break
    if not series:
        raise SystemExit("[cot] keine CFTC-Daten")
    trend = _trend_overlay()
    latest = series[-1]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "contract": used,
        "series": series,
        "latest": latest,
        "trend": trend,
        "note": ("CFTC COT ≠ echte CTA-Positionierung — nur Näherung über Leveraged-Funds/Asset-Manager "
                 "im E-mini S&P 500. Wöchentlich, ~3 Tage Meldeverzug (Stand Dienstag, Veröffentlichung Freitag). "
                 "Kein Live-Bild, kein Handelssignal."),
    }


def main() -> int:
    out = build()
    _DATA.mkdir(parents=True, exist_ok=True)
    (_DATA / "cot_positioning.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    lt = out["latest"]
    print(f"[cot] {len(out['series'])} Wochen · aktuell Lev-Funds {lt['lev_funds_net']:+d} / "
          f"Asset-Mgr {lt['asset_mgr_net']:+d} · Trend-Bias {out['trend']['bias']}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
