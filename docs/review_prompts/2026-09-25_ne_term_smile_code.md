# Code-Abnahme: NE-Skew, Skew-Term, Term-Struktur, Smile (Commit 569d2b7)

## <task>

Prüfe `git diff 60797aa..569d2b7 -- shared/black_scholes.py scripts/compute_options_skew.py
landing/pages/skew.html landing/i18n/en.json scripts/verify_skew_laufzeiten.py
scripts/verify_session_mutation.py`.

Du hast den **Entwurf** in `docs/review_prompts/2026-09-25_ne_term_smile_entwurf.md` mit „nicht
tragfähig" bewertet und zehn Befunde gemeldet. Prüfe je Befund, ob die Umsetzung ihn behebt:

| Entwurfsbefund | Umsetzung |
|---|---|
| Fehlender Anbieter-Pick beendet den Ticker | `_enrich`: `_anbieter_werte` optional; `return None` nur ohne Anbieter UND ohne `cm_mode` |
| Neue Felder ohne `last_close` | `_laufzeiten_eigen` setzt ALLE Felder zuerst leer, rechnet nur mit `by_own` + `spot_ref` |
| Rundung des ATM-Ankers | `_gefilterte_punkte` gibt den ungerundeten Anker zurück; 574 echte Expiries bit-identisch |
| `single` / `dte30 = 30` | `iv30` nur bei `_rankbar(r)` und zwei `cm_exps`; `modus30` = `cm_mode` |
| Contango mit `term[0]` ≥ 30 Tage, Gleichstand | Punkt ≤ 14 Tage (`_KONTANGO_KURZ_MAX`), Gleichstand → `None` |
| Steigung mit einem Punkt, feste „7→180d" | ≥ 2 Laufzeiten, `term_slope_von/bis`, Frontend zeigt echte Endpunkte |
| NE-Kurve verschwindet ohne `iv30` | `renderSkewCurve` rendert jede Kurve einzeln, Farben je Serie |
| `front_provider` überschrieben | `_enrich` sichert einmal vollständig; `_anzeige_aus_ranking` ergänzt nur (`setdefault`) |
| Überlappende Delta-Fenster | `SMILE_DELTA_TOL = 0.07` (disjunkt); 25Δ-Leg behält `DELTA_TOL` |
| Testumfang | `verify_skew_laufzeiten.py`: Regression, Basis, NE-Ersatz, NE ohne Ersatz, Anbieter fehlt, Spot veraltet, Flügel fehlen, Klammer-Lücke, single, Smile-Lücke, Audit |

## Entscheidungen, die du prüfen sollst (mit Messung begründet)

1. **NE-Ersatz:** strikter nächster Verfall (dte ≥ 1); scheitert er, der nächste auswertbare bis
   10 Tage, gekennzeichnet (`skew_ne_ersatz`, Tabelle `*` + Tooltip mit Laufzeit). Messung: 13 von
   40 scheiterten am 1-Tages-Verfall an der Delta-Toleranz bei frischen Kursen (Strike-Struktur).
   Ist die Kennzeichnung ausreichend (Tooltip-Text in `skew.html::neZelle`, `TH_NE`)?
2. **ATM ohne Flügel:** `atm_from_prices` verlangt Ankerabstand ≤ min(5 %, 0,5 σ√T), auch einseitig.
   Messung auf 239 Term-Punkten: Median z = 0,11, 90. Perzentil 0,49. Varianten: „beidseitig & ≤ 5 %"
   195 Punkte, gewählte Regel 193 (kurz 30, lang 163), „wie leg_from_prices" 220 (lässt XLU 8 T.
   z = 1,66 durch). Ist 0,5 σ vertretbar?
3. **Tick-Rauschen am 1-Tages-Verfall:** ein 25Δ-Kontrakt kostet dort wenige Cent; die Rundung auf
   1 Cent kann das Vorzeichen eines kleinen Skews drehen (synthetisch gemessen: −0,09 bei erwartet
   +0,14). Reicht die Kennzeichnung der Laufzeit, oder braucht NE eine Mindestprämie der gewählten
   Kontrakte?

## Ergebnisse auf echten Daten (40 gesicherte EOD-Ketten vom 24.09., neuer Code)

| | alt | neu |
|---|---|---|
| NE-Abdeckung / Ausreißer \|NE\|>15 | 40 / 5 | 40 / 0 |
| 90-Tage-Skew / Skew-Term | 38 / 38 | 33 / 32 |
| Ausreißer \|Skew-Term\|>10 | 3 | 0 |
| Contango | 40 | 30 |
| Term-Punkte | 237 | 193 |
| Smile-30 25Δ/ATM = Tabelle | — | 38/38 |

## Werkzeug

Python: `C:/Users/HeikoSeibel/AppData/Local/Python/pythoncore-3.14-64/python.exe`. Die Wächter
schreiben nur in Temp → TMP/TEMP auf `.codex_tmp` im Arbeitsverzeichnis. Vorher
`git status --porcelain --untracked-files=no | md5sum` merken, danach vergleichen. Den Mutationstest
**nicht** ausführen. Keine Dateien ändern.

## Erwartbare Fehlalarme

- TLT/HYG u. a. verlieren lange Term-Punkte durch die Paritätsprüfung (q = 0) — bekannt, eigener TODO.
- Die History speichert keines der vier Felder (in der Entwurfsprüfung bestätigt).

## Ausgabevertrag

Zuerst Tabelle Entwurfsbefund → `behoben | unvollständig | neu kaputt`. Dann Antworten auf 1–3 (je
3–6 Zeilen). Dann neue Befunde `DATEI:ZEILE | SCHWERE | Was | Reproduktion | Vorschlag`. Exit-Codes der
drei Wächter (`verify_session_stamp`, `verify_skew_anzeige`, `verify_skew_laufzeiten`), Hash
vorher/nachher. Schluss: `FREIGABE: ja/nein` + ein Satz. Kein Lob.
