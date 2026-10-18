# Kalender V2 — Antwort Codex auf Entwurf v1 (2026-10-18)

**Urteil**
Noch keine Freigabe als Bauvorlage. Die Architektur trägt; die nachgerechnete Verteilung aller 373 Ticker, sämtliche Offenheitsabweichungen sowie 26 Kalenderseiten und 23 Headeraufrufer stimmen.

**Befunde (P1/P2)**

- **P2 – Fehlersperre umgehbar:** `catch → NONE` mit anschließendem Kurzschluss ruft `isTradingDay` überhaupt nicht auf ([dashboard.html:565](/C:/dev/SeasonalEdge/landing/pages/dashboard.html:565), [monatszyklus.html:442](/C:/dev/SeasonalEdge/landing/pages/monatszyklus.html:442)). Watchlist fängt Zuordnungsfehler als NYSE ab. Das geplante Werfen allein verhindert diese Falschergebnisse nicht.
- **P2 – Einbindungs-Gate unvollständig:** Zusätzlich zu `verify_einbindung.py` verbietet [verify_boersenkalender_js.py:268](/C:/dev/SeasonalEdge/scripts/verify_boersenkalender_js.py:268) jede Bundle-Referenz. Beide Isolationsassertionen müssen durch den manifestgestützten Einbindungsvertrag ersetzt werden; Traversierungs-/Lesefehler bleiben rot.
- **P2 – Converter-Vertrag fehlt:** Status, sichtbare CRYPTO-/FOREX-Konvention, kumulierte Nummern an geschlossenen Tagen und echte Periodensummen ausdrücklich festlegen. Auch Erklärungskarten/FAQ enthalten feste Grenzen 23/252/365 ([Converter:162](/C:/dev/SeasonalEdge/seo/tools/trading-day-converter.html:162)); reine Rechnerumstellung reicht nicht.
- **P2 – Prüfplan nicht unabhängig genug:** `shared.sitzungen` und `handelstag_nummern` sind Produktionszwillinge. Die wenigen zusätzlichen Sollfälle ersetzen keine unabhängigen Sitzungslisten für alle Börsen und Statusgrenzen. C verlangt außerdem DST-/Mitternachtsfälle und A→B→A-Tickerwechsel.
- **P2 – Rückgabe-/Fehlervertrag lückenhaft:** `nummern` liefert eine Liste, deren Einträge keinen Status enthalten ([api.js:350](/C:/dev/SeasonalEdge/scripts/boersenkalender/api.js:350)); Header/Converter müssen `status(b, jahr)` ergänzen. `n` oberhalb der Periodensumme bleibt `null`; fehlende Börse sowie ungültige Typen/Datumswerte brauchen ausdrückliche Regeln.
- **P2 – Private Sonderliste:** Bloßes Entfernen von `_NYSE_SONDER` löst keinen Fehler aus: [strategy-compute.js:335](/C:/dev/SeasonalEdge/landing/js/strategy-compute.js:335) ersetzt sie durch `[]` und nimmt Sonderschließungen auf. Der angekündigte Fehler braucht einen werfenden Zugriff oder einen explizit gesperrten Verbraucher.
- **P2 – Zuordnungsbehauptung zu weit:** „Unbekannter Ticker → Fehler“ entspricht nicht `boerse`: unbekannte einfache Namen, sogar „11 Sektoren“, ergeben NYSE ([api.js:330](/C:/dev/SeasonalEdge/scripts/boersenkalender/api.js:330)). Den Vertrag auf die gemeinsame Listingregel präzisieren.

**Antworten 1–4**

1. Werfen trägt bis V9, solange `alt` aktiv bleibt. Keine Zwischenform nötig; vor Aktivierung müssen auch geschluckte Fehler und Kurzschlüsse beseitigt sein.
2. String-Rückgabe beibehalten. Ein Inventar reicht bei verbindlicher Phasenzuordnung und einem Aktivierungs-Gate, das keine offenen Einträge zulässt; `{boerse, alt}` bräche weitere Aufrufer.
3. Bundle bereits in V2 einbinden, nach gzip-Korrektur und Ersatz beider Isolationsassertionen. Der nginx-Befund wird durch die Konfiguration gestützt.
4. Für heutige Kalendernummern trägt die DB-Zeile nichts Erforderliches bei. Einen letzten Kursstand gegebenenfalls separat mit dessen Datum anzeigen.

**Auflagen**

- Converter in den Release-/Methodenvertrag aufnehmen: [release_setzen.py:31](/C:/dev/SeasonalEdge/deploy/release_setzen.py:31) berücksichtigt `seo/tools` bereits; Bootstrap und beide Zweige müssen auf der tatsächlich ausgelieferten Seite geprüft werden.
- Alle Headerfelder einschließlich Wochentag, TWOY, Quartal und Zyklus aus demselben Börsendatum ableiten; `ungeprueft` ausdrücklich als explorativ kennzeichnen.
- Alt-Momentaufnahme vor Umbau einfrieren; Defaults, Rückgabeformen, Fehlerklasse und Randfälle prüfen. Mutationen müssen benannte Vertragsverletzungen nachweisen.
- Read-only geprüft, reale JS-Kerne ausgeführt; keine Dateien geändert. Vollständige Gate-/Mutationstests waren nicht Gegenstand dieser Entwurfsprüfung.
