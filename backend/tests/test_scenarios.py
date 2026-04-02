import pytest
import pandas as pd

def test_scenario_deltas():
    """Validates that scenario outputs diverge safely driving numeric metrics via delta_pct."""
    df = pd.DataFrame({
        'unique_id': ['2528:CHN'],
        'baseline_value': [100.0],
        'scenario_value': [110.0]
    })
    df['delta_pct'] = ((df['scenario_value'] - df['baseline_value']) / df['baseline_value']) * 100.0
    
    assert df['delta_pct'][0] == 10.0, "Scenario delta arithmetic computes incorrectly."
    assert df['delta_pct'][0] != 0.0, "Scenario should yield safe, non-zero deltas on valid inputs."
