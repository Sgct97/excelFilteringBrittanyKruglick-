import pandas as pd
import logging
from rapidfuzz import fuzz
from typing import Tuple, Dict

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
            # Same house number - check apartment requirements for FullAddress matching
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

def compute_address_with_apartment_check(addr1: str, addr2: str) -> float:
    """Check apartment numbers for FullAddress matching with strict client requirements."""
    import re
    
    # Extract property designators (comprehensive pattern for apartments, units, trailers, lots, etc.)
    # Must be preceded by space and followed by space+number to avoid matching parts of street names
    apt_pattern = r'\s(APT|APARTMENT|UNIT|TRLR|TRAILER|LOT|BLDG|BUILDING|STE|SUITE|FLOOR|FL|RM|ROOM|SPACE|SPC|#)\s+([A-Z0-9]+)'
    apt1_match = re.search(apt_pattern, addr1, re.IGNORECASE)
    apt2_match = re.search(apt_pattern, addr2, re.IGNORECASE)
    
    # If both have apartment numbers, they must match exactly
    if apt1_match and apt2_match:
        apt1 = apt1_match.group(2).upper()  # group(2) is the number, group(1) is the type
        apt2 = apt2_match.group(2).upper()  # group(2) is the number, group(1) is the type
        
        if apt1 != apt2:
            # Different apartments - client requires no match for FullAddress
            return 0.0
    
    # If only one has apartment number, treat as different addresses
    elif apt1_match or apt2_match:
        return 0.0
    
    # Same apartment or no apartments - use full string comparison
    return fuzz.ratio(addr1, addr2)

def strip_apartment_numbers(address: str) -> str:
    """Remove property designators from address for flexible LastNameAddress matching."""
    import re
    # Remove property designator patterns and everything after them
    # Must be preceded by space and followed by space+number to avoid matching parts of street names
    apt_pattern = r'\s(APT|APARTMENT|UNIT|TRLR|TRAILER|LOT|BLDG|BUILDING|STE|SUITE|FLOOR|FL|RM|ROOM|SPACE|SPC|#)\s+[A-Z0-9]+.*'
    return re.sub(apt_pattern, '', address, flags=re.IGNORECASE).strip().rstrip(',')

def compute_lastname_address_score(row1: pd.Series, row2: pd.Series) -> float:
    """Compute LastNameAddress score with apartment-flexible matching.
    
    Client requirement: For LastNameAddress, match on name + base address,
    ignoring apartment numbers to catch same person who moved units.
    """
    last_score = fuzz.token_set_ratio(row1['Last_Name'], row2['Last_Name'])
    
    # Strip apartment numbers for flexible address matching
    addr1_base = strip_apartment_numbers(row1['FullAddress']) 
    addr2_base = strip_apartment_numbers(row2['FullAddress'])
    address_score = fuzz.token_set_ratio(addr1_base, addr2_base)
    
    # Combine scores (both must be reasonably high)
    return (last_score + address_score) / 2 if last_score > 0 and address_score > 0 else 0

def get_combined_score(scores: Tuple[float, float, float], match_type: str, row1: pd.Series = None, row2: pd.Series = None) -> float:
    """Combine individual scores based on match type.

    Args:
        scores (Tuple[float, float, float]): First, last, address scores.
        match_type (str): 'FullName', 'LastNameAddress', or 'FullAddress'.
        row1, row2 (pd.Series): Optional rows for LastNameAddress apartment-flexible matching.

    Returns:
        float: Combined score.
    """
    first, last, address = scores
    if match_type == 'FullName':
        return (first + last) / 2 if first > 0 and last > 0 else 0
    elif match_type == 'LastNameAddress':
        # Use apartment-flexible scoring for LastNameAddress
        if row1 is not None and row2 is not None:
            return compute_lastname_address_score(row1, row2)
        else:
            return (last + address) / 2 if last > 0 and address > 0 else 0
    elif match_type == 'FullAddress':
        return address
    raise ValueError(f"Unknown match_type: {match_type}")

def run_specific_match(df1: pd.DataFrame, df2: pd.DataFrame, match_type: str, threshold: float = None) -> pd.DataFrame:
    """Find best fuzzy match for each row in df1 from df2 based on match_type.

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
    results = []
    for idx1, row1 in df1.iterrows():
        best_score = 0
        best_idx2 = None
        best_row2 = None
        for idx2, row2 in df2.iterrows():
            scores = compute_individual_scores(row1, row2)
            score = get_combined_score(scores, match_type, row1, row2)
            if score > best_score:
                best_score = score
                best_idx2 = idx2
                best_row2 = row2
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