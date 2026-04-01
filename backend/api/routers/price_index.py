from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
from pydantic import BaseModel

from db.database import get_db

router = APIRouter(prefix="/analytics", tags=["analytics"])

class PriceIndexResponse(BaseModel):
    year: int
    product_name: str
    hs_code: str
    unit_price_usd_per_tonne: float
    price_z_score: float
    is_anomaly_price: bool

@router.get("/price-index", response_model=List[PriceIndexResponse])
def get_price_index(product: str, db: Session = Depends(get_db)):
    query = """
    SELECT px.year, p.name as product_name, p.hs_code, 
           px.unit_price_usd_per_tonne, px.price_z_score, px.is_anomaly_price
    FROM price_index px
    JOIN products p ON px.product_id = p.id
    WHERE p.hs_code = :hs
    ORDER BY px.year ASC
    """
    results = db.execute(text(query), {"hs": product}).fetchall()
    
    if not results:
        raise HTTPException(status_code=404, detail="No price index data found for the given HS code.")
        
    return [dict(r._mapping) for r in results] if not hasattr(results[0], '_asdict') else [r._asdict() for r in results]
