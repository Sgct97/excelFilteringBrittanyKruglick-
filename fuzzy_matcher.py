import pandas as pd
import logging
from rapidfuzz import fuzz, process
from typing import Tuple, Dict, List, Any, Optional

# Schema detection for variable-format small input sheet (Milestone 3)
from schema_detection import (
    detect_schema,
    evaluate_match_types,
    split_full_name,
    SchemaError,
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """Preprocess DataFrame by mapping column names, filling NaNs, and creating FullAddress without altering case or whitespace.

    Handles variations in column names from different sheets.

    Args:
        df (pd.DataFrame): Input DataFrame with raw data.

    Returns:
        pd.DataFrame: Preprocessed DataFrame with standard columns.
    """
    df_processed = df.copy()

    # Map column names to standard
    column_map = {
        'FirstName': 'First_Name',
        'LastName': 'Last_Name',
        'Address': 'Address1',
        'Zip5': 'Zip'
    }
    df_processed = df_processed.rename(columns=column_map)

    # For master sheet, concatenate Address and Address 2 if present
    if 'Address 2' in df_processed.columns:
        df_processed['Address1'] = df_processed['Address1'].fillna('') + ' ' + df_processed['Address 2'].fillna('').str.strip()
        df_processed = df_processed.drop(columns=['Address 2'], errors='ignore')

    # Standard columns to fill and normalize case for fuzzy matching accuracy
    columns_to_fill = ['First_Name', 'Last_Name', 'Address1', 'City', 'State', 'Zip']
    for col in columns_to_fill:
        if col in df_processed.columns:
            df_processed[col] = df_processed[col].fillna('').astype(str).str.upper().str.strip()
        else:
            raise KeyError(f"Missing required column: {col}")

    # Create FullAddress
    df_processed['FullAddress'] = (
        df_processed['Address1'] + ', ' +
        df_processed['City'] + ', ' +
        df_processed['State'] + ' ' +
        df_processed['Zip']
    ).str.strip(', ')

    # Drop extra columns like MD5, First_Name_CB, etc.
    extra_cols = [col for col in df_processed.columns if col not in columns_to_fill + ['FullAddress']]
    df_processed = df_processed.drop(columns=extra_cols, errors='ignore')

    return df_processed


def preprocess_input_variable(df: pd.DataFrame, *, file: str, sheet: str) -> Tuple[pd.DataFrame, Dict[str, Dict[str, Any]]]:
    """Preprocess variable-format INPUT DataFrame using schema detection.

    Returns standardized DataFrame with columns: First_Name, Last_Name, Address1, City, State, Zip, FullAddress
    and a match type report indicating which match types are enabled.
    Follows fail-fast rules for header ambiguity; skips match types later based on report.
    """
    try:
        mapping = detect_schema(list(df.columns), file=file, sheet=sheet)
    except SchemaError as e:
        # Re-raise to caller to surface in GUI/console
        raise

    report = evaluate_match_types(mapping)

    # Build standardized frame deterministically using only mapped/derivable fields
    std = pd.DataFrame(index=df.index)

    # Names: prefer deriving from FullName when available to ensure consistency
    if "FullName" in mapping and mapping["FullName"].source:
        first_vals: List[str] = []
        last_vals: List[str] = []
        for v in df[mapping["FullName"].source].fillna("").astype(str).tolist():
            f, l = split_full_name(v)
            first_vals.append(f)
            last_vals.append(l)
        std["First_Name"] = first_vals
        std["Last_Name"] = last_vals
    else:
        if "First_Name" in mapping and mapping["First_Name"].source:
            std["First_Name"] = df[mapping["First_Name"].source].fillna("").astype(str)
        else:
            std["First_Name"] = ""
        if "Last_Name" in mapping and mapping["Last_Name"].source:
            std["Last_Name"] = df[mapping["Last_Name"].source].fillna("").astype(str)
        else:
            std["Last_Name"] = ""

    # Address parts
    if "Address1" in mapping and mapping["Address1"].source:
        std["Address1"] = df[mapping["Address1"].source].fillna("").astype(str)
    else:
        std["Address1"] = ""

    if "City" in mapping and mapping["City"].source:
        std["City"] = df[mapping["City"].source].fillna("").astype(str)
    else:
        std["City"] = ""

    if "State" in mapping and mapping["State"].source:
        std["State"] = df[mapping["State"].source].fillna("").astype(str)
    else:
        std["State"] = ""

    if "Zip" in mapping and mapping["Zip"].source:
        std["Zip"] = df[mapping["Zip"].source].fillna("").astype(str)
    else:
        std["Zip"] = ""

    # FullAddress
    if "FullAddress" in mapping and mapping["FullAddress"].source:
        std["FullAddress"] = df[mapping["FullAddress"].source].fillna("").astype(str)
    else:
        # Derive if parts exist
        std["FullAddress"] = (
            std["Address1"].astype(str).fillna("")
            + ", "
            + std["City"].astype(str).fillna("")
            + ", "
            + std["State"].astype(str).fillna("")
            + " "
            + std["Zip"].astype(str).fillna("")
        ).str.strip(", ")

    # Normalize to uppercase/trim to match existing matcher expectations
    for col in ["First_Name", "Last_Name", "Address1", "City", "State", "Zip", "FullAddress"]:
        std[col] = std[col].fillna("").astype(str).str.upper().str.strip()

    return std, report


def _normalize_header_simple(header: str) -> str:
    import re as _re
    return _re.sub(r"[^a-z0-9]", "", str(header).strip().lower())


def _detect_opens_header(columns: List[str]) -> Optional[str]:
    """Find an opens-like column by header variants (case/punct insensitive)."""
    variants = [
        "opens",
        "open",
        "opened",
        "opening",
        "opens?",
    ]
    targets = {_normalize_header_simple(v) for v in variants}
    for col in columns:
        if _normalize_header_simple(col) in targets:
            return col
    return None


def preprocess_master_with_opens(df_master_raw: pd.DataFrame) -> Tuple[pd.DataFrame, bool]:
    """Preprocess master sheet and attach standardized 'Opens' column if present.

    Returns (df_master_processed, opens_missing_flag).
    - 'Opens' values standardized to 'x' or '' (blank). Only 'x'/'X' counts.
    - If no opens column found, opens_missing_flag=True and 'Opens' is not added.
    """
    # Detect opens before dropping extra columns
    opens_col = _detect_opens_header(list(df_master_raw.columns))

    # Run normal preprocessing first
    df2 = preprocess_data(df_master_raw)

    if opens_col is None:
        return df2, True

    # Map opens to 'x' or '' aligned by original index
    raw_series = df_master_raw[opens_col]
    normalized = raw_series.astype(str).fillna("").str.strip().str.lower().apply(lambda v: "x" if v == "x" else "")

    # Align to df2 by index (preprocess_data preserves index)
    df2 = df2.copy()
    df2["Opens"] = normalized.reindex(df2.index).fillna("")
    return df2, False

def compute_address_score(addr1: str, addr2: str) -> float:
    """Compute address similarity score that properly handles house numbers.
    
    For addresses, house numbers are critical - different numbers = different properties.
    
    Args:
        addr1, addr2 (str): Address strings to compare.
        
    Returns:
        float: Address similarity score (0-100).
    """
    import re
    
    # Extract house numbers (first number sequence in each address)
    num1_match = re.search(r'^\d+', addr1.strip())
    num2_match = re.search(r'^\d+', addr2.strip())
    
    if num1_match and num2_match:
        num1 = int(num1_match.group())
        num2 = int(num2_match.group())
        
        # If house numbers are very different, heavily penalize the score
        num_diff = abs(num1 - num2)
        if num_diff == 0:
            # Same house number - check property designators (APT, UNIT, TRLR, LOT, etc.)
            return compute_address_with_apartment_check(addr1, addr2)
        elif num_diff <= 2:
            # Very close house numbers (might be adjacent properties) - moderate score
            base_score = fuzz.token_set_ratio(addr1, addr2)
            return min(base_score * 0.8, 85.0)  # Cap at 85% for different house numbers
        elif num_diff <= 10:
            # Nearby house numbers - low score  
            return min(fuzz.token_set_ratio(addr1, addr2) * 0.5, 60.0)
        else:
            # Very different house numbers - very low score
            return min(fuzz.token_set_ratio(addr1, addr2) * 0.2, 30.0)
    else:
        # No house numbers found - fall back to standard fuzzy matching
        return fuzz.token_set_ratio(addr1, addr2)

def compute_address_with_apartment_check(addr1: str, addr2: str) -> float:
    """Check property designators for FullAddress matching with strict client requirements."""
    import re
    
    # Extract property designators (comprehensive pattern for apartments, units, trailers, lots, etc.)
    # Must be preceded by space and followed by space+number to avoid matching parts of street names
    apt_pattern = r'\s(APT|APARTMENT|UNIT|TRLR|TRAILER|LOT|BLDG|BUILDING|STE|SUITE|FLOOR|FL|RM|ROOM|SPACE|SPC|#)\s+([A-Z0-9]+)'
    apt1_match = re.search(apt_pattern, addr1, re.IGNORECASE)
    apt2_match = re.search(apt_pattern, addr2, re.IGNORECASE)
    
    # If both have property designators, they must match exactly
    if apt1_match and apt2_match:
        type1 = apt1_match.group(1).upper()  # Property type (APT, UNIT, TRLR, LOT, etc.)
        num1 = apt1_match.group(2).upper()   # Property number/identifier
        type2 = apt2_match.group(1).upper()
        num2 = apt2_match.group(2).upper()
        
        # Different property types (TRLR vs LOT) or different numbers = no match
        if type1 != type2 or num1 != num2:
            return 0.0
    
    # If only one has property designator, treat as different addresses
    elif apt1_match or apt2_match:
        return 0.0
    
    # Same property designator or no designators - validate street names first
    # Extract street names to check if they're actually similar
    import re
    
    # Extract street names (between house number and first comma)
    street1 = re.sub(r'^\d+\s*', '', addr1.strip()).split(',')[0].strip()
    street2 = re.sub(r'^\d+\s*', '', addr2.strip()).split(',')[0].strip()
    
    # Check if street names are similar with smart abbreviation handling
    from rapidfuzz import fuzz
    
    # First normalize common street abbreviations
    def normalize_street(street):
        return (street.replace(' STREET', ' ST')
                     .replace(' ROAD', ' RD') 
                     .replace(' AVENUE', ' AVE')
                     .replace(' LANE', ' LN')
                     .replace(' DRIVE', ' DR')
                     .replace(' COURT', ' CT')
                     .replace(' PLACE', ' PL'))
    
    norm_street1 = normalize_street(street1)
    norm_street2 = normalize_street(street2)
    
    # Check similarity after normalization
    street_similarity = fuzz.token_set_ratio(norm_street1, norm_street2)
    
    # If streets are very different after normalization, cap the score
    if street_similarity < 78:  # Just below the ALICE/VALERIE score (77.78%)
        return min(fuzz.ratio(addr1, addr2) * 0.7, 65.0)  # Cap at 65% for different streets
    
    # Streets are similar - use full string comparison
    return fuzz.ratio(addr1, addr2)

def compute_individual_scores(row1: pd.Series, row2: pd.Series) -> Tuple[float, float, float]:
    """Compute fuzzy scores for first name, last name, and full address.

    Args:
        row1, row2 (pd.Series): Rows to compare.

    Returns:
        Tuple[float, float, float]: Scores for first_name, last_name, address.
    """
    first_score = fuzz.token_set_ratio(row1['First_Name'], row2['First_Name'])
    last_score = fuzz.token_set_ratio(row1['Last_Name'], row2['Last_Name'])
    address_score = compute_address_score(row1['FullAddress'], row2['FullAddress'])
    return first_score, last_score, address_score

def get_combined_score(scores: Tuple[float, float, float], match_type: str) -> float:
    """Combine individual scores based on match type.

    Args:
        scores (Tuple[float, float, float]): First, last, address scores.
        match_type (str): 'FullName', 'LastNameAddress', or 'FullAddress'.

    Returns:
        float: Combined score.
    """
    first, last, address = scores
    if match_type == 'FullName':
        return (first + last) / 2 if first > 0 and last > 0 else 0
    elif match_type == 'LastNameAddress':
        return (last + address) / 2 if last > 0 and address > 0 else 0
    elif match_type == 'FullAddress':
        return address
    raise ValueError(f"Unknown match_type: {match_type}")

def create_search_string(row: pd.Series, match_type: str) -> str:
    """Create search string based on match type for process.extractOne.
    
    Args:
        row (pd.Series): Row to create search string from.
        match_type (str): Type of match to optimize for.
        
    Returns:
        str: Optimized search string.
    """
    if match_type == 'FullName':
        return f"{row['First_Name']} {row['Last_Name']}".strip()
    elif match_type == 'LastNameAddress':
        return f"{row['Last_Name']} {row['FullAddress']}".strip()
    elif match_type == 'FullAddress':
        return row['FullAddress']
    raise ValueError(f"Unknown match_type: {match_type}")



def run_specific_match(df1: pd.DataFrame, df2: pd.DataFrame, match_type: str, threshold: float = None) -> pd.DataFrame:
    """Find best fuzzy match for each row in df1 from df2 using optimized approach.

    Args:
        df1, df2 (pd.DataFrame): Preprocessed DataFrames.
        match_type (str): Type of match ('FullName', 'LastNameAddress', 'FullAddress').
        threshold (float): Optional minimum score. If None, uses smart defaults by match type.

    Returns:
        pd.DataFrame: Results sorted by descending score.
    """
    # Set appropriate threshold by match type if not provided
    if threshold is None:
        thresholds = {
            'FullName': 85.0,        # High threshold - we want actual name matches
            'LastNameAddress': 75.0, # Medium threshold - addresses can vary
            'FullAddress': 80.0      # High threshold - we want actual address matches, not geographic area
        }
        threshold = thresholds.get(match_type, 80.0)
    
    logging.info(f"Processing {len(df1)} rows against {len(df2)} master records for {match_type}...")
    
    # Pre-compute search strings ONCE (not for every input row!)
    logging.info("Pre-computing search strings for master data...")
    df2_list = list(df2.iterrows())  # [(actual_idx, row), ...]
    search_strings = [create_search_string(row2, match_type) for actual_idx, row2 in df2_list]
    logging.info(f"Pre-computed {len(search_strings)} search strings.")
    
    results = []
    for idx1, row1 in df1.iterrows():
        if (idx1 + 1) % 100 == 0:  # Progress logging
            logging.info(f"Processed {idx1 + 1}/{len(df1)} rows...")
            
        best_score = 0
        best_idx2 = None
        best_row2 = None
        
        # Use process.extract for initial filtering, then verify with our custom logic
        query_str = create_search_string(row1, match_type)
        
        # Get top candidates using process.extract (much faster than nested loop)
        candidates = process.extract(
            query_str,
            search_strings,
            scorer=fuzz.token_set_ratio,
            limit=10  # Get top 10 candidates for verification
        )
        
        # Verify candidates with our sophisticated scoring logic
        for candidate_str, candidate_score, list_position in candidates:
            if candidate_score < threshold * 0.8:  # Skip obviously poor matches
                break
            
            # Get the actual DataFrame row using the correct mapping
            actual_df_idx, row2 = df2_list[list_position]
            
            # Use our sophisticated scoring logic
            scores = compute_individual_scores(row1, row2)
            accurate_score = get_combined_score(scores, match_type)
            
            if accurate_score > best_score:
                best_score = accurate_score
                best_idx2 = actual_df_idx  # Use the actual DataFrame index
                best_row2 = row2
        
        # Add result if above threshold
        if best_score >= threshold and best_row2 is not None:
            name_a = f"{row1['First_Name']} {row1['Last_Name']}".strip()
            name_b = f"{best_row2['First_Name']} {best_row2['Last_Name']}".strip()
            results.append({
                'Match Score': round(best_score, 2),
                'Sheet A Row': idx1 + 2,  # Assuming 1-based indexing with header
                'Sheet B Row': best_idx2 + 2,
                'Name A': name_a,
                'Name B': name_b,
                'Address A': row1['FullAddress'],
                'Address B': best_row2['FullAddress']
            })
    
    results_df = pd.DataFrame(results)
    if not results_df.empty:
        results_df = results_df.sort_values(by='Match Score', ascending=False)
    logging.info(f"Found {len(results_df)} matches for {match_type} above threshold {threshold}.")
    return results_df 