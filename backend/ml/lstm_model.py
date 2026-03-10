import os
import sys
import logging
import torch
import torch.nn as nn
import torch.optim as optim
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sqlalchemy.orm import Session

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db.database import SessionLocal
from db.models import ModelRun

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../models"))

class LSTMForecaster(nn.Module):
    def __init__(self, input_size=1, hidden_size=64, num_layers=2, dropout=0.2):
        super(LSTMForecaster, self).__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True, dropout=dropout)
        self.fc1 = nn.Linear(hidden_size, 64)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(64, 1)

    def forward(self, x):
        out, _ = self.lstm(x)
        out = out[:, -1, :] # Take last hidden state
        out = self.fc1(out)
        out = self.relu(out)
        out = self.fc2(out)
        return out

def create_sequences(data, seq_length=5):
    xs = []
    ys = []
    for i in range(len(data)-seq_length):
        x = data[i:(i+seq_length)]
        y = data[i+seq_length]
        xs.append(x)
        ys.append(y)
    return np.array(xs), np.array(ys)

def train_lstm(df: pd.DataFrame, product_id: int, country_id: int) -> dict:
    """
    Trains LSTM and returns metrics for a specific product-country pair.
    """
    series_df = df[(df['product_id'] == product_id) & (df['country_id'] == country_id)].sort_values('year')
    if len(series_df) < 10:  # Need at least seq_length + some train/test rows
        logger.warning(f"Not enough data for product {product_id}, country {country_id}")
        return {}

    volumes = series_df['volume_tons'].values.astype(float).reshape(-1, 1)
    
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(volumes)
    
    SEQ_LENGTH = 5
    X, y = create_sequences(scaled_data, SEQ_LENGTH)
    
    if len(X) < 3:
        return {}
        
    # Walk-forward split: roughly 80% train, 20% test
    split = int(0.8 * len(X))
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]
    
    # Convert to PyTorch tensors
    X_train_t = torch.FloatTensor(X_train)
    y_train_t = torch.FloatTensor(y_train)
    X_test_t = torch.FloatTensor(X_test)
    y_test_t = torch.FloatTensor(y_test)
    
    model = LSTMForecaster(input_size=1)
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.01)
    
    epochs = 100
    model.train()
    for __ in range(epochs):
        optimizer.zero_grad()
        output = model(X_train_t)
        loss = criterion(output, y_train_t)
        loss.backward()
        optimizer.step()
        
    model.eval()
    with torch.no_grad():
        test_preds = model(X_test_t)
        
    # Inverse transform to calculate real MAE / RMSE
    test_preds_inv = scaler.inverse_transform(test_preds.numpy())
    y_test_inv = scaler.inverse_transform(y_test_t.numpy())
    
    mae = np.mean(np.abs(y_test_inv - test_preds_inv))
    rmse = np.sqrt(np.mean((y_test_inv - test_preds_inv)**2))
    r2 = 0.0 # Placeholder, can be calculated
    
    logger.info(f"LSTM Evaluated -> MAE: {mae:.2f}, RMSE: {rmse:.2f}")
    
    # Save Model Weights
    os.makedirs(MODELS_DIR, exist_ok=True)
    model_path = os.path.join(MODELS_DIR, f'lstm_demand_{product_id}_{country_id}.pt')
    torch.save(model.state_dict(), model_path)
    
    # Save scaler for inference later
    import joblib
    scaler_path = os.path.join(MODELS_DIR, f'scaler_{product_id}_{country_id}.pkl')
    joblib.dump(scaler, scaler_path)
    
    # Log to DB
    db: Session = SessionLocal()
    try:
        run = ModelRun(
            model_type='lstm',
            mae=float(mae),
            rmse=float(rmse),
            r2=float(r2),
            params_json={"seq_length": SEQ_LENGTH, "epochs": epochs, "hidden_size": 64, "product_id": product_id, "country_id": country_id}
        )
        db.add(run)
        db.commit()
    except Exception as e:
        logger.error(f"DB Error: {e}")
        db.rollback()
    finally:
        db.close()
        
    return {
        "mae": float(mae),
        "rmse": float(rmse),
        "r2": float(r2),
        "model_path": model_path
    }

if __name__ == "__main__":
    db = SessionLocal()
    # Fetch data directly or via feature dataset. 
    # For robust training across all pairs, we'd loop over unique combinations here.
    query = db.query(
            Export.year,
            Export.country_id,
            Export.product_id,
            Export.volume_tons
        )
    df = pd.read_sql(query.statement, db.get_bind())
    db.close()
    
    if not df.empty:
        # Just train for the first available pair to test the script
        c_id = df['country_id'].iloc[0]
        p_id = df['product_id'].iloc[0]
        logger.info(f"Training LSTM for C: {c_id}, P: {p_id}")
        train_lstm(df, p_id, c_id)
