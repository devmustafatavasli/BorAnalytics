from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy import text
from ml.shap_explainer import generate_explanation_text

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

class HierarchicalForecastResponse(BaseModel):
    level: str
    unique_id: str
    forecasts: List[ForecastPoint]

@router.get("/hierarchical", response_model=HierarchicalForecastResponse)
def get_hierarchical(level: str = Query(..., regex="^(global|product|country)$"), 
                     product: Optional[str] = None, 
                     country: Optional[str] = None, 
                     horizon: int = 3, 
                     db: Session = Depends(get_db)):
    if level == 'global':
        uid = 'GLOBAL:TOTAL'
    elif level == 'product':
        if not product: raise HTTPException(status_code=400, detail="Product HS Code required for product level")
        uid = f"PRODUCT:{product}"
    else:
        if not product or not country: raise HTTPException(status_code=400, detail="Product and Country required for country level")
        uid = f"{product}:{country}"
        
    query = "SELECT year, predicted_value, lower_ci, upper_ci FROM predictions WHERE model_type='hierarchical_nhits' AND unique_id=:uid ORDER BY year ASC LIMIT :hor"
    results = db.execute(text(query), {"uid": uid, "hor": horizon}).fetchall()
    
    if not results:
        raise HTTPException(status_code=404, detail="No predictions found for this unique_id.")
        
    forecasts = [ForecastPoint(year=r.year, predicted_value=r.predicted_value, lower_ci=r.lower_ci, upper_ci=r.upper_ci) for r in results]
    return HierarchicalForecastResponse(level=level, unique_id=uid, forecasts=forecasts)

class FeatureContribution(BaseModel):
    feature_name: str
    shap_value: float
    rank: int
    direction: str

class ExplanationResponse(BaseModel):
    prediction_id: str
    explanation_text: str
    features: List[FeatureContribution]

@router.get("/explanation", response_model=ExplanationResponse)
def get_explanation(prediction_id: str, db: Session = Depends(get_db)):
    text_desc = generate_explanation_text(prediction_id, db)
    query = "SELECT feature_name, shap_value, rank FROM shap_explanations WHERE prediction_id=:pid ORDER BY rank ASC"
    results = db.execute(text(query), {"pid": prediction_id}).fetchall()
    if not results:
        raise HTTPException(status_code=404, detail="No explanation found.")
        
    feats = [FeatureContribution(feature_name=r.feature_name, shap_value=r.shap_value, rank=r.rank, direction="positive" if r.shap_value > 0 else "negative") for r in results]
    return ExplanationResponse(prediction_id=prediction_id, explanation_text=text_desc, features=feats)
