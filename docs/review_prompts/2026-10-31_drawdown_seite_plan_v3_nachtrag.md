# Nachtrag zu Bauplan v3 — fehlende Kurszeilen in ungeprüften/Konventions-Kalenderjahren

Beim ersten Zwillingslauf (Python = JS, 0 Abweichungen auf QQQ, ^GDAXI, BTC-USD, EURUSD=X) zeigte die strenge
Lückenregel aus v2/v3 („fehlende Zeile an einer Kalendersitzung → Pfad ab dort unbekannt“) ein Problem:

| Reihe | Lücken | Kalenderstatus der Lückenjahre | häufigste Tage |
|---|---:|---|---|
| QQQ (NYSE) | 0 | – | – |
| ^GDAXI (XETRA) | 244 | **alle `ungeprueft`** (1959–1999) | 24.12. (28), 17.06. (21), 31.12. (19) |
| BTC-USD (CRYPTO) | 0 | – | – |
| EURUSD=X (FOREX) | 198 | **alle `konvention`** | 01.01. (21), 11.11. (15), 25.12. (15), 04.07. (12) |

In Jahren mit Status `belegt` gibt es in diesen Reihen **keine** Lücke. Die Lücken sind erkennbar Schließungen, die
der Kalender dort nicht kennt (17.06. = Tag der Deutschen Einheit bis 1990, Heiligabend/Silvester), bzw. Feiertage
ohne Kursstellung im Forex-Konventionskalender. Mit der strengen Regel wäre die gesamte DAX-Historie ab 15.10.1959
und die gesamte EURUSD-Historie ab 01.01.1975 „nicht bestimmbar“.

**Vorgeschlagene Regel:**
- Fehlende Kurszeile an einer Kalendersitzung eines Jahres mit Status `belegt` → echte Lücke (Pfad ab dort
  unbekannt, wie v3).
- Fehlende Kurszeile an einer Kalendersitzung eines Jahres mit Status `ungeprueft`, `annahme` oder `konvention` →
  **als geschlossen angenommen**: die Sitzung entfällt aus der Achse (Rendite der folgenden Sitzung = Summe der
  Zeilen seit der vorigen vorhandenen Sitzung). Anzahl und Jahre werden ausgewiesen („244 Sitzungen ohne Kurs in
  Jahren mit ungeprüftem Kalender als geschlossen angenommen“).
- Fehlender oder nicht endlicher `log_return` bleibt in jedem Jahr eine echte Lücke.
- Sitzungszählungen (Drawdown-Dauer usw.) zählen nur Sitzungen der Achse; in Annahmejahren also ohne die
  angenommenen Schließungen.

Frage: tragfähig? Schwachstelle ist eine echte Datenlücke in einem ungeprüften Jahr, die so unsichtbar wird —
ausreichend durch die Kennzeichnung (Anzahl, Jahre) abgedeckt, oder braucht es eine Obergrenze (z. B. mehr als
N aufeinanderfolgende fehlende Sitzungen → echte Lücke)?
Schluss: FREIGABE, FREIGABE MIT AUFLAGEN oder NICHT TRAGFÄHIG.
