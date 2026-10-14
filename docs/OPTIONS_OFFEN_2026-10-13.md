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
- [x] **Plan v3/v4** (2026-10-14, Codex-Freigabe B1/B2/B3).
- [x] **B1 Schreibsperre der Skew-History** (2026-10-14, `1080a55`, Code R2 FREIGABE): gemeinsame flock-Sperre für Cron,
      Massive-Backfill und VRP-Nachrechnung, defekte History bricht ab, `backfill_skew_history.py` gelöscht, Wächter
      `verify_skew_historie_sperre.py --streng` im Gate (Mutation 22/22 Linux).
- [x] **R1c ETHA-VRP repariert** (2026-10-14, Nutzerfreigabe des Trockenlauf-Berichts): 07.–13.10. von ≈ −333 auf
      1,3–3,0; Bericht `logs/reparatur/vrp_ETHA_2026-09-30_2026-10-13_20261014T133004Z.json` (Server).
- [x] **B2 Session als Stempel und Bewertungsdatum** (2026-10-14, `326bcc8`, Code R2 FREIGABE): GEX, Key Levels,
      IV-Surface, pc_ratio; Archiv `gex_history_session/`; Health-Frische in Sessions; Seiten /key-levels und
      /dealer-positioning. Wächter `verify_gex_session.py` im Gate (Mutation 25/25).
- [ ] **B2 beobachten (15.10. morgens):** erster GEX-Lauf 22:15 UTC — Tagesbalken der Session verfügbar? (sonst Lauf rot
      → später starten), Datei `gex_history_session/2026-10-14.json`, Health „Options: GEX-Ketten“ grün.
- [ ] **B3 Rang im Cron** (Plan frei): `shared/skew_rang.py`, `rang[ticker][W]` im Snapshot, /skew und Mail lesen nur
      noch das, JS-Referenz nach Spezifikation, Wirkungsbericht Radar alt/neu. Geschätzt 4–5 h.
- [ ] **Folgeposten:** Renditen aus Schlusskursen in Mail-Kursanzeigen (`daily_report.py` ~244/~422), Sektor-Monat
      (~1273), Vol-Control-Proxy (`build_volcontrol_proxy.py:74`); Kalenderseite/`kalender-compute.js` mit
      `earnings_events.report_date`; Health meldet ausgefallenen Options-Cron erst nach drei Tagen.
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
