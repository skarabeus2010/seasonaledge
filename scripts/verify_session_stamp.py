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

AUFBAU (nach fuenf Codex-Review-Runden):
  * Elternprozess: reine Rechenproben ohne jeden Schreibzugriff — Session-Tabelle,
    Mutationsprobe gegen die alte Logik, Handelszeit-Tabelle.
  * Unterprozess (`--isoliert`): alles, was `build()`/`main()` der Crons
    AUSFUEHRT. Dort ist `_ROOT` beider Crons auf ein Temp-Verzeichnis umgebogen,
    ein Audit-Hook meldet JEDEN Schreibzugriff ausserhalb — unabhaengig davon,
    ob per `open`, `write_text`, `mkdir` oder `os.replace` —, `.env` wird nicht
    geladen (SA_OHNE_DOTENV=1), kein Bytecode wird geschrieben. Was der
    Unterprozess an der Umgebung aendert, stirbt mit ihm.
  * Die Erzeuger werden unter ZWEI festen Uhren ausgefuehrt und der
    geschriebene Stempel geprueft. Ein Rueckfall auf `date.today()` liefert das
    echte Datum und kann nicht beide Erwartungen treffen (R5: der Waechter
    verglich die Crons vorher nur gegen die echte Uhr und blieb gruen, wenn man
    den Vorfall in die Crons zurueckbaute).

Aufruf: py -3.14 scripts/verify_session_stamp.py     (Exit 1 = Drift)
"""
from __future__ import annotations
import os
import sys

# VOR jedem shared-Import: keine echten Schluessel aus .env in diesen Prozess.
os.environ["SA_OHNE_DOTENV"] = "1"
sys.dont_write_bytecode = True

import json                                   # noqa: E402
import subprocess                             # noqa: E402
import tempfile                               # noqa: E402
from datetime import date, datetime, timedelta  # noqa: E402
from pathlib import Path                      # noqa: E402
from zoneinfo import ZoneInfo                 # noqa: E402

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from shared.exchange_holidays import (letzte_session, is_trading_day,   # noqa: E402
                                     markt_offen, pruefe_eod_fenster, MarktOffen)

ET = ZoneInfo("America/New_York")
UTC = ZoneInfo("UTC")

# (Beschreibung, UTC-Zeitpunkt des Laufs, erwartete Session)
# Der Kalender 2026: Do 24.09., Fr 25.09., Sa 26.09., Mo 28.09. sind echte Tage;
# der 25.12. ist NYSE-Feiertag (Freitag), der 24.12. ein verkuerzter Handelstag.
FAELLE = [
    ("Cron wie geplant, 23:00 UTC am Handelstag",
     datetime(2026, 9, 24, 23, 0, tzinfo=UTC), "2026-09-24"),
    ("Cron mit Verzug, 01:00 UTC am Folgetag (DER VORFALL)",
     datetime(2026, 9, 25, 1, 0, tzinfo=UTC), "2026-09-24"),
    ("Cron mit Verzug, 01:20 UTC nach Freitag -> bleibt Freitag",
     datetime(2026, 9, 26, 1, 20, tzinfo=UTC), "2026-09-25"),
    ("Ad-hoc-Lauf vormittags (Session laeuft noch)",
     datetime(2026, 9, 25, 10, 30, tzinfo=UTC), "2026-09-24"),
    ("Samstagslauf -> Freitag",
     datetime(2026, 9, 26, 18, 0, tzinfo=UTC), "2026-09-25"),
    ("Sonntagslauf -> Freitag",
     datetime(2026, 9, 27, 18, 0, tzinfo=UTC), "2026-09-25"),
    ("Montag 01:00 UTC -> Freitag, nicht Montag",
     datetime(2026, 9, 28, 1, 0, tzinfo=UTC), "2026-09-25"),
    ("nach dem Schluss am Montag -> Montag",
     datetime(2026, 9, 28, 23, 0, tzinfo=UTC), "2026-09-28"),
    ("Winterzeit: 21:30 UTC = 16:30 EST, nach Schluss",
     datetime(2026, 12, 1, 21, 30, tzinfo=UTC), "2026-12-01"),
    ("Winterzeit: 20:30 UTC = 15:30 EST, VOR Schluss -> Vortag",
     datetime(2026, 12, 1, 20, 30, tzinfo=UTC), "2026-11-30"),
    ("Feiertag 25.12. (Fr), Lauf 01:00 UTC danach -> 24.12.",
     datetime(2026, 12, 26, 1, 0, tzinfo=UTC), "2026-12-24"),
]

# Zwei Cron-Laeufe nach Mitternacht UTC mit VERSCHIEDENEN erwarteten Sessions.
# Ein Erzeuger, der auf date.today() zurueckfaellt, liefert das echte Datum und
# kann nicht beide treffen.
ERZEUGER_UHREN = [
    (datetime(2026, 9, 25, 1, 0, tzinfo=UTC), "2026-09-24"),   # der Vorfall
    (datetime(2026, 9, 29, 1, 0, tzinfo=UTC), "2026-09-28"),   # Montag-Session
]


# Jede ausfuehrende Probe traegt sich nach vollstaendigem Durchlauf hier ein.
# Der Elternprozess verlangt GENAU diese Menge — eine Bilanz ohne sie (Abbruch,
# vorzeitiges sys.exit, eine importierte Nebenwirkung, die eine gruene Zeile
# druckt) zaehlt als Fehler (Codex-Review R6).
PROBEN: list[str] = []
ERWARTETE_PROBEN = ("explizit", "rankbar", "handelszeit", "ohne_schluessel",
                    "kette", "stempel", "audit")


def _zeile(ok: bool, text: str) -> int:
    print(f"  {'OK  ' if ok else 'FAIL'} {text}")
    return 0 if ok else 1


# ══════════════════════════════════════════════════════════════════════════════
# Elternprozess: reine Rechenproben, kein Schreibzugriff, keine Cron-Module
# ══════════════════════════════════════════════════════════════════════════════
def _reine_proben() -> int:
    fehler = 0
    print("Session-Stempel je Laufzeitpunkt (shared.letzte_session)\n" + "-" * 68)
    for name, jetzt, soll in FAELLE:
        ist = letzte_session("NYSE", jetzt=jetzt).isoformat()
        et = jetzt.astimezone(ET).strftime("%a %d.%m. %H:%M ET")
        fehler += _zeile(ist == soll, f"{et} -> {ist}"
                         f"{'' if ist == soll else f'  ERWARTET {soll}'}   ({name})")

    # MUTATIONSPROBE: die alte Logik (letzter Handelstag <= date.today(), ohne
    # Schlusszeit) muss erkannt werden. Erste Fassung bildete date.today() mit
    # dem ET-Datum nach und fing den Vorfall NICHT (Codex R1) — der Container
    # laeuft in UTC. Jetzt UTC, und der Vorfall muss namentlich erkannt werden.
    print("\nMutationsprobe (alte Logik muss FAIL erzeugen)\n" + "-" * 68)
    def _alt(jetzt_utc: datetime) -> str:
        d = jetzt_utc.astimezone(UTC).date()
        for _ in range(10):
            if is_trading_day(d, "NYSE"):
                return d.isoformat()
            d -= timedelta(days=1)
        return d.isoformat()
    erkannt = [n for n, j, s in FAELLE if _alt(j) != s]
    print(f"  alte Logik scheitert an {len(erkannt)} von {len(FAELLE)} Faellen:")
    for n in erkannt:
        print(f"    - {n}")
    vorfall = next(n for n, _, _ in FAELLE if "DER VORFALL" in n)
    fehler += _zeile(vorfall in erkannt, "der dokumentierte Vorfall wird erkannt")

    print("\nHandelszeit-Sperre (markt_offen)\n" + "-" * 68)
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
        fehler += _zeile(ist == soll, f"{name:<34} -> offen={ist}"
                         f"{'' if ist == soll else f'  ERWARTET {soll}'}")
    try:
        pruefe_eod_fenster("probe", jetzt=datetime(2026, 9, 25, 14, 0, tzinfo=UTC))
        fehler += _zeile(False, "pruefe_eod_fenster laesst einen Schreiblauf durch")
    except MarktOffen:
        fehler += _zeile(True, "pruefe_eod_fenster bricht in der Handelszeit ab")
    return fehler


def _unterprozess() -> int:
    """Startet die ausfuehrenden Proben isoliert. Ein Unterprozess, der gar
    nicht erst laeuft oder keine Bilanz meldet, zaehlt als FEHLER — sonst waere
    ein blinder Lauf gruen (vier von fuenf "keine Freigabe" im Kern-Review
    waren solche Werkzeugfehler)."""
    import re
    import secrets
    print("\nAusfuehrende Proben (isolierter Unterprozess)\n" + "-" * 68)
    nonce = secrets.token_hex(16)
    with tempfile.TemporaryDirectory(prefix="sa_sessionprobe_") as tmp:
        env = {k: v for k, v in os.environ.items() if k != "MASSIVE_API_KEY"}
        env.update({"SA_OHNE_DOTENV": "1", "PYTHONDONTWRITEBYTECODE": "1",
                    "PYTHONUTF8": "1",
                    # build() ueberspringt ohne Schluessel die Ticker-Schleife —
                    # der Test waere dann stumm blind. Kein echter Schluessel.
                    "MASSIVE_API_KEY": "probe-kein-echter-schluessel",
                    "SA_PROBE_NONCE": nonce})
        r = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--isoliert", tmp],
                           cwd=tmp, env=env, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=600)
        ausgabe = [z for z in r.stdout.splitlines()
                   if "streamlit" not in z and "No runtime found" not in z]
        for z in ausgabe:
            if not z.startswith("ISOLIERT-BILANZ"):
                print(z)
        # GENAU eine Bilanzzeile, striktes Format, eigene Nonce, vollstaendige
        # Probenliste, Exit passend zur Fehlerzahl. Alles andere ist kein Beweis
        # (R6: "BILANZ 8" gefolgt von "BILANZ 0" wurde als 0 Fehler akzeptiert).
        bilanz = [z for z in r.stdout.splitlines() if z.startswith("ISOLIERT-BILANZ")]
        muster = re.compile(r"^ISOLIERT-BILANZ ([0-9a-f]{32}) (\d+) ([a-z_,]+)$")
        t = muster.match(bilanz[0]) if len(bilanz) == 1 else None
        n, grund = 0, None
        if len(bilanz) != 1:
            grund = f"{len(bilanz)} Bilanzzeilen statt genau einer"
        elif not t:
            grund = f"Bilanzzeile ohne gueltiges Format: {bilanz[0][:80]!r}"
        elif t.group(1) != nonce:
            grund = "Nonce stimmt nicht — die Zeile stammt nicht aus diesem Lauf"
        else:
            proben = t.group(3).split(",")
            n = int(t.group(2))
            if len(proben) != len(set(proben)) or set(proben) != set(ERWARTETE_PROBEN):
                grund = (f"Proben unvollstaendig/doppelt: fehlt "
                         f"{sorted(set(ERWARTETE_PROBEN) - set(proben))}, gemeldet {proben}")
            elif (n == 0) != (r.returncode == 0):
                grund = f"Bilanz {n} passt nicht zum Exit {r.returncode}"
        if grund:
            print(f"  FAIL {grund} (Exit {r.returncode}) — stderr:\n"
                  + "\n".join(r.stderr.splitlines()[-15:]))
            return 1
        return n


# ══════════════════════════════════════════════════════════════════════════════
# Unterprozess: fuehrt die Crons aus — isoliert
# ══════════════════════════════════════════════════════════════════════════════
class _Falle(BaseException):
    """Netzzugriff in einem Lauf, der keinen haben darf. BaseException, damit
    `except Exception` im Produktivcode sie nicht schluckt (R4); jeder Treffer
    wird ZUSAETZLICH protokolliert, falls jemand BaseException abfaengt."""


def _isoliert(tmp: str) -> int:
    tmp_p = Path(tmp).resolve()
    verstoesse: list[str] = []

    def _innen(pfad) -> bool:
        try:
            return Path(os.fsdecode(pfad)).resolve().is_relative_to(tmp_p)
        except Exception:
            return False

    _SCHREIB_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC

    def _audit(ereignis, args):
        vorher = len(verstoesse)
        _audit_pruefen(ereignis, args)
        if len(verstoesse) > vorher:
            # Nicht nur melden, sondern VERHINDERN: eine Mutation, die ins echte
            # Repo schreibt, darf im Test nichts anrichten. (In R3 hat genau so
            # eine Probe eine leere options_flow.json auf die Platte gelegt.)
            raise PermissionError(f"Waechter-Isolation: {verstoesse[-1]}")

    def _audit_pruefen(ereignis, args):
        if ereignis == "open":
            pfad, modus, flags = (list(args) + [None, None, None])[:3]
            if pfad is None or isinstance(pfad, int):
                return
            schreibt = (any(c in (modus or "") for c in "wax+")
                        or (modus is None and isinstance(flags, int) and flags & _SCHREIB_FLAGS))
            if schreibt and not _innen(pfad):
                verstoesse.append(f"open({os.fsdecode(pfad)}, {modus or flags})")
        elif ereignis in ("os.mkdir", "os.remove", "os.rmdir", "os.chmod", "os.truncate"):
            if args and not isinstance(args[0], int) and not _innen(args[0]):
                verstoesse.append(f"{ereignis}({os.fsdecode(args[0])})")
        elif ereignis == "os.rename":
            # BEIDE Seiten: auch "extern -> Temp-Baum" veraendert das echte Repo
            # (die Quelle verschwindet dort). R6.
            if len(args) >= 2 and not (_innen(args[0]) and _innen(args[1])):
                verstoesse.append(f"os.rename({os.fsdecode(args[0])} -> {os.fsdecode(args[1])})")
        elif ereignis in ("os.link", "os.symlink"):
            # Ein Hardlink/Symlink im Temp-Baum auf eine echte Datei macht jede
            # spaetere Schreiboperation "innen" zu einer aussen. Kein legitimer
            # Cron-Pfad braucht Links -> grundsaetzlich sperren. R6.
            verstoesse.append(f"{ereignis}{tuple(os.fsdecode(a) for a in args[:2] if not isinstance(a, int))}")

    # Hook VOR dem Import der Crons: auch Import-Nebenwirkungen zaehlen.
    sys.addaudithook(_audit)

    import shared.exchange_holidays as eh
    import scripts.compute_options_skew as m
    import scripts.compute_options_flow as f

    fehler = 0
    treffer: list[str] = []
    gesichert: dict = {}

    def _setze(mod, name, wert):
        if (mod, name) not in gesichert:
            gesichert[(mod, name)] = getattr(mod, name)
        setattr(mod, name, wert)

    def _falle(name):
        def _fn(*a, **k):
            treffer.append(name)
            raise _Falle(name)
        return _fn

    def _neue_wurzel(tag: str) -> Path:
        w = tmp_p / tag
        w.mkdir(parents=True, exist_ok=True)
        _setze(m, "_ROOT", w)
        _setze(f, "_ROOT", w)
        return w

    def _dateien(w: Path) -> list[str]:
        # ALLE Eintraege, nicht nur Dateien: ein angelegtes leeres Verzeichnis
        # ist in einem gesperrten Lauf genauso ein Verstoss (R6).
        return sorted(str(p.relative_to(w)).replace("\\", "/") + ("/" if p.is_dir() else "")
                      for p in w.rglob("*"))

    def _uhr(jetzt):
        eh._uhr = lambda tz: jetzt.astimezone(tz)

    def _main(mod, *args):
        alt = sys.argv
        sys.argv = [Path(mod.__file__).name, *args]
        try:
            return mod.main()
        except _Falle as e:
            return f"Falle {e}"
        finally:
            sys.argv = alt

    def _synth_chain(spot: float = 700.0) -> list:
        out = []
        for typ, delta in (("call", 0.5), ("put", -0.5)):
            for k in (690.0, 700.0, 710.0):
                out.append({"details": {"expiration_date": "2026-10-16", "contract_type": typ,
                                        "strike_price": k},
                            "open_interest": 1000, "implied_volatility": 0.2,
                            "greeks": {"gamma": 0.01, "delta": delta},
                            "day": {"volume": 10}, "underlying_asset": {"price": spot}})
        return out

    def _synth_skew(sym, key=None):
        return {"ticker": sym, "cats": ["Broad-Index"], "underlying": 700.0, "dte": 21,
                "put_vol": 100, "call_vol": 100, "put_oi": 1000, "call_oi": 1000,
                "call_25d": {"strike": 720, "iv": 0.19, "delta": 0.25},
                "put_25d": {"strike": 680, "iv": 0.22, "delta": -0.25},
                "skew_pts": 3.0, "call_zeta_pts": -1.0, "put_zeta_pts": 2.0,
                "iv_atm": 0.20, "vrp_pts": 2.0, "bfly_pts": 0.5, "pc_ratio": 1.15,
                "contango": True, "rv_1m": 0.18,
                "cm_mode": "cm", "cm_dte": 30, "cm_skew_pts": 3.0, "cm_put_iv": 0.22,
                "cm_call_iv": 0.19, "cm_iv_atm": 0.20, "cm_bfly_pts": 0.5,
                "cm_call_zeta_pts": -1.0, "cm_put_zeta_pts": 2.0}

    echte_uhr = eh._uhr
    try:
        # -- 1) explizites Datum: reine Kalenderlogik (fuer _fix_session_dates)
        print("  -- explizites Datum in _last_session(d)")
        for tag, soll in [(date(2026, 9, 26), "2026-09-25"), (date(2026, 9, 25), "2026-09-25"),
                          (date(2026, 12, 25), "2026-12-24")]:
            ist = m._last_session(tag)
            fehler += _zeile(ist == soll, f"{tag} -> {ist}{'' if ist == soll else f'  ERWARTET {soll}'}")

        PROBEN.append("explizit")

        # -- 2) Rankbarkeit exakt wie skew.html::_isNorm
        print("  -- Rankbarkeit (cm/cm_extrap, NICHT noatm/single)")
        for modus, soll in [("cm", True), ("cm_extrap", True), ("noatm", False),
                            ("single", False), (None, False)]:
            ist = m._rankbar({"cm_mode": modus})
            fehler += _zeile(ist == soll, f"cm_mode={modus!s:<10} -> rankbar={ist}")

        PROBEN.append("rankbar")

        # -- 3) Handelszeit: Schreiblauf muss VOR jedem Zugriff abbrechen
        print("  -- Handelszeit (Fr 10:00 ET), Schreiblauf")
        _uhr(datetime(2026, 9, 25, 14, 0, tzinfo=UTC))
        for mod, namen in ((m, ["_index_series", "_enrich", "_get"]),
                           (f, ["_spot", "_enrich", "_get", "_chain"])):
            for n in namen:
                _setze(mod, n, _falle(f"{Path(mod.__file__).name}:{n}"))
        for mod in (m, f):
            name = Path(mod.__file__).name
            w = _neue_wurzel(f"handel_{name}")
            treffer.clear()
            try:
                mod.build(["SPY"], write=True)
                erg = "lief durch"
            except MarktOffen:
                erg = "MarktOffen"
            except _Falle as e:
                erg = f"erreichte {e}"
            ok = erg == "MarktOffen" and not treffer and not _dateien(w)
            fehler += _zeile(ok, f"{name}: build(write=True) -> {erg}"
                             f"{'' if not treffer else f', Zugriffe {treffer}'}"
                             f"{'' if not _dateien(w) else f', Dateien {_dateien(w)}'}")
            treffer.clear()
            rc = _main(mod)
            fehler += _zeile(rc == 2 and not treffer and not _dateien(w),
                             f"{name}: main() -> Exit {rc}")

        PROBEN.append("handelszeit")

        # -- 3b) Schreiblauf OHNE Schluessel: frueher entstand eine Ausgabe ohne
        #        Ticker mit Exit 0 (beim Skew-Cron: leerer Radar). R6.
        print("  -- Schreiblauf ohne MASSIVE_API_KEY (nach Schluss)")
        _uhr(datetime(2026, 9, 25, 23, 0, tzinfo=UTC))
        schluessel = {k: os.environ.pop(k) for k in ("MASSIVE_API_KEY", "POLYGON_API_KEY")
                      if k in os.environ}
        try:
            for mod in (m, f):
                name = Path(mod.__file__).name
                w = _neue_wurzel(f"ohneschluessel_{name}")
                treffer.clear()
                rc = _main(mod, "--tickers", "SPY")
                d = _dateien(w)
                fehler += _zeile(rc == 3 and not d and not treffer,
                                 f"{name}: main() ohne Schluessel -> Exit {rc}, Eintraege {d or 'keine'}")
        finally:
            os.environ.update(schluessel)
        PROBEN.append("ohne_schluessel")

        # -- 4) echte Aufrufkette Flow: --no-write schreibt nichts, Schreiblauf schon
        print("  -- Flow-Aufrufkette nach Schluss (synthetische Chain)")
        _uhr(datetime(2026, 9, 25, 23, 0, tzinfo=UTC))
        _setze(f, "_spot", lambda sym, key: 700.0)
        _setze(f, "_chain", lambda sym, key, spot=None: _synth_chain(700.0))
        _setze(f, "_enrich", gesichert[(f, "_enrich")])
        for args, soll_dateien in ((["--no-write", "--tickers", "SPY"], False),
                                   (["--tickers", "SPY"], True)):
            w = _neue_wurzel("kette_" + ("nowrite" if "--no-write" in args else "write"))
            treffer.clear()
            rc = _main(f, *args)
            d = _dateien(w)
            ok = rc == 0 and bool(d) == soll_dateien and not treffer
            fehler += _zeile(ok, f"flow main {' '.join(args):<26} -> Exit {rc}, "
                             f"Dateien {d or 'keine'}")

        PROBEN.append("kette")

        # -- 5) ERZEUGER-STEMPEL unter zwei festen Uhren (R5)
        print("  -- Erzeuger-Stempel unter fester Uhr (Rueckfall auf date.today() muss auffallen)")
        _setze(m, "_enrich", _synth_skew)
        _setze(m, "_index_series", lambda *a, **k: None)
        for uhr, soll in ERZEUGER_UHREN:
            _uhr(uhr)
            lauf = uhr.strftime("%d.%m. %H:%M UTC")
            # Restlaufzeiten gegen die Session, nicht gegen date.today(). Die
            # Stempelprobe unten ersetzt _enrich und erreicht _byexp deshalb nie —
            # ein Rueckfall der Skew-dte auf date.today() blieb im ersten
            # Mutationslauf unbemerkt (M10). Also _byexp direkt ausfuehren.
            dte_soll = (date(2026, 10, 16) - date.fromisoformat(soll)).days
            dte_ist = m._byexp(_synth_chain()).get("2026-10-16", {}).get("dte")
            fehler += _zeile(dte_ist == dte_soll,
                             f"skew  {lauf}: _byexp dte     = {dte_ist}"
                             f"{'' if dte_ist == dte_soll else f'  ERWARTET {dte_soll}'}")
            dte_flow = (f._records(_synth_chain(), soll) or [{}])[0].get("dte")
            fehler += _zeile(dte_flow == dte_soll,
                             f"flow  {lauf}: _records dte   = {dte_flow}"
                             f"{'' if dte_flow == dte_soll else f'  ERWARTET {dte_soll}'}")
            # Skew
            w = _neue_wurzel(f"stempel_skew_{soll}")
            treffer.clear()
            try:
                m.build(["SPY"], write=True)
                out = json.loads((w / "landing/data/options_skew.json").read_text(encoding="utf-8"))
                hist = json.loads((w / "landing/data/options_skew_history.json").read_text(encoding="utf-8"))
                gefunden = {"session": out.get("session"),
                            "History SPY": (hist.get("SPY") or [{}])[-1].get("date"),
                            "History __PCR": (hist.get("__PCR") or [{}])[-1].get("date")}
            except (Exception, _Falle) as e:
                gefunden = {"Lauf": f"{type(e).__name__}: {e}"}
            for feld, ist in gefunden.items():
                fehler += _zeile(ist == soll and not treffer,
                                 f"skew  {lauf}: {feld:<14} = {ist}"
                                 f"{'' if ist == soll else f'  ERWARTET {soll}'}")
            # Flow
            w = _neue_wurzel(f"stempel_flow_{soll}")
            treffer.clear()
            rc = _main(f, "--tickers", "SPY")
            try:
                out = json.loads((w / "landing/data/options_flow.json").read_text(encoding="utf-8"))
                oi = json.loads((w / "landing/data/oi_history/SPY.json").read_text(encoding="utf-8"))
                gefunden = {"session": out.get("session"), "OI-History SPY": oi[-1].get("date")}
            except Exception as e:
                gefunden = {"Lauf": f"Exit {rc}, {type(e).__name__}: {e}"}
            for feld, ist in gefunden.items():
                fehler += _zeile(ist == soll and not treffer,
                                 f"flow  {lauf}: {feld:<14} = {ist}"
                                 f"{'' if ist == soll else f'  ERWARTET {soll}'}")
        PROBEN.append("stempel")
    finally:
        eh._uhr = echte_uhr
        for (mod, n), fn in gesichert.items():
            setattr(mod, n, fn)

    # -- Bilanz des Audit-Hooks: jeder Schreibzugriff ausserhalb des Temp-Baums
    print("  -- Schreibzugriffe ausserhalb des Temp-Verzeichnisses (Audit-Hook)")
    fehler += _zeile(not verstoesse, f"{len(verstoesse)} gefunden")
    for v in verstoesse[:10]:
        print(f"       {v}")
    PROBEN.append("audit")
    return fehler


def pruefe() -> int:
    fehler = _reine_proben()
    fehler += _unterprozess()
    print("\n" + ("ERGEBNIS: PASS" if fehler == 0 else f"ERGEBNIS: {fehler} FAIL"))
    return 1 if fehler else 0


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--isoliert":
        nonce = os.environ.pop("SA_PROBE_NONCE", "")   # fuer spaetere Importe unsichtbar
        n = _isoliert(sys.argv[2])
        print(f"ISOLIERT-BILANZ {nonce} {n} {','.join(PROBEN)}", flush=True)
        sys.exit(1 if n else 0)
    sys.exit(pruefe())
