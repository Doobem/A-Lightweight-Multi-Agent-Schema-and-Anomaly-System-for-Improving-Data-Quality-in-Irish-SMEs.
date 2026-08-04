import numpy as np

def detect_anomalies(df):
    results = {}

    # Missing values
    results["missing_values"] = df.isnull().sum().to_dict()

    # Outliers using Z-score
    numeric_cols = df.select_dtypes(include=["int64", "float64"]).columns
    outlier_report = {}

    for col in numeric_cols:
        z_scores = np.abs((df[col] - df[col].mean()) / df[col].std())
        outlier_report[col] = int((z_scores > 3).sum())

    results["outliers"] = outlier_report

    return results
