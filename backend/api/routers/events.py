from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from pydantic import BaseModel
from datetime import date

from db.database import get_db

router = APIRouter()

class EventResponse(BaseModel):
    id: int
    event_date: date
    event_year: int
    event_type: str
    title: str
    affected_product: Optional[str]
    affected_country: Optional[str]
    magnitude: Optional[str]
    source_url: str
    source_name: str

@router.get("/events", response_model=List[EventResponse])
def get_events(
    year: Optional[int] = None,
    event_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = """
        SELECT id, event_date, event_year, event_type, title, 
               affected_product, affected_country, magnitude, source_url, source_name 
        FROM events
        WHERE 1=1
    """
    params = {}
    
    if year:
        query += " AND event_year = :y"
        params['y'] = year
        
    if event_type:
        query += " AND event_type = :t"
        params['t'] = event_type
        
    query += " ORDER BY event_date DESC"
    
    results = db.execute(text(query), params).fetchall()
    return [dict(r._mapping) for r in results]

@router.get("/events/{event_id}", response_model=EventResponse)
def get_event(event_id: int, db: Session = Depends(get_db)):
    query = """
        SELECT id, event_date, event_year, event_type, title, 
               affected_product, affected_country, magnitude, source_url, source_name 
        FROM events
        WHERE id = :eid
    """
    res = db.execute(text(query), {"eid": event_id}).fetchone()
    if not res:
        raise HTTPException(status_code=404, detail="Event not found.")
        
    return dict(res._mapping)
