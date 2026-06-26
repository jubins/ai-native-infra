-- listing_2_12 — compose/postgres-init.sql
-- Creates three isolated databases (one per service) and seeds the
-- catalog with four products.  The checkout and orders schemas are
-- minimal stubs; they grow in later chapters.
--
-- This file is mounted as the Docker entrypoint init script, so it
-- runs automatically when the Postgres container first starts.

-- ── databases ────────────────────────────────────────────────────────────────

CREATE DATABASE catalog;   -- A
CREATE DATABASE checkout;
CREATE DATABASE orders;

-- ── catalog schema ───────────────────────────────────────────────────────────

\c catalog;                -- B

CREATE TABLE products (
    id          TEXT    PRIMARY KEY,         -- C
    name        TEXT    NOT NULL,
    price_cents INTEGER NOT NULL,            -- D
    description TEXT
);

INSERT INTO products VALUES                  -- E
    ('p_001', 'Merino Wool Jacket',  8900,  'Warm mid-weight winter jacket'),
    ('p_002', 'Down Puffer Coat',   12900,  'Heavy winter coat for cold climates'),
    ('p_003', 'Rain Shell',          6900,  'Lightweight waterproof jacket'),
    ('p_004', 'Summer Linen Shirt',  3900,  'Breathable shirt for hot weather');

-- The companion repository contains a longer seed (50 products) for
-- readers who want a fuller catalog to test semantic search against.

-- ── checkout schema ──────────────────────────────────────────────────────────

\c checkout;

CREATE TABLE orders (
    id          SERIAL  PRIMARY KEY,
    customer_id TEXT    NOT NULL,
    status      TEXT    NOT NULL DEFAULT 'pending',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ── orders schema ────────────────────────────────────────────────────────────

\c orders;

CREATE TABLE order_events (
    id          SERIAL  PRIMARY KEY,
    order_id    INTEGER NOT NULL,
    event_type  TEXT    NOT NULL,
    payload     JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- A — One database per service: logical isolation today, physical
--     isolation later if any service grows enough to need its own instance.
-- B — \c switches the active database so subsequent DDL lands there.
-- C — Stable string IDs (p_001) travel cleanly across services and URLs
--     without the collision concerns of auto-increment integers.
-- D — Prices in integer cents avoid the floating-point rounding errors
--     that have caused checkout incidents in real systems.
-- E — Four products are enough for the listings in this chapter.
