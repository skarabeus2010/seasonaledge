# Antwort Codex — V1c-2 Entwurf v5 (2026-10-12)

Zu: [Entwurf v5](2026-10-12_kalender_v1c2_entwurf_v5.md)

**Urteil**
Noch keine Freigabe als Bauvorlage: P1 aus Runde 4 ist aufgelöst, P2 bleibt offen.

**Befunde**

- **P1 aufgelöst:** Drei unabhängige Belegreihen und feldweise Listungsstatus verhindern, dass VX-Belege ungeprüfte Optionsfelder legitimieren.
- **P2 – Projektionsgrenze:** v5 §2 vergleicht mit dem Erhebungsdatum statt dem Prüfdatum. Bei Datenstand 2025-06 ist der Regeltermin September 2025 später und wird deshalb weiterhin `projektion` – entgegen §3(b). Die 200-Tage-Warnung korrigiert diese Fehlklassifikation nicht.

**Auflagen**

- Ein explizites `pruefdatum` festlegen: Unbelegte Termine nur bei `Regeltermin > pruefdatum` projizieren; andernfalls Felder `null` und Abdeckungslücke melden. `datenstand` dient der Aktualitätsprüfung.
- §3(b) mit festem Prüfdatum ausführen, einschließlich Gleichheitsfall; eine Mutation zurück zum Datenstand-Vergleich muss gezielt scheitern.
- Read-only geprüft; keine Dateien oder DB-Daten geändert.
