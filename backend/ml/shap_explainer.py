import os
import sys
import logging
import joblib
import pandas as pd
import numpy as np
import shap
from sqlalchemy.orm import Session
from sqlalchemy import text

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db.database import engine
from feature_engineering import generate_xgboost_features

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODEL_PATH = os.path.join(os.path.dirname(__file__), '../../models/xgboost_revenue.pkl')

def explain_predictions(db_engine):
    """
    Computes SHAP feature importance for XGBoost predictions.
    Matches prediction structure and inserts 3 top features into shap_explanations table.
    """
    if not os.path.exists(MODEL_PATH):
        logger.warning(f"XGBoost model not found at {MODEL_PATH}. Skipping SHAP explanations.")
        return

    # 1. Load XGBoost
    model = joblib.load(MODEL_PATH)
    
    # 2. Get Features (Dynamic caching simulation)
    X_matrix = generate_xgboost_features(db_engine, inference=True)
    if X_matrix.empty:
        logger.warning("No feature matrix available for SHAP evaluation.")
        return
        
    X = X_matrix.drop(columns=['year', 'country_iso3', 'product_name'], errors='ignore')
    
    # Ensure numeric matrix
    X = X.select_dtypes(include=[np.number])
    feature_names = X.columns.tolist()

    # 3. Create TreeExplainer properly mapping underlying Booster
    logger.info("Computing SHAP values on X feature matrix...")
    explainer = shap.TreeExplainer(model.get_booster())
    shap_values = explainer.shap_values(X)

    # We fetch ALL xgboost predictions to pair 
    # Match row index from X_matrix to the DB prediction logically 
    preds_query = """
    SELECT unique_id, year, model_run_id 
    FROM predictions 
    WHERE model_type = 'xgboost'
    ORDER BY year ASC
    """
    preds_df = pd.read_sql(preds_query, db_engine)
    
    if preds_df.empty:
        logger.warning("No predictions found in Database to attach SHAP values.")
        return

    insert_stmt = text("""
        INSERT INTO shap_explanations (prediction_id, feature_name, shap_value, rank)
        VALUES (:p_id, :fname, :sval, :rank)
        ON CONFLICT DO NOTHING
    """)

    logger.info("Extracting Top 3 structural SHAP values per prediction...")
    with db_engine.begin() as conn:
        for idx, row in X_matrix.iterrows():
            if idx >= len(preds_df):
                break
                
            pred_record = preds_df.iloc[idx]
            logical_pred_id = f"{pred_record['unique_id']}_{pred_record['year']}_{pred_record['model_run_id']}"
            
            # 5. Extract top 3 absolute values
            row_shap_vals = shap_values[idx]
            abs_shap = np.abs(row_shap_vals)
            top_3_indices = np.argsort(abs_shap)[-3:][::-1] # Descending order of top 3
            
            for rank_idx, feat_idx in enumerate(top_3_indices):
                conn.execute(insert_stmt, {
                    "p_id": logical_pred_id,
                    "fname": feature_names[feat_idx],
                    "sval": float(row_shap_vals[feat_idx]),
                    "rank": rank_idx + 1
                })
                
    logger.info("SHAP explanations stored successfully.")

def generate_explanation_text(prediction_id: str, db_engine) -> str:
    """
    Queries shap_explanations and returns a dynamically formatted human-readable sentence.
    """
    query = """
    SELECT feature_name, shap_value, rank 
    FROM shap_explanations 
    WHERE prediction_id = :p_id 
    ORDER BY rank ASC
    """
    with db_engine.connect() as conn:
        results = conn.execute(text(query), {"p_id": prediction_id}).fetchall()
        
    if not results:
        return "No causal explanation available for this prediction."
        
    components = []
    for row in results:
        sign = "+" if row.shap_value > 0 else "-"
        # Convert absolute metric scales into percentage approximation text
        abs_value = abs(row.shap_value) * 100 
        components.append(f"{row.feature_name} ({sign}{abs_value:.1f}%)")
        
    base_str = "This forecast is primarily driven by " + ", ".join(components) + "."
    return base_str

if __name__ == "__main__":
    explain_predictions(engine)
