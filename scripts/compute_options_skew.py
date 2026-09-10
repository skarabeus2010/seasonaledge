#!/usr/bin/env python3
"""
compute_options_skew.py — Options-Skew, IV-Term-Structure & Vol-Metriken, daily.

Ebenen:
  1) Markt-Gauges (gratis, kein Key): ^SKEW, ^VIX, ^VVIX via yahoo_downloader.
  2) Per-Ticker via Massive/Polygon Option-Chain-Snapshot (flatrate, EIN Fetch/Ticker):
     - 25Δ-Skew (Put-IV − Call-IV) bei 30d UND 90d  → Skew + Skew-Term-Structure
     - ATM-IV-Term-Structure über mehrere Laufzeiten (Contango/Backwardation)
     - VRP = ATM-IV(30d) − realisierte Vola (aus unseren Kursen)
     - 25Δ-Butterfly = (Put25+Call25)/2 − ATM  (Smile-Krümmung)
     - Put/Call-IV-Ratio

Schreibt landing/data/options_skew.json (+ akkumuliert options_skew_history.json).

Nutzung:  py -3.14 scripts/compute_options_skew.py [--tickers AAPL SPY QQQ]
"""
from __future__ import annotations
import argparse, gc, json, math, os, ssl, sys, time, urllib.error, urllib.request
from datetime import date, timedelta
from pathlib import Path

_THROTTLE = 0.05  # s zwischen Massive-Seiten (flatrate/unlimited; kleiner Puffer)

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from shared.env_loader import load_env          # noqa: E402
load_env()
from shared.yahoo_downloader import download_data, clear_cache  # noqa: E402
from shared.options_universe import all_option_tickers, categories_for, OPTIONS_CATEGORIES  # noqa: E402
from shared.exchange_holidays import is_trading_day                   # noqa: E402
from shared.black_scholes import (bs_delta, implied_vol, cm_interp as _cm_interp,  # noqa: E402
                                  CM_DAYS as _CM_DAYS, CM_DTE_MIN as _CM_DTE_MIN,
                                  CM_DTE_MAX as _CM_DTE_MAX, CM_SINGLE_TOL as _CM_SINGLE_TOL,
                                  DELTA_TOL as _DELTA_TOL, VOL_PCTL as _CM_VOL_PCTL)


def _last_session(d: date | None = None) -> str:
    """Letzter NYSE-Handelstag ≤ d. Das Options-Universum ist komplett US-gelistet.

    Der Cron läuft täglich um 23:00 UTC — auch samstags, sonntags und an
    Feiertagen. Mit date.today() gestempelt landeten dadurch Einträge auf Tagen
    ohne Handel in der History, die immer die Daten der letzten Session
    duplizieren. Das verfälscht jede Percentile-Berechnung (aufgeblähte
    Stichprobe mit Doppelwerten) und verstößt gegen die Grundregel, in
    Handelstagen statt Kalendertagen zu rechnen."""
    d = d or date.today()
    for _ in range(10):
        if is_trading_day(d, "NYSE"):
            return d.isoformat()
        d -= timedelta(days=1)
    return d.isoformat()


def _fix_session_dates(hist: dict) -> tuple[int, int]:
    """Alt-Einträge auf ihren tatsächlichen Handelstag umdatieren (selbstheilend).

    Ein am Samstag geschriebener Eintrag enthält die Chain von Freitag — der Wert
    stimmt, nur das Label war falsch. Deshalb umdatieren statt löschen. Danach
    dedupen: die Einträge von Sonntag und Feiertag fallen als Duplikate derselben
    Session weg. Bei Kollision gewinnt der Provider-Eintrag gegen eine
    BS-Rekonstruktion (echte IV schlägt invertierte)."""
    moved = dropped = 0
    for k, arr in hist.items():
        by_date: dict = {}
        for e in arr:
            try:
                s = _last_session(date.fromisoformat(e["date"]))
            except Exception:
                by_date.setdefault(e.get("date"), e)      # unparsbar: unangetastet behalten
                continue
            if s != e["date"]:
                e["date"] = s; moved += 1
            cur = by_date.get(s)
            if cur is None:
                by_date[s] = e
            else:
                dropped += 1
                # Normiert schlaegt nicht-normiert: ein laufzeitnormierter Punkt
                # (cm/cm_extrap) traegt die Rangfolge, ein Front-Monats-Punkt
                # nicht. Frueher gewann pauschal der Live-Eintrag — der konnte
                # damit einen brauchbaren Backfill-Punkt verdraengen und die
                # Stichprobe verkleinern.
                _norm = lambda x: x.get("cm_mode") in ("cm", "cm_extrap")
                if _norm(e) and not _norm(cur):
                    by_date[s] = e
                elif _norm(e) == _norm(cur) and cur.get("reconstructed") and not e.get("reconstructed"):
                    by_date[s] = e
        hist[k] = sorted(by_date.values(), key=lambda e: e.get("date") or "")
    return moved, dropped

_CTX = ssl.create_default_context(); _CTX.check_hostname = False; _CTX.verify_mode = ssl.CERT_NONE
# Massive.com (Polygon.io) Option-Chain-Snapshot — Flatrate, 1 Ticker = ganze Chain
# (Greeks/IV/OI je Kontrakt), paginiert. Ersetzt die per-Kontrakt-bepreiste marketdata-API.
_SNAP = "https://api.polygon.io/v3/snapshot/options/{sym}?expiration_date.lte={hi}&limit=250"
_MAXDTE = 190                       # nur Laufzeiten ≤190d (deckt Term-Structure + 25Δ ab)
_TERM_TARGETS = (7, 30, 60, 90, 120, 180)
_DEFAULT_TICKERS = all_option_tickers()   # thematisch gegliedertes US-Options-Universum


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


def _spot(sym: str, key: str):
    """EOD-Vortagsschluss als Spot-Proxy (Underlying im Snapshot ist oft leer)."""
    try:
        d = _get(f"https://api.polygon.io/v2/aggs/ticker/{sym}/prev", key)
        r = d.get("results") or []
        return round(float(r[0]["c"]), 2) if r else None
    except Exception:
        return None


def _chain(sym: str, key: str, spot=None) -> list:
    """Option-Chain (≤190d) als Kontraktliste (paginiert). Bei bekanntem Spot auf
    ±30 % Moneyness gefiltert — spart viele Seiten (25Δ+ATM liegen near-the-money)."""
    hi = (date.today() + timedelta(days=_MAXDTE)).isoformat()
    url = _SNAP.format(sym=sym, hi=hi)
    if spot:
        url += f"&strike_price.gte={round(spot * 0.7, 2)}&strike_price.lte={round(spot * 1.3, 2)}"
    out, pages = [], 0
    while url and pages < 45:
        d = _get(url, key)
        if d.get("status") not in ("OK", "DELAYED") and not d.get("results"):
            break
        out += d.get("results", [])
        url = d.get("next_url")
        pages += 1
    return out




def _pick(lst, target, tol=None):
    """Kontrakt mit |delta| am nächsten an target (lst = [(delta, iv, strike, oi), …]).

    tol: maximal erlaubte Abweichung vom Ziel. Ohne Toleranz liefert min() IMMER
    einen Treffer — bei dünner Kette also z.B. einen 0,40Δ-Kontrakt, der dann still
    als „25Δ" etikettiert wird und den Ticker-übergreifenden Vergleich verfälscht.
    Mit tol wird daraus None → der Ticker fällt für den Tag sauber raus."""
    if not lst:
        return None
    best = min(lst, key=lambda x: abs(abs(x[0]) - target))
    if tol is not None and abs(abs(best[0]) - target) > tol:
        return None
    return best


def _byexp(contracts: list) -> dict:
    """Kontrakte je Verfallstag: {exp: {dte, call:[(δ,iv,K,oi)], put:[…], spot}}."""
    today = date.today(); by = {}
    for c in contracts:
        g = c.get("greeks") or {}; iv = c.get("implied_volatility"); dl = g.get("delta")
        if iv is None or dl is None:
            continue
        det = c.get("details") or {}; ex = det.get("expiration_date"); typ = det.get("contract_type")
        if not ex or typ not in ("call", "put"):
            continue
        dte = (date.fromisoformat(ex) - today).days
        e = by.setdefault(ex, {"dte": dte, "call": [], "put": []})
        e[typ].append((float(dl), round(float(iv), 4), det.get("strike_price"), c.get("open_interest")))
    return by


def _index_series(sym: str, days: int = 504) -> dict:
    """Letzte ~days Handelstage: {dates:[...], vals:[...]} + letzter Wert."""
    try:
        df = download_data(sym, period="max")
        clear_cache()
        if df is None or len(df) == 0:
            return {}
        dts = [str(d)[:10] for d in (df["Date"] if "Date" in df.columns else df.index).tolist()][-days:]
        vals = [None if v != v else round(float(v), 2) for v in df["Close"].to_numpy()[-days:]]
        return {"dates": dts, "vals": vals, "last": vals[-1], "date": dts[-1]}
    except Exception as e:
        print(f"  [idx] {sym}: {e}")
        return {}


def _realized_vol(sym: str, n: int = 21):
    """Annualisierte realisierte Vola über n Handelstage (CBOE-Formel), Decimal.
    n=21 = 1 Monat (passt zur 30-Kalendertage-ATM-IV für den VRP).
    RV = sqrt( 252/(N-1) · Σ(R_t − R̄)² ), R_t = ln(P_t/P_{t-1}).

    Rückgabe: (rv, last_close). Der letzte Close dient als Spot-Fallback — der
    Massive-Endpoint liefert das Underlying nicht immer (ARM am 2026-09-08: Spot 0,00),
    und die Kursreihe ist hier ohnehin schon geladen."""
    try:
        df = download_data(sym, period="6mo")
    except Exception:
        clear_cache(); gc.collect(); return None, None
    if df is None or len(df) == 0:
        clear_cache(); gc.collect(); return None, None
    c = df["Close"].to_numpy(dtype=float)
    last = round(float(c[-1]), 2) if len(c) and c[-1] == c[-1] else None
    if len(df) < n + 5:
        clear_cache(); gc.collect(); return None, last
    r = [math.log(c[i] / c[i - 1]) for i in range(1, len(c)) if c[i - 1] > 0 and c[i] > 0]
    clear_cache(); gc.collect()
    if len(r) < n:
        return None, last
    seg = r[-n:]
    m = sum(seg) / n
    var = sum((x - m) ** 2 for x in seg) / (n - 1)        # Stichproben-Varianz (÷ N−1)
    return round(math.sqrt(var) * math.sqrt(252), 4), last  # × √252 annualisiert


def _is_monthly(iso: str) -> bool:
    """Standard-Monatsverfall = 3. Freitag (Tag 15-21 und ein Freitag)."""
    try:
        d = date.fromisoformat(iso)
    except Exception:
        return False
    return d.weekday() == 4 and 15 <= d.day <= 21


def _nearest_exp(by: dict, target_dte: int, prefer_monthly: bool = False):
    """Expiry am nächsten an target_dte.

    prefer_monthly: erst Monatsverfälle, dann Freitage, dann der Rest. Für den
    25Δ-Skew Pflicht — liquide Titel haben Mittwochs-Weeklies, die exakt auf
    30 Tage fallen können und dann gewinnen, obwohl fast niemand sie handelt.
    Deren IV ist dünn gestellt, und eine Zeitreihe, die mal Weeklies und mal
    Monatsverfälle enthält, vergleicht Ungleiches. Für die Term-Structure
    NICHT setzen — die will gerade das kurze Ende abbilden."""
    if not by:
        return None
    pool = by
    if prefer_monthly:
        pool = ([e for e in by if _is_monthly(e)]
                or [e for e in by if date.fromisoformat(e).weekday() == 4]
                or by)
    return min(pool, key=lambda e: abs(by[e]["dte"] - target_dte))


def _skew_at(by: dict, target_dte: int) -> dict | None:
    """25Δ-Skew (Put-IV − Call-IV) bei der Expiry nahe target_dte (Monatsverfall bevorzugt)."""
    ex = _nearest_exp(by, target_dte, prefer_monthly=True)
    if ex is None:
        return None
    e = by[ex]; cc = _pick(e["call"], 0.25, tol=_DELTA_TOL); pp = _pick(e["put"], 0.25, tol=_DELTA_TOL)
    if not cc or not pp:
        return None
    return {"exp": ex, "dte": e["dte"], "call_iv": cc[1], "call_strike": cc[2], "call_delta": round(cc[0], 3),
            "put_iv": pp[1], "put_strike": pp[2], "put_delta": round(pp[0], 3),
            "skew_pts": round((pp[1] - cc[1]) * 100, 2)}


def _atm_iv(e: dict):
    """ATM-IV = Mittel der 50Δ-Call/Put-IV einer Expiry."""
    cc = _pick(e["call"], 0.5); pp = _pick(e["put"], 0.5)
    return round((cc[1] + pp[1]) / 2, 4) if (cc and pp) else None


# ── Konstante 30-Tage-Laufzeit (identisch zu backfill_skew_massive.py) ────────
# Damit der Live-Tageswert auf DERSELBEN Skala wie der Backfill landet. Ohne das
# schwankt die Reihe zwischen ~21 und ~39 Tagen (nächste Monatsexpiry), und der
# Percentile misst die Position im Verfallszyklus statt den Skew.


def _cm_leg(e: dict):
    """25Δ-Call/Put-IV + ATM-IV einer Expiry (für die CM-Interpolation)."""
    cc = _pick(e["call"], 0.25, tol=_DELTA_TOL); pp = _pick(e["put"], 0.25, tol=_DELTA_TOL)
    if not cc or not pp:
        return None
    return {"dte": e["dte"], "call_iv": cc[1], "put_iv": pp[1], "iv_atm": _atm_iv(e)}


def _cm_legs(by: dict) -> list:
    """Ein bis zwei Verfälle wählen, die _CM_DAYS klammern (Monatsverfall bevorzugt).
    Ohne Bracket nach unten extrapolieren (zwei nächstlängere), sonst Einzelpunkt."""
    pool = ([e for e in by if _is_monthly(e)]
            or [e for e in by if date.fromisoformat(e).weekday() == 4]
            or list(by))
    below = sorted([e for e in pool if _CM_DTE_MIN <= by[e]["dte"] <= _CM_DAYS], key=lambda e: by[e]["dte"])
    above = sorted([e for e in pool if _CM_DAYS < by[e]["dte"] <= _CM_DTE_MAX], key=lambda e: by[e]["dte"])
    if below and above:
        return [below[-1], above[0]]      # echtes Bracket um 30d
    if len(above) >= 2:
        return [above[0], above[1]]       # kurz vor Roll: nach unten extrapolieren
    if len(below) >= 2:
        return [below[-2], below[-1]]     # selten: nach oben extrapolieren
    return above[:1] or below[-1:]        # nur ein Verfall → Einzelpunkt


# ── Ranking-Reihe: IV SELBST invertieren (Methodengleichheit mit dem Backfill) ─
# Die angezeigten Per-Ticker-Werte nutzen weiter die Provider-IV (genau, EOD).
# Fuer die HISTORIE zaehlt aber nicht Genauigkeit, sondern Vergleichbarkeit: die
# Reihe besteht zu >99 % aus BS-rekonstruierten Backfill-Punkten. Nimmt man fuer
# den Live-Punkt die Provider-IV, mischt man zwei Messmethoden — gemessen am
# 2026-09-09 ergab das einen Zeta-Versatz von 0,84-1,30 pts, bei NVDA so gross
# wie der gesamte Interquartilsabstand: der Live-Punkt landete im 99. Percentil,
# rein methodisch. Deshalb hier dieselbe Inversion, derselbe Volumenfilter.


def _own_cands(contracts: list, s30_ref: str | None = None) -> dict:
    """Snapshot-Kontrakte je Expiry als Rohpreise: {exp: {dte, cands:[…]}}.

    Bewusst OHNE Provider-IV/Greeks — nur Strike, Typ, Tagesschluss und Volumen.
    Deep-ITM/OTM-Kontrakte ohne Greeks fallen hier NICHT weg (anders als in
    _byexp), sie werden erst von der Bisektion verworfen, wenn kein Root existiert.

    s30_ref: Bezugsdatum fuer die Restlaufzeit. MUSS die Session sein, unter der
    die Zeile gestempelt wird — nicht date.today(). Ein Nachhol-Lauf nach einem
    ausgefallenen Cron (oder am Wochenende) hat sonst ein T, das bis zu drei Tage
    daneben liegt, und die daraus invertierte IV waere entsprechend verzerrt."""
    today = date.fromisoformat(s30_ref) if s30_ref else date.today()
    by = {}
    for c in contracts:
        det = c.get("details") or {}
        ex, typ, K = det.get("expiration_date"), det.get("contract_type"), det.get("strike_price")
        day = c.get("day") or {}
        px, vol = day.get("close"), day.get("volume") or 0
        if not ex or typ not in ("call", "put") or not K or not px:
            continue
        e = by.setdefault(ex, {"dte": (date.fromisoformat(ex) - today).days, "cands": []})
        e["cands"].append({"typ": typ, "K": float(K), "px": float(px), "vol": float(vol)})
    return by


def _leg_own(e: dict, spot: float, vol_pctl: float = _CM_VOL_PCTL):
    """25Δ-Call/Put- + ATM-IV EINER Expiry aus Preisen — Spiegel von
    backfill_skew_massive._leg_ivs (gleiche Filter, gleiche Toleranz)."""
    dte = e["dte"]; cands = e["cands"]
    if not spot or dte <= 0 or not cands:
        return None
    T = dte / 365.0
    cutoff = 0.0
    if vol_pctl > 0:
        vols = sorted(c["vol"] for c in cands)
        if vols:
            cutoff = vols[min(len(vols) - 1, int(len(vols) * vol_pctl))]
    best = {"call": {}, "put": {}}
    for c in cands:
        if cutoff and c["vol"] < cutoff:
            continue
        iv = implied_vol(c["px"], spot, c["K"], T, c["typ"])
        if iv is None or iv <= 0.01 or iv > 4.0:
            continue
        dl = bs_delta(spot, c["K"], T, iv, c["typ"])
        for tgt in (0.25, 0.50):
            dist = abs(abs(dl) - tgt)
            cur = best[c["typ"]].get(tgt)
            if cur is None or dist < cur[0]:
                best[c["typ"]][tgt] = (dist, iv)

    def _take(typ, tgt):
        v = best[typ].get(tgt)
        return v[1] if (v and v[0] <= _DELTA_TOL) else None

    call_iv, put_iv = _take("call", 0.25), _take("put", 0.25)
    atm_c, atm_p = _take("call", 0.50), _take("put", 0.50)
    if call_iv is None or put_iv is None:
        return None
    iv_atm = round((atm_c + atm_p) / 2, 4) if (atm_c and atm_p) else (atm_c or atm_p)
    return {"dte": dte, "call_iv": call_iv, "put_iv": put_iv, "iv_atm": iv_atm}


def _skew_cm(by: dict, leg_fn=None) -> dict | None:
    """Konstant-30-Tage 25Δ-Skew + ATM-IV — gleiche Methodik wie
    backfill_skew_massive.py, damit Live und Backfill eine Reihe bilden.

    leg_fn: Stuetzstellen-Quelle. Default = Provider-IV (_cm_leg); fuer die
    Ranking-Historie wird _leg_own uebergeben (eigene BS-Inversion)."""
    if not by:
        return None
    leg_fn = leg_fn or (lambda e: _cm_leg(by[e]))
    got = [g for g in (leg_fn(e) for e in _cm_legs(by)) if g]
    if not got:
        return None
    if len(got) >= 2:
        a, b = got[0], got[1]
        lo_d, hi_d = min(a["dte"], b["dte"]), max(a["dte"], b["dte"])
        if not (lo_d <= _CM_DAYS <= hi_d) and min(abs(lo_d - _CM_DAYS), abs(hi_d - _CM_DAYS)) > 15:
            return None
        call_iv = _cm_interp(a["call_iv"], a["dte"], b["call_iv"], b["dte"])
        put_iv = _cm_interp(a["put_iv"], a["dte"], b["put_iv"], b["dte"])
        iv_atm = (_cm_interp(a["iv_atm"], a["dte"], b["iv_atm"], b["dte"])
                  if (a["iv_atm"] and b["iv_atm"]) else None)
        mode, dte_out = ("cm" if lo_d <= _CM_DAYS <= hi_d else "cm_extrap"), _CM_DAYS
    else:
        a = got[0]
        if abs(a["dte"] - _CM_DAYS) > _CM_SINGLE_TOL:
            return None
        call_iv, put_iv, iv_atm = a["call_iv"], a["put_iv"], a["iv_atm"]
        mode, dte_out = "single", a["dte"]
    if call_iv is None or put_iv is None:
        return None
    out = {"cm_mode": mode, "cm_dte": dte_out,
           "cm_call_iv": round(call_iv, 4), "cm_put_iv": round(put_iv, 4),
           "cm_skew_pts": round((put_iv - call_iv) * 100, 2)}
    if iv_atm:
        out["cm_iv_atm"] = round(iv_atm, 4)
        out["cm_call_zeta_pts"] = round((call_iv - iv_atm) * 100, 2)
        out["cm_put_zeta_pts"] = round((put_iv - iv_atm) * 100, 2)
        out["cm_bfly_pts"] = round(((put_iv + call_iv) / 2 - iv_atm) * 100, 2)
    return out


def _enrich(sym: str, key: str) -> dict | None:
    """Voll-Metrik-Objekt aus EINEM Massive-Chain-Snapshot."""
    spot = _spot(sym, key)
    try:
        contracts = _chain(sym, key, spot)
    except Exception as e:
        print(f"  [massive] {sym}: {str(e)[:80]}")
        return None
    by = _byexp(contracts)
    s30 = _skew_at(by, 30)
    if not s30:
        print(f"  [massive] {sym}: kein 25Δ@30 (n={len(contracts)})")
        return None
    # Put/Call-Volumen + OI (für markt­weite Equity-P/C-Ratio; near-the-money aus ±30%-Chain)
    pv = cv = poi = coi = 0
    for c in contracts:
        typ = (c.get("details") or {}).get("contract_type")
        vol = (c.get("day") or {}).get("volume") or 0
        oi = c.get("open_interest") or 0
        if typ == "put":
            pv += vol; poi += oi
        elif typ == "call":
            cv += vol; coi += oi
    s90 = _skew_at(by, 90)
    # Term-Structure: ATM-IV je Ziel-Laufzeit (nächstliegende Expiry, dedupliziert)
    term, seen = [], set()
    for tgt in _TERM_TARGETS:
        ex = _nearest_exp(by, tgt)
        if ex is None or ex in seen:
            continue
        atm = _atm_iv(by[ex])
        if atm:
            term.append({"dte": by[ex]["dte"], "iv": atm}); seen.add(ex)
    term.sort(key=lambda t: t["dte"])
    # ATM MUSS aus derselben Expiry stammen wie die 25Δ-Picks. Sonst rechnet das
    # Zeta (25Δ-IV − ATM-IV) über zwei Laufzeiten und misst die Term-Struktur mit
    # statt den Skew. Vorher kam iv_atm aus der Term-Liste und traf s30 nur zufällig;
    # seit _skew_at Monatsverfälle bevorzugt, würden sie auseinanderlaufen.
    iv_atm = _atm_iv(by[s30["exp"]])
    if iv_atm is None and term:                       # Fallback: nichts ist besser als nichts
        iv_atm = min(term, key=lambda t: abs(t["dte"] - 30))["iv"]
    put_iv, call_iv = s30["put_iv"], s30["call_iv"]
    rv1m, last_close = _realized_vol(sym, 21)   # 1-Monat-Realized (CBOE), passend zur 30d-IV
    if not spot:                                    # Fallback 1: Underlying aus dem Snapshot
        for c in contracts:
            p = (c.get("underlying_asset") or {}).get("price")
            if p:
                spot = round(float(p), 2); break
    if not spot:                                    # Fallback 2: letzter Close aus eigener Kursreihe
        spot = last_close
        if spot:
            print(f"  [spot] {sym}: Massive ohne Underlying → letzter Close {spot}", flush=True)
    r = {
        "ticker": sym, "cats": categories_for(sym), "underlying": spot, "dte": s30["dte"],
        "put_vol": pv, "call_vol": cv, "put_oi": poi, "call_oi": coi,
        "call_25d": {"strike": s30["call_strike"], "iv": call_iv, "delta": s30["call_delta"]},
        "put_25d": {"strike": s30["put_strike"], "iv": put_iv, "delta": s30["put_delta"]},
        "skew_25d": round(put_iv - call_iv, 4), "skew_pts": s30["skew_pts"],
        # Zeta (SpotGamma-Def): OTM_IV − ATM_IV je Seite. call_zeta > 0 = Call-Skew (bullish),
        # put_zeta > 0 = Put-Skew (Absicherungsnachfrage). skew_pts = put_zeta − call_zeta.
        "call_zeta_pts": round((call_iv - iv_atm) * 100, 2) if iv_atm else None,
        "put_zeta_pts":  round((put_iv  - iv_atm) * 100, 2) if iv_atm else None,
        "iv_atm": iv_atm, "rv_1m": rv1m,
        "vrp_pts": round((iv_atm - rv1m) * 100, 2) if (iv_atm and rv1m) else None,
        "bfly_pts": round(((put_iv + call_iv) / 2 - iv_atm) * 100, 2) if iv_atm else None,
        "pc_ratio": round(put_iv / call_iv, 3) if call_iv else None,
        "skew_back_pts": s90["skew_pts"] if s90 else None,
        "skew_term_pts": round(s90["skew_pts"] - s30["skew_pts"], 2) if s90 else None,
        "term": term,
    }
    if term and iv_atm:
        r["contango"] = bool(term[0]["iv"] < iv_atm)
        r["term_slope_pts"] = round((term[-1]["iv"] - term[0]["iv"]) * 100, 2)
    else:
        r["contango"] = None; r["term_slope_pts"] = None
    # Expected Move (1σ) bis zum ~30d-Verfall: IV·√(T)  (Straddle-impliziert)
    emd = s30["dte"]
    if iv_atm and emd:
        r["em_pct"] = round(iv_atm * math.sqrt(emd / 365.0) * 100, 2)
        r["em_abs"] = round(spot * iv_atm * math.sqrt(emd / 365.0), 2) if spot else None
        r["em_dte"] = emd
    else:
        r["em_pct"] = r["em_abs"] = r["em_dte"] = None
    # NE-Skew (nächster Verfall — kurzfristig/spekulativ, wie SpotGamma "NE Skew")
    sne = _skew_at(by, 1)
    r["skew_ne_pts"] = sne["skew_pts"] if sne else None
    r["skew_ne_dte"] = sne["dte"] if sne else None
    # Skew-Kurve (IV je Delta): OTM-Puts (Downside) → ATM → OTM-Calls (Upside), für 30d + NE
    def _curve(ex_target):
        ex = _nearest_exp(by, ex_target)
        if ex is None:
            return None
        e = by[ex]; out = []
        for dl in (0.10, 0.25, 0.40):
            p = _pick(e["put"], dl); out.append(p[1] if p else None)
        out.append(_atm_iv(e))
        for dl in (0.40, 0.25, 0.10):
            c = _pick(e["call"], dl); out.append(c[1] if c else None)
        return out
    r["skew_curve"] = {
        "labels": ["10ΔP", "25ΔP", "40ΔP", "ATM", "40ΔC", "25ΔC", "10ΔC"],
        "iv30": _curve(30), "iv_ne": _curve(1),
        "dte30": s30["dte"], "dte_ne": (sne["dte"] if sne else None),
    }
    # Konstante 30-Tage-Werte für die Vorwärts-Historie — mit EIGENER BS-Inversion
    # aus den Snapshot-Preisen, also derselben Methode wie der Backfill. Nur so
    # bilden Live- und Backfill-Punkte eine Reihe, über die ein Percentile
    # ueberhaupt aussagekraeftig ist (Begruendung: shared/black_scholes.py).
    # Bewusst KEIN Rueckfall auf die Provider-IV: der wuerde die Methodenmischung
    # wieder einschleusen. Schlaegt die Inversion fehl, bekommt der Tag kein
    # cm_mode — das Frontend laesst ihn dann aus der Rangfolge heraus.
    # Die angezeigten Per-Ticker-Felder oben bleiben Provider-IV (genau, EOD).
    # Spot fuer die Inversion: der Schluss aus UNSERER Kursreihe — dieselbe Quelle,
    # die auch der Backfill nutzt (_closes). Ohne ihn wird NICHT normiert: Massives
    # /prev liefert je nach Laufzeitpunkt den Vortag, und ein damit falsch
    # skalierter Punkt bekaeme trotzdem ein cm_mode und landete in der Rangfolge.
    # Lieber kein Punkt als ein falsch skalierter.
    if last_close:
        # Restlaufzeit gegen die SESSION rechnen, unter der die Zeile gestempelt
        # wird — sonst liegt T bei einem Nachhol-Lauf um bis zu drei Tage daneben.
        by_own = _own_cands(contracts, s30_ref=_last_session())
        cm = _skew_cm(by_own, leg_fn=lambda e: _leg_own(by_own[e], last_close))
        # cm-Zeilen ohne iv_atm haetten kein Zeta — das Frontend wuerde auf die
        # (call_iv-put_iv)/2-Naeherung zurueckfallen, die put_zeta = -call_zeta
        # erzwingt und den Quadranten auf seine Antidiagonale kollabieren laesst.
        # Solche Tage gehoeren nicht in die Rangfolge.
        if cm and cm.get("cm_iv_atm"):
            r.update(cm)
    return r


def build(tickers: list[str], write: bool = True) -> dict:
    tok = os.environ.get("MASSIVE_API_KEY") or os.environ.get("POLYGON_API_KEY", "")
    skew_s = _index_series("^SKEW"); vix_s = _index_series("^VIX"); vvix_s = _index_series("^VVIX")
    indices = {}
    for name, s in [("SKEW", skew_s), ("VIX", vix_s), ("VVIX", vvix_s)]:
        if s:
            indices[name] = {"last": s["last"], "date": s["date"]}
            print(f"  idx {name:5} {s['last']} ({s['date']})")
    # CBOE Implied-Correlation-Indizes (gratis via Yahoo; oft nur letzter Wert) → KPI + Forward-History
    corr = {}
    for name, sym in [("COR1M", "^COR1M"), ("COR3M", "^COR3M"), ("COR30D", "^COR30D")]:
        s = _index_series(sym, days=504)
        if s and s.get("last") is not None:
            corr[name] = {"last": s["last"], "date": s["date"]}
            print(f"  cor {name:6} {s['last']} ({s['date']})")
    series = []
    if skew_s:
        vixmap = dict(zip(vix_s.get("dates", []), vix_s.get("vals", [])))
        for dt_, sk in zip(skew_s["dates"], skew_s["vals"]):
            series.append({"date": dt_, "skew": sk, "vix": vixmap.get(dt_)})

    per = []
    if not tok:
        print("  [massive] MASSIVE_API_KEY fehlt — überspringe Per-Ticker-Metriken.")
    else:
        for t in tickers:
            r = _enrich(t, tok)
            if r:
                per.append(r)
                ct = "contango" if r.get("contango") else ("backwardation" if r.get("contango") is False else "?")
                print(f"  {t:6} skew {r['skew_pts']:+.2f} · ATM {(r['iv_atm'] or 0)*100:.1f}% · "
                      f"VRP {r.get('vrp_pts')} · bfly {r.get('bfly_pts')} · P/C {r.get('pc_ratio')} · term {ct}", flush=True)

    # Marktweite Put/Call-Ratio (Equity = ohne Broad-Index-ETFs, Index = Broad-Index) — volumen- + OI-basiert
    def _pc(sel):
        pv = sum(t["put_vol"] for t in per if sel(t)); cv = sum(t["call_vol"] for t in per if sel(t))
        poi = sum(t["put_oi"] for t in per if sel(t)); coi = sum(t["call_oi"] for t in per if sel(t))
        return {"vol": round(pv / cv, 3) if cv else None, "oi": round(poi / coi, 3) if coi else None}
    _is_idx = lambda t: "Broad-Index" in (t.get("cats") or [])
    pc_ratio = {"equity": _pc(lambda t: not _is_idx(t)), "index": _pc(_is_idx), "date": date.today().isoformat()}
    if per:
        print(f"  P/C equity vol {pc_ratio['equity']['vol']} oi {pc_ratio['equity']['oi']} · index vol {pc_ratio['index']['vol']}", flush=True)

    out = {
        "generated": date.today().isoformat(),      # Laufzeitpunkt (Freshness-Checks)
        "session": _last_session(),                  # Handelstag, zu dem die Daten gehören
        "source": "CBOE ^SKEW/^VIX/^VVIX/^COR (Yahoo) + US-Option-Chain-Snapshot (25Δ-Skew, ATM-Term-Structure, VRP, Equity-P/C)",
        "indices": indices, "correlation": corr, "pc_ratio": pc_ratio, "series": series,
        "categories": list(OPTIONS_CATEGORIES.keys()), "tickers": per,
    }
    if write:
        p = _ROOT / "landing/data/options_skew.json"
        p.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n[OK] {len(per)} Ticker + {len(indices)} Indizes → {p}")
        # Skalare Metriken vorwärts in History akkumulieren
        hp = _ROOT / "landing/data/options_skew_history.json"
        hist = {}
        if hp.exists():
            try: hist = json.loads(hp.read_text(encoding="utf-8"))
            except Exception: hist = {}
        # Handelstag stempeln, NICHT den Laufzeitpunkt: der Cron läuft täglich um
        # 23:00 UTC, auch samstags/sonntags/feiertags — dann gehört die Chain zur
        # letzten Session. Der Dedup unten sorgt dafür, dass die Wiederholungen
        # am Wochenende keine Doppeleinträge erzeugen.
        today = out["session"]
        mv, dp = _fix_session_dates(hist)
        if mv or dp:
            print(f"[history] {mv} Einträge auf ihre Session umdatiert, {dp} Duplikate entfernt")
        for t in per:
            arr = hist.setdefault(t["ticker"], [])
            if not any(e.get("date") == today for e in arr):
                # Skew/IV auf konstante 30 Tage normiert speichern (gleiche Skala wie
                # der Backfill) → percentile-fähige Reihe. Felder tragen cm_mode; das
                # Frontend verwirft 'single'. Fällt die CM-Normierung aus (nur ein
                # Verfall zu weit weg), wird der reale Front-Monat gespeichert (kein
                # cm_mode) — für den Tag nicht normiert, aber kein Datenverlust.
                cm_ok = t.get("cm_mode") is not None
                arr.append({"date": today,
                            "cm_mode": t.get("cm_mode"),
                            "dte": t.get("cm_dte") if cm_ok else t.get("dte"),
                            "skew_pts": t.get("cm_skew_pts") if cm_ok else t["skew_pts"],
                            "put_iv": t.get("cm_put_iv") if cm_ok else t["put_25d"]["iv"],
                            "call_iv": t.get("cm_call_iv") if cm_ok else t["call_25d"]["iv"],
                            "iv_atm": t.get("cm_iv_atm") if cm_ok else t.get("iv_atm"),
                            # VRP/PC aus den CM-Werten ableiten, wenn vorhanden:
                            # sonst stuenden in EINER Zeile normierte IVs neben
                            # Front-Monats-Kennzahlen — intern inkonsistent.
                            "vrp_pts": (round((t["cm_iv_atm"] - t["rv_1m"]) * 100, 2)
                                        if (cm_ok and t.get("cm_iv_atm") and t.get("rv_1m"))
                                        else t.get("vrp_pts")),
                            "pc_ratio": (round(t["cm_put_iv"] / t["cm_call_iv"], 3)
                                         if (cm_ok and t.get("cm_call_iv")) else t.get("pc_ratio")),
                            "bfly_pts": t.get("cm_bfly_pts") if cm_ok else t.get("bfly_pts"),
                            "call_zeta_pts": t.get("cm_call_zeta_pts") if cm_ok else t.get("call_zeta_pts"),
                            "put_zeta_pts":  t.get("cm_put_zeta_pts") if cm_ok else t.get("put_zeta_pts")})
            hist[t["ticker"]] = arr[-750:]
        # CBOE-Correlation vorwärts akkumulieren (Yahoo liefert oft nur letzten Wert)
        if corr:
            carr = hist.setdefault("__CORR", [])
            if not any(e.get("date") == today for e in carr):
                carr.append({"date": today, "COR1M": (corr.get("COR1M") or {}).get("last"),
                             "COR3M": (corr.get("COR3M") or {}).get("last"),
                             "COR30D": (corr.get("COR30D") or {}).get("last")})
            hist["__CORR"] = carr[-750:]
        # Equity-P/C-Ratio vorwärts akkumulieren (keine freie Historie verfügbar)
        if per:
            parr = hist.setdefault("__PCR", [])
            if not any(e.get("date") == today for e in parr):
                parr.append({"date": today,
                             "eq_vol": pc_ratio["equity"]["vol"], "eq_oi": pc_ratio["equity"]["oi"],
                             "idx_vol": pc_ratio["index"]["vol"]})
            hist["__PCR"] = parr[-750:]
        hp.write_text(json.dumps(hist, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[history] {sum(len(v) for v in hist.values())} Punkte über {len(hist)} Ticker → {hp.name}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tickers", nargs="+", default=_DEFAULT_TICKERS)
    ap.add_argument("--no-write", action="store_true")
    a = ap.parse_args()
    build(a.tickers, not a.no_write)
    return 0


if __name__ == "__main__":
    sys.exit(main())
