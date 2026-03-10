-- 008_price_index_extensions.sql
-- BorAnalytics v3: Extends price_index table with local currency and constant 2010 tracking

ALTER TABLE price_index ADD COLUMN IF NOT EXISTS unit_price_try_per_tonne FLOAT;
ALTER TABLE price_index ADD COLUMN IF NOT EXISTS unit_price_usd_real_2010 FLOAT;
ALTER TABLE price_index ADD COLUMN IF NOT EXISTS try_z_score FLOAT;
ALTER TABLE price_index ADD COLUMN IF NOT EXISTS is_anomaly_try BOOLEAN DEFAULT FALSE;
