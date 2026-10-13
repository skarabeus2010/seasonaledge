# Entwurf v2: Präsidentenzyklus-Signifikanz + Jahresende — Runde 2 (Plan)

Read-only, Repo `C:\dev\Seasonaledge`, Stand `origin/master` (inzwischen `50a48c4`: rechte Y-Achse im Hauptchart von
`/jahreszyklus` — nicht Gegenstand, berührt aber dieselbe Datei). Deine Runde 1:
`docs/review_prompts/2026-10-13_zyklus_signifikanz_plan_antwort1.md` (9 Befunde, Plan-Freigabe nein).
Deutsch, echte Umlaute, Datei:Zeile, am Ende **FREIGABE (Plan): ja/nein**.

## Änderungen gegenüber v1 (je Befund)

**B1/B2 — Jahresende mit ausdrücklicher Jahresprüfung.** Neue Signatur in beiden Zwillingen:
`yearCovers(yd, endDoy, jahr, stichtagJahr)` / `year_covers(yd, end_day, jahr, stichtag_jahr)`.
- `endDoy < 365` (Monat/Quartal vor Jahresende): wie bisher `last_actual_day ≥ endDoy` (damit zählen abgeschlossene
  Monate des laufenden Jahres weiter).
- `endDoy ≥ 365` (Periode bis Jahresende): **nur wenn `jahr < stichtagJahr`** UND `last_actual_day ≥ 359`.
  Laufendes und zukünftiges Jahr nie — unabhängig von anderen Jahren.
- `yearEndRef`/`year_end_reference` entfallen; die Entscheidung über ein Jahr hängt nicht mehr von anderen Jahren ab.
- 359 ausdrücklich als **Toleranzentscheidung** dokumentiert (Restrisiko: Datenende ab 25.12. bzw. 24.12. im Schaltjahr
  gilt als Jahresende; IPO-Teiljahre und innere Lücken werden davon nicht erkannt — wie heute). Kalenderansatz
  bewusst zurückgestellt (V4 des Kalender-Umbaus führt Börsenkalender je Ticker ohnehin ein; dort nachziehen).
- `stichtagJahr` wird übergeben (Seite: `new Date().getFullYear()`, Wächter: fest injiziert), nicht intern gelesen.

**B3 — vollständige Gruppen.** Zyklus-Zweig in `JZ.renderSignificance` legt **immer** alle vier Gruppen an (auch
leere Arrays), feste Reihenfolge Post-Election, Midterm, Pre-Election, Election Year. Die Vorfilter `rets.length<3`
und `Object.keys(groups).length<4 → 'Sorry'` entfallen.

**B4 — Aufrufer.** `runSignificanceTest(groups, testValue, opts)` gibt Gruppen unter `opts.mindestN` (Standard 5)
**nicht mehr still weg**, sondern als `{name, n, zu_wenig:true}` zurück. `renderSection` zeichnet sie als graue Karte:
Name · „Nicht ausgewertet“ · „n Beobachtungen · mindestens 5 erforderlich“ (Einheit über `opts.einheit`, Standard
„Beobachtungen“; /jahreszyklus übergibt „abgeschlossene Jahre“). Kein Tacho, kein t/p, keine Rendite, kein
„nicht signifikant“. Statuszweig vor jeder Zahlformatierung; Relevanzsortierung stellt `zu_wenig` ans Ende.
**Lokale Vorfilter der anderen neun Seiten bleiben unverändert** (feiertage n<5, monatswechsel/mondphasen,
opex/vixpiration, zentralbanken <10, plain-vanilla <10, wochentage) — ausdrücklich als bestehende Anzeigeentscheidung
belassen und hier dokumentiert; dort ändert sich nur, dass eine Gruppe, die den Test erreicht und unter 5 liegt, jetzt
grau statt unsichtbar erscheint. Bitte prüfen, ob auf einer dieser Seiten damit eine graue Karte entsteht, die
dort keinen Sinn ergibt.

**B5 — Seiten-Builder Schaltjahr.** `buildExtendedYearData` in `jahreszyklus.html` (und, falls dieselbe Kopie, in
`risikozyklus.html` — bitte prüfen) bekommt die Tag-366-Faltung wie `SA.seasonal._interpolateTo365`; bevorzugt durch
Aufruf der gemeinsamen Interpolation statt eigener Kopie. EN-Fassung wird aus DE gebaut (`landing/build_en.py`).

**B6 — Seiten-Heatmap.** Nur abgeschlossene Monate: vergangene Jahre über `yearCovers(yd, monatsEnde, jahr, stichtag)`,
laufendes Jahr nur Monate mit Monatsende < heute. Leere Zellen statt fortgeschriebener 0 %.

**B7 — `monthly_stats`.** Folgenabschätzung korrigiert: L2 ändert die DB-Monatsstatistik nicht.

**B8 — Blog-Builder.** `blog/blog_builder.py:624/640` (Heatmap) und `:683/691` (Monatsmittel) auf die neue Signatur;
`None`-Zellen ergeben eine leere Beschriftung statt `TypeError`.

**B9 — Wirkungsbericht vor dem Deploy** (auf dem Server, identische Rohdaten/Stichtag): je Ticker/Jahr alte/neue
Aufnahme + Grund; je Periode/Zyklusgruppe n, Mittel, Gewinnquote; je Blog-Konfiguration alte/neue Zellen, Balken,
Renderfehler. L2 und Schaltjahr-Faltung getrennt ausgewiesen. Der Bericht geht an den Nutzer, bevor veröffentlichte
Zahlen sich ändern (Nutzerentscheidung 2026-10-11: geänderte veröffentlichte Zahlen nachrechnen und mit `updated:`).

## Wächter und Mutationen (aus deiner Liste übernommen)

`scripts/verify_seasonal_twins.py` + `scripts/js/twin_probe.js`: Jahresende 363+365 gemeinsam akzeptiert, XETRA
363/364, weiteres Jahr ändert nichts; laufendes Jahr bei 359/364/365 abgelehnt (allein und neben Vorjahren),
zukünftiges Jahr abgelehnt, abgeschlossene Monate des laufenden Jahres zugelassen; 358/359-Grenze; fehlende Metadaten
abgelehnt; Stichtag injiziert. Echter Seitenpfad: gemeinsamer Builder, DE-Seiten-Builder und Python mit Bewegung nur
am 31.12. eines Schaltjahres (Jahres-, Dezember-, Q4-Endwert). Gruppen n=0..5, vier Zykluskarten in fester Reihenfolge,
auch alle grau. Renderer ohne `.toFixed`-Fehler/NaN. Blog: vollständiges, abgeschnittenes und laufendes Jahr gemeinsam.
`scripts/verify_twins_mutation.py`: Maximumregel zurück, Jahresprüfung entfernt, `<`→`<=` beim Stichtagsjahr,
Untergrenze ±1, fehlende Metadaten → 365, Tag-366-Faltung entfernt, `<5 → continue` zurück, Zyklus-Vorfilter
`<3`/Viergruppen-Abbruch zurück, Statuszweig im Renderer entfernt. Fachliche Erwartung in beiden Implementierungen,
nicht nur Gleichheit.

## Prüffragen
1. Deckt v2 alle neun Befunde? Was fehlt oder ist falsch gelöst?
2. Ist die Signatur mit `stichtagJahr` an allen Aufrufern umsetzbar (Liste der Aufrufer bitte nennen)?
3. Gibt es bei den anderen Seiten (B4) einen Fall, in dem die graue Karte schadet?
4. Reicht der Wirkungsbericht als Gate vor dem Deploy?
