#!/usr/bin/env python3
"""
fix_index_bugs.py v4 — Heilt ALLE df.index-Bugs in SeasonAlpha Pages + shared/.

ROOT CAUSE: Nach preprocess() hat jeder DataFrame einen RangeIndex (0,1,2,...).
Alter Code behandelt df.index als DatetimeIndex mit .year/.month/.weekday etc.

BUG-TYPEN:
  Typ 1:  df.index.weekday / .year / .month / .day / .dayofyear
  Typ 2:  df.index.year.unique() / .nunique()
  Typ 3:  df.index.max() / .min() ± DateOffset
  Typ 4:  df.index <= / >= pd.Timestamp(...) / variable
  Typ 5:  download_data(ticker, period="max")
  Typ 6:  df.index.tolist() → gibt int-Liste statt Timestamp-Liste
  Typ 7:  list(df.index) → gibt int-Liste statt Timestamp-Liste
  Typ 8:  trading_days = df.index  (direkte Zuweisung)

Ausführen:
    py fix_index_bugs.py
aus dem Saisonalcharts-Verzeichnis.
"""

import re, pathlib

PROJECT_DIR = pathlib.Path(__file__).parent

PATTERNS = [

    # ── Typ 2: .index.*.unique() / .nunique() ────────────────────────────────
    (r'(\w+)\.index\.(year|month|day|weekday|dayofweek)\.unique\(\)',
     r"\1['Date'].dt.\2.unique()"),
    (r'(\w+)\.index\.(year|month|day|weekday|dayofweek)\.nunique\(\)',
     r"\1['Date'].dt.\2.nunique()"),

    # ── Typ 1: .index.weekday / .year / .month etc. ───────────────────────────
    (r'(\w+)\.index\.(weekday|dayofweek)',   r"\1['Date'].dt.weekday"),
    (r'(\w+)\.index\.year\b',               r"\1['Date'].dt.year"),
    (r'(\w+)\.index\.month\b',              r"\1['Date'].dt.month"),
    (r'(\w+)\.index\.day\b',               r"\1['Date'].dt.day"),
    (r'(\w+)\.index\.dayofyear\b',          r"\1['Date'].dt.dayofyear"),
    (r'(\w+)\.index\.quarter\b',            r"\1['Date'].dt.quarter"),

    # ── Typ 3: .index.max/min() ± DateOffset ─────────────────────────────────
    (r'(\w+)\.index\.max\(\)\s*-\s*(pd\.DateOffset\([^)]+\))',
     r"\1['Date'].max() - \2"),
    (r'(\w+)\.index\.min\(\)\s*\+\s*(pd\.DateOffset\([^)]+\))',
     r"\1['Date'].min() + \2"),
    (r'(\w+)\.index\.(max|min)\(\)',
     r"\1['Date'].\2()"),

    # ── Typ 4: .index Vergleiche ──────────────────────────────────────────────
    (r'(\w+)\.index\s*(<=|>=|<|>)\s*(pd\.Timestamp\([^)]+\))',
     r"\1['Date'] \2 \3"),
    (r'(\w+)\.index\s*(<=|>=|<|>)\s*(\w+)',
     r"\1['Date'] \2 \3"),

    # ── Typ 5: download_data mit period= ──────────────────────────────────────
    (r'download_data\(([^,)]+),\s*period\s*=\s*["\'][^"\']*["\']\)',
     r"download_data(\1)"),

    # ── Typ 6: df.index.tolist() → gibt int-Liste ────────────────────────────
    # Häufig: trading_days = df.index.tolist()
    (r'(\w+)\.index\.tolist\(\)',
     r"\1['Date'].tolist()"),

    # ── Typ 7: list(df.index) → gibt int-Liste ────────────────────────────────
    # Häufig: trading_days = list(df.index)
    # Vorsicht: list() kann auch andere Objekte wrappen — nur df.index treffen
    (r'list\((\w+)\.index\)',
     r"\1['Date'].tolist()"),

    # ── Typ 8: pd.Series(... index=df.index) wo DatetimeIndex erwartet ───────
    # Weniger häufig, aber möglich: series.index → 'Date' column
    # Nicht automatisch patchen — zu riskant ohne Kontext
]

def collect_files():
    files = []
    files += list((PROJECT_DIR / "pages").glob("*.py"))
    shared = PROJECT_DIR / "shared"
    if shared.exists():
        files += list(shared.glob("*.py"))
        for sub in shared.iterdir():
            if sub.is_dir():
                files += list(sub.glob("*.py"))
    return files

fixes_total = 0
files_fixed = []

for py_file in sorted(collect_files()):
    original = py_file.read_text(encoding="utf-8")
    patched  = original
    fixes_in_file = 0

    for pattern, replacement in PATTERNS:
        new, count = re.subn(pattern, replacement, patched)
        if count:
            patched = new
            fixes_in_file += count

    if fixes_in_file:
        py_file.write_text(patched, encoding="utf-8")
        fixes_total     += fixes_in_file
        files_fixed.append((py_file.name, fixes_in_file))
        print(f"  ✓ {py_file.name}: {fixes_in_file} Fix(e)")

if fixes_total == 0:
    print("  — Keine Bugs gefunden.")
else:
    print(f"\n✓ {fixes_total} Fixes in {len(files_fixed)} Datei(en)")

# ── Verifikation: Noch offene Stellen? ───────────────────────────────────────
print("\n── Verifikation ─────────────────────────────────────────────")
VERIFY_PATTERNS = [
    r"\.index\.(weekday|year|month|day|dayofyear|quarter|dayofweek)\b",
    r"\.index\s*(<=|>=|<|>)\s*",
    r"\.index\.(max|min)\(\)\s*[\-\+]",
    r"download_data\([^)]+,\s*period\s*=",
    r"\.index\.tolist\(\)",
    r"list\(\w+\.index\)",
]
remaining = []
for py_file in sorted(collect_files()):
    src = py_file.read_text(encoding="utf-8")
    for pat in VERIFY_PATTERNS:
        for m in re.finditer(pat, src):
            lno  = src[:m.start()].count('\n') + 1
            line = src.splitlines()[lno-1].strip()
            remaining.append((py_file.name, lno, line))

if remaining:
    print(f"\n⚠ {len(remaining)} möglicherweise ungepatchte Stellen:")
    for fname, lno, line in remaining[:20]:
        print(f"  {fname}:{lno}  {line}")
else:
    print("✓ Keine ungepatchten df.index-Zugriffe mehr gefunden.")
