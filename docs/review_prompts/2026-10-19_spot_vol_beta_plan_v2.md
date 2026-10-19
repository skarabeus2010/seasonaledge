# Review: /spot-vol-beta — Plan v2 (Runde 2)

Read-only. Vorgeschichte: `docs/review_prompts/2026-10-19_spot_vol_beta_plan.md` (v1) — dein Urteil war
„nicht tragfähig“ mit 8 Befunden und Auflagen zu P1–P5. Alle Befunde sind übernommen. Hier die verbindlichen
Festlegungen; bitte prüfen, ob sie die Auflagen erfüllen und ob neue Lücken entstehen.

## Architektur

Rechnung aus dem Inline-Script in **`landing/js/spot-vol-compute.js`** (`SA.spotVol`, erste Anweisung
`window.SA.__release('%%RELEASE%%')`, in `verify_einbindung` eingetragen), reine Funktionen ohne DOM. Die Seite
rendert nur. Damit ist der Kern in node prüfbar, ohne Funktionen aus dem HTML zu ziehen.

## Daten (Befunde 1, 4, 7)

- Laden: `SA.kurse.zeilen(t, {felder: ['date','close','log_return'], ab})` für Spot und Vol.
- **Renditen nur aus gespeichertem `log_return`** (je Ticker). Eine Zeile mit `log_return` null/nicht endlich →
  Rendite unbekannt. Einfache Rendite = `expm1(lr)`.
- **Gemeinsame Achse:** Datum d ist ein Paartag, wenn beide Reihen eine Zeile an d haben. Die Paarrendite an d ist
  nur gültig, wenn **in beiden Reihen die unmittelbar vorangehende eigene Zeile dasselbe Datum p hat** und p der
  vorige Paartag ist. Sonst (Lücke in einer Reihe) → Paarrendite unbekannt, kein Zusammenziehen.
  Keine Kalenderannahme nötig: eine fehlende Sitzung in einer Reihe macht den Folgetag ungültig.
- **Forward-Renditen auf der Spot-Achse:** Log-Preisindex der Spot-Reihe = kumulierte `log_return` (Basiswechsel
  zählen nicht). Forward h ab Spot-Zeile i = `expm1(Σ lr[i+1..i+h])`, nur wenn alle h Renditen bekannt und
  i+h existiert. Horizonte in Spot-Sitzungen (Zeilen der Spot-Reihe; Lücken in der Spot-Reihe → unbekannt über die
  Lückenregel „vorige Zeile = vorige Sitzung“ ist hier nicht prüfbar ohne Kalender → **Annahme:** Spot-Reihe ist
  die Sitzungsachse; Lücken darin sind Datenfehler, die die Nightly-Prüfung meldet). Bitte bewerten.
- Plausibilität `close > 0` nur noch für Anzeige (Kurs-Charts), nicht für Renditen.
- **Ausgewerteter Tag:** letzter Paartag mit gültiger Paarrendite; sein Datum steht sichtbar am Kasten und an
  „Heute“ im Scatter (Beschriftung „letzter gemeinsamer Handelstag dd.mm.yyyy“). Endet eine Reihe früher als die
  andere, Hinweis „Vol-Reihe endet am …“ bzw. „Spot-Reihe endet am …“.
- **Zeitraum:** Start = heute (lokales Datum aus `getFullYear/getMonth/getDate`, als String gebaut, kein
  `toISOString`) minus n Jahre, 29.02. → 28.02. Geladen wird ab Start **minus 3 Jahre Vorlauf** (für expandierende
  Schwellen und Rolling), angezeigt/ausgewertet ab Start. „Max“: Laden ab 1990-01-01, Anzeige ab erstem Paartag.

## Rechnung

- **Gesamt-OLS** über gültige Paarrenditen im Anzeigezeitraum (Prozent oder Log je Schalter). Anzeige des Betas als
  „Vol-Änderung je 1 % Spot“.
- **Rolling-60** (Befund 6): Wert an Paartag t nur, wenn die 60 Paartage t−59…t alle gültige Paarrenditen haben;
  sonst unbekannt. Python `compute_spot_vol_beta` identisch (Index 59 erst mit 60 gültigen Renditen).
- **Regime-Badge (P1):** aktuelles Rolling-Beta gegen Quantile q20/q80 (linear, numpy-Methode) aller Rolling-Betas
  im Anzeigezeitraum, beschreibend: > 0 → „positiv (anomal)“; ≤ q20 → „Vol reagiert stärker als üblich“ (steilere
  negative Steigung); ≥ q80 → „schwächer als üblich“; sonst „üblich“. Weniger als 60 Rolling-Werte oder q20 = q80 oder
  aktuelles Rolling unbekannt → „nicht bestimmbar“. Python `classify_beta`, `regime_color`, `analyze_vix_extremes`,
  `_first_day_of_regime`, `_compute_forward_stats` haben keinen Aufrufer (Streamlit gelöscht) → entfernen.
- **Ereignisse (P2, Befund 3):** Bedingung c(t) ∈ {wahr, falsch, unbekannt}. Eintritt an t, wenn c(t)=wahr und
  c(t−1)=falsch (bekannt). Sperre: ein Eintritt innerhalb von 10 Paartagen nach dem letzten **akzeptierten** Ereignis
  wird verworfen und nicht nachgeholt (nur Eintritte zählen ohnehin). Ereignisse nur mit Datum im Anzeigezeitraum,
  Bedingungen aber über den Vorlauf ausgewertet (Zeitraumwechsel definiert spätere Ereignisse nicht neu, solange
  der Vorlauf reicht).
  - Vol-Spike: Vol-Schluss ≥ Schwelle; Complacency: ≤ Schwelle (Schwellen wie bisher je Index).
  - **Beta-Stress:** Rolling-Beta(t) ≤ expandierendes Quantil q_p aller Rolling-Betas **vor** t (Standard p = 10 %,
    Eingabe 1–50 %), erst ab 252 vorherigen gültigen Rolling-Werten; vorher unbekannt.
  - Text: „Ereignisse können sich bei 20 und 60 Tagen überlappen; die Fälle sind nicht unabhängig.“ „entkoppelt“ entfällt.
  - Forward-Statistik je Horizont mit eigenem n.
- **Buckets (Befund 2):** Quintilsgrenzen aus Vol-Schlüssen im Anzeigezeitraum (beschreibend, Text sagt das).
  Spalten: Tage, % Zeit, **Ø nächster Tag (t → t+1)**, Trefferquote nächster Tag, Ø +5, +20, +60 — jede mit n
  (Tooltip/zweite Zeile). Immer einfache Renditen (expm1), unabhängig vom Log-Schalter. Diagramm zeigt Ø nächster Tag.
- **Letzter Tag gegen die Regression (P3):** immer einfache Prozentänderungen (unabhängig vom Schalter, Text sagt
  das). Training = alle gültigen Paartage im Anzeigezeitraum **außer** dem ausgewerteten Tag; OLS darauf; Residuen
  aller Trainingstage gegen genau diese Gerade; s = Stichproben-Std (÷ N−2) der Trainingsresiduen.
  Ausgabe: erwartet α+β·x, Ist y, Residuum (Pp), z = Residuum/s (ohne Wahrscheinlichkeit), **k = Anzahl
  Trainingstage mit Residuum strikt größer**, Text „k von N Tagen lagen weiter über der Linie“. Zweite Zählung im
  Stil der Grafik, aber in Prozent: nur wenn x < 0 und y > 0: Tage mit x_heute < x < 0 und y > y_heute (strikt).
  Bei x ≥ 0 oder y ≤ 0 entfällt die zweite Zählung mit Hinweis. Zusätzlich ein Satz in der Methodik, warum Prozent
  statt Vol-Punkte (Punkte skalieren mit dem Niveau). Kein Vorschauwert, kein Signaltext.
- **VRP (P4):** RV21 aus den gespeicherten Spot-`log_return`: 21 aufeinanderfolgende bekannte Renditen,
  √(252/20 · Σ(r−r̄)²)·100, unabhängig vom Schalter; sonst unbekannt. VRP = Vol-Schluss − RV21 am selben Paartag.
  Zwilling: Probe gegen `shared/realized_vol.rv_reihe_aus_returns` auf derselben Renditereihe (inkl. None-Lücke).
  Texte „30d“ → „21 Handelstage (≈ 30 Kalendertage)“; „short-vol opportunity“/„often a precursor“ und DE-Gegenstück
  ersetzen durch reine Beschreibung.
- **OVX (Befund 5):** Spot-Auswahl nur noch USO (OVX wird aus USO-Optionen berechnet); CL=F entfällt.
- **Tägliches Renditeprodukt (Befund 8):** Umbenennung von „Daily Beta“ in „Tägliches Renditeprodukt
  (Spot × Vol)“, EN-Legende korrigieren (grün = gegenläufig/negativ), Texte zum wählbaren Rolling-Fenster entfernen
  (fest 60).

## Texte

DE in der Seite + `en.json`, dynamische Texte via `SA.i18n.t`, `_JSON_VER` erhöhen, `verify_en` FAIL 0.
Methodik: Beta-Größe (VIX typisch −4…−6 % je 1 % seit 1990; Zahl wird nicht fest in den Text geschrieben, sondern
live gezeigt), Regime/Stress/Ereignis-Definitionen wie oben.

## Wächter `scripts/verify_spot_vol_beta.py` (ins Deploy-Gate)

node führt `spot-vol-compute.js` aus; unabhängige numpy-Referenz. Fälle: fehlende Sitzung in Vol bzw. Spot (keine
Zweitagesrendite), Basiswechsel im Close bei unverändertem `log_return` (keine Wirkung auf Renditen/Forward/RV),
konstante Reihe, Quantil-Gleichstände, erster gültiger Rolling-Wert (Index 59 erst mit 60), expandierendes Quantil
(< 252 → unbekannt), Eintrittslogik (25 wahre Tage → 1 Ereignis; unbekannt → falsch ist kein Eintritt; Sperre ohne
Nachholen), Forward-n je Horizont, Residuum/Rang strikt ohne aktuellen Tag, RV21 = `rv_reihe_aus_returns`,
Zeitraumgrenze unter sechs Zeitzonen (TZ im Prozess, wie verify_seasonal_twins Block 4b), Python-Rolling = JS-Rolling.
Mutationstest in isolierter Kopie. Render-/Ladepfad: `verify_seiten_kurse.py` (Seite in jsdom) muss weiter grün
sein; dort zusätzlich prüfen, dass `log_return` angefordert wird.

## Fragen
1. Erfüllt v2 alle Auflagen aus Runde 1? Wo nicht?
2. Ist die Annahme „Spot-Reihe = Sitzungsachse“ für Forward-Renditen vertretbar, oder brauche ich
   `SA.boersenkalender` (die Seite bindet ihn ein; Ticker ^GSPC/SPY/^NDX/QQQ/USO alle NYSE)?
3. Neue Lücken?

Antwort: Befunde (Schwere, Datei:Zeile), Urteil „tragfähig“/„nicht tragfähig“ + Auflagen.
