# SeasonalEdge — Email-System mit Brevo
## Einmalig einrichten, dann läuft es automatisch

---

## Warum Brevo?

| | Brevo | Mailchimp | Typeform |
|---|---|---|---|
| Kostenlos | bis 300 Emails/Tag | bis 500 Kontakte | nur Formular |
| DSGVO | ✅ Server EU | ⚠️ US-Server | ⚠️ US-Server |
| Automation | ✅ kostenlos | ❌ ab 13 €/Mo | ❌ |
| API für Streamlit | ✅ | ✅ | ❌ |
| Newsletter | ✅ | ✅ | ❌ |
| Empfehlung | ✅ **Beste Wahl** | — | — |

---

## Architektur — Einmal einrichten, nie mehr anfassen

```
Nutzer gibt Email ein (Streamlit)
        ↓
Brevo API → Kontakt in Liste "SeasonalEdge Early Birds"
        ↓
Automation startet sofort:
  └─ Email 1 (sofort):    Willkommen + Early-Bird-Versprechen
  └─ Email 2 (+3 Tage):   "Tipp: Hast du die TruePath KI gesehen?"
        ↓
Wöchentlicher Newsletter (manuell schreiben, Brevo versendet)
```

---

## SCHRITT 1 — Brevo Account erstellen (5 Min)

1. Gehe zu **brevo.com** → "Sign up free"
2. Email + Passwort → Konto bestätigen
3. Unter **Settings → Senders & IP** deine Absender-Adresse eintragen
   - z.B. `hello@seasonaledge.app`
   - Brevo verifiziert die Domain (DNS-Eintrag nötig — Brevo zeigt dir genau was)

---

## SCHRITT 2 — Liste anlegen (2 Min)

1. Im Brevo-Dashboard → **Contacts → Lists → Create a list**
2. Name: `SeasonalEdge Early Birds`
3. Liste-ID notieren (brauchst du für den API-Call) — steht in der URL

---

## SCHRITT 3 — Welcome Automation einrichten (15 Min)

1. **Automations → Create a workflow**
2. Trigger: `Contact added to list "SeasonalEdge Early Birds"`
3. Workflow-Schritte:

```
[Trigger: Kontakt zu Liste hinzugefügt]
        ↓
[Email senden: "Willkommen bei SeasonalEdge 🎉"]   ← sofort
        ↓
[Warten: 3 Tage]
        ↓
[Email senden: "Dein Early-Bird-Vorteil wartet"]
```

### Email 1 — Vorlage: Willkommen + Early-Bird

**Betreff:** `Willkommen bei SeasonalEdge — dein Early-Bird-Platz ist gesichert 🎉`

```
Hallo,

herzlich willkommen bei SeasonalEdge!

Du hast dir gerade einen Early-Bird-Platz gesichert. Das bedeutet:
Wenn wir in 2-3 Monaten auf Premium umstellen, bekommst du als
einer der Ersten ein exklusives Angebot — deutlich günstiger
als der reguläre Preis.

In der Zwischenzeit kannst du alle Features kostenlos nutzen:
→ https://seasonaledge.app

Besonders empfehlenswert: Die Mondphasen-Analyse und TruePath KI.

Viel Erfolg beim Trading,
Heiko | SeasonalEdge
```

### Email 2 — Vorlage: 3 Tage später

**Betreff:** `Hast du das schon probiert? → TruePath KI`

```
Hallo,

falls du noch nicht reingeschaut hast: Die TruePath KI-Seite
erkennt historische Saisonalitätsmuster und gibt dir einen
konkreten Score von 0–100.

Einfach ausprobieren (kostenlos):
→ https://seasonaledge.app

Bis zum nächsten Trend,
Heiko | SeasonalEdge
```

---

## SCHRITT 4 — API-Key anlegen (2 Min)

1. Brevo → **Settings → API Keys → Generate a new API key**
2. Name: `SeasonalEdge Streamlit`
3. Key kopieren und in Streamlit Cloud Secrets eintragen:

```toml
# .streamlit/secrets.toml (NICHT ins Git!)
brevo_api_key = "xkeysib-DEIN-KEY-HIER"
brevo_list_id = 3   # deine Listen-ID aus Schritt 2
```

---

## SCHRITT 5 — Streamlit Code (1x einbauen, fertig)

Diesen Code in `seasonal_app.py` oder als eigene Komponente einbauen:

```python
import streamlit as st
import requests

def subscribe_email(email: str) -> bool:
    """Trägt Email in Brevo-Liste ein. Gibt True bei Erfolg zurück."""
    api_key = st.secrets["brevo_api_key"]
    list_id = int(st.secrets["brevo_list_id"])
    
    url = "https://api.brevo.com/v3/contacts"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "api-key": api_key,
    }
    payload = {
        "email": email,
        "listIds": [list_id],
        "updateEnabled": True,   # kein Fehler wenn Email schon existiert
    }
    
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=5)
        return resp.status_code in (200, 201, 204)
    except Exception:
        return False


def email_capture_widget(location: str = "sidebar"):
    """
    Zeigt das Email-Formular an.
    location = "sidebar" oder "main"
    """
    with st.sidebar if location == "sidebar" else st.container():
        st.markdown("---")
        st.markdown("### 🎯 Early-Bird-Zugang sichern")
        st.caption(
            "Alle Premium-Features sind jetzt kostenlos. "
            "Trag dich ein und bekomm als Erster unser Angebot, "
            "wenn wir auf Paid umstellen."
        )
        
        email = st.text_input(
            "Deine Email-Adresse",
            placeholder="trading@example.com",
            key=f"email_capture_{location}",
            label_visibility="collapsed",
        )
        
        if st.button("🔒 Early-Bird-Platz sichern", 
                     key=f"btn_capture_{location}",
                     use_container_width=True):
            if "@" in email and "." in email:
                success = subscribe_email(email)
                if success:
                    st.success("✅ Du bist dabei! Check deine Inbox.")
                    st.balloons()
                else:
                    st.error("Fehler — bitte nochmal versuchen.")
            else:
                st.warning("Bitte gib eine gültige Email ein.")
        
        st.caption("🇩🇪 DSGVO-konform · Kein Spam · Jederzeit abmeldbar")
```

### Einbinden in seasonal_app.py

```python
# Am Ende von seasonal_app.py, nach dem Haupt-Content:
from shared.email_capture import email_capture_widget

# Sidebar auf JEDER Seite (empfohlen):
email_capture_widget(location="sidebar")
```

---

## SCHRITT 6 — Wöchentlicher Newsletter (laufender Betrieb)

Kein Code nötig — komplett in Brevo-UI:

1. **Campaigns → Email → Create a campaign**
2. Template auswählen (Brevo hat viele kostenlose)
3. Inhalt schreiben: "Saisonaler Trend der Woche" — 3-5 Sätze + Screenshot + Link
4. Empfänger: Liste `SeasonalEdge Early Birds`
5. Versandzeitpunkt: z.B. jeden Montag 08:00 Uhr
6. **Send** → fertig

**Zeitaufwand pro Newsletter:** ca. 20-30 Minuten

---

## DSGVO-Checkliste (Pflicht in DE)

- [x] Brevo speichert Daten auf EU-Servern ✅
- [x] `gatherUsageStats = false` in config.toml ✅
- [ ] Datenschutz-Seite: Erwähne Brevo als Email-Dienstleister
- [ ] Double-Opt-In aktivieren (Brevo-Setting): Brevo → Lists → Double opt-in
- [ ] Abmelde-Link ist in jeder Brevo-Email automatisch enthalten ✅
- [ ] In der Datenschutz-Seite: "Wir nutzen Brevo (Sendinblue SAS, Paris) für den Newsletter-Versand"

### Double-Opt-In aktivieren (5 Min, DSGVO Best Practice)

In Brevo → **Settings → Double opt-in**:
- Bestätigungs-Email: Brevo versendet automatisch
- Bestätigungsseite: kannst du auf `seasonaledge.app/confirmed` zeigen lassen
- Vorteil: Listensauberkeit + rechtlich wasserdicht

---

## Zusammenfassung: Was du einmalig tust

| Schritt | Aufwand | Danach automatisch |
|---|---|---|
| Brevo Account + Domain-Verifizierung | 15 Min | ✅ |
| Liste anlegen | 2 Min | ✅ |
| Welcome-Automation (2 Emails) | 20 Min | ✅ läuft für jeden Neuen |
| API-Key in Streamlit Secrets | 5 Min | ✅ |
| Code in seasonal_app.py einbauen | 30 Min | ✅ |
| Double-Opt-In aktivieren | 5 Min | ✅ |
| **Gesamt** | **~1,5 Stunden** | **Dann nie mehr anfassen** |

Einzige laufende Arbeit: Wöchentlicher Newsletter-Inhalt (20-30 Min/Woche).

---

*SeasonalEdge · Email-System v1.0 · März 2026*
