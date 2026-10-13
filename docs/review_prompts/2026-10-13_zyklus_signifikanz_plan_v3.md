# Entwurf v3: Präsidentenzyklus-Signifikanz + Jahresende — Runde 3 (Plan)

Read-only, Repo `C:\dev\Seasonaledge`, Stand `origin/master` (inzwischen `1e84da2`: Doppelklick/rechte Achse auf
`/jahreszyklus` + Deploy-Vorlage — nicht Gegenstand). Grundlage: v2
(`docs/review_prompts/2026-10-13_zyklus_signifikanz_plan_v2.md`) und deine Antwort
(`..._plan_v2_antwort.md`). Deutsch, echte Umlaute, Datei:Zeile, am Ende **FREIGABE (Plan): ja/nein**.

v2 gilt weiter; hier nur die Änderungen.

## B6 (Freigabeblocker) — neu formuliert

Jede Heatmap-Zelle (Seite `jahreszyklus.html:705`, gleiche Regel im Blog) braucht **beides**:
1. `yearCovers(yd, monatsEndeSlot, jahr, stichtagJahr)` — Datenabdeckung bis zum Monatsende.
2. Im laufenden Jahr zusätzlich: der Kalendermonat ist beendet, verglichen über **(Jahr, Monat)** gegen den Stichtag
   (`jahr < stichtag.jahr || monat < stichtag.monat`), nicht über `MONTH_BOUNDS`-Slots (nicht schaltjahrgenau).
Zukünftige Jahre bleiben leer. Leere Zelle statt 0 %.
Wächter: laufendes Jahr mit Daten bis 30.06. bei Stichtag 13.10. → Juli–September leer; Stichtag 29.02. →
Februar leer, Stichtag 01.03. → Februar kalenderseitig abgeschlossen (Abdeckung muss trotzdem bestehen);
zukünftiges Jahr leer.

## Präzisierungen aus deiner Antwort

- **B1/B2:** Im `yearCovers` steht der Zweig `endDoy ≥ 365` (Jahresprüfung) **vor** jedem `lad >= endDoy`-Erfolg.
- **B3:** Feste Kartenreihenfolge des Zyklus hat Vorrang vor der Relevanzsortierung (`significance.js:122`);
  `zu_wenig` nur innerhalb von Seiten ohne feste Reihenfolge ans Ende.
- **B4:** `renderSection(…, opts)` bekommt einen optionalen vierten Parameter; Mindestzahl in der grauen Karte aus
  `opts.mindestN`, nicht fest. Einheit „abgeschlossene Jahre" **nur im Zykluszweig**; Monate/Quartale behalten
  „Beobachtungen". Neue Texte über den vorhandenen i18n-Weg von `significance.js` (`SA.i18n.t` + de/en.json,
  `_JSON_VER` erhöhen). Overnight: graue Nullgruppen als sichtbare Änderung in der Doku vermerkt.
- **B5:** beide Seiten (`jahreszyklus.html:577`, `risikozyklus.html:319`) rufen die gemeinsame Interpolation
  (`SA.seasonal._interpolateTo365`) statt der Kopie; beide EN-Seiten in der Prüfung.
- **B8:** Monatsmittel-Schleife `.values()` → `.items()` (`blog_builder.py:684`).
- **Stichtag durchreichen:** `periodStats(…, stichtag)` (Aufrufe 1401/1443/1464/1503), `calculate_period_stats(…,
  stichtag_jahr=None)` (Standard heute, Wächter injiziert, `verify_seasonal_twins.py:460/474/484`), Blog-Funktionen
  nutzen ihr vorhandenes `current_year` (`blog_builder.py:586/672`). Die Seite liest den Stichtag einmal und reicht ihn
  durch. `yearEndRef`/`year_end_reference` samt Imports und alter Wächter-/Mutationsreferenzen entfernt; Fixtures
  unter `scripts/fixtures/kurse_vorher` sind keine Aufrufer.
- **B9 Gate:** Der Wirkungsbericht entsteht **vor dem Push** nach master (Push = Deploy), auf dem Server mit dem
  neuen Code in einem Temp-Verzeichnis im Container (Muster OPTIONS.md). Er nennt Code-Stand, Datenstand, Stichtag,
  Zeitraum, Filter; je Gruppe die aufgenommenen **Jahre**, nicht nur n; alle veröffentlichten Blog-Konfigurationen
  DE+EN; L2, Schaltjahr-Faltung und Heatmap-Filter getrennt zugeordnet; keine Renderfehler. Ändern sich
  veröffentlichte Zahlen: Text nachziehen + `updated:`; das entscheidet der Nutzer nach dem Bericht. Ändert sich die
  Vergleichsgrundlage danach wesentlich, wird der Bericht erneuert.
- **Deploy-Vorlage:** `scripts/fixtures/kurse_vorher/pages/jahreszyklus.html` bekommt die fachfremden Änderungen
  dieser Arbeit, damit `verify_seiten_kurse` nicht an „Anzeige gleich" scheitert — **oder**, falls die Signifikanz-
  bzw. Heatmap-Anzeige sich beabsichtigt ändert, werden dieselben Änderungen dort nachgezogen (die Vorlage soll nur
  die Lader-Umstellung vom alten Stand unterscheiden). Bitte prüfen, ob das so stimmt.

## Prüffragen
1. Ist B6 jetzt vollständig?
2. Fehlt sonst etwas für die Freigabe?
