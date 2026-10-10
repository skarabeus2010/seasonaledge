# P1b isoliert (Weg A): JS-Börsenkalender — Code-Review Runde 1

Plan: [v6](2026-10-10_xetra_tdoy_plan_v6.md) · deine Auflagen: [Antwort 6](2026-10-10_xetra_tdoy_plan_antwort6.md).
P1a ist deployt (`8f976a0`, Gates grün, im Container nachgeprüft; erster Intraday-Lauf 12:17 UTC Exit 0).

<task>
Prüfe den Code (neue Dateien, nichts committet): `scripts/boersenkalender/api.js`, `scripts/build_boersenkalender_js.py`,
erzeugt `landing/js/boersenkalender.js`, `scripts/js/probe_boersenkalender.js`, `scripts/verify_boersenkalender_js.py`,
`scripts/verify_boersenkalender_js_mutation.py`, `.gitattributes`, Diff `.github/workflows/deploy.yml`. Read-only.
</task>

## Umsetzung
- **Bundle** `landing/js/boersenkalender.js` = Daten + API, erzeugt; 136 498 B roh / 18 239 B gzip; LF
  (`.gitattributes eol=lf` für Bundle und API-Quelle). Namensraum `SA.boersenkalender` (eingefroren).
  **Keine Seite bindet es ein**; `holidays.js` und alle Seiten unverändert.
- **Abweichung vom Plan v6, bewusst — bitte beurteilen:** Schema 1 trägt **keine** `art` je Schließung.
  Deine Runde 6 sagte, `{d, art}` reiche für den Ereignisvergleich ohnehin nicht, und eine vollständige
  Klassifikation (Feiertag / Einmalschließung / regelmäßige Börsenschließung ohne Feiertag, Überschneidungen)
  braucht erst P4. Statt einer halben Einteilung: `schliessungen[börse][jahr] = "MMDDMMDD…"` (= Python
  `get_holidays`, sortiert, inkl. Wochenend-Einträge wie in Python) und ein **reservierter, leerer**
  Schlüssel `ereignisse: {}` für Schema 2 (stabile Kennung, Ereignisdatum, Bezug zur Schließung). Die API
  prüft `schema === 1` und wirft sonst.
- `version` = sha256 über die kanonische JSON-Serialisierung aller Nutzdaten (sortierte Schlüssel, ohne
  `version`). `pruefdatum`, `von`/`bis` 1885–2100, `woche`, `status` (aus `KALENDER_GUELTIG`), `ticker`
  (370, Schlüssel in Großschreibung, Wert = Python-Ergebnis), `suffix`.
- **API** zeitzonenfrei (nur ganze Zahlen, Wochentag über Tageszähler, kein `Date`): `boerse`,
  `istHandelstag`, `nummern` (Objekte eingefroren; gleiche Felder/Fehler wie Python), `nterHandelstag`,
  `letzterHandelstag`, `nterHandelstagImJahr` (Position ganze Zahl ≥ 1, fehlt → `null`),
  `naechsterHandelstag` (**ab einschließlich**, über Jahresgrenzen, Datenende → `throw`),
  `schliessungen` (neue Liste je Aufruf), `status`. Validierung vor jeder Abkürzung (Börse, Typ, strenges ISO,
  gültiges Datum, Bereich), Alias NASDAQ → NYSE, kein `'NONE'`.
- **Wächter** 58 Prüfungen, ~45 s: [Aktuell] Datei == Neuerzeugung; [Python] `istHandelstag` und `nummern`
  (5 Felder) für 13 Börsen × alle 78 893 Tage 1885–2100; [NumPy] dieselben Nummern gegen
  `numpy.busday_count` (Feiertage aus der Produktion — Arithmetik-Referenz); [Zeitzone] UTC, Berlin,
  New York, Apia, Kiritimati, Adak, je eigener node-Prozess, `process.env.TZ` vor jeder Date-Nutzung,
  Offsets Jan/Jul nachgewiesen, Ergebnisse == UTC (Hashvergleich); [API] Termine für 15 Jahre × 5 Monate ×
  13 Börsen inkl. fehlender Position, nächster Handelstag für jeden Tag 2019/2020/2099 × 13 Börsen,
  `schliessungen`, `status` (jedes 7. Jahr + Grenzjahre); [Ticker] alle 370 + Regel-/Fehlerfälle;
  [Validierung] 22 Fehlerfälle; [Sollfall] die 86 belegten Fälle; [Isolation] kein Verweis unter `landing/`.
  Mutationstest 10/10 (zweiter Lauf läuft), Gegenproben 2/2.
- **Deploy-Gate**: `build_boersenkalender_js.py --pruefen` (Arbeitsbaum **und** HEAD byteweise) +
  `verify_boersenkalender_js.py`, nach `setup-python` 3.12 und numpy; node ist auf dem Runner vorhanden.

## Fokusfragen
1. Ist der Verzicht auf `art` in Schema 1 vertretbar, und reicht `ereignisse: {}` + Schemaprüfung als
   Erweiterungsvertrag für P4?
2. API: Weicht irgendein Verhalten von Python ab (Validierungsreihenfolge, `.F`-Randfall, Groß/Klein,
   Duplikate/Reihenfolge, Schaltjahre, 1885/2100)?
3. Wächter: Kann er trotz Fehler grün sein (z. B. Hashvergleich der Zonen, `get()` auf den ersten
   Treffer, Isolation nur `.html/.js/.json`)? Fehlt eine Mutation?
4. Deploy: Laufzeit und Abhängigkeiten auf dem Runner (node-Version, numpy) tragfähig? Liefert nginx die
   neue Datei aus, ohne dass sie stört?

## Ausgabevertrag
**Urteil** (Freigabe / mit Auflagen / keine) · **Befunde** (Datei:Zeile, Beleg) · **Antworten** (je ≤ 6 Zeilen). ≤ 70 Zeilen.
