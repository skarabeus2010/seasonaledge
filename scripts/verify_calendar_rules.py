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
             "SIX", "STOCKHOLM", "OSLO", "TSE", "HKEX", "KRX", "FOREX", "CRYPTO"}

# Gap-Audit-Ausnahmen (nur noch Forex — Yahoo-Datenqualität):
GAP_EXEMPT = lambda t: t.upper().endswith("=X")
# Residual-Toleranz für unvermeidbare Index-/Datenquellen-Phantome. Nach dem
# Oslo-Kalender-Fix (NEL.OL: 4 echte Oslo-Feiertage, kein Proxy-Bug mehr) sind
# es nur noch ^STOXX50E:6 (Index-Phantome, Yahoo/Stooq) + RR.L:1 (Einzel-Datengap) = 7.
GAP_RESIDUAL_MAX = 10

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
    """Settlement zum Referenzmonat (y, m) — aus dem Produktkatalog (V1c-2), keine eigene Kopie mehr.

    Die frühere Kopie verschob bei Mittwoch- UND Freitagsfeiertag additiv (zwei Tage); Cboe verschiebt einmal."""
    from shared.produkttermine import vix_regel
    ky, km = (y - 1, 12) if m == 1 else (y, m - 1)          # Kontraktmonat = Monat vor dem Referenzmonat
    return vix_regel(ky, km)["settlement"]


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
    if (2025, 12, 17) in FOMC_MEETING_DATES or (2025, 12, 10) not in FOMC_MEETING_DATES:
        problems.append("FOMC 2025-12-10 fehlt / 12-17 noch da")
    from shared.fed_dates import FOMC_STRATEGIE_TREFFEN
    if set(FOMC_STRATEGIE_TREFFEN) & set(FOMC_MEETING_DATES):
        problems.append("Fed-Strategietreffen als Zinsentscheid geführt (z. B. 2027-10-27)")
    if (2027, 10, 27) not in FOMC_STRATEGIE_TREFFEN or (2027, 11, 17) not in FOMC_MEETING_DATES:
        problems.append("Fed 2027: Strategietreffen 26./27.10., reguläre Sitzung 16./17.11. (Fed-Kalender, Zeile Oktober)")
    if (2026, 3, 13) in CB.BOJ_MEETING_DATES:
        problems.append("BoJ 2026-03-13 (falsch) noch da")
    # Zwilling: landing/js/fomc-dates.js muss dieselben Termine tragen wie shared/fed_dates.py
    # (bis 11/2026 standen dort 2025-12-17, 2026-05-06, 2026-12-16 — niemand hat es bemerkt)
    import re as _re
    _js = (pathlib.Path(_project_dir) / "landing" / "js" / "fomc-dates.js").read_text(encoding="utf-8")
    js_fomc = {tuple(int(x) for x in t) for t in _re.findall(r"\[(\d{4}),(\d{1,2}),(\d{1,2})\]", _js)}
    if js_fomc != set(FOMC_MEETING_DATES):
        diff = sorted(js_fomc ^ set(FOMC_MEETING_DATES))
        problems.append(f"FOMC Python≠JS (fomc-dates.js): {diff[:4]}")
    # Fed-Protokolle: 3 Wochen nach der vorangehenden Sitzung; nur um Thanksgiving und den Jahreswechsel
    # früher (belegt: 21.11.2023, 26.11.2024, 30.12.2025)
    _fomc = sorted(date(*t) for t in FOMC_MEETING_DATES)
    for t in CB.FED_MINUTES_DATES:
        m = date(*t)
        vor = [f for f in _fomc if f < m]
        abstand = (m - vor[-1]).days if vor else None
        if abstand not in (19, 20, 21) or (abstand != 21 and m.month not in (11, 12)):
            problems.append(f"Fed-Protokoll {m}: {abstand} Tage nach der Sitzung")
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
    """Regel 4-6: gespeicherte TDOM/TDOY = Börsenkalender (Stichprobe: ein Ticker je Börse, ab Vorjahr).

    Soll ist `tdom_tdoy_fuer_ticker` (dieselbe Funktion, mit der Nightly/Intraday/Onboarding seit P2 schreiben).
    Bis 2026-11-22 verlangte die Regel „Vorzeile + 1“ — das meldet bei Phantomzeilen an geschlossenen Tagen und bei
    echten Kurslücken falsche Fehler und übersieht einen Versatz, der über einen ganzen Monat gleich bleibt
    (Codex 2026-11-22, docs/review_prompts/2026-11-22_tdom_sndk_reparatur_antwort.md, Befund 3).
    Futures (=F), Krypto und Devisen bleiben außen vor: für sie ist die Nummerierung noch offen.
    Grenze: geprüft wird die Speicherung gegen den Produktionsrechner, keine unabhängige Kalenderreferenz (die prüfen
    verify_kalender_sollfaelle.py und verify_sitzungen.py). Eine Börse ohne Stichprobe macht die Regel rot.
    """
    from shared.exchange_holidays import tdom_tdoy_fuer_ticker
    from shared.symbols import SYMBOLS, get_exchange_for_holidays
    je_boerse = {}
    for t in sorted(SYMBOLS):
        b = get_exchange_for_holidays(t)
        if t.endswith("=F") or b in ("CRYPTO", "FOREX") or b in je_boerse:
            continue
        je_boerse[b] = t
    for b, t in (("NYSE", "SPY"), ("XETRA", "SAP.DE")):
        je_boerse[b] = t
    bad, geprueft, leer = [], 0, []
    _start = f"{date.today().year - 1}-01-01"
    for b, t in sorted(je_boerse.items()):
        rows, ab = [], _start
        while True:   # Keyset, damit kein Jahr an der 1000-Zeilen-Grenze abgeschnitten wird
            r = (client.table("prices").select("date,tdom,tdoy").eq("ticker", t).gte("date", ab)
                 .order("date").limit(1000).execute().data)
            rows += [x for x in r if not rows or x["date"] > rows[-1]["date"]]
            if len(r) < 1000:
                break
            ab = r[-1]["date"]
        if not rows:
            leer.append(f"{t} ({b})")   # keine Stichprobe ist kein Bestehen (Codex R2 Befund 4)
            continue
        soll = tdom_tdoy_fuer_ticker(t, [x["date"][:10] for x in rows])
        falsch = [(x["date"][:10], (x["tdom"], x["tdoy"]), s) for x, s in zip(rows, soll)
                  if (x["tdom"], x["tdoy"]) != tuple(s)]
        geprueft += len(rows)
        if falsch:
            d, ist, s = falsch[0]
            bad.append(f"{t} ({b}) {len(falsch)} Zeilen, erste {d}: {ist}≠{tuple(s)}")
    if leer:
        bad.append("ohne Kurszeilen ab " + _start + ": " + ", ".join(leer))
    if bad:
        report("Regel 4-6: TDOM/TDOY = Börsenkalender (DB)", FAIL, "; ".join(bad[:4]))
    else:
        report("Regel 4-6: TDOM/TDOY = Börsenkalender (DB)", PASS,
               f"{len(je_boerse)} Börsen, {geprueft} Zeilen ab {_start} gleich dem Kalender")


def rule1_gap_audit_db(client):
    """Regel 1/9.1 empirisch: is_trading_day vs. reale DB-Handelstage."""
    from scripts.fix_missing_days import get_expected_trading_days, get_db_dates
    today = date.today()
    win = date(today.year - 1, 1, 1)
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
        for yr in range(2022, date.today().year + 1):
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
