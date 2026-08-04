import pandas as pd

def profile_schema(df, semantic_labels=None):
    profile = {}

    for col in df.columns:
        series = df[col]

        # Determine type from semantic labels OR dtype
        if semantic_labels and col in semantic_labels:
            semantic_type = semantic_labels[col].get("type", None)
        else:
            semantic_type = None

        # Fallback if semantic agent didn't specify type
        if semantic_type is None:
            if pd.api.types.is_numeric_dtype(series):
                semantic_type = "numeric"
            elif pd.api.types.is_string_dtype(series):
                semantic_type = "categorical"
            else:
                semantic_type = "unknown"

        # Base profile
        profile[col] = {
            "type": semantic_type,
            "dtype": str(series.dtype),
            "missing": int(series.isna().sum()),
            "unique_values": int(series.nunique(dropna=True)),
        }

        # Numeric stats
        if semantic_type == "numeric":
            profile[col]["min"] = float(series.min(skipna=True))
            profile[col]["max"] = float(series.max(skipna=True))
            profile[col]["categories"] = None

        # Categorical stats
        elif semantic_type == "categorical":
            profile[col]["sample_values"] = series.dropna().unique()[:5].tolist()
            profile[col]["categories"] = series.dropna().unique().tolist()
            profile[col]["min"] = None
            profile[col]["max"] = None

        # Unknown type
        else:
            profile[col]["min"] = None
            profile[col]["max"] = None
            profile[col]["categories"] = None

    return profile
