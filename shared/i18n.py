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


# SVG-Flags als Data-URI (funktioniert auf allen Plattformen inkl. Windows)
_FLAG_DE = (
    "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 5 3'%3E"
    "%3Crect width='5' height='1' fill='%23000'/%3E"
    "%3Crect width='5' height='1' y='1' fill='%23D00'/%3E"
    "%3Crect width='5' height='1' y='2' fill='%23FFCE00'/%3E"
    "%3C/svg%3E"
)
_FLAG_US = (
    "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 19 10'%3E"
    "%3Crect width='19' height='10' fill='%23B22234'/%3E"
    "%3Crect width='19' height='1.54' y='1.54' fill='%23fff'/%3E"
    "%3Crect width='19' height='1.54' y='4.62' fill='%23fff'/%3E"
    "%3Crect width='19' height='1.54' y='7.69' fill='%23fff'/%3E"
    "%3Crect width='7.6' height='5.38' fill='%233C3B6E'/%3E"
    "%3C/svg%3E"
)


# ── Language Toggle — Sidebar oben (via Main-Kontext injiziert) ──────────
def lang_toggle() -> None:
    """Rendert DE/US Flaggen-Toggle über den Sidebar-Nav-Items.

    Nutzt window.parent.document.body via JS-Iframe — einziger Weg,
    position:fixed aus Streamlit heraus korrekt zu rendern.
    """
    import streamlit.components.v1 as _components

    # Browser-Sprache beim allerersten Besuch
    if "lang" not in st.session_state and not st.query_params.get("lang"):
        st.session_state["lang"] = "de"

    lang = get_lang()
    de_outline = "outline:2px solid #fff;outline-offset:1px;" if lang == "de" else "opacity:0.45;"
    en_outline = "outline:2px solid #fff;outline-offset:1px;" if lang == "en" else "opacity:0.45;"

    _components.html(f"""
    <script>
    (function() {{
        function injectFlags() {{
            var doc = window.parent ? window.parent.document : document;

            // Bereits vorhandenen Toggle entfernen (bei Rerender)
            var old = doc.getElementById('sa-lang-toggle');
            if (old) old.remove();

            // Sidebar-Nav Platz schaffen
            var nav = doc.querySelector('[data-testid="stSidebarNav"]');
            if (nav) nav.style.paddingTop = '46px';

            // Toggle-Div direkt in body einhängen → position:fixed funktioniert
            var div = doc.createElement('div');
            div.id = 'sa-lang-toggle';
            div.style.cssText = [
                'position:fixed',
                'top:11px',
                'left:13px',
                'z-index:99999',
                'display:flex',
                'gap:7px',
                'align-items:center',
                'pointer-events:auto'
            ].join(';');

            div.innerHTML =
                '<a href="?lang=de" title="Deutsch" style="text-decoration:none;line-height:0;cursor:pointer;">' +
                    '<img src="{_FLAG_DE}" width="26" height="16" ' +
                         'style="display:block;border-radius:3px;{de_outline}">' +
                '</a>' +
                '<a href="?lang=en" title="English" style="text-decoration:none;line-height:0;cursor:pointer;">' +
                    '<img src="{_FLAG_US}" width="26" height="16" ' +
                         'style="display:block;border-radius:3px;{en_outline}">' +
                '</a>';

            doc.body.appendChild(div);
        }}

        // Sofort + nach DOM-Ready ausführen
        if (document.readyState === 'loading') {{
            document.addEventListener('DOMContentLoaded', injectFlags);
        }} else {{
            injectFlags();
        }}
    }})();
    </script>
    """, height=0)
