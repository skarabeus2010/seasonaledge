#!/usr/bin/env python3
"""
SeasonAlpha — Polymarket Refresh

Zieht fuer alle aktiven Maerkte im Katalog einen aktuellen Preis-Snapshot
aus der CLOB API und schreibt ihn nach Supabase polymarket_prices.

Nutzung:
    py scripts/polymarket_refresh.py                    # alle aktiven Maerkte
    py scripts/polymarket_refresh.py --category fed     # nur Fed-Maerkte
    py scripts/polymarket_refresh.py --refresh hourly   # nur hourly-Tier
    py scripts/polymarket_refresh.py --near-fomc-only   # nur wenn FOMC ±2d
    py scripts/polymarket_refresh.py --dry-run
"""
from __future__ import annotations

import argparse
import sys
import os
import pathlib
import time
from datetime import datetime, timezone

try:
    _project_dir = str(pathlib.Path(__file__).resolve().parent.parent)
except NameError:
    _project_dir = os.getcwd()
if _project_dir not in sys.path:
    sys.path.insert(0, _project_dir)

from shared.polymarket_data import (
    STATUS_SICHTBAR,
    load_markets_yaml,
)
from shared.logger import app_logger, error_logger


def build_price_record(condition_id: str, snap: dict, ts: datetime) -> dict:
    return {
        "condition_id": condition_id,
        "ts": ts.isoformat(),
        "yes_price": snap["yes_price"],
        "volume_24h": snap.get("volume_24h"),
        "spread": snap.get("spread"),
        # Die Zeile stammt aus der Gamma-API (fetch_current_price ->
        # fetch_market_by_condition_id), NICHT aus dem CLOB-Orderbuch. Die
        # bisherige Angabe "clob" war falsch und haette bei jeder Auswertung
        # nach Quelle in die Irre gefuehrt. Nichts filtert heute darauf
        # (geprueft), die Berichtigung ist also folgenlos — ALTE Zeilen tragen
        # weiterhin die falsche Angabe, das laesst sich ohne Migration nicht
        # ruekwirkend richtigstellen.
        "source": "gamma-snapshot",
        # Neu mit der Migration vom 2026-10: woraus der Preis entstand, die
        # beiden Quotes, und der Abrufzeitpunkt getrennt von `ts`. Bei einem
        # Snapshot sind beide gleich — Gamma nennt keine Quotenzeit, und ein
        # Abrufzeitpunkt darf nicht als Quotenalter ausgegeben werden.
        "price_kind": snap.get("price_kind"),
        "bid": snap.get("bid"),
        "ask": snap.get("ask"),
        "fetched_at": ts.isoformat(),
    }


def refresh_markets(
    entries: list[dict],
    dry_run: bool = False,
) -> tuple[dict, list[str]]:
    """
    Schreibt Preis-Snapshots fuer die gegebenen YAML-Eintraege.

    Returns (zaehler, errors). `zaehler` hat vier Felder, und nur zwei davon
    begruenden einen Erfolg (siehe `main`):

      preise                 Preiszeile geschrieben
      fachlich_uebersprungen Markt ERREICHT, Status gemessen, nicht bewertbar
      katalog_fehlt          condition_id nicht im DB-Katalog — nie abgefragt
      technische_fehler      Abruf gescheitert, Ausnahme, kein Markt
      schreiben_ok           beide Schreibwege (Zustand, Preise) gelungen

    Die Trennung von `fachlich_uebersprungen` und `katalog_fehlt` ist nicht
    kosmetisch: wuerden fehlende Katalogeintraege als fachliche Auslassung
    zaehlen, waere ein Lauf, der keinen einzigen Markt bearbeitet hat, gruen
    (Codex, Befund N2) — heute endet derselbe Fall ueber `success == 0` rot.
    """
    from shared.supabase_client import (
        fetch_polymarket_markets as _fetch_catalog,
        upsert_polymarket_prices,
        update_polymarket_markt_zustand,
    )
    from shared.polymarket_data import (aktueller_snapshot, fetch_market_by_condition_id,
                                        status_aus_markt)

    # Katalog aus DB laden (token_id-Mapping liegt dort). `active_only=False` ist
    # Pflicht: ein geschlossener oder unerreichbarer Markt ist `active=False` und
    # wuerde sonst als „nicht im Katalog" gelten, obwohl er dort steht.
    catalog = _fetch_catalog(active_only=False)
    by_cid = {c["condition_id"]: c for c in catalog}

    records = []
    zustaende: list[dict] = []
    errors: list[str] = []
    zaehler = {"preise": 0, "fachlich_uebersprungen": 0, "katalog_fehlt": 0,
               "technische_fehler": 0, "schreiben_ok": True}
    now = datetime.now(timezone.utc)

    for i, entry in enumerate(entries, 1):
        slug = entry["slug"]
        cid = (entry.get("condition_id") or "").strip()
        if not cid:
            app_logger.debug(f"skip {slug}: keine condition_id in YAML")
            continue

        cat_entry = by_cid.get(cid)
        if not cat_entry:
            zaehler["katalog_fehlt"] += 1
            errors.append(f"{slug}: nicht im DB-Katalog (erst 'polymarket_discover --sync-db' laufen lassen)")
            continue

        # Die conditionId geht an den Gamma-Markets-Endpoint; yes_token_id
        # braucht nur die CLOB-Historie (Backfill).
        #
        # `aktueller_snapshot` statt `bewerte_quote`, weil zwei Dinge zu pruefen
        # sind und die Regel zum ERZEUGER gehoert: die Quotenqualitaet UND der
        # Marktstatus. Ein geschlossener Markt liefert bei Gamma
        # `outcomePrices ["0","0"]`; diese Zeile als frischen Preis zu speichern
        # waere derselbe Fehler, den B1 an der Quotenseite geschlossen hat.
        # Der GRUND bleibt erhalten: „kein Preis geliefert", „Buch gekreuzt" und
        # „Markt geschlossen" sind verschiedene Lagen.
        db_status = cat_entry.get("status")
        try:
            markt = fetch_market_by_condition_id(cid)
            if markt:
                urteil = aktueller_snapshot(markt, db_status=db_status)
            else:
                urteil = {"status": None, "endstatus": None, "preis_freigegeben": False,
                          "grund": "kein_markt",
                          "quote": {"status": "fehler", "grund": "kein_markt"},
                          "snapshot": None}
                markt = None
        except Exception as e:                     # Netz, Zeitueberschreitung
            markt = None
            urteil = {"status": None, "endstatus": None, "preis_freigegeben": False,
                      "grund": type(e).__name__,
                      "quote": {"status": "fehler", "grund": type(e).__name__},
                      "snapshot": None}

        quote_status = (urteil.get("quote") or {}).get("status")
        zustand = quote_status if quote_status in ("ok", "kein_preis", "verworfen") else "fehler"
        satz = {"condition_id": cid,
                "last_fetch_state": zustand,
                "last_fetch_at": now.isoformat()}
        if markt is not None:
            # Status nur, wenn wir wirklich eine Antwort hatten. Ein gescheiterter
            # Abruf erneuert `status_checked_at` NICHT — geprueft wurde nichts.
            gemessen = status_aus_markt(markt)
            satz["status"] = gemessen
            satz["status_checked_at"] = now.isoformat()
            # `active` gehoert in dieselbe Anweisung: Frontend und Newsletter
            # filtern ausschliesslich darauf, ein geschlossener Markt bliebe
            # sonst bis zum naechsten Katalogabgleich sichtbar und ein
            # wiederaufgetauchter unsichtbar (Codex, Befund B4).
            satz["active"] = gemessen in STATUS_SICHTBAR
        zustaende.append(satz)

        if zustand == "fehler":
            zaehler["technische_fehler"] += 1
            errors.append(f"{slug}: Abruf fehler"
                          + (f" ({urteil.get('grund')})" if urteil.get("grund") else ""))
            print(f"  [{i:2d}/{len(entries)}] {slug:40s} -- FEHLER"
                  f": {urteil.get('grund') or '-'}")
            continue

        if not urteil.get("preis_freigegeben"):
            # Fachlich uebersprungen: der Markt war erreichbar, aber sein Status
            # oder seine Quote laesst keinen aktuellen Preis zu. Kein Ausfall.
            zaehler["fachlich_uebersprungen"] += 1
            errors.append(f"{slug}: kein Preis ({urteil.get('grund')})")
            print(f"  [{i:2d}/{len(entries)}] {slug:40s} -- UEBERSPRUNGEN"
                  f": {urteil.get('grund') or '-'}")
            continue

        snap = urteil["snapshot"]
        records.append(build_price_record(cid, snap, now))
        zaehler["preise"] += 1
        print(
            f"  [{i:2d}/{len(entries)}] {slug:40s} "
            f"YES={snap['yes_price']:.3f}  "
            f"spread={snap.get('spread') if snap.get('spread') is not None else float('nan'):.3f}  "
            f"{snap.get('price_kind')}"
        )

    if not dry_run:
        # Die Zustaende werden AUCH dann geschrieben, wenn keine einzige
        # Preiszeile entstand — gerade dann sind sie die Information. Ein
        # Fehlschlag hier ist ein Fehlschlag des Laufs und wird nicht
        # verschluckt. Beide Schreibwege werden GETRENNT bewertet, damit der
        # Erfolg des einen den Ausfall des anderen nicht verdeckt.
        if zustaende:
            try:
                geschrieben = update_polymarket_markt_zustand(zustaende)
                # Die Rueckgabe ist die Entscheidungsgrundlage fuer die
                # Preisfreigabe: fehlt ein Markt darin, war seine Zeile
                # aufgeloest (oder existiert nicht). Eine solche Preiszeile wird
                # verworfen, BEVOR sie geschrieben wird.
                erlaubt = {z.get("condition_id") for z in (geschrieben or [])}
                vorher = len(records)
                records = [r for r in records if r["condition_id"] in erlaubt]
                verworfen = vorher - len(records)
                if verworfen:
                    zaehler["preise"] -= verworfen
                    zaehler["fachlich_uebersprungen"] += verworfen
                    errors.append(f"{verworfen} Preiszeile(n) verworfen: Markt in der "
                                  f"Datenbank aufgeloest oder nicht vorhanden")
            except Exception as e:
                zaehler["schreiben_ok"] = False
                errors.append(f"Zustands-Update gescheitert: {type(e).__name__}: {e}")
        if records:
            try:
                upsert_polymarket_prices(records)
            except Exception as e:
                zaehler["schreiben_ok"] = False
                errors.append(f"Preis-Upsert gescheitert: {type(e).__name__}: {e}")

    return zaehler, errors


def filter_entries(
    entries: list[dict],
    category: str | None = None,
    refresh_tier: str | None = None,
) -> list[dict]:
    out = entries
    if category:
        wanted = set(c.strip().lower() for c in category.split(","))
        out = [e for e in out if e.get("category", "").lower() in wanted]
    if refresh_tier:
        out = [e for e in out if e.get("refresh", "").lower() == refresh_tier.lower()]
    return out


def main():
    ap = argparse.ArgumentParser(description="Polymarket Refresh (Snapshot)")
    ap.add_argument("--category", default=None,
                    help="Komma-getrennte Liste: fed,macro,index,events,crypto")
    ap.add_argument("--refresh", default=None, choices=["hourly", "daily"],
                    help="Nur Maerkte dieses Refresh-Tiers")
    ap.add_argument("--near-fomc-only", action="store_true",
                    help="Nur ausfuehren wenn heute innerhalb des FOMC-Fensters liegt "
                         "(FOMC-Tag -2 bis +1). Sonst Early-Exit ohne Fehler.")
    ap.add_argument("--dry-run", action="store_true",
                    help="Nichts in DB schreiben, nur logging")
    args = ap.parse_args()

    t0 = time.time()

    if args.near_fomc_only:
        from shared.fed_dates import is_near_fomc
        if not is_near_fomc():
            print(f"  [fomc-gate] Heute {datetime.now(timezone.utc).strftime('%Y-%m-%d')} "
                  f"nicht im FOMC-Fenster (+/-2d). Early-Exit.")
            # Auch der Skip hinterlaesst eine Zeile: der Health-Check erkennt am
            # Alter der letzten Zeile, ob der stuendliche Timer ueberhaupt laeuft.
            return 0 if _log_intraday(0, 0, [], t0, skip=True, dry_run=args.dry_run) else 1

    data = load_markets_yaml()
    entries = filter_entries(data.get("markets", []), args.category, args.refresh)

    print("=" * 60)
    print(f"  SeasonAlpha — Polymarket Refresh")
    print(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    if args.dry_run:
        print("  ** DRY RUN **")
    print(f"  Maerkte in Scope: {len(entries)}")
    if args.category:
        print(f"  Kategorie-Filter: {args.category}")
    if args.refresh:
        print(f"  Refresh-Tier:     {args.refresh}")
    print("=" * 60)

    if not entries:
        print("\n  Keine Maerkte im Scope.")
        if args.near_fomc_only:
            # Im FOMC-Fenster ohne Maerkte ist die YAML kaputt oder leer — ein Ausfall,
            # der sonst als stiller Erfolg ohne Log-Zeile durchginge.
            _log_intraday(0, 0, ["keine Maerkte im Scope (markets.yaml leer?)"], t0,
                          skip=False, dry_run=args.dry_run)
            return 1
        return 0

    try:
        zaehler, errors = refresh_markets(entries, dry_run=args.dry_run)
    except Exception as e:
        # Schreibfehler der Snapshots: frueher ungefangen ohne Log-Zeile.
        zaehler = {"preise": 0, "fachlich_uebersprungen": 0, "katalog_fehlt": 0,
                   "technische_fehler": 1, "schreiben_ok": False}
        errors = [f"upsert/abruf abgebrochen: {e}"]
    success = zaehler["preise"]
    elapsed = time.time() - t0

    print(f"\n{'=' * 60}")
    print(f"  Fertig! {success}/{len(entries)} Snapshots in {elapsed:.1f}s")
    print(f"  Preise {success} · fachlich uebersprungen "
          f"{zaehler['fachlich_uebersprungen']} · nicht im Katalog "
          f"{zaehler['katalog_fehlt']} · technische Fehler "
          f"{zaehler['technische_fehler']} · Schreiben "
          f"{'ok' if zaehler['schreiben_ok'] else 'GESCHEITERT'}")
    if errors:
        print(f"  Fehler ({len(errors)}):")
        for err in errors:
            print(f"    - {err}")
    print("=" * 60)

    if errors:
        app_logger.info(f"polymarket_refresh: {success} ok, {len(errors)} Fehler")

    log_ok = True
    if args.near_fomc_only:
        log_ok = _log_intraday(len(entries), success, errors, t0, skip=False, dry_run=args.dry_run)

    # Exit-Regel mit vier Zaehlern (Codex-Freigabe 2026-10-20, Runde 4).
    #
    # Fachliches Ueberspringen allein ist GRUEN: ein Tag, an dem alle Maerkte
    # legitim geschlossen sind, darf den Backfill nicht verhindern. Es
    # neutralisiert aber nichts — ein einziger technischer Fehler macht rot,
    # sonst haette „1 geschlossen, 25 Abruffehler" als Erfolg gegolten.
    #
    # `katalog_fehlt` begruendet KEINEN Erfolg: sonst waere ein Lauf, der keinen
    # einzigen Markt bearbeitet hat (alle 26 fehlen im Katalog), gruen — heute
    # endet derselbe Fall ueber `success == 0` rot. Es ist aber auch kein
    # technischer Fehler, sonst waere jeder Lauf vor dem ersten Katalogabgleich
    # rot.
    rot = (
        zaehler["technische_fehler"] > 0
        or not zaehler["schreiben_ok"]
        or not log_ok
        or (success == 0 and zaehler["fachlich_uebersprungen"] == 0 and len(entries) > 0)
    )
    return 1 if rot else 0


def _log_intraday(total: int, success: int, errors: list[str], t0: float,
                  skip: bool, dry_run: bool) -> bool:
    """refresh_log-Zeile run_type='polymarket_intraday' (nur im stuendlichen Modus)."""
    if dry_run:
        return True
    try:
        import json as _json
        from shared.supabase_client import get_client
        now = datetime.now(timezone.utc)
        get_client().table("refresh_log").insert({
            "run_date": now.strftime("%Y-%m-%d"),
            "run_type": "polymarket_intraday",
            "tickers_total": total,
            "tickers_success": success,
            "tickers_missing": len(errors),
            "missing_details": _json.dumps({"skip": "ausserhalb FOMC-Fenster"} if skip else {}),
            "auto_fixed": 0,
            "duration_seconds": round(time.time() - t0, 1),
            "errors": _json.dumps(errors[:20]),
        }).execute()
        return True
    except Exception as e:
        print(f"[polymarket] refresh_log insert failed: {e}")
        return False


if __name__ == "__main__":
    sys.exit(main())
