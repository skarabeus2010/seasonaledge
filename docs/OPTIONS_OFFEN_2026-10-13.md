# Optionen — offene Aufgaben (Stand 2026-10-17)

## Stand 17.10. (erledigt)
- **GEX-Abendlücke gefunden:** Yahoo liefert den Tagesbalken der Session, aber `close = None` etwa 00:00–01:00 UTC
  (Proben 17.10. 00:15/00:45); der GEX-Lauf 16.10. 00:21 UTC fiel genau hinein. Um 20:30 UTC noch vorläufiger
  Schluss (SPY 763,23 statt 763,25), ab 22:15 und ab 02:00 korrekt. Massive liefert Tagesbalken und `/prev` der
  Session nach Mitternacht New York (17.10. 07:47 UTC belegt); Aktien-Aggregate dort eng rate-limitiert (429 ab ~6
  Abrufen am Stück). Nachlauf `sa-gexnachlauf-1017` 08:00 UTC: 20/20, Archiv 16.10., Key Levels ok.
- **B3a/B3b laufen:** `rang_session = session`, 149 Ticker im Rang; History mit `rv_1m`, IV/RV-Rang `zu_kurz` (n = 1).
- **/skew überarbeitet** (Details: [OPTIONS.md](OPTIONS.md#skew-überarbeitet-2026-10-17)).

## Nächste Schritte
1. **Massive-Proben auswerten:** Timer `sa-massiveprobe` fragt in den Nächten nach den Sessions 19.10. und 20.10.
   (20:00–07:30 UTC, alle 30 min) Tagesbalken SPY/QQQ und `/prev` SPY ab → `/root/massive_abend/`. Frage: ab wann
   gibt Massive den Balken frei? Dann Spot-Regel mit Codex: GEX-Lauf als systemd-Timer nach Mitternacht New York mit
   Massive-Spot (Rate-Limit beachten) **oder** Yahoo mit Wiederholung bei `close = None`. Achtung Morgen-Mail 05:30
   UTC, falls sie GEX-Werte zeigen soll.
2. Gescheiterte Ticker zählen auf /skew je Kategorie erst, wenn der Options-Cron `coverage.failed[].cats` schreibt
   (ab Lauf 18.10.) — einmal ansehen.
3. Vanna-Vorzeichen gegen FlashAlpha (GitHub-Recherche: `aaguiar10/gflows` normiert Vanna mit ·S·σ, Charm mit ·S·T).

## Archiv: Liste für den 17.10.
1. **GEX-Abendproblem auswerten:** Proben `/root/yahoo_abend/*.json` (16.10. 20:30/22:15, 17.10. 00:15/00:45/02:00/04:30
   UTC) — was liefert Yahoo am Abend für den Tagesbalken der Session (fehlt er, `close` None, anderer Zeitstempel)?
   Dann die Spot-Regel festlegen (mit Codex). Bis dahin: Nachlauf `sa-gexnachlauf-1017` (17.10. 08:00 UTC) schreibt GEX
   + Key Levels der Session 16.10., Log `/root/gex_nachlauf.log`. GEX-Lauf vom 16.10. 00:21 UTC: alle 20 Ticker „kein
   Tagesbalken der Session“; Session 15.10. per Hand am 16.10. 07:45 UTC nachgeholt (20/20, Key Levels ok).
2. **B3a prüfen:** erster Options-Cron mit Rang (17.10. ~01:00 UTC) — `options_skew.json` hat `rang_session = session`,
   `rang` mit ~150 Tickern, keine `[rang]`-Meldungen im Workflow-Log; /skew Radar + Spalten gefüllt; Morgen-Mail
   (Mo 19.10.) zeigt P-Werte.
3. **B3b prüfen:** erster Cron mit B3b (17.10. ~01:00 UTC) — History-Zeilen tragen `rv_1m`, Snapshot `ivrv` und
   `rang_status`; /skew zeigt Spalte IV/RV (Rang „im Aufbau“) und den Block „Am Rand der eigenen Historie“.
4. Vanna-Vorzeichen gegen FlashAlpha; Folgeposten (unten).

- [x] **B3b IV/RV + neutrale Extremlisten** (16.10., Codex Plan R2 + Code R2 FREIGABE): IV/RV-Wert sofort, Rang ab 20
      Zeilen mit gespeichertem `rv_1m`; neu_rand/sprung/vorher_datum je Metrik, `rang_status`; /skew Spalte + Block.
      Mutation 44/44. [Plan v2](review_prompts/2026-10-16_options_b3b_plan_v2.md)
- [x] **Folgeposten** (16.10., `eb4af33`, Codex R2 FREIGABE): Health-Check Options-Frische in Sessions (Ausfall am
      nächsten Morgen gelb statt nach drei Tagen); Morgen-Mail-Kursreihe mit Gesamtordnung (vorher 16 von 10 567 Zeilen
      doppelt/fehlend) und Schnitt hinter dem jüngsten Kurs/Return-Widerspruch (nur ETHA betroffen).
- [x] **ETHA-Altkurse auf die neue Basis** (16.10., Nutzerfreigabe): 549 Zeilen 23.07.2024–29.09.2026 Kurse ×3,
      Volumen ÷3, `log_return` unverändert (Reverse-Split 1:3; Faktor aus Kurs/Return 2,99999999, Yahoo identisch).
      Rücklesen 0 Abweichungen, `basisabweichungen` 561/561 Paare ohne Treffer. Sicherung vorher:
      `/app/logs/reparatur/etha_basis_vorher_20261016.json` (Container).
- [ ] **Forex-Daten:** Wochenendzeilen mit kopiertem `log_return`; die Intraday-Zeile des Tages spannt zwei Tage
      (AUDUSD 16.10.: log_return −0,21 % gegen Kursverhältnis +0,61 %). Eigener Datenfehler, nicht behoben.
- [x] **B3a Skew-Rang im Cron** (16.10., Codex Code R2 FREIGABE; [Wirkung](review_prompts/2026-10-16_options_b3a_wirkung.md)):
      `shared/skew_rang.py` = `scripts/js/skew_rang_ref.js`, /skew und Mail lesen nur `rang`; Wächter `verify_skew_rang.py`
      im Gate, Mutation 22/22. Percentile-Radar ±1–2 Punkte, Mail-Perzentil Median 1 / max 11.

## A. Skew-Ausreißer (Radar /skew) — läuft mit Codex
Plan + Antworten: `docs/review_prompts/2026-10-13_skew_ausreisser_*` (plan, plan_v2, phase0 + je `_antwort`).
- [x] Phase 0: fünf Ausreißer-Tage nachgerechnet (`scripts/research/skew_phase0_probe.py`) — Hauptverdacht dünne
      Wochenverfälle (wenige bepreiste Kontrakte, Volumen 4–170), Extrapolation verstärkt; Codex: Verdacht, kein Beweis.
- [x] **Trockenlauf gelaufen** (337 Ticker-Tage: 8 Ticker × 40 Tage + bekannte Fälle + Earnings-/Verfallskontrollen,
      Seed 20261013, fertig 13.10. 21:15 UTC). Erste Auswertung 14.10.: 2 von 249 Zufallstagen auffällig (> 6 MAD),
      Volumen trennt nicht, h > 0,5 deutlich häufiger auffällig (> 4 MAD: 4/24 gegen 6/205 bei Klammer),
      Live ≠ Backfill an 68/336 Tagen.
- [x] **Auswertung + Plan v4** (16.10., Codex FREIGABE; [Plan v4](review_prompts/2026-10-16_skew_ausreisser_plan_v4.md),
      Skript `scripts/research/skew_trockenlauf_auswertung.py`): **keine belastbare Ausschlussregel** — 2 von 249
      Zufallstagen > 6 MAD; jede Rasterregel, die den Entwicklungsfall entfernt, kostet ≥ 47/123 unauffällige Tage;
      H ≤ 0,75 trifft BAC 19.03./C 18.06., ist an der Entwicklungsmenge aber nicht belegt (Kosten 5,7 %).
- [ ] **Nächster Bauschritt: Phase 1 + 2** — gemeinsame CM-Entscheidung Live/Backfill zuerst im Vergleichsbetrieb
      (vollständiges Expiry-Universum, bestehende Prüfungen + Rückfallreihenfolge, keine neue Ausschlussregel); Herkunft
      additiv in Snapshot UND History (`cm_h`, Leg-Volumen, Delta-Abstand, Klammer, Regelversion); `auffaellig` nur als
      Markierung (Grund h > 0,75 bzw. > 6 MAD mit Referenzfenster, n, Median/MAD, Version), bleibt bewertbar.
- [ ] Bei ≥ 20 markierten Fällen > 6 MAD erneut untersuchen (Anlass, keine Schwelle): neue, vorab getrennte Prüfmenge,
      unauffällige Kontrollen, Marktphasen. Phasen 3/4 (Bestand, „heute nicht bewertbar“) entfallen bis dahin; Phase 5
      (10Δ) unabhängig.
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
- [x] **B2 erster Lauf (15.10. 00:30 UTC) kontrolliert gescheitert:** Massive sperrt den Tagesbalken der Session bis
      Mitternacht New York (HTTP 403); der alte `/prev`-Abruf gab bis 13.10. die Session davor (GEX mit einem um eine
      Session veralteten Spot). Behoben (`bb70906`/`d8c1115`, Codex 4 Runden): unbereinigter Yahoo-Schluss, Nachweis
      `regularMarketTime` ≥ regulärer Sessionschluss.
- [ ] **GEX beobachten (16.10. morgens):** Lauf der Session 15.10. — `gex_history_session/2026-10-15.json`, Health
      „Options: GEX-Ketten“ grün, `key_levels.json` `gex_status: ok`.
- [x] **Radar-Quadranten einheitlich** (15.10., Nutzerhinweis + Entscheidung „Richtung + Vola“): /skew, /flows, Blog DE/EN;
      Wächter `verify_radar_quadranten.py` im Gate.
- [x] **^VIX9D, ^VIX3M, ^VIX1D onboarded** (15.10.; 3970/5095/874 Zeilen). Abgleich gegen Cboe-CSV: VIX9D 51 von 3968
      gemeinsamen Tagen > 0,01 abweichend, VIX3M 9 von 4294, VIX1D 1 von 873. Yahoo führt VIX3M 2006–2009 zusätzlich
      (Vorläufer VXV, nicht in der amtlichen Datei), Cboe VIX1D 05/2022–04/2023 zusätzlich. Für Studien: VIX3M erst ab
      09/2009 als amtlich behandeln.
- [ ] **FlashAlpha-Abgleich 15.10.:** Vanna mit umgekehrtem Vorzeichen (FA −27,7 Mrd, wir +3,7 Mrd) — Definitionsfrage
      (Dealer-Annahme/Einheit), mit FA-Methodenbeschreibung klären.
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
