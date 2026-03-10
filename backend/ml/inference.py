import os
import sys
import logging
import joblib
import torch
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db.database import SessionLocal
from db.models import Export, Prediction, ModelRun, Country, Product
from ml.lstm_model import LSTMForecaster

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../models"))

def run_lstm_inference(horizon_years: int = 5):
    """
    Runs inference using trained LSTM models to forecast N years into the future.
    Results are saved into the `predictions` DB table.
    """
    db: Session = SessionLocal()
    try:
        # Get latest LSTM model run to attach predictions to
        latest_run = db.query(ModelRun).filter(ModelRun.model_type == 'lstm').order_by(ModelRun.trained_at.desc()).first()
        if not latest_run:
            logger.error("No LSTM model run found in DB.")
            return

        # Ideally, we query available model weights in MODELS_DIR
        # e.g., lstm_demand_{product_id}_{country_id}.pt
        saved_models = [f for f in os.listdir(MODELS_DIR) if f.startswith('lstm_demand_') and f.endswith('.pt')]
        
        for model_file in saved_models:
            parts = model_file.replace('.pt', '').split('_')
            product_id = int(parts[2])
            country_id = int(parts[3])
            
            # Load Scaler
            scaler_path = os.path.join(MODELS_DIR, f'scaler_{product_id}_{country_id}.pkl')
            if not os.path.exists(scaler_path):
                continue
            scaler = joblib.load(scaler_path)
            
            # Load Model
            model_path = os.path.join(MODELS_DIR, model_file)
            model = LSTMForecaster(input_size=1)
            model.load_state_dict(torch.load(model_path))
            model.eval()
            
            # Get last 5 years of data for this pair to jumpstart the sequence
            last_exports = (
                db.query(Export.volume_tons, Export.year)
                .filter(Export.product_id == product_id, Export.country_id == country_id)
                .order_by(Export.year.desc())
                .limit(5)
                .all()
            )
            
            if len(last_exports) < 5:
                continue
                
            last_exports.reverse() # Sort chronologically
            last_volumes = np.array([e.volume_tons for e in last_exports]).reshape(-1, 1)
            last_year = last_exports[-1].year
            
            current_seq_scaled = scaler.transform(last_volumes).reshape(1, 5, 1)
            current_seq_tensor = torch.FloatTensor(current_seq_scaled)
            
            predictions_to_insert = []
            
            # Autoregressive generation
            with torch.no_grad():
                for i in range(1, horizon_years + 1):
                    pred_scaled = model(current_seq_tensor)
                    pred_value = scaler.inverse_transform(pred_scaled.numpy())[0][0]
                    
                    # Store prediction
                    predictions_to_insert.append({
                        "country_id": country_id,
                        "product_id": product_id,
                        "year": last_year + i,
                        "model_run_id": latest_run.id,
                        "predicted_value": float(max(0, pred_value)), # Ensure non-negative
                        "lower_ci": float(max(0, pred_value * 0.9)),  # Mock 10% interval
                        "upper_ci": float(pred_value * 1.1)
                    })
                    
                    # Update sequence window
                    current_seq_tensor = torch.cat(
                        (current_seq_tensor[:, 1:, :], pred_scaled.unsqueeze(1)), dim=1
                    )
                    
            if predictions_to_insert:
                stmt = insert(Prediction).values(predictions_to_insert)
                stmt = stmt.on_conflict_do_update(
                    index_elements=['country_id', 'product_id', 'year', 'model_run_id'],
                    set_={
                        'predicted_value': stmt.excluded.predicted_value,
                        'lower_ci': stmt.excluded.lower_ci,
                        'upper_ci': stmt.excluded.upper_ci
                    }
                )
                db.execute(stmt)
                db.commit()
                logger.info(f"Inserted {horizon_years} predictions for P:{product_id} C:{country_id}")

    except Exception as e:
        db.rollback()
        logger.error(f"Error during inference: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    run_lstm_inference(horizon_years=5)
