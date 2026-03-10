-- 007_exchange_rates.sql
-- BorAnalytics v3: Adds annual ECB exchange rate data

CREATE TABLE IF NOT EXISTS exchange_rates (
    id SERIAL PRIMARY KEY,
    year INT UNIQUE NOT NULL,
    usd_per_eur FLOAT NOT NULL,
    try_per_eur FLOAT NOT NULL,
    usd_per_try FLOAT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
