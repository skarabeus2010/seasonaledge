"""
scripts/compare_flashalpha_gex.py — SeasonAlpha-GEX vs. FlashAlpha-GEX gegenprüfen
==================================================================================
Ruft `get_gex` beim FlashAlpha-MCP (JSON-RPC über Streamable HTTP) ab und stellt die
Kennzahlen unserer eigenen Berechnung (`scripts/compute_gamma_exposure.py`) gegenüber.

Sinn: Unsere Zahlen beruhen auf der **naiven Dealer-Konvention** (long Calls / short Puts)
und Yahoo-EOD-OI. FlashAlpha nutzt ein eigenes Modell + eigene Chain. Abweichungen sind
ERWARTET — interessant ist, ob die *Struktur* übereinstimmt: Vorzeichen des Netto-GEX
(Regime), Lage des Zero-Gamma-Flips und die Call-/Put-Wall-Strikes.

⚠️ FlashAlpha Free-Plan = 5 Calls/Tag, Reset 00:00 UTC. Dieses Skript verbraucht 1 Call
   (bzw. 2 mit --account). Erst nach dem Reset laufen lassen.

Aufruf:
  PYTHONUTF8=1 py -3.14 scripts/compare_flashalpha_gex.py --ticker SPY
  PYTHONUTF8=1 py -3.14 scripts/compare_flashalpha_gex.py --ticker SPY --account
  PYTHONUTF8=1 py -3.14 scripts/compare_flashalpha_gex.py --dry-run   # nur unsere Seite, 0 Quota

Key: .env → FLASHALPHA_API_KEY  (oder --api-key)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.compute_gamma_exposure import analyze  # noqa: E402

_MCP_URL = "https://lab.flashalpha.com/mcp"
_OUT_DIR = _ROOT / "landing" / "data" / "gex_history"


# ─────────────────────────────────────────────────────── .env / Key
def _load_key(cli_key: str | None) -> str | None:
    if cli_key:
        return cli_key
    if os.environ.get("FLASHALPHA_API_KEY"):
        return os.environ["FLASHALPHA_API_KEY"]
    envf = _ROOT / ".env"
    if envf.exists():
        for line in envf.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("FLASHALPHA_API_KEY="):
                return line.split("=", 1)[1].strip()
    return None


# ─────────────────────────────────────────────────────── MCP-Client (Streamable HTTP)
def mcp_call(tool: str, arguments: dict, timeout: int = 60) -> dict:
    """Ruft ein FlashAlpha-MCP-Tool auf. Antwort kommt als SSE (text/event-stream)."""
    payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
               "params": {"name": tool, "arguments": arguments}}
    r = requests.post(_MCP_URL, json=payload, timeout=timeout, headers={
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    })
    r.raise_for_status()
    envelope = None
    for line in r.text.splitlines():
        line = line.strip()
        if line.startswith("data:"):
            line = line[5:].strip()
        if line.startswith("{"):
            envelope = json.loads(line)
    if envelope is None:
        raise RuntimeError(f"Keine JSON-RPC-Antwort erhalten: {r.text[:300]}")
    if "error" in envelope:
        raise RuntimeError(f"MCP-Fehler: {envelope['error']}")

    res = envelope.get("result", {})
    # structuredContent bevorzugen, sonst den (meist JSON-)Text der content-Blöcke parsen
    if isinstance(res.get("structuredContent"), dict):
        return {"parsed": res["structuredContent"], "raw": res}
    texts = [c.get("text", "") for c in res.get("content", []) if c.get("type") == "text"]
    for t in reversed(texts):
        t = t.strip()
        if t.startswith(("{", "[")):
            try:
                return {"parsed": json.loads(t), "raw": res}
            except json.JSONDecodeError:
                continue
    return {"parsed": {"_text": "\n".join(texts)}, "raw": res}


# ─────────────────────────────────────────────────────── Feld-Extraktion (Schema unbekannt)
def _walk(obj, depth=0):
    """Alle (key, value)-Paare rekursiv — FlashAlphas Response-Schema ist nicht dokumentiert."""
    if depth > 6:
        return
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k, v
            yield from _walk(v, depth + 1)
    elif isinstance(obj, list):
        for v in obj[:400]:
            yield from _walk(v, depth + 1)


def pick(obj, *aliases):
    """Erster skalarer Treffer für einen der Alias-Keys (case-/underscore-insensitiv)."""
    want = {a.lower().replace("_", "") for a in aliases}
    for k, v in _walk(obj):
        if k.lower().replace("_", "") in want and isinstance(v, (int, float, str)):
            return v
    return None


# ─────────────────────────────────────────────────────── Vergleich
def _from_snapshot(ticker: str, when: str) -> dict | None:
    """Kennzahlen aus dem Nightly-Archiv (landing/data/gex_history/<datum>.json).

    Der Cron laeuft 22:15 UTC — also im Zeitfenster, in dem Yahoo vollstaendiges
    Open Interest liefert. Damit ist der Snapshot die verlaesslichere Basis als eine
    Ad-hoc-Berechnung zur Tageszeit, und zugleich exakt das, was die Website zeigt.
    """
    name = f"{when}.json"
    local = _OUT_DIR / name
    payload = None
    if local.exists():
        payload = json.loads(local.read_text(encoding="utf-8"))
    else:
        r = requests.get(f"https://seasonalpha.ai/landing/data/gex_history/{name}", timeout=30)
        if r.status_code == 200:
            payload = r.json()
    if not payload:
        return None
    for o in payload.get("tickers", []):
        if o.get("ticker") == ticker:
            return {**o, "_as_of": payload.get("date", when)}
    return None


def _term_from_profile(ticker: str, when: str, exp: str) -> dict | None:
    """Unser Netto-Gamma fuer EINEN Verfall aus dem by_term-Profil des Nightly-Laufs.

    Noetig, weil FlashAlphas Free-Plan nur Einzelverfaelle erlaubt — ein Vergleich
    gegen unsere Full-Chain-Summe waere sonst ein Groessenordnungs-Vergleich von
    Aepfeln mit Obstkoerben.
    """
    name = f"gex_profile_{ticker.replace('^', '')}.json"
    local = _ROOT / "landing" / "data" / name
    payload = None
    if local.exists():
        cand = json.loads(local.read_text(encoding="utf-8"))
        if cand.get("date") == when:
            payload = cand
    if payload is None:
        r = requests.get(f"https://seasonalpha.ai/landing/data/{name}", timeout=30)
        if r.status_code == 200 and r.json().get("date") == when:
            payload = r.json()
    if not payload:
        return None
    for row in (payload.get("profile") or {}).get("by_term", []):
        if row.get("exp") == exp:
            return row
    return None


def _fmt(v, unit=""):
    if v is None:
        return "n/a"
    if isinstance(v, float):
        return f"{v:,.2f}{unit}"
    return f"{v}{unit}"


def _delta(ours, theirs):
    """Relative Abweichung in % (nur wenn beide numerisch und ours != 0)."""
    try:
        o, t = float(ours), float(theirs)
    except (TypeError, ValueError):
        return "—"
    if o == 0:
        return "—"
    return f"{(t - o) / abs(o) * 100:+.1f} %"


def _fa_walls(fa: dict):
    """Call-/Put-Wall aus FlashAlphas strikes-Array nach UNSERER Definition ableiten.

    FlashAlpha liefert die Walls nicht als Feld, wohl aber net_gex je Strike — damit
    sind sie nach derselben Regel bestimmbar wie bei uns (_walls in
    compute_gamma_exposure.py): staerkstes positives Netto-Gamma bei Strike >= Spot,
    staerkstes negatives bei Strike <= Spot. Gleiche Regel = fairer Vergleich.
    """
    strikes = fa.get("strikes") or []
    spot = fa.get("underlying_price")
    if not strikes or spot is None:
        return None, None
    above = [r for r in strikes if r.get("strike", 0) >= spot]
    below = [r for r in strikes if r.get("strike", 0) <= spot]
    cw = max(above, key=lambda r: r.get("net_gex", 0)) if above else None
    pw = min(below, key=lambda r: r.get("net_gex", 0)) if below else None
    return (cw or {}).get("strike"), (pw or {}).get("strike")


def compare(ticker: str, ours: dict, fa: dict) -> list[tuple]:
    fa_spot = pick(fa, "spot", "spot_price", "underlying_price", "price", "last")
    fa_flip = pick(fa, "gamma_flip", "zero_gamma", "flip", "gamma_flip_level", "zero_gamma_level")
    fa_gex = pick(fa, "total_gex", "net_gex", "gex_total", "total_gamma", "net_gamma", "gex")
    fa_cw, fa_pw = _fa_walls(fa)
    # FlashAlpha rechnet net_gex in ROH-Dollar, wir in Mio $ — sonst steht da ein Delta
    # von 98 Millionen Prozent und der eigentlich sehr gute Treffer bleibt unsichtbar.
    if isinstance(fa_gex, (int, float)) and abs(fa_gex) > 1e5:
        fa_gex = fa_gex / 1e6

    rows = [("Spot", ours.get("spot"), fa_spot)]
    if ours.get("_term_gamma_mn") is not None:
        # Einzelverfall-Modus: unser by_term-Gamma gegen FlashAlphas Verfalls-GEX
        rows.append(("Gamma Verfall (Mio $)", ours["_term_gamma_mn"], fa_gex))
    else:
        rows.append(("Netto-GEX (roh)", ours.get("net_gex_usd_bn"), fa_gex))
    rows += [
        ("Zero-Gamma / Flip",    ours.get("zero_gamma"),      fa_flip),
        ("Call-Wall",            ours.get("call_wall"),       fa_cw),
        ("Put-Wall",             ours.get("put_wall"),        fa_pw),
    ]
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticker", default="SPY")
    ap.add_argument("--max-days", type=int, default=90, help="Expiry-Fenster für UNSERE Rechnung")
    ap.add_argument("--min-oi", type=int, default=None, help="min. Open Interest an FlashAlpha")
    ap.add_argument("--api-key", default=None)
    ap.add_argument("--account", action="store_true", help="zusätzlich get_account (quota-frei)")
    ap.add_argument("--min-contracts", type=int, default=500,
                    help="Plausibilitätsschwelle für unsere Yahoo-Chain (Default 500)")
    ap.add_argument("--force", action="store_true", help="auch bei dünner Chain vergleichen")
    ap.add_argument("--snapshot", metavar="YYYY-MM-DD",
                    help="unsere Seite aus dem Nightly-Archiv statt frisch rechnen "
                         "(umgeht Yahoos Open-Interest-Tagesfenster)")
    ap.add_argument("--expiration", metavar="YYYY-MM-DD",
                    help="nur EINEN Verfall vergleichen (FlashAlpha-Free erlaubt keine Full-Chain); "
                         "unsere Seite kommt dann aus dem by_term-Profil")
    ap.add_argument("--dry-run", action="store_true", help="nur unsere Berechnung, kein FlashAlpha-Call")
    a = ap.parse_args()
    tk = a.ticker.upper()

    # ── 1) unsere Seite: entweder frisch rechnen oder den Nightly-Snapshot nehmen
    if a.snapshot:
        print(f"[1/2] SeasonAlpha-GEX für {tk} aus Nightly-Snapshot {a.snapshot} …", flush=True)
        ours = _from_snapshot(tk, a.snapshot)
        if not ours:
            print(f"  [FEHLER] {tk} nicht im Snapshot {a.snapshot}")
            return 1
        print(f"      Spot {ours['spot']} · net-GEX {ours['net_gex_usd_bn']:+.3f} Mrd $/1 % "
              f"· {ours['regime']} · Stand {ours['_as_of']} (EOD)")
        if a.expiration:
            term = _term_from_profile(tk, a.snapshot, a.expiration)
            if not term:
                print(f"  [FEHLER] kein by_term-Eintrag für {a.expiration} im Profil {a.snapshot}")
                return 1
            ours["_term_gamma_mn"] = term["gamma_usd_mn"]
            ours["_term_vanna_mn"] = term.get("vanna_usd_mn")
            print(f"      davon Verfall {a.expiration}: Gamma {term['gamma_usd_mn']:+.1f} Mio $/1 % "
                  f"· Vanna {term.get('vanna_usd_mn'):+.1f} Mio $/Vol-Pkt")
    else:
        print(f"[1/2] SeasonAlpha-GEX für {tk} (Yahoo-Chain, max {a.max_days} Tage) …", flush=True)
        ours = analyze(tk, a.max_days)
        if not ours:
            print(f"  [FEHLER] keine eigene Berechnung möglich für {tk}")
            return 1
        print(f"      Spot {ours['spot']} · net-GEX {ours['net_gex_usd_bn']:+.3f} Mrd $/1 % "
              f"· {ours['regime']} · {ours['n_contracts']} Kontrakte / {ours['n_expiries']} Expiries")

        # Yahoo befuellt das Open Interest erst im Lauf des Tages — im Vormittagsfenster kommt
        # die Chain mit OI=0 zurueck, unser Filter wirft alles raus und analyze() meldet
        # trotzdem Erfolg. Lieber abbrechen als einen Quota-Call fuer Muell verbrennen.
        per_exp = ours["n_contracts"] / max(ours["n_expiries"], 1)
        if ours["n_contracts"] < a.min_contracts or per_exp < 30:
            print(f"  [ABBRUCH] Chain unplausibel duenn ({ours['n_contracts']} Kontrakte, "
                  f"{per_exp:.0f}/Expiry) — Yahoo hat vermutlich noch kein Open Interest.")
            print("            Spaeter erneut versuchen, --snapshot <datum> nutzen oder --force.")
            if not a.force:
                return 5

    if a.dry_run:
        print("\n[dry-run] FlashAlpha übersprungen (0 Quota verbraucht).")
        return 0

    key = _load_key(a.api_key)
    if not key:
        print("  [FEHLER] Kein FLASHALPHA_API_KEY (.env / Env / --api-key)")
        return 2

    # ── 2) FlashAlpha
    if a.account:
        try:
            acc = mcp_call("get_account", {"apiKey": key})["parsed"]
            print(f"      Account: Plan {acc.get('plan')} · heute {acc.get('usage_today')}/"
                  f"{acc.get('daily_limit')} · übrig {acc.get('remaining')}")
            if str(acc.get("remaining")) == "0":
                print("  [ABBRUCH] Quota für heute aufgebraucht — Reset "
                      f"{acc.get('resets_at')}. Kein get_gex-Call abgesetzt.")
                return 3
        except Exception as e:  # noqa: BLE001
            print(f"      [WARN] get_account fehlgeschlagen: {e}")

    print(f"[2/2] FlashAlpha get_gex für {tk} …", flush=True)
    args = {"symbol": tk, "apiKey": key}
    if a.min_oi is not None:
        args["min_oi"] = a.min_oi
    if a.expiration:
        args["expiration"] = a.expiration
    try:
        fa = mcp_call("get_gex", args)["parsed"]
    except Exception as e:  # noqa: BLE001
        print(f"  [FEHLER] {e}")
        return 4
    # Fehler kommen teils als Klartext mit eingebettetem JSON (nicht als sauberes Objekt)
    # → beide Formen erkennen, sonst landet ein 403 unbemerkt als „n/a" in der Tabelle.
    err_obj = fa if isinstance(fa, dict) and "status" in fa else None
    if err_obj is None and isinstance(fa, dict) and "_text" in fa:
        for line in fa["_text"].splitlines():
            line = line.strip()
            if line.startswith("{"):
                try:
                    err_obj = json.loads(line)
                    break
                except json.JSONDecodeError:
                    pass
        if err_obj is None and "ERROR" in fa["_text"][:80]:
            print(f"  [FEHLER] FlashAlpha: {fa['_text'][:300]}")
            return 4
    if err_obj and str(err_obj.get("status", "")).upper() == "ERROR":
        msg = err_obj.get("message") or err_obj.get("error")
        print(f"  [FEHLER] FlashAlpha ({err_obj.get('error')}): {msg}")
        if err_obj.get("required_plan"):
            print(f"           Plan {err_obj.get('current_plan')} → benötigt {err_obj['required_plan']}")
        return 4

    # ── 3) Rohantwort sichern (Schema dokumentieren)
    _OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    raw_path = _OUT_DIR / f"flashalpha_gex_{tk}_{stamp}.json"
    raw_path.write_text(json.dumps(fa, indent=2, ensure_ascii=False), encoding="utf-8")

    # ── 4) Gegenüberstellung
    rows = compare(tk, ours, fa)
    print("\n" + "=" * 74)
    print(f"  {tk} — SeasonAlpha vs. FlashAlpha   ({datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC)")
    print("=" * 74)
    print(f"  {'Kennzahl':<22}{'SeasonAlpha':>16}{'FlashAlpha':>16}{'Δ':>14}")
    print("  " + "-" * 68)
    for label, o, t in rows:
        print(f"  {label:<22}{_fmt(o):>16}{_fmt(t):>16}{_delta(o, t):>14}")
    print("  " + "-" * 68)
    print("  Hinweis: unser net-GEX ist in Mrd $/1 %; FlashAlphas Einheit kann abweichen")
    print("           → Vorzeichen + Wall-/Flip-Strikes sind der eigentliche Vergleich.")
    print(f"\n  Rohantwort: {raw_path.relative_to(_ROOT)}")
    if isinstance(fa, dict):
        print(f"  Top-Level-Keys: {sorted(fa.keys())[:15]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
