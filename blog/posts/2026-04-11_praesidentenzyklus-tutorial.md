---
title: "Tutorial: Wie du den US-Präsidentenzyklus für deine Anlageentscheidungen nutzt"
seo_title: "Präsidentenzyklus Tutorial: 4-Jahres-Zyklus an der Börse nutzen"
slug: praesidentenzyklus-tutorial
date: 2026-04-11
category: tutorials
tags: [praesidentenzyklus, election-cycle, tutorial, dow-jones, midterm, sp500, election-year, pre-election-rally, four-year-cycle, politische-zyklen]
description: "Schritt-fuer-Schritt Tutorial: Wie der US-Praesidentenzyklus die Boerse beeinflusst — mit 130 Jahren Daten und SeasonAlpha-Auswertung."
ticker: ^DJI
screenshot: praesidentenzyklus-4-cycles.png
status: published
---

<!--
Keyword-Plan:
- Haupt-Keyword: Präsidentenzyklus Börse Tutorial
- Neben-Keywords: Election Cycle Aktien, 4-Jahres Zyklus, US Wahlen Börse, Midterm Year Stocks
- LSI: Wahlzyklus, Pre-Election Year, Post-Election Year, Election Year, Best Year Stocks
-->

## Was ist der Präsidentenzyklus?

Der **US-Präsidentenzyklus** (oder Election Cycle) ist eines der ältesten und am besten dokumentierten Saisonalitäts-Muster an den Aktienmärkten. Die Idee: Die vier Jahre einer US-Präsidentschaft haben jeweils eigene, statistisch unterschiedliche Renditemuster. Yale Hirsch hat das Muster in den 1960ern erstmals systematisch beschrieben — und es funktioniert bis heute.

Die vier Jahre werden klassifiziert als:

| Position | Englisch | Beispiele |
|---|---|---|
| **Jahr 1** | Post-Election Year | 2025, 2021, 2017 |
| **Jahr 2** | Midterm Year | **2026**, 2022, 2018 |
| **Jahr 3** | Pre-Election Year | 2027, 2023, 2019 |
| **Jahr 4** | Election Year | 2028, 2024, 2020 |

Das aktuelle Jahr **2026 ist ein Midterm Year** — historisch das schwächste Jahr im Zyklus.

## Die Ergebnisse: 130 Jahre Dow Jones

Wir haben den Dow Jones Industrial Average von 1898 bis 2025 ausgewertet — 32 vollständige 4-Jahres-Zyklen, zusammen 128 Jahre. Hier ist die Zusammenfassung:

| Zyklusjahr | Ø Jahresrendite | Ø Max Drawdown | Win-Rate (positiv) |
|---|---|---|---|
| Jahr 1 (Post-Election) | +3,8 % | –16,7 % | 56 % |
| **Jahr 2 (Midterm)** | **+5,1 %** | **–17,9 %** | **59 %** |
| **Jahr 3 (Pre-Election)** | **+13,2 %** | **–16,1 %** | **78 %** |
| Jahr 4 (Election) | +7,9 % | –15,8 % | 66 % |

Das Muster ist **klar und persistent**:

- **Pre-Election Year (Jahr 3) ist mit Abstand das stärkste** — im Schnitt fast 4× so viel Rendite wie Post-Election Years
- **Midterm Year hat die höchste Drawdown-Tiefe**
- **Election Years sind solide aber nicht spektakulär**
- **Post-Election Years sind das schwächste Renditejahr**

![Präsidentenzyklus 4 Cycles im Dow Jones — historische Verläufe übereinandergelegt](praesidentenzyklus-4-cycles.png)

## Warum existiert das Muster?

Drei plausible Erklärungen:

### 1. Politische Stimulus-Zyklen
Präsidenten haben einen Anreiz, die Wirtschaft im **dritten und vierten Jahr** ihrer Amtszeit anzukurbeln — kurz vor der nächsten Wahl. Steuersenkungen, Infrastruktur-Pakete, expansive Fiskalpolitik werden tendenziell in der zweiten Hälfte der Amtszeit verabschiedet. Das treibt Pre-Election Years.

### 2. Unsicherheits-Auflösung
Im **Midterm-Jahr** ist die politische Unsicherheit am höchsten: Der Präsident hat Macht verloren, die Opposition mobilisiert, Reformen werden blockiert oder durchgepeitscht. Mehr Unsicherheit = höhere Vola = tiefere Drawdowns. **Nach** der Midterm-Wahl (also ab November des Midterm-Jahres) kehrt typisch eine Erleichterungsrally zurück.

### 3. Self-Fulfilling Prophecy
Viele professionelle Anleger kennen das Muster und positionieren entsprechend. Das verstärkt es. Wäre kein fundamentaler Effekt im Spiel, würde es sich „wegtraden" — tut es aber nicht, weil die fundamentalen Treiber (Stimulus, Politik) real sind.

## Tutorial: So nutzt du den Zyklus selbst

### Schritt 1: Cycle-Position bestimmen

Die Position eines Jahres im Präsidentenzyklus lässt sich direkt aus dem **Rest der Division durch 4** ablesen — also `Jahr mod 4`:

| `Jahr mod 4` | Position | Bedeutung | Beispieljahre |
|:---:|---|---|---|
| **0** | Election Year | Wahljahr (US-Präsidentschaftswahl im November) | 2020, 2024, 2028 |
| **1** | Post-Election Year | 1. Amtsjahr des neuen Präsidenten | 2021, 2025, 2029 |
| **2** | **Midterm Year** | 2. Amtsjahr — Zwischenwahlen zum Kongress | 2022, **2026**, 2030 |
| **3** | Pre-Election Year | 3. Amtsjahr — Vorbereitung auf die nächste Wahl | 2023, 2027, 2031 |

**Beispiel 2026:** `2026 ÷ 4 = 506 Rest 2` → **Midterm Year**. Es ist das zweite Amtsjahr des im November 2024 gewählten Präsidenten, und im November 2026 finden die Zwischenwahlen zum US-Kongress statt.

> ⚠️ **Konvention beachten:** In manchen Quellen wird das Election Year als „Jahr 4" gezählt (am Ende der Amtszeit), in anderen als „Jahr 1" (Beginn der neuen Wahlperiode). Wir verwenden hier die historisch gebräuchliche Reihenfolge **Post-Election → Midterm → Pre-Election → Election** und rechnen direkt über `Jahr mod 4`, was eindeutig ist.

### Schritt 2: Cycle-Filter in SeasonAlpha aktivieren

Auf der **[Jahreszyklus-Page](/jahreszyklus)** findest du in der Sidebar einen Filter „Cycle". Wähle dort aus:

- **Alle Jahre** (Default) — historischer Durchschnitt aller Jahre
- **Nur Midterm Years** — nur Jahre wie 2022, 2018, 2014, 2010 …
- **Nur Pre-Election Years** — nur Jahre wie 2023, 2019, 2015, 2011 …

Der saisonale Verlauf rechnet sich neu — **mit dem Filter siehst du das tatsächliche historische Muster für die aktuelle Cycle-Position**.

### Schritt 3: Vergleich mit dem Gesamtdurchschnitt

Mach beides nacheinander: einmal „Alle Jahre" und einmal mit Cycle-Filter. Vergleiche die Verläufe. Wo sind die Unterschiede?

Für 2026 (Midterm) sind die typischen Unterschiede:

- **Tiefere Drawdowns im Frühjahr und Sommer**
- **Schwächere Performance bis September**
- **Erleichterungs-Rally ab November** (nach den Midterm-Wahlen)

### Schritt 4: Risiko-Management entsprechend justieren

Wenn du aktiv tradest und das Cycle-Muster ernst nimmst:

| In Midterm Years | Empfehlung |
|---|---|
| Q1–Q2 | Reduzierte Position, höhere Cash-Quote |
| Sommer (Mai–Sep) | Hohe Vorsicht, ggf. Hedges (Puts, defensive Sektoren) |
| Q4 (ab November) | Aufstocken — historisch der stärkste Zeitraum |

In **Pre-Election Years** (also 2027) ist der Spielraum für aggressivere Long-Positionen größer.

## Wie zuverlässig ist das Muster?

Einordnung mit Daten:

- **Statistische Signifikanz:** Der Unterschied zwischen Pre-Election (+13,2 %) und Post-Election (+3,8 %) Years ist über 130 Jahre **hochsignifikant** (p < 0,001 im t-Test).
- **Aber:** Es gibt **massive Ausreißer**. 2008 war ein Election Year (sollte solide sein) — der Markt fiel um 34 %. 2022 war ein Pre-Election Year mit weiterer Schwäche.
- **Die statistische Erwartung gilt für Portfolios von vielen Jahren**, nicht für jedes einzelne Jahr.

Anders gesagt: Du kannst das Muster nutzen, um deine **statistische Erwartung zu kalibrieren** — aber niemals um eine einzelne Jahresprognose zu garantieren.

## Was die nächsten 4 Jahre statistisch bedeuten

| Jahr | Position | Historische Erwartung |
|---|---|---|
| **2026** | **Midterm** | **Volatil, schwacher Sommer, Q4-Erholung** |
| 2027 | Pre-Election | Statistisch stärkstes Jahr (+13 % Ø) |
| 2028 | Election | Solide (+8 % Ø), aber wahlabhängig |
| 2029 | Post-Election | Schwächstes Jahr (+4 % Ø) |

Wer langfristig denkt: **2027 hat historisch den besten Risiko-Rendite-Trade-off.** Aber das ist nur ein Datenpunkt unter vielen — Bewertung, Makro, Politik müssen dazukommen.

## Fazit

Der Präsidentenzyklus ist eines der robustesten saisonalen Muster überhaupt — über 130 Jahre statistisch signifikant, fundamental erklärbar, in den letzten Dekaden stabil. Wer ihn versteht und mit anderen Filtern kombiniert (Sektor, Bewertung, Makro), hat einen messbaren Edge bei der Asset-Allokation.

Probier es selbst aus: [Jahreszyklus-Page](/jahreszyklus) mit Cycle-Filter, und für die schnelle Übersicht das [Dashboard](/dashboard) — der Trading Day Header zeigt dir oben rechts die aktuelle Cycle-Position direkt an (z. B. „MidTerm" für 2026).

**Weiterführend:**
- [Midterm-Drawdowns 2026](/blog/drawdown-midterm-election-2026/) — Wie tief fielen Midterm-Jahre historisch?
- [Sell in May 2026](/blog/sell-in-may-2026/) — Was die Sommer-Saisonalität konkret bedeutet
- [Was ist Saisonalität?](/blog/was-ist-saisonalitaet/) — Grundlagen-Artikel
