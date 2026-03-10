import os
import sys
import logging
import pandas as pd
from sqlalchemy.orm import Session
from sklearn.ensemble import IsolationForest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db.database import SessionLocal
from db.models import Export, Country, Product

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def detect_anomalies():
    """
    Run Isolation Forest on export volume series to detect anomalies.
    Updates the exports table with anomaly_flag and anomaly_score.
    """
    db: Session = SessionLocal()
    try:
        # Load data into pandas
        query = db.query(
            Export.year, 
            Export.country_id, 
            Export.product_id, 
            Export.volume_tons,
            Export.value_usd
        )
        df = pd.read_sql(query.statement, db.get_bind())
        
        if df.empty:
            logger.warning("No export data to analyze.")
            return

        # We will train an Isolation Forest on volume and value grouped by country/product over time
        df['anomaly_flag'] = False
        df['anomaly_score'] = 0.0
        
        # We group by country-product pair to find anomalies within a specific trade relationship
        groups = df.groupby(['country_id', 'product_id'])
        
        for (c_id, p_id), group in groups:
            if len(group) < 5:
                # Not enough data points to meaningfully detect anomalies
                continue
                
            X = group[['volume_tons', 'value_usd']].values
            
            # Isolation Forest setup
            # contamination=0.05 implies we expect about 5% of data points to be anomalies
            model = IsolationForest(contamination=0.05, random_state=42)
            model.fit(X)
            
            preds = model.predict(X)
            scores = model.decision_function(X) # Lower score = more anomalous
            
            # -1 indicates anomaly, 1 indicates normal
            group.loc[:, 'anomaly_flag'] = preds == -1
            group.loc[:, 'anomaly_score'] = scores
            
            df.update(group)
            
        # Update Database
        # For bulk updates, we iterate over rows where anomaly_flag is True
        anomalies = df[df['anomaly_flag'] == True]
        logger.info(f"Detected {len(anomalies)} anomalies out of {len(df)} records.")
        
        for _, row in anomalies.iterrows():
            db.query(Export).filter(
                Export.year == int(row['year']),
                Export.country_id == int(row['country_id']),
                Export.product_id == int(row['product_id'])
            ).update({
                "anomaly_flag": True,
                "anomaly_score": float(row['anomaly_score'])
            })
            
        db.commit()
            
    except Exception as e:
        db.rollback()
        logger.error(f"Error computing anomaly detection: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    detect_anomalies()
