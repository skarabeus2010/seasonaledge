#!/usr/bin/env python3
"""verify_gex_spot_mutation.py — prueft verify_gex_spot.py.

Ein gruener Waechter sagt nichts, bis er nachweislich rot werden kann. Jede Mutation
BENENNT die Pruefung, die sie reissen muss. Mechanik aus verify_twins_mutation.
Exit des Waechters: 0 gruen, 1 rot (= erkannt), 3 Absturz (= ungueltig, kein Nachweis).

Die Mutationen treffen den PRODUKTIONSPFAD: die Spot-Regel in snapshot_gex_massive.py,
den Statusvertrag in gex_kette.py und die Vertragsdateien (Unit, Timer, Installer,
Workflow, Produktionssperre). Ein fehlender Anker oder ein Absturz zaehlt als ungueltig,
nicht als gefangen.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
from scripts.verify_twins_mutation import (_atomar_schreiben, _exklusiver_lauf,  # noqa: E402
                                           _zeilenende, python_probe, LF)

_WAECHTER = _ROOT / "scripts" / "verify_gex_spot.py"
G = "scripts/snapshot_gex_massive.py"
K = "scripts/gex_kette.py"
U = "deploy/systemd/sa-gex-snapshot.service"
T = "deploy/systemd/sa-gex-snapshot.timer"
I = "deploy/install_timers.sh"
W = ".github/workflows/gex_snapshot.yml"
P = "shared/produktionssperre.py"
MIND_PRUEFUNGEN = 75


def _umfang(ausgabe: str) -> int:
    treffer = [z for z in (ausgabe or "").splitlines() if z.startswith("PROBE-ENDE")]
    if not treffer:
        return -1
    try:
        return int(treffer[-1].split()[1])
    except (IndexError, ValueError):
        return -1


MUTATIONEN = [
    # ── Spot-Regel: der Rueckfall oeffnet zu weit ────────────────────────────────────
    ("Rueckfall bei JEDEM Grund, nicht nur bei fehlendem Kurs", G,
     [("    if grund == GRUND_KURS_FEHLT:\n", "    if grund != GRUND_OK:\n")],
     "[4] rmt vor Schluss"),

    ("Schlussnachweis gar nicht geprueft", G,
     [("    if not _zeit_gueltig(rmt) or _als_zeit(rmt) < schluss:\n"
       "        return None, GRUND_KEIN_SCHLUSSNACHWEIS\n",
       "    if False:\n        return None, GRUND_KEIN_SCHLUSSNACHWEIS\n")],
     "[4] rmt vor Schluss"),

    ("Sessionschluss fest 16:00 statt Halbtag aus dem Kalender", G,
     [('    if info.get("halbtag") is True and info.get("schlusszeit"):\n',
       '    if False and info.get("halbtag") is True and info.get("schlusszeit"):\n')],
     "[10a] Halbtag"),

    # ── Massive-Adapter: Datum, Symbol, Einheit, Zahlenvertrag ──────────────────────
    ("Massive-Balkendatum nicht gegen die Session geprueft", G,
     [("    if _als_zeit(t, 1000).astimezone(_NY).date() != session:\n", "    if False:\n")],
     "[3] Massive-Balken der Vorsession"),

    ("genau EIN Aggregat nicht verlangt", G,
     [('    if not isinstance(ergebnisse, list) or len(ergebnisse) != 1:\n',
       '    if not isinstance(ergebnisse, list) or not ergebnisse:\n')],
     "[5b] Massive: nicht genau ein Aggregat"),

    ("Zahlenvertrag: bool gilt als Kurs", G,
     [("    if isinstance(c, bool) or not isinstance(c, (int, float)):\n",
       "    if not isinstance(c, (int, float)):\n")],
     "[6] Massive c als bool"),

    ("Zahlenvertrag: inf gilt als Kurs", G,
     [("    return _endlich(c) and c > 0\n", "    return c > 0\n")],
     "[6] Massive c = inf"),

    ("Rueckfall auch fuer Symbole ausserhalb des Universums", G,
     [("    if sym not in _RUECKFALL_SYMBOLE:\n", "    if False:\n")],
     "[11] Symbol ausserhalb des Universums"),

    ("bereinigter Kurs statt unbereinigt (adjusted=true)", G,
     [('_PREV = "https://api.polygon.io/v2/aggs/ticker/{sym}/prev?adjusted=false"',
       '_PREV = "https://api.polygon.io/v2/aggs/ticker/{sym}/prev?adjusted=true"')],
     "[12] Massive-URL mit adjusted=false"),

    # ── Yahoo-Adapter ───────────────────────────────────────────────────────────────
    ("Yahoo: Laengen von timestamp und close nicht geprueft", G,
     [("    if len(ts) != len(closes):\n        return None, GRUND_STRUKTUR\n",
       "    if False:\n        return None, GRUND_STRUKTUR\n")],
     "[7] Yahoo timestamp/close verschieden lang"),

    ("Yahoo: mehrere Balken der Session erlaubt", G,
     [("    if len(treffer) > 1:\n", "    if False:\n")],
     "[5a] Yahoo: mehrere Balken der Session"),

    ("Yahoo: ungueltiger Kurs gilt als Kurs", G,
     [("    return (float(treffer[0]), GRUND_OK) if _kurs_gueltig(treffer[0]) else (None, GRUND_KURS_FEHLT)\n",
       "    return (float(treffer[0] or 0), GRUND_OK)\n")],
     "[7c] Yahoo-Kurs"),

    # ── Wiederholung bei 429 ────────────────────────────────────────────────────────
    ("kein 429-Backoff (erster Versuch entscheidet)", G,
     [("            if e.code != 429 or i >= tries - 1:\n                raise\n",
       "            raise\n")],
     "[8a] 429 dann Erfolg"),

    # ── Handelstagpruefung ──────────────────────────────────────────────────────────
    ("Handelstagpruefung entfernt", G,
     [("        if not is_trading_day(heute_ny, \"NYSE\"):\n", "        if False:\n")],
     "[16] Feiertag, automatisch"),

    ("Handelstagpruefung greift auch bei --reparatur", G,
     [("    if not a.no_write and not a.reparatur:\n", "    if not a.no_write:\n")],
     "[17] Feiertag, --reparatur"),

    ("Handelstagpruefung mit UTC-Datum statt New York", G,
     [("        heute_ny = _uhr(_NY).date()\n", "        heute_ny = _uhr(timezone.utc).date()\n")],
     "[16b] Feiertag, Lauf 01:30 UTC"),

    # ── Marker ──────────────────────────────────────────────────────────────────────
    ("Trockenlauf meldet veroeffentlicht", G,
     [("        _marker(ERG_TROCKEN)\n", "        _marker(ERG_VEROEFFENTLICHT)\n")],
     "[19] Handelstag, --no-write"),

    ("Feiertagslauf meldet keinen Marker", G,
     [('            _marker(ERG_UEBERSPRUNGEN, f"kein Handelstag {heute_ny}")\n', "")],
     "[16] Feiertag, automatisch"),

    # ── Kettenvertrag ───────────────────────────────────────────────────────────────
    ("Exit 75 gilt als Fehler statt als Unterdrueckung", K,
     [("    if rc == EXIT_GESPERRT:\n", "    if False:\n")],
     "[13] Exit 75 OHNE Marker"),

    ("Fehlerexit mit veroeffentlicht-Marker gibt Key Levels frei", K,
     [("    if rc != 0:\n", "    if rc not in (0, 1):\n")],
     "[13] Exit 1 TROTZ"),

    ("fehlender Marker gilt als veroeffentlicht", K,
     [('    if len(marker) != 1 or marker[0] not in BEKANNT:\n        return "fehlgeschlagen", 1\n',
       '    if not marker:\n        return VEROEFFENTLICHT, 0\n')],
     "[13] Exit 0 OHNE Marker"),

    ("mehrere Marker: der erste gewinnt", K,
     [("    if len(marker) != 1 or marker[0] not in BEKANNT:\n",
       "    if not marker or marker[0] not in BEKANNT:\n")],
     "[13] Exit 0 + ZWEI Marker"),

    ("Key Levels laufen bei jedem Ergebnis", K,
     [("    if ergebnis != VEROEFFENTLICHT:\n", "    if False:\n")],
     "[14] uebersprungen"),

    ("Key-Levels-Fehler wird verschluckt", K,
     [("    if rc_kl != 0:\n", "    if False:\n")],
     "[14] Key Levels fehlgeschlagen"),

    # ── C2: Symbolnachweis ──────────────────────────────────────────────────────────
    ("Antwort ohne Symbol wird akzeptiert", G,
     [("    if not symbole:\n", "    if False:\n")],
     "[6b] Massive ohne jedes Symbolfeld"),

    ("widersprechendes Symbol wird akzeptiert", G,
     [("    if any(str(f).upper() != sym.upper() for f in symbole):\n", "    if False:\n")],
     "[6] Massive falsches Symbol"),

    # ── C3: Strukturabsicherung und Zeitumrechnung ──────────────────────────────────
    ("AttributeError nicht gefangen (result = [null])", G,
     [("    except (KeyError, IndexError, TypeError, AttributeError):\n",
       "    except (KeyError, IndexError, TypeError):\n")],
     "[6c] Yahoo result = [null]"),

    ("Listentypen nicht geprueft", G,
     [("    if not isinstance(ts, list) or not isinstance(closes, list):\n", "    if False:\n")],
     "[6c] Yahoo timestamp keine Liste"),

    ("Zeitstempel ohne Gueltigkeitspruefung umgerechnet (Yahoo rmt)", G,
     [("    if not _zeit_gueltig(rmt) or _als_zeit(rmt) < schluss:\n",
       "    if _als_zeit(rmt) < schluss:\n")],
     "[6c] Yahoo rmt = NaN"),

    ("Balkenzeit ohne Gueltigkeitspruefung", G,
     [("        if not _zeit_gueltig(t):\n            return None, GRUND_STRUKTUR\n",
       "        if False:\n            return None, GRUND_STRUKTUR\n")],
     "[6c] Yahoo timestamp als Text"),

    ("Massive-Zeitbereich nicht geprueft (1e30 laeuft auf)", G,
     [("    if not _zeit_gueltig(t, 1000):\n", "    if isinstance(t, bool) or not isinstance(t, (int, float)):\n")],
     "[6b] Massive Zeitstempel 1e30"),

    # ── C4: Retry-After ─────────────────────────────────────────────────────────────
    ("Retry-After wird ignoriert (nur eigener Backoff)", G,
     [("            pause = _retry_after(e)\n", "            pause = None\n")],
     "[8d] Retry-After 7 s wird beachtet"),

    ("Wartebudget unbegrenzt (Retry-After 600 wird abgewartet)", G,
     [("            if _gewartet_gesamt + pause > _WARTE_BUDGET:\n", "            if False:\n")],
     "[8e] Retry-After 600 s sprengt das Wartebudget"),

    ("Wartebudget je Abruf statt fuer den ganzen Lauf", G,
     [("            _gewartet_gesamt += pause\n", "            pass\n")],
     "[8f] Wartebudget gilt fuer den ganzen Lauf"),

    # ── C5: atomares Schreiben in den ECHTEN Erzeugern ─────────────────────────────
    ("Snapshot schreibt Summary wieder nicht atomar", G,
     [('    write_json_atomic(_DATA / "gex_summary.json", summary, indent=2)\n',
       '    (_DATA / "gex_summary.json").write_text(\n'
       '        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")\n')],
     "[21a-1] Abbruch beim Schreiben der Summary"),

    ("Snapshot schreibt Profile wieder nicht atomar", G,
     [('def _marker(ergebnis: str, warum: str = "") -> None:',
       'def _roh(pfad, obj, indent=None):\n    pfad.parent.mkdir(parents=True, exist_ok=True)\n    pfad.write_text(json.dumps(obj, indent=indent, ensure_ascii=False), encoding="utf-8")\n\n\ndef _marker(ergebnis: str, warum: str = "") -> None:'),
      ('        write_json_atomic(_DATA / f"gex_profile_',
       '        _roh(_DATA / f"gex_profile_')],
     '[21a-2] Abbruch beim Schreiben der Profil'),

    ("Snapshot schreibt Archiv wieder nicht atomar", G,
     [('def _marker(ergebnis: str, warum: str = "") -> None:',
       'def _roh(pfad, obj, indent=None):\n    pfad.parent.mkdir(parents=True, exist_ok=True)\n    pfad.write_text(json.dumps(obj, indent=indent, ensure_ascii=False), encoding="utf-8")\n\n\ndef _marker(ergebnis: str, warum: str = "") -> None:'),
      ('    write_json_atomic(hist / f"{stamp}.json", slim, indent=None)',
       '    _roh(hist / f"{stamp}.json", slim, indent=None)')],
     '[21a-3] Abbruch beim Schreiben der Archiv'),

    ("Key-Levels-CLI ignoriert --no-write", "scripts/compute_key_levels.py",
     # Anker nachgezogen (B2): die Zeile nimmt jetzt Datei und Laufkennung mit.
     [("        build(a.tickers, not a.no_write, a.gex_datei, a.lauf)",
       "        build(a.tickers, True, a.gex_datei, a.lauf)")],
     "[23] compute_key_levels direkt mit --no-write"),

    ("grosse Ganzzahl laesst isfinite platzen", G,
     [('    return _endlich(c) and c > 0\n',
       '    return math.isfinite(c) and c > 0\n')],
     "[6b] Massive Kurs 10**400 (Ganzzahl)"),

    ("Key Levels ohne Wartebudget", "scripts/compute_key_levels.py",
     [('            if _gewartet_gesamt + pause > _WARTE_BUDGET:\n',
       '            if False:\n')],
     "[27] Wartebudget der Key Levels wirkt"),

    ("Key Levels schreibt wieder nicht atomar", "scripts/compute_key_levels.py",
     [("        write_json_atomic(p, out, indent=2)",
       '        p.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")')],
     "[21b] Abbruch im Key-Levels-Schreibzugriff"),

    # ── C6: Reissleine und Reparaturlauf ───────────────────────────────────────────
    ("Reissleine abgeschaltet (halber Lauf ueberbuegelt die Dateien)", G,
     [("    if len(results) < 0.6 * len(universe):\n", "    if False:\n")],
     "[22a] 5 von 10 brauchbar"),

    ("Reissleine zu scharf (6 von 10 fallen durch)", G,
     [("    if len(results) < 0.6 * len(universe):\n", "    if len(results) < 0.7 * len(universe):\n")],
     "[22b] 6 von 10 brauchbar"),

    ("Reparaturlauf schreibt kein Archiv", G,
     [('    write_json_atomic(hist / f"{stamp}.json", slim, indent=None)\n', "")],
     "[17] Feiertag, --reparatur"),

    # ── Betriebsvertrag ─────────────────────────────────────────────────────────────
    ("Timer laeuft taeglich statt Mo-Fr", T,
     [("OnCalendar=Mon..Fri 22:15:00 UTC", "OnCalendar=*-*-* 22:15:00 UTC")],
     "[22] Timer:"),

    ("Timer holt verpasste Termine nach", T,
     [("Persistent=false", "Persistent=true")],
     "[22] Timer:"),

    ("Timeout nur am docker-Client, nicht im Container", U,
     [("timeout --kill-after=30s 28m python3 -u scripts/gex_kette.py",
       "python3 -u scripts/gex_kette.py")],
     "[23] Unit: Timeout IM Container"),

    ("zwei ExecStart-Zeilen (Lock zwischen den Schritten frei)", U,
     [("ExecStart=/usr/bin/docker exec seasonalpha-app timeout --kill-after=30s 28m python3 -u scripts/gex_kette.py",
       "ExecStart=/usr/bin/docker exec seasonalpha-app python3 -u scripts/snapshot_gex_massive.py\n"
       "ExecStart=/usr/bin/docker exec seasonalpha-app python3 -u scripts/compute_key_levels.py")],
     "[24] Unit: genau EIN ExecStart"),

    ("Exit 75 der Unit gilt als Fehler", U,
     [("SuccessExitStatus=75", "# SuccessExitStatus=75")],
     "[26] Unit: Exit 75 als Erfolg"),

    ("Unit nicht im Installer", I,
     [(" sa-gex-snapshot.service)", ")")],
     "[27] Installer kennt Service und Timer"),

    ("Workflow bekommt wieder einen Zeitplan (Doppellauf)", W,
     [("on:\n  workflow_dispatch:", "on:\n  schedule:\n    - cron: '15 22 * * 1-5'\n  workflow_dispatch:")],
     "[28] Workflow OHNE Zeitplan"),

    ("Notausloeser ohne --reparatur (am Feiertag wertlos)", W,
     [("python3 -u scripts/gex_kette.py --reparatur 2>&1 | tail -40",
       "python3 -u scripts/gex_kette.py 2>&1 | tail -40")],
     "[29] Workflow-Notausloeser ruft die Huelle"),

    ("Programme zurueck in AUSNAHMEN (Deploy wartet nicht)", P,
     [('    "snapshot_gex_massive.py": "GEX-Snapshot: Session-Stempel + Archiv",\n', "")],
     "[31] beide Programme und die Huelle sind PFLICHT"),
]

UNGUELTIG_ERWARTET = [
    # Aenderung ohne Wirkung: der Waechter darf NICHT rot werden. Prueft das Urteil des
    # Mutationstests selbst — meldet er hier "gefangen", ist er zu empfindlich.
    ("Kommentar umformuliert (wirkungslos)", G,
     [("# Yahoo traegt den regulaeren Termin.", "# Yahoo traegt den regulaeren Abendtermin.")]),
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


def _lauf(nr, name, datei, paare, erwartung, soll_rot=True):
    """Gibt 'gefangen' | 'unbemerkt' | 'ungueltig'."""
    pfad = _ROOT / datei
    original = pfad.read_bytes()
    neu = _anwenden(original, paare, nr, name)
    if neu is None:
        return "ungueltig"
    try:
        _atomar_schreiben(pfad, neu)
        r = python_probe([_WAECHTER], capture_output=True, text=True, cwd=str(_ROOT))
    finally:
        _atomar_schreiben(pfad, original)
        assert pfad.read_bytes() == original, f"{datei} nicht wiederhergestellt"
    if r.returncode == 3:
        print(f"{nr:>2}. [Absturz]   {name} — kein Nachweis")
        return "ungueltig"
    if not soll_rot:
        if r.returncode == 0:
            print(f"{nr:>2}. [ok, wirkungslos] {name}")
            return "gefangen"
        print(f"{nr:>2}. [ZU EMPFINDLICH] {name} (Exit {r.returncode})")
        return "unbemerkt"
    if r.returncode != 1:
        print(f"{nr:>2}. [UNBEMERKT] {name} (Exit {r.returncode})")
        return "unbemerkt"
    # Rot allein genuegt nicht: der Waechter muss die BENANNTE Pruefung reissen, und der
    # Lauf muss den Endmarker erreicht haben (ein Abbruch mitten im Lauf ist kein Beweis).
    if _umfang(r.stdout) < MIND_PRUEFUNGEN:
        print(f"{nr:>2}. [UNGUELTIG] {name} — Lauf unvollstaendig ({_umfang(r.stdout)})")
        return "ungueltig"
    rote = [z for z in (r.stdout or "").splitlines() if z.strip().startswith("FAIL")]
    marke = erwartung.split(" -> ")[0].strip()
    if not any(marke in z for z in rote):
        print(f"{nr:>2}. [FALSCHE PRUEFUNG] {name}\n"
              f"      erwartet gerissen: {erwartung}\n"
              f"      gerissen wurde:    {rote[:3]}")
        return "ungueltig"
    if "PRODUKTIONSAUSNAHME" in (r.stdout or ""):
        # Gefangen, aber durch einen Absturz im Produktivcode statt durch ein fachliches
        # Gegenbeispiel. Die Projektregel "eine eingefangene Ausnahme ist kein Nachweis"
        # wird dadurch nicht verletzt — der Waechter hat den Vertrag "None, kein Absturz"
        # geprueft und ist nicht selbst gestorben —, aber die Bilanz soll es zeigen.
        print(f"{nr:>2}. [gefangen*] {name}  ->  {marke}  (Produktionsausnahme)")
        return "ausnahme"
    print(f"{nr:>2}. [gefangen]  {name}  ->  {marke}")
    return "gefangen"


def main() -> int:
    gefangen, ausnahmen, unbemerkt, ungueltig = 0, [], [], []
    with _exklusiver_lauf():
        r0 = python_probe([_WAECHTER], capture_output=True, text=True, cwd=str(_ROOT))
        if r0.returncode != 0:
            print("[FAIL] Waechter ist schon ohne Mutation rot:\n" + (r0.stdout or "")[-2000:])
            return 1
        if _umfang(r0.stdout) < MIND_PRUEFUNGEN:
            print("[FAIL] Ausgangslauf unvollstaendig (%d)" % _umfang(r0.stdout))
            return 1
        print("Ausgangslauf: %d Pruefungen, Endmarker erreicht.\n" % _umfang(r0.stdout))

        for nr, (name, datei, paare, erwartung) in enumerate(MUTATIONEN, 1):
            erg = _lauf(nr, name, datei, paare, erwartung)
            if erg == "gefangen":
                gefangen += 1
            elif erg == "ausnahme":
                gefangen += 1
                ausnahmen.append(name)
            elif erg == "unbemerkt":
                unbemerkt.append(name)
            else:
                ungueltig.append(name)

        print()
        for nr, (name, datei, paare) in enumerate(UNGUELTIG_ERWARTET, len(MUTATIONEN) + 1):
            erg = _lauf(nr, name, datei, paare, "", soll_rot=False)
            if erg in ("gefangen", "ausnahme"):
                gefangen += 1
            elif erg == "unbemerkt":
                unbemerkt.append(name + " (haette wirkungslos sein muessen)")
            else:
                ungueltig.append(name)

    gesamt = len(MUTATIONEN) + len(UNGUELTIG_ERWARTET)
    print(f"\nErgebnis: {gefangen}/{gesamt} wie erwartet, "
          f"{len(unbemerkt)} unbemerkt, {len(ungueltig)} ungueltig")
    if ausnahmen:
        print(f"  davon {len(ausnahmen)} durch eine PRODUKTIONSAUSNAHME gefangen "
              f"(Vertrag 'None, kein Absturz' gerissen, kein fachliches Gegenbeispiel):")
        for n in ausnahmen:
            print("    * " + n)
    for n in unbemerkt:
        print("  UNBEMERKT: " + n)
    for n in ungueltig:
        print("  UNGUELTIG: " + n)
    return 1 if (unbemerkt or ungueltig) else 0


if __name__ == "__main__":
    sys.exit(main())
