#!/usr/bin/env python3
"""verify_session_stamp.py — die Session-Stempelung der Options-Crons pruefen.

WARUM DIESER WAECHTER EXISTIERT (Vorfall 2026-09-25):
`_last_session()` gab den letzten Handelstag <= `date.today()` zurueck. Der Cron
steht auf 23:00 UTC, GitHub startet ihn aber mit ein bis zwei Stunden Verzug
(gemessen 00:44 bis 01:20 UTC). Nach Mitternacht UTC ist `today` der Folgetag —
ist der ein Handelstag, wurden Daten der abgelaufenen Session auf eine Session
gestempelt, die noch nicht gehandelt hatte. Der Frische-Waechter in
`compute_options_skew` verglich die Kursreihe (korrekt: Vortag) mit diesem
Stempel, fand die Abweichung und verzichtete auf die cm-Normierung — fuer JEDEN
Ticker. Ergebnis: 0 von 165 Tickern im Radar, `method` zurueck auf `provider`.

Der Fehler war NICHT im Waechter und nicht im Backfill, sondern im Stempel.

Aufruf: py -3.14 scripts/verify_session_stamp.py     (Exit 1 = Drift)
"""
from __future__ import annotations
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import scripts.compute_options_skew as m           # noqa: E402
import scripts.compute_options_flow as f           # noqa: E402
from shared.exchange_holidays import (letzte_session, is_trading_day,   # noqa: E402
                                     markt_offen, pruefe_eod_fenster, MarktOffen)

ET = ZoneInfo("America/New_York")

# (Beschreibung, UTC-Zeitpunkt des Laufs, erwartete Session)
# Der Kalender 2026: Do 24.09., Fr 25.09., Sa 26.09., Mo 28.09. sind echte Tage;
# der 25.12. ist NYSE-Feiertag (Freitag), der 24.12. ein verkuerzter Handelstag.
FAELLE = [
    ("Cron wie geplant, 23:00 UTC am Handelstag",
     datetime(2026, 9, 24, 23, 0, tzinfo=ZoneInfo("UTC")), "2026-09-24"),
    ("Cron mit Verzug, 01:00 UTC am Folgetag (DER VORFALL)",
     datetime(2026, 9, 25, 1, 0, tzinfo=ZoneInfo("UTC")), "2026-09-24"),
    ("Cron mit Verzug, 01:20 UTC nach Freitag -> bleibt Freitag",
     datetime(2026, 9, 26, 1, 20, tzinfo=ZoneInfo("UTC")), "2026-09-25"),
    ("Ad-hoc-Lauf vormittags (Session laeuft noch)",
     datetime(2026, 9, 25, 10, 30, tzinfo=ZoneInfo("UTC")), "2026-09-24"),
    ("Samstagslauf -> Freitag",
     datetime(2026, 9, 26, 18, 0, tzinfo=ZoneInfo("UTC")), "2026-09-25"),
    ("Sonntagslauf -> Freitag",
     datetime(2026, 9, 27, 18, 0, tzinfo=ZoneInfo("UTC")), "2026-09-25"),
    ("Montag 01:00 UTC -> Freitag, nicht Montag",
     datetime(2026, 9, 28, 1, 0, tzinfo=ZoneInfo("UTC")), "2026-09-25"),
    ("nach dem Schluss am Montag -> Montag",
     datetime(2026, 9, 28, 23, 0, tzinfo=ZoneInfo("UTC")), "2026-09-28"),
    ("Winterzeit: 21:30 UTC = 16:30 EST, nach Schluss",
     datetime(2026, 12, 1, 21, 30, tzinfo=ZoneInfo("UTC")), "2026-12-01"),
    ("Winterzeit: 20:30 UTC = 15:30 EST, VOR Schluss -> Vortag",
     datetime(2026, 12, 1, 20, 30, tzinfo=ZoneInfo("UTC")), "2026-11-30"),
    ("Feiertag 25.12. (Fr), Lauf 01:00 UTC danach -> 24.12.",
     datetime(2026, 12, 26, 1, 0, tzinfo=ZoneInfo("UTC")), "2026-12-24"),
]


def _mit_zeit(jetzt_utc: datetime) -> str:
    """Session zum gegebenen Laufzeitpunkt — ueber die gemeinsame Quelle."""
    return letzte_session("NYSE", jetzt=jetzt_utc).isoformat()


class _Falle(BaseException):
    """Wird geworfen, sobald ein gesperrter Lauf trotzdem Netz oder Platte berührt.

    BaseException, NICHT Exception: Produktivcode mit `except Exception` (z. B.
    `_spot`, `_enrich`) hätte eine Exception-Falle geschluckt, und der Wächter
    hätte einen Zugriff vor der Sperre nicht bemerkt (Codex-Review R4,
    reproduziert mit einem `_spot`-Aufruf vor der Sperre). Zusätzlich wird jeder
    Treffer protokolliert — auch einer, den jemand mit `except BaseException`
    abfängt.
    """


FALLEN_TREFFER: list[str] = []


def _falle(name):
    def _f(*a, **k):
        FALLEN_TREFFER.append(name)
        raise _Falle(name)
    return _f


def _synth_chain(spot: float = 700.0) -> list:
    """Kleine Chain im Massive-Format — genug, damit _records/_doi/_front laufen."""
    out = []
    for typ, delta in (("call", 0.5), ("put", -0.5)):
        for k in (690.0, 700.0, 710.0):
            out.append({"details": {"expiration_date": "2026-10-16", "contract_type": typ,
                                    "strike_price": k},
                        "open_interest": 1000, "implied_volatility": 0.2,
                        "greeks": {"gamma": 0.01, "delta": delta},
                        "day": {"volume": 10}, "underlying_asset": {"price": spot}})
    return out


def _pruefe_sperre_ausgefuehrt() -> int:
    import os
    import pathlib as _pl
    import shared.exchange_holidays as eh
    fehler = 0
    UTC = ZoneInfo("UTC")
    handel = datetime(2026, 9, 25, 14, 0, tzinfo=UTC)       # Fr 10:00 ET
    geschlossen = datetime(2026, 9, 25, 23, 0, tzinfo=UTC)  # Fr 19:00 ET

    echte_uhr = eh._uhr
    echter_key = os.environ.get("MASSIVE_API_KEY")
    echtes_write_text = _pl.Path.write_text
    gesichert = {}

    def _setze(mod, name, wert):
        if (mod, name) not in gesichert:
            gesichert[(mod, name)] = getattr(mod, name, None)
        setattr(mod, name, wert)

    def _main(mod, *args):
        alt = sys.argv
        sys.argv = [Path(mod.__file__).name, *args]
        try:
            return mod.main()
        except _Falle as e:
            return f"Falle {e}"
        finally:
            sys.argv = alt

    # Ohne Schlüssel überspringt build() die Ticker-Schleife — der Test wäre
    # dann stumm blind. Also immer einen setzen.
    os.environ["MASSIVE_API_KEY"] = "probe-kein-echter-schluessel"
    try:
        # ---- A) Handelszeit: build(write=True) muss VOR jedem Zugriff abbrechen
        print("  -- Handelszeit, Schreiblauf")
        eh._uhr = lambda tz: handel.astimezone(tz)
        for mod, namen in ((m, ["_index_series", "_enrich", "_get", "write_json_atomic"]),
                           (f, ["_spot", "_enrich", "_get", "_chain", "_save_hist", "_load_hist"])):
            for n in namen:
                if hasattr(mod, n):
                    _setze(mod, n, _falle(f"{Path(mod.__file__).name}:{n}"))
        _pl.Path.write_text = _falle("Path.write_text")
        for mod in (m, f):
            name = Path(mod.__file__).name
            FALLEN_TREFFER.clear()
            try:
                mod.build(["SPY"], write=True)
                ergebnis = "lief durch"
            except MarktOffen:
                ergebnis = "MarktOffen"
            except _Falle as e:
                ergebnis = f"erreichte {e}"
            ok = ergebnis == "MarktOffen" and not FALLEN_TREFFER
            if not ok:
                fehler += 1
            print(f"  {'OK  ' if ok else 'FAIL'} {name}: build(write=True) -> {ergebnis}"
                  f"{'' if not FALLEN_TREFFER else f', Zugriffe vor der Sperre: {FALLEN_TREFFER}'}")
            FALLEN_TREFFER.clear()
            rc = _main(mod)
            ok = rc == 2 and not FALLEN_TREFFER
            if not ok:
                fehler += 1
            print(f"  {'OK  ' if ok else 'FAIL'} {name}: main() -> Exit {rc}"
                  f"{'' if not FALLEN_TREFFER else f', Zugriffe: {FALLEN_TREFFER}'}")

        # ---- B) Echte Aufrufkette mit synthetischer Chain: --no-write darf
        #         NICHTS schreiben, ein Schreiblauf nach Schluss MUSS schreiben.
        #         Prüft main -> build -> _enrich -> _doi -> _save_hist am Stück;
        #         eine abgerissene write-Weitergabe an JEDER Stelle wird rot
        #         (R4: die direkte _doi-Probe übersah Brüche an den Aufrufstellen).
        print("  -- Aufrufkette mit synthetischer Chain")
        eh._uhr = lambda tz: geschlossen.astimezone(tz)
        geschrieben: list[str] = []
        _pl.Path.write_text = lambda self, *a, **k: geschrieben.append(str(self.name)) or 0
        _setze(f, "_spot", lambda sym, key: 700.0)
        _setze(f, "_chain", lambda sym, key, spot=None: _synth_chain(700.0))
        _setze(f, "_load_hist", lambda sym: [])
        _setze(f, "_enrich", gesichert[(f, "_enrich")])
        _setze(f, "_save_hist", gesichert[(f, "_save_hist")])
        for args, soll_schreibt in ((["--no-write", "--tickers", "SPY"], False),
                                    (["--tickers", "SPY"], True)):
            geschrieben.clear(); FALLEN_TREFFER.clear()
            rc = _main(f, *args)
            schreibt = bool(geschrieben)
            ok = (rc == 0 and schreibt == soll_schreibt and not FALLEN_TREFFER)
            if not ok:
                fehler += 1
            print(f"  {'OK  ' if ok else 'FAIL'} flow main {' '.join(args):<26} -> Exit {rc}, "
                  f"Schreibzugriffe {geschrieben or 'keine'}"
                  f"{'' if not FALLEN_TREFFER else f', Fallen: {FALLEN_TREFFER}'}")
    finally:
        eh._uhr = echte_uhr
        _pl.Path.write_text = echtes_write_text
        if echter_key is None:
            os.environ.pop("MASSIVE_API_KEY", None)
        else:
            os.environ["MASSIVE_API_KEY"] = echter_key
        for (mod, n), fn in gesichert.items():
            setattr(mod, n, fn)
    return fehler


def pruefe() -> int:
    fehler = 0
    print("Session-Stempel je Laufzeitpunkt\n" + "-" * 68)
    for name, jetzt, soll in FAELLE:
        ist = _mit_zeit(jetzt)
        ok = ist == soll
        if not ok:
            fehler += 1
        et = jetzt.astimezone(ET).strftime("%a %d.%m. %H:%M ET")
        print(f"  {'OK  ' if ok else 'FAIL'} {et} -> {ist}"
              f"{'' if ok else f'  ERWARTET {soll}'}   ({name})")

    # Explizit uebergebene Daten muessen reine Kalenderlogik behalten —
    # _fix_session_dates datiert damit Alt-Eintraege um.
    print("\nExplizites Datum (muss ohne Uhrzeit-Regel arbeiten)\n" + "-" * 68)
    for tag, soll in [(date(2026, 9, 26), "2026-09-25"),   # Sa -> Fr
                      (date(2026, 9, 25), "2026-09-25"),   # Fr -> Fr selbst
                      (date(2026, 12, 25), "2026-12-24")]:  # Feiertag -> Vortag
        ist = m._last_session(tag)
        ok = ist == soll
        if not ok:
            fehler += 1
        print(f"  {'OK  ' if ok else 'FAIL'} {tag} -> {ist}"
              f"{'' if ok else f'  ERWARTET {soll}'}")

    # MUTATIONSPROBE: die alte Logik (letzter Handelstag <= date.today(), ohne
    # Schlusszeit) muss von diesem Waechter erkannt werden. Ohne diese Probe ist
    # ein gruener Lauf eine Aussage ueber den Test, nicht ueber den Code.
    #
    # ERSTE FASSUNG WAR SELBST FALSCH (Codex-Review 2026-09-25): sie bildete
    # date.today() mit dem ET-Datum nach. Der Cron-Container laeuft aber in
    # UTC — und genau die UTC-Sicht erzeugt den Vorfall. Mit ET-Datum lieferte
    # die "alte Logik" um 01:00 UTC korrekt den 24.09., die Probe fing also den
    # dokumentierten Fall NICHT, und die "2 von 11" waren andere Faelle. Dazu
    # reichte irgendein Treffer fuer PASS. Jetzt: UTC-Datum wie im Container,
    # und der Vorfall selbst muss zwingend erkannt werden.
    print("\nMutationsprobe (alte Logik muss FAIL erzeugen)\n" + "-" * 68)
    def _alt(jetzt_utc: datetime) -> str:
        d = jetzt_utc.astimezone(ZoneInfo("UTC")).date()   # date.today() im UTC-Container
        for _ in range(10):
            if is_trading_day(d, "NYSE"):
                return d.isoformat()
            d -= timedelta(days=1)
        return d.isoformat()

    erkannt = [name for name, jetzt, soll in FAELLE if _alt(jetzt) != soll]
    print(f"  alte Logik scheitert an {len(erkannt)} von {len(FAELLE)} Faellen:")
    for name in erkannt:
        print(f"    - {name}")
    vorfall = [n for n, _, _ in FAELLE if "DER VORFALL" in n]
    if not vorfall or vorfall[0] not in erkannt:
        print("  FAIL: der dokumentierte Vorfall wird von der Probe NICHT erkannt")
        fehler += 1

    # Ersetzungsregel der Historie: rankbar ersetzt nicht-rankbar, sonst nichts.
    # Erste Fassung pruefte "cm_mode is not None" und liess damit eine
    # noatm-Zeile einen rankbaren Punkt blockieren (Codex-Review 2026-09-25).
    print("\nRankbarkeit wie im Frontend (skew.html::_isNorm)\n" + "-" * 68)
    for modus, soll in [("cm", True), ("cm_extrap", True), ("noatm", False),
                        ("single", False), (None, False)]:
        ist = m._rankbar({"cm_mode": modus})
        ok = ist == soll
        if not ok:
            fehler += 1
        print(f"  {'OK  ' if ok else 'FAIL'} cm_mode={modus!s:<10} -> rankbar={ist}")

    # Handelszeit-Sperre: waehrend der Session darf kein EOD-Job schreiben
    # (Snapshot intraday, Stempel = Vorsession). Codex-Review 2026-09-25, R2.
    print("\nHandelszeit-Sperre (markt_offen)\n" + "-" * 68)
    UTC = ZoneInfo("UTC")
    for name, jetzt, soll in [
        ("Fr 09:00 ET, vor Oeffnung",        datetime(2026, 9, 25, 13, 0, tzinfo=UTC), False),
        ("Fr 10:00 ET, Handel laeuft",       datetime(2026, 9, 25, 14, 0, tzinfo=UTC), True),
        ("Fr 16:10 ET, im Puffer",           datetime(2026, 9, 25, 20, 10, tzinfo=UTC), True),
        ("Fr 16:20 ET, nach Schluss",        datetime(2026, 9, 25, 20, 20, tzinfo=UTC), False),
        ("Cron 01:00 UTC",                   datetime(2026, 9, 25, 1, 0, tzinfo=UTC), False),
        ("Sa 11:00 ET",                      datetime(2026, 9, 26, 15, 0, tzinfo=UTC), False),
        ("Feiertag 25.12. 11:00 ET",         datetime(2026, 12, 25, 16, 0, tzinfo=UTC), False),
        ("Winter 15:00 EST, Handel laeuft",  datetime(2026, 12, 1, 20, 0, tzinfo=UTC), True),
    ]:
        ist = markt_offen("NYSE", jetzt)
        ok = ist == soll
        if not ok:
            fehler += 1
        print(f"  {'OK  ' if ok else 'FAIL'} {name:<34} -> offen={ist}"
              f"{'' if ok else f'  ERWARTET {soll}'}")
    try:
        pruefe_eod_fenster("probe", jetzt=datetime(2026, 9, 25, 14, 0, tzinfo=UTC))
        print("  FAIL pruefe_eod_fenster laesst einen Schreiblauf in der Handelszeit durch")
        fehler += 1
    except MarktOffen:
        print("  OK   pruefe_eod_fenster bricht in der Handelszeit ab")
    # Der Schutz muss im ERZEUGER wirken — und zwar nachweislich, nicht nur im
    # Quelltext. Erste Fassung suchte den Aufruf per Textsuche; eine
    # auskommentierte Zeile, `if False:` oder ein No-op-Import bestanden
    # trotzdem (Codex-Review 2026-09-25, R3). Jetzt: Uhr auf 10:00 ET festsetzen,
    # jeden Netz- und Schreibweg durch eine Falle ersetzen, build() und main()
    # wirklich laufen lassen. Erwartet: MarktOffen VOR der ersten Falle, Exit 2.
    fehler += _pruefe_sperre_ausgefuehrt()

    # Beide Options-Crons muessen DIESELBE Session sehen. Eine eigene Kopie der
    # Regel in einem der Skripte wuerde driften wie die zwei
    # Black-Scholes-Implementierungen mit verschiedenen Zinssaetzen.
    print("\nBeide Crons an derselben Quelle\n" + "-" * 68)
    gemeinsam = letzte_session("NYSE").isoformat()
    proben = [("compute_options_skew._last_session()", m._last_session(), gemeinsam),
              ("compute_options_flow nutzt shared",
               str("letzte_session" in Path(f.__file__).read_text(encoding="utf-8")), "True")]
    for name, ist, soll in proben:
        ok = ist == soll
        if not ok:
            fehler += 1
        print(f"  {'OK  ' if ok else 'FAIL'} {name}: {ist}"
              f"{'' if ok else f'  ERWARTET {soll}'}")

    print("\n" + ("ERGEBNIS: PASS" if fehler == 0 else f"ERGEBNIS: {fehler} FAIL"))
    return 1 if fehler else 0


if __name__ == "__main__":
    sys.exit(pruefe())
