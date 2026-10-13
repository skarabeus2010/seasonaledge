**B6 ist jetzt vollständig; ich sehe keinen verbleibenden fachlichen Planblocker.** Geprüft gegen `HEAD = origin/master = 1e84da2`, ohne Dateien zu ändern. Dies ist eine Planprüfung, kein ausgeführter Wirkungsbericht.

1. **B6: ja.** Datenabdeckung **und** Kalenderabschluss verhindern die fortgeschriebenen Nullmonate. Die genannten Wächter decken Datenrückstand, Schaltjahrgrenze und zukünftige Jahre ab. Betroffene Stellen: [jahreszyklus.html:705](C:/dev/Seasonaledge/landing/pages/jahreszyklus.html:705), [blog_builder.py:624](C:/dev/Seasonaledge/blog/blog_builder.py:624).

   Die vollständige Kalenderbedingung sollte unmittelbar so ausgedrückt werden:
   ```text
   jahr < stichtag.jahr
   || (jahr == stichtag.jahr && monat < stichtag.monat)
   ```
   Deine kürzere Form ist mit vorgeschalteter Zukunftsjahr-Sperre ebenfalls korrekt. JS und Python müssen denselben Monatsbereich verwenden; bei JS also gegebenenfalls `getMonth() + 1`.

   Für die Blog-Heatmap reicht `current_year` allein nicht: Aus **einem vollständigen, injizierbaren Stichtag** müssen Jahr und Monat stammen. Das konkretisiert die bereits verlangte gleiche B6-Regel; derzeit wird dort nur das Jahr gelesen: [blog_builder.py:586](C:/dev/Seasonaledge/blog/blog_builder.py:586).

2. **Deploy-Vorlage: grundsätzlich richtig, aber kein „entweder/oder“.** Alle Änderungen dieser Arbeit außerhalb der Lader-Umstellung gehören in die betroffenen Fixture-Seiten – einschließlich beabsichtigter Anzeigeänderungen. Genau das verlangt [LIESMICH.md:7](C:/dev/Seasonaledge/scripts/fixtures/kurse_vorher/LIESMICH.md:7).

   Dabei sind **beide Seiten** betroffen:
   - Jahreszyklus: Signaturen, Stichtagsweitergabe, Interpolation, Signifikanz und Heatmap. Alte `yearEndRef`-Aufrufe müssen auch hier verschwinden: [Fixture:614](C:/dev/Seasonaledge/scripts/fixtures/kurse_vorher/pages/jahreszyklus.html:614).
   - Risikozyklus: ebenfalls die gemeinsame Interpolation verwenden: [Fixture:319](C:/dev/Seasonaledge/scripts/fixtures/kurse_vorher/pages/risikozyklus.html:319).

   Grund: Der Prüfer kombiniert aktuelle gemeinsame Module mit den Fixture-Dateien ([verify_seiten_kurse.py:57](C:/dev/Seasonaledge/scripts/verify_seiten_kurse.py:57)). Die Fixtures sind keine produktiven Aufrufer, aber ausführbarer Prüfcode. Der fachliche Alt/Neu-Wirkungsbericht muss deshalb echte getrennte Code-Stände vergleichen; die nachgezogene Lader-Vorlage ist dafür keine historische Referenz.

3. **Sonstige Freigabe: nichts Weiteres offen.** Die Präzisierungen zu B1–B5/B8 und das B9-Gate schließen die Punkte aus Runde 2. Bericht und anschließende Nutzerentscheidung liegen korrekt vor dem Master-Push, der den Deploy auslöst: [deploy.yml:4](C:/dev/Seasonaledge/.github/workflows/deploy.yml:4). Die oben erläuterte Stichtagsweitergabe und Fixture-Pflege gehören zur Umsetzung und Abnahme.

**FREIGABE (Plan): ja**
