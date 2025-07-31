#!/usr/bin/env python3
"""Tune cosine similarity parameters for better address matching."""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def cosine_address_score_v2(addr1: str, addr2: str, version="v1") -> float:
    """Test different parameter combinations for cosine similarity."""
    if not addr1 or not addr2:
        return 0.0
    
    # Different parameter combinations to test
    configs = {
        "v1": {  # Original
            "analyzer": "char",
            "ngram_range": (2, 4),
            "max_features": 1000
        },
        "v2": {  # More features, wider ngrams
            "analyzer": "char", 
            "ngram_range": (2, 5),
            "max_features": 2000
        },
        "v3": {  # Word + char hybrid
            "analyzer": "char",
            "ngram_range": (3, 4),
            "max_features": 1500
        },
        "v4": {  # Fine-tuned
            "analyzer": "char",
            "ngram_range": (2, 3),
            "max_features": 1000,
            "sublinear_tf": True  # Apply sublinear tf scaling
        }
    }
    
    config = configs[version]
    vectorizer = TfidfVectorizer(
        lowercase=True,
        **config
    )
    
    try:
        tfidf_matrix = vectorizer.fit_transform([addr1, addr2])
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        return max(0.0, similarity * 100)
    except ValueError:
        return 0.0

def test_parameter_tuning():
    """Test different parameter combinations."""
    
    test_cases = [
        # Bad matches (should be LOW)
        ("61 HENRY ST, NEW LONDON, CT 06320", "61 FULLER ST, NEW LONDON, CT 06320", "BAD"),
        ("268 FLANDERS RD TRLR 9, MYSTIC, CT 6355", "268 FLANDERS RD LOT 3, MYSTIC, CT 06355", "BAD"),
        ("123 MAIN ST, COLCHESTER, CT 06415", "123 MAIN ST, MYSTIC, CT 06355", "BAD"),
        
        # Good matches (should be HIGH)
        ("123 MAIN ST, ANYTOWN, CT 6355", "123 MAIN ST, ANYTOWN, CT 06355-1445", "GOOD"),
        ("456 OAK STREET, SOMEWHERE, CT 06355", "456 OAK ST, SOMEWHERE, CT 06355", "GOOD"),
        ("83 MANSFIELD RD UNIT 329, NEW LONDON, CT 6320", "83 MANSFIELD RD APT 329, NEW LONDON, CT 06320", "GOOD"),
    ]
    
    versions = ["v1", "v2", "v3", "v4"]
    
    print("=== Parameter Tuning Results ===\n")
    
    for addr1, addr2, expected in test_cases:
        print(f"Expected: {expected}")
        print(f"  {addr1}")
        print(f"  {addr2}")
        
        for version in versions:
            score = cosine_address_score_v2(addr1, addr2, version)
            print(f"  {version}: {score:.2f}")
        
        print()

if __name__ == "__main__":
    test_parameter_tuning()