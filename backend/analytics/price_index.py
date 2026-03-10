import os
import sys
import logging
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
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
    SELECT year, product_id, trade_value_usd, net_weight_kg 
    FROM exports 
    WHERE net_weight_kg > 0
    """
    df = pd.read_sql(query, db_engine)
    if df.empty:
        logger.warning("No export data available to compute unit prices.")
        return

    # Compute unit_price per transaction
    df['unit_price_usd_per_tonne'] = df['trade_value_usd'] / (df['net_weight_kg'] / 1000.0)

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
    SELECT px.year, px.unit_price_usd_per_tonne, px.price_z_score, px.is_anomaly_price
    FROM price_index px
    JOIN products p ON px.product_id = p.id
    WHERE p.hs_code = %s
    ORDER BY px.year ASC
    """
    return pd.read_sql(query, db_engine, params=(hs_code,))

if __name__ == "__main__":
    compute_price_index(engine)
