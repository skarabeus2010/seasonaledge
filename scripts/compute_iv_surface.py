#!/usr/bin/env python3
"""
compute_iv_surface.py — IV-Surface je Kern-Ticker (Delta-Grid × DTE-Buckets), daily.

Für ein Kern-Set liquider Ticker (SPY, QQQ, IWM, NVDA, AAPL, MSFT, TSLA, META,
AMZN, GOOGL, AMD, AVGO) wird aus EINEM Massive/Polygon-Option-Chain-Snapshot
eine kompakte Volatilitäts-Surface gebaut:

  Achsen:  Laufzeit (DTE-Buckets 7/14/30/60/90/120d) × Delta-Grid (10Δ…90Δ)
  Zelle :  interpolierte IV (%) am jeweiligen Delta/DTE-Punkt

Delta-Grid ist glatter als ein Moneyness-Grid (die Kette liefert Delta direkt und
saubere ATM-Nähe), deshalb die robustere Wahl. Put-Seite → hohes Delta (tiefes
Strike), Call-Seite → niedriges Delta; wir nutzen |delta| als gemeinsame Achse
und mischen die passende Optionsseite (Puts fürs untere, Calls fürs obere Ende),
so entsteht die klassische Skew-„Grimasse".

Schreibt landing/data/iv_surface.json (schlank; gitignored — NICHT committen).

Nutzung:  py -3.14 scripts/compute_iv_surface.py [--tickers SPY QQQ NVDA]
"""
from __future__ import annotations
import argparse, gc, json, os, ssl, sys, time, urllib.error, urllib.request
from datetime import date, timedelta
from pathlib import Path

_THROTTLE = 0.05  # s zwischen Massive-Seiten (flatrate/unlimited; kleiner Puffer)

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from shared.env_loader import load_env          # noqa: E402
load_env()
from shared.yahoo_downloader import clear_cache  # noqa: E402

_CTX = ssl.create_default_context(); _CTX.check_hostname = False; _CTX.verify_mode = ssl.CERT_NONE
_SNAP = "https://api.polygon.io/v3/snapshot/options/{sym}?expiration_date.lte={hi}&limit=250"
_MAXDTE = 140                         # deckt die 120d-Bucket + Puffer ab
# Achsen der Surface
_DTE_BUCKETS = (7, 14, 30, 60, 90, 120)
# Moneyness = Strike / Spot in % (unter 100 = downside/Puts, über 100 = upside/Calls).
# Klar lesbar + zeigt den Skew direkt (linker Rand hoch = Put-Skew).
_MONEYNESS = (85, 90, 95, 100, 105, 110, 115)
# Kern-Set liquider Underlyings (US-Optionen)
_CORE = ["SPY", "QQQ", "IWM", "NVDA", "AAPL", "MSFT",
         "TSLA", "META", "AMZN", "GOOGL", "AMD", "AVGO"]


def _get(url: str, key: str, tries: int = 5):
    """GET (Massive: apiKey als Query-Param) mit 429-Backoff."""
    full = url + ("&" if "?" in url else "?") + "apiKey=" + key
    for i in range(tries):
        time.sleep(_THROTTLE)
        try:
            return json.loads(urllib.request.urlopen(
                urllib.request.Request(full, headers={"User-Agent": "SeasonAlpha/1.0"}),
                timeout=30, context=_CTX).read())
        except urllib.error.HTTPError as e:
            if e.code == 429 and i < tries - 1:
                time.sleep(2.0 * (i + 1))
                continue
            raise


def _chain(sym: str, key: str) -> list:
    """Volle Option-Chain (≤_MAXDTE) als Kontraktliste (paginiert)."""
    hi = (date.today() + timedelta(days=_MAXDTE)).isoformat()
    url = _SNAP.format(sym=sym, hi=hi)
    out, pages = [], 0
    while url and pages < 45:
        d = _get(url, key)
        if d.get("status") not in ("OK", "DELAYED") and not d.get("results"):
            break
        out += d.get("results", [])
        url = d.get("next_url")
        pages += 1
    return out


def _byexp(contracts: list) -> tuple[dict, float | None]:
    """Kontrakte je Verfallstag: {exp: {dte, call:[(K,iv)], put:[(K,iv)]}} + Spot.

    Zweite Rückgabe = Underlying-Spot (falls im Snapshot vorhanden, sonst None →
    Proxy aus dem ATM-Strike, s. _spot_proxy).
    """
    today = date.today(); by = {}; spot = None
    for c in contracts:
        g = c.get("greeks") or {}; iv = c.get("implied_volatility"); dl = g.get("delta")
        if iv is None or dl is None or iv <= 0:
            continue
        det = c.get("details") or {}; ex = det.get("expiration_date"); typ = det.get("contract_type")
        k = det.get("strike_price")
        if not ex or typ not in ("call", "put") or k is None:
            continue
        if spot is None:
            p = (c.get("underlying_asset") or {}).get("price")
            if p:
                spot = round(float(p), 2)
        dte = (date.fromisoformat(ex) - today).days
        if dte < 1:
            continue
        e = by.setdefault(ex, {"dte": dte, "call": [], "put": [], "delta": []})
        e[typ].append((float(k), round(float(iv) * 100.0, 3)))
        e["delta"].append((float(k), abs(float(dl))))
    return by, spot


def _spot_proxy(e: dict) -> float | None:
    """Spot-Proxy einer Expiry: Strike, an dem |Call-Δ| ≈ 0.5 (ATM)."""
    d = sorted(e.get("delta", []), key=lambda x: abs(x[1] - 0.5))
    return round(float(d[0][0]), 2) if d else None


def _interp_iv(e: dict, spot: float, target_moneyness: float) -> float | None:
    """IV (%) bei Strike = target_moneyness% des Spots, per linearer Interpolation.

    Standard-OTM-Konstruktion: unter Spot Puts, ab Spot Calls (put-call-parity →
    gleiche IV bei gleichem Strike, aber OTM-Seiten sind liquider/robuster).
    """
    kt = spot * target_moneyness / 100.0
    side = e["put"] if target_moneyness < 100 else e["call"]
    s = sorted(side, key=lambda x: x[0])
    if len(s) < 2:
        s = sorted(e["put"] + e["call"], key=lambda x: x[0])
    if len(s) < 2:
        return None
    lo, hi = s[0][0], s[-1][0]
    if kt < lo or kt > hi:
        # außerhalb der Strike-Spanne → nächster verfügbarer Strike (kein Extrapolieren)
        near = min(s, key=lambda x: abs(x[0] - kt))
        return round(near[1], 2)
    for i in range(1, len(s)):
        if s[i][0] >= kt:
            k0, v0 = s[i - 1]; k1, v1 = s[i]
            if k1 == k0:
                return round(v1, 2)
            w = (kt - k0) / (k1 - k0)
            return round(v0 + w * (v1 - v0), 2)
    return round(s[-1][1], 2)


def _nearest_exp(by: dict, target_dte: int, used: set) -> str | None:
    cands = [e for e in by if e not in used]
    return min(cands, key=lambda e: abs(by[e]["dte"] - target_dte)) if cands else None


def build_surface(sym: str, key: str) -> dict | None:
    try:
        contracts = _chain(sym, key)
    except Exception as e:
        print(f"  [massive] {sym}: {str(e)[:80]}")
        return None
    by, spot = _byexp(contracts)
    if not by:
        print(f"  [massive] {sym}: keine brauchbaren Kontrakte (n={len(contracts)})")
        return None
    # Spot-Proxy aus der kürzesten Expiry, falls der Underlying-Preis im Snapshot
    # fehlt (Vormittag UTC ist er oft leer — der Cron läuft abends).
    spot_est = spot is None
    if spot is None:
        near_ex = min(by, key=lambda e: by[e]["dte"])
        spot = _spot_proxy(by[near_ex])
    if not spot:
        print(f"  [massive] {sym}: kein Spot/ATM-Strike bestimmbar")
        return None
    # Je DTE-Bucket die nächstliegende Expiry (dedupliziert), dann IV je Moneyness.
    grid, dtes, used = [], [], set()
    atm_idx = _MONEYNESS.index(100)
    for tgt in _DTE_BUCKETS:
        ex = _nearest_exp(by, tgt, used)
        if ex is None:
            continue
        used.add(ex)
        row = [_interp_iv(by[ex], spot, m) for m in _MONEYNESS]
        if row[atm_idx] is None:              # Zeile ohne ATM-IV ist unbrauchbar
            continue
        grid.append(row); dtes.append(by[ex]["dte"])
    if len(grid) < 3:
        print(f"  [massive] {sym}: zu wenige Laufzeiten ({len(grid)})")
        return None
    return {
        "ticker": sym, "spot": round(spot, 2), "spot_estimated": spot_est,
        "dtes": dtes, "moneyness": list(_MONEYNESS),
        "grid": grid,
    }


def build(tickers: list[str], write: bool = True) -> dict:
    tok = os.environ.get("MASSIVE_API_KEY") or os.environ.get("POLYGON_API_KEY", "")
    surfaces = []
    if not tok:
        print("  [massive] MASSIVE_API_KEY fehlt — kann keine Surface bauen.")
    else:
        for t in tickers:
            s = build_surface(t, tok)
            if s:
                surfaces.append(s)
                lo = min(v for r in s["grid"] for v in r if v is not None)
                hi = max(v for r in s["grid"] for v in r if v is not None)
                est = " (Spot~ATM)" if s["spot_estimated"] else ""
                print(f"  {t:6} spot {s['spot']}{est} · {len(s['dtes'])} DTE × "
                      f"{len(s['moneyness'])} Moneyness · IV {lo:.1f}–{hi:.1f}%")
            clear_cache(); gc.collect()

    out = {
        "generated": date.today().isoformat(),
        "source": "Massive/Polygon Option-Chain-Snapshot (Greeks/IV je Kontrakt) → "
                  "Moneyness (Strike/Spot) × DTE-Bucket-Surface, OTM-IV linear interpoliert",
        "moneyness": list(_MONEYNESS), "dte_buckets": list(_DTE_BUCKETS),
        "tickers": surfaces,
    }
    if write:
        p = _ROOT / "landing/data/iv_surface.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n[OK] {len(surfaces)} Surfaces → {p}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tickers", nargs="+", default=_CORE)
    ap.add_argument("--no-write", action="store_true")
    a = ap.parse_args()
    build(a.tickers, not a.no_write)
    return 0


if __name__ == "__main__":
    sys.exit(main())
