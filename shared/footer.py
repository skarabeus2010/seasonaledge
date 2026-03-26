"""
SeasonAlpha — Footer Component
===============================
Zentraler Footer fuer alle Pages: Imprint, Datenschutz, Risk Disclosure.
"""

import streamlit as st


def render_footer():
    """Rendert den SeasonAlpha Footer mit Links und Risk Disclosure."""
    st.markdown("---")
    st.markdown(
        """
        <style>
        .se-footer {
            margin-top: 40px;
            padding: 24px 0 12px 0;
            text-align: center;
        }
        .se-footer-links {
            display: flex;
            justify-content: center;
            gap: 24px;
            margin-bottom: 16px;
        }
        .se-footer-links a {
            color: #8899aa;
            text-decoration: none;
            font-size: 13px;
            font-weight: 500;
            transition: color 0.2s;
        }
        .se-footer-links a:hover {
            color: #00CED1;
        }
        .se-footer-brand {
            color: #556677;
            font-size: 12px;
            margin-bottom: 8px;
        }
        </style>

        <div class="se-footer">
            <div class="se-footer-links">
                <a href="#imprint" onclick="document.getElementById('se-risk-toggle').style.display='none'; return false;">Imprint</a>
                <span style="color:#334455;">|</span>
                <a href="#datenschutz" onclick="return false;">Datenschutz</a>
                <span style="color:#334455;">|</span>
                <a href="javascript:void(0)" onclick="var el=document.getElementById('se-risk-toggle'); el.style.display = el.style.display==='none' ? 'block' : 'none';">Risk Disclosure</a>
            </div>
            <div class="se-footer-brand">
                &copy; 2026 SeasonAlpha. All rights reserved.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("Risk Disclosure", expanded=False):
        st.markdown(
            "<div style='color:#8899aa; font-size:11px; line-height:1.7; text-align:justify;'>"
            "<b style='color:#aabbcc;'>Risikohinweis (DE)</b><br>"
            "Vergangene Ergebnisse sowie fruehere saisonale Muster bieten keinerlei Anhaltspunkt "
            "fuer kuenftige Ertraege, insbesondere nicht fuer zukuenftige Markttrends. SeasonAlpha "
            "empfiehlt noch billigt weder ein bestimmtes Finanzinstrument, eine Gruppe von "
            "Wertpapieren, einen Branchensegment, ein Analyseintervall noch eine bestimmte Idee, "
            "Herangehensweise, Strategie oder Haltung und erbringt weder Beratungs- noch Brokerage- "
            "noch Asset-Management-Dienstleistungen. SeasonAlpha schliesst hiermit jegliche "
            "ausdrueckliche oder implizite Handelsempfehlung aus, insbesondere jegliches Versprechen, "
            "jegliche Andeutung oder Garantie, dass Gewinne erzielt und Verluste ausgeschlossen "
            "werden; im Zweifelsfall sind diese Bestimmungen jedoch weit auszulegen. Saemtliche von "
            "SeasonAlpha oder auf dieser Website bzw. auf einem anderen Datentraeger bereitgestellten "
            "Informationen duerfen nicht als irgendeine Form von Garantie, Gewaehrleistung oder "
            "Zusicherung ausgelegt werden, insbesondere nicht als solche, wie sie in einem Prospekt "
            "dargelegt sind. Jeder Nutzer traegt allein die Verantwortung fuer die Ergebnisse oder "
            "die Handelsstrategie, die er erstellt, entwickelt oder anwendet. Indikatoren, "
            "Handelsstrategien und Funktionen, die von SeasonAlpha oder auf dieser Website bzw. auf "
            "einem anderen Datentraeger zur Verfuegung gestellt werden, koennen logische oder "
            "sonstige Fehler enthalten, die zu unerwarteten Ergebnissen, fehlerhaften Handelssignalen "
            "und/oder erheblichen Verlusten fuehren koennen. SeasonAlpha gewaehrleistet oder "
            "garantiert weder die Genauigkeit, Vollstaendigkeit, Qualitaet, Angemessenheit noch den "
            "Inhalt der von ihm oder auf dieser Website bzw. auf einem anderen Datentraeger "
            "bereitgestellten Informationen. Jeder Nutzer ist verpflichtet, alle anwendbaren "
            "Kapitalmarktregeln der jeweiligen Rechtsordnung einzuhalten. Alle auf dieser Website "
            "oder auf einem anderen Datentraeger veroeffentlichten Inhalte und Bilder sind "
            "urheberrechtlich geschuetzt. Jegliche Vervielfaeltigung, Bearbeitung, Verbreitung oder "
            "sonstige Form der Nutzung, die den Rahmen des Urheberrechtsgesetzes ueberschreitet, "
            "bedarf der vorherigen schriftlichen Zustimmung des jeweiligen Autors bzw. der jeweiligen "
            "Autoren. Der Handel mit Futures und Devisen birgt erhebliche Risiken und ist nicht fuer "
            "jeden Anleger geeignet. Ein Anleger koennte potenziell den gesamten oder sogar mehr als "
            "den anfaenglichen Einsatz verlieren. Risikokapital ist Geld, das verloren werden kann, "
            "ohne die finanzielle Sicherheit oder den Lebensstil einer Person zu gefaehrden. Nur "
            "Risikokapital sollte fuer den Handel verwendet werden, und nur Personen mit "
            "ausreichendem Risikokapital sollten den Handel in Betracht ziehen. Die vergangene "
            "Performance ist nicht notwendigerweise ein Hinweis auf zukuenftige Ergebnisse. "
            "Testimonials, die auf dieser Website erscheinen, sind moeglicherweise nicht "
            "repraesentativ fuer andere Kunden oder Klienten und stellen keine Garantie fuer "
            "kuenftige Performance oder Erfolg dar."
            "<br><br>"
            "<b style='color:#aabbcc;'>Risk Disclosure (EN)</b><br>"
            "Past results and past seasonal patterns provide no indication whatsoever of future "
            "performance, in particular future market trends. SeasonAlpha neither recommends nor "
            "endorses any particular financial instrument, group of securities, segment of industry, "
            "analysis interval or any particular idea, approach, strategy or attitude, nor does it "
            "provide consulting, brokerage or asset management services. SeasonAlpha hereby excludes "
            "any explicit or implied trading recommendation, in particular any promise, implication "
            "or guarantee that profits will be earned and losses avoided; however, in the event of "
            "any doubt, these terms shall be interpreted in the broadest possible sense. Any "
            "information provided by SeasonAlpha or appearing on this website or any other kind of "
            "data medium shall not be construed as any kind of guarantee, warranty or representation, "
            "in particular not as one set forth in a prospectus. Any user is solely responsible for "
            "the results or the trading strategy that is created, developed or applied. Indicators, "
            "trading strategies and functions provided by SeasonAlpha or on this website or any other "
            "kind of data medium may contain logical or other errors that may lead to unexpected "
            "results, faulty trading signals and/or substantial losses. SeasonAlpha neither warrants "
            "nor guarantees the accuracy, completeness, quality, adequacy or content of the "
            "information provided by it or on this website or any other kind of data medium. Any user "
            "is obligated to comply with all applicable capital market rules of the applicable "
            "jurisdiction. All published content and images on this website or any other kind of data "
            "medium are protected by copyright. Any duplication, processing, distribution or any form "
            "of utilisation beyond the scope of copyright law shall require the prior written consent "
            "of the author or authors in question. Futures and forex trading involves substantial "
            "risk and is not suitable for every investor. An investor could potentially lose all or "
            "more than the initial investment. Risk capital is money that can be lost without "
            "jeopardising one's financial security or lifestyle. Only risk capital should be used for "
            "trading and only those with sufficient risk capital should consider trading. Past "
            "performance is not necessarily indicative of future results. Testimonials appearing on "
            "this website may not be representative of other clients or customers and do not "
            "constitute a guarantee of future performance or success."
            "</div>",
            unsafe_allow_html=True,
        )
