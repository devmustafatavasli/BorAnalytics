import os
import sys
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Dict

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db.database import SessionLocal
from db.models import Export, Country, Product

def get_top_destinations(db: Session, year: int = 2023, limit: int = 10) -> List[Dict]:
    """Returns top N export destinations by value for a given year."""
    results = (
        db.query(
            Country.name,
            func.sum(Export.value_usd).label('total_value')
        )
        .join(Export, Export.country_id == Country.id)
        .filter(Export.year == year)
        .group_by(Country.id)
        .order_by(desc('total_value'))
        .limit(limit)
        .all()
    )
    return [{"country_name": r[0], "value_usd": r[1]} for r in results]

def calculate_yoy_growth(db: Session, product_hs_code: str = None) -> List[Dict]:
    """Calculates Year-over-Year growth of total export value."""
    query = db.query(
        Export.year,
        func.sum(Export.value_usd).label('total_value')
    )
    
    if product_hs_code:
        query = query.join(Product, Export.product_id == Product.id).filter(Product.hs_code == product_hs_code)
        
    results = query.group_by(Export.year).order_by(Export.year).all()
    
    growth_data = []
    for i in range(len(results)):
        year, current_val = results[i]
        if i == 0:
            growth_pct = 0.0
        else:
            prev_val = results[i-1][1]
            growth_pct = ((current_val - prev_val) / prev_val * 100.0) if prev_val > 0 else 0.0
            
        growth_data.append({
            "year": year,
            "value_usd": current_val,
            "yoy_growth_pct": round(growth_pct, 2)
        })
        
    return growth_data
