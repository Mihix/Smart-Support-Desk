
import pandas as pd
from pathlib import Path

# --------------------------------
# 1. CONFIGURATION
# --------------------------------

INPUT_FILE = Path("data/dataset.csv")
OUTPUT_FILE = Path("data/cleaned_dataset.csv")
REPORT_DIR = Path("data/reports")

REPORT_DIR.mkdir(parents=True, exist_ok=True)

# --------------------------------
# 2. LOAD DATA
# --------------------------------

df = pd.read_csv(INPUT_FILE)

print("\n===== ORIGINAL DATASET =====")
print("Original rows:", len(df))

# Keep original data unchanged
cleaned = df.copy()

# --------------------------------
# 3. REMOVE COMPLETELY IDENTICAL ROWS
# --------------------------------

before = len(cleaned)

cleaned = cleaned.drop_duplicates(
    keep="first"
)

exact_removed = before - len(cleaned)

print("\nExact duplicate rows removed:", exact_removed)

# --------------------------------
# 4. NORMALIZE TEXT
# --------------------------------

# Create normalized text for duplicate checking
normalized = (
    cleaned["instruction"]
    .astype(str)
    .str.lower()
    .str.strip()
    .str.replace(r"\s+", " ", regex=True)
)

cleaned["normalized_instruction"] = normalized

# --------------------------------
# 5. CHECK LABEL CONSISTENCY
# --------------------------------

label_check = (
    cleaned.groupby("normalized_instruction")
    .agg(
        category_count=("category", "nunique"),
        intent_count=("intent", "nunique")
    )
)

conflicting_messages = label_check[
    (label_check["category_count"] > 1) |
    (label_check["intent_count"] > 1)
]

print("\nConflicting normalized messages:",
      len(conflicting_messages))

# --------------------------------
# 6. REMOVE REPEATED MESSAGES
# --------------------------------

# This version is for classification.
# Keep one example per normalized instruction.

before = len(cleaned)

cleaned = cleaned.drop_duplicates(
    subset=["normalized_instruction"],
    keep="first"
)

repeated_removed = before - len(cleaned)

# Remove helper column
cleaned = cleaned.drop(
    columns=["normalized_instruction"]
)

# --------------------------------
# 7. SAVE CLEANED DATASET
# --------------------------------

cleaned.to_csv(OUTPUT_FILE, index=False)

# --------------------------------
# 8. FINAL VALIDATION
# --------------------------------

print("\n===== CLEANING SUMMARY =====")
print("Original rows:", len(df))
print("Exact duplicate rows removed:", exact_removed)
print("Repeated instructions removed:", repeated_removed)
print("Final rows:", len(cleaned))

print("\nMissing values:")
print(cleaned.isnull().sum())

print("\nRemaining exact duplicate rows:",
      cleaned.duplicated().sum())

print("\nCategory distribution:")
print(cleaned["category"].value_counts())

print("\nIntent distribution:")
print(cleaned["intent"].value_counts())

print("\nCleaned dataset saved to:", OUTPUT_FILE)
