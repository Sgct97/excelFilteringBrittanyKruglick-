#!/usr/bin/env python3
"""Test the trailer/lot example that should not match."""

from fuzzy_matcher import compute_address_score
from rapidfuzz import fuzz

def test_trailer_lot_example():
    """Test the trailer vs lot example with new cosine similarity."""
    print("=== Testing Trailer vs Lot Example (Cosine Similarity) ===")
    
    addr1 = "268 FLANDERS RD TRLR 9, MYSTIC, CT 6355"
    addr2 = "268 FLANDERS RD LOT 3, MYSTIC, CT 06355"
    
    print(f"Address 1: {addr1}")
    print(f"Address 2: {addr2}")
    
    # Test new cosine similarity scoring
    cosine_score = compute_address_score(addr1, addr2)
    print(f"New cosine score: {cosine_score:.2f} (should be much lower)")
    
    # Compare to old rapidfuzz approach
    rapidfuzz_score = fuzz.ratio(addr1, addr2)
    print(f"Old rapidfuzz score: {rapidfuzz_score:.2f}")
    
    print(f"\nImprovement:")
    if cosine_score < 70:
        print(f"✅ SUCCESS: Cosine similarity correctly identified different property types!")
        print(f"   TRLR 9 vs LOT 3 now properly distinguished")
    else:
        print(f"❌ PROBLEM: Score still too high at {cosine_score:.2f}")

if __name__ == "__main__":
    test_trailer_lot_example()