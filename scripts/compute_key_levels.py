#!/usr/bin/env python3
"""
compute_key_levels.py — Key Levels & Max Pain je Ticker (SpotGamma-Style-Panel).

Kombiniert zwei Quellen zu einem kompakten, teilbaren Level-Set je Ticker:
  1) landing/data/gex_summary.json (bereits aus der Massive-Voll-Chain gebaut):
     Spot, Zero-Gamma-Flip (= Vol-Trigger), Regime, Call-/Put-Wall.
     Diese Felder werden DIREKT übernommen (nicht neu gerechnet).
  2) Massive/Polygon-Option-Chain-Snapshot: Max Pain + OI-by-Strike + P/C-OI-Ratio
     (das steckt NICHT in gex_summary).

Max Pain (je nächstem großen Verfall mit substantieller OI, 0DTE gemieden):
  Der Strike, der die Summe der Auszahlungen über alle offenen Kontrakte minimiert:
    Σ_calls OI·max(0, S−K) + Σ_puts OI·max(0, K−S)  über Kandidat-S = alle Strikes.

Schreibt landing/data/key_levels.json (gitignored).

Nutzung:  py -3.14 scripts/compute_key_levels.py [--tickers SPY QQQ IWM DIA NVDA ...]
"""
from __future__ import annotations
import argparse, gc, json, os, ssl, sys, time, urllib.error, urllib.request
from datetime import date, timedelta
from pathlib import Path

_THROTTLE = 0.05  # s zwischen Massive-Seiten (flatrate/unlimited; kleiner Puffer)

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from shared.atomic_json import write_json_atomic  # noqa: E402
from shared.env_loader import load_env          # noqa: E402
load_env()
from shared.options_universe import CORE_OPTIONS, categories_for  # noqa: E402
from shared.niveau_felder import Z_QUELLE_FEHLT, feldzustand  # noqa: E402
from shared.exchange_holidays import letzte_session, pruefe_eod_fenster, MarktOffen  # noqa: E402
# Import-Einstieg: ein Schutz nur am __main__ ist ein Schutz fuer EINEN Aufrufer
# (v66.12). Wer dieses Modul importiert und die Rechnung direkt aufruft, haelt den
# geteilten Lock ab hier bis zum Prozessende.
if __name__ != "__main__":
    from shared.produktionssperre import modul_sperre
    modul_sperre("compute_key_levels")


_CTX = ssl.create_default_context(); _CTX.check_hostname = False; _CTX.verify_mode = ssl.CERT_NONE
# Massive.com (Polygon.io) Option-Chain-Snapshot — Flatrate, 1 Ticker = ganze Chain, paginiert.
_SNAP = "https://api.polygon.io/v3/snapshot/options/{sym}?expiration_date.lte={hi}&limit=250"
_MAXDTE = 70                       # Max Pain am nächsten Monatsverfall reicht (≤70d)
_MIN_EXP_OI = 5000                 # min. Gesamt-OI eines Verfalls, damit er als "groß" zählt
_DEFAULT_TICKERS = CORE_OPTIONS    # SPY, QQQ, IWM, DIA + Mag7


# Obergrenze fuer ALLE 429-Pausen dieses Prozesses — dieselbe Regel wie im Snapshot.
# Ohne sie waere das Budget der Kette nicht begrenzt: bis zu 45 Seiten je Ticker mit
# je 20 s Backoff liegen weder im Snapshot-Budget noch in den gemessenen 77 s der
# Key Levels (Codex D3). Die Containerfrist der Unit rechnet mit beiden Budgets.
_WARTE_BUDGET = 300.0
_gewartet_gesamt = 0.0


def _warte_zuruecksetzen() -> None:
    global _gewartet_gesamt
    _gewartet_gesamt = 0.0


def _get(url: str, key: str, tries: int = 5):
    """GET (Massive: apiKey als Query-Param) mit 429-Backoff und Prozess-Wartebudget."""
    global _gewartet_gesamt
    full = url + ("&" if "?" in url else "?") + "apiKey=" + key
    for i in range(tries):
        time.sleep(_THROTTLE)
        try:
            return json.loads(urllib.request.urlopen(
                urllib.request.Request(full, headers={"User-Agent": "SeasonAlpha/1.0"}),
                timeout=30, context=_CTX).read())
        except urllib.error.HTTPError as e:
            if e.code != 429 or i >= tries - 1:
                raise
            pause = 2.0 * (i + 1)
            if _gewartet_gesamt + pause > _WARTE_BUDGET:
                print(f"  [get] Wartebudget {_WARTE_BUDGET:.0f} s aufgebraucht", flush=True)
                raise
            _gewartet_gesamt += pause
            time.sleep(pause)


def _chain(sym: str, key: str, session: date) -> tuple[list, bool]:
    """Volle Option-Chain (≤_MAXDTE ab der Session), paginiert.

    Zurueck kommt (Kontrakte, vollstaendig) — vollstaendig nur am Ende der Paginierung.
    Seiten-Cap oder unbrauchbare Antwort heissen abgeschnitten; ein daraus gerechnetes
    Max Pain ist nicht beurteilbar und wird in der Zeile als `teilkette` gekennzeichnet
    statt als Ergebnis (Spec B1)."""
    hi = (session + timedelta(days=_MAXDTE)).isoformat()
    url = _SNAP.format(sym=sym, hi=hi)
    out, pages, vollstaendig = [], 0, True
    while url and pages < 45:
        d = _get(url, key)
        if d.get("status") not in ("OK", "DELAYED") and not d.get("results"):
            vollstaendig = False
            break
        out += d.get("results", [])
        url = d.get("next_url")
        pages += 1
    if url:                      # Cap gerissen, es gaebe noch eine Seite
        vollstaendig = False
    return out, vollstaendig


def _by_exp(contracts: list, session: date) -> dict:
    """Kontrakte je Verfallstag: {exp: {dte, oi_total, calls:{K:oi}, puts:{K:oi}}}. DTE ab der Session."""
    today = session; by = {}
    for c in contracts:
        det = c.get("details") or {}
        ex = det.get("expiration_date"); typ = det.get("contract_type"); K = det.get("strike_price")
        oi = c.get("open_interest")
        if not ex or typ not in ("call", "put") or K is None:
            continue
        oi = float(oi or 0)
        e = by.setdefault(ex, {"dte": (date.fromisoformat(ex) - today).days,
                               "oi_total": 0.0, "calls": {}, "puts": {}})
        side = e["calls"] if typ == "call" else e["puts"]
        side[float(K)] = side.get(float(K), 0.0) + oi
        e["oi_total"] += oi
    return by


def _pick_expiry(by: dict) -> str | None:
    """Nächster Verfall mit substantieller OI (0DTE/heute meiden)."""
    cand = [(ex, e) for ex, e in by.items()
            if e["dte"] >= 1 and e["oi_total"] >= _MIN_EXP_OI]
    if not cand:  # Fallback: irgendein Verfall ≥1 DTE mit der meisten OI
        cand = [(ex, e) for ex, e in by.items() if e["dte"] >= 1]
    if not cand:
        return None
    # der früheste großer Verfall (nächster Monats-/Wochenverfall mit Substanz)
    cand.sort(key=lambda t: t[1]["dte"])
    return cand[0][0]


def _max_pain(e: dict) -> dict | None:
    """Max Pain + OI-Walls + P/C-Ratio für EINEN Verfall e."""
    calls, puts = e["calls"], e["puts"]
    # NUR Strikes mit offener Position als Kandidaten. Strikes mit OI=0 stehen zwar
    # in der Kette, tragen aber nichts zur Auszahlung bei — sie machen das Minimum
    # flach und konnten als „Max Pain" gemeldet werden, obwohl dort niemand
    # positioniert ist.
    strikes = sorted({k for k, v in calls.items() if v} | {k for k, v in puts.items() if v})
    if len(strikes) < 3:
        return None
    total_oi = sum(calls.values()) + sum(puts.values())
    if total_oi <= 0:                       # ohne offene Position gibt es kein Max Pain
        return None
    # Auszahlungs-Summe über alle offenen Kontrakte je Kandidat-Strike S; Argmin = Max Pain
    best_S, best_pay, n_min = None, None, 0
    for S in strikes:
        pay = 0.0
        for K, oi in calls.items():
            if S > K:
                pay += oi * (S - K)
        for K, oi in puts.items():
            if S < K:
                pay += oi * (K - S)
        if best_pay is None or pay < best_pay:
            best_pay, best_S, n_min = pay, S, 1
        elif pay == best_pay:
            n_min += 1                      # flaches Minimum — Auswahl ist dann willkuerlich
    call_oi_sum = sum(calls.values()); put_oi_sum = sum(puts.values())
    top_call = sorted(calls.items(), key=lambda kv: kv[1], reverse=True)[:5]
    top_put = sorted(puts.items(), key=lambda kv: kv[1], reverse=True)[:5]
    return {
        "max_pain": best_S,
        # Bei mehreren Strikes mit identischer Auszahlung gewinnt der niedrigste —
        # das ist keine Aussage, sondern Sortierreihenfolge. Flag machen es sichtbar.
        "max_pain_non_unique": n_min > 1,
        "exp": None,  # vom Aufrufer gesetzt
        "top_call_oi": [{"strike": k, "oi": int(v)} for k, v in top_call],
        "top_put_oi": [{"strike": k, "oi": int(v)} for k, v in top_put],
        "pc_oi_ratio": round(put_oi_sum / call_oi_sum, 3) if call_oi_sum else None,
        "call_oi_sum": int(call_oi_sum), "put_oi_sum": int(put_oi_sum),
    }


class LaufFremd(RuntimeError):
    """Die GEX-Ausgabe gehoert zu einem anderen Lauf als dem uebergebenen."""


def _load_gex(session: date, datei: str | None = None,
              lauf: str | None = None) -> tuple[dict, str]:
    """gex_summary.json → ({ticker: {...}}, status). Übernommen wird nur ein GEX-Lauf DERSELBEN Session mit
    Session-Stempel; sonst stünden nach einem ausgefallenen GEX-Lauf alte Walls/Flip neben frischem Max Pain unter dem
    neuen Datum (Plan v4 B2). Status: "ok" | "fehlt" | "alter_stempel" | "andere_session:<datum>" | "defekt"
    | "anderer_lauf:<kennung>".

    `datei` und `lauf` kommen von der Kette (B2). Mit ihnen wird GENAU die Ausgabe dieses
    Laufs gelesen statt der gemeinsamen Datei nach Session: lief ein zweiter Snapshot
    derselben Session dazwischen, hätte die Session-Prüfung allein ihn durchgelassen."""
    p = Path(datei) if datei else _ROOT / "landing/data/gex_summary.json"
    if not p.exists():
        print("  [gex] gex_summary.json fehlt — Flip/Walls bleiben leer.")
        return {}, "fehlt"
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"  [gex] {e}")
        return {}, "defekt"
    if d.get("stempel_art") != "session":
        print("  [gex] gex_summary.json ohne Session-Stempel — Spot/Flip/Walls werden nicht übernommen.")
        return {}, "alter_stempel"
    if lauf and d.get("lauf") != lauf:
        print(f"  [gex] {p.name} gehört zu Lauf {d.get('lauf')!r}, erwartet {lauf!r} — "
              "nicht übernommen.")
        return {}, "anderer_lauf:%s" % (d.get("lauf") or "—")
    if d.get("session") != session.isoformat():
        print(f"  [gex] gex_summary.json gehört zur Session {d.get('session')}, nicht {session} — nicht übernommen.")
        return {}, f"andere_session:{d.get('session')}"
    return {t["ticker"]: t for t in d.get("tickers", [])}, "ok"


def _one(sym: str, key: str, gex: dict, session: date) -> dict | None:
    """Ein Ticker: gex-Felder + Max-Pain/OI aus der Chain."""
    try:
        contracts, mp_kette_vollst = _chain(sym, key, session)
    except Exception as e:
        print(f"  [massive] {sym}: {str(e)[:80]}")
        # Kein Abruf zustande gekommen: der Ladezustand ist UNBEKANNT, nicht False.
        # `quelle_da=False` unten macht daraus `quelle_fehlt` — "nicht abgerufen" ist
        # etwas anderes als "abgebrochen" (Spec 3).
        contracts, mp_kette_vollst = [], None
    row = {"ticker": sym, "cats": categories_for(sym)}
    g = gex.get(sym, {})
    # gex_summary direkt übernehmen (nicht neu rechnen)
    row["spot"] = g.get("spot")
    row["vol_trigger"] = g.get("zero_gamma")
    row["regime"] = g.get("regime")
    row["call_wall"] = g.get("call_wall")
    row["put_wall"] = g.get("put_wall")
    row["net_gex_usd_bn"] = g.get("net_gex_usd_bn")
    # Max Pain + OI aus der Chain
    if contracts:
        by = _by_exp(contracts, session)
        ex = _pick_expiry(by)
        if ex:
            mp = _max_pain(by[ex])
            if mp:
                mp["exp"] = ex
                mp["exp_dte"] = by[ex]["dte"]
                row.update(mp)
    gc.collect()
    # B1: Zustaende je Niveau. Walls und Vol-Trigger rechnet diese Datei NICHT selbst,
    # sie kommen aus der GEX-Summary — ihr Zustand wird deshalb uebernommen und nicht neu
    # erfunden. Fehlt die GEX-Zeile, ist er `quelle_fehlt`.
    g_felder = g.get("felder") or {}
    row["gex_kette_vollst"] = g.get("gex_kette_vollst")
    row["mp_kette_vollst"] = mp_kette_vollst
    row["gex_horizont_tage"] = g.get("gex_horizont_tage")
    row["strike_stufe"] = g.get("strike_stufe")
    row["strike_stufe_quelle"] = g.get("strike_stufe_quelle")
    row["felder"] = {
        "call_wall": g_felder.get("call_wall", Z_QUELLE_FEHLT),
        "put_wall": g_felder.get("put_wall", Z_QUELLE_FEHLT),
        "vol_trigger": g_felder.get("vol_trigger", Z_QUELLE_FEHLT),
        "max_pain": feldzustand(row.get("max_pain"), mp_kette_vollst,
                                quelle_da=bool(contracts),
                                mehrdeutig=bool(row.get("max_pain_non_unique"))),
    }
    # Abstand Spot→Vol-Trigger und Spot→Max-Pain (%), fürs Frontend
    sp = row.get("spot")
    if sp:
        vt = row.get("vol_trigger")
        row["vt_dist_pct"] = round((sp - vt) / vt * 100, 2) if vt else None
        mpv = row.get("max_pain")
        row["mp_dist_pct"] = round((mpv - sp) / sp * 100, 2) if mpv else None
    # nur zurückgeben, wenn wenigstens irgendein Level da ist
    if row.get("spot") is None and row.get("max_pain") is None:
        print(f"  [skip] {sym}: keine Daten")
        return None
    return row


def _nur_gex(sym: str, g: dict) -> dict:
    """Zeile ohne Kettenabruf (kein API-Schluessel): nur die GEX-Felder.

    Max Pain ist hier nicht `kein_niveau`, sondern `quelle_fehlt` — es wurde nicht
    gerechnet, und ein fehlender Abruf darf nicht wie ein Ergebnis aussehen (Spec 3).
    Die Zustaende der Walls kommen wie im Normalfall aus der GEX-Zeile.
    """
    g_felder = g.get("felder") or {}
    return {
        "ticker": sym, "cats": categories_for(sym),
        "spot": g.get("spot"), "vol_trigger": g.get("zero_gamma"),
        "regime": g.get("regime"), "call_wall": g.get("call_wall"),
        "put_wall": g.get("put_wall"),
        "gex_kette_vollst": g.get("gex_kette_vollst"),
        "mp_kette_vollst": None,
        "gex_horizont_tage": g.get("gex_horizont_tage"),
        "strike_stufe": g.get("strike_stufe"),
        "strike_stufe_quelle": g.get("strike_stufe_quelle"),
        "felder": {
            "call_wall": g_felder.get("call_wall", Z_QUELLE_FEHLT),
            "put_wall": g_felder.get("put_wall", Z_QUELLE_FEHLT),
            "vol_trigger": g_felder.get("vol_trigger", Z_QUELLE_FEHLT),
            "max_pain": Z_QUELLE_FEHLT,
        },
    }


def build(tickers: list[str], write: bool = True, gex_datei: str | None = None,
          lauf: str | None = None) -> dict:
    tok = os.environ.get("MASSIVE_API_KEY") or os.environ.get("POLYGON_API_KEY", "")
    # Session einmal bestimmen; Schreiblauf in der Handelszeit bricht VOR dem ersten Abruf ab (MarktOffen).
    session = letzte_session("NYSE")
    if write:
        pruefe_eod_fenster("compute_key_levels")
    gex, gex_status = _load_gex(session, gex_datei, lauf)
    # Laufgebundene Uebergabe (B2): passt die Kennung nicht, ist die Summary nicht die
    # dieses Laufs. Dann ist jeder Wall-Wert ein fremder — weitermachen hiesse, Niveaus
    # aus zwei Laeufen in einer Zeile zu mischen.
    if lauf and gex_status.startswith("anderer_lauf"):
        raise LaufFremd(
            "gex_summary.json gehört nicht zu Lauf %s (%s) — nichts geschrieben"
            % (lauf, gex_status))
    per = []
    if not tok:
        print("  [massive] MASSIVE_API_KEY fehlt — Max-Pain/OI übersprungen (nur gex-Felder).")
    for t in tickers:
        r = _one(t, tok, gex, session) if tok else (
            _nur_gex(t, gex[t]) if t in gex else None)
        if r:
            per.append(r)
            print(f"  {t:6} spot {r.get('spot')} · flip {r.get('vol_trigger')} · "
                  f"MaxPain {r.get('max_pain')} ({r.get('exp')}) · CW {r.get('call_wall')} · "
                  f"PW {r.get('put_wall')} · P/C-OI {r.get('pc_oi_ratio')}")
    out = {
        "generated": date.today().isoformat(),     # Laufzeitpunkt (Health-Check)
        "session": session.isoformat(),            # Handelstag der Daten = Bewertungsdatum
        "gex_status": gex_status,
        "lauf": lauf,                              # Kennung des Kettenlaufs (B2)
        "source": "Spot/Flip/Walls/Regime + US-Option-Chain "
                  "(Max Pain, OI-by-Strike, P/C-OI). EOD, naive Dealer-Heuristik, kein Signal.",
        "tickers": per,
    }
    if write:
        p = _ROOT / "landing/data/key_levels.json"
        write_json_atomic(p, out, indent=2)
        print(f"\n[OK] {len(per)} Ticker → {p}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tickers", nargs="+", default=_DEFAULT_TICKERS)
    ap.add_argument("--no-write", action="store_true")
    ap.add_argument("--gex-datei", help="Ausgabe GENAU dieses GEX-Laufs (Kette, B2)")
    ap.add_argument("--lauf", help="Kennung des Kettenlaufs; muss zur Datei passen (B2)")
    a = ap.parse_args()
    try:
        build(a.tickers, not a.no_write, a.gex_datei, a.lauf)
    except MarktOffen as e:
        print(f"[key-levels] ABBRUCH: {e}")
        return 2
    except LaufFremd as e:
        print(f"[key-levels] ABBRUCH: {e}")
        return 3
    return 0


if __name__ == "__main__":
    from shared.produktionssperre import produktion
    with produktion("compute_key_levels"):
        sys.exit(main())
