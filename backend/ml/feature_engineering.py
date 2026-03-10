import os
import sys
import logging
import pandas as pd
from sqlalchemy.orm import Session

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db.database import SessionLocal
from db.models import Export, Country, Product

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_features() -> pd.DataFrame:
    """
    Extracts data from the database and creates features for ML models.
    Features include lag features, rolling averages.
    Returns a processed pandas DataFrame.
    """
    db: Session = SessionLocal()
    try:
        # We need a joined flat table for ML
        query = db.query(
            Export.year,
            Export.country_id,
            Export.product_id,
            Export.volume_tons,
            Export.value_usd,
            Country.iso3.label('country_iso3'),
            Product.hs_code.label('hs_code')
        ).join(Country, Export.country_id == Country.id) \
         .join(Product, Export.product_id == Product.id)
         
        df = pd.read_sql(query.statement, db.get_bind())
        if df.empty:
            logger.warning("No data found for feature engineering.")
            return pd.DataFrame()
            
        # Sort values
        df.sort_values(by=['country_id', 'product_id', 'year'], inplace=True)
        
        # We will group by country and product to create time-series features safely
        def generate_lags(group):
            # Lags for value and volume
            for lag in [1, 2, 3]:
                group[f'lag_{lag}_value'] = group['value_usd'].shift(lag)
                group[f'lag_{lag}_volume'] = group['volume_tons'].shift(lag)
            
            # Rolling means
            group['rolling_mean_3_value'] = group['value_usd'].shift(1).rolling(window=3).mean()
            group['rolling_mean_3_volume'] = group['volume_tons'].shift(1).rolling(window=3).mean()
            return group

        df = df.groupby(['country_id', 'product_id']).apply(generate_lags).reset_index(drop=True)
        
        # Mock macro features for demonstration (World Bank GDP, Price Index usually joined here)
        # In a real app we join this from a macro table. Here we use dummy proxies based on year
        df['gdp_importer'] = df['year'].apply(lambda y: 1_000_000_000 + (y-2000)*50_000_000)
        df['boron_price_index'] = df['year'].apply(lambda y: 100 + (y-2000)*2.5)

        # Drop rows with NaN (due to lags) since we need complete rows for XGBoost
        # Alternatively, we can impute, but dropping first 3 years per series is safer for clean TS
        df.dropna(subset=['lag_3_value'], inplace=True)
        
        output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/processed"))
        os.makedirs(output_dir, exist_ok=True)
        
        csv_path = os.path.join(output_dir, 'ml_features.csv')
        df.to_csv(csv_path, index=False)
        logger.info(f"Feature engineering complete. Saved {len(df)} rows to {csv_path}")
        
        return df

    except Exception as e:
        logger.error(f"Error during feature engineering: {e}")
        return pd.DataFrame()
    finally:
        db.close()

def generate_xgboost_features(db_engine=None, inference=False) -> pd.DataFrame:
    """Wrapper mapping structural ML calls dynamically to create_features natively."""
    return create_features()

if __name__ == "__main__":
    create_features()
