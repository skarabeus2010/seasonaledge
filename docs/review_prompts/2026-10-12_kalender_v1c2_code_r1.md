# Kalender-Umstellung V1c-2 — Code-Runde 1 (US-Produkttermine OPEX und VIX)

Entwurf freigegeben in [v6](2026-10-12_kalender_v1c2_entwurf_v6.md) · [Antwort](2026-10-12_kalender_v1c2_entwurf_v6_antwort.md).
Auflagen v6: Pflichtparameter (inkl. fehlendem JS-Argument), Feldgruppen und `abdeckung(pruefdatum)` im
Produktionspfad; beide Mutationen (Datenstand statt Prüfdatum, ≥ statt >) gezielt rot; Bestandsschutz, unabhängige
Sollfälle, Python = JS; getrennte Monatsbelege mit Quelle und Abrufdatum. Read-only, Arbeitsbaum (nicht committet).

<task>Ist der Code V1c-2 freigegeben? Sind die Auflagen aus v6 erfüllt? Stimmen die Belegdaten?</task>

## Dateien
- **neu** `shared/produkttermine.py` — Regeln OPEX (ab 2015-02) und VIX (ab Kontrakt 2015-09, ODER-Regel), Einstufung
  `belegt/projektion/luecke` erst bei der Abfrage mit Pflicht-`pruefdatum` (keyword-only, kein Standard),
  `produkttermine(von, bis, art, *, pruefdatum, offen, belege)`, `abdeckung(*, pruefdatum)`, `produktversion()`
  (Fakten: Regeltermine + Belege), `VIX_BIS = 2100-11` (Dezember 2100 bräuchte den Referenzfreitag 2101).
- **neu** `shared/produkttermine_listung.py` — drei Belegreihen:
  `VX` 142 Kontrakte 2015-09…2027-06 per HEAD-Abruf auf `cdn.cboe.com/.../VX/VX_<Settlement>.csv` (ab 2027-07 HTTP
  403 = noch nicht gelistet); `SPX_STANDARD` und `VIX_OPT` je 84 Monate 2020–2026 aus den Cboe-Jahreskalendern
  `cdn.cboe.com/resources/options/Cboe<Jahr>OPTIONSCalendar.pdf` (visuell abgelesen; für 2014–2019 unter diesem
  Muster nicht vorhanden). Gegenprobe: VIX_OPT = VX in allen 84 Monaten.
- `scripts/boersenkalender/api.js` → `landing/js/boersenkalender.js`: `produkttermine(von, bis, art, pruefdatum)`,
  `abdeckung(pruefdatum)` (fehlendes Prüfdatum → `KalenderFehler`), `produktversion`; Generator schreibt nur Fakten.
- **neu** `scripts/verify_produkttermine.py` (+ `scripts/js/probe_produkttermine.js`), im Gate: 85 Prüfungen —
  [Beleg] alle 310 Belege = Regel; [Sollfall]; [Grenze] Datenstand 2025-06-30/Prüfdatum fest, Gleichheitsfall;
  [Synthetisch] Do zusätzlich zu, Codex-Fall 17.04.2025, Mi+Fr, Mi+Di+Fr, nur Mi, nur Di; [Abhängigkeit];
  [Pflicht] Python TypeError + JS KalenderFehler; [Zwilling] vier Prüfdaten (inkl. 2027-01-15 = Regeltermin ohne
  Beleg) × zwei Zeitzonen. Abdeckungslücken werden ausgegeben: SPX_STANDARD 2015-02…2019-12 (59), VIX_OPT
  2015-09…2019-12 (52).
- **neu** `scripts/verify_produkttermine_mutation.py` (nutzt die Mechanik von `verify_boersenereignisse_mutation.py`,
  dort nur der Wächtername parametriert): 15/15 gefangen, 2 Gegenproben verworfen, Projektbaum unverändert.
  Beim ersten Lauf entwischte „JS ≥ statt >" (kein Prüfdatum traf einen unbelegten Regeltermin) → Prüfdatum ergänzt.
- `scripts/verify_calendar_rules.py` Regel 8 ruft jetzt `vix_regel` statt einer eigenen (additiven) Kopie.

## Bewusst nicht in V1c-2
`nyse_holidays.get_opex_date/get_all_opex_dates` und alle Verbraucher (Seiten, Mails, `market_events`,
`ist_monatsverfall`) bleiben unverändert — Umstellung in V3. Deshalb keine Hülle und keine OPEX-Momentaufnahme hier;
die alten Werte ändern sich nicht. Bitte prüfen, ob das die Bestandsschutz-Auflage erfüllt oder ob die
Momentaufnahme (2 592 Monate, alle Rückgabefelder) schon jetzt eingefroren werden muss.

## Ausgabevertrag
**Urteil** · **Befunde** (P1/P2, Datei:Zeile) · **Auflagen**. ≤ 25 Zeilen.
