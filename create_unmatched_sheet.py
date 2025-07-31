#!/usr/bin/env python3
"""Create a new sheet with all unmatched rows from the small input sheet."""

import pandas as pd
import xlwings as xw

def create_unmatched_sheet():
    """Create a sheet with rows from small sheet that didn't match anything."""
    
    try:
        print("🔍 Reading data to find unmatched rows...")
        
        # Read all sheets from the workbook
        all_sheets = pd.read_excel('FuzzyMatch_Tool.xlsm', sheet_name=None, engine='openpyxl')
        
        # Find data sheets (not results)
        data_sheets = {name: df for name, df in all_sheets.items() if not name.startswith('results_')}
        sheet_names = list(data_sheets.keys())
        
        if len(sheet_names) < 2:
            print("❌ Need at least 2 data sheets")
            return
        
        # Auto-detect which is the small input sheet (same logic as before)
        sheet1_raw = data_sheets[sheet_names[0]]
        sheet2_raw = data_sheets[sheet_names[1]]
        
        if len(sheet1_raw) > len(sheet2_raw):
            input_raw = sheet2_raw
            input_sheet_name = sheet_names[1]
            print(f"📝 Input sheet: {input_sheet_name} ({len(input_raw)} rows)")
        else:
            input_raw = sheet1_raw
            input_sheet_name = sheet_names[0]
            print(f"📝 Input sheet: {input_sheet_name} ({len(input_raw)} rows)")
        
        # Find all results sheets
        results_sheets = {name: df for name, df in all_sheets.items() if name.startswith('results_')}
        print(f"📊 Found {len(results_sheets)} results sheets: {list(results_sheets.keys())}")
        
        if not results_sheets:
            print("❌ No results sheets found! Run the matching first.")
            return
        
        # Collect all matched row numbers from all results sheets
        all_matched_rows = set()
        
        for sheet_name, results_df in results_sheets.items():
            if not results_df.empty:
                # Sheet A Row contains the input sheet row numbers (1-based with header)
                matched_rows = set(results_df['Sheet A Row'].tolist())
                all_matched_rows.update(matched_rows)
                print(f"  {sheet_name}: {len(matched_rows)} matched rows")
        
        print(f"📈 Total unique matched rows across all sheets: {len(all_matched_rows)}")
        
        # Convert to 0-based indexing (subtract 2 because Excel rows are 1-based and have header)
        matched_indices = {row - 2 for row in all_matched_rows if row >= 2}
        
        # Find unmatched rows (all input rows except the matched ones)
        total_input_rows = set(range(len(input_raw)))
        unmatched_indices = total_input_rows - matched_indices
        
        print(f"📋 Input rows analysis:")
        print(f"  Total input rows: {len(input_raw)}")
        print(f"  Matched rows: {len(matched_indices)}")
        print(f"  Unmatched rows: {len(unmatched_indices)} ({len(unmatched_indices)/len(input_raw)*100:.1f}%)")
        
        if not unmatched_indices:
            print("✅ All input rows were matched! No unmatched sheet needed.")
            return
        
        # Create DataFrame with unmatched rows
        unmatched_rows = input_raw.iloc[list(unmatched_indices)].copy()
        
        # Add a column showing the original row number for reference
        unmatched_rows['Original_Row_Number'] = [idx + 2 for idx in sorted(unmatched_indices)]  # +2 for Excel 1-based + header
        
        # Reorder columns to put Original_Row_Number first
        cols = ['Original_Row_Number'] + [col for col in unmatched_rows.columns if col != 'Original_Row_Number']
        unmatched_rows = unmatched_rows[cols]
        
        print(f"📝 Created unmatched dataset with {len(unmatched_rows)} rows")
        print(f"   Sample unmatched rows:")
        for i, (idx, row) in enumerate(unmatched_rows.iterrows()):
            if i >= 3:  # Show first 3
                break
            orig_row = row['Original_Row_Number']
            name_cols = [col for col in row.index if 'Name' in col or 'First' in col or 'Last' in col]
            if name_cols:
                name = str(row[name_cols[0]]) if name_cols else "N/A"
            else:
                name = "N/A"
            print(f"     Row {orig_row}: {name}")
        
        # Write to Excel workbook
        print(f"\n💾 Adding 'Unmatched_Rows' sheet to FuzzyMatch_Tool.xlsm...")
        
        with xw.App(visible=False) as app:
            wb = app.books.open('FuzzyMatch_Tool.xlsm')
            
            # Remove existing Unmatched_Rows sheet if it exists
            sheet_name = 'Unmatched_Rows'
            if sheet_name in [s.name for s in wb.sheets]:
                print(f"  Removing existing '{sheet_name}' sheet...")
                wb.sheets[sheet_name].delete()
            
            # Add new sheet
            new_sheet = wb.sheets.add(sheet_name)
            
            # Write data
            new_sheet.range('A1').options(index=False).value = unmatched_rows
            new_sheet.autofit()
            
            # Save
            wb.save()
            print(f"✅ Successfully created '{sheet_name}' sheet with {len(unmatched_rows)} unmatched rows!")
        
        print(f"\n🎯 Next steps:")
        print(f"   1. Open FuzzyMatch_Tool.xlsm")
        print(f"   2. Check the 'Unmatched_Rows' sheet")
        print(f"   3. Manually verify if any of these {len(unmatched_rows)} people should be in the master sheet")
        print(f"   4. The 'Original_Row_Number' column shows where each row came from in {input_sheet_name}")
        
    except Exception as e:
        print(f"❌ Error creating unmatched sheet: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_unmatched_sheet()