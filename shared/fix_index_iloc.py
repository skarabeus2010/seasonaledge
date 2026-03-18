#!/usr/bin/env python3
"""
fix_index_iloc.py — Patcht df.index[N].year/.month/.day etc.
→ df["Date"].iloc[N].year/.month/.day

Ergänzung zu fix_index_bugs.py v4.
"""
import re, pathlib, sys

PROJECT_DIR = pathlib.Path(__file__).parent

PATTERNS = [
    # df.index[0].year / df.index[-1].year / df.index[n].year etc.
    (r'(\w+)\.index\[(-?\d+)\]\.(year|month|day|weekday|dayofyear|strftime)',
     r"\1['Date'].iloc[\2].\3"),
    # df.index[0] allein (ohne Attribut) — z.B. wenn als Datum verwendet
    (r'(\w+)\.index\[(-?\d+)\](?!\.\w)',
     r"\1['Date'].iloc[\2]"),
]

def collect_files():
    files = list((PROJECT_DIR / "pages").glob("*.py"))
    shared = PROJECT_DIR / "shared"
    if shared.exists():
        files += list(shared.glob("*.py"))
        for sub in shared.iterdir():
            if sub.is_dir():
                files += list(sub.glob("*.py"))
    return files

fixes_total = 0
for py_file in sorted(collect_files()):
    original = py_file.read_text(encoding="utf-8")
    patched  = original
    n = 0
    for pat, rep in PATTERNS:
        new, count = re.subn(pat, rep, patched)
        patched = new
        n += count
    if n:
        py_file.write_text(patched, encoding="utf-8")
        fixes_total += n
        print(f"  ✓ {py_file.name}: {n} Fix(e)")

print(f"\n{'✓ ' + str(fixes_total) + ' Fixes gesamt' if fixes_total else '— Keine Stellen gefunden'}")

# Verifikation
remaining = []
for py_file in sorted(collect_files()):
    src = py_file.read_text(encoding="utf-8")
    for m in re.finditer(r'\.index\[-?\d+\]', src):
        lno = src[:m.start()].count('\n') + 1
        remaining.append((py_file.name, lno, src.splitlines()[lno-1].strip()))

if remaining:
    print(f"\n⚠ {len(remaining)} verbleibende .index[N]-Stellen:")
    for f, l, line in remaining[:10]:
        print(f"  {f}:{l}  {line}")
else:
    print("✓ Keine df.index[N]-Zugriffe mehr")
