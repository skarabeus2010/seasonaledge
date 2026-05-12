"""
scripts/fix_log_returns_may2026.py
Einmalig: log_return für ^GDAXI 2026-05-05 und 2026-05-06 korrigieren.

Aufruf: docker exec seasonalpha-app python3 scripts/fix_log_returns_may2026.py
"""
import sys, pathlib, math

_project_dir = str(pathlib.Path(__file__).resolve().parent.parent)
if _project_dir not in sys.path:
    sys.path.insert(0, _project_dir)

from shared.supabase_client import get_client

client = get_client()

# Kurse der relevanten Tage holen
rows = (client.table("prices")
        .select("date,close,log_return")
        .eq("ticker", "^GDAXI")
        .in_("date", ["2026-05-04", "2026-05-05", "2026-05-06"])
        .order("date")
        .execute().data)

closes = {r["date"]: r["close"] for r in rows}
fixed = 0

for date_str, prev_date in [("2026-05-05", "2026-05-04"), ("2026-05-06", "2026-05-05")]:
    row = next((r for r in rows if r["date"] == date_str), None)
    if row is None:
        print(f"  {date_str}: kein Row gefunden — übersprungen")
        continue
    if row["log_return"] is not None:
        print(f"  {date_str}: log_return bereits gesetzt ({row['log_return']:.8f}) — übersprungen")
        continue
    if prev_date not in closes:
        print(f"  {date_str}: Vortag {prev_date} nicht in DB — übersprungen")
        continue

    lr = math.log(closes[date_str] / closes[prev_date])
    client.table("prices").update({"log_return": round(lr, 8)}).eq("ticker", "^GDAXI").eq("date", date_str).execute()
    print(f"  {date_str}: log_return gesetzt = {lr:.8f}  (close={closes[date_str]}, prev={closes[prev_date]})")
    fixed += 1

print(f"\n{fixed} Zeile(n) korrigiert.")
