# Plan v1 — Drawdown-Analyse QQQ (Vorlage für eine Unterseite „Drawdown-Analyse“ je Ticker)

Stand 2026-10-31, vor der Auswertung festgelegt. Auftrag des Nutzers: aktueller Drawdown im QQQ, wie lange er schon
dauert und ob das ungewöhnlich lang ist (Perzentil/Rang gegen die letzten 10, 15, 20 … Jahre), wie lange frühere
Drawdowns bis zur Erholung brauchten (Time to Recovery). Erst ein Exemplar als Artefakt, später eine Seite mit
Auswahl von Ticker und Perzentil.

## Datenstand (Abruf 2026-10-31)
QQQ aus Supabase `prices` (`date, close, log_return`), 1999-03-10 … 2026-10-30, 6 955 Zeilen; letzte abgeschlossene
Sitzung 2026-10-30 (`letzte_session('NYSE')`). Wird für das Artefakt eingefroren (SHA-256).
Renditebasis: gespeicherter `log_return` aus adjustierten Schlusskursen → Gesamtrendite-Näherung (Dividenden
enthalten, keine Kosten). Vorab gesehen (nur der aktuelle Rand): Hoch 2026-10-06, Schluss 2026-10-30 −9,11 %,
18 Sitzungen seit dem Hoch, der 30.10. ist zugleich das bisherige Tief.

## Definitionen
- Index `I_t = exp(Σ lr)`; laufendes Hoch `H_t = max_{s≤t} I_s`; Drawdown `D_t = I_t / H_t − 1` (Schlusskurse).
- **Episode:** beginnt am letzten Schluss mit `D = 0` (Hoch, Datum P), enthält alle folgenden Sitzungen mit `D < 0`,
  endet mit der ersten Sitzung `I ≥ H` (Erholung, Datum R). Tief T = Sitzung mit minimalem D in (P, R).
- Kennzahlen je Episode (Sitzungen und Kalendertage): **Tiefe** `min D`; **Dauer unter Wasser** P → R;
  **Zeit bis zum Tief** P → T; **Erholungszeit (Time to Recovery)** T → R. Laufende Episode: rechtszensiert
  (R unbekannt), Tiefe/Tief vorläufig.
- **Mindesttiefe:** Episoden mit Tiefe ≤ −5 %, ≤ −10 %, ≤ −20 % (kumulativ). Episoden flacher als −5 % sind
  Rauschen und werden nur gezählt.
- **Zeitfenster:** letzte 10 / 15 / 20 Jahre und gesamte Historie; eine Episode gehört zum Fenster, wenn ihr Hoch P
  im Fenster liegt (Fensterbeginn = letzte Sitzung − N Kalenderjahre).

## Fragen an die Daten (Kennzahlen des Artefakts)
1. **Ist die laufende Dauer ungewöhnlich lang?** Rang/Perzentil der bisherigen Dauer (18 Sitzungen) gegen die
   Dauer P → R abgeschlossener Episoden derselben Mindesttiefe je Fenster. Weil die laufende Episode zensiert ist,
   heißt die Kennzahl „Anteil früherer Episoden, die KÜRZER unter Wasser waren als die laufende bisher“ — keine
   Aussage über die Enddauer.
2. **Bedingte Restdauer:** unter den früheren Episoden, die mindestens so tief wie heute fielen (≤ −9,11 %), die
   Verteilung (Median, Quartile, Spanne) der gesamten Dauer P → R und der Erholungszeit T → R, jeweils mit n.
   Zusätzlich die Dauer ab dem ersten Erreichen der heutigen Tiefe bis R (das ist die Frage, die ein Anleger heute
   stellt).
3. **Tempo:** Sitzungen bis zum ersten Erreichen von −9,11 % — Rang der laufenden Episode (18) gegen frühere
   Episoden, die diese Tiefe erreichten.
4. **Tiefe:** Perzentil der heutigen Tiefe unter allen Sitzungen (Anteil der Tage mit `D ≤ −9,11 %`) je Fenster,
   und Rang unter den Episodentiefen.
5. **Tabelle** aller Episoden ≤ −10 % mit P, T, R, Tiefe, Dauer, Zeit bis Tief, Erholungszeit.

## Darstellung (Artefakt)
- Kopf: aktuelle Lage (Hoch, Tiefe, Sitzungen seit Hoch) + Perzentil-Kacheln je Fenster.
- Chart Unterwasserkurve (D_t) über die ganze Historie, Episoden ≤ −10 % markiert, laufende Episode hervorgehoben.
- Streudiagramm Tiefe × Dauer unter Wasser (alle Episoden ≤ −5 %), laufende Episode als Punkt mit „bisher“.
- „Überlebenskurve“: Anteil der Episoden (Tiefe ≤ −5 % bzw. ≥ heutige Tiefe), die nach k Sitzungen noch unter Wasser
  waren, mit der heutigen Position k = 18.
- Tabelle der großen Episoden.
- Steuerelemente als Vorschau der späteren Seite: Fenster (10/15/20/alle), Mindesttiefe (5/10/20 %).

## Fragen an den Reviewer
1. Trägt die Episodendefinition (Hoch-zu-Hoch auf Schlusskursen, Gesamtrendite-Näherung)? Kurs- statt
   Gesamtrendite würde die Erholungszeiten verlängern (Dividenden fehlen) — Kennzeichnung genügt?
2. Ist der Vergleich einer zensierten laufenden Dauer mit abgeschlossenen Dauern so korrekt formuliert, oder braucht
   es einen Überlebensschätzer (Kaplan-Meier mit der laufenden als zensierter Beobachtung)?
3. Fensterzuordnung über das Hoch P: führt das bei 10 Jahren zu Verzerrungen (lange Episoden, die vor dem Fenster
   begannen, fehlen; die 2000er-Episode dominiert „alle“)?
4. Ist „Restdauer ab heutiger Tiefe“ mit so wenigen Fällen aussagefähig, und wie muss sie formuliert sein?
5. Was fehlt, was ist zu stark? Welche Zusatzanalysen wären für die spätere Seite sinnvoll?
