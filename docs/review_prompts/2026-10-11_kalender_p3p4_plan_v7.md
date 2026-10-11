# Tage nach Börsenkalender — Plan P3/P4 v7 (nur Releasebindung + Sicherungsumfang)

Runde 6: [Plan v6](2026-10-11_kalender_p3p4_plan_v6.md) · [Antwort](2026-10-11_kalender_p3p4_plan_v6_antwort.md) (2 Befunde).
Alles aus v6 und früher + A/B/C gilt, außer den folgenden Punkten. Read-only.

<task>Prüfe, ob V9 jetzt als Bauplan freigegeben werden kann.</task>

## 1 Jede Datei prüft ihre eigene Kennung (Befund 1)
`inject_credentials.sh` ersetzt in **jeder** eigenen JS-Datei unter `landing/js/` den Platzhalter `%%RELEASE%%` in
deren erster Zeile `SA.__release('%%RELEASE%%');` und setzt in jedes HTML `window.__SA_RELEASE`. `SA.__release(k)`
(in `methode.js`, als erstes eingebunden) vergleicht **die Kennung dieser Datei** mit `window.__SA_RELEASE`; bei
Abweichung wirft es einen `ReleaseFehler` **vor** jeder Definition der Datei (die Datei definiert nichts, kein
Rechner existiert) und startet das einmalige Neuladen (v6, Schutz gegen Schleife). Inline-Skripte gehören zum
HTML und tragen dessen Kennung. Damit kann eine neue Datei unter einem alten HTML nie rechnen, und eine alte
Datei unter einem neuen HTML ebenso nicht — unabhängig von `methode.js` und vom Zeitpunkt.
Wächter: jede eigene JS-Datei beginnt mit der Zeile (sonst rot); Probe in jsdom: (a) HTML+`methode.js` alt,
weiteres Skript neu; (b) umgekehrt; (c) Pause über das gesamte Fenster — jeweils keine Rechnung, Neuladen bzw.
sichtbarer Fehler. Mutation: Zeile in einer Datei entfernt → Wächter rot; Vergleich auf `releaseOk` statt eigener
Kennung → Probe (a) rot.

## 2 Sicherungsumfang = alles, was die Injection verändert (Befund 2)
Die Sicherung und Rücksicherung umfasst **die Menge der Dateien, die `inject_credentials.sh` verändert**, plus die
generierten Ausgaben: `landing/` (inkl. `landing/en/`), `seo/tools/`, `seo/output/`, `blog/output/`. Die Liste
wird nicht von Hand geführt: ein Wächter leitet sie aus den Pfadmustern des Skripts ab und vergleicht sie mit
der Sicherungsliste (fehlt ein Muster → rot). Nach der Rücksicherung: HTTP-Prüfung je Verzeichnis mindestens einer
Datei gegen Sicherungsprüfsumme **und** alte Releasekennung, ausdrücklich `/tools/trading-day-converter` (bzw. die
tatsächlich ausgelieferte Converter-Adresse).

## Ausgabevertrag
**Urteil** · **Befunde** · **Auflagen**. ≤ 20 Zeilen.
