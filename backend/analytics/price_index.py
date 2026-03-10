import os
import sys
import logging
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db.database import engine, SessionLocal
from db.models import Export, Product

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def compute_price_index(db_engine):
    """
    Computes median unit price per tonne and highly standard rolling 10-year Z-scores.
    Loads to price_index Postgres table.
    """
    query = """
    SELECT year, product_id, value_usd, volume_tons 
    FROM exports 
    WHERE volume_tons > 0
    """
    df = pd.read_sql(query, db_engine)
    if df.empty:
        logger.warning("No export data available to compute unit prices.")
        return

    # Compute unit_price per transaction
    df['unit_price_usd_per_tonne'] = df['value_usd'] / df['volume_tons']

    # Median unit price across destination countries per product per year
    yearly_df = df.groupby(['year', 'product_id'])['unit_price_usd_per_tonne'].median().reset_index()

    # Sort to ensure rolling computations work chronologically
    yearly_df = yearly_df.sort_values(by=['product_id', 'year'])

    # Compute rolling metrics per product
    # The requirement specifically calls for exactly 10-yr rolling metrics
    yearly_df['rolling_mean'] = yearly_df.groupby('product_id')['unit_price_usd_per_tonne'].transform(lambda x: x.rolling(10, min_periods=1).mean())
    yearly_df['rolling_std'] = yearly_df.groupby('product_id')['unit_price_usd_per_tonne'].transform(lambda x: x.rolling(10, min_periods=1).std())

    # Replace nan std with 1.0 to avoid zero division where only 1 year exists
    yearly_df['rolling_std'] = yearly_df['rolling_std'].fillna(1.0).replace(0, 1.0)
    
    yearly_df['price_z_score'] = (yearly_df['unit_price_usd_per_tonne'] - yearly_df['rolling_mean']) / yearly_df['rolling_std']
    # If std is 1.0 because of padding and numerator is 0, z is 0 which is safe.

    yearly_df['is_anomaly_price'] = yearly_df['price_z_score'].abs() > 2.0

    # Write into the DB
    stmt = """
        INSERT INTO price_index (year, product_id, unit_price_usd_per_tonne, price_z_score, is_anomaly_price)
        VALUES (:y, :p_id, :px, :z, :is_anom)
        ON CONFLICT (year, product_id) DO UPDATE 
        SET unit_price_usd_per_tonne = EXCLUDED.unit_price_usd_per_tonne,
            price_z_score = EXCLUDED.price_z_score,
            is_anomaly_price = EXCLUDED.is_anomaly_price
    """
    
    with db_engine.begin() as conn:
        for _, row in yearly_df.iterrows():
            conn.execute(stmt, {
                "y": int(row['year']),
                "p_id": int(row['product_id']),
                "px": float(row['unit_price_usd_per_tonne']),
                "z": float(row['price_z_score']),
                "is_anom": bool(row['is_anomaly_price'])
            })
    logger.info(f"Successfully computed and loaded {len(yearly_df)} price index records.")

def get_price_series(db_engine, hs_code: str) -> pd.DataFrame:
    """
    Fetches the full time series out of price_index. 
    """
    query = """
    SELECT px.year, px.unit_price_usd_per_tonne, px.price_z_score, px.is_anomaly_price,
           px.unit_price_try_per_tonne, px.unit_price_usd_real_2010, px.try_z_score, px.is_anomaly_try
    FROM price_index px
    JOIN products p ON px.product_id = p.id
    WHERE p.hs_code = %s
    ORDER BY px.year ASC
    """
    return pd.read_sql(query, db_engine, params=(hs_code,))

def compute_currency_adjusted_price(db_engine):
    """
    Computes TRY unit prices, 2010 constant USD prices, and TRY Z-scores
    using the ECB exchange_rates table mapping. Updates price_index directly.
    """
    fetch_query = """
    SELECT px.id as px_id, px.year, px.product_id, px.unit_price_usd_per_tonne, er.usd_per_try
    FROM price_index px
    JOIN exchange_rates er ON px.year = er.year
    """
    df = pd.read_sql(fetch_query, db_engine)
    if df.empty:
        logger.warning("No overlapping pricing / exchange rate data. Skipping currency adjustment.")
        return
        
    df['unit_price_try_per_tonne'] = df['unit_price_usd_per_tonne'] * df['usd_per_try']
    
    # Identify 2010 rate for constant indexing
    try:
        usd_try_2010 = df[df['year'] == 2010]['usd_per_try'].values[0]
    except IndexError:
        logger.warning("Base year 2010 missing in exchange_rates map. Aborting real USD calc.")
        return
        
    df['unit_price_usd_real_2010'] = df['unit_price_usd_per_tonne'] * (df['usd_per_try'] / usd_try_2010)

    # Compute rolling 10 year z-scores on the TRY series strictly
    df = df.sort_values(by=['product_id', 'year'])
    df['try_rolling_mean'] = df.groupby('product_id')['unit_price_try_per_tonne'].transform(lambda x: x.rolling(10, min_periods=1).mean())
    df['try_rolling_std'] = df.groupby('product_id')['unit_price_try_per_tonne'].transform(lambda x: x.rolling(10, min_periods=1).std().fillna(1.0).replace(0, 1.0))
    df['try_z_score'] = (df['unit_price_try_per_tonne'] - df['try_rolling_mean']) / df['try_rolling_std']
    df['is_anomaly_try'] = df['try_z_score'].abs() > 2.0
    
    update_stmt = text("""
        UPDATE price_index
        SET unit_price_try_per_tonne = :try_px,
            unit_price_usd_real_2010 = :usd_real,
            try_z_score = :try_z,
            is_anomaly_try = :is_anom
        WHERE id = :px_id
    """)

    with db_engine.begin() as conn:
        for _, row in df.iterrows():
            conn.execute(update_stmt, {
                "try_px": float(row['unit_price_try_per_tonne']),
                "usd_real": float(row['unit_price_usd_real_2010']),
                "try_z": float(row['try_z_score']),
                "is_anom": bool(row['is_anomaly_try']),
                "px_id": int(row['px_id'])
            })
            
    logger.info(f"Currency adjusted indices mapped securely for {len(df)} records.")

if __name__ == "__main__":
    compute_price_index(engine)
    compute_currency_adjusted_price(engine)
