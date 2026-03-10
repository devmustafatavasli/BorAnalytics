import os
import sys
import logging
import requests
import io
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db.database import engine, SessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ECB Statistical Data Warehouse API Base
# EXR: Exchange Rates
# A: Annual
# USD/TRY: code currencies against EUR base
ECB_URL = "https://sdw-wsrest.ecb.europa.eu/service/data/EXR/A.{currency}.EUR.SP00.A"

def fetch_exchange_rates(start_year: int = 2000) -> pd.DataFrame:
    """
    Fetches Annual USD/EUR and TRY/EUR series from ECB SDMX API.
    Calculates unified USD/TRY cross-rate mapping.
    """
    # Fetch USD
    resp_usd = requests.get(ECB_URL.format(currency="USD"), params={"startPeriod": str(start_year), "format": "csvdata"})
    if resp_usd.status_code != 200:
        logger.error(f"Failed to fetch ECB USD rates: {resp_usd.text}")
        return pd.DataFrame()
        
    df_usd = pd.read_csv(io.StringIO(resp_usd.text))
    # 'TIME_PERIOD' -> year, 'OBS_VALUE' -> usd_per_eur (which means 1 EUR = X USD)
    df_usd = df_usd[['TIME_PERIOD', 'OBS_VALUE']].rename(columns={'TIME_PERIOD': 'year', 'OBS_VALUE': 'usd_per_eur'})
    df_usd['year'] = df_usd['year'].astype(int)
    
    # Fetch TRY
    resp_try = requests.get(ECB_URL.format(currency="TRY"), params={"startPeriod": str(start_year), "format": "csvdata"})
    if resp_try.status_code != 200:
        logger.error(f"Failed to fetch ECB TRY rates: {resp_try.text}")
        return pd.DataFrame()
        
    df_try = pd.read_csv(io.StringIO(resp_try.text))
    df_try = df_try[['TIME_PERIOD', 'OBS_VALUE']].rename(columns={'TIME_PERIOD': 'year', 'OBS_VALUE': 'try_per_eur'})
    df_try['year'] = df_try['year'].astype(int)
    
    # Merge and calculate cross-rate
    df = pd.merge(df_usd, df_try, on='year', how='inner')
    
    # ECB publishes base EUR. usd_per_eur = X USD / 1 EUR. try_per_eur = Y TRY / 1 EUR.
    # We want USD/TRY, which conceptually is "1 USD = ? TRY".
    # (Y TRY / 1 EUR) * (1 EUR / X USD) = (Y / X) TRY / USD
    # But wait, common nomenclature in Turkey "USD/TRY" means exactly "how many TRY per 1 USD".
    # However the docs specify "usd_per_try" column. 
    # "usd_per_try" mathematically means "how many USD per 1 TRY" (e.g. 0.04).
    # "usd_per_try" = usd_per_eur / try_per_eur -> (X/Y)
    # E.g. 2023: 1 EUR = 1.08 USD, 1 EUR = 25.8 TRY. 
    # USD per TRY = 1.08 / 25.8 = ~0.041.
    df['usd_per_try'] = df['usd_per_eur'] / df['try_per_eur']
    
    return df

def load_to_db(df: pd.DataFrame, db_engine):
    """Upserts ECB exchange rates mapped annually."""
    if df.empty: return
    
    stmt = """
        INSERT INTO exchange_rates (year, usd_per_eur, try_per_eur, usd_per_try)
        VALUES (:y, :usd_e, :try_e, :usd_t)
        ON CONFLICT (year) DO UPDATE 
        SET usd_per_eur = EXCLUDED.usd_per_eur,
            try_per_eur = EXCLUDED.try_per_eur,
            usd_per_try = EXCLUDED.usd_per_try
    """
    
    with db_engine.begin() as conn:
        for _, row in df.iterrows():
            conn.execute(stmt, {
                "y": int(row['year']),
                "usd_e": float(row['usd_per_eur']),
                "try_e": float(row['try_per_eur']),
                "usd_t": float(row['usd_per_try'])
            })
            
    logger.info(f"Successfully tracked {len(df)} annual exchange rates into PGSQL.")

if __name__ == "__main__":
    df = fetch_exchange_rates()
    load_to_db(df, engine)
