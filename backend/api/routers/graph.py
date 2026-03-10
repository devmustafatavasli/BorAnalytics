from fastapi import APIRouter, HTTPException, Query
from typing import List
from pydantic import BaseModel

from graph.trade_network import (
    get_driver, 
    run_centrality_query, 
    run_event_impact_query, 
    run_exposure_query
)

router = APIRouter()

class CentralityResponse(BaseModel):
    iso3: str
    name: str
    total_received: float
    years_active: int

class EventImpactResponse(BaseModel):
    iso3: str
    name: str
    before_value: float
    after_value: float
    pct_change: float

class ExposureResponse(BaseModel):
    total_from_turkey: float
    years_trading: int
    avg_annual_value: float
    products_imported: List[str]

@router.get("/graph/centrality", response_model=List[CentralityResponse])
def get_graph_centrality():
    try:
        driver = get_driver()
    except ValueError:
        raise HTTPException(status_code=503, detail="Graph database not configured. Set NEO4J_URI env var.")
        
    try:
        return run_centrality_query(driver)
    finally:
        driver.close()

@router.get("/graph/event-impact", response_model=List[EventImpactResponse])
def get_graph_event_impact(event_id: int = Query(...)):
    try:
        driver = get_driver()
    except ValueError:
        raise HTTPException(status_code=503, detail="Graph database not configured. Set NEO4J_URI env var.")
        
    try:
        return run_event_impact_query(driver, event_id)
    finally:
        driver.close()

@router.get("/graph/exposure", response_model=ExposureResponse)
def get_graph_exposure(country: str = Query(..., description="ISO3 country code")):
    try:
        driver = get_driver()
    except ValueError:
        raise HTTPException(status_code=503, detail="Graph database not configured. Set NEO4J_URI env var.")
        
    try:
        return run_exposure_query(driver, country)
    finally:
        driver.close()
