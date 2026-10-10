# Antwort Codex — Paket 3 Code Runde 1 (2026-10-10)

Prompt: [2026-10-10_kalender_paket3_code.md](2026-10-10_kalender_paket3_code.md). model: gpt-6.1-sol

**Urteil: Keine Freigabe.** Auflage 5 ist bei Intraday und Nightly noch nicht erfüllt.

Schreibfrei bestätigt: Ticker-Wächter **54/54**, Kalender-Sollfälle **86/86**, Handelstag-Nummern **86/86**. Keine Dateien oder Datenbankdaten geändert.

**Befunde**

- **[P1] Intraday-Kalenderfehler lassen den Job grün.** [intraday_refresh.py:172](C:/dev/SeasonalEdge/scripts/intraday_refresh.py:172) erfasst den Fehler, aber Zeilen 292–306 wenden anschließend die Ausfalltoleranz an. Isolierter Aufruf der echten `main()`: ein Zuordnungsfehler unter zehn Tickern → **Exit 0**, neun Erfolge, ein Fehler; die Kurse des betroffenen Tickers werden geschrieben. Kalenderfehler müssen unabhängig von der Yahoo-Ausfalltoleranz Exit ≠ 0 erzwingen.

- **[P1] Nightly zählt ungeprüfte Ticker weiterhin als vollständig.** [nightly_refresh.py:299](C:/dev/SeasonalEdge/scripts/nightly_refresh.py:299) sammelt Zuordnungsfehler, berücksichtigt sie aber weder in der Vollständigkeitsmeldung noch in `tickers_success` oder dem Exit. Isolierter Aufruf der echten `main()`: einer von zwei Tickern nicht prüfbar → **„Alle Ticker vollständig“**, **2/2 erfolgreich**, **Exit 0**. Das ist eine ausdrücklich offene A3-Auflage, keine neu eingeführte Regression.

- **[P2] Zwei Suffixregeln sind ungeschützt.** [verify_ticker_boerse.py:61](C:/dev/SeasonalEdge/scripts/verify_ticker_boerse.py:61) enthält keine unbekannten `.BR`-/`.LS`-Ticker. Beide Regeln einzeln ausschließlich im Arbeitsspeicher entfernt → Wächter weiterhin **54/54**, Exit 0. Je einen Regelfall und eine gezielte Mutation ergänzen.

**Antworten**

1. **370 bekannte Ticker:** Keine Zuordnungsänderung gefunden. Fixture und aktuelle Funktion stimmen unabhängig mit Commit `d6b683e` überein; alle 370 Kleinschreibvarianten ebenfalls. Keine ausführbaren Importe der entfernten APIs oder Root-Kopie gefunden.

2. **Verschluckende Aufrufer:** Intraday und Nightly bleiben problematisch, siehe P1. Daily lässt den MW-Wert nach protokolliertem Fehler leer; Completeness erzeugt einen roten Befund; Backfill reicht propagierte Kalenderfehler jetzt bis Exit 1 weiter.

3. **Kurse trotz Nummerierungsfehler:** Vertretbar, wenn der Kalenderfehler den Lauf zwingend scheitern lässt und keine teilweise berechneten Nummern veröffentlicht werden. Ein vollständiger Verzicht auf Kursupdates ist dafür nicht erforderlich.

4. **pip auf dem Runner:** Aktuell tragfähig: Ubuntu 24.04 liefert Python 3.12; die Image-Konfiguration erlaubt pip-Installationen. [Runner](https://raw.githubusercontent.com/actions/runner-images/main/images/ubuntu/Ubuntu2404-Readme.md), [Konfiguration](https://raw.githubusercontent.com/actions/runner-images/main/images/ubuntu/scripts/build/install-python.sh). Python über `setup-python` auf 3.12 festlegen: NumPy 1.26.4 unterstützt nur 3.9–3.12. [NumPy](https://numpy.org/doc/2.4/release/1.26.4-notes.html)

5. **Fehlende Mutationen:** Ja: Fehlerweitergabe der A3-Aufrufer, insbesondere Intraday unterhalb der Toleranz und Nightly-Erfolgszählung, außerdem `.BR`/`.LS`. Die vorhandenen 13 Mutationsfälle treffen im Arbeitsspeicher ihre benannten Prüfungen. Den dateischreibenden Mutationstest habe ich nicht ausgeführt.
