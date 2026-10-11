"""Gemeinsame Produktionssperre (docs/KALENDER_UMSTELLUNG.md, Plan v4/v5, Code-Runde V1a R2).

Jeder Lauf, der kalenderrelevante Daten schreibt oder versendet (Kurse, Tagesnummern, Statistiken, Saison-Score,
Stress, Kalender-/Studienausgaben, Newsletter), läuft in `with produktion("<name>"):`. Die Sperre ist ein
GETEILTER `flock` auf einer Datei im vom Host gemounteten Log-Verzeichnis — sie überlebt Containerneustarts und
gilt für Timer, GitHub-Notauslöser und manuelle Starts gleichermaßen.

Aktivierung (V9): `aktivierung_setzen(kennung)` nimmt den EXKLUSIVEN `flock` (wartet, bis kein Lauf mehr hält),
schreibt die Marke `AKTIVIERUNG` und GIBT DEN LOCK SOFORT WIEDER FREI — die Marke allein sperrt; ein gehaltener
exklusiver Lock würde auch die Abnahmeläufe blockieren. Solange die Marke liegt:

1. `produktion(name)` beendet jeden Lauf vor jeder Arbeit mit Exit 75 und hinterlässt einen neutralen
   Betriebsnachweis (Zeile in `logs/sperre/unterdrueckt.log` + `refresh_log`-Zeile `run_type='produktionssperre'`,
   beides bestmöglich). Ausnahme: der Lauf trägt die Kennung in `SA_AKTIVIERUNG` UND steht mit seinem Modus in
   `AKTIVIERUNG_ERLAUBT`. Die Kennung wird danach aus der Umgebung entfernt (Kindprozesse erben sie nicht).
2. Import-Einstiege: jedes Pflicht-Skript ruft auf Modulebene `modul_sperre("<name>")`, wenn es nicht als
   `__main__` läuft — der Import scheitert bei Marke (Exit 75), und ein Prozess, der vorher importiert hat, hält
   den geteilten Lock bis zum Ende (`aktivierung_setzen` wartet auf ihn). `produktion()` ist wiedereintrittsfähig.
3. `schreibsperre(kanal)` / `pruefe_schreiben(kanal)` — der Supabase-Client prüft Schreibzugriffe auf
   `GESCHUETZTE_TABELLEN`/`GESCHUETZTE_RPC` beim Aufbau UND bei `.execute()` (dann unter dem geteilten Lock);
   vor jedem Newsletter-Versand ebenso. Eine vor der Aktivierung aufgebaute Anfrage schreibt danach nicht.

Ohne Marke ändert sich nichts: der Schreibschutz greift nur bei gesetzter Marke.
Ohne `fcntl` (Windows-Entwicklung) gibt es keinen Lock; die Marke wird trotzdem geprüft.
"""
from __future__ import annotations

import contextlib
import datetime as _dt
import os
import pathlib
import sys

try:
    import fcntl  # POSIX
except ImportError:  # pragma: no cover - Windows-Entwicklung
    fcntl = None

EXIT_GESPERRT = 75

# Was bei gesetzter Marke MIT Kennung laufen darf (Plan v5 §1): Name → (Pflichtargument oder None, darf schreiben).
# Alle anderen Läufe bleiben auch mit Kennung gesperrt. P5/P6 (Tagesnummern/Statistik neu schreiben) werden in
# ihrer Phase mit `schreiben=True` eingetragen; bis dahin schreibt während einer Aktivierung niemand.
# Newsletter: `--dry-run` rendert in eine Datei, kein Versand, kein refresh_log (v5 nannte es `--nur-rendern`).
AKTIVIERUNG_ERLAUBT = {
    "daily_newsletter": ("--dry-run", False),
    "weekly_newsletter": ("--dry-run", False),
    "build_calendar_data": ("--aktivierung", False),
}
ABNAHME_PRAEFIX = "abnahme:"          # Abnahmeproben: nur lesen, Name frei wählbar nach dem Präfix

# Tabellen/Funktionen, deren Inhalt von Tagesnummern, Sitzungen oder Kalendermethode abhängt.
GESCHUETZTE_TABELLEN = frozenset({
    "prices", "tdom_stats", "tdoy_stats", "monthly_stats", "seasonality", "scanner_results",
    "saison_score_protokoll", "stress_laeufe", "stress_scores", "market_events", "ki_scores",
})
GESCHUETZTE_RPC = frozenset({"stress_lauf_starten", "stress_lauf_veroeffentlichen", "stress_lauf_abbrechen"})

_freigabe: dict | None = None         # gesetzt von produktion(), wenn eine Kennung angenommen wurde


def sperr_verzeichnis() -> pathlib.Path:
    """`<Projekt>/logs/sperre` — im Container /app/logs/sperre, auf dem Host /opt/seasonaledge/logs/sperre: dasselbe
    Verzeichnis, weil ./logs in den Container gemountet ist. So sperren sich Läufe im Container und auf dem Host
    (build_calendar_data im Deploy) gegenseitig."""
    if os.environ.get("SA_SPERR_DIR"):
        return pathlib.Path(os.environ["SA_SPERR_DIR"])
    return pathlib.Path(__file__).resolve().parent.parent / "logs" / "sperre"


class Gesperrt(SystemExit):
    """Lauf wegen laufender Aktivierung nicht gestartet bzw. Schreibzugriff verweigert (Exit 75)."""

    def __init__(self, name: str):
        super().__init__(EXIT_GESPERRT)
        self.name = name


def _marke(verz: pathlib.Path) -> str | None:
    m = verz / "AKTIVIERUNG"
    try:
        return m.read_text(encoding="utf-8").strip() or "(leer)"
    except FileNotFoundError:
        return None


def _nachweis(verz: pathlib.Path, name: str, grund: str) -> None:
    """Neutraler Betriebsnachweis einer geplanten Unterdrückung. Darf nie selbst scheitern."""
    jetzt = _dt.datetime.now(_dt.timezone.utc)
    sys.stderr.write(f"[produktionssperre] {name}: {grund} — Exit {EXIT_GESPERRT}\n")
    try:
        with open(verz / "unterdrueckt.log", "a", encoding="utf-8") as f:
            f.write(f"{jetzt.isoformat(timespec='seconds')}\t{name}\t{grund}\n")
    except OSError:
        pass
    if os.environ.get("SA_SPERRE_KEIN_DB_NACHWEIS") == "1":     # Wächter/Tests
        return
    try:
        from shared.supabase_client import get_client
        get_client().table("refresh_log").insert({
            "run_date": jetzt.strftime("%Y-%m-%d"),
            "run_type": "produktionssperre",
            "tickers_total": 0, "tickers_success": 0, "tickers_missing": 0,
            "missing_details": '{"lauf": "%s", "grund": "%s"}' % (name, grund),
            "auto_fixed": 0, "duration_seconds": 0, "errors": "[]",
        }).execute()
    except Exception:  # noqa: BLE001 - Nachweis ist bestmöglich, der Exit 75 zählt
        pass


def _zugelassen(name: str) -> tuple[bool, bool]:
    """(darf trotz Marke laufen, darf schreiben) für einen Lauf mit passender Kennung."""
    if name.startswith(ABNAHME_PRAEFIX) and len(name) > len(ABNAHME_PRAEFIX):
        return True, False
    eintrag = AKTIVIERUNG_ERLAUBT.get(name)
    if eintrag is None:
        return False, False
    flag, schreiben = eintrag
    if flag is not None and flag not in sys.argv[1:]:
        return False, False
    return True, schreiben


_zustand: dict = {"tiefe": 0}         # Wiedereintritt: produktion() hält höchstens EINEN geteilten Lock
_dauer_fds: list = []                 # eigene Lock-Deskriptoren von modul_sperre(), offen bis Prozessende
_KENNUNG: list = []                   # SA_AKTIVIERUNG, einmal je Prozess gelesen (und aus der Umgebung entfernt)


def _kennung() -> str:
    """Die Aktivierungskennung dieses Prozesses. Beim ersten Aufruf aus der Umgebung ENTFERNT — Kindprozesse erben
    sie nicht —, danach aufbewahrt, damit spätere Eintritte (Import vor `__main__`) dieselbe Kennung sehen."""
    if not _KENNUNG:
        _KENNUNG.append(os.environ.pop("SA_AKTIVIERUNG", ""))
    return _KENNUNG[0]


def _sperren(name: str, kennung: str, verz: pathlib.Path) -> None:
    """Prüft die Marke für `name`. Setzt die Freigabe oder wirft `Gesperrt`. Aufruf nur unter dem geteilten Lock."""
    global _freigabe
    marke = _marke(verz)
    if marke is None:
        return
    if kennung != marke:
        _nachweis(verz, name, "Aktivierung läuft, keine passende Kennung")
        raise Gesperrt(name)
    darf, schreiben = _zugelassen(name)
    if not darf:
        _nachweis(verz, name, "Aktivierung läuft, Lauf/Modus nicht freigegeben")
        raise Gesperrt(name)
    if _freigabe is None:
        _freigabe = {"name": name, "kennung": kennung, "schreiben": schreiben}
    else:   # verschachtelt: Schreibrecht nur, wenn ALLE beteiligten Läufe es haben
        _freigabe = {**_freigabe, "schreiben": _freigabe["schreiben"] and schreiben}


@contextlib.contextmanager
def produktion(name: str):
    """Geteilte Produktionssperre für einen Lauf. Wirft `Gesperrt` (Exit 75), wenn eine Aktivierung läuft und dieser
    Lauf nicht (Kennung + erlaubter Lauf/Modus) zugelassen ist. Wiedereintrittsfähig: hält der Prozess den Lock
    schon (z. B. weil ein importiertes Pflicht-Modul ihn per `modul_sperre` genommen hat), wird nur der Name gegen
    die Freigabeliste geprüft."""
    global _freigabe
    verz = sperr_verzeichnis()
    if _zustand["tiefe"] > 0:
        _sperren(name, _kennung(), verz)
        _zustand["tiefe"] += 1
        try:
            yield
        finally:
            _zustand["tiefe"] -= 1
        return
    verz.mkdir(parents=True, exist_ok=True)
    fd = os.open(verz / "produktion.lock", os.O_RDWR | os.O_CREAT, 0o644)
    kennung = _kennung()
    try:
        if fcntl is not None:
            fcntl.flock(fd, fcntl.LOCK_SH)
        _sperren(name, kennung, verz)
        _zustand["tiefe"] = 1
        yield
    finally:
        _zustand["tiefe"] = 0
        _freigabe = None
        if fcntl is not None:
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
            except OSError:
                pass
        os.close(fd)


def modul_sperre(name: str) -> None:
    """Für Pflicht-Skripte, die IMPORTIERT werden (`from scripts.<x> import …`): nimmt den geteilten Lock auf einem
    EIGENEN Deskriptor und hält ihn bis zum Prozessende — unabhängig von `produktion()`-Blöcken, deren Ende den
    eigenen Lock freigibt (ein Import innerhalb eines äußeren Blocks verlor sonst seinen Lock mit dessen Ende).
    Bei gesetzter Marke scheitert schon der Import (Exit 75); ein Prozess, der vor der Aktivierung importiert hat,
    hält den Lock — `aktivierung_setzen` wartet auf ihn."""
    verz = sperr_verzeichnis()
    verz.mkdir(parents=True, exist_ok=True)
    dfd = os.open(verz / "produktion.lock", os.O_RDWR | os.O_CREAT, 0o644)
    try:
        if fcntl is not None:
            fcntl.flock(dfd, fcntl.LOCK_SH)
        _sperren(name, _kennung(), verz)
    except BaseException:
        os.close(dfd)
        raise
    _dauer_fds.append(dfd)     # nie geschlossen: das Betriebssystem gibt den Lock beim Prozessende frei


@contextlib.contextmanager
def schreibsperre(kanal: str):
    """Um eine einzelne Schreibausführung: hält der Prozess keinen Produktionslock, wird er für die Dauer der
    Ausführung geteilt genommen und die Marke darunter geprüft — eine vor der Aktivierung aufgebaute Anfrage kann
    nicht danach ausgeführt werden, und `aktivierung_setzen` wartet, bis sie fertig ist."""
    if _zustand["tiefe"] > 0 or _dauer_fds:     # Lock wird schon gehalten
        pruefe_schreiben(kanal)
        yield
        return
    verz = sperr_verzeichnis()
    verz.mkdir(parents=True, exist_ok=True)
    fd = os.open(verz / "produktion.lock", os.O_RDWR | os.O_CREAT, 0o644)
    try:
        if fcntl is not None:
            fcntl.flock(fd, fcntl.LOCK_SH)
        pruefe_schreiben(kanal)
        yield
    finally:
        if fcntl is not None:
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
            except OSError:
                pass
        os.close(fd)


def pruefe_schreiben(kanal: str) -> None:
    """Schreib-/Versandschutz unabhängig vom Einstieg. Ohne Marke: nichts. Mit Marke: nur ein Prozess, dem
    `produktion()` eine SCHREIBENDE Freigabe mit dieser Kennung erteilt hat, darf weiter."""
    verz = sperr_verzeichnis()
    marke = _marke(verz)
    if marke is None:
        return
    f = _freigabe
    if f is not None and f["schreiben"] and f["kennung"] == marke:
        return
    sys.stderr.write(f"[produktionssperre] Schreibzugriff {kanal} verweigert (Aktivierung läuft) — Exit {EXIT_GESPERRT}\n")
    raise Gesperrt(kanal)


def aktivierung_setzen(kennung: str, frist_s: float | None = None) -> None:
    """V9: wartet auf alle laufenden Produktionsläufe (exklusiver Lock), setzt die Marke und gibt den Lock wieder
    frei. Danach sperrt die Marke allein; Abnahmeläufe mit Kennung starten ohne zu warten. Mit `frist_s` wird
    nach Ablauf `TimeoutError` geworfen statt unbegrenzt zu warten (keine Marke gesetzt)."""
    import time
    if not kennung or kennung != kennung.strip():
        raise ValueError("Kennung leer oder mit Leerraum")
    verz = sperr_verzeichnis()
    verz.mkdir(parents=True, exist_ok=True)
    fd = os.open(verz / "produktion.lock", os.O_RDWR | os.O_CREAT, 0o644)
    try:
        if fcntl is not None:
            if frist_s is None:
                fcntl.flock(fd, fcntl.LOCK_EX)
            else:
                ende = time.monotonic() + frist_s
                while True:
                    try:
                        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                        break
                    except BlockingIOError:
                        if time.monotonic() >= ende:
                            raise TimeoutError("Produktionsläufe halten den Lock noch")
                        time.sleep(0.5)
        tmp = verz / "AKTIVIERUNG.tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(kennung + "\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, verz / "AKTIVIERUNG")
    finally:
        if fcntl is not None:
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
            except OSError:
                pass
        os.close(fd)


def aktivierung_aufheben(kennung: str) -> None:
    """Entfernt die Marke, wenn sie diese Kennung trägt (sonst ValueError — fremde Aktivierung)."""
    verz = sperr_verzeichnis()
    marke = _marke(verz)
    if marke is None:
        return
    if marke != kennung:
        raise ValueError("Marke trägt eine andere Kennung")
    (verz / "AKTIVIERUNG").unlink()


# ── Inventar: welche Skripte die Sperre tragen MÜSSEN, welche bewusst nicht ─────────────────────────────────────
# Der Wächter scripts/verify_produktionssperre.py verlangt: jedes Skript unter scripts/ mit einem Schreib- oder
# Versandaufruf steht in genau einer der beiden Listen; jedes PFLICHT-Skript betritt `produktion(` in main.
PFLICHT = {
    "nightly_refresh.py": "Kurse, Tagesnummern, Statistiken, Saison-Score",
    "intraday_refresh.py": "Kurse + Tagesnummern",
    "onboard_ticker.py": "Voll-Backfill neuer Ticker",
    "backfill_new_ticker.py": "Kurse + Tagesnummern (auch direkt aufrufbar)",
    "fix_missing_days.py": "Lückenfüller Kurse + Tagesnummern",
    "backfill_tdoy.py": "Tagesnummern",
    "backfill_log_return.py": "log_return (Rendite-Endpunkte)",
    "backfill_ohlc.py": "OHLC",
    "fix_ohlc_adjustment.py": "OHLC",
    "full_scanner_run.py": "Saison-Score + scanner_results",
    "compute_regime_scores.py": "Stress-Ampel",
    "daily_newsletter.py": "Versand mit Tagesnummern/Statistik",
    "weekly_newsletter.py": "Versand mit Tagesnummern/Statistik",
    "build_calendar_data.py": "Kalender-JSON/ICS",
    "build_flows_rebalancing.py": "Kalendertermine/HT-Countdowns",
    "build_index_effect.py": "Sitzungsfenster/Offsets",
    "build_wahlen.py": "Wahlfenster",
    "generate_decade_data.py": "Tagesnummern in Dekadendaten",
    "check_db_completeness.py": "repariert mit --fix (fix_missing_days)",
}
AUSNAHMEN = {
    "archive_front_straddle.py": "Options-Archiv, keine Tagesnummern/Kalendermethode",
    "backfill_skew_history.py": "stillgelegt (marketdata)",
    "backfill_skew_massive.py": "Options-Skew-Historie, keine Kalendermethode",
    "backfill_skew_report.py": "Bericht",
    "backfill_skew_vrp.py": "Options-VRP",
    "backtest_newsletter_scoring.py": "Forschung, schreibt nur Berichte",
    "build_boersenkalender_js.py": "erzeugt das Kalenderbundle selbst (Build, kein Lauf)",
    "build_buyback_blackout.py": "Flows-Panel ohne Handelstagnummern",
    "build_cot_positioning.py": "COT, wöchentliche Daten",
    "build_etf_flows.py": "ETF-Flows",
    "build_shortvol_proxy.py": "Vola-Proxy",
    "build_volcontrol_proxy.py": "Vola-Proxy",
    "compare_flashalpha_gex.py": "Vergleichswerkzeug",
    "compute_brier_stats.py": "Polymarket-Kalibrierung",
    "compute_gamma_exposure.py": "Options-GEX",
    "compute_iv_surface.py": "Options",
    "compute_key_levels.py": "Options",
    "compute_options_flow.py": "Options",
    "compute_options_skew.py": "Options",
    "congress_trades.py": "Congress-Filings + Alert (keine Kalendermethode)",
    "daily_health_check.py": "Überwachung, liest nur und mailt Admin",
    "data_audit.py": "Audit-Werkzeug",
    "export_ticker_regimes.py": "Export",
    "fetch_event_data.py": "Earnings/Dividenden-Ereignisse (Quelldaten)",
    "fix_log_returns_may2026.py": "einmalige historische Reparatur (abgeschlossen)",
    "generate_landing_chart.py": "Startseiten-Grafik",
    "generate_tickers_json.py": "Ticker-Liste",
    "polymarket_backfill.py": "Polymarket",
    "polymarket_discover.py": "Polymarket",
    "polymarket_refresh.py": "Polymarket",
    "polymarket_scrape_resolved.py": "Polymarket",
    "refresh_central_bank_dates.py": "Notenbanktermine (Quelldaten)",
    "render_gex_profile.py": "Options-Grafik",
    "seed_tickers.py": "Ticker-Stammdaten",
    "snapshot_gex.py": "Options",
    "snapshot_gex_massive.py": "Options",
    "test_supabase.py": "Verbindungstest",
    "upgrade_page_meta.py": "Seiten-Metadaten",
    "waechter_isolation.py": "Testhilfe",
    "wahlen_snapshot.py": "eingefrorener Artikel-Snapshot (Bestand)",
}
