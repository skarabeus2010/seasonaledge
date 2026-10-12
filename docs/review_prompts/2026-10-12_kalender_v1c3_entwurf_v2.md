# Kalender-Umstellung V1c-3 — Entwurf v2 (Halbtage)

Runde 1: [Entwurf v1](2026-10-12_kalender_v1c3_entwurf.md) · [Antwort](2026-10-12_kalender_v1c3_entwurf_antwort1.md)
(3 × P2, kein P1). Alles aus v1 gilt, außer den folgenden Punkten. Read-only.

<task>Sind die drei P2-Befunde aufgelöst? Ist V1c-3 als Bauvorlage freigegeben? Bitte die Belegdaten unten gegen
die Quellen prüfen.</task>

## 1 Bedeutung der Uhrzeit (P2)
Drei Felder, für Nicht-Halbtage ausdrücklich `null`: `schlusszeit` (`HH:MM` lokal), `zeitzone` (IANA),
`sitzung`. Für NYSE: `schlusszeit = "13:00"`, `zeitzone = "America/New_York"`,
`sitzung = "nyse_aktien_kernhandel"` — der reguläre Schluss des Aktien-Kernhandels. Optionen (13:15), Late Sessions
(17:00) und Crossing Sessions sind **nicht** Inhalt des Feldes und werden nicht modelliert. LSE wird in V1c-3 nicht
aufgenommen (siehe §3); käme sie später, hieße ihr Feld `sitzung = "lse_schliessungsbeginn"` mit eigener Bedeutung
(Beginn des Schließungsprozesses), nie „Schluss".

## 2 Jahresabdeckung als eigener Beleg (P2)
Belegreihe `HALBTAGE["NYSE"]` in einem neuen Modul `shared/halbtage_belege.py`: `ereignisse` (Datum → Kurzname +
Quelle) und **getrennt** `jahre_vollstaendig` (Jahre, für die eine Quelle das **ganze Jahr** abdeckt), je mit Quelle
und Abrufdatum 2026-10-12. `halbtag_status(b, j) = "belegt"` nur für Jahre in `jahre_vollstaendig`, sonst
`"ungeprueft"`. Ein einzeln belegter Halbtag erscheint auch in einem `ungeprueft`-Jahr als Ereignis.
Bundle führt Ereignisse **und** `jahre_vollstaendig`; JS `halbtag_status` wie Python.

## 3 Belegdaten (aus den von dir genannten Quellen gelesen, 2026-10-12)
NYSE, 13:00 ET Aktien-Kernhandel:
- 2014: 03.07., 28.11., 24.12. · 2015: 27.11., 24.12. (ICE 2013, deckt 2014 und 2015 ganz)
- 2016: 25.11. — nur aus der ICE-Mitteilung 2016 zum Kalender 2017, deckt 2016 **nicht** ab Januar → Ereignis ja,
  Jahr `ungeprueft`
- 2017: 03.07., 24.11. · 2018: 03.07., 23.11., 24.12. · 2019: 03.07., 29.11., 24.12. · 2020: 27.11., 24.12. ·
  2021: 26.11. (ICE 2016/2017/2018)
- 2022: 25.11. · 2023: 03.07., 24.11. · 2024: 03.07., 29.11., 24.12. · 2025: 03.07., 28.11., 24.12. (ICE 2021/2022)
- 2026: 27.11., 24.12. · 2027: 26.11. · 2028: 03.07., 24.11. (nyse.com Hours & Calendars, Ankündigung)
`jahre_vollstaendig = 2014, 2015, 2017–2028`. Vor 2014 und 2016: `ungeprueft`. LSE: ungeprüft (die Seite ist hier
nicht maschinell lesbar; deine Belege 2026–2028 werden in einer späteren Erweiterung aufgenommen).

## 4 Wächter (P2 Vollständigkeit)
- **Unabhängige Jahres-Sollmengen** im Wächter, handgeschrieben je Jahr 2014–2028 aus den Quellen (nicht aus dem
  Modul importiert): Ereignismenge des Katalogs == Sollmenge, je Jahr; dazu Negativfälle 2020-07-02, 2021-07-02,
  2022-07-01, 2026-07-02, 2027-07-02 (kein Halbtag) und 2026-07-03, 2027-07-05 (Vollschließung, kein Halbtag).
- Jeder Halbtag liegt auf einem offenen Tag, erscheint weder in `get_holidays` noch in `schliessungen`;
  Momentaufnahme (3 024 Börsen-Jahre) unverändert.
- Versionen: Uhrzeit- oder Zonenänderung → `ereignisversion` anders, `kalenderversion` gleich (Wächtertest).
- Python = JS Objektgleichheit inkl. der drei neuen Felder (`null` bei Nicht-Halbtagen) und `halbtag_status`.
- Mutationen: Halbtag gelöscht; falsche Uhrzeit; falsche Zone; 2016 fälschlich vollständig; Halbtag als Schließung
  gezählt; Halbtag ohne Beleg erzeugt; JS-Decoder verliert `schlusszeit`.

## Ausgabevertrag
**Urteil** · **Befunde** · **Auflagen**. ≤ 15 Zeilen.
