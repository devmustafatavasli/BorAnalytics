-- 004_price_and_gap_cols.sql
-- BorAnalytics v2: Adds price index table and bilateral gap columns to exports

CREATE TABLE IF NOT EXISTS price_index (
    id SERIAL PRIMARY KEY,
    year INT NOT NULL,
    product_id INT REFERENCES products(id) ON DELETE CASCADE,
    unit_price_usd_per_tonne FLOAT,
    price_z_score FLOAT,
    is_anomaly_price BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(year, product_id)
);

ALTER TABLE exports ADD COLUMN IF NOT EXISTS mirror_value_usd FLOAT;
ALTER TABLE exports ADD COLUMN IF NOT EXISTS bilateral_gap_pct FLOAT;
