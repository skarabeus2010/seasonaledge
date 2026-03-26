# pages/99_Impressum.py
# ============================================================
# IMPRESSUM — SeasonAlpha
# ============================================================

import sys, os, pathlib

try:
    _project_dir = str(pathlib.Path(__file__).resolve().parent.parent)
except NameError:
    _project_dir = os.getcwd()
if not os.path.isdir(os.path.join(_project_dir, "shared")):
    for _candidate in [os.getcwd(), os.path.dirname(os.path.abspath(sys.argv[-1])) if sys.argv else ""]:
        if os.path.isdir(os.path.join(_candidate, "shared")):
            _project_dir = _candidate
            break
if _project_dir not in sys.path:
    sys.path.insert(0, _project_dir)

import streamlit as st

st.set_page_config(page_title="Impressum — SeasonAlpha", page_icon="⚖️", layout="wide")

# ── Custom CSS ───────────────────────────────────────────────
st.markdown("""
<style>
    .impressum-container {
        max-width: 800px;
        margin: 0 auto;
        padding: 2rem 1rem;
        color: #e8edf5;
    }
    .impressum-container h1 {
        color: #00D4AA;
        font-size: 2rem;
        margin-bottom: 1.5rem;
        border-bottom: 2px solid rgba(0, 212, 170, 0.3);
        padding-bottom: 0.5rem;
    }
    .impressum-container h2 {
        color: #ffffff;
        font-size: 1.3rem;
        margin-top: 2rem;
        margin-bottom: 0.8rem;
    }
    .impressum-container p, .impressum-container li {
        color: #b0b8c8;
        line-height: 1.7;
        font-size: 0.95rem;
    }
    .impressum-container strong {
        color: #e8edf5;
    }
    .impressum-container a {
        color: #00D4AA;
        text-decoration: none;
    }
    .impressum-container a:hover {
        text-decoration: underline;
    }
    .impressum-container hr {
        border: none;
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        margin: 2rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ── Impressum Content ────────────────────────────────────────
st.markdown("""
<div class="impressum-container">

<h1>⚖️ Impressum</h1>

<h2>Angaben gemäß § 5 DDG</h2>

<p>
<strong>Betreiber:</strong><br>
Anitha Kratochwil (Einzelunternehmen)
</p>

<p>
<strong>Anschrift:</strong><br>
Hansastraße 8<br>
80686 München<br>
Deutschland
</p>

<p>
<strong>Kontakt:</strong><br>
E-Mail: <a href="mailto:info@seasonalpha.ai">info@seasonalpha.ai</a>
</p>

<hr>

<h2>Verantwortlich für den Inhalt nach § 18 Abs. 2 MStV</h2>

<p>
Anitha Kratochwil<br>
Hansastraße 8<br>
80686 München
</p>

<hr>

<h2>EU-Streitschlichtung</h2>

<p>
Die Europäische Kommission stellt eine Plattform zur Online-Streitbeilegung (OS) bereit:<br>
<a href="https://ec.europa.eu/consumers/odr/" target="_blank">https://ec.europa.eu/consumers/odr/</a>
</p>

<p>Unsere E-Mail-Adresse finden Sie oben im Impressum.</p>

<hr>

<h2>Haftung für Inhalte</h2>

<p>
Als Diensteanbieter sind wir gemäß § 7 Abs.1 DDG für eigene Inhalte auf diesen Seiten
nach den allgemeinen Gesetzen verantwortlich.
Nach §§ 8 bis 10 DDG sind wir als Diensteanbieter jedoch nicht verpflichtet, übermittelte
oder gespeicherte fremde Informationen zu überwachen oder nach Umständen zu forschen,
die auf eine rechtswidrige Tätigkeit hinweisen.
</p>

<p>
Verpflichtungen zur Entfernung oder Sperrung der Nutzung von Informationen nach den
allgemeinen Gesetzen bleiben hiervon unberührt.
Eine diesbezügliche Haftung ist jedoch erst ab dem Zeitpunkt der Kenntnis einer konkreten
Rechtsverletzung möglich.
Bei Bekanntwerden von entsprechenden Rechtsverletzungen werden wir diese Inhalte
umgehend entfernen.
</p>

<hr>

<h2>Haftung für Links</h2>

<p>
Unser Angebot enthält Links zu externen Websites Dritter, auf deren Inhalte wir keinen
Einfluss haben. Deshalb können wir für diese fremden Inhalte auch keine Gewähr übernehmen.
Für die Inhalte der verlinkten Seiten ist stets der jeweilige Anbieter oder Betreiber der
Seiten verantwortlich.
</p>

<p>
Die verlinkten Seiten wurden zum Zeitpunkt der Verlinkung auf mögliche Rechtsverstöße
überprüft. Rechtswidrige Inhalte waren zum Zeitpunkt der Verlinkung nicht erkennbar.
</p>

<p>
Eine permanente inhaltliche Kontrolle der verlinkten Seiten ist jedoch ohne konkrete
Anhaltspunkte einer Rechtsverletzung nicht zumutbar.
Bei Bekanntwerden von Rechtsverletzungen werden wir derartige Links umgehend entfernen.
</p>

<hr>

<h2>Urheberrecht</h2>

<p>
Die durch die Seitenbetreiber erstellten Inhalte und Werke auf diesen Seiten unterliegen
dem deutschen Urheberrecht. Die Vervielfältigung, Bearbeitung, Verbreitung und jede Art
der Verwertung außerhalb der Grenzen des Urheberrechtes bedürfen der schriftlichen
Zustimmung des jeweiligen Autors bzw. Erstellers.
</p>

<p>
Downloads und Kopien dieser Seite sind nur für den privaten, nicht kommerziellen Gebrauch
gestattet.
</p>

<p>
Soweit die Inhalte auf dieser Seite nicht vom Betreiber erstellt wurden, werden die
Urheberrechte Dritter beachtet. Insbesondere werden Inhalte Dritter als solche
gekennzeichnet.
</p>

<p>
Sollten Sie trotzdem auf eine Urheberrechtsverletzung aufmerksam werden, bitten wir um
einen entsprechenden Hinweis. Bei Bekanntwerden von Rechtsverletzungen werden wir
derartige Inhalte umgehend entfernen.
</p>

</div>
""", unsafe_allow_html=True)
