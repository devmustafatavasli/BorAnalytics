import os
import sys
import logging
import joblib
import pandas as pd
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db.database import engine
from feature_engineering import generate_xgboost_features

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODEL_PATH = os.path.join(os.path.dirname(__file__), '../../models/xgboost_revenue.pkl')

def _run_and_store_scenario(db_engine, X_matrix: pd.DataFrame, scenario_tag: str, filter_mask=None) -> pd.DataFrame:
    """Helper method executing predictions via cached model dynamically without retraining."""
    if not os.path.exists(MODEL_PATH):
        logger.error("XGBoost model not found. Cannot evaluate scenarios.")
        return pd.DataFrame()

    model = joblib.load(MODEL_PATH)
    
    if filter_mask is not None:
        X_eval = X_matrix[filter_mask].copy()
    else:
        X_eval = X_matrix.copy()
        
    if X_eval.empty:
        return pd.DataFrame()

    X_numeric = X_eval.drop(columns=['year', 'country_iso3', 'product_name'], errors='ignore')
    
    # Evaluate scenario
    preds = model.predict(X_numeric)
    X_eval['scenario_value'] = preds
    X_eval['unique_id'] = X_eval['product_name'] + ':' + X_eval['country_iso3']
    
    # Store to PostgreSQL predictions matching table schema
    store_stmt = text("""
        INSERT INTO predictions (unique_id, year, model_run_id, model_type, scenario_tag, predicted_value)
        VALUES (:uid, :y, (SELECT MAX(id) FROM model_runs WHERE model_type='xgboost'), 'xgboost', :tag, :pval)
        ON CONFLICT (year, model_run_id, unique_id, scenario_tag) DO UPDATE 
        SET predicted_value = EXCLUDED.predicted_value
    """)

    # We also fetch baseline predictions logically to return deltas
    baseline_query = text("""
        SELECT unique_id, predicted_value as baseline_value 
        FROM predictions 
        WHERE model_type = 'xgboost' AND scenario_tag IS NULL 
            AND year = :y
    """)
    
    results = []
    
    with db_engine.begin() as conn:
        for _, row in X_eval.iterrows():
            uid = row['unique_id']
            pval = float(row['scenario_value'])
            y = int(row.get('year', 2024))
            
            # Insert Scenario prediction
            conn.execute(store_stmt, {
                "uid": uid,
                "y": y,
                "tag": scenario_tag,
                "pval": pval
            })
            
            # Evaluate baseline delta locally
            b_val = conn.execute(baseline_query, {"y": y}).fetchall()
            bpx = None
            for b in b_val:
                if b.unique_id == uid:
                    bpx = b.baseline_value
                    break
                    
            if bpx and bpx > 0:
                delta = ((pval - bpx) / bpx) * 100.0
            else:
                delta = 0.0
                
            results.append({
                "unique_id": uid,
                "baseline_value": bpx if bpx else 0,
                "scenario_value": pval,
                "delta_pct": delta
            })
            
    return pd.DataFrame(results)

def run_scenario_a(db_engine, competitor_increase_pct: float) -> pd.DataFrame:
    """Competitor Capacity Shock"""
    X_matrix = generate_xgboost_features(db_engine, inference=True)
    if X_matrix.empty: return pd.DataFrame()
    
    # Decrease Turkey's market share parameter inversely relative to global scale
    ratio = competitor_increase_pct / 100.0
    if 'market_share' in X_matrix.columns:
        X_matrix['market_share'] = X_matrix['market_share'] * (1 - ratio)
        
    tag = f"scenario_a_{competitor_increase_pct}"
    return _run_and_store_scenario(db_engine, X_matrix, tag)

def run_scenario_b(db_engine, country_iso3: str, new_gdp_growth: float) -> pd.DataFrame:
    """Targeted Economic Contraction / GDP Shock"""
    X_matrix = generate_xgboost_features(db_engine, inference=True)
    if X_matrix.empty: return pd.DataFrame()
    
    if 'gdp_importer' in X_matrix.columns:
        X_matrix.loc[X_matrix['country_iso3'] == country_iso3, 'gdp_importer'] = new_gdp_growth
        
    tag = f"scenario_b_{country_iso3}_{new_gdp_growth}"
    mask = X_matrix['country_iso3'] == country_iso3
    return _run_and_store_scenario(db_engine, X_matrix, tag, filter_mask=mask)

def run_scenario_c(db_engine, energy_sector_share: float) -> pd.DataFrame:
    """Sector Demand Shift"""
    X_matrix = generate_xgboost_features(db_engine, inference=True)
    if X_matrix.empty: return pd.DataFrame()
    
    baseline_share = 8.0
    ratio = energy_sector_share / baseline_share
    
    # Scale generic proxy metrics (like historic value rolling averages mapped to price spikes)
    price_proxy_cols = [c for c in X_matrix.columns if 'price' in c or 'value' in c]
    for c in price_proxy_cols:
        X_matrix[c] = X_matrix[c] * ratio
        
    tag = f"scenario_c_{energy_sector_share}"
    # Filter only HS codes tied physically to energy applications
    # (Assuming natural borates 2528 and tetraborates 2840 act heavily in energy glass)
    mask = X_matrix['product_name'].isin(["2528", "2840"])
    return _run_and_store_scenario(db_engine, X_matrix, tag, filter_mask=mask)

if __name__ == "__main__":
    df = run_scenario_a(engine, 10.0)
    logger.info(f"Scenario A Output shape: {df.shape}")
