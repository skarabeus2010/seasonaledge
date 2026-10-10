# Antwort Codex — Ticker schneller laden, Runde 2 (2026-10-10)

Prompt: [2026-10-10_ticker_laden_plan_v2.md](2026-10-10_ticker_laden_plan_v2.md). model: gpt-6.1-sol

**Urteil**

**Die Richtung ist tragfähig; S1 ist noch nicht ausreichend spezifiziert.** Hauptlücken sind überlappende Anforderungen, Abdeckungs- und Frischeregeln sowie die Migration bestehender Verbraucher. S2 braucht einen eindeutigen Fehlervertrag. S3 eignet sich zunächst ausschließlich für den Schattenmodus.

Geprüft: drei neueste Versionseinträge, Plan v2, Runde 1 und relevante Produktionspfade; zusätzlich eine isolierte Gegenprobe am Dekadenzyklus-Code. Nichts geschrieben. Keine eigenen Live-Laufzeitmessungen.

**Antworten**

1. **Reicht S1?** Noch nicht. Rückgaben müssen exakt den angeforderten Bereich und Feldsatz enthalten; intern dürfen sie aus einem größeren Bestand stammen. Abdeckung, TTL, gleichzeitige Erweiterungen und Veröffentlichung nach Fehlern brauchen ausdrückliche Regeln. Unveränderte Kennzahlen müssen an echten Verbrauchern nachgewiesen werden.

2. **Nur ältere Daten nachladen?** Möglich, aber für die erste Umsetzung empfehle ich bei Erweiterungen eine vollständige Neuladung des benötigten Gesamtbestands. Das vereinfacht Feldabdeckung, Korrekturen und Löschungen. Ältere Teilstücke später optimieren, sobald Revision und Zusammenführung zuverlässig geregelt sind. Auch vollständiges paginiertes Nachladen garantiert allein keinen gemeinsamen Datenstand.

3. **Browser-Probe lokal und im Deploy?** Beides ist realistisch, im Deploy auf dem GitHub-Runner mit festgelegten Paket-/Browserversionen und installierten Browserabhängigkeiten. `npx` allein beschreibt diese Voraussetzungen nicht. Lokal bildet `http.server` die nginx-Routen und Header nicht ab; dafür braucht es zusätzliche Einrichtung. [Playwright CI](https://playwright.dev/docs/ci), [Python-Dateiserver](https://docs.python.org/3/library/http.server.html).

4. **Genügen 26 Stunden?** Für produktive Kursdateien nein. Exportalter belegt weder erfolgreiche Kursaktualisierung noch aktuelle Intraday-Werte. Wochenenden, Feiertage und Krypto bleiben unzureichend definiert. Bis zur belastbaren Frischeregel: Schattenmodus, DB bleibt maßgeblich.

5. **Was fehlt sonst?** Begrenzter Memory-Cache, Behandlung alter persistenter Kurseinträge, Abbruch-/Timeoutregeln, Schutz aller verspäteten UI-Antworten, Verbraucherprüfungen und ein Veröffentlichungskonzept für S3.

**Befunde**

1. **Hoch — Rückgabevertrag lässt Zahlenänderungen zu.**  
   [Plan Z. 29](/C:/dev/SeasonalEdge/docs/review_prompts/2026-10-10_ticker_laden_plan_v2.md:29): „Sicht“ muss ausdrücklich `date >= ab` einschließlich Grenztag bedeuten. Eine Vollhistorie als Antwort auf einen begrenzten Aufruf verändert Stichproben. Feldprojektion, Datentypen und Erhalt von `null`/Nullwerten festlegen; fehlende angeforderte Eigenschaften sind kein vollständiges Ergebnis.

2. **Hoch — Promise je Anforderung erfüllt die gemeinsame Ladung nur teilweise.**  
   Feldsatz und Grenze unterscheiden Dashboard-Historie, Score, Radar und Overnight. Diese Anforderungen könnten weiterhin gleichzeitig überlappende Reihen laden. Pro Ticker koordinieren: ausreichende laufende Ladung teilen, sonst Erweiterung einreihen; Feldsätze normalisieren. Langsamere Abschlüsse dürfen einen inzwischen größeren Bestand nicht überschreiben.

3. **Hoch — Abdeckung und TTL sind nicht definiert.**  
   Das früheste vorhandene Kursdatum ist keine Abdeckungsgrenze: Ein ab 1990 vollständig geladener CRWV-Bestand beginnt trotzdem erst 2025. Angeforderte Abdeckung separat speichern, auch bei leeren Ergebnissen. Eine Erweiterung darf ältere vorhandene Daten nicht pauschal um weitere 15 Minuten verjüngen; nach Ablauf den Bestand ersetzen.

4. **Hoch — „Eingefroren oder Kopie“ ist für bestehende Verbraucher zu ungenau.**  
   [Dekadenzyklus Z. 317](/C:/dev/SeasonalEdge/landing/pages/dekadenzyklus.html:317) schreibt in Zeilenobjekte. Gegenprobe: Nur das Array einzufrieren ließ diese Mutation zu; eingefrorene Zeilen verhinderten die bisherige Konvertierung lautlos. Für S1 sind neue Arrays **mit kopierten Zeilenobjekten** der einfachste kompatible Vertrag; `slice()` allein reicht nicht.

5. **Hoch — Bestehende Seiten umgehen weiterhin Frische und Antwortschutz.**  
   Dekaden-, Earnings- und Dividenden-Caches liefern Ergebnisse ohne erneuten Laderaufruf; damit greift dessen TTL nicht. Außerdem hat der [Dashboard-Overnight-Abschluss](/C:/dev/SeasonalEdge/landing/pages/dashboard.html:2199) keine Kennungsprüfung. Migration muss diese Umgehungen beseitigen und auch Nebenabrufe gegen verspätetes Rendern schützen.

6. **Mittel — Memory-Cache braucht Größenbegrenzung und klaren Geltungsbereich.**  
   15 Minuten TTL begrenzen den Speicherverbrauch ohne aktive Verdrängung nicht. Budget/LRU festlegen. Der Bestand gilt pro Dokument; Navigation zur zweiten Seite startet einen neuen Memory-Cache. Der bisherige seitenübergreifende localStorage-Treffer entfällt und muss in S0 ausdrücklich bewertet werden.

7. **Mittel — S2 widerspricht sich beim fehlgeschlagenen Speichern.**  
   Erst Einträge verdrängen und danach `false` zurückgeben kann andere Treffer bereits zerstört haben. Übergroße Einträge vorab ablehnen, ausschließlich eigene Cache-Einträge berücksichtigen und Nicht-Quota-Fehler ohne Verdrängung behandeln. Im aktuellen Bestand nutzen nur die Kurslader `SA.cache.get/set`; nach S1 sind keine weiteren Nutzer belegt. Alte `prices`-Einträge gezielt entwerten; S2 gegebenenfalls vereinfachen.

8. **Hoch — Die Abnahme beweist bisher nicht die Verbraucherkompatibilität.**  
   Der tatsächliche URL-Ausdruck ist beispielsweise `fetch(SA.supabase.url + '/rest/v1/prices?' …)`; der angekündigte Suchtext darf das nicht verfehlen. Auch API-Helfer und alte Ladernamen erfassen. Bestehende Radar-Proben stubben `fetchAllPrices` und benötigen Anpassungen. Ergänzen: konkurrierende Feld-/Bereichsanfragen, Abschlussreihenfolge, TTL, leere Abdeckung, fehlerhafte Cursor und konkrete Kennzahlen aller migrierten Seiten.

9. **Hoch, vor S3 — Versetzte Timer verhindern keine Überlappung.**  
   Nightly startet um `:45`, Intraday um `:17`; Nightly darf [90 Minuten laufen](/C:/dev/SeasonalEdge/deploy/systemd/sa-nightly.service:16). Unterschiedliche Units schließen einander nicht aus. „Im selben Prozess nach den Schreibern“ schützt nur vor eigenen Schreibvorgängen. Alle relevanten Schreiber und Exporte brauchen gemeinsame Koordination oder einen nachprüfbaren Snapshotvertrag. Separate PostgREST-Anfragen teilen keine Transaktion. [PostgREST-Transaktionen](https://docs.postgrest.org/en/stable/references/transactions.html).

10. **Hoch, vor S3 — Frischer Export kann alte Kurse legitimieren.**  
    Scheitert ein Ticker-Update, kann der Export vorhandene alte DB-Zeilen mit neuem `stand_utc` veröffentlichen. Zusätzlich akzeptieren 26 Stunden mehrere ausgefallene Intraday-Läufe. Erfolgreichen Datenstand und erwarteten Aktualisierungsrhythmus pro Ticker nachweisen; Exportfehler dürfen den alten Stand nicht als frisch bestätigen.

11. **Mittel — S0 benötigt einen reproduzierbaren Seitenaufbau.**  
    Öffentliche Routen, Supabase-Konfiguration und Watchlist-Anmeldung/Testbestand fehlen im Messvertrag. Vorher/Nachher müssen dieselben Daten verwenden; Browsercache und Seitencaches getrennt kontrollieren. Renderabschluss, Mobile-Profil und Leistungsziel festlegen. Live-Performancewerte eignen sich als Messbericht; deterministische Funktionsproben als Deploy-Gate.

**Auflagen vor S1**

- Vertrag festschreiben: inklusive Bereichsgrenze, Feldprojektion, kopierte Zeilen, Abdeckungsmetadaten, TTL und begrenzter Cache.
- Einen Koordinator je Ticker definieren; Gesamtbestand zunächst vollständig nachladen und erst nach Erfolg veröffentlichen. Fehler lassen die Erweiterung ablehnen.
- Migrationstabelle um lokale Ergebnis-Caches, Nebenabrufe, Kennungsprüfungen und tatsächliche Script-Einbindung ergänzen; bestehende Score-/Radar-Regeln ausdrücklich erhalten.
- Produktionsproben um die genannten Konkurrenz-, Fehler- und Verbraucherfälle erweitern; Sollwerte unabhängig bestimmen. Mutationstests mit gültigem Anker und `_atomar_schreiben`, Ausnahmen zählen nicht als Nachweis.
- S0 reproduzierbar festschreiben und S2 vereinfachen oder seinen Verdrängungsvertrag präzisieren. Die offenen S3-Fragen können getrennt bearbeitet werden.
