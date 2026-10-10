#!/usr/bin/env python3
"""
SeasonAlpha — TDOM/TDOY prüfen und begrenzt reparieren (Plan v7, K3)
=====================================================================
Vergleicht `prices.tdom/tdoy` mit dem Börsenkalender (`shared.exchange_holidays.tdom_tdoy_fuer_ticker`)
und berichtet die Abweichungen je Jahr, getrennt nach TDOM und TDOY.

STANDARD IST EIN TROCKENLAUF. Geschrieben wird nur mit `--schreiben`, und nur innerhalb enger Grenzen —
die historische Massenkorrektur ist P5 (eine Transaktion mit Nutzerfreigabe), nicht dieses Skript.

  py -3.14 scripts/backfill_tdoy.py                                   # Bericht über alle Ticker
  py -3.14 scripts/backfill_tdoy.py --ticker SAP.DE                   # Bericht für einen Ticker
  py -3.14 scripts/backfill_tdoy.py --ticker SAP.DE --von 2026-09-01 --bis 2026-09-30 --schreiben
                                    [--max-aenderungen 500]

Grenzen beim Schreiben (alle geprüft, BEVOR der erste Schreibrequest geht):
  - genau ein Ticker, `--von` und `--bis` angegeben, `--von` ab 2001-01-01
  - kein Jahr im Bereich mit Kalenderstatus „ungeprueft“ (`kalender_status`)
  - höchstens `--max-aenderungen` geänderte Zeilen (Standard 500)
  - nur die Spalten tdom/tdoy, je Zeile per `update … eq(ticker) eq(date)`; jede Antwort muss genau eine
    Zeile bestätigen, sonst Fehler. Kein `close` im Schreibweg (früher: Upsert mit mitgelesenem Schlusskurs —
    ein Nightly dazwischen wäre überschrieben worden).
Exit 1 bei verweigertem Schreiben, Lese- oder Schreibfehlern.
"""
from __future__ import annotations

import os
import sys
from collections import Counter
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:  # Windows: UTF-8 erzwingen (cp1252 crasht sonst bei Datei-Umleitung)
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from shared.exchange_holidays import kalender_status, tdom_tdoy_fuer_ticker  # noqa: E402
from shared.symbols import SYMBOLS, get_exchange_for_holidays  # noqa: E402

FRUEHESTES_SCHREIBDATUM = date(2001, 1, 1)
MAX_AENDERUNGEN_STANDARD = 500


def lade(client, ticker: str, von: str | None, bis: str | None) -> list[dict]:
    """date, tdom, tdoy des Tickers im Bereich — seitenweise (1000er Grenze von PostgREST)."""
    zeilen, start = [], 0
    while True:
        q = client.table("prices").select("date,tdom,tdoy").eq("ticker", ticker)
        if von:
            q = q.gte("date", von)
        if bis:
            q = q.lte("date", bis)
        r = q.order("date").range(start, start + 999).execute()
        zeilen.extend(r.data or [])
        if len(r.data or []) < 1000:
            return zeilen
        start += 1000


def abweichungen(ticker: str, zeilen: list[dict]) -> list[dict]:
    soll = tdom_tdoy_fuer_ticker(ticker, [z["date"] for z in zeilen])
    out = []
    for z, (tdom, tdoy) in zip(zeilen, soll):
        if z.get("tdom") != tdom or z.get("tdoy") != tdoy:
            out.append({"date": z["date"], "alt": (z.get("tdom"), z.get("tdoy")), "neu": (tdom, tdoy)})
    return out


def bericht(ticker: str, abw: list[dict]) -> None:
    je_jahr_tdom, je_jahr_tdoy = Counter(), Counter()
    for a in abw:
        j = a["date"][:4]
        if a["alt"][0] != a["neu"][0]:
            je_jahr_tdom[j] += 1
        if a["alt"][1] != a["neu"][1]:
            je_jahr_tdoy[j] += 1
    jahre = sorted(set(je_jahr_tdom) | set(je_jahr_tdoy))
    print(f"  {ticker:10s} {len(abw):6d} Zeilen abweichend"
          + (": " + ", ".join(f"{j} TDOM {je_jahr_tdom[j]}/TDOY {je_jahr_tdoy[j]}" for j in jahre[:8])
             + (" …" if len(jahre) > 8 else "") if jahre else ""))


def grenzen_pruefen(ticker: str | None, von: str | None, bis: str | None, abw: list[dict],
                    max_aenderungen: int) -> list[str]:
    """Alle Gründe, warum NICHT geschrieben werden darf (leer = darf)."""
    gruende = []
    if not ticker:
        gruende.append("--ticker fehlt (Schreiben nur für genau einen Ticker)")
    if not von or not bis:
        gruende.append("--von und --bis sind beim Schreiben Pflicht")
        return gruende
    try:
        d_von, d_bis = date.fromisoformat(von), date.fromisoformat(bis)
    except ValueError:
        return gruende + [f"ungültiger Bereich {von}..{bis}"]
    if d_von < FRUEHESTES_SCHREIBDATUM:
        gruende.append(f"--von vor {FRUEHESTES_SCHREIBDATUM} (ältere Historie nur über P5)")
    if d_bis < d_von:
        gruende.append("--bis liegt vor --von")
    if ticker:
        boerse = get_exchange_for_holidays(ticker)
        for j in range(d_von.year, d_bis.year + 1):
            if kalender_status(boerse, j) == "ungeprueft":
                gruende.append(f"{boerse} {j}: Kalender ungeprüft")
    if len(abw) > max_aenderungen:
        gruende.append(f"{len(abw)} Änderungen > --max-aenderungen {max_aenderungen} (Massenkorrektur = P5)")
    return gruende


def schreiben(client, ticker: str, abw: list[dict]) -> list[str]:
    fehler = []
    for a in abw:
        tdom, tdoy = a["neu"]
        try:
            r = (client.table("prices").update({"tdom": tdom, "tdoy": tdoy})
                 .eq("ticker", ticker).eq("date", a["date"]).execute())
            if len(r.data or []) != 1:
                fehler.append(f"{a['date']}: {len(r.data or [])} Zeilen bestätigt statt 1")
        except Exception as e:
            fehler.append(f"{a['date']}: {str(e)[:120]}")
    return fehler


def wert(args: list[str], name: str) -> str | None:
    return args[args.index(name) + 1] if name in args and args.index(name) + 1 < len(args) else None


def main(argv: list[str] | None = None, client=None) -> int:
    args = sys.argv[1:] if argv is None else argv
    ticker, von, bis = wert(args, "--ticker"), wert(args, "--von"), wert(args, "--bis")
    schreib = "--schreiben" in args
    max_aenderungen = int(wert(args, "--max-aenderungen") or MAX_AENDERUNGEN_STANDARD)
    if client is None:
        from shared.supabase_client import get_client
        client = get_client()

    tickers = [ticker] if ticker else sorted(SYMBOLS)
    if schreib and len(tickers) != 1:
        print("VERWEIGERT: --schreiben nur mit genau einem --ticker")
        return 1
    print(f"TDOM/TDOY gegen Börsenkalender — {'SCHREIBEN' if schreib else 'Trockenlauf'}"
          f"{f', {von}..{bis}' if von or bis else ''}")
    fehler, alle_abw = [], {}
    for t in tickers:
        try:
            abw = abweichungen(t, lade(client, t, von, bis))
        except Exception as e:
            fehler.append(f"{t}: {type(e).__name__}: {str(e)[:120]}")
            continue
        alle_abw[t] = abw
        if abw or ticker:
            bericht(t, abw)

    if schreib and not fehler:
        abw = alle_abw.get(ticker, [])
        gruende = grenzen_pruefen(ticker, von, bis, abw, max_aenderungen)
        if gruende:
            print("VERWEIGERT — nichts geschrieben:")
            for g in gruende:
                print("  -", g)
            return 1
        fehler.extend(schreiben(client, ticker, abw))
        if not fehler:
            print(f"  {len(abw)} Zeilen geschrieben und bestätigt")
    for f in fehler[:20]:
        print("  FEHLER", f)
    return 1 if fehler else 0


if __name__ == "__main__":
    sys.exit(main())
