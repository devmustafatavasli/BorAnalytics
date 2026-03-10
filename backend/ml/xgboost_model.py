import os
import sys
import logging
import json
import joblib
import pandas as pd
from sqlalchemy.orm import Session
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db.database import SessionLocal
from db.models import ModelRun

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../models"))

def train_xgboost(df: pd.DataFrame) -> dict:
    """
    Trains an XGBoost Regressor on the provided DataFrame to predict `value_usd`.
    Walk-forward split: train <= 2018, test >= 2019.
    """
    if df.empty:
        logger.error("Empty dataframe provided to training.")
        return {}
        
    required_cols = ['year', 'value_usd', 'lag_1_value', 'lag_2_value', 'lag_3_value', 
                     'rolling_mean_3_value', 'gdp_importer', 'boron_price_index']
    
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        logger.error(f"Missing required columns for XGBoost training: {missing}")
        return {}

    # Feature List
    features = ['lag_1_value', 'lag_2_value', 'lag_3_value', 
                'rolling_mean_3_value', 'gdp_importer', 'boron_price_index']
    target = 'value_usd'
    
    # Train / Test Split (Walk-forward)
    train_df = df[df['year'] <= 2018]
    test_df = df[df['year'] >= 2019]
    
    if test_df.empty or train_df.empty:
        logger.error("Not enough data to split into train and test.")
        return {}
        
    X_train, y_train = train_df[features], train_df[target]
    X_test, y_test = test_df[features], test_df[target]
    
    # Model Setup
    model_params = {
        'n_estimators': 300,
        'max_depth': 4,
        'learning_rate': 0.05,
        'random_state': 42
    }
    
    model = XGBRegressor(**model_params)
    logger.info("Training XGBoost Regressor...")
    model.fit(X_train, y_train)
    
    # Evaluation
    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    rmse = mean_squared_error(y_test, preds, squared=False)
    r2 = r2_score(y_test, preds)
    
    logger.info(f"Evaluation -> MAE: {mae:.2f}, RMSE: {rmse:.2f}, R2: {r2:.2f}")
    
    # Save Artifact
    os.makedirs(MODELS_DIR, exist_ok=True)
    model_path = os.path.join(MODELS_DIR, 'xgboost_revenue.pkl')
    joblib.dump(model, model_path)
    logger.info(f"Model saved to {model_path}")
    
    # Log to Database
    db: Session = SessionLocal()
    try:
        run = ModelRun(
            model_type='xgboost',
            mae=float(mae),
            rmse=float(rmse),
            r2=float(r2),
            params_json=model_params
        )
        db.add(run)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error logging model run: {e}")
    finally:
        db.close()
        
    return {
        "mae": float(mae),
        "rmse": float(rmse),
        "r2": float(r2),
        "model_path": model_path
    }

if __name__ == "__main__":
    csv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/processed/ml_features.csv"))
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        train_xgboost(df)
    else:
        logger.error(f"Feature dataset not found at {csv_path}. Run feature_engineering.py first.")
