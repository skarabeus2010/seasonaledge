# pages/10_Methodik.py
# ============================================================
# METHODIK & ERKLÄRUNGEN — Zentrale Referenz-Seite
# ============================================================
# Ersetzt das verteilte ⓘ-Badge-System (info_badge.py) durch
# eine eigenständige, strukturierte Übersichtsseite.
# Datenquelle: shared/info_texts.yaml (DE/EN)
# ============================================================

import sys, os, pathlib

try:
    _project_dir = str(pathlib.Path(__file__).resolve().parent.parent)
except NameError:
    _project_dir = os.getcwd()
if not os.path.isdir(os.path.join(_project_dir, "shared")):
    for _c in [os.getcwd(), os.path.dirname(os.path.abspath(sys.argv[-1])) if sys.argv else ""]:
        if os.path.isdir(os.path.join(_c, "shared")):
            _project_dir = _c
            break
if _project_dir not in sys.path:
    sys.path.insert(0, _project_dir)

import streamlit as st
import yaml
from pathlib import Path

st.set_page_config(
    page_title="SeasonAlpha – Methodik & Erklärungen",
    page_icon="📖",
    layout="wide",
)

from shared.design import inject_se_css
from shared.footer import render_footer
from shared.i18n import t, lang_toggle, get_lang

inject_se_css()
lang_toggle()

# ══════════════════════════════════════════════════════════════
# Daten laden
# ══════════════════════════════════════════════════════════════
_YAML_PATH = Path(__file__).resolve().parent.parent / "shared" / "info_texts.yaml"

@st.cache_data
def _load_info_texts() -> dict:
    if not _YAML_PATH.exists():
        return {}
    with open(_YAML_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


# ── Sektionen: Key → (Icon, Titel DE, Titel EN, zugehörige YAML-Keys) ──
SECTIONS = [
    {
        "icon": "📊",
        "de": "Dekadenzyklus",
        "en": "Decade Cycle",
        "page": "01_Dekadenzyklus",
        "keys": [
            "dekade_kohorte", "dekade_jahresrendite",
            "dekade_monatsrendite", "dekade_boxplot",
        ],
    },
    {
        "icon": "📈",
        "de": "Jahreszyklus",
        "en": "Annual Cycle",
        "page": "02_Jahreszyklus",
        "keys": [
            "detrend_indikator", "pattern_breaks",
            "monats_performance", "monats_signifikanz",
            "signal_robustheit", "praesidentenzyklus_match",
            "heatmap_10j",
        ],
    },
    {
        "icon": "📅",
        "de": "Monatszyklus",
        "en": "Monthly Cycle",
        "page": "03_Monatszyklus",
        "keys": [
            "seasonal_match", "wochen_performance",
            "two_week_performance", "two_week_heatmap",
        ],
    },
    {
        "icon": "📆",
        "de": "Wochentage",
        "en": "Weekdays",
        "page": "04_Wochentage",
        "keys": [
            "kumulierter_wochenverlauf", "wochentag_rendite",
            "overnight_split", "konsekutiv_analyse",
            "quartals_wochentag", "volatilitaets_profil",
            "monat_wochentag_heatmap",
        ],
    },
    {
        "icon": "🔄",
        "de": "Monatswechsel",
        "en": "Turn of Month",
        "page": "05_Monatswechsel",
        "keys": [
            "tom_kennzahlen", "tom_heatmap",
            "streak_analyse", "fenster_optimierung",
            "praesidentenzyklus_tom",
        ],
    },
    {
        "icon": "🌙",
        "de": "Mondphasen",
        "en": "Moon Phases",
        "page": "06_Mondphasen",
        "keys": [
            "mond_heatmap", "supermond_analyse", "lunar_kalender",
        ],
    },
    {
        "icon": "🚦",
        "de": "Januar Trifecta",
        "en": "January Trifecta",
        "page": "07_Januar_Trifecta",
        "keys": [
            "trifecta_auswertung", "trifecta_verlauf", "trifecta_drawdown",
        ],
    },
    {
        "icon": "🔬",
        "de": "Backtest Engine",
        "en": "Backtest Engine",
        "page": "12_Backtest_Engine",
        "keys": [
            "event_relevanz",
        ],
    },
    {
        "icon": "🤖",
        "de": "KI-Analyse & Anomalien",
        "en": "AI Analysis & Anomalies",
        "page": "Premium",
        "keys": [
            "anomalie_radar", "ki_zusammenfassung",
            "anomalie_heatmap", "mstl_zerlegung",
            "chronos_forecast", "pattern_breaks",
            "dtw_aehnlichkeit", "prophet_prognose",
            "ki_winrate", "tracking_qualitaet",
            "tdom_anomalien",
        ],
    },
    {
        "icon": "📉",
        "de": "Spot-Vol Beta",
        "en": "Spot-Vol Beta",
        "page": "Premium",
        "keys": [
            "spot_vol_beta", "vix_extreme",
        ],
    },
]

# ── Lesbare Titel für YAML-Keys ─────────────────────────────────
KEY_TITLES: dict[str, dict[str, str]] = {
    "dekade_kohorte":              {"de": "Dekaden-Kohorte",               "en": "Decade Cohort"},
    "dekade_jahresrendite":        {"de": "Jahresrendite nach Endziffer",  "en": "Annual Return by Digit"},
    "dekade_monatsrendite":        {"de": "Monatsrendite × Dekade",        "en": "Monthly Return × Decade"},
    "dekade_boxplot":              {"de": "Box-Plot Dekaden",              "en": "Decade Box Plot"},
    "detrend_indikator":           {"de": "Detrend-Indikator",             "en": "Detrend Indicator"},
    "pattern_breaks":              {"de": "Muster-Brüche",                 "en": "Pattern Breaks"},
    "monats_performance":          {"de": "Monats-Performance",            "en": "Monthly Performance"},
    "monats_signifikanz":          {"de": "Monats-Signifikanz",            "en": "Monthly Significance"},
    "signal_robustheit":           {"de": "Signal-Robustheit",             "en": "Signal Robustness"},
    "praesidentenzyklus_match":    {"de": "Präsidentenzyklus Best Match",  "en": "Presidential Cycle Best Match"},
    "heatmap_10j":                 {"de": "10-Jahres Heatmap",             "en": "10-Year Heatmap"},
    "seasonal_match":              {"de": "Seasonal Match",                "en": "Seasonal Match"},
    "wochen_performance":          {"de": "Wochen-Performance",            "en": "Weekly Performance"},
    "two_week_performance":        {"de": "Two-Week Performance",          "en": "Two-Week Performance"},
    "two_week_heatmap":            {"de": "Two-Week Heatmap",              "en": "Two-Week Heatmap"},
    "kumulierter_wochenverlauf":   {"de": "Kumulierter Wochenverlauf",     "en": "Cumulative Weekly Pattern"},
    "wochentag_rendite":           {"de": "Wochentag-Rendite",             "en": "Weekday Returns"},
    "overnight_split":             {"de": "Overnight / Intraday Split",    "en": "Overnight / Intraday Split"},
    "konsekutiv_analyse":          {"de": "Konsekutiv-Analyse",            "en": "Consecutive Analysis"},
    "quartals_wochentag":          {"de": "Quartals-Wochentag",            "en": "Quarter × Weekday"},
    "volatilitaets_profil":        {"de": "Volatilitäts-Profil",           "en": "Volatility Profile"},
    "monat_wochentag_heatmap":     {"de": "Monat × Wochentag Heatmap",    "en": "Month × Weekday Heatmap"},
    "tom_kennzahlen":              {"de": "TOM Kennzahlen",                "en": "TOM Key Metrics"},
    "tom_heatmap":                 {"de": "TOM Heatmap",                   "en": "TOM Heatmap"},
    "streak_analyse":              {"de": "Streak-Analyse",                "en": "Streak Analysis"},
    "fenster_optimierung":         {"de": "Fenster-Optimierung",           "en": "Window Optimization"},
    "praesidentenzyklus_tom":      {"de": "Präsidentenzyklus × TOM",       "en": "Presidential Cycle × TOM"},
    "mond_heatmap":                {"de": "Mond-Heatmap",                  "en": "Moon Heatmap"},
    "supermond_analyse":           {"de": "Supermond-Analyse",             "en": "Supermoon Analysis"},
    "lunar_kalender":              {"de": "Lunar-Kalender",                "en": "Lunar Calendar"},
    "trifecta_auswertung":         {"de": "Trifecta-Auswertung",           "en": "Trifecta Evaluation"},
    "trifecta_verlauf":            {"de": "Trifecta-Verlauf",              "en": "Trifecta Trajectory"},
    "trifecta_drawdown":           {"de": "Trifecta Max Drawdown",         "en": "Trifecta Max Drawdown"},
    "event_relevanz":              {"de": "Event-Relevanz",                "en": "Event Relevance"},
    "anomalie_radar":              {"de": "Anomalie-Radar",                "en": "Anomaly Radar"},
    "ki_zusammenfassung":          {"de": "KI-Zusammenfassung",            "en": "AI Summary"},
    "anomalie_heatmap":            {"de": "Anomalie-Heatmap",              "en": "Anomaly Heatmap"},
    "mstl_zerlegung":              {"de": "MSTL-Zerlegung",                "en": "MSTL Decomposition"},
    "chronos_forecast":            {"de": "Chronos Forecast",              "en": "Chronos Forecast"},
    "dtw_aehnlichkeit":            {"de": "DTW-Ähnlichkeit",               "en": "DTW Similarity"},
    "prophet_prognose":            {"de": "Prophet-Prognose",              "en": "Prophet Forecast"},
    "ki_winrate":                  {"de": "KI Win-Rate",                   "en": "AI Win Rate"},
    "tracking_qualitaet":          {"de": "Tracking-Qualität",             "en": "Tracking Quality"},
    "tdom_anomalien":              {"de": "TDoM-Anomalien",                "en": "TDoM Anomalies"},
    "spot_vol_beta":               {"de": "Spot-Vol Beta",                 "en": "Spot-Vol Beta"},
    "vix_extreme":                 {"de": "VIX-Extreme",                   "en": "VIX Extremes"},
}


# ══════════════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════════════
st.markdown("""
<style>
.methodik-header {
    text-align: center;
    padding: 2rem 0 1rem;
}
.methodik-header h1 {
    font-size: 2.2rem;
    font-weight: 700;
    color: #e8e8e8;
    margin-bottom: 0.5rem;
}
.methodik-header p {
    color: #8899aa;
    font-size: 1rem;
    max-width: 700px;
    margin: 0 auto;
    line-height: 1.6;
}

/* Sektion-Header */
.methodik-section {
    margin: 2rem 0 0.5rem;
    padding: 0.8rem 1.2rem;
    background: linear-gradient(135deg, rgba(77,159,255,0.08) 0%, rgba(0,212,170,0.05) 100%);
    border-left: 3px solid #4d9fff;
    border-radius: 0 8px 8px 0;
}
.methodik-section h2 {
    font-size: 1.25rem;
    font-weight: 600;
    color: #e0e0e0;
    margin: 0;
}
.methodik-section .page-ref {
    font-size: 0.75rem;
    color: #5a7a9a;
    margin-top: 2px;
}

/* Einzelne Erklärungs-Karte */
.methodik-card {
    background: #0f1923;
    border: 1px solid #1c2a3e;
    border-radius: 10px;
    padding: 1rem 1.2rem;
    margin: 0.5rem 0;
    transition: border-color 0.2s;
}
.methodik-card:hover {
    border-color: #4d9fff;
}
.methodik-card .card-title {
    font-size: 0.9rem;
    font-weight: 600;
    color: #4d9fff;
    margin-bottom: 0.4rem;
}
.methodik-card .card-text {
    font-size: 0.82rem;
    color: #a0b0c5;
    line-height: 1.6;
    margin: 0;
}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# Sidebar
# ══════════════════════════════════════════════════════════════
lang = get_lang()

with st.sidebar:
    if lang == "de":
        st.markdown("## 📖 Methodik & Erklärungen")
        st.markdown("---")
        st.markdown(
            "Zentrale Übersicht aller Analyse-Methoden, "
            "statistischen Verfahren und Kennzahlen."
        )
    else:
        st.markdown("## 📖 Methodology & Explanations")
        st.markdown("---")
        st.markdown(
            "Central reference for all analysis methods, "
            "statistical procedures and key metrics."
        )


# ══════════════════════════════════════════════════════════════
# Header
# ══════════════════════════════════════════════════════════════
if lang == "de":
    st.markdown("""
    <div class="methodik-header">
        <h1>📖 Methodik & Erklärungen</h1>
        <p>
            Alle Analyse-Methoden, statistischen Verfahren und Kennzahlen
            auf einen Blick — von Dekaden-Kohorten über DTW Pattern Matching
            bis hin zur Anomalie-Erkennung.
        </p>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="methodik-header">
        <h1>📖 Methodology & Explanations</h1>
        <p>
            All analysis methods, statistical procedures and key metrics
            at a glance — from decade cohorts and DTW pattern matching
            to anomaly detection.
        </p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")


# ══════════════════════════════════════════════════════════════
# Kern-Methodik: Normalisierte Renditen
# ══════════════════════════════════════════════════════════════
if lang == "de":
    st.markdown("""
    <div class="methodik-section">
        <h2>🎯 Kern-Methodik: Normalisierte Renditen</h2>
    </div>
    <div class="methodik-card">
        <div class="card-text">
            Alle saisonalen Analysen basieren auf <b>normalisierten Renditen</b>:
            Jedes Jahr startet bei 100, tägliche prozentuale Renditen kumulieren darauf.
            So werden Jahre mit unterschiedlichem Kursniveau vergleichbar.
            <br><br>
            <b>Wichtig:</b> Es werden immer <b>Handelstage</b> (Trading Days) gezählt,
            nicht Kalendertage. Wochenenden und Feiertage sind ausgeschlossen.
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="methodik-section">
        <h2>🎯 Core Methodology: Normalized Returns</h2>
    </div>
    <div class="methodik-card">
        <div class="card-text">
            All seasonal analyses are based on <b>normalized returns</b>:
            Each year starts at 100, daily percentage returns accumulate on top.
            This makes years with different price levels comparable.
            <br><br>
            <b>Important:</b> We always count <b>trading days</b>,
            not calendar days. Weekends and holidays are excluded.
        </div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# Sektionen rendern
# ══════════════════════════════════════════════════════════════
texts = _load_info_texts()

for section in SECTIONS:
    icon = section["icon"]
    title = section["de"] if lang == "de" else section["en"]
    page_ref = section["page"]

    # Prüfen ob mindestens ein Key existiert
    valid_keys = [k for k in section["keys"] if k in texts]
    if not valid_keys:
        continue

    page_label = f"→ {page_ref}" if page_ref != "Premium" else "→ Premium (coming soon)"

    st.markdown(f"""
    <div class="methodik-section">
        <h2>{icon} {title}</h2>
        <div class="page-ref">{page_label}</div>
    </div>
    """, unsafe_allow_html=True)

    for key in valid_keys:
        entry = texts[key]
        text = entry.get(lang) or entry.get("de") or ""
        if not text:
            continue

        # Titel aus KEY_TITLES oder Fallback aus Key
        title_entry = KEY_TITLES.get(key, {})
        card_title = title_entry.get(lang) or title_entry.get("de") or key.replace("_", " ").title()

        st.markdown(f"""
        <div class="methodik-card">
            <div class="card-title">{card_title}</div>
            <div class="card-text">{text}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# Footer
# ══════════════════════════════════════════════════════════════
render_footer()
