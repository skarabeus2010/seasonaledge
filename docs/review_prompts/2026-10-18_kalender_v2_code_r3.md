# Kalender-Umstellung V2 — Code Runde 3

Runde 2: [Vorlage](2026-10-18_kalender_v2_code_r2.md) · [Antwort](2026-10-18_kalender_v2_code_r2_antwort.md)
(keine Freigabe; Typprüfung, EN, Inventar erledigt; offen: exakter Monatsnachfolger, Konventionsreferenzen,
alle 57 Statusfälle durch beide Anzeigen). Arbeitsbaum. Read-only.

<task>Sind die drei Befunde aus Runde 2 erledigt? Ist V2 freigabefähig?</task>

## Zu den Befunden
1. **Exakter Nachfolger:** `scripts/fixtures/kalender_monatslisten_2026.json` trägt je Börse
   `erste_sitzung_folgemonat` (Datum, Status, Quelle — wieder aus der Börsenquelle recherchiert, ohne Blick in den
   Code): NYSE 01.12., Xetra 04.01.2027 (Tabelle „handelsfreie Tage bis 2031“ der Deutschen Börse), Euronext 04.05.,
   SIX 01.09., Stockholm 01.07., Oslo 01.06., TSE 01.06., HKEX 02.11., KRX 01.10.; LSE 01.06. `unbelegt` (nur
   nächster Werktag); Mailand Januar 2027 `unbelegt` (Euronext-Kalender 2027 nicht veröffentlicht) — dort und nur
   dort prüft der Wächter „liegt im Folgemonat“ und benennt es so. Alle übrigen Tage nach der letzten Sitzung des
   Monats verlangen das exakte Datum.
2. **Konventionsreferenzen:** CRYPTO 02/2028 (jeder Kalendertag, Schaltjahr, 31 Sitzungen davor) und FOREX 12/2026
   (Mo–Fr, 238 Sitzungen davor, `numpy.busday_count`; Folgemonat Fr 01.01.2027 — Neujahr ist bei FOREX nach der
   Konvention offen) als eigene Listen mit `status: konvention`, gleiche Prüfungen wie die Börsenlisten.
3. **Alle 57 Statusfälle durch Header und Converter:** je (Börse, Jahr) aus der Literaltabelle ein Header (Referenz-
   ticker der Börse, 02.03. des Jahres) und ein Converter-Ergebnis; verlangt wird **genau** das erwartete
   Kennzeichen (belegt: keines; annahme/ungeprueft: der jeweilige Text; CRYPTO/FOREX: die Konvention) und kein
   anderes.

Wächter jetzt 2234 Prüfungen. Mutationstest: „Header ignoriert den Kalenderticker“ war äquivalent (alle Sektor-ETFs
an der NYSE) und ist durch „Korb übergibt keinen Kalenderticker“ ersetzt; Lauf dieser Runde parallel.

## Ausgabevertrag
**Urteil** · **Befunde** (nur neue/offene, P1/P2 mit Datei:Zeile) · **Auflagen**. ≤ 20 Zeilen.
