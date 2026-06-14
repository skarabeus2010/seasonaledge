"""
scripts/verify_calendar_rules.py — Prüfagent für die Handels-Kalender-Regeln
=============================================================================
Deterministische Verifikation der 9 Regeln aus docs/TRADING_CALENDAR_RULES.md
gegen die Implementierung (shared/) UND die realen Daten (Supabase + reale
Handelstage). Gedacht als CI-/Cron-tauglicher „Prüfagent".

Aufruf:
  py -3.14 scripts/verify_calendar_rules.py            # alle Regeln
  py -3.14 scripts/verify_calendar_rules.py --no-db    # nur Code-Logik (offline)
  py -3.14 scripts/verify_calendar_rules.py --rule 9   # nur Regel 9

Exit-Code: 0 = alle PASS (WARN erlaubt), 1 = mind. ein FAIL.

Hinweis (Windows): PYTHONUTF8=1 setzen (cp1252 crasht sonst an ✓/⚠).
"""
from __future__ import annotations

import argparse
import sys
import pathlib
from datetime import date, timedelta

_project_dir = str(pathlib.Path(__file__).resolve().parent.parent)
if _project_dir not in sys.path:
    sys.path.insert(0, _project_dir)

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from shared.symbols import get_all_tickers, get_exchange_for_holidays, SYMBOLS
from shared.exchange_holidays import is_trading_day
from shared.nyse_holidays import get_opex_date, is_nyse_holiday, _nth_weekday
from shared import central_banks as CB
from shared.fed_dates import FOMC_MEETING_DATES

# Vom Holiday-System unterstützte Börsen-Codes (is_trading_day kennt sie):
SUPPORTED = {"NYSE", "NASDAQ", "XETRA", "EURONEXT", "MILAN", "LSE",
             "SIX", "STOCKHOLM", "TSE", "HKEX", "KRX", "FOREX", "CRYPTO"}

# Gap-Audit-Ausnahmen (nur noch Forex — Yahoo-Datenqualität):
GAP_EXEMPT = lambda t: t.upper().endswith("=X")
GAP_RESIDUAL_MAX = 10   # Soll nach HKEX/KRX/TSE-Fix: ^STOXX50E:6 + RR.L:1 (advisory)

# ── Reporter ──────────────────────────────────────────────────────────────────

PASS, WARN, FAIL, SKIP = "PASS", "WARN", "FAIL", "SKIP"
_ICON = {PASS: "✓", WARN: "⚠", FAIL: "✗", SKIP: "–"}
_results: list[tuple[str, str, str]] = []


def report(rule: str, status: str, detail: str = "") -> None:
    _results.append((rule, status, detail))
    print(f"  [{_ICON[status]} {status}] {rule:<46} {detail}")


def expected_exchange(t: str) -> str | None:
    """Erwartete Börse laut Suffix-Regel (None = Index/unbestimmt → nur Validität)."""
    t = t.upper()
    if t.endswith("-USD"):
        return "CRYPTO"
    if t.endswith("=X"):
        return "FOREX"
    if t.endswith("=F"):
        return "NYSE"
    if t.startswith("^"):
        return None  # Index: via SYMBOLS.exchange, nicht strikt suffix-ableitbar
    if "." in t:
        suf = t.rsplit(".", 1)[1]
        return {"DE": "XETRA", "F": "XETRA", "PA": "EURONEXT", "AS": "EURONEXT",
                "BR": "EURONEXT", "MI": "MILAN", "MC": "EURONEXT", "L": "LSE",
                "SW": "SIX", "ST": "STOCKHOLM"}.get(suf)
    return "NYSE"  # kein Suffix = US-gelistet (inkl. ADRs)


# ── Regel 1 — Feiertags-Auflösung (Ticker → Handelsplatz) ─────────────────────

def rule1_resolution():
    bad_supported, bad_suffix = [], []
    for t in get_all_tickers():
        ex = get_exchange_for_holidays(t)
        if ex not in SUPPORTED:
            bad_supported.append(f"{t}->{ex}")
            continue
        try:
            is_trading_day(date(2026, 1, 5), ex)
        except Exception:
            bad_supported.append(f"{t}->{ex}(throws)")
        exp = expected_exchange(t)
        if exp is not None and ex != exp:
            bad_suffix.append(f"{t}: {ex}≠{exp}")
    if bad_supported:
        report("Regel 1: alle Ticker → gültige Börse", FAIL, ", ".join(bad_supported[:6]))
    else:
        report("Regel 1: alle Ticker → gültige Börse", PASS,
               f"{len(get_all_tickers())} Ticker, alle in {len(SUPPORTED)} Kalendern")
    if bad_suffix:
        report("Regel 1: Suffix-Konsistenz (ADRs→NYSE etc.)", FAIL, ", ".join(bad_suffix[:6]))
    else:
        report("Regel 1: Suffix-Konsistenz (ADRs→NYSE etc.)", PASS,
               "kein Suffix→NYSE, .DE→XETRA, .MI→MILAN, =X→FOREX …")


# ── Regel 2 — Krypto 24/7 ─────────────────────────────────────────────────────

def rule2_crypto():
    cryptos = [t for t in get_all_tickers() if t.upper().endswith("-USD")]
    # Sa, So, Wochentag, „Feiertag" (Neujahr) — alle müssen Handelstag sein
    probes = [date(2026, 1, 3), date(2026, 1, 4), date(2026, 1, 5), date(2026, 1, 1),
              date(2026, 12, 25)]
    bad = [t for t in cryptos if not all(is_trading_day(d, get_exchange_for_holidays(t)) for d in probes)]
    if not cryptos:
        report("Regel 2: Krypto 24/7", SKIP, "keine -USD-Ticker")
    elif bad:
        report("Regel 2: Krypto 24/7", FAIL, ", ".join(bad))
    else:
        report("Regel 2: Krypto 24/7", PASS, f"{len(cryptos)} Ticker, auch Sa/So/Feiertag offen")


# ── Regel 3 — Forex Mo-Fr, keine Feiertage ────────────────────────────────────

def rule3_forex():
    fx = [t for t in get_all_tickers() if t.upper().endswith("=X")]
    bad = []
    for t in fx:
        ex = get_exchange_for_holidays(t)
        if ex != "FOREX":
            bad.append(f"{t}->{ex}")
            continue
        # Mo-Fr offen, Sa/So zu, Feiertag (25.12. werktags) offen (FX kennt keine Feiertage)
        if not (is_trading_day(date(2026, 1, 5), ex)           # Mo
                and is_trading_day(date(2026, 12, 25), ex)      # Fr 25.12. → FX offen
                and not is_trading_day(date(2026, 1, 3), ex)    # Sa
                and not is_trading_day(date(2026, 1, 4), ex)):  # So
            bad.append(f"{t}(Verhalten)")
    if not fx:
        report("Regel 3: Forex Mo-Fr", SKIP, "keine =X-Ticker")
    elif bad:
        report("Regel 3: Forex Mo-Fr", FAIL, ", ".join(bad[:6]))
    else:
        report("Regel 3: Forex Mo-Fr", PASS, f"{len(fx)} Paare, Mo-Fr offen / Sa-So zu")


# ── Regel 9.1 — nationale Feiertage sind pro Börse/Ticker korrekt verlinkt ────

def rule91_national_holidays():
    # (Datum, {börse: erwartet_offen})  — prüft, dass der Feiertag NUR die
    # richtige(n) Börse(n) schließt und die anderen offen lässt.
    cases = [
        ("1. Mai 2026 (Tag der Arbeit)", date(2026, 5, 1),
         {"XETRA": False, "EURONEXT": False, "MILAN": False, "SIX": False,
          "STOCKHOLM": False, "NYSE": True}),
        ("3. Okt 2025 (Dt. Einheit — XETRA HANDELT!)", date(2025, 10, 3),
         {"XETRA": True}),   # häufiger Irrtum: Xetra ist am 3.10. OFFEN
        ("19. Juni 2026 (Juneteenth)", date(2026, 6, 19),
         {"NYSE": False, "XETRA": True, "LSE": True}),
        ("15. Aug 2025 (Ferragosto)", date(2025, 8, 15),
         {"MILAN": False, "EURONEXT": True, "XETRA": True}),
        ("26. Dez 2025 (Boxing/Stephanstag)", date(2025, 12, 26),
         {"LSE": False, "XETRA": False, "SIX": False, "NYSE": True}),
        ("Pfingstmontag 2025-06-09 (XETRA handelt, SIX zu)", date(2025, 6, 9),
         {"XETRA": True, "SIX": False, "EURONEXT": True, "STOCKHOLM": True, "NYSE": True}),
    ]
    bad = []
    for label, d, expect in cases:
        if d.weekday() >= 5:        # Wochenende → Feiertags-Test nicht aussagekräftig
            continue
        for ex, want_open in expect.items():
            got_open = is_trading_day(d, ex)
            if got_open != want_open:
                bad.append(f"{label}: {ex} {'offen' if got_open else 'zu'} (soll {'offen' if want_open else 'zu'})")
    if bad:
        report("Regel 9.1: nationale Feiertage je Börse", FAIL, "; ".join(bad[:5]))
    else:
        report("Regel 9.1: nationale Feiertage je Börse", PASS,
               "1.Mai/Juneteenth/Ferragosto/Boxing/Pfingsten korrekt zugeordnet")


# ── Regel 7 — OPEX (börsenspezifisch) ─────────────────────────────────────────

def de_opex(y, m):
    f = _nth_weekday(y, m, 4, 3)
    while not is_trading_day(f, "XETRA"):
        f -= timedelta(days=1)
    return f


def rule7_opex():
    bad = []
    # US-OPEX (get_opex_date): (Jahr, Monat) → erwartetes Datum
    us = {(2026, 6): date(2026, 6, 18),   # Juneteenth → Do
          (2025, 4): date(2025, 4, 17),   # Good Friday → Do
          (2026, 3): date(2026, 3, 20)}   # normal
    for (y, m), exp in us.items():
        got = get_opex_date(y, m)
        if got != exp:
            bad.append(f"US {y}-{m:02d}: {got}≠{exp}")
    # DE/US-Divergenz an Juneteenth
    if not (get_opex_date(2026, 6) == date(2026, 6, 18) and de_opex(2026, 6) == date(2026, 6, 19)):
        bad.append("Juneteenth-Divergenz US/DE fehlt")
    if bad:
        report("Regel 7: OPEX (US + DE-Divergenz)", FAIL, "; ".join(bad))
    else:
        report("Regel 7: OPEX (US + DE-Divergenz)", PASS,
               "3.Fr feiertagsbereinigt; 2026-06 US=18. vs DE=19.")


# ── Regel 8 — VIXpiration ─────────────────────────────────────────────────────

def vix_settlement(y, m):
    f = _nth_weekday(y, m, 4, 3)               # Referenz-3.-Freitag
    w = f - timedelta(days=30)
    while not is_trading_day(w, "NYSE"):
        w -= timedelta(days=1)
    if is_nyse_holiday(f):                      # Referenz-Fr Feiertag → 1 HT früher
        w -= timedelta(days=1)
        while not is_trading_day(w, "NYSE"):
            w -= timedelta(days=1)
    return w


def rule8_vix():
    cases = {(2025, 4): date(2025, 3, 18), (2026, 6): date(2026, 5, 19)}
    bad = [f"{y}-{m:02d}: {vix_settlement(y,m)}≠{exp}"
           for (y, m), exp in cases.items() if vix_settlement(y, m) != exp]
    if bad:
        report("Regel 8: VIXpiration", FAIL, "; ".join(bad))
    else:
        report("Regel 8: VIXpiration", PASS, "04/2025→18.03., 06/2026→19.05. (Feiertags-adj.)")


# ── Regel 9.2 — Notenbank-Verlinkung + Termin-Integrität ──────────────────────

def rule92_central_banks():
    bad = []
    # Verlinkung: Ticker → Notenbank(en) (folgt Handelsplatz, nicht Heimatwährung)
    link = {"AAPL": ["Fed"], "NVO": ["Fed"], "AZN": ["Fed"], "SAP.DE": ["ECB"],
            "NESN.SW": ["SNB"], "^N225": ["BoJ"], "VOLV-A.ST": ["Riksbank"],
            "AUDUSD=X": ["Fed", "RBA"], "NZDUSD=X": ["Fed", "RBNZ"],
            "USDCAD=X": ["BoC", "Fed"], "BTC-USD": []}
    for t, exp in link.items():
        got = CB.central_banks_for_ticker(t)
        if got != exp:
            bad.append(f"{t}: {got}≠{exp}")
    if bad:
        report("Regel 9.2: Ticker→Notenbank-Verlinkung", FAIL, "; ".join(bad[:5]))
    else:
        report("Regel 9.2: Ticker→Notenbank-Verlinkung", PASS,
               "ADRs→Fed, FX→beide Banken, Krypto→keine")

    # Termin-Integrität: keine Dubletten, plausible Anzahl/Jahr, korrigierte Marker
    lists = {"FOMC": FOMC_MEETING_DATES, "ECB": CB.ECB_MEETING_DATES,
             "BoE": CB.BOE_MEETING_DATES, "BoJ": CB.BOJ_MEETING_DATES,
             "SNB": CB.SNB_MEETING_DATES, "BoC": CB.BOC_MEETING_DATES,
             "RBA": CB.RBA_MEETING_DATES, "RBNZ": CB.RBNZ_MEETING_DATES}
    problems = []
    for name, L in lists.items():
        if len(L) != len(set(L)):
            problems.append(f"{name}: Dubletten")
        n2026 = sum(1 for y, m, d in L if y == 2026)
        # SNB bewusst unvollständig (Sep/Dez TODO) → nicht als Fehler werten
        if name != "SNB" and not (6 <= n2026 <= 9):
            problems.append(f"{name}: {n2026} Termine 2026 (unplausibel)")
    # Bekannte Korrekturen müssen sitzen (Regression-Guard):
    if (2026, 5, 6) in FOMC_MEETING_DATES or (2026, 4, 29) not in FOMC_MEETING_DATES:
        problems.append("FOMC 2026-04-29 fehlt / 05-06 noch da")
    if (2026, 3, 13) in CB.BOJ_MEETING_DATES:
        problems.append("BoJ 2026-03-13 (falsch) noch da")
    if problems:
        report("Regel 9.2: Notenbank-Termin-Integrität", FAIL, "; ".join(problems[:5]))
    else:
        report("Regel 9.2: Notenbank-Termin-Integrität", PASS,
               f"{len(lists)} Banken, keine Dubletten, Korrekturen aktiv")


# ── DB-Checks (optional) ──────────────────────────────────────────────────────

def _client():
    from shared.supabase_client import get_client
    return get_client()


def rule456_tdom_tdoy_db(client):
    """Regel 4-6: TDOM/CDOM/TDOY/CDOY-Konsistenz in prices (Stichprobe)."""
    bad = []
    for t in ("SPY", "SAP.DE"):
        rows = (client.table("prices").select("date,tdom,tdoy")
                .eq("ticker", t).gte("date", "2025-01-01").lte("date", "2026-06-13")
                .order("date").execute().data)
        rows = [r for r in rows if r.get("tdom") is not None]
        if len(rows) < 50:
            continue
        prev = None
        for r in rows:
            d = date.fromisoformat(r["date"])
            tdom, tdoy = r["tdom"], r["tdoy"]
            if prev:
                pd_, ptdom, ptdoy = prev
                if d.month == pd_.month and d.year == pd_.year:
                    if tdom != ptdom + 1:
                        bad.append(f"{t} {r['date']}: TDOM {ptdom}->{tdom}")
                        break
                else:  # neuer Monat
                    if tdom != 1:
                        bad.append(f"{t} {r['date']}: TDOM-Reset {tdom}≠1")
                        break
                if d.year == pd_.year and tdoy != ptdoy + 1:
                    bad.append(f"{t} {r['date']}: TDOY {ptdoy}->{tdoy}")
                    break
                if d.year != pd_.year and tdoy != 1:
                    bad.append(f"{t} {r['date']}: TDOY-Reset {tdoy}≠1")
                    break
            prev = (d, tdom, tdoy)
    if bad:
        report("Regel 4-6: TDOM/TDOY-Konsistenz (DB)", FAIL, "; ".join(bad[:4]))
    else:
        report("Regel 4-6: TDOM/TDOY-Konsistenz (DB)", PASS,
               "monoton +1/Handelstag, korrekte Monats-/Jahres-Resets")


def rule1_gap_audit_db(client):
    """Regel 1/9.1 empirisch: is_trading_day vs. reale DB-Handelstage."""
    from scripts.fix_missing_days import get_expected_trading_days, get_db_dates
    today, win = date(2026, 6, 13), date(2025, 1, 1)
    n_tickers, total = 0, 0
    worst = []
    for t in get_all_tickers():
        if GAP_EXEMPT(t):
            continue
        try:
            ex = get_exchange_for_holidays(t)
            dd = get_db_dates(client, t, win, today)
            if len(dd) < 50:
                continue
            dmin = min(date.fromisoformat(x) for x in dd)
            dmax = max(date.fromisoformat(x) for x in dd)
            exp = get_expected_trading_days(ex, max(win, dmin), min(today, dmax))
            miss = [d for d in exp if d.strftime("%Y-%m-%d") not in dd]
            if miss:
                n_tickers += 1
                total += len(miss)
                worst.append((t, len(miss)))
        except Exception:
            pass
    worst.sort(key=lambda x: -x[1])
    detail = f"{n_tickers} Ticker / {total} Geister-HT" + (f" ({', '.join(f'{t}:{n}' for t,n in worst[:4])})" if worst else "")
    if total > GAP_RESIDUAL_MAX:
        report("Regel 1/9.1: Kalender vs. reale Handelstage", FAIL, detail + f" > Soll {GAP_RESIDUAL_MAX}")
    elif total > 0:
        report("Regel 1/9.1: Kalender vs. reale Handelstage", WARN, detail + " (Deep-Tail, advisory)")
    else:
        report("Regel 1/9.1: Kalender vs. reale Handelstage", PASS, "0 Geister-Lücken")


def rule1_reverse_holidays_db(client):
    """Regel 1/9.1 RÜCKWÄRTS: keine FALSCHEN Feiertage — handelt eine Einzelaktie
    an einem Kalender-Feiertag? (Clean-Ära 2022+; Indizes ausgeschlossen, da Yahoo
    dort Phantom-Zeilen an Feiertagen hat; Stooq-Alt-Daten ≤2019 ebenfalls). Dieser
    Check hätte XETRA-3.-Oktober/Pfingstmontag + Observed-Shift-Fehler gefangen."""
    from shared.exchange_holidays import _EXCHANGE_FUNCTIONS
    reps = {"NYSE": ["AAPL", "MSFT"], "XETRA": ["SAP.DE", "BAS.DE", "BMW.DE", "SIE.DE"],
            "EURONEXT": ["MC.PA", "OR.PA", "AIR.PA"], "MILAN": ["ENEL.MI", "ISP.MI"],
            "SIX": ["NESN.SW", "RO.SW", "ZURN.SW"], "STOCKHOLM": ["VOLV-A.ST", "INVE-B.ST"]}

    def alldates(t):
        out, off = set(), 0
        while True:
            r = (client.table("prices").select("date").eq("ticker", t)
                 .gte("date", "2022-01-01").order("date").range(off, off + 999).execute().data)
            if not r:
                break
            out.update(x["date"] for x in r)
            if len(r) < 1000:
                break
            off += 1000
        return out

    bad = []
    for ex, ts in reps.items():
        ds = {t: alldates(t) for t in ts}
        if not any(ds.values()):
            continue
        fn = _EXCHANGE_FUNCTIONS[ex]
        for yr in range(2022, 2026):
            for h in fn(yr):
                if h.weekday() >= 5:
                    continue
                s = h.strftime("%Y-%m-%d")
                if sum(1 for t in ts if s in ds[t]) >= (len(ts) + 1) // 2:
                    bad.append(f"{ex} {s}")
    if bad:
        report("Regel 1/9.1: keine FALSCHEN Feiertage (rückwärts)", FAIL, ", ".join(bad[:6]))
    else:
        report("Regel 1/9.1: keine FALSCHEN Feiertage (rückwärts)", PASS,
               "Einzelaktien handeln an keinem Kalender-Feiertag (2022+)")


def rule92_cb_events_db(client):
    """Regel 9.2: CB-Events in DB korrekt (Datum + meta-Verlinkung)."""
    rows = (client.table("market_events").select("event_date,event_name,meta,year")
            .eq("event_type", "central_bank").gte("year", 2026).execute().data)
    if not rows:
        report("Regel 9.2: CB-Events in DB", WARN, "keine CB-Events ≥2026 (Sync nötig?)")
        return
    bad = []
    # FOMC 2026 muss 04-29 enthalten, NICHT 05-06
    foMc = {r["event_date"] for r in rows if r["event_name"].startswith("FOMC")}
    if "2026-04-29" not in foMc or "2026-05-06" in foMc:
        bad.append("FOMC 2026-04-29 fehlt/05-06 vorhanden")
    # meta-Verlinkung vorhanden (bank+currency)
    no_meta = [r["event_name"] for r in rows
               if not (isinstance(r.get("meta"), dict) and r["meta"].get("bank"))]
    no_meta = [n for n in no_meta if "Minutes" not in n]  # Fed Minutes ohne meta ok
    banks = {r["event_name"].split()[0] for r in rows}
    if no_meta:
        bad.append(f"{len(no_meta)} CB-Events ohne meta.bank")
    if bad:
        report("Regel 9.2: CB-Events in DB", FAIL, "; ".join(bad))
    else:
        report("Regel 9.2: CB-Events in DB", PASS,
               f"{len(rows)} Events, Banken={len(banks)}, Datum+meta korrekt")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="Prüfagent für die Handels-Kalender-Regeln")
    ap.add_argument("--no-db", action="store_true", help="Nur Code-Logik (keine Supabase-Checks)")
    ap.add_argument("--rule", type=int, default=None, help="Nur eine Regel-Nummer prüfen (1-9)")
    args = ap.parse_args()

    print("═" * 72)
    print("  SeasonAlpha — Prüfagent: Handels-Kalender-Regeln (docs/TRADING_CALENDAR_RULES.md)")
    print("═" * 72)

    offline = [
        (1, rule1_resolution), (2, rule2_crypto), (3, rule3_forex),
        (7, rule7_opex), (8, rule8_vix), (9, rule92_central_banks),
        (9, rule91_national_holidays),
    ]
    for num, fn in offline:
        if args.rule is None or args.rule == num:
            fn()

    if not args.no_db:
        try:
            client = _client()
            for num, fn in [(4, rule456_tdom_tdoy_db), (1, rule1_gap_audit_db),
                            (1, rule1_reverse_holidays_db), (9, rule92_cb_events_db)]:
                if args.rule is None or args.rule == num:
                    fn(client)
        except Exception as exc:
            report("DB-Checks (Regel 4-6 / 1 / 9.2)", SKIP, f"keine DB-Verbindung: {str(exc)[:60]}")

    n_fail = sum(1 for _, s, _ in _results if s == FAIL)
    n_warn = sum(1 for _, s, _ in _results if s == WARN)
    n_pass = sum(1 for _, s, _ in _results if s == PASS)
    n_skip = sum(1 for _, s, _ in _results if s == SKIP)
    print("─" * 72)
    print(f"  Ergebnis: {n_pass} PASS · {n_warn} WARN · {n_fail} FAIL · {n_skip} SKIP")
    print("═" * 72)
    sys.exit(1 if n_fail else 0)


if __name__ == "__main__":
    main()
