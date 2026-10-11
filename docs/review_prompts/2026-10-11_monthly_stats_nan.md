# monthly_stats: NaN in std_dev verhinderte jeden Upsert für junge Ticker (DB-Audit seit 4 Wochen rot)

Read-only. Änderung: `git diff shared/cache_manager.py`.

Befund (auf dem Server lesend nachgewiesen): `_compute_monthly_stats` rechnet `month_data.std()` auch bei EINEM Jahr
→ NaN; CRWV (IPO 03/2025) und SNDK (02/2025) haben 3–4 solcher Monate. `json.dumps(..., allow_nan=False)` →
„Out of range float values are not JSON compliant", der Upsert scheitert, `get_or_compute_monthly_stats` loggte das
auf DEBUG. Folge: beide Ticker ohne monthly_stats, `check_db_completeness.py` → Coverage rot → Weekly-Audit
`db_completeness.yml` an jedem Sonntag seit mindestens 2026-09-20 rot. `std_dev` ist laut PostgREST-OpenAPI
nullable; die Tabelle wird im Frontend nicht gelesen (nur Nightly schreibt, Audit prüft).

Fix: `std_dev = None` bei < 2 Beobachtungen; Upsert-Fehler als ERROR mit Ticker geloggt.

<task>Ist der Fix korrekt und vollständig (andere Felder, die NaN/inf werden können? weitere Aufrufer?), oder fehlt
etwas, damit der Audit nächsten Sonntag grün sein kann?</task>

**Urteil** · **Befunde** · **Auflagen**. ≤ 20 Zeilen.
