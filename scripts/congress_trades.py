#!/usr/bin/env python3
"""
congress_trades.py — Congress-Trades-Tracker (Pelosi & Co.) für /congress.

Quelle: offizieller House-Clerk-Disclosure-XML-Index (gratis, kein Key) +
PTR-PDFs. Filtert auf ein Roster (scripts/congress_roster.json), parst die
Periodic Transaction Reports (PTR) und schreibt landing/data/congress_trades.json.
Neue Filings (per DocID-Diff gegen den letzten Lauf) werden zurückgegeben →
Grundlage für den Brevo-E-Mail-Alert (separater Schritt).

Senat (EFD) ist Phase 2 — hier vorerst nur House.

Nutzung:
  py -3.14 scripts/congress_trades.py [--years 2026 2025] [--limit N] [--no-write]
"""
from __future__ import annotations
import argparse, io, json, os, re, ssl, sys, urllib.request, zipfile
import xml.etree.ElementTree as ET
from datetime import date, datetime
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

_CTX = ssl.create_default_context(); _CTX.check_hostname = False; _CTX.verify_mode = ssl.CERT_NONE
_UA = {"User-Agent": "Mozilla/5.0 (compatible; SeasonAlpha/1.0)"}
_XML_URL = "https://disclosures-clerk.house.gov/public_disc/financial-pdfs/{year}FD.zip"
_PDF_URL = "https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/{year}/{doc}.pdf"

_OWNER = {"SP": "Ehepartner", "JT": "gemeinsam", "DC": "Kind", "": "selbst"}
_ASSET = {"ST": "Aktie", "OP": "Option"}

# PTR-Formate variieren (Betrag mal um den Ticker gesplittet, mal zusammen).
# Robust: erst den Transaktions-"Header" (Typ + 2 Daten + $low - … $high) matchen,
# dann den Ticker (TICKER)[TYPE] im Fenster dahinter suchen. `[^$]*?` überspringt
# einen evtl. dazwischen stehenden Ticker, ohne über den nächsten Betrag zu laufen.
_HEADER = re.compile(
    r"\b(P|S\s*\(partial\)|S|E)\s+"
    r"(\d{2}/\d{2}/\d{4})\s+(\d{2}/\d{2}/\d{4})\s+"
    r"\$([\d,]+)\s*-\s*[^$]*?\$([\d,]+)"
)
_TICK = re.compile(r"\(([A-Z][A-Z.]{0,5})\)\s*\[(\w{2})\]")
_OWNER_RE = re.compile(r"\b(SP|JT|DC)\b")


def _get(url: str, timeout: int = 45) -> bytes:
    return urllib.request.urlopen(urllib.request.Request(url, headers=_UA), timeout=timeout, context=_CTX).read()


def _load_roster() -> list[dict]:
    cfg = json.loads((_ROOT / "scripts/congress_roster.json").read_text(encoding="utf-8"))
    return [r for r in cfg["roster"] if r.get("chamber") == "house"]


def _fetch_index(year: int) -> list[dict]:
    """Alle Filings eines Jahres aus dem House-Clerk-XML-Index."""
    z = zipfile.ZipFile(io.BytesIO(_get(_XML_URL.format(year=year))))
    xmlname = next(n for n in z.namelist() if n.lower().endswith(".xml"))
    root = ET.fromstring(z.read(xmlname))
    out = []
    for m in root.findall(".//Member"):
        out.append({k: (m.findtext(k) or "") for k in
                    ("Last", "First", "FilingType", "StateDst", "Year", "FilingDate", "DocID")})
    return out


def _roster_filings(members: list[dict], roster: list[dict], year: int) -> list[dict]:
    """PTR-Filings (Type P) der Roster-Mitglieder."""
    filings = []
    for m in members:
        if m["FilingType"] != "P":
            continue
        for r in roster:
            last, first_pref = r["match"]
            if m["Last"].strip() == last and m["First"].strip().startswith(first_pref):
                filings.append({**m, "person": r, "year": year})
                break
    return filings


def _parse_ptr(raw: bytes) -> tuple[list[dict], bool]:
    """Gibt (Transaktionen, is_image_scan). Scan-PDFs (Papierform) liefern keinen Text."""
    import pdfplumber
    with pdfplumber.open(io.BytesIO(raw)) as pdf:
        text = "\n".join((p.extract_text() or "") for p in pdf.pages)
    flat = re.sub(r"\s+", " ", text)
    if len(flat.strip()) < 120:
        return [], True                      # gescanntes Bild-PDF (kein Text)
    txns = []
    headers = list(_HEADER.finditer(flat))
    for i, h in enumerate(headers):
        tx, txd, _notif, low, high = h.groups()
        tk = _TICK.search(flat[h.start(): h.end() + 120])
        if not tk:
            continue                          # Asset ohne Ticker (LLC/Immobilie/Fonds)
        ticker, atype = tk.groups()
        seg_start = headers[i - 1].end() if i > 0 else 0
        oms = _OWNER_RE.findall(flat[seg_start:h.start()])   # letzter Code vor Header = der Besitzer
        owner = oms[-1] if oms else ""                        # (nicht der erste — "Washington, DC" wäre Fehlmatch)
        tx = tx.strip()
        if tx == "P":
            action, is_buy = "Kauf", True
        elif tx.startswith("S"):
            action, is_buy = ("Teilverkauf" if "partial" in tx else "Verkauf"), False
        else:
            action, is_buy = "Tausch", False   # E = Exchange
        txns.append({
            "ticker": ticker,
            "action": action,
            "is_buy": is_buy,
            "asset_type": _ASSET.get(atype, atype),
            "is_option": atype == "OP",
            "owner": _OWNER.get(owner, owner or "selbst"),
            "tx_date": datetime.strptime(txd, "%m/%d/%Y").date().isoformat(),
            "amount_low": int(low.replace(",", "")),
            "amount_high": int(high.replace(",", "")),
            "amount_range": f"${low} – ${high}",
        })
    return txns, False


def build(years: list[int], limit: int | None, write: bool) -> dict:
    from shared.symbols import get_all_tickers
    universe = set(get_all_tickers())
    roster = _load_roster()

    filings = []
    for y in years:
        try:
            filings += _roster_filings(_fetch_index(y), roster, y)
        except Exception as e:
            print(f"  [WARN] Index {y}: {e}")
    # neueste zuerst (nach FilingDate)
    def _fd(f):
        try: return datetime.strptime(f["FilingDate"], "%m/%d/%Y").date()
        except Exception: return date.min
    filings.sort(key=_fd, reverse=True)
    if limit:
        filings = filings[:limit]

    trades, unparsed = [], []
    for f in filings:
        doc, y = f["DocID"], f["year"]
        pdf_url = _PDF_URL.format(year=y, doc=doc)
        fdate = datetime.strptime(f["FilingDate"], "%m/%d/%Y").date().isoformat()
        try:
            txns, is_image = _parse_ptr(_get(pdf_url))
        except Exception as e:
            print(f"  [skip] {f['person']['name']} {doc}: {e}")
            txns, is_image = [], False
        for t in txns:
            trades.append({
                **t,
                "politician": f["person"]["name"],
                "party": f["person"]["party"],
                "district": f["person"]["district"],
                "in_universe": t["ticker"] in universe,
                "filing_date": fdate,
                "doc_id": doc,
                "pdf_url": pdf_url,
            })
        if is_image or (not txns):
            unparsed.append({"politician": f["person"]["name"], "party": f["person"]["party"],
                             "district": f["person"]["district"], "filing_date": fdate,
                             "doc_id": doc, "pdf_url": pdf_url,
                             "reason": "Scan-PDF (Papierform)" if is_image else "keine Wertpapier-Transaktion"})
        tag = "Scan" if is_image else f"{len(txns)} Txns"
        print(f"  ok  {f['person']['name']:24} filed {f['FilingDate']:11} DocID {doc} → {tag}")

    trades.sort(key=lambda t: (t["filing_date"], t["tx_date"]), reverse=True)
    out = {
        "generated": date.today().isoformat(),
        "source": "U.S. House Clerk — Financial Disclosures (PTR)",
        "roster": [r["name"] for r in roster],
        "n_trades": len(trades),
        "trades": trades,
        "unparsed_filings": unparsed,
    }
    if write:
        p = _ROOT / "landing/data/congress_trades.json"
        p.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n[OK] {len(trades)} Trades ({len(filings)} Filings) → {p}")
    return out


def _amt_short(n: int) -> str:
    if n >= 1_000_000: return f"${n/1e6:.0f}M".replace("$0M", "<$1M")
    if n >= 1_000: return f"${n/1e3:.0f}k"
    return f"${n}"


def render_alert_html(trades: list[dict]) -> str:
    """HTML-Alert für eine Gruppe neuer Trades (nach Politiker+Filing gruppiert)."""
    ACC, BG, CARD, TXT, MUT = "#e8a820", "#0a0a0a", "#141414", "#f0f0f0", "#8a8270"
    from collections import OrderedDict
    groups: "OrderedDict[tuple,list]" = OrderedDict()
    for t in trades:
        groups.setdefault((t["politician"], t["district"], t["party"], t["filing_date"]), []).append(t)
    blocks = []
    for (pol, dist, party, fdate), ts in groups.items():
        rows = ""
        for t in ts:
            col = "#30e878" if t["is_buy"] else "#ff4d5e"
            tk = t["ticker"]
            tklink = (f'<a href="https://seasonalpha.ai/index-effekt" style="color:{ACC};text-decoration:none">{tk}</a>'
                      if tk == "BE" else
                      (f'<a href="https://seasonalpha.ai/dashboard?ticker={tk}" style="color:{ACC};text-decoration:none">{tk} ★</a>'
                       if t["in_universe"] else f'<span style="color:{TXT}">{tk}</span>'))
            rows += (f'<tr>'
                     f'<td style="padding:6px 10px;color:{col};font-weight:700;white-space:nowrap">{t["action"]}</td>'
                     f'<td style="padding:6px 10px;font-family:monospace;font-weight:700">{tklink}</td>'
                     f'<td style="padding:6px 10px;color:{MUT}">{t["asset_type"]}</td>'
                     f'<td style="padding:6px 10px;color:{TXT};white-space:nowrap">{t["amount_range"]}</td>'
                     f'<td style="padding:6px 10px;color:{MUT};white-space:nowrap">{t["tx_date"]}</td>'
                     f'<td style="padding:6px 10px;color:{MUT}">{t["owner"]}</td></tr>')
        blocks.append(
            f'<div style="background:{CARD};border:1px solid #262626;border-radius:12px;padding:16px;margin:0 0 14px">'
            f'<div style="font-size:17px;font-weight:800;color:{TXT}">{pol} '
            f'<span style="color:{MUT};font-size:13px;font-weight:400">· {dist} ({party})</span></div>'
            f'<div style="color:{MUT};font-size:12px;margin:2px 0 10px">Offengelegt am {fdate} '
            f'· <a href="{ts[0]["pdf_url"]}" style="color:{ACC}">Original-Filing (PDF)</a></div>'
            f'<table style="width:100%;border-collapse:collapse;font-size:13px">'
            f'<tr style="color:{MUT};text-align:left;font-size:11px;text-transform:uppercase">'
            f'<th style="padding:4px 10px">Aktion</th><th style="padding:4px 10px">Ticker</th>'
            f'<th style="padding:4px 10px">Typ</th><th style="padding:4px 10px">Betrag</th>'
            f'<th style="padding:4px 10px">Handelstag</th><th style="padding:4px 10px">Konto</th></tr>'
            f'{rows}</table></div>')
    return (
        f'<div style="background:{BG};padding:24px;font-family:Arial,sans-serif;color:{TXT}">'
        f'<div style="max-width:640px;margin:0 auto">'
        f'<div style="font-size:22px;font-weight:800;color:{ACC};margin-bottom:2px">🏛️ Congress-Trade-Alert</div>'
        f'<div style="color:{MUT};font-size:13px;margin-bottom:18px">Neue STOCK-Act-Offenlegung eines beobachteten Politikers · '
        f'<a href="https://seasonalpha.ai/congress" style="color:{ACC}">Alle Trades auf seasonalpha.ai/congress</a></div>'
        f'{"".join(blocks)}'
        f'<div style="color:{MUT};font-size:11px;line-height:1.6;margin-top:16px;border-top:1px solid #262626;padding-top:12px">'
        f'★ = Ticker in deinem SeasonAlpha-Universum. Datenquelle: U.S. House Clerk (Pflichtoffenlegung, öffentlich). '
        f'<b>Einordnung:</b> Offenlegungsverzug 30–45 Tage (STOCK Act), rückwärtsgewandt. Kein Handelssignal, keine Anlageberatung.</div>'
        f'</div></div>')


def send_alert(trades: list[dict], to_email: str | None = None) -> bool:
    from shared.email_brevo import send_html
    pol = trades[0]["politician"]; n = len({t["ticker"] for t in trades})
    subject = f"🏛️ Congress-Trade-Alert: {pol} — {n} Ticker offengelegt"
    to = to_email or os.environ.get("ADMIN_EMAIL", "heiko.seibel@gmail.com")
    return send_html(to, subject, render_alert_html(trades))


_STATE = "landing/data/congress_trades_seen.json"


def run(years: list[int], seed_only: bool = False) -> int:
    """Cron-Modus: bauen, gegen letzten Stand diffen, bei NEUEN Filings alarmieren."""
    out = build(years, None, write=True)
    state_path = _ROOT / _STATE
    first = not state_path.exists()
    seen = {}
    if not first:
        try:
            seen = json.loads(state_path.read_text(encoding="utf-8"))
        except Exception:
            seen = {}
    current = {t["doc_id"]: t["filing_date"] for t in out["trades"]}
    for u in out["unparsed_filings"]:
        current.setdefault(u["doc_id"], u["filing_date"])
    new_docs = [d for d in current if d not in seen]

    if first or seed_only:
        state_path.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[run] Seed: {len(current)} Filings erfasst, KEINE Alerts (Erstlauf).")
        return 0

    sent = 0
    for doc in new_docs:
        trs = [t for t in out["trades"] if t["doc_id"] == doc]
        if trs:
            ok = send_alert(trs)
            sent += 1 if ok else 0
            print(f"[run] Alert {'OK' if ok else 'FEHLER'}: {trs[0]['politician']} {trs[0]['filing_date']} ({len(trs)} Trades)")
        else:
            print(f"[run] Neues Filing ohne parsebare Trades (Scan/leer): DocID {doc}")
    seen.update(current)
    state_path.write_text(json.dumps(seen, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[run] {len(new_docs)} neue Filings, {sent} Alerts gesendet.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", nargs="+", type=int, default=[date.today().year])
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--no-write", action="store_true")
    ap.add_argument("--email-test", action="store_true", help="Sample-Alert (neuestes Filing) an ADMIN_EMAIL senden")
    ap.add_argument("--run", action="store_true", help="Cron: bauen + bei neuen Filings alarmieren")
    ap.add_argument("--seed-only", action="store_true", help="State seeden ohne Alerts")
    a = ap.parse_args()
    if a.run or a.seed_only:
        return run(a.years, seed_only=a.seed_only)
    if a.email_test:
        data = json.loads((_ROOT / "landing/data/congress_trades.json").read_text(encoding="utf-8"))
        # neuestes Filing (politician+filing_date) als Sample-Alert
        newest = data["trades"][0]
        key = (newest["politician"], newest["filing_date"])
        sample = [t for t in data["trades"] if (t["politician"], t["filing_date"]) == key]
        ok = send_alert(sample)
        print(f"[email-test] {'OK gesendet' if ok else 'FEHLGESCHLAGEN'} — {len(sample)} Trades ({key[0]}, {key[1]})")
        return 0 if ok else 1
    build(a.years, a.limit, not a.no_write)
    return 0


if __name__ == "__main__":
    sys.exit(main())
