-- 004b_alter_predictions.sql
-- Accommodate unique_id, model_type, and scenario_tag for v2 requirements

-- Drop previous composite primary key to allow nulls in country_id/product_id
ALTER TABLE predictions DROP CONSTRAINT IF EXISTS predictions_pkey;

ALTER TABLE predictions ALTER COLUMN country_id DROP NOT NULL;
ALTER TABLE predictions ALTER COLUMN product_id DROP NOT NULL;

-- Add new v2 reporting columns
ALTER TABLE predictions ADD COLUMN IF NOT EXISTS unique_id VARCHAR(100);
ALTER TABLE predictions ADD COLUMN IF NOT EXISTS model_type VARCHAR(100);
ALTER TABLE predictions ADD COLUMN IF NOT EXISTS scenario_tag VARCHAR(100);

-- Recreate a safer Primary Key mapping
ALTER TABLE predictions ADD CONSTRAINT predictions_pkey PRIMARY KEY (year, model_run_id, unique_id, scenario_tag) USING INDEX TABLESPACE pg_default;
