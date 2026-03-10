import os
import sys
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db.database import SessionLocal
from db.models import Export, Country, Product

def get_market_share(db: Session, start_year: int = 2000, end_year: int = 2023) -> List[Dict]:
    """
    Calculates Turkey's market share vs the Rest of the World for boron exports.
    Assumes `exports` table contains all global exports, and Turkey is 'TUR'.
    """
    # 1. Total global exports per year
    global_query = (
        db.query(Export.year, func.sum(Export.value_usd).label('total'))
        .filter(Export.year >= start_year)
        .filter(Export.year <= end_year)
        .group_by(Export.year)
        .all()
    )
    global_totals = {row.year: row.total for row in global_query}
    
    # 2. Turkey exports per year
    turkey_query = (
        db.query(Export.year, func.sum(Export.value_usd).label('total_turkey'))
        .join(Country, Export.country_id == Country.id)
        .filter(Country.iso3 == 'TUR')
        .filter(Export.year >= start_year)
        .filter(Export.year <= end_year)
        .group_by(Export.year)
        .all()
    )
    turkey_totals = {row.year: row.total_turkey for row in turkey_query}
    
    # 3. Calculate share
    results = []
    for year in sorted(global_totals.keys()):
        total_wld = global_totals[year]
        total_tur = turkey_totals.get(year, 0)
        
        turkey_share = (total_tur / total_wld * 100.0) if total_wld > 0 else 0.0
        row_share = 100.0 - turkey_share
        
        results.append({
            "year": year,
            "turkey_share_pct": round(turkey_share, 2),
            "row_share_pct": round(row_share, 2),
            "turkey_value_usd": total_tur,
            "global_value_usd": total_wld
        })
        
    return results
