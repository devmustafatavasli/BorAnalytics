from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional

from db.database import get_db
from db.models import Export, Country, Product, Production
from api.schemas.models import ExportResponse, CountryResponse, ProductionResponse

router = APIRouter(prefix="/api")

@router.get("/countries", response_model=List[CountryResponse])
def get_countries(db: Session = Depends(get_db)):
    """Returns a full list of country references."""
    return db.query(Country).all()

@router.get("/exports", response_model=List[ExportResponse])
def get_exports(
    year: Optional[int] = None, 
    country_iso3: Optional[str] = None, 
    product_hs_code: Optional[str] = None, 
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db)
):
    """
    Export records with filters.
    If no matches, returns empty list with 200 status.
    """
    query = (
        db.query(
            Export.year,
            Export.value_usd,
            Export.volume_tons,
            Export.anomaly_flag,
            Country.name.label('country_name'),
            Country.iso3.label('country_iso3'),
            Product.name.label('product_name'),
            Product.hs_code.label('hs_code')
        )
        .join(Country, Export.country_id == Country.id)
        .join(Product, Export.product_id == Product.id)
    )
    
    if year:
        query = query.filter(Export.year == year)
    if country_iso3:
        query = query.filter(Country.iso3 == country_iso3)
    if product_hs_code:
        query = query.filter(Product.hs_code == product_hs_code)
        
    results = query.order_by(desc(Export.year), desc(Export.value_usd)).limit(limit).all()
    
    return [
        ExportResponse(
            year=r.year,
            country_name=r.country_name,
            country_iso3=r.country_iso3,
            product_name=r.product_name,
            hs_code=r.hs_code,
            value_usd=r.value_usd,
            volume_tons=r.volume_tons,
            anomaly_flag=r.anomaly_flag
        ) for r in results 
    ]

@router.get("/production", response_model=List[ProductionResponse])
def get_production(
    year: Optional[int] = None,
    facility: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Returns production volumes by facility and year."""
    query = (
        db.query(
            Production.year,
            Production.facility,
            Production.volume_tons,
            Product.name.label('product_name'),
            Product.hs_code.label('hs_code')
        )
        .join(Product, Production.product_id == Product.id)
    )
    
    if year:
        query = query.filter(Production.year == year)
    if facility:
        query = query.filter(Production.facility == facility)
        
    results = query.order_by(desc(Production.year)).all()
    
    return [
        ProductionResponse(
            year=r.year,
            facility=r.facility,
            product_name=r.product_name,
            hs_code=r.hs_code,
            volume_tons=r.volume_tons
        ) for r in results
    ]
