**Ja zum rein lesenden Trockenlauf. „Leg-Qualität zuerst untersuchen“ ist getragen; „Hauptursache bewiesen“ geht noch zu weit.** N, V und H bleiben Untersuchungskandidaten.

Geprüft gegen HEAD `88c02ff` und die lokale Probe. Keine Änderungen oder API-Abrufe durchgeführt; die berichteten Zahlen habe ich nicht unabhängig reproduziert. Die Probe ist unversioniert und sollte zusätzlich zum Repo-Commit mit eigenem Hash dokumentiert werden.

**1. Was die Auswertung trägt**

C 29.10. zeigt überzeugend: Ein Extrapolationslimit allein reicht nicht. Bei einer Stützstelle genau auf 30 Tagen hat die zweite Stützstelle rechnerisch Gewicht null; der auffällige Wert kommt unmittelbar aus dem 30-Tage-Leg. Die Varianzinterpolation bestätigt diesen Zusammenhang. [black_scholes.py:121](C:/dev/Seasonaledge/shared/black_scholes.py:121)

Folgende Aussagen würde ich abschwächen:

- **Dünne Legs sind ein Verdacht auf schlechte Messqualität, kein Fehlernachweis.** Wenig Volumen beweist weder einen veralteten Preis noch eine falsche IV. Im Repository ist sogar ein Gegenbeispiel dokumentiert, bei dem der Volumenfilter den besseren Kontrakt entfernt hat. V deshalb zunächst als erklärende Kennzahl und Regelvariante untersuchen. [black_scholes.py:86](C:/dev/Seasonaledge/shared/black_scholes.py:86)
- **„Extrapolation verstärkt, erzeugt aber nicht“ ist zu allgemein.** Der Fall ohne Extrapolation widerlegt deren Notwendigkeit, schließt sie aber als eigenständige Ursache anderer Auffälligkeiten nicht aus. Die Rechnung extrapoliert die totale Varianz für Call, Put und ATM separat. [black_scholes.py:107](C:/dev/Seasonaledge/shared/black_scholes.py:107)
- **„Historisch belegt“ weiterhin von „numerisch reproduziert“ unterscheiden.** Identische Ergebniswerte allein belegen keine identischen damaligen Eingaben. Ebenso beweist die fehlende Reproduktion von MS/XLF nicht, dass ausschließlich der ältere Code verantwortlich war. Diese Einschränkung stand bereits in Runde 2. [plan_v2_antwort.md:9](C:/dev/Seasonaledge/docs/review_prompts/2026-10-13_skew_ausreisser_plan_v2_antwort.md:9)
- **Leere Ergebnisse als „keine verwertbare Tagesbar geliefert“ ausweisen.** `_bars` überspringt auch ungültige Datensätze; daraus folgt nicht zwingend „kein Handel“. Der Zeitpunkt des letzten Einzeltrades wird ebenfalls nicht geliefert. [backfill_skew_massive.py:131](C:/dev/Seasonaledge/scripts/backfill_skew_massive.py:131)

Die unterschiedliche Auswahl ist dagegen im Code klar nachvollziehbar: Backfill bildet die Rangliste nach erfolgreicher Leg-Berechnung neu, Live probiert die ursprüngliche Rangliste. Die gemeinsame Entscheidung bleibt notwendig. [backfill_skew_massive.py:355](C:/dev/Seasonaledge/scripts/backfill_skew_massive.py:355), [compute_options_skew.py:547](C:/dev/Seasonaledge/scripts/compute_options_skew.py:547)

**2. Trockenlauf: richtig, mit folgenden Präzisierungen**

**Die bestehende Probe braucht vor der Skalierung zusätzliche Instrumentierung:**

- Sie protokolliert derzeit Gesamtzahl und Gesamtvolumen der bepreisten Kontrakte. Rohpreise, Kontraktidentitäten und Volumen der tatsächlich verwendeten Flügel beziehungsweise ATM-Anker fehlen im Ergebnis. Damit lassen sich die geplanten N/V-Regeln noch nicht beurteilen. [skew_phase0_probe.py:73](C:/dev/Seasonaledge/scripts/research/skew_phase0_probe.py:73)
- Der zweite Abruf für den Backfill verschluckt Exceptions trotz `strict=True` und zählt sie nicht. „Keine Abruffehler in allen Pfaden“ ist mit diesem stdout nicht nachgewiesen. Bereits geladene Bars im Speicher wiederverwenden und Fehler separat vom fachlichen Ausschluss behandeln. [skew_phase0_probe.py:104](C:/dev/Seasonaledge/scripts/research/skew_phase0_probe.py:104)
- `interp_roh` verwendet bereits gerundete ATM-Leg-Werte; w/h werden ebenfalls gerundet ausgegeben. Für Grenzwertvergleiche und spätere Fixtures Werte vor diesen Rundungen erfassen. [skew_phase0_probe.py:88](C:/dev/Seasonaledge/scripts/research/skew_phase0_probe.py:88), [black_scholes.py:504](C:/dev/Seasonaledge/shared/black_scholes.py:504)

**Die Stichprobe reicht zur Exploration, noch nicht zur abschließenden Validierung:**

1. Acht Symbole, Datumsgrenzen, Seed und gezogene Datumsliste festhalten. Aus allen Handelstagen ziehen, einschließlich bisher nicht rankbarer Tage; möglichst über Monate verteilen. Bekannte Problemfälle und gezielte Earnings-/Verfallskontrollen separat ergänzen.
2. „Statistisch auffällig/unauffällig“ verwenden, nicht „schlecht/gut“. Auffälligkeitsdefinition vorab fixieren; Schwellenentwicklung und eine zurückgehaltene Prüfmenge trennen.
3. N je Call/Put und Zielregion **vor und nach den bestehenden Filtern** messen. Delta-Band, Mindestvolumen je tatsächlich verwendetem Kontrakt und ATM-Klammer um den **Forward** eindeutig definieren; zusätzlich Ankerabstände erfassen. Die jetzige Leg-Funktion ignoriert die bereits berechnete Klammerinformation. [black_scholes.py:438](C:/dev/Seasonaledge/shared/black_scholes.py:438), [black_scholes.py:479](C:/dev/Seasonaledge/shared/black_scholes.py:479)
4. Baseline, nur gemeinsame Auswahl, nur Leg-Regeln, nur H und Kombination getrennt vergleichen. Nach Ausschluss eines Kandidaten die nächste Gruppe prüfen. H = 0,5 verwirft zunächst bestimmte **Paare**, nicht zwangsläufig den gesamten Tag.
5. Abdeckung mit absoluten Zahlen und Unsicherheit berichten. **40 Tage ergeben keine belastbare vollständige Rangwirkung:** Der aktuelle Rank hängt von Minimum und Maximum des gesamten Fensters ab. Stichprobenrang und partielle Änderungen im eingefrorenen Bestand ausdrücklich kennzeichnen; beide Zeta-Achsen, Percentile, aktuelle Session und `MIN_NORM` berücksichtigen. [skew.html:238](C:/dev/Seasonaledge/landing/pages/skew.html:238), [skew.html:258](C:/dev/Seasonaledge/landing/pages/skew.html:258)

Live-Quotes lassen sich mit diesem historischen Bars-Trockenlauf nicht validieren. Der aktuelle Live-`own_bs`-Pfad verwendet ebenfalls Tagesclose und Volumen. Eine zusätzliche Quote-Regel braucht später eine eigene Messbasis. [compute_options_skew.py:500](C:/dev/Seasonaledge/scripts/compute_options_skew.py:500)

**3. Umfang der Freigabe**

Freigegeben ist der entsprechend instrumentierte Diagnose-Trockenlauf über ungefähr 320 Ticker-Tage, mit Ergebnissen im Speicher/stdout und deaktiviertem Bytecode-Schreiben. Noch keine Schwellenfestlegung, Regelaktivierung oder Bestandsänderung.

„Nur Massive-Abrufe“ erfordert eine Präzisierung: `_closes` liest Supabase. Wenn ausschließlich Massive-Netzwerkzugriffe vorgesehen sind, muss die Spot-/Handelstagsbasis vorher eingefroren bereitliegen. [backfill_skew_massive.py:179](C:/dev/Seasonaledge/scripts/backfill_skew_massive.py:179)

**FREIGABE (Plan): ja**
