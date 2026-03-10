-- 001_init.sql

CREATE TABLE countries (
    id SERIAL PRIMARY KEY,
    iso3 VARCHAR(3) UNIQUE NOT NULL,
    name VARCHAR NOT NULL,
    region VARCHAR
);
CREATE INDEX idx_countries_iso3 ON countries(iso3);

CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    hs_code VARCHAR UNIQUE NOT NULL,
    name VARCHAR NOT NULL,
    category VARCHAR
);
CREATE INDEX idx_products_hs_code ON products(hs_code);

CREATE TABLE exports (
    year INTEGER NOT NULL,
    country_id INTEGER NOT NULL REFERENCES countries(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    volume_tons DOUBLE PRECISION NOT NULL,
    value_usd DOUBLE PRECISION NOT NULL,
    anomaly_flag BOOLEAN DEFAULT FALSE,
    anomaly_score DOUBLE PRECISION,
    PRIMARY KEY (year, country_id, product_id)
);
CREATE INDEX idx_exports_country_id ON exports(country_id);
CREATE INDEX idx_exports_product_id ON exports(product_id);
CREATE INDEX idx_exports_year ON exports(year);

CREATE TABLE production (
    year INTEGER NOT NULL,
    facility VARCHAR NOT NULL,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    volume_tons DOUBLE PRECISION NOT NULL,
    PRIMARY KEY (year, facility, product_id)
);

CREATE TABLE model_runs (
    id SERIAL PRIMARY KEY,
    model_type VARCHAR NOT NULL,
    trained_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    mae DOUBLE PRECISION,
    rmse DOUBLE PRECISION,
    r2 DOUBLE PRECISION,
    params_json JSONB
);
CREATE INDEX idx_model_runs_model_type ON model_runs(model_type);

CREATE TABLE predictions (
    country_id INTEGER NOT NULL REFERENCES countries(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    year INTEGER NOT NULL,
    model_run_id INTEGER NOT NULL REFERENCES model_runs(id) ON DELETE CASCADE,
    predicted_value DOUBLE PRECISION NOT NULL,
    lower_ci DOUBLE PRECISION,
    upper_ci DOUBLE PRECISION,
    PRIMARY KEY (country_id, product_id, year, model_run_id)
);
CREATE INDEX idx_predictions_country_id ON predictions(country_id);
CREATE INDEX idx_predictions_product_id ON predictions(product_id);
