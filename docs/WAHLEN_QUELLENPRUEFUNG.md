# Wahltermine – Recherchebericht (Stand 2026-10-06)

Datei: `elections_research.json` (88 Einträge: 34 US-Präsidentschaft 1896–2028, 33 US-Midterms 1898–2026, 21 Bundestagswahlen 1949–2025). Erzeugt von `build.py` im selben Ordner aus den heruntergeladenen Rohquellen (archives.gov, history.house.gov, senate.gov über web.archive.org, Wikipedia-Rohtext, NYSE-Feiertagshistorie, Yahoo ^GSPC, Bundeswahlleiterin-PDF „Ergebnisse früherer Bundestagswahlen“ Juni 2025, BVerfGE 62,1, BGBl.).

## Ergebnis der Gegenprüfung

| Bereich | Quellen | Ergebnis |
|---|---|---|
| US-Datum (Regel „Dienstag nach dem ersten Montag im November“) | Berechnung + Wikipedia-Infobox | 67/67 `rule_ok: true` |
| Sieger/Partei Präsident | archives.gov + Wikipedia | 33/33 übereinstimmend |
| prior_party | Wikipedia-Infobox + archives.gov-Notizen/Vorwahl | 34/34 |
| House vorher/nachher | history.house.gov (Sitze) + Speaker laut Wikipedia | 32/32 nach Speaker-Regel übereinstimmend (2 Sonderfälle, s. u.) |
| Senat vorher/nachher (ab 1914) | senate.gov (Archivkopie) + Wikipedia | 28/28 |
| NYSE am Wahltag geschlossen | NYSE-Feiertagshistorie + fehlender S&P-500-Tagesbalken | 1928–2024: 49/49 übereinstimmend; 1896–1926: nur eine Quelle |
| Bundestag Datum, stärkste Partei | Bundeswahlleiterin + Wikipedia (Stimmenzahlen) | 21/21 |
| Kanzler vorher/nachher | bundeskanzler.de + de/en-Wikipedia | 21/21 |
| Auflösungsdaten | Wikipedia, WD Bundestag, BVerfGE, BGBl., bpb | 4/4 (1983 korrigiert, s. u.) |

**Nicht verifizierte Felder: 16** – jeweils `nyse_verified: false` für 1896–1926 (8 Präsidentschafts-, 8 Midterm-Wahlen). Grund: Die einzige gefundene Quelle ist die NYSE-Feiertagshistorie („Closed every year through 1968“); tägliche Kursdaten zur unabhängigen Prüfung gibt es erst ab 1928. Inhaltlich gibt es keinen Hinweis auf eine Abweichung. Keine Felder auf `unknown`.

## NYSE-Prüfung

Die Erwartung stimmt ausnahmslos: geschlossen an jedem Wahltag bis 1968, danach nur 1972, 1976 und 1980, seit 1982 geöffnet. Die NYSE-Liste nennt „Closed every year through 1968. Closed presidential election years only, 1972-1980.“ Die Yahoo-Reihe ^GSPC hat an jedem dieser Tage ab 1928 keinen Balken und an allen übrigen einen. Montag und Mittwoch waren jeweils Handelstage. Einzige Besonderheit: **1914** war die Börse ohnehin vom 31.07. bis 27.11.1914 wegen Kriegsausbruch geschlossen.
Quelle der NYSE-Liste: Kopie unter ltadvisors.net („Revised through November 2008“). nyse.com selbst hat das Dokument nicht mehr greifbar.

## Diskrepanzen und Auflösung

1. **House 65. Kongress (Vorher-Wert für 1918):** history.house.gov zählt 215 R gegen 214 D, eine Sitzmehrheit also bei R. Den Speaker stellten aber die Demokraten (Champ Clark), weil sie das Haus mit Stimmen von Dritten organisierten. Entschieden nach der vorgegebenen Speaker-Regel: `house_before = US-D`. Wikipedia (Speaker vor der Wahl 1918) stimmt zu.
2. **House 72. Kongress (Nachher-Wert für 1930):** Am Wahlabend lag R mit 218:216 vorn. Laut Fußnote 2 bei history.house.gov starben 14 gewählte Abgeordnete vor Sitzungsbeginn, die Nachwahlen drehten die Mehrheit, Speaker wurde Garner (D). Daher `house_after = US-D`. Die Rohtabelle ohne Fußnote würde R ergeben.
3. **Senat 2002 (Vorher-Wert):** Der 107. Senat wechselte dreimal die Kontrolle (D 3.–20.01.2001 per VP Gore, R bis 06.06.2001, danach D nach dem Wechsel von Jeffords). Am **12.11.2002**, also eine Woche *nach* der Wahl, kippte die Zahlenmehrheit durch die Nachwahl in Missouri zu R, ohne Neuorganisation. Am Wahltag lag die Kontrolle bei D: `senate_before = US-D`. Die erste Zeile der senate.gov-Tabelle wäre irreführend und wurde im Skript bewusst überschrieben.
4. **Senat 2022:** vorher 50:50, Kontrolle D über die Stimme von VP Harris. Nachher führt senate.gov „47 D + 4 I“, weil Sinema im Dezember 2022 austrat; Wikipedia rechnet 51 D inklusive der Unabhängigen. Beide ergeben Kontrolle D.
5. **Senat 1926/1930/1954:** jeweils ohne absolute Mehrheit (48 Sitze), aber unstrittig organisiert durch R/R/D. Steht in den Notizen.
6. **Bundestagsauflösung 1983:** de.wikipedia („Vertrauensfrage“) nennt den **7. Januar 1983**. Die Wissenschaftlichen Dienste des Bundestags, das Kalenderblatt auf bundestag.de und das Urteil BVerfGE 62, 1 nennen eine **Anordnung vom 6. Januar 1983**, veröffentlicht im BGBl. I S. 1 am 7. Januar, am selben Tag folgte die Fernsehansprache von Carstens. Festgelegt: `dissolution_date = 1983-01-06`, zusätzlich `dissolution_published = 1983-01-07`. Wikipedia führt hier das Datum der Verkündung.
7. **Vertrauensfrage 1972:** Laut WD Bundestag stellte Brandt sie am 20.09., laut Wikipedia wurde am 22.09. abgestimmt. Kein Widerspruch: gestellt am 20., abgestimmt und aufgelöst am 22.09.1972.
8. **2024/25:** bpb schreibt „fünf Tage später“, abgestimmt wurde also am 16.12.2024. Das Auflösungsdatum 27.12.2024 ist belegt durch BGBl. 2024 I Nr. 434 (Ausfertigung 27.12.2024).
9. **Bundestag 2021, Stimmenzahlen:** Die Bundeswahlleiterin rechnet die Berliner Wiederholungswahl vom 11.02.2024 ein (SPD 11.901.558, Union 11.177.747), Wikipedia zeigt den ursprünglichen Stand (11.901.556 / 11.177.746). Für die Rangfolge unerheblich. Ins JSON gingen die amtlichen Werte.
10. **Bundestag 2002:** Laut Bundeswahlleiterin und Wikipedia übereinstimmend gleiche Prozentwerte (38,5 %), die SPD lag mit nur **6.027 Zweitstimmen** vor CDU/CSU zusammen. `strongest_party = DE-SPD`.
11. **Bundestag 1949:** Es gab nur eine Stimme (die Bundeswahlleiterin vermerkt „1949 nur Erststimmen“). Die stärkste Partei wurde mit dieser Stimme bestimmt (Union 7.359.084 gegen SPD 6.934.975).
12. **senate.gov** liefert für Skripte HTTP 403. Gelesen wurde über Snapshots von web.archive.org (Stand 2024 für 63.–118. und 2026 für den 119. Kongress). Das ist im JSON vermerkt.

## Hinweise für die Auswertung

- **Maine** wählte das House (und den Senat) bis 1958 im September (bei jeder Midterm 1898–1958 in den Notizen). 1898/1902/1906 wählten auch Oregon (Juni) und Vermont (September) früher. Maßgeblich ist das bundesweite November-Datum.
- **Stärkste Partei ≠ Kanzlerpartei** 1969, 1976 und 1980: Die Union war stärkste Kraft, der Kanzler kam von der SPD (sozialliberale Koalition). Wer „Wahlsieger“ als Signal nutzt, muss wählen, welches Feld er meint.
- `chancellor_change` (Personenwechsel) und `chancellor_party_change` sind bei allen Wahlen identisch. Wechsel gab es 1969, 1998, 2005, 2021 und 2025, die Wechsel innerhalb einer Wahlperiode 1963, 1966, 1974 und 1982 fallen nicht auf einen Wahltag.
- **1990** gilt nicht als vorgezogen (laut Fußnote der Bundeswahlleiterin vorgezogen: 1972, 1983, 2005, 2025).
- Zwei offene Termine (2026, 2028): Parteien und NYSE gesetzt nach aktuellem Stand bzw. heutiger Praxis, `status: scheduled`.
