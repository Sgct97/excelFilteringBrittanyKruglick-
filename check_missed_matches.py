#!/usr/bin/env python3
"""Check if we're missing legitimate matches due to strict thresholds or other issues."""

import pandas as pd
from fuzzy_matcher import run_specific_match, preprocess_data

def analyze_missed_matches():
    """Analyze rows that didn't get matches to see if we missed legitimate ones."""
    
    try:
        print("🔍 Analyzing potential missed matches...")
        
        # Read the actual data sheets
        all_sheets = pd.read_excel('FuzzyMatch_Tool.xlsm', sheet_name=None, engine='openpyxl')
        
        # Find data sheets (not results)
        data_sheets = {name: df for name, df in all_sheets.items() if not name.startswith('results_')}
        sheet_names = list(data_sheets.keys())
        
        if len(sheet_names) < 2:
            print("❌ Need at least 2 data sheets")
            return
        
        sheet1_raw = data_sheets[sheet_names[0]]
        sheet2_raw = data_sheets[sheet_names[1]]
        
        # Auto-detect master vs input (same logic as run_from_excel.py)
        if len(sheet1_raw) > len(sheet2_raw):
            input_raw = sheet2_raw
            master_raw = sheet1_raw
            input_name = sheet_names[1]
            master_name = sheet_names[0]
        else:
            input_raw = sheet1_raw
            master_raw = sheet2_raw
            input_name = sheet_names[0] 
            master_name = sheet_names[1]
        
        print(f"Input sheet: {input_name} ({len(input_raw)} rows)")
        print(f"Master sheet: {master_name} ({len(master_raw)} rows)")
        
        # Preprocess
        df_input = preprocess_data(input_raw)
        df_master = preprocess_data(master_raw)
        
        print(f"\nAfter preprocessing:")
        print(f"Input: {len(df_input)} rows")
        print(f"Master: {len(df_master)} rows")
        
        # Test with LOWER thresholds to see what we might be missing
        match_types = ['FullName', 'LastNameAddress', 'FullAddress']
        current_thresholds = [85.0, 75.0, 80.0]
        test_thresholds = [70.0, 60.0, 65.0]  # Much lower
        
        for i, match_type in enumerate(match_types):
            print(f"\n{'='*50}")
            print(f"ANALYZING {match_type.upper()}")
            print(f"{'='*50}")
            
            current_thresh = current_thresholds[i]
            test_thresh = test_thresholds[i]
            
            # Get results with current threshold
            current_results = run_specific_match(df_input, df_master, match_type, current_thresh)
            
            # Get results with lower threshold  
            test_results = run_specific_match(df_input, df_master, match_type, test_thresh)
            
            print(f"Current threshold ({current_thresh}%): {len(current_results)} matches")
            print(f"Lower threshold ({test_thresh}%): {len(test_results)} matches")
            
            # Find the additional matches we get with lower threshold
            additional_matches = len(test_results) - len(current_results)
            if additional_matches > 0:
                print(f"📈 {additional_matches} additional matches found with lower threshold")
                
                # Show some examples of what we might be missing
                if len(test_results) > len(current_results):
                    # Get the lowest scoring matches from the expanded results
                    lowest_scores = test_results.nsmallest(10, 'Match Score')
                    print(f"\nExamples of matches at {test_thresh}%-{current_thresh}% range:")
                    for j, row in lowest_scores.iterrows():
                        if row['Match Score'] < current_thresh:
                            print(f"  {row['Match Score']:.1f}% - '{row['Name A']}' vs '{row['Name B']}'")
                            if match_type != 'FullName':  # Show addresses for address-based matching
                                print(f"          '{row['Address A']}'")
                                print(f"          '{row['Address B']}'")
                            if j >= 2:  # Limit to first 3 examples
                                break
                    
            else:
                print(f"✅ No additional matches found - threshold seems appropriate")
        
        # Check unmatched input rows
        print(f"\n{'='*50}")
        print("UNMATCHED INPUT ANALYSIS")
        print(f"{'='*50}")
        
        # Read results to see which input rows got matches
        results_sheets = {name: df for name, df in all_sheets.items() if name.startswith('results_')}
        
        for match_type in match_types:
            results_name = f'results_{match_type}'
            if results_name in results_sheets:
                results_df = results_sheets[results_name]
                matched_rows = set(results_df['Sheet A Row'] - 2)  # Convert back to 0-based indexing
                total_input_rows = set(range(len(df_input)))
                unmatched_rows = total_input_rows - matched_rows
                
                print(f"\n{match_type}:")
                print(f"  Matched: {len(matched_rows)} rows")
                print(f"  Unmatched: {len(unmatched_rows)} rows ({len(unmatched_rows)/len(df_input)*100:.1f}%)")
                
                if len(unmatched_rows) > 0:
                    # Show some examples of unmatched rows
                    print(f"  Examples of unmatched input rows:")
                    for i, row_idx in enumerate(list(unmatched_rows)[:3]):
                        if row_idx < len(df_input):
                            row = df_input.iloc[row_idx]
                            name = f"{row['First_Name']} {row['Last_Name']}".strip()
                            print(f"    Row {row_idx+2}: {name} - {row['FullAddress']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_missed_matches()