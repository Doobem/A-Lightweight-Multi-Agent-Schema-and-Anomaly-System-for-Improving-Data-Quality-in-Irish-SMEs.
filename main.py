from utils.loader import load_file
from pipeline.run_pipeline import build_graph

df = load_file("data\sample.csv")
#print(df.head())

graph = build_graph()
result = graph.invoke({"df": df, "loop_count": 0})

print(result["anomalies"])
print(result["schema"])
