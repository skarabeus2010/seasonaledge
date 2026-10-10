codex
**Urteil: mit Auflagen.** Seitenmigration erst nach Erfüllung der Auflagen. Vorhandene Probe: **62/62 grün**. Keine Dateien geschrieben.

**Befunde**

1. **P2 – HTTP-Datum in `Retry-After` ignoriert.** [kurse.js:143](C:/dev/SeasonalEdge/landing/js/kurse.js:143): `parseInt` versteht nur Sekunden. Ein gültiges zukünftiges HTTP-Datum führt zur kurzen Standardwartezeit statt zur verlangten Verzögerung. Zusatzprobe bestätigt; beide Formate sind zulässig. [RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html#name-retry-after)

2. **P2 – Poolgrenze bei ausbleibendem Abbruch verletzt.** [kurse.js:123](C:/dev/SeasonalEdge/landing/js/kurse.js:123): Nach Timeout gibt `Promise.race` den Platz frei, obwohl der Fetch noch offen sein kann. Im vorgesehenen Pfad ohne `AbortController`: **8 offene Fetches bei Poolzähler 0** nach den Ablehnungen. Auch ein Fetch, der den Abbruch ignoriert, ermöglicht diese Überschreitung. Verspätete Ergebnisse werden allerdings nicht veröffentlicht.

3. **P2 – Probe kann mehrere Vertragsbrüche nicht erkennen.** [probe_kurse.js:52](C:/dev/SeasonalEdge/scripts/js/probe_kurse.js:52), insbesondere Z. 72, 112 und 170: Der Stub ignoriert Sortierung und Request-Header; der Retry-Test prüft keine Wartezeit. Drei ausschließlich im Speicher geprüfte Mutationen bleiben jeweils **62/62 grün**: `order=date.asc` entfernt, `Prefer: count=exact` ergänzt, `Retry-After` vollständig ignoriert.

**Auflagen**

- Beide `Retry-After`-Formate auswerten; positive Sekundenwerte und HTTP-Datum mit kontrollierter Uhr und nachgewiesener Wartezeit prüfen.
- Poolplätze bis zum tatsächlichen Transportabschluss halten; den Pfad ohne Abbruchunterstützung entsprechend behandeln. Verspätete Antworten und Poolgrenze gemeinsam testen.
- Request-Vertrag einschließlich Sortierung, Limit und Headern prüfen; die drei genannten Mutationen müssen gezielt rot werden.
- Dauerhafte Fälle für JSON-Fehler, scheiternde wartende Ladung, Übergangsanfragen und TTL-Ablauf eines **vorhandenen Bestands** ergänzen. Der bisherige TTL-Fall startet ohne Bestand.

Zusatzproben bestätigen korrekte Bedarfssichten und Übergaben, Ablehnung beider scheiternden Ladungen sowie unveränderten Cache nach verspäteter Antwort. Der Doppelfilter wird korrekt mit UND verknüpft. [PostgREST-Dokumentation](https://docs.postgrest.org/en/stable/references/api/tables_views.html#logical-operators)
