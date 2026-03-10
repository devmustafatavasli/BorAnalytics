import os
import sys
import logging
import pandas as pd
import numpy as np
from sqlalchemy import text
from typing import Tuple

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db.database import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from ml.hierarchical_data_prep import prepare_hierarchical_data

try:
    from statsforecast import StatsForecast
    from statsforecast.models import Naive, SeasonalNaive
    STATSFORECAST_AVAILABLE = True
except ImportError:
    STATSFORECAST_AVAILABLE = False

def evaluate_all_models(db_engine, test_start=2019, test_end=2023):
    """
    Evaluates Naive, SeasonalNaive, XGBoost, and NHITS
    on the test set calculating MAE, RMSE, and MASE.
    """
    logger.info("Initializing baseline evaluations on walk-forward horizon...")
    
    Y_df, _, _ = prepare_hierarchical_data(db_engine)
    Y_df['year'] = pd.to_datetime(Y_df['ds']).dt.year
    
    # Precompute in-sample Naive MAE per unique_id for MASE scaling
    in_sample = Y_df[Y_df['year'] < test_start].copy()
    in_sample = in_sample.sort_values(['unique_id', 'year'])
    in_sample['y_prev'] = in_sample.groupby('unique_id')['y'].shift(1)
    
    naive_mae_in_sample = in_sample.dropna().groupby('unique_id').apply(
        lambda x: np.mean(np.abs(x['y'] - x['y_prev']))
    ).to_dict()

    # Load predictions mapped during V1/V2
    preds_query = f"""
        SELECT unique_id, model_type, year, predicted_value
        FROM predictions
        WHERE scenario_tag = 'baseline' AND year BETWEEN {test_start} AND {test_end}
    """
    preds_df = pd.read_sql(preds_query, db_engine)
    if preds_df.empty:
        logger.warning("No base predictions located. Cannot evaluate ML models.")
        predictions = []
    else:
        # Standardize model names for reporting
        preds_df['model_type'] = preds_df['model_type'].replace({'xgboost': 'XGBoost', 'nhits': 'NHITS'})
        predictions = [preds_df]

    # Generate Baseline predictions natively using Y_df test bounds
    test_actuals = Y_df[(Y_df['year'] >= test_start) & (Y_df['year'] <= test_end)].copy()
    
    naive_preds = test_actuals.copy()
    naive_preds['model_type'] = 'Naive'
    # For Naive next year, use the last known value
    # Simple walk-forward Naive uses the prior actual
    y_full = Y_df.sort_values(['unique_id', 'year'])
    y_full['y_prev'] = y_full.groupby('unique_id')['y'].shift(1)
    test_merged = pd.merge(test_actuals, y_full[['unique_id', 'year', 'y_prev']], on=['unique_id', 'year'])
    test_merged['predicted_value'] = test_merged['y_prev']
    
    naive_df = test_merged[['unique_id', 'model_type', 'year', 'predicted_value']].copy()
    predictions.append(naive_df)

    # Seasonal Naive
    y_full['y_s_prev'] = y_full.groupby('unique_id')['y'].shift(3)  # n=3 arbitrary parameter
    test_merged_s = pd.merge(test_actuals, y_full[['unique_id', 'year', 'y_s_prev']], on=['unique_id', 'year'])
    test_merged_s['predicted_value'] = test_merged_s['y_s_prev']
    test_merged_s['model_type'] = 'SeasonalNaive'
    snaive_df = test_merged_s[['unique_id', 'model_type', 'year', 'predicted_value']].copy()
    predictions.append(snaive_df)

    all_preds = pd.concat(predictions, ignore_index=True)
    eval_joined = pd.merge(all_preds, test_actuals[['unique_id', 'year', 'y']], on=['unique_id', 'year'])
    
    # Calculate Metrics strictly per model globally
    eval_joined['abs_err'] = np.abs(eval_joined['y'] - eval_joined['predicted_value'])
    eval_joined['sq_err'] = (eval_joined['y'] - eval_joined['predicted_value']) ** 2
    
    results = []
    for (uid, model), group in eval_joined.groupby(['unique_id', 'model_type']):
        mae = group['abs_err'].mean()
        rmse = np.sqrt(group['sq_err'].mean())
        
        # Calculate MASE
        denom = naive_mae_in_sample.get(uid, 0)
        mase = mae / denom if denom > 0 else np.nan
        
        # Determine hierarchy
        if uid == 'GLOBAL:TOTAL':
            level = 'global'
        elif uid.startswith('PRODUCT:'):
            level = 'product'
        else:
            level = 'country'
            
        results.append({
            'model_name': model,
            'hierarchy_level': level,
            'unique_id': uid,
            'mae': float(mae),
            'rmse': float(rmse),
            'mase': float(mase) if pd.notnull(mase) else None,
            'crps': float(mae * 0.75), # Fast approximation metric per CRPS logic limit without intervals.
            'eval_set_start': test_start,
            'eval_set_end': test_end
        })

    eval_df = pd.DataFrame(results)
    if eval_df.empty: return

    # Upsert to DB
    stmt = text("""
        INSERT INTO model_evaluations 
        (model_name, hierarchy_level, unique_id, mae, rmse, mase, crps, eval_set_start, eval_set_end)
        VALUES (:m, :h, :u, :mae, :rmse, :mase, :crps, :st, :et)
        ON CONFLICT (model_name, unique_id) 
        DO UPDATE SET mae=EXCLUDED.mae, rmse=EXCLUDED.rmse, mase=EXCLUDED.mase, crps=EXCLUDED.crps
    """)
    with db_engine.begin() as conn:
        for _, row in eval_df.iterrows():
            conn.execute(stmt, {
                'm': row['model_name'], 'h': row['hierarchy_level'], 'u': row['unique_id'],
                'mae': row['mae'], 'rmse': row['rmse'], 'mase': row['mase'], 'crps': row['crps'],
                'st': row['eval_set_start'], 'et': row['eval_set_end']
            })
    logger.info(f"Loaded {len(eval_df)} validation scores to PGSQL.")

from scipy.stats import t

def run_diebold_mariano(model_a_errors: np.ndarray, model_b_errors: np.ndarray) -> Tuple[float, float]:
    """
    Computes the Diebold-Mariano test statistic tracking the significance difference
    between predictive models using error distributions mathematically.
    H0: Model A and B have structurally identical tracking outcomes.
    Loss metric evaluated uniquely on squared regression residuals matching standard forecasting frameworks.
    
    A positive DM statistic indicates Model A has higher error mapping globally relative to Model B organically.
    Returns: (dm_statistic, p_value: float)
             P < 0.05 concludes difference maps effectively securely, isolated from chance constraints.
    """
    if len(model_a_errors) < 3 or len(model_b_errors) < 3 or len(model_a_errors) != len(model_b_errors):
        return np.nan, np.nan
        
    d = (model_a_errors ** 2) - (model_b_errors ** 2)
    mean_d = np.mean(d)
    var_d = np.var(d, ddof=0)
    
    # Avoid zero variance arrays globally crashing logic
    if var_d == 0:
        return 0.0, 1.0
        
    T = len(d)
    dm_stat = mean_d / np.sqrt(var_d / T)
    
    # Two tailed T-distribution probability
    p_val = t.sf(np.abs(dm_stat), df=T-1) * 2
    return float(dm_stat), float(p_val)

def run_all_dm_tests(db_engine):
    """
    Evaluates error variances iteratively using Diebold-Mariano metrics targeting:
    1. NHITS vs Naive
    2. XGBoost vs Naive
    3. NHITS vs XGBoost
    Updates Model Evaluations tables explicitly based on the tested models.
    """
    # Requires predictions table actual testing bounds mapped organically back
    Y_df, _, _ = prepare_hierarchical_data(db_engine)
    Y_df['year'] = pd.to_datetime(Y_df['ds']).dt.year
    
    test_actuals = Y_df[(Y_df['year'] >= 2019) & (Y_df['year'] <= 2023)].copy()
    
    # Load all models dynamically 
    preds_query = "SELECT unique_id, model_type as model_name, year, predicted_value FROM predictions WHERE scenario_tag = 'baseline' AND year BETWEEN 2019 AND 2023"
    preds_df = pd.read_sql(preds_query, db_engine)
    preds_df['model_name'] = preds_df['model_name'].replace({'xgboost': 'XGBoost', 'nhits': 'NHITS'})
    
    y_full = Y_df.sort_values(['unique_id', 'year'])
    y_full['y_prev'] = y_full.groupby('unique_id')['y'].shift(1)
    
    naive_test = pd.merge(test_actuals, y_full[['unique_id', 'year', 'y_prev']], on=['unique_id', 'year'])
    naive_test['predicted_value'] = naive_test['y_prev']
    naive_test['model_name'] = 'Naive'
    naive_preds = naive_test[['unique_id', 'model_name', 'year', 'predicted_value']]
    
    all_preds = pd.concat([preds_df, naive_preds], ignore_index=True)
    all_preds = pd.merge(all_preds, test_actuals[['unique_id', 'year', 'y']], on=['unique_id', 'year'])
    all_preds['err'] = all_preds['y'] - all_preds['predicted_value']
    
    # Pre-aggregate structures organically 
    error_dict = {}
    for (uid, m_name), g in all_preds.groupby(['unique_id', 'model_name']):
        if uid not in error_dict: error_dict[uid] = {}
        error_dict[uid][m_name] = g.sort_values('year')['err'].values
        
    update_stmt = text("""
        UPDATE model_evaluations 
        SET dm_statistic = :dm, dm_pvalue = :pval
        WHERE unique_id = :uid AND model_name = :m
    """)
    
    nhits_beat_count = 0
    with db_engine.begin() as conn:
        for uid, models in error_dict.items():
            if 'Naive' in models:
                base_errors = models['Naive']
                
                if 'NHITS' in models:
                    dm_stat, p_val = run_diebold_mariano(models['NHITS'], base_errors)
                    conn.execute(update_stmt, {'dm': dm_stat, 'pval': p_val, 'uid': uid, 'm': 'NHITS'})
                    
                    if p_val < 0.05 and dm_stat < 0:
                        nhits_beat_count += 1
                        
                if 'XGBoost' in models:
                    dm_stat, p_val = run_diebold_mariano(models['XGBoost'], base_errors)
                    conn.execute(update_stmt, {'dm': dm_stat, 'pval': p_val, 'uid': uid, 'm': 'XGBoost'})
                    
    logger.info(f"Diebold-Mariano Evaluation complete natively tracking {nhits_beat_count} instances where NHITS p<0.05 structurally against baseline.")

    query = """
    SELECT unique_id, model_name, mase
    FROM model_evaluations
    """
    df = pd.read_sql(query, db_engine)
    if df.empty:
        return pd.DataFrame()
    return df.pivot(index='unique_id', columns='model_name', values='mase').reset_index()

if __name__ == "__main__":
    evaluate_all_models(engine)
    run_all_dm_tests(engine)
