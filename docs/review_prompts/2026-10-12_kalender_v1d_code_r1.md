# Kalender-Umstellung V1d — Code-Runde 1 (Sitzungshelfer)

Entwurf freigegeben in [v2](2026-10-12_kalender_v1d_entwurf_v2.md) · [Antwort](2026-10-12_kalender_v1d_entwurf_v2_antwort.md).
Auflagen v2: unabhängige Referenz, vollständiges Raster 1885–2100, Rand-/Zeitzonenfälle, wirksame Mutationen;
`naechsterHandelstag` delegiert einschließlich; unbekannte Halbtag-Abdeckung → `halbtag=null`; Generatorprüfung und
Sitzungswächter im Gate. Read-only, Arbeitsbaum (nicht committet).

<task>Ist der Code V1d freigegeben? Sind die Auflagen erfüllt?</task>

## Dateien
- **neu** `shared/sitzungen.py`: `offen`, `sitzungen`, `naechste`/`vorherige` (keyword-only `einschliesslich`,
  `type is bool`), `verschiebe` (`type is int`, ≠ 0, offenes Ausgangsdatum), `nte_im_monat`,
  `nte_von_hinten_im_monat`, `nte_im_jahr`, `heute` (`datetime` mit `tzinfo`, Zone aus `_SCHLUSSZEIT`,
  CRYPTO/FOREX UTC), `zieltermin` (zwei Arten, `heute` einmal erfasst), `sitzung_info` (Halbtag aus V1c-3,
  `halbtag=None` bei ungeprüfter Abdeckung). Rechenbereich in jedem Helfer geprüft, Suchen enden am Rand mit Fehler.
- `scripts/boersenkalender/api.js` → `landing/js/boersenkalender.js`: Kern `suche`, `sitzungenListe`,
  `nteImMonat`/`nteVonHintenImMonat`/`nteImJahr`, `heuteBerechnen` (Epoch-ms ganzzahlig oder ISO mit `Z`/`±HH:MM`,
  `Intl.DateTimeFormat` formatToParts); API `sitzungen(von, bis, boerse)`, `naechste(datum, boerse, einschliesslich)`,
  `vorherige`, `verschiebe`, `nteImMonat`, `nteVonHintenImMonat`, `nteImJahr`, `heute`, `zieltermin`, `sitzungInfo`.
  Alte Funktionen als Hüllen: `nterHandelstag`/`letzterHandelstag`/`nterHandelstagImJahr`/`naechsterHandelstag`
  (einschließlich). Generator schreibt `zonen` aus `shared.sitzungen.ZONEN`.
- **neu** `scripts/verify_sitzungen.py` (+ `scripts/js/probe_sitzungen.js`), im Gate nach dem numpy-Schritt:
  [Referenz] numpy `busday_offset`/`is_busday` aus Wochenmaske + `get_holidays`, jeder Tag 1885–2100 an 13 Börsen
  (vier Suchen), `verschiebe` (±1/5/21 auf jeder 7., ±252 jeder 49., ±2520 jeder 343. Sitzung — gekürzt, weil
  das volle Raster 26 min brauchte; jetzt 2½ min), Positionen, `sitzungen` = Referenzfolge; [Sollfall] 52 Fälle
  inkl. Hüllen, Ränder, Eingaben, `heute` an DST-Wechseln/Mitternacht, `zieltermin`, `sitzung_info`;
  [Zwilling] JS-Raster und -Fälle unter UTC und Pacific/Kiritimati, Fälle zusätzlich America/Adak, Objektgleichheit.
- **neu** `scripts/verify_sitzungen_mutation.py`: 14 Mutationen (Python 8, JS/Generator 6), isoliert.

## Nachweise
`verify_sitzungen` 399/399 · Mutationstest 14/14 + 2 Gegenproben, Projektbaum unverändert ·
`verify_boersenkalender_js` 62/62 (Hüllen unverändertes Verhalten).
Eigene Funde unterwegs: ein selbst eingetragener Sollwert war falsch (dritte Juli-Sitzung 2026 ist der 6., nicht
der 7.); gemischte Zeilenenden im Generator machten eine Mutation ungültig (vereinheitlicht).

## Ausgabevertrag
**Urteil** · **Befunde** (P1/P2, Datei:Zeile) · **Auflagen**. ≤ 20 Zeilen.
