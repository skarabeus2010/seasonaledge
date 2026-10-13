**v2 deckt die neun Befunde weitgehend ab. Eine sachliche Lücke bleibt in B6: Im laufenden Jahr braucht die Heatmap neben dem Kalenderabschluss auch die Datenabdeckung. Deshalb noch keine Plan-Freigabe.**

Geprüft: `HEAD = origin/master = 50a48c4`. Keine Dateien verändert. Die Schaltjahrfälle habe ich mit den tatsächlichen JS-Buildern in Node nachvollzogen; einen Server-Wirkungsbericht habe ich nicht ausgeführt.

**1. Abdeckung der neun Befunde**

- **B1/B2: gelöst.** Die Entscheidung pro Jahr ist unabhängig von anderen Jahren; die ausdrückliche Jahresprüfung verhindert die Aufnahme laufender und zukünftiger Jahre für Dezember, Q4 und Gesamtjahr. 359 ist jetzt korrekt als Toleranzentscheidung beschrieben. Die Regel muss vor einem möglichen allgemeinen `lad >= endDoy`-Erfolg greifen, damit Tag 365 im laufenden Jahr nicht erneut durchrutscht. Betroffene Stelle: [seasonal-compute.js:440](C:/dev/Seasonaledge/landing/js/seasonal-compute.js:440).
- **B3: gelöst.** Vier angelegte Gruppen einschließlich leerer Arrays und die Entfernung beider Vorfilter erfüllen die Anforderung. Die feste Kartenreihenfolge muss weiterhin Vorrang vor der Relevanzsortierung haben: [significance.js:122](C:/dev/Seasonaledge/landing/js/significance.js:122).
- **B4: grundsätzlich gelöst**, mit den unten genannten Präzisierungen für Optionen und Beschriftung. Das ausdrückliche Beibehalten lokaler Vorfilter ist eine nachvollziehbare Umfangsentscheidung.
- **B5: bestätigt, einschließlich Risikozyklus.** Beide Seiten besitzen die fehlerhafte Interpolationskopie: [jahreszyklus.html:577](C:/dev/Seasonaledge/landing/pages/jahreszyklus.html:577), [risikozyklus.html:319](C:/dev/Seasonaledge/landing/pages/risikozyklus.html:319). Ausgeführter Fall: 20 Dezemberkurse 2024, ausschließlich am 31.12. Bewegung von 100 auf 110. Beide Seiten liefern Endwert **100**, der gemeinsame Builder **110**. Beide DE-Builder müssen die gemeinsame Interpolation verwenden; beide erzeugten EN-Seiten gehören in die Prüfung.
- **B6: noch unvollständig**, siehe nächster Absatz.
- **B7: gelöst.** Die korrigierte Folgenabschätzung entspricht dem separaten Rohkursweg in [cache_manager.py:96](C:/dev/Seasonaledge/shared/cache_manager.py:96).
- **B8: gelöst im vorgesehenen Umfang.** Signaturmigration und leere Beschriftung für `None` behandeln beide Fehler. Beim Monatsmittel muss zusätzlich die Schleife von `.values()` auf `.items()` wechseln, damit das Jahr verfügbar ist: [blog_builder.py:684](C:/dev/Seasonaledge/blog/blog_builder.py:684).
- **B9: geeignetes Konzept.** Die Mehrjahresfälle und Mutationen adressieren den bisherigen Nachweismangel. Für das Veröffentlichungsgate sind die unten genannten Abnahmekriterien festzuhalten.

**Verbleibender Befund: B6 lässt bei veralteten Daten weiterhin falsche Nullmonate zu.**

Der vorgesehene Sonderzweig für das laufende Jahr prüft nur „Monatsende < heute“. Beispiel: Stichtag **13.10.2026**, letzte Kurse **30.06.2026**. Juli bis September sind kalendarisch abgeschlossen, enthalten aber ausschließlich Fortschreibung. Mit dem echten Seiten-Builder ergibt sich für Juli **0 %**; die Kalenderbedingung akzeptiert ihn, die Abdeckungsprüfung verwirft ihn. Ausgangspunkt: [jahreszyklus.html:705](C:/dev/Seasonaledge/landing/pages/jahreszyklus.html:705).

B6 sollte ausdrücklich lauten:

> Jede Zelle benötigt `yearCovers(yd, monatsEnde, jahr, stichtagJahr)`. Im laufenden Jahr muss zusätzlich der betreffende Kalendermonat beendet sein. Zukünftige Jahre bleiben leer.

Für die zusätzliche Kalenderprüfung besser Jahr/Monat vergleichen. Die festen [MONTH_BOUNDS:332](C:/dev/Seasonaledge/landing/pages/jahreszyklus.html:332) sind keine schaltjahrgenauen Monatsenddaten: Ein Vergleich von Slot 59 mit dem tatsächlichen Tag 60 würde am 29.02. einen noch laufenden Februar als beendet behandeln. Dafür ist kein Börsenkalender erforderlich.

Ergänzende Wächter: **laufendes Jahr mit im Juni abgeschnittenen Daten bei Oktober-Stichtag**, **29.02. noch leer / 01.03. kalenderseitig abgeschlossen**, zukünftiges Heatmap-Jahr leer. Die Datenabdeckungsprüfung muss jeweils zusätzlich bestehen bleiben.

**2. Aufrufer der neuen Signatur**

Die Migration ist überall umsetzbar; das jeweilige Jahr liegt vor oder kann über `.items()` bereitgestellt werden.

| Direkter Aufrufer | Fundstelle DE/Python | EN-Gegenstück |
|---|---|---|
| `periodStats` | [jahreszyklus.html:616](C:/dev/Seasonaledge/landing/pages/jahreszyklus.html:616) | [EN:605](C:/dev/Seasonaledge/landing/en/jahreszyklus.html:605) |
| Signifikanz Monate | [jahreszyklus.html:1533](C:/dev/Seasonaledge/landing/pages/jahreszyklus.html:1533) | [EN:1522](C:/dev/Seasonaledge/landing/en/jahreszyklus.html:1522) |
| Signifikanz Quartale | [jahreszyklus.html:1548](C:/dev/Seasonaledge/landing/pages/jahreszyklus.html:1548) | [EN:1537](C:/dev/Seasonaledge/landing/en/jahreszyklus.html:1537) |
| Signifikanz Präsidentenzyklus | [jahreszyklus.html:1562](C:/dev/Seasonaledge/landing/pages/jahreszyklus.html:1562) | [EN:1551](C:/dev/Seasonaledge/landing/en/jahreszyklus.html:1551) |
| `calculate_period_stats` | [calculations.py:332](C:/dev/Seasonaledge/shared/calculations.py:332) | — |
| Blog-Heatmap | [blog_builder.py:624](C:/dev/Seasonaledge/blog/blog_builder.py:624) | gemeinsamer Builder |
| Blog-Monatsmittel | [blog_builder.py:691](C:/dev/Seasonaledge/blog/blog_builder.py:691) | gemeinsamer Builder |
| JS-Wächter | [twin_probe.js:122](C:/dev/Seasonaledge/scripts/js/twin_probe.js:122) | — |
| **Neu:** Seiten-Heatmap | [jahreszyklus.html:705](C:/dev/Seasonaledge/landing/pages/jahreszyklus.html:705) | erzeugtes EN-Gegenstück |

Die Stichtagsinjektion muss auch durch die umgebenden Funktionen reichen. Sonst wäre zwar `yearCovers` deterministisch testbar, der tatsächliche Seiten-/Blogpfad aber weiterhin von der Rechnerzeit abhängig.

Das betrifft insbesondere:

- `periodStats`, aufgerufen in `jahreszyklus.html` bei **1401, 1443, 1464, 1503**.
- `calculate_period_stats`, derzeit im Wächter aufgerufen bei [verify_seasonal_twins.py:460](C:/dev/Seasonaledge/scripts/verify_seasonal_twins.py:460), **474 und 484**.
- Beide Blogfunktionen, die schon ein `current_year` bestimmen: [blog_builder.py:586](C:/dev/Seasonaledge/blog/blog_builder.py:586), [blog_builder.py:672](C:/dev/Seasonaledge/blog/blog_builder.py:672).

`yearEndRef`/`year_end_reference` einschließlich Imports und alter Wächter-/Mutationsreferenzen entfernen. Historische Dateien unter `scripts/fixtures/kurse_vorher` sind dabei keine produktiven Aufrufer.

**3. Graue Karten auf den anderen neun Seiten**

**Keinen fachlich schädlichen Fall gefunden**, sofern die vorhandene Gruppenauswahl unverändert bleibt.

| Seiten | Wirkung |
|---|---|
| Feiertage | Der lokale ≥5-Filter verhindert bei gültigen Werten neue graue Karten: [feiertage.html:463](C:/dev/Seasonaledge/landing/pages/feiertage.html:463). |
| Monatswechsel / Mondphasen | Monatsgruppen bleiben vorgefiltert; „Selected TOM“ beziehungsweise „Gesamt“ können grau werden. Das erklärt fehlende Testbarkeit sinnvoll: [monatswechsel.html:524](C:/dev/Seasonaledge/landing/pages/monatswechsel.html:524), [mondphasen.html:324](C:/dev/Seasonaledge/landing/pages/mondphasen.html:324). |
| OPEX / VIXpiration | Ausgewählte Gruppen mit drei oder vier Beobachtungen werden grau. Abgewählte Monate bleiben ausgeschlossen: [opex.html:1011](C:/dev/Seasonaledge/landing/pages/opex.html:1011), [vixpiration.html:942](C:/dev/Seasonaledge/landing/pages/vixpiration.html:942). |
| Zentralbanken / Plain-Vanilla | Die Zehnerschwellen bleiben. Plain-Vanilla-Monatsergebnisse werden weiterhin nicht gerendert: [zentralbanken.html:492](C:/dev/Seasonaledge/landing/pages/zentralbanken.html:492), [plain-vanilla.html:471](C:/dev/Seasonaledge/landing/pages/plain-vanilla.html:471). |
| Wochentage | Tagesgruppen und Weekend-Monatsgruppen mit einer bis vier Beobachtungen werden sichtbar grau; sachlich passend: [wochentage.html:1169](C:/dev/Seasonaledge/landing/pages/wochentage.html:1169), [wochentage.html:1314](C:/dev/Seasonaledge/landing/pages/wochentage.html:1314). |
| Overnight | Trotz 50er-Sektionsschwelle können Untergruppen klein oder leer sein. Alle zwölf Monatsgruppen werden angelegt, daher entstehen auch graue Nullgruppen: [overnight.html:555](C:/dev/Seasonaledge/landing/pages/overnight.html:555), [overnight.html:583](C:/dev/Seasonaledge/landing/pages/overnight.html:583). Sinnvoll, aber ausdrücklich als sichtbare Änderung dokumentieren. |

Für B4 noch festlegen:

- **Optionen bis zum Renderer transportieren.** Aktuell hat [renderSection:117](C:/dev/Seasonaledge/landing/js/significance.js:117) keinen `opts`-Parameter. Beispielsweise einen optionalen vierten Parameter verwenden; angezeigte Mindestzahl aus derselben Option beziehen, nicht fest „5“ schreiben.
- **„Abgeschlossene Jahre“ nur im Zykluszweig.** Monats-/Quartalsgruppen können Beobachtungen des laufenden Jahres enthalten. Dort „abgeschlossene Monats-/Quartalsbeobachtungen“ oder den Standard „Beobachtungen“ verwenden.
- **Neue Texte in DE und EN prüfen.** `build_en.py` allein übersetzt keine neu hinzugefügten Laufzeittexte in `significance.js`; dessen vorhandenen i18n-Weg weiterführen.

**4. Wirkungsbericht als Gate**

**Ja, mit konkreten Bestehenskriterien.** Der Bericht muss den geprüften Code, Datenstand, vollständigen Stichtag, Zeitraum und Filterzustand identifizieren. Zusätzlich zu den Kennzahlen sollten die aufgenommenen Jahre je Gruppe enthalten sein; gleiche Fallzahlen können unterschiedliche Zusammensetzungen verdecken.

Vor Veröffentlichung müssen:

- alle betroffenen veröffentlichten Blog-Konfigurationen einschließlich DE/EN erfasst sein;
- Zahlenänderungen erklärt und nachgerechnet sein;
- neue Ausgaben ohne Renderfehler entstehen;
- betroffene Artikeltexte zu den neuen Charts passen und das verlangte `updated:` erhalten;
- L2, Schaltjahrkorrektur und Heatmap-Filteränderung getrennt zuordenbar sein.

Der Bericht muss **vor dem Push nach `master` beziehungsweise vor Auslösen des Deploys** vorliegen: [deploy.yml:4](C:/dev/Seasonaledge/.github/workflows/deploy.yml:4) startet automatisch bei Push; der Blog-Build erfolgt erst nach dem Containerwechsel bei [deploy.yml:259](C:/dev/Seasonaledge/.github/workflows/deploy.yml:259). Ein Bericht innerhalb dieses Veröffentlichungslaufs wäre zu spät. Ändert sich anschließend die Vergleichsgrundlage wesentlich, ist der Vergleich zu erneuern.

Der verbleibende Freigabeblocker ist die unvollständige B6-Regel. Die übrigen Punkte sind konkret benannte Ergänzungen für Umsetzung und Abnahme.

**FREIGABE (Plan): nein**
