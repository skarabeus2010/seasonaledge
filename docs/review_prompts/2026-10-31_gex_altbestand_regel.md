# Planprüfung — GEX-Altbestand 03.08.–14.10.2026 wieder aufnehmen (Arm B der Gamma-Studie)

Grundlage: Studienplan v4–v7 (freigegeben), dort Arm B: „alles vor B2 ausgeschlossen (Stempelversatz **und** veralteter
Spot bis 13.10.)“, gestützt auf `docs/OPTIONS.md` (Abschnitt GEX-Spot) und die Commit-Nachricht `bb70906`. Der Nutzer
möchte die alten Tage nutzen, wo das sauber geht. Ich habe gemessen (nur lesend, Server) — **die Messung widerspricht
der Doku**.

## Messung

Je Archivdatei `gex_history/<stempel>.json` × Ticker: archivierter `spot` gegen die Supabase-Schlüsse der Sitzungen
im Umkreis ± 9 Kalendertage; dazu die Erstellungszeit (birth) jeder Datei.

| Zeitraum (Stempel) | Laufzeit (UTC) | Spot = Schluss von | Fälle |
|---|---|---|---|
| 08-03 … 08-25 (16 Dateien) | 22:52–23:25 am Stempeltag | **Stempeltag** (Abweichung ≤ 0,19 %) | 17–19/20 je Datei |
| 08-27 … 10-14 (35 Dateien) | 00:14–03:55 am Stempeltag (= Abend der Vortagssitzung in New York) | **letzte NYSE-Sitzung vor dem Stempeltag** (Abweichung meist 0,0000) | 13–20/20 je Datei |
| 09-06 (So, 15:12 UTC), 09-08 (00:31 UTC, nach Labor Day) | | beide 09-04 | — |
| `gex_history_session/` 10-15 … 10-30 | | Session (wie erwartet) | 20/20 |

Abweichungen > 0,3 %: 48 Ticker-Tage, davon ETHA 45 (Basiswechsel ×3, nicht im Studienuniversum), XLE 2, TLT 1.
In `scripts/snapshot_gex_massive.py` (Stand vor `bb70906`) ist der archivierte `spot` dieselbe Variable, mit der GEX,
Walls und Flip gerechnet wurden. Die Pipeline lief bis 2026-09-05 über Yahoo (`snapshot_gex.py`), ab 2026-09-06 über die
Massive-Voll-Chain (Commit `214c028`).

**Lesart:** Der Spot der Altdateien ist der Schluss der gemeinten Sitzung; falsch ist ab 27.08. nur der Dateiname
(Lauftag statt Session). Die Behauptung „GEX rechnete bis 13.10. mit einem um eine Session veralteten Spot“ finde ich in
den Daten nicht — sie stammt vermutlich aus dem einen Lauf am 15.10. 00:30 UTC, bei dem `/prev` die Vorsitzung lieferte.

## Vorgeschlagene Regel

1. Session je Datei = letzte NYSE-Sitzung, deren regulärer Schluss (16:00 New York, Halbtag laut Kalender) vor der
   Erstellungszeit der Datei liegt.
2. Ein Ticker-Tag zählt nur, wenn `|spot / Supabase-Schluss(Session) − 1| ≤ 0,3 %`; sonst ausgeschlossen mit Grund.
3. Mehrere Dateien für dieselbe Session (09-05/09-06/09-08 → 09-04): die erste nach Sessionschluss gilt, die übrigen
   werden als Dubletten ausgewiesen.
4. Methodenversion als eigenes Merkmal: `yahoo` (bis 2026-09-05), `massive_lauftag` (09-06 bis 10-14),
   `massive_session` (ab 10-15). Auswertung je Version getrennt ausgewiesen, Zusammenfassung nur mit Kennzeichnung.
   Bekannter Unterschied `massive_lauftag` ↔ `massive_session`: Restlaufzeit gegen den Lauftag statt die Session
   (DTE einen Tag kleiner, Horizontgrenze 45 Tage um einen Tag verschoben); verfallene Kontrakte waren durch den Lauf
   nach Mitternacht ohnehin ausgeschlossen.
5. Regime = archiviertes `regime`; `net_gex_usd_bn == 0.0` (gerundet) → unbekannt (wie v5/v7). 19.10. fehlt, 20.10.
   (nachgeholt, IV vom Folgemorgen) bleibt ausgeschlossen.
6. Ergebnis: ein eingefrorenes Inventar (Datei, Hash, Erstellungszeit, Session, Methodenversion, je Ticker Spot,
   Schluss, Abweichung, Regime, Ausschlussgrund). Erwartet rund 50 Sessions statt 10.

## Fragen

1. Trägt die Lesart? Oder gibt es einen Mechanismus, bei dem der Spot zwar zum Schluss passt, die Rechnung aber trotzdem
   eine Session daneben liegt (z. B. OI-Stand des Snapshots, IV-Zeitpunkt)?
2. Darf die Yahoo-Phase mit der Massive-Phase gemeinsam ausgewertet werden, oder nur getrennt?
3. Ist die Erstellungszeit (birth) als Beleg der Laufzeit ausreichend (sie ändert sich bei einem Überschreiben)?
4. Muss `docs/OPTIONS.md` korrigiert werden, und wie formulieren?

Schluss: TRAGFÄHIG, TRAGFÄHIG MIT ÄNDERUNGEN oder NICHT TRAGFÄHIG.
