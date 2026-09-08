#!/usr/bin/env python3
"""
backfill_skew_massive.py — 25Δ-Skew + ATM-IV-Historie aus Massive rekonstruieren.

WARUM SELBST RECHNEN: Massive liefert IV/Greeks ausschließlich im aktuellen
Snapshot — kein Endpoint mit Datumsparameter führt sie. Historisch gibt es nur
Preise (Aggregates/Trades/Quotes). Die IV wird deshalb je Kontrakt aus dem
Tagesschluss per Black-Scholes-Bisektion invertiert. Dasselbe Verfahren wie im
alten marketdata-Backfill (dort gegen echte IV verifiziert, <0,4 Vol-Punkte),
nur auf der einzigen Options-Quelle, die wir noch haben.

NEU gegenüber backfill_skew_history.py: **ATM-IV (50Δ) wird mitgepickt.** Ohne
sie gibt es kein echtes Zeta (call_zeta = 25ΔC-IV − ATM-IV). Der Frontend-
Fallback schätzt ATM sonst als Mittel der beiden Flügel — dabei wird
put_zeta = −call_zeta, beide Achsen des Vol-Regime-Radars werden spiegelbildlich
und der Call-/Put-Skew-Quadrant kollabiert auf seine Antidiagonale. Genau die
Information, für die die Zwei-Achsen-Darstellung existiert, ginge verloren.

ABLAUF je Ticker:
  1. Eigene Kursreihe -> Spot je Handelstag + Zieldaten
  2. Kontrakte im Fenster listen (expired=true UND false, paginiert)
  3. Je Zieldatum: Expiry ~30 DTE + Strikes in ±BAND des damaligen Spots,
     auf MAX_STRIKES je Seite ausgedünnt
  4. Für die VEREINIGUNG dieser Kontrakte Tagesbars holen — ein Call deckt den
     kompletten Zeitraum ab. Deshalb kosten tägliche Stützstellen kaum mehr als
     wöchentliche (--every-n-td 1 ist praktisch gratis).
  5. Je Zieldatum IV invertieren, Delta rechnen, 25ΔC/25ΔP/50Δ picken
  6. Inkrementell je Ticker mergen (überlebt Abbruch)

GRENZE: Aggregates sind TRADE-Preise, keine Bid/Ask-Mitte. Bei liquiden Namen
unkritisch; bei dünnen Strikes wird die IV verrauschter, Tage ohne Trade fehlen.
Die Abdeckung wird je Ticker mitgeloggt.

Nutzung:
  py -3.14 scripts/backfill_skew_massive.py --probe
  py -3.14 scripts/backfill_skew_massive.py --symbols MU DELL BE SMH ARM SNDK
  py -3.14 scripts/backfill_skew_massive.py --all --years 2
"""
from __future__ import annotations
import argparse, gc, json, math, os, socket, ssl, sys, time, urllib.error, urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

socket.setdefaulttimeout(30)

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
from shared.env_loader import load_env                                # noqa: E402
load_env()
from shared.yahoo_downloader import download_data, clear_cache        # noqa: E402
from shared.options_universe import all_option_tickers                # noqa: E402

_CTX = ssl.create_default_context(); _CTX.check_hostname = False; _CTX.verify_mode = ssl.CERT_NONE
_CONTRACTS = "https://api.polygon.io/v3/reference/options/contracts"
_AGGS = "https://api.polygon.io/v2/aggs/ticker/{occ}/range/1/day/{f}/{t}?adjusted=true&limit=50000"

_R = 0.045          # Risk-free-Näherung; q=0. Für Differenzen innerhalb einer Expiry unkritisch.
_THROTTLE = 0.05    # Flatrate, kleiner Puffer gegen Burst-429
_BAND = 0.30        # Strike-Fenster um den Spot des jeweiligen Zieldatums
_MAX_STRIKES = 24   # je Seite und Expiry — reicht, um 25Δ und 50Δ sauber zu klammern
_DELTA_TOL = 0.08   # wie in compute_options_skew.py: darüber ist die Stützstelle unbrauchbar
_DTE_MIN, _DTE_MAX = 10, 60

_DEFAULT = ["MU", "DELL", "BE", "SMH", "ARM", "SNDK", "AVGO", "NVDA", "AMD", "SPY", "QQQ"]


# ── Black-Scholes (self-contained, identisch zum marketdata-Backfill) ────────
def _cdf(x): return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _bs_price(S, K, T, sig, typ):
    if T <= 0 or sig <= 0 or S <= 0 or K <= 0:
        return max(0.0, (S - K) if typ == "call" else (K - S))
    srt = sig * math.sqrt(T)
    d1 = (math.log(S / K) + (_R + 0.5 * sig * sig) * T) / srt
    d2 = d1 - srt
    if typ == "call":
        return S * _cdf(d1) - K * math.exp(-_R * T) * _cdf(d2)
    return K * math.exp(-_R * T) * _cdf(-d2) - S * _cdf(-d1)


def _bs_delta(S, K, T, sig, typ):
    srt = sig * math.sqrt(T)
    d1 = (math.log(S / K) + (_R + 0.5 * sig * sig) * T) / srt
    return _cdf(d1) if typ == "call" else _cdf(d1) - 1.0


def _implied_vol(price, S, K, T, typ):
    """IV per Bisektion; None wenn kein Root (z.B. Preis = reiner innerer Wert)."""
    if price is None or price <= 0 or T <= 0:
        return None
    lo, hi = 1e-4, 5.0
    plo = _bs_price(S, K, T, lo, typ) - price
    phi = _bs_price(S, K, T, hi, typ) - price
    if plo * phi > 0:
        return None
    for _ in range(64):
        mid = 0.5 * (lo + hi)
        pm = _bs_price(S, K, T, mid, typ) - price
        if abs(pm) < 1e-6:
            return mid
        if plo * pm < 0:
            hi = mid
        else:
            lo, plo = mid, pm
    return 0.5 * (lo + hi)


# ── Massive-REST ────────────────────────────────────────────────────────────
def _get(url: str, key: str, tries: int = 5):
    full = url + ("&" if "?" in url else "?") + "apiKey=" + key
    for i in range(tries):
        time.sleep(_THROTTLE)
        try:
            return json.loads(urllib.request.urlopen(
                urllib.request.Request(full, headers={"User-Agent": "SeasonAlpha/1.0"}),
                timeout=30, context=_CTX).read())
        except urllib.error.HTTPError as e:
            if e.code == 429 and i < tries - 1:
                time.sleep(2.0 * (i + 1)); continue
            raise
        except Exception:
            if i < tries - 1:
                time.sleep(1.0 * (i + 1)); continue
            raise


def _list_contracts(sym: str, key: str, exp_lo: str, exp_hi: str, k_lo: float, k_hi: float) -> list:
    """Alle Kontrakte im Fenster. expired=true UND false — sonst fehlen entweder
    die alten (verfallen) oder die jungen (noch laufend) Expiries."""
    out = []
    for expired in ("true", "false"):
        url = (f"{_CONTRACTS}?underlying_ticker={sym}&expired={expired}"
               f"&expiration_date.gte={exp_lo}&expiration_date.lte={exp_hi}"
               f"&strike_price.gte={round(k_lo, 2)}&strike_price.lte={round(k_hi, 2)}&limit=1000")
        pages = 0
        while url and pages < 40:
            d = _get(url, key)
            out += d.get("results") or []
            url = d.get("next_url")
            pages += 1
    return out


def _bars(occ: str, key: str, d_from: str, d_to: str, strict: bool = False) -> dict:
    """Tagesschluss je Datum für EINEN Kontrakt — ein Call für den ganzen Zeitraum.

    strict=True lässt Fehler durch (für die Probe). Im Massenlauf wird geschluckt,
    sonst reißt ein einzelner toter Kontrakt den ganzen Ticker ab."""
    try:
        d = _get(_AGGS.format(occ=occ, f=d_from, t=d_to), key)
    except Exception:
        if strict:
            raise
        return {}
    out = {}
    for b in d.get("results") or []:
        try:
            ds = datetime.fromtimestamp(b["t"] / 1000, tz=timezone.utc).date().isoformat()
            if b.get("c"):
                # Volumen mitnehmen: der Schlusskurs ist der LETZTE Trade, bei duennen
                # Kontrakten also womoeglich Stunden alt. Gepaart mit dem Schlusskurs
                # des Basiswerts ergibt das eine zu tiefe IV. Das Volumen ist der
                # einzige Hinweis auf die Frische, den die Aggregates hergeben.
                out[ds] = (float(b["c"]), float(b.get("v") or 0))
        except Exception:
            continue
    return out


_QUOTES = ("https://api.polygon.io/v3/quotes/{occ}"
           "?timestamp.gte={f}&timestamp.lte={t}&order=desc&sort=timestamp&limit=1")


def _quote_mid(occ: str, key: str, d: str, strict: bool = False):
    """Letzte Bid/Ask-Mitte vor Handelsschluss. None wenn keine Quote.

    Warum überhaupt: Die Aggregates liefern den letzten TRADE. Bei dünnen
    Kontrakten liegt der Stunden vor dem Schluss, wird aber mit dem
    SCHLUSSKURS des Basiswerts gepaart — daraus entsteht eine verzerrte IV
    (MU 25Δ-Call: 4 Vol-Punkte zu tief). Eine Quote zum Schluss ist zeitlich
    sauber und kennt keine Aggressor-Verzerrung.

    Fenster 19:30-21:05 UTC deckt Sommer- (Close 20:00) und Winterzeit
    (21:00) ab; die letzte Quote darin ist in beiden Fällen die zum Schluss."""
    url = _QUOTES.format(occ=occ, f=f"{d}T19:30:00Z", t=f"{d}T21:05:00Z")
    try:
        r = _get(url, key)
    except Exception:
        if strict:
            raise
        return None
    res = r.get("results") or []
    if not res:
        return None
    q = res[0]
    b, a = q.get("bid_price"), q.get("ask_price")
    if not b or not a or a < b:
        return None
    return {"mid": round((b + a) / 2, 4), "bid": b, "ask": a,
            "spread_pct": round(100 * (a - b) / ((a + b) / 2), 1) if (a + b) else None}


def _closes(sym: str) -> dict:
    """Eigene Kursreihe: {ISO-Datum: Close}. Liefert Spot + echte Handelstage."""
    try:
        df = download_data(sym, period="max")
    except Exception:
        clear_cache(); gc.collect(); return {}
    if df is None or len(df) == 0:
        clear_cache(); gc.collect(); return {}
    dts = [str(x)[:10] for x in (df["Date"] if "Date" in df.columns else df.index).tolist()]
    vals = [float(v) for v in df["Close"].to_numpy()]
    clear_cache(); gc.collect()
    return {d: v for d, v in zip(dts, vals) if v == v and v > 0}


# ── Rekonstruktion ──────────────────────────────────────────────────────────
_CM_DAYS = 30       # Ziel-Laufzeit der Reihe (konstante Maturität)


def _cm_interp(v1, t1, v2, t2, t_target=_CM_DAYS):
    """IV auf konstante Laufzeit interpolieren — linear in der TOTALEN VARIANZ.

    Warum das nötig ist: Monatsverfälle erzeugen einen Sägezahn. Die Laufzeit
    läuft von ~46 Tagen auf ~10 herunter und springt beim Roll zurück, und die
    IV folgt der Term-Struktur mit (MU: ATM 0,52 bei 16 Tagen, 0,65 bei 42).
    Ein Percentil über so eine Reihe rankt die Position im Verfallszyklus, nicht
    den Skew — die Tagesänderung von call_zeta hatte ein p90 von 6,8 Punkten.

    Linear in σ²·T (nicht in σ), weil sich Varianz über die Zeit addiert. Das
    ist dieselbe Interpolation, die der VIX für seine 30-Tage-Konstante nutzt."""
    if v1 is None or v2 is None or t1 is None or t2 is None or t1 == t2:
        return None
    if t1 > t2:
        v1, t1, v2, t2 = v2, t2, v1, t1
    w1, w2 = v1 * v1 * t1, v2 * v2 * t2          # totale Varianz je Stützstelle
    var = w1 + (w2 - w1) * (t_target - t1) / (t2 - t1)
    if var <= 0 or t_target <= 0:
        return None
    return round(math.sqrt(var / t_target), 4)


def _is_monthly(iso: str) -> bool:
    """Standard-Monatsverfall = 3. Freitag des Monats (Tag 15-21 und ein Freitag)."""
    d = date.fromisoformat(iso)
    return d.weekday() == 4 and 15 <= d.day <= 21


def _plan(closes: dict, contracts: list, targets: list,
          prefer_monthly: bool = True) -> tuple[dict, dict]:
    """Je Zieldatum Expiry+Kontrakte festlegen. Rückgabe: (plan, benötigte Kontrakte)."""
    by_exp: dict[str, list] = {}
    for c in contracts:
        e = c.get("expiration_date")
        if e and c.get("strike_price") and c.get("contract_type") in ("call", "put"):
            by_exp.setdefault(e, []).append(c)
    exps = sorted(by_exp)
    plan, need = {}, {}
    for d in targets:
        spot = closes[d]
        cand = [e for e in exps if e > d]
        if not cand:
            continue
        dd = date.fromisoformat(d)
        # Standard-Monatsverfall bevorzugen (3. Freitag), dann irgendein Freitag.
        # Blind die 30-DTE-naechste Laufzeit zu nehmen greift bei liquiden Titeln
        # die Mittwochs-Weeklies ab — die 30 Tage im Voraus kaum handeln (keine
        # Trades = keine Bars) und eine Percentile-Reihe zusaetzlich inhomogen
        # machen. Die Liquiditaet sitzt im Monatsverfall.
        pool = cand
        if prefer_monthly:
            pool = ([e for e in cand if _is_monthly(e)]
                    or [e for e in cand if date.fromisoformat(e).weekday() == 4]
                    or cand)
        # ZWEI Verfälle wählen, die _CM_DAYS klammern — Grundlage für die
        # Interpolation auf konstante Laufzeit. Nur einen zu nehmen erzeugt den
        # Sägezahn (Laufzeit läuft von ~46 auf ~10 Tage und springt beim Roll
        # zurück, die IV folgt der Term-Struktur mit).
        dtes = sorted(((date.fromisoformat(e) - dd).days, e) for e in pool)
        below = [x for x in dtes if _DTE_MIN <= x[0] <= _CM_DAYS]
        above = [x for x in dtes if _CM_DAYS < x[0] <= _DTE_MAX]
        legs_raw = []
        if below:
            legs_raw.append(below[-1])            # größte Laufzeit ≤ Ziel
        if above:
            legs_raw.append(above[0])             # kleinste Laufzeit > Ziel
        if not legs_raw:
            continue
        lo, hi = spot * (1 - _BAND), spot * (1 + _BAND)
        legs = []
        for dte, exp in legs_raw:
            picked = []
            for typ in ("call", "put"):
                ss = sorted((c for c in by_exp[exp]
                             if c["contract_type"] == typ and lo <= c["strike_price"] <= hi),
                            key=lambda c: c["strike_price"])
                if len(ss) > _MAX_STRIKES:             # gleichmäßig ausdünnen
                    step = len(ss) / _MAX_STRIKES
                    ss = [ss[int(i * step)] for i in range(_MAX_STRIKES)]
                picked += ss
            if len(picked) < 6:
                continue
            legs.append((exp, dte, [c["ticker"] for c in picked]))
            for c in picked:
                need[c["ticker"]] = c
        if legs:
            plan[d] = legs
    return plan, need


def _leg_ivs(d: str, spot: float, dte: int, occs: list, need: dict, bars: dict,
             min_vol: float = 0.0, vol_pctl: float = 0.0):
    """Rohe 25Δ-Call/Put- und ATM-IV EINER Expiry. None wenn nicht klammerbar.

    Gegen den Stale-Print-Bias (letzter Trade Stunden vor Schluss, gepaart mit
    dem Schlusskurs des Basiswerts) zwei Filter:

    min_vol   absolute Volumenschwelle. Taugt nur ticker-spezifisch: 200
              Kontrakte sind bei MU viel, bei SPY nichts. Global gesetzt
              rettet sie MU und zerstoert SPY (dort faellt der ATM-Pick auf
              einen entfernteren Strike, dessen IV die Smile-Kruemmung anhebt).
    vol_pctl  Perzentil-Schwelle innerhalb der Kandidaten DIESES Tages — das
              normiert sich selbst auf das Liquiditaetsniveau des Tickers.
              0.5 verwirft die untere Haelfte."""
    T = dte / 365.0
    cutoff = 0.0
    if vol_pctl > 0:
        vols = sorted(rec[1] for occ in occs
                      if (rec := bars.get(occ, {}).get(d)) is not None)
        if vols:
            cutoff = vols[min(len(vols) - 1, int(len(vols) * vol_pctl))]
    best: dict = {"call": {}, "put": {}}
    for occ in occs:
        rec = bars.get(occ, {}).get(d)
        if not rec:
            continue
        px, vol = rec
        if min_vol and vol < min_vol:
            continue
        if cutoff and vol < cutoff:
            continue
        c = need[occ]
        typ, K = c["contract_type"], float(c["strike_price"])
        iv = _implied_vol(px, spot, K, T, typ)
        if iv is None or iv <= 0.01 or iv > 4.0:
            continue
        dl = _bs_delta(spot, K, T, iv, typ)
        for tgt in (0.25, 0.50):
            dist = abs(abs(dl) - tgt)
            cur = best[typ].get(tgt)
            if cur is None or dist < cur[0]:
                best[typ][tgt] = (dist, iv)

    def _take(typ, tgt):
        v = best[typ].get(tgt)
        return v[1] if (v and v[0] <= _DELTA_TOL) else None

    call_iv, put_iv = _take("call", 0.25), _take("put", 0.25)
    atm_c, atm_p = _take("call", 0.50), _take("put", 0.50)
    if call_iv is None or put_iv is None:
        return None
    iv_atm = round((atm_c + atm_p) / 2, 4) if (atm_c and atm_p) else (atm_c or atm_p)
    return {"dte": dte, "call_iv": call_iv, "put_iv": put_iv, "iv_atm": iv_atm}


def _reconstruct(d: str, spot: float, legs: list, need: dict, bars: dict,
                 min_vol: float = 0.0, vol_pctl: float = 0.0) -> dict | None:
    """Konstant-30-Tage-Werte für einen Handelstag.

    Rechnet die rohen IVs an den ein bis zwei klammernden Verfällen und
    interpoliert sie in der totalen Varianz auf _CM_DAYS. Ohne diesen Schritt
    misst die Reihe die Position im Verfallszyklus statt den Skew."""
    got = []
    for exp, dte, occs in legs:
        v = _leg_ivs(d, spot, dte, occs, need, bars, min_vol=min_vol, vol_pctl=vol_pctl)
        if v:
            got.append(v)
    if not got:
        return None

    if len(got) >= 2:
        a, b = got[0], got[1]
        call_iv = _cm_interp(a["call_iv"], a["dte"], b["call_iv"], b["dte"])
        put_iv = _cm_interp(a["put_iv"], a["dte"], b["put_iv"], b["dte"])
        iv_atm = (_cm_interp(a["iv_atm"], a["dte"], b["iv_atm"], b["dte"])
                  if (a["iv_atm"] and b["iv_atm"]) else None)
        dte_out, mode = _CM_DAYS, "cm"
    else:
        # Nur eine Stützstelle: ohne zweiten Punkt keine Interpolation möglich.
        # Dann nur akzeptieren, wenn die Laufzeit ohnehin nah am Ziel liegt —
        # sonst wandert genau der Sägezahn zurück in die Reihe.
        a = got[0]
        if abs(a["dte"] - _CM_DAYS) > 8:
            return None
        call_iv, put_iv, iv_atm = a["call_iv"], a["put_iv"], a["iv_atm"]
        dte_out, mode = a["dte"], "single"
    if call_iv is None or put_iv is None:
        return None

    r = {"date": d, "dte": dte_out, "cm_mode": mode,
         "put_iv": round(put_iv, 4), "call_iv": round(call_iv, 4),
         "skew_pts": round((put_iv - call_iv) * 100, 2),
         "reconstructed": True, "src": "massive"}
    if iv_atm:
        r["iv_atm"] = round(iv_atm, 4)
        r["call_zeta_pts"] = round((call_iv - iv_atm) * 100, 2)
        r["put_zeta_pts"] = round((put_iv - iv_atm) * 100, 2)
        r["bfly_pts"] = round(((put_iv + call_iv) / 2 - iv_atm) * 100, 2)
    return r


def run_ticker(sym: str, key: str, years: float, every: int, hist: dict, overwrite: bool,
               min_vol: float = 0.0, vol_pctl: float = 0.0) -> int:
    closes = _closes(sym)
    if not closes:
        print(f"  {sym:6} keine Kursreihe — übersprungen", flush=True); return 0
    cutoff = (date.today() - timedelta(days=int(years * 365))).isoformat()
    traded = sorted(d for d in closes if d >= cutoff)
    targets = traded[::max(1, every)]
    if len(targets) < 5:
        print(f"  {sym:6} zu wenig Handelstage im Fenster", flush=True); return 0

    arr = hist.setdefault(sym, [])
    have = {e["date"] for e in arr} if not overwrite else set()
    todo = [d for d in targets if d not in have]
    if not todo:
        print(f"  {sym:6} bereits vollständig ({len(arr)} Punkte)", flush=True); return 0

    spots = [closes[d] for d in todo]
    k_lo, k_hi = min(spots) * (1 - _BAND) * 0.9, max(spots) * (1 + _BAND) * 1.1
    exp_lo = todo[0]
    exp_hi = (date.fromisoformat(todo[-1]) + timedelta(days=_DTE_MAX + 5)).isoformat()

    contracts = _list_contracts(sym, key, exp_lo, exp_hi, k_lo, k_hi)
    if not contracts:
        print(f"  {sym:6} keine Kontrakte gelistet", flush=True); return 0
    plan, need = _plan(closes, contracts, todo)
    if not plan:
        print(f"  {sym:6} kein Zieldatum planbar (Kontrakte={len(contracts)})", flush=True); return 0
    print(f"  {sym:6} {len(todo)} Ziele · {len(contracts)} Kontrakte gelistet · "
          f"{len(need)} Bars-Abrufe …", flush=True)

    bars, n = {}, 0
    for occ in need:
        bars[occ] = _bars(occ, key, exp_lo, todo[-1])
        n += 1
        if n % 200 == 0:
            print(f"    … {n}/{len(need)} Bars", flush=True)

    added = 0
    for d, legs in sorted(plan.items()):
        r = _reconstruct(d, closes[d], legs, need, bars, min_vol=min_vol, vol_pctl=vol_pctl)
        if r:
            arr.append(r); added += 1
    # Dedup je Datum (neuere Rekonstruktion gewinnt), dann sortieren
    ded = {}
    for e in arr:
        ded[e["date"]] = e
    hist[sym] = sorted(ded.values(), key=lambda e: e["date"])[-900:]
    cov = 100.0 * added / max(1, len(plan))
    print(f"  {sym:6} +{added} Punkte (Abdeckung {cov:.0f}% der geplanten Tage, "
          f"gesamt {len(hist[sym])})", flush=True)
    return added


def probe(sym: str, key: str) -> int:
    """Prüft die zwei Annahmen, auf denen der Backfill steht — vor dem langen Lauf."""
    print(f"=== PROBE {sym} ===", flush=True)
    closes = _closes(sym)
    if not closes:
        print("[FAIL] keine Kursreihe"); return 1
    d = sorted(closes)[-40]                      # ~2 Monate zurück: Expiry sicher verfallen
    spot = closes[d]
    print(f"[1] Zieldatum {d}, Spot {spot:.2f}", flush=True)

    exp_hi = (date.fromisoformat(d) + timedelta(days=_DTE_MAX)).isoformat()
    cs = _list_contracts(sym, key, d, exp_hi, spot * 0.7, spot * 1.3)
    print(f"[2] Kontrakte gelistet: {len(cs)}", flush=True)
    if not cs:
        print("[FAIL] Listing leer — expired-Parameter oder Strike-Band prüfen"); return 2

    plan, need = _plan(closes, cs, [d])
    if not plan:
        print("[FAIL] kein planbares Zieldatum"); return 3
    legs = plan[d]
    exp, dte, occs = legs[0]
    _wd = date.fromisoformat(exp).strftime("%a")
    _kind = "Monatsverfall" if _is_monthly(exp) else (
        "Freitags-Weekly" if date.fromisoformat(exp).weekday() == 4 else "NICHT-Freitag (illiquide!)")
    print(f"[3] {len(legs)} Verfall/Verfaelle fuer konstante {_CM_DAYS}d: "
          + " + ".join(f"{e} (DTE {t}, {len(o)} Kontr.)" for e, t, o in legs), flush=True)

    # [4] Der kritische Test — und er muss die drei Ursachen TRENNEN:
    #     (a) Abo deckt historische Options-Aggregates nicht ab  -> HTTP-Fehler
    #     (b) verfallene Kontrakte generell gesperrt              -> leer, aber aktive gehen
    #     (c) kein Trade an genau diesem Tag                      -> leer, aber Range hat Daten
    probe_occ = occs[len(occs) // 4]                      # near-the-money, nicht der Rand
    print(f"[4] Roh-Test am verfallenen Kontrakt {probe_occ}", flush=True)
    url = _AGGS.format(occ=probe_occ, f=d, t=d)
    print(f"    URL: {url.split('?')[0]}", flush=True)
    try:
        raw = _get(url, key)
        print(f"    Antwort: status={raw.get('status')!r} resultsCount={raw.get('resultsCount')} "
              f"queryCount={raw.get('queryCount')}", flush=True)
        if raw.get("message") or raw.get("error"):
            print(f"    message={raw.get('message') or raw.get('error')}", flush=True)
    except Exception as e:
        print(f"    [HTTP-FEHLER] {type(e).__name__}: {str(e)[:200]}", flush=True)
        print("\n[FAIL] (a) Der Endpoint antwortet gar nicht — Abo/Tier deckt historische "
              "Options-Aggregates nicht ab. Massive-Plan pruefen.", flush=True)
        return 4

    # (c) ausschliessen: weiteres Fenster um das Zieldatum
    wide_f = (date.fromisoformat(d) - timedelta(days=20)).isoformat()
    wide = _bars(probe_occ, key, wide_f, exp, strict=True)
    print(f"    Im Fenster {wide_f}..{exp}: {len(wide)} Handelstage mit Kurs", flush=True)
    if wide:
        ds = sorted(wide)
        print(f"    z.B. {ds[0]}: Kurs {wide[ds[0]][0]} Vol {wide[ds[0]][1]:.0f}  …  "
              f"{ds[-1]}: Kurs {wide[ds[-1]][0]} Vol {wide[ds[-1]][1]:.0f}", flush=True)

    bars, hit = {}, 0
    for occ in occs:
        bars[occ] = _bars(occ, key, wide_f, exp)
        if bars[occ].get(d):
            hit += 1
    any_data = sum(1 for b in bars.values() if b)
    print(f"[4b] {hit}/{len(occs)} Kontrakte mit Kurs am {d} · "
          f"{any_data}/{len(occs)} mit Kursen irgendwo im Fenster", flush=True)

    if hit == 0:
        if any_data:
            print(f"\n[TEILWEISE] (c) Daten sind da, aber nicht am {d} — die Kontrakte haben an "
                  "diesem Tag nicht gehandelt. Fix: Zieldatum auf den naechsten Tag mit Kursen "
                  "schieben statt zu verwerfen.", flush=True)
            return 6
        # (b) pruefen: geht ein AKTIVER Kontrakt?
        print("\n[5] Gegenprobe mit AKTIVEM (nicht verfallenem) Kontrakt …", flush=True)
        today = date.today().isoformat()
        fut = (date.today() + timedelta(days=200)).isoformat()
        act = _list_contracts(sym, key, today, fut, closes[sorted(closes)[-1]] * 0.9,
                              closes[sorted(closes)[-1]] * 1.1)
        act = [c for c in act if c.get("expiration_date", "") > today]
        if act:
            a_occ = act[len(act) // 2]["ticker"]
            ab = _bars(a_occ, key, (date.today() - timedelta(days=30)).isoformat(), today)
            print(f"    aktiver Kontrakt {a_occ}: {len(ab)} Handelstage", flush=True)
            if ab:
                print("\n[FAIL] (b) Aktive Kontrakte liefern Bars, verfallene nicht. Historische "
                      "Rekonstruktion ueber Aggregates ist damit versperrt.", flush=True)
                return 7
        print("\n[FAIL] Aggregates liefern generell keine Options-Bars — Abo/Tier pruefen.", flush=True)
        return 4

    r = _reconstruct(d, spot, legs, need, bars)
    if not r:
        print("[FAIL] Rekonstruktion ergab nichts (25D nicht klammerbar)"); return 5
    print(f"[5] Rekonstruktion OK:", flush=True)
    for k in ("date", "dte", "cm_mode", "call_iv", "put_iv", "iv_atm",
              "call_zeta_pts", "put_zeta_pts", "skew_pts", "bfly_pts"):
        print(f"      {k:<15} {r.get(k)}", flush=True)
    print("\n[OK] Alle Annahmen bestaetigt — der Backfill kann laufen.", flush=True)
    return 0


def probe_quotes(sym: str, key: str) -> int:
    """Prüft den Quotes-Weg — und misst direkt, was er gegenüber Trades bringt.

    Zwei Fragen auf einmal:
      (1) Liefert der Quotes-Endpoint überhaupt für VERFALLENE Kontrakte?
      (2) Wie groß ist die Lücke Trade-Schluss vs. Quote-Mitte, und rettet sie
          das Zeta? Nur das entscheidet, ob der Zwei-Pass-Umbau lohnt."""
    print(f"=== QUOTES-PROBE {sym} ===", flush=True)
    closes = _closes(sym)
    if not closes:
        print("[FAIL] keine Kursreihe"); return 1
    d = sorted(closes)[-40]
    spot = closes[d]
    print(f"[1] Zieldatum {d}, Spot {spot:.2f}", flush=True)

    exp_hi = (date.fromisoformat(d) + timedelta(days=_DTE_MAX)).isoformat()
    cs = _list_contracts(sym, key, d, exp_hi, spot * 0.7, spot * 1.3)
    plan, need = _plan(closes, cs, [d])
    if not plan:
        print("[FAIL] kein planbares Zieldatum"); return 3
    legs = plan[d]
    exp, dte, occs = legs[0]
    print(f"[2] Expiry {exp} · DTE {dte} · {len(occs)} Kontrakte", flush=True)

    # Roh-Test am ersten Kontrakt: antwortet der Endpoint fuer Verfallenes?
    print(f"[3] Roh-Test {occs[0]}", flush=True)
    try:
        q0 = _quote_mid(occs[0], key, d, strict=True)
        print(f"    {'Quote: ' + str(q0) if q0 else 'keine Quote im Fenster'}", flush=True)
    except Exception as e:
        print(f"    [HTTP-FEHLER] {type(e).__name__}: {str(e)[:200]}", flush=True)
        print("\n[FAIL] Quotes-Endpoint nicht verfuegbar (Abo/Tier). Der Zwei-Pass-Weg "
              "ist damit versperrt — bleibt die Vorwaerts-Akkumulation.", flush=True)
        return 4

    bars_t = {occ: _bars(occ, key, d, d) for occ in occs}
    bars_q, hits, spreads = {}, 0, []
    print(f"[4] Quotes fuer {len(occs)} Kontrakte …", flush=True)
    for occ in occs:
        q = _quote_mid(occ, key, d)
        if q:
            hits += 1
            spreads.append(q["spread_pct"] or 0)
            bars_q[occ] = {d: (q["mid"], 1e9)}       # Volumen irrelevant, Quote ist frisch
        else:
            bars_q[occ] = {}
    print(f"    {hits}/{len(occs)} mit Quote · mittlerer Spread "
          f"{sum(spreads)/len(spreads):.1f}%" if spreads else "    keine Quotes", flush=True)
    if hits == 0:
        print("\n[FAIL] Keine Quotes fuer verfallene Kontrakte.", flush=True); return 5

    # Die eigentliche Aussage: Trade-Schluss gegen Quote-Mitte je Kontrakt
    print(f"\n[5] Trade-Schluss vs. Quote-Mitte (Auszug):", flush=True)
    print(f"    {'Strike':>9}{'Typ':>6}{'Vol':>8}{'Trade':>9}{'Quote':>9}{'Abw %':>8}", flush=True)
    shown = 0
    for occ in occs:
        t, q = bars_t.get(occ, {}).get(d), bars_q.get(occ, {}).get(d)
        if not t or not q or shown >= 10:
            continue
        c = need[occ]
        dev = 100 * (t[0] - q[0]) / q[0] if q[0] else 0
        print(f"    {c['strike_price']:>9.1f}{c['contract_type']:>6}{t[1]:>8.0f}"
              f"{t[0]:>9.2f}{q[0]:>9.2f}{dev:>+8.1f}", flush=True)
        shown += 1

    print(f"\n[6] Rekonstruktion im Vergleich:", flush=True)
    rt = _reconstruct(d, spot, [(exp, dte, occs)], need, bars_t)
    rq = _reconstruct(d, spot, [(exp, dte, occs)], need, bars_q)
    print(f"    {'Quelle':<14}{'ATM':>8}{'Call':>8}{'Put':>8}{'cZeta':>8}{'pZeta':>8}", flush=True)
    for lbl, r in (("Trades", rt), ("Quotes", rq)):
        if not r:
            print(f"    {lbl:<14} keine Rekonstruktion", flush=True); continue
        print(f"    {lbl:<14}{(r.get('iv_atm') or 0)*100:>8.2f}{(r.get('call_iv') or 0)*100:>8.2f}"
              f"{(r.get('put_iv') or 0)*100:>8.2f}{r.get('call_zeta_pts') or 0:>+8.2f}"
              f"{r.get('put_zeta_pts') or 0:>+8.2f}", flush=True)
    print("\n[OK] Quotes verfuegbar. Ob sie das Zeta retten, zeigt der Vergleich oben — "
          "massgeblich ist ein --verify-Lauf gegen die Provider-Werte.", flush=True)
    return 0


def verify(syms: list, key: str, min_vol: float = 0.0, vol_pctl: float = 0.0) -> int:
    """Rekonstruktion gegen die Provider-IV der Vorwaerts-Akkumulation halten.

    Die History enthaelt Eintraege OHNE 'reconstructed' — die stammen aus dem
    taeglichen Snapshot und tragen die IV des Providers. Genau diese Tage noch
    einmal aus Preisen zu rekonstruieren zeigt, wie gut die BS-Inversion trifft.
    Ohne diesen Abgleich waere der Backfill nur intern konsistent, nicht richtig."""
    hp = _ROOT / "landing/data/options_skew_history.json"
    if not hp.exists():
        print("[FAIL] keine History-Datei."); return 1
    hist = json.loads(hp.read_text(encoding="utf-8"))

    print(f"{'Ticker':<6}{'Modus':<11}{'DTE':>4}{'ATM':>8}{'Call':>8}{'Put':>8}"
          f"{'Skew':>8}{'cZeta':>8}{'pZeta':>8}", flush=True)
    print("-" * 67, flush=True)
    zeta_devs: list[float] = []
    flips: list[str] = []
    for sym in syms:
        ref = [e for e in hist.get(sym, [])
               if not e.get("reconstructed") and e.get("iv_atm") and e.get("call_iv")]
        if not ref:
            print(f"{sym:<7} keine Provider-Eintraege zum Vergleichen", flush=True); continue
        closes = _closes(sym)
        # Provider-Eintraege tragen (historisch) den Cron-Laufzeitpunkt, nicht den
        # Handelstag — der Cron laeuft auch Sa/So/feiertags. Auf die tatsaechliche
        # Session ziehen; die Kursreihe IST der Handelskalender.
        sess = {}
        for e in ref:
            d = e["date"]
            if d not in closes:
                prior = [x for x in closes if x < d]
                if not prior:
                    continue
                d = max(prior)
            sess.setdefault(d, e)              # Sa/So/Feiertag fallen auf dieselbe Session
        if not sess:
            print(f"{sym:<7} Provider-Tage nicht auf eine Session abbildbar", flush=True); continue
        ref = [(d, e) for d, e in sorted(sess.items())]
        dates = [d for d, _ in ref]

        spots = [closes[d] for d in dates]
        contracts = _list_contracts(sym, key, dates[0],
                                    (date.fromisoformat(dates[-1]) + timedelta(days=_DTE_MAX + 5)).isoformat(),
                                    min(spots) * 0.6, max(spots) * 1.4)
        # ZWEI Rekonstruktionen, um die Laufzeit als Ursache zu isolieren:
        # der Provider-Eintrag stammt aus der Zeit VOR der Monatspraeferenz, nahm
        # also die 30-Tage-naechste Expiry (womoeglich eine Weekly).
        plan_m, need_m = _plan(closes, contracts, dates, prefer_monthly=True)
        plan_n, need_n = _plan(closes, contracts, dates, prefer_monthly=False)
        need = {**need_m, **need_n}
        bars = {occ: _bars(occ, key, dates[0], dates[-1]) for occ in need}

        def _row(lbl, dte, atm, c, p):
            sk = (p - c) * 100 if (c and p) else None
            cz = (c - atm) * 100 if (c and atm) else None
            pz = (p - atm) * 100 if (p and atm) else None
            print(f"{sym:<6}{lbl:<11}{dte if dte else '?':>4}"
                  f"{atm*100 if atm else 0:>8.2f}{c*100 if c else 0:>8.2f}{p*100 if p else 0:>8.2f}"
                  f"{sk:>+8.2f}{cz:>+8.2f}{pz:>+8.2f}", flush=True)
            return sk, cz, pz

        for d, e in ref:
            print(f"  -- {sym} {d} " + "-" * 40, flush=True)
            _, pcz, ppz = _row("Provider", e.get("dte"), e["iv_atm"], e["call_iv"], e["put_iv"])
            for lbl, pl, nd in (("Monatsverf.", plan_m, need_m), ("Naechst-30", plan_n, need_n)):
                if d not in pl:
                    continue
                r = _reconstruct(d, closes[d], pl[d], nd, bars, min_vol=min_vol, vol_pctl=vol_pctl)
                if not r:
                    continue
                _, rcz, rpz = _row(lbl, r.get("dte"), r.get("iv_atm"), r.get("call_iv"), r.get("put_iv"))
                if lbl != "Monatsverf.":
                    continue                        # bewertet wird der Backfill-Modus
                for nm, pv, rv in (("cZeta", pcz, rcz), ("pZeta", ppz, rpz)):
                    if pv is None or rv is None:
                        continue
                    zeta_devs.append(abs(rv - pv))
                    # Vorzeichenwechsel ist disqualifizierend: genau diese Achse
                    # traegt die Aussage des Vol-Regime-Radars.
                    if pv * rv < 0 and min(abs(pv), abs(rv)) > 0.5:
                        flips.append(f"{sym} {d} {nm}: {pv:+.2f} -> {rv:+.2f}")
        clear_cache(); gc.collect()

    print("-" * 67, flush=True)
    if not zeta_devs:
        print("[FAIL] Nichts vergleichbar — Backfill NICHT starten."); return 2
    mean, mx = sum(zeta_devs) / len(zeta_devs), max(zeta_devs)
    print(f"{len(zeta_devs)} Zeta-Vergleiche · mittlere Abweichung {mean:.2f} pts · max {mx:.2f} pts",
          flush=True)
    # Bewertet wird ZETA, nicht die rohe IV: eine kleine mittlere IV-Abweichung kann
    # ein gedrehtes Zeta verdecken (MU 2026-09-04: IV-Mittel 0,82 pts "gut", waehrend
    # call_zeta von +3,40 auf -0,66 kippte). Das Produkt nutzt Zeta, also pruefen wir Zeta.
    if flips:
        print(f"\n[FAIL] {len(flips)} VORZEICHENWECHSEL im Zeta:", flush=True)
        for f in flips:
            print(f"   {f}", flush=True)
        print("Eine Historie, die das Vorzeichen der Zielgroesse dreht, ist schlechter "
              "als keine. Backfill NICHT starten.", flush=True)
        return 3
    if mean <= 1.0:
        print("[OK] Zeta wird gut getroffen — Backfill kann laufen.")
        return 0
    print("[WARN] Zeta-Abweichung ueber 1 pt. Fuer Rangfolgen ggf. brauchbar, wenn der "
          "Versatz konstant ist — vor dem Massenlauf an mehreren Tagen pruefen.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", nargs="+", default=None)
    ap.add_argument("--all", action="store_true", help="ganzes Options-Universum")
    ap.add_argument("--years", type=float, default=2.0)
    ap.add_argument("--every-n-td", type=int, default=1,
                    help="jeder N-te Handelstag (1=taeglich; kostet kaum mehr als woechentlich)")
    ap.add_argument("--overwrite", action="store_true", help="vorhandene Punkte neu rechnen")
    ap.add_argument("--probe", action="store_true", help="nur Annahmen pruefen, nichts schreiben")
    ap.add_argument("--verify", action="store_true",
                    help="Rekonstruktion gegen Provider-IV halten, nichts schreiben")
    ap.add_argument("--probe-quotes", action="store_true",
                    help="Quotes-Endpoint pruefen + Trade-Schluss gegen Quote-Mitte messen")
    ap.add_argument("--min-vol", type=float, default=0.0,
                    help="Kontrakte mit weniger Tagesvolumen verwerfen (0=aus). Gegen alte "
                         "Trade-Prints, die mit dem Schlusskurs gepaart eine zu tiefe IV geben.")
    ap.add_argument("--vol-pctl", type=float, default=0.0,
                    help="Perzentil-Volumenfilter innerhalb der Kandidaten des Tages (0=aus, "
                         "0.5=untere Haelfte verwerfen). Normiert sich selbst auf den Ticker.")
    a = ap.parse_args()

    key = os.environ.get("MASSIVE_API_KEY", "")
    if not key:
        print("MASSIVE_API_KEY fehlt (Server-.env)."); return 1

    syms = a.symbols or (all_option_tickers() if a.all else _DEFAULT)
    if a.probe:
        return probe(syms[0], key)
    if a.probe_quotes:
        return probe_quotes(syms[0], key)
    if a.verify:
        return verify(syms, key, min_vol=a.min_vol, vol_pctl=a.vol_pctl)

    hp = _ROOT / "landing/data/options_skew_history.json"
    hist = {}
    if hp.exists():
        try:
            hist = json.loads(hp.read_text(encoding="utf-8"))
        except Exception:
            hist = {}

    total = 0
    for i, sym in enumerate(syms, 1):
        print(f"[{i}/{len(syms)}] {sym}", flush=True)
        try:
            total += run_ticker(sym, key, a.years, a.every_n_td, hist, a.overwrite,
                                min_vol=a.min_vol, vol_pctl=a.vol_pctl)
        except KeyboardInterrupt:
            print("\n[abgebrochen] Fortschritt ist gespeichert."); break
        except Exception as e:
            print(f"  {sym:6} FEHLER: {str(e)[:120]}", flush=True)
        # inkrementell nach JEDEM Ticker — ueberlebt Abbruch/OOM
        hp.write_text(json.dumps(hist, ensure_ascii=False, indent=2), encoding="utf-8")
        clear_cache(); gc.collect()

    print(f"\n[OK] +{total} Punkte · {sum(len(v) for v in hist.values())} gesamt "
          f"ueber {len(hist)} Ticker -> {hp}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
