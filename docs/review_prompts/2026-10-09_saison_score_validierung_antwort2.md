Reading additional input from stdin...
OpenAI Codex v0.160.1
--------
workdir: C:\dev\Seasonaledge
model: gpt-6-astra
provider: openai
approval: never
sandbox: read-only
reasoning effort: medium
reasoning summaries: none
session id: 01a120b7-03f4-7921-a42a-b208d520f02a
--------
user
# Review VOR dem Lauf: Validierung Saison-Score — Runde 2

Repo `C:\dev\Seasonaledge`, HEAD 7e46729. Nur lesen, **`--lauf` NICHT ausführen**. Vorgeschichte: `..._validierung_runde1.md`
+ Antwort. Antwort auf Deutsch, je Befund Schwere + Datei:Zeile + Fall + Änderung; am Ende genau eine Zeile
`FREIGABE: ja` oder `FREIGABE: nein`.

## Korrekturen zu R1 (Commit 28a58a1, Protokoll 7e46729)
1. **Gültigkeit je Kennzahl getrennt:** dieselben 2000 Jahresziehungen; `bootstrap` zählt Verwerfungen je Kennzahl,
   der gepaarte Vergleich nur Ziehungen mit Score UND Vergleichsscore; Auswertbarkeit je Kennzahl (> 5 % → nicht
   auswertbar). Im Protokoll unter `gueltigkeit`.
2. **Skript festgeschrieben:** `skript_sha256` + `parameter` im Protokoll; `--lauf` verweigert bei abweichendem Skript,
   Parameter, Kern oder Daten. Protokoll und Skript sind committet (28a58a1, 7e46729); der Kern ist b7b01da unverändert.
3. **Nicht auswertbar ≠ nein:** `rangzusammenhang = null`, Konsole „nicht auswertbar"; gepaart mit eigenem Status.
4. **Positivrate:** je Reihe k/n Ziel > 0, Mittel der Raten über die Reihen (gleich gewichtet), explorativ die Rate
   im obersten Score-Quintil je Reihe; Abschnitt B ebenfalls.

Hinweis: die D3-Betriebsfunktionen liegen jetzt in `shared/saison_score_betrieb.py` (nicht Gegenstand), damit der
Rechenkern exakt der freigegebene Stand bleibt.
codex
Ich prüfe die Änderungen und das Runde-1-Protokoll am angegebenen Stand ausschließlich lesend. `--lauf` führe ich nicht aus.
exec
"C:\\Program Files\\PowerShell\\7\\pwsh.exe" -Command "git status --short; git rev-parse HEAD; rg --files -g AGENTS.md -g '*validierung*' -g '*runde1*' -g '*saison*'" in C:\dev\Seasonaledge
 succeeded in 1049ms:
warning: unable to access 'C:\Users\HeikoSeibel/.config/git/ignore': Permission denied
warning: unable to access 'C:\Users\HeikoSeibel/.config/git/ignore': Permission denied
 M scripts/nightly_refresh.py
?? docs/review_prompts/2026-10-09_saison_score_validierung_antwort2.md
?? docs/review_prompts/2026-10-09_saison_score_validierung_runde2.md
?? scripts/sql/scanner_saison_score_2026_10.sql
?? shared/saison_score_betrieb.py
7e46729e91f7ef969dce74e76432014031a7a975
shared\saison_score.py
shared\saison_score_betrieb.py
docs\AGENTS.md
docs\growth\2026-06-21_schlechtester-dax-monat-saisonalitaet_distribution.md
docs\review_prompts\2026-10-08_plain_vanilla_runde1_antwort.md
docs\review_prompts\2026-10-08_plain_vanilla_1b_code_runde1.md
docs\review_prompts\2026-10-08_plain_vanilla_1a_code_runde1.md
docs\review_prompts\2026-10-07_wahlen_blog_runde1.md
docs\review_prompts\2026-10-07_wahlen_1b2_runde1.md
docs\review_prompts\2026-10-07_wahlen_1b1_runde1.md
docs\review_prompts\2026-10-07_strategien_runde1.md
docs\review_prompts\2026-10-07_polymarket_seite_runde1_antwort.md
docs\review_prompts\2026-10-07_polymarket_seite_runde1.md
docs\review_prompts\2026-10-07_en_slugs_runde1.md
docs\review_prompts\2026-10-06_wahlen_code_runde1.md
docs\review_prompts\2026-09-30_seo_phase1_runde1.md
docs\review_prompts\2026-09-30_seo_phase1b_code_runde1.md
docs\review_prompts\2026-09-30_en_jsonld_code_runde1.md
docs\review_prompts\2026-09-29_nightly_timer_runde1.md
docs\review_prompts\2026-09-29_intraday_timer_runde1.md
docs\review_prompts\2026-10-09_saison_score_kern_antwort1.md
docs\review_prompts\2026-10-09_saison_score_anomalie_plan_v3.md
docs\review_prompts\2026-10-09_saison_score_anomalie_plan_v2.md
docs\review_prompts\2026-10-09_saison_score_anomalie_plan_antwort3.md
docs\review_prompts\2026-10-09_saison_score_anomalie_plan_antwort2.md
docs\review_prompts\2026-10-09_saison_score_anomalie_plan_antwort1.md
docs\review_prompts\2026-10-09_saison_score_anomalie_plan.md
docs\review_prompts\2026-10-09_anomalie_utc_code_runde1.md
docs\review_prompts\2026-10-09_saison_score_validierung_antwort1.md
docs\review_prompts\2026-10-09_saison_score_kern_runde2.md
docs\review_prompts\2026-10-09_saison_score_kern_runde1.md
docs\review_prompts\2026-10-09_saison_score_kern_antwort2.md
docs\review_prompts\2026-10-09_saison_score_validierung_runde1.md
docs\review_prompts\2026-10-09_saison_score_validierung_antwort2.md
docs\review_prompts\2026-10-09_saison_score_validierung_runde2.md
docs\review_prompts\2026-10-09_streamlit_aus_mails_ohne_ampel_runde1.md
docs\review_prompts\2026-10-09_stress_ampel_code_runde1.md
scripts\research\vol_saisonalitaet.py
scripts\research\saison_score_validierung_protokoll.json
scripts\research\saison_score_validierung.py
landing\pages\vola-saisonalitaet.html
landing\pages\ki-saisonalitaet.html
scripts\sql\scanner_saison_score_2026_10.sql
scripts\verify_saison_score.py
landing\js\saison-score.js
scripts\research\out\BERICHT_etf_saisonalitaet.md
landing\data\vol_saisonalitaet.json
blog\posts\2026-06-14_google-juli-saisonalitaet.md
blog\posts\2026-05-14_dax-vs-sp500-saisonalitaet.md
blog\posts\2026-03-30_outlier-filter-saisonalitaet.md
blog\posts\2026-03-27_was-ist-saisonalitaet.md
blog\posts\2026-03-27_april-saisonalitaet-sp500.md
blog\posts\2026-06-27_zweite-jahreshaelfte-h2-saisonalitaet.md
blog\posts\2026-06-15_schlechtester-dax-monat-saisonalitaet.md
blog\posts\2026-07-15_qqq-truepath-ki-saisonalitaet.md
blog\posts\2026-07-31_sektor-etf-saisonalitaet-april-november-dezember.md
raw\articles\2026-07-10_saisonalitaet-x-flows-moat.md
scripts\video\scripts\qqq-truepath-ki-saisonalitaet.json
scripts\js\probe_saison_score.js
scripts\js\probe_vola_saison.js

exec
"C:\\Program Files\\PowerShell\\7\\pwsh.exe" -Command 'Get-Content docs/AGENTS.md; Get-Content docs/review_prompts/2026-10-09_saison_score_validierung_runde1.md; Get-Content docs/review_prompts/2026-10-09_saison_score_validierung_antwort1.md; git show --stat 28a58a1; git show --stat 7e46729' in C:\dev\Seasonaledge
 succeeded in 794ms:
# SeasonAlpha-Agenten - Einsatz-Anleitung

> �bersicht aller Subagenten (`.claude/agents/`), wann man welchen einsetzt, der
> Wachstums-Flywheel und ein Automatisierungs-Vorschlag (was ohne Eingreifen l�uft).
> Stand: 2026-06-15.

## Die 8 Agenten im �berblick

| Agent | Zweck | Trigger (Beispiele) | Output | Modell |
|---|---|---|---|---|
| **blogger** | SEO-Blog-Artikel DE+EN mit echten Charts schreiben | "schreib einen Blog", "Artikel �ber X", "Daten-Studie" | `blog/posts/` (+ `en/`) | opus |
| **saisonalitaet-scout** | Web nach Saisonalit�ts-Forschung scannen  Blog-Ideen | "was gibt's Neues zu Sell in May", "Research-Radar" | `docs/research-radar/` | sonnet |
| **seo-experte** | SEO-Strategie/Audit (technical, E-E-A-T, Backlinks) | "SEO-Audit", "warum ranken wir nicht", "Backlink-Strategie" | Audit/Plan-Reports | opus |
| **daten-auditor** | Supabase-Daten auf Frische/Vollst�ndigkeit pr�fen | "ist die DB aktuell", "fehlen Ticker", "Daten-Audit" | Ampel-Reports | sonnet |
| **wachstum-distributor** ?neu | Content-Distribution (Reddit/Social/Outreach) + **einbettbare Charts mit Backlink** anbieten  Backlinks | "verteile den Post", "Outreach f�r die DAX-Studie", "Chart-Embed anbieten", "Backlink-Check" | `docs/growth/._distribution.md` + `backlinks.md` | opus |
| **frontend-qa** ?neu | 30+ Pages crawlen: tote Links, i18n, hreflang, Meta, A11y | "QA das Frontend", "tote Links pr�fen", "i18n-Check" | `docs/qa/._frontend_qa.md` | sonnet |
| **seo-seiten-bauer** ?neu | Daten-reiche Ticker-/Themen-Seiten f�r Long-Tail bauen | "SEO-Seite f�r AAPL", "programmatic SEO skalieren" | `seo/` / `landing/pages/` | opus |
| **gsc-analyst** ?neu | GSC/GA4 auswerten  priorisierte To-dos f�r blogger/seo-experte | "was als N�chstes schreiben", "GSC auswerten", "Striking-Distance" | `docs/growth/._gsc_priorities.md` | sonnet |

Aufruf: per Agent/Task-Tool mit dem Agent-Namen, oder die Trigger-Phrasen im Chat.

## Der Wachstums-Flywheel (Reihenfolge)

Die Agenten greifen ineinander - so dreht sich die Wachstums-Schleife:

```
  saisonalitaet-scout        blogger              wachstum-distributor    [DU postest]
  (findet Forschung/Hook)     (schreibt Studie)     (Reddit/Social/Outreach)   (Accounts/Beziehungen)
                                                                                  �
        �                                                                          
  gsc-analyst   ����������������������������������������������������������  Reichweite/Backlinks
  (misst, was wirkt  priorisiert n�chste Themen)
```

**Quer dazu (laufend):**
- **seo-experte** - setzt die Strategie / macht Audits (alle paar Wochen).
- **frontend-qa** - h�lt die 60+ Pages technisch sauber (w�chentlich).
- **seo-seiten-bauer** - skaliert den Long-Tail mit echten Daten-Seiten (gezielt, mit Review).
- **daten-auditor** - stellt sicher, dass die Datenbasis stimmt (l�uft via Cron).

**Kern-Idee:** Die alten Agenten *erzeugen* Wert (Content/Daten), die neuen *verteilen* ihn
(distributor), *messen* ihn (gsc-analyst), *skalieren* ihn (seo-seiten-bauer) und *sichern die
Qualit�t* (frontend-qa). Das schlie�t die L�cke zwischen "guter Content" und "0 Backlinks/Klicks".

## Entscheidungs-Tabelle - "Ich will ."

| Ich will . | Agent |
|---|---|
| einen Artikel/eine Daten-Studie schreiben | **blogger** |
| wissen, was es Neues in der Forschung gibt | **saisonalitaet-scout** |
| einen frischen Post verbreiten / Backlinks ansto�en | **wachstum-distributor** |
| wissen, was ich als N�chstes schreiben/optimieren soll | **gsc-analyst** |
| pr�fen, ob das Frontend sauber ist (Links/i18n/SEO-Tags) | **frontend-qa** |
| viele Ticker-Seiten f�r Long-Tail-Rankings | **seo-seiten-bauer** |
| eine SEO-Gesamtstrategie / einen Audit | **seo-experte** |
| wissen, ob die Daten/DB stimmen | **daten-auditor** |

## Automatisierungs-Vorschlag (ohne dein Eingreifen)

Was als Hintergrund-Routine laufen kann vs. was on-demand bleibt:

| Agent | Modus | Kadenz | Mensch n�tig? |
|---|---|---|---|
| daten-auditor + Kalender-Pr�fagent | **l�uft schon** - Cron `db_completeness.yml` | w�chentl. So 05:00 UTC | nein (Mail bei Problem) |
| saisonalitaet-scout | **l�uft schon** - Cloud-Routine | monatlich | nein (Digest) |
| **frontend-qa** | Cloud-Routine (neu, vorgeschlagen) | w�chentlich (So) | nein (nur Report) |
| **gsc-analyst** | Cloud-Routine (neu, vorgeschlagen) | monatlich (1.) | CSV-Export bereitstellen |
| **wachstum-distributor** | Cloud-Routine (neu, vorgeschlagen) | w�chentlich (Fr) | **ja** - Posten bleibt manuell |
| seo-experte | on-demand (+ opt. Quartals-Audit) | quartalsweise | nein (Report) |
| seo-seiten-bauer | **on-demand** (Review vor Publish!) | manuell | ja (Thin-Content-Schutz) |
| blogger | on-demand (+ opt. monatl. Entwurf) | manuell | ja (Freigabe) |

**Cloud-Routinen einrichten:** �ber `/schedule` (Cloud-Agenten = isolierte Sessions, NICHT lokale
Crons). Empfohlene erste drei:
1. **frontend-qa** w�chentlich So (nach `db_completeness`)  QA-Report.
2. **gsc-analyst** monatlich am 1.  Priorit�ten-Report (sobald GSC-Export bereitliegt).
3. **wachstum-distributor** w�chentlich Fr  Distributions-Pakete f�r neue Posts der Woche.

> Hinweis: Cloud-Routinen laufen in Anthropics Cloud (eigener git-Checkout), ohne Zugriff auf
> deinen lokalen Rechner. Posten auf Social/Reddit bleibt aus API-/Account-Gr�nden manuell -
> die Agenten liefern versandfertige Entw�rfe.

## Wichtige Grenzen (ehrlich)
- **wachstum-distributor** postet NICHT selbst (keine Social-/Reddit-APIs)  bereitet Entw�rfe vor.
- **gsc-analyst** braucht GSC-/GA4-Daten (CSV-Export in `docs/growth/gsc_export/` oder sp�ter API).
- **seo-seiten-bauer** erzeugt nur Seiten �ber der Daten-Tiefe-Schwelle (sonst wieder Thin-Content).
- Agenten committen/deployen **nicht ungefragt** - Review/Freigabe bleibt bei dir.
# Review VOR dem Lauf: Validierungsskript + Protokoll Saison-Score (D5) - Runde 1

Repo `C:\dev\Seasonaledge`. Nur lesen, **nichts ausf�hren, was `--lauf` startet** - das Ergebnis darf erst nach deiner
Freigabe entstehen (sonst w�re jede Korrektur am Skript eine Entscheidung nach Ansicht des Ergebnisses).
Antwort auf Deutsch, je Befund Schwere + Datei:Zeile + Fall + �nderung; am Ende genau eine Zeile `FREIGABE: ja` oder
`FREIGABE: nein`.

Gegenstand: `scripts/research/saison_score_validierung.py` und das damit geschriebene
`scripts/research/saison_score_validierung_protokoll.json` (Commit b7b01da = Rechenkern, freigegeben). Ma�stab:
Plan v2 Abschnitt D5 + v3 "Zu Befund 3" (`docs/review_prompts/2026-10-09_saison_score_anomalie_plan_v2.md`, `_v3.md`).

Bitte pr�fen, ob das Skript genau das festgelegte Protokoll rechnet:
- Manifest (43 Reihen: 5 Snapshot + Research-Cache ohne SPY/QQQ), Abschnitt A 2010-2025, jeder 5. Handelstag,
  Abschnitt B ^GSPC/^DJI 1960-2009 getrennt.
- Ziel: Rendite as_of  letzte Kurszeile = as_of + 30 KT mit derselben Endpunkt-/L�ckenregel, nur ausgereift.
- Auswertbarkeit (= 100 Beobachtungen, = 8 Jahre, nicht konstant), Universum einmal fest.
- Prim�r: Mittel der Spearman je Reihe (gleich gewichtet), Score (`score_roh`) vs. Ziel; Bootstrap �ber
  Kalenderjahre, dieselben Jahre f�r alle Reihen, 2000 Ziehungen, Seed 20261009, Ziehungen mit undefinierter Reihe
  verworfen und gez�hlt, > 5 %  nicht auswertbar, Perzentilintervall.
- Gepaart: Score vs. 5�(B1+B2) auf denselben Tagen/Ziehungen; explorativ B1-B4, Quintile, Abschnitt B.
- Schutz: `--lauf` verweigert bei abweichendem Kern- oder Datenhash.
Besonders: Werden mehrfach gezogene Jahre korrekt mehrfach gez�hlt? Ist `score_roh` (ungerundet) statt `score`
richtig? Ist die Spearman-Implementierung (R�nge mit Mittelwert bei Gleichstand, dann Pearson) korrekt? Wird das
Ziel dem Kalenderjahr von as_of zugeordnet (Dezember-Ziele ragen ins Folgejahr)? Fehlt etwas, das nach dem Lauf
nicht mehr ohne Verdacht nachgezogen werden kann?
# Codex-Antwort (Schlussantwort; Rohprotokoll nicht im Repo)

Nur lesend gepr�ft; kein Validierungslauf gestartet, keine Dateien ge�ndert.

1. **Hoch - [saison_score_validierung.py:140](C:/dev/Seasonaledge/scripts/research/saison_score_validierung.py:140): Explorative Kennzahlen beeinflussen den prim�ren Test.**  
   **Fall:** Ist beispielsweise B3 in einer gezogenen Stichprobe konstant, verwirft `any(...)` die gesamte Ziehung, obwohl Score und Ziel f�r jede Reihe definiert sind. Dadurch �ndern sich prim�res Intervall und Verwerfungsanteil aufgrund explorativer Bausteine. Auch der Vergleichsscore wirkt als zus�tzlicher Filter.  
   **�nderung:** Dieselben 2000 Jahresziehungen verwenden, aber G�ltigkeit getrennt bestimmen: prim�r anhand Score/Ziel, gepaart anhand beider Scores/Ziel, explorativ je Baustein. Verwerfungen und Auswertbarkeit getrennt berichten; diese Regel vorab protokollieren.

2. **Hoch - [saison_score_validierung.py:167](C:/dev/Seasonaledge/scripts/research/saison_score_validierung.py:167) und [saison_score_validierung.py:185](C:/dev/Seasonaledge/scripts/research/saison_score_validierung.py:185): Die Validierungslogik selbst ist nicht festgeschrieben.**  
   **Fall:** Commit `b7b01da` enth�lt weder Validierungsskript noch Protokoll; beide sind unversioniert. Gepr�ft werden ausschlie�lich Kern- und Datenhashes. �nderungen beispielsweise an Seed, Raster oder Bootstrap passieren die Sperre. Die entsprechenden JSON-Vorgaben werden beim Lauf auch nicht eingelesen oder gegen die Konstanten gepr�ft.  
   **�nderung:** Vor dem Lauf das gepr�fte Validierungsskript versionieren und seinen Hash im Protokoll festhalten und pr�fen. Auswertungsparameter aus dem Protokoll beziehen oder vollst�ndig auf �bereinstimmung pr�fen. Das endg�ltige Protokoll ebenfalls versionieren.

3. **Mittel - [saison_score_validierung.py:229](C:/dev/Seasonaledge/scripts/research/saison_score_validierung.py:229) und [saison_score_validierung.py:237](C:/dev/Seasonaledge/scripts/research/saison_score_validierung.py:237): "Nicht auswertbar" wird als negatives Ergebnis ausgegeben.**  
   **Fall:** Bei mehr als 100 verworfenen Ziehungen steht zwar `auswertbar=false` im JSON, gleichzeitig aber `rangzusammenhang=false`; die Konsolenausgabe meldet ausdr�cklich "nein". Das verwechselt fehlende Auswertbarkeit mit einem auswertbaren negativen Befund.  
   **�nderung:** Bei �berschreiten der Grenze `rangzusammenhang=null` und ausdr�cklich "nicht auswertbar" ausgeben. F�r den gepaarten Vergleich ebenfalls einen eigenen Auswertbarkeitsstatus vorsehen.

4. **Mittel - [saison_score_validierung.py:217](C:/dev/Seasonaledge/scripts/research/saison_score_validierung.py:217): Die vorgesehene Positivrate fehlt.**  
   **Fall:** D5 nennt "Immer positiv" als Basis der Positivrate. Ausgegeben werden lediglich Korrelationen und mittlere Quintilrenditen; weder positive Ziele noch deren Anteil werden berichtet.  
   **�nderung:** Vorab die Positivrate als Anteil `ziel > 0` auf denselben Bewertungstagen festhalten und mindestens je Reihe mit Z�hler und Nenner ausgeben. Eine etwaige Aggregation ebenfalls vor dem Lauf definieren.

Die ausdr�cklich hervorgehobenen Punkte sind ansonsten korrekt: Jahresmehrfachziehungen vervielfachen die Beobachtungen tats�chlich; verwendet wird `score_roh`; `rank().corr(rank())` berechnet Mittelr�nge und anschlie�end Pearson. Dezember-Ziele bleiben dem Jahr von `as_of` zugeordnet. Universum und Mindestanforderungen werden einmal auf den Originalbeobachtungen bestimmt. Abschnitt B bleibt getrennt.

Das Manifest enth�lt genau 43 Reihen; alle 43 Datenhashes und drei Kernhashes stimmen aktuell �berein. Endpunkt-, Reife- und L�ckenpr�fung entsprechen dem freigegebenen Kern einschlie�lich der sp�ter dokumentierten B�rsentoleranz von **7 Kalendertagen**. Das Raster beginnt jeweils beim ersten vorhandenen Handelstag im Abschnitt und nimmt anschlie�end jeden f�nften.

FREIGABE: nein
commit 28a58a1abc15b2ca42d121813fe9fae385b90378
Author: Heiko Seibel <seibel@bernstein-bank.com>
Date:   Fri Oct 9 14:49:45 2026 +0200

    research(saison-score): Validierungsskript D5 (vor dem Lauf, nach Codex-Prüfung R1)
    
    Gültigkeit je Kennzahl getrennt (eine konstante Explorativ-Kennzahl verwirft keine Ziehung des
    Primärtests), Skript-Hash und Parameter im Protokoll und beim Lauf geprüft, „nicht auswertbar“
    als null statt „nein“, Positivrate als Basis „immer positiv“ ergänzt. Noch KEIN Lauf.
    
    Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>

 ...2026-10-09_saison_score_validierung_antwort1.md |  25 ++
 .../2026-10-09_saison_score_validierung_runde1.md  |  25 ++
 scripts/research/saison_score_validierung.py       | 300 +++++++++++++++++++++
 3 files changed, 350 insertions(+)
commit 7e46729e91f7ef969dce74e76432014031a7a975
Author: Heiko Seibel <seibel@bernstein-bank.com>
Date:   Fri Oct 9 14:50:11 2026 +0200

    research(saison-score): Validierungsprotokoll festgeschrieben (vor dem Lauf)
    
    Kern b7b01da, Skript und 43 Datenreihen per SHA-256, Parameter wie im Skript. Noch KEIN Lauf;
    Codex prüft Skript und Protokoll vorher (Runde 2).
    
    Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>

 .../saison_score_validierung_protokoll.json        | 247 +++++++++++++++++++++
 1 file changed, 247 insertions(+)

exec
"C:\\Program Files\\PowerShell\\7\\pwsh.exe" -Command 'Get-Content scripts/research/saison_score_validierung.py; Get-Content scripts/research/saison_score_validierung_protokoll.json' in C:\dev\Seasonaledge
 succeeded in 642ms:
#!/usr/bin/env python3
"""
saison_score_validierung.py - historische Walk-forward-Auswertung des Saison-Scores NACH der Methodenrevision
(Plan v2/v3, Abschnitt D5, Codex-Freigabe 2026-10-09).

Ausdr�cklich KEIN Best�tigungstest: die Jahre 2010-2025 sind durch die Methodik-Berichte vom 08.10.2026 bereits
angesehen. Die prospektive Best�tigung l�uft �ber das unver�nderliche Protokoll `saison_score_protokoll` (fr�hestens
2027-10). Aussage danach nur: "Rangzusammenhang in der historischen Auswertung ja/nein" + Zahlen. Die Bullish/Bearish-
Etiketten kehren aufgrund dieses Laufs NICHT zur�ck.

Zwei Schritte:
    py -3.14 scripts/research/saison_score_validierung.py --protokoll --snapshot <pv_kurse>
        schreibt scripts/research/saison_score_validierung_protokoll.json (Codeversion = Git-Commit + SHA-256 der
        Rechenkern-Dateien, SHA-256 jeder Datenreihe, Manifest, Raster, Seed, Regeln). Verlangt saubere Kern-Dateien.
    py -3.14 scripts/research/saison_score_validierung.py --lauf
        rechnet NUR, wenn Kern und Daten exakt dem Protokoll entsprechen; schreibt ..._ergebnis.json.

Festgelegt (vor dem Lauf, hier im Code und im Protokoll):
  * Manifest: ^GSPC, ^DJI, ^GDAXI, SPY, QQQ (Snapshot) + alle Reihen in scripts/research/.cache au�er SPY/QQQ.
  * Abschnitt A: jeder 5. Handelstag 2010-01-01 . 2025-12-31; Abschnitt B (getrennt): ^GSPC, ^DJI 1960 . 2009.
  * Ziel: Rendite vom Schluss am as_of bis zur letzten Kurszeile = as_of + 30 KT - gleicher Vertrag wie die
    Fenster (Endpunkt = T Tage vor dem Ziel, keine L�cke > T); nur ausgereifte Ziele (letzte Kurszeile = as_of + 30).
  * Auswertbar: = 100 Bewertungstage mit Score und Ziel in A, auf = 8 Kalenderjahre verteilt, Score und Ziel nicht
    konstant. Universum einmal auf den Originaldaten bestimmt, dann fest.
  * Prim�r (einziger Test): Mittel der Spearman-Korrelationen je Reihe (gleich gewichtet) zwischen `score_roh` und
    Ziel, Abschnitt A. 95-%-Intervall: Block-Bootstrap �ber Kalenderjahre (dieselben gezogenen Jahre f�r alle Reihen,
    mit Zur�cklegen), 2000 Ziehungen, Seed 20261009, Perzentilintervall. Ziehung mit einer undefinierten Reihe
    (< 10 Beobachtungen oder konstant) wird VERWORFEN und gez�hlt; > 5 % verworfen  "nicht auswertbar".
  * Sekund�r, gepaart (dieselben Tage, dieselben Ziehungen): Score vs. 5 � (B1 + B2) - Differenz der Mittel.
  * Explorativ: B1-B4 einzeln, Quintile je Reihe (Mittelrang bei Gleichstand), Abschnitt B.
  * G�ltigkeit je Kennzahl GETRENNT (Codex vor dem Lauf): dieselben 2000 Jahresziehungen, aber eine Ziehung wird f�r
    den Prim�rtest nur nach Score/Ziel verworfen, f�r den gepaarten Vergleich nach beiden Scores/Ziel, explorativ je
    Baustein - eine konstante Explorativ-Kennzahl ver�ndert den Prim�rtest nicht. Verwerfungen getrennt berichtet;
    �ber 5 %  diese Kennzahl "nicht auswertbar" (null, nicht "nein").
  * Positivrate (Basis "immer positiv"): je Reihe k/n der Ziele > 0 auf denselben Bewertungstagen, dazu das Mittel
    der Raten �ber die Reihen (gleich gewichtet) und explorativ die Rate im obersten Score-Quintil je Reihe.
  * Das Protokoll h�lt den SHA-256 dieses Skripts fest; `--lauf` verweigert bei abweichendem Skript, Kern, Daten
    oder Parameter.
"""
from __future__ import annotations
import datetime as dt
import hashlib
import json
import pathlib
import subprocess
import sys

import numpy as np
import pandas as pd

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from shared import saison_score as SS  # noqa: E402

PROTOKOLL = REPO / "scripts/research/saison_score_validierung_protokoll.json"
ERGEBNIS = REPO / "scripts/research/saison_score_validierung_ergebnis.json"
KERN = ["shared/saison_score.py", "landing/js/saison-score.js", "shared/calculations.py"]
SKRIPT = "scripts/research/saison_score_validierung.py"
SNAP = {"^GSPC": "_GSPC.json", "^DJI": "_DJI.json", "^GDAXI": "_GDAXI.json", "SPY": "SPY.json", "QQQ": "QQQ.json"}
CACHE = REPO / "scripts/research/.cache"
SEED = 20261009
ZIEHUNGEN = 2000
A = ("2010-01-01", "2025-12-31")
B = ("1960-01-01", "2009-12-31")
B_REIHEN = ["^GSPC", "^DJI"]
RASTER = 5
MIN_BEOB, MIN_JAHRE, MIN_BEOB_ZIEHUNG = 100, 8, 10
MAX_VERWORFEN = 0.05


PARAMETER = {"seed": SEED, "ziehungen": ZIEHUNGEN, "abschnitt_a": list(A), "abschnitt_b": list(B), "b_reihen": B_REIHEN,
             "raster": RASTER, "min_beob": MIN_BEOB, "min_jahre": MIN_JAHRE, "min_beob_ziehung": MIN_BEOB_ZIEHUNG,
             "max_verworfen": MAX_VERWORFEN, "horizont_kt": 30}


def sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def manifest(snap: pathlib.Path) -> dict:
    m = {t: snap / f for t, f in SNAP.items()}
    for p in sorted(CACHE.glob("*.json")):
        if p.stem not in ("SPY", "QQQ"):
            m[p.stem] = p
    return m


def lade(p: pathlib.Path):
    rows = json.loads(p.read_text())
    return [r["date"] for r in rows], [r["close"] for r in rows]


def ziel(daten, closes, ticker, as_of):
    """Rendite as_of  letzte Kurszeile = as_of + 30 KT, gleicher Vertrag wie die Fenster des Scores."""
    T = SS.TOLERANZ[SS.marktklasse(ticker)]
    ds, cs = SS.bereinigen(daten, closes)
    i = ds.index(as_of)
    z = (dt.date.fromisoformat(as_of) + dt.timedelta(days=30)).isoformat()
    if ds[-1] < z:
        return None                                   # nicht ausgereift
    e = max(k for k in range(i, len(ds)) if ds[k] <= z)
    if e <= i or (dt.date.fromisoformat(z) - dt.date.fromisoformat(ds[e])).days > T:
        return None
    for k in range(i + 1, e + 1):
        if (dt.date.fromisoformat(ds[k]) - dt.date.fromisoformat(ds[k - 1])).days > T:
            return None
    return (cs[e] / cs[i] - 1) * 100


def beobachtungen(daten, closes, ticker, von, bis):
    ds, _ = SS.bereinigen(daten, closes)
    tage = [d for d in ds if von <= d <= bis][::RASTER]
    out = []
    for a in tage:
        e = SS.berechne(daten, closes, ticker, a)
        if e["status"] != "ok":
            continue
        zz = ziel(daten, closes, ticker, a)
        if zz is None:
            continue
        out.append({"as_of": a, "jahr": int(a[:4]), "score": e["score_roh"], "ohne": e["vergleich_ohne_matching"],
                    "b1": e["b1"]["wert"], "b2": e["b2"]["wert"], "b3": e["b3"]["wert"], "b4": e["b4"]["wert"],
                    "ziel": zz})
    return out


def spearman(x, y):
    x, y = pd.Series(x), pd.Series(y)
    if x.nunique() < 2 or y.nunique() < 2:
        return None
    return float(x.rank().corr(y.rank()))


def mittel_spearman(reihen, spalte):
    """Mittel der Spearman je Reihe; None, wenn EINE Reihe undefiniert ist (zu wenige Beobachtungen oder konstant)."""
    werte = []
    for obs in reihen.values():
        if len(obs) < MIN_BEOB_ZIEHUNG:
            return None
        s = spearman([o[spalte] for o in obs], [o["ziel"] for o in obs])
        if s is None:
            return None
        werte.append(s)
    return float(np.mean(werte))


def bootstrap(beob: dict, spalten, jahre):
    """Dieselben Jahresziehungen f�r alle Kennzahlen; G�ltigkeit und Verwerfung aber JE KENNZAHL getrennt.
    Gepaart: nur Ziehungen, in denen Score UND Vergleichsscore definiert sind."""
    rnd = np.random.default_rng(SEED)
    werte = {s: [] for s in spalten}
    verworfen = {s: 0 for s in spalten}
    diffs, verworfen_paar = [], 0
    for _ in range(ZIEHUNGEN):
        gezogen = rnd.choice(jahre, size=len(jahre), replace=True)
        zaehl = pd.Series(gezogen).value_counts().to_dict()
        reihen = {t: [o for o in obs for _ in range(zaehl.get(o["jahr"], 0))] for t, obs in beob.items()}
        z = {s: mittel_spearman(reihen, s) for s in spalten}
        for s in spalten:
            if z[s] is None:
                verworfen[s] += 1
            else:
                werte[s].append(z[s])
        if z["score"] is None or z["ohne"] is None:
            verworfen_paar += 1
        else:
            diffs.append(z["score"] - z["ohne"])

    def ci(v):
        return [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))] if v else None
    return ({s: ci(werte[s]) for s in spalten}, verworfen, ci(diffs), verworfen_paar)


def positivrate(obs):
    k = sum(1 for o in obs if o["ziel"] > 0)
    return {"k": k, "n": len(obs), "rate": k / len(obs) if obs else None}


def positivrate_top_quintil(obs):
    df = pd.DataFrame(obs)
    q = pd.qcut(df["score"].rank(method="average"), 5, labels=False, duplicates="drop")
    oben = df["ziel"][q == q.max()]
    return {"k": int((oben > 0).sum()), "n": int(len(oben)), "rate": float((oben > 0).mean()) if len(oben) else None}


def quintile(obs):
    df = pd.DataFrame(obs)
    q = pd.qcut(df["score"].rank(method="average"), 5, labels=False, duplicates="drop")
    return [float(df["ziel"][q == k].mean()) for k in sorted(q.unique())]


def protokoll(snap: pathlib.Path):
    st = subprocess.run(["git", "status", "--porcelain", "--"] + KERN + [SKRIPT], capture_output=True, text=True, cwd=REPO).stdout
    if st.strip():
        sys.exit(f"Kern-Dateien oder Validierungsskript nicht committet:\n{st}\nErst committen, dann das Protokoll festschreiben.")
    commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=REPO).stdout.strip()
    m = manifest(snap)
    p = {
        "erstellt": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "bezeichnung": "historische Walk-forward-Auswertung nach Methodenrevision (kein Best�tigungstest)",
        "commit": commit, "kern_sha256": {k: sha(REPO / k) for k in KERN}, "skript_sha256": sha(REPO / SKRIPT),
        "parameter": PARAMETER,
        "methode": SS.METHODE, "snapshot": str(snap),
        "manifest": {t: {"datei": str(p.relative_to(REPO) if p.is_relative_to(REPO) else p.name), "sha256": sha(p)}
                     for t, p in m.items()},
        "abschnitt_a": A, "abschnitt_b": {"zeitraum": B, "reihen": B_REIHEN}, "raster_handelstage": RASTER,
        "auswertbar": {"min_beobachtungen": MIN_BEOB, "min_jahre": MIN_JAHRE, "nicht_konstant": True},
        "primaer": "Mittel der Spearman je Reihe (gleich gewichtet), score_roh vs. Ziel, Abschnitt A",
        "bootstrap": {"ziehungen": ZIEHUNGEN, "seed": SEED, "block": "Kalenderjahr, dieselben Jahre f�r alle Reihen",
                      "min_beob_je_reihe_und_ziehung": MIN_BEOB_ZIEHUNG, "max_verworfen": MAX_VERWORFEN,
                      "intervall": "Perzentil 2,5/97,5"},
        "sekundaer": "gepaart: Score vs. 5�(B1+B2), Differenz der Mittel, dieselben Tage/Ziehungen",
        "gueltigkeit": "je Kennzahl getrennt: prim�r nach Score/Ziel, gepaart nach beiden Scores/Ziel, explorativ je Baustein",
        "positivrate": "je Reihe k/n Ziel > 0; Mittel der Raten (gleich gewichtet); explorativ oberstes Score-Quintil",
        "explorativ": ["B1-B4 einzeln", "Quintile je Reihe (Mittelrang)", "Abschnitt B"],
        "aussage": "nur Rangzusammenhang ja/nein mit Zahlen; keine R�ckkehr der Richtungsetiketten",
    }
    PROTOKOLL.write_text(json.dumps(p, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Protokoll geschrieben: {PROTOKOLL.relative_to(REPO)} (Commit {commit[:10]}, {len(m)} Reihen)")


def lauf():
    p = json.loads(PROTOKOLL.read_text(encoding="utf-8"))
    if sha(REPO / SKRIPT) != p.get("skript_sha256"):
        sys.exit("Validierungsskript weicht vom Protokoll ab - Lauf verweigert.")
    if p.get("parameter") != json.loads(json.dumps(PARAMETER)):
        sys.exit(f"Parameter weichen vom Protokoll ab - Lauf verweigert: {p.get('parameter')} ? {PARAMETER}")
    for k, h in p["kern_sha256"].items():
        if sha(REPO / k) != h:
            sys.exit(f"Kern {k} weicht vom Protokoll ab - Lauf verweigert.")
    snap = pathlib.Path(p["snapshot"])
    m = manifest(snap)
    if set(m) != set(p["manifest"]):
        sys.exit("Manifest weicht ab - Lauf verweigert.")
    for t, pp in m.items():
        if sha(pp) != p["manifest"][t]["sha256"]:
            sys.exit(f"Datenreihe {t} weicht vom Protokoll ab - Lauf verweigert.")

    beob, aus = {}, {}
    for t, pp in m.items():
        daten, closes = lade(pp)
        obs = beobachtungen(daten, closes, t, *A)
        jahre = {o["jahr"] for o in obs}
        if len(obs) < MIN_BEOB:
            aus[t] = f"nur {len(obs)} Beobachtungen"
        elif len(jahre) < MIN_JAHRE:
            aus[t] = f"nur {len(jahre)} Kalenderjahre"
        elif spearman([o["score"] for o in obs], [o["ziel"] for o in obs]) is None:
            aus[t] = "konstant"
        else:
            beob[t] = obs
        print(f"  {t:7} {len(obs):5} Beobachtungen{'   ' + aus[t] if t in aus else ''}", flush=True)
    spalten = ["score", "ohne", "b1", "b2", "b3", "b4"]
    punkt = {sp: mittel_spearman(beob, sp) for sp in spalten}
    jahre_a = list(range(int(A[0][:4]), int(A[1][:4]) + 1))
    ci, verworfen, ci_diff, verworfen_paar = bootstrap(beob, spalten, jahre_a)
    ok = {sp: verworfen[sp] / ZIEHUNGEN <= MAX_VERWORFEN for sp in spalten}
    ok_paar = verworfen_paar / ZIEHUNGEN <= MAX_VERWORFEN
    rang = (None if not ok["score"] or ci["score"] is None else bool(ci["score"][0] > 0))
    je_reihe = {t: {"n": len(o), "spearman": spearman([x["score"] for x in o], [x["ziel"] for x in o]),
                    "positivrate": positivrate(o), "positivrate_oberstes_quintil": positivrate_top_quintil(o),
                    "quintile_ziel": quintile(o)} for t, o in beob.items()}
    raten = [r["positivrate"]["rate"] for r in je_reihe.values()]
    abschnitt_b = {}
    for t in B_REIHEN:
        daten, closes = lade(m[t])
        o = beobachtungen(daten, closes, t, *B)
        abschnitt_b[t] = {"n": len(o), "spearman": spearman([x["score"] for x in o], [x["ziel"] for x in o]) if o else None,
                          "positivrate": positivrate(o) if o else None}
    erg = {
        "protokoll": str(PROTOKOLL.relative_to(REPO)), "commit": p["commit"],
        "universum": sorted(beob), "ausgeschlossen": aus,
        "primaer": {"mittel_spearman": punkt["score"], "ci95": ci["score"], "verworfen": verworfen["score"],
                    "auswertbar": ok["score"], "rangzusammenhang": rang},
        "sekundaer_gepaart": {"ohne_matching": punkt["ohne"], "ci95_ohne": ci["ohne"], "verworfen_ohne": verworfen["ohne"],
                              "differenz": (punkt["score"] - punkt["ohne"]) if None not in (punkt["score"], punkt["ohne"]) else None,
                              "ci95_differenz": ci_diff, "verworfen": verworfen_paar, "auswertbar": ok_paar},
        "positivrate": {"mittel_ueber_reihen": float(np.mean(raten)) if raten else None},
        "explorativ": {"bausteine": {sp: {"mittel_spearman": punkt[sp], "ci95": ci[sp], "verworfen": verworfen[sp],
                                          "auswertbar": ok[sp]} for sp in ("b1", "b2", "b3", "b4")},
                       "je_reihe": je_reihe, "abschnitt_b": abschnitt_b},
    }
    ERGEBNIS.write_text(json.dumps(erg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    pr = erg["primaer"]
    urteil = "nicht auswertbar" if pr["rangzusammenhang"] is None else ("ja" if pr["rangzusammenhang"] else "nein")
    print(f"\nPrim�r: Mittel Spearman {pr['mittel_spearman']}, 95-%-Intervall {pr['ci95']}, "
          f"verworfen {pr['verworfen']}/{ZIEHUNGEN}  Rangzusammenhang: {urteil}")
    g = erg["sekundaer_gepaart"]
    print(f"Gepaart ({'auswertbar' if g['auswertbar'] else 'nicht auswertbar'}): ohne Matching {g['ohne_matching']}, "
          f"Differenz {g['differenz']}, 95-%-Intervall {g['ci95_differenz']}")
    print(f"Positivrate (Mittel �ber Reihen): {erg['positivrate']['mittel_ueber_reihen']}")


if __name__ == "__main__":
    if "--protokoll" in sys.argv:
        protokoll(pathlib.Path(sys.argv[sys.argv.index("--snapshot") + 1]).resolve())
    elif "--lauf" in sys.argv:
        lauf()
    else:
        sys.exit(__doc__)
{
  "erstellt": "2026-10-09T12:50:11+00:00",
  "bezeichnung": "historische Walk-forward-Auswertung nach Methodenrevision (kein Best�tigungstest)",
  "commit": "28a58a1abc15b2ca42d121813fe9fae385b90378",
  "kern_sha256": {
    "shared/saison_score.py": "d4def89ee50d21ea61e07da6c7178aae8d18aa8dda2a6266e908c0426a2eca31",
    "landing/js/saison-score.js": "fda8cf4fa505fde06fa3bd8c9992de2919c482996bd47961ef38ea836b84bc2a",
    "shared/calculations.py": "724dd95237be48f4cae4f8c6dacabed943a3a9b360ae0c5a5824d602a3be2669"
  },
  "skript_sha256": "f397080f883f86adf6093027bcb433dc8aae210a552ad00b003ff8be1efac0f9",
  "parameter": {
    "seed": 20261009,
    "ziehungen": 2000,
    "abschnitt_a": [
      "2010-01-01",
      "2025-12-31"
    ],
    "abschnitt_b": [
      "1960-01-01",
      "2009-12-31"
    ],
    "b_reihen": [
      "^GSPC",
      "^DJI"
    ],
    "raster": 5,
    "min_beob": 100,
    "min_jahre": 8,
    "min_beob_ziehung": 10,
    "max_verworfen": 0.05,
    "horizont_kt": 30
  },
  "methode": "saison_v1",
  "snapshot": "C:\\Users\\HeikoSeibel\\AppData\\Local\\Temp\\claude\\C--dev-Seasonaledge\\b1245851-7084-4449-b6ab-61b4ed04fde7\\scratchpad\\pv_kurse",
  "manifest": {
    "^GSPC": {
      "datei": "_GSPC.json",
      "sha256": "3e37d6c6c2d66ed98149775e8f0ce67a8fef05962b0072e696021276489cb622"
    },
    "^DJI": {
      "datei": "_DJI.json",
      "sha256": "14c5ff27be9873aa5e123de9010884b82b13f84bfc8c0e19d28a8b721eb142cc"
    },
    "^GDAXI": {
      "datei": "_GDAXI.json",
      "sha256": "f995bd425a5d9a6282ca1374c65c564d36ea019d9684d929dd759b1726052ab5"
    },
    "SPY": {
      "datei": "SPY.json",
      "sha256": "7420f035047506cfbbe764099ea9b6f3c97d9a16d54b261e08e09ee3fe7bc240"
    },
    "QQQ": {
      "datei": "QQQ.json",
      "sha256": "55f5ce97c7f4ec3c43203e988d2425af4ae3e4984b3ec15d30ff80df828ef05a"
    },
    "CNXT": {
      "datei": "scripts\\research\\.cache\\CNXT.json",
      "sha256": "948b92adb9e6ce01d8a9439f6c284e2f37c78edeeb99ab7603fa07236fa46d8e"
    },
    "DIA": {
      "datei": "scripts\\research\\.cache\\DIA.json",
      "sha256": "88dd3fefc95417a77a4b8a0d2fede97121c6feabd9ba86fdf832529c055bd265"
    },
    "ETHA": {
      "datei": "scripts\\research\\.cache\\ETHA.json",
      "sha256": "eb8bd2a52649a0b96d5011c621f774c480c119240fb75453feea31b9df421b61"
    },
    "GDX": {
      "datei": "scripts\\research\\.cache\\GDX.json",
      "sha256": "3099848e9be554705bcbb376fdb195510118ed57826733ace5dae85bc24d0daf"
    },
    "GLD": {
      "datei": "scripts\\research\\.cache\\GLD.json",
      "sha256": "1e0683caa212b95c9bc8319add8fe374618b5958e90c805e270b65264ed54c51"
    },
    "IBIT": {
      "datei": "scripts\\research\\.cache\\IBIT.json",
      "sha256": "0ef2a37ac6df49935528d889ea2fcc1d4b1103815eff8af088fe254a4b1457ec"
    },
    "IGV": {
      "datei": "scripts\\research\\.cache\\IGV.json",
      "sha256": "6eb69a116a40376d4c2e9e25576e7697a6f982bfa2e7303189426a0d4c6610d1"
    },
    "ITB": {
      "datei": "scripts\\research\\.cache\\ITB.json",
      "sha256": "8581387eb0a6a9c1de2cb5fcea162be74c208ef316be00603e15991d687a1fb7"
    },
    "IWM": {
      "datei": "scripts\\research\\.cache\\IWM.json",
      "sha256": "4aaf0e59af9f37e43992e5b708eecf36f0165b3c7e7076b735890d385d83ccf9"
    },
    "IYT": {
      "datei": "scripts\\research\\.cache\\IYT.json",
      "sha256": "8685addd99e495923885cfce1faa68a459db224f00dd5ed57a1177d1048d7ac1"
    },
    "KRE": {
      "datei": "scripts\\research\\.cache\\KRE.json",
      "sha256": "84067601b7fe0e4f3d6dd8067eae208db61375d09cf316ffa1e33834e25ba846"
    },
    "KWEB": {
      "datei": "scripts\\research\\.cache\\KWEB.json",
      "sha256": "3510b021fdfae7b6d93aa31582280a0e3760975464c0d9aa35c86e60c8d0eccd"
    },
    "MAGS": {
      "datei": "scripts\\research\\.cache\\MAGS.json",
      "sha256": "d9cf389426cf58be74505f2b52765b2f2bf6cd181872e27fb862b7c732ddd9fc"
    },
    "RSP": {
      "datei": "scripts\\research\\.cache\\RSP.json",
      "sha256": "5dab10ac8843a76ceef0304cdf79e178fe016fdf0068345d6678ecb011a2d982"
    },
    "SLV": {
      "datei": "scripts\\research\\.cache\\SLV.json",
      "sha256": "e09a899b0b3c64d8430a20a1597866413476819402ea4d35c62f7155fce47b6e"
    },
    "SMH": {
      "datei": "scripts\\research\\.cache\\SMH.json",
      "sha256": "c612d950c343a496e92ee890199a85810152be09db0c255bd07da2fd50e99515"
    },
    "SOXX": {
      "datei": "scripts\\research\\.cache\\SOXX.json",
      "sha256": "6b8a21afe0656c455db5444da2fe8c7493225e14de6daed9a67611c5bd406c59"
    },
    "TAN": {
      "datei": "scripts\\research\\.cache\\TAN.json",
      "sha256": "b91fe7684d74a9ce43091e0c8ef421961c808eee03580239f10d3209a585e9c5"
    },
    "TLT": {
      "datei": "scripts\\research\\.cache\\TLT.json",
      "sha256": "a94f97f2d7ccfa0e17986af5ffd8ee1ccdcd6597b8ae065e9bf7dfd7cd785af5"
    },
    "URA": {
      "datei": "scripts\\research\\.cache\\URA.json",
      "sha256": "01cdf934025ef1d2da4f7e67e675d169dcc2d241ba6a0fc407f70abddaa5edd7"
    },
    "USO": {
      "datei": "scripts\\research\\.cache\\USO.json",
      "sha256": "039e091e24a9ab9827968065f66607a920eb7b9eac1ca263c83432a504e871d8"
    },
    "XBI": {
      "datei": "scripts\\research\\.cache\\XBI.json",
      "sha256": "238fe02812b84b04dc937afc5b90ccdd5f03820ed7ada4cda53ea21f4b6373b7"
    },
    "XHB": {
      "datei": "scripts\\research\\.cache\\XHB.json",
      "sha256": "be2192852c4bd16b3a2371c2f7e569783409cde2795683d785e6a5dec8824982"
    },
    "XLB": {
      "datei": "scripts\\research\\.cache\\XLB.json",
      "sha256": "e88608068bb6ef0b36da495828c4352c840671614153cfb8c1282cdf2f65fef4"
    },
    "XLC": {
      "datei": "scripts\\research\\.cache\\XLC.json",
      "sha256": "60a1aadd6798cf51573f35bf1c131bcd13991f9cedc6887346464dfbabd74343"
    },
    "XLE": {
      "datei": "scripts\\research\\.cache\\XLE.json",
      "sha256": "537a3815c30145947f64f659d5fe36ddce81e57c4dbdecf1adb1b9347d0da27a"
    },
    "XLF": {
      "datei": "scripts\\research\\.cache\\XLF.json",
      "sha256": "b43d22afbe09b62d781d8f1e6dc9b69d05f04bdcbffe2c309e37cf6835c7623f"
    },
    "XLI": {
      "datei": "scripts\\research\\.cache\\XLI.json",
      "sha256": "e6d2e310d0ed26ceec438cac3c3937573c159d8b8e5caba259cd3fa49e949e8c"
    },
    "XLK": {
      "datei": "scripts\\research\\.cache\\XLK.json",
      "sha256": "75000109fe5933021e28a94f042b9b6129aed35d61431ecf68ba812fb233f7ec"
    },
    "XLP": {
      "datei": "scripts\\research\\.cache\\XLP.json",
      "sha256": "e609a0304a0c58f047f6796317e513d544801fd07199b5976bd07ec79bbbcaf2"
    },
    "XLRE": {
      "datei": "scripts\\research\\.cache\\XLRE.json",
      "sha256": "e9a22c3736c953f57cf1111da64f391caae3e494eed3a6c2547cbaa8c05205a5"
    },
    "XLU": {
      "datei": "scripts\\research\\.cache\\XLU.json",
      "sha256": "11af12b7f1c1f0f9a2c028c1b453a970ab67a4bcf106de9511c83839ce5ee5e9"
    },
    "XLV": {
      "datei": "scripts\\research\\.cache\\XLV.json",
      "sha256": "88802f128d9492232865355c84475ae40658fb07e7b12fca344a969286dc7151"
    },
    "XLY": {
      "datei": "scripts\\research\\.cache\\XLY.json",
      "sha256": "9ea7b41d58f2aef50b1933cf5758633ad087cb9037f81802d9ced18e5393b220"
    },
    "XME": {
      "datei": "scripts\\research\\.cache\\XME.json",
      "sha256": "77fc282c9c76fcb68de379b5665897dffe598add6123aa0041ce141028d9b112"
    },
    "XOP": {
      "datei": "scripts\\research\\.cache\\XOP.json",
      "sha256": "b7bd224a49ed62c3586ca95214f530cffbdab3742f270c5d5d3932f081101280"
    },
    "XRT": {
      "datei": "scripts\\research\\.cache\\XRT.json",
      "sha256": "1bf7c8c99ba2e802d110913db3832bcca2a4d282f163eb21b16d5d495a889951"
    },
    "XSD": {
      "datei": "scripts\\research\\.cache\\XSD.json",
      "sha256": "0ca3751cf167b3e96f0d7f013f7a6945660d993ca6c4de4de98bee3a29c712ca"
    }
  },
  "abschnitt_a": [
    "2010-01-01",
    "2025-12-31"
  ],
  "abschnitt_b": {
    "zeitraum": [
      "1960-01-01",
      "2009-12-31"
    ],
    "reihen": [
      "^GSPC",
      "^DJI"
    ]
  },
  "raster_handelstage": 5,
  "auswertbar": {
    "min_beobachtungen": 100,
    "min_jahre": 8,
    "nicht_konstant": true
  },
  "primaer": "Mittel der Spearman je Reihe (gleich gewichtet), score_roh vs. Ziel, Abschnitt A",
  "bootstrap": {
    "ziehungen": 2000,
    "seed": 20261009,
    "block": "Kalenderjahr, dieselben Jahre f�r alle Reihen",
    "min_beob_je_reihe_und_ziehung": 10,
    "max_verworfen": 0.05,
    "intervall": "Perzentil 2,5/97,5"
  },
  "sekundaer": "gepaart: Score vs. 5�(B1+B2), Differenz der Mittel, dieselben Tage/Ziehungen",
  "gueltigkeit": "je Kennzahl getrennt: prim�r nach Score/Ziel, gepaart nach beiden Scores/Ziel, explorativ je Baustein",
  "positivrate": "je Reihe k/n Ziel > 0; Mittel der Raten (gleich gewichtet); explorativ oberstes Score-Quintil",
  "explorativ": [
    "B1-B4 einzeln",
    "Quintile je Reihe (Mittelrang)",
    "Abschnitt B"
  ],
  "aussage": "nur Rangzusammenhang ja/nein mit Zahlen; keine R�ckkehr der Richtungsetiketten"
}

exec
"C:\\Program Files\\PowerShell\\7\\pwsh.exe" -Command '$i=0; Get-Content -Encoding utf8 scripts/research/saison_score_validierung.py | ForEach-Object { $i++; '"'{0}: {1}' -f "'$i,$_ }; Get-Content -Encoding utf8 docs/review_prompts/2026-10-09_saison_score_anomalie_plan_v3.md; rg -n -A 65 '"'D5' docs/review_prompts/2026-10-09_saison_score_anomalie_plan_v2.md" in C:\dev\Seasonaledge
 succeeded in 948ms:
1: #!/usr/bin/env python3
2: """
3: saison_score_validierung.py - historische Walk-forward-Auswertung des Saison-Scores NACH der Methodenrevision
4: (Plan v2/v3, Abschnitt D5, Codex-Freigabe 2026-10-09).
5: 
6: Ausdr�cklich KEIN Best�tigungstest: die Jahre 2010-2025 sind durch die Methodik-Berichte vom 08.10.2026 bereits
7: angesehen. Die prospektive Best�tigung l�uft �ber das unver�nderliche Protokoll `saison_score_protokoll` (fr�hestens
8: 2027-10). Aussage danach nur: "Rangzusammenhang in der historischen Auswertung ja/nein" + Zahlen. Die Bullish/Bearish-
9: Etiketten kehren aufgrund dieses Laufs NICHT zur�ck.
10: 
11: Zwei Schritte:
12:     py -3.14 scripts/research/saison_score_validierung.py --protokoll --snapshot <pv_kurse>
13:         schreibt scripts/research/saison_score_validierung_protokoll.json (Codeversion = Git-Commit + SHA-256 der
14:         Rechenkern-Dateien, SHA-256 jeder Datenreihe, Manifest, Raster, Seed, Regeln). Verlangt saubere Kern-Dateien.
15:     py -3.14 scripts/research/saison_score_validierung.py --lauf
16:         rechnet NUR, wenn Kern und Daten exakt dem Protokoll entsprechen; schreibt ..._ergebnis.json.
17: 
18: Festgelegt (vor dem Lauf, hier im Code und im Protokoll):
19:   * Manifest: ^GSPC, ^DJI, ^GDAXI, SPY, QQQ (Snapshot) + alle Reihen in scripts/research/.cache au�er SPY/QQQ.
20:   * Abschnitt A: jeder 5. Handelstag 2010-01-01 . 2025-12-31; Abschnitt B (getrennt): ^GSPC, ^DJI 1960 . 2009.
21:   * Ziel: Rendite vom Schluss am as_of bis zur letzten Kurszeile = as_of + 30 KT - gleicher Vertrag wie die
22:     Fenster (Endpunkt = T Tage vor dem Ziel, keine L�cke > T); nur ausgereifte Ziele (letzte Kurszeile = as_of + 30).
23:   * Auswertbar: = 100 Bewertungstage mit Score und Ziel in A, auf = 8 Kalenderjahre verteilt, Score und Ziel nicht
24:     konstant. Universum einmal auf den Originaldaten bestimmt, dann fest.
25:   * Prim�r (einziger Test): Mittel der Spearman-Korrelationen je Reihe (gleich gewichtet) zwischen `score_roh` und
26:     Ziel, Abschnitt A. 95-%-Intervall: Block-Bootstrap �ber Kalenderjahre (dieselben gezogenen Jahre f�r alle Reihen,
27:     mit Zur�cklegen), 2000 Ziehungen, Seed 20261009, Perzentilintervall. Ziehung mit einer undefinierten Reihe
28:     (< 10 Beobachtungen oder konstant) wird VERWORFEN und gez�hlt; > 5 % verworfen  "nicht auswertbar".
29:   * Sekund�r, gepaart (dieselben Tage, dieselben Ziehungen): Score vs. 5 � (B1 + B2) - Differenz der Mittel.
30:   * Explorativ: B1-B4 einzeln, Quintile je Reihe (Mittelrang bei Gleichstand), Abschnitt B.
31:   * G�ltigkeit je Kennzahl GETRENNT (Codex vor dem Lauf): dieselben 2000 Jahresziehungen, aber eine Ziehung wird f�r
32:     den Prim�rtest nur nach Score/Ziel verworfen, f�r den gepaarten Vergleich nach beiden Scores/Ziel, explorativ je
33:     Baustein - eine konstante Explorativ-Kennzahl ver�ndert den Prim�rtest nicht. Verwerfungen getrennt berichtet;
34:     �ber 5 %  diese Kennzahl "nicht auswertbar" (null, nicht "nein").
35:   * Positivrate (Basis "immer positiv"): je Reihe k/n der Ziele > 0 auf denselben Bewertungstagen, dazu das Mittel
36:     der Raten �ber die Reihen (gleich gewichtet) und explorativ die Rate im obersten Score-Quintil je Reihe.
37:   * Das Protokoll h�lt den SHA-256 dieses Skripts fest; `--lauf` verweigert bei abweichendem Skript, Kern, Daten
38:     oder Parameter.
39: """
40: from __future__ import annotations
41: import datetime as dt
42: import hashlib
43: import json
44: import pathlib
45: import subprocess
46: import sys
47: 
48: import numpy as np
49: import pandas as pd
50: 
51: REPO = pathlib.Path(__file__).resolve().parents[2]
52: sys.path.insert(0, str(REPO))
53: from shared import saison_score as SS  # noqa: E402
54: 
55: PROTOKOLL = REPO / "scripts/research/saison_score_validierung_protokoll.json"
56: ERGEBNIS = REPO / "scripts/research/saison_score_validierung_ergebnis.json"
57: KERN = ["shared/saison_score.py", "landing/js/saison-score.js", "shared/calculations.py"]
58: SKRIPT = "scripts/research/saison_score_validierung.py"
59: SNAP = {"^GSPC": "_GSPC.json", "^DJI": "_DJI.json", "^GDAXI": "_GDAXI.json", "SPY": "SPY.json", "QQQ": "QQQ.json"}
60: CACHE = REPO / "scripts/research/.cache"
61: SEED = 20261009
62: ZIEHUNGEN = 2000
63: A = ("2010-01-01", "2025-12-31")
64: B = ("1960-01-01", "2009-12-31")
65: B_REIHEN = ["^GSPC", "^DJI"]
66: RASTER = 5
67: MIN_BEOB, MIN_JAHRE, MIN_BEOB_ZIEHUNG = 100, 8, 10
68: MAX_VERWORFEN = 0.05
69: 
70: 
71: PARAMETER = {"seed": SEED, "ziehungen": ZIEHUNGEN, "abschnitt_a": list(A), "abschnitt_b": list(B), "b_reihen": B_REIHEN,
72:              "raster": RASTER, "min_beob": MIN_BEOB, "min_jahre": MIN_JAHRE, "min_beob_ziehung": MIN_BEOB_ZIEHUNG,
73:              "max_verworfen": MAX_VERWORFEN, "horizont_kt": 30}
74: 
75: 
76: def sha(p: pathlib.Path) -> str:
77:     return hashlib.sha256(p.read_bytes()).hexdigest()
78: 
79: 
80: def manifest(snap: pathlib.Path) -> dict:
81:     m = {t: snap / f for t, f in SNAP.items()}
82:     for p in sorted(CACHE.glob("*.json")):
83:         if p.stem not in ("SPY", "QQQ"):
84:             m[p.stem] = p
85:     return m
86: 
87: 
88: def lade(p: pathlib.Path):
89:     rows = json.loads(p.read_text())
90:     return [r["date"] for r in rows], [r["close"] for r in rows]
91: 
92: 
93: def ziel(daten, closes, ticker, as_of):
94:     """Rendite as_of  letzte Kurszeile = as_of + 30 KT, gleicher Vertrag wie die Fenster des Scores."""
95:     T = SS.TOLERANZ[SS.marktklasse(ticker)]
96:     ds, cs = SS.bereinigen(daten, closes)
97:     i = ds.index(as_of)
98:     z = (dt.date.fromisoformat(as_of) + dt.timedelta(days=30)).isoformat()
99:     if ds[-1] < z:
100:         return None                                   # nicht ausgereift
101:     e = max(k for k in range(i, len(ds)) if ds[k] <= z)
102:     if e <= i or (dt.date.fromisoformat(z) - dt.date.fromisoformat(ds[e])).days > T:
103:         return None
104:     for k in range(i + 1, e + 1):
105:         if (dt.date.fromisoformat(ds[k]) - dt.date.fromisoformat(ds[k - 1])).days > T:
106:             return None
107:     return (cs[e] / cs[i] - 1) * 100
108: 
109: 
110: def beobachtungen(daten, closes, ticker, von, bis):
111:     ds, _ = SS.bereinigen(daten, closes)
112:     tage = [d for d in ds if von <= d <= bis][::RASTER]
113:     out = []
114:     for a in tage:
115:         e = SS.berechne(daten, closes, ticker, a)
116:         if e["status"] != "ok":
117:             continue
118:         zz = ziel(daten, closes, ticker, a)
119:         if zz is None:
120:             continue
121:         out.append({"as_of": a, "jahr": int(a[:4]), "score": e["score_roh"], "ohne": e["vergleich_ohne_matching"],
122:                     "b1": e["b1"]["wert"], "b2": e["b2"]["wert"], "b3": e["b3"]["wert"], "b4": e["b4"]["wert"],
123:                     "ziel": zz})
124:     return out
125: 
126: 
127: def spearman(x, y):
128:     x, y = pd.Series(x), pd.Series(y)
129:     if x.nunique() < 2 or y.nunique() < 2:
130:         return None
131:     return float(x.rank().corr(y.rank()))
132: 
133: 
134: def mittel_spearman(reihen, spalte):
135:     """Mittel der Spearman je Reihe; None, wenn EINE Reihe undefiniert ist (zu wenige Beobachtungen oder konstant)."""
136:     werte = []
137:     for obs in reihen.values():
138:         if len(obs) < MIN_BEOB_ZIEHUNG:
139:             return None
140:         s = spearman([o[spalte] for o in obs], [o["ziel"] for o in obs])
141:         if s is None:
142:             return None
143:         werte.append(s)
144:     return float(np.mean(werte))
145: 
146: 
147: def bootstrap(beob: dict, spalten, jahre):
148:     """Dieselben Jahresziehungen f�r alle Kennzahlen; G�ltigkeit und Verwerfung aber JE KENNZAHL getrennt.
149:     Gepaart: nur Ziehungen, in denen Score UND Vergleichsscore definiert sind."""
150:     rnd = np.random.default_rng(SEED)
151:     werte = {s: [] for s in spalten}
152:     verworfen = {s: 0 for s in spalten}
153:     diffs, verworfen_paar = [], 0
154:     for _ in range(ZIEHUNGEN):
155:         gezogen = rnd.choice(jahre, size=len(jahre), replace=True)
156:         zaehl = pd.Series(gezogen).value_counts().to_dict()
157:         reihen = {t: [o for o in obs for _ in range(zaehl.get(o["jahr"], 0))] for t, obs in beob.items()}
158:         z = {s: mittel_spearman(reihen, s) for s in spalten}
159:         for s in spalten:
160:             if z[s] is None:
161:                 verworfen[s] += 1
162:             else:
163:                 werte[s].append(z[s])
164:         if z["score"] is None or z["ohne"] is None:
165:             verworfen_paar += 1
166:         else:
167:             diffs.append(z["score"] - z["ohne"])
168: 
169:     def ci(v):
170:         return [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))] if v else None
171:     return ({s: ci(werte[s]) for s in spalten}, verworfen, ci(diffs), verworfen_paar)
172: 
173: 
174: def positivrate(obs):
175:     k = sum(1 for o in obs if o["ziel"] > 0)
176:     return {"k": k, "n": len(obs), "rate": k / len(obs) if obs else None}
177: 
178: 
179: def positivrate_top_quintil(obs):
180:     df = pd.DataFrame(obs)
181:     q = pd.qcut(df["score"].rank(method="average"), 5, labels=False, duplicates="drop")
182:     oben = df["ziel"][q == q.max()]
183:     return {"k": int((oben > 0).sum()), "n": int(len(oben)), "rate": float((oben > 0).mean()) if len(oben) else None}
184: 
185: 
186: def quintile(obs):
187:     df = pd.DataFrame(obs)
188:     q = pd.qcut(df["score"].rank(method="average"), 5, labels=False, duplicates="drop")
189:     return [float(df["ziel"][q == k].mean()) for k in sorted(q.unique())]
190: 
191: 
192: def protokoll(snap: pathlib.Path):
193:     st = subprocess.run(["git", "status", "--porcelain", "--"] + KERN + [SKRIPT], capture_output=True, text=True, cwd=REPO).stdout
194:     if st.strip():
195:         sys.exit(f"Kern-Dateien oder Validierungsskript nicht committet:\n{st}\nErst committen, dann das Protokoll festschreiben.")
196:     commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=REPO).stdout.strip()
197:     m = manifest(snap)
198:     p = {
199:         "erstellt": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
200:         "bezeichnung": "historische Walk-forward-Auswertung nach Methodenrevision (kein Best�tigungstest)",
201:         "commit": commit, "kern_sha256": {k: sha(REPO / k) for k in KERN}, "skript_sha256": sha(REPO / SKRIPT),
202:         "parameter": PARAMETER,
203:         "methode": SS.METHODE, "snapshot": str(snap),
204:         "manifest": {t: {"datei": str(p.relative_to(REPO) if p.is_relative_to(REPO) else p.name), "sha256": sha(p)}
205:                      for t, p in m.items()},
206:         "abschnitt_a": A, "abschnitt_b": {"zeitraum": B, "reihen": B_REIHEN}, "raster_handelstage": RASTER,
207:         "auswertbar": {"min_beobachtungen": MIN_BEOB, "min_jahre": MIN_JAHRE, "nicht_konstant": True},
208:         "primaer": "Mittel der Spearman je Reihe (gleich gewichtet), score_roh vs. Ziel, Abschnitt A",
209:         "bootstrap": {"ziehungen": ZIEHUNGEN, "seed": SEED, "block": "Kalenderjahr, dieselben Jahre f�r alle Reihen",
210:                       "min_beob_je_reihe_und_ziehung": MIN_BEOB_ZIEHUNG, "max_verworfen": MAX_VERWORFEN,
211:                       "intervall": "Perzentil 2,5/97,5"},
212:         "sekundaer": "gepaart: Score vs. 5�(B1+B2), Differenz der Mittel, dieselben Tage/Ziehungen",
213:         "gueltigkeit": "je Kennzahl getrennt: prim�r nach Score/Ziel, gepaart nach beiden Scores/Ziel, explorativ je Baustein",
214:         "positivrate": "je Reihe k/n Ziel > 0; Mittel der Raten (gleich gewichtet); explorativ oberstes Score-Quintil",
215:         "explorativ": ["B1-B4 einzeln", "Quintile je Reihe (Mittelrang)", "Abschnitt B"],
216:         "aussage": "nur Rangzusammenhang ja/nein mit Zahlen; keine R�ckkehr der Richtungsetiketten",
217:     }
218:     PROTOKOLL.write_text(json.dumps(p, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
219:     print(f"Protokoll geschrieben: {PROTOKOLL.relative_to(REPO)} (Commit {commit[:10]}, {len(m)} Reihen)")
220: 
221: 
222: def lauf():
223:     p = json.loads(PROTOKOLL.read_text(encoding="utf-8"))
224:     if sha(REPO / SKRIPT) != p.get("skript_sha256"):
225:         sys.exit("Validierungsskript weicht vom Protokoll ab - Lauf verweigert.")
226:     if p.get("parameter") != json.loads(json.dumps(PARAMETER)):
227:         sys.exit(f"Parameter weichen vom Protokoll ab - Lauf verweigert: {p.get('parameter')} ? {PARAMETER}")
228:     for k, h in p["kern_sha256"].items():
229:         if sha(REPO / k) != h:
230:             sys.exit(f"Kern {k} weicht vom Protokoll ab - Lauf verweigert.")
231:     snap = pathlib.Path(p["snapshot"])
232:     m = manifest(snap)
233:     if set(m) != set(p["manifest"]):
234:         sys.exit("Manifest weicht ab - Lauf verweigert.")
235:     for t, pp in m.items():
236:         if sha(pp) != p["manifest"][t]["sha256"]:
237:             sys.exit(f"Datenreihe {t} weicht vom Protokoll ab - Lauf verweigert.")
238: 
239:     beob, aus = {}, {}
240:     for t, pp in m.items():
241:         daten, closes = lade(pp)
242:         obs = beobachtungen(daten, closes, t, *A)
243:         jahre = {o["jahr"] for o in obs}
244:         if len(obs) < MIN_BEOB:
245:             aus[t] = f"nur {len(obs)} Beobachtungen"
246:         elif len(jahre) < MIN_JAHRE:
247:             aus[t] = f"nur {len(jahre)} Kalenderjahre"
248:         elif spearman([o["score"] for o in obs], [o["ziel"] for o in obs]) is None:
249:             aus[t] = "konstant"
250:         else:
251:             beob[t] = obs
252:         print(f"  {t:7} {len(obs):5} Beobachtungen{'   ' + aus[t] if t in aus else ''}", flush=True)
253:     spalten = ["score", "ohne", "b1", "b2", "b3", "b4"]
254:     punkt = {sp: mittel_spearman(beob, sp) for sp in spalten}
255:     jahre_a = list(range(int(A[0][:4]), int(A[1][:4]) + 1))
256:     ci, verworfen, ci_diff, verworfen_paar = bootstrap(beob, spalten, jahre_a)
257:     ok = {sp: verworfen[sp] / ZIEHUNGEN <= MAX_VERWORFEN for sp in spalten}
258:     ok_paar = verworfen_paar / ZIEHUNGEN <= MAX_VERWORFEN
259:     rang = (None if not ok["score"] or ci["score"] is None else bool(ci["score"][0] > 0))
260:     je_reihe = {t: {"n": len(o), "spearman": spearman([x["score"] for x in o], [x["ziel"] for x in o]),
261:                     "positivrate": positivrate(o), "positivrate_oberstes_quintil": positivrate_top_quintil(o),
262:                     "quintile_ziel": quintile(o)} for t, o in beob.items()}
263:     raten = [r["positivrate"]["rate"] for r in je_reihe.values()]
264:     abschnitt_b = {}
265:     for t in B_REIHEN:
266:         daten, closes = lade(m[t])
267:         o = beobachtungen(daten, closes, t, *B)
268:         abschnitt_b[t] = {"n": len(o), "spearman": spearman([x["score"] for x in o], [x["ziel"] for x in o]) if o else None,
269:                           "positivrate": positivrate(o) if o else None}
270:     erg = {
271:         "protokoll": str(PROTOKOLL.relative_to(REPO)), "commit": p["commit"],
272:         "universum": sorted(beob), "ausgeschlossen": aus,
273:         "primaer": {"mittel_spearman": punkt["score"], "ci95": ci["score"], "verworfen": verworfen["score"],
274:                     "auswertbar": ok["score"], "rangzusammenhang": rang},
275:         "sekundaer_gepaart": {"ohne_matching": punkt["ohne"], "ci95_ohne": ci["ohne"], "verworfen_ohne": verworfen["ohne"],
276:                               "differenz": (punkt["score"] - punkt["ohne"]) if None not in (punkt["score"], punkt["ohne"]) else None,
277:                               "ci95_differenz": ci_diff, "verworfen": verworfen_paar, "auswertbar": ok_paar},
278:         "positivrate": {"mittel_ueber_reihen": float(np.mean(raten)) if raten else None},
279:         "explorativ": {"bausteine": {sp: {"mittel_spearman": punkt[sp], "ci95": ci[sp], "verworfen": verworfen[sp],
280:                                           "auswertbar": ok[sp]} for sp in ("b1", "b2", "b3", "b4")},
281:                        "je_reihe": je_reihe, "abschnitt_b": abschnitt_b},
282:     }
283:     ERGEBNIS.write_text(json.dumps(erg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
284:     pr = erg["primaer"]
285:     urteil = "nicht auswertbar" if pr["rangzusammenhang"] is None else ("ja" if pr["rangzusammenhang"] else "nein")
286:     print(f"\nPrim�r: Mittel Spearman {pr['mittel_spearman']}, 95-%-Intervall {pr['ci95']}, "
287:           f"verworfen {pr['verworfen']}/{ZIEHUNGEN}  Rangzusammenhang: {urteil}")
288:     g = erg["sekundaer_gepaart"]
289:     print(f"Gepaart ({'auswertbar' if g['auswertbar'] else 'nicht auswertbar'}): ohne Matching {g['ohne_matching']}, "
290:           f"Differenz {g['differenz']}, 95-%-Intervall {g['ci95_differenz']}")
291:     print(f"Positivrate (Mittel �ber Reihen): {erg['positivrate']['mittel_ueber_reihen']}")
292: 
293: 
294: if __name__ == "__main__":
295:     if "--protokoll" in sys.argv:
296:         protokoll(pathlib.Path(sys.argv[sys.argv.index("--snapshot") + 1]).resolve())
297:     elif "--lauf" in sys.argv:
298:         lauf()
299:     else:
300:         sys.exit(__doc__)
# Plan v3: Saison-Score und Anomalie-Radar - Erg�nzungen zu v2

Repo `C:\dev\Seasonaledge`. Nur lesen. v2: `..._plan_v2.md`, deine Antwort `..._plan_antwort2.md` (4 Befunde).
Unten nur die �nderungen gegen�ber v2. Antwort auf Deutsch, je Befund Schwere + Abschnitt + Fall + �nderung; am Ende
genau eine Zeile `FREIGABE: ja` oder `FREIGABE: nein`.

## Zu Befund 1 - Marktklasse im Funktionsvertrag
Beide Kerne bekommen den **Ticker als Pflichtparameter**: JS `SA.decadeCompute.anomalie(rows, ticker, {as_of})`,
`SA.saisonScore.berechne(rows, ticker, {as_of})`; Python `anomalie(daten, closes, ticker, as_of=None)`,
`saison_score(daten, closes, ticker, as_of=None)`. Eine gemeinsame, in beiden Sprachen wortgleiche Zuordnung
`marktklasse(ticker)`: Endung `-USD`  `krypto` (T = 1), Endung `=X`  `forex` (T = 3), sonst  `boerse` (T = 5);
leerer/fehlender Ticker  Fehler (kein stiller Standard). Unbekannte Suffixe fallen bewusst unter `boerse` (die
gro�z�gigere Toleranz verwirft keine echten B�rsenreihen; dokumentiert). Alle Aufrufer (Dashboard, Watchlist,
KI-Seite, sieben Radar-Seiten, Nightly/Full-Scanner, D5) �bergeben den Ticker. Test: identische Datumsreihe mit
zweit�giger L�cke  `krypto` verwirft, `boerse` akzeptiert; Python = JS.

## Zu Befund 2 - Zeitzone im Jahreskurvenbau + Tag 366
- **`buildYearData`/`buildExtendedYearData` in `landing/js/seasonal-compute.js` werden auf UTC umgestellt**
  (Jahr, Tagesnummer und Jahresbeginn aus dem ISO-Datum per `Date.UTC`, nicht `getFullYear()`/lokaler Jahresanfang).
  Das ist ein **seitenweiter Fehler** (betrifft alle Saisonseiten f�r Leser au�erhalb UTC/MEZ, z. B. New York) und
  wird als eigener Schritt **vor** C gebaut, mit eigenem Review: Zwillingsw�chter `verify_seasonal_twins.py` l�uft
  zus�tzlich unter `TZ=America/New_York`, `TZ=Asia/Tokyo` und `TZ=UTC` (node mit gesetzter Umgebungsvariable) und
  verlangt identische Ausgaben; Mutationstest "lokales Jahr statt UTC" muss rei�en. Zus�tzlich pr�fe ich mit grep,
  welche anderen Stellen Datumsstrings �ber `new Date(...)` + lokale Getter auswerten, und liste sie (nicht alle
  im selben Schritt beheben - nur die, die in Score/Radar eingehen).
- **Tag 366:** Matching-Pr�fix d = **min(Tagesnummer(as_of), 365)**; die bestehende Faltung (31.12. im Schaltjahr auf
  Slot 365) bleibt. Tests: as_of = 30.12. und 31.12. eines Schaltjahres, Python = JS.

## Zu Befund 3 - D5 auswertbares Universum
Vor dem Lauf im Protokoll festgelegt:
- Eine Reihe ist **auswertbar**, wenn sie in Abschnitt A mindestens **100** Bewertungstage mit Score ? null und
  ausgereiftem Ziel hat, verteilt auf mindestens **8** verschiedene Kalenderjahre, und weder Score noch Ziel konstant
  sind. Nach Datenlage fallen damit u. a. ETHA, IBIT, MAGS (zu jung) und vermutlich XLC heraus - das wird nicht
  vorab angepasst, sondern aus der Regel ermittelt und berichtet.
- Das auswertbare Universum wird **einmal** auf den Originaldaten bestimmt und gilt dann fest f�r alle Ziehungen.
- **Bootstrap:** je Ziehung dieselben Kalenderjahre (mit Zur�cklegen) f�r alle Reihen; Spearman je Reihe auf den
  gezogenen Beobachtungen (mehrfach gezogene Jahre z�hlen mehrfach). Ist in einer Ziehung eine Reihe undefiniert
  (< 10 Beobachtungen oder konstant), wird die **ganze Ziehung verworfen und gez�hlt** - kein `nanmean`. Liegt der
  Verwerfungsanteil �ber **5 %**, gilt das Ergebnis als "nicht auswertbar" und wird so berichtet.
- **Gepaarter Vergleich** Score vs. 5�(B1+B2): exakt dieselben Bewertungstage (Schnittmenge, in der beide definiert
  sind), dieselben Ziehungen.
- Berichtet werden: auswertbares Universum, Ausschl�sse mit Grund, Fallzahl je Reihe, Verwerfungsanteil.

## Zu Befund 4 - unver�nderliches prospektives Protokoll
Neue Tabelle `saison_score_protokoll` (in derselben Migration wie D3): `protokoll_id` (Identit�t), `methode`,
`code_version` (Git-Kurz-SHA des Containers, im Image hinterlegt), `erstellt_am`, `ticker`, `as_of`, `kurse_bis`,
`kurse_hash` (wie bei der Stress-Ampel), `status`, `grund`, `score`, `bausteine`. **Nur INSERT**: eindeutiger
Schl�ssel `(methode, ticker, as_of)`, Schreiben mit `ON CONFLICT DO NOTHING`  **der erste Lauf je Ticker und as_of
z�hlt**, Wiederholungsl�ufe �ndern das Protokoll nicht (ein abweichender Wiederholungswert wird im App-Log gemeldet,
nicht �berschrieben). RLS: kein Zugriff f�r `anon`/`authenticated`, Schreiben nur `service_role`; kein UPDATE/DELETE-
Recht f�r die Rolle des Nightly. Die Scanner-Anzeige liest weiter aus `scanner_results`; die Best�tigungsauswertung
(fr�hestens 2027-10) liest nur aus dem Protokoll.

## Reihenfolge
**U** (UTC-Korrektur Jahreskurvenbau)  C  D1/D2  D5  D3 (Migration inkl. Protokolltabelle)  D4.
78:- **D5 Validierung (neu formuliert):**
79-  - Bezeichnung: **„historische Walk-forward-Auswertung nach Methodenrevision"** — kein Bestätigungstest; die Jahre
80-    sind durch die Berichte vom 08.10. bereits angesehen. **Prospektive Bestätigung:** die täglich gespeicherten
81-    `scanner_results` (`saison_v1`) sind das Protokoll; Auswertung frühestens 2027-10 mit diesem Protokoll.
82-  - **Vor dem Lauf festgehalten** in `scripts/research/saison_score_validierung_protokoll.json`: Codeversion (Commit),
83-    Snapshot-Hash, Ticker-Manifest, Bewertungsraster, Seed, Zeiträume, Kennzahlen.
84-  - **Manifest:** ^GSPC, ^DJI, ^GDAXI, SPY, QQQ (Snapshot) + die Research-Cache-ETFs **ohne** SPY/QQQ (dedupliziert),
85-    eindeutige Liste im Protokoll.
86-  - **Raster:** jeder 5. Handelstag 2010–2025 (Abschnitt A); ^GSPC/^DJI zusätzlich 1960–2009 (Abschnitt B, getrennt).
87-    Ziel = Fensterrendite as_of → Endpunkt ≤ as_of + 30 KT nach dem Vertrag oben; nur Bewertungstage, deren Ziel
88-    vollständig in den Daten liegt (ausgereift). Ziel wird dem Kalenderjahr von as_of zugeordnet.
89-  - **Primärer Test (einziger):** mittlere Spearman-Korrelation über die Reihen (je Reihe ein Spearman, **gleich
90-    gewichtet**) zwischen Score und Zielrendite, Abschnitt A. 95-%-Intervall per **Block-Bootstrap über Kalenderjahre,
91-    dieselben Jahre für alle Reihen je Ziehung**, 2000 Ziehungen, Seed 20261009, Perzentilintervall.
92-  - **Gepaart (sekundär, berichtet, keine Bestätigungsaussage):** Score vs. Vergleichsscore ohne Matching
93-    5·(B1 + B2) — Differenz der mittleren Spearman mit gepaartem Bootstrap-Intervall; Bausteine B1–B4 und
94-    Quintile (Gleichstände: Mittelrang, Quintile je Reihe) **explorativ**. „Immer positiv" nur als Basis der
95-    Positivrate.
96-  - **Aussage danach:** nur „Rangzusammenhang in der historischen Auswertung ja/nein" plus Zahlen. **Keine** Rückkehr
97-    der Bullish/Bearish-Etiketten aufgrund dieses Tests (Befund 11); dafür bräuchte es eine eigene, vorab definierte
98-    Prüfung konkreter Schwellen auf unabhängigen Daten.
99-
100-## Reihenfolge (unverändert)
101:C → D1/D2 → D5 → D3 → D4. Jeder Schritt mit eigenem Code-Review.

codex
Die getrennte Gültigkeitsprüfung, der gepaarte Vergleich und die Ausgabe „nicht auswertbar“ entsprechen jetzt den R1-Korrekturen. Ich gleiche noch Skript-, Kern- und Datenhashes mit dem Protokoll ab und prüfe die Positivrate für beide Abschnitte.
exec
"C:\\Program Files\\PowerShell\\7\\pwsh.exe" -Command '$p = Get-Content -Raw -Encoding utf8 scripts/research/saison_score_validierung_protokoll.json | ConvertFrom-Json; $bad = @(); foreach ($k in $p.kern_sha256.PSObject.Properties) { if ((Get-FileHash -Algorithm SHA256 -LiteralPath $k.Name).Hash.ToLower() -ne $k.Value) { $bad += $k.Name } }; $scriptok = (Get-FileHash -Algorithm SHA256 scripts/research/saison_score_validierung.py).Hash.ToLower() -eq $p.skript_sha256; $n=0; foreach ($t in $p.manifest.PSObject.Properties) { $f=$t.Value.datei; if ($f -notmatch '"'[/\\\\]') { "'$f=Join-Path $p.snapshot $f }; if ((Get-FileHash -Algorithm SHA256 -LiteralPath $f).Hash.ToLower() -ne $t.Value.sha256) { $bad += $t.Name }; $n++ }; [pscustomobject]@{SkriptHashOK=$scriptok; Datenreihen=$n; Abweichungen=($bad -join '"', ')} | ConvertTo-Json; git diff b7b01da HEAD -- shared/saison_score.py landing/js/saison-score.js shared/calculations.py; git diff HEAD -- scripts/research/saison_score_validierung.py scripts/research/saison_score_validierung_protokoll.json; rg --files scripts/research/.cache -g '*.json'" in C:\dev\Seasonaledge
exec
"C:\\Program Files\\PowerShell\\7\\pwsh.exe" -Command 'Get-Content -Encoding utf8 shared/saison_score.py' in C:\dev\Seasonaledge
 succeeded in 826ms:
"""
shared/saison_score.py - Saison-Score (Python-Zwilling von landing/js/saison-score.js)

Ersetzt den "KI-Score" (shared/ki_score.py). Plan v1-v3 mit Codex-Freigabe 2026-10-09:
docs/review_prompts/2026-10-09_saison_score_anomalie_plan.md (+ _v2, _v3).

EINE Definition f�r Scanner/Mails (hier) und Seiten (JS). Zeile f�r Zeile in derselben Reihenfolge gerechnet wie das
JS, damit die Ergebnisse bitgleich sind; gepr�ft von scripts/verify_saison_score.py (echtes JS in node gegen diese
Datei und gegen eine dritte, naive Referenz).

Kurzfassung (Details im JS-Kopf und im Plan):
  * Fenster as_of  +30 Kalendertage; Fensterrendite je Vorjahr aus Rohkursen (Start/Ende = letzte Kurszeile = Ziel,
    29.02.  28.02., L�ckenheuristik T = 1 Krypto / 3 Forex / 7 B�rse).
  * Lookback = 20 j�ngste abgeschlossene Jahre mit Fenster und vollst�ndigem Jahrespfad; mindestens 10.
  * B1/B2 aus allen Lookback-Jahren, B3/B4 aus den 5 Musterjahren (Pearson auf dem Jahrespfad, "Pfad�hnlichkeit").
  * Score = 2,5 � (B1 + B2 + B3 + B4), halb aufw�rts auf eine Stelle. Keine Richtungsetiketten.
  * Nicht berechenbar statt Ersatzwert (kein 0,5 mehr).
"""
from __future__ import annotations

import datetime as dt
import math

import bisect

METHODE = "saison_v1"
HORIZONT = 30
LOOKBACK = 20
MIN_JAHRE = 10
TOP_N = 5
MIN_HANDELSTAGE = 20
SPAETESTER_JAHRESSTART = 10
TOLERANZ = {"krypto": 1, "forex": 3, "boerse": 7}   # = SA.decadeCompute.ANOMALIE.TOLERANZ


def marktklasse(ticker) -> str:
    """Wortgleich mit SA.decadeCompute.marktklasse. Kein Ticker  Fehler (kein stiller Standard)."""
    if ticker is None or str(ticker).strip() == "":
        raise ValueError("Ticker fehlt")
    t = str(ticker).strip().upper()
    if t.endswith("-USD"):
        return "krypto"
    if t.endswith("=X"):
        return "forex"
    return "boerse"


def _epoch_tag(iso: str) -> int:
    return (dt.date.fromisoformat(iso[:10]) - dt.date(1970, 1, 1)).days


def _ziel_tag(y: int, m: int, d: int) -> int:
    letzter = ((dt.date(y + (m == 12), m % 12 + 1, 1)) - dt.timedelta(days=1)).day
    return (dt.date(y, m, min(d, letzter)) - dt.date(1970, 1, 1)).days


def _tag_nummer(iso: str) -> int:
    return dt.date.fromisoformat(iso[:10]).timetuple().tm_yday


def bereinigen(daten, closes, as_of: str | None = None):
    """Wie SA.decadeCompute._bereinigen: nicht-endlich/= 0 raus, doppelte Daten  letzter Wert, sortiert."""
    m = {}
    for d, c in zip(daten, closes):
        if d is None or c is None:
            continue
        try:
            c = float(c)
        except (TypeError, ValueError):
            continue
        if not math.isfinite(c) or c <= 0:
            continue
        d = str(d)[:10]
        if as_of and d > as_of:
            continue
        m[d] = c
    ds = sorted(m)
    return ds, [m[d] for d in ds]


def pearson(a, b):
    """Zweistufig wie SA.saisonScore.pearson; None bei Streuung 0."""
    n = min(len(a), len(b))
    if n < 2:
        return None
    # Konstanz VOR der Mittelwertrechnung (Summationsrest; Codex Kern R1) - wie SA.saisonScore.pearson
    if min(a[:n]) == max(a[:n]) or min(b[:n]) == max(b[:n]):
        return None
    ma = 0.0
    mb = 0.0
    for i in range(n):
        ma += a[i]
        mb += b[i]
    ma /= n
    mb /= n
    sab = saa = sbb = 0.0
    for i in range(n):
        da = a[i] - ma
        db = b[i] - mb
        sab += da * db
        saa += da * da
        sbb += db * db
    if not saa > 0 or not sbb > 0:
        return None
    return sab / math.sqrt(saa * sbb)


def interp365(days, values):
    """Schnelle Fassung von shared.calculations.interpolate_to_365 - DIESELBE Formel (prev + w�(next - prev),
    w = (Ziel - prev)/(next - prev)), Tag 366 auf 365 gefaltet, au�erhalb konstant. Statt linearer Suche je Zieltag
    bin�re Suche: interpolate_to_365 braucht je Jahr ~365 � L�nge Vergleiche, f�r die Validierung �ber tausende
    Stichtage zu langsam. Gleichheit (exakt, nicht auf Toleranz) pr�ft scripts/verify_saison_score.py."""
    if days and days[-1] > 365:
        keep = {}
        for d, v in zip(days, values):
            keep[min(d, 365)] = v
        days = sorted(keep)
        values = [keep[d] for d in days]
    out = []
    n = len(days)
    for ziel in range(1, 366):
        i = bisect.bisect_left(days, ziel)
        if i < n and days[i] == ziel:
            out.append(values[i])
        elif ziel < days[0]:
            out.append(values[0])
        elif ziel > days[-1]:
            out.append(values[-1])
        else:
            pv, nv = i - 1, i
            w = (ziel - days[pv]) / (days[nv] - days[pv])
            out.append(values[pv] + w * (values[nv] - values[pv]))
    return out


def _clip01(x):
    return 0.0 if x < 0 else (1.0 if x > 1 else x)


def _runden1(x):
    return math.floor(x * 10 + 0.5) / 10


def berechne(daten, closes, ticker, as_of: str | None = None) -> dict:
    klasse = marktklasse(ticker)
    T = TOLERANZ[klasse]
    asof_opt = str(as_of)[:10] if as_of else None
    ds, cs = bereinigen(daten, closes, asof_opt)
    n = len(ds)

    def aus(code, grund):
        return {"status": "nicht_berechenbar", "grund_code": code, "grund": grund, "methode": METHODE,
                "as_of": ds[-1] if n else None, "marktklasse": klasse, "score": None}

    if not n:
        return aus("keine_kurse", "keine Kurse")
    as_of_d = ds[-1]
    Y, mA, dA = int(as_of_d[:4]), int(as_of_d[5:7]), int(as_of_d[8:10])
    tage = [_epoch_tag(d) for d in ds]

    pro_jahr: dict[int, list[int]] = {}
    for i in range(n):
        pro_jahr.setdefault(int(ds[i][:4]), []).append(i)

    def pfad(y):
        idx = pro_jahr.get(y)
        if not idx or len(idx) < MIN_HANDELSTAGE:
            return None
        if int(ds[idx[0]][8:10]) > SPAETESTER_JAHRESSTART or int(ds[idx[0]][5:7]) != 1:
            return None
        c0 = cs[idx[0]]
        return interp365([_tag_nummer(ds[k]) for k in idx], [100 * cs[k] / c0 for k in idx])

    if Y not in pro_jahr or len(pro_jahr[Y]) < MIN_HANDELSTAGE:
        return aus("zu_frueh_im_jahr", "vor dem 20. Handelstag des Jahres")
    pfad_y = pfad(Y)
    if pfad_y is None:
        return aus("unvollstaendiges_jahr", "laufendes Jahr beginnt nach dem 10. Januar")
    d = min(_tag_nummer(as_of_d), 365)

    def bis_idx(ziel):
        lo, hi, best = 0, n - 1, -1
        while lo <= hi:
            mid = (lo + hi) >> 1
            if tage[mid] <= ziel:
                best = mid
                lo = mid + 1
            else:
                hi = mid - 1
        return best

    def fenster(y):
        z1 = _ziel_tag(y, mA, dA)
        z2 = z1 + HORIZONT
        s, e = bis_idx(z1), bis_idx(z2)
        if s < 0 or e <= s or z1 - tage[s] > T or z2 - tage[e] > T:
            return None
        for k in range(s + 1, e + 1):
            if tage[k] - tage[k - 1] > T:
                return None
        return (cs[e] / cs[s] - 1) * 100

    L = []
    erster_jahr = int(ds[0][:4])
    yy = Y - 1
    while yy >= erster_jahr and len(L) < LOOKBACK:
        py = pfad(yy)
        if py is not None:
            R = fenster(yy)
            if R is not None:
                L.append({"jahr": yy, "rendite": R, "pfad": py})
        yy -= 1
    if len(L) < MIN_JAHRE:
        return aus("zu_wenige_jahre", f"weniger als {MIN_JAHRE} Vergleichsjahre")

    cur = pfad_y[:d]
    kand = []
    for j in L:
        rr = pearson(cur, j["pfad"][:d])
        if rr is not None:
            kand.append({"jahr": j["jahr"], "r": rr, "rendite": j["rendite"]})
    kand.sort(key=lambda k: (-k["r"], -k["jahr"]))
    top = kand[:TOP_N]
    if len(top) < TOP_N:
        return aus("zu_wenige_musterjahre", f"weniger als {TOP_N} Musterjahre")
    W = 0.0
    WR = 0.0
    for t in top:
        w = (t["r"] + 1) / 2
        W += w
        WR += w * t["rendite"]
    if not W > 0:
        return aus("gewichte_null", "Gewichtssumme der Musterjahre 0")

    k1 = sum(1 for j in L if j["rendite"] > 0)
    summe = 0.0
    for j in L:
        summe += j["rendite"]
    mittel = summe / len(L)
    k3 = sum(1 for t in top if t["rendite"] > 0)
    mittel_w = WR / W
    b1 = k1 / len(L)
    b2 = _clip01((mittel + 3) / 6)
    b3 = k3 / len(top)
    b4 = _clip01((mittel_w + 3) / 6)
    roh = 2.5 * (b1 + b2 + b3 + b4)

    mittelpfad = []
    for t in range(d):
        sm = 0.0
        for q in range(len(L)):
            sm += L[q]["pfad"][t]
        mittelpfad.append(sm / len(L))
    bis = (dt.date(1970, 1, 1) + dt.timedelta(days=_epoch_tag(as_of_d) + HORIZONT)).isoformat()
    return {
        "status": "ok", "grund_code": None, "grund": None, "methode": METHODE, "as_of": as_of_d, "marktklasse": klasse,
        "fenster": {"von": as_of_d, "bis": bis, "tage": HORIZONT},
        "score": _runden1(roh), "score_roh": roh,
        "b1": {"wert": b1, "k": k1, "n": len(L)},
        "b2": {"wert": b2, "mittel": mittel},
        "b3": {"wert": b3, "k": k3, "n": len(top)},
        "b4": {"wert": b4, "mittel": mittel_w},
        "vergleich_ohne_matching": 5 * (b1 + b2),
        "jahre": [j["jahr"] for j in L],
        "musterjahre": top,
        "konformitaet": pearson(cur, mittelpfad),
    }

 succeeded in 1411ms:
InvalidArgument: 
Line |
   2 |  .  }; $n++ }; [pscustomobject]@{SkriptHashOK=$scriptok; Datenreihen=$n; .
     |                ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | Der Wert kann nicht in den Typ "System.Management.Automation.LanguagePrimitives+InternalPSCustomObject" konvertiert werden. In diesem Sprachmodus werden nur Kerntypen unterst�tzt.
warning: unable to access 'C:\Users\HeikoSeibel/.config/git/ignore': Permission denied
scripts/research/.cache\XSD.json
scripts/research/.cache\XRT.json
scripts/research/.cache\XOP.json
scripts/research/.cache\XME.json
scripts/research/.cache\XLY.json
scripts/research/.cache\XLV.json
scripts/research/.cache\XLU.json
scripts/research/.cache\XLRE.json
scripts/research/.cache\XLP.json
scripts/research/.cache\XLK.json
scripts/research/.cache\XLI.json
scripts/research/.cache\XLF.json
scripts/research/.cache\XLE.json
scripts/research/.cache\XLC.json
scripts/research/.cache\XLB.json
scripts/research/.cache\XHB.json
scripts/research/.cache\XBI.json
scripts/research/.cache\USO.json
scripts/research/.cache\URA.json
scripts/research/.cache\TLT.json
scripts/research/.cache\TAN.json
scripts/research/.cache\SPY.json
scripts/research/.cache\SOXX.json
scripts/research/.cache\SMH.json
scripts/research/.cache\SLV.json
scripts/research/.cache\RSP.json
scripts/research/.cache\QQQ.json
scripts/research/.cache\MAGS.json
scripts/research/.cache\KWEB.json
scripts/research/.cache\KRE.json
scripts/research/.cache\IYT.json
scripts/research/.cache\IWM.json
scripts/research/.cache\ITB.json
scripts/research/.cache\IGV.json
scripts/research/.cache\IBIT.json
scripts/research/.cache\GLD.json
scripts/research/.cache\GDX.json
scripts/research/.cache\ETHA.json
scripts/research/.cache\DIA.json
scripts/research/.cache\CNXT.json

exec
"C:\\Program Files\\PowerShell\\7\\pwsh.exe" -Command '$p = Get-Content -Raw -Encoding utf8 scripts/research/saison_score_validierung_protokoll.json | ConvertFrom-Json; $bad = @(); foreach ($k in $p.kern_sha256.PSObject.Properties) { if ((Get-FileHash -Algorithm SHA256 -LiteralPath $k.Name).Hash.ToLower() -ne $k.Value) { $bad += $k.Name } }; $scriptok = (Get-FileHash -Algorithm SHA256 scripts/research/saison_score_validierung.py).Hash.ToLower() -eq $p.skript_sha256; $n=0; foreach ($t in $p.manifest.PSObject.Properties) { $f=$t.Value.datei; if ($f -notmatch '"'[/\\\\]') { "'$f=Join-Path $p.snapshot $f }; if ((Get-FileHash -Algorithm SHA256 -LiteralPath $f).Hash.ToLower() -ne $t.Value.sha256) { $bad += $t.Name }; $n++ }; "SkriptHashOK: $scriptok"; "Datenreihen: $n"; "Hashabweichungen: $($bad.Count)"; $bad' in C:\dev\Seasonaledge
 succeeded in 822ms:
SkriptHashOK: True
Datenreihen: 43
Hashabweichungen: 0

codex
Keine freigabeverhindernden Befunde. Die vier R1-Korrekturen sind umgesetzt:

- Gültigkeit und Verwerfungen werden je Kennzahl getrennt bestimmt; der gepaarte Vergleich verwendet ausschließlich gemeinsam gültige Ziehungen.
- Skripthash und Parameter werden vor der Berechnung geprüft. Skript, alle drei Kernhashes und sämtliche 43 Datenhashes stimmen mit dem committeten Protokoll überein. Der Kern ist gegenüber `b7b01da` unverändert.
- Fehlende Auswertbarkeit ergibt `rangzusammenhang = null` und die entsprechende Konsolenausgabe; der gepaarte Vergleich besitzt einen eigenen Status.
- Positivraten werden als `k/n` berichtet, in A zusätzlich gleich gewichtet aggregiert und für das oberste Score-Quintil ausgewiesen; B enthält die Positivrate je Reihe.

Nur lesend geprüft; keine Dateien geändert und `--lauf` nicht ausgeführt. D3-Betriebsfunktionen waren nicht Gegenstand.

FREIGABE: ja
tokens used
32.878
Keine freigabeverhindernden Befunde. Die vier R1-Korrekturen sind umgesetzt:

- Gültigkeit und Verwerfungen werden je Kennzahl getrennt bestimmt; der gepaarte Vergleich verwendet ausschließlich gemeinsam gültige Ziehungen.
- Skripthash und Parameter werden vor der Berechnung geprüft. Skript, alle drei Kernhashes und sämtliche 43 Datenhashes stimmen mit dem committeten Protokoll überein. Der Kern ist gegenüber `b7b01da` unverändert.
- Fehlende Auswertbarkeit ergibt `rangzusammenhang = null` und die entsprechende Konsolenausgabe; der gepaarte Vergleich besitzt einen eigenen Status.
- Positivraten werden als `k/n` berichtet, in A zusätzlich gleich gewichtet aggregiert und für das oberste Score-Quintil ausgewiesen; B enthält die Positivrate je Reihe.

Nur lesend geprüft; keine Dateien geändert und `--lauf` nicht ausgeführt. D3-Betriebsfunktionen waren nicht Gegenstand.

FREIGABE: ja
