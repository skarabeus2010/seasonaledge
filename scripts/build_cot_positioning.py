"""
scripts/build_cot_positioning.py — Panel D der /flows-Seite: COT Managed-Money-Net (CTA-Proxy)
=============================================================================================
CFTC "Traders in Financial Futures" (TFF), wöchentlich, freie Socrata-API. Beste FREIE Näherung
für systematische Trendfolger (CTAs): Leveraged-Funds & Asset-Manager im E-mini S&P 500.

Aufwertung (Research-Spec 2026-08-02): rohe Netto-Kontrakte driften mit dem Open Interest →
Kernmetrik ist jetzt **OI-normiert** (net_pct_oi) plus **3-Jahres-Perzentil & z-Score** (wie stretched
ist die Positionierung?), **Wochen-Delta** (Flow-Momentum) und **^GSPC am Report-Datum** für den
Positionierung-vs-Preis-Chart. Trend-Ampel via Multi-Window-SMA-Signal.

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

import numpy as np

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
sys.path.insert(0, str(_ROOT))

from shared.yahoo_downloader import download_data  # noqa: E402

_DATA = _ROOT / "landing" / "data"

_TFF = "https://publicreporting.cftc.gov/resource/gpe5-46if.json"
_CONTRACTS = [
    "E-MINI S&P 500 - CHICAGO MERCANTILE EXCHANGE",
    "E-MINI S&P 500 STOCK INDEX - CHICAGO MERCANTILE EXCHANGE",
]
_LIMIT = 170          # ~3,25 Jahre Wochen
_WIN = 156            # 3-Jahres-Fenster für Perzentil/z-Score
_SMAS = [20, 50, 100, 200]
_SMA_W = {20: 0.15, 50: 0.25, 100: 0.30, 200: 0.30}   # Gewichte Multi-Window-Trend


def _f(row, key, default=0.0):
    try:
        return float(row.get(key) or default)
    except (ValueError, TypeError):
        return default


def _fetch_cot(contract: str) -> list[dict]:
    fields = ("report_date_as_yyyy_mm_dd,open_interest_all,"
              "lev_money_positions_long,lev_money_positions_short,"
              "asset_mgr_positions_long,asset_mgr_positions_short,"
              "pct_of_oi_lev_money_long,pct_of_oi_lev_money_short,"
              "change_in_lev_money_long,change_in_lev_money_short")
    url = (f"{_TFF}?market_and_exchange_names={quote(contract)}"
           f"&$select={quote(fields)}"
           f"&$order={quote('report_date_as_yyyy_mm_dd DESC')}"
           f"&$limit={_LIMIT}")
    req = Request(url, headers={"User-Agent": "SeasonAlpha/flows"})
    with urlopen(req, timeout=40) as r:
        rows = json.loads(r.read().decode("utf-8"))
    series = []
    for row in rows:
        d = (row.get("report_date_as_yyyy_mm_dd") or "")[:10]
        if not d:
            continue
        oi = _f(row, "open_interest_all")
        ll, ls = _f(row, "lev_money_positions_long"), _f(row, "lev_money_positions_short")
        al, as_ = _f(row, "asset_mgr_positions_long"), _f(row, "asset_mgr_positions_short")
        # OI-normiert: bevorzugt CFTC-pct-Felder, Fallback aus Rohkontrakten
        pl, ps = row.get("pct_of_oi_lev_money_long"), row.get("pct_of_oi_lev_money_short")
        if pl is not None and ps is not None:
            net_pct_oi = round(_f(row, "pct_of_oi_lev_money_long") - _f(row, "pct_of_oi_lev_money_short"), 3)
        elif oi > 0:
            net_pct_oi = round((ll - ls) / oi * 100.0, 3)
        else:
            net_pct_oi = None
        chg = None
        if row.get("change_in_lev_money_long") is not None:
            chg = int(_f(row, "change_in_lev_money_long") - _f(row, "change_in_lev_money_short"))
        series.append({
            "date": d,
            "lev_funds_net": int(ll - ls),
            "asset_mgr_net": int(al - as_),
            "open_interest": int(oi),
            "net_pct_oi": net_pct_oi,
            "lev_net_change_wk": chg,
        })
    series.sort(key=lambda x: x["date"])
    # Wochen-Delta-Fallback (wenn CFTC-change-Feld fehlt)
    for i, p in enumerate(series):
        if p["lev_net_change_wk"] is None and i > 0:
            p["lev_net_change_wk"] = p["lev_funds_net"] - series[i - 1]["lev_funds_net"]
    return series


def _gspc_and_trend(report_dates: list[str]) -> tuple[dict[str, float], dict]:
    """^GSPC-Close je Report-Datum (nächster HT ≤ Datum) + Multi-Window-Trend-Signal."""
    df = download_data("^GSPC")
    at_report: dict[str, float] = {}
    trend = {"trend_signal": None, "bias": "neutral", "flip_levels": {}, "last_close": None}
    if df is not None and not df.empty:
        if "Date" not in df.columns:
            df = df.reset_index()
        df = df.dropna(subset=["Close"]).copy()
        df["Date"] = df["Date"].astype("datetime64[ns]")
        df = df.sort_values("Date")
        dstr = df["Date"].dt.strftime("%Y-%m-%d").to_numpy()
        close = df["Close"].astype(float).to_numpy()
        import bisect
        dlist = list(dstr)
        for rd in report_dates:
            j = bisect.bisect_right(dlist, rd) - 1       # nächster HT ≤ Report-Datum
            if j >= 0:
                at_report[rd] = round(float(close[j]), 2)
        if len(close) >= max(_SMAS):
            last = float(close[-1])
            sig, wsum, flips = 0.0, 0.0, {}
            for w in _SMAS:
                sma = float(close[-w:].mean())
                flips[str(w)] = round(sma, 2)
                sig += _SMA_W[w] * float(np.tanh((last / sma - 1) / 0.03))
                wsum += _SMA_W[w]
            s = round(sig / wsum, 3)
            trend = {"trend_signal": s, "last_close": round(last, 2), "flip_levels": flips,
                     "bias": "long" if s > 0.33 else ("short" if s < -0.33 else "neutral")}
    download_data.clear()
    gc.collect()
    return at_report, trend


def _stats(vals: list[float]) -> dict:
    a = np.asarray([v for v in vals if v is not None], dtype=float)
    if len(a) < 10:
        return {}
    win = a[-_WIN:] if len(a) > _WIN else a
    cur = float(a[-1])
    srt = np.sort(win)
    # Perzentil-Rang des aktuellen Werts per linearer Interpolation (numpy-Stil, KEIN Floor-Indexing)
    pctile = float(np.interp(cur, srt, np.linspace(0.0, 100.0, len(srt))))
    mean, std = float(win.mean()), float(win.std(ddof=1))
    return {
        "lev_net_pctile_156": round(pctile, 1),
        "lev_net_zscore_156": round((cur - mean) / std, 2) if std > 0 else 0.0,
        "mean": round(mean, 2), "std": round(std, 2),
        "p80": round(float(np.percentile(win, 80)), 2),
        "p20": round(float(np.percentile(win, 20)), 2),
        "current": round(cur, 2), "window_weeks": int(len(win)),
    }


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
    at_report, trend = _gspc_and_trend([p["date"] for p in series])
    for p in series:
        p["gspc_at_report"] = at_report.get(p["date"])
    stats = _stats([p["net_pct_oi"] for p in series])
    latest = series[-1]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "contract": used,
        "series": series,
        "latest": latest,
        "stats": stats,
        "trend": trend,
        "note": ("CFTC COT ≠ echte CTA-Positionierung — nur Näherung über Leveraged-Funds im E-mini "
                 "S&P 500. 'Leveraged Funds' ist ein Mischtopf (u.a. Basis-Arbitrage), das rohe Vorzeichen "
                 "ist irreführend → aussagekräftig ist nur die Abweichung vom eigenen 3-Jahres-Schnitt "
                 "(Perzentil/z-Score) auf OI-normierter Basis. Wöchentlich, ~3 Tage Meldeverzug (Stichtag "
                 "Dienstag, Veröffentlichung Freitag). Trend-Signal = Multi-Window-SMA-Proxy, KEINE "
                 "proprietären $-Trigger-Level. Kein Live-Bild, kein Handelssignal."),
    }


def main() -> int:
    out = build()
    _DATA.mkdir(parents=True, exist_ok=True)
    (_DATA / "cot_positioning.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    lt, st = out["latest"], out["stats"]
    print(f"[cot] {len(out['series'])} Wochen · net%OI {lt.get('net_pct_oi')} "
          f"→ {st.get('lev_net_pctile_156')}. Perzentil (z {st.get('lev_net_zscore_156')}) · "
          f"Trend {out['trend']['bias']} ({out['trend']['trend_signal']})", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
