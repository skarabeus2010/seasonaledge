"""R1a (nur lesen): Tage, an denen der Schlusskurs-Sprung nicht zum gespeicherten log_return passt.
|ln(close_t/close_{t-1}) − log_return_t| > 0,05 in den letzten 2 Jahren, alle Ticker aus symbols.py."""
import sys, math, json
sys.path.insert(0, "/app"); sys.dont_write_bytecode = True
from shared.env_loader import load_env
load_env()
from shared.symbols import get_all_tickers
from shared.supabase_client import get_client

c = get_client()
treffer, geprueft, fehler = [], 0, []
abdeckung = {"zeilen": 0, "paare": 0, "ohne_return": 0, "luecke_gt7": 0, "ungueltiger_kurs": 0}
for t in get_all_tickers():
    try:
        rows, off = [], 0
        while True:
            b = (c.table("prices").select("date,close,log_return").eq("ticker", t).gte("date", "2024-10-01")
                 .order("date").range(off, off + 999).execute().data) or []
            rows += b; off += 1000
            if len(b) < 1000: break
        geprueft += 1
        abdeckung["zeilen"] += len(rows)
        for a, z in zip(rows, rows[1:]):
            if z["date"] < "2024-10-14": continue          # Vortag vor dem Fenster nur als Vorgänger
            abdeckung["paare"] += 1
            from datetime import date as _d
            if (_d.fromisoformat(z["date"]) - _d.fromisoformat(a["date"])).days > 7: abdeckung["luecke_gt7"] += 1
            if z["log_return"] is None: abdeckung["ohne_return"] += 1; continue
            try:
                ca, cz, lr = float(a["close"]), float(z["close"]), float(z["log_return"])
            except (TypeError, ValueError):
                abdeckung["ungueltiger_kurs"] += 1; continue
            if not math.isfinite(lr): abdeckung["ohne_return"] += 1; continue      # nicht endlicher Return = kein Return
            if not (math.isfinite(ca) and math.isfinite(cz) and ca > 0 and cz > 0):
                abdeckung["ungueltiger_kurs"] += 1; continue
            d = math.log(cz / ca) - lr
            if abs(d) > 0.05:
                treffer.append({"ticker": t, "datum": z["date"], "close_vor": ca, "close": cz, "log_return": lr,
                                "basissprung": round(math.exp(d), 4),
                                "korrektur_alte_kurse_auf_neue_basis": round(math.exp(d), 4)})
    except Exception as e:
        fehler.append((t, repr(e)[:120]))
print("@@ERG@@" + json.dumps({"abdeckung": abdeckung, "geprueft": geprueft, "treffer": treffer, "fehler": fehler}))
