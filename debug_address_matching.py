#!/usr/bin/env python3
"""Debug script to test address matching logic with specific examples."""

import pandas as pd
from fuzzy_matcher import compute_address_score, compute_address_with_apartment_check, strip_apartment_numbers, compute_lastname_address_score, get_combined_score, compute_individual_scores

def test_apartment_matching():
    """Test the specific apartment examples that should not match."""
    print("=== Testing Apartment Matching Logic ===")
    
    # Test case 1: Different apartment units (should NOT match for FullAddress)
    addr1 = "83 MANSFIELD RD UNIT 329, NEW LONDON, CT 6320"
    addr2 = "83 MANSFIELD RD APT 324, NEW LONDON, CT 06320"
    
    print(f"\nTest 1: Different apartment units")
    print(f"Address 1: {addr1}")
    print(f"Address 2: {addr2}")
    
    # Test compute_address_score (used by FullAddress matching)
    full_score = compute_address_score(addr1, addr2)
    print(f"FullAddress score (should be 0.0): {full_score}")
    
    # Test apartment check directly
    apt_score = compute_address_with_apartment_check(addr1, addr2)
    print(f"Apartment check score (should be 0.0): {apt_score}")
    
    # Test address stripping for LastNameAddress
    addr1_stripped = strip_apartment_numbers(addr1)
    addr2_stripped = strip_apartment_numbers(addr2)
    print(f"Stripped addr1: {addr1_stripped}")
    print(f"Stripped addr2: {addr2_stripped}")
    
    # Test case 2: Zip code differences (should match well)
    print(f"\n\nTest 2: Zip code differences")
    addr3 = "123 MAIN ST, ANYTOWN, CT 6355"
    addr4 = "123 MAIN ST, ANYTOWN, CT 06355-1445"
    print(f"Address 3: {addr3}")
    print(f"Address 4: {addr4}")
    
    zip_score = compute_address_score(addr3, addr4)
    print(f"Zip difference score (should be high): {zip_score}")
    
    # Test case 3: Same apartment (should match)
    print(f"\n\nTest 3: Same apartment")
    addr5 = "83 MANSFIELD RD UNIT 329, NEW LONDON, CT 6320"
    addr6 = "83 MANSFIELD RD APT 329, NEW LONDON, CT 06320"
    print(f"Address 5: {addr5}")
    print(f"Address 6: {addr6}")
    
    same_apt_score = compute_address_score(addr5, addr6)
    print(f"Same apartment score (should be high): {same_apt_score}")

def test_full_matching_logic():
    """Test the full matching logic for all three types."""
    print("\n\n=== Testing Full Matching Logic ===")
    
    # Create test data
    data1 = {
        'First_Name': ['JOHN'],
        'Last_Name': ['SMITH'],
        'Address1': ['83 MANSFIELD RD UNIT 329'],
        'City': ['NEW LONDON'],
        'State': ['CT'],
        'Zip': ['6320'],
        'FullAddress': ['83 MANSFIELD RD UNIT 329, NEW LONDON, CT 6320']
    }
    
    data2 = {
        'First_Name': ['JOHN'],
        'Last_Name': ['SMITH'], 
        'Address1': ['83 MANSFIELD RD APT 324'],
        'City': ['NEW LONDON'],
        'State': ['CT'],
        'Zip': ['06320'],
        'FullAddress': ['83 MANSFIELD RD APT 324, NEW LONDON, CT 06320']
    }
    
    df1 = pd.DataFrame(data1)
    df2 = pd.DataFrame(data2)
    
    row1 = df1.iloc[0]
    row2 = df2.iloc[0]
    
    # Test individual scores
    first_score, last_score, address_score = compute_individual_scores(row1, row2)
    print(f"\nIndividual Scores:")
    print(f"First Name: {first_score}")
    print(f"Last Name: {last_score}")
    print(f"Address: {address_score}")
    
    # Test combined scores for each match type
    scores = (first_score, last_score, address_score)
    
    full_name_score = get_combined_score(scores, 'FullName', row1, row2)
    lastname_addr_score = get_combined_score(scores, 'LastNameAddress', row1, row2)
    full_addr_score = get_combined_score(scores, 'FullAddress', row1, row2)
    
    print(f"\nCombined Scores:")
    print(f"FullName: {full_name_score}")
    print(f"LastNameAddress: {lastname_addr_score}")
    print(f"FullAddress: {full_addr_score} (should be 0.0)")

if __name__ == "__main__":
    test_apartment_matching()
    test_full_matching_logic()