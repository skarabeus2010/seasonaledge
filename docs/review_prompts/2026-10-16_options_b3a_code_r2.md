# Code-Review B3a, Runde 2

Deine Antwort R1: `docs/review_prompts/2026-10-16_options_b3a_code_antwort1.md` (nein, drei P2). Prompt R1:
`…_b3a_code.md`. Code uncommittet im Arbeitsbaum. Read-only, Deutsch, **FREIGABE (Code): ja/nein**.

## Umsetzung
1. **Duplikate sperren den ganzen Ticker + Meldung.** `shared/skew_rang.py`: `_normiert(arr, session)` = alle
   normierten Zeilen mit gültigem Datum bis S; ein doppeltes Datum darin → `rang_ticker` None für jedes Fenster, in
   `rang_gesamt` fehlt der Ticker ganz. Neu `pruefe_ticker(arr, session)` und `rang_gesamt(…, meldungen)`; der Cron
   druckt die Meldungen (`[rang] TICKER: doppelte Daten: …`). JS-Referenz gleich (Duplikat irgendwo bis S → null).
2. **Datum validiert statt abgeschnitten.** `datum_gueltig(d)`: genau `YYYY-MM-DD` und echtes Kalenderdatum
   (`date.fromisoformat(d).isoformat() == d`); Zeitstempel und „2026-08-99“ zählen nicht und werden gemeldet
   („n Zeile(n) mit ungültigem Datum“). JS-Referenz: Regex + Rückwandlung über `Date.UTC`.
3. **Tabellenanbindung geprüft.** Die Seitenprobe wertet jetzt die Spalten IV-Rang (Spalte 3) und Skew-Rang (Spalte 5)
   aus: Percentile/Rank, 1 J./3 M., Ticker ohne Rang „—“, `rang_session ≠ session` → „—“, Altdatei ohne `rang` → „—“;
   die Fixture hat einen eigenen `skew`-Rang mit anderen Werten als `iv`.

Weitere Fälle aus deiner Liste: verschiedene gültige Stichprobenumfänge je Metrik (rr 25, skew 22) + Mutation
„gemeinsames n“; Duplikat nur bei S−100 (Ticker fehlt ganz, Meldung) + Mutation „sperrt nur das Fenster“; ungültiges
Datum hebt 19 nicht auf 20 + Meldung; **Abbruch zwischen History- und Snapshot-Schreiben** (Snapshot-Schreiben wirft:
History neu mit der Session, alter Snapshot unverändert und in sich konsistent).
Mutationstest **22/22**. Live-History: weiter 150 Ticker, Python = JS, keine Meldungen.

Zu deinen Hinweisen ohne Befund: History-only-Ticker erscheinen nur unter „Alle“ (Kategorie fehlt) — bewusst so;
Altdatei ohne `rang` zeigt den allgemeinen Ladehinweis — vorübergehend bis zum ersten Cron-Lauf nach dem Deploy.
