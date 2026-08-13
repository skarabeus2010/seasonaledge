"""
scripts/compute_gamma_exposure.py — Dealer-Positioning-Greeks (GEX / Vanna / Charm)
====================================================================================
Holt die Options-Chain eines Underlyings von Yahoo (EOD, Crumb-Session wie fetch_event_data),
rechnet je Kontrakt Black-Scholes **Gamma, Vanna, Charm** und aggregiert die Dealer-Exposure.

  GEX   = Σ sign · Γ     · OI·100 · S²   · 0,01     ($-Gamma  pro 1 % Spot-Move)
  Vanna = Σ sign · Vanna · OI·100 · S    · 0,01     ($-Delta   pro 1 Vola-Punkt)
  Charm = Σ sign · Charm · OI·100 · S    / 365      ($-Delta-Drift pro Kalendertag)
  sign  = +1 Call, −1 Put   (naive Dealer-Konvention: long Calls / short Puts)

  Zero-Gamma-Flip = Spot-Level, an dem net-GEX das Vorzeichen wechselt (sticky-strike)
  Call-Wall = Strike ≥ Spot mit max. positivem Netto-Gamma; Put-Wall = Strike ≤ Spot mit max. negativem

BS-Formeln (mit Dividendenrendite q), verifiziert per Finite-Differenzen (`--self-test`):
  d1=(ln(S/K)+(r−q+σ²/2)T)/(σ√T),  d2=d1−σ√T
  Γ     = e^{−qT}·φ(d1)/(S·σ√T)
  Vanna = −e^{−qT}·φ(d1)·d2/σ
  Charm_call = q·e^{−qT}·N(d1)  − e^{−qT}·φ(d1)·(2(r−q)T − d2·σ√T)/(2T·σ√T)
  Charm_put  = −q·e^{−qT}·N(−d1) − e^{−qT}·φ(d1)·(2(r−q)T − d2·σ√T)/(2T·σ√T)

⚠️ ANNAHME: „naive" Dealer-Vorzeichen. Echte Dealer-Bücher sind unbekannt — Heuristik (wie bei
   Retail-Tools; SpotGamma nutzt ein proprietäres Modell → unsere Zahlen weichen ab). Immer kennzeichnen.

Aufruf:
  PYTHONUTF8=1 py -3.14 scripts/compute_gamma_exposure.py --self-test
  PYTHONUTF8=1 py -3.14 scripts/compute_gamma_exposure.py --ticker SPY --max-days 90
  PYTHONUTF8=1 py -3.14 scripts/compute_gamma_exposure.py --tickers SPY,QQQ,AAPL,NVDA --max-days 45
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from scipy.stats import norm

_ROOT = Path(__file__).resolve().parent.parent
_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
_OPT_HOSTS = ["https://query1.finance.yahoo.com", "https://query2.finance.yahoo.com"]
_R = 0.04  # risk-free proxy (Greeks sind kaum r-sensitiv)
_INDEX_TICKERS = {"SPY", "QQQ", "IWM", "DIA", "^SPX", "^GSPC", "SPX"}  # für den Markt-Gamma-Index

_SESSION: requests.Session | None = None
_CRUMB: str | None = None


# ─────────────────────────────────────────────────────── Black-Scholes-Greeks
def bs_greeks(S: float, K: float, T: float, sigma: float, typ: str,
              r: float = _R, q: float = 0.0) -> tuple[float, float, float]:
    """(gamma, vanna, charm) — gamma/vanna gleich für Call/Put; charm typ-abhängig (nur via q-Term).
    Einheiten: gamma pro 1$; vanna pro 1,0 Vola (=100 Vol-Punkte); charm pro Jahr."""
    if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
        return 0.0, 0.0, 0.0
    srt = sigma * math.sqrt(T)
    d1 = (math.log(S / K) + (r - q + 0.5 * sigma * sigma) * T) / srt
    d2 = d1 - srt
    pdf = norm.pdf(d1)
    eqt = math.exp(-q * T)
    gamma = eqt * pdf / (S * srt)
    vanna = -eqt * pdf * d2 / sigma
    shared = -eqt * pdf * (2 * (r - q) * T - d2 * srt) / (2 * T * srt)
    charm = (q * eqt * norm.cdf(d1) + shared) if typ == "call" else (-q * eqt * norm.cdf(-d1) + shared)
    return gamma, vanna, charm


def _self_test() -> int:
    """Finite-Differenzen-Beweis: analytische Greeks == numerische Ableitungen von Delta."""
    def delta(S, K, T, sig, typ, r, q):
        srt = sig * math.sqrt(T)
        d1 = (math.log(S / K) + (r - q + 0.5 * sig * sig) * T) / srt
        return math.exp(-q * T) * (norm.cdf(d1) if typ == "call" else norm.cdf(d1) - 1)

    print("=== Selbsttest: analytische Greeks vs. Finite-Differenzen (Δ) ===")
    ok = True
    for (S, K, T, sig, r, q) in [(100, 100, 0.25, 0.20, 0.04, 0.01),
                                 (100, 110, 0.08, 0.35, 0.04, 0.0),
                                 (250, 240, 0.5, 0.28, 0.03, 0.015)]:
        for typ in ("call", "put"):
            g, v, ch = bs_greeks(S, K, T, sig, typ, r, q)
            hS, hV, hT = S * 1e-4, 1e-5, 1e-5
            g_fd = (delta(S + hS, K, T, sig, typ, r, q) - delta(S - hS, K, T, sig, typ, r, q)) / (2 * hS)
            v_fd = (delta(S, K, T, sig + hV, typ, r, q) - delta(S, K, T, sig - hV, typ, r, q)) / (2 * hV)
            # charm = ∂Δ/∂t = −∂Δ/∂T  (t = Kalenderzeit vorwärts)
            ch_fd = -(delta(S, K, T + hT, sig, typ, r, q) - delta(S, K, T - hT, sig, typ, r, q)) / (2 * hT)
            for name, ana, fd in (("gamma", g, g_fd), ("vanna", v, v_fd), ("charm", ch, ch_fd)):
                rel = abs(ana - fd) / (abs(fd) + 1e-12)
                flag = "OK " if rel < 1e-4 else "!! "
                if rel >= 1e-4:
                    ok = False
                print(f"  {flag}{typ:<4} {name:<6} analytisch {ana:+.6e}  FD {fd:+.6e}  rel {rel:.1e}")
    print("=== " + ("ALLE GRÜN — Formeln bestätigt ===" if ok else "FEHLER — Formeln prüfen ==="))
    return 0 if ok else 1


# ─────────────────────────────────────────────────────── Yahoo-Chain
def _crumb_session():
    global _SESSION, _CRUMB
    if _SESSION is not None:
        return _SESSION, _CRUMB
    s = requests.Session(); s.headers.update(_HEADERS)
    try:
        s.get("https://fc.yahoo.com/", timeout=15, allow_redirects=True)
        r = s.get("https://query2.finance.yahoo.com/v1/test/getcrumb", timeout=15)
        _CRUMB = r.text.strip() if (r.status_code == 200 and len(r.text) < 50) else None
    except requests.RequestException:
        _CRUMB = None
    _SESSION = s
    return s, _CRUMB


def _fetch_options(ticker: str, date_epoch: int | None = None) -> dict:
    s, crumb = _crumb_session()
    q = f"?crumb={crumb}" if crumb else ""
    if date_epoch:
        q = (q + "&" if q else "?") + f"date={date_epoch}"
    for host in _OPT_HOSTS:
        try:
            r = s.get(f"{host}/v7/finance/options/{ticker}{q}", timeout=20)
            if r.status_code == 200:
                res = r.json().get("optionChain", {}).get("result", [])
                if res:
                    return res[0]
        except (requests.RequestException, ValueError):
            continue
    return {}


def _collect(ticker: str, max_days: int):
    root = _fetch_options(ticker)
    if not root:
        return None
    quote = root.get("quote", {}) or {}
    spot = quote.get("regularMarketPrice")
    q_yield = quote.get("trailingAnnualDividendYield") or 0.0   # Dividendenrendite (Dezimal)
    exps = root.get("expirationDates", []) or []
    now = time.time()
    keep = [e for e in exps if 0 <= (e - now) / 86400 <= max_days]
    contracts = []
    n_raw = 0   # alle gelieferten Kontrakte VOR dem OI/IV-Filter — Basis fuer den Plausibilitaetscheck
    for i, e in enumerate(keep):
        node = root if (i == 0 and root.get("options")) else _fetch_options(ticker, e)
        opts = (node.get("options") or [{}])[0]
        T = max((e - now) / (365 * 86400), 1e-6)
        exp = datetime.fromtimestamp(e, timezone.utc).strftime("%Y-%m-%d")
        for typ, arr in (("call", opts.get("calls", [])), ("put", opts.get("puts", []))):
            for o in arr:
                n_raw += 1
                K = o.get("strike"); oi = o.get("openInterest") or 0
                iv = o.get("impliedVolatility") or 0.0
                if K and oi and iv > 0:
                    contracts.append({"type": typ, "K": float(K), "oi": int(oi),
                                      "iv": float(iv), "T": T, "exp": exp})
        time.sleep(0.2)
    return {"spot": spot, "q": float(q_yield), "contracts": contracts,
            "n_exp": len(keep), "n_raw": n_raw}


# ─────────────────────────────────────────────────────── Aggregation
def _exposures(S: float, contracts: list, q: float):
    """(gex, vanna_exp, charm_exp) in Roh-$; sign = +Call/−Put."""
    gex = vex = cex = 0.0
    for c in contracts:
        g, v, ch = bs_greeks(S, c["K"], c["T"], c["iv"], c["type"], q=q)
        sign = 1.0 if c["type"] == "call" else -1.0
        oi_notional = c["oi"] * 100
        gex += sign * g * oi_notional * S * S * 0.01
        vex += sign * v * oi_notional * S * 0.01
        cex += sign * ch * oi_notional * S / 365.0
    return gex, vex, cex


def _zero_gamma(spot: float, contracts: list, q: float) -> float | None:
    lo, hi = spot * 0.80, spot * 1.20
    xs = [lo + (hi - lo) * i / 240 for i in range(241)]
    vals = [(x, _exposures(x, contracts, q)[0]) for x in xs]
    for (x0, v0), (x1, v1) in zip(vals, vals[1:]):
        if v0 == 0:
            return round(x0, 2)
        if v0 * v1 < 0:
            return round(x0 + (x1 - x0) * (-v0) / (v1 - v0), 2)
    return None


def _walls(spot: float, contracts: list, q: float):
    """Netto-Dealer-$-Gamma je Strike (Call +, Put −). Call-Wall = max positiv bei Strike ≥ Spot,
    Put-Wall = max negativ bei Strike ≤ Spot (Fallback: unbeschränkt)."""
    per: dict[float, float] = {}
    for c in contracts:
        g, _, _ = bs_greeks(spot, c["K"], c["T"], c["iv"], c["type"], q=q)
        dollar = g * c["oi"] * 100 * spot * spot * 0.01
        per[c["K"]] = per.get(c["K"], 0.0) + (dollar if c["type"] == "call" else -dollar)
    if not per:
        return None, None, None
    above = {k: v for k, v in per.items() if k >= spot}
    below = {k: v for k, v in per.items() if k <= spot}
    call_wall = max(above or per, key=(above or per).get)
    put_wall = min(below or per, key=(below or per).get)
    abs_gamma = max(per, key=lambda k: abs(per[k]))   # magnetischster Pin (max |Netto-Gamma|)
    return call_wall, put_wall, abs_gamma


def _profile(spot: float, contracts: list, q: float) -> list[dict]:
    """Netto-Dealer-Exposure JE STRIKE (für Vanna-/Gamma-/Charm-by-Strike-Charts)."""
    per: dict[float, dict] = {}
    for c in contracts:
        g, v, ch = bs_greeks(spot, c["K"], c["T"], c["iv"], c["type"], q=q)
        sign = 1.0 if c["type"] == "call" else -1.0
        n = c["oi"] * 100
        d = per.setdefault(c["K"], {"gamma": 0.0, "vanna": 0.0, "charm": 0.0, "oi_c": 0, "oi_p": 0})
        d["gamma"] += sign * g * n * spot * spot * 0.01
        d["vanna"] += sign * v * n * spot * 0.01
        d["charm"] += sign * ch * n * spot / 365.0
        d["oi_c" if c["type"] == "call" else "oi_p"] += c["oi"]
    out = []
    for K in sorted(per):
        d = per[K]
        out.append({"strike": K,
                    "gamma_usd_mn": round(d["gamma"] / 1e6, 3),
                    "vanna_usd_mn": round(d["vanna"] / 1e6, 3),
                    "charm_usd_mn": round(d["charm"] / 1e6, 3),
                    "oi_calls": d["oi_c"], "oi_puts": d["oi_p"]})
    return out


def _profile_by_term(spot: float, contracts: list, q: float) -> list[dict]:
    """Netto-Dealer-Exposure JE VERFALL (für Gamma-/Vanna-/Charm-by-Term-Charts)."""
    per: dict[str, dict] = {}
    for c in contracts:
        g, v, ch = bs_greeks(spot, c["K"], c["T"], c["iv"], c["type"], q=q)
        sign = 1.0 if c["type"] == "call" else -1.0
        n = c["oi"] * 100
        d = per.setdefault(c.get("exp", "?"), {"gamma": 0.0, "vanna": 0.0, "charm": 0.0})
        d["gamma"] += sign * g * n * spot * spot * 0.01
        d["vanna"] += sign * v * n * spot * 0.01
        d["charm"] += sign * ch * n * spot / 365.0
    return [{"exp": e,
             "gamma_usd_mn": round(per[e]["gamma"] / 1e6, 3),
             "vanna_usd_mn": round(per[e]["vanna"] / 1e6, 3),
             "charm_usd_mn": round(per[e]["charm"] / 1e6, 3)} for e in sorted(per)]


def _skew(spot: float, contracts: list) -> dict | None:
    """Vola-Skew der Front-Expiry: ATM-IV + OTM-Put(90%) − OTM-Call(110%) in Vol-Punkten.
    Positiv = Put-Skew (Index-typisch: Abwärts-Absicherung teurer)."""
    if not contracts:
        return None
    tmin = min(c["T"] for c in contracts)
    front = [c for c in contracts if abs(c["T"] - tmin) < 1e-9]

    def iv_at(target_k: float, typ: str):
        cands = [c for c in front if c["type"] == typ]
        return min(cands, key=lambda c: abs(c["K"] - target_k))["iv"] if cands else None

    atm = iv_at(spot, "call") or iv_at(spot, "put")
    put90 = iv_at(spot * 0.90, "put")
    call110 = iv_at(spot * 1.10, "call")
    skew = (put90 - call110) * 100 if (put90 and call110) else None
    return {"expiry": front[0].get("exp"),
            "atm_iv_pct": round(atm * 100, 2) if atm else None,
            "put_iv_90_pct": round(put90 * 100, 2) if put90 else None,
            "call_iv_110_pct": round(call110 * 100, 2) if call110 else None,
            "skew_pts": round(skew, 2) if skew is not None else None}


# Plausibilitaet der Chain. Yahoo liefert im Vormittagsfenster (UTC) die VOLLE Chain, aber mit
# openInterest=0 — der Filter in _collect wirft dann alles weg und analyze() meldete bisher
# trotzdem Erfolg mit einer Handvoll Kontrakten. Solche Zahlen sehen plausibel aus (z.B.
# „net-GEX -0.000 Mrd, short_gamma") und sind komplett wertlos. Der Check zielt bewusst auf die
# QUOTE brauchbar/geliefert statt auf absolute Mengen, damit echte illiquide Ticker nicht
# faelschlich als Fehlschlag gelten.
_MIN_RAW_FOR_CHECK = 100    # darunter ist die Chain zu klein fuer eine Aussage
_MIN_USABLE_RATIO = 0.05    # <5 % brauchbar bei voller Chain = OI-Fenster, kein Marktzustand


def analyze(ticker: str, max_days: int, with_profile: bool = False) -> dict | None:
    data = _collect(ticker, max_days)
    if not data or not data["spot"] or not data["contracts"]:
        return None
    n_raw, n_use = data.get("n_raw", 0), len(data["contracts"])
    if n_raw >= _MIN_RAW_FOR_CHECK and n_use < _MIN_USABLE_RATIO * n_raw:
        print(f"  [SKIP] {ticker}: {n_use}/{n_raw} Kontrakte brauchbar "
              f"({n_use/n_raw:.1%}) — Yahoo liefert kein Open Interest, kein valider Snapshot.",
              flush=True)
        return None
    spot, contracts, q = data["spot"], data["contracts"], data["q"]
    gex, vex, cex = _exposures(spot, contracts, q)
    cw, pw, ag = _walls(spot, contracts, q)
    return {
        "ticker": ticker, "spot": round(spot, 2), "div_yield": round(q, 4),
        "net_gex_usd_bn": round(gex / 1e9, 3),
        "net_vanna_usd_mn": round(vex / 1e6, 2),
        "net_charm_usd_mn_per_day": round(cex / 1e6, 2),
        "regime": "long_gamma" if gex > 0 else "short_gamma",
        "vol_regime": "vola-reduzierend" if gex > 0 else "vola-forcierend",
        "zero_gamma": _zero_gamma(spot, contracts, q),
        "call_wall": cw, "put_wall": pw, "abs_gamma": ag,
        "skew": _skew(spot, contracts),
        "n_contracts": len(contracts), "n_expiries": data["n_exp"],
        **({"profile": {"by_strike": _profile(spot, contracts, q),
                        "by_term": _profile_by_term(spot, contracts, q)}} if with_profile else {}),
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "note": "PoC · naive Dealer-Vorzeichen (long Calls/short Puts) = Heuristik, keine echten "
                "Dealer-Bücher · EOD-OI+IV von Yahoo · Greeks Black-Scholes (q=Div-Rendite)",
    }


def _print(o: dict):
    print("\n" + "=" * 60)
    print(f"  {o['ticker']}  Spot {o['spot']}   ({o['n_expiries']} Expiries, {o['n_contracts']} Kontrakte)")
    print("=" * 60)
    print(f"  net-GEX    {o['net_gex_usd_bn']:+.3f} Mrd $/1 %   → {o['regime']}")
    print(f"  net-Vanna  {o['net_vanna_usd_mn']:+.2f} Mio $/Vol-Pkt")
    print(f"  net-Charm  {o['net_charm_usd_mn_per_day']:+.2f} Mio $-Delta/Tag")
    print(f"  Zero-Gamma {o['zero_gamma']}   Call-Wall {o['call_wall']}   Put-Wall {o['put_wall']}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticker", help="einzelner Ticker")
    ap.add_argument("--tickers", help="Komma-Liste (Batch)")
    ap.add_argument("--max-days", type=int, default=90)
    ap.add_argument("--self-test", action="store_true", help="Greeks per Finite-Differenzen verifizieren")
    ap.add_argument("--profile", action="store_true", help="Per-Strike-Profil (Gamma/Vanna/Charm) mit ausgeben")
    ap.add_argument("--out-dir", default=str(_ROOT / "landing" / "data"))
    a = ap.parse_args()

    if a.self_test:
        return _self_test()

    tickers = ([a.ticker] if a.ticker else
               [t.strip().upper() for t in (a.tickers or "SPY").split(",") if t.strip()])
    outdir = Path(a.out_dir); outdir.mkdir(parents=True, exist_ok=True)
    results, failed = [], []
    for tk in tickers:
        print(f"[gex] {tk} …", flush=True)
        try:
            o = analyze(tk, a.max_days, with_profile=a.profile)
        except Exception as e:
            o = None; print(f"  [WARN] {tk}: {type(e).__name__}: {e}", flush=True)
        if not o:
            failed.append(tk); continue
        results.append(o)
        (outdir / f"gex_{tk}.json").write_text(json.dumps(o, indent=2, ensure_ascii=False), encoding="utf-8")
        if len(tickers) == 1:
            _print(o)

    if len(tickers) > 1 and results:
        print(f"\n{'Ticker':<8}{'Spot':>9}{'GEX(Mrd/1%)':>13}{'Vanna(M/pt)':>13}{'Charm(M/d)':>12}"
              f"{'Regime':>13}{'Flip':>9}{'CallW':>8}{'PutW':>8}")
        for o in results:
            print(f"{o['ticker']:<8}{o['spot']:>9}{o['net_gex_usd_bn']:>13.3f}"
                  f"{o['net_vanna_usd_mn']:>13.1f}{o['net_charm_usd_mn_per_day']:>12.1f}"
                  f"{o['regime']:>13}{str(o['zero_gamma']):>9}{str(o['call_wall']):>8}{str(o['put_wall']):>8}")
        # Markt-Gamma-Index (aggregiert aus den Index-Produkten, SpotGamma-Stil)
        idx = [o for o in results if o["ticker"] in _INDEX_TICKERS]
        gamma_index = None
        if idx:
            val = round(sum(o["net_gex_usd_bn"] for o in idx), 3)
            gamma_index = {"value_usd_bn_per_pct": val,
                           "vol_regime": "vola-reduzierend" if val > 0 else "vola-forcierend",
                           "components": [o["ticker"] for o in idx]}
            print(f"\n  ═══ MARKT-GAMMA-INDEX ({'+'.join(gamma_index['components'])}): "
                  f"{val:+.3f} Mrd $/1 %  → {gamma_index['vol_regime']} ═══")
        (outdir / "gex_summary.json").write_text(
            json.dumps({"generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                        "gamma_index": gamma_index, "tickers": results, "failed": failed},
                       indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\n[gex] {len(results)} ok, {len(failed)} ohne Daten: {failed}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
