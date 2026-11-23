
import pandas as pd
from pathlib import Path

INPUT_FILE = Path("data/reports/ai_manual_review.csv")
REPORT_DIR = Path("data/reports")

df = pd.read_csv(INPUT_FILE)

# Check required columns
required = [
    "same_meaning",
    "same_category",
    "same_intent",
    "review_decision"
]

missing = [col for col in required if col not in df.columns]

if missing:
    raise ValueError(f"Missing columns: {missing}")

# Normalize values
for col in required:
    df[col] = df[col].fillna("").astype(str).str.strip()

# Basic counts
total = len(df)
completed = df["same_meaning"].isin(
    ["Yes", "No", "Unclear"]
).sum()

print("\n===== NEAR DUPLICATE REVIEW SUMMARY =====")

print("Total pairs:", total)
print("Completed reviews:", completed)
print("Incomplete reviews:", total - completed)

print("\n===== MEANING RESULTS =====")
print(df["same_meaning"].value_counts().to_string())

print("\n===== LABEL CONSISTENCY =====")
print("Same category:")
print(df["same_category"].value_counts().to_string())

print("\nSame intent:")
print(df["same_intent"].value_counts().to_string())

print("\n===== REVIEW DECISIONS =====")
print(df["review_decision"].value_counts().to_string())

# Export pairs needing investigation
investigate = df[
    df["review_decision"].str.lower() == "investigate"
]

investigate.to_csv(
    REPORT_DIR / "investigate_pairs.csv",
    index=False
)

# Export pairs with same meaning but different labels
label_mismatches = df[
    (df["same_meaning"].str.lower() == "yes")
    & (
        (df["same_category"].str.lower() == "no")
        | (df["same_intent"].str.lower() == "no")
    )
]

label_mismatches.to_csv(
    REPORT_DIR / "label_mismatch_pairs.csv",
    index=False
)

print("\nInvestigate pairs:", len(investigate))
print("Potential label mismatches:", len(label_mismatches))

print("\nReports saved successfully!")
