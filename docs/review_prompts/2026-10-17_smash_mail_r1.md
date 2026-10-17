# Codex-Review: Smash Day in der Morgen-Mail (2026-10-17, Runde 1)

Nur lesen. Diff: `git diff HEAD -- shared scripts .github`.

## Nutzerentscheidung (nicht zur Diskussion)
Smash Day (Larry Williams) als Kursmuster in die Morgen-Mail, grün = Kauf-Setup, rot = Verkauf-Setup — „es geht nur um
ein Pattern“, der Prüfzeitraum muss es nicht bestätigt haben. Ergebnis der Studie (Entdeckung 2000–2023, H1/H3 je
+14 Bp auf 5 Tage, Holm-bestätigt; Prüfzeitraum 2024–09/2026 H1 +16,8 Bp p 0,024, H3 +13,4 Bp p 0,029 — gleiches
Vorzeichen, aber nicht unter der Holm-Schwelle). Muster nicht im Score.

## Änderungen
- `shared/kursmuster.py`: `smash_day(vorher, jetzt)` (Gültigkeit + Basis wie die Studie), `muster_fuer(ticker,
  kerzen, session)` (nur Aktien/ETFs, jüngste Kerze = erwartete Session, Vorkerze = direkte Vorsitzung laut
  `shared.sitzungen.vorherige`).
- `shared/daily_report.py`: `fetch_last_bar_ohlc` liest 2 Zeilen inkl. Volumen/log_return (`kerzen`), Signal-Row
  bekommt `muster` (Session aus `exchange_holidays.letzte_session(Börse des Tickers)`), Top-Auswahl und Watchlist
  übernehmen das Feld.
- Vorlage: Spalte „Muster“ nach BO (`Smash ↑` grün / `Smash ↓` rot / „—“), colspan 13 → 14, Legende mit Regel und
  Studienergebnis inkl. „im Prüfzeitraum ähnlich groß, statistisch aber nicht bestätigt“.
- Wächter `scripts/verify_kursmuster.py` (Einzelfälle, Zwilling Mail ↔ Studie an 1 499 Tagespaaren, Vorlage) im Gate;
  Mutationstest 9/9.

## Prüffragen
1. Stimmt die Regel exakt mit der Studie überein (Grenzfälle, Gültigkeit, Basis)?
2. Ist `letzte_session` zur Versandzeit (Mo–Fr 07:30 Berlin) die richtige erwartete Session für US-, XETRA- und
   andere Börsen? Was passiert am Montag (Freitagssession) und nach Feiertagen?
3. Wird irgendwo der Score, die Sortierung oder eine bestehende Spalte verändert? Mailgröße (Gmail ~102 KB)?
4. Ist die Legende sachlich korrekt (Zahlen, „nicht bestätigt“)? Fehlt ein nötiger Hinweis?
5. Kosten: eine zusätzliche Zeile je Ticker in `fetch_last_bar_ohlc` — unkritisch?

Befunde mit Datei:Zeile und Schwere, am Ende **FREIGABE** oder **KEINE FREIGABE**.
