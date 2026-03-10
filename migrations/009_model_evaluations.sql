-- 009_model_evaluations.sql
-- BorAnalytics v3: Adds model evaluation metrics 

CREATE TABLE IF NOT EXISTS model_evaluations (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    hierarchy_level VARCHAR(50) NOT NULL,
    unique_id VARCHAR(100) NOT NULL,
    mae FLOAT,
    rmse FLOAT,
    mase FLOAT,
    crps FLOAT,
    dm_statistic FLOAT,
    dm_pvalue FLOAT,
    eval_set_start INT NOT NULL,
    eval_set_end INT NOT NULL,
    evaluated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(model_name, unique_id)
);
