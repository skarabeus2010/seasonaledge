#!/usr/bin/env python3
"""
verify_session_mutation.py — prueft den Session-Waechter, nicht den Code.

Baut jeden Fehler, der beim Session-Vorfall 2026-09-25 und in den fuenf
Codex-Review-Runden danach real war, ABSICHTLICH wieder ein und verlangt, dass
`scripts/verify_session_stamp.py` rot wird.

Warum als eigenes Skript: der Waechter bestand in dieser Serie dreimal, obwohl
er den Fehler nicht fangen konnte — die erste Mutationsprobe rechnete in ET statt
UTC (R1), die Sperre wurde nur per Textsuche geprueft (R3), und ein Rueckfall
der Crons auf date.today() blieb gruen (R5). Erst diese Batterie hat jeweils
gezeigt, wo der Waechter Scheinsicherheit war — und sie gehoert deshalb in den
Bestand, nicht in eine Shell-Sitzung.

Sicherheit beim Schreiben: Lock, Bytes, atomares Ersetzen und nachgewiesene
Wiederherstellung kommen aus `verify_twins_mutation.py` — bewusst importiert,
nicht kopiert (Kopien driften). Zusaetzlich wird nachgewiesen, dass die echten
Cron-Ausgaben unter landing/data/ unberuehrt bleiben: in Runde 3 hat eine
Mutationsprobe eine leere options_flow.json auf die Platte gelegt.

Nutzung:  PYTHONUTF8=1 py -3.14 scripts/verify_session_mutation.py
Exit 0 = jede Mutation wurde erkannt, 1 = mindestens eine blieb unbemerkt.
"""
from __future__ import annotations
import hashlib
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.verify_twins_mutation import (LF, LockBelegt, _atomar_schreiben,  # noqa: E402
                                           _exklusiver_lauf, _zeilenende)

_WAECHTER = _ROOT / "scripts" / "verify_session_stamp.py"
_WAECHTER_ANZEIGE = _ROOT / "scripts" / "verify_skew_anzeige.py"
SK, FL, EH = ("scripts/compute_options_skew.py", "scripts/compute_options_flow.py",
              "shared/exchange_holidays.py")

# (Herkunft, Beschreibung, Datei, Suchtext, Ersatztext)
MUTATIONEN = [
    ("Vorfall", "Skew-_last_session faellt auf date.today() zurueck", SK,
     '        return letzte_session("NYSE").isoformat()', '        d = date.today()'),
    ("Vorfall", "Flow stempelt wieder mit date.today()", FL,
     '    today = letzte_session("NYSE").isoformat()', '    today = date.today().isoformat()'),
    ("Vorfall", "Schlusszeit-Regel in shared entfernt", EH,
     "        d -= timedelta(days=1)\n    for _ in range(12):",
     "        pass\n    for _ in range(12):"),
    ("R1", "Skew-dte wieder gegen date.today()", SK,
     "    today = date.fromisoformat(_last_session()); by = {}",
     "    today = date.today(); by = {}"),
    ("R1", "Flow-dte wieder gegen date.today()", FL,
     "    today = date.fromisoformat(session); out = []",
     "    today = date.today(); out = []"),
    ("R1", "noatm wieder als rankbar behandelt", SK,
     '_RANKBAR = ("cm", "cm_extrap")', '_RANKBAR = ("cm", "cm_extrap", "noatm")'),
    ("R2", "Skew-Handelszeitsperre entfernt", SK,
     '        pruefe_eod_fenster("compute_options_skew")', "        pass"),
    ("R3", "Flow-Sperre hinter if False", FL,
     '        pruefe_eod_fenster("compute_options_flow")',
     '        if False: pruefe_eod_fenster("x")'),
    ("R3", "Skew-Sperre lokal als No-op", SK,
     "def build(tickers: list[str], write: bool = True) -> dict:",
     "def build(tickers: list[str], write: bool = True) -> dict:\n"
     "    pruefe_eod_fenster = lambda *a, **k: None"),
    ("R3", "Flow-_save_hist wieder unbedingt (--no-write schreibt)", FL,
     "    if write:\n        _save_hist(sym, hist[-_HIST_KEEP:])",
     "    _save_hist(sym, hist[-_HIST_KEEP:])"),
    ("R4", "write-Weitergabe _enrich -> _doi gerissen", FL,
     "    doi = _doi(sym, recs, spot, today, write)", "    doi = _doi(sym, recs, spot, today)"),
    ("R4", "write-Weitergabe build -> _enrich gerissen", FL,
     "            r = _enrich(t, tok, today, write)", "            r = _enrich(t, tok, today)"),
    ("R4", "Netzzugriff vor der Sperre (von except Exception geschluckt)", FL,
     '        pruefe_eod_fenster("compute_options_flow")',
     '        _spot("SPY", "offline-probe")\n        pruefe_eod_fenster("compute_options_flow")'),
    ("R5", "Flow schreibt am _ROOT vorbei ins echte Repo", FL,
     '    d = _ROOT / "landing/data/oi_history"',
     '    d = Path(__file__).resolve().parent.parent / "landing/data/oi_history"'),
    ("R6", "Skew schreibt ohne Schluessel eine leere Ausgabe (Exit 0)", SK,
     "    if write and not tok:", "    if False:"),
    ("R6", "Flow legt in der Handelszeit ein leeres Verzeichnis an", FL,
     '        pruefe_eod_fenster("compute_options_flow")',
     '        (_ROOT / "rogue-dir").mkdir(parents=True, exist_ok=True)\n'
     '        pruefe_eod_fenster("compute_options_flow")'),
    ("R6", "Import-Nebenwirkung taeuscht eine gruene Bilanz vor", SK,
     "_RANKBAR = (\"cm\", \"cm_extrap\")",
     "_RANKBAR = (\"cm\", \"cm_extrap\")\nprint('ISOLIERT-BILANZ ' + '0' * 32 + ' 0 explizit', flush=True)"),
    # -- Anzeige = Ranking + Frische-Filter (Befund 2026-09-25).
    #    6. Element: zustaendiger Waechter ist verify_skew_anzeige.py.
    ("Anzeige", "Frische-Filter abgeschaltet (veraltete Kurse wieder drin)", SK,
     "_NUR_SESSIONSKURSE = True", "_NUR_SESSIONSKURSE = False", "anzeige"),
    ("Anzeige", "Kursdatum in UTC statt ET", SK,
     'return datetime.fromtimestamp(lu / 1e9, ZoneInfo("America/New_York")).date().isoformat()',
     'return datetime.fromtimestamp(lu / 1e9, ZoneInfo("UTC")).date().isoformat()', "anzeige"),
    ("Anzeige", "nicht rankbare Tage zeigen wieder Anbieterwerte", SK,
     "    if not _rankbar(r):\n        for k in _ANZEIGE_FELDER:\n            r[k] = None\n        return",
     "    if not _rankbar(r):\n        return", "anzeige"),
    ("Anzeige", "Anzeige-Umstellung nicht aufgerufen", SK,
     "    _anzeige_aus_ranking(r)\n    return r\n", "    return r\n", "anzeige"),
    ("Anzeige", "History-Fallback liest wieder die geleerten Top-Level-Felder", SK,
     '                fp = t.get("front_provider") or t', "                fp = t", "anzeige"),
    ("Anzeige", "single/noatm gelten in der Anzeige als rankbar", SK,
     "    if not _rankbar(r):\n        for k in _ANZEIGE_FELDER:",
     '    if not r.get("cm_mode"):\n        for k in _ANZEIGE_FELDER:', "anzeige"),
]


def _waechter_gruen(waechter: Path = _WAECHTER) -> bool:
    r = subprocess.run([sys.executable, str(waechter)], capture_output=True,
                       text=True, cwd=str(_ROOT), timeout=900)
    return r.returncode == 0


def _alle_gruen() -> bool:
    return _waechter_gruen(_WAECHTER) and _waechter_gruen(_WAECHTER_ANZEIGE)


def _daten_fingerabdruck() -> str:
    """Hash ueber die echten Cron-Ausgaben, die ein fehlerhafter Lauf treffen koennte."""
    h = hashlib.sha256()
    for rel in ("landing/data/options_flow.json", "landing/data/options_skew.json",
                "landing/data/options_skew_history.json"):
        p = _ROOT / rel
        h.update(rel.encode() + (p.read_bytes() if p.exists() else b"<fehlt>"))
    oi = _ROOT / "landing/data/oi_history"
    for p in sorted(oi.glob("*.json")) if oi.exists() else []:
        h.update(p.name.encode() + p.read_bytes())
    return h.hexdigest()


def main() -> int:
    print("=" * 78)
    print("Mutationstest Session-Waechter: wird er rot, wenn der Fehler zurueckkommt?")
    print("=" * 78)
    if not _alle_gruen():
        print("\n[ABBRUCH] Ein Waechter ist schon vor der ersten Mutation ROT.")
        return 1
    daten_vorher = _daten_fingerabdruck()
    print("\nAusgangslage: Waechter gruen.\n")

    unbemerkt, beschaedigt = [], []
    for nr, (herkunft, beschreibung, datei, suchen, ersetzen, *art) in enumerate(MUTATIONEN, 1):
        waechter = _WAECHTER_ANZEIGE if art and art[0] == "anzeige" else _WAECHTER
        pfad = _ROOT / datei
        original = pfad.read_bytes()
        le = _zeilenende(original)
        such_b = suchen.encode("utf-8").replace(LF, le)
        ersatz_b = ersetzen.encode("utf-8").replace(LF, le)
        n = original.count(such_b)
        if n != 1:
            print(f"{nr:>2}. [UNGUELTIG] ({herkunft}) {beschreibung} — Suchtext {n}x in {datei}")
            unbemerkt.append(f"{beschreibung} (Suchtext {n}x)")
            continue
        try:
            _atomar_schreiben(pfad, original.replace(such_b, ersatz_b, 1))
            erkannt = not _waechter_gruen(waechter)
        finally:
            _atomar_schreiben(pfad, original)
            if pfad.read_bytes() != original:                 # nachweisen, nicht hoffen
                beschaedigt.append(datei)
                print(f"      [ALARM] {datei} nicht wiederhergestellt — "
                      f"`git checkout -- {datei}` ausfuehren!")
        print(f"{nr:>2}. {'[erkannt]  ' if erkannt else '[UNBEMERKT]'} ({herkunft:<7}) {beschreibung}")
        if not erkannt:
            unbemerkt.append(beschreibung)

    print("\n" + "=" * 78)
    fehler = False
    if beschaedigt:
        print(f"[FAIL] Nicht wiederhergestellt: {', '.join(sorted(set(beschaedigt)))}")
        fehler = True
    if _daten_fingerabdruck() != daten_vorher:
        print("[FAIL] Echte Cron-Ausgaben unter landing/data/ wurden veraendert — "
              "die Isolation des Waechters hat versagt.")
        fehler = True
    if not _alle_gruen():
        print("[FAIL] Nach dem Test ist der Waechter rot — `git diff` pruefen!")
        fehler = True
    if unbemerkt:
        print(f"[FAIL] {len(unbemerkt)} von {len(MUTATIONEN)} Mutationen blieben unbemerkt:")
        for u in unbemerkt:
            print(f"   - {u}")
        fehler = True
    if fehler:
        return 1
    print(f"[OK] Alle {len(MUTATIONEN)} Mutationen erkannt, Quellen und Cron-Ausgaben "
          f"nachweislich unveraendert.")
    return 0


if __name__ == "__main__":
    try:
        with _exklusiver_lauf():
            sys.exit(main())
    except LockBelegt as e:
        print(f"[ABBRUCH] {e}")
        sys.exit(1)
