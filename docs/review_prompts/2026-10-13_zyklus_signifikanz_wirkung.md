# Wirkungsbericht: Jahresende-Regel, Präsidentenzyklus-Signifikanz, Schaltjahr, Heatmap (2026-10-13)

Plan: [v3](2026-10-13_zyklus_signifikanz_plan_v3.md) (Codex-Freigabe Runde 3). Erstellt **vor dem Push** (Push = Deploy).

**Stand:** alter Code = `HEAD` `1e84da2` (auf dem Server im Container `/app`, md5 von `shared/calculations.py`
gegen `git show HEAD` geprüft), neuer Code = Arbeitsbaum. **Stichtag** 13.10.2026 (Jahr 2026, Monat 10) in beiden
Läufen. **Daten:** Blog — `download_data` auf dem Server (Datenstand 12./13.10.2026); Seite — Kurszeilen über die
öffentliche REST-Schnittstelle wie die Seite (SPY ab 1993, ^GDAXI ab 1959, ^DJI ab 1896, QQQ ab 1999, ^GSPC ab 1789,
letzter Kurs 12./13.10.2026). Filter wie die Seite (`minYear = 2026 − Fenster`), Ausreißerfilter aus.
Nichts wurde geschrieben; die Builder-Funktionen wurden direkt aufgerufen (kein `--build`).

## Blog (alle veröffentlichten Konfigurationen, DE+EN)

| Konfiguration | Artikel (DE/EN) | alt | neu |
|---|---|---|---|
| `monthly_heatmap` ^GSPC 10, ^DJI 10, XLK 10, XLE 10, ^GDAXI 38 | April S&P, Was ist Saisonalität, Willkommen, Sektor-ETF, Schlechtester DAX-Monat | **Renderfehler** `TypeError` (None-Zelle) → Platzhalter statt Chart, **in Produktion** | Chart; 2026 Okt–Dez leer, alle übrigen Zellen belegt |
| `monthly_cycle` GOOGL 15 | Google Juli | Dez +1,663 % (11 J.) | Dez +1,307 % (15 J., neu 2011/2017/2022/2023) |
| `monthly_cycle` TLT 20 | Sell in May / Bonds | Dez −0,493 % (15 J.) | Dez −0,244 % (20 J.) |
| `monthly_cycle` ^GDAXI 38 | Schlechtester DAX-Monat, H2 | Dez +3,288 % (**7 von 38** J.) | Dez +1,979 % (38 J.) |
| `monthly_cycle` ^GSPC 30 | H2, Zwischenwahljahr 2026 | Dez +1,063 % (23 J.) | Dez +0,845 % (30 J.) |

In den Monatsbalken ändert sich **nur der Dezember** (alle übrigen 11 Monate identisch). Ursache allein L2: die alte
Referenz war 365, also fielen Jahre mit letztem Handelstag am 29./30.12. (NYSE) bzw. 30.12. (XETRA) aus dem Dezember.
**Artikeltexte:** Der DAX-Artikel nennt „Dezember +2,2 %, 74 %“ (DE/EN) aus einer eigenen Rechnung, nicht aus dem
Chart — der alte Chart zeigte daneben +3,29 %, der neue +1,98 %. Kein Text zitiert einen Chartwert, der sich ändert;
keine Textänderung vorgeschlagen, `updated:` daher nicht gesetzt (Nutzerentscheidung).

## /jahreszyklus (Seite, DE+EN gleich)

**Präsidentenzyklus-Karten** (alt → neu):

| Ticker | 10 J. | 20 J. | 30 J. | max |
|---|---|---|---|---|
| SPY | „Sorry, zu wenig Daten!“ → 4 graue (3/2/2/3) | **nur Election Year** → 4 Karten je n=5 | 6/5/5/7 → 8/7/7/8 | 7/5/5/7 → 9/8/8/8 |
| ^GDAXI | Sorry → 4 grau | **Sorry** → je 5 | **Sorry** → 8/7/7/8 | **Sorry** → 17/16/17/17 |
| ^DJI | Sorry → 4 grau | nur Election → je 5 | 6/5/5/7 → 8/7/7/8 | 24/23/22/29 → 32/31/31/32 |
| QQQ | Sorry → 4 grau | nur Election → je 5 | **Midterm fehlt** → 7/6/7/7 | wie 30 |
| ^GSPC | Sorry → 4 grau | nur Election → je 5 | 6/5/5/7 → 8/7/7/8 | 25/24/22/29 → 32/31/31/32 |

Beispiel SPY 20 J. neu: Post-Election n=5 p=0,0005 Ø +24,19 %, Midterm n=5 p=0,6246 Ø +3,53 %, Pre-Election n=5
p=0,1171, Election n=5 p=0,5658. Beim DAX gab es den Zyklustest **in keinem Fenster** (XETRA endet immer am 30.12.).

**Dezember/Q4/Jahr** (`periodStats`): Fallzahl steigt überall auf alle abgeschlossenen Jahre, z. B. ^GDAXI 20 J.
Jahr 4 J. Ø −1,66 % → 20 J. Ø +8,94 %; Q4 4 J. Ø +0,56 % → 20 J. Ø +4,84 %. **Alle übrigen Monate und Q1–Q3:
unverändert** in allen 20 Kombinationen.

**Schaltjahr-Faltung** (getrennt zugeordnet): Jahresendwert ändert sich in Schaltjahren mit Handel am 31.12.
(SPY/^GSPC/^DJI/QQQ: 2020, 2024 …; ^GDAXI nur 1964/1968 — XETRA schließt am 31.12.). Heatmap Dez 2024 SPY
−2,11 → −2,46 %, Dez 2020 +3,18 → +3,70 %.

**Heatmap-Filter** (getrennt zugeordnet): einzige weitere Änderung ist die **laufende Oktoberzelle 2026**
(SPY +1,85 % → leer), weil nur beendete Monate erscheinen.

**Andere Seiten** (gemeinsames `significance.js`): Gruppen, die den Test erreichen und unter 5 liegen, erscheinen grau
statt unsichtbar (Overnight auch mit n=0). Lokale Vorfilter unverändert.

## Prüfungen

`verify_seasonal_twins.py` grün (neu Block 7, 30+ Fälle, Blog-Fall), `verify_twins_mutation.py` **32/32**,
`verify_seiten_kurse.py` 313 bestanden (Vorlagen nachgezogen), `verify_en` FAIL 0, `verify_i18n_cache_version` ok.

## Anhang A — /jahreszyklus vollständig (Codex Code-R1, P1)

Je Ticker und Fenster: Zyklusgruppen (Jahresrendite) und Dezember/Q4/Jahr, alt (`HEAD`) gegen neu, mit Fallzahl, Mittel,
Gewinnquote und den Jahren, die neu hinzukommen bzw. wegfallen. **Grund jeder Neuaufnahme:** letzter Kurstag 362–364
(29./30.12., XETRA 30.12.), den die alte Referenz 365 verwarf. **Grund jedes Wegfalls:** keiner kam vor (die alte Regel
nahm das laufende Jahr bereits nicht auf). Die Mittel der Alt-Spalte stammen aus dem alten Builder (ohne Tag-366-Faltung);
eine Abweichung bei unveränderter Jahresliste (z. B. SPY Election Year 10 J.: +18,76 → +18,80 %) ist die Schaltjahr-Faltung
(2020/2024), keine Aufnahmeänderung. Monate Jan–Nov und Q1–Q3 sind in allen 20 Kombinationen unverändert (Abschnitt oben).

### SPY · 10 J.

| Gruppe | alt | neu | nur neu (letzter Kurstag) | nur alt |
|---|---|---|---|---|
| Zyklus Post-Election | n=2, Ø +24.26 %, Win 100 % | n=3, Ø +23.10 %, Win 100 % | 2017 (Tag 363) | — |
| Zyklus Midterm | n=1, Ø -5.25 %, Win 0 % | n=2, Ø -11.95 %, Win 0 % | 2022 (Tag 364) | — |
| Zyklus Pre-Election | n=1, Ø +31.09 %, Win 100 % | n=2, Ø +28.90 %, Win 100 % | 2023 (Tag 363) | — |
| Zyklus Election Year | n=3, Ø +18.76 %, Win 100 % | n=3, Ø +18.80 %, Win 100 % | — | — |
| Dez | n=7, Ø +0.53 %, Win 71 % | n=10, Ø +0.36 %, Win 70 % | 2017 (Tag 363), 2022 (Tag 364), 2023 (Tag 363) | — |
| Q4 | n=7, Ø +3.84 %, Win 86 % | n=10, Ø +5.19 %, Win 90 % | 2017 (Tag 363), 2022 (Tag 364), 2023 (Tag 363) | — |
| Jahr | n=7, Ø +18.66 %, Win 86 % | n=10, Ø +15.96 %, Win 80 % | 2017 (Tag 363), 2022 (Tag 364), 2023 (Tag 363) | — |

Aufgenommene Jahre neu: Post-Election: 2017 2021 2025 · Midterm: 2018 2022 · Pre-Election: 2019 2023 · Election Year: 2016 2020 2024

### SPY · 20 J.

| Gruppe | alt | neu | nur neu (letzter Kurstag) | nur alt |
|---|---|---|---|---|
| Zyklus Post-Election | n=4, Ø +25.04 %, Win 100 % | n=5, Ø +24.19 %, Win 100 % | 2017 (Tag 363) | — |
| Zyklus Midterm | n=3, Ø +7.48 %, Win 67 % | n=5, Ø +3.53 %, Win 60 % | 2006 (Tag 363), 2022 (Tag 364) | — |
| Zyklus Pre-Election | n=3, Ø +12.57 %, Win 100 % | n=5, Ø +13.05 %, Win 100 % | 2011 (Tag 364), 2023 (Tag 363) | — |
| Zyklus Election Year | n=5, Ø +6.54 %, Win 80 % | n=5, Ø +6.87 %, Win 80 % | — | — |
| Dez | n=15, Ø +0.98 %, Win 73 % | n=20, Ø +0.96 %, Win 75 % | 2006 (Tag 363), 2011 (Tag 364), 2017 (Tag 363), 2022 (Tag 364), 2023 (Tag 363) | — |
| Q4 | n=15, Ø +2.68 %, Win 73 % | n=20, Ø +4.32 %, Win 80 % | 2006 (Tag 363), 2011 (Tag 364), 2017 (Tag 363), 2022 (Tag 364), 2023 (Tag 363) | — |
| Jahr | n=15, Ø +12.87 %, Win 87 % | n=20, Ø +11.91 %, Win 85 % | 2006 (Tag 363), 2011 (Tag 364), 2017 (Tag 363), 2022 (Tag 364), 2023 (Tag 363) | — |

Aufgenommene Jahre neu: Post-Election: 2009 2013 2017 2021 2025 · Midterm: 2006 2010 2014 2018 2022 · Pre-Election: 2007 2011 2015 2019 2023 · Election Year: 2008 2012 2016 2020 2024

### SPY · 30 J.

| Gruppe | alt | neu | nur neu (letzter Kurstag) | nur alt |
|---|---|---|---|---|
| Zyklus Post-Election | n=6, Ø +20.53 %, Win 83 % | n=8, Ø +18.66 %, Win 88 % | 2005 (Tag 364), 2017 (Tag 363) | — |
| Zyklus Midterm | n=5, Ø +5.61 %, Win 60 % | n=7, Ø +3.32 %, Win 57 % | 2006 (Tag 363), 2022 (Tag 364) | — |
| Zyklus Pre-Election | n=5, Ø +16.51 %, Win 100 % | n=7, Ø +15.73 %, Win 100 % | 2011 (Tag 364), 2023 (Tag 363) | — |
| Zyklus Election Year | n=7, Ø +9.59 %, Win 86 % | n=8, Ø +7.18 %, Win 75 % | 2000 (Tag 364) | — |
| Dez | n=23, Ø +1.11 %, Win 70 % | n=30, Ø +0.88 %, Win 67 % | 2000 (Tag 364), 2005 (Tag 364), 2006 (Tag 363), 2011 (Tag 364), 2017 (Tag 363), 2022 (Tag 364), 2023 (Tag 363) | — |
| Q4 | n=23, Ø +5.40 %, Win 83 % | n=30, Ø +5.39 %, Win 83 % | 2000 (Tag 364), 2005 (Tag 364), 2006 (Tag 363), 2011 (Tag 364), 2017 (Tag 363), 2022 (Tag 364), 2023 (Tag 363) | — |
| Jahr | n=23, Ø +13.08 %, Win 83 % | n=30, Ø +11.34 %, Win 80 % | 2000 (Tag 364), 2005 (Tag 364), 2006 (Tag 363), 2011 (Tag 364), 2017 (Tag 363), 2022 (Tag 364), 2023 (Tag 363) | — |

Aufgenommene Jahre neu: Post-Election: 1997 2001 2005 2009 2013 2017 2021 2025 · Midterm: 1998 2002 2006 2010 2014 2018 2022 · Pre-Election: 1999 2003 2007 2011 2015 2019 2023 · Election Year: 1996 2000 2004 2008 2012 2016 2020 2024

### SPY · max

| Gruppe | alt | neu | nur neu (letzter Kurstag) | nur alt |
|---|---|---|---|---|
| Zyklus Post-Election | n=7, Ø +18.84 %, Win 86 % | n=9, Ø +17.55 %, Win 89 % | 2005 (Tag 364), 2017 (Tag 363) | — |
| Zyklus Midterm | n=5, Ø +5.61 %, Win 60 % | n=8, Ø +2.99 %, Win 63 % | 1994 (Tag 364), 2006 (Tag 363), 2022 (Tag 364) | — |
| Zyklus Pre-Election | n=5, Ø +16.51 %, Win 100 % | n=8, Ø +18.44 %, Win 100 % | 1995 (Tag 363), 2011 (Tag 364), 2023 (Tag 363) | — |
| Zyklus Election Year | n=7, Ø +9.59 %, Win 86 % | n=8, Ø +7.18 %, Win 75 % | 2000 (Tag 364) | — |
| Dez | n=24, Ø +1.11 %, Win 71 % | n=33, Ø +0.93 %, Win 70 % | 1994 (Tag 364), 1995 (Tag 363), 2000 (Tag 364), 2005 (Tag 364), 2006 (Tag 363), 2011 (Tag 364), 2017 (Tag 363), 2022 (Tag 364), 2023 (Tag 363) | — |
| Q4 | n=24, Ø +5.25 %, Win 83 % | n=33, Ø +5.12 %, Win 82 % | 1994 (Tag 364), 1995 (Tag 363), 2000 (Tag 364), 2005 (Tag 364), 2006 (Tag 363), 2011 (Tag 364), 2017 (Tag 363), 2022 (Tag 364), 2023 (Tag 363) | — |
| Jahr | n=24, Ø +12.90 %, Win 83 % | n=33, Ø +11.72 %, Win 82 % | 1994 (Tag 364), 1995 (Tag 363), 2000 (Tag 364), 2005 (Tag 364), 2006 (Tag 363), 2011 (Tag 364), 2017 (Tag 363), 2022 (Tag 364), 2023 (Tag 363) | — |

Aufgenommene Jahre neu: Post-Election: 1993 1997 2001 2005 2009 2013 2017 2021 2025 · Midterm: 1994 1998 2002 2006 2010 2014 2018 2022 · Pre-Election: 1995 1999 2003 2007 2011 2015 2019 2023 · Election Year: 1996 2000 2004 2008 2012 2016 2020 2024

### ^GDAXI · 10 J.

| Gruppe | alt | neu | nur neu (letzter Kurstag) | nur alt |
|---|---|---|---|---|
| Zyklus Post-Election | n=0 | n=3, Ø +16.47 %, Win 100 % | 2017 (Tag 363), 2021 (Tag 364), 2025 (Tag 364) | — |
| Zyklus Midterm | n=0 | n=2, Ø -15.53 %, Win 0 % | 2018 (Tag 362), 2022 (Tag 364) | — |
| Zyklus Pre-Election | n=0 | n=2, Ø +22.15 %, Win 100 % | 2019 (Tag 364), 2023 (Tag 363) | — |
| Zyklus Election Year | n=3, Ø +10.95 %, Win 100 % | n=3, Ø +10.95 %, Win 100 % | — | — |
| Dez | n=3, Ø +4.01 %, Win 100 % | n=10, Ø +1.19 %, Win 80 % | 2017 (Tag 363), 2018 (Tag 362), 2019 (Tag 364), 2021 (Tag 364), 2022 (Tag 364), 2023 (Tag 363), 2025 (Tag 364) | — |
| Q4 | n=3, Ø +6.59 %, Win 100 % | n=10, Ø +4.42 %, Win 90 % | 2017 (Tag 363), 2018 (Tag 362), 2019 (Tag 364), 2021 (Tag 364), 2022 (Tag 364), 2023 (Tag 363), 2025 (Tag 364) | — |
| Jahr | n=3, Ø +10.95 %, Win 100 % | n=10, Ø +9.55 %, Win 80 % | 2017 (Tag 363), 2018 (Tag 362), 2019 (Tag 364), 2021 (Tag 364), 2022 (Tag 364), 2023 (Tag 363), 2025 (Tag 364) | — |

Aufgenommene Jahre neu: Post-Election: 2017 2021 2025 · Midterm: 2018 2022 · Pre-Election: 2019 2023 · Election Year: 2016 2020 2024

### ^GDAXI · 20 J.

| Gruppe | alt | neu | nur neu (letzter Kurstag) | nur alt |
|---|---|---|---|---|
| Zyklus Post-Election | n=0 | n=5, Ø +18.40 %, Win 100 % | 2009 (Tag 364), 2013 (Tag 364), 2017 (Tag 363), 2021 (Tag 364), 2025 (Tag 364) | — |
| Zyklus Midterm | n=0 | n=5, Ø +1.72 %, Win 60 % | 2006 (Tag 363), 2010 (Tag 364), 2014 (Tag 364), 2018 (Tag 362), 2022 (Tag 364) | — |
| Zyklus Pre-Election | n=0 | n=5, Ø +11.89 %, Win 80 % | 2007 (Tag 362), 2011 (Tag 364), 2015 (Tag 364), 2019 (Tag 364), 2023 (Tag 363) | — |
| Zyklus Election Year | n=4, Ø -1.66 %, Win 75 % | n=5, Ø +3.73 %, Win 80 % | 2012 (Tag 363) | — |
| Dez | n=4, Ø +4.81 %, Win 100 % | n=20, Ø +1.36 %, Win 75 % | 2006 (Tag 363), 2007 (Tag 362), 2009 (Tag 364), 2010 (Tag 364), 2011 (Tag 364), 2012 (Tag 363), 2013 (Tag 364), 2014 (Tag 364), 2015 (Tag 364), 2017 (Tag 363), 2018 (Tag 362), 2019 (Tag 364), 2021 (Tag 364), 2022 (Tag 364), 2023 (Tag 363), 2025 (Tag 364) | — |
| Q4 | n=4, Ø +0.56 %, Win 75 % | n=20, Ø +4.84 %, Win 90 % | 2006 (Tag 363), 2007 (Tag 362), 2009 (Tag 364), 2010 (Tag 364), 2011 (Tag 364), 2012 (Tag 363), 2013 (Tag 364), 2014 (Tag 364), 2015 (Tag 364), 2017 (Tag 363), 2018 (Tag 362), 2019 (Tag 364), 2021 (Tag 364), 2022 (Tag 364), 2023 (Tag 363), 2025 (Tag 364) | — |
| Jahr | n=4, Ø -1.66 %, Win 75 % | n=20, Ø +8.94 %, Win 80 % | 2006 (Tag 363), 2007 (Tag 362), 2009 (Tag 364), 2010 (Tag 364), 2011 (Tag 364), 2012 (Tag 363), 2013 (Tag 364), 2014 (Tag 364), 2015 (Tag 364), 2017 (Tag 363), 2018 (Tag 362), 2019 (Tag 364), 2021 (Tag 364), 2022 (Tag 364), 2023 (Tag 363), 2025 (Tag 364) | — |

Aufgenommene Jahre neu: Post-Election: 2009 2013 2017 2021 2025 · Midterm: 2006 2010 2014 2018 2022 · Pre-Election: 2007 2011 2015 2019 2023 · Election Year: 2008 2012 2016 2020 2024

### ^GDAXI · 30 J.

| Gruppe | alt | neu | nur neu (letzter Kurstag) | nur alt |
|---|---|---|---|---|
| Zyklus Post-Election | n=0 | n=8, Ø +18.73 %, Win 88 % | 1997 (Tag 364), 2001 (Tag 362), 2005 (Tag 364), 2009 (Tag 364), 2013 (Tag 364), 2017 (Tag 363), 2021 (Tag 364), 2025 (Tag 364) | — |
| Zyklus Midterm | n=0 | n=7, Ø -2.96 %, Win 57 % | 1998 (Tag 364), 2002 (Tag 364), 2006 (Tag 363), 2010 (Tag 364), 2014 (Tag 364), 2018 (Tag 362), 2022 (Tag 364) | — |
| Zyklus Pre-Election | n=0 | n=7, Ø +16.95 %, Win 86 % | 1999 (Tag 364), 2003 (Tag 364), 2007 (Tag 362), 2011 (Tag 364), 2015 (Tag 364), 2019 (Tag 364), 2023 (Tag 363) | — |
| Zyklus Election Year | n=6, Ø +4.01 %, Win 83 % | n=8, Ø +5.59 %, Win 75 % | 2000 (Tag 364), 2012 (Tag 363) | — |
| Dez | n=6, Ø +3.91 %, Win 100 % | n=30, Ø +1.76 %, Win 80 % | 1997 (Tag 364), 1998 (Tag 364), 1999 (Tag 364), 2000 (Tag 364), 2001 (Tag 362), 2002 (Tag 364), 2003 (Tag 364), 2005 (Tag 364), 2006 (Tag 363), 2007 (Tag 362), 2009 (Tag 364), 2010 (Tag 364), 2011 (Tag 364), 2012 (Tag 363), 2013 (Tag 364), 2014 (Tag 364), 2015 (Tag 364), 2017 (Tag 363), 2018 (Tag 362), 2019 (Tag 364), 2021 (Tag 364), 2022 (Tag 364), 2023 (Tag 363), 2025 (Tag 364) | — |
| Q4 | n=6, Ø +3.34 %, Win 83 % | n=30, Ø +7.16 %, Win 87 % | 1997 (Tag 364), 1998 (Tag 364), 1999 (Tag 364), 2000 (Tag 364), 2001 (Tag 362), 2002 (Tag 364), 2003 (Tag 364), 2005 (Tag 364), 2006 (Tag 363), 2007 (Tag 362), 2009 (Tag 364), 2010 (Tag 364), 2011 (Tag 364), 2012 (Tag 363), 2013 (Tag 364), 2014 (Tag 364), 2015 (Tag 364), 2017 (Tag 363), 2018 (Tag 362), 2019 (Tag 364), 2021 (Tag 364), 2022 (Tag 364), 2023 (Tag 363), 2025 (Tag 364) | — |
| Jahr | n=6, Ø +4.01 %, Win 83 % | n=30, Ø +9.75 %, Win 77 % | 1997 (Tag 364), 1998 (Tag 364), 1999 (Tag 364), 2000 (Tag 364), 2001 (Tag 362), 2002 (Tag 364), 2003 (Tag 364), 2005 (Tag 364), 2006 (Tag 363), 2007 (Tag 362), 2009 (Tag 364), 2010 (Tag 364), 2011 (Tag 364), 2012 (Tag 363), 2013 (Tag 364), 2014 (Tag 364), 2015 (Tag 364), 2017 (Tag 363), 2018 (Tag 362), 2019 (Tag 364), 2021 (Tag 364), 2022 (Tag 364), 2023 (Tag 363), 2025 (Tag 364) | — |

Aufgenommene Jahre neu: Post-Election: 1997 2001 2005 2009 2013 2017 2021 2025 · Midterm: 1998 2002 2006 2010 2014 2018 2022 · Pre-Election: 1999 2003 2007 2011 2015 2019 2023 · Election Year: 1996 2000 2004 2008 2012 2016 2020 2024

### ^GDAXI · max

| Gruppe | alt | neu | nur neu (letzter Kurstag) | nur alt |
|---|---|---|---|---|
| Zyklus Post-Election | n=3, Ø -9.60 %, Win 33 % | n=17, Ø +15.60 %, Win 76 % | 1961 (Tag 363), 1977 (Tag 363), 1981 (Tag 364), 1985 (Tag 364), 1989 (Tag 363), 1993 (Tag 364), 1997 (Tag 364), 2001 (Tag 362), 2005 (Tag 364), 2009 (Tag 364), 2013 (Tag 364), 2017 (Tag 363), 2021 (Tag 364), 2025 (Tag 364) | — |
| Zyklus Midterm | n=2, Ø -25.67 %, Win 0 % | n=16, Ø -6.18 %, Win 50 % | 1966 (Tag 364), 1974 (Tag 364), 1978 (Tag 362), 1982 (Tag 364), 1986 (Tag 364), 1990 (Tag 362), 1994 (Tag 364), 1998 (Tag 364), 2002 (Tag 364), 2006 (Tag 363), 2010 (Tag 364), 2014 (Tag 364), 2018 (Tag 362), 2022 (Tag 364) | — |
| Zyklus Pre-Election | n=3, Ø +11.13 %, Win 100 % | n=17, Ø +15.14 %, Win 82 % | 1967 (Tag 363), 1975 (Tag 364), 1979 (Tag 362), 1983 (Tag 363), 1987 (Tag 364), 1991 (Tag 364), 1995 (Tag 363), 1999 (Tag 364), 2003 (Tag 364), 2007 (Tag 362), 2011 (Tag 364), 2015 (Tag 364), 2019 (Tag 364), 2023 (Tag 363) | — |
| Zyklus Election Year | n=11, Ø +2.10 %, Win 64 % | n=17, Ø +7.39 %, Win 71 % | 1960 (Tag 364), 1972 (Tag 364), 1984 (Tag 363), 1988 (Tag 364), 2000 (Tag 364), 2012 (Tag 363) | — |
| Dez | n=19, Ø +1.08 %, Win 58 % | n=67, Ø +1.08 %, Win 58 % | 1960 (Tag 364), 1961 (Tag 363), 1966 (Tag 364), 1967 (Tag 363), 1972 (Tag 364), 1974 (Tag 364), 1975 (Tag 364), 1977 (Tag 363), 1978 (Tag 362), 1979 (Tag 362), 1981 (Tag 364), 1982 (Tag 364), 1983 (Tag 363), 1984 (Tag 363), 1985 (Tag 364), 1986 (Tag 364), 1987 (Tag 364), 1988 (Tag 364), 1989 (Tag 363), 1990 (Tag 362), 1991 (Tag 364), 1993 (Tag 364), 1994 (Tag 364), 1995 (Tag 363), 1997 (Tag 364), 1998 (Tag 364), 1999 (Tag 364), 2000 (Tag 364), 2001 (Tag 362), 2002 (Tag 364), 2003 (Tag 364), 2005 (Tag 364), 2006 (Tag 363), 2007 (Tag 362), 2009 (Tag 364), 2010 (Tag 364), 2011 (Tag 364), 2012 (Tag 363), 2013 (Tag 364), 2014 (Tag 364), 2015 (Tag 364), 2017 (Tag 363), 2018 (Tag 362), 2019 (Tag 364), 2021 (Tag 364), 2022 (Tag 364), 2023 (Tag 363), 2025 (Tag 364) | — |
| Q4 | n=19, Ø +0.26 %, Win 47 % | n=67, Ø +3.73 %, Win 66 % | 1960 (Tag 364), 1961 (Tag 363), 1966 (Tag 364), 1967 (Tag 363), 1972 (Tag 364), 1974 (Tag 364), 1975 (Tag 364), 1977 (Tag 363), 1978 (Tag 362), 1979 (Tag 362), 1981 (Tag 364), 1982 (Tag 364), 1983 (Tag 363), 1984 (Tag 363), 1985 (Tag 364), 1986 (Tag 364), 1987 (Tag 364), 1988 (Tag 364), 1989 (Tag 363), 1990 (Tag 362), 1991 (Tag 364), 1993 (Tag 364), 1994 (Tag 364), 1995 (Tag 363), 1997 (Tag 364), 1998 (Tag 364), 1999 (Tag 364), 2000 (Tag 364), 2001 (Tag 362), 2002 (Tag 364), 2003 (Tag 364), 2005 (Tag 364), 2006 (Tag 363), 2007 (Tag 362), 2009 (Tag 364), 2010 (Tag 364), 2011 (Tag 364), 2012 (Tag 363), 2013 (Tag 364), 2014 (Tag 364), 2015 (Tag 364), 2017 (Tag 363), 2018 (Tag 362), 2019 (Tag 364), 2021 (Tag 364), 2022 (Tag 364), 2023 (Tag 363), 2025 (Tag 364) | — |
| Jahr | n=19, Ø -1.25 %, Win 58 % | n=67, Ø +8.20 %, Win 70 % | 1960 (Tag 364), 1961 (Tag 363), 1966 (Tag 364), 1967 (Tag 363), 1972 (Tag 364), 1974 (Tag 364), 1975 (Tag 364), 1977 (Tag 363), 1978 (Tag 362), 1979 (Tag 362), 1981 (Tag 364), 1982 (Tag 364), 1983 (Tag 363), 1984 (Tag 363), 1985 (Tag 364), 1986 (Tag 364), 1987 (Tag 364), 1988 (Tag 364), 1989 (Tag 363), 1990 (Tag 362), 1991 (Tag 364), 1993 (Tag 364), 1994 (Tag 364), 1995 (Tag 363), 1997 (Tag 364), 1998 (Tag 364), 1999 (Tag 364), 2000 (Tag 364), 2001 (Tag 362), 2002 (Tag 364), 2003 (Tag 364), 2005 (Tag 364), 2006 (Tag 363), 2007 (Tag 362), 2009 (Tag 364), 2010 (Tag 364), 2011 (Tag 364), 2012 (Tag 363), 2013 (Tag 364), 2014 (Tag 364), 2015 (Tag 364), 2017 (Tag 363), 2018 (Tag 362), 2019 (Tag 364), 2021 (Tag 364), 2022 (Tag 364), 2023 (Tag 363), 2025 (Tag 364) | — |

Aufgenommene Jahre neu: Post-Election: 1961 1965 1969 1973 1977 1981 1985 1989 1993 1997 2001 2005 2009 2013 2017 2021 2025 · Midterm: 1962 1966 1970 1974 1978 1982 1986 1990 1994 1998 2002 2006 2010 2014 2018 2022 · Pre-Election: 1959 1963 1967 1971 1975 1979 1983 1987 1991 1995 1999 2003 2007 2011 2015 2019 2023 · Election Year: 1960 1964 1968 1972 1976 1980 1984 1988 1992 1996 2000 2004 2008 2012 2016 2020 2024

### ^DJI · 10 J.

| Gruppe | alt | neu | nur neu (letzter Kurstag) | nur alt |
|---|---|---|---|---|
| Zyklus Post-Election | n=2, Ø +16.80 %, Win 100 % | n=3, Ø +19.31 %, Win 100 % | 2017 (Tag 363) | — |
| Zyklus Midterm | n=1, Ø -6.03 %, Win 0 % | n=2, Ø -7.71 %, Win 0 % | 2022 (Tag 364) | — |
| Zyklus Pre-Election | n=1, Ø +22.24 %, Win 100 % | n=2, Ø +17.99 %, Win 100 % | 2023 (Tag 363) | — |
| Zyklus Election Year | n=3, Ø +11.15 %, Win 100 % | n=3, Ø +11.35 %, Win 100 % | — | — |
| Dez | n=7, Ø +0.38 %, Win 71 % | n=10, Ø +0.56 %, Win 70 % | 2017 (Tag 363), 2022 (Tag 364), 2023 (Tag 363) | — |
| Q4 | n=7, Ø +3.18 %, Win 86 % | n=10, Ø +5.98 %, Win 90 % | 2017 (Tag 363), 2022 (Tag 364), 2023 (Tag 363) | — |
| Jahr | n=7, Ø +11.90 %, Win 86 % | n=10, Ø +11.26 %, Win 80 % | 2017 (Tag 363), 2022 (Tag 364), 2023 (Tag 363) | — |

Aufgenommene Jahre neu: Post-Election: 2017 2021 2025 · Midterm: 2018 2022 · Pre-Election: 2019 2023 · Election Year: 2016 2020 2024

### ^DJI · 20 J.

| Gruppe | alt | neu | nur neu (letzter Kurstag) | nur alt |
|---|---|---|---|---|
| Zyklus Post-Election | n=4, Ø +18.16 %, Win 100 % | n=5, Ø +19.39 %, Win 100 % | 2017 (Tag 363) | — |
| Zyklus Midterm | n=3, Ø +3.92 %, Win 67 % | n=5, Ø +3.45 %, Win 60 % | 2006 (Tag 363), 2022 (Tag 364) | — |
| Zyklus Pre-Election | n=3, Ø +8.76 %, Win 67 % | n=5, Ø +8.94 %, Win 80 % | 2011 (Tag 364), 2023 (Tag 363) | — |
| Zyklus Election Year | n=5, Ø +1.03 %, Win 80 % | n=5, Ø +1.41 %, Win 80 % | — | — |
| Dez | n=15, Ø +0.61 %, Win 67 % | n=20, Ø +0.89 %, Win 70 % | 2006 (Tag 363), 2011 (Tag 364), 2017 (Tag 363), 2022 (Tag 364), 2023 (Tag 363) | — |
| Q4 | n=15, Ø +2.12 %, Win 73 % | n=20, Ø +4.52 %, Win 80 % | 2006 (Tag 363), 2011 (Tag 364), 2017 (Tag 363), 2022 (Tag 364), 2023 (Tag 363) | — |
| Jahr | n=15, Ø +7.72 %, Win 80 % | n=20, Ø +8.30 %, Win 80 % | 2006 (Tag 363), 2011 (Tag 364), 2017 (Tag 363), 2022 (Tag 364), 2023 (Tag 363) | — |

Aufgenommene Jahre neu: Post-Election: 2009 2013 2017 2021 2025 · Midterm: 2006 2010 2014 2018 2022 · Pre-Election: 2007 2011 2015 2019 2023 · Election Year: 2008 2012 2016 2020 2024

### ^DJI · 30 J.

| Gruppe | alt | neu | nur neu (letzter Kurstag) | nur alt |
|---|---|---|---|---|
| Zyklus Post-Election | n=6, Ø +14.92 %, Win 83 % | n=8, Ø +14.22 %, Win 75 % | 2005 (Tag 364), 2017 (Tag 363) | — |
| Zyklus Midterm | n=5, Ø +1.97 %, Win 60 % | n=7, Ø +2.19 %, Win 57 % | 2006 (Tag 363), 2022 (Tag 364) | — |
| Zyklus Pre-Election | n=5, Ø +14.58 %, Win 80 % | n=7, Ø +13.05 %, Win 86 % | 2011 (Tag 364), 2023 (Tag 363) | — |
| Zyklus Election Year | n=7, Ø +5.06 %, Win 86 % | n=8, Ø +3.77 %, Win 75 % | 2000 (Tag 364) | — |
| Dez | n=23, Ø +0.81 %, Win 70 % | n=30, Ø +0.91 %, Win 67 % | 2000 (Tag 364), 2005 (Tag 364), 2006 (Tag 363), 2011 (Tag 364), 2017 (Tag 363), 2022 (Tag 364), 2023 (Tag 363) | — |
| Q4 | n=23, Ø +4.79 %, Win 78 % | n=30, Ø +5.65 %, Win 83 % | 2000 (Tag 364), 2005 (Tag 364), 2006 (Tag 363), 2011 (Tag 364), 2017 (Tag 363), 2022 (Tag 364), 2023 (Tag 363) | — |
| Jahr | n=23, Ø +9.03 %, Win 78 % | n=30, Ø +8.35 %, Win 73 % | 2000 (Tag 364), 2005 (Tag 364), 2006 (Tag 363), 2011 (Tag 364), 2017 (Tag 363), 2022 (Tag 364), 2023 (Tag 363) | — |

Aufgenommene Jahre neu: Post-Election: 1997 2001 2005 2009 2013 2017 2021 2025 · Midterm: 1998 2002 2006 2010 2014 2018 2022 · Pre-Election: 1999 2003 2007 2011 2015 2019 2023 · Election Year: 1996 2000 2004 2008 2012 2016 2020 2024

### ^DJI · max

| Gruppe | alt | neu | nur neu (letzter Kurstag) | nur alt |
|---|---|---|---|---|
| Zyklus Post-Election | n=24, Ø +2.59 %, Win 50 % | n=32, Ø +7.33 %, Win 56 % | 1905 (Tag 363), 1921 (Tag 364), 1933 (Tag 364), 1961 (Tag 363), 1977 (Tag 364), 1989 (Tag 363), 2005 (Tag 364), 2017 (Tag 363) | — |
| Zyklus Midterm | n=23, Ø +3.74 %, Win 52 % | n=31, Ø +3.18 %, Win 52 % | 1910 (Tag 364), 1922 (Tag 363), 1950 (Tag 364), 1966 (Tag 364), 1978 (Tag 363), 1994 (Tag 364), 2006 (Tag 363), 2022 (Tag 364) | — |
| Zyklus Pre-Election | n=22, Ø +10.44 %, Win 77 % | n=31, Ø +11.77 %, Win 77 % | 1911 (Tag 363), 1927 (Tag 364), 1939 (Tag 364), 1955 (Tag 364), 1967 (Tag 363), 1983 (Tag 364), 1995 (Tag 363), 2011 (Tag 364), 2023 (Tag 363) | — |
| Zyklus Election Year | n=29, Ø +8.09 %, Win 76 % | n=32, Ø +7.69 %, Win 72 % | 1916 (Tag 364), 1972 (Tag 364), 2000 (Tag 364) | — |
| Dez | n=98, Ø +1.34 %, Win 69 % | n=126, Ø +1.32 %, Win 69 % | 1905 (Tag 363), 1910 (Tag 364), 1911 (Tag 363), 1916 (Tag 364), 1921 (Tag 364), 1922 (Tag 363), 1927 (Tag 364), 1933 (Tag 364), 1939 (Tag 364), 1950 (Tag 364), 1955 (Tag 364), 1961 (Tag 363), 1966 (Tag 364), 1967 (Tag 363), 1972 (Tag 364), 1977 (Tag 364), 1978 (Tag 363), 1983 (Tag 364), 1989 (Tag 363), 1994 (Tag 364), 1995 (Tag 363), 2000 (Tag 364), 2005 (Tag 364), 2006 (Tag 363), 2011 (Tag 364), 2017 (Tag 363), 2022 (Tag 364), 2023 (Tag 363) | — |
| Q4 | n=98, Ø +2.39 %, Win 65 % | n=126, Ø +2.86 %, Win 68 % | 1905 (Tag 363), 1910 (Tag 364), 1911 (Tag 363), 1916 (Tag 364), 1921 (Tag 364), 1922 (Tag 363), 1927 (Tag 364), 1933 (Tag 364), 1939 (Tag 364), 1950 (Tag 364), 1955 (Tag 364), 1961 (Tag 363), 1966 (Tag 364), 1967 (Tag 363), 1972 (Tag 364), 1977 (Tag 364), 1978 (Tag 363), 1983 (Tag 364), 1989 (Tag 363), 1994 (Tag 364), 1995 (Tag 363), 2000 (Tag 364), 2005 (Tag 364), 2006 (Tag 363), 2011 (Tag 364), 2017 (Tag 363), 2022 (Tag 364), 2023 (Tag 363) | — |
| Jahr | n=98, Ø +6.25 %, Win 64 % | n=126, Ø +7.50 %, Win 64 % | 1905 (Tag 363), 1910 (Tag 364), 1911 (Tag 363), 1916 (Tag 364), 1921 (Tag 364), 1922 (Tag 363), 1927 (Tag 364), 1933 (Tag 364), 1939 (Tag 364), 1950 (Tag 364), 1955 (Tag 364), 1961 (Tag 363), 1966 (Tag 364), 1967 (Tag 363), 1972 (Tag 364), 1977 (Tag 364), 1978 (Tag 363), 1983 (Tag 364), 1989 (Tag 363), 1994 (Tag 364), 1995 (Tag 363), 2000 (Tag 364), 2005 (Tag 364), 2006 (Tag 363), 2011 (Tag 364), 2017 (Tag 363), 2022 (Tag 364), 2023 (Tag 363) | — |

Aufgenommene Jahre neu: Post-Election: 1901 1905 1909 1913 1917 1921 1925 1929 1933 1937 1941 1945 1949 1953 1957 1961 1965 1969 1973 1977 1981 1985 1989 1993 1997 2001 2005 2009 2013 2017 2021 2025 · Midterm: 1902 1906 1910 1914 1918 1922 1926 1930 1934 1938 1942 1946 1950 1954 1958 1962 1966 1970 1974 1978 1982 1986 1990 1994 1998 2002 2006 2010 2014 2018 2022 · Pre-Election: 1903 1907 1911 1915 1919 1923 1927 1931 1935 1939 1943 1947 1951 1955 1959 1963 1967 1971 1975 1979 1983 1987 1991 1995 1999 2003 2007 2011 2015 2019 2023 · Election Year: 1900 1904 1908 1912 1916 1920 1924 1928 1932 1936 1940 1944 1948 1952 1956 1960 1964 1968 1972 1976 1980 1984 1988 1992 1996 2000 2004 2008 2012 2016 2020 2024

### QQQ · 10 J.

| Gruppe | alt | neu | nur neu (letzter Kurstag) | nur alt |
|---|---|---|---|---|
| Zyklus Post-Election | n=2, Ø +25.13 %, Win 100 % | n=3, Ø +27.25 %, Win 100 % | 2017 (Tag 363) | — |
| Zyklus Midterm | n=1, Ø -1.85 %, Win 0 % | n=2, Ø -17.53 %, Win 0 % | 2022 (Tag 364) | — |
| Zyklus Pre-Election | n=1, Ø +38.41 %, Win 100 % | n=2, Ø +47.16 %, Win 100 % | 2023 (Tag 363) | — |
| Zyklus Election Year | n=3, Ø +27.95 %, Win 100 % | n=3, Ø +27.70 %, Win 100 % | — | — |
| Dez | n=7, Ø +0.67 %, Win 71 % | n=10, Ø +0.13 %, Win 70 % | 2017 (Tag 363), 2022 (Tag 364), 2023 (Tag 363) | — |
| Q4 | n=7, Ø +4.03 %, Win 86 % | n=10, Ø +4.79 %, Win 80 % | 2017 (Tag 363), 2022 (Tag 364), 2023 (Tag 363) | — |
| Jahr | n=7, Ø +24.38 %, Win 86 % | n=10, Ø +22.41 %, Win 80 % | 2017 (Tag 363), 2022 (Tag 364), 2023 (Tag 363) | — |

Aufgenommene Jahre neu: Post-Election: 2017 2021 2025 · Midterm: 2018 2022 · Pre-Election: 2019 2023 · Election Year: 2016 2020 2024

### QQQ · 20 J.

| Gruppe | alt | neu | nur neu (letzter Kurstag) | nur alt |
|---|---|---|---|---|
| Zyklus Post-Election | n=4, Ø +32.73 %, Win 100 % | n=5, Ø +32.48 %, Win 100 % | 2017 (Tag 363) | — |
| Zyklus Midterm | n=3, Ø +12.23 %, Win 67 % | n=5, Ø +1.66 %, Win 60 % | 2006 (Tag 363), 2022 (Tag 364) | — |
| Zyklus Pre-Election | n=3, Ø +22.33 %, Win 100 % | n=5, Ø +24.95 %, Win 100 % | 2011 (Tag 364), 2023 (Tag 363) | — |
| Zyklus Election Year | n=5, Ø +11.53 %, Win 80 % | n=5, Ø +11.64 %, Win 80 % | — | — |
| Dez | n=15, Ø +1.11 %, Win 67 % | n=20, Ø +0.63 %, Win 60 % | 2006 (Tag 363), 2011 (Tag 364), 2017 (Tag 363), 2022 (Tag 364), 2023 (Tag 363) | — |
| Q4 | n=15, Ø +3.19 %, Win 73 % | n=20, Ø +4.19 %, Win 75 % | 2006 (Tag 363), 2011 (Tag 364), 2017 (Tag 363), 2022 (Tag 364), 2023 (Tag 363) | — |
| Jahr | n=15, Ø +19.48 %, Win 87 % | n=20, Ø +17.68 %, Win 85 % | 2006 (Tag 363), 2011 (Tag 364), 2017 (Tag 363), 2022 (Tag 364), 2023 (Tag 363) | — |

Aufgenommene Jahre neu: Post-Election: 2009 2013 2017 2021 2025 · Midterm: 2006 2010 2014 2018 2022 · Pre-Election: 2007 2011 2015 2019 2023 · Election Year: 2008 2012 2016 2020 2024

### QQQ · 30 J.

| Gruppe | alt | neu | nur neu (letzter Kurstag) | nur alt |
|---|---|---|---|---|
| Zyklus Post-Election | n=5, Ø +20.75 %, Win 80 % | n=7, Ø +19.70 %, Win 86 % | 2005 (Tag 364), 2017 (Tag 363) | — |
| Zyklus Midterm | n=4, Ø -0.64 %, Win 50 % | n=6, Ø -5.16 %, Win 50 % | 2006 (Tag 363), 2022 (Tag 364) | — |
| Zyklus Pre-Election | n=5, Ø +37.90 %, Win 100 % | n=7, Ø +35.33 %, Win 100 % | 2011 (Tag 364), 2023 (Tag 363) | — |
| Zyklus Election Year | n=6, Ø +11.45 %, Win 83 % | n=7, Ø +4.38 %, Win 71 % | 2000 (Tag 364) | — |
| Dez | n=20, Ø +1.46 %, Win 65 % | n=27, Ø +0.52 %, Win 56 % | 2000 (Tag 364), 2005 (Tag 364), 2006 (Tag 363), 2011 (Tag 364), 2017 (Tag 363), 2022 (Tag 364), 2023 (Tag 363) | — |
| Q4 | n=20, Ø +8.54 %, Win 80 % | n=27, Ø +6.50 %, Win 78 % | 2000 (Tag 364), 2005 (Tag 364), 2006 (Tag 363), 2011 (Tag 364), 2017 (Tag 363), 2022 (Tag 364), 2023 (Tag 363) | — |
| Jahr | n=20, Ø +17.97 %, Win 80 % | n=27, Ø +14.26 %, Win 78 % | 2000 (Tag 364), 2005 (Tag 364), 2006 (Tag 363), 2011 (Tag 364), 2017 (Tag 363), 2022 (Tag 364), 2023 (Tag 363) | — |

Aufgenommene Jahre neu: Post-Election: 2001 2005 2009 2013 2017 2021 2025 · Midterm: 2002 2006 2010 2014 2018 2022 · Pre-Election: 1999 2003 2007 2011 2015 2019 2023 · Election Year: 2000 2004 2008 2012 2016 2020 2024

### QQQ · max

| Gruppe | alt | neu | nur neu (letzter Kurstag) | nur alt |
|---|---|---|---|---|
| Zyklus Post-Election | n=5, Ø +20.75 %, Win 80 % | n=7, Ø +19.70 %, Win 86 % | 2005 (Tag 364), 2017 (Tag 363) | — |
| Zyklus Midterm | n=4, Ø -0.64 %, Win 50 % | n=6, Ø -5.16 %, Win 50 % | 2006 (Tag 363), 2022 (Tag 364) | — |
| Zyklus Pre-Election | n=5, Ø +37.90 %, Win 100 % | n=7, Ø +35.33 %, Win 100 % | 2011 (Tag 364), 2023 (Tag 363) | — |
| Zyklus Election Year | n=6, Ø +11.45 %, Win 83 % | n=7, Ø +4.38 %, Win 71 % | 2000 (Tag 364) | — |
| Dez | n=20, Ø +1.46 %, Win 65 % | n=27, Ø +0.52 %, Win 56 % | 2000 (Tag 364), 2005 (Tag 364), 2006 (Tag 363), 2011 (Tag 364), 2017 (Tag 363), 2022 (Tag 364), 2023 (Tag 363) | — |
| Q4 | n=20, Ø +8.54 %, Win 80 % | n=27, Ø +6.50 %, Win 78 % | 2000 (Tag 364), 2005 (Tag 364), 2006 (Tag 363), 2011 (Tag 364), 2017 (Tag 363), 2022 (Tag 364), 2023 (Tag 363) | — |
| Jahr | n=20, Ø +17.97 %, Win 80 % | n=27, Ø +14.26 %, Win 78 % | 2000 (Tag 364), 2005 (Tag 364), 2006 (Tag 363), 2011 (Tag 364), 2017 (Tag 363), 2022 (Tag 364), 2023 (Tag 363) | — |

Aufgenommene Jahre neu: Post-Election: 2001 2005 2009 2013 2017 2021 2025 · Midterm: 2002 2006 2010 2014 2018 2022 · Pre-Election: 1999 2003 2007 2011 2015 2019 2023 · Election Year: 2000 2004 2008 2012 2016 2020 2024

### ^GSPC · 10 J.

| Gruppe | alt | neu | nur neu (letzter Kurstag) | nur alt |
|---|---|---|---|---|
| Zyklus Post-Election | n=2, Ø +22.72 %, Win 100 % | n=3, Ø +21.29 %, Win 100 % | 2017 (Tag 363) | — |
| Zyklus Midterm | n=1, Ø -7.01 %, Win 0 % | n=2, Ø -13.48 %, Win 0 % | 2022 (Tag 364) | — |
| Zyklus Pre-Election | n=1, Ø +28.71 %, Win 100 % | n=2, Ø +26.72 %, Win 100 % | 2023 (Tag 363) | — |
| Zyklus Election Year | n=3, Ø +16.78 %, Win 100 % | n=3, Ø +16.85 %, Win 100 % | — | — |
| Dez | n=7, Ø +0.39 %, Win 71 % | n=10, Ø +0.22 %, Win 70 % | 2017 (Tag 363), 2022 (Tag 364), 2023 (Tag 363) | — |
| Q4 | n=7, Ø +3.39 %, Win 86 % | n=10, Ø +4.72 %, Win 90 % | 2017 (Tag 363), 2022 (Tag 364), 2023 (Tag 363) | — |
| Jahr | n=7, Ø +16.78 %, Win 86 % | n=10, Ø +14.09 %, Win 80 % | 2017 (Tag 363), 2022 (Tag 364), 2023 (Tag 363) | — |

Aufgenommene Jahre neu: Post-Election: 2017 2021 2025 · Midterm: 2018 2022 · Pre-Election: 2019 2023 · Election Year: 2016 2020 2024

### ^GSPC · 20 J.

| Gruppe | alt | neu | nur neu (letzter Kurstag) | nur alt |
|---|---|---|---|---|
| Zyklus Post-Election | n=4, Ø +22.88 %, Win 100 % | n=5, Ø +21.98 %, Win 100 % | 2017 (Tag 363) | — |
| Zyklus Midterm | n=3, Ø +5.46 %, Win 67 % | n=5, Ø +1.64 %, Win 60 % | 2006 (Tag 363), 2022 (Tag 364) | — |
| Zyklus Pre-Election | n=3, Ø +10.56 %, Win 67 % | n=5, Ø +11.06 %, Win 60 % | 2011 (Tag 364), 2023 (Tag 363) | — |
| Zyklus Election Year | n=5, Ø +4.59 %, Win 80 % | n=5, Ø +4.93 %, Win 80 % | — | — |
| Dez | n=15, Ø +0.85 %, Win 73 % | n=20, Ø +0.84 %, Win 75 % | 2006 (Tag 363), 2011 (Tag 364), 2017 (Tag 363), 2022 (Tag 364), 2023 (Tag 363) | — |
| Q4 | n=15, Ø +2.16 %, Win 73 % | n=20, Ø +3.81 %, Win 80 % | 2006 (Tag 363), 2011 (Tag 364), 2017 (Tag 363), 2022 (Tag 364), 2023 (Tag 363) | — |
| Jahr | n=15, Ø +10.83 %, Win 80 % | n=20, Ø +9.90 %, Win 75 % | 2006 (Tag 363), 2011 (Tag 364), 2017 (Tag 363), 2022 (Tag 364), 2023 (Tag 363) | — |

Aufgenommene Jahre neu: Post-Election: 2009 2013 2017 2021 2025 · Midterm: 2006 2010 2014 2018 2022 · Pre-Election: 2007 2011 2015 2019 2023 · Election Year: 2008 2012 2016 2020 2024

### ^GSPC · 30 J.

| Gruppe | alt | neu | nur neu (letzter Kurstag) | nur alt |
|---|---|---|---|---|
| Zyklus Post-Election | n=6, Ø +18.77 %, Win 83 % | n=8, Ø +16.86 %, Win 88 % | 2005 (Tag 364), 2017 (Tag 363) | — |
| Zyklus Midterm | n=5, Ø +3.73 %, Win 60 % | n=7, Ø +1.50 %, Win 57 % | 2006 (Tag 363), 2022 (Tag 364) | — |
| Zyklus Pre-Election | n=5, Ø +14.73 %, Win 80 % | n=7, Ø +13.89 %, Win 71 % | 2011 (Tag 364), 2023 (Tag 363) | — |
| Zyklus Election Year | n=7, Ø +7.69 %, Win 86 % | n=8, Ø +5.50 %, Win 75 % | 2000 (Tag 364) | — |
| Dez | n=23, Ø +1.04 %, Win 70 % | n=30, Ø +0.84 %, Win 70 % | 2000 (Tag 364), 2005 (Tag 364), 2006 (Tag 363), 2011 (Tag 364), 2017 (Tag 363), 2022 (Tag 364), 2023 (Tag 363) | — |
| Q4 | n=23, Ø +5.01 %, Win 83 % | n=30, Ø +5.01 %, Win 83 % | 2000 (Tag 364), 2005 (Tag 364), 2006 (Tag 363), 2011 (Tag 364), 2017 (Tag 363), 2022 (Tag 364), 2023 (Tag 363) | — |
| Jahr | n=23, Ø +11.25 %, Win 78 % | n=30, Ø +9.55 %, Win 73 % | 2000 (Tag 364), 2005 (Tag 364), 2006 (Tag 363), 2011 (Tag 364), 2017 (Tag 363), 2022 (Tag 364), 2023 (Tag 363) | — |

Aufgenommene Jahre neu: Post-Election: 1997 2001 2005 2009 2013 2017 2021 2025 · Midterm: 1998 2002 2006 2010 2014 2018 2022 · Pre-Election: 1999 2003 2007 2011 2015 2019 2023 · Election Year: 1996 2000 2004 2008 2012 2016 2020 2024

### ^GSPC · max

| Gruppe | alt | neu | nur neu (letzter Kurstag) | nur alt |
|---|---|---|---|---|
| Zyklus Post-Election | n=25, Ø +3.41 %, Win 56 % | n=32, Ø +6.74 %, Win 63 % | 1905 (Tag 364), 1933 (Tag 364), 1961 (Tag 363), 1977 (Tag 364), 1989 (Tag 363), 2005 (Tag 364), 2017 (Tag 363) | — |
| Zyklus Midterm | n=24, Ø +2.27 %, Win 50 % | n=31, Ø +2.53 %, Win 52 % | 1922 (Tag 364), 1950 (Tag 364), 1966 (Tag 364), 1978 (Tag 363), 1994 (Tag 364), 2006 (Tag 363), 2022 (Tag 364) | — |
| Zyklus Pre-Election | n=22, Ø +8.37 %, Win 77 % | n=31, Ø +11.12 %, Win 77 % | 1911 (Tag 364), 1915 (Tag 364), 1939 (Tag 364), 1955 (Tag 364), 1967 (Tag 363), 1983 (Tag 364), 1995 (Tag 363), 2011 (Tag 364), 2023 (Tag 363) | — |
| Zyklus Election Year | n=29, Ø +9.62 %, Win 79 % | n=32, Ø +8.95 %, Win 75 % | 1916 (Tag 364), 1972 (Tag 364), 2000 (Tag 364) | — |
| Dez | n=100, Ø +1.29 %, Win 70 % | n=126, Ø +1.20 %, Win 73 % | 1905 (Tag 364), 1911 (Tag 364), 1915 (Tag 364), 1916 (Tag 364), 1922 (Tag 364), 1933 (Tag 364), 1939 (Tag 364), 1950 (Tag 364), 1955 (Tag 364), 1961 (Tag 363), 1966 (Tag 364), 1967 (Tag 363), 1972 (Tag 364), 1977 (Tag 364), 1978 (Tag 363), 1983 (Tag 364), 1989 (Tag 363), 1994 (Tag 364), 1995 (Tag 363), 2000 (Tag 364), 2005 (Tag 364), 2006 (Tag 363), 2011 (Tag 364), 2017 (Tag 363), 2022 (Tag 364), 2023 (Tag 363) | — |
| Q4 | n=100, Ø +2.42 %, Win 71 % | n=126, Ø +2.54 %, Win 71 % | 1905 (Tag 364), 1911 (Tag 364), 1915 (Tag 364), 1916 (Tag 364), 1922 (Tag 364), 1933 (Tag 364), 1939 (Tag 364), 1950 (Tag 364), 1955 (Tag 364), 1961 (Tag 363), 1966 (Tag 364), 1967 (Tag 363), 1972 (Tag 364), 1977 (Tag 364), 1978 (Tag 363), 1983 (Tag 364), 1989 (Tag 363), 1994 (Tag 364), 1995 (Tag 363), 2000 (Tag 364), 2005 (Tag 364), 2006 (Tag 363), 2011 (Tag 364), 2017 (Tag 363), 2022 (Tag 364), 2023 (Tag 363) | — |
| Jahr | n=100, Ø +6.03 %, Win 66 % | n=126, Ø +7.34 %, Win 67 % | 1905 (Tag 364), 1911 (Tag 364), 1915 (Tag 364), 1916 (Tag 364), 1922 (Tag 364), 1933 (Tag 364), 1939 (Tag 364), 1950 (Tag 364), 1955 (Tag 364), 1961 (Tag 363), 1966 (Tag 364), 1967 (Tag 363), 1972 (Tag 364), 1977 (Tag 364), 1978 (Tag 363), 1983 (Tag 364), 1989 (Tag 363), 1994 (Tag 364), 1995 (Tag 363), 2000 (Tag 364), 2005 (Tag 364), 2006 (Tag 363), 2011 (Tag 364), 2017 (Tag 363), 2022 (Tag 364), 2023 (Tag 363) | — |

Aufgenommene Jahre neu: Post-Election: 1901 1905 1909 1913 1917 1921 1925 1929 1933 1937 1941 1945 1949 1953 1957 1961 1965 1969 1973 1977 1981 1985 1989 1993 1997 2001 2005 2009 2013 2017 2021 2025 · Midterm: 1902 1906 1910 1914 1918 1922 1926 1930 1934 1938 1942 1946 1950 1954 1958 1962 1966 1970 1974 1978 1982 1986 1990 1994 1998 2002 2006 2010 2014 2018 2022 · Pre-Election: 1903 1907 1911 1915 1919 1923 1927 1931 1935 1939 1943 1947 1951 1955 1959 1963 1967 1971 1975 1979 1983 1987 1991 1995 1999 2003 2007 2011 2015 2019 2023 · Election Year: 1900 1904 1908 1912 1916 1920 1924 1928 1932 1936 1940 1944 1948 1952 1956 1960 1964 1968 1972 1976 1980 1984 1988 1992 1996 2000 2004 2008 2012 2016 2020 2024

## Anhang B — Blog-Monatsbalken: Dezember je Konfiguration

| Konfiguration | alt: n, Ø Dez | neu: n, Ø Dez | neu aufgenommene Jahre (alle Tag 362–364) |
|---|---|---|---|
| GOOGL 15 | 11, +1,663 % | 15, +1,307 % | 2011, 2017, 2022, 2023 |
| TLT 20 | 15, −0,493 % | 20, −0,244 % | 2006, 2011, 2017, 2022, 2023 |
| ^GDAXI 38 | 7, +3,288 % | 38, +1,979 % | 1988–1991, 1993–1995, 1997–2003, 2005–2007, 2009–2015, 2017–2019, 2021–2023, 2025 |
| ^GSPC 30 | 23, +1,063 % | 30, +0,845 % | 2000, 2005, 2006, 2011, 2017, 2022, 2023 |

Heatmaps (^GSPC/^DJI/XLK/XLE 10, ^GDAXI 38): alt Renderfehler, neu alle Zellen belegt außer Okt–Dez 2026.
**Artikeltexte und `updated:`:** Entscheidung des Nutzers nach diesem Bericht (keine Textänderung vorgeschlagen, weil
kein Text einen Chartwert zitiert, der sich ändert).
