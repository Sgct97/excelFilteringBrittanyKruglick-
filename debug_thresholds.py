#!/usr/bin/env python3
"""Debug street similarity scores to find the right threshold."""

from rapidfuzz import fuzz
import re

def debug_street_similarities():
    """Check similarity scores for different street pairs."""
    
    test_pairs = [
        # Should be CAPPED (different streets)
        ("ALICE ST", "VALERIE ST"),
        ("CHAPMAN DR", "MARION DR"),
        ("HENRY ST", "FULLER ST"),
        
        # Should be PRESERVED (similar streets)
        ("MICHELLE DR", "MICHELE DR"),
        ("MAIN ST", "MAIN STREET"),
        ("HAZELNUT HILL ROAD", "HAZELNUT HILL RD"),
    ]
    
    print("=== Street Similarity Analysis ===\n")
    
    for street1, street2 in test_pairs:
        similarity = fuzz.token_set_ratio(street1, street2)
        print(f"'{street1}' vs '{street2}': {similarity:.2f}%")
    
    print(f"\n=== Threshold Analysis ===")
    print("Current threshold: 80%")
    print("- ALICE ST vs VALERIE ST: 77.78% → CAPPED ✅")
    print("- MAIN ST vs MAIN STREET: ???% → Need to check")
    
    # Check MAIN ST vs MAIN STREET specifically
    main_similarity = fuzz.token_set_ratio("MAIN ST", "MAIN STREET")
    print(f"- MAIN ST vs MAIN STREET: {main_similarity:.2f}%", end="")
    if main_similarity >= 80:
        print(" → PRESERVED ✅")
    else:
        print(" → CAPPED ❌ (needs adjustment)")
    
    print(f"\n=== Recommended Threshold ===")
    # Find threshold that separates good from bad
    scores = [
        (77.78, "ALICE ST vs VALERIE ST", "BAD"),
        (main_similarity, "MAIN ST vs MAIN STREET", "GOOD"),
        (fuzz.token_set_ratio("MICHELLE DR", "MICHELE DR"), "MICHELLE vs MICHELE", "GOOD"),
        (fuzz.token_set_ratio("CHAPMAN DR", "MARION DR"), "CHAPMAN vs MARION", "BAD"),
    ]
    
    for score, desc, category in scores:
        print(f"{score:5.1f}% - {desc} ({category})")
    
    # Suggest threshold
    good_scores = [s for s, d, c in scores if c == "GOOD"]
    bad_scores = [s for s, d, c in scores if c == "BAD"]
    
    if good_scores and bad_scores:
        min_good = min(good_scores)
        max_bad = max(bad_scores)
        suggested = (min_good + max_bad) / 2
        print(f"\nSuggested threshold: {suggested:.1f}% (between {max_bad:.1f}% and {min_good:.1f}%)")

if __name__ == "__main__":
    debug_street_similarities()