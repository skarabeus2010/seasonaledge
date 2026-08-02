---
title: "Long Gamma vs. Short Gamma: Das Regime, das über die Marktvolatilität entscheidet"
seo_title: "Long Gamma vs. Short Gamma: Vola-Regime erklärt"
slug: long-gamma-short-gamma-regime
date: 2026-08-02
category: education
tags: [gamma-regime, long-gamma, short-gamma, gamma-exposure, gex, zero-gamma-flip, gamma-ampel, volatilitaet, dealer-positioning, market-maker]
description: "Long Gamma vs. Short Gamma einfach erklärt: warum das Gamma-Regime über ruhige oder wilde Märkte entscheidet — und was der Zero-Gamma-Flip bedeutet."
ticker: SPY
status: published
---

<!--
Keyword-Plan:
- Haupt-Keyword: Gamma Regime (Long Gamma vs. Short Gamma)
- Neben-Keywords: Gamma Exposure, GEX, Zero-Gamma-Flip, Gamma-Ampel, vola-reduzierend, vola-forcierend, Netto-Gamma, Markt-Gamma-Index, Dealer-Hedging, Market Maker
- Long-Tail: was bedeutet long gamma short gamma, warum ist der markt manchmal ruhig manchmal wild, zero gamma flip erklärt, GEX Vorzeichen Bedeutung, wann verstärkt der markt bewegungen
- LSI: Volatilität, Optionsverfall, Delta-Hedging, Mean-Reversion, Momentum, Pinning, implizite Volatilität, VIX, Fragilität, Saisonalität
- Suchintention: Privatanleger wollen verstehen, was das Gamma-Regime ist, warum es die Volatilität steuert und wie man den Zustand (long/short Gamma) einordnet
-->

## Long Gamma oder Short Gamma? Warum manche Tage ruhig sind und andere wild

Manche Handelstage plätschern in einer engen Spanne dahin — jeder Dip wird sofort gekauft, jeder Ausbruch verpufft. An anderen Tagen schaukelt sich eine kleine Bewegung zu einer Lawine auf. Der Unterschied hat oft weniger mit Nachrichten zu tun als mit einem strukturellen Zustand des Marktes: dem **Gamma-Regime**.

Ob der Markt gerade im **Long-Gamma**- oder im **Short-Gamma**-Regime steckt, entscheidet, ob Optionshändler Bewegungen **dämpfen** oder **verstärken**. Es ist der wichtigste Ein-Zahl-Schalter im Dealer Positioning — und der Baustein, den man verstanden haben muss, bevor Begriffe wie Call-Wall oder Vanna überhaupt Sinn ergeben. Dieser Artikel erklärt beide Regime, den Kipppunkt dazwischen (den Zero-Gamma-Flip) und wie wir das Ganze bei SeasonAlpha als **Gamma-Ampel** sichtbar machen.

## Was Gamma Exposure (GEX) überhaupt misst

Kurz zur Einordnung, falls du neu einsteigst: Wenn du eine Option kaufst, verkauft sie dir meist ein Market Maker — der „Dealer". Er will kein Marktrisiko tragen, sondern nur an der Geld-Brief-Spanne verdienen. Also sichert er seine Position im Basiswert ab (Delta-Hedging).

**Gamma** misst, wie stark sich diese Absicherung ändert, wenn der Kurs sich bewegt. Und weil Dealer riesige Bücher führen, werden ihre gebündelten Hedging-Käufe und -Verkäufe selbst zu einer Marktkraft. Die aggregierte Kennzahl über alle offenen Optionen heißt **Gamma Exposure**, kurz **GEX**. Bei uns siehst du sie als **Markt-Gamma-Index** (net-GEX).

Wenn du die Grundlagen — Delta-Hedging, Vanna, Charm, Call- und Put-Wall — noch einmal von vorn nachlesen willst, findest du sie im Basisartikel [Dealer Positioning erklärt](/blog/dealer-positioning-gamma-vanna-charm/). Hier gehen wir gezielt in die Tiefe: das Vorzeichen des Gamma und was es für die Volatilität bedeutet.

## Die zwei Regime: vola-reduzierend vs. vola-forcierend

Das gesamte Verhalten hängt an einem einzigen Vorzeichen — dem des Netto-Gamma aller Dealer.

### Long Gamma (positives Netto-Gamma): der Stoßdämpfer

Sind Dealer in Summe **long Gamma**, hedgen sie **gegen** die Bewegung. Steigt der Kurs, müssen sie verkaufen; fällt er, müssen sie kaufen. Sie handeln also antizyklisch und wirken wie ein **Stoßdämpfer**: Bewegungen werden gebremst, die Spanne bleibt eng, der Markt neigt zu Mean-Reversion und „Pinning" an großen Strikes. Dips werden strukturell gekauft. Das ist das **vola-reduzierende** Regime.

### Short Gamma (negatives Netto-Gamma): der Brandbeschleuniger

Sind Dealer **short Gamma**, dreht sich die Logik um. Jetzt müssen sie **mit** der Bewegung hedgen: in steigende Kurse kaufen, in fallende verkaufen. Sie werfen also Öl ins Feuer. Ein kleiner Impuls kann sich zu einem Trend aufschaukeln, die Volatilität steigt, Ausschläge werden größer. Dips werden verkauft statt gekauft. Das ist das **vola-forcierende** Regime — und der Nährboden für die berüchtigten Ausverkaufs-Kaskaden.

| Merkmal | Long Gamma (positiv) | Short Gamma (negativ) |
|---|---|---|
| Dealer-Hedging | verkauft Stärke, kauft Schwäche | kauft Stärke, verkauft Schwäche |
| Wirkung auf Vola | dämpfend (vola-reduzierend) | verstärkend (vola-forcierend) |
| Typisches Verhalten | Mean-Reversion, enge Spanne | Momentum, Trend, große Ausschläge |
| Dips werden ... | gekauft (stabilisiert) | verkauft (beschleunigt) |
| Analogie | Stoßdämpfer | Brandbeschleuniger |

## Der Zero-Gamma-Flip: der Kipppunkt

Zwischen beiden Welten liegt eine scharfe Grenze — der **Zero-Gamma-Flip**. Das ist der Kursstand, an dem das Netto-Gamma sein Vorzeichen wechselt. Oberhalb ist der Markt (im typischen Fall) long Gamma und ruhig, unterhalb short Gamma und nervös.

Entscheidend ist die **Distanz des Kurses zum Flip**. Liegt der Spot komfortabel darüber, wirkt das Dämpfer-Regime stabil. Klebt er direkt am Flip, kann das Regime schon bei einer kleinen Bewegung kippen — und aus dem Stoßdämpfer wird der Brandbeschleuniger. Genau diese Nähe ist ein **Fragilitäts-Signal**: nicht die Richtung, sondern die Kipp-Anfälligkeit.

Ein reales Beispiel aus unserem Live-Snapshot vom 2. August 2026 macht das greifbar: Der SPY stand bei rund **747 Punkten**, der Zero-Gamma-Flip lag bei etwa **748**. Der Kurs klebte also praktisch am Kipppunkt — knapp im Short-Gamma-Bereich. Der aggregierte Markt-Gamma-Index war mit rund **−3,4 Mrd. $ pro %** klar negativ, das Regime lautete **vola-forcierend**. Interessant dabei: Während die Index-ETFs (SPY, QQQ, IWM) short Gamma waren, standen mehrere Mega-Caps wie MSFT, NVDA und AMZN gleichzeitig im Long-Gamma-Bereich. Das Gesamtbild ist also selten einheitlich — genau deshalb lohnt der aggregierte Blick.

## Was die Wissenschaft sagt: Praktiker-Idee, akademisch validiert

Hier ist Sauberkeit wichtig, denn eine junge Finanzseite muss ihre Quellen ehrlich trennen.

**Der Ursprung ist Praktiker-Wissen.** Der Begriff „GEX" und die Zwei-Regime-Intuition stammen aus einem **Branchen-White-Paper (2016)**. Deren viel zitierte These: Bei niedriger Volatilität sagt das Vorzeichen des Gamma die Marktstabilität besser vorher als der VIX selbst. Das ist eine anregende Beobachtung — aber es ist eine **Vendor-Quelle**, kein peer-reviewtes Ergebnis. So sollte man es auch behandeln.

**Die akademische Validierung** liefert die Arbeit **„Gamma Fragility" von Barbon & Buraschi (2021)**. Sie zeigen mit harten Daten: Ist das aggregierte Dealer-Gamma **negativ**, entsteht Intraday-**Momentum** (Bewegungen setzen sich fort); ist es **positiv**, dominiert **Reversal** (Bewegungen kehren um). Der Effekt ist in illiquiden Phasen am stärksten. Das deckt sich exakt mit der Stoßdämpfer-vs.-Brandbeschleuniger-Logik.

Eine wichtige Einschränkung, die wir bewusst betonen: Der von Barbon & Buraschi gemessene Effekt ist **intraday und sehr kurzlebig** — er verpufft meist innerhalb von ein bis zwei Handelstagen. Er ist **kein** Rezept, um Tagesbewegungen zu traden. Wir nutzen daher ausschließlich die **Regime-Klassifikation** (long vs. short Gamma als Kontext), **nicht** den kurzfristigen Handelseffekt. Und Barbon & Buraschi ist ein breit zitiertes Working Paper, noch keine final begutachtete Publikation — auch das gehört zur ehrlichen Einordnung.

## Die Gamma-Ampel bei SeasonAlpha: Regime auf einen Blick

Aus dieser Zwei-Regime-Logik machen wir eine simple **Gamma-Ampel**. Sie fasst zwei Informationen zusammen: das **Vorzeichen** des Markt-Gamma-Index (dämpfend oder verstärkend) und die **Distanz zum Zero-Gamma-Flip** (wie kipp-anfällig das aktuelle Regime ist).

- **Grün / long Gamma:** Dämpfer-Regime, Spot deutlich über dem Flip — tendenziell ruhige, mean-revertende Tage.
- **Rot / short Gamma:** Verstärker-Regime, Spot unter dem Flip — erhöhte Trend- und Ausschlagneigung.
- **Nahe am Flip:** Übergangszone — das Regime kann jederzeit kippen, Vorsicht ist angebracht.

Du findest die Ampel live auf der Seite [Dealer Positioning](/dealer-positioning) — für SPY, QQQ und die wichtigsten US-Basiswerte. Als Ergänzung zum Gesamtmarkt-Risiko lohnt der Blick auf unsere [Crash-Frühwarnung](/crash-fruehwarnung): Beide Werkzeuge beschreiben Fragilität, aber aus unterschiedlichen Blickwinkeln — das Gamma-Regime aus der Options-Mechanik, die Crash-Ampel aus dem breiteren Marktregime.

## Regime trifft Saisonalität: der SeasonAlpha-Winkel

Jetzt der Teil, den kein reiner Gamma-Anbieter liefert. GEX-Seiten zeigen den Zustand im Jetzt. Saisonalitäts-Seiten zeigen das Kalendermuster im Mittel. **Wir besitzen beides** — und das ist der eigentliche Hebel.

![SPY — net-Gamma je Verfall: das Vorzeichen je Laufzeit zeigt das Dealer-Regime](long-gamma-short-gamma-regime/chart-gamma-by-term-spy.png)

Der Chart zeigt das **net-Gamma des SPY je Verfallstermin**. Das Vorzeichen je Laufzeit verrät das Regime: positive Balken (grün) stehen für **Long-Gamma** — Dealer dämpfen Bewegungen, der Markt läuft ruhiger; negative (rot) für **Short-Gamma** — Dealer verstärken Bewegungen, der Markt wird fragiler. Genau hier, im Wechsel dieser Regime entlang des Kalenders, kommen Gamma-Regime und Saisonalität zusammen.



Die zweite Grafik bricht das auf einzelne Kalendermonate herunter (aktueller Monat hervorgehoben). Der Spätsommer und der Frühherbst gehören historisch zu den holprigeren Fenstern des Jahres — dünnere Liquidität, breitere Streuung. Ein Markt, der ausgerechnet in einem solchen Fenster **short Gamma** ist (wie im Snapshot oben), verbindet zwei fragilitäts-fördernde Faktoren: den strukturellen Verstärker aus der Options-Mechanik und die saisonal dünnere Liquidität. Aus „Muster" wird so „Mechanismus plus Kontext".

Das ist der Moat: Wir zeigen nicht nur, *dass* ein Fenster statistisch auffällig ist, sondern liefern mit dem Gamma-Regime eine strukturelle Ebene, die erklärt, *warum* die Ausschläge gerade jetzt größer oder kleiner ausfallen könnten.

## Ehrlichkeit zuerst: was die Gamma-Ampel kann — und was nicht

Dealer Positioning ist ein YMYL-Thema (Your Money or Your Life). Deshalb legen wir die Grenzen offen, statt Präzision vorzutäuschen:

- **Naive Dealer-Heuristik.** Wir nehmen an, Dealer sind long Calls und short Puts. Das ist eine bewährte erste Näherung für Index-Gamma, aber **kein echtes Inventory-Modell** wie bei kommerziellen Anbietern — und keine Kenntnis der realen Dealer-Bücher.
- **EOD-Daten von Yahoo.** Wir rechnen auf Open Interest und impliziter Vola zum Handelsschluss. Unsere Werte weichen daher von proprietären Intraday-/0DTE-Modellen ab.
- **Live-Snapshot, keine Zeitreihe.** Unsere Gamma-Historie beginnt erst mit dem Snapshot-Cron (ab Sommer 2026). Aussagen wie „wie oft war der Markt short Gamma" lassen sich (noch) **nicht** sauber backtesten — die Ampel ist ein aktueller Stand, keine geprüfte historische Statistik.
- **Kein Signal.** Das Regime ist Kontext, kein Kauf- oder Verkaufssignal. Der akademische Fragilitäts-Effekt ist intraday und transitorisch (ein bis zwei Tage) — wir nutzen nur die Klassifikation.

Diese Grenzen sind kein Makel, sondern Teil der Methode. Wer das Regime ernst nimmt, muss wissen, wie belastbar die Datenbasis ist.

## Fazit

Das Gamma-Regime ist der einprägsamste Baustein im Dealer Positioning: Ein einziges Vorzeichen entscheidet, ob Dealer den Markt dämpfen (long Gamma, vola-reduzierend) oder anheizen (short Gamma, vola-forcierend). Der Zero-Gamma-Flip markiert den Kipppunkt — und die Nähe des Kurses dazu ist ein Fragilitäts-Barometer.

Praktikerwissen aus der Branche, akademisch gestützt durch Barbon & Buraschi, ehrlich gelabelt als Regime-Kontext ohne Signal-Anspruch: So wird aus einem Buzzword ein nützliches Denkwerkzeug. Und wenn du es mit unserem Saisonkalender kombinierst, siehst du nicht nur den aktuellen Zustand, sondern auch, in welchem saisonalen Umfeld er auftritt. Probiere die Gamma-Ampel auf **[seasonalpha.ai/dealer-positioning](/dealer-positioning)** selbst aus.

## Häufige Fragen

### Was bedeutet Long Gamma und Short Gamma?

Long Gamma (positives Netto-Gamma) bedeutet, dass Dealer Bewegungen dämpfen — sie verkaufen in Stärke und kaufen in Schwäche, der Markt neigt zu enger Spanne und Mean-Reversion. Short Gamma (negatives Netto-Gamma) bedeutet das Gegenteil: Dealer verstärken Bewegungen, die Volatilität steigt, Trends setzen sich eher fort.

### Was ist der Zero-Gamma-Flip?

Der Zero-Gamma-Flip ist der Kursstand, an dem das Netto-Gamma sein Vorzeichen wechselt — die Grenze zwischen dem vola-reduzierenden und dem vola-forcierenden Regime. Klebt der Kurs nah am Flip, kann das Regime schon bei kleinen Bewegungen kippen. Das gilt als Fragilitäts-Hinweis, nicht als Richtungsprognose.

### Ist das Gamma-Regime ein Handelssignal?

Nein. Es ist ein struktureller Kontext, kein Kauf- oder Verkaufssignal. Der wissenschaftlich belegte Effekt (Barbon & Buraschi) ist intraday und sehr kurzlebig; wir nutzen ausschließlich die Regime-Klassifikation als Einordnung, nicht für kurzfristige Trades.

### Schlägt GEX wirklich den VIX?

Das ist die These aus einem Branchen-White-Paper — bei niedriger Volatilität soll das Gamma-Vorzeichen die Stabilität besser anzeigen als der VIX. Das ist eine anregende Praktiker-Beobachtung aus einer Vendor-Quelle, kein peer-reviewtes Ergebnis. Wir behandeln es als Hypothese, nicht als Gesetz.
