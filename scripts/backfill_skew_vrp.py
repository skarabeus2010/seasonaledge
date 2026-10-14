#!/usr/bin/env python3
"""
backfill_skew_vrp.py — VRP in options_skew_history.json nachrechnen.

    python3 scripts/backfill_skew_vrp.py --dry-run          nur zeigen
    python3 scripts/backfill_skew_vrp.py --ticker SPY,QQQ   einzelne Ticker
    python3 scripts/backfill_skew_vrp.py                    alle, schreibend

    Reparatur einzelner Zeilen (R1c, Plan v4): erst Trockenlauf mit Bericht, dann Schreiben NUR gegen genau diesen
    Bericht:
    python3 scripts/backfill_skew_vrp.py --reparatur --ticker ETHA --von 2026-09-30 --bis 2026-10-13
    python3 scripts/backfill_skew_vrp.py --reparatur --ticker ETHA --von 2026-09-30 --bis 2026-10-13 \
            --schreiben --freigabe-datei logs/reparatur/vrp_ETHA_2026-09-30_2026-10-13_<zeit>.json

WARUM: das VRP (Variance Risk Premium = IV minus realisierte Vola) stand in der
Historie nur in 793 von 6271 Zeilen — der Live-Lauf schreibt es, der Backfill
(backfill_skew_massive.py) nicht. Der geplante IV/RealVol-Radar braucht ein
ticker-internes VRP-PERZENTIL; bei 87 % der Ticker gab es dafuer keine Reihe.

Es braucht dafuer keinen einzigen neuen API-Abruf: `iv_atm` steht in 3173
Zeilen, und die realisierte Vola ist aus unserer eigenen Kursreihe fuer jeden
vergangenen Handelstag rueckwaerts rechenbar.

WARUM ALLE ZEILEN NEU GERECHNET WERDEN, auch die 793 vorhandenen:
Eine Reihe, in der 12 % der Punkte aus der damaligen Kursreihe und 88 % aus
einer Nachrechnung stammen, ist genau die Methodenmischung, die in diesem
Projekt schon einmal das Perzentil zerstoert hat — am 2026-09-09 lag der
Live-Punkt im 99. Perzentil, weil die Historie BS-rekonstruiert war und der
Tagespunkt aus der Provider-IV kam (docs/OPTIONS.md, v54.0). Der Versatz war
damals so gross wie der gesamte Interquartilsabstand. Ein Perzentil ist nur
so gut wie die Gleichartigkeit der Reihe, aus der es kommt.

Gegengerechnet wird das: `--dry-run` zeigt, wie weit die vorhandenen Werte von
der Neurechnung abweichen. Gemessen ueber sieben Ticker: Median 0,55 pp,
95. Perzentil 2,71 pp, max 3,43 pp — MEHR als die Adjustierung erklaeren kann.
Nachgeprueft an GOOGL/2026-09-15 ergeben Supabase UND Yahoo rv21 = 0,225,
waehrend der gespeicherte Wert 0,191 impliziert; er passt zu keiner der beiden
Quellen, und der Daten-/Codestand seiner Entstehung ist nicht rekonstruierbar.
Das ist das eigentliche Argument fuer die Neurechnung: nicht dass die alten
Werte anders sind, sondern dass sie nicht nachvollziehbar sind.

QUELLE: Supabase ueber shared.data.lade_kurse (gespeicherter log_return) — kein Yahoo. Begruendung dort;
kurz: Yahoos Adjustierung wandert mit jeder Dividende, dieselbe Abfrage ergibt
an verschiedenen Tagen verschiedene Reihen. Der Live-Lauf nutzt seit
2026-09-19 dieselbe Quelle, damit Historie und Tagespunkt vergleichbar sind.

FORMEL: identisch zum Live-Lauf, weil BEIDE shared/realized_vol.py benutzen —
vrp_pts = (iv_atm − rv21) · 100, rv21 = annualisierte realisierte Vola der
21 Handelstage bis einschliesslich des jeweiligen Tages.

BETRIEB: geschrieben wird unter der gemeinsamen Sperre aller History-Schreiber
(shared.atomic_json.history_aktualisieren): die Kursreihen werden ohne Sperre
geladen, die VRP-Felder dann auf dem FRISCH gelesenen Stand gesetzt. Frueher
las das Skript die Datei einmal und schrieb die alte Gesamtstruktur zurueck —
was der Cron dazwischen anlegte, war weg (Lost Update, docs/OPTIONS.md).
"""
from __future__ import annotations

import argparse
import gc
import json
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

import datetime as _dt                                               # noqa: E402
import hashlib                                                       # noqa: E402
import math                                                          # noqa: E402
from shared.atomic_json import (write_json_atomic, history_aktualisieren,  # noqa: E402
                                history_lesen, HistorieDefekt, SperreBelegt)
from shared.data import KursreiheFehlt, lade_kurse                   # noqa: E402
from shared.realized_vol import RV_FENSTER, rv_reihe_aus_returns     # noqa: E402

HISTORIE = _ROOT / "landing/data/options_skew_history.json"

# Schluessel, die keine Ticker sind (vorwaerts akkumulierte Reihen).
KEINE_TICKER = {"__CORR", "__PCR"}

# So viele nachgerechnete Zeilen muessen mindestens vorliegen, bevor das
# Invariant-Urteil ueberhaupt etwas wert ist.
MIN_ZEILEN = 200


def _vrp_loeschen(z: dict) -> bool:
    """Entfernt alle drei VRP-Felder einer Zeile. True, wenn etwas dranstand.

    Immer alle drei zusammen: `vrp_quelle` ist die Behauptung, dieser Wert sei
    nachgerechnet worden. Sie ohne Wert stehenzulassen waere eine Luege ueber
    die Herkunft.
    """
    dran = any(z.get(k) is not None for k in ("vrp_pts", "vrp_rv", "vrp_quelle"))
    for k in ("vrp_pts", "vrp_rv", "vrp_quelle"):
        if k in z:
            z[k] = None
    return dran


def _kursfenster(daten: list[str]) -> str:
    """Fruehestes Ladedatum: das aelteste Historien-Datum minus Puffer.

    Der erste Punkt braucht 21 Handelstage VOR sich, sonst bekommt er kein
    VRP. Ein Jahr Vorlauf deckt das mit Reserve fuer Feiertage ab.
    """
    aeltestes = min(daten)
    return "%04d-%s" % (int(aeltestes[:4]) - 1, aeltestes[5:])


def _neue_stat() -> dict:
    return {"ticker": 0, "uebersprungen": 0, "zeilen_mit_iv": 0, "gesetzt": 0,
            "kein_rv": 0, "vorher_vorhanden": 0, "abweichungen": [],
            "ohne_reihe": [], "invariant_alt": [], "invariant_neu_gleich": [],
            "invariant_neu_dazu": [], "geleert_ohne_iv": 0}


def rv_laden(hist: dict, nur: set[str] | None, stat: dict) -> dict:
    """Phase 1 (langsam, ohne Sperre): RV je Ticker und Tag aus Supabase. `hist` nur zur Planung."""
    rv_je = {}
    for t in sorted(hist):
        if t in KEINE_TICKER:
            continue
        if nur and t not in nur:
            continue
        zeilen = hist.get(t) or []
        mit_iv = [z for z in zeilen if isinstance(z, dict) and z.get("iv_atm")]
        daten = [z["date"] for z in mit_iv if z.get("date")]
        if not daten:
            stat["uebersprungen"] += 1
            continue
        try:
            kd, _kc, kr = lade_kurse(t, ab=_kursfenster(daten),
                                     mindestens=RV_FENSTER + 5)
        except KursreiheFehlt as e:
            # Kein VRP ist besser als ein aus fremder Quelle gerechnetes.
            stat["ohne_reihe"].append(f"{t}: {e}")
            stat["uebersprungen"] += 1
            continue
        # Aus gespeicherten Returns, nicht aus Schlusskursen (shared/basisabweichung.py) — dieselbe Regel wie live.
        rv_je[t] = rv_reihe_aus_returns(kd, kr)
        stat["ticker"] += 1
        gc.collect()
    return rv_je


def anwenden(hist: dict, rv_je: dict, stat: dict) -> None:
    """Phase 2 (schnell, unter der Sperre auf dem frischen Stand): VRP-Felder setzen. Ticker ohne geladene RV
    bleiben unberuehrt."""
    for t in sorted(rv_je):
        rv_je_tag = rv_je[t]
        for z in hist.get(t) or []:
            if not isinstance(z, dict):
                continue
            if not z.get("iv_atm"):
                # KEIN ATM-Anker -> kein VRP moeglich. Ein alter Wert aus
                # fremder Quelle darf hier nicht stehenbleiben: er waere der
                # einzige nicht nachgerechnete Punkt in einer sonst
                # einheitlichen Reihe und ginge ungeprueft ins Perzentil.
                if _vrp_loeschen(z):
                    stat["geleert_ohne_iv"] += 1
                continue
            if not z.get("date"):
                continue
            stat["zeilen_mit_iv"] += 1
            rv = rv_je_tag.get(z["date"])
            if rv is None:
                # Handelstag ohne volles, lueckenfreies 21-Tage-Fenster. Die
                # Felder werden BEWUSST geleert, falls vorher etwas stand: ein
                # nicht nachvollziehbarer Wert in einer sonst einheitlichen
                # Reihe ist schlimmer als eine Luecke. ALLE drei Felder — eine
                # Zeile mit vrp_pts=None, aber vrp_quelle="supabase21" wuerde
                # behaupten, sie sei nachgerechnet worden.
                if z.get("vrp_pts") is not None:
                    stat["vorher_vorhanden"] += 1
                _vrp_loeschen(z)
                stat["kein_rv"] += 1
                continue
            neu = round((float(z["iv_atm"]) - rv) * 100, 2)
            alt = z.get("vrp_pts")
            if alt is not None:
                stat["vorher_vorhanden"] += 1
                stat["invariant_alt"].append(float(alt))
                stat["invariant_neu_gleich"].append(neu)
                stat["abweichungen"].append((t, z["date"], float(alt), neu))
            else:
                stat["invariant_neu_dazu"].append((neu, bool(z.get("reconstructed"))))
            z["vrp_pts"] = neu
            z["vrp_rv"] = rv            # Nachvollziehbarkeit: welche RV war es?
            z["vrp_quelle"] = "supabase21"
            stat["gesetzt"] += 1


def nachrechnen(hist: dict, nur: set[str] | None = None) -> dict:
    """Beide Phasen auf demselben Objekt (Trockenlauf, Tests). Veraendert `hist` an Ort und Stelle."""
    stat = _neue_stat()
    anwenden(hist, rv_laden(hist, nur, stat), stat)
    return stat


# ── Reparaturmodus (R1c): einzelne Zeilen eines Tickers, nur vrp_pts, gegen eine freigegebene Berichtsdatei ──────

REPARATUR_DIR = _ROOT / "logs" / "reparatur"
_RV_GRENZEN = (0.0, 3.0)          # realisierte Vola als Anteil; ausserhalb davon ist die Reihe kaputt, nicht der Markt


def _kanonisch(obj) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def reparatur_diff(hist: dict, ticker: str, von: str, bis: str, rv_je_tag: dict) -> dict:
    """Diff fuer die Zeilen von `ticker` mit von <= date <= bis. Geaendert wird nur `vrp_pts`, und nur bei
    cm/cm_extrap mit endlichem iv_atm und vorhandener RV; alles andere wird mit Grund gemeldet."""
    ziel = [z for z in hist.get(ticker) or [] if isinstance(z, dict) and von <= str(z.get("date", "")) <= bis]
    zeilen = []
    for z in ziel:
        e = {"date": z.get("date"), "cm_mode": z.get("cm_mode"), "iv_atm": z.get("iv_atm"),
             "vrp_alt": z.get("vrp_pts")}
        iv = z.get("iv_atm")
        if z.get("cm_mode") not in ("cm", "cm_extrap"):
            e["grund"] = "nicht normiert — unveraendert"
        elif not isinstance(iv, (int, float)) or isinstance(iv, bool) or not math.isfinite(iv):
            e["grund"] = "kein iv_atm — unveraendert"
        else:
            rv = rv_je_tag.get(z.get("date"))
            if rv is None:
                e["grund"] = "keine RV — unveraendert"
            else:
                e["rv_neu"] = rv
                e["vrp_neu"] = round((float(iv) - rv) * 100, 2)
        zeilen.append(e)
    return {"ticker": ticker, "von": von, "bis": bis,
            "zielhash": hashlib.sha256(_kanonisch(ziel).encode("utf-8")).hexdigest(),
            "zeilen": zeilen}


def reparatur_pruefen(diff: dict) -> list[str]:
    """Invarianten des Diffs selbst: eindeutige Daten, jede zu aendernde Zeile hat eine RV in (0, 3)."""
    fehler = []
    daten = [e["date"] for e in diff["zeilen"]]
    doppelt = sorted({d for d in daten if daten.count(d) > 1})
    if doppelt:
        # Zeilen werden ueber ihre Position identifiziert; zwei Zeilen desselben Datums waeren fuer den Leser des
        # Berichts nicht unterscheidbar — und die History dedupliziert je Datum, also ist es ohnehin ein Defekt.
        fehler.append("doppelte Daten im Bereich: " + ", ".join(doppelt))
    for e in diff["zeilen"]:
        if "vrp_neu" in e and not (_RV_GRENZEN[0] < e["rv_neu"] < _RV_GRENZEN[1]):
            fehler.append(f"{e['date']}: RV {e['rv_neu']} ausserhalb {_RV_GRENZEN}")
    if not any("vrp_neu" in e for e in diff["zeilen"]):
        fehler.append("keine Zeile zu aendern")
    return fehler


def _ziel_positionen(arr: list, von: str, bis: str) -> list[int]:
    return [i for i, z in enumerate(arr) if isinstance(z, dict) and von <= str(z.get("date", "")) <= bis]


def reparatur_anwenden(hist: dict, diff: dict) -> None:
    """Setzt NUR vrp_pts der Zielzeilen (identifiziert ueber ihre Position, nicht ueber das Datum) und prueft danach,
    dass sich sonst nichts geaendert hat — einschliesslich der Frage, ob ein Feld vorher ueberhaupt existierte."""
    fehler = reparatur_pruefen(diff)
    if fehler:
        raise RuntimeError("Diff nicht zulaessig: " + "; ".join(fehler))
    vorher = json.loads(_kanonisch(hist))
    arr = hist.get(diff["ticker"]) or []
    pos = _ziel_positionen(arr, diff["von"], diff["bis"])
    if [arr[i].get("date") for i in pos] != [e["date"] for e in diff["zeilen"]]:
        raise RuntimeError("Zielzeilen passen nicht zum Diff")
    geaendert = []
    for i, e in zip(pos, diff["zeilen"]):
        if "vrp_neu" in e:
            arr[i]["vrp_pts"] = e["vrp_neu"]
            geaendert.append(i)
    # Invariante: Ergebnis mit zurueckgesetzten Zielwerten == frisch gesperrter Ausgangsstand
    pruef = json.loads(_kanonisch(hist))
    alt_arr = vorher.get(diff["ticker"]) or []
    for i in geaendert:
        if "vrp_pts" in alt_arr[i]:
            pruef[diff["ticker"]][i]["vrp_pts"] = alt_arr[i]["vrp_pts"]
        else:
            pruef[diff["ticker"]][i].pop("vrp_pts", None)
    if _kanonisch(pruef) != _kanonisch(vorher):
        raise RuntimeError("Invariante verletzt: ausser vrp_pts der Zielzeilen hat sich etwas geaendert")


def reparatur(args) -> int:
    if not args.ticker or "," in args.ticker or not args.von or not args.bis:
        print("FEHLER: --reparatur braucht genau einen --ticker sowie --von und --bis")
        return 1
    t = args.ticker.strip().upper()
    plan = history_lesen(HISTORIE)
    stat = _neue_stat()
    rv_je = rv_laden({t: plan.get(t) or []}, {t}, stat)
    if t not in rv_je:
        print("FEHLER: keine Kursreihe fuer %s: %s" % (t, stat["ohne_reihe"]))
        return 1
    diff = reparatur_diff(plan, t, args.von, args.bis, rv_je[t])
    for e in diff["zeilen"]:
        print("  %s %-9s iv_atm %-8s vrp %8s -> %8s  rv %s  %s"
              % (e["date"], e.get("cm_mode"), e.get("iv_atm"), e.get("vrp_alt"), e.get("vrp_neu", "—"),
                 ("%.4f" % e["rv_neu"]) if "rv_neu" in e else "—", e.get("grund", "")))
    fehler = reparatur_pruefen(diff)
    if fehler:
        print("NICHT ZULAESSIG: " + "; ".join(fehler))
        return 2

    if not args.schreiben:
        # Bericht ist KEIN Produktionsdatum — er wird immer gespeichert, die History nicht angefasst.
        zeit = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        ziel = REPARATUR_DIR / ("vrp_%s_%s_%s_%s.json" % (t, args.von, args.bis, zeit))
        write_json_atomic(ziel, dict(diff, erstellt=zeit))
        print()
        print("Trockenlauf: History unveraendert. Bericht: %s" % ziel)
        print("Schreiben nur mit: --schreiben --freigabe-datei %s" % ziel)
        return 0

    if not args.freigabe_datei:
        print("FEHLER: --schreiben braucht --freigabe-datei <Bericht aus dem Trockenlauf>")
        return 1
    try:
        freigabe = json.loads(pathlib.Path(args.freigabe_datei).read_text(encoding="utf-8"))
    except Exception as e:
        print("FEHLER: Freigabedatei nicht lesbar: %s" % e)
        return 1
    if (freigabe.get("ticker"), freigabe.get("von"), freigabe.get("bis")) != (t, args.von, args.bis):
        print("ABBRUCH: Ticker/Bereich passen nicht zur Freigabedatei")
        return 2

    def _aendern(h):
        frisch = reparatur_diff(h, t, args.von, args.bis, rv_je[t])
        vergleich = {k: freigabe.get(k) for k in ("ticker", "von", "bis", "zielhash", "zeilen")}
        if _kanonisch(frisch) != _kanonisch(vergleich):
            raise RuntimeError("Diff auf dem aktuellen Stand weicht von der Freigabedatei ab — nichts geschrieben")
        reparatur_anwenden(h, frisch)

    try:
        history_aktualisieren(HISTORIE, _aendern)
    except (RuntimeError, HistorieDefekt, SperreBelegt) as e:
        print("ABBRUCH: %s" % e)
        return 2
    print("geschrieben: %d Zeilen von %s (vrp_pts)" % (sum(1 for x in diff["zeilen"] if "vrp_neu" in x), t))
    return 0


def bericht(stat: dict) -> bool:
    print()
    print("=" * 70)
    print("Ticker gerechnet        : %d" % stat["ticker"])
    print("Ticker uebersprungen    : %d" % stat["uebersprungen"])
    print("Zeilen mit iv_atm       : %d" % stat["zeilen_mit_iv"])
    print("VRP gesetzt             : %d" % stat["gesetzt"])
    print("ohne volles RV-Fenster  : %d" % stat["kein_rv"])
    print("ohne iv_atm geleert     : %d" % stat["geleert_ohne_iv"])
    print("vorher schon vorhanden  : %d" % stat["vorher_vorhanden"])

    ab = stat["abweichungen"]
    if ab:
        d = sorted(abs(n - a) for _, _, a, n in ab)
        print()
        print("Abweichung Neurechnung gegen die bestehenden %d Werte (pp):" % len(ab))
        print("  Median %.2f | 95. Perzentil %.2f | max %.2f"
              % (d[len(d) // 2], d[int(len(d) * 0.95)], d[-1]))
        print("  Die groessten fuenf:")
        for t, dt, a, n in sorted(ab, key=lambda x: -abs(x[3] - x[2]))[:5]:
            print("    %-7s %s  %7.2f -> %7.2f  (%+.2f pp)" % (t, dt, a, n, n - a))
        print()
        print("  Eine Abweichung ungleich null ist erwartet — aber sie ist")
        print("  GROESSER als durch Adjustierung erklaerbar, und das ist der")
        print("  Grund fuer die Neurechnung: die alten Werte lassen sich nicht")
        print("  reproduzieren, auch nicht mit der Yahoo-Reihe. Nachgemessen an")
        print("  GOOGL/2026-09-15: Supabase und Yahoo ergeben beide rv21 0,225,")
        print("  der gespeicherte Wert impliziert 0,191 — er passt zu keiner der")
        print("  beiden Quellen. Aus welchem Daten- und Codestand er stammt, ist")
        print("  nicht mehr rekonstruierbar. Eine Reihe aus nicht")
        print("  nachvollziehbaren Werten taugt nicht fuer ein Perzentil.")

    invariant_ok = _invariant(stat)

    if stat["ohne_reihe"]:
        print()
        print("Ohne Kursreihe in Supabase (%d):" % len(stat["ohne_reihe"]))
        for z in stat["ohne_reihe"][:10]:
            print("  " + z)
    return invariant_ok


def _verteilung(werte):
    w = sorted(werte)
    n = len(w)
    if not n:
        return None
    return (n, w[n // 2], sum(w) / n, sum(1 for v in w if v > 0) / n * 100)


def _invariant(stat: dict) -> bool:
    """Prueft den Domaenen-Invariant: das VRP ist im Mittel POSITIV.

    Optionskaeufer zahlen eine Praemie fuer Absicherung, die implizite Vola
    liegt deshalb im Schnitt ueber der realisierten. Eine Reihe, deren VRP im
    Mittel negativ ist, taugt nicht fuer ein Perzentil — dann stimmt etwas mit
    der IV oder der Vola nicht.

    Verglichen wird auf der GLEICHEN Teilmenge. Ein Vergleich der 772 alten
    Live-Zeilen gegen 3152 Zeilen inklusive Backfill waere wertlos, weil die
    Grundmengen verschieden sind — beim ersten Lauf sah die Neurechnung dadurch
    schlechter aus, obwohl sie auf den vergleichbaren Zeilen besser ist.
    """
    ok = True
    a = _verteilung(stat["invariant_alt"])
    b = _verteilung(stat["invariant_neu_gleich"])
    if a and b:
        print()
        print("Domaenen-Invariant (VRP im Mittel positiv), SELBE Zeilen:")
        print("  alt  n=%4d  Median %+6.2f  Mittel %+6.2f  positiv %5.1f %%" % a)
        print("  neu  n=%4d  Median %+6.2f  Mittel %+6.2f  positiv %5.1f %%" % b)
        # HART ist nur das positive Mittel. "Besser als die alten Werte" war
        # frueher ebenfalls hart und ist als Schranke NICHT haltbar: die alten
        # Werte sind genau die, die sich nicht reproduzieren lassen (siehe
        # Modul-Docstring) — sie als Messlatte zu nehmen ist zirkulaer. Dazu
        # kommt die Stichprobengroesse: am 2026-09-21 lagen 19 gemeinsame
        # Zeilen vor, und 0,14 pp Unterschied im Mittel sind dort Rauschen.
        # Die Richtung wird weiter ANGEZEIGT, aber sie blockiert nicht mehr.
        if b[2] <= 0:
            print("  -> ROT: das Mittel ist nicht positiv. Der Invariant ist")
            print("     verletzt, die Reihe taugt nicht fuer ein Perzentil.")
            ok = False
        else:
            print("  -> gruen: das Mittel ist positiv.")
        if b[2] >= a[2] and b[3] >= a[3]:
            print("     (zur Einordnung: auch besser als die alten Werte in")
            print("      Mittelwert und Anteil positiver Werte)")
        else:
            print("     (zur Einordnung: auf den %d gemeinsamen Zeilen NICHT" % a[0])
            print("      besser als die alten Werte — kein Ausschlussgrund,")
            print("      aber ein Blick wert, wenn die Stichprobe gross ist)")

    # MINDESTSTICHPROBE, hart. Ohne sie koennte eine Handvoll zufaellig
    # positiver Zeilen das Gate passieren — das Mittel einer Stichprobe von
    # drei sagt nichts. Der Wert ist bewusst grosszuegig: es geht darum,
    # Zufallstreffer auszuschliessen, nicht um statistische Signifikanz.
    ges = len(stat["invariant_neu_gleich"]) + len(stat["invariant_neu_dazu"])
    if ges < MIN_ZEILEN:
        print()
        print("  -> ROT: nur %d nachgerechnete Zeilen (mindestens %d noetig)."
              % (ges, MIN_ZEILEN))
        print("     Eine so kleine Stichprobe traegt keine Aussage.")
        ok = False

    dazu = stat["invariant_neu_dazu"]
    if dazu:
        d = _verteilung([v for v, _ in dazu])
        anteil_recon = sum(1 for _, r in dazu if r) / len(dazu) * 100
        print()
        print("Neu hinzugekommene Zeilen:")
        print("  n=%4d  Median %+6.2f  Mittel %+6.2f  positiv %5.1f %%" % d)
        print("  davon aus dem Backfill (reconstructed): %.0f %%" % anteil_recon)
        if d[2] < 0:
            print()
            print("  !! DAS VRP DIESER ZEILEN IST IM MITTEL NEGATIV.")
            print("  Das ist KEIN Fehler dieser Nachrechnung — die realisierte Vola")
            print("  kommt aus unserer gepflegten Kursreihe. Es liegt am gespeicherten")
            print("  iv_atm: die Backfill-Zeilen stammen aus der Zeit VOR der")
            print("  Skew-Reparatur vom 2026-09-11 (Volumenfilter als falsches")
            print("  Kriterium, selbstreferenzielles Delta, angepasste Optionsserien —")
            print("  siehe CLAUDE.md v61.0). Ein VRP-Perzentil ueber diese Reihe waere")
            print("  unbrauchbar, egal wie gut die Vola-Seite gerechnet ist.")
            print("  -> Erst den Reparatur-Backfill mit der korrigierten Methodik")
            print("     fahren, dann diese Nachrechnung.")
            ok = False
    return ok


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true",
                    help="nur rechnen und berichten, nichts schreiben")
    ap.add_argument("--ticker", help="Komma-Liste statt aller Ticker")
    ap.add_argument("--trotzdem", action="store_true",
                    help="schreiben, obwohl der Invariant rot ist (bewusste "
                         "Entscheidung, wird im Bericht vermerkt)")
    ap.add_argument("--reparatur", action="store_true", help="nur vrp_pts eines Tickers im Datumsbereich (R1c)")
    ap.add_argument("--von", help="Reparatur: erstes Datum (einschliesslich)")
    ap.add_argument("--bis", help="Reparatur: letztes Datum (einschliesslich)")
    ap.add_argument("--schreiben", action="store_true", help="Reparatur: schreiben (sonst Trockenlauf mit Bericht)")
    ap.add_argument("--freigabe-datei", help="Reparatur: Bericht des Trockenlaufs, gegen den geschrieben wird")
    args = ap.parse_args()

    if args.reparatur:
        return reparatur(args)

    try:
        plan = history_lesen(HISTORIE)
    except HistorieDefekt as e:
        print("FEHLER: %s" % e)
        return 1
    print("Historie: %d Ticker, %d Punkte"
          % (len(plan), sum(len(v) for v in plan.values() if isinstance(v, list))))

    nur = None
    if args.ticker:
        nur = {x.strip().upper() for x in args.ticker.split(",") if x.strip()}
        print("nur: %s" % ", ".join(sorted(nur)))

    basis = _neue_stat()
    rv_je = rv_laden(plan, nur, basis)

    if args.dry_run:
        stat = dict(basis)
        anwenden(plan, rv_je, stat)
        bericht(stat)
        print()
        print("--dry-run: nichts geschrieben.")
        return 0

    ergebnis = {}

    def _aendern(h):
        # Auf dem FRISCHEN Stand anwenden; Gate und Bericht beziehen sich auf genau diese Zeilen.
        stat = {k: (list(v) if isinstance(v, list) else v) for k, v in basis.items()}
        anwenden(h, rv_je, stat)
        ok = bericht(stat)
        ergebnis["stat"], ergebnis["ok"] = stat, ok
        if not stat["gesetzt"]:
            return False
        # GATE: ein roter Invariant blockiert das Schreiben. Eine Pruefung, die
        # warnt und dann doch schreibt, ist keine Pruefung — sie verschiebt die
        # Entscheidung nur auf jemanden, der die Ausgabe vielleicht nicht liest.
        if not ok and not args.trotzdem:
            return False
        return True

    try:
        geschrieben = history_aktualisieren(HISTORIE, _aendern)
    except (HistorieDefekt, SperreBelegt) as e:
        print("ABBRUCH: %s" % e)
        return 1
    if geschrieben is None:
        print()
        if not ergebnis.get("stat", {}).get("gesetzt"):
            print("Kein Wert gesetzt -> nicht geschrieben (eine Datei ohne Grund zu")
            print("ersetzen ist ein unnoetiges Risiko).")
            return 1
        print("NICHT GESCHRIEBEN: der Invariant ist rot (siehe oben).")
        print("Wenn das bewusst in Kauf genommen wird: --trotzdem.")
        return 2
    print()
    print("geschrieben: %s" % HISTORIE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
