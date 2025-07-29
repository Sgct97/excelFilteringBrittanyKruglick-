import pandas as pd

def inspect_excel_file(file_path, file_name):
    """
    Inspects an Excel file, prints its sheet names,
    and the first 5 rows of each sheet.
    """
    try:
        print(f"--- Inspecting: {file_name} ---")
        xls = pd.ExcelFile(file_path)
        sheet_names = xls.sheet_names
        print(f"Sheet names: {sheet_names}")

        for sheet in sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet)
            print(f"\nColumns in '{sheet}' sheet:", df.columns.tolist())
            print(f"First 5 rows of '{sheet}' sheet:")
            print(df.head())
        print("\n" + "="*40 + "\n")

    except Exception as e:
        print(f"An error occurred while inspecting {file_name}: {e}")
        print("\n" + "="*40 + "\n")


if __name__ == "__main__":
    file1_path = 'coloniel hyundai sales_mayjunejuly.xlsx'
    file1_name = 'coloniel hyundai sales_mayjunejuly.xlsx'
    
    file2_path = 'coloniel hyundai sales match_mayjunejuly.xlsx'
    file2_name = 'coloniel hyundai sales match_mayjunejuly.xlsx'

    inspect_excel_file(file1_path, file1_name)
    inspect_excel_file(file2_path, file2_name) 