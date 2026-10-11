# monthly_stats, Runde 2 — Auflagen aus [Antwort 1](2026-10-11_monthly_stats_nan_antwort1.md)

Read-only. `git diff shared/cache_manager.py scripts/nightly_refresh.py`.

1. Nur endliche Monatsrenditen (`np.isfinite`), Fallzahl/Gewinnquote/Mittel/Std auf derselben Stichprobe;
   `std_dev = None` bei < 2. Probe: Monatsanfangskurs 0 im Januar 2024 → Januar zählt 2 statt 3 Jahre, JSON strikt ok.
2. `get_or_compute_monthly_stats(..., schreibfehler_werfen=True)` reicht einen gescheiterten Upsert weiter; der
   Nightly fängt ihn eigens ab und hängt ihn an `ticker_fehler` (Lauf wird rot), die übrigen Schritte des Tickers
   (Saison-Score) laufen weiter. Andere Aufrufer: keine (nur Nightly). `verify_schreiber_nummern.py` 36/36.
3. Nach dem Deploy: Nightly heute Abend (Timer 16:45 New York) erzeugt die Zeilen; ich prüfe danach lesend
   die Coverage. Andere Auditdimensionen sind gelb, nicht rot (Datumslücken ^STOXX50E/RR.L, Earnings-Coverage).

<task>Auflagen erfüllt? Freigabe?</task> **Urteil** · **Befunde** · **Auflagen**. ≤ 15 Zeilen.
