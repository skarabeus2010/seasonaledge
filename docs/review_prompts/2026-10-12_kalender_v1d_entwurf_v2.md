# Kalender-Umstellung V1d — Entwurf v2 (Sitzungshelfer Python + JS)

Runde 1: [Entwurf v1](2026-10-12_kalender_v1d_entwurf.md) · [Antwort](2026-10-12_kalender_v1d_entwurf_antwort1.md)
(5 × P2, kein P1; Antworten 1–3 übernommen). Alles aus v1 gilt, außer den folgenden Punkten. Read-only.

<task>Sind die fünf P2-Befunde aufgelöst? Ist V1d als Bauvorlage freigegeben?</task>

## 1 `sitzung_info` mit Halbtag-Abdeckung (P2)
`sitzung_info(datum, boerse)` → `{offen, halbtag, halbtag_status, schlusszeit, zeitzone, sitzung}`:
- geschlossen: `offen=false`, `halbtag=null`, `schlusszeit=null`, `zeitzone=null`, `sitzung=null`;
- offen + belegtes Halbtagsereignis: `halbtag=true`, `schlusszeit/zeitzone/sitzung` aus dem Ereignis;
- offen, kein Ereignis, `halbtag_status(boerse, jahr) == "belegt"`: `halbtag=false`, `schlusszeit=null`
  (reguläre Schlusszeiten werden **nicht** als historisch belegte Sitzungszeit ausgegeben);
- offen, kein Ereignis, `ungeprueft`: `halbtag=null` (unbekannt), `schlusszeit=null`.
`halbtag_status` ist immer gesetzt (für geschlossene Tage der Status des Jahres).

## 2 Zeitpunktvertrag (P2)
- Python `heute(boerse, jetzt)`: `jetzt` muss ein `datetime` **mit** `tzinfo` sein (naiv → `TypeError`); kein
  Standardwert. JS `heute(boerse, jetzt)`: `jetzt` muss eine ganze Zahl (Epoch-Millisekunden) **oder** ein
  ISO-Zeitstempel mit `Z` bzw. `±HH:MM` sein; alles andere → `KalenderFehler`.
- Umrechnung in die Börsenzone: Python `zoneinfo`, JS `Intl.DateTimeFormat(..., {timeZone})` (formatToParts).
  Zonen = Python `_SCHLUSSZEIT` (IANA) + `CRYPTO`/`FOREX` → `"UTC"`, **einmal** aus Python ins Bundle erzeugt; Börse
  ohne Zone → Fehler. Rückgabe `{boerse, datum, zeitzone, zeitpunkt_utc}` (normalisiert, ISO mit `Z`).
- `zieltermin(boerse, jetzt, *, art)` erfasst `heute` genau einmal; Handelsschluss ändert die Datumswahl nicht.

## 3 Eingabe- und Randvertrag (P2)
- Rechenbereich 1885-01-01 … 2100-12-31 in **allen** neuen Helfern selbst geprüft (Python wirft `ValueError`, JS
  `KalenderFehler`); `sitzungen(von, bis)` schließt beide Enden ein, `von > bis` → Fehler.
- `einschliesslich` muss ein echtes Boolean sein (Python `type(x) is bool`, JS `typeof === 'boolean'`); `n` eine
  ganze Zahl ≠ 0 (Boolean zählt nicht als Zahl); `verschiebe` verlangt ein offenes Ausgangsdatum.
- Suche nach vorn **und** hinten endet am jeweiligen Rand mit Fehler (B5.8).
- Positionen (`nte_*`): `n < 1` oder Monat außerhalb 1–12 → Fehler; gültige, aber nicht vorhandene Position → `None`/`null`.
- Die bestehenden JS-Funktionen (`nterHandelstag`, `letzterHandelstag`, `nterHandelstagImJahr`,
  `naechsterHandelstag`) bleiben als **delegierende Hüllen** auf die neuen Helfer (unverändertes Verhalten, Wächter
  `verify_boersenkalender_js` bleibt grün).

## 4 Unabhängige Referenz und Ränder (P2)
- **Unabhängige Sitzungsfolge:** im Wächter je Börse und Jahr mit `numpy.busday_*` aus Wochenmaske + `get_holidays`
  (andere Logik als die Helfer; die Feiertagsmenge selbst ist durch die Momentaufnahme geschützt) — vergleicht
  `sitzungen`, `naechste/vorherige` (beide Modi), `verschiebe` mit n ∈ {±1, ±5, ±21, ±252, ±2520} und die
  Positionsfunktionen gegen Indexrechnung auf dieser Referenzfolge, **1885–2100 vollständig** (nicht nur 2000–2030).
- **Ränder:** 1885-01-01/02 und 2100-12-30/31 je Richtung und Modus, `verschiebe` über den Rand → Fehler.
- **Sollfälle (handgeschrieben):** TSE 27.04.2019 → 07.05.2019 (Golden Week + Thronwechsel), NYSE 2026-07-02 →
  2026-07-06, XETRA 2026-12-23 → 2026-12-28, Jahreswechsel, CRYPTO jeder Tag, FOREX Fr → Mo; `sitzung_info` NYSE
  2025-11-28 (Halbtag), 2025-11-26 (belegt voll), 2012-11-23 (ungeprüft → `halbtag=null`), XETRA 2025-12-23
  (ungeprüft).
- **`heute`:** NYSE an der Sommerzeitumstellung (2026-03-08 06:59Z/07:00Z, 2026-11-01), um New Yorker Mitternacht,
  Berlin vor/nach 00:00 für NYSE und XETRA, Tokio, CRYPTO/FOREX UTC; ungültige Eingaben (naiv, ohne Offset, Text,
  Boolean) → Fehlerklasse.
- **Zwilling Python = JS** über das volle Raster in zwei benannten Prozesszonen **UTC** und **Pacific/Kiritimati**
  (+14, das Ergebnis darf nicht von der Rechnerzone abhängen) — `heute` zusätzlich unter **America/Adak**.
- **Mutationstest** isoliert, atomar, frischer Bytecodepfad, Fehlerklasse geprüft (Absturz/abgefangene Ausnahme
  zählt nicht): einschließlich/strikt vertauscht, feste 10-Tage-Grenze, Halbtag ungeprüft als „voll", `heute` in
  UTC statt Börsenzone, naive Zeit angenommen, `verschiebe` zählt Kalendertage, Rand ohne Fehler, JS-Hülle ändert
  Verhalten. Generatorprüfung und Sitzungswächter ins Gate.

## 5 Doku (P2)
`docs/KALENDER_UMSTELLUNG.md` korrigiert: die Betriebskonvention (`letzte_session`/`markt_offen`, Halbtag = voller
Tag) bleibt auch in V1d unverändert; eine Änderung nur gemeinsam für beide Funktionen in einer eigens benannten
Betriebsphase.

## Ausgabevertrag
**Urteil** · **Befunde** · **Auflagen**. ≤ 15 Zeilen.
