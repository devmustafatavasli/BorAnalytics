-- 003_mirror_imports.sql
-- BorAnalytics v2: Adds bilateral mirror imports table

CREATE TABLE IF NOT EXISTS mirror_imports (
    id SERIAL PRIMARY KEY,
    year INT NOT NULL,
    reporter_id INT REFERENCES countries(id) ON DELETE CASCADE,
    product_id INT REFERENCES products(id) ON DELETE CASCADE,
    import_value_usd FLOAT,
    import_weight_kg FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(year, reporter_id, product_id)
);
