-- Orders schema for the ch03 companion.
-- The products table is a read-only copy of the catalog seed data so the
-- orders service can resolve SKU prices without a cross-service call at
-- companion scale. In production this would be an internal RPC to the
-- catalog service.

CREATE TABLE IF NOT EXISTS products (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    price_cents INTEGER NOT NULL CHECK (price_cents >= 0)
);

INSERT INTO products (id, name, price_cents) VALUES
    ('p_001', 'Merino Wool Jacket', 8900),
    ('p_002', 'Fleece Pullover',    5900),
    ('p_003', 'Down Puffer Jacket', 14900),
    ('p_004', 'Summer Linen Shirt', 3900),
    ('p_005', 'Rain Shell',         7900),
    ('p_006', 'Hiking Backpack',    11900),
    ('p_007', 'Wool Beanie',        1900)
ON CONFLICT (id) DO NOTHING;

CREATE TABLE IF NOT EXISTS orders (
    id          TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    total_cents INTEGER NOT NULL CHECK (total_cents >= 0),
    status      TEXT NOT NULL DEFAULT 'PENDING',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- The idempotency_keys table is also created at startup by main.py via
-- idempotency.CREATE_TABLE; this block ensures it exists even if the
-- service has not started yet (e.g. during a psql inspection).
CREATE TABLE IF NOT EXISTS idempotency_keys (
    key         TEXT PRIMARY KEY,
    response    JSONB NOT NULL,
    status_code INT   NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
