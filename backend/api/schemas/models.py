from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class CountryResponse(BaseModel):
    iso3: str
    name: str
    region: Optional[str] = None
    
    class Config:
        from_attributes = True

class ProductResponse(BaseModel):
    hs_code: str
    name: str
    category: Optional[str] = None
    
    class Config:
        from_attributes = True

class ExportResponse(BaseModel):
    year: int
    country_name: str
    country_iso3: str
    product_name: str
    hs_code: str
    value_usd: float
    volume_tons: float
    anomaly_flag: bool = False
    
    class Config:
        from_attributes = True

class ProductionResponse(BaseModel):
    year: int
    facility: str
    product_name: str
    hs_code: str
    volume_tons: float
    
    class Config:
        from_attributes = True

class ForecastPoint(BaseModel):
    year: int
    predicted_value: float
    lower_ci: Optional[float] = None
    upper_ci: Optional[float] = None

class PredictionResponse(BaseModel):
    country_name: str
    product_name: str
    model_type: str
    mae: Optional[float] = None
    rmse: Optional[float] = None
    forecasts: List[ForecastPoint]

class TopDestinationResponse(BaseModel):
    country_name: str
    value_usd: float
    
class YoYGrowthResponse(BaseModel):
    year: int
    value_usd: float
    yoy_growth_pct: float
    
class MarketShareResponse(BaseModel):
    year: int
    turkey_share_pct: float
    row_share_pct: float
    turkey_value_usd: float
    global_value_usd: float
