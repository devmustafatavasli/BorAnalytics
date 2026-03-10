-- 005_shap_table.sql
-- BorAnalytics v2: Adds SHAP feature importance table

CREATE TABLE IF NOT EXISTS shap_explanations (
    id SERIAL PRIMARY KEY,
    prediction_id VARCHAR(255) NOT NULL, -- Logical FK since prediction.id varies by complex unique_ids / years / model_runs
    feature_name VARCHAR(255) NOT NULL,
    shap_value FLOAT NOT NULL,
    rank INT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- We define an arbitrary unique constraint logically linking top 3 ranks per prediction
CREATE UNIQUE INDEX idx_shap_pred_rank ON shap_explanations(prediction_id, rank);
