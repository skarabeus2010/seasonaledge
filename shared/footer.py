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
            "Past results and past seasonal patterns are no indication of future performance, "
            "in particular, future market trends. SeasonAlpha neither recommends nor approves of "
            "any particular financial instrument, group of securities, segment of industry, analysis "
            "interval or any particular idea, approach, strategy or attitude nor provides consulting "
            "nor brokerage nor asset management services. SeasonAlpha hereby excludes any explicit or "
            "implied trading recommendation, in particular, any promise, implication or guarantee that "
            "profits are earned and losses excluded, provided, however, that in case of doubt, these "
            "terms shall be interpreted in a broad sense. Any information provided by SeasonAlpha or "
            "on this website or any other kind of data media shall not be construed as any kind of "
            "guarantee, warranty or representation, in particular as set forth in a prospectus. Any "
            "user is solely responsible for the results or the trading strategy that is created, "
            "developed or applied. Indicators, trading strategies and functions provided by SeasonAlpha "
            "or on this website or any other kind of data media may contain logical or other errors "
            "leading to unexpected results, faulty trading signals and/or substantial losses. "
            "SeasonAlpha neither warrants nor guarantees the accuracy, completeness, quality, adequacy "
            "or content of the information provided by it or on this website or any other kind of data "
            "media. Any user is obligated to comply with any applicable capital market rules of the "
            "applicable jurisdiction. All published content and images on this website or any other "
            "kind of data media are protected by copyright. Any duplication, processing, distribution "
            "or any form of utilisation beyond the scope of copyright law shall require the prior "
            "written consent of the author or authors in question. Futures and forex trading contains "
            "substantial risk and is not for every investor. An investor could potentially lose all or "
            "more than the initial investment. Risk capital is money that can be lost without "
            "jeopardizing ones' financial security or lifestyle. Only risk capital should be used for "
            "trading and only those with sufficient risk capital should consider trading. Past "
            "performance is not necessarily indicative of future results. Testimonials appearing on "
            "this website may not be representative of other clients or customers and is not a "
            "guarantee of future performance or success."
            "</div>",
            unsafe_allow_html=True,
        )
