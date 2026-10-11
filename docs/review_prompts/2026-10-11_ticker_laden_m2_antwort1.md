**Urteil**

Noch keine Deployfreigabe: VORLADEN ist als Optimierung vertretbar, die neue Rückfallregel verletzt aber die Fehlerisolation je Anfrage.

**Befunde**

- **P2 — Rückfall bei bloßer Felderweiterung fehlt:** [kurse.js:317](/C:/dev/SeasonalEdge/landing/js/kurse.js:317) lehnt bei gleicher Datumsgrenze sofort ab. Eine synthetische Node-Probe mit feldabhängigem HTTP 500 zeigt: `date,close` funktioniert, die um `open` erweiterte Ladung scheitert; der neue Lader versucht den eigenen Bedarf nicht. Ebenso scheitert nach TTL eine `close`-Anfrage an einem zuvor geladenen `high`-Feld; HEAD liefert sie erfolgreich. Das ist ein Vertragsnachweis, kein beobachteter Live-Ausfall.
- **Vorbestehende Anzeige-Lücke:** [Dashboard:2199](/C:/dev/SeasonalEdge/landing/pages/dashboard.html:2199) prüft weder Erfolg noch Fehler gegen die Abrufkennung. Reproduziert: Nach Wechsel von `^GSPC` zu `SPY` überschreibt der verspätete Overnight-Abschluss die SPY-Karte. Auch im Vorher-Stand vorhanden; kein neuer M2-Regressionsbefund.
- **Positiv:** Lader **122/122**, Hüllen **65/65**; Text und Chart-Serien aller zwölf Normalfälle gleich. Zusätzliche Kontrollinteraktionen auf elf Seiten ebenfalls gleich. Dashboard-Anfragen **36 → 26**; zwölf Blockfehlerfälle zeigen den Ladefehler.

**Auflagen**

- Den einmaligen Rückfall auf den exakten eigenen Bedarf auch bei zusätzlichen Feldern erhalten; identischen Bedarf weiterhin ohne doppelte Ladung ablehnen.
- Regressionstests für gescheitertes VORLADEN sowie Felderweiterung bei gleicher Grenze nach TTL ergänzen.
- Dashboard-Overnight in den angekündigten Schritt für Abrufkennungen aufnehmen, einschließlich Fehlerabschluss.

Nichts geschrieben; Mutationstests nicht ausgeführt.
