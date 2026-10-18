# Kalender-Umstellung V2 — Code Runde 4

Runde 3: [Vorlage](2026-10-18_kalender_v2_code_r3.md) · [Antwort](2026-10-18_kalender_v2_code_r3_antwort.md)
(keine Freigabe; offen: exakter Nachfolger Mailand/LSE ohne Börsenbeleg, Februar ohne Schalttag). Arbeitsbaum.
Read-only.

<task>Sind die zwei Befunde aus Runde 3 erledigt? Ist V2 freigabefähig?</task>

## Zu den Befunden
1. **Ersatz-Referenzmonate mit belegtem Nachfolger** (Auflage „nötigenfalls einen anderen Referenzmonat wählen"):
   Mailand **November 2026** (Euronext-Tabelle 2026, Spalte Milan; 213 Sitzungen davor; erste Dezembersitzung
   01.12. belegt), LSE **September 2026** (LSE business-days ab 31.08. + gov.uk Bank Holidays England & Wales für
   Januar–Mai, Übereinstimmung beider Quellen an 31.08./25.12./28.12.; 167 Sitzungen davor; erste Oktobersitzung
   01.10. belegt). Damit hat jede Liste einen exakt belegten Nachfolger; der Zweig „nur Folgemonat geprüft" wird von
   keiner Liste mehr erreicht (bleibt für künftige unbelegte Listen sichtbar benannt).
2. **Monatslänge** über `calendar.monthrange` — CRYPTO 02/2028 prüft jetzt den 29.02.2028 (Offenheit, Nummern,
   Nachfolger 01.03.2028).

Wächter 2239 Prüfungen grün; Mutationstest 20/20 (+ 2 Gegenproben verworfen), Projektbaum-Hash vor = nach.

## Ausgabevertrag
**Urteil** · **Befunde** (nur neue/offene) · **Auflagen**. ≤ 15 Zeilen.
