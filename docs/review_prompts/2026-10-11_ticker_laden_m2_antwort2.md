**Urteil**

Freigabe für den Deploy von Schritt 2. Auflagen 1 und 2 sind erfüllt; Auflage 3 ist für den nächsten Schritt vorgemerkt. Keine neuen blockierenden Befunde.

**Befunde**

- Rückfall funktioniert bei zusätzlichen Spalten: gescheitertes VORLADEN und Felderweiterung nach TTL sind abgedeckt. Identischer Bedarf bleibt ohne zweite Ladung.
- Unabhängig bestätigt: `eigene()` bleibt während Rückfall-Wiederholungen aktiv und endet nach Erfolg sowie Ablehnung bei 0.
- Node-Proben: Lader **125/125**, Hüllen **65/65**, Seitenkriterien **205/205** bestanden.
- Text und Chart-Serien aller zwölf Normalfälle stimmen überein; Dashboard-Anfragen **36 → 26**. Alle zwölf Blockfehlerfälle zeigen `prices 500`.
- Die zwölf neuen Vorher-Fixtures entsprechen HEAD.

**Auflagen**

- Die zwölf derzeit ungetrackten Fixtures in den Deploy-Commit aufnehmen.
- Dashboard-Overnight im nächsten Schritt mit Abrufkennung absichern, einschließlich Fehlerabschluss, zusammen mit den fünf angekündigten Seiten.

Nichts geschrieben; Mutationstests nicht ausgeführt.
