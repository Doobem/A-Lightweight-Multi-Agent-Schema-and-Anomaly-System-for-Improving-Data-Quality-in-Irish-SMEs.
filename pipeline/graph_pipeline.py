from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Any, Dict
import pandas as pd

# -------------------------
# PIPELINE STATE
# -------------------------
class PipelineState(TypedDict):
    df: pd.DataFrame
    generated_anomalies: List[Dict[str, Any]]
    schema_results: Dict[str, Any]
    semantic_schema: Dict[str, Any]
    done: bool

# -------------------------
# SAFE DATETIME PARSE (optional)
# -------------------------
def safe_parse_datetime(value):
    try:
        return pd.to_datetime(value)
    except Exception:
        return None

# -------------------------
# SCHEMA AGENT + PROFILER
# -------------------------
from agents.semantic_agent import semantic_align
from agents.schema_profiler import profile_schema

# -------------------------
# SCHEMA VALIDATOR
# -------------------------
def validate_schema(df: pd.DataFrame, semantic_schema: Dict[str, Any], profile: Dict[str, Any]):
    anomalies: List[Dict[str, Any]] = []

    for col in df.columns:
        col_schema = semantic_schema["columns"].get(col, {})
        col_profile = profile.get(col, {})
        series = df[col]

        semantic_type = col_schema.get("type", col_profile.get("type"))

        # 1. Missing values
        if col_profile.get("missing", 0) > 0:
            anomalies.append({
                "RowIndex": None,
                "Column": col,
                "IssueType": "Schema/MissingValues",
                "Description": f"{col} contains {col_profile['missing']} missing values.",
                "Severity": "Medium",
                "Category": "Schema"
            })

        # 2. Wrong data type
        if semantic_type == "numeric" and not pd.api.types.is_numeric_dtype(series):
            anomalies.append({
                "RowIndex": None,
                "Column": col,
                "IssueType": "Schema/InvalidType",
                "Description": f"{col} expected numeric but found {series.dtype}.",
                "Severity": "High",
                "Category": "Schema"
            })

        # 3. Date format
        if semantic_type == "date":
            try:
                pd.to_datetime(series, errors="raise")
            except Exception:
                anomalies.append({
                    "RowIndex": None,
                    "Column": col,
                    "IssueType": "Schema/WrongFormat",
                    "Description": f"{col} contains invalid date formats.",
                    "Severity": "High",
                    "Category": "Schema"
                })

        # 4. Invalid categories
        if semantic_type == "categorical":
            categories = col_profile.get("categories", [])
            for idx, val in series.items():
                if pd.notna(val) and categories and val not in categories:
                    anomalies.append({
                        "RowIndex": idx + 2,
                        "Column": col,
                        "IssueType": "Schema/InvalidCategory",
                        "Description": f"Unexpected category '{val}' in {col}.",
                        "Severity": "Medium",
                        "Category": "Schema"
                    })

        # 5. Duplicate identifiers
        if semantic_type == "identifier":
            duplicates = series[series.duplicated()].unique()
            if len(duplicates) > 0:
                anomalies.append({
                    "RowIndex": None,
                    "Column": col,
                    "IssueType": "Schema/DuplicateIdentifier",
                    "Description": f"{col} contains duplicate IDs: {duplicates.tolist()}",
                    "Severity": "High",
                    "Category": "Schema"
                })

    return anomalies

# -------------------------
# SCHEMA NODE
# -------------------------
def schema_node(state: PipelineState):
    df = state["df"]
    anomalies = state.get("generated_anomalies", [])

    # 1. Semantic schema
    semantic_schema = semantic_align(list(df.columns))

    # UNIVERSAL NORMALIZATION
    if isinstance(semantic_schema, list):
        merged = {}
        for item in semantic_schema:
            if isinstance(item, dict):
                merged.update(item)
        semantic_schema = merged

    if "columns" not in semantic_schema:
        columns_dict = {}
        for key, val in semantic_schema.items():
            if isinstance(val, dict):
                columns_dict[key] = val
        semantic_schema["columns"] = columns_dict

    if isinstance(semantic_schema["columns"], list):
        normalized_cols = {}
        for item in semantic_schema["columns"]:
            if isinstance(item, dict):
                normalized_cols.update(item)
        semantic_schema["columns"] = normalized_cols

    state["semantic_schema"] = semantic_schema

    # 2. Profile schema
    profile = profile_schema(
        df,
        semantic_labels={col: semantic_schema["columns"].get(col, {})
                         for col in df.columns}
    )
    state["schema_results"] = profile

    # 3. Validate schema
    schema_anomalies = validate_schema(df, semantic_schema, profile)
    anomalies.extend(schema_anomalies)

    return {
        "df": df,
        "generated_anomalies": anomalies,
        "schema_results": profile,
        "semantic_schema": semantic_schema,
        "done": False
    }

# -------------------------
# ANOMALY GENERATOR (UPGRADED)
# -------------------------
def anomaly_generator_node(state: PipelineState):
    import math

    df = state["df"]
    anomalies = state.get("generated_anomalies", [])
    profile = state["schema_results"]
    semantic_schema = state["semantic_schema"]

    for col in df.columns:
        col_meta = semantic_schema["columns"].get(col, {})
        col_type = col_meta.get("type", profile[col].get("type"))
        series = df[col]

        # 1. Missing values (row-level)
        for idx, val in series.items():
            if pd.isna(val) or val == "":
                anomalies.append({
                    "RowIndex": idx + 2,
                    "Column": col,
                    "IssueType": "Anomaly/Missing",
                    "Description": f"Missing value in {col}",
                    "Severity": "Medium",
                    "Category": "Anomaly"
                })

        # 2. Numeric outliers, negative, zero
        if col_type == "numeric":
            numeric_series = pd.to_numeric(series, errors="coerce")
            mean = numeric_series.mean()
            std = numeric_series.std()

            # Outliers (3σ)
            if std and std > 0:
                for idx, val in numeric_series.items():
                    if pd.notna(val) and abs(val - mean) > 3 * std:
                        anomalies.append({
                            "RowIndex": idx + 2,
                            "Column": col,
                            "IssueType": "Anomaly/Outlier",
                            "Description": f"Outlier in {col}: {val}",
                            "Severity": "Medium",
                            "Category": "Anomaly"
                        })

            # Negative values
            for idx, val in numeric_series.items():
                if pd.notna(val) and val < 0:
                    anomalies.append({
                        "RowIndex": idx + 2,
                        "Column": col,
                        "IssueType": "Anomaly/NegativeValue",
                        "Description": f"Negative value {val} in {col}",
                        "Severity": "High",
                        "Category": "Anomaly"
                    })

            # Suspicious zeros
            if col_meta.get("label", "").lower() not in ["id", "identifier"]:
                for idx, val in numeric_series.items():
                    if pd.notna(val) and val == 0:
                        anomalies.append({
                            "RowIndex": idx + 2,
                            "Column": col,
                            "IssueType": "Anomaly/SuspiciousZero",
                            "Description": f"Suspicious zero in {col}",
                            "Severity": "Low",
                            "Category": "Anomaly"
                        })

        # 3. Rare & invalid categories
        if col_type == "categorical":
            counts = series.value_counts(dropna=True)
            threshold = max(1, len(df) * 0.01)

            # Rare categories
            for cat, count in counts.items():
                if count < threshold:
                    for idx, val in series.items():
                        if val == cat:
                            anomalies.append({
                                "RowIndex": idx + 2,
                                "Column": col,
                                "IssueType": "Anomaly/RareCategory",
                                "Description": f"Rare category '{cat}' in {col}",
                                "Severity": "Low",
                                "Category": "Anomaly"
                            })

            # Invalid categories vs profile
            valid_categories = profile[col].get("categories", [])
            if valid_categories:
                for idx, val in series.items():
                    if pd.notna(val) and val not in valid_categories:
                        anomalies.append({
                            "RowIndex": idx + 2,
                            "Column": col,
                            "IssueType": "Anomaly/InvalidCategory",
                            "Description": f"Unexpected category '{val}' in {col}",
                            "Severity": "Medium",
                            "Category": "Anomaly"
                        })

        # 4. Mixed types in text/categorical
        if col_type in ["text", "categorical"]:
            numeric_like = series.dropna().apply(
                lambda x: isinstance(x, (int, float)) or
                          (isinstance(x, str) and x.replace('.', '', 1).isdigit())
            )
            if numeric_like.any():
                for idx, is_num in numeric_like.items():
                    if is_num:
                        anomalies.append({
                            "RowIndex": idx + 2,
                            "Column": col,
                            "IssueType": "Anomaly/MixedType",
                            "Description": f"Numeric-like value '{series[idx]}' in text column {col}",
                            "Severity": "Medium",
                            "Category": "Anomaly"
                        })

        # 5. Very long / very short text
        if col_type in ["text", "categorical"]:
            lengths = series.dropna().astype(str).str.len()
            if not lengths.empty:
                q1, q3 = lengths.quantile([0.25, 0.75])
                iqr = q3 - q1
                upper = q3 + 3 * iqr
                lower = max(0, q1 - 3 * iqr)

                for idx, val in series.items():
                    if pd.isna(val):
                        continue
                    l = len(str(val))
                    if l > upper:
                        anomalies.append({
                            "RowIndex": idx + 2,
                            "Column": col,
                            "IssueType": "Anomaly/VeryLongText",
                            "Description": f"Very long text in {col}: '{str(val)[:50]}...'",
                            "Severity": "Low",
                            "Category": "Anomaly"
                        })
                    elif l < lower:
                        anomalies.append({
                            "RowIndex": idx + 2,
                            "Column": col,
                            "IssueType": "Anomaly/VeryShortText",
                            "Description": f"Very short text in {col}: '{val}'",
                            "Severity": "Low",
                            "Category": "Anomaly"
                        })

        # 6. Duplicate identifiers
        if col_type == "identifier":
            dup_mask = series.duplicated(keep=False)
            for idx, is_dup in dup_mask.items():
                if is_dup:
                    anomalies.append({
                        "RowIndex": idx + 2,
                        "Column": col,
                        "IssueType": "Anomaly/DuplicateIdentifier",
                        "Description": f"Duplicate identifier '{series[idx]}' in {col}",
                        "Severity": "High",
                        "Category": "Anomaly"
                    })

        # 7. Date anomalies
        if col_type == "date":
            dates = pd.to_datetime(series, errors="coerce")
            now = pd.Timestamp.now()

            for idx, d in dates.items():
                if pd.isna(d):
                    continue
                if d > now:
                    anomalies.append({
                        "RowIndex": idx + 2,
                        "Column": col,
                        "IssueType": "Anomaly/FutureDate",
                        "Description": f"Future date {d} in {col}",
                        "Severity": "Medium",
                        "Category": "Anomaly"
                    })
                if d.year < 1970:
                    anomalies.append({
                        "RowIndex": idx + 2,
                        "Column": col,
                        "IssueType": "Anomaly/SuspiciousOldDate",
                        "Description": f"Suspicious old date {d} in {col}",
                        "Severity": "Low",
                        "Category": "Anomaly"
                    })

    # 8. Duplicate rows
    dup_rows = df.duplicated(keep=False)
    for idx, is_dup in dup_rows.items():
        if is_dup:
            anomalies.append({
                "RowIndex": idx + 2,
                "Column": None,
                "IssueType": "Anomaly/DuplicateRow",
                "Description": f"Duplicate row at index {idx}",
                "Severity": "Medium",
                "Category": "Anomaly"
            })

    # 9. Simple logical contradictions (example: Quantity vs UnitPrice)
    if set(["Quantity", "UnitPrice"]).issubset(df.columns):
        qty = pd.to_numeric(df["Quantity"], errors="coerce")
        price = pd.to_numeric(df["UnitPrice"], errors="coerce")
        for idx, (q, p) in enumerate(zip(qty, price)):
            if pd.notna(q) and pd.notna(p):
                if q == 0 and p > 0:
                    anomalies.append({
                        "RowIndex": idx + 2,
                        "Column": "Quantity",
                        "IssueType": "Anomaly/Logical",
                        "Description": f"Quantity=0 but UnitPrice={p}",
                        "Severity": "High",
                        "Category": "Anomaly"
                    })
                if q < 0 and p > 0:
                    anomalies.append({
                        "RowIndex": idx + 2,
                        "Column": "Quantity",
                        "IssueType": "Anomaly/Logical",
                        "Description": f"Negative Quantity={q} with UnitPrice={p}",
                        "Severity": "High",
                        "Category": "Anomaly"
                    })

    return {
        "df": df,
        "generated_anomalies": anomalies,
        "schema_results": profile,
        "semantic_schema": semantic_schema,
        "done": False
    }

# -------------------------
# ANOMALY EVALUATOR
# -------------------------
def anomaly_evaluator_node(state: PipelineState):
    anomalies = state.get("generated_anomalies", [])

    unique: Dict[Any, Dict[str, Any]] = {}
    for a in anomalies:
        key = (a.get("RowIndex"), a.get("Column"), a.get("IssueType"), a.get("Description"))
        if key not in unique:
            unique[key] = a

    cleaned = list(unique.values())

    normalized = []
    for a in cleaned:
        normalized.append({
            "row": a.get("RowIndex"),
            "column": a.get("Column"),
            "issue_type": a.get("IssueType"),
            "description": a.get("Description"),
            "severity": a.get("Severity"),
            "category": a.get("Category")
        })

    return {
        "df": state["df"],
        "generated_anomalies": normalized,
        "schema_results": state["schema_results"],
        "semantic_schema": state["semantic_schema"],
        "done": True
    }

# -------------------------
# BUILD GRAPH
# -------------------------
def build_graph():
    graph = StateGraph(PipelineState)

    graph.add_node("schema", schema_node)
    graph.add_node("anomaly_generator", anomaly_generator_node)
    graph.add_node("anomaly_evaluator", anomaly_evaluator_node)

    graph.set_entry_point("schema")

    graph.add_edge("schema", "anomaly_generator")
    graph.add_edge("anomaly_generator", "anomaly_evaluator")
    graph.add_edge("anomaly_evaluator", END)

    return graph.compile()

if __name__ == "__main__":
    print("Dynamic graph pipeline loaded successfully.")
