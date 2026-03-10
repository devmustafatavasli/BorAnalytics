import pytest
import pandas as pd

def test_bilateral_gap_computation():
    """Validates the standard arithmetic for bilateral_gap_pct matching specific prompt constraints."""
    df = pd.DataFrame({'export_val': [100.0, 50.0], 'mirror_val': [80.0, 50.0]})
    df['bilateral_gap_pct'] = ((df['export_val'] - df['mirror_val']) / df['export_val']) * 100
    
    assert df['bilateral_gap_pct'][0] == 20.0, "Gap formula arithmetic is mismatched."
    assert df['bilateral_gap_pct'][1] == 0.0, "Gap formula zero arithmetic mismatched."
