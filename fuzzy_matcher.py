import pandas as pd
from rapidfuzz import process, fuzz

def preprocess_data(df):
    """
    Prepares the DataFrame for matching by creating FullName and FullAddress columns.
    """
    # Combine first and last names, handling potential missing values
    df['FullName'] = df['First_Name'].fillna('') + ' ' + df['Last_Name'].fillna('')
    
    # Combine address parts, handling potential missing values
    df['FullAddress'] = df['Address1'].fillna('') + ', ' + \
                        df['City'].fillna('') + ', ' + \
                        df['State'].fillna('') + ' ' + \
                        df['Zip'].astype(str).fillna('')
    
    # Clean up and standardize the combined fields
    df['FullName'] = df['FullName'].str.lower().str.strip()
    df['FullAddress'] = df['FullAddress'].str.lower().str.strip()
    
    return df

def find_matches(df1, df2):
    """
    Finds fuzzy matches between two DataFrames.
    
    Args:
        df1 (pd.DataFrame): The first DataFrame.
        df2 (pd.DataFrame): The second DataFrame.
        
    Returns:
        pd.DataFrame: A DataFrame containing the match results.
    """
    df1 = preprocess_data(df1.copy())
    df2 = preprocess_data(df2.copy())

    results = []
    name_choices = df2['FullName'].tolist()
    address_choices = df2['FullAddress'].tolist()
    total_rows = len(df1)

    for index, row in df1.iterrows():
        # Print progress indicator every 25 rows
        if (index + 1) % 25 == 0:
            print(f"  ...processing row {index + 1} of {total_rows}")

        name_match = process.extractOne(row['FullName'], name_choices, scorer=fuzz.token_sort_ratio)
        address_match = process.extractOne(row['FullAddress'], address_choices, scorer=fuzz.token_sort_ratio)

        if name_match and address_match:
            combined_score = (name_match[1] + address_match[1]) / 2
            
            if combined_score > 75:
                match_row_df2 = df2.iloc[name_match[2]]
                results.append({
                    'Match Score': combined_score,
                    'Data1_Row': index + 2, # +2 to account for header and 0-indexing
                    'Data2_Row': name_match[2] + 2,
                    'Name_Data1': row['FullName'],
                    'Name_Data2': name_match[0],
                    'Address_Data1': row['FullAddress'],
                    'Address_Data2': address_match[0],
                })
    
    results_df = pd.DataFrame(results)
    if not results_df.empty:
        results_df = results_df.sort_values(by='Match Score', ascending=False)
        
    return results_df 