
import pandas as pd
from pathlib import Path

DATA_FILE = Path("data/dataset.csv")
REPORT_DIR = Path("data/reports")

REPORT_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(DATA_FILE)

# Find repeated customer instructions
duplicate_df = df[
    df["instruction"].duplicated(keep=False)
].copy()

# Analyze repeated messages
summary = (
    duplicate_df.groupby("instruction")
    .agg(
        occurrences=("instruction", "size"),
        unique_categories=("category", "nunique"),
        unique_intents=("intent", "nunique"),
        unique_responses=("response", "nunique")
    )
    .reset_index()
)

summary = summary.sort_values(
    "occurrences",
    ascending=False
)

# Save detailed report
summary.to_csv(
    REPORT_DIR / "duplicate_message_analysis.csv",
    index=False
)

print("\n===== DUPLICATE MESSAGE ANALYSIS =====")
print("Repeated message groups:", len(summary))
print("Rows involved:", len(duplicate_df))

print("\nRepeated messages with different responses:",
      (summary["unique_responses"] > 1).sum())

print("Repeated messages with different categories:",
      (summary["unique_categories"] > 1).sum())

print("Repeated messages with different intents:",
      (summary["unique_intents"] > 1).sum())

print("\nReport saved:")
print("data/reports/duplicate_message_analysis.csv")
