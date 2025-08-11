#!/usr/bin/env python3
"""Analyze schema on real workbook and emit a local artifact JSON.

Complies with rules.yaml: uses only real files, fail-fast, deterministic.
"""

import json
import sys
import os
import pandas as pd
from typing import Any, Dict

from schema_detection import detect_schema, evaluate_match_types, SchemaError


def main() -> int:
    workbook = "FuzzyMatch_Tool.xlsm"
    if not os.path.exists(workbook):
        print(json.dumps({
            "code": "DATA_READ_ERROR",
            "stage": "analyze_schema",
            "file": workbook,
            "detail": "Workbook not found",
            "repro": "Place FuzzyMatch_Tool.xlsm in project root"
        }))
        return 2

    try:
        all_sheets = pd.read_excel(workbook, sheet_name=None, engine="openpyxl")
    except Exception as e:
        print(json.dumps({
            "code": "DATA_READ_ERROR",
            "stage": "analyze_schema",
            "file": workbook,
            "detail": str(e),
            "repro": "Ensure file is not open/locked and is a valid Excel file"
        }))
        return 2

    # Identify data sheets (exclude results_* and Unmatched_*)
    data_sheets = {
        name: df for name, df in all_sheets.items()
        if not name.startswith("results_") and not name.startswith("Unmatched_")
    }
    sheet_names = list(data_sheets.keys())
    if len(sheet_names) < 2:
        print(json.dumps({
            "code": "SCHEMA_REQUIRED_MISSING",
            "stage": "analyze_schema",
            "file": workbook,
            "detail": "Need at least two data sheets",
            "repro": "Add two input sheets and retry"
        }))
        return 2

    # Auto-detect master vs input by row count
    s1, s2 = sheet_names[0], sheet_names[1]
    df1, df2 = data_sheets[s1], data_sheets[s2]
    input_name, master_name = (s1, s2) if len(df1) < len(df2) else (s2, s1)
    input_df = data_sheets[input_name]

    # Detect schema on the INPUT sheet only (as per scope)
    try:
        mapping = detect_schema(list(input_df.columns), file=workbook, sheet=input_name)
    except SchemaError as se:
        print(str(se))
        return 2

    report = evaluate_match_types(mapping)

    artifact: Dict[str, Any] = {
        "workbook": workbook,
        "input_sheet": input_name,
        "master_sheet": master_name,
        "columns": list(input_df.columns),
        "mapping": {k: {"canonical": v.canonical, "source": v.source, "derived": v.derived} for k, v in mapping.items()},
        "match_types": report,
    }

    out_path = "schema_artifact.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(artifact, f, indent=2, ensure_ascii=False)
    print(json.dumps({"status": "ok", "artifact": out_path}))
    return 0


if __name__ == "__main__":
    sys.exit(main())


