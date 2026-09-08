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
                out[ds] = float(b["c"])
        except Exception:
            continue
    return out


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
def _is_monthly(iso: str) -> bool:
    """Standard-Monatsverfall = 3. Freitag des Monats (Tag 15-21 und ein Freitag)."""
    d = date.fromisoformat(iso)
    return d.weekday() == 4 and 15 <= d.day <= 21


def _plan(closes: dict, contracts: list, targets: list) -> tuple[dict, dict]:
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
        pool = ([e for e in cand if _is_monthly(e)]
                or [e for e in cand if date.fromisoformat(e).weekday() == 4]
                or cand)
        exp = min(pool, key=lambda e: abs((date.fromisoformat(e) - dd).days - 30))
        dte = (date.fromisoformat(exp) - dd).days
        if not (_DTE_MIN <= dte <= _DTE_MAX):
            continue
        lo, hi = spot * (1 - _BAND), spot * (1 + _BAND)
        picked = []
        for typ in ("call", "put"):
            ss = sorted((c for c in by_exp[exp]
                         if c["contract_type"] == typ and lo <= c["strike_price"] <= hi),
                        key=lambda c: c["strike_price"])
            if len(ss) > _MAX_STRIKES:                 # gleichmäßig ausdünnen
                step = len(ss) / _MAX_STRIKES
                ss = [ss[int(i * step)] for i in range(_MAX_STRIKES)]
            picked += ss
        if len(picked) < 6:
            continue
        plan[d] = (exp, dte, [c["ticker"] for c in picked])
        for c in picked:
            need[c["ticker"]] = c
    return plan, need


def _reconstruct(d: str, spot: float, dte: int, occs: list, need: dict, bars: dict) -> dict | None:
    """IV je Kontrakt invertieren, 25Δ + 50Δ picken, Metriken rechnen."""
    T = dte / 365.0
    best: dict = {"call": {}, "put": {}}
    for occ in occs:
        px = bars.get(occ, {}).get(d)
        if not px:
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
    r = {"date": d, "dte": dte,
         "put_iv": round(put_iv, 4), "call_iv": round(call_iv, 4),
         "skew_pts": round((put_iv - call_iv) * 100, 2),
         "reconstructed": True, "src": "massive"}
    if iv_atm:
        r["iv_atm"] = round(iv_atm, 4)
        r["call_zeta_pts"] = round((call_iv - iv_atm) * 100, 2)
        r["put_zeta_pts"] = round((put_iv - iv_atm) * 100, 2)
        r["bfly_pts"] = round(((put_iv + call_iv) / 2 - iv_atm) * 100, 2)
    return r


def run_ticker(sym: str, key: str, years: float, every: int, hist: dict, overwrite: bool) -> int:
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
    for d, (exp, dte, occs) in sorted(plan.items()):
        r = _reconstruct(d, closes[d], dte, occs, need, bars)
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
    exp, dte, occs = plan[d]
    _wd = date.fromisoformat(exp).strftime("%a")
    _kind = "Monatsverfall" if _is_monthly(exp) else (
        "Freitags-Weekly" if date.fromisoformat(exp).weekday() == 4 else "NICHT-Freitag (illiquide!)")
    print(f"[3] Expiry {exp} ({_wd}, {_kind}) · DTE {dte} · {len(occs)} Kontrakte geplant", flush=True)

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
        print(f"    z.B. {ds[0]}={wide[ds[0]]}  …  {ds[-1]}={wide[ds[-1]]}", flush=True)

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

    r = _reconstruct(d, spot, dte, occs, need, bars)
    if not r:
        print("[FAIL] Rekonstruktion ergab nichts (25D nicht klammerbar)"); return 5
    print(f"[5] Rekonstruktion OK:", flush=True)
    for k in ("date", "dte", "call_iv", "put_iv", "iv_atm",
              "call_zeta_pts", "put_zeta_pts", "skew_pts", "bfly_pts"):
        print(f"      {k:<15} {r.get(k)}", flush=True)
    print("\n[OK] Alle Annahmen bestaetigt — der Backfill kann laufen.", flush=True)
    return 0


def verify(syms: list, key: str) -> int:
    """Rekonstruktion gegen die Provider-IV der Vorwaerts-Akkumulation halten.

    Die History enthaelt Eintraege OHNE 'reconstructed' — die stammen aus dem
    taeglichen Snapshot und tragen die IV des Providers. Genau diese Tage noch
    einmal aus Preisen zu rekonstruieren zeigt, wie gut die BS-Inversion trifft.
    Ohne diesen Abgleich waere der Backfill nur intern konsistent, nicht richtig."""
    hp = _ROOT / "landing/data/options_skew_history.json"
    if not hp.exists():
        print("[FAIL] keine History-Datei."); return 1
    hist = json.loads(hp.read_text(encoding="utf-8"))

    print(f"{'Ticker':<7}{'Datum':<12}{'Feld':<9}{'Provider':>10}{'Rekon':>10}{'Delta pts':>11}", flush=True)
    print("-" * 59, flush=True)
    devs: list[float] = []
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
        plan, need = _plan(closes, contracts, dates)
        bars = {occ: _bars(occ, key, dates[0], dates[-1]) for occ in need}

        for d, e in ref:
            if d not in plan:
                continue
            exp, dte, occs = plan[d]
            r = _reconstruct(d, closes[d], dte, occs, need, bars)
            if not r:
                continue
            for fld in ("iv_atm", "call_iv", "put_iv"):
                if e.get(fld) and r.get(fld):
                    dev = (r[fld] - e[fld]) * 100
                    devs.append(abs(dev))
                    print(f"{sym:<7}{d:<12}{fld:<9}{e[fld]*100:>9.2f}%{r[fld]*100:>9.2f}%{dev:>+11.2f}",
                          flush=True)
        clear_cache(); gc.collect()

    if not devs:
        print("\n[FAIL] Nichts vergleichbar — Backfill NICHT starten."); return 2
    mean, mx = sum(devs) / len(devs), max(devs)
    print("-" * 59, flush=True)
    print(f"{len(devs)} Vergleiche · mittlere Abweichung {mean:.2f} pts · max {mx:.2f} pts", flush=True)
    # Der alte marketdata-Backfill lag unter 0,4 pts. Trade-Preise statt Mid-Quotes
    # rechtfertigen etwas mehr, aber jenseits von ~2 pts ist die Reihe wertlos.
    if mean <= 1.0:
        print("[OK] Rekonstruktion trifft die Provider-IV gut — Backfill kann laufen.")
        return 0
    if mean <= 2.0:
        print("[WARN] Spuerbare Abweichung. Brauchbar fuer Percentile (Rangfolge), "
              "aber nicht fuer absolute IV-Aussagen.")
        return 0
    print("[FAIL] Zu grosse Abweichung — Ursache klaeren, bevor 2 Jahre Historie "
          "damit gefuellt werden.")
    return 3


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
    a = ap.parse_args()

    key = os.environ.get("MASSIVE_API_KEY", "")
    if not key:
        print("MASSIVE_API_KEY fehlt (Server-.env)."); return 1

    syms = a.symbols or (all_option_tickers() if a.all else _DEFAULT)
    if a.probe:
        return probe(syms[0], key)
    if a.verify:
        return verify(syms, key)

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
            total += run_ticker(sym, key, a.years, a.every_n_td, hist, a.overwrite)
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
