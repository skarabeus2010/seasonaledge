# Paket 2 (P1a K2+K5): Kalenderstatus und Nummernfunktion — Code-Review Runde 1

Plan: [v3](2026-10-10_xetra_tdoy_plan_v3.md) (P1.3) · [v4](2026-10-10_xetra_tdoy_plan_v4.md) (K2, K5) ·
Auflagen: [Antwort 3](2026-10-10_xetra_tdoy_plan_antwort3.md) Frage 3, [Antwort 4](2026-10-10_xetra_tdoy_plan_antwort4.md)
A2 + Auflagen 6–8. Paket 1 (K1) ist committet (`4d88ac6`).

<task>
Reine Ergänzungen, kein bestehender Aufrufer ändert sich: `kalender_status()` + `KALENDER_GUELTIG`,
`boerse_normalisieren()`, `handelstag_nummern()` am Ende von `shared/exchange_holidays.py`, dazu
`scripts/verify_handelstag_nummern.py` und `..._mutation.py`. Prüfe `git diff` + die zwei neuen Dateien.
Read-only.
</task>

## Umgesetzt
- **K5 Vertrag** wie in der Docstring von `handelstag_nummern`: Börse zuerst geprüft (auch bei leerer
  Eingabe), NASDAQ → NYSE, Groß/Klein normalisiert; nur `date` (kein `datetime`, `type(x) is date`) oder
  `[0-9]{4}-[0-9]{2}-[0-9]{2}` per `fullmatch`; Rechenbereich 1885–2100, sonst `ValueError`; Reihenfolge
  und Duplikate erhalten; Periodensummen über den ganzen Monat/das ganze Jahr; geschlossene Tage: Vorwärtszahl
  des letzten Handelstags davor in der Periode (sonst 0), Rückwärtszahlen `None`. Ergebnis `Nummer` ist ein
  unveränderliches Tupel mit Feldnamen; Cache je (Börse, Jahr) mit unveränderlichen Werten.
- **K2** `KALENDER_GUELTIG` = Standardstatus + Intervalle je Börse, im Wesentlichen dein A2-Vorschlag;
  NYSE 1971–2028 belegt (die acht WAHLEN-Fälle sind seit Paket 1 im gemeinsamen Kalender), XETRA 2002–2026
  belegt / 2001 Annahme / vor 2001 ungeprüft, HKEX ungeprüft außer 2016–2025 Annahme und 2026 belegt,
  KRX 2016–2026 Annahme. Rechnen ist unabhängig vom Status.
- **Wächter** 74 Prüfungen: [Arithmetik] `numpy.busday_count` (Ende `d+1`, rückwärts bis exklusives
  Periodenende) über die Produktionsfeiertage, jede Börse, jeder Tag 1950–2035, alle fünf Felder;
  [Sollkalender] wörtliche Schließtage XETRA 2012/2018, NYSE 2025, LSE 2022, TSE 2021, mit numpy gezählt und
  für jeden Tag des Jahres verglichen; [Vertrag] Validierung, Reihenfolge/Duplikate, geschlossene Tage,
  Jahressummen, Unveränderlichkeit, Cache je Börse; [Status]. Laufzeit 3,6 s.
- **Mutationstest** 12/12, zwei Läufe identisch, Gegenproben 2/2. Zwei Mutationen, die zuerst nur eine
  Ausnahme auslösten, sind jetzt verhaltensändernd formuliert (datetime still umgewandelt; NASDAQ → LSE).
- `verify_handelstag_nummern.py` braucht numpy und steht deshalb **noch nicht** im Deploy-Gate (Runner ohne
  numpy). Vorschlag: in Paket 3 mit `pip install numpy` ins Gate.

## Fokusfragen
1. Vertrag vollständig umgesetzt? Insbesondere Monats-/Jahresgrenzen, Schaltjahre, KRX/HKEX-Tabellenjahre,
   Krypto 31/366.
2. Sind die Sollkalender-Listen korrekt und vollständig (alle Werktags-Schließtage des Jahres)?
3. Ist die numpy-Referenz an einer Stelle zu nah an der Produktion (z. B. gleiche Wochenmaske-Annahme)?
4. `KALENDER_GUELTIG`: Einwände gegen einzelne Intervalle?
5. Fehlt eine wirksame Mutation?

## Ausgabevertrag
**Urteil** (Freigabe / Freigabe mit Auflagen / keine Freigabe) · **Befunde** (Datei:Zeile, Beleg) ·
**Antworten** (je ≤ 6 Zeilen). ≤ 70 Zeilen.
