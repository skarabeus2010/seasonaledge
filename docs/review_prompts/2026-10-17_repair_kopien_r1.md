# Codex-Review: Reparatur kopierter Kurszeilen (2026-10-17, Runde 1)

Nur lesen. Neues Skript `scripts/repair_kopierte_zeilen.py` (+ Inventar `shared/produktionssperre.py`). Nutzerfreigabe
für den Schreibzugriff liegt vor. Befund: 526 flache Zeilen (Hoch = Tief, meist Vortagsschluss, Volumen 0) an
Handelstagen bei 10 Tickern (SIE.DE, MUV2.DE, ADS.DE, BMW.DE, ALV.DE, MBG.DE, BAS.DE, DTE.DE, GC=F, DOGE-USD), für die
Yahoo heute echte Kerzen liefert. Messung: `/root/kopierte_zeilen.jsonl` (nur lesend).

## Regel (Docstring)
Faktor f aus DB-Schluss/Yahoo-Schluss am nächsten sauberen Tag davor und danach (Abweichung > 0,1 % → Basiswechsel,
übersprungen); O/H/L/C = Yahoo × f, Volumen = Yahoo, log_return der Kandidaten und der Folgezeile neu; Ketten
aufeinanderfolgender Kandidaten; Kontrolle: alte Σ log_return über Kette + Folgezeile = ln(C_folge/C_vor); Ketten
neben übersprungenen Kandidaten werden nicht angefasst. Trockenlauf Standard; `--schreiben`: Sicherung → Upsert
(`upsert_prices`, nur gesendete Spalten) → Rücklesen. Synthetischer Test: Kopie korrekt umgerechnet, Basiswechsel
übersprungen.

## Prüffragen
1. Ist die Umrechnung richtig — insbesondere: welche Kursbasis hat Yahoos `close` (split-, nicht dividendenbereinigt)
   gegenüber unserer DB, und genügt die Faktorgleichheit p/n als Schutz vor einem Ex-Tag zwischen p und n
   (Dividende genau AM Kandidatentag)?
2. Volumen: Ist Yahoo-Volumen mit unserem gespeicherten Volumen vergleichbar (Split-Bereinigung)?
3. Futures (GC=F, Rollwechsel) und Krypto (DOGE-USD, Tagesgrenze UTC) — Sonderfälle?
4. Kann ein Upsert etwas anderes verändern als die geplanten Spalten/Zeilen? Ist das Rücklesen ausreichend?
5. Wird `tdom/tdoy`, `source` oder irgendein Folgewert (monthly_stats u. a.) berührt, der danach neu gerechnet
   werden muss?
6. Fehlt ein Schutz (z. B. Obergrenze, Abbruch bei hoher Überspringquote)?

Befunde mit Datei:Zeile und Schwere, am Ende **FREIGABE** oder **KEINE FREIGABE**.
