-- 002_supply_table.sql
-- BorAnalytics v2: Adds USGS global supply and reserves tracking

CREATE TABLE IF NOT EXISTS supply (
    id SERIAL PRIMARY KEY,
    year INT NOT NULL,
    country_id INT REFERENCES countries(id) ON DELETE CASCADE,
    production_tons FLOAT NOT NULL,
    reserves_tons FLOAT,
    source_report TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(year, country_id)
);
