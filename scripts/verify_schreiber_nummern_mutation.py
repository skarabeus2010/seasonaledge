# -*- coding: utf-8 -*-
"""Prüft den Wächter, nicht den Code: baut die alten Schreibfehler (Zeilenzählung, „Vorzeile + 1“,
Erfolg ohne Schreiben, fehlende Grenzen) wieder ein und verlangt, dass verify_schreiber_nummern.py ROT wird —
an der benannten Prüfung.

    py -3.14 scripts/verify_schreiber_nummern_mutation.py

Beweisregeln wie in den übrigen Mutationstests: Endmarker `PROBE-ENDE` muss erreicht sein ·
jede Mutation BENENNT die Prüfung, die sie reißen muss · eine Ausnahme gilt nie als
Nachweis, auch eine eingefangene (`[Ausnahme]`) nicht · ein Anker, der nicht genau einmal
trifft, macht die Mutation ungültig · `UNGUELTIG_ERWARTET` prüft das Urteil dieses Tests.
"""
from __future__ import annotations

import io
import os
import pathlib
import re
import sys

# Atomares Schreiben mit Wiederholung — IMPORTIERT, nicht kopiert (deterministisch, v65.1/v66.5).
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from scripts.verify_twins_mutation import (LockBelegt, _atomar_schreiben,  # noqa: E402
                                           _exklusiver_lauf, python_probe)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

IR = "scripts/intraday_refresh.py"
NR = "scripts/nightly_refresh.py"
BN = "scripts/backfill_new_ticker.py"
OB = "scripts/onboard_ticker.py"
FM = "scripts/fix_missing_days.py"
BT = "scripts/backfill_tdoy.py"
EH = "shared/exchange_holidays.py"
SC = "shared/supabase_client.py"
PROBE = "scripts/verify_schreiber_nummern.py"

MUTATIONEN = [
    ("Nightly schreibt wieder die Zeilenzählung aus preprocess()",
     NR, '                        _rec["tdom"], _rec["tdoy"] = _nummern[_rec["date"]]',
     '                        _rec["tdom"], _rec["tdoy"] = int(_row["tdom"]), int(_row["tdoy"])',
     "[Nightly Kalendernummern trotz Lücke]"),
    # Codex P2 R1: der Wächter prüfte keine exakte Schreibmenge.
    ("Nightly schreibt nur die letzte Zeile",
     NR, "                if _price_records:\n                    upsert_prices(_price_records)",
     "                if _price_records:\n                    upsert_prices(_price_records[-1:])",
     "[Nightly Kalendernummern trotz Lücke]"),
    # Codex P2 R1 (P1): ein gemischter Upsert setzt fehlende Spalten auf NULL — Bestand verloren.
    ("upsert_prices mischt Spaltensätze wieder in einer Anfrage",
     SC, "        gruppen.setdefault(frozenset(r), []).append(r)",
     "        gruppen.setdefault(frozenset(), []).append(r)",   # alles in eine Anfrage, wie vor P2 R1
     "[Onboarding Bestand behält seine Nummern (echter Transport)]"),
    # Codex P2 R2: bestätigter Teil eines Chunks vor dem Gruppenfehler wird nicht gezählt.
    ("upsert_prices meldet den bestätigten Teil nicht",
     SC, "            raise UpsertTeilfehler(geschrieben, e) from e",
     "            raise UpsertTeilfehler(0, e) from e",
     "[Onboarding Teilfehler in einer Chunk-Gruppe zählt den bestätigten Teil]"),
    ("Onboarding zählt den bestätigten Teil nicht",
     BN, '            total_written += getattr(e, "geschrieben", 0)   # bestätigter Teil vor dem Fehler (UpsertTeilfehler)',
     "            pass",
     "[Onboarding Teilfehler in einer Chunk-Gruppe zählt den bestätigten Teil]"),
    ("Lückenfüller im Nightly schreibt ohne Nummern",
     NR, '                                rec["tdom"], rec["tdoy"] = tdom, tdoy',
     "                                pass",
     "[Lücke nachgeladen mit Kalendernummern]"),
    ("Ungeklärte Tage werden nicht gemeldet",
     NR, '                        health_errors.append(f"UNGEKLÄRT {ticker}: kein Kurs bei Yahoo für {\', \'.join(ungeklaert_tage)}")',
     "                        pass",
     "[Lücke ungeklärt wird gemeldet]"),
    ("Leeres Yahoo gilt wieder als „Börse war zu“",
     NR, "                    if ungeklaert_tage:\n                        missing_total += len(ungeklaert_tage)",
     "                    if ungeklaert_tage and records:\n                        missing_total += len(ungeklaert_tage)",
     "[Lücke leeres Yahoo ist ungeklärt"),
    ("Yahoo-Ladefehler macht den Ticker nicht zum Fehler",
     NR, '                        health_errors.append(f"{ticker}: Yahoo-Nachladen {str(de)[:100]}")\n                        health_ungeprueft.add(ticker)',
     '                        health_errors.append(f"{ticker}: Yahoo-Nachladen {str(de)[:100]}")',
     "[Lücke Ladefehler ist Fehler]"),
    ("Intraday zählt wieder Zeilen",
     IR, '                df["tdom"] = [_t for _t, _ in _num]',
     '                df["tdom"] = list(range(1, len(df) + 1))',
     "[Intraday Kalendernummern über Lücke/Jahreswechsel]"),
    ("Kalenderhelfer nimmt die falsche Börse",
     EH, "    return [(n.tdom, n.tdoy) for n in handelstag_nummern(daten, get_exchange_for_holidays(ticker))]",
     '    return [(n.tdom, n.tdoy) for n in handelstag_nummern(daten, "NYSE")]',
     "[Intraday Kalendernummern über Lücke/Jahreswechsel]"),
    ("Onboarding überschreibt auch bestehende Zeilen (P5 umgangen)",
     BN, "        if ds not in schon_da:",
     "        if True:",
     "[Onboarding nur neue Zeilen mit Kalendernummern]"),
    ("Onboarding meldet Erfolg trotz gescheiterter Chunks",
     BN, "    if fehler:\n        # Früher ok=True",
     "    if False:\n        # Früher ok=True",
     "[Onboarding Upsertfehler → ok=False]"),
    ("Onboarding-Aufrufer endet trotz Fehlschlag mit 0",
     OB, "    return 0 if backfill_ok else 1",
     "    return 0",
     "[Onboarding Aufrufer Exit 1 bei gescheitertem Backfill]"),
    ("fix_missing_days schreibt ohne Nummern",
     FM, '                rec["tdom"], rec["tdoy"] = tdom, tdoy',
     "                pass",
     "[Lückenfüller Kalendernummern]"),
    ("fix_missing_days verschluckt Batchfehler",
     FM, '                FEHLER.append(f"{ticker}: Batch {i} {str(e)[:100]}")',
     "                pass",
     "[Lückenfüller Batchfehler → Exit 1]"),
    ("backfill_tdoy schreibt vor 2001",
     BT, "    if d_von < FRUEHESTES_SCHREIBDATUM:",
     "    if False:",
     "[Reparatur vor 2001 verweigert]"),
    ("backfill_tdoy ohne Mengengrenze",
     BT, "    if len(abw) > max_aenderungen:",
     "    if False:",
     "[Reparatur Mengengrenze verweigert]"),
    ("backfill_tdoy prüft die Bestätigung nicht",
     BT, "            if len(r.data or []) != 1:",
     "            if False:",
     "[Reparatur ohne Bestätigung → Exit 1]"),
    ("backfill_tdoy ignoriert den Kalenderstatus",
     BT, '            if kalender_status(boerse, j) == "ungeprueft":',
     "            if False:",
     "[Reparatur ungeprüfter Kalender verweigert]"),
    ("backfill_tdoy schreibt den Schlusskurs mit",
     BT, '            r = (client.table("prices").update({"tdom": tdom, "tdoy": tdoy})',
     '            r = (client.table("prices").update({"tdom": tdom, "tdoy": tdoy, "close": 0})',
     "[Reparatur nur tdom/tdoy]"),
    ("backfill_tdoy schreibt schon im Trockenlauf",
     BT, '    schreib = "--schreiben" in args',
     "    schreib = True",
     "[Reparatur Trockenlauf schreibt nichts]"),
]

UNGUELTIG_ERWARTET = [
    # Ein Absturz, den backfill_tdoy selbst abfängt und nur als Exit 1 meldet — muss ungültig sein.
    ("Abgefangener Absturz in backfill_tdoy", BT,
     "def abweichungen(ticker: str, zeilen: list[dict]) -> list[dict]:",
     "def abweichungen(ticker: str, zeilen: list[dict]) -> list[dict]:\n    None.real"),
    # Ein Absturz, der den Prüfblock abbricht — ebenfalls ungültig.
    # Codex P2 R1: abgefangene Abstürze in den übrigen Schreibern — die Ausgabe nennt die Klasse nicht.
    ("Abgefangener Absturz im Onboarding", BN,
     "        tdoy_map = dict(zip(iso_daten, tdom_tdoy_fuer_ticker(ticker, iso_daten)))",
     "        None.real\n        tdoy_map = dict(zip(iso_daten, tdom_tdoy_fuer_ticker(ticker, iso_daten)))"),
    ("Abgefangener Absturz in Intraday", IR,
     '                _num = tdom_tdoy_fuer_ticker(ticker, [_i.strftime("%Y-%m-%d") for _i in df.index])',
     '                None.real\n                _num = tdom_tdoy_fuer_ticker(ticker, [_i.strftime("%Y-%m-%d") for _i in df.index])'),
    ("Abgefangener Absturz im Nightly-Lückenfüller", NR,
     "                            for rec, (tdom, tdoy) in zip(records, tdom_tdoy_fuer_ticker(",
     "                            None.real\n                            for rec, (tdom, tdoy) in zip(records, tdom_tdoy_fuer_ticker("),
    # Codex P2 R3: ein fremder Ausnahmetyp mit Stub-Ursache darf nicht als Umhüllung durchgehen.
    ("Fremde verkettete Ausnahme statt UpsertTeilfehler", SC,
     "            raise UpsertTeilfehler(geschrieben, e) from e",
     '            raise AttributeError("neuer Produktivfehler") from e'),
    ("Absturz außerhalb eines try", BT,
     '    """Alle Gründe, warum NICHT geschrieben werden darf (leer = darf)."""',
     '    """Alle Gründe, warum NICHT geschrieben werden darf (leer = darf)."""\n    None.real'),
    ("Anker existiert nicht", BT, "diese Zeile gibt es nicht", "egal"),
]

# Originalbytes erst UNTER der gemeinsamen Sperre lesen (Codex P1b R1): sonst kann ein
# paralleler Lauf mutierte Bytes als Original übernehmen.
DATEIEN = (IR, NR, BN, OB, FM, BT, EH, SC)
ROH: dict = {}


def anker(datei: str, text: str) -> bytes:
    roh = ROH[datei]
    if roh.count(b"\r\n") > roh.count(b"\n") // 2:
        text = text.replace("\r\n", "\n").replace("\n", "\r\n")
    return text.encode("utf-8")


def lauf() -> tuple[int, str]:
    # Eigener, leerer Bytecode-Cache je Lauf — siehe python_probe (sonst prüft eine
    # Mutation gleicher Länge die .pyc ihrer Vorgängerin; beobachtet 2026-10-10).
    r = python_probe([PROBE], capture_output=True, text=True, encoding="utf-8",
                     env={**os.environ, "PYTHONUTF8": "1"})
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def bewerte(datei, alt, neu, erwartet=None):
    a = anker(datei, alt)
    n = ROH[datei].count(a)
    if n != 1:
        return "ungueltig", f"Anker {n}x gefunden, erwartet 1x"
    _atomar_schreiben(pathlib.Path(datei), ROH[datei].replace(a, anker(datei, neu), 1))
    try:
        rc_, aus = lauf()
    finally:
        _atomar_schreiben(pathlib.Path(datei), ROH[datei])
    if rc_ == 0:
        return "entwischt", "Probe blieb grün"
    if "PROBE-ENDE" not in aus:
        return "ungueltig", "die Probe brach ab statt durchzulaufen"
    zeilen = [z for z in aus.splitlines() if "FEHL " in z]
    if any("[Ausnahme]" in z for z in zeilen):
        return "ungueltig", "Produktivcode warf"
    if not zeilen:
        return "ungueltig", "rot ohne inhaltliche Prüfung"
    if erwartet and not any(erwartet in z for z in zeilen):
        return "ungueltig", f"erwartete Prüfung {erwartet} blieb grün; rot war: {zeilen[0].strip()[:50]}"
    return "gefangen", zeilen[0].strip()[:70]


def _main() -> int:
    rc, ausgabe = lauf()
    if rc != 0:
        print("ABBRUCH: die Probe ist schon ohne Mutation rot.")
        print(ausgabe[-1500:])
        return 1
    m = re.search(r"PROBE-ENDE (\d+) Pruefungen", ausgabe)
    if not m:
        print("ABBRUCH: die Probe meldet keinen Endmarker.")
        return 1
    print(f"Grundlinie: Probe ohne Mutation grün, {m.group(1)} Prüfungen\n")

    gefangen, probleme, urteil_ok = 0, [], True
    try:
        for name, datei, alt, neu, erwartet in MUTATIONEN:
            art, warum = bewerte(datei, alt, neu, erwartet)
            if art == "gefangen":
                print(f"  gefangen       {name}")
                gefangen += 1
            else:
                print(f"  {art.upper():12s}   {name}  ({warum})")
                probleme.append(f"{name} [{art}: {warum}]")
        print("  -- Gegenprobe am Urteil dieses Tests --")
        for name, datei, alt, neu in UNGUELTIG_ERWARTET:
            art, warum = bewerte(datei, alt, neu)
            if art == "ungueltig":
                print(f"  richtig verworfen  {name}  ({warum})")
            else:
                print(f"  FALSCH EINGEORDNET {name}  -> {art}")
                probleme.append(f"{name} [als {art} verbucht]")
                urteil_ok = False
    finally:
        for d, b in ROH.items():
            _atomar_schreiben(pathlib.Path(d), b)
    for d, b in ROH.items():
        assert io.open(d, "rb").read() == b, "WIEDERHERSTELLUNG FEHLGESCHLAGEN: " + d
    rc_nach, _ = lauf()
    print()
    print("wiederhergestellt: Probe läuft wieder grün" if rc_nach == 0
          else "WARNUNG: Probe nach der Wiederherstellung ROT!")
    print(f"{gefangen} von {len(MUTATIONEN)} Mutationen gefangen")
    for p in probleme:
        print("  " + p)
    return 0 if (gefangen == len(MUTATIONEN) and urteil_ok and rc_nach == 0) else 1


def main() -> int:
    try:
        with _exklusiver_lauf():
            ROH.update({d: io.open(d, "rb").read() for d in DATEIEN})
            return _main()
    except LockBelegt as e:
        print(f"ABBRUCH: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
