# Paket 1 (P1a/K1): Kalenderkorrekturen — Code-Review Runde 1

Plan: [v4](2026-10-10_xetra_tdoy_plan_v4.md) · deine Recherche: [Antwort 4](2026-10-10_xetra_tdoy_plan_antwort4.md).

<task>
Ich habe **nur K1** umgesetzt — die von dir belegten Kalenderfehler — plus einen Wächter. K2–K7
(Gültigkeitsstatus, strenge Börse, Ticker-Zuordnung, Nummernfunktion, Wirkungsbericht) folgen in eigenen
Paketen. Prüfe den Diff (`git diff` im Arbeitsbaum + die zwei neuen Dateien). Read-only.
</task>

## Änderungen
- `shared/nyse_holidays.py`: acht Sonderschließungen 1972–1994 (deine N1-Liste ab 1971). Vor 1971 bewusst
  nichts ergänzt; Kommentar sagt „nicht geprüft“.
- `shared/exchange_holidays.py`:
  - LSE: Neujahrsersatz bei Samstag **und** Sonntag; Boxing Day auf Sonntag (Weihnachten Samstag) → 28.12.;
    2002-06-03 und 2011-04-29 ergänzt. 1999-12-31 bewusst nicht (dein Hinweis: kein LSE-Beleg).
  - TSE: Regeln datumsabhängig (Seijin 15.1. bis 1999; Umi 20.7. 1996–2002, 3. Mo ab 2003; Keiro 15.9.
    1966–2002, 3. Mo ab 2003; Taiiku 10.10. 1966–1999, 2. Mo ab 2000; Kaisergeburtstag 23.12. nur 1989–2018);
    Ersatztag erst ab 1973, bis 2006 nur der direkte Folgetag, wenn dieser kein Feiertag ist; Tabellen
    `_TSE_OLYMPIA` (2020/2021 ersetzt Umi/Sport/Yama), `_TSE_EINMALIG_FEIERTAG` (2019-05-01, 2019-10-22;
    4/30 und 5/2 entstehen als Brückentage), `_TSE_BOERSE_GESCHLOSSEN` (2020-10-01).
  - HKEX 2016 + KRX 2016: 1.1. ergänzt; KRX: 2017-09-22, 2017-12-20, 2022-01-03, 2022-05-09 entfernt.
    Kommentar: Tabelle stammte aus Kurslücken, neue Einträge nur aus offiziellen Kalendern.
- `scripts/verify_kalender_sollfaelle.py`: 75 wörtliche Sollfälle (offen **und** zu) mit Quellenkürzel.
  Gegen den alten Code (`git archive HEAD shared`): **23/75**, Exit 1. Mit neuem Code 75/75.
- `scripts/verify_kalender_sollfaelle_mutation.py`: 13 Mutationen, 13/13 gefangen, zweimal identisch;
  zwei Gegenproben (Ausnahme, fehlender Anker) richtig verworfen.

## Gemessen: alt gegen neu, jeder Tag 1950–2035, alle 13 Börsen
NYSE 8 Tage (genau die acht) · LSE 26 Tage (die 11 Belegfälle + regelgleiche Ersatztage 1954–2033) ·
HKEX 1 · KRX 5 · TSE 271 Tage, davon 27 = deine Belegliste, der Rest vor 2000 (Regeln vor ihrer Einführung
nicht mehr angewendet: kein Meerestag vor 1996, kein Keiro/Taiiku vor 1966, kein Ersatztag vor 1973) ·
alle übrigen Börsen 0. Bestehende Wächter grün: `verify_kalender_zwilling` (NYSE/XETRA 2000–2035, 0 Fehler),
`verify_elections`, `verify_wahlen_build`, `verify_plain_vanilla_1a` 50/50, `_1b --ohne-snapshot` 39/39,
`verify_seasonal_twins`, `verify_stress_ampel --ohne-snapshot` 32/32.

## Nebenbefund (eigener Fehler, behoben)
Zwei Mutationen meldeten zuerst den Fehler der **vorigen** Mutation: Python prüft `.pyc` nur gegen
Quell-mtime (Sekunden) und -größe; eine Mutation gleicher Länge, in derselben Sekunde zurückgeschrieben, lief
aus dem mutierten Cache. Jetzt `PYTHONPYCACHEPREFIX` = frisches Temp-Verzeichnis je Probelauf. **Fünf weitere
Mutationstests im Repo** starten ihre Probe ohne diese Isolation (`grep "subprocess.run(\['py', '-3.14'"`).

## Fokusfragen
1. Stimmen die TSE-Regeln für 2000–2030 vollständig (inkl. Brückentage 2019, Ersatztag 8.8.2021 → 9.8.,
   Kokumin no Kyujitsu um den Keiro/Shubun-Fall wie 2009/2015/2026-09-22)? Fehlt eine Regel, die zwischen
   2004–2018 oder 2022–2030 greift und mein Vergleich nicht zeigt (weil alter = neuer Code falsch)?
2. LSE: Ist die Ersatzregel jetzt für alle vier Kombinationen (25.12. Fr/Sa/So, 1.1. Sa/So) richtig?
3. Wirkung: Diese Änderung wirkt sofort auf `is_trading_day` für `^FTSE`, `RR.L`, `BA.L`, `^N225`, `^HSI`,
   `^KS11` und NYSE-Reihen 1972–1994. Wo wird das **jetzt** sichtbar (gespeicherte `prices.tdoy` ändert sich
   erst mit P5; `tdom_stats` zählen Zeilen)? Muss etwas davon vor dem Commit abgefangen werden?
4. Ist der Mutationstest fachlich wirksam, oder gibt es eine Mutation, die ich hätte einbauen müssen
   (z. B. „Ersatztag vor 1973“)?
5. Die fünf anderen Mutationstests: echter Nichtdeterminismus-Defekt? Dann gehört die Isolation in den
   gemeinsamen Helfer — welcher?

## Ausgabevertrag
**Urteil** (Freigabe / Freigabe mit Auflagen / keine Freigabe) · **Befunde** (nummeriert, Datei:Zeile,
Beleg) · **Antworten** (je ≤ 6 Zeilen). Höchstens 80 Zeilen.
