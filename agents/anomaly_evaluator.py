import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)
 

def evaluate_anomalies(profile, anomalies_df):
    logger.info("Evaluating %d generated anomalies", len(anomalies_df))
    realism_score = 10
    diversity_score = 0
    difficulty_score = 0

    anomaly_types_detected = set()
    suggestions = []

    numeric_cols = [col for col, meta in profile.items() if meta["type"] == "numeric"]
    categorical_cols = [col for col, meta in profile.items() if meta["type"] == "categorical"]

    # === NUMERIC EVALUATION ===
    for col in numeric_cols:
        col_values = anomalies_df[col]

        # Missing values
        if col_values.isna().any():
            anomaly_types_detected.add("missing_numeric")

        # Negative values
        if (col_values < 0).any():
            anomaly_types_detected.add("negative_numeric")
            realism_score -= 1

        # Extreme values
        if (col_values > 150).any():
            anomaly_types_detected.add("extreme_numeric")
            realism_score -= 2

        # Decimal values where integers expected
        if any(v % 1 != 0 for v in col_values.dropna()):
            anomaly_types_detected.add("decimal_numeric")
            difficulty_score += 1

    # === CATEGORICAL EVALUATION ===
    for col in categorical_cols:
        col_values = anomalies_df[col]
        valid_values = profile[col].get("categories", [])

        # Missing
        if col_values.isna().any():
            anomaly_types_detected.add("missing_categorical")

        # Invalid categories
        invalid_mask = ~col_values.isin(valid_values)
        if invalid_mask.any():
            anomaly_types_detected.add("invalid_category")
            realism_score -= 1

        # Misspellings (simple heuristic)
        for v in col_values.dropna():
            if isinstance(v, str) and v not in valid_values and len(v) > 2:
                anomaly_types_detected.add("misspell_category")
                difficulty_score += 1

    # === DIVERSITY SCORE ===
    diversity_score = len(anomaly_types_detected)

    # === SUGGESTIONS ===
    if "extreme_numeric" not in anomaly_types_detected:
        suggestions.append("Add age range anomalies")

    if "invalid_category" not in anomaly_types_detected:
        suggestions.append("Increase number of specialty anomalies")

    # === STOP FLAG ===
    stop_flag = False

    # If realism is too low OR diversity is high enough OR difficulty is high enough
    if realism_score >= 7 and diversity_score >= 5 and difficulty_score >= 5:
        stop_flag = True

    return {
        "realism": max(0, min(10, realism_score)),
        "diversity": diversity_score,
        "difficulty": difficulty_score,
        "missing_types": list(anomaly_types_detected),
        "suggestions": suggestions,
        "stop": stop_flag
    }
