# shared/i18n.py — Internationalisierung (DE / EN)
# ============================================================
# Verwendung:
#   from shared.i18n import t, lang_toggle
#   lang_toggle()          # in der Sidebar aufrufen
#   label = t("key")       # String übersetzen
# ============================================================

import streamlit as st

# ── Sprach-Erkennung via Browser ─────────────────────────────
_LANG_DETECT_JS = """
<script>
(function() {
    try {
        var stored = localStorage.getItem('sa_lang');
        if (stored) {
            window.parent.postMessage({type: 'SA_LANG', lang: stored}, '*');
            return;
        }
        var bl = (navigator.language || navigator.userLanguage || 'de').toLowerCase();
        var lang = bl.startsWith('de') ? 'de' : 'en';
        localStorage.setItem('sa_lang', lang);
        window.parent.postMessage({type: 'SA_LANG', lang: lang}, '*');
    } catch(e) {}
})();
</script>
"""

# ── Übersetzungs-Dictionary ───────────────────────────────────
TRANSLATIONS: dict[str, dict[str, str]] = {

    # ── Navigation ───────────────────────────────────────────
    "nav_home":             {"de": "Home",                  "en": "Home"},
    "nav_decade":           {"de": "Dekadenzyklus",         "en": "Decade Cycle"},
    "nav_yearly":           {"de": "Jahreszyklus",          "en": "Annual Cycle"},
    "nav_monthly":          {"de": "Monatszyklus",          "en": "Monthly Cycle"},
    "nav_weekdays":         {"de": "Wochentage",            "en": "Weekdays"},
    "nav_turn_of_month":    {"de": "Monatswechsel",         "en": "Turn of Month"},
    "nav_moon":             {"de": "Mondphasen",            "en": "Moon Phases"},
    "nav_trifecta":         {"de": "Januar Trifecta",       "en": "January Trifecta"},

    # ── Sidebar ───────────────────────────────────────────────
    "sidebar_ticker":       {"de": "Ticker",                "en": "Ticker"},
    "sidebar_years":        {"de": "Jahre zurück",          "en": "Years back"},
    "sidebar_language":     {"de": "Sprache",               "en": "Language"},

    # ── Home Page ─────────────────────────────────────────────
    "home_eyebrow":         {"de": "DATENGETRIEBENE BÖRSENANALYSE",
                             "en": "DATA-DRIVEN MARKET ANALYSIS"},
    "home_headline_1":      {"de": "Seasonal",              "en": "Seasonal"},
    "home_headline_2":      {"de": "Alpha",                 "en": "Alpha"},
    "home_subtitle":        {"de": "Entdecke saisonale Muster, historische Renditen und statistische Signale — für smarte Anlageentscheidungen.",
                             "en": "Discover seasonal patterns, historical returns and statistical signals — for smarter investment decisions."},
    "home_badge":           {"de": "📊 Daten seit 1896 · Kostenlos testen",
                             "en": "📊 Data since 1896 · Try for free"},
    "home_cta_start":       {"de": "Jetzt starten",         "en": "Get started"},
    "home_cta_learn":       {"de": "Mehr erfahren",         "en": "Learn more"},

    "home_modules_label":   {"de": "ANALYSE-MODULE",        "en": "ANALYSIS MODULES"},
    "home_modules_title":   {"de": "Alle Zyklen. Ein Tool.", "en": "All cycles. One tool."},
    "home_modules_sub":     {"de": "Von Dekaden bis Wochentagen — historisch analysiert.",
                             "en": "From decades to weekdays — historically analysed."},

    # ── Modul-Kacheln ─────────────────────────────────────────
    "module_decade_title":  {"de": "Dekadenzyklus",         "en": "Decade Cycle"},
    "module_decade_desc":   {"de": "131 Jahre DJI — Renditen nach Jahrzehnt-Endziffer",
                             "en": "131 years DJI — returns by decade digit"},
    "module_yearly_title":  {"de": "Jahreszyklus",          "en": "Annual Cycle"},
    "module_yearly_desc":   {"de": "Saisonaler Jahresverlauf, Präsidentenzyklus & Anomalien",
                             "en": "Seasonal annual pattern, presidential cycle & anomalies"},
    "module_monthly_title": {"de": "Monatszyklus",          "en": "Monthly Cycle"},
    "module_monthly_desc":  {"de": "Intramonatliche TDOM-Muster & Two-Week Performance",
                             "en": "Intra-month TDOM patterns & two-week performance"},
    "module_weekday_title": {"de": "Wochentage",            "en": "Weekdays"},
    "module_weekday_desc":  {"de": "Renditen nach Wochentag, Overnight vs. Intraday",
                             "en": "Returns by weekday, overnight vs. intraday"},
    "module_tom_title":     {"de": "Monatswechsel",         "en": "Turn of Month"},
    "module_tom_desc":      {"de": "Turn-of-Month Effekt: Renditen rund um den Monatsanfang",
                             "en": "Turn-of-month effect: returns around month start"},
    "module_moon_title":    {"de": "Mondphasen",            "en": "Moon Phases"},
    "module_moon_desc":     {"de": "Vollmond, Neumond & Supermond-Effekte",
                             "en": "Full moon, new moon & supermoon effects"},
    "module_trifecta_title":{"de": "Januar Trifecta",       "en": "January Trifecta"},
    "module_trifecta_desc": {"de": "Premium-Ampel: 3 Signale für das Börsenjahr",
                             "en": "Premium signal: 3 indicators for the stock market year"},
    "module_blog_title":    {"de": "Blog & Tutorials",      "en": "Blog & Tutorials"},
    "module_blog_desc":     {"de": "Strategien, Erklärungen und Marktanalysen",
                             "en": "Strategies, explanations and market analyses"},

    # ── Stats-Kacheln ─────────────────────────────────────────
    "stat_years":           {"de": "Jahre Daten",           "en": "Years of data"},
    "stat_tickers":         {"de": "Ticker verfügbar",      "en": "Tickers available"},
    "stat_patterns":        {"de": "Saisonale Muster",      "en": "Seasonal patterns"},
    "stat_free":            {"de": "Kostenlos",             "en": "Free"},

    # ── Allgemeine UI ─────────────────────────────────────────
    "loading":              {"de": "Lädt…",                 "en": "Loading…"},
    "no_data":              {"de": "Keine Daten verfügbar", "en": "No data available"},
    "years_back":           {"de": "Jahre",                 "en": "years"},
    "avg_return":           {"de": "Ø Rendite",             "en": "Avg. Return"},
    "win_rate":             {"de": "Win-Rate",              "en": "Win Rate"},
    "significant":          {"de": "Signifikant",           "en": "Significant"},
    "not_significant":      {"de": "Nicht signifikant",     "en": "Not significant"},
    "we_are_here":          {"de": "📍 Wir sind hier!",     "en": "📍 We are here!"},
    "show_details":         {"de": "Details anzeigen",      "en": "Show details"},
    "download":             {"de": "Download",              "en": "Download"},
    "disclaimer":           {"de": "Keine Anlageberatung. Vergangene Muster garantieren keine zukünftigen Renditen.",
                             "en": "Not financial advice. Past patterns do not guarantee future returns."},

    # ── Chartbeschriftungen ───────────────────────────────────
    "chart_return":         {"de": "Rendite (%)",           "en": "Return (%)"},
    "chart_year":           {"de": "Jahr",                  "en": "Year"},
    "chart_month":          {"de": "Monat",                 "en": "Month"},
    "chart_weekday":        {"de": "Wochentag",             "en": "Weekday"},
    "chart_heatmap_10y":    {"de": "10 Jahres Monats-Heatmap", "en": "10-Year Monthly Heatmap"},

    # ── Monatsnamen ───────────────────────────────────────────
    "month_jan":            {"de": "Jan", "en": "Jan"},
    "month_feb":            {"de": "Feb", "en": "Feb"},
    "month_mar":            {"de": "Mär", "en": "Mar"},
    "month_apr":            {"de": "Apr", "en": "Apr"},
    "month_may":            {"de": "Mai", "en": "May"},
    "month_jun":            {"de": "Jun", "en": "Jun"},
    "month_jul":            {"de": "Jul", "en": "Jul"},
    "month_aug":            {"de": "Aug", "en": "Aug"},
    "month_sep":            {"de": "Sep", "en": "Sep"},
    "month_oct":            {"de": "Okt", "en": "Oct"},
    "month_nov":            {"de": "Nov", "en": "Nov"},
    "month_dec":            {"de": "Dez", "en": "Dec"},

    # ── Wochentage ────────────────────────────────────────────
    "day_mon":              {"de": "Montag",    "en": "Monday"},
    "day_tue":              {"de": "Dienstag",  "en": "Tuesday"},
    "day_wed":              {"de": "Mittwoch",  "en": "Wednesday"},
    "day_thu":              {"de": "Donnerstag","en": "Thursday"},
    "day_fri":              {"de": "Freitag",   "en": "Friday"},

    # ── Footer ────────────────────────────────────────────────
    "footer_imprint":       {"de": "Impressum",             "en": "Imprint"},
    "footer_privacy":       {"de": "Datenschutz",           "en": "Privacy Policy"},
    "footer_risk":          {"de": "Risikohinweis",         "en": "Risk Disclosure"},
    "footer_blog":          {"de": "Blog",                  "en": "Blog"},
    "footer_rights":        {"de": "Alle Rechte vorbehalten.", "en": "All rights reserved."},
}


# ── Kern-Funktion ─────────────────────────────────────────────
def t(key: str, **kwargs) -> str:
    """Gibt den übersetzten String für den aktuellen Sprachmodus zurück.

    Beispiel:
        t("nav_weekdays")           → "Wochentage" oder "Weekdays"
        t("home_subtitle")          → langer Satz je Sprache
    """
    lang = st.session_state.get("lang", "de")
    entry = TRANSLATIONS.get(key)
    if entry is None:
        return key  # Fallback: Key selbst zurückgeben
    text = entry.get(lang, entry.get("de", key))
    if kwargs:
        text = text.format(**kwargs)
    return text


def get_lang() -> str:
    """Gibt die aktuelle Sprache zurück ('de' oder 'en').
    Priorität: URL-Parameter → session_state → Browser → Default 'de'
    """
    # 1. URL-Parameter hat höchste Priorität
    qp = st.query_params.get("lang", "")
    if qp in ("de", "en"):
        st.session_state["lang"] = qp
        return qp
    # 2. Session State
    return st.session_state.get("lang", "de")


def set_lang(lang: str) -> None:
    """Setzt die Sprache in Session und URL-Parameter."""
    st.session_state["lang"] = lang
    st.query_params["lang"] = lang


# ── Language Toggle — fixed oben rechts ──────────────────────
def lang_toggle() -> None:
    """Rendert kleine 🇩🇪 / 🇺🇸 Flaggen fixed oben rechts.

    Aufruf einmalig pro Page direkt nach inject_se_css():
        from shared.i18n import lang_toggle
        lang_toggle()
    """
    # Browser-Sprache beim allerersten Besuch (kein URL-Param, kein State)
    if "lang" not in st.session_state and not st.query_params.get("lang"):
        st.components.v1.html(_LANG_DETECT_JS, height=0)
        st.session_state["lang"] = "de"

    lang = get_lang()
    de_style = "opacity:1;transform:scale(1.15)" if lang == "de" else "opacity:0.45;transform:scale(1)"
    en_style = "opacity:1;transform:scale(1.15)" if lang == "en" else "opacity:0.45;transform:scale(1)"

    st.markdown(f"""
    <div style="
        position: fixed;
        top: 10px;
        right: 56px;
        z-index: 99999;
        display: flex;
        gap: 4px;
        align-items: center;
        background: rgba(8,12,18,0.75);
        backdrop-filter: blur(6px);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 20px;
        padding: 3px 8px;
    ">
        <a href="?lang=de" title="Deutsch" style="
            text-decoration: none;
            font-size: 1.25rem;
            line-height: 1;
            transition: all .2s;
            {de_style};
        ">🇩🇪</a>
        <span style="color:rgba(255,255,255,0.2);font-size:.7rem;">│</span>
        <a href="?lang=en" title="English" style="
            text-decoration: none;
            font-size: 1.25rem;
            line-height: 1;
            transition: all .2s;
            {en_style};
        ">🇺🇸</a>
    </div>
    """, unsafe_allow_html=True)
