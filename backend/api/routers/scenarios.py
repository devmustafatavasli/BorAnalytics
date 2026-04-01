from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, root_validator
from datetime import datetime

from db.database import get_db
from ml.scenario_simulation import run_scenario_a, run_scenario_b, run_scenario_c

router = APIRouter(prefix="/scenarios", tags=["scenarios"])

class ScenarioRequest(BaseModel):
    scenario: str
    parameter: float
    country_iso3: Optional[str] = None
    
    @root_validator(pre=True)
    def check_validity(cls, values):
        s = values.get('scenario')
        p = values.get('parameter')
        c = values.get('country_iso3')
        if s not in ['A', 'B', 'C']:
            raise ValueError("Scenario must be A, B, or C")
        if p is None or p < -100 or p > 500:
            raise ValueError("Parameter must be between -100 and 500")
        if s == 'B' and not c:
            raise ValueError("country_iso3 is strictly required for targeted GDP shock Scenario B.")
        return values

class ScenarioResult(BaseModel):
    unique_id: str
    baseline_value: float
    scenario_value: float
    delta_pct: float

class ScenarioResponse(BaseModel):
    scenario: str
    parameter: float
    run_at: datetime
    results: List[ScenarioResult]

@router.post("/run", response_model=ScenarioResponse)
def run_scenario(req: ScenarioRequest, db: Session = Depends(get_db)):
    try:
        if req.scenario == 'A':
            df = run_scenario_a(db.get_bind(), req.parameter)
        elif req.scenario == 'B':
            df = run_scenario_b(db.get_bind(), req.country_iso3, req.parameter)
        elif req.scenario == 'C':
            df = run_scenario_c(db.get_bind(), req.parameter)
        else:
            raise HTTPException(400, "Unmapped scenario.")
            
        if df.empty:
            return ScenarioResponse(scenario=req.scenario, parameter=req.parameter, run_at=datetime.utcnow(), results=[])
            
        results = [ScenarioResult(
            unique_id=r['unique_id'], 
            baseline_value=r['baseline_value'], 
            scenario_value=r['scenario_value'], 
            delta_pct=r['delta_pct']) for _, r in df.iterrows()]
            
        return ScenarioResponse(scenario=req.scenario, parameter=req.parameter, run_at=datetime.utcnow(), results=results)
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
