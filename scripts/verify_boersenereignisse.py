#!/usr/bin/env python3
"""
Wächter: Ereigniskatalog der Börsenschließungen (shared/boersenereignisse.py, Vertrag B4, V1c-1;
Entwurf docs/review_prompts/2026-10-11_kalender_v1c_entwurf*.md, Codex-Freigabe v4).

  [Bestand]     eingefrorene Momentaufnahme vor dem Umbau (scripts/kalender_momentaufnahme.py --pruefen):
                get_holidays, is_trading_day und alle Nummern je Börse/Jahr 1885–2100 unverändert.
  [Kompat]      get_holidays == kompat() je Börse/Jahr; die _compute_*-Hüllen liefern dieselbe Menge.
  [Invariante]  Felder, Arten, Ersatzgründe, Kennungen eindeutig, Jahreszuordnung, Quellen vorhanden,
                Tabellenereignisse ohne Namen, schliessungen ⊆ kompat und nur Werktage.
  [Sollfall]    handgeschriebene Fälle mit Quelle (gov.uk, NYSE, JPX/NAOJ, Xetra, Nasdaq Stockholm, KRX) — nicht
                aus dem Code abgeleitet.
  [Version]     (a) Nominaldatum, (b) Name/Quelle → nur ereignisversion; (c) wirksamer Werktag → beide;
                (d) wirksames Wochenenddatum → nur ereignisversion.
  [Zwilling]    landing/js/boersenkalender.js: vollständige Objektgleichheit aller Ereignisse, Schließungen,
                Identität und Versionen je Börse/Jahr 1885–2100, unter zwei Zeitzonen; Alias NASDAQ; eingefroren.
  [Abnahmelücke] alle Börse/Jahre mit Tabellenidentität werden AUSGEGEBEN (nicht stillschweigend grün).

Aufruf:  py -3.14 scripts/verify_boersenereignisse.py      Exit 0 = alles erfüllt (braucht node)
"""
from __future__ import annotations

import contextlib
import dataclasses
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from datetime import date

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, WURZEL)

from shared import boersenereignisse as BE  # noqa: E402
from shared import exchange_holidays as EH  # noqa: E402
from shared import nyse_holidays as NH  # noqa: E402
from shared.kalender_quellen import QUELLEN  # noqa: E402

VON, BIS = EH.NUMMERN_VON_JAHR, EH.NUMMERN_BIS_JAHR
PROBE = os.path.join(WURZEL, "scripts", "js", "probe_boersenereignisse.js")
ZONEN = {"UTC": [0, 0], "America/Adak": [600, 540]}

FEHLER: list[str] = []
ZAEHLER = {"n": 0}


def pruefe(kennung: str, bedingung: bool, text: str = "") -> None:
    ZAEHLER["n"] += 1
    if not bedingung:
        FEHLER.append(f"[{kennung}] {text}")


def D(s: str) -> date:
    return date.fromisoformat(s)


def ereignis(b: str, eid: str):
    jahr = int(eid.rsplit(":", 1)[1][:4])
    treffer = [e for e in BE.ereignisse(b, jahr) if e.ereignis_id == eid]
    return treffer[0] if len(treffer) == 1 else None


# ── Bestand ──────────────────────────────────────────────────────────────────────────────────────────────────
def bestand() -> None:
    r = subprocess.run([sys.executable, os.path.join(WURZEL, "scripts", "kalender_momentaufnahme.py"), "--pruefen"],
                       capture_output=True, text=True, encoding="utf-8", env=dict(os.environ, PYTHONUTF8="1"))
    pruefe("Bestand", r.returncode == 0 and "PROBE-ENDE 3024" in r.stdout,
           "Momentaufnahme weicht ab: " + (r.stdout + r.stderr)[-600:])


def kompat() -> None:
    hueller = {"XETRA": EH._compute_xetra_holidays, "LSE": EH._compute_lse_holidays,
               "EURONEXT": EH._compute_euronext_holidays, "MILAN": EH._compute_milan_holidays,
               "TSE": EH._compute_tse_holidays, "SIX": EH._compute_six_holidays,
               "STOCKHOLM": EH._compute_stockholm_holidays, "OSLO": EH._compute_oslo_holidays,
               "HKEX": EH._compute_hkex_holidays, "KRX": EH._compute_krx_holidays, "NYSE": NH._compute_nyse_holidays}
    abw = []
    for b in sorted(EH._EXCHANGE_FUNCTIONS):
        for j in range(VON, BIS + 1):
            gh = EH.get_holidays(b, j, j)
            if gh != set(BE.kompat(b, j)):
                abw.append(f"{b} {j} get_holidays≠kompat")
            if b in hueller and sorted(gh) != hueller[b](j):
                abw.append(f"{b} {j} Hülle")
    pruefe("Kompat", not abw, "; ".join(abw[:10]))


# ── Invarianten ──────────────────────────────────────────────────────────────────────────────────────────────
def invarianten() -> None:
    ids, fehl = {}, []
    for b in BE.BOERSEN:
        for j in range(VON, BIS + 1):
            ev = BE.ereignisse(b, j)
            km = BE.kompat(b, j)
            for e in ev:
                if e.ereignis_id in ids:
                    fehl.append(f"Kennung doppelt {e.ereignis_id}")
                ids[e.ereignis_id] = e
                if e.boerse != b or e.nominal.year != j:
                    fehl.append(f"{e.ereignis_id}: Börse/Jahr")
                if e.art not in BE.ARTEN or e.ersatzgrund not in BE.ERSATZGRUENDE:
                    fehl.append(f"{e.ereignis_id}: Art/Ersatzgrund unbekannt")
                if e.quelle not in QUELLEN:
                    fehl.append(f"{e.ereignis_id}: Quelle fehlt")
                if e.nominal_herkunft == "tabelle":
                    if not (e.art == "unbestimmt" and e.name_de is None and e.name_en is None
                            and e.regel_id == b + ".tabelle" and e.nominal == e.wirksam == e.rechtlich):
                        fehl.append(f"{e.ereignis_id}: Tabellenvertrag")
                    continue
                if e.nominal_herkunft != "regel" or not e.name_de or not e.name_en:
                    fehl.append(f"{e.ereignis_id}: Herkunft/Name")
                if e.verlegt != (e.rechtlich != e.nominal):
                    fehl.append(f"{e.ereignis_id}: verlegt ≠ (rechtlich ≠ nominal)")
                if e.art == "sonderschliessung":
                    if not (e.nominal == e.rechtlich == e.wirksam and e.ersatzgrund == "keiner"):
                        fehl.append(f"{e.ereignis_id}: Sonderschließung verschoben")
                    continue
                if (e.art == "ersatztag") != (e.wirksam != e.nominal):
                    fehl.append(f"{e.ereignis_id}: art ersatztag ⇔ wirksam ≠ nominal verletzt")
                if e.wirksam != e.rechtlich and e.ersatzgrund not in ("wochenende", "furikae"):
                    fehl.append(f"{e.ereignis_id}: Ersatz ohne Grund")
                if e.wirksam == e.rechtlich and e.ersatzgrund in ("wochenende", "furikae"):
                    fehl.append(f"{e.ereignis_id}: Grund ohne Ersatz")
                if e.verlegt and e.ersatzgrund not in ("verlegung", "furikae"):
                    fehl.append(f"{e.ereignis_id}: Verlegung ohne Grund")
                if not e.verlegt and e.ersatzgrund == "verlegung":
                    fehl.append(f"{e.ereignis_id}: Grund verlegung ohne Verlegung")
                if e.ersatzgrund == "furikae" and b != "TSE" or e.ersatzgrund == "wochenende" and b not in ("NYSE", "LSE"):
                    fehl.append(f"{e.ereignis_id}: Ersatzgrund an falscher Börse")
            s = BE.schliessungen(b, j)
            if s != sorted(set(s)) or any(d.weekday() >= 5 or d not in km for d in s):
                fehl.append(f"{b} {j}: schliessungen nicht eindeutig/Werktag/⊆ kompat")
            if set(d for d in km if d.weekday() < 5) != set(s):
                fehl.append(f"{b} {j}: Werktage der Kompatibilitätsmenge ≠ schliessungen")
    pruefe("Invariante", not fehl, "; ".join(fehl[:12]) + (f" … ({len(fehl)})" if len(fehl) > 12 else ""))
    pruefe("Invariante", BE.ereignisse("NASDAQ", 2025) == BE.ereignisse("NYSE", 2025), "Alias NASDAQ")
    # Versionsfelder (B4.1): jedes Objekt trägt die kalenderversion des Katalogs; der Ereignishash schließt sie aus
    kv, h, ohne = BE.kalenderversion(), hashlib.sha256(), True
    for b in BE.BOERSEN:
        for j in range(VON, BIS + 1):
            for e in BE.ereignisse(b, j):
                d = e.als_dict()
                ohne = ohne and d.get("kalenderversion") == kv and "kalenderversion" not in e.inhalt()
                h.update(json.dumps(e.inhalt(), sort_keys=True, ensure_ascii=False).encode("utf-8"))
    pruefe("Invariante", ohne, "kalenderversion fehlt am Objekt, ist falsch oder steckt im Inhalt")
    pruefe("Invariante", BE.ereignisversion() == h.hexdigest(), "ereignisversion ≠ Hash über den Inhalt ohne Versionsfelder")
    try:
        BE.ereignisse("FOO", 2025)
        pruefe("Invariante", False, "unbekannte Börse ohne Fehler")
    except ValueError:
        pruefe("Invariante", True)


# ── Sollfälle (handgeschrieben, Quelle je Fall) ──────────────────────────────────────────────────────────────
# (Börse, Kennung, Feld → Soll) — Quelle in der Kommentarzeile
SOLL = [
    # gov.uk: Early May 2020 auf Fr 8.5. verlegt (VE Day 75)
    ("LSE", "LSE:LSE.early_may:2020-05-04", dict(art="ersatztag", rechtlich="2020-05-08", wirksam="2020-05-08",
                                                 ersatzgrund="verlegung", verlegt=True)),
    # gov.uk 2021: Christmas Sa → Mo 27.12., Boxing Day So → Di 28.12.
    ("LSE", "LSE:LSE.christmas:2021-12-25", dict(art="ersatztag", wirksam="2021-12-27", ersatzgrund="wochenende")),
    ("LSE", "LSE:LSE.boxing_day:2021-12-26", dict(art="ersatztag", wirksam="2021-12-28", ersatzgrund="wochenende")),
    # gov.uk 2022: Boxing Day Mo 26.12. (Feiertag), Christmas (So) → Di 27.12.
    ("LSE", "LSE:LSE.boxing_day:2022-12-26", dict(art="feiertag", wirksam="2022-12-26", ersatzgrund="keiner")),
    ("LSE", "LSE:LSE.christmas:2022-12-25", dict(art="ersatztag", wirksam="2022-12-27", ersatzgrund="wochenende")),
    # gov.uk 2022: Spring Bank auf Do 2.6. verlegt, Fr 3.6. Platinum Jubilee
    ("LSE", "LSE:LSE.spring_bank:2022-05-30", dict(art="ersatztag", rechtlich="2022-06-02", wirksam="2022-06-02",
                                                   ersatzgrund="verlegung", verlegt=True)),
    ("LSE", "LSE:LSE.sonder.2022-06-03_platinum_jubilee:2022-06-03", dict(art="sonderschliessung")),
    # Proklamation (London Gazette 56043): 2002 Spring Bank auf Di 4.6. verlegt, Mo 3.6. Golden Jubilee
    ("LSE", "LSE:LSE.spring_bank:2002-05-27", dict(art="ersatztag", rechtlich="2002-06-04", wirksam="2002-06-04",
                                                   ersatzgrund="verlegung", verlegt=True)),
    ("LSE", "LSE:LSE.sonder.2002-06-03_golden_jubilee:2002-06-03", dict(art="sonderschliessung", wirksam="2002-06-03")),
    # gov.uk 2012: Spring Bank auf Mo 4.6. verlegt, Di 5.6. Diamond Jubilee
    ("LSE", "LSE:LSE.spring_bank:2012-05-28", dict(art="ersatztag", rechtlich="2012-06-04", wirksam="2012-06-04",
                                                   ersatzgrund="verlegung", verlegt=True)),
    ("LSE", "LSE:LSE.sonder.2012-06-05_diamond_jubilee:2012-06-05", dict(art="sonderschliessung", wirksam="2012-06-05")),
    # gov.uk 2022: New Year's Day Sa → Mo 3.1. (Bezug zum Regeltermin 1.1.)
    ("LSE", "LSE:LSE.new_year:2022-01-01", dict(art="ersatztag", wirksam="2022-01-03", ersatzgrund="wochenende")),
    # NYSE: 09.01.2025 National Day of Mourning (Carter) — eigene Kennung, nicht MLK (20.01.)
    ("NYSE", "NYSE:NYSE.sonder.2025-01-09_carter:2025-01-09", dict(art="sonderschliessung", name_en=
                                                                   "National Day of Mourning (Jimmy Carter)")),
    ("NYSE", "NYSE:NYSE.mlk_day:2025-01-20", dict(art="feiertag")),
    # NYSE 2021: Independence Day Sonntag → Mo 5.7.
    ("NYSE", "NYSE:NYSE.independence_day:2021-07-04", dict(art="ersatztag", wirksam="2021-07-05", ersatzgrund="wochenende")),
    # Japanisches Feiertagsgesetz: 22.09.2015 Kokumin no Kyujitsu (zwischen Keiro no Hi und Shubun no Hi)
    ("TSE", "TSE:TSE.kokumin_no_kyujitsu:2015-09-22", dict(art="feiertag")),
    # NAOJ 2020 (Olympia-Sondergesetz): Umi no Hi 20.7. → 23.7., Sport no Hi 12.10. → 24.7.
    ("TSE", "TSE:TSE.umi_no_hi:2020-07-20", dict(art="ersatztag", rechtlich="2020-07-23", wirksam="2020-07-23",
                                                 ersatzgrund="verlegung", verlegt=True, quelle="TSE.olympia")),
    ("TSE", "TSE:TSE.sports_no_hi:2020-10-12", dict(rechtlich="2020-07-24", wirksam="2020-07-24", verlegt=True)),
    # NAOJ 2021: Yama no Hi 11.8. → So 8.8., Furikae Mo 9.8.
    ("TSE", "TSE:TSE.yama_no_hi:2021-08-11", dict(art="ersatztag", rechtlich="2021-08-08", wirksam="2021-08-09",
                                                  ersatzgrund="furikae", verlegt=True)),
    # 2023: Ganjitsu So 1.1. → Furikae Mo 2.1.
    ("TSE", "TSE:TSE.ganjitsu:2023-01-01", dict(art="ersatztag", rechtlich="2023-01-01", wirksam="2023-01-02",
                                                ersatzgrund="furikae", verlegt=False)),
    # JPX: Jahreswechsel 31.12., 2.1., 3.1. — je Tag ein Ereignis
    ("TSE", "TSE:TSE.jahreswechsel_1231:2024-12-31", dict(art="feiertag")),
    ("TSE", "TSE:TSE.jahreswechsel_0102:2025-01-02", dict(art="feiertag")),
    ("TSE", "TSE:TSE.jahreswechsel_0103:2025-01-03", dict(art="feiertag")),
    # JPX: 01.10.2020 Systemausfall
    ("TSE", "TSE:TSE.sonder.2020-10-01_systemausfall:2020-10-01", dict(art="sonderschliessung")),
    # Xetra: 25.12.2021 ist ein Samstag — Ereignis ja (Feiertag), Schließung nein (unten)
    ("XETRA", "XETRA:XETRA.weihnachten_1:2021-12-25", dict(art="feiertag", wirksam="2021-12-25")),
    # Xetra-Handelskalender 2017: 31.10.2017 Reformationstag (Sonderschließung)
    ("XETRA", "XETRA:XETRA.sonder.2017-10-31_reformationstag:2017-10-31", dict(art="sonderschliessung")),
    # Nasdaq Stockholm 2008: 1. Mai = Christi Himmelfahrt — zwei Ereignisse, eine Schließung (unten)
    ("STOCKHOLM", "STOCKHOLM:STOCKHOLM.forsta_maj:2008-05-01", dict(art="feiertag")),
    ("STOCKHOLM", "STOCKHOLM:STOCKHOLM.kristi_himmelsfard:2008-05-01", dict(art="feiertag")),
    # KRX 10.04.2024 Parlamentswahl — nur aus der Tabelle, Identität unbestimmt
    ("KRX", "KRX:tabelle:2024-04-10", dict(art="unbestimmt", nominal_herkunft="tabelle", name_de=None, name_en=None,
                                           regel_id="KRX.tabelle")),
]
# (Börse, Jahr, Datum, in get_holidays, in schliessungen)
SOLL_MENGE = [
    ("LSE", 2020, "2020-05-04", False, False), ("LSE", 2020, "2020-05-08", True, True),
    ("LSE", 2022, "2022-05-30", False, False), ("LSE", 2022, "2022-06-02", True, True),
    ("LSE", 2022, "2022-06-03", True, True), ("LSE", 2021, "2021-12-25", False, False),
    ("TSE", 2020, "2020-07-20", False, False), ("TSE", 2020, "2020-10-12", False, False),
    ("TSE", 2021, "2021-08-08", True, False), ("TSE", 2021, "2021-08-09", True, True),
    ("TSE", 2021, "2021-08-11", False, False), ("TSE", 2023, "2023-01-01", True, False),
    ("TSE", 2023, "2023-01-02", True, True), ("XETRA", 2021, "2021-12-25", True, False),
    ("STOCKHOLM", 2008, "2008-05-01", True, True), ("NYSE", 2025, "2025-01-09", True, True),
]


def sollfaelle() -> None:
    for b, eid, felder in SOLL:
        e = ereignis(b, eid)
        if e is None:
            pruefe("Sollfall", False, f"{eid} fehlt oder doppelt")
            continue
        d = e.als_dict()
        for k, v in felder.items():
            pruefe("Sollfall", d[k] == v, f"{eid}.{k}: Ist {d[k]!r}, Soll {v!r}")
    for b, j, tag, in_gh, in_s in SOLL_MENGE:
        pruefe("Sollfall", (D(tag) in EH.get_holidays(b, j, j)) == in_gh, f"{b} {tag} get_holidays Soll {in_gh}")
        pruefe("Sollfall", (D(tag) in BE.schliessungen(b, j)) == in_s, f"{b} {tag} schliessungen Soll {in_s}")
    pruefe("Sollfall", BE.schliessungen("STOCKHOLM", 2008).count(D("2008-05-01")) == 1, "Stockholm 2008-05-01 einmal")
    pruefe("Sollfall", BE.identitaet("KRX", 2024) == "tabelle" and BE.identitaet("TSE", 2024) == "regel", "Identität")


# ── Versionsvertrag ──────────────────────────────────────────────────────────────────────────────────────────
@contextlib.contextmanager
def veraendert(boerse: str, jahr: int, eid: str, **neu):
    alt = BE._REGELN[boerse]

    def regel(j):
        out = alt(j)
        if j == jahr:
            out = [dataclasses.replace(e, **neu) if e.ereignis_id == eid else e for e in out]
        return out

    BE._REGELN[boerse] = regel
    BE._ereignisse.cache_clear()
    BE.kompat.cache_clear()
    BE._kalenderversion_gesamt.cache_clear()
    try:
        yield
    finally:
        BE._REGELN[boerse] = alt
        BE._ereignisse.cache_clear()
        BE.kompat.cache_clear()
        BE._kalenderversion_gesamt.cache_clear()


def versionen() -> None:
    bs, von, bis = ["LSE", "XETRA"], 2020, 2022

    def v():
        return BE.ereignisversion(bs, von, bis), BE.kalenderversion(bs, von, bis)

    basis = v()
    pruefe("Version", basis == v(), "nicht deterministisch")
    faelle = [
        ("a Nominaldatum", "LSE", 2020, "LSE:LSE.early_may:2020-05-04", dict(nominal=date(2020, 5, 5)), (True, False)),
        ("b Name", "LSE", 2020, "LSE:LSE.early_may:2020-05-04", dict(name_de="Maifeiertag"), (True, False)),
        ("b Quelle", "LSE", 2020, "LSE:LSE.early_may:2020-05-04", dict(quelle="LSE.regelwerk"), (True, False)),
        ("c wirksamer Werktag", "LSE", 2022, "LSE:LSE.sonder.2022-06-03_platinum_jubilee:2022-06-03",
         dict(wirksam=date(2022, 6, 6)), (True, True)),
        ("d Wochenenddatum", "XETRA", 2021, "XETRA:XETRA.weihnachten_1:2021-12-25",
         dict(wirksam=date(2021, 12, 26)), (True, False)),
    ]
    for name, b, j, eid, neu, (ev_anders, kv_anders) in faelle:
        pruefe("Version", ereignis(b, eid) is not None, f"{name}: Anker {eid} fehlt")
        with veraendert(b, j, eid, **neu):
            ist = v()
        pruefe("Version", (ist[0] != basis[0]) == ev_anders, f"{name}: ereignisversion anders={ist[0] != basis[0]}")
        pruefe("Version", (ist[1] != basis[1]) == kv_anders, f"{name}: kalenderversion anders={ist[1] != basis[1]}")
    pruefe("Version", v() == basis, "Zustand nach den Versionstests nicht wiederhergestellt")


# ── Zwilling (echte erzeugte Datei in node) ──────────────────────────────────────────────────────────────────
def zwilling() -> None:
    from scripts.build_boersenkalender_js import ZIEL, erzeugen
    with open(ZIEL, "rb") as fh:
        pruefe("Zwilling", fh.read() == erzeugen(), "landing/js/boersenkalender.js nicht aktuell (neu erzeugen)")
    boersen = [b for b in BE.BOERSEN]
    soll = {}
    for b in boersen:
        soll[b] = {
            "ereignisse": {str(j): [e.als_dict() for e in BE.ereignisse(b, j)] for j in range(VON, BIS + 1)
                           if BE.ereignisse(b, j)},
            "schliessungen": {str(j): [d.isoformat() for d in BE.schliessungen(b, j)] for j in range(VON, BIS + 1)
                              if BE.schliessungen(b, j)},
            "identitaet": {str(j): BE.identitaet(b, j) for j in range(VON, BIS + 1)},
        }
    ev_soll = BE.ereignisversion(boersen, VON, BIS)
    kv_soll = BE.kalenderversion(boersen, VON, BIS)
    with tempfile.TemporaryDirectory() as td:
        auftrag = os.path.join(td, "auftrag.json")
        with open(auftrag, "w", encoding="utf-8") as fh:
            json.dump({"boersen": boersen, "von": VON, "bis": BIS}, fh)
        for zone, offs in ZONEN.items():
            r = subprocess.run(["node", PROBE, zone, auftrag], capture_output=True, text=True, encoding="utf-8")
            if r.returncode != 0 or not r.stdout.rstrip().endswith("PROBE-ENDE"):
                pruefe("Zwilling", False, f"{zone}: Probe ohne Endmarker: {r.stderr[-400:]}")
                continue
            ist = json.loads(r.stdout.rstrip()[: -len("PROBE-ENDE")])
            pruefe("Zwilling", ist["offsets"] == offs, f"{zone}: Zone wirkt nicht {ist['offsets']}")
            pruefe("Zwilling", ist["ereignisversion"] == ev_soll, f"{zone}: ereignisversion")
            pruefe("Zwilling", ist["kalenderversion"] == kv_soll, f"{zone}: kalenderversion")
            pruefe("Zwilling", ist["alias_gleich"] is True, f"{zone}: Alias NASDAQ")
            pruefe("Zwilling", ist["eingefroren"] is True, f"{zone}: Ereignisse veränderlich")
            for b in boersen:
                for teil in ("ereignisse", "schliessungen", "identitaet"):
                    a, s = ist["boersen"][b][teil], soll[b][teil]
                    if a != s:
                        jahre = sorted(set(a) | set(s), key=int)
                        erst = next(j for j in jahre if a.get(j) != s.get(j))
                        pruefe("Zwilling", False, f"{zone} {b} {teil} {erst}: JS {a.get(erst)!r:.300} ≠ Py {s.get(erst)!r:.300}")
                    else:
                        pruefe("Zwilling", True)
            pruefe("Zwilling", sum(len(v) for b in boersen for v in ist["boersen"][b]["ereignisse"].values())
                   == sum(len(v) for b in boersen for v in soll[b]["ereignisse"].values()), f"{zone}: Anzahl")


def main() -> int:
    bestand()
    kompat()
    invarianten()
    sollfaelle()
    versionen()
    if "--ohne-node" not in sys.argv:
        zwilling()
    else:
        FEHLER.append("[Zwilling] UNGEPRÜFT (--ohne-node)")
    luecken: dict[str, list[int]] = {}
    for b, j in BE.abnahmeluecken():
        luecken.setdefault(b, []).append(j)
    for b, jahre in luecken.items():
        print(f"ABNAHMELÜCKE {b}: Identität nur aus Datumstabelle {jahre[0]}–{jahre[-1]} ({len(jahre)} Jahre) — "
              "Einzeltage ohne Regel/Name, als 'geschlossen (Tabelle)' auszugeben")
    for f in FEHLER:
        print("FEHL", f)
    n = sum(len(BE.ereignisse(b, j)) for b in BE.BOERSEN for j in range(VON, BIS + 1))
    print(f"verify_boersenereignisse: {ZAEHLER['n'] - len(FEHLER)}/{ZAEHLER['n']} Prüfungen bestanden "
          f"({n} Ereignisse)")
    if not FEHLER:
        print(f"PROBE-ENDE {ZAEHLER['n']} Pruefungen")
    return 0 if not FEHLER else 1


if __name__ == "__main__":
    sys.exit(main())
