# Entwurf: /jahreszyklus „Statistische Signifikanz der Präsidentenzyklus-Jahre“ zeigt nicht alle vier Jahre — Runde 1 (Plan)

Read-only, Repo `C:\dev\Seasonaledge`, Stand `origin/master`. Deutsch, echte Umlaute. Prüfe den **Entwurf**, bevor
Code entsteht: Diagnose am Code bestätigen oder widerlegen, Lösungsvorschlag bewerten, übersehene Fundstellen und
Folgen nennen. Jeder Befund mit Datei:Zeile, Mechanismus, konkretem Fehlerfall und Schwere. Am Ende
**FREIGABE (Plan): ja/nein**.

## Nutzermeldung

„In Jahreszyklus wird im Abschnitt ‚Statistische Signifikanz der Präsidentenzyklus-Jahre‘ nicht das Midterm-Jahr
angezeigt. Es sollen alle 4 Jahre des Präsidentenzyklus angezeigt werden. Das Feature haben wir wahrscheinlich schon
gebaut, aber es wird nicht mehr angezeigt.“

## Diagnose (live gemessen 2026-10-13, https://seasonalpha.ai/jahreszyklus?t=SPY)

| Zeitraum | angezeigte Karten (n) |
|---|---|
| 30 Jahre | Post-Election 6 · Midterm **5** · Pre-Election 5 · Election Year 7 |
| 20 Jahre | nur Election Year 5 — die anderen drei verschwinden |

**Defekt 1 — Gruppen verschwinden still.** `landing/js/significance.js:28` `runSignificanceTest` verwirft jede Gruppe
mit `returns.length < 5` (`continue`). `landing/pages/jahreszyklus.html` (`JZ.renderSignificance`, Zyklus-Zweig ab ca.
Z. 1387) prüft vorher nur `rets.length < 3` je Gruppe und danach `Object.keys(groups).length < 4` — beides **vor** dem
Test. Ergebnis: vier Gruppen bestehen die Prüfung, der Test lässt drei fallen, `renderSection` zeichnet eine Karte.
Midterm trifft es zuerst, weil das laufende Jahr 2026 selbst ein Midterm-Jahr und unvollständig ist (−1 Jahr).
`runSignificanceTest` nutzen elf Seiten (feiertage, monatswechsel, mondphasen, opex, overnight, plain-vanilla,
vixpiration, wochentage, zentralbanken, jahreszyklus) — überall verschwinden zu kleine Gruppen ohne Hinweis.

**Defekt 2 — vollständige Jahre werden verworfen (wiegt schwerer).** Gemessen im Seitenkontext mit den echten
Funktionen: `SA.seasonal.buildYearData(SPY ab 1995)` → `yearEndRef = 365` → `yearCovers(yd, 365, 365)` verwirft
**1995 (363), 2000 (364), 2005 (364), 2006 (363), 2011 (364), 2017 (363), 2022 (364), 2023 (363)** — 8 von 31
abgeschlossenen Jahren, dazu korrekt 2026 (285). Ursache: `yearEndRef` (`landing/js/seasonal-compute.js:411`) nimmt
das **Maximum** von `last_actual_day` über die abgeschlossenen Jahre; bei der NYSE endet irgendein Jahr am 31.12.
(365), also verlangt `yearCovers` (`:440`) von **jedem** Jahr Tag 365. Python-Zwilling identisch
(`shared/calculations.py:189` `year_end_reference`, `:228` `year_covers`). Damit ist die Korrektur aus Welle 1/4b
(`docs/KERNMETHODIK.md` ab Z. 255: „7 von 26 NYSE- und 15 von 26 XETRA-Jahren weg“) bei jeder Reihe unwirksam, in
der irgendein Jahr am 31.12. endet. Betroffen sind alle Perioden mit Ende 365: Präsidentenzyklus (ganzes Jahr),
**Dezember** und **Q4** in der Monats-/Quartals-Signifikanz, `calculate_period_stats` (Python, `:329`) und
**`blog/blog_builder.py:610/683`** (veröffentlichte Monats-/Heatmap-Zahlen, beim Deploy gebaut).

Frage dazu: Die Abnahme in `docs/KERNMETHODIK.md` (ca. Z. 385–392) behauptet „XETRA 2023 endet am 29.12. = Tag 363
… Mit `year_end_reference` wird es akzeptiert“. Bei SAP.DE enden andere Jahre am 30.12. (364) → ref ≥ 364 → 2023
müsste verworfen werden. Bitte prüfen, ob die Abnahme damals auf einer Reihe lief, die das nicht zeigt — oder ob ich
mich irre.

## Lösungsvorschlag

**L2 (Jahresende, beide Zwillinge gleich):** Ein **abgeschlossenes** Jahr (Jahr < laufendes Jahr) gilt als bis
Jahresende vollständig, wenn `last_actual_day ≥ JAHRESENDE_UNTERGRENZE` (359, gemessenes frühestes echtes
Jahresende = 362 über alle Kalender 1990–2030). Das laufende Jahr nie. `yearEndRef`/`year_end_reference` entfallen
oder liefern nur noch die Untergrenze; die Zirkelschluss-Sperren aus 4c bleiben erhalten (laufendes Jahr zählt nie;
abgeschnittene Historie < 359 zählt nie). Alternative, die ich **nicht** bevorzuge: Börsenkalender je Ticker
(exakter letzter Handelstag) — braucht den Ticker in der Signatur beider Zwillinge und ein Kalender-Mapping in
`buildYearData`. Bitte abwägen: Restrisiko der Untergrenze (Daten enden 27.–30.12. ohne Jahresende, Delisting kurz vor
Silvester) gegen den Umbau.

**L1 (stille Gruppen):** `runSignificanceTest` lässt Gruppen unter der Mindestzahl nicht mehr fallen, sondern gibt sie
mit `zu_wenig: true` und ihrem n zurück (kein t/p). `renderSection` zeichnet sie als graue Karte „zu wenige Jahre
(n=4, mind. 5)“ in fester Reihenfolge. Auf /jahreszyklus erscheinen damit immer alle vier Zyklusjahre. Die
Sonderprüfung „< 4 Gruppen → ‚Sorry, zu wenig Daten!‘“ im Zyklus-Zweig fällt weg bzw. greift nur, wenn gar keine Gruppe
auswertbar ist. Gilt für alle elf Seiten.

**Folgen, die ich sehe:** Blogzahlen (Dezember-/Q4-Werte) ändern sich beim nächsten Build; `monthly_stats` in der DB
(Dezember) beim nächsten Nightly; Wächter `scripts/verify_seasonal_twins.py` (Block yearEndRef/yearCovers,
`scripts/js/twin_probe.js:117`) und `scripts/verify_twins_mutation.py` (Mutationen Z. 57–72, 135) müssen auf die neue
Regel umgestellt werden — mit einem Fall, der den heutigen Fehler wörtlich trifft (NYSE-Reihe mit einem Jahr am
31.12. und einem am 29.12.).

## Prüffragen

1. Stimmen beide Diagnosen am Code? Gibt es weitere Stellen, die `last_actual_day` gegen 365 oder gegen ein Maximum
   vergleichen (z. B. Heatmap, `periodStats`, Detrend, andere Seiten mit eigenen Kopien)?
2. L2: Untergrenze oder Kalender? Was übersehe ich an Randfällen (Krypto 24/7 = 365/366, Forex, Halbtage,
   Sonderschließungen am Jahresende wie 2001/2004, Stooq-Altdaten)?
3. L1: Ist „graue Karte statt weglassen“ für alle elf Seiten richtig, oder gibt es Seiten, auf denen das Weglassen
   gewollt ist (z. B. viele kleine Gruppen)? Wie soll die Karte aussehen, damit niemand n=4 als Befund liest?
4. Wie messe ich die Wirkung vorher, damit eine geänderte veröffentlichte Zahl kein Überraschungsfund wird
   (Blog-Builder, `monthly_stats`)? Soll vor dem Deploy ein Vorher/Nachher-Bericht der betroffenen Blogzahlen entstehen?
5. Welche Wächter-Fälle und Mutationen brauche ich mindestens, damit beide Defekte nicht wiederkommen?
