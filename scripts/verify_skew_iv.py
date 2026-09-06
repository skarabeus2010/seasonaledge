#!/usr/bin/env python3
"""
verify_skew_iv.py — prüft, ob die 25Δ-IV-Werte stimmen (drei unabhängige Checks).

1) BS-ENGINE vs marketdata: live Chain (delta=.25) liefert Mid UND marketdatas
   eigene IV. Wir invertieren die IV aus dem Mid selbst per Black-Scholes und
   vergleichen — validiert genau die Maschinerie der historischen Rekonstruktion.
2) VIX-KONSISTENZ: SPYs ATM-nahe IV (~(Put25Δ+Call25Δ)/2, leicht über ATM) muss
   in der Nähe des VIX liegen (VIX = 30-Tage-ATM-IV des S&P).
3) PLAUSIBILITÄT: IV-Range + Put-Skew-Vorzeichen über alle Ticker in options_skew.json.

Nutzung:  py -3.14 scripts/verify_skew_iv.py [--symbols SPY QQQ AAPL] [--live]
"""
from __future__ import annotations
import argparse, json, os, ssl, sys, urllib.request
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
from shared.env_loader import load_env          # noqa: E402
load_env()
# BS-Engine aus der Rekonstruktion wiederverwenden (identischer Code-Pfad)
from scripts.backfill_skew_history import _bs_delta, _implied_vol   # noqa: E402

_CTX = ssl.create_default_context(); _CTX.check_hostname = False; _CTX.verify_mode = ssl.CERT_NONE
_MD = "https://api.marketdata.app/v1/options/chain/{sym}/?dte=30&delta=.25&token={tok}"


def _get(url):
    return json.loads(urllib.request.urlopen(
        urllib.request.Request(url, headers={"User-Agent": "SeasonAlpha/1.0"}),
        timeout=25, context=_CTX).read())


def live_cross_check(sym, tok):
    """Hole 25Δ-Chain (mit marketdatas IV) und invertiere IV selbst aus dem Mid."""
    try:
        d = _get(_MD.format(sym=sym, tok=tok))
    except Exception as e:
        return f"  {sym:6} FEHLER {e}"
    if d.get("s") != "ok":
        return f"  {sym:6} {d.get('errmsg', d.get('s'))}"
    S = float(d["underlyingPrice"][0]) if d.get("underlyingPrice") else None
    rows = []
    for i in range(len(d.get("strike", []))):
        K = d["strike"][i]; mid = d["mid"][i]; typ = d["side"][i]
        iv_md = d["iv"][i]; dl_md = d["delta"][i]
        T = (d["dte"][i] or 30) / 365.0
        iv_bs = _implied_vol(mid, S, K, T, typ)
        if iv_bs is None or iv_md is None:
            continue
        dl_bs = _bs_delta(S, K, T, iv_bs, typ)
        rows.append((typ, K, iv_md, iv_bs, (iv_bs - iv_md) * 100, dl_md, dl_bs))
    out = [f"  {sym:6} S={S}"]
    for typ, K, iv_md, iv_bs, dpts, dl_md, dl_bs in rows:
        flag = "OK " if abs(dpts) < 1.0 else "!! "
        out.append(f"     {flag}{typ:4} K={K:<8} IV_md={iv_md*100:5.1f}%  IV_bs={iv_bs*100:5.1f}%  "
                   f"Δ={dpts:+.2f}pts   δ_md={dl_md:+.3f} δ_bs={dl_bs:+.3f}")
    return "\n".join(out)


def offline_checks():
    p = _ROOT / "landing/data/options_skew.json"
    if not p.exists():
        print("  options_skew.json fehlt (noch kein Cron-Lauf)."); return
    d = json.loads(p.read_text(encoding="utf-8"))
    vix = (d.get("indices", {}).get("VIX", {}) or {}).get("last")
    print(f"\n[VIX-Konsistenz] VIX={vix} — VIX (30-Tage-ATM-Vol des S&P) muss ZWISCHEN")
    print("  25Δ-Call-IV und 25Δ-Put-IV von SPY liegen (ATM sitzt zwischen den Flügeln).")
    for t in d.get("tickers", []):
        if t["ticker"] in ("SPY", "QQQ", "IWM"):
            cv, pv = t["call_25d"]["iv"] * 100, t["put_25d"]["iv"] * 100
            note = ""
            if t["ticker"] == "SPY" and vix:
                ok = "OK" if min(cv, pv) - 1 <= vix <= max(cv, pv) + 1 else "!!"
                note = f"   → {ok}: VIX {vix} muss in [{cv:.1f}%, {pv:.1f}%] liegen"
            print(f"  {t['ticker']:5} 25Δ-Call={cv:.1f}%  25Δ-Put={pv:.1f}%{note}")

    print("\n[Plausibilität] IV-Range + Skew-Vorzeichen (Put−Call):")
    bad = 0
    for t in sorted(d.get("tickers", []), key=lambda x: -x["skew_pts"]):
        pv, cv = t["put_25d"]["iv"] * 100, t["call_25d"]["iv"] * 100
        rng = "OK" if (5 <= pv <= 200 and 5 <= cv <= 200) else "!! Range"
        if rng != "OK":
            bad += 1
        print(f"  {t['ticker']:6} Put={pv:5.1f}%  Call={cv:5.1f}%  Skew={t['skew_pts']:+6.2f}pts  {rng}")
    print(f"\n  {len(d.get('tickers', []))} Ticker geprüft, {bad} mit Range-Auffälligkeit.")
    print("  (Put-Skew positiv = normale Index-/Aktien-Absicherungsprämie; negativ = Call-Skew, z.B. Squeeze-Namen.)")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", nargs="+", default=["SPY", "QQQ", "AAPL"])
    ap.add_argument("--live", action="store_true", help="Live-Cross-Check gegen marketdata (kostet Credits)")
    a = ap.parse_args()

    print("=== IV-Verifikation ===")
    offline_checks()

    if a.live:
        tok = os.environ.get("MARKETDATA_API_KEY", "")
        if not tok:
            print("\n[Live] MARKETDATA_API_KEY fehlt — Cross-Check übersprungen."); return 0
        print("\n[BS-Engine vs marketdata] (unsere BS-IV aus Mid vs marketdatas IV; Ziel |Δ|<1 Vol-Punkt)")
        for s in a.symbols:
            print(live_cross_check(s, tok))
    else:
        print("\n[Live] Mit --live gegen marketdata cross-checken (fetcht live Chains, kostet Credits).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
