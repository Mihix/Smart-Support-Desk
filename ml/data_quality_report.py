
import pandas as pd
import re
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors

# Create output folder
Path("data/reports").mkdir(parents=True, exist_ok=True)

# Load dataset
df = pd.read_csv("data/dataset.csv")

print("=" * 50)
print("CUSTOMER SUPPORT DATA QUALITY REPORT")
print("=" * 50)

# ---------------------------------
# 1. Missing messages
# ---------------------------------
print("\n1. MISSING VALUES")

print(df[["instruction", "category", "intent"]].isnull().sum())

# Remove rows with missing essential information
invalid = df[
    df[["instruction", "category", "intent"]].isnull().any(axis=1)
]

print("Invalid rows:", len(invalid))

# ---------------------------------
# 2. Normalize customer messages
# ---------------------------------
def normalize_text(text):
    text = str(text).lower().strip()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text

df["normalized_message"] = df["instruction"].apply(normalize_text)

# ---------------------------------
# 3. Exact duplicate messages
# ---------------------------------
print("\n2. EXACT DUPLICATES")

duplicate_mask = df["normalized_message"].duplicated(keep="first")

print("Duplicate rows:", duplicate_mask.sum())
print("Unique duplicated messages:",
      df.loc[duplicate_mask, "normalized_message"].nunique())

duplicates = df[duplicate_mask]

duplicates.to_csv(
    "data/reports/exact_duplicates.csv",
    index=False
)

# ---------------------------------
# 4. Conflicting labels
# ---------------------------------
print("\n3. CONFLICTING LABELS")

label_counts = df.groupby("normalized_message").agg(
    category_count=("category", "nunique"),
    intent_count=("intent", "nunique")
)

conflicts = label_counts[
    (label_counts["category_count"] > 1) |
    (label_counts["intent_count"] > 1)
]

print("Messages with different labels:", len(conflicts))

conflict_examples = df[
    df["normalized_message"].isin(conflicts.index)
]

conflict_examples.to_csv(
    "data/reports/label_conflicts.csv",
    index=False
)

# ---------------------------------
# 5. Category imbalance
# ---------------------------------
print("\n4. CATEGORY DISTRIBUTION")

category_counts = df["category"].value_counts()

print(category_counts)

print("\nLargest / smallest category ratio:",
      round(category_counts.max() / category_counts.min(), 2))

# ---------------------------------
# 6. Very short messages
# ---------------------------------
print("\n5. VERY SHORT MESSAGES")

short_messages = df[
    df["instruction"].astype(str).str.strip().str.len() < 5
]

print("Very short messages:", len(short_messages))

short_messages.to_csv(
    "data/reports/short_messages.csv",
    index=False
)

# ---------------------------------
# 7. Potential near-duplicates
# ---------------------------------
print("\n6. POTENTIAL NEAR-DUPLICATES")

# Analyze unique normalized messages only
unique_messages = df.drop_duplicates(
    subset="normalized_message"
).copy()

texts = unique_messages["normalized_message"].tolist()

vectorizer = TfidfVectorizer(
    analyzer="char_wb",
    ngram_range=(3, 5),
    min_df=1
)

X = vectorizer.fit_transform(texts)

neighbors = NearestNeighbors(
    n_neighbors=2,
    metric="cosine",
    algorithm="brute"
)

neighbors.fit(X)

distances, indices = neighbors.kneighbors(X)

near_duplicates = []

for i in range(len(texts)):
    j = indices[i][1]
    similarity = 1 - distances[i][1]

    if similarity >= 0.90:
        if i < j:
            near_duplicates.append({
                "message_1": texts[i],
                "message_2": texts[j],
                "similarity": round(float(similarity), 3)
            })

near_df = pd.DataFrame(near_duplicates)

print("Potential near-duplicate pairs:", len(near_df))

near_df.to_csv(
    "data/reports/near_duplicates.csv",
    index=False
)

# ---------------------------------
# 8. Save summary
# ---------------------------------
print("\n" + "=" * 50)
print("DATA QUALITY ANALYSIS COMPLETED")
print("=" * 50)

print("\nReports saved inside data/reports/")
