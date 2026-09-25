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
_WAECHTER_LAUFZEITEN = _ROOT / "scripts" / "verify_skew_laufzeiten.py"
_WAECHTER_JE_ART = {"anzeige": _WAECHTER_ANZEIGE, "laufzeiten": _WAECHTER_LAUFZEITEN}
SK, FL, EH = ("scripts/compute_options_skew.py", "scripts/compute_options_flow.py",
              "shared/exchange_holidays.py")
BS = "shared/black_scholes.py"

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
     # Verankert an der Aufrufzeile SELBST: zweimal hing die Mutation an einer
     # Nachbarzeile, die ein spaeterer Umbau verschob, und meldete "UNGUELTIG".
     "    _anzeige_aus_ranking(r)\n    # Der NAECHSTE Verfall",
     "    # Der NAECHSTE Verfall", "anzeige"),
    ("Anzeige", "History-Fallback liest wieder die geleerten Top-Level-Felder", SK,
     '                fp = t.get("front_provider") or t', "                fp = t", "anzeige"),
    ("Anzeige", "Produktivcode schreibt beim Anzeige-Umbau ins echte Repo (Codex R1)", SK,
     '    fp = r.setdefault("front_provider", {})',
     '    Path(__file__).resolve().parent.parent.joinpath("landing/data/options_skew.json").write_text("{}")\n'
     '    fp = r.setdefault("front_provider", {})', "anzeige"),
    # -- NE/Skew-Term/Term/Smile aus eigener Rechnung (2026-09-25),
    #    Waechter verify_skew_laufzeiten.py
    ("Laufzeit", "Ticker ohne Anbieter-Pick wieder verworfen", SK,
     "    if not s30 and not r.get(\"cm_mode\"):", "    if not s30:", "laufzeiten"),
    ("Laufzeit", "ohne Session-Schluss sickern Anbieterwerte durch", SK,
     "    if not by_own or not spot_ref:\n        return\n",
     "    if not by_own or not spot_ref:\n"
     "        r.update({k: v for k, v in (r.get(\"front_provider\") or {}).items()\n"
     "                  if k in (\"skew_ne_pts\", \"term\", \"skew_curve\", \"contango\")})\n"
     "        return\n", "laufzeiten"),
    ("Laufzeit", "NE wieder mit Monatsvorzug (war faktisch der Front-Monat)", SK,
     "    ne, leg_ne = ne_roh, (_leg(ne_roh) if ne_roh else None)",
     "    ne = _nearest_exp(by_own, 1, prefer_monthly=True); leg_ne = _leg(ne)", "laufzeiten"),
    ("Laufzeit", "NE wieder aus der gefilterten statt der rohen Kette (Codex R1, HOCH)", SK,
     "    ne_dte_roh = (roh_dte or [by_own[laufend[0]][\"dte\"]])[0]",
     "    ne_dte_roh = by_own[laufend[0]][\"dte\"]", "laufzeiten"),
    ("Laufzeit", "Kursraster-Unsicherheit markiert nie 'Richtung unbestimmt' (Codex R1)", SK,
     "            r[\"skew_ne_richtung_unsicher\"] = bool(lo <= 0 <= hi)",
     "            r[\"skew_ne_richtung_unsicher\"] = False", "laufzeiten"),
    ("Laufzeit", "Vergleich wieder ueber gerundete Halbbreite statt Intervall (Codex R2)", SK,
     "            r[\"skew_ne_richtung_unsicher\"] = bool(lo <= 0 <= hi)",
     "            r[\"skew_ne_richtung_unsicher\"] = bool(round((hi - lo) / 2, 3) >= abs(r[\"skew_ne_pts\"]))",
     "laufzeiten"),
    ("Laufzeit", "Kennzahl wieder halbe Intervallbreite statt groesster Abstand (Codex R3)", SK,
     "max(sk_roh - lo, hi - sk_roh)", "(hi - lo) / 2", "laufzeiten"),
    ("Laufzeit", "Kursraster pauschal ein Cent (Codex R2)", BS,
     "    cents = round(px * 100)\n    if cents % 5:",
     "    return 0.01\n    cents = round(px * 100)\n    if cents % 5:", "laufzeiten"),
    ("Laufzeit", "NE ohne Verfall stuerzt die Smile-Rechnung ab (Ticker faellt aus)", SK,
     "    sc[\"iv_ne\"] = _kurve(_smile(ne), ersatz_ne) if ne else None",
     "    sc[\"iv_ne\"] = _kurve(_smile(ne), ersatz_ne)", "laufzeiten"),
    ("Laufzeit", "Frontend: NE-Kurve verschwindet wieder ohne 30-Tage-Kurve", "landing/pages/skew.html",
     "      if(!sc||(!sc.iv30&&!sc.iv_ne)){", "      if(!sc||!sc.iv30){", "laufzeiten"),
    ("Laufzeit", "Frontend: feste Farbfolge, NE-Kurve bekommt die 30-Tage-Farbe", "landing/pages/skew.html",
     "series:series,colors:farben,", "series:series,colors:[ACC,BLUE],", "laufzeiten"),
    ("Laufzeit", "NE-Ersatz ohne Kennzeichnung", SK,
     "                r[\"skew_ne_ersatz\"] = True", "                r[\"skew_ne_ersatz\"] = False",
     "laufzeiten"),
    ("Laufzeit", "NE-Ersatz ohne 10-Tage-Grenze", SK,
     "            if by_own[e][\"dte\"] > _NE_MAX_DTE:\n                break",
     "            if False:\n                break", "laufzeiten"),
    ("Laufzeit", "Contango wieder mit jedem Punkt unter 30 Tagen", SK,
     "    kurz = [t for t in (term or []) if t[\"dte\"] <= _KONTANGO_KURZ_MAX]",
     "    kurz = [t for t in (term or []) if t[\"dte\"] < _CM_DAYS]", "laufzeiten"),
    ("Laufzeit", "Contango-Gleichstand wieder als Backwardation", SK,
     "    if kurz[0][\"iv\"] > iv30:\n        return False\n    return None",
     "    return False", "laufzeiten"),
    ("Laufzeit", "ATM-Anker ohne Sigma-Grenze", BS,
     "    if klammer[\"max_abstand\"] > ATM_MAX_MONEYNESS or z > ATM_MAX_SIGMA:",
     "    if klammer[\"max_abstand\"] > ATM_MAX_MONEYNESS:", "laufzeiten"),
    ("Laufzeit", "Term wieder mit Fluegelzwang (ueber leg_from_prices)", SK,
     "        atm = atm_from_prices(None, spot_ref, by_own[ex][\"dte\"], _punkte=g) if g else None",
     "        atm = (_leg(ex) or {}).get(\"iv_atm\")", "laufzeiten"),
    ("Laufzeit", "front_provider wird in der Anzeige wieder ueberschrieben", SK,
     "    fp = r.setdefault(\"front_provider\", {})", "    fp = r[\"front_provider\"] = {}",
     "laufzeiten"),
    ("Laufzeit", "leg_from_prices: Referenz-IV vorzeitig gerundet", BS,
     "    return gueltig, iv_atm, T, klammer", "    return gueltig, round(iv_atm, 3), T, klammer",
     "laufzeiten"),
    ("Anzeige", "single/noatm gelten in der Anzeige als rankbar", SK,
     "    if not _rankbar(r):\n        for k in _ANZEIGE_FELDER:",
     '    if not r.get("cm_mode"):\n        for k in _ANZEIGE_FELDER:', "anzeige"),
]


def _waechter_gruen(waechter: Path = _WAECHTER) -> bool:
    r = subprocess.run([sys.executable, str(waechter)], capture_output=True,
                       text=True, cwd=str(_ROOT), timeout=900)
    return r.returncode == 0


def _alle_gruen() -> bool:
    return all(_waechter_gruen(w) for w in (_WAECHTER, _WAECHTER_ANZEIGE, _WAECHTER_LAUFZEITEN))


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
        waechter = _WAECHTER_JE_ART.get(art[0], _WAECHTER) if art else _WAECHTER
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
