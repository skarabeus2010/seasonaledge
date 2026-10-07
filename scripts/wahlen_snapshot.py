#!/usr/bin/env python3
"""
wahlen_snapshot.py — friert die Wahl-Studie für eine Veröffentlichung ein.

Plan (docs/review_prompts/2026-10-06_wahlen_plan.md, R4-4 / R5-1): ein Snapshot ist ein
vollständiges Auswertungspaket — Kurse und Gültigkeit je Offset, Wahl- und Ergebnismetadaten,
Kontrollzuordnungen, Reihenmetadaten, Versionen — plus die zitierte Ansicht und ihre Kennzahlen.
Die Seite zeigt ihn unter /wahlen?snapshot=<id> (bzw. /en/elections?snapshot=<id>) und mischt
dort nie aktuelle Daten bei. Ein bestehender Snapshot wird NIE überschrieben.

    # im Container (Studie vom Nightly), Ergebnis wird committet:
    python3 scripts/wahlen_snapshot.py --id midterm-2026-10 --reihe ^GSPC --typ midterm \
        --x 20 --y 20 --basis t0 --code-sha <git-sha> \
        --weitere live:^GSPC,midterm,40,20,tx

Prüfung: scripts/verify_wahlen_blog.py rechnet die gespeicherten Kennzahlen mit dem aktuellen
Rechenkern nach und gleicht sie mit den Zahlen im Blogtext ab.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from shared import elections as el  # noqa: E402

ZIEL = REPO / "landing" / "data" / "wahlen_snapshots"
ID_MUSTER = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")   # identisch mit der Seite
CALC_VERSION = "wahlen-aggregiere-1"


def ansicht(reihe: str, typ: str, x: int, y: int, basis: str, ab_jahr=None, wechsel: str = "alle") -> dict:
    return {"reihe": reihe, "typ": typ, "x": x, "y": y, "basis": basis, "abJahr": ab_jahr, "wechsel": wechsel}


def kennzahlen(st: dict, a: dict) -> dict:
    r = el.aggregiere(st, a["reihe"], a["typ"], a["x"], a["y"], a["basis"], a.get("abJahr"), a.get("wechsel", "alle"))
    k = dict(r["kennzahlen"])
    k["n_ausgeschlossen"] = len(r["ausgeschlossen"])
    k["n_kalender_ungeprueft"] = sum(1 for e in r["einzel"] if not e["kalenderBelegt"])
    if r["live"]:
        k["live_id"] = r["live"]["id"]
        k["live_letzter_kurs"] = r["live"]["letzter_kurs"]
        kurve = r["live"]["kurve"] or []
        gefuellt = [v for v in kurve if v is not None]
        k["live_letzter_wert"] = gefuellt[-1] if gefuellt else None
    return k


def baue_snapshot(st: dict, sid: str, haupt: dict, weitere: dict, code_sha: str | None) -> dict:
    if not ID_MUSTER.match(sid):
        raise SystemExit(f"Ungültige Snapshot-Kennung {sid!r}")
    snap = dict(st)
    snap.update({
        "snapshot_id": sid,
        "snapshot_erzeugt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "kursdatenstand": {t: m.get("letzter_kurs") for t, m in st.get("reihen", {}).items()},
        "calc_version": CALC_VERSION,
        "code_sha": code_sha,
        "ansicht": haupt,
        "kennzahlen": kennzahlen(st, haupt),
        "weitere_ansichten": {name: {"ansicht": a, "kennzahlen": kennzahlen(st, a)} for name, a in weitere.items()},
    })
    return snap


def _parse_weitere(werte: list[str]) -> dict:
    aus = {}
    for w in werte or []:
        name, rest = w.split(":", 1)
        reihe, typ, x, y, basis = rest.split(",")
        aus[name] = ansicht(reihe, typ, int(x), int(y), basis)
    return aus


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True)
    ap.add_argument("--reihe", default="^GSPC")
    ap.add_argument("--typ", default="midterm")
    ap.add_argument("--x", type=int, default=20)
    ap.add_argument("--y", type=int, default=20)
    ap.add_argument("--basis", default="t0", choices=["t0", "tx"])
    ap.add_argument("--code-sha", default=None)
    ap.add_argument("--quelle", default=str(REPO / "landing" / "data" / "wahlen_study.json"))
    ap.add_argument("--ziel", default=str(ZIEL))
    ap.add_argument("--weitere", nargs="*", help="name:reihe,typ,x,y,basis")
    a = ap.parse_args()
    st = json.loads(Path(a.quelle).read_text(encoding="utf-8"))
    snap = baue_snapshot(st, a.id, ansicht(a.reihe, a.typ, a.x, a.y, a.basis), _parse_weitere(a.weitere), a.code_sha)
    ziel = Path(a.ziel) / f"{a.id}.json"
    if ziel.exists():
        print(f"{ziel} existiert schon — Snapshots sind unveränderlich, neue Kennung wählen")
        return 1
    ziel.parent.mkdir(parents=True, exist_ok=True)
    ziel.write_text(json.dumps(snap, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    k = snap["kennzahlen"]
    print(f"Snapshot {a.id}: Datenstand {snap['kursdatenstand']}, n={k['n']}, nachher {k['nachlauf_mittel']:+.4f} %, "
          f"Differenz {k['differenz_mittel']:+.4f} Pp → {ziel}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
