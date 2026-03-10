import os
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("COMTRADE_API_KEY")
BASE_URL = "https://comtradeapi.un.org/data/v1/get/C/A/HS"
# C = Commodity, A = Annual, HS = Harmonized System

RAW_DATA_DIR = os.path.join(os.path.dirname(__file__), "../../data/raw/comtrade")

def fetch_comtrade_data(reporter_iso3: str = "TUR", hs_code: str = "2528", start_year: int = 2000, end_year: int = 2023):
    """
    Fetches annual export data from UN Comtrade API for a specific reporter and commodity code.
    Saves raw responses to /data/raw/comtrade/.
    
    Args:
        reporter_iso3: ISO3 code of the reporting country (default: 'TUR' for Turkey).
        hs_code: Harmonized System product code (default: '2528' for natural borates).
        start_year: Start year for data fetch.
        end_year: End year for data fetch.
    """
    
    if not API_KEY or API_KEY == "your_un_comtrade_api_key_here":
        print("Warning: COMTRADE_API_KEY not set in .env. Skipping actual fetch.")
        return

    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    
    # UN Comtrade allows up to 5 reporters/partners/years per request sometimes, 
    # but querying year-by-year is safer for paginated data to avoid timeouts.
    for year in range(start_year, end_year + 1):
        output_file = os.path.join(RAW_DATA_DIR, f"{reporter_iso3}_{hs_code}_{year}.json")
        
        # Skip if already downloaded
        if os.path.exists(output_file):
            print(f"Skipping {year} - File already exists.")
            continue
            
        print(f"Fetching data for {reporter_iso3} - {hs_code} - {year}...")
        
        params = {
            "reporterCode": 792,  # UN M49 code for Turkey
            "partnerCode": "0",   # 0 = World (or all partners individually depending on API version, we want all partners)
            # Actually, to get all country breakdown we need partnerCode = 'all' or omission depending on endpoint.
            "period": str(year),
            "cmdCode": hs_code,
            "flowCode": "M,X",    # Imports and Exports. M=Import, X=Export
            "subscription-key": API_KEY
        }
        
        try:
            response = requests.get(BASE_URL, params=params)
            
            if response.status_code == 200:
                data = response.json()
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"Successfully saved {year} data.")
            elif response.status_code == 429:
                print(f"Rate limited on year {year}. Retrying after 10 seconds...")
                time.sleep(10)
                # This could be a while loop for robust retry, keeping it simple for now
            else:
                print(f"Failed to fetch {year}: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"Error fetching {year}: {e}")
            
        # Comtrade free tier rate limit is strict
        time.sleep(2) 

if __name__ == "__main__":
    fetch_comtrade_data()
