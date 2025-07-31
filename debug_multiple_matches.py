#!/usr/bin/env python3
"""Debug script to see why we're getting multiple matches per input row."""

import pandas as pd
from fuzzy_matcher import run_specific_match, preprocess_data

def debug_matching():
    """Debug the matching logic with a tiny sample to see the problem."""
    
    # Create tiny test data
    input_data = {
        'First_Name': ['JOHN', 'MARY'],
        'Last_Name': ['SMITH', 'JONES'], 
        'Address1': ['123 MAIN ST', '456 OAK ST'],
        'City': ['ANYTOWN', 'SOMEWHERE'],
        'State': ['CT', 'CT'],
        'Zip': ['06355', '06355'],
        'FullAddress': ['123 MAIN ST, ANYTOWN, CT 06355', '456 OAK ST, SOMEWHERE, CT 06355']
    }
    
    master_data = {
        'First_Name': ['JOHN', 'JOHN', 'JANE', 'MARY', 'MICHAEL'],
        'Last_Name': ['SMITH', 'SMYTH', 'DOE', 'JONES', 'BROWN'],
        'Address1': ['123 MAIN ST', '124 MAIN ST', '789 ELM ST', '456 OAK ST', '321 PINE AVE'],
        'City': ['ANYTOWN', 'ANYTOWN', 'SOMEWHERE', 'SOMEWHERE', 'ELSEWHERE'],
        'State': ['CT', 'CT', 'CT', 'CT', 'CT'],
        'Zip': ['06355', '06355', '06355', '06355', '06355'],
        'FullAddress': [
            '123 MAIN ST, ANYTOWN, CT 06355',
            '124 MAIN ST, ANYTOWN, CT 06355', 
            '789 ELM ST, SOMEWHERE, CT 06355',
            '456 OAK ST, SOMEWHERE, CT 06355',
            '321 PINE AVE, ELSEWHERE, CT 06355'
        ]
    }
    
    df_input = pd.DataFrame(input_data)
    df_master = pd.DataFrame(master_data)
    
    print("=== DEBUG: Multiple Matches Issue ===")
    print(f"Input rows: {len(df_input)}")
    print(f"Master rows: {len(df_master)}")
    print()
    
    # Test FullAddress matching
    results = run_specific_match(df_input, df_master, 'FullAddress', threshold=70.0)
    
    print(f"Results found: {len(results)}")
    print()
    
    if len(results) > len(df_input):
        print("❌ PROBLEM: More results than input rows!")
        print("This confirms the multiple matches bug.")
        print()
        print("Results breakdown:")
        for i, row in results.iterrows():
            print(f"  Result {i+1}: Sheet A Row {row['Sheet A Row']} → Sheet B Row {row['Sheet B Row']} (Score: {row['Match Score']})")
    else:
        print("✅ OK: Results count matches expectation")
    
    return results

if __name__ == "__main__":
    debug_matching()