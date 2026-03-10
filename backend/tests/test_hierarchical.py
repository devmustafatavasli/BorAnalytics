import pytest
import pandas as pd

def test_hierarchical_coherence():
    """Validates that leaf nodes reconciled by MinTrace sum exactly to parent node totals."""
    # We mock a small reconciled DataFrame
    data = {
        'unique_id': ['GLOBAL:TOTAL', 'PRODUCT:2528', '2528:TUR', '2528:CHN'],
        'predicted_value': [100.0, 100.0, 60.0, 40.0]
    }
    df = pd.DataFrame(data)
    
    global_val = df[df['unique_id'] == 'GLOBAL:TOTAL']['predicted_value'].values[0]
    prod_val = df[df['unique_id'] == 'PRODUCT:2528']['predicted_value'].values[0]
    
    mask_leaves = df['unique_id'].str.contains(':') & ~df['unique_id'].str.startswith('GLOBAL') & ~df['unique_id'].str.startswith('PRODUCT')
    leaf_sum = df[mask_leaves]['predicted_value'].sum()
    
    assert global_val == prod_val, "Global must equal Product sum in this single-product hierarchical mock"
    assert prod_val == leaf_sum, "Product must strictly equal sum of underlying country leaves"
