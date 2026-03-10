import os
import json
import logging
import pandas as pd
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

# Adjust path to import models and connection correctly
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db.database import SessionLocal
from db.models import Export, Country, Product

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RAW_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/raw/comtrade"))

def load_raw_json_files() -> List[Dict[Any, Any]]:
    """Loads all JSON files from the raw directory."""
    all_records = []
    if not os.path.exists(RAW_DATA_DIR):
        logger.warning(f"Directory {RAW_DATA_DIR} not found.")
        return all_records

    for filename in os.listdir(RAW_DATA_DIR):
        if filename.endswith(".json"):
            filepath = os.path.join(RAW_DATA_DIR, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    # Handle API variations (data array might be under 'data' or top-level list)
                    records = data.get("data", []) if isinstance(data, dict) else data
                    all_records.extend(records)
                except json.JSONDecodeError:
                    logger.error(f"Error parsing JSON in file {filename}")
    
    return all_records

def clean_and_transform(raw_records: List[Dict[Any, Any]]) -> pd.DataFrame:
    """Transforms raw UN Comtrade API response to a normalized pandas DataFrame."""
    if not raw_records:
        return pd.DataFrame()

    df = pd.DataFrame(raw_records)
    
    # UN Comtrade fields: period, reporterISO, partnerISO, cmdCode, primaryValue, netWgt, etc.
    # Note: API format V1 vs V2 will yield different keys. Assuming V1/standardized keys for now.
    
    # We only care about exports (Flow code 2 usually, or 'X')
    if 'flowCode' in df.columns:
        df = df[df['flowCode'].isin(['X', 2, '2'])]
        
    required_cols = {'period', 'partnerISO', 'cmdCode', 'primaryValue', 'netWgt'}
    
    # Rename for our DB schema
    column_mapping = {
        'period': 'year',
        'partnerISO': 'country_iso3',
        'cmdCode': 'hs_code',
        'netWgt': 'volume_tons',
        'primaryValue': 'value_usd'
    }
    
    # Filter columns that exist
    available_cols = [c for c in required_cols if c in df.columns]
    df = df[available_cols]
    df.rename(columns=column_mapping, inplace=True)
    
    # Data Quality Checks & Cleaning
    df['year'] = pd.to_numeric(df['year'].astype(str).str[:4], errors='coerce') # Handle YYYYMM formats just in case
    df['volume_tons'] = pd.to_numeric(df['volume_tons'], errors='coerce') / 1000.0 # Standardize to Metric Tons if it was in KG
    df['value_usd'] = pd.to_numeric(df['value_usd'], errors='coerce')
    
    # Drop where partner is 'WLD' (World aggregation) to avoid double counting
    if 'country_iso3' in df.columns:
        df = df[~df['country_iso3'].isin(['WLD', '000'])]
        
    df.dropna(subset=['year', 'volume_tons', 'value_usd', 'country_iso3', 'hs_code'], inplace=True)
    
    # Remove duplicates
    df.drop_duplicates(subset=['year', 'country_iso3', 'hs_code'], keep='last', inplace=True)
    
    return df

def seed_dimension_tables(db: Session, df: pd.DataFrame):
    """Seed Country and Product tables dynamically based on fetched data if they don't exist."""
    
    # Products
    unique_hs_codes = df['hs_code'].unique()
    for code in unique_hs_codes:
        prod = db.query(Product).filter(Product.hs_code == code).first()
        if not prod:
            # Simplistic seeding, name should ideally be fetched from a reference table
            new_prod = Product(hs_code=code, name=f"Boron Product {code}", category="Borates")
            db.add(new_prod)
            
    # Countries
    unique_iso3 = df['country_iso3'].unique()
    for iso3 in unique_iso3:
        if not iso3 or len(str(iso3)) != 3: continue
        country = db.query(Country).filter(Country.iso3 == str(iso3)).first()
        if not country:
            # Simplistic seeding
            new_country = Country(iso3=iso3, name=f"Country {iso3}", region="Unknown")
            db.add(new_country)
            
    db.commit()

def load_to_db(df: pd.DataFrame):
    """Load the transformed DataFrame into PostgreSQL utilizing SQLAlchemy merge/upsert."""
    db: Session = SessionLocal()
    try:
        if df.empty:
            logger.info("No data to load.")
            return

        seed_dimension_tables(db, df)
        
        # We need mapping of hs_code->product_id and iso3->country_id
        products = {p.hs_code: p.id for p in db.query(Product).all()}
        countries = {c.iso3: c.id for c in db.query(Country).all()}
        
        records_to_insert = []
        for _, row in df.iterrows():
            c_id = countries.get(row['country_iso3'])
            p_id = products.get(row['hs_code'])
            
            if c_id and p_id:
                record = {
                    "year": int(row['year']),
                    "country_id": c_id,
                    "product_id": p_id,
                    "volume_tons": float(row['volume_tons']),
                    "value_usd": float(row['value_usd'])
                }
                records_to_insert.append(record)
                
        if records_to_insert:
            stmt = insert(Export).values(records_to_insert)
            # Idempotent upsert logic: ON CONFLICT DO UPDATE
            stmt = stmt.on_conflict_do_update(
                index_elements=['year', 'country_id', 'product_id'],
                set_={
                    'volume_tons': stmt.excluded.volume_tons,
                    'value_usd': stmt.excluded.value_usd,
                }
            )
            db.execute(stmt)
            db.commit()
            logger.info(f"Successfully upserted {len(records_to_insert)} export records.")

    except Exception as e:
        db.rollback()
        logger.error(f"Database error during load: {e}")
        raise
    finally:
        db.close()

def main():
    logger.info("Starting UN Comtrade Transform & Load pipeline.")
    raw_data = load_raw_json_files()
    logger.info(f"Loaded {len(raw_data)} raw records.")
    
    clean_df = clean_and_transform(raw_data)
    logger.info(f"Transformed to {len(clean_df)} clean records.")
    
    load_to_db(clean_df)
    logger.info("Pipeline completed successfully.")

if __name__ == "__main__":
    main()
