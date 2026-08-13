"""
scripts/snapshot_gex.py — täglicher GEX-Snapshot (Dealer-Positioning) für /dealer-positioning
=============================================================================================
Rechnet das Kern-Universum (Index + Mag7 + Leit-ETFs), schreibt die Live-Summary
`landing/data/gex_summary.json` (für die Seite) + ein **dagestempeltes Archiv**
`landing/data/gex_history/<YYYY-MM-DD>.json` (proprietäre GEX-Historie — jeder nicht
archivierte Tag ist für immer weg). Für die Charts zusätzlich Profil-JSONs je Chart-Ticker.

Läuft standalone (nur requests + scipy) → GitHub-Actions-tauglich.
  PYTHONUTF8=1 py -3.14 scripts/snapshot_gex.py
"""
from __future__ import annotations
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
from compute_gamma_exposure import analyze, _INDEX_TICKERS  # noqa: E402

_ROOT = _HERE.parent
_DATA = _ROOT / "landing" / "data"

# Kern-Universum (Index + Mag7 + Leit-ETFs) — Index zuerst (für den Markt-Gamma-Index)
UNIVERSE = [
    "SPY", "QQQ", "IWM", "DIA",
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA",
    "TLT", "GLD", "SLV", "SMH", "XLF", "XLE", "XLK", "IBIT", "ETHA",
]
# Für diese Ticker zusätzlich Per-Strike/Per-Term-Profile (Charts auf der Seite)
CHART_TICKERS = ["SPY", "QQQ", "NVDA", "TSLA"]

# Horizont für Summary + Archiv. BEWUSST KONSTANT: die dagestempelte GEX-Historie ist nur
# vergleichbar, wenn jeder Tag denselben Ausschnitt der Chain misst. Wer das aendert, bricht
# die Zeitreihe rueckwirkend.
MAX_DAYS = 45

# Horizont NUR fuer die Chart-Profile. Der Term-Chart soll die Struktur zeigen, und die
# steckt groesstenteils jenseits von 45 Tagen: Vanna waechst mit der Restlaufzeit, die
# grossen Dez-/Quartals-Verfaelle liegen ausserhalb. Getrennt gehalten, damit der
# Summary-Horizont (und damit die Historie) unberuehrt bleibt.
# 1200 Tage = praktisch die gesamte von Yahoo gelieferte Chain (SPY 30 von 31 Verfaellen,
# letzter 2028-12-15). Laengere LEAPS existieren nur fuer SPX, nicht fuer die ETF-Chains.
PROFILE_MAX_DAYS = 1200


def main() -> int:
    results, charts, failed = [], {}, []
    for tk in UNIVERSE:
        try:
            o = analyze(tk, MAX_DAYS)
        except Exception as e:
            o = None
            print(f"  [WARN] {tk}: {type(e).__name__}: {e}", flush=True)
        if not o:
            failed.append(tk)
            continue
        results.append(o)
        print(f"  [{tk}] GEX {o['net_gex_usd_bn']:+.3f}  {o['regime']}", flush=True)

        # Chart-Profile mit eigenem, laengerem Horizont — zweiter Durchlauf, damit der
        # Summary-Wert oben (und die Historie) auf MAX_DAYS bleibt.
        if tk in CHART_TICKERS:
            try:
                deep = analyze(tk, PROFILE_MAX_DAYS, with_profile=True)
            except Exception as e:
                deep = None
                print(f"  [WARN] {tk} Profil: {type(e).__name__}: {e}", flush=True)
            prof = (deep or {}).get("profile")
            charts[tk] = prof
            if prof:
                print(f"        Profil {PROFILE_MAX_DAYS}d: {len(prof.get('by_term', []))} Verfaelle, "
                      f"{len(prof.get('by_strike', []))} Strikes", flush=True)

    idx = [o for o in results if o["ticker"] in _INDEX_TICKERS]
    gamma_index = None
    if idx:
        val = round(sum(o["net_gex_usd_bn"] for o in idx), 3)
        gamma_index = {"value_usd_bn_per_pct": val,
                       "vol_regime": "vola-reduzierend" if val > 0 else "vola-forcierend",
                       "components": [o["ticker"] for o in idx]}

    stamp = date.today().isoformat()
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "date": stamp, "gamma_index": gamma_index, "tickers": results, "failed": failed,
        "note": "Naive Dealer-Heuristik (long Calls/short Puts), EOD-Yahoo-Daten, "
                "kein Handelssignal — Referenzen, keine Barrieren.",
    }
    _DATA.mkdir(parents=True, exist_ok=True)
    (_DATA / "gex_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    for tk, prof in charts.items():
        (_DATA / f"gex_profile_{tk.replace('^', '')}.json").write_text(
            json.dumps({"ticker": tk, "date": stamp, "max_days": PROFILE_MAX_DAYS,
                        "profile": prof}, ensure_ascii=False), encoding="utf-8")

    # Dagestempeltes Archiv (proprietäre Historie — schlank: nur die Kennzahlen, keine Profile)
    hist = _DATA / "gex_history"
    hist.mkdir(exist_ok=True)
    slim = {"date": stamp, "gamma_index": gamma_index,
            "tickers": [{k: o[k] for k in ("ticker", "spot", "net_gex_usd_bn", "net_vanna_usd_mn",
                                           "net_charm_usd_mn_per_day", "regime", "zero_gamma",
                                           "call_wall", "put_wall", "skew")} for o in results]}
    (hist / f"{stamp}.json").write_text(json.dumps(slim, ensure_ascii=False), encoding="utf-8")

    print(f"[snapshot] {len(results)} ok / {len(failed)} fail · Gamma-Index "
          f"{gamma_index['value_usd_bn_per_pct'] if gamma_index else '—'} · Archiv {stamp}.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
