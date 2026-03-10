import os
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.database import get_db
from graph.trade_network import get_driver
from nl_query.query_router import answer_question

router = APIRouter()

class NLQueryRequest(BaseModel):
    question: str

class NLQueryResponse(BaseModel):
    answer: str
    path: str
    query: str
    raw_results: list

@router.post("/nl-query", response_model=NLQueryResponse)
def run_natural_language_query(request: NLQueryRequest, db: Session = Depends(get_db)):
    """Accepts plain English/Turkish strings and routes them through the Gemini Data Broker."""
    
    if "GEMINI_API_KEY" not in os.environ:
        raise HTTPException(
            status_code=503, 
            detail="Natural language queries are not available in this environment. GEMINI_API_KEY missing."
        )

    driver = None
    try:
        driver = get_driver()
    except (ValueError, Exception):
        # Neo4j Graph failures will elegantly fall back structurally inside the router logic 
        pass

    try:
        # The engine is bound physically to Postgres mappings by `get_db` generator dependencies ordinarily,
        # but the query router natively requests the raw engine interface to invoke .connect() manually.
        from db.database import engine
        
        result_dict = answer_question(request.question, engine, driver)
        return NLQueryResponse(**result_dict)
    finally:
        if driver:
            driver.close()
