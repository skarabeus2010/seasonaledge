-- =============================================================================
-- User Subscriptions — Stripe-ready Tier-System
-- =============================================================================
-- Speichert den Abo-Status jedes Users. Defaults auf 'free'.
-- Stripe-Felder (customer_id, subscription_id) sind nullable —
-- werden erst bei Stripe-Integration befüllt.
--
-- Aufruf: Im Supabase SQL-Editor ausführen.
-- =============================================================================

-- 1) Tabelle
CREATE TABLE IF NOT EXISTS public.user_subscriptions (
    id              BIGSERIAL PRIMARY KEY,
    user_id         UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    tier            TEXT NOT NULL DEFAULT 'free'
                    CHECK (tier IN ('free', 'premium')),
    status          TEXT NOT NULL DEFAULT 'active'
                    CHECK (status IN ('active', 'cancelled', 'expired', 'past_due')),
    -- Stripe-Felder (NULL bis Stripe live)
    stripe_customer_id     TEXT,
    stripe_subscription_id TEXT,
    stripe_price_id        TEXT,
    -- Zeiträume
    current_period_start   TIMESTAMPTZ,
    current_period_end     TIMESTAMPTZ,
    cancelled_at           TIMESTAMPTZ,
    -- Audit
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id)
);

-- 2) moddatetime-Trigger (updated_at automatisch)
CREATE EXTENSION IF NOT EXISTS moddatetime SCHEMA extensions;

DROP TRIGGER IF EXISTS handle_updated_at ON user_subscriptions;
CREATE TRIGGER handle_updated_at
  BEFORE UPDATE ON user_subscriptions
  FOR EACH ROW EXECUTE FUNCTION extensions.moddatetime(updated_at);

-- 3) Index für Stripe-Lookups (Webhook braucht das)
CREATE INDEX IF NOT EXISTS idx_user_subs_stripe_customer
  ON user_subscriptions(stripe_customer_id)
  WHERE stripe_customer_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_user_subs_stripe_sub
  ON user_subscriptions(stripe_subscription_id)
  WHERE stripe_subscription_id IS NOT NULL;

-- 4) RLS: User sieht nur eigenes Abo
ALTER TABLE user_subscriptions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users read own subscription" ON user_subscriptions;
CREATE POLICY "Users read own subscription"
  ON user_subscriptions FOR SELECT
  USING (auth.uid() = user_id);

-- service_role darf alles (für Stripe-Webhook + Admin)
DROP POLICY IF EXISTS "Service role full access" ON user_subscriptions;
CREATE POLICY "Service role full access"
  ON user_subscriptions FOR ALL
  USING (auth.jwt() ->> 'role' = 'service_role');

-- 5) Grants
GRANT SELECT ON user_subscriptions TO authenticated;
GRANT ALL ON user_subscriptions TO service_role;
GRANT USAGE, SELECT ON SEQUENCE user_subscriptions_id_seq TO service_role;

-- 6) RPC: get_my_tier() — gibt den Tier des eingeloggten Users zurück
-- Gibt 'free' zurück wenn kein Abo existiert (= Default für alle)
CREATE OR REPLACE FUNCTION public.get_my_tier()
RETURNS TEXT
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT COALESCE(
    (SELECT tier FROM user_subscriptions
     WHERE user_id = auth.uid()
       AND status = 'active'
     LIMIT 1),
    'free'
  );
$$;

-- Nur eingeloggte User dürfen ihre Tier abfragen
GRANT EXECUTE ON FUNCTION public.get_my_tier() TO authenticated;
REVOKE EXECUTE ON FUNCTION public.get_my_tier() FROM anon;

-- 7) Auto-Insert: Wenn ein neuer User sich registriert,
-- automatisch einen 'free' Eintrag anlegen
CREATE OR REPLACE FUNCTION public.handle_new_user_subscription()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  INSERT INTO user_subscriptions (user_id, tier, status)
  VALUES (NEW.id, 'free', 'active')
  ON CONFLICT (user_id) DO NOTHING;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS on_auth_user_created_subscription ON auth.users;
CREATE TRIGGER on_auth_user_created_subscription
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user_subscription();
