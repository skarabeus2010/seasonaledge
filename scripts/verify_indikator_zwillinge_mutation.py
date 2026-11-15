#!/usr/bin/env python3
"""
verify_indikator_zwillinge_mutation.py — baut die alten Indikator-Rechnungen (vor 2026-11-15) wieder ein und verlangt
Rot im Wächter verify_indikator_zwillinge.py AN DER BENANNTEN PRÜFUNG. Mechanik aus verify_twins_mutation.
"""
from __future__ import annotations
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
from scripts.verify_twins_mutation import (_exklusiver_lauf, _zeilenende, _atomar_schreiben,  # noqa: E402
                                           python_probe, LF)

_WAECHTER = _ROOT / "scripts" / "verify_indikator_zwillinge.py"
PY, JS = "shared/indicators.py", "landing/js/indicators.js"

MUTATIONEN = [
    ("Python-RSI wieder gleitendes einfaches Mittel", PY,
     "        ag = (ag * (period - 1) + gew[i]) / period\n        av = (av * (period - 1) + ver[i]) / period",
     "        ag = float(np.mean(gew[i - period + 1:i + 1]))\n        av = float(np.mean(ver[i - period + 1:i + 1]))",
     "Hand Python RSI(2) Zickzack"),
    ("Python-EMA wieder ab dem ersten Kurs", PY,
     "    return pd.Series(_ema_werte(series.to_numpy(dtype=float), period), index=series.index)",
     "    return series.ewm(span=period, adjust=False).mean()",
     "Hand Python EMA vor dem Startwert"),
    ("Python-Bollinger wieder Stichprobe", PY,
     "    std = series.rolling(period).std(ddof=0)",
     "    std = series.rolling(period).std()",
     "Hand Python Bollinger"),
    ("Python-RSI ohne Verlust wieder unbestimmt", PY,
     "        return 100.0 if g > 0 else np.nan",
     "        return np.nan",
     "Hand Python RSI steigend"),
    ("Python-MACD-Signal wieder pandas ewm", PY,
     "    signal_line = calc_ema(macd_line, signal)",
     "    signal_line = macd_line.ewm(span=signal, adjust=False).mean()",
     "Zwilling weg macd_s"),
    ("JS-RSI ohne Verlust wieder RS = 100", JS,
     "    function rsiAus(g, v) { return v > 0 ? 100 - 100 / (1 + g / v) : (g > 0 ? 100 : null); }",
     "    function rsiAus(g, v) { var rs = v > 0 ? g / v : 100; return 100 - 100 / (1 + rs); }",
     "Hand JS RSI steigend"),
    ("Python-Histogramm mit umgekehrtem Vorzeichen", PY,
     "    histogram = macd_line - signal_line",
     "    histogram = signal_line - macd_line",
     "Hand Python Histogramm lbr_h"),
    ("Python-RSI ohne Lückenzweig", PY,
     "    if len(werte) < period + 1 or np.isnan(werte).any():",
     "    if len(werte) < period + 1:",
     "Hand Python RSI(2) mit Lücke"),
    ("Python-SMA mit Teilfenstern", PY,
     "    return series.rolling(period, min_periods=period).mean()",
     "    return series.rolling(period, min_periods=1).mean()",
     "Hand Python SMA-Fenster"),
    ("JS rechnet Lücke wieder als 0", JS,
     "  _gueltig: function(v) { return typeof v === 'number' && !isNaN(v); },",
     "  _gueltig: function(v) { return v !== undefined; },",
     "Hand JS RSI(2) mit Lücke"),
    ("JS-Histogramm mit umgekehrtem Vorzeichen", JS,
     "histogram[i] = macdLine[i] - signalLine[i];",
     "histogram[i] = signalLine[i] - macdLine[i];",
     "Hand JS Histogramm lbr_h"),
    ("JS-RSI flach wieder 100", JS,
     "(g > 0 ? 100 : null)",
     "100",
     "Hand JS RSI flach"),
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
            s, e = such.encode("utf-8").replace(LF, le), ersatz.encode("utf-8").replace(LF, le)
            if original.count(s) != 1:
                print(f"{nr:>2}. [UNGUELTIG] {name} — Anker {original.count(s)}x")
                ungueltig.append(name)
                continue
            try:
                _atomar_schreiben(pfad, original.replace(s, e, 1))
                r = python_probe([_WAECHTER], capture_output=True, text=True, cwd=str(_ROOT))
            finally:
                _atomar_schreiben(pfad, original)
                assert pfad.read_bytes() == original, f"{datei} nicht wiederhergestellt"
            fehl = [z for z in r.stdout.splitlines() if z.strip().startswith("FEHL")]
            if any("[Ausnahme]" in z for z in fehl):
                print(f"{nr:>2}. [Absturz]   {name} — kein Nachweis: {fehl[0][:120]}")
                ungueltig.append(name)
            elif r.returncode == 1 and any(f"[{pruefung}" in z for z in fehl):
                print(f"{nr:>2}. [erkannt]   {name}")
            else:
                print(f"{nr:>2}. [UNBEMERKT] {name} (Exit {r.returncode}, rot: {[z[:60] for z in fehl[:3]]})")
                unbemerkt.append(name)
    print()
    if unbemerkt or ungueltig:
        print(f"[FAIL] unbemerkt {len(unbemerkt)}, ungültig {len(ungueltig)} von {len(MUTATIONEN)}")
        return 1
    print(f"[OK] Alle {len(MUTATIONEN)} Mutationen an der benannten Prüfung erkannt.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
