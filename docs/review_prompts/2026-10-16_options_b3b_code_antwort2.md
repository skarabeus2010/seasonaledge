**FREIGABE (Code): ja.**

Keine neuen P1/P2/P3-Befunde. Beide Befunde aus R1 sind behoben:

- **P2:** Snapshot-`ivrv` und History-`rv_1m` verwenden `_rankbar(t)`. Die übrige `cm_ok`-Rückfalllogik bleibt unverändert. Der neue Cron-Test deckt `single` mit gültiger ATM-IV ab.
- **P3:** Explizite Vorher-/Nachhervergleiche für Mail und /skew sowie der ereignisgesteuerte Sprachwechsel sind ergänzt.

Unabhängig ausgeführt: JS-Syntaxprüfungen und eine Seitenprobe im Speicher. Englischer Block, IV/RV-Tooltip und unveränderte Radarpunkte passen; die Sprachwechsel-Mutation wird erkannt.

**Prüfgrenze:** Python ist hier weiterhin nicht ausführbar. Den vollständigen Wächterlauf und die gemeldeten **44/44** habe ich daher nicht unabhängig bestätigt. Keine Dateien geändert.
