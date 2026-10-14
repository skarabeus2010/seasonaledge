# Optionen — offene Aufgaben (Stand 2026-10-13, Fortsetzung 2026-10-14)

## A. Skew-Ausreißer (Radar /skew) — läuft mit Codex
Plan + Antworten: `docs/review_prompts/2026-10-13_skew_ausreisser_*` (plan, plan_v2, phase0 + je `_antwort`).
- [x] Phase 0: fünf Ausreißer-Tage nachgerechnet (`scripts/research/skew_phase0_probe.py`) — Hauptverdacht dünne
      Wochenverfälle (wenige bepreiste Kontrakte, Volumen 4–170), Extrapolation verstärkt; Codex: Verdacht, kein Beweis.
- [x] **Trockenlauf gelaufen** (337 Ticker-Tage: 8 Ticker × 40 Tage + bekannte Fälle + Earnings-/Verfallskontrollen,
      Seed 20261013, fertig 13.10. 21:15 UTC). Erste Auswertung 14.10.: 2 von 249 Zufallstagen auffällig (> 6 MAD),
      Volumen trennt nicht, h > 0,5 deutlich häufiger auffällig (> 4 MAD: 4/24 gegen 6/205 bei Klammer),
      Live ≠ Backfill an 68/336 Tagen.
- [ ] Schwellen an „entwicklung“ ableiten, an „pruefung“ prüfen; Regelvarianten mit Abdeckung je Ticker und Rangwirkung.
- [ ] Plan v4 mit Zahlen an Codex → dann Phase 1 (gemeinsame CM-Entscheidung Live/Backfill), Phase 2 (Herkunft je
      Zeile, Qualitätsstatus), Phase 3 (Bestand unter einer Sperre), Phase 4 (Frontend „heute nicht bewertbar“,
      Aktualisierungsregel), Phase 5 (10Δ in die Historie).
- [x] Radar standardmäßig Percentile — Nutzerentscheidung 2026-10-14, live mit Paket A (`1c0412f`).

## B. Opening-Setup-Abgleich — Plan `docs/OPENING_SETUP_PLAN.md`
- [x] **Lizenz mit Massive** — erledigt (Nutzer, 2026-10-14).
- [x] **Paket A der Sofortreparaturen** (2026-10-14, `1c0412f`, Codex: Plan v2 + Code R2 FREIGABE;
      [Wirkungsbericht](review_prompts/2026-10-14_options_paket_a_wirkung.md)): RV/VRP aus `log_return` (ETHA 380,7 → 45,8 %),
      Health-Check „Kursbasis“, Earnings aus der Morgen-Mail, /skew in Percentile.
- [ ] **Plan v3 an Codex** für den nicht freigegebenen Rest:
  - R1c: ETHA-VRP-History gezielt reparieren (Reparaturmodus mit Datumsbereich und vollständigem Diff; erst nach der
    Schreibsperre).
  - R2: Session statt Lauftag für `gex_summary.date`/`pc_ratio.date` — **und** als Bewertungsdatum für DTE/T in
    `snapshot_gex_massive.py`; getrenntes Archiv, Leser `compare_flashalpha_gex`, EOD-Wächter, Frischeprüfung.
  - R3: Skew-Perzentil der Mail aus EINER Rechnung im Cron (n je Metrik, Fenster `S−W ≤ date ≤ S`, Session-Prüfung im
    Mailleser, JS-Referenz an die Spezifikation), einfarbig (`daily_report.html.j2:115`).
  - **Gemeinsame Schreibsperre (flock) für alle Schreiber der Skew-History zuerst** — inkl. `backfill_skew_history.py`.
  - Folgeposten Codex: Renditen aus Schlusskursen noch in den Mail-Kursanzeigen (`daily_report.py` ~244/~422),
    Sektor-Monat (~1273), Vol-Control-Proxy (`build_volcontrol_proxy.py:74`).
  - Kalenderseite/`kalender-compute.js` nutzen `earnings_events.report_date` mit derselben falschen Bedeutung.
- [ ] Stufe 2 IV-Dashboard aktivste Namen · Stufe 3 Vola-Lage (VIX9D/VIX3M kostenlos, ±σ mit gemessener Deckung) ·
      Stufe 4 Earnings-Vorschau (Terminquelle) · Stufe 5 Studie (optional) · später Extremlisten, SPX-Gamma `I:SPX`.
- [ ] IWM-Historienpunkt 17.08. (ATM-IV 3,35 %) — fällt unter A.
- [ ] 16 Ticker ohne normierten Punkt zur Session (DUK seit 19.08., ARRY seit 01.06.) prüfen.

## Abruf des Trockenlaufs (Server, nur lesen)
- Lauf 1: Unit `sa-skewprobe` (Start 11:16 UTC, Grenze 5 h) → `/root/skew_trockenlauf.jsonl` (Zeile `@@META@@` mit
  Stichprobe + Spot, je Fall eine Zeile `@@FALL@@{json}`), Fehler `/root/skew_trockenlauf.err`.
- Lauf 2 (Fortsetzung, wartet auf Lauf 1): Unit `sa-skewprobe2`, Skript `/root/skewprobe_fortsetzung.sh`, rechnet die
  fehlenden Fälle (`/root/skew_trockenlauf_rest.txt`, Format SYM:DATUM:MENGE) in Teilen à 25 →
  `/root/skew_trockenlauf_2.jsonl`; am Ende Zeile `FERTIG …` in `/root/skew_trockenlauf_2.err`. In Lauf 2 steht
  `menge` = „einzeln“ — die echte Menge steht in `skew_trockenlauf_rest.txt`.
- Prüfen: `systemctl is-active sa-skewprobe sa-skewprobe2`; `grep -c '@@FALL@@' /root/skew_trockenlauf*.jsonl`;
  `tail -2 /root/skew_trockenlauf_2.err`. Holen: `scp root@<VPS>:/root/skew_trockenlauf*.jsonl <scratchpad>`.
- Probe-Code: `scripts/research/skew_trockenlauf_probe.py` (im Container unter `/tmp/`).
- ⚠️ Solange einer der beiden Läufe aktiv ist: **nicht pushen** (Deploy baut den Container neu und bricht `docker exec` ab;
  `/tmp` im Container ginge verloren).
