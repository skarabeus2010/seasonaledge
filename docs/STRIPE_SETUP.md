# Stripe-Integration Setup — SeasonAlpha

Technische Integration ist fertig (`supabase/functions/`). Folgende Schritte sind nötig um live zu gehen.

---

## Schritt 1 — Stripe-Account erstellen

1. https://dashboard.stripe.com/register
2. Geschäftsdaten eintragen (Name, Adresse, Bankverbindung für Auszahlungen)
3. **Test-Modus** für alles unten — erst am Ende auf Live umschalten

---

## Schritt 2 — Produkt + Preis anlegen

1. Stripe Dashboard → **Products** → „Add product"
2. Name: `SeasonAlpha Premium`
3. Beschreibung (optional): Volle Saisonalitäts-Analyse + KI-Score + Marktkalender
4. Pricing: **Recurring** → Monatlich → Preis festlegen (z.B. `9.99 EUR`)
5. Speichern → **Price ID** kopieren: `price_1Abc...` → wird in Schritt 4 gebraucht

---

## Schritt 3 — Supabase DB-Schema anwenden (falls noch nicht getan)

Im Supabase SQL-Editor (`supabase.com → dein Projekt → SQL Editor`) das folgende Script ausführen:

```
scripts/create_user_subscriptions.sql
```

Prüfen danach:
```sql
SELECT * FROM user_subscriptions LIMIT 5;
SELECT get_my_tier();
```

---

## Schritt 4 — Supabase Edge Functions deployen

### Supabase CLI installieren
```bash
npm install -g supabase
supabase login
supabase link --project-ref <dein-project-ref>
```

Project-Ref findest du in: Supabase Dashboard → Settings → General → Reference ID

### Functions deployen
```bash
supabase functions deploy create-checkout-session
supabase functions deploy stripe-webhook
supabase functions deploy create-portal-session
```

### Secrets setzen
```bash
supabase secrets set STRIPE_SECRET_KEY=sk_test_xxx
supabase secrets set STRIPE_PRICE_ID=price_1Abc...
# STRIPE_WEBHOOK_SECRET kommt in Schritt 5
```

---

## Schritt 5 — Stripe Webhook einrichten

1. Stripe Dashboard → **Webhooks** → „Add endpoint"
2. URL: `https://<dein-project-ref>.supabase.co/functions/v1/stripe-webhook`
3. Events auswählen:
   - `checkout.session.completed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_failed`
4. Speichern → **Signing secret** (`whsec_xxx`) kopieren
5. In Supabase setzen:
   ```bash
   supabase secrets set STRIPE_WEBHOOK_SECRET=whsec_xxx
   ```

---

## Schritt 6 — Stripe Customer Portal konfigurieren

1. Stripe Dashboard → **Settings** → **Billing** → **Customer portal**
2. Features aktivieren: Abo kündigen, Zahlungsmethode ändern, Rechnungen anzeigen
3. Speichern

---

## Schritt 7 — Pricing-Page mit Live-Preis aktualisieren

In `landing/pages/pricing.html` den Preis-Platzhalter ersetzen:

```html
<!-- Zeile mit id="price-amount": -->
<span id="price-amount">9,99</span>
<!-- und die price-note: -->
<div class="plan-price-note">Monatlich kündbar · MwSt. inklusive</div>
```

Und den i18n-Key `price.premium_price_note` in `en.json` aktualisieren:
```json
"price.premium_price_note": "Cancel monthly · VAT included"
```

---

## Schritt 8 — Testen (Test-Modus)

1. Pricing-Page → „Jetzt upgraden" klicken
2. Stripe Checkout erscheint (Testkarte: `4242 4242 4242 4242`, beliebiges Datum, CVC)
3. Nach Zahlung → Redirect zu `/pricing?checkout=success` → grüner Banner
4. Supabase prüfen: `SELECT tier, status FROM user_subscriptions WHERE user_id = 'deine-uid';`
5. Refresh Pricing-Page → Button zeigt „Abo verwalten"
6. „Abo verwalten" → Stripe Customer Portal öffnet sich

---

## Schritt 9 — Live schalten

1. Stripe Dashboard → oben rechts **Test mode → Live mode** umschalten
2. Neues Produkt + Preis in Live anlegen (gleiche Konfiguration)
3. Neue Live-Keys holen: `sk_live_xxx`, neue Price ID, neuen Webhook-Secret
4. Supabase Secrets überschreiben:
   ```bash
   supabase secrets set STRIPE_SECRET_KEY=sk_live_xxx
   supabase secrets set STRIPE_PRICE_ID=price_live_xxx
   supabase secrets set STRIPE_WEBHOOK_SECRET=whsec_live_xxx
   ```

---

## Env-Variablen Übersicht

| Variable | Wo setzen | Beispiel |
|---|---|---|
| `STRIPE_SECRET_KEY` | `supabase secrets set` | `sk_test_51...` |
| `STRIPE_PRICE_ID` | `supabase secrets set` | `price_1Abc...` |
| `STRIPE_WEBHOOK_SECRET` | `supabase secrets set` | `whsec_...` |
| `SUPABASE_URL` | automatisch verfügbar | — |
| `SUPABASE_SERVICE_ROLE_KEY` | automatisch verfügbar | — |

---

## Troubleshooting

**Webhook kommt nicht an:**
- Stripe Dashboard → Webhooks → „Recent deliveries" → Fehlerdetails
- Edge Function Logs: Supabase Dashboard → Edge Functions → Logs

**Checkout-Button macht nichts:**
- Browser-Konsole: `window.__SA_SB_URL` muss gesetzt sein (inject_credentials.sh)
- Edge Function URL: `window.__SA_SB_URL + '/functions/v1/create-checkout-session'`

**User bleibt auf `free` nach Zahlung:**
- Webhook-Secret falsch? → `supabase secrets set STRIPE_WEBHOOK_SECRET=...` neu setzen
- `user_subscriptions` Tabelle vorhanden? → `SELECT * FROM user_subscriptions LIMIT 1;`
- sessionStorage-Cache leeren: `sessionStorage.removeItem('sa_tier')`
