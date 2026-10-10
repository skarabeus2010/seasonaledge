#!/usr/bin/env python3
"""
Wächter: Ticker → Börsenkalender und strenge Börsenprüfung (Paket 3, Plan v4 K3/K4).

  [Bestand]   Jede Zuordnung aus scripts/fixtures/ticker_boerse_2026-10-10.json (370 Ticker, Stand vor
              der Vereinheitlichung) bleibt gleich; neu hinzugekommene SYMBOLS-Ticker lösen sich ohne Fehler auf.
  [Regel]     Suffix-, Groß/Klein-, Krypto-, Forex- und Fehlerfälle für Ticker ohne SYMBOLS-Eintrag.
  [Streng]    get_holidays / is_holiday / is_trading_day / handelstag_nummern / kalender_status /
              letzte_session / markt_offen lehnen eine unbekannte Börse mit ValueError ab — auch am Wochenende.
  [Einzig]    Es gibt keine zweite Ticker-Zuordnung mehr (TICKER_TO_EXCHANGE, get_exchange_for_ticker).

Nur Standardbibliothek. Aufruf:  py -3.14 scripts/verify_ticker_boerse.py      Exit 0 = alles erfüllt
"""
from __future__ import annotations

import json
import os
import sys
from datetime import date, datetime, timezone

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, WURZEL)

import shared.exchange_holidays as eh  # noqa: E402
from shared.symbols import SYMBOLS, get_exchange_for_holidays  # noqa: E402

FEHLER: list[str] = []
ZAEHLER = {"n": 0}


def pruefe(kennung: str, bedingung: bool, text: str = "") -> None:
    ZAEHLER["n"] += 1
    if not bedingung:
        FEHLER.append(f"[{kennung}] {text}")


def wirft_valueerror(f) -> bool:
    try:
        f()
    except ValueError:
        return True
    return False


def block_bestand() -> None:
    with open(os.path.join(WURZEL, "scripts", "fixtures", "ticker_boerse_2026-10-10.json"), encoding="utf-8") as fh:
        soll = json.load(fh)["zuordnung"]
    abw = {t: (b, get_exchange_for_holidays(t)) for t, b in soll.items() if get_exchange_for_holidays(t) != b}
    pruefe("Bestand 370 Zuordnungen unverändert", not abw and len(soll) == 370,
           f"{len(abw)} abweichend: {list(abw.items())[:5]}")
    neu = [t for t in SYMBOLS if t not in soll]
    kaputt = []
    for t in neu:
        try:
            get_exchange_for_holidays(t)
        except ValueError as e:
            kaputt.append(f"{t}: {e}")
    pruefe("Bestand neue SYMBOLS-Ticker auflösbar", not kaputt, "; ".join(kaputt[:5]))


REGELFAELLE = [
    # (Ticker, Soll) — Soll None = ValueError
    ("AAPL", "NYSE"), ("aapl", "NYSE"), (" spy ", "NYSE"),
    ("SAP", "NYSE"),            # US-ADR ohne Suffix
    ("SAP.DE", "XETRA"), ("sap.de", "XETRA"),
    ("ENR.F", "XETRA"), ("NEU.F", "XETRA"),
    ("NEU.DE", "XETRA"), ("air.pa", "EURONEXT"), ("NEU.AS", "EURONEXT"), ("NEU.MC", "EURONEXT"),
    ("NEU.BR", "EURONEXT"), ("NEU.LS", "EURONEXT"),   # Codex Paket 3: beide ungeschützt
    ("NEU.L", "LSE"), ("NEU.SW", "SIX"), ("NEU.MI", "MILAN"), ("NEU.ST", "STOCKHOLM"),
    ("NEU.CO", "STOCKHOLM"), ("NEU.OL", "OSLO"), ("NEU.T", "TSE"), ("NEU.HK", "HKEX"), ("NEU.KS", "KRX"),
    ("BTC-USD", "CRYPTO"), ("NEU-USDT", "CRYPTO"), ("EURUSD=X", "FOREX"), ("neu=x", "FOREX"),
    ("^GDAXI", "XETRA"), ("^gdaxi", "XETRA"), ("^N225", "TSE"), ("GC=F", "NYSE"),
    ("^XYZ", None), ("NEU=F", None), ("NEU.XX", None), ("", None), ("   ", None), (None, None),
]


def block_regel() -> None:
    # Ein SYMBOLS-Eintrag mit einer Börse ohne Kalender muss scheitern — kein heutiger Ticker
    # hat das, also vorübergehend einen einsetzen (Mutation „wird still US“ entwischte sonst).
    import shared.symbols as sy
    SYMBOLS["^SA_TEST"] = {"exchange": "Mondbörse"}
    sy._SYMBOLS_GROSS = None
    try:
        pruefe("Regel SYMBOLS-Börse ohne Kalender", wirft_valueerror(lambda: get_exchange_for_holidays("^SA_TEST")),
               "erwartet ValueError, kein US-Ersatz")
    finally:
        del SYMBOLS["^SA_TEST"]
        sy._SYMBOLS_GROSS = None
    for ticker, soll in REGELFAELLE:
        if soll is None:
            pruefe(f"Regel {ticker!r}", wirft_valueerror(lambda: get_exchange_for_holidays(ticker)),
                   "erwartet ValueError, kein NYSE-Ersatz")
        else:
            try:
                ist = get_exchange_for_holidays(ticker)
            except ValueError as e:
                ist = f"ValueError: {e}"
            pruefe(f"Regel {ticker!r}", ist == soll, f"soll {soll}, ist {ist}")


def block_streng() -> None:
    sa, mi = date(2026, 10, 10), date(2026, 10, 7)
    jetzt = datetime(2026, 10, 7, 22, 0, tzinfo=timezone.utc)
    faelle = {
        "is_trading_day Samstag": lambda: eh.is_trading_day(sa, "FOO"),
        "is_trading_day Mittwoch": lambda: eh.is_trading_day(mi, "FOO"),
        "is_trading_day leer": lambda: eh.is_trading_day(mi, ""),
        "is_holiday": lambda: eh.is_holiday(mi, "FOO"),
        "get_holidays": lambda: eh.get_holidays("FOO", 2026, 2026),
        "handelstag_nummern": lambda: eh.handelstag_nummern([], "FOO"),
        "kalender_status": lambda: eh.kalender_status("FOO", 2026),
        "letzte_session": lambda: eh.letzte_session("FOO", jetzt=jetzt),
        "letzte_session FOREX ohne Schlusszeit": lambda: eh.letzte_session("FOREX", jetzt=jetzt),
        "markt_offen": lambda: eh.markt_offen("FOO", jetzt=jetzt),
        "markt_offen XETRA ohne Öffnungszeit": lambda: eh.markt_offen("XETRA", jetzt=jetzt),
    }
    for name, f in faelle.items():
        pruefe(f"Streng {name}", wirft_valueerror(f), "erwartet ValueError")
    # Gültige Aliasse und Schreibweisen funktionieren weiter
    pruefe("Streng NASDAQ = NYSE", eh.is_trading_day(date(2025, 1, 9), "nasdaq") is False)
    pruefe("Streng Kleinschreibung", eh.is_trading_day(date(2026, 1, 2), "xetra") is True)
    pruefe("Streng Standard NYSE", eh.letzte_session(jetzt=jetzt) == date(2026, 10, 7))


def block_einzig() -> None:
    pruefe("Einzig keine zweite Zuordnung", not any(hasattr(eh, n) for n in
           ("TICKER_TO_EXCHANGE", "_TICKER_MAP", "get_exchange_for_ticker", "get_holidays_for_ticker")))
    pruefe("Einzig keine Root-Kopie", not os.path.exists(os.path.join(WURZEL, "exchange_holidays.py")))


def main() -> int:
    for name, block in (("Bestand", block_bestand), ("Regel", block_regel),
                        ("Streng", block_streng), ("Einzig", block_einzig)):
        try:
            block()
        except Exception as e:  # eine Ausnahme ist nie ein Nachweis
            FEHLER.append(f"[Ausnahme] Block {name}: {type(e).__name__}: {e}")
    print(f"verify_ticker_boerse: {ZAEHLER['n'] - len(FEHLER)}/{ZAEHLER['n']} Prüfungen bestanden")
    for f in FEHLER:
        print("  FEHL", f)
    print(f"PROBE-ENDE {ZAEHLER['n']} Pruefungen")
    return 1 if FEHLER else 0


if __name__ == "__main__":
    sys.exit(main())
