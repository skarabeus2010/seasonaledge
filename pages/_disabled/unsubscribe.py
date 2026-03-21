# pages/unsubscribe.py
# ============================================================
# UNSUBSCRIBE — Newsletter-Abmeldung
# URL: ?page=unsubscribe&email=xxx@yyy.de&token=abc123
# ============================================================

import sys, os, pathlib, hashlib

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

# ── Page Config ──────────────────────────────────────
st.set_page_config(
    page_title="Abmelden — SeasonalEdge",
    page_icon="📧",
    layout="centered",
)

from shared.design import inject_se_css
inject_se_css()


# ── Token-Validierung (DSGVO-Schutz gegen Missbrauch) ──
def _generate_token(email: str) -> str:
    """Einfacher HMAC-Token basierend auf E-Mail + Secret."""
    secret = os.environ.get("UNSUBSCRIBE_SECRET", "seasonaledge-unsub-2026")
    return hashlib.sha256(f"{email.lower().strip()}{secret}".encode()).hexdigest()[:16]


def _validate_token(email: str, token: str) -> bool:
    """Token prüfen."""
    return token == _generate_token(email)


# ── Unsubscribe-Logik ────────────────────────────────
def _do_unsubscribe(unsub_email: str):
    """Aus Supabase + Brevo austragen."""
    success_supa = False
    success_brevo = False

    # 1. Supabase
    try:
        from shared.supabase_client import unsubscribe_email
        success_supa = unsubscribe_email(unsub_email)
    except Exception as e:
        try:
            from shared.logger import error_logger
            error_logger.error(f"Unsubscribe Supabase failed: {unsub_email} — {e}")
        except Exception:
            pass

    # 2. Brevo — Kontakt aus Liste entfernen
    try:
        api_key = st.secrets.get("brevo_api_key", "")
        list_id = st.secrets.get("brevo_list_id", "")
        if api_key and list_id:
            import requests
            resp = requests.post(
                f"https://api.brevo.com/v3/contacts/lists/{list_id}/contacts/remove",
                json={"emails": [unsub_email]},
                headers={
                    "accept": "application/json",
                    "content-type": "application/json",
                    "api-key": api_key,
                },
                timeout=5,
            )
            success_brevo = resp.status_code in (200, 201, 204)
    except Exception:
        pass

    if success_supa or success_brevo:
        st.success("Du wurdest erfolgreich abgemeldet. Du erhältst keine weiteren E-Mails.")
        try:
            from shared.logger import app_logger
            app_logger.info(f"UNSUBSCRIBE | email={unsub_email}")
        except Exception:
            pass
    elif not success_supa:
        st.warning("Diese E-Mail-Adresse wurde nicht gefunden. "
                    "Vielleicht bist du bereits abgemeldet?")


# ── Styling ──────────────────────────────────────────
st.markdown("""
<style>
.unsub-box {
    background: linear-gradient(135deg, #0e1520, #1a2332);
    border: 1px solid #2a3a4e;
    border-radius: 12px;
    padding: 2rem;
    text-align: center;
    margin: 2rem auto;
    max-width: 500px;
}
.unsub-title { font-size: 1.5rem; color: #e8edf5; margin-bottom: 0.5rem; }
.unsub-sub { color: #4a5568; font-size: 0.9rem; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="unsub-box"><div class="unsub-title">SeasonalEdge Newsletter</div></div>',
            unsafe_allow_html=True)

# ── Query-Parameter lesen ────────────────────────────
params = st.query_params
email = params.get("email", "")
token = params.get("token", "")

# ── Fall 1: Direkt-Link aus E-Mail (mit Token) ──────
if email and token:
    if not _validate_token(email, token):
        st.error("Ungültiger Abmelde-Link. Bitte nutze das Formular unten.")
    else:
        st.warning(f"Möchtest du **{email}** wirklich vom Newsletter abmelden?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Ja, abmelden", type="primary", use_container_width=True):
                _do_unsubscribe(email)
        with col2:
            if st.button("Abbrechen", use_container_width=True):
                st.info("Abmeldung abgebrochen. Du bleibst eingetragen.")

# ── Fall 2: Manuelles Formular ───────────────────────
else:
    st.markdown("### Newsletter abmelden")
    st.caption("Gib deine E-Mail-Adresse ein, um dich vom Newsletter abzumelden.")

    with st.form("unsubscribe_form"):
        unsub_email = st.text_input(
            "E-Mail-Adresse",
            placeholder="name@beispiel.de",
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button("Abmelden", use_container_width=True)

        if submitted:
            val = unsub_email.strip()
            if not val or "@" not in val or "." not in val:
                st.error("Bitte gib eine gültige E-Mail-Adresse ein.")
            else:
                _do_unsubscribe(val)


# ── Footer ────────────────────────────────────────────
st.markdown("---")
st.caption("🇩🇪 DSGVO-konform · Deine Daten werden nicht weitergegeben.")
