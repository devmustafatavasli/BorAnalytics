import os
import json
import time
import logging
import google.generativeai as genai
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security & Context Bounds for Gemini
SCHEMA_CONTEXT = """
Relational MySQL/PostgreSQL schema:
- exports(id, year, exporter_id, importer_id, product_id, trade_value_usd, net_weight_kg, anomaly_flag, anomaly_context, bilateral_gap_pct)
- countries(id, iso3, name, region)
- products(id, hs_code, description)
- predictions(id, unique_id, ds, y, yhat, model_name, hierarchy_level)
- events(id, event_date, event_year, event_type, title, affected_product, affected_country, magnitude, source_url, source_name)
- price_index(id, year, product_id, unit_price_usd_per_tonne, unit_price_try_per_tonne, unit_price_usd_real_2010, is_anomaly_price)
- exchange_rates(id, year, usd_per_eur, try_per_eur, usd_per_try)
- model_evaluations(id, model_name, unique_id, mase, dm_pvalue)

Neo4j Graph Database schema:
- Nodes: Country(iso3,name,region), Product(hs_code, description), Year(year), Event(event_id,event_type,magnitude,title)
- Relationships: (Country)-[EXPORTS_TO(year,product_hs,value_usd,net_weight_kg)]->(Country), (Event)-[PRECEDES(months_before)]->(Year), (Event)-[AFFECTS_PRODUCT(confidence)]->(Product)
"""

def classify_and_generate(question: str) -> dict:
    """Classifies the user question into 'sql', 'cypher' or 'direct' and generates query code."""
    try:
        genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        prompt = f'''You are a database query generator for the BorAnalytics Trade platform.
        Given the user question, respond ONLY with valid JSON (no markdown strings like ```json, no preamble):
        {{"path": "sql" or "cypher" or "direct",
          "query": "SELECT-only SQL query or Cypher MATCH query, empty string if direct",
          "explanation": "one sentence explaining the query translation naturally"}}
          
        Rules: 
        1. 'sql' path computes relational data (e.g. historical trade volumes, financial metrics, anomalies). 
        2. 'cypher' path traverses network/relationship data (e.g. Graph mapping dependency, impact cascading, dependencies).
        3. 'direct' is for general Boron questions or platform questions not found in DB.
        4. For SQL, ALWAYS join `countries` for readable text output. ONLY SELECT permitted natively.
        
        Schema Context Boundaries: 
        {SCHEMA_CONTEXT}
        
        Question: {question}'''
        
        response = model.generate_content(prompt)
        text_resp = response.text.replace('```json', '').replace('```', '').strip()
        
        return json.loads(text_resp)
    except Exception as e:
        logger.error(f"NL Classification failed natively: {e}")
        return {"path": "direct", "query": "", "explanation": ""}

def execute_sql_query(query: str, engine) -> list[dict]:
    """Provides a sterile boundary executing generated SQL logically blocking unsafe mutations."""
    WRITE_KEYWORDS = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER', 'TRUNCATE', 'REPLACE']
    
    if any(kw in query.upper() for kw in WRITE_KEYWORDS):
        raise ValueError(f"Write operations are strictly prohibited natively in the query runner: {query}")
        
    with engine.connect() as conn:
        result = conn.execute(text(query))
        rows = [dict(row._mapping) for row in result]
        
    return rows[:50] # Strictly limit token explosion

def execute_cypher_query(query: str, driver) -> list[dict]:
    """Executes a generated Neo4j query structurally."""
    if driver is None: 
        return []
        
    with driver.session() as session:
        return [dict(record) for record in session.run(query)][:50]

def format_answer(question: str, results: list, path: str) -> str:
    """Leverages the LLM to format the rigid matrix results into a comprehensive analytical summary natively."""
    if not results and path != "direct":
        return "No statistical structural data found natively for your question within BorAnalytics bounds."
        
    time.sleep(1) # Strict 15RPM rate compliance limits
    
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        prompt = f'''
        User asked the query: "{question}"
        Query execution pathway: {path}
        Top 10 raw results array: {json.dumps(results[:10], default=str)}
        
        Write a 2-4 sentence plain English or Turkish answer based accurately on the data structure extracted above. 
        Be specific with numbers conditionally. 
        Do NOT mention SQL or Cypher explicitly. Answer natively as a senior global trade analyst.
        '''
        return model.generate_content(prompt).text
    except Exception as e:
        logger.error(f"NL formatting failed natively: {e}")
        return "A computational error occurred generating the written answer limits natively."

def answer_question(question: str, engine, driver=None) -> dict:
    """Entry point integrating full 2-stage LLM generation limits logically bridging databases natively."""
    try:
        classified = classify_and_generate(question)
        results = []
        
        if classified['path'] == 'sql': 
            results = execute_sql_query(classified['query'], engine)
        elif classified['path'] == 'cypher': 
            results = execute_cypher_query(classified['query'], driver)
            
        answer = format_answer(question, results, classified['path'])
        
        return {
            'answer': answer,
            'path': classified['path'],
            'query': classified['query'],
            'raw_results': results
        }
    except Exception as e:
        logger.warning(f"NL query execution error bound properly: {e}")
        return {
            'answer': 'Sorry, a structural matrix error occurred executing this question cleanly. Please try rephrasing or narrowing your question bounds natively.',
            'path': 'error',
            'query': '',
            'raw_results': []
        }
