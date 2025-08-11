import pandas as pd
import xlwings as xw
import sys
from fuzzy_matcher import (
    preprocess_data,
    run_specific_match,
    preprocess_input_variable,
    preprocess_master_with_opens,
    SchemaError,
)

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

        sheet1_raw = all_sheets_dfs[sheet_names[0]]
        sheet2_raw = all_sheets_dfs[sheet_names[1]]
        
        # --- Step 2: Auto-detect which sheet is master vs input based on size ---
        print(f"Found sheet '{sheet_names[0]}': {len(sheet1_raw)} rows")
        print(f"Found sheet '{sheet_names[1]}': {len(sheet2_raw)} rows")
        
        # Larger sheet = master data (search through this)
        # Smaller sheet = input data (find matches for these)
        if len(sheet1_raw) > len(sheet2_raw):
            master_raw = sheet1_raw
            input_raw = sheet2_raw
            master_name = sheet_names[0]
            input_name = sheet_names[1]
        else:
            master_raw = sheet2_raw
            input_raw = sheet1_raw
            master_name = sheet_names[1]
            input_name = sheet_names[0]
            
        print(f"Using {input_name} ({len(input_raw)} rows) as INPUT data")
        print(f"Using {master_name} ({len(master_raw)} rows) as MASTER data")
        
        # --- Step 3: Preprocess data (variable input schema) ---
        print("Preprocessing data (variable input schema)...")
        try:
            df1, report = preprocess_input_variable(input_raw, file=workbook_path, sheet=input_name)
        except SchemaError as se:
            print(str(se))
            return
        df2, opens_missing = preprocess_master_with_opens(master_raw)  # df2 = master (larger)

        # --- Step 4: Choose enabled match types ---
        all_types = ['FullName', 'LastNameAddress', 'FullAddress']
        match_types = [mt for mt in all_types if report.get(mt, {}).get('enabled')]
        for mt in all_types:
            if mt not in match_types:
                reason = report.get(mt, {}).get('reason')
                print(f"Skipping {mt}: {reason}")

        results = {match_type: run_specific_match(df1, df2, match_type) for match_type in match_types}

        # --- Step 5: Write all results back to the workbook ---
        print("\nWriting all results back to the workbook...")
        with xw.App(visible=False) as app:
            wb = app.books.open(workbook_path)
            
            for match_type, results_df in results.items():
                sheet_name = f'results_{match_type}'
                if sheet_name in [s.name for s in wb.sheets]:
                    wb.sheets[sheet_name].clear_contents()
                else:
                    wb.sheets.add(sheet_name)
                
                # Append Opens rightmost
                if 'Opens' in df2.columns:
                    results_df = results_df.copy()
                    opens_map = df2['Opens']
                    results_df['Opens'] = results_df['Sheet B Row'].apply(lambda r: opens_map.iloc[int(r) - 2] if 0 <= int(r) - 2 < len(opens_map) else "")
                else:
                    results_df = results_df.copy()
                    results_df['Opens'] = ""  # OPENS_NO_MATCH

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