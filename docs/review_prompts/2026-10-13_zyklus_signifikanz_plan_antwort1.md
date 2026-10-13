Die beiden Kerndiagnosen stimmen. **Den Plan würde ich in dieser Fassung noch nicht freigeben:** L1 erreicht mehrere Aufrufer nicht, L2 benötigt eine ausdrückliche Prüfung des jeweiligen Jahres, und der tatsächliche Seiten-Builder enthält einen zusätzlichen Jahresendfehler.

Geprüft wurde `HEAD = origin/master = abccbae`. Keine Dateien verändert. Die entscheidenden JS-Gegenbeispiele habe ich mit dem echten Quellcode in Node ausgeführt. Die gemeldeten Live-Fallzahlen und damaligen Rohkursmessungen habe ich nicht erneut erhoben.

**Befunde**

1. **Hoch — Defekt 2 bestätigt: Die Vollständigkeit eines Jahres hängt fälschlich von anderen Jahren ab.**  
   Quellen: [seasonal-compute.js:427](C:/dev/Seasonaledge/landing/js/seasonal-compute.js:427), [seasonal-compute.js:448](C:/dev/Seasonaledge/landing/js/seasonal-compute.js:448), [calculations.py:224](C:/dev/Seasonaledge/shared/calculations.py:224), [calculations.py:245](C:/dev/Seasonaledge/shared/calculations.py:245).  
   Mechanismus: Das Maximum wird zur Mindestanforderung für jedes einzelne Jahr. Ausgeführter Fehlerfall: `{2023:363, 2024:365}` akzeptiert nur 2024; `{2023:363}` akzeptiert 2023. Damit kann schon eine Änderung des gewählten Zeitraums die Akzeptanz eines unveränderten Jahres umschalten. Deine Erklärung für NYSE und SAP.DE ist richtig.

2. **Hoch — Die behauptete Sperre „laufendes Jahr zählt nie“ existiert bislang nicht vollständig.**  
   Quellen: [seasonal-compute.js:420](C:/dev/Seasonaledge/landing/js/seasonal-compute.js:420), [seasonal-compute.js:440](C:/dev/Seasonaledge/landing/js/seasonal-compute.js:440), [calculations.py:228](C:/dev/Seasonaledge/shared/calculations.py:228).  
   Mechanismus: Nur die *Referenzbildung* schließt das laufende Jahr aus. `yearCovers` kennt dessen Jahr nicht. Ausgeführter Fehlerfall: `{2023:363, 2026:364}`, Stichtagsjahr 2026, akzeptiert **beide** als volle Jahre. Eine konstante Referenz 359 würde dieses Problem verbreitern.  
   **Planauflage:** Jahr und Stichtagsjahr müssen bis zur Abdeckungsprüfung gelangen. Für Periodenende 365 das laufende und zukünftige Jahr ausdrücklich ausschließen; bereits abgeschlossene Monate des laufenden Jahres weiterhin zulassen. Bloß `yearEndRef` durch eine Konstante zu ersetzen reicht nicht.

3. **Mittel — Defekt 1 bestätigt; L1 muss auch die Gruppenerzeugung ändern.**  
   Quellen: [significance.js:28](C:/dev/Seasonaledge/landing/js/significance.js:28), [jahreszyklus.html:1402](C:/dev/Seasonaledge/landing/pages/jahreszyklus.html:1402), [jahreszyklus.html:1408](C:/dev/Seasonaledge/landing/pages/jahreszyklus.html:1408).  
   Ausgeführter Fehlerfall: Vier Gruppen mit `n=4,4,4,5` ergeben ausschließlich die letzte Karte. Bei `n=2` gelangt eine Zyklusgruppe hingegen überhaupt nicht zum Test.  
   **Planauflage:** Alle vier Zyklusgruppen einschließlich leerer Arrays anlegen und fest ordnen. Auch wenn keine Gruppe testbar ist, vier graue Karten anzeigen; ein ergänzender Hinweis darf sie nicht ersetzen. Sonst bleibt „immer alle vier“ unerfüllt.

4. **Mittel — „Gilt für alle elf Seiten“ ist weder als Bestandsbeschreibung noch als Umsetzung vollständig.**  
   Die genannte Liste enthält **zehn Seitentypen**, jeweils mit DE-/EN-Dateien. Zusätzliche Schwellen liegen vor dem gemeinsamen Test:

   | Fundstelle | Mechanismus und konkreter Fehlerfall |
   |---|---|
   | [feiertage.html:463](C:/dev/Seasonaledge/landing/pages/feiertage.html:463) | `n<5` wird vorher entfernt; ein Feiertag mit vier Ereignissen bleibt unsichtbar. |
   | [monatswechsel.html:528](C:/dev/Seasonaledge/landing/pages/monatswechsel.html:528), [mondphasen.html:327](C:/dev/Seasonaledge/landing/pages/mondphasen.html:327) | Monatsgruppen mit vier Beobachtungen erreichen L1 nicht. |
   | [opex.html:1023](C:/dev/Seasonaledge/landing/pages/opex.html:1023), [vixpiration.html:942](C:/dev/Seasonaledge/landing/pages/vixpiration.html:942) | Monatsgruppen mit zwei Ereignissen verschwinden vorher; entsprechende Filter existieren auch für kumulierte Fenster. |
   | [zentralbanken.html:492](C:/dev/Seasonaledge/landing/pages/zentralbanken.html:492) | Unter zehn Ereignissen wird die ganze Sektion verborgen. |
   | [plain-vanilla.html:440](C:/dev/Seasonaledge/landing/pages/plain-vanilla.html:440) | Unter zehn abgeschlossenen Trades wird die Sektion verborgen. Monatsresultate werden zwar berechnet, aber nicht ausgegeben, siehe [Zeile 471](C:/dev/Seasonaledge/landing/pages/plain-vanilla.html:471). |
   | [wochentage.html:1169](C:/dev/Seasonaledge/landing/pages/wochentage.html:1169) | Leere Wochentage fehlen bereits im Eingabeobjekt; „Gesamt“ hat zusätzlich eine Zehnerschwelle. |

   Hier bestehen ausdrückliche lokale Anzeigeentscheidungen. Ihre fachliche Absicht lässt sich aus dem Code allein nicht beweisen. Ich würde feste, ausgewählte Kategorien sichtbar halten, aber abgewählte OPEX-/VIX-Monate nicht wieder einblenden und ungenutzte Plain-Vanilla-Monatskarten nicht nebenbei aktivieren. Die lokalen Sektionenschwellen müssen im Plan ausdrücklich entschieden werden.

5. **Hoch — Übersehene Kopie: Der tatsächliche Jahreszyklus-Builder verliert den 31.12. im Schaltjahr.**  
   Quellen: [jahreszyklus.html:1600](C:/dev/Seasonaledge/landing/pages/jahreszyklus.html:1600), [jahreszyklus.html:569](C:/dev/Seasonaledge/landing/pages/jahreszyklus.html:569), [seasonal-compute.js:468](C:/dev/Seasonaledge/landing/js/seasonal-compute.js:468), [calculations.py:120](C:/dev/Seasonaledge/shared/calculations.py:120).  
   Mechanismus: Die Seite nutzt `buildExtendedYearData`, nicht den gemeinsamen Builder. Dessen eigene Interpolation faltet Tag 366 nicht auf Slot 365. Das spätere Begrenzen von `last_actual_day` repariert den Kurswert nicht.  
   Ausgeführter Fehlerfall mit 20 Dezemberbeobachtungen 2024, Kurs 100 bis 30.12., 110 am 31.12.: gemeinsamer Builder **110**, Seiten-Builder **100**. Betroffen sind Jahres-/Dezember-/Q4-Renditen und daraus berechnete Signifikanz. Die EN-Kopie besitzt dieselbe Interpolation: [en/jahreszyklus.html:555](C:/dev/Seasonaledge/landing/en/jahreszyklus.html:555).  
   **Planauflage:** Gemeinsame Interpolation verwenden oder beide Seitenkopien ausdrücklich korrigieren und testen.

6. **Mittel — Die Seiten-Heatmap hat eine abweichende Vollständigkeitsregel.**  
   Quelle: [jahreszyklus.html:713](C:/dev/Seasonaledge/landing/pages/jahreszyklus.html:713).  
   Mechanismus: Nur beim laufenden Jahr wird geprüft, und dort gegen den **Monatsanfang**, nicht das Monatsende. Vergangene Jahre erhalten keine Abdeckungsprüfung. Fehlerfall: Eine alte Historie endet im September; November und Dezember können als fortgeschriebene 0-%-Zellen erscheinen. Ein laufender, angebrochener Monat wird ebenfalls angezeigt, entgegen dem Kommentar.  
   L2 behebt das nicht automatisch. Entscheiden: abgeschlossene Monatswerte oder ausdrücklich gekennzeichnete Teilmonatswerte. `periodStats` dagegen nutzt den betroffenen Helfer direkt: [Zeile 605](C:/dev/Seasonaledge/landing/pages/jahreszyklus.html:605). Detrend enthält keinen zusätzlichen Jahresendfilter, sondern verarbeitet den gelieferten Durchschnitt: [Zeile 464](C:/dev/Seasonaledge/landing/pages/jahreszyklus.html:464).

7. **Mittel — Die angenommene Änderung von `monthly_stats` durch L2 ist widerlegt.**  
   Quelle: [cache_manager.py:96](C:/dev/Seasonaledge/shared/cache_manager.py:96).  
   Mechanismus: Die DB-Berechnung gruppiert Rohkurse nach Jahr/Monat und verwendet ersten und letzten Close. Sie ruft keinen der Jahresendhelfer auf. Konkreter Fall: Ein Dezember mit letztem Kurs am 29.12. wird dort bereits berücksichtigt.  
   L2 allein verändert diese Werte beim Nightly **nicht**. Ein Backfill zur Durchsetzung von L2 wäre wirkungslos. Eine Angleichung der DB-Methodik wäre ein eigener Änderungsumfang.

8. **Hoch — Der Blog-Heatmap-Pfad besitzt zusätzlich einen reproduzierbaren Fehler bei leeren Zellen.**  
   Quellen: [blog_builder.py:624](C:/dev/Seasonaledge/blog/blog_builder.py:624), [blog_builder.py:640](C:/dev/Seasonaledge/blog/blog_builder.py:640).  
   Mechanismus: Nicht abgedeckte Monate erzeugen `None`; anschließend wird jedes Element mit `f"{v:+.1f}%"` formatiert. Fehlerfall: Ein ausgewähltes laufendes Jahr mit zukünftigen Monaten führt beim Erzeugen der Beschriftung zu einem `TypeError`. L2 beseitigt diese berechtigten Leerzellen nicht.  
   Deshalb muss der Vorher/Nachher-Vergleich auch fehlgeschlagene beziehungsweise fehlende Charts erfassen. Die bestätigten L2-Folgen im Blog sind Dezemberzellen und Dezembermittelwerte: [Zeile 691](C:/dev/Seasonaledge/blog/blog_builder.py:691). Einen Q4-Builder belegen diese beiden Fundstellen nicht. Der Deploy ruft den Blog-Build tatsächlich auf: [deploy.yml:261](C:/dev/Seasonaledge/.github/workflows/deploy.yml:261).

9. **Mittel — Die dokumentierte Abnahme beweist den kritischen Mehrjahresfall nicht.**  
   Quellen: [KERNMETHODIK.md:380](C:/dev/Seasonaledge/docs/KERNMETHODIK.md:380), [twin_probe.js:133](C:/dev/Seasonaledge/scripts/js/twin_probe.js:133), [verify_seasonal_twins.py:452](C:/dev/Seasonaledge/scripts/verify_seasonal_twins.py:452).  
   Mechanismus: Die Dokumentation nennt Rohkursrenditen, aber keinen vollständigen Eingabedatensatz und keinen verwendeten Referenzwert. Die eingecheckten positiven Wächterfälle verwenden einheitlich Tag 364; unterschiedliche Jahresenden fehlen.  
   Fehlerfall: SAP.DE 2023 mit Tag 363 wird bei einem anderen Jahr mit Tag 364 verworfen. Das ist eindeutig. **Ob die damalige Messung nur 2023 verwendete oder lediglich den Renditewert ohne Auswahlfilter prüfte, bleibt unbelegt.** Ein Einjahreslauf erklärt das Ergebnis, ist aber keine nachgewiesene Rekonstruktion.

**Bewertung von L2**

Die Untergrenze ist als begrenzte Reparatur vertretbar, aber nur als **Jahresend-Heuristik**, nicht als Nachweis eines vollständigen Jahres.

- 359 akzeptiert im Nichtschaltjahr bereits den **25.12.**, im Schaltjahr den **24.12.**. Das Restrisiko beginnt früher als im Entwurf genannt.
- Die dokumentierte Messung „Minimum 362“ beweist keine Datenvollständigkeit und rechtfertigt nicht automatisch den zusätzlichen Spielraum bis 359. [calculations.py:176](C:/dev/Seasonaledge/shared/calculations.py:176) hält zudem ausdrücklich fest, dass der Wächter diese Messung nicht nachprüft.
- Krypto mit Datenende am 27.12. würde ebenfalls akzeptiert, obwohl der Repository-Kalender täglichen Handel vorsieht. Forex verwendet eine eigene Wochenendkonvention: [exchange_holidays.py:313](C:/dev/Seasonaledge/shared/exchange_holidays.py:313).
- Weder Untergrenze noch letzter erwarteter Handelstag erkennen fehlenden Jahresanfang, IPO-Teiljahre oder innere Datenlücken. Die Builder verlangen lediglich mindestens 20 Zeilen: [calculations.py:255](C:/dev/Seasonaledge/shared/calculations.py:255). Ein IPO im Herbst mit Daten bis Silvester bleibt damit als Jahresbeobachtung möglich.
- Kalenderinfrastruktur existiert bereits in beiden Sprachen: [holidays.js:207](C:/dev/Seasonaledge/landing/js/holidays.js:207), [holidays.js:260](C:/dev/Seasonaledge/landing/js/holidays.js:260). Der Umbau braucht zusätzlichen Kontext, aber kein völlig neues Kalendersystem. Allerdings dokumentiert der Kalender selbst historische Annahmen und ungeprüfte Bereiche: [exchange_holidays.py:474](C:/dev/Seasonaledge/shared/exchange_holidays.py:474).

Meine Empfehlung für diese Runde: **Untergrenze mit ausdrücklicher Jahresprüfung und dokumentiertem Restrisiko**. Die konkrete Wahl 359 muss als Toleranzentscheidung benannt werden. Bei einem Anspruch auf exakte Vollständigkeit ist der Kalenderansatz erforderlich. Halbtage zählen als Handelssitzung; Sonderschließungen und alte Stooq-Daten brauchen im Kalenderansatz belegte Regeln beziehungsweise einen definierten Umgang mit unbekannter Kalenderqualität.

**Bewertung von L1 und Kartengestaltung**

Die graue Karte ist richtig. Sie sollte beispielsweise enthalten:

> **Midterm**  
> Nicht ausgewertet  
> 4 abgeschlossene Jahresbeobachtungen · mindestens 5 erforderlich

Kein Tacho, Score, t/p-Wert, Gewinnanteil oder farbiger Renditewert. Insbesondere nicht „nicht signifikant“: Es wurde kein Test durchgeführt.

Für den gemeinsamen Renderer „Beobachtungen“ als Standard verwenden; Overnight zählt Handelstage, Plain-Vanilla Trades und Zentralbanken Ereignisse. „Jahre“ muss kontextabhängig sein. Der Statuszweig muss **vor** den numerischen Formatierungen liegen, sonst scheitern fehlende Werte an `.toFixed()`: [significance.js:156](C:/dev/Seasonaledge/landing/js/significance.js:156). Ebenso braucht die Relevanzsortierung einen definierten Umgang mit nicht getesteten Ergebnissen: [Zeile 70](C:/dev/Seasonaledge/landing/js/significance.js:70). DE und EN mitprüfen.

**Wirkungsmessung vor dem Deploy**

Ja, ein Vorher/Nachher-Bericht der betroffenen Blogausgaben sollte zur Abnahme gehören. Für beide Varianten **identische Rohdaten, identischen Stichtag, Zeitraum und Filterzustand** verwenden.

Erfassen:

- Je Ticker/Jahr: letzter echter Termin, alte/neue Aufnahmeentscheidung und Grund.
- Je Periode/Zyklusgruppe: aufgenommene Jahre, `n`, Mittelwert, Gewinnquote und gegebenenfalls Testwerte.
- Je Blog-Ausgabe: Artikel/Chart, Zeitraum, Sprache, alte/neue Zellen oder Balken sowie Renderfehler.
- Für `monthly_stats`: unveränderte Ergebnisse als Kontrollvergleich erwarten; keine Änderung durch L2 behaupten.

SPY, SAP.DE, Krypto, Forex und kurze beziehungsweise abgeschnittene Historien als gezielte Beispiele; für veröffentlichte Auswirkungen sämtliche tatsächlich betroffenen Blog-Konfigurationen prüfen. L2 und die Schaltjahrkorrektur getrennt ausweisen, damit Zahlenänderungen zugeordnet werden können.

**Mindestens erforderliche Wächter und Mutationen**

| Bereich | Pflichtfälle und erwartete Absicherung |
|---|---|
| Jahresende | Abgeschlossene Jahre mit 363 **und** 365 gemeinsam akzeptieren; zusätzlich XETRA 363/364. Ein weiteres Jahr darf die Entscheidung nicht ändern. |
| Stichtag | Laufendes Jahr bei 359/364/365 ablehnen für Jahresende – allein **und neben vollständigen Vorjahren**. Zukünftiges Jahr ebenfalls ablehnen; abgeschlossene frühere Monate des laufenden Jahres zulassen. |
| Grenzwerte | Bei gewählter Grenze 359: 358 ablehnen, 359 akzeptieren; fehlende/ungültige Metadaten ablehnen. Stichtag fest injizieren statt vom Ausführungsjahr abhängig machen. |
| Echter Seitenpfad | Gemeinsamer Builder, DE-/EN-Seiten-Builder und Python mit Schaltjahrbewegung ausschließlich am 31.12.; Jahres-, Dezember- und Q4-Endwert prüfen. |
| Gruppen | `n=0,1,2,3,4,5`; vier Zykluskarten in fester Reihenfolge, auch wenn alle grau sind. Bereits gültige Testergebnisse unverändert. |
| Renderer/Aufrufer | Kein `.toFixed()`-Fehler, keine NaN-Ausgabe, keine Signifikanzbehauptung bei grauen Karten; lokale Vorfilter und ausgewählte Kategorien testen. |
| Blog | Vergangenes vollständiges Jahr, abgeschnittenes Jahr und laufendes Jahr gemeinsam; `None` muss eine leere Zelle ergeben und renderbar bleiben. |

Gezielte Mutationen: Maximumregel wieder einsetzen; Jahresprüfung entfernen; `<` zu `<=` beim Stichtagsjahr; Untergrenze um einen Tag verschieben; fehlende Metadaten auf 365 setzen; Tag-366-Faltung entfernen; `<5 → continue` wieder einsetzen; Zyklus-Vorfilter `<3` beziehungsweise Viergruppen-Abbruch wiederherstellen; Statuszweig im Renderer entfernen.

Dabei fachliche Erwartungen in **beiden** Implementierungen prüfen, nicht nur ihre Gleichheit. Zwei identische Fehler dürfen keinen grünen Wächter ergeben.

**FREIGABE (Plan): nein** — erforderlich sind insbesondere die ausdrückliche Jahresprüfung, vollständige Gruppenerzeugung samt Aufruferentscheidungen, Einbeziehung des echten Seiten-Builders und eine korrigierte Folgenabschätzung.
