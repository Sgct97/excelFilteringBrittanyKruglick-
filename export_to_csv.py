import pandas as pd
import sys

def export_sheets_to_csv():
    """
    Reads the data from the .xlsm file and exports each data sheet to a
    separate CSV file for more reliable processing.
    """
    workbook_path = 'FuzzyMatch_Tool.xlsm'
    print(f"Attempting to read and export data from '{workbook_path}'...")

    try:
        all_sheets_dfs = pd.read_excel(workbook_path, sheet_name=None, engine='openpyxl')
        
        sheet_names = list(all_sheets_dfs.keys())
        data_sheet_names = [name for name in sheet_names if name != 'Match_Results']

        if len(data_sheet_names) < 2:
            print("Error: Could not find two data sheets to convert.")
            return

        # Export the two data sheets to CSV files
        sheet1_name = data_sheet_names[0]
        sheet2_name = data_sheet_names[1]
        
        csv1_path = 'data1.csv'
        csv2_path = 'data2.csv'

        all_sheets_dfs[sheet1_name].to_csv(csv1_path, index=False)
        print(f"Successfully exported '{sheet1_name}' to '{csv1_path}'")
        
        all_sheets_dfs[sheet2_name].to_csv(csv2_path, index=False)
        print(f"Successfully exported '{sheet2_name}' to '{csv2_path}'")
        
        print("\nData extraction complete.")

    except Exception as e:
        print(f"A critical error occurred during file reading: {e}")
        print("This confirms a problem with reading the .xlsm file itself.")

if __name__ == '__main__':
    export_sheets_to_csv() 