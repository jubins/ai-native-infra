-- Catalog schema and seed data.
-- This file recreates the chapter 2 products table so the ch03 companion
-- can be run standalone. If you already have the chapter 2 platform up,
-- you can skip this and point DATABASE_URL at that database instead.

CREATE TABLE IF NOT EXISTS products (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    price_cents INTEGER NOT NULL CHECK (price_cents >= 0),
    description TEXT,
    category    TEXT
);

INSERT INTO products (id, name, price_cents, description, category) VALUES
    ('p_001', 'Merino Wool Jacket', 8900,
        'Lightweight merino wool jacket suitable for cool weather.',
        'outerwear'),
    ('p_002', 'Fleece Pullover', 5900,
        'Mid-weight fleece pullover for layering on cold days.',
        'outerwear'),
    ('p_003', 'Down Puffer Jacket', 14900,
        'Insulated down puffer jacket for sub-zero temperatures.',
        'outerwear'),
    ('p_004', 'Summer Linen Shirt', 3900,
        'Breathable linen shirt for warm summer days.',
        'tops'),
    ('p_005', 'Rain Shell', 7900,
        'Waterproof rain shell with sealed seams.',
        'outerwear'),
    ('p_006', 'Hiking Backpack', 11900,
        'Forty-litre hiking backpack with hydration sleeve.',
        'accessories'),
    ('p_007', 'Wool Beanie', 1900,
        'Knit wool beanie, one size fits most.',
        'accessories')
ON CONFLICT (id) DO NOTHING;
