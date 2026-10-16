# Code-Review B3b, Runde 2

Deine Antwort R1: `docs/review_prompts/2026-10-16_options_b3b_code_antwort1.md` (nein, ein P2, ein P3). Prompt R1:
`…_b3b_code.md`. Code uncommittet im Arbeitsbaum. Read-only, Deutsch, **FREIGABE (Code): ja/nein**.

## Zu P2: IV/RV und rv_1m nur für rankbare Tage
`compute_options_skew.py`: Snapshot-`ivrv` und History-`rv_1m` nutzen jetzt `_rankbar(t)` (cm/cm_extrap, nicht
single/noatm). Die übrige History-Rückfalllogik (`cm_ok`) ist unverändert. Test: Cron-Lauf mit `cm_mode="single"` und
gültiger `cm_iv_atm` → `ivrv` None im Snapshot, `rv_1m` None in der History-Zeile. Zwei Mutationen dazu
(`cm_mode`-Bedingung bzw. `cm_ok` zurück) werden erkannt.

## Zu P3: Leserregression und Sprachwechsel als Tests
- Mail: `skew_pctl_map` mit B3b-Zusatzfeldern (neu_rand, sprung, vorher_datum, ivrv) und `rang_status` (inkl.
  `gesperrt`) liefert dasselbe wie mit der B3a-Fixture.
- /skew: Radarpunkte und die bestehenden IV-/Skew-Rangspalten mit B3b-Zusatzfeldern + `rang_status` identisch zur
  B3a-Fixture, in drei Einstellungen (Percentile 1 J. RR×IV, Rank 3 M., Percentile 1 J. Call/Put).
- Sprachwechsel: die Seitenprobe speichert jetzt `document.addEventListener`-Hörer; mit `SA_PROBE_I18N` wird nach den
  Daten das EN-Wörterbuch aus `en.json` gesetzt und `sa:i18n-bereit` ausgelöst. Geprüft: Block englisch („At the edge
  …“, „not a signal“, „new high in the window“), kein deutscher Titel mehr, Listen unverändert, IV/RV-Tooltip englisch.
  Mutation „Sprachwechsel zeichnet den Block nicht neu“ wird erkannt.

Mutationstest jetzt **44/44**. Python-Wächter grün.
