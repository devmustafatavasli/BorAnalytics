from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List

from db.database import get_db
from db.models import Prediction, ModelRun, Country, Product
from api.schemas.models import PredictionResponse, ForecastPoint

router = APIRouter(prefix="/api/predictions")

@router.get("/demand", response_model=PredictionResponse)
def get_demand_forecast(
    product_hs_code: str,
    country_iso3: str,
    horizon: int = Query(3, description="1, 3, or 5 years", le=5),
    db: Session = Depends(get_db)
):
    """
    Returns LSTM model forecasts with confidence intervals.
    """
    # Verify entities
    country = db.query(Country).filter(Country.iso3 == country_iso3).first()
    product = db.query(Product).filter(Product.hs_code == product_hs_code).first()
    
    if not country or not product:
        raise HTTPException(status_code=404, detail="Country or Product not found.")
        
    # Get latest LSTM model run
    latest_run = (
        db.query(ModelRun)
        .filter(ModelRun.model_type == 'lstm')
        .order_by(ModelRun.trained_at.desc())
        .first()
    )
    
    if not latest_run:
        raise HTTPException(status_code=404, detail="No LSTM model run found.")
        
    # Fetch predictions
    preds = (
        db.query(Prediction)
        .filter(
            Prediction.country_id == country.id,
            Prediction.product_id == product.id,
            Prediction.model_run_id == latest_run.id
        )
        .order_by(Prediction.year)
        .limit(horizon)
        .all()
    )
    
    if not preds:
        raise HTTPException(status_code=404, detail="No predictions found for this pairing.")
        
    forecasts = [
        ForecastPoint(
            year=p.year,
            predicted_value=p.predicted_value,
            lower_ci=p.lower_ci,
            upper_ci=p.upper_ci
        ) for p in preds
    ]
    
    return PredictionResponse(
        country_name=country.name,
        product_name=product.name,
        model_type=latest_run.model_type,
        mae=latest_run.mae,
        rmse=latest_run.rmse,
        forecasts=forecasts
    )
