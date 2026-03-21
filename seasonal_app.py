"""
SeasonalAlpha — Haupteinstieg
==============================
Startet die App und leitet zur Home Page weiter.
Start: py -3.14 -m streamlit run seasonal_app.py
"""

import streamlit as st

st.set_page_config(
    page_title="SeasonalAlpha",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Redirect zur Home Page
st.switch_page("pages/00_Home.py")
