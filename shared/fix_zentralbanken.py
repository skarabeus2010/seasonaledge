#!/usr/bin/env python3
"""
fix_zentralbanken.py — Behebt die 2 Bugs in 6_*_Zentralbanken.py
die zu "Nicht genug Daten" führen obwohl 173 Events gefunden werden.

BUG 1: datetime.date vs pd.Timestamp Vergleich (pandas 2.x Exception)
BUG 2: iloc mit nicht-resettem Index nach Jahr-Filter

Ausführen aus C:\Dev\Claude\Saisonalcharts:
    py fix_zentralbanken.py
"""
import re, pathlib, sys

PROJECT_DIR = pathlib.Path(__file__).parent

# Zentralbanken-Page finden
page_file = None
for p in (PROJECT_DIR / "pages").glob("*Zentral*"):
    page_file = p
    break
if not page_file:
    for p in (PROJECT_DIR / "pages").glob("*entralbank*"):
        page_file = p
        break

if not page_file:
    print("❌ Keine Zentralbanken-Page gefunden. Muster: pages/*Zentral*.py")
    sys.exit(1)

print(f"Patche: {page_file}")
original = page_file.read_text(encoding="utf-8")
patched = original

# ── Fix 1: Alle df["Date"] >= / <= event_date ohne pd.Timestamp ──────────────
# Suche Patterns wie:
#   df[df["Date"] >= event_date]
#   df["Date"] >= h_date
#   df[df['Date'] <= event_date]
# und wrape die rechte Seite mit pd.Timestamp(...)

# Pattern: df["Date"] OP variable  — nur wenn variable kein Timestamp/String-Literal ist
FIX1_PATTERNS = [
    # df[df["Date"] >= some_var]  →  df[df["Date"] >= pd.Timestamp(some_var)]
    (
        r'df\[df\["Date"\]\s*(>=|<=|>|<|==)\s*([a-zA-Z_]\w*)\]',
        lambda m: f'df[df["Date"] {m.group(1)} pd.Timestamp({m.group(2)})]'
    ),
    (
        r"df\[df\['Date'\]\s*(>=|<=|>|<|==)\s*([a-zA-Z_]\w*)\]",
        lambda m: f"df[df['Date'] {m.group(1)} pd.Timestamp({m.group(2)})]"
    ),
    # df_filtered["Date"] >= event_date  (in boolean mask außerhalb [])
    (
        r'(_df|df_filtered|_tdays|trading_days)\["Date"\]\s*(>=|<=|>|<|==)\s*([a-zA-Z_]\w*)',
        lambda m: f'{m.group(1)}["Date"] {m.group(2)} pd.Timestamp({m.group(3)})'
    ),
    # candidates = [t for t in trading_days if t >= event_date]
    # → wird durch fix_index_bugs.py bereits zu df['Date'].tolist() gemacht
    # hier nur Timestamp-Fix für direkte Vergleiche
    (
        r'\bt\s*(>=|<=|>|<|==)\s*([a-zA-Z_]*(?:date|ts|event|h_date|meeting)\w*)',
        lambda m: f't {m.group(1)} pd.Timestamp({m.group(2)})'
    ),
]

# Robusterer Ansatz: Zeile für Zeile, nur Date-Vergleichs-Zeilen anfassen
lines = patched.split('\n')
new_lines = []
fixes1 = 0

for line in lines:
    new_line = line
    # Nur Zeilen die einen Date-Vergleich enthalten
    if '"Date"' in line or "'Date'" in line:
        if any(op in line for op in ['>=', '<=', '==', '< ', '> ']):
            # Suche: df["Date"] OP var  wo var KEIN pd.Timestamp(...) ist
            # Pattern: ["Date"] OP (word_without_pd_Timestamp)
            def replace_date_compare(m):
                op   = m.group(1)
                var  = m.group(2)
                # Nicht doppelt wrappen
                if var.startswith('pd.Timestamp') or var.startswith('pd.to_datetime'):
                    return m.group(0)
                # String-Literale nicht wrappen (werden automatisch konvertiert)
                if var.startswith('"') or var.startswith("'"):
                    return m.group(0)
                return f'["Date"] {op} pd.Timestamp({var})'
            
            result = re.sub(
                r'\["Date"\]\s*(>=|<=|>|<|==)\s*([^\]\s,\)]+)',
                replace_date_compare,
                new_line
            )
            if result != new_line:
                new_line = result
                fixes1 += 1

    new_lines.append(new_line)

patched = '\n'.join(new_lines)

# ── Fix 2: reset_index nach DataFrame-Filter vor iloc-Nutzung ────────────────
# Suche: df_filtered = df[...].copy() oder df[...] ohne reset_index
# Dann: prüfe ob danach iloc[t0_idx...] verwendet wird
# 
# Einfacherer Fix: Alle .copy() nach Boolean-Filter → .copy().reset_index(drop=True)

fixes2_patterns = [
    # df_filtered = df[boolean_expr].copy()
    (
        r'((?:df_filtered|_df|df_cb|df_window)\s*=\s*df\[[^\]]+\]\.copy\(\))',
        r'\1.reset_index(drop=True)'  # wird zu .copy().reset_index(drop=True)
                                      # das ist equivalent
    ),
    # _df = df[...] ohne .copy() aber mit nachfolgendem .reset_index-Bedarf
    # Sicherer: nur wenn nicht schon reset_index vorhanden
]

fixes2 = 0
for pattern, replacement in fixes2_patterns:
    new_patched, count = re.subn(pattern, replacement, patched)
    if count:
        # Verhindere doppeltes reset_index
        new_patched = new_patched.replace(
            '.copy().reset_index(drop=True).reset_index(drop=True)',
            '.copy().reset_index(drop=True)'
        )
        patched = new_patched
        fixes2 += count

# ── Fix 3: get_next_trading_day / Kandidaten-Liste ───────────────────────────
# Falls trading_days eine Liste von Timestamps ist (nach fix_index_bugs.py),
# aber der Vergleich mit dem event_date immer noch als date-Objekt passiert:
# candidates = [t for t in trading_days if t >= target_ts]
# → target_ts muss ein Timestamp sein

fix3_pattern = r'(target_ts|target)\s*=\s*pd\.Timestamp\('
if not re.search(fix3_pattern, patched):
    # Suche: def get_next_trading_day(h_date, trading_days):
    # und füge pd.Timestamp-Konvertierung hinzu
    patched = re.sub(
        r'(def get_next_trading_day\([^)]+\):\s*\n(?:\s+[^\n]*\n)*?\s+)(candidates\s*=\s*\[t for t in trading_days if t >=)',
        r'\1target_ts = pd.Timestamp(h_date) if not isinstance(h_date, pd.Timestamp) else h_date\n    \2',
        patched
    )

# ── Schreiben ─────────────────────────────────────────────────────────────────
if patched != original:
    page_file.write_text(patched, encoding="utf-8")
    print(f"  ✓ Fix 1 (Date-Vergleich): {fixes1} Stelle(n)")
    print(f"  ✓ Fix 2 (reset_index):    {fixes2} Stelle(n)")
    print(f"\n✓ {page_file.name} gepatcht")
else:
    print("  — Keine automatisch patchbaren Stellen gefunden.")
    print("  ⚠ Bitte manuell prüfen: Datums-Vergleiche und iloc-Aufrufe nach Filter")

# ── Verifikation ──────────────────────────────────────────────────────────────
print("\n── Verifikation ─────────────────────────────────────────────")
src = page_file.read_text(encoding="utf-8")
lines = src.splitlines()

# Suche noch vorhandene riskante Date-Vergleiche
risky = []
for i, line in enumerate(lines, 1):
    if ('"Date"' in line or "'Date'" in line) and any(op in line for op in ['>=', '<=']):
        if 'pd.Timestamp' not in line and 'pd.to_datetime' not in line:
            risky.append((i, line.strip()))

if risky:
    print(f"⚠ {len(risky)} möglicherweise ungepatchte Date-Vergleiche:")
    for lno, l in risky[:10]:
        print(f"  Zeile {lno}: {l}")
else:
    print("✓ Alle Date-Vergleiche verwenden pd.Timestamp()")

# Suche reset_index nach Filter
no_reset = []
for i, line in enumerate(lines, 1):
    if re.search(r'=\s*df\[.*\]\.copy\(\)\s*$', line):
        no_reset.append((i, line.strip()))
if no_reset:
    print(f"⚠ {len(no_reset)} .copy() ohne reset_index:")
    for lno, l in no_reset[:5]:
        print(f"  Zeile {lno}: {l}")
else:
    print("✓ Alle .copy()-Filter haben reset_index(drop=True)")
