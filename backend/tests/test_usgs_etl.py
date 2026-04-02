import pytest
import pandas as pd
from backend.etl.usgs_fetcher import fetch_usgs_data

def test_usgs_production_positive():
    df = fetch_usgs_data()
    assert not df.empty, "USGS fetcher returned empty DataFrame."
    # Ensure production_tons > 0 as required by prompt
    assert (df['production_tons'] > 0).all(), "All production_tons must be rigidly strictly > 0"
