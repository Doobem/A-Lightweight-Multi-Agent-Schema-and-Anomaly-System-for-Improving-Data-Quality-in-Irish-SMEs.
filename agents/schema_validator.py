import pandas as pd
import numpy as np

def validate_schema(df, semantic_schema, profile):
    anomalies = []

    for col in df.columns:
        col_schema = semantic_schema["columns"].get(col, {})
        col_profile = profile.get(col, {})
        series = df[col]

        semantic_type = col_schema.get("type", col_profile.get("type"))

        # 1. Missing required values
        if col_profile["missing"] > 0:
            anomalies.append({
                "row": None,
                "column": col,
                "issue_type": "Schema/MissingValues",
                "description": f"{col} contains {col_profile['missing']} missing values.",
                "severity": "medium",
                "category": "schema"
            })

        # 2. Wrong data type
        if semantic_type == "numeric" and not pd.api.types.is_numeric_dtype(series):
            anomalies.append({
                "row": None,
                "column": col,
                "issue_type": "Schema/InvalidType",
                "description": f"{col} expected numeric but found {series.dtype}.",
                "severity": "high",
                "category": "schema"
            })

        if semantic_type == "date":
            try:
                pd.to_datetime(series, errors="raise")
            except Exception:
                anomalies.append({
                    "row": None,
                    "column": col,
                    "issue_type": "Schema/WrongFormat",
                    "description": f"{col} contains invalid date formats.",
                    "severity": "high",
                    "category": "schema"
                })

        # 3. Out-of-range values (numeric)
        if semantic_type == "numeric":
            min_val = col_profile.get("min")
            max_val = col_profile.get("max")

            if min_val is not None and min_val < 0:
                anomalies.append({
                    "row": None,
                    "column": col,
                    "issue_type": "Schema/OutOfRange",
                    "description": f"{col} contains negative values.",
                    "severity": "medium",
                    "category": "schema"
                })

        # 4. Invalid categories
        if semantic_type == "categorical":
            categories = col_profile.get("categories", [])
            for idx, val in series.items():
                if pd.notna(val) and val not in categories:
                    anomalies.append({
                        "row": idx + 2,  # Excel row
                        "column": col,
                        "issue_type": "Schema/InvalidCategory",
                        "description": f"Unexpected category '{val}' in {col}.",
                        "severity": "medium",
                        "category": "schema"
                    })

        # 5. Duplicate IDs
        if semantic_type == "identifier":
            duplicates = series[series.duplicated()].unique()
            if len(duplicates) > 0:
                anomalies.append({
                    "row": None,
                    "column": col,
                    "issue_type": "Schema/DuplicateIdentifier",
                    "description": f"{col} contains duplicate IDs: {duplicates.tolist()}",
                    "severity": "high",
                    "category": "schema"
                })

    return anomalies
