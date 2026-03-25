"""
SeasonAlpha — Haupteinstieg
==============================
Startet die App und leitet zur Home Page weiter.
Start: py -3.14 -m streamlit run seasonal_app.py
"""

import streamlit as st

st.set_page_config(
    page_title="SeasonAlpha",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Google Search Console Verifizierung
st.markdown(
    '<meta name="google-site-verification" content="46lbAINaqCQSU5pWAplt6WioigjnIc3mmLMBnCteMwk">',
    unsafe_allow_html=True,
)

# Redirect zur Home Page
st.switch_page("pages/00_Home.py")
