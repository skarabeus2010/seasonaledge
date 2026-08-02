"""
scripts/build_shortvol_proxy.py — Panel F der /flows-Seite: FINRA Short-Volume-Proxy (DIX-artig)
==============================================================================================
FINRA veröffentlicht täglich die "Reg SHO Daily Short Sale Volume Files" (frei, konsolidiert über
alle US-Symbole). Wir aggregieren marktweit den **Short-Volume-Anteil** = Σ ShortVolume / Σ TotalVolume.

WICHTIG (ehrlich): Der ANTEIL selbst ist NICHT richtungsweisend — ein Großteil des gemeldeten
Short-Volumens ist Market-Maker-Liquidität/Hedging, nicht bearische Wetten. Aussagekräftig ist nur
die **Abweichung vom eigenen Schnitt** (Perzentil/z-Score). Kein DIX (proprietär), nur freier Proxy.

Vorwärts-akkumulierend gecacht (`_shortvol_history.json`): erster Lauf backfillt ~Historie,
Folgeläufe holen nur neue Tage.

Schreibt `landing/data/shortvol_proxy.json`.
  PYTHONUTF8=1 py -3.14 scripts/build_shortvol_proxy.py
"""
from __future__ import annotations
import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.request import Request, urlopen

import numpy as np

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
sys.path.insert(0, str(_ROOT))

_DATA = _ROOT / "landing" / "data"
_HISTORY = _DATA / "_shortvol_history.json"

_URL = "https://cdn.finra.org/equity/regsho/daily/CNMSshvol{ymd}.txt"
_BACKFILL_DAYS = 120       # Kalendertage-Fenster
_MAX_FETCH = 90            # Deckel neuer Downloads pro Lauf (Runaway-Schutz)
_OUT_DAYS = 90             # Ausgabe-Fenster
_WIN = 60                  # Perzentil/z-Score-Fenster (Handelstage)


def _fetch_day(d: date) -> float | None:
    """Marktweiter Short-Volume-Anteil für einen Tag (None wenn kein File = Feiertag/Wochenende)."""
    url = _URL.format(ymd=d.strftime("%Y%m%d"))
    try:
        req = Request(url, headers={"User-Agent": "SeasonAlpha/flows"})
        with urlopen(req, timeout=40) as r:
            if r.status != 200:
                return None
            short_sum = total_sum = 0.0
            first = True
            for raw in r:
                if first:                      # Header überspringen
                    first = False
                    continue
                parts = raw.decode("utf-8", "ignore").rstrip("\n").split("|")
                if len(parts) < 5:
                    continue
                try:
                    short_sum += float(parts[2])
                    total_sum += float(parts[4])
                except ValueError:
                    continue
            if total_sum > 0:
                return round(short_sum / total_sum, 5)
    except Exception:
        return None
    return None


def _load_cache() -> dict[str, float]:
    try:
        if _HISTORY.exists():
            return {k: float(v) for k, v in json.loads(_HISTORY.read_text(encoding="utf-8")).items()}
    except Exception:
        pass
    return {}


def build() -> dict:
    today = datetime.now(timezone.utc).date()
    cache = _load_cache()
    # fehlende Werktage im Fenster nachladen (jüngste zuerst, Deckel _MAX_FETCH)
    fetched = 0
    d = today
    while d >= today - timedelta(days=_BACKFILL_DAYS) and fetched < _MAX_FETCH:
        key = d.isoformat()
        if d.weekday() < 5 and key not in cache:
            v = _fetch_day(d)
            if v is not None:
                cache[key] = v
            else:
                cache[key] = -1.0          # Marker "kein File" (Feiertag) → nicht erneut versuchen
            fetched += 1
        d -= timedelta(days=1)
    try:
        _HISTORY.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass

    # Serie: gültige Tage (ratio > 0), chronologisch, letzte _OUT_DAYS
    valid = sorted((k, v) for k, v in cache.items() if v and v > 0)
    valid = valid[-_OUT_DAYS:]
    if not valid:
        raise SystemExit("[shortvol] keine gültigen FINRA-Tage")
    ratios = np.array([v for _, v in valid], dtype=float)
    # nachlaufender 5-Tage-Schnitt (Rand: kürzeres Fenster statt Null-Padding-Artefakt)
    ma = np.array([ratios[max(0, i - 4):i + 1].mean() for i in range(len(ratios))])
    series = [{"date": k, "short_vol_ratio": round(v, 4), "ma5": round(float(m), 4)}
              for (k, v), m in zip(valid, ma)]

    win = ratios[-_WIN:] if len(ratios) > _WIN else ratios
    cur = float(ratios[-1])
    srt = np.sort(win)
    pctile = float(np.interp(cur, srt, np.linspace(0.0, 100.0, len(srt))))
    mean, std = float(win.mean()), float(win.std(ddof=1))
    stats = {
        "current": round(cur, 4),
        "pctile_60": round(pctile, 1),
        "zscore_60": round((cur - mean) / std, 2) if std > 0 else 0.0,
        "mean": round(mean, 4), "std": round(std, 4),
        "p80": round(float(np.percentile(win, 80)), 4),
        "p20": round(float(np.percentile(win, 20)), 4),
        "window_days": int(len(win)),
    }
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "series": series,
        "latest": series[-1],
        "stats": stats,
        "note": ("FINRA Reg-SHO konsolidiertes Short-Volumen (frei), marktweit aggregiert: "
                 "Σ Short / Σ Gesamt-Volumen. Der ANTEIL selbst ist NICHT richtungsweisend — ein "
                 "Großteil ist Market-Maker-Liquidität/Hedging, kein bearischer Einsatz. Aussagekräftig "
                 "ist nur die Abweichung vom eigenen Schnitt (Perzentil/z-Score). Kein DIX (proprietär), "
                 "nur freier Proxy. Kein Handelssignal."),
    }


def main() -> int:
    out = build()
    _DATA.mkdir(parents=True, exist_ok=True)
    (_DATA / "shortvol_proxy.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    st = out["stats"]
    print(f"[shortvol] {len(out['series'])} Tage · aktuell {st['current']:.1%} "
          f"→ {st['pctile_60']}. Perzentil (z {st['zscore_60']})", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
