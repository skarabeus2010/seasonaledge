# Codex-Antwort: Code Stress-Ampel, Runde 2

codex
Die drei Befunde aus Runde 1 sind behoben. Ein neuer Befund:

1. **Mittel (P2) – SQL-Livewächter meldet ungeprüfte Rechte als bestanden:** [scripts/verify_stress_sql_live.py:86](/C:/dev/Seasonaledge/scripts/verify_stress_sql_live.py:86). **Eingabefall:** `SUPABASE_ANON_KEY` fehlt oder der Anon-Client scheitert mit einem Verbindungsfehler. Beide Fälle ergeben reproduziert im Fake **„BESTANDEN“, Exit 0**, obwohl keine Berechtigungsprüfung stattgefunden hat. Damit greift die vorgesehene Deploy-Sperre nicht zuverlässig. **Änderung:** Konfiguration vorab prüfen; ausschließlich die erwartete Berechtigungsverweigerung als Erfolg behandeln. Alle anderen Ausnahmen müssen einen Fehler und Exit 1 auslösen. Beide Negativfälle ergänzen.

**Verifikation:** 32/32 einschließlich der fünf Snapshot-Ticker bestanden, mit ausschließlich speicherbasierter Anpassung der JavaScript-Testübergabe. `git diff --check` ohne Fehler. Mutationen und echte SQL-Liveprüfung nicht ausgeführt.

FREIGABE: nein
