#!/usr/bin/env python3
"""
build_index_effect.py — Event-Study zum Index-Inklusion-Effekt.

Liest einen Event-Katalog (S&P-500-Additions mit Ankuendigungs- + Wirksamkeits-
datum) und rechnet fuer jedes Event den normalisierten Kurspfad um T=0 (Ankuen-
digungstag) im Fenster [-WIN, +WIN] Handelstage. Aggregiert Mittelpfad +
Perzentilband ueber alle Events und schreibt landing/data/index_effect_study.json
fuer das Frontend.

Methodik (SeasonAlpha-Standard, normalisierte Renditen):
  - T=0  = erster Handelstag >= announcement_date.
  - Baseline = Close am Offset -1 (Handelstag VOR Ankuendigung) -> auf 100 normiert.
  - Pfad = kumulierte %-Entwicklung ab Baseline, so ist der Ankuendigungs-Pop im
    "danach"-Fenster sichtbar.
  - Effective-Offset (Handelstage von Ankuendigung bis Wirksamkeit) je Event
    gespeichert; Mittelwert als vertikaler Marker im Chart.

Nutzung:
  py -3.14 scripts/build_index_effect.py \
      [--events landing/data/index_effect_events.json] \
      [--out landing/data/index_effect_study.json] [--win 20]
"""
from __future__ import annotations
import argparse, gc, json, sys
from datetime import date
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from shared.yahoo_downloader import download_data, clear_cache  # noqa: E402


def _load_series(ticker: str):
    """Volle Tageshistorie (Yahoo-primaer). Gibt (dates:list[str], close:np.array)."""
    df = download_data(ticker, period="max")
    if df is None or len(df) == 0:
        return [], np.array([])
    if "Date" in df.columns:
        dts = [str(d)[:10] for d in df["Date"].tolist()]
    else:
        dts = [str(d)[:10] for d in df.index.tolist()]
    close = df["Close"].to_numpy(dtype=float)
    return dts, close


def _align_index(dates: list[str], anchor: str) -> int | None:
    """Position des ersten Handelstags >= anchor (ISO-String)."""
    for i, d in enumerate(dates):
        if d >= anchor:
            return i
    return None


def build(events_path: Path, out_path: Path, win: int) -> int:
    cat = json.loads(events_path.read_text(encoding="utf-8"))
    events = cat.get("events", [])
    offsets = list(range(-win, win + 1))
    per_event = []      # vollstaendiges Fenster -> geht ins Aggregat
    upcoming = []       # Ankuendigung liegt vor, aber +win-Fenster noch nicht komplett (Live-Events)

    for ev in events:
        tkr = ev.get("ticker")
        ann = ev.get("announcement_date")
        if not tkr or not ann:
            print(f"  skip {tkr}: kein Ticker/announcement_date")
            continue
        dates, close = _load_series(tkr)
        clear_cache(); gc.collect()
        if len(close) == 0:
            print(f"  skip {tkr}: keine Kursdaten")
            continue
        t0 = _align_index(dates, ann)
        if t0 is None or t0 - win - 1 < 0:
            print(f"  skip {tkr}: kein Vor-Fenster (t0={t0}, n={len(close)})")
            continue
        baseline = close[t0 - 1]
        if not np.isfinite(baseline) or baseline <= 0:
            print(f"  skip {tkr}: ungueltige Baseline")
            continue
        eff = ev.get("effective_date")
        eff_off = None
        if eff:
            te = _align_index(dates, eff)
            if te is not None:
                eff_off = te - t0
        rec = {
            "ticker": tkr,
            "company": ev.get("company", tkr),
            "announcement_date": ann,
            "effective_date": eff,
            "effective_offset": eff_off,
            "replaced_ticker": ev.get("replaced_ticker"),
        }
        if t0 + win < len(close):
            # Volles Fenster -> Aggregat
            window = close[t0 - win: t0 + win + 1]      # 2*win+1 Punkte, Offsets -win..+win
            rec["path"] = (window / baseline * 100.0).round(3).tolist()
            per_event.append(rec)
            print(f"  ok   {tkr:6} T0={dates[t0]} eff_off={eff_off} path[-1]={rec['path'][-1]}")
        else:
            # Live/anstehend -> Teilpfad bis zum letzten verfuegbaren Tag
            window = close[t0 - win:]                    # von -win bis Datenende
            rec["path"] = (window / baseline * 100.0).round(3).tolist()
            rec["last_offset"] = len(window) - 1 - win   # Offset des letzten Datenpunkts
            rec["last_date"] = dates[-1]
            upcoming.append(rec)
            print(f"  live {tkr:6} T0={dates[t0]} eff_off={eff_off} bis Offset +{rec['last_offset']} ({dates[-1]})")

    if not per_event:
        print("Keine verwertbaren Events — nichts geschrieben.")
        return 1

    # Aggregation je Offset (NaN-tolerant; hier keine NaN, aber robust)
    mat = np.array([e["path"] for e in per_event], dtype=float)  # (n_events, 2*win+1)
    avg = np.nanmean(mat, axis=0).round(3).tolist()
    p25 = np.nanpercentile(mat, 25, axis=0).round(3).tolist()
    p75 = np.nanpercentile(mat, 75, axis=0).round(3).tolist()
    eff_offs = [e["effective_offset"] for e in per_event if e["effective_offset"] is not None]
    avg_eff = round(float(np.mean(eff_offs)), 1) if eff_offs else None

    out = {
        "index": cat.get("index", "SP500"),
        "generated": date.today().isoformat(),
        "n_events": len(per_event),
        "win": win,
        "offsets": offsets,
        "avg_path": avg,
        "p25": p25,
        "p75": p75,
        "avg_effective_offset": avg_eff,
        "events": per_event,
        "upcoming": upcoming,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[OK] {len(per_event)} Events -> {out_path}")
    print(f"     avg_path[-1]={avg[-1]}  avg_effective_offset={avg_eff}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--events", default="landing/data/index_effect_events.json")
    ap.add_argument("--out", default="landing/data/index_effect_study.json")
    ap.add_argument("--win", type=int, default=20)
    a = ap.parse_args()
    return build(_ROOT / a.events, _ROOT / a.out, a.win)


if __name__ == "__main__":
    sys.exit(main())
