# Antwort Codex — V1c-2 Entwurf v6 (2026-10-12): FREIGABE

Zu: [Entwurf v6](2026-10-12_kalender_v1c2_entwurf_v6.md)

**Urteil**
P2 aus Runde 5 ist aufgelöst. V1c-2 ist als Bauvorlage freigegeben.
**Befunde**
Der verpflichtende Parameter `pruefdatum` trennt Einstufung und gespeicherte Fakten; Bundle und `produktversion` bleiben reproduzierbar.
Die Grenzfälle sind schlüssig: September 2025 → Lücke, Oktober 2026 und Januar 2027 → Projektion; Gleichheit → Lücke.
Keine neuen blockierenden Entwurfsbefunde.
**Auflagen**
Zur Code-Abnahme: Pflichtparameter einschließlich fehlendem JS-Argument, Feldgruppen und `abdeckung(pruefdatum)` im Produktionspfad prüfen.
Beide Mutationen müssen gezielt scheitern; zusätzlich Bestandsschutz, unabhängige Sollfälle und vollständige Python/JS-Objektgleichheit nachweisen.
Getrennte Monatsbelege samt Quellen und Abrufdatum vollständig erheben oder Abdeckung ausdrücklich begrenzen.
Read-only geprüft; keine Dateien oder DB-Daten geändert.
