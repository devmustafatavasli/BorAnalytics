import os
import sys
import logging
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import text

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db.database import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def compute_reconciliation(db_engine):
    """
    Runs an update linking exports table with mirror_imports table
    to accurately tag bilateral API gap metrics globally.
    """
    fetch_query = """
    SELECT e.id as export_id, e.trade_value_usd as export_val, m.import_value_usd as mirror_val
    FROM exports e
    JOIN mirror_imports m ON e.country_id = m.reporter_id 
        AND e.product_id = m.product_id 
        AND e.year = m.year
    WHERE m.import_value_usd IS NOT NULL
    """
    df = pd.read_sql(fetch_query, db_engine)
    if df.empty:
        logger.warning("No overlapping mirror data found. Has mirror_imports ETL run?")
        return
        
    df['bilateral_gap_pct'] = ((df['export_val'] - df['mirror_val']) / df['export_val']) * 100.0
    
    # Handle possible division by zero / infinities safely
    df['bilateral_gap_pct'] = df['bilateral_gap_pct'].replace([float('inf'), -float('inf')], 0).fillna(0)

    # Bulk update original records in exports using PostgreSQL safe binds
    update_stmt = text("""
        UPDATE exports 
        SET mirror_value_usd = :m_val, bilateral_gap_pct = :gap 
        WHERE id = :e_id
    """)
    
    with db_engine.begin() as conn:
        for _, row in df.iterrows():
            conn.execute(update_stmt, {
                "m_val": float(row['mirror_val']),
                "gap": float(row['bilateral_gap_pct']),
                "e_id": int(row['export_id'])
            })
    logger.info(f"Reconciled and updated {len(df)} export records with mirror import signals.")


def get_reconciliation_summary(db_engine) -> pd.DataFrame:
    """
    Returns grouped yearly summary measuring mirror divergence patterns.
    """
    query = """
    SELECT year, 
           AVG(bilateral_gap_pct) as mean_gap, 
           MAX(bilateral_gap_pct) as max_gap, 
           COUNT(*) FILTER (WHERE ABS(bilateral_gap_pct) > 20) as high_gap_count
    FROM exports
    WHERE mirror_value_usd IS NOT NULL
    GROUP BY year
    ORDER BY year ASC
    """
    return pd.read_sql(query, db_engine)

if __name__ == "__main__":
    compute_reconciliation(engine)
