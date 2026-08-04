import random
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


def generate_anomalies(profile, n_rows=30, suggestions=None):
    logger.info("Generating %d anomalies with suggestions: %s", n_rows, suggestions)
    anomalies = []

    numeric_cols = [col for col, meta in profile.items() if meta["type"] == "numeric"]
    categorical_cols = [col for col, meta in profile.items() if meta["type"] == "categorical"]

    # Adjust anomaly weights based on evaluator suggestions
    numeric_weights = {
        "missing": 1,
        "negative": 1,
        "extreme": 1,
        "decimal": 1,
        "duplicate": 1,
    }

    categorical_weights = {
        "missing": 1,
        "invalid": 1,
        "rare": 1,
        "misspell": 1,
    }

    if suggestions:
        s = " ".join(suggestions).lower()

        if "age" in s or "range" in s:
            numeric_weights["extreme"] += 2

        if "specialty" in s:
            categorical_weights["invalid"] += 2
            categorical_weights["misspell"] += 1

    for _ in range(n_rows):
        row = {}

        # === NUMERIC ANOMALIES ===
        for col in numeric_cols:
            anomaly_type = random.choices(
                population=list(numeric_weights.keys()),
                weights=list(numeric_weights.values()),
                k=1
            )[0]

            if anomaly_type == "missing":
                row[col] = None

            elif anomaly_type == "negative":
                row[col] = -abs(random.randint(1, 10))

            elif anomaly_type == "extreme":
                row[col] = random.choice([
                    random.randint(150, 500),
                    random.randint(200, 400)
                ])

            elif anomaly_type == "decimal":
                row[col] = round(random.uniform(0, 20), 1)

            elif anomaly_type == "duplicate":
                row[col] = random.choice([1, 2, 3])

        # === CATEGORICAL ANOMALIES ===
        for col in categorical_cols:
            anomaly_type = random.choices(
                population=list(categorical_weights.keys()),
                weights=list(categorical_weights.values()),
                k=1
            )[0]

            valid_values = profile[col].get("categories", [])

            if anomaly_type == "missing":
                row[col] = None

            elif anomaly_type == "invalid":
                row[col] = "INVALID_VALUE"

            elif anomaly_type == "rare":
                row[col] = "RareCategory"

            elif anomaly_type == "misspell" and valid_values:
                base = random.choice(valid_values)
                row[col] = base[:-1]  # simple misspelling

        anomalies.append(row)

    return pd.DataFrame(anomalies)

def anomaly_generator_node(state):
    df = state["df"]
    anomalies = state.get("generated_anomalies", [])
    profile = state["schema_results"]        # from semantic_profiler
    semantic_schema = state["semantic_schema"]  # from schema_agent

    for col in df.columns:
        col_type = profile[col]["type"]
        series = df[col]

        # -------------------------
        # 1. Statistical Missing Values
        # (Schema validator already handles structural missing)
        # -------------------------
        for idx, val in series.items():
            if pd.isna(val) or val == "":
                anomalies.append({
                    "row": idx,
                    "column": col,
                    "issue_type": "Anomaly/Missing",
                    "description": f"Missing value in {col}",
                    "severity": "Medium",
                    "category": "Anomaly"
                })

        # -------------------------
        # 2. Outliers (3σ rule)
        # -------------------------
        if col_type == "numeric":
            mean = series.mean()
            std = series.std()

            if std > 0:
                for idx, val in series.items():
                    if pd.notna(val) and abs(val - mean) > 3 * std:
                        anomalies.append({
                            "row": idx,
                            "column": col,
                            "issue_type": "Anomaly/Outlier",
                            "description": f"Outlier detected in {col}: {val}",
                            "severity": "Medium",
                            "category": "Anomaly"
                        })

        # -------------------------
        # 3. Rare Category Detection
        # -------------------------
        if col_type == "categorical":
            categories = profile[col]["categories"]
            counts = series.value_counts(dropna=True)

            threshold = len(df) * 0.01  # <1% of rows

            for cat, count in counts.items():
                if count < threshold:
                    for idx, val in series.items():
                        if val == cat:
                            anomalies.append({
                                "row": idx,
                                "column": col,
                                "issue_type": "Anomaly/RareCategory",
                                "description": f"Rare category '{cat}' in {col}",
                                "severity": "Low",
                                "category": "Anomaly"
                            })

        # -------------------------
        # 4. Logical Anomalies (Example)
        # -------------------------
        if col.lower() == "profit":
            for idx, val in series.items():
                if pd.notna(val) and val < 0:
                    anomalies.append({
                        "row": idx,
                        "column": col,
                        "issue_type": "Anomaly/Logical",
                        "description": f"Profit is negative: {val}",
                        "severity": "High",
                        "category": "Anomaly"
                    })

    return {
        "generated_anomalies": anomalies,
        "schema_results": profile,
        "semantic_schema": semantic_schema
    }
