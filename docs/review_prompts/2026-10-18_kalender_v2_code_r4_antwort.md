# Kalender V2 — Antwort Codex auf Code Runde 4 (2026-10-18)

**Urteil:** Noch keine Freigabe für V2. Der Schalttag-Befund ist behoben; der unabhängige Monatsüberlauf bleibt unvollständig geprüft.

**Befunde**
- **P2 – Neue Nachfolgerreferenzen werden nie verwendet:** [verify_holidays_fassade.py:354](C:/dev/SeasonalEdge/scripts/verify_holidays_fassade.py:354) liest sie nur nach der letzten offenen Sitzung innerhalb des Referenzmonats. Mailand November und LSE September enden jeweils offen; damit entfällt gerade die zuvor beanstandete Überlaufprüfung. Gegenprobe ausschließlich im Speicher: Beide Nachfolger auf `2099-12-31` gesetzt, trotzdem **1.757/1.757 Monatsprüfungen grün**.

**Auflagen**
- Für beide Börsen einen Referenzmonat mit geschlossenem Monatsende wählen und den exakten Übergang gegen die belegte Folgesitzung prüfen.
- Nachweis dieser Runde: **1.757 Monatsprüfungen einschließlich 29.02.2028 und 20 lesende Einbindungsprüfungen bestanden**. Gesamtlauf nicht bestätigt; keine Mutationstests ausgeführt, keine Projektdateien geändert.
