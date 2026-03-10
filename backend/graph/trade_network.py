import os
import sys
import logging
import pandas as pd
from neo4j import GraphDatabase
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _get_engine():
    """Lazy import to avoid crashing at module load time if DATABASE_URL is not set."""
    from db.database import engine
    return engine

def get_driver():
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USERNAME", "neo4j")
    pwd = os.getenv("NEO4J_PASSWORD")
    
    if not uri or not pwd:
        raise ValueError("NEO4J_URI or NEO4J_PASSWORD environment variables are missing.")
        
    return GraphDatabase.driver(uri, auth=(user, pwd))

def build_graph(db_engine, driver):
    """
    Reads PostgreSQL relational data and builds the Neo4j Knowledge Graph.
    Extracts Countries, Products, Years, Events, and generates relationship edges dynamically.
    """
    logger.info("Extracting Relational Data for Neo4j Build...")
    
    # 1. Fetch Countries
    df_countries = pd.read_sql("SELECT iso3, name, region FROM countries", db_engine)
    
    # 2. Fetch Products
    df_products = pd.read_sql("SELECT hs_code, description FROM products", db_engine)
    
    # 3. Fetch Trade Ties (Edges mapping TUR -> Country)
    trade_query = """
    SELECT 
        e.year,
        c.iso3 as target_iso3,
        p.hs_code as product_hs,
        e.value_usd,
        e.net_weight_kg,
        (e.value_usd / NULLIF(e.net_weight_kg, 0)) * 1000 as unit_price_usd_per_tonne
    FROM exports e
    JOIN countries c ON e.country_id = c.id
    JOIN products p ON e.product_id = p.id
    """
    df_trades = pd.read_sql(trade_query, db_engine)    
    # 4. Fetch Events
    df_events = pd.read_sql("""
        SELECT id as event_id, event_date, event_year, event_type, title, 
               affected_product, affected_country, magnitude 
        FROM events
    """, db_engine)

    logger.info("Purging existing Neo4j graph properties...")
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
        
        # Build Country Nodes
        logger.info("Building Country nodes...")
        for _, row in df_countries.iterrows():
            session.run("""
                MERGE (c:Country {iso3: $iso3})
                ON CREATE SET c.name = $name, c.region = $region
            """, iso3=row['iso3'], name=row['name'], region=row['region'])
            
        # Ensure TUR exists structurally 
        session.run("MERGE (c:Country {iso3: 'TUR'}) ON CREATE SET c.name = 'Turkey', c.region = 'Middle East'")

        # Build Product Nodes
        logger.info("Building Product nodes...")
        for _, row in df_products.iterrows():
            session.run("""
                MERGE (p:Product {hs_code: $hs})
                ON CREATE SET p.description = $desc
            """, hs=row['hs_code'], desc=row['description'])

        # Build Year Nodes and Trade Edges
        logger.info("Building Trade Network EXPORT_TO edges and Year bindings...")
        for _, row in df_trades.iterrows():
            year_val = int(row['year'])
            session.run("""
                MERGE (y:Year {year: $year})
                
                WITH y
                MATCH (tur:Country {iso3: 'TUR'})
                MATCH (target:Country {iso3: $t_iso})
                
                MERGE (tur)-[e:EXPORTS_TO {year: $year, product_hs: $hs}]->(target)
                ON CREATE SET 
                    e.value_usd = $val, 
                    e.net_weight_kg = $kg, 
                    e.unit_price_usd_per_tonne = $u_price
                    
                MERGE (tur)-[:HAS_YEAR]->(y)
                MERGE (target)-[:HAS_YEAR]->(y)
            """, 
            year=year_val, t_iso=row['target_iso3'], hs=row['product_hs'],
            val=float(row['value_usd']), kg=float(row['net_weight_kg']), 
            u_price=float(row['unit_price_usd_per_tonne']) if pd.notnull(row['unit_price_usd_per_tonne']) else 0.0)

        # Build Event Nodes and PRECEDES / AFFECTS Edges
        logger.info("Mapping Scraped Eti Maden Events to Graph Elements...")
        for _, row in df_events.iterrows():
            ev_id = int(row['event_id'])
            e_year = int(row['event_year'])
            e_type = str(row['event_type'])
            title = str(row['title'])
            mag = row['magnitude'] if pd.notnull(row['magnitude']) else 'moderate'
            
            # Create the Event Node itself
            session.run("""
                MERGE (ev:Event {event_id: $eid})
                ON CREATE SET 
                    ev.event_type = $etype, 
                    ev.title = $t, 
                    ev.magnitude = $mag
                    
                WITH ev
                MERGE (y:Year {year: $eyear})
                MERGE (ev)-[:PRECEDES {months_before: 6}]->(y)
            """, eid=ev_id, etype=e_type, t=title, mag=mag, eyear=e_year)
            
            # Map logical product effects 
            if pd.notnull(row['affected_product']):
                session.run("""
                    MATCH (ev:Event {event_id: $eid})
                    MATCH (p:Product {hs_code: $hs})
                    MERGE (ev)-[:AFFECTS_PRODUCT {confidence: 'high'}]->(p)
                """, eid=ev_id, hs=str(row['affected_product']))
                
            # Map logical country specific impacts (ie. New Export Agreements)
            if pd.notnull(row['affected_country']):
                session.run("""
                    MATCH (ev:Event {event_id: $eid})
                    MATCH (c:Country {iso3: $iso})
                    MERGE (ev)-[:AFFECTS_COUNTRY {confidence: 'high'}]->(c)
                """, eid=ev_id, iso=str(row['affected_country']))

    logger.info("Neo4j Building Iteration Complete.")

def run_centrality_query(driver) -> list:
    """Returns top countries by total EXPORTS_TO value received from Turkey."""
    query = """
    MATCH (turkey:Country {iso3:'TUR'})-[e:EXPORTS_TO]->(c:Country)
    RETURN c.iso3 as iso3, c.name as name, sum(e.value_usd) as total_received, count(distinct e.year) as years_active 
    ORDER BY total_received DESC LIMIT 15
    """
    with driver.session() as session:
        result = session.run(query)
        return [{"iso3": r["iso3"], "name": r["name"], "total_received": float(r["total_received"]), "years_active": r["years_active"]} for r in result]

def run_event_impact_query(driver, event_id: int) -> list:
    """Returns trade value changes in the year following a specific event."""
    query = """
    MATCH (ev:Event {event_id: $eid})-[:PRECEDES]->(y:Year)
    MATCH (turkey:Country {iso3:'TUR'})-[before:EXPORTS_TO {year: y.year-1}]->(c:Country)
    MATCH (turkey)-[after:EXPORTS_TO {year: y.year}]->(c)
    WITH c.iso3 as iso3, c.name as name, sum(before.value_usd) as total_before, sum(after.value_usd) as total_after
    RETURN iso3, name, total_before as before_value, total_after as after_value,
           ((total_after - total_before) / total_before) * 100 as pct_change
    ORDER BY pct_change DESC
    """
    with driver.session() as session:
        result = session.run(query, eid=event_id)
        return [{
            "iso3": r["iso3"], "name": r["name"], 
            "before_value": float(r["before_value"]), "after_value": float(r["after_value"]), 
            "pct_change": float(r["pct_change"])
        } for r in result]

def run_exposure_query(driver, country_iso3: str) -> dict:
    """Returns how dependent a given importing country is on Turkish boron industrially."""
    query = """
    MATCH (turkey:Country {iso3:'TUR'})-[e:EXPORTS_TO]->(c:Country {iso3: $iso})
    RETURN sum(e.value_usd) as total_from_turkey,
           count(distinct e.year) as years_trading,
           avg(e.value_usd) as avg_annual_value,
           collect(distinct e.product_hs) as products_imported
    """
    with driver.session() as session:
        res = session.run(query, iso=country_iso3).single()
        if not res or res["total_from_turkey"] is None:
            return {"total_from_turkey": 0.0, "years_trading": 0, "avg_annual_value": 0.0, "products_imported": []}
            
        return {
            "total_from_turkey": float(res["total_from_turkey"]),
            "years_trading": int(res["years_trading"]),
            "avg_annual_value": float(res["avg_annual_value"]),
            "products_imported": list(res["products_imported"])
        }

if __name__ == "__main__":
    try:
        db_engine = _get_engine()
        drv = get_driver()
        build_graph(db_engine, drv)
    except Exception as e:
        logger.error(f"Failed to build graph: {e}")
