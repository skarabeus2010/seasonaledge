"""
shared/polymarket_data.py — Polymarket Prediction-Market-Daten
===============================================================

Quellen:
  Gamma API  (https://gamma-api.polymarket.com)  — Events, Markets, Snapshot-Preise
  CLOB API   (https://clob.polymarket.com)       — prices-history (Historie)

Keine Authentifizierung noetig fuer Read-Zugriff. Defensive Rate-Limit-Policy:
0.3 s Sleep zwischen Requests, 15 s Timeout, Exponential Backoff nur bei 429/5xx.

Zur API-Struktur:
  - Gamma /events?tag_slug=fed        -> Event-Gruppen (z.B. "Fed rate cuts 2026")
  - Gamma /events/{id}                -> Event mit markets[]-Liste
  - Gamma /markets?condition_ids=...  -> Markt(e) mit bestBid/bestAsk/lastTradePrice
  - CLOB /prices-history?market=...   -> Preis-Historie pro YES-Token

Wichtige Feldnamen (Gamma):
  conditionId (camelCase, nicht condition_id)
  clobTokenIds (JSON-String mit [YES_TOKEN, NO_TOKEN])
  endDateIso, startDateIso
  liquidityNum, volumeNum, volume24hr
  bestBid, bestAsk, lastTradePrice (0.00-1.00)
"""
from __future__ import annotations

import json
import os
import time
import pathlib
from typing import Any

import requests

from shared.logger import app_logger, error_logger

# ── API-Basis-URLs ────────────────────────────────────────────────────────────

GAMMA_URL = "https://gamma-api.polymarket.com"
CLOB_URL = "https://clob.polymarket.com"

# ── Konfiguration (defensiv) ──────────────────────────────────────────────────

_TIMEOUT = 15
_SLEEP_BETWEEN = 0.3        # Sekunden zwischen Requests
_MAX_RETRIES = 3
_BACKOFF_BASE = 1.5

_USER_AGENT = "SeasonAlpha/1.0 (+https://seasonalpha.ai; contact heiko@seasonalpha.ai)"


# ── Optionaler API-Key (Rate-Limit-Erhoehung) ─────────────────────────────────

def _get_api_key() -> str:
    """
    Polymarket-CLOB-API-Key laden (optional).
    Aus Env-Var (gesetzt von shared/env_loader.py aus .env). Lesender Zugriff
    funktioniert ohne Key — Key erhoeht nur das Rate-Limit.
    """
    return os.environ.get("POLYMARKET_API_KEY", "")


# ── HTTP-Core ─────────────────────────────────────────────────────────────────

def _request(
    method: str,
    url: str,
    params: dict[str, Any] | None = None,
    json_body: dict[str, Any] | None = None,
) -> dict | list | None:
    """
    HTTP-Request mit Timeout, Retry bei 429/5xx, defensiver Rate-Limit-Policy.
    Gibt JSON zurueck oder None bei hartem Fehler.
    """
    headers = {
        "User-Agent": _USER_AGENT,
        "Accept": "application/json",
    }
    key = _get_api_key()
    if key:
        headers["Authorization"] = f"Bearer {key}"

    resp = None
    for attempt in range(_MAX_RETRIES):
        try:
            resp = requests.request(
                method, url,
                params=params, json=json_body,
                headers=headers, timeout=_TIMEOUT,
            )
            if resp.status_code == 429 or 500 <= resp.status_code < 600:
                wait = _BACKOFF_BASE ** (attempt + 1)
                app_logger.debug(
                    f"polymarket {method} {url} -> {resp.status_code}, retry in {wait:.1f}s"
                )
                time.sleep(wait)
                continue
            resp.raise_for_status()
            return resp.json()
        except requests.HTTPError as e:
            body = ""
            try:
                body = resp.text[:300] if resp is not None else ""
            except Exception:
                pass
            error_logger.error(
                f"polymarket HTTP-Fehler {method} {url} "
                f"status={getattr(resp, 'status_code', '?')} body={body} err={e}"
            )
            return None
        except requests.RequestException as e:
            wait = _BACKOFF_BASE ** (attempt + 1)
            app_logger.debug(f"polymarket Request-Fehler {e}, retry in {wait:.1f}s")
            time.sleep(wait)
        finally:
            time.sleep(_SLEEP_BETWEEN)

    error_logger.error(f"polymarket {method} {url} — alle {_MAX_RETRIES} Retries fehlgeschlagen")
    return None


# ── Gamma API: Events (Discovery) ─────────────────────────────────────────────

def fetch_events_by_tag(
    tag_slug: str,
    active: bool = True,
    closed: bool = False,
    limit: int = 100,
    offset: int = 0,
) -> list[dict]:
    """
    Liste aktiver Events mit Tag (z.B. 'fed','economy','crypto-prices').

    Events gruppieren verwandte Outcome-Markets. Ein Event "How many Fed rate
    cuts in 2026?" enthaelt z.B. 13 verschiedene Markets (0-12 cuts + none).
    """
    params: dict[str, Any] = {
        "tag_slug": tag_slug,
        "limit": min(limit, 500),
        "offset": offset,
        "active": "true" if active else "false",
        "closed": "true" if closed else "false",
    }
    data = _request("GET", f"{GAMMA_URL}/events", params=params)
    if not isinstance(data, list):
        return []
    return data


def fetch_event_detail(event_id: str | int) -> dict | None:
    """Vollstaendiges Event inkl. eingebetteter markets-Liste."""
    data = _request("GET", f"{GAMMA_URL}/events/{event_id}")
    if not isinstance(data, dict):
        return None
    return data


# ── Gamma API: Markets (Snapshot + Metadata) ──────────────────────────────────

def fetch_markets_by_condition_ids(condition_ids: list[str]) -> list[dict]:
    """
    Markt-Batch laden. Gamma unterstuetzt multiple condition_ids per Query-Param.
    Gibt leere Liste wenn keine IDs uebergeben.
    """
    if not condition_ids:
        return []
    # Gamma Query-Param: condition_ids wiederholen
    # Praktisch limitieren auf ~50 pro Request
    out: list[dict] = []
    for i in range(0, len(condition_ids), 50):
        batch = condition_ids[i:i + 50]
        # requests serialisiert list -> ?condition_ids=a&condition_ids=b
        data = _request(
            "GET", f"{GAMMA_URL}/markets",
            params={"condition_ids": batch},
        )
        if isinstance(data, list):
            out.extend(data)
    return out


def fetch_market_by_condition_id(condition_id: str) -> dict | None:
    """Ein einzelnes Market per conditionId holen."""
    lst = fetch_markets_by_condition_ids([condition_id])
    return lst[0] if lst else None


def normalize_market(raw: dict) -> dict:
    """
    Raw Gamma-Market auf einheitliches Schema mappen.

    Returns dict mit Feldern fuer polymarket_markets:
        condition_id, question, end_date, yes_token_id, no_token_id,
        liquidity_usd, volume_total_usd, meta
    """
    yes_token, no_token = _extract_token_ids(raw.get("clobTokenIds"))

    return {
        "condition_id": raw.get("conditionId") or "",
        "question": raw.get("question") or "",
        "end_date": raw.get("endDateIso") or raw.get("endDate"),
        "yes_token_id": yes_token,
        "no_token_id": no_token,
        "liquidity_usd": _safe_float(raw.get("liquidityNum") or raw.get("liquidity")),
        "volume_total_usd": _safe_float(raw.get("volumeNum") or raw.get("volume")),
        "meta": {
            "gamma_id": raw.get("id"),
            "slug_source": raw.get("slug"),
            "closed": raw.get("closed"),
            "accepting_orders": raw.get("acceptingOrders"),
            "outcomes": raw.get("outcomes"),
            "neg_risk": raw.get("negRisk"),
        },
    }


def _extract_token_ids(clob_token_ids) -> tuple[str, str]:
    """clobTokenIds kommt als JSON-String oder Liste. Gibt (yes, no) zurueck."""
    if not clob_token_ids:
        return "", ""
    tokens = clob_token_ids
    if isinstance(tokens, str):
        try:
            tokens = json.loads(tokens)
        except (ValueError, TypeError):
            return "", ""
    if not isinstance(tokens, list) or len(tokens) < 2:
        return "", ""
    # Konvention bei Polymarket: [YES, NO]
    return (str(tokens[0]) or "", str(tokens[1]) or "")


# ── Snapshot-Preis (aus Gamma — KEIN CLOB-Roundtrip noetig) ───────────────────

def market_to_price_snapshot(market: dict) -> dict | None:
    """
    Baut einen Preis-Snapshot direkt aus dem Gamma-Market-Response.
    Nutzt bestBid/bestAsk fuer Mid, fallback auf lastTradePrice.

    Returns dict oder None:
        yes_price  (0.00-1.00)
        spread     (best_ask - best_bid, None wenn nur lastTradePrice)
        volume_24h (aus volume24hr)
    """
    if not isinstance(market, dict):
        return None

    best_bid = _safe_float(market.get("bestBid"))
    best_ask = _safe_float(market.get("bestAsk"))
    last = _safe_float(market.get("lastTradePrice"))

    spread = None
    if best_bid is not None and best_ask is not None:
        mid = (best_bid + best_ask) / 2
        spread = best_ask - best_bid
    elif best_bid is not None:
        mid = best_bid
    elif best_ask is not None:
        mid = best_ask
    elif last is not None:
        mid = last
    else:
        return None

    return {
        "yes_price": round(mid, 4),
        "spread": round(spread, 4) if spread is not None else None,
        "volume_24h": _safe_float(market.get("volume24hr")),
    }


def fetch_current_price(condition_id: str) -> dict | None:
    """
    Convenience-Wrapper: Markt per conditionId von Gamma holen und
    Snapshot extrahieren. Ein Request, kein CLOB-Roundtrip.
    """
    m = fetch_market_by_condition_id(condition_id)
    if not m:
        return None
    return market_to_price_snapshot(m)


# ── CLOB API: Historische Preise ──────────────────────────────────────────────

def fetch_price_history(
    token_id: str,
    interval: str = "1d",
    fidelity: int = 1440,
) -> list[dict]:
    """
    Historische Mid-Preise fuer ein Token.

    Args:
        token_id:  YES-Token-ID (aus clobTokenIds[0])
        interval:  '1h','6h','1d','1w','max'
        fidelity:  Minuten-Aufloesung (60 = stuendlich, 1440 = taeglich)

    Returns:
        Liste von {'t': unix_seconds, 'p': float} Dicts — sortiert aufsteigend.
    """
    if not token_id:
        return []

    data = _request(
        "GET", f"{CLOB_URL}/prices-history",
        params={"market": token_id, "interval": interval, "fidelity": fidelity},
    )
    if not isinstance(data, dict):
        return []

    history = data.get("history") or []
    out = []
    for pt in history:
        ts = pt.get("t") or pt.get("timestamp")
        p = _safe_float(pt.get("p") or pt.get("price"))
        if ts is None or p is None:
            continue
        out.append({"t": int(ts), "p": p})
    out.sort(key=lambda x: x["t"])
    return out


# ── Hilfsfunktionen ───────────────────────────────────────────────────────────

def _safe_float(x) -> float | None:
    """Liberale Konvertierung zu float, None bei Fehler/leer."""
    if x is None or x == "":
        return None
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


# ── YAML-Loader (kuratiertes Market-Set) ──────────────────────────────────────

_YAML_PATH = pathlib.Path(__file__).resolve().parent / "polymarket_markets.yaml"


def load_markets_yaml(path: pathlib.Path | str | None = None) -> dict:
    """
    Laedt shared/polymarket_markets.yaml (kuratiertes Set).

    Returns dict mit Schluesseln 'version', 'updated', 'markets' (Liste).
    """
    try:
        import yaml  # type: ignore[import-not-found]
    except ImportError as e:
        raise ImportError(
            "PyYAML nicht installiert. Installiere mit: pip install pyyaml"
        ) from e

    p = pathlib.Path(path) if path else _YAML_PATH
    if not p.exists():
        raise FileNotFoundError(f"polymarket_markets.yaml fehlt: {p}")

    with open(p, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    markets = data.get("markets") or []
    if not isinstance(markets, list):
        raise ValueError("polymarket_markets.yaml 'markets' muss eine Liste sein")

    return data


def save_markets_yaml(data: dict, path: pathlib.Path | str | None = None) -> None:
    """
    Schreibt das aktualisierte YAML zurueck (bewahrt Reihenfolge der Keys).
    Wird vom Discovery-Script verwendet um condition_id's einzutragen.
    """
    try:
        import yaml  # type: ignore[import-not-found]
    except ImportError as e:
        raise ImportError("PyYAML nicht installiert.") from e

    p = pathlib.Path(path) if path else _YAML_PATH
    with open(p, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)


# ── Self-Test ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    _proj = pathlib.Path(__file__).resolve().parent.parent
    if str(_proj) not in sys.path:
        sys.path.insert(0, str(_proj))

    print("polymarket_data self-test")
    print("-" * 60)

    print("\n[1] fetch_events_by_tag('fed', limit=3)")
    events = fetch_events_by_tag(tag_slug="fed", limit=3)
    print(f"  -> {len(events)} Events")
    for e in events[:3]:
        print(f"     {e.get('title','')[:80]}  id={e.get('id')}")

    if events:
        eid = events[0]["id"]
        print(f"\n[2] fetch_event_detail({eid}) -> markets[]")
        detail = fetch_event_detail(eid)
        if detail and detail.get("markets"):
            m0 = detail["markets"][0]
            print(f"  erstes Market: {m0.get('question','')[:80]}")
            cid = m0.get("conditionId", "")
            print(f"  conditionId:   {cid[:30]}...")
            print(f"  bestBid/Ask:   {m0.get('bestBid')} / {m0.get('bestAsk')}")
            print(f"  lastTrade:     {m0.get('lastTradePrice')}")

            print(f"\n[3] normalize_market(...)")
            norm = normalize_market(m0)
            print(f"  yes_token: {norm['yes_token_id'][:20]}...  no_token: {norm['no_token_id'][:20]}...")
            print(f"  liquidity: ${norm['liquidity_usd']}")

            print(f"\n[4] market_to_price_snapshot(...)")
            snap = market_to_price_snapshot(m0)
            print(f"  -> {snap}")

            print(f"\n[5] fetch_price_history(...) interval=1d")
            if norm["yes_token_id"]:
                hist = fetch_price_history(norm["yes_token_id"], interval="1d")
                print(f"  -> {len(hist)} Datenpunkte")
                if hist:
                    print(f"     erster:  {hist[0]}")
                    print(f"     letzter: {hist[-1]}")

    sys.exit(0)
