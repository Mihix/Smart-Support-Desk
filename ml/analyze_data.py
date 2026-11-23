
import pandas as pd
from pathlib import Path

DATA_FILE = Path("data/dataset.csv")

df = pd.read_csv(DATA_FILE)

print("\n===== DATASET OVERVIEW =====")
print("Dataset shape:", df.shape)
print("\nColumns:")
print(df.columns.tolist())

print("\n===== MISSING VALUES =====")
print(df.isnull().sum())

print("\n===== EXACT DUPLICATES =====")
print("Duplicate instructions:", df["instruction"].duplicated().sum())

print("\n===== UNIQUE VALUES =====")
for col in ["category", "intent", "flags"]:
    print(f"\n{col}:")
    print("Unique values:", df[col].nunique())
    print(df[col].value_counts().head(15))

print("\n===== LABEL CONFLICTS =====")
conflicts = (
    df.groupby("instruction")
    .agg(
        category_count=("category", "nunique"),
        intent_count=("intent", "nunique")
    )
)

conflicts = conflicts[
    (conflicts["category_count"] > 1) |
    (conflicts["intent_count"] > 1)
]

print("Messages with conflicting labels:", len(conflicts))

print("\n===== MESSAGE LENGTH =====")
df["message_length"] = df["instruction"].astype(str).str.len()

print(df["message_length"].describe())

print("\nMessages shorter than 5 characters:",
      (df["message_length"] < 5).sum())

print("\n===== ANALYSIS COMPLETED =====")
