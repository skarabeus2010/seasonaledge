#!/usr/bin/env python3
"""
verify_basisabweichung_mutation.py — prüft den Wächter verify_basisabweichung.py: baut bekannte Fehler wieder ein und
verlangt Rot. Mechanik (Sperre, Bytes, atomares Schreiben, frischer Bytecode-Cache) aus verify_twins_mutation.
Exit des Wächters: 0 grün, 1 rot (= erkannt), 3 Absturz (= ungültig, kein Nachweis).
"""
from __future__ import annotations
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
from scripts.verify_twins_mutation import (_exklusiver_lauf, _zeilenende, _atomar_schreiben,  # noqa: E402
                                           python_probe, LF)

_WAECHTER = _ROOT / "scripts" / "verify_basisabweichung.py"

MUTATIONEN = [
    ("RV wieder aus Schlusskursen (Live)",
     "scripts/compute_options_skew.py",
     "    return rv_aus_returns(returns[:gueltig[-1] + 1], n), last, last_d",
     "    return rv_aus_returns([None] + [math.log(c[i] / c[i - 1]) for i in range(1, len(c))], n), last, last_d"),
    ("Spot aus der letzten Zeile auch bei ungültigem Schluss (Datum)",
     "scripts/compute_options_skew.py",
     "    last_d = daten[gueltig[-1]]",
     "    last_d = daten[-1]"),
    ("RV-Fenster endet nicht am letzten gültigen Schluss",
     "scripts/compute_options_skew.py",
     "    return rv_aus_returns(returns[:gueltig[-1] + 1], n), last, last_d",
     "    return rv_aus_returns(returns, n), last, last_d"),
    ("rv_aus_returns ohne Endlichkeitsprüfung",
     "shared/realized_vol.py",
     "    if any(x is None or not math.isfinite(x) for x in seg):",
     "    if any(x is None for x in seg):"),
    ("rv_reihe_aus_returns um einen Tag verschoben",
     "shared/realized_vol.py",
     "        rv = rv_aus_returns(returns[:i + 1], n)",
     "        rv = rv_aus_returns(returns[:i], n)"),
    ("Intermarket-Bewegung wieder aus Schlusskursen",
     "shared/intermarket.py",
     "    lr = returns[-tage:]",
     "    lr = [math.log(_closes[-k] / _closes[-k - 1]) for k in range(tage, 0, -1)]"),
    ("SPY-Vola wieder aus Schlusskursen",
     "shared/intermarket.py",
     "    return rv_aus_returns(returns, 21)",
     "    return rv_aus_returns([None] + [math.log(_closes[i] / _closes[i - 1]) for i in range(1, len(_closes))], 21)"),
    ("VRP-Nachrechnung wieder aus Schlusskursen",
     "scripts/backfill_skew_vrp.py",
     "        rv_je[t] = rv_reihe_aus_returns(kd, kr)",
     "        from shared.realized_vol import rv_reihe\n        rv_je[t] = rv_reihe(kd, _kc)"),
    ("Basisabweichung nur nach oben erkannt",
     "shared/basisabweichung.py",
     "            if abs(d) > schwelle:",
     "            if d > schwelle:"),
    ("Health-Check: nichts gelesen gilt als grün",
     "scripts/daily_health_check.py",
     "            status, detail = \"yellow\", \"ungeprüft — keine Kurszeilen gelesen\"",
     "            status, detail = \"green\", \"ungeprüft — keine Kurszeilen gelesen\""),
    ("Health-Check: nur die erste Seite",
     "scripts/daily_health_check.py",
     "            if len(teil) < 1000:\n                break\n            off += 1000\n        erg7",
     "            break\n        erg7"),
    ("Health-Check: Treffer nur grün gemeldet",
     "scripts/daily_health_check.py",
     "        elif erg7[\"treffer\"]:\n            status = \"yellow\"",
     "        elif erg7[\"treffer\"]:\n            status = \"green\""),
    ("Mail: Dividenden ohne eigenen Client (NameError, still verschluckt)",
     "shared/daily_report.py",
     "        from shared.supabase_client import get_client\n        client = get_client()\n        rows = (\n            client.table(\"dividend_events\")",
     "        rows = (\n            client.table(\"dividend_events\")"),
    ("Mail: Earnings wieder aus earnings_events",
     "shared/daily_report.py",
     "    # Dividenden (Ex-Date im Window)\n",
     "    from shared.supabase_client import get_client as _g\n    for r in (_g().table(\"earnings_events\").select(\"*\").execute().data or []):\n        events.append({\"date\": r[\"report_date\"], \"type\": \"Earnings\", \"name\": r[\"ticker\"], \"ticker\": r[\"ticker\"], \"impact\": \"medium\"})\n    # Dividenden (Ex-Date im Window)\n"),
    ("Health-Check: kein Paar vergleichbar gilt als grün",
     "scripts/daily_health_check.py",
     "            status, detail = \"yellow\", f\"ungeprüft — kein Kurspaar vergleichbar",
     "            status, detail = \"green\", f\"ungeprüft — kein Kurspaar vergleichbar"),
    ("Health-Check: Paare statt geprüfter Paare",
     "scripts/daily_health_check.py",
     "        elif erg7[\"geprueft\"] == 0:",
     "        elif erg7[\"paare\"] == 0:"),
    ("Health-Check: unvollständige Prüfung grün",
     "scripts/daily_health_check.py",
     "            status, detail = \"yellow\", (f\"unvollständig",
     "            status, detail = \"green\", (f\"unvollständig"),
    ("geprüfte Paare vor dem Überspringen gezählt",
     "shared/basisabweichung.py",
     "            out[\"paare\"] += 1\n",
     "            out[\"paare\"] += 1\n            out[\"geprueft\"] += 1\n"),
    ("Health-Check: data=None als Seitenende",
     "scripts/daily_health_check.py",
     "                raise RuntimeError(f\"Seite ab {off} ohne Daten\")",
     "                teil = []"),
    ("Lader: data=None als Seitenende",
     "shared/data.py",
     "        teil = q.execute().data\n        if teil is None:",
     "        teil = q.execute().data or []\n        if teil is None:"),
    ("Lader: doppelte Daten nicht geprüft",
     "shared/data.py",
     "        if daten and d <= daten[-1]:",
     "        if False:"),
    ("Lader: nicht endlicher Return bleibt stehen",
     "shared/data.py",
     "        returns.append(_wert(z.get(\"log_return\"), False))",
     "        returns.append(float(z[\"log_return\"]) if z.get(\"log_return\") is not None else None)"),
    ("RV ohne Kappung auf die Session",
     "scripts/compute_options_skew.py",
     "        daten, closes, returns = kappe_reihen(daten_alle, closes_alle, returns_alle, bis=bis)",
     "        daten, closes, returns = daten_alle, closes_alle, returns_alle"),
    ("fehlender Return nicht gezählt",
     "shared/basisabweichung.py",
     "                out[\"ohne_return\"] += 1\n                continue",
     "                continue"),
]


def main() -> int:
    unbemerkt, ungueltig = [], []
    with _exklusiver_lauf():
        r0 = python_probe([_WAECHTER], capture_output=True, text=True, cwd=str(_ROOT))
        if r0.returncode != 0:
            print("[FAIL] Wächter ist schon ohne Mutation rot:\n" + r0.stdout[-2000:])
            return 1
        for nr, (name, datei, such, ersatz) in enumerate(MUTATIONEN, 1):
            pfad = _ROOT / datei
            original = pfad.read_bytes()
            le = _zeilenende(original)
            s, e = such.encode("utf-8").replace(LF, le), ersatz.encode("utf-8").replace(LF, le)
            if original.count(s) != 1:
                print(f"{nr:>2}. [UNGUELTIG] {name} — Anker {original.count(s)}x")
                ungueltig.append(name); continue
            try:
                _atomar_schreiben(pfad, original.replace(s, e, 1))
                r = python_probe([_WAECHTER], capture_output=True, text=True, cwd=str(_ROOT))
            finally:
                _atomar_schreiben(pfad, original)
                assert pfad.read_bytes() == original, f"{datei} nicht wiederhergestellt"
            if r.returncode == 1:
                print(f"{nr:>2}. [erkannt]   {name}")
            elif r.returncode == 3:
                print(f"{nr:>2}. [Absturz]   {name} — kein Nachweis"); ungueltig.append(name)
            else:
                print(f"{nr:>2}. [UNBEMERKT] {name}"); unbemerkt.append(name)
    print()
    if unbemerkt or ungueltig:
        print(f"[FAIL] unbemerkt {len(unbemerkt)}, ungültig {len(ungueltig)} von {len(MUTATIONEN)}")
        return 1
    print(f"[OK] Alle {len(MUTATIONEN)} Mutationen erkannt.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
