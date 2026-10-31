#!/usr/bin/env python3
"""verify_polymarket_status_mutation.py — prueft verify_polymarket_status.py.

Baut jeden Defekt, den Phase B2 schliesst, absichtlich wieder ein und verlangt Rot.
Jede Mutation BENENNT die Pruefung, die sie reissen muss — sonst waere nicht belegt,
dass der Waechter die Wirkung messt und nicht irgendetwas.

Mechanik aus verify_twins_mutation (atomares Schreiben, exklusiver Lauf, frischer
Bytecode-Pfad). Exit des Waechters: 0 gruen, 1 rot (= erkannt), 3 Absturz (= ungueltig,
eine Ausnahme ist kein Nachweis).
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
from scripts.verify_twins_mutation import (_atomar_schreiben, _exklusiver_lauf,  # noqa: E402
                                           _zeilenende, python_probe, LF)

_WAECHTER = _ROOT / "scripts" / "verify_polymarket_status.py"
P = "shared/polymarket_data.py"
S = "shared/supabase_client.py"
D = "scripts/polymarket_discover.py"
R = "scripts/polymarket_refresh.py"
W = ".github/workflows/polymarket_daily.yml"
J = "landing/js/polymarket.js"

MUTATIONEN = [
    # ── Bestaetigt nicht vorhanden (2026-10-31, fed-hike-2026) ─────────────
    ("unavailable + bestaetigt fehlend wieder technischer Fehler", R,
     [('                and db_status == STATUS_UNERREICHBAR):\n', '                and False):\n')],
     "kein Markt, Katalog `unavailable`"),
    ("Ausnahme auch ohne Katalogbeleg", R,
     [('                and db_status == STATUS_UNERREICHBAR):\n', '                and True):\n')],
     "bestaetigt fehlend ohne Katalogbeleg"),
    ("technischer Fehlschlag gilt als bestaetigt fehlend", R,
     [('        if (zustand == "fehler" and bestaetigt_fehlend\n', '        if (zustand == "fehler"\n')],
     "Abruf scheitert technisch, Katalog `unavailable`"),

    # ── Entscheidungstabelle ───────────────────────────────────────────────
    ("closed nur auf Wahrheit geprueft", P,
     [("    if closed is True:\n", "    if closed:\n")],
     "closed kein Wahrheitswert"),

    ("archiviert-aber-offen durchgelassen", P,
     [("    if archiviert is True:\n        # Nicht geschlossen, aber archiviert — widerspruechlich.\n        return STATUS_UNBEKANNT\n",
       "    if False:\n        # Nicht geschlossen, aber archiviert — widerspruechlich.\n        return STATUS_UNBEKANNT\n")],
     # NICHT „archiviert aber offen": dieser Fall ist gegen die Mutation
     # AEQUIVALENT, weil die letzte Bedingung `archiviert is False` ohnehin
     # verlangt. Erst „pausiert UND archiviert" trennt — gemeldet vom
     # Mutationstest, nicht durch Nachdenken gefunden.
     "pausiert und archiviert"),

    ("acceptingOrders null gilt als offen", P,
     [("    if annahme is True and archiviert is False and orderbuch is True:\n",
       "    if archiviert is False and orderbuch is True:\n")],
     "acceptingOrders null, offen"),

    # ── Abdeckung: Dedup und Widerspruch ───────────────────────────────────
    # Die Deduplizierung ist seit dem 2026-10-20 STRUKTURELL: ein dict je cid, und
    # `markets` entsteht am Ende aus den bereits deduplizierten `ids`. Eine kleine
    # Mutation kann sie nicht reissen, ohne die Form umzubauen — mein erster Versuch
    # (`if vorher is None` -> `if True`) riss stattdessen die Widerspruchspruefung
    # und war damit kein Nachweis fuer die Deduplizierung. Geprueft wird deshalb die
    # Stelle, an der das Projekt den Fehler wirklich hatte: eine Mengendifferenz als
    # Beweis fuer „gibt es nicht".
    ("gescheiterte Einzelnachfrage gilt als bestaetigt fehlend", P,
     [("            unklar.add(cid)              # technischer Fehler, keine Aussage\n",
       "            fehlt_bestaetigt.add(cid)    # technischer Fehler, keine Aussage\n")],
     "erneut gescheitert -> unklar, NICHT verschwunden"),

    ("Widerspruch ignoriert", P,
     [("        elif _statusfelder(vorher) != _statusfelder(m):\n            widerspruch.add(cid)\n",
       "        elif False:\n            widerspruch.add(cid)\n")],
     "widerspruechliche Antworten fliegen aus `markets`"),

    # ── Schreibhelfer ──────────────────────────────────────────────────────
    ("Weissliste umgangen", S,
     [('        payload = {f: r[f] for f in _MARKT_ZUSTAND_FELDER if f in r}\n',
       '        payload = {f: v for f, v in r.items() if f != "condition_id"}\n')],
     "ein Feld ausserhalb der Weissliste wird nicht geschrieben"),

    ("NULL-Zweig im Filter entfernt", S,
     [('                   .or_("status.is.null,status.neq.%s" % _STATUS_AUFGELOEST)\n',
       '                   .neq("status", _STATUS_AUFGELOEST)\n')],
     "Status gesetzt, obwohl er vorher NULL war"),

    ("aufgeloeste Zeile verliert ihren Status", S,
     [('        rest = {f: v for f, v in payload.items() if f not in ("status", "active")}\n',
       '        rest = dict(payload)\n')],
     "der Status bleibt `resolved`"),

    # Die Ergaenzung muss HINTER die Weisslisten-Sperre, sonst loest die Mutation
    # den ValueError aus dem B3-Fix aus und stuerzt den Waechter ab — ein Absturz
    # ist kein Nachweis (Beweisregel 4), und der Mutationstest hat ihn korrekt als
    # ungueltig gezaehlt, nicht als erkannt.
    ("Pruefzeitpunkt wird ergaenzt, auch ungefragt", S,
     [("            antwort = (client.table(\"polymarket_markets\")\n"
       "                       .update(payload)\n"
       "                       .eq(\"condition_id\", cid)\n"
       "                       .execute())\n"
       "            zeilen = antwort.data or []\n",
       "            antwort = (client.table(\"polymarket_markets\")\n"
       "                       .update(dict(payload, status_checked_at=\"ERGAENZT\"))\n"
       "                       .eq(\"condition_id\", cid)\n"
       "                       .execute())\n"
       "            zeilen = antwort.data or []\n")],
     "ein nicht uebergebener Pruefzeitpunkt wird NICHT ergaenzt"),

    # ── Katalogabgleich ────────────────────────────────────────────────────
    ("Statusfelder wieder im Metadaten-Upsert", D,
     [('            "meta": meta,\n        })\n        gemessen = status_aus_markt(raw)\n',
       '            "meta": meta,\n            "status": status_aus_markt(raw),\n        })\n'
       '        gemessen = status_aus_markt(raw)\n')],
     "der Upsert enthaelt KEINE Statusfelder"),

    ("ungepruefte IDs bekommen doch eine Anweisung", D,
     [("    # `unklar` bekommt KEINE Anweisung: ein technischer Fehlschlag ist keine\n"
       "    # Aussage ueber den Markt, und ein erneuerter Pruefzeitpunkt waere eine.\n",
       "    for cid in sorted(abdeckung.unklar):\n"
       "        zustaende.append({\"condition_id\": cid, \"status\": STATUS_UNERREICHBAR,\n"
       "                          \"status_checked_at\": jetzt, \"active\": False})\n")],
     "die ungepruefte ID kommt in KEINER Anweisung vor"),

    ("bestaetigt-fehlend legt eine Katalogzeile an", D,
     [("    for cid in sorted(abdeckung.fehlt_bestaetigt):\n        zustaende.append({\"condition_id\": cid, \"status\": STATUS_UNERREICHBAR,\n",
       "    for cid in sorted(abdeckung.fehlt_bestaetigt):\n"
       "        records.append({\"condition_id\": cid, \"slug\": \"x\", \"question\": \"q\",\n"
       "                        \"category\": \"fed\"})\n"
       "        zustaende.append({\"condition_id\": cid, \"status\": STATUS_UNERREICHBAR,\n")],
     "fuer C wird KEINE Katalogzeile angelegt"),

    # ── Erzeuger ───────────────────────────────────────────────────────────
    ("irrefuehrender Name wieder oeffentlich", P,
     [("def _quote_snapshot(market: dict) -> dict | None:\n",
       "def market_to_price_snapshot(market: dict) -> dict | None:\n"
       "    return bewerte_quote(market).get(\"snapshot\")\n\n\n"
       "def _quote_snapshot(market: dict) -> dict | None:\n")],
     "der irrefuehrende oeffentliche Name ist weg"),

    ("db_status wird ignoriert", P,
     [('    endstatus = STATUS_AUFGELOEST if db_status == STATUS_AUFGELOEST else status\n',
       '    endstatus = status\n')],
     "DB `resolved` schlaegt Gamma `open`"),

    ("Status spielt fuer die Freigabe keine Rolle", P,
     [("    if endstatus not in STATUS_BEWERTBAR:\n",
       "    if False:\n")],
     "ein geschlossener Markt gibt keinen aktuellen Snapshot"),

    # ── Refresh ────────────────────────────────────────────────────────────
    ("active nicht mitgeschrieben", R,
     [('            satz["active"] = gemessen in STATUS_SICHTBAR\n', "")],
     "open -> closed setzt active=False"),

    ("Pruefzeitpunkt auch bei gescheitertem Abruf", R,
     [("        if markt is not None:\n", "        if True:\n")],
     "ein gescheiterter Abruf erneuert `status_checked_at` NICHT"),

    ("Rueckgabe des Schreibvorgangs ignoriert", R,
     [("            if cid in erlaubt:\n                behalten.append(r)\n",
       "            if True:\n                behalten.append(r)\n")],
     # Der DB-`resolved`-Fall wird schon von `aktueller_snapshot` geblockt, also
     # kann er die Rueckgabepruefung nicht pruefen. Erst der VERALTETE Katalog
     # (gelesen als `open`, inzwischen `resolved`) trennt die zweite Linie von
     # der ersten — auch das hat der Mutationstest gemeldet.
     "veralteter Katalog (`open`), Zeile inzwischen `resolved`: keine Preiszeile"),

    # ── Exit-Regel ─────────────────────────────────────────────────────────
    ("technische Fehler nicht in der Exit-Regel", R,
     [('        zaehler["technische_fehler"] > 0\n        or not zaehler["schreiben_ok"]\n',
       '        not zaehler["schreiben_ok"]\n')],
     "1 fachlich uebersprungen + 1 technischer Fehler -> Exit 1"),

    ("Katalogauslassung begruendet Erfolg", R,
     [('            zaehler["katalog_fehlt"] += 1\n',
       '            zaehler["fachlich_uebersprungen"] += 1\n')],
     "alle IDs fehlen im DB-Katalog -> Exit 1"),

    ("Schreibfehler nicht in der Exit-Regel", R,
     [('        or not zaehler["schreiben_ok"]\n        or not log_ok\n',
       '        or not log_ok\n')],
     # NICHT „Zustands-Update scheitert -> Exit 1": dieser Fall wird seit dem
     # B1-Fix ohnehin vom letzten Term rot gemacht (keine Freigabe -> 0 Preise),
     # die Mutation waere dort aequivalent. Nur der gemischte Fall traegt sie.
     "nur `schreiben_ok` traegt diesen Fall"),

    # ── Workflow und Lader ─────────────────────────────────────────────────
    ("Katalogabgleich ohne Abbruch", W,
     [('            if ! docker exec seasonalpha-app python3 scripts/polymarket_discover.py --sync-db 2>&1 | tail -40; then\n'
       '              echo "[polymarket-daily] FEHLER: Katalogabgleich fehlgeschlagen"\n'
       '              exit 1\n'
       '            fi\n',
       '            docker exec seasonalpha-app python3 scripts/polymarket_discover.py --sync-db 2>&1 | tail -40 || true\n')],
     "ein Fehlschlag in Schritt 1 bricht ab, bevor Schritt 2 laeuft"),

    ("Lader faellt auf die Tabelle zurueck", J,
     [("      if (!Array.isArray(rows)) {\n",
       "      if (!Array.isArray(rows)) { return SA.supabase.get('polymarket_prices', 'limit=1').then(function(){ return {}; }); }\n"
       "      if (false) {\n")],
     "KEIN Rueckfall auf die Tabelle polymarket_prices"),

    ("Lader prueft die Antwortform nicht", J,
     [("      if (!Array.isArray(rows)) {\n", "      if (false) {\n")],
     # NICHT „ein Fehlerobjekt fuehrt zur ABLEHNUNG": ohne die Formpruefung
     # scheitert `rows.forEach` als TypeError, die Ablehnung kommt also trotzdem —
     # nur eben ZUFAELLIG, genau wie Codex es zu SA.supabase.get gesagt hat. Was
     # kippt, ist die aussagekraeftige Meldung. Der Mutationstest hat das
     # gemeldet, nicht mein Nachdenken.
     "die Meldung nennt die Funktion"),

    # ── Die Gegenfaelle der Code-Abnahme (Codex B1..B7, W1, W2, W4) ────────
    # Jeder von ihnen war im ersten Bau wirklich drin. Sie duerfen nicht
    # zurueckkommen, ohne dass etwas rot wird.

    ("B1: Preise trotz gescheitertem Zustands-Update", R,
     [('        erlaubt: set[str] = set()\n',
       '        erlaubt: set[str] = {r["condition_id"] for r in records}\n')],
     "nach gescheitertem Zustands-Update entsteht KEINE Preiszeile"),

    ("B2: Quotenproblem zaehlt wieder als fachlich", R,
     [('            if (urteil.get("endstatus") or "") not in STATUS_BEWERTBAR:\n',
       '            if True:\n')],
     "gekreuztes Buch zaehlt als Quotenproblem, nicht als fachliche Auslassung"),

    ("B3: Fetch-only ohne Weisslisten-Pruefung", S,
     [('            unerlaubt = sorted(set(payload) - set(_FETCH_ONLY_FELDER))\n',
       '            unerlaubt = []\n')],
     "ohne `status` wird ein Feld ausserhalb der zwei Abruffelder abgelehnt"),

    ("B4: Statusfelder ohne Typ verglichen", P,
     [("        return tuple((type(m.get(f)), m.get(f)) for f in\n",
       "        return tuple((m.get(f),) for f in\n")],
     "`closed=False` gegen `closed=0` ist ein Widerspruch, kein Treffer"),

    ("B5: Nichtexistenz aus fehlender Freigabe geschlossen", D,
     [('        beruehrt = ergebnis.get("beruehrt") or set()\n',
       '        beruehrt = {z.get("condition_id") for z in (ergebnis.get("freigegeben") or [])}\n')],
     "die vorhandene aufgeloeste Zeile wird NICHT als fehlend gemeldet"),

    ("B6: Preise vor dem Upsert gezaehlt", R,
     [('        records.append(build_price_record(cid, snap, now))\n'
       '        zaehler["preise_vorbereitet"] += 1\n',
       '        records.append(build_price_record(cid, snap, now))\n'
       '        zaehler["preise_vorbereitet"] += 1\n        zaehler["preise"] += 1\n')],
     "ein gescheiterter Upsert meldet 0 geschriebene bei 1 vorbereiteten"),

    ("B7: fremde ID in der Einzelnachfrage verworfen", P,
     [("                elif antwort_cid and antwort_cid not in angefragt:\n",
       "                elif False:\n")],
     "eine fremde ID aus der Einzelnachfrage landet in `fremd`"),

    ("W1: Discovery meldet `unklar` nicht nach aussen", D,
     [("    if abgleich_rot:\n        return 1\n    return 0\n",
       "    if abgleich_rot:\n        return 0\n    return 0\n")],
     "main() --sync-db mit einer ungepruefte ID gibt 1 zurueck"),

    ("W2: Lader kehrt sofort zurueck, ohne zu fragen", J,
     [("    if (!conditionIds || !conditionIds.length) return Promise.resolve({});\n",
       "    if (!conditionIds || !conditionIds.length) return Promise.resolve({});\n"
       "    return Promise.resolve({});\n")],
     "probe_polymarket_lader.js laeuft durch"),

    ("W4: Logfehler nicht in der Exit-Regel", R,
     [('        or not log_ok\n        or (success == 0 and zaehler["fachlich_uebersprungen"] == 0 and len(entries) > 0)\n',
       '        or (success == 0 and zaehler["fachlich_uebersprungen"] == 0 and len(entries) > 0)\n')],
     "scheitert die refresh_log-Zeile, ist der Lauf rot"),

    # ── Die Auflagen der zweiten Code-Runde ────────────────────────────────
    ("N1: bestaetigte Aufloesung wird nicht gezaehlt", R,
     [('            elif cid in beruehrt:\n', '            elif False:\n')],
     "bestaetigte fachliche Auslassung und kein Ausfall"),

    ("B8: Ablehnungsgrund wieder auf debug", P,
     [('        app_logger.info("fetch_current_price %s: kein aktueller Preis (%s, status=%s)",\n',
       '        app_logger.debug("fetch_current_price %s: kein aktueller Preis (%s, status=%s)",\n')],
     "der Ablehnungsgrund erscheint auf INFO oder hoeher"),

    ("W1: Backfill dauerhaft abgeschaltet", W,
     [('            if [ "$DOW" = "1" ] || [ "$SA_BACKFILL" = "true" ]; then\n',
       '            if false; then\n')],
     "mit include_backfill=true laeuft Schritt 3 wirklich"),
]

# Mutationen, die der Waechter NICHT fangen kann und auch nicht soll — sie pruefen das
# Urteil des Tests selbst.
UNGUELTIG_ERWARTET = [
    ("Kommentar geaendert (wirkungslos)", P,
     [("# Wie viele IDs in einen Abruf gehen.", "# Wieviele IDs in einen Abruf gehen.")]),
]


def _anwenden(original: bytes, paare, nr: int, name: str):
    le = _zeilenende(original)
    neu = original
    for such, ersatz in paare:
        s = such.encode("utf-8").replace(LF, le)
        e = ersatz.encode("utf-8").replace(LF, le)
        if neu.count(s) != 1:
            print(f"{nr:>2}. [UNGUELTIG] {name} — Anker {neu.count(s)}x: {such[:70]!r}")
            return None
        neu = neu.replace(s, e, 1)
    return neu


# Mindestumfang des Ausgangslaufs. Ein Lauf, der vorzeitig endet, ist kein Nachweis —
# „Exit 1 plus passende FEHL-Zeile" liess bis zum 2026-10-20 einen anschliessend
# abgebrochenen Lauf als gueltig durchgehen (Codex, Befund W5).
MIND_PRUEFUNGEN = 125


def _umfang(ausgabe: str) -> int:
    """Umfang des WAECHTERLAUFS — die LETZTE Endmarker-Zeile.

    Der Waechter bettet bei einem Fehlschlag die Ausgabe der node-Probe ein, und
    die hat ihren eigenen `PROBE-ENDE`-Marker mit 15 Pruefungen. Wer den ersten
    Marker nimmt, haelt drei gueltige Mutationen fuer unvollstaendige Laeufe —
    genau das ist beim ersten Lauf passiert.
    """
    treffer = [z for z in (ausgabe or "").splitlines() if z.startswith("PROBE-ENDE")]
    if not treffer:
        return -1
    try:
        return int(treffer[-1].split()[1])
    except (IndexError, ValueError):
        return -1


def main() -> int:
    unbemerkt, ungueltig = [], []
    with _exklusiver_lauf():
        r0 = python_probe([_WAECHTER], capture_output=True, text=True, cwd=str(_ROOT))
        if r0.returncode != 0:
            print("[FAIL] Waechter ist schon ohne Mutation rot (Exit %d):\n%s"
                  % (r0.returncode, (r0.stdout or "")[-2500:]))
            return 1
        umfang0 = _umfang(r0.stdout)
        if umfang0 < MIND_PRUEFUNGEN:
            print("[FAIL] der Ausgangslauf erreicht den Endmarker nicht oder prueft zu "
                  "wenig: %d (erwartet mindestens %d)" % (umfang0, MIND_PRUEFUNGEN))
            return 1
        print("Ausgangslauf: %d Pruefungen, Endmarker erreicht." % umfang0)

        for nr, (name, datei, paare, pruefung) in enumerate(MUTATIONEN, 1):
            pfad = _ROOT / datei
            original = pfad.read_bytes()
            neu = _anwenden(original, paare, nr, name)
            if neu is None:
                ungueltig.append(name)
                continue
            try:
                _atomar_schreiben(pfad, neu)
                r = python_probe([_WAECHTER], capture_output=True, text=True, cwd=str(_ROOT))
            finally:
                _atomar_schreiben(pfad, original)
                assert pfad.read_bytes() == original, f"{datei} nicht wiederhergestellt"

            if r.returncode == 3:
                print(f"{nr:>2}. [Absturz]   {name} — kein Nachweis")
                ungueltig.append(name)
                continue
            if r.returncode != 1:
                print(f"{nr:>2}. [UNBEMERKT] {name} (Exit {r.returncode})")
                unbemerkt.append(name)
                continue
            # Rot allein genuegt nicht, und auch „rot an der richtigen Zeile" nicht:
            # der Lauf muss seinen Endmarker erreicht haben, sonst kann die Zeile
            # aus einem abgebrochenen Lauf stammen.
            umfang = _umfang(r.stdout)
            if umfang < MIND_PRUEFUNGEN:
                print(f"{nr:>2}. [UNGUELTIG] {name} — Lauf unvollstaendig "
                      f"({umfang} Pruefungen, erwartet mindestens {MIND_PRUEFUNGEN})")
                ungueltig.append(name)
                continue
            getroffen = [z for z in (r.stdout or "").splitlines()
                         if z.startswith("  FEHL") and pruefung in z]
            if getroffen:
                print(f"{nr:>2}. [erkannt]   {name}  ->  {pruefung}")
            else:
                print(f"{nr:>2}. [UNBEMERKT] {name} — rot, aber nicht an "
                      f"\"{pruefung}\"; rot war:")
                for z in (r.stdout or "").splitlines():
                    if z.startswith("  FEHL"):
                        print("        " + z.strip())
                unbemerkt.append(name)

        for nr, (name, datei, paare) in enumerate(UNGUELTIG_ERWARTET, len(MUTATIONEN) + 1):
            pfad = _ROOT / datei
            original = pfad.read_bytes()
            neu = _anwenden(original, paare, nr, name)
            if neu is None:
                ungueltig.append(name)
                continue
            try:
                _atomar_schreiben(pfad, neu)
                r = python_probe([_WAECHTER], capture_output=True, text=True, cwd=str(_ROOT))
            finally:
                _atomar_schreiben(pfad, original)
                assert pfad.read_bytes() == original, f"{datei} nicht wiederhergestellt"
            if r.returncode == 0 and _umfang(r.stdout) >= MIND_PRUEFUNGEN:
                print(f"{nr:>2}. [wirkungslos, richtig] {name}")
            elif r.returncode == 0:
                print(f"{nr:>2}. [UNGUELTIG] {name} — gruen, aber Lauf unvollstaendig "
                      f"({_umfang(r.stdout)})")
                ungueltig.append(name)
            else:
                print(f"{nr:>2}. [FALSCHALARM] {name} — rot ohne wirksame Aenderung "
                      f"(Exit {r.returncode})")
                unbemerkt.append(name)

    gesamt = len(MUTATIONEN) + len(UNGUELTIG_ERWARTET)
    print()
    if unbemerkt or ungueltig:
        print(f"[FAIL] unbemerkt {len(unbemerkt)}, ungueltig {len(ungueltig)} von {gesamt}")
        return 1
    print(f"[OK] Alle {len(MUTATIONEN)} Mutationen an der benannten Pruefung erkannt, "
          f"{len(UNGUELTIG_ERWARTET)} wirkungslose richtig durchgelassen.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
