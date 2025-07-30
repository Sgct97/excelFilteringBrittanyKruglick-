import pandas as pd
import logging
from rapidfuzz import fuzz
from typing import Tuple, Dict

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """Preprocess DataFrame by filling NaNs and creating FullAddress without altering case or whitespace.

    Args:
        df (pd.DataFrame): Input DataFrame with raw data.

    Returns:
        pd.DataFrame: Preprocessed DataFrame.

    Example:
        >>> df = pd.DataFrame({'First_Name': ['John'], 'Last_Name': ['Doe'], 'Address1': ['123 Main St'], 'City': ['Anytown'], 'State': ['CA'], 'Zip': [12345]})
        >>> processed = preprocess_data(df)
        >>> processed['FullAddress'][0]
        '123 Main St, Anytown, CA 12345'
    """
    df_processed = df.copy()
    columns_to_fill = ['First_Name', 'Last_Name', 'Address1', 'City', 'State', 'Zip']
    for col in columns_to_fill:
        if col in df_processed.columns:
            df_processed[col] = df_processed[col].fillna('').astype(str)
    df_processed['FullAddress'] = (
        df_processed['Address1'] + ', ' +
        df_processed['City'] + ', ' +
        df_processed['State'] + ' ' +
        df_processed['Zip']
    ).str.strip(', ')
    return df_processed

def compute_individual_scores(row1: pd.Series, row2: pd.Series) -> Tuple[float, float, float]:
    """Compute separate fuzzy scores for first name, last name, and full address.

    Args:
        row1, row2 (pd.Series): Rows to compare.

    Returns:
        Tuple[float, float, float]: Scores for first_name, last_name, address.
    """
    first_score = fuzz.token_set_ratio(row1['First_Name'], row2['First_Name'])
    last_score = fuzz.token_set_ratio(row1['Last_Name'], row2['Last_Name'])
    address_score = fuzz.token_set_ratio(row1['FullAddress'], row2['FullAddress'])
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

def run_specific_match(df1: pd.DataFrame, df2: pd.DataFrame, match_type: str, threshold: float = 80.0) -> pd.DataFrame:
    """Find best fuzzy match for each row in df1 from df2 based on match_type.

    Args:
        df1, df2 (pd.DataFrame): Preprocessed DataFrames.
        match_type (str): Type of match.
        threshold (float): Minimum score to consider a match.

    Returns:
        pd.DataFrame: Results sorted by descending score.
    """
    results = []
    for idx1, row1 in df1.iterrows():
        best_score = 0
        best_idx2 = None
        best_row2 = None
        for idx2, row2 in df2.iterrows():
            scores = compute_individual_scores(row1, row2)
            score = get_combined_score(scores, match_type)
            if score > best_score:
                best_score = score
                best_idx2 = idx2
                best_row2 = row2
        if best_score >= threshold:
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