**Urteil**
Noch keine Entwurfsfreigabe. Die Aufteilung V1c-1/2/3 ist sinnvoll; V1c-1 braucht die folgenden Präzisierungen. Eine vollständige B4-Abnahme erfolgt erst mit Produktterminen, Halbtagen und Verbrauchern.

**Befunde**

- **P1 – Kennungskollision (Entwurf Z. 29–31):** Feiertag und eigenes Ersatzereignis besitzen dieselbe Börse, Regel und nominales Datum. Entweder genau ein Ereignis je Regeltermin oder eine stabile Rollenkennung plus expliziter Verknüpfung vorsehen.
- **P1 – Bestandsschutz widersprüchlich (Z. 36–39):** `get_holidays` enthält heute auch Wochenenddaten (`shared/exchange_holidays.py:495`, etwa XETRA Weihnachten 2021). Der geplante Mo–Fr-Filter verändert die API und den Snapshot trotz unveränderter Sitzungen.
- **P1 – Quellenarbeit bereits in V1c-1 nötig:** HKEX/KRX enthalten reine Datumstabellen, teils ursprünglich aus Kurslücken (`shared/exchange_holidays.py:414–453`). Regel, Art, nominaler Termin und Name lassen sich daraus nicht verlässlich gewinnen; Raten verletzt B4.10.
- **P1 – Bundle unvollständig (Z. 40–42):** Quelle und Kalenderstatus fehlen im Transportvertrag; die Rekonstruktion der Ereigniskennung ist undefiniert. `wirksam(MMDD)` verlangt außerdem eine eindeutige Jahreszuordnung bei jahresübergreifenden Ersatzterminen.
- **P2 – Versionierung unklar (Z. 34/42):** Der heutige Bundlehash umfasst mehr als Schließungsdaten. Separate Inhalts-/Kalenderversionen und deren Hash-Eingänge definieren; Ereignisversion im eigenen Hash vermeiden.
- **P2 – Abnahmeumfang fehlt:** B4.5–7 und B4.10 sind mit unveränderten Verbrauchern noch offen. Gleiche Datenmengen und Python=JS beweisen zudem keine korrekte historische Ereignisidentität.

**Antworten 1–4**

1. Vorschlag tragfähig: verschobener Regeltermin als `ersatztag`, zusätzlicher Tag als `sonderschliessung`. Welcher Jubiläumstag welche Rolle hat, muss je Jahr belegt sein; der alte Kommentar genügt nicht.
2. Wochenendereignis darf erscheinen. Schließungszahl separat als Menge eindeutiger wirksamer Vollschließungen auf sonst offenen Tagen bilden; Halbtage ausschließen.
3. Snapshot genügt für die Mengeninvariante. Zusätzlich tatsächliche Offenheit und alle vier Handelstagnummern über 1885–2100 vergleichen: Der Umbau verändert den Produktionspfad.
4. `halbtage: ungeprüft` genügt als Zwischenstatus, nicht als vollständige B4.2-Erfüllung. Leere Halbtaglisten dürfen keine belegte Abwesenheit behaupten; modellierte Halbtage müssen offen bleiben.

**Auflagen**

- Ereignisidentität, Ersatzbezug, mehrtägige Ereignisse, Jahreszuordnung und NASDAQ-Alias verbindlich festlegen.
- Bestehende Feiertags-API erhalten; wirksame Schließungszahlen als separate Projektion definieren.
- Quellen und Status je Ereignis transportieren; ungeklärte Tabellenidentitäten ausdrücklich als Abnahmelücke behandeln.
- Unabhängige Sollfälle für LSE-Zuordnung, TSE-Ersatz-/Brückentage, Mehrfachereignisse derselben Börse am selben Datum und Jahresgrenzen ergänzen.
- Prüfmatrix B4.1–10 den Teilphasen zuordnen; vollständige Objektgleichheit Python/JS prüfen.
- Nur lesend geprüft; keine Dateien geschrieben und keine Tests ausgeführt.
