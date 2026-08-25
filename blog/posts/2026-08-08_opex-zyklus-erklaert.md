---
title: "Der OPEX-Zyklus: Wie der Optionsverfall den Handelsmonat strukturiert"
seo_title: "OPEX-Zyklus erklärt: die 4 Phasen des Verfalls"
slug: opex-zyklus-erklaert
date: 2026-08-08
author: SeasonAlpha Research
category: education
tags: [opex-zyklus, optionsverfall, vanna, charm, dealer-positioning, pre-opex-drift, post-opex, triple-witching, saisonalitaet]
description: "Der OPEX-Zyklus erklärt: die vier Phasen rund um den Optionsverfall, die Pre-OPEX-Drift, der Pin und das Vola-Fenster danach — Mechanik statt Signal."
ticker: SPY
status: published
---

<!--
Keyword-Plan:
- Haupt-Keyword: OPEX-Zyklus
- Neben-Keywords: Optionsverfall-Zyklus, monatlicher Optionszyklus, Vanna-Charm-Zyklus, Pre-OPEX-Drift, Post-OPEX-Fenster, Optionsverfall erklärt, Dealer-Hedging, Delta-Hedging, Triple Witching
- Long-Tail: was ist der OPEX-Zyklus, vier Phasen des Optionsverfalls, warum steigt der Markt vor dem Verfall, warum wird es nach dem Verfall volatiler, wie strukturiert der Optionsverfall den Handelsmonat
- LSI: Market Maker, Absicherung, Gamma-Exposure, implizite Volatilität, Open Interest, dritter Freitag, Verfallstag, normalisierte Renditen, Pinning
- Suchintention: Anleger wollen den wiederkehrenden monatlichen Rhythmus rund um den Optionsverfall verstehen — die Mechanik dahinter, nicht ein einzelnes Handelssignal.
-->

## Was der OPEX-Zyklus ist

Der Aktienmarkt hat einen versteckten Taktgeber, den die meisten Anleger nie sehen: den **OPEX-Zyklus**. OPEX steht für *option expiration* — den Optionsverfall am dritten Freitag jedes Monats. Rund um diesen Termin läuft ein immer gleicher Vier-Phasen-Rhythmus ab, der den Handelsmonat leise strukturiert: erst der ruhige Aufbau, dann eine oft geräuscharme Aufwärtsdrift, der Pin am Verfallstag und schließlich ein richtungsoffeneres, volatileres Fenster danach.

Wichtig vorweg: Der OPEX-Zyklus ist **kein Handelssignal**, sondern struktureller Kontext. Er erklärt, *warum* bestimmte saisonale Muster überhaupt existieren. In diesem Artikel zerlegen wir den Zyklus in seine vier Phasen, zeigen an echten Dealer-Daten, wo die Absicherungsströme sich ballen — und benennen, wo das Muster kippt.

## Die vier Phasen des Optionsverfall-Zyklus

Der Zyklus ist ein Kreislauf, kein linearer Ablauf. Nach jedem Verfall beginnt er von vorn. Das folgende Schaubild zeigt die vier Stationen: **Options Positions Build** (Positionsaufbau), **Options Hedges Build** (Hedge-Aufbau), **Options Expire** (Verfall) und **Options Hedges Covered** (Hedge-Auflösung).

![Der OPEX-Zyklus als Kreislauf: Positionsaufbau, Hedge-Aufbau, Optionsverfall und Hedge-Auflösung — die vier Phasen rund um den dritten Freitag](opex-zyklus-erklaert/opex-cycle.png)

Übersetzt in den Handelsalltag sehen die vier Phasen so aus:

| Phase | Was passiert | Marktwirkung |
|-------|--------------|--------------|
| 1. Positionsaufbau | Anleger und Fonds kaufen Optionen — vor allem Index-Puts als Absicherung | Aufbau von offenem Interesse (Open Interest) |
| 2. Hedge-Aufbau | Dealer/Market Maker sichern ihr Risiko im Basiswert ab (Delta-Hedging) | Es entsteht ein „Hedge-Polster" |
| 3. Verfall | Kontrakte laufen am 3. Freitag aus (Triple Witching in Mär/Jun/Sep/Dez) | Pin an Strikes, Großverfall |
| 4. Hedge-Auflösung | Die Absicherung wird zurückgekauft, gebundenes Kapital wird frei | Post-OPEX-Fenster, richtungsoffener |

### Phase 1 — Positionsaufbau

Am Anfang steht die Nachfrage. Nach dem letzten Verfall bauen Institutionen und Fonds frische Optionspositionen auf — überwiegend **Index-Puts** als Versicherung gegen fallende Kurse. Das offene Interesse an den nächsten Verfallsterminen wächst. Diese Nachfrage ist die eigentliche Ursache des ganzen Zyklus: Ohne die Absicherungskäufe der Investoren gäbe es nichts, was die Dealer hedgen müssten.

### Phase 2 — Hedge-Aufbau

Die **Dealer** — die Market Maker, die diese Optionen verkaufen — stehen jetzt auf der Gegenseite. Sie sind netto short Puts und müssen ihr Risiko im Basiswert neutralisieren. Das nennt man **Delta-Hedging**: Sie verkaufen Aktien oder Futures leer, um gegen fallende Kurse abgesichert zu sein. Über den Monat baut sich so ein „Hedge-Polster" auf. Solange die Dealer dieses Polster halten, wirken sie oft stabilisierend — sie kaufen in Schwäche und verkaufen in Stärke.

### Phase 3 — Der Verfall

Am **dritten Freitag** laufen die Kontrakte aus. Viermal im Jahr — im März, Juni, September und Dezember — verfallen Index-Optionen, Index-Futures und Aktienoptionen gleichzeitig. Diesen Großverfall nennt man **Triple Witching**. An diesem Tag ballt sich das größte Volumen an offenem Interesse, und die Kurse neigen dazu, an den wichtigsten Ausübungspreisen zu „kleben" — das sogenannte [Pinning](/blog/pinning-call-wall-put-wall/).

### Phase 4 — Hedge-Auflösung

Sobald die Kontrakte verfallen sind, braucht der Dealer die Absicherung nicht mehr. Er **löst das Hedge-Polster auf** und kauft seine Short-Absicherung zurück. Gebundenes Kapital wird frei — und mit dem Wegfall des stabilisierenden Polsters verliert der Markt einen Teil seiner „Bremse". Genau hier beginnt der Zyklus von vorn, während sich das Marktverhalten spürbar ändert.

## Warum daraus ein monatlicher Rhythmus wird

Aus diesen vier Phasen entstehen drei bekannte Muster, die den Handelsmonat prägen.

### Die ruhige Aufwärtsdrift vor dem Verfall

Das Hedge-Polster aus Phase 2 ist nicht statisch — es schrumpft in den Verfall hinein. Zwei „Griechen" sorgen dafür:

- **Charm (Zeitverfall):** Je näher der Verfall rückt, desto kleiner wird das Delta der aus dem Geld liegenden Puts. Der Dealer braucht weniger Short-Hedge und **kauft Aktien zurück**.
- **Vanna (Volatilität):** Bleibt der Markt ruhig, sinkt die implizite Volatilität. Auch das lässt das Put-Delta schrumpfen — der Dealer deckt sich ebenfalls ein.

Beide Kräfte wirken in dieselbe Richtung: ein mechanischer, oft geräuscharmer **Kaufdruck in die OPEX-Woche hinein**. Das ist die bekannte Pre-OPEX-Drift. Den spezifischen Eröffnungs-Sprung am dritten Freitag — im Schnitt rund +18,5 Basispunkte über den Zeitraum 2003–2021 — haben wir in einer eigenen Studie zum [Third-Friday-Effekt](/blog/opex-effekt-sp500-third-friday-drift/) auseinandergenommen.

### Der Pin am Verfallstag

Am Verfallstag selbst dominiert nicht die Richtung, sondern die Anziehung. Wo viel offenes Interesse an einem Ausübungspreis liegt, ziehen die Absicherungsströme den Kurs immer wieder zurück in Richtung dieses Strikes — der Markt „pinnt". Das ist kein Aberglaube, sondern in der akademischen Forschung dokumentiert (siehe unten).

### Das Post-OPEX-Vola-Fenster

Fällt in Phase 4 das Hedge-Polster weg, verschwindet die stabilisierende Wirkung der Dealer. Der Markt wird richtungsoffener und anfälliger für größere Bewegungen — die berüchtigte Post-OPEX-Schwäche oder, neutraler gesagt, das **Post-OPEX-Vola-Fenster**. Die ruhige Drift *in* den Verfall und die höhere Nervosität *danach* sind zwei Seiten derselben Mechanik.

## Was die Daten zeigen

Wo im Kalender ballen sich die Absicherungsströme wirklich? Der folgende Chart zeigt die **Charm-Exposure des SPY je Verfallstermin** — also, wie stark sich die Dealer-Absicherung an jedem Termin allein durch den Zeitverfall täglich verschiebt.

![SPY — Charm-Exposure je Verfall: die größten zeitverfall-getriebenen Hedge-Ströme ballen sich an den monatlichen Verfallsterminen](opex-zyklus-erklaert/chart-charm-by-term-spy.png)

Das Bild ist eindeutig: Der mit Abstand größte Balken liegt auf dem **nächsten monatlichen Verfall (21. August)** — dem dritten Freitag. Der zweitgrößte sitzt auf dem **September-Termin (18. September)**, dem nächsten Triple Witching. Die vielen kleinen Termine dazwischen bleiben kaum sichtbar. Genau diese Konzentration ist der Kern des Zyklus: Der Zeitverfall zwingt die Dealer nicht gleichmäßig, sondern **gebündelt rund um die großen Verfallstage** zu Anpassungen. Das ist der mechanische Motor hinter der Pre-OPEX-Drift.

Zwei Einordnungen sind Pflicht: Erstens ist das eine **Momentaufnahme** aus den End-of-Day-Optionsdaten (Stand 8. August 2026), kein Durchschnitt über viele Monate. Zweitens beruht das Dealer-Vorzeichen auf einer **vereinfachten Heuristik** (long Calls / short Puts), nicht auf echten Dealer-Büchern. Der Chart zeigt die *Struktur* der Absicherungsströme, kein Handelssignal.

## Wissenschaftliche Fundierung

Der OPEX-Zyklus ist nicht nur Praktiker-Folklore. Mehrere Bausteine sind peer-reviewt:

- **Ni, Pearson & Poteshman (2005), *Journal of Financial Economics*** — der Klassiker zum **Pinning**: Schlusskurse optionierter Einzelaktien clustern am Verfallstag an den Ausübungspreisen; die Renditen wurden im Schnitt um rund 16,5 Basispunkte verschoben. Das belegt Phase 3.
- **Barbon & Buraschi (2021)** — beschreiben die **Gamma-Fragilität**: Wie das Vorzeichen der Dealer-Positionierung die Stabilität des Marktes verändert. Genau das erklärt, warum nach dem Verfall (Phase 4) das Vola-Fenster aufgeht, sobald das stabilisierende Gamma-Polster wegfällt.
- **Baltussen, Terstegge & Whelan (2024)** — der oben verlinkte Third-Friday-Effekt: der messbare Eröffnungs-Sprung am Verfallstag, zurückgeführt auf charm-getriebenes Hedging.

Man sollte sauber trennen: Pinning und der Third-Friday-Sprung sind in Finanzjournalen dokumentierte Effekte. Die exakte Größe der **Pre-OPEX-Drift** und der **Post-OPEX-Schwäche** dagegen ist stärker vom Marktumfeld abhängig und gehört eher ins Reich des belegten Praktiker-Wissens als der harten Statistik.

## Grenzen und Gegenbeispiele

Ein nüchterner Blick auf den Zyklus muss die Bruchstellen zeigen.

**Muster verschwinden, wenn alle sie kennen.** Je bekannter die Pre-OPEX-Drift wird, desto eher wird sie weggehandelt. Ein historischer Durchschnitt ist keine Prognose für den nächsten Freitag.

**Makro schlägt Mechanik.** Eine Fed-Sitzung, ein Inflationswert oder eine geopolitische Nachricht überlagert den dünnen OPEX-Rhythmus jederzeit. Der Zyklus ist ein leises Hintergrundmuster, keine dominante Kraft.

**Die Positionierung wechselt das Vorzeichen.** Der Zyklus wirkt anders, je nachdem, ob die Dealer insgesamt long oder short Gamma stehen. In einem [Long-Gamma-Regime](/blog/dealer-positioning-gamma-vanna-charm/) dämpfen sie Bewegungen, im Short-Gamma-Regime verstärken sie sie — dasselbe Kalenderdatum kann so ganz unterschiedlich wirken.

**Wir rechnen mit Tagesschlusskursen.** SeasonAlpha nutzt normalisierte Close-zu-Close-Renditen (jedes Jahr auf 100 normiert). Den Eröffnungs-Sprung am Verfallstag können wir damit nicht eins zu eins nachbauen — wir zeigen die Struktur der Ströme und den saisonalen Rahmen, nicht den Intraday-Sprung selbst.

## So nutzt du den Zyklus auf SeasonAlpha

Der eigentliche Mehrwert liegt im **Verständnis**, nicht im Klick auf „Kaufen". Wer den Zyklus kennt, ordnet Marktbewegungen besser ein: Eine ruhige Aufwärtsphase vor dem Verfall ist selten ein starkes Kaufsignal, und ein nervöseres Fenster danach ist selten der Anfang eines Crashs — beides ist oft einfach der OPEX-Rhythmus.

Konkret findest du die Bausteine hier: Den börsengenauen **Kalender** für OPEX, Triple Witching und VIXpiration liefert die Seite [Optionsverfall](/opex). Die aktuellen **Gamma-, Vanna- und Charm-Kennzahlen** — also, in welcher Phase des Zyklus die Dealer gerade stehen — zeigt [Dealer Positioning](/dealer-positioning). Und die saisonalen Muster, die daraus entstehen, siehst du über die Wochentag- und Monatszyklus-Seiten. So verheiratet SeasonAlpha den Kalender mit den Dealer-Flows: Du siehst nicht nur *dass* ein Muster existiert, sondern verstehst die strukturelle Ursache dahinter.

## Fazit

Der OPEX-Zyklus ist der versteckte monatliche Taktgeber des Aktienmarktes: Positionen werden aufgebaut, Dealer hedgen, die Kontrakte verfallen am dritten Freitag, und die Absicherung wird aufgelöst. Daraus entstehen die ruhige Pre-OPEX-Drift, der Pin am Verfallstag und das richtungsoffenere Fenster danach.

Der Zyklus erklärt *warum* — er ist Kontext, kein Signal. Muster schwächen sich ab, Makro überlagert sie, und das Vorzeichen der Dealer-Positionierung dreht die Wirkung. Erkunde den [Optionsverfall-Kalender](/opex) und das [Dealer Positioning](/dealer-positioning) selbst auf **seasonalpha.ai** — und sieh, in welcher Phase des Zyklus der Markt gerade steckt.

## Häufige Fragen

### Was ist der OPEX-Zyklus einfach erklärt?

Der OPEX-Zyklus ist der wiederkehrende Vier-Phasen-Rhythmus rund um den monatlichen Optionsverfall (den dritten Freitag). Anleger bauen Optionspositionen auf, Dealer sichern sich im Basiswert ab, am Verfallstag laufen die Kontrakte aus, und danach wird die Absicherung wieder aufgelöst. Aus diesem Kreislauf entstehen die typischen Muster: die ruhige Aufwärtsdrift vor dem Verfall und ein volatileres Fenster danach.

### Warum ist der Markt vor dem Optionsverfall oft ruhig und leicht steigend?

Weil Dealer ihre Short-Absicherung in den Verfall hinein zurückkaufen müssen. Zeitverfall (Charm) und fallende Volatilität (Vanna) lassen das Delta ihrer verkauften Puts schrumpfen — beides zwingt sie zu Käufen im Basiswert. Dieser mechanische Kaufdruck erzeugt die geräuscharme Pre-OPEX-Drift. Er ist ein Nebeneffekt des Hedgings, keine Meinung der Dealer über die Marktrichtung.

### Warum wird es nach dem Verfall oft volatiler?

Nach dem Verfall lösen die Dealer ihr Hedge-Polster auf. Damit fällt die stabilisierende Wirkung weg, die den Markt vorher in engen Bahnen gehalten hat. Der Markt wird richtungsoffener und anfälliger für größere Bewegungen — das Post-OPEX-Vola-Fenster. Barbon und Buraschi (2021) beschreiben diese Gamma-Fragilität wissenschaftlich.

### Kann ich den OPEX-Zyklus als Handelsstrategie nutzen?

Der Zyklus ist struktureller Kontext, kein Handelssignal und keine Anlageberatung. Die Muster sind dünn, schwächen sich ab, wenn sie bekannt werden, und werden von Makro-Ereignissen jederzeit überlagert. Sein Wert liegt darin, Marktbewegungen besser einzuordnen — nicht darin, mechanisch Kauf- oder Verkaufsentscheidungen abzuleiten.

<!--
#### Social Media Snippet

**LinkedIn:** Der Aktienmarkt hat einen versteckten monatlichen Taktgeber: den OPEX-Zyklus. Vier Phasen rund um den Optionsverfall am dritten Freitag — Positionsaufbau, Hedge-Aufbau, Verfall, Hedge-Auflösung. Daraus entstehen drei bekannte Muster: die ruhige Pre-OPEX-Drift (Charm & Vanna zwingen Dealer zum Rückkauf ihrer Absicherung), der Pin am Verfallstag (Ni/Pearson/Poteshman 2005) und das richtungsoffenere Vola-Fenster danach (Barbon/Buraschi 2021, Gamma-Fragilität). Unsere aktuellen Charm-Daten zeigen es klar: Die Absicherungsströme ballen sich an den monatlichen Verfallsterminen. Wichtig: Das ist Mechanik und Kontext, kein Handelssignal. In welcher Phase steckt der Markt gerade? https://seasonalpha.ai/dealer-positioning

**Twitter/X:** Der OPEX-Zyklus: 4 Phasen rund um den Optionsverfall → Pre-OPEX-Drift (Charm/Vanna), Pin am Verfallstag, Vola-Fenster danach. Unsere Charm-Daten zeigen: Hedge-Ströme ballen sich an den monatlichen Verfällen. Mechanik, kein Signal. seasonalpha.ai/dealer-positioning #OPEX #Optionen #SP500

#### Interne Verlinkung
- /opex (Optionsverfall-Kalender — direktes Feature)
- /dealer-positioning (Gamma/Vanna/Charm live — aktuelle Phase des Zyklus)
- /blog/opex-effekt-sp500-third-friday-drift/ (der spezifische Third-Friday-Sprung, +18,5 bps)
- /blog/dealer-positioning-gamma-vanna-charm/ (Long- vs. Short-Gamma-Regime, Mechanismus)
- /blog/pinning-call-wall-put-wall/ (Pinning am Verfallstag)
- /vixpiration (der zweite Verfallszyklus rund um den VIX)

#### Content-Ideen (Folgeartikel)
- „Post-OPEX-Schwäche: Was in der Woche nach dem Verfall wirklich passiert (Daten-Studie)"
- „Long vs. Short Gamma: Wie das Dealer-Vorzeichen denselben Kalendertag umkehrt"
- „VIXpiration: Der zweite Verfallszyklus, den kaum jemand kennt"
-->
