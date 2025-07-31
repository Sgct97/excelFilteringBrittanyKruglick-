#!/usr/bin/env python3
"""Detailed debugging of the trailer/lot example."""

import re
from rapidfuzz import fuzz

def debug_apartment_pattern():
    """Debug the apartment pattern matching."""
    print("=== Debugging Apartment Pattern ===")
    
    addr1 = "268 FLANDERS RD TRLR 9, MYSTIC, CT 6355"
    addr2 = "268 FLANDERS RD LOT 3, MYSTIC, CT 06355"
    
    # Test the pattern directly (fixed with word boundaries)
    apt_pattern = r'\b(?:APT|APARTMENT|UNIT|TRLR|TRAILER|LOT|BLDG|BUILDING|STE|SUITE|FLOOR|FL|RM|ROOM|SPACE|SPC|#)\s*([A-Z0-9]+)'
    
    apt1_match = re.search(apt_pattern, addr1, re.IGNORECASE)
    apt2_match = re.search(apt_pattern, addr2, re.IGNORECASE)
    
    print(f"Address 1: {addr1}")
    print(f"Pattern match 1: {apt1_match}")
    if apt1_match:
        print(f"  Full match: '{apt1_match.group(0)}'")
        print(f"  Match group: '{apt1_match.group(1)}'")
        print(f"  Match span: {apt1_match.span()}")
    
    print(f"\nAddress 2: {addr2}")
    print(f"Pattern match 2: {apt2_match}")
    if apt2_match:
        print(f"  Full match: '{apt2_match.group(0)}'")
        print(f"  Match group: '{apt2_match.group(1)}'")
        print(f"  Match span: {apt2_match.span()}")
    
    # Test house number extraction
    print(f"\n=== House Number Extraction ===")
    num1_match = re.search(r'^\d+', addr1.strip())
    num2_match = re.search(r'^\d+', addr2.strip())
    
    print(f"House number 1: {num1_match.group() if num1_match else None}")
    print(f"House number 2: {num2_match.group() if num2_match else None}")
    
    if num1_match and num2_match:
        num1 = int(num1_match.group())
        num2 = int(num2_match.group())
        num_diff = abs(num1 - num2)
        print(f"Number difference: {num_diff}")
        
        if num_diff == 0:
            print("Should call apartment check function!")
            
            # Manual apartment check
            if apt1_match and apt2_match:
                apt1 = apt1_match.group(1).upper()
                apt2 = apt2_match.group(1).upper()
                print(f"Apartment 1: '{apt1}'")
                print(f"Apartment 2: '{apt2}'")
                
                if apt1 != apt2:
                    print("Different apartments - should return 0.0!")
                else:
                    print("Same apartments - should use fuzz.ratio")
            elif apt1_match or apt2_match:
                print("Only one has apartment - should return 0.0!")
            else:
                print("No apartments found - should use fuzz.ratio")
                ratio_score = fuzz.ratio(addr1, addr2)
                print(f"fuzz.ratio score: {ratio_score}")

if __name__ == "__main__":
    debug_apartment_pattern()