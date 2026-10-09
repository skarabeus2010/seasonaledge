# Plan v3: Saison-Score und Anomalie-Radar — Ergänzungen zu v2

Repo `C:\dev\Seasonaledge`. Nur lesen. v2: `..._plan_v2.md`, deine Antwort `..._plan_antwort2.md` (4 Befunde).
Unten nur die Änderungen gegenüber v2. Antwort auf Deutsch, je Befund Schwere + Abschnitt + Fall + Änderung; am Ende
genau eine Zeile `FREIGABE: ja` oder `FREIGABE: nein`.

## Zu Befund 1 — Marktklasse im Funktionsvertrag
Beide Kerne bekommen den **Ticker als Pflichtparameter**: JS `SA.decadeCompute.anomalie(rows, ticker, {as_of})`,
`SA.saisonScore.berechne(rows, ticker, {as_of})`; Python `anomalie(daten, closes, ticker, as_of=None)`,
`saison_score(daten, closes, ticker, as_of=None)`. Eine gemeinsame, in beiden Sprachen wortgleiche Zuordnung
`marktklasse(ticker)`: Endung `-USD` → `krypto` (T = 1), Endung `=X` → `forex` (T = 3), sonst → `boerse` (T = 5);
leerer/fehlender Ticker → Fehler (kein stiller Standard). Unbekannte Suffixe fallen bewusst unter `boerse` (die
großzügigere Toleranz verwirft keine echten Börsenreihen; dokumentiert). Alle Aufrufer (Dashboard, Watchlist,
KI-Seite, sieben Radar-Seiten, Nightly/Full-Scanner, D5) übergeben den Ticker. Test: identische Datumsreihe mit
zweitägiger Lücke → `krypto` verwirft, `boerse` akzeptiert; Python = JS.

## Zu Befund 2 — Zeitzone im Jahreskurvenbau + Tag 366
- **`buildYearData`/`buildExtendedYearData` in `landing/js/seasonal-compute.js` werden auf UTC umgestellt**
  (Jahr, Tagesnummer und Jahresbeginn aus dem ISO-Datum per `Date.UTC`, nicht `getFullYear()`/lokaler Jahresanfang).
  Das ist ein **seitenweiter Fehler** (betrifft alle Saisonseiten für Leser außerhalb UTC/MEZ, z. B. New York) und
  wird als eigener Schritt **vor** C gebaut, mit eigenem Review: Zwillingswächter `verify_seasonal_twins.py` läuft
  zusätzlich unter `TZ=America/New_York`, `TZ=Asia/Tokyo` und `TZ=UTC` (node mit gesetzter Umgebungsvariable) und
  verlangt identische Ausgaben; Mutationstest „lokales Jahr statt UTC" muss reißen. Zusätzlich prüfe ich mit grep,
  welche anderen Stellen Datumsstrings über `new Date(...)` + lokale Getter auswerten, und liste sie (nicht alle
  im selben Schritt beheben — nur die, die in Score/Radar eingehen).
- **Tag 366:** Matching-Präfix d = **min(Tagesnummer(as_of), 365)**; die bestehende Faltung (31.12. im Schaltjahr auf
  Slot 365) bleibt. Tests: as_of = 30.12. und 31.12. eines Schaltjahres, Python = JS.

## Zu Befund 3 — D5 auswertbares Universum
Vor dem Lauf im Protokoll festgelegt:
- Eine Reihe ist **auswertbar**, wenn sie in Abschnitt A mindestens **100** Bewertungstage mit Score ≠ null und
  ausgereiftem Ziel hat, verteilt auf mindestens **8** verschiedene Kalenderjahre, und weder Score noch Ziel konstant
  sind. Nach Datenlage fallen damit u. a. ETHA, IBIT, MAGS (zu jung) und vermutlich XLC heraus — das wird nicht
  vorab angepasst, sondern aus der Regel ermittelt und berichtet.
- Das auswertbare Universum wird **einmal** auf den Originaldaten bestimmt und gilt dann fest für alle Ziehungen.
- **Bootstrap:** je Ziehung dieselben Kalenderjahre (mit Zurücklegen) für alle Reihen; Spearman je Reihe auf den
  gezogenen Beobachtungen (mehrfach gezogene Jahre zählen mehrfach). Ist in einer Ziehung eine Reihe undefiniert
  (< 10 Beobachtungen oder konstant), wird die **ganze Ziehung verworfen und gezählt** — kein `nanmean`. Liegt der
  Verwerfungsanteil über **5 %**, gilt das Ergebnis als „nicht auswertbar" und wird so berichtet.
- **Gepaarter Vergleich** Score vs. 5·(B1+B2): exakt dieselben Bewertungstage (Schnittmenge, in der beide definiert
  sind), dieselben Ziehungen.
- Berichtet werden: auswertbares Universum, Ausschlüsse mit Grund, Fallzahl je Reihe, Verwerfungsanteil.

## Zu Befund 4 — unveränderliches prospektives Protokoll
Neue Tabelle `saison_score_protokoll` (in derselben Migration wie D3): `protokoll_id` (Identität), `methode`,
`code_version` (Git-Kurz-SHA des Containers, im Image hinterlegt), `erstellt_am`, `ticker`, `as_of`, `kurse_bis`,
`kurse_hash` (wie bei der Stress-Ampel), `status`, `grund`, `score`, `bausteine`. **Nur INSERT**: eindeutiger
Schlüssel `(methode, ticker, as_of)`, Schreiben mit `ON CONFLICT DO NOTHING` → **der erste Lauf je Ticker und as_of
zählt**, Wiederholungsläufe ändern das Protokoll nicht (ein abweichender Wiederholungswert wird im App-Log gemeldet,
nicht überschrieben). RLS: kein Zugriff für `anon`/`authenticated`, Schreiben nur `service_role`; kein UPDATE/DELETE-
Recht für die Rolle des Nightly. Die Scanner-Anzeige liest weiter aus `scanner_results`; die Bestätigungsauswertung
(frühestens 2027-10) liest nur aus dem Protokoll.

## Reihenfolge
**U** (UTC-Korrektur Jahreskurvenbau) → C → D1/D2 → D5 → D3 (Migration inkl. Protokolltabelle) → D4.
