import Stripe from 'npm:stripe@14'

// Env-Vars (in Supabase Dashboard → Project Settings → Edge Functions → Secrets setzen):
//   STRIPE_SECRET_KEY   — sk_live_xxx  (oder sk_test_xxx zum Testen)
//   STRIPE_PRICE_ID     — price_xxx    (aus Stripe Dashboard: Products → dein Produkt → Price ID)

const stripe = new Stripe(Deno.env.get('STRIPE_SECRET_KEY') ?? '', {
  apiVersion: '2024-06-20',
})

const CORS = {
  'Access-Control-Allow-Origin': 'https://seasonalpha.ai',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
}

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: CORS })
  }

  try {
    const { user_id, email, return_url } = await req.json()

    if (!user_id || !email) {
      return new Response(JSON.stringify({ error: 'Fehlende Parameter: user_id + email erforderlich' }), {
        status: 400,
        headers: { ...CORS, 'Content-Type': 'application/json' },
      })
    }

    const priceId = Deno.env.get('STRIPE_PRICE_ID') ?? ''
    if (!priceId) {
      return new Response(JSON.stringify({ error: 'STRIPE_PRICE_ID nicht konfiguriert' }), {
        status: 500,
        headers: { ...CORS, 'Content-Type': 'application/json' },
      })
    }

    const base = (return_url || 'https://seasonalpha.ai/pricing').replace(/[?#].*$/, '')

    const session = await stripe.checkout.sessions.create({
      mode: 'subscription',
      customer_email: email,
      line_items: [{ price: priceId, quantity: 1 }],
      success_url: base + '?checkout=success',
      cancel_url: base + '?checkout=cancelled',
      metadata: { user_id },
      allow_promotion_codes: true,
      billing_address_collection: 'auto',
      tax_id_collection: { enabled: true },
      locale: 'de',
    })

    return new Response(JSON.stringify({ url: session.url }), {
      headers: { ...CORS, 'Content-Type': 'application/json' },
    })
  } catch (err) {
    console.error('[create-checkout-session]', err)
    return new Response(JSON.stringify({ error: err.message }), {
      status: 500,
      headers: { ...CORS, 'Content-Type': 'application/json' },
    })
  }
})
