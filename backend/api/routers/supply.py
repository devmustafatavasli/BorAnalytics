from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from pydantic import BaseModel

from db.database import get_db

router = APIRouter(prefix="/supply", tags=["supply"])

class SupplyResponse(BaseModel):
    year: int
    country_name: str
    country_iso3: str
    production_tons: float
    reserves_tons: Optional[float]
    source_report: Optional[str]

@router.get("/", response_model=List[SupplyResponse])
def get_supply(year: Optional[int] = None, country_iso3: Optional[str] = None, db: Session = Depends(get_db)):
    query = """
    SELECT s.year, c.name as country_name, c.iso3 as country_iso3, 
           s.production_tons, s.reserves_tons, s.source_report
    FROM supply s
    JOIN countries c ON s.country_id = c.id
    WHERE 1=1
    """
    params = {}
    if year:
        query += " AND s.year = :y"
        params['y'] = year
    if country_iso3:
        query += " AND c.iso3 = :iso"
        params['iso'] = country_iso3
        
    results = db.execute(text(query), params).fetchall()
    return [dict(mapping=r._mapping) for r in results] if not hasattr(results[0], '_asdict') else [r._asdict() for r in results]
