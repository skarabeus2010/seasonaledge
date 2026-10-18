# Kalender V2 — Antwort Codex auf Entwurf v3 (2026-10-18) — Freigabe

**Urteil**
Freigabe als Bauvorlage für v1 + v2 + v3. Die drei Befunde aus Runde 2 sind im Entwurf erledigt; die Implementierungsabnahme steht noch aus.

**Befunde (P1/P2, nur neue oder offene)**
Keine. Auslieferungspfad, Cache-Buster und Release-Bootstrap sind am Code geprüft. Alle 57 Statusfälle aus v3 stimmen mit dem ausgeführten JS-Bundle und den Python-Intervallen überein.

**Auflagen**

- Einbindungs-, Release- und jsdom-Prüfung müssen die tatsächlich ausgelieferte Datei unter `seo/tools/` erfassen; HTTP-Nachweis nach dem Deploy wie vorgesehen.
- Alt-Momentaufnahme vor Änderungen einfrieren; Rechnerausgabe und freigegebene Textänderungen getrennt prüfen.
- Unabhängige Monatslisten einschließlich Monatsüberlauf bei `nextTradingDay` prüfen; Quellen und abgezählten TDOY-Ausgangswert festhalten.
- Bestehende Wächter erhalten; Mutationen müssen die benannten Vertragsverletzungen nachweisen.
- Read-only geprüft, keine Dateien geändert. Vollständige Gate- und Mutationstests waren nicht Gegenstand dieser Entwurfsprüfung.
