# Tage nach Börsenkalender — Plan P3/P4 v9 (nur Sperre in laufenden Ladungen)

Runde 8: [Plan v8](2026-10-11_kalender_p3p4_plan_v8.md) · [Antwort](2026-10-11_kalender_p3p4_plan_v8_antwort.md) (1 Befund).
Alles Übrige aus v8 und früher + A/B/C gilt. Read-only.

<task>Prüfe, ob V9 jetzt als Bauplan freigegeben werden kann.</task>

## Sperre an jedem Netz- und Übernahmepunkt
In `kurse.js` (und analog `SA.supabase.get`/`getAll` in `app.js`) wird `SA.__gesperrt` geprüft:
1. **unmittelbar vor `fetch`** — nach der Platzvergabe, also auch nach Poolwartezeit, zwischen zwei Blöcken, vor
   einer Wiederholung und vor einer Rückfall-Ladung (`eigeneLadung`);
2. **vor der Übernahme**: vor dem Veröffentlichen eines Bestands (`starte`), vor jeder Sicht (`aus`) und vor dem
   Auflösen einer wartenden Ladung;
3. ein `ReleaseFehler` ist **endgültig**: `holeBlock` wiederholt ihn nicht, `geteilt` fällt nicht auf den eigenen
   Bedarf zurück, eine wartende Ladung wird nicht gestartet; alle offenen Anfragen dieses Koordinators lehnen mit
   `ReleaseFehler` ab; ein laufender Transport wird per `AbortController` abgebrochen (`SA.__sperre` ruft
   `SA.kurse._abbrechenAlle()`).
Probe (node, echter `kurse.js` + echter Sperr-Bootstrap): Sperre (a) zwischen Block 1 und 2, (b) während
Poolwartezeit, (c) während einer Wiederholungspause, (d) während einer Rückfall-Ladung, (e) nach dem letzten Block
vor der Übernahme — jeweils: **keine weitere Netzanfrage nach der Sperre**, kein Bestand veröffentlicht, alle
Anfragen lehnen mit `ReleaseFehler` ab. Mutationen: Prüfung vor `fetch` entfernt; `ReleaseFehler` wiederholbar;
Rückfall bei `ReleaseFehler`; Übernahme ohne Prüfung → jeweils ein benannter Vertragsverstoß (weitere Anfrage
bzw. veröffentlichter Bestand) rot.

## Ausgabevertrag
**Urteil** · **Befunde** · **Auflagen**. ≤ 15 Zeilen.
