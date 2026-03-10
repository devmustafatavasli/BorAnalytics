import os
import json
import logging
import pandas as pd
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db.database import SessionLocal
from db.models import Country

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RAW_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/raw/worldbank"))

def load_world_bank_json() -> List[Dict]:
    """Loads World Bank JSON dump from disk."""
    records = []
    if not os.path.exists(RAW_DATA_DIR):
        return records
        
    for filename in os.listdir(RAW_DATA_DIR):
        if filename.endswith(".json"):
            filepath = os.path.join(RAW_DATA_DIR, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    records.extend(data)
                except json.JSONDecodeError:
                    logger.error(f"Error parsing {filename}")
    return records

def transform_and_load(raw_records: List[Dict]):
    """
    Transforms World Bank data (GDP, etc.) and updates the Database.
    Since we didn't specify a generic 'Economy' table, we will add GDP 
    as an optional column on `exports` or handle it via a new table.
    For this example, we will just ensure Countries exist and are updated.
    Ideally, we'd have a `macro_indicators` table. We'll simply ensure
    the country dimension is rich.
    """
    if not raw_records:
        logger.info("No World Bank records to process.")
        return
        
    df = pd.DataFrame(raw_records)
    
    # World Bank structure: 'countryiso3code', 'date', 'value', 'indicator'
    if 'countryiso3code' not in df.columns or 'date' not in df.columns:
        return
        
    # Drop rows without iso3 or value
    df.dropna(subset=['countryiso3code', 'value'], inplace=True)
    df = df[df['countryiso3code'] != ""]
    
    # Seed countries based on World Bank data too
    db: Session = SessionLocal()
    try:
        unique_countries = df[['countryiso3code', 'country']].drop_duplicates()
        existing_iso = {c.iso3 for c in db.query(Country.iso3).all()}
        
        for _, row in unique_countries.iterrows():
            iso = row['countryiso3code']
            # World bank 'country' is a dict: {'id': '..', 'value': 'Name'}
            name = row['country'].get('value', f"Country {iso}") if isinstance(row['country'], dict) else row['country']
            
            if iso not in existing_iso:
                new_country = Country(iso3=iso, name=name, region="World Bank Data")
                db.add(new_country)
                existing_iso.add(iso)
                
        db.commit()
        logger.info("World Bank country dimension sync complete.")
        
    except Exception as e:
        db.rollback()
        logger.error(f"DB Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    records = load_world_bank_json()
    transform_and_load(records)
