# -*- coding: utf-8 -*-
"""Erzeugt landing/pages/studien.html + die EN-Schluessel in en.json.

Die Studien stehen hier EINMAL mit DE- und EN-Text. Wuerde man die Karten von
Hand ins HTML schreiben und die EN-Werte getrennt in en.json pflegen, laufen
die beiden Seiten frueher oder spaeter auseinander — und zwar still, weil
verify_en nur meldet, was FEHLT, nicht was inhaltlich nicht mehr passt.
"""
import io
import json

# chip: belegt | teilweise | offen | beschreibend
S = [
 dict(k="pinning", chip="belegt", datum="2026-09-22",
   href="/blog/pinning-verfallstag/", en_href="/en/blog/options-expiration-pinning/",
   t_de="Pinning am Verfallstag",
   t_en="Pinning on expiration day",
   f_de="Schliessen Aktien am Optionsverfall h&auml;ufiger genau auf einem Strike?",
   f_en="Do stocks close exactly on a strike more often on option expiration days?",
   e_de="Ja, aber knapp. An Verfallstagen schliessen <b>6,88&nbsp;%</b> der Titel auf einem "
        "Strike gegen <b>6,53&nbsp;%</b> an gew&ouml;hnlichen Tagen. Die Differenz von 0,35 "
        "Prozentpunkten h&auml;lt einem Permutationstest stand (<b>p&nbsp;=&nbsp;0,0050</b>). "
        "Vor 2010 war sie nicht messbar (p&nbsp;=&nbsp;0,27), seither ist sie es "
        "(p&nbsp;=&nbsp;0,0015) &mdash; der Effekt wird st&auml;rker, nicht schw&auml;cher.",
   e_en="Yes, but barely. On expiration days <b>6.88&nbsp;%</b> of stocks close on a strike "
        "against <b>6.53&nbsp;%</b> on ordinary days. The gap of 0.35 percentage points "
        "survives a permutation test (<b>p&nbsp;=&nbsp;0.0050</b>). Before 2010 it was not "
        "measurable (p&nbsp;=&nbsp;0.27); since then it is (p&nbsp;=&nbsp;0.0015) &mdash; the "
        "effect is growing, not fading.",
   b_de="158 Aktien &middot; 30 Jahre &middot; 41.203 Beobachtungen",
   b_en="158 stocks &middot; 30 years &middot; 41,203 observations"),

 dict(k="bonds", chip="teilweise", datum="2026-09-22",
   href="/blog/anleihen-fruehindikator-aktienmarkt/",
   en_href="/en/blog/bonds-as-a-stock-market-indicator/",
   t_de="Anleihen als Fr&uuml;hindikator",
   t_en="Bonds as a leading indicator",
   f_de="Sagt eine Flucht in langlaufende Staatsanleihen die Aktienrendite der n&auml;chsten "
        "Wochen voraus?",
   f_en="Does a flight into long-dated government bonds predict equity returns over the "
        "weeks that follow?",
   e_de="Nur im Stress. Nach einem TLT-Anstieg ab 4,06&nbsp;% &uuml;ber zehn Handelstage stieg "
        "der S&amp;P&nbsp;500 in den folgenden zwei Wochen um <b>+2,09&nbsp;%</b> gegen "
        "+0,48&nbsp;% im Mittel (50 F&auml;lle, p 0,001&ndash;0,005). In ruhigen Phasen liegt "
        "der Effekt bei <b>exakt der Basisrate</b> (p&nbsp;=&nbsp;0,935), in unruhigen bei "
        "+3,65&nbsp;%. Und es ist ein <b>Erholungsmuster</b>: der S&amp;P&nbsp;500 war vorher "
        "im Median um 1,31&nbsp;% gefallen. Ohne diese H&auml;lfte liest man eine Prognose, wo "
        "eine Erholung steht.",
   e_en="Only under stress. After a TLT rise of 4.06&nbsp;% or more over ten trading days the "
        "S&amp;P&nbsp;500 gained <b>+2.09&nbsp;%</b> over the next two weeks against "
        "+0.48&nbsp;% on average (50 cases, p 0.001&ndash;0.005). In calm periods the effect "
        "sits at <b>exactly the base rate</b> (p&nbsp;=&nbsp;0.935); in turbulent ones at "
        "+3.65&nbsp;%. And it is a <b>recovery pattern</b>: the S&amp;P&nbsp;500 had fallen by "
        "a median 1.31&nbsp;% beforehand. Without that half you read a forecast where a "
        "recovery stands.",
   b_de="TLT gegen S&amp;P&nbsp;500 &middot; 50 F&auml;lle seit 2002",
   b_en="TLT against the S&amp;P&nbsp;500 &middot; 50 cases since 2002"),

 dict(k="matrix", chip="offen", datum="2026-09-22",
   href="/intermarket", en_href=None,
   t_de="Die Intermarket-Matrix",
   t_en="The intermarket matrix",
   f_de="Wenn sich ein Markt ungew&ouml;hnlich stark bewegt hat &mdash; bewegt sich danach ein "
        "anderer?",
   f_en="When one market has moved unusually hard, does another move afterwards?",
   e_de="Von <b>470</b> vorab festgelegten Paarungen h&auml;lt <b>keine einzige</b> der "
        "Korrektur f&uuml;r die Zahl der gestellten Fragen stand. Bei 470 Tests sind rund 24 "
        "Zufallstreffer zu erwarten &mdash; gefunden wurde keiner, der standh&auml;lt. Das ist "
        "das Ergebnis und kein Scheitern: die meisten Intermarket-Regeln verschwinden, sobald "
        "man dazusagt, wie viele Fragen man gestellt hat.",
   e_en="Of <b>470</b> pre-specified pairings, <b>not one</b> survives the correction for the "
        "number of questions asked. Across 470 tests some 24 chance hits are to be expected "
        "&mdash; none was found that holds. That is the result, not a failure: most "
        "intermarket rules dissolve as soon as you state how many questions you asked.",
   b_de="18 M&auml;rkte &middot; 556 auswertbare Zellen &middot; 470 in der Prim&auml;rfamilie",
   b_en="18 markets &middot; 556 usable cells &middot; 470 in the primary family"),

 dict(k="volsaison", chip="offen", datum="2026-09-22",
   href="/vola-saisonalitaet", en_href=None,
   t_de="Sind September und Oktober die Crash-Monate?",
   t_en="Are September and October the crash months?",
   f_de="Schwankt der S&amp;P&nbsp;500 in diesen beiden Monaten messbar st&auml;rker als im "
        "&uuml;brigen Jahr?",
   f_en="Does the S&amp;P&nbsp;500 swing measurably harder in those two months than in the "
        "rest of the year?",
   e_de="Nein. Die Volatilit&auml;t liegt beim <b>1,059-fachen</b> des &uuml;brigen Jahres, und "
        "das ist von Zufall nicht zu unterscheiden (<b>p&nbsp;=&nbsp;0,127</b>). Gerechnet am "
        "Index selbst ab 1957, nicht an einem ETF &mdash; dessen Dividendenbereinigung tr&auml;gt "
        "ausgerechnet in vier Kalendermonaten k&uuml;nstliche Spr&uuml;nge in die Reihe, zwei "
        "davon sind die getesteten. Die Erinnerung h&auml;ngt an einzelnen Oktobern, nicht am "
        "Durchschnitt des Monats.",
   e_en="No. Volatility sits at <b>1.059&times;</b> the rest of the year, and that cannot be "
        "told apart from chance (<b>p&nbsp;=&nbsp;0.127</b>). Computed on the index itself from "
        "1957, not on an ETF &mdash; its dividend adjustment puts artificial jumps into the "
        "series in exactly four calendar months, two of which are the ones under test. The "
        "memory hangs on individual Octobers, not on the month&#39;s average.",
   b_de="S&amp;P&nbsp;500 ab 1957 &middot; 836 Monate &middot; 1832 Zufallsziehungen",
   b_en="S&amp;P&nbsp;500 from 1957 &middot; 836 months &middot; 1,832 random draws"),

 dict(k="btc", chip="teilweise", datum="2026-09-21",
   href="/blog/laeuft-bitcoin-dem-aktienmarkt-voraus/",
   en_href="/en/blog/does-bitcoin-lead-the-stock-market/",
   t_de="L&auml;uft Bitcoin dem Aktienmarkt voraus?",
   t_en="Does bitcoin lead the stock market?",
   f_de="K&uuml;ndigt eine gro&szlig;e Krypto-Bewegung eine Aktienbewegung an?",
   f_en="Does a large move in crypto announce a move in equities?",
   e_de="Bei der viel zitierten <b>5-%-Schwelle</b> nicht &mdash; das ist bei Bitcoin der "
        "<b>Median</b> aller Zehn-Tage-Bewegungen, also die normalste Bewegung &uuml;berhaupt. "
        "Messbar wird es erst ab 10&nbsp;%, belastbar ab 20&nbsp;% (S&amp;P&nbsp;500 "
        "+2,29&nbsp;% nach drei Wochen, p&nbsp;=&nbsp;0,027). Bei Versatz null liegt die "
        "Korrelation bei +0,36 bis +0,45 &mdash; einen Tag versetzt ist sie verschwunden. Genau "
        "das macht sie als Prognose wertlos.",
   e_en="Not at the much-quoted <b>5&nbsp;% threshold</b> &mdash; for bitcoin that is the "
        "<b>median</b> of all ten-day moves, i.e. the most ordinary move there is. It becomes "
        "measurable only from 10&nbsp;% and dependable from 20&nbsp;% (S&amp;P&nbsp;500 "
        "+2.29&nbsp;% after three weeks, p&nbsp;=&nbsp;0.027). At zero lag the correlation runs "
        "+0.36 to +0.45 &mdash; shifted by one day it is gone. That is precisely what makes it "
        "worthless as a forecast.",
   b_de="Bitcoin und Ether gegen S&amp;P&nbsp;500 &middot; 12 Jahre &middot; 3020 Handelstage",
   b_en="Bitcoin and ether against the S&amp;P&nbsp;500 &middot; 12 years &middot; 3,020 "
        "trading days"),

 dict(k="em", chip="belegt", datum="2026-09-20",
   href="/skew", en_href=None,
   t_de="Der Expected Move ist systematisch zu weit",
   t_en="The expected move is systematically too wide",
   f_de="H&auml;lt das rechnerische 1-Sigma-Band aus den Optionspreisen, was es verspricht?",
   f_en="Does the calculated one-sigma band from option prices deliver what it promises?",
   e_de="Es h&auml;lt zu oft. In <b>84,3&nbsp;%</b> der F&auml;lle blieb der S&amp;P&nbsp;500 "
        "innerhalb des Bandes statt in den rechnerischen <b>68,3&nbsp;%</b> (Vertrauensbereich "
        "82,2 bis 86,3&nbsp;%, also klar daneben). Das Band ist damit systematisch zu weit "
        "&mdash; und genau diese L&uuml;cke ist die Volatilit&auml;ts-Risikopr&auml;mie, von der "
        "Optionsverk&auml;ufer leben.",
   e_en="It holds too often. In <b>84.3&nbsp;%</b> of cases the S&amp;P&nbsp;500 stayed inside "
        "the band instead of the calculated <b>68.3&nbsp;%</b> (confidence interval 82.2 to "
        "86.3&nbsp;%, so clearly outside it). The band is therefore systematically too wide "
        "&mdash; and that gap is exactly the volatility risk premium that option sellers live "
        "on.",
   b_de="VIX gegen S&amp;P&nbsp;500 &middot; 1990&ndash;2026",
   b_en="VIX against the S&amp;P&nbsp;500 &middot; 1990&ndash;2026"),

 dict(k="monthly10", chip="offen", datum="2026-09-17",
   href="/blog/monthly-10-strategie/", en_href=None,
   t_de="Die Monthly-10-Strategie",
   t_en="The monthly-10 strategy",
   f_de="Bringt es etwas, nur an zehn ausgew&auml;hlten Handelstagen im Monat investiert zu "
        "sein?",
   f_en="Is there anything to be gained from being invested on only ten selected trading days "
        "a month?",
   e_de="Nicht im Ertrag. &Uuml;ber 32 Jahre liefert die Regel <b>5,58&nbsp;%</b> pro Jahr gegen "
        "<b>10,71&nbsp;%</b> f&uuml;r Kaufen-und-Halten und lag nur in 10 von 32 Jahren vorn. "
        "Sie senkt daf&uuml;r die Schwankung (10,79 statt 18,84&nbsp;%) und den gr&ouml;ssten "
        "Verlust (&minus;41,0 statt &minus;55,2&nbsp;%). Pro Risikoeinheit steht 0,52 gegen "
        "0,57 &mdash; knapp hinten. Und der Ertrag kommt aus der <b>Monatsmitte</b>, nicht vom "
        "Monatswechsel, auf den sich die Regel beruft.",
   e_en="Not in return. Over 32 years the rule delivers <b>5.58&nbsp;%</b> a year against "
        "<b>10.71&nbsp;%</b> for buy and hold, and led in only 10 of 32 years. It does cut "
        "volatility (10.79 against 18.84&nbsp;%) and the largest loss (&minus;41.0 against "
        "&minus;55.2&nbsp;%). Per unit of risk it stands at 0.52 against 0.57 &mdash; narrowly "
        "behind. And the return comes from the <b>middle of the month</b>, not from the turn of "
        "the month the rule invokes.",
   b_de="S&amp;P&nbsp;500 &middot; 1994&ndash;2025 &middot; 32 Jahre",
   b_en="S&amp;P&nbsp;500 &middot; 1994&ndash;2025 &middot; 32 years"),

 dict(k="fomc", chip="beschreibend", datum="2026-09-03",
   href="/blog/pre-fomc-drift/", en_href="/en/blog/pre-fomc-drift/",
   t_de="Pre-FOMC-Drift",
   t_en="The pre-FOMC drift",
   f_de="Liefern die Stunden vor einer Fed-Entscheidung &uuml;berproportional Rendite?",
   f_en="Do the hours before a Fed decision deliver a disproportionate share of the return?",
   e_de="Der Tag <b>vor</b> der Entscheidung liefert im Schnitt <b>+0,131&nbsp;%</b>, der "
        "Entscheidungstag selbst <b>+0,202&nbsp;%</b> &mdash; gegen <b>+0,040&nbsp;%</b> an "
        "allen &uuml;brigen Tagen. Auf diese Tage entfallen rund 22&nbsp;% der aufsummierten "
        "Tagesrendite bei einem Anteil von nur 6,6&nbsp;% aller Handelstage. Das ist nicht die "
        "80-%-Zahl der Originalstudie, aber dieselbe Richtung.",
   e_en="The day <b>before</b> the decision returns <b>+0.131&nbsp;%</b> on average and the "
        "decision day itself <b>+0.202&nbsp;%</b> &mdash; against <b>+0.040&nbsp;%</b> on all "
        "other days. Those days account for roughly 22&nbsp;% of the summed daily return while "
        "making up just 6.6&nbsp;% of all trading days. That is not the 80&nbsp;% figure of the "
        "original study, but it points the same way.",
   b_de="S&amp;P&nbsp;500 &middot; 2006&ndash;2025",
   b_en="S&amp;P&nbsp;500 &middot; 2006&ndash;2025"),

 dict(k="index", chip="beschreibend", datum="2026-09-05",
   href="/index-effekt", en_href=None, en_seite=False,
   t_de="Der Index-Inklusions-Effekt",
   t_en="The index inclusion effect",
   f_de="Steigt eine Aktie, wenn ihre Aufnahme in den S&amp;P&nbsp;500 angek&uuml;ndigt wird?",
   f_en="Does a stock rise when its addition to the S&amp;P&nbsp;500 is announced?",
   e_de="Im Mittel ja. Zwanzig Handelstage nach der Ank&uuml;ndigung liegt der Kurs "
        "<b>+5,8&nbsp;%</b> h&ouml;her, der H&ouml;chststand um den Wirksamkeitstag bei "
        "<b>+7,8&nbsp;%</b>; 72&nbsp;% der F&auml;lle sind positiv. Mit 36 Ereignissen ist die "
        "Basis zu schmal f&uuml;r einen Signifikanztest &mdash; der gemittelte Pfad ist "
        "beschreibend.",
   e_en="On average, yes. Twenty trading days after the announcement the price stands "
        "<b>+5.8&nbsp;%</b> higher, with a peak of <b>+7.8&nbsp;%</b> around the effective "
        "date; 72&nbsp;% of cases are positive. With 36 events the base is too narrow for a "
        "significance test &mdash; the averaged path is descriptive.",
   b_de="36 Aufnahmen in den S&amp;P&nbsp;500",
   b_en="36 additions to the S&amp;P&nbsp;500"),

 dict(k="daxsep", chip="belegt", datum="2026-08-24",
   href="/blog/dax-september-signifikanz/", en_href=None,
   t_de="Der DAX im September",
   t_en="The DAX in September",
   f_de="Ist die Septemberschw&auml;che des DAX ein echter Effekt oder eine Erz&auml;hlung?",
   f_en="Is the DAX&#39;s September weakness a real effect or a story?",
   e_de="Ein echter, aber kleiner. Der September liegt im Mittel bei <b>&minus;1,55&nbsp;%</b> "
        "gegen &minus;0,27&nbsp;% f&uuml;r einen durchschnittlichen Monat, und der Unterschied "
        "&uuml;bersteht den Test (<b>p&nbsp;=&nbsp;0,0241</b>). Die Effektst&auml;rke ist dabei "
        "gering &mdash; ein signifikanter Effekt ist nicht dasselbe wie ein gro&szlig;er.",
   e_en="A real one, but small. September averages <b>&minus;1.55&nbsp;%</b> against "
        "&minus;0.27&nbsp;% for an average month, and the difference survives the test "
        "(<b>p&nbsp;=&nbsp;0.0241</b>). The effect size is modest &mdash; a significant effect "
        "is not the same thing as a large one.",
   b_de="DAX &middot; Monatsrenditen seit 1988",
   b_en="DAX &middot; monthly returns since 1988"),

 dict(k="midterm", chip="beschreibend", datum="2026-09-02",
   href="/blog/zwischenwahljahr-2026-erholung-praesidentenzyklus/", en_href=None,
   t_de="Das Zwischenwahljahr im Pr&auml;sidentenzyklus",
   t_en="The midterm year in the presidential cycle",
   f_de="Unterscheidet sich das zweite Jahr einer US-Amtszeit von den drei anderen?",
   f_en="Does the second year of a US term differ from the other three?",
   e_de="Im Muster ja. Zwischenwahljahre tragen den <b>tiefsten R&uuml;ckgang</b> der vier "
        "Jahre, und auf diesen Tiefpunkt folgt im Mittel eine Erholung von <b>+31&nbsp;%</b>. "
        "Mit rund zwanzig Zyklen seit 1950 ist die Zahl der Beobachtungen klein &mdash; das ist "
        "ein beschreibendes Muster und kein getesteter Effekt.",
   e_en="In pattern, yes. Midterm years carry the <b>deepest drawdown</b> of the four, and that "
        "low is on average followed by a recovery of <b>+31&nbsp;%</b>. With roughly twenty "
        "cycles since 1950 the number of observations is small &mdash; this is a descriptive "
        "pattern, not a tested effect.",
   b_de="S&amp;P&nbsp;500 &middot; Pr&auml;sidentenzyklen seit 1950",
   b_en="S&amp;P&nbsp;500 &middot; presidential cycles since 1950"),
]

CHIP_DE = {"belegt": "belegt", "teilweise": "eingeschr&auml;nkt",
           "offen": "nicht belegt", "beschreibend": "beschreibend"}
CHIP_EN = {"belegt": "supported", "teilweise": "qualified",
           "offen": "not supported", "beschreibend": "descriptive"}

TEXTE = {
 "st.h1": ("<b>Studien</b> &mdash; was wir gemessen haben",
           "<b>Studies</b> &mdash; what we measured"),
 "st.caption": (
   "Jede Auswertung hier beantwortet eine Frage, die <b>vor</b> der Rechnung feststand. "
   "Sie steht auf dieser Seite unabh&auml;ngig davon, ob die Antwort ja lautet: ein Test, "
   "dessen Ergebnis nur dann ver&ouml;ffentlicht wird, wenn es gef&auml;llt, ist keiner. "
   "Vier der elf Fragen sind mit Nein beantwortet oder ohne Befund geblieben.",
   "Every analysis here answers a question that was fixed <b>before</b> the computation. It "
   "appears on this page regardless of whether the answer is yes: a test whose result is "
   "published only when it pleases is not a test. Four of the eleven questions came back as "
   "no or produced no finding."),
 "st.disclaimer": (
   "<b>Wichtig:</b> Auswertungen historischer Kursdaten, <b>keine Prognose und keine "
   "Anlageberatung</b>. Ein signifikanter Effekt ist nicht dasselbe wie ein gro&szlig;er, und "
   "vergangene Muster garantieren keine k&uuml;nftigen Ergebnisse.",
   "<b>Important:</b> analyses of historical price data, <b>not a forecast and not investment "
   "advice</b>. A significant effect is not the same thing as a large one, and past patterns "
   "guarantee no future results."),
 "st.tally": ("11 Fragen", "11 questions"),
 "st.tally_sub": ("gestellt und ausgerechnet", "asked and computed"),
 "st.read": ("Ansehen", "Read it"),
 # Der Link-Teil ist asymmetrisch, und zwar absichtlich. rewrite_body_links in
 # build_en.py ueberspringt /blog/ — nicht jeder Post hat eine EN-Fassung —,
 # also bliebe ein Blog-Link auf der EN-Seite sonst deutsch. Deshalb:
 #   st.read_alt     zweiter Anker. Auf DE "English version", auf EN "Read it";
 #                   der deutsche Anker daneben traegt data-en-hide und faellt
 #                   im EN-Build weg, dieser wird dort also zum Hauptlink.
 #   st.read_deonly  fuer alles ohne EN-Fassung. Ein englischer Leser soll VOR
 #                   dem Klick wissen, dass er auf Deutsch landet.
 "st.read_alt": ("English version", "Read it"),
 "st.read_deonly": ("Ansehen", "Read it (German)"),

 "st.method_h": ("Methodik &mdash; was die vier Kennzeichen bedeuten",
                 "Methodology &mdash; what the four labels mean"),
 "st.method_body": (
   "<h4>Die vier Kennzeichen</h4>"
   "<p><b>Belegt</b> hei&szlig;t: die Frage war vorab festgelegt, der Unterschied ist "
   "gemessen, und er &uuml;bersteht einen Signifikanztest. <b>Eingeschr&auml;nkt</b> hei&szlig;t: "
   "der Effekt existiert, aber nur unter einer Bedingung, die dazugeh&ouml;rt &mdash; in "
   "unruhigen Marktphasen etwa, oder erst ab einer bestimmten Gr&ouml;ssenordnung. Wer die "
   "Bedingung wegl&auml;sst, zitiert etwas anderes als das, was gemessen wurde. <b>Nicht "
   "belegt</b> hei&szlig;t: gerechnet, und der Unterschied ist von Zufall nicht zu "
   "unterscheiden. <b>Beschreibend</b> hei&szlig;t: das Muster ist da, aber die Zahl der "
   "Beobachtungen tr&auml;gt keinen Test &mdash; bei 36 Ereignissen ist ein p-Wert eine "
   "Scheingenauigkeit.</p>"

   "<h4>Warum die Nullergebnisse hier stehen</h4>"
   "<p>Wer zehn Fragen stellt und nur die eine ver&ouml;ffentlicht, die ein Ergebnis hatte, "
   "hat nichts gemessen, sondern ausgew&auml;hlt. Bei 470 Paarungen der Intermarket-Matrix "
   "sind rund 24 Zufallstreffer zu erwarten &mdash; wer sie einzeln zeigt, zeigt Rauschen mit "
   "p-Wert. Deshalb steht die Zahl der gestellten Fragen bei jeder Auswertung dabei, und "
   "deshalb bleiben die Nullergebnisse stehen.</p>"

   "<h4>Was nicht hier steht</h4>"
   "<p>Auswertungen, deren Datenbasis zu schmal ist, werden nicht ver&ouml;ffentlicht &mdash; "
   "auch dann nicht, wenn die Zahlen gerade gut aussehen. Die Renditen der Kongress-Abgeordneten "
   "etwa liegen gerechnet vor, st&uuml;tzen sich aber bisher auf zu wenige Ereignisse und zu "
   "wenige Personen; daraus w&uuml;rde jede Aussage &uuml;ber „die Politiker“ eine Aussage "
   "&uuml;ber zwei von ihnen.</p>"

   "<h4>Wiederholbarkeit</h4>"
   "<p>Alle Auswertungen laufen auf derselben Kursdatenbank wie der Rest der Seite. Die "
   "Hypothese, der Zeitraum und die Schwelle stehen jeweils im Text &mdash; nicht, weil das "
   "sch&ouml;n klingt, sondern weil eine Zahl ohne diese drei Angaben nicht nachpr&uuml;fbar "
   "ist.</p>",

   "<h4>The four labels</h4>"
   "<p><b>Supported</b> means the question was fixed in advance, the difference is measured, "
   "and it survives a significance test. <b>Qualified</b> means the effect exists, but only "
   "under a condition that belongs with it &mdash; in turbulent markets, say, or only above a "
   "certain magnitude. Drop the condition and you are quoting something other than what was "
   "measured. <b>Not supported</b> means it was computed and the difference cannot be told "
   "apart from chance. <b>Descriptive</b> means the pattern is there but the number of "
   "observations carries no test &mdash; at 36 events a p-value is false precision.</p>"

   "<h4>Why the null results are here</h4>"
   "<p>Asking ten questions and publishing only the one that produced an answer is not "
   "measuring, it is selecting. Across the 470 pairings of the intermarket matrix some 24 "
   "chance hits are to be expected &mdash; showing them one at a time means showing noise with "
   "a p-value attached. That is why the number of questions asked appears with every analysis, "
   "and why the null results stay up.</p>"

   "<h4>What is not here</h4>"
   "<p>Analyses whose data base is too thin are not published &mdash; not even when the figures "
   "happen to look good. The returns of members of Congress, for instance, have been computed, "
   "but so far rest on too few events and too few people; any statement about &lsquo;the "
   "politicians&rsquo; would be a statement about two of them.</p>"

   "<h4>Repeatability</h4>"
   "<p>Every analysis runs on the same price database as the rest of the site. The hypothesis, "
   "the period and the threshold appear in each write-up &mdash; not because it sounds good, "
   "but because a figure without those three is not checkable.</p>"),

 "st.faq_h": ("H&auml;ufige Fragen", "Frequently asked questions"),
 "st.faq1_q": ("Warum ver&ouml;ffentlicht ihr Auswertungen, die nichts gefunden haben?",
               "Why publish analyses that found nothing?"),
 "st.faq1_a": (
   "Weil sie genauso viel wert sind. Die viel zitierte Regel, eine 5-Prozent-Bewegung bei "
   "Bitcoin k&uuml;ndige etwas an, f&auml;llt erst auf, wenn jemand nachrechnet, dass "
   "5&nbsp;Prozent bei Bitcoin der <i>Median</i> aller Zehn-Tage-Bewegungen sind. Ein "
   "Nullergebnis nimmt eine Regel aus dem Verkehr &mdash; das ist ein Ergebnis.",
   "Because they are worth just as much. The much-quoted rule that a 5&nbsp;% move in bitcoin "
   "announces something only comes apart when someone works out that 5&nbsp;% is the "
   "<i>median</i> of all ten-day moves in bitcoin. A null result takes a rule out of "
   "circulation &mdash; that is a result."),
 "st.faq2_q": ("Was hei&szlig;t „vorab festgelegt“?",
               "What does &lsquo;fixed in advance&rsquo; mean?"),
 "st.faq2_a": (
   "Dass Ticker, Zeitraum, Schwelle und Messgr&ouml;sse feststanden, bevor gerechnet wurde. "
   "Wer erst rechnet und dann die Variante aussucht, die am besten aussieht, findet immer "
   "etwas: bei genug Varianten ist ein auff&auml;lliges Ergebnis garantiert. Bei der "
   "Volatilit&auml;ts-Saisonalit&auml;t etwa waren <i>ein</i> Ticker und <i>ein</i> Monatspaar "
   "festgelegt &mdash; sonst h&auml;tte man zw&ouml;lf Monate mal mehrere hundert Titel zur "
   "Auswahl gehabt.",
   "That the ticker, the period, the threshold and the measure were set before anything was "
   "computed. Compute first and then pick the variant that looks best, and you always find "
   "something: with enough variants a striking result is guaranteed. For the volatility "
   "seasonality study, <i>one</i> ticker and <i>one</i> pair of months were fixed &mdash; "
   "otherwise there would have been twelve months times several hundred names to choose from."),
 "st.faq3_q": ("Kann ich diese Effekte handeln?",
               "Can I trade these effects?"),
 "st.faq3_a": (
   "Diese Seite gibt keine Anlageberatung und spricht keine Empfehlung aus. Zwei Dinge sind "
   "beim Lesen wichtig: ein signifikanter Effekt kann winzig sein &mdash; 0,35 Prozentpunkte "
   "beim Pinning &uuml;berleben keine Geb&uuml;hren &mdash; und ein Effekt, der an eine "
   "Bedingung gebunden ist, verschwindet ohne sie. Der Anleihen-Befund gilt in unruhigen "
   "Phasen; in ruhigen liegt er exakt auf der Basisrate.",
   "This page gives no investment advice and makes no recommendation. Two things matter when "
   "reading it: a significant effect can be tiny &mdash; the 0.35 percentage points of the "
   "pinning study survive no fees &mdash; and an effect tied to a condition disappears without "
   "it. The bond finding holds in turbulent periods; in calm ones it sits exactly on the base "
   "rate."),
 "st.faq4_q": ("Wie oft kommt etwas Neues dazu?",
               "How often is something new added?"),
 "st.faq4_a": (
   "Unregelm&auml;&szlig;ig. Eine Auswertung entsteht, wenn eine Frage konkret genug ist, um "
   "sie falsifizierbar zu stellen, und die Datenbasis sie tr&auml;gt. Beides zusammen kommt "
   "seltener vor, als die Menge der kursierenden B&ouml;rsenregeln vermuten l&auml;sst.",
   "Irregularly. An analysis comes about when a question is concrete enough to be put in a "
   "falsifiable form and the data base can carry it. The two together occur less often than the "
   "volume of market rules in circulation would suggest."),
}

KOPF = """<!DOCTYPE html>
<html lang="de">
<head>
  <!-- SA_META_V5 -->
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Studien &mdash; elf gemessene B&ouml;rsenregeln, vier davon widerlegt | SeasonAlpha</title>
  <meta name="description" content="Elf Auswertungen historischer Kursdaten mit Frage, Ergebnis und Datenbasis — Pinning am Verfallstag, Anleihen als Frühindikator, Volatilitäts-Saisonalität. Die Nullergebnisse stehen mit dabei.">
  <meta name="author" content="SeasonAlpha">
  <meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large">
  <meta name="theme-color" content="#000000">
  <link rel="canonical" href="https://seasonalpha.ai/studien">
  <link rel="alternate" hreflang="de" href="https://seasonalpha.ai/studien">
  <link rel="alternate" hreflang="en" href="https://seasonalpha.ai/en/studien">
  <link rel="alternate" hreflang="x-default" href="https://seasonalpha.ai/studien">

  <meta property="og:type" content="website">
  <meta property="og:url" content="https://seasonalpha.ai/studien">
  <meta property="og:title" content="Studien &mdash; elf gemessene B&ouml;rsenregeln, vier davon widerlegt | SeasonAlpha">
  <meta property="og:description" content="Frage, Ergebnis und Datenbasis für elf Auswertungen historischer Kursdaten. Die Nullergebnisse stehen mit dabei.">
  <meta property="og:image" content="https://seasonalpha.ai/landing/assets/images/og-image.png">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:site_name" content="SeasonAlpha">
  <meta property="og:locale" content="de_DE">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:site" content="@SeasonAlph4882">
  <meta name="twitter:title" content="Studien | SeasonAlpha">
  <meta name="twitter:description" content="Elf gemessene Börsenregeln, vier davon widerlegt.">
  <meta name="twitter:image" content="https://seasonalpha.ai/landing/assets/images/og-image.png">

  <link rel="icon" type="image/svg+xml" href="/landing/assets/images/favicon.svg">
  <link rel="icon" type="image/png" sizes="32x32" href="/landing/assets/images/favicon-32x32.png">
  <link rel="apple-touch-icon" sizes="180x180" href="/landing/assets/images/apple-touch-icon.png">

__LD__

  <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&family=Sora:wght@600;800&family=JetBrains+Mono:wght@400&display=swap" rel="stylesheet" media="print" onload="this.media='all'"><noscript><link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&family=Sora:wght@600;800&family=JetBrains+Mono:wght@400&display=swap" rel="stylesheet"></noscript>
  <link rel="stylesheet" href="/landing/css/app.css">
  <style>
    .page-title{font-family:var(--f-d);font-size:1.5rem;font-weight:800;color:var(--text);margin-bottom:.25rem}
    .page-title b{color:var(--accent)}
    .page-caption{color:var(--muted);font-size:.8125rem;margin-bottom:1rem;line-height:1.55;max-width:70ch}
    .disc{background:rgba(232,168,32,.07);border:1px solid rgba(232,168,32,.18);border-radius:10px;padding:.6rem 1rem;font-size:.78rem;color:var(--muted);margin-bottom:1.5rem;line-height:1.5}
    .tally{display:flex;flex-wrap:wrap;gap:.5rem;align-items:baseline;margin:0 0 1.4rem}
    .tally .n{font-family:var(--f-d);font-weight:800;font-size:1.35rem;color:var(--accent)}
    .tally .s{color:var(--dim);font-size:.78rem}
    .tally .bar{display:flex;flex-wrap:wrap;gap:.35rem;margin-left:.4rem}
    .st-card{background:var(--card);border:1px solid var(--border);border-radius:14px;padding:1rem 1.1rem;margin-bottom:.85rem}
    .st-card h3{font-family:var(--f-d);font-size:1.02rem;font-weight:700;color:var(--text);margin:.45rem 0 .3rem;line-height:1.3}
    .st-q{color:var(--dim);font-size:.8rem;line-height:1.5;margin:0 0 .5rem;font-style:italic}
    .st-e{color:var(--muted);font-size:.83rem;line-height:1.65;margin:0 0 .6rem}
    .st-e b{color:var(--text)}
    .st-foot{display:flex;flex-wrap:wrap;gap:.5rem 1rem;align-items:center;font-size:.72rem;color:var(--dim);border-top:1px solid var(--border);padding-top:.55rem}
    .st-foot a{color:var(--accent);text-decoration:none;font-weight:600}
    .st-foot a:hover{text-decoration:underline}
    .chip{display:inline-block;font-size:.68rem;font-weight:700;letter-spacing:.04em;text-transform:uppercase;padding:.15rem .5rem;border-radius:999px;border:1px solid}
    .chip.belegt{color:#e8a820;border-color:rgba(232,168,32,.45);background:rgba(232,168,32,.12)}
    .chip.teilweise{color:#c9a96a;border-color:rgba(201,169,106,.35);background:rgba(201,169,106,.08)}
    .chip.offen{color:#8a8270;border-color:rgba(138,130,112,.35);background:rgba(138,130,112,.08)}
    .chip.beschreibend{color:#8a8270;border-color:rgba(138,130,112,.35);background:rgba(138,130,112,.08)}
    .sec-h{font-family:var(--f-d);font-size:1.05rem;font-weight:700;color:var(--text);margin:2rem 0 .7rem}
    details.method,details.faq{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:.7rem 1rem;margin-bottom:.6rem}
    details.method summary,details.faq summary{cursor:pointer;font-weight:600;color:var(--text);font-size:.86rem}
    details.method .body{color:var(--muted);font-size:.82rem;line-height:1.7;margin-top:.6rem}
    details.method h4{color:var(--text);font-size:.85rem;margin:.9rem 0 .3rem}
    details.method h4:first-child{margin-top:.2rem}
    details.faq p{color:var(--muted);font-size:.82rem;line-height:1.65;margin:.5rem 0 0}
  </style>
</head>
<body>
  <div id="nav-container"></div>

  <main class="container" style="padding-top:1.5rem">
    <h1 class="page-title" data-i18n-html="st.h1">__H1__</h1>
    <p class="page-caption" data-i18n-html="st.caption">__CAP__</p>
    <div class="disc" data-i18n-html="st.disclaimer">__DISC__</div>

    <div class="tally">
      <span class="n" data-i18n="st.tally">__TALLY__</span>
      <span class="s" data-i18n="st.tally_sub">__TALLYSUB__</span>
      <span class="bar">__BAR__</span>
    </div>

__KARTEN__
    <h2 class="sec-h" data-i18n="st.method_h">__METHH__</h2>
    <details class="method">
      <summary data-i18n="st.method_h">__METHH__</summary>
      <div class="body" data-i18n-html="st.method_body">__METHB__</div>
    </details>

    <h2 class="sec-h" data-i18n="st.faq_h">__FAQH__</h2>
__FAQS__
    <div id="footer-container"></div>
  </main>

  <script>window.__SA_SB_URL='%%SUPABASE_URL%%';window.__SA_SB_KEY='%%SUPABASE_ANON_KEY%%';</script>
  <script src="/landing/js/i18n.js"></script>
  <script src="/landing/js/app.js"></script>
  <script>
  (function () {
    'use strict';
    loadComponent('nav-container', '/landing/components/nav.html');
    loadComponent('footer-container', '/landing/components/footer.html');
  })();
  </script>
</body>
</html>
"""


def karte(s: str) -> str:
    """Eine Studien-Karte.

    Drei Faelle, weil der EN-Build Seiten- und Blog-Links verschieden behandelt:
      Blog mit EN-Fassung   deutscher Anker mit data-en-hide plus englischer
                            Anker; im EN-Build bleibt nur der englische.
      Ohne EN-Fassung       ein Anker, und das Etikett sagt Deutsch an.
      Seite mit EN-Fassung  ein Anker; das /en davor setzt der Build selbst.
    """
    if s["en_href"]:
        assert s["href"].startswith("/blog/"), \
            "Seiten brauchen kein en_href — /en setzt rewrite_body_links"
        links = ('<a href="%s" data-en-hide data-i18n="st.read">Ansehen</a>\n'
                 '        <a href="%s" hreflang="en" data-i18n="st.read_alt">'
                 'English version</a>' % (s["href"], s["en_href"]))
    elif s.get("en_seite", True) and not s["href"].startswith("/blog/"):
        links = '<a href="%s" data-i18n="st.read">Ansehen</a>' % s["href"]
    else:
        links = '<a href="%s" data-i18n="st.read_deonly">Ansehen</a>' % s["href"]
    return (
        '    <article class="st-card">\n'
        '      <span class="chip %(chip)s" data-i18n="st.chip_%(chip)s">%(chipde)s</span>\n'
        '      <h3 data-i18n-html="st.%(k)s_t">%(t)s</h3>\n'
        '      <p class="st-q" data-i18n-html="st.%(k)s_f">%(f)s</p>\n'
        '      <p class="st-e" data-i18n-html="st.%(k)s_e">%(e)s</p>\n'
        '      <div class="st-foot">\n'
        '        <span data-i18n-html="st.%(k)s_b">%(b)s</span>\n'
        '        <span>%(datum)s</span>\n'
        '        %(links)s\n'
        '      </div>\n'
        '    </article>\n'
    ) % dict(chip=s["chip"], chipde=CHIP_DE[s["chip"]], k=s["k"], t=s["t_de"],
             f=s["f_de"], e=s["e_de"], b=s["b_de"], datum=s["datum"],
             links=links)


def seite() -> str:
    """Baut das HTML und gibt es zurueck, ohne zu schreiben."""
    zaehl = {}
    for s in S:
        zaehl[s["chip"]] = zaehl.get(s["chip"], 0) + 1
    assert sum(zaehl.values()) == len(S) == 11, zaehl
    bar = " ".join(
        '<span class="chip %s" data-i18n-html="st.bar_%s">%d&nbsp;%s</span>'
        % (c, c, zaehl[c], CHIP_DE[c])
        for c in ["belegt", "teilweise", "offen", "beschreibend"] if c in zaehl)

    ld_web = {"@context": "https://schema.org", "@type": "CollectionPage",
              "name": "Studien", "url": "https://seasonalpha.ai/studien",
              "description": ("Elf Auswertungen historischer Kursdaten mit Frage, "
                              "Ergebnis und Datenbasis. Die Nullergebnisse stehen "
                              "mit dabei."),
              "isPartOf": {"@type": "WebSite", "name": "SeasonAlpha",
                           "url": "https://seasonalpha.ai"},
              "publisher": {"@type": "Organization", "name": "SeasonAlpha",
                            "url": "https://seasonalpha.ai",
                            "logo": {"@type": "ImageObject",
                                     "url": "https://seasonalpha.ai/landing/assets/images/og-image.png"}}}
    ld_bc = {"@context": "https://schema.org", "@type": "BreadcrumbList",
             "itemListElement": [
                 {"@type": "ListItem", "position": 1, "name": "Home",
                  "item": "https://seasonalpha.ai/"},
                 {"@type": "ListItem", "position": 2, "name": "Studien",
                  "item": "https://seasonalpha.ai/studien"}]}

    def entschaerf(x: str) -> str:
        """HTML-Entities und Auszeichnung raus — JSON-LD will reinen Text."""
        for a, b in [("&mdash;", "—"), ("&ndash;", "–"), ("&nbsp;", " "),
                     ("&middot;", "·"), ("&minus;", "−"), ("&amp;", "&"),
                     ("&auml;", "ä"), ("&ouml;", "ö"), ("&uuml;", "ü"),
                     ("&szlig;", "ß"), ("&Uuml;", "Ü"), ("&times;", "×"),
                     ("&lsquo;", "‚"), ("&rsquo;", "'"), ("&#39;", "'"),
                     ("<b>", ""), ("</b>", ""), ("<i>", ""), ("</i>", "")]:
            x = x.replace(a, b)
        return x

    # Ein ItemList-Block, damit jede Studie als eigener Eintrag lesbar ist.
    ld_list = {"@context": "https://schema.org", "@type": "ItemList",
               "itemListOrder": "https://schema.org/ItemListOrderDescending",
               "numberOfItems": len(S),
               "itemListElement": [
                   {"@type": "ListItem", "position": i + 1,
                    "name": entschaerf(s["t_de"]),
                    "url": "https://seasonalpha.ai" + s["href"]}
                   for i, s in enumerate(S)]}

    faq_paare = [("st.faq%d_q" % i, "st.faq%d_a" % i) for i in (1, 2, 3, 4)]
    ld_faq = {"@context": "https://schema.org", "@type": "FAQPage",
              "mainEntity": [
                  {"@type": "Question", "name": entschaerf(TEXTE[q][0]),
                   "acceptedAnswer": {"@type": "Answer",
                                      "text": entschaerf(TEXTE[a][0])}}
                  for q, a in faq_paare]}

    ld = "\n".join(
        '  <script type="application/ld+json">%s</script>' % json.dumps(x, ensure_ascii=False)
        for x in (ld_web, ld_bc, ld_list, ld_faq))

    faqs = "".join(
        '    <details class="faq"%s>\n'
        '      <summary data-i18n="st.faq%d_q">%s</summary>\n'
        '      <p data-i18n-html="st.faq%d_a">%s</p>\n'
        '    </details>\n'
        % (" open" if i == 1 else "", i, TEXTE["st.faq%d_q" % i][0],
           i, TEXTE["st.faq%d_a" % i][0])
        for i in (1, 2, 3, 4))

    html = (KOPF
            .replace("__LD__", ld)
            .replace("__H1__", TEXTE["st.h1"][0])
            .replace("__CAP__", TEXTE["st.caption"][0])
            .replace("__DISC__", TEXTE["st.disclaimer"][0])
            .replace("__TALLY__", TEXTE["st.tally"][0])
            .replace("__TALLYSUB__", TEXTE["st.tally_sub"][0])
            .replace("__BAR__", bar)
            .replace("__KARTEN__", "".join(karte(s) for s in S) + "\n")
            .replace("__METHH__", TEXTE["st.method_h"][0])
            .replace("__METHB__", TEXTE["st.method_body"][0])
            .replace("__FAQH__", TEXTE["st.faq_h"][0])
            .replace("__FAQS__", faqs))
    assert "__" not in html.replace("window.__SA_SB", "").replace("__SA_SB", ""), \
        "unersetzter Platzhalter"
    return html


def sprachdateien() -> tuple:
    """Die Schluessel fuer en.json und de.json, ohne zu schreiben."""
    zaehl = {}
    for s in S:
        zaehl[s["chip"]] = zaehl.get(s["chip"], 0) + 1
    en = {k: v[1] for k, v in TEXTE.items()}
    en["nav.studien"] = "Studies"
    for c in CHIP_EN:
        en["st.chip_" + c] = CHIP_EN[c]
        if c in zaehl:
            en["st.bar_" + c] = "%d&nbsp;%s" % (zaehl[c], CHIP_EN[c])
    for s in S:
        en["st." + s["k"] + "_t"] = s["t_en"]
        en["st." + s["k"] + "_f"] = s["f_en"]
        en["st." + s["k"] + "_e"] = s["e_en"]
        en["st." + s["k"] + "_b"] = s["b_en"]

    return en, {"nav.studien": "Studien"}


def main() -> None:
    io.open("landing/pages/studien.html", "w", encoding="utf-8",
            newline="").write(seite())
    print("%-34s %d Karten" % ("landing/pages/studien.html", len(S)))
    en, de = sprachdateien()

    p = "landing/i18n/en.json"
    roh = io.open(p, encoding="utf-8").read()
    vorhanden = json.loads(roh)
    fehlend = {k: v for k, v in en.items() if k not in vorhanden}
    if fehlend:
        kopf = roh.rstrip()
        assert kopf.endswith("}")
        schn = ",\n".join("  %s: %s" % (json.dumps(k, ensure_ascii=False),
                                        json.dumps(v, ensure_ascii=False))
                          for k, v in fehlend.items())
        raus = kopf[:-1].rstrip() + ",\n\n" + schn + "\n}"
        k = json.loads(raus)
        for kk, vv in en.items():
            assert k[kk] == vv, kk
        for kk, vv in vorhanden.items():
            assert k[kk] == vv, "Bestandskey %s geaendert" % kk
        io.open(p, "w", encoding="utf-8", newline="").write(raus)
    print("%-34s %d neu" % (p, len(fehlend)))

    p = "landing/i18n/de.json"
    roh = io.open(p, encoding="utf-8").read()
    vorhanden = json.loads(roh)
    fehlend = {k: v for k, v in de.items() if k not in vorhanden}
    if fehlend:
        kopf = roh.rstrip()
        schn = ",\n".join("  %s: %s" % (json.dumps(k, ensure_ascii=False),
                                        json.dumps(v, ensure_ascii=False))
                          for k, v in fehlend.items())
        raus = kopf[:-1].rstrip() + ",\n\n" + schn + "\n}"
        json.loads(raus)
        io.open(p, "w", encoding="utf-8", newline="").write(raus)
    print("%-34s %d neu" % (p, len(fehlend)))


if __name__ == "__main__":
    main()
