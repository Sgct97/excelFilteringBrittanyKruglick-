#!/usr/bin/env python3
"""Test the trailer/lot example that should not match."""

from fuzzy_matcher import compute_address_score, compute_address_with_apartment_check

def test_trailer_lot_example():
    """Test the specific trailer vs lot example."""
    print("=== Testing Trailer vs Lot Example ===")
    
    addr1 = "268 FLANDERS RD TRLR 9, MYSTIC, CT 6355"
    addr2 = "268 FLANDERS RD LOT 3, MYSTIC, CT 06355"
    
    print(f"Address 1: {addr1}")
    print(f"Address 2: {addr2}")
    
    # Test current logic
    score = compute_address_score(addr1, addr2)
    print(f"Current FullAddress score (should be 0.0 but probably isn't): {score}")
    
    # Test apartment check directly
    apt_score = compute_address_with_apartment_check(addr1, addr2)
    print(f"Current apartment check score (should be 0.0 but probably isn't): {apt_score}")

if __name__ == "__main__":
    test_trailer_lot_example()