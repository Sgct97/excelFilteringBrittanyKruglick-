#!/usr/bin/env python3
"""Test the specific Henry St vs Fuller St example."""

from fuzzy_matcher import compute_address_score
from rapidfuzz import fuzz

def test_henry_fuller():
    """Test the Henry St vs Fuller St example with new cosine similarity."""
    print("=== Testing Henry St vs Fuller St (Cosine Similarity) ===")
    
    addr1 = "61 HENRY ST, NEW LONDON, CT 06320"
    addr2 = "61 FULLER ST, NEW LONDON, CT 06320"
    
    print(f"Address 1: {addr1}")
    print(f"Address 2: {addr2}")
    
    # Test new cosine similarity scoring
    cosine_score = compute_address_score(addr1, addr2)
    print(f"New cosine score: {cosine_score:.2f} (should be much lower than 87.88)")
    
    # Compare to old rapidfuzz approach
    rapidfuzz_score = fuzz.ratio(addr1, addr2)
    print(f"Old rapidfuzz score: {rapidfuzz_score:.2f}")
    
    print(f"\nImprovement:")
    if cosine_score < 70:
        print(f"✅ SUCCESS: Cosine similarity correctly identified different streets!")
        print(f"   Score dropped from ~87.88 to {cosine_score:.2f}")
    else:
        print(f"❌ PROBLEM: Score still too high at {cosine_score:.2f}")
    
    # Test street names only for comparison
    street1 = "HENRY ST"
    street2 = "FULLER ST" 
    print(f"\nStreet name comparison:")
    print(f"  '{street1}' vs '{street2}': {fuzz.ratio(street1, street2):.2f}%")

if __name__ == "__main__":
    test_henry_fuller()