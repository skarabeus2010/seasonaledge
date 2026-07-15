import Stripe from 'npm:stripe@14'
import { createClient } from 'npm:@supabase/supabase-js@2'

// Env-Vars:
//   STRIPE_SECRET_KEY      — sk_live_xxx
//   STRIPE_WEBHOOK_SECRET  — whsec_xxx  (aus Stripe Dashboard → Webhooks → Signing secret)
//   SUPABASE_URL           — automatisch verfügbar in Edge Functions
//   SUPABASE_SERVICE_ROLE_KEY — automatisch verfügbar in Edge Functions

const stripe = new Stripe(Deno.env.get('STRIPE_SECRET_KEY') ?? '', {
  apiVersion: '2024-06-20',
})

const supabase = createClient(
  Deno.env.get('SUPABASE_URL') ?? '',
  Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
)

Deno.serve(async (req) => {
  const sig = req.headers.get('stripe-signature')
  if (!sig) {
    return new Response('Missing stripe-signature header', { status: 400 })
  }

  const body = await req.text()
  let event: Stripe.Event

  try {
    event = await stripe.webhooks.constructEventAsync(
      body,
      sig,
      Deno.env.get('STRIPE_WEBHOOK_SECRET') ?? ''
    )
  } catch (err) {
    console.error('[stripe-webhook] Signature-Fehler:', err.message)
    return new Response(`Webhook Error: ${err.message}`, { status: 400 })
  }

  console.log('[stripe-webhook] Event:', event.type)

  try {
    switch (event.type) {
      // ── Checkout abgeschlossen → Premium aktivieren ──────────────
      case 'checkout.session.completed': {
        const session = event.data.object as Stripe.Checkout.Session
        const userId = session.metadata?.user_id
        if (!userId) { console.warn('Kein user_id in metadata'); break }

        const { error } = await supabase.from('user_subscriptions').upsert({
          user_id: userId,
          tier: 'premium',
          status: 'active',
          stripe_customer_id: session.customer as string,
          stripe_subscription_id: session.subscription as string,
          stripe_price_id: Deno.env.get('STRIPE_PRICE_ID') ?? null,
          current_period_start: new Date().toISOString(),
        }, { onConflict: 'user_id' })

        if (error) console.error('[stripe-webhook] upsert error:', error)
        else console.log('[stripe-webhook] Premium aktiviert für user_id:', userId)
        break
      }

      // ── Abo-Status geändert (Verlängerung, past_due, …) ─────────
      case 'customer.subscription.updated': {
        const sub = event.data.object as Stripe.Subscription
        const isActive = ['active', 'trialing'].includes(sub.status)
        const periodEnd = sub.current_period_end
          ? new Date(sub.current_period_end * 1000).toISOString()
          : null

        const { error } = await supabase.from('user_subscriptions')
          .update({
            tier: isActive ? 'premium' : 'free',
            status: isActive ? 'active' : (sub.status === 'past_due' ? 'past_due' : 'expired'),
            current_period_end: periodEnd,
          })
          .eq('stripe_subscription_id', sub.id)

        if (error) console.error('[stripe-webhook] update error:', error)
        break
      }

      // ── Abo gekündigt / abgelaufen ───────────────────────────────
      case 'customer.subscription.deleted': {
        const sub = event.data.object as Stripe.Subscription

        const { error } = await supabase.from('user_subscriptions')
          .update({
            tier: 'free',
            status: 'cancelled',
            cancelled_at: new Date().toISOString(),
          })
          .eq('stripe_subscription_id', sub.id)

        if (error) console.error('[stripe-webhook] cancel error:', error)
        else console.log('[stripe-webhook] Abo gekündigt:', sub.id)
        break
      }

      // ── Zahlung fehlgeschlagen ───────────────────────────────────
      case 'invoice.payment_failed': {
        const invoice = event.data.object as Stripe.Invoice
        if (invoice.subscription) {
          await supabase.from('user_subscriptions')
            .update({ status: 'past_due' })
            .eq('stripe_subscription_id', invoice.subscription as string)
        }
        break
      }

      default:
        console.log('[stripe-webhook] Ignoriertes Event:', event.type)
    }
  } catch (err) {
    console.error('[stripe-webhook] Handler-Fehler:', err)
    return new Response('Internal Server Error', { status: 500 })
  }

  return new Response(JSON.stringify({ received: true }), {
    headers: { 'Content-Type': 'application/json' },
  })
})
