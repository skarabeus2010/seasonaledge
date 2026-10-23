#!/usr/bin/env python3
"""Waechter B2: Laufbindung, Abschlussmarke, exklusive Kettensperre.

Geprueft wird der echte Pfad: `lauf_aus` und `marke_schreiben` im Original, die echte
`gex_kette.main()` mit Attrappen fuer die beiden Teilschritte, `_load_gex` mit einer
fremden Kennung, und — unter Linux — die Sperre mit zwei echten Prozessen.

Hintergrund: docs/KEY_LEVELS_CHART.md, Abschnitt 4 (Veroeffentlichungsvertrag).

Aufruf: py -3.14 scripts/verify_gex_kette_lauf.py   — Exit 0 gruen, 1 rot, 3 Absturz.
"""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import tempfile
import textwrap
import traceback

_WURZEL = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_WURZEL))
sys.path.insert(0, str(_WURZEL / "scripts"))

_TMP = pathlib.Path(tempfile.mkdtemp(prefix="sa-b2-"))
os.environ["SA_SPERR_DIR"] = str(_TMP / "sperre")
os.environ["SA_OHNE_DOTENV"] = "1"
os.environ["MASSIVE_API_KEY"] = "probe-kein-echter-schluessel"


def _absturz(t, w, tb):
    print("\n[ABSTURZ] %s: %s" % (t.__name__, w))
    traceback.print_tb(tb)
    sys.exit(3)


sys.excepthook = _absturz

try:                                           # noqa: SIM105
    import streamlit  # noqa: F401
except ImportError:
    import types
    st = types.ModuleType("streamlit")
    st.cache_data = lambda *a, **k: (lambda f: f)
    st.secrets = {}
    sys.modules["streamlit"] = st
    (_TMP / "stub").mkdir(parents=True, exist_ok=True)
    (_TMP / "stub" / "streamlit.py").write_text(
        "def cache_data(*a, **k):\n    return lambda f: f\n\n\nsecrets = {}\n",
        encoding="utf-8")
    os.environ["PYTHONPATH"] = str(_TMP / "stub") + os.pathsep + os.environ.get("PYTHONPATH", "")

from datetime import date                                              # noqa: E402

import gex_kette as gk                                                 # noqa: E402

_SESSION = "2026-10-21"
_fehler = 0
_n = 0


def pruef(name, ok, info=None):
    global _fehler, _n
    _n += 1
    print("  %s %s%s" % ("ok  " if ok else "FAIL", name,
                         "" if info is None else "  ->  %s" % (info,)))
    if not ok:
        _fehler += 1


def _marke_weg():
    if gk._MARKE.exists():
        gk._MARKE.unlink()


def _marke():
    """Marke defensiv lesen: entfernt eine Mutation das Schreiben, soll die Probe
    SCHEITERN und nicht abstuerzen — ein Absturz ist kein Nachweis."""
    if not gk._MARKE.exists():
        return {}
    try:
        return json.loads(gk._MARKE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _arg(argv, name):
    """Wert eines Arguments oder None — `argv.index` wuerde bei fehlendem Argument
    werfen und die Probe mitnehmen."""
    return argv[argv.index(name) + 1] if name in argv and argv.index(name) + 1 < len(argv) else None


# ───────────────────── 1 lauf_aus: reine Funktion ───────────────────────────────
print("\n[1] lauf_aus — Kennung und Session aus der Ausgabe")
pruef("eine Markerzeile mit zwei Feldern",
      gk.lauf_aus("blah\n[lauf] L1 2026-10-21\nmehr") == ("L1", "2026-10-21"))
pruef("keine Markerzeile -> (None, None)", gk.lauf_aus("nichts") == (None, None))
pruef("ZWEI Markerzeilen -> (None, None), keine Zuordnung mehr sicher",
      gk.lauf_aus("[lauf] L1 2026-10-21\n[lauf] L2 2026-10-21") == (None, None))
pruef("Marker ohne Session -> (None, None)", gk.lauf_aus("[lauf] L1") == (None, None))
pruef("leerer Marker -> (None, None)", gk.lauf_aus("[lauf] ") == (None, None))
pruef("Kennungen sind verschieden", gk.neue_kennung() != gk.neue_kennung())

# ───────────────────── 2 marke_schreiben ────────────────────────────────────────
print("\n[2] marke_schreiben — Versuch, Abschluss, Artefakthashes")
gk._ROOT = _TMP
gk._MARKE = _TMP / "landing" / "data" / "gex_lauf.json"
daten = _TMP / "landing" / "data"
daten.mkdir(parents=True, exist_ok=True)

gk.marke_schreiben("L1", None, fertig=False)
m = _marke()
pruef("Versuchseintrag ohne Session moeglich",
      m.get("lauf") == "L1" and m.get("fertig") is False and m.get("session") is None, m)
pruef("Versuchseintrag traegt keine Artefakte", "artefakte" not in m)

fehlgeschlagen = False
try:
    gk.marke_schreiben("L1", None, fertig=True)
except ValueError:
    fehlgeschlagen = True
pruef("Abschluss ohne Session wird verweigert", fehlgeschlagen)

# Pflichtartefakte fehlen noch
gk.marke_schreiben("L1", _SESSION, fertig=True)
m = _marke()
pruef("ohne Pflichtartefakte KEIN Abschluss", m.get("fertig") is False, m.get("fehlend"))
pruef("die fehlenden Artefakte werden benannt", len(m.get("fehlend") or []) == 3,
      m.get("fehlend"))

(daten / "gex_history_session").mkdir(exist_ok=True)
(daten / "gex_summary.json").write_text('{"a":1}', encoding="utf-8")
(daten / "gex_history_session" / ("%s.json" % _SESSION)).write_text('{"b":2}', encoding="utf-8")
(daten / "key_levels.json").write_text('{"c":3}', encoding="utf-8")
gk.marke_schreiben("L1", _SESSION, fertig=True)
m = _marke()
pruef("mit allen Artefakten: Abschluss", m.get("fertig") is True)
pruef("drei Artefakte mit Hash und Groesse",
      len(m.get("artefakte") or []) == 3
      and all(len(a["sha256"]) == 64 and a["bytes"] > 0 for a in (m.get("artefakte") or [])),
      [a["pfad"] for a in (m.get("artefakte") or [])])
pruef("Pfade sind relativ (kein Laufwerksbuchstabe)",
      all(not a["pfad"].startswith(str(_TMP)) and ":" not in a["pfad"]
          for a in (m.get("artefakte") or [])), [a["pfad"] for a in (m.get("artefakte") or [])])

alt = {a["pfad"]: a["sha256"] for a in (m.get("artefakte") or [])}
(daten / "key_levels.json").write_text('{"c":4}', encoding="utf-8")
gk.marke_schreiben("L1", _SESSION, fertig=True)
m2 = _marke()
neu = {a["pfad"]: a["sha256"] for a in (m2.get("artefakte") or [])}
pruef("ein geaendertes Artefakt aendert seinen Hash",
      any(alt[p] != neu[p] for p in alt), [p for p in alt if alt[p] != neu[p]])

# ───────────────────── 3 die echte Kette ────────────────────────────────────────
print("\n[3] gex_kette.main() — echte Funktion, Teilschritte als Attrappe")


def _attrappe(schritte):
    """_lauf ersetzen: je Aufruf (rc, ausgabe) aus der Liste, Aufrufe werden protokolliert."""
    protokoll = []

    def f(argv):
        i = len(protokoll)
        protokoll.append(list(argv))
        return schritte[i] if i < len(schritte) else (1, "")
    return f, protokoll


# (a) Glücklicher Fall
_marke_weg()
gk._lauf, prot = _attrappe([(0, "[lauf] {lauf} %s\n[ergebnis] veroeffentlicht\n" % _SESSION),
                            (0, "ok")])
# Die Kennung kennt nur die Kette — die Attrappe muss sie aus dem Argument nehmen.
def _lauf_echo(argv):
    prot.append(list(argv))
    if "snapshot_gex_massive.py" in argv[0]:
        kennung = argv[argv.index("--lauf") + 1]
        return 0, "[lauf] %s %s\n[ergebnis] veroeffentlicht\n" % (kennung, _SESSION)
    return 0, "ok"


gk._lauf = _lauf_echo
rc = gk.main([])
pruef("glueckliche Kette: Exit 0", rc == 0, rc)
m = _marke()
pruef("Abschlussmarke gesetzt", m.get("fertig") is True and m.get("session") == _SESSION, m.get("session"))
kl = [a for a in prot if "compute_key_levels.py" in a[0]]
pruef("Key Levels wurde MIT --lauf und --gex-datei gerufen",
      bool(kl) and "--lauf" in kl[0] and "--gex-datei" in kl[0], kl[0] if kl else None)
pruef("die uebergebene Kennung ist die der Marke",
      bool(kl) and _arg(kl[0], "--lauf") == m.get("lauf"),
      (_arg(kl[0], "--lauf") if kl else None, m.get("lauf")))

# (b) Snapshot meldet eine ANDERE Kennung — kein Weitermachen
_marke_weg()
prot.clear()
gk._lauf = lambda argv: (0, "[lauf] FREMD %s\n[ergebnis] veroeffentlicht\n" % _SESSION)
rc = gk.main([])
pruef("fremde Kennung -> Abbruch mit 1", rc == 1, rc)
m = _marke()
pruef("Versuchseintrag bleibt, aber nicht fertig", m.get("fertig") is False)

# (c) Abbruch ZWISCHEN den Schritten: Key Levels scheitert
_marke_weg()


def _kl_scheitert(argv):
    if "snapshot_gex_massive.py" in argv[0]:
        kennung = argv[argv.index("--lauf") + 1]
        return 0, "[lauf] %s %s\n[ergebnis] veroeffentlicht\n" % (kennung, _SESSION)
    return 1, "kaputt"


gk._lauf = _kl_scheitert
rc = gk.main([])
pruef("Key Levels scheitert -> Exit 1", rc == 1, rc)
m = _marke()
pruef("KEIN Abschluss nach gescheitertem zweiten Schritt", m.get("fertig") is False, m)
# Die Session steht hier schon drin: nach dem veroeffentlichten Snapshot schreibt die
# Kette den Versuchseintrag erneut und ergaenzt sie. Meine erste Fassung erwartete None
# und war damit falsch — nicht der Code (vom Waechter selbst gemeldet).
pruef("der Versuch ist festgehalten, mit Session und ohne Abschluss",
      bool(m.get("lauf")) and m.get("fertig") is False and m.get("session") == _SESSION,
      (m.get("session"), m.get("fertig")))

# (d) Snapshot uebersprungen: Key Levels laeuft nicht, keine Marke
_marke_weg()
prot.clear()


def _uebersprungen(argv):
    prot.append(list(argv))
    return 0, "[ergebnis] uebersprungen (kein Handelstag)\n"


gk._lauf = _uebersprungen
rc = gk.main([])
pruef("uebersprungener Snapshot -> Exit 0", rc == 0, rc)
pruef("Key Levels wurde NICHT gerufen",
      not any("compute_key_levels.py" in a[0] for a in prot))
m = _marke()
pruef("Versuchseintrag existiert auch dann (nicht 'nie versucht')",
      bool(m) and m.get("fertig") is False, m or "KEINE Marke")

# (e) Pflichtartefakt fehlt -> kein Abschluss, Exit 1
_marke_weg()
(daten / "key_levels.json").unlink()
gk._lauf = _lauf_echo
rc = gk.main([])
pruef("fehlendes Pflichtartefakt -> Exit 1 trotz gruener Teilschritte", rc == 1, rc)
m = _marke()
pruef("Marke bleibt unfertig und benennt das Fehlende",
      m.get("fertig") is False and "key_levels.json" in " ".join(m.get("fehlend") or []),
      m.get("fehlend"))
(daten / "key_levels.json").write_text('{"c":3}', encoding="utf-8")

# ───────────────────── 4 _load_gex mit fremder Kennung ──────────────────────────
print("\n[4] compute_key_levels._load_gex — Laufbindung")
import compute_key_levels as ckl                                       # noqa: E402

ckl._ROOT = _TMP
fremd = _TMP / "fremd.json"
fremd.write_text(json.dumps({"stempel_art": "session", "session": _SESSION,
                             "lauf": "ANDERER", "tickers": [{"ticker": "SPY"}]}),
                 encoding="utf-8")
g, status = ckl._load_gex(date(2026, 10, 21), str(fremd), "MEINER")
pruef("fremde Kennung -> nichts uebernommen", g == {} and status.startswith("anderer_lauf"),
      status)
g, status = ckl._load_gex(date(2026, 10, 21), str(fremd), "ANDERER")
pruef("passende Kennung -> uebernommen", status == "ok" and "SPY" in g, status)
g, status = ckl._load_gex(date(2026, 10, 21), str(fremd), None)
pruef("ohne Kennung bleibt das alte Verhalten (Session entscheidet)", status == "ok", status)

# Die Kennung muss in der AUSGABE stehen — ohne diese Pruefung bliebe unbemerkt, wenn
# build() sie verschweigt (vom Mutationstest gefangen: die Pruefung darueber vergleicht
# nur das Argument mit der Marke und sieht key_levels.json nie an).
ckl._get = lambda url, key, tries=4: {"status": "OK", "next_url": None, "results": [
    {"details": {"expiration_date": "2026-10-23", "contract_type": t2, "strike_price": K},
     "open_interest": 100} for K in (100.0, 101.0, 102.0) for t2 in ("call", "put")]}
ckl.letzte_session = lambda boerse: date(2026, 10, 21)
aus = ckl.build(["SPY"], write=False, gex_datei=str(fremd), lauf="ANDERER")
pruef("die Kennung steht in der Ausgabe von build()", aus.get("lauf") == "ANDERER",
      aus.get("lauf"))

gescheitert = False
try:
    ckl.build(["SPY"], write=False, gex_datei=str(fremd), lauf="MEINER")
except ckl.LaufFremd:
    gescheitert = True
except Exception as e:                       # Session/Netz — anderer Grund, nicht gewertet
    gescheitert = isinstance(e, ckl.LaufFremd)
pruef("build() bricht bei fremder Kennung ab, statt zu mischen", gescheitert)

# ───────────────────── 5 Sperre mit zwei echten Prozessen ───────────────────────
print("\n[5] exklusive Kettensperre (zwei Prozesse)")
try:
    import fcntl                                                        # noqa: F401
    hat_fcntl = True
except ImportError:
    hat_fcntl = False

if not hat_fcntl:
    pruef("[Aufbau] ohne fcntl nicht pruefbar (Windows) — unter Linux Pflicht", True,
          "uebersprungen")
else:
    halter = textwrap.dedent("""
        import sys, time
        sys.path.insert(0, %r)
        from shared.atomic_json import exklusive_sperre
        with exklusive_sperre(%r, frist_s=0, name="probe"):
            print("HABE", flush=True)
            time.sleep(5)
    """) % (str(_WURZEL), str(_TMP / "k.lock"))
    zweiter = textwrap.dedent("""
        import sys
        sys.path.insert(0, %r)
        from shared.atomic_json import SperreBelegt, exklusive_sperre
        try:
            with exklusive_sperre(%r, frist_s=0, name="probe"):
                print("AUCH")
        except SperreBelegt as e:
            print("BELEGT")
    """) % (str(_WURZEL), str(_TMP / "k.lock"))
    p1 = subprocess.Popen([sys.executable, "-u", "-c", halter], stdout=subprocess.PIPE,
                          text=True)
    assert p1.stdout.readline().strip() == "HABE"
    p2 = subprocess.run([sys.executable, "-c", zweiter], capture_output=True, text=True,
                        timeout=30)
    pruef("zweiter Prozess kommt nicht herein", "BELEGT" in p2.stdout, p2.stdout.strip())
    p1.kill()
    p1.wait()
    p3 = subprocess.run([sys.executable, "-c", zweiter], capture_output=True, text=True,
                        timeout=30)
    pruef("nach dem Ende des ersten ist die Sperre frei", "AUCH" in p3.stdout,
          p3.stdout.strip())

print("\nPROBE-ENDE %d" % _n)
if _fehler:
    print("\n[FEHLER] %d von %d Pruefungen rot" % (_fehler, _n))
    sys.exit(1)
print("\n[OK] alle %d Pruefungen gruen" % _n)
