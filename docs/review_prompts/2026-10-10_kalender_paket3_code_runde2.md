# Paket 3 (K3+K4) — Code-Review Runde 2 (Abnahme)

Runde 1: [Prompt](2026-10-10_kalender_paket3_code.md) · [Antwort](2026-10-10_kalender_paket3_code_antwort1.md) — keine Freigabe.

<task>Prüfe, ob die Befunde behoben sind und nichts Neues kaputtging. Read-only. `git diff` + neue Dateien
(`scripts/verify_kalender_fehlerweitergabe*.py`, `scripts/verify_ticker_boerse*.py`, Fixture).</task>

## Umsetzung
1. **Intraday** (P1): neue Modulliste `KALENDER_FEHLER`; ein TDOM/TDOY-Fehler trägt den Ticker dort ein, und
   `main()` endet dann **vor** der Yahoo-Toleranz mit Exit 1 (nach dem `refresh_log`-Eintrag). Kurse werden
   weiter geschrieben, Nummern aus einer gescheiterten Berechnung nicht (die Spalten bleiben dann weg).
2. **Nightly** (P1): Phase C ist jetzt die Funktion `health_check(tickers) -> dict` (Verhalten sonst
   unverändert, nur herausgezogen). Ein nicht prüfbarer Ticker → `ungeprueft` + `gescheitert`; „Alle Ticker
   vollständig“ nur ohne ungeprüfte; Ausnahme der ganzen Phase → ebenfalls gescheitert. `main()` übernimmt
   `gescheitert` in `_FEHLGESCHLAGEN` (→ Exit 1). `tickers_success` = neue Funktion `tickers_erfolgreich`
   (ohne Lücken **und** ohne ungeprüfte).
3. **`.BR`/`.LS`** (P2): Regelfälle + je eine Mutation. Ticker-Wächter 56/56, Mutationen 15/15 (zweimal).
4. **Wächter `verify_kalender_fehlerweitergabe.py`** (8 Prüfungen): führt die echten `intraday_refresh.main()`
   und `nightly_refresh.health_check()` offline aus (Stubs nur für Supabase und Yahoo): neun gültige + ein
   unbekannter Ticker → Intraday Exit 1, alle gültig → 0; Nightly: ungeprüft/gescheitert/keine
   Vollständigkeitsmeldung/Erfolgszählung 1 statt 2. Mutationstest 7/7 (zweimal), Gegenproben 2/2.
   Nicht im Deploy-Gate (braucht pandas).
5. **Deploy**: `actions/setup-python@v5` mit 3.12 vor den Wächtern (numpy 1.26.4).
6. Weiter grün: Stress 32/32 + Mutationen 29/29, Session-Stempel, Sollfälle 86/86, Nummern 86/86.

## Fragen
1. Befunde behoben? 2. Ist das Herausziehen von `health_check` verhaltensgleich (Variablen, Ausnahmepfade,
`refresh_log`-Felder)? 3. Sonst etwas vor dem Commit?

## Ausgabevertrag
**Urteil** · **Befunde** · **Antworten**. ≤ 40 Zeilen.
