# Methodik-Expander Template

> Vorlage für den Methodik-Expander auf jeder Analysis-Page.
> Referenz-Implementierung: `pages/01_Dekadenzyklus.py` (Zeile ~812)
>
> Jede Page bekommt einen eigenen Methodik-Expander am Ende (vor `render_footer()`),
> der alle Analyse-Methoden dieser Page verständlich erklärt.

## Struktur

Der Methodik-Expander hat immer diese Gliederung:

```
### Datengrundlage
- Ticker, Datenzeitraum, Datenquellen, Mindestlänge/Filter

### Rendite-Analyse
- Normierung (wie werden Renditen berechnet?)
- Gruppierung/Aggregation (wie werden Jahre/Perioden zusammengefasst?)
- Visualisierungen (was zeigt jeder Chart?)
- Interaktive Elemente (Sidebar-Filter, Overlays)

### Drawdown-Analyse (falls vorhanden)
- Definition (Formel verständlich erklärt)
- Ø Drawdown-Verlauf (was zeigt der Chart?)
- Aktuelles Jahr (Gold-Overlay)
- Worst-DD-Tabelle (Recovery-Erklärung)
- Heatmap (was bedeuten die Farben?)

### Volatilitäts-Analyse (falls vorhanden)
- Rolling Volatilität (Formel, Fenster, Annualisierung)
- Darstellung (Interpolation, Mittelung)
- Aktuelle Vola-KPIs (Perzentil, Status)

### Weitere Sektionen (page-spezifisch)
- z.B. Anomalie-Radar, Signifikanztest, Präsidentenzyklus
```

## Stil-Regeln

1. **Sprache:** Deutsch, klar und verständlich für ambitionierte Privatanleger
2. **Formeln:** Nur wenn nötig, immer mit Text-Erklärung daneben
3. **Stichpunkte:** Fettgedruckter Titel + Erklärung in einem Satz
4. **Beispiele:** Konkrete Zahlen wo möglich (z.B. "DJI 1929: 25 Jahre bis zur Erholung")
5. **Farbcodes:** Erklären was Grün/Rot/Gold bedeutet
6. **Dynamische Werte:** Ticker, Zeitraum, Kohorten-Info, Vola-Fenster per f-string einfügen
7. **Umfang:** Jede Sektion (Rendite, Drawdown, Vola) ca. 4-6 Bullet Points

## Referenz-Implementierung (Dekadenzyklus)

```python
with st.expander("ℹ️ Methodik"):
    st.markdown(f"""
### Datengrundlage

- **Ticker:** {ticker}
- **Datenzeitraum:** {data_start}–{data_end} ({total_years} vollständige Jahre)
- **Datenquellen:** Yahoo Finance (ab ~1992) + Stooq.com (historische Daten ab 1896 für ausgewählte Indizes)
- **Mindestlänge:** Jahre mit weniger als 200 Handelstagen werden ausgeschlossen

### Rendite-Analyse

- **Normierung:** Erster Handelstag jedes Jahres = 0% (logarithmische Returns)
- **Interpolation:** Jede Jahreskurve wird auf 252 Handelstage normiert (lineare Interpolation), damit Jahre mit unterschiedlicher Handelstag-Anzahl vergleichbar sind
- **Kohorten:** Alle Jahre werden nach ihrer letzten Ziffer gruppiert (x0 = 1900, 1910, …, 2020; x6 = 1896, 1906, …, 2026). Die Ø-Kurve ist der Mittelwert aller Jahre einer Kohorte.
- **Glättung:** 5-Tage zentrierter Moving Average auf der Ø-Kurve
- **Aktuelle Kohorte:** {CURRENT_YEAR} → X{CURRENT_DIGIT} (gelb markiert)
- **Monatsrendite-Heatmap:** Zeigt die durchschnittliche Monatsrendite pro Dekaden-Endziffer. Grün = positiv, Rot = negativ.
- **Box-Plot:** Verteilung der Jahresrenditen pro Kohorte. Kasten = mittlere 50% (25.–75. Perzentil), Linie = Median, Antennen = 1.5× Interquartilsabstand, Punkte = Ausreißer (Crash-/Boom-Jahre).

### Drawdown-Analyse

- **Definition:** Der Drawdown misst den prozentualen Rückgang vom bisherigen Jahreshoch. Formel: DD = (Kurs – Höchstkurs seit Jahresbeginn) / Höchstkurs × 100. Ein Drawdown von –20% bedeutet: Der Kurs liegt 20% unter dem bisherigen Jahreshoch.
- **Ø Drawdown-Verlauf:** Für jede Kohorte (Endziffer) wird der Drawdown pro Tag berechnet, dann über alle Jahre der Kohorte gemittelt. Das zeigt, wann im Jahr typischerweise die größten Rücksetzer auftreten.
- **Aktuelles Jahr (Gold):** Das laufende Jahr {CURRENT_YEAR} wird als goldene Linie eingezeichnet, um den aktuellen Drawdown mit dem historischen Durchschnitt zu vergleichen.
- **Worst-DD-Tabelle:** Zeigt die 25 schlimmsten Drawdown-Jahre mit Peak-Datum (Höchstkurs), Tief-Datum und Recovery. Die Recovery misst, wie viele Handelstage es dauerte, bis der Kurs den Peak-Preis wieder überschritten hat — auch über das Jahresende hinaus (z.B. DJI 1929: 25 Jahre bis zur Erholung).
- **Drawdown-Heatmap:** Durchschnittlicher maximaler Drawdown pro Monat und Dekade. Zeigt saisonal-zyklische Risikophasen.

### Volatilitäts-Analyse

- **Rolling Volatilität:** Annualisierte Standardabweichung der täglichen Log-Returns über ein rollendes Fenster (einstellbar: {vola_window} Tage in der Sidebar). Formel: σ_annualisiert = σ_täglich × √252 × 100.
- **Darstellung:** Pro Kohorte wird die Rolling-Vola für jedes Jahr berechnet, auf 252 Punkte interpoliert und dann über alle Jahre gemittelt. Das zeigt, wann im Jahr die Schwankungsbreite typischerweise am höchsten ist (z.B. Oktober = historisch volatilster Monat).
- **Kohorten-Filter:** Über die Sidebar können einzelne Dekaden-Kohorten ein-/ausgeblendet werden. Das gilt für alle Charts (Rendite, Drawdown und Volatilität).
- **Aktuelle Vola:** Die KPI-Karten vergleichen die aktuelle Rolling-Vola mit dem historischen Ø am gleichen Handelstag des Jahres. Perzentil zeigt: "In wie viel Prozent der vergangenen Jahre war die Vola niedriger als heute?"

### Anomalie-Radar

- **Methode:** Isolation Forest (Machine Learning) vergleicht die letzten 10 Handelstage mit allen historischen 10-Tages-Fenstern am gleichen Kalenderzeitpunkt.
- **Score:** 0–100 (0 = völlig normal, 100 = extrem ungewöhnlich). Ab 40 = leicht anomal, ab 70 = stark anomal.
    """)
```

## Anpassung für andere Pages

Beim Kopieren auf andere Pages:
- **Datengrundlage:** Ticker + Zeitraum per f-string (immer gleich)
- **Rendite-Analyse:** An die spezifischen Berechnungen der Page anpassen (z.B. Jahreszyklus: Kalendertage statt Handelstage, Monatszyklus: TDOM, Wochentage: Rendite-Modi)
- **Drawdown/Vola:** Nur einbauen wenn die Page diese Sektionen hat
- **Page-spezifische Sektionen:** z.B. Präsidentenzyklus (Jahreszyklus), Mondphasen (Lunar), Turn-of-Month (Monatswechsel), Signifikanztest
