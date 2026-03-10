import os
import logging
import pandas as pd
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

# Adjust path to import models and connection correctly
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db.database import SessionLocal
from db.models import Production, Country, Product

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_eti_maden_reports() -> List[Dict]:
    """
    Simulates parsing Eti Maden PDF reports using pdfplumber.
    In a real scenario, this would extract text/tables from actual PDFs.
    Here we generate mock data based on the project requirements.
    """
    logger.info("Parsing Eti Maden Annual Reports...")
    mock_data = []
    facilities = ["Bandırma", "Kırka", "Emet", "Bigadiç"]
    hs_codes = ["2528", "2840", "2841"] # Borates, Perborates, Natural Borates
    
    # Generate some realistic-looking volume data
    for year in range(2000, 2024):
        for facility in facilities:
            for hs in hs_codes:
                # Add some variance
                base_vol = 50000 + (year - 2000) * 2000 
                if facility == "Kırka":
                    base_vol *= 1.5
                
                mock_data.append({
                    "year": year,
                    "facility": facility,
                    "hs_code": hs,
                    "volume_tons": round(base_vol)
                })
    return mock_data

def load_production_to_db(records: List[Dict]):
    """Loads production data into the database."""
    db: Session = SessionLocal()
    try:
        # Get products
        products = {p.hs_code: p.id for p in db.query(Product).all()}
        
        # We need to make sure products exist. If they don't, we seed them.
        for hs in ["2528", "2840", "2841"]:
            if hs not in products:
                new_prod = Product(hs_code=hs, name=f"Boron {hs}", category="Borates")
                db.add(new_prod)
                db.commit()
                db.refresh(new_prod)
                products[hs] = new_prod.id
        
        records_to_insert = []
        for r in records:
            p_id = products.get(r['hs_code'])
            if p_id:
                records_to_insert.append({
                    "year": r['year'],
                    "facility": r['facility'],
                    "product_id": p_id,
                    "volume_tons": r['volume_tons']
                })
                
        if records_to_insert:
            stmt = insert(Production).values(records_to_insert)
            stmt = stmt.on_conflict_do_update(
                index_elements=['year', 'facility', 'product_id'],
                set_={'volume_tons': stmt.excluded.volume_tons}
            )
            db.execute(stmt)
            db.commit()
            logger.info(f"Upserted {len(records_to_insert)} production records.")
            
    except Exception as e:
        db.rollback()
        logger.error(f"Error loading production data: {e}")
    finally:
        db.close()

def main():
    production_data = parse_eti_maden_reports()
    load_production_to_db(production_data)

if __name__ == "__main__":
    main()
