**FREIGABE (Plan): nein** — die Richtung passt, aber drei P2-Vertragslücken sollten vor der Umsetzung geschlossen werden. Keine P1-Befunde. Read-only geprüft; keine Dateien geändert.

1. **P2 — `neu_rand` darf nicht aus dem gerundeten Percentile entstehen.**  
   Die bestehende [`_pctl`-Definition](C:/dev/Seasonaledge/shared/skew_rang.py:60) zählt strikt kleinere Vorwerte und rundet anschließend. Eine konstante Reihe bekommt deshalb Percentile 0, obwohl kein neuer Extremwert vorliegt. Bei langen Reihen kann außerdem 100 durch Rundung entstehen, obwohl ein früherer Wert höher liegt.

   **Korrektur:** `neu_rand = x_S < min(Vorwerte) oder x_S > max(Vorwerte)`. Gleichstände sind keine neuen Extreme. Tests für konstante Reihen, wiederholte Minima/Maxima und rundungsbedingte 0/100 ergänzen.

2. **P2 — Für „Rang ab 20 Tagen (n = 16)“ fehlt ein Ausgabevertrag.**  
   [`rang_ticker`](C:/dev/Seasonaledge/shared/skew_rang.py:111) lässt eine Metrik bei weniger als 20 Werten vollständig weg. Der Browser kann daraus weder `n` noch den Grund erkennen. Auch „aktueller Wert fehlt“, „Duplikat sperrt Ticker“ und „Historie zu kurz“ sind unterschiedliche Zustände.

   **Korrektur:** separate, im Cron berechnete Verfügbarkeitsmetadaten je Ticker/Fenster/Metrik ausgeben, etwa Anzahl und Status. Den bisherigen Vertrag vollständiger `rang`-Einträge beibehalten; sonst riskieren bestehende Leser unvollständige Rangobjekte. Formulierung: „Rang ab 20 gültigen Beobachtungen“, nicht pauschal „Tagen“.

3. **P2 — „Tagessprung“ kann tatsächlich eine Änderung über mehrere Sessions sein.**  
   Nach dem Filtern ungültiger Werte ist der vorangehende gültige Wert nicht zwingend der vorherige Handelstag. Dasselbe betrifft die Änderungen im Median. Dadurch werden unterschiedlich lange Abstände als Tagesänderungen verglichen.

   **Korrektur bei gleicher Einfachheit:** Text „Sprung zum letzten gültigen Wert — Messung prüfen“, Vorgängerdatum verfügbar machen und die Referenz ausdrücklich als Änderungen zwischen aufeinanderfolgenden gültigen Beobachtungen definieren. Falls „Tagessprung“ bleiben soll, müssen echte benachbarte Handelssessions geprüft werden. Zusätzlich festlegen, ob die aktuelle Änderung im Median enthalten ist; die geplanten mindestens 19 Änderungen passen zu **inklusive aktueller Änderung**.

4. **P3 — Auswahl und Darstellung der Listen brauchen wenige zusätzliche Festlegungen.**  
   Percentile-Gleichstände sind häufig. Deshalb deterministisch sortieren, beispielsweise Percentile, danach Tickersymbol. Höchstens acht verfügbare Einträge zeigen; Überschneidungen beider Listen bei kleinen Universen ausdrücklich zulassen oder vermeiden. Ohne Rand-Schwelle sind es relative Spitzenlisten, nicht zwingend extreme Werte: ein kurzer Hinweis verhindert diese Fehlinterpretation.

   „IV-Niveau“ bezeichnet im bestehenden Rangvertrag das **Flügelmittel**, während IV/RV ATM-IV verwendet. Tooltip und Werteinheiten müssen das unterscheiden; insbesondere liegt `rr.wert` intern in Dezimalvolatilität vor.

**Zu deinen fünf Fragen:**

- **1. Empfehlung: (a).** Den IV/RV-Wert sofort zeigen, den Rang mit gespeicherter RV aufbauen. Das Startdatum ergibt sich aus gültigen Beobachtungen, nicht aus einem garantierten Novembertermin.

  **(b) ist technisch vertretbar**, sofern der Reparaturlauf die identische Herkunft von ATM-IV und VRP nachweist und ausschließlich geeignete Live-Zeilen bearbeitet. Abgeleitete RV muss je Zeile gekennzeichnet werden, etwa durch `rv_1m_source`, ergänzt um Reparaturbericht und Versionsangabe. Vorhandene RV nicht überschreiben; Massive-Zeilen nicht einbeziehen.

  Die Fehlerabschätzung ist knapp zu korrigieren: Bei RV 0,05 liegt die theoretische relative Verhältnisabweichung bei ungefähr **0,1001 %**, bei RV 0,01 bei ungefähr **0,503 %**. Kleine Wertfehler können außerdem Rangfolgen bei eng benachbarten Werten ändern oder die Zulässigkeitsgrenze 0,01 verschieben. Das spricht für (a), obwohl (b) keine grundsätzliche Methodenvermischung sein muss.

- **2. Die Paarung passt zum bestehenden VRP-Vertrag.** Im Tooltip sollte stehen: „Annualisierte ATM-IV für 30 Kalendertage / annualisierte realisierte Volatilität der vergangenen 21 Handelstage.“ Damit werden sowohl die näherungsweise gleichen Monatshorizonte als auch die unterschiedliche Blickrichtung klar. Nur normierte `cm`/`cm_extrap`-Werte zulassen; kein Frontmonat-Fallback. Eingangsprüfung ausdrücklich endlich, numerisch, kein Boolean, ATM-IV positiv, RV ≥ 0,01.

- **3. Als Hinweis ist die 5×-Median-Regel tragfähig**, nach Klärung von Befund 3. Die lokale Kopie enthält Snapshot-Session **2026-10-15**. Bei direkter Anwendung einschließlich aktueller Änderung ergaben sich:

  | Fenster | IV markiert | Skew markiert | RR markiert |
  |---|---:|---:|---:|
  | 92 Tage | 4/149 | 11/149 | 11/149 |
  | 183 Tage | 3/150 | 5/150 | 5/150 |
  | 365 Tage | 3/150 | 6/150 | 6/150 |

  Kein Median war null. Das zeigt keine flächendeckende Markierung, belegt aber weder eine Fehlalarmquote noch die Eignung für kurze IV/RV-Reihen. Daher die einfache Regel zunächst beibehalten; keine statistisch kalibrierte Ausreißererkennung behaupten. Fehlendes Feld bei Median null muss „nicht beurteilbar“ bedeuten.

- **4. Morgen-Mail: vorerst nein.** Das ist kein fehlender Bestandteil von B3b. Die Erweiterung von `rang` sollte allerdings bestehende Mail-Leser unverändert funktionieren lassen; dafür einen Regressionstest vorsehen.

- **5. Folgende Zustände ergänzen:**
  - Kategorieauswahl gilt auch für Listen; Ticker ohne Kategorie bleiben wie bisher nur unter „Alle“ sichtbar.
  - Altdatei ohne `ivrv`: Wert „—“, eigener Verfügbarkeitstext, kein Browser-Fallback aus IV/VRP.
  - Fehlender aktueller Wert trotz genügend Historie: kein Rang und keine Listenteilnahme.
  - Leere IV/RV-Liste während des Aufbaus: expliziter Aufbauhinweis.
  - Offene Seite beim Session-Wechsel: Derzeit gibt es keinen automatischen Snapshot-Refresh. Den angezeigten Datenstand beibehalten und sichtbar machen. Bei späterem Refresh Snapshot, Ränge, Metadaten und Listen gemeinsam ersetzen; keine Mischung alter und neuer Sessions.
  - Fenster-, Kategorie- und Sprachwechsel müssen Listen und Tooltips neu rendern; der Rank/Percentile-Schalter darf die fest nach Percentile sortierten Listen nicht umstellen.

Die geplanten Tests sind sinnvoll. Ergänzen würde ich vor allem die drei P2-Gegenbeispiele, RV exakt 0,01, ungültige Zahlentypen, Listen-Gleichstände und einen zweiten Snapshot im selben DOM. Die Zahl „≥ 30 Mutationen“ allein ist kein Freigabekriterium; entscheidend ist, dass diese Vertragsverletzungen erkannt werden.

**FREIGABE (Plan): nein** — nach Schließung der drei P2-Punkte ist der Plan mit Variante **(a)** tragfähig.
