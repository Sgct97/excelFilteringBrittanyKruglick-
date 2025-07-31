#!/usr/bin/env python3
"""Test the street name validation fix."""

from fuzzy_matcher import compute_address_score

def test_street_name_fix():
    """Test that the street name validation fix works correctly."""
    
    print("=== Testing Street Name Validation Fix ===\n")
    
    test_cases = [
        # Should be FIXED (capped at ~65%)
        ("8 ALICE ST, NEW LONDON, CT 06320", "8 VALERIE ST, NEW LONDON, CT 06320", "FIXED", 92.1),
        ("15 CHAPMAN DR, MYSTIC, CT 06355", "15 MARION DR, MYSTIC, CT 06355", "FIXED", 87.9),
        
        # Should PRESERVE high scores (street variations)
        ("20 MICHELLE DR, NEW LONDON, CT 06320", "20 MICHELE DR, NEW LONDON, CT 06320", "PRESERVE", 96.9),
        ("123 MAIN ST, ANYTOWN, CT 06355", "123 MAIN STREET, ANYTOWN, CT 06355", "PRESERVE", None),
        ("429 HAZELNUT HILL ROAD, MYSTIC, CT 06355", "429 HAZELNUT HILL RD, MYSTIC, CT 06355", "PRESERVE", None),
        
        # Completely different (should stay low)
        ("61 HENRY ST, NEW LONDON, CT 06320", "61 FULLER ST, NEW LONDON, CT 06320", "DIFFERENT", None),
    ]
    
    for addr1, addr2, expected, old_score in test_cases:
        new_score = compute_address_score(addr1, addr2)
        
        print(f"Test: {expected}")
        print(f"  Address 1: {addr1}")
        print(f"  Address 2: {addr2}")
        print(f"  New score: {new_score:.2f}%", end="")
        if old_score:
            print(f" (was {old_score:.1f}%)")
        else:
            print()
        
        if expected == "FIXED":
            if new_score <= 65:
                print(f"  ✅ SUCCESS: Score capped at {new_score:.2f}% (was {old_score:.1f}%)")
            else:
                print(f"  ❌ FAILED: Score still too high at {new_score:.2f}%")
        elif expected == "PRESERVE":
            if new_score >= 85:
                print(f"  ✅ SUCCESS: High score preserved at {new_score:.2f}%")
            else:
                print(f"  ❌ FAILED: Score dropped too low to {new_score:.2f}%")
        elif expected == "DIFFERENT":
            if new_score <= 70:
                print(f"  ✅ SUCCESS: Different streets scored low at {new_score:.2f}%")
            else:
                print(f"  ❌ PROBLEM: Different streets still scoring {new_score:.2f}%")
        
        print()

if __name__ == "__main__":
    test_street_name_fix()