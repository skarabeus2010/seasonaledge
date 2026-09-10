#!/usr/bin/env python3
"""
check_flows_freshness.py — prüft, ob die /flows-Panels frische Daten haben.

WARUM: Ein Build-Skript kann exit 0 melden und trotzdem nichts geschrieben
haben (leere API-Antwort, abgefangene Exception, unveränderte Datei). Der
Workflow wäre grün, die Seite zeigte alte Zahlen. Der Exit-Status allein
belegt also nichts — geprüft wird das Alter von `generated_at` im Ergebnis.

Nutzung:
  py -3.14 scripts/check_flows_freshness.py [--max-age-hours 26] [--files a.json b.json]

Exit 0 = alle frisch · 1 = mindestens eine Datei fehlt/veraltet/unlesbar.
"""
from __future__ import annotations
import argparse, json, sys
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_DATA = _ROOT / "landing" / "data"

# Die sechs Panels, die flows_update.yml baut. _mktcap_cache.json steht
# bewusst NICHT hier: ein Cache darf alt sein, das ist sein Zweck.
_FILES = [
    "flows_rebalancing.json",
    "volcontrol_proxy.json",
    "cot_positioning.json",
    "buyback_blackout.json",
    "shortvol_proxy.json",
    "etf_flows.json",
]


def age_hours(path: Path, now: datetime | None = None) -> tuple[float | None, str]:
    """Alter von `generated_at` in Stunden. (None, Grund) wenn nicht bestimmbar."""
    if not path.exists():
        return None, "fehlt"
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        return None, f"unlesbar ({type(e).__name__})"
    ts = d.get("generated_at")
    if not ts:
        return None, "kein generated_at"
    try:
        gen = datetime.fromisoformat(ts)
    except Exception:
        return None, f"generated_at unparsbar ({ts[:30]})"
    if gen.tzinfo is None:                      # naive Angabe als UTC lesen
        gen = gen.replace(tzinfo=timezone.utc)
    now = now or datetime.now(timezone.utc)
    return (now - gen).total_seconds() / 3600.0, ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-age-hours", type=float, default=26.0,
                    help="Schwelle (Default 26 = ein Tag + Puffer für einen späten Lauf)")
    ap.add_argument("--files", nargs="+", default=None)
    ap.add_argument("--data-dir", default=None)
    a = ap.parse_args()

    data = Path(a.data_dir) if a.data_dir else _DATA
    files = a.files or _FILES
    now = datetime.now(timezone.utc)

    bad = 0
    print(f"{'Datei':<26}{'Alter':>10}   Status", flush=True)
    print("-" * 52, flush=True)
    for f in files:
        h, why = age_hours(data / f, now)
        if h is None:
            print(f"{f:<26}{'—':>10}   VERALTET: {why}", flush=True); bad += 1
        elif h > a.max_age_hours:
            print(f"{f:<26}{h:>9.1f}h   VERALTET (>{a.max_age_hours:.0f}h)", flush=True); bad += 1
        else:
            print(f"{f:<26}{h:>9.1f}h   ok", flush=True)

    print("-" * 52, flush=True)
    if bad:
        print(f"[FAIL] {bad} von {len(files)} Panels ohne frische Daten.", flush=True)
        return 1
    print(f"[OK] alle {len(files)} Panels frisch (< {a.max_age_hours:.0f}h).", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
