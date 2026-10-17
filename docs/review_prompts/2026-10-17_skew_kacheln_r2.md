# Codex-Review: /skew Kacheln, Runde 2 (2026-10-17)

Nur lesen. Runde 1: [Antwort, 3 Befunde](2026-10-17_skew_kacheln_r1_antwort.md). Diff: `git diff HEAD -- landing scripts .github`.

## Behandlung
1. Ausblenden nur, wenn KEINE angezeigte Kennzahl vorhanden ist (`_hatWert` über alle 12 Spalten) — PFE/OKLO mit
   NE-Skew bleiben sichtbar. Probe: Zeile nur mit NE bleibt, ganz leere fällt raus.
2. Walls: `_zahl()` zeigt ganze Zahlen ohne, halbe mit einer Nachkommastelle; Differenz ungerundet, Farbe nach
   ungerundetem Vorzeichen, „±0“ nur bei exakt 0. Probe: 100 → 99,5 = „99.5 (−0.5)“ rot.
3. Vorsession: erwartet = voriger Werktag (Mo–Fr) vor der Session; ist die gefundene Archivdatei älter (Ausfall oder
   Feiertag), Kennzeichnung `*` an jeder Differenz und Hinweis im Kopf mit Datum (auch ohne Gamma-Index). Bewusst ohne
   Börsenkalender auf der Seite (480 KB); nach Feiertagen erscheint der Hinweis also auch bei echter Vorsession — er
   nennt das Datum und sagt „fehlt im Archiv oder war ein Feiertag“. Probe: Archiv 16.10. fehlt → „400 (+10*)“ + Hinweis.
4. Fußnote: Veränderung zur Vorsession, grün höher/rot tiefer, nach Verfallstagen oft mechanische Verschiebung.

Befunde behoben? Neue Probleme? Am Ende **FREIGABE** oder **KEINE FREIGABE**.
