from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from db.database import get_db
from api.schemas.models import TopDestinationResponse, YoYGrowthResponse, MarketShareResponse

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
