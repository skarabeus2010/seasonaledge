#!/usr/bin/env python3
"""
verify_gex_spot.py — Spot-Regel und Kettenvertrag des GEX-Snapshots.

Anlass: der GEX-Workflow war seit dem 15.10.2026 fuenf Naechte rot. Yahoo liefert den
Tagesbalken der Session etwa 00:00-01:10 UTC mit `close = null` (gemessen, Proben
/root/yahoo_abend: 16.10. 22:15 UTC 763.25, 17.10. 00:15 und 00:45 UTC null, 02:00 UTC
wieder 763.25), `_spot` laeuft VOR der Chain, also fiel jeder Ticker aus. Der verspaetete
GitHub-Cron traf genau dorthin.

Geprueft werden die ECHTEN Funktionen aus snapshot_gex_massive und gex_kette; ersetzt sind
nur Netz (`_fetch_yahoo`, `_get`) und Uhr (`exchange_holidays._uhr`). Entwurf und
Freigabe: docs/review_prompts/2026-10-21_gex_abendluecke_entwurf_v5.md (Codex-Freigabe
nach vier Entwurfsrunden, zwei Auflagen).

Die Fixtures der Yahoo-Antworten sind den ECHTEN Probe-Antworten nachgebildet, nicht
erfunden: Zeitstempel 09:30 New York fuer den Tagesbalken, `regularMarketTime` auf dem
Sessionschluss, und fuer das Loch derselbe Satz mit `close = null`.

Exit 0 gruen, 1 rot, 3 Absturz (kein Nachweis).
"""
from __future__ import annotations

import contextlib
import io
import json
import math
import os
import shutil
import stat
import sys
import tempfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.dont_write_bytecode = True
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "scripts"))
_TMP = Path(tempfile.mkdtemp(prefix="sa_gexspot_"))
# VOR jedem Produktionsimport: eigenes Sperrverzeichnis, keine .env, Probeschluessel.
# Ohne das lief dieser Waechter gegen die echte .env und das echte logs/sperre — und
# im CI ohne .env waeren die Ganzlaufpruefungen rot gewesen (Codex C1, am Code belegt:
# die lokale .env hat einen echten MASSIVE_API_KEY, der CI-Checkout nicht).
os.environ["SA_SPERR_DIR"] = str(_TMP / "sperre")
os.environ["SA_OHNE_DOTENV"] = "1"
os.environ["MASSIVE_API_KEY"] = "probe-kein-echter-schluessel"


def _absturz(typ, wert, tb):
    """Ein Absturz ist KEIN Nachweis: Exit 3, damit der Mutationstest ihn als
    ungueltig zaehlt statt als gefangenen Fehler."""
    import traceback
    traceback.print_exception(typ, wert, tb)
    print("[Absturz]")
    shutil.rmtree(_TMP, ignore_errors=True)
    os._exit(3)


sys.excepthook = _absturz

# streamlit nur ersetzen, wenn es fehlt (Muster aus verify_gex_session.py:54).
# shared/yahoo_downloader importiert es wegen st.cache_data; der Gate-Runner hat es
# nicht installiert, der App-Container schon. Ohne das schlaegt der Gate-Schritt mit
# ModuleNotFoundError fehl — genau daran war der Deploy von e7e881f rot.
try:
    import streamlit  # noqa: F401
except ImportError:
    import types

    def _cache_data(*a, **k):
        def deko(f):
            f.clear = lambda: None
            return f
        return deko(a[0]) if a and callable(a[0]) else deko

    sys.modules["streamlit"] = types.SimpleNamespace(cache_data=_cache_data)
    # ... und dasselbe als DATEI fuer Kindprozesse: die Faelle mit echtem Unterprozess
    # (Sperreintritt) starten scripts/snapshot_gex_massive.py neu, und dort gilt die
    # Attrappe aus sys.modules nicht. Ohne das scheitert der Kindprozess am Import und
    # meldet Exit 1 statt der erwarteten 75.
    _STUB = _TMP / "stub"
    _STUB.mkdir(parents=True, exist_ok=True)
    (_STUB / "streamlit.py").write_text(
        "def cache_data(*a, **k):\n"
        "    def deko(f):\n"
        "        f.clear = lambda: None\n"
        "        return f\n"
        "    return deko(a[0]) if a and callable(a[0]) else deko\n",
        encoding="utf-8")
    os.environ["PYTHONPATH"] = (str(_STUB) + os.pathsep
                                + os.environ.get("PYTHONPATH", "")).rstrip(os.pathsep)

NY = ZoneInfo("America/New_York")
UTC = ZoneInfo("UTC")
FEHLER: list[str] = []
UEBERSPRUNGEN: list[str] = []
S = date(2026, 10, 16)                      # Freitag, voller Handelstag
HALBTAG = date(2026, 11, 27)                # Tag nach Thanksgiving, NYSE-Halbtag 13:00 (belegt)
WINTER = date(2026, 11, 20)                 # Freitag NACH der Zeitumstellung (01.11.2026)


ANZAHL = [0]


def pruef(name, ok, info=""):
    ANZAHL[0] += 1
    print(f"  {'ok  ' if ok else 'FAIL'} {name}" + (f"  ->  {info}" if info else ""))
    if not ok:
        FEHLER.append(name)


def _ruhig(fn, *a, **k):
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return fn(*a, **k)


def _ruhig_mit_ausgabe(fn, *a, **k):
    puffer = io.StringIO()
    with contextlib.redirect_stdout(puffer), contextlib.redirect_stderr(puffer):
        erg = fn(*a, **k)
    return erg, puffer.getvalue()


import snapshot_gex_massive as gm                                        # noqa: E402

# Die ECHTE Lader-Funktion beim Import sichern: die Spot-Faelle ersetzen gm._get durch
# eine Attrappe und stellen sie nicht zurueck. Fall 8 braucht den Produktionspfad, sonst
# prueft er die Attrappe und meldet 0 Versuche.
_GET_ECHT = gm._get
from shared import exchange_holidays as eh                               # noqa: E402


def _uhr(jetzt):
    eh._uhr = lambda tz: jetzt.astimezone(tz)


def _schluss_ny(session: date) -> datetime:
    """Sessionschluss UNABHAENGIG vom Produktivcode festgelegt: 16:00 New York, am
    belegten Halbtag 27.11.2026 um 13:00. Bewusst nicht ueber gm._sessionschluss — ein
    Test, der seinen Sollwert aus der zu pruefenden Funktion zieht, prueft nichts."""
    hh = 13 if session == HALBTAG else 16
    return datetime(session.year, session.month, session.day, hh, 0, tzinfo=NY)


# ── Yahoo-Fixtures ────────────────────────────────────────────────────────────────────
def yahoo_antwort(session: date, *, kurs=700.0, rmt: datetime | None = None,
                  balken_datum: date | None = None, doppelt=False,
                  laengen_bruch=False, ohne_meta=False, kaputt=False):
    """Yahoo-Chart-Antwort wie die echte: Tagesbalken 09:30 New York, close/adjclose
    parallel, regularMarketTime in meta."""
    if kaputt:
        return {"chart": {"result": []}}
    tag = balken_datum or session
    ts = [int(datetime(d.year, d.month, d.day, 9, 30, tzinfo=NY).timestamp())
          for d in (tag - timedelta(days=3), tag)]
    closes = [690.0, kurs]
    if doppelt:                              # zwei Balken MIT Sessiondatum
        ts.append(int(datetime(tag.year, tag.month, tag.day, 9, 31, tzinfo=NY).timestamp()))
        closes.append(kurs + 5)
    if laengen_bruch:
        # Ein close ZU VIEL, und zwar vorne: zip() paart den Sessionstempel dann mit
        # dem Kurs des Vortags und liefert still 690.0 statt 700.0.
        closes = [600.0] + closes
    meta = {} if ohne_meta else {
        "regularMarketTime": int((rmt or _schluss_ny(session)).timestamp())}
    return {"chart": {"result": [{"meta": meta, "timestamp": ts,
                                  "indicators": {"quote": [{"close": closes}],
                                                 "adjclose": [{"adjclose": closes}]}}]}}


def massive_antwort(session: date, *, kurs=769.05, sym="SPY", balken_datum=None,
                    anzahl=1, sekunden=False, fremdes_symbol=None,
                    ohne_symbol=False, t_wert=None):
    tag = balken_datum or session
    t = datetime(tag.year, tag.month, tag.day, 16, 0, tzinfo=NY).timestamp()
    bar = {"c": kurs, "t": t_wert if t_wert is not None else int(t if sekunden else t * 1000)}
    kopf = {"status": "OK", "results": [bar] * anzahl if anzahl else []}
    if not ohne_symbol:
        bar["T"] = fremdes_symbol or sym
        kopf["ticker"] = fremdes_symbol or sym
    return kopf


class Netz:
    """Attrappe fuer gm._get. Zaehlt die Massive-Abrufe — Fall 1 braucht den Nachweis,
    dass die zweite Quelle bei gueltigem Yahoo GAR NICHT gefragt wird."""
    def __init__(self, antwort=None, fehler=None, folge=None):
        self.abrufe, self.antwort, self.fehler = [], antwort, fehler
        self.folge = list(folge or [])

    def __call__(self, url, key, tries=5):
        self.abrufe.append(url)
        if self.folge:
            naechste = self.folge.pop(0)
            if isinstance(naechste, BaseException):
                raise naechste
            return naechste
        if self.fehler:
            raise self.fehler
        return self.antwort


class Geplatzt:
    """Markiert eine Ausnahme AUS DEM PRODUKTIVCODE. Sie ist nie `None` und nie ein Kurs,
    also reisst jede Pruefung, die eines von beidem erwartet — und zwar mit lesbarem
    Grund. Der Waechter selbst darf dabei nicht sterben: ein Waechterabsturz ist Exit 3
    und zaehlt im Mutationstest als ungueltig, die Zusage „None, kein Absturz" waere dann
    unbewiesen."""

    def __init__(self, fehler):
        self.fehler = fehler

    def __repr__(self):
        return f"AUSNAHME {type(self.fehler).__name__}: {self.fehler}"

    def __eq__(self, andere):
        return False


def spot(sym="SPY", session=S, yahoo=None, netz=None):
    gm._fetch_yahoo = lambda s, p, t: yahoo
    n = netz or Netz()
    gm._get = n
    try:
        erg, ausgabe = _ruhig_mit_ausgabe(gm._spot, sym, "schluessel", session)
    except Exception as e:
        # Eigene Marke: der Mutationstest soll einen PRODUKTIONSABSTURZ von einem
        # fachlichen Gegenbeispiel unterscheiden koennen. Die Pruefung wird trotzdem
        # rot (der Vertrag lautet "None, kein Absturz"), aber die Bilanz sagt, wodurch
        # (Codex D4).
        print("  PRODUKTIONSAUSNAHME %s: %s" % (type(e).__name__, e))
        return Geplatzt(e), n, repr(e)
    return erg, n, ausgabe


print("== Spot: Yahoo traegt, Massive faengt nur das Loch")

# 1 — Yahoo gueltig: Kurs, und KEIN Massive-Abruf.
erg, n, _ = spot(yahoo=yahoo_antwort(S))
pruef("[1] Yahoo gueltig -> Kurs, kein Massive-Abruf", erg == 700.0 and not n.abrufe,
      f"{erg}, {len(n.abrufe)} Abrufe")

# 2 — Das Loch: Balken der Session da, close null, Schluss nachgewiesen -> Massive.
erg, n, _ = spot(yahoo=yahoo_antwort(S, kurs=None), netz=Netz(massive_antwort(S)))
pruef("[2] close=null bei nachgewiesenem Schluss -> Massive-Kurs", erg == 769.05 and len(n.abrufe) == 1,
      f"{erg}, {len(n.abrufe)} Abrufe")

# 3 — /prev vor 00:00 UTC liefert die VORSESSION. Genau der Fall, aus dem /prev in v66.20
#     verworfen wurde; die Datumspruefung faengt ihn unabhaengig von der Uhrzeit.
erg, n, _ = spot(yahoo=yahoo_antwort(S, kurs=None),
                 netz=Netz(massive_antwort(S, balken_datum=S - timedelta(days=1))))
pruef("[3] Massive-Balken der Vorsession -> verworfen", erg is None, erg)

# 4 — DER FALL, DER DEN ENTWURF ENTSCHEIDET: kein Schlussnachweis PLUS gleichdatierter
#     Massive-Balken. Der Rueckfall darf den Yahoo-Schlussnachweis nicht aushebeln.
erg, n, _ = spot(yahoo=yahoo_antwort(S, kurs=None, rmt=_schluss_ny(S) - timedelta(hours=2)),
                 netz=Netz(massive_antwort(S)))
pruef("[4] rmt vor Schluss + gleichdatierter Massive-Balken -> verworfen, kein Abruf",
      erg is None and not n.abrufe, f"{erg}, {len(n.abrufe)} Abrufe")

# 5 — Mehrere Balken mit Sessiondatum sind eine kaputte Antwort, keine Auswahlfrage.
erg, n, _ = spot(yahoo=yahoo_antwort(S, doppelt=True), netz=Netz(massive_antwort(S)))
pruef("[5a] Yahoo: mehrere Balken der Session -> verworfen, kein Rueckfall",
      erg is None and not n.abrufe, f"{erg}, {len(n.abrufe)} Abrufe")
erg, _n, _ = spot(yahoo=yahoo_antwort(S, kurs=None), netz=Netz(massive_antwort(S, anzahl=2)))
pruef("[5b] Massive: nicht genau ein Aggregat -> verworfen", erg is None, erg)

# 6 — Massive-Fehlerfaelle: je None, kein Absturz.
import urllib.error                                                      # noqa: E402
faelle = [
    ("leer", Netz(massive_antwort(S, anzahl=0)), None),
    ("403", Netz(fehler=urllib.error.HTTPError("u", 403, "x", {}, None)), None),
    ("Timeout", Netz(fehler=TimeoutError("timeout")), None),
    ("Struktur kaputt", Netz({"status": "OK"}), None),
    ("falsches Symbol", Netz(massive_antwort(S, fremdes_symbol="QQQ")), None),
    ("c als bool", Netz(massive_antwort(S, kurs=True)), None),
    ("c = inf", Netz(massive_antwort(S, kurs=math.inf)), None),
    ("Zeitstempel in Sekunden", Netz(massive_antwort(S, sekunden=True)), None),
]
for name, netz, soll in faelle:
    erg, _n, _ = spot(yahoo=yahoo_antwort(S, kurs=None), netz=netz)
    pruef(f"[6] Massive {name} -> {soll}", erg is soll, erg)

# 7 — Yahoo-Adapter: timestamp und close verschieden lang.
for name, netz in (
        ("ohne jedes Symbolfeld", Netz(massive_antwort(S, ohne_symbol=True))),
        ("Zeitstempel NaN", Netz(massive_antwort(S, t_wert=float("nan")))),
        ("Zeitstempel 1e30", Netz(massive_antwort(S, t_wert=1e30))),
        # math.isfinite wandelt intern in float um und platzt bei sehr grossen
        # Ganzzahlen mit OverflowError — eine JSON-Antwort darf so etwas enthalten.
        ("Kurs 10**400 (Ganzzahl)", Netz(massive_antwort(S, kurs=10 ** 400))),
        ("Zeitstempel 10**400 (Ganzzahl)", Netz(massive_antwort(S, t_wert=10 ** 400))),
        ("Zeitstempel None", Netz(massive_antwort(S, t_wert=None, sekunden=False))),
):
    if name == "Zeitstempel None":
        continue        # t_wert=None faellt auf den Normalwert zurueck, kein eigener Fall
    erg, _n, _ = spot(yahoo=yahoo_antwort(S, kurs=None), netz=netz)
    pruef(f"[6b] Massive {name} -> None, kein Absturz", erg is None, erg)

# C3: Yahoo-Antworten, die vor der Absicherung eine Ausnahme ausloesten statt eines
# benannten Grundes.
for name, yh in (
        ("result = [null]", {"chart": {"result": [None]}}),
        ("rmt = NaN", yahoo_antwort(S, rmt=None, kurs=700.0)),
        ("timestamp als Text", None),
        ("timestamp keine Liste", None),
):
    if name == "rmt = NaN":
        yh = yahoo_antwort(S)
        yh["chart"]["result"][0]["meta"]["regularMarketTime"] = float("nan")
    if name == "timestamp als Text":
        yh = yahoo_antwort(S)
        yh["chart"]["result"][0]["timestamp"] = ["keine Zahl", "auch nicht"]
    if name == "timestamp keine Liste":
        # Eine ZAHL statt einer Liste: ohne die Typpruefung platzt zip() mit TypeError,
        # und der Vertrag „None, kein Absturz" waere gebrochen. Mein erstes Fixture gab
        # eine Liste von Texten — die besteht die Typpruefung und traf sie deshalb nicht.
        yh = yahoo_antwort(S)
        yh["chart"]["result"][0]["timestamp"] = 1792157400
    erg, n, _ = spot(yahoo=yh, netz=Netz(massive_antwort(S)))
    pruef(f"[6c] Yahoo {name} -> None, kein Absturz, kein Rueckfall",
          erg is None and not n.abrufe, f"{erg}, {len(n.abrufe)} Abrufe")

erg, n, _ = spot(yahoo=yahoo_antwort(S, laengen_bruch=True), netz=Netz(massive_antwort(S)))
pruef("[7] Yahoo timestamp/close verschieden lang -> verworfen (sonst stiller Vortageskurs)",
      erg is None and not n.abrufe, f"{erg}, {len(n.abrufe)} Abrufe")

# 7b — weitere Yahoo-Ablehnungsgruende duerfen den Rueckfall NICHT oeffnen.
for name, yh in (("keine Antwort", None), ("Struktur kaputt", yahoo_antwort(S, kaputt=True)),
                 ("rmt fehlt", yahoo_antwort(S, ohne_meta=True)),
                 ("kein Balken der Session", yahoo_antwort(S, balken_datum=S - timedelta(days=1)))):
    erg, n, _ = spot(yahoo=yh, netz=Netz(massive_antwort(S)))
    pruef(f"[7b] Yahoo {name} -> None, kein Rueckfall", erg is None and not n.abrufe,
          f"{erg}, {len(n.abrufe)} Abrufe")

# 7c — ungueltige Yahoo-Kurse: dieselbe Zahlenregel wie bei Massive.
for name, k in (("bool", True), ("inf", math.inf), ("null", 0.0), ("negativ", -5.0)):
    erg, n, _ = spot(yahoo=yahoo_antwort(S, kurs=k), netz=Netz(massive_antwort(S)))
    pruef(f"[7c] Yahoo-Kurs {name} -> Rueckfall (Kurs fehlt, Schluss steht)",
          erg == 769.05 and len(n.abrufe) == 1, f"{erg}, {len(n.abrufe)} Abrufe")

# 8 — 429: die gedrosselte Wiederholung sitzt in gm._get. Mein erster Testentwurf
#     stubbte _get weg und konnte sie deshalb gar nicht sehen — ein Test, der den
#     Produktionspfad ersetzt, prueft ihn nicht. Hier wird _get selbst ausgefuehrt, mit
#     ausgetauschtem urlopen und ohne echtes Warten.
h429 = urllib.error.HTTPError("u", 429, "Too Many Requests", {}, None)


class _Antwort:
    def __init__(self, nutzlast):
        self._n = json.dumps(nutzlast).encode("utf-8")

    def read(self):
        return self._n

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _get_mit(folge):
    """gm._get echt ausfuehren; urlopen und sleep ersetzt. Gibt (Ergebnis, Versuche)."""
    rufe = []

    def urlopen(req, timeout=None, context=None):
        rufe.append(1)
        naechste = folge[min(len(rufe) - 1, len(folge) - 1)]
        if isinstance(naechste, BaseException):
            raise naechste
        return _Antwort(naechste)

    pausen = []
    alt_open, alt_sleep = gm.urllib.request.urlopen, gm.time.sleep
    gm.urllib.request.urlopen = urlopen
    # Kein echtes Warten, aber die Pausen MESSEN: sonst ist nicht pruefbar, ob
    # Retry-After beachtet wird oder der eigene Backoff laeuft.
    gm.time.sleep = lambda s: pausen.append(s)
    try:
        with contextlib.suppress(urllib.error.HTTPError):
            return _GET_ECHT("https://x/y", "k"), len(rufe), pausen
        return None, len(rufe), pausen
    finally:
        gm.urllib.request.urlopen = alt_open
        gm.time.sleep = alt_sleep


erg, versuche, _p = _get_mit([h429, massive_antwort(S)])
pruef("[8a] 429 dann Erfolg -> Wiederholung im Lader, zweiter Versuch traegt",
      erg is not None and erg.get("status") == "OK" and versuche == 2, f"{versuche} Versuche")
def _h429_mit(sekunden):
    import email.message
    kopf = email.message.Message()
    kopf["Retry-After"] = str(sekunden)
    return urllib.error.HTTPError("u", 429, "Too Many Requests", kopf, None)


erg, versuche, pausen = _get_mit([_h429_mit(7), massive_antwort(S)])
pruef("[8d] Retry-After 7 s wird beachtet (nicht der eigene Backoff von 2 s)",
      7.0 in pausen and 2.0 not in pausen, pausen)

gm._warte_zuruecksetzen()
erg_b, versuche_b, pausen_b = _get_mit([_h429_mit(600)])
pruef("[8e] Retry-After 600 s sprengt das Wartebudget -> Abbruch statt Warten",
      erg_b is None and 600.0 not in pausen_b and versuche_b == 1,
      f"{versuche_b} Versuche, Pausen {pausen_b}")

# [8f] Das Budget gilt fuer den GANZEN Lauf: viele Ticker koennen es gemeinsam
# aufbrauchen. Mit einem Budget je Abruf waere die Summe unbegrenzt — im Yahoo-Loch
# fragen alle 20 Ticker Massive, und die Frist der Unit haette das nicht getragen.
gm._warte_zuruecksetzen()
_summe, _abrufe_bis_stop = 0.0, 0
for _ in range(20):
    _e, _v, _p = _get_mit([_h429_mit(60), massive_antwort(S)])
    _summe += sum(x for x in _p if x >= 1.0)
    if _e is None:
        break
    _abrufe_bis_stop += 1
pruef("[8f] Wartebudget gilt fuer den ganzen Lauf (Summe begrenzt, nicht je Abruf)",
      _summe <= gm._WARTE_BUDGET and _abrufe_bis_stop < 20,
      f"{_summe:.0f} s gewartet, {_abrufe_bis_stop} Abrufe trugen")
gm._warte_zuruecksetzen()

erg, versuche, _p = _get_mit([h429])
pruef("[8b] Dauer-429 -> alle Versuche ausgeschoepft, dann HTTPError",
      erg is None and versuche == 5, f"{erg}, {versuche} Versuche")
erg, n, _ = spot(yahoo=yahoo_antwort(S, kurs=None), netz=Netz(fehler=h429))
pruef("[8c] Dauer-429 im Spot -> None, kein Absturz", erg is None, erg)

# 9 — Winterzeit: NACH der Umstellung am 01.11.2026. Drei Prozesszeitzonen mit
#     Oktober-Fixtures beweisen die Winterzeit nicht.
erg, _n, _ = spot(session=WINTER, yahoo=yahoo_antwort(WINTER))
pruef("[9] Winterzeit (20.11.2026) -> Kurs", erg == 700.0, erg)
erg, _n, _ = spot(session=WINTER,
                  yahoo=yahoo_antwort(WINTER, rmt=_schluss_ny(WINTER) - timedelta(minutes=1)))
pruef("[9] Winterzeit, rmt 1 min vor Schluss -> verworfen", erg is None, erg)

# 10 — Echter Halbtag: Schlusszeit 13:00 unabhaengig festgelegt. Ein Kurs mit rmt 13:00
#      muss durchkommen, einer mit 12:59 nicht — und 16:00 waere die falsche Schwelle.
erg, _n, _ = spot(session=HALBTAG, yahoo=yahoo_antwort(HALBTAG))
pruef("[10a] Halbtag 27.11.2026, rmt 13:00 -> Kurs", erg == 700.0, erg)
erg, _n, _ = spot(session=HALBTAG,
                  yahoo=yahoo_antwort(HALBTAG, rmt=_schluss_ny(HALBTAG) - timedelta(minutes=1)))
pruef("[10b] Halbtag, rmt 12:59 -> verworfen", erg is None, erg)

# 11 — Rueckfall nur fuer belegte Symbole: ein Index bekommt keinen Ersatzkurs.
erg, n, _ = spot(sym="^SPX", yahoo=yahoo_antwort(S, kurs=None), netz=Netz(massive_antwort(S, sym="^SPX")))
pruef("[11] Symbol ausserhalb des Universums -> kein Rueckfall", erg is None and not n.abrufe,
      f"{erg}, {len(n.abrufe)} Abrufe")

# 12 — adjusted=false steht in der angefragten URL (der Spot ist die Strike-Basis).
erg, n, _ = spot(yahoo=yahoo_antwort(S, kurs=None), netz=Netz(massive_antwort(S)))
pruef("[12] Massive-URL mit adjusted=false und /prev",
      len(n.abrufe) == 1 and "adjusted=false" in n.abrufe[0] and "/prev" in n.abrufe[0],
      n.abrufe[:1])


print("== Kette: Exit-Code UND Marker, Exit hat Vorrang")
import gex_kette as kette                                                # noqa: E402

M = kette.MARKER
for name, rc, ausgabe, soll in [
    ("Exit 75 OHNE Marker -> unterdrueckt", 75, "Sperre\n", ("unterdrueckt", 75)),
    ("Exit 75 mit Marker -> unterdrueckt", 75, M + "veroeffentlicht\n", ("unterdrueckt", 75)),
    ("Exit 0 + veroeffentlicht -> veroeffentlicht", 0, M + "veroeffentlicht (Session X)\n",
     ("veroeffentlicht", 0)),
    ("Exit 0 + uebersprungen -> uebersprungen", 0, M + "uebersprungen (Feiertag)\n",
     ("uebersprungen", 0)),
    ("Exit 0 + trocken -> trocken", 0, M + "trocken\n", ("trocken", 0)),
    ("Exit 0 OHNE Marker -> fehlgeschlagen", 0, "nichts\n", ("fehlgeschlagen", 1)),
    ("Exit 0 + ZWEI Marker -> fehlgeschlagen", 0, M + "trocken\n" + M + "veroeffentlicht\n",
     ("fehlgeschlagen", 1)),
    ("Exit 0 + unbekannter Marker -> fehlgeschlagen", 0, M + "irgendwas\n", ("fehlgeschlagen", 1)),
    ("Exit 1 TROTZ veroeffentlicht -> fehlgeschlagen", 1, M + "veroeffentlicht\n",
     ("fehlgeschlagen", 1)),
    ("Exit 2 (Handelszeit) -> fehlgeschlagen", 2, "", ("fehlgeschlagen", 2)),
]:
    ist = kette.ergebnis_aus(rc, ausgabe)
    pruef("[13] " + name, ist == soll, f"{ist} statt {soll}")

# 14 — Key Levels laufen NUR bei veroeffentlicht. Geprueft am echten main() der Huelle,
#      mit ausgetauschtem Teilschritt-Laeufer: der Nachweis ist die Aufrufliste.
def _kette_lauf(rc_snap, marker, rc_kl=0):
    rufe = []

    def laeufer(argv):
        rufe.append(argv[0])
        if "snapshot" in argv[0]:
            return rc_snap, (M + marker + "\n" if marker else "")
        return rc_kl, ""

    alt = kette._lauf
    kette._lauf = laeufer
    try:
        rc = _ruhig(kette.main, [])
    finally:
        kette._lauf = alt
    return rc, rufe


for name, rc_snap, marker, soll_rc, soll_kl in [
    ("veroeffentlicht -> Key Levels laufen", 0, "veroeffentlicht", 0, True),
    ("uebersprungen -> Key Levels laufen NICHT", 0, "uebersprungen", 0, False),
    ("trocken -> Key Levels laufen NICHT", 0, "trocken", 0, False),
    ("unterdrueckt (75) -> Key Levels laufen NICHT", 75, "", 75, False),
    ("ohne Marker -> Key Levels laufen NICHT", 0, "", 1, False),
    ("Fehlerexit trotz Marker -> Key Levels laufen NICHT", 1, "veroeffentlicht", 1, False),
]:
    rc, rufe = _kette_lauf(rc_snap, marker)
    kl = any("key_levels" in r for r in rufe)
    pruef(f"[14] {name}", rc == soll_rc and kl is soll_kl, f"rc {rc}, Aufrufe {rufe}")

rc, rufe = _kette_lauf(0, "veroeffentlicht", rc_kl=75)
pruef("[14] Key Levels unterdrueckt (75) -> Kette 75", rc == 75, rc)
rc, rufe = _kette_lauf(0, "veroeffentlicht", rc_kl=1)
pruef("[14] Key Levels fehlgeschlagen -> Kette rot", rc == 1, rc)


print("== Handelstagpruefung: nur im automatischen Modus")


def _kette_kontrakte(session: date, spot_kurs=700.0):
    """Options-Kette wie im Bestandswaechter: genug Kontrakte, damit _MIN_CONTRACTS
    haelt. Eine leere Kette liess den Ticker ausfallen und die Reissleine den Lauf rot
    machen — dann faellt der Trockenlauf-Marker nie, und der Test prueft das Falsche."""
    verfaelle = [session + timedelta(days=k) for k in (7, 14, 28)]
    out = []
    for ex in verfaelle:
        for k in range(650, 751, 5):
            for typ in ("call", "put"):
                m = (k - spot_kurs) / spot_kurs
                iv = 0.20 + (0.3 * m * m) + (0.02 if typ == "put" else 0.0)
                delta = 0.5 - m * 4 if typ == "call" else -0.5 - m * 4
                out.append({"details": {"expiration_date": ex.isoformat(), "contract_type": typ,
                                        "strike_price": float(k)},
                            "open_interest": 1000 + abs(k - 700) * 20,
                            "implied_volatility": iv,
                            "greeks": {"delta": max(-0.99, min(0.99, delta)), "gamma": 0.01},
                            "day": {"volume": 10}, "underlying_asset": {"price": spot_kurs}})
    return out


class NetzKette:
    """Attrappe fuer gm._get im Ganzlauf: Options-Snapshot. Zaehlt Abrufe."""
    def __init__(self, session=S):
        self.abrufe, self.session = [], session

    def __call__(self, url, key, tries=5):
        self.abrufe.append(url)
        if "/v3/snapshot/options/" in url:
            return {"status": "OK", "results": _kette_kontrakte(self.session), "next_url": None}
        return massive_antwort(self.session)


def ganzlauf(name, jetzt, *argv, yahoo_kurs=700.0):
    sess = eh.letzte_session("NYSE", jetzt)
    n = NetzKette(sess)
    gm._get = n
    gm._fetch_yahoo = lambda s, p, t: yahoo_antwort(sess, kurs=yahoo_kurs)
    ziel = _TMP / name
    ziel.mkdir(parents=True, exist_ok=True)
    gm._DATA = ziel
    _uhr(jetzt)
    alt = sys.argv
    sys.argv = ["snapshot_gex_massive.py", "--tickers", "SPY", *argv]
    try:
        (rc, ausgabe) = _ruhig_mit_ausgabe(gm.main)
    finally:
        sys.argv = alt
    dateien = sorted(p.name for p in ziel.rglob("*") if p.is_file())
    return rc, ausgabe, dateien, n


# Thanksgiving 2026 ist ein DONNERSTAG: ein Mo-Fr-Timer feuert, markt_offen ist False
# (der EOD-Test laesst also durch), und letzte_session zeigt auf den 25.11. — die Session,
# die in der Nacht davor schon veroeffentlicht wurde.
FEIERTAG_ABEND = datetime(2026, 11, 26, 22, 15, tzinfo=UTC)
pruef("[15] Vorbedingung: 26.11.2026 ist kein Handelstag, letzte_session = 25.11.",
      not eh.is_trading_day(date(2026, 11, 26), "NYSE")
      and eh.letzte_session("NYSE", FEIERTAG_ABEND) == date(2026, 11, 25),
      eh.letzte_session("NYSE", FEIERTAG_ABEND))

rc, ausgabe, dateien, n = ganzlauf("feiertag_auto", FEIERTAG_ABEND)
pruef("[16] Feiertag, automatisch -> uebersprungen, KEIN Abruf, keine Datei",
      rc == 0 and f"{M}uebersprungen" in ausgabe and not n.abrufe and not dateien,
      f"rc {rc}, {len(n.abrufe)} Abrufe, {dateien}")

# 01:30 UTC am 27.11. = 26.11. 20:30 New York, also noch Thanksgiving. Nach UTC-Datum
# waere es der 27.11. (ein Handelstag) — genau hier trennt sich die Zeitzone.
NACH_MITTERNACHT_UTC = datetime(2026, 11, 27, 1, 30, tzinfo=UTC)
pruef("[16b] Vorbedingung: 27.11. 01:30 UTC ist in New York noch der 26.11.",
      NACH_MITTERNACHT_UTC.astimezone(NY).date() == date(2026, 11, 26)
      and eh.is_trading_day(date(2026, 11, 27), "NYSE"),
      NACH_MITTERNACHT_UTC.astimezone(NY).date())
rc, ausgabe, dateien, n = ganzlauf("feiertag_nach_mitternacht", NACH_MITTERNACHT_UTC)
pruef("[16b] Feiertag, Lauf 01:30 UTC -> uebersprungen (New Yorker Datum entscheidet)",
      rc == 0 and f"{M}uebersprungen" in ausgabe and not n.abrufe and not dateien,
      f"rc {rc}, {len(n.abrufe)} Abrufe, {dateien}")

rc, ausgabe, dateien, n = ganzlauf("feiertag_rep", FEIERTAG_ABEND, "--reparatur")
# Nicht nur "irgendein Abruf": Exit, Marker UND Dateien. Ein Reparaturlauf, der
# abruft und dann scheitert, haette die schwaechere Pruefung bestanden (Codex C6).
_sess_rep = eh.letzte_session("NYSE", FEIERTAG_ABEND)
pruef("[17] Feiertag, --reparatur -> laeuft, veroeffentlicht, schreibt Summary UND Archiv",
      rc == 0 and n.abrufe != [] and f"{M}veroeffentlicht" in ausgabe
      and "gex_summary.json" in dateien
      # Namentlich: "irgendeine weitere JSON-Datei" erfuellte die Profildatei, das Archiv
      # blieb ungeprueft — die Mutation "schreibt kein Archiv" kam damit durch.
      and f"{_sess_rep.isoformat()}.json" in dateien,
      f"rc {rc}, {len(n.abrufe)} Abrufe, {dateien}")

rc, ausgabe, dateien, n = ganzlauf("feiertag_trocken", FEIERTAG_ABEND, "--no-write")
pruef("[18] Feiertag, --no-write -> trocken, schreibt nichts",
      rc == 0 and f"{M}trocken" in ausgabe and not dateien, f"rc {rc}, {dateien}")

HANDELSTAG_ABEND = datetime(2026, 10, 16, 22, 15, tzinfo=UTC)
rc, ausgabe, dateien, n = ganzlauf("handelstag_trocken", HANDELSTAG_ABEND, "--no-write")
pruef("[19] Handelstag, --no-write -> trocken, schreibt nichts",
      rc == 0 and f"{M}trocken" in ausgabe and not dateien, f"rc {rc}, {dateien}")


print("== Reissleine: unter der Abdeckungsgrenze bleibt JEDE Datei unveraendert")
# Codex C6: die vereinbarten Faelle 11/20 und 12/20 fehlten. 0,6 x 20 = 12, also sind 11
# Ticker zu wenig und 12 genug. Geprueft wird per Hash ueber ALLE vorhandenen Ausgaben,
# nicht nur ueber die Summary.
def _hashes(ordner: Path) -> dict:
    import hashlib
    return {str(p.relative_to(ordner)).replace("\\", "/"):
            hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(ordner.rglob("*")) if p.is_file()}


def _lauf_mit_ausfaellen(name, gute: int):
    """Ganzlauf ueber 20 Ticker, von denen nur `gute` einen Spot bekommen."""
    universum = list(gm.UNIVERSE)[:10]
    ok_ticker = set(universum[:gute])
    ordner = _TMP / name
    ordner.mkdir(parents=True, exist_ok=True)
    # Bestand anlegen, der NICHT ueberschrieben werden darf
    (ordner / "gex_summary.json").write_text(json.dumps({"stand": "alt"}), encoding="utf-8")
    (ordner / "gex_history_session").mkdir(exist_ok=True)
    (ordner / "gex_history_session" / f"{S.isoformat()}.json").write_text(
        json.dumps({"stand": "alt"}), encoding="utf-8")
    vorher = _hashes(ordner)

    n = NetzKette(S)
    gm._get = n
    gm._fetch_yahoo = lambda s, p, t: (yahoo_antwort(S) if s in ok_ticker else None)
    gm._DATA = ordner
    _uhr(datetime(2026, 10, 16, 22, 15, tzinfo=UTC))
    alt = sys.argv
    sys.argv = ["snapshot_gex_massive.py", "--tickers", ",".join(universum)]
    try:
        rc, ausgabe = _ruhig_mit_ausgabe(gm.main)
    finally:
        sys.argv = alt
    return rc, ausgabe, vorher, _hashes(ordner)


rc, ausgabe, vorher, nachher = _lauf_mit_ausfaellen("grenze_5", 5)
pruef("[22a] 5 von 10 brauchbar -> Abbruch, JEDE Datei unveraendert",
      rc == 1 and vorher == nachher and M not in ausgabe,
      f"rc {rc}, gleich {vorher == nachher}")

rc, ausgabe, vorher, nachher = _lauf_mit_ausfaellen("grenze_6", 6)
pruef("[22b] 6 von 10 brauchbar -> veroeffentlicht (Grenze 0,6 x 10 = 6)",
      rc == 0 and f"{M}veroeffentlicht" in ausgabe and vorher != nachher,
      f"rc {rc}, geaendert {vorher != nachher}")

print("== Atomares Schreiben: Rechte und Vollstaendigkeit")
from shared.atomic_json import write_json_atomic                         # noqa: E402

# 20 — Rechte der Zieldatei bleiben erhalten. mkstemp legt mit 0600 an, os.replace
#      uebertraegt das — nginx laeuft als anderer Nutzer und liefert dann 403
#      (live aufgetreten 2026-09-11).
if os.name == "nt":
    # NICHT als bestanden zaehlen: Windows kennt diese Rechte nicht, die Pruefung koennte
    # hier gar nicht reissen (Codex C6). Ein uebersprungener Nachweis ist kein Nachweis.
    print("  uebersprungen [20] Rechte der Zieldatei — nur unter Linux pruefbar")
    UEBERSPRUNGEN.append("[20] Rechte der Zieldatei")
else:
    ziel = _TMP / "rechte.json"
    write_json_atomic(ziel, {"a": 1})
    modus_neu = stat.S_IMODE(os.stat(ziel).st_mode)
    os.chmod(ziel, 0o644)
    write_json_atomic(ziel, {"a": 2})
    modus_erhalten = stat.S_IMODE(os.stat(ziel).st_mode)
    pruef("[20] atomar: Rechte der Zieldatei bleiben (0644, nicht 0600)",
          modus_erhalten == 0o644 and modus_neu != 0o600,
          f"neu {oct(modus_neu)}, erhalten {oct(modus_erhalten)}")

# 21 — Fristablauf IM Veroeffentlichungsweg der ECHTEN Erzeuger. Genau dafuer ist
#      Auflage 2 da: der Container-Timeout beendet den Prozess im Container und kann
#      mitten in einem Schreibzugriff zuschlagen.
#      Mein erster Entwurf rief write_json_atomic DIREKT — damit waere der Test gruen
#      geblieben, selbst wenn der Erzeuger wieder write_text benutzt haette (Codex C5).
#      Jetzt laeuft der Erzeuger, und der Abbruch trifft seinen Schreibzugriff.
class _Abbruch(BaseException):
    """Wie SIGTERM/timeout: kein normaler Fehler, erbt von BaseException."""


import shared.atomic_json as aj                                          # noqa: E402
import compute_key_levels as kl                                          # noqa: E402
# Die ECHTE Lader-Funktion SOFORT sichern: spaetere Faelle setzen kl._get auf eine
# Attrappe und stellen sie nicht zurueck. Eine Sicherung weiter unten griffe schon
# die Attrappe — der Budgetfall bestand dann mit lauter Nullen.
_KL_GET_ECHT = kl._get


def _abbruch_beim_schreiben(erzeuger, ziel_namen, vorbelegung, ordnername="abbruch",
                            treffer=1):
    """Erzeuger laufen lassen und beim `treffer`-ten Schreibzugriff abbrechen.

    Gibt (alles_unveraendert, alles_gueltiges_json, Temp-Reste, zugriffe, abgebrochen).
    `abgebrochen` ist der Beweis, dass der Test ueberhaupt etwas getan hat: mein erster
    Entwurf unterdrueckte die Ausnahme, ohne zu pruefen, ob sie geworfen wurde — ein
    Erzeuger, der vorzeitig zurueckkehrt, haette den Test gruen bestehen lassen
    (Codex D2, mit einem sofort zurueckkehrenden Erzeuger nachgestellt).

    Der Abbruch wird im json.dump der atomaren Veroeffentlichung ausgeloest, also genau
    dort, wo eine Frist zuschlagen wuerde. Wer den Erzeuger auf write_text zurueckstellt,
    schreibt nicht mehr atomar: die Zieldatei wird gekuerzt und der Test wird rot.
    """
    ordner = _TMP / ordnername
    ordner.mkdir(parents=True, exist_ok=True)
    vorher = {}
    for name in ziel_namen:
        p = ordner / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(vorbelegung), encoding="utf-8")
        vorher[name] = p.read_bytes()

    alt_dump = aj.json.dump
    zustand = {"zugriffe": 0, "abgebrochen": False}

    def dump_bricht(obj, f, **k):
        zustand["zugriffe"] += 1
        if zustand["zugriffe"] < treffer:
            return alt_dump(obj, f, **k)       # frueheren Schreibzugriff durchlassen
        f.write('{"halb": true')               # halbe Datei in die TEMP-Datei
        zustand["abgebrochen"] = True
        raise _Abbruch()

    aj.json.dump = dump_bricht
    try:
        with contextlib.suppress(_Abbruch):
            _ruhig(erzeuger, ordner)
    finally:
        aj.json.dump = alt_dump

    geaendert, gueltig = {}, True
    for name in ziel_namen:
        p = ordner / name
        geaendert[name] = p.read_bytes() != vorher[name]
        try:
            json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            gueltig = False
    reste = [p.name for p in ordner.rglob(".*tmp")] + [p.name for p in ordner.rglob("*.tmp")]
    return geaendert, gueltig, reste, zustand["zugriffe"], zustand["abgebrochen"]


def _snapshot_erzeuger(ordner):
    n = NetzKette(S)
    gm._get = n
    gm._fetch_yahoo = lambda s, p, t: yahoo_antwort(S)
    gm._DATA = ordner
    _uhr(datetime(2026, 10, 16, 22, 15, tzinfo=UTC))
    alt = sys.argv
    sys.argv = ["snapshot_gex_massive.py", "--tickers", "SPY", "--reparatur"]
    try:
        return gm.main()
    finally:
        sys.argv = alt


# Der Snapshot schreibt DREI Arten von Dateien nacheinander: Summary, Profile, Archiv.
# Ein Abbruch nur an der ersten liesse einen Rueckfall auf write_text an den beiden
# anderen unentdeckt (Codex D2). Deshalb jede Stelle einzeln treffen.
_snap_ziele = ["gex_summary.json", "gex_profile_SPY.json",
               "gex_history_session/%s.json" % S.isoformat()]
for _nr, _was in ((1, "Summary"), (2, "Profil"), (3, "Archiv")):
    g_je, g, reste, zugriffe, abgebrochen = _abbruch_beim_schreiben(
        _snapshot_erzeuger, _snap_ziele, {"stand": "alt"},
        ordnername="abbruch_snap%d" % _nr, treffer=_nr)
    # Dateien VOR der abgebrochenen Stelle sind legitim geschrieben; die Datei der
    # abgebrochenen Stelle muss unveraendert bleiben, und alle muessen gueltiges JSON
    # sein. "Alle unveraendert" waere hier die falsche Zusicherung gewesen.
    _ziel = _snap_ziele[_nr - 1]
    pruef("[21a-%d] Abbruch beim Schreiben der %s -> ausgeloest, %s unveraendert, "
          "alle Dateien gueltiges JSON" % (_nr, _was, _was),
          abgebrochen and zugriffe == _nr and not g_je[_ziel] and g and not reste,
          f"abgebrochen {abgebrochen}, Zugriffe {zugriffe}, {_was} veraendert "
          f"{g_je[_ziel]}, gueltig {g}, Reste {reste}")


def _keylevels_erzeuger(ordner):
    """Muster aus verify_gex_session.py:257 — `kl._ROOT` (nicht `_DATA`) und
    `kl.build(..., write=True)` mit einer ECHTEN Kette. Mein erster Entwurf setzte
    `_DATA` und lieferte eine leere Kette: der Erzeuger kam nie bis zum Schreibzugriff,
    und der Abbruchtest blieb gruen, obwohl das Programm wieder nicht atomar schrieb."""
    (ordner / "landing/data").mkdir(parents=True, exist_ok=True)
    (ordner / "landing/data/gex_summary.json").write_text(json.dumps(
        {"date": S.isoformat(), "session": S.isoformat(), "bewertung": S.isoformat(),
         "stempel_art": "session",
         "tickers": [{"ticker": "SPY", "spot": 700.0, "zero_gamma": 690.0,
                      "call_wall": 720.0, "put_wall": 680.0, "regime": "long_gamma",
                      "net_gex_usd_bn": 1.0}]}), encoding="utf-8")
    kl._ROOT = ordner
    kl._get = NetzKette(S)
    _uhr(datetime(2026, 10, 16, 22, 15, tzinfo=UTC))
    return kl.build(["SPY"], write=True)


_kl_ziel = "landing/data/key_levels.json"
g_je, g, reste, zugriffe, abgebrochen = _abbruch_beim_schreiben(
    _keylevels_erzeuger, [_kl_ziel], {"stand": "alt"}, ordnername="abbruch_kl")
pruef("[21b] Abbruch im Key-Levels-Schreibzugriff -> ausgeloest, Datei unveraendert, gueltig",
      abgebrochen and not g_je[_kl_ziel] and g and not reste,
      f"abgebrochen {abgebrochen}, Zugriffe {zugriffe}, veraendert {g_je[_kl_ziel]}, "
      f"gueltig {g}, Reste {reste}")


# Codex C6: der direkte CLI-Aufruf von compute_key_levels umgeht die Huelle, sein Modus
# muss also selbstaendig gelten. Geprueft wird, dass --no-write auch dort nichts schreibt.
import compute_key_levels as kl_cli                                      # noqa: E402

# build() schreibt nach _ROOT/"landing/data/key_levels.json" — NICHT nach _DATA.
# Mein erster Entwurf setzte _DATA und beobachtete deshalb ein leeres Verzeichnis: die
# Pruefung konnte nicht reissen, auch wenn --no-write ignoriert wird (Codex D1).
_ordner_kl = _TMP / "kl_cli"
(_ordner_kl / "landing/data").mkdir(parents=True, exist_ok=True)
_ziel_kl = _ordner_kl / "landing/data/key_levels.json"
_ziel_kl.write_text(json.dumps({"stand": "alt"}), encoding="utf-8")
_vorher_kl = _ziel_kl.read_bytes()
(_ordner_kl / "landing/data/gex_summary.json").write_text(json.dumps(
    {"date": S.isoformat(), "session": S.isoformat(), "bewertung": S.isoformat(),
     "stempel_art": "session",
     "tickers": [{"ticker": "SPY", "spot": 700.0, "zero_gamma": 690.0, "call_wall": 720.0,
                  "put_wall": 680.0, "regime": "long_gamma", "net_gex_usd_bn": 1.0}]}),
    encoding="utf-8")
kl_cli._ROOT = _ordner_kl
kl_cli._get = NetzKette(S)
_uhr(datetime(2026, 10, 16, 22, 15, tzinfo=UTC))
_alt_argv = sys.argv
sys.argv = ["compute_key_levels.py", "--tickers", "SPY", "--no-write"]
try:
    rc_kl = _ruhig(kl_cli.main)
finally:
    sys.argv = _alt_argv
pruef("[23] compute_key_levels direkt mit --no-write -> Exit 0 und Zieldatei unveraendert",
      rc_kl == 0 and _ziel_kl.read_bytes() == _vorher_kl,
      f"rc {rc_kl}, veraendert {_ziel_kl.read_bytes() != _vorher_kl}")

print("== Produktionssperre: echter Eintritt, Exit 75 ohne Marker")
# Codex C6: Exit 75 kam bisher nur aus dem Ersatzlaeufer. Hier wird die Sperre WIRKLICH
# betreten — mit gesetzter Aktivierungsmarke im isolierten Sperrverzeichnis — und der
# Nachweis ist, dass dabei KEIN Marker entsteht. Genau diese Kombination haette die
# Regel "fehlender Marker = fehlgeschlagen" falsch eingeordnet.
import subprocess                                                        # noqa: E402

_SPERRVERZ = Path(os.environ["SA_SPERR_DIR"])
_SPERRVERZ.mkdir(parents=True, exist_ok=True)
(_SPERRVERZ / "AKTIVIERUNG").write_text("probe-kennung\n", encoding="utf-8")
_umg = dict(os.environ, PYTHONUTF8="1")
_umg.pop("SA_AKTIVIERUNG", None)
p = subprocess.run([sys.executable, "-u", "scripts/snapshot_gex_massive.py",
                    "--tickers", "SPY", "--no-write"],
                   cwd=str(_ROOT), capture_output=True, text=True,
                   encoding="utf-8", errors="replace", env=_umg)
(_SPERRVERZ / "AKTIVIERUNG").unlink()
pruef("[21c] echter Sperreintritt -> Exit 75 und KEIN Ergebnismarker",
      p.returncode == 75 and M not in (p.stdout or ""),
      f"Exit {p.returncode}, Marker im Text: {M in (p.stdout or '')}")
ist = kette.ergebnis_aus(p.returncode, p.stdout or "")
pruef("[21d] die Huelle ordnet diesen echten Lauf als unterdrueckt ein",
      ist == ("unterdrueckt", 75), ist)

# Beide Programme der Kette brauchen dasselbe Prozess-Wartebudget. Key Levels holt seine
# Chain selbst (bis zu 45 Seiten je Ticker) — ohne Budget waere die Frist der Unit nicht
# gedeckt, auch wenn der Snapshot sauber begrenzt ist (Codex D3).
import compute_key_levels as _kl_budget                                  # noqa: E402
pruef("[27] Key Levels hat dasselbe Prozess-Wartebudget wie der Snapshot",
      getattr(_kl_budget, "_WARTE_BUDGET", None) == gm._WARTE_BUDGET
      and hasattr(_kl_budget, "_gewartet_gesamt"),
      f"KL {getattr(_kl_budget, '_WARTE_BUDGET', None)}, Snapshot {gm._WARTE_BUDGET}")


def _kl_get_mit(folge):
    """compute_key_levels._get ECHT ausfuehren, urlopen und sleep ersetzt.
    Eine Pruefung auf die blosse Existenz der Konstante reicht nicht — sie bliebe gruen,
    wenn die Budgetpruefung im Lader abgeschaltet waere (Codex-Befund am Mutationslauf)."""
    rufe, pausen = [], []

    def urlopen(req, timeout=None, context=None):
        rufe.append(1)
        n = folge[min(len(rufe) - 1, len(folge) - 1)]
        if isinstance(n, BaseException):
            raise n
        return _Antwort(n)

    alt_open, alt_sleep = _kl_budget.urllib.request.urlopen, _kl_budget.time.sleep
    _kl_budget.urllib.request.urlopen = urlopen
    _kl_budget.time.sleep = lambda s: pausen.append(s)
    try:
        with contextlib.suppress(urllib.error.HTTPError):
            return _KL_GET_ECHT("https://x/y", "k"), len(rufe), pausen
        return None, len(rufe), pausen
    finally:
        _kl_budget.urllib.request.urlopen = alt_open
        _kl_budget.time.sleep = alt_sleep


_kl_budget._warte_zuruecksetzen()
_summe_kl, _mit_pause = 0.0, 0
for _ in range(25):
    # Dauerhaft 429: ein Abruf schoepft 2+4+6+8 = 20 s aus. Ohne Budget waeren das
    # 25 x 20 = 500 s; mit Budget ist bei 300 s Schluss und die letzten Abrufe warten
    # gar nicht mehr.
    _e, _v, _p = _kl_get_mit([h429])
    _lang = sum(x for x in _p if x >= 1.0)
    _summe_kl += _lang
    if _lang:
        _mit_pause += 1
# `_mit_pause > 0` ist Pflicht: ohne diese Bedingung besteht die Pruefung auch dann,
# wenn gar nichts passiert ist (genau so war sie zuerst gruen, obwohl sie eine Attrappe
# befragte). Eine Pruefung, die mit lauter Nullen besteht, prueft nichts.
pruef("[27] Wartebudget der Key Levels wirkt (es wird gewartet, aber begrenzt)",
      _mit_pause > 0 and _summe_kl <= _kl_budget._WARTE_BUDGET and _mit_pause < 25,
      f"{_summe_kl:.0f} s gewartet, {_mit_pause} von 25 Abrufen mit Pause")
_kl_budget._warte_zuruecksetzen()

# Der Gate-Runner hat eine schlanke Umgebung: numpy, requests, pandas, jinja2 — kein
# streamlit. snapshot_gex_massive zieht es aber ueber shared/yahoo_downloader, und zwar
# auf MODULEBENE. Daran war der Deploy von e7e881f rot. Diese Pruefung haelt fest, dass
# die Attrappe fuer BEIDE Wege vorhanden ist: fuer diesen Prozess und fuer Kindprozesse,
# die scripts/ neu starten (daran scheiterten [21c]/[21d] in der Gegenprobe).
_hat_streamlit = "streamlit" in sys.modules
_stub_datei = (_TMP / "stub" / "streamlit.py").exists()
_stub_im_pfad = str(_TMP / "stub") in os.environ.get("PYTHONPATH", "")
pruef("[32] streamlit: entweder echt vorhanden oder Attrappe fuer Prozess UND Kindprozesse",
      _hat_streamlit and (_stub_datei == _stub_im_pfad),
      f"in sys.modules {_hat_streamlit}, Attrappendatei {_stub_datei}, im PYTHONPATH {_stub_im_pfad}")

print("== Vertrag: Unit, Installer, Workflow, Sperre")
unit = (_ROOT / "deploy/systemd/sa-gex-snapshot.service").read_text(encoding="utf-8")
timer = (_ROOT / "deploy/systemd/sa-gex-snapshot.timer").read_text(encoding="utf-8")
installer = (_ROOT / "deploy/install_timers.sh").read_text(encoding="utf-8")
wf = (_ROOT / ".github/workflows/gex_snapshot.yml").read_text(encoding="utf-8")

pruef("[22] Timer: Mo-Fr 22:15 UTC, nicht nachholend",
      "OnCalendar=Mon..Fri 22:15:00 UTC" in timer and "Persistent=false" in timer)
pruef("[23] Unit: Timeout IM Container (docker exec ... timeout ... python3)",
      "docker exec seasonalpha-app timeout" in unit and "gex_kette.py" in unit)
pruef("[24] Unit: genau EIN ExecStart (die Huelle haelt den Lock ueber beide Schritte)",
      len([z for z in unit.splitlines() if z.startswith("ExecStart=")]) == 1)
import re as _re                                                      # noqa: E402
_m_aussen = _re.search(r"TimeoutStartSec=(\d+)min", unit)
_m_innen = _re.search(r"timeout --kill-after=\d+s (\d+)m ", unit)
pruef("[25] Unit: TimeoutStartSec liegt ueber der Containerfrist",
      bool(_m_aussen and _m_innen) and int(_m_aussen.group(1)) > int(_m_innen.group(1)),
      f"aussen {_m_aussen and _m_aussen.group(1)} min, innen {_m_innen and _m_innen.group(1)} min")
# Zeilenweise, NICHT per Substring: `# SuccessExitStatus=75` enthaelt den Text auch
# auskommentiert — die Mutation blieb damit unbemerkt (eigene Lektion v66.0: ein
# Waechter, der ein Wort sucht statt die Wirkung, ist keiner).
pruef("[26] Unit: Exit 75 als Erfolg (wirksame Zeile, nicht auskommentiert)",
      any(z.strip() == "SuccessExitStatus=75" for z in unit.splitlines()))
pruef("[27] Installer kennt Service und Timer",
      "sa-gex-snapshot.service" in installer and "sa-gex-snapshot.timer" in installer)
pruef("[28] Workflow OHNE Zeitplan (sonst Doppellauf zum Timer)",
      "workflow_dispatch" in wf and "schedule:" not in wf and "cron:" not in wf)
# Am BEFEHL pruefen, nicht im Dateitext: "--reparatur" steht auch im Kommentar
# darueber, deshalb blieb die Mutation am docker-exec-Aufruf unbemerkt.
pruef("[29] Workflow-Notausloeser ruft die Huelle mit --reparatur",
      any("gex_kette.py" in z and "--reparatur" in z for z in wf.splitlines()))
pruef("[30] Workflow bildet Exit 75 auf Erfolg ab", 'rc" -eq 75' in wf or "rc\" -eq 75" in wf
      or '[ "$rc" -eq 75 ]' in wf)

from shared.produktionssperre import PFLICHT, AUSNAHMEN                  # noqa: E402
pruef("[31] beide Programme und die Huelle sind PFLICHT, nicht AUSNAHME",
      all(n in PFLICHT for n in ("snapshot_gex_massive.py", "compute_key_levels.py", "gex_kette.py"))
      and not any(n in AUSNAHMEN for n in ("snapshot_gex_massive.py", "compute_key_levels.py")),
      [n for n in ("snapshot_gex_massive.py", "compute_key_levels.py", "gex_kette.py")
       if n not in PFLICHT])

for u in UEBERSPRUNGEN:
    print("  (uebersprungen, kein Nachweis) " + u)
print(f"PROBE-ENDE {ANZAHL[0]}")
shutil.rmtree(_TMP, ignore_errors=True)
if FEHLER:
    print(f"\n[FEHLER] {len(FEHLER)} Pruefung(en) rot:")
    for f in FEHLER:
        print("  - " + f)
    sys.exit(1)
print("\n[OK] alle Pruefungen gruen")
