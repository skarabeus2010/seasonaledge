#!/usr/bin/env python3
"""
SeasonAlpha — kopierte Kurszeilen reparieren (Nutzerfreigabe 2026-10-17).

Befund (Messung 2026-10-17, `logs`/Server `/root/kopierte_zeilen.jsonl`): 526 Zeilen an Handelstagen bei 10 Tickern
tragen eine flache Kerze (Hoch = Tief, meist Vortagsschluss mit Volumen 0), obwohl Yahoo heute eine echte Kerze hat.
Geschrieben beim Massen-Neuladen 18.03./01.04./03.04.2026 — vermutlich lieferte Yahoo damals Platzhalter.
Folge: Tagesrendite 0, die Bewegung landet am Folgetag; Tagesstatistiken (Wochentage, TDOM, Overnight) falsch.

Regel je Kandidat t (flache DB-Zeile an einem Handelstag, Yahoo-Kerze mit Hoch > Tief und Volumen > 0):
  Faktor f = DB-Schluss / Yahoo-Schluss am nächsten SAUBEREN Tag davor (p) und danach (n); weichen f_p und f_n um mehr
  als 0,1 % ab, liegt dazwischen ein Wechsel der Bereinigung (Ex-Tag, Split) → übersprungen und gemeldet.
  Neu: O/H/L/C = Yahoo × f (4 Nachkommastellen), Volumen = Yahoo, log_return(t) = ln(C_t / C_vorher),
  log_return(Folgezeile) = ln(C_folge / C_t). Kontrolle: Σ log_return über t und Folgezeile bleibt gleich
  (die Kurve ab dem Folgetag stimmte schon) — sonst übersprungen.
Zeilen vor 2000 werden nicht angefasst. tdom/tdoy bleiben unverändert (die Zeilen existieren).

Nutzung (Server, im Container):
    python3 scripts/repair_kopierte_zeilen.py --ticker SIE.DE,BMW.DE          # Trockenlauf (Standard)
    python3 scripts/repair_kopierte_zeilen.py --ticker ... --schreiben         # Sicherung → Upsert → Rücklesen
"""
from __future__ import annotations

if __name__ != "__main__":   # Produktionssperre auch beim Import (shared/produktionssperre.py)
    from shared.produktionssperre import modul_sperre
    modul_sperre("repair_kopierte_zeilen")

import argparse
import json
import math
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

AB = "2000-01-01"
FAKTOR_TOL = 1e-3
SUMME_TOL = 1e-6
RUNDUNG_TOL = 1e-4          # relativer Fehler durch die 4 Nachkommastellen der DB (Codex R1: DOGE 0,000149 → 0,0001)
MAX_KANDIDATEN = 400        # Obergrenze je Lauf (Messung: 313 Zeilen bei den 8 Aktien)
MAX_UEBERSPRUNG = 0.25      # mehr übersprungene als erwartet → Abbruch ohne Schreiben
SICHERUNG = _ROOT / "logs" / "reparatur"


def _db_zeilen(c, t: str) -> list[dict]:
    out, last = [], "1999-12-01"
    while True:
        for v in range(4):
            try:
                d = (c.table("prices").select("date,open,high,low,close,volume,log_return,source").eq("ticker", t)
                     .gt("date", last).order("date").limit(1000).execute().data)
                break
            except Exception:
                if v == 3:
                    raise
                time.sleep(2 * (v + 1))
        if not d:
            return out
        out += d
        last = d[-1]["date"]
        if len(d) < 1000:
            return out


def _yahoo(t: str) -> dict:
    from shared.yahoo_downloader import _fetch_yahoo
    p1 = int(datetime(1999, 12, 1, tzinfo=timezone.utc).timestamp())
    y = _fetch_yahoo(t, {"period1": p1, "period2": int(time.time()), "interval": "1d"}, 30)
    res = y["chart"]["result"][0]
    tz = ZoneInfo((res.get("meta") or {}).get("exchangeTimezoneName") or "UTC")
    q = res["indicators"]["quote"][0]
    aus = {}
    for i, ts in enumerate(res.get("timestamp") or []):
        tag = datetime.fromtimestamp(ts, timezone.utc).astimezone(tz).date().isoformat()
        aus[tag] = {k: q[k][i] for k in ("open", "high", "low", "close", "volume")}
    return aus


def _echt(y: dict | None) -> bool:
    return bool(y) and all(y.get(k) is not None for k in ("open", "high", "low", "close")) \
        and y["high"] > y["low"] and (y.get("volume") or 0) > 0


def im_universum(t: str) -> bool:
    return not (t.endswith("-USD") or t.endswith("=X") or t.endswith("=F") or t.startswith("^"))


def _flach(r: dict) -> bool:
    return r.get("high") is not None and r.get("high") == r.get("low")


def planen(t: str, zeilen: list[dict], ya: dict, boerse: str) -> tuple[list[dict], list[dict], dict]:
    """→ (neue Datensätze für den Upsert, Sicherung der betroffenen Zeilen, Zähler je Ergebnis)."""
    from shared.exchange_holidays import is_trading_day
    idx = {r["date"]: i for i, r in enumerate(zeilen)}
    kand = [i for i, r in enumerate(zeilen) if r["date"] >= AB and _flach(r)
            and is_trading_day(date.fromisoformat(r["date"]), boerse) and _echt(ya.get(r["date"]))]
    kset = set(kand)
    zaehl = {"kandidaten": len(kand), "repariert": 0, "kein_sauberer_nachbar": 0, "basiswechsel": 0,
             "summe_abweichend": 0}
    neu_close: dict[int, float] = {}
    plan, sicher = {}, {}

    def sauber(i):
        """Saubere Nachbarzeile: kein Kandidat, nicht flach, Handelstag der Börse (keine Phantomzeile), Yahoo echt."""
        r = zeilen[i]
        return (i not in kset and not _flach(r) and r.get("close") and _echt(ya.get(r["date"]))
                and ya[r["date"]]["close"] and is_trading_day(date.fromisoformat(r["date"]), boerse))

    for i in kand:
        p = next((j for j in range(i - 1, -1, -1) if sauber(j)), None)
        n = next((j for j in range(i + 1, len(zeilen)) if sauber(j)), None)
        if p is None or n is None:
            zaehl["kein_sauberer_nachbar"] += 1
            continue
        fp = zeilen[p]["close"] / ya[zeilen[p]["date"]]["close"]
        fn = zeilen[n]["close"] / ya[zeilen[n]["date"]]["close"]
        if abs(fp / fn - 1) > FAKTOR_TOL:
            zaehl["basiswechsel"] += 1
            continue
        f = (fp + fn) / 2
        y = ya[zeilen[i]["date"]]
        neu = {k: round(y[k] * f, 4) for k in ("open", "high", "low", "close")}
        if any(abs(neu[k] / (y[k] * f) - 1) > RUNDUNG_TOL for k in neu):
            zaehl["rundung"] = zaehl.get("rundung", 0) + 1
            continue
        neu["volume"] = int(y["volume"])
        neu_close[i] = neu["close"]
        plan[i] = neu
    # log_return in Reihenfolge (aufeinanderfolgende Kandidaten nutzen die schon neuen Schlusskurse)
    def close(i):
        return neu_close.get(i, zeilen[i]["close"])

    # Ketten aufeinanderfolgender Kandidaten i..j; davor Zeile i−1, danach Folgezeile j+1 (beide nicht im Plan).
    # Kontrolle je Kette: die ALTE Σ log_return über i..j+1 muss zum Kursverhältnis C_{j+1}/C_{i−1} passen (sonst
    # sind die gespeicherten Renditen schon inkonsistent → nicht anfassen). Die neuen Renditen summieren sich dann
    # zwangsläufig zum selben Wert; die Kurve ab der Folgezeile bleibt unverändert.
    datensaetze, ketten, i_alle = [], [], sorted(plan)
    for i in i_alle:
        if ketten and ketten[-1][-1] == i - 1:
            ketten[-1].append(i)
        else:
            ketten.append([i])
    for kette in ketten:
        a, b = kette[0], kette[-1]
        if a == 0 or b + 1 >= len(zeilen):
            zaehl["kein_sauberer_nachbar"] += len(kette)
            continue
        # Vor- und Folgezeile müssen saubere Handelstage sein: kein übersprungener Kandidat (seine Bewegung rutschte
        # sonst herein) und keine Phantomzeile an einem Börsenfeiertag (Codex R1: Rendite landete auf dem 01.05.)
        if not (sauber(a - 1) and sauber(b + 1)):
            zaehl["nachbar_ungeklaert"] = zaehl.get("nachbar_ungeklaert", 0) + len(kette)
            continue
        alt = sum((zeilen[k].get("log_return") or 0.0) for k in range(a, b + 2))
        soll = math.log(zeilen[b + 1]["close"] / zeilen[a - 1]["close"])
        if abs(alt - soll) > 1e-4 + 1e-4 / zeilen[b + 1]["close"] + 1e-4 * len(kette):
            zaehl["summe_abweichend"] += len(kette)
            continue
        neu_lr = {k: round(math.log(close(k) / close(k - 1)), 8) for k in range(a, b + 2)}
        if abs(sum(neu_lr.values()) - soll) > SUMME_TOL + 1e-8 * len(neu_lr):
            zaehl["summe_abweichend"] += len(kette)
            continue
        for k in kette:
            datensaetze.append({"ticker": t, "date": zeilen[k]["date"], **plan[k], "log_return": neu_lr[k]})
            sicher[zeilen[k]["date"]] = zeilen[k]
        f_ = zeilen[b + 1]
        datensaetze.append({"ticker": t, "date": f_["date"], "open": f_["open"], "high": f_["high"], "low": f_["low"],
                            "close": f_["close"], "volume": f_["volume"], "log_return": neu_lr[b + 1]})
        sicher[zeilen[b + 1]["date"]] = zeilen[b + 1]
        zaehl["repariert"] += len(kette)
    return datensaetze, [dict(v, ticker=t) for v in sicher.values()], zaehl


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticker", required=True, help="kommagetrennt")
    ap.add_argument("--schreiben", action="store_true")
    a = ap.parse_args()
    from shared.supabase_client import get_client, upsert_prices
    from shared.symbols import get_exchange_for_holidays
    c = get_client()
    alle_rec, alle_sicher, gesamt = [], [], {}
    liste = [x.strip() for x in a.ticker.split(",") if x.strip()]
    fremd = [t for t in liste if not im_universum(t)]
    if fremd:
        print(f"[abbruch] nur Aktien/ETFs: {fremd}", flush=True)
        return 2
    for t in liste:
        boerse = get_exchange_for_holidays(t)
        zeilen, ya = _db_zeilen(c, t), _yahoo(t)
        rec, sicher, z = planen(t, zeilen, ya, boerse)
        print(f"{t:10} {boerse:8} {json.dumps(z)}", flush=True)
        for r in rec[:3]:
            print("   ", json.dumps(r), flush=True)
        alle_rec += rec
        alle_sicher += sicher
        for k, v in z.items():
            gesamt[k] = gesamt.get(k, 0) + v
    print("GESAMT", json.dumps(gesamt), "Datensätze", len(alle_rec), flush=True)
    kand = gesamt.get("kandidaten", 0)
    if kand > MAX_KANDIDATEN:
        print(f"[abbruch] {kand} Kandidaten > {MAX_KANDIDATEN}", flush=True)
        return 2
    if kand and (kand - gesamt.get("repariert", 0)) / kand > MAX_UEBERSPRUNG:
        print(f"[abbruch] Überspringquote {(kand - gesamt.get('repariert', 0)) / kand:.0%} > {MAX_UEBERSPRUNG:.0%}", flush=True)
        return 2
    if len({frozenset(r) for r in alle_rec}) > 1:
        print("[abbruch] Datensätze mit verschiedenen Spaltensätzen — Upsert wäre nicht eine Anfrage", flush=True)
        return 2
    if not a.schreiben:
        print("[trocken] nichts geschrieben", flush=True)
        return 0
    SICHERUNG.mkdir(parents=True, exist_ok=True)
    stempel = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    (SICHERUNG / f"kopierte_zeilen_plan_{stempel}.json").write_text(json.dumps(alle_rec, ensure_ascii=False), encoding="utf-8")
    pfad = SICHERUNG / f"kopierte_zeilen_vorher_{stempel}.json"
    pfad.write_text(json.dumps(alle_sicher, ensure_ascii=False), encoding="utf-8")
    print(f"[sicherung] {len(alle_sicher)} Zeilen → {pfad}", flush=True)
    upsert_prices(alle_rec)
    # Rücklesen: jeder geschriebene Wert muss so in der DB stehen
    abw = 0
    for r in alle_rec:
        d = c.table("prices").select("open,high,low,close,volume,log_return").eq("ticker", r["ticker"]) \
            .eq("date", r["date"]).execute().data
        if not d:
            abw += 1
            continue
        for k, v in r.items():
            if k in ("ticker", "date"):
                continue
            w = d[0].get(k)
            if w is None or abs(float(w) - float(v)) > 1e-9 * max(1.0, abs(float(v))):
                abw += 1
                print(f"[rücklesen] {r['ticker']} {r['date']} {k}: soll {v} ist {w}", flush=True)
    print(f"[rücklesen] {len(alle_rec)} Datensätze, {abw} Abweichungen", flush=True)
    return 1 if abw else 0


if __name__ == "__main__":
    # Produktionssperre (shared/produktionssperre.py): während einer Kalender-Aktivierung Exit 75
    from shared.produktionssperre import produktion
    with produktion("repair_kopierte_zeilen"):
        sys.exit(main())
