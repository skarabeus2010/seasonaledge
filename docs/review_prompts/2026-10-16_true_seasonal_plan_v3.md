# Plan v3: Williams True Seasonal auf /jahreszyklus

Read-only, Repo `C:\dev\Seasonaledge`. Runde 2: `..._plan_v2_antwort.md`. Nur Änderungen gegenüber v2. Deutsch,
Datei:Zeile, am Ende **FREIGABE (Plan): ja/nein**.

## 1. Vollständiges Jahr: benannte Heuristik, Kalenderprüfung erst mit V4
Die Abdeckung gegen den Börsenkalender (`shared/sitzungen.py:72`, JS `SA.boersenkalender`) würde
`boersenkalender.js` auf /jahreszyklus einbinden. Das widerspricht der Nutzerentscheidung „Weg A“ (Kalender isoliert
bauen, Seiten gemeinsam umschalten; `jahreszyklus.html:315–316` lädt heute nur `methode.js` + `holidays.js`, und
`holidays.js` ist kein Zwilling des Python-Kalenders). Deshalb vorerst eine **ausdrücklich so benannte Heuristik**,
die mit der Kalender-Umstellung V4 durch die Sitzungsprüfung ersetzt wird (Posten in `KALENDER_UMSTELLUNG.md`):
- erste Kurszeile ≤ Kalendertag 7,
- letzte Kurszeile ≥ Tag **362** (gemessenes frühestes Jahresende aller Kalender 1990–2030, `calculations.py:176–186`;
  nicht 359 — damit fällt ein Jahr, das am 25.12. endet),
- keine Lücke zwischen zwei Kurszeilen > **14 Kalendertage** (TSE 27.04.–06.05.2019 = 11, NYSE 2001 = 7; was länger
  fehlt, ist kein Börsenjahr mehr, sondern ein Datenloch),
- vergangenes Jahr (`jahr < stichtag_jahr`).
Einzelne fehlende Sitzungen im Inneren erkennt sie nicht; die Seite interpoliert sie schon heute
(`interpolate_to_365`) — im Text: „vollständig nach Heuristik (Jahresanfang, Jahresende, keine Lücke über zwei
Wochen)“. Wächter: TSE 2019 zulässig, Ende 25.12. verworfen, Lücke 15 Tage verworfen, Jahr nur Dezember verworfen,
eine fehlende innere Sitzung **zulässig** (dokumentierte Grenze, kein stiller Fall).

## 2. Kennzahl = Änderungen der berechneten Kurven (Konventionen der Seite)
Keine gemittelten Monatsrenditen mehr. Bewertet werden die **Kurven selbst** auf der 365er-Achse der Seite:
Monatsänderung m = ln(K[e_m] / K[e_{m−1}]) mit e = 31, 59, 90, …, 365 (Slot-Ende wie im Chart), K[e_0] = 100 —
für das Ist-Jahr dessen `full_365`, für die Modelle die gemittelte Kurve. Damit gilt: Januar = erster bis letzter
Januarschluss (wie `normalize_year`, `calculations.py:106`), fehlende Returns werden wie in der Normalisierung
rekonstruiert/verworfen (der Kern liest nur fertige `full_365`), Schaltjahre folgen der Achse der Seite (Slot 59 =
28.02.; im Text „Monatsgrenzen der Chart-Achse“). Pearson r über die 12 Änderungen + Vorzeichentreffer (0 = kein
Treffer) neben „immer positiv“; konstante Reihe → nicht auswertbar.

## 3. Vergleich: Y als jüngstes Jahr
Je vergangenem Jahr Y im Fenster: **True Seasonal Y** = Mittel der vollständigen Jahre (Regel 1) in [Y−N, Y−1]
gegen **rückblickend Y** = Mittel aller Jahre in [Y−N, Y] nach der Regel der Seite im Durchschnittsmodus (Teiljahre
wie `buildExtendedYearData` sie liefert, `jahreszyklus.html:1764`). Bei `max`: [erstes Jahr, Y−1] bzw.
[erstes Jahr, Y]. Kein Ausreißerfilter im Rückblick (im Text genannt). Die „heutige Kurve“ als dritter Vergleich
entfällt (Nutzen gering, Definition strittig). Ausgewertet: alle vergangenen Jahre Y ≥ aktuellesJahr − N mit
genügend Vorjahren.

## 4. Mindestmenge nach dem Ausreißerfilter
Im True-Modus gilt ⌈0,8·N⌉ (bei `max` 10) **nach** dem IQR-Filter über die Modelljahre; darunter Hinweis statt Kurve.
Im Rückblick dieselbe Mindestmenge für True Seasonal Y; für rückblickend Y keine (die Seite zeigt sie heute auch).

## Unverändert aus v2
Kalenderfenster, getrenntes Ist-Jahr, Overlays/Perzentile/Einzeljahre/Detrend auf der Modellmenge, Pressure als
unabhängig beschriftet, Embed-Parameter, `SA.prefs`-Schlüssel, eigene Rückblick-Anfragekennung, DE/EN + `_JSON_VER`,
Wächter + Mutationen + jsdom-Seitenprobe. Blogartikel: Nutzerentscheidung, keine Änderung.

## Prüffragen
1. Trägt die Heuristik als Übergang bis V4 (Schwellen 7 / 362 / 14), oder gibt es ein Gegenbeispiel an unseren Börsen
   (u. a. Crypto 24/7, Forex, KRX, HKEX Taifun, ältere NYSE-Schließungen 1968/1969)?
2. Kennzahl auf den Kurven der Seite — tragfähig?
3. Freigabe für den Bau?
