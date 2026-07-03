"""
scripts/export_ticker_regimes.py — Regime-Lookup für den Newsletter erzeugen
============================================================================
Liest die (committete, reproduzierbare) Per-Ticker-Backtest-CSV
`landing/data/score_backtest_results.csv` und schreibt eine schlanke
`shared/ticker_regimes.json` mit dem momentum/fade/neutral-Regime je Ticker
(TS + GESAMT). Quelle des Regimes: full-history-Klassifikation, out-of-sample
validiert (PR #145, ~83 % Vorzeichen-Persistenz). Jährlich neu erzeugen.

Aufruf:  PYTHONUTF8=1 py -3.14 scripts/export_ticker_regimes.py
"""
from __future__ import annotations

import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_CSV = _ROOT / "landing" / "data" / "score_backtest_results.csv"
_OUT = _ROOT / "shared" / "ticker_regimes.json"


def _num(v):
    try:
        return round(float(v), 4)
    except (TypeError, ValueError):
        return None


def main() -> int:
    if not _CSV.exists():
        print(f"[regimes] FEHLT: {_CSV} — erst backtest_newsletter_scoring.py laufen lassen.")
        return 1
    regimes: dict[str, dict] = {}
    with open(_CSV, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            tk, st = r["ticker"], r["score_type"]
            if st not in ("TS", "GESAMT"):
                continue
            d = regimes.setdefault(tk, {})
            key = st.lower()                      # "ts" / "gesamt"
            if key not in d:                      # class ist je (Ticker,Score) konstant
                d[key] = r.get("class") or "n/a"
                d[f"{key}_rho"] = _num(r.get("class_mean_rho"))
    counts = {"momentum": 0, "fade": 0, "neutral": 0}
    for d in regimes.values():
        counts[d.get("ts", "neutral")] = counts.get(d.get("ts", "neutral"), 0) + 1
    payload = {
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "source": "landing/data/score_backtest_results.csv",
            "regime_basis": "TS full-history-Klassifikation, OOS-validiert (PR #145)",
            "note": "Jährlich neu erzeugen. Hinweis-Basis = TS (richtungstragender Score-Teil).",
            "ts_counts": counts,
        },
        "regimes": dict(sorted(regimes.items())),
    }
    _OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[regimes] {len(regimes)} Ticker -> {_OUT}")
    print(f"[regimes] TS: {counts}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
