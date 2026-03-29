-- 006_anomaly_context.sql
-- BorAnalytics v2: Adds anomaly reasoning explanation string support

ALTER TABLE exports ADD COLUMN IF NOT EXISTS anomaly_context TEXT;
