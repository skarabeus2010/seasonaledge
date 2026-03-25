# pages/0_🏠_Home.py
# ============================================================
# STARTSEITE — SeasonalEdge Light Live v1.0
# ============================================================

import sys, os, pathlib, requests  # base64 entfernt (Iframe deaktiviert)

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
    page_title="SeasonalEdge – Saisonale Börsenanalyse & Trading-Signale",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

from shared.design import inject_se_css
inject_se_css()

# Google Search Console Verifizierung
st.markdown(
    '<meta name="google-site-verification" content="46lbAINaqCQSU5pWAplt6WioigjnIc3mmLMBnCteMwk">',
    unsafe_allow_html=True,
)

# ══════════════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif !important; }
#MainMenu, footer { visibility: hidden; }
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

/* ── Newsletter Button gold ── */
[data-testid="stFormSubmitButton"] button[kind="primaryFormSubmit"],
[data-testid="stFormSubmitButton"] button[type="submit"] {
    background-color: #e8a425 !important;
    border-color: #e8a425 !important;
    color: #080c12 !important;
    font-weight: 700 !important;
}
[data-testid="stFormSubmitButton"] button:hover {
    background-color: #d4941f !important;
    border-color: #d4941f !important;
}
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
  <!-- SVG Saisonalitaets-Chart im Hintergrund -->
  <svg style="position:absolute;top:0;left:0;width:100%;height:100%;opacity:0.25;pointer-events:none;"
       viewBox="0 0 1200 400" preserveAspectRatio="none">
    <!-- Vertikale Grid-Linien (Monate) -->
    <line x1="100" y1="50" x2="100" y2="380" stroke="rgba(255,255,255,0.06)" stroke-width="1"/>
    <line x1="200" y1="50" x2="200" y2="380" stroke="rgba(255,255,255,0.06)" stroke-width="1"/>
    <line x1="300" y1="50" x2="300" y2="380" stroke="rgba(255,255,255,0.06)" stroke-width="1"/>
    <line x1="400" y1="50" x2="400" y2="380" stroke="rgba(255,255,255,0.06)" stroke-width="1"/>
    <line x1="500" y1="50" x2="500" y2="380" stroke="rgba(255,255,255,0.06)" stroke-width="1"/>
    <line x1="600" y1="50" x2="600" y2="380" stroke="rgba(255,255,255,0.06)" stroke-width="1"/>
    <line x1="700" y1="50" x2="700" y2="380" stroke="rgba(255,255,255,0.06)" stroke-width="1"/>
    <line x1="800" y1="50" x2="800" y2="380" stroke="rgba(255,255,255,0.06)" stroke-width="1"/>
    <line x1="900" y1="50" x2="900" y2="380" stroke="rgba(255,255,255,0.06)" stroke-width="1"/>
    <line x1="1000" y1="50" x2="1000" y2="380" stroke="rgba(255,255,255,0.06)" stroke-width="1"/>
    <line x1="1100" y1="50" x2="1100" y2="380" stroke="rgba(255,255,255,0.06)" stroke-width="1"/>
    <!-- Horizontale Grid-Linien -->
    <line x1="0" y1="150" x2="1200" y2="150" stroke="rgba(255,255,255,0.04)" stroke-width="1"/>
    <line x1="0" y1="250" x2="1200" y2="250" stroke="rgba(255,255,255,0.04)" stroke-width="1"/>
    <!-- Saisonale Hauptkurve (aufsteigend mit Dips) -->
    <path d="M0,320 C40,315 80,310 120,300 C160,290 200,285 240,275
             C280,270 320,280 360,290 C400,275 440,260 480,250
             C520,245 560,258 600,248 C640,235 680,220 720,210
             C760,200 800,195 840,185 C880,178 920,195 960,180
             C1000,165 1040,150 1080,140 C1120,132 1160,125 1200,115"
          fill="none" stroke="#4d9fff" stroke-width="3"/>
    <!-- Flaechenfuellung unter der Kurve -->
    <path d="M0,320 C40,315 80,310 120,300 C160,290 200,285 240,275
             C280,270 320,280 360,290 C400,275 440,260 480,250
             C520,245 560,258 600,248 C640,235 680,220 720,210
             C760,200 800,195 840,185 C880,178 920,195 960,180
             C1000,165 1040,150 1080,140 C1120,132 1160,125 1200,115
             L1200,400 L0,400 Z"
          fill="url(#heroGrad)"/>
    <defs>
      <linearGradient id="heroGrad" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#4d9fff" stop-opacity="0.15"/>
        <stop offset="100%" stop-color="#4d9fff" stop-opacity="0"/>
      </linearGradient>
    </defs>
    <!-- Volatilitaetsband oben -->
    <path d="M0,290 C100,275 200,260 300,245 C400,230 500,225 600,215
             C700,200 800,180 900,160 C1000,145 1100,120 1200,95"
          fill="none" stroke="#4d9fff" stroke-width="1" stroke-dasharray="4,6" opacity="0.4"/>
    <!-- Volatilitaetsband unten -->
    <path d="M0,350 C100,340 200,330 300,315 C400,310 500,300 600,285
             C700,270 800,260 900,250 C1000,235 1100,225 1200,140"
          fill="none" stroke="#4d9fff" stroke-width="1" stroke-dasharray="4,6" opacity="0.4"/>
    <!-- Goldene Trendlinie -->
    <path d="M0,330 C200,310 400,280 600,255 C800,230 1000,190 1200,130"
          fill="none" stroke="#e8a425" stroke-width="2" opacity="0.7"/>
    <!-- Gelbe Punkte an den Tiefpunkten (saisonale Dips) -->
    <circle cx="360" cy="290" r="5" fill="#e8a425" opacity="0.9"/>
    <circle cx="560" cy="258" r="5" fill="#e8a425" opacity="0.9"/>
    <circle cx="920" cy="195" r="5" fill="#e8a425" opacity="0.9"/>
    <!-- Blaue Punkte an Hochpunkten -->
    <circle cx="240" cy="275" r="4" fill="#4d9fff" opacity="0.7"/>
    <circle cx="480" cy="250" r="4" fill="#4d9fff" opacity="0.7"/>
    <circle cx="840" cy="185" r="4" fill="#4d9fff" opacity="0.7"/>
    <circle cx="1200" cy="115" r="4" fill="#4d9fff" opacity="0.7"/>
    <!-- Kleine Annotations-Linien von Dip-Punkten -->
    <line x1="360" y1="290" x2="360" y2="310" stroke="#e8a425" stroke-width="1" opacity="0.5"/>
    <line x1="560" y1="258" x2="560" y2="278" stroke="#e8a425" stroke-width="1" opacity="0.5"/>
    <line x1="920" y1="195" x2="920" y2="215" stroke="#e8a425" stroke-width="1" opacity="0.5"/>
  </svg>
  <div class="se-eyebrow">Traditionelle Saisonalitaet trifft Intelligenz.</div>
  <div class="se-h1">
    <span class="gold">Seasonal</span><span class="blue">Alpha</span>&nbsp;<span class="white">BETA</span>
  </div>
  <div class="se-sub">
    Datengetriebene Saisonalitaets-Analyse mit KI.<br>
    Bis zu 131 Jahre Boersengeschichte in Charts. 15 Machine-Learning-Modelle.<br>
    Erkenne Muster, bevor der Markt sie sieht.
  </div>
  <div class="se-badge">More. Coming. Soon.</div>
</div>
""", unsafe_allow_html=True)

# ── Begrüßungstext ──
st.markdown("""
<div style="max-width:800px;margin:0 auto 2rem;">
  <h2 style="color:#e8edf5;font-size:clamp(1.6rem,4vw,2.4rem);font-weight:800;text-align:center;margin-bottom:1.2rem;letter-spacing:-.5px;">
    Willkommen bei SeasonalAlpha – der naechsten Generation der Marktanalyse
  </h2>
  <p style="color:#a0b0c5;font-size:1.15rem;line-height:1.8;text-align:center;margin-bottom:1.2rem;">
    Wir erweitern traditionelle Saisonalitaets-Charts um modernste Kuenstliche Intelligenz
    und geben dir Tools an die Hand, die auf dem Markt einzigartig sind.
  </p>
  <ul style="color:#a0b0c5;font-size:1.05rem;line-height:1.9;list-style:none;padding:0;">
    <li style="margin-bottom:.8rem;">
      <strong style="color:#e8a425;">Klassik trifft High-Tech:</strong>
      Wir durchsuchen bis zu 130 Jahre Marktdaten nach Dekaden-, Jahres- und Monatszyklen.
      Wir nehmen auch einzelne Handelstage unter die Lupe, genauso wie Events wie z.B.
      Notenbanksitzungen, OPEX und Mondphasen und geben Dir konkrete Strategien an die Hand.
    </li>
    <li style="margin-bottom:.8rem;">
      <strong style="color:#4d9fff;">KI-gestuetzte Prognosen:</strong>
      15 fortschrittliche Machine-Learning-Modelle erkennen Anomalien,
      bewerten Crash-Risiken und identifizieren optimal getimte Wendepunkte.
    </li>
    <li style="margin-bottom:.8rem;">
      <strong style="color:#4d9fff;">Entdecke unsere innovativen Basis-Charts sofort</strong>
      – kostenlos und ohne vorherige Registrierung.
    </li>
    <li>
      <strong style="color:#e8a425;">Die Beta-Phase hat gerade erst begonnen.</strong>
      Freu Dich jetzt schon auf innovativen und tech-getriebene Analysen!
    </li>
  </ul>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# SEKTION 2 — ALLE 12 MODULE als HTML-Grid mit st.page_link
# Die Cards sind in reinem HTML für sauberes Layout.
# Die st.page_link-Elemente folgen darunter — unsichtbar positioniert
# als echte Streamlit-Navigation.
# ══════════════════════════════════════════════════════════════
st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<div class="se-section-label">Analyse-Module</div>', unsafe_allow_html=True)
st.markdown('<div class="se-section-title">Deine SeasonalAlpha Suite</div>', unsafe_allow_html=True)
st.markdown('<div class="se-section-sub">Klicke auf ein Modul — du landest direkt in der Analyse.</div>', unsafe_allow_html=True)

# ── 9 Light-Live Pages (3×3 Grid) ──
_LIGHT_PAGES = [
    ("pages/01_Dekadenzyklus.py",            "📊", "Dekadenzyklus",          "131 Jahre DJI — Dekaden-Kohorten & KI"),
    ("pages/02_Jahreszyklus.py",             "📈", "Jahreszyklus",           "Saisonaler Jahresverlauf & Anomalie-Radar"),
    ("pages/03_Monatszyklus.py",             "📆", "Monatszyklus",           "Monatliche Saisonalität — Heatmap & Boxplots"),
    ("pages/04_Wochentage.py",               "📅", "Wochentage",             "Wochentagseffekt — Montag bis Freitag"),
    ("pages/05_Monatswechsel.py",            "🔄", "Monatswechsel",          "Turn of the Month — erste/letzte 3 Tage"),
    ("pages/06_Mondphasen.py",               "🌕", "Mondphasen",             "Vollmond & Neumond — Börsen-Effekt"),
    ("pages/07_Januar_Trifecta.py",          "🚦", "Januar-Trifecta",        "Ampelsystem — 3 Signale für das Börsenjahr"),
    ("pages/08_Kriegszeiten.py",             "⚔️", "Kriegszeiten",           "Krieg vs. Frieden — Saisonalität im Vergleich"),
    ("pages/11_Saisonal_Events_Kalender.py", "🗓️", "Saisonal-Kalender",      "Fed, EZB, OPEX, Mond & Feiertage — 12 Monate"),
    ("pages/12_Backtest_Engine.py",          "🔬", "Backtest Engine",        "KI-Optimierer: Events, Stop-Loss, Walk-Forward"),
]

# CSS: page_link überlagert die Kachel — ganze Card ist klickbar
st.markdown("""
<style>
.se-card-wrap { position: relative; }
.se-card-wrap .se-card {
    background: #0c1420; border: 1px solid #1e2d42; border-radius: 14px;
    padding: 1rem 1rem 0.6rem; min-height: 90px;
    transition: border-color 0.2s, background 0.2s;
}
.se-card-wrap:hover .se-card {
    border-color: #4d9fff; background: #0e1828; cursor: pointer;
}
/* page_link: Text unsichtbar, über die Card gelegt */
[data-testid="stVerticalBlock"] [data-testid="stPageLink"] {
    margin-top: -95px !important; position: relative; z-index: 10;
    height: 95px !important; overflow: hidden;
}
[data-testid="stVerticalBlock"] [data-testid="stPageLink"] a,
[data-testid="stVerticalBlock"] [data-testid="stPageLink"] span,
[data-testid="stVerticalBlock"] [data-testid="stPageLink"] p {
    color: transparent !important; font-size: 0 !important;
}
[data-testid="stVerticalBlock"] [data-testid="stPageLink"] a {
    display: block !important; width: 100% !important;
    height: 95px !important; min-height: 95px !important;
}
</style>
""", unsafe_allow_html=True)

for row_idx in range(3):
    cols = st.columns(3, gap="medium")
    for col_idx in range(3):
        card_idx = row_idx * 3 + col_idx
        if card_idx >= len(_LIGHT_PAGES):
            continue
        path, emoji, title, cap = _LIGHT_PAGES[card_idx]
        with cols[col_idx]:
            st.markdown(
                f"""<div class="se-card-wrap"><div class="se-card">
                  <div style="font-size:1.4rem;line-height:1;margin-bottom:.4rem;">{emoji}</div>
                  <div style="font-size:.85rem;font-weight:700;color:#dde8f5;margin-bottom:.15rem;">{title}</div>
                  <div style="font-size:.7rem;color:#5a6e85;line-height:1.3;">{cap}</div>
                </div></div>""",
                unsafe_allow_html=True,
            )
            # page_link wird per CSS über die Card gezogen (unsichtbar, aber klickbar)
            st.page_link(page=path, label=title, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# SEKTION 3 — SPLIT-SLIDER: Spaghetti → Durchschnitt
# ══════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown('<div class="se-section-label">Saisonalitäts-Analyse</div>', unsafe_allow_html=True)
st.markdown('<div class="se-section-title">Vom Rauschen zum Trend</div>', unsafe_allow_html=True)
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

# Dow Jones Wars Chart — deaktiviert für Light Live (Performance)
# Wird in der Vollversion wieder aktiviert.


st.markdown("<br>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# SEKTION 5 — FEATURE STATS (Glasmorphismus + Glow + Sinuswelle)
# ══════════════════════════════════════════════════════════════

st.markdown("""
<style>
.se-glass-wrap {
    position: relative;
    border-radius: 16px;
    overflow: visible;
    padding: 2.5rem 1rem;
}
.se-glass-bg {
    position: absolute; top: 0; left: 0; width: 100%; height: 100%;
    pointer-events: none; z-index: 0;
}
.se-glass-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1rem;
    position: relative;
    z-index: 1;
}
.se-glass-card {
    background: rgba(12, 20, 32, 0.65);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border: 0.5px solid rgba(255,255,255,0.1);
    border-radius: 14px;
    padding: 1.6rem 1rem;
    text-align: center;
    transition: box-shadow 0.3s ease, border-color 0.3s ease, transform 0.3s ease;
    cursor: default;
}
.se-glass-card:hover {
    transform: translateY(-3px);
}
.se-glass-card.blue:hover {
    box-shadow: 0 0 30px rgba(77,159,255,0.25), inset 0 0 20px rgba(77,159,255,0.05);
    border-color: rgba(77,159,255,0.4);
}
.se-glass-card.gold:hover {
    box-shadow: 0 0 30px rgba(232,164,37,0.25), inset 0 0 20px rgba(232,164,37,0.05);
    border-color: rgba(232,164,37,0.4);
}
.se-glass-card.hero:hover {
    box-shadow: 0 0 40px rgba(232,164,37,0.35), inset 0 0 25px rgba(232,164,37,0.08);
    border-color: rgba(232,164,37,0.5);
}
.se-glass-num {
    font-size: 2.2rem; font-weight: 800;
    color: #e8edf5; margin-bottom: .3rem;
}
.se-glass-card.hero .se-glass-num {
    font-size: 2.8rem;
    background: linear-gradient(135deg, #e8a425, #f5d78e);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    text-shadow: 0 0 30px rgba(232,164,37,0.3);
}
.se-glass-label {
    font-size: .72rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 1.5px;
}
.se-glass-label.blue { color: #4d9fff; }
.se-glass-label.gold { color: #e8a425; }
/* ── Tooltip für Seit-1896-Kachel ── */
.se-tooltip-wrap { position: relative; }
.se-tooltip {
    visibility: hidden; opacity: 0;
    position: absolute; bottom: calc(100% + 12px); left: 50%;
    transform: translateX(-50%); width: 280px;
    background: rgba(10, 16, 28, 0.95);
    backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
    border: none;
    border-radius: 10px; padding: 0.75rem 1rem;
    font-size: 0.72rem; font-weight: 400; line-height: 1.5;
    color: #c8d6e5; letter-spacing: 0;
    text-transform: none;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.5), 0 0 20px rgba(232, 164, 37, 0.08);
    transition: opacity 0.25s ease, visibility 0.25s ease;
    z-index: 20; pointer-events: none;
}
.se-tooltip::after {
    content: ''; position: absolute; top: 100%; left: 50%;
    transform: translateX(-50%);
    border: 6px solid transparent;
    border-top-color: rgba(10, 16, 28, 0.95);
}
.se-tooltip-wrap:hover .se-tooltip {
    visibility: visible; opacity: 1;
}
@media (max-width: 700px) {
    .se-glass-grid { grid-template-columns: repeat(2, 1fr); }
    .se-tooltip { width: 220px; font-size: 0.68rem; }
}
</style>

<div class="se-glass-wrap">
  <!-- SVG Sinuswelle im Hintergrund -->
  <svg class="se-glass-bg" viewBox="0 0 1200 160" preserveAspectRatio="none">
    <path d="M0,80 C100,40 200,120 300,80 C400,40 500,120 600,80 C700,40 800,120 900,80 C1000,40 1100,120 1200,80"
          fill="none" stroke="rgba(77,159,255,0.07)" stroke-width="2"/>
    <path d="M0,95 C150,55 300,135 450,95 C600,55 750,135 900,95 C1050,55 1200,135 1200,95"
          fill="none" stroke="rgba(232,164,37,0.05)" stroke-width="1.5"/>
    <path d="M0,65 C200,45 400,105 600,65 C800,25 1000,105 1200,65"
          fill="none" stroke="rgba(77,159,255,0.04)" stroke-width="1" stroke-dasharray="6,8"/>
  </svg>

  <div class="se-glass-grid">
    <div class="se-glass-card blue">
      <div class="se-glass-num">500+</div>
      <div class="se-glass-label blue">Basiswerte</div>
    </div>
    <div class="se-glass-card hero gold se-tooltip-wrap">
      <div class="se-glass-num">seit 1896</div>
      <div class="se-glass-label gold">Markthistorie</div>
      <div class="se-tooltip">Gilt f\u00fcr den Dow Jones.</div>
    </div>
    <div class="se-glass-card blue">
      <div class="se-glass-num">15</div>
      <div class="se-glass-label blue">ML-Modelle</div>
    </div>
    <div class="se-glass-card gold">
      <div class="se-glass-num">Open Beta</div>
      <div class="se-glass-label gold">Early Access</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# SEKTION 6 — NEWSLETTER (ganz unten, vor Footer)
# ══════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown(
    '<div style="text-align:center;margin-bottom:1rem;">'
    '<div class="se-section-label">Newsletter</div>'
    '<div class="se-section-title">Jetzt zum Newsletter anmelden!</div>'
    '<div style="color:#e8a425;font-size:.9rem;margin-top:.3rem;">'
    'Erhalten Sie jede Woche einen Newsletter zum Thema Saisonalitaet. Kostenlos.'
    '</div></div>',
    unsafe_allow_html=True,
)

_nl_spacer1, _nl_form_col, _nl_spacer2 = st.columns([1, 2, 1])
with _nl_form_col:
    with st.form("newsletter_form"):
        nl_email = st.text_input("E-Mail", placeholder="name@beispiel.de",
                                  label_visibility="collapsed", key="nl_mail")
        if st.form_submit_button("Jetzt anmelden", use_container_width=True, type="primary"):
            _handle_submit(nl_email)
    st.caption("DSGVO-konform · Kein Spam · Jederzeit abmeldbar")


# ══════════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════════
st.markdown("""
<div class="se-footer">
  &copy; 2026 SeasonalAlpha — Keine Anlageberatung. Trading birgt Risiken.<br>
  <a href="#">Impressum</a>
  <a href="#">Datenschutz</a>
  <a href="#">Risikohinweis</a>
</div>
""", unsafe_allow_html=True)
