import xlwings as xw
from fuzzy_matcher import find_matches
import pandas as pd
import sys

def main():
    """
    This function is called from the run.sh script. It takes the workbook
    path as a command-line argument, identifies the two data sheets,
    runs the fuzzy matching, and writes the results to a new sheet.
    """
    if len(sys.argv) < 2:
        # This is a fallback for testing, not used in production
        print("Error: Workbook path not provided.")
        return

    workbook_path = sys.argv[1]

    try:
        # Make Excel visible for debugging
        with xw.App(visible=True) as app:
            wb = app.books.open(workbook_path)

            results_sheet_name = 'Match_Results'
            all_sheet_names = [sheet.name for sheet in wb.sheets]
            data_sheet_names = [name for name in all_sheet_names if name != results_sheet_name]

            if len(data_sheet_names) < 2:
                # In this model, we can't show an alert, but we can handle the error.
                print("Error: Could not find two data sheets to compare.")
                return

            sheet1_name, sheet2_name = data_sheet_names[0], data_sheet_names[1]
            df1 = wb.sheets[sheet1_name].used_range.options(pd.DataFrame, header=True, index=False).value
            df2 = wb.sheets[sheet2_name].used_range.options(pd.DataFrame, header=True, index=False).value
            
            print(f"Matching data from '{sheet1_name}' and '{sheet2_name}'...")
            results_df = find_matches(df1, df2)

            if results_sheet_name in all_sheet_names:
                results_sheet = wb.sheets[results_sheet_name]
                results_sheet.clear_contents()
            else:
                results_sheet = wb.sheets.add(results_sheet_name, after=wb.sheets[-1])
            
            results_sheet.range('A1').options(index=False).value = results_df
            results_sheet.autofit()
            
            print(f"Matching complete! Found {len(results_df)} potential matches.")
            wb.save()
            wb.close()
            
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    main() 