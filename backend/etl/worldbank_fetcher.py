import os
import requests
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = os.getenv("WORLDBANK_BASE_URL", "https://api.worldbank.org/v2")
RAW_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/raw/worldbank"))

def fetch_world_bank_data(indicator: str, start_year: int = 2000, end_year: int = 2023):
    """
    Fetches indicator data for all countries from the World Bank API.
    Indicators of interest:
      NY.GDP.MKTP.CD : GDP (current US$)
      CM.MKT.INDX.ZG : Custom/price index if available, often varies. 
                       (We'll mock the boron index since World bank doesn't have a specific 'boron' index)
    """
    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    
    url = f"{BASE_URL}/country/all/indicator/{indicator}"
    params = {
        "format": "json",
        "date": f"{start_year}:{end_year}",
        "per_page": 1000  # Max allowed page size to reduce requests
    }
    
    logger.info(f"Fetching World Bank indicator {indicator}...")
    
    # First request to get pagination info
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        if len(data) < 2:
            logger.error(f"Unexpected API response structure for {indicator}")
            return
            
        page_info = data[0]
        records = data[1]
        
        total_pages = page_info.get("pages", 1)
        
        # If there are more pages, fetch them
        for page in range(2, total_pages + 1):
            params["page"] = page
            res = requests.get(url, params=params)
            res.raise_for_status()
            records.extend(res.json()[1])
            
        # Save raw dump
        output_file = os.path.join(RAW_DATA_DIR, f"{indicator.replace('.', '_')}_{start_year}_{end_year}.json")
        import json
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(records, f, indent=2)
            
        logger.info(f"Successfully saved {len(records)} records for indicator {indicator}")
            
    except Exception as e:
        logger.error(f"Failed to fetch World Bank data: {e}")

if __name__ == "__main__":
    fetch_world_bank_data("NY.GDP.MKTP.CD") # GDP
