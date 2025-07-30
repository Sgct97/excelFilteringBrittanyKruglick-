#!/usr/bin/env python3
"""Debug the specific address examples from user's images."""

from fuzzy_matcher import compute_address_score, compute_address_with_apartment_check

def test_user_examples():
    """Test the specific problematic examples from the user's images."""
    print("=== Testing User's Problematic Examples ===")
    
    # From the images - these pairs should NOT match well but are getting high scores
    problematic_pairs = [
        # Example 1: Different cities - should score low but might be scoring high
        ("123 MAIN ST, COLCHESTER, CT 06415", "123 MAIN ST, MYSTIC, CT 06355"),
        
        # Example 2: Different street names but same city - should score low  
        ("15 OAK ST, MYSTIC, CT 06355", "25 PINE AVE, MYSTIC, CT 06355"),
        
        # Example 3: Very different addresses - should score very low
        ("EAST LYME CT", "MYSTIC CT"),
    ]
    
    # These pairs SHOULD match well but might be scoring low
    good_pairs = [
        # Zip code format differences - should score high (90+)
        ("123 MAIN ST, ANYTOWN, CT 6355", "123 MAIN ST, ANYTOWN, CT 06355-1445"),
        ("456 OAK ST, SOMEWHERE, CT 06355", "456 OAK ST, SOMEWHERE, CT 6355"),
    ]
    
    print("\n--- Problematic Pairs (should score LOW but might score HIGH) ---")
    for i, (addr1, addr2) in enumerate(problematic_pairs, 1):
        score = compute_address_score(addr1, addr2)
        print(f"\nExample {i}:")
        print(f"  Address 1: {addr1}")
        print(f"  Address 2: {addr2}")
        print(f"  Score: {score:.2f} (should be LOW)")
        
        if score > 60:  # If scoring too high
            print(f"  ❌ PROBLEM: Scoring too high! Should be much lower.")
        else:
            print(f"  ✅ OK: Score is appropriately low.")
    
    print("\n--- Good Pairs (should score HIGH but might score LOW) ---")
    for i, (addr1, addr2) in enumerate(good_pairs, 1):
        score = compute_address_score(addr1, addr2)
        print(f"\nExample {i}:")
        print(f"  Address 1: {addr1}")
        print(f"  Address 2: {addr2}")
        print(f"  Score: {score:.2f} (should be HIGH)")
        
        if score < 85:  # If scoring too low
            print(f"  ❌ PROBLEM: Scoring too low! Should be 90+.")
        else:
            print(f"  ✅ OK: Score is appropriately high.")

if __name__ == "__main__":
    test_user_examples()