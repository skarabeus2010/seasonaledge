# -*- coding: utf-8 -*-
"""Wächter für den Live-Versand des Daily Morning Briefings auf dem systemd-Timer (2026-10-12, Codex-Prüfung
docs/review_prompts/2026-10-12_briefing_timer.md).

    py -3.14 scripts/verify_briefing_versand.py

Prüft die WIRKUNG, nicht den Wortlaut: `scripts/daily_newsletter.main()` läuft echt, nur Datenaufbau, Empfängerliste,
Mailversand und refresh_log sind durch Attrappen ersetzt (Versandsperre in einem Temp-Verzeichnis per SA_VERSAND_VERZ).

  [Sperre]     shared/versandsperre.py: Berliner Datum, fertig/abgebrochen/Wiederaufnahme, Hash statt Adresse,
               paralleler Lauf (nur unter Linux — unter Windows gibt es kein flock; dort UNGEPRÜFT, im Gate läuft Linux)
  [Versand]    main(): Abbruch mitten im Versand → kein blinder Neustart, Wiederaufnahme ohne Doppelte, zweiter Lauf
               nach Abschluss versendet nichts, Test-/Einzelversand unberührt und mit eigenem Modus im refresh_log
  [Health]     Check 5c zählt nur Live-Läufe und hat die 10:00-Frist
  [Betrieb]    Timer/Unit/Installer/Workflow: kein GitHub-Zeitplan mehr, Timer in Berliner Zeit, Timeout im Container

Ein Absturz einer Prüfung ist kein Nachweis: er erscheint als `[Absturz]`.
"""
from __future__ import annotations

import importlib
import json
import os
import pathlib
import re
import sys
import tempfile
import traceback
import types
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

WURZEL = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL))

FEHLER: list[str] = []
ZAEHLER = {"n": 0}
UNGEPRUEFT: list[str] = []
BERLIN = ZoneInfo("Europe/Berlin")


def pruefe(kennung, bedingung, text=""):
    ZAEHLER["n"] += 1
    if not bedingung:
        FEHLER.append("%s %s" % (kennung, text))


def absturz(name):
    FEHLER.append("[Absturz] %s: %s" % (name, traceback.format_exc(limit=3).strip().splitlines()[-1]))


# ── [Sperre] ─────────────────────────────────────────────────────────────────────────────────────────────────────
def sperre(verz: pathlib.Path):
    os.environ["SA_VERSAND_VERZ"] = str(verz)
    from shared import versandsperre as vs
    importlib.reload(vs)
    spaet = datetime(2026, 10, 12, 22, 30, tzinfo=timezone.utc)   # 00:30 Berlin am 13.10.
    v = vs.Versand("probe", jetzt=spaet)
    pruefe("[Sperre]", v.datum == "2026-10-13", "Datum nicht nach Berliner Zeit: %s" % v.datum)
    pruefe("[Sperre]", v.uebrige(["a@x.de", "B@x.de"]) == ["a@x.de", "B@x.de"], "frischer Versand filtert")
    v.notieren("A@X.de ")
    pruefe("[Sperre]", v.uebrige(["a@x.de", "b@x.de"]) == ["b@x.de"], "bediente Adresse (Groß/Klein, Leerzeichen) erneut")
    f = verz / ("probe_%s.gesendet" % v.datum)
    roh = f.read_text(encoding="utf-8") if f.exists() else ""
    pruefe("[Sperre]", "@" not in roh and roh.strip() == "+ " + vs.kennung("a@x.de"), "Adresse statt Hash auf Platte")
    v.schliessen()
    try:
        vs.Versand("probe", jetzt=spaet)
        pruefe("[Sperre]", False, "abgebrochener Versand startet ohne Wiederaufnahme")
    except vs.VersandGesperrt as e:
        pruefe("[Sperre]", e.grund == "abgebrochen", "falscher Grund %s" % e.grund)
    w = vs.Versand("probe", wiederaufnahme=True, jetzt=spaet)
    pruefe("[Sperre]", w.uebrige(["a@x.de", "c@x.de"]) == ["c@x.de"], "Wiederaufnahme kennt die Bedienten nicht")
    w.notieren("c@x.de")
    w.abschliessen(1, 0)
    w.schliessen()
    for wa in (False, True):
        try:
            vs.Versand("probe", wiederaufnahme=wa, jetzt=spaet)
            pruefe("[Sperre]", False, "abgeschlossener Versand startet erneut (wiederaufnahme=%s)" % wa)
        except vs.VersandGesperrt as e:
            pruefe("[Sperre]", e.grund == "schon_versandt", "falscher Grund %s" % e.grund)
    andert = vs.Versand("probe", jetzt=datetime(2026, 10, 13, 22, 30, tzinfo=timezone.utc))
    pruefe("[Sperre]", andert.datum == "2026-10-14", "Folgetag nicht frei")
    andert.schliessen()
    for falsch in (dict(jetzt=datetime(2026, 10, 12, 8, 0)), dict(wiederaufnahme="ja")):
        try:
            vs.Versand("probe2", **falsch)
            pruefe("[Sperre]", False, "ungültige Eingabe angenommen: %r" % falsch)
        except TypeError:
            pruefe("[Sperre]", True)
    if vs.fcntl is None:
        UNGEPRUEFT.append("paralleler Live-Lauf (kein flock unter Windows)")
    else:
        halt = vs.Versand("parallel", jetzt=spaet)
        try:
            vs.Versand("parallel", wiederaufnahme=True, jetzt=spaet)
            pruefe("[Sperre]", False, "zweiter gleichzeitiger Live-Lauf nicht gesperrt")
        except vs.VersandGesperrt as e:
            pruefe("[Sperre]", e.grund == "parallel", "falscher Grund %s" % e.grund)
        finally:
            halt.schliessen()


# ── [Versand] — main() echt, Umgebung als Attrappe ────────────────────────────────────────────────────────────────
class Welt:
    def __init__(self):
        self.gesendet: list[str] = []      # vom Mailanbieter ANGENOMMEN
        self.alerts: list[str] = []
        self.logs: list[dict] = []
        self.abbruch_vor: str | None = None    # Lauf endet im Versandaufruf, BEVOR der Anbieter annimmt
        self.abbruch_nach: str | None = None   # Anbieter hat angenommen, Lauf endet vor dem Journaleintrag
        self.ablehnen: set[str] = set()        # Anbieter lehnt ab (Ergebnis "abgelehnt")
        self.unklar: set[str] = set()          # Anbieter nimmt an, die Antwort geht verloren (Ergebnis "unklar")
        self.empfaenger = ["eins@x.de", "zwei@x.de", "drei@x.de"]


def newsletter_laden(welt: Welt):
    def mod(name, **attrs):
        m = types.ModuleType(name)
        m.__dict__.update(attrs)
        sys.modules[name] = m
        return m

    class _Log:
        def __getattr__(self, _):
            return lambda *a, **k: None

    mod("shared.produktionssperre", modul_sperre=lambda *a, **k: None, pruefe_schreiben=lambda *a, **k: None,
        produktion=None)
    mod("shared.daily_report", DEFAULT_N_ETFS=5, DEFAULT_N_STOCKS=5,
        build_daily_context=lambda **k: {"etfs": [1], "stocks": [1], "events": [], "target_display": "x"})
    mod("shared.logger", app_logger=_Log(), error_logger=_Log())
    mod("shared.supabase_client", fetch_scanner_results=lambda: [])

    def send_html_ergebnis(email, subject, html):
        if welt.abbruch_vor == email:
            raise SystemExit(137)   # wie SIGKILL beim Container-Neubau, vor der Annahme
        if email in welt.ablehnen:
            return "abgelehnt"
        welt.gesendet.append(email)
        if welt.abbruch_nach == email:
            raise SystemExit(137)   # angenommen, aber der Lauf endet vor dem Journaleintrag
        if email in welt.unklar:
            return "unklar"         # angenommen, Antwort verloren (Lese-Timeout)
        return "angenommen"

    mod("shared.email_brevo", send_html_ergebnis=send_html_ergebnis, send_admin_alert=lambda t: welt.alerts.append(t),
        ANGENOMMEN="angenommen", ABGELEHNT="abgelehnt", UNKLAR="unklar")
    sys.modules.pop("scripts.daily_newsletter", None)
    dn = importlib.import_module("scripts.daily_newsletter")
    dn._get_active_daily_subscribers = lambda: list(welt.empfaenger)
    dn.render_email = lambda ctx, email, cache: ("Betreff", "<html></html>")
    dn._write_refresh_log = lambda el, s, f, fe, modus: welt.logs.append({"sent": s, "failed": f, "modus": modus})
    dn.SEND_RATE_LIMIT_SEC = 0
    dn.time.sleep = lambda *_: None
    return dn


OFFEN: list = []   # Versand-Objekte der laufenden Probe — ein "getöteter" Lauf gibt seine Sperre wie beim Prozessende frei


def starte(dn, *argv):
    import contextlib
    import io
    alt = sys.argv
    sys.argv = ["daily_newsletter.py", *argv]
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            return dn.main()
    except SystemExit as e:
        return ("abbruch", e.code)
    except OSError as e:   # Journal-Schreibfehler: der Lauf endet mit der Ausnahme
        return ("ausnahme", type(e).__name__)
    finally:
        for v in OFFEN:   # wie beim Prozessende: der Kernel gibt flock und Deskriptoren frei, der Status bleibt
            try:
                v.schliessen()
            except OSError:
                pass
        OFFEN.clear()
        sys.argv = alt


def versand(verz: pathlib.Path):
    import shared.versandsperre as vs
    importlib.reload(vs)
    _echt = vs.Versand

    class _Beobachtet(_echt):
        journal_fehler = False

        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            OFFEN.append(self)

        def notieren(self, email):
            if _Beobachtet.journal_fehler:
                raise OSError("Platte voll (Probe)")
            super().notieren(email)

    vs.Versand = _Beobachtet
    welt = Welt()
    dn = newsletter_laden(welt)

    # 1) Abbruch NACH der Annahme von zwei@ (vor dem Journaleintrag)
    os.environ["SA_VERSAND_VERZ"] = str(verz / "nach_annahme")
    welt.abbruch_nach = "zwei@x.de"
    rc = starte(dn)
    pruefe("[Versand]", rc == ("abbruch", 137) and welt.gesendet == ["eins@x.de", "zwei@x.de"],
           "Abbruch-Szenario: %r %r" % (rc, welt.gesendet))
    welt.abbruch_nach = None

    welt.gesendet.clear()
    rc = starte(dn)
    pruefe("[Versand]", rc not in (0, None) and welt.gesendet == [],
           "abgebrochener Versand wird blind wiederholt: rc=%r gesendet=%r" % (rc, welt.gesendet))
    pruefe("[Versand]", len(welt.alerts) == 1, "kein Admin-Alarm beim abgebrochenen Versand")

    welt.gesendet.clear()
    rc = starte(dn, "--wiederaufnahme")
    pruefe("[Versand]", rc == 0 and welt.gesendet == ["drei@x.de"],
           "Wiederaufnahme: rc=%r gesendet=%r (eins@ angenommen, zwei@ ungeklärt — beide nicht erneut)" % (rc, welt.gesendet))
    pruefe("[Versand]", len(welt.alerts) == 2 and "1 Empfänger" in welt.alerts[-1],
           "Wiederaufnahme meldet den ungeklärten Empfänger nicht: %r" % welt.alerts[1:])
    pruefe("[Versand]", welt.logs[-1:] == [{"sent": 1, "failed": 0, "modus": "live"}], "Live-Lauf ohne modus=live im refresh_log")

    welt.gesendet.clear()
    n_logs = len(welt.logs)
    for argv in ((), ("--wiederaufnahme",)):
        rc = starte(dn, *argv)
        pruefe("[Versand]", rc == 0 and welt.gesendet == [],
               "zweiter Lauf nach Abschluss versendet (%r): rc=%r %r" % (argv, rc, welt.gesendet))
    pruefe("[Versand]", len(welt.logs) == n_logs, "Lauf ohne Versand schreibt einen Live-Eintrag ins refresh_log")

    rc = starte(dn, "--test")
    pruefe("[Versand]", rc == 0 and len(welt.gesendet) == 1 and welt.logs[-1:] == [{"sent": 1, "failed": 0, "modus": "test"}],
           "Testversand gesperrt oder ohne modus=test: rc=%r %r %r" % (rc, welt.gesendet, welt.logs[-1:]))
    rc = starte(dn, "--to", "z@x.de")
    pruefe("[Versand]", rc == 0 and welt.gesendet[-1:] == ["z@x.de"] and welt.logs[-1:] == [{"sent": 1, "failed": 0, "modus": "einzel"}],
           "Einzelversand gesperrt oder ohne modus=einzel")
    rc = starte(dn, "--test", "--wiederaufnahme")
    pruefe("[Versand]", rc not in (0, None), "--wiederaufnahme außerhalb des Live-Versands angenommen")

    # 2) Abgelehnt = eindeutig nicht versandt → Wiederaufnahme versucht es erneut; Abbruch VOR der Annahme = ungeklärt
    os.environ["SA_VERSAND_VERZ"] = str(verz / "abgelehnt")
    welt.gesendet.clear()
    welt.ablehnen, welt.abbruch_vor = {"eins@x.de"}, "drei@x.de"
    rc = starte(dn)
    pruefe("[Versand]", rc == ("abbruch", 137) and welt.gesendet == ["zwei@x.de"], "Ablehnungs-Szenario: %r %r" % (rc, welt.gesendet))
    welt.ablehnen, welt.abbruch_vor = set(), None
    welt.gesendet.clear()
    welt.abbruch_nach = "eins@x.de"   # zweiter Versuch: angenommen, Lauf endet vor dem Journaleintrag → ? - ?
    rc = starte(dn, "--wiederaufnahme")
    welt.abbruch_nach = None
    pruefe("[Versand]", rc == ("abbruch", 137) and welt.gesendet == ["eins@x.de"],
           "abgelehnter Empfänger nicht erneut versucht oder ungeklärter erneut versandt: rc=%r %r" % (rc, welt.gesendet))
    welt.gesendet.clear()
    rc = starte(dn, "--wiederaufnahme")
    pruefe("[Versand]", rc == 0 and welt.gesendet == [],
           "Journalfolge ? - ? (alte Ablehnung, neuer ungeklärter Versuch) erneut versandt: rc=%r %r" % (rc, welt.gesendet))

    # 2b) unklarer Ausgang des Mailadapters (Annahme, Antwort verloren) bleibt ungeklärt
    os.environ["SA_VERSAND_VERZ"] = str(verz / "unklar")
    welt.gesendet.clear()
    welt.unklar, welt.abbruch_vor = {"eins@x.de"}, "drei@x.de"
    rc = starte(dn)
    welt.unklar, welt.abbruch_vor = set(), None
    pruefe("[Versand]", rc == ("abbruch", 137) and welt.gesendet == ["eins@x.de", "zwei@x.de"], "Unklar-Szenario: %r %r" % (rc, welt.gesendet))
    welt.gesendet.clear()
    rc = starte(dn, "--wiederaufnahme")
    pruefe("[Versand]", rc == 0 and welt.gesendet == [],
           "unklarer Ausgang wie eine Ablehnung behandelt (erneut versandt): rc=%r %r" % (rc, welt.gesendet))

    # 3) Journal-Schreibfehler nach der Annahme: kein gewöhnlicher Versandfehler, der Lauf endet
    os.environ["SA_VERSAND_VERZ"] = str(verz / "journal")
    welt.gesendet.clear()
    n_logs = len(welt.logs)
    _Beobachtet.journal_fehler = True
    try:
        rc = starte(dn)
    finally:
        _Beobachtet.journal_fehler = False
    pruefe("[Versand]", rc == ("ausnahme", "OSError") and welt.gesendet == ["eins@x.de"] and len(welt.logs) == n_logs,
           "Journalfehler als Versandfehler weitergezählt: rc=%r gesendet=%r" % (rc, welt.gesendet))
    rc = starte(dn)
    pruefe("[Versand]", rc not in (0, None) and welt.gesendet == ["eins@x.de"], "nach Journalfehler blind weiterversandt")

    if vs.fcntl is None:
        UNGEPRUEFT.append("paralleler Live-Lauf über main() (kein flock unter Windows)")
    else:
        os.environ["SA_VERSAND_VERZ"] = str(verz / "parallel")
        welt.gesendet.clear()
        halt = _echt("daily_newsletter")
        try:
            rc = starte(dn)
            pruefe("[Versand]", rc not in (0, None) and welt.gesendet == [],
                   "paralleler Live-Lauf versendet: rc=%r %r" % (rc, welt.gesendet))
        finally:
            halt.schliessen()

    for m in ("shared.produktionssperre", "shared.daily_report", "shared.logger", "shared.supabase_client",
              "shared.email_brevo", "scripts.daily_newsletter"):
        sys.modules.pop(m, None)


# ── [Adapter] — shared/email_brevo.send_html_ergebnis echt, nur requests.post ersetzt ───────────────────────────
def adapter():
    import requests
    for m in ("shared.email_brevo", "shared.logger"):
        sys.modules.pop(m, None)
    eb = importlib.import_module("shared.email_brevo")

    class _Antwort:
        def __init__(self, status):
            self.status_code, self.text = status, "{}"

        def raise_for_status(self):
            if self.status_code >= 400:
                raise requests.HTTPError("HTTP %d" % self.status_code)

        def json(self):
            return {"messageId": "x"}

    def post_mit(wirkung):
        def post(*a, **k):
            if isinstance(wirkung, BaseException):
                raise wirkung
            return _Antwort(wirkung)
        return post

    import contextlib
    import io
    alt_post, alt_key = eb.requests.post, eb.BREVO_API_KEY
    eb.BREVO_API_KEY = "probe"
    try:
        for name, wirkung, soll in (("201", 201, "angenommen"), ("302", 302, "unklar"), ("101", 101, "unklar"),
                                    ("400", 400, "abgelehnt"), ("502", 502, "unklar"),
                                    ("Lese-Timeout", requests.ReadTimeout("t"), "unklar"),
                                    ("Verbindungsaufbau", requests.ConnectTimeout("t"), "abgelehnt"),
                                    ("Verbindungsabbruch", requests.ConnectionError("t"), "unklar")):
            eb.requests.post = post_mit(wirkung)
            with contextlib.redirect_stdout(io.StringIO()):
                ist = eb.send_html_ergebnis("a@x.de", "B", "<p/>")
                alt = eb.send_html("a@x.de", "B", "<p/>")
            pruefe("[Adapter]", ist == soll, "%s → %r statt %r" % (name, ist, soll))
            pruefe("[Adapter]", alt is (soll == "angenommen"), "send_html %s → %r" % (name, alt))
        eb.BREVO_API_KEY = ""
        os.environ.pop("BREVO_API_KEY", None)
        with contextlib.redirect_stdout(io.StringIO()):
            pruefe("[Adapter]", eb.send_html_ergebnis("a@x.de", "B", "<p/>") == "abgelehnt", "ohne Schlüssel nicht abgelehnt")
    finally:
        eb.requests.post, eb.BREVO_API_KEY = alt_post, alt_key
        sys.modules.pop("shared.email_brevo", None)


# ── [Health] ─────────────────────────────────────────────────────────────────────────────────────────────────────
class _Kette:
    """Attrappe des Supabase-Clients: daily_newsletter-Zeilen aus `zeilen`, jede andere Abfrage leer."""

    def __init__(self, zeilen):
        self.zeilen, self.filter = zeilen, {}

    def table(self, name):
        k = _Kette(self.zeilen)
        k.filter = {"table": name}
        return k

    def eq(self, spalte, wert):
        self.filter[spalte] = wert
        return self

    def execute(self):
        treffer = self.filter.get("table") == "refresh_log" and self.filter.get("run_type") == "daily_newsletter"
        return types.SimpleNamespace(data=list(self.zeilen) if treffer else [], count=0)

    def __getattr__(self, _):
        return lambda *a, **k: self


def check_5c(hc, zeilen, jetzt):
    """Führt collect_health_data() echt aus (Client-Attrappe, feste Uhr) und gibt den Check „Daily Newsletter“."""
    import contextlib
    import io

    class _Uhr(datetime):
        @classmethod
        def now(cls, tz=None):
            return jetzt.astimezone(tz) if tz else jetzt.replace(tzinfo=None)

    alt_dt = hc.datetime
    sys.modules["shared.supabase_client"] = types.SimpleNamespace(get_client=lambda: _Kette(zeilen))
    hc.datetime = _Uhr
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            ctx = hc.collect_health_data()
    finally:
        hc.datetime = alt_dt
        sys.modules.pop("shared.supabase_client", None)
    return next((c for c in ctx["checks"] if c["name"] == "Daily Newsletter"), None)


def health():
    hc = importlib.import_module("scripts.daily_health_check")
    z = lambda modus=None, ts="2026-10-12T05:31:00+00:00": {   # noqa: E731
        "created_at": ts, "run_date": ts[:10], "tickers_success": 3, "tickers_total": 3,
        "missing_details": json.dumps({} if modus is None else {"modus": modus})}
    pruefe("[Health]", hc._newsletter_modus(z()) == "live", "Altzeile ohne Modus nicht als live gezählt")
    pruefe("[Health]", hc._newsletter_modus(z("test")) == "test", "Testzeile als live gezählt")
    pruefe("[Health]", hc._newsletter_modus({"missing_details": None}) == "live", "leere Details nicht live")
    mo_11 = datetime(2026, 10, 12, 9, 0, tzinfo=timezone.utc)      # Mo 11:00 Berlin
    mo_09 = datetime(2026, 10, 12, 7, 0, tzinfo=timezone.utc)      # Mo 09:00 Berlin
    sa_11 = datetime(2026, 10, 17, 9, 0, tzinfo=timezone.utc)
    pruefe("[Health]", hc._newsletter_frist_verpasst([z()], mo_11) is False, "heutiger Live-Lauf als verpasst")
    pruefe("[Health]", hc._newsletter_frist_verpasst([z(ts="2026-10-09T05:31:00+00:00")], mo_11) is True,
           "Freitagslauf deckt Montag nach 10:00")
    pruefe("[Health]", hc._newsletter_frist_verpasst([], mo_11) is True, "kein Lauf nach 10:00 nicht rot")
    pruefe("[Health]", hc._newsletter_frist_verpasst([], mo_09) is False, "Frist vor 10:00 schon rot")
    pruefe("[Health]", hc._newsletter_frist_verpasst([], sa_11) is False, "Frist am Wochenende")
    # 22:30 UTC am Sonntag = Montag 00:30 Berlin: zählt als Montagslauf (Berliner Datum, nicht UTC-Datum)
    pruefe("[Health]", hc._newsletter_frist_verpasst([z(ts="2026-10-11T22:30:00+00:00")], mo_11) is False,
           "Datum nicht nach Berliner Zeit verglichen")

    # Check 5c über collect_health_data() — die Wirkung, nicht der Wortlaut
    test_heute, live_fr = z("test", "2026-10-12T08:00:00+00:00"), z("live", "2026-10-09T05:31:00+00:00")
    faelle = [
        ("nur Testzeile heute, nach 10:00", [test_heute, live_fr], mo_11, "red"),
        ("gar keine Zeile, nach 10:00", [], mo_11, "red"),
        ("nur Testzeilen, nach 10:00", [test_heute], mo_11, "red"),
        ("Live heute, nach 10:00", [z("live")], mo_11, "green"),
        ("gar keine Zeile, vor 10:00", [], mo_09, "yellow"),
    ]
    for name, zeilen, jetzt, soll in faelle:
        c = check_5c(hc, zeilen, jetzt)
        pruefe("[Health]", c is not None and c["status"] == soll,
               "Check 5c %s: %s statt %s" % (name, c and c["status"], soll))

    # Fristprüfung (sa-briefing-frist.timer): Alarm genau bei Verstoß
    for name, zeilen, jetzt, soll_rc in (("nur Test heute", [test_heute], mo_11, 1), ("leer", [], mo_11, 1),
                                         ("Live heute", [z("live")], mo_11, 0), ("vor der Frist", [], mo_09, 0),
                                         ("Wochenende", [], sa_11, 0)):
        alarme = []
        import contextlib
        import io
        with contextlib.redirect_stdout(io.StringIO()):
            rc = hc.briefing_frist(_Kette(zeilen), jetzt, alarme.append)
        pruefe("[Health]", rc == soll_rc and len(alarme) == soll_rc,
               "Fristprüfung %s: rc=%r Alarme=%d (soll %d)" % (name, rc, len(alarme), soll_rc))


# ── [Betrieb] ────────────────────────────────────────────────────────────────────────────────────────────────────
def betrieb():
    sd = WURZEL / "deploy" / "systemd"
    t = (sd / "sa-daily-briefing.timer").read_text(encoding="utf-8")
    s = (sd / "sa-daily-briefing.service").read_text(encoding="utf-8")
    pruefe("[Betrieb]", re.search(r"(?m)^OnCalendar=Mon\.\.Fri \*-\*-\* 07:30:00 Europe/Berlin\s*$", t) is not None,
           "Timer nicht Mo–Fr 07:30 Berliner Zeit")
    pruefe("[Betrieb]", re.search(r"(?m)^Unit=sa-daily-briefing\.service\s*$", t) is not None, "Timer startet falsche Unit")
    m = re.search(r"(?m)^ExecStart=/usr/bin/docker exec seasonalpha-app timeout --kill-after=\d+s (\d+)m python3 -u "
                  r"scripts/daily_newsletter\.py\s*$", s)
    ts = re.search(r"(?m)^TimeoutStartSec=(\d+)min\s*$", s)
    pruefe("[Betrieb]", m is not None, "ExecStart nicht live-Versand mit Timeout im Container")
    pruefe("[Betrieb]", m is not None and ts is not None and int(ts.group(1)) > int(m.group(1)),
           "äußeres Limit nicht über dem Timeout im Container")
    pruefe("[Betrieb]", re.search(r"(?m)^SuccessExitStatus=75\s*$", s) is not None, "Exit 75 nicht als Erfolg")
    it = (WURZEL / "deploy" / "install_timers.sh").read_text(encoding="utf-8")
    pruefe("[Betrieb]", "sa-daily-briefing.service" in it and "sa-daily-briefing.timer" in it,
           "install_timers.sh installiert den Briefing-Timer nicht")
    wf = (WURZEL / ".github" / "workflows" / "daily_newsletter.yml").read_text(encoding="utf-8")
    pruefe("[Betrieb]", re.search(r"(?m)^\s*schedule\s*:", wf) is None and re.search(r"(?m)^\s*-?\s*cron\s*:", wf) is None,
           "daily_newsletter.yml hat noch einen GitHub-Zeitplan (Doppelversand)")
    pruefe("[Betrieb]", re.search(r"(?m)^\s*workflow_dispatch\s*:", wf) is not None, "Notauslöser fehlt")
    ft = (sd / "sa-briefing-frist.timer").read_text(encoding="utf-8")
    fs = (sd / "sa-briefing-frist.service").read_text(encoding="utf-8")
    pruefe("[Betrieb]", re.search(r"(?m)^OnCalendar=Mon\.\.Fri \*-\*-\* 10:(\d\d):00 Europe/Berlin\s*$", ft) is not None,
           "Fristprüfung nicht Mo–Fr nach 10:00 Berliner Zeit")
    pruefe("[Betrieb]", re.search(r"(?m)^ExecStart=/usr/bin/docker exec seasonalpha-app timeout --kill-after=\d+s \d+m "
                                  r"python3 -u scripts/daily_health_check\.py --briefing-frist\s*$", fs) is not None,
           "Fristprüfung startet nicht --briefing-frist mit Timeout im Container")
    pruefe("[Betrieb]", "sa-briefing-frist.service" in it and "sa-briefing-frist.timer" in it,
           "install_timers.sh installiert die Fristprüfung nicht")


def main():
    with tempfile.TemporaryDirectory(prefix="sa_versand_", ignore_cleanup_errors=True) as tmp:
        for name, fn, arg in (("Sperre", sperre, pathlib.Path(tmp) / "a"), ("Versand", versand, pathlib.Path(tmp) / "b"),
                              ("Adapter", adapter, None), ("Health", health, None), ("Betrieb", betrieb, None)):
            try:
                fn(arg) if arg is not None else fn()
            except Exception:
                absturz(name)
    for f in FEHLER:
        print("FEHL", f)
    for u in UNGEPRUEFT:
        print("UNGEPRÜFT", u)
    print("verify_briefing_versand: %d/%d Prüfungen bestanden%s" % (
        ZAEHLER["n"] - len([f for f in FEHLER if not f.startswith("[Absturz]")]), ZAEHLER["n"],
        "" if not UNGEPRUEFT else " (%d ungeprüft — nur unter Linux prüfbar)" % len(UNGEPRUEFT)))
    if UNGEPRUEFT and "--streng" in sys.argv:
        return 1
    return 1 if FEHLER else 0


if __name__ == "__main__":
    sys.exit(main())
