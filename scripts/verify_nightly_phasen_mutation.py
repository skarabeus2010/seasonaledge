#!/usr/bin/env python3
"""
verify_nightly_phasen_mutation.py — prüft den Wächter verify_nightly_phasen.py: baut die Fehler aus dem Audit
2026-11-15 wieder ein und verlangt Rot AN DER BENANNTEN PRÜFUNG (eine andere rote Zeile ist kein Nachweis).
Mechanik (Sperre, Bytes, atomares Schreiben, frischer Bytecode-Cache) aus verify_twins_mutation.
"""
from __future__ import annotations
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
from scripts.verify_twins_mutation import (_exklusiver_lauf, _zeilenende, _atomar_schreiben,  # noqa: E402
                                           python_probe, LF)

_WAECHTER = _ROOT / "scripts" / "verify_nightly_phasen.py"
NR, HC, CM = "scripts/nightly_refresh.py", "scripts/daily_health_check.py", "shared/cache_manager.py"

MUTATIONEN = [
    ("Health: PHASE-Eintrag nicht rot", HC,
     "    if phasen:\n        # Der Nightly endete rot",
     "    if False:\n        # Der Nightly endete rot",
     "Health PHASE → rot"),
    ("Health: erwarteter Nightly-Tag nicht geprüft", HC,
     "    if erwartet is not None and (run_d is None or run_d < erwartet):",
     "    if False:",
     "Health Vortageszeile bei fehlendem Lauf"),
    ("Health: Puffer nicht abgewartet", HC,
     "    if jetzt_ny < start + timedelta(hours=NIGHTLY_PUFFER_H):",
     "    if jetzt_ny < start:",
     "Health erwarteter Nightly-Tag 2026-11-15T23:00"),
    ("Health-Check ruft ohne erwarteten Tag", HC,
     "        status, detail = bewerte_nightly(last, now_utc.date(), erwarteter_nightly_tag(now_utc))",
     "        status, detail = bewerte_nightly(last, now_utc.date())",
     "Health Aufruf mit erwartetem Tag"),
    ("refresh_log ohne gescheiterte Phasen", NR,
     '    errs = [f"PHASE: {p}"[:200] for p in gescheitert] + list(health_errors[:20])',
     "    errs = list(health_errors[:20])",
     "Haupt Saison-Score → PHASE im refresh_log"),
    ("refresh_log-Fehler verschluckt", NR,
     '        _FEHLGESCHLAGEN.append("refresh_log")',
     "        pass",
     "Haupt refresh_log scheitert"),
    ("Backfill-Abfragefehler verschluckt", NR,
     '                backfill_fehler.append(f"{_bf_ticker}: {str(_qe)[:80]}")',
     "                pass",
     "Haupt Backfill"),
    ("Kalender-Fehler verschluckt", NR,
     '        print(f"Calendar sync failed: {e}")\n        _FEHLGESCHLAGEN.append("Calendar-Sync")',
     '        print(f"Calendar sync failed: {e}")',
     "Haupt Kalender"),
    ("refresh_log wieder vor Phase J", NR,
     [("    # Phase F: Weekly Newsletter",
       "    _schreibe_refresh_log(tickers, missing_details, health_errors, health_ungeprueft, 0, regime_status, t_start)\n"
       "    # Phase F: Weekly Newsletter"),
      ("    if not _schreibe_refresh_log(tickers, missing_details, health_errors, health_ungeprueft,\n"
       "                                 auto_fixed + backfill_fixed, regime_status, t_start):\n"
       '        _FEHLGESCHLAGEN.append("refresh_log")',
       "    pass")],
     None,
     "Haupt Wahl-Studie"),
    ("tdom-Schreibfehler verschluckt", CM,
     '        app_logger.error(f"cache_manager: DB-Upsert tdom_stats {ticker} {strategy} fehlgeschlagen: {e}")\n'
     "        if schreibfehler_werfen:\n            raise",
     '        app_logger.error(f"cache_manager: DB-Upsert tdom_stats {ticker} {strategy} fehlgeschlagen: {e}")',
     "Cache tdom wirft"),
    ("tdoy-Schreibfehler verschluckt", CM,
     '        app_logger.error(f"cache_manager: DB-Upsert tdoy_stats {ticker} {strategy} fehlgeschlagen: {e}")\n'
     "        if schreibfehler_werfen:\n            raise",
     '        app_logger.error(f"cache_manager: DB-Upsert tdoy_stats {ticker} {strategy} fehlgeschlagen: {e}")',
     "Cache tdoy wirft"),
    ("Nightly ruft TDOM/TDOY ohne Weitergabe", NR,
     '_fn(ticker, df, strategy=strategy, direction="forward", schreibfehler_werfen=True)',
     '_fn(ticker, df, strategy=strategy, direction="forward")',
     "Ticker tdoy-Schreibfehler"),
    ("Marktkalender-Fehler verschluckt", NR,
     '            _FEHLGESCHLAGEN.append("Marktkalender")',
     "            pass",
     "Haupt Marktkalender scheitert"),
    ("Health: Kalenderinhalt nicht geprüft", HC,
     '            if erstes < grenze.isoformat():',
     "            if False:",
     "Kalender frisches Datum, alter Inhalt"),
    ("Health: Dateialter > 4 Tage nur gelb", HC,
     '        if tage > 4:\n            alt.append(f"{name} {tage:.0f} T.")\n            schlimmst = "red"',
     '        if tage > 4:\n            alt.append(f"{name} {tage:.0f} T.")\n            schlimmst = "yellow"',
     "Ausgaben 6 Tage"),
    ("getAll gibt Teilbestand zurück", "landing/js/app.js",
     "        if (!Array.isArray(rows)) {\n",
     "        if (!Array.isArray(rows)) { return results;\n",
     "getAll Fehlerantwort"),
]


def main() -> int:
    unbemerkt, ungueltig = [], []
    with _exklusiver_lauf():
        r0 = python_probe([_WAECHTER], capture_output=True, text=True, cwd=str(_ROOT))
        if r0.returncode != 0:
            print("[FAIL] Wächter ist schon ohne Mutation rot:\n" + r0.stdout[-2000:])
            return 1
        for nr, (name, datei, such, ersatz, pruefung) in enumerate(MUTATIONEN, 1):
            pfad = _ROOT / datei
            original = pfad.read_bytes()
            le = _zeilenende(original)
            paare = such if isinstance(such, list) else [(such, ersatz)]   # mehrere Anker in derselben Datei
            mutiert, gueltig = original, True
            for a, b in paare:
                s, e = a.encode("utf-8").replace(LF, le), b.encode("utf-8").replace(LF, le)
                if mutiert.count(s) != 1:
                    print(f"{nr:>2}. [UNGUELTIG] {name} — Anker {mutiert.count(s)}x")
                    gueltig = False
                    break
                mutiert = mutiert.replace(s, e, 1)
            if not gueltig:
                ungueltig.append(name)
                continue
            try:
                _atomar_schreiben(pfad, mutiert)
                r = python_probe([_WAECHTER], capture_output=True, text=True, cwd=str(_ROOT))
            finally:
                _atomar_schreiben(pfad, original)
                assert pfad.read_bytes() == original, f"{datei} nicht wiederhergestellt"
            fehl = [z for z in r.stdout.splitlines() if z.strip().startswith("FEHL")]
            if any("[Ausnahme]" in z for z in fehl):
                print(f"{nr:>2}. [Absturz]   {name} — kein Nachweis: {fehl[0][:120]}"); ungueltig.append(name)
            elif r.returncode == 1 and any(f"[{pruefung}" in z for z in fehl):
                print(f"{nr:>2}. [erkannt]   {name}")
            else:
                print(f"{nr:>2}. [UNBEMERKT] {name} (Exit {r.returncode}, rot: {[z[:60] for z in fehl]})")
                unbemerkt.append(name)
    print()
    if unbemerkt or ungueltig:
        print(f"[FAIL] unbemerkt {len(unbemerkt)}, ungültig {len(ungueltig)} von {len(MUTATIONEN)}")
        return 1
    print(f"[OK] Alle {len(MUTATIONEN)} Mutationen an der benannten Prüfung erkannt.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
