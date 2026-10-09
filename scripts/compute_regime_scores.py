"""
scripts/compute_regime_scores.py — Stress-Ampel: geprüfter Vollauf je Ticker
============================================================================
Seit 2026-10-09 kein Isolation Forest mehr (der Rang war im Vorzeichen vertauscht: Lehman 15.10.2008 und Corona
16.03.2020 standen auf 0/grün). Rechnung und Schreibweg: shared/stress_score.py, Plan
docs/review_prompts/2026-10-09_stress_ampel_plan.md (v5, Codex-Freigabe).

Jeder Lauf ist ein Vollauf mit eigener lauf_id in `stress_scores`; sichtbar wird er erst nach dem Rücklesevergleich
über `stress_lauf_veroeffentlichen`. `regime_scores` wird nicht mehr geschrieben.

Usage:
    python3 compute_regime_scores.py                  # SPY (Default)
    python3 compute_regime_scores.py --ticker ^GSPC
    python3 compute_regime_scores.py --trocken        # nur rechnen und prüfen, nichts schreiben
Der frühere Schalter --full bleibt als wirkungsloser Alias (jeder Lauf ist voll).
"""

import sys
import os
import pathlib
import argparse

try:
    _project_dir = str(pathlib.Path(__file__).resolve().parent.parent)
except NameError:
    _project_dir = os.getcwd()
if _project_dir not in sys.path:
    sys.path.insert(0, _project_dir)

from shared import stress_score
from shared.logger import app_logger


def main() -> int:
    parser = argparse.ArgumentParser(description="Stress-Ampel: geprüfter Vollauf")
    parser.add_argument("--ticker", default="SPY")
    parser.add_argument("--full", action="store_true", help="ohne Wirkung — jeder Lauf ist ein Vollauf")
    parser.add_argument("--trocken", action="store_true", help="rechnen und prüfen, nicht schreiben")
    args = parser.parse_args()
    ticker = args.ticker.upper()
    try:
        if args.trocken:
            daten, closes, info = stress_score.lade_kurse(ticker)
            soll = stress_score.sollmenge(daten, closes)
            letzte = soll[-1] if soll else None
            print(f"{ticker}: {info}, {len(soll)} Scores, letzter {letzte and (letzte['date'], letzte['score'], letzte['ampel'])}")
            return 0
        r = stress_score.vollauf(ticker, protokoll=lambda m: (app_logger.info(m), print(m, flush=True)))
        print(f"{ticker}: {r}")
        return 0
    except Exception as e:  # noqa: BLE001 — Fehler muss als Exit 1 sichtbar sein
        app_logger.error(f"Stress-Ampel {ticker}: {e}")
        print(f"FEHLER {ticker}: {e}", flush=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
