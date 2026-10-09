-- SeasonAlpha — Polymarket: Schema-Ergaenzung fuer die Befunde 1, 2, 3 und 11
-- des Reviews vom 2026-10-07.
--
-- IM SUPABASE-SQL-EDITOR AUSFUEHREN (SeasonAlpha-Projekt, nicht das
-- Schwesterprojekt). Einmal; wiederholtes Ausfuehren ist unschaedlich.
--
-- ╔══════════════════════════════════════════════════════════════════════════╗
-- ║ WAS DIESE MIGRATION TUT — und was sie bewusst NICHT tut                 ║
-- ╚══════════════════════════════════════════════════════════════════════════╝
--
-- Sie ist REIN ERGAENZEND: neue Spalten, ein neuer Index, eine Funktion.
-- Nichts wird umbenannt, verengt, gefuellt oder geloescht. Der Grund ist das
-- Zeitfenster zwischen dieser Migration und dem Deploy des neuen Codes: in
-- diesem Fenster laeuft der ALTE Code weiter, und er darf nicht brechen.
--
-- Deshalb gilt fuer jede Pruefbedingung: sie bindet nur Zeilen, die sich
-- ausdruecklich als klassifiziert ausgeben (`price_kind` gesetzt und nicht
-- 'unbekannt'). Der alte Erzeuger schreibt diese Spalte gar nicht, seine
-- Zeilen erfuellen die Bedingung also trivial. Eine unbedingte Pruefung haette
-- den alten Schreibweg mit "violates check constraint" abgewuergt — und der
-- laeuft bis zum Deploy taeglich.
--
-- Bestandszeilen bekommen KEINE geratenen Werte. Was unbekannt ist, bleibt
-- NULL und gilt im neuen Code als nicht bewertbar. Nachtraeglich eine
-- Preisart zu erfinden waere eine Behauptung ueber Daten, die wir nicht haben.
--
-- NICHT Gegenstand dieser Migration (eigene Phasen, siehe docs/POLYMARKET.md):
--   * das Fuellen von `status` aus der Gamma-Antwort (Entscheidungstabelle)
--   * die Pflege von `resolution` / `resolved_at`
--   * die Verbraucher-Seite (Seite + Newsletter)

BEGIN;

-- ╔══════════════════════════════════════════════════════════════════════════╗
-- ║ 1) polymarket_prices — Preisart, Quotes, Abrufzeit                      ║
-- ╚══════════════════════════════════════════════════════════════════════════╝
--
-- Befund 11: Mittelkurs, einseitige Quote und letzter Trade landeten
-- ununterscheidbar in `yes_price`. Ein gekreuztes Buch (Bid 0,80 / Ask 0,20)
-- wurde als Preis 0,50 mit negativem Spread gespeichert. Ohne die Preisart
-- laesst sich im Nachhinein nicht sagen, was eine Zeile ueberhaupt behauptet.

ALTER TABLE public.polymarket_prices
    ADD COLUMN IF NOT EXISTS price_kind TEXT,
    ADD COLUMN IF NOT EXISTS bid        NUMERIC,
    ADD COLUMN IF NOT EXISTS ask        NUMERIC,
    ADD COLUMN IF NOT EXISTS fetched_at TIMESTAMPTZ;

-- Zur Bedeutung von `ts` und `fetched_at` — hier steckte ein Denkfehler:
--
--   `ts`         = der Zeitpunkt, ZU DEM der Preis gehoert.
--   `fetched_at` = der Zeitpunkt, AN DEM wir ihn abgerufen haben.
--
-- Bisher trug `ts` beides, je nach Erzeuger: `polymarket_refresh.py` schrieb
-- dort den Abrufzeitpunkt, `polymarket_backfill.py` den historischen
-- Quellzeitpunkt aus der CLOB-Historie (`history_to_records`, Feld `t`).
-- Dieselbe Spalte, zwei Bedeutungen — und das Alter eines Preises laesst sich
-- so nicht berechnen. `fetched_at` trennt die beiden.
--
-- Was Gamma NICHT liefert: einen Zeitstempel der konkreten Quote. Fuer
-- Snapshots ist `ts` daher weiterhin der Abrufzeitpunkt, und `fetched_at` ist
-- derselbe Wert. Das ist eine Beobachtungszeit, kein Quotenalter, und der
-- neue Code darf es auch nicht als solches ausgeben.

COMMENT ON COLUMN public.polymarket_prices.ts IS
    'Zeitpunkt, zu dem der Preis gehoert. Snapshot: Abrufzeitpunkt (Gamma '
    'liefert keine Quotenzeit). Backfill: historische Quellzeit aus der '
    'CLOB-Historie.';
COMMENT ON COLUMN public.polymarket_prices.fetched_at IS
    'Zeitpunkt des Abrufs. Bei Snapshots gleich ts, beim Backfill deutlich '
    'spaeter als ts. NULL bei Zeilen aus der Zeit vor dieser Migration.';
COMMENT ON COLUMN public.polymarket_prices.price_kind IS
    'Woraus der Preis entstand: mid | bid_only | ask_only | last_trade | '
    'history | unbekannt. NULL = aus der Zeit vor dieser Migration, nicht '
    'bewertbar.';
COMMENT ON COLUMN public.polymarket_prices.bid IS 'Bestes Gebot zum Abrufzeitpunkt, falls geliefert.';
COMMENT ON COLUMN public.polymarket_prices.ask IS 'Beste Nachfrage zum Abrufzeitpunkt, falls geliefert.';

-- Erlaubte Preisarten. Als CHECK und nicht als ENUM: einen ENUM-Typ zu
-- erweitern ist spaeter eine eigene Migration mit eigener Sperre.
ALTER TABLE public.polymarket_prices
    DROP CONSTRAINT IF EXISTS pm_prices_price_kind_erlaubt;
ALTER TABLE public.polymarket_prices
    ADD CONSTRAINT pm_prices_price_kind_erlaubt CHECK (
        price_kind IS NULL OR price_kind IN (
            'mid', 'bid_only', 'ask_only', 'last_trade', 'history', 'unbekannt'
        )
    );

-- Wertebereich und Konsistenz — nur fuer Zeilen, die sich als klassifiziert
-- ausgeben. Fuer Bestandszeilen (price_kind IS NULL) und fuer den alten
-- Schreibweg ist die Bedingung trivial erfuellt; deshalb braucht sie kein
-- NOT VALID. (NOT VALID haette ohnehin nicht geleistet, was ich zuerst
-- annahm: es ueberspringt nur die Pruefung des Bestands, gilt aber sofort
-- fuer neue UND geaenderte Zeilen.)
ALTER TABLE public.polymarket_prices
    DROP CONSTRAINT IF EXISTS pm_prices_wertebereich;
ALTER TABLE public.polymarket_prices
    ADD CONSTRAINT pm_prices_wertebereich CHECK (
        price_kind IS NULL
        OR price_kind = 'unbekannt'
        OR (
            yes_price >= 0 AND yes_price <= 1
            AND (bid IS NULL OR (bid >= 0 AND bid <= 1))
            AND (ask IS NULL OR (ask >= 0 AND ask <= 1))
            -- Ein gekreuztes Buch ist ein Messfehler, kein Preis.
            AND (bid IS NULL OR ask IS NULL OR bid <= ask)
            -- 'mid' behauptet, aus ZWEI Quotes entstanden zu sein. Ohne beide
            -- ist die Behauptung nicht gedeckt.
            AND (price_kind <> 'mid' OR (bid IS NOT NULL AND ask IS NOT NULL))
        )
    );

-- ╔══════════════════════════════════════════════════════════════════════════╗
-- ║ 2) polymarket_markets — Status und Abrufzustand                         ║
-- ╚══════════════════════════════════════════════════════════════════════════╝
--
-- Befund 3: der Katalogabgleich schrieb `active = TRUE` fest, obwohl die
-- Gamma-Antwort `closed` und `acceptingOrders` mitliefert. Aufgeloeste und
-- pausierte Maerkte blieben damit in der aktuellen Ansicht.
--
-- `active` BLEIBT eine normale Spalte und wird nicht angetastet: der alte Code
-- schreibt sie, und `loadCatalog()` filtert auf `active=eq.true`. Sichtbarkeit
-- (`active`) und Bewertbarkeit (`status`) sind bewusst ZWEI Dinge — ein
-- pausierter Markt soll sichtbar bleiben und gekennzeichnet werden, nicht
-- verschwinden.

ALTER TABLE public.polymarket_markets
    ADD COLUMN IF NOT EXISTS status            TEXT,
    ADD COLUMN IF NOT EXISTS status_checked_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS last_fetch_state  TEXT,
    ADD COLUMN IF NOT EXISTS last_fetch_at     TIMESTAMPTZ;

COMMENT ON COLUMN public.polymarket_markets.status IS
    'open | paused | closed | resolved | unavailable | unbekannt. NULL = aus '
    'der Zeit vor dieser Migration. Steuert die BEWERTBARKEIT, nicht die '
    'Sichtbarkeit (das tut active).';
COMMENT ON COLUMN public.polymarket_markets.status_checked_at IS
    'Wann der Status letztmals aus einer ERFOLGREICHEN Antwort bestimmt wurde. '
    'Bei einem API-Ausfall bleibt der Status stehen, dieser Zeitstempel wird '
    'aber NICHT erneuert — ein alter Status veraltet damit sichtbar.';
COMMENT ON COLUMN public.polymarket_markets.last_fetch_state IS
    'Ergebnis des letzten Preisabrufs: ok | kein_preis | verworfen | fehler. '
    'Ein gescheiterter oder verworfener Abruf muss den zuletzt gespeicherten '
    'Preis entwerten koennen — sonst bleibt ein noch junger Mittelkurs '
    'bewertbar, obwohl das Buch inzwischen gekreuzt ist.';
COMMENT ON COLUMN public.polymarket_markets.last_fetch_at IS
    'Zeitpunkt des letzten Preisabrufversuchs, unabhaengig vom Ergebnis.';

ALTER TABLE public.polymarket_markets
    DROP CONSTRAINT IF EXISTS pm_markets_status_erlaubt;
ALTER TABLE public.polymarket_markets
    ADD CONSTRAINT pm_markets_status_erlaubt CHECK (
        status IS NULL OR status IN (
            'open', 'paused', 'closed', 'resolved', 'unavailable', 'unbekannt'
        )
    );

ALTER TABLE public.polymarket_markets
    DROP CONSTRAINT IF EXISTS pm_markets_fetch_state_erlaubt;
ALTER TABLE public.polymarket_markets
    ADD CONSTRAINT pm_markets_fetch_state_erlaubt CHECK (
        last_fetch_state IS NULL OR last_fetch_state IN (
            'ok', 'kein_preis', 'verworfen', 'fehler'
        )
    );

-- Ein Abrufzustand ohne Zeitpunkt ist nicht einzuordnen: „verworfen" sagt
-- nichts, wenn offen bleibt, wann. Das tatsaechliche Entwerten eines Preises
-- bleibt Aufgabe der Folgephase; hier wird nur die Angabe selbst vollstaendig
-- verlangt.
ALTER TABLE public.polymarket_markets
    DROP CONSTRAINT IF EXISTS pm_markets_fetch_zeit_vollstaendig;
ALTER TABLE public.polymarket_markets
    ADD CONSTRAINT pm_markets_fetch_zeit_vollstaendig CHECK (
        last_fetch_state IS NULL OR last_fetch_at IS NOT NULL
    );

CREATE INDEX IF NOT EXISTS idx_pm_markets_status
    ON public.polymarket_markets (status);

-- ╔══════════════════════════════════════════════════════════════════════════╗
-- ║ 3) Neueste Preiszeile pro Markt — serverseitig                          ║
-- ╚══════════════════════════════════════════════════════════════════════════╝
--
-- Befund 2: das Frontend holte `5 x Anzahl Maerkte` Zeilen nach Zeit sortiert
-- und suchte den neuesten Eintrag pro Markt im Browser heraus. Ein haeufig
-- aktualisierter Markt kann einen selten aktualisierten damit VOLLSTAENDIG aus
-- der Antwort verdraengen — der hat dann gar keinen Preis, und zusammen mit
-- Befund 1 wurde daraus eine gruene Kachel mit 0,0 %.
--
-- Umgesetzt als FUNKTION und nicht als View, und zwar aus einem belegten
-- Grund: `security_invoker` fuer Views gibt es erst ab PostgreSQL 15, und die
-- Version dieses Projekts ist nicht geprueft. Eine Funktion ist
-- standardmaessig SECURITY INVOKER und laeuft damit auf jeder Version mit den
-- Rechten und der RLS des Aufrufers.
--
-- `STABLE` ist hier sachlich richtig, weil die Funktion nur liest. Hier stand
-- zuerst, PostgREST lasse GET „nur fuer STABLE oder IMMUTABLE" zu — das ist
-- als allgemeine Aussage falsch (seit PostgREST 11.2 geht GET auch fuer
-- VOLATILE in einer Nur-Lese-Transaktion) und von Codex widerlegt worden. Die
-- Wahl bleibt trotzdem: eine lesende Funktion gehoert als STABLE deklariert.
-- Gelesen wird sie mit dem vorhandenen
-- `SA.supabase.get('rpc/polymarket_latest_prices', ...)`, ohne dass `app.js`
-- eine neue Methode braucht.
--
-- DISTINCT ON nutzt den bestehenden Index idx_pm_prices_cid_ts
-- (condition_id, ts DESC). `UNIQUE(condition_id, ts)` macht die Auswahl
-- eindeutig — es gibt keine zwei Zeilen mit gleichem Zeitpunkt.

-- CREATE OR REPLACE statt DROP + CREATE: ein Drop kann an spaeteren
-- Abhaengigkeiten scheitern und verwirft die einzeln erteilten
-- Ausfuehrungsrechte. Die Signatur bleibt `(text[])`, ein Standardwert
-- aendert sie nicht.
--
-- `DEFAULT NULL`, damit ein Aufruf OHNE Parameter „alle Maerkte" bedeutet:
-- ein weggelassener HTTP-Parameter und SQL-NULL sind nicht automatisch
-- dasselbe (Codex, Pruefung der Migration).
CREATE OR REPLACE FUNCTION public.polymarket_latest_prices(
    p_condition_ids TEXT[] DEFAULT NULL)
RETURNS TABLE (
    condition_id TEXT,
    ts           TIMESTAMPTZ,
    yes_price    NUMERIC,
    volume_24h   NUMERIC,
    spread       NUMERIC,
    source       TEXT,
    price_kind   TEXT,
    bid          NUMERIC,
    ask          NUMERIC,
    fetched_at   TIMESTAMPTZ
)
LANGUAGE sql
STABLE
AS $$
    SELECT DISTINCT ON (p.condition_id)
           p.condition_id, p.ts, p.yes_price, p.volume_24h, p.spread,
           p.source, p.price_kind, p.bid, p.ask, p.fetched_at
      FROM public.polymarket_prices p
     WHERE p_condition_ids IS NULL
        OR p.condition_id = ANY (p_condition_ids)
     ORDER BY p.condition_id, p.ts DESC;
$$;

COMMENT ON FUNCTION public.polymarket_latest_prices(TEXT[]) IS
    'Neueste Preiszeile je condition_id. NULL als Argument = alle Maerkte. '
    'Ersetzt die Reduktion im Browser, bei der ein haeufig aktualisierter '
    'Markt einen selten aktualisierten aus der Antwort verdraengen konnte.';

GRANT EXECUTE ON FUNCTION public.polymarket_latest_prices(TEXT[])
    TO anon, authenticated, service_role;

-- PostgREST haelt ein Abbild des Schemas im Speicher. Ohne diesen Anstoss ist
-- die neue Funktion ueber HTTP NICHT sichtbar — der Aufruf endet mit „Could
-- not find the function", obwohl sie in der Datenbank steht. Supabase setzt
-- dafuer ueblicherweise einen Event-Trigger; dieses NOTIFY ist die
-- ausdrueckliche Absicherung und schadet nicht, wenn der Trigger existiert.
NOTIFY pgrst, 'reload schema';

COMMIT;

-- ╔══════════════════════════════════════════════════════════════════════════╗
-- ║ ABNAHME — nach dem Ausfuehren bitte laufen lassen                       ║
-- ╚══════════════════════════════════════════════════════════════════════════╝
--
-- Die Migration ist erst dann nachgewiesen, wenn diese Abfragen das Erwartete
-- liefern. „Keine Fehlermeldung" ist kein Nachweis.
--
-- (1) Alle acht Spalten da?  -> erwartet: 8 Zeilen
--
-- SELECT table_name, column_name
--   FROM information_schema.columns
--  WHERE (table_name, column_name) IN (
--          ('polymarket_prices',  'price_kind'),
--          ('polymarket_prices',  'bid'),
--          ('polymarket_prices',  'ask'),
--          ('polymarket_prices',  'fetched_at'),
--          ('polymarket_markets', 'status'),
--          ('polymarket_markets', 'status_checked_at'),
--          ('polymarket_markets', 'last_fetch_state'),
--          ('polymarket_markets', 'last_fetch_at'))
--  ORDER BY table_name, column_name;
--
-- (2) Sind alle Preiszeilen noch UNKLASSIFIZIERT?  -> erwartet:
--     bestand = gesamt, klassifiziert = 0.
--     Das belegt NICHT, dass der Bestand unveraendert ist — dafuer brauchte
--     es einen Vorher-Nachher-Vergleich. Es belegt, dass die Migration
--     keine Preisart erfunden hat.
--
-- SELECT count(*) AS gesamt,
--        count(*) FILTER (WHERE price_kind IS NULL) AS bestand,
--        count(*) FILTER (WHERE price_kind IS NOT NULL) AS klassifiziert
--   FROM polymarket_prices;
--
-- (3) Verletzt eine Bestandszeile den Wertebereich?  -> zur KENNTNIS, nicht
--     zum Reparieren. Diese Zeilen bleiben, wie sie sind; der neue Code
--     behandelt sie als nicht bewertbar. Eine nachtraegliche Korrektur waere
--     eine Behauptung ueber Daten, die wir nicht haben.
--
-- SELECT count(*) FILTER (WHERE yes_price < 0 OR yes_price > 1) AS ausserhalb,
--        count(*) FILTER (WHERE spread < 0)                     AS negativer_spread
--   FROM polymarket_prices;
--
-- (4) Funktion lesbar, und liefert sie GENAU eine Zeile pro Markt?
--     -> erwartet: maerkte_mit_preis = zeilen
--
-- SELECT count(*) AS zeilen,
--        count(DISTINCT condition_id) AS maerkte_mit_preis
--   FROM polymarket_latest_prices(NULL);
--
-- (5) Und stimmt sie mit einer unabhaengig gerechneten Referenz ueberein?
--     -> erwartet: 0 Zeilen (keine Abweichung)
--
-- WITH referenz AS (
--     SELECT condition_id, max(ts) AS ts
--       FROM polymarket_prices
--      GROUP BY condition_id
-- )
-- SELECT r.condition_id, r.ts AS referenz_ts, f.ts AS funktion_ts
--   FROM referenz r
--   FULL JOIN polymarket_latest_prices(NULL) f USING (condition_id)
--  WHERE r.ts IS DISTINCT FROM f.ts;
--
-- (6) Darf anon die Funktion ausfuehren?  -> erwartet: beide true
--
-- SELECT has_function_privilege('anon', 'public.polymarket_latest_prices(text[])', 'EXECUTE')          AS anon_darf,
--        has_function_privilege('authenticated', 'public.polymarket_latest_prices(text[])', 'EXECUTE') AS auth_darf;
--
-- (7) Und die Probe aufs Exempel: das Privileg zu HABEN ist nicht dasselbe wie
--     durchzukommen — die RLS der Basistabelle muss auch greifen. Deshalb ein
--     echter Lauf in der Rolle anon, mit ROLLBACK.
--     -> erwartet: eine Zeile (sofern Bestand da ist)
--
-- BEGIN;
-- SET LOCAL ROLE anon;
-- SELECT * FROM public.polymarket_latest_prices(NULL) LIMIT 1;
-- ROLLBACK;
--
-- (8) Zuletzt der Weg, den das Frontend wirklich nimmt — ueber HTTP, nicht
--     ueber SQL. Erst das beweist, dass PostgREST die Funktion kennt:
--
--     curl -s -H "apikey: <ANON_KEY>" \
--       "<PROJEKT-URL>/rest/v1/rpc/polymarket_latest_prices" | head -c 300
