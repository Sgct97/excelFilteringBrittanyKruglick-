import pandas as pd
import sys

def verify_files_are_identical():
    """
    Reads two specified CSV files and prints a definitive statement
    on whether they are identical or not.
    """
    file1 = 'coloniel hyundai sales_mayjunejuly.csv'
    file2 = 'coloniel hyundai sales match_mayjunejuly.csv'

    print(f"Reading '{file1}'...")
    try:
        df1 = pd.read_csv(file1)
    except FileNotFoundError:
        print(f"FATAL ERROR: Could not find '{file1}'. Please ensure it is in the correct folder.")
        sys.exit(1)
    except Exception as e:
        print(f"FATAL ERROR: Could not read '{file1}': {e}")
        sys.exit(1)

    print(f"Reading '{file2}'...")
    try:
        df2 = pd.read_csv(file2)
    except FileNotFoundError:
        print(f"FATAL ERROR: Could not find '{file2}'. Please ensure it is in the correct folder.")
        sys.exit(1)
    except Exception as e:
        print(f"FATAL ERROR: Could not read '{file2}': {e}")
        sys.exit(1)

    print("\nComparing the two files...")
    
    # Fill NaN values to allow for accurate comparison, as NaN != NaN
    df1_filled = df1.fillna("NULL_VALUE")
    df2_filled = df2.fillna("NULL_VALUE")

    if df1_filled.equals(df2_filled):
        print("\n----------------------------------------------------")
        print("    FACT: The two CSV files are IDENTICAL.")
        print("    This is the reason for the 100% match scores.")
        print("----------------------------------------------------")
    else:
        print("\n----------------------------------------------------")
        print("    FACT: The two CSV files are DIFFERENT.")
        print("    The matching logic needs to be re-evaluated.")
        print("----------------------------------------------------")
        # Find and print the first differing row for debugging
        diff_mask = df1_filled.ne(df2_filled).any(axis=1)
        first_diff_index = diff_mask.idxmax()
        print("\nFirst difference found at row:", first_diff_index)
        print("--- Data from file 1 ---")
        print(df1.iloc[first_diff_index])
        print("\n--- Data from file 2 ---")
        print(df2.iloc[first_diff_index])


if __name__ == '__main__':
    verify_files_are_identical() 