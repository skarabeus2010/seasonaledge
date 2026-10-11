# Handelstag-Nummern — Plan v7: P2 „Schreiber nach Börsenkalender“ (Runde 7)

Stand: P1a (`4d88ac6`, `d6b683e`, `7264366`, `8f976a0`) und P1b isoliert (`109f7c5`) sind deployt.
Bestandsliste: [Antwort 2](2026-10-10_xetra_tdoy_plan_antwort2.md); Auflagen zu Schreibern: [Antwort 1](2026-10-10_xetra_tdoy_plan_antwort1.md)
Befunde 1/4/6, [Antwort 2](2026-10-10_xetra_tdoy_plan_antwort2.md) Befunde 4/9/11 + Fokus 2/4, [Antwort 4](2026-10-10_xetra_tdoy_plan_antwort4.md) A3.

<task>
Prüfe den Entwurf für P2, bevor Code entsteht. P2 = jede Stelle, die `prices.tdom`/`prices.tdoy` **schreibt**.
Nutzerentscheidung Weg A: Leser (Statistiken, Seiten, Strategien) werden erst mit P3/P4 gemeinsam umgeschaltet;
die historische Spalte wird in P5 per freigegebener Transaktion korrigiert. Read-only.
</task>

## Schreiber (gemessen)
| Schreiber | heute | geplant |
|---|---|---|
| `scripts/nightly_refresh.py:105–109` (Phase B, letzte 7 Tage) | Werte aus `preprocess()`: Yahoo-Download ohne Spalte → `groupby(year).cumcount()+1` (**Zeilenzählung**) | Nummern für die geschriebenen Zeilen aus `handelstag_nummern(daten, börse)` |
| `nightly_refresh.health_check` Lückenfüller (Auto-Fix-Upsert) | schreibt Kurszeilen **ohne** Nummern | mit Nummern |
| `scripts/intraday_refresh.py:134–180` | „letzte DB-Zeile + Kalenderschritte über die heruntergeladenen Tage“ — eine Lücke zwischen DB-Zeile und Download verschiebt alles; Fehler → Zeilen ohne Nummern + Lauf rot (P1a) | `handelstag_nummern`; keine DB-Abfrage der Vorzeile mehr |
| `scripts/backfill_new_ticker.py:39–60, 139–142` (Onboarding) | zählt entlang der Datumsliste ab der ersten Zeile; schreibt nur Werte `> 0` | `handelstag_nummern`; schreibt auch 0 (Tag vor der ersten Sitzung der Periode) |
| `scripts/fix_missing_days.py` | fügt Zeilen **ohne** Nummern ein, empfiehlt danach `backfill_tdoy` | mit Nummern |
| `scripts/backfill_tdoy.py` | Kalenderzählung (eigene Kopie), **ganze Historie**, `upsert` mit mitgelesenem `close` (Lost-Update-Risiko gegen den Nightly), von `check_db_completeness --fix` automatisch angestoßen (`:646`, `:661`, `:670`) | Siehe K3 |
| `bulk_load_supabase.py` (Repo-Wurzel) | Werte aus `preprocess()` (Zeilenzählung), Upsert der ganzen Historie | Siehe K4 |
| `shared/cache_manager.py:161/217` | schreibt `tdom_stats`/`tdoy_stats` (Statistik, nicht `prices`) | **P3/P6**, nicht hier |

## Entwurf
**K1 Eine Funktion.** Alle Schreiber berechnen die Nummern für **genau die Zeilen, die sie schreiben**, mit
`shared.exchange_holidays.handelstag_nummern(daten, get_exchange_for_holidays(ticker))` und schreiben beide
Spalten immer (auch 0). Kann die Funktion nicht rechnen (Zuordnung/Bereich), werden die Zeilen ohne Nummern
geschrieben und der Lauf ist rot (Vertrag aus P1a). Keine „Vorzeile + 1“, kein `cumcount`, keine DB-Abfrage
nach der Vorzeile.

**K2 Sofort aktiv statt hinter einem Schalter — bitte prüfen.** Begründung: Die Spalte `prices.tdoy/tdom` ist
heute schon überwiegend kalenderbasiert (gemessen XETRA: 234 464 von ~289 000 Zeilen = Kalender; der Rest
Korrektur-/Zählweisen-Drift). Ihr einziger Leser mit sichtbarer Wirkung ist der Header-Ersatz `app.js:877`
(selbst ein P4-Befund); `preprocess()` übernimmt die DB-Spalte, aber `add_tdom_columns`/`add_tdoy_columns`
überschreiben sie für alle Statistiken mit `cumcount` (Antwort 2, Frage 3). Die heutigen Schreiber erzeugen dagegen
**jede Nacht neue Drift** (SAP.DE 2026-09-07/08 beide `(5,174)`). Sofort umstellen beendet die Drift; die
Statistiken ändern sich dadurch nicht. Alternative: Schalter `TAGE_NACH_KALENDER` bis zur gemeinsamen
Umschaltung — dann wächst die Drift bis dahin weiter und P5 muss mehr korrigieren.

**K3 `backfill_tdoy.py` wird zum Prüf-/Reparaturwerkzeug mit Grenzen.** Standard = Trockenlauf (nur Bericht:
Zeilen je Jahr, getrennt TDOM/TDOY). Schreiben nur mit `--schreiben` **und** nur ab 2001, nur für Börsen mit
`kalender_status != "ungeprueft"` im betroffenen Jahr, nur die zwei Nummernspalten (kein `close` im Upsert —
`update().eq(ticker).eq(date)` in Stapeln, oder RPC aus P5). `check_db_completeness --fix` ruft es nur noch im
Trockenlauf (Empfehlung statt Ausführung). Die historische Massenkorrektur bleibt **P5** (eine Transaktion,
Nutzerfreigabe) — `backfill_tdoy` ist dafür nicht der Weg.

**K4 `bulk_load_supabase.py`**: kein Aufrufer in Repo, Workflows, Deploy (gesucht); Doku nennt es nicht mehr.
Vorschlag: löschen. Wenn es bleiben soll: Nummern über K1.

**K5 Lückenfüller und „Börse war zu“** (Antwort 1, Befund 6): Der Nightly-Health-Check wertet „Yahoo hat für
keinen der fehlenden Tage Daten“ als Schließung und meldet keinen Fehlbestand. Vorschlag: der Fall bleibt
„ungeklärt“ und erscheint im `refresh_log` als eigene Zahl (nicht als Lücke, nicht als vollständig). Gehört er in
P2 oder getrennt?

**K6 Prüfung** `scripts/verify_schreiber_nummern.py` führt jeden Schreiber offline aus (Stubs nur für Supabase und
Yahoo, Muster `verify_kalender_fehlerweitergabe.py`) und vergleicht die **tatsächlich übergebenen Datensätze** mit
`handelstag_nummern`: Nightly (Yahoo-Daten mit Lücke im Fenster), Lückenfüller, Intraday (Lücke zwischen DB-Stand
und Download, Monats-/Jahreswechsel, geschlossener Tag als Füllzeile), Onboarding (Historie ab 1. Juli, 0-Werte),
`fix_missing_days`, `backfill_tdoy` (Trockenlauf schreibt nichts; `--schreiben` vor 2001 verweigert; kein
`close` im Schreibweg), XETRA- und NYSE-Ticker. Mutationstest deterministisch mit Sperre.

## Fokusfragen
1. K2: sofort aktiv oder Schalter? Gibt es einen Leser der Spalte, den ich übersehe, für den der Wechsel jetzt
   sichtbar wird (Python, JS, SQL, Newsletter)?
2. K3: Ist `update()` je Zeile in Stapeln für ein Reparaturwerkzeug akzeptabel, oder gleich die P5-RPC?
3. K5 in P2 oder eigenes Paket?
4. Was fehlt in K6, damit ein grüner Wächter wirklich „alle Schreiber schreiben Kalendernummern“ beweist?
   (z. B. ein Schreiber, den die Bestandsliste nicht kennt)

## Ausgabevertrag
**Urteil** · **Antworten** (je ≤ 8 Zeilen, Datei:Zeile) · **Befunde** · **Auflagen vor dem Code**. ≤ 80 Zeilen.
