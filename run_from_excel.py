import pandas as pd
import xlwings as xw
import sys
from fuzzy_matcher import preprocess_data, run_specific_match

def main():
    """
    Called from run.sh. Reads data from the Excel workbook, runs all three
    match types, and writes three separate result sheets back to the workbook.
    """
    if len(sys.argv) < 2:
        print("Error: Workbook path not provided.")
        return

    workbook_path = sys.argv[1]

    try:
        # --- Step 1: Read data quickly using pandas ---
        print("Reading data from Excel file...")
        all_sheets_dfs = pd.read_excel(workbook_path, sheet_name=None, engine='openpyxl')
        
        sheet_names = [name for name in all_sheets_dfs.keys() if not name.startswith('results_')]
        if len(sheet_names) < 2:
            print("Error: Could not find two data sheets to compare.")
            return

        df1_raw = all_sheets_dfs[sheet_names[0]]
        df2_raw = all_sheets_dfs[sheet_names[1]]
        
        # --- Step 2: Preprocess data once ---
        print("Preprocessing data...")
        df1 = preprocess_data(df1_raw)
        df2 = preprocess_data(df2_raw)

        # --- Step 3: Run all three match types ---
        match_types = ['FullName', 'LastNameAddress', 'FullAddress']
        results = {match_type: run_specific_match(df1, df2, match_type) for match_type in match_types}

        # --- Step 4: Write all results back to the workbook ---
        print("\nWriting all results back to the workbook...")
        with xw.App(visible=False) as app:
            wb = app.books.open(workbook_path)
            
            for match_type, results_df in results.items():
                sheet_name = f'results_{match_type}'
                if sheet_name in [s.name for s in wb.sheets]:
                    wb.sheets[sheet_name].clear_contents()
                else:
                    wb.sheets.add(sheet_name)
                
                wb.sheets[sheet_name].range('A1').options(index=False).value = results_df
                wb.sheets[sheet_name].autofit()

            wb.save()
            print("Successfully saved all results to the workbook.")
            
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main() 