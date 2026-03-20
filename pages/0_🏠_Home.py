# pages/0_🏠_Home.py
# ============================================================
# STARTSEITE — SeasonalEdge v8.3
# ============================================================

import sys, os, pathlib, requests, base64
import pandas as pd

try:
    _project_dir = str(pathlib.Path(__file__).resolve().parent.parent)
except NameError:
    _project_dir = os.getcwd()
if not os.path.isdir(os.path.join(_project_dir, "shared")):
    for _c in [os.getcwd(), os.path.dirname(os.path.abspath(sys.argv[-1])) if sys.argv else ""]:
        if os.path.isdir(os.path.join(_c, "shared")):
            _project_dir = _c; break
if _project_dir not in sys.path:
    sys.path.insert(0, _project_dir)

import streamlit as st

st.set_page_config(
    page_title="SeasonalEdge | Saisonale Trading-Analysen",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

from shared.design import inject_se_css
inject_se_css()

# ══════════════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif !important; }
#MainMenu, footer, header { visibility: hidden; }
/* Sidebar sichtbar lassen fuer Navigation */
.block-container { padding-top: 2rem !important; padding-bottom: 2rem !important; max-width: 1200px; }

/* ── Hero ── */
.se-hero {
    background: linear-gradient(160deg, #080b10 0%, #0e1520 60%, #0a1128 100%);
    border: 1px solid #1a2235; border-radius: 16px;
    padding: 4rem 2rem 3rem; text-align: center;
    margin-bottom: 2rem; position: relative; overflow: hidden;
}
.se-hero::before {
    content: ''; position: absolute; top: -60px; left: 50%; transform: translateX(-50%);
    width: 600px; height: 300px;
    background: radial-gradient(ellipse, rgba(30,110,240,0.12) 0%, transparent 70%);
    pointer-events: none;
}
.se-eyebrow {
    display: inline-block; background: rgba(30,110,240,0.12);
    border: 1px solid rgba(30,110,240,0.3); color: #4d9fff;
    font-size: .72rem; font-weight: 600; letter-spacing: 2px;
    text-transform: uppercase; padding: 4px 14px; border-radius: 20px; margin-bottom: 1.2rem;
}
.se-h1 {
    font-size: clamp(2rem,5vw,3.8rem); font-weight: 800;
    line-height: 1.1; letter-spacing: -1.5px; margin-bottom: .8rem;
}
/* Seasonal = Gold (#e8a425), Edge = Blau (#4d9fff), BETA = weißlich */
.se-h1 .gold { color: #e8a425; }
.se-h1 .blue { color: #4d9fff; }
.se-h1 .white { color: #e8edf5; }
.se-sub {
    font-size: clamp(.9rem,1.8vw,1.1rem); color: #e8a425;
    max-width: 580px; margin: 0 auto 2rem; font-weight: 400; line-height: 1.7;
}
.se-badge {
    display: inline-block; background: rgba(232,164,37,0.1);
    border: 1px solid rgba(232,164,37,0.25); color: #e8a425;
    font-size: .75rem; font-weight: 600; padding: 4px 14px;
    border-radius: 20px; margin-top: 1.5rem;
}

/* ── Section Headers ── */
.se-section-label { font-size: .7rem; letter-spacing: 3px; text-transform: uppercase; color: #4d9fff; font-weight: 600; margin-bottom: .4rem; }
.se-section-title { font-size: clamp(1.4rem,3vw,2rem); font-weight: 800; letter-spacing: -.5px; color: #e8edf5; margin-bottom: .5rem; }
.se-section-sub { color: #e8a425; font-size: .9rem; margin-bottom: 1.5rem; }

/* ── Module Cards — komplett in HTML gerendert ── */
.se-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 14px;
    margin-bottom: 2rem;
}
.se-card {
    background: #0c1420;
    border: 1px solid #1e2d42;
    border-radius: 14px;
    padding: 1.4rem 1.2rem 1.2rem;
    min-height: 155px;
    display: flex; flex-direction: column;
    transition: border-color .2s, transform .2s;
    text-decoration: none;
}
.se-card:hover {
    border-color: #4d9fff;
    transform: translateY(-3px);
}
.se-card-emoji { font-size: 2rem; line-height: 1; margin-bottom: .5rem; }
.se-card-title {
    font-size: 1rem; font-weight: 700;
    color: #dde8f5; margin-bottom: .35rem;
}
.se-card-link {
    font-size: .83rem; font-weight: 600;
    color: #4d9fff; margin-bottom: auto;
    text-decoration: none;
}
.se-card-cap {
    font-size: .8rem; font-weight: 500;
    color: #e8a425;
    line-height: 1.45;
    margin-top: .7rem;
    padding-top: .6rem;
    border-top: 1px solid #1a2a3a;
}

/* ── Feature Cards ── */
.se-feat { background: #0c1420; border: 1px solid #1a2538; border-radius: 14px; padding: 1.6rem 1.4rem; height: 100%; }
.se-feat-icon { width: 42px; height: 42px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 1.3rem; margin-bottom: 1rem; }
.ic-b { background: rgba(30,110,240,0.15); }
.ic-g { background: rgba(232,164,37,0.12); }
.ic-t { background: rgba(20,184,166,0.12); }
/* Feature Titel: Blau wie Sektion-3-Überschrift */
.se-feat h3 { font-size: .95rem; font-weight: 700; color: #4d9fff; margin-bottom: .4rem; }
.se-feat p { font-size: .82rem; color: #e8a425; line-height: 1.6; margin: 0; }

/* ── Stats ── */
.se-stat { background: #0c1420; border: 1px solid #1a2538; border-radius: 14px; padding: 1.8rem 1rem; text-align: center; }
.se-stat big { display: block; font-size: 2rem; font-weight: 800; color: #e8edf5; margin-bottom: .2rem; }
.se-stat small { font-size: .72rem; color: #3a5070; text-transform: uppercase; letter-spacing: 1px; }

/* ── CTA ── */
.se-cta-box { background: linear-gradient(135deg,#0a1020,#0e1830); border: 1px solid #1a2538; border-radius: 16px; padding: 2.5rem 2rem; }
.se-cta-title { font-size: 1.5rem; font-weight: 800; color: #e8edf5; margin-bottom: .5rem; }
.se-cta-sub { color: #e8a425; font-size: .9rem; margin-bottom: 1.2rem; }

/* ── Chart wrapper ── */
.se-chart-wrap { background: #080d14; border: 1px solid #1a2538; border-radius: 14px; overflow: hidden; margin-bottom: 1rem; }

/* ── Footer ── */
.se-footer { text-align: center; padding: 1.5rem 0 .5rem; color: #2a3a50; font-size: .78rem; border-top: 1px solid #111820; }
.se-footer a { color: #2a4060; text-decoration: none; margin: 0 .6rem; }
.se-footer a:hover { color: #4d9fff; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# BREVO
# ══════════════════════════════════════════════════════════════
def _subscribe_email(email: str) -> tuple[bool, str]:
    brevo_ok = False
    try:
        api_key = st.secrets["brevo_api_key"]
        list_id = int(st.secrets["brevo_list_id"])
    except (KeyError, FileNotFoundError):
        brevo_ok = True  # Dev-Modus — kein Brevo
        _save_to_supabase(email, brevo_synced=False)
        return True, "dev_mode"
    try:
        resp = requests.post(
            "https://api.brevo.com/v3/contacts",
            json={"email": email, "listIds": [list_id], "updateEnabled": True},
            headers={"accept":"application/json","content-type":"application/json","api-key":api_key},
            timeout=5,
        )
        if resp.status_code in (200, 201, 204):
            brevo_ok = True
        elif resp.status_code == 400:
            return False, "Ungültige E-Mail-Adresse."
        else:
            return False, f"Brevo-Fehler {resp.status_code}"
    except requests.exceptions.Timeout:
        return False, "Timeout — bitte nochmal versuchen."
    except Exception as e:
        return False, str(e)

    # Immer auch in Supabase speichern
    _save_to_supabase(email, brevo_synced=brevo_ok)
    return True, ""


def _save_to_supabase(email: str, brevo_synced: bool = False):
    """Subscriber parallel in Supabase speichern."""
    try:
        from shared.supabase_client import subscribe_email
        subscribe_email(
            email=email,
            source="website",
            brevo_synced=brevo_synced,
        )
    except Exception as e:
        # Supabase-Fehler soll Anmeldung nicht blockieren
        try:
            from shared.logger import error_logger
            error_logger.error(f"Supabase subscriber save failed: {email} — {e}")
        except Exception:
            pass


def _handle_submit(email: str):
    val = email.strip()
    if not val or "@" not in val or "." not in val:
        st.error("Bitte gib eine gültige E-Mail-Adresse ein."); return
    with st.spinner("Einen Moment …"):
        ok, err = _subscribe_email(val)
    if ok:
        if err == "dev_mode": st.info(f"🛠️ Dev-Modus: '{val}' würde in Brevo eingetragen.")
        else: st.success("✅ Du bist dabei! Check deine Inbox."); st.balloons()
    else: st.error(f"Fehler: {err}")


# ══════════════════════════════════════════════════════════════
# SEKTION 1 — HERO
# ══════════════════════════════════════════════════════════════
st.markdown("""
<div class="se-hero">
  <div class="se-eyebrow">● Early Access läuft</div>
  <div class="se-h1">
    <span class="gold">Seasonal</span><span class="blue">Edge</span>&nbsp;<span class="white">BETA</span>
  </div>
  <div class="se-sub">
    Sei unter den Ersten: Entdecke saisonale Trading-Chancen,<br>
    bevor der Markt sie sieht. Early Access jetzt!
  </div>
  <div class="se-badge">🔒 Nur 100 Early-Bird-Plätze · Lifetime-Zugang für erste 100</div>
</div>
""", unsafe_allow_html=True)

h1, h2, h3 = st.columns([2,1,2])
with h2:
    if st.button("🚀 Beta beitreten", use_container_width=True, type="primary"):
        st.session_state["show_email"] = True
if st.session_state.get("show_email"):
    e1, e2 = st.columns([3,1])
    with e1:
        hero_mail = st.text_input("Email", placeholder="name@beispiel.de",
                                   label_visibility="collapsed", key="hero_mail")
    with e2:
        if st.button("OK", use_container_width=True, key="hero_ok"):
            _handle_submit(hero_mail)
    st.caption("🇩🇪 DSGVO-konform · Kein Spam · Jederzeit abmeldbar")


# ══════════════════════════════════════════════════════════════
# SEKTION 2 — ALLE 12 MODULE als HTML-Grid mit st.page_link
# Die Cards sind in reinem HTML für sauberes Layout.
# Die st.page_link-Elemente folgen darunter — unsichtbar positioniert
# als echte Streamlit-Navigation.
# ══════════════════════════════════════════════════════════════
st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<div class="se-section-label">Analyse-Module</div>', unsafe_allow_html=True)
st.markdown('<div class="se-section-title">Alle 12 Module auf einen Blick</div>', unsafe_allow_html=True)
st.markdown('<div class="se-section-sub">Klicke auf einen Titel — du landest direkt im Modul.</div>', unsafe_allow_html=True)

_PAGES = [
    ("pages/1_📊_Erweiterte_Analyse.py",          "📊", "Erweiterte Analyse",     "Jahres-Saisonalität, Dekaden- & Präsidentenzyklus"),
    ("pages/2_🔄_Turn_of_the_Month.py",           "🔄", "Turn of the Month",      "Monatswechsel-Effekt, t0=0%-Normalisierung"),
    ("pages/3_📅_Feiertags_Effekt.py",            "🎉", "Feiertags-Effekt",       "12 NYSE-Feiertage, Pre/Post-Holiday-Bias"),
    ("pages/4_📅_Weekday_Analyse.py",             "📅", "Weekday Analyse",        "Wochentag-Renditen, SMA/RSI-Filter"),
    ("pages/5_📆_Monthly_Performance.py",         "📆", "Monthly Performance",    "Monats-Performance, Heatmap, Boxplots"),
    ("pages/6_🏛️_Zentralbanken.py",               "🏛️", "Zentralbanken",          "Fed, ECB, BOE, BOJ — Zinsentscheide & Minutes"),
    ("pages/7_🌕_Mondphasen.py",                  "🌕", "Mondphasen",             "Voll-/Neumond-Effekt, Meeus-Algorithmus"),
    ("pages/8_🧠_TruePath.py",                    "🧠", "TruePath KI",            "KI-Score 0–100, Pattern-Matching"),
    ("pages/9_🚦_Strategien.py",                  "🚦", "Strategien",             "Käppel-Strategien, Saisonale Regelwerke"),
    ("pages/10_📅_OPEX.py",                       "📉", "OPEX / Verfallstag",     "Triple/Quad Witching, Expiry-Bias"),
    ("pages/11_Intra_Decade_Seasonality_1.py",    "🔟", "Intra-Decade",           "X0–X9 Jahres-Zyklen im Vergleich"),
    ("pages/12_🌙_Overnight_vs_Intraday.py",      "🌙", "Overnight vs. Intraday", "Overnight-Gap vs. Intraday-Rendite"),
]

# Zeile 1: Module 0-2
r1c1, r1c2, r1c3 = st.columns(3, gap="medium")
# Zeile 2: Module 3-5
r2c1, r2c2, r2c3 = st.columns(3, gap="medium")
# Zeile 3: Module 6-8
r3c1, r3c2, r3c3 = st.columns(3, gap="medium")
# Zeile 4: Module 9-11
r4c1, r4c2, r4c3 = st.columns(3, gap="medium")

_col_map = [r1c1,r1c2,r1c3, r2c1,r2c2,r2c3, r3c1,r3c2,r3c3, r4c1,r4c2,r4c3]

for col, (path, emoji, title, cap) in zip(_col_map, _PAGES):
    with col:
        # Card-Rahmen
        st.markdown(
            f"""<div style="background:#0c1420;border:1px solid #1e2d42;border-radius:14px;
            padding:1.2rem 1.2rem 0.8rem;margin-bottom:2px;">
              <div style="font-size:2rem;line-height:1;margin-bottom:.5rem;">{emoji}</div>
              <div style="font-size:1rem;font-weight:700;color:#dde8f5;margin-bottom:.2rem;">{title}</div>
            </div>""",
            unsafe_allow_html=True,
        )
        # Klickbarer page_link — direkt unter dem Emoji/Titel-Block
        st.page_link(
            page=path,
            label=f"📂 {title} öffnen →",
            use_container_width=True,
        )
        # Gold-Caption
        st.markdown(
            f'<div style="font-size:.8rem;font-weight:500;color:#e8a425;'
            f'padding:.3rem .2rem .8rem;line-height:1.45;">{cap}</div>',
            unsafe_allow_html=True,
        )

st.markdown("<br>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# SEKTION 3 — SPLIT-SLIDER: Spaghetti → Durchschnitt
# ══════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown('<div class="se-section-label">Saisonalitäts-Analyse</div>', unsafe_allow_html=True)
st.markdown('<div class="se-section-title">Vom Rauschen zum klaren Trend</div>', unsafe_allow_html=True)
st.markdown(
    '<div style="color:#e8a425;font-size:.9rem;margin-bottom:1rem;">'
    'Ziehe den Slider — links alle Einzeljahre, rechts der saisonale Durchschnitt.'
    '</div>',
    unsafe_allow_html=True,
)

# Daten laden — nutzt shared/yahoo_downloader.py (Yahoo + Stooq-Backfill)
try:
    # Imports mit Fallback auf direkte Pfade
    try:
        from shared.dj_data import load_dj_data
        from shared.split_slider import render_split_slider
    except ImportError:
        import importlib.util as _ilu
        for _mod, _fname in [("dj_data", "dj_data.py"), ("split_slider", "split_slider.py")]:
            _path = os.path.join(_project_dir, "shared", _fname)
            if os.path.exists(_path):
                _spec = _ilu.spec_from_file_location(_mod, _path)
                _m = _ilu.module_from_spec(_spec)
                _spec.loader.exec_module(_m)
                if _mod == "dj_data":
                    load_dj_data = _m.load_dj_data
                else:
                    render_split_slider = _m.render_split_slider

    _df, _src = load_dj_data(_project_dir)
    if _src == "synthetic":
        st.markdown(
            '<div style="background:#0c1420;border:1px solid #2a3a1a;border-radius:8px;'
            'padding:.6rem 1rem;margin-bottom:.8rem;font-size:.78rem;color:#a0b880;">'
            '📶 Offline-Modus — Chart zeigt historische Jahresrenditen (1980–2024). '
            'Live-Daten werden geladen sobald eine Internetverbindung verfügbar ist.'
            '</div>',
            unsafe_allow_html=True,
        )
    _n_years = _df['year'].nunique() if 'year' in _df.columns else 0
    _src_label = {"live+synthetic": "Live + Hist.", "synthetic": "Hist. 1950–2024"}.get(_src, _src)
    _info = f"{_n_years} Jahre · {_src_label}"
    if _src == "synthetic":
        st.markdown(
            '<div style="background:#0c1420;border:1px solid #2a3a1a;border-radius:8px;'
            'padding:.5rem 1rem;margin-bottom:.6rem;font-size:.78rem;color:#a0b880;">'
            '📶 Offline-Modus — historische Jahresrenditen 1950–2024. '
            'Live-Daten beim nächsten Start mit Internetverbindung.'
            '</div>',
            unsafe_allow_html=True,
        )
    render_split_slider(_df, height=520, info=_info)

except Exception as _e:
    import traceback as _tb
    st.error(f"Split-Slider Fehler: {_e}")
    st.code(_tb.format_exc(), language="python")

st.markdown("<br>", unsafe_allow_html=True)

# Dow Jones Wars Chart (bestehendes HTML, optional)
_html_path = os.path.join(_project_dir, "dow_jones_wars.html")
if os.path.exists(_html_path):
    st.markdown('<div class="se-section-label">Markthistorie</div>', unsafe_allow_html=True)
    st.markdown('<div class="se-section-title">Der Dow Jones seit 1886</div>', unsafe_allow_html=True)
    with open(_html_path, "r", encoding="utf-8") as _f:
        _html_content = _f.read()
    _b64 = base64.b64encode(_html_content.encode()).decode()
    st.markdown(
        f'<div class="se-chart-wrap">'
        f'<iframe src="data:text/html;base64,{_b64}" '
        f'width="100%" height="900" frameborder="0" scrolling="no" '
        f'style="border:none;display:block;"></iframe>'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# CRASH-FRUEHWARNUNG (Ampel)
# ══════════════════════════════════════════════════════════════
try:
    from shared.data import download_data as _dl, preprocess as _pp
    from shared.anomaly_engine import compute_market_regime, TRAFFIC_LIGHT_LABELS

    _spy_raw = _dl("SPY")
    if _spy_raw is not None and not _spy_raw.empty:
        _spy_df = _pp(_spy_raw)
        _regime = compute_market_regime(_spy_df)
        _tl = TRAFFIC_LIGHT_LABELS.get(_regime["traffic_light"], TRAFFIC_LIGHT_LABELS["grey"])

        st.markdown("---")
        st.markdown('<div class="se-section-label">Markt-Regime</div>', unsafe_allow_html=True)
        st.markdown('<div class="se-section-title">Crash-Fruehwarnung (KI)</div>', unsafe_allow_html=True)

        _rc1, _rc2, _rc3, _rc4 = st.columns(4, gap="small")
        with _rc1:
            st.markdown(
                f'<div style="background:#0c1420;border:2px solid {_tl["color"]};border-radius:14px;'
                f'padding:1.2rem;text-align:center;">'
                f'<div style="font-size:2.5rem;">{_tl["emoji"]}</div>'
                f'<div style="color:{_tl["color"]};font-weight:700;font-size:1rem;">{_tl["label"]}</div>'
                f'</div>', unsafe_allow_html=True)
        with _rc2:
            st.metric("Risk-Score", f'{_regime["risk_score"]:.0f}/100')
        with _rc3:
            st.metric("Vola (5d)", f'{_regime.get("volatility_5d", 0):.2f}%')
        with _rc4:
            st.metric("Drawdown", f'{_regime.get("drawdown", 0):.1f}%')

        st.caption(f'{_tl["desc"]} Basis: SPY, Isolation Forest auf Rendite/Volatilitaet/Drawdown.')

except Exception:
    pass

st.markdown("<br>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# SEKTION 4 — FEATURES
# ══════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown('<div class="se-section-label">Was dich erwartet</div>', unsafe_allow_html=True)
st.markdown('<div class="se-section-title">Drei Werkzeuge. Ein Vorteil.</div>', unsafe_allow_html=True)

f1, f2, f3 = st.columns(3, gap="medium")
_PT = 'style="color:#e8a425;font-size:.82rem;line-height:1.6;margin:0;"'
_P  = lambda t: f'<div {_PT}>{t}</div>'
# FIX 3: h3 explizit color:white — Streamlit überschreibt h3 sonst mit eigenem Grau
# FIX 4: min-height:160px + display:flex/flex-direction:column → gleiche Kartenhöhe
_CARD = (
    'style="background:#0c1420;border:1px solid #1a2538;border-radius:14px;'
    'padding:1.6rem 1.4rem;min-height:180px;display:flex;flex-direction:column;"'
)
_H3 = 'style="color:#ffffff !important;font-size:.95rem;font-weight:700;margin-bottom:.4rem;"'

with f1:
    st.markdown(f"""<div {_CARD}>
      <div class="se-feat-icon ic-b" style="width:42px;height:42px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:1.3rem;margin-bottom:1rem;background:rgba(30,110,240,0.15);">📊</div>
      <h3 {_H3}>Saisonaler Screener</h3>
      {_P('Scanne alle Instrumente nach historisch starken Phasen. Filtere nach Win-Rate, Median-Rendite und Drawdown auf Knopfdruck.')}
    </div>""", unsafe_allow_html=True)
with f2:
    st.markdown(f"""<div {_CARD}>
      <div class="se-feat-icon ic-g" style="width:42px;height:42px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:1.3rem;margin-bottom:1rem;background:rgba(232,164,37,0.12);">🧠</div>
      <h3 {_H3}>TruePath KI-Score</h3>
      {_P('Unser KI-Algorithmus bewertet jedes Setup 0–100 nach statistischer Signifikanz. Nur A-Setups, kein Rauschen.')}
    </div>""", unsafe_allow_html=True)
with f3:
    st.markdown(f"""<div {_CARD}>
      <div class="se-feat-icon ic-t" style="width:42px;height:42px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:1.3rem;margin-bottom:1rem;background:rgba(20,184,166,0.12);">🌖</div>
      <h3 {_H3}>Event-Analysen & Alerts</h3>
      {_P('FOMC, Mondphasen, Feiertage — alle Ereignisse mit historischem Markteinfluss auf einen Blick.')}
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# SEKTION 5 — STATS
# ══════════════════════════════════════════════════════════════
def _stat(num, label):
    return (
        f'<div style="background:#0c1420;border:1px solid #1a2538;border-radius:14px;'
        f'padding:1.8rem 1rem;text-align:center;">'
        f'<div style="font-size:2rem;font-weight:800;color:#e8edf5;margin-bottom:.4rem;">{num}</div>'
        f'<div style="font-size:.72rem;font-weight:600;color:#e8a425;'
        f'text-transform:uppercase;letter-spacing:1.5px;">{label}</div>'
        f'</div>'
    )

s1, s2, s3, s4 = st.columns(4, gap="small")
with s1:
    st.markdown(_stat("500+", "Instrumente (Beta)"), unsafe_allow_html=True)
with s2:
    st.markdown(_stat("100 J.", "Datenhistorie"), unsafe_allow_html=True)
with s3:
    st.markdown(_stat("12", "Analyse-Module"), unsafe_allow_html=True)
with s4:
    st.markdown(_stat("KI", "TruePath Score"), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# SEKTION 6 — CTA + BREVO
# ══════════════════════════════════════════════════════════════
st.markdown("---")
cta_l, cta_r = st.columns([2,1], gap="large")
with cta_l:
    st.markdown("""<div class="se-cta-box">
      <div class="se-cta-title">Bereit, die Märkte mit System zu schlagen?</div>
      <div class="se-cta-sub">Trag dich ein und sichere dir deinen kostenlosen Early-Bird Zugang.<br>
      Lifetime-Zugang für die ersten 100 Nutzer — kein Abo, kein Risiko.</div>
    </div>""", unsafe_allow_html=True)
with cta_r:
    with st.form("cta_form"):
        cta_email = st.text_input("E-Mail", placeholder="name@beispiel.de",
                                   label_visibility="collapsed", key="cta_mail")
        if st.form_submit_button("Jetzt Platz sichern →", use_container_width=True):
            _handle_submit(cta_email)
    st.caption("🇩🇪 DSGVO-konform · Kein Spam · Jederzeit abmeldbar")


# ══════════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════════
st.markdown("""
<div class="se-footer">
  © 2026 SeasonalEdge — Keine Anlageberatung. Trading birgt Risiken.<br>
  <a href="#">Impressum</a>
  <a href="#">Datenschutz</a>
  <a href="#">Risikohinweis</a>
</div>
""", unsafe_allow_html=True)
