#!/usr/bin/env python3
"""Test and fix the apartment regex properly."""

import re

def test_patterns():
    """Test different regex patterns to find one that works correctly."""
    
    test_addresses = [
        "268 FLANDERS RD TRLR 9, MYSTIC, CT 6355",      # Should match TRLR 9
        "268 FLANDERS RD LOT 3, MYSTIC, CT 06355",       # Should match LOT 3
        "83 MANSFIELD RD UNIT 329, NEW LONDON, CT 6320", # Should match UNIT 329
        "83 MANSFIELD RD APT 324, NEW LONDON, CT 06320", # Should match APT 324
        "123 MAIN ST FLOOR 2, ANYTOWN, CT 06355",        # Should match FLOOR 2
        "456 OAK AVE, SOMEWHERE, CT 06355",              # Should match nothing
    ]
    
    # Pattern 1: Original (broken)
    pattern1 = r'(?:APT|APARTMENT|UNIT|TRLR|TRAILER|LOT|BLDG|BUILDING|STE|SUITE|FLOOR|FL|RM|ROOM|SPACE|SPC|#)\s*([A-Z0-9]+)'
    
    # Pattern 2: With word boundaries (still broken)
    pattern2 = r'\b(?:APT|APARTMENT|UNIT|TRLR|TRAILER|LOT|BLDG|BUILDING|STE|SUITE|FLOOR|FL|RM|ROOM|SPACE|SPC|#)\s*([A-Z0-9]+)'
    
    # Pattern 3: Must be preceded by space (better)
    pattern3 = r'\s(?:APT|APARTMENT|UNIT|TRLR|TRAILER|LOT|BLDG|BUILDING|STE|SUITE|FLOOR|FL|RM|ROOM|SPACE|SPC|#)\s*([A-Z0-9]+)'
    
    # Pattern 4: Even more specific - space before, then space/number after
    pattern4 = r'\s(APT|APARTMENT|UNIT|TRLR|TRAILER|LOT|BLDG|BUILDING|STE|SUITE|FLOOR|FL|RM|ROOM|SPACE|SPC|#)\s+([A-Z0-9]+)'
    
    patterns = [
        ("Original (broken)", pattern1),
        ("Word boundaries", pattern2),
        ("Space before", pattern3),
        ("Specific format", pattern4)
    ]
    
    for addr in test_addresses:
        print(f"\nTesting: {addr}")
        
        for name, pattern in patterns:
            match = re.search(pattern, addr, re.IGNORECASE)
            if match:
                if len(match.groups()) == 1:
                    print(f"  {name}: Found '{match.group(0)}' -> '{match.group(1)}'")
                else:
                    print(f"  {name}: Found '{match.group(0)}' -> type:'{match.group(1)}' num:'{match.group(2)}'")
            else:
                print(f"  {name}: No match")

if __name__ == "__main__":
    test_patterns()