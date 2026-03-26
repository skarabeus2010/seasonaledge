# pages/98_Datenschutz.py
# ============================================================
# DATENSCHUTZERKLÄRUNG — SeasonAlpha
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

st.set_page_config(page_title="Datenschutz — SeasonAlpha", page_icon="🔒", layout="wide")

# ── Custom CSS ───────────────────────────────────────────────
st.markdown("""
<style>
    .dse-container {
        max-width: 800px;
        margin: 0 auto;
        padding: 2rem 1rem;
        color: #e8edf5;
    }
    .dse-container h1 {
        color: #00D4AA;
        font-size: 2rem;
        margin-bottom: 1.5rem;
        border-bottom: 2px solid rgba(0, 212, 170, 0.3);
        padding-bottom: 0.5rem;
    }
    .dse-container h2 {
        color: #ffffff;
        font-size: 1.3rem;
        margin-top: 2rem;
        margin-bottom: 0.8rem;
    }
    .dse-container p, .dse-container li {
        color: #b0b8c8;
        line-height: 1.7;
        font-size: 0.95rem;
    }
    .dse-container strong {
        color: #e8edf5;
    }
    .dse-container a {
        color: #00D4AA;
        text-decoration: none;
    }
    .dse-container a:hover {
        text-decoration: underline;
    }
    .dse-container hr {
        border: none;
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        margin: 2rem 0;
    }
    .dse-container ul {
        padding-left: 1.5rem;
        color: #b0b8c8;
    }
    .dse-container ul li {
        margin-bottom: 0.3rem;
    }
</style>
""", unsafe_allow_html=True)

# ── Datenschutzerklärung Content ─────────────────────────────
st.markdown("""
<div class="dse-container">

<h1>🔒 Datenschutzerklärung</h1>

<h2>1. Allgemeine Hinweise</h2>

<p>
Der Schutz Ihrer persönlichen Daten ist uns ein besonderes Anliegen.
Wir verarbeiten Ihre Daten ausschließlich auf Grundlage der gesetzlichen Bestimmungen
(insbesondere DSGVO und BDSG).
</p>

<p>
Diese Datenschutzerklärung informiert Sie über Art, Umfang und Zweck der Verarbeitung
personenbezogener Daten auf unserer Website.
</p>

<hr>

<h2>2. Verantwortlicher</h2>

<p>
Anitha Kratochwil<br>
Hansastraße 8<br>
80686 München<br>
Deutschland
</p>

<p>E-Mail: <a href="mailto:info@seasonalpha.ai">info@seasonalpha.ai</a></p>

<hr>

<h2>3. Hosting</h2>

<p>Unsere Website wird bei folgendem Anbieter gehostet:</p>

<p>
Hetzner Online GmbH<br>
Industriestr. 25<br>
91710 Gunzenhausen<br>
Deutschland
</p>

<p>
Beim Aufruf unserer Website werden durch den Hosting-Anbieter automatisch Informationen
erfasst (sog. Server-Logfiles), insbesondere:
</p>

<ul>
    <li>IP-Adresse</li>
    <li>Datum und Uhrzeit der Anfrage</li>
    <li>Browsertyp und -version</li>
    <li>Betriebssystem</li>
    <li>Referrer-URL</li>
</ul>

<p>
Diese Daten sind technisch erforderlich, um die Website bereitzustellen und die
Systemsicherheit zu gewährleisten.
</p>

<p><strong>Rechtsgrundlage:</strong> Art. 6 Abs. 1 lit. f DSGVO (berechtigtes Interesse)</p>

<hr>

<h2>4. Nutzung von KI-Funktionen</h2>

<p>
Auf unserer Website kommen KI-basierte Funktionen zum Einsatz
(z.&nbsp;B. über APIs externer Anbieter wie OpenAI oder vergleichbare Dienste).
</p>

<p>Dabei gilt:</p>

<ul>
    <li>Nutzereingaben werden zur Verarbeitung an externe KI-Dienstleister übermittelt</li>
    <li>Eine Speicherung der Eingaben durch uns erfolgt nicht</li>
    <li>Eine Verwendung der Daten zu Trainingszwecken durch uns findet nicht statt</li>
</ul>

<p>
Es kann nicht ausgeschlossen werden, dass die Daten durch den jeweiligen KI-Anbieter
technisch verarbeitet werden.
</p>

<p>
<strong>Rechtsgrundlage:</strong><br>
Art. 6 Abs. 1 lit. b DSGVO (Vertragserfüllung)<br>
Art. 6 Abs. 1 lit. f DSGVO (berechtigtes Interesse an innovativen Services)
</p>

<hr>

<h2>5. Kontaktaufnahme</h2>

<p>
Wenn Sie uns per E-Mail kontaktieren, werden Ihre Angaben zur Bearbeitung der Anfrage
gespeichert.
</p>

<p><strong>Verarbeitete Daten:</strong></p>

<ul>
    <li>E-Mail-Adresse</li>
    <li>Inhalt der Nachricht</li>
</ul>

<p>
<strong>Rechtsgrundlage:</strong><br>
Art. 6 Abs. 1 lit. b DSGVO (vorvertragliche Maßnahmen)<br>
Art. 6 Abs. 1 lit. f DSGVO
</p>

<hr>

<h2>6. Newsletter</h2>

<p>Wenn Sie sich für unseren Newsletter anmelden, verarbeiten wir:</p>

<ul>
    <li>E-Mail-Adresse</li>
</ul>

<p>Die Anmeldung erfolgt im Double-Opt-in-Verfahren.</p>

<p>Die Daten werden ausschließlich für den Versand des Newsletters verwendet.</p>

<p>
<strong>Rechtsgrundlage:</strong><br>
Art. 6 Abs. 1 lit. a DSGVO (Einwilligung)
</p>

<p>Sie können Ihre Einwilligung jederzeit widerrufen.</p>

<hr>

<h2>7. Cookies</h2>

<p>Unsere Website verwendet derzeit nur technisch notwendige Cookies.</p>

<p>
Sollten künftig Analyse- oder Marketing-Cookies eingesetzt werden, erfolgt dies
ausschließlich nach vorheriger Einwilligung über ein Cookie-Consent-Tool.
</p>

<p>
<strong>Rechtsgrundlage:</strong><br>
Art. 6 Abs. 1 lit. f DSGVO (notwendige Cookies)<br>
Art. 6 Abs. 1 lit. a DSGVO (Einwilligung bei optionalen Cookies)
</p>

<hr>

<h2>8. Drittanbieter-Inhalte (geplant)</h2>

<p>
Wir behalten uns vor, künftig Inhalte von Drittanbietern einzubinden, insbesondere:
</p>

<ul>
    <li>YouTube (Videos)</li>
    <li>Instagram / TikTok (Social Media Inhalte)</li>
</ul>

<p>
Beim Aufruf solcher Inhalte können personenbezogene Daten (z.&nbsp;B. IP-Adresse) an die
jeweiligen Anbieter übertragen werden.
</p>

<p>Die Einbindung erfolgt nur nach entsprechender Einwilligung.</p>

<hr>

<h2>9. Zahlungsdienstleister (zukünftig)</h2>

<p>Für kostenpflichtige Angebote planen wir die Nutzung von:</p>

<p>Stripe Payments Europe Ltd.</p>

<p>
Im Rahmen von Zahlungsabwicklungen werden personenbezogene Daten an den
Zahlungsdienstleister übermittelt.
</p>

<p>Die Verarbeitung erfolgt ausschließlich zum Zweck der Zahlungsabwicklung.</p>

<hr>

<h2>10. Datenübermittlung in Drittländer</h2>

<p>
Eine Übermittlung personenbezogener Daten in Länder außerhalb der EU erfolgt derzeit
nicht aktiv durch uns.
</p>

<p>
Bei Nutzung von KI-Diensten kann eine Verarbeitung in Drittländern (z.&nbsp;B. USA) nicht
ausgeschlossen werden.
</p>

<p>
In solchen Fällen achten wir auf geeignete Garantien gemäß Art. 44 ff. DSGVO
(z.&nbsp;B. Standardvertragsklauseln).
</p>

<hr>

<h2>11. Speicherdauer</h2>

<p>
Personenbezogene Daten werden nur so lange gespeichert, wie dies zur Erfüllung der
jeweiligen Zwecke erforderlich ist oder gesetzliche Aufbewahrungsfristen bestehen.
</p>

<hr>

<h2>12. Ihre Rechte</h2>

<p>Sie haben folgende Rechte:</p>

<ul>
    <li>Auskunft (Art. 15 DSGVO)</li>
    <li>Berichtigung (Art. 16 DSGVO)</li>
    <li>Löschung (Art. 17 DSGVO)</li>
    <li>Einschränkung der Verarbeitung (Art. 18 DSGVO)</li>
    <li>Datenübertragbarkeit (Art. 20 DSGVO)</li>
    <li>Widerspruch (Art. 21 DSGVO)</li>
</ul>

<hr>

<h2>13. Beschwerderecht</h2>

<p>Sie haben das Recht, sich bei einer Datenschutzaufsichtsbehörde zu beschweren.</p>

<p>Zuständig ist z.&nbsp;B.:</p>

<p>Bayerisches Landesamt für Datenschutzaufsicht (BayLDA)</p>

<hr>

<h2>14. Aktualität</h2>

<p>
Diese Datenschutzerklärung hat den Stand: März 2026.<br>
Wir behalten uns vor, sie bei Bedarf anzupassen.
</p>

</div>
""", unsafe_allow_html=True)
