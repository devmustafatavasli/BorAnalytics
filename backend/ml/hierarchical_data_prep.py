import os
import sys
import logging
import pandas as pd
from typing import Tuple, Dict, List

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db.database import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def prepare_hierarchical_data(db_engine) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, List[str]]]:
    """
    Builds the long-format DataFrame Y_df, the summation matrix S_df, and hierarchy tags.
    """
    query = """
    SELECT e.year, p.hs_code, c.iso3, e.trade_volume_tons as volume_tons
    FROM exports e
    JOIN products p ON e.product_id = p.id
    JOIN countries c ON e.country_id = c.id
    """
    df = pd.read_sql(query, db_engine)
    
    if df.empty:
        logger.warning("Exports table is empty. Returning empty constructs.")
        return pd.DataFrame(), pd.DataFrame(), {}
        
    df = df.rename(columns={'year': 'ds'})
    
    # 1. Leaf level (Country-Product pairs)
    df_country = df.groupby(['hs_code', 'iso3', 'ds'])['volume_tons'].sum().reset_index()
    df_country['unique_id'] = df_country['hs_code'] + ':' + df_country['iso3']
    df_country = df_country[['unique_id', 'ds', 'volume_tons']].rename(columns={'volume_tons': 'y'})
    
    # 2. Product level 
    df_product = df.groupby(['hs_code', 'ds'])['volume_tons'].sum().reset_index()
    df_product['unique_id'] = 'PRODUCT:' + df_product['hs_code']
    df_product = df_product[['unique_id', 'ds', 'volume_tons']].rename(columns={'volume_tons': 'y'})
    
    # 3. Global level
    df_global = df.groupby(['ds'])['volume_tons'].sum().reset_index()
    df_global['unique_id'] = 'GLOBAL:TOTAL'
    df_global = df_global[['unique_id', 'ds', 'volume_tons']].rename(columns={'volume_tons': 'y'})
    
    # Combine into single long-format Y_df
    Y_df = pd.concat([df_global, df_product, df_country], ignore_index=True)
    Y_df['ds'] = pd.to_datetime(Y_df['ds'], format="%Y") # neuralforecast expects dates

    # Building Tags
    global_nodes = ['GLOBAL:TOTAL']
    product_nodes = sorted(df_product['unique_id'].unique().tolist())
    country_nodes = sorted(df_country['unique_id'].unique().tolist())
    
    tags = {
        'Global': global_nodes,
        'Product': product_nodes,
        'Country': country_nodes
    }
    
    # Building S_df (Summation Matrix)
    # Rows: Leaf nodes (country_nodes), Columns: All nodes in hierarchy
    all_nodes = global_nodes + product_nodes + country_nodes
    
    # Initialize zero matrix
    S_data = {node: [0] * len(country_nodes) for node in all_nodes}
    S_df = pd.DataFrame(S_data, index=country_nodes)
    
    for country_node in country_nodes:
        # Self connection
        S_df.at[country_node, country_node] = 1
        # Parent product connection
        hs_code = country_node.split(':')[0]
        prod_node = f'PRODUCT:{hs_code}'
        S_df.at[country_node, prod_node] = 1
        # Grandparent global connection
        S_df.at[country_node, 'GLOBAL:TOTAL'] = 1

    return Y_df, S_df, tags

if __name__ == "__main__":
    Y, S, t = prepare_hierarchical_data(engine)
    logger.info(f"Y_df shape: {Y.shape}")
    logger.info(f"S_df shape: {S.shape}")
    logger.info(f"Tags keys: {t.keys()}")
