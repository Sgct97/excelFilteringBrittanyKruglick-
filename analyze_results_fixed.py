#!/usr/bin/env python3
"""Analyze the results from the 3 matching sheets to identify ACTUAL issues."""

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

def are_similar_streets(street1, street2):
    """Check if two street names are similar variations (not completely different)."""
    # Normalize common abbreviations
    normalize = lambda s: s.replace('ROAD', 'RD').replace('STREET', 'ST').replace('AVENUE', 'AVE').replace('LANE', 'LN')
    s1_norm = normalize(street1.upper())
    s2_norm = normalize(street2.upper())
    
    # Check if they're the same after normalization
    if s1_norm == s2_norm:
        return True
    
    # Check for common name variations (MICHELLE vs MICHELE)
    from rapidfuzz import fuzz
    similarity = fuzz.ratio(s1_norm, s2_norm)
    return similarity > 85  # High similarity suggests variations of same street

def analyze_sheet(df, sheet_name):
    """Analyze a results sheet for ACTUAL problematic matches."""
    print(f"\n{'='*60}")
    print(f"ANALYZING {sheet_name.upper()}")
    print(f"{'='*60}")
    
    if df.empty:
        print("❌ No results found in this sheet!")
        return {}
    
    print(f"📊 Total matches: {len(df)}")
    print(f"📊 Score range: {df['Match Score'].min():.2f} - {df['Match Score'].max():.2f}")
    print(f"📊 Average score: {df['Match Score'].mean():.2f}")
    
    # Score distribution
    print(f"\n📈 Score Distribution:")
    for threshold in [100, 95, 90, 85, 80, 75, 70]:
        count = len(df[df['Match Score'] >= threshold])
        pct = (count / len(df)) * 100
        print(f"   ≥{threshold}%: {count:4d} matches ({pct:5.1f}%)")
    
    # Analyze ACTUAL problematic patterns based on match type
    problems = defaultdict(list)
    
    for idx, row in df.iterrows():
        addr_a = row['Address A']
        addr_b = row['Address B']
        name_a = row['Name A']
        name_b = row['Name B']
        score = row['Match Score']
        
        # Extract components
        house_a = extract_house_number(addr_a)
        house_b = extract_house_number(addr_b)
        street_a = extract_street_name(addr_a)
        street_b = extract_street_name(addr_b)
        prop_a = extract_property_designator(addr_a)
        prop_b = extract_property_designator(addr_b)
        
        # Parse names
        parts_a = name_a.split()
        parts_b = name_b.split()
        first_a = parts_a[0] if parts_a else ""
        last_a = parts_a[-1] if parts_a else ""
        first_b = parts_b[0] if parts_b else ""
        last_b = parts_b[-1] if parts_b else ""
        
        # FULLNAME-specific problems: Different names scoring high
        if sheet_name.upper() == 'FULLNAME':
            # Only flag if BOTH first and last names are completely different
            if (first_a != first_b and last_a != last_b and 
                score > 80 and 
                not (first_a in first_b or first_b in first_a) and  # Not nicknames
                not (last_a in last_b or last_b in last_a)):       # Not similar last names
                problems['completely_diff_names'].append({
                    'score': score,
                    'name_a': name_a,
                    'name_b': name_b,
                    'addr_a': addr_a,
                    'addr_b': addr_b
                })
        
        # FULLADDRESS-specific problems
        elif sheet_name.upper() == 'FULLADDRESS':
            # Problem 1: Same house number, COMPLETELY different streets (not variations)
            if (house_a and house_b and house_a == house_b and 
                street_a != street_b and score > 80 and 
                not are_similar_streets(street_a, street_b)):
                problems['diff_streets_same_house'].append({
                    'score': score,
                    'addr_a': addr_a,
                    'addr_b': addr_b,
                    'street_a': street_a,
                    'street_b': street_b
                })
            
            # Problem 2: Different property types (TRLR vs LOT should be near 0)
            if prop_a and prop_b:
                type_a = prop_a.split()[0]
                type_b = prop_b.split()[0]
                if type_a != type_b and score > 20:  # Should be very low, not 0 due to other similarities
                    problems['diff_property_types'].append({
                        'score': score,
                        'addr_a': addr_a,
                        'addr_b': addr_b,
                        'prop_a': prop_a,
                        'prop_b': prop_b
                    })
        
        # LASTNAMEADDRESS-specific problems
        elif sheet_name.upper() == 'LASTNAMEADDRESS':
            # Problem: Different last names scoring high
            if (last_a != last_b and score > 80 and 
                not (last_a in last_b or last_b in last_a)):  # Not similar variations
                problems['diff_last_names'].append({
                    'score': score,
                    'name_a': name_a,
                    'name_b': name_b,
                    'last_a': last_a,
                    'last_b': last_b,
                    'addr_a': addr_a,
                    'addr_b': addr_b
                })
    
    # Report ACTUAL problems
    print(f"\n🚨 ACTUAL PROBLEM ANALYSIS:")
    
    total_problems = 0
    
    if sheet_name.upper() == 'FULLNAME':
        if problems['completely_diff_names']:
            count = len(problems['completely_diff_names'])
            total_problems += count
            print(f"\n❌ Completely different names scoring high: {count} cases")
            print("   Examples:")
            for i, p in enumerate(problems['completely_diff_names'][:3]):
                print(f"     {i+1}. {p['score']:.1f}% - '{p['name_a']}' vs '{p['name_b']}'")
        else:
            print(f"\n✅ FullName matching: No problematic cases found")
    
    elif sheet_name.upper() == 'FULLADDRESS':
        if problems['diff_streets_same_house']:
            count = len(problems['diff_streets_same_house'])
            total_problems += count
            print(f"\n❌ Same house #, completely different streets: {count} cases")
            print("   Examples:")
            for i, p in enumerate(problems['diff_streets_same_house'][:3]):
                print(f"     {i+1}. {p['score']:.1f}% - '{p['street_a']}' vs '{p['street_b']}'")
        else:
            print(f"\n✅ Same house, different streets: No problematic cases found")
        
        if problems['diff_property_types']:
            count = len(problems['diff_property_types'])
            total_problems += count
            print(f"\n❌ Different property types scoring >20%: {count} cases")
            print("   Examples:")
            for i, p in enumerate(problems['diff_property_types'][:3]):
                print(f"     {i+1}. {p['score']:.1f}% - '{p['prop_a']}' vs '{p['prop_b']}'")
        else:
            print(f"\n✅ Property type matching: No problematic cases found")
    
    elif sheet_name.upper() == 'LASTNAMEADDRESS':
        if problems['diff_last_names']:
            count = len(problems['diff_last_names'])
            total_problems += count
            print(f"\n❌ Different last names scoring high: {count} cases")
            print("   Examples:")
            for i, p in enumerate(problems['diff_last_names'][:3]):
                print(f"     {i+1}. {p['score']:.1f}% - '{p['last_a']}' vs '{p['last_b']}'")
        else:
            print(f"\n✅ LastName matching: No problematic cases found")
    
    # Calculate success rate
    success_rate = ((len(df) - total_problems) / len(df)) * 100 if len(df) > 0 else 0
    
    print(f"\n📈 SUMMARY:")
    print(f"   Total matches: {len(df)}")
    print(f"   Actual problems: {total_problems}")
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
            print(f"{match_type:15}: {total_matches:4d} matches, {total_problems:3d} actual problems, {success_rate:5.1f}% success")
        
    except FileNotFoundError:
        print("❌ Could not find FuzzyMatch_Tool.xlsm. Make sure it exists and has results sheets.")
    except Exception as e:
        print(f"❌ Error analyzing results: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()