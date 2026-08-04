import pandas as pd

# Load anomaly sheet
anomaly = pd.read_excel("anomaly_report_Milk quality traits and mid-infrared spectral data.xlsx", sheet_name="Anomalies")

# Load schema summary
schema = pd.read_excel("anomaly_report_Milk quality traits and mid-infrared spectral data.xlsx", sheet_name="Schema Summary")

#Visualize Missing Values
import matplotlib.pyplot as plt

plt.figure(figsize=(14,6))
plt.bar(schema['Column'], schema['Missing'], color='steelblue')
plt.xticks(rotation=90)
plt.title("Missing Values per Column — Milk Quality Traits and Mid-Infrared Spectral Data")
plt.ylabel("Count")
plt.tight_layout()
plt.show()

#Missingness Heatmap (Schema Visual)
import seaborn as sns

milk_df = pd.read_excel("anomaly_report_Milk quality traits and mid-infrared spectral data.xlsx", sheet_name="Schema Summary")
plt.figure(figsize=(14,6))
sns.heatmap(milk_df.isnull(), cbar=False)
plt.title("Missingness Heatmap — Milk Quality Dataset")
plt.show()


#Visualise Outliers
outliers = anomaly[anomaly['issue_type'].str.contains("Outlier")]

values = outliers['description'].str.extract(r'(-?\d+\.?\d*)').astype(float)[0]

plt.figure(figsize=(12,6))
plt.scatter(outliers['row'], values, color='darkred')
plt.title("Outliers in Milk Quality Traits and Mid-Infrared Spectral Data")
plt.xlabel("Row Index")
plt.ylabel("Value")
plt.tight_layout()
plt.show()

#visualise Severity Distribution
severity_counts = anomaly['severity'].value_counts()

plt.figure(figsize=(6,6))
plt.pie(severity_counts, labels=severity_counts.index, autopct='%1.1f%%', colors=['gold','tomato'])
plt.title("Anomaly Severity Distribution — Milk Quality Traits and Mid-Infrared Spectral Data")
plt.show()


#Outlier Value Distribution

#plt.figure(figsize=(12,6))
#plt.hist(values, bins=30, color='purple')
#plt.title("Distribution of Outlier Values — Loan to Irish SMEs")
#plt.xlabel("Value")
#plt.ylabel("Frequency")
#plt.tight_layout()
#plt.show()



#anomaly type bar count
issue_counts = anomaly['issue_type'].value_counts()

plt.figure(figsize=(10,5))
plt.bar(issue_counts.index, issue_counts.values, color='teal')
plt.xticks(rotation=45)
plt.title("Anomaly Types — and Severity Distribution in Milk Quality Traits and Mid-Infrared Spectral Data")
plt.ylabel("Count")
plt.tight_layout()
plt.show()

#schema vs anomaly comparison
category_counts = anomaly['category'].value_counts()

plt.figure(figsize=(8,5))
plt.bar(category_counts.index, category_counts.values, color=['blue','red'])
plt.title("Schema vs Numeric Anomalies — Milk Quality Traits and Mid-Infrared Spectral Data")
plt.ylabel("Count")
plt.tight_layout()
plt.show()
