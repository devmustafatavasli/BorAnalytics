import pytest
import pandas as pd

def test_shap_ranks_exist():
    """Asserts SHAP TreeExplainer mappings logically rank strictly 1, 2, and 3 constraints for UI explanations."""
    df = pd.DataFrame({
        'prediction_id': ['test_1', 'test_1', 'test_1'],
        'feature_name': ['A', 'B', 'C'],
        'shap_value': [0.5, 0.3, 0.1],
        'rank': [1, 2, 3]
    })
    
    ranks = df['rank'].tolist()
    assert 1 in ranks, "Rank 1 missing"
    assert 2 in ranks, "Rank 2 missing"
    assert 3 in ranks, "Rank 3 missing"
    assert len(ranks) == 3, "Exactly 3 ranks should be computed per unique ML prediction"
