# Entwurf v2: unplausible Punkte in der Skew-Historie — Runde 2 (Plan)

Read-only, Repo `C:\dev\Seasonaledge`, Stand `88c02ff`. Deine Runde 1: `..._skew_ausreisser_plan_antwort1.md`.
Deutsch, Datei:Zeile, am Ende **FREIGABE (Plan): ja/nein**.

## Messbasis (eingefroren)
Live-Abruf 13.10.2026 ~12:30 MESZ, `generated 2026-10-13`, `session 2026-10-12`:
`options_skew_history.json` sha256 `789a6fa5…66cff9`, `options_skew.json` sha256 `8b9955a3…e729`.
Auswertungsregeln für alle Zahlen: Fenster `date >= 2025-10-13`, nur `cm`/`cm_extrap`; MAD **roh** (ohne 1,4826),
MAD = 0 → 0,1; Quantile linear (numpy „linear“); Rang „ohne Ausreißer“ = Zeilen mit |skew − Median| / MAD ≤ 6,
die letzte Zeile immer behalten. Ich stelle beide Dateien (Hash geprüft) und das Auswerteskript in den
Wirkungsbericht. „> 6 MAD“ heißt nur auffällig, nicht fehlerhaft — im Bericht getrennt.

## Neue Reihenfolge: erst Diagnose, dann Regel
**Phase 0 — Fälle rekonstruieren (Server, nur lesen, kein Schreiben in Dateien/DB):** ein Probeskript nutzt die
Backfill-Maschinerie (`_closes`, `_list_contracts`, `_bars`, `_plan`, `_leg_ivs`) für **einen** Tag und protokolliert
je Expiry: DTE, Spot, Kontrakte, `leg_from_prices`-Ergebnis bzw. Verwerfungsgrund, dann jede Kandidatengruppe aus
`cm_leg_kandidaten` mit w, h, interpolierten IVs und der Entscheidung von Live-Logik **und** Backfill-Logik.
Fälle: MS 16.09.2026, XLF 16.09.2026, C 18.06.2026, C 29.10.2025, GS 20.10.2025; dazu je ein unauffälliger
Vergleichstag. Für die Live-Zeilen (`own_bs`, ab 11.09.) gibt es keinen Ketten-Snapshot — die Rekonstruktion aus
Tagesbars ist eine Näherung; das wird je Fall ausgewiesen. Ergebnis: Bericht „Ursache je Fall belegt / unbelegt“.
**Erst danach** wird die Regel festgelegt (Plan v3 mit Zahlen).

**Phase 1 — gemeinsame CM-Entscheidung** (`shared/black_scholes.py`, eine Funktion `cm_entscheidung(legs_je_expiry,
regeln)` für Live und Backfill): Kandidatenreihenfolge aus `cm_leg_kandidaten`, je Gruppe Gewichtsprüfung
**h = max(0, −w, w − 1) ≤ H** (H aus Phase 0/Trockenlauf, Abstandsschutz 15 Tage bleibt), Interpolation, Endlichkeit
und IV-Bereich, bei Fehlschlag nächste Gruppe, erst dann `single`/nicht rankbar. Der Backfill lädt dafür Legs für
**alle** Gruppen der Rangliste (nicht nur drei) bzw. lädt bei Fehlschlag nach; `got[:2]` entfällt. Unterschiede der
verfügbaren Rohdaten (Backfill ±30 %, 24 Strikes) werden ausgewiesen, nicht verdeckt.

**Phase 2 — Qualitätsstatus statt harter Flügelschranke:** Herkunft je Zeile speichern (`cm_mode` original,
`cm_exps`, `cm_exp_dte`, `cm_w`, `cm_h`, Leg-IVs, `regel_version`) — auch im History-Schreiben
(`compute_options_skew.py` ~1279). Statistische Auffälligkeit wird als `auffaellig` + Grund **markiert**, aber nur
aus dem Ranking genommen, wenn eine **in Phase 0 validierte** Regel greift (z. B. h > H, Leg-Fehler). Die
Leg-Prüfung „ATM > Flügel + 3“ (`black_scholes.py` ~493, Kommentarwiderspruch zu ~130) wird in Phase 0 an
Earnings-Tagen mitgemessen; Ergebnis bestimmt, ob sie bleibt.

**Phase 3 — Bestand:** Zeilen ohne Herkunft = `nicht_pruefbar` (kein Ausschluss allein deswegen); gezielte
Rekonstruktion nur für Zeilen mit Auffälligkeit, über den Backfill-Pfad mit neuer Regel. Migration idempotent,
Backup, atomar, Ausgangshash geprüft; alle Schreiber der Datei (Cron 23:00, Backfill, Migration) über **eine**
Dateisperre (`flock` auf eine Sperrdatei neben der History) — Supervisor-Pause allein reicht nicht.

**Phase 4 — Frontend + Aktualisierung:** markierte aktuelle Session → Ticker zeigt „heute nicht bewertbar“ statt still
zu verschwinden; `MIN_NORM` unverändert; Aktualisierungsregel: ein neuerer Lauf derselben Session darf eine rankbare
Zeile durch eine nicht rankbare ersetzen, wenn die Regelversion neuer ist. Percentile als Standard bleibt
Nutzerentscheidung.

**Phase 5 — 10Δ:** `put10_iv`/`call10_iv` aus denselben CM-Stützstellen persistieren, `null` erlaubt, Rang unberührt.

**Wächter/Mutationen/Bericht:** wie von dir aufgezählt (ungerundete Originalfälle aus Phase 0, beide
Extrapolationsrichtungen, nächste Gruppe nach Fehlschlag, Earnings durch die Leg-Pipeline, Live = Backfill bei
gleichen Eingaben, Migration/Wiederholung, aktuelle Session markiert, MIN_NORM). Bericht je Ticker mit beiden
Achsen, Rank und Percentile, verschwundene Ticker.

## Prüffragen
1. Ist „erst Phase 0, dann Regel“ die richtige Gate-Reihenfolge? Reicht die Rekonstruktion aus Tagesbars für die
   Live-Fälle, oder ist sie als Beleg wertlos?
2. Ist die Phasenfolge 1–5 vollständig und richtig geschnitten (einzeln deploybar)?
3. Freigabe für Phase 0 (rein lesend)?
