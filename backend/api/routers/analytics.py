from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from db.database import get_db
from api.schemas.models import TopDestinationResponse, YoYGrowthResponse, MarketShareResponse
from pydantic import BaseModel
from sqlalchemy import text

# Import logic from our ETL/Analytics layer
from analytics.aggregations import get_top_destinations, calculate_yoy_growth
from analytics.market_share import get_market_share as calc_market_share

router = APIRouter(prefix="/api/analytics")

@router.get("/top-destinations", response_model=List[TopDestinationResponse])
def top_destinations(year: int = 2023, limit: int = Query(10, le=50), db: Session = Depends(get_db)):
    """Top N export destinations for a given year."""
    results = get_top_destinations(db, year=year, limit=limit)
    return results

@router.get("/yoy-growth", response_model=List[YoYGrowthResponse])
def yoy_growth(product_hs_code: Optional[str] = None, db: Session = Depends(get_db)):
    """Year-over-Year growth of total export value."""
    results = calculate_yoy_growth(db, product_hs_code=product_hs_code)
    return results

@router.get("/market-share", response_model=List[MarketShareResponse])
def market_share(start_year: int = 2000, end_year: int = 2023, db: Session = Depends(get_db)):
    """Turkey vs Rest of World market share."""
    results = calc_market_share(db, start_year=start_year, end_year=end_year)
    return results
<<<<<<< Updated upstream
=======

class ReconciliationResponse(BaseModel):
    year: int
    country_name: str
    country_iso3: str
    hs_code: str
    export_value_usd: float
    mirror_value_usd: float
    bilateral_gap_pct: float
    high_gap: bool

@router.get("/reconciliation", response_model=List[ReconciliationResponse])
def reconciliation(year: Optional[int] = None, country_iso3: Optional[str] = None, db: Session = Depends(get_db)):
    query = "SELECT e.year, c.name as country_name, c.iso3 as country_iso3, p.hs_code, e.trade_value_usd as export_value_usd, e.mirror_value_usd, e.bilateral_gap_pct FROM exports e JOIN countries c ON e.country_id = c.id JOIN products p ON e.product_id = p.id WHERE e.mirror_value_usd IS NOT NULL"
    params = {}
    if year:
        query += " AND e.year = :y"
        params['y'] = year
    if country_iso3:
        query += " AND c.iso3 = :iso"
        params['iso'] = country_iso3
        
    results = db.execute(text(query), params).fetchall()
    out = []
    for r in results:
        d = dict(r._mapping) if hasattr(r, '_mapping') else r._asdict()
        d['high_gap'] = abs(d['bilateral_gap_pct']) > 20.0 if d['bilateral_gap_pct'] else False
        out.append(d)
    return out

class AnomalyResponse(BaseModel):
    year: int
    country_name: str
    country_iso3: str
    product_name: str
    hs_code: str
    volume_tons: float
    value_usd: float
    anomaly_context: Optional[str]

@router.get("/anomalies", response_model=List[AnomalyResponse])
def anomalies(year: Optional[int] = None, country_iso3: Optional[str] = None, db: Session = Depends(get_db)):
    query = "SELECT e.year, c.name as country_name, c.iso3 as country_iso3, p.name as product_name, p.hs_code, e.trade_volume_tons as volume_tons, e.trade_value_usd as value_usd, e.anomaly_context FROM exports e JOIN countries c ON e.country_id = c.id JOIN products p ON e.product_id = p.id WHERE e.anomaly_flag = TRUE"
    params = {}
    if year:
        query += " AND e.year = :y"
        params['y'] = year
    if country_iso3:
        query += " AND c.iso3 = :iso"
        params['iso'] = country_iso3
        
    results = db.execute(text(query), params).fetchall()
    return [dict(r._mapping) if hasattr(r, '_mapping') else r._asdict() for r in results]

class ExchangeRateResponse(BaseModel):
    year: int
    usd_per_eur: float
    try_per_eur: float
    usd_per_try: float

@router.get("/exchange-rates", response_model=List[ExchangeRateResponse])
def exchange_rates(start_year: Optional[int] = None, end_year: Optional[int] = None, db: Session = Depends(get_db)):
    query = "SELECT year, usd_per_eur, try_per_eur, usd_per_try FROM exchange_rates WHERE 1=1"
    params = {}
    if start_year:
        query += " AND year >= :sy"
        params['sy'] = start_year
    if end_year:
        query += " AND year <= :ey"
        params['ey'] = end_year
    query += " ORDER BY year ASC"
    
    results = db.execute(text(query), params).fetchall()
    return [dict(r._mapping) if hasattr(r, '_mapping') else r._asdict() for r in results]
>>>>>>> Stashed changes
