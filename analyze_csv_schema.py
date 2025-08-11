#!/usr/bin/env python3
"""Analyze schema on a CSV (small input sheet sample) and emit a local artifact JSON.

Complies with rules.yaml: uses only real files, fail-fast, deterministic.
"""

import json
import sys
import os
import pandas as pd
from typing import Any, Dict

from schema_detection import detect_schema, evaluate_match_types, SchemaError


def main() -> int:
    if len(sys.argv) < 2:
        print(json.dumps({
            "code": "DATA_READ_ERROR",
            "stage": "analyze_csv_schema",
            "file": None,
            "detail": "CSV path arg missing",
            "repro": "Run: analyze_csv_schema.py <csv_path>"
        }))
        return 2

    csv_path = sys.argv[1]
    if not os.path.exists(csv_path):
        print(json.dumps({
            "code": "DATA_READ_ERROR",
            "stage": "analyze_csv_schema",
            "file": csv_path,
            "detail": "CSV not found",
            "repro": "Provide existing CSV path"
        }))
        return 2

    try:
        # Read only headers to avoid large memory, but pandas needs some rows; read minimal
        df = pd.read_csv(csv_path, nrows=1)
    except Exception as e:
        print(json.dumps({
            "code": "DATA_READ_ERROR",
            "stage": "analyze_csv_schema",
            "file": csv_path,
            "detail": str(e),
            "repro": "Ensure valid CSV file"
        }))
        return 2

    try:
        mapping = detect_schema(list(df.columns), file=csv_path, sheet="<csv>")
    except SchemaError as se:
        print(str(se))
        return 2

    report = evaluate_match_types(mapping)

    artifact: Dict[str, Any] = {
        "csv": csv_path,
        "columns": list(df.columns),
        "mapping": {k: {"canonical": v.canonical, "source": v.source, "derived": v.derived} for k, v in mapping.items()},
        "match_types": report,
    }

    out_path = "schema_artifact_small.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(artifact, f, indent=2, ensure_ascii=False)
    print(json.dumps({"status": "ok", "artifact": out_path}))
    return 0


if __name__ == "__main__":
    sys.exit(main())


