# Gegenprüfung: zwei Produktions-DB-Reparaturen (2026-11-22)

Du prüfst read-only. Es ist noch NICHTS geschrieben. Urteile je Reparatur: FREIGABE / FREIGABE MIT AUFLAGEN /
KEINE FREIGABE, mit Begründung. Prüfe die Skripte gegen den Code im Repo: `scripts/backfill_tdoy.py`,
`shared/exchange_holidays.py` (`tdom_tdoy_fuer_ticker`, `handelstag_nummern`, `kalender_status`), `shared/symbols.py`,
`shared/produktionssperre.py`, `shared/basisabweichung.py`, und die Schreibwege von tdom/tdoy und Kursen in
`scripts/nightly_refresh.py` und `scripts/intraday_refresh.py`.

## Anlass

- Der wöchentliche Audit ist rot: `scripts/verify_calendar_rules.py` Regel 4-6 meldet `SAP.DE 2026-09-08: TDOM 5->5`.
- Der Health-Check meldet: Kursbasis SNDK 2026-11-13 ×0.125.

## Reparatur 1: TDOM/TDOY ab 2025 nach Börsenkalender

Die Nutzerentscheidung lautet: alle Ticker außer Futures (`=F`). Futures sind ausgenommen, weil sie auf NYSE gemappt
sind, aber an NYSE-Schließungen (z. B. 09.01.2025) CME-Kurszeilen haben. Welcher Kalender für `=F` gilt, ist offen.

Zusätzlich habe ich CRYPTO und FOREX ausgenommen. Der Kalender zählt Devisen Mo–Fr ohne Feiertage, die DB dagegen nur
Tage mit Kurszeile. 11 Devisenpaare hätten je ~440 Zeilen geändert; das ist eine eigene Entscheidung.

Das Skript läuft im Container und schreibt über `backfill_tdoy.schreiben`. Es schreibt nur tdom/tdoy, je Zeile per
`update … eq(ticker) eq(date)`, und verlangt die Bestätigung von genau einer Zeile. Danach liest es zurück.
Skript und Trockenlauf stehen unten (Anhang A).

Meine Einordnung der Ursachen. Bitte prüfen, nicht übernehmen:

- SNDK/CRWV: Die DB zählte ab Börsengang (Zeilenzählung vor P2), der Kalender zählt ab 1. Januar.
- ^VIX: Eine Phantomzeile an einem US-Feiertag (25.05.2026?) hat TDOY um 1 erhöht.
- Versatz um −1 in Euronext/Stockholm/SIX ab 03.08.2026 (TDOY), in XETRA vom 08.–10.09. (TDOM und TDOY) und bei
  US-Titeln am 11.08. (nur TDOY). Vermutlich stammen diese Zeilen aus Intraday-Läufen vor dem P2-Deploy am 10.10.
- Nachgerechnet: Euronext 2026 Jan–Jul hat 21+20+22+20+20+22+23 = 148 Handelstage, also ist der 03.08. Tag 149. Der
  Kalender stimmt.

Fragen:

- (a) Stimmen die Sollwerte grundsätzlich? Besonders Phantomzeilen an geschlossenen Tagen: `tdom_tdoy_fuer_ticker`
  gibt dort den Wert des letzten Handelstags, das erzeugt Dubletten in der DB. Ist das tragbar?
- (b) Überschreibt ein späterer Nightly- oder Intraday-Lauf die neuen Werte wieder falsch?
- (c) Fehlt eine Sicherung oder Grenze?
- (d) Müssen danach abgeleitete Tabellen (`tdom_stats`, `tdoy_stats`) oder Seiten neu gerechnet werden?

## Reparatur 2: SNDK-Split 8:1

Fakten:

- Der Split wurde am 19.11.2026 nach Handelsschluss wirksam, der erste Tag auf neuer Basis war der 20.11.
  (OCC-Infomemo 60125, 8-K).
- Yahoo hat die Historie rückwirkend angepasst.
- Unser Nightly holt nur die letzten 7 Tage neu. Deshalb liegt der Basisbruch in der DB am 13.11.: Der 12.11. steht
  mit Close 937,46 auf alter Basis, der 13.11. mit 110,63 auf neuer.
- Die gespeicherte log_return vom 13.11. ist −0,05757516. Aus 937,46/8 nachgerechnet ergibt sich −0,05757469.
- 440 Zeilen von 2025-02-13 bis 2026-11-12 stehen auf alter Basis.

Plan:

- Diese 440 Zeilen: open/high/low/close ÷ 8, volume × 8, log_return/tdom/tdoy unverändert.
- Upsert in Blöcken mit `on_conflict=ticker,date`, nur diese Spalten im Payload.
- Sicherung vorher, Rücklesen danach.

Skript und Trockenlauf stehen unten (Anhang B).

Fragen:

- (a) Ist ein Upsert mit Teilspalten hier sicher? Überschreibt er andere Spalten mit NULL, gibt es Trigger oder
  Defaults?
- (b) Durch ÷8 entstehen mehr Nachkommastellen (Yahoo liefert 117.183). Ist das ein Problem für den Kursbasis-Check
  oder das Rücklesen?
- (c) Muss danach etwas neu gerechnet werden?
- (d) Fehlt etwas? Zum Beispiel andere Ticker mit demselben Muster (Split innerhalb des 7-Tage-Fensters).

Antworte knapp, Befunde nummeriert, mit Datei:Zeile.

## Anhang A: tdom_2025_lauf.py

```python
"""TDOM/TDOY ab 2025-01-01 nach Börsenkalender, alle Ticker außer Futures (=F), Krypto und Devisen — Nutzerfreigabe 2026-11-22.

  python3 /tmp/tdom_2025_lauf.py              Trockenlauf: Bericht + Sicherungsdatei (alt/neu je Zeile)
  python3 /tmp/tdom_2025_lauf.py --schreiben  schreibt über backfill_tdoy.schreiben (nur tdom/tdoy, je Zeile bestätigt),
                                              danach Rücklesen: 0 Abweichungen Pflicht
Grenzen je Ticker wie backfill_tdoy.grenzen_pruefen (kein ungeprüftes Kalenderjahr, ≤ 500 Zeilen).
"""
import json
import sys
from datetime import datetime, timezone

sys.path.insert(0, "/app")
sys.path.insert(0, "/app/scripts")
from shared.supabase_client import get_client  # noqa: E402
from shared.symbols import SYMBOLS, get_exchange_for_holidays  # noqa: E402
from shared.produktionssperre import produktion  # noqa: E402
import backfill_tdoy as bt  # noqa: E402

VON, BIS = "2025-01-01", "2026-12-31"
SCHREIB = "--schreiben" in sys.argv


def main():
    c = get_client()
    plan, verweigert, fehler = {}, {}, []
    for t in sorted(SYMBOLS):
        if t.endswith("=F") or get_exchange_for_holidays(t) in ("CRYPTO", "FOREX"):
            continue
        try:
            abw = bt.abweichungen(t, bt.lade(c, t, VON, BIS))
        except Exception as e:
            fehler.append(f"{t}: {type(e).__name__}: {str(e)[:120]}")
            continue
        if not abw:
            continue
        g = bt.grenzen_pruefen(t, VON, BIS, abw, 500)
        (verweigert if g else plan)[t] = g if g else abw
    n = sum(len(v) for v in plan.values())
    print(f"Ticker mit Änderungen: {len(plan)} · Zeilen: {n} · verweigert: {len(verweigert)} · Lesefehler: {len(fehler)}")
    for t, abw in sorted(plan.items(), key=lambda x: -len(x[1])):
        print(f"  {t:10s} {len(abw):4d}  erste {abw[0]['date']} {abw[0]['alt']}→{abw[0]['neu']}  letzte {abw[-1]['date']} {abw[-1]['alt']}→{abw[-1]['neu']}")
    for t, g in verweigert.items():
        print(f"  VERWEIGERT {t}: {g}")
    for f in fehler:
        print("  LESEFEHLER", f)
    stempel = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    pfad = f"/app/logs/reparatur/tdom_tdoy_2025_vorher_{stempel}.json"
    import os
    os.makedirs("/app/logs/reparatur", exist_ok=True)
    with open(pfad, "w") as h:
        json.dump({"von": VON, "bis": BIS, "plan": plan, "verweigert": verweigert}, h)
    print("Sicherung/Plan:", pfad)
    if not SCHREIB:
        return 0
    if fehler or verweigert:
        print("ABBRUCH: Lesefehler oder verweigerte Ticker — nichts geschrieben")
        return 1
    sfehler = []
    for t, abw in plan.items():
        sfehler += [f"{t} {x}" for x in bt.schreiben(c, t, abw)]
    print(f"Geschrieben: {n} Zeilen, Schreibfehler: {len(sfehler)}")
    for f in sfehler[:20]:
        print("  SCHREIBFEHLER", f)
    rest = {t: len(bt.abweichungen(t, bt.lade(c, t, VON, BIS))) for t in plan}
    offen = {t: k for t, k in rest.items() if k}
    print(f"Rücklesen: {len(plan)} Ticker, verbleibende Abweichungen: {sum(offen.values())} {offen if offen else ''}")
    return 1 if sfehler or offen else 0


if __name__ == "__main__":
    with produktion("backfill_tdoy"):
        sys.exit(main())
```

Trockenlauf (Server, 22.11. 15:33 UTC):

```
Ticker mit Änderungen: 109 · Zeilen: 975 · verweigert: 0 · Lesefehler: 0
  SNDK        222  erste 2025-02-13 (1, 1)→(9, 29)  letzte 2025-12-31 (22, 222)→(22, 250)
  CRWV        192  erste 2025-03-28 (1, 1)→(20, 59)  letzte 2025-12-31 (22, 192)→(22, 250)
  ^VIX         84  erste 2026-06-08 (6, 109)→(6, 108)  letzte 2026-10-02 (2, 191)→(2, 189)
  BNP.PA       12  erste 2026-08-03 (1, 148)→(1, 149)  letzte 2026-09-10 (7, 176)→(8, 177)
  CABK.MC      12  erste 2026-08-03 (1, 148)→(1, 149)  letzte 2026-09-10 (7, 176)→(8, 177)
  CS.PA        12  erste 2026-08-03 (1, 148)→(1, 149)  letzte 2026-09-10 (7, 176)→(8, 177)
  EL.PA        12  erste 2026-08-03 (1, 148)→(1, 149)  letzte 2026-09-10 (7, 176)→(8, 177)
  IBE.MC       12  erste 2026-08-03 (1, 148)→(1, 149)  letzte 2026-09-10 (7, 176)→(8, 177)
  ISP.MI       12  erste 2026-08-03 (1, 148)→(1, 149)  letzte 2026-09-10 (7, 176)→(8, 177)
  RMS.PA       12  erste 2026-08-03 (1, 148)→(1, 149)  letzte 2026-09-10 (7, 176)→(8, 177)
  SU.PA        12  erste 2026-08-03 (1, 148)→(1, 149)  letzte 2026-09-10 (7, 176)→(8, 177)
  VOLV-A.ST    12  erste 2026-08-03 (1, 145)→(1, 146)  letzte 2026-09-10 (7, 173)→(8, 174)
  AI.PA        11  erste 2026-08-03 (1, 148)→(1, 149)  letzte 2026-09-10 (7, 176)→(8, 177)
  AIR.PA       11  erste 2026-08-03 (1, 148)→(1, 149)  letzte 2026-09-10 (7, 176)→(8, 177)
  ATCO-B.ST    11  erste 2026-08-03 (1, 145)→(1, 146)  letzte 2026-09-10 (7, 173)→(8, 174)
  CDI.PA       11  erste 2026-08-03 (1, 148)→(1, 149)  letzte 2026-09-10 (7, 176)→(8, 177)
  DG.PA        11  erste 2026-08-03 (1, 148)→(1, 149)  letzte 2026-09-10 (7, 176)→(8, 177)
  ENEL.MI      11  erste 2026-08-03 (1, 148)→(1, 149)  letzte 2026-09-10 (7, 176)→(8, 177)
  ENGI.PA      11  erste 2026-08-03 (1, 148)→(1, 149)  letzte 2026-09-10 (7, 176)→(8, 177)
  G.MI         11  erste 2026-08-03 (1, 148)→(1, 149)  letzte 2026-09-10 (7, 176)→(8, 177)
  HO.PA        11  erste 2026-08-03 (1, 148)→(1, 149)  letzte 2026-09-10 (7, 176)→(8, 177)
  INVE-B.ST    11  erste 2026-08-03 (1, 145)→(1, 146)  letzte 2026-09-10 (7, 173)→(8, 174)
  ITX.MC       11  erste 2026-08-03 (1, 148)→(1, 149)  letzte 2026-09-10 (7, 176)→(8, 177)
  MC.PA        11  erste 2026-08-03 (1, 148)→(1, 149)  letzte 2026-09-10 (7, 176)→(8, 177)
  OR.PA        11  erste 2026-08-03 (1, 148)→(1, 149)  letzte 2026-09-10 (7, 176)→(8, 177)
  PRX.AS       11  erste 2026-08-03 (1, 148)→(1, 149)  letzte 2026-09-10 (7, 176)→(8, 177)
  RO.SW        11  erste 2026-08-03 (1, 145)→(1, 146)  letzte 2026-09-10 (7, 173)→(8, 174)
  SAF.PA       11  erste 2026-08-03 (1, 148)→(1, 149)  letzte 2026-09-10 (7, 176)→(8, 177)
  UCG.MI       11  erste 2026-08-03 (1, 148)→(1, 149)  letzte 2026-09-10 (7, 176)→(8, 177)
  CFR.SW        8  erste 2026-08-03 (1, 145)→(1, 146)  letzte 2026-08-13 (9, 153)→(9, 154)
  ^STOXX50E     5  erste 2026-09-28 (20, 186)→(20, 189)  letzte 2026-10-02 (2, 190)→(2, 193)
  ABBN.SW       3  erste 2026-09-08 (5, 171)→(6, 172)  letzte 2026-09-10 (7, 173)→(8, 174)
  ADS.DE        3  erste 2026-09-08 (5, 174)→(6, 175)  letzte 2026-09-10 (7, 176)→(8, 177)
  ALV.DE        3  erste 2026-09-08 (5, 174)→(6, 175)  letzte 2026-09-10 (7, 176)→(8, 177)
  BAS.DE        3  erste 2026-09-08 (5, 174)→(6, 175)  letzte 2026-09-10 (7, 176)→(8, 177)
  BAYN.DE       3  erste 2026-09-08 (5, 174)→(6, 175)  letzte 2026-09-10 (7, 176)→(8, 177)
  BEI.DE        3  erste 2026-09-08 (5, 174)→(6, 175)  letzte 2026-09-10 (7, 176)→(8, 177)
  BMW.DE        3  erste 2026-09-08 (5, 174)→(6, 175)  letzte 2026-09-10 (7, 176)→(8, 177)
  BNR.DE        3  erste 2026-09-08 (5, 174)→(6, 175)  letzte 2026-09-10 (7, 176)→(8, 177)
  CBK.DE        3  erste 2026-09-08 (5, 174)→(6, 175)  letzte 2026-09-10 (7, 176)→(8, 177)
  CON.DE        3  erste 2026-09-08 (5, 174)→(6, 175)  letzte 2026-09-10 (7, 176)→(8, 177)
  DB1.DE        3  erste 2026-09-08 (5, 174)→(6, 175)  letzte 2026-09-10 (7, 176)→(8, 177)
  DBK.DE        3  erste 2026-09-08 (5, 174)→(6, 175)  letzte 2026-09-10 (7, 176)→(8, 177)
  DHL.DE        3  erste 2026-09-08 (5, 174)→(6, 175)  letzte 2026-09-10 (7, 176)→(8, 177)
  DTE.DE        3  erste 2026-09-08 (5, 174)→(6, 175)  letzte 2026-09-10 (7, 176)→(8, 177)
  DTG.DE        3  erste 2026-09-08 (5, 174)→(6, 175)  letzte 2026-09-10 (7, 176)→(8, 177)
  ENR.F         3  erste 2026-09-08 (5, 174)→(6, 175)  letzte 2026-09-10 (7, 176)→(8, 177)
  EOAN.DE       3  erste 2026-09-08 (5, 174)→(6, 175)  letzte 2026-09-10 (7, 176)→(8, 177)
  FME.DE        3  erste 2026-09-08 (5, 174)→(6, 175)  letzte 2026-09-10 (7, 176)→(8, 177)
  FRE.DE        3  erste 2026-09-08 (5, 174)→(6, 175)  letzte 2026-09-10 (7, 176)→(8, 177)
  G1A.DE        3  erste 2026-09-08 (5, 174)→(6, 175)  letzte 2026-09-10 (7, 176)→(8, 177)
  G24.DE        3  erste 2026-09-08 (5, 174)→(6, 175)  letzte 2026-09-10 (7, 176)→(8, 177)
  HEI.DE        3  erste 2026-09-08 (5, 174)→(6, 175)  letzte 2026-09-10 (7, 176)→(8, 177)
  HEN3.DE       3  erste 2026-09-08 (5, 174)→(6, 175)  letzte 2026-09-10 (7, 176)→(8, 177)
  HNR1.DE       3  erste 2026-09-08 (5, 174)→(6, 175)  letzte 2026-09-10 (7, 176)→(8, 177)
  IFX.DE        3  erste 2026-09-08 (5, 174)→(6, 175)  letzte 2026-09-10 (7, 176)→(8, 177)
  MBG.DE        3  erste 2026-09-08 (5, 174)→(6, 175)  letzte 2026-09-10 (7, 176)→(8, 177)
  MRK.DE        3  erste 2026-09-08 (5, 174)→(6, 175)  letzte 2026-09-10 (7, 176)→(8, 177)
  MTX.DE        3  erste 2026-09-08 (5, 174)→(6, 175)  letzte 2026-09-10 (7, 176)→(8, 177)
  MUV2.DE       3  erste 2026-09-08 (5, 174)→(6, 175)  letzte 2026-09-10 (7, 176)→(8, 177)
  NDX1.DE       3  erste 2026-09-08 (5, 174)→(6, 175)  letzte 2026-09-10 (7, 176)→(8, 177)
  NEL.OL        3  erste 2026-09-08 (5, 171)→(6, 172)  letzte 2026-09-10 (7, 173)→(8, 174)
  PAH3.DE       3  erste 2026-09-08 (5, 174)→(6, 175)  letzte 2026-09-10 (7, 176)→(8, 177)
  QIA.DE        3  erste 2026-09-08 (5, 174)→(6, 175)  letzte 2026-09-10 (7, 176)→(8, 177)
  RHM.F         3  erste 2026-09-08 (5, 174)→(6, 175)  letzte 2026-09-10 (7, 176)→(8, 177)
  RWE.DE        3  erste 2026-09-08 (5, 174)→(6, 175)  letzte 2026-09-10 (7, 176)→(8, 177)
  S92.DE        3  erste 2026-09-08 (5, 174)→(6, 175)  letzte 2026-09-10 (7, 176)→(8, 177)
  SAP.DE        3  erste 2026-09-08 (5, 174)→(6, 175)  letzte 2026-09-10 (7, 176)→(8, 177)
  SHL.DE        3  erste 2026-09-08 (5, 174)→(6, 175)  letzte 2026-09-10 (7, 176)→(8, 177)
  SIE.DE        3  erste 2026-09-08 (5, 174)→(6, 175)  letzte 2026-09-10 (7, 176)→(8, 177)
  SY1.DE        3  erste 2026-09-08 (5, 174)→(6, 175)  letzte 2026-09-10 (7, 176)→(8, 177)
  VNA.DE        3  erste 2026-09-08 (5, 174)→(6, 175)  letzte 2026-09-10 (7, 176)→(8, 177)
  VOW3.DE       3  erste 2026-09-08 (5, 174)→(6, 175)  letzte 2026-09-10 (7, 176)→(8, 177)
  ZAL.DE        3  erste 2026-09-08 (5, 174)→(6, 175)  letzte 2026-09-10 (7, 176)→(8, 177)
  ABBV          2  erste 2026-08-12 (7, 152)→(8, 153)  letzte 2026-08-13 (8, 153)→(9, 154)
  SPOT          2  erste 2026-08-12 (7, 152)→(8, 153)  letzte 2026-08-13 (8, 153)→(9, 154)
  UBS           2  erste 2026-08-12 (7, 152)→(8, 153)  letzte 2026-08-13 (8, 153)→(9, 154)
  XLC           2  erste 2026-08-12 (7, 152)→(8, 153)  letzte 2026-08-13 (8, 153)→(9, 154)
  XLRE          2  erste 2026-08-12 (7, 152)→(8, 153)  letzte 2026-08-13 (8, 153)→(9, 154)
  AON           1  erste 2026-08-11 (7, 150)→(7, 152)  letzte 2026-08-11 (7, 150)→(7, 152)
  CB            1  erste 2026-08-11 (7, 151)→(7, 152)  letzte 2026-08-11 (7, 151)→(7, 152)
  COF           1  erste 2026-08-11 (7, 151)→(7, 152)  letzte 2026-08-11 (7, 151)→(7, 152)
  DE            1  erste 2026-08-11 (7, 149)→(7, 152)  letzte 2026-08-11 (7, 149)→(7, 152)
  ETN           1  erste 2026-08-11 (7, 150)→(7, 152)  letzte 2026-08-11 (7, 150)→(7, 152)
  EWZ           1  erste 2026-08-11 (7, 151)→(7, 152)  letzte 2026-08-11 (7, 151)→(7, 152)
  HYG           1  erste 2026-08-11 (7, 150)→(7, 152)  letzte 2026-08-11 (7, 150)→(7, 152)
  ICE           1  erste 2026-08-11 (7, 150)→(7, 152)  letzte 2026-08-11 (7, 150)→(7, 152)
  IYT           1  erste 2026-08-11 (7, 149)→(7, 152)  letzte 2026-08-11 (7, 149)→(7, 152)
  KRE           1  erste 2026-08-11 (7, 151)→(7, 152)  letzte 2026-08-11 (7, 151)→(7, 152)
  MAR           1  erste 2026-08-11 (7, 151)→(7, 152)  letzte 2026-08-11 (7, 151)→(7, 152)
  MS            1  erste 2026-08-11 (7, 151)→(7, 152)  letzte 2026-08-11 (7, 151)→(7, 152)
  NVS           1  erste 2026-08-11 (7, 149)→(7, 152)  letzte 2026-08-11 (7, 149)→(7, 152)
  PGR           1  erste 2026-08-11 (7, 150)→(7, 152)  letzte 2026-08-11 (7, 150)→(7, 152)
  PLD           1  erste 2026-08-11 (7, 150)→(7, 152)  letzte 2026-08-11 (7, 150)→(7, 152)
  SAN           1  erste 2026-08-11 (7, 149)→(7, 152)  letzte 2026-08-11 (7, 149)→(7, 152)
  SCHW          1  erste 2026-08-11 (7, 151)→(7, 152)  letzte 2026-08-11 (7, 151)→(7, 152)
  SHW           1  erste 2026-08-11 (7, 149)→(7, 152)  letzte 2026-08-11 (7, 149)→(7, 152)
  SPGI          1  erste 2026-08-11 (7, 150)→(7, 152)  letzte 2026-08-11 (7, 150)→(7, 152)
  TT            1  erste 2026-08-11 (7, 150)→(7, 152)  letzte 2026-08-11 (7, 150)→(7, 152)
  TTE           1  erste 2026-08-11 (7, 150)→(7, 152)  letzte 2026-08-11 (7, 150)→(7, 152)
  WM            1  erste 2026-08-11 (7, 150)→(7, 152)  letzte 2026-08-11 (7, 150)→(7, 152)
  XME           1  erste 2026-08-11 (7, 149)→(7, 152)  letzte 2026-08-11 (7, 149)→(7, 152)
  ^FCHI         1  erste 2026-08-11 (7, 152)→(7, 155)  letzte 2026-08-11 (7, 152)→(7, 155)
  ^GSPC         1  erste 2026-08-11 (7, 149)→(7, 152)  letzte 2026-08-11 (7, 149)→(7, 152)
  ^HSI          1  erste 2026-08-11 (7, 145)→(7, 148)  letzte 2026-08-11 (7, 145)→(7, 148)
  ^IBEX         1  erste 2026-08-11 (7, 152)→(7, 155)  letzte 2026-08-11 (7, 152)→(7, 155)
  ^OVX          1  erste 2026-08-11 (7, 149)→(7, 152)  letzte 2026-08-11 (7, 149)→(7, 152)
  ^RUT          1  erste 2026-08-11 (7, 149)→(7, 152)  letzte 2026-08-11 (7, 149)→(7, 152)
  ^SSMI         1  erste 2026-08-11 (7, 149)→(7, 152)  letzte 2026-08-11 (7, 149)→(7, 152)
Sicherung/Plan: /app/logs/reparatur/tdom_tdoy_2025_vorher_20261122T153316.json
```

## Anhang B: sndk_split.py

```python
"""SNDK-Split 8:1 einpflegen (Nutzerfreigabe 2026-11-22, Muster SOXX v66.29).

Split wirksam 19.11.2026 nach Handelsschluss, erster Tag neuer Basis 20.11. (OCC-Infomemo 60125, 8-K). Yahoo hat
die Historie rückwirkend angepasst; der Nightly holte nur 7 Tage neu, daher liegt der Basisbruch in der DB am
Fensterrand 13.11. (12.11. alt 937,46, 13.11. neu 110,63).


Alle SNDK-Zeilen VOR dem 13.11.2026: open/high/low/close ÷ 8, volume × 8, log_return/tdom/tdoy unverändert.
  python3 /tmp/sndk_split.py              Trockenlauf: Prüfungen + Sicherung, nichts geschrieben
  python3 /tmp/sndk_split.py --schreiben  Upsert in Blöcken (nur ticker,date + die fünf Spalten), danach Rücklesen
Vorbedingungen (sonst Abbruch): 12.11. ÷ 8 erklärt die gespeicherte Rendite des 13.11. (|Δ| < 1e-4), Yahoo meldet
den Split 8:1 am 13.11., keine Zeile vor dem Split hat bereits Kurse < 200 (Schutz gegen Doppelanwendung).
"""
import json
import math
import os
import sys
from datetime import datetime, timezone

import requests

sys.path.insert(0, "/app")
from shared.supabase_client import get_client  # noqa: E402
from shared.produktionssperre import produktion  # noqa: E402

T, SPLIT, F = "SNDK", "2026-11-13", 8   # SPLIT = erste Zeile auf neuer Basis in der DB
SCHREIB = "--schreiben" in sys.argv
SPALTEN = "ticker,date,open,high,low,close,volume,log_return,tdom,tdoy"


def lade(c, bis=None):
    z, ab = [], "1900-01-01"
    while True:
        q = c.table("prices").select(SPALTEN).eq("ticker", T).gt("date", ab)
        r = q.order("date").limit(1000).execute().data
        z += r
        if len(r) < 1000:
            return z
        ab = r[-1]["date"]


def main():
    c = get_client()
    alle = lade(c)
    vor = [z for z in alle if z["date"][:10] < SPLIT]
    nach = {z["date"][:10]: z for z in alle if z["date"][:10] >= SPLIT}
    letzte, erste = vor[-1], nach[SPLIT]
    erklaert = math.log(erste["close"] / (letzte["close"] / F))
    print(f"Zeilen vor Split: {len(vor)} ({vor[0]['date'][:10]}..{letzte['date'][:10]}), nach: {len(nach)}")
    print(f"Rendite 13.11. gespeichert {erste['log_return']:.8f}, aus 12.11./8 {erklaert:.8f}")
    y = requests.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{T}?range=1mo&interval=1d&events=split",
                     headers={"User-Agent": "Mozilla/5.0"}, timeout=20).json()["chart"]["result"][0]
    splits = [(datetime.fromtimestamp(s["date"], timezone.utc).date().isoformat(), s["numerator"] / s["denominator"])
              for s in (y.get("events") or {}).get("splits", {}).values()]
    print("Yahoo-Splits:", splits)
    gruende = []
    if abs(erklaert - erste["log_return"]) > 1e-4:
        gruende.append("Rendite des Splittags passt nicht zu Faktor 8")
    if not any(d in ("2026-11-19", "2026-11-20") and abs(f - F) < 1e-9 for d, f in splits):
        gruende.append("Yahoo meldet keinen Split 8:1 am 19./20.11.")
    if min(z["close"] for z in vor[-60:]) < 200:
        gruende.append("Zeilen vor dem Split sehen schon umgerechnet aus (Doppelanwendung?)")
    if any(z[k] is None for z in vor for k in ("open", "high", "low", "close")):
        gruende.append("NULL-Kurse vor dem Split")
    os.makedirs("/app/logs/reparatur", exist_ok=True)
    pfad = f"/app/logs/reparatur/sndk_basis_vorher_{datetime.now(timezone.utc):%Y%m%dT%H%M%S}.json"
    with open(pfad, "w") as h:
        json.dump(vor, h)
    print("Sicherung:", pfad)
    if gruende:
        print("ABBRUCH:", gruende)
        return 1
    neu = [{"ticker": T, "date": z["date"][:10], "open": z["open"] / F, "high": z["high"] / F, "low": z["low"] / F,
            "close": z["close"] / F, "volume": int(round((z["volume"] or 0) * F)) if z["volume"] is not None else None}
           for z in vor]
    print(f"Beispiel {neu[-1]}")
    if not SCHREIB:
        print("Trockenlauf — nichts geschrieben")
        return 0
    for i in range(0, len(neu), 200):
        r = c.table("prices").upsert(neu[i:i + 200], on_conflict="ticker,date").execute()
        if len(r.data or []) != len(neu[i:i + 200]):
            print("SCHREIBFEHLER Block", i, len(r.data or []))
            return 1
    zurueck = {z["date"][:10]: z for z in lade(c)}
    abw = 0
    for z, n in zip(vor, neu):
        r = zurueck[n["date"]]
        for k in ("open", "high", "low", "close"):
            if abs(r[k] - n[k]) > 1e-6 * max(1, abs(n[k])):
                abw += 1
        if r["volume"] != n["volume"] or r["log_return"] != z["log_return"] or r["tdom"] != z["tdom"] or r["tdoy"] != z["tdoy"]:
            abw += 1
    print(f"Rücklesen: {len(neu)} Zeilen, Abweichungen {abw}")
    return 1 if abw else 0


if __name__ == "__main__":
    with produktion("backfill_tdoy"):
        sys.exit(main())
```

Trockenlauf:

```
Zeilen vor Split: 440 (2025-02-13..2026-11-12), nach: 6
Rendite 13.11. gespeichert -0.05757516, aus 12.11./8 -0.05757469
Yahoo-Splits: [('2026-11-20', 8.0)]
Sicherung: /app/logs/reparatur/sndk_basis_vorher_20261122T153419.json
Beispiel {'ticker': 'SNDK', 'date': '2026-11-12', 'open': 110.924375, 'high': 119.15, 'low': 108.6825, 'close': 117.1825, 'volume': 106097600}
Trockenlauf — nichts geschrieben
```
