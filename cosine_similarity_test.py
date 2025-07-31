#!/usr/bin/env python3
"""Test cosine similarity approach for address matching."""

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from rapidfuzz import fuzz

def cosine_address_score(addr1: str, addr2: str) -> float:
    """Compute address similarity using TF-IDF + cosine similarity.
    
    Args:
        addr1, addr2 (str): Address strings to compare.
        
    Returns:
        float: Cosine similarity score (0-100).
    """
    if not addr1 or not addr2:
        return 0.0
    
    # Use character n-grams to handle address variations (St/Street, etc.)
    vectorizer = TfidfVectorizer(
        analyzer='char',           # Character-level analysis
        ngram_range=(2, 4),       # 2-4 character n-grams
        lowercase=True,           # Already uppercase from preprocessing
        max_features=1000         # Limit features for performance
    )
    
    try:
        # Create TF-IDF vectors for both addresses
        tfidf_matrix = vectorizer.fit_transform([addr1, addr2])
        
        # Compute cosine similarity
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        
        # Convert to 0-100 scale
        return max(0.0, similarity * 100)
        
    except ValueError:
        # Handle edge case where vectorizer fails
        return 0.0

def cosine_name_score(name1: str, name2: str) -> float:
    """Compute name similarity using TF-IDF + cosine similarity.
    
    Args:
        name1, name2 (str): Name strings to compare.
        
    Returns:
        float: Cosine similarity score (0-100).
    """
    if not name1 or not name2:
        return 0.0
    
    # Use word-level analysis for names
    vectorizer = TfidfVectorizer(
        analyzer='word',          # Word-level for names
        ngram_range=(1, 2),       # 1-2 word n-grams
        lowercase=True
    )
    
    try:
        tfidf_matrix = vectorizer.fit_transform([name1, name2])
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        return max(0.0, similarity * 100)
    except ValueError:
        return 0.0

def test_comparison():
    """Compare cosine similarity vs current rapidfuzz approach."""
    
    test_cases = [
        # Problematic cases that should score LOW
        ("61 HENRY ST, NEW LONDON, CT 06320", "61 FULLER ST, NEW LONDON, CT 06320"),
        ("268 FLANDERS RD TRLR 9, MYSTIC, CT 6355", "268 FLANDERS RD LOT 3, MYSTIC, CT 06355"),
        ("123 MAIN ST, COLCHESTER, CT 06415", "123 MAIN ST, MYSTIC, CT 06355"),
        
        # Good cases that should score HIGH
        ("123 MAIN ST, ANYTOWN, CT 6355", "123 MAIN ST, ANYTOWN, CT 06355-1445"),
        ("456 OAK STREET, SOMEWHERE, CT 06355", "456 OAK ST, SOMEWHERE, CT 06355"),
        ("83 MANSFIELD RD UNIT 329, NEW LONDON, CT 6320", "83 MANSFIELD RD APT 329, NEW LONDON, CT 06320"),
        
        # Edge cases
        ("EAST LYME CT", "MYSTIC CT"),
        ("", "123 MAIN ST"),
    ]
    
    print("=== Cosine Similarity vs RapidFuzz Comparison ===\n")
    
    for i, (addr1, addr2) in enumerate(test_cases, 1):
        print(f"Test Case {i}:")
        print(f"  Address 1: {addr1}")
        print(f"  Address 2: {addr2}")
        
        # Current approach (simplified)
        rapidfuzz_score = fuzz.ratio(addr1, addr2)
        
        # New cosine approach
        cosine_score = cosine_address_score(addr1, addr2)
        
        print(f"  RapidFuzz ratio: {rapidfuzz_score:.2f}")
        print(f"  Cosine similarity: {cosine_score:.2f}")
        
        # Analyze result
        if i <= 3:  # Should be LOW
            print(f"  Expected: LOW score")
            if cosine_score < rapidfuzz_score:
                print(f"  ✅ Cosine is better (lower)")
            else:
                print(f"  ❌ RapidFuzz is better (lower)")
        elif i <= 6:  # Should be HIGH
            print(f"  Expected: HIGH score")
            if cosine_score > rapidfuzz_score:
                print(f"  ✅ Cosine is better (higher)")
            else:
                print(f"  ❌ RapidFuzz is better (higher)")
        
        print()

if __name__ == "__main__":
    test_comparison()