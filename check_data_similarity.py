import pandas as pd

def check_differences():
    """
    Checks for differences between the Data1 and Data2 sheets in the workbook
    by reading the file directly with pandas for speed and reliability.
    """
    workbook_path = 'FuzzyMatch_Tool.xlsm'
    
    print(f"Directly reading '{workbook_path}' to check for data differences...")
    
    try:
        all_sheets_dfs = pd.read_excel(workbook_path, sheet_name=None, engine='openpyxl')
        
        sheet_names = list(all_sheets_dfs.keys())
        data_sheet_names = [name for name in sheet_names if name != 'Match_Results']

        if len(data_sheet_names) < 2:
            print(f"Error: Could not find two data sheets to compare.")
            return

        sheet1_name = data_sheet_names[0]
        sheet2_name = data_sheet_names[1]
        df1 = all_sheets_dfs[sheet1_name]
        df2 = all_sheets_dfs[sheet2_name]
        
        print(f"'{sheet1_name}' has {len(df1)} rows.")
        print(f"'{sheet2_name}' has {len(df2)} rows.")
        
        df1_filled = df1.fillna("NULL")
        df2_filled = df2.fillna("NULL")

        if df1_filled.equals(df2_filled):
            print("\\n----------------------------------------")
            print("DIAGNOSIS: The two data sheets are IDENTICAL.")
            print("This is the reason for the 100% match scores.")
            print("Please ensure you use two different datasets.")
            print("----------------------------------------")
        else:
            print("\\n----------------------------------------")
            print("DIAGNOSIS: The two data sheets are DIFFERENT.")
            print("The issue is likely with the match sensitivity, not the data.")
            print("----------------------------------------")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    check_differences() 