#!/usr/bin/env python3
"""Write results to a NEW timestamped Excel file (GUI-equivalent flow).

Usage: ./venv/bin/python3 write_results_new_file.py <workbook.xlsx>
"""

import sys
import os
import datetime
import pandas as pd

from fuzzy_matcher import (
    preprocess_input_variable,
    preprocess_master_with_opens,
    run_specific_match,
    SchemaError,
)


def main() -> int:
    if len(sys.argv) < 2:
        print("Error: Workbook path not provided.")
        return 2

    file_path = sys.argv[1]
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return 2

    # Read all sheets
    all_sheets = pd.read_excel(file_path, sheet_name=None, engine='openpyxl')
    data_sheets = {k: v for k, v in all_sheets.items() if not k.startswith('results_') and not k.startswith('Unmatched_')}
    if len(data_sheets) < 2:
        print("Error: Need at least 2 data sheets to compare")
        return 2

    sheet_names = list(data_sheets.keys())
    s1_df = data_sheets[sheet_names[0]]
    s2_df = data_sheets[sheet_names[1]]

    if len(s1_df) > len(s2_df):
        master_df, input_df = s1_df, s2_df
        master_name, input_name = sheet_names[0], sheet_names[1]
    else:
        master_df, input_df = s2_df, s1_df
        master_name, input_name = sheet_names[1], sheet_names[0]

    print(f"INPUT: {input_name} ({len(input_df)} rows)")
    print(f"MASTER: {master_name} ({len(master_df)} rows)")

    # Preprocess
    try:
        df1, report = preprocess_input_variable(input_df, file=file_path, sheet=input_name)
    except SchemaError as se:
        print(str(se))
        return 2

    df2, opens_missing = preprocess_master_with_opens(master_df)

    # Run matches
    all_types = ['FullName', 'LastNameAddress', 'FullAddress']
    match_types = [mt for mt in all_types if report.get(mt, {}).get('enabled')]
    for mt in all_types:
        if mt not in match_types:
            print(f"Skipping {mt}: {report.get(mt, {}).get('reason')}")

    results = {}
    for mt in match_types:
        results[mt] = run_specific_match(df1, df2, mt)
        print(f"{mt}: {len(results[mt])} matches")

    # Write to new timestamped file
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    out_name = f"{base_name}_RESULTS_{ts}.xlsx"
    out_path = os.path.join(os.path.dirname(file_path), out_name)

    with pd.ExcelWriter(out_path, engine='openpyxl') as writer:
        for sheet_name, df in data_sheets.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            ws = writer.sheets[sheet_name]
            for col in ws.columns:
                max_len = 0
                letter = col[0].column_letter
                for cell in col:
                    try:
                        max_len = max(max_len, len(str(cell.value)))
                    except Exception:
                        pass
                ws.column_dimensions[letter].width = min(max_len + 2, 50)

        for mt, df_res in results.items():
            if df_res.empty:
                continue
            sheet_name = f"results_{mt}"
            df_out = df_res.copy()

            # Append Opens as rightmost
            if 'Opens' in df2.columns:
                opens_map = df2['Opens']
                df_out['Opens'] = df_out['Sheet B Row'].apply(lambda r: opens_map.iloc[int(r) - 2] if 0 <= int(r) - 2 < len(opens_map) else "")
            else:
                df_out['Opens'] = ""  # OPENS_NO_MATCH

            df_out.to_excel(writer, sheet_name=sheet_name, index=False)
            ws = writer.sheets[sheet_name]
            for col in ws.columns:
                max_len = 0
                letter = col[0].column_letter
                for cell in col:
                    try:
                        max_len = max(max_len, len(str(cell.value)))
                    except Exception:
                        pass
                ws.column_dimensions[letter].width = min(max_len + 2, 50)

    print(f"Wrote: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())


