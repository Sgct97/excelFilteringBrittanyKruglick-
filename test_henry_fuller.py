#!/usr/bin/env python3
"""Test the specific Henry St vs Fuller St example."""

from fuzzy_matcher import compute_address_score, compute_address_with_apartment_check
from rapidfuzz import fuzz

def test_henry_fuller():
    """Test the Henry St vs Fuller St example that's scoring too high."""
    print("=== Testing Henry St vs Fuller St ===")
    
    addr1 = "61 HENRY ST, NEW LONDON, CT 06320"
    addr2 = "61 FULLER ST, NEW LONDON, CT 06320"
    
    print(f"Address 1: {addr1}")
    print(f"Address 2: {addr2}")
    
    # Test current scoring
    score = compute_address_score(addr1, addr2)
    print(f"Current score: {score:.2f} (user says 87.88)")
    
    # Debug why it's scoring high
    print(f"\nDebugging:")
    print(f"House numbers: 61 == 61 (same)")
    print(f"Since house numbers are same, calling apartment check...")
    
    apt_score = compute_address_with_apartment_check(addr1, addr2)
    print(f"Apartment check score: {apt_score:.2f}")
    
    # Test individual components
    print(f"\nComponent analysis:")
    print(f"fuzz.ratio full addresses: {fuzz.ratio(addr1, addr2):.2f}")
    print(f"fuzz.token_set_ratio: {fuzz.token_set_ratio(addr1, addr2):.2f}")
    
    # Test street names only
    street1 = "HENRY ST"
    street2 = "FULLER ST" 
    print(f"Street name similarity: {fuzz.ratio(street1, street2):.2f}")
    print(f"Street token_set_ratio: {fuzz.token_set_ratio(street1, street2):.2f}")

if __name__ == "__main__":
    test_henry_fuller()