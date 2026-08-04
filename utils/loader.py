
import pandas as pd

def load_file(path: str):
    if path.endswith(".csv"):
        return pd.read_csv(path)
    if path.endswith(".xlsx") or path.endswith(".xls"):
        return pd.read_excel(path)
    raise ValueError("Unsupported file type")
