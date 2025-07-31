#!/usr/bin/env python3
"""Debug why ALICE ST vs VALERIE ST isn't being capped."""

from rapidfuzz import fuzz
import re

def debug_alice_valerie():
    """Debug the ALICE vs VALERIE case specifically."""
    
    addr1 = "8 ALICE ST, NEW LONDON, CT 06320"
    addr2 = "8 VALERIE ST, NEW LONDON, CT 06320"
    
    print("=== Debugging ALICE ST vs VALERIE ST ===")
    print(f"Address 1: {addr1}")
    print(f"Address 2: {addr2}")
    print()
    
    # Extract street names (same logic as in the fix)
    street1 = re.sub(r'^\d+\s*', '', addr1.strip()).split(',')[0].strip()
    street2 = re.sub(r'^\d+\s*', '', addr2.strip()).split(',')[0].strip()
    
    print(f"Extracted street 1: '{street1}'")
    print(f"Extracted street 2: '{street2}'")
    print()
    
    # Check street similarity
    street_similarity = fuzz.token_set_ratio(street1, street2)
    print(f"Street similarity (token_set_ratio): {street_similarity:.2f}%")
    print(f"Street similarity threshold: 70%")
    print(f"Streets considered different: {street_similarity < 70}")
    print()
    
    # Test full address similarity
    full_similarity = fuzz.ratio(addr1, addr2)
    print(f"Full address similarity (fuzz.ratio): {full_similarity:.2f}%")
    
    if street_similarity < 70:
        capped_score = min(full_similarity * 0.7, 65.0)
        print(f"Should be capped at: {capped_score:.2f}%")
    else:
        print(f"Not capped (streets considered similar)")
    
    # Test different similarity functions
    print(f"\n=== Different Similarity Functions ===")
    print(f"fuzz.ratio('{street1}', '{street2}'): {fuzz.ratio(street1, street2):.2f}%")
    print(f"fuzz.partial_ratio: {fuzz.partial_ratio(street1, street2):.2f}%")
    print(f"fuzz.token_sort_ratio: {fuzz.token_sort_ratio(street1, street2):.2f}%")
    print(f"fuzz.token_set_ratio: {fuzz.token_set_ratio(street1, street2):.2f}%")

if __name__ == "__main__":
    debug_alice_valerie()