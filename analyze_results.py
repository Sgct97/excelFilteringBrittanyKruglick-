#!/usr/bin/env python3
"""Analyze the results from the 3 matching sheets to identify issues and success rates."""

import pandas as pd
import re
from collections import defaultdict

def extract_house_number(address):
    """Extract house number from address."""
    match = re.search(r'^\d+', address.strip())
    return int(match.group()) if match else None

def extract_street_name(address):
    """Extract street name (everything between house number and first comma)."""
    # Remove house number and everything after first comma
    no_house = re.sub(r'^\d+\s*', '', address.strip())
    street = no_house.split(',')[0].strip()
    return street

def extract_property_designator(address):
    """Extract property designator (APT, UNIT, TRLR, LOT, etc.)."""
    pattern = r'\s(APT|APARTMENT|UNIT|TRLR|TRAILER|LOT|BLDG|BUILDING|STE|SUITE|FLOOR|FL|RM|ROOM|SPACE|SPC|#)\s+([A-Z0-9]+)'
    match = re.search(pattern, address, re.IGNORECASE)
    if match:
        return f"{match.group(1)} {match.group(2)}"
    return None

def analyze_sheet(df, sheet_name):
    """Analyze a results sheet for problematic matches."""
    print(f"\n{'='*60}")
    print(f"ANALYZING {sheet_name.upper()}")
    print(f"{'='*60}")
    
    if df.empty:
        print("❌ No results found in this sheet!")
        return
    
    print(f"📊 Total matches: {len(df)}")
    print(f"📊 Score range: {df['Match Score'].min():.2f} - {df['Match Score'].max():.2f}")
    print(f"📊 Average score: {df['Match Score'].mean():.2f}")
    
    # Score distribution
    print(f"\n📈 Score Distribution:")
    for threshold in [100, 95, 90, 85, 80, 75, 70]:
        count = len(df[df['Match Score'] >= threshold])
        pct = (count / len(df)) * 100
        print(f"   ≥{threshold}%: {count:4d} matches ({pct:5.1f}%)")
    
    # Analyze problematic patterns
    problems = defaultdict(list)
    
    for idx, row in df.iterrows():
        addr_a = row['Address A']
        addr_b = row['Address B']
        score = row['Match Score']
        
        # Extract components
        house_a = extract_house_number(addr_a)
        house_b = extract_house_number(addr_b)
        street_a = extract_street_name(addr_a)
        street_b = extract_street_name(addr_b)
        prop_a = extract_property_designator(addr_a)
        prop_b = extract_property_designator(addr_b)
        
        # Problem 1: Same house number, different street names (Henry/Fuller issue)
        if house_a and house_b and house_a == house_b and street_a != street_b and score > 70:
            problems['same_house_diff_street'].append({
                'score': score,
                'addr_a': addr_a,
                'addr_b': addr_b,
                'street_a': street_a,
                'street_b': street_b
            })
        
        # Problem 2: Different property types (TRLR vs LOT should be 0)
        if prop_a and prop_b:
            type_a = prop_a.split()[0]
            type_b = prop_b.split()[0]
            if type_a != type_b and score > 50:
                problems['diff_property_types'].append({
                    'score': score,
                    'addr_a': addr_a,
                    'addr_b': addr_b,
                    'prop_a': prop_a,
                    'prop_b': prop_b
                })
        
        # Problem 3: Very different house numbers but high scores
        if house_a and house_b and abs(house_a - house_b) > 50 and score > 70:
            problems['diff_house_numbers'].append({
                'score': score,
                'addr_a': addr_a,
                'addr_b': addr_b,
                'house_a': house_a,
                'house_b': house_b,
                'diff': abs(house_a - house_b)
            })
        
        # Problem 4: Different cities but high scores
        city_a = addr_a.split(',')[-3].strip() if len(addr_a.split(',')) >= 3 else ""
        city_b = addr_b.split(',')[-3].strip() if len(addr_b.split(',')) >= 3 else ""
        if city_a != city_b and score > 60:
            problems['diff_cities'].append({
                'score': score,
                'addr_a': addr_a,
                'addr_b': addr_b,
                'city_a': city_a,
                'city_b': city_b
            })
    
    # Report problems
    print(f"\n🚨 PROBLEM ANALYSIS:")
    
    if problems['same_house_diff_street']:
        print(f"\n❌ Same house #, different streets: {len(problems['same_house_diff_street'])} cases")
        print("   (These should score LOW but are scoring HIGH)")
        for i, p in enumerate(problems['same_house_diff_street'][:3]):  # Show first 3
            print(f"   Example {i+1}: {p['score']:.1f}% - '{p['street_a']}' vs '{p['street_b']}'")
    else:
        print(f"\n✅ Same house #, different streets: No problematic cases found")
    
    if problems['diff_property_types']:
        print(f"\n❌ Different property types: {len(problems['diff_property_types'])} cases")
        print("   (These should be 0% but are scoring higher)")
        for i, p in enumerate(problems['diff_property_types'][:3]):
            print(f"   Example {i+1}: {p['score']:.1f}% - '{p['prop_a']}' vs '{p['prop_b']}'")
    else:
        print(f"\n✅ Different property types: No problematic cases found")
    
    if problems['diff_house_numbers']:
        print(f"\n❌ Very different house numbers: {len(problems['diff_house_numbers'])} cases")
        print("   (These should score LOW but are scoring HIGH)")
        for i, p in enumerate(problems['diff_house_numbers'][:3]):
            print(f"   Example {i+1}: {p['score']:.1f}% - {p['house_a']} vs {p['house_b']} (diff: {p['diff']})")
    else:
        print(f"\n✅ Very different house numbers: No problematic cases found")
    
    if problems['diff_cities']:
        print(f"\n❌ Different cities: {len(problems['diff_cities'])} cases")
        print("   (These should score LOW but are scoring HIGH)")
        for i, p in enumerate(problems['diff_cities'][:3]):
            print(f"   Example {i+1}: {p['score']:.1f}% - '{p['city_a']}' vs '{p['city_b']}'")
    else:
        print(f"\n✅ Different cities: No problematic cases found")
    
    # Calculate success rate
    total_problems = sum(len(problems[key]) for key in problems)
    success_rate = ((len(df) - total_problems) / len(df)) * 100 if len(df) > 0 else 0
    
    print(f"\n📈 SUMMARY:")
    print(f"   Total matches: {len(df)}")
    print(f"   Problematic matches: {total_problems}")
    print(f"   Success rate: {success_rate:.1f}%")
    
    return problems

def main():
    """Analyze the results from FuzzyMatch_Tool.xlsm."""
    
    try:
        print("🔍 Reading results from FuzzyMatch_Tool.xlsm...")
        
        # Read all sheets
        all_sheets = pd.read_excel('FuzzyMatch_Tool.xlsm', sheet_name=None, engine='openpyxl')
        
        # Find results sheets
        results_sheets = {name: df for name, df in all_sheets.items() if name.startswith('results_')}
        
        if not results_sheets:
            print("❌ No results sheets found! Make sure you've run the matching tool first.")
            return
        
        print(f"📋 Found {len(results_sheets)} results sheets: {list(results_sheets.keys())}")
        
        # Analyze each sheet
        all_problems = {}
        for sheet_name, df in results_sheets.items():
            match_type = sheet_name.replace('results_', '')
            all_problems[match_type] = analyze_sheet(df, match_type)
        
        # Overall summary
        print(f"\n{'='*60}")
        print("OVERALL SUMMARY")
        print(f"{'='*60}")
        
        for match_type, problems in all_problems.items():
            total_problems = sum(len(problems[key]) for key in problems)
            total_matches = len(results_sheets[f'results_{match_type}'])
            success_rate = ((total_matches - total_problems) / total_matches) * 100 if total_matches > 0 else 0
            print(f"{match_type:15}: {total_matches:4d} matches, {total_problems:3d} problems, {success_rate:5.1f}% success")
        
    except FileNotFoundError:
        print("❌ Could not find FuzzyMatch_Tool.xlsm. Make sure it exists and has results sheets.")
    except Exception as e:
        print(f"❌ Error analyzing results: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()