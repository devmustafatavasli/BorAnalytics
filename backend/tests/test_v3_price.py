import pytest
import pandas as pd

def test_currency_conversion_logic():
    """Validates the math parsing nominal USD dynamically into 2010 Real USD based on TRY devaluation scales."""
    df = pd.DataFrame({
        'year': [2010, 2023],
        'unit_price_usd_per_tonne': [100.0, 100.0],
        'usd_per_try': [0.66, 0.04] # Approximated ratio scaling
    })
    
    usd_try_2010 = df[df['year'] == 2010]['usd_per_try'].values[0]
    df['unit_price_usd_real_2010'] = df['unit_price_usd_per_tonne'] * (df['usd_per_try'] / usd_try_2010)
    
    assert df['unit_price_usd_real_2010'][0] == 100.0, "Base 2010 year pricing must equal nominal rates inherently."
    assert df['unit_price_usd_real_2010'][1] < 100.0, "With steep TRY metric losses, adjusted parity value falls appropriately mapping constant indexing."
